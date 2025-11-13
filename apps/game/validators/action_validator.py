import re
from typing import Optional, Tuple


class ActionValidator:
    """
    Valida ações do usuário e determina qual tool é necessária.
    """

    ACTION_PATTERNS = {
        "movement": [
            r"(?:vou|ir|seguir|voltar) (?:para|à|ao)",
            r"(?:entrar|sair|atravessar)",
        ],
        "combat": [
            r"(?:atacar|lutar|combater|enfrentar)",
            r"(?:golpear|acertar|investir)",
        ],
        "search": [
            r"(?:procurar|buscar|vasculhar|examinar)",
            r"(?:pegar|pegar|coletar)",
        ],
        "test_luck": [
            r"testar (?:minha )?sorte",
            r"usar (?:minha )?sorte",
        ],
        "dialogue": [
            r"(?:falar|conversar|perguntar|dizer)",
            r"(?:dialogar|questionar)",
        ],
    }

    def classify_action(self, user_input: str) -> Tuple[str, Optional[str]]:
        """
        Classifica ação do usuário.

        Returns:
            (action_type, required_tool)
        """
        text = user_input.lower()

        for action_type, patterns in self.ACTION_PATTERNS.items():
            if any(re.search(p, text, re.I) for p in patterns):
                tool = self._get_required_tool(action_type)
                return action_type, tool

        return "exploration", None  # Exploração livre

    def _get_required_tool(self, action_type: str) -> Optional[str]:
        """Retorna tool obrigatória para cada tipo de ação."""
        mapping = {
            "movement": "try_move_to",
            "combat": "combat_round",
            "search": "check_section_items",
            "test_luck": "check_luck",
            "dialogue": None,  # Livre
        }
        return mapping.get(action_type)
