"""
🎯 Cliente LLM Singleton - Instância única compartilhada

Resolve problema de múltiplas instâncias causando erro 429.

Antes:
- Cada get_llm() criava nova instância
- narrative_agent.py criava sua própria instância
- embeddings criava sua própria instância
= múltiplas conexões HTTP, overhead, 429

Depois:
- UMA instância global de ChatGoogleGenerativeAI
- UMA instância global de GoogleGenerativeAIEmbeddings
- Todos os módulos compartilham as mesmas instâncias
= 1 conexão, menos overhead, sem 429
"""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from django.conf import settings

logger = logging.getLogger("game.llm_client")

# 🎯 Instâncias singleton globais
_llm_instance = None
_embeddings_instance = None


def get_shared_llm(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """
    Retorna instância ÚNICA e compartilhada do ChatGoogleGenerativeAI.

    Todas as chamadas retornam a MESMA instância, reduzindo overhead
    e evitando múltiplas conexões simultâneas.

    Args:
        temperature: Temperatura para geração (padrão 0.7)

    Returns:
        Instância singleton de ChatGoogleGenerativeAI
    """
    global _llm_instance

    if _llm_instance is None:
        logger.info("[LLM Client] Criando instância singleton de ChatGoogleGenerativeAI")
        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
            max_output_tokens=2048,
        )

    return _llm_instance


def get_shared_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    Retorna instância ÚNICA e compartilhada do GoogleGenerativeAIEmbeddings.

    Todas as chamadas retornam a MESMA instância, reduzindo overhead
    e evitando múltiplas conexões simultâneas ao embedding API.

    Returns:
        Instância singleton de GoogleGenerativeAIEmbeddings
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        logger.info("[LLM Client] Criando instância singleton de GoogleGenerativeAIEmbeddings")
        _embeddings_instance = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY,
        )

    return _embeddings_instance


def reset_clients():
    """
    Reset das instâncias singleton (útil para testes).

    ATENÇÃO: Só use em testes ou quando necessário reconfigurar.
    """
    global _llm_instance, _embeddings_instance

    logger.warning("[LLM Client] Resetando instâncias singleton")
    _llm_instance = None
    _embeddings_instance = None
