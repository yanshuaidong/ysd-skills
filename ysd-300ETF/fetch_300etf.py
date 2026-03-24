#!/usr/bin/env python3
"""获取沪深300ETF(510300)最近30个交易日的日K线数据"""

import json
import sys
from datetime import datetime, timedelta

import akshare as ak


def fetch_300etf_daily(days_back: int = 60) -> list[dict]:
    """
    获取510300最近约30个交易日的日线数据。
    days_back 设为60是为了覆盖节假日，确保拿到至少30个交易日。
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")

    df = ak.fund_etf_hist_em(
        symbol="510300",
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )

    column_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "振幅": "amplitude",
        "涨跌幅": "change_pct",
        "涨跌额": "change_amt",
        "换手率": "turnover",
    }
    df = df.rename(columns=column_map)
    df = df[[c for c in column_map.values() if c in df.columns]]
    df = df.sort_values("date").tail(30).reset_index(drop=True)
    df["date"] = df["date"].astype(str)

    return df.to_dict(orient="records")


def main():
    try:
        data = fetch_300etf_daily()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取数据失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
