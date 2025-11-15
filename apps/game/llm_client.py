"""
🎯 Cliente LLM Global - OpenAI

Migrado de Gemini para OpenAI para evitar rate limiting (15 RPM -> 500 RPM).
Usando gpt-4o-mini (mais barato) + text-embedding-3-small.
"""

import logging
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from django.conf import settings

logger = logging.getLogger("game.llm_client")

# 🎯 Instância global OpenAI
logger.info("[LLM Client] Criando instância global de ChatOpenAI (gpt-4o-mini)")
llm_client = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.OPENAI_API_KEY,
    temperature=0.2,  # 🎯 Reduzido de 0.7 para forçar seguir instruções RAG
    max_tokens=2048,
    max_retries=2,
)

logger.info("[LLM Client] Criando instância global de OpenAIEmbeddings")
embedding_client = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.OPENAI_API_KEY,
)
