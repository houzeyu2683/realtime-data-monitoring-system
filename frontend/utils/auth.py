import streamlit as st

from utils.api_client import get_me, login


def is_logged_in() -> bool:
    return bool(st.session_state.get("token"))


def get_token() -> str:
    return st.session_state.get("token", "")


def get_current_user() -> dict:
    return st.session_state.get("user", {})


def require_login() -> None:
    if not is_logged_in():
        st.warning("請先登入")
        st.stop()


def require_role(*roles: str) -> None:
    require_login()
    user = get_current_user()
    if user.get("role") not in roles:
        st.error("權限不足")
        st.stop()


def do_login(username: str, password: str) -> bool:
    try:
        data = login(username, password)
        token = data["access_token"]
        user = get_me(token)
        st.session_state["token"] = token
        st.session_state["user"] = user
        return True
    except Exception:
        return False


def do_logout() -> None:
    st.session_state.pop("token", None)
    st.session_state.pop("user", None)
