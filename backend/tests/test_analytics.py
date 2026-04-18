"""TC-ANA-001 ~ TC-ANA-008"""
from httpx import AsyncClient

RECORD_PAYLOAD = {"title": "Sensor", "value": 50.0, "category": "temperature", "threshold": 80.0}
ANOMALY_PAYLOAD = {"title": "Anomaly", "value": 90.0, "category": "temperature", "threshold": 80.0}


async def _create_records(client, token, payloads):
    for p in payloads:
        await client.post("/api/v1/data/", headers={"Authorization": f"Bearer {token}"}, json=p)


async def test_TC_ANA_001_summary_fields(client: AsyncClient, user_token):
    await _create_records(client, user_token, [RECORD_PAYLOAD, ANOMALY_PAYLOAD])
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    summary = r.json()["summary"]
    for field in ["total", "avg_value", "max_value", "min_value", "anomaly_count"]:
        assert field in summary


async def test_TC_ANA_002_summary_time_range(client: AsyncClient, user_token):
    await _create_records(client, user_token, [RECORD_PAYLOAD])
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"start_time": "2020-01-01T00:00:00", "end_time": "2099-12-31T00:00:00"})
    assert r.status_code == 200
    assert r.json()["summary"]["total"] >= 1


async def test_TC_ANA_003_summary_filter_category(client: AsyncClient, user_token):
    await _create_records(client, user_token, [
        RECORD_PAYLOAD,
        {"title": "Humidity", "value": 60.0, "category": "humidity"},
    ])
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"category": "humidity"})
    assert r.status_code == 200
    assert r.json()["summary"]["total"] == 1


async def test_TC_ANA_004_category_aggregation(client: AsyncClient, user_token):
    await _create_records(client, user_token, [RECORD_PAYLOAD, ANOMALY_PAYLOAD])
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    categories = r.json()["categories"]
    assert len(categories) >= 1
    for cat in categories:
        assert "category" in cat
        assert "count" in cat
        assert "avg_value" in cat


async def test_TC_ANA_005_trend_hourly(client: AsyncClient, user_token):
    await _create_records(client, user_token, [RECORD_PAYLOAD])
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"trend_interval": "hour"})
    assert r.status_code == 200
    assert isinstance(r.json()["trend"], list)


async def test_TC_ANA_006_trend_daily(client: AsyncClient, user_token):
    await _create_records(client, user_token, [RECORD_PAYLOAD])
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"},
                         params={"trend_interval": "day"})
    assert r.status_code == 200
    assert isinstance(r.json()["trend"], list)


async def test_TC_ANA_007_export_excel(client: AsyncClient, user_token):
    await _create_records(client, user_token, [RECORD_PAYLOAD])
    r = await client.get("/api/v1/analytics/export/excel", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def test_TC_ANA_008_empty_db_summary(client: AsyncClient, user_token):
    r = await client.get("/api/v1/analytics/", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["total"] == 0
    assert summary["avg_value"] == 0
