from typing import TypedDict, List, Dict, Optional, Any


class GameState(TypedDict):
    session_id: str
    user_id: int
    adventure_id: int
    character_id: str
    character_name: str
    skill: int
    stamina: int
    luck: int
    initial_skill: int
    initial_stamina: int
    initial_luck: int
    gold: int
    provisions: int
    equipment: List[str]
    inventory: List[str]
    current_section: int
    visited_sections: List[int]
    book_class_name: str
    section_content: str
    section_metadata: Dict[str, Any]
    player_action: str
    action_type: str
    in_combat: bool
    combat_data: Optional[Dict[str, Any]]
    flags: Dict[str, Any]
    narrative_response: str
    available_actions: List[str]
    action_valid: bool
    validation_message: str
    next_step: str
    error: Optional[str]
    game_over: bool
    victory: bool
    history: List[Dict[str, Any]]
    turn_number: int
    timestamp: str


class CombatState(TypedDict):
    enemy_name: str
    enemy_skill: int
    enemy_stamina: int
    rounds: int
    combat_log: List[str]


class TestState(TypedDict):
    test_type: str
    difficulty_modifier: int
    success: bool
    roll: int
    message: str
