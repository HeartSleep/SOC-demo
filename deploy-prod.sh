#!/bin/bash
# =============================================================================
# SOC Platform - Production Deployment Script
# =============================================================================

set -e

echo "🚀 Starting SOC Platform Production Deployment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found. Please create one from .env.docker template.${NC}"
    exit 1
fi

# Check critical environment variables
echo -e "${BLUE}🔍 Checking environment configuration...${NC}"

source .env

if [ "$SECRET_KEY" == "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_USE_STRONG_RANDOM_STRING" ]; then
    echo -e "${RED}❌ SECRET_KEY is not set! Please update .env file.${NC}"
    echo -e "${YELLOW}💡 Generate with: openssl rand -hex 32${NC}"
    exit 1
fi

if [ "$POSTGRES_PASSWORD" == "CHANGE_THIS_PASSWORD_IN_PRODUCTION" ]; then
    echo -e "${RED}❌ POSTGRES_PASSWORD is not set! Please update .env file.${NC}"
    echo -e "${YELLOW}💡 Generate with: openssl rand -base64 32${NC}"
    exit 1
fi

if [ "$DEBUG" == "true" ]; then
    echo -e "${YELLOW}⚠️  WARNING: DEBUG is enabled in production!${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create backup
echo -e "${BLUE}💾 Creating backup...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database if exists
if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
    echo -e "${BLUE}📦 Backing up database...${NC}"
    docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres soc_platform > "$BACKUP_DIR/database.sql" 2>/dev/null || true
fi

# Set build date
export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Build images
echo -e "${BLUE}🏗️  Building production Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop old containers
echo -e "${BLUE}🛑 Stopping old containers...${NC}"
docker-compose -f docker-compose.prod.yml down

# Start new containers
echo -e "${BLUE}🚀 Starting production services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 20

# Check health
echo -e "${BLUE}🏥 Checking service health...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Test backend
echo -e "${BLUE}🧪 Testing backend...${NC}"
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8000/health > /dev/null; then
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
    docker-compose -f docker-compose.prod.yml logs --tail=50 backend
    exit 1
fi

# Test frontend
echo -e "${BLUE}🧪 Testing frontend...${NC}"
if curl -sf http://localhost/ > /dev/null; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${RED}❌ Frontend is not responding${NC}"
fi

# Show resource usage
echo -e "\n${BLUE}📊 Resource usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Show logs
echo -e "\n${GREEN}✅ Production deployment complete!${NC}"
echo -e "\n📍 Access points:"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
echo -e "  ${BLUE}Health:${NC}    http://localhost:8000/health"

echo -e "\n📋 Management commands:"
echo -e "  ${BLUE}View logs:${NC}        docker-compose -f docker-compose.prod.yml logs -f"
echo -e "  ${BLUE}Check status:${NC}     docker-compose -f docker-compose.prod.yml ps"
echo -e "  ${BLUE}Resource usage:${NC}   docker stats"
echo -e "  ${BLUE}Stop services:${NC}    docker-compose -f docker-compose.prod.yml down"

echo -e "\n${GREEN}🎉 SOC Platform is now running in production mode!${NC}"