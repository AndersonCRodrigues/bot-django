"""
GameState: Define o estado compartilhado do workflow LangGraph.

Este estado é passado entre todos os nodes do grafo e contém:
- Informações da sessão de jogo
- Stats do personagem
- Contexto da narrativa
- Histórico de ações
- Estado de combate
"""

from typing import TypedDict, List, Dict, Optional, Any


class GameState(TypedDict):
    """
    Estado completo do jogo que circula pelo workflow LangGraph.

    Cada node pode ler e modificar este estado.
    """

    # ===== SESSÃO E IDENTIFICAÇÃO =====
    session_id: str  # ID da GameSession (MongoDB)
    user_id: int  # ID do usuário (Django)
    adventure_id: int  # ID da Adventure (PostgreSQL)
    character_id: str  # ID do Character (MongoDB)

    # ===== STATS DO PERSONAGEM =====
    character_name: str
    skill: int  # HABILIDADE
    stamina: int  # ENERGIA
    luck: int  # SORTE
    initial_skill: int
    initial_stamina: int
    initial_luck: int
    gold: int
    provisions: int  # Provisões
    equipment: List[str]  # Equipamentos

    # ===== INVENTÁRIO =====
    inventory: List[str]  # Lista de itens

    # ===== NAVEGAÇÃO =====
    current_section: int  # Seção atual do livro
    visited_sections: List[int]  # Seções visitadas

    # ===== CONTEXTO RAG =====
    book_class_name: str  # Nome da classe Weaviate
    section_content: str  # Conteúdo da seção atual (do RAG)
    section_metadata: Dict[str, Any]  # Metadados da seção

    # ===== AÇÃO DO JOGADOR =====
    player_action: str  # Última ação do jogador
    action_type: str  # Tipo: "navigation", "combat", "inventory", "talk", "test"

    # ===== COMBATE =====
    in_combat: bool  # Se está em combate
    combat_data: Optional[Dict[str, Any]]  # Dados do inimigo atual
    # {
    #     "enemy_name": str,
    #     "enemy_skill": int,
    #     "enemy_stamina": int,
    #     "rounds": int
    # }

    # ===== FLAGS DO JOGO =====
    flags: Dict[str, Any]  # Flags de progresso (ex: {"porta_aberta": True})

    # ===== NARRATIVA =====
    narrative_response: str  # Resposta narrativa gerada pelo Gemini
    available_actions: List[str]  # Ações disponíveis para o jogador

    # ===== VALIDAÇÃO =====
    action_valid: bool  # Se a ação é válida
    validation_message: str  # Mensagem de validação

    # ===== CONTROLE DO WORKFLOW =====
    next_step: str  # Próximo passo do workflow
    # Valores possíveis:
    # - "validate_action"
    # - "retrieve_context"
    # - "generate_narrative"
    # - "execute_combat"
    # - "execute_test"
    # - "update_state"
    # - "end"

    error: Optional[str]  # Mensagem de erro
    game_over: bool  # Se o jogo terminou
    victory: bool  # Se o jogador venceu

    # ===== HISTÓRICO =====
    history: List[Dict[str, Any]]  # Histórico de interações
    # [{
    #     "turn": int,
    #     "player_action": str,
    #     "narrative": str,
    #     "timestamp": datetime
    # }]

    # ===== METADADOS =====
    turn_number: int  # Número do turno atual
    timestamp: str  # Timestamp da última atualização


class CombatState(TypedDict):
    """Estado específico para combate."""
    enemy_name: str
    enemy_skill: int
    enemy_stamina: int
    rounds: int
    combat_log: List[str]


class TestState(TypedDict):
    """Estado específico para testes (Sorte, Habilidade)."""
    test_type: str  # "luck", "skill"
    difficulty_modifier: int  # Para testes de skill
    success: bool
    roll: int
    message: str
