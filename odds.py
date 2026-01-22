"""Utilities for generating Poisson-based odds from DNB prices."""
from __future__ import annotations

import logging
import math
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def _poisson_pmf(k: int, lam: float) -> float:
    """Calculate Poisson probability mass function.

    Args:
        k: Number of occurrences
        lam: Poisson parameter (lambda)

    Returns:
        Probability of k occurrences
    """
    if lam < 0:
        logger.debug(f"Negative lambda ({lam}) provided to Poisson PMF, returning 0")
        return 0.0
    try:
        return math.exp(-lam) * (lam ** k) / math.factorial(k)
    except OverflowError:
        logger.debug(f"Overflow in Poisson PMF calculation: k={k}, lam={lam}")
        return 0.0
    except (ValueError, TypeError) as e:
        logger.error(f"Error in Poisson PMF: k={k}, lam={lam}, error={e}")
        return 0.0


def _build_poisson_distribution(lam: float, max_goals: int) -> List[float]:
    """Return a truncated Poisson distribution that sums to one.

    Args:
        lam: Poisson parameter (lambda)
        max_goals: Maximum number of goals to consider

    Returns:
        List of probabilities for 0 to max_goals (inclusive)
    """
    try:
        lam = max(float(lam), 0.0)
        max_goals = max(int(max_goals), 1)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid inputs for Poisson distribution: lam={lam}, max_goals={max_goals}")
        raise TypeError(f"Invalid parameter types: {e}") from e

    probabilities = [_poisson_pmf(k, lam) for k in range(max_goals)]
    tail = 1.0 - sum(probabilities)
    probabilities.append(max(tail, 0.0))

    total = sum(probabilities)
    if total <= 0:
        probs = [0.0 for _ in range(max_goals + 1)]
        probs[0] = 1.0
        return probs

    return [max(p / total, 0.0) for p in probabilities]


def _match_probabilities(home_dist: List[float], away_dist: List[float]) -> Tuple[float, float, float]:
    """Calculate match outcome probabilities from goal distributions.

    Args:
        home_dist: Home team goal distribution
        away_dist: Away team goal distribution

    Returns:
        Tuple of (p_home, p_draw, p_away)
    """
    if not home_dist or not away_dist:
        logger.warning("Empty distribution provided to _match_probabilities")
        return 0.0, 1.0, 0.0

    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0

    try:
        for i, p_i in enumerate(home_dist):
            for j, p_j in enumerate(away_dist):
                prob = p_i * p_j
                if i > j:
                    p_home += prob
                elif i == j:
                    p_draw += prob
                else:
                    p_away += prob
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating match probabilities: {e}")
        return 0.0, 1.0, 0.0

    total = p_home + p_draw + p_away
    if total > 0:
        return p_home / total, p_draw / total, p_away / total

    logger.warning("Total probability is zero, returning default draw")
    return 0.0, 1.0, 0.0


def _conditional_home_win_probability(
    s: float, lambda_total: float, max_goals: int
) -> Tuple[float, List[float], List[float]]:
    """Calculate conditional home win probability given strength split.

    Args:
        s: Strength split parameter (0 to 1, home's share of total strength)
        lambda_total: Total expected goals
        max_goals: Maximum goals to consider

    Returns:
        Tuple of (conditional home win probability, home distribution, away distribution)
    """
    xg_home = lambda_total * s
    xg_away = lambda_total * (1.0 - s)

    home_dist = _build_poisson_distribution(xg_home, max_goals)
    away_dist = _build_poisson_distribution(xg_away, max_goals)

    p_home, _, p_away = _match_probabilities(home_dist, away_dist)
    denom = p_home + p_away
    if denom <= 0:
        logger.debug(f"Zero denominator in conditional probability, returning 0.5")
        return 0.5, home_dist, away_dist

    return p_home / denom, home_dist, away_dist


