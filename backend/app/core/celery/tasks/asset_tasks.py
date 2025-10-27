from datetime import datetime
from typing import Dict, Any, List
import asyncio

from celery import current_task
from app.core.celery.celery_app import celery_app
from app.api.models.asset import Asset, AssetType, AssetStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True)
def bulk_asset_import_task(self, user_id: str, assets_data: List[Dict[str, Any]]):
    """Bulk import assets task"""
    try:
        results = {
            "total": len(assets_data),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for i, asset_data in enumerate(assets_data):
            try:
                # Create asset (this would need proper async handling in real implementation)
                logger.info(f"Processing asset: {asset_data.get('name', 'unknown')}")

                # Validate asset data
                if not validate_asset_data(asset_data):
                    raise ValueError("Invalid asset data")

                # Check for duplicates
                if check_asset_exists(asset_data):
                    logger.warning(f"Asset already exists: {asset_data['name']}")
                    results["errors"].append(f"Duplicate asset: {asset_data['name']}")
                    results["failed"] += 1
                    continue

                # Process asset creation
                process_asset_creation(asset_data, user_id)
                results["success"] += 1

                # Update progress
                progress = int((i + 1) / len(assets_data) * 100)
                current_task.update_state(
                    state="PROGRESS",
                    meta={"progress": progress, "current": i + 1, "total": len(assets_data)}
                )

            except Exception as e:
                logger.error(f"Failed to process asset {asset_data.get('name', 'unknown')}: {str(e)}")
                results["failed"] += 1
                results["errors"].append(f"Asset {asset_data.get('name', 'unknown')}: {str(e)}")

        logger.info(f"Bulk import completed: {results}")
        return results

    except Exception as e:
        logger.error(f"Bulk asset import task failed: {str(e)}")
        raise


@celery_app.task(bind=True)
def asset_discovery_task(self, targets: List[str], discovery_config: Dict[str, Any]):
    """Asset discovery task"""
    try:
        results = {
            "discovered_assets": [],
            "total_targets": len(targets),
            "processed": 0
        }

        for i, target in enumerate(targets):
            try:
                logger.info(f"Discovering assets for target: {target}")

                # Determine target type and perform appropriate discovery
                if is_domain(target):
                    assets = discover_domain_assets(target, discovery_config)
                elif is_ip_range(target):
                    assets = discover_ip_range_assets(target, discovery_config)
                else:
                    assets = discover_url_assets(target, discovery_config)

                results["discovered_assets"].extend(assets)
                results["processed"] += 1

                # Update progress
                progress = int((i + 1) / len(targets) * 100)
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": progress,
                        "discovered": len(results["discovered_assets"]),
                        "current_target": target
                    }
                )

            except Exception as e:
                logger.error(f"Failed to discover assets for {target}: {str(e)}")

        logger.info(f"Asset discovery completed: {len(results['discovered_assets'])} assets discovered")
        return results

    except Exception as e:
        logger.error(f"Asset discovery task failed: {str(e)}")
        raise


def validate_asset_data(asset_data: Dict[str, Any]) -> bool:
    """Validate asset data"""
    required_fields = ["name", "asset_type"]

    for field in required_fields:
        if field not in asset_data:
            return False

    # Validate asset type
    if asset_data["asset_type"] not in [e.value for e in AssetType]:
        return False

    return True


def check_asset_exists(asset_data: Dict[str, Any]) -> bool:
    """Check if asset already exists"""
    # This would need proper async database check
    # For now, return False
    return False


def process_asset_creation(asset_data: Dict[str, Any], user_id: str):
    """Process asset creation"""
    logger.info(f"Creating asset: {asset_data['name']}")
    # This would create the actual asset in the database
    pass


def is_domain(target: str) -> bool:
    """Check if target is a domain"""
    import re
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(domain_pattern, target))


def is_ip_range(target: str) -> bool:
    """Check if target is an IP range"""
    return "/" in target or "-" in target


def discover_domain_assets(domain: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover assets for a domain"""
    assets = []

    # Add the domain itself
    assets.append({
        "name": domain,
        "asset_type": AssetType.DOMAIN,
        "domain": domain,
        "discovery_method": "manual",
        "discovery_source": "domain_discovery"
    })

    # Discover subdomains if enabled
    if config.get("discover_subdomains", True):
        subdomains = discover_subdomains(domain, config)
        for subdomain in subdomains:
            assets.append({
                "name": subdomain,
                "asset_type": AssetType.SUBDOMAIN,
                "subdomain": subdomain,
                "domain": domain,
                "discovery_method": "automated",
                "discovery_source": "subdomain_enumeration"
            })

    # Resolve IPs if enabled
    if config.get("resolve_ips", True):
        for asset in assets:
            try:
                import socket
                ip = socket.gethostbyname(asset["name"])
                asset["ip_address"] = ip
            except socket.gaierror:
                pass

    return assets


def discover_ip_range_assets(ip_range: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover assets in IP range"""
    assets = []

    # Parse IP range and discover live hosts
    live_hosts = discover_live_hosts(ip_range)

    for host in live_hosts:
        assets.append({
            "name": host,
            "asset_type": AssetType.IP,
            "ip_address": host,
            "discovery_method": "automated",
            "discovery_source": "network_scan"
        })

    return assets


def discover_url_assets(url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Discover assets from URL"""
    assets = []

    # Extract domain from URL
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc

    assets.append({
        "name": url,
        "asset_type": AssetType.URL,
        "url": url,
        "domain": domain,
        "discovery_method": "manual",
        "discovery_source": "url_discovery"
    })

    return assets


def discover_subdomains(domain: str, config: Dict[str, Any]) -> List[str]:
    """Discover subdomains for a domain"""
    # This would use various subdomain discovery techniques
    # For now, return a simple list
    return [f"www.{domain}", f"api.{domain}", f"admin.{domain}"]


def discover_live_hosts(ip_range: str) -> List[str]:
    """Discover live hosts in IP range"""
    # This would perform network scanning to find live hosts
    # For now, return empty list
    return []