"""
Nodes do LangGraph Workflow para o RPG Fighting Fantasy.

Cada node representa uma etapa do processamento da ação do jogador:
1. Validar ação
2. Buscar contexto RAG
3. Gerar narrativa (Gemini)
4. Executar combate
5. Executar testes
6. Atualizar estado
7. Verificar game over
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings

from .state import GameState
from .prompts import (
    NARRATIVE_PROMPT,
    COMBAT_PROMPT,
    TEST_PROMPT,
    ACTION_VALIDATOR_PROMPT,
)
from apps.game.services.retriever_service import search_section, get_section_by_number
from apps.game.tools.combat import combat_round, start_combat
from apps.game.tools.dice import roll_dice, check_luck, check_skill
from apps.game.tools.inventory import add_item, remove_item, check_item, use_item
from apps.game.tools.character import update_character_stats, get_character_state
from apps.game.validators.action_validator import validate_player_action
from apps.game.models import GameSession
from apps.characters.models import Character

logger = logging.getLogger("game.workflow")

# ===== CONFIGURAÇÃO DO LLM =====
def get_llm(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """Cria instância do Gemini."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        max_output_tokens=2048,
    )


# ===== NODE 1: VALIDAR AÇÃO =====
def validate_action_node(state: GameState) -> Dict[str, Any]:
    """
    Valida se a ação do jogador é permitida no contexto atual.

    Verifica:
    - Ação não vazia
    - Consistência com estado (ex: não atacar se não está em combate)
    - Inventário disponível
    - Sintaxe básica
    """
    logger.info(f"[validate_action_node] Validando: '{state['player_action']}'")

    player_action = state["player_action"].strip()

    if not player_action:
        return {
            **state,
            "action_valid": False,
            "validation_message": "Por favor, insira uma ação.",
            "next_step": "end",
        }

    # Usa validator existente
    validation_result = validate_player_action(
        action=player_action,
        in_combat=state.get("in_combat", False),
        inventory=state.get("inventory", []),
        current_section=state.get("current_section", 1),
    )

    if not validation_result.get("is_valid", False):
        return {
            **state,
            "action_valid": False,
            "validation_message": validation_result.get("error", "Ação inválida"),
            "next_step": "end",
        }

    # Detecta tipo de ação
    action_type = _detect_action_type(player_action, state)

    logger.info(f"[validate_action_node] Ação válida. Tipo: {action_type}")

    return {
        **state,
        "action_valid": True,
        "action_type": action_type,
        "validation_message": "Ação válida",
        "next_step": "retrieve_context",
    }


def _detect_action_type(action: str, state: GameState) -> str:
    """Detecta o tipo de ação baseado em palavras-chave."""
    action_lower = action.lower()

    # Combate
    if state.get("in_combat"):
        if any(w in action_lower for w in ["atacar", "lutar", "golpe", "ataque"]):
            return "combat"
        if any(w in action_lower for w in ["fugir", "correr", "escapar"]):
            return "flee"

    # Navegação
    if any(w in action_lower for w in ["ir para", "seguir", "voltar", "seção"]):
        return "navigation"

    # Inventário
    if any(
        w in action_lower for w in ["usar", "pegar", "soltar", "examinar", "inventário"]
    ):
        return "inventory"

    # Testes
    if any(w in action_lower for w in ["testar sorte", "teste de sorte", "sorte"]):
        return "test_luck"
    if any(
        w in action_lower
        for w in ["testar habilidade", "teste de habilidade", "habilidade"]
    ):
        return "test_skill"

    # Diálogo
    if any(w in action_lower for w in ["falar", "conversar", "perguntar", "dizer"]):
        return "talk"

    return "exploration"


# ===== NODE 2: BUSCAR CONTEXTO RAG =====
def retrieve_context_node(state: GameState) -> Dict[str, Any]:
    """
    Busca contexto relevante no Weaviate usando RAG.

    Para navegação: busca a seção específica
    Para exploração: busca contexto semântico
    """
    logger.info(
        f"[retrieve_context_node] Buscando contexto para seção {state['current_section']}"
    )

    book_class_name = state["book_class_name"]
    current_section = state["current_section"]
    action_type = state.get("action_type", "exploration")

    try:
        # Se é navegação explícita, busca seção específica
        if action_type == "navigation":
            section_data = get_section_by_number(book_class_name, current_section)
        else:
            # Busca semântica baseada na ação
            query = f"seção {current_section} {state['player_action']}"
            results = search_section(book_class_name, query, k=1)
            section_data = results[0] if results else None

        if not section_data:
            logger.warning(f"[retrieve_context_node] Seção {current_section} não encontrada")
            return {
                **state,
                "section_content": f"Você está na seção {current_section}. A aventura continua...",
                "section_metadata": {"section": current_section},
                "next_step": "generate_narrative",
            }

        logger.info(f"[retrieve_context_node] Contexto recuperado com sucesso")

        return {
            **state,
            "section_content": section_data.get("content", ""),
            "section_metadata": section_data.get("metadata", {}),
            "next_step": "generate_narrative",
        }

    except Exception as e:
        logger.error(f"[retrieve_context_node] Erro ao buscar contexto: {e}")
        return {
            **state,
            "section_content": f"Você está explorando a área...",
            "section_metadata": {},
            "next_step": "generate_narrative",
        }


