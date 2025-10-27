#!/bin/bash

# SOC Platform Setup Script
# This script sets up the complete SOC platform environment

set -e  # Exit on any error

echo "=========================================="
echo "SOC Platform Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check Python 3.8+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION is installed"
        else
            print_error "Python 3.8+ is required, but $PYTHON_VERSION is installed"
            exit 1
        fi
    else
        print_error "Python 3.8+ is required but not installed"
        exit 1
    fi

    # Check Node.js 16+
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2)
        MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1)
        if [ "$MAJOR_VERSION" -ge 16 ]; then
            print_success "Node.js $NODE_VERSION is installed"
        else
            print_error "Node.js 16+ is required, but $NODE_VERSION is installed"
            exit 1
        fi
    else
        print_error "Node.js 16+ is required but not installed"
        exit 1
    fi

    # Check available ports
    check_port() {
        if ss -tuln | grep -q ":$1 "; then
            print_warning "Port $1 is already in use"
            return 1
        fi
        return 0
    }

    print_status "Checking required ports..."
    PORTS_IN_USE=()

    for port in 3000 8000 8001 27017 6379; do
        if ! check_port $port; then
            PORTS_IN_USE+=($port)
        fi
    done

    if [ ${#PORTS_IN_USE[@]} -gt 0 ]; then
        print_error "The following required ports are in use: ${PORTS_IN_USE[*]}"
        print_error "Please stop services using these ports or modify the configuration"
        exit 1
    fi

    print_success "All system requirements met"
}

# Create directory structure
create_directories() {
    print_status "Creating directory structure..."

    mkdir -p logs
    mkdir -p data/mongodb
    mkdir -p data/redis
    mkdir -p uploads
    mkdir -p reports
    mkdir -p temp
    mkdir -p backups

    # Set permissions
    chmod 755 logs data uploads reports temp backups
    chmod 700 data/mongodb data/redis

    print_success "Directory structure created"
}

# Generate environment files
generate_env_files() {
    print_status "Generating environment configuration files..."

    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    MONGODB_ROOT_PASSWORD=$(openssl rand -base64 16)
    REDIS_PASSWORD=$(openssl rand -base64 16)

    # Backend .env file
    cat > backend/.env << EOF
# Application
APP_NAME=SOC Platform
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
MONGODB_URL=mongodb://admin:$MONGODB_ROOT_PASSWORD@mongodb:27017/soc_platform?authSource=admin
MONGODB_DB_NAME=soc_platform

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:$REDIS_PASSWORD@redis:6379/1
CELERY_RESULT_BACKEND=redis://:$REDIS_PASSWORD@redis:6379/2

# Email (configure as needed)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_TLS=true

# External APIs
FOFA_EMAIL=
FOFA_KEY=

# Security
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]

# File paths
UPLOAD_DIR=/app/uploads
REPORTS_DIR=/app/reports
TEMP_DIR=/app/temp
LOGS_DIR=/app/logs

# Scanning
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT=3600
NMAP_PATH=/usr/bin/nmap
NUCLEI_PATH=/usr/bin/nuclei

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
EOF

    # Frontend .env file
    cat > frontend/.env << EOF
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Application
VITE_APP_NAME=SOC Platform
VITE_APP_VERSION=1.0.0

# Features
VITE_ENABLE_DEBUG=false
VITE_ENABLE_ANALYTICS=false

# Theme
VITE_DEFAULT_THEME=light
EOF

    # Docker environment file
    cat > .env << EOF
# Docker Configuration
COMPOSE_PROJECT_NAME=soc-platform

# Database
MONGODB_ROOT_PASSWORD=$MONGODB_ROOT_PASSWORD
MONGODB_DATABASE=soc_platform

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD

# Ports
FRONTEND_PORT=3000
BACKEND_PORT=8000
WORKER_PORT=8001
MONGODB_PORT=27017
REDIS_PORT=6379

# Volumes
DATA_DIR=./data
LOGS_DIR=./logs
UPLOADS_DIR=./uploads
REPORTS_DIR=./reports
EOF

    print_success "Environment files generated"
    print_warning "Please review and update the configuration files as needed"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."

    cd backend

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    pip install -r requirements.txt

    cd ..
    print_success "Python dependencies installed"
}

# Install Node.js dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."

    cd frontend

    # Install dependencies
    npm install

    cd ..
    print_success "Node.js dependencies installed"
}

# Build Docker images
build_docker_images() {
    print_status "Building Docker images..."

    # Build images
    docker-compose build --no-cache

    print_success "Docker images built successfully"
}

# Start services
start_services() {
    print_status "Starting services..."

    # Start infrastructure services first
    docker-compose up -d mongodb redis

    # Wait for MongoDB to be ready
    print_status "Waiting for MongoDB to be ready..."
    while ! docker-compose exec -T mongodb mongosh --eval "db.runCommand('ismaster')" --quiet; do
        sleep 2
    done

    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    while ! docker-compose exec -T redis redis-cli ping; do
        sleep 2
    done

    # Start application services
    docker-compose up -d

    print_success "Services started successfully"
}

# Initialize database
initialize_database() {
    print_status "Initializing database with sample data..."

    # Wait a bit for services to stabilize
    sleep 10

    # Run database initialization script
    if python3 scripts/init_db.py; then
        print_success "Database initialized successfully"
    else
        print_error "Database initialization failed"
        return 1
    fi
}

# Run health checks
health_check() {
    print_status "Running health checks..."

    # Check backend health
    print_status "Checking backend service..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend service is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend service health check failed"
            return 1
        fi
        sleep 2
    done

    # Check frontend
    print_status "Checking frontend service..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend service is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Frontend service health check failed"
            return 1
        fi
        sleep 2
    done

    print_success "All health checks passed"
}

# Show final information
show_final_info() {
    echo ""
    echo "=========================================="
    echo "SOC Platform Setup Complete!"
    echo "=========================================="
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "Default Login Credentials:"
    echo "👤 Admin: admin / admin123"
    echo "🔍 Security Analyst: security_analyst / analyst123"
    echo "⚙️  Operator: operator / operator123"
    echo "👁️  Viewer: viewer / viewer123"
    echo ""
    echo "Useful Commands:"
    echo "• View logs: docker-compose logs -f"
    echo "• Stop services: docker-compose down"
    echo "• Restart services: docker-compose restart"
    echo "• View status: docker-compose ps"
    echo ""
    echo "Configuration files generated:"
    echo "• backend/.env - Backend configuration"
    echo "• frontend/.env - Frontend configuration"
    echo "• .env - Docker environment"
    echo ""
    echo "Please change default passwords before production use!"
    echo "=========================================="
}

# Cleanup on error
cleanup_on_error() {
    print_error "Setup failed. Cleaning up..."
    docker-compose down -v 2>/dev/null || true
}

# Main setup function
main() {
    # Set error trap
    trap cleanup_on_error ERR

    print_status "Starting SOC Platform setup..."

    check_root
    check_requirements
    create_directories
    generate_env_files

    # Ask user if they want to install dependencies
    read -p "Do you want to install Python and Node.js dependencies locally? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_python_deps
        install_node_deps
    fi

    build_docker_images
    start_services

    # Ask user if they want to initialize database
    read -p "Do you want to initialize the database with sample data? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        initialize_database
    fi

    health_check
    show_final_info
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi