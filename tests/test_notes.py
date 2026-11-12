import base64
import html
import re
import sqlite3
from pathlib import Path

import pytest

from conftest import csrf_token, login

CONTENT = "MISIÓN-FICTICIA-729: muestra privada con acentos y espacios.\n  Final  "


def create_note(client, content=CONTENT, title="Mi nota de prueba"):
    return client.post("/notes/new", data={"title": title, "content": content, "csrf_token": csrf_token(client, "/notes/new")})


def stored_note(app):
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM notes ORDER BY rowid DESC LIMIT 1").fetchone()


@pytest.mark.parametrize("path", ["/notes/", "/notes/new", "/notes/inexistente", "/notes/inexistente/edit", "/notes/inexistente/delete"])
def test_notes_require_session(client, path):
    assert client.get(path).status_code == 302


def test_create_read_and_sqlite_is_encrypted(app, logged_client):
    response = create_note(logged_client)
    assert response.status_code == 302
    note = stored_note(app)
    assert CONTENT not in note["ciphertext"]
    assert CONTENT.encode() not in Path(app.config["DATABASE"]).read_bytes()
    assert len(base64.b64decode(note["nonce"])) == 12
    page = logged_client.get(response.location).get_data(as_text=True)
    assert CONTENT in page
    assert "Mi nota de prueba" in logged_client.get("/notes/").get_data(as_text=True)


def test_edit_reencrypts_and_delete_requires_confirmation(app, logged_client):
    create_note(logged_client)
    before = stored_note(app)
    url = f"/notes/{before['id']}"
    response = logged_client.post(url + "/edit", data={"title": "Título nuevo", "content": "Texto nuevo", "csrf_token": csrf_token(logged_client, url + "/edit")})
    assert response.status_code == 302
    after = stored_note(app)
    assert after["nonce"] != before["nonce"]
    assert after["ciphertext"] != before["ciphertext"]
    assert "Texto nuevo" in logged_client.get(url).get_data(as_text=True)
    assert logged_client.get(url + "/delete").status_code == 200
    assert stored_note(app) is not None
    token = csrf_token(logged_client, url + "/delete")
    assert logged_client.post(url + "/delete", data={"csrf_token": token}).status_code == 400
    assert logged_client.post(url + "/delete", data={"csrf_token": token, "confirm": "yes"}).status_code == 302
    assert stored_note(app) is None
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        assert conn.execute("SELECT count(*) FROM encryption_nonces").fetchone()[0] == 2


def test_other_user_cannot_access_note(app, logged_client):
    create_note(logged_client)
    note_id = stored_note(app)["id"]
    other = app.test_client()
    login(other, "otro", "Otro-usuario-42!")
    for suffix in ("", "/edit", "/delete"):
        assert other.get(f"/notes/{note_id}{suffix}").status_code == 404
    token = csrf_token(other, "/")
    for suffix in ("/edit", "/delete"):
        assert other.post(f"/notes/{note_id}{suffix}", data={"csrf_token": token, "confirm": "yes", "title": "x", "content": "x"}).status_code == 404
    assert "Mi nota de prueba" not in other.get("/notes/").get_data(as_text=True)


def test_tampered_note_is_controlled_error(app, logged_client):
    create_note(logged_client)
    note_id = stored_note(app)["id"]
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.execute("UPDATE notes SET ciphertext = ? WHERE id = ?", (base64.b64encode(b"alterado").decode(), note_id))
    response = logged_client.get(f"/notes/{note_id}")
    assert response.status_code == 422
    assert "No se pudo descifrar" in response.get_data(as_text=True)
    assert "Traceback" not in response.get_data(as_text=True)


@pytest.mark.parametrize("title,content", [(" ", "texto"), ("x" * 161, "texto"), ("título", " "), ("título", "x" * 100001)])
def test_server_validation(app, logged_client, title, content):
    assert create_note(logged_client, content, title).status_code == 400
    assert stored_note(app) is None


def test_csrf_required_and_html_escaped(app, logged_client):
    assert logged_client.post("/notes/new", data={"title": "x", "content": "x"}).status_code == 400
    response = create_note(logged_client, "<script>alert('x')</script>", "<b>Título</b>")
    page = logged_client.get(response.location).get_data(as_text=True)
    assert "<script>" not in page
    assert "&lt;script&gt;" in page


def test_nonce_collision_is_retried_without_reuse(app, logged_client, monkeypatch):
    from app.notes import routes

    create_note(logged_client)
    old = stored_note(app)
    actual_encrypt = routes.encrypt_note
    calls = []

    def collide_once(*args):
        calls.append(True)
        return (old["nonce"], old["ciphertext"]) if len(calls) == 1 else actual_encrypt(*args)

    monkeypatch.setattr(routes, "encrypt_note", collide_once)
    assert create_note(logged_client, "Otra nota").status_code == 302
    assert stored_note(app)["nonce"] != old["nonce"]
    assert len(calls) == 2


def test_edit_form_preserves_initial_newlines(logged_client):
    content = "\n\nNota que comienza con dos líneas vacías.\n"
    response = create_note(logged_client, content)
    page = logged_client.get(response.location + "/edit").get_data(as_text=True)
    raw = re.search(r'<textarea[^>]*>(.*?)</textarea>', page, re.DOTALL).group(1)
    # El parser HTML descarta el primer LF justo después de abrir textarea.
    browser_value = html.unescape(raw[1:] if raw.startswith("\n") else raw)
    assert browser_value == content
