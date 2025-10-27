"""
GraphQL Application Integration for FastAPI
Integrates Strawberry GraphQL with FastAPI and adds authentication
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from strawberry.extensions import Extension
from strawberry.utils.logging import StrawberryLogger
from typing import Optional, Dict, Any
import time
import logging
from datetime import datetime
import json

from app.graphql.schema import schema
from app.core.security import decode_access_token
from app.db.database import get_db

# Configure logging
logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthenticationExtension(Extension):
    """Extension to handle authentication for GraphQL requests"""

    def on_request_start(self):
        """Check authentication before processing request"""
        request = self.execution_context.context["request"]

        # Skip auth for introspection queries
        if self.execution_context.query and "IntrospectionQuery" in self.execution_context.query:
            return

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            if self.requires_authentication():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            return

        # Validate token
        token = auth_header.split(" ")[1]
        try:
            payload = decode_access_token(token)
            self.execution_context.context["user"] = payload
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

    def requires_authentication(self) -> bool:
        """Check if the current operation requires authentication"""
        # List of public operations that don't require auth
        public_operations = ["login", "register", "healthCheck"]

        operation_name = getattr(self.execution_context, "operation_name", None)
        if operation_name and operation_name in public_operations:
            return False

        return True


class PerformanceExtension(Extension):
    """Extension to track GraphQL query performance"""

    def on_request_start(self):
        self.start_time = time.time()

    def on_request_end(self):
        duration = (time.time() - self.start_time) * 1000  # Convert to ms

        request = self.execution_context.context["request"]
        operation_name = getattr(self.execution_context, "operation_name", "unknown")

        logger.info(
            f"GraphQL Request - "
            f"Operation: {operation_name}, "
            f"Duration: {duration:.2f}ms, "
            f"IP: {request.client.host}"
        )

        # Store metrics
        if hasattr(request.app, "graphql_metrics"):
            request.app.graphql_metrics.append({
                "operation": operation_name,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "success": not hasattr(self.execution_context, "errors")
            })


class RateLimitExtension(Extension):
    """Extension to implement rate limiting for GraphQL"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts: Dict[str, list] = {}

    def on_request_start(self):
        request = self.execution_context.context["request"]
        client_id = request.client.host

        now = time.time()

        # Clean old requests
        if client_id in self.request_counts:
            self.request_counts[client_id] = [
                t for t in self.request_counts[client_id]
                if now - t < self.window_seconds
            ]
        else:
            self.request_counts[client_id] = []

        # Check rate limit
        if len(self.request_counts[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
            )

        # Record request
        self.request_counts[client_id].append(now)


class QueryDepthLimitExtension(Extension):
    """Extension to limit query depth to prevent abuse"""

    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth

    def on_request_start(self):
        depth = self.calculate_query_depth(self.execution_context.query)
        if depth > self.max_depth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query depth {depth} exceeds maximum allowed depth {self.max_depth}"
            )

    def calculate_query_depth(self, query: str) -> int:
        """Calculate the depth of a GraphQL query"""
        # Simplified depth calculation
        depth = 0
        current_depth = 0

        for char in query:
            if char == '{':
                current_depth += 1
                depth = max(depth, current_depth)
            elif char == '}':
                current_depth -= 1

        return depth


class CachingExtension(Extension):
    """Extension to cache GraphQL query results"""

    def __init__(self, cache_ttl: int = 60):
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Any] = {}

    def on_request_start(self):
        # Generate cache key from query
        query = self.execution_context.query
        variables = self.execution_context.variables or {}

        cache_key = self.generate_cache_key(query, variables)

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                # Return cached result
                self.execution_context.result = cached_data
                return True

        self.cache_key = cache_key

    def on_request_end(self):
        # Cache the result if successful
        if hasattr(self, "cache_key") and not hasattr(self.execution_context, "errors"):
            self.cache[self.cache_key] = (
                self.execution_context.result,
                time.time()
            )

    def generate_cache_key(self, query: str, variables: dict) -> str:
        """Generate a unique cache key for the query"""
        import hashlib
        key_str = f"{query}:{json.dumps(variables, sort_keys=True)}"
        return hashlib.sha256(key_str.encode()).hexdigest()


async def get_context(request, response):
    """Context getter for GraphQL requests"""
    return {
        "request": request,
        "response": response,
        "db": get_db(),
        "user": None  # Will be populated by AuthenticationExtension
    }


def create_graphql_app() -> GraphQLRouter:
    """Create and configure the GraphQL application"""

    # Configure extensions
    extensions = [
        AuthenticationExtension,
        PerformanceExtension(),
        RateLimitExtension(max_requests=100, window_seconds=60),
        QueryDepthLimitExtension(max_depth=10),
        CachingExtension(cache_ttl=60)
    ]

    # Create GraphQL router
    graphql_app = GraphQLRouter(
        schema,
        context_getter=get_context,
        extensions=extensions,
        graphiql=True  # Enable GraphiQL interface
    )

    return graphql_app


def integrate_graphql(app: FastAPI):
    """Integrate GraphQL with existing FastAPI application"""

    # Initialize metrics storage
    app.graphql_metrics = []

    # Create GraphQL router
    graphql_router = create_graphql_app()

    # Include GraphQL router
    app.include_router(
        graphql_router,
        prefix="/graphql",
        tags=["GraphQL"]
    )

    # Add GraphQL health check
    @app.get("/graphql/health")
    async def graphql_health():
        return {
            "status": "healthy",
            "schema": "loaded",
            "extensions": [
                "authentication",
                "performance",
                "rate_limiting",
                "depth_limiting",
                "caching"
            ]
        }

    # Add GraphQL metrics endpoint
    @app.get("/graphql/metrics")
    async def graphql_metrics():
        # Get recent metrics
        recent_metrics = app.graphql_metrics[-100:] if hasattr(app, "graphql_metrics") else []

        if recent_metrics:
            avg_duration = sum(m["duration"] for m in recent_metrics) / len(recent_metrics)
            success_rate = sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics)
        else:
            avg_duration = 0
            success_rate = 1

        return {
            "total_requests": len(app.graphql_metrics) if hasattr(app, "graphql_metrics") else 0,
            "recent_requests": len(recent_metrics),
            "avg_duration_ms": avg_duration,
            "success_rate": success_rate,
            "operations": list(set(m["operation"] for m in recent_metrics))
        }

    logger.info("GraphQL integration completed successfully")
    logger.info("GraphQL endpoint: /graphql")
    logger.info("GraphiQL interface: /graphql (in browser)")

    return app


# Middleware for GraphQL-specific CORS headers
async def graphql_cors_middleware(request, call_next):
    """Add GraphQL-specific CORS headers"""
    response = await call_next(request)

    if request.url.path.startswith("/graphql"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Max-Age"] = "3600"

    return response