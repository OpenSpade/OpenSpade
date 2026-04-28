import requests
import json
import re
import time
import random
import argparse
import os
from datetime import datetime


LIST_API_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
DETAIL_API_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
CATALOG_ID = 161  # 下架讯息
PAGE_SIZE = 20
MAX_RETRIES = 5
OUTPUT_FILE = "../../binance_delisting_announcements.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/zh-CN/support/announcement/list/161",
}


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def _request_with_retry(session, method, url, max_retries=MAX_RETRIES, **kwargs):
    """Send a request with exponential-backoff retry and 429 handling."""
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 15)
    for attempt in range(1, max_retries + 1):
        try:
            resp = getattr(session, method)(url, **kwargs)
            if resp.status_code == 429:
                wait = min(10 + 5 * attempt + random.random() * 5, 60)
                print(f"  [!] 429 rate-limited, waiting {wait:.0f}s (attempt {attempt}/{max_retries}) ...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError:
            raise
        except (requests.RequestException, ValueError) as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt + random.random()
            print(f"  [!] attempt {attempt}/{max_retries} failed: {e}, retry in {wait:.1f}s")
            time.sleep(wait)
    return None


# ---------------------------------------------------------------------------
# List API – pagination
# ---------------------------------------------------------------------------

def fetch_page(session, page_no):
    """Fetch a single page of the announcement list."""
    params = {
        "type": 1,
        "catalogId": CATALOG_ID,
        "pageNo": page_no,
        "pageSize": PAGE_SIZE,
    }
    try:
        resp = _request_with_retry(session, "get", LIST_API_URL, params=params)
        if resp is None:
            return None
        data = resp.json()
        if data.get("code") != "000000" or not data.get("success"):
            print(f"  [!] API error on page {page_no}: {data.get('message', 'unknown')}")
            return None
        return data.get("data", {})
    except Exception as e:
        print(f"  [!] Failed to fetch page {page_no}: {e}")
        return None


def fetch_all_articles(session):
    """Paginate through the list API and return all article stubs."""
    all_articles = []
    page_no = 1
    print("正在获取公告列表 ...")

    while True:
        print(f"  -> 第 {page_no} 页 ...")
        page_data = fetch_page(session, page_no)
        if page_data is None:
            break

        catalogs = page_data.get("catalogs", [])
        articles = catalogs[0].get("articles", []) if catalogs else page_data.get("articles", [])
        if not articles:
            print(f"  [i] 第 {page_no} 页无数据，翻页结束。")
            break

        all_articles.extend(articles)
        print(f"      本页 {len(articles)} 条，累计 {len(all_articles)} 条")

        total = catalogs[0].get("total", 0) if catalogs else page_data.get("total", 0)
        if total and len(all_articles) >= total:
            print(f"  [i] 已获取全部 {total} 条。")
            break

        page_no += 1
        time.sleep(random.uniform(1.0, 2.0))

    return all_articles


# ---------------------------------------------------------------------------
# Detail API – article body
# ---------------------------------------------------------------------------

def fetch_article_detail(session, article_code):
    """Fetch the full body of a single article via the detail API."""
    try:
        resp = _request_with_retry(
            session, "get", DETAIL_API_URL,
            params={"articleCode": article_code},
        )
        if resp is None:
            return None
        data = resp.json()
        if data.get("code") != "000000":
            return None
        return data.get("data", {})
    except Exception:
        return None


def _extract_text_from_body(node):
    """Recursively extract plain text from the Binance body JSON tree."""
    if isinstance(node, str):
        return node
    parts = []
    if isinstance(node, dict):
        if "text" in node:
            parts.append(node["text"])
        for child in node.get("child", []):
            parts.append(_extract_text_from_body(child))
        tag = node.get("tag", "")
        if tag in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br"):
            parts.append("\n")
    elif isinstance(node, list):
        for item in node:
            parts.append(_extract_text_from_body(item))
    return "".join(parts)


def parse_body(raw_body):
    """Parse the body field (a JSON string) into plain text."""
    if not raw_body:
        return ""
    try:
        tree = json.loads(raw_body)
        text = _extract_text_from_body(tree)
        text = text.replace("\xa0", " ")
        text = text.replace("&nbsp;", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except (json.JSONDecodeError, TypeError):
        return raw_body


# ---------------------------------------------------------------------------
# Structured content extraction
# ---------------------------------------------------------------------------

# Date-time pattern: 2026-04-28 09:00 (UTC) or 2026-04-28 10:00 (UTC)
_DATETIME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*\(UTC\)")

# Trading pair pattern: XXX/YYY (allow digit-starting like 1INCH/BTC)
_PAIR_RE = re.compile(r"\b([A-Z0-9][A-Z0-9]{0,9}/[A-Z][A-Z0-9]{1,9})\b")

# Futures contract name: XXXUSDT, XXXUSD (allow short prefixes like AI, B3)
_CONTRACT_RE = re.compile(r"\b([A-Z0-9][A-Z0-9]{0,15}(?:USDT|USD|BUSD))\b")

_TICKER_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9})\b")

