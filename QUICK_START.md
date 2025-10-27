# 🚀 SOC Platform - 快速启动指南

## Docker 一键启动（推荐）

### 1. 确保Docker已安装

```bash
docker --version
docker-compose --version
```

### 2. 一键启动

```bash
# 给予脚本执行权限
chmod +x docker-start.sh

# 启动所有服务（包含API安全检测功能）
./docker-start.sh
```

### 3. 访问系统

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000  
- **API文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

### 4. 停止服务

```bash
./docker-stop.sh
```

---

## 功能亮点

### ✨ API安全检测（新功能）

访问 `/api-security` 页面体验：

1. **JS资源提取** - 自动提取目标网站的所有JS文件
2. **API发现** - 智能识别API接口（支持动态拼接）
3. **微服务识别** - 自动识别和分组微服务架构
4. **未授权检测** - 检测API未授权访问问题
5. **敏感信息检测** - 扫描敏感信息泄露

#### 使用流程

1. 登录系统后，点击导航栏的 "API安全检测"
2. 点击 "创建扫描任务" 按钮
3. 填写任务名称和目标URL（如：https://example.com）
4. 选择扫描配置项
5. 点击创建，系统自动开始扫描
6. 查看扫描结果和安全问题

---

## 服务组件

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | Vue.js前端界面 |
| Backend | 8000 | FastAPI后端API |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存和消息队列 |
| Celery Worker | - | 异步任务执行（API扫描） |

---

## 常见命令

```bash
# 查看服务状态
docker-compose -f docker-compose.full.yml ps

# 查看日志
docker-compose -f docker-compose.full.yml logs -f

# 重启服务
docker-compose -f docker-compose.full.yml restart

# 进入后端容器
docker exec -it soc_backend bash

# 运行数据库迁移
docker exec soc_backend alembic upgrade head
```

---

## 故障排查

### 问题：端口被占用

```bash
# 修改 docker-compose.full.yml 中的端口映射
# 或者停止占用端口的服务
```

### 问题：API扫描任务一直pending

```bash
# 检查Celery Worker是否运行
docker ps | grep celery

# 查看Worker日志
docker logs soc_celery_worker -f
```

### 问题：前端无法连接后端

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 查看后端日志
docker logs soc_backend
```

---

## 详细文档

- **完整Docker文档**: [DOCKER_SETUP.md](./DOCKER_SETUP.md)
- **API安全检测功能**: [docs/API_SECURITY_SCANNER.md](./docs/API_SECURITY_SCANNER.md)
- **前后端集成**: [docs/API_SECURITY_INTEGRATION.md](./docs/API_SECURITY_INTEGRATION.md)

---

## 技术栈

**后端**:
- FastAPI
- SQLAlchemy (PostgreSQL)
- Celery
- Redis
- Beautiful Soup (JS解析)

**前端**:
- Vue 3
- TypeScript
- Element Plus
- Vite

**基础设施**:
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7
- Nginx

---

## 🎯 下一步

1. 修改默认密码
2. 配置邮件通知
3. 设置定时扫描任务
4. 导出安全报告

**祝使用愉快！** 🎉
