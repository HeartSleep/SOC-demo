#!/usr/bin/env python3
"""
Test script to verify API routing is working correctly
"""

import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:8000"

# Define all API endpoints to test
API_ENDPOINTS = [
    # Health check
    {"method": "GET", "path": "/health", "auth": False},

    # Authentication endpoints
    {"method": "POST", "path": "/api/v1/auth/login", "auth": False, "data": {"username": "admin", "password": "admin"}},
    {"method": "GET", "path": "/api/v1/auth/me", "auth": True},

    # Assets endpoints
    {"method": "GET", "path": "/api/v1/assets/", "auth": True},
    {"method": "GET", "path": "/api/v1/assets/stats", "auth": True},

    # Tasks endpoints
    {"method": "GET", "path": "/api/v1/tasks/", "auth": True},
    {"method": "GET", "path": "/api/v1/tasks/stats", "auth": True},

    # Vulnerabilities endpoints
    {"method": "GET", "path": "/api/v1/vulnerabilities/", "auth": True},
    {"method": "GET", "path": "/api/v1/vulnerabilities/stats", "auth": True},

    # Users endpoints
    {"method": "GET", "path": "/api/v1/users/", "auth": True},

    # System endpoints
    {"method": "GET", "path": "/api/v1/system/status", "auth": False},

    # Settings endpoints
    {"method": "GET", "path": "/api/v1/settings/", "auth": True},

    # Vulnerability rules endpoints
    {"method": "GET", "path": "/api/v1/vulnerability-rules/", "auth": True},
    {"method": "GET", "path": "/api/v1/vulnerability-rules/stats", "auth": True},
]

def get_auth_token():
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_endpoint(endpoint, token=None):
    """Test a single API endpoint"""
    headers = {}
    if endpoint.get("auth") and token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if endpoint["method"] == "GET":
            response = requests.get(f"{BASE_URL}{endpoint['path']}", headers=headers, timeout=5)
        elif endpoint["method"] == "POST":
            data = endpoint.get("data", {})
            response = requests.post(f"{BASE_URL}{endpoint['path']}", json=data, headers=headers, timeout=5)
        else:
            return False, "Unsupported method"

        if response.status_code in [200, 201]:
            return True, f"✓ {response.status_code}"
        elif response.status_code == 404:
            return False, f"✗ 404 Not Found"
        elif response.status_code == 401:
            return False, f"✗ 401 Unauthorized"
        elif response.status_code == 403:
            return False, f"✗ 403 Forbidden"
        else:
            return False, f"✗ {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "✗ Connection Failed"
    except requests.exceptions.Timeout:
        return False, "✗ Timeout"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def main():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Testing SOC Platform API Routes")
    print(f"{Fore.CYAN}{'='*60}\n")

    # First, get auth token
    print(f"{Fore.YELLOW}Getting authentication token...")
    token = get_auth_token()
    if token:
        print(f"{Fore.GREEN}✓ Authentication successful\n")
    else:
        print(f"{Fore.RED}✗ Authentication failed\n")

    # Test all endpoints
    success_count = 0
    failed_count = 0

    for endpoint in API_ENDPOINTS:
        success, message = test_endpoint(endpoint, token)

        if success:
            print(f"{Fore.GREEN}{endpoint['method']:6} {endpoint['path']:45} {message}")
            success_count += 1
        else:
            print(f"{Fore.RED}{endpoint['method']:6} {endpoint['path']:45} {message}")
            failed_count += 1

    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Test Summary")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}✓ Success: {success_count}/{len(API_ENDPOINTS)}")
    print(f"{Fore.RED}✗ Failed:  {failed_count}/{len(API_ENDPOINTS)}")

    if failed_count == 0:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 All API routes are working correctly!")
    else:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  Some API routes need attention.")

if __name__ == "__main__":
    main()