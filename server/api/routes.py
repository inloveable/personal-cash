"""REST /api/v1 薄适配层：只做参数校验与序列化，业务全在 service。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import cashflow_service, loan_service, recurring_service, transaction_service
from . import serialize
from .deps import verify_token
from .schemas import BalanceIn, LoanIn, RecurringIn, SimulateIn, TransactionIn

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_token)])

EXPENSE_CATEGORIES = ["餐饮", "交通", "购物", "居住", "娱乐", "医疗", "教育", "数码", "旅行", "其他"]
INCOME_CATEGORIES = ["工资", "年终奖", "意外收入", "理财收益", "报销", "其他"]


@router.get("/categories")
def get_categories():
    return {"expense": EXPENSE_CATEGORIES, "income": INCOME_CATEGORIES}


# ---------- 流水 ----------


@router.get("/transactions")
def list_transactions(month: str | None = None, limit: int = 200, offset: int = 0, db: Session = Depends(get_db)):
    items = transaction_service.list_transactions(db, month=month, limit=limit, offset=offset)
    return {"items": [serialize.tx_to_dict(t) for t in items]}


@router.post("/transactions", status_code=201)
def create_transaction(body: TransactionIn, db: Session = Depends(get_db)):
    tx = transaction_service.add_transaction(
        db,
        amount_yuan=body.amount,
        direction=body.direction,
        category=body.category,
        note=body.note,
        occurred_date=body.date,
        source="manual",
    )
    return serialize.tx_to_dict(tx)


@router.delete("/transactions/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    if not transaction_service.delete_transaction(db, tx_id):
        raise HTTPException(404, "流水不存在")


# ---------- 周期项 ----------


@router.get("/recurring")
def list_recurring(db: Session = Depends(get_db)):
    items = recurring_service.list_recurring(db)
    return {"items": [serialize.recurring_to_dict(r) for r in items]}


@router.post("/recurring", status_code=201)
def create_recurring(body: RecurringIn, db: Session = Depends(get_db)):
    try:
        item = recurring_service.add_recurring(
            db,
            name=body.name,
            amount_yuan=body.amount,
            direction=body.direction,
            category=body.category,
            day_of_month=body.day_of_month,
            start_month=body.start_month,
            end_month=body.end_month,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    return serialize.recurring_to_dict(item)


@router.delete("/recurring/{item_id}", status_code=204)
def delete_recurring(item_id: int, db: Session = Depends(get_db)):
    if not recurring_service.delete_recurring(db, item_id):
        raise HTTPException(404, "周期项不存在")


# ---------- 贷款 ----------


@router.get("/loans")
def list_loans(db: Session = Depends(get_db)):
    loans = loan_service.list_loans(db)
    return {"items": [serialize.loan_to_dict(l) for l in loans]}


@router.post("/loans", status_code=201)
def create_loan(body: LoanIn, db: Session = Depends(get_db)):
    try:
        loan = loan_service.add_loan(
            db,
            name=body.name,
            principal_yuan=body.principal,
            periods=body.periods,
            annual_rate=body.annual_rate,
            method=body.method,
            start_date=body.start_date,
            exclude_principal=body.exclude_principal,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    return serialize.loan_to_dict(loan)


@router.get("/loans/{loan_id}/schedule")
def loan_schedule(loan_id: int, db: Session = Depends(get_db)):
    loan = loan_service.get_loan(db, loan_id)
    if loan is None:
        raise HTTPException(404, "贷款不存在")
    return {
        "loan": serialize.loan_to_dict(loan),
        "schedule": [serialize.schedule_to_dict(s) for s in loan.schedules],
    }


@router.delete("/loans/{loan_id}", status_code=204)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    if not loan_service.delete_loan(db, loan_id):
        raise HTTPException(404, "贷款不存在")


# ---------- 结余预测 / 沙盘 ----------


@router.get("/cashflow/forecast")
def cashflow_forecast(months: int = 12, db: Session = Depends(get_db)):
    return serialize.forecast_to_dict(cashflow_service.get_forecast(db, months=months))


@router.post("/cashflow/simulate")
def cashflow_simulate(body: SimulateIn, db: Session = Depends(get_db)):
    try:
        result = cashflow_service.simulate_purchase(
            db,
            amount_yuan=body.amount,
            periods=body.periods,
            annual_rate=body.annual_rate,
            months=body.months,
            method=body.method,
            exclude_principal=body.exclude_principal,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    return serialize.simulate_to_dict(result)


# ---------- 仪表盘 / 设置 ----------


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    s = cashflow_service.dashboard_summary(db)
    skip = {"next6", "yearly_net_cents"}
    return {
        **{
            (k[: -len("_cents")] if k.endswith("_cents") else k): (
                v / 100 if k.endswith("_cents") else v
            )
            for k, v in s.items()
            if k not in skip
        },
        "yearly_net": {y: v / 100 for y, v in s["yearly_net_cents"].items()},
        "next6": [
            {"month": m["month"], "net": m["net_cents"] / 100, "cumulative": m["cumulative_cents"] / 100}
            for m in s["next6"]
        ],
    }


@router.put("/settings/balance")
def set_balance(body: BalanceIn, db: Session = Depends(get_db)):
    cents = cashflow_service.set_initial_balance(db, int(round(body.initial_balance * 100)))
    return {"initial_balance": cents / 100}
