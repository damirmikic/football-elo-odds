"""Comprehensive tests for odds calculation module."""

import math
from typing import Dict, Tuple

import pytest

from odds import (
    _build_poisson_distribution,
    _conditional_home_win_probability,
    _match_probabilities,
    _poisson_pmf,
    _solve_strength_split,
    _total_goals_distribution,
    calculate_poisson_markets_from_dnb,
)


class TestPoissonPMF:
    """Test suite for Poisson PMF calculations."""

    def test_poisson_pmf_normal_case(self):
        """Test Poisson PMF with normal inputs."""
        # P(X=2) when lambda=3
        result = _poisson_pmf(2, 3.0)
        expected = math.exp(-3) * (3**2) / math.factorial(2)
        assert abs(result - expected) < 1e-10

    def test_poisson_pmf_zero_lambda(self):
        """Test Poisson PMF with lambda=0."""
        # When lambda=0, P(X=0)=1 and P(X>0)=0
        assert abs(_poisson_pmf(0, 0.0) - 1.0) < 1e-10
        assert abs(_poisson_pmf(1, 0.0) - 0.0) < 1e-10
        assert abs(_poisson_pmf(5, 0.0) - 0.0) < 1e-10

    def test_poisson_pmf_negative_lambda(self):
        """Test Poisson PMF with negative lambda returns 0."""
        assert _poisson_pmf(2, -1.0) == 0.0
        assert _poisson_pmf(0, -5.0) == 0.0

    def test_poisson_pmf_large_values(self):
        """Test Poisson PMF handles large values gracefully."""
        # Should handle overflow gracefully
        result = _poisson_pmf(100, 200.0)
        assert result >= 0.0
        assert not math.isinf(result)

    def test_poisson_pmf_overflow_protection(self):
        """Test Poisson PMF returns 0 on overflow."""
        # Very large k and lambda should trigger overflow protection
        result = _poisson_pmf(1000, 10.0)
        assert result == 0.0


class TestBuildPoissonDistribution:
    """Test suite for building Poisson distributions."""

    def test_distribution_sums_to_one(self):
        """Test that distribution probabilities sum to 1."""
        dist = _build_poisson_distribution(2.5, 10)
        assert abs(sum(dist) - 1.0) < 1e-10

    def test_distribution_length(self):
        """Test distribution has correct length."""
        max_goals = 15
        dist = _build_poisson_distribution(2.5, max_goals)
        assert len(dist) == max_goals + 1  # Includes 0 to max_goals

    def test_distribution_all_positive(self):
        """Test all probabilities are non-negative."""
        dist = _build_poisson_distribution(3.0, 10)
        assert all(p >= 0 for p in dist)

    def test_distribution_zero_lambda(self):
        """Test distribution with lambda=0."""
        dist = _build_poisson_distribution(0.0, 5)
        assert abs(dist[0] - 1.0) < 1e-10  # P(0) = 1
        assert sum(dist) == pytest.approx(1.0)

    def test_distribution_negative_lambda(self):
        """Test distribution handles negative lambda gracefully."""
        dist = _build_poisson_distribution(-1.0, 5)
        # Should treat as lambda=0
        assert abs(dist[0] - 1.0) < 1e-10
        assert sum(dist) == pytest.approx(1.0)

    def test_distribution_small_max_goals(self):
        """Test distribution with very small max_goals."""
        dist = _build_poisson_distribution(2.5, 1)
        assert len(dist) == 2
        assert sum(dist) == pytest.approx(1.0)

    def test_distribution_tail_probability(self):
        """Test that tail probability is captured correctly."""
        dist = _build_poisson_distribution(2.5, 3)
        # Sum of explicit probabilities plus tail should equal 1
        assert sum(dist) == pytest.approx(1.0)
        # Tail probability (last element) should be positive
        assert dist[-1] > 0


