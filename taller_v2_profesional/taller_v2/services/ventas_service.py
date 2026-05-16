"""
services/ventas_service.py — Lógica de negocio para ventas.

Orquesta los repositorios de inventario y ventas.
Aplica todas las reglas de negocio antes de persistir una venta.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from domain import Venta
from repositories.interfaces import AbstractInventarioRepo, AbstractVentasRepo


class VentasService:
    """Servicio de ventas: validaciones, registro y KPIs."""

    def __init__(
        self,
        inv_repo: AbstractInventarioRepo,
        ven_repo: AbstractVentasRepo,
    ) -> None:
        self._inv = inv_repo
        self._ven = ven_repo

    # ── Registro de venta ────────────────────────────────────────
    def registrar_venta(self, id_pieza: str, cantidad: int) -> Venta:
        """
        Flujo completo de una venta:
        1. Verifica que la pieza exista en inventario.
        2. Valida que la cantidad sea positiva.
        3. Verifica que haya stock suficiente.
        4. Calcula el total.
        5. Descuenta stock y persiste la venta.

        Raises:
            ValueError: Si alguna validación de negocio falla.
        """
        # 1. Existencia
        pieza = self._inv.get(id_pieza)
        if pieza is None:
            raise ValueError(f"La pieza '{id_pieza}' no existe en inventario.")

        # 2. Cantidad válida
        if cantidad <= 0:
            raise ValueError("La cantidad a vender debe ser mayor a 0.")

        # 3. Stock suficiente
        if pieza.cantidad < cantidad:
            raise ValueError(
                f"Stock insuficiente para '{pieza.nombre}'. "
                f"Disponible: {pieza.cantidad} | Solicitado: {cantidad}"
            )

        # 4. Cálculo del total
        total = float(np.multiply(cantidad, pieza.precio_unitario))
        venta = Venta(id_pieza=id_pieza, cantidad=cantidad, total=total)

        # 5. Persistencia (descuento de stock primero, luego venta)
        self._inv.restar_stock(id_pieza, cantidad)
        self._ven.insertar(venta)

        return venta

    # ── Consultas ────────────────────────────────────────────────
    def get_df(
        self,
        fecha_ini: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Ventas como DataFrame, con filtro de fechas delegado al repositorio
        (los filtros se aplican en SQL, no en Python).
        """
        return self._ven.get_all(fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    # ── KPIs ──────────────────────────────────────────────────────
    def kpis(self, df: pd.DataFrame) -> dict[str, float | int]:
        """
        Calcula KPIs de ventas a partir de un DataFrame.

        Returns:
            dict con claves: total, transacciones, unidades, ticket_promedio.
            Todos en 0 si el DataFrame está vacío.
        """
        if df.empty:
            return {
                "total":           0.0,
                "transacciones":   0,
                "unidades":        0,
                "ticket_promedio": 0.0,
            }
        totales   = df["total"].to_numpy(dtype=float)
        unidades  = df["cantidad"].to_numpy(dtype=int)
        return {
            "total":           float(np.sum(totales)),
            "transacciones":   int(len(df)),
            "unidades":        int(np.sum(unidades)),
            "ticket_promedio": float(np.mean(totales)),
        }
