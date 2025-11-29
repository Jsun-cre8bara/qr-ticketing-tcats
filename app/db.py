from __future__ import annotations

import os
from functools import lru_cache
from typing import Generator

from pydantic import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class Settings(BaseSettings):
    """Application settings sourced from the environment."""

    database_url: str = os.getenv("DATABASE_URL", "")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


def _build_database_url(raw_url: str) -> str:
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not configured")

    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)

    if raw_url.startswith("postgresql://") and "+" not in raw_url:
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return raw_url


_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None or _SessionLocal is None:
        database_url = _build_database_url(get_settings().database_url)
        _engine = create_engine(database_url, pool_pre_ping=True, future=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_sessionmaker():
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session that is automatically closed."""

    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
