"""
services/ventas_service.py — Lógica de negocio para ventas.

Soporta venta de una sola pieza y venta múltiple con carrito.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from domain import Venta
from domain.item_carrito import ItemCarrito
from repositories.interfaces import AbstractInventarioRepo, AbstractVentasRepo


class VentasService:

    def __init__(
        self,
        inv_repo: AbstractInventarioRepo,
        ven_repo: AbstractVentasRepo,
    ) -> None:
        self._inv = inv_repo
        self._ven = ven_repo

    # ── Venta simple (una sola pieza) ────────────────────────────
    def registrar_venta(self, id_pieza: str, cantidad: int) -> Venta:
        """Venta de una sola pieza. Mantiene compatibilidad anterior."""
        pieza = self._inv.get(id_pieza)
        if pieza is None:
            raise ValueError(f"La pieza '{id_pieza}' no existe.")
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        if pieza.cantidad < cantidad:
            raise ValueError(
                f"Stock insuficiente para '{pieza.nombre}'. "
                f"Disponible: {pieza.cantidad} | Solicitado: {cantidad}"
            )
        total = float(np.multiply(cantidad, pieza.precio_unitario))
        venta = Venta(id_pieza=id_pieza, cantidad=cantidad, total=total)
        self._inv.restar_stock(id_pieza, cantidad)
        self._ven.insertar(venta)
        return venta

    # ── Venta múltiple (carrito) ──────────────────────────────────
    def registrar_venta_multiple(
        self,
        items: list[ItemCarrito],
        id_cliente: Optional[str] = None,
    ) -> list[Venta]:
        """
        Registra una venta con múltiples piezas.

        Flujo:
        1. Valida stock de TODAS las piezas antes de descontar cualquiera.
        2. Si todo está OK descuenta stock y persiste cada venta.
        3. Si alguna falla cancela toda la operación (rollback lógico).

        Raises:
            ValueError: Si el carrito está vacío o hay stock insuficiente.
        """
        if not items:
            raise ValueError("El carrito está vacío.")

        # 1. Validar stock de todas las piezas primero
        for item in items:
            pieza = self._inv.get(item.id_pieza)
            if pieza is None:
                raise ValueError(f"La pieza '{item.id_pieza}' no existe en inventario.")
            if pieza.cantidad < item.cantidad:
                raise ValueError(
                    f"Stock insuficiente para '{pieza.nombre}'. "
                    f"Disponible: {pieza.cantidad} | "
                    f"Solicitado: {item.cantidad}"
                )

        # 2. Todo OK — descontar stock y registrar ventas
        ventas_registradas: list[Venta] = []
        for item in items:
            total = float(np.multiply(item.cantidad, item.precio_unitario))
            venta = Venta(
                id_pieza=item.id_pieza,
                cantidad=item.cantidad,
                total=total,
                
                id_cliente = id_cliente
            )
            self._inv.restar_stock(item.id_pieza, item.cantidad)
            self._ven.insertar(venta)
            ventas_registradas.append(venta)

        return ventas_registradas

    # ── Consultas ─────────────────────────────────────────────────
    def get_df(
        self,
        fecha_ini: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> pd.DataFrame:
        return self._ven.get_all(fecha_ini=fecha_ini, fecha_fin=fecha_fin)

    # ── KPIs ──────────────────────────────────────────────────────
    def kpis(self, df: pd.DataFrame) -> dict[str, float | int]:
        if df.empty:
            return {
                "total": 0.0,
                "transacciones": 0,
                "unidades": 0,
                "ticket_promedio": 0.0,
            }
        totales = df["total"].to_numpy(dtype=float)
        unidades = df["cantidad"].to_numpy(dtype=int)
        return {
            "total": float(np.sum(totales)),
            "transacciones": int(len(df)),
            "unidades": int(np.sum(unidades)),
            "ticket_promedio": float(np.mean(totales)),
        }
