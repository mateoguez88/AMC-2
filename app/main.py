"""
Dashboard Interactivo AMC - Analisis Multicriterio
Aplicacion Streamlit con 7 paginas:
1. Inicio - Carga y resumen
2. Pesos - AHP interactivo
3. Resultados - Rankings
4. Visualizaciones - Graficos avanzados
5. Comparacion de Metodos
6. Sensibilidad y Monte Carlo
7. Reporte
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
import tempfile

# Asegurar que el directorio raiz del proyecto esta en el path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau

from app.data_loader import (
    AMCData, load_from_excel, get_decision_matrix,
    get_weights_from_data, get_linear_weights, group_by_vision,
)
from app.ahp import consistency_ratio, compute_weights, AHPResult
from app.mcda_methods import weighted_sum, topsis, electre_i, compare_methods, WSResult
from app.normalization import normalize_matrix, METHODS, METHOD_LABELS
from app.sensitivity import (
    one_at_a_time_sensitivity, monte_carlo_simulation, monte_carlo_summary, vision_sensitivity,
)
from app.charts import (
    ranking_bar_chart, radar_chart, heatmap_chart, stacked_bar_chart,
    waterfall_chart, tornado_chart, parallel_coordinates_chart,
    monte_carlo_box_plot, monte_carlo_rank_histogram, bump_chart,
    methods_comparison_chart, weights_pie_chart, ahp_consistency_gauge,
)

logger = logging.getLogger(__name__)

# --- Configuracion de pagina ---
st.set_page_config(
    page_title="AMC - Analisis Multicriterio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS personalizado ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# UTILIDADES Y CACHE
# ============================================================

@st.cache_data(show_spinner="Cargando datos del Excel...")
def _cached_load_excel(file_bytes: bytes, _file_hash: str) -> AMCData:
    """Carga datos del Excel con cache basado en hash del archivo."""
    with tempfile.NamedTemporaryFile(suffix=".xlsm", delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name
    try:
        return load_from_excel(tmp_path, include_reference=False)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _get_active_weights(data: AMCData) -> tuple[np.ndarray, str]:
    """Obtiene los pesos activos segun la seleccion del usuario."""
    weight_type = st.session_state.get("weight_type", "Ponderado (AHP)")
    if weight_type == "Lineal (igual)":
        return get_linear_weights(data), "Lineal"
    elif weight_type == "Personalizado (sliders)":
        custom_vw = st.session_state.get("custom_vision_weights", data.vision_weights)
        return _recalculate_global_weights(data, custom_vw), "Personalizado"
    else:
        return get_weights_from_data(data), "Ponderado"


def _recalculate_global_weights(data: AMCData, custom_vision_weights: np.ndarray) -> np.ndarray:
    """Recalcula pesos globales de indicadores con pesos de vision personalizados."""
    indicators = data.indicators
    vision_ids = data.vision_ids

    vision_weight_map = {}
    for i, v_id in enumerate(vision_ids):
        if i < len(custom_vision_weights):
            vision_weight_map[v_id] = custom_vision_weights[i]

    global_weights = np.zeros(len(indicators))
    for idx, (_, row) in enumerate(indicators.iterrows()):
        v_id = row.get("ID VISION", "")
        v_weight = vision_weight_map.get(v_id, 1.0 / max(len(vision_ids), 1))
        same_vision = indicators[indicators["ID VISION"] == v_id]
        n_in_vision = max(len(same_vision), 1)
        global_weights[idx] = v_weight / n_in_vision

    total = global_weights.sum()
    if total > 0:
        global_weights = global_weights / total
    return global_weights


def main():
    # --- Sidebar ---
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/combo-chart.png", width=80)
        st.title("AMC Tool")
        st.markdown("---")

        # Carga de archivo
        uploaded_file = st.file_uploader(
            "Cargar archivo Excel (.xlsm/.xlsx)",
            type=["xlsm", "xlsx"],
            help="Sube tu archivo de Analisis Multicriterio",
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            try:
                data = _cached_load_excel(file_bytes, file_hash)
                st.session_state.amc_data = data
                st.success(f"Datos cargados: {data.n_alternatives} alternativas, {data.n_indicators} indicadores")
            except Exception as e:
                st.error(f"Error al cargar: {e}")
                st.session_state.amc_data = None

        st.markdown("---")

        page = st.radio(
            "Navegacion",
            [
                "🏠 Inicio",
                "⚖️ Pesos y AHP",
                "🏆 Resultados",
                "📊 Visualizaciones",
                "🔄 Comparacion Metodos",
                "🎲 Sensibilidad",
                "📄 Reporte",
            ],
        )

    # --- Contenido principal ---
    data: AMCData | None = st.session_state.get("amc_data")

    pages = {
        "🏠 Inicio": page_inicio,
        "⚖️ Pesos y AHP": page_pesos,
        "🏆 Resultados": page_resultados,
        "📊 Visualizaciones": page_visualizaciones,
        "🔄 Comparacion Metodos": page_comparacion,
        "🎲 Sensibilidad": page_sensibilidad,
        "📄 Reporte": page_reporte,
    }
    pages[page](data)


# ============================================================
# PAGINA 1: INICIO
# ============================================================
def page_inicio(data: AMCData | None):
    st.markdown('<div class="main-header">Analisis Multicriterio - Dashboard</div>', unsafe_allow_html=True)

    if data is None:
        st.warning("Por favor, carga un archivo Excel desde la barra lateral.")
        st.markdown("""
        ### Bienvenido a la herramienta AMC

        Esta aplicacion permite realizar analisis multicriterio avanzado con:
        - **Suma Ponderada** (metodo del Excel original)
        - **TOPSIS** (distancia a solucion ideal)
        - **ELECTRE I** (relaciones de superacion)
        - **Analisis de Sensibilidad** y **Monte Carlo**
        - **Graficos interactivos** con Plotly

        Sube tu archivo Excel para comenzar.
        """)
        return

    # Metricas principales
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alternativas", data.n_alternatives)
    col2.metric("Indicadores", data.n_indicators)
    col3.metric("Visiones", data.n_visions)
    col4.metric("Escenario", data.scenario or "N/A")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Alternativas")
        st.dataframe(data.alternatives[["ID", "NOMBRE"]].reset_index(drop=True), use_container_width=True)
    with col2:
        st.subheader("Visiones")
        if not data.visions.empty and "VISION" in data.visions.columns:
            vision_display = data.visions[["ID VISION", "VISION"]].copy()
            if "PONDERACION" in data.visions.columns:
                vision_display["Peso"] = data.visions["PONDERACION"].astype(float).round(4)
            st.dataframe(vision_display.reset_index(drop=True), use_container_width=True)

    st.subheader("Indicadores")
    ind_cols = ["ID", "ID VISION", "INDICADOR", "SUMA O RESTA"]
    if "PESO_PONDERADO" in data.indicators.columns:
        ind_cols.append("PESO_PONDERADO")
    indicator_display = data.indicators[ind_cols].copy()
    if "PESO_PONDERADO" in indicator_display.columns:
        indicator_display["PESO_PONDERADO"] = indicator_display["PESO_PONDERADO"].astype(float).round(6)
    st.dataframe(indicator_display, use_container_width=True, height=400)

    st.subheader("Matriz de Valores")
    st.dataframe(data.values_matrix, use_container_width=True, height=300)


# ============================================================
# PAGINA 2: PESOS Y AHP
# ============================================================
def page_pesos(data: AMCData | None):
    st.header("⚖️ Ponderacion y AHP")

    if data is None:
        st.warning("Carga un archivo Excel primero.")
        return

    tab1, tab2, tab3 = st.tabs(["Pesos de Visiones", "Matriz AHP", "Pesos de Indicadores"])

    with tab1:
        st.subheader("Ajustar Pesos de Visiones")
        st.markdown("Usa los sliders para ajustar los pesos de cada vision. Los pesos se normalizan automaticamente.")

        vision_names = data.vision_names
        current_weights = data.vision_weights.copy()

        if "custom_vision_weights" not in st.session_state:
            st.session_state.custom_vision_weights = current_weights.copy()

        n_cols = min(4, len(vision_names))
        cols = st.columns(n_cols)
        new_weights = []

        for i, (name, weight) in enumerate(zip(vision_names, st.session_state.custom_vision_weights)):
            with cols[i % n_cols]:
                w = st.slider(
                    f"{data.vision_ids[i]}: {name[:30]}",
                    min_value=0.0, max_value=1.0,
                    value=float(weight), step=0.01,
                    key=f"vision_weight_{i}",
                )
                new_weights.append(w)

        new_weights = np.array(new_weights)
        total = new_weights.sum()
        normalized = new_weights / total if total > 0 else np.ones(len(new_weights)) / len(new_weights)
        st.session_state.custom_vision_weights = normalized

        fig = weights_pie_chart(normalized, data.vision_ids, "Distribucion de Pesos de Visiones")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Matriz de Comparacion Pareada (AHP)")

        if data.ahp_matrix.size > 0:
            n = data.ahp_matrix.shape[0]
            labels = data.vision_ids[:n]

            ahp_df = pd.DataFrame(data.ahp_matrix, index=labels, columns=labels)
            st.dataframe(ahp_df.round(3), use_container_width=True)

            cr_result = consistency_ratio(data.ahp_matrix)

            col1, col2 = st.columns(2)
            with col1:
                fig = ahp_consistency_gauge(cr_result.CR)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.metric("Lambda Max", f"{cr_result.lambda_max:.4f}")
                st.metric("Indice de Consistencia (CI)", f"{cr_result.CI:.4f}")
                st.metric("Indice Aleatorio (RI)", f"{cr_result.RI:.4f}")
                st.metric("Ratio de Consistencia (CR)", f"{cr_result.CR:.4f}")
                if cr_result.is_consistent:
                    st.success("La matriz es CONSISTENTE (CR < 0.10)")
                else:
                    st.error("La matriz es INCONSISTENTE (CR >= 0.10). Revise las comparaciones.")

            st.subheader("Pesos derivados del AHP")
            ahp_weights_df = pd.DataFrame({"Vision": labels, "Peso AHP": cr_result.weights})
            st.dataframe(ahp_weights_df.round(4), use_container_width=True)
        else:
            st.info("No se encontro matriz AHP en el archivo.")

    with tab3:
        st.subheader("Pesos por Indicador")
        weight_cols = ["ID", "ID VISION", "INDICADOR"]
        if "PESO_LINEAL" in data.indicators.columns:
            weight_cols.append("PESO_LINEAL")
        if "PESO_PONDERADO" in data.indicators.columns:
            weight_cols.append("PESO_PONDERADO")
        weights_df = data.indicators[weight_cols].copy()
        for c in ("PESO_LINEAL", "PESO_PONDERADO"):
            if c in weights_df.columns:
                weights_df[c] = weights_df[c].astype(float).round(6)
        st.dataframe(weights_df, use_container_width=True, height=500)

        st.session_state["weight_type"] = st.radio(
            "Tipo de pesos para el analisis:",
            ["Ponderado (AHP)", "Lineal (igual)", "Personalizado (sliders)"],
            horizontal=True,
        )


# ============================================================
# PAGINA 3: RESULTADOS
# ============================================================
def page_resultados(data: AMCData | None):
    st.header("🏆 Resultados del Analisis")

    if data is None:
        st.warning("Carga un archivo Excel primero.")
        return

    dm = get_decision_matrix(data)
    criteria_types = data.criteria_types
    weights, weight_label = _get_active_weights(data)

    norm_method = st.selectbox(
        "Metodo de normalizacion:",
        list(METHODS.keys()),
        index=0,
        format_func=lambda x: METHOD_LABELS.get(x, x),
    )

    method = st.selectbox("Metodo MCDA:", ["Suma Ponderada", "TOPSIS"], index=0)

    if st.button("Calcular", type="primary"):
        with st.spinner("Calculando..."):
            if method == "Suma Ponderada":
                ws_result = weighted_sum(dm, weights, criteria_types, norm_method)
                st.session_state["last_results"] = ws_result.ranking
                st.session_state["last_contributions"] = ws_result.contributions

                col1, col2 = st.columns([2, 1])
                with col1:
                    fig = ranking_bar_chart(ws_result.ranking, f"Ranking - Suma Ponderada ({weight_label})")
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.subheader("Tabla de Resultados")
                    st.dataframe(ws_result.ranking.round(4), use_container_width=True)
            else:
                topsis_result = topsis(dm, weights, criteria_types)
                st.session_state["last_results"] = topsis_result.ranking

                col1, col2 = st.columns([2, 1])
                with col1:
                    fig = ranking_bar_chart(
                        topsis_result.ranking, f"Ranking - TOPSIS ({weight_label})", method_name="TOPSIS",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.subheader("Tabla de Resultados")
                    display_cols = ["alternative", "score", "dist_positive", "dist_negative", "rank"]
                    st.dataframe(topsis_result.ranking[display_cols].round(4), use_container_width=True)


# ============================================================
# PAGINA 4: VISUALIZACIONES
# ============================================================
def page_visualizaciones(data: AMCData | None):
    st.header("📊 Visualizaciones Avanzadas")

    if data is None:
        st.warning("Carga un archivo Excel primero.")
        return

    dm = get_decision_matrix(data)
    criteria_types = data.criteria_types
    weights = get_weights_from_data(data)
    normalized = normalize_matrix(dm, criteria_types, "min_max")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Radar", "Heatmap", "Barras Apiladas", "Waterfall", "Coordenadas Paralelas",
    ])

    with tab1:
        st.subheader("Grafico Radar por Vision")
        radar_data = group_by_vision(normalized, data.indicators)

        selected_alts = st.multiselect(
            "Seleccionar alternativas:",
            dm.index.tolist(),
            default=dm.index.tolist(),
        )
        vision_ids = sorted(data.indicators["ID VISION"].unique())
        fig = radar_chart(radar_data, vision_ids, selected_alts)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Heatmap de Rendimiento Normalizado")
        group_by = st.checkbox("Agrupar por vision", value=True)

        if group_by:
            grouped = group_by_vision(normalized, data.indicators)
            fig = heatmap_chart(grouped, "Rendimiento Promedio por Vision")
        else:
            fig = heatmap_chart(normalized, "Rendimiento por Indicador")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Contribucion por Vision")
        ws_result = weighted_sum(dm, weights, criteria_types)
        vision_map = dict(zip(dm.columns, data.indicators["ID VISION"].tolist()))
        fig = stacked_bar_chart(ws_result.contributions, vision_map)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Descomposicion del Score (Waterfall)")
        ws_result = weighted_sum(dm, weights, criteria_types)
        alt_selected = st.selectbox("Seleccionar alternativa:", dm.index.tolist())

        if alt_selected in ws_result.contributions.index:
            indicator_vision = data.indicators["ID VISION"].tolist()
            vision_map = dict(zip(dm.columns, indicator_vision))
            contrib_series = ws_result.contributions.loc[alt_selected]

            grouped_contrib = pd.Series(dtype=float)
            for v_id in sorted(set(indicator_vision)):
                cols = [c for c in contrib_series.index if vision_map.get(c) == v_id]
                if cols:
                    grouped_contrib[v_id] = contrib_series[cols].sum()

            fig = waterfall_chart(alt_selected, grouped_contrib)
            st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader("Coordenadas Paralelas")
        fig = parallel_coordinates_chart(normalized)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PAGINA 5: COMPARACION DE METODOS
# ============================================================
def page_comparacion(data: AMCData | None):
    st.header("🔄 Comparacion de Metodos MCDA")

    if data is None:
        st.warning("Carga un archivo Excel primero.")
        return

    dm = get_decision_matrix(data)
    criteria_types = data.criteria_types
    weights = get_weights_from_data(data)

    if st.button("Ejecutar Comparacion", type="primary"):
        with st.spinner("Ejecutando Suma Ponderada, TOPSIS y ELECTRE I..."):
            comparison = compare_methods(dm, weights, criteria_types)
            st.session_state["comparison"] = comparison

    comparison = st.session_state.get("comparison")
    if comparison is not None:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = methods_comparison_chart(comparison)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Tabla Comparativa")
            st.dataframe(comparison.round(4), use_container_width=True)

        # Concordancia entre metodos
        st.subheader("Analisis de Concordancia")
        methods_pairs = [("WS", "TOPSIS"), ("WS", "ELECTRE"), ("TOPSIS", "ELECTRE")]
        concordance_data = []

        for m1, m2 in methods_pairs:
            r1 = comparison[f"{m1}_rank"].values
            r2 = comparison[f"{m2}_rank"].values
            sp_rho, sp_p = spearmanr(r1, r2)
            kt_tau, kt_p = kendalltau(r1, r2)
            concordance_data.append({
                "Metodos": f"{m1} vs {m2}",
                "Spearman rho": round(sp_rho, 4),
                "p-value (Spearman)": round(sp_p, 4),
                "Kendall tau": round(kt_tau, 4),
                "p-value (Kendall)": round(kt_p, 4),
            })

        st.dataframe(pd.DataFrame(concordance_data), use_container_width=True)


# ============================================================
# PAGINA 6: SENSIBILIDAD
# ============================================================
def page_sensibilidad(data: AMCData | None):
    st.header("🎲 Analisis de Sensibilidad y Monte Carlo")

    if data is None:
        st.warning("Carga un archivo Excel primero.")
        return

    dm = get_decision_matrix(data)
    criteria_types = data.criteria_types
    weights = get_weights_from_data(data)

    tab1, tab2 = st.tabs(["Sensibilidad OAT", "Monte Carlo"])

    with tab1:
        st.subheader("Analisis de Sensibilidad Uno-a-la-vez")

        col1, col2 = st.columns(2)
        with col1:
            variation = st.slider("Variacion de pesos (%):", 5, 50, 10) / 100
        with col2:
            sens_method = st.selectbox("Metodo:", ["weighted_sum", "topsis"], key="sens_method")

        if st.button("Ejecutar Sensibilidad", type="primary"):
            with st.spinner("Analizando sensibilidad..."):
                sens_results = one_at_a_time_sensitivity(
                    dm, weights, criteria_types,
                    variation_pct=variation, method=sens_method,
                )
                st.session_state["sens_results"] = sens_results

        sens_results = st.session_state.get("sens_results")
        if sens_results is not None:
            alt_for_tornado = st.selectbox(
                "Alternativa para grafico tornado:",
                dm.index.tolist(),
                key="tornado_alt",
            )
            fig = tornado_chart(sens_results, alt_for_tornado)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Simulacion Monte Carlo")

        col1, col2, col3 = st.columns(3)
        with col1:
            n_sims = st.number_input("Numero de simulaciones:", 100, 10000, 1000, step=100)
        with col2:
            mc_variation = st.slider("Variacion de pesos MC (%):", 5, 50, 20) / 100
        with col3:
            mc_dist = st.selectbox("Distribucion:", ["uniform", "triangular"])

        if st.button("Ejecutar Monte Carlo", type="primary"):
            progress_bar = st.progress(0, text="Ejecutando simulaciones...")

            def _update_progress(pct: float):
                progress_bar.progress(min(pct, 1.0), text=f"Simulacion {int(pct * n_sims)}/{n_sims}")

            mc_results = monte_carlo_simulation(
                dm, weights, criteria_types,
                n_simulations=int(n_sims),
                weight_variation=mc_variation,
                distribution=mc_dist,
                progress_callback=_update_progress,
            )
            st.session_state["mc_results"] = mc_results
            st.session_state["mc_summary"] = monte_carlo_summary(mc_results)
            progress_bar.progress(1.0, text="Completado!")

        mc_results = st.session_state.get("mc_results")
        mc_summary_df = st.session_state.get("mc_summary")

        if mc_results is not None:
            col1, col2 = st.columns(2)
            with col1:
                fig = monte_carlo_box_plot(mc_results)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = monte_carlo_rank_histogram(mc_results)
                st.plotly_chart(fig, use_container_width=True)

            if mc_summary_df is not None:
                st.subheader("Resumen Monte Carlo")
                st.dataframe(mc_summary_df.round(4), use_container_width=True)


# ============================================================
# PAGINA 7: REPORTE
# ============================================================
def page_reporte(data: AMCData | None):
    st.header("📄 Generacion de Reporte")

    if data is None:
        st.warning("Carga un archivo Excel primero.")
        return

    st.markdown("""
    ### Contenido del Reporte
    El reporte incluira:
    - Resumen del modelo (alternativas, indicadores, visiones)
    - Pesos utilizados y verificacion AHP
    - Resultados del analisis (ranking y scores)
    - Graficos principales (si kaleido esta instalado)
    - Analisis de sensibilidad (si fue ejecutado)
    - Comparacion de metodos (si fue ejecutada)
    """)

    report_title = st.text_input("Titulo del reporte:", "Analisis Multicriterio - Reporte de Resultados")
    include_sections = st.multiselect(
        "Secciones a incluir:",
        ["Resumen", "Pesos", "Resultados", "Graficos", "Sensibilidad", "Comparacion"],
        default=["Resumen", "Pesos", "Resultados", "Graficos"],
    )

    if st.button("Generar Reporte PDF", type="primary"):
        try:
            from app.report_generator import generate_report

            dm = get_decision_matrix(data)
            weights = get_weights_from_data(data)
            criteria_types = data.criteria_types
            ws_result = weighted_sum(dm, weights, criteria_types)

            # Preparar graficos para el PDF
            report_figures = {}
            try:
                report_figures["ranking_bar"] = ranking_bar_chart(ws_result.ranking)
                report_figures["weights_pie"] = weights_pie_chart(
                    data.vision_weights, data.vision_ids,
                )
            except Exception:
                pass

            report_data = {
                "title": report_title,
                "data": data,
                "results": ws_result.ranking,
                "contributions": ws_result.contributions,
                "weights": weights,
                "sections": include_sections,
                "figures": report_figures,
                "sensitivity": st.session_state.get("sens_results"),
                "monte_carlo": st.session_state.get("mc_summary"),
                "comparison": st.session_state.get("comparison"),
            }

            pdf_path = generate_report(report_data)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Descargar Reporte PDF",
                    data=f.read(),
                    file_name="AMC_Reporte.pdf",
                    mime="application/pdf",
                )
            st.success("Reporte generado exitosamente!")

        except ImportError:
            st.error("Modulo reportlab no disponible. Instala con: pip install reportlab")
        except Exception as e:
            st.error(f"Error al generar reporte: {e}")
            logger.exception("Error generando reporte PDF")

    # Exportar a Excel
    st.markdown("---")
    st.subheader("Exportar Resultados a Excel")

    if st.button("Exportar a Excel"):
        try:
            dm = get_decision_matrix(data)
            weights = get_weights_from_data(data)
            criteria_types = data.criteria_types
            ws_result = weighted_sum(dm, weights, criteria_types)

            output_path = os.path.join(tempfile.gettempdir(), "AMC_Resultados.xlsx")

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                ws_result.ranking.to_excel(writer, sheet_name="Resultados", index=False)
                ws_result.contributions.to_excel(writer, sheet_name="Contribuciones")
                data.values_matrix.to_excel(writer, sheet_name="Valores")

                comparison = st.session_state.get("comparison")
                if comparison is not None:
                    comparison.to_excel(writer, sheet_name="Comparacion Metodos", index=False)

                mc_summary = st.session_state.get("mc_summary")
                if mc_summary is not None:
                    mc_summary.to_excel(writer, sheet_name="Monte Carlo", index=False)

            with open(output_path, "rb") as f:
                st.download_button(
                    "Descargar Excel",
                    data=f.read(),
                    file_name="AMC_Resultados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            st.success("Exportado correctamente!")

        except Exception as e:
            st.error(f"Error al exportar: {e}")
            logger.exception("Error exportando a Excel")


if __name__ == "__main__":
    main()
