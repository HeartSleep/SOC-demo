"""
Response Interceptor Middleware
Ensures consistent response format across all endpoints
"""
from typing import Any, Callable, Dict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json
import time
from datetime import datetime
import traceback
from app.core.logging import get_logger

logger = get_logger(__name__)


class ResponseInterceptorMiddleware:
    """
    Middleware to intercept and standardize all API responses
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Track request timing
        start_time = time.time()
        request_id = f"{datetime.utcnow().timestamp()}-{id(request)}"

        # Add request ID to request state
        request.state.request_id = request_id

        try:
            # Process the request
            response = await call_next(request)

            # Calculate response time
            process_time = round((time.time() - start_time) * 1000, 2)

            # Add standard headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{process_time}ms"

            # For API routes, standardize JSON responses
            if request.url.path.startswith("/api/v1"):
                # Read response body
                if hasattr(response, "body_iterator"):
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk

                    try:
                        # Parse JSON response
                        data = json.loads(body.decode())

                        # Standardize successful responses
                        if response.status_code < 400:
                            # Check if already standardized
                            if not isinstance(data, dict) or "success" not in data:
                                # Wrap response in standard format
                                if isinstance(data, list):
                                    # List responses (for compatibility)
                                    standardized = data
                                elif "items" in data and "total" in data:
                                    # Already paginated
                                    standardized = data
                                else:
                                    # Single entity
                                    standardized = data

                                # Log successful request
                                logger.info(
                                    f"Request {request_id}: {request.method} {request.url.path} "
                                    f"completed in {process_time}ms"
                                )

                                # Return standardized response
                                return JSONResponse(
                                    content=standardized,
                                    status_code=response.status_code,
                                    headers=dict(response.headers)
                                )
                        else:
                            # Standardize error responses
                            if "detail" not in data:
                                standardized = {
                                    "success": False,
                                    "error": {
                                        "message": data.get("message", "An error occurred"),
                                        "code": response.status_code,
                                        "details": data
                                    },
                                    "request_id": request_id
                                }

                                return JSONResponse(
                                    content=standardized,
                                    status_code=response.status_code,
                                    headers=dict(response.headers)
                                )

                    except json.JSONDecodeError:
                        # Non-JSON response, pass through
                        pass

            return response

        except Exception as e:
            # Log error
            logger.error(
                f"Request {request_id} failed: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )

            # Return standardized error response
            return JSONResponse(
                content={
                    "success": False,
                    "error": {
                        "message": "Internal server error",
                        "code": 500,
                        "details": str(e) if logger.level <= 10 else None  # Only in DEBUG
                    },
                    "request_id": request_id
                },
                status_code=500,
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time": f"{round((time.time() - start_time) * 1000, 2)}ms"
                }
            )


class PaginationMiddleware:
    """
    Middleware to handle pagination parameters consistently
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Extract pagination params from query
        if request.method == "GET" and "/api/v1" in str(request.url):
            query_params = dict(request.query_params)

            # Standardize pagination parameters
            page = int(query_params.get("page", 1))
            size = int(query_params.get("size", 20))
            skip = int(query_params.get("skip", (page - 1) * size))
            limit = int(query_params.get("limit", size))

            # Add standardized params to request state
            request.state.pagination = {
                "page": page,
                "size": size,
                "skip": skip,
                "limit": limit
            }

        response = await call_next(request)
        return response


class CacheControlMiddleware:
    """
    Middleware to add cache control headers
    """

    def __init__(self, app):
        self.app = app
        self.cache_config = {
            # Static resources - long cache
            "/assets/": "public, max-age=31536000",  # 1 year
            "/static/": "public, max-age=31536000",  # 1 year

            # API responses - shorter cache
            "/api/v1/assets/": "private, max-age=60",  # 1 minute
            "/api/v1/users/": "private, max-age=300",  # 5 minutes
            "/api/v1/reports/": "private, max-age=300",  # 5 minutes

            # Real-time data - no cache
            "/api/v1/tasks/": "no-cache, no-store, must-revalidate",
            "/api/v1/vulnerabilities/": "no-cache, no-store, must-revalidate",
            "/ws/": "no-cache, no-store, must-revalidate",

            # Auth endpoints - never cache
            "/api/v1/auth/": "no-cache, no-store, must-revalidate",
        }

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Apply cache control based on path
        path = str(request.url.path)
        for pattern, cache_control in self.cache_config.items():
            if path.startswith(pattern):
                response.headers["Cache-Control"] = cache_control
                break
        else:
            # Default cache control
            response.headers["Cache-Control"] = "private, max-age=0"

        return response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        if request.url.path.startswith("/api/"):
            # API endpoints - strict CSP
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        else:
            # Web pages - relaxed CSP for development
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' data:; "
                "frame-ancestors 'none';"
            )

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        return response


class RequestLoggingMiddleware:
    """
    Middleware to log all requests and responses
    """

    def __init__(self, app):
        self.app = app
        self.exclude_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Log request
        start_time = time.time()
        request_body = None

        # Try to read request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.body()
                # Create new request with body for downstream
                request = Request(request.scope, receive=lambda: {"type": "http.request", "body": request_body})
            except:
                pass

        # Log incoming request
        log_data = {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "headers": {k: v for k, v in request.headers.items() if k.lower() != "authorization"},
            "client": request.client.host if request.client else "unknown"
        }

        if request_body and len(request_body) < 10000:  # Don't log large bodies
            try:
                log_data["body"] = json.loads(request_body.decode())
            except:
                log_data["body"] = "Binary or non-JSON data"

        logger.debug(f"Incoming request: {json.dumps(log_data, default=str)}")

        # Process request
        response = await call_next(request)

        # Log response
        duration = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} ({duration}ms)"
        )

        return response


def setup_middleware(app):
    """
    Setup all middleware in the correct order
    """
    from fastapi import FastAPI

    # Order matters! Applied in reverse order
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(PaginationMiddleware)
    app.add_middleware(ResponseInterceptorMiddleware)

    logger.info("Response interceptor middleware configured")