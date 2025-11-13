from typing import Dict
from langchain_core.tools import tool


@tool
def update_character_stats(character_id: str, updates: Dict[str, int]) -> dict:
    """
    Atualiza stats do personagem no MongoDB.

    Args:
        character_id: ID do personagem
        updates: Dict com alterações (ex: {'stamina': -2, 'gold': +10})

    Returns:
        dict: {
            'success': bool,
            'character_id': str,
            'updates': dict,
            'new_stats': dict,
            'message': str
        }
    """
    from apps.characters.models import Character
    from bson import ObjectId

    try:
        collection = Character.get_collection()
        character_doc = collection.find_one({"_id": ObjectId(character_id)})

        if not character_doc:
            return {"success": False, "error": "Personagem não encontrado"}

        new_values = {}
        changes = []

        for stat, change in updates.items():
            if stat not in character_doc:
                continue

            old_value = character_doc[stat]
            new_value = old_value + change

            if stat in ["stamina", "skill", "luck"]:
                new_value = max(0, new_value)

            new_values[stat] = new_value
            changes.append(f"{stat.upper()}: {old_value} → {new_value}")

        collection.update_one({"_id": ObjectId(character_id)}, {"$set": new_values})

        return {
            "success": True,
            "character_id": character_id,
            "updates": updates,
            "new_stats": new_values,
            "message": f'Stats atualizados: {", ".join(changes)}',
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_character_state(character_id: str) -> dict:
    """
    Busca estado atual do personagem.

    Args:
        character_id: ID do personagem

    Returns:
        dict com todos os stats atuais
    """
    from apps.characters.models import Character
    from bson import ObjectId

    try:
        collection = Character.get_collection()
        character_doc = collection.find_one({"_id": ObjectId(character_id)})

        if not character_doc:
            return {"error": "Personagem não encontrado"}

        return {
            "name": character_doc["name"],
            "skill": character_doc["skill"],
            "stamina": character_doc["stamina"],
            "luck": character_doc["luck"],
            "initial_skill": character_doc["initial_skill"],
            "initial_stamina": character_doc["initial_stamina"],
            "initial_luck": character_doc["initial_luck"],
            "gold": character_doc["gold"],
            "provisions": character_doc["provisions"],
            "equipment": character_doc["equipment"],
        }

    except Exception as e:
        return {"error": str(e)}
