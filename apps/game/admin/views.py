import os
from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.conf import settings

from .decorators import superuser_required
from .forms import BookUploadForm
from apps.adventures.models import Adventure
from apps.characters.models import Character
from apps.game.models import APIUsage, ProcessedBook
from apps.game.processors import process_book_upload
from apps.game.services import check_weaviate_health, delete_vector_store
from django.contrib.auth.models import User


@superuser_required
def dashboard(request):
    """
    Dashboard principal com métricas em tempo real.
    """
    # Período de análise
    days = int(request.GET.get("days", 30))
    since = timezone.now() - timedelta(days=days)

    # ====== BUSINESS METRICS ======
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__gte=since).count()

    # Active users (D1, D7, D30)
    active_d1 = (
        APIUsage.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))
        .values("user")
        .distinct()
        .count()
    )

    active_d7 = (
        APIUsage.objects.filter(created_at__gte=timezone.now() - timedelta(days=7))
        .values("user")
        .distinct()
        .count()
    )

    active_d30 = (
        APIUsage.objects.filter(created_at__gte=since).values("user").distinct().count()
    )

    # ====== CONTENT METRICS ======
    total_adventures = Adventure.objects.count()
    published_adventures = Adventure.objects.filter(is_published=True).count()

    most_played = Adventure.objects.annotate(play_count=Count("api_usage")).order_by(
        "-play_count"
    )[:5]

    # ====== TECHNICAL METRICS ======
    api_stats = APIUsage.objects.filter(created_at__gte=since).aggregate(
        total_calls=Count("id"),
        total_tokens=Sum("tokens_total"),
        total_cost=Sum("estimated_cost"),
        avg_response_time=Avg("response_time_ms"),
        success_count=Count("id", filter=Q(success=True)),
    )

    total_calls = api_stats["total_calls"] or 0
    success_rate = (
        (api_stats["success_count"] / total_calls * 100) if total_calls > 0 else 0
    )

    # ====== SYSTEM HEALTH ======
    weaviate_status = check_weaviate_health()

    # Storage usage
    processed_books = ProcessedBook.objects.aggregate(
        total_size=Sum("pdf_size_bytes"), total_chunks=Sum("chunks_indexed")
    )

    # ====== CHARTS DATA ======
    # Tokens por dia (últimos 30 dias)
    daily_tokens = []
    for i in range(days):
        day = timezone.now().date() - timedelta(days=i)
        tokens = (
            APIUsage.objects.filter(created_at__date=day).aggregate(
                total=Sum("tokens_total")
            )["total"]
            or 0
        )

        daily_tokens.append({"date": day.strftime("%d/%m"), "tokens": tokens})

    daily_tokens.reverse()

    # Custo por dia
    daily_costs = []
    for i in range(days):
        day = timezone.now().date() - timedelta(days=i)
        cost = APIUsage.objects.filter(created_at__date=day).aggregate(
            total=Sum("estimated_cost")
        )["total"] or Decimal("0")

        daily_costs.append({"date": day.strftime("%d/%m"), "cost": float(cost)})

    daily_costs.reverse()

    # Top operações
    top_operations = (
        APIUsage.objects.filter(created_at__gte=since)
        .values("operation_type")
        .annotate(count=Count("id"), tokens=Sum("tokens_total"))
        .order_by("-count")[:5]
    )

    # ====== ALERTS ======
    alerts = []

    # Alert: custo alto
    daily_cost = APIUsage.objects.filter(
        created_at__date=timezone.now().date()
    ).aggregate(total=Sum("estimated_cost"))["total"] or Decimal("0")

    if daily_cost > 10:
        alerts.append(
            {
                "type": "warning",
                "message": f"Custo hoje: ${daily_cost:.2f} (acima de $10)",
            }
        )

    # Alert: taxa de erro alta
    if success_rate < 95 and total_calls > 10:
        alerts.append(
            {"type": "danger", "message": f"Taxa de sucesso baixa: {success_rate:.1f}%"}
        )

    # Alert: Weaviate down
    if weaviate_status["status"] != "healthy":
        alerts.append({"type": "danger", "message": "Weaviate indisponível!"})

    context = {
        "days": days,
        # Business
        "total_users": total_users,
        "new_users": new_users,
        "active_d1": active_d1,
        "active_d7": active_d7,
        "active_d30": active_d30,
        # Content
        "total_adventures": total_adventures,
        "published_adventures": published_adventures,
        "most_played": most_played,
        # Technical
        "total_calls": total_calls,
        "total_tokens": api_stats["total_tokens"] or 0,
        "total_cost": float(api_stats["total_cost"] or 0),
        "avg_response_time": int(api_stats["avg_response_time"] or 0),
        "success_rate": round(success_rate, 1),
        # System
        "weaviate_status": weaviate_status,
        "total_storage_mb": round(
            (processed_books["total_size"] or 0) / 1024 / 1024, 2
        ),
        "total_chunks": processed_books["total_chunks"] or 0,
        # Charts
        "daily_tokens": daily_tokens,
        "daily_costs": daily_costs,
        "top_operations": top_operations,
        # Alerts
        "alerts": alerts,
    }

    return render(request, "game/admin/dashboard.html", context)


