"""
Modulo de normalizacion para Analisis Multicriterio.
Soporta multiples metodos: Min-Max, Z-score, Max, Sum, Vector.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def min_max(values: np.ndarray, is_benefit: bool = True) -> np.ndarray:
    """Normalizacion Min-Max (la usada en el Excel original).

    Para criterios de beneficio (SUMA): (valor - min) / (max - min)
    Para criterios de costo (RESTA):   (max - valor) / (max - min)
    """
    v_min = np.nanmin(values)
    v_max = np.nanmax(values)
    rango = v_max - v_min
    if rango == 0:
        return np.full_like(values, 0.5, dtype=float)
    if is_benefit:
        return (values - v_min) / rango
    else:
        return (v_max - values) / rango


def z_score(values: np.ndarray, is_benefit: bool = True) -> np.ndarray:
    """Normalizacion Z-score (estandarizacion)."""
    mean = np.nanmean(values)
    std = np.nanstd(values, ddof=0)
    if std == 0:
        return np.zeros_like(values, dtype=float)
    normalized = (values - mean) / std
    if not is_benefit:
        normalized = -normalized
    return normalized


def max_normalization(values: np.ndarray, is_benefit: bool = True) -> np.ndarray:
    """Normalizacion por maximo: valor / max."""
    v_max = np.nanmax(np.abs(values))
    if v_max == 0:
        return np.zeros_like(values, dtype=float)
    if is_benefit:
        return values / v_max
    else:
        v_min = np.nanmin(values)
        rango = v_max - v_min
        return (v_max - values) / rango if rango != 0 else np.full_like(values, 0.5, dtype=float)


def sum_normalization(values: np.ndarray, is_benefit: bool = True) -> np.ndarray:
    """Normalizacion por suma: valor / sum(valores)."""
    if is_benefit:
        total = np.nansum(values)
        if total == 0:
            return np.full_like(values, 1.0 / max(len(values), 1), dtype=float)
        return values / total
    else:
        # Para costos: invertir y normalizar, con proteccion contra division por 0
        safe_values = np.where(values == 0, np.finfo(float).eps, values)
        inverted = 1.0 / safe_values
        inv_total = np.nansum(inverted)
        if inv_total == 0:
            return np.full_like(values, 1.0 / max(len(values), 1), dtype=float)
        return inverted / inv_total


def vector_normalization(values: np.ndarray, is_benefit: bool = True) -> np.ndarray:
    """Normalizacion vectorial: valor / sqrt(sum(valores^2)). Usada en TOPSIS."""
    norm = np.sqrt(np.nansum(values ** 2))
    if norm == 0:
        return np.zeros_like(values, dtype=float)
    normalized = values / norm
    if not is_benefit:
        normalized = 1.0 - normalized
    return normalized


METHODS: dict[str, callable] = {
    "min_max": min_max,
    "z_score": z_score,
    "max": max_normalization,
    "sum": sum_normalization,
    "vector": vector_normalization,
}

METHOD_LABELS: dict[str, str] = {
    "min_max": "Min-Max (original)",
    "z_score": "Z-Score",
    "max": "Maximo",
    "sum": "Suma",
    "vector": "Vectorial",
}


def normalize_matrix(
    decision_matrix: pd.DataFrame,
    criteria_types: list[str],
    method: str = "min_max",
) -> pd.DataFrame:
    """Normaliza una matriz de decision completa.

    Args:
        decision_matrix: DataFrame con alternativas en filas y criterios en columnas.
        criteria_types: Lista de 'SUMA' (beneficio) o 'RESTA' (costo) por criterio.
        method: Metodo de normalizacion ('min_max', 'z_score', 'max', 'sum', 'vector').

    Returns:
        DataFrame normalizado con la misma estructura.

    Raises:
        ValueError: Si la longitud de criteria_types no coincide con las columnas.
    """
    if len(criteria_types) != decision_matrix.shape[1]:
        raise ValueError(
            f"criteria_types ({len(criteria_types)}) no coincide con "
            f"columnas de la matriz ({decision_matrix.shape[1]})."
        )

    norm_func = METHODS.get(method)
    if norm_func is None:
        logger.warning("Metodo '%s' no reconocido, usando 'min_max'.", method)
        norm_func = min_max

    matrix = decision_matrix.values.astype(float)
    normalized = np.empty_like(matrix, dtype=float)

    for i in range(matrix.shape[1]):
        is_benefit = criteria_types[i].upper().strip() == "SUMA"
        normalized[:, i] = norm_func(matrix[:, i], is_benefit)

    return pd.DataFrame(normalized, index=decision_matrix.index, columns=decision_matrix.columns)
