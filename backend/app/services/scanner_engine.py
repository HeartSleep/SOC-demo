"""
Real Scanner Engine with Tool Integration
This module provides actual scanning capabilities using real security tools
"""

import os
import subprocess
import json
import asyncio
import tempfile
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
import re
import aiohttp
from app.services.vulnerability_rules import VulnerabilityDetector, Severity
from app.services.vulnerability_merger import VulnerabilityMerger

logger = logging.getLogger(__name__)

class ScannerEngine:
    """
    Main scanner engine that orchestrates various security tools
    """

    def __init__(self):
        # Get tools directory from environment or use default
        self.base_dir = Path(__file__).parent.parent.parent.parent.parent
        self.tools_dir = self.base_dir / "tools"

        # Tool binaries
        self.tools = {
            "nuclei": self.tools_dir / "nuclei" / "nuclei",
            "subfinder": self.tools_dir / "subfinder" / "subfinder",
            "httpx": self.tools_dir / "httpx" / "httpx",
            "naabu": self.tools_dir / "naabu" / "naabu",
            "katana": self.tools_dir / "katana" / "katana",
        }

        # Custom scripts
        self.scripts = {
            "subdomain_enum": self.tools_dir / "custom-scripts" / "subdomain_enum.sh",
            "port_scan": self.tools_dir / "custom-scripts" / "port_scan.sh",
            "vuln_scan": self.tools_dir / "custom-scripts" / "vuln_scan.sh",
        }

        # Wordlists
        self.wordlists = {
            "common": self.tools_dir / "wordlists" / "common.txt",
            "directories": self.tools_dir / "wordlists" / "directory-list-2.3-medium.txt",
            "subdomains": self.tools_dir / "wordlists" / "subdomains-top1million-5000.txt",
        }

        # Results directory
        self.results_dir = self.base_dir / "backend" / "scan_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Initialize vulnerability detector for advanced pattern-based detection
        self.vuln_detector = VulnerabilityDetector()

        # Verify tools are installed
        self._verify_tools()

    def _verify_tools(self):
        """Verify that required tools are installed"""
        self.available_tools = {}
        self.missing_tools = []

        for tool_name, tool_path in self.tools.items():
            if tool_path.exists():
                self.available_tools[tool_name] = tool_path
                logger.info(f"Tool {tool_name} available at {tool_path}")
            else:
                self.missing_tools.append(tool_name)
                logger.warning(f"Tool {tool_name} not found at {tool_path}")

        if self.missing_tools:
            logger.warning(f"Missing tools: {', '.join(self.missing_tools)}")

        # Store tool availability status
        self.tool_status = {
            tool: tool not in self.missing_tools
            for tool in self.tools.keys()
        }

    async def run_command(self, cmd: List[str], timeout: int = 300) -> Dict[str, Any]:
        """
        Execute a command and capture output
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "returncode": process.returncode
            }
        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()  # Wait for process to actually terminate
            except:
                pass  # Process might have already terminated
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    async def scan_subdomains(self, domain: str) -> Dict[str, Any]:
        """
        Perform subdomain enumeration using multiple tools
        """
        results = {
            "domain": domain,
            "subdomains": [],
            "live_subdomains": [],
            "timestamp": datetime.now().isoformat()
        }

        scan_id = str(uuid.uuid4())
        output_dir = self.results_dir / scan_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run subfinder if available
        if self.tool_status.get("subfinder", False):
            logger.info(f"Running subfinder for {domain}")
            subfinder_out = output_dir / "subfinder.txt"
            cmd = [
                str(self.tools["subfinder"]),
                "-d", domain,
                "-o", str(subfinder_out),
                "-silent"
            ]
            result = await self.run_command(cmd)

            if result["success"] and subfinder_out.exists():
                with open(subfinder_out) as f:
                    subdomains = f.read().strip().split('\n')
                    results["subdomains"].extend(subdomains)

        # Remove duplicates
        results["subdomains"] = list(set(results["subdomains"]))

        # Check live hosts with httpx if available
        if self.tool_status.get("httpx", False) and results["subdomains"]:
            logger.info(f"Checking live hosts with httpx")
            httpx_input = output_dir / "all_subdomains.txt"
            httpx_output = output_dir / "live_subdomains.txt"

            with open(httpx_input, 'w') as f:
                f.write('\n'.join(results["subdomains"]))

            cmd = [
                str(self.tools["httpx"]),
                "-l", str(httpx_input),
                "-o", str(httpx_output),
                "-silent"
            ]
            result = await self.run_command(cmd)

            if result["success"] and httpx_output.exists():
                with open(httpx_output) as f:
                    results["live_subdomains"] = f.read().strip().split('\n')

        results["scan_id"] = scan_id
        results["total_found"] = len(results["subdomains"])
        results["total_live"] = len(results["live_subdomains"])

        return results

    async def scan_ports(self, target: str, port_range: str = "1-65535") -> Dict[str, Any]:
        """
        Perform port scanning using naabu
        """
        results = {
            "target": target,
            "open_ports": [],
            "services": {},
            "timestamp": datetime.now().isoformat()
        }

        scan_id = str(uuid.uuid4())
        output_dir = self.results_dir / scan_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run naabu for port scanning if available
        if self.tool_status.get("naabu", False):
            logger.info(f"Running naabu port scan for {target}")
            naabu_out = output_dir / "open_ports.txt"

            cmd = [
                str(self.tools["naabu"]),
                "-host", target,
                "-p", port_range,
                "-o", str(naabu_out),
                "-silent"
            ]

            result = await self.run_command(cmd, timeout=600)

            if result["success"] and naabu_out.exists():
                with open(naabu_out) as f:
                    for line in f:
                        if ':' in line:
                            host, port = line.strip().split(':')
                            results["open_ports"].append(int(port))

        results["scan_id"] = scan_id
        results["total_ports"] = len(results["open_ports"])

        return results

    async def scan_vulnerabilities(self, target: str, scan_type: str = "all") -> Dict[str, Any]:
        """
        Perform vulnerability scanning using Nuclei
        """
        results = {
            "target": target,
            "vulnerabilities": [],
            "scan_type": scan_type,
            "timestamp": datetime.now().isoformat()
        }

        scan_id = str(uuid.uuid4())
        output_dir = self.results_dir / scan_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run Nuclei if available
        if self.tool_status.get("nuclei", False):
            logger.info(f"Running nuclei vulnerability scan for {target}")
            nuclei_out = output_dir / "nuclei_results.json"

            cmd = [
                str(self.tools["nuclei"]),
                "-u", target,
                "-json-export", str(nuclei_out),
                "-silent"
            ]

            # Add specific scan options based on type
            if scan_type == "critical":
                cmd.extend(["-severity", "critical,high"])
            elif scan_type == "cve":
                cmd.extend(["-tags", "cve"])
            elif scan_type == "exposure":
                cmd.extend(["-tags", "exposure,disclosure"])

            result = await self.run_command(cmd, timeout=900)

            if nuclei_out.exists():
                with open(nuclei_out) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            vuln = json.loads(line)
                            # Safely extract nested fields with defaults
                            info = vuln.get("info", {})
                            vulnerability_data = {
                                "template": vuln.get("template-id", "unknown"),
                                "name": info.get("name", vuln.get("template-id", "Unknown Vulnerability")),
                                "severity": info.get("severity", "unknown"),
                                "type": vuln.get("type", "unknown"),
                                "host": vuln.get("host", target),
                                "path": vuln.get("path", ""),
                                "matched": vuln.get("matched-at", ""),
                                "description": info.get("description", ""),
                                "reference": info.get("reference", []) if isinstance(info.get("reference"), list) else [info.get("reference")] if info.get("reference") else [],
                                "tags": info.get("tags", []) if isinstance(info.get("tags"), list) else []
                            }
                            results["vulnerabilities"].append(vulnerability_data)
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Failed to parse Nuclei output line: {line[:100]}... Error: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Unexpected error parsing Nuclei output: {e}")
                            continue

        results["scan_id"] = scan_id
        results["total_vulnerabilities"] = len(results["vulnerabilities"])

        # Group vulnerabilities by severity
        severity_count = {}
        for vuln in results["vulnerabilities"]:
            severity = vuln.get("severity", "unknown")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        results["severity_breakdown"] = severity_count

        return results

    async def scan_with_detection_rules(self, target: str, fetch_content: bool = True) -> Dict[str, Any]:
        """
        Perform advanced vulnerability scanning using detection rules
        This complements Nuclei scanning with pattern-based detection
        """
        results = {
            "target": target,
            "vulnerabilities": [],
            "scan_type": "pattern_detection",
            "timestamp": datetime.now().isoformat()
        }

        content_to_scan = ""

        # Fetch web content if target is a URL
        if fetch_content and (target.startswith("http://") or target.startswith("https://")):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(target, timeout=30, ssl=False) as response:
                        content_to_scan = await response.text()

                        # Also scan response headers
                        headers_str = "\n".join([f"{k}: {v}" for k, v in response.headers.items()])
                        header_vulns = self.vuln_detector.scan_content(headers_str, context="HTTP Headers")

                        for vuln in header_vulns:
                            vuln["location"] = "HTTP Headers"
                            results["vulnerabilities"].append(vuln)

            except Exception as e:
                logger.warning(f"Failed to fetch content from {target}: {e}")

        # Scan the fetched content with our detection rules
        if content_to_scan:
            content_vulns = self.vuln_detector.scan_content(content_to_scan, context=target)

            # Convert to scanner engine format
            for vuln in content_vulns:
                vulnerability_data = {
                    "template": vuln["rule_id"],
                    "name": vuln["name"],
                    "severity": vuln["severity"].lower(),
                    "type": vuln["category"],
                    "host": target,
                    "matched": vuln.get("matched_content", ""),
                    "description": vuln["description"],
                    "reference": [f"CWE-{vuln['cwe_id']}", f"OWASP: {vuln['owasp_category']}"],
                    "tags": [vuln["category"], "pattern-detection"],
                    "remediation": vuln.get("remediation", ""),
                    "confidence": vuln.get("confidence", "high")
                }
                results["vulnerabilities"].append(vulnerability_data)

        # Also scan local files if target is a file path
        if not fetch_content or not target.startswith("http"):
            file_path = Path(target)
            if file_path.exists() and file_path.is_file():
                file_vulns = self.vuln_detector.scan_file(str(file_path))
                for vuln in file_vulns:
                    vulnerability_data = {
                        "template": vuln["rule_id"],
                        "name": vuln["name"],
                        "severity": vuln["severity"].lower(),
                        "type": vuln["category"],
                        "host": str(file_path),
                        "matched": vuln.get("matched_content", ""),
                        "description": vuln["description"],
                        "reference": [f"CWE-{vuln['cwe_id']}", f"OWASP: {vuln['owasp_category']}"],
                        "tags": [vuln["category"], "pattern-detection", "file-scan"],
                        "remediation": vuln.get("remediation", ""),
                        "line_number": vuln.get("line_number", 0)
                    }
                    results["vulnerabilities"].append(vulnerability_data)

        results["total_vulnerabilities"] = len(results["vulnerabilities"])

        # Group by severity
        severity_count = {}
        for vuln in results["vulnerabilities"]:
            severity = vuln.get("severity", "unknown")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        results["severity_breakdown"] = severity_count

        return results

    async def scan_comprehensive(self, target: str) -> Dict[str, Any]:
        """
        Perform comprehensive scanning combining multiple techniques:
        - Nuclei template scanning
        - Pattern-based detection rules
        - Web technology identification
        """
        results = {
            "target": target,
            "scan_results": {},
            "total_vulnerabilities": 0,
            "timestamp": datetime.now().isoformat()
        }

        # Run Nuclei scanning
        nuclei_results = await self.scan_vulnerabilities(target)
        results["scan_results"]["nuclei"] = nuclei_results

        # Run pattern-based detection
        pattern_results = await self.scan_with_detection_rules(target)
        results["scan_results"]["pattern_detection"] = pattern_results

        # Run web technology scan if URL
        if target.startswith("http"):
            tech_results = await self.scan_web_technologies(target)
            results["scan_results"]["technologies"] = tech_results

        # Combine and intelligently deduplicate vulnerabilities using merger
        vulnerability_merger = VulnerabilityMerger()

        for scan_name, scan_data in results["scan_results"].items():
            vulnerabilities = scan_data.get("vulnerabilities", []) if isinstance(scan_data, dict) else []
            if not vulnerabilities:
                continue

            timestamp = scan_data.get("timestamp") if isinstance(scan_data, dict) else None

            for vuln in vulnerabilities:
                if not isinstance(vuln, dict):
                    continue

                vuln_with_source = vuln.copy()
                vuln_with_source.setdefault("source", scan_name)

                vulnerability_merger.add_vulnerability(
                    vuln_with_source,
                    source=scan_name,
                    timestamp=timestamp
                )

        merged_vulnerabilities = vulnerability_merger.get_merged_vulnerabilities()
        results["vulnerabilities"] = merged_vulnerabilities
        results["total_vulnerabilities"] = len(merged_vulnerabilities)

        # Calculate combined severity breakdown
        severity_count = {}
        for vuln in merged_vulnerabilities:
            severity = vuln.get("severity", "unknown")
            severity_key = severity.lower() if isinstance(severity, str) else str(severity)
            severity_count[severity_key] = severity_count.get(severity_key, 0) + 1
        results["severity_breakdown"] = severity_count

        # Provide merger statistics for analytics/insights
        results["merger_statistics"] = vulnerability_merger.get_statistics()

        return results

    async def scan_web_technologies(self, url: str) -> Dict[str, Any]:
        """
        Identify web technologies using httpx
        """
        results = {
            "url": url,
            "technologies": [],
            "headers": {},
            "status_code": None,
            "timestamp": datetime.now().isoformat()
        }

        if self.tool_status.get("httpx", False):
            logger.info(f"Scanning web technologies for {url}")

            # Get detailed information with httpx
            cmd = [
                str(self.tools["httpx"]),
                "-u", url,
                "-tech-detect",
                "-status-code",
                "-title",
                "-web-server",
                "-json",
                "-silent"
            ]

            result = await self.run_command(cmd)

            if result["success"] and result["stdout"]:
                try:
                    data = json.loads(result["stdout"].strip())
                    results["status_code"] = data.get("status-code")
                    results["title"] = data.get("title")
                    results["web_server"] = data.get("webserver")
                    results["technologies"] = data.get("tech", [])
                except json.JSONDecodeError:
                    pass

        return results

    async def crawl_website(self, url: str, depth: int = 2) -> Dict[str, Any]:
        """
        Crawl website using katana
        """
        results = {
            "url": url,
            "endpoints": [],
            "forms": [],
            "parameters": [],
            "timestamp": datetime.now().isoformat()
        }

        scan_id = str(uuid.uuid4())
        output_dir = self.results_dir / scan_id
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.tool_status.get("katana", False):
            logger.info(f"Crawling website {url}")
            katana_out = output_dir / "crawl_results.txt"

            cmd = [
                str(self.tools["katana"]),
                "-u", url,
                "-d", str(depth),
                "-o", str(katana_out),
                "-silent"
            ]

            result = await self.run_command(cmd, timeout=600)

            if result["success"] and katana_out.exists():
                with open(katana_out) as f:
                    results["endpoints"] = f.read().strip().split('\n')

                # Extract forms and parameters
                for endpoint in results["endpoints"]:
                    if '?' in endpoint:
                        params = endpoint.split('?')[1]
                        for param in params.split('&'):
                            if '=' in param:
                                results["parameters"].append(param.split('=')[0])

                results["parameters"] = list(set(results["parameters"]))

        results["scan_id"] = scan_id
        results["total_endpoints"] = len(results["endpoints"])
        results["total_parameters"] = len(results["parameters"])

        return results

    async def comprehensive_scan(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a comprehensive scan using multiple tools
        """
        results = {
            "target": target,
            "scan_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "scans": {}
        }

        # Parse target to determine scan types
        is_domain = not target.startswith('http') and '/' not in target
        is_url = target.startswith('http')

        tasks = []

        # Subdomain enumeration for domains
        if is_domain and config.get("subdomain_scan", True):
            tasks.append(("subdomains", self.scan_subdomains(target)))

        # Port scanning
        if config.get("port_scan", True):
            port_target = target if not is_url else target.split('/')[2]
            port_range = config.get("port_range", "80,443,8080,8443")
            tasks.append(("ports", self.scan_ports(port_target, port_range)))

        # Vulnerability scanning with both Nuclei and pattern detection
        if config.get("vulnerability_scan", True):
            scan_url = f"https://{target}" if is_domain else target
            scan_type = config.get("vuln_scan_type", "all")

            # Add both Nuclei scanning and pattern-based detection
            tasks.append(("vulnerabilities", self.scan_vulnerabilities(scan_url, scan_type)))
            tasks.append(("pattern_detection", self.scan_with_detection_rules(scan_url)))

        # Web technology detection
        if is_url and config.get("tech_detection", True):
            tasks.append(("technologies", self.scan_web_technologies(target)))

        # Website crawling
        if is_url and config.get("crawl", True):
            depth = config.get("crawl_depth", 2)
            tasks.append(("crawl", self.crawl_website(target, depth)))

        # Execute all scans concurrently
        for scan_name, task in tasks:
            try:
                results["scans"][scan_name] = await task
            except Exception as e:
                logger.error(f"Error in {scan_name} scan: {str(e)}")
                results["scans"][scan_name] = {
                    "error": str(e),
                    "status": "failed"
                }

        # Calculate overall statistics
        results["statistics"] = self._calculate_statistics(results["scans"])

        return results

    def _calculate_statistics(self, scans: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall scan statistics
        """
        stats = {
            "total_scans": len(scans),
            "successful_scans": 0,
            "failed_scans": 0,
            "findings": {}
        }

        for scan_name, scan_result in scans.items():
            if isinstance(scan_result, dict) and "error" not in scan_result:
                stats["successful_scans"] += 1

                # Collect specific findings
                if scan_name == "subdomains" and "total_found" in scan_result:
                    stats["findings"]["subdomains"] = scan_result["total_found"]
                    stats["findings"]["live_subdomains"] = scan_result["total_live"]

                if scan_name == "ports" and "total_ports" in scan_result:
                    stats["findings"]["open_ports"] = scan_result["total_ports"]

                if scan_name == "vulnerabilities" and "total_vulnerabilities" in scan_result:
                    stats["findings"]["vulnerabilities"] = scan_result["total_vulnerabilities"]
                    stats["findings"]["severity_breakdown"] = scan_result.get("severity_breakdown", {})

                if scan_name == "pattern_detection" and "total_vulnerabilities" in scan_result:
                    # Combine pattern detection results with existing vulnerabilities
                    if "vulnerabilities" in stats["findings"]:
                        stats["findings"]["vulnerabilities"] += scan_result["total_vulnerabilities"]
                    else:
                        stats["findings"]["vulnerabilities"] = scan_result["total_vulnerabilities"]

                    # Merge severity breakdown
                    if "severity_breakdown" in stats["findings"]:
                        for severity, count in scan_result.get("severity_breakdown", {}).items():
                            stats["findings"]["severity_breakdown"][severity] = \
                                stats["findings"]["severity_breakdown"].get(severity, 0) + count
                    else:
                        stats["findings"]["severity_breakdown"] = scan_result.get("severity_breakdown", {})

                if scan_name == "crawl" and "total_endpoints" in scan_result:
                    stats["findings"]["endpoints"] = scan_result["total_endpoints"]
                    stats["findings"]["parameters"] = scan_result["total_parameters"]
            else:
                stats["failed_scans"] += 1

        return stats

    async def get_scan_results(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve scan results by ID
        """
        scan_dir = self.results_dir / scan_id
        if not scan_dir.exists():
            return None

        results = {
            "scan_id": scan_id,
            "files": []
        }

        for file_path in scan_dir.iterdir():
            if file_path.is_file():
                with open(file_path) as f:
                    content = f.read()
                    results["files"].append({
                        "name": file_path.name,
                        "content": content
                    })

        return results

# Create global scanner instance
scanner_engine = ScannerEngine()