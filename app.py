import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
import math
import random
import time
import re
import html
from datetime import datetime

# Set page title and icon
st.set_page_config(page_title="Elo Ratings Odds Calculator", page_icon="odds_icon.png")

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
        "Czech-Republic": ["CZ1", "CZ2"],
        "Turkey": ["TU1", "TU2", "TU3B", "TU3K"],
        "Belgium": ["BE1", "BE2"],
        "Scotland": ["SC1", "SC2", "SC3", "SC4"],
        "Switzerland": ["CH1", "CH2"],
        "Finland": ["FI1", "FI2", "FI3", "FI4A", "FI4B", "FI4C"],
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


SPINNER_MESSAGES = [
    "Fetching the latest football ratings...",
    "Hold tight, we're gathering the data...",
    "Just a moment, crunching the numbers...",
    "Loading the football magic...",
    "Almost there, preparing the stats..."
]

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

DEFAULT_DRAW_RATE = 0.27
# Constants for the Elo-based draw model
# A 200-point Elo diff will reduce the draw prob by ~25%
# A 400-point Elo diff will reduce the draw prob by ~44%
DRAW_DECAY_FACTOR = 0.0035


def load_css(file_name):
    """Loads a local CSS file."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_name}")

def fetch_with_headers(url, referer=None, timeout=15):
    """Performs a GET request with standard browser headers."""
    headers = BASE_HEADERS.copy()
    headers["Referer"] = referer or "https://www.soccer-rating.com/"
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response

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
                            # Extract team name from the URL for consistency
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
        expected_columns = {"M", "P.", "Goals", "Home", "Away", "Home.4", "Away.4"}
        for candidate in all_html_tables:
            if expected_columns.issubset(set(candidate.columns.astype(str))):
                league_table = candidate
                break
        return home_rating_table, away_rating_table, league_table
    except Exception:
        return None, None, None

@st.cache_data(ttl=3600)
def fetch_soccerstats_data():
    """Fetches league-wide stats (Draw %, Avg Goals) from soccerstats.com."""
    url = "https://www.soccerstats.com/leagues.asp"
    try:
        response = requests.get(url, headers=BASE_HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        
        table = soup.find('table', id='btable')
        if not table:
            return None

        data = []
        rows = table.find_all('tr')
        
        for row in rows[1:]: # Skip header row
            cols = row.find_all('td')
            if len(cols) == 14: # Ensure it's a data row
                try:
                    league_full = cols[0].get_text(strip=True)
                    country, league_name = league_full.split(' - ', 1)
                    
                    draw_pct = cols[5].get_text(strip=True).replace('%', '')
                    avg_goals = cols[7].get_text(strip=True)

                    data.append({
                        "Country": country.strip(),
                        "League": league_name.strip(),
                        "Draw%": float(draw_pct) / 100.0 if draw_pct != '-' else None,
                        "AvgGoals": float(avg_goals) if avg_goals != '-' else None
                    })
                except (ValueError, IndexError):
                    continue # Skip rows that don't parse correctly
        
        return pd.DataFrame(data)
    except Exception:
        return None

def find_section_header(soup, header_text):
    """Finds a specific header tag in the soup."""
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None

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

def get_league_suggested_draw_rate(selected_country, selected_league):
    """
    Finds the actual draw rate for the selected league from the scraped soccerstats data.
    """
    try:
        stats_df = st.session_state.get("soccer_stats")
        if not isinstance(stats_df, pd.DataFrame):
            return DEFAULT_DRAW_RATE

        # Find the league index from our own mapping
        league_list = all_leagues[selected_country]
        try:
            league_index = league_list.index(selected_league)
        except (ValueError, TypeError):
            league_index = 0 # Default to first league

        # Normalize country name for matching
        country_name = selected_country.replace('-', ' ').replace('-Women', '')
        if country_name == "Bosnia-Herzegovina": country_name = "Bosnia and Herzegovina"
        if country_name == "South-Korea": country_name = "South Korea"
        if country_name == "South-Africa": country_name = "South Africa"
        if country_name == "Saudi-Arabia": country_name = "Saudi Arabia"
        if country_name == "Czech Republic": country_name = "Czech Republic"
        
        # Filter stats_df by country
        country_leagues = stats_df[stats_df['Country'].str.contains(country_name, case=False, na=False)]
        
        # Handle Women's leagues
        if "Women" in selected_country:
            country_leagues = country_leagues[country_leagues['League'].str.contains("Women", case=False, na=False)]
        else:
            # Exclude women's leagues if we're looking for men's
            country_leagues = country_leagues[~country_leagues['League'].str.contains("Women", case=False, na=False)]

        if country_leagues.empty:
            return DEFAULT_DRAW_RATE

        # Try to pick the league by its index
        if league_index < len(country_leagues):
            draw_rate = country_leagues.iloc[league_index]["Draw%"]
        else:
            # Fallback to the primary league for that country
            draw_rate = country_leagues.iloc[0]["Draw%"]

        return draw_rate if pd.notna(draw_rate) else DEFAULT_DRAW_RATE

    except Exception:
        # Broad fallback in case of any error
        return DEFAULT_DRAW_RATE

def calculate_outcome_probabilities(home_rating, away_rating, base_draw_prob):
    """
    Calculates home, draw, and away probabilities with Elo-based draw adjustment.
    """
    # 1. Adjust draw probability based on Elo difference
    elo_diff = abs(home_rating - away_rating)
    # Use an exponential decay to reduce draw prob as Elo diff increases
    # The decay factor is tuned to reduce prob reasonably
    draw_probability = base_draw_prob * math.exp(-elo_diff * DRAW_DECAY_FACTOR)
    
    # 2. Calculate initial H/A probs based on Elo (as if no draw)
    home_advantage = 0 # This could be a tunable constant, e.g., 50-80 Elo points
    adjusted_rating_diff = home_rating - away_rating + home_advantage
    p_home_vs_away = 1 / (1 + 10**(-adjusted_rating_diff / 400))
    
    # 3. Distribute the remaining probability between Home and Away
    remaining_prob = 1 - draw_probability
    p_home = p_home_vs_away * remaining_prob
    p_away = (1 - p_home_vs_away) * remaining_prob
    
    # 4. Normalize to ensure sum is 1 (should be close already)
    total = p_home + draw_probability + p_away
    return p_home / total, draw_probability / total, p_away / total

def apply_overround(probs, margin_pct):
    """
    Applies a bookmaker's margin (overround) to a set of fair probabilities
    using the proportional scaling method.
    """
    if not probs or sum(probs) == 0:
        return [0] * len(probs)
        
    margin_decimal = margin_pct / 100.0
    target_overround = 1 + margin_decimal
    
    # This is the scaling factor 'k'. We solve k * sum(p_i) = target_overround
    # But since sum(p_i) is 1, k is just target_overround.
    # We apply this k to the *inverse* of the probabilities (the odds)
    # which is equivalent to dividing the probabilities by k.
    
    # No, the standard method is to find a factor 'k' such that sum(p_i / k) = target_overround
    # This is not quite right.
    
    # Let's use the standard multiplicative method (which is one of several)
    # p_i' = p_i / (1 - margin_decimal)
    # This will result in sum(p_i') > 1.
    # Let's use the method where sum(1/odds_i) = target_overround.
    
    # p_i' = k * p_i
    # sum(p_i') = k * sum(p_i) = k * 1 = k
    # We want sum(p_i') = target_overround
    # So k = target_overround. This is incorrect, as this would mean p_i' = p_i * (1 + margin)
    
    # Let's use the correct "proportional scaling" or "odds ratio" method.
    # We need to find a single scaling factor 'k' such that:
    # (p_home / k) + (p_draw / k) + (p_away / k) = target_overround
    # (1/k) * (p_home + p_draw + p_away) = target_overround
    # (1/k) * 1 = target_overround
    # k = 1 / target_overround
    
    # This factor k is applied to the probabilities *before* inverting to odds.
    k = 1 / target_overround
    
    adjusted_probs = [p * (1/k) for p in probs]
    
    # Wait, that's wrong. Let's re-think.
    # Fair odds = 1/p. Bookie odds = 1/p'
    # We want sum(p') = target_overround.
    # Let p_i' = p_i * C (where C is a constant > 1)
    # sum(p_i') = sum(p_i * C) = C * sum(p_i) = C * 1 = C
    # So, the constant C is just the target overround.
    
    adjusted_probs = [p * target_overround for p in probs]
    
    # This simple scaling method isn't perfect, as it applies margin uniformly.
    # A more common one is to scale odds: bookie_odds = fair_odds * (1 - margin)
    # bookie_odds = (1/p) * (1 - margin)
    # p' = 1 / bookie_odds = 1 / ((1/p) * (1-margin)) = p / (1-margin)
    
    if margin_decimal == 1:
        return [0] * len(probs) # Avoid division by zero if margin is 100%

    k = 1.0 - margin_decimal
    
    adjusted_probs = [p / k for p in probs]
    
    # Let's check: p_h=0.5, p_a=0.5. Margin=10% (0.1)
    # k = 0.9
    # p_h' = 0.5 / 0.9 = 0.555...
    # p_a' = 0.5 / 0.9 = 0.555...
    # sum(p') = 1.111... (which is 1 / 0.9, or 1 / (1-margin))
    # This is a common method. The total book % is 1 / (1 - margin_pct).
    # A 5% margin (0.05) gives k=0.95, 1/0.95 = 1.0526 (105.3% book). This is correct.
    
    return adjusted_probs


def probs_to_odds(probs):
    """Converts a list of probabilities to decimal odds."""
    return [1 / p if p > 0 else 0 for p in probs]

# --- UI Helper Functions ---

def display_team_stats(team_name, table, column):
    """Displays key league stats for a team in a given column."""
    try:
        normalized_target = normalize_team_name(team_name)
        if 'normalized_name' not in table.columns:
            table['normalized_name'] = table.iloc[:, 1].apply(normalize_team_name)
        
        team_stats = table[table['normalized_name'] == normalized_target].iloc[0]
        column.markdown(f"**{team_name}**")
        
        pos = int(team_stats.iloc[0])
        column.metric(label="League Position", value=f"#{pos}")
        
        matches, points = int(team_stats['M']), int(team_stats['P.'])
        gf, ga = map(int, team_stats['Goals'].split(':'))
        
        column.metric(label="Avg. Goals Scored", value=f"{gf/matches:.2f}")
        column.metric(label="Avg. Goals Conceded", value=f"{ga/matches:.2f}")
    except (IndexError, ValueError, KeyError, ZeroDivisionError):
        column.warning(f"Stats unavailable for {team_name}.")

def display_interactive_lineup(team_name, team_key):
    """Displays the interactive lineup selector for a team."""
    st.subheader(f"{team_name}")
    lineup_data = st.session_state.get(team_key)
    if not lineup_data: 
        st.warning("Lineup data not available.")
        return
    
    header_cols = st.columns([1, 4, 2, 2, 2])
    header_cols[0].markdown('<p class="player-table-header">On</p>', unsafe_allow_html=True)
    header_cols[1].markdown('<p class="player-table-header">Player</p>', unsafe_allow_html=True)
    header_cols[2].markdown('<p class="player-table-header">Pos</p>', unsafe_allow_html=True)
    header_cols[3].markdown('<p class="player-table-header">Stats</p>', unsafe_allow_html=True)
    header_cols[4].markdown('<p class="player-table-header">Rating</p>', unsafe_allow_html=True)

    selected_starters = []
    for i, p in enumerate(lineup_data):
        player_cols = st.columns([1, 4, 2, 2, 2])
        if player_cols[0].checkbox("", value=(i < 11), key=f"check_{team_key}_{i}", label_visibility="collapsed"):
            selected_starters.append(p)
        player_cols[1].write(p['name'])
        player_cols[2].write(p['position'])
        player_cols[3].write(p['stats'])
        player_cols[4].write(f"**{p['rating']}**")
    
    if selected_starters:
        avg_rating = sum(p['rating'] for p in selected_starters) / len(selected_starters)
        st.metric(label="Avg. Starter Rating", value=f"{avg_rating:.2f}")

def display_squad(team_name, squad_key, lineup_key):
    """Displays the full squad list."""
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

def display_last_matches(team_name, matches_key):
    """Displays the last 5 league matches for a team."""
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

# --- Main App Layout ---
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
        - Use the **Single Match** tab to analyze a specific matchup.
        - Use the **Multi-Match** tab to see odds for all league fixtures.
        """
    )

