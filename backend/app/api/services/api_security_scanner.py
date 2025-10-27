import asyncio
import httpx
import re
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from collections import defaultdict

from app.core.logging import get_logger
from app.core.url_validator import url_validator, URLValidationError
from app.api.services.js_extractor import JSExtractorService
from app.api.services.api_discovery import APIDiscoveryService

logger = get_logger(__name__)


class APISecurityScanner:
    """API安全扫描器 - 主服务类

    整合所有功能模块:
    1. JS资源提取
    2. API发现
    3. 微服务架构识别
    4. API未授权访问检测
    5. 敏感信息匹配
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.use_ai = self.config.get('use_ai', True)

        # 初始化子服务
        self.js_extractor = JSExtractorService()
        self.api_discovery = APIDiscoveryService(use_ai=self.use_ai)

        # HTTP客户端配置
        self.timeout = 30
        self.user_agent = "Mozilla/5.0 SOC-Platform API-Security-Scanner"

    async def scan(
        self,
        target_url: str,
        scan_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行完整的API安全扫描

        Args:
            target_url: 目标URL
            scan_config: 扫描配置

        Returns:
            扫描结果
        """
        result = {
            "target_url": target_url,
            "start_time": datetime.utcnow().isoformat(),
            "status": "running",
            "js_resources": [],
            "apis": [],
            "microservices": [],
            "security_issues": [],
            "statistics": {}
        }

        try:
            logger.info(f"开始API安全扫描: {target_url}")

            # 阶段1: JS资源提取
            if scan_config.get('enable_js_extraction', True):
                logger.info("阶段1: 提取JS资源")
                js_resources = await self.js_extractor.extract_js_resources(
                    target_url,
                    max_files=scan_config.get('max_js_files', 100)
                )
                result["js_resources"] = js_resources
                logger.info(f"提取到 {len(js_resources)} 个JS资源")

            # 阶段2: API发现
            if scan_config.get('enable_api_discovery', True):
                logger.info("阶段2: 发现API接口")
                apis = await self.api_discovery.discover_apis(
                    js_resources,
                    target_url
                )
                result["apis"] = apis
                logger.info(f"发现 {len(apis)} 个API接口")

            # 阶段3: 微服务架构识别
            if scan_config.get('enable_microservice_detection', True):
                logger.info("阶段3: 识别微服务架构")
                microservices = await self.identify_microservices(result["apis"])
                result["microservices"] = microservices
                logger.info(f"识别到 {len(microservices)} 个微服务")

            # 阶段4: API未授权访问检测
            if scan_config.get('enable_unauthorized_check', True):
                logger.info("阶段4: 检测API未授权访问")
                unauthorized_issues = await self.check_unauthorized_access(
                    result["apis"],
                    target_url
                )
                result["security_issues"].extend(unauthorized_issues)
                logger.info(f"发现 {len(unauthorized_issues)} 个未授权访问问题")

            # 阶段5: 敏感信息匹配
            if scan_config.get('enable_sensitive_info_check', True):
                logger.info("阶段5: 匹配敏感信息")
                sensitive_issues = await self.check_sensitive_information(
                    result["js_resources"],
                    result["apis"]
                )
                result["security_issues"].extend(sensitive_issues)
                logger.info(f"发现 {len(sensitive_issues)} 个敏感信息泄露")

            # 统计结果
            result["statistics"] = self._calculate_statistics(result)
            result["status"] = "completed"
            result["end_time"] = datetime.utcnow().isoformat()

            logger.info(f"API安全扫描完成: {target_url}")

        except Exception as e:
            logger.error(f"API安全扫描失败: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    async def identify_microservices(
        self,
        apis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """识别微服务架构

        根据service_path对API进行分组，识别不同的微服务
        """
        microservices = []

        try:
            # 按service_path分组
            service_groups = defaultdict(list)

            for api in apis:
                service_path = api.get('service_path')
                if service_path:
                    key = f"{api['base_url']}{api.get('base_api_path', '')}{service_path}"
                    service_groups[key].append(api)

            # 为每个服务创建微服务信息
            for service_full_path, service_apis in service_groups.items():
                if not service_apis:
                    continue

                first_api = service_apis[0]
                service_name = first_api.get('service_path', 'unknown')

                # 提取唯一路径
                unique_paths = list(set([api['api_path'] for api in service_apis]))

                microservice = {
                    "base_url": first_api['base_url'],
                    "service_name": service_name,
                    "service_full_path": service_full_path,
                    "total_endpoints": len(service_apis),
                    "unique_paths": unique_paths,
                    "detected_technologies": await self._detect_technologies(service_full_path),
                    "has_vulnerabilities": False,
                    "vulnerability_details": []
                }

                # 检测组件漏洞 (SpringBoot Actuator, FastJSON, Log4j2等)
                vulnerabilities = await self._check_component_vulnerabilities(
                    service_full_path,
                    microservice['detected_technologies']
                )

                if vulnerabilities:
                    microservice["has_vulnerabilities"] = True
                    microservice["vulnerability_details"] = vulnerabilities

                microservices.append(microservice)

        except Exception as e:
            logger.error(f"识别微服务失败: {str(e)}")

        return microservices

    async def _detect_technologies(self, service_url: str) -> List[str]:
        """检测技术栈"""
        technologies = []

        try:
            # ✅ 安全修复：验证URL安全性
            try:
                url_validator.validate(service_url)
            except URLValidationError as e:
                logger.warning(f"Blocked unsafe service URL: {service_url}, reason: {str(e)}")
                return []

            # ✅ 安全修复：开启SSL验证
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=True,  # 修改：开启SSL验证
                follow_redirects=True
            ) as client:
                headers = {"User-Agent": self.user_agent}

                # 尝试访问服务
                try:
                    response = await client.get(service_url, headers=headers)

                    # 从响应头检测
                    server = response.headers.get('server', '').lower()
                    if 'spring' in server or 'tomcat' in server:
                        technologies.append('SpringBoot')

                    powered_by = response.headers.get('x-powered-by', '').lower()
                    if 'java' in powered_by:
                        technologies.append('Java')

                    # 从响应体检测
                    content = response.text.lower()
                    if 'fastjson' in content:
                        technologies.append('FastJSON')
                    if 'log4j' in content:
                        technologies.append('Log4j2')

                except Exception:
                    pass

        except Exception as e:
            logger.debug(f"检测技术栈失败: {str(e)}")

        return technologies

    async def _check_component_vulnerabilities(
        self,
        service_url: str,
        technologies: List[str]
    ) -> List[Dict[str, Any]]:
        """检测组件漏洞

        检测: SpringBoot Actuator, FastJSON, Log4j2等
        """
        vulnerabilities = []

        try:
            # 检测SpringBoot Actuator
            if 'SpringBoot' in technologies or 'Java' in technologies:
                actuator_vulns = await self._check_actuator_endpoints(service_url)
                vulnerabilities.extend(actuator_vulns)

            # TODO: 添加更多组件漏洞检测
            # - FastJSON 反序列化
            # - Log4j2 RCE
            # - 等等

        except Exception as e:
            logger.error(f"检测组件漏洞失败: {str(e)}")

        return vulnerabilities

    async def _check_actuator_endpoints(self, service_url: str) -> List[Dict[str, Any]]:
        """检测SpringBoot Actuator端点"""
        vulnerabilities = []

        actuator_paths = [
            '/actuator',
            '/actuator/health',
            '/actuator/info',
            '/actuator/env',
            '/actuator/beans',
            '/actuator/metrics',
            '/actuator/mappings',
        ]

        try:
            # ✅ 安全修复：验证基础URL安全性
            try:
                url_validator.validate(service_url)
            except URLValidationError as e:
                logger.warning(f"Blocked unsafe service URL for actuator check: {service_url}")
                return []

            # ✅ 安全修复：开启SSL验证
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=True,  # 修改：开启SSL验证
                follow_redirects=True
            ) as client:
                headers = {"User-Agent": self.user_agent}

                for path in actuator_paths:
                    url = f"{service_url.rstrip('/')}{path}"

                    try:
                        response = await client.get(url, headers=headers)

                        if response.status_code == 200:
                            vulnerabilities.append({
                                "type": "SpringBoot Actuator Exposed",
                                "url": url,
                                "severity": "medium" if '/health' in path or '/info' in path else "high",
                                "description": f"SpringBoot Actuator endpoint exposed: {path}"
                            })

                    except Exception:
                        pass

        except Exception as e:
            logger.debug(f"检测Actuator端点失败: {str(e)}")

        return vulnerabilities

    async def check_unauthorized_access(
        self,
        apis: List[Dict[str, Any]],
        site_url: str
    ) -> List[Dict[str, Any]]:
        """检测API未授权访问 (传统过滤 + AI研判)"""
        issues = []

        try:
            # 第一层过滤: 排除404接口 (传统代码)
            logger.info("过滤404接口")
            valid_apis = await self._filter_404_apis(apis)

            logger.info(f"有效API数量: {len(valid_apis)}")

            # AI研判 (如果启用)
            if self.use_ai:
                # 1. 站点定性
                site_description = await self._ai_analyze_site(site_url)

                # 2. 接口登录分析 + 3. 公共接口分析
                for api in valid_apis[:50]:  # 限制数量，避免过多请求
                    requires_login = await self._ai_check_requires_login(api)

                    if not requires_login:
                        is_public = await self._ai_check_is_public_api(
                            api,
                            site_description
                        )

                        if not is_public:
                            # 未授权访问问题
                            issues.append({
                                "type": "unauthorized_access",
                                "severity": "high",
                                "title": f"API未授权访问: {api['full_url']}",
                                "description": "该API无需登录即可访问，且不是公共接口",
                                "target_url": api['full_url'],
                                "evidence": {
                                    "api_path": api['api_path'],
                                    "requires_login": False,
                                    "is_public": False
                                }
                            })

        except Exception as e:
            logger.error(f"检测未授权访问失败: {str(e)}")

        return issues

    async def _filter_404_apis(self, apis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤404接口（并发优化版本）"""
        valid_apis = []

        try:
            # ✅ 性能优化：使用并发请求，限制并发数量
            max_concurrent = self.config.get('max_concurrent_requests', 10)
            semaphore = asyncio.Semaphore(max_concurrent)

            # ✅ 安全修复：开启SSL验证
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=True,  # 修改：开启SSL验证
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
            ) as client:
                headers = {"User-Agent": self.user_agent}

                async def check_single_api(api: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                    """检查单个API"""
                    async with semaphore:
                        # ✅ 安全修复：验证每个API的URL安全性
                        try:
                            url_validator.validate(api['full_url'])
                        except URLValidationError as e:
                            logger.warning(f"Skipped unsafe API URL: {api['full_url']}, reason: {str(e)}")
                            return None

                        try:
                            response = await client.get(
                                api['full_url'],
                                headers=headers
                            )

                            # 记录状态码
                            api['status_code'] = response.status_code
                            api['response_size'] = len(response.content)

                            if response.status_code != 404:
                                return api

                        except Exception as e:
                            logger.debug(f"API check failed: {api['full_url']}, error: {str(e)}")
                            pass

                        # 小延迟避免请求过快
                        await asyncio.sleep(0.05)
                        return None

                # ✅ 性能优化：并发执行所有检查
                tasks = [check_single_api(api) for api in apis]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 收集有效的API
                for result in results:
                    if result and not isinstance(result, Exception):
                        valid_apis.append(result)

                logger.info(f"API filtering completed: {len(valid_apis)}/{len(apis)} valid APIs")

        except Exception as e:
            logger.error(f"过滤404接口失败: {str(e)}")

        return valid_apis

    async def _ai_analyze_site(self, site_url: str) -> str:
        """AI分析站点定性"""
        # TODO: 集成实际的AI服务
        return "企业内部管理系统"

    async def _ai_check_requires_login(self, api: Dict[str, Any]) -> bool:
        """AI判断接口是否需要登录"""
        # TODO: 集成实际的AI服务
        # 简单判断: 状态码401/403需要登录
        status_code = api.get('status_code', 200)
        return status_code in [401, 403]

    async def _ai_check_is_public_api(
        self,
        api: Dict[str, Any],
        site_description: str
    ) -> bool:
        """AI判断是否为公共接口"""
        # TODO: 集成实际的AI服务
        # 简单判断: 包含public/common等关键字
        api_path = api.get('api_path', '').lower()
        return any(kw in api_path for kw in ['public', 'common', 'health', 'ping'])

    async def check_sensitive_information(
        self,
        js_resources: List[Dict[str, Any]],
        apis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """检测敏感信息泄露 (传统正则 + AI)"""
        issues = []

        try:
            # 检测JS文件中的敏感信息
            for js_file in js_resources:
                content = js_file.get('content', '')
                if not content:
                    continue

                sensitive_data = await self._match_sensitive_patterns(content)

                if sensitive_data:
                    issues.append({
                        "type": "sensitive_data_leak",
                        "severity": "high",
                        "title": f"JS文件敏感信息泄露: {js_file['url']}",
                        "description": "JS文件中包含敏感信息",
                        "target_url": js_file['url'],
                        "evidence": {
                            "sensitive_data": sensitive_data
                        }
                    })

            # 检测API响应中的敏感信息
            for api in apis[:50]:  # 限制数量
                if 'response_body' in api and api['response_body']:
                    sensitive_data = await self._match_sensitive_patterns(
                        api['response_body']
                    )

                    if sensitive_data:
                        issues.append({
                            "type": "sensitive_data_leak",
                            "severity": "high",
                            "title": f"API响应敏感信息泄露: {api['full_url']}",
                            "description": "API响应中包含敏感信息",
                            "target_url": api['full_url'],
                            "evidence": {
                                "sensitive_data": sensitive_data
                            }
                        })

        except Exception as e:
            logger.error(f"检测敏感信息失败: {str(e)}")

        return issues

    async def _match_sensitive_patterns(self, content: str) -> List[Dict[str, Any]]:
        """匹配敏感信息模式 (传统正则)"""
        sensitive_data = []

        patterns = {
            "accesskey": r'(?i)access[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9]{20,})["\']',
            "secretkey": r'(?i)secret[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9]{20,})["\']',
            "password": r'(?i)password["\']?\s*[:=]\s*["\']([^"\']{6,})["\']',
            "api_key": r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9]{20,})["\']',
            "token": r'(?i)token["\']?\s*[:=]\s*["\']([a-zA-Z0-9._-]{20,})["\']',
            "phone": r'1[3-9]\d{9}',
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "id_card": r'\d{17}[\dxX]',
        }

        for data_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                sensitive_data.append({
                    "type": data_type,
                    "count": len(matches),
                    "samples": matches[:3]  # 只保留前3个样本
                })

        return sensitive_data

    def _calculate_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """计算统计信息"""
        statistics = {
            "total_js_files": len(result.get("js_resources", [])),
            "total_apis": len(result.get("apis", [])),
            "total_microservices": len(result.get("microservices", [])),
            "total_issues": len(result.get("security_issues", [])),
            "issues_by_type": {},
            "issues_by_severity": {}
        }

        # 按类型统计
        for issue in result.get("security_issues", []):
            issue_type = issue.get("type", "unknown")
            statistics["issues_by_type"][issue_type] = \
                statistics["issues_by_type"].get(issue_type, 0) + 1

            severity = issue.get("severity", "info")
            statistics["issues_by_severity"][severity] = \
                statistics["issues_by_severity"].get(severity, 0) + 1

        return statistics