def _solve_strength_split(pi_home: float, lambda_total: float, max_goals: int) -> Tuple[float, List[float], List[float]]:
    """Solve for strength split using bisection method.

    Args:
        pi_home: Target home win probability (excluding draws)
        lambda_total: Total expected goals
        max_goals: Maximum goals to consider

    Returns:
        Tuple of (strength split, home distribution, away distribution)
    """
    if lambda_total <= 0 or not 0 < pi_home < 1:
        logger.debug(
            f"Invalid inputs for strength split: lambda_total={lambda_total}, "
            f"pi_home={pi_home}. Returning neutral split."
        )
        s = 0.5
        _, home_dist, away_dist = _conditional_home_win_probability(s, lambda_total, max_goals)
        return s, home_dist, away_dist

    eps = 1e-6
    lower = eps
    upper = 1.0 - eps

    try:
        lower_cond, _, _ = _conditional_home_win_probability(lower, lambda_total, max_goals)
        upper_cond, _, _ = _conditional_home_win_probability(upper, lambda_total, max_goals)
    except Exception as e:
        logger.error(f"Error computing boundary conditions: {e}")
        s = 0.5
        _, home_dist, away_dist = _conditional_home_win_probability(s, lambda_total, max_goals)
        return s, home_dist, away_dist

    if pi_home <= lower_cond:
        logger.debug(f"pi_home ({pi_home}) at or below lower bound ({lower_cond})")
        _, home_dist, away_dist = _conditional_home_win_probability(lower, lambda_total, max_goals)
        return lower, home_dist, away_dist

    if pi_home >= upper_cond:
        logger.debug(f"pi_home ({pi_home}) at or above upper bound ({upper_cond})")
        _, home_dist, away_dist = _conditional_home_win_probability(upper, lambda_total, max_goals)
        return upper, home_dist, away_dist

    max_iterations = 60
    for iteration in range(max_iterations):
        mid = 0.5 * (lower + upper)
        try:
            cond_mid, _, _ = _conditional_home_win_probability(mid, lambda_total, max_goals)
        except Exception as e:
            logger.warning(f"Error in bisection iteration {iteration}: {e}")
            break

        if abs(cond_mid - pi_home) < 1e-6:
            _, home_dist, away_dist = _conditional_home_win_probability(mid, lambda_total, max_goals)
            logger.debug(f"Converged in {iteration + 1} iterations")
            return mid, home_dist, away_dist

        if cond_mid > pi_home:
            upper = mid
        else:
            lower = mid

    s = 0.5 * (lower + upper)
    _, home_dist, away_dist = _conditional_home_win_probability(s, lambda_total, max_goals)
    logger.debug(f"Bisection completed with final split s={s:.6f}")
    return s, home_dist, away_dist


def _total_goals_distribution(goal_matrix: Dict[Tuple[int, int], float]) -> Dict[int, float]:
    """Calculate total goals distribution from goal matrix.

    Args:
        goal_matrix: Dictionary mapping (home_goals, away_goals) to probability

    Returns:
        Dictionary mapping total goals to probability
    """
    totals: Dict[int, float] = {}
    try:
        for (i, j), prob in goal_matrix.items():
            totals[i + j] = totals.get(i + j, 0.0) + prob
    except (TypeError, ValueError, KeyError) as e:
        logger.error(f"Error calculating total goals distribution: {e}")
        return {}
    return totals


