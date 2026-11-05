"""Persistence: scenarios and results in SQLite through SQLAlchemy 2 (ADR 008).

A scenario row keeps the parameters that rebuild its world. A result row keeps the whole
`ScenarioResult` as JSON, so the API and the precomputed files share one contract and a schema
change of the payload needs no table migration. Postgres works with the same models by changing
the URL.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

DEFAULT_DB_URL = "sqlite:///reshelf.db"


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


class ScenarioRow(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    spec: Mapped[dict[str, Any]] = mapped_column(JSON)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ResultRow(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), index=True)
    payload: Mapped[str] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


def make_engine(url: str | None = None) -> Engine:
    url = url or os.environ.get("RESHELF_DB", DEFAULT_DB_URL)
    if url == "sqlite://":  # in memory: one shared connection, so tables survive across sessions
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


def make_session_factory(engine: Engine) -> sessionmaker[Any]:
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)
