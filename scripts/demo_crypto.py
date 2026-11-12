"""Demostración repetible con SQLite y archivos temporales, sin tocar datos reales."""

import base64
import secrets
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cryptography.exceptions import InvalidTag
from werkzeug.security import generate_password_hash

from app import create_app
from app.crypto.encryption import decrypt_note, encrypt_note, note_aad
from app.crypto.signatures import generate_keypair, sign_document, verify_document
from app.database.db import get_db, init_db


def main():
    cache = (ROOT / ".cache").resolve()
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="demo-crypto-", dir=cache) as folder:
        temporary = Path(folder).resolve()
        assert temporary.is_relative_to(cache)
        private_path, public_path = temporary / "keys/private.pem", temporary / "keys/public.pem"
        generate_keypair(private_path, public_path)
        key = secrets.token_bytes(32)
        app = create_app({
            "SECRET_KEY": secrets.token_hex(32),
            "AES_KEY": base64.b64encode(key).decode(),
            "DATABASE": str(temporary / "demo.sqlite3"),
            "STORAGE_PATH": str(temporary / "documents"),
            "ED25519_PRIVATE_KEY_PATH": str(private_path),
            "ED25519_PUBLIC_KEY_PATH": str(public_path),
        })
        with app.app_context():
            init_db()
            db = get_db()
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("demo-ficticio", generate_password_hash(secrets.token_urlsafe(24))))
            note_id = uuid.uuid4().hex
            text = "NOTA FICTICIA AURORA: reunión académica a las 10:30."
            aad = note_aad(note_id, 1)
            nonce, ciphertext = encrypt_note(key, text, aad)
            db.execute("INSERT INTO notes (id, user_id, title, nonce, ciphertext) VALUES (?, ?, ?, ?, ?)", (note_id, 1, "Demostración ficticia", nonce, ciphertext))
            db.commit()
            row = db.execute("SELECT nonce, ciphertext FROM notes WHERE id = ?", (note_id,)).fetchone()
            assert text not in row["ciphertext"]
            assert text.encode() not in Path(app.config["DATABASE"]).read_bytes()
            recovered = decrypt_note(key, row["nonce"], row["ciphertext"], aad)
            assert recovered == text
            print("AES-256-GCM / SQLite")
            print("  Nonce Base64 (12 bytes):", row["nonce"])
            print("  Ciphertext + tag Base64:", row["ciphertext"])
            print("  Texto claro ausente en SQLite; recuperación exacta: OK")
            try:
                decrypt_note(secrets.token_bytes(32), nonce, ciphertext, aad)
            except InvalidTag:
                print("  Llave incorrecta rechazada por autenticación GCM: OK")
            else:
                raise AssertionError("La llave incorrecta no fue rechazada")

            original = temporary / "documents/original_ficticio.txt"
            copy = temporary / "documents/copia_alterada.txt"
            original.write_bytes(b"Comprobante FICTICIO Aurora. Folio 2042.\n")
            private, public = app.extensions["ed25519"]
            signed_bytes = original.read_bytes()
            signature = sign_document(private, signed_bytes)
            copy.write_bytes(signed_bytes + b"CAMBIO DE PRUEBA\n")
            assert verify_document(public, original.read_bytes(), signature)
            assert not verify_document(public, copy.read_bytes(), signature)
            assert original.read_bytes() == signed_bytes
            print("Ed25519 / bytes exactos")
            print("  Archivo original: Firma válida")
            print("  Copia alterada: Firma inválida")
            print("  Archivo original conservado intacto: OK")
    print("Demostración terminada; los datos y claves temporales se retiraron.")


if __name__ == "__main__":
    main()
