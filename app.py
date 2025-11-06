import html
import io
import logging
import random
import re
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import numpy as np
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

# Set page title and icon
st.set_page_config(page_title="Elo Ratings Odds Calculator", page_icon="odds_icon.png")

BASE_URL = "https://www.soccer-rating.com/"
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

_session = requests.Session()
_retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=_retries))


def build_league_urls(country: str, league: str) -> dict:
    """Return normalized URLs for a league including home/away views."""
    normalized = f"{country.strip('/')}/{league.strip('/')}/"
    base_url = urljoin(BASE_URL, normalized)
    return {
        "base": base_url,
        "home": urljoin(base_url, "home/"),
        "away": urljoin(base_url, "away/"),
    }


def build_team_url(team_path: str) -> str:
    """Return an absolute team URL relative to the base site."""
    team_path = team_path.lstrip('/')
    return urljoin(BASE_URL, team_path)


def fetch_soup(url: str, referer: Optional[str] = None, timeout: int = 15) -> BeautifulSoup:
    """Fetch a URL using the shared session and return a BeautifulSoup parser."""
    headers = BASE_HEADERS.copy()
    headers["Referer"] = referer or BASE_URL
    response = _session.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def fetch_league_soup(country: str, league: str, view: str = "base") -> BeautifulSoup:
    """Fetch and parse a league page view (base/home/away)."""
    urls = build_league_urls(country, league)
    target_url = urls.get(view, urls["base"])
    referer = urls["base"] if view != "base" else BASE_URL
    return fetch_soup(target_url, referer=referer)


def fetch_team_soup(team_path: str) -> BeautifulSoup:
    """Fetch and parse a team page."""
    url = build_team_url(team_path)
    return fetch_soup(url)

