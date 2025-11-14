"""
🎯 Cliente LLM Global Simplificado

SEM rate limiter por enquanto - focar em resolver 429 primeiro.
"""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from django.conf import settings

logger = logging.getLogger("game.llm_client")

# 🎯 Instância global SIMPLES
logger.info("[LLM Client] Criando instância global de ChatGoogleGenerativeAI")
llm_client = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
    max_output_tokens=2048,
    max_retries=0,  # 🚫 Desabilita retries para evitar multiplicar chamadas
)

logger.info("[LLM Client] Criando instância global de GoogleGenerativeAIEmbeddings")
embedding_client = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=settings.GEMINI_API_KEY,
)
