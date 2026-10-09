"""Pruebas de Aceptación de Usuario (UAT) automatizadas.

Cada prueba reproduce una historia de usuario de punta a punta sobre el API,
con formato *Dado / Cuando / Entonces*. El detalle de los casos (incluida la
validación manual en la interfaz) está en ``docs/UAT.md``.
"""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.acceptance

API = "/api/v1"


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_hu01_iniciar_y_cerrar_sesion(client: TestClient) -> None:
    """HU-01: Como usuario quiero iniciar y cerrar sesión para proteger la información."""
    # Dado un usuario registrado
    # Cuando inicia sesión con credenciales válidas
    headers = _login(client, "analista", "Analista#2026")
    # Entonces puede acceder a las incidencias
    assert client.get(f"{API}/issues", headers=headers).status_code == 200
    # Cuando cierra sesión
    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 204
    # Entonces su token deja de ser válido
    assert client.get(f"{API}/issues", headers=headers).status_code == 401


def test_hu01_credenciales_invalidas(client: TestClient) -> None:
    """HU-01 (alterno): credenciales incorrectas no otorgan acceso."""
    res = client.post(f"{API}/auth/login", json={"username": "analista", "password": "x"})
    assert res.status_code == 401
    assert res.json()["error"]["message"] == "Usuario o contraseña incorrectos."


def test_hu02_hu03_crear_y_visualizar_incidencias(client: TestClient) -> None:
    """HU-02/HU-03: crear una incidencia con título, descripción y prioridad y verla listada."""
    headers = _login(client, "soporte", "Soporte#2026")
    # Cuando crea una incidencia
    created = client.post(
        f"{API}/issues",
        json={
            "title": "Impresora del piso 2 sin conexión",
            "description": "No responde desde las 9:00",
            "priority": "medium",
        },
        headers=headers,
    ).json()
    # Entonces aparece en el listado, en estado "abierto" y con su autor
    listed = client.get(f"{API}/issues", headers=headers).json()
    assert listed[0]["id"] == created["id"]
    assert listed[0]["status"] == "open"
    assert listed[0]["created_by"] == "soporte"


def test_hu04_actualizar_estado_y_prioridad(client: TestClient) -> None:
    """HU-04: actualizar el estado (abierto→en progreso→completado) y la prioridad."""
    headers = _login(client, "admin", "Admin#2026")
    issue = client.post(
        f"{API}/issues", json={"title": "Caída de VPN", "priority": "low"}, headers=headers
    ).json()

    for new_status in ("in_progress", "completed"):
        res = client.patch(
            f"{API}/issues/{issue['id']}", json={"status": new_status}, headers=headers
        )
        assert res.json()["status"] == new_status

    res = client.patch(f"{API}/issues/{issue['id']}", json={"priority": "high"}, headers=headers)
    assert res.json()["priority"] == "high"
    assert res.json()["status"] == "completed"


def test_hu05_filtrar_por_estado_o_prioridad(client: TestClient) -> None:
    """HU-05: filtrar incidencias por estado o por prioridad."""
    headers = _login(client, "admin", "Admin#2026")
    ids = {}
    for title, priority in (("A", "high"), ("B", "low"), ("C", "high")):
        ids[title] = client.post(
            f"{API}/issues", json={"title": f"Inc {title}", "priority": priority}, headers=headers
        ).json()["id"]
    client.patch(f"{API}/issues/{ids['C']}", json={"status": "in_progress"}, headers=headers)

    high = client.get(f"{API}/issues?priority=high", headers=headers).json()
    in_progress = client.get(f"{API}/issues?status=in_progress", headers=headers).json()

    assert {i["title"] for i in high} == {"Inc A", "Inc C"}
    assert [i["title"] for i in in_progress] == ["Inc C"]


def test_hu06_resumen_por_estado(client: TestClient) -> None:
    """HU-06: ver el total de incidencias y la cantidad por cada estado."""
    headers = _login(client, "admin", "Admin#2026")
    created = [
        client.post(
            f"{API}/issues", json={"title": f"Inc {n}", "priority": "low"}, headers=headers
        ).json()
        for n in range(4)
    ]
    client.patch(
        f"{API}/issues/{created[0]['id']}", json={"status": "in_progress"}, headers=headers
    )
    client.patch(f"{API}/issues/{created[1]['id']}", json={"status": "completed"}, headers=headers)
    client.patch(f"{API}/issues/{created[2]['id']}", json={"status": "completed"}, headers=headers)

    summary = client.get(f"{API}/issues/summary", headers=headers).json()
    assert summary == {"total": 4, "open": 1, "in_progress": 1, "completed": 2}
    assert summary["open"] + summary["in_progress"] + summary["completed"] == summary["total"]


def test_hu07_soporte_resuelve_y_elimina(client: TestClient) -> None:
    """HU-07: Como Soporte/Administrador quiero dar por resuelto o eliminar un ticket."""
    usuario = _login(client, "analista", "Analista#2026")
    soporte = _login(client, "soporte", "Soporte#2026")
    # Dado un ticket reportado por un usuario normal
    ticket = client.post(
        f"{API}/issues", json={"title": "Sin acceso al correo", "priority": "high"}, headers=usuario
    ).json()
    # Cuando el usuario normal intenta cerrarlo, Entonces el sistema lo impide
    assert client.post(f"{API}/issues/{ticket['id']}/resolve", headers=usuario).status_code == 403
    # Cuando Soporte lo da por resuelto, Entonces queda completado
    res = client.post(f"{API}/issues/{ticket['id']}/resolve", headers=soporte)
    assert res.json()["status"] == "completed"
    # Y el usuario normal ya no puede modificarlo
    reopen = client.patch(f"{API}/issues/{ticket['id']}", json={"status": "open"}, headers=usuario)
    assert reopen.status_code == 403
    # Cuando Soporte lo elimina, Entonces desaparece del listado
    assert client.delete(f"{API}/issues/{ticket['id']}", headers=soporte).status_code == 204
    assert client.get(f"{API}/issues", headers=soporte).json() == []


def test_hu08_vista_de_resumen_solo_para_privilegiados(client: TestClient) -> None:
    """HU-08: Como Administrador quiero una vista de resumen por estado y prioridad."""
    admin = _login(client, "admin", "Admin#2026")
    usuario = _login(client, "analista", "Analista#2026")
    for priority in ("high", "high", "low"):
        client.post(f"{API}/issues", json={"title": "Ticket", "priority": priority}, headers=admin)

    stats = client.get(f"{API}/issues/stats", headers=admin).json()
    assert stats["total"] == 3
    assert stats["by_priority"]["high"] == 2
    assert sum(stats["by_status"].values()) == stats["total"]
    assert client.get(f"{API}/issues/stats", headers=usuario).status_code == 403
