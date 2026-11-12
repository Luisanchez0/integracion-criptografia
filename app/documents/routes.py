"""Registro firmado, descarga y verificación de bytes actuales o candidatos."""

import io
import sqlite3
import uuid

from cryptography.hazmat.primitives import serialization
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, send_file, url_for

from app.auth.routes import login_required
from app.crypto.signatures import sign_document, verify_document
from app.database.db import get_db
from app.documents.storage import read_stored, read_upload, stored_path
from app.local_files import write_private_file

bp = Blueprint("documents", __name__, url_prefix="/documents")


def get_document(document_id):
    doc = get_db().execute("SELECT * FROM documents WHERE id = ? AND user_id = ?", (document_id, g.user["id"])).fetchone()
    if doc is None:
        abort(404)
    return doc


@bp.get("/")
@login_required
def list_documents():
    docs = get_db().execute("SELECT * FROM documents WHERE user_id = ? ORDER BY id DESC", (g.user["id"],)).fetchall()
    return render_template("documents/list.html", documents=docs)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        try:
            name, suffix, data = read_upload(request.files.get("file"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("documents/form.html"), 400
        private, _ = current_app.extensions["ed25519"]
        signature = sign_document(private, data)
        storage_name = uuid.uuid4().hex + suffix
        path = stored_path(storage_name)
        try:
            write_private_file(path, data)
        except (OSError, RuntimeError):
            return render_template("error.html", code=503, message="No fue posible guardar el documento de forma segura."), 503
        try:
            cursor = get_db().execute("INSERT INTO documents (user_id, original_name, storage_name, signature, size_bytes) VALUES (?, ?, ?, ?, ?)", (g.user["id"], name, storage_name, signature, len(data)))
            get_db().commit()
        except sqlite3.Error:
            get_db().rollback()
            path.unlink(missing_ok=True)
            return render_template("error.html", code=503, message="No fue posible registrar el documento. Inténtalo de nuevo."), 503
        flash("Documento guardado y firmado con Ed25519.", "success")
        return redirect(url_for("documents.detail", document_id=cursor.lastrowid))
    return render_template("documents/form.html")


@bp.get("/<int:document_id>")
@login_required
def detail(document_id):
    return render_template("documents/detail.html", document=get_document(document_id), result=None, source=None)


@bp.post("/<int:document_id>/verify")
@login_required
def verify(document_id):
    doc = get_document(document_id)
    data = read_stored(doc["storage_name"])
    _, public = current_app.extensions["ed25519"]
    valid = verify_document(public, data, doc["signature"])
    get_db().execute("UPDATE documents SET last_verification = ?, last_verified_at = strftime('%Y-%m-%d %H:%M:%S', 'now') WHERE id = ? AND user_id = ?", (int(valid), document_id, g.user["id"]))
    get_db().commit()
    return render_template("documents/detail.html", document=get_document(document_id), result=valid, source="original")


@bp.post("/<int:document_id>/check-copy")
@login_required
def check_copy(document_id):
    doc = get_document(document_id)
    try:
        _, _, data = read_upload(request.files.get("file"))
    except ValueError as error:
        flash(str(error), "danger")
        return render_template("documents/detail.html", document=doc, result=None, source=None), 400
    _, public = current_app.extensions["ed25519"]
    valid = verify_document(public, data, doc["signature"])
    return render_template("documents/detail.html", document=doc, result=valid, source="copy")


@bp.get("/<int:document_id>/download")
@login_required
def download(document_id):
    doc = get_document(document_id)
    data = read_stored(doc["storage_name"])
    return send_file(io.BytesIO(data), as_attachment=True, download_name=doc["original_name"], mimetype="application/octet-stream")


@bp.get("/public-key")
@login_required
def public_key():
    _, public = current_app.extensions["ed25519"]
    pem = public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return send_file(io.BytesIO(pem), as_attachment=True, download_name="ed25519_public.pem", mimetype="application/x-pem-file")
