"""贷款/分期业务规则：创建时调 engine 预生成摊还表并落库。"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engine import amortize
from ..engine.months import to_month
from ..models import Loan, LoanSchedule


def add_loan(
    db: Session,
    name: str,
    principal_yuan: float,
    periods: int,
    annual_rate: float = 0.0,
    method: str = amortize.EQUAL_PAYMENT,
    start_date: date | None = None,
    exclude_principal: bool = False,
) -> Loan:
    """annual_rate 为年利率百分数（如 4.9 表示 4.9%），内部转基点。

    exclude_principal：仅先息后本可用。到期本金不计入现金流预测（续贷/借新还旧口径），
    摊还表仍完整生成，仅预测聚合时只计利息。
    """
    if principal_yuan <= 0:
        raise ValueError("本金必须为正数（单位：元）")
    if periods <= 0:
        raise ValueError("期数必须为正整数")
    if not 0 <= annual_rate <= 36:
        raise ValueError("年利率超出合理范围 0-36%")
    if exclude_principal and method != amortize.INTEREST_ONLY:
        raise ValueError("仅先息后本支持「本金不影响现金流」")

    principal_cents = int(round(principal_yuan * 100))
    annual_rate_bp = int(round(annual_rate * 100))
    start_date = start_date or date.today().replace(day=1)

    schedule = amortize.build_schedule(
        principal_cents, annual_rate_bp, periods, method, to_month(start_date)
    )

    loan = Loan(
        name=name.strip(),
        principal_cents=principal_cents,
        annual_rate_bp=annual_rate_bp,
        periods=periods,
        method=method,
        exclude_principal=exclude_principal,
        start_date=start_date,
        status="active",
    )
    loan.schedules = [
        LoanSchedule(
            period_no=it.period_no,
            due_month=it.due_month,
            principal_cents=it.principal_cents,
            interest_cents=it.interest_cents,
            remaining_cents=it.remaining_cents,
        )
        for it in schedule
    ]
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def list_loans(db: Session, include_closed: bool = False) -> list[Loan]:
    stmt = select(Loan).order_by(Loan.id.desc())
    if not include_closed:
        stmt = stmt.where(Loan.status == "active")
    return list(db.execute(stmt).scalars())


def get_loan(db: Session, loan_id: int) -> Loan | None:
    return db.get(Loan, loan_id)


def close_loan(db: Session, loan_id: int) -> Loan | None:
    """结清：状态置 closed，删除尚未到期的摊还期次。"""
    loan = db.get(Loan, loan_id)
    if loan is None:
        return None
    from ..engine.months import current_month

    cur = current_month()
    loan.schedules = [s for s in loan.schedules if s.due_month < cur]
    if not loan.schedules:
        loan.status = "closed"
    db.commit()
    db.refresh(loan)
    return loan


def delete_loan(db: Session, loan_id: int) -> bool:
    loan = db.get(Loan, loan_id)
    if loan is None:
        return False
    db.delete(loan)  # schedules 级联删除
    db.commit()
    return True
