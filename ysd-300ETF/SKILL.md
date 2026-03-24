# ysd-300ETF

获取沪深300ETF（510300）最近30个交易日的日线K线数据。

## 使用方法

运行 Python 脚本：

```bash
python3 /Users/ysd/.openclaw/workspace/skills/ysd-300ETF/fetch_300etf.py
```

脚本会输出 JSON 格式的 K 线数据到 stdout，可直接读取解析。

## 输出格式

JSON 数组，每条记录包含：

| 字段 | 说明 |
|------|------|
| date | 日期 (YYYY-MM-DD) |
| open | 开盘价 |
| close | 收盘价 |
| high | 最高价 |
| low | 最低价 |
| volume | 成交量 |
| amount | 成交额 |
| amplitude | 振幅 (%) |
| change_pct | 涨跌幅 (%) |
| change_amt | 涨跌额 |
| turnover | 换手率 (%) |

## 数据来源

通过 [AKShare](https://github.com/akfamily/akshare) 调用东方财富接口，获取前复权日线数据。

## 依赖

- Python 3
- akshare（已安装）

## 示例输出

```json
[
  {
    "date": "2026-02-10",
    "open": 3.95,
    "close": 3.98,
    "high": 4.01,
    "low": 3.93,
    "volume": 123456789,
    "amount": 4912345678.0,
    "amplitude": 2.02,
    "change_pct": 0.76,
    "change_amt": 0.03,
    "turnover": 1.23
  }
]
```

## 注意事项

- 仅返回交易日数据，周末和节假日不包含在内
- 数据为前复权（qfq）
- 如遇网络问题或数据源不可用，脚本会输出错误信息到 stderr 并以非零状态码退出