# Combined dictionary for both Men's and Women's leagues
leagues_data = {
    "Men's": {
        "England": ["UK1", "UK2", "UK3", "UK4", "UK5", "UK6N", "UK6S", "UK7N"],
        "Germany": ["DE1", "DE2", "DE3", "DE4SW", "DE4W", "DE4N", "DE4NO", "DE4B"],
        "Italy": ["IT1", "IT2", "IT3C", "IT3B", "IT3A"],
        "Spain": ["ES1", "ES2", "ES3G1", "ES3G2", "ES3G3", "ES3G4", "ES3G5"],
        "France": ["FR1", "FR2", "FR3"],
        "Sweden": ["SW1", "SW2", "SW3S", "SW3N"],
        "Netherlands": ["NL1", "NL2", "NL3"],
        "Russia": ["RU1", "RU2"],
        "Portugal": ["PT1", "PT2"],
        "Austria": ["AT1", "AT2", "AT3O", "AT3T", "AT3M", "AT3W", "AT3V"],
        "Denmark": ["DK1", "DK2", "DK3", "DK4"],
        "Greece": ["GR1", "GR2"],
        "Norway": ["NO1", "NO2", "NO3G1", "NO3G2"],
        "Czech Republic": ["CZ1", "CZ2"],
        "Turkey": ["TU1", "TU2", "TU3B", "TU3K"],
        "Belgium": ["BE1", "BE2"],
        "Scotland": ["SC1", "SC2", "SC3", "SC4"],
        "Switzerland": ["CH1", "CH2"],
        "Finland": ["FI1", "FI2", "FI3A", "FI3B", "FI3C"],
        "Ukraine": ["UA1", "UA2"],
        "Romania": ["RO1", "RO2"],
        "Poland": ["PL1", "PL2", "PL3"],
        "Croatia": ["HR1", "HR2"],
        "Belarus": ["BY1", "BY2"],
        "Israel": ["IL1", "IL2"],
        "Iceland": ["IS1", "IS2", "IS3", "IS4"],
        "Cyprus": ["CY1", "CY2"],
        "Serbia": ["CS1", "CS2"],
        "Bulgaria": ["BG1", "BG2"],
        "Slovakia": ["SK1", "SK2"],
        "Hungary": ["HU1", "HU2"],
        "Kazakhstan": ["KZ1", "KZ2"],
        "Bosnia-Herzegovina": ["BA1"],
        "Slovenia": ["SI1", "SI2"],
        "Azerbaijan": ["AZ1"],
        "Ireland": ["IR1", "IR2"],
        "Latvia": ["LA1", "LA2"],
        "Georgia": ["GE1", "GE2"],
        "Kosovo": ["XK1"],
        "Albania": ["AL1"],
        "Lithuania": ["LT1", "LT2"],
        "North-Macedonia": ["MK1"],
        "Armenia": ["AM1"],
        "Estonia": ["EE1", "EE2"],
        "Northern-Ireland": ["NI1", "NI2"],
        "Malta": ["MT1"],
        "Luxembourg": ["LU1"],
        "Wales": ["WL1"],
        "Montenegro": ["MN1"],
        "Moldova": ["MD1"],
        "Färöer": ["FA1"],
        "Gibraltar": ["GI1"],
        "Andorra": ["AD1"],
        "San-Marino": ["SM1"],
        "Brazil": ["BR1", "BR2", "BR3", "BRC", "BRGA"],
        "Mexico": ["MX1", "MX2"],
        "Argentina": ["AR1", "AR2", "AR3F", "AR5", "AR3", "AR4"],
        "USA": ["US1", "US2", "US3"],
        "Colombia": ["CO1", "CO2"],
        "Ecuador": ["EC1", "EC2"],
        "Paraguay": ["PY1", "PY2"],
        "Chile": ["CL1", "CL2"],
        "Uruguay": ["UY1", "UY2"],
        "Costa-Rica": ["CR1", "CR2"],
        "Bolivia": ["BO1"],
        "Guatemala": ["GT1", "GT2"],
        "Dominican-Rep.": ["DO1"],
        "Honduras": ["HN1"],
        "Venezuela": ["VE1"],
        "Peru": ["PE1", "PE2"],
        "Panama": ["PA1"],
        "El-Salvador": ["SV1"],
        "Jamaica": ["JM1"],
        "Nicaragua": ["NC1"],
        "Canada": ["CA1"],
        "Haiti": ["HT1"],
        "Japan": ["JP1", "JP2", "JP3"],
        "South-Korea": ["KR1", "KR2", "KR3"],
        "China": ["CN1", "CN2", "CN3"],
        "Iran": ["IA1", "IA2"],
        "Australia": ["AU1", "AU2V", "AU2NSW", "AU2Q", "AU2S", "AU2W", "AU3V", "AU3NSW", "AU2T", "AU2NOR", "AU3Q", "AU2CAP", "AU3S"],
        "Saudi-Arabia": ["SA1", "SA2"],
        "Thailand": ["TH1", "TH2"],
        "Qatar": ["QA1", "QA2"],
        "United Arab Emirates": ["AE1", "AE2"],
        "Indonesia": ["ID1", "ID2"],
        "Jordan": ["JO1"],
        "Syria": ["SY1"],
        "Uzbekistan": ["UZ1"],
        "Malaysia": ["MY1", "MY2"],
        "Vietnam": ["VN1", "VN2"],
        "Iraq": ["IQ1"],
        "Kuwait": ["KW1"],
        "Bahrain": ["BH1"],
        "Myanmar": ["MM1"],
        "Palestine": ["PS1"],
        "India": ["IN1", "IN2"],
        "New Zealand": ["NZ1"],
        "Hong Kong": ["HK1", "HK2"],
        "Oman": ["OM1"],
        "Taiwan": ["TW1"],
        "Tajikistan": ["TJ1"],
        "Turkmenistan": ["TM1"],
        "Lebanon": ["LB1"],
        "Bangladesh": ["BD1"],
        "Singapore": ["SG1"],
        "Cambodia": ["KH1"],
        "Kyrgyzstan": ["KG1"],
        "Egypt": ["EG1", "EG2"],
        "Algeria": ["DZ1", "DZ2"],
        "Tunisia": ["TN1", "TN2"],
        "Morocco": ["MA1", "MA2"],
        "South-Africa": ["ZA1", "ZA2"],
        "Kenya": ["KE1", "KE2"],
        "Zambia": ["ZM1"],
        "Ghana": ["GH1"],
        "Nigeria": ["NG1"],
        "Uganda": ["UG1"],
        "Burundi": ["BI1"],
        "Rwanda": ["RW1"],
        "Cameroon": ["CM1"],
        "Tanzania": ["TZ1"],
        "Gambia": ["GM1"],
        "Sudan": ["SD1"]
    },
    "Women's": {
        "England-Women": ["UW1", "UW2"],
        "Spain-Women": ["EW1", "EW2"],
        "Germany-Women": ["GW1", "GW2"],
        "Brazil-Women": ["FB1"],
        "France-Women": ["FF1"],
        "Italy-Women": ["IF1"],
        "Sweden-Women": ["SX1","SX2"],
        "Argentina-Women": ["AP1"],
        "Norway-Women": ["NW1", "NW2"],
        "Iceland-Women": ["IW1", "IW2"],
        "Scotland-Women": ["SP1"],
        "Netherlands-Women": ["NV1"],
        "Denmark-Women": ["DW1"],
        "Belgium-Women": ["BW1"],
        "Japan-Women": ["JW1", "JW2"],
        "Finland-Women": ["FW1"],
        "Mexico-Women": ["MF1"],
        "Czech-Republic-Women": ["LZ1"],
        "Israel-Women": ["IJ1"],
        "USA-Women": ["UV1", "UV2"],
        "Australia-Women": ["AW1"],
        "South-Korea-Women": ["KX1"]
    }
}

# Combine Men's and Women's league data into a single dictionary
all_leagues = {**leagues_data["Men's"], **leagues_data["Women's"]}
# Sort the combined list of countries/leagues alphabetically
sorted_countries = sorted(all_leagues.keys())


spinner_messages = [
    "Fetching the latest football ratings...",
    "Hold tight, we're gathering the data...",
    "Just a moment, crunching the numbers...",
    "Loading the football magic...",
    "Almost there, preparing the stats..."
]

logger = logging.getLogger(__name__)

