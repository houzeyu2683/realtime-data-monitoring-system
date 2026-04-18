import asyncio
import json
import os
import threading
import time
from collections import deque
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from utils.auth import get_token, require_login

st.set_page_config(page_title="即時監控", page_icon="📡", layout="wide")
require_login()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WS_URL = BACKEND_URL.replace("http://", "ws://").replace("https://", "wss://")

MAX_POINTS = 60

if "ws_data" not in st.session_state:
    st.session_state["ws_data"] = deque(maxlen=MAX_POINTS)
if "ws_running" not in st.session_state:
    st.session_state["ws_running"] = False


def ws_listener(token: str, data_queue: deque) -> None:
    import websockets

    async def _run() -> None:
        url = f"{WS_URL}/ws?token={token}"
        try:
            async with websockets.connect(url) as ws:
                while True:
                    msg = await ws.recv()
                    payload = json.loads(msg)
                    if payload.get("type") == "realtime_data":
                        data_queue.append(payload["data"])
        except Exception:
            pass

    asyncio.run(_run())


token = get_token()
if not st.session_state["ws_running"]:
    t = threading.Thread(target=ws_listener, args=(token, st.session_state["ws_data"]), daemon=True)
    t.start()
    st.session_state["ws_running"] = True

st.title("📡 即時監控 Dashboard")

placeholder = st.empty()

for _ in range(3600):
    data_list = list(st.session_state["ws_data"])

    with placeholder.container():
        if not data_list:
            st.info("等待即時資料中...")
        else:
            latest = data_list[-1]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("最新數值", f"{latest['value']:.2f}")
            col2.metric("分類", latest["category"])
            col3.metric("異常狀態", "⚠️ 異常" if latest["is_anomaly"] else "✅ 正常")
            col4.metric("資料點數", len(data_list))

            categories = list({d["category"] for d in data_list})
            selected_cat = st.selectbox("篩選分類", ["全部"] + categories, key="dash_cat")

            filtered = data_list if selected_cat == "全部" else [d for d in data_list if d["category"] == selected_cat]

            if filtered:
                times = [d["timestamp"] for d in filtered]
                values = [d["value"] for d in filtered]
                is_anomaly = [d["is_anomaly"] for d in filtered]

                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=times, y=values, mode="lines+markers", name="Value"))
                anomaly_times = [t for t, a in zip(times, is_anomaly) if a]
                anomaly_vals = [v for v, a in zip(values, is_anomaly) if a]
                if anomaly_times:
                    fig_line.add_trace(
                        go.Scatter(
                            x=anomaly_times, y=anomaly_vals,
                            mode="markers", marker=dict(color="red", size=10),
                            name="Anomaly",
                        )
                    )
                fig_line.update_layout(title="即時數值折線圖", height=350)
                st.plotly_chart(fig_line, use_container_width=True)

                cat_counts: dict = {}
                for d in data_list:
                    cat_counts[d["category"]] = cat_counts.get(d["category"], 0) + 1

                fig_bar = go.Figure(
                    go.Bar(x=list(cat_counts.keys()), y=list(cat_counts.values()), marker_color="steelblue")
                )
                fig_bar.update_layout(title="各分類資料筆數", height=300)
                st.plotly_chart(fig_bar, use_container_width=True)

    time.sleep(1)
    st.rerun()
