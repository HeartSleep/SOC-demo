"""
Burp Suite Integration - Professional Traffic Analysis & Vulnerability Import
===========================================================================

Advanced Burp Suite integration providing:
- Traffic redirection and flow management
- Automatic vulnerability import from Burp
- Passive scanning integration
- Request/response logging and analysis
- Extension-based communication
- Session management and authentication
"""

import asyncio
import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import requests
import base64
import hashlib
from urllib.parse import urlparse, parse_qs
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import queue

logger = logging.getLogger(__name__)

@dataclass
class BurpVulnerability:
    """Burp Suite vulnerability finding"""
    issue_id: str
    name: str
    host: str
    path: str
    location: str
    severity: str
    confidence: str
    issue_background: str
    remediation_background: str
    issue_detail: str
    remediation_detail: str
    vulnerability_classifications: List[str]
    request: str
    response: str
    discovered_at: datetime = field(default_factory=datetime.now)

@dataclass
class BurpRequest:
    """Burp Suite HTTP request/response pair"""
    request_id: str
    method: str
    url: str
    headers: Dict[str, str]
    body: str
    response_status: int
    response_headers: Dict[str, str]
    response_body: str
    timestamp: datetime = field(default_factory=datetime.now)

class BurpIntegrationServer:
    """HTTP server to receive data from Burp Suite extension"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.server = None
        self.request_queue = queue.Queue()
        self.vulnerability_queue = queue.Queue()
        self.running = False

    def start(self):
        """Start the integration server"""
        class BurpHandler(BaseHTTPRequestHandler):
            def __init__(self, parent_server, *args, **kwargs):
                self.parent_server = parent_server
                super().__init__(*args, **kwargs)

            def do_POST(self):
                """Handle POST requests from Burp extension"""
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length).decode('utf-8')

                    if self.path == '/vulnerability':
                        self._handle_vulnerability(post_data)
                    elif self.path == '/request':
                        self._handle_request(post_data)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "success"}')

                except Exception as e:
                    logger.error(f"Error handling Burp request: {str(e)}")
                    self.send_error(500)

            def _handle_vulnerability(self, data: str):
                """Handle vulnerability data from Burp"""
                try:
                    vuln_data = json.loads(data)
                    vulnerability = BurpVulnerability(
                        issue_id=vuln_data.get('issue_id', ''),
                        name=vuln_data.get('name', ''),
                        host=vuln_data.get('host', ''),
                        path=vuln_data.get('path', ''),
                        location=vuln_data.get('location', ''),
                        severity=vuln_data.get('severity', ''),
                        confidence=vuln_data.get('confidence', ''),
                        issue_background=vuln_data.get('issue_background', ''),
                        remediation_background=vuln_data.get('remediation_background', ''),
                        issue_detail=vuln_data.get('issue_detail', ''),
                        remediation_detail=vuln_data.get('remediation_detail', ''),
                        vulnerability_classifications=vuln_data.get('vulnerability_classifications', []),
                        request=vuln_data.get('request', ''),
                        response=vuln_data.get('response', '')
                    )
                    self.parent_server.vulnerability_queue.put(vulnerability)

                except Exception as e:
                    logger.error(f"Error processing vulnerability: {str(e)}")

            def _handle_request(self, data: str):
                """Handle request/response data from Burp"""
                try:
                    req_data = json.loads(data)
                    request = BurpRequest(
                        request_id=req_data.get('request_id', ''),
                        method=req_data.get('method', ''),
                        url=req_data.get('url', ''),
                        headers=req_data.get('headers', {}),
                        body=req_data.get('body', ''),
                        response_status=req_data.get('response_status', 0),
                        response_headers=req_data.get('response_headers', {}),
                        response_body=req_data.get('response_body', '')
                    )
                    self.parent_server.request_queue.put(request)

                except Exception as e:
                    logger.error(f"Error processing request: {str(e)}")

            def log_message(self, format, *args):
                """Suppress default HTTP server logging"""
                pass

        def create_handler(*args, **kwargs):
            return BurpHandler(self, *args, **kwargs)

        self.server = HTTPServer((self.host, self.port), create_handler)
        self.running = True

        # Start server in separate thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        logger.info(f"Burp integration server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the integration server"""
        if self.server:
            self.server.shutdown()
            self.running = False
            logger.info("Burp integration server stopped")