st.sidebar.header("🎯 Build Your Matchup")

if 'data_fetched' not in st.session_state: st.session_state['data_fetched'] = False
if 'current_selection' not in st.session_state: st.session_state['current_selection'] = None

def fetch_data_for_selection(country, league):
    """Callback to fetch all data when league selection changes."""
    current_selection = f"{country}_{league}"
    if st.session_state.get('current_selection') != current_selection or not st.session_state.get('data_fetched', False):
        st.session_state['current_selection'] = current_selection
        with st.spinner(random.choice(SPINNER_MESSAGES)):
            home_table, away_table, league_table = fetch_table_data(country, league)
            soccer_stats = fetch_soccerstats_data()
            
            if isinstance(home_table, pd.DataFrame) and not home_table.empty:
                st.session_state.update({
                    "home_table": home_table,
                    "away_table": away_table,
                    "league_table": league_table,
                    "soccer_stats": soccer_stats,
                    "data_fetched": True,
                    "last_refresh": time.time()
                })
                # Clear team-specific data
                for key in ['home_lineup', 'away_lineup', 'home_squad', 'away_squad', 
                           'home_matches', 'away_matches', 'last_home_team', 'last_away_team']: 
                    st.session_state.pop(key, None)
                st.success(f"✅ Loaded {country} - {league}")
            else:
                st.session_state['data_fetched'] = False
                st.error(f"❌ Failed to load data for {country} - {league}")

