"""tests/test_users_admin.py — integration tests for User Management endpoints."""

import pytest
from fastapi import status

from src.api.dependencies import get_current_user
from src.models.user import UserORM
from src.utils.auth import hash_password


@pytest.fixture()
def db_admin(db_session):
    admin = UserORM(
        username="admin_test",
        email="admin_test@test.com",
        hashed_password=hash_password("adminpassword123"),
        role="Admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture()
def db_editor(db_session):
    editor = UserORM(
        username="editor_test",
        email="editor_test@test.com",
        hashed_password=hash_password("editorpassword123"),
        role="Editor",
        is_active=True
    )
    db_session.add(editor)
    db_session.commit()
    db_session.refresh(editor)
    return editor


def test_list_users_as_admin(client, db_admin):
    """Admins can list all operators."""
    # We query the DB to get a fresh instance to avoid session conflicts
    client.app.dependency_overrides[get_current_user] = lambda: db_admin
    
    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["username"] == "admin_test"


def test_list_users_as_editor_forbidden(client, db_editor):
    """Non-admins (Editors/Viewers) are forbidden from listing operators."""
    client.app.dependency_overrides[get_current_user] = lambda: db_editor
    
    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_user_as_admin(client, db_admin):
    """Admins can create new operator accounts."""
    client.app.dependency_overrides[get_current_user] = lambda: db_admin
    
    payload = {
        "username": "new_operator",
        "email": "new@easyskill.com",
        "password": "securepassword123",
        "role": "Viewer"
    }
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "new_operator"
    assert data["role"] == "Viewer"
    assert data["is_active"] is True


def test_update_user_role_and_status(client, db_admin, db_editor):
    """Admins can update other users' roles and toggle active state."""
    client.app.dependency_overrides[get_current_user] = lambda: db_admin
    
    # Update db_editor's role and deactivate them
    update_payload = {
        "role": "Admin",
        "is_active": False
    }
    response = client.patch(f"/api/v1/users/{db_editor.id}", json=update_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["role"] == "Admin"
    assert data["is_active"] is False


def test_self_deactivation_prevented(client, db_admin):
    """Admins cannot deactivate their own active accounts."""
    client.app.dependency_overrides[get_current_user] = lambda: db_admin
    
    # Try deactivating the currently logged in admin user
    update_payload = {
        "is_active": False
    }
    response = client.patch(f"/api/v1/users/{db_admin.id}", json=update_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot deactivate" in response.json()["detail"].lower()
