"""摊还引擎：等额本息 / 等额本金。

约定：
- 金额整数分，月利率 = annual_rate_bp / 10000 / 12（基点 -> 小数 -> 月化）
- 每期利息按"期初剩余本金 * 月利率"四舍五入到分
- 最后一期吸收尾差，保证 Σ各期本金 == 本金总额、末期剩余 == 0
- due_month 为 YYYY-MM，从 start_month 起逐月推进
"""
from __future__ import annotations

from dataclasses import dataclass

from .months import add_months

EQUAL_PAYMENT = "equal_payment"  # 等额本息
EQUAL_PRINCIPAL = "equal_principal"  # 等额本金
INTEREST_ONLY = "interest_only"  # 先息后本（每期只还利息，到期一次性还本）


@dataclass(frozen=True)
class ScheduleItem:
    period_no: int
    due_month: str
    principal_cents: int
    interest_cents: int
    remaining_cents: int  # 本期还款后剩余本金

    @property
    def payment_cents(self) -> int:
        return self.principal_cents + self.interest_cents


def _round_cents(x: float) -> int:
    return int(round(x))


def monthly_rate(annual_rate_bp: int) -> float:
    return annual_rate_bp / 10000.0 / 12.0


def equal_payment_monthly(principal_cents: int, annual_rate_bp: int, periods: int) -> int:
    """等额本息月供（分）。零利率时为本金平摊。"""
    if periods <= 0:
        raise ValueError("periods 必须为正整数")
    r = monthly_rate(annual_rate_bp)
    if r == 0:
        return _round_cents(principal_cents / periods)
    factor = (1 + r) ** periods
    return _round_cents(principal_cents * r * factor / (factor - 1))


def build_schedule(
    principal_cents: int,
    annual_rate_bp: int,
    periods: int,
    method: str,
    start_month: str,
) -> list[ScheduleItem]:
    """生成完整摊还表。最后一期吸收全部尾差。"""
    if principal_cents <= 0:
        raise ValueError("principal_cents 必须为正")
    if periods <= 0:
        raise ValueError("periods 必须为正整数")
    if method not in (EQUAL_PAYMENT, EQUAL_PRINCIPAL, INTEREST_ONLY):
        raise ValueError(f"未知还款方式: {method}")

    r = monthly_rate(annual_rate_bp)
    items: list[ScheduleItem] = []
    remaining = principal_cents

    if method == EQUAL_PAYMENT:
        monthly = equal_payment_monthly(principal_cents, annual_rate_bp, periods)

    for i in range(1, periods + 1):
        interest = _round_cents(remaining * r)
        if i == periods:
            principal_part = remaining  # 尾差全部并入末期
        elif method == EQUAL_PAYMENT:
            principal_part = monthly - interest
            if principal_part > remaining:
                principal_part = remaining
        elif method == EQUAL_PRINCIPAL:
            principal_part = _round_cents(principal_cents / periods)
            if principal_part > remaining:
                principal_part = remaining
        else:  # INTEREST_ONLY：中间期不还本金
            principal_part = 0
        remaining -= principal_part
        items.append(
            ScheduleItem(
                period_no=i,
                due_month=add_months(start_month, i - 1),
                principal_cents=principal_part,
                interest_cents=interest,
                remaining_cents=remaining,
            )
        )

    # 校验不变量：本金守恒、末期清零
    assert sum(it.principal_cents for it in items) == principal_cents
    assert items[-1].remaining_cents == 0
    return items
