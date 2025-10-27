from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import csv
import json
import io
from xml.etree import ElementTree as ET

from app.core.deps import get_current_active_user, require_permission
from app.core.database import is_database_connected
from app.api.models.user import User
from app.api.models.asset import Asset, AssetType, AssetStatus
from app.api.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetBulkCreate,
    AssetImport, AssetSearch, AssetStats
)
from app.core.celery.tasks.asset_tasks import bulk_asset_import_task, asset_discovery_task
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class BulkAssetRequest(BaseModel):
    ids: List[str]


@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    asset_type: Optional[AssetType] = None,
    status: Optional[AssetStatus] = None,
    organization: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    criticality: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """List assets with optional filtering"""

    # Demo mode - return mock assets
    if not is_database_connected():
        current_time = datetime.utcnow()
        demo_assets = [
            {
                "id": "demo_asset_1",
                "name": "web-server-01.example.com",
                "asset_type": "domain",
                "status": "active",
                "domain": "web-server-01.example.com",
                "subdomain": None,
                "ip_address": "192.168.1.100",
                "url": None,
                "port": 80,
                "protocol": None,
                "organization": "Demo Corp",
                "department": None,
                "owner": "IT Department",
                "tags": ["web", "production"],
                "criticality": "high",
                "notes": None,
                "labels": {"environment": "production", "team": "devops"},
                "service_name": "nginx",
                "service_version": "1.20.1",
                "operating_system": "Ubuntu 20.04",
                "technology_stack": ["nginx", "php", "mysql"],
                "open_ports": [{"port": 80, "protocol": "tcp", "service": "http"}],
                "ssl_info": None,
                "dns_records": [{"type": "A", "value": "192.168.1.100"}],
                "discovery_method": "manual",
                "discovery_source": "asset_management",
                "first_seen": current_time,
                "last_seen": current_time,
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": "admin",
                "updated_by": "admin",
                "parent_asset_id": None,
                "child_assets": [],
                "monitoring_enabled": True,
                "scan_enabled": True,
                "last_scan": current_time,
                "metadata": {"source": "demo_data", "version": "1.0"}
            },
            {
                "id": "demo_asset_2",
                "name": "db-server-01.example.com",
                "asset_type": "domain",
                "status": "active",
                "domain": "db-server-01.example.com",
                "subdomain": None,
                "ip_address": "192.168.1.101",
                "url": None,
                "port": 3306,
                "protocol": None,
                "organization": "Demo Corp",
                "department": None,
                "owner": "Database Team",
                "tags": ["database", "mysql", "production"],
                "criticality": "critical",
                "notes": None,
                "labels": {"environment": "production", "team": "database"},
                "service_name": "mysql",
                "service_version": "8.0.28",
                "operating_system": "Ubuntu 20.04",
                "technology_stack": ["mysql", "percona"],
                "open_ports": [{"port": 3306, "protocol": "tcp", "service": "mysql"}],
                "ssl_info": {"enabled": True, "version": "TLS 1.2"},
                "dns_records": [{"type": "A", "value": "192.168.1.101"}],
                "discovery_method": "network_scan",
                "discovery_source": "nmap",
                "first_seen": current_time,
                "last_seen": current_time,
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": "admin",
                "updated_by": "admin",
                "parent_asset_id": None,
                "child_assets": [],
                "monitoring_enabled": True,
                "scan_enabled": True,
                "last_scan": current_time,
                "metadata": {"source": "demo_data", "version": "1.0"}
            },
            {
                "id": "demo_asset_3",
                "name": "192.168.1.102",
                "asset_type": "ip",
                "status": "inactive",
                "domain": None,
                "subdomain": None,
                "ip_address": "192.168.1.102",
                "url": None,
                "port": None,
                "protocol": None,
                "organization": "Demo Corp",
                "department": None,
                "owner": "Security Team",
                "tags": ["network", "test"],
                "criticality": "low",
                "notes": None,
                "labels": {"environment": "test", "team": "security"},
                "service_name": None,
                "service_version": None,
                "operating_system": None,
                "technology_stack": [],
                "open_ports": [],
                "ssl_info": None,
                "dns_records": [],
                "discovery_method": "automated",
                "discovery_source": "network_discovery",
                "first_seen": current_time,
                "last_seen": current_time,
                "created_at": current_time,
                "updated_at": current_time,
                "created_by": "analyst",
                "updated_by": "analyst",
                "parent_asset_id": None,
                "child_assets": [],
                "monitoring_enabled": False,
                "scan_enabled": False,
                "last_scan": None,
                "metadata": {"source": "demo_data", "version": "1.0"}
            }
        ]

        # Apply basic filtering
        filtered_assets = demo_assets
        if status:
            filtered_assets = [a for a in filtered_assets if a["status"] == status]
        if criticality:
            filtered_assets = [a for a in filtered_assets if a["criticality"] == criticality]

        # Apply pagination
        start = skip
        end = skip + limit
        paginated_assets = filtered_assets[start:end]

        logger.info(f"Demo mode: returning {len(paginated_assets)} mock assets")
        return [AssetResponse(**asset) for asset in paginated_assets]

    # Build query filters
    filters = {}

    if asset_type:
        filters["asset_type"] = asset_type
    if status:
        filters["status"] = status
    if organization:
        filters["organization"] = organization
    if criticality:
        filters["criticality"] = criticality
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        filters["tags"] = {"$in": tag_list}

    # Execute query
    query = Asset.find(filters)
    assets = await query.skip(skip).limit(limit).to_list()

    return [AssetResponse(**asset.dict()) for asset in assets]


