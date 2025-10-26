"""
Distributed Tracing Configuration for Bwenge OS

This module provides OpenTelemetry-based distributed tracing
with Jaeger integration for better observability.
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

class TracingConfig:
    """Configuration for distributed tracing."""
    
    def __init__(self):
        self.service_name = os.getenv("SERVICE_NAME", "bwenge-service")
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.tracing_enabled = os.getenv("TRACING_ENABLED", "true").lower() == "true"
        self.sample_rate = float(os.getenv("TRACING_SAMPLE_RATE", "1.0"))

def setup_tracing(service_name: str, service_version: str = "1.0.0") -> Optional[trace.Tracer]:
    """
    Setup distributed tracing with Jaeger.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        
    Returns:
        Tracer instance if tracing is enabled, None otherwise
    """
    config = TracingConfig()
    
    if not config.tracing_enabled:
        logger.info("Tracing is disabled")
        return None
    
    try:
        # Create resource with service information
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: config.environment,
        })
        
        # Setup tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer_provider = trace.get_tracer_provider()
        
        # Setup Jaeger exporter
        jaeger_exporter = JaegerExporter(
            endpoint=config.jaeger_endpoint,
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Get tracer
        tracer = trace.get_tracer(service_name, service_version)
        
        # Auto-instrument common libraries
        FastAPIInstrumentor.instrument()
        RequestsInstrumentor.instrument()
        SQLAlchemyInstrumentor.instrument()
        RedisInstrumentor.instrument()
        Psycopg2Instrumentor.instrument()
        
        logger.info(f"Tracing initialized for service: {service_name}")
        return tracer
        
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")
        return None

def get_tracer(service_name: str = None) -> trace.Tracer:
    """Get tracer instance."""
    if service_name is None:
        service_name = os.getenv("SERVICE_NAME", "bwenge-service")
    
    return trace.get_tracer(service_name)

def trace_function(operation_name: str = None, tags: Dict[str, Any] = None):
    """
    Decorator to trace function execution.
    
    Args:
        operation_name: Name of the operation (defaults to function name)
        tags: Additional tags to add to the span
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(op_name) as span:
                # Add tags
                if tags:
                    for key, value in tags.items():
                        span.set_attribute(key, str(value))
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator

async def trace_async_function(operation_name: str = None, tags: Dict[str, Any] = None):
    """
    Decorator to trace async function execution.
    
    Args:
        operation_name: Name of the operation (defaults to function name)
        tags: Additional tags to add to the span
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(op_name) as span:
                # Add tags
                if tags:
                    for key, value in tags.items():
                        span.set_attribute(key, str(value))
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator

class TracingMiddleware:
    """FastAPI middleware for enhanced tracing."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        tracer = get_tracer()
        
        # Extract request info
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        with tracer.start_as_current_span(f"{method} {path}") as span:
            # Add request attributes
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", path)
            span.set_attribute("http.scheme", scope.get("scheme", ""))
            
            # Add headers (selective)
            headers = dict(scope.get("headers", []))
            if b"user-agent" in headers:
                span.set_attribute("http.user_agent", headers[b"user-agent"].decode())
            if b"x-tenant-id" in headers:
                span.set_attribute("tenant.id", headers[b"x-tenant-id"].decode())
            
            # Process request
            try:
                await self.app(scope, receive, send)
                span.set_attribute("http.status_code", 200)  # Default success
            except Exception as e:
                span.set_attribute("http.status_code", 500)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
                raise

def trace_database_operation(operation: str, table: str = None):
    """
    Trace database operations.
    
    Args:
        operation: Type of database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Database table name
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(f"db.{operation.lower()}") as span:
                span.set_attribute("db.operation", operation)
                if table:
                    span.set_attribute("db.table", table)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("db.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("db.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator

def trace_ai_operation(model: str = None, operation: str = None):
    """
    Trace AI/ML operations.
    
    Args:
        model: AI model name (e.g., "gpt-3.5-turbo")
        operation: Type of AI operation (e.g., "completion", "embedding")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(f"ai.{operation or 'operation'}") as span:
                if model:
                    span.set_attribute("ai.model", model)
                if operation:
                    span.set_attribute("ai.operation", operation)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("ai.result", "success")
                    
                    # Add token usage if available
                    if hasattr(result, 'usage'):
                        span.set_attribute("ai.tokens.prompt", getattr(result.usage, 'prompt_tokens', 0))
                        span.set_attribute("ai.tokens.completion", getattr(result.usage, 'completion_tokens', 0))
                        span.set_attribute("ai.tokens.total", getattr(result.usage, 'total_tokens', 0))
                    
                    return result
                except Exception as e:
                    span.set_attribute("ai.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator

def trace_file_operation(operation: str, file_type: str = None):
    """
    Trace file operations.
    
    Args:
        operation: Type of file operation (upload, process, delete)
        file_type: Type of file (pdf, audio, video, etc.)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.start_as_current_span(f"file.{operation}") as span:
                span.set_attribute("file.operation", operation)
                if file_type:
                    span.set_attribute("file.type", file_type)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("file.result", "success")
                    
                    # Add file size if available
                    if isinstance(result, dict) and "file_size" in result:
                        span.set_attribute("file.size", result["file_size"])
                    
                    return result
                except Exception as e:
                    span.set_attribute("file.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator

def add_span_attributes(**attributes):
    """Add attributes to the current span."""
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))

def add_span_event(name: str, attributes: Dict[str, Any] = None):
    """Add an event to the current span."""
    current_span = trace.get_current_span()
    if current_span:
        current_span.add_event(name, attributes or {})

def get_trace_id() -> str:
    """Get the current trace ID."""
    current_span = trace.get_current_span()
    if current_span:
        return format(current_span.get_span_context().trace_id, '032x')
    return ""

def get_span_id() -> str:
    """Get the current span ID."""
    current_span = trace.get_current_span()
    if current_span:
        return format(current_span.get_span_context().span_id, '016x')
    return ""