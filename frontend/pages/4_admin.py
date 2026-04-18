import streamlit as st
import pandas as pd

from utils.auth import get_current_user, get_token, require_role
from utils import api_client

st.set_page_config(page_title="系統管理", page_icon="⚙️", layout="wide")
require_role("admin")

token = get_token()

st.title("⚙️ 系統管理（Admin）")

tab_users, tab_logs, tab_db = st.tabs(["使用者管理", "系統日誌", "資料庫狀態"])

with tab_users:
    try:
        users = api_client.list_users(token)
        df = pd.DataFrame(users)
        st.dataframe(df[["id", "username", "email", "role", "is_active", "created_at"]], use_container_width=True)

        st.subheader("修改使用者權限")
        with st.form("update_user_form"):
            user_id = st.number_input("User ID", min_value=1, step=1)
            new_role = st.selectbox("新角色", ["admin", "user", "viewer"])
            is_active = st.checkbox("啟用帳號", value=True)
            submitted = st.form_submit_button("更新")
        if submitted:
            try:
                api_client.update_user(token, user_id, {"role": new_role, "is_active": is_active})
                st.success("更新成功")
                st.rerun()
            except Exception as e:
                st.error(f"更新失敗：{e}")
    except Exception as e:
        st.error(f"載入使用者失敗：{e}")

with tab_logs:
    page = st.number_input("頁碼", min_value=1, value=1, step=1, key="log_page")
    try:
        result = api_client.get_logs(token, page=page, size=50)
        st.caption(f"共 {result['total']} 筆日誌，第 {page} 頁")
        df = pd.DataFrame(result["items"])
        if not df.empty:
            st.dataframe(df[["id", "action", "resource", "detail", "user_id", "ip_address", "created_at"]], use_container_width=True)
        else:
            st.info("無日誌資料")
    except Exception as e:
        st.error(f"載入日誌失敗：{e}")

with tab_db:
    try:
        status = api_client.get_db_status(token)
        st.metric("MariaDB 版本", status["db_version"])
        st.subheader("資料表狀態")
        st.dataframe(pd.DataFrame(status["tables"]), use_container_width=True)
    except Exception as e:
        st.error(f"載入資料庫狀態失敗：{e}")
