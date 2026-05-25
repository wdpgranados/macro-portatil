"""
domain/venta.py — Entidad de dominio: Venta.

Representa una transacción de salida de inventario (despacho o venta).
Genera su propio ID único en el momento de creación.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Venta:
    """
    Registro de una venta / salida de inventario.

    Attributes:
        id_pieza:  Referencia al ID de la pieza despachada.
        cantidad:  Unidades despachadas en esta transacción.
        total:     Importe total cobrado (cantidad × precio_unitario al momento).
        fecha:     Timestamp de la transacción. Se asigna automáticamente.
        id_venta:  Identificador único autogenerado con prefijo 'V'.
    """

    id_pieza: str
    cantidad: int
    total: float
    id_cliente: Optional[str] = None

    fecha: datetime = field(default_factory=datetime.now)
    id_venta: str = field(default_factory=lambda: f"V{uuid.uuid4().hex[:8].upper()}")
