#!/bin/bash

# SOC Platform Deployment Script
# This script automates the deployment of the SOC Platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

# Default values
ENVIRONMENT=${ENVIRONMENT:-development}
BUILD_FRONTEND=${BUILD_FRONTEND:-false}
BUILD_BACKEND=${BUILD_BACKEND:-false}
RUN_TESTS=${RUN_TESTS:-false}
PUSH_IMAGES=${PUSH_IMAGES:-false}
DEPLOY_TARGET=${DEPLOY_TARGET:-local}

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
SOC Platform Deployment Script

USAGE:
    $0 [OPTIONS] COMMAND

COMMANDS:
    build       Build Docker images
    deploy      Deploy the application
    start       Start the services
    stop        Stop the services
    restart     Restart the services
    logs        Show service logs
    status      Show service status
    clean       Clean up resources
    test        Run tests

OPTIONS:
    -e, --env ENVIRONMENT       Set environment (development|staging|production)
    -t, --target TARGET         Set deployment target (local|docker|k8s)
    --frontend-only             Build frontend only
    --backend-only              Build backend only
    --skip-tests               Skip running tests
    --push                     Push images to registry
    --help                     Show this help message

EXAMPLES:
    $0 build                   Build all images
    $0 --env staging deploy    Deploy to staging environment
    $0 --target k8s deploy     Deploy to Kubernetes
    $0 logs backend            Show backend service logs
    $0 clean                   Clean up all resources

EOF
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi

    # Check Docker Compose (both old and new syntax)
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("docker-compose")
    fi

    # Check Node.js (for frontend builds)
    if [[ "$BUILD_FRONTEND" == "true" ]] && ! command -v node &> /dev/null; then
        missing_deps+=("node")
    fi

    # Check Python (for backend)
    if [[ "$BUILD_BACKEND" == "true" ]] && ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again."
        exit 1
    fi

    log_success "All dependencies are installed"
}

load_environment() {
    log_info "Loading environment configuration..."

    # Load main .env file
    if [[ -f "$ENV_FILE" ]]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
        log_success "Loaded main environment file"
    else
        log_warning "Main .env file not found, using defaults"
    fi

    # Load environment-specific file
    local env_specific_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    if [[ -f "$env_specific_file" ]]; then
        export $(grep -v '^#' "$env_specific_file" | xargs)
        log_success "Loaded $ENVIRONMENT environment file"
    else
        log_warning "$ENVIRONMENT environment file not found"
    fi

    # Set deployment-specific variables
    export COMPOSE_PROJECT_NAME="soc-platform-$ENVIRONMENT"
    export COMPOSE_FILE="$DOCKER_COMPOSE_FILE"

    if [[ "$ENVIRONMENT" == "production" ]]; then
        export COMPOSE_FILE="$DOCKER_COMPOSE_FILE:$PROJECT_ROOT/docker-compose.prod.yml"
    fi

    # Define docker compose command (support both old and new syntax)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"
    fi
}

build_frontend() {
    if [[ "$BUILD_FRONTEND" != "true" ]]; then
        return 0
    fi

    log_info "Skipping local frontend build (will be built in Docker)..."
    log_success "Frontend build step completed"
}

build_backend() {
    if [[ "$BUILD_BACKEND" != "true" ]]; then
        return 0
    fi

    log_info "Skipping local backend build (will be built in Docker)..."
    log_success "Backend preparation completed"
}

