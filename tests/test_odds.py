"""Tests for odds calculation module."""

import pytest


class TestOddsCalculations:
    """Test suite for odds calculations."""

    def test_placeholder(self):
        """Placeholder test to verify pytest is working."""
        assert True

    def test_sample_fixture(self, sample_league_data):
        """Test that fixtures are properly loaded."""
        assert sample_league_data["league_name"] == "Test League"
        assert sample_league_data["home_advantage"] == 100
        assert sample_league_data["avg_goals"] == 2.5
