"""
🎯 Cliente LLM Global com Rate Limiting

Usa monkey-patching para adicionar rate limiting sem wrapper.
Compatível com LangChain LCEL (operador |).
"""

import logging
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from django.conf import settings

logger = logging.getLogger("game.llm_client")


def _add_rate_limiting_to_llm(llm: ChatGoogleGenerativeAI) -> ChatGoogleGenerativeAI:
    """
    Adiciona rate limiting a um LLM via monkey-patching.

    Substitui o método invoke() original por versão com rate limiting,
    mantendo o LLM como Runnable válido para LangChain.
    """
    original_invoke = llm.invoke

    def rate_limited_invoke(*args, **kwargs) -> Any:
        """Invoke com rate limiting automático."""
        from apps.game.services.rate_limiter import get_llm_rate_limiter

        rate_limiter = get_llm_rate_limiter()

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

        result = original_invoke(*args, **kwargs)

        logger.info(f"✅ LLM CALL CONCLUÍDA")

        return result

    # Substitui invoke() mantendo LLM como Runnable válido
    llm.invoke = rate_limited_invoke

    return llm

# 🎯 Instâncias globais criadas no import do módulo
# Python garante execução única - mais simples que singleton pattern

logger.info("[LLM Client] Criando instância global de ChatGoogleGenerativeAI")
llm_client = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
    max_output_tokens=2048,
    max_retries=0,  # 🚫 Desabilita retries para evitar 4x mais chamadas no 429
)

# 🚦 Adiciona rate limiting via monkey-patch (mantém compatibilidade LCEL)
logger.info("[LLM Client] Adicionando rate limiting (15 RPM) via monkey-patch")
llm_client = _add_rate_limiting_to_llm(llm_client)

logger.info("[LLM Client] Criando instância global de GoogleGenerativeAIEmbeddings")
embedding_client = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=settings.GEMINI_API_KEY,
)
