"""
Handler de consumíveis (rações e poções) para Fighting Fantasy RPG.

Processa ações de consumo de rações e poções seguindo as regras dos livros-jogo.
"""

import logging
from apps.characters.models import Character
from apps.game.models import GameSession

logger = logging.getLogger("game.consumables")


def handle_consumable_action(action: str, character: Character, session: GameSession) -> dict:
    """
    Processa ações de consumíveis.

    Args:
        action: Nome da ação (eat_provision, use_potion1, use_potion2)
        character: Character do jogador
        session: GameSession atual

    Returns:
        dict com resultado da ação ou None se não for ação de consumível
    """
    # Verificar se é ação de consumível
    if not any(keyword in action.lower() for keyword in ['eat_provision', 'use_potion']):
        return None

    # Verificar morte
    if character.stamina <= 0:
        return {
            'success': False,
            'narrative': '❌ Você não pode usar consumíveis estando morto!',
            'stats': get_character_stats(character),
            'inventory': session.inventory,
            'current_section': session.current_section,
            'game_over': True,
            'victory': False,
            'turn_number': len(session.history),
            'in_combat': session.flags.get('in_combat', False),
            'character': get_character_data(character),
            'flags': session.flags,
        }

    # Verificar combate
    in_combat = session.flags.get('in_combat', False)
    if in_combat:
        return {
            'success': False,
            'narrative': '❌ Você não pode usar consumíveis durante o combate! Espere o combate terminar.',
            'stats': get_character_stats(character),
            'inventory': session.inventory,
            'current_section': session.current_section,
            'game_over': False,
            'victory': False,
            'turn_number': len(session.history),
            'in_combat': True,
            'character': get_character_data(character),
            'flags': session.flags,
        }

    # Processar ação específica
    if 'eat_provision' in action.lower():
        return eat_provision(character, session)
    elif 'use_potion1' in action.lower():
        return use_potion(character, session, 1)
    elif 'use_potion2' in action.lower():
        return use_potion(character, session, 2)

    return None


def eat_provision(character: Character, session: GameSession) -> dict:
    """
    Come uma ração, restaurando 4 de ENERGIA.

    Regras:
    - Restaura 4 pontos de ENERGIA
    - Não pode exceder ENERGIA inicial
    - Consome 1 ração do inventário
    """
    if character.provisions <= 0:
        return create_error_response(
            '❌ Você não tem rações!',
            character, session
        )

    # Verificar se já está com energia máxima
    if character.stamina >= character.initial_stamina:
        return create_error_response(
            '❌ Sua ENERGIA já está no máximo!',
            character, session
        )

    # Restaurar energia
    old_stamina = character.stamina
    character.stamina = min(character.stamina + 4, character.initial_stamina)
    character.provisions -= 1
    character.save()

    # Adicionar ao histórico
    session.add_to_history({
        'player_action': 'Comer uma ração',
        'narrative': f'🥖 Você come uma ração deliciosa e recupera {character.stamina - old_stamina} pontos de ENERGIA! '
                     f'(ENERGIA: {old_stamina} → {character.stamina})',
        'stamina': character.stamina,
        'provisions': character.provisions,
        'action_type': 'consumable',
    })

    logger.info(f"[eat_provision] ENERGIA {old_stamina} → {character.stamina}, Rações: {character.provisions}")

    return {
        'success': True,
        'narrative': f'🥖 Você come uma ração deliciosa e recupera {character.stamina - old_stamina} pontos de ENERGIA!\n\n'
                     f'ENERGIA: {old_stamina} → {character.stamina}\n'
                     f'Rações restantes: {character.provisions}',
        'stats': get_character_stats(character),
        'inventory': session.inventory,
        'current_section': session.current_section,
        'game_over': False,
        'victory': False,
        'turn_number': len(session.history),
        'in_combat': False,
        'character': get_character_data(character),
        'flags': session.flags,
    }


