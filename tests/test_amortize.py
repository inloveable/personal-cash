"""摊还引擎单测：月供公式、本金守恒、尾差吸收。"""
import pytest

from server.engine.amortize import (
    EQUAL_PAYMENT,
    EQUAL_PRINCIPAL,
    INTEREST_ONLY,
    build_schedule,
    equal_payment_monthly,
)


class TestEqualPayment:
    def test_zero_rate_flat_split(self):
        # 零利率：月供 = 本金/期数
        monthly = equal_payment_monthly(12000_00, 0, 12)
        assert monthly == 1000_00

    def test_known_rate(self):
        # 12 万本金，年利率 12%（月利率 1%），12 期：月供约 10661.85 元
        monthly = equal_payment_monthly(120000_00, 1200, 12)
        assert abs(monthly - 1066185) <= 100  # 容差 1 元

    def test_principal_conservation(self):
        s = build_schedule(120000_00, 1200, 12, EQUAL_PAYMENT, "2026-08")
        assert sum(it.principal_cents for it in s) == 120000_00
        assert s[-1].remaining_cents == 0
        assert len(s) == 12

    def test_equal_payment_monthly_constant(self):
        s = build_schedule(50000_00, 600, 24, EQUAL_PAYMENT, "2026-08")
        payments = [it.payment_cents for it in s]
        # 等额本息月供恒定（末期吸收尾差允许小幅差异）
        assert max(payments) - min(payments) <= 100

    def test_due_months_sequential(self):
        s = build_schedule(1000_00, 0, 3, EQUAL_PAYMENT, "2026-11")
        assert [it.due_month for it in s] == ["2026-11", "2026-12", "2027-01"]

    def test_interest_declines(self):
        s = build_schedule(100000_00, 1200, 12, EQUAL_PAYMENT, "2026-08")
        interests = [it.interest_cents for it in s]
        assert interests == sorted(interests, reverse=True)


class TestEqualPrincipal:
    def test_principal_conservation(self):
        s = build_schedule(120000_00, 1200, 12, EQUAL_PRINCIPAL, "2026-08")
        assert sum(it.principal_cents for it in s) == 120000_00
        assert s[-1].remaining_cents == 0

    def test_payment_declines(self):
        s = build_schedule(120000_00, 1200, 12, EQUAL_PRINCIPAL, "2026-08")
        payments = [it.payment_cents for it in s]
        assert payments == sorted(payments, reverse=True)

    def test_first_payment(self):
        # 12 万 / 12 期等额本金：首月本金 1 万 + 利息 120000*1% = 1200 → 11200 元
        s = build_schedule(120000_00, 1200, 12, EQUAL_PRINCIPAL, "2026-08")
        assert s[0].principal_cents == 10000_00
        assert s[0].interest_cents == 1200_00


class TestInterestOnly:
    def test_interest_only_middle_periods_zero_principal(self):
        # 10w 消费贷，年利率 12%（月息 1%），12 期先息后本：前 11 期只还 1000 利息
        s = build_schedule(100000_00, 1200, 12, INTEREST_ONLY, "2026-08")
        for it in s[:-1]:
            assert it.principal_cents == 0
            assert it.interest_cents == 1000_00
            assert it.remaining_cents == 100000_00

    def test_interest_only_final_period(self):
        # 末期：本金一次性还完 + 当月利息
        s = build_schedule(100000_00, 1200, 12, INTEREST_ONLY, "2026-08")
        last = s[-1]
        assert last.principal_cents == 100000_00
        assert last.interest_cents == 1000_00
        assert last.remaining_cents == 0
        assert sum(it.principal_cents for it in s) == 100000_00

    def test_interest_only_zero_rate(self):
        # 免息：中间期还款为 0，末期全额本金
        s = build_schedule(12000_00, 0, 12, INTEREST_ONLY, "2026-08")
        assert all(it.payment_cents == 0 for it in s[:-1])
        assert s[-1].payment_cents == 12000_00

    def test_interest_only_total_interest(self):
        # 总利息 = 本金 × 月利率 × 期数（本金全程不还）
        s = build_schedule(50000_00, 1200, 6, INTEREST_ONLY, "2026-08")
        assert sum(it.interest_cents for it in s) == 50000_00 * 6 // 100


class TestEdgeCases:
    def test_one_period(self):
        s = build_schedule(999_99, 500, 1, EQUAL_PAYMENT, "2026-08")
        assert len(s) == 1
        assert s[0].remaining_cents == 0
        assert s[0].principal_cents == 999_99

    def test_odd_amount_tail_absorb(self):
        # 100 元分 3 期零利率：33.33+33.33+33.34，尾差进末期
        s = build_schedule(100_00, 0, 3, EQUAL_PAYMENT, "2026-08")
        assert sum(it.principal_cents for it in s) == 100_00

    def test_invalid_inputs(self):
        with pytest.raises(ValueError):
            build_schedule(0, 0, 12, EQUAL_PAYMENT, "2026-08")
        with pytest.raises(ValueError):
            build_schedule(100_00, 0, 0, EQUAL_PAYMENT, "2026-08")
        with pytest.raises(ValueError):
            build_schedule(100_00, 0, 12, "unknown", "2026-08")
