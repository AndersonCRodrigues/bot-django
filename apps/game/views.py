"""
Views para o jogo RPG Fighting Fantasy.

Rotas principais:
- list_adventures: Lista aventuras disponíveis
- adventure_detail: Detalhes da aventura
- start_game: Iniciar nova partida
- play_game: Interface principal de jogo
- process_action: Processar ação via AJAX
- save_game: Salvar progresso
- load_game: Carregar save
- game_history: Histórico de jogadas
"""

import logging
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId

from apps.adventures.models import Adventure
from apps.characters.models import Character
from apps.game.models import GameSession
from apps.game.workflows.game_workflow import process_game_action
from apps.game.services.usage_tracker import UsageTracker

logger = logging.getLogger("game.views")


# ===== LISTA DE AVENTURAS =====
@login_required
def list_adventures(request):
    """
    Lista todas as aventuras disponíveis para jogar.

    Mostra aventuras com livros processados (prontas para RAG).
    """
    adventures = Adventure.objects.filter(
        processed_book__isnull=False
    ).select_related('processed_book')

    context = {
        'adventures': adventures,
        'page_title': 'Escolha sua Aventura',
    }

    return render(request, 'game/adventures_list.html', context)


# ===== DETALHES DA AVENTURA =====
@login_required
def adventure_detail(request, pk):
    """
    Mostra detalhes de uma aventura específica.

    Permite criar novo personagem ou selecionar personagem existente.
    """
    adventure = get_object_or_404(Adventure, pk=pk)

    # Buscar personagens do usuário para esta aventura
    # (personagens são do MongoDB, então fazemos query separada)
    characters = Character.find_by_user(request.user.id)

    # Filtrar personagens que não estão em sessões ativas desta aventura
    active_sessions = GameSession.find_by_user(request.user.id)
    character_ids_in_use = [
        session.character_id
        for session in active_sessions
        if session.adventure_id == adventure.id and session.status == GameSession.STATUS_ACTIVE
    ]

    available_characters = [
        char for char in characters
        if str(char['_id']) not in character_ids_in_use
    ]

    context = {
        'adventure': adventure,
        'available_characters': available_characters,
        'page_title': adventure.title,
    }

    return render(request, 'game/adventure_detail.html', context)


# ===== INICIAR JOGO =====
@login_required
@require_http_methods(["POST"])
def start_game(request, pk):
    """
    Inicia uma nova sessão de jogo.

    POST params:
        - character_id: ID do personagem (MongoDB)
        - create_new: se deve criar novo personagem
        - character_name: nome do novo personagem (se create_new)
    """
    adventure = get_object_or_404(Adventure, pk=pk)

    # Verificar se aventura tem livro processado
    if not hasattr(adventure, 'processed_book'):
        return JsonResponse({
            'success': False,
            'error': 'Esta aventura ainda não está disponível para jogar.'
        }, status=400)

    create_new = request.POST.get('create_new') == 'true'

    if create_new:
        # Criar novo personagem
        character_name = request.POST.get('character_name', f'Herói de {request.user.username}')

        try:
            character = Character.create(
                user_id=request.user.id,
                name=character_name,
            )
            character_id = str(character['_id'])
            logger.info(f"Novo personagem criado: {character_id} - {character_name}")

        except Exception as e:
            logger.error(f"Erro ao criar personagem: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro ao criar personagem: {str(e)}'
            }, status=500)
    else:
        # Usar personagem existente
        character_id = request.POST.get('character_id')

        if not character_id:
            return JsonResponse({
                'success': False,
                'error': 'Selecione um personagem ou crie um novo.'
            }, status=400)

        # Verificar se personagem existe e pertence ao usuário
        character = Character.find_by_id(character_id, request.user.id)
        if not character or character.get('user_id') != request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Personagem não encontrado.'
            }, status=404)

    # Criar GameSession
    try:
        session = GameSession.create_session(
            user_id=request.user.id,
            character_id=character_id,
            adventure_id=adventure.id,
        )

        logger.info(f"Nova sessão criada: {session.session_id}")

        return JsonResponse({
            'success': True,
            'session_id': session.session_id,
            'redirect_url': f'/game/play/{session.session_id}/',
        })

    except Exception as e:
        logger.error(f"Erro ao criar sessão: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao iniciar jogo: {str(e)}'
        }, status=500)


