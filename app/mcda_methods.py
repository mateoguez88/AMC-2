"""
Metodos de Analisis Multicriterio: Suma Ponderada, TOPSIS, ELECTRE I.
Implementaciones vectorizadas con NumPy para maximo rendimiento.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from app.normalization import normalize_matrix

logger = logging.getLogger(__name__)


# ── Tipos de retorno estructurados ────────────────────────────────────

@dataclass
class WSResult:
    """Resultado del metodo de Suma Ponderada."""
    ranking: pd.DataFrame
    contributions: pd.DataFrame


@dataclass
class TOPSISResult:
    """Resultado del metodo TOPSIS."""
    ranking: pd.DataFrame


@dataclass
class ELECTREResult:
    """Resultado del metodo ELECTRE I."""
    ranking: pd.DataFrame
    concordance_matrix: np.ndarray
    discordance_matrix: np.ndarray
    outranking_matrix: np.ndarray


# ── Validacion ────────────────────────────────────────────────────────

def _validate_inputs(
    decision_matrix: pd.DataFrame,
    weights: np.ndarray,
    criteria_types: list[str],
) -> None:
    """Valida coherencia entre matriz, pesos y tipos de criterio."""
    n_cols = decision_matrix.shape[1]
    if len(weights) != n_cols:
        raise ValueError(
            f"Longitud de pesos ({len(weights)}) no coincide con "
            f"columnas de la matriz ({n_cols})."
        )
    if len(criteria_types) != n_cols:
        raise ValueError(
            f"Longitud de criteria_types ({len(criteria_types)}) no coincide con "
            f"columnas de la matriz ({n_cols})."
        )
    if decision_matrix.empty:
        raise ValueError("La matriz de decision esta vacia.")


# ── Suma Ponderada ────────────────────────────────────────────────────

def weighted_sum(
    decision_matrix: pd.DataFrame,
    weights: np.ndarray,
    criteria_types: list[str],
    normalization_method: str = "min_max",
) -> WSResult:
    """Metodo de Suma Ponderada (el mismo que usa el Excel original).

    Args:
        decision_matrix: Alternativas (filas) x Criterios (columnas).
        weights: Vector de pesos normalizados.
        criteria_types: 'SUMA' (beneficio) o 'RESTA' (costo) por criterio.
        normalization_method: Metodo de normalizacion a usar.

    Returns:
        WSResult con ranking y contribuciones por criterio.
    """
    _validate_inputs(decision_matrix, weights, criteria_types)

    normalized = normalize_matrix(decision_matrix, criteria_types, normalization_method)
    norm_values = normalized.values
    scores = norm_values @ weights

    result = pd.DataFrame({
        "alternative": decision_matrix.index,
        "score": scores,
    })
    result["rank"] = result["score"].rank(ascending=False, method="min").astype(int)
    result = result.sort_values("rank")

    # Contribucion por criterio (vectorizado)
    contributions = pd.DataFrame(
        norm_values * weights[np.newaxis, :],
        index=decision_matrix.index,
        columns=decision_matrix.columns,
    )

    return WSResult(ranking=result, contributions=contributions)


# ── TOPSIS ────────────────────────────────────────────────────────────

def topsis(
    decision_matrix: pd.DataFrame,
    weights: np.ndarray,
    criteria_types: list[str],
) -> TOPSISResult:
    """Metodo TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution).

    Args:
        decision_matrix: Alternativas (filas) x Criterios (columnas).
        weights: Vector de pesos normalizados.
        criteria_types: 'SUMA' o 'RESTA' por criterio.

    Returns:
        TOPSISResult con ranking incluyendo closeness coefficient.
    """
    _validate_inputs(decision_matrix, weights, criteria_types)

    matrix = decision_matrix.values.astype(float)
    is_benefit = np.array([t.upper().strip() == "SUMA" for t in criteria_types])

    # Paso 1: Normalizacion vectorial
    norms = np.sqrt(np.sum(matrix ** 2, axis=0))
    norms = np.where(norms == 0, 1.0, norms)
    normalized = matrix / norms

    # Paso 2: Matriz ponderada
    weighted = normalized * weights

    # Paso 3: Solucion ideal positiva y negativa (vectorizado)
    ideal_positive = np.where(is_benefit, np.max(weighted, axis=0), np.min(weighted, axis=0))
    ideal_negative = np.where(is_benefit, np.min(weighted, axis=0), np.max(weighted, axis=0))

    # Paso 4: Distancias euclidianas
    dist_positive = np.sqrt(np.sum((weighted - ideal_positive) ** 2, axis=1))
    dist_negative = np.sqrt(np.sum((weighted - ideal_negative) ** 2, axis=1))

    # Paso 5: Coeficiente de proximidad
    denominator = dist_positive + dist_negative
    denominator = np.where(denominator == 0, 1.0, denominator)
    closeness = dist_negative / denominator

    result = pd.DataFrame({
        "alternative": decision_matrix.index,
        "score": closeness,
        "dist_positive": dist_positive,
        "dist_negative": dist_negative,
    })
    result["rank"] = result["score"].rank(ascending=False, method="min").astype(int)
    result = result.sort_values("rank")

    return TOPSISResult(ranking=result)


# ── ELECTRE I ─────────────────────────────────────────────────────────

def electre_i(
    decision_matrix: pd.DataFrame,
    weights: np.ndarray,
    criteria_types: list[str],
    concordance_threshold: float = 0.65,
    discordance_threshold: float = 0.35,
) -> ELECTREResult:
    """Metodo ELECTRE I (ELimination Et Choix Traduisant la REalite).

    Implementacion vectorizada usando broadcasting de NumPy.

    Args:
        decision_matrix: Alternativas (filas) x Criterios (columnas).
        weights: Vector de pesos normalizados.
        criteria_types: 'SUMA' o 'RESTA' por criterio.
        concordance_threshold: Umbral de concordancia (default 0.65).
        discordance_threshold: Umbral de discordancia (default 0.35).

    Returns:
        ELECTREResult con ranking, matrices de concordancia/discordancia y superacion.
    """
    _validate_inputs(decision_matrix, weights, criteria_types)

    normalized = normalize_matrix(decision_matrix, criteria_types, "min_max")
    matrix = normalized.values.astype(float)
    n_alt = matrix.shape[0]

    # Vectorizado con broadcasting: diff[i,j,k] = matrix[i,k] - matrix[j,k]
    diff = matrix[:, np.newaxis, :] - matrix[np.newaxis, :, :]  # (n_alt, n_alt, n_crit)

    # Concordancia: suma de pesos donde a_i >= a_j (por criterio)
    concordance_mask = diff >= 0  # (n_alt, n_alt, n_crit)
    concordance_matrix = np.sum(concordance_mask * weights[np.newaxis, np.newaxis, :], axis=2)

    # Discordancia: max diferencia negativa / max rango global
    negative_diff = np.maximum(-diff, 0)  # (n_alt, n_alt, n_crit)
    max_neg_diff = np.max(negative_diff, axis=2)  # (n_alt, n_alt)
    max_range = np.max(np.ptp(matrix, axis=0))
    discordance_matrix = max_neg_diff / max_range if max_range > 0 else np.zeros((n_alt, n_alt))

    # Diagonal a 0
    np.fill_diagonal(concordance_matrix, 0)
    np.fill_diagonal(discordance_matrix, 0)

    # Matriz de superacion
    outranking = (concordance_matrix >= concordance_threshold) & (discordance_matrix <= discordance_threshold)
    np.fill_diagonal(outranking, False)

    # Score: alternativas que supera - alternativas que la superan
    dominance_score = np.sum(outranking, axis=1) - np.sum(outranking, axis=0)

    result = pd.DataFrame({
        "alternative": decision_matrix.index,
        "score": dominance_score,
        "outranks": np.sum(outranking, axis=1),
        "outranked_by": np.sum(outranking, axis=0),
    })
    result["rank"] = result["score"].rank(ascending=False, method="min").astype(int)
    result = result.sort_values("rank")

    return ELECTREResult(
        ranking=result,
        concordance_matrix=concordance_matrix,
        discordance_matrix=discordance_matrix,
        outranking_matrix=outranking.astype(int),
    )


# ── Comparacion de metodos ───────────────────────────────────────────

def compare_methods(
    decision_matrix: pd.DataFrame,
    weights: np.ndarray,
    criteria_types: list[str],
) -> pd.DataFrame:
    """Ejecuta los tres metodos y compara rankings usando merge.

    Returns:
        DataFrame con rankings de cada metodo lado a lado.
    """
    ws_result = weighted_sum(decision_matrix, weights, criteria_types)
    topsis_result = topsis(decision_matrix, weights, criteria_types)
    electre_result = electre_i(decision_matrix, weights, criteria_types)

    # Usar merge en lugar de indexacion posicional (mas robusto)
    ws_df = ws_result.ranking[["alternative", "score", "rank"]].rename(
        columns={"score": "WS_score", "rank": "WS_rank"}
    )
    topsis_df = topsis_result.ranking[["alternative", "score", "rank"]].rename(
        columns={"score": "TOPSIS_score", "rank": "TOPSIS_rank"}
    )
    electre_df = electre_result.ranking[["alternative", "score", "rank"]].rename(
        columns={"score": "ELECTRE_score", "rank": "ELECTRE_rank"}
    )

    comparison = ws_df.merge(topsis_df, on="alternative").merge(electre_df, on="alternative")
    return comparison
