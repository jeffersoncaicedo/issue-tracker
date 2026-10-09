"""Pruebas de integración de los endpoints de incidencias."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.container import Container
from app.core.exceptions import RepositoryError

URL = "/api/v1/issues"


def _create(client: TestClient, headers: dict[str, str], **overrides: str) -> dict:
    payload = {"title": "Falla en reporte", "description": "Detalle", "priority": "high"}
    payload.update(overrides)
    res = client.post(URL, json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_endpoints_require_authentication(client: TestClient) -> None:
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={}).status_code == 401
    assert client.get(f"{URL}/summary").status_code == 401
    assert client.patch(f"{URL}/x", json={"status": "open"}).status_code == 401


def test_create_issue(client: TestClient, auth_headers: dict[str, str]) -> None:
    issue = _create(client, auth_headers)
    assert issue["status"] == "open"
    assert issue["priority"] == "high"
    assert issue["created_by"] == "admin"


def test_create_issue_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.post(URL, json={"title": "ab", "priority": "urgent"}, headers=auth_headers)
    assert res.status_code == 422
    fields = {d["field"] for d in res.json()["error"]["details"]}
    assert {"title", "priority"} <= fields


def test_create_issue_rejects_unknown_fields(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    res = client.post(
        URL,
        json={"title": "Válido", "priority": "low", "status": "completed"},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_get_issue_and_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    issue = _create(client, auth_headers)
    assert client.get(f"{URL}/{issue['id']}", headers=auth_headers).status_code == 200
    res = client.get(f"{URL}/does-not-exist", headers=auth_headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"


def test_list_with_filters(client: TestClient, auth_headers: dict[str, str]) -> None:
    _create(client, auth_headers, title="Alta abierta", priority="high")
    low = _create(client, auth_headers, title="Baja", priority="low")
    client.patch(f"{URL}/{low['id']}", json={"status": "completed"}, headers=auth_headers)

    all_items = client.get(URL, headers=auth_headers).json()
    completed = client.get(URL, params={"status": "completed"}, headers=auth_headers).json()
    high = client.get(URL, params={"priority": "high"}, headers=auth_headers).json()

    assert len(all_items) == 2
    assert [i["title"] for i in completed] == ["Baja"]
    assert [i["title"] for i in high] == ["Alta abierta"]


def test_list_rejects_invalid_filter(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.get(URL, params={"status": "closed"}, headers=auth_headers)
    assert res.status_code == 422


def test_patch_status_and_priority(client: TestClient, auth_headers: dict[str, str]) -> None:
    issue = _create(client, auth_headers)
    res = client.patch(
        f"{URL}/{issue['id']}",
        json={"status": "in_progress", "priority": "low"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"
    assert res.json()["priority"] == "low"


def test_patch_requires_some_field(client: TestClient, auth_headers: dict[str, str]) -> None:
    issue = _create(client, auth_headers)
    res = client.patch(f"{URL}/{issue['id']}", json={}, headers=auth_headers)
    assert res.status_code == 422


def test_patch_unknown_issue(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.patch(f"{URL}/nope", json={"status": "completed"}, headers=auth_headers)
    assert res.status_code == 404


def test_summary(client: TestClient, auth_headers: dict[str, str]) -> None:
    a = _create(client, auth_headers)
    _create(client, auth_headers)
    client.patch(f"{URL}/{a['id']}", json={"status": "completed"}, headers=auth_headers)

    res = client.get(f"{URL}/summary", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"total": 2, "open": 1, "in_progress": 0, "completed": 1}


def test_persistence_failure_returns_503(
    client: TestClient, container: Container, auth_headers: dict[str, str]
) -> None:
    container.issues.list = AsyncMock(side_effect=RepositoryError())  # type: ignore[method-assign]
    res = client.get(URL, headers=auth_headers)
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "persistence_unavailable"


def test_unexpected_error_returns_generic_500(
    settings,
    container: Container,
    auth_headers: dict[str, str],  # noqa: ANN001
) -> None:
    from app.main import create_app

    container.issues.count_by_status = AsyncMock(side_effect=RuntimeError("secreto interno"))  # type: ignore[method-assign]
    with TestClient(create_app(settings, container), raise_server_exceptions=False) as c:
        res = c.get(f"{URL}/summary", headers=auth_headers)
    assert res.status_code == 500
    assert "secreto interno" not in res.text
