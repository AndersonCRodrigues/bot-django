from typing import Dict, Optional
from langchain_core.tools import tool
from .dice import roll_dice


@tool
def combat_round(
    character_skill: int,
    character_stamina: int,
    enemy_name: str,
    enemy_skill: int,
    enemy_stamina: int,
) -> dict:
    """
    Executa UMA rodada de combate no estilo Fighting Fantasy.

    Args:
        character_skill: HABILIDADE do personagem
        character_stamina: ENERGIA atual do personagem
        enemy_name: Nome do inimigo
        enemy_skill: HABILIDADE do inimigo
        enemy_stamina: ENERGIA do inimigo

    Returns:
        dict: {
            'character_roll': int,
            'character_attack': int,
            'enemy_roll': int,
            'enemy_attack': int,
            'character_damage': int,
            'enemy_damage': int,
            'character_stamina': int (novo),
            'enemy_stamina': int (novo),
            'winner': None | 'character' | 'enemy',
            'message': str
        }

    Regra Fighting Fantasy:
        1. Jogador rola 2d6 + HABILIDADE
        2. Inimigo rola 2d6 + HABILIDADE
        3. Maior ataque acerta, causa 2 de dano
        4. Empate: ninguém acerta
    """
    char_roll = roll_dice("2d6")
    enemy_roll = roll_dice("2d6")

    char_attack = char_roll["total"] + character_skill
    enemy_attack = enemy_roll["total"] + enemy_skill

    char_damage = 0
    enemy_damage = 0

    if char_attack > enemy_attack:
        enemy_damage = 2
        enemy_stamina -= 2
        result = f"Você acerta {enemy_name}! (-2 ENERGIA)"
    elif enemy_attack > char_attack:
        char_damage = 2
        character_stamina -= 2
        result = f"{enemy_name} acerta você! (-2 ENERGIA)"
    else:
        result = "Empate! Ninguém acerta nesta rodada."

    winner = None
    if enemy_stamina <= 0:
        winner = "character"
        result += f"\n🎉 Você derrotou {enemy_name}!"
    elif character_stamina <= 0:
        winner = "enemy"
        result += f"\n💀 Você foi derrotado por {enemy_name}..."

    return {
        "character_roll": char_roll["total"],
        "character_roll_details": char_roll["rolls"],
        "character_attack": char_attack,
        "enemy_roll": enemy_roll["total"],
        "enemy_roll_details": enemy_roll["rolls"],
        "enemy_attack": enemy_attack,
        "character_damage": char_damage,
        "enemy_damage": enemy_damage,
        "character_stamina": character_stamina,
        "enemy_stamina": enemy_stamina,
        "winner": winner,
        "message": result,
    }


@tool
def start_combat(enemy_name: str, enemy_skill: int, enemy_stamina: int) -> dict:
    """
    Inicia um combate com um inimigo.

    Args:
        enemy_name: Nome do inimigo
        enemy_skill: HABILIDADE do inimigo
        enemy_stamina: ENERGIA do inimigo

    Returns:
        dict com informações do inimigo
    """
    return {
        "combat_started": True,
        "enemy": {"name": enemy_name, "skill": enemy_skill, "stamina": enemy_stamina},
        "message": f"⚔️ Combate iniciado contra {enemy_name}! (HABILIDADE {enemy_skill}, ENERGIA {enemy_stamina})",
    }
