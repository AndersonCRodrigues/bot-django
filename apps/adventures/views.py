from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Adventure
from apps.game.models import GameSession
from apps.characters.models import Character


def adventure_list(request):
    adventures = Adventure.objects.filter(is_active=True).order_by("-created_at")

    context = {
        "adventures": adventures,
    }

    return render(request, "adventures/list.html", context)


def adventure_detail(request, pk):
    adventure = get_object_or_404(Adventure, pk=pk, is_active=True)

    user_session = None
    if request.user.is_authenticated:
        user_session = GameSession.objects.filter(
            user=request.user, adventure=adventure, status="active"
        ).first()

    context = {
        "adventure": adventure,
        "user_session": user_session,
    }

    return render(request, "adventures/detail.html", context)


@login_required
def adventure_start(request, pk):
    """Redireciona para seleção de personagem"""
    adventure = get_object_or_404(Adventure, pk=pk, is_active=True)
    return redirect("adventures:select_character", pk=pk)


@login_required
def select_character(request, pk):
    """Tela de seleção de personagem"""
    adventure = get_object_or_404(Adventure, pk=pk, is_active=True)
    characters = Character.find_by_user(request.user.id)

    context = {
        "adventure": adventure,
        "characters": characters,
    }

    return render(request, "adventures/select_character.html", context)


@login_required
def start_with_character(request, pk):
    """Inicia sessão com personagem selecionado"""
    if request.method != "POST":
        return redirect("adventures:select_character", pk=pk)

    adventure = get_object_or_404(Adventure, pk=pk, is_active=True)
    character_id = request.POST.get("character_id")

    if not character_id:
        messages.error(request, "Selecione um personagem.")
        return redirect("adventures:select_character", pk=pk)

    # Verificar se personagem existe e pertence ao usuário
    character = Character.find_by_id(character_id, request.user.id)
    if not character:
        messages.error(request, "Personagem não encontrado.")
        return redirect("adventures:select_character", pk=pk)

    # Verificar se já tem sessão ativa
    active_session = GameSession.objects.filter(
        user=request.user, adventure=adventure, status="active"
    ).first()

    if active_session:
        return redirect("game:play", session_id=active_session.id)

    # Criar nova sessão
    session = GameSession.objects.create(
        user=request.user,
        adventure=adventure,
        character_id=str(character._id),
        character_name=character.name,
        status="active",
    )

    messages.success(request, f"Aventura iniciada com {character.name}!")
    return redirect("game:play", session_id=session.id)