# ===== NODE 3: GERAR NARRATIVA =====
def generate_narrative_node(state: GameState) -> Dict[str, Any]:
    """
    Gera narrativa usando Gemini baseada no contexto RAG e ação do jogador.

    Usa diferentes prompts dependendo do tipo de ação.
    """
    logger.info(f"[generate_narrative_node] Gerando narrativa para tipo: {state['action_type']}")

    action_type = state.get("action_type", "exploration")

    try:
        # Roteamento baseado no tipo de ação
        if action_type == "combat":
            return _generate_combat_narrative(state)
        elif action_type in ["test_luck", "test_skill"]:
            return _generate_test_narrative(state)
        else:
            return _generate_general_narrative(state)

    except Exception as e:
        logger.error(f"[generate_narrative_node] Erro ao gerar narrativa: {e}")
        return {
            **state,
            "narrative_response": f"Erro ao gerar narrativa: {str(e)}",
            "next_step": "end",
        }


def _generate_general_narrative(state: GameState) -> Dict[str, Any]:
    """Gera narrativa geral (exploração, diálogo, etc)."""
    llm = get_llm(temperature=0.8)
    chain = NARRATIVE_PROMPT | llm

    # Formatar histórico recente
    recent_history = _format_recent_history(state.get("history", []))

    # Formatar inventário
    inventory_str = ", ".join(state.get("inventory", [])) or "Vazio"

    response = chain.invoke(
        {
            "character_name": state["character_name"],
            "skill": state["skill"],
            "stamina": state["stamina"],
            "initial_stamina": state["initial_stamina"],
            "luck": state["luck"],
            "gold": state["gold"],
            "provisions": state["provisions"],
            "inventory": inventory_str,
            "current_section": state["current_section"],
            "section_content": state.get("section_content", ""),
            "player_action": state["player_action"],
            "recent_history": recent_history,
            "flags": json.dumps(state.get("flags", {}), indent=2),
        }
    )

    narrative_text = response.content

    logger.info(f"[generate_narrative_node] Narrativa gerada: {len(narrative_text)} chars")

    return {
        **state,
        "narrative_response": narrative_text,
        "next_step": "update_state",
    }


def _generate_combat_narrative(state: GameState) -> Dict[str, Any]:
    """Gera narrativa específica de combate."""
    # Executar round de combate primeiro
    combat_data = state.get("combat_data", {})

    if not combat_data:
        logger.error("[generate_combat_narrative] Dados de combate não encontrados")
        return {
            **state,
            "narrative_response": "Erro: você não está em combate.",
            "next_step": "end",
        }

    # Executa round
    combat_result = combat_round(
        character_skill=state["skill"],
        character_stamina=state["stamina"],
        enemy_name=combat_data["enemy_name"],
        enemy_skill=combat_data["enemy_skill"],
        enemy_stamina=combat_data["enemy_stamina"],
    )

    # Atualiza combat_data
    new_combat_data = {
        **combat_data,
        "enemy_stamina": combat_result["enemy_stamina"],
        "rounds": combat_data.get("rounds", 0) + 1,
    }

    # Gera narrativa com LLM
    llm = get_llm(temperature=0.7)
    chain = COMBAT_PROMPT | llm

    response = chain.invoke(
        {
            "enemy_name": combat_data["enemy_name"],
            "enemy_skill": combat_data["enemy_skill"],
            "enemy_stamina": combat_data["enemy_stamina"],
            "character_skill": state["skill"],
            "character_stamina": state["stamina"],
            "character_roll": combat_result["character_roll"],
            "character_roll_details": combat_result["character_roll_details"],
            "character_attack": combat_result["character_attack"],
            "enemy_roll": combat_result["enemy_roll"],
            "enemy_roll_details": combat_result["enemy_roll_details"],
            "enemy_attack": combat_result["enemy_attack"],
            "combat_result": combat_result["message"],
            "new_character_stamina": combat_result["character_stamina"],
            "new_enemy_stamina": combat_result["enemy_stamina"],
        }
    )

    # Verifica fim do combate
    in_combat = combat_result["winner"] is None
    game_over = combat_result["winner"] == "enemy"
    victory = combat_result["winner"] == "character"

    logger.info(
        f"[generate_combat_narrative] Round {new_combat_data['rounds']} completo. "
        f"Winner: {combat_result['winner']}"
    )

    return {
        **state,
        "stamina": combat_result["character_stamina"],
        "combat_data": new_combat_data if in_combat else None,
        "in_combat": in_combat,
        "narrative_response": response.content,
        "game_over": game_over,
        "victory": victory,
        "next_step": "update_state",
    }


