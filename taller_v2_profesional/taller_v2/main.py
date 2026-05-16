"""
main.py — Punto de entrada del Sistema de Gestión de Taller v2.0.

Ejecutar:
    python main.py

Requisitos:
    pip install pandas numpy matplotlib
"""

from ui.app import TallerApp

if __name__ == "__main__":
    app = TallerApp()
    app.mainloop()
