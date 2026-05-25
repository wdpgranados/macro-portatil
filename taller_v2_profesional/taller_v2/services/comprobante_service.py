"""
services/comprobante_service.py — Generación de comprobante PDF.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from config import MONEDA
from domain.item_carrito import ItemCarrito

# ── Ruta absoluta a la carpeta comprobantes ───────────────────────
BASE_DIR = Path(os.path.abspath(__file__)).parent.parent
COMPROBANTES_DIR = BASE_DIR / "comprobantes"


class ComprobanteService:

    def __init__(self) -> None:
        COMPROBANTES_DIR.mkdir(parents=True, exist_ok=True)

    def generar(
        self,
        items: list[ItemCarrito],
        subtotal: float,
        descuento: float,
        total_final: float,
        vendedor: str = "Administrador",
        num_venta: str = "",
        cliente: str = "Público General",
    ) -> Path:
        """
        Genera un PDF con el comprobante de venta.
        """

        if not num_venta:
            num_venta = datetime.now().strftime("V%Y%m%d%H%M%S")

        archivo = COMPROBANTES_DIR / f"comprobante_{num_venta}.pdf"

        # ── Documento PDF ─────────────────────────────────────────
        doc = SimpleDocTemplate(
            str(archivo),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # ── Colores ───────────────────────────────────────────────
        azul = colors.HexColor("#1E3A5F")
        azul_m = colors.HexColor("#2E75B6")
        verde = colors.HexColor("#22c55e")
        rojo = colors.HexColor("#ef4444")
        gris = colors.HexColor("#F5F5F5")

        # ── Estilos ───────────────────────────────────────────────
        estilo_titulo = ParagraphStyle(
            "titulo",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.white,
            alignment=TA_CENTER,
        )

        estilo_sub = ParagraphStyle(
            "sub",
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.white,
            alignment=TA_CENTER,
        )

        estilo_pie = ParagraphStyle(
            "pie",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.white,
            alignment=TA_CENTER,
        )

        elementos = []

        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════

        tabla_header = Table(
            [
                [Paragraph("MACRO PORTATIL", estilo_titulo)],
                [Paragraph("Sistema de Gestión de Taller", estilo_sub)],
            ],
            colWidths=[doc.width],
        )

        tabla_header.setStyle(
            TableStyle(
                [
                    # Fondos
                    ("BACKGROUND", (0, 0), (0, 0), azul),
                    ("BACKGROUND", (0, 1), (0, 1), azul_m),
                    # Alineación
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    # Padding
                    ("TOPPADDING", (0, 0), (0, 0), 18),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 10),
                    ("TOPPADDING", (0, 1), (0, 1), 8),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 14),
                    # Bordes
                    ("BOX", (0, 0), (-1, -1), 0, colors.white),
                    ("GRID", (0, 0), (-1, -1), 0, colors.white),
                ]
            )
        )

        tabla_header.hAlign = "CENTER"

        elementos.append(tabla_header)
        elementos.append(Spacer(1, 0.5 * cm))

        # ═══════════════════════════════════════════════════════════
        # DATOS DEL COMPROBANTE
        # ═══════════════════════════════════════════════════════════

        fecha = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")

        datos = [
            ["N Comprobante:", num_venta, "Fecha:", fecha],
            ["Vendedor:", vendedor, "Cliente:", cliente],  # ← MODIFICAR
            ["Estado:", "PAGADO", "", ""],
        ]

        tabla_datos = Table(
            datos,
            colWidths=[4 * cm, 5 * cm, 3 * cm, 5 * cm],
        )

        tabla_datos.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), gris),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, 0), (0, -1), azul),
                    ("TEXTCOLOR", (2, 0), (2, -1), azul),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elementos.append(tabla_datos)
        elementos.append(Spacer(1, 0.5 * cm))

        # ═══════════════════════════════════════════════════════════
        # TABLA DE PRODUCTOS
        # ═══════════════════════════════════════════════════════════

        filas = [["ID Pieza", "Descripción", "Cant.", "Precio Unit.", "Subtotal"]]

        for item in items:
            filas.append(
                [
                    item.id_pieza,
                    item.nombre,
                    str(item.cantidad),
                    f"{MONEDA}{item.precio_unitario:,.2f}",
                    f"{MONEDA}{item.subtotal:,.2f}",
                ]
            )

        tabla_items = Table(
            filas,
            colWidths=[3 * cm, 6.5 * cm, 2 * cm, 3 * cm, 2.5 * cm],
        )

        tabla_items.setStyle(
            TableStyle(
                [
                    # Header
                    ("BACKGROUND", (0, 0), (-1, 0), azul),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    # Contenido
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                    # Filas alternadas
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, gris]),
                    # Bordes
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                    # Padding
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elementos.append(tabla_items)
        elementos.append(Spacer(1, 0.5 * cm))

        # ═══════════════════════════════════════════════════════════
        # TOTALES
        # ═══════════════════════════════════════════════════════════

        totales = [
            ["", "Subtotal:", f"{MONEDA}{subtotal:,.2f}"],
            ["", "Descuento:", f"-{MONEDA}{descuento:,.2f}"],
            ["", "TOTAL:", f"{MONEDA}{total_final:,.2f}"],
        ]

        tabla_totales = Table(
            totales,
            colWidths=[9.5 * cm, 4 * cm, 3.5 * cm],
        )

        tabla_totales.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (1, 0), (1, 1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 2), (2, 2), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 1), 10),
                    ("FONTSIZE", (0, 2), (-1, 2), 14),
                    ("TEXTCOLOR", (2, 1), (2, 1), rojo),
                    ("TEXTCOLOR", (1, 2), (2, 2), verde),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LINEABOVE", (1, 2), (2, 2), 1, azul),
                ]
            )
        )

        elementos.append(tabla_totales)
        elementos.append(Spacer(1, 1 * cm))

        # ═══════════════════════════════════════════════════════════
        # PIE DE PÁGINA
        # ═══════════════════════════════════════════════════════════

        tabla_pie = Table(
            [[Paragraph("Gracias por su compra — MACRO PORTATIL", estilo_pie)]],
            colWidths=[doc.width],
        )

        tabla_pie.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), azul_m),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("BOX", (0, 0), (-1, -1), 0, colors.white),
                ]
            )
        )

        elementos.append(tabla_pie)

        # ═══════════════════════════════════════════════════════════
        # GENERAR PDF
        # ═══════════════════════════════════════════════════════════

        print(f">>> Intentando generar PDF en: {archivo.resolve()}")
        print(f">>> Carpeta existe: {COMPROBANTES_DIR.exists()}")
        print(f">>> Items recibidos: {len(items)}")

        doc.build(elementos)

        print(">>> PDF generado exitosamente")

        return archivo.resolve()
