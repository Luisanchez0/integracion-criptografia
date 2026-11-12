"""Ed25519 firma los bytes exactos; no cifra documentos."""

import base64
import binascii
from pathlib import Path

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.local_files import restrict_permissions, write_private_file


def generate_keypair(private_path: Path, public_path: Path) -> None:
    private_path, public_path = Path(private_path), Path(public_path)
    if private_path.resolve() == public_path.resolve():
        raise ValueError("Las claves privada y pública requieren archivos distintos.")
    if private_path.exists() or public_path.exists():
        raise FileExistsError("Ya existe al menos una clave. No se sobrescribe ninguna.")
    if not private_path.parent.exists():
        private_path.parent.mkdir(parents=True)
        restrict_permissions(private_path.parent, directory=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public_pem = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    write_private_file(private_path, private_pem)
    try:
        with public_path.open("xb") as stream:
            stream.write(public_pem)
    except BaseException:
        private_path.unlink(missing_ok=True)
        raise


def load_keypair(private_path: Path, public_path: Path) -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    try:
        private_data, public_data = Path(private_path).read_bytes(), Path(public_path).read_bytes()
    except OSError:
        raise ValueError("Faltan claves Ed25519 o no se pueden leer. Ejecuta: python scripts/generate_keys.py") from None
    try:
        private = serialization.load_pem_private_key(private_data, password=None)
        public = serialization.load_pem_public_key(public_data)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise ValueError("Los archivos de claves Ed25519 no son válidos. Restaura el par original.") from None
    if not isinstance(private, Ed25519PrivateKey) or not isinstance(public, Ed25519PublicKey):
        raise ValueError("Ambas claves deben ser Ed25519.")
    expected = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    actual = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    if expected != actual:
        raise ValueError("Las claves Ed25519 no se corresponden. Restaura el par original.")
    return private, public


def sign_document(private_key: Ed25519PrivateKey, data: bytes) -> str:
    return base64.b64encode(private_key.sign(data)).decode("ascii")


def verify_document(public_key: Ed25519PublicKey, data: bytes, signature_b64: str) -> bool:
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        if len(signature) != 64:
            return False
        public_key.verify(signature, data)
        return True
    except (InvalidSignature, ValueError, TypeError, binascii.Error):
        return False
