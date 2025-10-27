# SOC 企业级网络安全测试扫描平台 - API 文档

## 概述

SOC平台提供完整的REST API接口，支持所有核心功能的程序化访问。所有API都遵循RESTful设计原则，使用JSON格式进行数据交换，支持JWT认证和基于角色的访问控制。

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### 1. 用户登录

**POST** `/auth/login`

```json
{
  "username": "admin",
  "password": "password"
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrator",
    "role": "admin",
    "permissions": ["asset:read", "asset:create", "..."]
  }
}
```

### 2. 获取当前用户信息

**GET** `/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**响应:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Administrator",
  "role": "admin",
  "permissions": ["asset:read", "asset:create", "..."],
  "last_login": "2024-01-15T10:30:00Z",
  "login_count": 15
}
```

## 资产管理

### 1. 获取资产列表

**GET** `/assets`

**查询参数:**
- `skip`: 跳过记录数 (默认: 0)
- `limit`: 返回记录数 (默认: 100, 最大: 1000)
- `asset_type`: 资产类型筛选
- `status`: 状态筛选
- `organization`: 组织筛选
- `tags`: 标签筛选 (逗号分隔)
- `criticality`: 重要性筛选

**响应:**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "example.com",
    "asset_type": "domain",
    "status": "active",
    "domain": "example.com",
    "organization": "Example Corp",
    "tags": ["web", "production"],
    "criticality": "high",
    "created_at": "2024-01-15T10:00:00Z",
    "last_seen": "2024-01-15T10:30:00Z"
  }
]
```

### 2. 创建资产

**POST** `/assets`

```json
{
  "name": "test.example.com",
  "asset_type": "domain",
  "domain": "test.example.com",
  "organization": "Example Corp",
  "owner": "Security Team",
  "tags": ["test", "staging"],
  "criticality": "medium",
  "notes": "Test environment"
}
```

### 3. 批量导入资产

**POST** `/assets/import`

**Form Data:**
- `file`: CSV/JSON/XML文件
- `auto_create_missing`: 自动创建缺失资产 (bool)
- `update_existing`: 更新现有资产 (bool)

**响应:**
```json
{
  "message": "Asset import started",
  "task_id": "abc123",
  "assets_count": 150,
  "filename": "assets.csv"
}
```

### 4. 资产发现

**POST** `/assets/discover`

```json
{
  "targets": ["example.com", "192.168.1.0/24"],
  "discovery_config": {
    "search_subdomains": true,
    "search_certificates": true,
    "max_results": 100
  }
}
```

## 扫描任务

### 1. 创建扫描任务

**POST** `/tasks`

```json
{
  "name": "Port Scan - example.com",
  "description": "Comprehensive port scan",
  "task_type": "port_scan",
  "priority": "normal",
  "target_domains": ["example.com"],
  "config": {
    "scan_type": "syn",
    "timing": "aggressive",
    "ports": "top1000",
    "version_detection": true,
    "os_detection": false
  },
  "schedule_type": "immediate",
  "tags": ["weekly-scan"]
}
```

**响应:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "name": "Port Scan - example.com",
  "task_type": "port_scan",
  "status": "running",
  "created_at": "2024-01-15T10:00:00Z",
  "celery_task_id": "xyz789"
}
```

### 2. 获取任务状态

**GET** `/tasks/{task_id}`

**响应:**
```json
{
  "id": "507f1f77bcf86cd799439012",
  "name": "Port Scan - example.com",
  "status": "completed",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:00Z",
  "execution_time": 300.5,
  "total_targets": 1,
  "processed_targets": 1,
  "success_count": 1,
  "error_count": 0,
  "results": [
    {
      "target": "example.com",
      "status": "success",
      "open_ports": [
        {
          "port": 80,
          "protocol": "tcp",
          "service": "http",
          "version": "nginx 1.18.0"
        },
        {
          "port": 443,
          "protocol": "tcp",
          "service": "https",
          "version": "nginx 1.18.0"
        }
      ]
    }
  ]
}
```

### 3. 执行任务

**POST** `/tasks/{task_id}/execute`

