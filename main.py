import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import bootstrap_initial_admin, router as auth_router
from database import SessionLocal, engine
from models import Base
from routers.assets import router as assets_router
from routers.tickets import router as tickets_router
from routers.users import router as users_router


origins = [
    "https://it-asset-manager-frontend-kqxx.onrender.com",
    "https://localhost:5173",
]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


RUN_DB_CREATE_ALL_ON_STARTUP = _env_bool("RUN_DB_CREATE_ALL_ON_STARTUP", False)
RUN_ADMIN_BOOTSTRAP_ON_STARTUP = _env_bool("RUN_ADMIN_BOOTSTRAP_ON_STARTUP", False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Avoid slow cold-start DB work unless explicitly enabled.
    if RUN_DB_CREATE_ALL_ON_STARTUP:
        Base.metadata.create_all(bind=engine)

    if RUN_ADMIN_BOOTSTRAP_ON_STARTUP:
        with SessionLocal() as db:
            bootstrap_initial_admin(db)

    yield


app = FastAPI(title="IT Asset Manager Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(assets_router)
app.include_router(tickets_router)

