"""Typed domain models for match outcome probability calculations."""

from dataclasses import dataclass

from football_elo_odds.errors import DataValidationError


@dataclass(frozen=True)
class MatchInputs:
    """Inputs required for match outcome probability projection."""

    home_rating: float
    away_rating: float
    base_draw_probability: float
    average_goals: float
    draw_weight: float

    def __post_init__(self) -> None:
        if self.average_goals < 0:
            raise DataValidationError("average_goals cannot be negative")
        if not 0.0 <= self.base_draw_probability <= 1.0:
            raise DataValidationError("base_draw_probability must be between 0 and 1")
        if not 0.0 <= self.draw_weight <= 1.0:
            raise DataValidationError("draw_weight must be between 0 and 1")


@dataclass(frozen=True)
class MatchOutcomeProbabilities:
    """Normalized home/draw/away probabilities for a match."""

    home: float
    draw: float
    away: float

    def __post_init__(self) -> None:
        values = (self.home, self.draw, self.away)
        if any(value < 0.0 or value > 1.0 for value in values):
            raise DataValidationError("all probabilities must be between 0 and 1")

        total = sum(values)
        if abs(total - 1.0) > 1e-6:
            raise DataValidationError("probabilities must sum to 1")
