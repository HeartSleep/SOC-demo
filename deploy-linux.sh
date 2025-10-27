#!/bin/bash
# =============================================================================
# Deploy SOC Platform on Linux Server
# Supports: Ubuntu 20.04+, Debian 11+, CentOS 8+, RHEL 8+, Amazon Linux 2
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 SOC Platform Linux Deployment${NC}"
echo "========================================"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
    echo -e "${BLUE}📍 Detected OS: ${OS} ${VER}${NC}"
else
    echo -e "${RED}❌ Cannot detect OS${NC}"
    exit 1
fi

# Check if running as root or with sudo
if [ "$EUID" -eq 0 ]; then
    SUDO_CMD=""
else
    if ! command -v sudo &> /dev/null; then
        echo -e "${RED}❌ This script requires root or sudo privileges${NC}"
        exit 1
    fi
    SUDO_CMD="sudo"
fi

# Function to install Docker on different Linux distributions
install_docker() {
    echo -e "${BLUE}🐳 Installing Docker...${NC}"

    case "$OS" in
        *"Ubuntu"*|*"Debian"*)
            $SUDO_CMD apt-get update
            $SUDO_CMD apt-get install -y \
                apt-transport-https \
                ca-certificates \
                curl \
                gnupg \
                lsb-release

            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO_CMD gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

            echo \
              "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
              $(lsb_release -cs) stable" | $SUDO_CMD tee /etc/apt/sources.list.d/docker.list > /dev/null

            $SUDO_CMD apt-get update
            $SUDO_CMD apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;

        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*)
            $SUDO_CMD yum install -y yum-utils
            $SUDO_CMD yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            $SUDO_CMD yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            $SUDO_CMD systemctl start docker
            $SUDO_CMD systemctl enable docker
            ;;

        *"Amazon"*)
            $SUDO_CMD yum update -y
            $SUDO_CMD yum install -y docker
            $SUDO_CMD service docker start
            $SUDO_CMD systemctl enable docker
            ;;

        *)
            echo -e "${RED}❌ Unsupported OS: $OS${NC}"
            echo -e "${YELLOW}💡 Please install Docker manually: https://docs.docker.com/engine/install/${NC}"
            exit 1
            ;;
    esac

    # Add current user to docker group
    if [ -n "$SUDO_USER" ]; then
        $SUDO_CMD usermod -aG docker $SUDO_USER
        echo -e "${GREEN}✅ Added $SUDO_USER to docker group${NC}"
        echo -e "${YELLOW}⚠️  You may need to log out and back in for group changes to take effect${NC}"
    fi
}

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found${NC}"
    read -p "Install Docker now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_docker
    else
        echo -e "${RED}❌ Docker is required${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker is installed${NC}"
    docker --version
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose plugin not found${NC}"
    echo -e "${BLUE}Installing Docker Compose...${NC}"

    # Install Docker Compose plugin
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p $DOCKER_CONFIG/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose is installed${NC}"
    docker compose version
fi

# Check environment file
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}💡 Creating from template...${NC}"
    cp .env.docker .env

    echo -e "${RED}⚠️  IMPORTANT: You MUST update .env with secure values:${NC}"
    echo -e "  1. SECRET_KEY - Generate with: openssl rand -hex 32"
    echo -e "  2. POSTGRES_PASSWORD - Generate with: openssl rand -base64 32"
    echo -e "  3. BACKEND_CORS_ORIGINS - Set your domain"

    read -p "Press Enter to edit .env now (or Ctrl+C to exit and edit later)..."
    ${EDITOR:-vi} .env
fi

# Validate critical environment variables
source .env

if [ "$SECRET_KEY" == "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_USE_STRONG_RANDOM_STRING" ]; then
    echo -e "${RED}❌ SECRET_KEY not configured!${NC}"
    echo -e "${YELLOW}💡 Generate with: openssl rand -hex 32${NC}"
    exit 1
fi

if [ "$POSTGRES_PASSWORD" == "CHANGE_THIS_PASSWORD_IN_PRODUCTION" ]; then
    echo -e "${RED}❌ POSTGRES_PASSWORD not configured!${NC}"
    echo -e "${YELLOW}💡 Generate with: openssl rand -base64 32${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"

# Configure system limits for production
echo -e "${BLUE}🔧 Configuring system limits...${NC}"

# Increase file descriptors
if ! grep -q "fs.file-max" /etc/sysctl.conf; then
    echo -e "${BLUE}Setting system limits...${NC}"
    $SUDO_CMD bash -c 'cat >> /etc/sysctl.conf << EOF

# SOC Platform optimizations
fs.file-max = 65536
net.core.somaxconn = 32768
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
EOF'
    $SUDO_CMD sysctl -p
