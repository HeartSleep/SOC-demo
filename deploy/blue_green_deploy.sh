#!/bin/bash

# Blue-Green Deployment Script
# Zero-downtime deployment with automatic rollback

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-staging}
DOCKER_REGISTRY="ghcr.io"
IMAGE_NAME="soc-platform"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10
ROLLBACK_ON_FAILURE=true

# Load balancer configuration
NGINX_CONFIG="/etc/nginx/sites-available/soc-platform"
BLUE_PORT=8001
GREEN_PORT=8002
FRONTEND_BLUE_PORT=3001
FRONTEND_GREEN_PORT=3002

# Current active environment
CURRENT_ENV_FILE="/var/lib/soc-platform/current-env"
DEPLOYMENT_LOG="/var/log/soc-platform/deployment.log"

# Functions
log() {
    echo -e "${2}$1${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $DEPLOYMENT_LOG
}

get_current_env() {
    if [ -f "$CURRENT_ENV_FILE" ]; then
        cat $CURRENT_ENV_FILE
    else
        echo "blue"
    fi
}

get_target_env() {
    current=$(get_current_env)
    if [ "$current" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

get_backend_port() {
    if [ "$1" = "blue" ]; then
        echo $BLUE_PORT
    else
        echo $GREEN_PORT
    fi
}

get_frontend_port() {
    if [ "$1" = "blue" ]; then
        echo $FRONTEND_BLUE_PORT
    else
        echo $FRONTEND_GREEN_PORT
    fi
}

health_check() {
    local port=$1
    local service=$2
    local retries=$HEALTH_CHECK_RETRIES

    log "Performing health check for $service on port $port..." "$YELLOW"

    while [ $retries -gt 0 ]; do
        if curl -f "http://localhost:$port/health" > /dev/null 2>&1; then
            log "✅ Health check passed for $service" "$GREEN"
            return 0
        fi

        retries=$((retries - 1))
        log "Health check failed, retries remaining: $retries" "$YELLOW"
        sleep $HEALTH_CHECK_INTERVAL
    done

    log "❌ Health check failed for $service after $HEALTH_CHECK_RETRIES attempts" "$RED"
    return 1
}

run_smoke_tests() {
    local backend_port=$1
    local frontend_port=$2

    log "Running smoke tests..." "$YELLOW"

    # Test backend API
    if ! curl -f "http://localhost:$backend_port/api/v1/users/" > /dev/null 2>&1; then
        log "❌ Backend smoke test failed" "$RED"
        return 1
    fi

    # Test frontend
    if ! curl -f "http://localhost:$frontend_port" > /dev/null 2>&1; then
        log "❌ Frontend smoke test failed" "$RED"
        return 1
    fi

    # Test WebSocket
    if ! python3 -c "
import asyncio
import websockets
import json

async def test_ws():
    try:
        async with websockets.connect(f'ws://localhost:$backend_port/api/v1/ws/test') as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            return True
    except:
        return False

result = asyncio.run(test_ws())
exit(0 if result else 1)
    " 2>/dev/null; then
        log "⚠️ WebSocket test failed (non-critical)" "$YELLOW"
    fi

    log "✅ Smoke tests passed" "$GREEN"
    return 0
}

deploy_environment() {
    local env=$1
    local backend_port=$(get_backend_port $env)
    local frontend_port=$(get_frontend_port $env)

    log "Deploying to $env environment (Backend: $backend_port, Frontend: $frontend_port)..." "$BLUE"

    # Create docker-compose file for the environment
    cat > "docker-compose.$env.yml" << EOF
version: '3.8'

services:
  backend-$env:
    image: $DOCKER_REGISTRY/$IMAGE_NAME-backend:$GITHUB_SHA
    container_name: soc-backend-$env
    environment:
      - ENVIRONMENT=$ENVIRONMENT
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=\${REDIS_URL}
      - SECRET_KEY=\${SECRET_KEY}
      - JWT_SECRET_KEY=\${JWT_SECRET_KEY}
      - CORS_ORIGINS=http://localhost:$frontend_port
    ports:
      - "$backend_port:8000"
    networks:
      - soc-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend-$env:
    image: $DOCKER_REGISTRY/$IMAGE_NAME-frontend:$GITHUB_SHA
    container_name: soc-frontend-$env
    environment:
      - VITE_API_URL=http://localhost:$backend_port
      - VITE_WS_URL=ws://localhost:$backend_port
    ports:
      - "$frontend_port:80"
    networks:
      - soc-network
    depends_on:
      - backend-$env
    restart: unless-stopped

networks:
  soc-network:
    external: true
EOF

    # Start the new environment
    log "Starting $env environment containers..." "$BLUE"
    docker-compose -f "docker-compose.$env.yml" up -d

    # Wait for services to be ready
    if ! health_check $backend_port "backend-$env"; then
        log "Backend health check failed for $env environment" "$RED"
        return 1
    fi

    if ! health_check $frontend_port "frontend-$env"; then
        log "Frontend health check failed for $env environment" "$RED"
        return 1
    fi

    # Run smoke tests
    if ! run_smoke_tests $backend_port $frontend_port; then
        log "Smoke tests failed for $env environment" "$RED"
        return 1
    fi

    log "✅ $env environment deployed successfully" "$GREEN"
    return 0
}

switch_traffic() {
    local target_env=$1
    local backend_port=$(get_backend_port $target_env)
    local frontend_port=$(get_frontend_port $target_env)

    log "Switching traffic to $target_env environment..." "$BLUE"

    # Update nginx configuration
    cat > /tmp/nginx-soc-platform.conf << EOF
upstream soc_backend {
    server localhost:$backend_port;
}

upstream soc_frontend {
    server localhost:$frontend_port;
}

server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Frontend
    location / {
        proxy_pass http://soc_frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://soc_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket
    location /api/v1/ws {
        proxy_pass http://soc_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

    # Test nginx configuration
    if nginx -t -c /tmp/nginx-soc-platform.conf 2>/dev/null; then
        sudo mv /tmp/nginx-soc-platform.conf $NGINX_CONFIG
        sudo nginx -s reload
        log "✅ Traffic switched to $target_env environment" "$GREEN"

        # Update current environment
        echo $target_env > $CURRENT_ENV_FILE
        return 0
    else
        log "❌ Nginx configuration test failed" "$RED"
        return 1
    fi
}

cleanup_old_environment() {
    local env=$1

    log "Cleaning up $env environment..." "$YELLOW"

    # Keep the old environment running for 5 minutes (for quick rollback)
    sleep 300

    # Stop and remove old containers
    docker-compose -f "docker-compose.$env.yml" down

    # Clean up compose file
    rm -f "docker-compose.$env.yml"

    log "✅ $env environment cleaned up" "$GREEN"
}

rollback() {
    local current_env=$1
    local previous_env=$2

    log "🔄 Rolling back to $previous_env environment..." "$YELLOW"

    # Switch traffic back
    if switch_traffic $previous_env; then
        log "✅ Rolled back to $previous_env environment" "$GREEN"

        # Stop failed deployment
        docker-compose -f "docker-compose.$current_env.yml" down
        rm -f "docker-compose.$current_env.yml"

        return 0
    else
        log "❌ Rollback failed! Manual intervention required!" "$RED"
        return 1
    fi
}

# Main deployment process
main() {
    log "========================================" "$BLUE"
    log "   Blue-Green Deployment for $ENVIRONMENT" "$BLUE"
    log "========================================" "$BLUE"

    # Get current and target environments
    CURRENT_ENV=$(get_current_env)
    TARGET_ENV=$(get_target_env)

    log "Current environment: $CURRENT_ENV" "$BLUE"
    log "Target environment: $TARGET_ENV" "$BLUE"

    # Create necessary directories
    mkdir -p /var/lib/soc-platform
    mkdir -p /var/log/soc-platform

    # Create docker network if not exists
    docker network create soc-network 2>/dev/null || true

    # Deploy to target environment
    if deploy_environment $TARGET_ENV; then
        # Run integration tests
        log "Running integration tests..." "$YELLOW"
        if python3 /opt/soc-platform/test_frontend_backend_integration.py \
           --backend-port $(get_backend_port $TARGET_ENV) \
           --frontend-port $(get_frontend_port $TARGET_ENV); then

            log "✅ Integration tests passed" "$GREEN"

            # Switch traffic to new environment
            if switch_traffic $TARGET_ENV; then
                # Monitor for 2 minutes
                log "Monitoring new deployment for 2 minutes..." "$YELLOW"
                sleep 120

                # Check if still healthy
                if health_check $(get_backend_port $TARGET_ENV) "backend-$TARGET_ENV"; then
                    log "✅ Deployment successful!" "$GREEN"

                    # Schedule cleanup of old environment
                    (cleanup_old_environment $CURRENT_ENV &)

                    # Send notification
                    if [ -n "$SLACK_WEBHOOK" ]; then
                        curl -X POST $SLACK_WEBHOOK \
                            -H 'Content-Type: application/json' \
                            -d "{\"text\":\"✅ Blue-Green deployment to $ENVIRONMENT successful! Switched from $CURRENT_ENV to $TARGET_ENV.\"}"
                    fi

                    exit 0
                else
                    log "❌ Health degradation detected after deployment" "$RED"
                    if [ "$ROLLBACK_ON_FAILURE" = true ]; then
                        rollback $TARGET_ENV $CURRENT_ENV
                    fi
                    exit 1
                fi
            else
                log "❌ Failed to switch traffic" "$RED"
                if [ "$ROLLBACK_ON_FAILURE" = true ]; then
                    rollback $TARGET_ENV $CURRENT_ENV
                fi
                exit 1
            fi
        else
            log "❌ Integration tests failed" "$RED"
            docker-compose -f "docker-compose.$TARGET_ENV.yml" down
            exit 1
        fi
    else
        log "❌ Failed to deploy $TARGET_ENV environment" "$RED"
        exit 1
    fi
}

# Handle interrupts
trap 'log "Deployment interrupted!" "$RED"; exit 1' INT TERM

# Run main deployment
main