_STOPWORDS = {
    "UTC", "BEP", "ERC", "TRC", "BNB", "ETH", "BTC", "USDT", "USDC", "BUSD",
    "API", "FAQ", "URL", "THE", "AND", "FOR", "NOT", "ARE", "ALL", "HAS",
    "WILL", "FROM", "THIS", "THAT", "WITH", "HAVE", "BEEN", "WERE", "THEY",
    "EACH", "WHICH", "THEIR", "THERE", "ABOUT", "AFTER", "BEFORE", "WHEN",
    "THAN", "ALSO", "INTO", "OVER", "SUCH", "ONLY", "OTHER", "MORE",
    "SOME", "VERY", "JUST", "WHERE", "MOST", "WOULD", "COULD", "SHOULD",
    "DOES", "DID", "MAY", "CAN", "UPON", "PNL", "IOCO",
    "HTML", "CSS", "JSON", "XML", "HTTP", "HTTPS",
    "USD", "EUR", "GBP", "JPY", "CNY", "MXN", "RON", "CZK",
    "NOTE", "PLEASE", "DEAR", "FELLOW",
    "COIN", "PERPETUAL", "MULTIPLE", "CONTRACTS",
}


def _classify_announcement(title):
    """Determine the announcement type from the title."""
    t = title.lower()
    if "futures" in t and ("delist" in t or "suspend" in t):
        return "futures_delist"
    if "alpha" in t and "remove" in t.lower():
        return "alpha_removal"
    if ("margin" in t and "delist" in t) or "removal of margin" in t or "removal of isolated margin" in t or "removal of cross margin" in t:
        return "margin_delist"
    if "loan" in t and "delist" in t:
        return "loan_delist"
    if "removal of spot" in t or "removal of trading pair" in t:
        return "spot_pair_removal"
    if "delist" in t and "margin" not in t and "futures" not in t:
        return "token_delist"
    if "removal" in t or "remove" in t:
        return "spot_pair_removal"
    return "other"


def _extract_tokens_from_title(title):
    """Extract token/contract symbols from the title delist pattern."""
    m = re.search(r"[Dd]elist\s+(.+?)(?:\s+on\s+|\s*\(|\s*$)", title)
    if m:
        raw = m.group(1)
        tokens = re.findall(r"[A-Z][A-Z0-9]{1,9}", raw)
        return [t for t in tokens if t not in _STOPWORDS]
    return []


def _extract_trading_pairs(content):
    """Extract trading pairs like XXX/YYY from content."""
    return list(dict.fromkeys(_PAIR_RE.findall(content)))


def _extract_contracts(content):
    """Extract futures contract names like VINEUSDT from content."""
    return list(dict.fromkeys(_CONTRACT_RE.findall(content)))


def _extract_action_dates(content):
    """Extract key action dates from content text."""
    dates = []
    lines = content.split("\n")
    for line in lines:
        matches = _DATETIME_RE.findall(line)
        if matches:
            for date_str, time_str in matches:
                # Try to extract what happens at this date
                action = line.strip()
                # Clean up very long lines to just the relevant part
                if len(action) > 200:
                    action = action[:200] + "..."
                dates.append({
                    "datetime_utc": f"{date_str} {time_str}",
                    "action": action,
                })
    # Deduplicate by datetime
    seen = set()
    unique = []
    for d in dates:
        if d["datetime_utc"] not in seen:
            seen.add(d["datetime_utc"])
            unique.append(d)
    return unique