# --- Helper Functions ---
def normalize_team_name(name):
    """Robustly cleans and standardizes a team name for reliable matching."""
    if not isinstance(name, str): return ""
    name = name.lower()
    name = name.replace('ö', 'oe').replace('ü', 'ue').replace('ä', 'ae')
    name = name.replace('ø', 'oe').replace('å', 'aa').replace('æ', 'ae')
    name = re.sub(r'[\&\-\.]+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    # Remove league identifiers like (N) or (S) that sometimes appear in names
    name = re.sub(r'\s\([ns]\)$', '', name)
    return ' '.join(name.split())

# --- Data Fetching and Parsing Functions ---

@st.cache_data(ttl=3600)
def fetch_table_data(country, league):
    """Fetches and parses ratings and league table in one go."""
    def extract_rating_table(soup, keyword, fallback_ids):
        """Extract rating table for home/away views with validation."""
        keyword_lower = keyword.lower()
        candidates = list(soup.find_all('table', class_='rattab'))
        for table_id in fallback_ids:
            fallback_table = soup.find('table', id=table_id)
            if fallback_table:
                candidates.append(fallback_table)

        seen = set()
        required_headers = {"team", "rating"}
        for table in candidates:
            if id(table) in seen:
                continue
            seen.add(id(table))

            header = table.find('th')
            header_text = header.get_text(strip=True).lower() if header else ""
            if keyword_lower not in header_text:
                continue

            header_row = None
            for potential_row in table.find_all('tr'):
                cells = potential_row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    header_row = potential_row
                    break
            if not header_row:
                logger.error("%s rating table missing header row", keyword)
                continue

            header_cells = {
                re.sub(r"[^a-z]", "", cell.get_text(strip=True).lower())
                for cell in header_row.find_all(['th', 'td'])
            }
            if not required_headers.issubset(header_cells):
                logger.error("%s rating table missing required columns: %s", keyword, required_headers - header_cells)
                continue

            teams_data = []
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue
                team_link = cols[1].find('a')
                if not team_link or not team_link.has_attr('href'):
                    continue
                team_url = team_link['href']
                team_name_text = team_link.get_text(strip=True)
                team_slug = team_url.strip('/').split('/')[-1] if team_url else ""
                name_from_url = team_name_text or team_slug.replace('-', ' ')
                rating_text = cols[4].get_text(strip=True)
                try:
                    rating = float(rating_text)
                except ValueError:
                    logger.error("Invalid rating value '%s' encountered in %s table", rating_text, keyword)
                    continue
                teams_data.append({"Team": name_from_url, "Rating": rating, "URL": team_url})

            if teams_data:
                return pd.DataFrame(teams_data)
            logger.error("%s rating table did not contain any rows", keyword)
        return None

    try:
        soup_home = fetch_league_soup(country, league, "home")
        soup_away = fetch_league_soup(country, league, "away")

        home_rating_table = extract_rating_table(soup_home, "Home", ("home", "home_table", "home_rating"))
        away_rating_table = extract_rating_table(soup_away, "Away", ("away", "away_table", "away_rating"))

        league_table = None
        try:
            all_html_tables = pd.read_html(io.StringIO(str(soup_home)), flavor="lxml")
        except ValueError:
            all_html_tables = []
        expected_columns = {"M", "P.", "Goals", "Home", "Away", "Home.4", "Away.4"}
        for candidate in all_html_tables:
            candidate_columns = set(candidate.columns.astype(str))
            if expected_columns.issubset(candidate_columns):
                league_table = candidate
                break
        if league_table is None:
            logger.error(
                "League table for %s %s missing required columns: %s",
                country,
                league,
                expected_columns,
            )
        return home_rating_table, away_rating_table, league_table
    except Exception as exc:
        logger.exception("Failed to fetch league tables for %s %s: %s", country, league, exc)
        return None, None, None

@st.cache_data(ttl=3600)
def fetch_league_odds(country, league):
    """Fetches the available odds table from the main league page."""
    try:
        soup = fetch_league_soup(country, league)

        header_selectors = [
            lambda s: s.find('th', string=re.compile(r"Rating\s*Available Odds", re.I)),
            lambda s: s.find('caption', string=re.compile(r"Available Odds", re.I)),
        ]

        header = None
        for selector in header_selectors:
            header = selector(soup)
            if header:
                break
        if not header:
            logger.error("Could not locate odds header for %s %s", country, league)
            return None

        odds_table = header.find_parent('table')
        if not odds_table:
            logger.error("Odds table missing for %s %s", country, league)
            return None

        odds_data = []
        for row in odds_table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if not cols:
                continue

            # Guard against decorative spacer rows that break the expected width
            if len(cols) < 7:
                logger.debug("Skipping odds row with insufficient columns for %s %s", country, league)
                continue

            date_text = cols[0].get_text(" ", strip=True)
            date_text = date_text.split('•')[0].strip()

            rating_text = cols[1].get_text(" ", strip=True)
            league_code = cols[2].get_text(" ", strip=True)

            flag_img = cols[3].find('img') if len(cols) >= 4 else None
            flag_src = flag_img['src'] if flag_img and flag_img.has_attr('src') else None
            if flag_src and flag_src.startswith('/'):
                flag_src = f"https://www.soccer-rating.com{flag_src}"

            home_index = 4 if len(cols) > 4 else None
            away_index = 6 if len(cols) > 6 else None

            home_team_raw = cols[home_index].get_text(" ", strip=True) if home_index is not None else ""
            away_team_raw = cols[away_index].get_text(" ", strip=True) if away_index is not None else ""

            clean_home = re.sub(r'[↑↓]', '', home_team_raw).strip()
            clean_away = re.sub(r'[↑↓]', '', away_team_raw).strip()

            odds_cells = cols[-3:]
            if len(odds_cells) < 3:
                continue

            normalize_odd = lambda value: value.replace(',', '.').strip()
            odd_1 = normalize_odd(odds_cells[0].get_text(strip=True)) or "-"
            odd_x = normalize_odd(odds_cells[1].get_text(strip=True)) or "-"
            odd_2 = normalize_odd(odds_cells[2].get_text(strip=True)) or "-"

            odds_data.append({
                "match_date": date_text,
                "rating": rating_text,
                "league_code": league_code,
                "flag_src": flag_src,
                "home_team_raw": home_team_raw,
                "away_team_raw": away_team_raw,
                "home_team": clean_home,
                "away_team": clean_away,
                "odd_1": odd_1,
                "odd_x": odd_x,
                "odd_2": odd_2
            })

        if not odds_data:
            logger.error("No odds rows parsed for %s %s", country, league)
            return None
        return pd.DataFrame(odds_data)
    except Exception as exc:
        logger.exception("Failed to fetch league odds for %s %s: %s", country, league, exc)
        return None

def find_section_header(soup, header_text):
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None


def render_odds_table(odds_df, league_label):
    """Renders the available odds DataFrame as an HTML table."""
    if not isinstance(odds_df, pd.DataFrame) or odds_df.empty:
        return ""

    header_html = f"""
    <div class="odds-table-wrapper">
        <table class="odds-table">
            <caption>Rating &amp; Available Odds &mdash; {html.escape(league_label)}</caption>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Rating</th>
                    <th>League</th>
                    <th>Home</th>
                    <th></th>
                    <th>Away</th>
                    <th>1</th>
                    <th>X</th>
                    <th>2</th>
                </tr>
            </thead>
            <tbody>
    """

    body_rows = []
    for _, row in odds_df.iterrows():
        odds_values = []
        best_index = None
        parsed_odds = []
        for value in (row.get('odd_1'), row.get('odd_x'), row.get('odd_2')):
            try:
                parsed_value = float(str(value).replace(',', '.'))
            except (TypeError, ValueError):
                parsed_value = None
            parsed_odds.append(parsed_value)

        if any(v is not None for v in parsed_odds):
            max_value = max(v for v in parsed_odds if v is not None)
            best_index = parsed_odds.index(max_value)

        for idx, key in enumerate(['odd_1', 'odd_x', 'odd_2']):
            cell_value = row.get(key, '')
            cell_text = html.escape(str(cell_value)) if cell_value not in (None, '') else "-"
            css_class = "odds-cell"
            if best_index is not None and idx == best_index:
                css_class += " best"
            odds_values.append(f"<td class=\"{css_class}\">{cell_text}</td>")

        flag_html = ""
        flag_src = row.get('flag_src')
        if flag_src:
            flag_html = f"<img src=\"{html.escape(flag_src)}\" alt=\"flag\" width=\"20\" height=\"14\" style=\"margin-right:6px;\">"

        body_rows.append(
            """
            <tr>
                <td>{date}</td>
                <td class="league-cell">{rating}</td>
                <td class="league-cell">{league}</td>
                <td class="teams-cell">{flag}{home}</td>
                <td class="vs-cell"><span class="vs-badge">vs</span></td>
                <td class="teams-cell">{away}</td>
                {odds_cells}
            </tr>
            """.format(
                date=html.escape(row.get('match_date', '')),
                rating=html.escape(row.get('rating', '')),
                league=html.escape(row.get('league_code', '')),
                flag=flag_html,
                home=html.escape(row.get('home_team_raw', row.get('home_team', ''))),
                away=html.escape(row.get('away_team_raw', row.get('away_team', ''))),
                odds_cells="".join(odds_values)
            )
        )

    table_html = header_html + "".join(body_rows) + "</tbody></table></div>"
    return table_html

def get_correct_table(soup, target_team_name, target_team_url, header_text, table_id_1, table_id_2):
    """Finds the correct data table using a hybrid URL-first, then name-fallback approach."""
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
def fetch_team_page_data(team_name, team_url):
    """Fetches lineup, squad, and last matches from a single team page visit."""
    try:
        soup = fetch_team_soup(team_url)

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
    except Exception as exc:
        logger.exception("Failed to fetch team data for %s (%s): %s", team_name, team_url, exc)
        return None, None, None

def get_league_suggested_draw_rate(league_table):
    """
    Analyzes the league table to suggest a realistic draw rate.
    Returns a suggested draw probability based on league data.
    """
    if not isinstance(league_table, pd.DataFrame) or league_table.empty:
        return 0.27
    
    try:
        total_matches, total_draws = 0, 0
        for _, row in league_table.iterrows():
            matches_played, points = int(row['M']), int(row['P.'])
            if ':' in str(row['Goals']):
                max_wins = min(points // 3, matches_played)
                draws = min(points - (max_wins * 3), matches_played - max_wins)
                total_matches += matches_played
                total_draws += draws
        
        league_draw_rate = total_draws / total_matches if total_matches > 0 else 0.27
        return max(0.20, min(0.35, league_draw_rate))
    except Exception:
        return 0.27

def calculate_outcome_probabilities(home_rating, away_rating, draw_probability):
    """
    Calculates home, draw, and away probabilities with user-specified draw rate.
    """
    home_advantage = 0
    adjusted_rating_diff = home_rating - away_rating + home_advantage
    p_home_vs_away = 1 / (1 + 10**(-adjusted_rating_diff / 400))
    
    remaining_prob = 1 - draw_probability
    p_home = p_home_vs_away * remaining_prob
    p_away = (1 - p_home_vs_away) * remaining_prob
    
    total = p_home + draw_probability + p_away
    return p_home / total, draw_probability / total, p_away / total

# --- UI Styling & App Layout ---
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --primary:#0f766e;
            --primary-dark:#0b4d4a;
            --accent:#22c55e;
            --text-main:#0f172a;
            --muted:#5b7083;
        }

        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }

        body {
            background: radial-gradient(circle at 20% 20%, rgba(34,197,94,0.12), transparent 55%),
                        radial-gradient(circle at 80% 0%, rgba(59,130,246,0.14), transparent 50%),
                        linear-gradient(135deg, #f5f7fa 0%, #e2e8f0 100%);
            color: var(--text-main);
        }

        .stApp {
            background: transparent;
            color: var(--text-main);
        }

        .main .block-container {
            background: rgba(255, 255, 255, 0.82);
            border-radius: 28px;
            padding: 28px 36px 40px;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
            border: 1px solid rgba(15, 118, 110, 0.08);
            backdrop-filter: blur(10px);
        }

        @media (max-width: 992px) {
            .main .block-container {
                padding: 22px 20px 28px;
                border-radius: 22px;
            }
        }

        .stApp header { background: transparent; }

        section[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.88);
            color: #e2e8f0;
            backdrop-filter: blur(16px);
        }

        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h1 {
            color: #f8fafc;
        }

        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] label {
            color: #cbd5f5;
        }

        section[data-testid="stSidebar"] div[data-testid="stAlert"] {
            background: #fef9c3;
            border: 1px solid rgba(202, 138, 4, 0.35);
            color: #713f12;
        }

        section[data-testid="stSidebar"] div[data-testid="stAlert"] p,
        section[data-testid="stSidebar"] div[data-testid="stAlert"] span {
            color: #713f12 !important;
        }

        .header {
            text-align: center;
            font-size: 40px;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--primary-dark);
        }

        .subheader {
            text-align: center;
            color: var(--muted);
            margin-bottom: 30px;
            font-size: 16px;
        }

        .hero-card {
            background: rgba(255, 255, 255, 0.82);
            border-radius: 20px;
            padding: 24px 28px;
            box-shadow: 0 20px 45px rgba(15, 118, 110, 0.18);
            border: 1px solid rgba(15, 118, 110, 0.08);
            margin-bottom: 28px;
        }

        .hero-title {
            font-size: 26px;
            font-weight: 700;
            color: var(--primary-dark);
        }

        .hero-subtitle {
            color: var(--muted);
            margin-top: 4px;
            font-size: 14px;
        }

        .hero-meta {
            margin-top: 16px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .hero-pill {
            background: rgba(34, 197, 94, 0.14);
            color: var(--primary-dark);
            border-radius: 999px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        .card {
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.1), rgba(34, 197, 94, 0.08));
            padding: 18px;
            border-radius: 16px;
            box-shadow: 0 18px 30px rgba(15, 23, 42, 0.08);
            text-align: center;
            border: 1px solid rgba(15, 118, 110, 0.14);
        }

        .card-title {
            font-size: 13px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }

        .card-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--primary-dark);
        }

        .player-table-header {
            font-weight: 600;
            font-size: 13px;
            color: var(--muted);
        }

        .odds-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.88em;
            padding: 10px 12px;
            margin-bottom: 6px;
            border-radius: 12px;
            background: rgba(148, 163, 184, 0.12);
            border: 1px solid rgba(148, 163, 184, 0.15);
        }

        .odds-teams { flex-grow: 1; font-weight: 600; color: var(--text-main); }

        .odds-values {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            min-width: 120px;
        }

        .odds-value {
            font-weight: 700;
            color: var(--primary-dark);
            text-align: center;
        }

        .odds-table-wrapper { margin-top: 10px; }

        .odds-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            background: rgba(255,255,255,0.92);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 18px 35px rgba(15, 23, 42, 0.08);
        }

        .odds-table caption {
            background: linear-gradient(120deg, rgba(15, 118, 110, 0.92), rgba(34, 197, 94, 0.82));
            color: #f8fafc;
            font-weight: 700;
            padding: 12px 18px;
            text-align: center;
            font-size: 14px;
            letter-spacing: 0.05em;
        }

        .odds-table thead th {
            background-color: rgba(15, 118, 110, 0.12);
            color: var(--primary-dark);
            padding: 12px 8px;
            text-align: center;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .odds-table tbody td {
            padding: 12px 10px;
            font-size: 12px;
            border-bottom: 1px solid rgba(15, 118, 110, 0.08);
            vertical-align: middle;
        }

        .odds-table tbody tr:nth-child(even) { background-color: rgba(241, 245, 249, 0.7); }

        .odds-table .teams-cell { font-weight: 600; color: var(--text-main); }

        .odds-table .league-cell { text-align: center; font-weight: 600; color: var(--primary-dark); }

        .odds-table .odds-cell { text-align: center; font-weight: 600; color: var(--text-main); }

        .odds-table .odds-cell.best { color: var(--primary); font-weight: 700; }

        .vs-cell { text-align: center; }

        .vs-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(15, 118, 110, 0.14);
            color: var(--primary-dark);
            font-weight: 700;
            letter-spacing: 0.08em;
        }

        div[data-testid="stAlert"] {
            color: var(--text-main);
        }

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span {
            color: var(--text-main) !important;
        }

        .main div[data-testid="stExpander"] {
            border-radius: 18px;
            border: 1px solid rgba(15, 118, 110, 0.12);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
            background: rgba(255,255,255,0.9);
        }

        .main div[data-testid="stExpander"] > div:first-child {
            border-radius: 18px;
            background: rgba(15, 118, 110, 0.1);
        }

        .main div[data-testid="stExpander"] label {
            color: var(--primary-dark) !important;
            font-weight: 600;
        }

        .main div[data-testid="stExpander"] p,
        .main div[data-testid="stExpander"] span,
        .main div[data-testid="stExpander"] li,
        .main div[data-testid="stExpander"] h1,
        .main div[data-testid="stExpander"] h2,
        .main div[data-testid="stExpander"] h3,
        .main div[data-testid="stExpander"] h4,
        .main div[data-testid="stExpander"] h5,
        .main div[data-testid="stExpander"] h6 {
            color: var(--text-main) !important;
        }

        .main div[data-testid="stExpander"] div[data-testid="stMarkdown"] p,
        .main div[data-testid="stExpander"] div[data-testid="stMarkdown"] li,
        .main div[data-testid="stExpander"] div[data-testid="stMarkdown"] span {
            color: var(--text-main) !important;
        }

        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: var(--primary-dark) !important;
        }

        div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {
            color: var(--text-main) !important;
            font-weight: 600;
        }

        div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
            color: var(--accent) !important;
        }

        .main div[data-testid="stExpander"] pre {
            color: var(--text-main);
            background: rgba(15, 118, 110, 0.08);
            border-radius: 14px;
            padding: 10px 14px;
            font-weight: 600;
            border: 1px solid rgba(15, 118, 110, 0.12);
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.78);
            box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.18);
            color: #e2e8f0;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] > div:first-child {
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.62);
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] button {
            color: #f8fafc !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stExpander"] p,
        section[data-testid="stSidebar"] div[data-testid="stExpander"] li,
        section[data-testid="stSidebar"] div[data-testid="stExpander"] span,
        section[data-testid="stSidebar"] div[data-testid="stExpander"] label {
            color: #e2e8f0 !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            color: var(--primary-dark);
        }

        .sidebar-odds-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
            color: #94a3b8;
        }

        .pill-muted {
            background: rgba(148, 163, 184, 0.18);
            color: #e2e8f0;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 10px;
            letter-spacing: 0.06em;
        }

        .match-line {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: 14px;
            background: rgba(15, 118, 110, 0.08);
            border: 1px solid rgba(15, 118, 110, 0.14);
            color: var(--text-main);
            font-size: 13px;
            font-weight: 600;
        }

        .match-line + .match-line {
            margin-top: 10px;
        }

        .match-date {
            color: var(--primary-dark);
            font-weight: 700;
            min-width: 70px;
        }

        .match-opponent {
            flex: 1;
        }

        .match-result {
            background: rgba(34, 197, 94, 0.18);
            color: var(--primary-dark);
            padding: 6px 14px;
            border-radius: 999px;
            font-weight: 700;
            letter-spacing: 0.04em;
        }
    </style>
