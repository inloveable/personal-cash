"""SQLAlchemy 引擎与会话。SQLite 单文件，check_same_thread=False 适配 FastAPI 多线程。"""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    db_dir = os.path.dirname(os.path.abspath(settings.db_path))
    os.makedirs(db_dir, exist_ok=True)
    return create_engine(
        f"sqlite:///{settings.db_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """供 MCP 工具等非 DI 场景使用。"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401 确保模型已注册

    Base.metadata.create_all(engine)
    _migrate_add_columns()


def _migrate_add_columns() -> None:
    """轻量列迁移：老库补新列（个人项目量级，不引 alembic）。"""
    import sqlalchemy as sa

    with engine.begin() as conn:
        cols = {r[1] for r in conn.execute(sa.text("PRAGMA table_info(loans)"))}
        if cols and "exclude_principal" not in cols:
            conn.execute(
                sa.text("ALTER TABLE loans ADD COLUMN exclude_principal BOOLEAN NOT NULL DEFAULT 0")
            )
