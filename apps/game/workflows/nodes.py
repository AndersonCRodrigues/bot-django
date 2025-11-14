import logging
import json
import re
from datetime import datetime
from typing import Dict, Any
from django.conf import settings
from .state import GameState
from .prompts import (
    NARRATIVE_PROMPT,
    COMBAT_PROMPT,
    TEST_PROMPT,
    ACTION_VALIDATOR_PROMPT,
)
from apps.game.services.retriever_service import (
    search_section,
    get_section_by_number,
    get_section_by_number_direct,
)
from apps.game.tools.combat import combat_round, start_combat
from apps.game.tools.dice import roll_dice, check_luck, check_skill
from apps.game.tools.inventory import add_item, remove_item, check_item, use_item
from apps.game.tools.character import update_character_stats, get_character_state
from apps.game.models import GameSession
from apps.characters.models import Character
from apps.game.workflows.narrative_agent import RigidStructureValidator
from apps.game.llm_client import llm_client  # 🎯 Cliente LLM global
from apps.game.narrative_templates import (
    format_combat_narrative,
    format_luck_test_narrative,
    format_skill_test_narrative,
)
from apps.game.action_parser import parse_player_action
from apps.game.action_validators import (
    validate_pickup_item,
    validate_use_item,
    validate_navigation,
    validate_talk_to_npc,
)
from apps.game.rag_extractors import extract_all_section_info

logger = logging.getLogger("game.workflow")


def _clean_section_navigation(text: str) -> str:
    """
    Remove referências de navegação (números de seções) do texto do RAG.

    Remove padrões como:
    - "vá para 74"
    - "(seção 42)"
    - "volte para 15"
    - "passe para o 200"

    Mantém o resto da narrativa intacta.
    """
    if not text:
        return text

    # Padrões de navegação a remover
    patterns = [
        r'\(vá para (?:a seção )?(\d+)\)',
        r'\(volte para (?:a seção )?(\d+)\)',
        r'\(seção (\d+)\)',
        r'\(passe para (?:o |a seção )?(\d+)\)',
        r'\(retorne (?:para |à seção )?(\d+)\)',
        r'vá para (?:a seção )?(\d+)',
        r'volte para (?:a seção )?(\d+)',
        r'passe para (?:o |a seção )?(\d+)',
        r'retorne (?:para |à seção )?(\d+)',
    ]

    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Limpar espaços duplos e pontuação órfã resultantes
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s+\.', '.', cleaned)
    cleaned = re.sub(r'\s+,', ',', cleaned)

    return cleaned.strip()


def get_llm(temperature: float = 0.7):
    """
    🎯 Retorna cliente LLM global.

    IMPORTANTE: Sempre retorna a MESMA instância global.
    Temperatura é fixa em 0.7 (configurada no llm_client).
    """
    return llm_client


def validate_action_node(state: GameState) -> Dict[str, Any]:
    logger.info(f"[validate_action_node] Validando: '{state['player_action']}'")
    player_action = state["player_action"].strip()
    if not player_action:
        return {
            **state,
            "action_valid": False,
            "validation_message": "Por favor, insira uma ação.",
            "next_step": "end",
        }
    validator = RigidStructureValidator(state["book_class_name"])
    validation_result = validator.validate_action(
        player_action=player_action,
        current_section=state.get("current_section", 1),
        flags=state.get("flags", {}),
        in_combat=state.get("in_combat", False),
    )
    if not validation_result.get("valid", False):
        return {
            **state,
            "action_valid": False,
            "validation_message": validation_result.get(
                "error_message", "Ação inválida"
            ),
            "next_step": "end",
        }
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
    action_lower = action.lower()
    if state.get("in_combat"):
        if any(w in action_lower for w in ["atacar", "lutar", "golpe", "ataque"]):
            return "combat"
        if any(w in action_lower for w in ["fugir", "correr", "escapar"]):
            return "flee"
    if any(w in action_lower for w in ["ir para", "seguir", "voltar", "seção"]):
        return "navigation"
    if any(
        w in action_lower for w in ["usar", "pegar", "soltar", "examinar", "inventário"]
    ):
        return "inventory"
    if any(w in action_lower for w in ["testar sorte", "teste de sorte", "sorte"]):
        return "test_luck"
    if any(
        w in action_lower
        for w in ["testar habilidade", "teste de habilidade", "habilidade"]
    ):
        return "test_skill"
    if any(w in action_lower for w in ["falar", "conversar", "perguntar", "dizer"]):
        return "talk"
    return "exploration"


