#!/usr/bin/env python3
"""
API Gateway for SOC Platform Microservices
Routes requests to appropriate microservices with authentication and rate limiting
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import consul
import redis
import jwt
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache
import json
from prometheus_client import Counter, Histogram, generate_latest
from circuitbreaker import circuit
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
request_counter = Counter('gateway_requests_total', 'Total requests', ['method', 'service', 'status'])
request_duration = Histogram('gateway_request_duration_seconds', 'Request duration', ['service'])

app = FastAPI(title="SOC Platform API Gateway", version="1.0.0")

# Configuration
class Settings:
    jwt_secret: str = "your-secret-key"
    redis_url: str = "redis://redis:6379"
    consul_host: str = "consul"
    consul_port: int = 8500
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30
    cache_ttl: int = 300
    cors_origins: List[str] = ["*"]
    timeout: int = 30

@lru_cache()
def get_settings():
    return Settings()

# Initialize connections
settings = get_settings()
redis_client = redis.from_url(settings.redis_url, decode_responses=True)
consul_client = consul.Consul(host=settings.consul_host, port=settings.consul_port)
http_client = httpx.AsyncClient(timeout=settings.timeout)

# Service registry
class ServiceRegistry:
    """Service discovery using Consul"""

    def __init__(self, consul_client):
        self.consul = consul_client
        self.services_cache = {}
        self.cache_ttl = 10

    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service endpoint from Consul"""
        # Check cache
        if service_name in self.services_cache:
            cached, timestamp = self.services_cache[service_name]
            if time.time() - timestamp < self.cache_ttl:
                return cached

        try:
            _, services = self.consul.health.service(service_name, passing=True)
            if services:
                service = services[0]
                endpoint = {
                    "host": service["Service"]["Address"] or service["Node"]["Address"],
                    "port": service["Service"]["Port"]
                }
                self.services_cache[service_name] = (endpoint, time.time())
                return endpoint
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return None

    def register_service(self, name: str, port: int, tags: List[str] = None):
        """Register service with Consul"""
        try:
            self.consul.agent.service.register(
                name=name,
                service_id=f"{name}-{port}",
                port=port,
                tags=tags or [],
                check=consul.Check.http(
                    f"http://localhost:{port}/health",
                    interval="10s",
                    timeout="5s"
                )
            )
            logger.info(f"Registered service {name} on port {port}")
        except Exception as e:
            logger.error(f"Failed to register service {name}: {e}")

service_registry = ServiceRegistry(consul_client)

# Authentication
class AuthHandler:
    """JWT authentication handler"""

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def get_current_user(request: Request) -> Dict[str, Any]:
        """Extract user from request"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication"
            )

        token = auth_header.split(" ")[1]
        return AuthHandler.decode_token(token)

# Rate limiting
class RateLimiter:
    """Redis-based rate limiter"""

    @staticmethod
    async def check_rate_limit(client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        key = f"rate_limit:{client_id}"
        current_time = int(time.time())
        window_start = current_time - settings.rate_limit_window

        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        request_count = redis_client.zcard(key)

        if request_count >= settings.rate_limit_requests:
            return False

        # Add current request
        redis_client.zadd(key, {str(current_time): current_time})
        redis_client.expire(key, settings.rate_limit_window)

        return True

# Circuit breaker
class CircuitBreaker:
    """Circuit breaker for service calls"""

    def __init__(self):
        self.failures = {}
        self.last_failure_time = {}
        self.state = {}  # CLOSED, OPEN, HALF_OPEN

    def call_service(self, service_name: str):
        """Check circuit breaker state"""
        state = self.state.get(service_name, "CLOSED")

        if state == "OPEN":
            # Check if timeout has passed
            if time.time() - self.last_failure_time.get(service_name, 0) > settings.circuit_breaker_timeout:
                self.state[service_name] = "HALF_OPEN"
                self.failures[service_name] = 0
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {service_name} is unavailable"
                )

    def record_success(self, service_name: str):
        """Record successful call"""
        self.failures[service_name] = 0
        self.state[service_name] = "CLOSED"

    def record_failure(self, service_name: str):
        """Record failed call"""
        self.failures[service_name] = self.failures.get(service_name, 0) + 1

        if self.failures[service_name] >= settings.circuit_breaker_threshold:
            self.state[service_name] = "OPEN"
            self.last_failure_time[service_name] = time.time()
            logger.warning(f"Circuit breaker opened for service {service_name}")

circuit_breaker = CircuitBreaker()

# Request routing
class RequestRouter:
    """Route requests to appropriate microservices"""

    def __init__(self):
        self.routes = {
            "/api/users": "user-service",
            "/api/assets": "asset-service",
            "/api/vulnerabilities": "vulnerability-service",
            "/api/scans": "scanning-service",
            "/api/notifications": "notification-service",
            "/api/analytics": "analytics-service",
            "/api/reports": "reporting-service",
            "/api/monitoring": "monitoring-service",
            "/api/compliance": "compliance-service",
            "/api/threat-intel": "threat-intel-service"
        }

    def get_service_for_path(self, path: str) -> Optional[str]:
        """Determine which service handles the path"""
        for route_prefix, service in self.routes.items():
            if path.startswith(route_prefix):
                return service
        return None

    async def forward_request(
        self,
        service_name: str,
        method: str,
        path: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        body: Optional[bytes] = None
    ) -> JSONResponse:
        """Forward request to microservice"""

        # Check circuit breaker
        circuit_breaker.call_service(service_name)

        # Get service endpoint
        service = service_registry.get_service(service_name)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} not available"
            )

        # Build URL
        url = f"http://{service['host']}:{service['port']}{path}"

        # Forward request
        try:
            start_time = time.time()

            response = await http_client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                content=body
            )

            # Record metrics
            duration = time.time() - start_time
            request_counter.labels(method=method, service=service_name, status=response.status_code).inc()
            request_duration.labels(service=service_name).observe(duration)

            # Record success
            circuit_breaker.record_success(service_name)

            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except httpx.TimeoutException:
            circuit_breaker.record_failure(service_name)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service {service_name} timeout"
            )
        except Exception as e:
            circuit_breaker.record_failure(service_name)
            logger.error(f"Error forwarding to {service_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with {service_name}"
            )

request_router = RequestRouter()

# Response caching
class ResponseCache:
    """Cache responses in Redis"""

    @staticmethod
    def get_cache_key(method: str, path: str, params: Dict[str, Any]) -> str:
        """Generate cache key"""
        key_data = f"{method}:{path}:{json.dumps(params, sort_keys=True)}"
        return f"cache:{hashlib.sha256(key_data.encode()).hexdigest()}"

    @staticmethod
    async def get(key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    @staticmethod
    async def set(key: str, data: Dict[str, Any], ttl: int = None):
        """Cache response"""
        redis_client.setex(
            key,
            ttl or settings.cache_ttl,
            json.dumps(data)
        )

response_cache = ResponseCache()

# Middleware
@app.middleware("http")
async def add_middleware(request: Request, call_next):
    """Add common middleware processing"""

    # Add request ID
    request_id = request.headers.get("X-Request-ID", str(time.time()))

    # Log request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")

    # Add security headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Health check
@app.get("/health")
async def health_check():
    """Gateway health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": len(service_registry.services_cache),
        "version": "1.0.0"
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    return generate_latest()

