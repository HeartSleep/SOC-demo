from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Union
from app.api.models.asset import AssetType, AssetStatus, PortProtocol


class AssetBase(BaseModel):
    name: str
    asset_type: AssetType
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    ip_address: Optional[Union[IPv4Address, IPv6Address]] = None
    url: Optional[HttpUrl] = None
    port: Optional[int] = None
    protocol: Optional[PortProtocol] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    tags: List[str] = []
    criticality: str = "medium"
    notes: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[AssetStatus] = None
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    ip_address: Optional[Union[IPv4Address, IPv6Address]] = None
    url: Optional[HttpUrl] = None
    port: Optional[int] = None
    protocol: Optional[PortProtocol] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    criticality: Optional[str] = None
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    operating_system: Optional[str] = None
    technology_stack: Optional[List[str]] = None
    monitoring_enabled: Optional[bool] = None
    scan_enabled: Optional[bool] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetResponse(AssetBase):
    id: str
    status: AssetStatus
    labels: Dict[str, str]
    service_name: Optional[str]
    service_version: Optional[str]
    operating_system: Optional[str]
    technology_stack: List[str]
    open_ports: List[Dict[str, Any]]
    ssl_info: Optional[Dict[str, Any]]
    dns_records: List[Dict[str, Any]]
    discovery_method: Optional[str]
    discovery_source: Optional[str]
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    parent_asset_id: Optional[str]
    child_assets: List[str]
    monitoring_enabled: bool
    scan_enabled: bool
    last_scan: Optional[datetime]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class AssetBulkCreate(BaseModel):
    assets: List[AssetCreate]


class AssetImport(BaseModel):
    import_type: str  # csv, json, nmap_xml
    data: str  # File content or JSON data
    auto_create_missing: bool = True
    update_existing: bool = False


class AssetSearch(BaseModel):
    query: Optional[str] = None
    asset_type: Optional[AssetType] = None
    status: Optional[AssetStatus] = None
    organization: Optional[str] = None
    tags: Optional[List[str]] = None
    criticality: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    skip: int = 0
    limit: int = 100


class AssetStats(BaseModel):
    total_assets: int
    assets_by_type: Dict[AssetType, int]
    assets_by_status: Dict[AssetStatus, int]
    assets_by_criticality: Dict[str, int]
    recent_assets: int  # Assets created in last 7 days
    monitored_assets: int
    scan_enabled_assets: int