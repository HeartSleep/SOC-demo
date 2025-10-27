# 🚀 修复后的部署指南

## 快速开始（5分钟）

### 1. 安装新依赖

```bash
cd /Users/heart/Documents/Code/WEB/SOC/backend
pip install -r requirements/base.txt
```

主要新增依赖：
- `slowapi==0.1.9` - API速率限制

### 2. 创建数据库迁移

```bash
cd backend

# 如果没有 alembic 目录，初始化
alembic init alembic

# 创建迁移文件
alembic revision --autogenerate -m "security_fixes_add_foreign_keys"

# 查看将要执行的SQL（可选）
alembic upgrade head --sql

# 应用迁移
alembic upgrade head
```

### 3. 验证配置

检查 `.env` 文件是否包含以下配置：

```bash
# Redis（用于速率限制）
REDIS_URL=redis://:redis_password_2024@redis:6379/0

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# 数据库
DATABASE_URL=postgresql+asyncpg://soc_user:soc_password_2024@localhost:5432/soc_platform
```

### 4. 重启服务

#### 方式一：Docker（推荐）

```bash
# 重新构建（包含新依赖）
docker-compose -f docker-compose.full.yml build backend celery_worker

# 重启服务
docker-compose -f docker-compose.full.yml restart backend celery_worker

# 或使用一键启动脚本
./docker-start.sh
```

#### 方式二：本地开发

```bash
# 停止现有服务
pkill -f "uvicorn"
pkill -f "celery"

# 启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# 启动Celery Worker
celery -A app.core.celery.celery_app worker --loglevel=info &
```

### 5. 验证部署

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 预期响应：
# {
#   "status": "healthy",
#   "features": {
#     "rate_limiting": true,
#     ...
#   }
# }

# 2. 测试SSRF防护
curl -X POST http://localhost:8000/api/v1/api-security/scans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "SSRF Test",
    "target_url": "http://192.168.1.1"
  }'

# 预期：400 Bad Request
# {"detail": "Invalid target URL: Private IP addresses are not allowed"}

# 3. 测试速率限制
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/api-security/scans \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -d '{"name": "Test'$i'", "target_url": "https://www.baidu.com"}'
  echo ""
done

# 预期：前5个成功，第6个返回 429 Too Many Requests
```

---

## 完整部署步骤（生产环境）

### 步骤1：代码审查

```bash
# 查看所有修改
git diff HEAD~1

# 关键文件检查清单
- backend/app/core/url_validator.py  # 新文件
- backend/app/api/endpoints/api_security.py
- backend/app/api/services/js_extractor.py
- backend/app/api/services/api_security_scanner.py
- backend/app/api/models/api_security.py
- backend/requirements/base.txt
```

### 步骤2：备份数据库

```bash
# 备份PostgreSQL数据库
docker exec soc_postgres pg_dump -U soc_user soc_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用脚本
./scripts/backup_database.sh
```

### 步骤3：在测试环境验证

```bash
# 1. 在测试环境部署
export ENVIRONMENT=staging

# 2. 运行测试套件（如果有）
cd backend
pytest tests/ -v

# 3. 手动测试关键功能
# - 创建扫描任务
# - 检查速率限制
# - 验证SSRF防护
```

### 步骤4：生产环境部署

```bash
# 1. 设置维护模式（可选）
# 在前端显示维护页面

# 2. 拉取最新代码
git pull origin main

# 3. 安装依赖
cd backend
pip install -r requirements/base.txt

# 4. 运行数据库迁移
alembic upgrade head

# 5. 重启服务
docker-compose -f docker-compose.full.yml restart backend celery_worker

# 6. 验证部署
curl http://localhost:8000/health

# 7. 监控日志
docker-compose -f docker-compose.full.yml logs -f backend
```

### 步骤5：监控和回滚计划

```bash
# 监控关键指标
watch -n 5 'curl -s http://localhost:8000/metrics | grep -E "(request_count|error_rate|response_time)"'

# 如果出现问题，回滚步骤：
# 1. 停止服务
docker-compose -f docker-compose.full.yml stop backend celery_worker

# 2. 回滚代码
git reset --hard HEAD~1

# 3. 回滚数据库
alembic downgrade -1

# 4. 重启服务
docker-compose -f docker-compose.full.yml start backend celery_worker
```

---

## 常见问题排查

### 问题1：速率限制不工作

**症状**：可以无限创建扫描任务

**诊断**：
```bash
# 检查Redis连接
docker exec soc_redis redis-cli -a redis_password_2024 ping
# 预期：PONG

# 检查配置
grep RATE_LIMIT .env
# 预期：RATE_LIMIT_ENABLED=true
```

**解决**：
```bash
# 确保Redis运行
docker-compose -f docker-compose.full.yml restart redis

