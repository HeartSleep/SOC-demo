# ✅ Docker一键启动 - 完成清单

## 🎉 已完成的工作

### 1. Docker配置文件

| 文件 | 说明 | 状态 |
|------|------|------|
| `docker-compose.full.yml` | 完整生产环境配置（PostgreSQL + Redis + Celery） | ✅ |
| `backend/Dockerfile.prod` | 生产环境后端Dockerfile | ✅ |
| `backend/Dockerfile` | 开发环境Dockerfile（已存在） | ✅ |
| `.env` | 环境变量配置（启动时自动创建） | ✅ |

### 2. 启动脚本

| 文件 | 说明 | 状态 |
|------|------|------|
| `docker-start.sh` | 一键启动脚本（交互式） | ✅ |
| `docker-stop.sh` | 一键停止脚本 | ✅ |

### 3. 依赖更新

| 文件 | 更新内容 | 状态 |
|------|----------|------|
| `backend/requirements/base.txt` | 添加PostgreSQL和API扫描依赖 | ✅ |
| - | SQLAlchemy + asyncpg | ✅ |
| - | beautifulsoup4 + lxml | ✅ |
| - | playwright（可选） | ✅ |

### 4. 文档

| 文件 | 说明 | 状态 |
|------|------|------|
| `QUICK_START.md` | 快速启动指南 | ✅ |
| `DOCKER_SETUP.md` | 详细Docker使用文档 | ✅ |
| `docs/API_SECURITY_SCANNER.md` | API安全检测功能说明 | ✅ |
| `docs/API_SECURITY_INTEGRATION.md` | 前后端集成说明 | ✅ |

---

## 🚀 立即开始

### 方式一：一键启动（推荐）

```bash
# 1. 给予执行权限
chmod +x docker-start.sh docker-stop.sh

# 2. 启动所有服务
./docker-start.sh

# 3. 等待1-2分钟，然后访问
# 前端: http://localhost:3000
# 后端: http://localhost:8000/docs
```

### 方式二：手动启动

```bash
# 1. 创建.env文件
cat > .env << 'EOF'
POSTGRES_USER=soc_user
POSTGRES_PASSWORD=soc_password_2024
POSTGRES_DB=soc_platform
REDIS_PASSWORD=redis_password_2024
SECRET_KEY=soc-platform-secret-key-2024
EOF

# 2. 构建并启动
docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.full.yml logs -f
```

---

## 📦 服务清单

启动后包含以下服务：

### 核心服务
- ✅ **PostgreSQL 15** - 主数据库（端口5432）
- ✅ **Redis 7** - 缓存和消息队列（端口6379）
- ✅ **Backend API** - FastAPI服务（端口8000）
- ✅ **Celery Worker** - 异步任务执行
- ✅ **Celery Beat** - 定时任务调度（可选）
- ✅ **Frontend** - Vue.js界面（端口3000）

### 功能特性
- ✅ API安全检测
- ✅ JS资源提取
- ✅ 动态API发现
- ✅ 微服务架构识别
- ✅ 未授权访问检测
- ✅ 敏感信息扫描

---

## ⚙️ 配置说明

### 数据库配置（PostgreSQL）

```yaml
POSTGRES_USER: soc_user
POSTGRES_PASSWORD: soc_password_2024
POSTGRES_DB: soc_platform
Port: 5432
```

### Redis配置

```yaml
REDIS_PASSWORD: redis_password_2024
Port: 6379
```

### Celery配置

```yaml
CELERY_BROKER_URL: redis://:redis_password_2024@redis:6379/1
CELERY_RESULT_BACKEND: redis://:redis_password_2024@redis:6379/2
Worker Concurrency: 4
```

---

## 🔍 验证安装

### 1. 检查服务状态

```bash
docker-compose -f docker-compose.full.yml ps
```

预期输出：
```
NAME                STATUS
soc_postgres        Up (healthy)
soc_redis           Up (healthy)
soc_backend         Up (healthy)
soc_celery_worker   Up
soc_frontend        Up
```

### 2. 测试后端API

```bash
curl http://localhost:8000/health
```

