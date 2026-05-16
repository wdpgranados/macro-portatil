from __future__ import annotations
import hashlib
import uuid
from typing import Optional

from config import log
from domain.usuario import Usuario, ROLES
from repositories.usuarios_repo import SQLiteUsuariosRepo


class AuthService:

    MAX_INTENTOS = 3

    def __init__(self, repo: SQLiteUsuariosRepo) -> None:
        self._repo = repo
        self._usuario_activo: Optional[Usuario] = None
        self._intentos: int = 0

    @staticmethod
    def hashear(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username: str, password: str) -> tuple[bool, str]:
        if self._intentos >= self.MAX_INTENTOS:
            return False, "Cuenta bloqueada. Reinicia el sistema."

        usuario = self._repo.get_by_username(username.strip())
        if usuario is None:
            self._intentos += 1
            return (
                False,
                f"Usuario no encontrado. Intento {self._intentos}/{self.MAX_INTENTOS}",
            )

        if usuario.password_hash != self.hashear(password):
            self._intentos += 1
            return (
                False,
                f"Contraseña incorrecta. Intento {self._intentos}/{self.MAX_INTENTOS}",
            )

        self._usuario_activo = usuario
        self._intentos = 0
        log.info("Login exitoso: %s (%s)", usuario.username, usuario.rol)
        return True, f"Bienvenido, {usuario.nombre}"

    def logout(self) -> None:
        log.info(
            "Logout: %s", self._usuario_activo.username if self._usuario_activo else "–"
        )
        self._usuario_activo = None

    @property
    def usuario(self) -> Optional[Usuario]:
        return self._usuario_activo

    @property
    def rol(self) -> str:
        return self._usuario_activo.rol if self._usuario_activo else ""

    def crear_usuario(
        self, nombre: str, username: str, password: str, rol: str
    ) -> Usuario:
        if rol not in ROLES:
            raise ValueError(f"Rol inválido: {rol}")
        usuario = Usuario(
            id_usuario=f"USR{uuid.uuid4().hex[:6].upper()}",
            nombre=nombre.strip(),
            username=username.strip().lower(),
            password_hash=self.hashear(password),
            rol=rol,
        )
        self._repo.insertar(usuario)
        return usuario

    def cambiar_password(self, id_usuario: str, nueva_password: str) -> None:
        self._repo.actualizar_password(id_usuario, self.hashear(nueva_password))

    def listar_usuarios(self) -> list[Usuario]:
        return self._repo.get_all()