# 检查后端日志
docker logs soc_backend | grep "Rate"
```

---

### 问题2：URL验证器阻止了合法网站

**症状**：提示 "Invalid target URL"

**诊断**：
```bash
# 检查URL解析
python3 << EOF
from backend.app.core.url_validator import url_validator
try:
    url_validator.validate("https://your-website.com")
    print("✓ Valid")
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

**解决**：
- 如果是内网测试环境，修改 `url_validator.py:44`：
  ```python
  url_validator = URLValidator(allow_internal=True)  # 仅开发环境
  ```
- 生产环境保持 `allow_internal=False`

---

### 问题3：数据库迁移失败

**症状**：`alembic upgrade head` 报错

**常见错误1**：外键约束冲突

```bash
# 错误：violates foreign key constraint

# 原因：数据库中存在孤儿记录
# 解决：清理孤儿记录
docker exec -it soc_postgres psql -U soc_user -d soc_platform

-- 查找孤儿记录
SELECT * FROM api_endpoints
WHERE scan_task_id NOT IN (SELECT id FROM api_scan_tasks);

-- 删除孤儿记录
DELETE FROM api_endpoints
WHERE scan_task_id NOT IN (SELECT id FROM api_scan_tasks);

-- 重新运行迁移
alembic upgrade head
```

**常见错误2**：Alembic未初始化

```bash
# 错误：alembic: command not found

# 解决：初始化Alembic
cd backend
alembic init alembic

# 配置 alembic.ini
# sqlalchemy.url = postgresql+asyncpg://soc_user:soc_password_2024@localhost:5432/soc_platform

# 重新创建迁移
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

### 问题4：性能没有提升

**症状**：扫描速度仍然很慢

**诊断**：
```bash
# 检查并发配置
grep max_concurrent backend/app/api/services/api_security_scanner.py

# 预期：max_concurrent = self.config.get('max_concurrent_requests', 10)
```

**解决**：
```bash
# 在扫描配置中增加并发数
curl -X POST http://localhost:8000/api/v1/api-security/scans \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Fast Scan",
    "target_url": "https://example.com",
    "scan_config": {
      "max_concurrent_requests": 20  // 增加到20
    }
  }'
```

---

## 性能调优建议

### 1. 调整并发数

根据服务器配置调整：

```python
# backend/app/api/services/api_security_scanner.py:370
max_concurrent = self.config.get('max_concurrent_requests', 10)

# 建议值：
# - 1核CPU: 5
# - 2核CPU: 10
# - 4核CPU: 20
# - 8核CPU: 40
```

### 2. 调整连接池

```python
# backend/app/api/services/api_security_scanner.py:378
limits=httpx.Limits(
    max_keepalive_connections=20,  # 根据max_concurrent调整
    max_connections=50
)
```

### 3. 调整速率限制

```bash
# .env
RATE_LIMIT_PER_MINUTE=100  # 根据实际负载调整

# 或针对特定端点
# backend/app/api/endpoints/api_security.py:43
@custom_rate_limit("10/minute")  # 调整为10个/分钟
```

---

## 监控指标

### 关键指标

1. **安全指标**
   - SSRF尝试次数（应被阻止）
   - 速率限制触发次数
   - SSL验证失败次数

2. **性能指标**
   - API扫描平均耗时
   - 并发请求数
   - 响应时间百分位（P50, P95, P99）

3. **系统指标**
   - CPU使用率
   - 内存使用率
   - 网络带宽

### Prometheus配置（可选）

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'soc_backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## 回滚计划

如果部署后出现严重问题，按以下步骤回滚：

### 快速回滚（5分钟）

```bash
# 1. 切换到上一个稳定版本
git checkout <previous_commit>

# 2. 回滚数据库
alembic downgrade -1

# 3. 重启服务
docker-compose -f docker-compose.full.yml restart backend celery_worker
```

### 完整回滚（15分钟）

```bash
# 1. 停止服务
docker-compose -f docker-compose.full.yml stop

# 2. 恢复数据库备份
docker exec -i soc_postgres psql -U soc_user -d soc_platform < backup_20250110_120000.sql

# 3. 切换代码
git checkout <stable_tag>

# 4. 重新构建
docker-compose -f docker-compose.full.yml build

# 5. 启动服务
docker-compose -f docker-compose.full.yml up -d

# 6. 验证
curl http://localhost:8000/health
```

---

## 联系支持

如遇到无法解决的问题：

1. 查看完整日志：
   ```bash
   docker-compose -f docker-compose.full.yml logs --tail=1000 > logs.txt
   ```

2. 收集系统信息：
   ```bash
   docker-compose -f docker-compose.full.yml ps
   docker stats --no-stream
   ```

3. 提交Issue到GitHub，附带：
   - 错误日志
   - 系统信息
   - 复现步骤

---

**部署完成后，请参考 `docs/SECURITY_FIXES_SUMMARY.md` 查看详细的修复说明和测试验证方法。**
