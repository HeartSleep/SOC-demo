from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from app.api.models.api_security import (
    APIScanStatus,
    APISecurityIssueType,
    APIIssueSeverity
)


# ============ API扫描任务 ============

class APIScanConfigSchema(BaseModel):
    """API扫描配置"""
    enable_js_extraction: bool = True
    enable_api_discovery: bool = True
    enable_microservice_detection: bool = True
    enable_unauthorized_check: bool = True
    enable_sensitive_info_check: bool = True
    use_ai: bool = True
    timeout: int = 300
    max_js_files: int = 100
    max_apis: int = 1000


class APIScanTaskCreate(BaseModel):
    """创建API扫描任务"""
    name: str
    target_url: str
    scan_config: Optional[APIScanConfigSchema] = None


class APIScanTaskUpdate(BaseModel):
    """更新API扫描任务"""
    name: Optional[str] = None
    status: Optional[APIScanStatus] = None
    progress: Optional[float] = None
    current_phase: Optional[str] = None
    error_message: Optional[str] = None


class APIScanTaskResponse(BaseModel):
    """API扫描任务响应"""
    id: str
    name: str
    target_url: str
    status: APIScanStatus
    scan_config: Dict[str, Any]

    total_js_files: int
    total_apis: int
    total_services: int
    total_issues: int

    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int

    progress: float
    current_phase: Optional[str]

    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]

    error_message: Optional[str]

    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True


# ============ JS资源 ============

class JSResourceCreate(BaseModel):
    """创建JS资源"""
    scan_task_id: str
    url: str
    base_url: Optional[str] = None
    file_name: Optional[str] = None
    extraction_method: Optional[str] = None


class JSResourceResponse(BaseModel):
    """JS资源响应"""
    id: str
    scan_task_id: str
    url: str
    base_url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    extraction_method: Optional[str]
    has_apis: bool
    has_base_api_path: bool
    has_sensitive_info: bool
    extracted_apis: List[str]
    extracted_base_paths: List[str]
    metadata: Dict[str, Any]
    discovered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============ API接口 ============

class APIEndpointCreate(BaseModel):
    """创建API接口"""
    scan_task_id: str
    base_url: str
    base_api_path: Optional[str] = None
    service_path: Optional[str] = None
    api_path: str
    full_url: str
    http_method: str = "GET"
    discovery_method: Optional[str] = None


class APIEndpointResponse(BaseModel):
    """API接口响应"""
    id: str
    scan_task_id: str
    base_url: str
    base_api_path: Optional[str]
    service_path: Optional[str]
    api_path: str
    full_url: str
    http_method: str
    status_code: Optional[int]
    response_time: Optional[float]
    discovery_method: Optional[str]
    is_public_api: Optional[bool]
    requires_auth: Optional[bool]
    is_404: bool
    ai_analysis: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    discovered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============ 微服务信息 ============

class MicroserviceInfoCreate(BaseModel):
    """创建微服务信息"""
    scan_task_id: str
    base_url: str
    service_name: str
    service_full_path: str


class MicroserviceInfoResponse(BaseModel):
    """微服务信息响应"""
    id: str
    scan_task_id: str
    base_url: str
    service_name: str
    service_full_path: str
    total_endpoints: int
    unique_paths: List[str]
    detected_technologies: List[str]
    has_vulnerabilities: bool
    vulnerability_details: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    discovered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ============ API安全问题 ============

class APISecurityIssueCreate(BaseModel):
    """创建API安全问题"""
    scan_task_id: str
    api_endpoint_id: Optional[str] = None
    microservice_id: Optional[str] = None
    title: str
    description: str
    issue_type: APISecurityIssueType
    severity: APIIssueSeverity
    target_url: str
    target_api: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None


class APISecurityIssueUpdate(BaseModel):
    """更新API安全问题"""
    is_verified: Optional[bool] = None
    is_false_positive: Optional[bool] = None
    verification_notes: Optional[str] = None
    is_resolved: Optional[bool] = None


class APISecurityIssueResponse(BaseModel):
    """API安全问题响应"""
    id: str
    scan_task_id: str
    api_endpoint_id: Optional[str]
    microservice_id: Optional[str]
    title: str
    description: str
    issue_type: APISecurityIssueType
    severity: APIIssueSeverity
    target_url: str
    target_api: Optional[str]
    evidence: Dict[str, Any]
    ai_verified: bool
    ai_analysis_result: Optional[Dict[str, Any]]
    remediation: Optional[str]
    references: List[str]
    is_verified: bool
    is_false_positive: bool
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    verification_notes: Optional[str]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    metadata: Dict[str, Any]
    discovered_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 统计和搜索 ============

class APIScanStatistics(BaseModel):
    """API扫描统计"""
    total_scans: int
    completed_scans: int
    running_scans: int
    failed_scans: int
    total_apis_discovered: int
    total_js_files: int
    total_microservices: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    issues_by_type: Dict[str, int]


class APIScanTaskSearch(BaseModel):
    """API扫描任务搜索"""
    status: Optional[APIScanStatus] = None
    target_url: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    skip: int = 0
    limit: int = 100


class APISecurityIssueSearch(BaseModel):
    """API安全问题搜索"""
    scan_task_id: Optional[str] = None
    issue_type: Optional[APISecurityIssueType] = None
    severity: Optional[APIIssueSeverity] = None
    is_verified: Optional[bool] = None
    is_false_positive: Optional[bool] = None
    is_resolved: Optional[bool] = None
    skip: int = 0
    limit: int = 100
