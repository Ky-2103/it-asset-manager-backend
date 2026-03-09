import pytest
from pydantic import ValidationError

from schemas import UserRegister, UserUpdate


def test_user_register_normalizes_email():
    payload = UserRegister(username="alice", email="  ALICE@EXAMPLE.COM ", password="password123")
    assert payload.email == "alice@example.com"


def test_user_register_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserRegister(username="alice", email="invalid", password="password123")


def test_user_update_allows_none_email_and_normalizes_when_present():
    payload = UserUpdate(email=None)
    assert payload.email is None

    payload2 = UserUpdate(email="  NEW@EXAMPLE.COM  ")
    assert payload2.email == "new@example.com"
