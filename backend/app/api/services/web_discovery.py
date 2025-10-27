import asyncio
import httpx
import aiofiles
import ssl
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import re
import json
from playwright.async_api import async_playwright

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebDiscoveryService:
    """Web application discovery and reconnaissance service"""

    def __init__(self):
        self.session_timeout = 30
        self.max_concurrent = 10
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]

    async def discover_web_applications(
        self,
        targets: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Discover web applications on targets"""

        results = {
            "total_targets": len(targets),
            "discovered_applications": [],
            "discovery_time": datetime.utcnow().isoformat(),
            "errors": []
        }

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Process targets concurrently
        tasks = []
        for target in targets:
            task = self._discover_target(target, config, semaphore)
            tasks.append(task)

        target_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(target_results):
            if isinstance(result, Exception):
                results["errors"].append({
                    "target": targets[i],
                    "error": str(result)
                })
                logger.error(f"Discovery failed for {targets[i]}: {str(result)}")
            elif result:
                results["discovered_applications"].extend(result)

        return results

    async def _discover_target(
        self,
        target: str,
        config: Dict[str, Any],
        semaphore: asyncio.Semaphore
    ) -> List[Dict[str, Any]]:
        """Discover web applications for a single target"""

        async with semaphore:
            discovered_apps = []

            try:
                logger.info(f"Starting web discovery for: {target}")

                # Normalize target URL
                if not target.startswith(('http://', 'https://')):
                    targets_to_check = [f"http://{target}", f"https://{target}"]
                else:
                    targets_to_check = [target]

                for url in targets_to_check:
                    # Basic HTTP reconnaissance
                    if config.get("http_recon", True):
                        http_info = await self._http_reconnaissance(url, config)
                        if http_info:
                            discovered_apps.append(http_info)

                    # Directory/path discovery
                    if config.get("path_discovery", True):
                        paths = await self._discover_paths(url, config)
                        discovered_apps.extend(paths)

                    # Technology detection
                    if config.get("tech_detection", True):
                        tech_info = await self._detect_technologies(url, config)
                        if tech_info and "technologies" in tech_info:
                            # Update the main application info with technologies
                            if discovered_apps:
                                discovered_apps[0]["technologies"] = tech_info["technologies"]

                    # Screenshot capture
                    if config.get("screenshot", False):
                        screenshot_path = await self._capture_screenshot(url, config)
                        if screenshot_path and discovered_apps:
                            discovered_apps[0]["screenshot"] = screenshot_path

            except Exception as e:
                logger.error(f"Error discovering {target}: {str(e)}")
                raise

            return discovered_apps

    async def _http_reconnaissance(
        self,
        url: str,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Perform basic HTTP reconnaissance"""

        try:
            async with httpx.AsyncClient(
                timeout=config.get("timeout", self.session_timeout),
                verify=False,  # Skip SSL verification for discovery
                follow_redirects=True
            ) as client:

                # Add random user agent
                import random
                headers = {
                    "User-Agent": random.choice(self.user_agents)
                }

                response = await client.get(url, headers=headers)

                # Extract application information
                app_info = {
                    "url": str(response.url),
                    "original_url": url,
                    "status_code": response.status_code,
                    "title": self._extract_title(response.text),
                    "server": response.headers.get("server", ""),
                    "powered_by": response.headers.get("x-powered-by", ""),
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(response.content),
                    "headers": dict(response.headers),
                    "response_time": response.elapsed.total_seconds(),
                    "ssl_info": {},
                    "forms": [],
                    "links": [],
                    "javascript": [],
                    "cookies": [],
                    "discovery_method": "http_recon",
                    "discovery_time": datetime.utcnow().isoformat()
                }

                # Extract SSL information for HTTPS
                if url.startswith("https://"):
                    ssl_info = await self._get_ssl_info(url)
                    app_info["ssl_info"] = ssl_info

                # Extract page elements
                if response.status_code == 200:
                    app_info["forms"] = self._extract_forms(response.text)
                    app_info["links"] = self._extract_links(response.text, url)
                    app_info["javascript"] = self._extract_javascript(response.text)
                    app_info["cookies"] = [
                        {"name": cookie.name, "value": cookie.value}
                        for cookie in client.cookies
                    ]

                return app_info

        except Exception as e:
            logger.error(f"HTTP recon failed for {url}: {str(e)}")
            return None

    async def _discover_paths(
        self,
        base_url: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Discover paths/directories"""

        discovered_paths = []

        # Common paths to check
        common_paths = config.get("common_paths", [
            "/admin", "/administrator", "/login", "/wp-admin", "/phpmyadmin",
            "/api", "/api/v1", "/swagger", "/docs", "/test", "/dev",
            "/backup", "/tmp", "/uploads", "/files", "/images",
            "/css", "/js", "/assets", "/static", "/public",
            "/config", "/conf", "/etc", "/.env", "/.git",
            "/robots.txt", "/sitemap.xml", "/.well-known"
        ])

        # Custom wordlist
        if config.get("wordlist_path"):
            try:
                async with aiofiles.open(config["wordlist_path"], 'r') as f:
                    custom_paths = await f.readlines()
                    common_paths.extend([path.strip() for path in custom_paths])
            except Exception as e:
                logger.warning(f"Failed to load wordlist: {str(e)}")

        # Check paths concurrently
        semaphore = asyncio.Semaphore(config.get("path_concurrency", 20))
        tasks = []

        for path in common_paths[:config.get("max_paths", 100)]:
            task = self._check_path(base_url, path, config, semaphore)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, dict) and result.get("status_code") not in [404, 403]:
                discovered_paths.append(result)

        return discovered_paths

    async def _check_path(
        self,
        base_url: str,
        path: str,
        config: Dict[str, Any],
        semaphore: asyncio.Semaphore
    ) -> Optional[Dict[str, Any]]:
        """Check if a specific path exists"""

        async with semaphore:
            try:
                url = urljoin(base_url, path)

                async with httpx.AsyncClient(
                    timeout=config.get("timeout", 10),
                    verify=False
                ) as client:

                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; WebDiscovery/1.0)"
                    })

                    if response.status_code not in [404]:
                        return {
                            "url": url,
                            "path": path,
                            "status_code": response.status_code,
                            "content_length": len(response.content),
                            "title": self._extract_title(response.text),
                            "discovery_method": "path_discovery"
                        }

            except Exception as e:
                logger.debug(f"Path check failed for {base_url}{path}: {str(e)}")

            return None

    async def _detect_technologies(
        self,
        url: str,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Detect web technologies"""

        try:
            async with httpx.AsyncClient(
                timeout=config.get("timeout", 30),
                verify=False
            ) as client:

                response = await client.get(url)

                if response.status_code != 200:
                    return None

                technologies = []

                # Check headers
                headers_tech = self._analyze_headers(response.headers)
                technologies.extend(headers_tech)

                # Check HTML content
                content_tech = self._analyze_content(response.text)
                technologies.extend(content_tech)

                # Check JavaScript libraries
                js_tech = self._analyze_javascript_libs(response.text)
                technologies.extend(js_tech)

                return {
                    "url": url,
                    "technologies": technologies,
                    "discovery_method": "technology_detection"
                }

        except Exception as e:
            logger.error(f"Technology detection failed for {url}: {str(e)}")
            return None

    def _analyze_headers(self, headers: httpx.Headers) -> List[Dict[str, Any]]:
        """Analyze HTTP headers for technology detection"""

        technologies = []

        # Server header
        server = headers.get("server", "").lower()
        if "nginx" in server:
            technologies.append({"name": "Nginx", "version": self._extract_version(server, "nginx")})
        elif "apache" in server:
            technologies.append({"name": "Apache", "version": self._extract_version(server, "apache")})
        elif "iis" in server:
            technologies.append({"name": "IIS", "version": self._extract_version(server, "iis")})

        # X-Powered-By header
        powered_by = headers.get("x-powered-by", "").lower()
        if "php" in powered_by:
            technologies.append({"name": "PHP", "version": self._extract_version(powered_by, "php")})
        elif "asp.net" in powered_by:
            technologies.append({"name": "ASP.NET", "version": self._extract_version(powered_by, "asp.net")})

        # Framework detection
        if "x-framework" in headers:
            framework = headers["x-framework"]
            technologies.append({"name": framework, "category": "Framework"})

        return technologies

    def _analyze_content(self, content: str) -> List[Dict[str, Any]]:
        """Analyze HTML content for technology detection"""

        technologies = []

        # WordPress detection
        if "wp-content" in content or "wordpress" in content.lower():
            version_match = re.search(r'ver=([\d.]+)', content)
            version = version_match.group(1) if version_match else None
            technologies.append({"name": "WordPress", "version": version, "category": "CMS"})

        # Drupal detection
        if "drupal" in content.lower() or 'generator.*drupal' in content.lower():
            technologies.append({"name": "Drupal", "category": "CMS"})

        # Joomla detection
        if "joomla" in content.lower():
            technologies.append({"name": "Joomla", "category": "CMS"})

        # React detection
        if "react" in content.lower() or "_react" in content or "data-reactroot" in content:
            technologies.append({"name": "React", "category": "JavaScript Framework"})

        # Vue.js detection
        if "vue.js" in content.lower() or "__vue__" in content:
            technologies.append({"name": "Vue.js", "category": "JavaScript Framework"})

        # Angular detection
        if "angular" in content.lower() or "ng-app" in content:
            technologies.append({"name": "Angular", "category": "JavaScript Framework"})

        # Bootstrap detection
        if "bootstrap" in content.lower():
            version_match = re.search(r'bootstrap[/-]v?([\d.]+)', content.lower())
            version = version_match.group(1) if version_match else None
            technologies.append({"name": "Bootstrap", "version": version, "category": "CSS Framework"})

        return technologies

    def _analyze_javascript_libs(self, content: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript libraries"""

        technologies = []

        # jQuery detection
        jquery_match = re.search(r'jquery[/-]v?([\d.]+)', content.lower())
        if jquery_match:
            technologies.append({
                "name": "jQuery",
                "version": jquery_match.group(1),
                "category": "JavaScript Library"
            })
        elif "jquery" in content.lower():
            technologies.append({"name": "jQuery", "category": "JavaScript Library"})

        return technologies

    async def _capture_screenshot(
        self,
        url: str,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """Capture screenshot of web page"""

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(
                    viewport={"width": 1920, "height": 1080}
                )

                # Navigate to page
                await page.goto(url, timeout=30000, wait_until="networkidle")

                # Generate screenshot path
                parsed_url = urlparse(url)
                filename = f"{parsed_url.hostname}_{int(datetime.utcnow().timestamp())}.png"
                screenshot_path = f"/tmp/screenshots/{filename}"

                # Ensure directory exists
                import os
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

                # Take screenshot
                await page.screenshot(path=screenshot_path, full_page=True)

                await browser.close()

                return screenshot_path

        except Exception as e:
            logger.error(f"Screenshot capture failed for {url}: {str(e)}")
            return None

    async def _get_ssl_info(self, url: str) -> Dict[str, Any]:
        """Get SSL certificate information"""

        ssl_info = {}

        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443

            # Get SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Connect and get certificate
            import socket
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    if cert:
                        ssl_info = {
                            "subject": dict(x[0] for x in cert.get('subject', [])),
                            "issuer": dict(x[0] for x in cert.get('issuer', [])),
                            "version": cert.get('version'),
                            "serial_number": cert.get('serialNumber'),
                            "not_before": cert.get('notBefore'),
                            "not_after": cert.get('notAfter'),
                            "signature_algorithm": cert.get('signatureAlgorithm'),
                            "san": cert.get('subjectAltName', [])
                        }

        except Exception as e:
            logger.debug(f"SSL info extraction failed for {url}: {str(e)}")

        return ssl_info

    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML"""

        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        return ""

    def _extract_forms(self, html: str) -> List[Dict[str, Any]]:
        """Extract forms from HTML"""

        forms = []
        form_matches = re.finditer(r'<form[^>]*>(.*?)</form>', html, re.IGNORECASE | re.DOTALL)

        for form_match in form_matches:
            form_html = form_match.group(0)

            # Extract form attributes
            form_info = {
                "action": self._extract_attribute(form_html, "action"),
                "method": self._extract_attribute(form_html, "method") or "GET",
                "inputs": []
            }

            # Extract input fields
            input_matches = re.finditer(r'<input[^>]*>', form_html, re.IGNORECASE)
            for input_match in input_matches:
                input_html = input_match.group(0)
                input_info = {
                    "type": self._extract_attribute(input_html, "type") or "text",
                    "name": self._extract_attribute(input_html, "name"),
                    "value": self._extract_attribute(input_html, "value"),
                }
                form_info["inputs"].append(input_info)

            forms.append(form_info)

        return forms

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML"""

        links = []
        link_matches = re.finditer(r'<a[^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)

        for link_match in link_matches:
            href = link_match.group(1)
            if href:
                # Convert relative URLs to absolute
                if href.startswith(('http://', 'https://')):
                    links.append(href)
                else:
                    absolute_url = urljoin(base_url, href)
                    links.append(absolute_url)

        return list(set(links))  # Remove duplicates

    def _extract_javascript(self, html: str) -> List[str]:
        """Extract JavaScript sources from HTML"""

        js_sources = []

        # Extract external JavaScript files
        script_matches = re.finditer(r'<script[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for script_match in script_matches:
            js_sources.append(script_match.group(1))

        return js_sources

    def _extract_attribute(self, html: str, attribute: str) -> Optional[str]:
        """Extract HTML attribute value"""

        pattern = rf'{attribute}=["\']([^"\']*)["\']'
        match = re.search(pattern, html, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_version(self, text: str, software: str) -> Optional[str]:
        """Extract version number from text"""

        pattern = rf'{software}[/-]v?([\d.]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None