# ===== JOGAR (INTERFACE PRINCIPAL) =====
@login_required
def play_game(request, session_id):
    """
    Interface principal do jogo.

    Renderiza template com:
    - Narrativa
    - Stats do personagem
    - Inventário
    - Input de ações
    - Histórico
    """
    try:
        # Buscar sessão
        session = GameSession.find_by_id(session_id, request.user.id)

        if not session:
            return render(request, 'game/error.html', {
                'error_message': 'Sessão não encontrada.',
                'page_title': 'Erro',
            }, status=404)

        # Verificar se jogo terminou
        if session.status in [GameSession.STATUS_DEAD, GameSession.STATUS_COMPLETED]:
            game_over = session.status == GameSession.STATUS_DEAD
            victory = session.status == GameSession.STATUS_COMPLETED

            return render(request, 'game/game_over.html', {
                'session': session,
                'game_over': game_over,
                'victory': victory,
                'page_title': 'Jogo Terminado',
            })

        # Buscar personagem
        character = Character.find_by_id(session.character_id, request.user.id)

        if not character:
            return render(request, 'game/error.html', {
                'error_message': 'Personagem não encontrado.',
                'page_title': 'Erro',
            }, status=404)

        # Buscar adventure
        adventure = get_object_or_404(Adventure, pk=session.adventure_id)

        # Se é primeira vez, gerar narrativa inicial
        if not session.history:
            initial_action = "Começar a aventura com uma breve narração da introdução!"
            result = process_game_action(
                session_id=session_id,
                user_id=request.user.id,
                player_action=initial_action,
            )

            # Recarregar sessão com histórico atualizado
            session = GameSession.find_by_id(session_id, request.user.id)

        context = {
            'session': session,
            'character': character,
            'adventure': adventure,
            'history': session.history[-20:],  # Últimas 20 interações
            'page_title': f'Jogando: {adventure.title}',
        }

        return render(request, 'game/play.html', context)

    except Exception as e:
        logger.error(f"Erro em play_game: {e}", exc_info=True)
        return render(request, 'game/error.html', {
            'error_message': f'Erro ao carregar jogo: {str(e)}',
            'page_title': 'Erro',
        }, status=500)


# ===== PROCESSAR AÇÃO (AJAX) =====
@login_required
@require_http_methods(["POST"])
def process_action(request, session_id):
    """
    Processa uma ação do jogador via AJAX.

    POST params:
        - action: Ação digitada pelo jogador

    Returns JSON:
        {
            "success": true,
            "narrative": "...",
            "stats": {...},
            "inventory": [...],
            "game_over": false,
            "victory": false,
            "turn_number": 5,
            "in_combat": false,
            "current_section": 42,
        }
    """
    try:
        # Buscar sessão
        session = GameSession.find_by_id(session_id, request.user.id)

        if not session:
            return JsonResponse({
                'success': False,
                'error': 'Sessão não encontrada.'
            }, status=404)

        # Verificar se jogo já terminou
        if session.status in [GameSession.STATUS_DEAD, GameSession.STATUS_COMPLETED]:
            return JsonResponse({
                'success': False,
                'error': 'O jogo já terminou.',
                'game_over': session.status == GameSession.STATUS_DEAD,
                'victory': session.status == GameSession.STATUS_COMPLETED,
            })

        # Obter ação
        player_action = request.POST.get('action', '').strip()

        if not player_action:
            return JsonResponse({
                'success': False,
                'error': 'Por favor, insira uma ação.'
            }, status=400)

        logger.info(f"[process_action] Sessão {session_id}: '{player_action}'")

        # Processar ação através do LangGraph workflow
        result = process_game_action(
            session_id=session_id,
            user_id=request.user.id,
            player_action=player_action,
        )

        # Adicionar metadados úteis
        if result['success']:
            # Buscar adventure para info adicional
            adventure = Adventure.objects.get(pk=session.adventure_id)
            result['adventure_title'] = adventure.title

            # Track API usage
            UsageTracker.track_api_call(
                user_id=request.user.id,
                api_name='gemini_narrative',
                tokens_used=len(result.get('narrative', '')) // 4,  # Estimativa
                cost=0.0001,  # Estimativa
            )

        logger.info(f"[process_action] Resultado: success={result['success']}, "
                   f"game_over={result['game_over']}, turn={result['turn_number']}")

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Erro em process_action: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Erro ao processar ação: {str(e)}'
        }, status=500)


