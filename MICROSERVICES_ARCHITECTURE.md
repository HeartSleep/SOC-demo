# 🚀 Microservices Architecture for SOC Platform

## Overview

The SOC Platform has been redesigned using a **Microservices Architecture** that breaks down the monolithic application into smaller, independently deployable services. This provides better scalability, fault isolation, and development flexibility.

## 🏗️ Architecture Overview

```
                            ┌─────────────┐
                            │   Traefik   │
                            │Load Balancer│
                            └──────┬──────┘
                                   │
                            ┌──────▼──────┐
                            │ API Gateway │
                            │  (Port 8080)│
                            └──────┬──────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
  ┌─────▼─────┐             ┌─────▼─────┐             ┌─────▼─────┐
  │   User    │             │   Asset   │             │   Vuln    │
  │  Service  │             │  Service  │             │  Service  │
  └─────┬─────┘             └─────┬─────┘             └─────┬─────┘
        │                          │                          │
  ┌─────▼─────┐             ┌─────▼─────┐             ┌─────▼─────┐
  │PostgreSQL │             │PostgreSQL │             │PostgreSQL │
  └───────────┘             └───────────┘             └───────────┘
```

## 🔧 Core Components

### 1. **API Gateway** (`gateway/api_gateway.py`)
- **Purpose**: Single entry point for all client requests
- **Port**: 8080
- **Features**:
  - Request routing to microservices
  - Authentication/authorization
  - Rate limiting (100 req/min)
  - Circuit breaker pattern
  - Response caching
  - Request/response logging
  - Metrics collection

### 2. **Service Discovery** (Consul)
- **Purpose**: Dynamic service registration and discovery
- **Port**: 8500 (UI), 8600 (DNS)
- **Features**:
  - Health checking
  - Service catalog
  - Key/value store
  - Multi-datacenter support

### 3. **Microservices**

#### User Service (Port 8001)
```
Responsibilities:
- User registration/authentication
- JWT token management
- Role-based access control
- Session management
- User profile management
```

#### Asset Service (Port 8002)
```
Responsibilities:
- Asset inventory management
- Asset discovery
- Asset classification
- Risk scoring
- Asset relationships
```

#### Vulnerability Service (Port 8003)
```
Responsibilities:
- Vulnerability tracking
- CVE management
- CVSS scoring
- Remediation tracking
- Vulnerability lifecycle
```

#### Scanning Service (Port 8004)
```
Responsibilities:
- Scan orchestration
- Scanner integration
- Scan scheduling
- Results processing
- Scan history
```

#### Notification Service (Port 8005)
```
Responsibilities:
- Email notifications
- Slack/Teams integration
- SMS alerts
- WebSocket real-time updates
- Notification preferences
```

#### Analytics Service (Port 8006)
```
Responsibilities:
- Data aggregation
- Trend analysis
- Risk calculations
- Report generation
- Dashboard metrics
```

#### Reporting Service (Port 8007)
```
Responsibilities:
- PDF report generation
- Excel exports
- Scheduled reports
- Custom templates
- Report distribution
```

#### Monitoring Service (Port 8008)
```
Responsibilities:
- System health monitoring
- Performance metrics
- Alert management
- SLA tracking
- Capacity planning
```

#### Compliance Service (Port 8009)
```
Responsibilities:
- Compliance frameworks
- Policy management
- Audit logging
- Compliance scoring
- Evidence collection
```

#### Threat Intelligence Service (Port 8010)
```
Responsibilities:
- Threat feed integration
- IOC management
- Threat correlation
- Intelligence sharing
- Threat hunting
```

## 📦 Infrastructure Services

### Message Queue (RabbitMQ)
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Usage**: Asynchronous communication between services
- **Patterns**: Pub/Sub, Work Queues, RPC

### Cache (Redis)
- **Port**: 6379
- **Usage**: Session storage, response caching, rate limiting
- **Features**: Pub/Sub, TTL, Clustering

