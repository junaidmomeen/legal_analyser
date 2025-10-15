import redis.asyncio as redis
import json
import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class InMemoryCacheManager:
    """In-memory fallback used for tests or environments without Redis."""

    def __init__(self):
        self.analysis_store: Dict[str, Dict[str, Any]] = {}
        self.export_store: Dict[str, Dict[str, Any]] = {}
        self.hash_to_id: Dict[str, str] = {}
        self.prefix = "analysis_cache:"
        self.export_prefix = "export_task:"

    async def get_redis_connection(self):  # type: ignore[override]
        return None

    async def get_analysis(self, file_id: str) -> Optional[Dict[str, Any]]:
        return self.analysis_store.get(file_id)

    async def set_analysis(self, file_id: str, data: Dict[str, Any], file_hash: str):
        self.analysis_store[file_id] = data
        if file_hash:
            self.hash_to_id[file_hash] = file_id

    async def get_file_id_by_hash(self, file_hash: str) -> Optional[str]:
        return self.hash_to_id.get(file_hash)

    async def delete_analysis(self, file_id: str):
        data = self.analysis_store.pop(file_id, None)
        if data and (h := data.get("file_hash")):
            self.hash_to_id.pop(h, None)

    async def get_all_analysis_data(self) -> List[Dict[str, Any]]:
        return list(self.analysis_store.values())

    async def clear_all_analyses(self):
        self.analysis_store.clear()
        self.hash_to_id.clear()

    async def get_export_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.export_store.get(task_id)

    async def set_export_task(self, task_id: str, data: Dict[str, Any]):
        self.export_store[task_id] = data

    async def clear_all_export_tasks(self):
        self.export_store.clear()

    async def get_analysis_cache_size(self) -> int:
        return len(self.analysis_store)

    async def get_export_tasks_size(self) -> int:
        return len(self.export_store)


