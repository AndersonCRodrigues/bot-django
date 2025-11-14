"""
Sistema de Achievements (Conquistas) para o RPG.

Define conquistas, verifica condições e notifica jogadores.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from django.conf import settings
from apps.game.models import GameSession
from apps.characters.models import Character


class AchievementCategory(Enum):
    """Categorias de achievements."""
    COMBAT = "combat"
    EXPLORATION = "exploration"
    SURVIVAL = "survival"
    COLLECTION = "collection"
    STORY = "story"
    SPECIAL = "special"


class Achievement:
    """
    Definição de um achievement.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: AchievementCategory,
        icon: str,
        points: int = 10,
        hidden: bool = False,
        condition_func: Optional[callable] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.icon = icon
        self.points = points
        self.hidden = hidden
        self.condition_func = condition_func

    def check_unlock(self, user_id: int, session: GameSession, character: Character) -> bool:
        """
        Verifica se o achievement foi desbloqueado.

        Args:
            user_id: ID do usuário
            session: GameSession atual
            character: Character do jogador

        Returns:
            True se desbloqueou
        """
        if self.condition_func:
            return self.condition_func(user_id, session, character)
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "icon": self.icon,
            "points": self.points,
            "hidden": self.hidden
        }


# ===== DEFINIÇÃO DE ACHIEVEMENTS =====

