from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
import os

from app.core.deps import get_current_active_user, require_permission
from app.core.database import is_database_connected
from app.api.models.user import User
from app.api.models.vulnerability import Vulnerability, VulnerabilityType, Severity, VulnerabilityStatus
from app.api.schemas.vulnerability import (
    VulnerabilityCreate, VulnerabilityUpdate, VulnerabilityResponse,
    VulnerabilitySearch, VulnerabilityStats, VulnerabilityComment,
    VulnerabilityVerification
)
from app.core.celery.tasks.vulnerability_tasks import vulnerability_verification_task
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[VulnerabilityResponse])
async def list_vulnerabilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    vulnerability_type: Optional[VulnerabilityType] = None,
    severity: Optional[Severity] = None,
    status: Optional[VulnerabilityStatus] = None,
    assigned_to: Optional[str] = None,
    verified: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    """List vulnerabilities with optional filtering"""

    # Demo mode - return mock vulnerabilities
    if not is_database_connected():
        current_time = datetime.utcnow()
        demo_vulnerabilities = [
            {
                "id": "demo_vuln_1",
                "title": "SQL Injection in Login Form",
                "description": "SQL injection vulnerability found in user login form allowing data extraction",
                "vulnerability_type": "sql_injection",
                "severity": "high",
                "status": "open",
                "target_asset_id": "demo_asset_1",
                "target_url": "https://web-server-01.example.com/login",
                "target_ip": "192.168.1.100",
                "target_port": 80,
                "target_path": "/login",
                "cve_id": None,
                "cwe_id": "CWE-89",
                "cvss_score": 8.1,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                "scanner": "demo_scanner",
                "scan_task_id": None,
                "discovery_date": current_time,
                "request": "POST /login HTTP/1.1\nContent-Type: application/x-www-form-urlencoded\n\nusername=' OR 1=1--&password=test",
                "response": "HTTP/1.1 200 OK\nContent-Type: text/html\n\n<html>Welcome admin</html>",
                "payload": "' OR 1=1--",
                "proof_of_concept": "1. Navigate to login page\n2. Enter payload in username field\n3. Observe successful login bypass",
                "screenshots": [],
                "evidence_files": [],
                "impact_description": "Unauthorized access to administrative functions",
                "business_impact": "High risk of data breach and system compromise",
                "affected_systems": ["web-server-01.example.com"],
                "remediation_advice": "Use parameterized queries and input validation",
                "remediation_priority": "high",
                "fix_complexity": "medium",
                "estimated_fix_time": 4,
                "verified": False,
                "verified_by": None,
                "verified_at": None,
                "verification_notes": None,
                "assigned_to": None,
                "due_date": None,
                "sla_breach": False,
                "reported_to": [],
                "comments": [],
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": "demo_scanner",
                "updated_by": "demo_scanner",
                "retest_count": 0,
                "last_retest": None,
                "retest_results": [],
                "tags": ["injection", "authentication"],
                "custom_fields": {},
                "references": ["https://owasp.org/www-project-top-ten/"],
                "exploitability": 3.9,
                "remediation_level": 0.95,
                "report_confidence": 1.0
            },
            {
                "id": "demo_vuln_2",
                "title": "Cross-Site Scripting (XSS)",
                "description": "Reflected XSS vulnerability in search functionality allows script injection",
                "vulnerability_type": "xss",
                "severity": "medium",
                "status": "in_progress",
                "target_asset_id": "demo_asset_2",
                "target_url": "https://db-server-01.example.com/search",
                "target_ip": "192.168.1.101",
                "target_port": 80,
                "target_path": "/search",
                "cve_id": None,
                "cwe_id": "CWE-79",
                "cvss_score": 6.1,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                "scanner": "demo_scanner",
                "scan_task_id": None,
                "discovery_date": current_time,
                "request": "GET /search?q=<script>alert('XSS')</script> HTTP/1.1",
                "response": "HTTP/1.1 200 OK\nContent-Type: text/html\n\n<div>Results for: <script>alert('XSS')</script></div>",
                "payload": "<script>alert('XSS')</script>",
                "proof_of_concept": "1. Navigate to search page\n2. Enter XSS payload in search field\n3. Observe script execution",
                "screenshots": [],
                "evidence_files": [],
                "impact_description": "Session hijacking and data theft possible",
                "business_impact": "Medium risk of user account compromise",
                "affected_systems": ["db-server-01.example.com"],
                "remediation_advice": "Implement proper output encoding and Content Security Policy",
                "remediation_priority": "medium",
                "fix_complexity": "low",
                "estimated_fix_time": 2,
                "verified": True,
                "verified_by": "analyst",
                "verified_at": current_time,
                "verification_notes": "Confirmed exploitable in production environment",
                "assigned_to": "analyst",
                "due_date": current_time + timedelta(days=7),
                "sla_breach": False,
                "reported_to": ["security_team"],
                "comments": [{"comment": "Working on fix", "author": "analyst", "timestamp": current_time.isoformat()}],
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": "demo_scanner",
                "updated_by": "analyst",
                "retest_count": 1,
                "last_retest": current_time,
                "retest_results": [{"status": "confirmed", "date": current_time.isoformat()}],
                "tags": ["xss", "web_security"],
                "custom_fields": {"priority_escalation": False},
                "references": ["https://owasp.org/www-community/attacks/xss/"],
                "exploitability": 2.8,
                "remediation_level": 0.87,
                "report_confidence": 0.95
            },
            {
                "id": "demo_vuln_3",
                "title": "Outdated Software Component",
                "description": "Using vulnerable version of jQuery library with known security issues",
                "vulnerability_type": "vulnerable_component",
                "severity": "low",
                "status": "fixed",
                "target_asset_id": "demo_asset_1",
                "target_url": "https://web-server-01.example.com",
                "target_ip": "192.168.1.100",
                "target_port": 80,
                "target_path": "/js/jquery-1.8.0.min.js",
                "cve_id": "CVE-2020-11022",
                "cwe_id": "CWE-79",
                "cvss_score": 3.7,
                "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:L/A:N",
                "scanner": "demo_scanner",
                "scan_task_id": None,
                "discovery_date": current_time - timedelta(days=5),
                "request": "GET /js/jquery-1.8.0.min.js HTTP/1.1",
                "response": "HTTP/1.1 200 OK\nContent-Type: application/javascript\n\n/*! jQuery v1.8.0",
                "payload": None,
                "proof_of_concept": "Version detection shows jQuery 1.8.0 which contains known vulnerabilities",
                "screenshots": [],
                "evidence_files": [],
                "impact_description": "Potential XSS through vulnerable jQuery methods",
                "business_impact": "Low risk due to specific exploitation requirements",
                "affected_systems": ["web-server-01.example.com"],
                "remediation_advice": "Update jQuery to version 3.5.0 or later",
                "remediation_priority": "low",
                "fix_complexity": "low",
                "estimated_fix_time": 1,
                "verified": True,
                "verified_by": "admin",
                "verified_at": current_time - timedelta(days=2),
                "verification_notes": "Vulnerability confirmed, library updated to latest version",
                "assigned_to": "admin",
                "due_date": current_time - timedelta(days=1),
                "sla_breach": False,
                "reported_to": ["dev_team"],
                "comments": [
                    {"comment": "Library updated successfully", "author": "admin", "timestamp": (current_time - timedelta(days=1)).isoformat()}
                ],
                "created_at": current_time - timedelta(days=5),
                "updated_at": current_time - timedelta(days=1),
                "created_by": "demo_scanner",
                "updated_by": "admin",
                "retest_count": 1,
                "last_retest": current_time - timedelta(days=1),
                "retest_results": [{"status": "fixed", "date": (current_time - timedelta(days=1)).isoformat()}],
                "tags": ["component", "jquery", "cve"],
                "custom_fields": {"fix_verified": True},
                "references": ["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-11022"],
                "exploitability": 1.2,
                "remediation_level": 1.0,
                "report_confidence": 1.0
            }
        ]

        # Apply basic filtering
        filtered_vulnerabilities = demo_vulnerabilities
        if severity:
            filtered_vulnerabilities = [v for v in filtered_vulnerabilities if v["severity"] == severity]
        if status:
            filtered_vulnerabilities = [v for v in filtered_vulnerabilities if v["status"] == status]

        # Apply pagination
        start = skip
        end = skip + limit
        paginated_vulnerabilities = filtered_vulnerabilities[start:end]

        logger.info(f"Demo mode: returning {len(paginated_vulnerabilities)} mock vulnerabilities")
        return [VulnerabilityResponse(**vuln) for vuln in paginated_vulnerabilities]

    filters = {}

    if vulnerability_type:
        filters["vulnerability_type"] = vulnerability_type
    if severity:
        filters["severity"] = severity
    if status:
        filters["status"] = status
    if assigned_to:
        filters["assigned_to"] = assigned_to
    if verified is not None:
        filters["verified"] = verified

    query = Vulnerability.find(filters)
    vulnerabilities = await query.skip(skip).limit(limit).to_list()

    return [VulnerabilityResponse(**vuln.dict()) for vuln in vulnerabilities]


