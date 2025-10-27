import pytest
from httpx import AsyncClient
from app.api.models.asset import Asset, AssetType, AssetStatus


class TestAssets:
    """Test asset management endpoints."""

    async def test_create_asset(self, async_client: AsyncClient, auth_headers):
        """Test creating a new asset."""
        asset_data = {
            "name": "Test Asset",
            "type": "url",
            "value": "https://test.example.com",
            "priority": "high",
            "tags": ["test", "web"],
            "department": "IT",
            "description": "Test asset description"
        }

        response = await async_client.post("/api/assets", json=asset_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == asset_data["name"]
        assert data["type"] == asset_data["type"]
        assert data["value"] == asset_data["value"]
        assert data["status"] == "active"

    async def test_create_asset_duplicate_value(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test creating asset with duplicate value."""
        asset_data = {
            "name": "Duplicate Asset",
            "type": "url",
            "value": sample_asset.value,  # Same value as existing asset
            "priority": "medium"
        }

        response = await async_client.post("/api/assets", json=asset_data, headers=auth_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_get_assets(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test getting asset list."""
        response = await async_client.get("/api/assets", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        # Check if sample asset is in the list
        asset_ids = [item["id"] for item in data["items"]]
        assert str(sample_asset.id) in asset_ids

    async def test_get_assets_with_filters(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test getting assets with filters."""
        # Filter by type
        response = await async_client.get(
            f"/api/assets?type={sample_asset.type}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert all(item["type"] == sample_asset.type for item in data["items"])

        # Filter by status
        response = await async_client.get(
            f"/api/assets?status={sample_asset.status}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert all(item["status"] == sample_asset.status for item in data["items"])

    async def test_get_asset_by_id(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test getting a specific asset by ID."""
        response = await async_client.get(
            f"/api/assets/{sample_asset.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(sample_asset.id)
        assert data["name"] == sample_asset.name
        assert data["value"] == sample_asset.value

    async def test_get_asset_not_found(self, async_client: AsyncClient, auth_headers):
        """Test getting nonexistent asset."""
        from bson import ObjectId
        fake_id = str(ObjectId())

        response = await async_client.get(f"/api/assets/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_update_asset(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test updating an asset."""
        update_data = {
            "name": "Updated Asset Name",
            "description": "Updated description",
            "priority": "critical"
        }

        response = await async_client.put(
            f"/api/assets/{sample_asset.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]

    async def test_delete_asset(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test deleting an asset."""
        response = await async_client.delete(
            f"/api/assets/{sample_asset.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # Verify asset is deleted
        get_response = await async_client.get(
            f"/api/assets/{sample_asset.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_bulk_create_assets(self, async_client: AsyncClient, auth_headers):
        """Test bulk creating assets."""
        assets_data = [
            {
                "name": "Bulk Asset 1",
                "type": "ip",
                "value": "192.168.1.1",
                "priority": "medium"
            },
            {
                "name": "Bulk Asset 2",
                "type": "domain",
                "value": "test1.example.com",
                "priority": "low"
            }
        ]

        response = await async_client.post(
            "/api/assets/bulk",
            json={"assets": assets_data},
            headers=auth_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == assets_data[0]["name"]
        assert data[1]["name"] == assets_data[1]["name"]

    async def test_scan_asset(self, async_client: AsyncClient, auth_headers, sample_asset, mock_celery_task):
        """Test triggering asset scan."""
        response = await async_client.post(
            f"/api/assets/{sample_asset.id}/scan",
            headers=auth_headers
        )
        assert response.status_code == 202
        assert "task_id" in response.json()

    async def test_asset_unauthorized(self, async_client: AsyncClient):
        """Test asset operations without authentication."""
        response = await async_client.get("/api/assets")
        assert response.status_code == 401

        response = await async_client.post("/api/assets", json={})
        assert response.status_code == 401