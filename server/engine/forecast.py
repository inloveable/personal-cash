"""结余预测引擎：纯函数，输入内存数据，输出逐月结余与年结余汇总。

口径：工资 = 日常开销 + 贷款月供 + 结余
每月净结余 = 当月收入(recurring_income + 当月 income 流水)
           - 当月固定支出(recurring_expense)
           - 当月贷款月供(Σ 摊还表 due_month 命中)
           - 当月 expense 流水
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .months import month_range


@dataclass(frozen=True)
class RecurringInput:
    amount_cents: int
    direction: str  # income | expense
    start_month: str
    end_month: str | None
    active: bool


@dataclass(frozen=True)
class TransactionInput:
    amount_cents: int
    direction: str  # income | expense
    month: str  # YYYY-MM（由 occurred_date 归集）


@dataclass(frozen=True)
class LoanPaymentInput:
    due_month: str
    payment_cents: int


@dataclass
class MonthForecast:
    month: str
    income_cents: int = 0
    recurring_expense_cents: int = 0
    loan_payment_cents: int = 0
    expense_cents: int = 0  # 日常开销流水（不含贷款月供）
    net_cents: int = 0  # 当月净结余
    cumulative_cents: int = 0  # 累计结余（含期初余额）


@dataclass
class ForecastResult:
    months: list[MonthForecast] = field(default_factory=list)
    yearly_net_cents: dict[str, int] = field(default_factory=dict)  # {"2026": xxx} 年结余
    min_cumulative_cents: int = 0
    first_negative_month: str | None = None


def forecast(
    start_month: str,
    n_months: int,
    initial_balance_cents: int,
    recurring: list[RecurringInput],
    transactions: list[TransactionInput],
    loan_payments: list[LoanPaymentInput],
    extra_payments: list[LoanPaymentInput] | None = None,
) -> ForecastResult:
    """主预测函数。extra_payments 用于沙盘叠加虚拟贷款月供（不落库）。"""
    months = month_range(start_month, n_months)
    month_set = set(months)

    tx_by_month: dict[str, list[TransactionInput]] = {}
    for tx in transactions:
        if tx.month in month_set:
            tx_by_month.setdefault(tx.month, []).append(tx)

    loan_by_month: dict[str, int] = {}
    for lp in loan_payments + (extra_payments or []):
        if lp.due_month in month_set:
            loan_by_month[lp.due_month] = loan_by_month.get(lp.due_month, 0) + lp.payment_cents

    result = ForecastResult()
    cumulative = initial_balance_cents
    min_cumulative: int | None = None  # 只看逐月，不含期初

    for m in months:
        mf = MonthForecast(month=m)
        for rec in recurring:
            if not rec.active:
                continue
            if m < rec.start_month:
                continue
            if rec.end_month is not None and m > rec.end_month:
                continue
            if rec.direction == "income":
                mf.income_cents += rec.amount_cents
            else:
                mf.recurring_expense_cents += rec.amount_cents

        for tx in tx_by_month.get(m, []):
            if tx.direction == "income":
                mf.income_cents += tx.amount_cents
            else:
                mf.expense_cents += tx.amount_cents

        mf.loan_payment_cents = loan_by_month.get(m, 0)
        mf.net_cents = (
            mf.income_cents - mf.recurring_expense_cents - mf.loan_payment_cents - mf.expense_cents
        )
        cumulative += mf.net_cents
        mf.cumulative_cents = cumulative

        if min_cumulative is None or cumulative < min_cumulative:
            min_cumulative = cumulative
        if result.first_negative_month is None and cumulative < 0:
            result.first_negative_month = m

        result.months.append(mf)
        year = m[:4]
        result.yearly_net_cents[year] = result.yearly_net_cents.get(year, 0) + mf.net_cents

    result.min_cumulative_cents = min_cumulative if min_cumulative is not None else initial_balance_cents
    return result
