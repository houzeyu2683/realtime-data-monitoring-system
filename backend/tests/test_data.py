"""TC-DATA-001 ~ TC-DATA-015"""
import io
import pytest
from httpx import AsyncClient


VALID_PAYLOAD = {
    "title": "Test Record",
    "value": 50.0,
    "category": "temperature",
    "threshold": 80.0,
}


async def test_TC_DATA_001_user_create_record(client: AsyncClient, user_token):
    r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"}, json=VALID_PAYLOAD)
    assert r.status_code == 201
    assert r.json()["title"] == "Test Record"


async def test_TC_DATA_002_viewer_cannot_create_record(client: AsyncClient, viewer_token):
    r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {viewer_token}"}, json=VALID_PAYLOAD)
    assert r.status_code == 403


async def test_TC_DATA_003_list_records_pagination(client: AsyncClient, user_token):
    for i in range(5):
        await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                          json={**VALID_PAYLOAD, "title": f"Record {i}"})
    r = await client.get("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"page": 1, "size": 3})
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5


async def test_TC_DATA_004_filter_by_category(client: AsyncClient, user_token):
    await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                      json={**VALID_PAYLOAD, "category": "humidity"})
    await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                      json={**VALID_PAYLOAD, "category": "temperature"})
    r = await client.get("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"category": "humidity"})
    assert r.status_code == 200
    assert all(item["category"] == "humidity" for item in r.json()["items"])


async def test_TC_DATA_005_filter_by_time_range(client: AsyncClient, user_token):
    r = await client.get("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"start_time": "2020-01-01T00:00:00", "end_time": "2099-12-31T00:00:00"})
    assert r.status_code == 200


async def test_TC_DATA_006_sort_by_value_asc(client: AsyncClient, user_token):
    for v in [30.0, 10.0, 50.0]:
        await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                          json={**VALID_PAYLOAD, "value": v})
    r = await client.get("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"sort_by": "value", "sort_order": "asc"})
    values = [item["value"] for item in r.json()["items"]]
    assert values == sorted(values)


async def test_TC_DATA_007_owner_update_record(client: AsyncClient, user_token):
    create_r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"}, json=VALID_PAYLOAD)
    record_id = create_r.json()["id"]
    r = await client.patch(f"/api/v1/data/{record_id}", headers={"Authorization": f"Bearer {user_token}"},
                           json={"title": "Updated Title"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated Title"


async def test_TC_DATA_008_non_owner_cannot_update(client: AsyncClient, user_token, admin_token, normal_user):
    create_r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {admin_token}"}, json=VALID_PAYLOAD)
    record_id = create_r.json()["id"]
    r = await client.patch(f"/api/v1/data/{record_id}", headers={"Authorization": f"Bearer {user_token}"},
                           json={"title": "Hacked"})
    assert r.status_code == 403


async def test_TC_DATA_009_admin_update_any_record(client: AsyncClient, user_token, admin_token):
    create_r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"}, json=VALID_PAYLOAD)
    record_id = create_r.json()["id"]
    r = await client.patch(f"/api/v1/data/{record_id}", headers={"Authorization": f"Bearer {admin_token}"},
                           json={"title": "Admin Updated"})
    assert r.status_code == 200


async def test_TC_DATA_010_owner_delete_record(client: AsyncClient, user_token):
    create_r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"}, json=VALID_PAYLOAD)
    record_id = create_r.json()["id"]
    r = await client.delete(f"/api/v1/data/{record_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 204


async def test_TC_DATA_011_non_owner_cannot_delete(client: AsyncClient, user_token, admin_token):
    create_r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {admin_token}"}, json=VALID_PAYLOAD)
    record_id = create_r.json()["id"]
    r = await client.delete(f"/api/v1/data/{record_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


async def test_TC_DATA_012_delete_nonexistent_record(client: AsyncClient, user_token):
    r = await client.delete("/api/v1/data/99999", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 404


async def test_TC_DATA_013_anomaly_flag_when_above_threshold(client: AsyncClient, user_token):
    r = await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {user_token}"},
                          json={**VALID_PAYLOAD, "value": 90.0, "threshold": 80.0})
    assert r.status_code == 201
    assert r.json()["is_anomaly"] is True


async def test_TC_DATA_014_import_csv(client: AsyncClient, user_token):
    csv_content = (
        "title,value,category,description,threshold,timestamp\n"
        "Sensor A,72.5,temperature,,80.0,2026-04-18T08:00:00\n"
        "Sensor B,65.3,humidity,,90.0,2026-04-18T08:01:00\n"
    )
    r = await client.post(
        "/api/v1/data/import/csv",
        headers={"Authorization": f"Bearer {user_token}"},
        files={"file": ("test.csv", csv_content.encode(), "text/csv")},
    )
    assert r.status_code == 201
    assert r.json()["imported"] == 2


async def test_TC_DATA_015_import_json(client: AsyncClient, user_token):
    import json
    records = [
        {"title": "JSON Record 1", "value": 55.0, "category": "cpu_load"},
        {"title": "JSON Record 2", "value": 70.0, "category": "memory_usage"},
    ]
    r = await client.post(
        "/api/v1/data/import/json",
        headers={"Authorization": f"Bearer {user_token}"},
        files={"file": ("test.json", json.dumps(records).encode(), "application/json")},
    )
    assert r.status_code == 201
    assert r.json()["imported"] == 2
