"""Redis caching service for flight data to minimize API calls.

This service provides caching functionality with:
- 24-hour TTL for flight data
- Permanent caching for airport information
- Error resilience (doesn't fail if Redis unavailable)
- Cache statistics tracking
"""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.config import config

logger = logging.getLogger(__name__)


class CacheService:
    """Static service for Redis caching operations."""

    _redis_client: Optional[aioredis.Redis] = None

    @classmethod
    async def get_redis_client(cls) -> Optional[aioredis.Redis]:
        """
        Get or create Redis client connection.

        Returns:
            Redis client instance or None if connection fails
        """
        if cls._redis_client is None:
            try:
                cls._redis_client = await aioredis.from_url(
                    config.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await cls._redis_client.ping()
                logger.info(f"Redis client connected to {config.REDIS_URL}")
            except RedisError as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                cls._redis_client = None

        return cls._redis_client

    @classmethod
    async def close_redis_client(cls):
        """Close Redis client connection."""
        if cls._redis_client:
            await cls._redis_client.close()
            cls._redis_client = None
            logger.info("Redis client connection closed")

    @classmethod
    def _generate_cache_key(cls, prefix: str, identifier: str) -> str:
        """
        Generate cache key with consistent format.

        Args:
            prefix: Cache key prefix (e.g., "flight:status", "airport:info")
            identifier: Unique identifier (e.g., "BA123:2024-01-15")

        Returns:
            Formatted cache key (e.g., "flight:status:BA123:2024-01-15")
        """
        return f"{prefix}:{identifier}"

    @classmethod
    async def get_cached_flight(cls, flight_number: str, flight_date: str) -> Optional[Dict[str, Any]]:
        """
        Get cached flight data.

        Args:
            flight_number: Flight number (e.g., "BA123")
            flight_date: Flight date in YYYY-MM-DD format

        Returns:
            Cached flight data dict or None if cache miss
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping cache lookup")
                return None

            # Normalize flight number (uppercase, no spaces)
            flight_number = flight_number.upper().replace(" ", "")

            # Generate cache key
            cache_key = cls._generate_cache_key("flight:status", f"{flight_number}:{flight_date}")

            # Get from cache
            cached_data = await client.get(cache_key)

            if cached_data:
                logger.info(f"Cache HIT for flight {flight_number} on {flight_date}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for flight {flight_number} on {flight_date}")
                return None

        except RedisError as e:
            logger.error(f"Redis error during cache lookup: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in cache: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during cache lookup: {str(e)}", exc_info=True)
            return None

    @classmethod
    async def cache_flight(cls, flight_number: str, flight_date: str,
                          flight_data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Cache flight data with TTL.

        Args:
            flight_number: Flight number (e.g., "BA123")
            flight_date: Flight date in YYYY-MM-DD format
            flight_data: Flight data dictionary to cache
            ttl: Time-to-live in seconds (default: FLIGHT_CACHE_TTL_SECONDS from config)

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping cache write")
                return False

            # Normalize flight number
            flight_number = flight_number.upper().replace(" ", "")

            # Use default TTL from config if not specified
            if ttl is None:
                ttl = config.FLIGHT_CACHE_TTL_SECONDS

            # Generate cache key
            cache_key = cls._generate_cache_key("flight:status", f"{flight_number}:{flight_date}")

            # Add cache metadata
            cache_entry = {
                "data": flight_data,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl
            }

            # Write to cache with TTL
            await client.setex(cache_key, ttl, json.dumps(cache_entry))

            logger.info(f"Cached flight {flight_number} on {flight_date} with TTL {ttl}s")
            return True

        except RedisError as e:
            logger.error(f"Redis error during cache write: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache write: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def get_cached_airport(cls, airport_code: str) -> Optional[Dict[str, Any]]:
        """
        Get cached airport information.

        Args:
            airport_code: IATA airport code (e.g., "JFK")

        Returns:
            Cached airport data dict or None if cache miss
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping cache lookup")
                return None

            # Normalize airport code (uppercase, 3 chars)
            airport_code = airport_code.upper()[:3]

            # Generate cache key
            cache_key = cls._generate_cache_key("airport:info", airport_code)

            # Get from cache
            cached_data = await client.get(cache_key)

            if cached_data:
                logger.info(f"Cache HIT for airport {airport_code}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for airport {airport_code}")
                return None

        except RedisError as e:
            logger.error(f"Redis error during airport cache lookup: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in airport cache: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during airport cache lookup: {str(e)}", exc_info=True)
            return None

    @classmethod
    async def cache_airport(cls, airport_code: str, airport_data: Dict[str, Any]) -> bool:
        """
        Cache airport information permanently (no TTL).

        Airport data doesn't change, so we cache it permanently.

        Args:
            airport_code: IATA airport code (e.g., "JFK")
            airport_data: Airport data dictionary to cache

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping airport cache write")
                return False

            # Normalize airport code
            airport_code = airport_code.upper()[:3]

            # Generate cache key
            cache_key = cls._generate_cache_key("airport:info", airport_code)

            # Add cache metadata
            cache_entry = {
                "data": airport_data,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl": None  # Permanent
            }

            # Write to cache permanently (no TTL)
            await client.set(cache_key, json.dumps(cache_entry))

            logger.info(f"Cached airport {airport_code} permanently")
            return True

        except RedisError as e:
            logger.error(f"Redis error during airport cache write: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during airport cache write: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def invalidate_flight_cache(cls, flight_number: str, flight_date: str) -> bool:
        """
        Invalidate (delete) cached flight data.

        Args:
            flight_number: Flight number (e.g., "BA123")
            flight_date: Flight date in YYYY-MM-DD format

        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping cache invalidation")
                return False

            # Normalize flight number
            flight_number = flight_number.upper().replace(" ", "")

            # Generate cache key
            cache_key = cls._generate_cache_key("flight:status", f"{flight_number}:{flight_date}")

            # Delete from cache
            deleted = await client.delete(cache_key)

            if deleted:
                logger.info(f"Invalidated cache for flight {flight_number} on {flight_date}")
                return True
            else:
                logger.warning(f"No cache entry found for flight {flight_number} on {flight_date}")
                return False

        except RedisError as e:
            logger.error(f"Redis error during cache invalidation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache invalidation: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (keys, memory, hits/misses)
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                return {
                    "available": False,
                    "error": "Redis client unavailable"
                }

            # Get Redis info
            info = await client.info()

            # Count keys by pattern
            flight_keys = 0
            airport_keys = 0

            async for key in client.scan_iter(match="flight:status:*"):
                flight_keys += 1

            async for key in client.scan_iter(match="airport:info:*"):
                airport_keys += 1

            return {
                "available": True,
                "flight_cache_entries": flight_keys,
                "airport_cache_entries": airport_keys,
                "total_keys": info.get("db0", {}).get("keys", 0),
                "memory_used_bytes": info.get("used_memory", 0),
                "memory_used_human": info.get("used_memory_human", "unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) /
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                ) if info.get("keyspace_hits") is not None else 0
            }

        except RedisError as e:
            logger.error(f"Redis error getting cache stats: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting cache stats: {str(e)}", exc_info=True)
            return {
                "available": False,
                "error": str(e)
            }

    @classmethod
    async def clear_all_flight_cache(cls) -> int:
        """
        Clear all cached flight data (admin operation).

        Returns:
            Number of keys deleted
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, cannot clear cache")
                return 0

            deleted_count = 0

            # Delete all flight:status:* keys
            async for key in client.scan_iter(match="flight:status:*"):
                await client.delete(key)
                deleted_count += 1

            logger.info(f"Cleared {deleted_count} flight cache entries")
            return deleted_count

        except RedisError as e:
            logger.error(f"Redis error clearing flight cache: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error clearing flight cache: {str(e)}", exc_info=True)
            return 0

    # ========================================================================
    # Phase 6.5: Route Search Caching
    # ========================================================================

    @classmethod
    async def get_cached_route_search(
        cls,
        departure_iata: str,
        arrival_iata: str,
        flight_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached route search results.

        Args:
            departure_iata: Departure airport IATA code
            arrival_iata: Arrival airport IATA code
            flight_date: Flight date in YYYY-MM-DD format

        Returns:
            Cached route search data dict or None if cache miss
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping route search cache lookup")
                return None

            # Normalize inputs
            departure_iata = departure_iata.upper()
            arrival_iata = arrival_iata.upper()

            # Generate cache key (omit time to maximize cache hits)
            cache_key = cls._generate_cache_key(
                "flight_search",
                f"{departure_iata}:{arrival_iata}:{flight_date}"
            )

            # Get from cache
            cached_data = await client.get(cache_key)

            if cached_data:
                logger.info(f"Cache HIT for route search {departure_iata} → {arrival_iata} on {flight_date}")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for route search {departure_iata} → {arrival_iata} on {flight_date}")
                return None

        except RedisError as e:
            logger.error(f"Redis error during route search cache lookup: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in route search cache: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during route search cache lookup: {str(e)}", exc_info=True)
            return None

    @classmethod
    async def cache_route_search(
        cls,
        departure_iata: str,
        arrival_iata: str,
        flight_date: str,
        flights: list,
        ttl: int = None
    ) -> bool:
        """
        Cache route search results with TTL.

        Args:
            departure_iata: Departure airport IATA code
            arrival_iata: Arrival airport IATA code
            flight_date: Flight date in YYYY-MM-DD format
            flights: List of flight dictionaries
            ttl: Time-to-live in seconds (default: FLIGHT_SEARCH_CACHE_TTL_SECONDS from config)

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping route search cache write")
                return False

            # Normalize inputs
            departure_iata = departure_iata.upper()
            arrival_iata = arrival_iata.upper()

            # Use default TTL from config if not specified
            if ttl is None:
                ttl = config.FLIGHT_SEARCH_CACHE_TTL_SECONDS

            # Generate cache key
            cache_key = cls._generate_cache_key(
                "flight_search",
                f"{departure_iata}:{arrival_iata}:{flight_date}"
            )

            # Add cache metadata
            cache_entry = {
                "data": flights,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl,
                "route": f"{departure_iata}->{arrival_iata}",
                "flight_date": flight_date
            }

            # Write to cache with TTL
            await client.setex(cache_key, ttl, json.dumps(cache_entry))

            logger.info(
                f"Cached route search {departure_iata} → {arrival_iata} on {flight_date} "
                f"with {len(flights)} flights, TTL {ttl}s"
            )
            return True

        except RedisError as e:
            logger.error(f"Redis error during route search cache write: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during route search cache write: {str(e)}", exc_info=True)
            return False

    @classmethod
    async def get_cached_airport_search(cls, query: str) -> Optional[list]:
        """
        Get cached airport search results.

        Args:
            query: Search query (normalized)

        Returns:
            Cached airport list or None if cache miss
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping airport search cache lookup")
                return None

            # Normalize query (uppercase, no spaces)
            query_normalized = query.upper().replace(" ", "")

            # Generate cache key
            cache_key = cls._generate_cache_key("airports:search", query_normalized)

            # Get from cache
            cached_data = await client.get(cache_key)

            if cached_data:
                logger.info(f"Cache HIT for airport search '{query}'")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS for airport search '{query}'")
                return None

        except RedisError as e:
            logger.error(f"Redis error during airport search cache lookup: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in airport search cache: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during airport search cache lookup: {str(e)}", exc_info=True)
            return None

    @classmethod
    async def cache_airport_search(cls, query: str, airports: list) -> bool:
        """
        Cache airport search results with 7-day TTL.

        Args:
            query: Search query
            airports: List of airport dictionaries

        Returns:
            True if cached successfully, False otherwise
        """
        try:
            client = await cls.get_redis_client()
            if not client:
                logger.warning("Redis client unavailable, skipping airport search cache write")
                return False

            # Normalize query
            query_normalized = query.upper().replace(" ", "")

            # Use 7-day TTL for airport search results
            ttl = config.AIRPORT_AUTOCOMPLETE_CACHE_TTL_SECONDS

            # Generate cache key
            cache_key = cls._generate_cache_key("airports:search", query_normalized)

            # Add cache metadata
            cache_entry = {
                "data": airports,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl,
                "query": query
            }

            # Write to cache with TTL
            await client.setex(cache_key, ttl, json.dumps(cache_entry))

            logger.info(f"Cached airport search '{query}' with {len(airports)} results, TTL {ttl}s")
            return True

        except RedisError as e:
            logger.error(f"Redis error during airport search cache write: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during airport search cache write: {str(e)}", exc_info=True)
            return False
