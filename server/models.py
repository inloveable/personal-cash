"""数据模型。金额一律整数分（cents），年利率用基点 bp（万分之一）。"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)  # income | expense
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="其他")
    occurred_date: Mapped[date] = mapped_column(nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(8), nullable=False, default="manual")  # manual | mcp
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("ix_transactions_month", "occurred_date"),)


class RecurringItem(Base):
    __tablename__ = "recurring_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)  # income | expense
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="其他")
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    start_month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    end_month: Mapped[str | None] = mapped_column(String(7), nullable=True)  # YYYY-MM, None=永久
    active: Mapped[bool] = mapped_column(nullable=False, default=True)


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    principal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_rate_bp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    periods: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False, default="equal_payment")  # equal_payment | equal_principal | interest_only
    exclude_principal: Mapped[bool] = mapped_column(nullable=False, default=False)  # 先息后本专用：到期本金不计入现金流（续贷口径）
    start_date: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, default="active")  # active | closed
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    schedules: Mapped[list["LoanSchedule"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan", order_by="LoanSchedule.period_no"
    )


class LoanSchedule(Base):
    __tablename__ = "loan_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    period_no: Mapped[int] = mapped_column(Integer, nullable=False)
    due_month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    principal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    interest_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    loan: Mapped[Loan] = relationship(back_populates="schedules")

    __table_args__ = (Index("ix_loan_schedules_due_month", "due_month"),)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
