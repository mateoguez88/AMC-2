"""Tests para el modulo AHP."""

import numpy as np
import pytest

from app.ahp import consistency_ratio, compute_weights, build_comparison_matrix, AHPResult


@pytest.fixture
def consistent_matrix_3x3():
    """Matriz AHP 3x3 perfectamente consistente."""
    return np.array([
        [1.0, 3.0, 5.0],
        [1 / 3, 1.0, 5 / 3],
        [1 / 5, 3 / 5, 1.0],
    ])


@pytest.fixture
def identity_matrix():
    """Matriz identidad (todo igual)."""
    return np.eye(4)


class TestConsistencyRatio:
    def test_returns_ahp_result(self, consistent_matrix_3x3):
        result = consistency_ratio(consistent_matrix_3x3)
        assert isinstance(result, AHPResult)

    def test_consistent_matrix(self, consistent_matrix_3x3):
        result = consistency_ratio(consistent_matrix_3x3)
        assert result.is_consistent
        assert result.CR < 0.10

    def test_identity_is_consistent(self, identity_matrix):
        result = consistency_ratio(identity_matrix)
        assert result.is_consistent

    def test_identity_equal_weights(self, identity_matrix):
        result = consistency_ratio(identity_matrix)
        expected = np.ones(4) / 4
        np.testing.assert_allclose(result.weights, expected, atol=1e-6)

    def test_weights_sum_to_one(self, consistent_matrix_3x3):
        result = consistency_ratio(consistent_matrix_3x3)
        assert abs(result.weights.sum() - 1.0) < 1e-10

    def test_small_matrix_no_ri(self):
        """Matriz 2x2 siempre es consistente (RI=0)."""
        m = np.array([[1.0, 3.0], [1 / 3, 1.0]])
        result = consistency_ratio(m)
        assert result.is_consistent


class TestComputeWeights:
    def test_weights_sum_to_one(self, consistent_matrix_3x3):
        w = compute_weights(consistent_matrix_3x3)
        assert abs(w.sum() - 1.0) < 1e-10

    def test_weights_positive(self, consistent_matrix_3x3):
        w = compute_weights(consistent_matrix_3x3)
        assert (w > 0).all()

    def test_dominant_criterion(self):
        m = np.array([
            [1.0, 9.0, 9.0],
            [1 / 9, 1.0, 1.0],
            [1 / 9, 1.0, 1.0],
        ])
        w = compute_weights(m)
        assert w[0] > w[1]
        assert w[0] > w[2]

    def test_non_square_raises(self):
        with pytest.raises(ValueError):
            compute_weights(np.array([[1.0, 2.0]]))

    def test_negative_values_raise(self):
        with pytest.raises(ValueError):
            compute_weights(np.array([[1.0, -1.0], [-1.0, 1.0]]))


class TestBuildComparisonMatrix:
    def test_output_shape(self):
        values = {(0, 1): 3.0, (0, 2): 5.0, (1, 2): 2.0}
        m = build_comparison_matrix(3, values)
        assert m.shape == (3, 3)

    def test_diagonal_is_one(self):
        values = {(0, 1): 3.0}
        m = build_comparison_matrix(2, values)
        np.testing.assert_array_equal(np.diag(m), [1.0, 1.0])

    def test_reciprocal(self):
        values = {(0, 1): 4.0}
        m = build_comparison_matrix(2, values)
        assert m[0, 1] == 4.0
        assert abs(m[1, 0] - 0.25) < 1e-10
