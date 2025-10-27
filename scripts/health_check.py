#!/usr/bin/env python3
"""
SOC Platform monitoring and health check script
"""

import asyncio
import aiohttp
import time
import json
import argparse
from datetime import datetime
from pathlib import Path


class HealthChecker:
    def __init__(self, config_file="monitoring.json"):
        self.config = self.load_config(config_file)
        self.results = []

    def load_config(self, config_file):
        """Load monitoring configuration"""
        default_config = {
            "services": [
                {
                    "name": "Frontend",
                    "url": "http://localhost:3000",
                    "expected_status": 200,
                    "timeout": 10
                },
                {
                    "name": "Backend API",
                    "url": "http://localhost:8000/health",
                    "expected_status": 200,
                    "timeout": 10
                },
                {
                    "name": "Backend Docs",
                    "url": "http://localhost:8000/docs",
                    "expected_status": 200,
                    "timeout": 10
                },
                {
                    "name": "MongoDB",
                    "url": "http://localhost:8000/health/db",
                    "expected_status": 200,
                    "timeout": 5
                },
                {
                    "name": "Redis",
                    "url": "http://localhost:8000/health/cache",
                    "expected_status": 200,
                    "timeout": 5
                }
            ],
            "notification": {
                "webhook_url": "",
                "email": "",
                "slack_webhook": ""
            }
        }

        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Create default config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

    async def check_service(self, session, service):
        """Check individual service health"""
        start_time = time.time()

        try:
            async with session.get(
                service["url"],
                timeout=aiohttp.ClientTimeout(total=service["timeout"])
            ) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms

                result = {
                    "service": service["name"],
                    "url": service["url"],
                    "status_code": response.status,
                    "response_time_ms": round(response_time, 2),
                    "timestamp": datetime.now().isoformat(),
                    "healthy": response.status == service["expected_status"]
                }

                if not result["healthy"]:
                    result["error"] = f"Expected status {service['expected_status']}, got {response.status}"

                return result

        except asyncio.TimeoutError:
            return {
                "service": service["name"],
                "url": service["url"],
                "status_code": None,
                "response_time_ms": service["timeout"] * 1000,
                "timestamp": datetime.now().isoformat(),
                "healthy": False,
                "error": "Request timeout"
            }

        except Exception as e:
            return {
                "service": service["name"],
                "url": service["url"],
                "status_code": None,
                "response_time_ms": (time.time() - start_time) * 1000,
                "timestamp": datetime.now().isoformat(),
                "healthy": False,
                "error": str(e)
            }

    async def check_all_services(self):
        """Check all configured services"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.check_service(session, service)
                for service in self.config["services"]
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and add to results
            for result in results:
                if not isinstance(result, Exception):
                    self.results.append(result)

    def print_results(self, verbose=False):
        """Print health check results"""
        print(f"\n{'='*60}")
        print(f"SOC Platform Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        healthy_count = 0
        total_count = len(self.results)

        for result in self.results:
            status = "✅ HEALTHY" if result["healthy"] else "❌ UNHEALTHY"
            print(f"\n{result['service']}: {status}")

            if verbose or not result["healthy"]:
                print(f"  URL: {result['url']}")
                print(f"  Status Code: {result.get('status_code', 'N/A')}")
                print(f"  Response Time: {result['response_time_ms']}ms")

                if "error" in result:
                    print(f"  Error: {result['error']}")

            if result["healthy"]:
                healthy_count += 1

        print(f"\n{'='*60}")
        print(f"Overall Status: {healthy_count}/{total_count} services healthy")

        if healthy_count == total_count:
            print("🎉 All services are healthy!")
        else:
            print(f"⚠️  {total_count - healthy_count} service(s) need attention")

        return healthy_count == total_count

    def save_results(self, output_file="health_check_results.json"):
        """Save results to file"""
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(self.results),
            "healthy_services": sum(1 for r in self.results if r["healthy"]),
            "results": self.results
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"Results saved to {output_file}")

    async def send_notification(self, all_healthy):
        """Send notification if configured"""
        notification_config = self.config.get("notification", {})

        if not any(notification_config.values()):
            return

        message = self.format_notification_message(all_healthy)

        # Send webhook notification
        if notification_config.get("webhook_url"):
            await self.send_webhook(notification_config["webhook_url"], message)

        # Send Slack notification
        if notification_config.get("slack_webhook"):
            await self.send_slack(notification_config["slack_webhook"], message)

    def format_notification_message(self, all_healthy):
        """Format notification message"""
        healthy_count = sum(1 for r in self.results if r["healthy"])
        total_count = len(self.results)

        status_emoji = "✅" if all_healthy else "❌"

        message = {
            "status": "healthy" if all_healthy else "unhealthy",
            "summary": f"{status_emoji} SOC Platform Health Check",
            "details": f"{healthy_count}/{total_count} services healthy",
            "timestamp": datetime.now().isoformat(),
            "services": [
                {
                    "name": r["service"],
                    "status": "healthy" if r["healthy"] else "unhealthy",
                    "response_time": f"{r['response_time_ms']}ms",
                    "error": r.get("error")
                }
                for r in self.results
            ]
        }

        return message

    async def send_webhook(self, webhook_url, message):
        """Send webhook notification"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status == 200:
                        print("Webhook notification sent successfully")
                    else:
                        print(f"Failed to send webhook notification: {response.status}")
        except Exception as e:
            print(f"Error sending webhook: {e}")

    async def send_slack(self, slack_webhook, message):
        """Send Slack notification"""
        try:
            slack_message = {
                "text": message["summary"],
                "attachments": [
                    {
                        "color": "good" if message["status"] == "healthy" else "danger",
                        "fields": [
                            {
                                "title": "Status",
                                "value": message["details"],
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": message["timestamp"],
                                "short": True
                            }
                        ]
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(slack_webhook, json=slack_message) as response:
                    if response.status == 200:
                        print("Slack notification sent successfully")
                    else:
                        print(f"Failed to send Slack notification: {response.status}")
        except Exception as e:
            print(f"Error sending Slack notification: {e}")


async def main():
    parser = argparse.ArgumentParser(description="SOC Platform Health Checker")
    parser.add_argument(
        "--config", "-c",
        default="monitoring.json",
        help="Configuration file path"
    )
    parser.add_argument(
        "--output", "-o",
        default="health_check_results.json",
        help="Output file for results"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--continuous",
        type=int,
        help="Run continuously with specified interval (seconds)"
    )
    parser.add_argument(
        "--notify", "-n",
        action="store_true",
        help="Send notifications"
    )

    args = parser.parse_args()

    checker = HealthChecker(args.config)

    if args.continuous:
        print(f"Running health checks every {args.continuous} seconds...")
        while True:
            await checker.check_all_services()
            all_healthy = checker.print_results(args.verbose)
            checker.save_results(args.output)

            if args.notify:
                await checker.send_notification(all_healthy)

            checker.results.clear()  # Clear results for next iteration
            await asyncio.sleep(args.continuous)
    else:
        await checker.check_all_services()
        all_healthy = checker.print_results(args.verbose)
        checker.save_results(args.output)

        if args.notify:
            await checker.send_notification(all_healthy)

        # Exit with error code if not all healthy
        exit(0 if all_healthy else 1)


if __name__ == "__main__":
    asyncio.run(main())