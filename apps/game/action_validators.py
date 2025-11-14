"""
🎯 Validadores Rígidos de Ações

Valida se ações do jogador são possíveis baseado no RAG (fonte de verdade).

Previne:
- Pegar itens que não existem na seção
- Navegar para seções não conectadas
- Usar itens que não estão no inventário
- Ações impossíveis no contexto atual
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("game.validators")


class ValidationResult:
    """Resultado de uma validação."""

    def __init__(self, valid: bool, message: Optional[str] = None, reason: Optional[str] = None):
        self.valid = valid
        self.message = message or ("Ação válida" if valid else "Ação inválida")
        self.reason = reason or ("ok" if valid else "unknown")

    def __bool__(self):
        return self.valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            'valid': self.valid,
            'message': self.message,
            'reason': self.reason
        }


def validate_pickup_item(
    item_name: str,
    available_items: List[str],
    inventory: List[str],
    max_inventory_size: int = 12
) -> ValidationResult:
    """
    Valida se o jogador pode pegar um item.

    Args:
        item_name: Nome do item que o jogador quer pegar
        available_items: Lista de itens disponíveis na seção (whitelist do RAG)
        inventory: Inventário atual do jogador
        max_inventory_size: Tamanho máximo do inventário

    Returns:
        ValidationResult com resultado da validação
    """
    # Normalizar nomes para comparação (case-insensitive)
    item_lower = item_name.lower()
    available_lower = [item.lower() for item in available_items]

    # Verificar se item existe na seção
    if item_lower not in available_lower:
        logger.warning(f"[validate_pickup] Item '{item_name}' não está disponível. Disponíveis: {available_items}")
        return ValidationResult(
            valid=False,
            message=f"Você não vê nenhum(a) {item_name} aqui.",
            reason="item_not_available"
        )

    # Verificar se inventário está cheio
    if len(inventory) >= max_inventory_size:
        logger.warning(f"[validate_pickup] Inventário cheio ({len(inventory)}/{max_inventory_size})")
        return ValidationResult(
            valid=False,
            message=f"Seu inventário está cheio! Você carrega {len(inventory)} itens. Solte algo primeiro.",
            reason="inventory_full"
        )

    # Verificar se já tem o item
    if item_lower in [inv_item.lower() for inv_item in inventory]:
        logger.info(f"[validate_pickup] Jogador já tem '{item_name}'")
        return ValidationResult(
            valid=False,
            message=f"Você já tem {item_name}.",
            reason="already_have_item"
        )

    logger.info(f"[validate_pickup] ✓ Pode pegar '{item_name}'")
    return ValidationResult(valid=True)


def validate_use_item(
    item_name: str,
    inventory: List[str],
    context: Optional[str] = None
) -> ValidationResult:
    """
    Valida se o jogador pode usar um item.

    Args:
        item_name: Nome do item que o jogador quer usar
        inventory: Inventário atual do jogador
        context: Contexto opcional (ex: "combat", "locked_door")

    Returns:
        ValidationResult com resultado da validação
    """
    # Normalizar para comparação
    item_lower = item_name.lower()
    inventory_lower = [item.lower() for item in inventory]

    # Verificar se tem o item
    if item_lower not in inventory_lower:
        logger.warning(f"[validate_use_item] Item '{item_name}' não está no inventário")
        return ValidationResult(
            valid=False,
            message=f"Você não tem {item_name}.",
            reason="item_not_in_inventory"
        )

    # Validações de contexto específicas
    if context == "combat":
        # Apenas certos itens são usáveis em combate
        combat_items = ['poção', 'elixir', 'espada', 'escudo', 'arco', 'flecha']
        if not any(ci in item_lower for ci in combat_items):
            return ValidationResult(
                valid=False,
                message=f"Você não pode usar {item_name} durante o combate.",
                reason="item_not_usable_in_combat"
            )

    logger.info(f"[validate_use_item] ✓ Pode usar '{item_name}'")
    return ValidationResult(valid=True)


def validate_navigation(
    target_section: Optional[int],
    available_exits: List[int],
    current_section: int
) -> ValidationResult:
    """
    Valida se o jogador pode navegar para uma seção.

    Args:
        target_section: Seção alvo (número)
        available_exits: Lista de seções conectadas (exits do RAG)
        current_section: Seção atual

    Returns:
        ValidationResult com resultado da validação
    """
    if target_section is None:
        logger.warning("[validate_navigation] Nenhuma seção alvo especificada")
        return ValidationResult(
            valid=False,
            message="Para onde você quer ir?",
            reason="no_target"
        )

    # Verificar se exit existe
    if target_section not in available_exits:
        logger.warning(
            f"[validate_navigation] Seção {target_section} não está conectada. "
            f"Exits disponíveis: {available_exits}"
        )
        return ValidationResult(
            valid=False,
            message=f"Não há caminho para lá daqui.",
            reason="invalid_exit"
        )

    # Não permitir voltar muito (anti-exploit)
    if target_section < current_section - 20:
        logger.warning(f"[validate_navigation] Tentativa de voltar muito (de {current_section} para {target_section})")
        return ValidationResult(
            valid=False,
            message="Você não pode voltar tanto na história.",
            reason="backward_too_far"
        )

    logger.info(f"[validate_navigation] ✓ Pode ir de {current_section} para {target_section}")
    return ValidationResult(valid=True)


def validate_talk_to_npc(
    npc_name: str,
    available_npcs: List[str]
) -> ValidationResult:
    """
    Valida se o jogador pode falar com um NPC.

    Args:
        npc_name: Nome do NPC
        available_npcs: Lista de NPCs presentes na seção (do RAG)

    Returns:
        ValidationResult com resultado da validação
    """
    # Normalizar
    npc_lower = npc_name.lower()
    npcs_lower = [npc.lower() for npc in available_npcs]

    if npc_lower not in npcs_lower:
        logger.warning(f"[validate_talk] NPC '{npc_name}' não está presente. Disponíveis: {available_npcs}")
        return ValidationResult(
            valid=False,
            message=f"Não há ninguém chamado {npc_name} aqui.",
            reason="npc_not_present"
        )

    logger.info(f"[validate_talk] ✓ Pode falar com '{npc_name}'")
    return ValidationResult(valid=True)


def validate_combat_action(
    in_combat: bool,
    combat_data: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Valida se ação de combate é possível.

    Args:
        in_combat: Se está em combate atualmente
        combat_data: Dados do combate

    Returns:
        ValidationResult com resultado da validação
    """
    if not in_combat:
        logger.warning("[validate_combat] Tentativa de atacar fora de combate")
        return ValidationResult(
            valid=False,
            message="Não há ninguém para atacar aqui.",
            reason="not_in_combat"
        )

    if not combat_data or 'enemy_stamina' not in combat_data:
        logger.error("[validate_combat] Dados de combate inválidos")
        return ValidationResult(
            valid=False,
            message="Erro nos dados de combate.",
            reason="invalid_combat_data"
        )

    if combat_data.get('enemy_stamina', 0) <= 0:
        logger.info("[validate_combat] Inimigo já derrotado")
        return ValidationResult(
            valid=False,
            message="O inimigo já foi derrotado.",
            reason="enemy_already_defeated"
        )

    logger.info("[validate_combat] ✓ Pode atacar")
    return ValidationResult(valid=True)


