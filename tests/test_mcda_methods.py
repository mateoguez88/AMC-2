"""Tests para los metodos MCDA."""

import numpy as np
import pandas as pd
import pytest

from app.mcda_methods import weighted_sum, topsis, electre_i, compare_methods, WSResult, TOPSISResult, ELECTREResult


@pytest.fixture
def dm():
    """Matriz de decision 4x3."""
    return pd.DataFrame(
        [[8, 7, 9], [6, 9, 7], [9, 6, 8], [7, 8, 6]],
        index=["Alt1", "Alt2", "Alt3", "Alt4"],
        columns=["Ind1", "Ind2", "Ind3"],
    )


@pytest.fixture
def weights():
    return np.array([0.4, 0.35, 0.25])


@pytest.fixture
def criteria_types():
    return ["SUMA", "SUMA", "RESTA"]


class TestWeightedSum:
    def test_returns_ws_result(self, dm, weights, criteria_types):
        result = weighted_sum(dm, weights, criteria_types)
        assert isinstance(result, WSResult)

    def test_ranking_has_correct_columns(self, dm, weights, criteria_types):
        result = weighted_sum(dm, weights, criteria_types)
        assert "alternative" in result.ranking.columns
        assert "score" in result.ranking.columns
        assert "rank" in result.ranking.columns

    def test_ranking_sorted(self, dm, weights, criteria_types):
        result = weighted_sum(dm, weights, criteria_types)
        ranks = result.ranking["rank"].values
        assert list(ranks) == sorted(ranks)

    def test_n_alternatives_match(self, dm, weights, criteria_types):
        result = weighted_sum(dm, weights, criteria_types)
        assert len(result.ranking) == len(dm)

    def test_contributions_shape(self, dm, weights, criteria_types):
        result = weighted_sum(dm, weights, criteria_types)
        assert result.contributions.shape == dm.shape

    def test_scores_positive(self, dm, weights, criteria_types):
        result = weighted_sum(dm, weights, criteria_types)
        assert (result.ranking["score"] >= 0).all()


class TestTOPSIS:
    def test_returns_topsis_result(self, dm, weights, criteria_types):
        result = topsis(dm, weights, criteria_types)
        assert isinstance(result, TOPSISResult)

    def test_scores_between_0_and_1(self, dm, weights, criteria_types):
        result = topsis(dm, weights, criteria_types)
        scores = result.ranking["score"].values
        assert (scores >= 0).all() and (scores <= 1).all()

    def test_distances_positive(self, dm, weights, criteria_types):
        result = topsis(dm, weights, criteria_types)
        assert (result.ranking["dist_positive"] >= 0).all()
        assert (result.ranking["dist_negative"] >= 0).all()

    def test_ranking_columns(self, dm, weights, criteria_types):
        result = topsis(dm, weights, criteria_types)
        required_cols = {"alternative", "score", "dist_positive", "dist_negative", "rank"}
        assert required_cols.issubset(result.ranking.columns)


class TestELECTRE:
    def test_returns_electre_result(self, dm, weights, criteria_types):
        result = electre_i(dm, weights, criteria_types)
        assert isinstance(result, ELECTREResult)

    def test_concordance_matrix_shape(self, dm, weights, criteria_types):
        n = len(dm)
        result = electre_i(dm, weights, criteria_types)
        assert result.concordance_matrix.shape == (n, n)

    def test_discordance_matrix_shape(self, dm, weights, criteria_types):
        n = len(dm)
        result = electre_i(dm, weights, criteria_types)
        assert result.discordance_matrix.shape == (n, n)

    def test_concordance_values_in_range(self, dm, weights, criteria_types):
        result = electre_i(dm, weights, criteria_types)
        assert result.concordance_matrix.min().min() >= 0
        assert result.concordance_matrix.max().max() <= 1

    def test_discordance_values_in_range(self, dm, weights, criteria_types):
        result = electre_i(dm, weights, criteria_types)
        assert result.discordance_matrix.min().min() >= 0
        assert result.discordance_matrix.max().max() <= 1

    def test_ranking_has_columns(self, dm, weights, criteria_types):
        result = electre_i(dm, weights, criteria_types)
        assert "alternative" in result.ranking.columns
        assert "net_flow" in result.ranking.columns
        assert "rank" in result.ranking.columns


class TestCompare:
    def test_compare_returns_dataframe(self, dm, weights, criteria_types):
        result = compare_methods(dm, weights, criteria_types)
        assert isinstance(result, pd.DataFrame)

    def test_compare_has_all_methods(self, dm, weights, criteria_types):
        result = compare_methods(dm, weights, criteria_types)
        for prefix in ("WS_rank", "TOPSIS_rank", "ELECTRE_rank"):
            assert prefix in result.columns

    def test_compare_n_rows(self, dm, weights, criteria_types):
        result = compare_methods(dm, weights, criteria_types)
        assert len(result) == len(dm)


class TestInputValidation:
    def test_mismatched_weights_raises(self, dm, criteria_types):
        with pytest.raises(ValueError):
            weighted_sum(dm, np.array([0.5, 0.5]), criteria_types)

    def test_mismatched_criteria_raises(self, dm, weights):
        with pytest.raises(ValueError):
            weighted_sum(dm, weights, ["SUMA", "SUMA"])
