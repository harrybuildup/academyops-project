# tests/test_auth.py

import pytest
from fastapi import status
from src.utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from src.models.user import UserORM


def test_password_hashing():
    pwd = "secretpassword123"
    hashed = hash_password(pwd)
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_creation_and_decoding():
    data = {"sub": "john_doe", "role": "operator"}
    token = create_access_token(data, expires_minutes=1)
    
    assert token.count(".") == 2
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "john_doe"
    assert decoded["role"] == "operator"
    assert "exp" in decoded


def test_jwt_token_invalid_signature():
    token = create_access_token({"sub": "john_doe"})
    # Modify signature
    tampered_token = token[:-5] + "xxxxx"
    assert decode_access_token(tampered_token) is None


def test_api_auth_register_and_login(client):
    # Register user
    reg_payload = {
        "username": "new_operator",
        "email": "operator@easyskill.com",
        "password": "strongpassword123"
    }
    
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["username"] == "new_operator"
    
    # Try duplicate registration
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Login
    login_payload = {
        "username": "new_operator",
        "password": "strongpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_api_auth_login_invalid_credentials(client):
    login_payload = {
        "username": "admin",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_api_protected_route_without_token(db_engine):
    # Override get_db to prevent RuntimeError on missing DATABASE_URL in CI
    from fastapi.testclient import TestClient
    from src.api.app import create_app
    from src.database.connections import get_db
    from sqlalchemy.orm import sessionmaker
    
    TestingSession = sessionmaker(bind=db_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()
            
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    # get_current_user is NOT overridden to test actual authorization checks
    
    with TestClient(app) as c:
        response = c.get("/api/v1/leads")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
