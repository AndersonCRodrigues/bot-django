"""
🎯 Parser de Ações do Jogador

Detecta a intenção do jogador de forma determinística (SEM LLM).

Tipos de ação suportados:
- pickup: pegar item
- use_item: usar item
- talk: conversar com NPC
- navigation: ir para outra seção
- combat: atacar inimigo
- test_luck: testar sorte
- test_skill: testar habilidade
- examine: examinar algo
- exploration: exploração geral (fallback)
"""

import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("game.action_parser")


def parse_player_action(action_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Detecta a intenção do jogador a partir do texto da ação.

    Args:
        action_text: Texto da ação do jogador
        context: Contexto opcional (NPCs presentes, itens disponíveis, etc)

    Returns:
        {
            'type': str,  # tipo de ação
            'target': str,  # alvo da ação (item, NPC, etc)
            'confidence': float,  # confiança na detecção (0-1)
            'raw_action': str  # ação original
        }
    """
    action_lower = action_text.lower().strip()
    context = context or {}

    # ========== PICKUP ITEM ==========
    pickup_patterns = [
        r'peg(?:o|ar|ue) (?:o |a |um |uma )?(\w+)',
        r'apanh(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'colh(?:o|er|a) (?:o |a |um |uma )?(\w+)',
        r'obtenho (?:o |a |um |uma )?(\w+)',
        r'me apodero (?:d)?(?:o |a )?(\w+)',
    ]

    for pattern in pickup_patterns:
        match = re.search(pattern, action_lower)
        if match:
            item = match.group(1).strip().title()
            logger.debug(f"[parse_action] Detectado: pickup de '{item}'")
            return {
                'type': 'pickup',
                'target': item,
                'confidence': 0.95,
                'raw_action': action_text
            }

    # ========== USE ITEM ==========
    use_patterns = [
        r'us(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'utiliz(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'empunh(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'beb(?:o|er|e) (?:o |a |um |uma )?(\w+)',
        r'com(?:o|er|e) (?:o |a |um |uma )?(\w+)',
    ]

    for pattern in use_patterns:
        match = re.search(pattern, action_lower)
        if match:
            item = match.group(1).strip().title()
            logger.debug(f"[parse_action] Detectado: use_item '{item}'")
            return {
                'type': 'use_item',
                'target': item,
                'confidence': 0.95,
                'raw_action': action_text
            }

    # ========== TALK TO NPC ==========
    talk_patterns = [
        r'fal(?:o|ar|e) com (?:o |a )?(\w+)',
        r'convers(?:o|ar|e) com (?:o |a )?(\w+)',
        r'pergunt(?:o|ar|e) (?:ao |à |para )?(\w+)',
        r'digo (?:ao |à )?(\w+)',
        r'questiono (?:o |a )?(\w+)',
    ]

    for pattern in talk_patterns:
        match = re.search(pattern, action_lower)
        if match:
            npc = match.group(1).strip().title()
            logger.debug(f"[parse_action] Detectado: talk com '{npc}'")
            return {
                'type': 'talk',
                'target': npc,
                'confidence': 0.9,
                'raw_action': action_text
            }

    # ========== COMBAT ==========
    combat_keywords = ['atac', 'lut', 'golpe', 'invest', 'desferir', 'combat', 'batalh']
    if any(keyword in action_lower for keyword in combat_keywords):
        # Tentar extrair nome do inimigo (se mencionado)
        enemy_match = re.search(r'(?:atac|lut)(?:o|ar|e) (?:o |a |um |uma )?(\w+)', action_lower)
        target = enemy_match.group(1).strip().title() if enemy_match else 'enemy'

        logger.debug(f"[parse_action] Detectado: combat contra '{target}'")
        return {
            'type': 'combat',
            'target': target,
            'confidence': 0.9,
            'raw_action': action_text
        }

    # ========== NAVIGATION ==========
    navigation_patterns = [
        r'v(?:ou|á|amos) (?:para )?(?:o |a )?(\w+)',
        r'sig(?:o|a|amos) (?:para )?(?:o |a )?(\w+)',
        r'vou (?:pelo |pela )?(\w+)',
        r'sigo (?:pelo |pela )?(\w+)',
        r'entro (?:no |na )?(\w+)',
        r'avanço (?:para )?(?:o |a )?(\w+)',
    ]

    for pattern in navigation_patterns:
        match = re.search(pattern, action_lower)
        if match:
            direction = match.group(1).strip().title()
            logger.debug(f"[parse_action] Detectado: navigation para '{direction}'")
            return {
                'type': 'navigation',
                'target': direction,
                'confidence': 0.85,
                'raw_action': action_text
            }

    # ========== TEST LUCK ==========
    if 'sorte' in action_lower or 'testar sorte' in action_lower:
        logger.debug("[parse_action] Detectado: test_luck")
        return {
            'type': 'test_luck',
            'target': None,
            'confidence': 1.0,
            'raw_action': action_text
        }

    # ========== TEST SKILL ==========
    if 'habilidade' in action_lower or 'testar habilidade' in action_lower:
        logger.debug("[parse_action] Detectado: test_skill")
        return {
            'type': 'test_skill',
            'target': None,
            'confidence': 1.0,
            'raw_action': action_text
        }

    # ========== EXAMINE ==========
    examine_patterns = [
        r'examin(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'inspect(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'observ(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
        r'olh(?:o|ar|e) (?:para )?(?:o |a )?(\w+)',
        r'investigu(?:o|ar|e) (?:o |a |um |uma )?(\w+)',
    ]

    for pattern in examine_patterns:
        match = re.search(pattern, action_lower)
        if match:
            target = match.group(1).strip().title()
            logger.debug(f"[parse_action] Detectado: examine '{target}'")
            return {
                'type': 'examine',
                'target': target,
                'confidence': 0.8,
                'raw_action': action_text
            }

    # ========== EXPLORATION (FALLBACK) ==========
    logger.debug(f"[parse_action] Fallback: exploration genérica")
    return {
        'type': 'exploration',
        'target': None,
        'confidence': 0.5,
        'raw_action': action_text
    }


def extract_target_from_action(action_text: str, candidates: List[str]) -> Optional[str]:
    """
    Extrai o alvo específico da ação baseado em uma lista de candidatos.

    Útil para resolver ambiguidades como:
    - "pego a espada" quando há ["espada", "escudo", "tocha"]
    - "falo com o guarda" quando há ["Guarda", "Mercador"]

    Args:
        action_text: Texto da ação
        candidates: Lista de possíveis alvos (NPCs, itens disponíveis)

    Returns:
        Nome do alvo encontrado ou None
    """
    action_lower = action_text.lower()

    for candidate in candidates:
        if candidate.lower() in action_lower:
            logger.debug(f"[extract_target] Encontrado: '{candidate}' em '{action_text}'")
            return candidate

    return None


def is_combat_action(action_text: str) -> bool:
    """Verifica se a ação é de combate."""
    combat_keywords = ['atac', 'lut', 'golpe', 'invest', 'desferir', 'combat']
    return any(keyword in action_text.lower() for keyword in combat_keywords)


def is_navigation_action(action_text: str) -> bool:
    """Verifica se a ação é de navegação."""
    nav_keywords = ['vou', 'sigo', 'entro', 'vá', 'avanço', 'caminho']
    return any(keyword in action_text.lower() for keyword in nav_keywords)


def is_test_action(action_text: str) -> bool:
    """Verifica se a ação é teste de sorte/habilidade."""
    return 'sorte' in action_text.lower() or 'habilidade' in action_text.lower()
