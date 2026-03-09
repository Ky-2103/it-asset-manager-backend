import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker


def _resolve_database_url() -> str:
    # In production, provide DATABASE_URL and that database is used as-is.
    # For local development, default to SQLite when DATABASE_URL is absent.
    return os.getenv("DATABASE_URL", "sqlite:///./dev.db")


DATABASE_URL = _resolve_database_url()

engine_kwargs = {"pool_pre_ping": True}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Fail fast when cold-start DB connection is unavailable.
    connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))
    url = make_url(DATABASE_URL)
    dialect = (url.get_backend_name() or "").lower()

    if "postgres" in dialect:
        engine_kwargs["connect_args"] = {"connect_timeout": connect_timeout}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
