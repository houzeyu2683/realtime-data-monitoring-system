"""TC-ADM-001 ~ TC-ADM-006"""
from httpx import AsyncClient


async def test_TC_ADM_001_admin_get_logs(client: AsyncClient, admin_token):
    r = await client.get("/api/v1/admin/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data


async def test_TC_ADM_002_non_admin_cannot_get_logs(client: AsyncClient, user_token):
    r = await client.get("/api/v1/admin/logs", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


async def test_TC_ADM_003_logs_pagination(client: AsyncClient, admin_token):
    r = await client.get("/api/v1/admin/logs", headers={"Authorization": f"Bearer {admin_token}"},
                         params={"page": 1, "size": 50})
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["size"] == 50


async def test_TC_ADM_004_admin_get_db_status(client: AsyncClient, admin_token):
    r = await client.get("/api/v1/admin/db-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "db_version" in data
    assert "tables" in data


async def test_TC_ADM_005_login_written_to_log(client: AsyncClient, admin_token, normal_user):
    await client.post("/api/v1/auth/login", json={"username": "normal_user", "password": "password123"})
    r = await client.get("/api/v1/admin/logs", headers={"Authorization": f"Bearer {admin_token}"},
                         params={"size": 100})
    actions = [log["action"] for log in r.json()["items"]]
    assert "login" in actions


async def test_TC_ADM_006_register_written_to_log(client: AsyncClient, admin_token):
    await client.post("/api/v1/auth/register", json={
        "username": "log_test_user",
        "email": "logtest@test.com",
        "password": "password123",
    })
    r = await client.get("/api/v1/admin/logs", headers={"Authorization": f"Bearer {admin_token}"},
                         params={"size": 100})
    actions = [log["action"] for log in r.json()["items"]]
    assert "register" in actions
