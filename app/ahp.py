"""
Motor AHP (Analytic Hierarchy Process) con verificacion de consistencia.
Implementa el metodo completo de Saaty para elicitacion de pesos.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Indices de consistencia aleatorios de Saaty (para n=1..15)
RANDOM_INDEX: dict[int, float] = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59,
}

# Escala de Saaty
SAATY_SCALE: dict[int, str] = {
    1: "Igual importancia",
    2: "Importancia intermedia entre 1 y 3",
    3: "Importancia moderada",
    4: "Importancia intermedia entre 3 y 5",
    5: "Importancia fuerte",
    6: "Importancia intermedia entre 5 y 7",
    7: "Importancia muy fuerte",
    8: "Importancia intermedia entre 7 y 9",
    9: "Importancia extrema",
}


@dataclass(frozen=True)
class AHPResult:
    """Resultado del analisis AHP con consistencia."""
    weights: np.ndarray
    lambda_max: float
    CI: float
    RI: float
    CR: float
    is_consistent: bool
    n: int


def compute_weights(comparison_matrix: np.ndarray) -> np.ndarray:
    """Calcula los pesos usando el metodo del autovector principal (Saaty).

    Args:
        comparison_matrix: Matriz cuadrada de comparaciones pareadas (n x n).

    Returns:
        Vector de pesos normalizados.

    Raises:
        ValueError: Si la matriz no es cuadrada o contiene valores invalidos.
    """
    if comparison_matrix.ndim != 2 or comparison_matrix.shape[0] != comparison_matrix.shape[1]:
        raise ValueError(f"La matriz debe ser cuadrada, recibida: {comparison_matrix.shape}")
    if np.any(comparison_matrix <= 0):
        raise ValueError("La matriz AHP no puede contener valores <= 0.")

    eigenvalues, eigenvectors = np.linalg.eig(comparison_matrix)
    max_idx = np.argmax(eigenvalues.real)
    principal_eigenvector = eigenvectors[:, max_idx].real
    weights = np.abs(principal_eigenvector)
    total = weights.sum()
    if total > 0:
        weights = weights / total
    return weights


def compute_weights_geometric_mean(comparison_matrix: np.ndarray) -> np.ndarray:
    """Calcula pesos usando el metodo de la media geometrica (alternativo).

    Mas estable numericamente que el metodo del autovector para matrices
    mal condicionadas.
    """
    n = comparison_matrix.shape[0]
    geometric_means = np.prod(comparison_matrix, axis=1) ** (1.0 / n)
    total = geometric_means.sum()
    if total > 0:
        return geometric_means / total
    return np.ones(n) / n


def consistency_ratio(comparison_matrix: np.ndarray) -> AHPResult:
    """Calcula el ratio de consistencia (CR) de una matriz AHP.

    Returns:
        AHPResult con lambda_max, CI, RI, CR, is_consistent, weights.
    """
    n = comparison_matrix.shape[0]
    weights = compute_weights(comparison_matrix)

    # lambda_max: autovalor principal
    weighted_sum_vec = comparison_matrix @ weights
    # Evitar division por cero en pesos muy pequeños
    safe_weights = np.where(weights > 1e-10, weights, 1e-10)
    lambda_values = weighted_sum_vec / safe_weights
    lambda_max = float(np.mean(lambda_values))

    # Indice de consistencia
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0

    # Indice aleatorio
    ri = RANDOM_INDEX.get(n, 1.59)

    # Ratio de consistencia
    cr = ci / ri if ri > 0 else 0.0

    return AHPResult(
        weights=weights,
        lambda_max=lambda_max,
        CI=ci,
        RI=ri,
        CR=cr,
        is_consistent=cr < 0.10 or n <= 2,
        n=n,
    )


def build_comparison_matrix(pairwise_values: dict[tuple[int, int], float], n_criteria: int) -> np.ndarray:
    """Construye una matriz de comparacion a partir de valores pareados.

    Args:
        pairwise_values: Dict con claves (i, j) y valores de comparacion Saaty.
        n_criteria: Numero de criterios.

    Returns:
        Matriz numpy de comparaciones pareadas.
    """
    matrix = np.ones((n_criteria, n_criteria))

    for (i, j), value in pairwise_values.items():
        if value <= 0:
            logger.warning("Valor AHP invalido (%f) para par (%d,%d), usando 1.0", value, i, j)
            value = 1.0
        matrix[i, j] = value
        matrix[j, i] = 1.0 / value

    return matrix


def hierarchical_weights(
    vision_weights: np.ndarray,
    objective_weights_per_vision: dict[str, np.ndarray],
    indicator_weights_per_objective: dict[str, np.ndarray],
    vision_ids: list[str],
    objective_ids: dict[str, list[str]],
    indicator_ids: dict[str, list[str]],
) -> pd.DataFrame:
    """Calcula pesos globales a traves de la jerarquia Vision > Objetivo > Indicador.

    Args:
        vision_weights: Pesos de las visiones (nivel 1).
        objective_weights_per_vision: Dict {vision_id: array de pesos de objetivos}.
        indicator_weights_per_objective: Dict {obj_id: array de pesos de indicadores}.
        vision_ids: IDs de las visiones.
        objective_ids: Dict {vision_id: lista de IDs de objetivos}.
        indicator_ids: Dict {obj_id: lista de IDs de indicadores}.

    Returns:
        DataFrame con peso global de cada indicador.
    """
    rows = []

    for v_idx, v_id in enumerate(vision_ids):
        w_vision = vision_weights[v_idx]
        obj_ids = objective_ids.get(v_id, [])
        n_obj = max(len(obj_ids), 1)
        obj_weights = objective_weights_per_vision.get(v_id, np.ones(n_obj) / n_obj)

        for o_idx, o_id in enumerate(obj_ids):
            w_obj = obj_weights[o_idx] if o_idx < len(obj_weights) else 1.0 / n_obj
            ind_ids = indicator_ids.get(o_id, [])
            n_ind = max(len(ind_ids), 1)
            ind_weights = indicator_weights_per_objective.get(o_id, np.ones(n_ind) / n_ind)

            for i_idx, i_id in enumerate(ind_ids):
                w_ind = ind_weights[i_idx] if i_idx < len(ind_weights) else 1.0 / n_ind
                global_weight = w_vision * w_obj * w_ind
                rows.append({
                    "vision_id": v_id,
                    "objective_id": o_id,
                    "indicator_id": i_id,
                    "weight_vision": w_vision,
                    "weight_objective": w_obj,
                    "weight_indicator": w_ind,
                    "global_weight": global_weight,
                })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Normalizar pesos globales para que sumen 1
    total = df["global_weight"].sum()
    df["global_weight_normalized"] = df["global_weight"] / total if total > 0 else 0.0

    return df
