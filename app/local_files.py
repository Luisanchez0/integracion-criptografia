"""Escritura exclusiva de secretos y permisos del usuario local."""

import csv
import io
import os
import subprocess
from pathlib import Path


def restrict_permissions(path: Path, *, directory=False):
    if os.name == "nt":
        result = subprocess.run(["whoami", "/user", "/fo", "csv", "/nh"], capture_output=True, text=True, check=True)
        sid = next(csv.reader(io.StringIO(result.stdout.strip())))[1]
        grant = f"*{sid}:(OI)(CI)F" if directory else f"*{sid}:F"
        try:
            subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", grant], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("No fue posible restringir los permisos del archivo local.") from None
    else:
        path.chmod(0o700 if directory else 0o600)


def write_private_file(path: Path, data: bytes):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        restrict_permissions(path)
        with os.fdopen(fd, "wb") as stream:
            fd = None
            stream.write(data)
    except BaseException:
        if fd is not None:
            os.close(fd)
        path.unlink(missing_ok=True)
        raise