def retrieve_context_node(state: GameState) -> Dict[str, Any]:
    logger.info(
        f"[retrieve_context_node] Buscando contexto para seção {state['current_section']}"
    )
    book_class_name = state["book_class_name"]
    current_section = state["current_section"]
    action_type = state.get("action_type", "exploration")
    try:
        # 🚀 OTIMIZAÇÃO: Busca direta por metadata (SEM EMBEDDING!)
        # Economiza 1 API call por turno, reduzindo rate limiting
        section_data = get_section_by_number_direct(book_class_name, current_section)

        if not section_data:
            logger.warning(
                f"[retrieve_context_node] Seção {current_section} não encontrada"
            )
            return {
                **state,
                "section_content": f"Você está na seção {current_section}. A aventura continua...",
                "section_metadata": {"section": current_section},
                "next_step": "generate_narrative",
            }

        # 🎯 MELHORIA: Limpar referências de navegação do RAG
        raw_content = section_data.get("content", "")
        cleaned_content = _clean_section_navigation(raw_content)

        logger.info(f"[retrieve_context_node] Contexto recuperado e limpo com sucesso")
        return {
            **state,
            "section_content": cleaned_content,
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


def generate_narrative_node(state: GameState) -> Dict[str, Any]:
    logger.info(
        f"[generate_narrative_node] Gerando narrativa para tipo: {state['action_type']}"
    )
    action_type = state.get("action_type", "exploration")
    try:
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
    """
    Gera narrativa geral usando arquitetura RAG-first:
    1. Parse da ação do jogador (detectar intenção)
    2. Extrair info do RAG (items, NPCs, exits)
    3. Validar ação
    4. Executar ação (se aplicável)
    5. LLM narra o resultado
    """
    player_action = state["player_action"]
    section_content = state.get("section_content", "")
    current_section = state.get("current_section", 1)
    inventory = state.get("inventory", [])

    # 🎯 STEP 1: Parse da ação do jogador
    parsed_action = parse_player_action(player_action)
    action_type = parsed_action['type']
    action_target = parsed_action.get('target')

    logger.info(f"[general_narrative] Ação parseada: {action_type} (target: {action_target})")

    # 🎯 STEP 2: Extrair informações do RAG
    section_info = extract_all_section_info(section_content, current_section)
    available_items = section_info.get('items', [])
    available_exits = section_info.get('exits', [])
    available_npcs = section_info.get('npcs', [])

    logger.debug(
        f"[general_narrative] RAG info: {len(available_items)} items, "
        f"{len(available_exits)} exits, {len(available_npcs)} NPCs"
    )

    # 🎯 STEP 3 & 4: Validar e executar ação (baseado no tipo)
    action_result = None
    updates = {}

    if action_type == 'pickup':
        # Validar pickup
        validation = validate_pickup_item(action_target, available_items, inventory)
        if validation.valid:
            # Executar: adicionar item ao inventário
            add_item(state, action_target)
            updates['inventory'] = state.get('inventory', []) + [action_target]
            action_result = {
                'success': True,
                'message': f"Você pega {action_target}."
            }
            logger.info(f"[general_narrative] ✓ Item '{action_target}' adicionado")
        else:
            action_result = {
                'success': False,
                'message': validation.message
            }
            logger.warning(f"[general_narrative] ✗ Pickup falhou: {validation.reason}")

    elif action_type == 'use_item':
        # Validar uso de item
        validation = validate_use_item(action_target, inventory)
        if validation.valid:
            # Executar: usar item (lógica específica por tipo de item)
            use_result = use_item(state, action_target)
            action_result = {
                'success': True,
                'message': f"Você usa {action_target}.",
                'effect': use_result
            }
            logger.info(f"[general_narrative] ✓ Item '{action_target}' usado")
        else:
            action_result = {
                'success': False,
                'message': validation.message
            }
            logger.warning(f"[general_narrative] ✗ Use item falhou: {validation.reason}")

    elif action_type == 'talk':
        # Validar conversa com NPC
        validation = validate_talk_to_npc(action_target, available_npcs)
        if not validation.valid:
            action_result = {
                'success': False,
                'message': validation.message
            }
            logger.warning(f"[general_narrative] ✗ Talk falhou: {validation.reason}")
        else:
            # NPC válido - LLM vai gerar diálogo
            action_result = {
                'success': True,
                'message': f"Você conversa com {action_target}."
            }

    # 🎯 STEP 5: LLM narra o resultado
    llm = get_llm(temperature=0.8)
    chain = NARRATIVE_PROMPT | llm
    recent_history = _format_recent_history(state.get("history", []))
    inventory_str = ", ".join(updates.get('inventory', inventory)) or "Vazio"

    # Preparar contexto enriquecido com resultado da validação
    narrative_context = state.get("section_content", "")
    if action_result:
        narrative_context += f"\n\n[Resultado da ação: {action_result['message']}]"

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
            "current_section": current_section,
            "section_content": narrative_context,
            "player_action": player_action,
            "recent_history": recent_history,
            "flags": json.dumps(state.get("flags", {}), indent=2),
        }
    )

    narrative_text = response.content

    # Se ação falhou, priorizar mensagem de erro
    if action_result and not action_result['success']:
        narrative_text = f"{action_result['message']}\n\n{narrative_text}"

    logger.info(
        f"[generate_narrative_node] Narrativa gerada: {len(narrative_text)} chars "
        f"(ação: {action_type}, sucesso: {action_result.get('success') if action_result else 'N/A'})"
    )

    return {
        **state,
        **updates,
        "narrative_response": narrative_text,
        "next_step": "update_state",
    }


