"""
domain/pieza.py — Entidad de dominio: Pieza.

Representa una pieza física en el inventario del taller.
No tiene dependencias externas: puro Python con dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Pieza:
    """
    Pieza de inventario.

    Attributes:
        id_pieza:        Código único (ej: 'RAM-DDR4-16G').
        nombre:          Descripción legible (ej: 'Memoria RAM DDR4 16GB').
        categoria:       Grupo al que pertenece (ej: 'Memoria', 'Disco', 'CPU').
        cantidad:        Unidades disponibles en stock. Debe ser >= 0.
        precio_unitario: Precio de venta por unidad. Debe ser >= 0.
    """

    id_pieza:        str
    nombre:          str
    categoria:       str
    cantidad:        int
    precio_unitario: float

    # ── Propiedad calculada ────────────────────────────────────────
    @property
    def valor_stock(self) -> float:
        """Valor total de las unidades en stock (cantidad × precio)."""
        return self.cantidad * self.precio_unitario

    # ── Validaciones en construcción ───────────────────────────────
    def __post_init__(self) -> None:
        if self.precio_unitario < 0:
            raise ValueError(
                f"El precio no puede ser negativo. Recibido: {self.precio_unitario}"
            )
        if self.cantidad < 0:
            raise ValueError(
                f"La cantidad no puede ser negativa. Recibido: {self.cantidad}"
            )
        if not self.id_pieza or not self.id_pieza.strip():
            raise ValueError("El ID de pieza no puede estar vacío.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre de pieza no puede estar vacío.")