### Databases

#### PostgreSQL (User, Asset, Vulnerability, Compliance)
- **Usage**: Structured data storage
- **Features**: ACID compliance, JSON support, Full-text search

#### MongoDB (Threat Intelligence)
- **Port**: 27017
- **Usage**: Document storage for threat data
- **Features**: Flexible schema, Aggregation pipeline

#### ClickHouse (Analytics)
- **Ports**: 8123 (HTTP), 9000 (Native)
- **Usage**: Time-series data and analytics
- **Features**: Columnar storage, Fast aggregations

### Search (Elasticsearch)
- **Port**: 9200
- **Usage**: Full-text search, log aggregation
- **Features**: Real-time search, Analytics

## 📊 Monitoring & Observability

### Metrics (Prometheus + Grafana)
- **Prometheus Port**: 9090
- **Grafana Port**: 3000
- **Metrics Collected**:
  - Request rates
  - Response times
  - Error rates
  - Resource utilization
  - Business metrics

### Logging (ELK Stack)
- **Elasticsearch**: 9200
- **Logstash**: 5000
- **Kibana**: 5601
- **Log Types**:
  - Application logs
  - Access logs
  - Error logs
  - Audit logs

### Tracing (Jaeger)
- **Port**: 16686 (UI), 6831 (Agent)
- **Features**:
  - Distributed tracing
  - Request flow visualization
  - Performance bottleneck identification
  - Service dependency mapping

## 🚀 Deployment

### Docker Compose Deployment

```bash
# Start all services
cd microservices
docker-compose -f docker-compose.microservices.yml up -d

# Scale specific services
docker-compose -f docker-compose.microservices.yml up -d --scale asset-service=3

# View logs
docker-compose -f docker-compose.microservices.yml logs -f gateway

# Stop all services
docker-compose -f docker-compose.microservices.yml down
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: soc-platform/user-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: SERVICE_NAME
          value: "user-service"
        - name: CONSUL_HOST
          value: "consul-service"
```

## 🔄 Communication Patterns

### Synchronous Communication (HTTP/REST)
```python
# Service-to-service call
response = await self.call_service(
    service_name="user-service",
    method="GET",
    path="/api/users/123"
)
```

### Asynchronous Communication (Message Queue)
```python
# Publish event
await self.publish_event("user.created", {
    "user_id": 123,
    "username": "john_doe"
})

# Subscribe to events
await self.mq.subscribe("user.created", handle_user_created)
```

### Real-time Communication (WebSocket)
```javascript
// Client-side subscription
const ws = new WebSocket('ws://localhost:8080/ws/notifications')
ws.onmessage = (event) => {
    const notification = JSON.parse(event.data)
    console.log('New notification:', notification)
}
```

## 🛡️ Security

### Service-to-Service Authentication
- **Method**: mTLS (Mutual TLS)
- **Implementation**: Service mesh (Istio/Linkerd)
- **Certificate Management**: Consul Connect

### API Gateway Security
- **Authentication**: JWT tokens
- **Authorization**: Role-based access control
- **Rate Limiting**: Redis-based per-client limits
- **DDoS Protection**: Traefik middleware

### Data Security
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: TLS 1.3
- **Secrets Management**: HashiCorp Vault integration

## 📈 Scalability Strategies

### Horizontal Scaling
```bash
# Scale user service to 5 instances
docker-compose up -d --scale user-service=5
```

### Auto-scaling (Kubernetes)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Scaling
- **Read Replicas**: PostgreSQL streaming replication
- **Sharding**: ClickHouse distributed tables
- **Caching**: Redis cache layer

## 🔧 Development

### Creating a New Microservice

1. **Extend Base Service**:
```python
from base_service import BaseMicroservice

class MyService(BaseMicroservice):
    async def setup_routes(self):
        # Add service-specific routes
        pass

    async def initialize(self):
        # Initialize service
        pass

    async def cleanup(self):
        # Cleanup resources
        pass

    async def check_health(self):
        # Health check logic
        return {"status": "healthy"}
```

