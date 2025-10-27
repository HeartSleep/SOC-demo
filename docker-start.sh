#!/bin/bash

# =============================================================================
# SOC Platform - Docker一键启动脚本
# =============================================================================

set -e

echo "🚀 SOC Security Platform - Docker一键启动"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose未安装，请先安装docker-compose${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker和docker-compose已安装${NC}"
echo ""

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data logs data/logs data/uploads data/reports
echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# 创建.env文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "📝 创建.env配置文件..."
    cat > .env << 'ENVEOF'
# 数据库配置
POSTGRES_USER=soc_user
POSTGRES_PASSWORD=soc_password_2024
POSTGRES_DB=soc_platform

# Redis配置
REDIS_PASSWORD=redis_password_2024

# 应用配置
SECRET_KEY=soc-platform-secret-key-change-in-production-2024
DEBUG=false
ENVIRONMENT=production
ENVEOF
    echo -e "${GREEN}✓ .env文件创建完成${NC}"
else
    echo -e "${YELLOW}⚠ .env文件已存在，跳过创建${NC}"
fi
echo ""

# 询问启动模式
echo "请选择启动模式:"
echo "1) 完整模式 (PostgreSQL + Redis + Backend + Celery + Frontend)"
echo "2) 开发模式 (使用现有配置)"
echo ""
read -p "请输入选项 [1/2] (默认: 1): " MODE
MODE=${MODE:-1}

if [ "$MODE" == "1" ]; then
    COMPOSE_FILE="docker-compose.full.yml"
    echo -e "${GREEN}✓ 使用完整模式${NC}"
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "${GREEN}✓ 使用开发模式${NC}"
fi
echo ""

# 停止并删除旧容器
echo "🛑 停止并删除旧容器..."
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose -f $COMPOSE_FILE build --no-cache
echo -e "${GREEN}✓ 镜像构建完成${NC}"
echo ""

# 启动服务
echo "🚀 启动所有服务..."
docker-compose -f $COMPOSE_FILE up -d
echo -e "${GREEN}✓ 服务启动完成${NC}"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15
echo ""

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose -f $COMPOSE_FILE ps
echo ""

# 显示日志
echo "📋 显示最近的日志..."
docker-compose -f $COMPOSE_FILE logs --tail=50
echo ""

# 显示访问信息
echo "=========================================="
echo -e "${GREEN}🎉 SOC Platform 启动成功！${NC}"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  🌐 前端: http://localhost:3000"
echo "  🔧 后端API: http://localhost:8000"
echo "  📚 API文档: http://localhost:8000/docs"
echo "  💾 PostgreSQL: localhost:5432"
echo "  🔴 Redis: localhost:6379"
echo ""
echo "默认账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose -f $COMPOSE_FILE logs -f"
echo "  停止服务: docker-compose -f $COMPOSE_FILE down"
echo "  重启服务: docker-compose -f $COMPOSE_FILE restart"
echo "  进入后端: docker exec -it soc_backend bash"
echo "  进入数据库: docker exec -it soc_postgres psql -U soc_user -d soc_platform"
echo ""
echo "=========================================="
echo -e "${YELLOW}💡 提示: 首次启动需要初始化数据库，请等待1-2分钟${NC}"
echo "=========================================="
echo ""

# 询问是否查看实时日志
read -p "是否查看实时日志? [y/N]: " VIEW_LOGS
if [ "$VIEW_LOGS" == "y" ] || [ "$VIEW_LOGS" == "Y" ]; then
    echo ""
    echo "按 Ctrl+C 退出日志查看"
    sleep 2
    docker-compose -f $COMPOSE_FILE logs -f
fi
