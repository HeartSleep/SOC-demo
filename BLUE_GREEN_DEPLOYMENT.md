# 🚀 Blue-Green Deployment System

## Overview

The SOC Platform now features a comprehensive **Zero-Downtime Blue-Green Deployment** system that ensures seamless updates with automatic rollback capabilities.

## 🎯 Key Features

### Zero-Downtime Deployments
- **Parallel Environments**: Blue and Green environments run simultaneously
- **Instant Traffic Switching**: Sub-second switchover between environments
- **Health-Aware Routing**: Automatic health checks before switching traffic
- **Gradual Rollout Support**: Optional canary and gradual deployment strategies

### Automatic Rollback
- **Health Monitoring**: Continuous monitoring during and after deployment
- **Performance Thresholds**: Automatic rollback if response time exceeds limits
- **Error Rate Tracking**: Rollback triggered on error rate spikes
- **Test Failures**: Automatic rollback on integration test failures

### Comprehensive Testing
- **Pre-deployment Validation**: Database migrations and dependency checks
- **Integration Testing**: Full API and WebSocket testing
- **Performance Testing**: Response time and throughput validation
- **Post-deployment Verification**: Continuous monitoring for 2+ minutes

## 📁 Components

### 1. Shell Scripts (`deploy/`)

#### `blue_green_deploy.sh`
Main deployment script with complete lifecycle management:
```bash
./deploy/blue_green_deploy.sh production
```

Features:
- Environment detection (blue/green)
- Docker container management
- Nginx configuration updates
- Health check orchestration
- Automatic cleanup of old environments

#### `rollback.sh`
Emergency rollback capabilities:
```bash
# Interactive rollback
./deploy/rollback.sh

# Emergency immediate rollback
./deploy/rollback.sh EMERGENCY
```

Options:
1. Quick rollback (switch traffic)
2. Full rollback (redeploy previous version)
3. Database-only rollback
4. Restore from backup
5. Emergency stop all services

### 2. Python Orchestrator

#### `blue_green_orchestrator.py`
Advanced deployment orchestration with monitoring:

```bash
# Deploy with specific tag
python blue_green_orchestrator.py --tag v1.2.3

# Deploy with custom config
python blue_green_orchestrator.py --tag v1.2.3 --config production.yaml

# Skip tests (not recommended)
python blue_green_orchestrator.py --tag v1.2.3 --skip-tests
```

Features:
- Async deployment pipeline
- Parallel test execution
- Real-time metrics collection
- WebSocket testing
- Automated notifications
- Deployment reports

### 3. Configuration

#### `deployment-config.yaml`
Comprehensive deployment configuration:

```yaml
environments:
  blue:
    backend_port: 8001
    frontend_port: 3001
  green:
    backend_port: 8002
    frontend_port: 3002

monitoring:
  error_threshold: 0.01  # 1% error rate
  response_time_threshold: 500  # ms
  monitoring_duration: 120  # seconds

rollback:
  automatic: true
  conditions:
    error_rate_exceeded: true
    health_check_failed: true
    test_failed: true
```

## 🔄 Deployment Flow

```mermaid
graph TD
    A[Start Deployment] --> B[Deploy to Inactive Environment]
    B --> C[Health Checks]
    C --> D{Healthy?}
    D -->|No| E[Rollback]
    D -->|Yes| F[Run Integration Tests]
    F --> G{Tests Pass?}
    G -->|No| E
    G -->|Yes| H[Switch Traffic]
    H --> I[Monitor for 2 Minutes]
    I --> J{Metrics OK?}
    J -->|No| E
    J -->|Yes| K[Cleanup Old Environment]
    K --> L[Deployment Complete]
    E --> M[Restore Previous]
    M --> N[Alert Team]
```

## 🎮 Usage Examples

### Basic Deployment
```bash
# Using shell script
./deploy/blue_green_deploy.sh staging

# Using Python orchestrator
python blue_green_orchestrator.py --tag latest
```

### Production Deployment with CI/CD
```yaml
# In .github/workflows/ci-cd-pipeline.yml
- name: Blue-Green Deployment
  run: |
    ./deploy/blue_green_deploy.sh production
  env:
    GITHUB_SHA: ${{ github.sha }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

### Emergency Rollback
```bash
# Immediate rollback to previous environment
./deploy/rollback.sh NOW

# Interactive rollback with options
./deploy/rollback.sh
```

### Custom Deployment
```python
# Using orchestrator programmatically
import asyncio
from blue_green_orchestrator import BlueGreenOrchestrator

async def custom_deploy():
    orchestrator = BlueGreenOrchestrator("custom-config.yaml")
    status = await orchestrator.execute_deployment("v2.0.0")
    report = orchestrator.generate_report()
    print(report)

asyncio.run(custom_deploy())
```

## 📊 Monitoring & Metrics

### Health Endpoints
- **Backend Health**: `http://localhost:8001/health`
- **Frontend Health**: `http://localhost:3001/`
- **Detailed Health**: `http://localhost:8001/api/v1/monitoring/health/detailed`

