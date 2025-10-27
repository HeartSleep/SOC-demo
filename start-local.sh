#!/bin/bash
# SOC Platform Local Development Startup Script

set -e

echo "🚀 启动 SOC 安全平台 (本地开发模式)"
echo "================================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python 3.9+"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 16+"
    exit 1
fi

# 检查并安装后端依赖
echo "📦 检查后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements/base.txt

echo "📦 检查前端依赖..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "🔧 修改配置为本地模式..."
# 修改后端配置使用内存数据库
cd ../backend
export DEBUG=true
export MONGODB_URL="sqlite:///./soc_local.db"  # 使用 SQLite 替代 MongoDB
export REDIS_URL="memory://"  # 使用内存替代 Redis

echo "🚀 启动服务..."

# 启动后端 (后台运行)
echo "启动后端服务..."
source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

echo ""
echo "✅ SOC 平台启动成功!"
echo "🌐 前端访问地址: http://localhost:5173"
echo "🔧 后端 API 地址: http://localhost:8000"
echo "📖 API 文档地址: http://localhost:8000/docs"
echo ""
echo "停止服务命令: ./stop-local.sh"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID" > ../logs/backend.pid
echo "$FRONTEND_PID" > ../logs/frontend.pid

echo "按 Ctrl+C 停止所有服务"
wait