def use_potion(character: Character, session: GameSession, potion_num: int) -> dict:
    """
    Usa uma poção (Sorte, Habilidade ou Energia).

    Args:
        potion_num: 1 ou 2 (potion1 ou potion2)

    Regras:
    - Poção de Sorte: +1 SORTE (max inicial)
    - Poção de Habilidade: +1 HABILIDADE (max inicial)
    - Poção de Energia: +4 ENERGIA (max inicial)
    - Poção é removida após uso
    """
    potion_attr = 'potion1' if potion_num == 1 else 'potion2'
    potion_type = getattr(character, potion_attr, None)

    if not potion_type:
        return create_error_response(
            f'❌ Você não tem poção {potion_num}!',
            character, session
        )

    # Configurações de poções
    potion_configs = {
        'luck': {
            'name': 'Poção de Sorte',
            'icon': '🍀',
            'stat': 'luck',
            'bonus': 1,
            'initial_attr': 'initial_luck'
        },
        'skill': {
            'name': 'Poção de Habilidade',
            'icon': '⚔️',
            'stat': 'skill',
            'bonus': 1,
            'initial_attr': 'initial_skill'
        },
        'stamina': {
            'name': 'Poção de Energia',
            'icon': '❤️',
            'stat': 'stamina',
            'bonus': 4,
            'initial_attr': 'initial_stamina'
        }
    }

    config = potion_configs.get(potion_type)
    if not config:
        return create_error_response(
            f'❌ Tipo de poção inválido: {potion_type}',
            character, session
        )

    # Verificar se já está no máximo
    current_value = getattr(character, config['stat'])
    max_value = getattr(character, config['initial_attr'])

    if current_value >= max_value:
        return create_error_response(
            f'❌ Seu {config["stat"].upper()} já está no máximo!',
            character, session
        )

    # Aplicar bônus
    old_value = current_value
    new_value = min(current_value + config['bonus'], max_value)
    setattr(character, config['stat'], new_value)

    # Remover poção do personagem
    setattr(character, potion_attr, None)

    # Remover poção do equipment
    potion_name = Character.POTION_CHOICES.get(potion_type)
    if potion_name in character.equipment:
        character.equipment.remove(potion_name)

    character.save()

    # Adicionar ao histórico
    session.add_to_history({
        'player_action': f'Usar {config["name"]}',
        'narrative': f'{config["icon"]} Você bebe a {config["name"]} e ganha {new_value - old_value} pontos de {config["stat"].upper()}! '
                     f'({config["stat"].upper()}: {old_value} → {new_value})',
        config['stat']: new_value,
        'action_type': 'consumable',
    })

    logger.info(f"[use_potion] {config['name']}: {config['stat'].upper()} {old_value} → {new_value}")

    return {
        'success': True,
        'narrative': f'{config["icon"]} Você bebe a {config["name"]} e sente seu poder aumentar!\n\n'
                     f'{config["stat"].upper()}: {old_value} → {new_value}\n\n'
                     f'A poção foi consumida e desapareceu.',
        'stats': get_character_stats(character),
        'inventory': session.inventory,
        'current_section': session.current_section,
        'game_over': False,
        'victory': False,
        'turn_number': len(session.history),
        'in_combat': False,
        'character': get_character_data(character),
        'flags': session.flags,
    }


def create_error_response(message: str, character: Character, session: GameSession) -> dict:
    """Cria resposta de erro padrão."""
    return {
        'success': False,
        'narrative': message,
        'stats': get_character_stats(character),
        'inventory': session.inventory,
        'current_section': session.current_section,
        'game_over': False,
        'victory': False,
        'turn_number': len(session.history),
        'in_combat': session.flags.get('in_combat', False),
        'character': get_character_data(character),
        'flags': session.flags,
    }


def get_character_stats(character: Character) -> dict:
    """Retorna stats do personagem."""
    return {
        'skill': character.skill,
        'stamina': character.stamina,
        'luck': character.luck,
        'gold': character.gold,
        'provisions': character.provisions,
    }


def get_character_data(character: Character) -> dict:
    """Retorna dados completos do personagem para atualizar UI."""
    return {
        'skill': character.skill,
        'stamina': character.stamina,
        'luck': character.luck,
        'initial_skill': character.initial_skill,
        'initial_stamina': character.initial_stamina,
        'initial_luck': character.initial_luck,
        'gold': character.gold,
        'provisions': character.provisions,
        'potion1': character.potion1,
        'potion2': character.potion2,
    }
