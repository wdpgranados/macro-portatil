"""
services/inventario_service.py — Lógica de negocio para el inventario.

Orquesta el repositorio de inventario. No sabe nada de SQLite ni de Tkinter.
Aplica validaciones de negocio y cálculos vectorizados con NumPy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import STOCK_BAJO_UMBRAL
from domain import Pieza
from repositories.interfaces import AbstractInventarioRepo


class InventarioService:
    """Servicio de inventario: validaciones, cálculos y consultas."""

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
    ) -> Pieza:
        """
        Crea la entidad Pieza (con validaciones en __post_init__)
        y la persiste mediante upsert.
        """
        pieza = Pieza(
            id_pieza=id_pieza.strip().upper(),
            nombre=nombre.strip(),
            categoria=categoria.strip(),
            cantidad=cantidad,
            precio_unitario=precio,
        )
        self._repo.upsert(pieza)
        return pieza

    # ── Consultas ─────────────────────────────────────────────────
    def listar(self) -> list[Pieza]:
        """Todas las piezas ordenadas por nombre."""
        return self._repo.get_all()

    def buscar(self, query: str) -> list[Pieza]:
        """
        Búsqueda de texto libre delegada al repositorio (se filtra en SQL).
        Si el query está vacío, retorna todas las piezas.
        """
        if not query or not query.strip():
            return self._repo.get_all()
        return self._repo.buscar(query.strip())

    def get_stock_bajo(self, umbral: int = STOCK_BAJO_UMBRAL) -> list[Pieza]:
        """Piezas con stock crítico por debajo del umbral configurado."""
        return self._repo.get_stock_bajo(umbral)

    # ── KPIs ──────────────────────────────────────────────────────
    def valor_total_inventario(self) -> float:
        """
        Valor total del inventario: Σ(cantidad_i × precio_i).
        Usa np.dot para el cálculo vectorizado.
        """
        piezas = self._repo.get_all()
        if not piezas:
            return 0.0
        cantidades = np.array([p.cantidad for p in piezas], dtype=float)
        precios    = np.array([p.precio_unitario for p in piezas], dtype=float)
        return float(np.dot(cantidades, precios))

    def get_df(self) -> pd.DataFrame:
        """
        Retorna el inventario completo como DataFrame de Pandas.
        Útil para gráficos y reportes.
        """
        piezas = self._repo.get_all()
        if not piezas:
            return pd.DataFrame(
                columns=["id_pieza", "nombre", "categoria",
                         "cantidad", "precio_unitario"]
            )
        return pd.DataFrame([vars(p) for p in piezas])
