from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import date, timedelta

from auth import hash_password
from database import SessionLocal, engine
from models import Asset, Base, Ticket, User


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(User).count() >= 10 and db.query(Asset).count() >= 10 and db.query(Ticket).count() >= 10:
            print("Seed data already exists (10+ records in each table).")
            return

        users: list[User] = []
        for i in range(1, 11):
            role = "admin" if i == 1 else "regular"
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password_hash=hash_password("password123"),
                role=role,
            )
            db.merge(user)
            users.append(user)

        db.commit()
        users = db.query(User).order_by(User.id).limit(10).all()

        statuses = ["Available", "Assigned", "Maintenance"]
        assets: list[Asset] = []
        for i in range(1, 11):
            status = statuses[(i - 1) % len(statuses)]
            assigned_user_id = users[i % len(users)].id if status == "Assigned" else None
            asset = Asset(
                asset_tag=f"AST-{1000 + i}",
                name=f"Laptop {i}",
                category="Laptop",
                purchase_date=date.today() - timedelta(days=i * 30),
                status=status,
                assigned_user_id=assigned_user_id,
            )
            db.merge(asset)
            assets.append(asset)

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
            db.merge(ticket)

        db.commit()
        print("Seeding complete: at least 10 users, 10 assets, 10 tickets available.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
