from __future__ import annotations
from dataclasses import dataclass

ROLES = ["admin", "vendedor", "tecnico"]


@dataclass
class Usuario:
    id_usuario: str
    nombre: str
    username: str
    password_hash: str
    rol: str
    activo: int = 1

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValueError("El username no puede estar vacío.")
        if self.rol not in ROLES:
            raise ValueError(f"Rol inválido. Use: {ROLES}")

    @property
    def es_admin(self) -> bool:
        return self.rol == "admin"

    @property
    def es_vendedor(self) -> bool:
        return self.rol == "vendedor"

    @property
    def es_tecnico(self) -> bool:
        return self.rol == "tecnico"
