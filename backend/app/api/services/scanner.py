import asyncio
import subprocess
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile
import os

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NmapScanner:
    """Nmap scanner integration"""

    def __init__(self):
        self.nmap_path = settings.NMAP_PATH

    async def port_scan(
        self,
        targets: List[str],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute port scan against targets"""

        results = []

        for target in targets:
            try:
                logger.info(f"Starting port scan for target: {target}")

                # Build nmap command
                cmd = self._build_nmap_command(target, config)

                # Execute nmap scan
                result = await self._execute_nmap(cmd, config.get("timeout", 300))

                if result["success"]:
                    scan_result = self._parse_nmap_output(result["output"], target)
                    results.append(scan_result)
                else:
                    logger.error(f"Nmap failed for {target}: {result['error']}")
                    results.append({
                        "target": target,
                        "status": "failed",
                        "error": result["error"]
                    })

            except Exception as e:
                logger.error(f"Error scanning {target}: {str(e)}")
                results.append({
                    "target": target,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def _build_nmap_command(self, target: str, config: Dict[str, Any]) -> List[str]:
        """Build nmap command based on configuration"""

        cmd = [self.nmap_path]

        # Scan type
        scan_type = config.get("scan_type", "syn")
        if scan_type == "syn":
            cmd.append("-sS")
        elif scan_type == "tcp":
            cmd.append("-sT")
        elif scan_type == "udp":
            cmd.append("-sU")
        elif scan_type == "comprehensive":
            cmd.extend(["-sS", "-sU"])

        # Timing template
        timing = config.get("timing", "normal")
        timing_map = {
            "paranoid": "-T0",
            "sneaky": "-T1",
            "polite": "-T2",
            "normal": "-T3",
            "aggressive": "-T4",
            "insane": "-T5"
        }
        cmd.append(timing_map.get(timing, "-T3"))

        # Port specification
        ports = config.get("ports")
        if ports:
            if ports == "top100":
                cmd.append("--top-ports=100")
            elif ports == "top1000":
                cmd.append("--top-ports=1000")
            elif ports == "all":
                cmd.extend(["-p", "1-65535"])
            else:
                cmd.extend(["-p", ports])
        else:
            cmd.append("-F")  # Fast scan (top 100 ports)

        # Additional options
        if config.get("version_detection", False):
            cmd.append("-sV")

        if config.get("os_detection", False):
            cmd.append("-O")

        if config.get("script_scan", False):
            cmd.append("-sC")

        if config.get("aggressive", False):
            cmd.append("-A")

        # Output format
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as f:
            output_file = f.name

        cmd.extend(["-oX", output_file])

        # Disable DNS resolution for faster scanning
        if config.get("no_dns", True):
            cmd.append("-n")

        # Host discovery
        if config.get("skip_discovery", False):
            cmd.append("-Pn")

        # Add target
        cmd.append(target)

        # Store output file for cleanup
        config["_output_file"] = output_file

        return cmd

    async def _execute_nmap(self, cmd: List[str], timeout: int) -> Dict[str, Any]:
        """Execute nmap command asynchronously"""

        try:
            logger.debug(f"Executing nmap command: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                return {
                    "success": process.returncode == 0,
                    "output": stdout.decode(),
                    "error": stderr.decode(),
                    "return_code": process.returncode
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Scan timeout after {timeout} seconds",
                    "return_code": -1
                }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1
            }

    def _parse_nmap_output(self, output: str, target: str) -> Dict[str, Any]:
        """Parse nmap XML output"""

        result = {
            "target": target,
            "status": "success",
            "scan_time": datetime.utcnow().isoformat(),
            "open_ports": [],
            "closed_ports": [],
            "filtered_ports": [],
            "host_info": {
                "state": "unknown",
                "os_info": None,
                "mac_address": None
            },
            "services": []
        }

        try:
            # Try to find and read the XML output file
            output_file = None
            if hasattr(self, "_current_config") and "_output_file" in self._current_config:
                output_file = self._current_config["_output_file"]

            if output_file and os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    xml_content = f.read()

                # Clean up the temporary file
                os.unlink(output_file)

                # Parse XML
                root = ET.fromstring(xml_content)
                result = self._parse_xml_output(root, target)

            else:
                # Fallback to parsing text output
                result = self._parse_text_output(output, target)

        except Exception as e:
            logger.error(f"Failed to parse nmap output: {str(e)}")
            result["status"] = "parse_error"
            result["error"] = str(e)

        return result

    def _parse_xml_output(self, root: ET.Element, target: str) -> Dict[str, Any]:
        """Parse nmap XML output"""

        result = {
            "target": target,
            "status": "success",
            "scan_time": datetime.utcnow().isoformat(),
            "open_ports": [],
            "closed_ports": [],
            "filtered_ports": [],
            "host_info": {
                "state": "unknown",
                "os_info": None,
                "mac_address": None
            },
            "services": []
        }

        # Find host element
        host = root.find(".//host")
        if host is None:
            result["status"] = "no_host_found"
            return result

        # Get host status
        status_elem = host.find("status")
        if status_elem is not None:
            result["host_info"]["state"] = status_elem.get("state", "unknown")

        # Get addresses
        addresses = host.findall("address")
        for addr in addresses:
            addr_type = addr.get("addrtype")
            if addr_type == "ipv4":
                result["host_info"]["ip_address"] = addr.get("addr")
            elif addr_type == "mac":
                result["host_info"]["mac_address"] = addr.get("addr")
                result["host_info"]["vendor"] = addr.get("vendor")

        # Get hostnames
        hostnames = host.findall(".//hostname")
        if hostnames:
            result["host_info"]["hostnames"] = [
                {"name": h.get("name"), "type": h.get("type")}
                for h in hostnames
            ]

        # Get ports
        ports = host.findall(".//port")
        for port in ports:
            port_id = int(port.get("portid"))
            protocol = port.get("protocol")

            state_elem = port.find("state")
            state = state_elem.get("state") if state_elem is not None else "unknown"

            service_elem = port.find("service")
            service_info = {}
            if service_elem is not None:
                service_info = {
                    "name": service_elem.get("name", ""),
                    "product": service_elem.get("product", ""),
                    "version": service_elem.get("version", ""),
                    "extrainfo": service_elem.get("extrainfo", ""),
                    "tunnel": service_elem.get("tunnel", ""),
                    "method": service_elem.get("method", "")
                }

            port_info = {
                "port": port_id,
                "protocol": protocol,
                "state": state,
                "service": service_info
            }

            if state == "open":
                result["open_ports"].append(port_info)
                if service_info.get("name"):
                    result["services"].append({
                        "port": port_id,
                        "protocol": protocol,
                        "service": service_info["name"],
                        "version": service_info.get("version", ""),
                        "product": service_info.get("product", "")
                    })
            elif state == "closed":
                result["closed_ports"].append(port_info)
            elif state == "filtered":
                result["filtered_ports"].append(port_info)

        # Get OS information
        os_elem = host.find(".//os")
        if os_elem is not None:
            osmatch = os_elem.find("osmatch")
            if osmatch is not None:
                result["host_info"]["os_info"] = {
                    "name": osmatch.get("name"),
                    "accuracy": osmatch.get("accuracy"),
                    "line": osmatch.get("line")
                }

        return result

    def _parse_text_output(self, output: str, target: str) -> Dict[str, Any]:
        """Parse nmap text output (fallback method)"""

        result = {
            "target": target,
            "status": "success",
            "scan_time": datetime.utcnow().isoformat(),
            "open_ports": [],
            "services": [],
            "host_info": {"state": "up"}
        }

        lines = output.split('\n')
        for line in lines:
            line = line.strip()

            # Parse open ports
            if '/tcp' in line and 'open' in line:
                parts = line.split()
                if len(parts) >= 3:
                    port_proto = parts[0]
                    port = int(port_proto.split('/')[0])
                    protocol = port_proto.split('/')[1]
                    service = parts[2] if len(parts) > 2 else "unknown"

                    port_info = {
                        "port": port,
                        "protocol": protocol,
                        "state": "open",
                        "service": {"name": service}
                    }

                    result["open_ports"].append(port_info)
                    result["services"].append({
                        "port": port,
                        "protocol": protocol,
                        "service": service
                    })

            # Parse OS info
            elif line.startswith("Running:"):
                result["host_info"]["os_info"] = {
                    "name": line.replace("Running:", "").strip()
                }

        return result

    async def service_scan(
        self,
        targets: List[str],
        ports: List[int],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform service version detection scan"""

        results = []

        for target in targets:
            try:
                logger.info(f"Starting service scan for target: {target}")

                # Build command for service detection
                port_list = ",".join(str(p) for p in ports)
                cmd = [
                    self.nmap_path,
                    "-sV",  # Version detection
                    "-p", port_list,
                    "-T4",  # Aggressive timing
                    target
                ]

                if config.get("script_scan", False):
                    cmd.append("-sC")

                # Execute scan
                result = await self._execute_nmap(cmd, config.get("timeout", 300))

                if result["success"]:
                    scan_result = self._parse_nmap_output(result["output"], target)
                    results.append(scan_result)
                else:
                    results.append({
                        "target": target,
                        "status": "failed",
                        "error": result["error"]
                    })

            except Exception as e:
                logger.error(f"Error in service scan for {target}: {str(e)}")
                results.append({
                    "target": target,
                    "status": "error",
                    "error": str(e)
                })

        return results