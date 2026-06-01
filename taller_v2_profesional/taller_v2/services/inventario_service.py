"""
services/inventario_service.py — Lógica de negocio para el inventario.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import STOCK_BAJO_UMBRAL
from domain import Pieza
from repositories.interfaces import AbstractInventarioRepo


class InventarioService:

    def __init__(self, repo: AbstractInventarioRepo) -> None:
        self._repo = repo

    # ── Persistencia ─────────────────────────────────────────────
    def guardar_pieza(
        self,
        id_pieza: str,
        nombre: str,
        categoria: str,
        cantidad: int,
        precio: float,
        stock_minimo: int = 5,
    ) -> Pieza:
        """Inserta o acumula stock si ya existe."""
        pieza = Pieza(
            id_pieza=id_pieza.strip().upper(),
            nombre=nombre.strip(),
            categoria=categoria.strip(),
            cantidad=cantidad,
            precio_unitario=precio,
            stock_minimo=stock_minimo,
        )
        self._repo.upsert(pieza)
        return pieza

    def actualizar_pieza(
        self,
        id_pieza: str,
        nombre: str,
        categoria: str,
        cantidad: int,
        precio: float,
        stock_minimo: int = 5,
    ) -> Pieza:
        """Actualiza pieza existente SIN acumular stock."""
        pieza = Pieza(
            id_pieza=id_pieza.strip().upper(),
            nombre=nombre.strip(),
            categoria=categoria.strip(),
            cantidad=cantidad,
            precio_unitario=precio,
            stock_minimo=stock_minimo,
        )
        self._repo.actualizar(pieza)
        return pieza

    def eliminar_pieza(self, id_pieza: str) -> None:
        """Soft delete de una pieza."""
        self._repo.eliminar(id_pieza)

    # ── Consultas ─────────────────────────────────────────────────
    def listar(self) -> list[Pieza]:
        return self._repo.get_all()

    def buscar(self, query: str) -> list[Pieza]:
        if not query or not query.strip():
            return self._repo.get_all()
        return self._repo.buscar(query.strip())

    def get_stock_critico(self) -> list[Pieza]:
        """Piezas con stock <= su stock_minimo configurado."""
        return self._repo.get_stock_bajo()

    def get_stock_bajo(self, umbral: int = STOCK_BAJO_UMBRAL) -> list[Pieza]:
        return self._repo.get_stock_bajo(umbral)

    # ── KPIs ──────────────────────────────────────────────────────
    def valor_total_inventario(self) -> float:
        piezas = self._repo.get_all()
        if not piezas:
            return 0.0
        cantidades = np.array([p.cantidad for p in piezas], dtype=float)
        precios = np.array([p.precio_unitario for p in piezas], dtype=float)
        return float(np.dot(cantidades, precios))

    def get_df(self) -> pd.DataFrame:
        piezas = self._repo.get_all()
        if not piezas:
            return pd.DataFrame(
                columns=[
                    "id_pieza",
                    "nombre",
                    "categoria",
                    "cantidad",
                    "precio_unitario",
                    "stock_minimo",
                ]
            )
        return pd.DataFrame(
            [
                {
                    "id_pieza": p.id_pieza,
                    "nombre": p.nombre,
                    "categoria": p.categoria,
                    "cantidad": p.cantidad,
                    "precio_unitario": p.precio_unitario,
                    "stock_minimo": p.stock_minimo,
                }
                for p in piezas
            ]
        )