@router.post("/search", response_model=List[AssetResponse])
async def search_assets(
    search_params: AssetSearch,
    current_user: User = Depends(require_permission("asset:read"))
):
    """Advanced asset search"""

    filters = {}

    # Text search
    if search_params.query:
        filters["$text"] = {"$search": search_params.query}

    # Specific field filters
    if search_params.asset_type:
        filters["asset_type"] = search_params.asset_type
    if search_params.status:
        filters["status"] = search_params.status
    if search_params.organization:
        filters["organization"] = {"$regex": search_params.organization, "$options": "i"}
    if search_params.criticality:
        filters["criticality"] = search_params.criticality
    if search_params.tags:
        filters["tags"] = {"$in": search_params.tags}

    # Date filters
    if search_params.created_after or search_params.created_before:
        date_filter = {}
        if search_params.created_after:
            date_filter["$gte"] = search_params.created_after
        if search_params.created_before:
            date_filter["$lte"] = search_params.created_before
        filters["created_at"] = date_filter

    # Execute search
    query = Asset.find(filters)
    assets = await query.skip(search_params.skip).limit(search_params.limit).to_list()

    return [AssetResponse(**asset.dict()) for asset in assets]


@router.get("/stats", response_model=AssetStats)
async def get_asset_statistics(
    current_user: User = Depends(require_permission("asset:read"))
):
    """Get asset statistics"""

    try:
        # Count total assets
        total_assets = await Asset.count()

        # Count by type
        assets_by_type = {}
        for asset_type in AssetType:
            count = await Asset.find(Asset.asset_type == asset_type).count()
            assets_by_type[asset_type] = count

        # Count by status
        assets_by_status = {}
        for asset_status in AssetStatus:
            count = await Asset.find(Asset.status == asset_status).count()
            assets_by_status[asset_status] = count

        # Count by criticality
        assets_by_criticality = {}
        for criticality in ["low", "medium", "high", "critical"]:
            count = await Asset.find(Asset.criticality == criticality).count()
            assets_by_criticality[criticality] = count

        # Count recent assets (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_assets = await Asset.find(Asset.created_at >= week_ago).count()

        # Count monitored and scan-enabled assets
        monitored_assets = await Asset.find(Asset.monitoring_enabled == True).count()
        scan_enabled_assets = await Asset.find(Asset.scan_enabled == True).count()

        return AssetStats(
            total_assets=total_assets,
            assets_by_type=assets_by_type,
            assets_by_status=assets_by_status,
            assets_by_criticality=assets_by_criticality,
            recent_assets=recent_assets,
            monitored_assets=monitored_assets,
            scan_enabled_assets=scan_enabled_assets
        )

    except Exception as e:
        logger.error(f"Failed to get asset statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset statistics"
        )


