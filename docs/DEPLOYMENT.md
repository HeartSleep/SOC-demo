# SOC 企业级网络安全测试扫描平台

## 项目概述

SOC (Security Operations Center) 是一个企业级网络安全测试扫描平台，实现从资产发现到漏洞检测的完整安全测试流程。该平台采用现代化的微服务架构，提供Web界面和API接口，支持大规模并发扫描和自动化安全测试。

## 系统架构

### 技术栈

**后端技术栈：**
- **框架**: Python FastAPI + Uvicorn
- **数据库**: MongoDB (主数据存储) + Redis (缓存/队列)
- **任务队列**: Celery + Redis
- **认证**: JWT + RBAC权限控制
- **文档**: Swagger/OpenAPI 自动生成

**前端技术栈：**
- **框架**: Vue.js 3 + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts + Vue-ECharts
- **工具库**: Axios, Lodash, Day.js

**容器化：**
- **容器**: Docker + Docker Compose
- **Web服务器**: Nginx (生产环境)
- **监控**: 日志收集与分析

### 系统组件

1. **Web API服务** - FastAPI后端服务，提供REST API
2. **任务队列服务** - Celery Worker进程，处理异步任务
3. **调度服务** - Celery Beat，定时任务调度
4. **前端服务** - Vue.js应用，用户界面
5. **数据库服务** - MongoDB，数据存储
6. **缓存服务** - Redis，缓存和消息队列

## 核心功能模块

### 1. 用户管理与权限控制
- **多级角色权限**: Admin, Security_Analyst, Operator, Viewer
- **JWT认证**: 安全的token认证机制
- **RBAC权限模型**: 细粒度权限控制
- **用户会话管理**: 登录状态跟踪，失败锁定

### 2. 资产发现与管理
- **多类型资产**: 域名、IP、URL、端口等
- **批量导入**: 支持CSV、JSON、XML格式
- **自动发现**: 基于FOFA搜索引擎的资产发现
- **标签分类**: 灵活的资产分类和标记
- **关联分析**: 资产之间的关联关系

### 3. 扫描任务管理
- **多种扫描类型**:
  - 端口扫描 (Nmap集成)
  - 子域名枚举
  - Web应用发现
  - 漏洞扫描
  - SSL/TLS检测
- **任务调度**: 即时执行、定时执行、周期执行
- **并发控制**: 可配置的并发扫描数量
- **结果存储**: 结构化存储扫描结果

### 4. 漏洞检测引擎
- **DAST动态扫描**:
  - Nuclei引擎集成
  - Xray扫描器支持
  - 自研POC框架
- **漏洞验证**: 自动/手动漏洞验证
- **误报处理**: 漏洞确认和误报标记
- **风险评估**: CVSS评分和风险等级

### 5. 报告生成系统
- **多格式支持**: PDF, HTML, Excel, JSON
- **模板系统**: 可自定义报告模板
- **定时生成**: 周期性报告生成
- **邮件发送**: 报告自动邮件分发

### 6. Web应用发现
- **HTTP侦察**: 响应头分析、技术栈识别
- **路径发现**: 目录/文件模糊测试
- **截图捕获**: 自动页面截图 (Playwright)
- **技术检测**: 框架、CMS、库版本识别

## 安装部署

### 环境要求

**系统要求：**
- 操作系统: Linux (推荐Ubuntu 20.04+)
- 内存: 至少8GB (推荐16GB+)
- 存储: 至少50GB可用空间
- 网络: 互联网连接

**软件依赖：**
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nmap (用于端口扫描)

### 快速部署 (Docker Compose)

1. **克隆项目**
```bash
git clone <repository-url>
cd SOC
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库密码、API密钥等
```

3. **启动服务**
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

4. **初始化数据**
```bash
# 进入后端容器
docker-compose exec backend bash

# 创建管理员用户
python scripts/create_admin.py
```

5. **访问系统**
- Web界面: http://localhost (前端)
- API文档: http://localhost:8000/docs (后端Swagger)

### 开发环境部署

**后端开发环境：**
```bash
cd backend

# 创建Python虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements/dev.txt

# 启动MongoDB和Redis
docker-compose -f docker-compose.dev.yml up -d mongodb redis

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker (新终端)
celery -A app.core.celery.celery_app worker --loglevel=info

# 启动Celery Beat (新终端)
celery -A app.core.celery.celery_app beat --loglevel=info
```

**前端开发环境：**
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 配置说明

### 主要配置文件

1. **后端配置** (`backend/app/core/config.py`)
   - 数据库连接
   - Redis配置
   - 安全设置
   - 外部API配置

2. **前端配置** (`frontend/vite.config.ts`)
   - 开发服务器设置
   - 代理配置
   - 构建选项

3. **Docker配置** (`docker-compose.yml`)
   - 服务定义
   - 网络配置
   - 卷挂载

### 关键环境变量

