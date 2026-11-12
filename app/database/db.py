"""Conexiones por solicitud y creación idempotente del esquema."""

import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    with current_app.open_resource("database/schema.sql") as schema:
        get_db().executescript(schema.read().decode("utf-8"))


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Crea las tablas faltantes sin borrar datos."""
        init_db()
        click.echo("Base de datos inicializada sin borrar registros existentes.")
