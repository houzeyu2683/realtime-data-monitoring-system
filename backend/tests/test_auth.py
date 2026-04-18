"""TC-AUTH-001 ~ TC-AUTH-009"""
import pytest
from httpx import AsyncClient


async def test_TC_AUTH_001_login_success(client: AsyncClient, normal_user):
    r = await client.post("/api/v1/auth/login", json={"username": "normal_user", "password": "password123"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


async def test_TC_AUTH_002_login_wrong_password(client: AsyncClient, normal_user):
    r = await client.post("/api/v1/auth/login", json={"username": "normal_user", "password": "wrongpass"})
    assert r.status_code == 401


async def test_TC_AUTH_003_login_nonexistent_user(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={"username": "ghost", "password": "password123"})
    assert r.status_code == 401


async def test_TC_AUTH_004_login_inactive_user(client: AsyncClient, db):
    from app.models.user import User, UserRole
    from app.core.security import hash_password
    user = User(
        username="inactive_user",
        email="inactive@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.USER,
        is_active=False,
    )
    db.add(user)
    await db.commit()

    r = await client.post("/api/v1/auth/login", json={"username": "inactive_user", "password": "password123"})
    assert r.status_code == 403


async def test_TC_AUTH_005_register_success(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "newuser@test.com",
        "password": "password123",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "newuser"
    assert data["role"] == "user"


async def test_TC_AUTH_006_register_duplicate_username(client: AsyncClient, normal_user):
    r = await client.post("/api/v1/auth/register", json={
        "username": "normal_user",
        "email": "other@test.com",
        "password": "password123",
    })
    assert r.status_code == 409


async def test_TC_AUTH_007_register_duplicate_email(client: AsyncClient, normal_user):
    r = await client.post("/api/v1/auth/register", json={
        "username": "other_user",
        "email": "normal_user@test.com",
        "password": "password123",
    })
    assert r.status_code == 409


async def test_TC_AUTH_008_get_me(client: AsyncClient, user_token):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "normal_user"


async def test_TC_AUTH_009_invalid_token(client: AsyncClient):
    r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401
