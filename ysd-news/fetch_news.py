#!/usr/bin/env python3
"""获取财联社每日早间新闻"""

import json
import sys
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timedelta


API_BASE = "http://8.141.115.112/api-a/news/list"
MAX_DAYS_BACK = 10


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def clamp_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """将日期范围限制在最近 MAX_DAYS_BACK 天内"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    earliest = today - timedelta(days=MAX_DAYS_BACK)

    end_dt = min(parse_date(end_date), today)
    start_dt = max(parse_date(start_date), earliest)

    if start_dt > end_dt:
        start_dt = end_dt

    return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")


def fetch_page(start_date: str, end_date: str, page: int, page_size: int = 10) -> dict:
    params = urllib.parse.urlencode({
        "page": page,
        "page_size": page_size,
        "search": "早间",
        "search_field": "title",
        "message_label": "",
        "start_date": start_date,
        "end_date": end_date,
    })
    url = f"{API_BASE}?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


KEEP_FIELDS = ("id", "title", "content", "time", "created_at", "updated_at")


def fetch_all_news(start_date: str, end_date: str) -> list[dict]:
    start_date, end_date = clamp_date_range(start_date, end_date)

    all_news = []
    page = 1

    while True:
        result = fetch_page(start_date, end_date, page)
        if result.get("code") != 0:
            raise RuntimeError(f"API 返回错误: {result.get('message', '未知错误')}")

        data = result["data"]
        for item in data["news_list"]:
            all_news.append({k: item[k] for k in KEEP_FIELDS if k in item})

        if not data["pagination"]["has_next"]:
            break
        page += 1

    return all_news


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="获取财联社早间新闻")
    parser.add_argument("--start_date", default=today, help="起始日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--end_date", default=today, help="结束日期 YYYY-MM-DD（默认今天）")
    args = parser.parse_args()

    try:
        news = fetch_all_news(args.start_date, args.end_date)
        print(json.dumps(news, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取新闻失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
