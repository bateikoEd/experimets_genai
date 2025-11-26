from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_engine = None
_SessionLocal = None


def configure_engine(force: bool = False) -> None:
    global _engine, _SessionLocal
    if _engine is not None and not force:
        return
    settings = get_settings()
    _engine = create_engine(settings.database_url, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def get_session_factory():
    if _SessionLocal is None:
        configure_engine()
    return _SessionLocal


def get_engine():
    if _engine is None:
        configure_engine()
    return _engine


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager that provides a transactional scope."""

    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a session per request."""

    with session_scope() as session:
        yield session


def reset_connections() -> None:
    """Allow tests to rebuild the engine after overriding settings."""

    configure_engine(force=True)
