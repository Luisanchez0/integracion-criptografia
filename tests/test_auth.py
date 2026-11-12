import sqlite3

import pytest
from werkzeug.security import check_password_hash

from conftest import csrf_token, login


def test_login_page_and_dashboard_require_session(client):
    assert client.get("/auth/login").status_code == 200
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_password_is_hashed(app):
    with sqlite3.connect(app.config["DATABASE"]) as db:
        stored = db.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()[0]
    assert stored != "Prueba-academica-42!"
    assert check_password_hash(stored, "Prueba-academica-42!")


def test_login_logout_and_no_public_registration(client):
    assert "Inicio" in login(client).get_data(as_text=True)
    response = client.post("/auth/logout", data={"csrf_token": csrf_token(client, "/")})
    assert response.status_code == 302
    assert client.get("/").status_code == 302
    assert client.get("/auth/register").status_code == 404
    assert client.get("/auth/logout").status_code == 405


def test_bad_login_is_generic_and_sql_is_parameterized(client):
    for username, password in [("admin", "incorrecta"), ("' OR 1=1 --", "x")]:
        response = login(client, username, password)
        assert "Usuario o contraseña incorrectos" in response.get_data(as_text=True)
        assert client.get("/").status_code == 302


def test_csrf_rejects_missing_token(client, logged_client):
    assert client.post("/auth/login", data={"username": "admin", "password": "x"}).status_code == 400
    assert logged_client.post("/auth/logout").status_code == 400


def test_login_ignores_external_next(client):
    response = client.post(
        "/auth/login?next=https://example.org/",
        data={"username": "admin", "password": "Prueba-academica-42!", "csrf_token": csrf_token(client)},
    )
    assert response.location == "/"


def test_init_db_preserves_existing_data(app):
    from app.database.db import get_db, init_db

    with app.app_context():
        init_db()
        assert get_db().execute("SELECT count(*) FROM users").fetchone()[0] == 2


def test_headers_and_session_cookie(logged_client):
    response = logged_client.get("/")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "HttpOnly" in response.headers.get("Set-Cookie", "")


@pytest.mark.parametrize("path", ["/no-existe", "/auth/register"])
def test_error_pages_do_not_expose_paths(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert "Traceback" not in response.get_data(as_text=True)
