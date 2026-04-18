import os
from typing import Any, Optional

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _headers(token: Optional[str] = None) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def login(username: str, password: str) -> dict:
    r = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def register(username: str, email: str, password: str, role: str = "user") -> dict:
    r = requests.post(
        f"{BACKEND_URL}/api/v1/auth/register",
        json={"username": username, "email": email, "password": password, "role": role},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_me(token: str) -> dict:
    r = requests.get(f"{BACKEND_URL}/api/v1/auth/me", headers=_headers(token), timeout=10)
    r.raise_for_status()
    return r.json()


def list_records(token: str, **params: Any) -> dict:
    r = requests.get(f"{BACKEND_URL}/api/v1/data/", headers=_headers(token), params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def create_record(token: str, payload: dict) -> dict:
    r = requests.post(f"{BACKEND_URL}/api/v1/data/", headers=_headers(token), json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def update_record(token: str, record_id: int, payload: dict) -> dict:
    r = requests.patch(
        f"{BACKEND_URL}/api/v1/data/{record_id}", headers=_headers(token), json=payload, timeout=10
    )
    r.raise_for_status()
    return r.json()


def delete_record(token: str, record_id: int) -> None:
    r = requests.delete(f"{BACKEND_URL}/api/v1/data/{record_id}", headers=_headers(token), timeout=10)
    r.raise_for_status()


def import_csv(token: str, file_bytes: bytes, filename: str) -> dict:
    r = requests.post(
        f"{BACKEND_URL}/api/v1/data/import/csv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, file_bytes, "text/csv")},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def get_analytics(token: str, **params: Any) -> dict:
    r = requests.get(
        f"{BACKEND_URL}/api/v1/analytics/", headers=_headers(token), params=params, timeout=10
    )
    r.raise_for_status()
    return r.json()


def export_excel(token: str, **params: Any) -> bytes:
    r = requests.get(
        f"{BACKEND_URL}/api/v1/analytics/export/excel",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.content


def list_users(token: str) -> list:
    r = requests.get(f"{BACKEND_URL}/api/v1/users/", headers=_headers(token), timeout=10)
    r.raise_for_status()
    return r.json()


def update_user(token: str, user_id: int, payload: dict) -> dict:
    r = requests.patch(
        f"{BACKEND_URL}/api/v1/users/{user_id}", headers=_headers(token), json=payload, timeout=10
    )
    r.raise_for_status()
    return r.json()


def get_logs(token: str, page: int = 1, size: int = 50) -> dict:
    r = requests.get(
        f"{BACKEND_URL}/api/v1/admin/logs",
        headers=_headers(token),
        params={"page": page, "size": size},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_db_status(token: str) -> dict:
    r = requests.get(f"{BACKEND_URL}/api/v1/admin/db-status", headers=_headers(token), timeout=10)
    r.raise_for_status()
    return r.json()
