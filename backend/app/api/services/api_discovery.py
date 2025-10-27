import asyncio
import re
import json
from typing import List, Dict, Any, Set, Optional, Tuple
from urllib.parse import urlparse, urljoin
from app.core.logging import get_logger

logger = get_logger(__name__)


class APIDiscoveryService:
    """API发现服务

    实现文章中的"全面发现动态API接口"功能
    使用 "传统代码 + AI协同" 的方式

    API分层架构:
    完整API = 基础URL + 基础API路径 + API路径
    例: https://xxx.com + /api + /user/getInfo
    """

    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai
        # 基础API路径的常见关键字
        self.base_api_keywords = [
            'api', 'v1', 'v2', 'v3', 'rest', 'service',
            'gateway', 'backend', 'server'
        ]

    async def discover_apis(
        self,
        js_contents: List[Dict[str, Any]],
        target_url: str
    ) -> List[Dict[str, Any]]:
        """从JS文件中发现API接口

        Args:
            js_contents: JS文件内容列表 [{url, content, ...}, ...]
            target_url: 目标URL

        Returns:
            发现的API列表
        """
        try:
            logger.info(f"开始API发现，JS文件数: {len(js_contents)}")

            all_apis = []
            discovered_apis = set()

            # 解析目标URL
            parsed_url = urlparse(target_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            for js_file in js_contents:
                content = js_file.get('content', '')
                if not content:
                    continue

                logger.debug(f"分析JS文件: {js_file.get('url', 'unknown')}")

                # 1. 提取基础URL (传统代码实现)
                base_urls = await self._extract_base_urls(content, base_url)

                # 2. 提取基础API路径 (传统代码 + AI)
                base_api_paths = await self._extract_base_api_paths(content, base_urls)

                # 3. 提取API路径 (传统代码 + AI)
                api_paths = await self._extract_api_paths(content)

                # 4. 组合生成完整API
                apis = await self._combine_api_components(
                    base_urls,
                    base_api_paths,
                    api_paths
                )

                for api in apis:
                    full_url = api['full_url']
                    if full_url not in discovered_apis:
                        discovered_apis.add(full_url)
                        api['source_js'] = js_file.get('url', 'unknown')
                        all_apis.append(api)

            logger.info(f"API发现完成，共发现 {len(all_apis)} 个API")
            return all_apis

        except Exception as e:
            logger.error(f"API发现失败: {str(e)}")
            return []

    async def _extract_base_urls(
        self,
        content: str,
        default_base_url: str
    ) -> List[str]:
        """提取基础URL (传统代码实现)

        从JS代码中提取基础域名URL
        """
        base_urls = set()
        base_urls.add(default_base_url)

        try:
            # 方法1: 提取完整URL中的基础部分
            # 匹配: https://xxx.com
            pattern = r'https?://[a-zA-Z0-9.-]+(?::\d+)?'
            matches = re.findall(pattern, content)

            for match in matches:
                base_urls.add(match)

            # 方法2: 提取配置中的baseURL
            # 匹配: baseURL: 'https://api.example.com'
            patterns = [
                r'baseURL\s*[:=]\s*["\']([^"\']+)["\']',
                r'BASE_URL\s*[:=]\s*["\']([^"\']+)["\']',
                r'API_URL\s*[:=]\s*["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.startswith('http'):
                        parsed = urlparse(match)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        base_urls.add(base_url)

        except Exception as e:
            logger.error(f"提取基础URL失败: {str(e)}")

        return list(base_urls)

    async def _extract_base_api_paths(
        self,
        content: str,
        base_urls: List[str]
    ) -> List[str]:
        """提取基础API路径 (传统代码 + AI)

        例如: /api, /v1, /api/v1
        """
        base_api_paths = set()
        base_api_paths.add('')  # 空路径也是一种可能

        try:
            # 方法1: 关键字匹配 (传统代码)
            for keyword in self.base_api_keywords:
                # 匹配: '/api', "/api", '/api/v1'
                patterns = [
                    rf'["\']/({\|'.join(self.base_api_keywords)})[/"\']',
                    rf'["\']/({\|'.join(self.base_api_keywords)})/[a-z0-9]+["\']',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]
                        path = f"/{match}" if not match.startswith('/') else match
                        base_api_paths.add(path)

            # 方法2: 从完整API中提取公共前缀
            all_paths = self._extract_all_paths(content)
            common_prefixes = self._find_common_prefixes(all_paths)
            base_api_paths.update(common_prefixes)

            # 方法3: AI分析 (如果启用)
            if self.use_ai:
                ai_base_paths = await self._ai_extract_base_api_paths(content)
                base_api_paths.update(ai_base_paths)

        except Exception as e:
            logger.error(f"提取基础API路径失败: {str(e)}")

        return list(base_api_paths)

    async def _extract_api_paths(self, content: str) -> List[str]:
        """提取API路径 (传统代码 + AI)

        例如: /user/getInfo, /admin/users
        """
        api_paths = set()

        try:
            # 方法1: 正则表达式提取 (传统代码)
            # 匹配常见API路径模式
            patterns = [
                # 匹配: '/user/info', "/admin/users"
                r'["\'](/[a-zA-Z0-9/_-]+)["\']',

                # 匹配: get('/api/users')
                r'(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',

                # 匹配: axios.get('/api/users')
                r'axios\.\w+\s*\(\s*["\']([^"\']+)["\']',

                # 匹配: fetch('/api/users')
                r'fetch\s*\(\s*["\']([^"\']+)["\']',

                # 匹配: url: '/api/users'
                r'url\s*:\s*["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]

                    # 过滤: 必须以/开头，包含合理字符
                    if match and match.startswith('/') and self._is_valid_api_path(match):
                        api_paths.add(match)

            # 方法2: AI分析动态拼接的API (如果启用)
            if self.use_ai:
                ai_api_paths = await self._ai_extract_api_paths(content)
                api_paths.update(ai_api_paths)

        except Exception as e:
            logger.error(f"提取API路径失败: {str(e)}")

        return list(api_paths)

    def _extract_all_paths(self, content: str) -> List[str]:
        """提取所有可能的路径"""
        paths = []
        pattern = r'["\'](/[a-zA-Z0-9/_-]+)["\']'
        matches = re.findall(pattern, content)

        for match in matches:
            if self._is_valid_api_path(match):
                paths.append(match)

        return paths

    def _find_common_prefixes(self, paths: List[str]) -> Set[str]:
        """查找路径的公共前缀

        例如: ['/api/user/info', '/api/admin/users'] -> {'/api'}
        """
        if not paths or len(paths) < 2:
            return set()

        common_prefixes = set()

        # 统计路径片段
        segment_counts = {}
        for path in paths:
            segments = path.split('/')
            for i in range(1, len(segments)):
                prefix = '/'.join(segments[:i+1])
                if prefix:
                    segment_counts[prefix] = segment_counts.get(prefix, 0) + 1

        # 选择出现次数多的前缀
        threshold = max(2, len(paths) * 0.3)  # 至少出现30%
        for prefix, count in segment_counts.items():
            if count >= threshold:
                # 检查是否包含API关键字
                if any(keyword in prefix.lower() for keyword in self.base_api_keywords):
                    common_prefixes.add(prefix)

        return common_prefixes

    def _is_valid_api_path(self, path: str) -> bool:
        """检查是否为有效的API路径"""
        if not path or not path.startswith('/'):
            return False

        # 排除静态资源
        invalid_extensions = [
            '.js', '.css', '.html', '.png', '.jpg', '.jpeg',
            '.gif', '.svg', '.ico', '.woff', '.ttf', '.mp4'
        ]

        path_lower = path.lower()
        for ext in invalid_extensions:
            if path_lower.endswith(ext):
                return False

        # 排除明显不是API的路径
        invalid_patterns = [
            'assets', 'static', 'public', 'images',
            'css', 'fonts', 'vendor'
        ]

        for pattern in invalid_patterns:
            if pattern in path_lower and not any(kw in path_lower for kw in self.base_api_keywords):
                return False

        # 必须包含字母
        if not re.search(r'[a-zA-Z]', path):
            return False

        return True

    async def _combine_api_components(
        self,
        base_urls: List[str],
        base_api_paths: List[str],
        api_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """组合API组件生成完整API

        完整API = 基础URL + 基础API路径 + API路径
        """
        apis = []

        for base_url in base_urls:
            for base_api_path in base_api_paths:
                for api_path in api_paths:
                    # 组合完整URL
                    full_url = self._build_full_url(base_url, base_api_path, api_path)

                    # 提取服务路径 (用于微服务识别)
                    service_path = self._extract_service_path(api_path)

                    api_info = {
                        "base_url": base_url,
                        "base_api_path": base_api_path,
                        "service_path": service_path,
                        "api_path": api_path,
                        "full_url": full_url,
                        "http_method": "GET",  # 默认GET，实际使用时可能需要多种方法
                        "discovery_method": "regex" if not self.use_ai else "regex+ai"
                    }

                    apis.append(api_info)

        return apis

    def _build_full_url(
        self,
        base_url: str,
        base_api_path: str,
        api_path: str
    ) -> str:
        """构建完整URL"""
        # 移除重复的斜杠
        parts = [base_url.rstrip('/')]

        if base_api_path:
            parts.append(base_api_path.strip('/'))

        parts.append(api_path.lstrip('/'))

        return '/'.join(parts)

    def _extract_service_path(self, api_path: str) -> Optional[str]:
        """从API路径中提取服务路径

        例如: /user/getInfo -> /user
        """
        if not api_path or api_path == '/':
            return None

        segments = api_path.strip('/').split('/')
        if segments:
            return f"/{segments[0]}"

        return None

    # ============ AI辅助方法 (占位符，需要集成实际的AI服务) ============

    async def _ai_extract_base_api_paths(self, content: str) -> List[str]:
        """AI提取基础API路径

        这里需要调用实际的AI服务 (如Claude API)
        Prompt示例:
        "请分析以下JavaScript代码，提取其中的基础API路径（如/api, /v1等）。
        完整API的构成逻辑: 基础URL + 基础API路径 + API路径
        请只返回基础API路径部分，以JSON数组格式返回。"
        """
        # TODO: 集成实际的AI服务
        # 暂时返回空列表
        return []

    async def _ai_extract_api_paths(self, content: str) -> List[str]:
        """AI提取API路径

        这里需要调用实际的AI服务
        Prompt示例:
        "请分析以下JavaScript代码，提取其中的API路径。
        特别注意动态拼接的API路径，例如:
        - const api = baseUrl + '/user/' + userId
        - '${API_PREFIX}/admin/users'
        请返回所有可能的API路径，以JSON数组格式返回。"
        """
        # TODO: 集成实际的AI服务

        # 简单实现：提取模板字符串和字符串拼接
        ai_paths = set()

        try:
            # 匹配模板字符串: `${xxx}/api/users`
            template_pattern = r'`[^`]*(\$\{[^}]+\})?([/a-zA-Z0-9_-]+)[^`]*`'
            matches = re.findall(template_pattern, content)
            for match in matches:
                if isinstance(match, tuple) and len(match) > 1:
                    path = match[1]
                    if path and path.startswith('/') and self._is_valid_api_path(path):
                        ai_paths.add(path)

            # 匹配字符串拼接: baseUrl + '/api/users'
            concat_pattern = r'\+\s*["\']([/a-zA-Z0-9/_-]+)["\']'
            matches = re.findall(concat_pattern, content)
            for match in matches:
                if match and match.startswith('/') and self._is_valid_api_path(match):
                    ai_paths.add(match)

        except Exception as e:
            logger.error(f"AI提取API路径失败: {str(e)}")

        return list(ai_paths)
