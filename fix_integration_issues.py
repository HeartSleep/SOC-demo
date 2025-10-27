#!/usr/bin/env python3
"""
Fix Frontend-Backend Integration Issues
Automatically fixes common integration problems
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

class IntegrationFixer:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.fixes_applied = []
        self.fixes_failed = []

    def backup_file(self, filepath: Path):
        """Create backup of file before modification"""
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        if not backup_path.exists():
            shutil.copy2(filepath, backup_path)
            print(f"📦 Backed up: {filepath.name}")

    def fix_websocket_authentication(self):
        """Fix WebSocket authentication issue"""
        print("\n🔧 Fixing WebSocket Authentication...")

        ws_file = self.backend_dir / "app/api/endpoints/websocket_endpoint.py"

        if ws_file.exists():
            self.backup_file(ws_file)

            with open(ws_file, 'r') as f:
                content = f.read()

            # Replace TODO with actual authentication
            new_auth_code = '''    # Validate authentication token
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    from app.core.security import security
    from app.core.deps import get_user_from_token

    try:
        # Verify JWT token
        payload = security.verify_token(token)
        if not payload:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return

        # Verify user_id matches token
        token_user = payload.get("sub")
        if token_user != user_id and user_id != "demo_" + token_user:
            await websocket.close(code=1008, reason="User ID mismatch")
            return

    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return'''

            # Replace the TODO comment
            pattern = r'    # TODO: Add token validation here\n    # For now.*?\n'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, new_auth_code + '\n', content, flags=re.DOTALL)

                with open(ws_file, 'w') as f:
                    f.write(content)

                self.fixes_applied.append("WebSocket authentication implemented")
                print("✅ WebSocket authentication fixed")
            else:
                print("⚠️  WebSocket authentication already modified")
        else:
            self.fixes_failed.append("WebSocket file not found")
            print("❌ WebSocket endpoint file not found")

    def fix_user_model_compatibility(self):
        """Fix user model SQLAlchemy vs MongoDB compatibility"""
        print("\n🔧 Fixing User Model Compatibility...")

        users_endpoint = self.backend_dir / "app/api/endpoints/users.py"

        if users_endpoint.exists():
            self.backup_file(users_endpoint)

            with open(users_endpoint, 'r') as f:
                content = f.read()

            # Fix MongoDB-style queries to SQLAlchemy
            replacements = [
                # Fix find() calls
                (r'User\.find\(\)', 'db.query(User)'),
                (r'query\.find\(', 'query.filter('),
                (r'await query\.count\(\)', 'query.count()'),
                (r'await query\.skip\((\w+)\)\.limit\((\w+)\)\.to_list\(\)',
                 r'query.offset(\1).limit(\2).all()'),

                # Fix create/save operations
                (r'await new_user\.create\(\)', 'db.add(new_user)\n    await db.commit()\n    await db.refresh(new_user)'),
                (r'await user\.save\(\)', 'await db.commit()'),
                (r'await user\.delete\(\)', 'await db.delete(user)\n    await db.commit()'),
                (r'await User\.get\((\w+)\)', r'db.query(User).filter(User.id == \1).first()'),

                # Fix find_one
                (r'await User\.find_one\((.*?)\)', r'db.query(User).filter(\1).first()'),

                # Add db session dependency
                (r'async def get_users\((.*?)\):', r'async def get_users(\1, db: AsyncSession = Depends(get_session)):'),
            ]

            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)

            # Add missing imports
            if 'from sqlalchemy.ext.asyncio import AsyncSession' not in content:
                imports = '''from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.core.database import get_session
'''
                content = imports + content

            with open(users_endpoint, 'w') as f:
                f.write(content)

            self.fixes_applied.append("User model SQLAlchemy compatibility fixed")
            print("✅ User model compatibility fixed")
        else:
            self.fixes_failed.append("Users endpoint file not found")
            print("❌ Users endpoint file not found")

    def fix_cors_configuration(self):
        """Ensure CORS is properly configured"""
        print("\n🔧 Checking CORS Configuration...")

        config_file = self.backend_dir / "app/core/config.py"

        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()

            # Check if frontend URLs are in CORS origins
            if 'http://localhost:3000' not in content:
                print("⚠️  Adding frontend URL to CORS origins...")
                self.backup_file(config_file)

                # Update BACKEND_CORS_ORIGINS
                pattern = r'BACKEND_CORS_ORIGINS: List\[str\] = \[(.*?)\]'
                match = re.search(pattern, content, re.DOTALL)

                if match:
                    current_origins = match.group(1)
                    if 'http://localhost:3000' not in current_origins:
                        new_origins = current_origins.rstrip() + ',\n        "http://localhost:3000",\n        "http://localhost:3001"'
                        content = re.sub(pattern, f'BACKEND_CORS_ORIGINS: List[str] = [{new_origins}\n    ]', content, flags=re.DOTALL)

                        with open(config_file, 'w') as f:
                            f.write(content)

                        self.fixes_applied.append("CORS origins updated")
                        print("✅ CORS configuration updated")
            else:
                print("✅ CORS already configured correctly")
        else:
            self.fixes_failed.append("Config file not found")
            print("❌ Config file not found")

    def fix_response_format_consistency(self):
        """Ensure consistent response formats"""
        print("\n🔧 Fixing Response Format Consistency...")

        # Create a standardized response wrapper
        response_wrapper = '''"""
