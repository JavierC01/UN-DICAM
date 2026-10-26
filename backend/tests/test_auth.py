import time
from uuid import uuid4

from fastapi.testclient import TestClient

from app.Core.security import crear_token, verificar_token
from app.main import app

CLAVE = "k" * 40


def test_token_valido_devuelve_el_usuario():
    assert verificar_token(crear_token("user-1", CLAVE, 5), CLAVE) == "user-1"


def test_token_alterado_expirado_o_con_otra_clave_se_rechaza(monkeypatch):
    token = crear_token("user-1", CLAVE, 5)
    header, payload, firma = token.split(".")
    assert verificar_token(f"{header}.{payload}.{firma[:-2]}xx", CLAVE) is None
    assert verificar_token(token, "otra" * 10) is None
    assert verificar_token("basura", CLAVE) is None

    monkeypatch.setattr(time, "time", lambda: 10**12)
    assert verificar_token(token, CLAVE) is None


def test_endpoints_protegidos_sin_token_dan_401():
    anonimo = TestClient(app)
    for ruta in ("/api/v1/projects", "/api/v1/devices/cameras", f"/api/v1/export/csv/{uuid4()}"):
        assert anonimo.get(ruta).status_code == 401
    assert anonimo.get("/api/v1/projects", headers={"Authorization": "Bearer x.y.z"}).status_code == 401


def test_login_emite_token_que_abre_los_endpoints():
    anonimo = TestClient(app)
    correo = f"{uuid4().hex}@test.co"
    assert anonimo.post("/api/v1/auth/register", json={"full_name": "A", "email": correo, "password": "secreto123"}).status_code == 201
    login = anonimo.post("/api/v1/auth/login", json={"email": correo, "password": "secreto123"})

    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer" and body["user"]["email"] == correo
    assert anonimo.get("/api/v1/projects", headers={"Authorization": f"Bearer {body['access_token']}"}).status_code == 200
    assert anonimo.get(f"/api/v1/projects?token={body['access_token']}").status_code == 200


def test_login_con_clave_incorrecta_da_401():
    anonimo = TestClient(app)
    assert anonimo.post("/api/v1/auth/login", json={"email": "nadie@x.co", "password": "malo"}).status_code == 401
