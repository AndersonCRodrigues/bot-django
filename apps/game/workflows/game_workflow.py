"""
LangGraph Workflow Principal para RPG Fighting Fantasy.

Orquestra o fluxo de jogo:
1. Validar ação do jogador
2. Buscar contexto RAG (Weaviate)
3. Gerar narrativa (Gemini)
4. Atualizar estado (MongoDB)
5. Verificar game over
6. Retornar resposta

Este workflow é stateless - cada invocação processa UMA ação.
O estado é persistido no MongoDB entre turnos.
"""

import logging
from typing import Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import GameState
from .nodes import (
    initialize_state_node,
    validate_action_node,
    retrieve_context_node,
    generate_narrative_node,
    update_game_state_node,
    check_game_over_node,
)

logger = logging.getLogger("game.workflow")


# ===== ROUTER: DECIDE PRÓXIMO PASSO =====
def router(state: GameState) -> Literal["validate_action", "retrieve_context", "generate_narrative", "update_state", "check_game_over", "end"]:
    """
    Decide o próximo node baseado no estado atual.

    Fluxo normal:
    validate_action → retrieve_context → generate_narrative → update_state → check_game_over → end

    Fluxo com erro:
    validate_action → end
    """
    next_step = state.get("next_step", "end")

    logger.debug(f"[router] Próximo passo: {next_step}")

    # Validações de segurança
    valid_steps = [
        "validate_action",
        "retrieve_context",
        "generate_narrative",
        "update_state",
        "check_game_over",
        "end",
    ]

    if next_step not in valid_steps:
        logger.warning(f"[router] Passo inválido '{next_step}', indo para 'end'")
        return "end"

    return next_step


# ===== CRIAR WORKFLOW =====
def create_game_workflow() -> StateGraph:
    """
    Cria o grafo LangGraph para o jogo.

    Retorna:
        StateGraph compilado e pronto para uso
    """
    logger.info("[create_game_workflow] Criando workflow LangGraph...")

    # Criar grafo
    workflow = StateGraph(GameState)

    # Adicionar nodes
    workflow.add_node("validate_action", validate_action_node)
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("generate_narrative", generate_narrative_node)
    workflow.add_node("update_state", update_game_state_node)
    workflow.add_node("check_game_over", check_game_over_node)

    # Definir ponto de entrada
    workflow.set_entry_point("validate_action")

    # Adicionar edges condicionais (usa router)
    workflow.add_conditional_edges(
        "validate_action",
        router,
        {
            "retrieve_context": "retrieve_context",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "retrieve_context",
        router,
        {
            "generate_narrative": "generate_narrative",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "generate_narrative",
        router,
        {
            "update_state": "update_state",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "update_state",
        router,
        {
            "check_game_over": "check_game_over",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "check_game_over",
        router,
        {
            "end": END,
        },
    )

    # Compilar workflow
    # memory = MemorySaver()  # Checkpointing em memória (opcional)
    # app = workflow.compile(checkpointer=memory)
    app = workflow.compile()

    logger.info("[create_game_workflow] Workflow criado com sucesso!")

    return app


# ===== FUNÇÃO HELPER: PROCESSAR AÇÃO =====
def process_game_action(session_id: str, user_id: int, player_action: str) -> Dict[str, Any]:
    """
    Processa uma ação do jogador através do workflow completo.

    Args:
        session_id: ID da GameSession (MongoDB)
        user_id: ID do usuário (Django)
        player_action: Ação digitada pelo jogador

    Returns:
        Dict com:
        - success: bool
        - narrative: str (resposta narrativa)
        - game_over: bool
        - victory: bool
        - error: str | None
        - stats: dict (stats atualizados)

    Exemplo:
        result = process_game_action(
            session_id="507f1f77bcf86cd799439011",
            user_id=1,
            player_action="Eu abro a porta e entro na sala"
        )

        if result["success"]:
            print(result["narrative"])
            print(f"ENERGIA: {result['stats']['stamina']}")
        else:
            print(f"Erro: {result['error']}")
    """
    logger.info(
        f"[process_game_action] Processando ação para sessão {session_id}: '{player_action}'"
    )

    try:
        # 1. Inicializar estado
        initial_state = initialize_state_node(session_id, user_id, player_action)

        # 2. Criar workflow
        app = create_game_workflow()

        # 3. Executar workflow
        final_state = app.invoke(initial_state)

        # 4. Montar resposta
        result = {
            "success": not bool(final_state.get("error")),
            "narrative": final_state.get("narrative_response", ""),
            "game_over": final_state.get("game_over", False),
            "victory": final_state.get("victory", False),
            "error": final_state.get("error"),
            "stats": {
                "skill": final_state.get("skill", 0),
                "stamina": final_state.get("stamina", 0),
                "luck": final_state.get("luck", 0),
                "gold": final_state.get("gold", 0),
                "provisions": final_state.get("provisions", 0),
            },
            "inventory": final_state.get("inventory", []),
            "current_section": final_state.get("current_section", 1),
            "in_combat": final_state.get("in_combat", False),
            "turn_number": final_state.get("turn_number", 0),
        }

        logger.info(
            f"[process_game_action] Ação processada com sucesso. "
            f"Turn: {result['turn_number']}, GameOver: {result['game_over']}"
        )

        return result

    except Exception as e:
        logger.error(f"[process_game_action] Erro ao processar ação: {e}", exc_info=True)
        return {
            "success": False,
            "narrative": "",
            "game_over": False,
            "victory": False,
            "error": str(e),
            "stats": {},
            "inventory": [],
            "current_section": 1,
            "in_combat": False,
            "turn_number": 0,
        }


# ===== VISUALIZAR GRAFO (DEBUG) =====
def visualize_workflow():
    """
    Gera visualização do grafo (requer graphviz).

    Uso:
        from apps.game.workflows.game_workflow import visualize_workflow
        visualize_workflow()
    """
    try:
        from IPython.display import Image, display

        app = create_game_workflow()
        display(Image(app.get_graph().draw_mermaid_png()))
    except ImportError:
        logger.warning("IPython não disponível. Instale para visualizar o grafo.")
    except Exception as e:
        logger.error(f"Erro ao visualizar workflow: {e}")


# ===== EXEMPLO DE USO =====
if __name__ == "__main__":
    """
    Exemplo de como usar o workflow em modo standalone.

    Em produção, este workflow é chamado pelas views do Django.
    """
    import sys

    # Configuração de logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    # Exemplo: processar ação
    test_session_id = "507f1f77bcf86cd799439011"  # Substitua por ID real
    test_user_id = 1
    test_action = "Eu examino a sala cuidadosamente"

    print(f"\n{'='*60}")
    print(f"TESTANDO WORKFLOW")
    print(f"{'='*60}\n")

    result = process_game_action(test_session_id, test_user_id, test_action)

    print(f"\n{'='*60}")
    print(f"RESULTADO:")
    print(f"{'='*60}\n")

    if result["success"]:
        print(f"✓ Sucesso!\n")
        print(f"NARRATIVA:\n{result['narrative']}\n")
        print(f"STATS:")
        print(f"  HABILIDADE: {result['stats']['skill']}")
        print(f"  ENERGIA: {result['stats']['stamina']}")
        print(f"  SORTE: {result['stats']['luck']}")
        print(f"  OURO: {result['stats']['gold']}")
        print(f"\nINVENTÁRIO: {', '.join(result['inventory']) or 'Vazio'}")
        print(f"SEÇÃO: {result['current_section']}")
        print(f"TURNO: {result['turn_number']}")
    else:
        print(f"✗ Erro: {result['error']}")
