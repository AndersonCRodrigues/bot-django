import logging
from typing import Dict, Optional
from langchain_weaviate import WeaviateVectorStore
from django.conf import settings
import weaviate

logger = logging.getLogger("game.weaviate")

_weaviate_client = None
_vector_store_cache: Dict[str, WeaviateVectorStore] = {}


def get_weaviate_client():
    """Retorna cliente Weaviate singleton."""
    global _weaviate_client

    if _weaviate_client is None:
        try:
            _weaviate_client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                timeout_config=(5, 15),
            )
            logger.info("Weaviate client conectado")
        except Exception as e:
            logger.error(f"Erro ao conectar Weaviate: {e}")
            raise

    return _weaviate_client


def get_embedding_model():
    """Retorna modelo de embeddings do Google."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", google_api_key=settings.GEMINI_API_KEY
    )


def create_vector_store(class_name: str) -> Optional[WeaviateVectorStore]:
    """
    Cria ou retorna vector store existente para uma classe.

    Args:
        class_name: Nome da classe no Weaviate (ex: "Ovilarejoamaldicoado")

    Returns:
        WeaviateVectorStore ou None em caso de erro
    """
    try:
        if class_name in _vector_store_cache:
            logger.debug(f"Vector store em cache: {class_name}")
            return _vector_store_cache[class_name]

        client = get_weaviate_client()
        embedding_model = get_embedding_model()

        vector_store = WeaviateVectorStore(
            client=client,
            index_name=class_name,
            embedding=embedding_model,
            text_key="text",
        )

        _vector_store_cache[class_name] = vector_store
        logger.info(f"Vector store criado: {class_name}")

        return vector_store

    except Exception as e:
        logger.error(f"Erro ao criar vector store para {class_name}: {e}")
        return None


def delete_vector_store(class_name: str) -> bool:
    """
    Deleta uma classe do Weaviate.

    Args:
        class_name: Nome da classe a deletar

    Returns:
        True se sucesso, False se erro
    """
    try:
        client = get_weaviate_client()
        client.schema.delete_class(class_name)

        if class_name in _vector_store_cache:
            del _vector_store_cache[class_name]

        logger.info(f"Vector store deletado: {class_name}")
        return True

    except Exception as e:
        logger.error(f"Erro ao deletar vector store {class_name}: {e}")
        return False


def check_weaviate_health() -> Dict:
    """
    Verifica saúde do Weaviate.

    Returns:
        dict: {
            'status': 'healthy' | 'unhealthy',
            'classes': int,
            'error': str (opcional)
        }
    """
    try:
        client = get_weaviate_client()
        schema = client.schema.get()

        return {
            "status": "healthy",
            "classes": len(schema.get("classes", [])),
            "classes_list": [c["class"] for c in schema.get("classes", [])],
        }

    except Exception as e:
        logger.error(f"Weaviate health check falhou: {e}")
        return {"status": "unhealthy", "error": str(e)}


def clear_cache():
    """Limpa cache de vector stores."""
    global _vector_store_cache
    _vector_store_cache.clear()
    logger.info("Cache de vector stores limpo")