def _extract_key_content(content):
    """Strip boilerplate, return only the essential content paragraphs."""
    # Remove common header boilerplate
    boilerplate_starts = [
        "This is a general",
        "Products and services referred to here",
        "Fellow Binancians",
        "At Binance Futures, the team periodically",
        "At Binance, we periodically review",
        "The team considers the following factors",
    ]
    boilerplate_ends = [
        "There may be discrepancies between",
        "For More Information:",
        "Guides & Related Materials:",
        "Thank you for your support!",
        "Binance Team",
    ]
    # Boilerplate mid-sections (repeated verbatim in many announcements)
    boilerplate_mid = [
        "Trading volume and liquidity",
        "Stability and safety of network from attacks",
        "New regulatory requirements",
        "Change in token supply, tokenomics",
        "Responsiveness to our periodic due diligence",
        "Evidence of unethical/fraudulent conduct",
        "Commitment of team to project",
        "Level and quality of development activity",
        "Level of public communication",
        "Community sentiments",
        "Impact from changes to the project",
        "Material/unjustified increase in token supply",
        "During the final hour proceeding the scheduled settlement",
        "In order to protect users and prevent potential risks",
    ]

    lines = content.split("\n")
    result_lines = []
    skip = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip header boilerplate
        if any(stripped.startswith(bp) for bp in boilerplate_starts):
            continue

        # Skip footer boilerplate and everything after
        if any(stripped.startswith(bp) for bp in boilerplate_ends):
            break

        # Skip known boilerplate mid-sections
        if any(bp in stripped for bp in boilerplate_mid):
            continue

        result_lines.append(stripped)

    return "\n".join(result_lines)


