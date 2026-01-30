import html
import io
import json
import math
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

import config
from ev_calculator import analyze_match_ev, kelly_criterion
from kambi_client import KambiClient
from odds import calculate_poisson_markets_from_dnb

# Set page title and icon
st.set_page_config(
    page_title="Elo Ratings Odds Calculator", page_icon=str(config.ODDS_ICON_PATH)
)


def modified_bessel_i0(x: float) -> float:
    """Compute the modified Bessel function I0 with a pure-Python fallback.

    Args:
        x: Input value for Bessel function

    Returns:
        Computed Bessel function value
    """
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
                + y
                * (
                    1.2067492
                    + y
                    * (
                        0.2659732
                        + y * (0.0360768 + y * 0.0045813)
                    )
                )
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
                            + y
                            * (
                                0.02635537
                                + y * (-0.01647633 + y * 0.00392377)
                            )
                        )
                    )
                )
            )
        )
    )


def normalize_league_key(name: str) -> str:
    """Ensure league names use a consistent format for lookups.

    Args:
        name: League name to normalize

    Returns:
        Normalized league name
    """
    return re.sub(r"\s+", " ", str(name)).strip()


@st.cache_resource
def get_kambi_client() -> KambiClient:
    """Get cached Kambi API client.

    Returns:
        KambiClient instance
    """
    return KambiClient()


@st.cache_data
def load_league_stats(path: str = str(config.LEAGUE_STATS_PATH)) -> Dict[str, Dict[str, Any]]:
    """Load league statistics from a JSON or CSV source.

    Args:
        path: Path to the league stats file

    Returns:
        Dictionary mapping league names to their statistics
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return {}

    if path_obj.suffix.lower() == ".csv":
        df = pd.read_csv(path_obj)
        raw_data = {}
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            league_name = normalize_league_key(row_dict.pop("League", ""))
            if not league_name:
                continue
            raw_data[league_name] = row_dict
    else:
        with path_obj.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)

    league_stats = {}
    for league_name, stats in raw_data.items():
        if not isinstance(stats, dict):
            continue
        normalized_name = normalize_league_key(league_name)
        league_stats[normalized_name] = {str(key): value for key, value in stats.items()}

    return league_stats







# Combined dictionary for both Men's and Women's leagues

# Combine Men's and Women's league data into a single dictionary
all_leagues = {**config.LEAGUES_DATA["Men's"], **config.LEAGUES_DATA["Women's"]}
# Sort the combined list of countries/leagues alphabetically
sorted_countries = sorted(all_leagues.keys())


# --- Utility Functions ---

def load_css(file_name: str) -> None:
    """Loads a local CSS file.

    Args:
        file_name: Path to the CSS file
    """
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please add it to the directory.")

def fetch_with_headers(
    url: str, referer: Optional[str] = None, timeout: int = 15
) -> requests.Response:
    """Fetches a URL with custom headers to mimic a browser.

    Args:
        url: URL to fetch
        referer: Referer header value (optional)
        timeout: Request timeout in seconds

    Returns:
        Response object

    Raises:
        requests.HTTPError: If the request fails
    """
    headers = config.BASE_HEADERS.copy()
    headers["Referer"] = referer or "https://www.soccer-rating.com/"
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response

def normalize_team_name(name: Any) -> str:
    """Robustly cleans and standardizes a team name for reliable matching.

    Args:
        name: Team name to normalize

    Returns:
        Normalized team name
    """
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = name.replace('ö', 'oe').replace('ü', 'ue').replace('ä', 'ae')
    name = name.replace('ø', 'oe').replace('å', 'aa').replace('æ', 'ae')
    name = re.sub(r'[\&\-\.]+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s\([ns]\)$', '', name)
    return ' '.join(name.split())

def safe_float(value: Any, default: float = 0.0) -> float:
    """Converts a value to float, handling percentage strings and errors.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Converted float value or default
    """
    try:
        if isinstance(value, str) and '%' in value:
            return float(value.replace('%', '')) / 100.0
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default

# --- Data Fetching and Parsing Functions ---

@st.cache_data(ttl=3600)
def fetch_table_data(
    country: str, league: str
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Fetches and parses ratings and league table in one go.

    Args:
        country: Country identifier
        league: League identifier

    Returns:
        Tuple of (home_rating_table, away_rating_table, league_table) or (None, None, None) on error
    """
    base_url = f"https://www.soccer-rating.com/{country}/{league}/"
    home_url = f"{base_url}home/"
    away_url = f"{base_url}away/"
    
    try:
        response_home = fetch_with_headers(home_url, referer=base_url)
        soup_home = BeautifulSoup(response_home.text, "lxml")

        response_away = fetch_with_headers(away_url, referer=base_url)
        soup_away = BeautifulSoup(response_away.text, "lxml")

        home_rating_table = None
        for table in soup_home.find_all('table', class_='rattab'):
            header = table.find('th')
            if header and "Home" in header.get_text():
                teams_data = []
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) == 5:
                        team_link = cols[1].find('a')
                        if team_link and team_link.has_attr('href'):
                            team_url = team_link['href']
                            name_from_url = team_url.split('/')[1].replace('-', ' ')
                            rating = float(cols[4].get_text(strip=True))
                            teams_data.append({"Team": name_from_url, "Rating": rating, "URL": team_url})
                home_rating_table = pd.DataFrame(teams_data)
                break
        
        away_rating_table = None
        for table in soup_away.find_all('table', class_='rattab'):
            header = table.find('th')
            if header and "Away" in header.get_text():
                teams_data = []
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) == 5:
                        team_link = cols[1].find('a')
                        if team_link and team_link.has_attr('href'):
                            team_url = team_link['href']
                            name_from_url = team_url.split('/')[1].replace('-', ' ')
                            rating = float(cols[4].get_text(strip=True))
                            teams_data.append({"Team": name_from_url, "Rating": rating, "URL": team_url})
                away_rating_table = pd.DataFrame(teams_data)
                break

        league_table = None
        all_html_tables = pd.read_html(io.StringIO(str(soup_home)), flavor="lxml")
        expected_columns = {"M", "P.", "Goals", "Home", "Away"}
        for candidate in all_html_tables:
            if expected_columns.issubset(set(candidate.columns.astype(str))):
                league_table = candidate
                break
        
        return home_rating_table, away_rating_table, league_table
    except Exception:
        return None, None, None

