from datetime import datetime

from sqlalchemy.orm import Session

import bcrypt
from models import Asset, Ticket, User


def seed_database(db: Session) -> dict[str, int | str]:
    if db.query(User).count() >= 10 and db.query(Asset).count() >= 10 and db.query(Ticket).count() >= 10:
        return {
            "message": "Seed data already exists",
            "users": db.query(User).count(),
            "assets": db.query(Asset).count(),
            "tickets": db.query(Ticket).count(),
        }

    users: list[User] = []
    for i in range(1, 11):
        role = "admin" if i == 1 else "regular"
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            password_hash=bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            role=role,
        )
        db.add(user)
        users.append(user)

    db.commit()
    users = db.query(User).order_by(User.id).limit(10).all()

    statuses = ["Available", "Assigned", "Maintenance"]
    for i in range(1, 11):
        status = statuses[(i - 1) % len(statuses)]
        assigned_user_id = users[i % len(users)].id if status == "Assigned" else None
        asset = Asset(
            asset_tag=f"AST-{1000 + i}",
            name=f"Laptop {i}",
            category="Laptop",
            created_at=datetime.utcnow(),
            status=status,
            assigned_user_id=assigned_user_id,
        )
        db.add(asset)

    db.commit()
    assets = db.query(Asset).order_by(Asset.id).limit(10).all()

    priorities = ["Low", "Medium", "High"]
    ticket_statuses = ["Open", "In Progress", "Closed"]
    for i in range(1, 11):
        ticket = Ticket(
            asset_id=assets[(i - 1) % len(assets)].id,
            description=f"Issue report #{i}",
            priority=priorities[(i - 1) % len(priorities)],
            status=ticket_statuses[(i - 1) % len(ticket_statuses)],
            created_by=users[(i - 1) % len(users)].id,
        )
        db.add(ticket)

    db.commit()
    return {
        "message": "Seeding complete",
        "users": db.query(User).count(),
        "assets": db.query(Asset).count(),
        "tickets": db.query(Ticket).count(),
    }
