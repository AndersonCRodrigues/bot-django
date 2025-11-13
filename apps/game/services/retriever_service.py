import logging
from typing import Optional, List
from langchain_core.retrievers import BaseRetriever
from .weaviate_service import create_vector_store

logger = logging.getLogger("game.retriever")

_retriever_cache = {}


def create_as_retriever(
    class_name: str,
    search_type: str = "mmr",
    k: int = 3,
    fetch_k: int = 10,
    lambda_mult: float = 0.5,
) -> Optional[BaseRetriever]:
    """
    Cria retriever otimizado para busca de seções do livro.

    Args:
        class_name: Nome da classe Weaviate (nome do livro)
        search_type: Tipo de busca ("mmr" ou "similarity")
        k: Número de resultados a retornar
        fetch_k: Número de documentos a buscar antes de MMR
        lambda_mult: Diversidade vs relevância (0 = diversidade, 1 = relevância)

    Returns:
        BaseRetriever configurado
    """
    cache_key = f"{class_name}_{search_type}_{k}_{fetch_k}_{lambda_mult}"

    if cache_key in _retriever_cache:
        logger.debug(f"Retriever em cache: {cache_key}")
        return _retriever_cache[cache_key]

    try:
        vector_store = create_vector_store(class_name)

        if not vector_store:
            logger.error(f"Não foi possível criar vector store para {class_name}")
            return None

        retriever = vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={
                "k": k,
                "fetch_k": fetch_k,
                "lambda_mult": lambda_mult,
            },
        )

        _retriever_cache[cache_key] = retriever
        logger.info(f"Retriever criado: {cache_key}")

        return retriever

    except Exception as e:
        logger.error(f"Erro ao criar retriever para {class_name}: {e}")
        return None


def search_section(class_name: str, query: str, k: int = 3) -> List[dict]:
    """
    Busca seções específicas no livro.

    Args:
        class_name: Nome da classe Weaviate
        query: Query de busca (ex: "seção 23", "taverna")
        k: Número de resultados

    Returns:
        Lista de documentos encontrados
    """
    try:
        retriever = create_as_retriever(class_name, k=k)

        if not retriever:
            return []

        docs = retriever.invoke(query)

        results = []
        for doc in docs:
            results.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", ""),
                    "page": doc.metadata.get("page", 0),
                }
            )

        logger.info(f"Busca em {class_name}: '{query}' → {len(results)} resultados")
        return results

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return []


def get_section_by_number(class_name: str, section_number: int) -> Optional[dict]:
    """
    Busca seção específica por número.

    Args:
        class_name: Nome da classe Weaviate
        section_number: Número da seção (ex: 23)

    Returns:
        Dados da seção ou None
    """
    query = f"seção {section_number}"
    results = search_section(class_name, query, k=1)

    if results:
        return results[0]

    return None


def clear_retriever_cache():
    """Limpa cache de retrievers."""
    global _retriever_cache
    _retriever_cache.clear()
    logger.info("Cache de retrievers limpo")