def calculate_poisson_markets_from_dnb(
    home_dnb_odds: float,
    away_dnb_odds: float,
    avg_league_goals: float,
    beta: float = 0.5,
    max_goals: int = 15,
) -> Dict[str, object]:
    """Generate Poisson-based odds that align with the supplied DNB prices.

    Args:
        home_dnb_odds: Draw No Bet odds for home team (must be positive)
        away_dnb_odds: Draw No Bet odds for away team (must be positive)
        avg_league_goals: Average goals per match in the league (must be non-negative)
        beta: Weight for imbalance adjustment (default: 0.5, range: 0.0-1.0)
        max_goals: Maximum goals to consider in distribution (default: 15, minimum: 1)

    Returns:
        Dictionary containing calculated odds, probabilities, and distributions

    Raises:
        ValueError: If inputs are invalid (negative values, etc.)
        TypeError: If inputs cannot be converted to appropriate numeric types
    """
    try:
        home_dnb = float(home_dnb_odds) if home_dnb_odds else 0.0
        away_dnb = float(away_dnb_odds) if away_dnb_odds else 0.0
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid DNB odds: home={home_dnb_odds}, away={away_dnb_odds}")
        raise TypeError(f"DNB odds must be numeric: {e}") from e

    try:
        avg_goals = float(avg_league_goals)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid avg_league_goals: {avg_league_goals}")
        raise TypeError(f"Average league goals must be numeric: {e}") from e

    try:
        beta = float(beta)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid beta: {beta}")
        raise TypeError(f"Beta parameter must be numeric: {e}") from e

    try:
        max_goals = int(max_goals)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid max_goals: {max_goals}")
        raise TypeError(f"Max goals must be an integer: {e}") from e

    # Validate ranges
    if avg_goals < 0:
        logger.warning(f"Negative avg_league_goals ({avg_goals}) will be treated as 0")

    if max_goals < 1:
        logger.warning(f"max_goals ({max_goals}) too low, setting to 1")
        max_goals = 1

    if home_dnb <= 0 or away_dnb <= 0:
        pi_home = 0.5
        pi_away = 0.5
    else:
        p_home_raw = 1.0 / home_dnb
        p_away_raw = 1.0 / away_dnb
        normalizer = p_home_raw + p_away_raw
        if normalizer <= 0:
            pi_home = pi_away = 0.5
        else:
            pi_home = p_home_raw / normalizer
            pi_away = p_away_raw / normalizer

    avg_goals = max(float(avg_league_goals), 0.0)
    beta = float(beta)
    imbalance = abs(pi_home - 0.5)
    lambda_total = avg_goals * (1.0 + beta * imbalance)

    s, home_dist, away_dist = _solve_strength_split(pi_home, lambda_total, max_goals)
    xg_home = lambda_total * s
    xg_away = lambda_total * (1.0 - s)

    goal_matrix: Dict[Tuple[int, int], float] = {}
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0
    for i, p_i in enumerate(home_dist):
        for j, p_j in enumerate(away_dist):
            prob = p_i * p_j
            goal_matrix[(i, j)] = prob
            if i > j:
                p_home += prob
            elif i == j:
                p_draw += prob
            else:
                p_away += prob

    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total
        p_draw /= total
        p_away /= total
    else:
        p_home = p_away = 0.0
        p_draw = 1.0

    total_goals = _total_goals_distribution(goal_matrix)
    p_under25 = sum(prob for goals, prob in total_goals.items() if goals <= 2)
    p_under25 = min(max(p_under25, 0.0), 1.0)
    p_over25 = 1.0 - p_under25

    p_home_clean = home_dist[0] if home_dist else 0.0
    p_away_clean = away_dist[0] if away_dist else 0.0
    p_btts = 1.0 - (p_home_clean + p_away_clean - (p_home_clean * p_away_clean))
    p_btts = min(max(p_btts, 0.0), 1.0)
    p_no_btts = 1.0 - p_btts

    pi_model = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0.5

    def _probability_to_odds(prob: float) -> float:
        prob = min(max(prob, 0.0), 1.0)
        if prob <= 0:
            return float("inf")
        return 1.0 / prob

    return {
        "lambda_total": lambda_total,
        "xg_home": xg_home,
        "xg_away": xg_away,
        "probabilities": {
            "home": p_home,
            "draw": p_draw,
            "away": p_away,
        },
        "odds": {
            "home": _probability_to_odds(p_home),
            "draw": _probability_to_odds(p_draw),
            "away": _probability_to_odds(p_away),
        },
        "over_under": {
            "over25_prob": p_over25,
            "under25_prob": p_under25,
            "over25_odds": _probability_to_odds(p_over25),
            "under25_odds": _probability_to_odds(p_under25),
        },
        "btts": {
            "yes_prob": p_btts,
            "no_prob": p_no_btts,
            "yes_odds": _probability_to_odds(p_btts),
            "no_odds": _probability_to_odds(p_no_btts),
        },
        "home_distribution": home_dist,
        "away_distribution": away_dist,
        "pi_home_target": pi_home,
        "pi_home_model": pi_model,
    }
