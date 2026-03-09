"""Pure match outcome probability engine."""

import math
from typing import Any

import config

from football_elo_odds.domain.models import MatchInputs, MatchOutcomeProbabilities


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str) and "%" in value:
            return float(value.replace("%", "")) / 100.0
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default


def _modified_bessel_i0(x: float) -> float:
    if hasattr(math, "i0"):
        return math.i0(x)

    ax = abs(x)
    if ax == 0.0:
        return 1.0

    if ax < 3.75:
        y = (x / 3.75) ** 2
        return 1.0 + y * (
            3.5156229
            + y
            * (
                3.0899424
                + y * (1.2067492 + y * (0.2659732 + y * (0.0360768 + y * 0.0045813)))
            )
        )

    y = 3.75 / ax
    return (math.exp(ax) / math.sqrt(ax)) * (
        0.39894228
        + y
        * (
            0.01328592
            + y
            * (
                0.00225319
                + y
                * (
                    -0.00157565
                    + y
                    * (
                        0.00916281
                        + y
                        * (
                            -0.02057706
                            + y * (0.02635537 + y * (-0.01647633 + y * 0.00392377))
                        )
                    )
                )
            )
        )
    )


def calculate_match_outcome_probabilities(inputs: MatchInputs) -> MatchOutcomeProbabilities:
    """Calculate 1X2 probabilities via Bradley-Terry-Davidson anchored to league scoring."""
    rating_diff = _safe_float(inputs.home_rating, 0) - _safe_float(inputs.away_rating, 0)
    strength_ratio = 10 ** (rating_diff / 400)

    mu = max(_safe_float(inputs.average_goals, config.DEFAULT_AVG_GOALS), 0)
    rating_gap = abs(rating_diff)
    gap_ratio = rating_gap / config.ELO_GOAL_SCALE_DIVISOR if config.ELO_GOAL_SCALE_DIVISOR else 0
    goal_scale = 1 + min(gap_ratio * config.ELO_GOAL_SCALE_FACTOR, config.ELO_GOAL_SCALE_CAP)
    mu_adjusted = mu * goal_scale
    poisson_draw = math.exp(-mu_adjusted) * _modified_bessel_i0(mu_adjusted)

    observed_draw = min(max(_safe_float(inputs.base_draw_probability, config.DEFAULT_DRAW_RATE), 0.0), 0.95)
    blended_draw = inputs.draw_weight * observed_draw + (1 - inputs.draw_weight) * poisson_draw
    blended_draw = min(max(blended_draw, 1e-6), 0.999999)

    nu = blended_draw / (1 - blended_draw)
    nu = max(nu * max(config.DRAW_RATE_SCALE, 1e-6), 0.0)

    denominator = strength_ratio + 1 + (2 * nu)
    if denominator == 0:
        return MatchOutcomeProbabilities(home=0.0, draw=0.0, away=1.0)

    p_home = strength_ratio / denominator
    p_draw = (2 * nu) / denominator
    p_away = 1 / denominator

    total = p_home + p_draw + p_away
    if total == 0:
        return MatchOutcomeProbabilities(home=0.0, draw=0.0, away=1.0)

    return MatchOutcomeProbabilities(home=p_home / total, draw=p_draw / total, away=p_away / total)
