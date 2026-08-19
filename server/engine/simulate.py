"""沙盘试算：构造虚拟分期贷款叠加到预测上，纯计算不落库。"""
from __future__ import annotations

from dataclasses import dataclass

from .amortize import INTEREST_ONLY, build_schedule
from .forecast import ForecastResult, LoanPaymentInput, RecurringInput, TransactionInput, forecast
from .months import current_month


@dataclass
class SimulateResult:
    base: ForecastResult  # 不买的基线
    simulated: ForecastResult  # 叠加虚拟分期后
    virtual_monthly_cents: int  # 虚拟分期月供（首期）
    conclusion: str  # 中文结论


def simulate_purchase(
    amount_cents: int,
    periods: int,
    annual_rate_bp: int,
    n_months: int,
    initial_balance_cents: int,
    recurring: list[RecurringInput],
    transactions: list[TransactionInput],
    loan_payments: list[LoanPaymentInput],
    method: str = "equal_payment",
    start_month: str | None = None,
    exclude_principal: bool = False,
) -> SimulateResult:
    start_month = start_month or current_month()

    base = forecast(
        start_month, n_months, initial_balance_cents, recurring, transactions, loan_payments
    )

    virtual = build_schedule(amount_cents, annual_rate_bp, periods, method, start_month)
    # 先息后本 + 本金不影响现金流：只叠加利息，到期本金视为续贷滚续
    if exclude_principal and method == INTEREST_ONLY:
        extra = [
            LoanPaymentInput(due_month=it.due_month, payment_cents=it.interest_cents)
            for it in virtual
        ]
    else:
        extra = [
            LoanPaymentInput(due_month=it.due_month, payment_cents=it.payment_cents)
            for it in virtual
        ]
    simulated = forecast(
        start_month,
        n_months,
        initial_balance_cents,
        recurring,
        transactions,
        loan_payments,
        extra_payments=extra,
    )

    yuan = lambda c: f"{c / 100:,.2f}"  # noqa: E731
    rolling = exclude_principal and method == INTEREST_ONLY
    interest_note = "（先息后本，本金到期续贷不计入）" if rolling else ""
    monthly_show = virtual[0].interest_cents if rolling else virtual[0].payment_cents
    if simulated.first_negative_month:
        conclusion = (
            f"如果分 {periods} 期购买{interest_note}（月供约 {yuan(monthly_show)} 元），"
            f"{simulated.first_negative_month} 累计结余将转负，"
            f"最低结余 {yuan(simulated.min_cumulative_cents)} 元，现金流扛不住。"
        )
    else:
        delta = simulated.min_cumulative_cents - base.min_cumulative_cents
        conclusion = (
            f"如果分 {periods} 期购买{interest_note}（月供约 {yuan(monthly_show)} 元），"
            f"未来 {n_months} 个月累计结余始终为正，"
            f"最低结余 {yuan(simulated.min_cumulative_cents)} 元（比不买少 {yuan(-delta)} 元），可以买。"
        )

    return SimulateResult(
        base=base,
        simulated=simulated,
        virtual_monthly_cents=virtual[0].payment_cents,
        conclusion=conclusion,
    )
