from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.database import Base
import uuid
import enum


class AssetType(str, enum.Enum):
    DOMAIN = "domain"
    SUBDOMAIN = "subdomain"
    IP = "ip"
    URL = "url"
    PORT = "port"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class PortProtocol(str, enum.Enum):
    TCP = "tcp"
    UDP = "udp"


class Asset(Base):
    __tablename__ = "assets"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic info
    name = Column(String(500), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.UNKNOWN, nullable=False, index=True)

    # Asset details
    domain = Column(String(255), nullable=True, index=True)
    subdomain = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)  # Supports IPv4 and IPv6
    url = Column(Text, nullable=True)
    port = Column(Integer, nullable=True)
    protocol = Column(SQLEnum(PortProtocol), nullable=True)

    # Organization info
    organization = Column(String(255), nullable=True, index=True)
    department = Column(String(255), nullable=True)
    owner = Column(String(255), nullable=True)

    # Tags and categorization
    tags = Column(ARRAY(String), server_default='{}', nullable=False)
    labels = Column(JSON, server_default='{}', nullable=False)
    criticality = Column(String(20), default="medium", nullable=False, index=True)

    # Technical details
    service_name = Column(String(255), nullable=True)
    service_version = Column(String(100), nullable=True)
    operating_system = Column(String(255), nullable=True)
    technology_stack = Column(ARRAY(String), server_default='{}', nullable=False)

    # Network information
    open_ports = Column(JSON, server_default='[]', nullable=False)
    ssl_info = Column(JSON, nullable=True)
    dns_records = Column(JSON, server_default='[]', nullable=False)

    # Discovery information
    discovery_method = Column(String(100), nullable=True)
    discovery_source = Column(String(100), nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Relationships
    parent_asset_id = Column(UUID(as_uuid=True), nullable=True)
    child_assets = Column(ARRAY(String), server_default='{}', nullable=False)

    # Monitoring
    monitoring_enabled = Column(Boolean, default=True, nullable=False)
    scan_enabled = Column(Boolean, default=True, nullable=False)
    last_scan = Column(DateTime, nullable=True)

    # Custom fields
    custom_metadata = Column(JSON, server_default='{}', nullable=False)
    notes = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_asset_name', 'name'),
        Index('idx_asset_type', 'asset_type'),
        Index('idx_asset_status', 'status'),
        Index('idx_asset_domain', 'domain'),
        Index('idx_asset_ip', 'ip_address'),
        Index('idx_asset_organization', 'organization'),
        Index('idx_asset_criticality', 'criticality'),
        Index('idx_asset_created_at', 'created_at'),
        Index('idx_asset_last_seen', 'last_seen'),
    )

    def __str__(self):
        return f"{self.asset_type.value}: {self.name}"