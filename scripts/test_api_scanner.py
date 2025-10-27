#!/usr/bin/env python3
"""
API安全扫描器测试脚本

使用方法:
    python scripts/test_api_scanner.py https://example.com
"""

import asyncio
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.api.services.api_security_scanner import APISecurityScanner


async def test_api_scanner(target_url: str):
    """测试API安全扫描器"""

    print("=" * 80)
    print(f"API安全扫描测试")
    print(f"目标URL: {target_url}")
    print("=" * 80)
    print()

    # 创建扫描器
    scanner = APISecurityScanner(config={'use_ai': False})

    # 配置扫描
    scan_config = {
        "enable_js_extraction": True,
        "enable_api_discovery": True,
        "enable_microservice_detection": True,
        "enable_unauthorized_check": False,  # 关闭以加快测试
        "enable_sensitive_info_check": True,
        "max_js_files": 20,  # 限制数量以加快测试
    }

    print("扫描配置:")
    for key, value in scan_config.items():
        print(f"  - {key}: {value}")
    print()

    # 执行扫描
    print("开始扫描...")
    result = await scanner.scan(target_url, scan_config)

    # 显示结果
    print("\n" + "=" * 80)
    print("扫描结果")
    print("=" * 80)

    print(f"\n状态: {result['status']}")
    print(f"开始时间: {result['start_time']}")
    if 'end_time' in result:
        print(f"结束时间: {result['end_time']}")

    # 统计信息
    stats = result.get('statistics', {})
    print("\n📊 统计信息:")
    print(f"  - JS文件数: {stats.get('total_js_files', 0)}")
    print(f"  - API数量: {stats.get('total_apis', 0)}")
    print(f"  - 微服务数: {stats.get('total_microservices', 0)}")
    print(f"  - 安全问题: {stats.get('total_issues', 0)}")

    # JS资源
    js_resources = result.get('js_resources', [])
    if js_resources:
        print("\n📦 JS资源 (前5个):")
        for i, js in enumerate(js_resources[:5], 1):
            print(f"  {i}. {js.get('file_name', 'unknown')}")
            print(f"     URL: {js.get('url', 'N/A')}")
            print(f"     大小: {js.get('file_size', 0)} bytes")
            print(f"     提取方法: {js.get('extraction_method', 'unknown')}")

    # API列表
    apis = result.get('apis', [])
    if apis:
        print(f"\n🔌 API接口 (前10个，共{len(apis)}个):")
        for i, api in enumerate(apis[:10], 1):
            print(f"  {i}. {api.get('full_url', 'N/A')}")
            print(f"     分层: {api.get('base_url', '')}{api.get('base_api_path', '')}")
            print(f"           + {api.get('service_path', '')} + {api.get('api_path', '')}")

    # 微服务
    microservices = result.get('microservices', [])
    if microservices:
        print(f"\n🏗️  微服务 (共{len(microservices)}个):")
        for i, service in enumerate(microservices, 1):
            print(f"  {i}. {service.get('service_name', 'unknown')}")
            print(f"     路径: {service.get('service_full_path', 'N/A')}")
            print(f"     端点数: {service.get('total_endpoints', 0)}")
            if service.get('detected_technologies'):
                print(f"     技术栈: {', '.join(service['detected_technologies'])}")
            if service.get('has_vulnerabilities'):
                print(f"     ⚠️  存在漏洞: {len(service.get('vulnerability_details', []))}个")

    # 安全问题
    issues = result.get('security_issues', [])
    if issues:
        print(f"\n⚠️  安全问题 (共{len(issues)}个):")
        for i, issue in enumerate(issues[:10], 1):
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            emoji = severity_emoji.get(issue.get('severity', 'info'), '⚪')
            print(f"  {i}. {emoji} [{issue.get('severity', 'N/A').upper()}] {issue.get('title', 'N/A')}")
            print(f"     类型: {issue.get('type', 'N/A')}")
            print(f"     URL: {issue.get('target_url', 'N/A')}")

    # 保存详细结果
    output_file = "api_scan_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # 移除content字段以减小文件大小
        result_copy = result.copy()
        for js in result_copy.get('js_resources', []):
            if 'content' in js:
                del js['content']

        json.dump(result_copy, f, indent=2, ensure_ascii=False)

    print(f"\n详细结果已保存到: {output_file}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python scripts/test_api_scanner.py <target_url>")
        print("示例: python scripts/test_api_scanner.py https://example.com")
        sys.exit(1)

    target_url = sys.argv[1]

    # 运行测试
    asyncio.run(test_api_scanner(target_url))


if __name__ == "__main__":
    main()
