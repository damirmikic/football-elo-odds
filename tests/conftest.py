"""Pytest configuration and fixtures."""

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def sample_league_data():
    """Provide sample league data for testing."""
    return {
        "league_name": "Test League",
        "home_advantage": 100,
        "avg_goals": 2.5,
    }
