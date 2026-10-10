"""Middleware for request ID injection and structured logging context."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RequestIDAndLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate Request ID
        request_id = request.headers.get("x-request-id")
        if not request_id:
            request_id = str(uuid.uuid4())
            
        # Store in request state so routes/services can access it if needed
        request.state.request_id = request_id
        
        # Bind structlog contextvars for the duration of this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        
        start_time = time.perf_counter()
        
        # Log request started
        logger.info("request_started")
        
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            
            # Log completed successfully
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_s=process_time,
            )
            
            # Inject request ID into response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            process_time = time.perf_counter() - start_time
            # Log failed
            logger.error(
                "request_failed",
                error=str(exc),
                duration_s=process_time,
            )
            raise

