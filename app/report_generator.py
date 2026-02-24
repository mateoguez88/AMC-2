"""
Generador de reportes PDF para AMC usando ReportLab.
Incluye soporte para graficos Plotly exportados como imagenes.
"""
from __future__ import annotations

import io
import logging
import os
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

# ── Estilos reutilizables ────────────────────────────────────────────

_PRIMARY = "#1f77b4"
_SUCCESS = "#27ae60"
_PURPLE = "#8e44ad"
_ORANGE = "#e67e22"
_DARK = "#2c3e50"
_DARK2 = "#34495e"
_ALT_ROW = "#f0f4f8"
_ALT_ROW_GREEN = "#eafaf1"


def _get_styles():
    """Crea estilos personalizados para el reporte."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", parent=base["Title"], fontSize=22, spaceAfter=20,
            textColor=colors.HexColor(_PRIMARY), alignment=TA_CENTER,
        ),
        "heading": ParagraphStyle(
            "ReportHeading", parent=base["Heading1"], fontSize=16,
            spaceBefore=20, spaceAfter=10, textColor=colors.HexColor(_DARK),
        ),
        "subheading": ParagraphStyle(
            "ReportSubheading", parent=base["Heading2"], fontSize=13,
            spaceBefore=12, spaceAfter=6, textColor=colors.HexColor(_DARK2),
        ),
        "body": ParagraphStyle(
            "ReportBody", parent=base["Normal"], fontSize=10,
            spaceBefore=4, spaceAfter=4,
        ),
        "center": ParagraphStyle(
            "ReportCenter", parent=base["Normal"], fontSize=12, alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "ReportFooter", parent=base["Normal"], fontSize=8,
            alignment=TA_CENTER, textColor=colors.grey,
        ),
        "best": ParagraphStyle(
            "ReportBest", parent=base["Normal"], fontSize=12,
            textColor=colors.HexColor(_SUCCESS),
        ),
    }


def _make_table(data: list[list], col_widths: list, header_color: str = _PRIMARY) -> Table:
    """Crea una tabla formateada con estilo consistente."""
    table = Table(data, colWidths=[w * cm for w in col_widths])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_ALT_ROW)]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    return table


def _add_plotly_image(elements: list, fig, width_cm: float = 16, height_cm: float = 10) -> None:
    """Intenta exportar un grafico Plotly como imagen e insertarlo en el PDF."""
    try:
        from app.charts import export_figure_to_image
        img_bytes = export_figure_to_image(fig, width=800, height=500)
        if img_bytes:
            img_io = io.BytesIO(img_bytes)
            img = Image(img_io, width=width_cm * cm, height=height_cm * cm)
            elements.append(img)
            elements.append(Spacer(1, 0.5 * cm))
    except Exception as e:
        logger.warning("No se pudo insertar grafico en PDF: %s", e)


def generate_report(report_data: dict, output_path: str | None = None) -> str:
    """Genera un reporte PDF completo del analisis multicriterio.

    Args:
        report_data: Diccionario con todos los datos del reporte:
            - title: Titulo del reporte
            - data: AMCData con datos del modelo
            - results: DataFrame con resultados del ranking
            - contributions: DataFrame con contribuciones
            - weights: np.ndarray con pesos usados
            - sections: Lista de secciones a incluir
            - sensitivity: DataFrame de sensibilidad OAT
            - monte_carlo: DataFrame resumen Monte Carlo
            - comparison: DataFrame comparacion de metodos
            - figures: Dict {nombre: go.Figure} con graficos a insertar
        output_path: Ruta de salida del PDF.

    Returns:
        Ruta al archivo PDF generado.
    """
    if output_path is None:
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"AMC_Reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = _get_styles()
    elements: list = []
    data = report_data.get("data")
    results = report_data.get("results")
    sections = report_data.get("sections", [])
    figures = report_data.get("figures", {})

    # --- PORTADA ---
    elements.append(Spacer(1, 4 * cm))
    elements.append(Paragraph(report_data.get("title", "Analisis Multicriterio"), styles["title"]))
    elements.append(Spacer(1, 1 * cm))
    elements.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor(_PRIMARY)))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["center"],
    ))
    if data:
        elements.append(Paragraph(
            f"Escenario: {data.scenario} | Plazo: {data.timeframe}", styles["center"],
        ))
    elements.append(PageBreak())

    section_num = 0

    # --- RESUMEN ---
    if "Resumen" in sections and data:
        section_num += 1
        elements.append(Paragraph(f"{section_num}. Resumen del Modelo", styles["heading"]))
        elements.append(Paragraph(
            f"Este analisis multicriterio evalua <b>{data.n_alternatives} alternativas</b> "
            f"utilizando <b>{data.n_indicators} indicadores</b> agrupados en "
            f"<b>{data.n_visions} visiones</b>.",
            styles["body"],
        ))
        elements.append(Spacer(1, 0.5 * cm))

        # Tabla de alternativas
        elements.append(Paragraph("Alternativas evaluadas:", styles["subheading"]))
        alt_data = [["ID", "Nombre"]]
        for _, row in data.alternatives.iterrows():
            alt_data.append([str(row["ID"]), str(row["NOMBRE"])])
        elements.append(_make_table(alt_data, [3, 12]))
        elements.append(Spacer(1, 0.5 * cm))

    # --- PESOS ---
    if "Pesos" in sections and data:
        section_num += 1
        elements.append(Paragraph(f"{section_num}. Ponderacion", styles["heading"]))

        if not data.visions.empty and "PONDERACION" in data.visions.columns:
            elements.append(Paragraph("Pesos de las Visiones:", styles["subheading"]))
            weight_data = [["Vision", "Peso"]]
            for _, row in data.visions.iterrows():
                weight_data.append([
                    str(row.get("VISION", "")),
                    f"{float(row.get('PONDERACION', 0)):.4f}",
                ])
            elements.append(_make_table(weight_data, [10, 5]))

            # Insertar grafico de pesos si disponible
            if "weights_pie" in figures:
                _add_plotly_image(elements, figures["weights_pie"])

        elements.append(Spacer(1, 0.5 * cm))

    # --- RESULTADOS ---
    if "Resultados" in sections and results is not None:
        section_num += 1
        elements.append(Paragraph(f"{section_num}. Resultados del Analisis", styles["heading"]))
        elements.append(Paragraph("Ranking de alternativas (Suma Ponderada):", styles["subheading"]))

        result_rows = [["Ranking", "Alternativa", "Score"]]
        for _, row in results.iterrows():
            result_rows.append([
                str(int(row["rank"])),
                str(row["alternative"]),
                f"{row['score']:.4f}",
            ])
        elements.append(_make_table(result_rows, [3, 8, 4], header_color=_SUCCESS))
        elements.append(Spacer(1, 0.5 * cm))

        # Mejor alternativa
        best = results.iloc[0]
        elements.append(Paragraph(
            f"<b>Mejor alternativa:</b> {best['alternative']} con un score de {best['score']:.4f}",
            styles["best"],
        ))

        # Insertar grafico de ranking si disponible
        if "ranking_bar" in figures:
            _add_plotly_image(elements, figures["ranking_bar"])

    # --- GRAFICOS ---
    if "Graficos" in sections and figures:
        for name, fig in figures.items():
            if name not in ("weights_pie", "ranking_bar"):  # Ya insertados
                _add_plotly_image(elements, fig)

    # --- COMPARACION DE METODOS ---
    if "Comparacion" in sections:
        comparison = report_data.get("comparison")
        if comparison is not None:
            section_num += 1
            elements.append(PageBreak())
            elements.append(Paragraph(f"{section_num}. Comparacion de Metodos", styles["heading"]))

            comp_data = [["Alternativa", "WS Rank", "TOPSIS Rank", "ELECTRE Rank"]]
            for _, row in comparison.iterrows():
                comp_data.append([
                    str(row["alternative"]),
                    str(int(row["WS_rank"])),
                    str(int(row["TOPSIS_rank"])),
                    str(int(row["ELECTRE_rank"])),
                ])
            elements.append(_make_table(comp_data, [6, 3, 3, 3], header_color=_PURPLE))

    # --- SENSIBILIDAD ---
    if "Sensibilidad" in sections:
        mc_summary = report_data.get("monte_carlo")
        if mc_summary is not None:
            section_num += 1
            elements.append(PageBreak())
            elements.append(Paragraph(
                f"{section_num}. Analisis de Sensibilidad (Monte Carlo)", styles["heading"],
            ))

            mc_data = [["Alternativa", "Score Medio", "Desv. Std", "Rank Medio", "% Primero", "% Top 3"]]
            for _, row in mc_summary.iterrows():
                mc_data.append([
                    str(row["alternative"]),
                    f"{row['mean_score']:.4f}",
                    f"{row['std_score']:.4f}",
                    f"{row['mean_rank']:.2f}",
                    f"{row['pct_first']:.1f}%",
                    f"{row['pct_top3']:.1f}%",
                ])
            elements.append(_make_table(mc_data, [5, 2.5, 2.5, 2.5, 2, 2], header_color=_ORANGE))

    # --- PIE DE PAGINA ---
    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Paragraph(
        f"Generado automaticamente por AMC Tool | {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["footer"],
    ))

    # Construir PDF
    doc.build(elements)
    logger.info("Reporte PDF generado: %s", output_path)
    return output_path
