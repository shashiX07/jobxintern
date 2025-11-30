import redis
import json
import config
import logging
import hashlib
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                **config.REDIS_CONFIG, 
                decode_responses=True,
                socket_keepalive=True,
                socket_connect_timeout=5,
                max_connections=10
            )
            self.redis_client.ping()
            logger.info("Redis connected successfully with connection pooling")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            self.redis_client = None
    
    def set_jobs(self, key, jobs, ttl=config.CACHE_TTL):
        """Cache jobs list"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(jobs))
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def get_jobs(self, key):
        """Get cached jobs"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    def delete(self, key):
        """Delete cache entry"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    def set_user_state(self, user_id, state, ttl=3600):
        """Set user onboarding state"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(f"user_state:{user_id}", ttl, json.dumps(state))
            return True
        except Exception as e:
            logger.error(f"Error setting user state: {e}")
            return False
    
    def get_user_state(self, user_id):
        """Get user onboarding state"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(f"user_state:{user_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting user state: {e}")
            return None
    
    def clear_user_state(self, user_id):
        """Clear user onboarding state"""
        return self.delete(f"user_state:{user_id}")
    
    def cache_user_jobs(self, user_id, jobs, ttl=1800):
        """Cache matching jobs for a user (30 min default)"""
        if not self.redis_client or not jobs:
            return False
        
        try:
            key = f"user_jobs:{user_id}"
            self.redis_client.setex(key, ttl, json.dumps(jobs))
            return True
        except Exception as e:
            logger.error(f"Error caching user jobs: {e}")
            return False
    
    def get_user_jobs(self, user_id):
        """Get cached jobs for user"""
        if not self.redis_client:
            return None
        
        try:
            key = f"user_jobs:{user_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting cached user jobs: {e}")
            return None
    
    def cache_query_result(self, query_key, result, ttl=3600):
        """Cache any query result with custom TTL"""
        if not self.redis_client:
            return False
        
        try:
            # Create hash of query for consistent key
            key_hash = hashlib.md5(query_key.encode()).hexdigest()
            cache_key = f"query:{key_hash}"
            self.redis_client.setex(cache_key, ttl, json.dumps(result))
            return True
        except Exception as e:
            logger.error(f"Error caching query: {e}")
            return False
    
    def get_query_result(self, query_key):
        """Get cached query result"""
        if not self.redis_client:
            return None
        
        try:
            key_hash = hashlib.md5(query_key.encode()).hexdigest()
            cache_key = f"query:{key_hash}"
            data = self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting cached query: {e}")
            return None
    
    def invalidate_user_cache(self, user_id):
        """Invalidate all cache for a user (when preferences change)"""
        if not self.redis_client:
            return False
        
        try:
            patterns = [
                f"user_jobs:{user_id}",
                f"user_state:{user_id}"
            ]
            for pattern in patterns:
                self.redis_client.delete(pattern)
            logger.info(f"Cache invalidated for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    def get_stats(self):
        """Get Redis cache statistics"""
        if not self.redis_client:
            return None
        
        try:
            info = self.redis_client.info('stats')
            return {
                'total_connections': info.get('total_connections_received', 0),
                'keys': self.redis_client.dbsize(),
                'memory_used': self.redis_client.info('memory').get('used_memory_human', 'N/A')
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return None

cache = CacheManager()
