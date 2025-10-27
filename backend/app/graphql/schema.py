"""
GraphQL Schema Definition for SOC Platform
Provides flexible querying and real-time subscriptions
"""

import strawberry
from strawberry.types import Info
from strawberry.subscriptions import AsyncGenerator
from typing import List, Optional, Any
import asyncio
from datetime import datetime
from enum import Enum

# GraphQL Types
@strawberry.enum
class AssetType(Enum):
    DOMAIN = "domain"
    IP = "ip"
    URL = "url"
    NETWORK = "network"
    APPLICATION = "application"


@strawberry.enum
class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@strawberry.enum
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@strawberry.type
class User:
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    permissions: List[str]

    @strawberry.field
    async def tasks(self, info: Info) -> List["Task"]:
        """Get tasks assigned to this user"""
        from app.services.task_service import get_user_tasks
        return await get_user_tasks(self.id)

    @strawberry.field
    async def activity_count(self, info: Info, days: int = 7) -> int:
        """Get user activity count for specified days"""
        from app.services.analytics_service import get_user_activity
        return await get_user_activity(self.id, days)


@strawberry.type
class Asset:
    id: str
    name: str
    asset_type: AssetType
    status: str
    ip_address: Optional[str]
    domain: Optional[str]
    tags: List[str]
    criticality: Severity
    organization: str
    owner: str
    created_at: datetime
    updated_at: datetime
    last_scan: Optional[datetime]

    @strawberry.field
    async def vulnerabilities(
        self,
        info: Info,
        severity: Optional[Severity] = None,
        limit: int = 10
    ) -> List["Vulnerability"]:
        """Get vulnerabilities for this asset"""
        from app.services.vulnerability_service import get_asset_vulnerabilities
        return await get_asset_vulnerabilities(self.id, severity, limit)

    @strawberry.field
    async def risk_score(self, info: Info) -> float:
        """Calculate risk score for this asset"""
        from app.services.risk_service import calculate_asset_risk
        return await calculate_asset_risk(self.id)

    @strawberry.field
    async def scan_history(self, info: Info, limit: int = 5) -> List["ScanResult"]:
        """Get scan history for this asset"""
        from app.services.scan_service import get_asset_scan_history
        return await get_asset_scan_history(self.id, limit)


@strawberry.type
class Vulnerability:
    id: str
    title: str
    description: str
    severity: Severity
    status: str
    asset_id: str
    cvss_score: float
    cve_id: Optional[str]
    discovered_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    @strawberry.field
    async def asset(self, info: Info) -> Asset:
        """Get the asset associated with this vulnerability"""
        from app.services.asset_service import get_asset_by_id
        return await get_asset_by_id(self.asset_id)

    @strawberry.field
    async def remediation(self, info: Info) -> Optional[str]:
        """Get remediation suggestions"""
        from app.services.remediation_service import get_remediation
        return await get_remediation(self.cve_id)


@strawberry.type
class Task:
    id: str
    name: str
    type: str
    status: TaskStatus
    priority: Severity
    assigned_to: str
    progress: int
    created_at: datetime
    updated_at: datetime
    eta: Optional[datetime]

    @strawberry.field
    async def assigned_user(self, info: Info) -> User:
        """Get the user assigned to this task"""
        from app.services.user_service import get_user_by_username
        return await get_user_by_username(self.assigned_to)

    @strawberry.field
    async def logs(self, info: Info, limit: int = 10) -> List[str]:
        """Get task execution logs"""
        from app.services.task_service import get_task_logs
        return await get_task_logs(self.id, limit)


@strawberry.type
class ScanResult:
    id: str
    asset_id: str
    scan_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    findings_count: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int


@strawberry.type
class SystemMetrics:
    uptime_seconds: int
    total_requests: int
    failed_requests: int
    error_rate: float
    requests_per_minute: int
    avg_response_time_ms: float
    active_users: int
    cpu_usage: float
    memory_usage_mb: int
    disk_usage_percent: float
    timestamp: datetime


@strawberry.type
class DashboardStats:
    total_assets: int
    active_vulnerabilities: int
    critical_vulnerabilities: int
    tasks_in_progress: int
    recent_scans: int
    compliance_score: float
    risk_score: float