### Metrics Tracked
- Deployment duration
- Success/failure rate
- Rollback frequency
- Response times (p50, p95, p99)
- Error rates
- Resource utilization

### Deployment Reports
Generated after each deployment:
```
deployment-reports/
├── deploy-1699123456.txt
├── deploy-1699127890.txt
└── deploy-1699131234.txt
```

## 🛡️ Safety Features

### Pre-deployment Checks
1. Database migration validation
2. Dependency vulnerability scanning
3. Docker image security scanning
4. Configuration validation

### During Deployment
1. Parallel environment validation
2. Progressive health checks
3. Integration test suite
4. Performance benchmarking

### Post-deployment
1. Continuous monitoring (2+ minutes)
2. Error rate tracking
3. Response time validation
4. Automatic rollback triggers

### Rollback Conditions
- Health check failures
- Test failures
- Error rate > 1%
- Response time > 500ms
- Manual trigger

## 🔧 Configuration

### Environment Variables
```bash
# Required
export DATABASE_URL="postgresql://user:pass@localhost/db"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-key"

# Optional
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export PAGERDUTY_INTEGRATION_KEY="your-key"
export GITHUB_SHA="commit-sha"
```

### Network Setup
```bash
# Create Docker network
docker network create soc-network

# Verify network
docker network ls | grep soc-network
```

### Nginx Configuration
The system automatically manages nginx configuration for traffic routing:
```nginx
upstream backend {
    server localhost:8001;  # or 8002
}

location /api {
    proxy_pass http://backend;
}
```

## 📈 Performance

### Deployment Metrics
- **Deployment Time**: ~2-3 minutes total
- **Switchover Time**: <1 second
- **Rollback Time**: <30 seconds
- **Health Check Duration**: 30-60 seconds
- **Test Execution**: 60-90 seconds

### Resource Usage
- **Blue Environment**: 768MB RAM, 750m CPU
- **Green Environment**: 768MB RAM, 750m CPU
- **During Deployment**: 2x resources (both environments)
- **After Cleanup**: 1x resources (single environment)

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Conflicts
```bash
# Check port usage
lsof -i :8001
lsof -i :8002

# Kill conflicting processes
kill -9 <PID>
```

#### 2. Health Check Failures
```bash
# Check container logs
docker logs soc-backend-blue
docker logs soc-frontend-blue

# Manual health check
curl http://localhost:8001/health
```

#### 3. Failed Rollback
```bash
# Emergency stop all
./deploy/rollback.sh EMERGENCY

# Manual restore
docker-compose -f docker-compose.blue.yml up -d
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
./deploy/blue_green_deploy.sh staging

# Verbose Python orchestrator
python blue_green_orchestrator.py --tag latest --verbose
```

## 📚 Best Practices

1. **Always Test in Staging First**
   ```bash
   ./deploy/blue_green_deploy.sh staging
   # If successful, then:
   ./deploy/blue_green_deploy.sh production
   ```

2. **Use Deployment Windows**
   - Configure in `deployment-config.yaml`
   - Avoid deployments during peak hours
   - Block deployments on holidays

3. **Monitor After Deployment**
   - Watch metrics for at least 30 minutes
   - Check error logs
   - Verify all integrations

4. **Maintain Backups**
   - Database backups before deployment
   - Docker image backups
   - Configuration backups

5. **Document Changes**
   - Update CHANGELOG.md
   - Tag releases properly
   - Document breaking changes

## 🎯 Integration with CI/CD

The blue-green deployment is fully integrated with the CI/CD pipeline:

1. **Code Push** → GitHub Actions triggered
2. **Tests Run** → Unit, integration, and contract tests
3. **Build Images** → Docker images built and pushed
4. **Security Scan** → Trivy and OWASP ZAP scanning
5. **Deploy Staging** → Blue-green deployment to staging
6. **Smoke Tests** → Automated verification
7. **Deploy Production** → Blue-green deployment to production
8. **Monitor** → Continuous monitoring and alerting

## 📋 Checklist

### Pre-deployment
- [ ] All tests passing in CI/CD
- [ ] Security scans completed
- [ ] Database migrations prepared
- [ ] Rollback plan documented
- [ ] Team notified

### Deployment
- [ ] Run deployment script
- [ ] Monitor health checks
- [ ] Verify integration tests
- [ ] Check performance metrics
- [ ] Confirm traffic switched

### Post-deployment
- [ ] Monitor for 30+ minutes
- [ ] Check error rates
- [ ] Verify all integrations
- [ ] Update documentation
- [ ] Send deployment report

## 🎉 Summary

The Blue-Green Deployment system provides:

- ✅ **Zero-downtime deployments**
- ✅ **Automatic rollback on failures**
- ✅ **Comprehensive health monitoring**
- ✅ **Integration test validation**
- ✅ **Performance threshold enforcement**
- ✅ **Multi-environment support**
- ✅ **Emergency rollback capabilities**
- ✅ **Deployment reporting**
- ✅ **CI/CD integration**
- ✅ **Production-ready configuration**

The system ensures that deployments are safe, monitored, and reversible, providing confidence in production updates while maintaining service availability.