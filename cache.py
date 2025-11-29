import redis
import json
import config
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(**config.REDIS_CONFIG, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connected successfully")
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

cache = CacheManager()
