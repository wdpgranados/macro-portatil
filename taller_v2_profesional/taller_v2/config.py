"""
config.py — Configuración global del sistema.

Centraliza rutas, tema visual y logging para que ningún otro módulo
tenga valores mágicos (magic strings / magic numbers) dispersos.
"""

from __future__ import annotations

import logging
from pathlib import Path

# ══════════════════════════════════════════════════════════════════
#  RUTAS
# ══════════════════════════════════════════════════════════════════
DB_PATH: Path = Path("taller_v2.db")

# ══════════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("TallerApp")

# ══════════════════════════════════════════════════════════════════
#  TEMA VISUAL  (dark dashboard)
# ══════════════════════════════════════════════════════════════════
THEME: dict[str, str] = {
    "bg":        "#0f1117",
    "surface":   "#1a1d27",
    "surface2":  "#242736",
    "accent":    "#4f8ef7",
    "accent2":   "#7c4dff",
    "success":   "#22c55e",
    "warning":   "#f59e0b",
    "danger":    "#ef4444",
    "text":      "#e2e8f0",
    "text_dim":  "#64748b",
    "border":    "#2e3347",
}

# ══════════════════════════════════════════════════════════════════
#  UMBRALES DE NEGOCIO
# ══════════════════════════════════════════════════════════════════
STOCK_BAJO_UMBRAL: int = 3   # Resalta en rojo si stock < este valor
MAX_VENTAS_HISTORIAL: int = 60  # Filas máximas en tabla de historial

MONEDA: str = "S/"   # Cambia aquí para toda la app