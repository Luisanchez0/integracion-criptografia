"""Genera .env una sola vez, sin mostrar secretos en consola."""

import base64
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.local_files import write_private_file


def main():
    target = ROOT / ".env"
    if target.exists():
        print(".env ya existe; se conserva sin cambios.")
        return
    template = (ROOT / ".env.example").read_text(encoding="utf-8")
    template = template.replace("SECRET_KEY=\n", f"SECRET_KEY={secrets.token_hex(32)}\n")
    template = template.replace("AES_KEY=\n", f"AES_KEY={base64.b64encode(secrets.token_bytes(32)).decode()}\n")
    write_private_file(target, template.encode("utf-8"))
    print(".env creado con secretos aleatorios y permisos restringidos. No lo compartas.")


if __name__ == "__main__":
    main()