""", unsafe_allow_html=True)

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
        - Scan the **market odds rail** for instant price discovery.
        - Use the main workspace to **compare clubs, lineups, and value zones**.
        """
    )

st.sidebar.header("🎯 Build Your Matchup")

if 'data_fetched' not in st.session_state: st.session_state['data_fetched'] = False
if 'current_selection' not in st.session_state: st.session_state['current_selection'] = None

def fetch_data_for_selection(country, league):
    current_selection = f"{country}_{league}"
    if st.session_state.get('current_selection') != current_selection or not st.session_state.get('data_fetched', False):
        st.session_state['current_selection'] = current_selection
        with st.spinner(random.choice(spinner_messages)):
            home_table, away_table, league_table = fetch_table_data(country, league)
            odds_table = fetch_league_odds(country, league)
            
            if isinstance(home_table, pd.DataFrame) and not home_table.empty:
                st.session_state.update({
                    "home_table": home_table,
                    "away_table": away_table,
                    "league_table": league_table,
                    "odds_table": odds_table,
                    "data_fetched": True,
                    "last_refresh": time.time()
                })
                for key in ['home_lineup', 'away_lineup', 'home_squad', 'away_squad', 
                           'home_matches', 'away_matches', 'last_home_team', 'last_away_team']: 
                    st.session_state.pop(key, None)
                st.success(f"✅ Loaded {country} - {league}")
            else:
                st.session_state['data_fetched'] = False
                st.error(f"❌ Failed to load data for {country} - {league}")

