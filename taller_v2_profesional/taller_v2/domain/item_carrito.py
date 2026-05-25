"""
domain/item_carrito.py — Entidad de dominio: Item del carrito de compras.

Representa una pieza agregada al carrito temporal antes de confirmar
la venta. Vive únicamente en memoria, no se persiste en la DB.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ItemCarrito:
    """
    Pieza seleccionada dentro del carrito de compras.

    Attributes:
        id_pieza:        ID de la pieza en inventario.
        nombre:          Nombre descriptivo de la pieza.
        cantidad:        Unidades solicitadas.
        precio_unitario: Precio al momento de agregar al carrito.
    """

    id_pieza: str
    nombre: str
    cantidad: int
    precio_unitario: float

    @property
    def subtotal(self) -> float:
        """Subtotal = cantidad × precio unitario."""
        return self.cantidad * self.precio_unitario

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        if self.precio_unitario < 0:
            raise ValueError("El precio no puede ser negativo.")
        if not self.id_pieza.strip():
            raise ValueError("El ID de pieza no puede estar vacío.")
