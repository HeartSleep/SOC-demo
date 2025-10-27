# SOC Platform - Docker一键启动指南

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM
- 10GB 磁盘空间

### 一键启动

```bash
# 给予执行权限
chmod +x docker-start.sh docker-stop.sh

# 启动系统
./docker-start.sh

# 停止系统
./docker-stop.sh
```

## 📋 服务架构

完整模式包含以下服务：

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| PostgreSQL | soc_postgres | 5432 | 主数据库 |
| Redis | soc_redis | 6379 | 缓存和消息队列 |
| Backend | soc_backend | 8000 | FastAPI后端服务 |
| Celery Worker | soc_celery_worker | - | 异步任务执行 |
| Frontend | soc_frontend | 3000 | Vue.js前端 |

## 🔧 配置说明

### 环境变量

在项目根目录的 `.env` 文件中配置：

```bash
# 数据库配置
POSTGRES_USER=soc_user
POSTGRES_PASSWORD=soc_password_2024
POSTGRES_DB=soc_platform

# Redis配置
REDIS_PASSWORD=redis_password_2024

# 应用配置
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### 数据持久化

数据卷配置：
- `postgres_data`: PostgreSQL数据
- `redis_data`: Redis持久化数据
- `./data`: 应用数据（上传文件、报告等）
- `./logs`: 应用日志

## 📚 使用指南

### 访问应用

启动成功后，访问以下地址：

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Redoc文档**: http://localhost:8000/redoc

### 默认账号

```
用户名: admin
密码: admin123
```

⚠️ **生产环境请务必修改默认密码！**

### 常用命令

#### 查看服务状态
```bash
docker-compose -f docker-compose.full.yml ps
```

#### 查看实时日志
```bash
# 所有服务
docker-compose -f docker-compose.full.yml logs -f

# 单个服务
docker-compose -f docker-compose.full.yml logs -f backend
docker-compose -f docker-compose.full.yml logs -f celery_worker
```

#### 重启服务
```bash
# 重启所有服务
docker-compose -f docker-compose.full.yml restart

# 重启单个服务
docker-compose -f docker-compose.full.yml restart backend
```

#### 进入容器
```bash
# 进入后端容器
docker exec -it soc_backend bash

# 进入PostgreSQL
docker exec -it soc_postgres psql -U soc_user -d soc_platform

# 进入Redis
docker exec -it soc_redis redis-cli -a redis_password_2024
```

#### 数据库操作
```bash
# 运行数据库迁移
docker exec soc_backend alembic upgrade head

# 创建新的迁移
docker exec soc_backend alembic revision --autogenerate -m "migration message"

# 回滚迁移
docker exec soc_backend alembic downgrade -1
```

#### 清理系统
```bash
# 停止并删除容器
docker-compose -f docker-compose.full.yml down

# 同时删除数据卷（⚠️ 会删除所有数据）
docker-compose -f docker-compose.full.yml down -v

# 清理未使用的镜像
docker system prune -a
```

## 🔍 故障排查

### 1. 容器启动失败

查看容器日志：
```bash
docker-compose -f docker-compose.full.yml logs backend
```

常见问题：
- 端口被占用：修改 `docker-compose.full.yml` 中的端口映射
- 数据库连接失败：检查PostgreSQL是否正常启动
- 权限问题：确保 `data` 和 `logs` 目录有写权限

### 2. 数据库连接错误

检查PostgreSQL健康状态：
```bash
docker exec soc_postgres pg_isready -U soc_user
```

手动连接测试：
```bash
docker exec -it soc_postgres psql -U soc_user -d soc_platform
```

### 3. Celery Worker不工作

检查Celery Worker日志：
```bash
docker logs soc_celery_worker
```

手动重启Worker：
```bash
docker-compose -f docker-compose.full.yml restart celery_worker
```

### 4. 前端无法连接后端

检查后端健康状态：
```bash
curl http://localhost:8000/health
```

检查网络连接：
```bash
docker network inspect soc_soc_network
```

### 5. API扫描任务无响应

1. 检查Celery Worker是否运行
2. 检查Redis连接
3. 查看Worker日志

```bash
docker logs soc_celery_worker -f
```

## 🔒 安全建议

### 生产环境部署

1. **修改默认密码**
   ```bash
   # 修改 .env 文件中的密码
   POSTGRES_PASSWORD=your-strong-password
   REDIS_PASSWORD=your-redis-password
   SECRET_KEY=your-secret-key-min-32-characters
   ```

2. **启用HTTPS**
   - 使用Nginx反向代理
   - 配置SSL证书

3. **限制端口暴露**
   - 只暴露必要的端口（80, 443）
   - 数据库和Redis不对外暴露

4. **定期备份**
   ```bash
   # 备份数据库
   docker exec soc_postgres pg_dump -U soc_user soc_platform > backup.sql
   
   # 备份数据卷
   docker run --rm -v soc_postgres_data:/data -v $(pwd):/backup \
     alpine tar czf /backup/postgres_backup.tar.gz /data
   ```

5. **监控和日志**
   - 配置日志轮转
   - 设置监控告警

## 📊 性能优化

### 调整Worker数量

修改 `docker-compose.full.yml` 中的 Celery 配置：

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

### 启用Redis持久化

已默认启用AOF持久化，数据安全性高。

## 🆘 获取帮助

遇到问题？

1. 查看日志：`docker-compose logs -f`
2. 检查GitHub Issues
3. 联系技术支持

## 📝 更新日志

### v2.0.0 (2025-01-11)
- ✅ 添加API安全检测功能
- ✅ 集成Celery异步任务
- ✅ 支持PostgreSQL数据库
- ✅ 添加Docker一键启动
- ✅ 完善前后端集成

---

**祝使用愉快！** 🎉