@router.post("/search", response_model=List[VulnerabilityResponse])
async def search_vulnerabilities(
    search_params: VulnerabilitySearch,
    current_user: User = Depends(require_permission("vulnerability:read"))
):
    """Advanced vulnerability search"""

    filters = {}

    # Text search
    if search_params.query:
        filters["$text"] = {"$search": search_params.query}

    # Specific field filters
    if search_params.vulnerability_type:
        filters["vulnerability_type"] = search_params.vulnerability_type
    if search_params.severity:
        filters["severity"] = search_params.severity
    if search_params.status:
        filters["status"] = search_params.status
    if search_params.target_asset_id:
        filters["target_asset_id"] = search_params.target_asset_id
    if search_params.scanner:
        filters["scanner"] = search_params.scanner
    if search_params.assigned_to:
        filters["assigned_to"] = search_params.assigned_to
    if search_params.verified is not None:
        filters["verified"] = search_params.verified
    if search_params.tags:
        filters["tags"] = {"$in": search_params.tags}

    # Date filters
    if search_params.discovered_after or search_params.discovered_before:
        date_filter = {}
        if search_params.discovered_after:
            date_filter["$gte"] = search_params.discovered_after
        if search_params.discovered_before:
            date_filter["$lte"] = search_params.discovered_before
        filters["discovery_date"] = date_filter

    query = Vulnerability.find(filters)
    vulnerabilities = await query.skip(search_params.skip).limit(search_params.limit).to_list()

    return [VulnerabilityResponse(**vuln.dict()) for vuln in vulnerabilities]


