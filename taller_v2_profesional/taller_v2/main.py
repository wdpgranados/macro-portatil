import sys
from pathlib import Path

# Agrega la carpeta raíz al path de Python
sys.path.insert(0, str(Path(__file__).parent))

from config import DB_PATH
from repositories.usuarios_repo import SQLiteUsuariosRepo
from services.auth_service import AuthService
from ui.login import LoginWindow


def iniciar_app(auth_svc: AuthService) -> None:
    from ui.app import TallerApp

    app = TallerApp(auth_svc=auth_svc)
    app.mainloop()


if __name__ == "__main__":
    usr_repo = SQLiteUsuariosRepo(DB_PATH)
    auth_svc = AuthService(usr_repo)

    login = LoginWindow(auth_svc=auth_svc, on_success=iniciar_app)
    login.mainloop()