def find_section_header(soup: BeautifulSoup, header_text: str) -> Optional[Any]:
    """Finds a table header element by its text.

    Args:
        soup: BeautifulSoup object
        header_text: Text to search for in headers

    Returns:
        Header element or None
    """
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None

def get_correct_table(
    soup: BeautifulSoup,
    target_team_name: str,
    target_team_url: str,
    header_text: str,
    table_id_1: str,
    table_id_2: str,
) -> Optional[Any]:
    """Finds the correct data table using a hybrid URL-first, then name-fallback approach.

    Args:
        soup: BeautifulSoup object
        target_team_name: Name of the target team
        target_team_url: URL of the target team
        header_text: Text to search for in table header
        table_id_1: ID of the first table
        table_id_2: ID of the second table

    Returns:
        Table element or None
    """
    header = find_section_header(soup, header_text)
    if not header: return None 
    team_name_row = header.find_next('tr')
    if not team_name_row: return None
    team_links = team_name_row.find_all('a')
    normalized_target_url = target_team_url.strip('/')
    
    if len(team_links) >= 1 and team_links[0].has_attr('href'):
        href1 = team_links[0]['href']
        if not href1.startswith('javascript:'):
             if href1.strip('/') == normalized_target_url:
                return soup.find("table", id=table_id_1)
            
    if len(team_links) == 2 and team_links[1].has_attr('href'):
        href2 = team_links[1]['href']
        if not href2.startswith('javascript:'):
            if href2.strip('/') == normalized_target_url:
                return soup.find("table", id=table_id_2)

    normalized_target_name = normalize_team_name(target_team_name)
    if len(team_links) >= 1:
        header_team1_raw = team_links[0].get_text(strip=True)
        header_team1 = re.sub(r'\s*\([^)]*\)', '', header_team1_raw).strip()
        if normalize_team_name(header_team1) == normalized_target_name:
            return soup.find("table", id=table_id_1)
            
    if len(team_links) == 2:
        header_team2_raw = team_links[1].get_text(strip=True)
        header_team2 = re.sub(r'\s*\([^)]*\)', '', header_team2_raw).strip()
        if normalize_team_name(header_team2) == normalized_target_name:
            return soup.find("table", id=table_id_2)
    return None

