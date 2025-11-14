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
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from django.conf import settings

logger = logging.getLogger("game.llm_client")

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

logger.info("[LLM Client] Criando instância global de GoogleGenerativeAIEmbeddings")
embedding_client = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=settings.GEMINI_API_KEY,
)
