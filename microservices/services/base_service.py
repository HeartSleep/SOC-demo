#!/usr/bin/env python3
"""
Base Microservice Template
Common functionality for all SOC platform microservices
"""

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import consul
import redis
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika
import asyncio
import logging
import time
import os
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import httpx
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceConfig:
    """Service configuration"""

    def __init__(self):
        self.service_name = os.getenv("SERVICE_NAME", "base-service")
        self.service_port = int(os.getenv("SERVICE_PORT", "8000"))
        self.consul_host = os.getenv("CONSUL_HOST", "localhost")
        self.consul_port = int(os.getenv("CONSUL_PORT", "8500"))
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.database_url = os.getenv("DATABASE_URL", "")
        self.mongodb_url = os.getenv("MONGODB_URL", "")
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.jaeger_host = os.getenv("JAEGER_HOST", "localhost")
        self.jaeger_port = int(os.getenv("JAEGER_PORT", "6831"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")


class ServiceMetrics:
    """Service metrics collection"""

    def __init__(self, service_name: str):
        self.request_count = Counter(
            f"{service_name}_requests_total",
            "Total requests",
            ["method", "endpoint", "status"]
        )
        self.request_duration = Histogram(
            f"{service_name}_request_duration_seconds",
            "Request duration",
            ["method", "endpoint"]
        )
        self.active_connections = Gauge(
            f"{service_name}_active_connections",
            "Active connections"
        )
        self.error_count = Counter(
            f"{service_name}_errors_total",
            "Total errors",
            ["error_type"]
        )


class ServiceRegistry:
    """Service registration with Consul"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.consul = consul.Consul(
            host=config.consul_host,
            port=config.consul_port
        )

    async def register(self):
        """Register service with Consul"""
        try:
            self.consul.agent.service.register(
                name=self.config.service_name,
                service_id=f"{self.config.service_name}-{self.config.service_port}",
                address="",
                port=self.config.service_port,
                tags=["microservice", self.config.service_name],
                check=consul.Check.http(
                    f"http://localhost:{self.config.service_port}/health",
                    interval="10s",
                    timeout="5s"
                )
            )
            logger.info(f"Registered {self.config.service_name} with Consul")
        except Exception as e:
            logger.error(f"Failed to register service: {e}")

    async def deregister(self):
        """Deregister service from Consul"""
        try:
            self.consul.agent.service.deregister(
                f"{self.config.service_name}-{self.config.service_port}"
            )
            logger.info(f"Deregistered {self.config.service_name} from Consul")
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")

    async def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover another service"""
        try:
            _, services = self.consul.health.service(service_name, passing=True)
            if services:
                service = services[0]
                return {
                    "host": service["Service"]["Address"] or service["Node"]["Address"],
                    "port": service["Service"]["Port"]
                }
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {e}")
        return None


class MessageBroker:
    """RabbitMQ message broker"""

    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection:
            await self.connection.close()

    async def publish(self, exchange: str, routing_key: str, message: Dict[str, Any]):
        """Publish message"""
        if not self.channel:
            await self.connect()

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json"
            ),
            routing_key=routing_key
        )

    async def subscribe(self, queue_name: str, callback: Callable):
        """Subscribe to queue"""
        if not self.channel:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable=True)

        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                data = json.loads(message.body.decode())
                await callback(data)

        await queue.consume(process_message)


class CacheManager:
    """Redis cache manager"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        """Delete from cache"""
        self.redis.delete(key)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern"""
        for key in self.redis.scan_iter(pattern):
            self.redis.delete(key)


class DatabaseManager:
    """Database connection manager"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None

    async def connect(self):
        """Create connection pool"""
        if self.database_url.startswith("postgresql"):
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("Connected to PostgreSQL")

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection"""
        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch results"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)


