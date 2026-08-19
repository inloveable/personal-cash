"""环境变量配置，fail-soft：本地开发给默认值并打印警告，生产必须显式设置。"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger("ai-ledger.config")


@dataclass(frozen=True)
class Settings:
    api_token: str
    db_path: str
    initial_balance_cents: int
    cors_origins: list[str] = field(default_factory=list)


def _parse_cents(env_name: str, default_yuan: float) -> int:
    raw = os.environ.get(env_name)
    if raw is None:
        return int(round(default_yuan * 100))
    try:
        return int(round(float(raw) * 100))
    except ValueError:
        raise SystemExit(f"[config] {env_name}={raw!r} 不是合法数字（单位：元）")


def load_settings() -> Settings:
    token = os.environ.get("API_TOKEN", "").strip()
    if not token:
        token = "dev-token"
        logger.warning("API_TOKEN 未设置，使用本地开发默认值 'dev-token'；部署到公网前务必通过环境变量设置强 token")

    db_path = os.environ.get("DB_PATH", "./data/ledger.db")

    cors_raw = os.environ.get("CORS_ORIGINS", "").strip()
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    return Settings(
        api_token=token,
        db_path=db_path,
        initial_balance_cents=_parse_cents("INITIAL_BALANCE", 0.0),
        cors_origins=cors_origins,
    )


settings = load_settings()
