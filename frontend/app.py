import streamlit as st

from utils.auth import do_login, do_logout, get_current_user, is_logged_in

st.set_page_config(page_title="監控系統", page_icon="📊", layout="wide")

if is_logged_in():
    user = get_current_user()
    st.sidebar.success(f"已登入：{user.get('username')} ({user.get('role')})")
    if st.sidebar.button("登出"):
        do_logout()
        st.rerun()
    st.title("📊 即時資料分析與監控系統")
    st.info("請從左側選單選擇功能頁面")
else:
    st.title("📊 即時資料分析與監控系統")
    tab_login, tab_register = st.tabs(["登入", "註冊"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("帳號")
            password = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("登入")
        if submitted:
            if do_login(username, password):
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("帳號或密碼錯誤")

    with tab_register:
        with st.form("register_form"):
            r_username = st.text_input("帳號", key="reg_username")
            r_email = st.text_input("Email", key="reg_email")
            r_password = st.text_input("密碼", type="password", key="reg_password")
            r_submitted = st.form_submit_button("註冊")
        if r_submitted:
            try:
                from utils.api_client import register as api_register
                api_register(r_username, r_email, r_password)
                st.success("註冊成功，請登入！")
            except Exception as e:
                st.error(f"註冊失敗：{e}")
