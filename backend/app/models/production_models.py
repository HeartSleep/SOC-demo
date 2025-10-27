"""
Production Database Models for SOC Security Platform
Comprehensive security-focused database schema
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, JSON, ForeignKey, Enum, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, INET, CIDR, ARRAY, JSONB
import uuid
import enum
from datetime import datetime

Base = declarative_base()


# Enums
class UserRole(enum.Enum):
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    SECURITY_ENGINEER = "security_engineer"
    INCIDENT_RESPONDER = "incident_responder"
    COMPLIANCE_OFFICER = "compliance_officer"
    READ_ONLY = "read_only"
    GUEST = "guest"


class ScanType(enum.Enum):
    NETWORK = "network"
    WEB = "web"
    API = "api"
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE = "compliance"
    VULNERABILITY = "vulnerability"
    PENETRATION = "penetration"
    CONFIGURATION = "configuration"


class VulnerabilitySeverity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AssetType(enum.Enum):
    SERVER = "server"
    WORKSTATION = "workstation"
    NETWORK_DEVICE = "network_device"
    WEB_APPLICATION = "web_application"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"
    CLOUD_RESOURCE = "cloud_resource"
    CONTAINER = "container"
    MOBILE_APP = "mobile_app"
    IOT_DEVICE = "iot_device"


class AlertStatus(enum.Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class ComplianceFramework(enum.Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    NIST = "nist"
    CIS = "cis"


# User Management
class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.READ_ONLY)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(INET)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

    __table_args__ = (
        CheckConstraint('failed_login_attempts >= 0'),
        Index('idx_user_email_active', 'email', 'is_active'),
    )


class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(INET, nullable=False)
    user_agent = Column(Text)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")


class APIKey(Base):
    __tablename__ = 'api_keys'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True))
    last_used_ip = Column(INET)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    permissions = Column(JSONB, default={})
    rate_limit = Column(Integer, default=1000)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="api_keys")


# Asset Management
class Asset(Base):
    __tablename__ = 'assets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(Enum(AssetType), nullable=False)
    identifier = Column(String(255), unique=True, nullable=False, index=True)  # IP, domain, etc.
    description = Column(Text)
    owner = Column(String(255))
    business_unit = Column(String(255))
    criticality = Column(Integer, default=3)  # 1-5 scale
    location = Column(String(255))
    tags = Column(ARRAY(String))
    metadata = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    vulnerabilities = relationship("Vulnerability", back_populates="asset")
    scans = relationship("ScanTask", back_populates="asset")
    network_info = relationship("NetworkInfo", back_populates="asset", uselist=False)
    services = relationship("Service", back_populates="asset")

    __table_args__ = (
        CheckConstraint('criticality >= 1 AND criticality <= 5'),
        Index('idx_asset_type_active', 'type', 'is_active'),
    )


class NetworkInfo(Base):
    __tablename__ = 'network_info'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), unique=True, nullable=False)
    ip_address = Column(INET)
    ipv6_address = Column(INET)
    mac_address = Column(String(17))
    hostname = Column(String(255))
    domain = Column(String(255))
    subnet = Column(CIDR)
    gateway = Column(INET)
    dns_servers = Column(ARRAY(INET))
    open_ports = Column(ARRAY(Integer))
    os_fingerprint = Column(String(255))
    os_version = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    asset = relationship("Asset", back_populates="network_info")


class Service(Base):
    __tablename__ = 'services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String(10))  # TCP, UDP
    service_name = Column(String(255))
    product = Column(String(255))
    version = Column(String(100))
    banner = Column(Text)
    state = Column(String(20))  # open, closed, filtered
    ssl_enabled = Column(Boolean, default=False)
    ssl_cert_info = Column(JSONB)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset", back_populates="services")

    __table_args__ = (
        UniqueConstraint('asset_id', 'port', 'protocol'),
        Index('idx_service_port', 'port'),
    )


# Vulnerability Management
class Vulnerability(Base):
    __tablename__ = 'vulnerabilities'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), nullable=False)
    scan_id = Column(UUID(as_uuid=True), ForeignKey('scan_tasks.id'))
    cve_id = Column(String(50), index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(Enum(VulnerabilitySeverity), nullable=False)
    cvss_score = Column(Float)
    cvss_vector = Column(String(255))
    exploit_available = Column(Boolean, default=False)
    exploit_info = Column(JSONB)
    solution = Column(Text)
    references = Column(ARRAY(String))
    affected_component = Column(String(255))
    affected_version = Column(String(100))
    is_confirmed = Column(Boolean, default=True)
    is_false_positive = Column(Boolean, default=False)
    status = Column(String(50), default='open')  # open, mitigated, resolved, accepted
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    evidence = Column(JSONB)  # Screenshots, request/response, etc.

    # Relationships
    asset = relationship("Asset", back_populates="vulnerabilities")
    scan = relationship("ScanTask")
    remediation = relationship("Remediation", back_populates="vulnerability", uselist=False)

    __table_args__ = (
        CheckConstraint('cvss_score >= 0 AND cvss_score <= 10'),
        Index('idx_vuln_severity_status', 'severity', 'status'),
        Index('idx_vuln_cve', 'cve_id'),
    )


class Remediation(Base):
    __tablename__ = 'remediations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vulnerability_id = Column(UUID(as_uuid=True), ForeignKey('vulnerabilities.id'), unique=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    priority = Column(Integer, default=3)  # 1-5 scale
    status = Column(String(50), default='pending')
    action_taken = Column(Text)
    verification_status = Column(String(50))
    remediated_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    vulnerability = relationship("Vulnerability", back_populates="remediation")


# Scanning
class ScanTask(Base):
    __tablename__ = 'scan_tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(Enum(ScanType), nullable=False)
    target = Column(Text, nullable=False)  # Can be IP, domain, CIDR, URL
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'))
    scan_profile = Column(String(100))  # aggressive, normal, stealth
    tools_used = Column(ARRAY(String))  # nmap, nuclei, zap, etc.
    configuration = Column(JSONB, default={})
    scheduled_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), default='pending')
    progress = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    results_summary = Column(JSONB)
    raw_output = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    asset = relationship("Asset", back_populates="scans")
    scan_results = relationship("ScanResult", back_populates="scan")

    __table_args__ = (
        Index('idx_scan_status_type', 'status', 'type'),
        Index('idx_scan_scheduled', 'scheduled_at'),
    )


class ScanResult(Base):
    __tablename__ = 'scan_results'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey('scan_tasks.id'), nullable=False)
    finding_type = Column(String(100))  # port, vulnerability, misconfiguration, etc.
    severity = Column(Enum(VulnerabilitySeverity))
    title = Column(String(500))
    description = Column(Text)
    location = Column(String(500))  # URL, file path, port, etc.
    evidence = Column(JSONB)
    recommendation = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("ScanTask", back_populates="scan_results")


# Security Policies
class SecurityPolicy(Base):
    __tablename__ = 'security_policies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(100))  # password, network, access, etc.
    rules = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    enforcement_level = Column(String(50))  # block, warn, log
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    violations = relationship("PolicyViolation", back_populates="policy")


class PolicyViolation(Base):
    __tablename__ = 'policy_violations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey('security_policies.id'), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    violation_details = Column(JSONB)
    severity = Column(Enum(VulnerabilitySeverity))
    status = Column(String(50), default='open')
    remediation_status = Column(String(50))
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    policy = relationship("SecurityPolicy", back_populates="violations")


# Threat Intelligence
class ThreatIndicator(Base):
    __tablename__ = 'threat_indicators'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_type = Column(String(50))  # ip, domain, hash, email, url
    indicator_value = Column(String(500), unique=True, nullable=False, index=True)
    threat_type = Column(String(100))  # malware, phishing, botnet, etc.
    confidence_score = Column(Float)
    source = Column(String(255))
    tags = Column(ARRAY(String))
    metadata = Column(JSONB)
    is_active = Column(Boolean, default=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 100'),
        Index('idx_threat_type_active', 'threat_type', 'is_active'),
    )


# Incident Response
class Incident(Base):
    __tablename__ = 'incidents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(Enum(VulnerabilitySeverity), nullable=False)
    status = Column(String(50), default='open')
    category = Column(String(100))  # data_breach, malware, ddos, etc.
    source = Column(String(255))  # How it was detected
    affected_assets = Column(ARRAY(UUID(as_uuid=True)))
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    response_plan = Column(Text)
    containment_status = Column(String(50))
    eradication_status = Column(String(50))
    recovery_status = Column(String(50))
    lessons_learned = Column(Text)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    contained_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    timeline = relationship("IncidentTimeline", back_populates="incident")

    __table_args__ = (
        Index('idx_incident_status_severity', 'status', 'severity'),
    )


class IncidentTimeline(Base):
    __tablename__ = 'incident_timeline'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey('incidents.id'), nullable=False)
    action = Column(String(255), nullable=False)
    description = Column(Text)
    performed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    incident = relationship("Incident", back_populates="timeline")


# Compliance
class ComplianceCheck(Base):
    __tablename__ = 'compliance_checks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework = Column(Enum(ComplianceFramework), nullable=False)
    control_id = Column(String(100), nullable=False)
    control_name = Column(String(500))
    description = Column(Text)
    check_type = Column(String(50))  # automated, manual
    script = Column(Text)  # Automated check script
    last_checked = Column(DateTime(timezone=True))
    status = Column(String(50))  # compliant, non_compliant, not_applicable
    evidence = Column(JSONB)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('framework', 'control_id'),
        Index('idx_compliance_framework_status', 'framework', 'status'),
    )


# Reporting
class Report(Base):
    __tablename__ = 'reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(100))  # vulnerability, compliance, executive, technical
    format = Column(String(20))  # pdf, html, json, csv
    template = Column(String(100))
    filters = Column(JSONB)  # Date range, severity, assets, etc.
    content = Column(JSONB)
    file_path = Column(String(500))
    generated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_report_type_date', 'type', 'generated_at'),
    )


# Alerts and Notifications
class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(Enum(VulnerabilitySeverity), nullable=False)
    source = Column(String(255))  # System component that generated the alert
    category = Column(String(100))
    status = Column(Enum(AlertStatus), default=AlertStatus.NEW)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    metadata = Column(JSONB)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('idx_alert_status_severity', 'status', 'severity'),
        Index('idx_alert_triggered', 'triggered_at'),
    )


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    type = Column(String(50))  # email, sms, webhook, in_app
    subject = Column(String(500))
    message = Column(Text)
    metadata = Column(JSONB)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
    )


# Audit Logging
class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_data = Column(JSONB)
    response_status = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_timestamp', 'timestamp'),
    )


# Create indexes for better performance
def create_indexes():
    """Additional indexes for optimization"""
    return [
        # Composite indexes for common queries
        Index('idx_vuln_asset_severity', 'vulnerabilities.asset_id', 'vulnerabilities.severity'),
        Index('idx_scan_created_status', 'scan_tasks.created_at', 'scan_tasks.status'),
        Index('idx_incident_assigned_status', 'incidents.assigned_to', 'incidents.status'),
        Index('idx_alert_assigned_status', 'alerts.assigned_to', 'alerts.status'),
    ]