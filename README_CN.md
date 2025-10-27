# SOC 安全运营中心平台

<div align="center">
  <h1>🛡️ SOC Security Platform</h1>
  <p>企业级安全运营中心管理平台</p>

  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Vue.js-3.0-brightgreen)](https://vuejs.org/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-blue)](https://www.postgresql.org/)
  [![Redis](https://img.shields.io/badge/Redis-6%2B-red)](https://redis.io/)
</div>

---

## 📖 项目简介

SOC安全运营中心平台是一个功能完善的企业级安全管理解决方案，专为安全团队设计，用于集中管理、监控和响应安全事件。该平台集成了多种业界领先的安全扫描工具，提供了从资产发现到漏洞管理的完整工作流程。

### 🌟 核心特性

- **🔍 资产管理**: 自动化资产发现、分类和持续监控
- **🚨 漏洞扫描**: 集成Nuclei、Nmap、OWASP ZAP等专业工具
- **📊 威胁情报**: 实时威胁情报收集与关联分析
- **🎯 事件响应**: 完整的事件响应工作流和自动化处置
- **📈 合规审计**: 支持GDPR、HIPAA、PCI-DSS、SOC2等标准
- **🔐 安全加固**: 内置多层安全防护机制
- **📱 实时告警**: WebSocket实时推送，多渠道告警通知
- **📋 报告生成**: 自动化漏洞报告和管理层报告

## 🚀 一键部署

### 快速开始

```bash
# 克隆项目
git clone https://github.com/your-org/soc-platform.git
cd soc-platform

# 执行一键部署脚本（需要root权限）
sudo chmod +x deploy_production.sh
sudo ./deploy_production.sh
```

**就这么简单！** 🎉 脚本会自动完成所有配置和依赖安装。

### 部署脚本功能

一键部署脚本会自动完成以下操作：

1. ✅ 检测操作系统（支持Ubuntu/Debian/CentOS/RHEL）
2. ✅ 安装所有系统依赖
3. ✅ 配置PostgreSQL数据库
4. ✅ 配置Redis缓存
5. ✅ 安装安全扫描工具（Nuclei、Nmap、ZAP等）
6. ✅ 设置Python和Node.js环境
7. ✅ 配置Nginx反向代理
8. ✅ 申请Let's Encrypt SSL证书
9. ✅ 配置防火墙规则
10. ✅ 设置Fail2ban防护
11. ✅ 创建系统服务
12. ✅ 初始化管理员账户

## 💻 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端展示层                           │
│         Vue 3 + Element Plus + ECharts                  │
└────────────────────────┬───────���────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                     API网关层                            │
│              Nginx (反向代理 + 负载均衡)                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    应用服务层                            │
│     FastAPI + SQLAlchemy + Celery + WebSocket          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                    数据存储层                            │
│         PostgreSQL (主库) + Redis (缓存/队列)           │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│                  安全扫描工具层                          │
│    Nuclei + Nmap + OWASP ZAP + Metasploit + 自定义     │
└──────────────────────────────────────────────────────────┘
```

## 🔧 技术栈

### 后端技术
- **框架**: FastAPI (高性能异步Web框架)
- **ORM**: SQLAlchemy (支持异步)
- **认证**: JWT + OAuth2
- **任务队列**: Celery + Redis
- **WebSocket**: 实时通信
- **API文档**: Swagger/ReDoc

### 前端技术
- **框架**: Vue 3 (Composition API)
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **构建工具**: Vite
- **类型检查**: TypeScript

### 基础设施
- **数据库**: PostgreSQL 13+
- **缓存**: Redis 6+
- **Web服务器**: Nginx
- **进程管理**: Systemd
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack (可选)

### 安全工具集成
- **Nuclei**: 基于模板的漏洞扫描器（5000+检测规则）
- **Nmap**: 网络发现和端口扫描
- **OWASP ZAP**: Web应用安全测试
- **Metasploit**: 渗透测试框架
- **SQLMap**: SQL注入检测
- **Hydra**: 密码爆破工具
- **Amass/Subfinder**: 子域名枚举

## 📦 功能模块

### 1. 资产管理模块
- 🖥️ 自动化资产发现
- 🏷️ 资产分类和标签
- 📍 网络拓扑映射
- 🔄 实时状态监控
- 📊 资产统计分析

### 2. 漏洞管理模块
- 🔍 多引擎扫描
- 🎯 漏洞优先级排序
- 📈 CVSS评分
- 🔧 修复建议
- 📅 修复跟踪

### 3. 安全扫描模块
- 🌐 Web应用扫描
- 🖧 网络扫描
- 🔐 配置审计
- 📱 API安全测试
- 🐳 容器安全扫描

### 4. 威胁情报模块
- 🌍 威胁情报收集
- 🔗 IOC关联分析
- 📡 威胁源订阅
- 🚨 自动告警
- 📊 威胁趋势分析

### 5. 事件响应模块
- 📝 事件工单管理
- 🔄 响应流程自动化
- 👥 团队协作
- 📈 响应时效统计
- 📚 知识库集成

### 6. 合规管理模块
- ✅ 合规性检查
- 📋 审计报告
- 🔍 证据收集
- 📊 合规仪表板
- 🎯 整改跟踪

### 7. 报告中心
- 📊 可视化报告
- 📈 趋势分析
- 📑 自定义模板
- 📧 定时发送
- 📥 多格式导出

## 🔐 安全特性

### 认证与授权
- 🔑 JWT令牌认证
- 🔐 多因素认证(MFA)
- 👥 基于角色的访问控制(RBAC)
- 🔄 Token自动刷新
- 📝 审计日志

### 安全防护
- 🛡️ CSRF防护
- 🚫 SQL注入防护
- 🔒 XSS防护
- ⚡ DDoS防护
- 🔐 API速率限制

### 数据���全
- 🔐 密码加密存储(bcrypt)
- 🔑 敏感数据加密
- 🔒 SSL/TLS传输加密
- 💾 加密备份
- 🗑️ 安全删除

## 📋 安装要求

### 最低配置
- **CPU**: 4核
- **内存**: 8GB RAM
- **存储**: 100GB SSD
- **系统**: Ubuntu 20.04+ / Debian 10+ / CentOS 8+

### 推荐配置
- **CPU**: 8核
- **内存**: 16GB RAM
- **存储**: 500GB SSD
- **系统**: Ubuntu 22.04 LTS

## 🛠️ 手动安装

如果您想要手动安装，请按照以下步骤操作：

### 1. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.9 python3-pip nodejs npm postgresql redis nginx

# CentOS/RHEL
sudo yum install -y python39 python39-pip nodejs postgresql-server redis nginx
```

### 2. 克隆项目

```bash
git clone https://github.com/your-org/soc-platform.git
cd soc-platform
```

### 3. 配置后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 生成生产配置
python ../scripts/generate_production_config.py

# 运行数据库迁移
alembic upgrade head
```

### 4. 配置前端

```bash
cd ../frontend
npm install
npm run build
```

### 5. 配置Nginx

```bash
sudo cp nginx.conf /etc/nginx/sites-available/soc-platform
sudo ln -s /etc/nginx/sites-available/soc-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 启动服务

```bash
# 启动后端
cd backend
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 启动Celery
celery -A app.core.celery.celery_app worker --loglevel=info

# 启动Celery Beat
celery -A app.core.celery.celery_app beat --loglevel=info
```

## 🔧 配置说明

### 环境变量配置

主要配置文件：`.env.production`

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/soc_platform

# Redis配置
REDIS_URL=redis://:password@localhost:6379/0

# 安全配置
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# 扫描工具路径
NUCLEI_PATH=/usr/local/bin/nuclei
NMAP_PATH=/usr/bin/nmap
```

### 扫描策略配置

```yaml
# config/scan_policy.yaml
scan_profiles:
  quick:
    - nuclei: critical,high
    - nmap: top-1000

  full:
    - nuclei: critical,high,medium,low
    - nmap: all-ports
    - zap: active-scan
```

## 📊 使用指南

### 初次登录

1. 访问 `https://your-domain.com`
2. 使用默认管理员账户登录：
   - 用户名：`admin`
   - 密码：`ChangeMeNow123!`
3. **立即修改默认密码！**

### 快速开始工作流

1. **添加资产** → 资产管理 → 添加资产
2. **执行扫描** → 安全扫描 → 新建扫描任务
3. **查看结果** → 漏洞管理 → 漏洞列表
4. **生成报告** → 报告中心 → 生成报告

### API使用

获取API文档：`https://your-domain.com/docs`

示例请求：
```python
import requests

# 认证
response = requests.post(
    "https://your-domain.com/api/v1/auth/login",
    json={"username": "admin", "password": "your-password"}
)
token = response.json()["access_token"]

# 获取资产列表
assets = requests.get(
    "https://your-domain.com/api/v1/assets",
    headers={"Authorization": f"Bearer {token}"}
)
print(assets.json())
```

## 🔄 更新升级

```bash
cd soc-platform
git pull origin main
sudo ./deploy_production.sh --upgrade
```

## 🐛 故障排除

### 常见问题

**Q: 无法访问Web界面**
```bash
# 检查服务状态
sudo systemctl status soc-backend
sudo systemctl status nginx

# 查看日志
sudo tail -f /var/log/soc-platform/app/error.log
```

**Q: 数据库连接失败**
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 测试连接
psql -U soc_prod_user -d soc_platform_prod -h localhost
```

**Q: 扫描任务失败**
```bash
# 检查Celery状态
sudo systemctl status soc-celery

# 查看Celery日志
sudo tail -f /var/log/soc-platform/app/celery.log
```

## 📈 性能优化

### 数据库优化
```sql
-- 创建索引
CREATE INDEX idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX idx_assets_type ON assets(type);

-- 定期维护
VACUUM ANALYZE;
```

### Redis优化
```bash
# 调整最大内存
redis-cli CONFIG SET maxmemory 4gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Nginx优化
```nginx
# 启用Gzip压缩
gzip on;
gzip_types text/plain application/json application/javascript;

# 配置缓存
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 开发环境搭建

```bash
# Fork项目并克隆
git clone https://github.com/your-username/soc-platform.git
cd soc-platform

# 创建开发分支
git checkout -b feature/your-feature

# 安装开发依赖
pip install -r requirements-dev.txt
npm install --save-dev

# 运行测试
pytest
npm run test
```

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 团队

- 架构设计：安全架构团队
- 前端开发：前端工程团队
- 后端开发：后端工程团队
- 安全工具：安全研究团队
- 运维支持：DevOps团队

## 📞 支持

- 📧 邮箱：support@soc-platform.com
- 💬 论坛：https://forum.soc-platform.com
- 📚 文档：https://docs.soc-platform.com
- 🐛 问题：https://github.com/your-org/soc-platform/issues

## 🙏 致谢

感谢以下开源项目的支持：

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [Nuclei](https://nuclei.projectdiscovery.io/)
- [OWASP ZAP](https://www.zaproxy.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

---

<div align="center">
  <p>用 ❤️ 构建，为安全而生</p>
  <p>© 2024 SOC Security Platform. All rights reserved.</p>
</div>