import time
import logging
from typing import Optional
from django.contrib.auth.models import User
from apps.game.models import APIUsage

logger = logging.getLogger("game.usage")


class UsageTracker:
    """
    Rastreia uso da API Gemini para métricas e custos.

    Preços Gemini (aproximados USD por 1M tokens):
    - Input: $0.075
    - Output: $0.30
    """

    PRICE_INPUT_PER_1M = 0.075
    PRICE_OUTPUT_PER_1M = 0.30

    def __init__(
        self,
        user: User,
        adventure_id: Optional[int] = None,
        session_id: Optional[str] = None,
        operation_type: str = APIUsage.OPERATION_OTHER,
    ):
        self.user = user
        self.adventure_id = adventure_id
        self.session_id = session_id
        self.operation_type = operation_type
        self.start_time = None
        self.model_name = "gemini-pro"

    def start(self):
        """Inicia cronômetro."""
        self.start_time = time.time()

    def track(
        self,
        tokens_input: int,
        tokens_output: int,
        success: bool = True,
        error_message: Optional[str] = None,
        model_name: str = "gemini-pro",
    ) -> APIUsage:
        """
        Registra uso da API.

        Args:
            tokens_input: Tokens de entrada
            tokens_output: Tokens de saída
            success: Se a chamada foi bem-sucedida
            error_message: Mensagem de erro (se houver)
            model_name: Nome do modelo usado

        Returns:
            APIUsage record criado
        """
        tokens_total = tokens_input + tokens_output

        # Calcula custo
        cost_input = (tokens_input / 1_000_000) * self.PRICE_INPUT_PER_1M
        cost_output = (tokens_output / 1_000_000) * self.PRICE_OUTPUT_PER_1M
        estimated_cost = cost_input + cost_output

        # Calcula tempo de resposta
        response_time_ms = 0
        if self.start_time:
            response_time_ms = int((time.time() - self.start_time) * 1000)

        # Cria registro
        try:
            usage = APIUsage.objects.create(
                user=self.user,
                adventure_id=self.adventure_id,
                session_id=self.session_id,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_total,
                estimated_cost=estimated_cost,
                operation_type=self.operation_type,
                model_name=model_name,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
            )

            logger.info(
                f"API Usage tracked: {self.user.username} - "
                f"{tokens_total} tokens - ${estimated_cost:.6f}"
            )

            return usage

        except Exception as e:
            logger.error(f"Erro ao rastrear usage: {e}")
            return None

    @classmethod
    def track_simple(
        cls, user: User, tokens_input: int, tokens_output: int, **kwargs
    ) -> Optional[APIUsage]:
        """
        Método simplificado para rastreamento rápido.

        Usage:
            UsageTracker.track_simple(
                user=request.user,
                tokens_input=100,
                tokens_output=200,
                operation_type='narrate'
            )
        """
        tracker = cls(user=user, **kwargs)
        return tracker.track(tokens_input, tokens_output)


def get_user_daily_usage(user: User) -> dict:
    """
    Retorna uso do usuário hoje.

    Returns:
        dict: {
            'calls': int,
            'tokens': int,
            'cost': Decimal
        }
    """
    from django.utils import timezone
    from django.db.models import Sum, Count

    today = timezone.now().date()

    stats = APIUsage.objects.filter(user=user, created_at__date=today).aggregate(
        calls=Count("id"), tokens=Sum("tokens_total"), cost=Sum("estimated_cost")
    )

    return {
        "calls": stats["calls"] or 0,
        "tokens": stats["tokens"] or 0,
        "cost": stats["cost"] or 0,
    }


def get_adventure_total_cost(adventure_id: int) -> dict:
    """
    Retorna custo total de uma aventura.

    Returns:
        dict: {
            'total_cost': Decimal,
            'total_tokens': int,
            'total_calls': int,
            'unique_users': int
        }
    """
    from django.db.models import Sum, Count

    stats = APIUsage.objects.filter(adventure_id=adventure_id).aggregate(
        total_cost=Sum("estimated_cost"),
        total_tokens=Sum("tokens_total"),
        total_calls=Count("id"),
        unique_users=Count("user", distinct=True),
    )

    return {
        "total_cost": stats["total_cost"] or 0,
        "total_tokens": stats["total_tokens"] or 0,
        "total_calls": stats["total_calls"] or 0,
        "unique_users": stats["unique_users"] or 0,
    }
