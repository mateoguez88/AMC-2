"""
Modulo de graficos avanzados con Plotly para AMC.
Incluye: radar, heatmap, barras apiladas, tornado, waterfall,
parallel coordinates, box plots Monte Carlo, bump chart.

Cada funcion retorna un go.Figure listo para mostrar con st.plotly_chart().
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Paleta de colores corporativa (10 colores distintos)
COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

TEMPLATE = "plotly_white"

_LAYOUT_DEFAULTS = dict(template=TEMPLATE, font=dict(family="Inter, Arial, sans-serif"))


def _color(i: int) -> str:
    """Devuelve un color ciclico de la paleta."""
    return COLORS[i % len(COLORS)]


def ranking_bar_chart(
    results: pd.DataFrame,
    title: str = "Ranking de Alternativas",
    score_col: str = "score",
    name_col: str = "alternative",
    method_name: str = "Suma Ponderada",
) -> go.Figure:
    """Grafico de barras horizontales con ranking de alternativas."""
    df = results.sort_values(score_col, ascending=True)

    fig = go.Figure(go.Bar(
        x=df[score_col],
        y=df[name_col],
        orientation="h",
        marker_color=[_color(i) for i in range(len(df))],
        text=[f"{v:.4f}" for v in df[score_col]],
        textposition="outside",
    ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        xaxis_title=f"Score ({method_name})",
        yaxis_title="Alternativa",
        height=max(400, len(df) * 50),
        margin=dict(l=200, r=80),
        **_LAYOUT_DEFAULTS,
    )

    return fig


def radar_chart(
    data: pd.DataFrame,
    categories: list[str],
    alternatives: list[str] | None = None,
    title: str = "Perfil por Vision",
) -> go.Figure:
    """Grafico radar interactivo con overlay de multiples alternativas."""
    if alternatives is None:
        alternatives = data.index.tolist()

    fig = go.Figure()

    for i, alt in enumerate(alternatives):
        if alt not in data.index:
            continue
        values = data.loc[alt].values.tolist()
        values.append(values[0])  # Cerrar poligono
        cats = list(categories) + [categories[0]]

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=cats,
            fill="toself",
            name=str(alt),
            line_color=_color(i),
            opacity=0.7,
        ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=600,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def heatmap_chart(
    data: pd.DataFrame,
    title: str = "Heatmap de Rendimiento",
    colorscale: str = "RdYlGn",
) -> go.Figure:
    """Heatmap de rendimiento: alternativas x indicadores/criterios."""
    fig = go.Figure(go.Heatmap(
        z=data.values,
        x=data.columns.tolist(),
        y=data.index.tolist(),
        colorscale=colorscale,
        text=np.round(data.values, 3).astype(str),
        texttemplate="%{text}",
        textfont={"size": 9},
        hoverongaps=False,
        colorbar=dict(title="Valor"),
    ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        xaxis_title="Indicador",
        yaxis_title="Alternativa",
        height=max(400, len(data) * 50),
        width=max(800, len(data.columns) * 35),
        **_LAYOUT_DEFAULTS,
    )

    return fig


def stacked_bar_chart(
    contributions: pd.DataFrame,
    vision_map: dict[str, str] | None = None,
    title: str = "Contribucion por Vision al Score Total",
) -> go.Figure:
    """Barras apiladas mostrando contribucion de cada vision/criterio al score."""
    if vision_map:
        # Agrupar contribuciones por vision
        unique_visions = sorted(set(vision_map.values()))
        grouped = pd.DataFrame(index=contributions.index)
        for vision_id in unique_visions:
            cols = [c for c in contributions.columns if vision_map.get(c) == vision_id]
            if cols:
                grouped[vision_id] = contributions[cols].sum(axis=1)
        plot_data = grouped
    else:
        plot_data = contributions

    fig = go.Figure()

    for i, col in enumerate(plot_data.columns):
        fig.add_trace(go.Bar(
            name=str(col),
            x=plot_data.index,
            y=plot_data[col],
            marker_color=_color(i),
        ))

    fig.update_layout(
        barmode="stack",
        title=dict(text=title, font_size=18),
        xaxis_title="Alternativa",
        yaxis_title="Contribucion al Score",
        height=500,
        legend=dict(title="Criterio/Vision"),
        **_LAYOUT_DEFAULTS,
    )

    return fig


def waterfall_chart(
    alternative_name: str,
    contributions: pd.Series,
    title: str | None = None,
) -> go.Figure:
    """Grafico waterfall mostrando descomposicion del score de una alternativa."""
    if title is None:
        title = f"Descomposicion del Score - {alternative_name}"

    sorted_contrib = contributions.sort_values(ascending=False)
    total_value = sorted_contrib.sum()

    fig = go.Figure(go.Waterfall(
        name="Contribucion",
        orientation="v",
        measure=["relative"] * len(sorted_contrib) + ["total"],
        x=list(sorted_contrib.index) + ["TOTAL"],
        y=list(sorted_contrib.values) + [0],
        text=[f"{v:.4f}" for v in sorted_contrib.values] + [f"{total_value:.4f}"],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#2ca02c"}},
        decreasing={"marker": {"color": "#d62728"}},
        totals={"marker": {"color": "#1f77b4"}},
    ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        yaxis_title="Contribucion",
        height=500,
        showlegend=False,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def tornado_chart(
    sensitivity_df: pd.DataFrame,
    alternative: str,
    title: str = "Analisis de Sensibilidad (Tornado)",
) -> go.Figure:
    """Grafico tornado mostrando sensibilidad del score a cambios en pesos."""
    alt_data = sensitivity_df[sensitivity_df["alternative"] == alternative].copy()

    if alt_data.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"Sin datos para {alternative}", showarrow=False)
        return fig

    # Calcular rango de cambio por criterio
    impact = alt_data.groupby("criterion_name").agg(
        min_change=("score_change", "min"),
        max_change=("score_change", "max"),
    ).reset_index()
    impact["total_range"] = impact["max_change"] - impact["min_change"]
    impact = impact.sort_values("total_range", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=impact["criterion_name"],
        x=impact["min_change"],
        orientation="h",
        name="Reduccion peso",
        marker_color="#d62728",
    ))

    fig.add_trace(go.Bar(
        y=impact["criterion_name"],
        x=impact["max_change"],
        orientation="h",
        name="Aumento peso",
        marker_color="#2ca02c",
    ))

    fig.update_layout(
        title=dict(text=f"{title} - {alternative}", font_size=18),
        xaxis_title="Cambio en Score",
        yaxis_title="Criterio",
        barmode="overlay",
        height=max(400, len(impact) * 30),
        margin=dict(l=200),
        **_LAYOUT_DEFAULTS,
    )

    return fig


def parallel_coordinates_chart(
    data: pd.DataFrame,
    score_col: str | None = None,
    title: str = "Comparacion de Alternativas (Coordenadas Paralelas)",
) -> go.Figure:
    """Grafico de coordenadas paralelas para comparar alternativas."""
    dimensions = []
    numeric_dtypes = {"float64", "int64", "float32", "int32"}

    for col in data.columns:
        if col == score_col:
            continue
        if str(data[col].dtype) in numeric_dtypes:
            dimensions.append(dict(
                label=str(col),
                values=data[col],
                range=[float(data[col].min()), float(data[col].max())],
            ))

    color_values = list(range(len(data)))
    if score_col and score_col in data.columns:
        color_values = data[score_col].values.tolist()

    fig = go.Figure(go.Parcoords(
        line=dict(
            color=color_values,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Score"),
        ),
        dimensions=dimensions,
    ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        height=500,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def monte_carlo_box_plot(
    mc_results: pd.DataFrame,
    value_col: str = "score",
    title: str = "Distribucion Monte Carlo de Scores",
) -> go.Figure:
    """Box plots de resultados Monte Carlo por alternativa."""
    fig = go.Figure()

    alternatives = (
        mc_results.groupby("alternative")[value_col]
        .mean()
        .sort_values(ascending=False)
        .index
    )

    for i, alt in enumerate(alternatives):
        alt_data = mc_results[mc_results["alternative"] == alt]
        fig.add_trace(go.Box(
            y=alt_data[value_col],
            name=str(alt),
            marker_color=_color(i),
            boxmean="sd",
        ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        yaxis_title=value_col.capitalize(),
        height=500,
        showlegend=False,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def monte_carlo_rank_histogram(
    mc_results: pd.DataFrame,
    title: str = "Frecuencia de Rankings (Monte Carlo)",
) -> go.Figure:
    """Histograma agrupado de frecuencia de rankings por alternativa."""
    alternatives = mc_results.groupby("alternative")["rank"].mean().sort_values().index

    fig = go.Figure()

    for i, alt in enumerate(alternatives):
        alt_data = mc_results[mc_results["alternative"] == alt]
        rank_counts = alt_data["rank"].value_counts().sort_index()

        fig.add_trace(go.Bar(
            x=[f"Rank {r}" for r in rank_counts.index],
            y=rank_counts.values,
            name=str(alt),
            marker_color=_color(i),
        ))

    fig.update_layout(
        barmode="group",
        title=dict(text=title, font_size=18),
        xaxis_title="Ranking",
        yaxis_title="Frecuencia",
        height=500,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def bump_chart(
    scenarios_data: pd.DataFrame,
    title: str = "Evolucion de Rankings por Escenario",
) -> go.Figure:
    """Bump chart mostrando como cambian los rankings entre escenarios."""
    fig = go.Figure()

    alternatives = scenarios_data["alternative"].unique()

    for i, alt in enumerate(alternatives):
        alt_data = scenarios_data[scenarios_data["alternative"] == alt].sort_values("scenario")

        fig.add_trace(go.Scatter(
            x=alt_data["scenario"],
            y=alt_data["rank"],
            mode="lines+markers",
            name=str(alt),
            line=dict(color=_color(i), width=3),
            marker=dict(size=10),
        ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        xaxis_title="Escenario",
        yaxis_title="Ranking",
        yaxis=dict(autorange="reversed"),
        height=500,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def methods_comparison_chart(
    comparison_df: pd.DataFrame,
    title: str = "Comparacion de Rankings por Metodo",
) -> go.Figure:
    """Grafico comparativo de rankings entre diferentes metodos MCDA."""
    methods = ["WS", "TOPSIS", "ELECTRE"]
    rank_cols = [f"{m}_rank" for m in methods]

    fig = go.Figure()

    for i, alt in enumerate(comparison_df["alternative"]):
        ranks = [
            comparison_df.loc[comparison_df["alternative"] == alt, col].values[0]
            for col in rank_cols
        ]

        fig.add_trace(go.Scatter(
            x=methods,
            y=ranks,
            mode="lines+markers",
            name=str(alt),
            line=dict(color=_color(i), width=2),
            marker=dict(size=10),
        ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        xaxis_title="Metodo",
        yaxis_title="Ranking",
        yaxis=dict(autorange="reversed"),
        height=500,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def weights_pie_chart(
    weights: np.ndarray,
    labels: list[str],
    title: str = "Distribucion de Pesos",
) -> go.Figure:
    """Grafico de pie/donut para distribucion de pesos."""
    fig = go.Figure(go.Pie(
        labels=labels,
        values=weights,
        hole=0.4,
        textinfo="label+percent",
        marker_colors=COLORS[:len(weights)],
    ))

    fig.update_layout(
        title=dict(text=title, font_size=18),
        height=500,
        **_LAYOUT_DEFAULTS,
    )

    return fig


def ahp_consistency_gauge(cr: float, threshold: float = 0.10) -> go.Figure:
    """Indicador tipo gauge para el ratio de consistencia AHP."""
    color = "#2ca02c" if cr < threshold else "#d62728"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=cr,
        delta={
            "reference": threshold,
            "increasing": {"color": "#d62728"},
            "decreasing": {"color": "#2ca02c"},
        },
        gauge={
            "axis": {"range": [0, 0.3]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, threshold], "color": "#d4edda"},
                {"range": [threshold, 0.3], "color": "#f8d7da"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": threshold,
            },
        },
        title={"text": "Ratio de Consistencia (CR)"},
        number={"suffix": "", "valueformat": ".4f"},
    ))

    fig.update_layout(height=300, **_LAYOUT_DEFAULTS)

    return fig


def export_figure_to_image(fig: go.Figure, width: int = 800, height: int = 500) -> bytes | None:
    """Exporta un grafico Plotly a bytes PNG para insertar en reportes.

    Requiere kaleido instalado. Retorna None si falla.
    """
    try:
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception:
        return None