@strawberry.type
class Notification:
    id: str
    type: str
    title: str
    message: str
    severity: Severity
    timestamp: datetime
    read: bool


# Pagination types
@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]


@strawberry.type
class UserConnection:
    edges: List[User]
    page_info: PageInfo
    total_count: int


@strawberry.type
class AssetConnection:
    edges: List[Asset]
    page_info: PageInfo
    total_count: int


# Input types for mutations
@strawberry.input
class CreateUserInput:
    username: str
    email: str
    password: str
    full_name: str
    role: str
    permissions: List[str]


@strawberry.input
class UpdateUserInput:
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


@strawberry.input
class CreateAssetInput:
    name: str
    asset_type: AssetType
    ip_address: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str]
    criticality: Severity
    organization: str
    owner: str


@strawberry.input
class UpdateAssetInput:
    id: str
    name: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    criticality: Optional[Severity] = None
    owner: Optional[str] = None


@strawberry.input
class CreateTaskInput:
    name: str
    type: str
    priority: Severity
    assigned_to: str


@strawberry.input
class ScanAssetInput:
    asset_id: str
    scan_type: str
    deep_scan: bool = False


# Queries
@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: Info) -> User:
        """Get current authenticated user"""
        from app.services.auth_service import get_current_user_from_context
        return await get_current_user_from_context(info.context)

    @strawberry.field
    async def user(self, info: Info, id: str) -> Optional[User]:
        """Get user by ID"""
        from app.services.user_service import get_user_by_id
        return await get_user_by_id(id)

    @strawberry.field
    async def users(
        self,
        info: Info,
        first: int = 20,
        after: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> UserConnection:
        """Get paginated list of users"""
        from app.services.user_service import get_users_paginated
        return await get_users_paginated(first, after, role, is_active)

    @strawberry.field
    async def asset(self, info: Info, id: str) -> Optional[Asset]:
        """Get asset by ID"""
        from app.services.asset_service import get_asset_by_id
        return await get_asset_by_id(id)

    @strawberry.field
    async def assets(
        self,
        info: Info,
        first: int = 20,
        after: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        criticality: Optional[Severity] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> AssetConnection:
        """Get paginated list of assets with filtering"""
        from app.services.asset_service import get_assets_paginated
        return await get_assets_paginated(
            first, after, asset_type, criticality, tags, search
        )

    @strawberry.field
    async def vulnerabilities(
        self,
        info: Info,
        asset_id: Optional[str] = None,
        severity: Optional[Severity] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Vulnerability]:
        """Get vulnerabilities with filtering"""
        from app.services.vulnerability_service import get_vulnerabilities
        return await get_vulnerabilities(asset_id, severity, status, limit)

    @strawberry.field
    async def tasks(
        self,
        info: Info,
        assigned_to: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[Severity] = None,
        limit: int = 20
    ) -> List[Task]:
        """Get tasks with filtering"""
        from app.services.task_service import get_tasks
        return await get_tasks(assigned_to, status, priority, limit)

    @strawberry.field
    async def system_metrics(self, info: Info) -> SystemMetrics:
        """Get current system metrics"""
        from app.services.monitoring_service import get_system_metrics
        return await get_system_metrics()

    @strawberry.field
    async def dashboard_stats(self, info: Info) -> DashboardStats:
        """Get dashboard statistics"""
        from app.services.analytics_service import get_dashboard_stats
        return await get_dashboard_stats()

    @strawberry.field
    async def search(
        self,
        info: Info,
        query: str,
        types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Any]:
        """Global search across all entities"""
        from app.services.search_service import global_search
        return await global_search(query, types, limit)

    @strawberry.field
    async def notifications(
        self,
        info: Info,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Notification]:
        """Get user notifications"""
        from app.services.notification_service import get_user_notifications
        user = await get_current_user_from_context(info.context)
        return await get_user_notifications(user.id, unread_only, limit)


# Mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_user(self, info: Info, input: CreateUserInput) -> User:
        """Create a new user"""
        from app.services.user_service import create_user
        return await create_user(input)

    @strawberry.mutation
    async def update_user(self, info: Info, input: UpdateUserInput) -> User:
        """Update an existing user"""
        from app.services.user_service import update_user
        return await update_user(input)

    @strawberry.mutation
    async def delete_user(self, info: Info, id: str) -> bool:
        """Delete a user"""
        from app.services.user_service import delete_user
        return await delete_user(id)

    @strawberry.mutation
    async def create_asset(self, info: Info, input: CreateAssetInput) -> Asset:
        """Create a new asset"""
        from app.services.asset_service import create_asset
        return await create_asset(input)

    @strawberry.mutation
    async def update_asset(self, info: Info, input: UpdateAssetInput) -> Asset:
        """Update an existing asset"""
        from app.services.asset_service import update_asset
        return await update_asset(input)

    @strawberry.mutation
    async def delete_asset(self, info: Info, id: str) -> bool:
        """Delete an asset"""
        from app.services.asset_service import delete_asset
        return await delete_asset(id)

    @strawberry.mutation
    async def scan_asset(self, info: Info, input: ScanAssetInput) -> Task:
        """Initiate a scan on an asset"""
        from app.services.scan_service import initiate_scan
        return await initiate_scan(input)

    @strawberry.mutation
    async def create_task(self, info: Info, input: CreateTaskInput) -> Task:
        """Create a new task"""
        from app.services.task_service import create_task
        return await create_task(input)

    @strawberry.mutation
    async def update_task_status(
        self,
        info: Info,
        id: str,
        status: TaskStatus,
        progress: Optional[int] = None
    ) -> Task:
        """Update task status and progress"""
        from app.services.task_service import update_task_status
        return await update_task_status(id, status, progress)

    @strawberry.mutation
    async def mark_vulnerability_resolved(
        self,
        info: Info,
        id: str,
        resolution_notes: Optional[str] = None
    ) -> Vulnerability:
        """Mark a vulnerability as resolved"""
        from app.services.vulnerability_service import mark_resolved
        return await mark_resolved(id, resolution_notes)

    @strawberry.mutation
    async def mark_notification_read(self, info: Info, id: str) -> Notification:
        """Mark a notification as read"""
        from app.services.notification_service import mark_as_read
        return await mark_as_read(id)

    @strawberry.mutation
    async def trigger_full_scan(self, info: Info) -> Task:
        """Trigger a full system scan"""
        from app.services.scan_service import trigger_full_scan
        return await trigger_full_scan()


# Subscriptions
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def system_metrics_stream(self, info: Info) -> AsyncGenerator[SystemMetrics, None]:
        """Subscribe to real-time system metrics"""
        from app.services.monitoring_service import get_system_metrics

        while True:
            metrics = await get_system_metrics()
            yield metrics
            await asyncio.sleep(5)  # Update every 5 seconds

    @strawberry.subscription
    async def task_updates(
        self,
        info: Info,
        task_id: Optional[str] = None
    ) -> AsyncGenerator[Task, None]:
        """Subscribe to task updates"""
        from app.services.task_service import subscribe_to_task_updates

        async for task in subscribe_to_task_updates(task_id):
            yield task

    @strawberry.subscription
    async def vulnerability_alerts(
        self,
        info: Info,
        min_severity: Severity = Severity.MEDIUM
    ) -> AsyncGenerator[Vulnerability, None]:
        """Subscribe to vulnerability alerts"""
        from app.services.vulnerability_service import subscribe_to_alerts

        async for vuln in subscribe_to_alerts(min_severity):
            yield vuln

    @strawberry.subscription
    async def asset_changes(
        self,
        info: Info,
        asset_id: Optional[str] = None
    ) -> AsyncGenerator[Asset, None]:
        """Subscribe to asset changes"""
        from app.services.asset_service import subscribe_to_changes

        async for asset in subscribe_to_changes(asset_id):
            yield asset

    @strawberry.subscription
    async def notifications(self, info: Info) -> AsyncGenerator[Notification, None]:
        """Subscribe to user notifications"""
        from app.services.notification_service import subscribe_to_notifications
        from app.services.auth_service import get_current_user_from_context

        user = await get_current_user_from_context(info.context)
        async for notification in subscribe_to_notifications(user.id):
            yield notification

    @strawberry.subscription
    async def scan_progress(
        self,
        info: Info,
        scan_id: str
    ) -> AsyncGenerator[ScanResult, None]:
        """Subscribe to scan progress updates"""
        from app.services.scan_service import subscribe_to_scan_progress

        async for update in subscribe_to_scan_progress(scan_id):
            yield update


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)