class BurpSuiteIntegration:
    """
    Main Burp Suite integration class
    """

    def __init__(self):
        self.integration_server = BurpIntegrationServer()
        self.burp_api_url = "http://127.0.0.1:1337"  # Default Burp REST API URL
        self.burp_api_key = None
        self.session = None
        self.vulnerabilities = []
        self.requests_log = []

        logger.info("Burp Suite Integration initialized")

    async def start_integration(self):
        """Start Burp Suite integration services"""
        try:
            # Start integration server
            self.integration_server.start()

            # Start background tasks
            asyncio.create_task(self._process_vulnerabilities())
            asyncio.create_task(self._process_requests())

            logger.info("Burp Suite integration started successfully")

        except Exception as e:
            logger.error(f"Failed to start Burp integration: {str(e)}")

    async def import_burp_project(self, project_path: str) -> List[BurpVulnerability]:
        """
        Import vulnerabilities from Burp Suite project file

        Args:
            project_path: Path to Burp project file

        Returns:
            List of imported vulnerabilities
        """
        vulnerabilities = []

        try:
            # Parse Burp project XML (older format)
            if project_path.endswith('.xml'):
                vulnerabilities = await self._parse_burp_xml(project_path)

            # Parse Burp project file (newer format)
            elif project_path.endswith('.burp'):
                vulnerabilities = await self._parse_burp_project(project_path)

            logger.info(f"Imported {len(vulnerabilities)} vulnerabilities from {project_path}")

        except Exception as e:
            logger.error(f"Failed to import Burp project: {str(e)}")

        return vulnerabilities

    async def scan_with_burp(self, target_urls: List[str], scan_config: Dict = None) -> str:
        """
        Initiate scan using Burp Suite REST API

        Args:
            target_urls: URLs to scan
            scan_config: Scan configuration options

        Returns:
            Task ID for tracking scan progress
        """
        task_id = None

        try:
            if not self.burp_api_key:
                logger.warning("Burp API key not configured, using extension method")
                return await self._scan_via_extension(target_urls, scan_config)

            # Use Burp REST API
            scan_data = {
                "urls": target_urls,
                "application_logins": scan_config.get("logins", []) if scan_config else [],
                "scan_configurations": [{
                    "name": "Crawl and audit - fast",
                    "type": "NamedConfiguration"
                }]
            }

            response = requests.post(
                f"{self.burp_api_url}/v0.1/scan",
                headers={
                    "X-API-Key": self.burp_api_key,
                    "Content-Type": "application/json"
                },
                json=scan_data,
                timeout=30
            )

            if response.status_code == 201:
                task_id = response.headers.get("Location", "").split("/")[-1]
                logger.info(f"Burp scan initiated with task ID: {task_id}")

        except Exception as e:
            logger.error(f"Failed to initiate Burp scan: {str(e)}")

        return task_id

    async def get_scan_status(self, task_id: str) -> Dict[str, Any]:
        """Get scan status from Burp Suite"""
        try:
            response = requests.get(
                f"{self.burp_api_url}/v0.1/scan/{task_id}",
                headers={"X-API-Key": self.burp_api_key},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get scan status: {str(e)}")

        return {}

    async def get_scan_issues(self, task_id: str) -> List[BurpVulnerability]:
        """Retrieve scan issues from Burp Suite"""
        vulnerabilities = []

        try:
            response = requests.get(
                f"{self.burp_api_url}/v0.1/scan/{task_id}/issues",
                headers={"X-API-Key": self.burp_api_key},
                timeout=30
            )

            if response.status_code == 200:
                issues_data = response.json()
                vulnerabilities = self._convert_api_issues(issues_data)

        except Exception as e:
            logger.error(f"Failed to get scan issues: {str(e)}")

        return vulnerabilities

    async def configure_passive_scanning(self, target_scope: List[str]):
        """Configure passive scanning for target scope"""
        try:
            # Enable passive scanning for specified targets
            scope_data = {
                "include": [{"enabled": True, "file": url} for url in target_scope]
            }

            response = requests.put(
                f"{self.burp_api_url}/v0.1/target/scope",
                headers={
                    "X-API-Key": self.burp_api_key,
                    "Content-Type": "application/json"
                },
                json=scope_data,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Passive scanning configured successfully")

        except Exception as e:
            logger.error(f"Failed to configure passive scanning: {str(e)}")

    async def export_traffic_log(self, output_path: str, format: str = "json"):
        """Export traffic log from Burp Suite"""
        try:
            # Get proxy history
            response = requests.get(
                f"{self.burp_api_url}/v0.1/proxy/history",
                headers={"X-API-Key": self.burp_api_key},
                timeout=30
            )

            if response.status_code == 200:
                traffic_data = response.json()

                if format == "json":
                    with open(output_path, 'w') as f:
                        json.dump(traffic_data, f, indent=2)
                elif format == "har":
                    har_data = self._convert_to_har(traffic_data)
                    with open(output_path, 'w') as f:
                        json.dump(har_data, f, indent=2)

                logger.info(f"Traffic log exported to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export traffic log: {str(e)}")

    # Private methods

    async def _process_vulnerabilities(self):
        """Background task to process vulnerabilities from extension"""
        while self.integration_server.running:
            try:
                if not self.integration_server.vulnerability_queue.empty():
                    vulnerability = self.integration_server.vulnerability_queue.get()
                    self.vulnerabilities.append(vulnerability)

                    # Process vulnerability (save to database, trigger alerts, etc.)
                    await self._handle_new_vulnerability(vulnerability)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error processing vulnerabilities: {str(e)}")

    async def _process_requests(self):
        """Background task to process requests from extension"""
        while self.integration_server.running:
            try:
                if not self.integration_server.request_queue.empty():
                    request = self.integration_server.request_queue.get()
                    self.requests_log.append(request)

                    # Process request (analyze for patterns, extract parameters, etc.)
                    await self._analyze_request(request)

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error processing requests: {str(e)}")

    async def _parse_burp_xml(self, xml_path: str) -> List[BurpVulnerability]:
        """Parse Burp Suite XML export"""
        vulnerabilities = []

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for issue in root.findall('.//issue'):
                vulnerability = BurpVulnerability(
                    issue_id=issue.find('serialNumber').text if issue.find('serialNumber') is not None else '',
                    name=issue.find('name').text if issue.find('name') is not None else '',
                    host=issue.find('host').text if issue.find('host') is not None else '',
                    path=issue.find('path').text if issue.find('path') is not None else '',
                    location=issue.find('location').text if issue.find('location') is not None else '',
                    severity=issue.find('severity').text if issue.find('severity') is not None else '',
                    confidence=issue.find('confidence').text if issue.find('confidence') is not None else '',
                    issue_background=issue.find('issueBackground').text if issue.find('issueBackground') is not None else '',
                    remediation_background=issue.find('remediationBackground').text if issue.find('remediationBackground') is not None else '',
                    issue_detail=issue.find('issueDetail').text if issue.find('issueDetail') is not None else '',
                    remediation_detail=issue.find('remediationDetail').text if issue.find('remediationDetail') is not None else '',
                    vulnerability_classifications=[],
                    request=base64.b64decode(issue.find('request').text).decode() if issue.find('request') is not None else '',
                    response=base64.b64decode(issue.find('response').text).decode() if issue.find('response') is not None else ''
                )
                vulnerabilities.append(vulnerability)

        except Exception as e:
            logger.error(f"Failed to parse Burp XML: {str(e)}")

        return vulnerabilities

    async def _parse_burp_project(self, project_path: str) -> List[BurpVulnerability]:
        """Parse Burp Suite project file (SQLite format)"""
        vulnerabilities = []

        try:
            import sqlite3

            conn = sqlite3.connect(project_path)
            cursor = conn.cursor()

            # Query issues table
            cursor.execute("""
                SELECT * FROM issues
                WHERE severity IN ('High', 'Medium', 'Low', 'Information')
            """)

            for row in cursor.fetchall():
                # Parse row data based on Burp project schema
                vulnerability = self._parse_burp_issue_row(row)
                if vulnerability:
                    vulnerabilities.append(vulnerability)

            conn.close()

        except Exception as e:
            logger.error(f"Failed to parse Burp project: {str(e)}")

        return vulnerabilities

    def _parse_burp_issue_row(self, row: tuple) -> Optional[BurpVulnerability]:
        """Parse individual issue row from Burp project database"""
        try:
            # This would need to be adjusted based on actual Burp project schema
            return BurpVulnerability(
                issue_id=str(row[0]),
                name=row[1] or '',
                host=row[2] or '',
                path=row[3] or '',
                location=row[4] or '',
                severity=row[5] or '',
                confidence=row[6] or '',
                issue_background=row[7] or '',
                remediation_background=row[8] or '',
                issue_detail=row[9] or '',
                remediation_detail=row[10] or '',
                vulnerability_classifications=[],
                request=row[11] or '',
                response=row[12] or ''
            )

        except Exception as e:
            logger.error(f"Failed to parse issue row: {str(e)}")
            return None

    async def _scan_via_extension(self, target_urls: List[str], scan_config: Dict = None) -> str:
        """Initiate scan via Burp extension"""
        scan_request = {
            "action": "start_scan",
            "targets": target_urls,
            "config": scan_config or {}
        }

        # This would communicate with the Burp extension
        # For now, return a mock task ID
        task_id = f"ext_scan_{int(time.time())}"
        logger.info(f"Scan initiated via extension with task ID: {task_id}")
        return task_id

    def _convert_api_issues(self, issues_data: Dict) -> List[BurpVulnerability]:
        """Convert API response to BurpVulnerability objects"""
        vulnerabilities = []

        for issue in issues_data.get('issues', []):
            vulnerability = BurpVulnerability(
                issue_id=str(issue.get('issue_id', '')),
                name=issue.get('name', ''),
                host=issue.get('origin', ''),
                path=issue.get('path', ''),
                location=issue.get('location', ''),
                severity=issue.get('severity', ''),
                confidence=issue.get('confidence', ''),
                issue_background=issue.get('issue_background', ''),
                remediation_background=issue.get('remediation_background', ''),
                issue_detail=issue.get('issue_detail', ''),
                remediation_detail=issue.get('remediation_detail', ''),
                vulnerability_classifications=issue.get('vulnerability_classifications', []),
                request=issue.get('evidence', {}).get('request_response', {}).get('request', ''),
                response=issue.get('evidence', {}).get('request_response', {}).get('response', '')
            )
            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _handle_new_vulnerability(self, vulnerability: BurpVulnerability):
        """Handle newly discovered vulnerability"""
        logger.info(f"New vulnerability: {vulnerability.name} - {vulnerability.severity}")

        # Here you would:
        # - Save to database
        # - Trigger alerts
        # - Update dashboard
        # - Generate notifications

    async def _analyze_request(self, request: BurpRequest):
        """Analyze HTTP request for patterns"""
        # Extract parameters, detect sensitive data, identify endpoints, etc.
        parsed_url = urlparse(request.url)
        query_params = parse_qs(parsed_url.query)

        # Log interesting findings
        if 'password' in request.body.lower() or 'token' in request.body.lower():
            logger.info(f"Sensitive data detected in request to {request.url}")

    def _convert_to_har(self, traffic_data: Dict) -> Dict:
        """Convert traffic data to HAR format"""
        # Implementation for HAR conversion
        har_template = {
            "log": {
                "version": "1.2",
                "creator": {"name": "SOC-Platform", "version": "1.0"},
                "entries": []
            }
        }

        # Convert each request to HAR entry format
        # This is a simplified example
        return har_template

logger.info("Burp Suite Integration module loaded")