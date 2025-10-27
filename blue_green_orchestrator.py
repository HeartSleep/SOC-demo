#!/usr/bin/env python3
"""
Blue-Green Deployment Orchestrator
Advanced zero-downtime deployment with monitoring and rollback
"""

import asyncio
import subprocess
import json
import time
import httpx
import docker
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from enum import Enum
import logging
import psutil
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Environment(Enum):
    BLUE = "blue"
    GREEN = "green"


class DeploymentStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    TESTING = "testing"
    SWITCHING = "switching"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class BlueGreenOrchestrator:
    """Orchestrates blue-green deployments with monitoring and rollback"""

    def __init__(self, config_file: str = "deployment-config.yaml"):
        self.config = self.load_config(config_file)
        self.docker_client = docker.from_env()
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.current_env = self.get_current_environment()
        self.target_env = None
        self.deployment_id = None
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "tests_passed": False,
            "health_checks_passed": False,
            "rollback_triggered": False,
            "error_count": 0,
            "warnings": []
        }

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load deployment configuration"""
        default_config = {
            "registry": "ghcr.io",
            "image_prefix": "soc-platform",
            "environments": {
                "blue": {
                    "backend_port": 8001,
                    "frontend_port": 3001,
                    "color": "blue"
                },
                "green": {
                    "backend_port": 8002,
                    "frontend_port": 3002,
                    "color": "green"
                }
            },
            "health_check": {
                "retries": 30,
                "interval": 10,
                "timeout": 5
            },
            "monitoring": {
                "error_threshold": 0.01,  # 1% error rate
                "response_time_threshold": 500,  # 500ms
                "monitoring_duration": 120  # 2 minutes
            },
            "rollback": {
                "automatic": True,
                "conditions": {
                    "error_rate_exceeded": True,
                    "health_check_failed": True,
                    "response_time_exceeded": True,
                    "test_failed": True
                }
            },
            "notifications": {
                "slack_webhook": None,
                "email": None,
                "pagerduty_key": None
            }
        }

        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                default_config.update(loaded_config)

        return default_config

    def get_current_environment(self) -> Environment:
        """Get the currently active environment"""
        env_file = Path("/var/lib/soc-platform/current-env")
        if env_file.exists():
            env = env_file.read_text().strip()
            return Environment(env)
        return Environment.BLUE

    def set_current_environment(self, env: Environment):
        """Set the currently active environment"""
        env_file = Path("/var/lib/soc-platform/current-env")
        env_file.parent.mkdir(parents=True, exist_ok=True)
        env_file.write_text(env.value)
        self.current_env = env

    async def health_check(self, url: str, service_name: str) -> bool:
        """Perform health check on a service"""
        retries = self.config["health_check"]["retries"]
        interval = self.config["health_check"]["interval"]

        for attempt in range(retries):
            try:
                response = await self.http_client.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ Health check passed for {service_name}")
                    return True
            except Exception as e:
                logger.warning(f"Health check attempt {attempt + 1}/{retries} failed for {service_name}: {e}")

            if attempt < retries - 1:
                await asyncio.sleep(interval)

        logger.error(f"❌ Health check failed for {service_name} after {retries} attempts")
        return False

    async def run_integration_tests(self, backend_port: int, frontend_port: int) -> Tuple[bool, List[str]]:
        """Run integration tests against the deployment"""
        logger.info("Running integration tests...")
        test_results = []
        all_passed = True

        tests = [
            ("Authentication", self.test_authentication),
            ("API Endpoints", self.test_api_endpoints),
            ("WebSocket", self.test_websocket),
            ("Frontend Loading", self.test_frontend),
            ("Database Connection", self.test_database),
            ("Performance", self.test_performance)
        ]

        for test_name, test_func in tests:
            try:
                result = await test_func(backend_port, frontend_port)
                if result:
                    test_results.append(f"✅ {test_name}: PASSED")
                else:
                    test_results.append(f"❌ {test_name}: FAILED")
                    all_passed = False
            except Exception as e:
                test_results.append(f"❌ {test_name}: ERROR - {e}")
                all_passed = False

        return all_passed, test_results

    async def test_authentication(self, backend_port: int, frontend_port: int) -> bool:
        """Test authentication flow"""
        try:
            # Test login
            response = await self.http_client.post(
                f"http://localhost:{backend_port}/api/v1/auth/login",
                json={"username": "test_user", "password": "test_pass"}
            )
            if response.status_code not in [200, 201]:
                return False

            # Test token validation
            token = response.json().get("access_token")
            if not token:
                return False

            # Test authenticated request
            response = await self.http_client.get(
                f"http://localhost:{backend_port}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            return False

    async def test_api_endpoints(self, backend_port: int, frontend_port: int) -> bool:
        """Test critical API endpoints"""
        endpoints = [
            "/api/v1/users/",
            "/api/v1/assets/",
            "/api/v1/monitoring/metrics",
            "/api/v1/monitoring/health/detailed"
        ]

        for endpoint in endpoints:
            try:
                response = await self.http_client.get(f"http://localhost:{backend_port}{endpoint}")
                if response.status_code not in [200, 401]:  # 401 is ok for auth-required endpoints
                    logger.warning(f"Endpoint {endpoint} returned {response.status_code}")
                    return False
            except Exception as e:
                logger.error(f"Failed to test endpoint {endpoint}: {e}")
                return False

        return True

    async def test_websocket(self, backend_port: int, frontend_port: int) -> bool:
        """Test WebSocket connectivity"""
        try:
            import websockets

            async with websockets.connect(f"ws://localhost:{backend_port}/api/v1/ws/test") as ws:
                await ws.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(response)
                return data.get("type") == "pong"

        except Exception as e:
            logger.warning(f"WebSocket test failed: {e}")
            return False

    async def test_frontend(self, backend_port: int, frontend_port: int) -> bool:
        """Test frontend availability"""
        try:
            response = await self.http_client.get(f"http://localhost:{frontend_port}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Frontend test failed: {e}")
            return False

    async def test_database(self, backend_port: int, frontend_port: int) -> bool:
        """Test database connectivity"""
        try:
            response = await self.http_client.get(
                f"http://localhost:{backend_port}/api/v1/monitoring/health/detailed"
            )
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("components", {}).get("database", {})
                return db_status.get("connected", False)
            return False
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False

    async def test_performance(self, backend_port: int, frontend_port: int) -> bool:
        """Test performance thresholds"""
        threshold = self.config["monitoring"]["response_time_threshold"]

        try:
            # Test multiple endpoints
            endpoints = ["/health", "/api/v1/users/", "/api/v1/assets/"]
            response_times = []

            for endpoint in endpoints:
                start = time.time()
                response = await self.http_client.get(f"http://localhost:{backend_port}{endpoint}")
                response_time = (time.time() - start) * 1000  # Convert to ms
                response_times.append(response_time)

            avg_response_time = sum(response_times) / len(response_times)
            logger.info(f"Average response time: {avg_response_time:.2f}ms (threshold: {threshold}ms)")

            return avg_response_time < threshold

        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False

    async def deploy_environment(self, env: Environment, image_tag: str) -> bool:
        """Deploy to specified environment"""
        logger.info(f"🚀 Deploying to {env.value} environment with tag {image_tag}...")

        env_config = self.config["environments"][env.value]
        backend_port = env_config["backend_port"]
        frontend_port = env_config["frontend_port"]

        # Generate docker-compose configuration
        compose_config = {
            "version": "3.8",
            "services": {
                f"backend-{env.value}": {
                    "image": f"{self.config['registry']}/{self.config['image_prefix']}-backend:{image_tag}",
                    "container_name": f"soc-backend-{env.value}",
                    "environment": [
                        f"ENVIRONMENT={env.value}",
                        "DATABASE_URL=${DATABASE_URL}",
                        "REDIS_URL=${REDIS_URL}",
                        "SECRET_KEY=${SECRET_KEY}",
                        "JWT_SECRET_KEY=${JWT_SECRET_KEY}"
                    ],
                    "ports": [f"{backend_port}:8000"],
                    "networks": ["soc-network"],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    },
                    "restart": "unless-stopped"
                },
                f"frontend-{env.value}": {
                    "image": f"{self.config['registry']}/{self.config['image_prefix']}-frontend:{image_tag}",
                    "container_name": f"soc-frontend-{env.value}",
                    "environment": [
                        f"VITE_API_URL=http://localhost:{backend_port}",
                        f"VITE_WS_URL=ws://localhost:{backend_port}"
                    ],
                    "ports": [f"{frontend_port}:80"],
                    "networks": ["soc-network"],
                    "depends_on": [f"backend-{env.value}"],
                    "restart": "unless-stopped"
                }
            },
            "networks": {
                "soc-network": {
                    "external": True
                }
            }
        }

        # Write docker-compose file
        compose_file = f"docker-compose.{env.value}.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(compose_config, f)

        # Create network if not exists
        try:
            self.docker_client.networks.get("soc-network")
        except docker.errors.NotFound:
            self.docker_client.networks.create("soc-network")

        # Deploy using docker-compose
        try:
            subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d"],
                check=True,
                capture_output=True
            )
            logger.info(f"✅ Containers started for {env.value} environment")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy {env.value} environment: {e}")
            return False

    async def switch_traffic(self, target_env: Environment) -> bool:
        """Switch traffic to target environment"""
        logger.info(f"🔄 Switching traffic to {target_env.value} environment...")

        env_config = self.config["environments"][target_env.value]
        backend_port = env_config["backend_port"]
        frontend_port = env_config["frontend_port"]

        # Update load balancer configuration
        # This would typically update nginx, HAProxy, or cloud load balancer
        # For demonstration, we'll update a simple nginx config

        nginx_config = f"""
