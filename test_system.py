#!/usr/bin/env python3
"""
SOC Platform System Test Script
Tests all major functionality of the SOC security platform
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(test_name: str, status: bool, details: str = ""):
    """Print test result with colors"""
    icon = "✓" if status else "✗"
    color = GREEN if status else RED
    print(f"{color}{icon} {test_name}{RESET}")
    if details:
        print(f"  {details}")


def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, expected_status: int = 200) -> tuple:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return False, "Invalid method"

        success = response.status_code == expected_status

        try:
            response_data = response.json()
        except:
            response_data = response.text

        return success, response_data
    except Exception as e:
        return False, str(e)


def run_tests():
    """Run all system tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}SOC Platform System Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Health Check
    success, data = test_endpoint("GET", "/../health")
    print_test("Health Check", success, f"Status: {data.get('status', 'unknown') if isinstance(data, dict) else 'error'}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 2: Task Stats
    success, data = test_endpoint("GET", "/tasks/stats")
    print_test("Task Statistics", success, f"Total tasks: {data.get('total_tasks', 0) if isinstance(data, dict) else 'N/A'}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 3: Asset List
    success, data = test_endpoint("GET", "/assets/?limit=10")
    print_test("Asset List", success, f"Assets found: {data.get('total', 0) if isinstance(data, dict) else 'N/A'}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 4: Create Task
    task_data = {
        "name": f"Test Scan - {datetime.now().strftime('%H:%M:%S')}",
        "type": "vulnerability_scan",
        "target": "test.example.com",
        "priority": "medium",
        "description": "Automated test scan"
    }
    success, data = test_endpoint("POST", "/tasks/", data=task_data)
    created_task_id = data.get("id") if isinstance(data, dict) else None
    print_test("Create Task", success, f"Task ID: {created_task_id}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 5: Start Task (if created)
    if created_task_id:
        success, data = test_endpoint("POST", f"/tasks/{created_task_id}/start")
        print_test("Start Task", success, f"Status: {data.get('message', 'unknown') if isinstance(data, dict) else 'error'}")
        tests_passed += 1 if success else 0
        tests_failed += 0 if success else 1

        # Test 6: Get Task Status
        time.sleep(1)  # Wait a moment for task to process
        success, data = test_endpoint("GET", f"/tasks/{created_task_id}")
        task_status = data.get("status", "unknown") if isinstance(data, dict) else "error"
        print_test("Get Task Status", success, f"Status: {task_status}")
        tests_passed += 1 if success else 0
        tests_failed += 0 if success else 1

        # Test 7: Get Task Logs
        success, data = test_endpoint("GET", f"/tasks/{created_task_id}/logs")
        log_count = len(data) if isinstance(data, list) else 0
        print_test("Get Task Logs", success, f"Logs: {log_count} entries")
        tests_passed += 1 if success else 0
        tests_failed += 0 if success else 1

        # Test 8: Clone Task
        success, data = test_endpoint("POST", f"/tasks/{created_task_id}/clone")
        cloned_task_id = data.get("task", {}).get("id") if isinstance(data, dict) else None
        print_test("Clone Task", success, f"Cloned ID: {cloned_task_id}")
        tests_passed += 1 if success else 0
        tests_failed += 0 if success else 1

    # Test 9: Vulnerability Stats
    success, data = test_endpoint("GET", "/vulnerabilities/stats")
    print_test("Vulnerability Statistics", success, f"Total: {data.get('total_vulnerabilities', 0) if isinstance(data, dict) else 'N/A'}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 10: User Profile
    success, data = test_endpoint("GET", "/users/profile")
    username = data.get("username", "unknown") if isinstance(data, dict) else "error"
    print_test("User Profile", success, f"User: {username}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 11: Asset Stats
    success, data = test_endpoint("GET", "/assets/stats")
    total_assets = data.get("total_assets", 0) if isinstance(data, dict) else "N/A"
    print_test("Asset Statistics", success, f"Total assets: {total_assets}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Test 12: Create Asset
    asset_data = {
        "name": f"test-server-{int(time.time())}",
        "type": "server",
        "ip_address": "192.168.1.100",
        "description": "Test server created by automated test"
    }
    success, data = test_endpoint("POST", "/assets/", data=asset_data)
    created_asset_id = data.get("id") if isinstance(data, dict) else None
    print_test("Create Asset", success, f"Asset ID: {created_asset_id}")
    tests_passed += 1 if success else 0
    tests_failed += 0 if success else 1

    # Print Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary:{RESET}")
    print(f"  {GREEN}Passed: {tests_passed}{RESET}")
    print(f"  {RED}Failed: {tests_failed}{RESET}")
    print(f"  Total: {tests_passed + tests_failed}")

    success_rate = (tests_passed / (tests_passed + tests_failed)) * 100 if (tests_passed + tests_failed) > 0 else 0

    if success_rate >= 80:
        print(f"\n{GREEN}✓ System is functioning well ({success_rate:.1f}% success rate){RESET}")
    elif success_rate >= 50:
        print(f"\n{YELLOW}⚠ System has some issues ({success_rate:.1f}% success rate){RESET}")
    else:
        print(f"\n{RED}✗ System has critical issues ({success_rate:.1f}% success rate){RESET}")

    print(f"{BLUE}{'='*60}{RESET}\n")

    return tests_passed, tests_failed


if __name__ == "__main__":
    try:
        # Check if services are running
        response = requests.get(f"{BASE_URL}/../health", timeout=2)
        if response.status_code == 200:
            run_tests()
        else:
            print(f"{RED}Error: Backend service returned status {response.status_code}{RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{RED}Error: Cannot connect to backend service at {BASE_URL}{RESET}")
        print(f"{YELLOW}Please ensure the SOC platform is running:{RESET}")
        print(f"  cd /Users/heart/Documents/Code/WEB/SOC")
        print(f"  ./start.sh start")
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")