"""Generación explícita e irrepetible del par Ed25519 local."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_settings
from app.crypto.signatures import generate_keypair


def main():
    settings = load_settings()
    paths = []
    for name in ("ED25519_PRIVATE_KEY_PATH", "ED25519_PUBLIC_KEY_PATH"):
        path = Path(settings[name]).expanduser()
        paths.append(path if path.is_absolute() else ROOT / path)
    try:
        generate_keypair(*paths)
    except FileExistsError:
        print("Ya existe al menos una clave Ed25519. Se conservan sin cambios; no se regeneran.")
        return
    print("Par Ed25519 generado. Clave privada protegida con permisos del usuario local.")
    print("Las rutas están configuradas en .env. Conserva ambas claves para firmas futuras.")


if __name__ == "__main__":
    main()
