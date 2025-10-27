"""
Asset Discovery Engine - Advanced Reconnaissance & DNS Intelligence
================================================================

Core module for comprehensive asset discovery including:
- Root domain enumeration
- Subdomain discovery (multi-method)
- DNS intelligence gathering with historical data
- Port scanning with service detection
- Path fuzzing and content discovery
- Host collision detection
- VHost identification (CDN/WAF detection)
"""

import asyncio
import logging
import dns.resolver
import dns.query
import dns.zone
import socket
import subprocess
import json
import ssl
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
import concurrent.futures
import ipaddress
from urllib.parse import urlparse
import aiohttp
import aiodns
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class AssetInfo:
    """Asset information container"""
    domain: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    service: Optional[str] = None
    version: Optional[str] = None
    ssl_info: Optional[Dict] = None
    headers: Optional[Dict] = None
    title: Optional[str] = None
    technologies: List[str] = None
    cdn_provider: Optional[str] = None
    waf_detected: Optional[str] = None
    discovered_at: datetime = None

@dataclass
class DNSRecord:
    """DNS record information"""
    domain: str
    record_type: str  # A, AAAA, CNAME, MX, TXT, NS, etc.
    value: str
    ttl: Optional[int] = None
    discovered_at: datetime = None

class AssetDiscoveryEngine:
    """
    Advanced asset discovery and reconnaissance engine
    """

    def __init__(self):
        self.session = None
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 10

        # Subdomain wordlists
        self.common_subdomains = [
            'www', 'api', 'app', 'admin', 'test', 'dev', 'staging', 'prod', 'mail',
            'webmail', 'ftp', 'sftp', 'ssh', 'vpn', 'remote', 'secure', 'portal',
            'dashboard', 'panel', 'cp', 'blog', 'shop', 'store', 'cdn', 'static',
            'assets', 'media', 'images', 'js', 'css', 'docs', 'help', 'support',
            'status', 'monitor', 'health', 'prometheus', 'grafana', 'kibana',
            'jenkins', 'ci', 'cd', 'git', 'gitlab', 'github', 'bitbucket',
            'jira', 'confluence', 'wiki', 'kb', 'forum', 'chat', 'slack',
            'teams', 'zoom', 'meet', 'calendar', 'email', 'smtp', 'imap', 'pop3'
        ]

        # Path discovery wordlists
        self.common_paths = [
            '/.git/', '/admin/', '/administrator/', '/panel/', '/cp/', '/dashboard/',
            '/login/', '/signin/', '/auth/', '/api/', '/v1/', '/v2/', '/graphql/',
            '/swagger/', '/docs/', '/documentation/', '/backup/', '/backups/',
            '/tmp/', '/temp/', '/test/', '/dev/', '/debug/', '/.env/', '/config/',
            '/robots.txt', '/sitemap.xml', '/.htaccess', '/.well-known/',
            '/wp-admin/', '/wp-content/', '/wp-includes/', '/phpmyadmin/',
            '/mysql/', '/database/', '/db/', '/sql/', '/uploads/', '/files/',
            '/assets/', '/static/', '/public/', '/private/', '/secure/'
        ]

        logger.info("Asset Discovery Engine initialized")

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def discover_assets(self, target: str, scan_depth: str = "normal") -> List[AssetInfo]:
        """
        Main asset discovery entry point

        Args:
            target: Domain or IP address to scan
            scan_depth: 'surface', 'normal', or 'deep'

        Returns:
            List of discovered assets
        """
        assets = []

        try:
            # Phase 1: DNS Intelligence
            dns_records = await self.gather_dns_intelligence(target)

            # Phase 2: Subdomain Discovery
            if self._is_domain(target):
                subdomains = await self.discover_subdomains(target, depth=scan_depth)
                logger.info(f"Discovered {len(subdomains)} subdomains for {target}")
            else:
                subdomains = [target]

            # Phase 3: Service Discovery
            for subdomain in subdomains[:100]:  # Limit to prevent excessive scanning
                subdomain_assets = await self.discover_services(subdomain, scan_depth)
                assets.extend(subdomain_assets)

            # Phase 4: Host Collision Detection
            collision_hosts = await self.detect_host_collisions(subdomains[:10])
            for host_info in collision_hosts:
                assets.append(host_info)

            logger.info(f"Total assets discovered for {target}: {len(assets)}")

        except Exception as e:
            logger.error(f"Asset discovery failed for {target}: {str(e)}")

        return assets

    async def gather_dns_intelligence(self, domain: str) -> List[DNSRecord]:
        """
        Comprehensive DNS intelligence gathering

        Args:
            domain: Target domain

        Returns:
            List of DNS records with intelligence
        """
        dns_records = []
        record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'SRV', 'PTR']

        for record_type in record_types:
            try:
                answers = self.dns_resolver.resolve(domain, record_type)
                for answer in answers:
                    dns_record = DNSRecord(
                        domain=domain,
                        record_type=record_type,
                        value=str(answer),
                        ttl=answers.rrset.ttl,
                        discovered_at=datetime.now()
                    )
                    dns_records.append(dns_record)

            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
                pass
            except Exception as e:
                logger.debug(f"DNS query failed for {domain} {record_type}: {str(e)}")

        # Zone transfer attempt (ethical testing only)
        try:
            zone_records = await self._attempt_zone_transfer(domain)
            dns_records.extend(zone_records)
        except Exception:
            pass

        return dns_records

    async def discover_subdomains(self, domain: str, depth: str = "normal") -> List[str]:
        """
        Multi-method subdomain discovery

        Args:
            domain: Root domain
            depth: Scan depth level

        Returns:
            List of discovered subdomains
        """
        subdomains = set()

        # Method 1: Dictionary-based enumeration
        dict_subdomains = await self._dictionary_subdomain_enum(domain, depth)
        subdomains.update(dict_subdomains)

        # Method 2: Certificate Transparency logs
        ct_subdomains = await self._certificate_transparency_search(domain)
        subdomains.update(ct_subdomains)

        # Method 3: Search engine enumeration
        if depth in ["normal", "deep"]:
            search_subdomains = await self._search_engine_enum(domain)
            subdomains.update(search_subdomains)

        # Method 4: DNS brute force with permutations
        if depth == "deep":
            brute_subdomains = await self._dns_bruteforce_advanced(domain)
            subdomains.update(brute_subdomains)

        # Validate discovered subdomains
        valid_subdomains = await self._validate_subdomains(list(subdomains))

        return sorted(valid_subdomains)

    async def discover_services(self, target: str, scan_depth: str) -> List[AssetInfo]:
        """
        Service discovery and fingerprinting

        Args:
            target: IP address or domain
            scan_depth: Scan intensity level

        Returns:
            List of discovered services
        """
        services = []

        # Port scanning
        open_ports = await self.port_scan(target, scan_depth)

        for port_info in open_ports:
            asset = AssetInfo(
                domain=target if self._is_domain(target) else None,
                ip_address=port_info.get('ip'),
                port=port_info.get('port'),
                service=port_info.get('service'),
                version=port_info.get('version'),
                discovered_at=datetime.now()
            )

            # Enhanced service fingerprinting
            if port_info.get('service') in ['http', 'https']:
                web_info = await self._fingerprint_web_service(target, port_info['port'])
                asset.headers = web_info.get('headers')
                asset.title = web_info.get('title')
                asset.technologies = web_info.get('technologies', [])
                asset.cdn_provider = web_info.get('cdn')
                asset.waf_detected = web_info.get('waf')

            if port_info.get('service') == 'https':
                asset.ssl_info = await self._analyze_ssl_certificate(target, port_info['port'])

            services.append(asset)

        return services

    async def port_scan(self, target: str, scan_depth: str) -> List[Dict]:
        """
        Comprehensive port scanning with service detection

        Args:
            target: Target IP or domain
            scan_depth: Scan intensity

        Returns:
            List of open ports with service information
        """
        open_ports = []

        # Define port ranges based on scan depth
        if scan_depth == "surface":
            port_ranges = "1-1000"
            timing = "-T4"
        elif scan_depth == "normal":
            port_ranges = "1-10000"
            timing = "-T3"
        else:  # deep
            port_ranges = "1-65535"
            timing = "-T2"

        try:
            # Nmap service detection scan
            nmap_cmd = [
                "nmap", "-sS", "-sV", "-O", "--version-intensity", "5",
                timing, "-p", port_ranges, target
            ]

            if scan_depth == "deep":
                nmap_cmd.extend(["--script", "default,vuln"])

            logger.info(f"Running nmap scan: {' '.join(nmap_cmd)}")

            result = await asyncio.create_subprocess_exec(
                *nmap_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                open_ports = self._parse_nmap_output(stdout.decode())
            else:
                logger.warning(f"Nmap scan failed: {stderr.decode()}")

        except FileNotFoundError:
            logger.warning("Nmap not found, falling back to basic port scanning")
            open_ports = await self._basic_port_scan(target, scan_depth)
        except Exception as e:
            logger.error(f"Port scan failed for {target}: {str(e)}")

        return open_ports

    async def fuzz_paths(self, base_url: str, depth: str = "normal") -> List[str]:
        """
        Path fuzzing and content discovery

        Args:
            base_url: Base URL to fuzz
            depth: Scan depth

        Returns:
            List of discovered paths
        """
        discovered_paths = []

        # Adjust wordlist size based on depth
        if depth == "surface":
            paths_to_test = self.common_paths[:50]
        elif depth == "normal":
            paths_to_test = self.common_paths[:200]
        else:  # deep
            paths_to_test = self.common_paths + await self._generate_custom_paths(base_url)

        async def test_path(path: str) -> Optional[str]:
            try:
                url = base_url.rstrip('/') + path
                async with self.session.get(url, allow_redirects=False) as response:
                    if response.status in [200, 301, 302, 401, 403]:
                        return path
            except Exception:
                pass
            return None

        # Concurrent path testing
        semaphore = asyncio.Semaphore(20)  # Limit concurrent requests

        async def bounded_test(path):
            async with semaphore:
                return await test_path(path)

        tasks = [bounded_test(path) for path in paths_to_test]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        discovered_paths = [path for path in results if isinstance(path, str) and path]

        logger.info(f"Discovered {len(discovered_paths)} paths for {base_url}")
        return discovered_paths

    async def detect_host_collisions(self, domains: List[str]) -> List[AssetInfo]:
        """
        Detect host collision vulnerabilities

        Args:
            domains: List of domains to test

        Returns:
            List of collision vulnerabilities found
        """
        collisions = []

        for domain in domains:
            try:
                # Test with custom Host headers
                test_hosts = [
                    f"admin.{domain}",
                    f"internal.{domain}",
                    f"dev.{domain}",
                    f"staging.{domain}",
                    f"test.{domain}"
                ]

                for test_host in test_hosts:
                    collision_info = await self._test_host_collision(domain, test_host)
                    if collision_info:
                        collisions.append(collision_info)

            except Exception as e:
                logger.debug(f"Host collision test failed for {domain}: {str(e)}")

        return collisions

    # Private helper methods

    async def _dictionary_subdomain_enum(self, domain: str, depth: str) -> Set[str]:
        """Dictionary-based subdomain enumeration"""
        subdomains = set()

        wordlist_size = {
            "surface": 100,
            "normal": 500,
            "deep": len(self.common_subdomains)
        }

        wordlist = self.common_subdomains[:wordlist_size.get(depth, 500)]

        async def test_subdomain(sub: str) -> Optional[str]:
            test_domain = f"{sub}.{domain}"
            try:
                answers = self.dns_resolver.resolve(test_domain, 'A')
                if answers:
                    return test_domain
            except Exception:
                pass
            return None

        # Concurrent DNS resolution
        semaphore = asyncio.Semaphore(50)

        async def bounded_test(sub):
            async with semaphore:
                return await test_subdomain(sub)

        tasks = [bounded_test(sub) for sub in wordlist]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        subdomains = {result for result in results if isinstance(result, str)}
        return subdomains

    async def _certificate_transparency_search(self, domain: str) -> Set[str]:
        """Search certificate transparency logs"""
        subdomains = set()

        try:
            ct_url = f"https://crt.sh/?q=%.{domain}&output=json"

            async with self.session.get(ct_url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    for cert in data:
                        names = cert.get('name_value', '').split('\n')
                        for name in names:
                            name = name.strip()
                            if name and name.endswith(domain) and name != domain:
                                subdomains.add(name)

        except Exception as e:
            logger.debug(f"Certificate transparency search failed for {domain}: {str(e)}")

        return subdomains

    def _parse_nmap_output(self, nmap_output: str) -> List[Dict]:
        """Parse nmap scan output"""
        open_ports = []

        lines = nmap_output.split('\n')
        current_ip = None

        for line in lines:
            line = line.strip()

            # Extract IP address
            if "Nmap scan report for" in line:
                parts = line.split()
                current_ip = parts[-1].strip('()')

            # Parse open ports
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port_service = parts[0]
                    port = int(port_service.split('/')[0])
                    service = parts[2] if len(parts) > 2 else "unknown"
                    version = ' '.join(parts[3:]) if len(parts) > 3 else ""

                    open_ports.append({
                        'ip': current_ip,
                        'port': port,
                        'service': service,
                        'version': version,
                        'state': 'open'
                    })

        return open_ports

    def _is_domain(self, target: str) -> bool:
        """Check if target is a domain name"""
        try:
            ipaddress.ip_address(target)
            return False
        except ValueError:
            return True

    async def _fingerprint_web_service(self, target: str, port: int) -> Dict:
        """Fingerprint web service for technologies, CDN, WAF"""
        info = {
            'headers': {},
            'title': None,
            'technologies': [],
            'cdn': None,
            'waf': None
        }

        try:
            protocol = 'https' if port == 443 else 'http'
            url = f"{protocol}://{target}:{port}"

            async with self.session.get(url, timeout=10) as response:
                info['headers'] = dict(response.headers)

                # Extract title
                content = await response.text()
                if '<title>' in content.lower():
                    start = content.lower().find('<title>') + 7
                    end = content.lower().find('</title>', start)
                    if end > start:
                        info['title'] = content[start:end].strip()

                # Technology detection based on headers and content
                info['technologies'] = self._detect_technologies(info['headers'], content)

                # CDN detection
                info['cdn'] = self._detect_cdn(info['headers'])

                # WAF detection
                info['waf'] = self._detect_waf(info['headers'], content)

        except Exception as e:
            logger.debug(f"Web fingerprinting failed for {target}:{port}: {str(e)}")

        return info

    def _detect_technologies(self, headers: Dict, content: str) -> List[str]:
        """Detect web technologies"""
        technologies = []

        # Server header analysis
        server = headers.get('server', '').lower()
        if 'nginx' in server:
            technologies.append('Nginx')
        if 'apache' in server:
            technologies.append('Apache')
        if 'iis' in server:
            technologies.append('IIS')

        # Framework detection
        if 'x-powered-by' in headers:
            powered_by = headers['x-powered-by'].lower()
            if 'php' in powered_by:
                technologies.append('PHP')
            if 'asp.net' in powered_by:
                technologies.append('ASP.NET')

        # Content-based detection
        content_lower = content.lower()
        if 'wordpress' in content_lower:
            technologies.append('WordPress')
        if 'drupal' in content_lower:
            technologies.append('Drupal')
        if 'joomla' in content_lower:
            technologies.append('Joomla')

        return technologies

    def _detect_cdn(self, headers: Dict) -> Optional[str]:
        """Detect CDN provider"""
        cdn_headers = {
            'cloudflare': ['cf-ray', 'cf-cache-status'],
            'akamai': ['akamai-origin-hop'],
            'amazon': ['x-amz-cf-id', 'x-amz-cf-pop'],
            'fastly': ['fastly-debug-digest'],
            'keycdn': ['x-edge-location'],
            'maxcdn': ['x-maxcdn-forwarded-for']
        }

        for cdn, header_list in cdn_headers.items():
            for header in header_list:
                if header in headers:
                    return cdn.title()

        return None

    def _detect_waf(self, headers: Dict, content: str) -> Optional[str]:
        """Detect Web Application Firewall"""
        waf_signatures = {
            'cloudflare': ['cf-ray', 'cloudflare'],
            'incapsula': ['x-iinfo', 'incap_ses'],
            'sucuri': ['x-sucuri-id'],
            'barracuda': ['barra'],
            'f5': ['x-wa-info', 'f5-bigip'],
            'aws': ['x-amzn-requestid']
        }

        # Check headers
        for waf, signatures in waf_signatures.items():
            for sig in signatures:
                for header_name, header_value in headers.items():
                    if sig.lower() in header_name.lower() or sig.lower() in header_value.lower():
                        return waf.upper()

        # Check content
        content_lower = content.lower()
        if 'blocked by' in content_lower or 'access denied' in content_lower:
            return "Unknown WAF"

        return None

logger.info("Asset Discovery Engine module loaded")