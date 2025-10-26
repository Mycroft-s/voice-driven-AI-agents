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
    """Redis缓存管理器 - 多级缓存策略"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 db: int = 0, password: str = None, 
                 decode_responses: bool = True):
        """
        初始化Redis连接
        
        Args:
            host: Redis服务器地址
            port: Redis服务器端口
            db: 数据库编号
            password: 密码
            decode_responses: 是否自动解码响应
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
        """生成缓存键"""
        parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(parts)
    
    def _hash_query(self, query: str) -> str:
        """生成查询哈希（用于模糊匹配）"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
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
        """设置缓存值"""
        if not self.connected or not self.client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str) if not isinstance(value, str) else value
            return self.client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """删除缓存键"""
        if not self.connected or not self.client:
            return 0
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete cache keys: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self.connected or not self.client:
            return 0
        
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment cache key {key}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.connected or not self.client:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    # ==================== 用户数据缓存 ====================
    
    def cache_user_profile(self, user_id: int, profile: Dict[str, Any], ttl: int = 7200):
        """缓存用户资料"""
        key = self._generate_key("user:profile", user_id)
        return self.set(key, profile, ttl)
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取缓存的用户资料"""
        key = self._generate_key("user:profile", user_id)
        return self.get(key)
    
    def invalidate_user_cache(self, user_id: int):
        """失效用户相关的所有缓存"""
        if not self.connected or not self.client:
            return
        
        try:
            # 获取所有用户相关的键
            pattern = f"user:{user_id}:*"
            keys = self.client.keys(pattern)
            
            if keys:
                self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
    
    def cache_user_medications(self, user_id: int, medications: List[Dict[str, Any]], ttl: int = 3600):
        """缓存用户药物信息"""
        key = self._generate_key("user:medications", user_id)
        return self.set(key, medications, ttl)
    
    def get_user_medications(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的用户药物信息"""
        key = self._generate_key("user:medications", user_id)
        return self.get(key)
    
    def cache_user_reminders(self, user_id: int, reminders: List[Dict[str, Any]], ttl: int = 1800):
        """缓存用户提醒（TTL较短，因为提醒经常变化）"""
        key = self._generate_key("user:reminders", user_id)
        return self.set(key, reminders, ttl)
    
    def get_user_reminders(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的用户提醒"""
        key = self._generate_key("user:reminders", user_id)
        return self.get(key)
    
    # ==================== 对话缓存（高频优化） ====================
    
    def cache_conversation(self, query: str, response: str, ttl: int = 1800):
        """
        缓存对话响应
        
        对于常见问题（如"我的用药是什么"），直接返回缓存
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
        """获取缓存的对话响应"""
        query_hash = self._hash_query(query)
        key = self._generate_key("conversation:response", query_hash)
        
        cached = self.get(key)
        if cached:
            return cached.get("response")
        
        return None
    
    def cache_similar_query(self, original_query: str, similar_query: str, response: str):
        """
        缓存相似查询的响应
        
        用于处理语义相似但措辞不同的查询
        """
        original_hash = self._hash_query(original_query)
        similar_hash = self._hash_query(similar_query)
        
        # 记录相似查询映射
        mapping_key = self._generate_key("conversation:similar", similar_hash)
        self.set(mapping_key, original_hash, ttl=86400)
        
        # 缓存响应（使用原始查询的哈希）
        cache_key = self._generate_key("conversation:response", original_hash)
        return self.get(cache_key)  # 如果原始查询已被缓存，则不需要重新缓存
    
    def get_similar_conversation(self, query: str) -> Optional[str]:
        """获取相似查询的缓存响应"""
        query_hash = self._hash_query(query)
        mapping_key = self._generate_key("conversation:similar", query_hash)
        
        original_hash = self.get(mapping_key)
        if original_hash:
            cache_key = self._generate_key("conversation:response", original_hash)
            cached = self.get(cache_key)
            if cached:
                return cached.get("response")
        
        return None
    
    # ==================== 聊天历史缓存 ====================
    
    def cache_chat_messages(self, chat_id: str, messages: List[Dict[str, Any]], ttl: int = 3600):
        """缓存聊天消息"""
        key = self._generate_key("chat:messages", chat_id)
        return self.set(key, messages, ttl)
    
    def get_chat_messages(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的聊天消息"""
        key = self._generate_key("chat:messages", chat_id)
        return self.get(key)
    
    def cache_chat_title(self, chat_id: str, title: str, ttl: int = 86400):
        """缓存聊天标题"""
        key = self._generate_key("chat:title", chat_id)
        return self.set(key, title, ttl)
    
    def get_chat_title(self, chat_id: str) -> Optional[str]:
        """获取缓存的聊天标题"""
        key = self._generate_key("chat:title", chat_id)
        return self.get(key)
    
    # ==================== 统计与分析 ====================
    
    def track_query_frequency(self, query: str) -> int:
        """追踪查询频率"""
        query_hash = self._hash_query(query)
        key = self._generate_key("stats:query_frequency", query_hash)
        
        # 记录查询
        frequency = self.increment(key, 1)
        
        # 设置过期时间（24小时）
        if self.connected and self.client:
            try:
                self.client.expire(key, 86400)
            except:
                pass
        
        return frequency
    
    def get_query_frequency(self, query: str) -> int:
        """获取查询频率"""
        query_hash = self._hash_query(query)
        key = self._generate_key("stats:query_frequency", query_hash)
        
        value = self.get(key)
        return int(value) if value else 0
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取高频查询（需要手动实现，因为需要遍历）"""
        # 注意：生产环境应该使用Redis Sorted Set来实现
        return []
    
    # ==================== 缓存预热 ====================
    
    def preload_hot_data(self, user_id: int, data_types: List[str] = None):
        """预热热点数据"""
        if data_types is None:
            data_types = ["medications", "reminders"]
        
        # 这个函数通常在其他模块中调用
        logger.info(f"Preloading hot data for user {user_id}: {data_types}")
        # 具体实现由调用方提供数据
    
    # ==================== 批量操作 ====================
    
    def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存"""
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
        """批量设置缓存"""
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

