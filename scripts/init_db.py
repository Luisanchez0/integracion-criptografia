"""Crea tablas y un administrador con contraseña local aleatoria."""

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from werkzeug.security import generate_password_hash

from app import create_app
from app.database.db import get_db, init_db
from app.local_files import write_private_file


def main():
    app = create_app(require_signing_keys=False)
    with app.app_context():
        init_db()
        db = get_db()
        if db.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone():
            print("La base de datos y el administrador ya existen. No se han modificado.")
            return
        password = secrets.token_urlsafe(18)
        credentials = ROOT / "instance" / "demo_credentials.txt"
        # Escribir primero evita crear una cuenta cuya contraseña no se pueda recuperar.
        write_private_file(credentials, f"Solo demostración académica local\nUsuario: admin\nContraseña: {password}\n".encode("utf-8"))
        try:
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", generate_password_hash(password)))
            db.commit()
        except BaseException:
            credentials.unlink(missing_ok=True)
            raise
        print("Base de datos inicializada. Usuario admin creado.")
        print("Consulta la contraseña local en instance/demo_credentials.txt; no se imprime en logs.")


if __name__ == "__main__":
    main()