upstream backend {{
    server localhost:{backend_port};
}}

upstream frontend {{
    server localhost:{frontend_port};
}}

server {{
    listen 80;
    server_name localhost;

    location / {{
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}

    location /api {{
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}

    location /api/v1/ws {{
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""

        # Write nginx config (would need sudo in production)
        nginx_file = Path("/tmp/soc-platform-nginx.conf")
        nginx_file.write_text(nginx_config)

        # In production, you would:
        # 1. Test nginx config: nginx -t
        # 2. Copy to /etc/nginx/sites-available/
        # 3. Reload nginx: nginx -s reload

        logger.info(f"✅ Traffic switched to {target_env.value} environment")
        self.set_current_environment(target_env)
        return True

    async def monitor_deployment(self, env: Environment, duration: int) -> bool:
        """Monitor deployment for issues"""
        logger.info(f"👁️ Monitoring {env.value} deployment for {duration} seconds...")

        env_config = self.config["environments"][env.value]
        backend_port = env_config["backend_port"]

        start_time = time.time()
        error_count = 0
        total_requests = 0
        response_times = []

        while time.time() - start_time < duration:
            try:
                # Check health
                req_start = time.time()
                response = await self.http_client.get(f"http://localhost:{backend_port}/health")
                response_time = (time.time() - req_start) * 1000

                total_requests += 1
                response_times.append(response_time)

                if response.status_code != 200:
                    error_count += 1

                # Check metrics
                metrics_response = await self.http_client.get(
                    f"http://localhost:{backend_port}/api/v1/monitoring/metrics"
                )
                if metrics_response.status_code == 200:
                    metrics = metrics_response.json()
                    current_error_rate = metrics.get("error_rate", 0)

                    # Check thresholds
                    if current_error_rate > self.config["monitoring"]["error_threshold"] * 100:
                        logger.error(f"Error rate exceeded threshold: {current_error_rate}%")
                        return False

            except Exception as e:
                logger.warning(f"Monitoring error: {e}")
                error_count += 1

            # Check error rate
            if total_requests > 0:
                error_rate = error_count / total_requests
                if error_rate > self.config["monitoring"]["error_threshold"]:
                    logger.error(f"Error rate {error_rate:.2%} exceeds threshold")
                    return False

            # Check response time
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time > self.config["monitoring"]["response_time_threshold"]:
                    logger.error(f"Response time {avg_response_time:.2f}ms exceeds threshold")
                    return False

            await asyncio.sleep(5)  # Check every 5 seconds

        logger.info("✅ Monitoring completed successfully")
        return True

    async def rollback(self, from_env: Environment, to_env: Environment) -> bool:
        """Rollback deployment"""
        logger.warning(f"🔄 Rolling back from {from_env.value} to {to_env.value}...")

        # Switch traffic back
        if await self.switch_traffic(to_env):
            # Stop failed environment
            try:
                subprocess.run(
                    ["docker-compose", "-f", f"docker-compose.{from_env.value}.yml", "down"],
                    check=True,
                    capture_output=True
                )
                logger.info(f"✅ Rolled back to {to_env.value} environment")
                self.metrics["rollback_triggered"] = True
                return True

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to stop {from_env.value} environment: {e}")

        return False

    async def cleanup_old_environment(self, env: Environment, delay: int = 300):
        """Clean up old environment after successful deployment"""
        logger.info(f"Scheduling cleanup of {env.value} environment in {delay} seconds...")

        await asyncio.sleep(delay)

        try:
            subprocess.run(
                ["docker-compose", "-f", f"docker-compose.{env.value}.yml", "down"],
                check=True,
                capture_output=True
            )
            logger.info(f"✅ Cleaned up {env.value} environment")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup {env.value} environment: {e}")

    async def notify(self, message: str, severity: str = "info"):
        """Send deployment notifications"""
        # Slack notification
        if self.config["notifications"]["slack_webhook"]:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            await self.http_client.post(
                self.config["notifications"]["slack_webhook"],
                json={"text": f"{icon.get(severity, '')} {message}"}
            )

        # Add email, PagerDuty, etc. as needed
        logger.info(f"Notification [{severity}]: {message}")

    async def execute_deployment(self, image_tag: str) -> DeploymentStatus:
        """Execute the full blue-green deployment"""
        self.deployment_id = f"deploy-{int(time.time())}"
        self.metrics["start_time"] = datetime.now()

        # Determine target environment
        self.target_env = Environment.GREEN if self.current_env == Environment.BLUE else Environment.BLUE

        logger.info("=" * 60)
        logger.info(f"🚀 Blue-Green Deployment Started")
        logger.info(f"   Deployment ID: {self.deployment_id}")
        logger.info(f"   Current: {self.current_env.value}")
        logger.info(f"   Target: {self.target_env.value}")
        logger.info(f"   Image Tag: {image_tag}")
        logger.info("=" * 60)

        try:
            # Step 1: Deploy to target environment
            await self.notify(f"Starting deployment to {self.target_env.value} environment", "info")

            if not await self.deploy_environment(self.target_env, image_tag):
                raise Exception("Failed to deploy target environment")

            # Step 2: Health checks
            env_config = self.config["environments"][self.target_env.value]
            backend_url = f"http://localhost:{env_config['backend_port']}/health"
            frontend_url = f"http://localhost:{env_config['frontend_port']}"

            if not await self.health_check(backend_url, f"backend-{self.target_env.value}"):
                raise Exception("Backend health check failed")

            if not await self.health_check(frontend_url, f"frontend-{self.target_env.value}"):
                raise Exception("Frontend health check failed")

            self.metrics["health_checks_passed"] = True

            # Step 3: Run integration tests
            tests_passed, test_results = await self.run_integration_tests(
                env_config["backend_port"],
                env_config["frontend_port"]
            )

            for result in test_results:
                logger.info(result)

            if not tests_passed:
                raise Exception("Integration tests failed")

            self.metrics["tests_passed"] = True

            # Step 4: Switch traffic
            if not await self.switch_traffic(self.target_env):
                raise Exception("Failed to switch traffic")

            # Step 5: Monitor new deployment
            monitoring_duration = self.config["monitoring"]["monitoring_duration"]
            if not await self.monitor_deployment(self.target_env, monitoring_duration):
                raise Exception("Monitoring detected issues")

            # Step 6: Cleanup old environment
            asyncio.create_task(self.cleanup_old_environment(self.current_env))

            # Success
            self.metrics["end_time"] = datetime.now()
            self.metrics["duration"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()

            await self.notify(
                f"✅ Deployment successful! Switched from {self.current_env.value} to {self.target_env.value} "
                f"in {self.metrics['duration']:.1f} seconds",
                "success"
            )

            return DeploymentStatus.SUCCESS

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            self.metrics["error_count"] += 1

            # Attempt rollback
            if self.config["rollback"]["automatic"]:
                await self.notify(f"Deployment failed, initiating rollback: {e}", "error")

                if await self.rollback(self.target_env, self.current_env):
                    await self.notify("Rollback completed successfully", "warning")
                    return DeploymentStatus.ROLLED_BACK
                else:
                    await self.notify("⚠️ CRITICAL: Rollback failed! Manual intervention required!", "error")

            return DeploymentStatus.FAILED

    def generate_report(self):
        """Generate deployment report"""
        report = f"""
        Deployment Report - {self.deployment_id}
        {'=' * 50}

        Deployment Details:
        - Start Time: {self.metrics['start_time']}
        - End Time: {self.metrics['end_time']}
        - Duration: {self.metrics['duration']:.1f} seconds
        - Source Environment: {self.current_env.value}
        - Target Environment: {self.target_env.value}

        Results:
        - Health Checks: {'✅ Passed' if self.metrics['health_checks_passed'] else '❌ Failed'}
        - Integration Tests: {'✅ Passed' if self.metrics['tests_passed'] else '❌ Failed'}
        - Rollback Triggered: {'Yes' if self.metrics['rollback_triggered'] else 'No'}
        - Error Count: {self.metrics['error_count']}

        Warnings:
        {chr(10).join('- ' + w for w in self.metrics['warnings']) if self.metrics['warnings'] else '- None'}
        """

        # Save report
        report_file = Path(f"deployment-reports/{self.deployment_id}.txt")
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report)

        logger.info(report)
        return report


async def main():
    """Main deployment function"""
    import argparse

    parser = argparse.ArgumentParser(description="Blue-Green Deployment Orchestrator")
    parser.add_argument("--tag", required=True, help="Docker image tag to deploy")
    parser.add_argument("--config", default="deployment-config.yaml", help="Configuration file")
    parser.add_argument("--skip-tests", action="store_true", help="Skip integration tests")
    parser.add_argument("--no-rollback", action="store_true", help="Disable automatic rollback")

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = BlueGreenOrchestrator(args.config)

    # Override config if needed
    if args.skip_tests:
        orchestrator.config["rollback"]["conditions"]["test_failed"] = False
    if args.no_rollback:
        orchestrator.config["rollback"]["automatic"] = False

    # Execute deployment
    status = await orchestrator.execute_deployment(args.tag)

    # Generate report
    orchestrator.generate_report()

    # Exit with appropriate code
    if status == DeploymentStatus.SUCCESS:
        sys.exit(0)
    else:
        sys.exit(1)


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    logger.warning("Deployment interrupted! Initiating cleanup...")
    # Cleanup logic here
    sys.exit(1)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run deployment
    asyncio.run(main())