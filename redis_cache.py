"""
Redis Cache Manager
Multi-level cache system for high-frequency query acceleration
"""

import redis
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Redis Cache Manager - Multi-level cache strategy"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: str = None, 
                 decode_responses: bool = True):
        """
        Initialize Redis connection
        
        Args:
            host: Redis server address
            port: Redis server port
            db: Database number
            password: Redis password
            decode_responses: Whether to auto-decode responses
        """
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=decode_responses,
                socket_connect_timeout=5
            )
            # 测试连接
            self.client.ping()
            self.connected = True
            logger.info(f"Redis cache manager connected to {host}:{port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.client = None
            self.connected = False
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(parts)
    
    def _hash_query(self, query: str) -> str:
        """Generate query hash (for fuzzy matching)"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self.connected or not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value) if isinstance(value, str) else value
        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value"""
        if not self.connected or not self.client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str) if not isinstance(value, str) else value
            return self.client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete cache keys"""
        if not self.connected or not self.client:
            return 0
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete cache keys: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.connected or not self.client:
            return 0
        
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.connected or not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    # ==================== User Data Cache ====================
    
    def cache_user_profile(self, user_id: int, profile: Dict[str, Any], ttl: int = 7200):
        """Cache user profile"""
        key = self._generate_key("user:profile", user_id)
        return self.set(key, profile, ttl)
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        key = self._generate_key("user:profile", user_id)
        return self.get(key)
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache related to user"""
        if not self.connected or not self.client:
            return
        
        try:
            # Get all user-related keys
            pattern = f"user:{user_id}:*"
            keys = self.client.keys(pattern)
            
            if keys:
                self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
    
    def cache_user_medications(self, user_id: int, medications: List[Dict[str, Any]], ttl: int = 3600):
        """Cache user medications"""
        key = self._generate_key("user:medications", user_id)
        return self.set(key, medications, ttl)
    
    def get_user_medications(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached user medications"""
        key = self._generate_key("user:medications", user_id)
        return self.get(key)
    
    def cache_user_reminders(self, user_id: int, reminders: List[Dict[str, Any]], ttl: int = 1800):
        """Cache user reminders (shorter TTL, as reminders change frequently)"""
        key = self._generate_key("user:reminders", user_id)
        return self.set(key, reminders, ttl)
    
    def get_user_reminders(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached user reminders"""
        key = self._generate_key("user:reminders", user_id)
        return self.get(key)
    
    # ==================== Conversation Cache (High-frequency Optimization) ====================
    
    def cache_conversation(self, query: str, response: str, ttl: int = 1800):
        """
        Cache conversation response
        
        For common questions (e.g., "What are my medications?"), return cached response directly
        """
        query_hash = self._hash_query(query)
        key = self._generate_key("conversation:response", query_hash)
        
        cache_data = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.set(key, cache_data, ttl)
    
    def get_conversation_cache(self, query: str) -> Optional[str]:
        """Get cached conversation response"""
        query_hash = self._hash_query(query)
        key = self._generate_key("conversation:response", query_hash)
        
        cached = self.get(key)
        if cached:
            return cached.get("response")
        
        return None
    
    def cache_similar_query(self, original_query: str, similar_query: str, response: str):
        """
        Cache similar query response
        
        Used to handle semantically similar but differently worded queries
        """
        original_hash = self._hash_query(original_query)
        similar_hash = self._hash_query(similar_query)
        
        # Record similar query mapping
        mapping_key = self._generate_key("conversation:similar", similar_hash)
        self.set(mapping_key, original_hash, ttl=86400)
        
        # Cache response (using original query hash)
        cache_key = self._generate_key("conversation:response", original_hash)
        return self.get(cache_key)  # No need to re-cache if original query is already cached
    
    def get_similar_conversation(self, query: str) -> Optional[str]:
        """Get cached response for similar query"""
        query_hash = self._hash_query(query)
        mapping_key = self._generate_key("conversation:similar", query_hash)
        
        original_hash = self.get(mapping_key)
        if original_hash:
            cache_key = self._generate_key("conversation:response", original_hash)
            cached = self.get(cache_key)
            if cached:
                return cached.get("response")
        
        return None
    
    # ==================== Chat History Cache ====================
    
    def cache_chat_messages(self, chat_id: str, messages: List[Dict[str, Any]], ttl: int = 3600):
        """Cache chat messages"""
        key = self._generate_key("chat:messages", chat_id)
        return self.set(key, messages, ttl)
    
    def get_chat_messages(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached chat messages"""
        key = self._generate_key("chat:messages", chat_id)
        return self.get(key)
    
    def cache_chat_title(self, chat_id: str, title: str, ttl: int = 86400):
        """Cache chat title"""
        key = self._generate_key("chat:title", chat_id)
        return self.set(key, title, ttl)
    
    def get_chat_title(self, chat_id: str) -> Optional[str]:
        """Get cached chat title"""
        key = self._generate_key("chat:title", chat_id)
        return self.get(key)
    
    # ==================== Statistics & Analysis ====================
    
    def track_query_frequency(self, query: str) -> int:
        """Track query frequency"""
        query_hash = self._hash_query(query)
        key = self._generate_key("stats:query_frequency", query_hash)
        
        # Record query
        frequency = self.increment(key, 1)
        
        # Set expiration (24 hours)
        if self.connected and self.client:
            try:
                self.client.expire(key, 86400)
            except:
                pass
        
        return frequency
    
    def get_query_frequency(self, query: str) -> int:
        """Get query frequency"""
        query_hash = self._hash_query(query)
        key = self._generate_key("stats:query_frequency", query_hash)
        
        value = self.get(key)
        return int(value) if value else 0
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top frequent queries (needs manual implementation, requires iteration)"""
        # Note: Production environment should use Redis Sorted Set for this
        return []
    
    # ==================== Cache Preloading ====================
    
    def preload_hot_data(self, user_id: int, data_types: List[str] = None):
        """Preload hot data"""
        if data_types is None:
            data_types = ["medications", "reminders"]
        
        # This function is typically called from other modules
        logger.info(f"Preloading hot data for user {user_id}: {data_types}")
        # Specific implementation provided by caller
    
    # ==================== Batch Operations ====================
    
    def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get cache"""
        if not self.connected or not self.client:
            return {}
        
        try:
            values = self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value) if isinstance(value, str) else value
                    except:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Failed to batch get cache: {e}")
            return {}
    
    def batch_set(self, data: Dict[str, Any], ttl: int = 3600):
        """Batch set cache"""
        if not self.connected or not self.client:
            return
        
        try:
            pipe = self.client.pipeline()
            for key, value in data.items():
                serialized_value = json.dumps(value, default=str) if not isinstance(value, str) else value
                pipe.setex(key, ttl, serialized_value)
            pipe.execute()
        except Exception as e:
            logger.error(f"Failed to batch set cache: {e}")

