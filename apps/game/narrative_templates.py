"""
🎯 Templates de Narrativa Determinística (SEM LLM)

Este módulo contém templates Python para gerar narrativas de combate e testes
sem precisar chamar a LLM, economizando tokens e evitando rate limiting.

Usado para mecânicas DETERMINÍSTICAS:
- Combate (resultado já calculado por combat_round)
- Testes de Sorte/Habilidade (resultado já calculado por check_luck/check_skill)

Narrativas CRIATIVAS (exploração, conversas) continuam usando LLM em nodes.py
"""

import random
from typing import Dict, Any


# ========================================
# 🎯 TEMPLATES DE COMBATE
# ========================================

COMBAT_ATTACK_VERBS = [
    "golpeia", "acerta", "atinge", "fere", "corta", "perfura",
    "machuca", "ataca com precisão", "desfere um golpe em"
]

COMBAT_DEFENSE_VERBS = [
    "desvia", "esquiva", "defende", "bloqueia", "recua",
    "apara o golpe de", "evita o ataque de"
]

COMBAT_REACTIONS_HIT = [
    "O inimigo urra de dor!",
    "Um gemido de agonia escapa do inimigo.",
    "Você vê sangue escorrer!",
    "O golpe foi certeiro!",
    "O impacto ressoa pelo ambiente!",
]

COMBAT_REACTIONS_MISS = [
    "Os dois combatentes circulam um ao outro, cautelosos.",
    "A tensão é palpável no ar!",
    "Ambos procuram uma brecha na defesa do oponente.",
    "O momento de hesitação passa...",
]


def format_combat_narrative(
    enemy_name: str,
    enemy_skill: int,
    enemy_stamina: int,
    character_skill: int,
    character_stamina: int,
    character_roll: int,
    character_attack: int,
    enemy_roll: int,
    enemy_attack: int,
    combat_result: str,
    new_character_stamina: int,
    new_enemy_stamina: int,
    **kwargs
) -> str:
    """
    Gera narrativa de combate usando templates Python (SEM LLM).

    Args:
        combat_result: "character_hit", "enemy_hit", ou "tie"
    """

    # Introdução da rodada
    narrative = f"Você enfrenta {enemy_name} em combate mortal!\n\n"

    # Detalhes dos ataques
    narrative += f"**Seu ataque:** {character_attack} (rolou {character_roll} + {character_skill} HABILIDADE)\n"
    narrative += f"**Ataque de {enemy_name}:** {enemy_attack} (rolou {enemy_roll} + {enemy_skill} HABILIDADE)\n\n"

    # Resultado narrativo
    if combat_result == "character_hit":
        verb = random.choice(COMBAT_ATTACK_VERBS)
        reaction = random.choice(COMBAT_REACTIONS_HIT)
        damage = character_stamina - new_character_stamina

        narrative += f"Sua arma {verb} {enemy_name}! {reaction} (-2 ENERGIA)\n\n"

    elif combat_result == "enemy_hit":
        verb = random.choice(COMBAT_ATTACK_VERBS)
        damage = character_stamina - new_character_stamina

        narrative += f"{enemy_name} {verb} você! Você sente a dor do golpe! (-2 ENERGIA)\n\n"

    else:  # tie
        reaction = random.choice(COMBAT_REACTIONS_MISS)
        narrative += f"Nenhum golpe conecta! {reaction}\n\n"

    # Status atual
    narrative += f"**Status:**\n"
    narrative += f"- Sua ENERGIA: {new_character_stamina}\n"
    narrative += f"- {enemy_name} ENERGIA: {new_enemy_stamina}\n\n"

    # Opções do jogador
    if new_enemy_stamina <= 0:
        narrative += f"🎉 **VITÓRIA!** Você derrotou {enemy_name}!\n\n"
        narrative += "O que você faz agora?\n"
        narrative += "1. Procurar por tesouros no corpo\n"
        narrative += "2. Seguir em frente rapidamente\n"
        narrative += "3. Descansar e recuperar o fôlego"

    elif new_character_stamina <= 0:
        narrative += "💀 **Você foi derrotado!** Sua visão escurece...\n"

    else:
        narrative += "O que você faz?\n\n"
        narrative += "1. Continuar atacando\n"
        narrative += "2. Tentar fugir (Teste de SORTE)\n"
        narrative += "3. Usar um item do inventário"

    return narrative


# ========================================
# 🎯 TEMPLATES DE TESTE DE SORTE
# ========================================

LUCK_SUCCESS_REACTIONS = [
    "A sorte está ao seu lado!",
    "Os deuses da fortuna sorriem para você!",
    "Que golpe de sorte!",
    "Você foi afortunado desta vez!",
    "As estrelas se alinham em seu favor!",
]

LUCK_FAILURE_REACTIONS = [
    "A sorte não está do seu lado...",
    "Os deuses da fortuna viram o rosto...",
    "Não foi dessa vez...",
    "A fortuna é caprichosa...",
    "O destino não favorece os hesitantes...",
]


