"""沙盘试算单测。"""
from server.engine.forecast import RecurringInput
from server.engine.simulate import simulate_purchase


def _salary(amount=25000_00):
    return RecurringInput(
        amount_cents=amount, direction="income", start_month="2026-01", end_month=None, active=True
    )


def _rent(amount=5000_00):
    return RecurringInput(
        amount_cents=amount, direction="expense", start_month="2026-01", end_month=None, active=True
    )


class TestSimulatePurchase:
    def test_affordable(self):
        # 月剩 2 万，买 2.4w 分 12 期免息（月供 2000）→ 扛得住
        r = simulate_purchase(
            amount_cents=24000_00, periods=12, annual_rate_bp=0, n_months=12,
            initial_balance_cents=0, recurring=[_salary(), _rent()],
            transactions=[], loan_payments=[], start_month="2026-08",
        )
        assert r.simulated.first_negative_month is None
        assert r.virtual_monthly_cents == 2000_00
        assert "可以买" in r.conclusion
        # 基线结余应始终高于沙盘结余
        for b, s in zip(r.base.months, r.simulated.months):
            assert b.cumulative_cents > s.cumulative_cents

    def test_unaffordable(self):
        # 月剩 2 万，买 25w 分 12 期（月供约 20833 > 2 万）→ 立即转负
        r = simulate_purchase(
            amount_cents=250000_00, periods=12, annual_rate_bp=0, n_months=12,
            initial_balance_cents=0, recurring=[_salary(), _rent()],
            transactions=[], loan_payments=[], start_month="2026-08",
        )
        assert r.simulated.first_negative_month == "2026-08"
        assert "扛不住" in r.conclusion

    def test_with_interest(self):
        r = simulate_purchase(
            amount_cents=12000_00, periods=12, annual_rate_bp=1200, n_months=12,
            initial_balance_cents=0, recurring=[_salary()],
            transactions=[], loan_payments=[], start_month="2026-08",
        )
        # 有利率时月供高于平摊
        assert r.virtual_monthly_cents > 1000_00

    def test_base_not_polluted(self):
        # 沙盘不影响基线
        r = simulate_purchase(
            amount_cents=10000_00, periods=10, annual_rate_bp=0, n_months=6,
            initial_balance_cents=0, recurring=[_salary()],
            transactions=[], loan_payments=[], start_month="2026-08",
        )
        assert all(m.net_cents == 25000_00 for m in r.base.months)
