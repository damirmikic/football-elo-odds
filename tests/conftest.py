"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_league_data():
    """Provide sample league data for testing."""
    return {
        "league_name": "Test League",
        "home_advantage": 100,
        "avg_goals": 2.5,
    }
