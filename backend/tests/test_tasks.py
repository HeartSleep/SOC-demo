import pytest
from httpx import AsyncClient
from unittest.mock import patch, Mock


class TestTasks:
    """Test task management endpoints."""

    async def test_create_task(self, async_client: AsyncClient, auth_headers, sample_asset):
        """Test creating a new task."""
        task_data = {
            "name": "Test Scan Task",
            "type": "port_scan",
            "priority": "high",
            "target_assets": [str(sample_asset.id)],
            "description": "Test scanning task",
            "config": {
                "port_range": "80,443",
                "scan_speed": "3",
                "concurrency": 5
            }
        }

        response = await async_client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == task_data["name"]
        assert data["type"] == task_data["type"]
        assert data["status"] == "pending"
        assert data["target_assets"] == task_data["target_assets"]

    async def test_get_tasks(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test getting task list."""
        response = await async_client.get("/api/tasks", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

        # Check if sample task is in the list
        task_ids = [item["id"] for item in data["items"]]
        assert str(sample_task.id) in task_ids

    async def test_get_tasks_with_filters(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test getting tasks with filters."""
        # Filter by status
        response = await async_client.get(
            f"/api/tasks?status={sample_task.status}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert all(item["status"] == sample_task.status for item in data["items"])

        # Filter by type
        response = await async_client.get(
            f"/api/tasks?type={sample_task.type}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert all(item["type"] == sample_task.type for item in data["items"])

    async def test_get_task_by_id(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test getting a specific task by ID."""
        response = await async_client.get(
            f"/api/tasks/{sample_task.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(sample_task.id)
        assert data["name"] == sample_task.name
        assert data["type"] == sample_task.type

    async def test_update_task(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test updating a task."""
        update_data = {
            "name": "Updated Task Name",
            "description": "Updated description",
            "priority": "critical"
        }

        response = await async_client.put(
            f"/api/tasks/{sample_task.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]

    async def test_delete_task(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test deleting a task."""
        response = await async_client.delete(
            f"/api/tasks/{sample_task.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # Verify task is deleted
        get_response = await async_client.get(
            f"/api/tasks/{sample_task.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    @patch('app.core.celery.tasks.scan_tasks.port_scan_task.delay')
    async def test_start_task(self, mock_celery, async_client: AsyncClient, auth_headers, sample_task):
        """Test starting a task."""
        mock_celery.return_value.id = "test-celery-task-id"

        response = await async_client.post(
            f"/api/tasks/{sample_task.id}/start",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Task started successfully"
        assert "celery_task_id" in data

        # Verify task status is updated
        get_response = await async_client.get(
            f"/api/tasks/{sample_task.id}",
            headers=auth_headers
        )
        task_data = get_response.json()
        assert task_data["status"] == "running"

    async def test_stop_task(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test stopping a running task."""
        # First set task to running status
        sample_task.status = "running"
        sample_task.celery_task_id = "test-task-id"
        await sample_task.save()

        with patch('app.core.celery.celery_app.control.revoke') as mock_revoke:
            response = await async_client.post(
                f"/api/tasks/{sample_task.id}/stop",
                headers=auth_headers
            )
            assert response.status_code == 200

            data = response.json()
            assert data["message"] == "Task stopped successfully"

            # Verify revoke was called
            mock_revoke.assert_called_once()

    async def test_restart_task(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test restarting a failed task."""
        # Set task to failed status
        sample_task.status = "failed"
        await sample_task.save()

        with patch('app.core.celery.tasks.scan_tasks.port_scan_task.delay') as mock_celery:
            mock_celery.return_value.id = "new-celery-task-id"

            response = await async_client.post(
                f"/api/tasks/{sample_task.id}/restart",
                headers=auth_headers
            )
            assert response.status_code == 200

            data = response.json()
            assert data["message"] == "Task restarted successfully"

    async def test_get_task_logs(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test getting task logs."""
        response = await async_client.get(
            f"/api/tasks/{sample_task.id}/logs",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    async def test_get_task_results(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test getting task results."""
        response = await async_client.get(
            f"/api/tasks/{sample_task.id}/results",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "results" in data

    async def test_clone_task(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test cloning a task."""
        response = await async_client.post(
            f"/api/tasks/{sample_task.id}/clone",
            headers=auth_headers
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] != sample_task.name  # Should have different name
        assert data["type"] == sample_task.type
        assert data["status"] == "pending"

    async def test_bulk_operations(self, async_client: AsyncClient, auth_headers, sample_task):
        """Test bulk task operations."""
        task_ids = [str(sample_task.id)]

        # Test bulk stop
        with patch('app.core.celery.celery_app.control.revoke'):
            response = await async_client.post(
                "/api/tasks/bulk-stop",
                json={"ids": task_ids},
                headers=auth_headers
            )
            assert response.status_code == 200

        # Test bulk delete
        response = await async_client.delete(
            "/api/tasks/bulk",
            json={"ids": task_ids},
            headers=auth_headers
        )
        assert response.status_code == 204