#!/bin/bash

# Frontend-Backend Integrated Startup Script
# This script starts both frontend and backend with proper configuration

echo "=========================================="
echo "🚀 SOC Platform Integrated Startup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $service to start...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null; then
            echo -e "${GREEN}✅ $service is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ $service failed to start after $max_attempts seconds${NC}"
    return 1
}

# Kill existing processes on ports
echo "🔍 Checking for existing services..."

if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Stopping existing backend...${NC}"
    pkill -f "uvicorn app.main:app" 2>/dev/null
    sleep 2
fi

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is in use. Stopping existing frontend...${NC}"
    pkill -f "vite" 2>/dev/null
    sleep 2
fi

# Start Backend
echo ""
echo "=========================================="
echo "📦 Starting Backend Service"
echo "=========================================="

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo "📦 Installing backend dependencies..."
pip install -q -r requirements.txt

# Set environment variables for demo mode
export DATABASE_URL="postgresql+asyncpg://soc_admin:soc_secure_password_2024@localhost:5432/soc_platform"
export DEBUG=True
export SECRET_KEY="demo-secret-key-change-in-production"
export JWT_SECRET_KEY="demo-jwt-key-change-in-production"

# Start backend in background
echo -e "${GREEN}🚀 Starting backend on http://localhost:8000${NC}"
nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
wait_for_service "http://localhost:8000/health" "Backend"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend is running (PID: $BACKEND_PID)${NC}"
    echo "   📄 Logs: backend/backend.log"
    echo "   📚 API Docs: http://localhost:8000/docs"
else
    echo -e "${RED}❌ Backend failed to start. Check backend/backend.log for errors${NC}"
    exit 1
fi

cd ..

# Start Frontend
echo ""
echo "=========================================="
echo "🎨 Starting Frontend Service"
echo "=========================================="

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend in background
echo -e "${GREEN}🚀 Starting frontend on http://localhost:3000${NC}"
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
sleep 5  # Give frontend time to compile
wait_for_service "http://localhost:3000" "Frontend"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend is running (PID: $FRONTEND_PID)${NC}"
    echo "   📄 Logs: frontend/frontend.log"
    echo "   🌐 URL: http://localhost:3000"
else
    echo -e "${YELLOW}⚠️  Frontend may still be compiling. Check frontend/frontend.log${NC}"
fi

cd ..

# Display summary
echo ""
echo "=========================================="
echo "📊 Services Status"
echo "=========================================="
echo -e "${GREEN}✅ Backend:${NC}  http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health:   http://localhost:8000/health"
echo ""
echo -e "${GREEN}✅ Frontend:${NC} http://localhost:3000"
echo "   • Login with: admin/admin"
echo ""
echo "=========================================="
echo "🧪 Test Integration"
echo "=========================================="
echo "Run integration tests with:"
echo "  python test_frontend_backend_integration.py"
echo ""
echo "=========================================="
echo "🛑 Stop Services"
echo "=========================================="
echo "To stop all services, run:"
echo "  pkill -f 'uvicorn app.main:app'"
echo "  pkill -f 'vite'"
echo ""
echo "Or use the PIDs:"
echo "  kill $BACKEND_PID  # Backend"
echo "  kill $FRONTEND_PID # Frontend"
echo ""
echo -e "${GREEN}🎉 Platform is ready!${NC}"
echo "   Open http://localhost:3000 in your browser"
echo ""

# Save PIDs to file for easy stopping
echo "BACKEND_PID=$BACKEND_PID" > .pids
echo "FRONTEND_PID=$FRONTEND_PID" >> .pids

# Keep script running and show logs
echo "=========================================="
echo "📋 Monitoring Services (Press Ctrl+C to stop)"
echo "=========================================="

# Trap Ctrl+C to clean shutdown
trap 'echo ""; echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT

# Monitor services
while true; do
    sleep 5

    # Check if backend is still running
    if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Backend stopped unexpectedly${NC}"
        break
    fi

    # Check if frontend is still running
    if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${RED}❌ Frontend stopped unexpectedly${NC}"
        break
    fi
done

echo "Services stopped. Check logs for details."