#!/usr/bin/env python3
"""
SOC Platform Database Initialization Script
Initializes MongoDB collections and creates initial data
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import init_database, get_database
from app.core.security import get_password_hash
from app.api.models.user import User, UserRole
from app.api.models.asset import Asset, AssetType, AssetStatus
from app.api.models.task import Task, TaskType, TaskStatus
from app.api.models.vulnerability import Vulnerability, VulnerabilitySeverity, VulnerabilityStatus
from app.api.models.report import Report, ReportType, ReportStatus
from beanie import init_beanie
import motor.motor_asyncio


async def create_admin_user():
    """Create default admin user"""
    print("Creating admin user...")

    # Check if admin user already exists
    admin_user = await User.find_one(User.username == "admin")
    if admin_user:
        print("Admin user already exists, skipping...")
        return admin_user

    admin_data = {
        "username": "admin",
        "email": "admin@soc-platform.com",
        "full_name": "System Administrator",
        "password_hash": get_password_hash("admin123"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "permissions": [
            "system:admin", "user:read", "user:write", "user:delete",
            "asset:read", "asset:write", "asset:delete",
            "task:read", "task:write", "task:delete", "task:execute",
            "vulnerability:read", "vulnerability:write", "vulnerability:verify",
            "report:read", "report:write", "report:delete",
            "settings:read", "settings:write"
        ]
    }

    admin_user = User(**admin_data)
    await admin_user.create()
    print(f"Admin user created: {admin_user.username}")
    return admin_user


async def create_sample_users():
    """Create sample users for different roles"""
    print("Creating sample users...")

    sample_users = [
        {
            "username": "security_analyst",
            "email": "analyst@soc-platform.com",
            "full_name": "Security Analyst",
            "password_hash": get_password_hash("analyst123"),
            "role": UserRole.SECURITY_ANALYST,
            "is_active": True,
            "permissions": [
                "asset:read", "asset:write",
                "task:read", "task:write", "task:execute",
                "vulnerability:read", "vulnerability:write", "vulnerability:verify",
                "report:read", "report:write"
            ]
        },
        {
            "username": "operator",
            "email": "operator@soc-platform.com",
            "full_name": "SOC Operator",
            "password_hash": get_password_hash("operator123"),
            "role": UserRole.OPERATOR,
            "is_active": True,
            "permissions": [
                "asset:read", "asset:write",
                "task:read", "task:write", "task:execute",
                "vulnerability:read",
                "report:read"
            ]
        },
        {
            "username": "viewer",
            "email": "viewer@soc-platform.com",
            "full_name": "Security Viewer",
            "password_hash": get_password_hash("viewer123"),
            "role": UserRole.VIEWER,
            "is_active": True,
            "permissions": [
                "asset:read",
                "task:read",
                "vulnerability:read",
                "report:read"
            ]
        }
    ]

    created_users = []
    for user_data in sample_users:
        existing_user = await User.find_one(User.username == user_data["username"])
        if existing_user:
            print(f"User {user_data['username']} already exists, skipping...")
            continue

        user = User(**user_data)
        await user.create()
        created_users.append(user)
        print(f"Created user: {user.username}")

    return created_users


async def create_sample_assets():
    """Create sample assets for testing"""
    print("Creating sample assets...")

    sample_assets = [
        {
            "name": "Company Website",
            "type": AssetType.URL,
            "value": "https://example.com",
            "status": AssetStatus.ACTIVE,
            "priority": "high",
            "tags": ["production", "web", "public"],
            "department": "IT",
            "description": "Main company website",
            "scan_config": {
                "enabled_scans": ["port_scan", "vulnerability_scan", "web_discovery"],
                "schedule": "weekly",
                "port_range": "80,443,8080,8443",
                "intensity": "normal"
            }
        },
        {
            "name": "Mail Server",
            "type": AssetType.IP,
            "value": "192.168.1.10",
            "status": AssetStatus.ACTIVE,
            "priority": "critical",
            "tags": ["production", "mail", "internal"],
            "department": "IT",
            "description": "Primary mail server",
            "scan_config": {
                "enabled_scans": ["port_scan", "vulnerability_scan"],
                "schedule": "daily",
                "port_range": "25,465,587,993,995",
                "intensity": "normal"
            }
        },
        {
            "name": "Database Server",
            "type": AssetType.IP,
            "value": "192.168.1.20",
            "status": AssetStatus.ACTIVE,
            "priority": "critical",
            "tags": ["production", "database", "internal"],
            "department": "IT",
            "description": "Primary database server",
            "scan_config": {
                "enabled_scans": ["port_scan", "vulnerability_scan"],
                "schedule": "daily",
                "port_range": "3306,5432,1433,6379",
                "intensity": "light"
            }
        },
        {
            "name": "Development Server",
            "type": AssetType.IP,
            "value": "192.168.1.100",
            "status": AssetStatus.ACTIVE,
            "priority": "medium",
            "tags": ["development", "web", "internal"],
            "department": "Development",
            "description": "Development environment server",
            "scan_config": {
                "enabled_scans": ["port_scan", "vulnerability_scan", "web_discovery"],
                "schedule": "weekly",
                "port_range": "80,443,8080,3000,9000",
                "intensity": "intensive"
            }
        },
        {
            "name": "Company Domain",
            "type": AssetType.DOMAIN,
            "value": "example.com",
            "status": AssetStatus.ACTIVE,
            "priority": "high",
            "tags": ["production", "domain", "public"],
            "department": "IT",
            "description": "Primary company domain",
            "scan_config": {
                "enabled_scans": ["subdomain_enum", "port_scan", "vulnerability_scan"],
                "schedule": "daily",
                "port_range": "80,443",
                "intensity": "normal"
            }
        }
    ]

    created_assets = []
    for asset_data in sample_assets:
        existing_asset = await Asset.find_one(Asset.value == asset_data["value"])
        if existing_asset:
            print(f"Asset {asset_data['value']} already exists, skipping...")
            continue

        asset = Asset(**asset_data)
        await asset.create()
        created_assets.append(asset)
        print(f"Created asset: {asset.name}")

    return created_assets


async def create_sample_tasks(assets):
    """Create sample scanning tasks"""
    print("Creating sample tasks...")

    if not assets:
        print("No assets available, skipping task creation...")
        return []

    sample_tasks = [
        {
            "name": "Daily Security Scan - Production Assets",
            "type": TaskType.COMPREHENSIVE,
            "status": TaskStatus.COMPLETED,
            "priority": "high",
            "target_assets": [str(asset.id) for asset in assets[:3]],  # First 3 assets
            "description": "Comprehensive security scan of production assets",
            "config": {
                "port_range": "1-65535",
                "scan_speed": "3",
                "vuln_engines": ["nuclei", "xray"],
                "severity_filter": ["critical", "high", "medium"],
                "concurrency": 10,
                "retry_count": 2
            },
            "progress": 100,
            "started_at": datetime.utcnow() - timedelta(hours=2),
            "completed_at": datetime.utcnow() - timedelta(minutes=30),
            "duration": 5400  # 1.5 hours in seconds
        },
        {
            "name": "Web Discovery - Company Website",
            "type": TaskType.WEB_DISCOVERY,
            "status": TaskStatus.RUNNING,
            "priority": "medium",
            "target_assets": [str(assets[0].id)],  # First asset
            "description": "Web application discovery and technology identification",
            "config": {
                "crawl_depth": 3,
                "timeout": 30,
                "web_options": ["screenshot", "technology_detection", "directory_scan"],
                "concurrency": 5,
                "retry_count": 1
            },
            "progress": 65,
            "started_at": datetime.utcnow() - timedelta(minutes=45)
        },
        {
            "name": "Port Scan - Internal Network",
            "type": TaskType.PORT_SCAN,
            "status": TaskStatus.PENDING,
            "priority": "low",
            "target_assets": [str(asset.id) for asset in assets[1:4]],  # Assets 2-4
            "description": "Port scanning of internal network assets",
            "config": {
                "port_range": "1-1000,8080,8443,3389",
                "scan_speed": "4",
                "port_options": ["service_detection", "os_detection"],
                "concurrency": 15,
                "retry_count": 1
            },
            "scheduled_at": datetime.utcnow() + timedelta(hours=1)
        }
    ]

    created_tasks = []
    for task_data in sample_tasks:
        task = Task(**task_data)
        await task.create()
        created_tasks.append(task)
        print(f"Created task: {task.name}")

    return created_tasks


async def create_sample_vulnerabilities(assets, tasks):
    """Create sample vulnerabilities"""
    print("Creating sample vulnerabilities...")

    if not assets or not tasks:
        print("No assets or tasks available, skipping vulnerability creation...")
        return []

    sample_vulnerabilities = [
        {
            "name": "Weak SSL/TLS Configuration",
            "description": "The server supports weak SSL/TLS cipher suites that may be vulnerable to attacks.",
            "severity": VulnerabilitySeverity.HIGH,
            "cvss_score": 7.5,
            "cve_id": "CVE-2021-12345",
            "asset_id": str(assets[0].id),
            "asset_name": assets[0].name,
            "task_id": str(tasks[0].id),
            "task_name": tasks[0].name,
            "status": VulnerabilityStatus.OPEN,
            "verified": True,
            "details": {
                "port": 443,
                "protocol": "https",
                "evidence": "Weak cipher suites detected: TLS_RSA_WITH_RC4_128_SHA",
                "impact": "Potential man-in-the-middle attacks",
                "recommendation": "Update SSL/TLS configuration to use strong cipher suites"
            },
            "discovered_at": datetime.utcnow() - timedelta(hours=2)
        },
        {
            "name": "SQL Injection Vulnerability",
            "description": "SQL injection vulnerability found in login form",
            "severity": VulnerabilitySeverity.CRITICAL,
            "cvss_score": 9.8,
            "cve_id": "CVE-2023-54321",
            "asset_id": str(assets[0].id),
            "asset_name": assets[0].name,
            "task_id": str(tasks[0].id),
            "task_name": tasks[0].name,
            "status": VulnerabilityStatus.OPEN,
            "verified": True,
            "details": {
                "port": 80,
                "protocol": "http",
                "url": "https://example.com/login",
                "parameter": "username",
                "payload": "admin' OR '1'='1",
                "evidence": "Database error message revealed",
                "impact": "Complete database compromise",
                "recommendation": "Use parameterized queries and input validation"
            },
            "discovered_at": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "name": "Outdated Software Version",
            "description": "Server running outdated version of Apache web server",
            "severity": VulnerabilitySeverity.MEDIUM,
            "cvss_score": 6.1,
            "asset_id": str(assets[3].id),
            "asset_name": assets[3].name,
            "task_id": str(tasks[0].id),
            "task_name": tasks[0].name,
            "status": VulnerabilityStatus.FIXED,
            "verified": True,
            "details": {
                "port": 80,
                "service": "Apache httpd",
                "version": "2.4.25",
                "latest_version": "2.4.54",
                "evidence": "HTTP response headers reveal Apache/2.4.25",
                "impact": "Potential exploitation of known vulnerabilities",
                "recommendation": "Update Apache to the latest stable version"
            },
            "discovered_at": datetime.utcnow() - timedelta(days=1),
            "fixed_at": datetime.utcnow() - timedelta(hours=6)
        },
        {
            "name": "Open SSH with Weak Configuration",
            "description": "SSH service allows weak authentication methods",
            "severity": VulnerabilitySeverity.MEDIUM,
            "cvss_score": 5.3,
            "asset_id": str(assets[1].id),
            "asset_name": assets[1].name,
            "task_id": str(tasks[0].id),
            "task_name": tasks[0].name,
            "status": VulnerabilityStatus.OPEN,
            "verified": False,
            "details": {
                "port": 22,
                "service": "SSH",
                "evidence": "Password authentication enabled, root login allowed",
                "impact": "Potential brute force attacks",
                "recommendation": "Disable password authentication, use key-based authentication"
            },
            "discovered_at": datetime.utcnow() - timedelta(hours=3)
        },
        {
            "name": "Missing Security Headers",
            "description": "Web application missing important security headers",
            "severity": VulnerabilitySeverity.LOW,
            "cvss_score": 3.1,
            "asset_id": str(assets[0].id),
            "asset_name": assets[0].name,
            "task_id": str(tasks[1].id),
            "task_name": tasks[1].name,
            "status": VulnerabilityStatus.FALSE_POSITIVE,
            "verified": True,
            "details": {
                "port": 443,
                "protocol": "https",
                "missing_headers": ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection"],
                "evidence": "HTTP response analysis",
                "impact": "Increased risk of XSS and clickjacking attacks",
                "recommendation": "Implement security headers"
            },
            "discovered_at": datetime.utcnow() - timedelta(minutes=45)
        }
    ]

    created_vulnerabilities = []
    for vuln_data in sample_vulnerabilities:
        vulnerability = Vulnerability(**vuln_data)
        await vulnerability.create()
        created_vulnerabilities.append(vulnerability)
        print(f"Created vulnerability: {vulnerability.name}")

    return created_vulnerabilities


async def create_sample_reports(assets, vulnerabilities):
    """Create sample reports"""
    print("Creating sample reports...")

    sample_reports = [
        {
            "title": "Weekly Security Assessment Report",
            "description": "Comprehensive security assessment for the week",
            "type": ReportType.COMPREHENSIVE,
            "format": "pdf",
            "status": ReportStatus.COMPLETED,
            "config": {
                "include_assets": True,
                "include_vulnerabilities": True,
                "include_tasks": True,
                "severity_filter": ["critical", "high", "medium"],
                "date_range": {
                    "start": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            },
            "file_path": "/reports/weekly_security_report.pdf",
            "file_size": 2048576,  # 2MB
            "generated_at": datetime.utcnow() - timedelta(hours=1),
            "expires_at": datetime.utcnow() + timedelta(days=30)
        },
        {
            "title": "Critical Vulnerabilities Report",
            "description": "Report focusing on critical and high-severity vulnerabilities",
            "type": ReportType.VULNERABILITY,
            "format": "html",
            "status": ReportStatus.COMPLETED,
            "config": {
                "include_vulnerabilities": True,
                "severity_filter": ["critical", "high"],
                "include_remediation": True,
                "include_timeline": True
            },
            "file_path": "/reports/critical_vulnerabilities.html",
            "file_size": 512000,  # 500KB
            "generated_at": datetime.utcnow() - timedelta(hours=6),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        },
        {
            "title": "Asset Inventory Report",
            "description": "Complete inventory of all managed assets",
            "type": ReportType.ASSET,
            "format": "excel",
            "status": ReportStatus.GENERATING,
            "config": {
                "include_assets": True,
                "include_ports": True,
                "include_services": True,
                "group_by_department": True
            },
            "progress": 75
        }
    ]

    created_reports = []
    for report_data in sample_reports:
        report = Report(**report_data)
        await report.create()
        created_reports.append(report)
        print(f"Created report: {report.title}")

    return created_reports


async def create_indexes():
    """Create database indexes for better performance"""
    print("Creating database indexes...")

    db = get_database()

    # User indexes
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index([("role", 1), ("is_active", 1)])

    # Asset indexes
    await db.assets.create_index("value", unique=True)
    await db.assets.create_index([("type", 1), ("status", 1)])
    await db.assets.create_index("tags")
    await db.assets.create_index([("priority", 1), ("status", 1)])
    await db.assets.create_index("department")

    # Task indexes
    await db.tasks.create_index([("status", 1), ("priority", 1)])
    await db.tasks.create_index([("type", 1), ("status", 1)])
    await db.tasks.create_index("target_assets")
    await db.tasks.create_index("created_by")
    await db.tasks.create_index("scheduled_at")

    # Vulnerability indexes
    await db.vulnerabilities.create_index([("severity", 1), ("status", 1)])
    await db.vulnerabilities.create_index("asset_id")
    await db.vulnerabilities.create_index("task_id")
    await db.vulnerabilities.create_index("cve_id")
    await db.vulnerabilities.create_index([("verified", 1), ("status", 1)])
    await db.vulnerabilities.create_index("discovered_at")

    # Report indexes
    await db.reports.create_index([("type", 1), ("status", 1)])
    await db.reports.create_index("created_by")
    await db.reports.create_index("expires_at")
    await db.reports.create_index("generated_at")

    print("Database indexes created successfully")


async def main():
    """Main initialization function"""
    print("=" * 50)
    print("SOC Platform Database Initialization")
    print("=" * 50)

    try:
        # Initialize database connection
        print("Initializing database connection...")
        await init_database()
        print("Database connection established")

        # Create indexes
        await create_indexes()

        # Create users
        admin_user = await create_admin_user()
        sample_users = await create_sample_users()

        # Create assets
        sample_assets = await create_sample_assets()

        # Create tasks
        sample_tasks = await create_sample_tasks(sample_assets)

        # Create vulnerabilities
        sample_vulnerabilities = await create_sample_vulnerabilities(sample_assets, sample_tasks)

        # Create reports
        sample_reports = await create_sample_reports(sample_assets, sample_vulnerabilities)

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("=" * 50)
        print(f"Created {len(sample_users) + 1} users (including admin)")
        print(f"Created {len(sample_assets)} assets")
        print(f"Created {len(sample_tasks)} tasks")
        print(f"Created {len(sample_vulnerabilities)} vulnerabilities")
        print(f"Created {len(sample_reports)} reports")
        print("\nDefault credentials:")
        print("Admin: admin / admin123")
        print("Analyst: security_analyst / analyst123")
        print("Operator: operator / operator123")
        print("Viewer: viewer / viewer123")
        print("=" * 50)

    except Exception as e:
        print(f"Error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())