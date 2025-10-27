#!/usr/bin/env python3
"""
Frontend-Backend Integration Test Script
Tests API compatibility between frontend and backend
"""

import asyncio
import json
import sys
from typing import Dict, List, Any
import httpx
import websockets

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws"

# Test credentials
TEST_USERS = {
    "admin": {"username": "admin", "password": "admin"},
    "analyst": {"username": "analyst", "password": "analyst"},
    "demo": {"username": "demo", "password": "demo"}
}

class IntegrationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.token = None
        self.user = None
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

    async def test_authentication(self):
        """Test authentication flow"""
        print("\n🔐 Testing Authentication...")

        # Test login endpoint
        try:
            response = await self.client.post(
                f"{API_PREFIX}/auth/login",
                json=TEST_USERS["admin"]
            )

            if response.status_code == 200:
                data = response.json()

                # Check expected fields from frontend LoginResponse
                required_fields = ["access_token", "token_type", "expires_in", "user"]
                missing = [f for f in required_fields if f not in data]

                if missing:
                    self.results["failed"].append({
                        "test": "Login Response Fields",
                        "error": f"Missing fields: {missing}",
                        "expected": required_fields,
                        "received": list(data.keys())
                    })
                else:
                    # Check user object fields
                    user_fields = ["id", "username", "email", "full_name", "role", "permissions"]
                    user_missing = [f for f in user_fields if f not in data.get("user", {})]

                    if user_missing:
                        self.results["warnings"].append({
                            "test": "User Object Fields",
                            "warning": f"Missing user fields: {user_missing}",
                            "expected": user_fields,
                            "received": list(data.get("user", {}).keys())
                        })

                    self.token = data["access_token"]
                    self.user = data.get("user")
                    self.client.headers["Authorization"] = f"Bearer {self.token}"

                    self.results["passed"].append({
                        "test": "Authentication",
                        "endpoint": "/auth/login"
                    })

                    print("✅ Authentication successful")
            else:
                self.results["failed"].append({
                    "test": "Authentication",
                    "error": f"Status {response.status_code}: {response.text}"
                })
                print(f"❌ Authentication failed: {response.status_code}")

        except Exception as e:
            self.results["failed"].append({
                "test": "Authentication",
                "error": str(e),
                "hint": "Backend may not be running or database connection failed"
            })
            print(f"❌ Authentication error: {e}")

    async def test_user_endpoints(self):
        """Test user management endpoints"""
        print("\n👤 Testing User Endpoints...")

        if not self.token:
            print("⚠️  Skipping - Authentication required")
            return

        # Test get current user
        try:
            response = await self.client.get(f"{API_PREFIX}/auth/me")
            if response.status_code == 200:
                self.results["passed"].append({
                    "test": "Get Current User",
                    "endpoint": "/auth/me"
                })
                print("✅ Get current user successful")
            else:
                self.results["failed"].append({
                    "test": "Get Current User",
                    "error": f"Status {response.status_code}"
                })
        except Exception as e:
            self.results["failed"].append({
                "test": "Get Current User",
                "error": str(e)
            })

        # Test users list (frontend expects this at /users/)
        try:
            response = await self.client.get(f"{API_PREFIX}/users/")
            if response.status_code == 200:
                data = response.json()

                # Check response format
                if "items" in data and "total" in data:
                    self.results["passed"].append({
                        "test": "List Users",
                        "endpoint": "/users/"
                    })
                    print("✅ List users successful")
                else:
                    self.results["warnings"].append({
                        "test": "List Users Response Format",
                        "warning": "Response format mismatch",
                        "expected": {"items": [], "total": 0},
                        "received": list(data.keys()) if isinstance(data, dict) else "array"
                    })
            else:
                self.results["failed"].append({
                    "test": "List Users",
                    "error": f"Status {response.status_code}"
                })
        except Exception as e:
            self.results["failed"].append({
                "test": "List Users",
                "error": str(e)
            })

    async def test_asset_endpoints(self):
        """Test asset management endpoints"""
        print("\n📦 Testing Asset Endpoints...")

        if not self.token:
            print("⚠️  Skipping - Authentication required")
            return

        # Test list assets
        try:
            response = await self.client.get(f"{API_PREFIX}/assets/")
            if response.status_code == 200:
                data = response.json()

                # Frontend expects array or object with items
                if isinstance(data, list):
                    self.results["passed"].append({
                        "test": "List Assets",
                        "endpoint": "/assets/"
                    })
                    print("✅ List assets successful")
                elif isinstance(data, dict) and "items" in data:
                    self.results["passed"].append({
                        "test": "List Assets (paginated)",
                        "endpoint": "/assets/"
                    })
                    print("✅ List assets (paginated) successful")
                else:
                    self.results["warnings"].append({
                        "test": "List Assets Format",
                        "warning": "Unexpected response format",
                        "received": type(data).__name__
                    })
            else:
                self.results["failed"].append({
                    "test": "List Assets",
                    "error": f"Status {response.status_code}"
                })
        except Exception as e:
            self.results["failed"].append({
                "test": "List Assets",
                "error": str(e)
            })

        # Test create asset
        test_asset = {
            "name": "test-asset.example.com",
            "asset_type": "domain",
            "domain": "test-asset.example.com",
            "tags": ["test"],
            "criticality": "medium"
        }

        try:
            response = await self.client.post(
                f"{API_PREFIX}/assets/",
                json=test_asset
            )
            if response.status_code in [200, 201]:
                created_asset = response.json()
                self.results["passed"].append({
                    "test": "Create Asset",
                    "endpoint": "/assets/"
                })
                print("✅ Create asset successful")

                # Test get single asset
                if "id" in created_asset:
                    asset_id = created_asset["id"]
                    response = await self.client.get(f"{API_PREFIX}/assets/{asset_id}")
                    if response.status_code == 200:
                        self.results["passed"].append({
                            "test": "Get Asset",
                            "endpoint": f"/assets/{asset_id}"
                        })
                        print("✅ Get asset successful")

                    # Clean up - delete test asset
                    await self.client.delete(f"{API_PREFIX}/assets/{asset_id}")
            else:
                self.results["failed"].append({
                    "test": "Create Asset",
                    "error": f"Status {response.status_code}: {response.text}"
                })
        except Exception as e:
            self.results["failed"].append({
                "test": "Create Asset",
                "error": str(e)
            })

    async def test_websocket_connection(self):
        """Test WebSocket connectivity"""
        print("\n🔌 Testing WebSocket Connection...")

        if not self.token:
            print("⚠️  Skipping - Authentication required")
            return

        try:
            # Frontend connects with user_id and optional token
            ws_url = f"{WS_URL}/{self.user['id']}?token={self.token}"

            async with websockets.connect(ws_url) as websocket:
                # Test ping-pong
                await websocket.send(json.dumps({"type": "ping"}))

                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=5.0
                )
                data = json.loads(response)

                if data.get("type") == "pong":
                    self.results["passed"].append({
                        "test": "WebSocket Connection",
                        "endpoint": "/ws/{user_id}"
                    })
                    print("✅ WebSocket connection successful")
                else:
                    self.results["warnings"].append({
                        "test": "WebSocket Response",
                        "warning": f"Unexpected response: {data}"
                    })

        except asyncio.TimeoutError:
            self.results["failed"].append({
                "test": "WebSocket Connection",
                "error": "Connection timeout"
            })
            print("❌ WebSocket timeout")
        except Exception as e:
            self.results["failed"].append({
                "test": "WebSocket Connection",
                "error": str(e),
                "hint": "WebSocket authentication may not be implemented"
            })
            print(f"❌ WebSocket error: {e}")

    async def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Configuration...")

        try:
            # Simulate frontend request from localhost:3000
            response = await self.client.options(
                f"{API_PREFIX}/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )

            cors_headers = {
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            }

            missing = [h for h in cors_headers if h not in response.headers]

            if not missing:
                self.results["passed"].append({
                    "test": "CORS Headers",
                    "headers": list(cors_headers)
                })
                print("✅ CORS properly configured")
            else:
                self.results["failed"].append({
                    "test": "CORS Headers",
                    "error": f"Missing headers: {missing}"
                })
                print(f"❌ Missing CORS headers: {missing}")

        except Exception as e:
            self.results["failed"].append({
                "test": "CORS Configuration",
                "error": str(e)
            })

    async def test_error_responses(self):
        """Test error response formats"""
        print("\n⚠️  Testing Error Response Formats...")

        # Test 404 response
        try:
            response = await self.client.get(f"{API_PREFIX}/nonexistent")
            if response.status_code == 404:
                data = response.json()
                if "detail" in data:
                    self.results["passed"].append({
                        "test": "404 Error Format",
                        "format": "FastAPI standard"
                    })
                    print("✅ Error format consistent")
                else:
                    self.results["warnings"].append({
                        "test": "404 Error Format",
                        "warning": "Non-standard error format",
                        "received": list(data.keys())
                    })
        except Exception:
            pass

    async def test_data_model_compatibility(self):
        """Test data model compatibility between frontend and backend"""
        print("\n🔄 Testing Data Model Compatibility...")

        issues = []

        # Check User model
        if self.user:
            frontend_user_fields = {
                "id", "username", "email", "full_name", "role", "permissions"
            }
            backend_user_fields = set(self.user.keys())

            missing_in_backend = frontend_user_fields - backend_user_fields
            if missing_in_backend:
                issues.append({
                    "model": "User",
                    "missing_fields": list(missing_in_backend),
                    "severity": "high"
                })

        # Check Asset model (if we have test data)
        try:
            response = await self.client.get(f"{API_PREFIX}/assets/", params={"limit": 1})
            if response.status_code == 200:
                data = response.json()
                assets = data if isinstance(data, list) else data.get("items", [])

                if assets:
                    asset = assets[0]
                    frontend_asset_fields = {
                        "id", "name", "asset_type", "status", "domain",
                        "ip_address", "tags", "criticality"
                    }
                    backend_asset_fields = set(asset.keys())

                    missing_in_backend = frontend_asset_fields - backend_asset_fields
                    if missing_in_backend:
                        issues.append({
                            "model": "Asset",
                            "missing_fields": list(missing_in_backend),
                            "severity": "medium"
                        })
        except Exception:
            pass

        if issues:
            for issue in issues:
                self.results["warnings"].append({
                    "test": f"{issue['model']} Model Compatibility",
                    "warning": f"Missing fields: {issue['missing_fields']}",
                    "severity": issue['severity']
                })
            print(f"⚠️  Found {len(issues)} model compatibility issues")
        else:
            self.results["passed"].append({
                "test": "Data Model Compatibility"
            })
            print("✅ Data models compatible")

    async def run_all_tests(self):
        """Run all integration tests"""
        print("=" * 60)
        print("🚀 Starting Frontend-Backend Integration Tests")
        print("=" * 60)

        await self.test_authentication()
        await self.test_user_endpoints()
        await self.test_asset_endpoints()
        await self.test_websocket_connection()
        await self.test_cors_headers()
        await self.test_error_responses()
        await self.test_data_model_compatibility()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)

        print(f"\n✅ Passed: {len(self.results['passed'])} tests")
        for test in self.results['passed']:
            print(f"   • {test['test']}")

        if self.results['warnings']:
            print(f"\n⚠️  Warnings: {len(self.results['warnings'])} issues")
            for warning in self.results['warnings']:
                print(f"   • {warning['test']}: {warning.get('warning', '')}")

        if self.results['failed']:
            print(f"\n❌ Failed: {len(self.results['failed'])} tests")
            for failure in self.results['failed']:
                print(f"   • {failure['test']}: {failure['error']}")
                if "hint" in failure:
                    print(f"     💡 Hint: {failure['hint']}")

        # Generate recommendations
        print("\n" + "=" * 60)
        print("🔧 Recommendations")
        print("=" * 60)

        self.generate_recommendations()

        # Save detailed report
        with open("integration_test_report.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print("\n📄 Detailed report saved to: integration_test_report.json")

        await self.client.aclose()

        # Return exit code
        return 0 if not self.results['failed'] else 1

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []

        # Check for database issues
        auth_failed = any(f['test'] == 'Authentication' for f in self.results['failed'])
        if auth_failed:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": "Authentication failing",
                "fixes": [
                    "1. Ensure backend is running: cd backend && python -m uvicorn app.main:app --reload",
                    "2. Check database connection in backend/app/core/config.py",
                    "3. Verify DATABASE_URL in .env file",
                    "4. Fix SQLAlchemy/MongoDB mismatch in user endpoints"
                ]
            })

        # Check for WebSocket issues
        ws_failed = any(f['test'] == 'WebSocket Connection' for f in self.results['failed'])
        if ws_failed:
            recommendations.append({
                "priority": "HIGH",
                "issue": "WebSocket authentication not implemented",
                "fixes": [
                    "1. Implement token validation in backend/app/api/endpoints/websocket_endpoint.py:28",
                    "2. Validate JWT token in WebSocket connection",
                    "3. Add proper user authentication check"
                ]
            })

        # Check for CORS issues
        cors_failed = any(f['test'] == 'CORS Headers' for f in self.results['failed'])
        if cors_failed:
            recommendations.append({
                "priority": "HIGH",
                "issue": "CORS configuration issues",
                "fixes": [
                    "1. Update BACKEND_CORS_ORIGINS in backend/app/core/config.py",
                    "2. Ensure frontend URL (http://localhost:3000) is in allowed origins",
                    "3. Restart backend after configuration changes"
                ]
            })

        # Check for model compatibility
        model_warnings = [w for w in self.results['warnings'] if 'Model Compatibility' in w['test']]
        if model_warnings:
            recommendations.append({
                "priority": "MEDIUM",
                "issue": "Data model mismatches between frontend and backend",
                "fixes": [
                    "1. Update backend schemas to include all required fields",
                    "2. Ensure response serialization includes all expected fields",
                    "3. Consider using TypeScript interfaces generated from OpenAPI spec"
                ]
            })

        # Print recommendations
        for rec in recommendations:
            print(f"\n🔴 {rec['priority']}: {rec['issue']}")
            for fix in rec['fixes']:
                print(f"   {fix}")

        if not recommendations:
            print("\n✅ No critical issues found! The frontend and backend are well integrated.")

async def main():
    """Main function"""
    tester = IntegrationTester()

    try:
        exit_code = await tester.run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔧 Frontend-Backend Integration Tester")
    print("Make sure the backend is running on http://localhost:8000")
    print("Press Ctrl+C to stop\n")

    asyncio.run(main())