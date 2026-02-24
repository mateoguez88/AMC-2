"""Tests para el modulo de sensibilidad."""

import numpy as np
import pandas as pd
import pytest

from app.sensitivity import one_at_a_time_sensitivity, monte_carlo_simulation, monte_carlo_summary


@pytest.fixture
def dm():
    return pd.DataFrame(
        [[8, 7, 9], [6, 9, 7], [9, 6, 8]],
        index=["A1", "A2", "A3"],
        columns=["I1", "I2", "I3"],
    )


@pytest.fixture
def weights():
    return np.array([0.4, 0.35, 0.25])


@pytest.fixture
def criteria_types():
    return ["SUMA", "SUMA", "RESTA"]


class TestOATSensitivity:
    def test_returns_dict(self, dm, weights, criteria_types):
        result = one_at_a_time_sensitivity(dm, weights, criteria_types, variation_pct=0.1)
        assert isinstance(result, dict)

    def test_has_indicator_keys(self, dm, weights, criteria_types):
        result = one_at_a_time_sensitivity(dm, weights, criteria_types, variation_pct=0.1)
        assert len(result) > 0

    def test_each_entry_has_up_down(self, dm, weights, criteria_types):
        result = one_at_a_time_sensitivity(dm, weights, criteria_types, variation_pct=0.1)
        for key, val in result.items():
            assert "up" in val
            assert "down" in val


class TestMonteCarlo:
    def test_returns_dataframe(self, dm, weights, criteria_types):
        result = monte_carlo_simulation(dm, weights, criteria_types, n_simulations=50)
        assert isinstance(result, pd.DataFrame)

    def test_correct_columns(self, dm, weights, criteria_types):
        result = monte_carlo_simulation(dm, weights, criteria_types, n_simulations=50)
        for alt in dm.index:
            assert alt in result.columns

    def test_n_simulations(self, dm, weights, criteria_types):
        n = 100
        result = monte_carlo_simulation(dm, weights, criteria_types, n_simulations=n)
        assert len(result) == n

    def test_progress_callback(self, dm, weights, criteria_types):
        calls = []
        result = monte_carlo_simulation(
            dm, weights, criteria_types,
            n_simulations=50,
            progress_callback=lambda p: calls.append(p),
        )
        assert len(calls) > 0
        assert calls[-1] == 1.0


class TestMonteCarloSummary:
    def test_summary_columns(self, dm, weights, criteria_types):
        mc = monte_carlo_simulation(dm, weights, criteria_types, n_simulations=50)
        summary = monte_carlo_summary(mc)
        assert isinstance(summary, pd.DataFrame)
        assert "mean_score" in summary.columns
        assert "std_score" in summary.columns

    def test_summary_rows(self, dm, weights, criteria_types):
        mc = monte_carlo_simulation(dm, weights, criteria_types, n_simulations=50)
        summary = monte_carlo_summary(mc)
        assert len(summary) == len(dm)
