from auth import create_access_token, hash_password
from models import User


def create_user(db_session, username: str, email: str, role: str = "regular", password: str = "password123") -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_header_for(user: User) -> dict[str, str]:
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}
