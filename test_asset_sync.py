#!/usr/bin/env python3
"""
测试资产同步功能
"""

import sys
import os
from asset_sync import AssetSync
from database_extension import get_assets, get_asset_statistics, init_capital_pool_tables


def test_asset_sync():
    print("=== 测试资产同步功能 ===")
    
    # 初始化数据库表
    init_capital_pool_tables()
    
    # 获取API密钥（如果环境变量中有）
    api_key = "e5UeIzDnW2OpuW2BMfFtppfb94zVcKdoPgwah1icSPE9whEScIDtDqcXDcipiGLJ"
    api_secret = "4sBd9RYcigt5tmtMiC1pcCVZMbEdiCnAfslTQ8nlEA901WFVwVWTjgfv53dxwH6j"
    
    if not api_key or not api_secret:
        print("警告：未设置BINANCE_API_KEY和BINANCE_API_SECRET环境变量")
        print("将使用模拟数据进行测试")
        
        # 创建一个模拟的AssetSync类
        class MockAssetSync:
            def sync_assets(self):
                print("模拟同步资产...")
                return {
                    'sync_type': 'full',
                    'status': 'success',
                    'start_time': '2026-04-19T00:00:00',
                    'end_time': '2026-04-19T00:00:01',
                    'records_synced': 2,
                    'error_message': None
                }
            
            def get_sync_status(self):
                return {
                    'auto_sync_running': False,
                    'sync_interval': 300,
                    'asset_statistics': {
                        'total_assets': 0,
                        'spot_total': 0,
                        'futures_total': 0,
                        'total_portfolio': 0,
                        'successful_syncs_24h': 0
                    }
                }
        
        sync = MockAssetSync()
    else:
        print("使用真实API密钥进行测试")
        sync = AssetSync(api_key, api_secret)
    
    # 测试同步功能
    print("\n1. 测试同步功能")
    result = sync.sync_assets()
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
    status = sync.get_sync_status()
    print(f"同步状态: {status}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_asset_sync()
