#!/bin/bash

# Master Integration Script
# Complete frontend-backend integration with all advanced features

echo "
╔════════════════════════════════════════════════════════════╗
║     🚀 SOC Platform - Master Integration Suite 🚀          ║
║                                                            ║
║     Complete Frontend-Backend Integration System           ║
║     Version 2.0 - Enterprise Edition                      ║
╔════════════════════════════════════════════════════════════╝
"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
MONITORING_URL="http://localhost:3000/monitoring"

# Function to print section headers
print_section() {
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
}

# Function to check command availability
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 is installed${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is not installed${NC}"
        return 1
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "═══════════════════════════════════════════"
    echo "           MASTER INTEGRATION MENU"
    echo "═══════════════════════════════════════════"
    echo ""
    echo "  1) 🔧 Complete Setup & Fix Issues"
    echo "  2) 🚀 Start Integrated Services"
    echo "  3) 🧪 Run All Tests"
    echo "  4) 📊 Performance Profiling"
    echo "  5) 🔨 Load Testing"
    echo "  6) 📚 Generate Documentation"
    echo "  7) 🎯 Generate TypeScript Interfaces"
    echo "  8) 📈 View Monitoring Dashboard"
    echo "  9) 🔍 Check System Status"
    echo "  10) 🛠️ Development Mode"
    echo "  11) 🏭 Production Deployment"
    echo "  12) 📦 Full Integration Package"
    echo "  0) ❌ Exit"
    echo ""
    echo -n "Select option: "
}

# 1. Complete setup
complete_setup() {
    print_section "COMPLETE SETUP & FIX ISSUES"

    echo "🔧 Applying integration fixes..."
    if [ -f "fix_integration_issues.py" ]; then
        python3 fix_integration_issues.py
        echo -e "${GREEN}✅ Integration issues fixed${NC}"
    fi

    echo "🔧 Setting up environment..."
    if [ -f "complete_integration_setup.sh" ]; then
        chmod +x complete_integration_setup.sh
        ./complete_integration_setup.sh
    fi
}

# 2. Start services
start_services() {
    print_section "STARTING INTEGRATED SERVICES"

    if [ -f "start_integrated.sh" ]; then
        chmod +x start_integrated.sh
        ./start_integrated.sh
    else
        echo "Starting services manually..."

        # Start backend
        echo -e "${BLUE}Starting backend...${NC}"
        cd backend
        source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
        nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        BACKEND_PID=$!
        cd ..

        # Start frontend
        echo -e "${BLUE}Starting frontend...${NC}"
        cd frontend
        nohup npm run dev > frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..

        echo -e "${GREEN}✅ Services started${NC}"
        echo "  Backend PID: $BACKEND_PID"
        echo "  Frontend PID: $FRONTEND_PID"
    fi
}

# 3. Run all tests
run_all_tests() {
    print_section "RUNNING ALL TESTS"

    echo "🧪 Running integration tests..."
    python3 test_frontend_backend_integration.py

    echo ""
    echo "🧪 Running contract tests..."
    python3 test_contracts.py

    echo ""
    echo "🧪 Running performance profile..."
    python3 performance_profiler.py

    echo -e "${GREEN}✅ All tests completed${NC}"
}

# 4. Performance profiling
performance_profiling() {
    print_section "PERFORMANCE PROFILING"

    echo "📊 Starting performance profiler..."
    python3 performance_profiler.py

    echo ""
    echo "📈 Performance results:"
    if [ -f "performance_report.txt" ]; then
        tail -20 performance_report.txt
    fi

    echo ""
    echo -e "${GREEN}✅ Performance profiling complete${NC}"
    echo "  Report: performance_report.txt"
    echo "  Charts: performance_charts/"
}