Standard API response wrappers for consistency
"""
from typing import Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response"""
    items: List[T]
    total: int
    page: int = 1
    size: int = 20
    pages: int = 1

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None

def create_paginated_response(items: List[Any], total: int, page: int = 1, size: int = 20) -> dict:
    """Helper to create paginated response"""
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if size > 0 else 1
    }

def create_success_response(data: Any = None, message: str = None) -> dict:
    """Helper to create success response"""
    return {
        "success": True,
        "data": data,
        "message": message
    }

def create_error_response(message: str, errors: List[str] = None) -> dict:
    """Helper to create error response"""
    return {
        "success": False,
        "message": message,
        "errors": errors or []
    }
'''
        response_file = self.backend_dir / "app/core/responses.py"

        with open(response_file, 'w') as f:
            f.write(response_wrapper)

        self.fixes_applied.append("Response format standardization added")
        print("✅ Response format helpers created")

    def fix_frontend_api_base_url(self):
        """Ensure frontend API base URL is correct"""
        print("\n🔧 Checking Frontend API Configuration...")

        # Check vite config
        vite_config = self.frontend_dir / "vite.config.ts"

        if vite_config.exists():
            with open(vite_config, 'r') as f:
                content = f.read()

            if '/api/v1' not in content or 'proxy' not in content:
                print("⚠️  Adding API proxy to Vite config...")
                self.backup_file(vite_config)

                proxy_config = '''    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        }
      }
    },'''

                # Add proxy configuration
                pattern = r'export default defineConfig\({(.*?)}\)'
                match = re.search(pattern, content, re.DOTALL)

                if match:
                    current_config = match.group(1)
                    if 'server:' not in current_config:
                        new_config = current_config.rstrip() + ',\n' + proxy_config
                        content = re.sub(pattern, f'export default defineConfig({{{new_config}\n}})', content, flags=re.DOTALL)

                        with open(vite_config, 'w') as f:
                            f.write(content)

                        self.fixes_applied.append("Frontend API proxy configured")
                        print("✅ Frontend API proxy configured")
            else:
                print("✅ Frontend API proxy already configured")
        else:
            print("⚠️  Vite config not found")

    def create_integration_test_suite(self):
        """Create automated integration test suite"""
        print("\n🔧 Creating Integration Test Suite...")

        test_suite = '''"""
Automated Integration Test Suite
Run with: pytest test_integration.py
"""
import pytest
import httpx
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

