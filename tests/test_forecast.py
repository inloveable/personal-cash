"""结余预测单测：工资 = 开销 + 月供 + 结余。"""
from server.engine.forecast import (
    LoanPaymentInput,
    RecurringInput,
    TransactionInput,
    forecast,
)


def _salary(amount=25000_00):
    return RecurringInput(
        amount_cents=amount, direction="income", start_month="2026-01", end_month=None, active=True
    )


def _rent(amount=5000_00):
    return RecurringInput(
        amount_cents=amount, direction="expense", start_month="2026-01", end_month=None, active=True
    )


class TestBasicForecast:
    def test_salary_minus_rent(self):
        r = forecast("2026-08", 3, 10000_00, [_salary(), _rent()], [], [])
        assert len(r.months) == 3
        for m in r.months:
            assert m.income_cents == 25000_00
            assert m.recurring_expense_cents == 5000_00
            assert m.net_cents == 20000_00
        assert r.months[2].cumulative_cents == 10000_00 + 3 * 20000_00
        assert r.first_negative_month is None

    def test_loan_payment_deducted(self):
        loans = [LoanPaymentInput(due_month="2026-08", payment_cents=3500_00)]
        r = forecast("2026-08", 1, 0, [_salary()], [], loans)
        assert r.months[0].loan_payment_cents == 3500_00
        assert r.months[0].net_cents == 25000_00 - 3500_00

    def test_transactions_counted_in_month(self):
        txs = [
            TransactionInput(amount_cents=500_00, direction="expense", month="2026-08"),
            TransactionInput(amount_cents=30000_00, direction="income", month="2026-09"),  # 年终奖
        ]
        r = forecast("2026-08", 2, 0, [_salary()], txs, [])
        assert r.months[0].net_cents == 25000_00 - 500_00
        assert r.months[1].net_cents == 25000_00 + 30000_00

    def test_yearly_aggregation(self):
        r = forecast("2026-11", 4, 0, [_salary()], [], [])
        assert r.yearly_net_cents["2026"] == 2 * 25000_00
        assert r.yearly_net_cents["2027"] == 2 * 25000_00


class TestBoundaries:
    def test_recurring_end_month_excluded(self):
        rent = RecurringInput(
            amount_cents=5000_00, direction="expense",
            start_month="2026-01", end_month="2026-08", active=True,
        )
        r = forecast("2026-08", 2, 0, [rent], [], [])
        assert r.months[0].recurring_expense_cents == 5000_00
        assert r.months[1].recurring_expense_cents == 0

    def test_inactive_recurring_ignored(self):
        r = forecast("2026-08", 1, 0, [
            RecurringInput(amount_cents=5000_00, direction="expense",
                           start_month="2026-01", end_month=None, active=False)
        ], [], [])
        assert r.months[0].recurring_expense_cents == 0

    def test_negative_cumulative_detected(self):
        # 月薪 2.5w，9 月一笔 6w 月供：8 月累计 2.5w → 9 月 2.5w-3.5w=-1w 转负
        big_loan = [LoanPaymentInput(due_month="2026-09", payment_cents=60000_00)]
        r = forecast("2026-08", 3, 0, [_salary()], [], big_loan)
        assert r.first_negative_month == "2026-09"
        assert r.min_cumulative_cents == -10000_00

    def test_out_of_range_data_ignored(self):
        txs = [TransactionInput(amount_cents=999_00, direction="expense", month="2025-01")]
        loans = [LoanPaymentInput(due_month="2027-12", payment_cents=999_00)]
        r = forecast("2026-08", 2, 0, [], txs, loans)
        assert all(m.net_cents == 0 for m in r.months)
