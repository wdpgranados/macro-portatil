"""domain — Entidades puras del negocio (sin dependencias externas)."""

from .pieza import Pieza
from .venta import Venta
from .usuario import Usuario
from .item_carrito import ItemCarrito
from .cliente import Cliente

__all__ = ["Pieza", "Venta", "Usuario", "ItemCarrito", "Cliente"]
