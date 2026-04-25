import requests
import json
import time
import random
from datetime import datetime


API_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
CATALOG_ID = 161  # 下架讯息
PAGE_SIZE = 20
MAX_RETRIES = 3
OUTPUT_FILE = "binance_delisting_announcements.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/zh-CN/support/announcement/list/161",
}


def fetch_page(session, page_no):
    """Fetch a single page of announcements with retry logic."""
    params = {
        "type": 1,
        "catalogId": CATALOG_ID,
        "pageNo": page_no,
        "pageSize": PAGE_SIZE,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(API_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != "000000" or not data.get("success"):
                print(f"  [!] API returned error on page {page_no}: {data.get('message', 'unknown')}")
                return None
            return data.get("data", {})
        except (requests.RequestException, ValueError) as e:
            wait = 2 ** attempt + random.random()
            print(f"  [!] Page {page_no} attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"      Retrying in {wait:.1f}s ...")
                time.sleep(wait)
    return None


def parse_articles(raw_articles):
    """Extract useful fields from raw API article list."""
    results = []
    for article in raw_articles:
        release_ts = article.get("releaseDate")
        release_date = (
            datetime.fromtimestamp(release_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
            if release_ts
            else ""
        )
        code = article.get("code", "")
        url = f"https://www.binance.com/zh-CN/support/announcement/detail/{code}" if code else ""
        results.append({
            "id": article.get("id"),
            "title": article.get("title", ""),
            "release_date": release_date,
            "url": url,
        })
    return results


def crawl_binance_delisting():
    """Fetch all delisting announcements via Binance CMS API with pagination."""
    session = requests.Session()
    all_articles = []
    page_no = 1

    print("正在通过 Binance CMS API 获取下架公告 ...")

    while True:
        print(f"  -> 正在获取第 {page_no} 页 ...")
        page_data = fetch_page(session, page_no)

        if page_data is None:
            print("  [!] 获取失败，停止翻页。")
            break

        catalogs = page_data.get("catalogs", [])
        if not catalogs:
            print("  [i] 未返回 catalog 数据，尝试从 articles 字段读取 ...")
            articles = page_data.get("articles", [])
        else:
            articles = catalogs[0].get("articles", [])

        if not articles:
            print(f"  [i] 第 {page_no} 页无数据，翻页结束。")
            break

        parsed = parse_articles(articles)
        all_articles.extend(parsed)
        print(f"      本页获取 {len(parsed)} 条，累计 {len(all_articles)} 条")

        total = catalogs[0].get("total", 0) if catalogs else page_data.get("total", 0)
        if total and len(all_articles) >= total:
            print(f"  [i] 已获取全部 {total} 条公告。")
            break

        page_no += 1
        delay = random.uniform(1.0, 2.0)
        time.sleep(delay)

    return all_articles


def main():
    announcements = crawl_binance_delisting()

    if not announcements:
        print("\n未获取到任何公告，请检查网络连接或 API 是否可用。")
        return

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(announcements, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"共获取 {len(announcements)} 条下架公告，已保存到 {OUTPUT_FILE}")
    print(f"{'=' * 70}")

    print("\n最新公告：")
    print("-" * 70)
    for i, item in enumerate(announcements[:10], 1):
        print(f"  {i}. [{item['release_date']}] {item['title']}")
        print(f"     {item['url']}")
    if len(announcements) > 10:
        print(f"  ... 还有 {len(announcements) - 10} 条历史公告，详见 JSON 文件")
    print("-" * 70)


if __name__ == "__main__":
    main()