ACHIEVEMENTS = [
    # === COMBATE ===
    Achievement(
        id="first_blood",
        name="Primeiro Sangue",
        description="Vença seu primeiro combate",
        category=AchievementCategory.COMBAT,
        icon="⚔️",
        points=10,
        condition_func=lambda u, s, c: len([h for h in s.history if h.get("action_type") == "combat"]) >= 1
    ),

    Achievement(
        id="warrior",
        name="Guerreiro",
        description="Vença 10 combates",
        category=AchievementCategory.COMBAT,
        icon="🗡️",
        points=30,
        condition_func=lambda u, s, c: len([h for h in s.history if h.get("action_type") == "combat"]) >= 10
    ),

    Achievement(
        id="undefeated",
        name="Invicto",
        description="Complete uma aventura sem morrer",
        category=AchievementCategory.COMBAT,
        icon="🛡️",
        points=50,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED and c.stamina > 0
    ),

    Achievement(
        id="lucky_survivor",
        name="Sobrevivente Sortudo",
        description="Sobreviva a um combate com 1 de ENERGIA",
        category=AchievementCategory.SURVIVAL,
        icon="🍀",
        points=25,
        condition_func=lambda u, s, c: any(h.get("stamina") == 1 for h in s.history)
    ),

    # === EXPLORAÇÃO ===
    Achievement(
        id="explorer",
        name="Explorador",
        description="Visite 20 seções diferentes",
        category=AchievementCategory.EXPLORATION,
        icon="🗺️",
        points=20,
        condition_func=lambda u, s, c: len(set(s.visited_sections)) >= 20
    ),

    Achievement(
        id="completionist",
        name="Completista",
        description="Visite 50 seções diferentes",
        category=AchievementCategory.EXPLORATION,
        icon="🎯",
        points=50,
        condition_func=lambda u, s, c: len(set(s.visited_sections)) >= 50
    ),

    Achievement(
        id="fast_runner",
        name="Corredor Veloz",
        description="Complete uma aventura em menos de 30 turnos",
        category=AchievementCategory.EXPLORATION,
        icon="⚡",
        points=40,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED and len(s.history) < 30
    ),

    # === COLEÇÃO ===
    Achievement(
        id="hoarder",
        name="Acumulador",
        description="Tenha 10 itens no inventário",
        category=AchievementCategory.COLLECTION,
        icon="🎒",
        points=15,
        condition_func=lambda u, s, c: len(s.inventory) >= 10
    ),

    Achievement(
        id="rich",
        name="Rico",
        description="Acumule 50 moedas de ouro",
        category=AchievementCategory.COLLECTION,
        icon="💰",
        points=25,
        condition_func=lambda u, s, c: c.gold >= 50
    ),

    # === HISTÓRIA ===
    Achievement(
        id="first_adventure",
        name="Primeira Aventura",
        description="Complete sua primeira aventura",
        category=AchievementCategory.STORY,
        icon="📖",
        points=50,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED
    ),

    Achievement(
        id="veteran",
        name="Veterano",
        description="Complete 5 aventuras",
        category=AchievementCategory.STORY,
        icon="🎖️",
        points=100,
        hidden=True,
        condition_func=lambda u, s, c: GameSession.get_collection().count_documents({
            "user_id": u,
            "status": GameSession.STATUS_COMPLETED
        }) >= 5
    ),

    # === ESPECIAL ===
    Achievement(
        id="iron_man",
        name="Homem de Ferro",
        description="Complete uma aventura sem usar provisões",
        category=AchievementCategory.SPECIAL,
        icon="🦾",
        points=75,
        hidden=True,
        condition_func=lambda u, s, c: (
            s.status == GameSession.STATUS_COMPLETED and
            not any("provisão" in h.get("player_action", "").lower() for h in s.history)
        )
    ),

    Achievement(
        id="speedrunner",
        name="Speedrunner",
        description="Complete uma aventura em menos de 15 turnos",
        category=AchievementCategory.SPECIAL,
        icon="🏃",
        points=100,
        hidden=True,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED and len(s.history) < 15
    ),

    Achievement(
        id="perfectionist",
        name="Perfeccionista",
        description="Complete uma aventura com ENERGIA, SORTE e HABILIDADE no máximo",
        category=AchievementCategory.SPECIAL,
        icon="✨",
        points=150,
        hidden=True,
        condition_func=lambda u, s, c: (
            s.status == GameSession.STATUS_COMPLETED and
            c.stamina == c.initial_stamina and
            c.luck == c.initial_luck and
            c.skill == c.initial_skill
        )
    ),

    # === DADOS E SORTE ===
    Achievement(
        id="dice_master",
        name="Mestre dos Dados",
        description="Role dados 100 vezes em uma aventura",
        category=AchievementCategory.SPECIAL,
        icon="🎲",
        points=35,
        condition_func=lambda u, s, c: len([h for h in s.history if "2d6" in h.get("narrative", "").lower() or "rolou" in h.get("narrative", "").lower()]) >= 100
    ),

    Achievement(
        id="lucky_seven",
        name="Sorte em Sete",
        description="Role exatamente 7 em 2d6 cinco vezes",
        category=AchievementCategory.SURVIVAL,
        icon="🎰",
        points=30,
        condition_func=lambda u, s, c: len([h for h in s.history if "resultado: 7" in h.get("narrative", "").lower()]) >= 5
    ),

    Achievement(
        id="snake_eyes",
        name="Olhos de Cobra",
        description="Role o pior resultado possível (2 em 2d6)",
        category=AchievementCategory.SPECIAL,
        icon="🐍",
        points=20,
        condition_func=lambda u, s, c: any("resultado: 2" in h.get("narrative", "").lower() for h in s.history)
    ),

    Achievement(
        id="boxcars",
        name="Duplo Seis",
        description="Role o melhor resultado possível (12 em 2d6)",
        category=AchievementCategory.SPECIAL,
        icon="🎯",
        points=25,
        condition_func=lambda u, s, c: any("resultado: 12" in h.get("narrative", "").lower() for h in s.history)
    ),

    Achievement(
        id="fortunes_favor",
        name="Favorito da Fortuna",
        description="Passe em 5 testes de SORTE consecutivos",
        category=AchievementCategory.SURVIVAL,
        icon="🌟",
        points=40,
        hidden=True,
        condition_func=lambda u, s, c: any(
            all("teste de sorte" in h.get("narrative", "").lower() and "sucesso" in h.get("narrative", "").lower()
                for h in s.history[i:i+5])
            for i in range(len(s.history) - 4)
        )
    ),

    Achievement(
        id="jinxed",
        name="Azarado",
        description="Falhe em 3 testes de SORTE consecutivos",
        category=AchievementCategory.SURVIVAL,
        icon="😰",
        points=15,
        condition_func=lambda u, s, c: any(
            all("teste de sorte" in h.get("narrative", "").lower() and "falhou" in h.get("narrative", "").lower()
                for h in s.history[i:i+3])
            for i in range(len(s.history) - 2)
        )
    ),

    Achievement(
        id="death_defying",
        name="Desafiando a Morte",
        description="Sobreviva com 0 pontos de SORTE",
        category=AchievementCategory.SURVIVAL,
        icon="💀",
        points=60,
        hidden=True,
        condition_func=lambda u, s, c: c.luck == 0 and c.stamina > 0
    ),

    # === COMBATE AVANÇADO ===
    Achievement(
        id="berserker",
        name="Berserker",
        description="Vença 5 combates consecutivos sem fugir",
        category=AchievementCategory.COMBAT,
        icon="⚡",
        points=45,
        condition_func=lambda u, s, c: any(
            all(h.get("action_type") == "combat" and "vitória" in h.get("narrative", "").lower()
                for h in s.history[i:i+5])
            for i in range(len(s.history) - 4)
        )
    ),

    Achievement(
        id="glass_cannon",
        name="Canhão de Vidro",
        description="Vença um combate com 2 ou menos pontos de ENERGIA",
        category=AchievementCategory.COMBAT,
        icon="🥊",
        points=35,
        condition_func=lambda u, s, c: any(
            h.get("action_type") == "combat" and "vitória" in h.get("narrative", "").lower() and h.get("stamina", 99) <= 2
            for h in s.history
        )
    ),

    Achievement(
        id="never_tell_odds",
        name="Nunca Me Diga as Chances",
        description="Vença combate contra inimigo muito superior (HABILIDADE 4+ maior)",
        category=AchievementCategory.COMBAT,
        icon="🦸",
        points=75,
        hidden=True,
        condition_func=lambda u, s, c: any(
            h.get("action_type") == "combat" and
            "vitória" in h.get("narrative", "").lower() and
            h.get("enemy_skill", 0) >= c.skill + 4
            for h in s.history
        )
    ),

    # === EXPLORAÇÃO AVANÇADA ===
    Achievement(
        id="cartographer",
        name="Cartógrafo",
        description="Visite 100 seções diferentes",
        category=AchievementCategory.EXPLORATION,
        icon="🗺️",
        points=75,
        hidden=True,
        condition_func=lambda u, s, c: len(set(s.visited_sections)) >= 100
    ),

    Achievement(
        id="early_bird",
        name="Pássaro Madrugador",
        description="Complete uma aventura em menos de 10 turnos",
        category=AchievementCategory.EXPLORATION,
        icon="🐦",
        points=80,
        hidden=True,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED and len(s.history) < 10
    ),

    Achievement(
        id="marathon_runner",
        name="Maratonista",
        description="Complete uma aventura com mais de 100 turnos",
        category=AchievementCategory.EXPLORATION,
        icon="🏃",
        points=50,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED and len(s.history) > 100
    ),

    # === COLEÇÃO AVANÇADA ===
    Achievement(
        id="treasure_hunter",
        name="Caçador de Tesouros",
        description="Acumule 100 moedas de ouro",
        category=AchievementCategory.COLLECTION,
        icon="💎",
        points=40,
        condition_func=lambda u, s, c: c.gold >= 100
    ),

    Achievement(
        id="minimalist",
        name="Minimalista",
        description="Complete uma aventura com apenas 3 itens no inventário",
        category=AchievementCategory.COLLECTION,
        icon="🎒",
        points=55,
        hidden=True,
        condition_func=lambda u, s, c: s.status == GameSession.STATUS_COMPLETED and len(s.inventory) <= 3
    ),

    Achievement(
        id="hoarder_supreme",
        name="Acumulador Supremo",
        description="Tenha 20 itens no inventário",
        category=AchievementCategory.COLLECTION,
        icon="👑",
        points=35,
        condition_func=lambda u, s, c: len(s.inventory) >= 20
    ),

    Achievement(
        id="prepared",
        name="Bem Preparado",
        description="Comece um combate com 10 provisões",
        category=AchievementCategory.SURVIVAL,
        icon="🥖",
        points=20,
        condition_func=lambda u, s, c: any(
            h.get("action_type") == "combat" and h.get("provisions", 0) >= 10
            for h in s.history
        )
    ),

    Achievement(
        id="potion_master",
        name="Mestre das Poções",
        description="Use todas as 3 poções diferentes em uma aventura",
        category=AchievementCategory.COLLECTION,
        icon="🧪",
        points=30,
        condition_func=lambda u, s, c: len([
            h for h in s.history
            if "poção" in h.get("player_action", "").lower()
        ]) >= 3
    ),

    # === HISTÓRIA AVANÇADA ===
    Achievement(
        id="legend",
        name="Lenda Viva",
        description="Complete 10 aventuras",
        category=AchievementCategory.STORY,
        icon="👑",
        points=200,
        hidden=True,
        condition_func=lambda u, s, c: GameSession.get_collection().count_documents({
            "user_id": u,
            "status": GameSession.STATUS_COMPLETED
        }) >= 10
    ),
]

