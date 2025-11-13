import re
from typing import Dict, Tuple, Optional, List


class ResponseValidator:
    """
    Valida respostas do Agent para evitar alucinações.
    """

    FORBIDDEN_PATTERNS = {
        "dice_without_tool": [
            r"você (?:tira|tirou|rolou) (?:um )?(\d+)",
            r"resultado (?:é |foi )?(\d+)",
            r"os dados (?:mostram|mostraram) (\d+)",
        ],
        "movement_without_tool": [
            r"você (?:vai|foi|segue|seguiu) (?:para|à) (?:seção )?(\d+)",
            r"chegando (?:na|à|em) seção (\d+)",
            r"você se encontra na seção (\d+)",
        ],
        "item_without_tool": [
            r"você (?:encontra|encontrou|acha|achou|ganha|ganhou) (?:uma?|um) ([A-Z_]+)",
            r"há (?:uma?|um) ([A-Z_]+) (?:no|na)",
        ],
        "combat_without_tool": [
            r"você (?:acerta|acertou) o (?:inimigo|orc|goblin)",
            r"(?:inimigo|orc|goblin) (?:acerta|acertou) você",
            r"você (?:perde|perdeu) (\d+) de energia",
        ],
    }

    def __init__(self):
        self.last_tools_used = []

    def validate(
        self, response: str, tools_executed: List[str], tool_results: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida resposta do Agent.

        Returns:
            (is_valid, error_message)
        """

        # 1. Mencionou dados mas não rolou?
        if self._mentions_dice(response) and "roll_dice" not in tools_executed:
            return False, "❌ Agent mencionou resultado de dados sem chamar roll_dice"

        # 2. Mencionou movimento mas não validou?
        if self._mentions_movement(response) and "try_move_to" not in tools_executed:
            return False, "❌ Agent mencionou mudança de seção sem chamar try_move_to"

        # 3. Mencionou item mas não verificou?
        if (
            self._mentions_item(response)
            and "check_section_items" not in tools_executed
        ):
            return False, "❌ Agent mencionou item sem verificar disponibilidade"

        # 4. Mencionou combate mas não executou?
        if self._mentions_combat(response) and "combat_round" not in tools_executed:
            return False, "❌ Agent mencionou resultado de combate sem executar combate"

        # 5. Validar que números mencionados batem com tool results
        if "roll_dice" in tool_results:
            mentioned_numbers = self._extract_numbers_from_text(response)
            actual_result = tool_results["roll_dice"].get("total")
            if mentioned_numbers and actual_result not in mentioned_numbers:
                return (
                    False,
                    f"❌ Agent mencionou números diferentes do resultado real ({actual_result})",
                )

        return True, None

    def _mentions_dice(self, text: str) -> bool:
        patterns = self.FORBIDDEN_PATTERNS["dice_without_tool"]
        return any(re.search(p, text, re.I) for p in patterns)

    def _mentions_movement(self, text: str) -> bool:
        patterns = self.FORBIDDEN_PATTERNS["movement_without_tool"]
        return any(re.search(p, text, re.I) for p in patterns)

    def _mentions_item(self, text: str) -> bool:
        patterns = self.FORBIDDEN_PATTERNS["item_without_tool"]
        return any(re.search(p, text, re.I) for p in patterns)

    def _mentions_combat(self, text: str) -> bool:
        patterns = self.FORBIDDEN_PATTERNS["combat_without_tool"]
        return any(re.search(p, text, re.I) for p in patterns)

    def _extract_numbers_from_text(self, text: str) -> List[int]:
        """Extrai todos os números mencionados no texto."""
        return [int(n) for n in re.findall(r"\b(\d+)\b", text)]
