#!/usr/bin/env python3
"""
Mock API Server for Frontend Development
Provides realistic API responses without backend dependencies
"""

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from faker import Faker
import uvicorn

fake = Faker()

# Mock data storage
mock_data = {
    "users": [],
    "assets": [],
    "tasks": [],
    "vulnerabilities": [],
    "reports": [],
    "tokens": {}
}


class MockAPIServer:
    def __init__(self):
        self.app = FastAPI(title="Mock API Server", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()
        self.generate_mock_data()
        self.websocket_connections = set()

    def setup_middleware(self):
        """Configure CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.middleware("http")
        async def add_delay(request: Request, call_next):
            """Simulate network latency"""
            delay = random.uniform(0.01, 0.1)  # 10-100ms
            await asyncio.sleep(delay)

            # Randomly fail some requests (1% error rate)
            if random.random() < 0.01:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Random server error for testing"}
                )

            response = await call_next(request)
            return response

    def generate_mock_data(self):
        """Generate realistic mock data"""
        # Generate users
        for i in range(20):
            user = {
                "id": fake.uuid4(),
                "username": fake.user_name(),
                "email": fake.email(),
                "full_name": fake.name(),
                "role": random.choice(["admin", "security_analyst", "operator", "viewer"]),
                "status": random.choice(["active", "inactive"]),
                "permissions": ["read", "write"] if i < 5 else ["read"],
                "is_active": random.choice([True, False]),
                "created_at": fake.date_time_this_year().isoformat(),
                "last_login": fake.date_time_this_month().isoformat()
            }
            mock_data["users"].append(user)

        # Generate assets
        for i in range(100):
            asset = {
                "id": fake.uuid4(),
                "name": fake.domain_name() if i % 2 == 0 else fake.ipv4(),
                "asset_type": random.choice(["domain", "ip", "url"]),
                "status": random.choice(["active", "inactive", "monitoring"]),
                "domain": fake.domain_name() if i % 2 == 0 else None,
                "ip_address": fake.ipv4(),
                "tags": random.sample(["production", "staging", "development", "critical", "web", "database"], k=random.randint(1, 3)),
                "criticality": random.choice(["low", "medium", "high", "critical"]),
                "organization": fake.company(),
                "owner": fake.name(),
                "created_at": fake.date_time_this_year().isoformat(),
                "updated_at": fake.date_time_this_month().isoformat(),
                "last_scan": fake.date_time_this_week().isoformat()
            }
            mock_data["assets"].append(asset)

        # Generate tasks
        for i in range(50):
            task = {
                "id": fake.uuid4(),
                "name": f"Task {i+1}: {fake.catch_phrase()}",
                "type": random.choice(["scan", "monitor", "report", "investigate"]),
                "status": random.choice(["pending", "running", "completed", "failed"]),
                "priority": random.choice(["low", "medium", "high", "critical"]),
                "assigned_to": random.choice(mock_data["users"])["username"],
                "progress": random.randint(0, 100),
                "created_at": fake.date_time_this_month().isoformat(),
                "updated_at": fake.date_time_this_week().isoformat(),
                "eta": fake.future_datetime(end_date="+30d").isoformat()
            }
            mock_data["tasks"].append(task)

        # Generate vulnerabilities
        severities = ["low", "medium", "high", "critical"]
        vuln_types = ["XSS", "SQL Injection", "CSRF", "RCE", "Information Disclosure", "Authentication Bypass"]

        for i in range(75):
            vulnerability = {
                "id": fake.uuid4(),
                "title": f"{random.choice(vuln_types)} in {fake.domain_word()}.{fake.file_extension()}",
                "severity": random.choice(severities),
                "status": random.choice(["open", "in_progress", "resolved", "false_positive"]),
                "asset_id": random.choice(mock_data["assets"])["id"],
                "description": fake.text(max_nb_chars=200),
                "cvss_score": round(random.uniform(0.1, 10.0), 1),
                "cve_id": f"CVE-{fake.year()}-{random.randint(1000, 9999)}",
                "discovered_at": fake.date_time_this_month().isoformat(),
                "updated_at": fake.date_time_this_week().isoformat()
            }
            mock_data["vulnerabilities"].append(vulnerability)

    def setup_routes(self):
        """Setup all mock API routes"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "mode": "mock"
            }

        @self.app.post("/api/v1/auth/login")
        async def login(request: dict):
            """Mock authentication"""
            username = request.get("username")
            password = request.get("password")

            # Accept any credentials in mock mode
            user = next((u for u in mock_data["users"] if u["username"] == username), mock_data["users"][0])

            token = fake.sha256()
            mock_data["tokens"][token] = user

            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": user
            }

        @self.app.get("/api/v1/auth/me")
        async def get_current_user(authorization: Optional[str] = None):
            """Get current user from token"""
            if not authorization:
                raise HTTPException(status_code=401, detail="Not authenticated")

            # Return first user as current user
            return mock_data["users"][0]

        @self.app.get("/api/v1/users/")
        async def get_users(
            page: int = 1,
            size: int = 20,
            search: Optional[str] = None,
            role: Optional[str] = None
        ):
            """Get paginated users list"""
            users = mock_data["users"]

            # Apply filters
            if search:
                users = [u for u in users if search.lower() in u["username"].lower() or search.lower() in u["email"].lower()]
            if role:
                users = [u for u in users if u["role"] == role]

            # Paginate
            start = (page - 1) * size
            end = start + size
            paginated = users[start:end]

            return {
                "items": paginated,
                "total": len(users),
                "page": page,
                "size": size,
                "pages": (len(users) + size - 1) // size
            }

        @self.app.get("/api/v1/assets/")
        async def get_assets(
            page: int = 1,
            size: int = 20,
            search: Optional[str] = None,
            asset_type: Optional[str] = None,
            criticality: Optional[str] = None
        ):
            """Get paginated assets list"""
            assets = mock_data["assets"]

            # Apply filters
            if search:
                assets = [a for a in assets if search.lower() in a["name"].lower()]
            if asset_type:
                assets = [a for a in assets if a["asset_type"] == asset_type]
            if criticality:
                assets = [a for a in assets if a["criticality"] == criticality]

            # Simulate both array and paginated responses
            if random.choice([True, False]):
                # Return array (for compatibility testing)
                return assets[:size]
            else:
                # Return paginated
                start = (page - 1) * size
                end = start + size
                paginated = assets[start:end]

                return {
                    "items": paginated,
                    "total": len(assets),
                    "page": page,
                    "size": size,
                    "pages": (len(assets) + size - 1) // size
                }

        @self.app.post("/api/v1/assets/")
        async def create_asset(asset: dict):
            """Create new asset"""
            new_asset = {
                "id": fake.uuid4(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                **asset
            }
            mock_data["assets"].append(new_asset)
            return new_asset

        @self.app.get("/api/v1/assets/{asset_id}")
        async def get_asset(asset_id: str):
            """Get single asset"""
            asset = next((a for a in mock_data["assets"] if a["id"] == asset_id), None)
            if not asset:
                # Return random asset for testing
                return random.choice(mock_data["assets"])
            return asset

        @self.app.put("/api/v1/assets/{asset_id}")
        async def update_asset(asset_id: str, asset: dict):
            """Update asset"""
            existing = next((a for a in mock_data["assets"] if a["id"] == asset_id), None)
            if existing:
                existing.update(asset)
                existing["updated_at"] = datetime.now().isoformat()
                return existing
            raise HTTPException(status_code=404, detail="Asset not found")

        @self.app.delete("/api/v1/assets/{asset_id}")
        async def delete_asset(asset_id: str):
            """Delete asset"""
            mock_data["assets"] = [a for a in mock_data["assets"] if a["id"] != asset_id]
            return {"message": "Asset deleted"}

        @self.app.get("/api/v1/tasks/")
        async def get_tasks(page: int = 1, size: int = 20):
            """Get tasks list"""
            tasks = mock_data["tasks"]
            start = (page - 1) * size
            end = start + size

            return {
                "items": tasks[start:end],
                "total": len(tasks),
                "page": page,
                "size": size,
                "pages": (len(tasks) + size - 1) // size
            }

        @self.app.get("/api/v1/vulnerabilities/")
        async def get_vulnerabilities(
            page: int = 1,
            size: int = 20,
            severity: Optional[str] = None
        ):
            """Get vulnerabilities list"""
            vulns = mock_data["vulnerabilities"]

            if severity:
                vulns = [v for v in vulns if v["severity"] == severity]

            start = (page - 1) * size
            end = start + size

            return {
                "items": vulns[start:end],
                "total": len(vulns),
                "page": page,
                "size": size,
                "pages": (len(vulns) + size - 1) // size
            }

        @self.app.get("/api/v1/monitoring/metrics")
        async def get_metrics():
            """Get mock metrics"""
            return {
                "uptime_seconds": random.randint(10000, 100000),
                "total_requests": random.randint(10000, 50000),
                "failed_requests": random.randint(10, 100),
                "error_rate": round(random.uniform(0.1, 2.0), 2),
                "requests_per_minute": random.randint(100, 500),
                "avg_response_time_ms": round(random.uniform(50, 200), 2),
                "active_websocket_connections": len(self.websocket_connections),
                "database_connected": True,
                "cache_hit_rate": round(random.uniform(70, 95), 1),
                "cpu_usage": round(random.uniform(10, 50), 1),
                "memory_usage_mb": random.randint(100, 500),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/v1/monitoring/health/detailed")
        async def detailed_health():
            """Get detailed health status"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "database": {
                        "status": "healthy",
                        "type": "postgresql",
                        "connected": True,
                        "latency_ms": round(random.uniform(1, 10), 2)
                    },
                    "cache": {
                        "status": "healthy",
                        "type": "redis",
                        "connected": True,
                        "memory_used_mb": random.randint(10, 100)
                    },
                    "websocket": {
                        "status": "healthy",
                        "active_connections": len(self.websocket_connections)
                    }
                }
            }

        @self.app.websocket("/api/v1/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            """Mock WebSocket endpoint"""
            await websocket.accept()
            self.websocket_connections.add(websocket)

            try:
                # Send initial message
                await websocket.send_json({
                    "type": "connected",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                })

                # Simulate real-time updates
                async def send_updates():
                    while True:
                        await asyncio.sleep(random.uniform(2, 5))

                        # Send random update
                        update_types = ["asset_created", "vulnerability_found", "task_completed", "system_alert"]
                        update = {
                            "type": random.choice(update_types),
                            "data": {
                                "id": fake.uuid4(),
                                "message": fake.sentence(),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        await websocket.send_json(update)

                # Start sending updates
                update_task = asyncio.create_task(send_updates())

                # Handle incoming messages
                while True:
                    data = await websocket.receive_json()

                    if data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif data.get("type") == "subscribe":
                        channel = data.get("channel")
                        await websocket.send_json({
                            "type": "subscribed",
                            "channel": channel
                        })

            except WebSocketDisconnect:
                self.websocket_connections.discard(websocket)
                update_task.cancel()

        # Add chaos engineering endpoints for testing
        @self.app.post("/api/v1/chaos/slow")
        async def simulate_slow_response(delay_seconds: float = 5.0):
            """Simulate slow response"""
            await asyncio.sleep(delay_seconds)
            return {"message": f"Response delayed by {delay_seconds} seconds"}

        @self.app.post("/api/v1/chaos/error")
        async def simulate_error(status_code: int = 500):
            """Simulate error response"""
            raise HTTPException(
                status_code=status_code,
                detail=f"Simulated error with status {status_code}"
            )

        @self.app.post("/api/v1/chaos/flaky")
        async def simulate_flaky_endpoint():
            """Randomly succeed or fail"""
            if random.random() < 0.5:
                raise HTTPException(status_code=500, detail="Random failure")
            return {"message": "Success"}

        @self.app.get("/api/v1/chaos/memory-leak")
        async def simulate_memory_leak():
            """Simulate memory leak"""
            # Allocate memory that won't be freed
            leak = []
            for _ in range(1000000):
                leak.append(random.random())
            return {"message": f"Allocated {len(leak)} items"}

    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the mock server"""
        print("=" * 60)
        print("🎭 Mock API Server")
        print("=" * 60)
        print(f"\nStarting mock server on http://{host}:{port}")
        print("\nFeatures:")
        print("  • Realistic mock data with Faker")
        print("  • Simulated network latency")
        print("  • Random error injection (1%)")
        print("  • WebSocket support")
        print("  • Chaos engineering endpoints")
        print("\nEndpoints:")
        print("  • Health: http://localhost:8001/health")
        print("  • API: http://localhost:8001/api/v1/*")
        print("  • WebSocket: ws://localhost:8001/api/v1/ws/{user_id}")
        print("\nChaos Testing:")
        print("  • Slow: POST /api/v1/chaos/slow?delay_seconds=5")
        print("  • Error: POST /api/v1/chaos/error?status_code=500")
        print("  • Flaky: POST /api/v1/chaos/flaky")
        print("  • Memory Leak: GET /api/v1/chaos/memory-leak")
        print("\n" + "=" * 60)

        uvicorn.run(self.app, host=host, port=port)


def main():
    server = MockAPIServer()
    server.run()


if __name__ == "__main__":
    main()