```bash
# 数据库配置
MONGODB_URL=mongodb://admin:password@mongodb:27017/soc_platform?authSource=admin
REDIS_URL=redis://:password@redis:6379/0

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# FOFA API配置 (可选)
FOFA_API_EMAIL=your_email@example.com
FOFA_API_KEY=your_fofa_api_key

# 扫描配置
MAX_CONCURRENT_SCANS=10
SCAN_TIMEOUT=300
```

## API文档

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/register` - 用户注册 (管理员)

### 资产管理接口
- `GET /api/v1/assets` - 获取资产列表
- `POST /api/v1/assets` - 创建资产
- `GET /api/v1/assets/{id}` - 获取资产详情
- `PUT /api/v1/assets/{id}` - 更新资产
- `DELETE /api/v1/assets/{id}` - 删除资产
- `POST /api/v1/assets/bulk` - 批量创建资产
- `POST /api/v1/assets/import` - 导入资产文件

### 任务管理接口
- `GET /api/v1/tasks` - 获取任务列表
- `POST /api/v1/tasks` - 创建扫描任务
- `GET /api/v1/tasks/{id}` - 获取任务详情
- `POST /api/v1/tasks/{id}/execute` - 执行任务
- `POST /api/v1/tasks/{id}/cancel` - 取消任务

### 漏洞管理接口
- `GET /api/v1/vulnerabilities` - 获取漏洞列表
- `POST /api/v1/vulnerabilities` - 创建漏洞
- `GET /api/v1/vulnerabilities/{id}` - 获取漏洞详情
- `PUT /api/v1/vulnerabilities/{id}` - 更新漏洞
- `POST /api/v1/vulnerabilities/{id}/verify` - 验证漏洞

### 报告管理接口
- `GET /api/v1/reports` - 获取报告列表
- `POST /api/v1/reports` - 生成报告
- `GET /api/v1/reports/{id}` - 获取报告详情
- `GET /api/v1/reports/{id}/download` - 下载报告文件

### 权限说明

所有API接口都需要相应权限：
- `asset:read/create/update/delete` - 资产相关权限
- `task:read/create/execute/delete` - 任务相关权限
- `vulnerability:read/create/update/verify` - 漏洞相关权限
- `report:read/create/generate` - 报告相关权限

## 使用指南

### 1. 首次使用

1. **创建管理员账户**
```bash
# 进入后端容器
docker-compose exec backend python scripts/create_admin.py
```

2. **登录系统**
   - 访问 http://localhost
   - 使用管理员账户登录

3. **添加资产**
   - 进入资产管理页面
   - 手动添加或批量导入资产

### 2. 扫描任务创建

1. **选择扫描类型**
   - 端口扫描: 发现开放端口和服务
   - Web发现: 发现Web应用和技术栈
   - 漏洞扫描: 使用Nuclei/Xray检测漏洞

2. **配置扫描参数**
   - 目标资产: 选择要扫描的资产
   - 扫描配置: 超时时间、并发数等
   - 调度设置: 立即执行或定时执行

3. **监控执行过程**
   - 查看任务状态和进度
   - 实时日志输出
   - 结果预览

### 3. 漏洞管理

1. **漏洞分类**
   - 按严重程度分类 (Critical/High/Medium/Low)
   - 按漏洞类型分类 (SQL注入/XSS/RCE等)
   - 按状态分类 (新发现/已确认/已修复等)

2. **漏洞处理流程**
   - 漏洞发现 → 初步分析 → 漏洞验证 → 修复建议 → 复测 → 关闭

3. **风险评估**
   - CVSS评分
   - 业务影响分析
   - 修复优先级

### 4. 报告生成

1. **报告类型**
   - 漏洞报告: 详细的漏洞信息和修复建议
   - 资产清单: 资产发现和分类报告
   - 扫描总结: 扫描活动汇总报告

2. **自定义配置**
   - 筛选条件: 时间范围、严重程度等
   - 输出格式: PDF、HTML、Excel
   - 模板选择: 技术报告、管理报告

## 高级配置

### 扩展扫描引擎

1. **集成新的扫描器**
```python
# 在 app/api/services/ 中创建新的扫描器服务
class CustomScanner:
    def __init__(self):
        self.scanner_path = "/path/to/scanner"

    async def scan(self, targets, config):
        # 实现扫描逻辑
        pass
```

2. **注册Celery任务**
```python
# 在 app/core/celery/tasks/ 中创建任务
@celery_app.task(bind=True)
def custom_scan_task(self, task_id, targets, config):
    scanner = CustomScanner()
    return scanner.scan(targets, config)
