"""Pruebas de integración de autorización por rol sobre el API."""

import pytest
from fastapi.testclient import TestClient

from app.core.seed_data import DEMO_USERS

URL = "/api/v1/issues"
PASSWORDS = {u["username"]: u["password"] for u in DEMO_USERS}


def _headers(client: TestClient, username: str) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", json={"username": username, "password": PASSWORDS[username]}
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _new_issue(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post(URL, json={"title": "Incidencia", "priority": "low"}, headers=headers)
    return res.json()["id"]


@pytest.mark.parametrize(
    ("username", "role", "permissions"),
    [
        ("admin", "admin", ["issues:delete", "issues:resolve", "stats:view"]),
        ("soporte", "support", ["issues:delete", "issues:resolve", "stats:view"]),
        ("analista", "user", []),
    ],
)
def test_login_exposes_role_and_permissions(
    client: TestClient, username: str, role: str, permissions: list[str]
) -> None:
    res = client.post(
        "/api/v1/auth/login", json={"username": username, "password": PASSWORDS[username]}
    )
    user = res.json()["user"]
    assert user["role"] == role
    assert user["permissions"] == permissions


def test_regular_user_gets_403_on_privileged_operations(client: TestClient) -> None:
    user = _headers(client, "analista")
    issue_id = _new_issue(client, user)

    resolve = client.post(f"{URL}/{issue_id}/resolve", headers=user)
    complete = client.patch(f"{URL}/{issue_id}", json={"status": "completed"}, headers=user)
    delete = client.delete(f"{URL}/{issue_id}", headers=user)
    stats = client.get(f"{URL}/stats", headers=user)

    for res in (resolve, complete, delete, stats):
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "forbidden"
    # La incidencia sigue intacta
    assert client.get(f"{URL}/{issue_id}", headers=user).json()["status"] == "open"


def test_regular_user_can_still_work_the_issue(client: TestClient) -> None:
    user = _headers(client, "analista")
    issue_id = _new_issue(client, user)
    res = client.patch(
        f"{URL}/{issue_id}", json={"status": "in_progress", "priority": "high"}, headers=user
    )
    assert res.status_code == 200


@pytest.mark.parametrize("username", ["admin", "soporte"])
def test_privileged_user_resolves_and_deletes(client: TestClient, username: str) -> None:
    headers = _headers(client, username)
    issue_id = _new_issue(client, headers)

    resolved = client.post(f"{URL}/{issue_id}/resolve", headers=headers)
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "completed"

    assert client.delete(f"{URL}/{issue_id}", headers=headers).status_code == 204
    assert client.get(f"{URL}/{issue_id}", headers=headers).status_code == 404


def test_delete_unknown_issue_returns_404(client: TestClient) -> None:
    res = client.delete(f"{URL}/no-existe", headers=_headers(client, "admin"))
    assert res.status_code == 404


def test_stats_for_privileged_user(client: TestClient) -> None:
    headers = _headers(client, "soporte")
    _new_issue(client, headers)
    issue_id = _new_issue(client, headers)
    client.post(f"{URL}/{issue_id}/resolve", headers=headers)

    body = client.get(f"{URL}/stats", headers=headers).json()
    assert body["total"] == 2
    assert body["by_status"] == {"open": 1, "in_progress": 0, "completed": 1}
    assert body["by_priority"] == {"high": 0, "medium": 0, "low": 2}
    assert body["matrix"]["completed"]["low"] == 1


def test_cors_allows_delete_method(client: TestClient) -> None:
    res = client.options(
        f"{URL}/x",
        headers={"Origin": "http://localhost:4200", "Access-Control-Request-Method": "DELETE"},
    )
    assert res.status_code == 200
