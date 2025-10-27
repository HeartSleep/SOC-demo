#!/bin/bash

# =============================================================================
# SOC Platform - Docker停止脚本
# =============================================================================

echo "🛑 停止SOC Platform..."
echo ""

# 检测使用的compose文件
if [ -f "docker-compose.full.yml" ]; then
    COMPOSE_FILE="docker-compose.full.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

echo "使用配置文件: $COMPOSE_FILE"
echo ""

# 停止服务
docker-compose -f $COMPOSE_FILE down

echo ""
echo "✓ SOC Platform 已停止"
echo ""
echo "如需删除数据卷，请执行:"
echo "  docker-compose -f $COMPOSE_FILE down -v"
echo ""