fi

# Create backup directory
echo -e "${BLUE}💾 Setting up backup directory...${NC}"
mkdir -p backups

# Backup existing deployment if running
if docker ps | grep -q soc_; then
    echo -e "${YELLOW}⚠️  Existing deployment detected${NC}"
    read -p "Create backup before redeployment? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        echo -e "${BLUE}📦 Backing up database...${NC}"
        docker compose -f docker-compose.linux.yml exec -T postgres pg_dump -U postgres soc_platform > "$BACKUP_DIR/database.sql" 2>/dev/null || true

        echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
    fi
fi

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker compose -f docker-compose.linux.yml down 2>/dev/null || true

# Pull or load images
if [ -d "./docker-images" ] && [ "$(ls -A ./docker-images/*.tar.gz 2>/dev/null)" ]; then
    echo -e "${BLUE}📦 Loading pre-built images...${NC}"

    for image in ./docker-images/*.tar.gz; do
        echo -e "${BLUE}Loading $(basename $image)...${NC}"
        docker load < "$image"
    done
else
    echo -e "${BLUE}🏗️  Building images locally...${NC}"
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    docker compose -f docker-compose.linux.yml build --no-cache
fi

# Create required directories
echo -e "${BLUE}📁 Creating data directories...${NC}"
mkdir -p data/logs data/uploads data/reports logs

# Set permissions
chmod 755 data logs
chmod -R 755 data/* logs/* 2>/dev/null || true

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker compose -f docker-compose.linux.yml up -d

# Wait for services
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 20

# Check health
echo -e "${BLUE}🏥 Checking service health...${NC}"
docker compose -f docker-compose.linux.yml ps

# Test backend
echo -e "${BLUE}🧪 Testing backend...${NC}"
MAX_RETRIES=15
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}⏳ Waiting for backend... (${RETRY_COUNT}/${MAX_RETRIES})${NC}"
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo -e "${YELLOW}📋 Backend logs:${NC}"
    docker compose -f docker-compose.linux.yml logs --tail=50 backend
    exit 1
fi

# Test frontend
if curl -sf http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend check failed (may need port 80/443)${NC}"
fi

# Show resource usage
echo -e "\n${BLUE}📊 Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || docker stats --no-stream

# Configure firewall (if ufw or firewalld available)
if command -v ufw &> /dev/null; then
    echo -e "\n${YELLOW}💡 Firewall detected (ufw). Configure ports:${NC}"
    echo -e "  sudo ufw allow 80/tcp"
    echo -e "  sudo ufw allow 443/tcp"
    echo -e "  sudo ufw allow 8000/tcp"
elif command -v firewall-cmd &> /dev/null; then
    echo -e "\n${YELLOW}💡 Firewall detected (firewalld). Configure ports:${NC}"
    echo -e "  sudo firewall-cmd --permanent --add-port=80/tcp"
    echo -e "  sudo firewall-cmd --permanent --add-port=443/tcp"
    echo -e "  sudo firewall-cmd --permanent --add-port=8000/tcp"
    echo -e "  sudo firewall-cmd --reload"
fi

# Show deployment info
echo -e "\n${GREEN}✅ Deployment Complete!${NC}"
echo -e "\n📍 Access Points:"
echo -e "  ${BLUE}Frontend:${NC}  http://$(hostname -I | awk '{print $1}')"
echo -e "  ${BLUE}Backend:${NC}   http://$(hostname -I | awk '{print $1}'):8000"
echo -e "  ${BLUE}Health:${NC}    http://$(hostname -I | awk '{print $1}'):8000/health"
echo -e "  ${BLUE}API Docs:${NC}  http://$(hostname -I | awk '{print $1}'):8000/docs"

echo -e "\n📋 Management Commands:"
echo -e "  ${BLUE}View logs:${NC}        docker compose -f docker-compose.linux.yml logs -f"
echo -e "  ${BLUE}Check status:${NC}     docker compose -f docker-compose.linux.yml ps"
echo -e "  ${BLUE}Resource usage:${NC}   docker stats"
echo -e "  ${BLUE}Stop services:${NC}    docker compose -f docker-compose.linux.yml down"
echo -e "  ${BLUE}Restart service:${NC}  docker compose -f docker-compose.linux.yml restart backend"

echo -e "\n${YELLOW}💡 Recommended next steps:${NC}"
echo -e "  1. Configure SSL/TLS certificates"
echo -e "  2. Set up automated backups"
echo -e "  3. Configure monitoring (Prometheus/Grafana)"
echo -e "  4. Set up log rotation"
echo -e "  5. Configure firewall rules"

echo -e "\n${GREEN}🎉 SOC Platform is now running on Linux!${NC}"