@router.get("/stats", response_model=VulnerabilityStats)
async def get_vulnerability_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """Get vulnerability statistics"""

    # Demo mode - return mock stats
    if not is_database_connected():
        demo_stats = {
            "total_vulnerabilities": 3,
            "vulnerabilities_by_severity": {
                "critical": 0,
                "high": 1,
                "medium": 1,
                "low": 1,
                "info": 0
            },
            "vulnerabilities_by_status": {
                "open": 1,
                "confirmed": 1,
                "fixed": 1,
                "closed": 0,
                "false_positive": 0,
                "risk_accepted": 0,
                "retest_required": 0
            },
            "vulnerabilities_by_type": {
                "sql_injection": 1,
                "xss": 1,
                "outdated_software": 1,
                "weak_credentials": 0,
                "csrf": 0,
                "rce": 0,
                "directory_traversal": 0,
                "information_disclosure": 0,
                "weak_configuration": 0,
                "other": 0
            },
            "verified_vulnerabilities": 2,
            "overdue_vulnerabilities": 0,
            "recent_vulnerabilities": 3,
            "average_cvss_score": 6.0
        }

        logger.info("Demo mode: returning mock vulnerability statistics")
        return VulnerabilityStats(**demo_stats)

    try:
        # Count total vulnerabilities
        total_vulnerabilities = await Vulnerability.count()

        # Count by severity
        vulnerabilities_by_severity = {}
        for severity in Severity:
            count = await Vulnerability.find(Vulnerability.severity == severity).count()
            vulnerabilities_by_severity[severity] = count

        # Count by status
        vulnerabilities_by_status = {}
        for vuln_status in VulnerabilityStatus:
            count = await Vulnerability.find(Vulnerability.status == vuln_status).count()
            vulnerabilities_by_status[vuln_status] = count

        # Count by type
        vulnerabilities_by_type = {}
        for vuln_type in VulnerabilityType:
            count = await Vulnerability.find(Vulnerability.vulnerability_type == vuln_type).count()
            vulnerabilities_by_type[vuln_type] = count

        # Count verified vulnerabilities
        verified_vulnerabilities = await Vulnerability.find(Vulnerability.verified == True).count()

        # Count overdue vulnerabilities
        now = datetime.utcnow()
        overdue_vulnerabilities = await Vulnerability.find({
            "due_date": {"$lt": now},
            "status": {"$nin": [VulnerabilityStatus.FIXED, VulnerabilityStatus.CLOSED]}
        }).count()

        # Count recent vulnerabilities (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_vulnerabilities = await Vulnerability.find(
            Vulnerability.discovery_date >= week_ago
        ).count()

        # Calculate average CVSS score
        vulnerabilities_with_cvss = await Vulnerability.find({
            "cvss_score": {"$ne": None}
        }).to_list()

        average_cvss_score = None
        if vulnerabilities_with_cvss:
            total_score = sum(v.cvss_score for v in vulnerabilities_with_cvss if v.cvss_score)
            average_cvss_score = total_score / len(vulnerabilities_with_cvss)

        return VulnerabilityStats(
            total_vulnerabilities=total_vulnerabilities,
            vulnerabilities_by_severity=vulnerabilities_by_severity,
            vulnerabilities_by_status=vulnerabilities_by_status,
            vulnerabilities_by_type=vulnerabilities_by_type,
            verified_vulnerabilities=verified_vulnerabilities,
            overdue_vulnerabilities=overdue_vulnerabilities,
            recent_vulnerabilities=recent_vulnerabilities,
            average_cvss_score=average_cvss_score
        )

    except Exception as e:
        logger.error(f"Failed to get vulnerability statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vulnerability statistics"
        )


