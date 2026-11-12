import base64
import secrets

import pytest


def settings(tmp_path):
    return {
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(32),
        "AES_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        "DATABASE": str(tmp_path / "config.sqlite3"),
        "STORAGE_PATH": str(tmp_path / "documents"),
    }


@pytest.mark.parametrize("value", ["", "no-base64!", base64.b64encode(b"corta").decode()])
def test_invalid_aes_key_fails_startup(tmp_path, value):
    from app import create_app

    config = settings(tmp_path)
    config["AES_KEY"] = value
    with pytest.raises(ValueError, match="AES_KEY"):
        create_app(config, require_signing_keys=False)


def test_secret_key_is_required(tmp_path):
    from app import create_app

    config = settings(tmp_path)
    config["SECRET_KEY"] = ""
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(config, require_signing_keys=False)


def test_debug_off_by_default(app):
    assert app.debug is False
    assert len(app.config["AES_KEY_BYTES"]) == 32


@pytest.mark.parametrize("value", [0, -1, "incorrecto", 52428801])
def test_invalid_upload_limit_fails_startup(tmp_path, value):
    from app import create_app

    config = settings(tmp_path)
    config["MAX_UPLOAD_BYTES"] = value
    with pytest.raises(ValueError, match="MAX_UPLOAD_BYTES"):
        create_app(config, require_signing_keys=False)


def test_missing_signing_keys_stop_normal_startup(tmp_path):
    from app import create_app

    config = settings(tmp_path)
    config["ED25519_PRIVATE_KEY_PATH"] = str(tmp_path / "missing-private.pem")
    config["ED25519_PUBLIC_KEY_PATH"] = str(tmp_path / "missing-public.pem")
    with pytest.raises(ValueError, match="python scripts/generate_keys.py"):
        create_app(config)
