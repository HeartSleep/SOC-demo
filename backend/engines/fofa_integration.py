"""
FOFA Integration Engine - Cyber Threat Intelligence Platform
===========================================================

Advanced FOFA API integration for:
- Asset discovery and correlation
- Threat intelligence gathering
- Global exposure analysis
- Historical attack surface monitoring
- Vulnerability correlation with public exposure
"""

import asyncio
import logging
import base64
import hashlib
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp
import json
from urllib.parse import quote

logger = logging.getLogger(__name__)

@dataclass
class FOFAAsset:
    """FOFA discovered asset information"""
    ip: str
    port: int
    domain: Optional[str] = None
    title: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    organization: Optional[str] = None
    protocol: Optional[str] = None
    service: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    os: Optional[str] = None
    banner: Optional[str] = None
    cert: Optional[str] = None
    header: Optional[str] = None
    body: Optional[str] = None
    lastupdatetime: Optional[str] = None
    cname: List[str] = None
    icon_hash: Optional[str] = None
    asn: Optional[int] = None
    as_organization: Optional[str] = None
    vulnerabilities: List[str] = None

@dataclass
class FOFAQuery:
    """FOFA search query configuration"""
    query: str
    size: int = 100
    page: int = 1
    fields: List[str] = None
    full: bool = False

