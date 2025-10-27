#!/usr/bin/env python3
"""
Self-Healing System for SOC Platform
Automatically detects and recovers from system failures
"""

import asyncio
import psutil
import httpx
import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import smtplib
from email.mime.text import MIMEText

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthCheck:
    """Health check for a service"""
    def __init__(self, name: str, url: str, critical: bool = True):
        self.name = name
        self.url = url
        self.critical = critical
        self.consecutive_failures = 0
        self.last_check = None
        self.status = "unknown"
        self.response_time = 0


class SelfHealingSystem:
    """Self-healing system for automatic recovery"""

    def __init__(self):
        self.config = {
            "backend_url": "http://localhost:8000",
            "frontend_url": "http://localhost:3000",
            "check_interval": 30,  # seconds
            "max_retries": 3,
            "recovery_actions": True,
            "alert_email": None,
            "metrics_file": "self_healing_metrics.json"
        }

        self.health_checks = [
            HealthCheck("Backend API", f"{self.config['backend_url']}/health", critical=True),
            HealthCheck("Frontend", self.config['frontend_url'], critical=True),
            HealthCheck("Database", f"{self.config['backend_url']}/api/v1/monitoring/health/detailed", critical=False),
            HealthCheck("Metrics", f"{self.config['backend_url']}/api/v1/monitoring/metrics", critical=False),
        ]

        self.recovery_actions = {
            "Backend API": self.recover_backend,
            "Frontend": self.recover_frontend,
            "Database": self.recover_database,
            "High Memory": self.recover_memory,
            "High CPU": self.recover_cpu,
            "Disk Space": self.recover_disk,
        }

        self.metrics = {
            "checks_performed": 0,
            "failures_detected": 0,
            "recoveries_attempted": 0,
            "recoveries_successful": 0,
            "alerts_sent": 0,
            "uptime_percentage": 100.0,
            "incidents": []
        }

        self.client = httpx.AsyncClient(timeout=10.0)

    async def check_service_health(self, health_check: HealthCheck) -> bool:
        """Check if a service is healthy"""
        try:
            start_time = time.time()
            response = await self.client.get(health_check.url)
            response_time = (time.time() - start_time) * 1000

            health_check.response_time = response_time
            health_check.last_check = datetime.now()

            if response.status_code == 200:
                health_check.status = "healthy"
                health_check.consecutive_failures = 0

                # Check response time threshold
                if response_time > 5000:  # 5 seconds
                    logger.warning(f"{health_check.name} is slow: {response_time:.2f}ms")
                    return False

                return True
            else:
                health_check.status = "unhealthy"
                health_check.consecutive_failures += 1
                return False

        except Exception as e:
            health_check.status = "unreachable"
            health_check.consecutive_failures += 1
            logger.error(f"Failed to check {health_check.name}: {e}")
            return False

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        resources = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / 1024 / 1024,
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024
        }

        # Check thresholds
        issues = []
        if cpu_percent > 80:
            issues.append({"type": "High CPU", "value": cpu_percent})
        if memory.percent > 85:
            issues.append({"type": "High Memory", "value": memory.percent})
        if disk.percent > 90:
            issues.append({"type": "Disk Space", "value": disk.percent})

        return {"resources": resources, "issues": issues}

    async def recover_backend(self) -> bool:
        """Recover backend service"""
        logger.info("Attempting to recover backend...")

        try:
            # Try to restart the backend
            subprocess.run(["pkill", "-f", "uvicorn app.main:app"], check=False)
            time.sleep(2)

            # Start backend
            subprocess.Popen([
                "python", "-m", "uvicorn", "app.main:app",
                "--host", "0.0.0.0", "--port", "8000", "--reload"
            ], cwd="backend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for startup
            await asyncio.sleep(10)

            # Verify recovery
            health_check = next(h for h in self.health_checks if h.name == "Backend API")
            if await self.check_service_health(health_check):
                logger.info("✅ Backend recovered successfully")
                return True
            else:
                logger.error("❌ Backend recovery failed")
                return False

        except Exception as e:
            logger.error(f"Backend recovery error: {e}")
            return False

    async def recover_frontend(self) -> bool:
        """Recover frontend service"""
        logger.info("Attempting to recover frontend...")

        try:
            # Kill existing frontend process
            subprocess.run(["pkill", "-f", "vite"], check=False)
            time.sleep(2)

            # Start frontend
            subprocess.Popen([
                "npm", "run", "dev"
            ], cwd="frontend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for startup
            await asyncio.sleep(15)

            # Verify recovery
            health_check = next(h for h in self.health_checks if h.name == "Frontend")
            if await self.check_service_health(health_check):
                logger.info("✅ Frontend recovered successfully")
                return True
            else:
                logger.error("❌ Frontend recovery failed")
                return False

        except Exception as e:
            logger.error(f"Frontend recovery error: {e}")
            return False

    async def recover_database(self) -> bool:
        """Recover database connection"""
        logger.info("Attempting to recover database...")

        try:
            # Try to restart PostgreSQL
            subprocess.run(["brew", "services", "restart", "postgresql"], check=False)
            # Or for Linux: subprocess.run(["sudo", "systemctl", "restart", "postgresql"], check=False)

            await asyncio.sleep(5)

            # Test connection
            response = await self.client.get(f"{self.config['backend_url']}/api/v1/monitoring/health/detailed")
            if response.status_code == 200:
                data = response.json()
                if data.get("components", {}).get("database", {}).get("connected"):
                    logger.info("✅ Database recovered successfully")
                    return True

            logger.error("❌ Database recovery failed")
            return False

        except Exception as e:
            logger.error(f"Database recovery error: {e}")
            return False

    async def recover_memory(self) -> bool:
        """Recover from high memory usage"""
        logger.info("Attempting to recover from high memory usage...")

        try:
            # Clear caches
            subprocess.run(["sync"], check=False)
            subprocess.run(["sudo", "sh", "-c", "echo 1 > /proc/sys/vm/drop_caches"], check=False)

            # Restart services with memory issues
            subprocess.run(["pkill", "-f", "celery"], check=False)
            subprocess.run(["pkill", "-f", "redis-server"], check=False)
            time.sleep(2)

            # Restart Redis
            subprocess.run(["redis-server", "--daemonize", "yes"], check=False)

            logger.info("✅ Memory recovery completed")
            return True

        except Exception as e:
            logger.error(f"Memory recovery error: {e}")
            return False

    async def recover_cpu(self) -> bool:
        """Recover from high CPU usage"""
        logger.info("Attempting to recover from high CPU usage...")

        try:
            # Kill CPU-intensive processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                if proc.info['cpu_percent'] > 50:
                    logger.info(f"Killing high CPU process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()

            logger.info("✅ CPU recovery completed")
            return True

        except Exception as e:
            logger.error(f"CPU recovery error: {e}")
            return False

    async def recover_disk(self) -> bool:
        """Recover from low disk space"""
        logger.info("Attempting to recover disk space...")

        try:
            # Clean up logs
            log_dirs = ["backend/logs", "frontend/logs", "logs", "/var/log"]
            for log_dir in log_dirs:
                if Path(log_dir).exists():
                    subprocess.run(["find", log_dir, "-name", "*.log", "-mtime", "+7", "-delete"], check=False)

            # Clean Docker if available
            subprocess.run(["docker", "system", "prune", "-f"], check=False)

            # Clean npm cache
            subprocess.run(["npm", "cache", "clean", "--force"], check=False)

            logger.info("✅ Disk space recovery completed")
            return True

        except Exception as e:
            logger.error(f"Disk recovery error: {e}")
            return False

    async def send_alert(self, message: str, severity: str = "WARNING"):
        """Send alert notification"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "message": message
        }

        # Log alert
        logger.warning(f"ALERT [{severity}]: {message}")

        # Save to metrics
        self.metrics["alerts_sent"] += 1
        self.metrics["incidents"].append(alert)

        # Send email if configured
        if self.config.get("alert_email"):
            try:
                msg = MIMEText(f"Alert from Self-Healing System:\n\n{message}")
                msg['Subject'] = f'[{severity}] SOC Platform Alert'
                msg['From'] = 'alerts@soc-platform.com'
                msg['To'] = self.config["alert_email"]

                # Send email (configure SMTP settings)
                # smtp = smtplib.SMTP('localhost')
                # smtp.send_message(msg)
                # smtp.quit()
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")

        # Send to monitoring dashboard via WebSocket
        try:
            # WebSocket notification implementation
            pass
        except:
            pass

    async def perform_healing_cycle(self):
        """Perform one healing cycle"""
        self.metrics["checks_performed"] += 1
        issues_found = []
        recoveries_performed = []

        # Check all health endpoints
        for health_check in self.health_checks:
            is_healthy = await self.check_service_health(health_check)

            if not is_healthy:
                issues_found.append(health_check.name)
                self.metrics["failures_detected"] += 1

                # Attempt recovery if critical
                if health_check.critical and health_check.consecutive_failures >= 2:
                    await self.send_alert(
                        f"{health_check.name} is down. Attempting recovery...",
                        "CRITICAL"
                    )

                    if health_check.name in self.recovery_actions:
                        recovery_func = self.recovery_actions[health_check.name]
                        self.metrics["recoveries_attempted"] += 1

                        if await recovery_func():
                            self.metrics["recoveries_successful"] += 1
                            recoveries_performed.append(health_check.name)
                            await self.send_alert(
                                f"{health_check.name} recovered successfully",
                                "INFO"
                            )
                        else:
                            await self.send_alert(
                                f"Failed to recover {health_check.name}",
                                "ERROR"
                            )

        # Check system resources
        system_check = await self.check_system_resources()
        for issue in system_check["issues"]:
            issues_found.append(issue["type"])

            # Attempt recovery
            if issue["type"] in self.recovery_actions:
                recovery_func = self.recovery_actions[issue["type"]]
                if await recovery_func():
                    recoveries_performed.append(issue["type"])

        # Calculate uptime
        total_checks = len(self.health_checks) * self.metrics["checks_performed"]
        if total_checks > 0:
            self.metrics["uptime_percentage"] = (
                (total_checks - self.metrics["failures_detected"]) / total_checks * 100
            )

        # Save metrics
        self.save_metrics()

        return {
            "issues_found": issues_found,
            "recoveries_performed": recoveries_performed,
            "system_resources": system_check["resources"]
        }

    def save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.config["metrics_file"], 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def load_metrics(self):
        """Load metrics from file"""
        try:
            if Path(self.config["metrics_file"]).exists():
                with open(self.config["metrics_file"], 'r') as f:
                    saved_metrics = json.load(f)
                    self.metrics.update(saved_metrics)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")

    async def run(self):
        """Run the self-healing system"""
        logger.info("=" * 60)
        logger.info("🏥 Self-Healing System Started")
        logger.info("=" * 60)
        logger.info(f"Check Interval: {self.config['check_interval']} seconds")
        logger.info(f"Recovery Actions: {'Enabled' if self.config['recovery_actions'] else 'Disabled'}")
        logger.info("=" * 60)

        self.load_metrics()

        try:
            while True:
                start_time = time.time()

                # Perform healing cycle
                result = await self.perform_healing_cycle()

                # Log status
                if result["issues_found"]:
                    logger.warning(f"Issues found: {', '.join(result['issues_found'])}")
                else:
                    logger.info("✅ All systems healthy")

                if result["recoveries_performed"]:
                    logger.info(f"Recoveries performed: {', '.join(result['recoveries_performed'])}")

                # Display metrics
                logger.info(f"Metrics - Uptime: {self.metrics['uptime_percentage']:.2f}%, "
                           f"Checks: {self.metrics['checks_performed']}, "
                           f"Failures: {self.metrics['failures_detected']}, "
                           f"Recoveries: {self.metrics['recoveries_successful']}/{self.metrics['recoveries_attempted']}")

                # Wait for next cycle
                elapsed = time.time() - start_time
                wait_time = max(0, self.config['check_interval'] - elapsed)
                await asyncio.sleep(wait_time)

        except KeyboardInterrupt:
            logger.info("\n🛑 Self-healing system stopped")
            self.save_metrics()
            await self.client.aclose()


async def main():
    system = SelfHealingSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())