@pytest.fixture
async def authenticated_client():
    """Create authenticated HTTP client"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Login
        response = await client.post("/auth/login", json={
            "username": "admin",
            "password": "admin"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client

@pytest.mark.asyncio
async def test_authentication_flow(authenticated_client):
    """Test complete authentication flow"""
    response = await authenticated_client.get("/auth/me")
    assert response.status_code == 200
    user = response.json()
    assert "id" in user
    assert "username" in user

@pytest.mark.asyncio
async def test_asset_crud_operations(authenticated_client):
    """Test asset CRUD operations"""
    # Create
    asset_data = {
        "name": "test-asset.com",
        "asset_type": "domain",
        "domain": "test-asset.com"
    }
    response = await authenticated_client.post("/assets/", json=asset_data)
    assert response.status_code in [200, 201]
    asset = response.json()
    asset_id = asset["id"]

    # Read
    response = await authenticated_client.get(f"/assets/{asset_id}")
    assert response.status_code == 200

    # Update
    response = await authenticated_client.put(f"/assets/{asset_id}", json={"name": "updated-asset.com"})
    assert response.status_code == 200

    # Delete
    response = await authenticated_client.delete(f"/assets/{asset_id}")
    assert response.status_code in [200, 204]

@pytest.mark.asyncio
async def test_response_format_consistency(authenticated_client):
    """Test that all endpoints return consistent formats"""
    endpoints = [
        ("/assets/", "GET"),
        ("/users/", "GET"),
        ("/tasks/", "GET"),
    ]

    for endpoint, method in endpoints:
        if method == "GET":
            response = await authenticated_client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                # Check for consistent pagination format
                if isinstance(data, dict):
                    assert "items" in data or "data" in data
                # Arrays are also acceptable
                elif not isinstance(data, list):
                    pytest.fail(f"Unexpected response type for {endpoint}")
'''
        test_file = self.root_dir / "test_integration.py"

        with open(test_file, 'w') as f:
            f.write(test_suite)

        self.fixes_applied.append("Integration test suite created")
        print("✅ Integration test suite created")

    def generate_api_documentation(self):
        """Generate API documentation for frontend developers"""
        print("\n🔧 Generating API Documentation...")

        api_docs = '''# API Integration Guide

## Authentication

### Login
```typescript
POST /api/v1/auth/login
Body: {
  username: string,
  password: string
}
Response: {
  access_token: string,
  token_type: string,
  expires_in: number,
  user: UserObject
}
```

### Get Current User
```typescript
GET /api/v1/auth/me
Headers: { Authorization: "Bearer {token}" }
Response: UserObject
```

## Assets

### List Assets
```typescript
GET /api/v1/assets/
Query: {
  skip?: number,
  limit?: number,
  asset_type?: string,
  status?: string
}
Response: Asset[] | { items: Asset[], total: number }
```

### Create Asset
```typescript
POST /api/v1/assets/
Body: {
  name: string,
  asset_type: "domain" | "ip" | "url",
  domain?: string,
  ip_address?: string,
  tags?: string[],
  criticality?: "low" | "medium" | "high" | "critical"
}
Response: Asset
```

## WebSocket

### Connect
```typescript
ws://localhost:8000/api/v1/ws/{user_id}?token={jwt_token}
```

### Message Format
```typescript
Send: {
  type: "ping" | "join_room" | "leave_room",
  room?: string
}
Response: {
  type: "pong" | "room_joined" | "room_left" | "error",
  message?: string
}
```

## Error Handling

All errors follow this format:
```typescript
{
  detail: string,
  status?: number,
  errors?: string[]
}
```

## Frontend Integration Checklist

- [ ] Configure API proxy in vite.config.ts
- [ ] Set baseURL to '/api/v1' in axios config
- [ ] Handle 401 responses with token refresh/logout
- [ ] Add Authorization header to all authenticated requests
- [ ] Handle both array and paginated responses for lists
- [ ] Implement WebSocket reconnection logic
- [ ] Add CSRF token for state-changing requests
'''

        docs_file = self.root_dir / "API_INTEGRATION_GUIDE.md"

        with open(docs_file, 'w') as f:
            f.write(api_docs)

        self.fixes_applied.append("API documentation generated")
        print("✅ API documentation generated")

    def run_all_fixes(self):
        """Run all fixes"""
        print("=" * 60)
        print("🔧 Starting Integration Fixes")
        print("=" * 60)

        self.fix_websocket_authentication()
        self.fix_user_model_compatibility()
        self.fix_cors_configuration()
        self.fix_response_format_consistency()
        self.fix_frontend_api_base_url()
        self.create_integration_test_suite()
        self.generate_api_documentation()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Fix Summary")
        print("=" * 60)

        if self.fixes_applied:
            print(f"\n✅ Successfully applied {len(self.fixes_applied)} fixes:")
            for fix in self.fixes_applied:
                print(f"   • {fix}")

        if self.fixes_failed:
            print(f"\n❌ Failed to apply {len(self.fixes_failed)} fixes:")
            for fix in self.fixes_failed:
                print(f"   • {fix}")

        print("\n" + "=" * 60)
        print("📋 Next Steps")
        print("=" * 60)
        print("\n1. Restart the backend server:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        print("\n2. Restart the frontend dev server:")
        print("   cd frontend && npm run dev")
        print("\n3. Run integration tests:")
        print("   python test_frontend_backend_integration.py")
        print("\n4. Check the API documentation:")
        print("   cat API_INTEGRATION_GUIDE.md")

        # Create summary file
        summary = {
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "timestamp": str(Path.cwd()),
            "recommendations": [
                "Review backup files before committing changes",
                "Test all endpoints after restarting services",
                "Update frontend TypeScript types if needed",
                "Consider using OpenAPI spec generation"
            ]
        }

        with open("fix_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        print("\n📄 Fix summary saved to: fix_summary.json")

def main():
    """Main function"""
    fixer = IntegrationFixer()
    fixer.run_all_fixes()

if __name__ == "__main__":
    print("🔧 Frontend-Backend Integration Fixer")
    print("This script will fix common integration issues")
    print("Backup files will be created before modifications")
    print("\nPress Enter to continue or Ctrl+C to cancel...")

    try:
        input()
        main()
    except KeyboardInterrupt:
        print("\n\nFix cancelled by user")