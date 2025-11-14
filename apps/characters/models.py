from datetime import datetime
from typing import Optional, List, Dict
from bson import ObjectId
from django.conf import settings
import random


# Singleton para conexão MongoDB
_mongo_client = None


def get_mongo_client():
    """Retorna cliente MongoDB singleton"""
    global _mongo_client
    if _mongo_client is None:
        from pymongo import MongoClient

        _mongo_client = MongoClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
    return _mongo_client


class Character:
    collection_name = "characters"

    BASE_EQUIPMENT = ["Espada", "Mochila", "Lanterna"]
    PROTECTION_CHOICES = {
        "shield": "Escudo",
        "boots": "Botas",
    }
    POTION_CHOICES = {
        "luck": "Poção de Sorte",
        "skill": "Poção de Habilidade",
        "stamina": "Poção de Energia",
    }

    def __init__(
        self,
        name: str,
        adventure_id: int = None,
        skill: int = None,
        stamina: int = None,
        luck: int = None,
        initial_skill: int = None,
        initial_stamina: int = None,
        initial_luck: int = None,
        gold: int = 10,
        provisions: int = 10,
        protection: str = "shield",
        potion1: str = None,
        potion2: str = None,
        equipment: List[str] = None,
        notes: str = "",
        user_id: int = None,
        _id: ObjectId = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self._id = _id or ObjectId()
        self.name = name
        self.adventure_id = adventure_id

        self.initial_skill = initial_skill or self._roll_skill()
        self.initial_stamina = initial_stamina or self._roll_stamina()
        self.initial_luck = initial_luck or self._roll_luck()

        self.skill = skill if skill is not None else self.initial_skill
        self.stamina = stamina if stamina is not None else self.initial_stamina
        self.luck = luck if luck is not None else self.initial_luck

        self.gold = gold
        self.provisions = provisions
        self.protection = protection
        self.potion1 = potion1
        self.potion2 = potion2

        if equipment is None:
            self.equipment = self.BASE_EQUIPMENT.copy()
            self.equipment.append(self.PROTECTION_CHOICES.get(protection, "Escudo"))
            if potion1:
                self.equipment.append(self.POTION_CHOICES.get(potion1))
            if potion2:
                self.equipment.append(self.POTION_CHOICES.get(potion2))
        else:
            self.equipment = equipment

        self.notes = notes
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def id(self) -> str:
        """Retorna o ID como string (para usar em templates)"""
        return str(self._id)

    @staticmethod
    def _roll_dice() -> int:
        return random.randint(1, 6)

    def _roll_skill(self) -> int:
        return self._roll_dice() + 6

    def _roll_stamina(self) -> int:
        return self._roll_dice() + self._roll_dice() + 12

    def _roll_luck(self) -> int:
        return self._roll_dice() + 6

    def to_dict(self) -> Dict:
        return {
            "_id": self._id,
            "name": self.name,
            "adventure_id": self.adventure_id,
            "skill": self.skill,
            "stamina": self.stamina,
            "luck": self.luck,
            "initial_skill": self.initial_skill,
            "initial_stamina": self.initial_stamina,
            "initial_luck": self.initial_luck,
            "gold": self.gold,
            "provisions": self.provisions,
            "protection": self.protection,
            "potion1": self.potion1,
            "potion2": self.potion2,
            "equipment": self.equipment,
            "notes": self.notes,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        return cls(
            _id=data.get("_id"),
            name=data.get("name"),
            adventure_id=data.get("adventure_id"),
            skill=data.get("skill"),
            stamina=data.get("stamina"),
            luck=data.get("luck"),
            initial_skill=data.get("initial_skill"),
            initial_stamina=data.get("initial_stamina"),
            initial_luck=data.get("initial_luck"),
            gold=data.get("gold", 10),
            provisions=data.get("provisions", 10),
            protection=data.get("protection", "shield"),
            potion1=data.get("potion1"),
            potion2=data.get("potion2"),
            equipment=data.get("equipment"),
            notes=data.get("notes", ""),
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def get_collection(cls):
        """Retorna a collection do PyMongo (síncrona) usando singleton"""
        client = get_mongo_client()
        db = client[settings.MONGODB_DB_NAME]
        return db[cls.collection_name]

    @classmethod
    def find_by_user(cls, user_id: int) -> List["Character"]:
        """Busca TODOS personagens do usuário"""
        collection = cls.get_collection()
        docs = list(collection.find({"user_id": user_id}).sort("created_at", -1))
        return [cls.from_dict(doc) for doc in docs]

    @classmethod
    def find_by_user_and_adventure(
        cls, user_id: int, adventure_id: int
    ) -> List["Character"]:
        """Busca personagens do usuário para uma aventura específica"""
        collection = cls.get_collection()
        docs = list(
            collection.find({"user_id": user_id, "adventure_id": adventure_id}).sort(
                "created_at", -1
            )
        )
        return [cls.from_dict(doc) for doc in docs]

    @classmethod
    def find_by_id(cls, character_id: str, user_id: int) -> Optional["Character"]:
        """Busca personagem por ID (síncrono)"""
        import logging
        logger = logging.getLogger("game.character")

        try:
            logger.info(f"[Character.find_by_id] Buscando character_id={character_id}, user_id={user_id}")
            collection = cls.get_collection()
            doc = collection.find_one(
                {"_id": ObjectId(character_id), "user_id": user_id}
            )

            if doc:
                logger.info(f"[Character.find_by_id] Personagem encontrado: {doc.get('name')}")
                return cls.from_dict(doc)
            else:
                logger.warning(f"[Character.find_by_id] Personagem NÃO encontrado para character_id={character_id}, user_id={user_id}")
                return None
        except Exception as e:
            logger.error(f"[Character.find_by_id] ERRO ao buscar personagem: {e}", exc_info=True)
            return None

    def save(self):
        """Salva personagem (síncrono)"""
        collection = self.get_collection()
        self.updated_at = datetime.utcnow()
        collection.update_one({"_id": self._id}, {"$set": self.to_dict()}, upsert=True)

    def delete(self):
        """
        Deleta personagem e invalida todas as sessões relacionadas.

        As sessões são marcadas como STATUS_DEAD em vez de deletadas
        para manter histórico.
        """
        import logging
        logger = logging.getLogger("game.character")

        # Importar aqui para evitar circular import
        from apps.game.models import GameSession

        # Invalidar todas as sessões deste personagem
        try:
            session_collection = GameSession.get_collection()
            result = session_collection.update_many(
                {"character_id": str(self._id)},
                {"$set": {"status": GameSession.STATUS_DEAD}}
            )
            logger.info(
                f"[Character.delete] Invalidadas {result.modified_count} sessões "
                f"do personagem {self.name} (ID: {self.id})"
            )
        except Exception as e:
            logger.error(f"[Character.delete] Erro ao invalidar sessões: {e}")

        # Deletar personagem
        collection = self.get_collection()
        collection.delete_one({"_id": self._id})
        logger.info(f"[Character.delete] Personagem {self.name} (ID: {self.id}) deletado")
