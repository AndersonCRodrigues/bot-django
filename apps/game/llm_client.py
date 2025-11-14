"""
🎯 Cliente LLM Global - Instância única compartilhada

Padrão module-level singleton (como código de referência).

Instâncias criadas UMA VEZ quando módulo é importado.
Todos os imports compartilham as MESMAS instâncias.

Uso:
    from apps.game.llm_client import llm_client, embedding_client
    response = llm_client.invoke(...)
"""

import logging
from typing import Any, Dict, Optional
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from django.conf import settings

logger = logging.getLogger("game.llm_client")


class RateLimitedLLM:
    """
    Wrapper transparente que adiciona rate limiting ao LLM.

    Delega TODOS métodos/atributos ao LLM original,
    mas intercepta invoke() para rate limiting.
    """

    def __init__(self, llm: ChatGoogleGenerativeAI):
        # Usa __dict__ direto para evitar __setattr__
        object.__setattr__(self, '_llm', llm)
        object.__setattr__(self, '_rate_limiter', None)

    def _get_rate_limiter(self):
        """Lazy load do rate limiter."""
        if self._rate_limiter is None:
            from apps.game.services.rate_limiter import get_llm_rate_limiter
            object.__setattr__(self, '_rate_limiter', get_llm_rate_limiter())
        return self._rate_limiter

    def invoke(self, *args, **kwargs) -> Any:
        """
        Invoca LLM com rate limiting automático.

        Aguarda automaticamente se necessário para não exceder 15 RPM.
        """
        rate_limiter = self._get_rate_limiter()

        # 📊 Log de uso antes da chamada
        usage = rate_limiter.get_current_usage()
        logger.info(
            f"🔵 LLM CALL INICIADA - "
            f"Uso atual: {usage['requests_in_window']}/{usage['max_requests']} "
            f"(restam {usage['remaining']} na janela de 60s)"
        )

        wait_time = rate_limiter.acquire()

        if wait_time > 0:
            logger.warning(f"⏳ Aguardou {wait_time:.1f}s pelo rate limit")

        result = self._llm.invoke(*args, **kwargs)

        logger.info(f"✅ LLM CALL CONCLUÍDA")

        return result

    def bind_tools(self, tools):
        """
        Retorna novo wrapper com tools bindadas.

        Mantém rate limiting no LLM com tools.
        """
        bound_llm = self._llm.bind_tools(tools)
        return RateLimitedLLM(bound_llm)

    def __getattr__(self, name):
        """Delega TODOS outros métodos/atributos ao LLM original."""
        return getattr(self._llm, name)

    def __setattr__(self, name, value):
        """Delega setattr ao LLM original (exceto atributos internos)."""
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._llm, name, value)

    def __dir__(self):
        """Mostra atributos do LLM original para introspecção."""
        return dir(self._llm)

    def __repr__(self):
        """Representação mostra que é wrapper do LLM."""
        return f"RateLimitedLLM({repr(self._llm)})"

# 🎯 Instâncias globais criadas no import do módulo
# Python garante execução única - mais simples que singleton pattern

logger.info("[LLM Client] Criando instância global de ChatGoogleGenerativeAI")
_base_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
    max_output_tokens=2048,
    max_retries=0,  # 🚫 Desabilita retries para evitar 4x mais chamadas no 429
)

# 🚦 Wrapper com rate limiting automático
logger.info("[LLM Client] Adicionando rate limiting (15 RPM)")
llm_client = RateLimitedLLM(_base_llm)

logger.info("[LLM Client] Criando instância global de GoogleGenerativeAIEmbeddings")
embedding_client = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=settings.GEMINI_API_KEY,
)
