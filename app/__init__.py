"""Factoría Flask de Gestor Seguro."""

import sqlite3
from pathlib import Path

from flask import Flask, g, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from config import load_settings, validate_settings

csrf = CSRFProtect()


def create_app(test_config=None, *, require_signing_keys=True):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(load_settings())
    if test_config:
        app.config.update(test_config)
    validate_settings(app.config)
    if require_signing_keys:
        from app.crypto.signatures import load_keypair
        app.extensions["ed25519"] = load_keypair(
            Path(app.config["ED25519_PRIVATE_KEY_PATH"]),
            Path(app.config["ED25519_PUBLIC_KEY_PATH"]),
        )
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["STORAGE_PATH"]).mkdir(parents=True, exist_ok=True)
    csrf.init_app(app)

    from app.database import db
    from app.auth.routes import bp as auth_bp, login_required

    db.init_app(app)
    app.register_blueprint(auth_bp)
    from app.notes.routes import bp as notes_bp
    app.register_blueprint(notes_bp)
    from app.documents.routes import bp as documents_bp
    app.register_blueprint(documents_bp)

    @app.context_processor
    def template_context():
        return {"current_app": app}

    @app.get("/")
    @login_required
    def dashboard():
        conn = db.get_db()
        notes_count = conn.execute("SELECT count(*) FROM notes WHERE user_id = ?", (g.user["id"],)).fetchone()[0]
        documents_count = conn.execute("SELECT count(*) FROM documents WHERE user_id = ?", (g.user["id"],)).fetchone()[0]
        return render_template("dashboard.html", notes_count=notes_count, documents_count=documents_count)

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; font-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("error.html", code=400, message="El formulario expiró o no es válido. Recarga la página e inténtalo de nuevo."), 400

    for code, message in {
        400: "La solicitud no es válida.",
        404: "No se encontró el recurso solicitado.",
        405: "Esta acción requiere enviar el formulario correspondiente.",
        413: "El archivo supera el tamaño permitido.",
        500: "No fue posible completar la operación. Inténtalo de nuevo.",
        503: "No fue posible completar la operación de forma segura. Inténtalo de nuevo.",
    }.items():
        def handler(error, code=code, message=message):
            return render_template("error.html", code=code, message=message), code
        app.register_error_handler(code, handler)

    @app.errorhandler(sqlite3.OperationalError)
    def database_error(error):
        return render_template("error.html", code=503, message="La base de datos no está disponible. Comprueba la inicialización local."), 503

    return app
