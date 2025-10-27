#!/usr/bin/env python3
"""
Performance Profiler for Frontend-Backend Integration
Identifies bottlenecks and optimization opportunities
"""

import asyncio
import time
import statistics
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import httpx
import psutil
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class PerformanceProfiler:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.token = None
        self.metrics = {
            "endpoint_timings": {},
            "database_queries": {},
            "memory_usage": [],
            "cpu_usage": [],
            "network_latency": [],
            "cache_hits": 0,
            "cache_misses": 0
        }

    async def authenticate(self):
        """Authenticate and get token"""
        response = await self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.client.headers["Authorization"] = f"Bearer {self.token}"
            return True
        return False

    async def profile_endpoint(self, method: str, path: str, data: Any = None,
                              iterations: int = 10) -> Dict[str, Any]:
        """Profile a single endpoint"""
        timings = []
        errors = 0
        status_codes = {}

        print(f"  Profiling {method} {path} ({iterations} iterations)...")

        for i in range(iterations):
            start_time = time.perf_counter()

            try:
                if method == "GET":
                    response = await self.client.get(path)
                elif method == "POST":
                    response = await self.client.post(path, json=data)
                elif method == "PUT":
                    response = await self.client.put(path, json=data)
                elif method == "DELETE":
                    response = await self.client.delete(path)
                else:
                    continue

                elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
                timings.append(elapsed)

                # Track status codes
                status = response.status_code
                status_codes[status] = status_codes.get(status, 0) + 1

            except Exception as e:
                errors += 1
                print(f"    Error on iteration {i+1}: {e}")

        if timings:
            return {
                "endpoint": f"{method} {path}",
                "iterations": iterations,
                "min_time": min(timings),
                "max_time": max(timings),
                "avg_time": statistics.mean(timings),
                "median_time": statistics.median(timings),
                "std_dev": statistics.stdev(timings) if len(timings) > 1 else 0,
                "p95": np.percentile(timings, 95) if timings else 0,
                "p99": np.percentile(timings, 99) if timings else 0,
                "errors": errors,
                "success_rate": ((iterations - errors) / iterations) * 100,
                "status_codes": status_codes,
                "all_timings": timings
            }
        else:
            return {
                "endpoint": f"{method} {path}",
                "error": "All requests failed",
                "errors": errors
            }

    async def profile_database_operations(self):
        """Profile database query performance"""
        print("\n🗄️ Profiling Database Operations...")

        db_operations = [
            ("List Users", "GET", "/api/v1/users/?limit=100"),
            ("List Assets", "GET", "/api/v1/assets/?limit=100"),
            ("Get Single User", "GET", "/api/v1/auth/me"),
            ("Search Assets", "GET", "/api/v1/assets/?search=test"),
        ]

        results = {}
        for name, method, path in db_operations:
            result = await self.profile_endpoint(method, path, iterations=20)
            results[name] = result
            print(f"    {name}: {result.get('avg_time', 0):.2f}ms avg")

        self.metrics["database_queries"] = results
        return results

    async def profile_api_endpoints(self):
        """Profile all API endpoints"""
        print("\n🔍 Profiling API Endpoints...")

        endpoints = [
            ("Authentication", "POST", "/api/v1/auth/login",
             {"username": "admin", "password": "admin"}),
            ("Get Current User", "GET", "/api/v1/auth/me", None),
            ("List Assets", "GET", "/api/v1/assets/", None),
            ("Create Asset", "POST", "/api/v1/assets/",
             {"name": "perf-test.com", "asset_type": "domain"}),
            ("List Users", "GET", "/api/v1/users/", None),
            ("Health Check", "GET", "/health", None),
            ("Metrics", "GET", "/api/v1/monitoring/metrics", None),
        ]

        for name, method, path, data in endpoints:
            if path == "/api/v1/auth/login":
                # Skip auth endpoint as we're already authenticated
                continue

            result = await self.profile_endpoint(method, path, data)
            self.metrics["endpoint_timings"][name] = result

        return self.metrics["endpoint_timings"]

    async def profile_concurrent_requests(self, concurrency: List[int] = [1, 5, 10, 20, 50]):
        """Profile performance under concurrent load"""
        print("\n⚡ Profiling Concurrent Requests...")

        results = {}
        endpoint = "/api/v1/assets/"

        for level in concurrency:
            print(f"  Testing with {level} concurrent requests...")

            async def make_request():
                start = time.perf_counter()
                try:
                    response = await self.client.get(endpoint)
                    return (time.perf_counter() - start) * 1000, response.status_code
                except:
                    return None, None

            # Run concurrent requests
            tasks = [make_request() for _ in range(level)]
            responses = await asyncio.gather(*tasks)

            # Calculate metrics
            timings = [r[0] for r in responses if r[0] is not None]
            success_count = sum(1 for r in responses if r[1] and 200 <= r[1] < 300)

            if timings:
                results[level] = {
                    "concurrency": level,
                    "avg_time": statistics.mean(timings),
                    "max_time": max(timings),
                    "min_time": min(timings),
                    "success_rate": (success_count / level) * 100,
                    "throughput": (level / (max(timings) / 1000)) if max(timings) > 0 else 0
                }

                print(f"    Avg: {results[level]['avg_time']:.2f}ms, "
                      f"Success: {results[level]['success_rate']:.1f}%, "
                      f"Throughput: {results[level]['throughput']:.1f} req/s")

        return results

    async def profile_memory_usage(self):
        """Profile memory usage patterns"""
        print("\n💾 Profiling Memory Usage...")

        process = psutil.Process()
        memory_samples = []

        # Take memory samples during various operations
        operations = [
            ("Baseline", None),
            ("After Auth", self.authenticate),
            ("After List Assets", lambda: self.client.get("/api/v1/assets/")),
            ("After List Users", lambda: self.client.get("/api/v1/users/")),
        ]

        for name, operation in operations:
            if operation:
                await operation()

            mem_info = process.memory_info()
            memory_samples.append({
                "operation": name,
                "rss": mem_info.rss / 1024 / 1024,  # Convert to MB
                "vms": mem_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            })

            print(f"    {name}: {memory_samples[-1]['rss']:.2f} MB")

        self.metrics["memory_usage"] = memory_samples
        return memory_samples

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze collected metrics and generate recommendations"""
        analysis = {
            "summary": {},
            "bottlenecks": [],
            "recommendations": []
        }

        # Analyze endpoint timings
        if self.metrics["endpoint_timings"]:
            slowest = sorted(
                self.metrics["endpoint_timings"].items(),
                key=lambda x: x[1].get("avg_time", 0),
                reverse=True
            )[:3]

            analysis["summary"]["slowest_endpoints"] = [
                {
                    "name": name,
                    "avg_time": data.get("avg_time", 0),
                    "p95": data.get("p95", 0)
                }
                for name, data in slowest
            ]

            # Identify bottlenecks
            for name, data in self.metrics["endpoint_timings"].items():
                if data.get("avg_time", 0) > 500:  # > 500ms is slow
                    analysis["bottlenecks"].append({
                        "type": "slow_endpoint",
                        "name": name,
                        "avg_time": data.get("avg_time", 0),
                        "severity": "high" if data.get("avg_time", 0) > 1000 else "medium"
                    })

                if data.get("errors", 0) > 0:
                    analysis["bottlenecks"].append({
                        "type": "unreliable_endpoint",
                        "name": name,
                        "error_rate": (data.get("errors", 0) / data.get("iterations", 1)) * 100,
                        "severity": "high"
                    })

        # Generate recommendations
        recommendations = []

        # Check for slow endpoints
        slow_endpoints = [b for b in analysis["bottlenecks"] if b["type"] == "slow_endpoint"]
        if slow_endpoints:
            recommendations.append({
                "category": "Performance",
                "issue": "Slow API endpoints detected",
                "recommendation": "Implement caching for frequently accessed endpoints",
                "priority": "high",
                "endpoints": [e["name"] for e in slow_endpoints]
            })

        # Check database performance
        if self.metrics["database_queries"]:
            slow_queries = [
                name for name, data in self.metrics["database_queries"].items()
                if data.get("avg_time", 0) > 200
            ]
            if slow_queries:
                recommendations.append({
                    "category": "Database",
                    "issue": "Slow database queries",
                    "recommendation": "Add database indexes and optimize queries",
                    "priority": "high",
                    "queries": slow_queries
                })

        # Check memory usage
        if self.metrics["memory_usage"]:
            memory_growth = self.metrics["memory_usage"][-1]["rss"] - self.metrics["memory_usage"][0]["rss"]
            if memory_growth > 50:  # > 50MB growth
                recommendations.append({
                    "category": "Memory",
                    "issue": f"High memory growth: {memory_growth:.2f} MB",
                    "recommendation": "Review for memory leaks and optimize data structures",
                    "priority": "medium"
                })

        analysis["recommendations"] = recommendations
        return analysis

    def generate_report(self, analysis: Dict[str, Any]):
        """Generate performance report"""
        report = []
        report.append("=" * 60)
        report.append("📊 Performance Profile Report")
        report.append("=" * 60)
        report.append(f"\nGenerated: {datetime.now().isoformat()}")

        # Summary
        report.append("\n## Summary")
        report.append("-" * 30)

        if analysis["summary"].get("slowest_endpoints"):
            report.append("\n### Slowest Endpoints:")
            for endpoint in analysis["summary"]["slowest_endpoints"]:
                report.append(f"  • {endpoint['name']}: {endpoint['avg_time']:.2f}ms avg, {endpoint['p95']:.2f}ms p95")

        # Bottlenecks
        if analysis["bottlenecks"]:
            report.append("\n## Bottlenecks Identified")
            report.append("-" * 30)

            for bottleneck in analysis["bottlenecks"]:
                severity_icon = "🔴" if bottleneck["severity"] == "high" else "🟡"
                report.append(f"\n{severity_icon} {bottleneck['type'].replace('_', ' ').title()}")
                report.append(f"   Name: {bottleneck.get('name', 'N/A')}")

                if bottleneck["type"] == "slow_endpoint":
                    report.append(f"   Average Time: {bottleneck['avg_time']:.2f}ms")
                elif bottleneck["type"] == "unreliable_endpoint":
                    report.append(f"   Error Rate: {bottleneck['error_rate']:.1f}%")

        # Recommendations
        if analysis["recommendations"]:
            report.append("\n## Recommendations")
            report.append("-" * 30)

            for i, rec in enumerate(analysis["recommendations"], 1):
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
                report.append(f"\n{i}. {priority_icon} [{rec['category']}] {rec['issue']}")
                report.append(f"   → {rec['recommendation']}")

                if rec.get("endpoints"):
                    report.append(f"   Affected: {', '.join(rec['endpoints'])}")
                elif rec.get("queries"):
                    report.append(f"   Affected: {', '.join(rec['queries'])}")

        # Detailed Metrics
        report.append("\n## Detailed Metrics")
        report.append("-" * 30)

        for name, data in self.metrics["endpoint_timings"].items():
            if isinstance(data, dict) and "avg_time" in data:
                report.append(f"\n### {name}")
                report.append(f"  Average: {data['avg_time']:.2f}ms")
                report.append(f"  Median: {data['median_time']:.2f}ms")
                report.append(f"  Min: {data['min_time']:.2f}ms")
                report.append(f"  Max: {data['max_time']:.2f}ms")
                report.append(f"  P95: {data['p95']:.2f}ms")
                report.append(f"  P99: {data['p99']:.2f}ms")
                report.append(f"  Success Rate: {data['success_rate']:.1f}%")

        return "\n".join(report)

    def generate_visualizations(self):
        """Generate performance visualization charts"""
        print("\n📈 Generating Visualizations...")

        # Create charts directory
        charts_dir = Path("performance_charts")
        charts_dir.mkdir(exist_ok=True)

        # 1. Endpoint Response Times Chart
        if self.metrics["endpoint_timings"]:
            fig, ax = plt.subplots(figsize=(12, 6))

            endpoints = []
            avg_times = []
            p95_times = []

            for name, data in self.metrics["endpoint_timings"].items():
                if isinstance(data, dict) and "avg_time" in data:
                    endpoints.append(name)
                    avg_times.append(data["avg_time"])
                    p95_times.append(data["p95"])

            x = np.arange(len(endpoints))
            width = 0.35

            bars1 = ax.bar(x - width/2, avg_times, width, label='Average', color='skyblue')
            bars2 = ax.bar(x + width/2, p95_times, width, label='P95', color='lightcoral')

            ax.set_xlabel('Endpoints')
            ax.set_ylabel('Response Time (ms)')
            ax.set_title('API Endpoint Performance')
            ax.set_xticks(x)
            ax.set_xticklabels(endpoints, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(charts_dir / 'endpoint_performance.png')
            print(f"  ✅ Saved: endpoint_performance.png")

        # 2. Memory Usage Chart
        if self.metrics["memory_usage"]:
            fig, ax = plt.subplots(figsize=(10, 6))

            operations = [m["operation"] for m in self.metrics["memory_usage"]]
            memory = [m["rss"] for m in self.metrics["memory_usage"]]

            ax.plot(operations, memory, marker='o', linewidth=2, markersize=8, color='green')
            ax.fill_between(range(len(operations)), memory, alpha=0.3, color='green')

            ax.set_xlabel('Operations')
            ax.set_ylabel('Memory Usage (MB)')
            ax.set_title('Memory Usage Pattern')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(charts_dir / 'memory_usage.png')
            print(f"  ✅ Saved: memory_usage.png")

        plt.close('all')

    async def run_complete_profile(self):
        """Run complete performance profile"""
        print("=" * 60)
        print("🚀 Starting Performance Profiling")
        print("=" * 60)

        # Authenticate
        print("\n🔐 Authenticating...")
        if not await self.authenticate():
            print("❌ Authentication failed")
            return

        print("✅ Authenticated successfully")

        # Run profiling
        await self.profile_api_endpoints()
        await self.profile_database_operations()
        concurrent_results = await self.profile_concurrent_requests()
        await self.profile_memory_usage()

        # Analyze results
        print("\n🔍 Analyzing Performance...")
        analysis = self.analyze_performance()

        # Generate report
        report = self.generate_report(analysis)
        print("\n" + report)

        # Save detailed results
        results_file = "performance_profile.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "metrics": self.metrics,
                "concurrent_load": concurrent_results,
                "analysis": analysis
            }, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Generate visualizations
        self.generate_visualizations()

        # Save report to file
        report_file = "performance_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"📄 Report saved to: {report_file}")

        await self.client.aclose()


async def main():
    profiler = PerformanceProfiler()
    await profiler.run_complete_profile()


if __name__ == "__main__":
    print("🔧 Performance Profiler")
    print("This tool will profile your API performance")
    print("Ensure the backend is running on http://localhost:8000")
    print("")

    # Check if matplotlib is installed
    try:
        import matplotlib
    except ImportError:
        print("⚠️  matplotlib not installed. Install with: pip install matplotlib")
        print("   Continuing without visualizations...")

    asyncio.run(main())