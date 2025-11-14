import logging
from typing import Optional, List
from langchain_core.retrievers import BaseRetriever
from .weaviate_service import create_vector_store, get_weaviate_client
from .retrieval_cache import get_cache
import weaviate.classes.query as wq

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


def get_section_by_number_direct(class_name: str, section_number: int) -> Optional[dict]:
    """
    🚀 OTIMIZAÇÃO: Busca seção por número diretamente (SEM EMBEDDING + CACHE).

    Esta função elimina a chamada de embedding API, economizando:
    - 1 API call por turno
    - Rate limit preciosos (15 RPM)

    Estratégia de 4 camadas:
    0. Cache: Tenta buscar no cache SQLite (0 API calls) ✅
    1. Metadata: Tenta filtrar por metadata.section (se existir)
    2. Texto: Busca por texto contendo "seção X" (BM25, sem embedding)
    3. Fallback: Busca com embedding (método antigo, última opção)

    Args:
        class_name: Nome da classe Weaviate (nome do livro)
        section_number: Número da seção (ex: 23)

    Returns:
        Dados da seção ou None
    """
    # 🎯 CAMADA 0: CACHE (mais rápido, 0 API calls)
    cache = get_cache()
    cache_key = f"{class_name}:section:{section_number}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"🚀 Cache HIT: Seção {section_number} (0 API calls)")
        return cached_result

    try:
        client = get_weaviate_client()
        collection = client.collections.get(class_name)

        # TENTATIVA 1: Query por metadata.section (se existir)
        try:
            response = collection.query.fetch_objects(
                filters=wq.Filter.by_property("section").equal(section_number),
                limit=1
            )

            if response.objects:
                obj = response.objects[0]
                result = {
                    "content": obj.properties.get("text", ""),
                    "metadata": {
                        "section": obj.properties.get("section", section_number),
                        "source": obj.properties.get("source", ""),
                        "page": obj.properties.get("page", 0),
                    },
                    "source": obj.properties.get("source", ""),
                    "page": obj.properties.get("page", 0),
                }
                logger.info(f"✅ Seção {section_number} recuperada por METADATA (sem embedding)")
                cache.set(cache_key, result)  # 💾 Salvar no cache
                return result
        except Exception:
            # Propriedade "section" não existe, tenta busca por texto
            logger.debug(f"Propriedade 'section' não existe em {class_name}, usando busca por texto")

        # TENTATIVA 2: Busca por texto contendo o número da seção
        # Padrões comuns: "23\n", "Seção 23", "23 ", etc.
        response = collection.query.fetch_objects(
            filters=wq.Filter.by_property("text").contains_any([
                f"{section_number}\n",
                f"seção {section_number}",
                f"Seção {section_number}",
                f"{section_number} ",
            ]),
            limit=10  # Pegar vários e filtrar o melhor
        )

        if response.objects:
            # Filtrar o objeto que mais provavelmente contém a seção correta
            # Prioriza objetos que começam com o número da seção
            best_match = None
            for obj in response.objects:
                text = obj.properties.get("text", "")
                # Se o texto começa com o número da seção, é muito provável ser a seção correta
                if text.strip().startswith(f"{section_number}\n") or text.strip().startswith(f"{section_number} "):
                    best_match = obj
                    break

            # Se não encontrou match perfeito, pega o primeiro
            if not best_match and response.objects:
                best_match = response.objects[0]

            if best_match:
                result = {
                    "content": best_match.properties.get("text", ""),
                    "metadata": {
                        "section": section_number,  # Inferido
                        "source": best_match.properties.get("source", ""),
                        "page": best_match.properties.get("page", 0),
                    },
                    "source": best_match.properties.get("source", ""),
                    "page": best_match.properties.get("page", 0),
                }
                logger.info(f"✅ Seção {section_number} recuperada por BUSCA DE TEXTO (sem embedding)")
                cache.set(cache_key, result)  # 💾 Salvar no cache
                return result

        logger.warning(f"Seção {section_number} não encontrada em {class_name}")
        return None

    except Exception as e:
        logger.error(f"Erro ao buscar seção {section_number} diretamente: {e}")
        # Fallback para método com embedding
        logger.warning("⚠️ Fallback para busca com embedding...")
        fallback_result = get_section_by_number(class_name, section_number)
        if fallback_result:
            cache.set(cache_key, fallback_result)  # 💾 Cachear resultado do fallback também
        return fallback_result


def clear_retriever_cache():
    """Limpa cache de retrievers e cache de retrieval."""
    global _retriever_cache
    _retriever_cache.clear()
    logger.info("Cache de retrievers limpo")

    # Limpar cache de retrieval também
    cache = get_cache()
    cache.clear()
    logger.info("Cache de retrieval limpo")


def cleanup_expired_cache():
    """Remove entradas expiradas do cache de retrieval."""
    cache = get_cache()
    removed = cache.cleanup_expired()
    logger.info(f"Limpeza automática: {removed} entradas expiradas removidas")
    return removed
