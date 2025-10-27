#!/bin/bash
# SOC Platform 简化本地启动脚本

set -e

echo "🚀 启动 SOC 安全平台 (简化版)"
echo "================================="

# 创建日志目录
mkdir -p logs

# 检查并启动后端
echo "📦 启动后端服务..."
cd backend

# 使用简化的本地版本启动后端
python3 -m uvicorn app.main_local:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "后端已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 2

# 启动前端
echo "📦 启动前端服务..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "前端已启动 (PID: $FRONTEND_PID)"

# 保存PID
echo "$BACKEND_PID" > ../logs/backend.pid  
echo "$FRONTEND_PID" > ../logs/frontend.pid

echo ""
echo "✅ SOC 平台启动成功!"
echo ""
echo "🌐 前端地址: http://localhost:5173"
echo "🔧 后端API: http://localhost:8000" 
echo "📖 API文档: http://localhost:8000/docs"
echo ""
echo "默认登录账号:"
echo "用户名: admin"
echo "密码: admin123"
echo ""
echo "停止服务: ./stop-local.sh"

# 保持脚本运行
wait
