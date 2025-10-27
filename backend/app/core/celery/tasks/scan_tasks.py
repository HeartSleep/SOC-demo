import asyncio
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import json

from celery import current_task
from app.core.celery.celery_app import celery_app
from app.api.models.task import ScanTask, TaskStatus
from app.api.models.asset import Asset, AssetStatus
from app.api.models.vulnerability import Vulnerability
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True)
def port_scan_task(self, task_id: str, targets: List[str], config: Dict[str, Any]):
    """Execute port scanning task"""
    try:
        # Update task status
        update_task_status(task_id, TaskStatus.RUNNING, {
            "message": "Starting port scan",
            "progress": 0
        })

        results = []
        total_targets = len(targets)

        for i, target in enumerate(targets):
            try:
                logger.info(f"Scanning target: {target}")

                # Build nmap command
                nmap_args = build_nmap_command(target, config)

                # Execute nmap
                result = subprocess.run(
                    nmap_args,
                    capture_output=True,
                    text=True,
                    timeout=config.get("timeout", 300)
                )

                if result.returncode == 0:
                    # Parse nmap output
                    scan_result = parse_nmap_output(result.stdout, target)
                    results.append(scan_result)

                    # Update progress
                    progress = int((i + 1) / total_targets * 100)
                    update_task_status(task_id, TaskStatus.RUNNING, {
                        "message": f"Scanned {i + 1}/{total_targets} targets",
                        "progress": progress
                    })

                else:
                    logger.error(f"Nmap failed for {target}: {result.stderr}")
                    results.append({
                        "target": target,
                        "error": result.stderr,
                        "status": "failed"
                    })

            except subprocess.TimeoutExpired:
                logger.error(f"Nmap timeout for target: {target}")
                results.append({
                    "target": target,
                    "error": "Scan timeout",
                    "status": "timeout"
                })
            except Exception as e:
                logger.error(f"Error scanning {target}: {str(e)}")
                results.append({
                    "target": target,
                    "error": str(e),
                    "status": "error"
                })

        # Complete task
        update_task_status(task_id, TaskStatus.COMPLETED, {
            "message": "Port scan completed",
            "progress": 100,
            "results": results
        })

        return {
            "status": "success",
            "results": results,
            "total_targets": total_targets,
            "successful_scans": len([r for r in results if r.get("status") == "success"])
        }

    except Exception as e:
        logger.error(f"Port scan task failed: {str(e)}")
        update_task_status(task_id, TaskStatus.FAILED, {
            "message": f"Task failed: {str(e)}",
            "error": str(e)
        })
        raise


@celery_app.task(bind=True)
def subdomain_enumeration_task(self, task_id: str, domains: List[str], config: Dict[str, Any]):
    """Execute subdomain enumeration task"""
    try:
        update_task_status(task_id, TaskStatus.RUNNING, {
            "message": "Starting subdomain enumeration",
            "progress": 0
        })

        results = []
        total_domains = len(domains)

        for i, domain in enumerate(domains):
            try:
                logger.info(f"Enumerating subdomains for: {domain}")

                # Use multiple methods for subdomain enumeration
                subdomains = set()

                # Method 1: DNS brute force
                if config.get("dns_bruteforce", True):
                    dns_subdomains = dns_bruteforce_subdomains(domain, config)
                    subdomains.update(dns_subdomains)

                # Method 2: Certificate transparency logs
                if config.get("cert_transparency", True):
                    ct_subdomains = get_cert_transparency_subdomains(domain)
                    subdomains.update(ct_subdomains)

                # Validate subdomains
                validated_subdomains = []
                for subdomain in subdomains:
                    if validate_subdomain(subdomain):
                        validated_subdomains.append({
                            "subdomain": subdomain,
                            "domain": domain,
                            "discovered_at": datetime.utcnow().isoformat()
                        })

                results.append({
                    "domain": domain,
                    "subdomains": validated_subdomains,
                    "count": len(validated_subdomains),
                    "status": "success"
                })

                # Update progress
                progress = int((i + 1) / total_domains * 100)
                update_task_status(task_id, TaskStatus.RUNNING, {
                    "message": f"Enumerated {i + 1}/{total_domains} domains",
                    "progress": progress
                })

            except Exception as e:
                logger.error(f"Error enumerating subdomains for {domain}: {str(e)}")
                results.append({
                    "domain": domain,
                    "error": str(e),
                    "status": "error"
                })

        # Complete task
        update_task_status(task_id, TaskStatus.COMPLETED, {
            "message": "Subdomain enumeration completed",
            "progress": 100,
            "results": results
        })

        return {
            "status": "success",
            "results": results,
            "total_domains": total_domains,
            "total_subdomains": sum(len(r.get("subdomains", [])) for r in results)
        }

    except Exception as e:
        logger.error(f"Subdomain enumeration task failed: {str(e)}")
        update_task_status(task_id, TaskStatus.FAILED, {
            "message": f"Task failed: {str(e)}",
            "error": str(e)
        })
        raise


