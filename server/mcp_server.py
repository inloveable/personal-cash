"""MCP 工具集：面向自然语言设计，全部委托 service 层（MCP-first）。

Agent 连接方式（Streamable HTTP）：
  URL: http://<host>:8000/mcp/
  Header: Authorization: Bearer <API_TOKEN>
"""
from __future__ import annotations

from datetime import date

from fastmcp import FastMCP

from .db import session_scope
from .services import cashflow_service, loan_service, recurring_service, transaction_service
from .api import serialize

mcp = FastMCP("ai-ledger")


@mcp.tool
def add_expense(amount: float, category: str = "其他", note: str = "", date_str: str | None = None) -> dict:
    """记一笔支出。amount 为金额（元，如 35.5）；category 建议从 餐饮/交通/购物/居住/娱乐/医疗/教育/数码/旅行/其他 中选；date_str 格式 YYYY-MM-DD，缺省为今天。"""
    with session_scope() as db:
        tx = transaction_service.add_transaction(
            db,
            amount_yuan=amount,
            direction="expense",
            category=category,
            note=note,
            occurred_date=date.fromisoformat(date_str) if date_str else None,
            source="mcp",
        )
        return {"ok": True, "transaction": serialize.tx_to_dict(tx)}


@mcp.tool
def add_income(amount: float, category: str = "其他", note: str = "", date_str: str | None = None) -> dict:
    """记一笔收入（工资外的奖金、意外收入等；每月固定工资建议用 add_recurring）。category 建议从 工资/年终奖/意外收入/理财收益/报销/其他 中选。"""
    with session_scope() as db:
        tx = transaction_service.add_transaction(
            db,
            amount_yuan=amount,
            direction="income",
            category=category,
            note=note,
            occurred_date=date.fromisoformat(date_str) if date_str else None,
            source="mcp",
        )
        return {"ok": True, "transaction": serialize.tx_to_dict(tx)}


@mcp.tool
def add_loan(
    name: str,
    principal: float,
    periods: int,
    annual_rate: float = 0.0,
    method: str = "equal_payment",
    start_date_str: str | None = None,
    exclude_principal: bool = False,
) -> dict:
    """新建一笔贷款/分期。只需提供：name 名称（如"车贷"）、principal 贷款总额（元）、periods 期数（月）、annual_rate 年利率百分数（如 4.9 表示 4.9%，免息分期填 0）、method 还款方式 equal_payment(等额本息，默认)/equal_principal(等额本金)/interest_only(先息后本：每期只还利息，到期一次性还本，消费贷常用)、exclude_principal 仅先息后本可用：到期本金不影响现金流（打算到期续贷/借新还旧时选 True）、start_date_str 首次还款月 YYYY-MM-01（存量贷款必传——用户说"车贷已经还了8期/贷了一年了"时，根据当前月份反推起始月传入，系统会自动把已过月份标记为已还、预测只算剩余期次）。摊还表自动生成。返回月供、已还期数、剩余本金、总利息等摘要。"""
    with session_scope() as db:
        loan = loan_service.add_loan(
            db,
            name=name,
            principal_yuan=principal,
            periods=periods,
            annual_rate=annual_rate,
            method=method,
            start_date=date.fromisoformat(start_date_str) if start_date_str else None,
            exclude_principal=exclude_principal,
        )
        d = serialize.loan_to_dict(loan)
        return {
            "ok": True,
            "loan": d,
            "summary": (
                f"已创建「{d['name']}」：本金 {d['principal']:,.2f} 元，{d['periods']} 期，"
                f"月供 {d['monthly_payment']:,.2f} 元，总利息 {d['total_interest']:,.2f} 元。"
            ),
        }


@mcp.tool
def add_recurring(
    name: str,
    amount: float,
    direction: str,
    category: str = "其他",
    day_of_month: int = 1,
    start_month: str | None = None,
    end_month: str | None = None,
) -> dict:
    """添加每月固定收支项（如工资、房租、话费）。direction: income(收入)/expense(支出)；amount 金额（元）；day_of_month 每月几号；start_month/end_month 格式 YYYY-MM，缺省当月起、永久。"""
    with session_scope() as db:
        item = recurring_service.add_recurring(
            db,
            name=name,
            amount_yuan=amount,
            direction=direction,
            category=category,
            day_of_month=day_of_month,
            start_month=start_month,
            end_month=end_month,
        )
        return {"ok": True, "recurring": serialize.recurring_to_dict(item)}


@mcp.tool
def get_cashflow_forecast(months: int = 12) -> dict:
    """查询未来 N 个月（默认 12）的结余预测：每月收入、日常开销、贷款月供、月结余、累计结余，以及按年聚合的年结余。回答"我这个月/今年能剩多少钱"类问题时调用。"""
    with session_scope() as db:
        result = cashflow_service.get_forecast(db, months=months)
        d = serialize.forecast_to_dict(result)
        lines = [
            f"{m['month']}: 收入 {m['income']:,.0f} 开销 {m['expense'] + m['recurring_expense']:,.0f} "
            f"月供 {m['loan_payment']:,.0f} 结余 {m['net']:,.0f} 累计 {m['cumulative']:,.0f}"
            for m in d["months"]
        ]
        yearly = "，".join(f"{y} 年结余 {v:,.0f} 元" for y, v in d["yearly_net"].items())
        return {"ok": True, "forecast": d, "summary": yearly + "。\n" + "\n".join(lines)}


@mcp.tool
def simulate_purchase(
    amount: float,
    periods: int,
    annual_rate: float = 0.0,
    months: int = 12,
    method: str = "equal_payment",
    exclude_principal: bool = False,
) -> dict:
    """沙盘试算：假设分期买某个东西（不落库），看未来现金流是否扛得住。amount 价格（元）、periods 分期数、annual_rate 分期年利率（免息填 0）、method 还款方式（默认等额本息，可选 equal_principal 等额本金 / interest_only 先息后本）、exclude_principal 仅先息后本：到期本金续贷滚续不计入。返回中文结论：结余是否会变负、最低结余多少。回答"我想买 X，分 Y 期，买得起吗"类问题时调用。"""
    with session_scope() as db:
        result = cashflow_service.simulate_purchase(
            db,
            amount_yuan=amount,
            periods=periods,
            annual_rate=annual_rate,
            months=months,
            method=method,
            exclude_principal=exclude_principal,
        )
        return {"ok": True, **serialize.simulate_to_dict(result)}


@mcp.tool
def list_recent(limit: int = 20) -> dict:
    """查看最近录入的流水，默认 20 条。用于核对账目或回答"我最近记了什么"。"""
    with session_scope() as db:
        items = transaction_service.list_transactions(db, limit=limit)
        return {"ok": True, "items": [serialize.tx_to_dict(t) for t in items]}


@mcp.tool
def get_dashboard() -> dict:
    """查看本月概览：收入/开销/月供/月结余、预计年结余、未来 6 个月结余趋势。"""
    with session_scope() as db:
        return {"ok": True, **cashflow_service.dashboard_summary(db)}
