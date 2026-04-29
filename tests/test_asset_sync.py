#!/usr/bin/env python3
"""
测试资产同步功能
"""

import os
from openspade.scheduler.jobs.asset_sync_job import sync_assets, get_sync_status
from openspade.db.database_extension import get_assets, get_asset_statistics, init_capital_pool_tables


def test_asset_sync():
    print("=== 测试资产同步功能 ===")

    # 初始化数据库表
    init_capital_pool_tables()

    # 获取API密钥（如果环境变量中有）
    api_key = os.environ.get('BINANCE_API_KEY')
    api_secret = os.environ.get('BINANCE_API_SECRET')

    use_mock = not api_key or not api_secret

    if use_mock:
        print("警告：未设置BINANCE_API_KEY和BINANCE_API_SECRET环境变量")
        print("将使用模拟数据进行测试")

        mock_sync_result = {
            'sync_type': 'full',
            'status': 'success',
            'start_time': '2026-04-19T00:00:00',
            'end_time': '2026-04-19T00:00:01',
            'records_synced': 2,
            'error_message': None,
        }
    else:
        print("使用真实API密钥进行测试")

    # 测试同步功能
    print("\n1. 测试同步功能")
    if use_mock:
        result = mock_sync_result
    else:
        result = sync_assets()
    print(f"同步结果: {result}")

    # 测试获取资产
    print("\n2. 测试获取资产")
    assets = get_assets()
    print(f"当前资产数量: {len(assets)}")
    for asset in assets:
        print(f"  - {asset['asset_type']}: {asset['asset']} = {asset['total']}")

    # 测试获取资产统计
    print("\n3. 测试获取资产统计")
    stats = get_asset_statistics()
    print(f"资产统计: {stats}")

    # 测试同步状态
    print("\n4. 测试同步状态")
    status = get_sync_status()
    print(f"同步状态: {status}")

    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_asset_sync()
