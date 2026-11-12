"""CRUD de notas: el contenido nunca se escribe claro en SQLite."""

import hashlib
import uuid

from cryptography.exceptions import InvalidTag
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from app.auth.routes import login_required
from app.crypto.encryption import decrypt_note, encrypt_note, note_aad
from app.database.db import get_db

bp = Blueprint("notes", __name__, url_prefix="/notes")


def get_note(note_id):
    note = get_db().execute("SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, g.user["id"])).fetchone()
    if note is None:
        abort(404)
    return note


def encrypted_content(note_id, content):
    key = current_app.config["AES_KEY_BYTES"]
    key_id = hashlib.sha256(key).hexdigest()
    for _ in range(5):
        nonce, ciphertext = encrypt_note(key, content, note_aad(note_id, g.user["id"]))
        inserted = get_db().execute("INSERT OR IGNORE INTO encryption_nonces (key_id, nonce) VALUES (?, ?)", (key_id, nonce))
        if inserted.rowcount == 1:
            return nonce, ciphertext
    # No se utiliza ningún nonce repetido aunque la fuente aleatoria fallara.
    get_db().rollback()
    abort(503)


def decrypt(note):
    try:
        return decrypt_note(current_app.config["AES_KEY_BYTES"], note["nonce"], note["ciphertext"], note_aad(note["id"], g.user["id"]))
    except InvalidTag:
        return None


def validate_note():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "")
    error = None
    if not 1 <= len(title) <= 160:
        error = "El título debe tener entre 1 y 160 caracteres."
    elif not content.strip() or len(content) > 100000:
        error = "El contenido debe tener entre 1 y 100 000 caracteres y no puede estar vacío."
    return title, content, error


def decryption_error():
    return render_template("error.html", code=422, message="No se pudo descifrar la nota. La llave no corresponde o el contenido fue alterado."), 422


@bp.get("/")
@login_required
def list_notes():
    notes = get_db().execute("SELECT id, title, created_at, updated_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC, rowid DESC", (g.user["id"],)).fetchall()
    return render_template("notes/list.html", notes=notes)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    title, content = "", ""
    if request.method == "POST":
        title, content, error = validate_note()
        if error:
            flash(error, "danger")
            return render_template("notes/form.html", note=None, title=title, content=content), 400
        note_id = uuid.uuid4().hex
        nonce, ciphertext = encrypted_content(note_id, content)
        get_db().execute("INSERT INTO notes (id, user_id, title, ciphertext, nonce) VALUES (?, ?, ?, ?, ?)", (note_id, g.user["id"], title, ciphertext, nonce))
        get_db().commit()
        flash("Nota creada y cifrada correctamente.", "success")
        return redirect(url_for("notes.detail", note_id=note_id))
    return render_template("notes/form.html", note=None, title=title, content=content)


@bp.get("/<note_id>")
@login_required
def detail(note_id):
    note = get_note(note_id)
    content = decrypt(note)
    if content is None:
        return decryption_error()
    return render_template("notes/detail.html", note=note, content=content)


@bp.route("/<note_id>/edit", methods=["GET", "POST"])
@login_required
def edit(note_id):
    note = get_note(note_id)
    content = decrypt(note)
    if content is None:
        return decryption_error()
    title = note["title"]
    if request.method == "POST":
        title, content, error = validate_note()
        if error:
            flash(error, "danger")
            return render_template("notes/form.html", note=note, title=title, content=content), 400
        nonce, ciphertext = encrypted_content(note_id, content)
        get_db().execute("UPDATE notes SET title = ?, ciphertext = ?, nonce = ?, updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now') WHERE id = ? AND user_id = ?", (title, ciphertext, nonce, note_id, g.user["id"]))
        get_db().commit()
        flash("Nota actualizada con un nuevo nonce.", "success")
        return redirect(url_for("notes.detail", note_id=note_id))
    return render_template("notes/form.html", note=note, title=title, content=content)


@bp.route("/<note_id>/delete", methods=["GET", "POST"])
@login_required
def delete(note_id):
    note = get_note(note_id)
    if request.method == "POST":
        if request.form.get("confirm") != "yes":
            flash("Confirma que deseas eliminar la nota.", "danger")
            return render_template("notes/delete.html", note=note), 400
        get_db().execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, g.user["id"]))
        get_db().commit()
        flash("Nota eliminada correctamente.", "success")
        return redirect(url_for("notes.list_notes"))
    return render_template("notes/delete.html", note=note)