# Criar lookup dict
ACHIEVEMENTS_DICT = {ach.id: ach for ach in ACHIEVEMENTS}


# ===== FUNÇÕES DE VERIFICAÇÃO =====

def check_achievements(user_id: int, session: GameSession, character: Character) -> List[Achievement]:
    """
    Verifica quais achievements foram desbloqueados.

    Args:
        user_id: ID do usuário
        session: GameSession atual
        character: Character do jogador

    Returns:
        Lista de achievements desbloqueados neste turno
    """
    # Buscar achievements já desbloqueados
    unlocked_ids = get_unlocked_achievement_ids(user_id)

    # Verificar novos achievements
    newly_unlocked = []

    for achievement in ACHIEVEMENTS:
        if achievement.id in unlocked_ids:
            continue  # Já desbloqueado

        if achievement.check_unlock(user_id, session, character):
            newly_unlocked.append(achievement)
            # Salvar no banco
            save_achievement_unlock(user_id, achievement.id)

    return newly_unlocked


def get_unlocked_achievement_ids(user_id: int) -> List[str]:
    """
    Retorna IDs dos achievements já desbloqueados.

    Args:
        user_id: ID do usuário

    Returns:
        Lista de IDs
    """
    from pymongo import MongoClient

    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    collection = db["user_achievements"]

    docs = collection.find({"user_id": user_id})
    return [doc["achievement_id"] for doc in docs]