class CacheManager:
    """Manages caching of analysis results and export tasks in Redis."""

    def __init__(self, redis_url: str, default_ttl_seconds: int = 3600 * 24):
        """
        Initializes the CacheManager.

        Args:
            redis_url: The connection URL for Redis.
            default_ttl_seconds: Default time-to-live for cache entries in seconds (24 hours).
        """
        self.redis_url = redis_url
        self.redis_pool = redis.ConnectionPool.from_url(
            self.redis_url, decode_responses=True
        )
        self.default_ttl = default_ttl_seconds
        self.prefix = "analysis_cache:"
        self.export_prefix = "export_task:"
        self.hash_prefix = "file_hash:"

    async def get_redis_connection(self) -> redis.Redis:
        """Gets a Redis connection from the connection pool."""
        return redis.Redis(connection_pool=self.redis_pool)

    async def get_analysis(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves analysis data from the cache."""
        try:
            r = await self.get_redis_connection()
            data = await r.get(f"{self.prefix}{file_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(
                f"Error getting analysis from cache for file_id {file_id}: {e}"
            )
            return None

    async def set_analysis(self, file_id: str, data: Dict[str, Any], file_hash: str):
        """
        Stores analysis data in the cache and creates a hash-to-file_id mapping
        for deduplication.
        """
        try:
            r = await self.get_redis_connection()
            # Use a pipeline for atomic operations
            async with r.pipeline() as pipe:
                pipe.set(
                    f"{self.prefix}{file_id}",
                    json.dumps(data, default=str),
                    ex=self.default_ttl,
                )
                pipe.set(f"{self.hash_prefix}{file_hash}", file_id, ex=self.default_ttl)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Error setting analysis in cache for file_id {file_id}: {e}")

    async def get_file_id_by_hash(self, file_hash: str) -> Optional[str]:
        """Finds a file_id by its content hash for deduplication."""
        try:
            r = await self.get_redis_connection()
            return await r.get(f"{self.hash_prefix}{file_hash}")
        except Exception as e:
            logger.error(
                f"Error getting file_id by hash from cache for hash {file_hash}: {e}"
            )
            return None

    async def delete_analysis(self, file_id: str):
        """Deletes an analysis entry and its corresponding hash mapping."""
        try:
            r = await self.get_redis_connection()
            data = await self.get_analysis(file_id)
            async with r.pipeline() as pipe:
                pipe.delete(f"{self.prefix}{file_id}")
                if data and "file_hash" in data:
                    pipe.delete(f"{self.hash_prefix}{data['file_hash']}")
                await pipe.execute()
        except Exception as e:
            logger.error(
                f"Error deleting analysis from cache for file_id {file_id}: {e}"
            )

    async def get_all_analysis_data(self) -> List[Dict[str, Any]]:
        """Retrieves all analysis data entries from the cache."""
        try:
            r = await self.get_redis_connection()
            keys = [key async for key in r.scan_iter(f"{self.prefix}*")]
            if not keys:
                return []
            values = await r.mget(keys)
            return [json.loads(v) for v in values if v]
        except Exception as e:
            logger.error(f"Error getting all analysis data from cache: {e}")
            return []

    async def clear_all_analyses(self):
        """Clears all analysis-related keys from the cache."""
        try:
            r = await self.get_redis_connection()
            async with r.pipeline() as pipe:
                keys = [key async for key in r.scan_iter(f"{self.prefix}*")]
                if keys:
                    pipe.delete(*keys)
                hash_keys = [key async for key in r.scan_iter(f"{self.hash_prefix}*")]
                if hash_keys:
                    pipe.delete(*hash_keys)
                await pipe.execute()
        except Exception as e:
            logger.error(f"Error clearing all analyses from cache: {e}")

    async def get_export_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an export task from the cache."""
        try:
            r = await self.get_redis_connection()
            data = await r.get(f"{self.export_prefix}{task_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(
                f"Error getting export task from cache for task_id {task_id}: {e}"
            )
            return None

    async def set_export_task(self, task_id: str, data: Dict[str, Any]):
        """Stores an export task in the cache."""
        try:
            r = await self.get_redis_connection()
            await r.set(
                f"{self.export_prefix}{task_id}",
                json.dumps(data, default=str),
                ex=self.default_ttl,
            )
        except Exception as e:
            logger.error(
                f"Error setting export task in cache for task_id {task_id}: {e}"
            )

    async def clear_all_export_tasks(self):
        """Clears all export task keys from the cache."""
        try:
            r = await self.get_redis_connection()
            keys = [key async for key in r.scan_iter(f"{self.export_prefix}*")]
            if keys:
                await r.delete(*keys)
        except Exception as e:
            logger.error(f"Error clearing all export tasks from cache: {e}")

    async def get_analysis_cache_size(self) -> int:
        """Returns the number of entries in the analysis cache."""
        r = await self.get_redis_connection()
        return len([key async for key in r.scan_iter(f"{self.prefix}*")])

    async def get_export_tasks_size(self) -> int:
        """Returns the number of entries in the export tasks cache."""
        r = await self.get_redis_connection()
        return len([key async for key in r.scan_iter(f"{self.export_prefix}*")])


# --- Singleton Pattern for CacheManager ---
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Provides a singleton instance of the CacheManager.
    Connects to the Redis instance specified by environment variables.
    """
    global _cache_manager
    if _cache_manager is None:
        # Allow test environments to run without Redis
        if (
            os.getenv("PYTEST_CURRENT_TEST") is not None
            or os.getenv("USE_IN_MEMORY_CACHE") == "true"
        ):
            logger.info("Initializing InMemoryCacheManager (test mode)")
            _cache_manager = InMemoryCacheManager()  # type: ignore[assignment]
            return _cache_manager  # type: ignore[return-value]
        # Check for a full Redis URL first
        redis_url = os.getenv("CACHE_REDIS_URL")

        if not redis_url:
            # If CACHE_REDIS_URL is not set, construct it from components
            redis_host = os.getenv("REDIS_HOST", "redis")
            redis_port = os.getenv("REDIS_PORT", "6379")
            redis_db = os.getenv("REDIS_DB", "2")
            redis_password = os.getenv("REDIS_PASSWORD")

            if redis_password:
                redis_url = (
                    f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
                )
            else:
                redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

        logger.info("Initializing CacheManager with Redis URL.")
        _cache_manager = CacheManager(redis_url)
    return _cache_manager
