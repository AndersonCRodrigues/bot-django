"""
Cache de resultados de retrieval para evitar chamadas repetidas de embedding.

Baseado na versão original do projeto que tinha performance superior.
"""
import logging
import os
import sqlite3
import pickle
import hashlib
from typing import Optional
from datetime import datetime
from django.conf import settings

logger = logging.getLogger("game.retrieval_cache")


class RetrievalCache:
    """
    Cache SQLite para resultados de busca no Weaviate.

    Evita chamadas repetidas de embedding API ao cachear resultados
    de buscas anteriores.
    """

    def __init__(self, db_path: Optional[str] = None, expiration_seconds: int = 3600):
        """
        Args:
            db_path: Caminho do banco SQLite (default: cache/retrieval_cache.db)
            expiration_seconds: Tempo de expiração do cache (default: 1 hora)
        """
        if db_path is None:
            cache_dir = os.path.join(settings.BASE_DIR, 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            db_path = os.path.join(cache_dir, 'retrieval_cache.db')

        self.db_path = db_path
        self.expiration_seconds = expiration_seconds
        self._create_db()
        logger.info(f"RetrievalCache inicializado: {db_path}")

    def _create_db(self):
        """Cria tabela de cache se não existir."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS retrieval_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT,
                result BLOB,
                timestamp INTEGER
            )
        """
        )
        conn.commit()
        conn.close()

    def _hash_query(self, query: str) -> str:
        """Gera hash MD5 da query."""
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[dict]:
        """
        Busca resultado no cache.

        Args:
            query: Query de busca (ex: "seção 23")

        Returns:
            Resultado cacheado ou None se não encontrado/expirado
        """
        query_hash = self._hash_query(query)
        current_time = int(datetime.now().timestamp())
        expiration_time = current_time - self.expiration_seconds

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT result FROM retrieval_cache
            WHERE query_hash = ? AND timestamp > ?""",
            (query_hash, expiration_time),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            try:
                cached_result = pickle.loads(result[0])
                logger.debug(f"✅ Cache HIT: {query}")
                return cached_result
            except Exception as e:
                logger.error(f"Erro ao desserializar cache: {e}")
                return None

        logger.debug(f"❌ Cache MISS: {query}")
        return None

    def set(self, query: str, result: dict) -> None:
        """
        Salva resultado no cache.

        Args:
            query: Query de busca
            result: Resultado para cachear
        """
        query_hash = self._hash_query(query)
        current_time = int(datetime.now().timestamp())

        try:
            serialized_result = pickle.dumps(result)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO retrieval_cache
                (query_hash, query, result, timestamp) VALUES (?, ?, ?, ?)
                """,
                (query_hash, query, serialized_result, current_time),
            )
            conn.commit()
            conn.close()
            logger.debug(f"💾 Salvou no cache: {query}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")

    def clear(self) -> None:
        """Limpa todo o cache."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM retrieval_cache")
        conn.commit()
        conn.close()
        logger.info("Cache limpo completamente")

    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas do cache.

        Returns:
            Número de entradas removidas
        """
        current_time = int(datetime.now().timestamp())
        expiration_time = current_time - self.expiration_seconds

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM retrieval_cache WHERE timestamp < ?",
            (expiration_time,),
        )
        removed_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Limpeza: {removed_count} entradas expiradas removidas")
        return removed_count


# Singleton global
_global_cache: Optional[RetrievalCache] = None


def get_cache() -> RetrievalCache:
    """Retorna instância singleton do cache."""
    global _global_cache
    if _global_cache is None:
        _global_cache = RetrievalCache()
    return _global_cache
