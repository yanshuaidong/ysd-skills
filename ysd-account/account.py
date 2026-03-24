import json
import os
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_FILE = os.path.join(SKILL_DIR, "account.json")
OPERATION_FILE = os.path.join(SKILL_DIR, "operation.json")


def _load_json(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(filepath: str, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _recalculate_account(account: dict) -> dict:
    """根据持仓重新计算总市值和总资产"""
    total_market_value = 0.0
    for stock_code, pos in account["positions"].items():
        total_market_value += pos["quantity"] * pos["avg_cost"]
    account["total_market_value"] = round(total_market_value, 2)
    account["total_assets"] = round(account["available_funds"] + account["total_market_value"], 2)
    return account


def query_account() -> dict:
    """查询账户状态，返回账户信息字典。

    Returns:
        dict: {
            "available_funds": 可用资金,
            "total_market_value": 总市值,
            "total_assets": 总资产,
            "positions": { "股票代码": { "name": 名称, "quantity": 持仓数量, "avg_cost": 成本价 }, ... }
        }
    """
    return _load_json(ACCOUNT_FILE)


def query_operations(stock_code: str = None, op_type: str = None) -> list:
    """查询操作记录。

    Args:
        stock_code: 可选，按股票代码筛选
        op_type: 可选，按操作类型筛选 ("buy" / "sell")

    Returns:
        list: 操作记录列表
    """
    operations = _load_json(OPERATION_FILE)
    if stock_code:
        operations = [op for op in operations if op["stock_code"] == stock_code]
    if op_type:
        operations = [op for op in operations if op["type"] == op_type]
    return operations


def buy(stock_code: str, stock_name: str, price: float, quantity: int) -> dict:
    """买入股票。

    Args:
        stock_code: 股票代码，如 "600519"
        stock_name: 股票名称，如 "贵州茅台"
        price: 买入价格（元）
        quantity: 买入数量（股）

    Returns:
        dict: { "success": bool, "message": str, "operation": 操作记录 | None }
    """
    if price <= 0:
        return {"success": False, "message": "买入价格必须大于0", "operation": None}
    if quantity <= 0:
        return {"success": False, "message": "买入数量必须大于0", "operation": None}

    total_cost = round(price * quantity, 2)
    account = _load_json(ACCOUNT_FILE)

    if total_cost > account["available_funds"]:
        return {
            "success": False,
            "message": f"资金不足，需要 {total_cost} 元，可用资金仅 {account['available_funds']} 元",
            "operation": None,
        }

    account["available_funds"] = round(account["available_funds"] - total_cost, 2)

    if stock_code in account["positions"]:
        pos = account["positions"][stock_code]
        old_total = pos["avg_cost"] * pos["quantity"]
        new_total = old_total + total_cost
        pos["quantity"] += quantity
        pos["avg_cost"] = round(new_total / pos["quantity"], 4)
    else:
        account["positions"][stock_code] = {
            "name": stock_name,
            "quantity": quantity,
            "avg_cost": price,
        }

    _recalculate_account(account)
    _save_json(ACCOUNT_FILE, account)

    operation = {
        "type": "buy",
        "stock_code": stock_code,
        "stock_name": stock_name,
        "price": price,
        "quantity": quantity,
        "total_amount": total_cost,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    operations = _load_json(OPERATION_FILE)
    operations.append(operation)
    _save_json(OPERATION_FILE, operations)

    return {"success": True, "message": f"成功买入 {stock_name}({stock_code}) {quantity}股 @ {price}元，共 {total_cost}元", "operation": operation}


def sell(stock_code: str, price: float, quantity: int) -> dict:
    """卖出股票。

    Args:
        stock_code: 股票代码，如 "600519"
        price: 卖出价格（元）
        quantity: 卖出数量（股）

    Returns:
        dict: { "success": bool, "message": str, "operation": 操作记录 | None, "profit": 本次盈亏 | None }
    """
    if price <= 0:
        return {"success": False, "message": "卖出价格必须大于0", "operation": None, "profit": None}
    if quantity <= 0:
        return {"success": False, "message": "卖出数量必须大于0", "operation": None, "profit": None}

    account = _load_json(ACCOUNT_FILE)

    if stock_code not in account["positions"]:
        return {"success": False, "message": f"未持有股票 {stock_code}，无法卖出", "operation": None, "profit": None}

    pos = account["positions"][stock_code]
    if quantity > pos["quantity"]:
        return {
            "success": False,
            "message": f"持仓不足，持有 {pos['quantity']}股，要卖出 {quantity}股",
            "operation": None,
            "profit": None,
        }

    total_revenue = round(price * quantity, 2)
    profit = round((price - pos["avg_cost"]) * quantity, 2)
    stock_name = pos["name"]

    account["available_funds"] = round(account["available_funds"] + total_revenue, 2)
    pos["quantity"] -= quantity

    if pos["quantity"] == 0:
        del account["positions"][stock_code]

    _recalculate_account(account)
    _save_json(ACCOUNT_FILE, account)

    operation = {
        "type": "sell",
        "stock_code": stock_code,
        "stock_name": stock_name,
        "price": price,
        "quantity": quantity,
        "total_amount": total_revenue,
        "profit": profit,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    operations = _load_json(OPERATION_FILE)
    operations.append(operation)
    _save_json(OPERATION_FILE, operations)

    profit_str = f"盈利 {profit}元" if profit >= 0 else f"亏损 {abs(profit)}元"
    return {
        "success": True,
        "message": f"成功卖出 {stock_name}({stock_code}) {quantity}股 @ {price}元，共 {total_revenue}元，{profit_str}",
        "operation": operation,
        "profit": profit,
    }


if __name__ == "__main__":
    print("=== 账户状态 ===")
    print(json.dumps(query_account(), ensure_ascii=False, indent=2))

    print("\n=== 买入测试 ===")
    result = buy("600519", "贵州茅台", 1800.00, 1)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n=== 买入后账户状态 ===")
    print(json.dumps(query_account(), ensure_ascii=False, indent=2))

    print("\n=== 卖出测试 ===")
    result = sell("600519", 1850.00, 1)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n=== 卖出后账户状态 ===")
    print(json.dumps(query_account(), ensure_ascii=False, indent=2))

    print("\n=== 操作记录 ===")
    print(json.dumps(query_operations(), ensure_ascii=False, indent=2))