def extract_structured_info(title, content):
    """
    Extract structured information from an announcement.

    Returns a dict with:
      - type: announcement category
      - tokens: delisted token symbols (if applicable)
      - trading_pairs: affected trading pairs
      - contracts: affected futures contracts
      - action_dates: key dates with actions
      - summary: cleaned essential content
    """
    ann_type = _classify_announcement(title)
    tokens = _extract_tokens_from_title(title)

    # If no tokens from title, try content-based extraction for token_delist type
    if not tokens and ann_type == "token_delist":
        m = re.search(
            r"(?:delist|cease trading).{0,200}?following.{0,50}?token\(?s?\)?[:\s]*(.*?)(?:Please note|Please Note|$)",
            content, re.DOTALL | re.IGNORECASE,
        )
        if m:
            block = m.group(1)
            tokens = _TICKER_RE.findall(block)
            tokens = [t for t in tokens if t not in _STOPWORDS and len(t) >= 2]

    trading_pairs = _extract_trading_pairs(content)
    contracts = _extract_contracts(content) if ann_type == "futures_delist" else []
    action_dates = _extract_action_dates(content)
    summary = _extract_key_content(content)

    return {
        "type": ann_type,
        "tokens": tokens,
        "trading_pairs": trading_pairs,
        "contracts": contracts,
        "action_dates": action_dates,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Incremental save / resume
# ---------------------------------------------------------------------------

def _load_existing(output_path):
    """Load previously saved results and build a set of already-fetched codes."""
    if not os.path.exists(output_path):
        return [], set()
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        done = {
            item["url"].rsplit("/", 1)[-1]
            for item in data
            if item.get("summary") is not None
        }
        return data, done
    except (json.JSONDecodeError, KeyError):
        return [], set()


def _save_results(results, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def crawl_binance_delisting(fetch_content=True, output_path=OUTPUT_FILE):
    """
    Fetch all delisting announcements.

    Supports incremental mode: if the output JSON already exists, articles
    whose content was previously fetched will be skipped.
    """
    session = requests.Session()

    # Step 1: get all article stubs from the list API
    raw_articles = fetch_all_articles(session)
    if not raw_articles:
        return []

    # Step 2: load existing results for incremental support
    existing, done_codes = _load_existing(output_path) if fetch_content else ([], set())
    existing_map = {item.get("id"): item for item in existing}

    results = []
    total = len(raw_articles)
    fetched = 0
    skipped = 0

    if fetch_content:
        print(f"\n正在获取 {total} 条公告的详细内容（已缓存 {len(done_codes)} 条）...")

    for idx, art in enumerate(raw_articles, 1):
        release_ts = art.get("releaseDate")
        release_date = (
            datetime.fromtimestamp(release_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
            if release_ts else ""
        )
        code = art.get("code", "")
        art_id = art.get("id")
        url = f"https://www.binance.com/zh-CN/support/announcement/detail/{code}" if code else ""

        # Check if we already have this article with structured data
        if fetch_content and code in done_codes and art_id in existing_map:
            results.append(existing_map[art_id])
            skipped += 1
            continue

        entry = {
            "id": art_id,
            "title": art.get("title", ""),
            "release_date": release_date,
            "url": url,
        }

        if fetch_content and code:
            print(f"  [{idx}/{total}] {art.get('title', '')[:60]} ...")
            detail = fetch_article_detail(session, code)
            if detail:
                plain_text = parse_body(detail.get("body", ""))
                structured = extract_structured_info(entry["title"], plain_text)
                entry.update(structured)
            else:
                entry.update({
                    "type": _classify_announcement(entry["title"]),
                    "tokens": [],
                    "trading_pairs": [],
                    "contracts": [],
                    "action_dates": [],
                    "summary": "",
                })

            fetched += 1
            time.sleep(random.uniform(2.0, 3.5))

            if fetched % 20 == 0:
                _save_results(results + [_stub(a) for a in raw_articles[idx:]], output_path)
                print(f"  [i] 已保存中间结果 ({len(results)} 条)")

        results.append(entry)

    if fetch_content and skipped:
        print(f"  [i] 跳过已缓存 {skipped} 条，新获取 {fetched} 条")

    return results


def _stub(art):
    """Create a minimal entry from a raw article (no content)."""
    release_ts = art.get("releaseDate")
    release_date = (
        datetime.fromtimestamp(release_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if release_ts else ""
    )
    code = art.get("code", "")
    return {
        "id": art.get("id"),
        "title": art.get("title", ""),
        "release_date": release_date,
        "url": f"https://www.binance.com/zh-CN/support/announcement/detail/{code}" if code else "",
    }


def main():
    parser = argparse.ArgumentParser(description="爬取币安下架公告")
    parser.add_argument(
        "--no-content", action="store_true",
        help="只获取公告列表，不解析详细内容（速度更快）",
    )
    parser.add_argument(
        "-o", "--output", default=OUTPUT_FILE,
        help=f"输出 JSON 文件路径（默认: {OUTPUT_FILE}）",
    )
    args = parser.parse_args()

    announcements = crawl_binance_delisting(
        fetch_content=not args.no_content,
        output_path=args.output,
    )

    if not announcements:
        print("\n未获取到任何公告，请检查网络连接或 API 是否可用。")
        return

    _save_results(announcements, args.output)

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"共获取 {len(announcements)} 条下架公告，已保存到 {args.output}")
    print(f"{'=' * 70}")

    # Stats by type
    from collections import Counter
    type_counts = Counter(a.get("type", "unknown") for a in announcements if a.get("type"))
    if type_counts:
        print("\n按类型统计：")
        type_labels = {
            "token_delist": "代币下架",
            "futures_delist": "合约下架",
            "spot_pair_removal": "现货交易对移除",
            "margin_delist": "杠杆交易对下架",
            "alpha_removal": "Alpha 移除",
            "loan_delist": "借贷下架",
            "other": "其他",
        }
        for t, cnt in type_counts.most_common():
            print(f"  {type_labels.get(t, t)}: {cnt}")

    print("\n最新公告：")
    print("-" * 70)
    for i, item in enumerate(announcements[:10], 1):
        tokens = item.get("tokens", [])
        pairs = item.get("trading_pairs", [])
        contracts = item.get("contracts", [])
        ann_type = item.get("type", "")

        print(f"  {i}. [{item['release_date']}] {item['title']}")
        print(f"     类型: {ann_type}")
        if tokens:
            print(f"     代币: {', '.join(tokens)}")
        if contracts:
            print(f"     合约: {', '.join(contracts)}")
        if pairs:
            print(f"     交易对: {', '.join(pairs[:10])}")
            if len(pairs) > 10:
                print(f"             ... 等 {len(pairs)} 个")
        dates = item.get("action_dates", [])
        if dates:
            for d in dates[:3]:
                print(f"     时间: {d['datetime_utc']} UTC")
        print()
    if len(announcements) > 10:
        print(f"  ... 还有 {len(announcements) - 10} 条历史公告，详见 JSON 文件")
    print("-" * 70)


if __name__ == "__main__":
    main()