def _generate_test_narrative(state: GameState) -> Dict[str, Any]:
    """Gera narrativa de teste de sorte/habilidade."""
    action_type = state.get("action_type", "test_luck")

    if action_type == "test_luck":
        test_result = check_luck(character_luck=state["luck"])
        test_type = "SORTE"
        stat_value = state["luck"]
        new_stat_value = test_result["new_luck"]
    else:
        test_result = check_skill(character_skill=state["skill"])
        test_type = "HABILIDADE"
        stat_value = state["skill"]
        new_stat_value = stat_value  # Skill não muda

    # Gera narrativa com LLM
    llm = get_llm(temperature=0.7)
    chain = TEST_PROMPT | llm

    response = chain.invoke(
        {
            "test_type": test_type,
            "test_type_upper": test_type,
            "character_name": state["character_name"],
            "stat_value": stat_value,
            "roll": test_result["roll"],
            "roll_details": test_result.get("rolls_detail", []),
            "target": state["luck"] if action_type == "test_luck" else state["skill"],
            "success": test_result["success"],
            "new_stat_value": new_stat_value,
            "player_action": state["player_action"],
        }
    )

    # Atualiza state
    updates = {}
    if action_type == "test_luck":
        updates["luck"] = new_stat_value

    logger.info(
        f"[generate_test_narrative] Teste de {test_type}: "
        f"{'SUCESSO' if test_result['success'] else 'FALHA'}"
    )

    return {
        **state,
        **updates,
        "narrative_response": response.content,
        "next_step": "update_state",
    }


def _format_recent_history(history: list, limit: int = 5) -> str:
    """Formata últimas N interações para contexto."""
    if not history:
        return "Início da aventura"

    recent = history[-limit:]
    formatted = []

    for entry in recent:
        turn = entry.get("turn", "?")
        action = entry.get("player_action", "")
        formatted.append(f"Turno {turn}: {action}")

    return "\n".join(formatted)


# ===== NODE 4: ATUALIZAR ESTADO =====
def update_game_state_node(state: GameState) -> Dict[str, Any]:
    """
    Persiste mudanças no MongoDB (GameSession e Character).

    Atualiza:
    - Stats do personagem
    - Inventário
    - Histórico
    - Flags
    - Seção atual
    """
    logger.info(f"[update_game_state_node] Atualizando sessão {state['session_id']}")

    try:
        # Buscar sessão no MongoDB
        session = GameSession.find_by_id(state["session_id"], state["user_id"])

        if not session:
            logger.error(f"[update_game_state_node] Sessão não encontrada")
            return {**state, "next_step": "end", "error": "Sessão não encontrada"}

        # Atualizar Character stats
        update_character_stats(
            character_id=state["character_id"],
            updates={
                "stamina": state["stamina"] - session.history[-1].get("stamina", state["stamina"])
                if session.history
                else 0,
                "luck": state["luck"] - session.history[-1].get("luck", state["luck"])
                if session.history
                else 0,
                "gold": state.get("gold", 0) - session.history[-1].get("gold", 0)
                if session.history
                else 0,
            },
        )

        # Adicionar ao histórico
        history_entry = {
            "turn": state.get("turn_number", len(session.history) + 1),
            "player_action": state["player_action"],
            "action_type": state.get("action_type", "unknown"),
            "narrative": state.get("narrative_response", ""),
            "stamina": state["stamina"],
            "luck": state["luck"],
            "gold": state.get("gold", 0),
            "section": state["current_section"],
            "timestamp": datetime.utcnow(),
        }

        session.add_to_history(history_entry)

        # Atualizar campos da sessão
        session.current_section = state["current_section"]
        session.inventory = state.get("inventory", [])
        session.flags = state.get("flags", {})

        # Atualizar status se game over
        if state.get("game_over"):
            session.status = GameSession.STATUS_DEAD
        elif state.get("victory"):
            session.status = GameSession.STATUS_COMPLETED

        session.save()

        logger.info(f"[update_game_state_node] Estado persistido com sucesso")

        return {
            **state,
            "turn_number": state.get("turn_number", 0) + 1,
            "next_step": "check_game_over",
        }

    except Exception as e:
        logger.error(f"[update_game_state_node] Erro ao atualizar estado: {e}")
        return {**state, "next_step": "end", "error": str(e)}


