"""
domain/pieza.py — Entidad de dominio: Pieza.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Pieza:
    id_pieza: str
    nombre: str
    categoria: str
    cantidad: int
    precio_unitario: float
    stock_minimo: int = 5

    @property
    def valor_stock(self) -> float:
        return self.cantidad * self.precio_unitario

    @property
    def stock_critico(self) -> bool:
        """True si el stock está en o por debajo del mínimo."""
        return self.cantidad <= self.stock_minimo

    def __post_init__(self) -> None:
        if self.precio_unitario < 0:
            raise ValueError("El precio no puede ser negativo.")
        if self.cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        if self.stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser negativo.")
        if not self.id_pieza or not self.id_pieza.strip():
            raise ValueError("El ID de pieza no puede estar vacío.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
