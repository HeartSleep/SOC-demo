#!/usr/bin/env python3
"""
Frontend-Backend Contract Tests
Ensures API contracts remain consistent between frontend and backend
"""

import asyncio
import json
from typing import Dict, List, Any
import httpx
from jsonschema import validate, ValidationError
import yaml
from pathlib import Path

# API Contract Schemas
CONTRACTS = {
    "LoginRequest": {
        "type": "object",
        "required": ["username", "password"],
        "properties": {
            "username": {"type": "string", "minLength": 1},
            "password": {"type": "string", "minLength": 1}
        }
    },
    "LoginResponse": {
        "type": "object",
        "required": ["access_token", "token_type", "expires_in", "user"],
        "properties": {
            "access_token": {"type": "string"},
            "token_type": {"type": "string"},
            "expires_in": {"type": "number"},
            "user": {
                "type": "object",
                "required": ["id", "username", "email", "full_name", "role"],
                "properties": {
                    "id": {"type": "string"},
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "full_name": {"type": "string"},
                    "role": {"type": "string"},
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    },
    "UserResponse": {
        "type": "object",
        "required": ["id", "username", "email", "full_name", "role"],
        "properties": {
            "id": {"type": "string"},
            "username": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "full_name": {"type": "string"},
            "role": {"type": "string"},
            "status": {"type": "string"},
            "permissions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "is_active": {"type": "boolean"},
            "is_verified": {"type": "boolean"}
        }
    },
    "AssetResponse": {
        "type": "object",
        "required": ["id", "name", "asset_type"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "asset_type": {"type": "string", "enum": ["domain", "ip", "url"]},
            "status": {"type": "string"},
            "domain": {"type": ["string", "null"]},
            "ip_address": {"type": ["string", "null"]},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            },
            "criticality": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"]
            }
        }
    },
    "PaginatedResponse": {
        "type": "object",
        "required": ["items", "total", "page", "size", "pages"],
        "properties": {
            "items": {"type": "array"},
            "total": {"type": "number"},
            "page": {"type": "number"},
            "size": {"type": "number"},
            "pages": {"type": "number"}
        }
    },
    "ErrorResponse": {
        "type": "object",
        "required": ["detail"],
        "properties": {
            "detail": {"type": "string"},
            "status": {"type": "number"},
            "errors": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
}


class ContractTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.token = None
        self.test_results = []

    async def test_contract(self, name: str, endpoint: str, method: str,
                          request_data: Any = None,
                          response_schema: str = None,
                          expected_status: List[int] = [200]):
        """Test a single API contract"""
        print(f"\n🧪 Testing {name}...")

        try:
            # Prepare headers
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            # Make request
            if method == "GET":
                response = await self.client.get(endpoint, headers=headers)
            elif method == "POST":
                response = await self.client.post(endpoint, json=request_data, headers=headers)
            elif method == "PUT":
                response = await self.client.put(endpoint, json=request_data, headers=headers)
            elif method == "DELETE":
                response = await self.client.delete(endpoint, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check status code
            if response.status_code not in expected_status:
                self.test_results.append({
                    "test": name,
                    "passed": False,
                    "error": f"Expected status {expected_status}, got {response.status_code}",
                    "response": response.text
                })
                print(f"  ❌ Status code mismatch: {response.status_code}")
                return False

            # Validate response schema
            if response_schema and response.status_code < 400:
                try:
                    response_data = response.json()

                    # Handle both direct responses and paginated responses
                    if response_schema == "AssetResponse" and isinstance(response_data, list):
                        # Validate each item in the list
                        for item in response_data:
                            validate(item, CONTRACTS[response_schema])
                    elif response_schema == "PaginatedResponse":
                        # Validate pagination structure
                        validate(response_data, CONTRACTS[response_schema])
                        # Also validate items if specified
                        if "items" in response_data and len(response_data["items"]) > 0:
                            # Infer item schema from endpoint
                            if "users" in endpoint:
                                for item in response_data["items"]:
                                    validate(item, CONTRACTS["UserResponse"])
                            elif "assets" in endpoint:
                                for item in response_data["items"]:
                                    validate(item, CONTRACTS["AssetResponse"])
                    else:
                        validate(response_data, CONTRACTS[response_schema])

                    self.test_results.append({
                        "test": name,
                        "passed": True,
                        "message": "Contract validated successfully"
                    })
                    print(f"  ✅ Contract validated")
                    return True

                except ValidationError as e:
                    self.test_results.append({
                        "test": name,
                        "passed": False,
                        "error": f"Schema validation failed: {str(e)}",
                        "expected_schema": CONTRACTS[response_schema],
                        "received_data": response_data
                    })
                    print(f"  ❌ Schema validation failed: {e.message}")
                    return False

                except json.JSONDecodeError as e:
                    self.test_results.append({
                        "test": name,
                        "passed": False,
                        "error": f"Invalid JSON response: {str(e)}"
                    })
                    print(f"  ❌ Invalid JSON response")
                    return False

            # For error responses, validate error schema
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    validate(error_data, CONTRACTS["ErrorResponse"])
                    self.test_results.append({
                        "test": name,
                        "passed": True,
                        "message": "Error response format correct"
                    })
                    print(f"  ✅ Error response validated")
                    return True
                except:
                    self.test_results.append({
                        "test": name,
                        "passed": False,
                        "error": "Error response doesn't match schema"
                    })
                    print(f"  ❌ Error response format invalid")
                    return False

            # No schema validation needed
            self.test_results.append({
                "test": name,
                "passed": True,
                "message": f"Request successful: {response.status_code}"
            })
            print(f"  ✅ Request successful")
            return True

        except Exception as e:
            self.test_results.append({
                "test": name,
                "passed": False,
                "error": str(e)
            })
            print(f"  ❌ Test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all contract tests"""
        print("=" * 60)
        print("🔍 Frontend-Backend Contract Tests")
        print("=" * 60)

        # Test 1: Authentication Contract
        auth_result = await self.test_contract(
            name="Authentication Contract",
            endpoint="/api/v1/auth/login",
            method="POST",
            request_data={"username": "admin", "password": "admin"},
            response_schema="LoginResponse",
            expected_status=[200]
        )

        if auth_result:
            # Extract token for subsequent tests
            response = await self.client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "admin"}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")

        # Test 2: Get Current User Contract
        await self.test_contract(
            name="Get Current User Contract",
            endpoint="/api/v1/auth/me",
            method="GET",
            response_schema="UserResponse",
            expected_status=[200, 401]
        )

        # Test 3: List Users Contract
        await self.test_contract(
            name="List Users Contract",
            endpoint="/api/v1/users/",
            method="GET",
            response_schema="PaginatedResponse",
            expected_status=[200, 403]
        )

        # Test 4: List Assets Contract
        await self.test_contract(
            name="List Assets Contract",
            endpoint="/api/v1/assets/",
            method="GET",
            response_schema="AssetResponse",  # Can be array or paginated
            expected_status=[200]
        )

        # Test 5: Create Asset Contract
        await self.test_contract(
            name="Create Asset Contract",
            endpoint="/api/v1/assets/",
            method="POST",
            request_data={
                "name": "test-contract-asset.com",
                "asset_type": "domain",
                "domain": "test-contract-asset.com",
                "tags": ["test"],
                "criticality": "medium"
            },
            response_schema="AssetResponse",
            expected_status=[200, 201]
        )

        # Test 6: Error Response Contract
        await self.test_contract(
            name="Error Response Contract (404)",
            endpoint="/api/v1/nonexistent",
            method="GET",
            response_schema=None,
            expected_status=[404]
        )

        # Test 7: Unauthorized Error Contract
        temp_token = self.token
        self.token = "invalid-token"
        await self.test_contract(
            name="Unauthorized Error Contract",
            endpoint="/api/v1/auth/me",
            method="GET",
            response_schema=None,
            expected_status=[401, 403]
        )
        self.token = temp_token

        # Generate report
        await self.generate_report()

        await self.client.aclose()

    async def generate_report(self):
        """Generate contract test report"""
        print("\n" + "=" * 60)
        print("📊 Contract Test Results")
        print("=" * 60)

        passed = [t for t in self.test_results if t["passed"]]
        failed = [t for t in self.test_results if not t["passed"]]

        print(f"\n✅ Passed: {len(passed)}/{len(self.test_results)} tests")
        for test in passed:
            print(f"   • {test['test']}")

        if failed:
            print(f"\n❌ Failed: {len(failed)} tests")
            for test in failed:
                print(f"   • {test['test']}: {test['error']}")

        # Save detailed report
        report = {
            "timestamp": str(Path.cwd()),
            "total_tests": len(self.test_results),
            "passed": len(passed),
            "failed": len(failed),
            "success_rate": f"{(len(passed) / len(self.test_results) * 100):.1f}%",
            "test_results": self.test_results
        }

        with open("contract_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: contract_test_report.json")

        # Generate contract documentation
        self.generate_contract_docs()

        # Return exit code
        return 0 if len(failed) == 0 else 1

    def generate_contract_docs(self):
        """Generate API contract documentation"""
        docs = """# API Contract Documentation

## Overview
This document defines the contracts between frontend and backend.

## Request/Response Contracts

### Authentication

#### POST /api/v1/auth/login
**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "string",
  "expires_in": "number",
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string",
    "permissions": ["string"]
  }
}
```

### Users

#### GET /api/v1/users/
**Response (200):**
```json
{
  "items": [...],
  "total": "number",
  "page": "number",
  "size": "number",
  "pages": "number"
}
```

### Assets

#### GET /api/v1/assets/
**Response (200):**
Array of assets or paginated response

#### POST /api/v1/assets/
**Request:**
```json
{
  "name": "string",
  "asset_type": "domain|ip|url",
  "domain": "string (optional)",
  "ip_address": "string (optional)",
  "tags": ["string"],
  "criticality": "low|medium|high|critical"
}
```

### Error Responses

All error responses follow this format:
```json
{
  "detail": "string",
  "status": "number (optional)",
  "errors": ["string"] (optional)
}
```

## Contract Validation

All responses are validated against JSON Schema definitions.
See `contract_test_report.json` for validation results.

## Breaking Changes Policy

1. Never remove required fields from responses
2. New optional fields can be added
3. Field types must remain consistent
4. Enum values can be extended but not removed
5. Error formats must remain consistent

## Version History

- v1.0.0: Initial contract definition
"""

        with open("API_CONTRACTS.md", "w") as f:
            f.write(docs)

        print("📄 Contract documentation saved to: API_CONTRACTS.md")


async def main():
    """Main function"""
    tester = ContractTester()

    try:
        result = await tester.run_all_tests()
        return result
    except Exception as e:
        print(f"\n❌ Contract tests failed: {e}")
        return 1


if __name__ == "__main__":
    print("🔧 Frontend-Backend Contract Testing")
    print("Ensures API contracts remain consistent")
    print("")

    result = asyncio.run(main())
    exit(result)