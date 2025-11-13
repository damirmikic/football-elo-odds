"""Utilities for generating Poisson-based odds from DNB prices."""
from __future__ import annotations

import math
from typing import Dict, List, Tuple


def _poisson_pmf(k: int, lam: float) -> float:
    if lam < 0:
        return 0.0
    try:
        return math.exp(-lam) * (lam ** k) / math.factorial(k)
    except OverflowError:
        return 0.0


def _build_poisson_distribution(lam: float, max_goals: int) -> List[float]:
    """Return a truncated Poisson distribution that sums to one."""
    lam = max(lam, 0.0)
    max_goals = max(int(max_goals), 1)

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
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0

    for i, p_i in enumerate(home_dist):
        for j, p_j in enumerate(away_dist):
            prob = p_i * p_j
            if i > j:
                p_home += prob
            elif i == j:
                p_draw += prob
            else:
                p_away += prob

    total = p_home + p_draw + p_away
    if total > 0:
        return p_home / total, p_draw / total, p_away / total

    return 0.0, 1.0, 0.0


def _conditional_home_win_probability(
    s: float, lambda_total: float, max_goals: int
) -> Tuple[float, List[float], List[float]]:
    xg_home = lambda_total * s
    xg_away = lambda_total * (1.0 - s)

    home_dist = _build_poisson_distribution(xg_home, max_goals)
    away_dist = _build_poisson_distribution(xg_away, max_goals)

    p_home, _, p_away = _match_probabilities(home_dist, away_dist)
    denom = p_home + p_away
    if denom <= 0:
        return 0.5, home_dist, away_dist

    return p_home / denom, home_dist, away_dist


def _solve_strength_split(pi_home: float, lambda_total: float, max_goals: int) -> Tuple[float, List[float], List[float]]:
    if lambda_total <= 0 or not 0 < pi_home < 1:
        s = 0.5
        _, home_dist, away_dist = _conditional_home_win_probability(s, lambda_total, max_goals)
        return s, home_dist, away_dist

    eps = 1e-6
    lower = eps
    upper = 1.0 - eps

    lower_cond, _, _ = _conditional_home_win_probability(lower, lambda_total, max_goals)
    upper_cond, _, _ = _conditional_home_win_probability(upper, lambda_total, max_goals)

    if pi_home <= lower_cond:
        _, home_dist, away_dist = _conditional_home_win_probability(lower, lambda_total, max_goals)
        return lower, home_dist, away_dist

    if pi_home >= upper_cond:
        _, home_dist, away_dist = _conditional_home_win_probability(upper, lambda_total, max_goals)
        return upper, home_dist, away_dist

    for _ in range(60):
        mid = 0.5 * (lower + upper)
        cond_mid, _, _ = _conditional_home_win_probability(mid, lambda_total, max_goals)

        if abs(cond_mid - pi_home) < 1e-6:
            _, home_dist, away_dist = _conditional_home_win_probability(mid, lambda_total, max_goals)
            return mid, home_dist, away_dist

        if cond_mid > pi_home:
            upper = mid
        else:
            lower = mid

    s = 0.5 * (lower + upper)
    _, home_dist, away_dist = _conditional_home_win_probability(s, lambda_total, max_goals)
    return s, home_dist, away_dist


def _total_goals_distribution(goal_matrix: Dict[Tuple[int, int], float]) -> Dict[int, float]:
    totals: Dict[int, float] = {}
    for (i, j), prob in goal_matrix.items():
        totals[i + j] = totals.get(i + j, 0.0) + prob
    return totals


def calculate_poisson_markets_from_dnb(
    home_dnb_odds: float,
    away_dnb_odds: float,
    avg_league_goals: float,
    beta: float = 0.5,
    max_goals: int = 15,
) -> Dict[str, object]:
    """Generate Poisson-based odds that align with the supplied DNB prices."""

    home_dnb = float(home_dnb_odds) if home_dnb_odds else 0.0
    away_dnb = float(away_dnb_odds) if away_dnb_odds else 0.0

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
