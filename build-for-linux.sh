#!/bin/bash
# =============================================================================
# Build Docker Images for Linux from Mac
# Supports: Building on Mac (Intel/Apple Silicon) for Linux deployment
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Building Docker images for Linux deployment...${NC}"

# Check platform
CURRENT_ARCH=$(uname -m)
CURRENT_OS=$(uname -s)

echo -e "${BLUE}📍 Current platform: ${CURRENT_OS} (${CURRENT_ARCH})${NC}"

if [ "$CURRENT_OS" != "Darwin" ]; then
    echo -e "${YELLOW}⚠️  This script is designed to run on Mac. Running on: ${CURRENT_OS}${NC}"
    echo -e "${YELLOW}💡 For native Linux builds, use deploy-linux.sh directly on the server${NC}"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check Docker buildx
if ! docker buildx version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker buildx not available${NC}"
    echo -e "${BLUE}🔧 Setting up buildx...${NC}"
    docker buildx create --use --name multiarch --driver docker-container
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env not found. Creating from template...${NC}"
    cp .env.docker .env
    echo -e "${GREEN}✅ Created .env - please update before deploying${NC}"
fi

# Load environment
source .env

# Set build metadata
export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
export VERSION=${VERSION:-2.0.0}

echo -e "${BLUE}📦 Build Info:${NC}"
echo -e "  Version: ${VERSION}"
echo -e "  Build Date: ${BUILD_DATE}"
echo -e "  Target Platform: linux/amd64"

# Build backend for Linux
echo -e "\n${BLUE}🏗️  Building backend image for Linux...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --file ./backend/Dockerfile.linux \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VERSION="${VERSION}" \
    --tag soc-backend:${VERSION}-linux \
    --tag soc-backend:latest-linux \
    --load \
    ./backend

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend image built successfully${NC}"
else
    echo -e "${RED}❌ Backend build failed${NC}"
    exit 1
fi

# Build frontend for Linux
echo -e "\n${BLUE}🏗️  Building frontend image for Linux...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --file ./frontend/Dockerfile.prod \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VERSION="${VERSION}" \
    --tag soc-frontend:${VERSION}-linux \
    --tag soc-frontend:latest-linux \
    --load \
    ./frontend

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend image built successfully${NC}"
else
    echo -e "${RED}❌ Frontend build failed${NC}"
    exit 1
fi

# Show image sizes
echo -e "\n${BLUE}📊 Image Sizes:${NC}"
docker images | grep -E "soc-(backend|frontend)" | grep linux

# Export images for transfer (optional)
echo -e "\n${YELLOW}💡 To transfer images to Linux server:${NC}"
echo -e "${BLUE}1. Save images:${NC}"
echo -e "   docker save soc-backend:${VERSION}-linux | gzip > soc-backend-linux.tar.gz"
echo -e "   docker save soc-frontend:${VERSION}-linux | gzip > soc-frontend-linux.tar.gz"
echo -e "\n${BLUE}2. Transfer to server:${NC}"
echo -e "   scp soc-backend-linux.tar.gz soc-frontend-linux.tar.gz user@server:/path/"
echo -e "\n${BLUE}3. Load on server:${NC}"
echo -e "   docker load < soc-backend-linux.tar.gz"
echo -e "   docker load < soc-frontend-linux.tar.gz"

# Ask if user wants to save images
echo -e "\n"
read -p "Do you want to save images for transfer now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}💾 Saving images...${NC}"

    mkdir -p ./docker-images

    echo -e "${BLUE}📦 Saving backend image...${NC}"
    docker save soc-backend:${VERSION}-linux | gzip > ./docker-images/soc-backend-${VERSION}-linux.tar.gz

    echo -e "${BLUE}📦 Saving frontend image...${NC}"
    docker save soc-frontend:${VERSION}-linux | gzip > ./docker-images/soc-frontend-${VERSION}-linux.tar.gz

    echo -e "${GREEN}✅ Images saved to ./docker-images/${NC}"
    ls -lh ./docker-images/

    echo -e "\n${BLUE}📤 To deploy on Linux server:${NC}"
    echo -e "1. Transfer files:    scp docker-images/*.tar.gz user@server:/tmp/"
    echo -e "2. Load on server:    ./load-images.sh (or docker load < *.tar.gz)"
    echo -e "3. Deploy:            ./deploy-linux.sh"
fi

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "  1. Test images locally (optional): docker-compose -f docker-compose.linux.yml up"
echo -e "  2. Transfer to Linux server (if not using registry)"
echo -e "  3. Run deployment script on server: ./deploy-linux.sh"