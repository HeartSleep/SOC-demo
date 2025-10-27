# API安全检测功能使用文档

## 概述

基于文章《黑盒视角下的API安全检测》实现的API安全扫描功能，采用 **"传统代码 + AI协同"** 的混合架构。

## 功能特性

### 1. JS资源提取
- ✅ 静态JS资源提取（`<script>`标签）
- ✅ 动态JS资源提取（Vue/React/Angular）
- ✅ Webpack打包资源解析
- ✅ 适配主流前端框架

### 2. API发现
采用文章中的**API分层架构**：
```
完整API = 基础URL + 基础API路径 + API路径
例: https://xxx.com + /api + /user/getInfo
```

- ✅ 静态API提取（正则表达式）
- ✅ 动态API识别（字符串拼接、模板字符串）
- ✅ 基础API路径自动识别
- ✅ AI辅助分析（预留接口）

### 3. 微服务架构识别
- ✅ 自动识别服务路径（如/user, /admin）
- ✅ 按服务分组API
- ✅ 技术栈检测
- ✅ 组件漏洞扫描（SpringBoot Actuator等）

### 4. API未授权访问检测
采用文章中的**多层过滤机制**：
- ✅ 传统代码过滤404接口
- ✅ AI站点定性分析（预留）
- ✅ AI接口登录需求判断（预留）
- ✅ AI公共接口识别（预留）

### 5. 敏感信息匹配
- ✅ 正则匹配敏感信息（密钥、手机号、邮箱等）
- ✅ JS文件敏感信息检测
- ✅ API响应敏感信息检测
- ✅ AI辅助识别（预留）

## 文件结构

```
backend/app/api/
├── models/
│   └── api_security.py          # 数据模型
├── schemas/
│   └── api_security.py          # Pydantic Schema
└── services/
    ├── js_extractor.py          # JS资源提取服务
    ├── api_discovery.py         # API发现服务
    └── api_security_scanner.py  # API安全扫描主服务
```

## 数据模型

### 1. APIScanTask - 扫描任务
```python
- id: UUID
- name: 任务名称
- target_url: 目标URL
- status: 任务状态（pending/running/completed/failed）
- scan_config: 扫描配置
- 统计信息: JS文件数、API数、服务数、问题数
```

### 2. JSResource - JS资源
```python
- id: UUID
- scan_task_id: 关联任务
- url: JS文件URL
- content: 文件内容
- extraction_method: 提取方法（static/webpack/vue/react）
```

### 3. APIEndpoint - API接口
```python
- id: UUID
- scan_task_id: 关联任务
- base_url: 基础URL
- base_api_path: 基础API路径
- service_path: 服务路径
- api_path: API路径
- full_url: 完整URL
- status_code: 响应状态码
- requires_auth: 是否需要认证
- is_public_api: 是否为公共接口
```

### 4. MicroserviceInfo - 微服务信息
```python
- id: UUID
- scan_task_id: 关联任务
- service_name: 服务名称
- service_full_path: 服务完整路径
- detected_technologies: 检测到的技术栈
- has_vulnerabilities: 是否有漏洞
- vulnerability_details: 漏洞详情
```

### 5. APISecurityIssue - 安全问题
```python
- id: UUID
- scan_task_id: 关联任务
- title: 问题标题
- description: 问题描述
- issue_type: 问题类型（unauthorized_access/sensitive_data_leak等）
- severity: 严重程度（critical/high/medium/low）
- evidence: 证据
```

## 使用示例

### 基本使用

```python
from app.api.services.api_security_scanner import APISecurityScanner

# 创建扫描器
scanner = APISecurityScanner(config={'use_ai': True})

# 配置扫描
scan_config = {
    "enable_js_extraction": True,
    "enable_api_discovery": True,
    "enable_microservice_detection": True,
    "enable_unauthorized_check": True,
    "enable_sensitive_info_check": True,
    "max_js_files": 100,
}

# 执行扫描
result = await scanner.scan(
    target_url="https://example.com",
    scan_config=scan_config
)

# 查看结果
print(f"发现 {len(result['js_resources'])} 个JS文件")
print(f"发现 {len(result['apis'])} 个API")
print(f"识别 {len(result['microservices'])} 个微服务")
print(f"发现 {len(result['security_issues'])} 个安全问题")
```

### 扫描结果结构

