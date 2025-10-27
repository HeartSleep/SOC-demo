#!/usr/bin/env python3
"""
SOC Platform performance monitoring script
"""

import asyncio
import aiohttp
import psutil
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path


class PerformanceMonitor:
    def __init__(self):
        self.metrics = []

    async def collect_system_metrics(self):
        """Collect system performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.used / disk.total * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
        }

    async def collect_docker_metrics(self):
        """Collect Docker container metrics"""
        try:
            import docker
            client = docker.from_env()

            containers = []
            for container in client.containers.list():
                if 'soc-platform' in container.name or any(
                    service in container.name
                    for service in ['mongodb', 'redis', 'backend', 'frontend', 'worker']
                ):
                    stats = container.stats(stream=False)
                    containers.append({
                        "name": container.name,
                        "status": container.status,
                        "cpu_usage": self.calculate_cpu_percent(stats),
                        "memory_usage": stats['memory_stats'].get('usage', 0),
                        "memory_limit": stats['memory_stats'].get('limit', 0),
                        "network_rx": stats['networks']['eth0']['rx_bytes'] if 'networks' in stats else 0,
                        "network_tx": stats['networks']['eth0']['tx_bytes'] if 'networks' in stats else 0
                    })

            return {"docker_containers": containers}

        except ImportError:
            return {"docker_containers": [], "error": "Docker Python library not installed"}
        except Exception as e:
            return {"docker_containers": [], "error": str(e)}

    def calculate_cpu_percent(self, stats):
        """Calculate CPU percentage from Docker stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_cpu_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
            number_cpus = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])

            if system_cpu_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_cpu_delta) * number_cpus * 100
            return 0.0
        except (KeyError, ZeroDivisionError):
            return 0.0

    async def collect_application_metrics(self):
        """Collect application-specific metrics"""
        metrics = {"application": {}}

        try:
            # Get metrics from backend API
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000/metrics") as response:
                    if response.status == 200:
                        data = await response.json()
                        metrics["application"]["backend"] = data
        except Exception as e:
            metrics["application"]["backend_error"] = str(e)

        return metrics

    async def run_load_test(self, duration=60, concurrent_requests=10):
        """Run a simple load test"""
        endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/api/assets",
            "http://localhost:8000/api/tasks",
            "http://localhost:8000/api/vulnerabilities"
        ]

        results = []
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                tasks = []
                for _ in range(concurrent_requests):
                    endpoint = endpoints[len(tasks) % len(endpoints)]
                    tasks.append(self.make_request(session, endpoint))

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for i, response in enumerate(responses):
                    if not isinstance(response, Exception):
                        results.append({
                            "endpoint": endpoints[i % len(endpoints)],
                            "status_code": response["status_code"],
                            "response_time": response["response_time"],
                            "timestamp": response["timestamp"]
                        })

                await asyncio.sleep(1)  # Wait 1 second between batches

        # Calculate statistics
        successful_requests = [r for r in results if r["status_code"] == 200]
        failed_requests = [r for r in results if r["status_code"] != 200]

        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "load_test": {
                "duration": duration,
                "concurrent_requests": concurrent_requests,
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": len(successful_requests) / len(results) * 100 if results else 0,
                "average_response_time": avg_response_time,
                "requests_per_second": len(results) / duration
            }
        }

    async def make_request(self, session, url):
        """Make a single HTTP request and measure response time"""
        start_time = time.time()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response_time = (time.time() - start_time) * 1000
                return {
                    "status_code": response.status,
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception:
            response_time = (time.time() - start_time) * 1000
            return {
                "status_code": 0,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }

    def generate_report(self, metrics, output_file="performance_report.json"):
        """Generate performance report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "metrics": metrics,
            "summary": self.generate_summary(metrics)
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def generate_summary(self, metrics):
        """Generate performance summary"""
        summary = {}

        if "system" in metrics:
            system = metrics["system"]
            summary["system_health"] = {
                "cpu_status": "high" if system["cpu_percent"] > 80 else "normal",
                "memory_status": "high" if system["memory"]["percent"] > 80 else "normal",
                "disk_status": "high" if system["disk"]["percent"] > 80 else "normal"
            }

        if "load_test" in metrics:
            load_test = metrics["load_test"]
            summary["performance"] = {
                "success_rate": load_test["success_rate"],
                "avg_response_time": load_test["average_response_time"],
                "requests_per_second": load_test["requests_per_second"],
                "status": "good" if load_test["success_rate"] > 95 else "degraded"
            }

        return summary

    def print_report(self, report):
        """Print performance report to console"""
        print(f"\n{'='*60}")
        print(f"SOC Platform Performance Report")
        print(f"Generated: {report['generated_at']}")
        print(f"{'='*60}")

        # System metrics
        if "system" in report["metrics"]:
            system = report["metrics"]["system"]
            print(f"\n📊 System Metrics:")
            print(f"  CPU Usage: {system['cpu_percent']:.1f}%")
            print(f"  Memory Usage: {system['memory']['percent']:.1f}%")
            print(f"  Disk Usage: {system['disk']['percent']:.1f}%")

        # Docker containers
        if "docker_containers" in report["metrics"]:
            containers = report["metrics"]["docker_containers"]
            if containers:
                print(f"\n🐳 Docker Containers:")
                for container in containers:
                    print(f"  {container['name']}: {container['status']}")
                    print(f"    CPU: {container['cpu_usage']:.1f}%")
                    print(f"    Memory: {container['memory_usage'] / 1024 / 1024:.1f}MB")

        # Load test results
        if "load_test" in report["metrics"]:
            load_test = report["metrics"]["load_test"]
            print(f"\n🚀 Load Test Results:")
            print(f"  Duration: {load_test['duration']}s")
            print(f"  Total Requests: {load_test['total_requests']}")
            print(f"  Success Rate: {load_test['success_rate']:.1f}%")
            print(f"  Avg Response Time: {load_test['average_response_time']:.2f}ms")
            print(f"  Requests/Second: {load_test['requests_per_second']:.1f}")

        # Summary
        if "summary" in report:
            summary = report["summary"]
            print(f"\n📋 Summary:")

            if "system_health" in summary:
                health = summary["system_health"]
                print(f"  System Health: CPU({health['cpu_status']}) Memory({health['memory_status']}) Disk({health['disk_status']})")

            if "performance" in summary:
                perf = summary["performance"]
                print(f"  Performance: {perf['status'].upper()} - {perf['success_rate']:.1f}% success rate")


async def main():
    parser = argparse.ArgumentParser(description="SOC Platform Performance Monitor")
    parser.add_argument(
        "--output", "-o",
        default="performance_report.json",
        help="Output file for report"
    )
    parser.add_argument(
        "--load-test",
        action="store_true",
        help="Run load test"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Load test duration in seconds"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Concurrent requests for load test"
    )

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    print("Collecting performance metrics...")

    # Collect all metrics
    metrics = {}

    # System metrics
    system_metrics = await monitor.collect_system_metrics()
    metrics.update(system_metrics)

    # Docker metrics
    docker_metrics = await monitor.collect_docker_metrics()
    metrics.update(docker_metrics)

    # Application metrics
    app_metrics = await monitor.collect_application_metrics()
    metrics.update(app_metrics)

    # Load test (if requested)
    if args.load_test:
        print(f"Running load test for {args.duration} seconds...")
        load_test_metrics = await monitor.run_load_test(args.duration, args.concurrent)
        metrics.update(load_test_metrics)

    # Generate and print report
    report = monitor.generate_report(metrics, args.output)
    monitor.print_report(report)

    print(f"\nFull report saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())