# --- Sidebar League Selection ---
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
    
    last_refresh = st.session_state.get("last_refresh")
    refresh_text = datetime.utcfromtimestamp(last_refresh).strftime("%d %b %Y %H:%M UTC") if last_refresh else "Awaiting refresh"

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{html.escape(selected_country)} · {html.escape(selected_league)}</div>
            <div class="hero-subtitle">Explore the live blend of Elo strength, bookmaker prices, and matchup context.</div>
            <div class="hero-meta">
                <span class="hero-pill">Teams: {len(team_list)}</span>
                <span class="hero-pill">Last synced: {refresh_text}</span>
                <span class="hero-pill">Dynamic draw modelling</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Global Inputs ---
    with st.expander("📈 Odds Analysis (Global Inputs)", expanded=False):
        col_info, col_model = st.columns([1, 3])
        suggested_draw_rate = get_league_suggested_draw_rate(selected_country, selected_league)
        col_info.metric("League Avg. Draw", f"{suggested_draw_rate:.1%}")
        col_model.info(f"Using Elo-based 'Closeness Model'. Draw probability starts at **{suggested_draw_rate:.1%}** and decreases as the Elo gap between teams widens.")
    
    
    # --- Main App Tabs ---
    tab1, tab2 = st.tabs(["Single Match Analysis", "Multi-Match Calculator"])

    with tab1:
        with st.expander("⚽ Matchup Selection", expanded=True):
            col1, col2 = st.columns(2)
            home_team_name = col1.selectbox("Select Home Team:", team_list, key="home_team_select")
            away_team_name = col2.selectbox("Select Away Team:", team_list, index=1 if len(team_list) > 1 else 0, key="away_team_select")
        
        # --- Fetch Team-Specific Data (Lineups, etc.) ---
        home_team_data = home_table[home_table["Team"] == home_team_name].iloc[0]
        away_team_data = away_table[away_table["Team"] == away_team_name].iloc[0]

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
        
        # --- Single Match Analysis ---
        with st.expander("📊 Team Ratings", expanded=True):
            home_rating, away_rating = home_team_data['Rating'], away_team_data['Rating']
            c1, c2 = st.columns(2)
            c1.metric(f"{home_team_name} (Home) Rating", f"{home_rating:.2f}")
            c2.metric(f"{away_team_name} (Away) Rating", f"{away_rating:.2f}")

        with st.expander("🎯 Calculated Odds", expanded=True):
            margin = st.slider("Apply Bookmaker's Margin (%):", 0.0, 15.0, 5.0, 0.5, format="%.1f%%", key="single_margin")

            # --- 1. Fair Probabilities ---
            p_home, p_draw, p_away = calculate_outcome_probabilities(home_rating, away_rating, suggested_draw_rate)
            
            st.markdown("---")
            st.markdown(f"**Calculated Fair Probabilities** (Dynamic Draw: {p_draw:.2%})")
            prob_cols = st.columns(3)
            prob_cols[0].metric("Home Win", f"{p_home:.2%}")
            prob_cols[1].metric("Draw", f"{p_draw:.2%}")
            prob_cols[2].metric("Away Win", f"{p_away:.2%}")
            
            # --- 2. Apply Margin & Get Odds (1x2) ---
            adj_probs_1x2 = apply_overround([p_home, p_draw, p_away], margin)
            odds_1x2 = probs_to_odds(adj_probs_1x2)
            
            st.markdown("---")
            st.write("**Calculated Odds with Margin:**")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='card'><div class='card-title'>Home (1)</div><div class='card-value'>{odds_1x2[0]:.2f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-value'>{odds_1x2[1]:.2f}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='card'><div class='card-title'>Away (2)</div><div class='card-value'>{odds_1x2[2]:.2f}</div></div>", unsafe_allow_html=True)

            # --- 3. Apply Margin & Get Odds (DNB) ---
            p_dnb_home = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0
            p_dnb_away = 1 - p_dnb_home
            
            adj_probs_dnb = apply_overround([p_dnb_home, p_dnb_away], margin)
            odds_dnb = probs_to_odds(adj_probs_dnb)
            
            st.markdown("---")
            st.write("**Draw No Bet Odds:**")
            dnb_c1, dnb_c2 = st.columns(2)
            dnb_c1.markdown(f"<div class='card'><div class='card-title'>Home (DNB)</div><div class='card-value'>{odds_dnb[0]:.2f}</div></div>", unsafe_allow_html=True)
            dnb_c2.markdown(f"<div class='card'><div class='card-title'>Away (DNB)</div><div class='card-value'>{odds_dnb[1]:.2f}</div></div>", unsafe_allow_html=True)


        with st.expander("📋 Interactive Lineups", expanded=False):
            col1, col2 = st.columns(2)
            with col1: display_interactive_lineup(f"{home_team_name} (Home)", "home_lineup")
            with col2: display_interactive_lineup(f"{away_team_name} (Away)", "away_lineup")

        with st.expander("👥 Full Squads", expanded=False):
            squad_col1, squad_col2 = st.columns(2)
            with squad_col1: display_squad(f"{home_team_name} (Home)", "home_squad", "home_lineup")
            with squad_col2: display_squad(f"{away_team_name} (Away)", "away_squad", "away_lineup")

        with st.expander("📅 Last 5 League Matches", expanded=False):
            match_col1, match_col2 = st.columns(2)
            with match_col1: display_last_matches(f"{home_team_name} (Home)", "home_matches")
            with match_col2: display_last_matches(f"{away_team_name} (Away)", "away_matches")

        with st.expander("📊 League Statistics", expanded=False):
            league_table = st.session_state.get("league_table")
            if isinstance(league_table, pd.DataFrame):
                stat_col1, stat_col2 = st.columns(2)
                display_team_stats(home_team_name, league_table, stat_col1)
                display_team_stats(away_team_name, league_table, stat_col2)
            else:
                st.warning("League table not available for detailed statistics.")
    
    with tab2:
        st.subheader("League Fixture Odds Calculator")
        
        margin_multi = st.slider("Apply Bookmaker's Margin (%):", 0.0, 15.0, 5.0, 0.5, format="%.1f%%", key="multi_margin")
        st.markdown("---")

        num_matches = math.ceil(len(team_list) / 2)
        
        # Create a header
        header_cols = st.columns([3, 3, 1, 1, 1])
        header_cols[0].markdown("**Home Team**")
        header_cols[1].markdown("**Away Team**")
        header_cols[2].markdown("<div class='odds-box-title' style='text-align:center;'>1</div>", unsafe_allow_html=True)
        header_cols[3].markdown("<div class='odds-box-title' style='text-align:center;'>X</div>", unsafe_allow_html=True)
        header_cols[4].markdown("<div class='odds-box-title' style='text-align:center;'>2</div>", unsafe_allow_html=True)


        for i in range(num_matches):
            cols = st.columns([3, 3, 1, 1, 1])
            
            # --- 1. Team Selection ---
            home_idx = i * 2 if (i * 2) < len(team_list) else 0
            away_idx = (i * 2) + 1 if (i * 2) + 1 < len(team_list) else 1
            
            key_h = f"multi_home_{i}"
            key_a = f"multi_away_{i}"
            
            multi_home_name = cols[0].selectbox(f"Home {i+1}", team_list, index=home_idx, key=key_h, label_visibility="collapsed")
            multi_away_name = cols[1].selectbox(f"Away {i+1}", team_list, index=away_idx, key=key_a, label_visibility="collapsed")

            # --- 2. Get Ratings ---
            try:
                multi_home_rating = home_table[home_table["Team"] == multi_home_name].iloc[0]['Rating']
                multi_away_rating = away_table[away_table["Team"] == multi_away_name].iloc[0]['Rating']
            except IndexError:
                cols[2].write("ERR")
                cols[3].write("ERR")
                cols[4].write("ERR")
                continue

            # --- 3. Calculate Probs & Odds ---
            p_h, p_d, p_a = calculate_outcome_probabilities(multi_home_rating, multi_away_rating, suggested_draw_rate)
            adj_probs = apply_overround([p_h, p_d, p_a], margin_multi)
            odds = probs_to_odds(adj_probs)

            # --- 4. Display Odds in Boxes ---
            cols[2].markdown(f"<div class='odds-box'><div class='odds-box-value'>{odds[0]:.2f}</div></div>", unsafe_allow_html=True)
            cols[3].markdown(f"<div class='odds-box'><div class='odds-box-value'>{odds[1]:.2f}</div></div>", unsafe_allow_html=True)
            cols[4].markdown(f"<div class='odds-box'><div class='odds-box-value'>{odds[2]:.2f}</div></div>", unsafe_allow_html=True)

else:
    st.info("Please select a country and league in the sidebar to begin.")