@router.post("/", response_model=VulnerabilityResponse)
async def create_vulnerability(
    vulnerability_data: VulnerabilityCreate,
    current_user: User = Depends(require_permission("vulnerability:create"))
):
    """Create a new vulnerability"""

    try:
        # Verify target asset exists
        from app.api.models.asset import Asset
        asset = await Asset.get(vulnerability_data.target_asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target asset not found"
            )

        # Create vulnerability
        vulnerability = Vulnerability(
            **vulnerability_data.dict(),
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            discovery_date=datetime.utcnow()
        )

        await vulnerability.insert()

        logger.info(f"Vulnerability created: {vulnerability.title} by {current_user.username}")

        return VulnerabilityResponse(**vulnerability.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create vulnerability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vulnerability"
        )


@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    vulnerability_id: str,
    current_user: User = Depends(require_permission("vulnerability:read"))
):
    """Get vulnerability by ID"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    return VulnerabilityResponse(**vulnerability.dict())


@router.put("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vulnerability_id: str,
    vulnerability_update: VulnerabilityUpdate,
    current_user: User = Depends(require_permission("vulnerability:update"))
):
    """Update vulnerability"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    try:
        # Update fields
        update_data = vulnerability_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(vulnerability, field, value)

        vulnerability.updated_by = current_user.username
        vulnerability.updated_at = datetime.utcnow()

        await vulnerability.save()

        logger.info(f"Vulnerability updated: {vulnerability.title} by {current_user.username}")

        return VulnerabilityResponse(**vulnerability.dict())

    except Exception as e:
        logger.error(f"Failed to update vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vulnerability"
        )


