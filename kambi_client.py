"""Kambi API client for fetching bookmaker odds."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import requests
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


@dataclass
class KambiMatch:
    """Represents a match from Kambi API."""

    event_id: int
    home_team: str
    away_team: str
    league: str
    league_id: int
    country: str
    start_time: datetime
    state: str
    odds_home: Optional[float] = None
    odds_draw: Optional[float] = None
    odds_away: Optional[float] = None
    odds_timestamp: Optional[datetime] = None

    @property
    def has_odds(self) -> bool:
        """Check if match has complete 1X2 odds."""
        return all(
            [self.odds_home is not None, self.odds_draw is not None, self.odds_away is not None]
        )

    @property
    def bookmaker_margin(self) -> Optional[float]:
        """Calculate bookmaker's overround/margin percentage."""
        if not self.has_odds:
            return None
        implied_probs = 1 / self.odds_home + 1 / self.odds_draw + 1 / self.odds_away
        return (implied_probs - 1) * 100


class KambiClient:
    """Client for interacting with Kambi betting API."""

    BASE_URL = "https://eu1.offering-api.kambicdn.com/offering/v2018/kambi"

    def __init__(
        self,
        channel_id: int = 7,
        client_id: int = 200,
        lang: str = "en_GB",
        market: str = "GB",
    ):
        """
        Initialize Kambi API client.

        Args:
            channel_id: Kambi channel identifier
            client_id: Kambi client identifier
            lang: Language code (default: en_GB)
            market: Market code (default: GB)
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )

        self.default_params = {
            "channel_id": channel_id,
            "client_id": client_id,
            "lang": lang,
            "market": market,
            "useCombined": "true",
            "useCombinedLive": "false",
        }

    def get_all_football_matches(
        self, include_live: bool = False, timeout: int = 15
    ) -> List[KambiMatch]:
        """
        Fetch all football matches with odds from Kambi.

        Args:
            include_live: Include live/in-play matches
            timeout: Request timeout in seconds

        Returns:
            List of KambiMatch objects
        """
        url = f"{self.BASE_URL}/listView/football/all/all/all/matches.json"

        try:
            response = self.session.get(url, params=self.default_params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            matches = []
            for event_data in data.get("events", []):
                match = self._parse_event(event_data, include_live)
                if match:
                    matches.append(match)

            logger.info(f"Fetched {len(matches)} matches from Kambi")
            return matches

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Kambi matches: {e}")
            return []

    def get_matches_by_league(
        self, country: str, league: str, include_live: bool = False, timeout: int = 15
    ) -> List[KambiMatch]:
        """
        Fetch matches for a specific league.

        Args:
            country: Country name or code (e.g., "england", "spain")
            league: League name or code (e.g., "premier-league", "la-liga")
            include_live: Include live/in-play matches
            timeout: Request timeout in seconds

        Returns:
            List of KambiMatch objects for the specified league
        """
        # Normalize country/league for URL
        country_slug = country.lower().replace(" ", "-")
        league_slug = league.lower().replace(" ", "-")

        url = f"{self.BASE_URL}/listView/football/{country_slug}/{league_slug}/all/matches.json"

        try:
            response = self.session.get(url, params=self.default_params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            matches = []
            for event_data in data.get("events", []):
                match = self._parse_event(event_data, include_live)
                if match:
                    matches.append(match)

            logger.info(
                f"Fetched {len(matches)} matches for {country}/{league} from Kambi"
            )
            return matches

        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Failed to fetch Kambi matches for {country}/{league}: {e}"
            )
            return []

    def find_match(
        self, home_team: str, away_team: str, league: Optional[str] = None, threshold: int = 85
    ) -> Optional[KambiMatch]:
        """
        Find a specific match by team names using fuzzy matching.

        Args:
            home_team: Home team name
            away_team: Away team name
            league: Optional league filter
            threshold: Fuzzy matching threshold (0-100, default 85)

        Returns:
            KambiMatch if found, None otherwise
        """
        matches = self.get_all_football_matches()

        # Normalize search terms
        home_normalized = self._normalize_team_name(home_team)
        away_normalized = self._normalize_team_name(away_team)

        best_match = None
        best_score = 0

        for match in matches:
            match_home = self._normalize_team_name(match.home_team)
            match_away = self._normalize_team_name(match.away_team)

            # Calculate fuzzy match scores
            home_score = fuzz.token_sort_ratio(home_normalized, match_home)
            away_score = fuzz.token_sort_ratio(away_normalized, match_away)

            # Average score for both teams
            avg_score = (home_score + away_score) / 2

            # If league specified, boost score for matches in that league
            if league:
                league_normalized = self._normalize_team_name(league)
                match_league = self._normalize_team_name(match.league)
                league_score = fuzz.partial_ratio(league_normalized, match_league)

                # If league matches well, boost the score
                if league_score > 70:
                    avg_score = avg_score * 1.1  # 10% boost for league match

            # Exact match - return immediately
            if home_score == 100 and away_score == 100:
                if league:
                    league_normalized = self._normalize_team_name(league)
                    match_league = self._normalize_team_name(match.league)
                    if league_normalized not in match_league and fuzz.partial_ratio(league_normalized, match_league) < 70:
                        continue
                return match

            # Track best match
            if avg_score > best_score and avg_score >= threshold:
                best_score = avg_score
                best_match = match

        if best_match:
            logger.info(f"Found match with {best_score:.0f}% confidence: {best_match.home_team} vs {best_match.away_team}")
            return best_match

        logger.warning(f"Match not found in Kambi: {home_team} vs {away_team}")
        return None

    def _parse_event(
        self, event_data: Dict, include_live: bool = False
    ) -> Optional[KambiMatch]:
        """
        Parse a single event from Kambi API response.

        Args:
            event_data: Raw event data from API
            include_live: Whether to include live matches

        Returns:
            KambiMatch object or None if event should be skipped
        """
        event = event_data.get("event", {})

        # Skip live matches if not requested
        if not include_live and event.get("state") == "STARTED":
            return None

        # Extract basic match info
        event_id = event.get("id")
        home_team = event.get("homeName", "")
        away_team = event.get("awayName", "")
        league = event.get("group", "")
        league_id = event.get("groupId", 0)
        state = event.get("state", "")

        # Exclude Esports and Cyber matches using keyword matching
        league_lower = league.lower()
        excluded_keywords = [
            ["esports", "battle"],  # Matches any league with both "esports" AND "battle"
            ["cyber", "live"],       # Matches any league with both "cyber" AND "live"
            ["cyber", "arena"],      # Matches any league with both "cyber" AND "arena"
        ]

        for keywords in excluded_keywords:
            if all(keyword in league_lower for keyword in keywords):
                return None

        # Parse start time
        start_str = event.get("start", "")
        try:
            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        except ValueError:
            start_time = datetime.now()

        # Extract country from path
        country = ""
        path = event.get("path", [])
        if len(path) >= 2:  # [Sport, Country, League]
            country = path[1].get("englishName", "")

        # Initialize match
        match = KambiMatch(
            event_id=event_id,
            home_team=home_team,
            away_team=away_team,
            league=league,
            league_id=league_id,
            country=country,
            start_time=start_time,
            state=state,
        )

        # Extract 1X2 odds from betOffers
        bet_offers = event_data.get("betOffers", [])
        for bet_offer in bet_offers:
            # Look for "Match" bet type (1X2)
            bet_type = bet_offer.get("betOfferType", {}).get("englishName", "")
            criterion = bet_offer.get("criterion", {}).get("englishLabel", "")

            if bet_type == "Match" and criterion == "Full Time":
                outcomes = bet_offer.get("outcomes", [])

                for outcome in outcomes:
                    outcome_type = outcome.get("type", "")
                    odds_raw = outcome.get("odds", 0)
                    status = outcome.get("status", "")

                    # Skip suspended/closed outcomes
                    if status != "OPEN":
                        continue

                    # Convert odds (Kambi uses 1000-based format)
                    odds_decimal = odds_raw / 1000.0

                    if outcome_type == "OT_ONE":
                        match.odds_home = odds_decimal
                    elif outcome_type == "OT_CROSS":
                        match.odds_draw = odds_decimal
                    elif outcome_type == "OT_TWO":
                        match.odds_away = odds_decimal

                # Set timestamp if we found odds
                if match.has_odds:
                    match.odds_timestamp = datetime.now()
                    break

        return match

    @staticmethod
    def _normalize_team_name(name: str) -> str:
        """
        Normalize team/league name for matching.

        Args:
            name: Team or league name

        Returns:
            Normalized lowercase name
        """
        if not isinstance(name, str):
            return ""

        # Convert to lowercase and remove extra whitespace
        normalized = name.lower().strip()

        # Replace common special characters
        replacements = {
            "ö": "oe",
            "ü": "ue",
            "ä": "ae",
            "ø": "oe",
            "å": "aa",
            "æ": "ae",
            "ß": "ss",
            "é": "e",
            "è": "e",
            "ê": "e",
            "á": "a",
            "à": "a",
            "â": "a",
            "í": "i",
            "ó": "o",
            "ú": "u",
        }

        for char, replacement in replacements.items():
            normalized = normalized.replace(char, replacement)

        # Remove punctuation
        for char in ["-", ".", "&", "'", ","]:
            normalized = normalized.replace(char, " ")

        # Collapse multiple spaces
        normalized = " ".join(normalized.split())

        return normalized