class TestMatchProbabilities:
    """Test suite for match probability calculations."""

    def test_equal_distributions(self):
        """Test probabilities when teams are equally matched."""
        # Equal distributions should give p_home ≈ p_away
        dist = _build_poisson_distribution(1.5, 10)
        p_home, p_draw, p_away = _match_probabilities(dist, dist)

        assert abs(p_home - p_away) < 1e-10
        assert p_draw > 0
        assert abs(p_home + p_draw + p_away - 1.0) < 1e-10

    def test_probabilities_sum_to_one(self):
        """Test that probabilities sum to 1."""
        home_dist = _build_poisson_distribution(2.0, 10)
        away_dist = _build_poisson_distribution(1.5, 10)
        p_home, p_draw, p_away = _match_probabilities(home_dist, away_dist)

        assert abs(p_home + p_draw + p_away - 1.0) < 1e-10

    def test_stronger_home_team(self):
        """Test probabilities favor stronger home team."""
        home_dist = _build_poisson_distribution(2.5, 10)
        away_dist = _build_poisson_distribution(1.0, 10)
        p_home, p_draw, p_away = _match_probabilities(home_dist, away_dist)

        assert p_home > p_away
        assert p_home > p_draw

    def test_all_probabilities_positive(self):
        """Test all probabilities are non-negative."""
        home_dist = _build_poisson_distribution(2.0, 10)
        away_dist = _build_poisson_distribution(1.8, 10)
        p_home, p_draw, p_away = _match_probabilities(home_dist, away_dist)

        assert p_home >= 0
        assert p_draw >= 0
        assert p_away >= 0

    def test_empty_distributions(self):
        """Test handling of edge case with minimal distributions."""
        home_dist = [1.0]
        away_dist = [1.0]
        p_home, p_draw, p_away = _match_probabilities(home_dist, away_dist)

        # Both score 0, so it's a draw
        assert abs(p_draw - 1.0) < 1e-10
        assert p_home == 0.0
        assert p_away == 0.0


class TestConditionalHomeProbability:
    """Test suite for conditional home win probability."""

    def test_equal_strength_split(self):
        """Test s=0.5 gives roughly equal probabilities."""
        prob, home_dist, away_dist = _conditional_home_win_probability(0.5, 3.0, 10)
        # With equal strengths, conditional probability should be around 0.5
        assert 0.4 < prob < 0.6

    def test_strong_home_advantage(self):
        """Test high s value favors home team."""
        prob_high, _, _ = _conditional_home_win_probability(0.8, 3.0, 10)
        prob_low, _, _ = _conditional_home_win_probability(0.2, 3.0, 10)

        assert prob_high > prob_low
        assert prob_high > 0.5

    def test_returns_distributions(self):
        """Test that distributions are returned correctly."""
        prob, home_dist, away_dist = _conditional_home_win_probability(0.6, 2.5, 10)

        assert len(home_dist) == 11
        assert len(away_dist) == 11
        assert sum(home_dist) == pytest.approx(1.0)
        assert sum(away_dist) == pytest.approx(1.0)

    def test_zero_lambda(self):
        """Test handling of zero lambda."""
        prob, home_dist, away_dist = _conditional_home_win_probability(0.5, 0.0, 10)
        # Should return 0.5 as default
        assert prob == 0.5

    def test_extreme_strength_split(self):
        """Test extreme values of strength split."""
        prob_min, _, _ = _conditional_home_win_probability(0.01, 3.0, 10)
        prob_max, _, _ = _conditional_home_win_probability(0.99, 3.0, 10)

        assert prob_min < 0.5
        assert prob_max > 0.5


class TestSolveStrengthSplit:
    """Test suite for solving strength split."""

    def test_symmetric_case(self):
        """Test that pi_home=0.5 returns s≈0.5."""
        s, home_dist, away_dist = _solve_strength_split(0.5, 3.0, 10)
        # Should be close to 0.5 for symmetric case
        assert 0.4 < s < 0.6

    def test_returns_distributions(self):
        """Test that distributions are returned."""
        s, home_dist, away_dist = _solve_strength_split(0.6, 2.5, 10)

        assert len(home_dist) > 0
        assert len(away_dist) > 0
        assert sum(home_dist) == pytest.approx(1.0)
        assert sum(away_dist) == pytest.approx(1.0)

    def test_higher_target_gives_higher_split(self):
        """Test that higher pi_home gives higher s."""
        s_low, _, _ = _solve_strength_split(0.3, 2.5, 10)
        s_high, _, _ = _solve_strength_split(0.7, 2.5, 10)

        assert s_high > s_low

    def test_boundary_pi_values(self):
        """Test extreme values of pi_home."""
        s_min, _, _ = _solve_strength_split(0.01, 2.5, 10)
        s_max, _, _ = _solve_strength_split(0.99, 2.5, 10)

        assert 0 < s_min < 1
        assert 0 < s_max < 1
        assert s_max > s_min

    def test_invalid_pi_home(self):
        """Test handling of invalid pi_home values."""
        # pi_home = 0 (invalid)
        s, home_dist, away_dist = _solve_strength_split(0.0, 2.5, 10)
        assert s == pytest.approx(0.5)

        # pi_home = 1 (invalid)
        s, home_dist, away_dist = _solve_strength_split(1.0, 2.5, 10)
        assert s == pytest.approx(0.5)

    def test_zero_lambda(self):
        """Test handling of zero lambda."""
        s, home_dist, away_dist = _solve_strength_split(0.6, 0.0, 10)
        assert s == pytest.approx(0.5)

    def test_negative_lambda(self):
        """Test handling of negative lambda."""
        s, home_dist, away_dist = _solve_strength_split(0.6, -1.0, 10)
        assert s == pytest.approx(0.5)