@superuser_required
def upload_book(request):
    """Upload e processamento de novo livro."""
    if request.method == "POST":
        form = BookUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Cria Adventure
                adventure = form.save(commit=False)
                adventure.author = request.user
                adventure.save()

                # Salva PDF temporariamente
                pdf_file = request.FILES["pdf_file"]
                upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads", "books")
                os.makedirs(upload_dir, exist_ok=True)

                pdf_path = os.path.join(upload_dir, f"{adventure.id}_{pdf_file.name}")

                with open(pdf_path, "wb+") as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)

                # Processa PDF (async seria melhor, mas simplificado)
                weaviate_class = form.cleaned_data["weaviate_class_name"]

                result = process_book_upload(
                    pdf_path=pdf_path,
                    class_name=weaviate_class,
                    adventure_id=adventure.id,
                )

                if result["status"] in ["success", "partial"]:
                    messages.success(
                        request,
                        f'🎉 Livro "{adventure.title}" processado com sucesso! '
                        f'{result["chunks_extracted"]} chunks indexados.',
                    )
                    return redirect("game_admin:list_books")
                else:
                    messages.error(
                        request,
                        f'❌ Erro ao processar livro: {result.get("error", "Desconhecido")}',
                    )

            except Exception as e:
                messages.error(request, f"❌ Erro: {str(e)}")
        else:
            messages.error(request, "❌ Formulário inválido. Verifique os campos.")
    else:
        form = BookUploadForm()

    context = {
        "form": form,
    }

    return render(request, "game/admin/upload_book.html", context)


@superuser_required
def list_books(request):
    """Lista todos os livros com estatísticas."""
    # Filtros
    status_filter = request.GET.get("status", "all")
    search = request.GET.get("q", "")

    # Query base
    books = Adventure.objects.select_related("author").prefetch_related(
        "processed_book"
    )

    # Filtros
    if status_filter == "published":
        books = books.filter(is_published=True)
    elif status_filter == "draft":
        books = books.filter(is_published=False)

    if search:
        books = books.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Anotações
    books = books.annotate(
        play_count=Count("api_usage"),
        total_tokens=Sum("api_usage__tokens_total"),
        total_cost=Sum("api_usage__estimated_cost"),
        unique_players=Count("api_usage__user", distinct=True),
    ).order_by("-created_at")

    # Paginação
    paginator = Paginator(books, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "search": search,
    }

    return render(request, "game/admin/list_books.html", context)


@superuser_required
def book_detail(request, pk):
    """Detalhes de um livro específico."""
    adventure = get_object_or_404(Adventure, pk=pk)

    try:
        processed = ProcessedBook.objects.get(adventure=adventure)
    except ProcessedBook.DoesNotExist:
        processed = None

    # Stats últimos 30 dias
    since = timezone.now() - timedelta(days=30)

    stats = APIUsage.objects.filter(
        adventure=adventure, created_at__gte=since
    ).aggregate(
        total_calls=Count("id"),
        unique_players=Count("user", distinct=True),
        total_tokens=Sum("tokens_total"),
        total_cost=Sum("estimated_cost"),
        avg_response_time=Avg("response_time_ms"),
    )

    # Personagens criados
    characters_count = Character.find_by_user_and_adventure(
        user_id=request.user.id, adventure_id=pk
    )

    context = {
        "adventure": adventure,
        "processed": processed,
        "stats": stats,
        "characters_count": len(characters_count) if characters_count else 0,
    }

    return render(request, "game/admin/book_detail.html", context)


@superuser_required
def delete_book(request, pk):
    """Deleta livro e dados do Weaviate."""
    adventure = get_object_or_404(Adventure, pk=pk)

    if request.method == "POST":
        try:
            # Remove do Weaviate
            try:
                processed = ProcessedBook.objects.get(adventure=adventure)
                delete_vector_store(processed.weaviate_class_name)
            except ProcessedBook.DoesNotExist:
                pass

            title = adventure.title
            adventure.delete()

            messages.success(request, f'✓ Livro "{title}" deletado com sucesso!')
            return redirect("game_admin:list_books")

        except Exception as e:
            messages.error(request, f"❌ Erro ao deletar: {str(e)}")

    context = {
        "adventure": adventure,
    }

    return render(request, "game/admin/delete_book.html", context)


@superuser_required
def users_list(request):
    """Lista usuários com estatísticas."""
    users = User.objects.annotate(
        total_calls=Count("api_usage"),
        total_tokens=Sum("api_usage__tokens_total"),
        total_cost=Sum("api_usage__estimated_cost"),
        characters_count=Count("profile__characters", distinct=True),
    ).order_by("-date_joined")

    # Paginação
    paginator = Paginator(users, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }

    return render(request, "game/admin/users_list.html", context)


@superuser_required
def api_logs(request):
    """Logs de API calls."""
    logs = APIUsage.objects.select_related("user", "adventure").order_by("-created_at")

    # Filtros
    user_id = request.GET.get("user")
    operation = request.GET.get("operation")
    success = request.GET.get("success")

    if user_id:
        logs = logs.filter(user_id=user_id)
    if operation:
        logs = logs.filter(operation_type=operation)
    if success:
        logs = logs.filter(success=(success == "true"))

    # Paginação
    paginator = Paginator(logs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "operations": APIUsage.OPERATION_CHOICES,
    }

    return render(request, "game/admin/api_logs.html", context)


@superuser_required
def system_health(request):
    """Status de saúde do sistema."""
    weaviate_health = check_weaviate_health()

    # MongoDB check
    try:
        from apps.characters.models import get_mongo_client

        mongo_client = get_mongo_client()
        mongo_client.server_info()
        mongo_status = {"status": "healthy"}
    except Exception as e:
        mongo_status = {"status": "unhealthy", "error": str(e)}

    # PostgreSQL check
    try:
        User.objects.count()
        postgres_status = {"status": "healthy"}
    except Exception as e:
        postgres_status = {"status": "unhealthy", "error": str(e)}

    context = {
        "weaviate": weaviate_health,
        "mongodb": mongo_status,
        "postgresql": postgres_status,
    }

    return render(request, "game/admin/system_health.html", context)
