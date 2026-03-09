"""Use-case service for match analysis workflows."""

import config

from football_elo_odds.domain.models import MatchInputs, MatchOutcomeProbabilities
from football_elo_odds.domain.odds_engine import calculate_match_outcome_probabilities


class MatchAnalysisService:
    """Orchestrates match outcome probability projection from typed inputs."""

    def project_outcome_probabilities(
        self,
        home_rating: float,
        away_rating: float,
        base_draw_probability: float,
        average_goals: float,
        draw_weight: float = config.DRAW_OBS_WEIGHT,
    ) -> MatchOutcomeProbabilities:
        inputs = MatchInputs(
            home_rating=home_rating,
            away_rating=away_rating,
            base_draw_probability=base_draw_probability,
            average_goals=average_goals,
            draw_weight=draw_weight,
        )
        return calculate_match_outcome_probabilities(inputs)