```json
{
  "target_url": "https://example.com",
  "status": "completed",
  "start_time": "2025-10-11T12:00:00",
  "end_time": "2025-10-11T12:05:00",

  "js_resources": [
    {
      "url": "https://example.com/static/js/app.js",
      "file_name": "app.js",
      "file_size": 102400,
      "extraction_method": "webpack"
    }
  ],

  "apis": [
    {
      "base_url": "https://example.com",
      "base_api_path": "/api",
      "service_path": "/user",
      "api_path": "/getInfo",
      "full_url": "https://example.com/api/user/getInfo",
      "http_method": "GET",
      "status_code": 200
    }
  ],

  "microservices": [
    {
      "service_name": "/user",
      "service_full_path": "https://example.com/api/user",
      "total_endpoints": 10,
      "detected_technologies": ["SpringBoot", "FastJSON"],
      "has_vulnerabilities": true,
      "vulnerability_details": [
        {
          "type": "SpringBoot Actuator Exposed",
          "severity": "high"
        }
      ]
    }
  ],

  "security_issues": [
    {
      "type": "unauthorized_access",
      "severity": "high",
      "title": "API未授权访问: /api/admin/users",
      "description": "该API无需登录即可访问，且不是公共接口",
      "evidence": {...}
    },
    {
      "type": "sensitive_data_leak",
      "severity": "high",
      "title": "JS文件敏感信息泄露",
      "evidence": {
        "sensitive_data": [
          {"type": "accesskey", "count": 1}
        ]
      }
    }
  ],

  "statistics": {
    "total_js_files": 50,
    "total_apis": 120,
    "total_microservices": 5,
    "total_issues": 23,
    "issues_by_severity": {
      "critical": 2,
      "high": 8,
      "medium": 10,
      "low": 3
    }
  }
}
```

## 与文章对照

| 文章功能 | 实现情况 | 说明 |
|---------|---------|------|
| JS资源提取 | ✅ 已实现 | `js_extractor.py` - 支持静态、动态、Webpack |
| API发现 | ✅ 已实现 | `api_discovery.py` - 支持分层架构、动态拼接 |
| 微服务识别 | ✅ 已实现 | `api_security_scanner.py` - 按service_path分组 |
| 未授权访问检测 | ✅ 已实现 | 传统过滤 + AI预留接口 |
| 敏感信息匹配 | ✅ 已实现 | 正则匹配 + AI预留接口 |
| AI技术 | ⏳ 预留接口 | 需要集成实际AI服务（Claude API等） |

## AI集成说明

当前代码中AI功能为**预留接口**，需要集成实际的AI服务（如Claude API）。

需要实现的AI方法：
1. `_ai_extract_base_api_paths()` - AI提取基础API路径
2. `_ai_extract_api_paths()` - AI提取API路径（动态拼接）
3. `_ai_analyze_site()` - AI站点定性
4. `_ai_check_requires_login()` - AI判断是否需要登录
5. `_ai_check_is_public_api()` - AI判断是否为公共接口

### AI集成示例（以Claude API为例）

```python
async def _ai_extract_api_paths(self, content: str) -> List[str]:
    """AI提取API路径"""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""
    请分析以下JavaScript代码，提取其中的API路径。
    特别注意动态拼接的API路径，例如:
    - const api = baseUrl + '/user/' + userId
    - `${{API_PREFIX}}/admin/users`

    完整API构成: 基础URL + 基础API路径 + API路径
    请只返回API路径部分，以JSON数组格式返回。

    JavaScript代码:
    {content[:5000]}  # 限制长度
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    # 解析AI响应
    api_paths = json.loads(response.content[0].text)
    return api_paths
```

## 下一步工作

1. **集成数据库** - 将扫描结果保存到数据库
2. **创建API端点** - 提供HTTP API接口
3. **创建Celery任务** - 支持异步扫描
4. **集成AI服务** - 实现AI辅助分析
5. **前端界面** - 创建扫描任务管理界面
6. **数据迁移** - 运行`alembic`创建数据表

## 技术亮点

1. **API分层架构** - 完全按照文章设计实现
2. **传统代码 + AI协同** - 预留AI接口，易于扩展
3. **微服务架构识别** - 自动识别不同服务
4. **多层过滤机制** - 减少误报
5. **组件漏洞检测** - 支持SpringBoot Actuator等
6. **异步处理** - 使用asyncio提高性能

## 参考文章

《黑盒视角下的API安全检测》
- 文章核心思想：传统代码 + AI协同
- API分层：基础URL + 基础API路径 + API路径
- 多层过滤：传统过滤 + AI研判
- 实际效果：153个站点，发现23个真实有效问题
