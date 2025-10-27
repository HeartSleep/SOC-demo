"""
URL安全验证工具
防止SSRF攻击
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class URLValidationError(Exception):
    """URL验证失败异常"""
    pass


class URLValidator:
    """URL安全验证器"""

    # 黑名单域名和IP
    BLOCKED_DOMAINS = {
        'localhost',
        'metadata.google.internal',  # GCP metadata
        'metadata.azure.com',  # Azure metadata
    }

    BLOCKED_IPS = {
        '169.254.169.254',  # AWS/Azure metadata
        '127.0.0.1',
        '0.0.0.0',
    }

    def __init__(self, allow_internal: bool = False):
        """
        初始化验证器

        Args:
            allow_internal: 是否允许内网地址（开发环境可设为True）
        """
        self.allow_internal = allow_internal

    def validate(self, url: str) -> bool:
        """
        验证URL是否安全

        Args:
            url: 待验证的URL

        Returns:
            True if valid

        Raises:
            URLValidationError: 如果URL不安全
        """
        try:
            # 1. 解析URL
            parsed = urlparse(url)

            # 2. 检查协议
            if parsed.scheme not in ['http', 'https']:
                raise URLValidationError(
                    f"Only HTTP/HTTPS protocols are allowed, got: {parsed.scheme}"
                )

            # 3. 检查主机名
            hostname = parsed.hostname
            if not hostname:
                raise URLValidationError("Missing hostname")

            # 4. 检查黑名单域名
            if hostname.lower() in self.BLOCKED_DOMAINS:
                raise URLValidationError(f"Domain is blocked: {hostname}")

            # 5. 解析IP地址
            try:
                ip_str = socket.gethostbyname(hostname)
            except socket.gaierror:
                raise URLValidationError(f"Cannot resolve hostname: {hostname}")

            # 6. 检查黑名单IP
            if ip_str in self.BLOCKED_IPS:
                raise URLValidationError(f"IP address is blocked: {ip_str}")

            # 7. 检查IP类型
            try:
                ip_obj = ipaddress.ip_address(ip_str)

                # 如果不允许内网地址
                if not self.allow_internal:
                    if ip_obj.is_private:
                        raise URLValidationError(
                            f"Private IP addresses are not allowed: {ip_str}"
                        )

                    if ip_obj.is_loopback:
                        raise URLValidationError(
                            f"Loopback addresses are not allowed: {ip_str}"
                        )

                    if ip_obj.is_link_local:
                        raise URLValidationError(
                            f"Link-local addresses are not allowed: {ip_str}"
                        )

                    if ip_obj.is_multicast:
                        raise URLValidationError(
                            f"Multicast addresses are not allowed: {ip_str}"
                        )

                    if ip_obj.is_reserved:
                        raise URLValidationError(
                            f"Reserved addresses are not allowed: {ip_str}"
                        )

            except ValueError:
                raise URLValidationError(f"Invalid IP address: {ip_str}")

            # 8. 检查端口（可选）
            port = parsed.port
            if port:
                # 禁止常见内部服务端口
                blocked_ports = {
                    22,    # SSH
                    3306,  # MySQL
                    5432,  # PostgreSQL
                    6379,  # Redis
                    27017, # MongoDB
                    9200,  # Elasticsearch
                }
                if port in blocked_ports and not self.allow_internal:
                    raise URLValidationError(
                        f"Port {port} is not allowed for external scanning"
                    )

            logger.info(f"URL validation passed: {url} -> {ip_str}")
            return True

        except URLValidationError:
            raise
        except Exception as e:
            raise URLValidationError(f"URL validation error: {str(e)}")

    def get_safe_url_info(self, url: str) -> Optional[dict]:
        """
        获取安全URL的信息

        Returns:
            包含hostname、ip、port等信息的字典，如果不安全则返回None
        """
        try:
            self.validate(url)
            parsed = urlparse(url)
            hostname = parsed.hostname
            ip = socket.gethostbyname(hostname)

            return {
                'url': url,
                'hostname': hostname,
                'ip': ip,
                'port': parsed.port,
                'scheme': parsed.scheme,
                'is_safe': True
            }
        except URLValidationError as e:
            logger.warning(f"Unsafe URL: {url}, reason: {str(e)}")
            return None


# 全局验证器实例
# 生产环境：不允许内网
url_validator = URLValidator(allow_internal=False)

# 开发环境使用：允许内网（在配置文件中切换）
# url_validator = URLValidator(allow_internal=True)
