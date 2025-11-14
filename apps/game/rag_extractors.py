"""
Extratores inteligentes de informações do RAG.

Funções para extrair automaticamente:
- Exits (seções conectadas)
- Flags (portas trancadas, combate, testes, etc)
- NPCs presentes
- Requisitos (itens necessários, testes obrigatórios)
"""

import re
import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger("game.rag_extractors")


def extract_exits_from_content(section_content: str) -> List[int]:
    """
    Extrai números de seções conectadas do texto.

    Padrões comuns em Fighting Fantasy:
    - "vá para 285"
    - "seção 42"
    - "parágrafo 156"
    - "volte para 12"
    - "Se você tem a chave, vá para 300"

    Args:
        section_content: Texto da seção

    Returns:
        Lista ordenada de seções conectadas
    """
    exits: Set[int] = set()

    # Padrões de referência a seções
    patterns = [
        r'v[áa] para (?:a se[çc][ãa]o )?(\d+)',
        r'se[çc][ãa]o (\d+)',
        r'par[áa]grafo (\d+)',
        r'volte para (?:a se[çc][ãa]o )?(\d+)',
        r'retorne (?:para |[àa] se[çc][ãa]o )?(\d+)',
        r'siga para (?:a se[çc][ãa]o )?(\d+)',
        r'escolha (?:a se[çc][ãa]o )?(\d+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, section_content, re.IGNORECASE)
        for match in matches:
            try:
                section_num = int(match)
                if 1 <= section_num <= 400:  # Validar range típico
                    exits.add(section_num)
            except ValueError:
                continue

    # Ordenar e retornar
    return sorted(list(exits))


def extract_flags_from_content(section_content: str, section_number: int) -> Dict[str, Any]:
    """
    Extrai flags automaticamente do conteúdo da seção.

    Detecta:
    - Combate obrigatório
    - Testes de sorte/habilidade
    - Portas/passagens bloqueadas
    - Itens obrigatórios
    - NPCs importantes
    - Perigos/armadilhas

    Args:
        section_content: Texto da seção
        section_number: Número da seção (para contexto)

    Returns:
        Dict com flags extraídos
    """
    flags = {}
    content_lower = section_content.lower()

    # Detectar combate
    combat_keywords = [
        'lute', 'combate', 'ataque', 'batalha', 'enfrente',
        'habilidade de combate', 'energia do', 'ataca você'
    ]
    if any(keyword in content_lower for keyword in combat_keywords):
        flags['combat_required'] = True
        logger.debug(f"[extract_flags] Seção {section_number}: Combate detectado")

    # Detectar testes
    if 'teste sua sorte' in content_lower or 'testar a sorte' in content_lower:
        flags['luck_test_required'] = True
        logger.debug(f"[extract_flags] Seção {section_number}: Teste de sorte detectado")

    if 'teste sua habilidade' in content_lower or 'testar a habilidade' in content_lower:
        flags['skill_test_required'] = True
        logger.debug(f"[extract_flags] Seção {section_number}: Teste de habilidade detectado")

    # Detectar portas/bloqueios
    lock_keywords = [
        'porta trancada', 'porta bloqueada', 'porta fechada',
        'bloqueado', 'trancado', 'fechado com cadeado'
    ]
    if any(keyword in content_lower for keyword in lock_keywords):
        flags['door_locked'] = True
        logger.debug(f"[extract_flags] Seção {section_number}: Porta trancada detectada")

    # Detectar requisito de chave
    key_patterns = [
        r'voc[êe] precisa (?:de |da )?chave',
        r'se (?:voc[êe] |)tiver (?:a |uma )?chave',
        r'usar a chave',
        r'chave (?:de |)(\w+)',  # chave de ouro, chave de prata, etc
    ]
    for pattern in key_patterns:
        match = re.search(pattern, content_lower)
        if match:
            flags['requires_key'] = True
            # Tentar extrair tipo de chave
            if match.groups():
                key_type = match.group(1)
                flags['key_type'] = key_type.upper()
            logger.debug(f"[extract_flags] Seção {section_number}: Requer chave")
            break

    # Detectar itens obrigatórios genéricos
    item_patterns = [
        r'voc[êe] precisa (?:de |do |da )?(\w+)',
        r'se (?:voc[êe] |)tiver (?:o |a |um |uma )?(\w+)',
        r'sem (?:o |a )?(\w+), voc[êe]',
    ]
    required_items = []
    for pattern in item_patterns:
        matches = re.findall(pattern, content_lower)
        for match in matches:
            item = match.strip()
            # Filtrar palavras comuns que não são itens
            if item not in ['que', 'isso', 'ele', 'ela', 'um', 'uma', 'o', 'a']:
                required_items.append(item.upper())

    if required_items:
        flags['required_items'] = list(set(required_items))
        logger.debug(f"[extract_flags] Seção {section_number}: Itens requeridos: {required_items}")

    # Detectar armadilhas
    trap_keywords = ['armadilha', 'armadilhado', 'alçapão', 'cilada', 'veneno']
    if any(keyword in content_lower for keyword in trap_keywords):
        flags['trap_present'] = True
        logger.debug(f"[extract_flags] Seção {section_number}: Armadilha detectada")

    # Detectar perigo mortal
    death_keywords = [
        'voc[êe] morre', 'sua aventura termina', 'fim da jornada',
        'morte instantânea', 'cai morto'
    ]
    for keyword in death_keywords:
        if re.search(keyword, content_lower):
            flags['instant_death_possible'] = True
            logger.warning(f"[extract_flags] Seção {section_number}: Perigo mortal detectado!")
            break

    # Detectar escolha importante (múltiplos caminhos)
    if len(extract_exits_from_content(section_content)) >= 3:
        flags['important_choice'] = True
        logger.debug(f"[extract_flags] Seção {section_number}: Escolha importante (3+ exits)")

    return flags


def extract_npcs_from_content(section_content: str) -> List[str]:
    """
    Extrai NPCs mencionados no texto.

    Busca por:
    - Nomes próprios capitalizados
    - Títulos (Rei, Mago, Guarda, etc)
    - Criaturas específicas nomeadas

    Args:
        section_content: Texto da seção

    Returns:
        Lista de NPCs detectados
    """
    npcs = []

    # Padrão para títulos comuns
    title_pattern = r'\b(Rei|Rainha|Príncipe|Princesa|Mago|Feiticeiro|Guarda|Capitão|Eremita|Druida|Mercador|Ferreiro)\b'
    titles = re.findall(title_pattern, section_content, re.IGNORECASE)
    npcs.extend([t.title() for t in titles])

    # Padrão para nomes próprios (palavras capitalizadas no meio de frases)
    # Evitar primeira palavra da sentença
    name_pattern = r'(?<=[.!?]\s)([A-Z][a-zà-ú]+(?:\s+[A-Z][a-zà-ú]+)?)'
    names = re.findall(name_pattern, section_content)
    npcs.extend(names)

    # Criaturas nomeadas específicas (comum em Fighting Fantasy)
    creature_pattern = r'\b([A-Z][a-zà-ú]+) (?:o |a )(Orc|Goblin|Dragão|Troll|Gigante|Demônio)\b'
    creatures = re.findall(creature_pattern, section_content)
    npcs.extend([f"{name} {creature}" for name, creature in creatures])

    return list(set(npcs))  # Remove duplicatas


def extract_combat_info(section_content: str) -> Dict[str, Any]:
    """
    Extrai informações de combate do texto.

    Busca por:
    - Nome do inimigo
    - HABILIDADE do inimigo
    - ENERGIA do inimigo
    - Notas especiais do combate

    Args:
        section_content: Texto da seção

    Returns:
        {
            'enemy_name': str,
            'enemy_skill': int,
            'enemy_stamina': int,
            'special_rules': str
        }
    """
    combat_info = {}

    # Padrão típico: "GOBLIN HABILIDADE 5 ENERGIA 4"
    combat_pattern = r'([A-ZÀ-Ú\s]+)\s+HABILIDADE\s+(\d+)\s+ENERGIA\s+(\d+)'
    match = re.search(combat_pattern, section_content, re.IGNORECASE)

    if match:
        enemy_name = match.group(1).strip().title()
        enemy_skill = int(match.group(2))
        enemy_stamina = int(match.group(3))

        combat_info = {
            'enemy_name': enemy_name,
            'enemy_skill': enemy_skill,
            'enemy_stamina': enemy_stamina,
            'enemy_initial_stamina': enemy_stamina
        }

        logger.info(
            f"[extract_combat] Combate: {enemy_name} "
            f"(HABILIDADE {enemy_skill}, ENERGIA {enemy_stamina})"
        )

    # Buscar regras especiais
    special_rules = []
    if 'veneno' in section_content.lower():
        special_rules.append('Ataque venenoso')
    if 'regenera' in section_content.lower():
        special_rules.append('Regeneração')
    if 'fogo' in section_content.lower():
        special_rules.append('Ataque de fogo')

    if special_rules:
        combat_info['special_rules'] = special_rules

    return combat_info


def consolidate_rag_results(
    results: List[Dict[str, Any]],
    current_section: int
) -> Dict[str, Any]:
    """
    Consolida múltiplos resultados do RAG (k=3) em um único contexto rico.

    Estratégia:
    1. Prioriza resultado da seção atual
    2. Usa outros resultados como contexto adicional
    3. Combina informações complementares

    Args:
        results: Lista de resultados do RAG (k=3)
        current_section: Seção que estamos buscando

    Returns:
        Resultado consolidado com contexto enriquecido
    """
    if not results:
        return {
            'content': '',
            'metadata': {},
            'context_sections': []
        }

    # Separar resultado principal e contexto
    primary_result = None
    context_results = []

    for result in results:
        section_num = result.get('metadata', {}).get('section', 0)
        if section_num == current_section:
            primary_result = result
        else:
            context_results.append(result)

    # Se não encontrou seção exata, usar o primeiro resultado
    if not primary_result and results:
        primary_result = results[0]
        context_results = results[1:]

    # Enriquecer com contexto
    consolidated = {
        'content': primary_result.get('content', ''),
        'metadata': primary_result.get('metadata', {}),
        'section': primary_result.get('metadata', {}).get('section', current_section),
        'context_sections': []
    }

    # Adicionar contexto de seções adjacentes
    for ctx_result in context_results[:2]:  # Máximo 2 seções de contexto
        ctx_section = ctx_result.get('metadata', {}).get('section', 0)
        ctx_content = ctx_result.get('content', '')[:200]  # Apenas preview

        consolidated['context_sections'].append({
            'section': ctx_section,
            'preview': ctx_content + '...'
        })

    logger.debug(
        f"[consolidate_rag] Consolidado: seção {consolidated['section']} "
        f"+ {len(consolidated['context_sections'])} contextos"
    )

    return consolidated


def extract_all_section_info(
    section_content: str,
    section_number: int
) -> Dict[str, Any]:
    """
    Extrai TODAS as informações relevantes de uma seção.

    Combina todos os extratores em uma única chamada.

    Args:
        section_content: Texto completo da seção
        section_number: Número da seção

    Returns:
        Dict completo com exits, flags, npcs, combat, etc
    """
    info = {
        'section': section_number,
        'exits': extract_exits_from_content(section_content),
        'flags': extract_flags_from_content(section_content, section_number),
        'npcs': extract_npcs_from_content(section_content),
        'combat': extract_combat_info(section_content),
    }

    logger.info(
        f"[extract_all] Seção {section_number}: "
        f"{len(info['exits'])} exits, "
        f"{len(info['flags'])} flags, "
        f"{len(info['npcs'])} NPCs, "
        f"combate={'sim' if info['combat'] else 'não'}"
    )

    return info
