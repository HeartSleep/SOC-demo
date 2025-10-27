import re
import ipaddress
import socket
import asyncio
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import hashlib
import json


def is_valid_ip(ip_string: str) -> bool:
    """Check if string is a valid IP address"""
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def is_valid_domain(domain: str) -> bool:
    """Check if string is a valid domain name"""
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(domain_pattern, domain)) and len(domain) <= 253


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL"""
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except Exception:
        return False


def extract_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def normalize_target(target: str) -> Dict[str, Any]:
    """Normalize target and determine its type"""
    target = target.strip()

    result = {
        "original": target,
        "normalized": target,
        "type": "unknown",
        "valid": False
    }

    # Check if it's an IP address
    if is_valid_ip(target):
        result.update({
            "normalized": target,
            "type": "ip",
            "valid": True
        })

    # Check if it's a URL
    elif is_valid_url(target):
        domain = extract_domain_from_url(target)
        result.update({
            "normalized": target,
            "type": "url",
            "domain": domain,
            "valid": True
        })

    # Check if it's a domain
    elif is_valid_domain(target):
        result.update({
            "normalized": target.lower(),
            "type": "domain",
            "valid": True
        })

    # Check if it's a CIDR range
    elif "/" in target:
        try:
            ipaddress.ip_network(target, strict=False)
            result.update({
                "normalized": target,
                "type": "cidr",
                "valid": True
            })
        except ValueError:
            pass

    return result


def expand_cidr_range(cidr: str, max_hosts: int = 1000) -> List[str]:
    """Expand CIDR range to individual IP addresses"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        hosts = []

        for i, host in enumerate(network.hosts()):
            if i >= max_hosts:
                break
            hosts.append(str(host))

        return hosts
    except ValueError:
        return []


def extract_subdomains(domain: str, content: str) -> List[str]:
    """Extract subdomains from content"""
    subdomains = set()

    # Regex pattern to find subdomains
    subdomain_pattern = rf'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{{0,61}}[a-zA-Z0-9])?\.)+{re.escape(domain)}'

    matches = re.finditer(subdomain_pattern, content, re.IGNORECASE)
    for match in matches:
        subdomain = match.group(0).lower()
        if subdomain != domain and is_valid_domain(subdomain):
            subdomains.add(subdomain)

    return list(subdomains)


async def resolve_domain(domain: str, timeout: int = 5) -> List[str]:
    """Resolve domain to IP addresses"""
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyname_ex, domain),
            timeout=timeout
        )
        return result[2]  # Return IP addresses
    except Exception:
        return []


async def reverse_dns_lookup(ip: str, timeout: int = 5) -> Optional[str]:
    """Perform reverse DNS lookup"""
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyaddr, ip),
            timeout=timeout
        )
        return result[0]  # Return hostname
    except Exception:
        return None


def calculate_risk_score(
    vulnerability_count: Dict[str, int],
    asset_criticality: str = "medium",
    exposure_level: str = "internal"
) -> float:
    """Calculate risk score based on vulnerabilities and asset properties"""

    # Base scores for different severity levels
    severity_weights = {
        "critical": 10.0,
        "high": 7.5,
        "medium": 5.0,
        "low": 2.5,
        "info": 0.5
    }

    # Calculate base vulnerability score
    vuln_score = 0
    for severity, count in vulnerability_count.items():
        weight = severity_weights.get(severity.lower(), 0)
        vuln_score += weight * count

    # Asset criticality multiplier
    criticality_multipliers = {
        "critical": 2.0,
        "high": 1.5,
        "medium": 1.0,
        "low": 0.5
    }
    criticality_multiplier = criticality_multipliers.get(asset_criticality.lower(), 1.0)

    # Exposure level multiplier
    exposure_multipliers = {
        "external": 2.0,
        "dmz": 1.5,
        "internal": 1.0,
        "isolated": 0.5
    }
    exposure_multiplier = exposure_multipliers.get(exposure_level.lower(), 1.0)

    # Calculate final risk score
    risk_score = vuln_score * criticality_multiplier * exposure_multiplier

    # Cap at 100
    return min(risk_score, 100.0)


def generate_task_id(task_type: str, targets: List[str]) -> str:
    """Generate unique task ID"""
    content = f"{task_type}:{':'.join(sorted(targets))}:{datetime.utcnow().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def parse_port_range(port_range: str) -> List[int]:
    """Parse port range string into list of ports"""
    ports = []

    for part in port_range.split(','):
        part = part.strip()

        if '-' in part:
            # Port range (e.g., "80-443")
            try:
                start, end = part.split('-', 1)
                start_port = int(start.strip())
                end_port = int(end.strip())

                if start_port <= end_port and 1 <= start_port <= 65535 and 1 <= end_port <= 65535:
                    ports.extend(range(start_port, end_port + 1))
            except ValueError:
                continue
        else:
            # Single port
            try:
                port = int(part)
                if 1 <= port <= 65535:
                    ports.append(port)
            except ValueError:
                continue

    return sorted(list(set(ports)))


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove/replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first/last few characters"""
    if not data or len(data) <= visible_chars * 2:
        return mask_char * len(data) if data else ""

    prefix = data[:visible_chars]
    suffix = data[-visible_chars:]
    middle_length = len(data) - (visible_chars * 2)

    return f"{prefix}{mask_char * middle_length}{suffix}"


def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value

    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def validate_cron_expression(cron_expr: str) -> bool:
    """Validate cron expression format"""
    # Basic validation for cron expression
    # Format: minute hour day month day_of_week
    parts = cron_expr.split()

    if len(parts) != 5:
        return False

    # Each part should be either a number, range, list, or wildcard
    for part in parts:
        if not re.match(r'^(\*|(\d+(-\d+)?(,\d+(-\d+)?)*))$', part):
            return False

    return True


async def test_network_connectivity(
    host: str,
    port: int,
    timeout: int = 5
) -> bool:
    """Test network connectivity to host:port"""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'https?://(?:[-\w.])+(?::\d+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    return list(set(urls))


def calculate_percentage(part: int, total: int) -> float:
    """Calculate percentage with division by zero protection"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)