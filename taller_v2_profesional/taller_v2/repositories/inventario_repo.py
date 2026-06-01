"""
repositories/inventario_repo.py — Repositorio SQLite para Inventario.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from config import log
from database.connection import SQLiteConnection
from domain import Pieza
from repositories.interfaces import AbstractInventarioRepo


class SQLiteInventarioRepo(AbstractInventarioRepo):

    def __init__(self, db: Path) -> None:
        self._db = db
        self._setup()

    def _setup(self) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventario (
                    id_pieza        TEXT PRIMARY KEY,
                    nombre          TEXT NOT NULL,
                    categoria       TEXT NOT NULL,
                    cantidad        INTEGER NOT NULL DEFAULT 0
                                    CHECK(cantidad >= 0),
                    precio_unitario REAL NOT NULL DEFAULT 0.0
                                    CHECK(precio_unitario >= 0),
                    stock_minimo    INTEGER NOT NULL DEFAULT 5,
                    activo          INTEGER NOT NULL DEFAULT 1
                )
            """)
            # Agregar columnas nuevas si ya existe la tabla sin ellas
            for columna, definicion in [
                ("stock_minimo", "INTEGER NOT NULL DEFAULT 5"),
                ("activo", "INTEGER NOT NULL DEFAULT 1"),
            ]:
                try:
                    conn.execute(
                        f"ALTER TABLE inventario ADD COLUMN {columna} {definicion}"
                    )
                except Exception:
                    pass

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inv_nombre
                ON inventario (nombre COLLATE NOCASE)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inv_categoria
                ON inventario (categoria COLLATE NOCASE)
            """)

    def upsert(self, pieza: Pieza) -> None:
        """Inserta o acumula stock si ya existe."""
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                INSERT INTO inventario
                    (id_pieza, nombre, categoria, cantidad,
                     precio_unitario, stock_minimo, activo)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(id_pieza) DO UPDATE SET
                    nombre          = excluded.nombre,
                    categoria       = excluded.categoria,
                    cantidad        = inventario.cantidad + excluded.cantidad,
                    precio_unitario = excluded.precio_unitario,
                    stock_minimo    = excluded.stock_minimo,
                    activo          = 1
            """,
                (
                    pieza.id_pieza,
                    pieza.nombre,
                    pieza.categoria,
                    pieza.cantidad,
                    pieza.precio_unitario,
                    pieza.stock_minimo,
                ),
            )
        log.info("Upsert pieza: %s", pieza.id_pieza)

    def actualizar(self, pieza: Pieza) -> None:
        """Actualiza pieza SIN acumular cantidad."""
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                UPDATE inventario SET
                    nombre          = ?,
                    categoria       = ?,
                    cantidad        = ?,
                    precio_unitario = ?,
                    stock_minimo    = ?
                WHERE id_pieza = ?
            """,
                (
                    pieza.nombre,
                    pieza.categoria,
                    pieza.cantidad,
                    pieza.precio_unitario,
                    pieza.stock_minimo,
                    pieza.id_pieza,
                ),
            )
        log.info("Pieza actualizada: %s", pieza.id_pieza)

    def get(self, id_pieza: str) -> Optional[Pieza]:
        with SQLiteConnection(self._db) as conn:
            row = conn.execute(
                """
                SELECT id_pieza, nombre, categoria, cantidad,
                       precio_unitario, stock_minimo
                FROM inventario
                WHERE id_pieza = ? AND activo = 1
            """,
                (id_pieza,),
            ).fetchone()
        return Pieza(**dict(row)) if row else None

    def get_all(self) -> list[Pieza]:
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute("""
                SELECT id_pieza, nombre, categoria, cantidad,
                       precio_unitario, stock_minimo
                FROM inventario
                WHERE activo = 1
                ORDER BY nombre COLLATE NOCASE
            """).fetchall()
        return [Pieza(**dict(r)) for r in rows]

    def restar_stock(self, id_pieza: str, cantidad: int) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                UPDATE inventario
                SET cantidad = cantidad - ?
                WHERE id_pieza = ?
            """,
                (cantidad, id_pieza),
            )
        log.info("Stock restado: %s | -%d", id_pieza, cantidad)

    def eliminar(self, id_pieza: str) -> None:
        """Soft delete: marca como inactiva sin borrar físicamente."""
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                "UPDATE inventario SET activo = 0 WHERE id_pieza = ?", (id_pieza,)
            )
        log.info("Pieza desactivada: %s", id_pieza)

    def buscar(self, query: str) -> list[Pieza]:
        patron = f"%{query}%"
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute(
                """
                SELECT id_pieza, nombre, categoria, cantidad,
                       precio_unitario, stock_minimo
                FROM inventario
                WHERE activo = 1
                  AND (
                    id_pieza  LIKE ? COLLATE NOCASE OR
                    nombre    LIKE ? COLLATE NOCASE OR
                    categoria LIKE ? COLLATE NOCASE
                  )
                ORDER BY nombre COLLATE NOCASE
            """,
                (patron, patron, patron),
            ).fetchall()
        return [Pieza(**dict(r)) for r in rows]

    def get_stock_bajo(self, umbral: int = None) -> list[Pieza]:
        with SQLiteConnection(self._db) as conn:
            if umbral is not None:
                rows = conn.execute(
                    """
                    SELECT id_pieza, nombre, categoria, cantidad,
                           precio_unitario, stock_minimo
                    FROM inventario
                    WHERE activo = 1 AND cantidad < ?
                    ORDER BY cantidad ASC
                """,
                    (umbral,),
                ).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id_pieza, nombre, categoria, cantidad,
                           precio_unitario, stock_minimo
                    FROM inventario
                    WHERE activo = 1 AND cantidad <= stock_minimo
                    ORDER BY cantidad ASC
                """).fetchall()
        return [Pieza(**dict(r)) for r in rows]
