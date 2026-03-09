from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="regular")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="assigned_user")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="creator")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_tag: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[date] = mapped_column(DateTime, default=datetime.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Available")
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    assigned_user: Mapped[User | None] = relationship("User", back_populates="assets")
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Open")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    asset: Mapped[Asset] = relationship("Asset", back_populates="tickets")
    creator: Mapped[User] = relationship("User", back_populates="tickets")
