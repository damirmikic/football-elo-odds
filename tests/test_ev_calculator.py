"""Tests for EV calculator module."""

import pytest

from ev_calculator import (
    EVResult,
    MatchEVAnalysis,
    analyze_match_ev,
    calculate_bookmaker_margin,
    calculate_ev,
    calculate_roi,
    implied_probability,
    kelly_criterion,
    remove_bookmaker_margin,
)


class TestImpliedProbability:
    """Tests for implied probability calculation."""

    def test_even_odds(self):
        """Test conversion of even odds (2.00)."""
        assert implied_probability(2.00) == pytest.approx(0.5)

    def test_short_odds(self):
        """Test conversion of short odds (1.50)."""
        assert implied_probability(1.50) == pytest.approx(0.6667, rel=1e-3)

    def test_long_odds(self):
        """Test conversion of long odds (5.00)."""
        assert implied_probability(5.00) == pytest.approx(0.2)

    def test_zero_odds(self):
        """Test handling of invalid zero odds."""
        assert implied_probability(0.0) == 0.0

    def test_negative_odds(self):
        """Test handling of invalid negative odds."""
        assert implied_probability(-1.0) == 0.0


class TestCalculateEV:
    """Tests for expected value calculation."""

    def test_positive_ev(self):
        """Test calculation of positive EV."""
        # You think 60% chance, bookmaker offers 2.00 (50% implied)
        ev = calculate_ev(0.60, 2.00)
        assert ev == pytest.approx(0.20)  # 20% edge

    def test_zero_ev(self):
        """Test calculation of zero EV (fair odds)."""
        # You think 50%, bookmaker offers 2.00 (50% implied)
        ev = calculate_ev(0.50, 2.00)
        assert ev == pytest.approx(0.0)

    def test_negative_ev(self):
        """Test calculation of negative EV."""
        # You think 40%, bookmaker offers 2.00 (50% implied)
        ev = calculate_ev(0.40, 2.00)
        assert ev == pytest.approx(-0.20)

    def test_invalid_probability(self):
        """Test handling of invalid probability."""
        assert calculate_ev(-0.1, 2.00) == float('-inf')
        assert calculate_ev(1.5, 2.00) == float('-inf')

    def test_invalid_odds(self):
        """Test handling of invalid odds."""
        assert calculate_ev(0.5, 0.0) == float('-inf')
        assert calculate_ev(0.5, -1.0) == float('-inf')


class TestCalculateROI:
    """Tests for ROI calculation."""

    def test_positive_roi(self):
        """Test positive ROI calculation."""
        assert calculate_roi(0.20) == 20.0

    def test_negative_roi(self):
        """Test negative ROI calculation."""
        assert calculate_roi(-0.15) == -15.0

    def test_zero_roi(self):
        """Test zero ROI calculation."""
        assert calculate_roi(0.0) == 0.0


class TestRemoveBookmakerMargin:
    """Tests for margin removal."""

    def test_remove_margin(self):
        """Test removing typical bookmaker margin."""
        # Bookmaker odds with ~5% margin
        odds = {'home': 2.00, 'draw': 3.50, 'away': 4.00}

        # Implied probabilities: 0.5 + 0.286 + 0.25 = 1.036 (3.6% margin)
        fair_odds = remove_bookmaker_margin(odds)

        # Fair odds should have exactly 100% total probability
        total_prob = sum(1 / fair_odds[o] for o in ['home', 'draw', 'away'])
        assert total_prob == pytest.approx(1.0)

        # Fair odds should be higher than bookmaker odds
        assert fair_odds['home'] > odds['home']
        assert fair_odds['draw'] > odds['draw']
        assert fair_odds['away'] > odds['away']

    def test_zero_margin(self):
        """Test handling of already fair odds (no margin)."""
        # Theoretical fair odds (sum to 100%)
        odds = {'home': 2.00, 'draw': 4.00, 'away': 4.00}
        fair_odds = remove_bookmaker_margin(odds)

        # Should remain approximately the same
        assert fair_odds['home'] == pytest.approx(2.00, rel=1e-2)
        assert fair_odds['draw'] == pytest.approx(4.00, rel=1e-2)
        assert fair_odds['away'] == pytest.approx(4.00, rel=1e-2)


class TestCalculateBookmakerMargin:
    """Tests for bookmaker margin calculation."""

    def test_typical_margin(self):
        """Test calculation of typical ~5% margin."""
        odds = {'home': 2.00, 'draw': 3.50, 'away': 4.00}
        # Implied: 0.5 + 0.286 + 0.25 = 1.036
        margin = calculate_bookmaker_margin(odds)
        assert margin == pytest.approx(3.6, rel=1e-2)

    def test_high_margin(self):
        """Test calculation of high margin."""
        odds = {'home': 1.80, 'draw': 3.00, 'away': 3.50}
        # Higher margin due to lower odds
        margin = calculate_bookmaker_margin(odds)
        assert margin > 5.0

    def test_zero_margin(self):
        """Test fair odds (zero margin)."""
        odds = {'home': 2.00, 'draw': 4.00, 'away': 4.00}
        margin = calculate_bookmaker_margin(odds)
        assert margin == pytest.approx(0.0, abs=1e-10)