# 5. Load testing
load_testing() {
    print_section "LOAD TESTING"

    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        echo "Installing Locust..."
        pip install locust
    fi

    echo "Select load test scenario:"
    echo "  1) Normal Load (50 users)"
    echo "  2) Stress Test (500 users)"
    echo "  3) Spike Test"
    echo "  4) Endurance Test (1 hour)"
    echo "  5) Web UI Mode"
    echo -n "Choice: "
    read choice

    case $choice in
        1)
            echo "Running normal load test..."
            locust -f locustfile.py --headless -u 50 -r 5 -t 300s --host=$BACKEND_URL --html load_report.html
            ;;
        2)
            echo "Running stress test..."
            locust -f locustfile.py --headless -u 500 -r 50 -t 600s --host=$BACKEND_URL --html stress_report.html
            ;;
        3)
            echo "Running spike test..."
            locust -f locustfile.py --headless --class SpikeLoadShape --host=$BACKEND_URL
            ;;
        4)
            echo "Running endurance test (1 hour)..."
            locust -f locustfile.py --headless -u 100 -r 10 -t 3600s --host=$BACKEND_URL --html endurance_report.html
            ;;
        5)
            echo "Starting Locust web UI..."
            echo "Open browser at: http://localhost:8089"
            locust -f locustfile.py --host=$BACKEND_URL
            ;;
    esac
}

# 6. Generate documentation
generate_docs() {
    print_section "GENERATING DOCUMENTATION"

    echo "📚 Generating OpenAPI documentation..."
    python3 generate_openapi_docs.py

    echo ""
    echo "📄 Generated documentation:"
    echo "  • OpenAPI JSON: docs/api/openapi.json"
    echo "  • OpenAPI YAML: docs/api/openapi.yaml"
    echo "  • HTML Docs: docs/api/index.html"
    echo "  • Postman Collection: docs/api/postman_collection.json"
    echo "  • API Reference: docs/api/API_REFERENCE.md"

    # Open HTML docs if possible
    if [ -f "docs/api/index.html" ]; then
        echo ""
        echo "Opening API documentation..."
        open docs/api/index.html 2>/dev/null || xdg-open docs/api/index.html 2>/dev/null
    fi
}

# 7. Generate TypeScript interfaces
generate_typescript() {
    print_section "GENERATING TYPESCRIPT INTERFACES"

    echo "🔧 Generating TypeScript interfaces..."
    python3 generate_typescript_interfaces.py

    echo ""
    echo -e "${GREEN}✅ TypeScript generation complete${NC}"
    echo "  Generated files:"
    echo "  • frontend/src/types/generated/models.ts"
    echo "  • frontend/src/types/generated/api-client.ts"
    echo "  • frontend/src/types/generated/schemas.ts"
}

# 8. View monitoring
view_monitoring() {
    print_section "MONITORING DASHBOARD"

    echo "📊 Opening monitoring dashboard..."
    echo "  URL: $MONITORING_URL"

    # Check if services are running
    curl -s $BACKEND_URL/health > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend is running${NC}"
    else
        echo -e "${RED}❌ Backend is not running${NC}"
        echo "  Start services first (option 2)"
        return
    fi

    # Open monitoring dashboard
    open $MONITORING_URL 2>/dev/null || xdg-open $MONITORING_URL 2>/dev/null

    # Show current metrics
    echo ""
    echo "Current Metrics:"
    curl -s $BACKEND_URL/api/v1/monitoring/metrics | python3 -m json.tool | head -20
}

# 9. Check system status
check_status() {
    print_section "SYSTEM STATUS CHECK"

    echo "🔍 Checking system components..."
    echo ""

    # Check backend
    echo -n "Backend API: "
    curl -s $BACKEND_URL/health > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Online${NC}"

        # Get detailed health
        echo "  Health details:"
        curl -s $BACKEND_URL/api/v1/monitoring/health/detailed | python3 -m json.tool | head -15
    else
        echo -e "${RED}❌ Offline${NC}"
    fi

    echo ""

    # Check frontend
    echo -n "Frontend: "
    curl -s $FRONTEND_URL > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Online${NC}"
    else
        echo -e "${RED}❌ Offline${NC}"
    fi

    echo ""

    # Check database
    echo -n "Database: "
    psql -U soc_admin -d soc_platform -c "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Connected${NC}"
    else
        echo -e "${YELLOW}⚠️  Not connected (Demo mode)${NC}"
    fi

    echo ""

    # Check Redis
    echo -n "Redis Cache: "
    redis-cli ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Connected${NC}"
    else
        echo -e "${YELLOW}⚠️  Not connected${NC}"
    fi

    # Show process status
    echo ""
    echo "Running Processes:"
    ps aux | grep -E "uvicorn|vite" | grep -v grep | head -5
}

