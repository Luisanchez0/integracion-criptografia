import base64
import secrets

import pytest
from cryptography.exceptions import InvalidTag

from app.crypto.encryption import decrypt_note, encrypt_note, note_aad


@pytest.mark.parametrize("text", ["", "Texto ficticio 42", "  Árbol, México 🔐\nSegunda línea  "])
def test_roundtrip_preserves_exact_text(text):
    key = secrets.token_bytes(32)
    aad = note_aad("nota-1", 1)
    nonce, ciphertext = encrypt_note(key, text, aad)
    assert len(base64.b64decode(nonce)) == 12
    assert len(base64.b64decode(ciphertext)) == len(text.encode()) + 16
    assert decrypt_note(key, nonce, ciphertext, aad) == text


def test_random_nonce_changes_ciphertext():
    key = secrets.token_bytes(32)
    results = {encrypt_note(key, "mismo texto", b"contexto") for _ in range(100)}
    assert len(results) == 100
    assert len({nonce for nonce, _ in results}) == 100


@pytest.mark.parametrize("alter", ["ciphertext", "nonce", "key", "aad", "base64"])
def test_tampering_and_wrong_key_fail(alter):
    key, aad = secrets.token_bytes(32), b"contexto"
    nonce, ciphertext = encrypt_note(key, "contenido privado", aad)
    if alter == "ciphertext":
        raw = bytearray(base64.b64decode(ciphertext))
        raw[0] ^= 1
        ciphertext = base64.b64encode(raw).decode()
    elif alter == "nonce":
        nonce = base64.b64encode(secrets.token_bytes(12)).decode()
    elif alter == "key":
        key = secrets.token_bytes(32)
    elif alter == "aad":
        aad = b"otro contexto"
    else:
        ciphertext = "no es base64!"
    with pytest.raises(InvalidTag):
        decrypt_note(key, nonce, ciphertext, aad)


def test_aes_requires_256_bit_key():
    with pytest.raises(ValueError):
        encrypt_note(secrets.token_bytes(16), "texto", b"contexto")
