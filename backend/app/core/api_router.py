"""
Centralized API router configuration for consistent API versioning
"""

from fastapi import APIRouter
from app.api.endpoints import (
    auth, assets, tasks, vulnerabilities,
    reports, users, settings as settings_endpoints,
    system, vulnerability_rules
)

# Create main API router with version prefix
api_v1_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers with proper prefixes
api_v1_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_v1_router.include_router(
    assets.router,
    prefix="/assets",
    tags=["assets"]
)

api_v1_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"]
)

api_v1_router.include_router(
    vulnerabilities.router,
    prefix="/vulnerabilities",
    tags=["vulnerabilities"]
)

api_v1_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"]
)

api_v1_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_v1_router.include_router(
    settings_endpoints.router,
    prefix="/settings",
    tags=["settings"]
)

api_v1_router.include_router(
    system.router,
    prefix="/system",
    tags=["system"]
)

api_v1_router.include_router(
    vulnerability_rules.router,
    prefix="/vulnerability-rules",
    tags=["vulnerability-rules"]
)