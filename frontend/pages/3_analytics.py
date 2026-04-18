from datetime import datetime, timedelta

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from utils.auth import get_token, require_login
from utils import api_client

st.set_page_config(page_title="資料分析", page_icon="📈", layout="wide")
require_login()

token = get_token()

st.title("📈 資料分析")

with st.sidebar:
    st.subheader("篩選條件")
    start_date = st.date_input("開始日期", value=datetime.today() - timedelta(days=7))
    end_date = st.date_input("結束日期", value=datetime.today())
    category_filter = st.text_input("分類（空白=全部）")
    interval = st.selectbox("趨勢區間", ["hour", "day"])
    apply = st.button("套用")

params: dict = {
    "start_time": datetime.combine(start_date, datetime.min.time()).isoformat(),
    "end_time": datetime.combine(end_date, datetime.max.time()).isoformat(),
    "trend_interval": interval,
}
if category_filter:
    params["category"] = category_filter

try:
    data = api_client.get_analytics(token, **params)
    summary = data["summary"]
    categories = data["categories"]
    trend = data["trend"]

    st.subheader("統計摘要")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("總筆數", summary["total"])
    c2.metric("加總", f"{summary['total_value']:.2f}")
    c3.metric("平均", f"{summary['avg_value']:.2f}")
    c4.metric("最大值", f"{summary['max_value']:.2f}")
    c5.metric("最小值", f"{summary['min_value']:.2f}")
    c6.metric("異常筆數", summary["anomaly_count"])

    col_left, col_right = st.columns(2)

    with col_left:
        if trend:
            trend_df = pd.DataFrame(trend)
            fig = px.line(trend_df, x="timestamp", y="avg_value", title="數值趨勢（平均）")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("無趨勢資料")

    with col_right:
        if categories:
            cat_df = pd.DataFrame(categories)
            fig = px.bar(cat_df, x="category", y="total_value", title="各分類加總", color="category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("無分類資料")

    if categories:
        st.subheader("分類聚合明細")
        st.dataframe(pd.DataFrame(categories), use_container_width=True)

    st.subheader("匯出資料")
    if st.button("下載 Excel"):
        try:
            content = api_client.export_excel(token, **{k: v for k, v in params.items() if k != "trend_interval"})
            st.download_button(
                label="點此下載",
                data=content,
                file_name="data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            st.error(f"匯出失敗：{e}")

except Exception as e:
    st.error(f"載入分析資料失敗：{e}")
