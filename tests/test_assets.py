from tests.helpers import auth_header_for, create_user


def test_admin_can_create_asset(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")

    res = client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={"asset_tag": "A-100", "name": "Laptop", "category": "Hardware", "status": "Available"},
    )
    assert res.status_code == 201
    assert res.json()["asset_tag"] == "A-100"


def test_non_admin_cannot_create_asset(client, db_session):
    user = create_user(db_session, "bob", "bob@example.com", role="regular")

    res = client.post(
        "/assets",
        headers=auth_header_for(user),
        json={"asset_tag": "A-101", "name": "Laptop", "category": "Hardware", "status": "Available"},
    )
    assert res.status_code == 403


def test_create_asset_assigned_requires_user(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")

    res = client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={"asset_tag": "A-102", "name": "Phone", "category": "Hardware", "status": "Assigned"},
    )
    assert res.status_code == 400


def test_update_asset_unassigns_when_status_not_assigned(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")
    assignee = create_user(db_session, "worker", "worker@example.com", role="regular")

    create_res = client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={
            "asset_tag": "A-103",
            "name": "Desktop",
            "category": "Hardware",
            "status": "Assigned",
            "assigned_user_id": assignee.id,
        },
    )
    asset_id = create_res.json()["id"]

    update_res = client.put(
        f"/assets/{asset_id}",
        headers=auth_header_for(admin),
        json={"status": "Maintenance"},
    )
    assert update_res.status_code == 200
    body = update_res.json()
    assert body["status"] == "Maintenance"
    assert body["assigned_user_id"] is None


def test_get_my_assets_only_returns_assigned_assets(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")
    user = create_user(db_session, "bob", "bob@example.com", role="regular")

    client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={
            "asset_tag": "A-104",
            "name": "Monitor",
            "category": "Hardware",
            "status": "Assigned",
            "assigned_user_id": user.id,
        },
    )
    client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={"asset_tag": "A-105", "name": "Keyboard", "category": "Hardware", "status": "Available"},
    )

    res = client.get("/assets/my", headers=auth_header_for(user))
    assert res.status_code == 200
    assets = res.json()
    assert len(assets) == 1
    assert assets[0]["asset_tag"] == "A-104"