class TestTotalGoalsDistribution:
    """Test suite for total goals distribution."""

    def test_simple_case(self):
        """Test with a simple goal matrix."""
        goal_matrix = {
            (0, 0): 0.2,
            (1, 0): 0.3,
            (0, 1): 0.3,
            (1, 1): 0.2,
        }
        totals = _total_goals_distribution(goal_matrix)

        assert totals[0] == pytest.approx(0.2)  # 0+0
        assert totals[1] == pytest.approx(0.6)  # 1+0 and 0+1
        assert totals[2] == pytest.approx(0.2)  # 1+1

    def test_probabilities_sum_correctly(self):
        """Test that total probabilities sum correctly."""
        goal_matrix = {
            (0, 0): 0.1,
            (1, 0): 0.2,
            (2, 0): 0.15,
            (0, 1): 0.2,
            (1, 1): 0.25,
            (0, 2): 0.1,
        }
        totals = _total_goals_distribution(goal_matrix)

        assert sum(totals.values()) == pytest.approx(1.0)

    def test_empty_goal_matrix(self):
        """Test with empty goal matrix."""
        goal_matrix: Dict[Tuple[int, int], float] = {}
        totals = _total_goals_distribution(goal_matrix)

        assert len(totals) == 0

    def test_high_scoring_game(self):
        """Test with high-scoring scenarios."""
        goal_matrix = {
            (5, 3): 0.4,
            (4, 4): 0.3,
            (3, 5): 0.3,
        }
        totals = _total_goals_distribution(goal_matrix)

        # All three results sum to 8 goals (5+3, 4+4, 3+5)
        assert totals[8] == pytest.approx(1.0)  # 0.4 + 0.3 + 0.3