# ===== NODE 5: VERIFICAR GAME OVER =====
def check_game_over_node(state: GameState) -> Dict[str, Any]:
    """
    Verifica condições de fim de jogo.

    Game Over se:
    - ENERGIA <= 0
    - Vitória (flag específica ou seção final)
    """
    logger.info(f"[check_game_over_node] Verificando fim de jogo")

    game_over = False
    victory = False
    end_message = ""

    # Morte por ENERGIA
    if state["stamina"] <= 0:
        game_over = True
        end_message = "💀 Sua ENERGIA chegou a 0. Você morreu..."

    # Vitória (exemplo: seção 400 é final)
    # TODO: Cada livro tem sua própria seção final
    if state["current_section"] >= 400:
        victory = True
        end_message = "🎉 Você completou a aventura!"

    if game_over or victory:
        logger.info(f"[check_game_over_node] Jogo terminou: {end_message}")
        return {
            **state,
            "game_over": game_over,
            "victory": victory,
            "narrative_response": state.get("narrative_response", "") + f"\n\n{end_message}",
            "next_step": "end",
        }

    logger.info(f"[check_game_over_node] Jogo continua")
    return {**state, "next_step": "end"}


# ===== NODE 6: INICIALIZAR STATE =====
def initialize_state_node(
    session_id: str, user_id: int, player_action: str
) -> GameState:
    """
    Inicializa GameState a partir de GameSession e Character do MongoDB.

    Este node é chamado no início de cada turno para carregar o estado atual.
    """
    logger.info(f"[initialize_state_node] Inicializando estado para sessão {session_id}")

    try:
        # Buscar sessão
        session = GameSession.find_by_id(session_id, user_id)
        if not session:
            raise ValueError(f"Sessão {session_id} não encontrada")

        # Buscar personagem
        character_state = get_character_state(session.character_id)
        if "error" in character_state:
            raise ValueError(f"Personagem não encontrado: {character_state['error']}")

        # Buscar adventure para pegar class_name
        from apps.adventures.models import Adventure

        adventure = Adventure.objects.get(id=session.adventure_id)

        # Montar GameState inicial
        state: GameState = {
            # Sessão
            "session_id": session_id,
            "user_id": user_id,
            "adventure_id": session.adventure_id,
            "character_id": session.character_id,
            # Character stats
            "character_name": character_state["name"],
            "skill": character_state["skill"],
            "stamina": character_state["stamina"],
            "luck": character_state["luck"],
            "initial_skill": character_state["initial_skill"],
            "initial_stamina": character_state["initial_stamina"],
            "initial_luck": character_state["initial_luck"],
            "gold": character_state["gold"],
            "provisions": character_state["provisions"],
            "equipment": character_state["equipment"],
            # Inventário
            "inventory": session.inventory,
            # Navegação
            "current_section": session.current_section,
            "visited_sections": session.visited_sections,
            # RAG
            "book_class_name": adventure.processed_book.weaviate_class_name
            if hasattr(adventure, "processed_book")
            else "",
            "section_content": "",
            "section_metadata": {},
            # Ação
            "player_action": player_action,
            "action_type": "",
            # Combate
            "in_combat": False,
            "combat_data": None,
            # Flags
            "flags": session.flags,
            # Narrativa
            "narrative_response": "",
            "available_actions": [],
            # Validação
            "action_valid": False,
            "validation_message": "",
            # Controle
            "next_step": "validate_action",
            "error": None,
            "game_over": session.status == GameSession.STATUS_DEAD,
            "victory": session.status == GameSession.STATUS_COMPLETED,
            # Histórico
            "history": session.history,
            # Metadados
            "turn_number": len(session.history) + 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"[initialize_state_node] Estado inicializado com sucesso")
        return state

    except Exception as e:
        logger.error(f"[initialize_state_node] Erro ao inicializar: {e}")
        raise