@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new asset"""

    # Demo mode - return mock created asset
    if not is_database_connected():
        demo_asset = {
            "id": f"demo_asset_{len(asset_data.name)}",
            "name": asset_data.name,
            "asset_type": asset_data.asset_type,
            "status": "active",
            "domain": getattr(asset_data, 'domain', None),
            "ip_address": getattr(asset_data, 'ip_address', None),
            "port": getattr(asset_data, 'port', None),
            "organization": getattr(asset_data, 'organization', "Demo Corp"),
            "owner": getattr(asset_data, 'owner', current_user.username),
            "tags": getattr(asset_data, 'tags', []),
            "criticality": getattr(asset_data, 'criticality', "medium"),
            "monitoring_enabled": getattr(asset_data, 'monitoring_enabled', True),
            "scan_enabled": getattr(asset_data, 'scan_enabled', True),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": current_user.username,
            "updated_by": current_user.username,
            "last_seen": datetime.utcnow().isoformat()
        }

        logger.info(f"Demo mode: mock asset created: {demo_asset['name']} by {current_user.username}")
        return AssetResponse(**demo_asset)

    try:
        # Check for duplicate asset
        existing_asset = await Asset.find_one(
            {"$and": [
                {"name": asset_data.name},
                {"asset_type": asset_data.asset_type}
            ]}
        )

        if existing_asset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset '{asset_data.name}' of type '{asset_data.asset_type}' already exists"
            )

        # Create new asset
        asset = Asset(
            **asset_data.dict(),
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await asset.insert()

        logger.info(f"Asset created: {asset.name} by {current_user.username}")

        return AssetResponse(**asset.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create asset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create asset"
        )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:read"))
):
    """Get asset by ID"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    return AssetResponse(**asset.dict())


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset_update: AssetUpdate,
    current_user: User = Depends(require_permission("asset:update"))
):
    """Update asset"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        # Update fields
        update_data = asset_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(asset, field, value)

        asset.updated_by = current_user.username
        asset.updated_at = datetime.utcnow()
        asset.last_seen = datetime.utcnow()

        await asset.save()

        logger.info(f"Asset updated: {asset.name} by {current_user.username}")

        return AssetResponse(**asset.dict())

    except Exception as e:
        logger.error(f"Failed to update asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update asset"
        )


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:delete"))
):
    """Delete asset"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        await asset.delete()

        logger.info(f"Asset deleted: {asset.name} by {current_user.username}")

        return {"message": "Asset deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete asset"
        )


@router.post("/bulk", response_model=dict)
async def bulk_create_assets(
    bulk_data: AssetBulkCreate,
    current_user: User = Depends(require_permission("asset:create"))
):
    """Bulk create assets"""

    try:
        # Convert to list of dicts for Celery task
        assets_data = [asset.dict() for asset in bulk_data.assets]

        # Start bulk import task
        task = bulk_asset_import_task.delay(current_user.id, assets_data)

        logger.info(f"Bulk asset import started by {current_user.username}: {len(assets_data)} assets")

        return {
            "message": "Bulk import started",
            "task_id": task.id,
            "assets_count": len(assets_data)
        }

    except Exception as e:
        logger.error(f"Failed to start bulk asset import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bulk asset import"
        )


@router.post("/import")
async def import_assets(
    file: UploadFile = File(...),
    auto_create_missing: bool = True,
    update_existing: bool = False,
    current_user: User = Depends(require_permission("asset:create"))
):
    """Import assets from file"""

    try:
        content = await file.read()

        # Parse file based on extension
        assets_data = []

        if file.filename.endswith('.csv'):
            assets_data = parse_csv_assets(content.decode('utf-8'))
        elif file.filename.endswith('.json'):
            assets_data = parse_json_assets(content.decode('utf-8'))
        elif file.filename.endswith('.xml'):
            assets_data = parse_nmap_xml_assets(content.decode('utf-8'))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Supported: CSV, JSON, XML"
            )

        # Start bulk import task
        task = bulk_asset_import_task.delay(current_user.id, assets_data)

        logger.info(f"Asset import started by {current_user.username}: {len(assets_data)} assets from {file.filename}")

        return {
            "message": "Asset import started",
            "task_id": task.id,
            "assets_count": len(assets_data),
            "filename": file.filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import assets: {str(e)}"
        )


@router.get("/export/csv")
async def export_assets_csv(
    current_user: User = Depends(require_permission("asset:read"))
):
    """Export assets as CSV"""

    try:
        assets = await Asset.find_all().to_list()

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Name', 'Type', 'Status', 'Domain', 'IP Address', 'Port',
            'Organization', 'Owner', 'Tags', 'Criticality', 'Created At'
        ])

        # Write data
        for asset in assets:
            writer.writerow([
                asset.name,
                asset.asset_type.value,
                asset.status.value,
                asset.domain or '',
                str(asset.ip_address) if asset.ip_address else '',
                asset.port or '',
                asset.organization or '',
                asset.owner or '',
                ','.join(asset.tags),
                asset.criticality,
                asset.created_at.isoformat()
            ])

        output.seek(0)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=assets.csv"}
        )

    except Exception as e:
        logger.error(f"Failed to export assets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export assets"
        )


