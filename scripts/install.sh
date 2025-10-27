#!/bin/bash

# SOC Platform Installation Script
# This script will install and configure the SOC Security Platform

set -e

echo "============================================="
echo "SOC Security Platform Installation Script"
echo "============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons"
   exit 1
fi

# Variables
PROJECT_NAME="SOC"
PROJECT_DIR="$HOME/soc-platform"
DOCKER_COMPOSE_VERSION="2.20.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    else
        log_info "$1 is available"
        return 0
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Operating System: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "Operating System: macOS"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi

    # Check memory
    MEMORY=$(free -g 2>/dev/null | awk 'NR==2{printf "%.0f\n", $2}' || sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0f\n", $1/1024/1024/1024}')
    if [[ $MEMORY -lt 8 ]]; then
        log_warn "System has ${MEMORY}GB RAM. Minimum 8GB recommended."
    else
        log_info "System has ${MEMORY}GB RAM"
    fi

    # Check disk space
    DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $DISK_SPACE -lt 50 ]]; then
        log_warn "Available disk space: ${DISK_SPACE}GB. Minimum 50GB recommended."
    else
        log_info "Available disk space: ${DISK_SPACE}GB"
    fi
}

# Install Docker if not present
install_docker() {
    if ! check_command docker; then
        log_info "Installing Docker..."

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Install Docker on Linux
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            log_info "Docker installed. Please log out and back in to use Docker without sudo."
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            log_error "Please install Docker Desktop for Mac from https://docs.docker.com/docker-for-mac/install/"
            exit 1
        fi
    fi
}

# Install Docker Compose if not present
install_docker_compose() {
    if ! check_command docker-compose; then
        log_info "Installing Docker Compose..."

        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    fi
}

# Create project directory and download source
setup_project() {
    log_info "Setting up project directory..."

    if [[ -d "$PROJECT_DIR" ]]; then
        log_warn "Project directory already exists: $PROJECT_DIR"
        read -p "Remove existing directory? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            log_error "Installation cancelled"
            exit 1
        fi
    fi

    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"

    # If this script is being run from the project directory, copy files
    if [[ -f "$(dirname $0)/../docker-compose.yml" ]]; then
        cp -r $(dirname $0)/.. .
        log_info "Project files copied from local directory"
    else
        log_error "Project files not found. Please ensure you're running this script from the project directory."
        exit 1
    fi
}

# Configure environment
configure_environment() {
    log_info "Configuring environment..."

    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        log_info "Environment file created from template"

        # Generate random passwords
        MONGO_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

        # Update .env file
        sed -i "s/MONGO_ROOT_PASSWORD=.*/MONGO_ROOT_PASSWORD=$MONGO_PASSWORD/" .env
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env

        log_info "Random passwords generated and configured"
    else
        log_info "Environment file already exists"
    fi
}

# Start services
start_services() {
    log_info "Starting SOC Platform services..."

    # Pull images
    docker-compose pull

    # Build and start services
    docker-compose up -d

    log_info "Waiting for services to start..."
    sleep 30

    # Check service health
    if docker-compose ps | grep -q "Up"; then
        log_info "Services started successfully"
    else
        log_error "Some services failed to start"
        docker-compose logs
        exit 1
    fi
}

# Create admin user
create_admin_user() {
    log_info "Creating admin user..."

    echo "Please provide admin user details:"
    read -p "Username: " ADMIN_USERNAME
    read -p "Email: " ADMIN_EMAIL
    read -p "Full Name: " ADMIN_FULLNAME
    read -s -p "Password: " ADMIN_PASSWORD
    echo

    # Create admin user script
    cat > create_admin.py << EOF
import asyncio
from app.core.database import init_database
from app.api.models.user import User, UserRole, UserStatus
from app.core.security import security
from datetime import datetime

async def create_admin():
    await init_database()

    # Check if admin already exists
    existing_admin = await User.find_one(User.username == "$ADMIN_USERNAME")
    if existing_admin:
        print("Admin user already exists")
        return

    # Create admin user
    admin_user = User(
        username="$ADMIN_USERNAME",
        email="$ADMIN_EMAIL",
        full_name="$ADMIN_FULLNAME",
        hashed_password=security.get_password_hash("$ADMIN_PASSWORD"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow()
    )

    await admin_user.insert()
    print(f"Admin user '{admin_user.username}' created successfully")

if __name__ == "__main__":
    asyncio.run(create_admin())
EOF

    # Run the script inside the backend container
    docker-compose exec -T backend python create_admin.py
    rm create_admin.py

    log_info "Admin user created successfully"
}

# Display final information
show_completion_info() {
    log_info "============================================="
    log_info "SOC Platform Installation Complete!"
    log_info "============================================="
    echo
    log_info "Services Status:"
    docker-compose ps
    echo
    log_info "Access URLs:"
    log_info "  Web Interface: http://localhost"
    log_info "  API Documentation: http://localhost:8000/docs"
    echo
    log_info "Default Admin Credentials:"
    log_info "  Username: $ADMIN_USERNAME"
    log_info "  Password: [as configured]"
    echo
    log_info "Useful Commands:"
    log_info "  Stop services:    docker-compose stop"
    log_info "  Start services:   docker-compose start"
    log_info "  View logs:        docker-compose logs -f"
    log_info "  Update services:  docker-compose pull && docker-compose up -d"
    echo
    log_info "Project Directory: $PROJECT_DIR"
    log_info "Configuration File: $PROJECT_DIR/.env"
    echo
    log_warn "Please secure your system:"
    log_warn "1. Change default passwords in .env file"
    log_warn "2. Configure firewall rules"
    log_warn "3. Set up SSL certificates for production"
    log_warn "4. Regularly backup your data"
}

# Main installation flow
main() {
    log_info "Starting SOC Platform installation..."

    check_requirements
    install_docker
    install_docker_compose
    setup_project
    configure_environment
    start_services
    create_admin_user
    show_completion_info

    log_info "Installation completed successfully!"
}

# Handle interruption
trap 'log_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"