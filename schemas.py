from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

UserRole = Literal["admin", "regular"]
AssetStatus = Literal["Available", "Assigned", "Maintenance"]
TicketPriority = Literal["Low", "Medium", "High"]
TicketStatus = Literal["Open", "In Progress", "Closed"]


def _validate_email(value: str) -> str:
    candidate = value.strip()
    if "@" not in candidate or "." not in candidate.split("@")[-1]:
        raise ValueError("Invalid email format")
    return candidate.lower()


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8)


    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = None
    role: UserRole | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_email(value)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetBase(BaseModel):
    asset_tag: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    created_at: Optional[datetime] = Field(default=None)
    status: AssetStatus = "Available"
    assigned_user_id: int | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_tag: str | None = Field(default=None, min_length=2, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    created_at: Optional[datetime] = Field(default=None)
    status: AssetStatus | None = None
    assigned_user_id: int | None = None


class AssetOut(BaseModel):
    id: int
    asset_tag: str
    name: str
    category: str
    created_at: datetime
    status: AssetStatus
    assigned_user_id: int | None

    model_config = {"from_attributes": True}


class TicketCreate(BaseModel):
    asset_id: int
    description: str = Field(min_length=1)
    priority: TicketPriority


class TicketUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None


class TicketOut(BaseModel):
    id: int
    asset_id: int
    description: str
    priority: TicketPriority
    status: TicketStatus
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