def _generate_combat_narrative(state: GameState) -> Dict[str, Any]:
    combat_data = state.get("combat_data", {})
    if not combat_data:
        logger.error("[generate_combat_narrative] Dados de combate não encontrados")
        return {
            **state,
            "narrative_response": "Erro: você não está em combate.",
            "next_step": "end",
        }
    combat_result = combat_round(
        character_skill=state["skill"],
        character_stamina=state["stamina"],
        enemy_name=combat_data["enemy_name"],
        enemy_skill=combat_data["enemy_skill"],
        enemy_stamina=combat_data["enemy_stamina"],
    )
    new_combat_data = {
        **combat_data,
        "enemy_stamina": combat_result["enemy_stamina"],
        "rounds": combat_data.get("rounds", 0) + 1,
    }

    # 🎯 OTIMIZAÇÃO: Usar template Python em vez de LLM (evita 429 errors)
    narrative_text = format_combat_narrative(
        enemy_name=combat_data["enemy_name"],
        enemy_skill=combat_data["enemy_skill"],
        enemy_stamina=combat_data["enemy_stamina"],
        character_skill=state["skill"],
        character_stamina=state["stamina"],
        character_roll=combat_result["character_roll"],
        character_attack=combat_result["character_attack"],
        enemy_roll=combat_result["enemy_roll"],
        enemy_attack=combat_result["enemy_attack"],
        combat_result=combat_result["message"],
        new_character_stamina=combat_result["character_stamina"],
        new_enemy_stamina=combat_result["enemy_stamina"],
    )

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
        "narrative_response": narrative_text,
        "game_over": game_over,
        "victory": victory,
        "next_step": "update_state",
    }


def _generate_test_narrative(state: GameState) -> Dict[str, Any]:
    action_type = state.get("action_type", "test_luck")

    # 🎯 OTIMIZAÇÃO: Usar template Python em vez de LLM (evita 429 errors)
    if action_type == "test_luck":
        test_result = check_luck(character_luck=state["luck"])
        test_type = "SORTE"
        new_stat_value = test_result["new_luck"]

        narrative_text = format_luck_test_narrative(
            character_name=state["character_name"],
            luck_value=state["luck"],
            roll=test_result["roll"],
            success=test_result["success"],
            new_luck=new_stat_value,
            player_action=state["player_action"],
        )
    else:
        test_result = check_skill(character_skill=state["skill"])
        test_type = "HABILIDADE"
        new_stat_value = state["skill"]

        narrative_text = format_skill_test_narrative(
            character_name=state["character_name"],
            skill_value=state["skill"],
            roll=test_result["roll"],
            success=test_result["success"],
            player_action=state["player_action"],
        )

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
        "narrative_response": narrative_text,
        "next_step": "update_state",
    }


def _format_recent_history(history: list, limit: int = 5) -> str:
    if not history:
        return "Início da aventura"
    recent = history[-limit:]
    formatted = []
    for entry in recent:
        turn = entry.get("turn", "?")
        action = entry.get("player_action", "")
        formatted.append(f"Turno {turn}: {action}")
    return "\n".join(formatted)


