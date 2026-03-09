import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import get_db, router as auth_router
from models import Base
from routers.assets import router as assets_router
from routers.tickets import router as tickets_router
from routers.users import router as users_router


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def app(db_session):
    app = FastAPI()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(assets_router)
    app.include_router(tickets_router)
    return app


@pytest.fixture()
def client(app):
    return TestClient(app)

