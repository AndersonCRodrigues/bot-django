from typing import List
from langchain_core.tools import tool


@tool
def add_item(item_name: str, inventory: List[str]) -> dict:
    """
    Adiciona item ao inventário.

    Args:
        item_name: Nome do item em MAIÚSCULAS (ex: CHAVE_ENFERRUJADA)
        inventory: Lista atual de itens

    Returns:
        dict: {
            'success': bool,
            'item': str,
            'inventory': List[str],
            'message': str
        }
    """
    item_upper = item_name.upper().replace(" ", "_")

    if item_upper in inventory:
        return {
            "success": False,
            "item": item_upper,
            "inventory": inventory,
            "message": f"Você já tem {item_upper}",
        }

    new_inventory = inventory + [item_upper]

    return {
        "success": True,
        "item": item_upper,
        "inventory": new_inventory,
        "message": f"✓ {item_upper} adicionado ao inventário",
    }


@tool
def remove_item(item_name: str, inventory: List[str]) -> dict:
    """
    Remove item do inventário.

    Args:
        item_name: Nome do item
        inventory: Lista atual de itens

    Returns:
        dict com resultado
    """
    item_upper = item_name.upper().replace(" ", "_")

    if item_upper not in inventory:
        return {
            "success": False,
            "item": item_upper,
            "inventory": inventory,
            "message": f"Você não tem {item_upper}",
        }

    new_inventory = [i for i in inventory if i != item_upper]

    return {
        "success": True,
        "item": item_upper,
        "inventory": new_inventory,
        "message": f"✗ {item_upper} removido do inventário",
    }


@tool
def check_item(item_name: str, inventory: List[str]) -> dict:
    """
    Verifica se personagem tem um item.

    Args:
        item_name: Nome do item
        inventory: Lista atual de itens

    Returns:
        dict: {
            'has_item': bool,
            'item': str,
            'message': str
        }
    """
    item_upper = item_name.upper().replace(" ", "_")
    has_item = item_upper in inventory

    return {
        "has_item": has_item,
        "item": item_upper,
        "message": f'Você {"TEM" if has_item else "NÃO TEM"} {item_upper}',
    }


@tool
def use_item(item_name: str, item_type: str, character_stats: dict) -> dict:
    """
    Usa um item (poção, etc).

    Args:
        item_name: Nome do item
        item_type: Tipo (potion_luck, potion_skill, potion_stamina)
        character_stats: Stats atuais do personagem

    Returns:
        dict com novos stats
    """
    effects = {
        "potion_luck": {"luck": 1},
        "potion_skill": {"skill": 1},
        "potion_stamina": {"stamina": 4},
    }

    if item_type not in effects:
        return {"success": False, "message": f"Não é possível usar {item_name}"}

    effect = effects[item_type]
    stat_name = list(effect.keys())[0]
    bonus = effect[stat_name]

    old_value = character_stats.get(stat_name, 0)
    new_value = old_value + bonus
    initial_value = character_stats.get(f"initial_{stat_name}", new_value)

    if new_value > initial_value:
        new_value = initial_value

    return {
        "success": True,
        "item": item_name,
        "stat": stat_name,
        "old_value": old_value,
        "new_value": new_value,
        "message": f"Você usou {item_name}! {stat_name.upper()} {old_value} → {new_value}",
    }
