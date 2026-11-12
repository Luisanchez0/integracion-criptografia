import base64
import os

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.crypto.signatures import generate_keypair, load_keypair, sign_document, verify_document


def test_valid_signature_and_corresponding_public_key():
    private = Ed25519PrivateKey.generate()
    data = b"Documento academico ficticio\n\x00\xff"
    signature = sign_document(private, data)
    assert len(base64.b64decode(signature)) == 64
    assert verify_document(private.public_key(), data, signature)


@pytest.mark.parametrize("change", ["document", "signature", "public_key", "base64"])
def test_invalid_signature_is_rejected(change):
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    data = b"Documento original"
    signature = sign_document(private, data)
    if change == "document":
        data += b" MODIFICADO"
    elif change == "signature":
        raw = bytearray(base64.b64decode(signature))
        raw[0] ^= 1
        signature = base64.b64encode(raw).decode()
    elif change == "public_key":
        public = Ed25519PrivateKey.generate().public_key()
    else:
        signature = "invalida!"
    assert not verify_document(public, data, signature)


def test_persisted_keys_match_and_are_not_overwritten(tmp_path):
    private_path, public_path = tmp_path / "keys/private.pem", tmp_path / "keys/public.pem"
    generate_keypair(private_path, public_path)
    before = private_path.read_bytes(), public_path.read_bytes()
    private, public = load_keypair(private_path, public_path)
    assert verify_document(public, b"prueba", sign_document(private, b"prueba"))
    with pytest.raises(FileExistsError):
        generate_keypair(private_path, public_path)
    assert (private_path.read_bytes(), public_path.read_bytes()) == before
    if os.name != "nt":
        assert private_path.stat().st_mode & 0o777 == 0o600


def test_missing_keys_have_actionable_message(tmp_path):
    with pytest.raises(ValueError, match="python scripts/generate_keys.py"):
        load_keypair(tmp_path / "missing-private.pem", tmp_path / "missing-public.pem")


def test_mismatched_keypair_fails(tmp_path, keypair_pem):
    private_path, public_path = tmp_path / "private.pem", tmp_path / "public.pem"
    private_path.write_bytes(keypair_pem[0])
    from cryptography.hazmat.primitives import serialization
    other = Ed25519PrivateKey.generate().public_key()
    public_path.write_bytes(other.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    with pytest.raises(ValueError, match="corresponden"):
        load_keypair(private_path, public_path)


def test_malformed_keys_fail_without_exposing_pem(tmp_path):
    private, public = tmp_path / "private.pem", tmp_path / "public.pem"
    private.write_bytes(b"CONTENIDO-NO-ES-UNA-CLAVE")
    public.write_bytes(b"publica-invalida")
    with pytest.raises(ValueError, match="Ed25519") as caught:
        load_keypair(private, public)
    assert "CONTENIDO" not in str(caught.value)
