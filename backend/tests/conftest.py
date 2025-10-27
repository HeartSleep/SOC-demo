import pytest
import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.main import app
from app.core.config import settings
from app.api.models.user import User
from app.api.models.asset import Asset
from app.api.models.task import Task
from app.api.models.vulnerability import Vulnerability
from app.api.models.report import Report


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_client():
    """Create a test database client."""
    # Use a test database
    test_db_name = f"{settings.MONGODB_DB_NAME}_test"
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[test_db_name]

    # Initialize Beanie with test database
    await init_beanie(
        database=db,
        document_models=[User, Asset, Task, Vulnerability, Report]
    )

    yield client

    # Cleanup: drop test database
    await client.drop_database(test_db_name)
    client.close()


@pytest.fixture
async def db_cleanup(db_client):
    """Clean up database before each test."""
    db_name = f"{settings.MONGODB_DB_NAME}_test"
    db = db_client[db_name]

    # Clear all collections
    collections = await db.list_collection_names()
    for collection_name in collections:
        await db[collection_name].delete_many({})

    yield

    # Cleanup after test
    for collection_name in collections:
        await db[collection_name].delete_many({})


@pytest.fixture
async def async_client(db_cleanup):
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def admin_user(db_cleanup):
    """Create an admin user for testing."""
    from app.core.security import get_password_hash
    from app.api.models.user import UserRole

    user_data = {
        "username": "test_admin",
        "email": "admin@test.com",
        "full_name": "Test Admin",
        "password_hash": get_password_hash("testpass123"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "permissions": [
            "system:admin", "user:read", "user:write", "user:delete",
            "asset:read", "asset:write", "asset:delete",
            "task:read", "task:write", "task:delete", "task:execute",
            "vulnerability:read", "vulnerability:write", "vulnerability:verify",
            "report:read", "report:write", "report:delete"
        ]
    }

    user = User(**user_data)
    await user.create()
    return user


@pytest.fixture
async def test_user(db_cleanup):
    """Create a regular user for testing."""
    from app.core.security import get_password_hash
    from app.api.models.user import UserRole

    user_data = {
        "username": "test_user",
        "email": "user@test.com",
        "full_name": "Test User",
        "password_hash": get_password_hash("testpass123"),
        "role": UserRole.OPERATOR,
        "is_active": True,
        "permissions": [
            "asset:read", "asset:write",
            "task:read", "task:write", "task:execute",
            "vulnerability:read",
            "report:read"
        ]
    }

    user = User(**user_data)
    await user.create()
    return user


@pytest.fixture
async def auth_headers(async_client, admin_user):
    """Get authentication headers for API requests."""
    login_data = {
        "username": admin_user.username,
        "password": "testpass123"
    }

    response = await async_client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
async def sample_asset(db_cleanup):
    """Create a sample asset for testing."""
    from app.api.models.asset import AssetType, AssetStatus

    asset_data = {
        "name": "Test Website",
        "type": AssetType.URL,
        "value": "https://example.com",
        "status": AssetStatus.ACTIVE,
        "priority": "high",
        "tags": ["test", "web"],
        "department": "IT",
        "description": "Test website asset"
    }

    asset = Asset(**asset_data)
    await asset.create()
    return asset


@pytest.fixture
async def sample_task(db_cleanup, sample_asset):
    """Create a sample task for testing."""
    from app.api.models.task import TaskType, TaskStatus

    task_data = {
        "name": "Test Scan Task",
        "type": TaskType.PORT_SCAN,
        "status": TaskStatus.PENDING,
        "priority": "medium",
        "target_assets": [str(sample_asset.id)],
        "description": "Test scanning task",
        "config": {
            "port_range": "80,443",
            "scan_speed": "3",
            "concurrency": 5
        }
    }

    task = Task(**task_data)
    await task.create()
    return task


@pytest.fixture
async def sample_vulnerability(db_cleanup, sample_asset, sample_task):
    """Create a sample vulnerability for testing."""
    from app.api.models.vulnerability import VulnerabilitySeverity, VulnerabilityStatus

    vuln_data = {
        "name": "Test Vulnerability",
        "description": "Test vulnerability description",
        "severity": VulnerabilitySeverity.HIGH,
        "cvss_score": 7.5,
        "asset_id": str(sample_asset.id),
        "asset_name": sample_asset.name,
        "task_id": str(sample_task.id),
        "task_name": sample_task.name,
        "status": VulnerabilityStatus.OPEN,
        "verified": False,
        "details": {
            "port": 80,
            "evidence": "Test evidence",
            "recommendation": "Test recommendation"
        }
    }

    vulnerability = Vulnerability(**vuln_data)
    await vulnerability.create()
    return vulnerability


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing."""
    from unittest.mock import Mock

    mock_task = Mock()
    mock_task.delay.return_value.id = "test-task-id"
    mock_task.delay.return_value.status = "PENDING"

    return mock_task