selected_country = st.sidebar.selectbox("Select Country/League Type:", sorted_countries, key="country_select")
league_list = all_leagues[selected_country]
selected_league = st.sidebar.selectbox("Select League:", league_list, key="league_select")

fetch_data_for_selection(selected_country, selected_league)

# --- Display Odds in Sidebar ---
if st.session_state.get('data_fetched', False):
    with st.sidebar.expander("Available Market Odds", expanded=True):
        odds_table = st.session_state.get("odds_table")
        if isinstance(odds_table, pd.DataFrame) and not odds_table.empty:
            st.markdown(
                """
                <div class="sidebar-odds-header">
                    <span>Upcoming matchups</span>
                    <span class="pill-muted">1 · X · 2</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            for _, row in odds_table.iterrows():
                st.markdown(
                    f"""<div class="odds-row">
                        <div class="odds-teams">{row['home_team']} vs {row['away_team']}</div>
                        <div class="odds-values">
                            <div class="odds-value">{row['odd_1']}</div>
                            <div class="odds-value">{row['odd_x']}</div>
                            <div class="odds-value">{row['odd_2']}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.warning("Market odds are not available right now. Try refreshing or choose another league.")

# --- Main Content Area ---
if st.session_state.get('data_fetched', False):
    home_table = st.session_state.home_table
    away_table = st.session_state.away_table

    odds_table = st.session_state.get("odds_table")
    match_count = int(odds_table.shape[0]) if isinstance(odds_table, pd.DataFrame) else 0
    last_refresh = st.session_state.get("last_refresh")
    if last_refresh:
        refresh_text = datetime.utcfromtimestamp(last_refresh).strftime("%d %b %Y %H:%M UTC")
    else:
        refresh_text = "Awaiting refresh"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{html.escape(selected_country)} · {html.escape(selected_league)}</div>
            <div class="hero-subtitle">Explore the live blend of Elo strength, bookmaker prices, and matchup context.</div>
            <div class="hero-meta">
                <span class="hero-pill">Upcoming fixtures: {match_count}</span>
                <span class="hero-pill">Last synced: {refresh_text}</span>
                <span class="hero-pill">Interactive odds modelling</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("🎲 League Available Odds", expanded=True):
        odds_table = st.session_state.get("odds_table")
        if isinstance(odds_table, pd.DataFrame) and not odds_table.empty:
            league_label = f"{selected_country} {selected_league}"
            st.markdown(render_odds_table(odds_table, league_label), unsafe_allow_html=True)
        else:
            st.warning("Market odds are not available right now. Try refreshing or choose another league.")

    with st.expander("⚽ Matchup", expanded=True):
        col1, col2 = st.columns(2)
        home_team_name = col1.selectbox("Select Home Team:", home_table["Team"], key="home_team_select")
        away_team_name = col2.selectbox("Select Away Team:", away_table["Team"], key="away_team_select")
        home_team_data = home_table[home_table["Team"] == home_team_name].iloc[0]
        away_team_data = away_table[away_table["Team"] == away_team_name].iloc[0]

    changed = False
    if st.session_state.get('last_home_team') != home_team_name:
        with st.spinner(f"Fetching {home_team_name} data..."):
            lineup, squad, matches = fetch_team_page_data(home_team_name, home_team_data['URL'])
            st.session_state.update({
                'home_lineup': lineup,
                'home_squad': squad,
                'home_matches': matches,
                'last_home_team': home_team_name,
            })
        changed = True

    if st.session_state.get('last_away_team') != away_team_name:
        with st.spinner(f"Fetching {away_team_name} data..."):
            lineup, squad, matches = fetch_team_page_data(away_team_name, away_team_data['URL'])
            st.session_state.update({
                'away_lineup': lineup,
                'away_squad': squad,
                'away_matches': matches,
                'last_away_team': away_team_name,
            })
        changed = True

    if changed:
        st.rerun()

    with st.expander("📊 Team Statistics", expanded=False):
        league_table = st.session_state.get("league_table")
        if isinstance(league_table, pd.DataFrame):
            # ... (omitting stat display function for brevity; it remains unchanged) ...
            def display_team_stats(team_name, table, column):
                try:
                    normalized_target = normalize_team_name(team_name)
                    table['normalized_name'] = table.iloc[:, 1].apply(normalize_team_name)
                    team_stats = table[table['normalized_name'] == normalized_target].iloc[0]
                    column.markdown(f"**{team_name}**")
                    column.metric(label="League Position", value=f"#{int(team_stats.iloc[0])}")
                    matches, points = int(team_stats['M']), int(team_stats['P.'])
                    gf, ga = map(int, team_stats['Goals'].split(':'))
                    column.metric(label="Avg. Goals Scored", value=f"{gf/matches:.2f}")
                    column.metric(label="Avg. Goals Conceded", value=f"{ga/matches:.2f}")
                except (IndexError, ValueError, KeyError):
                    column.warning(f"Stats unavailable for {team_name}.")
            
            stat_col1, stat_col2 = st.columns(2)
            display_team_stats(home_team_name, league_table, stat_col1)
            display_team_stats(away_team_name, league_table, stat_col2)
        else:
            st.warning("League table not available for detailed statistics.")

    with st.expander("📈 Odds Analysis", expanded=True):
        home_rating, away_rating = home_team_data['Rating'], away_team_data['Rating']
        c1, c2 = st.columns(2)
        c1.metric(f"{home_team_name} Rating", f"{home_rating:.2f}")
        c2.metric(f"{away_team_name} Rating", f"{away_rating:.2f}")

        st.markdown("---")
        suggested_draw_rate = get_league_suggested_draw_rate(st.session_state.get("league_table"))
        col_slider, col_info = st.columns([3, 1])
        draw_probability = col_slider.slider("Set Draw Probability:", 0.15, 0.45, suggested_draw_rate, 0.01, "%.2f")
        col_info.metric("League Avg", f"{suggested_draw_rate:.1%}")

        p_home, p_draw, p_away = calculate_outcome_probabilities(home_rating, away_rating, draw_probability)
        
        st.markdown("---")
        st.markdown(f"**Calculated Fair Probabilities**")
        prob_cols = st.columns(3)
        prob_cols[0].metric("Home Win", f"{p_home:.2%}")
        prob_cols[1].metric("Draw", f"{p_draw:.2%}")
        prob_cols[2].metric("Away Win", f"{p_away:.2%}")
        
        st.markdown("---")
        margin = st.slider("Apply Bookmaker's Margin (%):", 0, 15, 5, 1)
        margin_decimal = margin / 100.0
        probs = np.array([p_home, p_draw, p_away], dtype=float)
        target_sum = 1.0 + margin_decimal
        if probs.sum() > 0 and target_sum > 0:
            normalized_probs = probs / probs.sum()
            adjusted_probs = normalized_probs * target_sum
            odds_array = np.divide(1.0, adjusted_probs, out=np.zeros_like(adjusted_probs), where=adjusted_probs > 0)
        else:
            odds_array = np.zeros_like(probs)
        h_odds, d_odds, a_odds = odds_array

        st.write("**Calculated Odds with Margin:**")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='card'><div class='card-title'>Home (1)</div><div class='card-value'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-value'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='card'><div class='card-title'>Away (2)</div><div class='card-value'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.write("**Draw No Bet Odds:**")
        p_dnb_home = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0
        dnb_probs = np.array([p_dnb_home, 1 - p_dnb_home], dtype=float)
        if dnb_probs.sum() > 0 and target_sum > 0:
            adjusted_dnb = (dnb_probs / dnb_probs.sum()) * target_sum
            dnb_odds_array = np.divide(1.0, adjusted_dnb, out=np.zeros_like(adjusted_dnb), where=adjusted_dnb > 0)
        else:
            dnb_odds_array = np.zeros_like(dnb_probs)
        dnb_h_odds, dnb_a_odds = dnb_odds_array
        dnb_c1, dnb_c2 = st.columns(2)
        dnb_c1.markdown(f"<div class='card'><div class='card-title'>Home (DNB)</div><div class='card-value'>{dnb_h_odds:.2f}</div></div>", unsafe_allow_html=True)
        dnb_c2.markdown(f"<div class='card'><div class='card-title'>Away (DNB)</div><div class='card-value'>{dnb_a_odds:.2f}</div></div>", unsafe_allow_html=True)

    with st.expander("📋 Interactive Lineups", expanded=True):
        # ... (omitting lineup display function for brevity; it remains unchanged) ...
        def display_interactive_lineup(team_name, team_key):
            st.subheader(f"{team_name}")
            lineup_data = st.session_state.get(team_key)
            if not lineup_data: st.warning("Lineup data not available."); return
            
            header_cols = st.columns([1, 4, 2, 2, 2])
            header_cols[0].markdown('<p class="player-table-header">On</p>', unsafe_allow_html=True)
            # ... (rest of headers) ...

            selected_starters = []
            for i, p in enumerate(lineup_data):
                player_cols = st.columns([1, 4, 2, 2, 2])
                if player_cols[0].checkbox("", value=(i < 11), key=f"check_{team_key}_{i}", label_visibility="collapsed"):
                    selected_starters.append(p)
                player_cols[1].write(p['name']); player_cols[2].write(p['position']); player_cols[3].write(p['stats']); player_cols[4].write(f"**{p['rating']}**")
            
            # ... (rest of lineup analysis) ...

        col1, col2 = st.columns(2)
        with col1: display_interactive_lineup(f"{home_team_name} (Home)", "home_lineup")
        with col2: display_interactive_lineup(f"{away_team_name} (Away)", "away_lineup")

    with st.expander("👥 Full Squads", expanded=False):
        # ... (omitting squad display function for brevity; it remains unchanged) ...
        def display_squad(team_name, squad_key, lineup_key):
            st.subheader(f"{team_name}")
            squad_data = st.session_state.get(squad_key)
            if not squad_data: st.warning("Squad data not available."); return

            starter_names = {p['name'] for p in st.session_state.get(lineup_key, [])[:11]}
            for p in squad_data:
                player_cols = st.columns([4, 2, 2])
                player_cols[0].write(f"**{p['name']}**" if p['name'] in starter_names else p['name'])
                player_cols[1].write(str(p['age'])); player_cols[2].write(f"**{p['rating']}**")

        squad_col1, squad_col2 = st.columns(2)
        with squad_col1: display_squad(f"{home_team_name} (Home)", "home_squad", "home_lineup")
        with squad_col2: display_squad(f"{away_team_name} (Away)", "away_squad", "away_lineup")

    with st.expander("📅 Last 5 League Matches", expanded=False):
        # ... (omitting matches display function for brevity; it remains unchanged) ...
        def display_last_matches(team_name, matches_key):
            st.subheader(f"{team_name}")
            matches_data = st.session_state.get(matches_key)
            if not matches_data or not matches_data["matches"]: st.warning("Recent match data not available."); return
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

        match_col1, match_col2 = st.columns(2)
        with match_col1: display_last_matches(f"{home_team_name} (Home)", "home_matches")
        with match_col2: display_last_matches(f"{away_team_name} (Away)", "away_matches")

else:
    st.info("Please select a country and league in the sidebar to begin.")

