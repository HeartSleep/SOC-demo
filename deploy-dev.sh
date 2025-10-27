#!/bin/bash
# =============================================================================
# SOC Platform - Development Deployment Script
# =============================================================================

set -e

echo "🚀 Starting SOC Platform Development Environment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.docker .env
    echo -e "${GREEN}✅ Created .env file. Please review and update if needed.${NC}"
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

# Stop any existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Clean up old containers and volumes (optional)
read -p "Do you want to clean up old volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 Cleaning up volumes...${NC}"
    docker-compose -f docker-compose.dev.yml down -v
fi

# Build images
echo -e "${BLUE}🏗️  Building Docker images...${NC}"
docker-compose -f docker-compose.dev.yml build --no-cache

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 10

# Check health
echo -e "${BLUE}🏥 Checking service health...${NC}"
docker-compose -f docker-compose.dev.yml ps

# Test backend
echo -e "${BLUE}🧪 Testing backend...${NC}"
if curl -sf http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend is not responding${NC}"
fi

# Show logs
echo -e "\n${GREEN}✅ Development environment is ready!${NC}"
echo -e "\n📍 Access points:"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:5173"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}  http://localhost:8000/docs"
echo -e "  ${BLUE}PostgreSQL:${NC} localhost:5432"
echo -e "  ${BLUE}Redis:${NC}     localhost:6379"

echo -e "\n📋 Useful commands:"
echo -e "  ${BLUE}View logs:${NC}        docker-compose -f docker-compose.dev.yml logs -f"
echo -e "  ${BLUE}Stop services:${NC}    docker-compose -f docker-compose.dev.yml down"
echo -e "  ${BLUE}Restart service:${NC}  docker-compose -f docker-compose.dev.yml restart backend"

echo -e "\n${YELLOW}💡 Tip: Your code changes will be automatically reloaded!${NC}"