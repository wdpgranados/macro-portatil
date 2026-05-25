"""
domain/cliente.py — Entidad de dominio: Cliente.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Cliente:
    id_cliente: str
    nombre: str
    telefono: str
    direccion: str

    def __post_init__(self) -> None:
        if not self.id_cliente or not self.id_cliente.strip():
            raise ValueError("El ID de cliente no puede estar vacío.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