### 4. 取消任务

**POST** `/tasks/{task_id}/cancel`

## 漏洞管理

### 1. 获取漏洞列表

**GET** `/vulnerabilities`

**查询参数:**
- `vulnerability_type`: 漏洞类型
- `severity`: 严重程度
- `status`: 状态
- `assigned_to`: 分配给
- `verified`: 是否已验证

**响应:**
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "title": "SQL Injection in login form",
    "vulnerability_type": "sql_injection",
    "severity": "high",
    "status": "open",
    "target_url": "https://example.com/login",
    "scanner": "nuclei",
    "discovery_date": "2024-01-15T10:00:00Z",
    "verified": false,
    "cvss_score": 8.1
  }
]
```

### 2. 创建漏洞

**POST** `/vulnerabilities`

```json
{
  "title": "Cross-Site Scripting in search form",
  "description": "Reflected XSS vulnerability found in search parameter",
  "vulnerability_type": "xss",
  "severity": "medium",
  "target_asset_id": "507f1f77bcf86cd799439011",
  "target_url": "https://example.com/search",
  "scanner": "manual",
  "request": "GET /search?q=<script>alert(1)</script> HTTP/1.1\nHost: example.com",
  "response": "HTTP/1.1 200 OK\n...",
  "proof_of_concept": "1. Navigate to https://example.com/search\n2. Enter <script>alert(1)</script>\n3. Observe XSS execution"
}
```

### 3. 验证漏洞

**POST** `/vulnerabilities/{vuln_id}/verify`

```json
{
  "verified": true,
  "verification_notes": "Confirmed exploitable in production environment"
}
```

### 4. 添加评论

**POST** `/vulnerabilities/{vuln_id}/comments`

```json
{
  "comment": "Fixed in version 1.2.3, pending verification"
}
```

### 5. 分配漏洞

**POST** `/vulnerabilities/{vuln_id}/assign`

```json
{
  "assigned_to": "developer1"
}
```

## 报告管理

### 1. 生成报告

**POST** `/reports`

```json
{
  "title": "Weekly Security Report",
  "description": "Comprehensive security assessment report",
  "report_type": "vulnerability_report",
  "format": "pdf",
  "date_range": {
    "start": "2024-01-08T00:00:00Z",
    "end": "2024-01-15T23:59:59Z"
  },
  "severity_filter": ["critical", "high", "medium"],
  "include_sections": ["summary", "vulnerabilities", "recommendations"],
  "auto_email": true,
  "email_recipients": ["security@example.com"]
}
```

**响应:**
```json
{
  "id": "507f1f77bcf86cd799439014",
  "title": "Weekly Security Report",
  "status": "generating",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### 2. 下载报告

**GET** `/reports/{report_id}/download`

返回文件流，浏览器会自动下载报告文件。

### 3. 获取报告状态

**GET** `/reports/{report_id}`

**响应:**
```json
{
  "id": "507f1f77bcf86cd799439014",
  "title": "Weekly Security Report",
  "status": "completed",
  "generated_at": "2024-01-15T10:05:00Z",
  "generation_time": 45.2,
  "file_size": 2048576,
  "total_vulnerabilities": 25,
  "vulnerability_by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 18
  }
}
```

## 高级搜索

### 1. 资产搜索

**POST** `/assets/search`

```json
{
  "query": "example.com",
  "asset_type": "domain",
  "status": "active",
  "tags": ["production"],
  "created_after": "2024-01-01T00:00:00Z",
  "skip": 0,
  "limit": 50
}
```

### 2. 漏洞搜索

**POST** `/vulnerabilities/search`

```json
{
  "query": "SQL injection",
  "severity": ["critical", "high"],
  "status": "open",
  "discovered_after": "2024-01-01T00:00:00Z",
  "skip": 0,
  "limit": 50
}
```

## 统计信息

### 1. 资产统计

**GET** `/assets/stats`

**响应:**
```json
{
  "total_assets": 1250,
  "assets_by_type": {
    "domain": 450,
    "ip": 300,
    "url": 500
  },
  "assets_by_status": {
    "active": 1100,
    "inactive": 150
  },
  "recent_assets": 25,
  "monitored_assets": 1000
}
```

### 2. 漏洞统计

**GET** `/vulnerabilities/stats`

**响应:**
```json
{
  "total_vulnerabilities": 156,
  "vulnerabilities_by_severity": {
    "critical": 5,
    "high": 23,
    "medium": 78,
    "low": 50
  },
  "vulnerabilities_by_status": {
    "open": 89,
    "fixed": 45,
    "false_positive": 22
  },
  "verified_vulnerabilities": 134,
  "overdue_vulnerabilities": 12,
  "average_cvss_score": 6.2
}
```

## 错误处理

### HTTP状态码

- `200 OK` - 请求成功
- `201 Created` - 资源创建成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `422 Unprocessable Entity` - 数据验证失败
- `500 Internal Server Error` - 服务器内部错误

### 错误响应格式

```json
{
  "detail": "权限不足",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "timestamp": "2024-01-15T10:00:00Z",
  "path": "/api/v1/vulnerabilities"
}
```

## 分页

所有列表接口都支持分页，使用以下参数：

- `skip`: 跳过的记录数
- `limit`: 返回的记录数

响应头包含分页信息：
```
X-Total-Count: 1250
X-Page-Count: 25
X-Current-Page: 1
X-Per-Page: 50
```

## 限流

API接口实现了速率限制：

- 认证接口: 5次/分钟
- 普通接口: 100次/分钟
- 批量操作: 10次/分钟

超出限制时返回429状态码：
```json
{
  "detail": "Request rate limit exceeded",
  "retry_after": 60
}
```

## SDK 示例

### Python

```python
import requests

class SOCClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})

    def login(self, username, password):
        response = self.session.post(f'{self.base_url}/auth/login', json={
            'username': username,
            'password': password
        })
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        return data

    def get_assets(self, **params):
        response = self.session.get(f'{self.base_url}/assets', params=params)
        return response.json()

    def create_scan_task(self, task_data):
        response = self.session.post(f'{self.base_url}/tasks', json=task_data)
        return response.json()

# 使用示例
client = SOCClient('http://localhost:8000/api/v1')
client.login('admin', 'password')

assets = client.get_assets(asset_type='domain', limit=10)
print(f"Found {len(assets)} assets")

task = client.create_scan_task({
    'name': 'API Test Scan',
    'task_type': 'port_scan',
    'target_domains': ['example.com']
})
print(f"Created task: {task['id']}")
```

### JavaScript

```javascript
class SOCClient {
    constructor(baseURL, token = null) {
        this.baseURL = baseURL;
        this.token = token;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        this.token = data.access_token;
        return data;
    }

    async getAssets(params = {}) {
        const query = new URLSearchParams(params);
        const response = await fetch(`${this.baseURL}/assets?${query}`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        return response.json();
    }

    async createScanTask(taskData) {
        const response = await fetch(`${this.baseURL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify(taskData)
        });
        return response.json();
    }
}

// 使用示例
const client = new SOCClient('http://localhost:8000/api/v1');
await client.login('admin', 'password');

const assets = await client.getAssets({ asset_type: 'domain', limit: 10 });
console.log(`Found ${assets.length} assets`);
```

## Webhook集成

SOC平台支持Webhook通知，可以在特定事件发生时向指定URL发送HTTP请求。

### 支持的事件

- `scan.completed` - 扫描任务完成
- `vulnerability.discovered` - 发现新漏洞
- `vulnerability.verified` - 漏洞验证完成
- `report.generated` - 报告生成完成

### Webhook负载示例

```json
{
  "event": "vulnerability.discovered",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "vulnerability_id": "507f1f77bcf86cd799439013",
    "title": "SQL Injection in login form",
    "severity": "high",
    "target_url": "https://example.com/login"
  }
}
```

---

完整的API文档可以通过访问 `http://localhost:8000/docs` 查看Swagger交互式文档，或访问 `http://localhost:8000/redoc` 查看ReDoc格式的文档。