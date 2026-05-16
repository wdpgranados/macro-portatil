"""
database/connection.py — Infraestructura de base de datos.

Provee un context manager seguro para conexiones SQLite:
- Activa foreign keys en cada sesión.
- Hace commit automático al salir sin error.
- Hace rollback automático si hay una excepción.
- Cierra la conexión siempre.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from config import log


class SQLiteConnection:
    """
    Context manager ligero para conexiones SQLite seguras.

    Uso:
        with SQLiteConnection(DB_PATH) as conn:
            conn.execute("SELECT ...")

    Garantías:
        - PRAGMA foreign_keys = ON activo en cada sesión.
        - row_factory = sqlite3.Row para acceso por nombre de columna.
        - Commit automático si no hay excepciones.
        - Rollback automático + log de error si hay excepción.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def __enter__(self) -> sqlite3.Connection:
        self._conn = sqlite3.connect(self._path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> bool:
        if exc_type:
            self._conn.rollback()
            log.error("DB rollback – %s: %s", exc_type.__name__, exc_val)
        else:
            self._conn.commit()
        self._conn.close()
        return False  # No suprime la excepción; deja que suba al llamador
