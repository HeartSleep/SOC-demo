from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, JSON, Index, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum


class APIScanStatus(str, enum.Enum):
    """API扫描任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class APISecurityIssueType(str, enum.Enum):
    """API安全问题类型"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"  # 未授权访问
    SENSITIVE_DATA_LEAK = "sensitive_data_leak"  # 敏感信息泄露
    COMPONENT_VULNERABILITY = "component_vulnerability"  # 组件漏洞
    WEAK_AUTHENTICATION = "weak_authentication"  # 弱认证
    OTHER = "other"


class APIIssueSeverity(str, enum.Enum):
    """API安全问题严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class APIScanTask(Base):
    """API安全扫描任务"""
    __tablename__ = "api_scan_tasks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # 基本信息
    name = Column(String(500), nullable=False)
    target_url = Column(Text, nullable=False, index=True)
    status = Column(SQLEnum(APIScanStatus), default=APIScanStatus.PENDING, nullable=False, index=True)

    # 扫描配置
    scan_config = Column(JSON, server_default='{}', nullable=False)
    # 配置示例: {
    #     "enable_js_extraction": true,
    #     "enable_api_discovery": true,
    #     "enable_microservice_detection": true,
    #     "enable_unauthorized_check": true,
    #     "enable_sensitive_info_check": true,
    #     "use_ai": true,
    #     "timeout": 300
    # }

    # 扫描结果统计
    total_js_files = Column(Integer, default=0, nullable=False)
    total_apis = Column(Integer, default=0, nullable=False)
    total_services = Column(Integer, default=0, nullable=False)
    total_issues = Column(Integer, default=0, nullable=False)

    # 问题统计
    critical_issues = Column(Integer, default=0, nullable=False)
    high_issues = Column(Integer, default=0, nullable=False)
    medium_issues = Column(Integer, default=0, nullable=False)
    low_issues = Column(Integer, default=0, nullable=False)

    # 扫描进度
    progress = Column(Float, default=0.0, nullable=False)  # 0-100
    current_phase = Column(String(100), nullable=True)  # JS提取、API发现、安全检测等

    # 时间信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # 错误信息
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_api_scan_task_status', 'status'),
        Index('idx_api_scan_task_target', 'target_url'),
        Index('idx_api_scan_task_created_at', 'created_at'),
    )


class JSResource(Base):
    """JavaScript资源"""
    __tablename__ = "js_resources"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # ✅ 修复：关联扫描任务（添加外键约束）
    scan_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_scan_tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # JS资源信息
    url = Column(Text, nullable=False)
    base_url = Column(String(500), nullable=True, index=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    content_hash = Column(String(64), nullable=True)  # SHA256

    # 提取方法
    extraction_method = Column(String(100), nullable=True)  # static, dynamic, webpack

    # 内容分析
    has_apis = Column(Boolean, default=False, nullable=False)
    has_base_api_path = Column(Boolean, default=False, nullable=False)
    has_sensitive_info = Column(Boolean, default=False, nullable=False)

    # 提取的数据
    extracted_apis = Column(ARRAY(String), server_default='{}', nullable=False)
    extracted_base_paths = Column(ARRAY(String), server_default='{}', nullable=False)

    # 元数据
    metadata = Column(JSON, server_default='{}', nullable=False)

    # 时间字段
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_js_resource_scan_task', 'scan_task_id'),
        Index('idx_js_resource_base_url', 'base_url'),
    )


class APIEndpoint(Base):
    """API接口"""
    __tablename__ = "api_endpoints"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # ✅ 修复：关联扫描任务（添加外键约束）
    scan_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_scan_tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # API分层结构（参考文章中的分层设计）
    base_url = Column(String(500), nullable=False, index=True)  # https://xxx.com
    base_api_path = Column(String(255), nullable=True, index=True)  # /api
    service_path = Column(String(255), nullable=True, index=True)  # /user
    api_path = Column(String(500), nullable=False)  # /getInfo

    # 完整URL
    full_url = Column(Text, nullable=False)  # https://xxx.com/api/user/getInfo

    # 请求信息
    http_method = Column(String(10), default="GET", nullable=False)
    request_headers = Column(JSON, server_default='{}', nullable=False)
    request_params = Column(JSON, server_default='{}', nullable=False)

    # 响应信息
    status_code = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    response_size = Column(Integer, nullable=True)  # bytes
    response_time = Column(Float, nullable=True)  # seconds

    # 发现方法
    discovery_method = Column(String(100), nullable=True)  # static_regex, ai_analysis, dynamic

    # API分类
    is_public_api = Column(Boolean, nullable=True)  # 是否为公共接口
    requires_auth = Column(Boolean, nullable=True)  # 是否需要认证
    is_404 = Column(Boolean, default=False, nullable=False)  # 是否为404

    # AI分析结果
    ai_analysis = Column(JSON, nullable=True)
    # 示例: {
    #     "requires_login": false,
    #     "is_public": true,
    #     "api_description": "用户信息获取接口",
    #     "confidence": 0.95
    # }

    # 元数据
    metadata = Column(JSON, server_default='{}', nullable=False)

    # 时间字段
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_api_endpoint_scan_task', 'scan_task_id'),
        Index('idx_api_endpoint_base_url', 'base_url'),
        Index('idx_api_endpoint_base_api_path', 'base_api_path'),
        Index('idx_api_endpoint_service_path', 'service_path'),
    )


class MicroserviceInfo(Base):
    """微服务信息"""
    __tablename__ = "microservice_info"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # ✅ 修复：关联扫描任务（添加外键约束）
    scan_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_scan_tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # 服务信息
    base_url = Column(String(500), nullable=False, index=True)
    service_name = Column(String(255), nullable=False, index=True)  # 例如: /user, /admin
    service_full_path = Column(String(500), nullable=False)  # 例如: https://xxx.com/api/user

    # 服务统计
    total_endpoints = Column(Integer, default=0, nullable=False)
    unique_paths = Column(ARRAY(String), server_default='{}', nullable=False)

    # 技术栈检测
    detected_technologies = Column(ARRAY(String), server_default='{}', nullable=False)
    # 例如: ["SpringBoot", "FastJSON", "Log4j2"]

    # 组件漏洞
    has_vulnerabilities = Column(Boolean, default=False, nullable=False)
    vulnerability_details = Column(JSON, server_default='[]', nullable=False)

    # 元数据
    metadata = Column(JSON, server_default='{}', nullable=False)

    # 时间字段
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_microservice_scan_task', 'scan_task_id'),
        Index('idx_microservice_base_url', 'base_url'),
        Index('idx_microservice_name', 'service_name'),
    )


class APISecurityIssue(Base):
    """API安全问题"""
    __tablename__ = "api_security_issues"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # ✅ 修复：关联扫描任务（添加外键约束）
    scan_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_scan_tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    api_endpoint_id = Column(
        UUID(as_uuid=True),
        ForeignKey('api_endpoints.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    microservice_id = Column(
        UUID(as_uuid=True),
        ForeignKey('microservice_info.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # 问题基本信息
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    issue_type = Column(SQLEnum(APISecurityIssueType), nullable=False, index=True)
    severity = Column(SQLEnum(APIIssueSeverity), nullable=False, index=True)

    # 目标信息
    target_url = Column(Text, nullable=False)
    target_api = Column(String(500), nullable=True)

    # 证据
    evidence = Column(JSON, server_default='{}', nullable=False)
    # 示例: {
    #     "request": "...",
    #     "response": "...",
    #     "sensitive_data": ["phone_number", "id_card"],
    #     "proof": "..."
    # }

    # AI分析
    ai_verified = Column(Boolean, default=False, nullable=False)
    ai_analysis_result = Column(JSON, nullable=True)

    # 修复建议
    remediation = Column(Text, nullable=True)
    references = Column(ARRAY(String), server_default='{}', nullable=False)

    # 人工验证
    is_verified = Column(Boolean, default=False, nullable=False)
    is_false_positive = Column(Boolean, default=False, nullable=False)
    verified_by = Column(UUID(as_uuid=True), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)

    # 状态
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)

    # 元数据
    metadata = Column(JSON, server_default='{}', nullable=False)

    # 时间字段
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_api_issue_scan_task', 'scan_task_id'),
        Index('idx_api_issue_endpoint', 'api_endpoint_id'),
        Index('idx_api_issue_type', 'issue_type'),
        Index('idx_api_issue_severity', 'severity'),
        Index('idx_api_issue_created_at', 'created_at'),
    )
