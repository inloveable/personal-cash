"""模型 -> 对外 dict 的序列化，金额分转元。"""
from __future__ import annotations

from ..engine.forecast import ForecastResult
from ..engine.simulate import SimulateResult
from ..models import Loan, LoanSchedule, RecurringItem, Transaction


def tx_to_dict(t: Transaction) -> dict:
    return {
        "id": t.id,
        "amount": t.amount_cents / 100,
        "direction": t.direction,
        "category": t.category,
        "date": t.occurred_date.isoformat(),
        "note": t.note,
        "source": t.source,
        "created_at": t.created_at.isoformat(),
    }


def recurring_to_dict(r: RecurringItem) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "amount": r.amount_cents / 100,
        "direction": r.direction,
        "category": r.category,
        "day_of_month": r.day_of_month,
        "start_month": r.start_month,
        "end_month": r.end_month,
        "active": r.active,
    }


def schedule_to_dict(s: LoanSchedule) -> dict:
    return {
        "period_no": s.period_no,
        "due_month": s.due_month,
        "principal": s.principal_cents / 100,
        "interest": s.interest_cents / 100,
        "payment": (s.principal_cents + s.interest_cents) / 100,
        "remaining": s.remaining_cents / 100,
    }


def loan_to_dict(loan: Loan) -> dict:
    paid_periods = 0
    from ..engine.months import current_month

    cur = current_month()
    remaining = loan.principal_cents
    for s in loan.schedules:
        if s.due_month < cur:
            paid_periods += 1
            remaining = s.remaining_cents
    first = loan.schedules[0] if loan.schedules else None
    return {
        "id": loan.id,
        "name": loan.name,
        "principal": loan.principal_cents / 100,
        "annual_rate": loan.annual_rate_bp / 100,
        "periods": loan.periods,
        "method": loan.method,
        "exclude_principal": loan.exclude_principal,
        "start_date": loan.start_date.isoformat(),
        "status": loan.status,
        "monthly_payment": (first.principal_cents + first.interest_cents) / 100 if first else 0,
        "remaining_principal": remaining / 100,
        "paid_periods": paid_periods,
        "total_interest": sum(s.interest_cents for s in loan.schedules) / 100,
    }


def month_to_dict(m) -> dict:
    return {
        "month": m.month,
        "income": m.income_cents / 100,
        "recurring_expense": m.recurring_expense_cents / 100,
        "loan_payment": m.loan_payment_cents / 100,
        "expense": m.expense_cents / 100,
        "net": m.net_cents / 100,
        "cumulative": m.cumulative_cents / 100,
    }


def forecast_to_dict(r: ForecastResult) -> dict:
    return {
        "months": [month_to_dict(m) for m in r.months],
        "yearly_net": {y: v / 100 for y, v in r.yearly_net_cents.items()},
        "min_cumulative": r.min_cumulative_cents / 100,
        "first_negative_month": r.first_negative_month,
    }


def simulate_to_dict(r: SimulateResult) -> dict:
    return {
        "virtual_monthly_payment": r.virtual_monthly_cents / 100,
        "conclusion": r.conclusion,
        "base": forecast_to_dict(r.base),
        "simulated": forecast_to_dict(r.simulated),
    }
