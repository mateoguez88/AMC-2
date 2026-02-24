"""Tests para el modulo de normalizacion."""

import numpy as np
import pandas as pd
import pytest

from app.normalization import normalize_matrix, METHODS, METHOD_LABELS


@pytest.fixture
def sample_matrix():
    """Matriz de decision de ejemplo 3x4."""
    return pd.DataFrame(
        [[10, 200, 5, 30], [20, 100, 10, 20], [15, 150, 8, 25]],
        index=["A1", "A2", "A3"],
        columns=["C1", "C2", "C3", "C4"],
    )


@pytest.fixture
def criteria_types():
    return ["SUMA", "SUMA", "RESTA", "SUMA"]


class TestMinMaxNormalization:
    def test_values_in_0_1(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "min_max")
        assert result.min().min() >= 0.0
        assert result.max().max() <= 1.0

    def test_benefit_direction(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "min_max")
        # C1 es SUMA (beneficio): mayor valor original -> mayor valor normalizado
        assert result.loc["A2", "C1"] > result.loc["A1", "C1"]

    def test_cost_direction(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "min_max")
        # C3 es RESTA (costo): menor valor original -> mayor valor normalizado
        assert result.loc["A1", "C3"] > result.loc["A2", "C3"]

    def test_shape_preserved(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "min_max")
        assert result.shape == sample_matrix.shape

    def test_equal_values_return_half(self):
        df = pd.DataFrame([[5, 5], [5, 5]], columns=["C1", "C2"])
        result = normalize_matrix(df, ["SUMA", "SUMA"], "min_max")
        assert np.allclose(result.values, 0.5)


class TestZScoreNormalization:
    def test_mean_near_zero(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "z_score")
        # Media de cada columna debe ser ~0
        assert np.allclose(result.mean().values, 0, atol=1e-10)

    def test_std_near_one(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "z_score")
        stds = result.std(ddof=0).values
        assert np.allclose(stds, 1.0, atol=1e-10)


class TestSumNormalization:
    def test_columns_sum_to_one(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "sum")
        for col in result.columns:
            assert abs(result[col].sum() - 1.0) < 1e-10


class TestMaxNormalization:
    def test_max_is_one(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "max")
        for col in result.columns:
            assert abs(result[col].max() - 1.0) < 1e-10

    def test_all_positive(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "max")
        assert (result.values >= 0).all()


class TestVectorNormalization:
    def test_vector_length_one(self, sample_matrix, criteria_types):
        result = normalize_matrix(sample_matrix, criteria_types, "vector")
        for col in result.columns:
            length = np.sqrt((result[col] ** 2).sum())
            assert abs(length - 1.0) < 1e-10


class TestEdgeCases:
    def test_wrong_criteria_length_raises(self, sample_matrix):
        with pytest.raises(ValueError, match="criteria_types"):
            normalize_matrix(sample_matrix, ["SUMA", "SUMA"], "min_max")

    def test_unknown_method_fallback(self, sample_matrix, criteria_types):
        # Metodo desconocido debe usar min_max como fallback
        result = normalize_matrix(sample_matrix, criteria_types, "desconocido")
        expected = normalize_matrix(sample_matrix, criteria_types, "min_max")
        pd.testing.assert_frame_equal(result, expected)

    def test_single_row(self):
        df = pd.DataFrame([[10, 20]], columns=["C1", "C2"])
        result = normalize_matrix(df, ["SUMA", "SUMA"], "min_max")
        assert result.shape == (1, 2)

    def test_method_labels_exist(self):
        for method in METHODS:
            assert method in METHOD_LABELS
