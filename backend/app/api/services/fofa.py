import asyncio
import httpx
import json
import base64
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FOFAClient:
    """FOFA search API client"""

    def __init__(self, api_email: str = None, api_key: str = None):
        self.api_email = api_email or settings.FOFA_API_EMAIL
        self.api_key = api_key or settings.FOFA_API_KEY
        self.base_url = "https://fofa.so/api/v1"

        if not self.api_email or not self.api_key:
            logger.warning("FOFA API credentials not configured")

    async def search(
        self,
        query: str,
        size: int = 100,
        page: int = 1,
        fields: List[str] = None,
        full: bool = False
    ) -> Dict[str, Any]:
        """Search FOFA with given query"""

        if not self.api_email or not self.api_key:
            raise ValueError("FOFA API credentials not configured")

        try:
            # Default fields
            if not fields:
                fields = [
                    "host", "ip", "port", "protocol", "title", "country",
                    "province", "city", "server", "banner"
                ]

            # Encode query
            query_encoded = base64.b64encode(query.encode()).decode()

            # Build request parameters
            params = {
                "email": self.api_email,
                "key": self.api_key,
                "qbase64": query_encoded,
                "size": size,
                "page": page,
                "fields": ",".join(fields),
                "full": "true" if full else "false"
            }

            # Make API request
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/search/all", params=params)
                response.raise_for_status()

                result = response.json()

                if not result.get("error"):
                    return self._parse_search_results(result, fields)
                else:
                    raise Exception(f"FOFA API error: {result.get('errmsg', 'Unknown error')}")

        except httpx.HTTPError as e:
            logger.error(f"FOFA API HTTP error: {str(e)}")
            raise Exception(f"FOFA API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"FOFA search error: {str(e)}")
            raise

    def _parse_search_results(self, result: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Parse FOFA search results"""

        parsed_results = {
            "query": result.get("query", ""),
            "size": result.get("size", 0),
            "page": result.get("page", 1),
            "total": result.get("size", 0),
            "results": []
        }

        # Parse results
        for item in result.get("results", []):
            if isinstance(item, list) and len(item) >= len(fields):
                result_item = {}
                for i, field in enumerate(fields):
                    if i < len(item):
                        result_item[field] = item[i]
                parsed_results["results"].append(result_item)

        return parsed_results

    async def get_user_info(self) -> Dict[str, Any]:
        """Get FOFA user account information"""

        if not self.api_email or not self.api_key:
            raise ValueError("FOFA API credentials not configured")

        try:
            params = {
                "email": self.api_email,
                "key": self.api_key
            }

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.base_url}/info/my", params=params)
                response.raise_for_status()

                return response.json()

        except Exception as e:
            logger.error(f"FOFA get user info error: {str(e)}")
            raise

    def build_query(self, **kwargs) -> str:
        """Build FOFA search query from parameters"""

        query_parts = []

        # Common search parameters
        if kwargs.get("domain"):
            query_parts.append(f'domain="{kwargs["domain"]}"')

        if kwargs.get("ip"):
            query_parts.append(f'ip="{kwargs["ip"]}"')

        if kwargs.get("port"):
            if isinstance(kwargs["port"], list):
                port_query = " || ".join(f'port="{p}"' for p in kwargs["port"])
                query_parts.append(f"({port_query})")
            else:
                query_parts.append(f'port="{kwargs["port"]}"')

        if kwargs.get("protocol"):
            query_parts.append(f'protocol="{kwargs["protocol"]}"')

        if kwargs.get("title"):
            query_parts.append(f'title="{kwargs["title"]}"')

        if kwargs.get("server"):
            query_parts.append(f'server="{kwargs["server"]}"')

        if kwargs.get("banner"):
            query_parts.append(f'banner="{kwargs["banner"]}"')

        if kwargs.get("cert"):
            query_parts.append(f'cert="{kwargs["cert"]}"')

        if kwargs.get("country"):
            query_parts.append(f'country="{kwargs["country"]}"')

        if kwargs.get("city"):
            query_parts.append(f'city="{kwargs["city"]}"')

        if kwargs.get("os"):
            query_parts.append(f'os="{kwargs["os"]}"')

        if kwargs.get("app"):
            query_parts.append(f'app="{kwargs["app"]}"')

        # Custom query string
        if kwargs.get("custom_query"):
            query_parts.append(kwargs["custom_query"])

        return " && ".join(query_parts) if query_parts else "*"

    async def domain_search(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Search for assets related to a domain"""

        query = self.build_query(domain=domain, **kwargs)
        return await self.search(query, **kwargs)

    async def ip_search(self, ip: str, **kwargs) -> Dict[str, Any]:
        """Search for assets related to an IP"""

        query = self.build_query(ip=ip, **kwargs)
        return await self.search(query, **kwargs)

    async def subdomain_search(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Search for subdomains of a domain"""

        # Use wildcard subdomain search
        query = f'domain="{domain}" || domain="*.{domain}"'
        if kwargs.get("custom_query"):
            query += f" && {kwargs['custom_query']}"

        return await self.search(query, **kwargs)

    async def certificate_search(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Search using SSL certificate information"""

        query = self.build_query(cert=domain, **kwargs)
        return await self.search(query, **kwargs)

    async def technology_search(self, technology: str, **kwargs) -> Dict[str, Any]:
        """Search for assets using specific technology"""

        query = self.build_query(app=technology, **kwargs)
        return await self.search(query, **kwargs)

    async def vulnerability_search(self, cve_id: str, **kwargs) -> Dict[str, Any]:
        """Search for assets vulnerable to specific CVE"""

        query = f'vuln="{cve_id}"'
        if kwargs.get("custom_query"):
            query += f" && {kwargs['custom_query']}"

        return await self.search(query, **kwargs)


class FOFASearchService:
    """FOFA search service with caching and rate limiting"""

    def __init__(self):
        self.client = FOFAClient()
        self._cache = {}
        self._last_request_time = 0
        self.rate_limit_delay = 1  # seconds between requests

    async def search_with_cache(
        self,
        query: str,
        cache_ttl: int = 300,
        **kwargs
    ) -> Dict[str, Any]:
        """Search with caching support"""

        # Check cache
        cache_key = f"{query}:{json.dumps(sorted(kwargs.items()))}"
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < cache_ttl:
                logger.debug(f"Returning cached FOFA result for: {query}")
                return cached_result

        # Rate limiting
        await self._rate_limit()

        # Execute search
        try:
            result = await self.client.search(query, **kwargs)

            # Cache result
            self._cache[cache_key] = (result, datetime.now().timestamp())

            return result

        except Exception as e:
            logger.error(f"FOFA search failed: {str(e)}")
            raise

    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = datetime.now().timestamp()
        if (current_time - self._last_request_time) < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay)
        self._last_request_time = datetime.now().timestamp()

    async def discover_assets(
        self,
        targets: List[str],
        discovery_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Discover assets using FOFA for multiple targets"""

        results = []

        for target in targets:
            try:
                logger.info(f"FOFA discovery for target: {target}")

                # Determine target type
                if self._is_domain(target):
                    result = await self._discover_domain_assets(target, discovery_config)
                elif self._is_ip(target):
                    result = await self._discover_ip_assets(target, discovery_config)
                else:
                    logger.warning(f"Unknown target type: {target}")
                    continue

                results.extend(result.get("results", []))

            except Exception as e:
                logger.error(f"FOFA discovery failed for {target}: {str(e)}")

        return {
            "total_discovered": len(results),
            "assets": results,
            "discovery_time": datetime.utcnow().isoformat()
        }

    async def _discover_domain_assets(
        self,
        domain: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Discover assets for a domain"""

        discovered_assets = []

        # Direct domain search
        if config.get("search_domain", True):
            try:
                result = await self.search_with_cache(
                    self.client.build_query(domain=domain),
                    size=config.get("max_results", 100)
                )
                discovered_assets.extend(result.get("results", []))
            except Exception as e:
                logger.error(f"Domain search failed for {domain}: {str(e)}")

        # Subdomain search
        if config.get("search_subdomains", True):
            try:
                result = await self.search_with_cache(
                    f'domain="*.{domain}"',
                    size=config.get("max_results", 100)
                )
                discovered_assets.extend(result.get("results", []))
            except Exception as e:
                logger.error(f"Subdomain search failed for {domain}: {str(e)}")

        # Certificate search
        if config.get("search_certificates", True):
            try:
                result = await self.search_with_cache(
                    self.client.build_query(cert=domain),
                    size=config.get("max_results", 100)
                )
                discovered_assets.extend(result.get("results", []))
            except Exception as e:
                logger.error(f"Certificate search failed for {domain}: {str(e)}")

        return {
            "target": domain,
            "results": discovered_assets
        }

    async def _discover_ip_assets(
        self,
        ip: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Discover assets for an IP address"""

        try:
            result = await self.search_with_cache(
                self.client.build_query(ip=ip),
                size=config.get("max_results", 100)
            )

            return {
                "target": ip,
                "results": result.get("results", [])
            }

        except Exception as e:
            logger.error(f"IP search failed for {ip}: {str(e)}")
            return {"target": ip, "results": []}

    def _is_domain(self, target: str) -> bool:
        """Check if target is a domain"""
        import re
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(domain_pattern, target))

    def _is_ip(self, target: str) -> bool:
        """Check if target is an IP address"""
        import ipaddress
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get FOFA service statistics"""

        try:
            user_info = await self.client.get_user_info()

            return {
                "service": "FOFA",
                "status": "connected",
                "user_info": user_info,
                "cache_size": len(self._cache),
                "last_request": self._last_request_time
            }

        except Exception as e:
            return {
                "service": "FOFA",
                "status": "error",
                "error": str(e)
            }