# ===== SALVAR JOGO =====
@login_required
@require_http_methods(["POST"])
def save_game(request, session_id):
    """
    Salva o jogo manualmente (já é salvo automaticamente).

    Retorna estado atual para confirmar.
    """
    try:
        session = GameSession.find_by_id(session_id, request.user.id)

        if not session:
            return JsonResponse({
                'success': False,
                'error': 'Sessão não encontrada.'
            }, status=404)

        # Buscar character para stats atualizados
        character = Character.find_by_id(session.character_id, request.user.id)

        return JsonResponse({
            'success': True,
            'message': 'Jogo salvo com sucesso!',
            'saved_at': datetime.utcnow().isoformat(),
            'turn_number': len(session.history),
            'character_stats': {
                'skill': character['skill'],
                'stamina': character['stamina'],
                'luck': character['luck'],
                'gold': character['gold'],
            }
        })

    except Exception as e:
        logger.error(f"Erro em save_game: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao salvar: {str(e)}'
        }, status=500)


# ===== CARREGAR JOGO =====
@login_required
def load_game(request):
    """
    Mostra lista de saves do usuário.

    Lista todas as sessões ativas do usuário.
    """
    try:
        sessions = GameSession.find_by_user(request.user.id)

        # Enriquecer com dados de adventures e characters
        enriched_sessions = []

        for session in sessions:
            adventure = Adventure.objects.get(pk=session.adventure_id)
            character = Character.find_by_id(session.character_id, request.user.id)

            enriched_sessions.append({
                'session': session,
                'adventure': adventure,
                'character': character,
            })

        context = {
            'sessions': enriched_sessions,
            'page_title': 'Carregar Jogo',
        }

        return render(request, 'game/load_game.html', context)

    except Exception as e:
        logger.error(f"Erro em load_game: {e}")
        return render(request, 'game/error.html', {
            'error_message': f'Erro ao carregar saves: {str(e)}',
            'page_title': 'Erro',
        }, status=500)


# ===== HISTÓRICO DE JOGADAS =====
@login_required
def game_history(request, session_id):
    """
    Mostra histórico completo de uma sessão.

    Útil para revisar decisões passadas.
    """
    try:
        session = GameSession.find_by_id(session_id, request.user.id)

        if not session:
            return render(request, 'game/error.html', {
                'error_message': 'Sessão não encontrada.',
                'page_title': 'Erro',
            }, status=404)

        adventure = get_object_or_404(Adventure, pk=session.adventure_id)
        character = Character.find_by_id(session.character_id, request.user.id)

        context = {
            'session': session,
            'adventure': adventure,
            'character': character,
            'history': session.history,
            'page_title': f'Histórico: {adventure.title}',
        }

        return render(request, 'game/history.html', context)

    except Exception as e:
        logger.error(f"Erro em game_history: {e}")
        return render(request, 'game/error.html', {
            'error_message': f'Erro ao carregar histórico: {str(e)}',
            'page_title': 'Erro',
        }, status=500)


# ===== DELETE SESSION (AJAX) =====
@login_required
@require_http_methods(["POST"])
def delete_session(request, session_id):
    """
    Deleta uma sessão (save).

    Apenas marca como abandonada, não deleta de verdade.
    """
    try:
        session = GameSession.find_by_id(session_id, request.user.id)

        if not session:
            return JsonResponse({
                'success': False,
                'error': 'Sessão não encontrada.'
            }, status=404)

        session.status = GameSession.STATUS_ABANDONED
        session.save()

        logger.info(f"Sessão {session_id} marcada como abandonada")

        return JsonResponse({
            'success': True,
            'message': 'Save deletado com sucesso.'
        })

    except Exception as e:
        logger.error(f"Erro em delete_session: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao deletar: {str(e)}'
        }, status=500)


# ===== API: GET CHARACTER STATS (AJAX) =====
@login_required
def get_character_stats(request, session_id):
    """
    Retorna stats atuais do personagem via AJAX.

    Útil para atualizar UI sem reload.
    """
    try:
        session = GameSession.find_by_id(session_id, request.user.id)

        if not session:
            return JsonResponse({
                'success': False,
                'error': 'Sessão não encontrada.'
            }, status=404)

        character = Character.find_by_id(session.character_id, request.user.id)

        return JsonResponse({
            'success': True,
            'stats': {
                'name': character['name'],
                'skill': character['skill'],
                'stamina': character['stamina'],
                'luck': character['luck'],
                'initial_skill': character['initial_skill'],
                'initial_stamina': character['initial_stamina'],
                'initial_luck': character['initial_luck'],
                'gold': character['gold'],
                'provisions': character['provisions'],
            },
            'inventory': session.inventory,
            'current_section': session.current_section,
            'turn_number': len(session.history),
        })

    except Exception as e:
        logger.error(f"Erro em get_character_stats: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erro ao obter stats: {str(e)}'
        }, status=500)