```

### 性能优化

1. **数据库优化**
   - 合理设置索引
   - 配置连接池
   - 使用读写分离

2. **缓存策略**
   - Redis缓存频繁查询
   - API响应缓存
   - 静态文件缓存

3. **并发控制**
   - 调整Celery Worker数量
   - 配置扫描并发限制
   - 实现熔断机制

### 监控告警

1. **系统监控**
   - CPU、内存、磁盘使用率
   - 数据库连接数
   - API响应时间

2. **业务监控**
   - 扫描任务执行情况
   - 漏洞发现趋势
   - 用户活跃度

3. **告警通知**
   - 邮件通知
   - 钉钉/企业微信
   - Slack集成

## 安全注意事项

### 1. 访问控制
- 严格的RBAC权限控制
- API访问限流
- 网络访问白名单

### 2. 数据安全
- 敏感数据加密存储
- 传输加密 (HTTPS)
- 定期备份

### 3. 扫描安全
- 扫描目标授权确认
- 扫描频率限制
- 避免对生产环境的影响

### 4. 日志审计
- 完整的操作日志
- 敏感操作审计
- 异常行为监控

## 故障排除

### 常见问题

1. **服务启动失败**
```bash
# 检查容器状态
docker-compose ps

# 查看错误日志
docker-compose logs <service-name>

# 重启服务
docker-compose restart <service-name>
```

2. **数据库连接错误**
   - 检查MongoDB服务状态
   - 验证连接字符串
   - 检查网络连通性

3. **扫描任务异常**
   - 检查Celery Worker状态
   - 查看任务队列堆积情况
   - 验证扫描器工具安装

4. **前端页面无法访问**
   - 检查Nginx配置
   - 验证后端API连接
   - 查看浏览器控制台错误

### 日志位置

- **应用日志**: `data/logs/app.log`
- **Celery日志**: 通过 `docker-compose logs celery_worker`
- **Nginx日志**: 容器内 `/var/log/nginx/`
- **MongoDB日志**: 通过 `docker-compose logs mongodb`

## 项目结构

```
SOC/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API接口层
│   │   │   ├── endpoints/     # API端点
│   │   │   ├── models/        # 数据模型
│   │   │   ├── schemas/       # Pydantic模式
│   │   │   ├── services/      # 业务服务
│   │   │   └── utils/         # 工具函数
│   │   ├── core/              # 核心配置
│   │   │   ├── celery/        # Celery配置和任务
│   │   │   ├── config.py      # 应用配置
│   │   │   ├── database.py    # 数据库配置
│   │   │   ├── deps.py        # 依赖注入
│   │   │   ├── logging.py     # 日志配置
│   │   │   ├── permissions.py # 权限管理
│   │   │   └── security.py    # 安全配置
│   │   └── main.py            # 应用入口
│   ├── requirements/          # 依赖管理
│   ├── scripts/               # 工具脚本
│   ├── tests/                 # 测试代码
│   └── Dockerfile             # 后端Dockerfile
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── api/               # API调用
│   │   ├── components/        # Vue组件
│   │   ├── composables/       # 组合式函数
│   │   ├── layout/            # 布局组件
│   │   ├── pages/             # 页面组件
│   │   ├── router/            # 路由配置
│   │   ├── store/             # 状态管理
│   │   ├── styles/            # 样式文件
│   │   ├── utils/             # 工具函数
│   │   ├── views/             # 视图页面
│   │   ├── App.vue            # 根组件
│   │   └── main.ts            # 应用入口
│   ├── public/                # 静态资源
│   ├── Dockerfile             # 前端Dockerfile
│   ├── nginx.conf             # Nginx配置
│   ├── package.json           # 依赖管理
│   └── vite.config.ts         # Vite配置
├── docker/                     # Docker配置
├── docs/                       # 项目文档
├── scripts/                    # 部署脚本
├── tools/                      # 外部工具
├── data/                       # 数据目录
├── docker-compose.yml          # 容器编排
├── .env.example                # 环境变量模板
└── README.md                   # 项目说明
```

## 贡献指南

### 开发流程

1. Fork项目仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

### 代码规范

**Python后端:**
- 遵循PEP 8编码规范
- 使用类型注解
- 编写单元测试
- 添加详细的docstring

**TypeScript前端:**
- 使用ESLint和Prettier
- 遵循Vue.js最佳实践
- 组件化开发
- 响应式设计

### 提交规范

使用约定式提交格式:
```
type(scope): description

feat(assets): add bulk import functionality
fix(auth): resolve login token expiration issue
docs(api): update authentication documentation
```

## 版本历史

### v1.0.0 (当前版本)
- 完整的资产管理功能
- 多种扫描引擎集成
- 漏洞管理和报告生成
- RBAC权限控制系统
- Docker容器化部署

### 后续版本规划
- v1.1.0: 增强的Web应用测试
- v1.2.0: 移动端适配
- v1.3.0: 威胁情报集成
- v2.0.0: 分布式扫描集群

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]
- 文档站点: [Documentation]
- 技术支持: [Support Email]

---

**重要提醒**:
1. 本系统仅用于授权的安全测试，禁止用于恶意攻击
2. 使用前请确保有目标系统的合法测试授权
3. 遵守相关法律法规，合理使用安全测试工具
4. 定期更新系统组件，保持安全防护水平