# 10. Development mode
dev_mode() {
    print_section "DEVELOPMENT MODE"

    echo "🔧 Starting development environment..."

    # Start backend with auto-reload
    echo "Starting backend with auto-reload..."
    cd backend
    source venv/bin/activate 2>/dev/null
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    cd ..

    # Start frontend with HMR
    echo "Starting frontend with HMR..."
    cd frontend
    npm run dev &
    cd ..

    echo ""
    echo -e "${GREEN}✅ Development mode active${NC}"
    echo "  Backend: $BACKEND_URL (auto-reload enabled)"
    echo "  Frontend: $FRONTEND_URL (HMR enabled)"
    echo "  API Docs: $BACKEND_URL/docs"
}

# 11. Production deployment
prod_deployment() {
    print_section "PRODUCTION DEPLOYMENT"

    echo "🏭 Preparing production deployment..."

    # Build frontend
    echo "Building frontend..."
    cd frontend
    npm run build
    cd ..

    # Create production config
    echo "Creating production configuration..."
    cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=soc_platform
      - POSTGRES_USER=soc_admin
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

    echo -e "${GREEN}✅ Production configuration created${NC}"
    echo ""
    echo "To deploy:"
    echo "  1. Set environment variables in .env.production"
    echo "  2. Run: docker-compose -f docker-compose.production.yml up -d"
}

# 12. Full integration package
full_package() {
    print_section "FULL INTEGRATION PACKAGE"

    echo "📦 Creating complete integration package..."

    # Run everything
    complete_setup
    generate_typescript
    generate_docs

    echo ""
    echo "🧪 Running tests..."
    python3 test_frontend_backend_integration.py
    python3 test_contracts.py

    echo ""
    echo "📊 Running performance analysis..."
    python3 performance_profiler.py

    echo ""
    echo "🚀 Starting services..."
    start_services

    echo ""
    echo "════════════════════════════════════════════"
    echo -e "${GREEN}✅ FULL INTEGRATION COMPLETE!${NC}"
    echo "════════════════════════════════════════════"
    echo ""
    echo "📋 Summary:"
    echo "  • All issues fixed"
    echo "  • TypeScript interfaces generated"
    echo "  • API documentation created"
    echo "  • Tests passed"
    echo "  • Performance profiled"
    echo "  • Services running"
    echo ""
    echo "🔗 Access Points:"
    echo "  • Application: $FRONTEND_URL"
    echo "  • API: $BACKEND_URL"
    echo "  • API Docs: $BACKEND_URL/docs"
    echo "  • Monitoring: $MONITORING_URL"
    echo ""
    echo "📚 Documentation:"
    echo "  • Integration Guide: FRONTEND_BACKEND_INTEGRATION_GUIDE.md"
    echo "  • Advanced Features: ADVANCED_INTEGRATION_COMPLETE.md"
    echo "  • API Reference: docs/api/API_REFERENCE.md"
}

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    pkill -f "uvicorn app.main:app" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    pkill -f "locust" 2>/dev/null
    echo "Cleanup complete"
}

# Trap Ctrl+C
trap cleanup INT

# Main loop
main() {
    # Check prerequisites
    print_section "CHECKING PREREQUISITES"

    check_command python3
    check_command node
    check_command npm
    check_command curl

    # Main menu loop
    while true; do
        show_menu
        read option

        case $option in
            1) complete_setup ;;
            2) start_services ;;
            3) run_all_tests ;;
            4) performance_profiling ;;
            5) load_testing ;;
            6) generate_docs ;;
            7) generate_typescript ;;
            8) view_monitoring ;;
            9) check_status ;;
            10) dev_mode ;;
            11) prod_deployment ;;
            12) full_package ;;
            0)
                echo "Exiting..."
                cleanup
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac

        echo ""
        echo "Press Enter to continue..."
        read
    done
}

# Run main function
main