@router.post("/discover")
async def discover_assets(
    targets: List[str],
    discovery_config: Dict[str, Any] = {},
    current_user: User = Depends(require_permission("asset:create"))
):
    """Start asset discovery task"""

    try:
        # Validate targets
        if not targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No targets provided"
            )

        # Start asset discovery task
        task = asset_discovery_task.delay(targets, discovery_config)

        logger.info(f"Asset discovery started by {current_user.username}: {len(targets)} targets")

        return {
            "message": "Asset discovery started",
            "task_id": task.id,
            "targets_count": len(targets)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start asset discovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start asset discovery"
        )


@router.post("/{asset_id}/scan")
async def scan_asset(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:scan"))
):
    """Start scan for a specific asset"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        # Create a scan task for this asset
        from app.api.models.task import ScanTask, TaskType, TaskStatus, TaskPriority

        scan_task = ScanTask(
            name=f"Asset Scan - {asset.name}",
            description=f"Automated scan for asset {asset.name}",
            task_type=TaskType.PORT_SCAN,
            priority=TaskPriority.NORMAL,
            target_assets=[str(asset.id)],
            target_domains=[asset.domain] if asset.domain else [],
            target_ips=[str(asset.ip_address)] if asset.ip_address else [],
            target_urls=[],
            config={"scan_type": "comprehensive"},
            scan_profile="default",
            engine="nmap",
            schedule_type="immediate",
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await scan_task.insert()

        logger.info(f"Asset scan initiated: {asset.name} by {current_user.username}")

        return {"message": "Asset scan started", "task_id": str(scan_task.id)}

    except Exception as e:
        logger.error(f"Failed to start asset scan for {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start asset scan"
        )


@router.post("/bulk-scan")
async def bulk_scan_assets(
    request_data: BulkAssetRequest,
    current_user: User = Depends(require_permission("asset:scan"))
):
    """Start scans for multiple assets"""

    successful_scans = []
    failed_scans = []

    for asset_id in request_data.ids:
        try:
            asset = await Asset.get(asset_id)
            if not asset:
                failed_scans.append({"asset_id": asset_id, "error": "Asset not found"})
                continue

            from app.api.models.task import ScanTask, TaskType, TaskStatus, TaskPriority

            scan_task = ScanTask(
                name=f"Bulk Scan - {asset.name}",
                description=f"Bulk scan for asset {asset.name}",
                task_type=TaskType.PORT_SCAN,
                priority=TaskPriority.NORMAL,
                target_assets=[str(asset.id)],
                target_domains=[asset.domain] if asset.domain else [],
                target_ips=[str(asset.ip_address)] if asset.ip_address else [],
                target_urls=[],
                config={"scan_type": "comprehensive"},
                scan_profile="default",
                engine="nmap",
                schedule_type="immediate",
                created_by=current_user.username,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            await scan_task.insert()
            successful_scans.append({"asset_id": asset_id, "task_id": str(scan_task.id)})

        except Exception as e:
            failed_scans.append({"asset_id": asset_id, "error": str(e)})

    logger.info(f"Bulk asset scan by {current_user.username}: {len(successful_scans)} successful, {len(failed_scans)} failed")

    return {
        "message": f"Started {len(successful_scans)} scans",
        "successful_scans": successful_scans,
        "failed_scans": failed_scans
    }


@router.get("/{asset_id}/vulnerabilities")
async def get_asset_vulnerabilities(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:read"))
):
    """Get vulnerabilities for a specific asset"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        # In a real implementation, you'd query from a vulnerabilities collection
        # For now, return mock data or query from scan results
        vulnerabilities = [
            {
                "id": "vuln_1",
                "title": "Open SSH Port",
                "severity": "medium",
                "cvss_score": 5.3,
                "description": "SSH service detected on port 22",
                "port": 22,
                "service": "ssh",
                "discovered_at": datetime.utcnow().isoformat()
            }
        ]

        return {"vulnerabilities": vulnerabilities, "total": len(vulnerabilities)}

    except Exception as e:
        logger.error(f"Failed to get vulnerabilities for asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset vulnerabilities"
        )


