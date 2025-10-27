"""
Load Testing Configuration using Locust
Tests API performance under various load conditions
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import json
import random
import time
from datetime import datetime


class SOCPlatformUser(HttpUser):
    """
    Simulates a user interacting with the SOC Platform
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = "http://localhost:8000"

    def on_start(self):
        """Called when a simulated user starts"""
        # Authenticate and get token
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": random.choice(["admin", "analyst", "demo"]),
                "password": random.choice(["admin", "analyst", "demo"])
            },
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id", "test-user")

            # Set authorization header for all subsequent requests
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")
            self.token = None
            self.user_id = None

    @task(10)
    def view_assets(self):
        """View assets list - most common operation"""
        with self.client.get(
            "/api/v1/assets/",
            catch_response=True,
            name="GET /assets/"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(5)
    def view_single_asset(self):
        """View single asset details"""
        # First get list to get an ID
        response = self.client.get("/api/v1/assets/", catch_response=True)
        if response.status_code == 200:
            data = response.json()
            assets = data if isinstance(data, list) else data.get("items", [])

            if assets:
                asset = random.choice(assets)
                asset_id = asset.get("id")

                with self.client.get(
                    f"/api/v1/assets/{asset_id}",
                    catch_response=True,
                    name="GET /assets/{id}"
                ) as detail_response:
                    if detail_response.status_code == 200:
                        detail_response.success()
                    else:
                        detail_response.failure(f"Status {detail_response.status_code}")

    @task(3)
    def create_asset(self):
        """Create a new asset"""
        asset_data = {
            "name": f"load-test-{random.randint(1000, 9999)}.example.com",
            "asset_type": random.choice(["domain", "ip", "url"]),
            "tags": ["load-test"],
            "criticality": random.choice(["low", "medium", "high", "critical"])
        }

        with self.client.post(
            "/api/v1/assets/",
            json=asset_data,
            catch_response=True,
            name="POST /assets/"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
                # Store created asset ID for potential deletion
                data = response.json()
                self.created_asset_id = data.get("id")
            else:
                response.failure(f"Status {response.status_code}")

    @task(8)
    def view_users(self):
        """View users list"""
        with self.client.get(
            "/api/v1/users/",
            catch_response=True,
            name="GET /users/"
        ) as response:
            if response.status_code in [200, 403]:  # 403 for non-admin users
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(4)
    def get_current_user(self):
        """Get current user profile"""
        with self.client.get(
            "/api/v1/auth/me",
            catch_response=True,
            name="GET /auth/me"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def view_tasks(self):
        """View tasks list"""
        with self.client.get(
            "/api/v1/tasks/",
            catch_response=True,
            name="GET /tasks/"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def view_vulnerabilities(self):
        """View vulnerabilities list"""
        with self.client.get(
            "/api/v1/vulnerabilities/",
            catch_response=True,
            name="GET /vulnerabilities/"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def search_assets(self):
        """Search for assets"""
        search_terms = ["test", "example", "domain", "web", "server"]
        search = random.choice(search_terms)

        with self.client.get(
            f"/api/v1/assets/?search={search}",
            catch_response=True,
            name="GET /assets/?search="
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def health_check(self):
        """Check system health"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class WebSocketUser(HttpUser):
    """
    Simulates WebSocket connections
    """
    wait_time = between(5, 10)
    host = "ws://localhost:8000"

    def on_start(self):
        """Establish WebSocket connection"""
        # Get auth token first
        response = self.client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"username": "demo", "password": "demo"}
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id", "test-user")

    @task
    def websocket_ping(self):
        """Send WebSocket ping"""
        # Note: Locust doesn't natively support WebSocket
        # This is a placeholder for WebSocket testing
        # Consider using locust-plugins for WebSocket support
        pass


class AdminUser(HttpUser):
    """
    Simulates admin user performing administrative tasks
    """
    wait_time = between(2, 5)
    host = "http://localhost:8000"

    def on_start(self):
        """Authenticate as admin"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.token}"
            response.success()

    @task(5)
    def manage_users(self):
        """User management operations"""
        with self.client.get("/api/v1/users/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()

    @task(3)
    def view_system_metrics(self):
        """View system metrics"""
        with self.client.get(
            "/api/v1/monitoring/metrics",
            catch_response=True,
            name="GET /monitoring/metrics"
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(2)
    def generate_report(self):
        """Generate system report"""
        with self.client.post(
            "/api/v1/reports/",
            json={"type": "system", "format": "pdf"},
            catch_response=True,
            name="POST /reports/"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()

    @task(1)
    def system_settings(self):
        """View system settings"""
        with self.client.get(
            "/api/v1/settings/",
            catch_response=True,
            name="GET /settings/"
        ) as response:
            if response.status_code == 200:
                response.success()


class MixedLoadUser(HttpUser):
    """
    Simulates mixed user behavior patterns
    """
    wait_time = between(0.5, 2)
    host = "http://localhost:8000"

    user_types = [
        {"username": "admin", "password": "admin", "weight": 0.1},
        {"username": "analyst", "password": "analyst", "weight": 0.3},
        {"username": "demo", "password": "demo", "weight": 0.6}
    ]

    def on_start(self):
        """Random user authentication"""
        # Select user type based on weights
        user_type = random.choices(
            self.user_types,
            weights=[u["weight"] for u in self.user_types]
        )[0]

        response = self.client.post(
            "/api/v1/auth/login",
            json={"username": user_type["username"], "password": user_type["password"]}
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_role = data.get("user", {}).get("role", "viewer")
            self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(20)
    def read_operations(self):
        """Perform read operations (80% of traffic)"""
        endpoints = [
            "/api/v1/assets/",
            "/api/v1/users/",
            "/api/v1/tasks/",
            "/api/v1/vulnerabilities/",
            "/health"
        ]

        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name=f"READ {endpoint}")

    @task(5)
    def write_operations(self):
        """Perform write operations (20% of traffic)"""
        operations = [
            {
                "method": "POST",
                "endpoint": "/api/v1/assets/",
                "data": {
                    "name": f"mixed-test-{random.randint(1000, 9999)}.com",
                    "asset_type": "domain"
                }
            },
            {
                "method": "POST",
                "endpoint": "/api/v1/tasks/",
                "data": {
                    "name": f"Task {random.randint(1000, 9999)}",
                    "type": "scan",
                    "status": "pending"
                }
            }
        ]

        operation = random.choice(operations)

        if operation["method"] == "POST":
            self.client.post(
                operation["endpoint"],
                json=operation["data"],
                name=f"WRITE {operation['endpoint']}"
            )


# Custom event handlers for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("=" * 60)
    print(f"Load Test Started: {datetime.now().isoformat()}")
    print(f"Target Host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("=" * 60)
    print(f"Load Test Completed: {datetime.now().isoformat()}")
    print("=" * 60)

    # Generate summary report
    if environment.stats:
        print("\nTest Summary:")
        print(f"Total Requests: {environment.stats.total.num_requests}")
        print(f"Total Failures: {environment.stats.total.num_failures}")
        print(f"Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
        print(f"Median Response Time: {environment.stats.total.median_response_time:.2f}ms")
        print(f"95% Response Time: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"99% Response Time: {environment.stats.total.get_response_time_percentile(0.99):.2f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called for each request"""
    if exception:
        print(f"Request Failed: {name} - {exception}")


# Configuration for different test scenarios
class StressTestUser(SOCPlatformUser):
    """Stress test with no wait time"""
    wait_time = between(0, 0.1)


class SpikeTestUser(SOCPlatformUser):
    """Spike test with sudden load increases"""
    wait_time = between(0, 0.5)


class EnduranceTestUser(SOCPlatformUser):
    """Endurance test with steady load"""
    wait_time = between(2, 4)


# Custom shapes for advanced load patterns
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern:
    Gradually increase users in steps
    """
    step_time = 30  # Time for each step (seconds)
    step_users = 10  # Users to add per step
    max_users = 100

    def tick(self):
        run_time = self.get_run_time()
        current_step = run_time // self.step_time
        target_users = min(self.max_users, (current_step + 1) * self.step_users)
        return (target_users, self.step_users)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern:
    Normal load with periodic spikes
    """
    time_limit = 300  # 5 minutes total
    normal_users = 20
    spike_users = 100

    def tick(self):
        run_time = self.get_run_time()

        if run_time < self.time_limit:
            # Spike every 60 seconds for 10 seconds
            if run_time % 60 < 10:
                return (self.spike_users, 50)  # Rapid spawn during spike
            else:
                return (self.normal_users, 5)
        else:
            return None


# Usage Instructions
"""
Run load tests with:

1. Basic load test:
   locust -f locustfile.py --host=http://localhost:8000

2. Headless mode:
   locust -f locustfile.py --headless -u 50 -r 5 -t 60s --host=http://localhost:8000

3. With web UI:
   locust -f locustfile.py --host=http://localhost:8000
   Then open: http://localhost:8089

4. Specific user class:
   locust -f locustfile.py --host=http://localhost:8000 --class SOCPlatformUser

5. Step load pattern:
   locust -f locustfile.py --host=http://localhost:8000 --class StepLoadShape

6. Generate HTML report:
   locust -f locustfile.py --headless -u 100 -r 10 -t 300s --html report.html

Parameters:
  -u: Number of users
  -r: Spawn rate (users per second)
  -t: Test duration
  --html: Generate HTML report
  --csv: Generate CSV data
"""