"""Pruebas de integración de los endpoints de autenticación."""

from fastapi.testclient import TestClient

LOGIN = "/api/v1/auth/login"


def test_login_ok(client: TestClient, demo_user: dict[str, str]) -> None:
    res = client.post(LOGIN, json={"username": "admin", "password": demo_user["password"]})
    body = res.json()
    assert res.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "admin"
    assert "password_hash" not in body["user"]


def test_login_wrong_password_returns_401_with_standard_error(client: TestClient) -> None:
    res = client.post(LOGIN, json={"username": "admin", "password": "nope"})
    assert res.status_code == 401
    assert res.headers["www-authenticate"] == "Bearer"
    assert res.json()["error"]["code"] == "invalid_credentials"


def test_login_validation_error(client: TestClient) -> None:
    res = client.post(LOGIN, json={"username": "a"})
    assert res.status_code == 422
    error = res.json()["error"]
    assert error["code"] == "validation_error"
    fields = {d["field"] for d in error["details"]}
    assert {"username", "password"} <= fields


def test_me_requires_token(client: TestClient) -> None:
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "not_authenticated"


def test_me_rejects_invalid_token(client: TestClient) -> None:
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401


def test_me_returns_current_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "admin"


def test_logout_invalidates_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401


def test_health_and_security_headers(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"


def test_cors_preflight_allows_configured_origin(client: TestClient) -> None:
    res = client.options(
        LOGIN,
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:4200"


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    res = client.options(
        LOGIN,
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in res.headers