预期响应：
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "features": {
    "database": "postgresql",
    "caching": "enabled"
  }
}
```

### 3. 测试前端

访问 http://localhost:3000，应该看到登录页面

### 4. 测试Celery Worker

```bash
docker logs soc_celery_worker | grep "ready"
```

预期看到：`celery@xxx ready.`

---

## 🧪 功能测试

### 测试API安全检测

1. 登录系统（admin / admin123）
2. 访问 `/api-security` 页面
3. 点击"创建扫描任务"
4. 填写：
   - 任务名称：测试扫描
   - 目标URL：https://www.baidu.com
   - 选择所有扫描选项
5. 点击创建
6. 等待扫描完成（1-3分钟）
7. 查看扫描结果

---

## 🐛 常见问题

### Q1: 端口被占用

**症状**：启动失败，提示端口已被使用

**解决**：
```bash
# 方法1：停止占用端口的服务
# 方法2：修改 docker-compose.full.yml 中的端口映射
ports:
  - "8001:8000"  # 将8000改为其他端口
```

### Q2: Celery Worker 不工作

**症状**：API扫描任务一直处于pending状态

**诊断**：
```bash
# 检查Worker状态
docker logs soc_celery_worker

# 检查Redis连接
docker exec soc_redis redis-cli -a redis_password_2024 ping
```

**解决**：
```bash
# 重启Celery Worker
docker-compose -f docker-compose.full.yml restart celery_worker
```

### Q3: 数据库迁移失败

**症状**：后端启动失败，提示数据库表不存在

**解决**：
```bash
# 手动运行迁移
docker exec soc_backend alembic upgrade head

# 如果没有迁移文件，创建一个
docker exec soc_backend alembic revision --autogenerate -m "init"
docker exec soc_backend alembic upgrade head
```

### Q4: 前端无法连接后端

**症状**：前端页面加载失败或API调用失败

**诊断**：
```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查网络
docker network inspect soc_soc_network
```

**解决**：
- 确保后端服务健康
- 检查CORS配置
- 清除浏览器缓存

---

## 🔒 生产环境建议

### 1. 修改默认密码

编辑 `.env` 文件：
```bash
POSTGRES_PASSWORD=your-strong-password-here
REDIS_PASSWORD=your-redis-password-here
SECRET_KEY=your-secret-key-min-32-characters
```

### 2. 配置反向代理

使用Nginx作为反向代理，配置SSL证书。

### 3. 限制端口暴露

生产环境只暴露80和443端口：
```yaml
ports:
  # - "8000:8000"  # 注释掉
  # - "5432:5432"  # 注释掉
  # - "6379:6379"  # 注释掉
```

### 4. 启用备份

```bash
# 数据库备份脚本
docker exec soc_postgres pg_dump -U soc_user soc_platform > backup_$(date +%Y%m%d).sql
```

### 5. 监控配置

- 配置Prometheus + Grafana
- 设置告警规则
- 启用日志收集

---

## 📊 性能优化

### 调整Celery Worker数量

编辑 `docker-compose.full.yml`：
```yaml
celery_worker:
  command: celery -A app.core.celery.celery_app worker --loglevel=info --concurrency=8
```

### 调整数据库连接池

在 `.env` 中添加：
```bash
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60
```

### 启用缓存

Redis已配置AOF持久化，性能和可靠性平衡。

---

## 📝 更新和维护

### 更新代码

```bash
# 1. 停止服务
./docker-stop.sh

# 2. 拉取最新代码
git pull

# 3. 重新构建
docker-compose -f docker-compose.full.yml build --no-cache

# 4. 启动服务
./docker-start.sh
```

### 数据备份

```bash
# 自动备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec soc_postgres pg_dump -U soc_user soc_platform | gzip > backup_$DATE.sql.gz
echo "Backup completed: backup_$DATE.sql.gz"
EOF
chmod +x backup.sh
```

### 日志管理

```bash
# 清理旧日志
docker-compose -f docker-compose.full.yml logs --tail=100 > recent_logs.txt
```

---

## 🎓 学习资源

- [Docker官方文档](https://docs.docker.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Celery文档](https://docs.celeryproject.org/)
- [Vue.js文档](https://vuejs.org/)

---

## 📞 技术支持

遇到问题？

1. 查看 `DOCKER_SETUP.md` 详细文档
2. 检查日志：`docker-compose logs -f`
3. GitHub Issues
4. 联系开发团队

---

## ✨ 功能亮点

### API安全检测（核心功能）

- 🔍 **智能JS解析** - 自动提取静态、动态、Webpack资源
- 🎯 **API分层架构** - 基础URL + 基础API路径 + API路径
- 🏗️ **微服务识别** - 自动识别和分组不同服务
- 🚨 **安全检测** - 未授权访问、敏感信息、组件漏洞
- 🤖 **AI预留接口** - 支持未来集成LLM

---

**🎉 恭喜！Docker一键启动环境已配置完成！**

现在你可以使用 `./docker-start.sh` 快速启动整个系统了！
