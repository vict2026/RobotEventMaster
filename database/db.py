"""数据库连接与会话管理"""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from database.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if config.DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            config.DATABASE_URL,
            echo=False,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized: %s", config.DATABASE_URL.split("@")[-1])


@contextmanager
def get_session():
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def write_audit_log(action, resource=None, detail=None, actor="system", ip_address=None):
    from database.models import AuditLog

    with get_session() as session:
        session.add(
            AuditLog(
                action=action,
                resource=resource,
                detail=detail,
                actor=actor,
                ip_address=ip_address,
            )
        )
