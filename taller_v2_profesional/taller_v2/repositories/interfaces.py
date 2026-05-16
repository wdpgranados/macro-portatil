"""
repositories/interfaces.py — Contratos abstractos de repositorio.

Define las interfaces que CUALQUIER implementación de persistencia
debe respetar (SQLite, PostgreSQL, en memoria para tests, etc.).

Principio: los servicios dependen de estas abstracciones,
NO de implementaciones concretas (Dependency Inversion).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from domain import Pieza, Venta


# ══════════════════════════════════════════════════════════════════
#  CONTRATO: Inventario
# ══════════════════════════════════════════════════════════════════
class AbstractInventarioRepo(ABC):
    """Contrato de acceso a datos para el inventario de piezas."""

    @abstractmethod
    def upsert(self, pieza: Pieza) -> None:
        """
        Inserta la pieza si no existe; si ya existe, acumula la cantidad
        y actualiza nombre, categoría y precio.
        """
        ...

    @abstractmethod
    def get(self, id_pieza: str) -> Optional[Pieza]:
        """Retorna la pieza con ese ID, o None si no existe."""
        ...

    @abstractmethod
    def get_all(self) -> list[Pieza]:
        """Retorna todas las piezas ordenadas por nombre."""
        ...

    @abstractmethod
    def restar_stock(self, id_pieza: str, cantidad: int) -> None:
        """Descuenta `cantidad` unidades del stock de la pieza."""
        ...

    @abstractmethod
    def buscar(self, query: str) -> list[Pieza]:
        """
        Búsqueda por texto parcial en id_pieza, nombre o categoría.
        Case-insensitive.
        """
        ...

    @abstractmethod
    def get_stock_bajo(self, umbral: int) -> list[Pieza]:
        """Retorna piezas con cantidad < umbral, ordenadas por cantidad ASC."""
        ...


# ══════════════════════════════════════════════════════════════════
#  CONTRATO: Ventas
# ══════════════════════════════════════════════════════════════════
class AbstractVentasRepo(ABC):
    """Contrato de acceso a datos para el registro de ventas."""

    @abstractmethod
    def insertar(self, venta: Venta) -> None:
        """Persiste una nueva venta en el almacén."""
        ...

    @abstractmethod
    def get_all(
        self,
        fecha_ini: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retorna todas las ventas como DataFrame.
        Acepta filtros opcionales de fecha en formato 'YYYY-MM-DD'.
        La columna 'fecha' se devuelve como datetime.
        """
        ...
