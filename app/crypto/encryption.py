"""AES-256-GCM: columnas Base64 nonce y ciphertext || tag de 16 bytes."""

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def note_aad(note_id: str, user_id: int) -> bytes:
    return f"gestor-seguro:note:v1:{user_id}:{note_id}".encode("utf-8")


def encrypt_note(key: bytes, content: str, aad: bytes) -> tuple[str, str]:
    if len(key) != 32:
        raise ValueError("AES-256 requiere una llave de 32 bytes.")
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, content.encode("utf-8"), aad)
    return base64.b64encode(nonce).decode("ascii"), base64.b64encode(ciphertext).decode("ascii")


def decrypt_note(key: bytes, nonce_b64: str, ciphertext_b64: str, aad: bytes) -> str:
    if len(key) != 32:
        raise ValueError("AES-256 requiere una llave de 32 bytes.")
    try:
        nonce = base64.b64decode(nonce_b64, validate=True)
        ciphertext = base64.b64decode(ciphertext_b64, validate=True)
        if len(nonce) != 12 or len(ciphertext) < 16:
            raise InvalidTag
        return AESGCM(key).decrypt(nonce, ciphertext, aad).decode("utf-8")
    except (ValueError, TypeError, binascii.Error, UnicodeDecodeError):
        raise InvalidTag from None