class FOFAEngine:
    """
    FOFA Cyber Threat Intelligence Integration

    Provides comprehensive threat intelligence and asset discovery
    through FOFA's global internet assets database
    """

    def __init__(self, fofa_email: Optional[str] = None, fofa_key: Optional[str] = None):
        """
        Initialize FOFA engine

        Args:
            fofa_email: FOFA account email
            fofa_key: FOFA API key
        """
        self.fofa_email = fofa_email or "demo@example.com"  # Demo fallback
        self.fofa_key = fofa_key or "demo_key"
        self.base_url = "https://fofa.info"
        self.api_url = f"{self.base_url}/api/v1"
        self.session = None

        # Default fields to retrieve
        self.default_fields = [
            "ip", "port", "protocol", "country", "city", "isp", "domain",
            "title", "os", "server", "product", "version", "lastupdatetime",
            "asn", "org", "banner", "cert", "header", "body", "cname"
        ]

        # Predefined search templates
        self.search_templates = {
            "web_services": 'port="80" || port="443" || port="8080" || port="8443"',
            "database_services": 'port="3306" || port="5432" || port="1433" || port="27017"',
            "remote_access": 'port="22" || port="3389" || port="5900" || port="23"',
            "email_services": 'port="25" || port="465" || port="587" || port="993"',
            "ftp_services": 'port="21" || port="22" || protocol="ftp"',
            "dns_services": 'port="53" || protocol="dns"',
            "vulnerable_services": 'product="Apache" && version<"2.4.50"',
            "exposed_databases": '"mysql" || "mongodb" || "redis" || "elasticsearch"',
            "iot_devices": 'product="webcam" || product="router" || "IoT"',
            "cloud_services": '"Amazon" || "Google Cloud" || "Microsoft Azure"'
        }

        logger.info("FOFA Engine initialized")

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'User-Agent': 'SOC-Platform-Scanner/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_assets(self, target: str, search_type: str = "comprehensive") -> List[FOFAAsset]:
        """
        Search for assets related to target

        Args:
            target: Domain, IP, or search term
            search_type: Type of search to perform

        Returns:
            List of discovered assets
        """
        assets = []

        try:
            # Build search queries based on target
            queries = self._build_search_queries(target, search_type)

            for query_config in queries:
                logger.info(f"Executing FOFA search: {query_config.query}")

                batch_assets = await self._execute_search(query_config)
                assets.extend(batch_assets)

                # Rate limiting
                await asyncio.sleep(1)

            # Remove duplicates
            unique_assets = self._deduplicate_assets(assets)

            logger.info(f"FOFA discovered {len(unique_assets)} unique assets for {target}")

        except Exception as e:
            logger.error(f"FOFA search failed for {target}: {str(e)}")

        return unique_assets

    async def threat_intelligence_lookup(self, ip_address: str) -> Dict[str, Any]:
        """
        Get threat intelligence for an IP address

        Args:
            ip_address: IP address to lookup

        Returns:
            Threat intelligence data
        """
        threat_info = {
            'ip': ip_address,
            'is_malicious': False,
            'threat_types': [],
            'first_seen': None,
            'last_seen': None,
            'associated_domains': [],
            'open_ports': [],
            'vulnerabilities': [],
            'geolocation': {},
            'asn_info': {},
            'reputation_score': 0
        }

        try:
            # Search for the IP in FOFA
            query = FOFAQuery(
                query=f'ip="{ip_address}"',
                size=100,
                fields=self.default_fields
            )

            assets = await self._execute_search(query)

            if assets:
                latest_asset = max(assets, key=lambda x: x.lastupdatetime or "")

                threat_info.update({
                    'geolocation': {
                        'country': latest_asset.country,
                        'city': latest_asset.city,
                        'isp': latest_asset.isp,
                        'organization': latest_asset.organization
                    },
                    'asn_info': {
                        'asn': latest_asset.asn,
                        'organization': latest_asset.as_organization
                    },
                    'open_ports': list(set(asset.port for asset in assets)),
                    'associated_domains': list(set(
                        asset.domain for asset in assets if asset.domain
                    ))
                })

                # Analyze for potential threats
                threat_info['threat_types'] = self._analyze_threats(assets)
                threat_info['is_malicious'] = len(threat_info['threat_types']) > 0
                threat_info['reputation_score'] = self._calculate_reputation_score(assets)

        except Exception as e:
            logger.error(f"Threat intelligence lookup failed for {ip_address}: {str(e)}")

        return threat_info

    async def monitor_attack_surface(self, organization: str) -> Dict[str, Any]:
        """
        Monitor organization's internet-facing attack surface

        Args:
            organization: Organization name or domain

        Returns:
            Attack surface analysis
        """
        attack_surface = {
            'organization': organization,
            'total_assets': 0,
            'exposed_services': {},
            'vulnerable_assets': [],
            'geographic_distribution': {},
            'risk_assessment': {},
            'recommendations': []
        }

        try:
            # Search for organization assets
            queries = [
                FOFAQuery(f'org="{organization}"', size=1000),
                FOFAQuery(f'domain="{organization}"', size=1000),
                FOFAQuery(f'cert="{organization}"', size=1000)
            ]

            all_assets = []
            for query in queries:
                assets = await self._execute_search(query)
                all_assets.extend(assets)

            # Deduplicate assets
            unique_assets = self._deduplicate_assets(all_assets)
            attack_surface['total_assets'] = len(unique_assets)

            # Analyze exposed services
            service_distribution = {}
            country_distribution = {}
            vulnerable_assets = []

            for asset in unique_assets:
                # Service distribution
                service_key = f"{asset.protocol}:{asset.port}"
                service_distribution[service_key] = service_distribution.get(service_key, 0) + 1

                # Geographic distribution
                country = asset.country or 'Unknown'
                country_distribution[country] = country_distribution.get(country, 0) + 1

                # Vulnerability analysis
                if self._is_vulnerable_asset(asset):
                    vulnerable_assets.append({
                        'ip': asset.ip,
                        'port': asset.port,
                        'service': asset.service,
                        'vulnerabilities': asset.vulnerabilities or []
                    })

            attack_surface.update({
                'exposed_services': service_distribution,
                'vulnerable_assets': vulnerable_assets,
                'geographic_distribution': country_distribution,
                'risk_assessment': self._assess_attack_surface_risk(unique_assets),
                'recommendations': self._generate_security_recommendations(unique_assets)
            })

        except Exception as e:
            logger.error(f"Attack surface monitoring failed for {organization}: {str(e)}")

        return attack_surface

    async def vulnerability_correlation(self, cve_id: str) -> List[FOFAAsset]:
        """
        Find assets potentially affected by a specific CVE

        Args:
            cve_id: CVE identifier (e.g., CVE-2023-12345)

        Returns:
            List of potentially vulnerable assets
        """
        vulnerable_assets = []

        try:
            # Build vulnerability-specific search queries
            vuln_queries = self._build_vulnerability_queries(cve_id)

            for query in vuln_queries:
                assets = await self._execute_search(query)
                vulnerable_assets.extend(assets)

            # Additional analysis for vulnerability correlation
            for asset in vulnerable_assets:
                asset.vulnerabilities = asset.vulnerabilities or []
                asset.vulnerabilities.append(cve_id)

            logger.info(f"Found {len(vulnerable_assets)} potentially vulnerable assets for {cve_id}")

        except Exception as e:
            logger.error(f"Vulnerability correlation failed for {cve_id}: {str(e)}")

        return vulnerable_assets

    # Private methods

    def _build_search_queries(self, target: str, search_type: str) -> List[FOFAQuery]:
        """Build FOFA search queries based on target and type"""
        queries = []

        if self._is_ip_address(target):
            # IP-based searches
            queries.append(FOFAQuery(f'ip="{target}"', size=100))
            queries.append(FOFAQuery(f'server="{target}" || host="{target}"', size=50))

        elif self._is_domain(target):
            # Domain-based searches
            queries.append(FOFAQuery(f'domain="{target}"', size=100))
            queries.append(FOFAQuery(f'host="{target}" || server="{target}"', size=100))
            queries.append(FOFAQuery(f'cert="{target}"', size=100))
            queries.append(FOFAQuery(f'title="{target}"', size=50))

            # Subdomain searches
            root_domain = '.'.join(target.split('.')[-2:])
            queries.append(FOFAQuery(f'domain="*.{root_domain}"', size=200))

        # Add search type specific queries
        if search_type == "comprehensive":
            for template_name, template_query in self.search_templates.items():
                combined_query = f'({template_query}) && (domain="{target}" || host="{target}")'
                queries.append(FOFAQuery(combined_query, size=50))

        return queries

    async def _execute_search(self, query: FOFAQuery) -> List[FOFAAsset]:
        """Execute a FOFA search query"""
        assets = []

        try:
            # Encode query
            query_encoded = base64.b64encode(query.query.encode()).decode()

            # Build API URL
            fields_param = ",".join(query.fields or self.default_fields)

            url = f"{self.api_url}/search/all"
            params = {
                'email': self.fofa_email,
                'key': self.fofa_key,
                'qbase64': query_encoded,
                'size': query.size,
                'page': query.page,
                'fields': fields_param,
                'full': '1' if query.full else '0'
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get('error', False):
                        logger.error(f"FOFA API error: {data.get('errmsg', 'Unknown error')}")
                        return assets

                    # Parse results
                    results = data.get('results', [])
                    fields = query.fields or self.default_fields

                    for result in results:
                        asset_data = dict(zip(fields, result))
                        asset = self._parse_fofa_asset(asset_data)
                        assets.append(asset)

                else:
                    logger.error(f"FOFA API request failed: {response.status}")

        except Exception as e:
            logger.error(f"FOFA search execution failed: {str(e)}")

        return assets

    def _parse_fofa_asset(self, data: Dict) -> FOFAAsset:
        """Parse FOFA API response data into FOFAAsset object"""
        return FOFAAsset(
            ip=data.get('ip', ''),
            port=int(data.get('port', 0)) if data.get('port') else 0,
            domain=data.get('domain'),
            title=data.get('title'),
            country=data.get('country'),
            city=data.get('city'),
            isp=data.get('isp'),
            organization=data.get('org'),
            protocol=data.get('protocol'),
            service=data.get('server'),
            product=data.get('product'),
            version=data.get('version'),
            os=data.get('os'),
            banner=data.get('banner'),
            cert=data.get('cert'),
            header=data.get('header'),
            body=data.get('body'),
            lastupdatetime=data.get('lastupdatetime'),
            cname=data.get('cname', '').split(',') if data.get('cname') else [],
            asn=int(data.get('asn', 0)) if data.get('asn') else None,
            as_organization=data.get('as_organization')
        )

    def _deduplicate_assets(self, assets: List[FOFAAsset]) -> List[FOFAAsset]:
        """Remove duplicate assets based on IP:port combination"""
        seen = set()
        unique_assets = []

        for asset in assets:
            key = f"{asset.ip}:{asset.port}"
            if key not in seen:
                seen.add(key)
                unique_assets.append(asset)

        return unique_assets

    def _analyze_threats(self, assets: List[FOFAAsset]) -> List[str]:
        """Analyze assets for potential threats"""
        threat_types = []

        for asset in assets:
            # Check for known malicious services
            if asset.service and any(malware in asset.service.lower() for malware in
                                   ['botnet', 'malware', 'trojan', 'backdoor']):
                threat_types.append('Malware')

            # Check for suspicious ports
            suspicious_ports = [4444, 5555, 6666, 7777, 31337, 12345, 54321]
            if asset.port in suspicious_ports:
                threat_types.append('Suspicious Service')

            # Check banner for threats
            if asset.banner:
                banner_lower = asset.banner.lower()
                if any(threat in banner_lower for threat in ['honeypot', 'scanner', 'exploit']):
                    threat_types.append('Security Tool')

        return list(set(threat_types))

    def _calculate_reputation_score(self, assets: List[FOFAAsset]) -> int:
        """Calculate reputation score (0-100, lower is worse)"""
        score = 100

        for asset in assets:
            # Deduct for suspicious ports
            if asset.port in [4444, 5555, 6666, 7777]:
                score -= 20

            # Deduct for old/vulnerable software
            if asset.version and any(old_ver in asset.version.lower() for old_ver in
                                   ['1.', '2.', '3.', '4.', '5.', '6.']):
                score -= 10

            # Deduct for suspicious titles
            if asset.title and any(sus in asset.title.lower() for sus in
                                 ['hacked', 'defaced', 'owned']):
                score -= 30

        return max(0, score)

    def _is_vulnerable_asset(self, asset: FOFAAsset) -> bool:
        """Check if asset appears vulnerable"""
        # Check for known vulnerable services/versions
        vulnerable_patterns = [
            ('apache', ['2.2.', '2.3.', '2.4.1', '2.4.2', '2.4.3']),
            ('nginx', ['1.0.', '1.1.', '1.2.', '1.3.']),
            ('openssh', ['5.', '6.', '7.0', '7.1', '7.2']),
            ('mysql', ['5.0.', '5.1.', '5.2.', '5.3.', '5.4.']),
        ]

        if asset.service and asset.version:
            service_lower = asset.service.lower()
            version_lower = asset.version.lower()

            for service_name, vuln_versions in vulnerable_patterns:
                if service_name in service_lower:
                    for vuln_ver in vuln_versions:
                        if vuln_ver in version_lower:
                            return True

        # Check for default credentials indicators
        if asset.banner or asset.title:
            content = (asset.banner or '') + (asset.title or '')
            default_indicators = ['default', 'admin', 'password', 'login', 'welcome']
            if any(indicator in content.lower() for indicator in default_indicators):
                return True

        return False

    def _assess_attack_surface_risk(self, assets: List[FOFAAsset]) -> Dict[str, Any]:
        """Assess attack surface risk level"""
        risk_factors = {
            'exposed_databases': 0,
            'remote_access_services': 0,
            'vulnerable_web_servers': 0,
            'unencrypted_services': 0,
            'total_exposure': len(assets)
        }

        for asset in assets:
            # Database exposure
            if asset.port in [3306, 5432, 1433, 27017, 6379]:
                risk_factors['exposed_databases'] += 1

            # Remote access
            if asset.port in [22, 3389, 5900, 23, 21]:
                risk_factors['remote_access_services'] += 1

            # Web servers with known vulns
            if asset.port in [80, 443, 8080, 8443] and self._is_vulnerable_asset(asset):
                risk_factors['vulnerable_web_servers'] += 1

            # Unencrypted services
            if asset.port in [21, 23, 25, 53, 80, 110, 143]:
                risk_factors['unencrypted_services'] += 1

        # Calculate overall risk level
        total_risk_score = sum(risk_factors.values())
        if total_risk_score > 50:
            risk_level = 'Critical'
        elif total_risk_score > 20:
            risk_level = 'High'
        elif total_risk_score > 10:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'

        risk_factors['risk_level'] = risk_level
        risk_factors['risk_score'] = total_risk_score

        return risk_factors

    def _generate_security_recommendations(self, assets: List[FOFAAsset]) -> List[str]:
        """Generate security recommendations based on discovered assets"""
        recommendations = []

        # Analyze asset exposure patterns
        exposed_dbs = [a for a in assets if a.port in [3306, 5432, 1433, 27017, 6379]]
        remote_services = [a for a in assets if a.port in [22, 3389, 5900, 23]]
        web_services = [a for a in assets if a.port in [80, 443, 8080, 8443]]

        if exposed_dbs:
            recommendations.append(
                f"🔒 Secure {len(exposed_dbs)} exposed database services behind firewall"
            )

        if remote_services:
            recommendations.append(
                f"🛡️ Implement VPN/bastion host for {len(remote_services)} remote access services"
            )

        if web_services:
            vulnerable_web = [a for a in web_services if self._is_vulnerable_asset(a)]
            if vulnerable_web:
                recommendations.append(
                    f"⬆️ Update {len(vulnerable_web)} vulnerable web servers"
                )

        # Generic recommendations
        if len(assets) > 100:
            recommendations.append("📊 Consider attack surface reduction - many services exposed")

        recommendations.append("🔍 Regular vulnerability scanning recommended")
        recommendations.append("📈 Implement continuous security monitoring")

        return recommendations

    def _build_vulnerability_queries(self, cve_id: str) -> List[FOFAQuery]:
        """Build FOFA queries for vulnerability correlation"""
        # This would contain CVE-specific search patterns
        # For now, return a generic vulnerable service search
        return [
            FOFAQuery(f'banner="{cve_id}" || body="{cve_id}"', size=100),
            FOFAQuery('product="Apache" && version<"2.4.50"', size=100),
            FOFAQuery('product="nginx" && version<"1.20.0"', size=100)
        ]

    def _is_ip_address(self, target: str) -> bool:
        """Check if target is an IP address"""
        import ipaddress
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    def _is_domain(self, target: str) -> bool:
        """Check if target is a domain"""
        return not self._is_ip_address(target) and '.' in target

logger.info("FOFA Engine module loaded")