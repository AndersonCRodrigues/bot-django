from typing import Dict, Optional, List
from langchain_core.tools import tool
from django.conf import settings


def get_weaviate_client():
    """Retorna cliente Weaviate."""
    import weaviate

    return weaviate.Client(settings.WEAVIATE_URL)


@tool
def get_current_section(section_number: int, adventure_name: str) -> dict:
    """
    Busca informações da seção atual no Weaviate.

    Args:
        section_number: Número da seção (1-400)
        adventure_name: Nome da aventura (classe no Weaviate)

    Returns:
        dict: {
            'section_number': int,
            'text': str,
            'npcs': List[str],
            'items': List[str],
            'exits': List[int],
            'combat': dict | None,
            'tests': dict | None
        }
    """
    try:
        client = get_weaviate_client()

        result = (
            client.query.get(
                adventure_name,
                ["section_number", "text", "npcs", "items", "exits", "combat", "tests"],
            )
            .with_where(
                {
                    "path": ["section_number"],
                    "operator": "Equal",
                    "valueInt": section_number,
                }
            )
            .with_limit(1)
            .do()
        )

        if result["data"]["Get"][adventure_name]:
            return result["data"]["Get"][adventure_name][0]

        return {"error": f"Seção {section_number} não encontrada"}

    except Exception as e:
        return {"error": f"Erro ao buscar seção: {str(e)}"}


@tool
def try_move_to(
    target_section: int,
    current_section: int,
    current_exits: List[int],
    inventory: List[str],
    adventure_name: str,
) -> dict:
    """
    Valida e executa movimento para nova seção.

    Args:
        target_section: Seção de destino
        current_section: Seção atual
        current_exits: Lista de saídas permitidas da seção atual
        inventory: Inventário do personagem
        adventure_name: Nome da aventura

    Returns:
        dict: {
            'success': bool,
            'reason': str,
            'new_section': dict (se sucesso)
        }

    Validações:
        1. Seção destino está nas saídas?
        2. Personagem tem itens necessários?
        3. Pré-requisitos cumpridos?
    """
    if target_section not in current_exits:
        return {
            "success": False,
            "reason": f"Não há caminho direto da seção {current_section} para {target_section}. Saídas disponíveis: {current_exits}",
        }

    target = get_current_section.invoke(
        {"section_number": target_section, "adventure_name": adventure_name}
    )

    if "error" in target:
        return {
            "success": False,
            "reason": f'Erro ao acessar seção {target_section}: {target["error"]}',
        }

    required_items = target.get("required_items", [])
    if required_items:
        missing = [item for item in required_items if item not in inventory]
        if missing:
            return {
                "success": False,
                "reason": f'Você precisa ter: {", ".join(missing)}',
            }

    return {
        "success": True,
        "reason": f"Movimento validado para seção {target_section}",
        "new_section": target,
    }
