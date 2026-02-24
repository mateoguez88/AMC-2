"""
Analisis de sensibilidad y Monte Carlo para AMC.
Incluye implementaciones vectorizadas para maximo rendimiento.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from app.normalization import normalize_matrix
from app.mcda_methods import weighted_sum, topsis, WSResult, TOPSISResult

logger = logging.getLogger(__name__)


def one_at_a_time_sensitivity(
    decision_matrix: pd.DataFrame,
    base_weights: np.ndarray,
    criteria_types: list[str],
    variation_pct: float = 0.10,
    method: str = "weighted_sum",
) -> pd.DataFrame:
    """Analisis de sensibilidad uno-a-la-vez (OAT).

    Varia cada peso individualmente +/- variation_pct y registra el cambio en ranking.

    Returns:
        DataFrame con el impacto de cada criterio en el ranking.
    """
    results = []

    # Resultado base
    base_result = _run_method(decision_matrix, base_weights, criteria_types, method)
    base_ranks = dict(zip(base_result["alternative"], base_result["rank"]))
    base_scores = dict(zip(base_result["alternative"], base_result["score"]))

    n_weights = len(base_weights)
    col_names = decision_matrix.columns.tolist()

    for i in range(n_weights):
        for direction in (-1, 1):
            modified_weights = base_weights.copy()
            delta = base_weights[i] * variation_pct * direction
            modified_weights[i] += delta

            # Renormalizar
            total = modified_weights.sum()
            if total > 0:
                modified_weights = modified_weights / total

            mod_result = _run_method(decision_matrix, modified_weights, criteria_types, method)
            mod_ranks = dict(zip(mod_result["alternative"], mod_result["rank"]))
            mod_scores = dict(zip(mod_result["alternative"], mod_result["score"]))

            for alt in base_ranks:
                results.append({
                    "criterion_index": i,
                    "criterion_name": col_names[i] if i < len(col_names) else f"C{i}",
                    "direction": "+" if direction > 0 else "-",
                    "variation_pct": variation_pct * 100 * direction,
                    "alternative": alt,
                    "base_score": base_scores[alt],
                    "modified_score": mod_scores.get(alt, 0),
                    "score_change": mod_scores.get(alt, 0) - base_scores[alt],
                    "base_rank": base_ranks[alt],
                    "modified_rank": mod_ranks.get(alt, 0),
                    "rank_change": mod_ranks.get(alt, 0) - base_ranks[alt],
                })

    return pd.DataFrame(results)


def vision_sensitivity(
    decision_matrix: pd.DataFrame,
    base_vision_weights: np.ndarray,
    indicator_vision_map: list[str],
    indicator_weights_within_vision: np.ndarray,
    criteria_types: list[str],
    variation_pct: float = 0.10,
) -> pd.DataFrame:
    """Analisis de sensibilidad a nivel de visiones.

    Varia el peso de cada vision y recalcula los pesos globales de indicadores.
    """
    results = []
    n_visions = len(base_vision_weights)
    vision_ids = sorted(set(indicator_vision_map))

    # Resultado base
    base_global_weights = _compute_global_weights(
        base_vision_weights, indicator_vision_map, indicator_weights_within_vision, vision_ids
    )
    base_result = _run_method(decision_matrix, base_global_weights, criteria_types, "weighted_sum")
    base_ranks = dict(zip(base_result["alternative"], base_result["rank"]))
    base_scores = dict(zip(base_result["alternative"], base_result["score"]))

    for v_idx in range(n_visions):
        for direction in (-1, 1):
            mod_vision_weights = base_vision_weights.copy()
            delta = base_vision_weights[v_idx] * variation_pct * direction
            mod_vision_weights[v_idx] += delta
            mod_vision_weights = np.maximum(mod_vision_weights, 0)
            total = mod_vision_weights.sum()
            if total > 0:
                mod_vision_weights = mod_vision_weights / total

            mod_global_weights = _compute_global_weights(
                mod_vision_weights, indicator_vision_map, indicator_weights_within_vision, vision_ids
            )
            mod_result = _run_method(decision_matrix, mod_global_weights, criteria_types, "weighted_sum")
            mod_ranks = dict(zip(mod_result["alternative"], mod_result["rank"]))
            mod_scores = dict(zip(mod_result["alternative"], mod_result["score"]))

            for alt in base_ranks:
                results.append({
                    "vision_index": v_idx,
                    "vision_id": vision_ids[v_idx] if v_idx < len(vision_ids) else f"V{v_idx + 1}",
                    "direction": "+" if direction > 0 else "-",
                    "variation_pct": variation_pct * 100 * direction,
                    "alternative": alt,
                    "base_score": base_scores[alt],
                    "modified_score": mod_scores.get(alt, 0),
                    "score_change": mod_scores.get(alt, 0) - base_scores[alt],
                    "base_rank": base_ranks[alt],
                    "modified_rank": mod_ranks.get(alt, 0),
                    "rank_change": mod_ranks.get(alt, 0) - base_ranks[alt],
                })

    return pd.DataFrame(results)


def monte_carlo_simulation(
    decision_matrix: pd.DataFrame,
    base_weights: np.ndarray,
    criteria_types: list[str],
    n_simulations: int = 1000,
    weight_variation: float = 0.20,
    distribution: str = "uniform",
    method: str = "weighted_sum",
    seed: int = 42,
    progress_callback: callable | None = None,
) -> pd.DataFrame:
    """Simulacion Monte Carlo vectorizada sobre los pesos.

    Genera n_simulations conjuntos de pesos aleatorios y calcula rankings.
    Para Suma Ponderada, usa multiplicacion matricial vectorizada (x20 mas rapido).

    Args:
        decision_matrix: Matriz de decision.
        base_weights: Pesos base.
        criteria_types: Tipos de criterio.
        n_simulations: Numero de simulaciones.
        weight_variation: Variacion maxima de los pesos (fraccion).
        distribution: 'uniform' o 'triangular'.
        method: 'weighted_sum' o 'topsis'.
        seed: Semilla aleatoria.
        progress_callback: Funcion callback(pct: float) para reportar progreso.

    Returns:
        DataFrame con resultados de todas las simulaciones.
    """
    rng = np.random.default_rng(seed)
    n_weights = len(base_weights)
    n_alts = decision_matrix.shape[0]
    alt_names = decision_matrix.index.tolist()

    # Generar todas las perturbaciones de pesos de una vez
    if distribution == "uniform":
        noise = rng.uniform(-weight_variation, weight_variation, size=(n_simulations, n_weights))
    else:  # triangular
        noise = rng.triangular(-weight_variation, 0, weight_variation, size=(n_simulations, n_weights))

    all_weights = base_weights[np.newaxis, :] * (1 + noise)  # (n_sims, n_weights)
    all_weights = np.maximum(all_weights, 0)
    row_sums = all_weights.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    all_weights = all_weights / row_sums

    # --- Camino rapido: Suma Ponderada vectorizada ---
    if method == "weighted_sum":
        normalized = normalize_matrix(decision_matrix, criteria_types, "min_max")
        norm_values = normalized.values  # (n_alts, n_weights)

        # Multiplicacion matricial: (n_alts, n_weights) @ (n_weights, n_sims) = (n_alts, n_sims)
        all_scores = norm_values @ all_weights.T

        # Rankings vectorizados: argsort de argsort da el ranking
        # Rank descendente: negar scores
        all_ranks = np.argsort(np.argsort(-all_scores, axis=0), axis=0) + 1

        # Construir DataFrame de resultados eficientemente
        sim_indices = np.repeat(np.arange(n_simulations), n_alts)
        alt_indices = np.tile(np.arange(n_alts), n_simulations)

        all_results = pd.DataFrame({
            "simulation": sim_indices,
            "alternative": [alt_names[i] for i in alt_indices],
            "score": all_scores.T.ravel(),
            "rank": all_ranks.T.ravel().astype(int),
        })

        if progress_callback:
            progress_callback(1.0)

        return all_results

    # --- Camino lento: TOPSIS (no totalmente vectorizable) ---
    all_results = []
    batch_size = max(1, n_simulations // 20)

    for sim in range(n_simulations):
        sim_weights = all_weights[sim]
        result = topsis(decision_matrix, sim_weights, criteria_types)

        for _, row in result.ranking.iterrows():
            all_results.append({
                "simulation": sim,
                "alternative": row["alternative"],
                "score": row["score"],
                "rank": int(row["rank"]),
            })

        if progress_callback and (sim + 1) % batch_size == 0:
            progress_callback((sim + 1) / n_simulations)

    if progress_callback:
        progress_callback(1.0)

    return pd.DataFrame(all_results)


def monte_carlo_summary(mc_results: pd.DataFrame) -> pd.DataFrame:
    """Resume los resultados de Monte Carlo por alternativa."""
    summary = mc_results.groupby("alternative").agg(
        mean_score=("score", "mean"),
        std_score=("score", "std"),
        min_score=("score", "min"),
        max_score=("score", "max"),
        median_score=("score", "median"),
        mean_rank=("rank", "mean"),
        std_rank=("rank", "std"),
        best_rank=("rank", "min"),
        worst_rank=("rank", "max"),
        pct_first=("rank", lambda x: (x == 1).mean() * 100),
        pct_top3=("rank", lambda x: (x <= 3).mean() * 100),
    ).reset_index()

    summary = summary.sort_values("mean_rank")
    return summary


# ── Funciones internas ───────────────────────────────────────────────

def _run_method(
    decision_matrix: pd.DataFrame,
    weights: np.ndarray,
    criteria_types: list[str],
    method: str,
) -> pd.DataFrame:
    """Ejecuta un metodo MCDA y retorna el DataFrame de ranking."""
    if method == "weighted_sum":
        result = weighted_sum(decision_matrix, weights, criteria_types)
        return result.ranking
    else:
        result = topsis(decision_matrix, weights, criteria_types)
        return result.ranking


def _compute_global_weights(
    vision_weights: np.ndarray,
    indicator_vision_map: list[str],
    indicator_weights_within_vision: np.ndarray,
    vision_ids: list[str],
) -> np.ndarray:
    """Calcula pesos globales de indicadores a partir de pesos de visiones."""
    global_weights = np.zeros(len(indicator_vision_map))
    vision_weight_map = {v_id: vision_weights[i] for i, v_id in enumerate(vision_ids)}

    for i, v_id in enumerate(indicator_vision_map):
        v_weight = vision_weight_map.get(v_id, 0)
        global_weights[i] = v_weight * indicator_weights_within_vision[i]

    total = global_weights.sum()
    if total > 0:
        global_weights = global_weights / total
    return global_weights