class TestEVResult:
    """Tests for EVResult dataclass."""

    def test_has_value_positive(self):
        """Test positive EV detection."""
        result = EVResult(
            outcome='home',
            true_probability=0.55,
            bookmaker_odds=2.00,
            implied_probability=0.50,
            expected_value=0.10,
            roi_percentage=10.0
        )
        assert result.has_value is True

    def test_has_value_negative(self):
        """Test negative EV detection."""
        result = EVResult(
            outcome='home',
            true_probability=0.45,
            bookmaker_odds=2.00,
            implied_probability=0.50,
            expected_value=-0.10,
            roi_percentage=-10.0
        )
        assert result.has_value is False

    def test_ev_percentage_str(self):
        """Test EV percentage formatting."""
        result = EVResult(
            outcome='home',
            true_probability=0.55,
            bookmaker_odds=2.00,
            implied_probability=0.50,
            expected_value=0.155,
            roi_percentage=15.5
        )
        assert result.ev_percentage_str == "+15.50%"

    def test_probability_edge(self):
        """Test probability edge calculation."""
        result = EVResult(
            outcome='home',
            true_probability=0.55,
            bookmaker_odds=2.00,
            implied_probability=0.50,
            expected_value=0.10,
            roi_percentage=10.0
        )
        assert result.probability_edge == pytest.approx(0.05)


class TestAnalyzeMatchEV:
    """Tests for complete match EV analysis."""

    def test_analyze_match_with_value(self):
        """Test analysis of match with positive EV."""
        elo_probs = {'home': 0.55, 'draw': 0.25, 'away': 0.20}
        bookmaker_odds = {'home': 2.10, 'draw': 3.40, 'away': 3.50}

        analysis = analyze_match_ev(elo_probs, bookmaker_odds)

        assert isinstance(analysis, MatchEVAnalysis)
        assert analysis.has_any_value is True
        assert analysis.best_value is not None
        assert analysis.best_value.outcome == 'home'  # Home has best value

    def test_analyze_match_no_value(self):
        """Test analysis of match with no positive EV."""
        elo_probs = {'home': 0.35, 'draw': 0.30, 'away': 0.35}
        # Lower odds = higher implied prob = negative EV
        bookmaker_odds = {'home': 2.50, 'draw': 3.00, 'away': 2.50}

        analysis = analyze_match_ev(elo_probs, bookmaker_odds)

        assert isinstance(analysis, MatchEVAnalysis)
        # All outcomes should have negative EV
        assert analysis.has_any_value is False
        assert analysis.best_value is None

    def test_bookmaker_margin_calculation(self):
        """Test bookmaker margin is calculated correctly."""
        elo_probs = {'home': 0.50, 'draw': 0.25, 'away': 0.25}
        bookmaker_odds = {'home': 2.00, 'draw': 3.50, 'away': 4.00}

        analysis = analyze_match_ev(elo_probs, bookmaker_odds)

        # Margin should be positive (bookmaker advantage)
        assert analysis.bookmaker_margin > 0


class TestKellyCriterion:
    """Tests for Kelly Criterion staking."""

    def test_kelly_positive_ev(self):
        """Test Kelly calculation for positive EV bet."""
        # 55% chance at 2.00 odds
        kelly = kelly_criterion(0.55, 2.00, fraction=1.0)
        assert kelly > 0
        assert kelly < 1  # Should never bet more than bankroll

    def test_kelly_negative_ev(self):
        """Test Kelly returns zero for negative EV."""
        # 45% chance at 2.00 odds (negative EV)
        kelly = kelly_criterion(0.45, 2.00, fraction=1.0)
        assert kelly == 0.0

    def test_kelly_fractional(self):
        """Test fractional Kelly is less than full Kelly."""
        full_kelly = kelly_criterion(0.55, 2.00, fraction=1.0)
        half_kelly = kelly_criterion(0.55, 2.00, fraction=0.5)
        quarter_kelly = kelly_criterion(0.55, 2.00, fraction=0.25)

        assert quarter_kelly < half_kelly < full_kelly
        assert quarter_kelly == pytest.approx(full_kelly * 0.25)
        assert half_kelly == pytest.approx(full_kelly * 0.5)

    def test_kelly_invalid_inputs(self):
        """Test Kelly handles invalid inputs."""
        assert kelly_criterion(0.0, 2.00) == 0.0
        assert kelly_criterion(1.0, 2.00) == 0.0
        assert kelly_criterion(0.5, 1.0) == 0.0
        assert kelly_criterion(0.5, 0.5) == 0.0


class TestMatchEVAnalysis:
    """Tests for MatchEVAnalysis dataclass."""

    def test_best_value_summary_with_value(self):
        """Test summary string for match with value."""
        elo_probs = {'home': 0.55, 'draw': 0.25, 'away': 0.20}
        bookmaker_odds = {'home': 2.10, 'draw': 3.40, 'away': 3.50}

        analysis = analyze_match_ev(elo_probs, bookmaker_odds)

        summary = analysis.best_value_summary
        assert 'HOME' in summary or 'DRAW' in summary or 'AWAY' in summary
        assert '@' in summary
        assert 'EV:' in summary

    def test_best_value_summary_no_value(self):
        """Test summary string for match without value."""
        elo_probs = {'home': 0.35, 'draw': 0.30, 'away': 0.35}
        # Lower odds = higher implied prob = negative EV
        bookmaker_odds = {'home': 2.50, 'draw': 3.00, 'away': 2.50}

        analysis = analyze_match_ev(elo_probs, bookmaker_odds)

        summary = analysis.best_value_summary
        assert summary == "No value found"
