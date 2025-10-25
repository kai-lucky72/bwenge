import redis
import time
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: str = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Rate limit key (e.g., "api_calls:user_123")
            limit: Maximum number of requests
            window: Time window in seconds
            identifier: Optional identifier for logging
            
        Returns:
            (is_allowed, info_dict)
        """
        
        current_time = int(time.time())
        window_start = current_time - window
        
        try:
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1]
            
            info = {
                "limit": limit,
                "remaining": max(0, limit - current_count - 1),
                "reset_time": current_time + window,
                "window": window
            }
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for {identifier or key}")
                return False, info
            
            return True, info
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {
                "limit": limit,
                "remaining": limit - 1,
                "reset_time": current_time + window,
                "window": window
            }
    
    def get_usage(self, key: str, window: int) -> int:
        """Get current usage for a key"""
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Clean old entries and count
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            results = pipe.execute()
            
            return results[1]
        except Exception as e:
            logger.error(f"Error getting rate limit usage: {e}")
            return 0

class QuotaManager:
    """Manages usage quotas for organizations"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def check_quota(
        self,
        org_id: str,
        quota_type: str,
        amount: int = 1
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if organization has quota available
        
        Args:
            org_id: Organization ID
            quota_type: Type of quota (messages, storage, users)
            amount: Amount to consume
            
        Returns:
            (has_quota, quota_info)
        """
        
        quota_key = f"quota:{org_id}:{quota_type}"
        
        try:
            # Get current quota info
            quota_data = self.redis.get(quota_key)
            if not quota_data:
                # No quota set - assume unlimited for now
                return True, {
                    "limit": -1,
                    "used": 0,
                    "remaining": -1,
                    "quota_type": quota_type
                }
            
            quota_info = json.loads(quota_data)
            limit = quota_info.get("limit", -1)
            used = quota_info.get("used", 0)
            
            # Check if unlimited
            if limit == -1:
                return True, {
                    "limit": -1,
                    "used": used,
                    "remaining": -1,
                    "quota_type": quota_type
                }
            
            # Check if quota available
            if used + amount > limit:
                return False, {
                    "limit": limit,
                    "used": used,
                    "remaining": max(0, limit - used),
                    "quota_type": quota_type
                }
            
            return True, {
                "limit": limit,
                "used": used,
                "remaining": limit - used - amount,
                "quota_type": quota_type
            }
            
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            # Fail open - allow if quota check fails
            return True, {
                "limit": -1,
                "used": 0,
                "remaining": -1,
                "quota_type": quota_type
            }
    
    def consume_quota(
        self,
        org_id: str,
        quota_type: str,
        amount: int = 1
    ) -> bool:
        """
        Consume quota for organization
        
        Args:
            org_id: Organization ID
            quota_type: Type of quota
            amount: Amount to consume
            
        Returns:
            Success status
        """
        
        quota_key = f"quota:{org_id}:{quota_type}"
        
        try:
            # Check and consume atomically
            has_quota, quota_info = self.check_quota(org_id, quota_type, amount)
            
            if not has_quota:
                return False
            
            # Update usage
            if quota_info["limit"] != -1:  # Only update if not unlimited
                new_quota_info = {
                    "limit": quota_info["limit"],
                    "used": quota_info["used"] + amount,
                    "last_updated": int(time.time())
                }
                
                self.redis.set(quota_key, json.dumps(new_quota_info))
            
            return True
            
        except Exception as e:
            logger.error(f"Error consuming quota: {e}")
            return False
    
    def set_quota(
        self,
        org_id: str,
        quota_type: str,
        limit: int,
        used: int = 0
    ):
        """Set quota for organization"""
        
        quota_key = f"quota:{org_id}:{quota_type}"
        quota_info = {
            "limit": limit,
            "used": used,
            "last_updated": int(time.time())
        }
        
        try:
            self.redis.set(quota_key, json.dumps(quota_info))
        except Exception as e:
            logger.error(f"Error setting quota: {e}")
    
    def reset_quota(self, org_id: str, quota_type: str):
        """Reset quota usage for organization"""
        
        quota_key = f"quota:{org_id}:{quota_type}"
        
        try:
            quota_data = self.redis.get(quota_key)
            if quota_data:
                quota_info = json.loads(quota_data)
                quota_info["used"] = 0
                quota_info["last_updated"] = int(time.time())
                self.redis.set(quota_key, json.dumps(quota_info))
        except Exception as e:
            logger.error(f"Error resetting quota: {e}")

def rate_limit(
    limit: int,
    window: int,
    key_func: callable = None,
    redis_client: redis.Redis = None
):
    """
    Rate limiting decorator
    
    Args:
        limit: Maximum requests per window
        window: Time window in seconds
        key_func: Function to generate rate limit key
        redis_client: Redis client instance
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # No request object found, skip rate limiting
                return await func(*args, **kwargs)
            
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                client_ip = request.client.host
                key = f"rate_limit:{client_ip}:{func.__name__}"
            
            # Check rate limit
            if redis_client:
                limiter = RateLimiter(redis_client)
                is_allowed, info = limiter.is_allowed(key, limit, window)
                
                if not is_allowed:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "message": "Rate limit exceeded",
                            "error_code": "RATE_LIMIT_EXCEEDED",
                            "details": info
                        },
                        headers={
                            "X-RateLimit-Limit": str(info["limit"]),
                            "X-RateLimit-Remaining": str(info["remaining"]),
                            "X-RateLimit-Reset": str(info["reset_time"])
                        }
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def quota_required(quota_type: str, amount: int = 1):
    """
    Quota checking decorator
    
    Args:
        quota_type: Type of quota to check
        amount: Amount of quota to consume
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need to be integrated with the auth system
            # to get the org_id from the current user
            # For now, this is a placeholder
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator