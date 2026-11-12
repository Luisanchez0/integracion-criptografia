import io
import re
import sqlite3
from pathlib import Path

import pytest

from conftest import csrf_token, login

ORIGINAL = b"Comprobante FICTICIO: Proyecto Aurora, folio 2042.\n"


def upload(client, data=ORIGINAL, filename="comprobante.txt"):
    return client.post("/documents/new", data={"file": (io.BytesIO(data), filename), "csrf_token": csrf_token(client, "/documents/new")}, content_type="multipart/form-data")


def stored_document(app):
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM documents ORDER BY id DESC LIMIT 1").fetchone()


@pytest.mark.parametrize("path", ["/documents/", "/documents/new", "/documents/1", "/documents/1/download", "/documents/public-key"])
def test_documents_require_login(client, path):
    assert client.get(path).status_code == 302


def test_upload_sign_verify_download_and_public_key(app, logged_client):
    response = upload(logged_client)
    assert response.status_code == 302
    doc = stored_document(app)
    assert re.fullmatch(r"[a-f0-9]{32}\.txt", doc["storage_name"])
    assert doc["signature"]
    assert (Path(app.config["STORAGE_PATH"]) / doc["storage_name"]).read_bytes() == ORIGINAL
    url = f"/documents/{doc['id']}"
    verified = logged_client.post(url + "/verify", data={"csrf_token": csrf_token(logged_client, url)})
    assert verified.status_code == 200
    assert "Firma válida" in verified.get_data(as_text=True)
    downloaded = logged_client.get(url + "/download")
    assert downloaded.data == ORIGINAL
    assert "attachment" in downloaded.headers["Content-Disposition"]
    assert b"BEGIN PUBLIC KEY" in logged_client.get("/documents/public-key").data
    assert "PRIVATE" not in logged_client.get("/documents/public-key").get_data(as_text=True)


def test_current_file_changes_invalidate_signature(app, logged_client):
    upload(logged_client)
    doc = stored_document(app)
    path = Path(app.config["STORAGE_PATH"]) / doc["storage_name"]
    path.write_bytes(ORIGINAL + b"Cambio de prueba")
    url = f"/documents/{doc['id']}"
    response = logged_client.post(url + "/verify", data={"csrf_token": csrf_token(logged_client, url)})
    assert "Firma inválida" in response.get_data(as_text=True)
    assert stored_document(app)["last_verification"] == 0


def test_modified_copy_does_not_overwrite_original(app, logged_client):
    upload(logged_client)
    doc = stored_document(app)
    url = f"/documents/{doc['id']}"
    for content, result in [(ORIGINAL, "Firma válida"), (ORIGINAL + b"CAMBIO", "Firma inválida")]:
        response = logged_client.post(url + "/check-copy", data={"csrf_token": csrf_token(logged_client, url), "file": (io.BytesIO(content), "copia.txt")}, content_type="multipart/form-data")
        assert response.status_code == 200
        assert result in response.get_data(as_text=True)
    assert (Path(app.config["STORAGE_PATH"]) / doc["storage_name"]).read_bytes() == ORIGINAL
    assert len(list(Path(app.config["STORAGE_PATH"]).iterdir())) == 1
    assert stored_document(app)["last_verification"] is None


@pytest.mark.parametrize("filename,data", [("riesgo.exe", b"archivo"), ("vacio.txt", b""), ("exceso.txt", b"x" * 1025), ("falso.pdf", b"esto no es PDF"), ("binario.txt", b"\xff\x00")])
def test_reject_invalid_files_without_orphans(app, logged_client, filename, data):
    assert upload(logged_client, data, filename).status_code == 400
    assert stored_document(app) is None
    assert list(Path(app.config["STORAGE_PATH"]).iterdir()) == []


def test_secure_names_and_collision_avoidance(app, logged_client):
    assert upload(logged_client, filename="../../carpeta/prueba.txt").status_code == 302
    first = stored_document(app)
    assert "/" not in first["original_name"] and "\\" not in first["original_name"]
    assert upload(logged_client, filename="../../carpeta/prueba.txt").status_code == 302
    assert stored_document(app)["storage_name"] != first["storage_name"]


def test_other_user_cannot_access_or_verify(app, logged_client):
    upload(logged_client)
    doc_id = stored_document(app)["id"]
    other = app.test_client()
    login(other, "otro", "Otro-usuario-42!")
    url = f"/documents/{doc_id}"
    assert other.get(url).status_code == 404
    assert other.get(url + "/download").status_code == 404
    token = csrf_token(other, "/")
    assert other.post(url + "/verify", data={"csrf_token": token}).status_code == 404
    assert other.post(url + "/check-copy", data={"csrf_token": token, "file": (io.BytesIO(ORIGINAL), "x.txt")}).status_code == 404
    assert "comprobante.txt" not in other.get("/documents/").get_data(as_text=True)


def test_missing_file_and_unsafe_storage_reference_are_controlled(app, logged_client):
    upload(logged_client)
    doc = stored_document(app)
    url = f"/documents/{doc['id']}"
    (Path(app.config["STORAGE_PATH"]) / doc["storage_name"]).unlink()
    response = logged_client.post(url + "/verify", data={"csrf_token": csrf_token(logged_client, url)})
    assert response.status_code == 404
    assert app.config["STORAGE_PATH"] not in response.get_data(as_text=True)
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.execute("UPDATE documents SET storage_name = ? WHERE id = ?", ("../../.env", doc["id"]))
    assert logged_client.get(url + "/download").status_code == 404


def test_upload_and_verification_require_csrf(logged_client):
    assert logged_client.post("/documents/new", data={"file": (io.BytesIO(ORIGINAL), "x.txt")}).status_code == 400
    assert logged_client.post("/documents/1/verify").status_code == 400


def test_pdf_upload(app, logged_client):
    assert upload(logged_client, b"%PDF-1.4\n%Documento ficticio\n%%EOF", "muestra.PDF").status_code == 302
    assert stored_document(app)["storage_name"].endswith(".pdf")
