import json

# 从浏览器快照中提取下架信息
def extract_delisting_info():
    # 从快照中提取的下架公告信息
    delisting_announcements = [
        {
            "title": "币安合约将下架多个U本位永续合约（2026-04-28）",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安合约将下架多个U本位永续合约（2026-04-28 & 2026-04-29）",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安移除部分现货交易对的公告 - 2026-04-24",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安杠杆移除部分交易对的公告 - 2026-04-24",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安将下架 DEGO、DENT、TRU（2026-04-28）",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安移除部分现货交易对的公告 - 2026-04-17",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安杠杆及借币将下架BAR、PIVX、XVG（2026-04-17）",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安将下架UTK并支持其在币安Alpha的品牌升级及空投计划",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安将下架 BIFI、FIO、FUN、MDT、OXT、WAN（2026-04-23）",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        },
        {
            "title": "币安杠杆将于2026年04月10日下架WAN",
            "url": "https://www.binance.com/zh-CN/support/announcement/list/161"
        }
    ]
    
    return delisting_announcements

# 主函数
if __name__ == "__main__":
    print("正在提取币安下架信息...")
    announcements = extract_delisting_info()
    
    print(f"\n共收集到 {len(announcements)} 条下架信息：")
    print("-" * 80)
    
    for i, announcement in enumerate(announcements, 1):
        print(f"{i}. {announcement['title']}")
        print(f"   链接: {announcement['url']}")
        print("-" * 80)
    
    # 保存为JSON文件
    with open('binance_delisting_announcements.json', 'w', encoding='utf-8') as f:
        json.dump(announcements, f, ensure_ascii=False, indent=2)
    
    print("\n下架信息已保存到 binance_delisting_announcements.json 文件中。")