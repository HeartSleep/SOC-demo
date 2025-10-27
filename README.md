# SOC - 企业级网络安全测试扫描平台

## 项目概述

SOC是一个企业级网络安全测试扫描平台，实现从资产发现到漏洞检测的完整安全测试流程。

## 技术栈

### 后端
- Python FastAPI
- Celery 分布式任务队列
- MongoDB 主数据存储
- Redis 缓存/队列

### 前端
- Vue.js 3
- Element Plus
- TypeScript

### 容器化
- Docker
- Docker Compose

## 核心功能

### 1. 资产发现模块
- 域名管理系统（根域名→子域名拓展）
- DNS信息收集与月度存储
- FOFA搜索集成
- 端口扫描（Nmap集成）
- Web应用发现

### 2. 漏洞检测引擎
- DAST动态检测
- IAST交互检测
- SAST静态检测
- OOB检测

### 3. 流量处理与分析
- Burpsuite插件开发
- 域名碰撞（HostCollision）
- 流量管控系统

### 4. 运营管理系统
- 漏洞生命周期管理
- 自动化工作流
- 报告生成

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- MongoDB 4.4+
- Redis 6.0+

### 开发环境设置

1. 克隆项目
```bash
git clone <repository-url>
cd SOC
```

2. 启动开发环境
```bash
docker-compose -f docker/dev/docker-compose.yml up -d
```

3. 安装后端依赖
```bash
cd backend
pip install -r requirements/dev.txt
```

4. 安装前端依赖
```bash
cd frontend
npm install
```

5. 启动服务
```bash
# 后端
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm run dev

# Celery Worker
cd backend && celery -A app.core.celery.celery_app worker --loglevel=info
```

### 生产部署

```bash
docker-compose -f docker/prod/docker-compose.yml up -d
```

## 项目结构

```
SOC/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API接口
│   │   ├── core/              # 核心配置
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试代码
│   └── requirements/          # 依赖文件
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── api/               # API调用
│   │   ├── components/        # 组件
│   │   ├── pages/             # 页面
│   │   ├── router/            # 路由
│   │   └── store/             # 状态管理
│   └── public/                # 静态资源
├── docker/                     # Docker配置
│   ├── dev/                   # 开发环境
│   └── prod/                  # 生产环境
├── docs/                       # 文档
├── tools/                      # 工具集合
│   ├── burp-plugin/           # Burp插件
│   └── scanner-engines/       # 扫描引擎
└── data/                       # 数据目录
    ├── logs/                  # 日志
    ├── uploads/               # 上传文件
    └── reports/               # 报告
```

## API文档

启动服务后访问 http://localhost:8000/docs 查看Swagger文档

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License