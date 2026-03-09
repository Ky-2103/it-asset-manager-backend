# IT Asset Manager Backend

This project is a FastAPI backend for managing users, IT assets, and support tickets.

## Prerequisites

- Python 3.13+
- [Poetry](https://python-poetry.org/docs/)

## 1) Install dependencies

```bash
poetry install
```

## 2) Configure environment variables (optional but recommended)

Create a `.env` file in the project root (or export variables in your shell):

```env
# Database
DATABASE_URL=sqlite:///./dev.db

# JWT settings
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60

# Optional initial admin bootstrap (all 3 required together)
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=strongpassword123
```

Notes:
- If `DATABASE_URL` is not set, the app defaults to local SQLite at `dev.db`.
- Initial admin is created/promoted only when all three `INITIAL_ADMIN_*` values are provided.

## 3) Run the application

```bash
poetry run uvicorn main:app --reload
```

The API will be available at:
- App: http://127.0.0.1:8000
- Interactive docs (Swagger): http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc


## Deploying on Render (recommended settings)

If your Render service cold starts are very slow, the biggest issue is usually running Uvicorn in **reload** mode in production.

Use this start command instead:

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port $PORT
```

Do **not** use `--reload` on Render. `--reload` starts a file watcher and a supervisor process, which can noticeably increase startup time.

Also set:

- Health check path: `/health`
- `RUN_DB_CREATE_ALL_ON_STARTUP=false`
- `RUN_ADMIN_BOOTSTRAP_ON_STARTUP=false`

These avoid extra DB work during cold starts.

A sample `render.yaml` is included in this repo.

## 4) (Optional) Seed sample data

```bash
poetry run python scripts/seed_data.py
```

This script creates at least 10 users, 10 assets, and 10 tickets if data is missing.

You can also trigger seeding through the API (admin token required):

```bash
curl -X POST http://localhost:8000/seed \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

## Common development commands

```bash
# Run server
poetry run uvicorn main:app --reload

# Run data seed
poetry run python scripts/seed_data.py
```
