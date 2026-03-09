"""Tests for newly extracted revamp domain + service layers."""

import math

import config
import pytest

from football_elo_odds.app.error_mapper import map_error_to_ui
from football_elo_odds.domain.models import MatchInputs, MatchOutcomeProbabilities
from football_elo_odds.errors import DataValidationError, ExternalServiceError
from football_elo_odds.services.match_analysis import MatchAnalysisService


def test_match_analysis_service_projects_normalized_probabilities():
    service = MatchAnalysisService()

    result = service.project_outcome_probabilities(
        home_rating=1650,
        away_rating=1550,
        base_draw_probability=0.26,
        average_goals=2.6,
        draw_weight=config.DRAW_OBS_WEIGHT,
    )

    assert isinstance(result, MatchOutcomeProbabilities)
    assert math.isclose(result.home + result.draw + result.away, 1.0, rel_tol=1e-9)
    assert result.home > result.away


def test_match_inputs_validate_bounds():
    with pytest.raises(DataValidationError):
        MatchInputs(
            home_rating=1500,
            away_rating=1500,
            base_draw_probability=1.1,
            average_goals=2.5,
            draw_weight=0.2,
        )


def test_error_mapper_returns_user_safe_payload():
    mapped = map_error_to_ui(ExternalServiceError("provider timeout"))

    assert mapped.level == "warning"
    assert "External data source unavailable" in mapped.title
