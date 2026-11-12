"""Configuración local. Ningún secreto tiene un valor predeterminado."""

import base64
import binascii
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def load_settings():
    load_dotenv(ROOT / ".env", override=False)
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY", ""),
        "AES_KEY": os.getenv("AES_KEY", ""),
        "DATABASE": os.getenv("DATABASE_PATH", "instance/gestor.sqlite3"),
        "STORAGE_PATH": os.getenv("STORAGE_PATH", "storage/documents"),
        "ED25519_PRIVATE_KEY_PATH": os.getenv("ED25519_PRIVATE_KEY_PATH", "instance/keys/ed25519_private.pem"),
        "ED25519_PUBLIC_KEY_PATH": os.getenv("ED25519_PUBLIC_KEY_PATH", "instance/keys/ed25519_public.pem"),
        "MAX_UPLOAD_BYTES": os.getenv("MAX_UPLOAD_BYTES", "5242880"),
        "SESSION_COOKIE_SECURE": os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "DEBUG": False,
    }


def validate_settings(config):
    if not isinstance(config["SECRET_KEY"], str) or len(config["SECRET_KEY"].encode()) < 32:
        raise ValueError("SECRET_KEY debe tener al menos 32 bytes. Ejecuta: python scripts/setup_env.py")
    try:
        key = base64.b64decode(config["AES_KEY"], validate=True)
    except (ValueError, TypeError, binascii.Error):
        raise ValueError("AES_KEY debe ser Base64 válido de exactamente 32 bytes.") from None
    if len(key) != 32:
        raise ValueError("AES_KEY debe representar exactamente 32 bytes. Ejecuta: python scripts/setup_env.py")
    config["AES_KEY_BYTES"] = key
    try:
        size = int(config["MAX_UPLOAD_BYTES"])
    except (ValueError, TypeError):
        raise ValueError("MAX_UPLOAD_BYTES debe ser un entero positivo.") from None
    if not 1 <= size <= 50 * 1024 * 1024:
        raise ValueError("MAX_UPLOAD_BYTES debe estar entre 1 y 52428800.")
    config["MAX_UPLOAD_BYTES"] = size
    config["MAX_CONTENT_LENGTH"] = max(size + 64 * 1024, 512 * 1024)
    for name in ("DATABASE", "STORAGE_PATH", "ED25519_PRIVATE_KEY_PATH", "ED25519_PUBLIC_KEY_PATH"):
        path = Path(config[name]).expanduser()
        config[name] = str((path if path.is_absolute() else ROOT / path).resolve())
