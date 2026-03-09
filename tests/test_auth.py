from auth import bootstrap_initial_admin, hash_password, verify_password
from models import User
from tests.helpers import auth_header_for, create_user


def test_hash_and_verify_password_roundtrip():
    hashed = hash_password("supersecret")
    assert hashed != "supersecret"
    assert verify_password("supersecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_register_and_login_flow(client):
    register_payload = {
        "username": "alice",
        "email": "ALICE@example.com",
        "password": "password123",
    }
    register_res = client.post("/register", json=register_payload)
    assert register_res.status_code == 201
    body = register_res.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["role"] == "regular"

    login_res = client.post("/login", json={"username": "alice", "password": "password123"})
    assert login_res.status_code == 200
    login_body = login_res.json()
    assert login_body["token_type"] == "bearer"
    assert login_body["user"]["username"] == "alice"


def test_protected_endpoint_requires_auth(client):
    response = client.get("/dashboard")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_dashboard_for_admin_and_regular(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")
    regular = create_user(db_session, "bob", "bob@example.com", role="regular")

    admin_res = client.get("/dashboard", headers=auth_header_for(admin))
    assert admin_res.status_code == 200
    admin_body = admin_res.json()
    assert admin_body["role"] == "admin"
    assert set(admin_body["totals"].keys()) == {"users", "assets", "open_tickets"}

    regular_res = client.get("/dashboard", headers=auth_header_for(regular))
    assert regular_res.status_code == 200
    regular_body = regular_res.json()
    assert regular_body["role"] == "regular"
    assert regular_body["assigned_assets"] == []
    assert regular_body["open_ticket_ids"] == []


def test_bootstrap_initial_admin_creates_admin(db_session, monkeypatch):
    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "root")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "root@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "password123")

    bootstrap_initial_admin(db_session)

    admin = db_session.query(User).filter(User.role == "admin").first()
    assert admin is not None
    assert admin.username == "root"


def test_bootstrap_initial_admin_promotes_existing_user(db_session, monkeypatch):
    existing = create_user(db_session, "root", "root@example.com", role="regular", password="oldpassword")

    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "root")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "root@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "password123")

    bootstrap_initial_admin(db_session)

    db_session.refresh(existing)
    assert existing.role == "admin"
    assert verify_password("password123", existing.password_hash) is True


def test_bootstrap_initial_admin_skips_short_password(db_session, monkeypatch):
    monkeypatch.setenv("INITIAL_ADMIN_USERNAME", "root")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "root@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "short")

    bootstrap_initial_admin(db_session)

    assert db_session.query(User).count() == 0
