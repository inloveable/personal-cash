"""流水业务规则：REST 与 MCP 共用的唯一落点。"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Transaction

VALID_DIRECTIONS = ("income", "expense")
DEFAULT_CATEGORY = "其他"


def add_transaction(
    db: Session,
    amount_yuan: float,
    direction: str,
    category: str | None = None,
    note: str = "",
    occurred_date: date | None = None,
    source: str = "manual",
) -> Transaction:
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"direction 必须是 {VALID_DIRECTIONS}")
    if amount_yuan <= 0:
        raise ValueError("金额必须为正数（单位：元）")
    tx = Transaction(
        amount_cents=int(round(amount_yuan * 100)),
        direction=direction,
        category=(category or DEFAULT_CATEGORY).strip() or DEFAULT_CATEGORY,
        note=note.strip(),
        occurred_date=occurred_date or date.today(),
        source=source,
        created_at=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def list_transactions(
    db: Session,
    month: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[Transaction]:
    stmt = select(Transaction).order_by(Transaction.occurred_date.desc(), Transaction.id.desc())
    if month:
        stmt = stmt.where(Transaction.occurred_date.like(f"{month}-%"))
    return list(db.execute(stmt.limit(limit).offset(offset)).scalars())


def delete_transaction(db: Session, tx_id: int) -> bool:
    tx = db.get(Transaction, tx_id)
    if tx is None:
        return False
    db.delete(tx)
    db.commit()
    return True


def transactions_in_range(db: Session, start_month: str, end_month: str) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .where(Transaction.occurred_date >= f"{start_month}-01")
        .where(Transaction.occurred_date <= f"{end_month}-31")
    )
    return list(db.execute(stmt).scalars())
