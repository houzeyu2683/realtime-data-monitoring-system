"""TC-USER-001 ~ TC-USER-007"""
from httpx import AsyncClient


async def test_TC_USER_001_admin_list_users(client: AsyncClient, admin_token, normal_user, viewer_user):
    r = await client.get("/api/v1/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 2


async def test_TC_USER_002_non_admin_list_users(client: AsyncClient, user_token):
    r = await client.get("/api/v1/users/", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


async def test_TC_USER_003_get_own_profile(client: AsyncClient, user_token, normal_user):
    r = await client.get(f"/api/v1/users/{normal_user.id}", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "normal_user"


async def test_TC_USER_004_get_other_profile_as_non_admin(client: AsyncClient, user_token, admin_user):
    r = await client.get(f"/api/v1/users/{admin_user.id}", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


async def test_TC_USER_005_admin_change_role(client: AsyncClient, admin_token, normal_user):
    r = await client.patch(
        f"/api/v1/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "viewer"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "viewer"


async def test_TC_USER_006_user_cannot_change_role(client: AsyncClient, user_token, normal_user):
    r = await client.patch(
        f"/api/v1/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"role": "admin"},
    )
    assert r.status_code == 403


async def test_TC_USER_007_admin_deactivate_user(client: AsyncClient, admin_token, normal_user):
    r = await client.patch(
        f"/api/v1/users/{normal_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False
