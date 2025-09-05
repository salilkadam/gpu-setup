"""
Error Handlers for the Routing API

This module provides centralized error handling for the routing system.
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class RoutingError(Exception):
    """Base exception for routing system errors."""
    
    def __init__(self, message: str, error_code: str = "ROUTING_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class ModelNotFoundError(RoutingError):
    """Exception raised when a model is not found."""
    
    def __init__(self, model_id: str):
        super().__init__(
            message=f"Model {model_id} not found",
            error_code="MODEL_NOT_FOUND",
            status_code=404
        )


class ModelLoadError(RoutingError):
    """Exception raised when model loading fails."""
    
    def __init__(self, model_id: str, reason: str):
        super().__init__(
            message=f"Failed to load model {model_id}: {reason}",
            error_code="MODEL_LOAD_ERROR",
            status_code=500
        )


class BackendError(RoutingError):
    """Exception raised when backend operations fail."""
    
    def __init__(self, backend_name: str, reason: str):
        super().__init__(
            message=f"Backend {backend_name} error: {reason}",
            error_code="BACKEND_ERROR",
            status_code=500
        )


class InsufficientResourcesError(RoutingError):
    """Exception raised when there are insufficient resources."""
    
    def __init__(self, resource_type: str, required: str, available: str):
        super().__init__(
            message=f"Insufficient {resource_type}: required {required}, available {available}",
            error_code="INSUFFICIENT_RESOURCES",
            status_code=507  # Insufficient Storage
        )


class ClassificationError(RoutingError):
    """Exception raised when query classification fails."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Query classification failed: {reason}",
            error_code="CLASSIFICATION_ERROR",
            status_code=400
        )


def setup_error_handlers(app: FastAPI):
    """Setup error handlers for the FastAPI application."""
    
    @app.exception_handler(RoutingError)
    async def routing_error_handler(request: Request, exc: RoutingError):
        """Handle routing system errors."""
        logger.error(f"Routing error: {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "RoutingError",
                    "code": exc.error_code,
                    "message": exc.message,
                    "timestamp": getattr(request.state, "timestamp", "unknown")
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.error(f"HTTP error: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "HTTPException",
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "timestamp": getattr(request.state, "timestamp", "unknown")
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions."""
        logger.error(f"Starlette HTTP error: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "StarletteHTTPException",
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "timestamp": getattr(request.state, "timestamp", "unknown")
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.error(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "ValidationError",
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "timestamp": getattr(request.state, "timestamp", "unknown")
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "InternalServerError",
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "timestamp": getattr(request.state, "timestamp", "unknown")
                }
            }
        )
    
    @app.middleware("http")
    async def add_timestamp_middleware(request: Request, call_next):
        """Add timestamp to request state for error handling."""
        import time
        request.state.timestamp = time.time()
        response = await call_next(request)
        return response
    
    @app.middleware("http")
    async def log_requests_middleware(request: Request, call_next):
        """Log all requests for debugging."""
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        return response


# Utility functions for error handling
def handle_model_error(model_id: str, operation: str, error: Exception) -> RoutingError:
    """Create appropriate error for model operations."""
    if "not found" in str(error).lower():
        return ModelNotFoundError(model_id)
    elif "load" in operation.lower():
        return ModelLoadError(model_id, str(error))
    else:
        return RoutingError(f"Model {operation} failed: {str(error)}")


def handle_backend_error(backend_name: str, operation: str, error: Exception) -> BackendError:
    """Create appropriate error for backend operations."""
    return BackendError(backend_name, f"{operation}: {str(error)}")


def handle_resource_error(resource_type: str, required: str, available: str) -> InsufficientResourcesError:
    """Create appropriate error for resource issues."""
    return InsufficientResourcesError(resource_type, required, available)


def handle_classification_error(error: Exception) -> ClassificationError:
    """Create appropriate error for classification issues."""
    return ClassificationError(str(error))


# Example usage
if __name__ == "__main__":
    # Example of how to use the error classes
    try:
        raise ModelNotFoundError("microsoft/phi-2")
    except RoutingError as e:
        print(f"Error: {e.message}")
        print(f"Code: {e.error_code}")
        print(f"Status: {e.status_code}")
    
    try:
        raise ModelLoadError("Qwen/Qwen2.5-7B-Instruct", "Insufficient memory")
    except RoutingError as e:
        print(f"Error: {e.message}")
        print(f"Code: {e.error_code}")
        print(f"Status: {e.status_code}")
    
    try:
        raise BackendError("vLLM", "Connection timeout")
    except RoutingError as e:
        print(f"Error: {e.message}")
        print(f"Code: {e.error_code}")
        print(f"Status: {e.status_code}")
