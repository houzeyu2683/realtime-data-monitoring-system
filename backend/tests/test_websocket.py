"""TC-WS-001 ~ TC-WS-005"""
import json
import pytest
from httpx import AsyncClient
from httpx_ws import aconnect_ws


async def test_TC_WS_001_valid_token_connects(ws_client: AsyncClient, user_token):
    async with aconnect_ws(f"/ws?token={user_token}", ws_client) as ws:
        assert ws is not None


async def test_TC_WS_002_invalid_token_rejected(ws_client: AsyncClient):
    with pytest.raises(Exception):
        async with aconnect_ws("/ws?token=invalid.token", ws_client) as ws:
            await ws.receive_text()


async def test_TC_WS_003_receives_realtime_data(ws_client: AsyncClient, user_token):
    async with aconnect_ws(f"/ws?token={user_token}", ws_client) as ws:
        msg = await ws.receive_text()
        payload = json.loads(msg)
        assert payload["type"] == "realtime_data"


async def test_TC_WS_004_realtime_data_schema(ws_client: AsyncClient, user_token):
    async with aconnect_ws(f"/ws?token={user_token}", ws_client) as ws:
        msg = await ws.receive_text()
        data = json.loads(msg)["data"]
        assert "value" in data
        assert "category" in data
        assert "is_anomaly" in data
        assert "timestamp" in data


async def test_TC_WS_005_anomaly_detection(ws_client: AsyncClient, user_token):
    async with aconnect_ws(f"/ws?token={user_token}", ws_client) as ws:
        for _ in range(10):
            msg = await ws.receive_text()
            data = json.loads(msg)["data"]
            if data["is_anomaly"]:
                assert data["value"] > data["threshold"]
                return
