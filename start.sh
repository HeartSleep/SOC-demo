#!/bin/bash

# SOC Security Platform Startup Script
# This script manages the startup of both backend and frontend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if a port is in use
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    if check_port $1; then
        print_message "Killing process on port $1..." "$YELLOW"
        lsof -ti:$1 | xargs kill -9 2>/dev/null || true
    fi
}

# Function to wait for service
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if check_port $port; then
            print_message "✓ $service is running on port $port" "$GREEN"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    print_message "✗ Failed to start $service on port $port" "$RED"
    return 1
}

# Parse command line arguments
COMMAND=${1:-start}
MODE=${2:-dev}

case $COMMAND in
    start)
        print_message "Starting SOC Security Platform ($MODE mode)..." "$GREEN"

        # Kill any existing processes
        print_message "Cleaning up existing processes..." "$YELLOW"
        kill_port 8000
        kill_port 5173
        pkill -f "python.*main_local.py" 2>/dev/null || true
        pkill -f "npm run dev" 2>/dev/null || true
        pkill -f "vite" 2>/dev/null || true

        # Start backend
        print_message "Starting Backend API Server..." "$GREEN"
        cd backend

        # Create logs directory if it doesn't exist
        mkdir -p logs

        # Install dependencies if needed
        if [ ! -d "venv" ]; then
            print_message "Creating Python virtual environment..." "$YELLOW"
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt
        else
            source venv/bin/activate
        fi

        # Start backend based on mode
        if [ "$MODE" = "dev" ]; then
            PYTHONPATH=. nohup python app/main_local.py > logs/backend.log 2>&1 &
            BACKEND_PID=$!
        else
            PYTHONPATH=. nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
            BACKEND_PID=$!
        fi

        cd ..

        # Wait for backend to start
        wait_for_service 8000 "Backend API"

        # Start frontend
        print_message "Starting Frontend Development Server..." "$GREEN"
        cd frontend

        # Install dependencies if needed
        if [ ! -d "node_modules" ]; then
            print_message "Installing frontend dependencies..." "$YELLOW"
            npm install
        fi

        # Clean cache and start frontend
        rm -rf .vite 2>/dev/null || true
        nohup npm run dev > ../backend/logs/frontend.log 2>&1 &
        FRONTEND_PID=$!

        cd ..

        # Wait for frontend to start
        wait_for_service 5173 "Frontend"

        # Save PIDs
        echo "$BACKEND_PID" > .backend.pid
        echo "$FRONTEND_PID" > .frontend.pid

        print_message "\n✓ SOC Security Platform started successfully!" "$GREEN"
        print_message "  Backend:  http://localhost:8000" "$GREEN"
        print_message "  Frontend: http://localhost:5173" "$GREEN"
        print_message "\nLogs:" "$YELLOW"
        print_message "  Backend:  backend/logs/backend.log" "$NC"
        print_message "  Frontend: backend/logs/frontend.log" "$NC"
        print_message "\nTo stop: ./start.sh stop" "$YELLOW"
        ;;

    stop)
        print_message "Stopping SOC Security Platform..." "$YELLOW"

        # Kill using saved PIDs
        if [ -f .backend.pid ]; then
            kill $(cat .backend.pid) 2>/dev/null || true
            rm .backend.pid
        fi

        if [ -f .frontend.pid ]; then
            kill $(cat .frontend.pid) 2>/dev/null || true
            rm .frontend.pid
        fi

        # Kill by port as fallback
        kill_port 8000
        kill_port 5173

        # Kill by process name as last resort
        pkill -f "python.*main_local.py" 2>/dev/null || true
        pkill -f "npm run dev" 2>/dev/null || true
        pkill -f "vite" 2>/dev/null || true

        print_message "✓ SOC Security Platform stopped" "$GREEN"
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start $MODE
        ;;

    status)
        print_message "SOC Security Platform Status:" "$GREEN"

        if check_port 8000; then
            print_message "  ✓ Backend is running on port 8000" "$GREEN"
        else
            print_message "  ✗ Backend is not running" "$RED"
        fi

        if check_port 5173; then
            print_message "  ✓ Frontend is running on port 5173" "$GREEN"
        else
            print_message "  ✗ Frontend is not running" "$RED"
        fi
        ;;

    logs)
        SERVICE=${2:-all}
        case $SERVICE in
            backend)
                tail -f backend/logs/backend.log
                ;;
            frontend)
                tail -f backend/logs/frontend.log
                ;;
            all)
                tail -f backend/logs/*.log
                ;;
            *)
                print_message "Usage: $0 logs [backend|frontend|all]" "$YELLOW"
                ;;
        esac
        ;;

    *)
        print_message "Usage: $0 {start|stop|restart|status|logs} [dev|prod]" "$YELLOW"
        exit 1
        ;;
esac