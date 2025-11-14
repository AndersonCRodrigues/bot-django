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
    from apps.game.models import GameSession
    import logging

    logger = logging.getLogger("adventures")
    adventure = get_object_or_404(Adventure, pk=pk, is_published=True)

    # Verificar se aventura tem livro processado
    if not hasattr(adventure, 'processed_book'):
        messages.error(request, "Esta aventura ainda não está disponível para jogar.")
        return redirect("adventures:list")

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

    # ===== VERIFICAR STATUS DO PERSONAGEM =====
    if character.stamina <= 0:
        messages.error(
            request,
            f"💀 {character.name} está morto (ENERGIA = 0). Crie um novo personagem para jogar."
        )
        return redirect("adventures:select_character", pk=pk)

    # ===== VERIFICAR SESSÃO EXISTENTE =====
    existing_session = GameSession.find_active_session(request.user.id, pk)

    if existing_session:
        # Verificar se é do mesmo personagem
        if existing_session.character_id == character_id:
            # Continuar sessão existente
            messages.info(request, f"Continuando aventura com {character.name}...")
            return redirect("game:play", session_id=existing_session.id)
        else:
            # Tem sessão ativa com OUTRO personagem
            other_char = Character.find_by_id(existing_session.character_id, request.user.id)

            if other_char:
                messages.warning(
                    request,
                    f"Você já tem uma aventura ativa com {other_char.name}. "
                    f"Complete ou abandone antes de começar outra."
                )
            else:
                messages.warning(
                    request,
                    "Você já tem uma aventura ativa. "
                    "Complete ou abandone antes de começar outra."
                )
            return redirect("game:play", session_id=existing_session.id)

    # ===== CRIAR NOVA SESSÃO =====
    try:
        logger.info(f"[start_with_character] Criando sessão: user_id={request.user.id}, adventure_id={pk}, character_id={character_id}")

        session = GameSession(
            user_id=request.user.id,
            adventure_id=pk,
            character_id=character_id,
            current_section=1,
            visited_sections=[1],
            inventory=[],
            flags={},
            history=[],
            status=GameSession.STATUS_ACTIVE
        )
        session.save()

        logger.info(f"Nova sessão criada: {session.id} - User: {request.user.id}, Character ID: {character_id}, Character Name: {character.name}")

        messages.success(
            request,
            f"🎮 Começando aventura '{adventure.title}' com {character.name}!"
        )

        return redirect("game:play", session_id=session.id)

    except Exception as e:
        logger.error(f"Erro ao criar sessão: {e}", exc_info=True)
        messages.error(request, f"Erro ao iniciar jogo: {str(e)}")
        return redirect("adventures:select_character", pk=pk)
