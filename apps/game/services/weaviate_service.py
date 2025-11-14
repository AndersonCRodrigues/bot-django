import contextlib
import logging
from typing import Dict, Optional
from langchain_weaviate import WeaviateVectorStore
from django.conf import settings
import weaviate
from weaviate.connect import ConnectionParams, ProtocolParams
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import atexit

logger = logging.getLogger("game.weaviate")

_weaviate_client: Optional[weaviate.WeaviateClient] = None
_vector_store_cache: Dict[str, WeaviateVectorStore] = {}


def _get_connection_params() -> ConnectionParams:
    host = getattr(settings, "WEAVIATE_HOST", "localhost")
    http_port = getattr(settings, "WEAVIATE_PORT", 8080)
    grpc_port = getattr(settings, "WEAVIATE_GRPC_PORT", 50051)
    secure = getattr(settings, "WEAVIATE_SECURE", False)

    http_params = ProtocolParams(host=host, port=http_port, secure=secure)
    grpc_params = ProtocolParams(host=host, port=grpc_port, secure=secure)

    return ConnectionParams(http=http_params, grpc=grpc_params)


def get_weaviate_client():
    global _weaviate_client

    if _weaviate_client is None:
        try:
            connection_params = _get_connection_params()
            _weaviate_client = weaviate.WeaviateClient(
                connection_params=connection_params
            )
            _weaviate_client.connect()
        except Exception as e:
            logger.error(f"Erro ao conectar Weaviate (API v4): {e}")
            raise

    return _weaviate_client


def get_embedding_model():
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GEMINI_API_KEY,
    )


def create_vector_store(class_name: str) -> Optional[WeaviateVectorStore]:
    try:
        if class_name in _vector_store_cache:
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
        return vector_store

    except Exception as e:
        logger.error(f"Erro ao criar vector store para {class_name}: {e}")
        return None


def create_as_retriever(class_name: str):
    try:
        vector_store = create_vector_store(class_name)
        if vector_store is None:
            return None

        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.5},
        )

    except Exception as e:
        logger.error(f"Erro ao criar retriever para {class_name}: {str(e)}")
        return None


def delete_vector_store(class_name: str) -> bool:
    try:
        client: weaviate.WeaviateClient = get_weaviate_client()
        client.collections.delete(class_name)

        if class_name in _vector_store_cache:
            del _vector_store_cache[class_name]

        return True

    except Exception as e:
        logger.error(f"Erro ao deletar vector store {class_name}: {e}")
        return False


def check_weaviate_health() -> Dict:
    try:
        client: weaviate.WeaviateClient = get_weaviate_client()

        if not client.is_ready():
            return {
                "status": "unhealthy",
                "error": "Client reports service is not ready",
            }

        collections = client.collections.list_all()

        return {
            "status": "healthy",
            "classes": len(collections),
            "classes_list": collections,
        }

    except Exception as e:
        logger.error(f"Weaviate health check falhou: {e}")
        return {"status": "unhealthy", "error": str(e)}


def clear_cache():
    global _vector_store_cache
    _vector_store_cache.clear()
    logger.info("Cache de vector stores limpo")


def close_weaviate_client():
    global _weaviate_client
    if _weaviate_client is not None:
        with contextlib.suppress(Exception):
            _weaviate_client.close()


atexit.register(close_weaviate_client)
