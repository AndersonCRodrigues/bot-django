"""
Rate Limiter simples para evitar 429 do Gemini.

Garante que não excedemos 15 RPM (Requests Per Minute).
"""
import time
import logging
from collections import deque
from threading import Lock
from typing import Optional

logger = logging.getLogger("game.rate_limiter")


class RateLimiter:
    """
    Rate limiter thread-safe usando sliding window.

    Rastreia timestamps de requests e força espera se exceder limite.
    """

    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        """
        Args:
            max_requests: Máximo de requests permitidos na janela (default: 15)
            window_seconds: Tamanho da janela em segundos (default: 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = Lock()
        logger.info(f"RateLimiter inicializado: {max_requests} requests/{window_seconds}s")

    def acquire(self) -> float:
        """
        Adquire permissão para fazer request.

        Bloqueia (sleep) se necessário até que seja seguro fazer request.

        Returns:
            Tempo de espera em segundos (0 se não esperou)
        """
        with self.lock:
            now = time.time()

            # Remove requests fora da janela
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()

            # Se atingiu o limite, calcula quanto tempo esperar
            if len(self.requests) >= self.max_requests:
                # Tempo até o request mais antigo sair da janela
                oldest = self.requests[0]
                wait_time = (oldest + self.window_seconds) - now + 0.1  # +0.1s margem

                if wait_time > 0:
                    logger.warning(
                        f"⏳ Rate limit atingido ({self.max_requests}/{self.window_seconds}s). "
                        f"Aguardando {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    now = time.time()

                    # Limpa novamente após esperar
                    while self.requests and self.requests[0] < now - self.window_seconds:
                        self.requests.popleft()

                    # Registra request atual
                    self.requests.append(now)
                    return wait_time

            # Registra request atual
            self.requests.append(now)
            logger.debug(f"✅ Request permitido ({len(self.requests)}/{self.max_requests} na janela)")
            return 0.0

    def get_current_usage(self) -> dict:
        """
        Retorna estatísticas atuais do rate limiter.

        Returns:
            {
                'requests_in_window': int,
                'max_requests': int,
                'remaining': int,
                'window_seconds': int
            }
        """
        with self.lock:
            now = time.time()

            # Limpa requests expirados
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()

            current = len(self.requests)

            return {
                'requests_in_window': current,
                'max_requests': self.max_requests,
                'remaining': max(0, self.max_requests - current),
                'window_seconds': self.window_seconds,
            }


# Singleton global para LLM calls
_llm_rate_limiter: Optional[RateLimiter] = None


def get_llm_rate_limiter() -> RateLimiter:
    """
    Retorna instância singleton do rate limiter para LLM.

    Configurado para Gemini free tier: 15 RPM
    """
    global _llm_rate_limiter
    if _llm_rate_limiter is None:
        _llm_rate_limiter = RateLimiter(max_requests=15, window_seconds=60)
    return _llm_rate_limiter