build_docker_images() {
    log_info "Building Docker images..."

    cd "$PROJECT_ROOT"

    local build_args=(
        --build-arg ENVIRONMENT="$ENVIRONMENT"
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        --build-arg VERSION="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    )

    if [[ "$BUILD_FRONTEND" == "true" ]]; then
        log_info "Building frontend image..."
        docker build "${build_args[@]}" -t soc-platform-frontend:$ENVIRONMENT -f frontend/Dockerfile ./frontend
    fi

    if [[ "$BUILD_BACKEND" == "true" ]]; then
        log_info "Building backend image..."
        docker build "${build_args[@]}" -t soc-platform-backend:$ENVIRONMENT -f backend/Dockerfile ./backend
    fi

    log_success "Docker images built successfully"
}

push_docker_images() {
    if [[ "$PUSH_IMAGES" != "true" ]]; then
        return 0
    fi

    log_info "Pushing Docker images..."

    # This would be configured based on your registry
    local registry=${DOCKER_REGISTRY:-"localhost:5000"}

    if [[ "$BUILD_FRONTEND" == "true" ]]; then
        docker tag soc-platform-frontend:$ENVIRONMENT "$registry/soc-platform-frontend:$ENVIRONMENT"
        docker push "$registry/soc-platform-frontend:$ENVIRONMENT"
    fi

    if [[ "$BUILD_BACKEND" == "true" ]]; then
        docker tag soc-platform-backend:$ENVIRONMENT "$registry/soc-platform-backend:$ENVIRONMENT"
        docker push "$registry/soc-platform-backend:$ENVIRONMENT"
    fi

    log_success "Docker images pushed successfully"
}

deploy_local() {
    log_info "Deploying to local environment..."

    cd "$PROJECT_ROOT"

    # Stop existing services
    $DOCKER_COMPOSE_CMD down --remove-orphans

    # Start services
    $DOCKER_COMPOSE_CMD up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30

    # Check service health
    check_service_health

    log_success "Local deployment completed"
}

deploy_docker() {
    log_info "Deploying with Docker Compose..."

    cd "$PROJECT_ROOT"

    # Update services
    $DOCKER_COMPOSE_CMD up -d --remove-orphans

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30

    # Check service health
    check_service_health

    log_success "Docker deployment completed"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    # This would be implemented based on your K8s setup
    log_warning "Kubernetes deployment not implemented yet"

    # Example implementation:
    # kubectl apply -f k8s/namespace.yaml
    # kubectl apply -f k8s/configmap.yaml
    # kubectl apply -f k8s/deployment.yaml
    # kubectl apply -f k8s/service.yaml
    # kubectl apply -f k8s/ingress.yaml
}

check_service_health() {
    log_info "Checking service health..."

    local services=("frontend" "backend" "mongodb" "redis")
    local failed_services=()

    for service in "${services[@]}"; do
        if $DOCKER_COMPOSE_CMD ps | grep -q "${service}.*Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            failed_services+=("$service")
        fi
    done

    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Failed services: ${failed_services[*]}"
        return 1
    fi

    # Test API endpoint
    local api_url="${API_BASE_URL:-http://localhost:8000}"
    if curl -f -s "$api_url/health" > /dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
}

show_logs() {
    local service=${1:-}

    cd "$PROJECT_ROOT"

    if [[ -n "$service" ]]; then
        $DOCKER_COMPOSE_CMD logs -f "$service"
    else
        $DOCKER_COMPOSE_CMD logs -f
    fi
}

show_status() {
    cd "$PROJECT_ROOT"

    log_info "Service status:"
    $DOCKER_COMPOSE_CMD ps

    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

cleanup() {
    log_info "Cleaning up resources..."

    cd "$PROJECT_ROOT"

    # Stop and remove containers
    $DOCKER_COMPOSE_CMD down --remove-orphans

    # Remove unused images
    docker image prune -f

    # Remove unused volumes (be careful with this in production)
    if [[ "$ENVIRONMENT" != "production" ]]; then
        docker volume prune -f
    fi

    log_success "Cleanup completed"
}

run_tests() {
    log_info "Running all tests..."

    # Frontend tests
    if [[ -d "$PROJECT_ROOT/frontend" ]]; then
        log_info "Running frontend tests..."
        cd "$PROJECT_ROOT/frontend"
        npm run test:unit
        npm run test:e2e
    fi

    # Backend tests
    if [[ -d "$PROJECT_ROOT/backend" ]]; then
        log_info "Running backend tests..."
        cd "$PROJECT_ROOT/backend"
        python -m pytest tests/ -v --cov=app --cov-report=html
    fi

    log_success "All tests completed"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--target)
            DEPLOY_TARGET="$2"
            shift 2
            ;;
        --frontend-only)
            BUILD_FRONTEND=true
            BUILD_BACKEND=false
            shift
            ;;
        --backend-only)
            BUILD_FRONTEND=false
            BUILD_BACKEND=true
            shift
            ;;
        --skip-tests)
            RUN_TESTS=false
            shift
            ;;
        --push)
            PUSH_IMAGES=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            COMMAND="$1"
            shift
            break
            ;;
    esac
done

# Main execution
log_info "SOC Platform Deployment Script"
log_info "Environment: $ENVIRONMENT"
log_info "Deploy Target: $DEPLOY_TARGET"

# Check dependencies
check_dependencies

# Load environment
load_environment

# Execute command
case "${COMMAND:-deploy}" in
    build)
        build_frontend
        build_backend
        build_docker_images
        push_docker_images
        ;;
    deploy)
        build_frontend
        build_backend
        build_docker_images
        push_docker_images
        case "$DEPLOY_TARGET" in
            local)
                deploy_local
                ;;
            docker)
                deploy_docker
                ;;
            k8s)
                deploy_kubernetes
                ;;
            *)
                log_error "Unknown deploy target: $DEPLOY_TARGET"
                exit 1
                ;;
        esac
        ;;
    start)
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE_CMD up -d
        check_service_health
        ;;
    stop)
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE_CMD down
        ;;
    restart)
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE_CMD restart
        check_service_health
        ;;
    logs)
        show_logs "$@"
        ;;
    status)
        show_status
        ;;
    clean)
        cleanup
        ;;
    test)
        run_tests
        ;;
    *)
        log_error "Unknown command: ${COMMAND}"
        show_help
        exit 1
        ;;
esac

log_success "Deployment script completed successfully"