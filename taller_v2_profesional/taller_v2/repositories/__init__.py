"""repositories — Acceso a datos: interfaces y sus implementaciones SQLite."""

from .interfaces import AbstractInventarioRepo, AbstractVentasRepo
from .inventario_repo import SQLiteInventarioRepo
from .ventas_repo import SQLiteVentasRepo

__all__ = [
    "AbstractInventarioRepo",
    "AbstractVentasRepo",
    "SQLiteInventarioRepo",
    "SQLiteVentasRepo",
]
