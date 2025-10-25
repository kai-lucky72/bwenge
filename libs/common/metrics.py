from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'service']
)

ACTIVE_CONNECTIONS = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections',
    ['service']
)

TASK_COUNT = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status', 'service']
)

TASK_DURATION = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name', 'service']
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections',
    ['service']
)

VECTOR_DB_OPERATIONS = Counter(
    'vector_db_operations_total',
    'Total vector database operations',
    ['operation', 'status', 'service']
)

LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'status', 'service']
)

LLM_TOKENS = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['provider', 'model', 'type', 'service']  # type: prompt, completion
)

def track_request_metrics(service_name: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                # Extract request info (this is FastAPI specific)
                request = None
                for arg in args:
                    if hasattr(arg, 'method') and hasattr(arg, 'url'):
                        request = arg
                        break
                
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                duration = time.time() - start_time
                
                if request:
                    method = request.method
                    endpoint = str(request.url.path)
                    
                    REQUEST_COUNT.labels(
                        method=method,
                        endpoint=endpoint,
                        status_code=status_code,
                        service=service_name
                    ).inc()
                    
                    REQUEST_DURATION.labels(
                        method=method,
                        endpoint=endpoint,
                        service=service_name
                    ).observe(duration)
        
        return wrapper
    return decorator

def track_task_metrics(service_name: str):
    """Decorator to track Celery task metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            task_name = func.__name__
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failure"
                logger.error(f"Task {task_name} failed: {e}")
                raise
            finally:
                duration = time.time() - start_time
                
                TASK_COUNT.labels(
                    task_name=task_name,
                    status=status,
                    service=service_name
                ).inc()
                
                TASK_DURATION.labels(
                    task_name=task_name,
                    service=service_name
                ).observe(duration)
        
        return wrapper
    return decorator

def track_llm_request(provider: str, model: str, service_name: str, status: str = "success"):
    """Track LLM request metrics"""
    LLM_REQUESTS.labels(
        provider=provider,
        model=model,
        status=status,
        service=service_name
    ).inc()

def track_llm_tokens(provider: str, model: str, service_name: str, prompt_tokens: int, completion_tokens: int):
    """Track LLM token usage"""
    LLM_TOKENS.labels(
        provider=provider,
        model=model,
        type="prompt",
        service=service_name
    ).inc(prompt_tokens)
    
    LLM_TOKENS.labels(
        provider=provider,
        model=model,
        type="completion",
        service=service_name
    ).inc(completion_tokens)

def track_vector_db_operation(operation: str, service_name: str, status: str = "success"):
    """Track vector database operations"""
    VECTOR_DB_OPERATIONS.labels(
        operation=operation,
        status=status,
        service=service_name
    ).inc()

def increment_active_connections(service_name: str):
    """Increment active WebSocket connections"""
    ACTIVE_CONNECTIONS.labels(service=service_name).inc()

def decrement_active_connections(service_name: str):
    """Decrement active WebSocket connections"""
    ACTIVE_CONNECTIONS.labels(service=service_name).dec()

def get_metrics():
    """Get Prometheus metrics in text format"""
    return generate_latest()

def get_metrics_content_type():
    """Get Prometheus metrics content type"""
    return CONTENT_TYPE_LATEST