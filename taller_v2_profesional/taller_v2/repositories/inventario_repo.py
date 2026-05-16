"""
repositories/inventario_repo.py — Implementación SQLite para Inventario.

Todas las queries usan placeholders `?` (parametrizadas).
NUNCA se concatena input del usuario en el SQL → sin riesgo de SQL injection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from config import log
from database.connection import SQLiteConnection
from domain import Pieza
from repositories.interfaces import AbstractInventarioRepo


class SQLiteInventarioRepo(AbstractInventarioRepo):
    """Repositorio de inventario respaldado en SQLite."""

    def __init__(self, db: Path) -> None:
        self._db = db
        self._setup()

    # ── Inicialización del esquema ────────────────────────────────
    def _setup(self) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventario (
                    id_pieza        TEXT PRIMARY KEY,
                    nombre          TEXT NOT NULL,
                    categoria       TEXT NOT NULL,
                    cantidad        INTEGER NOT NULL DEFAULT 0
                                    CHECK(cantidad >= 0),
                    precio_unitario REAL    NOT NULL DEFAULT 0.0
                                    CHECK(precio_unitario >= 0)
                )
            """)
            # Índice para acelerar búsquedas por nombre y categoría
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inv_nombre
                ON inventario (nombre COLLATE NOCASE)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inv_categoria
                ON inventario (categoria COLLATE NOCASE)
            """)

    # ── upsert ────────────────────────────────────────────────────
    def upsert(self, pieza: Pieza) -> None:
        """
        Inserta la pieza o, si ya existe, acumula el stock y actualiza
        nombre, categoría y precio. Usa UPSERT nativo de SQLite 3.24+.
        """
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                INSERT INTO inventario
                    (id_pieza, nombre, categoria, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id_pieza) DO UPDATE SET
                    nombre          = excluded.nombre,
                    categoria       = excluded.categoria,
                    cantidad        = inventario.cantidad + excluded.cantidad,
                    precio_unitario = excluded.precio_unitario
                """,
                (
                    pieza.id_pieza,
                    pieza.nombre,
                    pieza.categoria,
                    pieza.cantidad,
                    pieza.precio_unitario,
                ),
            )
        log.info("Upsert pieza: %s | stock nuevo: +%d", pieza.id_pieza, pieza.cantidad)

    # ── get ───────────────────────────────────────────────────────
    def get(self, id_pieza: str) -> Optional[Pieza]:
        """Retorna la pieza exacta por ID, o None si no existe."""
        with SQLiteConnection(self._db) as conn:
            row = conn.execute(
                "SELECT * FROM inventario WHERE id_pieza = ?",
                (id_pieza,),
            ).fetchone()
        return Pieza(**dict(row)) if row else None

    # ── get_all ───────────────────────────────────────────────────
    def get_all(self) -> list[Pieza]:
        """Retorna todas las piezas ordenadas alfabéticamente por nombre."""
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute(
                "SELECT * FROM inventario ORDER BY nombre COLLATE NOCASE"
            ).fetchall()
        return [Pieza(**dict(r)) for r in rows]

    # ── restar_stock ──────────────────────────────────────────────
    def restar_stock(self, id_pieza: str, cantidad: int) -> None:
        """
        Decrementa el stock de la pieza.
        El CHECK(cantidad >= 0) en la DB actúa como segunda barrera.
        """
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                UPDATE inventario
                SET cantidad = cantidad - ?
                WHERE id_pieza = ?
                """,
                (cantidad, id_pieza),
            )
        log.info("Stock restado: %s | -%d unidades", id_pieza, cantidad)

    # ── buscar ────────────────────────────────────────────────────
    def buscar(self, query: str) -> list[Pieza]:
        """
        Búsqueda de texto libre en id_pieza, nombre y categoría.
        Usa LIKE con COLLATE NOCASE → case-insensitive sin conversión Python.
        """
        patron = f"%{query}%"
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute(
                """
                SELECT * FROM inventario
                WHERE id_pieza  LIKE ? COLLATE NOCASE
                   OR nombre    LIKE ? COLLATE NOCASE
                   OR categoria LIKE ? COLLATE NOCASE
                ORDER BY nombre COLLATE NOCASE
                """,
                (patron, patron, patron),
            ).fetchall()
        return [Pieza(**dict(r)) for r in rows]

    # ── get_stock_bajo ────────────────────────────────────────────
    def get_stock_bajo(self, umbral: int) -> list[Pieza]:
        """
        Piezas críticas con stock por debajo del umbral.
        Ordenadas de menor a mayor cantidad para priorizar reposición.
        """
        with SQLiteConnection(self._db) as conn:
            rows = conn.execute(
                """
                SELECT * FROM inventario
                WHERE cantidad < ?
                ORDER BY cantidad ASC, nombre COLLATE NOCASE
                """,
                (umbral,),
            ).fetchall()
        return [Pieza(**dict(r)) for r in rows]
