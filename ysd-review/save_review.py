#!/usr/bin/env python3
"""将交易复盘（AAR）结果保存为 JSON 文件，方便导出和回溯分析"""

import json
import sys
import os
import argparse
from datetime import datetime

REQUIRED_FIELDS = ("trade_plan", "actual_result", "good", "improve", "lessons", "next_actions")
OPTIONAL_FIELDS = ("market_data", "operation", "account", "scores")
LIST_FIELDS = ("good", "improve", "lessons", "next_actions")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "reviews")


def validate_review(data: dict) -> list[str]:
    """校验复盘数据完整性，返回缺失字段列表"""
    return [f for f in REQUIRED_FIELDS if f not in data]


def build_review_record(date_str: str, data: dict) -> dict:
    """构建标准化的交易复盘记录"""
    now = datetime.now()

    record = {
        "date": date_str,
        "time": now.strftime("%H:%M:%S"),
        "market_data": data.get("market_data", None),
        "trade_plan": data["trade_plan"],
        "actual_result": data["actual_result"],
        "operation": data.get("operation", {"action": "hold", "quantity": 0, "price": 0}),
        "account": data.get("account", None),
        "good": _ensure_list(data["good"]),
        "improve": _ensure_list(data["improve"]),
        "lessons": _ensure_list(data["lessons"]),
        "next_actions": _ensure_list(data["next_actions"]),
        "scores": data.get("scores", None),
    }
    return record


def _ensure_list(value) -> list:
    if isinstance(value, list):
        return value
    return [value]


def save_review(date_str: str, record: dict) -> str:
    """保存复盘记录到 JSON 文件，返回文件路径。同一天多次复盘会追加"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{date_str}.json")

    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
            existing = content if isinstance(content, list) else [content]

    existing.append(record)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description="保存交易复盘（AAR）结果为 JSON")
    parser.add_argument("--date", default=today, help="交易日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--data", default=None, help="复盘数据 JSON 字符串（也可通过 stdin 传入）")
    args = parser.parse_args()

    if args.data:
        raw = args.data
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    else:
        print("错误: 请通过 --data 参数或 stdin 传入复盘数据（JSON 格式）", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    missing = validate_review(data)
    if missing:
        print(f"复盘数据不完整，缺少字段: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    record = build_review_record(args.date, data)
    filepath = save_review(args.date, record)

    result = {"status": "ok", "file": filepath, "record": record}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
