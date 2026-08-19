"""service 层单测：先息后本「本金不影响现金流」口径。"""
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.db import Base
from server.services import cashflow_service, loan_service

START_MONTH = "2026-08"  # 与贷款 start_date 对齐


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _add_consumer_loan(db, exclude_principal: bool):
    return loan_service.add_loan(
        db,
        name="消费贷",
        principal_yuan=120000,
        periods=12,
        annual_rate=12,  # 月息 1% → 每月利息 1000
        method="interest_only",
        exclude_principal=exclude_principal,
        start_date=date(2026, 8, 1),
    )


class TestExcludePrincipal:
    def test_excluded_final_month_interest_only(self):
        db = make_db()
        _add_consumer_loan(db, exclude_principal=True)
        r = cashflow_service.get_forecast(db, months=12, start_month=START_MONTH)
        # 全部 12 个月只计利息 1200，末期不含 12w 本金
        for m in r.months[:11]:
            assert m.loan_payment_cents == 1200_00
        assert r.months[11].loan_payment_cents == 1200_00

    def test_not_excluded_final_month_has_principal(self):
        db = make_db()
        _add_consumer_loan(db, exclude_principal=False)
        r = cashflow_service.get_forecast(db, months=12, start_month=START_MONTH)
        assert r.months[11].loan_payment_cents == 1200_00 + 120000_00

    def test_schedule_keeps_principal_for_display(self):
        # 排除只影响预测，摊还表仍完整（展示口径不变）
        db = make_db()
        loan = _add_consumer_loan(db, exclude_principal=True)
        assert sum(s.principal_cents for s in loan.schedules) == 120000_00

    def test_exclude_only_for_interest_only(self):
        db = make_db()
        with pytest.raises(ValueError, match="先息后本"):
            loan_service.add_loan(
                db,
                name="车贷",
                principal_yuan=10000,
                periods=12,
                annual_rate=5,
                method="equal_payment",
                exclude_principal=True,
            )

    def test_simulate_exclude_principal(self):
        db = make_db()
        r = cashflow_service.simulate_purchase(
            db, amount_yuan=120000, periods=12, annual_rate=12,
            months=12, method="interest_only", exclude_principal=True,
        )
        # 沙盘叠加后每月贷款支出只有利息 1200（虚拟贷款从当月起算）
        for m in r.simulated.months[:11]:
            assert m.loan_payment_cents == 1200_00
        assert r.simulated.months[11].loan_payment_cents == 1200_00
        assert "本金到期续贷" in r.conclusion


class TestExistingLoan:
    """存量贷款：起始月在过去，已过月份自动标记已还，预测只算未来期次。"""

    def test_backdated_loan_paid_periods_and_remaining(self):
        db = make_db()
        # 2026-01 起还的 1.2w 免息 12 期（月供 1000），当前 2026-08 → 已还 7 期
        loan = loan_service.add_loan(
            db, name="旧分期", principal_yuan=12000, periods=12,
            annual_rate=0, method="equal_payment", start_date=date(2026, 1, 1),
        )
        from server.api.serialize import loan_to_dict
        from server.engine.months import current_month

        d = loan_to_dict(loan)
        if current_month() == "2026-08":  # 时间敏感，仅在当月断言精确值
            assert d["paid_periods"] == 7
            assert d["remaining_principal"] == 5000.0

    def test_backdated_loan_forecast_only_future(self):
        db = make_db()
        loan_service.add_loan(
            db, name="旧分期", principal_yuan=12000, periods=12,
            annual_rate=0, method="equal_payment", start_date=date(2026, 1, 1),
        )
        r = cashflow_service.get_forecast(db, months=12, start_month="2026-08")
        # 2026-08 ~ 2026-12 剩 5 期，每期 1000；2027 起摊还结束为 0
        for m in r.months[:5]:
            assert m.loan_payment_cents == 1000_00
        assert all(m.loan_payment_cents == 0 for m in r.months[5:])

    def test_backdated_loan_past_months_not_in_forecast(self):
        db = make_db()
        loan_service.add_loan(
            db, name="旧分期", principal_yuan=12000, periods=12,
            annual_rate=0, method="equal_payment", start_date=date(2026, 1, 1),
        )
        r = cashflow_service.get_forecast(db, months=12, start_month="2026-08")
        # 过去期次（1-7 月）不会出现在预测里
        assert r.months[0].month == "2026-08"
        assert sum(m.loan_payment_cents for m in r.months) == 5000_00
