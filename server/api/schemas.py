"""REST 请求/响应模型（Pydantic）。对外金额单位一律为元。"""
from __future__ import annotations

from datetime import date as dt_date

from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    amount: float = Field(gt=0, description="金额（元）")
    direction: str = Field(pattern="^(income|expense)$")
    category: str | None = None
    note: str = ""
    date: dt_date | None = None


class RecurringIn(BaseModel):
    name: str
    amount: float = Field(gt=0)
    direction: str = Field(pattern="^(income|expense)$")
    category: str | None = None
    day_of_month: int = Field(default=1, ge=1, le=31)
    start_month: str | None = None
    end_month: str | None = None


_METHOD_PATTERN = "^(equal_payment|equal_principal|interest_only)$"


class LoanIn(BaseModel):
    name: str
    principal: float = Field(gt=0, description="本金（元）")
    periods: int = Field(gt=0, le=360)
    annual_rate: float = Field(default=0.0, ge=0, le=36, description="年利率百分数，如 4.9")
    method: str = Field(default="equal_payment", pattern=_METHOD_PATTERN)
    exclude_principal: bool = Field(default=False, description="仅先息后本：到期本金不计入现金流（续贷口径）")
    start_date: dt_date | None = None


class SimulateIn(BaseModel):
    amount: float = Field(gt=0, description="想买的东西的价格（元）")
    periods: int = Field(gt=0, le=60, description="分期数")
    annual_rate: float = Field(default=0.0, ge=0, le=36)
    months: int = Field(default=12, ge=1, le=36)
    method: str = Field(default="equal_payment", pattern=_METHOD_PATTERN)
    exclude_principal: bool = Field(default=False, description="仅先息后本：到期本金不计入现金流（续贷口径）")


class BalanceIn(BaseModel):
    initial_balance: float = Field(description="期初现金余额（元）")