def build_nmap_command(target: str, config: Dict[str, Any]) -> List[str]:
    """Build nmap command based on configuration"""
    cmd = ["nmap"]

    # Add common options
    cmd.extend(["-sS", "-O", "-sV", "-sC"])  # SYN scan, OS detection, version detection, default scripts

    # Scan type
    scan_type = config.get("scan_type", "fast")
    if scan_type == "fast":
        cmd.extend(["-T4", "-F"])  # Fast timing, fast scan (top 100 ports)
    elif scan_type == "comprehensive":
        cmd.extend(["-T3", "-p-"])  # Normal timing, all ports
    elif scan_type == "stealth":
        cmd.extend(["-T1", "-f"])  # Slow timing, fragment packets

    # Custom port range
    if config.get("port_range"):
        cmd.extend(["-p", config["port_range"]])

    # Output format
    cmd.extend(["-oA", f"/tmp/nmap_{target.replace('.', '_')}"])

    # Add target
    cmd.append(target)

    return cmd


def parse_nmap_output(nmap_output: str, target: str) -> Dict[str, Any]:
    """Parse nmap output and extract useful information"""
    result = {
        "target": target,
        "status": "success",
        "open_ports": [],
        "os_info": None,
        "services": []
    }

    lines = nmap_output.split("\n")
    for line in lines:
        line = line.strip()

        # Parse open ports
        if "/tcp" in line and "open" in line:
            parts = line.split()
            if len(parts) >= 3:
                port = parts[0].split("/")[0]
                service = parts[2] if len(parts) > 2 else "unknown"
                result["open_ports"].append({
                    "port": int(port),
                    "protocol": "tcp",
                    "service": service,
                    "state": "open"
                })

        # Parse OS information
        if "Running:" in line:
            result["os_info"] = line.replace("Running:", "").strip()

    return result


def dns_bruteforce_subdomains(domain: str, config: Dict[str, Any]) -> List[str]:
    """Perform DNS brute force for subdomain discovery"""
    # Common subdomain wordlist
    wordlist = config.get("subdomain_wordlist", [
        "www", "mail", "ftp", "webmail", "admin", "api", "test", "dev",
        "staging", "beta", "portal", "app", "mobile", "blog", "shop",
        "vpn", "remote", "secure", "ssl", "support", "help", "ns1", "ns2"
    ])

    subdomains = []
    for subdomain in wordlist:
        full_domain = f"{subdomain}.{domain}"
        try:
            import socket
            socket.gethostbyname(full_domain)
            subdomains.append(full_domain)
        except socket.gaierror:
            pass

    return subdomains


def get_cert_transparency_subdomains(domain: str) -> List[str]:
    """Get subdomains from certificate transparency logs"""
    subdomains = []
    try:
        import requests
        response = requests.get(
            f"https://crt.sh/?q=%25.{domain}&output=json",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            for cert in data:
                name_value = cert.get("name_value", "")
                for name in name_value.split("\n"):
                    name = name.strip()
                    if name and name.endswith(domain) and name not in subdomains:
                        subdomains.append(name)
    except Exception as e:
        logger.warning(f"Failed to get CT logs for {domain}: {str(e)}")

    return subdomains


def validate_subdomain(subdomain: str) -> bool:
    """Validate if subdomain resolves"""
    try:
        import socket
        socket.gethostbyname(subdomain)
        return True
    except socket.gaierror:
        return False


def update_task_status(task_id: str, status: TaskStatus, metadata: Dict[str, Any] = None):
    """Update task status in database"""
    try:
        # This would need to be properly implemented with async context
        # For now, just log the update
        logger.info(f"Task {task_id} status: {status}, metadata: {metadata}")
    except Exception as e:
        logger.error(f"Failed to update task status: {str(e)}")