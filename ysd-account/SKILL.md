# ysd-account — 股票模拟账户管理

管理 ysd 的股票模拟交易账户，支持买入、卖出、查询账户状态和操作记录。

## 文件结构

- `account.json` — 账户状态（可用资金、总市值、总资产、持仓明细）
- `operation.json` — 所有操作记录（买入/卖出历史）
- `account.py` — Python 模块，提供核心操作方法

## 使用方式

用 Python 调用 `account.py` 中的方法：

```python
from account import query_account, query_operations, buy, sell
```

### 1. 查询账户状态

```python
account = query_account()
# 返回: { "available_funds": 可用资金, "total_market_value": 总市值, "total_assets": 总资产, "positions": {...} }
```

### 2. 查询操作记录

```python
ops = query_operations()                         # 全部记录
ops = query_operations(stock_code="600519")      # 按股票筛选
ops = query_operations(op_type="buy")            # 按类型筛选
```

### 3. 买入股票

```python
result = buy(stock_code="600519", stock_name="贵州茅台", price=1800.00, quantity=1)
# 返回: { "success": True/False, "message": "...", "operation": {...} }
```

- 自动扣减可用资金
- 若已持有该股票，自动计算加权平均成本
- 资金不足时返回失败

### 4. 卖出股票

```python
result = sell(stock_code="600519", price=1850.00, quantity=1)
# 返回: { "success": True/False, "message": "...", "operation": {...}, "profit": 盈亏金额 }
```

- 自动增加可用资金
- 自动计算本次卖出盈亏（基于持仓均价）
- 卖完自动清除持仓
- 持仓不足时返回失败

## Agent 使用指南

当用户要求查看账户、买入或卖出股票时：

1. 先 `query_account()` 了解当前状态
2. 执行对应操作（buy/sell）
3. 将结果用自然语言告知用户
4. 如需查看历史，用 `query_operations()`

也可以直接读取 `account.json` 和 `operation.json` 获取原始数据。

## 初始状态

- 可用资金：10,000 元
- 总市值：0 元
- 总资产：10,000 元
- 持仓：无
