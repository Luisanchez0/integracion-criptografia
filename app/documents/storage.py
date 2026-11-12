"""Validación de cargas y referencias internas de archivos."""

import re
from pathlib import Path

from flask import abort, current_app
from werkzeug.utils import secure_filename


def read_upload(upload):
    if upload is None or not upload.filename:
        raise ValueError("Selecciona un archivo .txt o .pdf.")
    name = secure_filename(upload.filename)
    suffix = Path(name).suffix.lower()
    if suffix not in {".txt", ".pdf"} or not 1 <= len(name) <= 200:
        raise ValueError("Solo se permiten archivos .txt o .pdf con un nombre de hasta 200 caracteres.")
    data = upload.read(current_app.config["MAX_UPLOAD_BYTES"] + 1)
    if not data:
        raise ValueError("El documento no puede estar vacío.")
    if len(data) > current_app.config["MAX_UPLOAD_BYTES"]:
        raise ValueError("El archivo supera el tamaño permitido.")
    if suffix == ".pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("El archivo seleccionado no tiene una cabecera PDF válida.")
    if suffix == ".txt":
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Los archivos .txt deben estar codificados en UTF-8.") from None
        if b"\x00" in data:
            raise ValueError("El archivo .txt contiene datos binarios no permitidos.")
    return name, suffix, data


def stored_path(storage_name):
    if not re.fullmatch(r"[a-f0-9]{32}\.(txt|pdf)", storage_name):
        abort(404)
    root = Path(current_app.config["STORAGE_PATH"]).resolve()
    path = root / storage_name
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        abort(404)
    return path


def read_stored(storage_name):
    try:
        # También se limita la lectura de un archivo alterado fuera de la app.
        with stored_path(storage_name).open("rb") as stream:
            data = stream.read(current_app.config["MAX_UPLOAD_BYTES"] + 1)
    except OSError:
        abort(404)
    return data