@router.get("/{asset_id}/scan-history")
async def get_asset_scan_history(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:read"))
):
    """Get scan history for a specific asset"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        # Query scan tasks that targeted this asset
        from app.api.models.task import ScanTask

        scans = await ScanTask.find({
            "$or": [
                {"target_assets": str(asset_id)},
                {"target_domains": asset.domain} if asset.domain else {},
                {"target_ips": str(asset.ip_address)} if asset.ip_address else {}
            ]
        }).sort([("created_at", -1)]).to_list()

        scan_history = []
        for scan in scans:
            scan_history.append({
                "id": str(scan.id),
                "name": scan.name,
                "type": scan.task_type,
                "status": scan.status,
                "created_at": scan.created_at,
                "completed_at": scan.completed_at,
                "execution_time": scan.execution_time,
                "results_count": len(scan.results) if scan.results else 0
            })

        return {"scan_history": scan_history, "total": len(scan_history)}

    except Exception as e:
        logger.error(f"Failed to get scan history for asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset scan history"
        )


@router.get("/{asset_id}/activities")
async def get_asset_activities(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:read"))
):
    """Get activity log for a specific asset"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        # Mock activity data - in reality, you'd have an audit log system
        activities = [
            {
                "id": "activity_1",
                "action": "created",
                "description": f"Asset {asset.name} was created",
                "user": asset.created_by,
                "timestamp": asset.created_at,
                "details": {"asset_type": asset.asset_type}
            },
            {
                "id": "activity_2",
                "action": "updated",
                "description": f"Asset {asset.name} was last updated",
                "user": asset.updated_by,
                "timestamp": asset.updated_at,
                "details": {"last_seen": asset.last_seen}
            }
        ]

        return {"activities": activities, "total": len(activities)}

    except Exception as e:
        logger.error(f"Failed to get activities for asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset activities"
        )


@router.get("/{asset_id}/export")
async def export_single_asset(
    asset_id: str,
    current_user: User = Depends(require_permission("asset:read"))
):
    """Export single asset data"""

    asset = await Asset.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    try:
        asset_data = {
            "asset_info": asset.dict(),
            "export_metadata": {
                "exported_by": current_user.username,
                "exported_at": datetime.utcnow().isoformat(),
                "format": "json"
            }
        }

        return asset_data

    except Exception as e:
        logger.error(f"Failed to export asset {asset_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export asset"
        )


@router.delete("/bulk")
async def bulk_delete_assets(
    request_data: BulkAssetRequest,
    current_user: User = Depends(require_permission("asset:delete"))
):
    """Bulk delete multiple assets"""

    deleted_assets = []
    failed_assets = []

    for asset_id in request_data.ids:
        try:
            asset = await Asset.get(asset_id)
            if not asset:
                failed_assets.append({"asset_id": asset_id, "error": "Asset not found"})
                continue

            await asset.delete()
            deleted_assets.append(asset_id)

        except Exception as e:
            failed_assets.append({"asset_id": asset_id, "error": str(e)})

    logger.info(f"Bulk delete completed by {current_user.username}: {len(deleted_assets)} deleted, {len(failed_assets)} failed")

    return {
        "message": f"Deleted {len(deleted_assets)} assets",
        "deleted_assets": deleted_assets,
        "failed_assets": failed_assets
    }


def parse_csv_assets(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV content into asset data"""
    assets = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for row in reader:
        asset_data = {
            "name": row.get("name", "").strip(),
            "asset_type": row.get("type", "domain").lower(),
            "domain": row.get("domain", "").strip() or None,
            "ip_address": row.get("ip_address", "").strip() or None,
            "organization": row.get("organization", "").strip() or None,
            "owner": row.get("owner", "").strip() or None,
            "tags": [tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()],
            "criticality": row.get("criticality", "medium").lower()
        }

        if asset_data["name"]:
            assets.append(asset_data)

    return assets


def parse_json_assets(json_content: str) -> List[Dict[str, Any]]:
    """Parse JSON content into asset data"""
    try:
        data = json.loads(json_content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "assets" in data:
            return data["assets"]
        else:
            return [data]
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")


def parse_nmap_xml_assets(xml_content: str) -> List[Dict[str, Any]]:
    """Parse Nmap XML content into asset data"""
    assets = []

    try:
        root = ET.fromstring(xml_content)

        for host in root.findall(".//host"):
            # Get IP address
            address_elem = host.find(".//address[@addrtype='ipv4']")
            if address_elem is None:
                continue

            ip_address = address_elem.get("addr")

            # Get hostname if available
            hostname_elem = host.find(".//hostname")
            hostname = hostname_elem.get("name") if hostname_elem is not None else ip_address

            # Create asset data
            asset_data = {
                "name": hostname,
                "asset_type": "ip" if ip_address == hostname else "domain",
                "ip_address": ip_address,
                "domain": hostname if hostname != ip_address else None,
                "discovery_method": "nmap",
                "discovery_source": "nmap_import"
            }

            assets.append(asset_data)

    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {str(e)}")

    return assets