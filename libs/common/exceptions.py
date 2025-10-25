from fastapi import HTTPException
from typing import Dict, Any, Optional

class BwengeException(Exception):
    """Base exception for Bwenge OS"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(BwengeException):
    """Authentication related errors"""
    pass

class AuthorizationError(BwengeException):
    """Authorization related errors"""
    pass

class ValidationError(BwengeException):
    """Data validation errors"""
    pass

class NotFoundError(BwengeException):
    """Resource not found errors"""
    pass

class ConflictError(BwengeException):
    """Resource conflict errors"""
    pass

class ExternalServiceError(BwengeException):
    """External service integration errors"""
    pass

class LLMError(ExternalServiceError):
    """LLM service errors"""
    pass

class VectorDBError(ExternalServiceError):
    """Vector database errors"""
    pass

class StorageError(ExternalServiceError):
    """File storage errors"""
    pass

class PaymentError(ExternalServiceError):
    """Payment processing errors"""
    pass

class QuotaExceededError(BwengeException):
    """Usage quota exceeded errors"""
    pass

class ProcessingError(BwengeException):
    """File processing errors"""
    pass

# HTTP Exception mappings
def to_http_exception(error: BwengeException) -> HTTPException:
    """Convert Bwenge exception to HTTP exception"""
    
    status_code_map = {
        AuthenticationError: 401,
        AuthorizationError: 403,
        NotFoundError: 404,
        ConflictError: 409,
        ValidationError: 422,
        QuotaExceededError: 429,
        ExternalServiceError: 502,
        LLMError: 502,
        VectorDBError: 502,
        StorageError: 502,
        PaymentError: 502,
        ProcessingError: 500,
        BwengeException: 500
    }
    
    status_code = status_code_map.get(type(error), 500)
    
    detail = {
        "message": error.message,
        "error_code": error.error_code,
        "details": error.details
    }
    
    return HTTPException(status_code=status_code, detail=detail)

# Error handler decorator
def handle_exceptions(func):
    """Decorator to handle exceptions and convert to HTTP exceptions"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BwengeException as e:
            raise to_http_exception(e)
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            
            # Convert to generic HTTP exception
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "details": {}
                }
            )
    
    return wrapper