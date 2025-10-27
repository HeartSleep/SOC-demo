#!/usr/bin/env python3
"""
SOC Vulnerability Scanning Platform - Main Startup Script
========================================================

Enterprise-grade vulnerability scanning platform startup script.
Initializes all scanning engines and provides command-line interface.
"""

import asyncio
import logging
import argparse
import sys
import json
from datetime import datetime
import signal
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our scanning engines
try:
    from soc_vulnerability_scanner import SOCVulnerabilityScanner, ScanTarget, ScanType
    from engines.asset_discovery import AssetDiscoveryEngine
    from engines.fofa_integration import FOFAEngine
    from engines.vulnerability_scanner import VulnerabilityScanner
    from engines.burp_integration import BurpSuiteIntegration
    from managers.vulnerability_manager import VulnerabilityManager
    from managers.operations_manager import OperationsManager
except ImportError as e:
    print(f"❌ Failed to import scanning modules: {e}")
    print("Please ensure all required dependencies are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/soc_scanner.log')
    ]
)

logger = logging.getLogger(__name__)

class SOCPlatform:
    """Main SOC Platform orchestrator"""

    def __init__(self):
        self.scanner = None
        self.running = False
        self.active_scans = {}

    async def initialize(self):
        """Initialize the SOC platform"""
        try:
            logger.info("🚀 Starting SOC Vulnerability Scanning Platform...")

            # Initialize main scanner
            self.scanner = SOCVulnerabilityScanner()

            logger.info("✅ SOC Platform initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize SOC Platform: {str(e)}")
            return False

    async def start_interactive_mode(self):
        """Start interactive command-line mode"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    SOC SECURITY PLATFORM                     ║
║              Vulnerability Scanning Engine                   ║
╚══════════════════════════════════════════════════════════════╝

🛡️  Enterprise-grade vulnerability scanning platform
🔍 Multi-engine scanning (DAST/IAST/SAST)
🌐 FOFA threat intelligence integration
🔗 Burp Suite integration
📊 Professional reporting and analytics

Available Commands:
  scan <target>     - Start comprehensive vulnerability scan
  status <scan_id>  - Check scan status
  list             - List all scans
  fofa <query>     - Search FOFA database
  assets <domain>  - Discover assets for domain
  help             - Show this help
  exit             - Exit the platform

""")

        self.running = True

        while self.running:
            try:
                command = input("SOC> ").strip()

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []

                if cmd == "scan":
                    await self._handle_scan_command(args)
                elif cmd == "status":
                    await self._handle_status_command(args)
                elif cmd == "list":
                    await self._handle_list_command()
                elif cmd == "fofa":
                    await self._handle_fofa_command(args)
                elif cmd == "assets":
                    await self._handle_assets_command(args)
                elif cmd == "help":
                    await self._handle_help_command()
                elif cmd == "exit":
                    self.running = False
                    print("👋 Goodbye!")
                else:
                    print(f"❌ Unknown command: {cmd}. Type 'help' for available commands.")

            except KeyboardInterrupt:
                self.running = False
                print("\n👋 Goodbye!")
            except Exception as e:
                logger.error(f"Command error: {str(e)}")
                print(f"❌ Error: {str(e)}")

    async def _handle_scan_command(self, args):
        """Handle scan command"""
        if not args:
            print("❌ Please provide a target. Usage: scan <domain_or_ip>")
            return

        target_input = args[0]

        try:
            print(f"🔍 Starting comprehensive scan for: {target_input}")

            # Create scan target
            target = ScanTarget(
                target_id=f"cli_scan_{target_input}",
                domain=target_input if not target_input.replace('.', '').isdigit() else None,
                ip_address=target_input if target_input.replace('.', '').isdigit() else None,
                url=f"https://{target_input}",
                scan_depth="normal",
                include_subdomains=True,
                include_fofa_search=True,
                include_dast=True,
                enable_oob=True,
                enable_waf_bypass=True
            )

            # Start scan
            scan_id = await self.scanner.start_comprehensive_scan(target)
            self.active_scans[scan_id] = {
                'target': target_input,
                'started_at': datetime.now()
            }

            print(f"✅ Scan started successfully!")
            print(f"📋 Scan ID: {scan_id}")
            print(f"🎯 Target: {target_input}")
            print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\n💡 Use 'status {scan_id}' to check progress")

        except Exception as e:
            print(f"❌ Failed to start scan: {str(e)}")

    async def _handle_status_command(self, args):
        """Handle status command"""
        if not args:
            print("❌ Please provide scan ID. Usage: status <scan_id>")
            return

        scan_id = args[0]

        try:
            status = self.scanner.get_scan_status(scan_id)

            if not status:
                print(f"❌ Scan not found: {scan_id}")
                return

            print(f"📊 Scan Status Report")
            print(f"─" * 50)
            print(f"🆔 Scan ID: {status['scan_id']}")
            print(f"🎯 Target: {status['target']}")
            print(f"📈 Status: {status['status'].upper()}")
            print(f"⏰ Started: {status['started_at']}")

            if status['completed_at']:
                print(f"✅ Completed: {status['completed_at']}")

            progress = status['progress']
            print(f"\n📋 Progress:")
            print(f"  🔍 Vulnerabilities Found: {progress['total_vulnerabilities']}")
            print(f"  🏢 Assets Discovered: {progress['discovered_assets']}")
            print(f"  🌐 Subdomains Found: {progress['subdomains_found']}")
            print(f"  🚪 Open Ports: {progress['open_ports']}")
            print(f"  📁 Paths Discovered: {progress['paths_discovered']}")

        except Exception as e:
            print(f"❌ Error getting status: {str(e)}")

    async def _handle_list_command(self):
        """Handle list command"""
        if not self.active_scans:
            print("📝 No active scans found.")
            return

        print(f"📋 Active Scans ({len(self.active_scans)} total)")
        print(f"─" * 80)
        print(f"{'Scan ID':<20} {'Target':<30} {'Started':<20}")
        print(f"─" * 80)

        for scan_id, scan_info in self.active_scans.items():
            started = scan_info['started_at'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"{scan_id:<20} {scan_info['target']:<30} {started:<20}")

    async def _handle_fofa_command(self, args):
        """Handle FOFA command"""
        if not args:
            print("❌ Please provide search query. Usage: fofa <search_term>")
            return

        query = ' '.join(args)
        print(f"🌐 Searching FOFA database for: {query}")
        print("⚠️  FOFA integration requires API credentials")

        # This would integrate with actual FOFA API
        print("📊 FOFA search completed (demo mode)")

    async def _handle_assets_command(self, args):
        """Handle assets command"""
        if not args:
            print("❌ Please provide domain. Usage: assets <domain>")
            return

        domain = args[0]

        try:
            print(f"🔍 Discovering assets for: {domain}")

            # Use asset discovery engine
            async with AssetDiscoveryEngine() as engine:
                assets = await engine.discover_assets(domain, "normal")

                if assets:
                    print(f"✅ Discovered {len(assets)} assets:")
                    for i, asset in enumerate(assets[:10], 1):  # Show first 10
                        print(f"  {i}. {asset.ip_address or asset.domain}:{asset.port or 80} ({asset.service or 'unknown'})")

                    if len(assets) > 10:
                        print(f"  ... and {len(assets) - 10} more")
                else:
                    print("📝 No assets discovered.")

        except Exception as e:
            print(f"❌ Asset discovery failed: {str(e)}")

    async def _handle_help_command(self):
        """Handle help command"""
        print("""
🔧 SOC Platform Commands:

📊 Scanning Commands:
  scan <target>     - Start comprehensive vulnerability scan
                     Example: scan example.com
                     Example: scan 192.168.1.1

📈 Monitoring Commands:
  status <scan_id>  - Check detailed scan status and progress
  list             - List all active scans with basic info

🌐 Intelligence Commands:
  fofa <query>     - Search FOFA threat intelligence database
                     Example: fofa "nginx"
                     Example: fofa "org:example"

  assets <domain>  - Discover assets and subdomains for domain
                     Example: assets example.com

🔧 System Commands:
  help             - Show this help message
  exit             - Exit the SOC platform

💡 Tips:
  - Use 'status <scan_id>' regularly to monitor scan progress
  - Comprehensive scans include DAST, IAST, asset discovery, and FOFA intelligence
  - All scan results are automatically saved and can be exported
        """)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SOC Vulnerability Scanning Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_soc.py                    # Interactive mode
  python start_soc.py --scan example.com # Direct scan
  python start_soc.py --help            # Show help
        """
    )

    parser.add_argument('--scan', metavar='TARGET',
                       help='Start scan for target (domain or IP)')
    parser.add_argument('--interactive', action='store_true', default=True,
                       help='Start interactive mode (default)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Initialize platform
    platform = SOCPlatform()

    if not await platform.initialize():
        print("❌ Failed to initialize SOC platform")
        sys.exit(1)

    # Handle direct scan
    if args.scan:
        target = ScanTarget(
            target_id=f"direct_scan_{args.scan}",
            domain=args.scan if not args.scan.replace('.', '').isdigit() else None,
            ip_address=args.scan if args.scan.replace('.', '').isdigit() else None,
            url=f"https://{args.scan}",
            scan_depth="normal"
        )

        print(f"🚀 Starting scan for: {args.scan}")
        scan_id = await platform.scanner.start_comprehensive_scan(target)
        print(f"📋 Scan ID: {scan_id}")

        # Monitor scan progress
        while True:
            await asyncio.sleep(5)
            status = platform.scanner.get_scan_status(scan_id)
            if status and status['status'] in ['completed', 'failed']:
                print(f"✅ Scan {status['status']}: {scan_id}")
                break

        return

    # Start interactive mode
    await platform.start_interactive_mode()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 SOC Platform shutdown complete")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)