def format_luck_test_narrative(
    character_name: str,
    luck_value: int,
    roll: int,
    success: bool,
    new_luck: int,
    player_action: str,
    **kwargs
) -> str:
    """
    Gera narrativa de teste de sorte usando templates Python (SEM LLM).
    """

    # Introdução baseada na ação
    if "fugir" in player_action.lower() or "escapar" in player_action.lower():
        context = "tentar escapar do combate"
    elif "abrir" in player_action.lower():
        context = "abrir algo com cuidado"
    elif "evitar" in player_action.lower():
        context = "evitar o perigo"
    else:
        context = "confiar na sorte"

    narrative = f"Você respira fundo e decide {context}...\n\n"
    narrative += f"**Teste de SORTE:**\n"
    narrative += f"Rolou: {roll} vs SORTE: {luck_value}\n\n"

    if success:
        reaction = random.choice(LUCK_SUCCESS_REACTIONS)
        narrative += f"🍀 **SUCESSO!** {reaction}\n\n"

        # Consequência positiva
        if "fugir" in player_action.lower():
            narrative += "Você consegue escapar ileso! Corre pelo corredor e some de vista.\n\n"
        elif "abrir" in player_action.lower():
            narrative += "O mecanismo abre suavemente, sem ativar nenhuma armadilha!\n\n"
        else:
            narrative += "Você consegue realizar sua intenção sem problemas!\n\n"
    else:
        reaction = random.choice(LUCK_FAILURE_REACTIONS)
        narrative += f"❌ **FALHA!** {reaction}\n\n"

        # Consequência negativa
        if "fugir" in player_action.lower():
            narrative += "O inimigo está em seu encalço! Você não conseguiu fugir e deve enfrentá-lo.\n\n"
        elif "abrir" in player_action.lower():
            narrative += "Você ouve um clique sinistro... Uma armadilha foi ativada!\n\n"
        else:
            narrative += "As coisas não saíram como planejado...\n\n"

    narrative += f"(Sua SORTE agora é {new_luck})\n\n"

    # Opções
    narrative += "O que você faz agora?\n\n"

    if success:
        narrative += "1. Seguir em frente com confiança\n"
        narrative += "2. Procurar por mais oportunidades\n"
        narrative += "3. Ser mais cauteloso daqui em diante"
    else:
        narrative += "1. Lidar com as consequências\n"
        narrative += "2. Tentar encontrar outra saída\n"
        narrative += "3. Preparar-se para o pior"

    return narrative


# ========================================
# 🎯 TEMPLATES DE TESTE DE HABILIDADE
# ========================================

SKILL_SUCCESS_REACTIONS = [
    "Suas habilidades de aventureiro provam seu valor!",
    "Seu treinamento não foi em vão!",
    "Você demonstra maestria!",
    "Suas habilidades são impressionantes!",
    "Você executa com perfeição!",
]

SKILL_FAILURE_REACTIONS = [
    "Você não consegue realizar a tarefa...",
    "Suas habilidades não foram suficientes desta vez...",
    "A dificuldade era maior do que você pensava...",
    "Você falha na tentativa...",
]


def format_skill_test_narrative(
    character_name: str,
    skill_value: int,
    roll: int,
    success: bool,
    player_action: str,
    **kwargs
) -> str:
    """
    Gera narrativa de teste de habilidade usando templates Python (SEM LLM).
    """

    # Introdução baseada na ação
    if "escalar" in player_action.lower() or "subir" in player_action.lower():
        context = "escalar o obstáculo"
    elif "saltar" in player_action.lower() or "pular" in player_action.lower():
        context = "fazer o salto perigoso"
    elif "desarmar" in player_action.lower():
        context = "desarmar o mecanismo"
    elif "equilibrar" in player_action.lower():
        context = "manter o equilíbrio"
    else:
        context = "usar suas habilidades"

    narrative = f"Você se concentra e tenta {context}...\n\n"
    narrative += f"**Teste de HABILIDADE:**\n"
    narrative += f"Rolou: {roll} vs HABILIDADE: {skill_value}\n\n"

    if success:
        reaction = random.choice(SKILL_SUCCESS_REACTIONS)
        narrative += f"✓ **SUCESSO!** {reaction}\n\n"
        narrative += "Você completa a tarefa com êxito!\n\n"
    else:
        reaction = random.choice(SKILL_FAILURE_REACTIONS)
        narrative += f"✗ **FALHA!** {reaction}\n\n"
        narrative += "Você precisará encontrar outro caminho ou tentar novamente.\n\n"

    # Opções
    narrative += "O que você faz agora?\n\n"

    if success:
        narrative += "1. Continuar com confiança\n"
        narrative += "2. Procurar por mais desafios\n"
        narrative += "3. Seguir adiante com cuidado"
    else:
        narrative += "1. Procurar uma alternativa\n"
        narrative += "2. Tentar novamente com mais cuidado\n"
        narrative += "3. Desistir e seguir outro caminho"

    return narrative
