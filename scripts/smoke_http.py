"""Recorre los flujos reales por HTTP contra el servidor local en ejecución."""

import argparse
import base64
import http.cookiejar
import re
import secrets
import sqlite3
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_settings, validate_settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(path):
        with opener.open(base + path, timeout=15) as response:
            return response.read(), urlsplit(response.url).path

    def token(path):
        body, _ = get(path)
        match = re.search(rb'name="csrf_token" value="([^"]+)"', body)
        assert match, "Falta token CSRF"
        return match.group(1).decode()

    def post(path, data, filename=None, content=None):
        headers = {}
        if filename is None:
            payload = urlencode(data).encode()
        else:
            boundary = "Gestor" + secrets.token_hex(16)
            parts = []
            for key, value in data.items():
                parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: text/plain\r\n\r\n'.encode() + content + b"\r\n")
            parts.append(f"--{boundary}--\r\n".encode())
            payload = b"".join(parts)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        with opener.open(Request(base + path, data=payload, headers=headers), timeout=15) as response:
            return response.read().decode("utf-8"), urlsplit(response.url).path

    credentials = (ROOT / "instance/demo_credentials.txt").read_text(encoding="utf-8").splitlines()
    username = next(line.removeprefix("Usuario: ") for line in credentials if line.startswith("Usuario: "))
    password = next(line.removeprefix("Contraseña: ") for line in credentials if line.startswith("Contraseña: "))
    page, path = post("/auth/login", {"username": username, "password": password, "csrf_token": token("/auth/login")})
    assert path == "/" and "Cerrar sesión" in page
    print("OK: inicio de sesión HTTP con CSRF.")

    marker = "CONTENIDO-FICTICIO-HTTP-" + secrets.token_hex(8)
    page, note_url = post("/notes/new", {"title": "Nota ficticia HTTP", "content": marker, "csrf_token": token("/notes/new")})
    assert marker in page
    settings = load_settings()
    validate_settings(settings)
    with sqlite3.connect(settings["DATABASE"]) as db:
        row = db.execute("SELECT nonce, ciphertext FROM notes WHERE id = ?", (note_url.rsplit("/", 1)[1],)).fetchone()
    assert len(base64.b64decode(row[0])) == 12 and marker not in row[1]
    assert marker.encode() not in Path(settings["DATABASE"]).read_bytes()
    updated = marker + " / edición verificada"
    page, _ = post(note_url + "/edit", {"title": "Nota HTTP editada", "content": updated, "csrf_token": token(note_url + "/edit")})
    assert updated in page
    print("OK: crear, abrir y editar nota; consulta directa SQLite sin texto claro.")

    original = b"Comprobante FICTICIO HTTP: Proyecto Aurora, folio 2042.\n"
    page, doc_url = post("/documents/new", {"csrf_token": token("/documents/new")}, "comprobante_http_ficticio.txt", original)
    page, _ = post(doc_url + "/verify", {"csrf_token": token(doc_url)})
    assert "Firma válida" in page
    page, _ = post(doc_url + "/check-copy", {"csrf_token": token(doc_url)}, "copia_alterada.txt", original + b"CAMBIO FICTICIO")
    assert "Firma inválida" in page
    downloaded, _ = get(doc_url + "/download")
    assert downloaded == original
    print("OK: subir, firmar, verificar firma válida, rechazar copia alterada y descargar original intacto.")

    post(note_url + "/delete", {"csrf_token": token(note_url + "/delete"), "confirm": "yes"})
    try:
        get(note_url)
    except HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError("La nota de prueba no fue eliminada")
    for path in ("/static/css/app.css", "/static/vendor/bootstrap.min.css"):
        assert get(path)[0]
    page, path = post("/auth/logout", {"csrf_token": token("/")})
    assert path == "/auth/login" and "Iniciar sesión" in page
    assert get("/")[1] == "/auth/login"
    print("OK: eliminación confirmada, activos locales, logout y protección de rutas privadas.")
    print("La nota de prueba fue eliminada. Se conserva un comprobante ficticio firmado para la demostración.")


if __name__ == "__main__":
    main()
