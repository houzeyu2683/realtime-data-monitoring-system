import streamlit as st
import pandas as pd

from utils.auth import get_token, get_current_user, require_login
from utils import api_client

st.set_page_config(page_title="資料管理", page_icon="🗄️", layout="wide")
require_login()

token = get_token()
user = get_current_user()
can_edit = user.get("role") in ("admin", "user")

st.title("🗄️ 資料管理")

tab_list, tab_create, tab_import = st.tabs(["資料列表", "新增資料", "批量導入"])

with tab_list:
    col1, col2, col3 = st.columns(3)
    with col1:
        category_filter = st.text_input("分類篩選", key="list_cat")
    with col2:
        sort_by = st.selectbox("排序欄位", ["timestamp", "value", "category", "title"])
    with col3:
        sort_order = st.selectbox("排序方向", ["desc", "asc"])

    page = st.number_input("頁碼", min_value=1, value=1, step=1)

    params = {"page": page, "size": 20, "sort_by": sort_by, "sort_order": sort_order}
    if category_filter:
        params["category"] = category_filter

    try:
        result = api_client.list_records(token, **params)
        items = result["items"]
        total = result["total"]
        pages = result["pages"]
        st.caption(f"共 {total} 筆，第 {page}/{pages} 頁")

        if items:
            df = pd.DataFrame(items)
            display_cols = ["id", "title", "value", "category", "is_anomaly", "source", "timestamp"]
            st.dataframe(df[display_cols], use_container_width=True)

            if can_edit:
                st.subheader("編輯 / 刪除")
                record_id = st.number_input("輸入 Record ID", min_value=1, step=1, key="edit_id")
                action = st.radio("操作", ["編輯", "刪除"], horizontal=True)

                if action == "編輯":
                    with st.form("edit_form"):
                        new_title = st.text_input("Title")
                        new_value = st.number_input("Value", value=0.0)
                        new_category = st.text_input("Category")
                        submitted = st.form_submit_button("更新")
                    if submitted:
                        try:
                            payload = {}
                            if new_title:
                                payload["title"] = new_title
                            if new_value:
                                payload["value"] = new_value
                            if new_category:
                                payload["category"] = new_category
                            api_client.update_record(token, record_id, payload)
                            st.success("更新成功")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失敗：{e}")

                elif action == "刪除":
                    if st.button("確認刪除", type="primary"):
                        try:
                            api_client.delete_record(token, record_id)
                            st.success("刪除成功")
                            st.rerun()
                        except Exception as e:
                            st.error(f"刪除失敗：{e}")
        else:
            st.info("無資料")
    except Exception as e:
        st.error(f"載入失敗：{e}")

with tab_create:
    if not can_edit:
        st.warning("您沒有新增資料的權限")
    else:
        with st.form("create_form"):
            title = st.text_input("標題")
            value = st.number_input("數值", value=0.0)
            category = st.selectbox("分類", ["temperature", "humidity", "pressure", "cpu_load", "memory_usage", "network_io", "custom"])
            description = st.text_area("描述（選填）")
            threshold = st.number_input("告警閾值（選填，0 為不設定）", value=0.0)
            submitted = st.form_submit_button("新增")

        if submitted:
            try:
                payload = {
                    "title": title,
                    "value": value,
                    "category": category,
                    "description": description or None,
                    "threshold": threshold if threshold > 0 else None,
                }
                api_client.create_record(token, payload)
                st.success("新增成功！")
            except Exception as e:
                st.error(f"新增失敗：{e}")

with tab_import:
    if not can_edit:
        st.warning("您沒有導入資料的權限")
    else:
        st.markdown("CSV 格式：`title, value, category, description, threshold, timestamp`")
        uploaded = st.file_uploader("上傳 CSV 檔案", type=["csv"])
        if uploaded and st.button("開始導入"):
            try:
                result = api_client.import_csv(token, uploaded.read(), uploaded.name)
                st.success(f"成功導入 {result['imported']} 筆資料")
            except Exception as e:
                st.error(f"導入失敗：{e}")
