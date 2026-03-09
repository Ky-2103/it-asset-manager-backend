from tests.helpers import auth_header_for, create_user


def test_regular_user_ticket_permissions(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")
    user1 = create_user(db_session, "u1", "u1@example.com", role="regular")
    user2 = create_user(db_session, "u2", "u2@example.com", role="regular")

    asset_res = client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={"asset_tag": "A-200", "name": "Server", "category": "Infra", "status": "Available"},
    )
    asset_id = asset_res.json()["id"]

    ticket_res = client.post(
        "/tickets",
        headers=auth_header_for(user1),
        json={"asset_id": asset_id, "description": "Needs repair", "priority": "High"},
    )
    assert ticket_res.status_code == 201
    ticket_id = ticket_res.json()["id"]

    forbidden_update = client.put(
        f"/tickets/{ticket_id}",
        headers=auth_header_for(user2),
        json={"description": "I should not edit this"},
    )
    assert forbidden_update.status_code == 403

    bad_status_update = client.put(
        f"/tickets/{ticket_id}",
        headers=auth_header_for(user1),
        json={"status": "Closed"},
    )
    assert bad_status_update.status_code == 403


def test_admin_can_update_and_delete_ticket(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")
    user = create_user(db_session, "user", "user@example.com", role="regular")

    asset_id = client.post(
        "/assets",
        headers=auth_header_for(admin),
        json={"asset_tag": "A-201", "name": "Router", "category": "Network", "status": "Available"},
    ).json()["id"]

    ticket_id = client.post(
        "/tickets",
        headers=auth_header_for(user),
        json={"asset_id": asset_id, "description": "Packet loss", "priority": "Medium"},
    ).json()["id"]

    update_res = client.put(
        f"/tickets/{ticket_id}",
        headers=auth_header_for(admin),
        json={"status": "Closed", "description": "Resolved", "priority": "Low"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Closed"

    delete_res = client.delete(f"/tickets/{ticket_id}", headers=auth_header_for(admin))
    assert delete_res.status_code == 204


def test_user_admin_routes_and_duplicate_checks(client, db_session):
    admin = create_user(db_session, "admin", "admin@example.com", role="admin")
    user1 = create_user(db_session, "user1", "user1@example.com", role="regular")
    regular_user = create_user(db_session, "regular", "regular@example.com", role="regular")
    create_user(db_session, "taken", "taken@example.com", role="regular")

    list_res = client.get("/users", headers=auth_header_for(admin))
    assert list_res.status_code == 200
    assert len(list_res.json()) == 4

    dup_username = client.put(
        f"/users/{user1.id}",
        headers=auth_header_for(admin),
        json={"username": "taken"},
    )
    assert dup_username.status_code == 400

    update_role = client.put(
        f"/users/{user1.id}",
        headers=auth_header_for(admin),
        json={"role": "admin", "email": "newuser1@example.com"},
    )
    assert update_role.status_code == 200
    assert update_role.json()["role"] == "admin"

    regular_forbidden = client.get("/users", headers=auth_header_for(regular_user))
    assert regular_forbidden.status_code == 403