@st.cache_data(ttl=3600)
def fetch_team_page_data(
    team_name: str, team_url: str
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """Fetches lineup, squad, and last matches from a single team page visit.

    Args:
        team_name: Name of the team
        team_url: URL path for the team

    Returns:
        Tuple of (lineup_data, squad_data, last_matches_data) or (None, None, None) on error
    """
    try:
        url = f"https://www.soccer-rating.com{team_url}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Parse Lineup
        lineup_table = get_correct_table(soup, team_name, team_url, 'Expected Lineup', 'line1', 'line2')
        lineup_data = []
        if lineup_table:
            for row in lineup_table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 4:
                    try:
                        player_div = cols[1].find("div", class_="nomobil")
                        if not player_div: continue
                        img_tag = player_div.find('img')
                        full_text = (img_tag.next_sibling.strip() if img_tag and img_tag.next_sibling else player_div.get_text(strip=True))
                        match = re.match(r'(.+?)\s*\((.+)\)', full_text)
                        name, pos = (match.group(1).strip(), match.group(2).strip()) if match else (full_text.strip(), "N/A")
                        stats = cols[2].get_text(strip=True)
                        rating = int(cols[3].get_text(strip=True))
                        lineup_data.append({"name": name, "position": pos, "stats": stats, "rating": rating})
                    except (ValueError, IndexError): continue
        
        # Parse Squad
        squad_table = get_correct_table(soup, team_name, team_url, 'Squad', 'squad1', 'squad2')
        squad_data = []
        if squad_table:
            for row in squad_table.find_all('tr'):
                if row.find('th') or row.find('hr'): continue
                cols = row.find_all('td')
                if len(cols) == 3:
                    try:
                        player_div = cols[0].find("div", class_="nomobil")
                        if not player_div: continue
                        img_tag = player_div.find('img')
                        full_text = (img_tag.next_sibling.strip() if img_tag and img_tag.next_sibling else player_div.get_text(strip=True))
                        match = re.match(r'(.+?)\s*\((\d+)\)', full_text)
                        name, age = (match.group(1).strip(), int(match.group(2))) if match else (full_text, "N/A")
                        rating = int(cols[2].get_text(strip=True))
                        squad_data.append({"name": name, "age": age, "rating": rating})
                    except (ValueError, IndexError): continue
        
        # Parse Last Matches
        last_matches_data, points, league_matches_count = [], 0, 0
        matches_table = soup.find('table', {'class': 'bigtable', 'cellspacing': '0'})
        if matches_table:
            for row in matches_table.find_all('tr'):
                if league_matches_count >= 5: break
                cols = row.find_all('td')
                if len(cols) > 9 and "cup" not in cols[7].get_text(strip=True).lower():
                    date = cols[1].get_text(strip=True, separator=" ").split(" ")[0]
                    opponent = cols[2].get_text(strip=True)
                    result = cols[10].get_text(strip=True)
                    if result:
                        last_matches_data.append({"date": date, "opponent": opponent, "result": result})
                        try:
                            own_score, opp_score = map(int, result.split(':'))
                            is_home_match = team_name.lower() in opponent.split('-')[0].lower()
                            if (is_home_match and own_score > opp_score) or (not is_home_match and own_score < opp_score):
                                points += 3
                            elif own_score == opp_score:
                                points += 1
                        except (ValueError, IndexError): pass
                        league_matches_count += 1

        return lineup_data, squad_data, {"matches": last_matches_data, "points": points}
    except Exception:
        return None, None, None

# --- Statistical & Odds Calculation Functions ---

def get_league_stats(country_key: str, league_code: str) -> Optional[Dict[str, Any]]:
    """Retrieves the stored stats for a given league using the mapping.

    Args:
        country_key: Country identifier
        league_code: League code

    Returns:
        Dictionary of league statistics or None
    """
    map_key = (country_key, league_code)
    league_name = config.LEAGUE_STATS_MAP.get(map_key)
    
    stats_data = load_league_stats()

    if league_name:
        normalized_league_name = normalize_league_key(league_name)
        stats = stats_data.get(normalized_league_name)
        if stats:
            # Add league name to the dict for display
            stats_processed = stats.copy()
            stats_processed["League"] = league_name
            return stats_processed
    
    # Fallback if no specific league map is found
    # Try to find the primary league for the country
    primary_league_code_key = next(iter(config.LEAGUES_DATA.get(country_key, {})), None)
    if primary_league_code_key:
        primary_league_code = config.LEAGUES_DATA[country_key][primary_league_code_key][0]
        map_key = (country_key, primary_league_code)
        league_name = config.LEAGUE_STATS_MAP.get(map_key)
        if league_name:
            normalized_league_name = normalize_league_key(league_name)
            stats = stats_data.get(normalized_league_name)
            if stats:
                stats_copy = stats.copy()
                stats_copy["League"] = league_name
                return stats_copy

    return None

def get_league_suggested_draw_rate(
    country_key: str, league_code: str, stats: Optional[Dict[str, Any]] = None
) -> float:
    """Analyzes the league table to suggest a realistic draw rate.

    Args:
        country_key: Country identifier
        league_code: League code
        stats: Pre-loaded league statistics (optional)

    Returns:
        Suggested draw probability
    """
    stats = stats or get_league_stats(country_key, league_code)
    if stats and 'Draw%' in stats:
        return safe_float(stats['Draw%'], config.DEFAULT_DRAW_RATE)

    return config.DEFAULT_DRAW_RATE


def get_league_average_goals(
    country_key: str, league_code: str, stats: Optional[Dict[str, Any]] = None
) -> float:
    """Return the league's average total goals per match for draw calibration.

    Args:
        country_key: Country identifier
        league_code: League code
        stats: Pre-loaded league statistics (optional)

    Returns:
        Average goals per match
    """
    stats = stats or get_league_stats(country_key, league_code)
    if stats and 'AvgGoals' in stats:
        return safe_float(stats['AvgGoals'], config.DEFAULT_AVG_GOALS)

    return config.DEFAULT_AVG_GOALS

def calculate_outcome_probabilities(
    home_rating: float,
    away_rating: float,
    base_draw_prob: float,
    avg_goals: float,
    draw_weight: float = config.DRAW_OBS_WEIGHT,
) -> Tuple[float, float, float]:
    """Calculate 1X2 probabilities via Bradley-Terry-Davidson anchored to league scoring.

    Args:
        home_rating: Home team Elo rating
        away_rating: Away team Elo rating
        base_draw_prob: Base draw probability from league statistics
        avg_goals: Average goals per match
        draw_weight: Weight for blending observed draw rate

    Returns:
        Tuple of (p_home, p_draw, p_away)
    """

    rating_diff = safe_float(home_rating, 0) - safe_float(away_rating, 0)
    strength_ratio = 10 ** (rating_diff / 400)

    # Adjust the league scoring environment by scaling the average goals with
    # the Elo rating gap before computing the Poisson draw probability.
    mu = max(safe_float(avg_goals, config.DEFAULT_AVG_GOALS), 0)
    rating_gap = abs(rating_diff)
    gap_ratio = rating_gap / config.ELO_GOAL_SCALE_DIVISOR if config.ELO_GOAL_SCALE_DIVISOR else 0
    goal_scale = 1 + min(gap_ratio * config.ELO_GOAL_SCALE_FACTOR, config.ELO_GOAL_SCALE_CAP)
    mu_adjusted = mu * goal_scale
    poisson_draw = math.exp(-mu_adjusted) * modified_bessel_i0(mu_adjusted)

    alpha = 0.0 if draw_weight is None else min(max(draw_weight, 0.0), 1.0)
    observed_draw = min(max(safe_float(base_draw_prob, config.DEFAULT_DRAW_RATE), 0.0), 0.95)
    blended_draw = poisson_draw if alpha == 0 else (
        alpha * observed_draw + (1 - alpha) * poisson_draw
    )
    blended_draw = min(max(blended_draw, 1e-6), 0.999999)

    nu = blended_draw / (1 - blended_draw)
    nu = max(nu * max(config.DRAW_RATE_SCALE, 1e-6), 0.0)

    denominator = strength_ratio + 1 + (2 * nu)
    if denominator == 0:
        return 0.0, 0.0, 0.0

    p_home = strength_ratio / denominator
    p_draw = (2 * nu) / denominator
    p_away = 1 / denominator

    total = p_home + p_draw + p_away
    if total == 0:
        return 0.0, 0.0, 0.0

    return p_home / total, p_draw / total, p_away / total


def apply_margin(probabilities: List[float], margin_percent: float) -> List[float]:
    """Applies a bookmaker's margin to a list of probabilities using proportional scaling.

    Args:
        probabilities: List of probabilities
        margin_percent: Margin percentage to apply

    Returns:
        List of odds with margin applied
    """
    if not probabilities or sum(probabilities) == 0:
        return [0.0] * len(probabilities)

    target_overround = 1 + (margin_percent / 100.0)
    
    # Handle potential edge case where probabilities don't sum to 1
    total_prob = sum(probabilities)
    normalized_probs = [p / total_prob for p in probabilities]

    # Standard method: p_i' = p_i * target_overround
    # This scales the sum of probabilities to the target overround.
    adjusted_probs = [p * target_overround for p in normalized_probs]
    
    # Odds are the inverse of these adjusted probabilities
    return [1 / p if p > 0 else 0 for p in adjusted_probs]


# --- UI Display Functions ---

def display_league_stats(stats_row: Optional[Dict[str, Any]]) -> None:
    """Renders the soccerstats data in a compact, multi-column format.

    Args:
        stats_row: Dictionary containing league statistics
    """
    if stats_row is None:
        st.info("Detailed league stats from SoccerStats.com are not available for this selection.")
        return
    
    league_name = stats_row.get('League', 'Selected League')
    gp = int(stats_row.get('GP', 0))
    st.markdown(f"##### {league_name} (GP: {gp})")
    
    # Row 1: Win/Draw/Loss
    c1, c2, c3 = st.columns(3)
    c1.metric("Home Win", f"{stats_row.get('HomeW%', 0):.1%}")
    c2.metric("Draw", f"{stats_row.get('Draw%', 0):.1%}")
    c3.metric("Away Win", f"{stats_row.get('AwayW%', 0):.1%}")

    # Row 2: Goal Averages
    c4, c5, c6 = st.columns(3)
    c4.metric("Avg Goals", f"{stats_row.get('AvgGoals', 0):.2f}")
    c5.metric("Avg HG", f"{stats_row.get('AvgHG', 0):.2f}")
    c6.metric("Avg AG", f"{stats_row.get('AvgAG', 0):.2f}")

def display_team_stats(team_name: str, table: pd.DataFrame, column: Any) -> None:
    """Displays key stats for a single team from the league table.

    Args:
        team_name: Name of the team
        table: DataFrame containing league table
        column: Streamlit column to display in
    """
    try:
        normalized_target = normalize_team_name(team_name)
        
        # Check if 'normalized_name' column already exists
        if 'normalized_name' not in table.columns:
            table['normalized_name'] = table.iloc[:, 1].apply(normalize_team_name)
            
        team_stats_row = table[table['normalized_name'] == normalized_target]
        
        if team_stats_row.empty:
            column.warning(f"Stats unavailable for {team_name}.")
            return

        team_stats = team_stats_row.iloc[0]
        column.markdown(f"**{team_name}**")
        
        # Handle potential errors if columns are missing
        pos_value = f"#{int(team_stats.iloc[0])}" if pd.notna(team_stats.iloc[0]) else "N/A"
        column.metric(label="League Position", value=pos_value)
        
        if 'M' in team_stats and 'P.' in team_stats and pd.notna(team_stats['M']) and pd.notna(team_stats['P.']):
            matches, points = int(team_stats['M']), int(team_stats['P.'])
        else:
            matches, points = 0, 0

        if 'Goals' in team_stats and ':' in str(team_stats['Goals']):
            gf, ga = map(int, team_stats['Goals'].split(':'))
            if matches > 0:
                column.metric(label="Avg. Goals Scored", value=f"{gf/matches:.2f}")
                column.metric(label="Avg. Goals Conceded", value=f"{ga/matches:.2f}")
            else:
                column.metric(label="Goals For", value=f"{gf}")
                column.metric(label="Goals Against", value=f"{ga}")
        else:
            column.info("Goal data not available.")
            
    except (IndexError, ValueError, KeyError, TypeError) as e:
        st.error(f"Error displaying stats for {team_name}: {e}")
        column.warning(f"Stats unavailable for {team_name}.")

def display_interactive_lineup(team_name: str, team_key: str) -> Tuple[float, int]:
    """Displays an interactive checklist of the team's lineup.

    Args:
        team_name: Name of the team
        team_key: Session state key for lineup data

    Returns:
        Tuple of (average_rating, number_of_starters)
    """
    st.subheader(f"{team_name}")
    lineup_data = st.session_state.get(team_key)
    if not lineup_data:
        st.warning("Lineup data not available.")
        return 0.0, 0
    
    header_cols = st.columns([1, 4, 2, 2, 2])
    header_cols[0].markdown('<p class="player-table-header">On</p>', unsafe_allow_html=True)
    header_cols[1].markdown('<p class="player-table-header">Player</p>', unsafe_allow_html=True)
    header_cols[2].markdown('<p class="player-table-header">Pos</p>', unsafe_allow_html=True)
    header_cols[3].markdown('<p class="player-table-header">Stats</p>', unsafe_allow_html=True)
    header_cols[4].markdown('<p class="player-table-header">Rating</p>', unsafe_allow_html=True)

    selected_starters = []
    for i, p in enumerate(lineup_data):
        player_cols = st.columns([1, 4, 2, 2, 2])
        is_starter = (i < 11) # Default to top 11 as starters
        if player_cols[0].checkbox("", value=is_starter, key=f"check_{team_key}_{i}", label_visibility="collapsed"):
            selected_starters.append(p)
        player_cols[1].write(p['name'])
        player_cols[2].write(p['position'])
        player_cols[3].write(p['stats'])
        player_cols[4].write(f"**{p['rating']}**")
    
    if selected_starters:
        avg_rating = sum(p['rating'] for p in selected_starters) / len(selected_starters)
        st.metric(f"Avg. Starter Rating", f"{avg_rating:.2f}")
        return avg_rating, len(selected_starters)
    else:
        st.metric(f"Avg. Starter Rating", "N/A")
        return 0, 0

def display_squad(team_name: str, squad_key: str, lineup_key: str) -> None:
    """Displays the full squad, highlighting starters.

    Args:
        team_name: Name of the team
        squad_key: Session state key for squad data
        lineup_key: Session state key for lineup data
    """
    st.subheader(f"{team_name}")
    squad_data = st.session_state.get(squad_key)
    if not squad_data:
        st.warning("Squad data not available.")
        return

    starter_names = {p['name'] for p in st.session_state.get(lineup_key, [])[:11]}
    
    header_cols = st.columns([4, 2, 2])
    header_cols[0].markdown('<p class="player-table-header">Player</p>', unsafe_allow_html=True)
    header_cols[1].markdown('<p class="player-table-header">Age</p>', unsafe_allow_html=True)
    header_cols[2].markdown('<p class="player-table-header">Rating</p>', unsafe_allow_html=True)
    
    for p in squad_data:
        player_cols = st.columns([4, 2, 2])
        player_cols[0].write(f"**{p['name']}**" if p['name'] in starter_names else p['name'])
        player_cols[1].write(str(p['age']))
        player_cols[2].write(f"**{p['rating']}**")

def display_last_matches(team_name: str, matches_key: str) -> None:
    """Displays the last 5 league matches for a team.

    Args:
        team_name: Name of the team
        matches_key: Session state key for matches data
    """
    st.subheader(f"{team_name}")
    matches_data = st.session_state.get(matches_key)
    if not matches_data or not matches_data["matches"]:
        st.warning("Recent match data not available.")
        return
        
    st.metric("Points in Last 5 League Matches", matches_data["points"])
    for match in matches_data["matches"]:
        match_date = html.escape(match['date'])
        opponent = html.escape(match['opponent'])
        result = html.escape(match['result'])
        st.markdown(
            f"<div class='match-line'>"
            f"<span class='match-date'>{match_date}</span>"
            f"<span class='match-opponent'>{opponent}</span>"
            f"<span class='match-result'>{result}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

# --- Main Application ---

load_css("style.css")

st.markdown(
    """
    <div class="header">⚽ Elo Ratings Odds Studio</div>
    <div class="subheader">Track live ratings, surface the sharpest prices, and dive into form in one polished workspace.</div>
    """,
    unsafe_allow_html=True
)

with st.sidebar.expander("✨ Quick Guide", expanded=True):
    st.markdown(
        """
        - Select a **country + league** to pull the freshest ratings snapshot.
        - Use the **Single Match** tab to compare clubs, lineups, and value zones.
        - Use the **Multi-Match** tab to see odds for all league fixtures.
        """
    )

st.sidebar.header("🎯 Build Your Matchup")

# --- Session State Initialization ---
if 'data_fetched' not in st.session_state: st.session_state['data_fetched'] = False
if 'current_selection' not in st.session_state: st.session_state['current_selection'] = None

def fetch_data_for_selection(country: str, league: str) -> None:
    """Callback to fetch all data for a newly selected league.

    Args:
        country: Country identifier
        league: League code
    """
    current_selection = f"{country}_{league}"
    if st.session_state.get('current_selection') != current_selection or not st.session_state.get('data_fetched', False):
        st.session_state['current_selection'] = current_selection
        with st.spinner(random.choice(config.SPINNER_MESSAGES)):
            home_table, away_table, league_table = fetch_table_data(country, league)
            
            if isinstance(home_table, pd.DataFrame) and not home_table.empty:
                st.session_state.update({
                    "home_table": home_table,
                    "away_table": away_table,
                    "league_table": league_table,
                    "data_fetched": True,
                    "last_refresh": time.time()
                })
                # Clear old team-specific data
                for key in ['home_lineup', 'away_lineup', 'home_squad', 'away_squad', 
                           'home_matches', 'away_matches', 'last_home_team', 'last_away_team']: 
                    st.session_state.pop(key, None)
                st.success(f"✅ Loaded {country} - {league}")
            else:
                st.session_state['data_fetched'] = False
                st.error(f"❌ Failed to load data for {country} - {league}")

# --- Sidebar Controls ---
selected_country = st.sidebar.selectbox("Select Country/League Type:", sorted_countries, key="country_select")
league_list = all_leagues[selected_country]
selected_league = st.sidebar.selectbox("Select League:", league_list, key="league_select")

# Fetch data on selection change
fetch_data_for_selection(selected_country, selected_league)


# --- Main Content Area ---
if st.session_state.get('data_fetched', False):
    home_table = st.session_state.home_table
    away_table = st.session_state.away_table
    team_list = sorted(home_table["Team"].unique())

    league_stats = get_league_stats(selected_country, selected_league)
    league_avg_draw = get_league_suggested_draw_rate(selected_country, selected_league, stats=league_stats)
    league_avg_goals = get_league_average_goals(selected_country, selected_league, stats=league_stats)

    last_refresh = st.session_state.get("last_refresh")
    refresh_text = datetime.utcfromtimestamp(last_refresh).strftime("%d %b %Y %H:%M UTC") if last_refresh else "Awaiting refresh"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{html.escape(selected_country)} · {html.escape(selected_league)}</div>
            <div class="hero-subtitle">Explore the live blend of Elo strength and statistical context.</div>
            <div class="hero-meta">
                <span class="hero-pill">Teams loaded: {len(team_list)}</span>
                <span class="hero-pill">Last synced: {refresh_text}</span>
                <span class="hero-pill">Interactive odds modelling</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Main Tabs ---
    tab1, tab2 = st.tabs(["Single Match Analysis", "Multi-Match Calculator"])

    with tab1:
        with st.expander("📈 League-Wide Stats", expanded=True):
            display_league_stats(league_stats)

        with st.expander("⚽ Select Matchup", expanded=True):
            col1, col2 = st.columns(2)
            
            # Use index 0 and 1 as defaults, or handle short lists
            default_home_index = 0
            default_away_index = min(1, len(team_list) - 1)

            home_team_name = col1.selectbox("Select Home Team:", team_list, index=default_home_index, key="home_team_select")
            away_team_name = col2.selectbox("Select Away Team:", team_list, index=default_away_index, key="away_team_select")
            
            home_team_data = home_table[home_table["Team"] == home_team_name].iloc[0]
            away_team_data = away_table[away_table["Team"] == away_team_name].iloc[0]

        # --- Team-Specific Data Fetching ---
        home_needs_fetch = 'last_home_team' not in st.session_state or st.session_state.last_home_team != home_team_name
        away_needs_fetch = 'last_away_team' not in st.session_state or st.session_state.last_away_team != away_team_name

        if home_needs_fetch or away_needs_fetch:
            with st.spinner("Fetching team data..."):
                if home_needs_fetch:
                    lineup, squad, matches = fetch_team_page_data(home_team_name, home_team_data['URL'])
                    st.session_state.update({'home_lineup': lineup, 'home_squad': squad, 'home_matches': matches, 'last_home_team': home_team_name})
                
                if away_needs_fetch:
                    lineup, squad, matches = fetch_team_page_data(away_team_name, away_team_data['URL'])
                    st.session_state.update({'away_lineup': lineup, 'away_squad': squad, 'away_matches': matches, 'last_away_team': away_team_name})
            st.rerun()

        # --- Analysis Expanders ---
        with st.expander("📊 Team Statistics", expanded=False):
            league_table = st.session_state.get("league_table")
            if isinstance(league_table, pd.DataFrame):
                stat_col1, stat_col2 = st.columns(2)
                display_team_stats(home_team_name, league_table, stat_col1)
                display_team_stats(away_team_name, league_table, stat_col2)
            else:
                st.warning("League table not available for detailed statistics.")

        with st.expander("📈 Odds Analysis (Inputs)", expanded=True):
            home_rating, away_rating = home_team_data['Rating'], away_team_data['Rating']
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{home_team_name} Rating", f"{home_rating:.2f}")
            c2.metric(f"{away_team_name} Rating", f"{away_rating:.2f}")
            c3.metric("League Avg. Draw", f"{league_avg_draw:.1%}")

            st.markdown("---")
            margin = st.slider("Apply Bookmaker's Margin (%):", 0.0, 15.0, 5.0, 0.5, format="%.1f%%", key="single_margin")

        # --- Calculations for Single Match ---
        p_home, p_draw, p_away = calculate_outcome_probabilities(
            home_rating,
            away_rating,
            league_avg_draw,
            league_avg_goals,
        )

        p_dnb_home = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0.5
        p_dnb_away = 1 - p_dnb_home
        min_prob = 1e-6
        fair_dnb_home_odds = 1 / max(p_dnb_home, min_prob)
        fair_dnb_away_odds = 1 / max(p_dnb_away, min_prob)

        poisson_markets = calculate_poisson_markets_from_dnb(
            fair_dnb_home_odds,
            fair_dnb_away_odds,
            league_avg_goals,
        )

        poisson_probs = poisson_markets["probabilities"]

        # Apply margin for 1x2 odds based on Poisson probabilities
        odds_1x2 = apply_margin(
            [poisson_probs["home"], poisson_probs["draw"], poisson_probs["away"]],
            margin,
        )
        h_odds, d_odds, a_odds = odds_1x2[0], odds_1x2[1], odds_1x2[2]

        # Apply margin for DNB odds using Elo-derived strengths
        odds_dnb = apply_margin([p_dnb_home, p_dnb_away], margin)
        dnb_h_odds, dnb_a_odds = odds_dnb[0], odds_dnb[1]

        ou_probs = poisson_markets["over_under"]
        ou_odds = apply_margin(
            [ou_probs["over25_prob"], ou_probs["under25_prob"]],
            margin,
        )
        over25_odds, under25_odds = ou_odds[0], ou_odds[1]

        btts_probs = poisson_markets["btts"]
        btts_odds = apply_margin(
            [btts_probs["yes_prob"], btts_probs["no_prob"]],
            margin,
        )
        btts_yes_odds, btts_no_odds = btts_odds[0], btts_odds[1]

        with st.expander("🎯 Calculated Odds", expanded=True):
            st.markdown("**Adjusted Expected Goals**")
            xg_cols = st.columns(3)
            xg_cols[0].metric("Total xG", f"{poisson_markets['lambda_total']:.2f}")
            xg_cols[1].metric(f"{home_team_name} xG", f"{poisson_markets['xg_home']:.2f}")
            xg_cols[2].metric(f"{away_team_name} xG", f"{poisson_markets['xg_away']:.2f}")

            st.markdown("---")
            st.markdown("**Poisson-Derived Fair Probabilities**")
            prob_cols = st.columns(3)
            prob_cols[0].metric("Home Win", f"{poisson_probs['home']:.2%}")
            prob_cols[1].metric("Draw", f"{poisson_probs['draw']:.2%}")
            prob_cols[2].metric("Away Win", f"{poisson_probs['away']:.2%}")

            st.markdown("---")
            st.write(f"**Calculated Odds with {margin:.1f}% Margin:**")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='card'><div class='card-title'>Home (1)</div><div class='card-value'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-value'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='card'><div class='card-title'>Away (2)</div><div class='card-value'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)

            st.markdown("---")
            st.write("**Draw No Bet Odds:**")
            dnb_c1, dnb_c2 = st.columns(2)
            dnb_c1.markdown(f"<div class='card'><div class='card-title'>Home (DNB)</div><div class='card-value'>{dnb_h_odds:.2f}</div></div>", unsafe_allow_html=True)
            dnb_c2.markdown(f"<div class='card'><div class='card-title'>Away (DNB)</div><div class='card-value'>{dnb_a_odds:.2f}</div></div>", unsafe_allow_html=True)

            st.markdown("---")
            st.write("**Over/Under 2.5 Goals:**")
            ou_cols = st.columns(2)
            ou_cols[0].metric("Over 2.5 (Prob)", f"{ou_probs['over25_prob']:.2%}", help="Fair probability from Poisson model")
            ou_cols[1].metric("Under 2.5 (Prob)", f"{ou_probs['under25_prob']:.2%}", help="Fair probability from Poisson model")
            ou_card_cols = st.columns(2)
            ou_card_cols[0].markdown(f"<div class='card'><div class='card-title'>Over 2.5</div><div class='card-value'>{over25_odds:.2f}</div></div>", unsafe_allow_html=True)
            ou_card_cols[1].markdown(f"<div class='card'><div class='card-title'>Under 2.5</div><div class='card-value'>{under25_odds:.2f}</div></div>", unsafe_allow_html=True)

            st.markdown("---")
            st.write("**Both Teams to Score:**")
            btts_cols = st.columns(2)
            btts_cols[0].metric("BTTS - Yes (Prob)", f"{btts_probs['yes_prob']:.2%}", help="Fair probability from Poisson model")
            btts_cols[1].metric("BTTS - No (Prob)", f"{btts_probs['no_prob']:.2%}", help="Fair probability from Poisson model")
            btts_card_cols = st.columns(2)
            btts_card_cols[0].markdown(f"<div class='card'><div class='card-title'>BTTS - Yes</div><div class='card-value'>{btts_yes_odds:.2f}</div></div>", unsafe_allow_html=True)
            btts_card_cols[1].markdown(f"<div class='card'><div class='card-title'>BTTS - No</div><div class='card-value'>{btts_no_odds:.2f}</div></div>", unsafe_allow_html=True)

        # --- Bookmaker Odds Comparison & EV ---
        with st.expander("💰 Bookmaker Odds & Expected Value (EV)", expanded=True):
            st.markdown("**Live Bookmaker Odds from Kambi**")

            # Try to fetch odds from Kambi
            kambi = get_kambi_client()

            with st.spinner("Fetching live bookmaker odds..."):
                kambi_match = kambi.find_match(
                    home_team_name,
                    away_team_name,
                    league=selected_league
                )

            if kambi_match and kambi_match.has_odds:
                # Display bookmaker info
                st.success(f"✓ Found live odds for {kambi_match.home_team} vs {kambi_match.away_team}")

                info_cols = st.columns(3)
                info_cols[0].metric("League", kambi_match.league)
                info_cols[1].metric("Kickoff", kambi_match.start_time.strftime("%d %b %H:%M UTC"))
                info_cols[2].metric("Bookmaker Margin", f"{kambi_match.bookmaker_margin:.2f}%")

                st.markdown("---")

                # Prepare data for EV analysis
                elo_probs = {
                    'home': poisson_probs['home'],
                    'draw': poisson_probs['draw'],
                    'away': poisson_probs['away']
                }

                bookmaker_odds_dict = {
                    'home': kambi_match.odds_home,
                    'draw': kambi_match.odds_draw,
                    'away': kambi_match.odds_away
                }

                # Calculate EV
                ev_analysis = analyze_match_ev(elo_probs, bookmaker_odds_dict)

                # Display comparison table
                st.markdown("**Odds Comparison & Expected Value**")

                comparison_data = {
                    'Outcome': ['Home (1)', 'Draw (X)', 'Away (2)'],
                    'Elo Prob': [f"{elo_probs['home']:.2%}", f"{elo_probs['draw']:.2%}", f"{elo_probs['away']:.2%}"],
                    'Elo Fair Odds': [f"{1/elo_probs['home']:.2f}", f"{1/elo_probs['draw']:.2f}", f"{1/elo_probs['away']:.2f}"],
                    'Bookmaker Odds': [f"{kambi_match.odds_home:.2f}", f"{kambi_match.odds_draw:.2f}", f"{kambi_match.odds_away:.2f}"],
                    'Implied Prob': [f"{ev_analysis.home_ev.implied_probability:.2%}", f"{ev_analysis.draw_ev.implied_probability:.2%}", f"{ev_analysis.away_ev.implied_probability:.2%}"],
                    'Expected Value': [ev_analysis.home_ev.ev_percentage_str, ev_analysis.draw_ev.ev_percentage_str, ev_analysis.away_ev.ev_percentage_str],
                }

                comparison_df = pd.DataFrame(comparison_data)

                # Style the dataframe with color coding
                def highlight_ev(row):
                    ev_str = row['Expected Value']
                    ev_val = float(ev_str.replace('%', '').replace('+', '')) / 100

                    if ev_val > 0.05:  # >5% EV
                        color = '#90EE90'  # Light green
                    elif ev_val > 0:  # Positive but small
                        color = '#FFFFE0'  # Light yellow
                    elif ev_val < -0.05:  # Bad value
                        color = '#FFB6C6'  # Light red
                    else:
                        color = ''

                    return [f'background-color: {color}' if color else '' for _ in row]

                st.dataframe(
                    comparison_df.style.apply(highlight_ev, axis=1),
                    hide_index=True,
                    use_container_width=True
                )

                st.markdown("---")

                # Highlight best value bet
                if ev_analysis.has_any_value:
                    best = ev_analysis.best_value
                    st.success(f"🎯 **Best Value Bet:** {best.outcome.upper()} @ {best.bookmaker_odds:.2f} (EV: {best.ev_percentage_str}, Edge: {best.edge_percentage_str})")

                    # Kelly Criterion suggestion
                    kelly_full = kelly_criterion(best.true_probability, best.bookmaker_odds, fraction=1.0)
                    kelly_quarter = kelly_criterion(best.true_probability, best.bookmaker_odds, fraction=0.25)
                    kelly_half = kelly_criterion(best.true_probability, best.bookmaker_odds, fraction=0.5)

                    st.info(f"**Kelly Criterion Staking:**\n\n"
                            f"• Full Kelly: {kelly_full:.2%} of bankroll\n\n"
                            f"• Half Kelly: {kelly_half:.2%} of bankroll (moderate)\n\n"
                            f"• Quarter Kelly: {kelly_quarter:.2%} of bankroll (conservative)")
                else:
                    st.warning("⚠️ No positive expected value found on any outcome.")

                # Color legend
                st.markdown("---")
                st.caption("🟢 Green: Strong value (EV > 5%) | 🟡 Yellow: Slight value (0% < EV < 5%) | 🔴 Red: Poor value (EV < -5%)")

            elif kambi_match and not kambi_match.has_odds:
                st.warning(f"⚠️ Match found but odds not available yet for {kambi_match.home_team} vs {kambi_match.away_team}")
            else:
                st.info("ℹ️ Match not found in Kambi. This could mean:\n"
                        "- The match hasn't been listed yet\n"
                        "- Team names don't match exactly\n"
                        "- League not covered by Kambi\n\n"
                        "**Manual Odds Input** (coming soon)")

        with st.expander("📋 Interactive Lineups", expanded=True):
            col1, col2 = st.columns(2)
            with col1: 
                avg_home_rating, home_starters = display_interactive_lineup(f"{home_team_name} (Home)", "home_lineup")
            with col2: 
                avg_away_rating, away_starters = display_interactive_lineup(f"{away_team_name} (Away)", "away_lineup")

        with st.expander("👥 Full Squads", expanded=False):
            squad_col1, squad_col2 = st.columns(2)
            with squad_col1: display_squad(f"{home_team_name} (Home)", "home_squad", "home_lineup")
            with squad_col2: display_squad(f"{away_team_name} (Away)", "away_squad", "away_lineup")

        with st.expander("📅 Last 5 League Matches", expanded=False):
            match_col1, match_col2 = st.columns(2)
            with match_col1: display_last_matches(f"{home_team_name} (Home)", "home_matches")
            with match_col2: display_last_matches(f"{away_team_name} (Away)", "away_matches")

    with tab2:
        with st.expander("📈 League-Wide Stats", expanded=True):
            display_league_stats(league_stats)

        st.subheader("💰 Upcoming Matches - Value Bet Scanner")
        st.caption("Automatically fetches upcoming matches from Kambi and identifies value betting opportunities")

        # Settings
        col_settings1, col_settings2 = st.columns(2)
        with col_settings1:
            min_ev_filter = st.slider("Show matches with EV above:", -20.0, 20.0, 0.0, 1.0, format="%.1f%%", key="min_ev_filter")
        with col_settings2:
            include_live = st.checkbox("Include live matches", value=False, key="include_live_multi")

        st.markdown("---")

        # Fetch matches from Kambi
        kambi = get_kambi_client()

        with st.spinner(f"🔍 Fetching upcoming matches for {selected_league}..."):
            # Try to fetch matches by league first
            kambi_matches = kambi.get_matches_by_league(
                selected_country,
                selected_league,
                include_live=include_live
            )

            # If no matches found, try getting all matches and filter
            if not kambi_matches:
                all_matches = kambi.get_all_football_matches(include_live=include_live)
                # Filter by league/country
                kambi_matches = [
                    m for m in all_matches
                    if normalize_league_key(m.league) == normalize_league_key(selected_league) or
                       normalize_league_key(m.country) == normalize_league_key(selected_country)
                ]

        if not kambi_matches:
            st.warning(f"⚠️ No upcoming matches found in Kambi for {selected_country} - {selected_league}")
            st.info("This could mean:\n"
                    "- No matches scheduled in the near future\n"
                    "- League name doesn't match Kambi's naming\n"
                    "- League not covered by Kambi\n\n"
                    "Try selecting a different league or check back closer to match time.")
        else:
            st.success(f"✓ Found {len(kambi_matches)} upcoming match(es)")

            # Process each match
            match_data_list = []

            for kambi_match in kambi_matches:
                # Skip matches without odds
                if not kambi_match.has_odds:
                    continue

                try:
                    # Find matching teams in Elo ratings
                    # Try fuzzy matching with team names
                    home_match = None
                    away_match = None

                    for _, team_row in home_table.iterrows():
                        team_name = team_row['Team']
                        if normalize_team_name(team_name) == normalize_team_name(kambi_match.home_team):
                            home_match = team_row
                            break

                    for _, team_row in away_table.iterrows():
                        team_name = team_row['Team']
                        if normalize_team_name(team_name) == normalize_team_name(kambi_match.away_team):
                            away_match = team_row
                            break

                    # Skip if we can't find Elo ratings
                    if home_match is None or away_match is None:
                        continue

                    home_rating = home_match['Rating']
                    away_rating = away_match['Rating']

                    # Calculate Elo probabilities
                    p_h, p_draw, p_a = calculate_outcome_probabilities(
                        home_rating,
                        away_rating,
                        league_avg_draw,
                        league_avg_goals,
                    )

                    p_dnb_home = p_h / (p_h + p_a) if (p_h + p_a) > 0 else 0.5
                    p_dnb_away = 1 - p_dnb_home
                    min_prob = 1e-6
                    fair_dnb_home = 1 / max(p_dnb_home, min_prob)
                    fair_dnb_away = 1 / max(p_dnb_away, min_prob)

                    poisson_markets = calculate_poisson_markets_from_dnb(
                        fair_dnb_home,
                        fair_dnb_away,
                        league_avg_goals,
                    )
                    poisson_probs = poisson_markets["probabilities"]

                    # Calculate EV
                    elo_probs = {
                        'home': poisson_probs['home'],
                        'draw': poisson_probs['draw'],
                        'away': poisson_probs['away']
                    }

                    bookmaker_odds_dict = {
                        'home': kambi_match.odds_home,
                        'draw': kambi_match.odds_draw,
                        'away': kambi_match.odds_away
                    }

                    ev_analysis = analyze_match_ev(elo_probs, bookmaker_odds_dict)

                    # Get best EV value (could be negative)
                    best_ev_value = max(
                        ev_analysis.home_ev.expected_value,
                        ev_analysis.draw_ev.expected_value,
                        ev_analysis.away_ev.expected_value
                    )

                    # Apply filter
                    if best_ev_value * 100 < min_ev_filter:
                        continue

                    # Store match data
                    match_data_list.append({
                        'match': kambi_match,
                        'elo_probs': elo_probs,
                        'ev_analysis': ev_analysis,
                        'best_ev': best_ev_value
                    })

                except Exception as e:
                    logger.warning(f"Failed to process match {kambi_match.home_team} vs {kambi_match.away_team}: {e}")
                    continue

            if not match_data_list:
                st.info(f"No matches found with EV above {min_ev_filter:.1f}%. Try lowering the EV filter.")
            else:
                # Sort by best EV descending
                match_data_list.sort(key=lambda x: x['best_ev'], reverse=True)

                st.write(f"**Showing {len(match_data_list)} match(es) with value betting opportunities:**")
                st.markdown("---")

                # Display each match
                for match_data in match_data_list:
                    kambi_match = match_data['match']
                    elo_probs = match_data['elo_probs']
                    ev_analysis = match_data['ev_analysis']

                    # Determine best value outcome
                    if ev_analysis.has_any_value:
                        best = ev_analysis.best_value
                        value_indicator = f"🎯 **Best Value: {best.outcome.upper()} @ {best.bookmaker_odds:.2f} (EV: {best.ev_percentage_str})**"
                    else:
                        value_indicator = "No positive EV found"

                    # Match header
                    with st.container():
                        col_header1, col_header2, col_header3 = st.columns([3, 2, 2])

                        with col_header1:
                            st.markdown(f"### {kambi_match.home_team} vs {kambi_match.away_team}")
                        with col_header2:
                            st.caption(f"⏰ {kambi_match.start_time.strftime('%d %b, %H:%M UTC')}")
                        with col_header3:
                            if ev_analysis.has_any_value and ev_analysis.best_value.expected_value > 0.05:
                                st.success(value_indicator)
                            elif ev_analysis.has_any_value:
                                st.info(value_indicator)
                            else:
                                st.caption(value_indicator)

                        # Comparison table
                        comparison_data = {
                            'Outcome': ['Home (1)', 'Draw (X)', 'Away (2)'],
                            'Elo Prob': [
                                f"{elo_probs['home']:.1%}",
                                f"{elo_probs['draw']:.1%}",
                                f"{elo_probs['away']:.1%}"
                            ],
                            'Elo Odds': [
                                f"{1/elo_probs['home']:.2f}",
                                f"{1/elo_probs['draw']:.2f}",
                                f"{1/elo_probs['away']:.2f}"
                            ],
                            'Kambi Odds': [
                                f"{kambi_match.odds_home:.2f}",
                                f"{kambi_match.odds_draw:.2f}",
                                f"{kambi_match.odds_away:.2f}"
                            ],
                            'EV': [
                                ev_analysis.home_ev.ev_percentage_str,
                                ev_analysis.draw_ev.ev_percentage_str,
                                ev_analysis.away_ev.ev_percentage_str
                            ]
                        }

                        comparison_df = pd.DataFrame(comparison_data)

                        # Style with color coding
                        def highlight_ev_multi(row):
                            ev_str = row['EV']
                            ev_val = float(ev_str.replace('%', '').replace('+', '')) / 100

                            if ev_val > 0.05:  # >5% EV
                                color = '#90EE90'  # Light green
                            elif ev_val > 0:  # Positive but small
                                color = '#FFFFE0'  # Light yellow
                            elif ev_val < -0.05:  # Bad value
                                color = '#FFB6C6'  # Light red
                            else:
                                color = ''

                            return [f'background-color: {color}' if color else '' for _ in row]

                        st.dataframe(
                            comparison_df.style.apply(highlight_ev_multi, axis=1),
                            hide_index=True,
                            use_container_width=True
                        )

                        # Kelly Criterion for best bet
                        if ev_analysis.has_any_value and ev_analysis.best_value.expected_value > 0:
                            best = ev_analysis.best_value
                            kelly_quarter = kelly_criterion(best.true_probability, best.bookmaker_odds, fraction=0.25)
                            kelly_half = kelly_criterion(best.true_probability, best.bookmaker_odds, fraction=0.5)

                            st.caption(f"💰 **Suggested Stakes:** Quarter Kelly: {kelly_quarter:.2%} | Half Kelly: {kelly_half:.2%}")

                        st.markdown("---")


else:
    st.info("Please select a country and league in the sidebar to begin.")
