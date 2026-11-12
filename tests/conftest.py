import base64
import re
import secrets

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def app(tmp_path, user_hashes, keypair_pem):
    from app import create_app
    from app.database.db import get_db, init_db

    (tmp_path / "private.pem").write_bytes(keypair_pem[0])
    (tmp_path / "public.pem").write_bytes(keypair_pem[1])
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": secrets.token_hex(32),
            "AES_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "STORAGE_PATH": str(tmp_path / "documents"),
            "ED25519_PRIVATE_KEY_PATH": str(tmp_path / "private.pem"),
            "ED25519_PUBLIC_KEY_PATH": str(tmp_path / "public.pem"),
            "MAX_UPLOAD_BYTES": 1024,
        },
        require_signing_keys=True,
    )
    with application.app_context():
        init_db()
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", user_hashes[0]),
        )
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("otro", user_hashes[1]),
        )
        db.commit()
    return application


@pytest.fixture(scope="session")
def user_hashes():
    return (generate_password_hash("Prueba-academica-42!"), generate_password_hash("Otro-usuario-42!"))


@pytest.fixture(scope="session")
def keypair_pem():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.generate()
    return (
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
        key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo),
    )


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_token(client, path="/auth/login"):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
    assert match, "La página debe incluir un token CSRF"
    return match.group(1)


def login(client, username="admin", password="Prueba-academica-42!"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password, "csrf_token": csrf_token(client)},
        follow_redirects=True,
    )


@pytest.fixture
def logged_client(client):
    response = login(client)
    assert response.status_code == 200
    return client
