from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


def get_mongo_client():
    from pymongo import MongoClient

    global _mongo_client
    if "_mongo_client" not in globals():
        _mongo_client = MongoClient(
            settings.MONGODB_URI, maxPoolSize=50, minPoolSize=10
        )
    return _mongo_client


class GameSession:
    collection_name = "game_sessions"

    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_DEAD = "dead"

    def __init__(
        self,
        user_id: int,
        adventure_id: int,
        character_id: str,
        current_section: int = 1,
        visited_sections: List[int] = None,
        inventory: List[str] = None,
        flags: Dict[str, Any] = None,
        history: List[Dict] = None,
        status: str = STATUS_ACTIVE,
        _id: ObjectId = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self._id = _id or ObjectId()
        self.user_id = user_id
        self.adventure_id = adventure_id
        self.character_id = character_id
        self.current_section = current_section
        self.visited_sections = visited_sections or [1]
        self.inventory = inventory or []
        self.flags = flags or {}
        self.history = history or []
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def id(self) -> str:
        return str(self._id)

    def to_dict(self) -> Dict:
        return {
            "_id": self._id,
            "user_id": self.user_id,
            "adventure_id": self.adventure_id,
            "character_id": self.character_id,
            "current_section": self.current_section,
            "visited_sections": self.visited_sections,
            "inventory": self.inventory,
            "flags": self.flags,
            "history": self.history,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "GameSession":
        return cls(
            _id=data.get("_id"),
            user_id=data.get("user_id"),
            adventure_id=data.get("adventure_id"),
            character_id=data.get("character_id"),
            current_section=data.get("current_section", 1),
            visited_sections=data.get("visited_sections", [1]),
            inventory=data.get("inventory", []),
            flags=data.get("flags", {}),
            history=data.get("history", []),
            status=data.get("status", cls.STATUS_ACTIVE),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def get_collection(cls):
        client = get_mongo_client()
        db = client[settings.MONGODB_DB_NAME]
        return db[cls.collection_name]

    @classmethod
    def find_by_id(cls, session_id: str, user_id: int) -> Optional["GameSession"]:
        try:
            collection = cls.get_collection()
            doc = collection.find_one({"_id": ObjectId(session_id), "user_id": user_id})
            return cls.from_dict(doc) if doc else None
        except:
            return None

    @classmethod
    def find_by_user(cls, user_id: int) -> List["GameSession"]:
        """Busca todas as sessões de um usuário"""
        collection = cls.get_collection()
        docs = list(collection.find({"user_id": user_id}).sort("updated_at", -1))
        return [cls.from_dict(doc) for doc in docs]

    @classmethod
    def find_active_session(
        cls, user_id: int, adventure_id: int
    ) -> Optional["GameSession"]:
        collection = cls.get_collection()
        doc = collection.find_one(
            {
                "user_id": user_id,
                "adventure_id": adventure_id,
                "status": cls.STATUS_ACTIVE,
            }
        )
        return cls.from_dict(doc) if doc else None

    def save(self):
        collection = self.get_collection()
        self.updated_at = datetime.utcnow()
        collection.update_one({"_id": self._id}, {"$set": self.to_dict()}, upsert=True)

    def add_to_history(self, entry: Dict):
        self.history.append({**entry, "timestamp": datetime.utcnow()})
        self.save()


class APIUsage(models.Model):
    """
    Rastreamento de uso da API Gemini para métricas e custos.
    Particionado por mês para escalabilidade.
    """

    OPERATION_NARRATE = "narrate"
    OPERATION_COMBAT = "combat"
    OPERATION_TEST = "test"
    OPERATION_DIALOGUE = "dialogue"
    OPERATION_EXPLORATION = "exploration"
    OPERATION_OTHER = "other"

    OPERATION_CHOICES = [
        (OPERATION_NARRATE, "Narrativa"),
        (OPERATION_COMBAT, "Combate"),
        (OPERATION_TEST, "Teste"),
        (OPERATION_DIALOGUE, "Diálogo"),
        (OPERATION_EXPLORATION, "Exploração"),
        (OPERATION_OTHER, "Outro"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, db_index=True, related_name="api_usage"
    )
    adventure = models.ForeignKey(
        "adventures.Adventure",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="api_usage",
    )
    session_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    tokens_total = models.IntegerField(default=0, db_index=True)

    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=6, default=0, help_text="Custo estimado em USD"
    )

    operation_type = models.CharField(
        max_length=50, choices=OPERATION_CHOICES, default=OPERATION_OTHER, db_index=True
    )

    model_name = models.CharField(max_length=100, default="gemini-pro", db_index=True)

    response_time_ms = models.IntegerField(
        default=0, help_text="Tempo de resposta em milissegundos"
    )

    success = models.BooleanField(default=True, db_index=True)
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "game_api_usage"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["adventure", "created_at"]),
            models.Index(fields=["created_at", "success"]),
            models.Index(fields=["user", "operation_type", "created_at"]),
        ]
        verbose_name = "API Usage"
        verbose_name_plural = "API Usage Records"

    def __str__(self):
        return (
            f"{self.user.username} - {self.operation_type} - {self.tokens_total} tokens"
        )

    @classmethod
    def get_user_stats(cls, user_id: int, days: int = 30):
        """Estatísticas de uso por usuário."""
        from django.utils import timezone
        from django.db.models import Sum, Avg, Count
        from datetime import timedelta

        since = timezone.now() - timedelta(days=days)

        stats = cls.objects.filter(user_id=user_id, created_at__gte=since).aggregate(
            total_calls=Count("id"),
            total_tokens=Sum("tokens_total"),
            total_cost=Sum("estimated_cost"),
            avg_response_time=Avg("response_time_ms"),
            success_rate=Avg(
                models.Case(
                    models.When(success=True, then=1),
                    default=0,
                    output_field=models.FloatField(),
                )
            ),
        )

        return stats

    @classmethod
    def get_adventure_stats(cls, adventure_id: int, days: int = 30):
        """Estatísticas de uso por aventura."""
        from django.utils import timezone
        from django.db.models import Sum, Count
        from datetime import timedelta

        since = timezone.now() - timedelta(days=days)

        stats = cls.objects.filter(
            adventure_id=adventure_id, created_at__gte=since
        ).aggregate(
            total_calls=Count("id"),
            unique_users=Count("user", distinct=True),
            total_tokens=Sum("tokens_total"),
            total_cost=Sum("estimated_cost"),
        )

        return stats

    @classmethod
    def get_global_stats(cls, days: int = 30):
        """Estatísticas globais do sistema."""
        from django.utils import timezone
        from django.db.models import Sum, Avg, Count
        from datetime import timedelta

        since = timezone.now() - timedelta(days=days)

        stats = cls.objects.filter(created_at__gte=since).aggregate(
            total_calls=Count("id"),
            unique_users=Count("user", distinct=True),
            total_tokens=Sum("tokens_total"),
            total_cost=Sum("estimated_cost"),
            avg_response_time=Avg("response_time_ms"),
            success_rate=Avg(
                models.Case(
                    models.When(success=True, then=1),
                    default=0,
                    output_field=models.FloatField(),
                )
            ),
        )

        return stats


class ProcessedBook(models.Model):
    """
    Rastreia livros processados e indexados no Weaviate.
    """

    adventure = models.OneToOneField(
        "adventures.Adventure", on_delete=models.CASCADE, related_name="processed_book"
    )

    weaviate_class_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Nome da classe no Weaviate",
    )

    pdf_filename = models.CharField(max_length=255)
    pdf_size_bytes = models.BigIntegerField(default=0)

    chunks_extracted = models.IntegerField(default=0)
    chunks_indexed = models.IntegerField(default=0)

    processing_status = models.CharField(
        max_length=50,
        choices=[
            ("pending", "Pendente"),
            ("processing", "Processando"),
            ("success", "Sucesso"),
            ("partial", "Parcial"),
            ("error", "Erro"),
        ],
        default="pending",
        db_index=True,
    )

    error_message = models.TextField(null=True, blank=True)

    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_processed_books"
        ordering = ["-created_at"]
        verbose_name = "Processed Book"
        verbose_name_plural = "Processed Books"

    def __str__(self):
        return f"{self.adventure.title} - {self.weaviate_class_name}"
