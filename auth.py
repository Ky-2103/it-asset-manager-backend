import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
import bcrypt
import jwt
from jwt import InvalidTokenError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Asset, Ticket, User
from schemas import UserLogin, UserOut, UserRegister

router = APIRouter(tags=["Auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))


def bootstrap_initial_admin(db: Session) -> None:
    username = os.getenv("INITIAL_ADMIN_USERNAME")
    email = os.getenv("INITIAL_ADMIN_EMAIL")
    password = os.getenv("INITIAL_ADMIN_PASSWORD")

    if not username and not email and not password:
        return

    if not username or not email or not password:
        print(
            "Skipping initial admin bootstrap: set INITIAL_ADMIN_USERNAME, "
            "INITIAL_ADMIN_EMAIL, and INITIAL_ADMIN_PASSWORD together."
        )
        return

    username = username.strip()
    email = email.strip().lower()

    if len(password) < 8:
        print("Skipping initial admin bootstrap: INITIAL_ADMIN_PASSWORD must be at least 8 characters.")
        return

    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        return

    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()

    if existing_user:
        existing_user.role = "admin"
        existing_user.password_hash = hash_password(password)
        if existing_user.email != email:
            existing_user.email = email
        if existing_user.username != username:
            existing_user.username = username
        db.commit()
        print(f"Promoted existing user '{existing_user.username}' to initial admin.")
        return

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="admin",
    )
    db.add(user)
    db.commit()
    print(f"Created initial admin user '{username}'.")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="regular",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    print("Username:", payload.username)
    print("DB role value:", user.role if user else None)

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user)
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token") from None

    if not user_id or not str(user_id).isdigit():
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": f"User {current_user.username} logged out. Discard the access token on the client."}


def admin_required(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_assets = db.query(func.count(Asset.id)).scalar() or 0
        open_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == "Open").scalar() or 0
        return {
            "role": "admin",
            "totals": {
                "users": total_users,
                "assets": total_assets,
                "open_tickets": open_tickets,
            },
        }

    assigned_assets = db.query(Asset).filter(Asset.assigned_user_id == current_user.id).all()
    open_tickets = db.query(Ticket).filter(Ticket.created_by == current_user.id, Ticket.status == "Open").all()
    return {
        "role": "regular",
        "assigned_assets": [asset.asset_tag for asset in assigned_assets],
        "open_ticket_ids": [ticket.id for ticket in open_tickets],
    }
