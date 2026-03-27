from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False)


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=300)

    return _engine


def get_session_local() -> sessionmaker:
    if SessionLocal.kw.get("bind") is None:
        SessionLocal.configure(bind=get_engine())

    return SessionLocal