def update_game_state_node(state: GameState) -> Dict[str, Any]:
    logger.info(f"[update_game_state_node] Atualizando sessão {state['session_id']}")
    try:
        session = GameSession.find_by_id(state["session_id"], state["user_id"])
        if not session:
            logger.error(f"[update_game_state_node] Sessão não encontrada")
            return {**state, "next_step": "end", "error": "Sessão não encontrada"}

        # Atualizar personagem diretamente
        character = Character.find_by_id(state["character_id"], state["user_id"])
        if character:
            # Calcular diferenças
            old_stamina = session.history[-1].get("stamina", state["stamina"]) if session.history else state["stamina"]
            old_luck = session.history[-1].get("luck", state["luck"]) if session.history else state["luck"]
            old_gold = session.history[-1].get("gold", state.get("gold", 0)) if session.history else state.get("gold", 0)

            stamina_diff = state["stamina"] - old_stamina
            luck_diff = state["luck"] - old_luck
            gold_diff = state.get("gold", 0) - old_gold

            # Atualizar apenas se houver mudanças
            if stamina_diff != 0:
                character.stamina = max(0, state["stamina"])
            if luck_diff != 0:
                character.luck = max(0, state["luck"])
            if gold_diff != 0:
                character.gold = max(0, state.get("gold", 0))

            character.save()
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
        session.current_section = state["current_section"]
        session.inventory = state.get("inventory", [])
        session.flags = state.get("flags", {})
        if state.get("game_over"):
            session.status = GameSession.STATUS_DEAD
        elif state.get("victory"):
            session.status = GameSession.STATUS_COMPLETED
        session.save()
        logger.info(f"[update_game_state_node] Estado persistido com sucesso")
        return {
            **state,
            "turn_number": state.get("turn_number", 0) + 1,
            "achievements_unlocked": [],  # Achievements temporariamente desabilitados
            "next_step": "check_game_over",
        }
    except Exception as e:
        logger.error(f"[update_game_state_node] Erro ao atualizar estado: {e}")
        return {**state, "next_step": "end", "error": str(e)}


def check_game_over_node(state: GameState) -> Dict[str, Any]:
    logger.info(f"[check_game_over_node] Verificando fim de jogo")
    game_over = False
    victory = False
    end_message = ""
    if state["stamina"] <= 0:
        game_over = True
        end_message = "💀 Sua ENERGIA chegou a 0. Você morreu..."
    if state["current_section"] >= 400:
        victory = True
        end_message = "🎉 Você completou a aventura!"
    if game_over or victory:
        logger.info(f"[check_game_over_node] Jogo terminou: {end_message}")
        return {
            **state,
            "game_over": game_over,
            "victory": victory,
            "narrative_response": state.get("narrative_response", "")
            + f"\n\n{end_message}",
            "next_step": "end",
        }
    logger.info(f"[check_game_over_node] Jogo continua")
    return {**state, "next_step": "end"}


def initialize_state_node(
    session_id: str, user_id: int, player_action: str
) -> GameState:
    logger.info(
        f"[initialize_state_node] Inicializando estado para sessão {session_id}"
    )
    try:
        session = GameSession.find_by_id(session_id, user_id)
        if not session:
            raise ValueError(f"Sessão {session_id} não encontrada")

        # Buscar personagem diretamente
        character = Character.find_by_id(session.character_id, user_id)
        if not character:
            raise ValueError(f"Personagem não encontrado")

        character_state = {
            "name": character.name,
            "skill": character.skill,
            "stamina": character.stamina,
            "luck": character.luck,
            "initial_skill": character.initial_skill,
            "initial_stamina": character.initial_stamina,
            "initial_luck": character.initial_luck,
            "gold": character.gold,
            "provisions": character.provisions,
            "equipment": character.equipment,
        }
        from apps.adventures.models import Adventure

        adventure = Adventure.objects.get(id=session.adventure_id)
        state: GameState = {
            "session_id": session_id,
            "user_id": user_id,
            "adventure_id": session.adventure_id,
            "character_id": session.character_id,
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
            "inventory": session.inventory,
            "current_section": session.current_section,
            "visited_sections": session.visited_sections,
            "book_class_name": (
                adventure.processed_book.weaviate_class_name
                if hasattr(adventure, "processed_book")
                else ""
            ),
            "section_content": "",
            "section_metadata": {},
            "player_action": player_action,
            "action_type": "",
            "in_combat": False,
            "combat_data": None,
            "flags": session.flags,
            "narrative_response": "",
            "available_actions": [],
            "action_valid": False,
            "validation_message": "",
            "next_step": "validate_action",
            "error": None,
            "game_over": session.status == GameSession.STATUS_DEAD,
            "victory": session.status == GameSession.STATUS_COMPLETED,
            "history": session.history,
            "turn_number": len(session.history) + 1,
            "timestamp": datetime.utcnow().isoformat(),
        }
        logger.info(f"[initialize_state_node] Estado inicializado com sucesso")
        return state
    except Exception as e:
        logger.error(f"[initialize_state_node] Erro ao inicializar: {e}")
        raise