def validate_test_action(
    test_type: str,
    character_stats: Dict[str, int],
    flags: Dict[str, Any]
) -> ValidationResult:
    """
    Valida se teste de sorte/habilidade é necessário.

    Args:
        test_type: "luck" ou "skill"
        character_stats: Stats do personagem
        flags: Flags da seção (do RAG)

    Returns:
        ValidationResult com resultado da validação
    """
    if test_type == "luck":
        if character_stats.get('luck', 0) <= 0:
            return ValidationResult(
                valid=False,
                message="Sua SORTE está zerada! Você não pode testar sorte.",
                reason="no_luck_remaining"
            )

        # Verificar se seção requer teste
        if not flags.get('luck_test_required', False):
            logger.info("[validate_test] Teste de sorte não é obrigatório aqui")
            # Permitir, mas avisar
            return ValidationResult(
                valid=True,
                message="Você pode testar sua sorte, mas não é obrigatório aqui.",
                reason="optional_test"
            )

    elif test_type == "skill":
        if character_stats.get('skill', 0) <= 0:
            return ValidationResult(
                valid=False,
                message="Sua HABILIDADE está zerada!",
                reason="no_skill"
            )

    logger.info(f"[validate_test] ✓ Pode testar {test_type}")
    return ValidationResult(valid=True)
