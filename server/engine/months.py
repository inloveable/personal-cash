"""月份工具：YYYY-MM 字符串的加减与区间生成。"""
from __future__ import annotations

from datetime import date


def to_month(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def add_months(month: str, n: int) -> str:
    y, m = int(month[:4]), int(month[5:7])
    total = (y * 12 + (m - 1)) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def month_range(start_month: str, n: int) -> list[str]:
    return [add_months(start_month, i) for i in range(n)]


def current_month() -> str:
    return to_month(date.today())


def cmp_month(a: str, b: str) -> int:
    return (a > b) - (a < b)