2. **Register with Consul**:
```python
await self.registry.register()
```

3. **Add to API Gateway**:
```python
self.routes["/api/myservice"] = "my-service"
```

### Local Development

```bash
# Run services locally
cd microservices/services/user
python user_service.py

# Use environment variables
export SERVICE_PORT=8001
export DATABASE_URL=postgresql://localhost/users
export CONSUL_HOST=localhost
```

## 📊 Monitoring Dashboards

### Service Health Dashboard
- Service status (up/down)
- Response times (p50, p95, p99)
- Error rates
- Request rates
- Active connections

### Business Metrics Dashboard
- User registrations
- Assets discovered
- Vulnerabilities found
- Scans completed
- Reports generated

### Infrastructure Dashboard
- CPU usage
- Memory usage
- Disk I/O
- Network traffic
- Container metrics

## 🚨 Fault Tolerance

### Circuit Breaker Pattern
```python
# Implemented in API Gateway
if failures >= threshold:
    state = "OPEN"  # Stop sending requests
    # After timeout, transition to HALF_OPEN
```

### Retry Logic
```python
@retry(max_attempts=3, backoff=exponential)
async def call_service():
    # Service call with automatic retry
```

### Bulkhead Pattern
- Isolate critical resources
- Separate connection pools
- Thread pool isolation

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 📝 Configuration Management

### Environment-based Configuration
```python
class ServiceConfig:
    service_name = os.getenv("SERVICE_NAME")
    database_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL")
```

### Consul Key/Value Store
```python
# Get configuration from Consul
config = consul_client.kv.get("config/user-service")
```

### Configuration Hot Reload
```python
# Watch for configuration changes
@consul_client.watch("config/user-service")
def update_config(new_config):
    self.config = new_config
```

## 🎯 Best Practices

1. **Single Responsibility**: Each service handles one business capability
2. **Database per Service**: Services don't share databases
3. **API Versioning**: Support multiple API versions
4. **Idempotent Operations**: Handle duplicate requests gracefully
5. **Event Sourcing**: Store events for audit and replay
6. **CQRS**: Separate read and write models
7. **Saga Pattern**: Manage distributed transactions
8. **Service Mesh**: Use Istio/Linkerd for advanced features

## 📋 Migration Strategy

### Phase 1: Strangler Pattern
- Run microservices alongside monolith
- Route specific endpoints to microservices
- Gradual migration of functionality

### Phase 2: Database Decomposition
- Extract service-specific databases
- Implement data synchronization
- Handle distributed transactions

### Phase 3: Complete Migration
- Retire monolithic application
- Full microservices deployment
- Optimize inter-service communication

## 🎉 Benefits Achieved

- ✅ **Independent Deployment**: Services can be deployed independently
- ✅ **Technology Diversity**: Use best technology for each service
- ✅ **Fault Isolation**: Failures don't cascade
- ✅ **Scalability**: Scale services independently
- ✅ **Team Autonomy**: Teams own their services
- ✅ **Faster Development**: Parallel development of services
- ✅ **Better Monitoring**: Service-level metrics and tracing
- ✅ **Improved Resilience**: Circuit breakers and retries
- ✅ **Cost Optimization**: Scale only what's needed

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/soc-platform/microservices

# Start infrastructure
docker-compose -f docker-compose.microservices.yml up -d consul redis rabbitmq

# Start services
docker-compose -f docker-compose.microservices.yml up -d

# Access services
- API Gateway: http://localhost:8080
- Consul UI: http://localhost:8500
- RabbitMQ UI: http://localhost:15672
- Grafana: http://localhost:3000
- Kibana: http://localhost:5601
- Jaeger: http://localhost:16686

# Test API Gateway
curl http://localhost:8080/health
```

The microservices architecture provides a robust, scalable foundation for the SOC platform's continued growth and evolution!