import asyncio
import httpx
import re
import hashlib
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Set, Optional
from bs4 import BeautifulSoup
from app.core.logging import get_logger
from app.core.url_validator import url_validator, URLValidationError

logger = get_logger(__name__)


class JSExtractorService:
    """JS资源提取服务

    实现文章中的"适配主流前端技术并提取JS资源文件"功能
    """

    def __init__(self):
        self.timeout = 30
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    async def extract_js_resources(
        self,
        target_url: str,
        max_files: int = 100
    ) -> List[Dict[str, Any]]:
        """提取目标URL的所有JS资源

        Args:
            target_url: 目标网站URL
            max_files: 最大提取文件数

        Returns:
            JS资源列表
        """
        try:
            logger.info(f"开始提取JS资源: {target_url}")

            js_resources = []
            js_urls = set()

            # 1. 获取首页HTML
            html_content = await self._fetch_html(target_url)
            if not html_content:
                logger.warning(f"无法获取HTML内容: {target_url}")
                return []

            # 2. 提取静态JS资源 (传统代码实现)
            static_js = await self._extract_static_js(html_content, target_url)
            for js_url in static_js:
                if js_url not in js_urls and len(js_urls) < max_files:
                    js_urls.add(js_url)

            # 3. 提取动态加载的JS资源 (Vue, React, Angular等)
            dynamic_js = await self._extract_dynamic_js(html_content, target_url)
            for js_url in dynamic_js:
                if js_url not in js_urls and len(js_urls) < max_files:
                    js_urls.add(js_url)

            # 4. 解析Webpack等打包工具的资源路径
            webpack_js = await self._extract_webpack_resources(html_content, target_url)
            for js_url in webpack_js:
                if js_url not in js_urls and len(js_urls) < max_files:
                    js_urls.add(js_url)

            # 5. 获取JS文件详细信息
            logger.info(f"发现 {len(js_urls)} 个JS资源")
            for js_url in js_urls:
                js_info = await self._get_js_file_info(js_url)
                if js_info:
                    js_resources.append(js_info)

            logger.info(f"成功提取 {len(js_resources)} 个JS资源")
            return js_resources

        except Exception as e:
            logger.error(f"提取JS资源失败: {str(e)}")
            return []

    async def _fetch_html(self, url: str) -> Optional[str]:
        """获取HTML内容"""
        try:
            # ✅ 安全修复：验证URL安全性，防止SSRF攻击
            try:
                url_validator.validate(url)
            except URLValidationError as e:
                logger.warning(f"Blocked unsafe URL: {url}, reason: {str(e)}")
                return None

            # ✅ 安全修复：开启SSL证书验证，防止中间人攻击
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=True,  # 修改：开启SSL验证
                follow_redirects=True
            ) as client:
                headers = {"User-Agent": self.user_agent}
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.text

        except Exception as e:
            logger.error(f"获取HTML失败 {url}: {str(e)}")

        return None

    async def _extract_static_js(
        self,
        html_content: str,
        base_url: str
    ) -> List[str]:
        """提取静态JS资源 (传统方法)

        使用正则表达式和BeautifulSoup提取<script>标签中的JS文件
        """
        js_urls = []

        try:
            # 使用BeautifulSoup解析
            soup = BeautifulSoup(html_content, 'html.parser')

            # 提取<script src="">标签
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if self._is_js_url(full_url):
                        js_urls.append(full_url)

            # 使用正则表达式作为补充
            # 匹配: <script src="xxx.js">
            pattern = r'<script[^>]*src=["\']([^"\']+)["\']'
            matches = re.findall(pattern, html_content, re.IGNORECASE)

            for match in matches:
                full_url = urljoin(base_url, match)
                if self._is_js_url(full_url) and full_url not in js_urls:
                    js_urls.append(full_url)

            logger.debug(f"提取到 {len(js_urls)} 个静态JS资源")

        except Exception as e:
            logger.error(f"提取静态JS失败: {str(e)}")

        return js_urls

    async def _extract_dynamic_js(
        self,
        html_content: str,
        base_url: str
    ) -> List[str]:
        """提取动态加载的JS资源

        主要针对Vue、React、Angular等现代前端框架
        """
        js_urls = []

        try:
            # Vue.js 特征: vue-router, vuex等
            vue_patterns = [
                r'src:\s*["\']([^"\']+\.js)["\']',
                r'component:\s*["\']([^"\']+)["\']',
            ]

            # React 特征: webpack chunk
            react_patterns = [
                r'__webpack_require__[^"\']+["\']([^"\']+\.js)["\']',
                r'chunkId[^"\']+["\']([^"\']+)["\']',
            ]

            # Angular 特征: lazy loading
            angular_patterns = [
                r'loadChildren:[^"\']+["\']([^"\']+)["\']',
            ]

            all_patterns = vue_patterns + react_patterns + angular_patterns

            for pattern in all_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    full_url = urljoin(base_url, match)
                    if self._is_js_url(full_url) and full_url not in js_urls:
                        js_urls.append(full_url)

            logger.debug(f"提取到 {len(js_urls)} 个动态JS资源")

        except Exception as e:
            logger.error(f"提取动态JS失败: {str(e)}")

        return js_urls

    async def _extract_webpack_resources(
        self,
        html_content: str,
        base_url: str
    ) -> List[str]:
        """解析Webpack打包后的资源路径

        参考文章示例: 将类似 "chunk-2d0e5357":"d48c529f" 解析为
        /static/js/chunk-2d0e5357.d48c529f.js
        """
        js_urls = []

        try:
            # 模式1: {chunk-id: hash} -> /path/chunk-id.hash.js
            # 例如: {"chunk-2d0e5357":"d48c529f"}
            pattern1 = r'["\']?(chunk-[a-f0-9]+)["\']?\s*:\s*["\']([a-f0-9]+)["\']'
            matches = re.findall(pattern1, html_content, re.IGNORECASE)

            for chunk_id, chunk_hash in matches:
                # 尝试多种可能的路径模式
                possible_paths = [
                    f"/static/js/{chunk_id}.{chunk_hash}.js",
                    f"/js/{chunk_id}.{chunk_hash}.js",
                    f"/assets/{chunk_id}.{chunk_hash}.js",
                    f"/{chunk_id}.{chunk_hash}.js",
                ]

                for path in possible_paths:
                    full_url = urljoin(base_url, path)
                    if full_url not in js_urls:
                        js_urls.append(full_url)
                        break  # 只添加第一个可能的路径

            # 模式2: 直接提取chunk文件名
            # 例如: chunk-vendors.a1b2c3d4.js
            pattern2 = r'(chunk-[a-z0-9-]+\.[a-f0-9]+\.js)'
            matches = re.findall(pattern2, html_content, re.IGNORECASE)

            for filename in matches:
                possible_paths = [
                    f"/static/js/{filename}",
                    f"/js/{filename}",
                    f"/assets/{filename}",
                ]

                for path in possible_paths:
                    full_url = urljoin(base_url, path)
                    if full_url not in js_urls:
                        js_urls.append(full_url)
                        break

            # 模式3: app.js, vendor.js等主文件
            pattern3 = r'["\']([a-z0-9-]+\.[a-f0-9]{8,}\.js)["\']'
            matches = re.findall(pattern3, html_content, re.IGNORECASE)

            for filename in matches:
                if any(name in filename.lower() for name in ['app', 'vendor', 'main', 'bundle']):
                    possible_paths = [
                        f"/static/js/{filename}",
                        f"/js/{filename}",
                        f"/assets/{filename}",
                    ]

                    for path in possible_paths:
                        full_url = urljoin(base_url, path)
                        if full_url not in js_urls:
                            js_urls.append(full_url)
                            break

            logger.debug(f"提取到 {len(js_urls)} 个Webpack资源")

        except Exception as e:
            logger.error(f"提取Webpack资源失败: {str(e)}")

        return js_urls

    async def _get_js_file_info(self, url: str) -> Optional[Dict[str, Any]]:
        """获取JS文件详细信息"""
        try:
            # ✅ 安全修复：验证URL安全性
            try:
                url_validator.validate(url)
            except URLValidationError as e:
                logger.warning(f"Blocked unsafe JS URL: {url}, reason: {str(e)}")
                return None

            # ✅ 安全修复：开启SSL验证
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=True,  # 修改：开启SSL验证
                follow_redirects=True
            ) as client:
                headers = {"User-Agent": self.user_agent}

                # 先HEAD请求检查文件大小
                try:
                    head_response = await client.head(url, headers=headers)
                    content_length = head_response.headers.get('content-length')

                    if content_length and int(content_length) > self.max_file_size:
                        logger.warning(f"JS文件过大，跳过: {url}")
                        return None

                except Exception:
                    # HEAD请求失败，继续尝试GET
                    pass

                # GET请求获取内容
                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    return None

                content = response.text
                file_size = len(content.encode('utf-8'))

                # 计算文件hash
                content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

                # 提取文件名
                parsed_url = urlparse(url)
                file_name = parsed_url.path.split('/')[-1] if parsed_url.path else 'unknown.js'

                # 获取base_url
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                return {
                    "url": url,
                    "base_url": base_url,
                    "file_name": file_name,
                    "file_size": file_size,
                    "content_hash": content_hash,
                    "content": content,  # 内容将用于后续API提取
                    "extraction_method": self._detect_extraction_method(url)
                }

        except Exception as e:
            logger.debug(f"获取JS文件信息失败 {url}: {str(e)}")
            return None

    def _is_js_url(self, url: str) -> bool:
        """检查URL是否为JS文件"""
        if not url:
            return False

        url_lower = url.lower()

        # 检查扩展名
        if url_lower.endswith('.js'):
            return True

        # 检查MIME类型关键字
        if 'javascript' in url_lower or 'js' in url_lower:
            return True

        # 排除明显不是JS的URL
        exclude_patterns = [
            '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.pdf'
        ]

        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False

        return False

    def _detect_extraction_method(self, url: str) -> str:
        """检测提取方法"""
        url_lower = url.lower()

        if 'chunk-' in url_lower or 'vendor' in url_lower:
            return "webpack"
        elif 'vue' in url_lower:
            return "vue"
        elif 'react' in url_lower:
            return "react"
        elif 'angular' in url_lower:
            return "angular"
        else:
            return "static"

    async def analyze_js_content(self, content: str) -> Dict[str, Any]:
        """分析JS内容 (简单分析，详细分析在API发现服务中)

        Args:
            content: JS文件内容

        Returns:
            分析结果
        """
        analysis = {
            "has_api_patterns": False,
            "has_base_path_patterns": False,
            "has_sensitive_patterns": False,
            "size": len(content)
        }

        try:
            # 检查是否包含API模式
            api_patterns = [
                r'["\'][/a-zA-Z0-9_-]+/api[/a-zA-Z0-9_-]*["\']',
                r'axios\.',
                r'fetch\(',
                r'\.get\(',
                r'\.post\(',
                r'http[s]?://',
            ]

            for pattern in api_patterns:
                if re.search(pattern, content):
                    analysis["has_api_patterns"] = True
                    break

            # 检查是否包含基础路径模式
            base_path_patterns = [
                r'baseURL\s*[:=]',
                r'API_BASE',
                r'apiPrefix',
            ]

            for pattern in base_path_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    analysis["has_base_path_patterns"] = True
                    break

            # 检查是否包含敏感信息模式
            sensitive_patterns = [
                r'accesskey',
                r'secretkey',
                r'password',
                r'token',
                r'apikey',
            ]

            for pattern in sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    analysis["has_sensitive_patterns"] = True
                    break

        except Exception as e:
            logger.error(f"分析JS内容失败: {str(e)}")

        return analysis
