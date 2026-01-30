"""Tests for Kambi API client."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from kambi_client import KambiClient, KambiMatch


class TestKambiMatch:
    """Tests for KambiMatch dataclass."""

    def test_has_odds_complete(self):
        """Test has_odds with complete odds."""
        match = KambiMatch(
            event_id=123,
            home_team="Arsenal",
            away_team="Chelsea",
            league="Premier League",
            league_id=456,
            country="England",
            start_time=datetime.now(),
            state="NOT_STARTED",
            odds_home=2.00,
            odds_draw=3.40,
            odds_away=3.50
        )
        assert match.has_odds is True

    def test_has_odds_incomplete(self):
        """Test has_odds with missing odds."""
        match = KambiMatch(
            event_id=123,
            home_team="Arsenal",
            away_team="Chelsea",
            league="Premier League",
            league_id=456,
            country="England",
            start_time=datetime.now(),
            state="NOT_STARTED",
            odds_home=2.00,
            odds_draw=None,
            odds_away=3.50
        )
        assert match.has_odds is False

    def test_bookmaker_margin(self):
        """Test bookmaker margin calculation."""
        match = KambiMatch(
            event_id=123,
            home_team="Arsenal",
            away_team="Chelsea",
            league="Premier League",
            league_id=456,
            country="England",
            start_time=datetime.now(),
            state="NOT_STARTED",
            odds_home=2.00,
            odds_draw=3.50,
            odds_away=4.00
        )
        # Margin = (1/2.00 + 1/3.50 + 1/4.00 - 1) * 100
        # = (0.5 + 0.286 + 0.25 - 1) * 100 = 3.6%
        assert match.bookmaker_margin == pytest.approx(3.6, rel=1e-2)

    def test_bookmaker_margin_no_odds(self):
        """Test margin returns None when odds missing."""
        match = KambiMatch(
            event_id=123,
            home_team="Arsenal",
            away_team="Chelsea",
            league="Premier League",
            league_id=456,
            country="England",
            start_time=datetime.now(),
            state="NOT_STARTED"
        )
        assert match.bookmaker_margin is None


class TestKambiClient:
    """Tests for KambiClient."""

    def test_initialization(self):
        """Test client initialization with default parameters."""
        client = KambiClient()
        assert client.default_params['channel_id'] == 7
        assert client.default_params['client_id'] == 200
        assert client.default_params['lang'] == 'en_GB'
        assert client.default_params['market'] == 'GB'

    def test_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        client = KambiClient(
            channel_id=1,
            client_id=100,
            lang='en_US',
            market='US'
        )
        assert client.default_params['channel_id'] == 1
        assert client.default_params['client_id'] == 100
        assert client.default_params['lang'] == 'en_US'
        assert client.default_params['market'] == 'US'

    def test_normalize_team_name(self):
        """Test team name normalization."""
        assert KambiClient._normalize_team_name("Manchester United") == "manchester united"
        assert KambiClient._normalize_team_name("  Arsenal  ") == "arsenal"
        assert KambiClient._normalize_team_name("Brighton & Hove Albion") == "brighton hove albion"
        assert KambiClient._normalize_team_name("Köln") == "koeln"
        assert KambiClient._normalize_team_name("Malmö FF") == "malmoe ff"

    def test_normalize_team_name_special_chars(self):
        """Test normalization with various special characters."""
        assert "mueller" in KambiClient._normalize_team_name("Müller")  # ü -> ue
        assert "jose" in KambiClient._normalize_team_name("José")  # é -> e
        assert "fc barcelona" == KambiClient._normalize_team_name("FC Barcelona")

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_with_odds(self, mock_get):
        """Test parsing event with complete 1X2 odds."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Arsenal",
                "awayName": "Chelsea",
                "group": "Premier League",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "England"},
                    {"englishName": "Premier League"}
                ]
            },
            "betOffers": [
                {
                    "betOfferType": {"englishName": "Match"},
                    "criterion": {"englishLabel": "Full Time"},
                    "outcomes": [
                        {"type": "OT_ONE", "odds": 2000, "status": "OPEN"},
                        {"type": "OT_CROSS", "odds": 3400, "status": "OPEN"},
                        {"type": "OT_TWO", "odds": 3500, "status": "OPEN"}
                    ]
                }
            ]
        }

        match = client._parse_event(event_data)

        assert match is not None
        assert match.event_id == 1025052006
        assert match.home_team == "Arsenal"
        assert match.away_team == "Chelsea"
        assert match.league == "Premier League"
        assert match.country == "England"
        assert match.odds_home == 2.00
        assert match.odds_draw == 3.40
        assert match.odds_away == 3.50
        assert match.has_odds is True

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_without_odds(self, mock_get):
        """Test parsing event without bet offers."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Arsenal",
                "awayName": "Chelsea",
                "group": "Premier League",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "England"},
                    {"englishName": "Premier League"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data)

        assert match is not None
        assert match.has_odds is False

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_live_excluded(self, mock_get):
        """Test that live matches are excluded when include_live=False."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Arsenal",
                "awayName": "Chelsea",
                "group": "Premier League",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "STARTED",  # Live match
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "England"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data, include_live=False)
        assert match is None

        match = client._parse_event(event_data, include_live=True)
        assert match is not None

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_esports_excluded(self, mock_get):
        """Test that Esports battle matches are excluded."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Team A",
                "awayName": "Team B",
                "group": "Esports battle",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "World"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data)
        assert match is None

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_cyber_live_arena_excluded(self, mock_get):
        """Test that Cyber Live Arena matches are excluded."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Team X",
                "awayName": "Team Y",
                "group": "Cyber Live Arena",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "World"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data)
        assert match is None

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_esports_case_insensitive(self, mock_get):
        """Test that Esports exclusion is case-insensitive."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Team A",
                "awayName": "Team B",
                "group": "ESPORTS BATTLE",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "World"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data)
        assert match is None

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_esports_with_extra_words(self, mock_get):
        """Test that Esports exclusion works with variations like 'ESports Battle FC'."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Team A",
                "awayName": "Team B",
                "group": "ESports Battle FC - Premier League",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "World"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data)
        assert match is None

    @patch('kambi_client.requests.Session.get')
    def test_parse_event_cyber_with_extra_words(self, mock_get):
        """Test that Cyber exclusion works with variations like 'Cyber Live Football'."""
        client = KambiClient()

        event_data = {
            "event": {
                "id": 1025052006,
                "homeName": "Team X",
                "awayName": "Team Y",
                "group": "Cyber Live Football League",
                "groupId": 2000075067,
                "start": "2026-01-30T15:00:00Z",
                "state": "NOT_STARTED",
                "path": [
                    {"englishName": "Football"},
                    {"englishName": "World"}
                ]
            },
            "betOffers": []
        }

        match = client._parse_event(event_data)
        assert match is None

    @patch('kambi_client.requests.Session.get')
    def test_get_all_football_matches_success(self, mock_get):
        """Test successful fetching of all football matches."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "events": [
                {
                    "event": {
                        "id": 1,
                        "homeName": "Arsenal",
                        "awayName": "Chelsea",
                        "group": "Premier League",
                        "groupId": 100,
                        "start": "2026-01-30T15:00:00Z",
                        "state": "NOT_STARTED",
                        "path": [{"englishName": "Football"}, {"englishName": "England"}]
                    },
                    "betOffers": []
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = KambiClient()
        matches = client.get_all_football_matches()

        assert len(matches) == 1
        assert matches[0].home_team == "Arsenal"

    def test_get_all_football_matches_error(self):
        """Test error handling when API request fails."""
        client = KambiClient()

        # Mock the session.get method directly on the instance
        with patch.object(client.session, 'get', side_effect=requests.exceptions.RequestException("Network error")):
            matches = client.get_all_football_matches()

        assert matches == []

    @patch('kambi_client.KambiClient.get_all_football_matches')
    def test_find_match_exact(self, mock_get_matches):
        """Test finding match with exact team name match."""
        mock_get_matches.return_value = [
            KambiMatch(
                event_id=1,
                home_team="Arsenal",
                away_team="Chelsea",
                league="Premier League",
                league_id=100,
                country="England",
                start_time=datetime.now(),
                state="NOT_STARTED",
                odds_home=2.00,
                odds_draw=3.40,
                odds_away=3.50
            )
        ]

        client = KambiClient()
        match = client.find_match("Arsenal", "Chelsea")

        assert match is not None
        assert match.home_team == "Arsenal"
        assert match.away_team == "Chelsea"

    @patch('kambi_client.KambiClient.get_all_football_matches')
    def test_find_match_fuzzy(self, mock_get_matches):
        """Test finding match with fuzzy team name match."""
        mock_get_matches.return_value = [
            KambiMatch(
                event_id=1,
                home_team="Manchester United",
                away_team="Liverpool FC",
                league="Premier League",
                league_id=100,
                country="England",
                start_time=datetime.now(),
                state="NOT_STARTED",
                odds_home=2.00,
                odds_draw=3.40,
                odds_away=3.50
            )
        ]

        client = KambiClient()
        # Try with slightly different names (lower threshold for fuzzy matching)
        match = client.find_match("Manchester Utd", "Liverpool", threshold=75)

        assert match is not None
        assert match.home_team == "Manchester United"

    @patch('kambi_client.KambiClient.get_all_football_matches')
    def test_find_match_not_found(self, mock_get_matches):
        """Test behavior when match is not found."""
        mock_get_matches.return_value = [
            KambiMatch(
                event_id=1,
                home_team="Arsenal",
                away_team="Chelsea",
                league="Premier League",
                league_id=100,
                country="England",
                start_time=datetime.now(),
                state="NOT_STARTED"
            )
        ]

        client = KambiClient()
        match = client.find_match("Barcelona", "Real Madrid")

        assert match is None

    @patch('kambi_client.KambiClient.get_all_football_matches')
    def test_find_match_with_league_filter(self, mock_get_matches):
        """Test finding match with league filtering."""
        mock_get_matches.return_value = [
            KambiMatch(
                event_id=1,
                home_team="Arsenal",
                away_team="Chelsea",
                league="Premier League",
                league_id=100,
                country="England",
                start_time=datetime.now(),
                state="NOT_STARTED",
                odds_home=2.00,
                odds_draw=3.40,
                odds_away=3.50
            ),
            KambiMatch(
                event_id=2,
                home_team="Arsenal U21",
                away_team="Chelsea U21",
                league="U21 Premier League",
                league_id=200,
                country="England",
                start_time=datetime.now(),
                state="NOT_STARTED",
                odds_home=2.00,
                odds_draw=3.40,
                odds_away=3.50
            )
        ]

        client = KambiClient()
        match = client.find_match("Arsenal", "Chelsea", league="Premier League")

        assert match is not None
        assert match.league == "Premier League"
        assert "U21" not in match.home_team
