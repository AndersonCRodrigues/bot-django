from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Adventure
from apps.characters.models import Character


def adventure_list(request):
    adventures = Adventure.objects.filter(is_published=True).order_by("-created_at")

    context = {
        "adventures": adventures,
    }

    return render(request, "adventures/list.html", context)


def adventure_detail(request, pk):
    adventure = get_object_or_404(Adventure, pk=pk, is_published=True)

    # TODO: Implementar verificação de sessão ativa quando criar o app game
    user_session = None

    context = {
        "adventure": adventure,
        "user_session": user_session,
    }

    return render(request, "adventures/detail.html", context)


@login_required
def adventure_start(request, pk):
    """Redireciona para seleção de personagem"""
    adventure = get_object_or_404(Adventure, pk=pk, is_published=True)
    return redirect("adventures:select_character", pk=pk)


@login_required
def select_character(request, pk):
    """Tela de seleção de personagem - APENAS da aventura específica"""
    adventure = get_object_or_404(Adventure, pk=pk, is_published=True)

    # Buscar APENAS personagens criados para ESTA aventura
    characters = Character.find_by_user_and_adventure(request.user.id, pk)

    context = {
        "adventure": adventure,
        "characters": characters,
    }

    return render(request, "adventures/select_character.html", context)


@login_required
def start_with_character(request, pk):
    """Inicia sessão com personagem selecionado"""
    adventure = get_object_or_404(Adventure, pk=pk, is_published=True)

    # Aceitar character_id via POST ou GET
    if request.method == "POST":
        character_id = request.POST.get("character_id")
    else:
        character_id = request.GET.get("character_id")

    if not character_id:
        messages.error(request, "Selecione um personagem.")
        return redirect("adventures:select_character", pk=pk)

    # Verificar se personagem existe e pertence ao usuário
    character = Character.find_by_id(character_id, request.user.id)
    if not character:
        messages.error(request, "Personagem não encontrado.")
        return redirect("adventures:select_character", pk=pk)

    # Verificar se personagem pertence a esta aventura
    if character.adventure_id != pk:
        messages.error(request, f"{character.name} não foi criado para esta aventura.")
        return redirect("adventures:select_character", pk=pk)

    # TODO: Criar sessão de jogo quando implementar o app game
    messages.success(request, f"Pronto para começar a aventura com {character.name}!")

    # Por enquanto, redireciona de volta para aventuras
    # Quando criar o app game, vai redirecionar para: redirect('game:play', session_id=session.id)
    return redirect("adventures:list")
