"""结余预测 / 沙盘试算业务规则：一次性查数，内存聚合，避免 N+1。"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engine import forecast as eng_forecast
from ..engine import simulate as eng_simulate
from ..engine.months import add_months, current_month
from ..models import Loan, LoanSchedule, RecurringItem, Setting, Transaction
from . import loan_service, recurring_service, transaction_service

INITIAL_BALANCE_KEY = "initial_balance_cents"


def get_initial_balance(db: Session) -> int:
    row = db.get(Setting, INITIAL_BALANCE_KEY)
    return int(row.value) if row else 0


def set_initial_balance(db: Session, cents: int) -> int:
    row = db.get(Setting, INITIAL_BALANCE_KEY)
    if row is None:
        row = Setting(key=INITIAL_BALANCE_KEY, value=str(cents))
        db.add(row)
    else:
        row.value = str(cents)
    db.commit()
    return cents


def _gather_inputs(db: Session, start_month: str, n_months: int):
    """一次性查出区间所需全部数据，转 engine 输入。"""
    end_month = add_months(start_month, n_months - 1)

    recurring = [
        eng_forecast.RecurringInput(
            amount_cents=r.amount_cents,
            direction=r.direction,
            start_month=r.start_month,
            end_month=r.end_month,
            active=r.active,
        )
        for r in recurring_service.list_recurring(db)
        # 粗过滤：结束月份早于区间起点的直接排除
        if r.end_month is None or r.end_month >= start_month
    ]

    transactions = [
        eng_forecast.TransactionInput(
            amount_cents=t.amount_cents,
            direction=t.direction,
            month=t.occurred_date.strftime("%Y-%m"),
        )
        for t in transaction_service.transactions_in_range(db, start_month, end_month)
    ]

    schedules = list(
        db.execute(
            select(LoanSchedule)
            .join(Loan, LoanSchedule.loan_id == Loan.id)
            .where(Loan.status == "active")
            .where(LoanSchedule.due_month >= start_month)
            .where(LoanSchedule.due_month <= end_month)
        ).scalars()
    )
    loans_by_id = {l.id: l for l in loan_service.list_loans(db)}
    loan_payments = []
    for s in schedules:
        loan = loans_by_id.get(s.loan_id)
        # 先息后本 + 本金不影响现金流：只计利息，到期本金视为续贷滚续
        if loan is not None and loan.exclude_principal:
            payment = s.interest_cents
        else:
            payment = s.principal_cents + s.interest_cents
        loan_payments.append(eng_forecast.LoanPaymentInput(due_month=s.due_month, payment_cents=payment))

    return recurring, transactions, loan_payments


def get_forecast(db: Session, months: int = 12, start_month: str | None = None) -> eng_forecast.ForecastResult:
    start_month = start_month or current_month()
    months = max(1, min(months, 36))
    recurring, transactions, loan_payments = _gather_inputs(db, start_month, months)
    return eng_forecast.forecast(
        start_month, months, get_initial_balance(db), recurring, transactions, loan_payments
    )


def simulate_purchase(
    db: Session,
    amount_yuan: float,
    periods: int,
    annual_rate: float = 0.0,
    months: int = 12,
    method: str = "equal_payment",
    exclude_principal: bool = False,
) -> eng_simulate.SimulateResult:
    if amount_yuan <= 0:
        raise ValueError("金额必须为正数（单位：元）")
    if periods <= 0:
        raise ValueError("期数必须为正整数")
    start_month = current_month()
    months = max(1, min(months, 36))
    recurring, transactions, loan_payments = _gather_inputs(db, start_month, months)
    return eng_simulate.simulate_purchase(
        amount_cents=int(round(amount_yuan * 100)),
        periods=periods,
        annual_rate_bp=int(round(annual_rate * 100)),
        n_months=months,
        initial_balance_cents=get_initial_balance(db),
        recurring=recurring,
        transactions=transactions,
        loan_payments=loan_payments,
        method=method,
        start_month=start_month,
        exclude_principal=exclude_principal,
    )


def dashboard_summary(db: Session) -> dict:
    """仪表盘：本月概览 + 年结余预测。"""
    cur = current_month()
    result = get_forecast(db, months=12)
    this = result.months[0]
    active_loans = loan_service.list_loans(db)
    return {
        "month": cur,
        "income_cents": this.income_cents,
        "expense_cents": this.expense_cents,
        "recurring_expense_cents": this.recurring_expense_cents,
        "loan_payment_cents": this.loan_payment_cents,
        "net_cents": this.net_cents,
        "cumulative_cents": this.cumulative_cents,
        "initial_balance_cents": get_initial_balance(db),
        "yearly_net_cents": result.yearly_net_cents,
        "first_negative_month": result.first_negative_month,
        "min_cumulative_cents": result.min_cumulative_cents,
        "active_loan_count": len(active_loans),
        "next6": [
            {"month": m.month, "net_cents": m.net_cents, "cumulative_cents": m.cumulative_cents}
            for m in result.months[:6]
        ],
    }
