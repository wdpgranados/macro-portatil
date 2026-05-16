"""
repositories/ventas_repo.py — Implementación SQLite para Ventas.

Las consultas de lectura se realizan directamente con filtros SQL
(no en Python post-carga), reduciendo el volumen de datos transferido.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from config import log
from database.connection import SQLiteConnection
from domain import Venta
from repositories.interfaces import AbstractVentasRepo


class SQLiteVentasRepo(AbstractVentasRepo):
    """Repositorio de ventas respaldado en SQLite."""

    def __init__(self, db: Path) -> None:
        self._db = db
        self._setup()

    # ── Inicialización del esquema ────────────────────────────────
    def _setup(self) -> None:
        with SQLiteConnection(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id_venta TEXT PRIMARY KEY,
                    id_pieza TEXT    NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    total    REAL    NOT NULL CHECK(total >= 0),
                    fecha    TEXT    NOT NULL,
                    FOREIGN KEY(id_pieza) REFERENCES inventario(id_pieza)
                )
            """)
            # Índice para acelerar filtros por fecha y reportes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ventas_fecha
                ON ventas (fecha)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ventas_pieza
                ON ventas (id_pieza)
            """)

    # ── insertar ──────────────────────────────────────────────────
    def insertar(self, venta: Venta) -> None:
        """Persiste una nueva venta. La fecha se guarda en formato ISO 8601."""
        with SQLiteConnection(self._db) as conn:
            conn.execute(
                """
                INSERT INTO ventas (id_venta, id_pieza, cantidad, total, fecha)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    venta.id_venta,
                    venta.id_pieza,
                    venta.cantidad,
                    venta.total,
                    venta.fecha.isoformat(),
                ),
            )
        log.info("Venta registrada: %s | $%.2f", venta.id_venta, venta.total)

    # ── get_all ───────────────────────────────────────────────────
    def get_all(
        self,
        fecha_ini: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retorna ventas como DataFrame con filtros de fecha aplicados en SQL.

        Los filtros se aplican en la query (no en Python), reduciendo
        la cantidad de filas transferidas de la DB al proceso.

        Args:
            fecha_ini: Fecha inicio 'YYYY-MM-DD' (inclusive). None = sin límite.
            fecha_fin: Fecha fin   'YYYY-MM-DD' (inclusive). None = sin límite.

        Returns:
            DataFrame con columnas: id_venta, id_pieza, cantidad, total, fecha.
            La columna 'fecha' es de tipo datetime64.
        """
        conditions: list[str] = []
        params: list[str] = []

        if fecha_ini:
            # Comparación ISO: '2025-01-01' <= '2025-01-01T10:30:00'
            conditions.append("fecha >= ?")
            params.append(fecha_ini)

        if fecha_fin:
            # Incluye todo el día final añadiendo T23:59:59
            conditions.append("fecha <= ?")
            params.append(f"{fecha_fin}T23:59:59")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sql = f"""
            SELECT
                id_venta,
                id_pieza,
                cantidad,
                total,
                fecha
            FROM ventas
            {where_clause}
            ORDER BY fecha DESC
        """

        with SQLiteConnection(self._db) as conn:
            df = pd.read_sql_query(sql, conn, params=params if params else None)

        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"])

        return df