class TestCalculatePoissonMarketsFromDNB:
    """Test suite for the main odds calculation function."""

    def test_normal_case(self):
        """Test calculation with normal DNB odds."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.8,
            away_dnb_odds=2.2,
            avg_league_goals=2.6,
        )

        assert "lambda_total" in result
        assert "xg_home" in result
        assert "xg_away" in result
        assert "probabilities" in result
        assert "odds" in result
        assert "over_under" in result
        assert "btts" in result

    def test_probabilities_valid(self):
        """Test that probabilities are valid (0-1 range and sum to 1)."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=2.5,
        )

        probs = result["probabilities"]
        assert 0 <= probs["home"] <= 1
        assert 0 <= probs["draw"] <= 1
        assert 0 <= probs["away"] <= 1
        assert abs(probs["home"] + probs["draw"] + probs["away"] - 1.0) < 1e-6

    def test_odds_positive(self):
        """Test that all odds are positive."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.5,
            away_dnb_odds=3.0,
            avg_league_goals=2.8,
        )

        odds = result["odds"]
        assert odds["home"] > 0
        assert odds["draw"] > 0
        assert odds["away"] > 0

    def test_home_favorite_scenario(self):
        """Test odds when home team is favorite."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.3,  # Strong favorite
            away_dnb_odds=4.0,  # Underdog
            avg_league_goals=2.5,
        )

        probs = result["probabilities"]
        assert probs["home"] > probs["away"]
        assert probs["home"] > probs["draw"]

    def test_away_favorite_scenario(self):
        """Test odds when away team is favorite."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=3.5,  # Underdog
            away_dnb_odds=1.4,  # Strong favorite
            avg_league_goals=2.5,
        )

        probs = result["probabilities"]
        assert probs["away"] > probs["home"]

    def test_equal_teams(self):
        """Test odds when teams are equally matched."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=2.5,
        )

        probs = result["probabilities"]
        # Home and away should be similar
        assert abs(probs["home"] - probs["away"]) < 0.05

    def test_over_under_probabilities(self):
        """Test over/under probabilities sum to 1."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=2.5,
        )

        ou = result["over_under"]
        assert abs(ou["over25_prob"] + ou["under25_prob"] - 1.0) < 1e-6
        assert 0 <= ou["over25_prob"] <= 1
        assert 0 <= ou["under25_prob"] <= 1

    def test_btts_probabilities(self):
        """Test BTTS probabilities sum to 1."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=2.5,
        )

        btts = result["btts"]
        assert abs(btts["yes_prob"] + btts["no_prob"] - 1.0) < 1e-6
        assert 0 <= btts["yes_prob"] <= 1
        assert 0 <= btts["no_prob"] <= 1

    def test_expected_goals_positive(self):
        """Test that expected goals are positive."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.8,
            away_dnb_odds=2.2,
            avg_league_goals=2.6,
        )

        assert result["xg_home"] >= 0
        assert result["xg_away"] >= 0
        assert result["lambda_total"] >= 0

    def test_zero_odds_handling(self):
        """Test handling of zero or invalid odds."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=0.0,
            away_dnb_odds=0.0,
            avg_league_goals=2.5,
        )

        # Should default to equal probabilities
        probs = result["probabilities"]
        assert abs(probs["home"] + probs["draw"] + probs["away"] - 1.0) < 1e-6

    def test_negative_odds_handling(self):
        """Test handling of negative odds."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=-1.0,
            away_dnb_odds=-2.0,
            avg_league_goals=2.5,
        )

        # Should still produce valid output
        probs = result["probabilities"]
        assert abs(probs["home"] + probs["draw"] + probs["away"] - 1.0) < 1e-6

    def test_custom_beta_parameter(self):
        """Test custom beta parameter affects results."""
        result1 = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.5,
            away_dnb_odds=3.0,
            avg_league_goals=2.5,
            beta=0.0,
        )

        result2 = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.5,
            away_dnb_odds=3.0,
            avg_league_goals=2.5,
            beta=1.0,
        )

        # Different beta should affect lambda_total
        assert result1["lambda_total"] != result2["lambda_total"]

    def test_custom_max_goals(self):
        """Test custom max_goals parameter."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=2.5,
            max_goals=20,
        )

        # Should still produce valid results
        assert len(result["home_distribution"]) == 21
        assert len(result["away_distribution"]) == 21

    def test_distributions_returned(self):
        """Test that goal distributions are included in result."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.8,
            away_dnb_odds=2.2,
            avg_league_goals=2.6,
        )

        assert "home_distribution" in result
        assert "away_distribution" in result
        assert len(result["home_distribution"]) > 0
        assert len(result["away_distribution"]) > 0

    def test_pi_home_consistency(self):
        """Test that pi_home_target and pi_home_model are reasonably close."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=1.8,
            away_dnb_odds=2.2,
            avg_league_goals=2.6,
        )

        assert "pi_home_target" in result
        assert "pi_home_model" in result
        # They should be relatively close (within 10%)
        assert abs(result["pi_home_target"] - result["pi_home_model"]) < 0.1

    def test_high_scoring_league(self):
        """Test with high average goals."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=4.0,
        )

        # Should favor over 2.5
        assert result["over_under"]["over25_prob"] > result["over_under"]["under25_prob"]

    def test_low_scoring_league(self):
        """Test with low average goals."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=1.5,
        )

        # Should favor under 2.5
        assert result["over_under"]["under25_prob"] > result["over_under"]["over25_prob"]

    def test_odds_reciprocal_relationship(self):
        """Test that odds are reciprocal of probabilities."""
        result = calculate_poisson_markets_from_dnb(
            home_dnb_odds=2.0,
            away_dnb_odds=2.0,
            avg_league_goals=2.5,
        )

        probs = result["probabilities"]
        odds = result["odds"]

        # Odds should be approximately 1/probability
        assert abs(odds["home"] - 1/probs["home"]) < 1e-6
        assert abs(odds["draw"] - 1/probs["draw"]) < 1e-6
        assert abs(odds["away"] - 1/probs["away"]) < 1e-6
