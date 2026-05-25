"""
repositories/clientes_repo.py — Repositorio SQLite para Clientes.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from config import log
from database.connection import SQLiteConnection
from domain.cliente import Cliente


class SQLiteClientesRepo:

    def __init__(self, db: Path) -> None:
        self._db = db
        self._setup()

    def _setup(self) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id_cliente TEXT PRIMARY KEY,
                    nombre     TEXT NOT NULL,
                    telefono   TEXT NOT NULL DEFAULT '',
                    direccion  TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_clientes_nombre
                ON clientes (nombre COLLATE NOCASE)
            """)

    def upsert(self, cliente: Cliente) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                INSERT INTO clientes (id_cliente, nombre, telefono, direccion)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id_cliente) DO UPDATE SET
                    nombre    = excluded.nombre,
                    telefono  = excluded.telefono,
                    direccion = excluded.direccion
            """,
                (
                    cliente.id_cliente,
                    cliente.nombre,
                    cliente.telefono,
                    cliente.direccion,
                ),
            )
        log.info("Upsert cliente: %s", cliente.id_cliente)

    def get(self, id_cliente: str) -> Optional[Cliente]:
        with SQLiteConnection(self._db) as conn:
            row = conn.execute(
                "SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,)
            ).fetchone()
        return Cliente(**dict(row)) if row else None

    def get_all(self) -> list[Cliente]:
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute(
                "SELECT * FROM clientes ORDER BY nombre COLLATE NOCASE"
            ).fetchall()
        return [Cliente(**dict(r)) for r in rows]

    def buscar(self, query: str) -> list[Cliente]:
        patron = f"%{query}%"
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute(
                """
                SELECT * FROM clientes
                WHERE id_cliente LIKE ? COLLATE NOCASE
                   OR nombre     LIKE ? COLLATE NOCASE
                   OR telefono   LIKE ? COLLATE NOCASE
                ORDER BY nombre COLLATE NOCASE
            """,
                (patron, patron, patron),
            ).fetchall()
        return [Cliente(**dict(r)) for r in rows]

    def eliminar(self, id_cliente: str) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute("DELETE FROM clientes WHERE id_cliente = ?", (id_cliente,))
        log.info("Cliente eliminado: %s", id_cliente)
