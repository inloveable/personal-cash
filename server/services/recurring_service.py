"""周期项业务规则（工资、房租等按月 recurring）。"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engine.months import current_month
from ..models import RecurringItem

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def add_recurring(
    db: Session,
    name: str,
    amount_yuan: float,
    direction: str,
    category: str | None = None,
    day_of_month: int = 1,
    start_month: str | None = None,
    end_month: str | None = None,
) -> RecurringItem:
    if direction not in ("income", "expense"):
        raise ValueError("direction 必须是 income 或 expense")
    if amount_yuan <= 0:
        raise ValueError("金额必须为正数（单位：元）")
    if not 1 <= day_of_month <= 31:
        raise ValueError("day_of_month 必须在 1-31")
    start_month = start_month or current_month()
    for m in (start_month, end_month):
        if m is not None and not _MONTH_RE.match(m):
            raise ValueError(f"月份格式必须为 YYYY-MM: {m}")
    if end_month is not None and end_month < start_month:
        raise ValueError("end_month 不能早于 start_month")

    item = RecurringItem(
        name=name.strip(),
        amount_cents=int(round(amount_yuan * 100)),
        direction=direction,
        category=(category or "其他").strip() or "其他",
        day_of_month=day_of_month,
        start_month=start_month,
        end_month=end_month,
        active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_recurring(db: Session, include_inactive: bool = False) -> list[RecurringItem]:
    stmt = select(RecurringItem).order_by(RecurringItem.id.desc())
    if not include_inactive:
        stmt = stmt.where(RecurringItem.active.is_(True))
    return list(db.execute(stmt).scalars())


def set_active(db: Session, item_id: int, active: bool) -> RecurringItem | None:
    item = db.get(RecurringItem, item_id)
    if item is None:
        return None
    item.active = active
    db.commit()
    db.refresh(item)
    return item


def delete_recurring(db: Session, item_id: int) -> bool:
    item = db.get(RecurringItem, item_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True
