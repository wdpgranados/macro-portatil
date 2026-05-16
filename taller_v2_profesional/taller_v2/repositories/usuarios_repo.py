from __future__ import annotations
from pathlib import Path
from typing import Optional

from config import log
from database.connection import SQLiteConnection
from domain.usuario import Usuario


class SQLiteUsuariosRepo:

    def __init__(self, db: Path) -> None:
        self._db = db
        self._setup()

    def _setup(self) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario    TEXT PRIMARY KEY,
                    nombre        TEXT NOT NULL,
                    username      TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol           TEXT NOT NULL,
                    activo        INTEGER NOT NULL DEFAULT 1
                )
            """)
            existe = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
            if existe == 0:
                self._crear_admin_default(conn)

    def _crear_admin_default(self, conn) -> None:
        import hashlib

        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute(
            """
            INSERT INTO usuarios
                (id_usuario, nombre, username, password_hash, rol)
            VALUES ('USR001', 'Administrador', 'admin', ?, 'admin')
        """,
            (password_hash,),
        )
        log.info("Usuario admin creado. Password: admin123")

    def get_by_username(self, username: str) -> Optional[Usuario]:
        with SQLiteConnection(self._db) as conn:
            row = conn.execute(
                """
                SELECT * FROM usuarios
                WHERE username = ? AND activo = 1
            """,
                (username,),
            ).fetchone()
        return Usuario(**dict(row)) if row else None

    def get_all(self) -> list[Usuario]:
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute("SELECT * FROM usuarios ORDER BY nombre").fetchall()
        return [Usuario(**dict(r)) for r in rows]

    def insertar(self, usuario: Usuario) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                INSERT INTO usuarios
                    (id_usuario, nombre, username, password_hash, rol, activo)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    usuario.id_usuario,
                    usuario.nombre,
                    usuario.username,
                    usuario.password_hash,
                    usuario.rol,
                    usuario.activo,
                ),
            )
        log.info("Usuario creado: %s", usuario.username)

    def actualizar_password(self, id_usuario: str, nuevo_hash: str) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                UPDATE usuarios SET password_hash = ?
                WHERE id_usuario = ?
            """,
                (nuevo_hash, id_usuario),
            )

    def desactivar(self, id_usuario: str) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                "UPDATE usuarios SET activo = 0 WHERE id_usuario = ?", (id_usuario,)
            )
        log.info("Usuario desactivado: %s", id_usuario)
