import random
import re
from typing import Dict
from langchain_core.tools import tool


@tool
def roll_dice(notation: str) -> dict:
    """
    Rola dados seguindo notação RPG padrão.

    Args:
        notation: String no formato '1d6', '2d6', '2d6+3', '1d6+6'

    Returns:
        dict: {
            'notation': '2d6+3',
            'rolls': [4, 3],
            'modifier': 3,
            'total': 10,
            'details': 'Rolou 2d6+3: [4, 3] + 3 = 10'
        }

    Examples:
        roll_dice("1d6") → rola 1 dado de 6 faces
        roll_dice("2d6+12") → rola 2 dados de 6 faces e soma 12
    """
    pattern = r"(\d+)d(\d+)([+-]\d+)?"
    match = re.match(pattern, notation.lower().strip())

    if not match:
        return {
            "error": f"Notação inválida: {notation}. Use formato NdM ou NdM+X",
            "total": 0,
        }

    num_dice = int(match.group(1))
    dice_sides = int(match.group(2))
    modifier = int(match.group(3) or 0)

    if num_dice > 10:
        return {"error": "Máximo de 10 dados por rolagem", "total": 0}

    if dice_sides not in [4, 6, 8, 10, 12, 20]:
        return {"error": f"Dado d{dice_sides} não suportado", "total": 0}

    rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier

    return {
        "notation": notation,
        "rolls": rolls,
        "modifier": modifier,
        "total": total,
        "details": f'Rolou {notation}: {rolls} {"+" if modifier >= 0 else ""}{modifier if modifier != 0 else ""} = {total}',
    }


@tool
def check_luck(character_luck: int) -> dict:
    """
    Testa a sorte do personagem no estilo Fighting Fantasy.

    Args:
        character_luck: Valor atual de SORTE do personagem

    Returns:
        dict: {
            'success': bool,
            'roll': int,
            'character_luck': int (antes),
            'new_luck': int (depois),
            'message': str
        }

    Regra Fighting Fantasy:
        - Rola 2d6
        - Se resultado <= SORTE atual: SUCESSO
        - Sempre reduz 1 ponto de SORTE após o teste
    """
    roll_result = roll_dice("2d6")
    roll_total = roll_result["total"]

    success = roll_total <= character_luck
    new_luck = character_luck - 1

    return {
        "success": success,
        "roll": roll_total,
        "character_luck": character_luck,
        "new_luck": new_luck,
        "rolls_detail": roll_result["rolls"],
        "message": (
            f"🍀 Teste de Sorte: Rolou {roll_total} vs Sorte {character_luck} → "
            f"{'SUCESSO! ✓' if success else 'FALHOU ✗'} "
            f"(Sorte agora é {new_luck})"
        ),
    }


@tool
def check_skill(character_skill: int, difficulty_modifier: int = 0) -> dict:
    """
    Testa a habilidade do personagem.

    Args:
        character_skill: Valor atual de HABILIDADE
        difficulty_modifier: Modificador de dificuldade (0 = normal, +2 = difícil, -2 = fácil)

    Returns:
        dict com resultado do teste
    """
    roll_result = roll_dice("2d6")
    roll_total = roll_result["total"]

    target = character_skill + difficulty_modifier
    success = roll_total <= target

    return {
        "success": success,
        "roll": roll_total,
        "target": target,
        "character_skill": character_skill,
        "modifier": difficulty_modifier,
        "rolls_detail": roll_result["rolls"],
        "message": (
            f"💪 Teste de Habilidade: Rolou {roll_total} vs {target} → "
            f"{'SUCESSO! ✓' if success else 'FALHOU ✗'}"
        ),
    }
