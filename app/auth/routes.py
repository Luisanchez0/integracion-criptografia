"""Acceso básico sin registro público."""

from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.database.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")
# Igualar el coste de comprobar un nombre inexistente sin guardar contraseñas claras.
_DUMMY_HASH = generate_password_hash("valor-ficticio-no-utilizado-para-acceso")


@bp.before_app_request
def load_logged_user():
    user_id = session.get("user_id")
    g.user = None if user_id is None else get_db().execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = None
        if 1 <= len(username) <= 80 and 1 <= len(password) <= 256:
            user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        valid = check_password_hash(user["password_hash"] if user else _DUMMY_HASH, password[:256])
        if user is not None and valid:
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(url_for("dashboard"))
        flash("Usuario o contraseña incorrectos.", "danger")
    return render_template("login.html")


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("auth.login"))
