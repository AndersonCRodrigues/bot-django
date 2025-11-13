import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("game.parser")


class SectionParser:
    """
    Parser para extrair dados estruturados de seções Fighting Fantasy.
    """

    # Padrões regex
    SECTION_NUMBER_PATTERN = r"^(\d+)\s*$"
    GOTO_PATTERN = r"(?:vá para|vire para|ir para|siga para|volte para)\s+(\d+)"
    COMBAT_PATTERN = r"HABILIDADE\s+(\d+)\s+ENERGIA\s+(\d+)"
    TEST_LUCK_PATTERN = r"[Tt]este sua\s+(?:SORTE|sorte)"
    TEST_SKILL_PATTERN = r"[Tt]este sua\s+(?:HABILIDADE|habilidade)"
    ITEM_PATTERN = r"\b([A-Z]{3,}(?:\s+[A-Z]{3,})*)\b"
    NPC_PATTERN = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"

    @classmethod
    def parse_section(cls, text: str) -> Dict:
        """
        Parse completo de uma seção.

        Args:
            text: Texto da seção

        Returns:
            dict: {
                'section_number': int,
                'text': str,
                'exits': List[int],
                'combat': dict | None,
                'tests': dict | None,
                'items': List[str],
                'npcs': List[str]
            }
        """
        lines = text.strip().split("\n")

        # Extrai número da seção
        section_number = cls.extract_section_number(lines[0] if lines else "")

        # Texto narrativo (remove primeira linha se for número)
        narrative_text = "\n".join(lines[1:]) if section_number else text

        return {
            "section_number": section_number,
            "text": narrative_text.strip(),
            "exits": cls.extract_exits(text),
            "combat": cls.extract_combat(text),
            "tests": cls.extract_tests(text),
            "items": cls.extract_items(text),
            "npcs": cls.extract_npcs(narrative_text),
        }

    @classmethod
    def extract_section_number(cls, line: str) -> Optional[int]:
        """Extrai número da seção."""
        match = re.match(cls.SECTION_NUMBER_PATTERN, line.strip())
        if match:
            return int(match.group(1))
        return None

    @classmethod
    def extract_exits(cls, text: str) -> List[int]:
        """Extrai números de seções seguintes (exits)."""
        matches = re.findall(cls.GOTO_PATTERN, text, re.IGNORECASE)
        exits = [int(num) for num in matches]
        return sorted(list(set(exits)))  # Remove duplicatas e ordena

    @classmethod
    def extract_combat(cls, text: str) -> Optional[Dict]:
        """
        Extrai informações de combate.

        Returns:
            dict: {'enemy': str, 'skill': int, 'stamina': int} ou None
        """
        match = re.search(cls.COMBAT_PATTERN, text)
        if match:
            skill = int(match.group(1))
            stamina = int(match.group(2))

            # Tenta extrair nome do inimigo (palavra antes do padrão)
            enemy_pattern = r"(\w+)\s+HABILIDADE"
            enemy_match = re.search(enemy_pattern, text)
            enemy = enemy_match.group(1) if enemy_match else "Inimigo"

            return {"enemy": enemy, "skill": skill, "stamina": stamina}

        return None

    @classmethod
    def extract_tests(cls, text: str) -> Optional[Dict]:
        """
        Extrai informações de testes.

        Returns:
            dict: {'type': 'luck' | 'skill'} ou None
        """
        if re.search(cls.TEST_LUCK_PATTERN, text):
            return {"type": "luck"}

        if re.search(cls.TEST_SKILL_PATTERN, text):
            return {"type": "skill"}

        return None

    @classmethod
    def extract_items(cls, text: str) -> List[str]:
        """
        Extrai itens (palavras em MAIÚSCULAS).

        Returns:
            Lista de itens encontrados
        """
        # Palavras em maiúsculas (mínimo 3 letras)
        matches = re.findall(cls.ITEM_PATTERN, text)

        # Filtra palavras comuns que não são itens
        stopwords = {
            "HABILIDADE",
            "ENERGIA",
            "SORTE",
            "TESTE",
            "VÁ",
            "PARA",
            "SE",
            "OU",
            "E",
        }
        items = [item for item in matches if item not in stopwords]

        return sorted(list(set(items)))  # Remove duplicatas

    @classmethod
    def extract_npcs(cls, text: str) -> List[str]:
        """
        Extrai possíveis NPCs (nomes próprios).

        Returns:
            Lista de NPCs encontrados
        """
        # Palavras capitalizadas (possíveis nomes)
        matches = re.findall(cls.NPC_PATTERN, text)

        # Filtra palavras comuns
        stopwords = {"Você", "Teste", "Role", "Se", "Vá", "Para", "A", "O"}
        npcs = [npc for npc in matches if npc not in stopwords]

        return sorted(list(set(npcs)))  # Remove duplicatas

    @classmethod
    def validate_section(cls, section_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Valida dados de uma seção.

        Returns:
            (is_valid, error_message)
        """
        if not section_data.get("section_number"):
            return False, "Número da seção ausente"

        if not section_data.get("text"):
            return False, "Texto narrativo ausente"

        if not section_data.get("exits"):
            logger.warning(f"Seção {section_data['section_number']} sem exits")

        return True, None


def parse_full_book(chunks: List[str]) -> List[Dict]:
    """
    Parse completo de todos os chunks do livro.

    Args:
        chunks: Lista de chunks de texto

    Returns:
        Lista de seções parseadas
    """
    sections = []

    for chunk in chunks:
        try:
            section = SectionParser.parse_section(chunk)

            # Valida seção
            is_valid, error = SectionParser.validate_section(section)
            if is_valid:
                sections.append(section)
            else:
                logger.warning(f"Seção inválida: {error}")

        except Exception as e:
            logger.error(f"Erro ao parsear chunk: {e}")

    return sections