@router.post("/{vulnerability_id}/verify")
async def verify_vulnerability(
    vulnerability_id: str,
    verification_data: VulnerabilityVerification,
    current_user: User = Depends(require_permission("vulnerability:verify"))
):
    """Verify a vulnerability"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    try:
        # Update verification status
        vulnerability.verified = verification_data.verified
        vulnerability.verified_by = current_user.username
        vulnerability.verified_at = datetime.utcnow()
        vulnerability.verification_notes = verification_data.verification_notes
        vulnerability.updated_by = current_user.username
        vulnerability.updated_at = datetime.utcnow()

        await vulnerability.save()

        # Start automated verification if requested
        if verification_data.verified and vulnerability.vulnerability_type in [
            VulnerabilityType.SQL_INJECTION,
            VulnerabilityType.XSS,
            VulnerabilityType.RCE
        ]:
            verification_task = vulnerability_verification_task.delay(
                vulnerability_id,
                {"method": "automated"}
            )
            logger.info(f"Started automated verification task: {verification_task.id}")

        logger.info(f"Vulnerability verification updated: {vulnerability.title} by {current_user.username}")

        return {"message": "Vulnerability verification updated successfully"}

    except Exception as e:
        logger.error(f"Failed to verify vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify vulnerability"
        )


@router.post("/{vulnerability_id}/comments")
async def add_vulnerability_comment(
    vulnerability_id: str,
    comment_data: VulnerabilityComment,
    current_user: User = Depends(require_permission("vulnerability:update"))
):
    """Add comment to vulnerability"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    try:
        comment = {
            "id": str(len(vulnerability.comments) + 1),
            "comment": comment_data.comment,
            "author": current_user.username,
            "created_at": datetime.utcnow().isoformat()
        }

        vulnerability.comments.append(comment)
        vulnerability.updated_by = current_user.username
        vulnerability.updated_at = datetime.utcnow()

        await vulnerability.save()

        logger.info(f"Comment added to vulnerability: {vulnerability.title} by {current_user.username}")

        return {"message": "Comment added successfully", "comment": comment}

    except Exception as e:
        logger.error(f"Failed to add comment to vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment"
        )


@router.post("/{vulnerability_id}/assign")
async def assign_vulnerability(
    vulnerability_id: str,
    assigned_to: str,
    current_user: User = Depends(require_permission("vulnerability:update"))
):
    """Assign vulnerability to a user"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    try:
        # Verify assignee exists
        from app.api.models.user import User as UserModel
        assignee = await UserModel.find_one(UserModel.username == assigned_to)
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user not found"
            )

        vulnerability.assigned_to = assigned_to
        vulnerability.updated_by = current_user.username
        vulnerability.updated_at = datetime.utcnow()

        await vulnerability.save()

        logger.info(f"Vulnerability assigned: {vulnerability.title} to {assigned_to} by {current_user.username}")

        return {"message": f"Vulnerability assigned to {assigned_to}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign vulnerability"
        )


@router.post("/{vulnerability_id}/evidence")
async def upload_evidence(
    vulnerability_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("vulnerability:update"))
):
    """Upload evidence file for vulnerability"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    try:
        # Create evidence directory
        evidence_dir = os.path.join(settings.UPLOAD_DIR, "evidence", vulnerability_id)
        os.makedirs(evidence_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(evidence_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update vulnerability
        if file.content_type.startswith("image/"):
            vulnerability.screenshots.append(file_path)
        else:
            vulnerability.evidence_files.append(file_path)

        vulnerability.updated_by = current_user.username
        vulnerability.updated_at = datetime.utcnow()

        await vulnerability.save()

        logger.info(f"Evidence uploaded for vulnerability: {vulnerability.title} by {current_user.username}")

        return {
            "message": "Evidence uploaded successfully",
            "filename": file.filename,
            "file_path": file_path
        }

    except Exception as e:
        logger.error(f"Failed to upload evidence for vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload evidence"
        )


@router.get("/{vulnerability_id}/evidence/{filename}")
async def download_evidence(
    vulnerability_id: str,
    filename: str,
    current_user: User = Depends(require_permission("vulnerability:read"))
):
    """Download evidence file"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    file_path = os.path.join(settings.UPLOAD_DIR, "evidence", vulnerability_id, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found"
        )

    return FileResponse(file_path, filename=filename)


@router.delete("/{vulnerability_id}")
async def delete_vulnerability(
    vulnerability_id: str,
    current_user: User = Depends(require_permission("vulnerability:delete"))
):
    """Delete vulnerability"""

    vulnerability = await Vulnerability.get(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    try:
        await vulnerability.delete()

        logger.info(f"Vulnerability deleted: {vulnerability.title} by {current_user.username}")

        return {"message": "Vulnerability deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vulnerability"
        )