from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import SessionLocal, engine
from models import Base
from seed import seed_database


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        result = seed_database(db)
        print(f"{result['message']}: users={result['users']}, assets={result['assets']}, tickets={result['tickets']}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
