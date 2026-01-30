"""Expected Value calculator for comparing Elo probabilities with bookmaker odds."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EVResult:
    """Expected Value calculation result for a single outcome."""

    outcome: str  # 'home', 'draw', or 'away'
    true_probability: float  # Elo model probability
    bookmaker_odds: float  # Decimal odds from bookmaker
    implied_probability: float  # Bookmaker's implied probability
    expected_value: float  # EV as decimal (0.15 = 15% edge)
    roi_percentage: float  # Expected ROI if bet placed

    @property
    def has_value(self) -> bool:
        """Check if this is a positive EV bet."""
        return self.expected_value > 0

    @property
    def ev_percentage_str(self) -> str:
        """Format EV as percentage string."""
        return f"{self.expected_value * 100:+.2f}%"

    @property
    def probability_edge(self) -> float:
        """Difference between true and implied probability."""
        return self.true_probability - self.implied_probability

    @property
    def edge_percentage_str(self) -> str:
        """Format probability edge as percentage string."""
        return f"{self.probability_edge * 100:+.2f}%"


@dataclass
class MatchEVAnalysis:
    """Complete EV analysis for a match."""

    home_ev: EVResult
    draw_ev: EVResult
    away_ev: EVResult
    bookmaker_margin: float  # Bookmaker's overround percentage
    best_value: Optional[EVResult] = None

    def __post_init__(self):
        """Calculate best value bet after initialization."""
        candidates = [self.home_ev, self.draw_ev, self.away_ev]
        value_bets = [ev for ev in candidates if ev.has_value]

        if value_bets:
            self.best_value = max(value_bets, key=lambda x: x.expected_value)

    @property
    def has_any_value(self) -> bool:
        """Check if any outcome has positive EV."""
        return self.best_value is not None

    @property
    def best_value_summary(self) -> str:
        """Get summary string for best value bet."""
        if not self.best_value:
            return "No value found"

        outcome_label = self.best_value.outcome.upper()
        odds = self.best_value.bookmaker_odds
        ev = self.best_value.ev_percentage_str

        return f"{outcome_label} @ {odds:.2f} (EV: {ev})"


def calculate_ev(
    true_probability: float, bookmaker_odds: float
) -> float:
    """
    Calculate expected value for a single outcome.

    Formula: EV = (True_Probability × Bookmaker_Odds) - 1

    Args:
        true_probability: Your model's probability (0-1)
        bookmaker_odds: Bookmaker's decimal odds

    Returns:
        Expected value as decimal (0.15 = 15% edge, -0.05 = -5% edge)

    Example:
        >>> calculate_ev(0.60, 2.00)  # You think 60%, bookie implies 50%
        0.20  # 20% positive EV
    """
    if bookmaker_odds <= 0 or true_probability < 0 or true_probability > 1:
        return float("-inf")

    return (true_probability * bookmaker_odds) - 1


def calculate_roi(ev: float) -> float:
    """
    Calculate expected ROI percentage from EV.

    Args:
        ev: Expected value as decimal

    Returns:
        ROI percentage (0.20 = 20% ROI)
    """
    return ev * 100


def implied_probability(decimal_odds: float) -> float:
    """
    Convert decimal odds to implied probability.

    Args:
        decimal_odds: Decimal odds (e.g., 2.00)

    Returns:
        Implied probability (0-1)
    """
    if decimal_odds <= 0:
        return 0.0
    return 1 / decimal_odds


def remove_bookmaker_margin(odds: Dict[str, float]) -> Dict[str, float]:
    """
    Remove bookmaker's margin to get fair odds.

    Uses proportional method: normalize implied probabilities to sum to 100%.

    Args:
        odds: Dict with 'home', 'draw', 'away' decimal odds

    Returns:
        Fair odds with margin removed
    """
    # Calculate implied probabilities
    implied_probs = {
        outcome: implied_probability(odds[outcome])
        for outcome in ["home", "draw", "away"]
    }

    # Total probability (should be >1 due to margin)
    total_prob = sum(implied_probs.values())

    if total_prob <= 0:
        return odds

    # Normalize to 100%
    fair_probs = {
        outcome: prob / total_prob for outcome, prob in implied_probs.items()
    }

    # Convert back to odds
    fair_odds = {
        outcome: 1 / prob if prob > 0 else float("inf")
        for outcome, prob in fair_probs.items()
    }

    return fair_odds


def analyze_match_ev(
    elo_probabilities: Dict[str, float], bookmaker_odds: Dict[str, float]
) -> MatchEVAnalysis:
    """
    Perform complete EV analysis for a match.

    Args:
        elo_probabilities: Dict with 'home', 'draw', 'away' probabilities (0-1)
        bookmaker_odds: Dict with 'home', 'draw', 'away' decimal odds

    Returns:
        MatchEVAnalysis object with complete analysis

    Example:
        >>> elo_probs = {'home': 0.55, 'draw': 0.25, 'away': 0.20}
        >>> bookie_odds = {'home': 2.10, 'draw': 3.40, 'away': 3.50}
        >>> analysis = analyze_match_ev(elo_probs, bookie_odds)
        >>> print(analysis.best_value_summary)
        HOME @ 2.10 (EV: +15.5%)
    """
    # Calculate bookmaker margin
    total_implied = sum(implied_probability(bookmaker_odds[o]) for o in ["home", "draw", "away"])
    margin = (total_implied - 1) * 100

    # Calculate EV for each outcome
    results = {}
    for outcome in ["home", "draw", "away"]:
        true_prob = elo_probabilities.get(outcome, 0)
        odds = bookmaker_odds.get(outcome, 0)
        implied_prob = implied_probability(odds)
        ev = calculate_ev(true_prob, odds)
        roi = calculate_roi(ev)

        results[outcome] = EVResult(
            outcome=outcome,
            true_probability=true_prob,
            bookmaker_odds=odds,
            implied_probability=implied_prob,
            expected_value=ev,
            roi_percentage=roi,
        )

    return MatchEVAnalysis(
        home_ev=results["home"],
        draw_ev=results["draw"],
        away_ev=results["away"],
        bookmaker_margin=margin,
    )


def kelly_criterion(
    probability: float, decimal_odds: float, fraction: float = 0.25
) -> float:
    """
    Calculate optimal bet size using Kelly Criterion.

    Kelly formula: f = (bp - q) / b
    where:
        f = fraction of bankroll to bet
        b = net odds (decimal_odds - 1)
        p = probability of winning
        q = probability of losing (1 - p)

    Args:
        probability: Your true win probability (0-1)
        decimal_odds: Decimal odds
        fraction: Kelly fraction for safety (0.25 = quarter Kelly)

    Returns:
        Percentage of bankroll to bet (0-1)

    Example:
        >>> kelly_criterion(0.55, 2.10, fraction=0.25)
        0.0595  # Bet 5.95% of bankroll (quarter Kelly)
    """
    if probability <= 0 or probability >= 1 or decimal_odds <= 1:
        return 0.0

    q = 1 - probability  # Probability of losing
    b = decimal_odds - 1  # Net odds

    # Full Kelly
    kelly = (b * probability - q) / b

    # Never bet negative Kelly or more than full bankroll
    kelly = max(0, min(kelly, 1))

    # Apply fractional Kelly for safety
    return kelly * fraction


def find_value_bets(
    matches: list, min_ev_threshold: float = 0.05
) -> list:
    """
    Filter matches to find value bets above threshold.

    Args:
        matches: List of MatchEVAnalysis objects
        min_ev_threshold: Minimum EV required (0.05 = 5%)

    Returns:
        List of matches with value bets, sorted by EV descending
    """
    value_matches = [
        match
        for match in matches
        if match.has_any_value and match.best_value.expected_value >= min_ev_threshold
    ]

    # Sort by EV descending
    value_matches.sort(key=lambda m: m.best_value.expected_value, reverse=True)

    return value_matches


def calculate_bookmaker_margin(odds: Dict[str, float]) -> float:
    """
    Calculate bookmaker's overround/margin percentage.

    Args:
        odds: Dict with 'home', 'draw', 'away' decimal odds

    Returns:
        Margin as percentage (5.2 = 5.2% margin)
    """
    total_implied = sum(implied_probability(odds[o]) for o in ["home", "draw", "away"])
    return (total_implied - 1) * 100
