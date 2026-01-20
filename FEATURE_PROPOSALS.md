# Feature Proposals and Enhancements
## Football Elo Odds Calculator

**Date:** 2026-01-20
**Author:** Claude Code

---

## Table of Contents

1. [Core Feature Enhancements](#core-feature-enhancements)
2. [New Features](#new-features)
3. [User Experience Improvements](#user-experience-improvements)
4. [Data and Analytics](#data-and-analytics)
5. [Integration and API](#integration-and-api)
6. [Performance and Scalability](#performance-and-scalability)

---

## Core Feature Enhancements

### 1. Historical Odds Tracking 📊

**Priority:** HIGH
**Effort:** Medium (3-4 days)
**Business Value:** HIGH

**Description:**
Track historical odds predictions and actual match results to measure model accuracy and build trust with users.

**Features:**
- Store calculated odds with timestamps
- Record actual match results
- Calculate model performance metrics (Brier score, log loss, ROI)
- Display accuracy trends over time
- Compare model performance across leagues

**Implementation:**

```python
# src/models/history.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import sqlite3

@dataclass
class OddsRecord:
    """Historical odds record."""
    match_id: str
    timestamp: datetime
    home_team: str
    away_team: str
    league: str
    predicted_home_odds: float
    predicted_draw_odds: float
    predicted_away_odds: float
    actual_result: Optional[str] = None  # "H", "D", "A"
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None

class OddsHistoryTracker:
    """Track and analyze historical odds predictions."""

    def __init__(self, db_path: str = "odds_history.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS odds_history (
                match_id TEXT PRIMARY KEY,
                timestamp DATETIME,
                home_team TEXT,
                away_team TEXT,
                league TEXT,
                country TEXT,
                home_rating REAL,
                away_rating REAL,
                predicted_home_odds REAL,
                predicted_draw_odds REAL,
                predicted_away_odds REAL,
                predicted_home_prob REAL,
                predicted_draw_prob REAL,
                predicted_away_prob REAL,
                actual_result TEXT,
                actual_home_score INTEGER,
                actual_away_score INTEGER,
                result_timestamp DATETIME
            )
        """)
        self.conn.commit()

    def save_prediction(self, record: OddsRecord):
        """Save an odds prediction."""
        # Implementation...

    def update_result(self, match_id: str, result: str, home_score: int, away_score: int):
        """Update actual match result."""
        # Implementation...

    def calculate_accuracy(self, league: Optional[str] = None, days: int = 30) -> dict:
        """Calculate model accuracy metrics."""
        # Calculate:
        # - Correct prediction rate
        # - Brier score
        # - Log loss
        # - ROI (if betting at predicted odds)
        # Implementation...

# UI Component
def display_model_performance():
    """Display model accuracy metrics in sidebar."""
    st.sidebar.subheader("📈 Model Performance")

    tracker = OddsHistoryTracker()
    accuracy = tracker.calculate_accuracy(days=30)

    st.sidebar.metric("30-Day Accuracy", f"{accuracy['correct_rate']:.1%}")
    st.sidebar.metric("Brier Score", f"{accuracy['brier_score']:.3f}")
    st.sidebar.metric("Theoretical ROI", f"{accuracy['roi']:.1%}")

    with st.sidebar.expander("View Details"):
        st.write("Last 10 predictions:")
        recent = tracker.get_recent_predictions(10)
        st.dataframe(recent)
```

**UI Mockup:**
```
┌─────────────────────────────────────┐
│ 📈 Model Performance (Last 30 Days) │
├─────────────────────────────────────┤
│ Predictions: 247                     │
│ Correct: 108 (43.7%) ✓              │
│ Brier Score: 0.248                   │
│ Log Loss: 1.05                       │
│ Theoretical ROI: +5.2%               │
│                                      │
│ ▶ View Detailed Breakdown           │
└─────────────────────────────────────┘
```

---

### 2. Odds Comparison with Bookmakers 💰

**Priority:** HIGH
**Effort:** High (5-6 days)
**Business Value:** VERY HIGH

**Description:**
Compare calculated fair odds with actual bookmaker odds to identify value bets.

**Features:**
- Scrape odds from multiple bookmakers
- Display odds comparison table
- Highlight value bets (bookmaker odds > fair odds)
- Calculate expected value (EV) for each bet
- Track best odds across bookmakers

**Implementation:**

```python
# src/services/bookmaker_scraper.py
from dataclasses import dataclass
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

@dataclass
class BookmakerOdds:
    """Bookmaker odds for a match."""
    bookmaker: str
    home_odds: float
    draw_odds: float
    away_odds: float
    timestamp: datetime
    url: str

class OddsComparison:
    """Compare fair odds with bookmaker odds."""

    BOOKMAKERS = {
        "bet365": "https://www.bet365.com/...",
        "betfair": "https://www.betfair.com/...",
        "pinnacle": "https://www.pinnacle.com/...",
        # Add more bookmakers
    }

    def get_bookmaker_odds(self, home_team: str, away_team: str) -> List[BookmakerOdds]:
        """Fetch odds from multiple bookmakers."""
        # Implementation with scraping or API calls
        pass

    def calculate_value_bets(
        self,
        fair_odds: Dict[str, float],
        bookmaker_odds: List[BookmakerOdds]
    ) -> List[dict]:
        """Identify value bets."""
        value_bets = []

        for bookie_odds in bookmaker_odds:
            # Home value bet
            if bookie_odds.home_odds > fair_odds['home']:
                ev = (bookie_odds.home_odds / fair_odds['home'] - 1) * 100
                value_bets.append({
                    'bookmaker': bookie_odds.bookmaker,
                    'market': 'Home Win',
                    'fair_odds': fair_odds['home'],
                    'bookmaker_odds': bookie_odds.home_odds,
                    'expected_value': ev,
                    'edge': (1/fair_odds['home'] - 1/bookie_odds.home_odds) * 100
                })

            # Similar for draw and away...

        return sorted(value_bets, key=lambda x: x['expected_value'], reverse=True)

# UI Component
def display_odds_comparison(fair_odds: dict, home_team: str, away_team: str):
    """Display odds comparison with bookmakers."""
    st.subheader("💰 Odds Comparison")

    comparator = OddsComparison()
    bookmaker_odds = comparator.get_bookmaker_odds(home_team, away_team)
    value_bets = comparator.calculate_value_bets(fair_odds, bookmaker_odds)

    # Display comparison table
    comparison_df = pd.DataFrame([
        {
            'Bookmaker': 'Fair Value',
            'Home': f"{fair_odds['home']:.2f}",
            'Draw': f"{fair_odds['draw']:.2f}",
            'Away': f"{fair_odds['away']:.2f}",
            'Margin': "0.0%"
        }
    ] + [
        {
            'Bookmaker': odds.bookmaker.title(),
            'Home': f"{odds.home_odds:.2f}",
            'Draw': f"{odds.draw_odds:.2f}",
            'Away': f"{odds.away_odds:.2f}",
            'Margin': f"{((1/odds.home_odds + 1/odds.draw_odds + 1/odds.away_odds - 1) * 100):.1f}%"
        }
        for odds in bookmaker_odds
    ])

    st.dataframe(comparison_df)

    # Display value bets
    if value_bets:
        st.subheader("🎯 Value Bets Identified")
        for bet in value_bets[:5]:  # Top 5 value bets
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.write(f"**{bet['bookmaker']}** - {bet['market']}")
            col2.write(f"Odds: {bet['bookmaker_odds']:.2f} (Fair: {bet['fair_odds']:.2f})")
            col3.metric("EV", f"+{bet['expected_value']:.1f}%")
    else:
        st.info("No value bets identified at current odds.")
```

---

### 3. Advanced Lineup Impact Analysis 🎽

**Priority:** MEDIUM
**Effort:** Medium (3-4 days)
**Business Value:** MEDIUM

**Description:**
Calculate how lineup changes affect team strength and odds in real-time.

**Features:**
- Real-time odds recalculation as lineup changes
- Position-weighted impact (goalkeeper vs striker)
- Fatigue modeling (recent match congestion)
- Injury impact assessment
- Lineup strength visualization

**Implementation:**

```python
# src/models/lineup_impact.py
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Player:
    """Player with position and rating."""
    name: str
    position: str
    rating: int
    minutes_played_last_7_days: int = 0
    is_injured: bool = False

POSITION_WEIGHTS = {
    'GK': 1.2,   # Goalkeeper more important
    'DEF': 1.0,
    'MID': 0.95,
    'FWD': 1.1,  # Striker important for goals
}

def calculate_lineup_strength(
    players: List[Player],
    include_fatigue: bool = True
) -> Dict[str, float]:
    """Calculate adjusted team strength from lineup."""

    total_weighted_rating = 0
    total_weight = 0

    for player in players:
        if player.is_injured:
            continue

        # Base rating
        rating = player.rating

        # Apply fatigue penalty
        if include_fatigue and player.minutes_played_last_7_days > 270:
            fatigue_penalty = (player.minutes_played_last_7_days - 270) / 100
            rating -= min(fatigue_penalty, 10)  # Max 10 point penalty

        # Apply position weight
        position_weight = POSITION_WEIGHTS.get(player.position, 1.0)

        total_weighted_rating += rating * position_weight
        total_weight += position_weight

    avg_rating = total_weighted_rating / total_weight if total_weight > 0 else 0

    return {
        'average_rating': avg_rating,
        'player_count': len(players),
        'fatigue_adjusted': include_fatigue,
    }

def simulate_lineup_changes(
    current_lineup: List[Player],
    bench_players: List[Player],
    changes: List[tuple]
) -> dict:
    """Simulate impact of lineup changes."""

    current_strength = calculate_lineup_strength(current_lineup)

    # Apply changes
    modified_lineup = current_lineup.copy()
    for player_out, player_in in changes:
        idx = next(i for i, p in enumerate(modified_lineup) if p.name == player_out.name)
        modified_lineup[idx] = player_in

    new_strength = calculate_lineup_strength(modified_lineup)

    rating_delta = new_strength['average_rating'] - current_strength['average_rating']

    return {
        'current_strength': current_strength,
        'new_strength': new_strength,
        'rating_delta': rating_delta,
        'impact_description': _describe_impact(rating_delta)
    }

def _describe_impact(delta: float) -> str:
    """Describe the impact of lineup change."""
    if abs(delta) < 0.5:
        return "Minimal impact"
    elif delta > 2:
        return "Significant strengthening"
    elif delta > 0:
        return "Slight strengthening"
    elif delta < -2:
        return "Significant weakening"
    else:
        return "Slight weakening"

# UI Component
def display_lineup_impact_tool():
    """Interactive lineup change simulator."""
    st.subheader("🎽 Lineup Impact Simulator")

    st.info("Select players to substitute and see real-time odds impact")

    # Player substitution UI
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Player Out**")
        player_out = st.selectbox("Select player to remove", current_lineup)

    with col2:
        st.write("**Player In**")
        player_in = st.selectbox("Select replacement", bench_players)

    if st.button("Calculate Impact"):
        impact = simulate_lineup_changes(
            current_lineup,
            bench_players,
            [(player_out, player_in)]
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Avg", f"{impact['current_strength']['average_rating']:.2f}")
        col2.metric("New Avg", f"{impact['new_strength']['average_rating']:.2f}")
        col3.metric("Change", f"{impact['rating_delta']:+.2f}")

        st.write(f"**Impact:** {impact['impact_description']}")

        # Recalculate odds with new rating
        # ...
```

---

## New Features

### 4. Betting Strategy Simulator 🎲

**Priority:** MEDIUM
**Effort:** High (5-6 days)
**Business Value:** HIGH

**Description:**
Simulate different betting strategies over historical data to test profitability.

**Features:**
- Kelly Criterion calculator
- Flat stake simulation
- Value betting strategy
- Martingale/Fibonacci strategies
- Risk management tools
- Performance visualization

**Implementation:**

```python
# src/models/betting_strategy.py
from typing import List, Dict, Callable
from dataclasses import dataclass
from enum import Enum

class BettingStrategy(Enum):
    FLAT_STAKE = "flat_stake"
    KELLY_CRITERION = "kelly"
    VALUE_BETTING = "value"
    PROPORTIONAL = "proportional"

@dataclass
class Bet:
    """Individual bet record."""
    match_id: str
    stake: float
    odds: float
    outcome: str  # "W", "L", "P" (win, loss, push)
    profit: float

class BettingSimulator:
    """Simulate betting strategies on historical data."""

    def __init__(self, starting_bankroll: float = 1000.0):
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll
        self.bets: List[Bet] = []

    def kelly_stake(self, fair_prob: float, bookmaker_odds: float, bankroll: float, kelly_fraction: float = 0.25) -> float:
        """Calculate Kelly Criterion stake."""
        q = 1 - fair_prob  # Probability of losing
        p = fair_prob      # Probability of winning
        b = bookmaker_odds - 1  # Net odds

        # Kelly formula: f = (bp - q) / b
        kelly = (b * p - q) / b

        # Apply fractional Kelly for safety
        stake = max(0, kelly * kelly_fraction * bankroll)

        return min(stake, bankroll * 0.1)  # Max 10% of bankroll

    def simulate_flat_stake(self, bets_data: List[Dict], stake_size: float = 10.0) -> Dict:
        """Simulate flat stake betting."""
        bankroll = self.starting_bankroll
        results = []

        for bet_data in bets_data:
            if bankroll < stake_size:
                break

            stake = stake_size
            bankroll -= stake

            if bet_data['won']:
                profit = stake * (bet_data['odds'] - 1)
                bankroll += stake + profit
                results.append(Bet(
                    bet_data['match_id'],
                    stake,
                    bet_data['odds'],
                    'W',
                    profit
                ))
            else:
                results.append(Bet(
                    bet_data['match_id'],
                    stake,
                    bet_data['odds'],
                    'L',
                    -stake
                ))

        return {
            'final_bankroll': bankroll,
            'total_profit': bankroll - self.starting_bankroll,
            'roi': ((bankroll - self.starting_bankroll) / self.starting_bankroll) * 100,
            'total_bets': len(results),
            'winning_bets': sum(1 for b in results if b.outcome == 'W'),
            'win_rate': sum(1 for b in results if b.outcome == 'W') / len(results) if results else 0,
            'bets': results
        }

    def simulate_kelly(self, bets_data: List[Dict], kelly_fraction: float = 0.25) -> Dict:
        """Simulate Kelly Criterion betting."""
        # Similar to flat_stake but with dynamic stake sizing
        pass

    def simulate_value_betting(self, bets_data: List[Dict], min_edge: float = 5.0) -> Dict:
        """Simulate value betting (only bet when edge > min_edge)."""
        pass

# UI Component
def display_betting_simulator():
    """Interactive betting strategy simulator."""
    st.header("🎲 Betting Strategy Simulator")

    # Load historical data
    tracker = OddsHistoryTracker()
    historical_data = tracker.get_completed_predictions(days=90)

    if not historical_data:
        st.warning("Not enough historical data for simulation.")
        return

    # Strategy selection
    st.subheader("Configure Strategy")

    col1, col2 = st.columns(2)

    with col1:
        strategy = st.selectbox(
            "Betting Strategy",
            ["Flat Stake", "Kelly Criterion", "Value Betting (5% edge)", "Value Betting (10% edge)"]
        )

        starting_bankroll = st.number_input(
            "Starting Bankroll",
            min_value=100.0,
            max_value=100000.0,
            value=1000.0,
            step=100.0
        )

    with col2:
        if strategy == "Flat Stake":
            stake_size = st.slider("Stake Size", 1.0, 100.0, 10.0, 1.0)
        elif strategy == "Kelly Criterion":
            kelly_fraction = st.slider("Kelly Fraction", 0.1, 1.0, 0.25, 0.05)

    if st.button("Run Simulation"):
        simulator = BettingSimulator(starting_bankroll)

        if strategy == "Flat Stake":
            results = simulator.simulate_flat_stake(historical_data, stake_size)
        elif strategy == "Kelly Criterion":
            results = simulator.simulate_kelly(historical_data, kelly_fraction)
        # ... other strategies

        # Display results
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Bankroll", f"£{results['final_bankroll']:.2f}")
        col2.metric("Total Profit", f"£{results['total_profit']:.2f}")
        col3.metric("ROI", f"{results['roi']:.1f}%")
        col4.metric("Win Rate", f"{results['win_rate']:.1%}")

        # Bankroll evolution chart
        st.subheader("Bankroll Evolution")
        bankroll_history = [starting_bankroll]
        for bet in results['bets']:
            bankroll_history.append(bankroll_history[-1] + bet.profit)

        chart_data = pd.DataFrame({
            'Bet Number': range(len(bankroll_history)),
            'Bankroll': bankroll_history
        })

        st.line_chart(chart_data, x='Bet Number', y='Bankroll')

        # Bet history table
        with st.expander("View Bet History"):
            bets_df = pd.DataFrame([
                {
                    'Match': bet.match_id,
                    'Stake': f"£{bet.stake:.2f}",
                    'Odds': f"{bet.odds:.2f}",
                    'Outcome': bet.outcome,
                    'Profit/Loss': f"£{bet.profit:.2f}"
                }
                for bet in results['bets']
            ])
            st.dataframe(bets_df)
```

---

### 5. Live Match Odds Updates ⚡

**Priority:** HIGH
**Effort:** Very High (10+ days)
**Business Value:** VERY HIGH

**Description:**
Real-time odds updates during live matches based on current score, time, and events.

**Features:**
- Live score integration
- In-play odds calculation
- Event-based odds adjustments (red cards, injuries)
- Time-decay modeling
- Live odds visualization

**Technical Requirements:**
- WebSocket connection to live score API
- Real-time Streamlit updates
- In-play odds model

**Implementation Outline:**

```python
# src/services/live_odds.py
import asyncio
import websockets
from typing import Dict, Callable

class LiveMatchOdds:
    """Calculate and update odds during live matches."""

    def __init__(self, match_id: str):
        self.match_id = match_id
        self.current_state = {
            'minute': 0,
            'home_score': 0,
            'away_score': 0,
            'red_cards_home': 0,
            'red_cards_away': 0,
        }

    async def connect_live_feed(self, callback: Callable):
        """Connect to live score feed and update odds."""
        uri = f"wss://api.livescores.com/matches/{self.match_id}"

        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                data = json.loads(message)
                self.current_state.update(data)

                # Recalculate odds
                new_odds = self.calculate_live_odds()
                callback(new_odds)

    def calculate_live_odds(self) -> Dict[str, float]:
        """Calculate odds based on current match state."""
        minute = self.current_state['minute']
        score_diff = self.current_state['home_score'] - self.current_state['away_score']
        time_remaining = 90 - minute

        # Apply Bayesian update to pre-match odds
        # Factor in:
        # - Current score
        # - Time remaining
        # - Red cards
        # - Expected goals remaining

        # Implementation...
        pass

# Streamlit integration with auto-refresh
def display_live_match_odds(match_id: str):
    """Display live updating odds."""
    st.header("⚡ Live Match Odds")

    placeholder = st.empty()

    live_odds_calculator = LiveMatchOdds(match_id)

    def update_display(odds: dict):
        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            col1.metric("Home", f"{odds['home']:.2f}")
            col2.metric("Draw", f"{odds['draw']:.2f}")
            col3.metric("Away", f"{odds['away']:.2f}")

            st.progress(odds['minute'] / 90)
            st.write(f"⚽ {odds['home_score']} - {odds['away_score']}")

    asyncio.run(live_odds_calculator.connect_live_feed(update_display))
```

---

### 6. League Comparison Tool 📊

**Priority:** LOW
**Effort:** Low (2 days)
**Business Value:** MEDIUM

**Description:**
Compare statistics and odds patterns across different leagues.

**Features:**
- Multi-league statistics comparison
- Home advantage analysis by league
- Draw rate comparison
- Goal distribution analysis
- Market efficiency comparison

**Implementation:**

```python
def display_league_comparison():
    """Compare statistics across multiple leagues."""
    st.header("📊 League Comparison")

    # Select leagues to compare
    selected_leagues = st.multiselect(
        "Select Leagues to Compare",
        options=list(LEAGUE_STATS_MAP.values()),
        default=["England - Premier League", "Spain - LaLiga", "Germany - Bundesliga"]
    )

    if len(selected_leagues) < 2:
        st.warning("Select at least 2 leagues to compare.")
        return

    # Load stats for selected leagues
    stats_data = load_league_stats()
    comparison_data = []

    for league in selected_leagues:
        normalized = normalize_league_key(league)
        if normalized in stats_data:
            stats = stats_data[normalized]
            comparison_data.append({
                'League': league,
                'Home Win %': f"{stats.get('HomeW%', 0):.1%}",
                'Draw %': f"{stats.get('Draw%', 0):.1%}",
                'Away Win %': f"{stats.get('AwayW%', 0):.1%}",
                'Avg Goals': f"{stats.get('AvgGoals', 0):.2f}",
                'Home Adv': f"{stats.get('AvgHG', 0) - stats.get('AvgAG', 0):.2f}",
            })

    df = pd.DataFrame(comparison_data)
    st.dataframe(df)

    # Visualization
    st.subheader("Visual Comparison")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Plot 1: Win Distribution
    # Plot 2: Average Goals
    # Plot 3: Home Advantage
    # Plot 4: Draw Rate Trend

    st.pyplot(fig)
```

---

### 7. Custom Odds Model Builder 🔧

**Priority:** LOW
**Effort:** High (6-7 days)
**Business Value:** LOW (niche users)

**Description:**
Allow advanced users to customize the odds calculation model parameters.

**Features:**
- Adjustable model parameters (draw rate scale, Elo factors)
- A/B testing of different models
- Backtest custom models on historical data
- Save and load model configurations
- Model performance comparison

---

### 8. Mobile-Optimized PWA 📱

**Priority:** MEDIUM
**Effort:** Medium (4-5 days)
**Business Value:** MEDIUM

**Description:**
Convert to Progressive Web App for mobile users.

**Features:**
- Responsive mobile design
- Offline capability
- Push notifications for value bets
- Install as mobile app
- Touch-optimized interface

---

### 9. Social Features 👥

**Priority:** LOW
**Effort:** Very High (10+ days)
**Business Value:** MEDIUM (for growth)

**Description:**
Community features for sharing and discussing predictions.

**Features:**
- User accounts and profiles
- Share predictions
- Leaderboard for prediction accuracy
- Follow other users
- Comments and discussions
- Betting tips marketplace

---

### 10. Advanced Analytics Dashboard 📈

**Priority:** MEDIUM
**Effort:** High (5-6 days)
**Business Value:** HIGH

**Description:**
Comprehensive analytics and insights dashboard.

**Features:**
- Custom date range analysis
- League-specific insights
- Team performance trends
- Odds movement tracking
- Market inefficiency detection
- Export reports (PDF, Excel)

**Implementation:**

```python
# src/analytics/dashboard.py
import plotly.express as px
import plotly.graph_objects as go

class AnalyticsDashboard:
    """Advanced analytics and visualization."""

    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data

    def team_performance_over_time(self, team_name: str) -> go.Figure:
        """Plot team Elo rating evolution."""
        team_data = self.data[self.data['team'] == team_name]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=team_data['date'],
            y=team_data['elo_rating'],
            mode='lines+markers',
            name='Elo Rating'
        ))

        fig.update_layout(
            title=f"{team_name} - Elo Rating History",
            xaxis_title="Date",
            yaxis_title="Elo Rating"
        )

        return fig

    def league_home_advantage_analysis(self) -> go.Figure:
        """Analyze home advantage across leagues."""
        # Group by league and calculate home win rate
        league_stats = self.data.groupby('league').agg({
            'home_win': 'mean',
            'draw': 'mean',
            'away_win': 'mean',
            'avg_home_goals': 'mean',
            'avg_away_goals': 'mean'
        }).reset_index()

        league_stats['home_advantage'] = league_stats['avg_home_goals'] - league_stats['avg_away_goals']

        fig = px.bar(
            league_stats.sort_values('home_advantage', ascending=False),
            x='league',
            y='home_advantage',
            title='Home Advantage by League',
            labels={'home_advantage': 'Goal Difference (Home - Away)'}
        )

        return fig

    def odds_accuracy_by_confidence(self) -> go.Figure:
        """Plot accuracy vs confidence level."""
        # Bin predictions by confidence (implied probability)
        # Calculate actual win rate for each bin
        # Plot calibration curve

        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        self.data['prob_bin'] = pd.cut(self.data['implied_prob'], bins=bins)

        calibration = self.data.groupby('prob_bin').agg({
            'predicted_prob': 'mean',
            'actual_win': 'mean'
        }).reset_index()

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=calibration['predicted_prob'],
            y=calibration['actual_win'],
            mode='markers+lines',
            name='Model'
        ))

        # Add perfect calibration line
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Perfect Calibration',
            line=dict(dash='dash', color='gray')
        ))

        fig.update_layout(
            title='Model Calibration Curve',
            xaxis_title='Predicted Probability',
            yaxis_title='Actual Win Rate'
        )

        return fig

    def value_bet_heatmap(self) -> go.Figure:
        """Heatmap showing where value is most commonly found."""
        # Analyze value bet patterns by:
        # - League
        # - Market (1X2, O/U, etc.)
        # - Day of week
        # - Time until kickoff

        pivot = self.data.pivot_table(
            values='edge',
            index='league',
            columns='market',
            aggfunc='mean'
        )

        fig = px.imshow(
            pivot,
            title='Average Edge by League and Market',
            labels=dict(x='Market', y='League', color='Edge %'),
            color_continuous_scale='RdYlGn'
        )

        return fig

# UI Component
def display_analytics_dashboard():
    """Render analytics dashboard."""
    st.header("📈 Advanced Analytics Dashboard")

    # Load historical data
    data = load_historical_predictions()

    dashboard = AnalyticsDashboard(data)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        date_range = st.date_input("Date Range", [])
    with col2:
        selected_leagues = st.multiselect("Leagues", options=data['league'].unique())
    with col3:
        min_matches = st.number_input("Min Matches", min_value=0, value=10)

    # Apply filters
    filtered_data = data  # Apply filters...

    # Display charts
    tab1, tab2, tab3, tab4 = st.tabs([
        "Performance", "Calibration", "Value Patterns", "League Analysis"
    ])

    with tab1:
        st.plotly_chart(dashboard.team_performance_over_time(selected_team))

    with tab2:
        st.plotly_chart(dashboard.odds_accuracy_by_confidence())

    with tab3:
        st.plotly_chart(dashboard.value_bet_heatmap())

    with tab4:
        st.plotly_chart(dashboard.league_home_advantage_analysis())

    # Export functionality
    if st.button("📥 Export Report"):
        # Generate PDF or Excel report
        pass
```

---

## User Experience Improvements

### 11. Favorites and Watchlists ⭐

**Priority:** MEDIUM
**Effort:** Low (2 days)
**Business Value:** MEDIUM

**Description:**
Allow users to save favorite teams and matches for quick access.

**Features:**
- Favorite teams list
- Custom watchlists
- Quick access sidebar
- Notifications for favorite matches
- Persistent user preferences

---

### 12. Dark/Light Theme Toggle 🌙

**Priority:** LOW
**Effort:** Low (1 day)
**Business Value:** LOW

**Description:**
Add theme switcher for better user experience.

**Implementation:**

```python
# Theme configuration
def apply_theme(theme: str):
    """Apply dark or light theme."""
    if theme == "dark":
        st.markdown("""
            <style>
            :root {
                --background: #0e1117;
                --text: #fafafa;
                --card-bg: #262730;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            :root {
                --background: #ffffff;
                --text: #0e1117;
                --card-bg: #f0f2f6;
            }
            </style>
        """, unsafe_allow_html=True)

# UI Component
theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=1)
apply_theme(theme.lower())
```

---

### 13. Keyboard Shortcuts ⌨️

**Priority:** LOW
**Effort:** Low (1 day)
**Business Value:** LOW

**Description:**
Add keyboard shortcuts for power users.

**Shortcuts:**
- `Alt + H`: Select home team dropdown
- `Alt + A`: Select away team dropdown
- `Alt + C`: Calculate odds
- `Alt + R`: Refresh data
- `/`: Focus search box

---

### 14. Guided Tour for New Users 👋

**Priority:** LOW
**Effort:** Medium (2-3 days)
**Business Value:** MEDIUM

**Description:**
Interactive tutorial for first-time users.

**Features:**
- Step-by-step guide
- Tooltips on features
- Video tutorials
- FAQ section
- Help center

---

## Data and Analytics

### 15. API for External Access 🔌

**Priority:** MEDIUM
**Effort:** High (5-6 days)
**Business Value:** HIGH (monetization)

**Description:**
RESTful API for accessing odds calculations programmatically.

**Endpoints:**
```
GET /api/v1/leagues
GET /api/v1/leagues/{league_id}/teams
GET /api/v1/odds/match?home={team}&away={team}&league={league}
GET /api/v1/odds/historical?team={team}&days={n}
POST /api/v1/odds/calculate
```

**Implementation:**

```python
# api/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

app = FastAPI(title="Football Elo Odds API", version="1.0.0")

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key."""
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

class OddsRequest(BaseModel):
    home_team: str
    away_team: str
    league: str
    country: str
    margin: float = 5.0

class OddsResponse(BaseModel):
    home_odds: float
    draw_odds: float
    away_odds: float
    home_probability: float
    draw_probability: float
    away_probability: float
    timestamp: datetime

@app.get("/api/v1/leagues")
def get_leagues(api_key: str = Depends(verify_api_key)):
    """Get list of available leagues."""
    return {"leagues": list(LEAGUE_STATS_MAP.values())}

@app.post("/api/v1/odds/calculate", response_model=OddsResponse)
def calculate_odds(
    request: OddsRequest,
    api_key: str = Depends(verify_api_key)
):
    """Calculate odds for a match."""
    try:
        # Fetch team ratings
        home_rating = get_team_rating(request.home_team, request.country, request.league)
        away_rating = get_team_rating(request.away_team, request.country, request.league)

        # Get league stats
        league_draw_rate = get_league_suggested_draw_rate(request.country, request.league)
        league_avg_goals = get_league_average_goals(request.country, request.league)

        # Calculate probabilities
        p_home, p_draw, p_away = calculate_outcome_probabilities(
            home_rating, away_rating, league_draw_rate, league_avg_goals
        )

        # Apply margin
        odds = apply_margin([p_home, p_draw, p_away], request.margin)

        return OddsResponse(
            home_odds=odds[0],
            draw_odds=odds[1],
            away_odds=odds[2],
            home_probability=p_home,
            draw_probability=p_draw,
            away_probability=p_away,
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn api.main:app --reload
```

---

### 16. Data Export and Import 💾

**Priority:** LOW
**Effort:** Low (2 days)
**Business Value:** LOW

**Description:**
Export historical predictions and import custom data.

**Features:**
- Export to CSV/JSON/Excel
- Import custom league statistics
- Backup and restore functionality
- Data migration tools

---

## Integration and API

### 17. Telegram Bot Integration 🤖

**Priority:** MEDIUM
**Effort:** Medium (3-4 days)
**Business Value:** MEDIUM

**Description:**
Telegram bot for quick odds lookups and notifications.

**Features:**
- `/odds Team1 vs Team2` - Get match odds
- `/value` - Today's value bets
- `/subscribe Team` - Get notifications
- `/history Team` - Team statistics

**Implementation:**

```python
# bot/telegram_bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def odds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /odds command."""
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /odds HomeTeam vs AwayTeam")
        return

    home_team = context.args[0]
    away_team = context.args[2]

    # Calculate odds
    odds = calculate_match_odds(home_team, away_team)

    message = f"""
    ⚽ {home_team} vs {away_team}

    1️⃣ Home: {odds['home']:.2f}
    ❌ Draw: {odds['draw']:.2f}
    2️⃣ Away: {odds['away']:.2f}

    📊 Fair probabilities:
    Home: {odds['home_prob']:.1%}
    Draw: {odds['draw_prob']:.1%}
    Away: {odds['away_prob']:.1%}
    """

    await update.message.reply_text(message)

async def value_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /value command."""
    value_bets = find_todays_value_bets()

    if not value_bets:
        await update.message.reply_text("No value bets found today.")
        return

    message = "🎯 Today's Value Bets:\n\n"
    for bet in value_bets[:5]:
        message += f"{bet['home']} vs {bet['away']}\n"
        message += f"Market: {bet['market']}\n"
        message += f"Fair odds: {bet['fair_odds']:.2f}\n"
        message += f"Bookmaker: {bet['bookmaker_odds']:.2f}\n"
        message += f"Edge: +{bet['edge']:.1f}%\n\n"

    await update.message.reply_text(message)

def main():
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("odds", odds_command))
    application.add_handler(CommandHandler("value", value_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))

    application.run_polling()

if __name__ == '__main__':
    main()
```

---

### 18. Discord Bot Integration 💬

**Priority:** LOW
**Effort:** Medium (3 days)
**Business Value:** LOW

Similar to Telegram bot but for Discord communities.

---

### 19. Browser Extension 🔧

**Priority:** LOW
**Effort:** High (6-7 days)
**Business Value:** MEDIUM

**Description:**
Browser extension to display fair odds on bookmaker websites.

**Features:**
- Overlay fair odds on bookmaker sites
- Highlight value bets in green
- One-click odds comparison
- Works on bet365, Betfair, etc.

---

## Priority Matrix

| Feature | Priority | Effort | Business Value | Suggested Order |
|---------|----------|--------|----------------|-----------------|
| Historical Odds Tracking | HIGH | Medium | HIGH | 1 |
| Dependency Management | HIGH | Low | HIGH | 2 |
| Testing Infrastructure | HIGH | Medium | HIGH | 3 |
| Odds Comparison with Bookmakers | HIGH | High | VERY HIGH | 4 |
| Error Handling & Logging | HIGH | Medium | HIGH | 5 |
| Code Refactoring | HIGH | High | MEDIUM | 6 |
| Betting Strategy Simulator | MEDIUM | High | HIGH | 7 |
| Advanced Analytics Dashboard | MEDIUM | High | HIGH | 8 |
| API Development | MEDIUM | High | HIGH | 9 |
| Live Match Odds | HIGH | Very High | VERY HIGH | 10 |
| Advanced Lineup Analysis | MEDIUM | Medium | MEDIUM | 11 |
| Favorites & Watchlists | MEDIUM | Low | MEDIUM | 12 |
| Telegram Bot | MEDIUM | Medium | MEDIUM | 13 |
| Mobile PWA | MEDIUM | Medium | MEDIUM | 14 |
| League Comparison | LOW | Low | MEDIUM | 15 |
| Documentation | MEDIUM | Medium | MEDIUM | 16 |

---

## Estimated Development Timeline

### Phase 1: Foundation & Quality (4-6 weeks)
- Testing infrastructure
- Linting and formatting
- Error handling
- Code refactoring
- Documentation

### Phase 2: Core Features (6-8 weeks)
- Historical odds tracking
- Odds comparison
- Betting strategy simulator
- Advanced analytics dashboard

### Phase 3: Integration & Growth (4-6 weeks)
- API development
- Telegram bot
- Mobile PWA
- Social features (optional)

### Phase 4: Advanced Features (6-8 weeks)
- Live match odds
- Advanced lineup analysis
- Browser extension
- Custom model builder

**Total Estimated Time:** 20-28 weeks (5-7 months)

---

## Monetization Opportunities

1. **Premium API Access** - Charge for API usage
2. **Pro Subscription** - Advanced features, more data, no ads
3. **Betting Tips Service** - Curated value bets
4. **Affiliate Partnerships** - Bookmaker referrals
5. **White-label Solution** - Sell to other platforms
6. **Data Licensing** - License historical odds data

---

## Conclusion

This Football Elo Odds Calculator has significant potential for growth. The priority should be:

1. **Short-term:** Fix code quality issues and add testing
2. **Medium-term:** Add value-adding features (odds comparison, betting simulator)
3. **Long-term:** Scale with API, mobile app, and advanced analytics

The most impactful features are:
- ✅ Odds comparison with bookmakers (identifies value)
- ✅ Historical tracking (builds credibility)
- ✅ Betting strategy simulator (helps users make decisions)
- ✅ API access (monetization + reach)

Focus on features that help users win bets, and the platform will grow organically.
