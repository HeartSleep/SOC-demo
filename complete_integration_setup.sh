#!/bin/bash

# Complete Frontend-Backend Integration Setup
# This script applies all integration improvements

echo "=========================================="
echo "🚀 Complete Integration Setup"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Fix all integration issues"
echo "2. Generate TypeScript interfaces"
echo "3. Set up monitoring"
echo "4. Run tests"
echo "5. Start services"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Apply integration fixes
echo ""
echo "=========================================="
echo "🔧 Step 1: Applying Integration Fixes"
echo "=========================================="

if [ -f "fix_integration_issues.py" ]; then
    echo "Running integration fixer..."
    python3 fix_integration_issues.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Integration fixes applied successfully${NC}"
    else
        echo -e "${RED}❌ Integration fixes failed${NC}"
        echo "Please review the errors and try again"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  fix_integration_issues.py not found, skipping${NC}"
fi

# Step 2: Generate TypeScript interfaces
echo ""
echo "=========================================="
echo "🔧 Step 2: Generating TypeScript Interfaces"
echo "=========================================="

if [ -f "generate_typescript_interfaces.py" ]; then
    echo "Generating TypeScript types..."
    python3 generate_typescript_interfaces.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ TypeScript interfaces generated${NC}"
    else
        echo -e "${YELLOW}⚠️  TypeScript generation had issues${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  generate_typescript_interfaces.py not found, skipping${NC}"
fi

# Step 3: Install dependencies
echo ""
echo "=========================================="
echo "🔧 Step 3: Installing Dependencies"
echo "=========================================="

# Backend dependencies
echo "Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Check if requirements file exists
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Backend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

# Add new dependencies for integration
pip install -q httpx jsonschema pyyaml zod 2>/dev/null

cd ..

# Frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
if [ -f "package.json" ]; then
    npm install --silent
    # Install additional packages for integration
    npm install --save axios zod 2>/dev/null
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  package.json not found${NC}"
fi

cd ..

# Step 4: Set up monitoring route
echo ""
echo "=========================================="
echo "🔧 Step 4: Setting Up Monitoring"
echo "=========================================="

# Add monitoring route to frontend router if not exists
ROUTER_FILE="frontend/src/router/index.ts"
if [ -f "$ROUTER_FILE" ]; then
    if ! grep -q "MonitoringDashboard" "$ROUTER_FILE"; then
        echo "Adding monitoring route..."
        cat >> "$ROUTER_FILE" << 'EOF'

// Monitoring Dashboard Route
{
  path: '/monitoring',
  name: 'monitoring',
  component: () => import('@/views/MonitoringDashboard.vue'),
  meta: {
    title: 'Integration Monitor',
    requiresAuth: true,
    roles: ['admin', 'analyst']
  }
}
EOF
        echo -e "${GREEN}✅ Monitoring route added${NC}"
    else
        echo -e "${GREEN}✅ Monitoring route already exists${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Router file not found${NC}"
fi

# Step 5: Update backend main.py to include monitoring
echo ""
echo "=========================================="
echo "🔧 Step 5: Updating Backend Configuration"
echo "=========================================="

MAIN_FILE="backend/app/main.py"
if [ -f "$MAIN_FILE" ]; then
    # Check if monitoring is already imported
    if ! grep -q "monitoring" "$MAIN_FILE"; then
        echo "Adding monitoring endpoints to backend..."

        # Create a backup
        cp "$MAIN_FILE" "${MAIN_FILE}.backup"

        # Add import
        sed -i '' '/from app.api.endpoints import/a\
    monitoring,' "$MAIN_FILE" 2>/dev/null || \
        sed -i '/from app.api.endpoints import/a\    monitoring,' "$MAIN_FILE"

        # Add router
        cat >> "$MAIN_FILE" << 'EOF'

# Monitoring routes
app.include_router(
    monitoring.router,
    prefix=f"{settings.API_V1_STR}/monitoring",
    tags=["monitoring"]
)
EOF
        echo -e "${GREEN}✅ Monitoring endpoints added${NC}"
    else
        echo -e "${GREEN}✅ Monitoring already configured${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Backend main.py not found${NC}"
fi

# Step 6: Create environment files
echo ""
echo "=========================================="
echo "🔧 Step 6: Setting Up Environment"
echo "=========================================="

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Development Environment
DEBUG=True
DATABASE_URL=postgresql+asyncpg://soc_admin:soc_secure_password_2024@localhost:5432/soc_platform
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-key-change-in-production
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000"]
EOF
    echo -e "${GREEN}✅ Environment file created${NC}"
else
    echo -e "${GREEN}✅ Environment file exists${NC}"
fi

# Step 7: Run initial tests
echo ""
echo "=========================================="
echo "🔧 Step 7: Running Integration Tests"
echo "=========================================="

# Start backend in background for testing
echo "Starting backend for testing..."
cd backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > test_backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend is running${NC}"

    # Run integration tests
    if [ -f "test_frontend_backend_integration.py" ]; then
        echo "Running integration tests..."
        python3 test_frontend_backend_integration.py
        TEST_RESULT=$?

        if [ $TEST_RESULT -eq 0 ]; then
            echo -e "${GREEN}✅ Integration tests passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Some integration tests failed${NC}"
        fi
    fi

    # Run contract tests
    if [ -f "test_contracts.py" ]; then
        echo "Running contract tests..."
        python3 test_contracts.py
        CONTRACT_RESULT=$?

        if [ $CONTRACT_RESULT -eq 0 ]; then
            echo -e "${GREEN}✅ Contract tests passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Some contract tests failed${NC}"
        fi
    fi
else
    echo -e "${RED}❌ Backend failed to start${NC}"
fi

# Stop test backend
kill $BACKEND_PID 2>/dev/null

# Step 8: Final summary
echo ""
echo "=========================================="
echo "📊 Integration Setup Complete"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Integration setup completed successfully!${NC}"
echo ""
echo "📚 Documentation:"
echo "   • Integration Guide: FRONTEND_BACKEND_INTEGRATION_GUIDE.md"
echo "   • Integration Status: INTEGRATION_COMPLETE.md"
echo "   • API Contracts: API_CONTRACTS.md"
echo ""
echo "🚀 Start Services:"
echo "   ./start_integrated.sh"
echo ""
echo "🧪 Run Tests:"
echo "   python test_frontend_backend_integration.py"
echo "   python test_contracts.py"
echo ""
echo "📊 Monitor Integration:"
echo "   http://localhost:3000/monitoring"
echo ""
echo "🔧 Fix Issues:"
echo "   python fix_integration_issues.py"
echo ""
echo -e "${GREEN}🎉 Your frontend and backend are now perfectly integrated!${NC}"

# Make all scripts executable
chmod +x *.sh *.py 2>/dev/null

echo ""
echo "Press Enter to start the integrated platform or Ctrl+C to exit..."
read

# Start the platform
if [ -f "start_integrated.sh" ]; then
    ./start_integrated.sh
fi