# Service discovery endpoint
@app.get("/services")
async def list_services(current_user: Dict = Depends(AuthHandler.get_current_user)):
    """List all registered services"""
    try:
        _, services = consul_client.catalog.services()
        return {"services": list(services.keys())}
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        return {"services": []}

# Main gateway route
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_route(
    request: Request,
    path: str,
    current_user: Optional[Dict] = None
):
    """Main gateway routing logic"""

    # Get client ID for rate limiting
    client_id = request.client.host

    # Check rate limit
    if not await RateLimiter.check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    # Determine target service
    service_name = request_router.get_service_for_path(f"/{path}")
    if not service_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    # Check authentication for protected routes
    if not path.startswith("api/auth/login"):
        current_user = AuthHandler.get_current_user(request)

    # Check cache for GET requests
    if request.method == "GET":
        cache_key = response_cache.get_cache_key(
            request.method,
            path,
            dict(request.query_params)
        )
        cached_response = await response_cache.get(cache_key)
        if cached_response:
            return JSONResponse(content=cached_response)

    # Prepare headers
    headers = dict(request.headers)
    headers["X-User-ID"] = str(current_user.get("sub", "")) if current_user else ""
    headers["X-Forwarded-For"] = client_id

    # Get request body
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None

    # Forward request
    response = await request_router.forward_request(
        service_name=service_name,
        method=request.method,
        path=f"/{path}",
        headers=headers,
        params=dict(request.query_params),
        body=body
    )

    # Cache successful GET responses
    if request.method == "GET" and response.status_code == 200:
        await response_cache.set(cache_key, response.body)

    return response

# WebSocket proxy
@app.websocket("/ws/{service_name}/{path:path}")
async def websocket_proxy(websocket, service_name: str, path: str):
    """Proxy WebSocket connections"""
    service = service_registry.get_service(service_name)
    if not service:
        await websocket.close(code=1008, reason="Service not available")
        return

    ws_url = f"ws://{service['host']}:{service['port']}/ws/{path}"

    async with httpx.AsyncClient() as client:
        async with client.websocket(ws_url) as service_ws:
            # Forward messages bidirectionally
            async def forward_to_service():
                async for message in websocket:
                    await service_ws.send(message)

            async def forward_to_client():
                async for message in service_ws:
                    await websocket.send(message)

            await asyncio.gather(
                forward_to_service(),
                forward_to_client()
            )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup"""
    # Register gateway itself with Consul
    service_registry.register_service(
        name="api-gateway",
        port=8080,
        tags=["gateway", "api"]
    )

    logger.info("API Gateway started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()
    redis_client.close()
    logger.info("API Gateway shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)