class BaseMicroservice(ABC):
    """Base microservice class"""

    def __init__(self, config: ServiceConfig = None):
        self.config = config or ServiceConfig()
        self.app = FastAPI(
            title=self.config.service_name,
            version="1.0.0"
        )
        self.metrics = ServiceMetrics(self.config.service_name)
        self.registry = ServiceRegistry(self.config)
        self.cache = CacheManager(self.config.redis_url) if self.config.redis_url else None
        self.db = DatabaseManager(self.config.database_url) if self.config.database_url else None
        self.mq = MessageBroker(self.config.rabbitmq_url) if self.config.rabbitmq_url else None
        self.http_client = httpx.AsyncClient(timeout=30.0)

        self._setup_middleware()
        self._setup_routes()
        self._setup_tracing()

    def _setup_middleware(self):
        """Setup middleware"""

        @self.app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            start_time = time.time()
            self.metrics.active_connections.inc()

            try:
                response = await call_next(request)

                # Record metrics
                process_time = time.time() - start_time
                self.metrics.request_count.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code
                ).inc()
                self.metrics.request_duration.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(process_time)

                # Add headers
                response.headers["X-Process-Time"] = str(process_time)
                response.headers["X-Service-Name"] = self.config.service_name

                return response

            except Exception as e:
                self.metrics.error_count.labels(error_type=type(e).__name__).inc()
                raise
            finally:
                self.metrics.active_connections.dec()

        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

    def _setup_routes(self):
        """Setup common routes"""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            health_status = await self.check_health()
            return {
                "service": self.config.service_name,
                "status": health_status.get("status", "healthy"),
                "timestamp": datetime.now().isoformat(),
                "details": health_status.get("details", {})
            }

        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            return generate_latest()

        @self.app.get("/info")
        async def service_info():
            """Service information"""
            return {
                "service": self.config.service_name,
                "version": "1.0.0",
                "port": self.config.service_port,
                "dependencies": {
                    "redis": self.cache is not None,
                    "database": self.db is not None,
                    "rabbitmq": self.mq is not None
                }
            }

        # Add service-specific routes
        self.setup_routes()

    def _setup_tracing(self):
        """Setup distributed tracing"""
        trace.set_tracer_provider(TracerProvider())

        jaeger_exporter = JaegerExporter(
            agent_host_name=self.config.jaeger_host,
            agent_port=self.config.jaeger_port,
            collector_endpoint=None
        )

        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(self.app, service=self.config.service_name)

    async def start(self):
        """Start the service"""
        # Register with Consul
        await self.registry.register()

        # Connect to databases
        if self.db:
            await self.db.connect()

        # Connect to message broker
        if self.mq:
            await self.mq.connect()

        # Initialize service
        await self.initialize()

        logger.info(f"{self.config.service_name} started on port {self.config.service_port}")

    async def stop(self):
        """Stop the service"""
        # Cleanup service
        await self.cleanup()

        # Deregister from Consul
        await self.registry.deregister()

        # Disconnect from databases
        if self.db:
            await self.db.disconnect()

        # Disconnect from message broker
        if self.mq:
            await self.mq.disconnect()

        # Close HTTP client
        await self.http_client.aclose()

        logger.info(f"{self.config.service_name} stopped")

    async def call_service(self, service_name: str, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Call another microservice"""
        service = await self.registry.discover_service(service_name)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} not available"
            )

        url = f"http://{service['host']}:{service['port']}{path}"

        try:
            response = await self.http_client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error calling {service_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error calling {service_name}"
            )

    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to message broker"""
        if self.mq:
            await self.mq.publish(
                exchange="events",
                routing_key=event_type,
                message={
                    "event_type": event_type,
                    "service": self.config.service_name,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                }
            )

    @abstractmethod
    async def setup_routes(self):
        """Setup service-specific routes"""
        pass

    @abstractmethod
    async def initialize(self):
        """Initialize service"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup service"""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        pass

    def run(self):
        """Run the service"""
        import uvicorn

        @self.app.on_event("startup")
        async def startup_event():
            await self.start()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.stop()

        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.config.service_port
        )