def save_achievement_unlock(user_id: int, achievement_id: str):
    """
    Salva achievement desbloqueado no MongoDB.

    Args:
        user_id: ID do usuário
        achievement_id: ID do achievement
    """
    from pymongo import MongoClient

    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    collection = db["user_achievements"]

    collection.insert_one({
        "user_id": user_id,
        "achievement_id": achievement_id,
        "unlocked_at": datetime.utcnow()
    })


def get_user_achievements(user_id: int) -> List[Dict[str, Any]]:
    """
    Retorna todos achievements do usuário com status.

    Args:
        user_id: ID do usuário

    Returns:
        Lista de dicts com achievement + unlocked
    """
    unlocked_ids = get_unlocked_achievement_ids(user_id)

    result = []
    for achievement in ACHIEVEMENTS:
        if achievement.hidden and achievement.id not in unlocked_ids:
            continue  # Não mostrar hidden não desbloqueados

        ach_dict = achievement.to_dict()
        ach_dict["unlocked"] = achievement.id in unlocked_ids
        result.append(ach_dict)

    return result


def get_achievement_stats(user_id: int) -> Dict[str, Any]:
    """
    Retorna estatísticas de achievements do usuário.

    Args:
        user_id: ID do usuário

    Returns:
        Dict com total, unlocked, points, etc.
    """
    unlocked_ids = get_unlocked_achievement_ids(user_id)

    total_achievements = len([a for a in ACHIEVEMENTS if not a.hidden]) + len(unlocked_ids)
    unlocked_count = len(unlocked_ids)
    total_points = sum(ACHIEVEMENTS_DICT[aid].points for aid in unlocked_ids)

    return {
        "total": total_achievements,
        "unlocked": unlocked_count,
        "locked": total_achievements - unlocked_count,
        "points": total_points,
        "completion_rate": (unlocked_count / total_achievements * 100) if total_achievements > 0 else 0
    }
