import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
import math
import random
import time
import re
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


SPINNER_MESSAGES = [
# ... (rest of constants) ...
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

def load_css(file_name):
# ... (rest of function) ...
    """Loads a CSS file and injects it into the Streamlit app."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please add it to the app directory.")

def fetch_with_headers(url, referer=None, timeout=15):
    headers = BASE_HEADERS.copy()
    headers["Referer"] = referer or "https://www.soccer-rating.com/"
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response

# --- Helper Functions ---
def normalize_team_name(name):
# ... (rest of function) ...
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
def fetch_soccerstats_data():
    """
    Fetches and parses league-wide statistics (Draw %, Avg Goals)
    from soccerstats.com to be used for better draw probability estimates.
    """
    url = "https://www.soccerstats.com/leagues.asp"
    try:
        response = fetch_with_headers(url, referer="https://www.soccerstats.com/")
        soup = BeautifulSoup(response.text, "lxml")
        
        table = soup.find("table", id="btable")
        if not table:
            return None

        league_stats = []
        for row in table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 8:
                continue
            
            try:
                # Clean and split league name
                league_full = cols[0].get_text(strip=True)
                if ' - ' not in league_full:
                    continue
                country, league_name = league_full.split(' - ', 1)
                
                # Clean and convert draw string
                draw_str = cols[5].get_text(strip=True)
                draw_pct = float(draw_str.replace('%', ''))
                
                # Clean and convert goals string
                goals_str = cols[7].get_text(strip=True)
                avg_goals = float(goals_str)

                league_stats.append({
                    "Country": country,
                    "LeagueName": league_name,
                    "Draws": draw_pct,
                    "AvgGoals": avg_goals
                })
            except (ValueError, TypeError):
                # Skip rows with invalid data (e.g., '-', or non-numeric)
                continue
        
        return pd.DataFrame(league_stats)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def fetch_table_data(country, league):
# ... (rest of function) ...
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

def find_section_header(soup, header_text):
# ... (rest of function) ...
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None


def get_correct_table(soup, target_team_name, target_team_url, header_text, table_id_1, table_id_2):
# ... (rest of function) ...
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
# ... (rest of function) ...
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
    Tries to find the exact league draw rate from the scraped soccerstats.com data.
    It maps the selected league (e.g., "England", "UK2") to the corresponding
    entry in the soccerstats DataFrame.
    """
    DEFAULT_DRAW_RATE = 0.27
    try:
        soccer_stats_df = st.session_state.get("soccer_stats")
        if soccer_stats_df is None or soccer_stats_df.empty:
            return DEFAULT_DRAW_RATE

        # Get the list of leagues for the selected country from our app's dictionary
        league_list = all_leagues[selected_country]
        
        # Normalize country name for matching (e.g., "USA-Women" -> "USA")
        stats_country_name = selected_country.split('-')[0]

        # Filter stats by the matched country name
        leagues_for_country_stats = soccer_stats_df[
            soccer_stats_df['Country'].str.contains(stats_country_name, case=False)
        ].reset_index()

        if leagues_for_country_stats.empty:
            return DEFAULT_DRAW_RATE

        # Find the index of the selected league (e.g., "UK1" is 0, "UK2" is 1)
        league_index = league_list.index(selected_league)

        # If we have a stat row corresponding to that index, use it
        if league_index < len(leagues_for_country_stats):
            matched_rate = leagues_for_country_stats.iloc[league_index]['Draws']
            return matched_rate / 100.0  # Convert 30.0 to 0.30
        else:
            # Fallback: If we selected a lower league (e.g., UK5) that soccerstats
            # doesn't list, just use the draw rate of the country's primary league.
            return leagues_for_country_stats.iloc[0]['Draws'] / 100.0

    except Exception:
        # Broad fallback in case of any error
        return DEFAULT_DRAW_RATE

#
# REMOVED: This was a bad copy-paste of the function above
# (The entire try...except block that was here is now gone)
#

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

# --- UI Display Functions ---

def display_team_stats(team_name, table, column):
# ... (rest of function) ...
    """Displays key league stats for a selected team in a given column."""
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

def display_interactive_lineup(team_name, team_key):
# ... (rest of function) ...
    """Renders the interactive lineup selector for a team."""
    st.subheader(f"{team_name}")
    lineup_data = st.session_state.get(team_key)
    if not lineup_data: 
        st.warning("Lineup data not available.")
        return
    
    header_cols = st.columns([1, 4, 2, 2, 2])
    header_cols[0].markdown('<p class="player-table-header">On</p>', unsafe_allow_html=True)
    header_cols[1].markdown('<p class="player-table-header">Player</p>', unsafe_allow_html=True)
    header_cols[2].markdown('<p class="player-table-header">Position</p>', unsafe_allow_html=True)
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
    
    # ... (rest of lineup analysis) ...

def display_squad(team_name, squad_key, lineup_key):
# ... (rest of function) ...
    """Renders the full squad list."""
    st.subheader(f"{team_name}")
    squad_data = st.session_state.get(squad_key)
    if not squad_data: 
        st.warning("Squad data not available.")
        return

    starter_names = {p['name'] for p in st.session_state.get(lineup_key, [])[:11]}
    for p in squad_data:
        player_cols = st.columns([4, 2, 2])
        player_cols[0].write(f"**{p['name']}**" if p['name'] in starter_names else p['name'])
        player_cols[1].write(str(p['age']))
        player_cols[2].write(f"**{p['rating']}**")

def display_last_matches(team_name, matches_key):
# ... (rest of function) ...
    """Renders the last 5 league matches for a team."""
    st.subheader(f"{team_name}")
    matches_data = st.session_state.get(matches_key)
    if not matches_data or not matches_data["matches"]: 
        st.warning("Recent match data not available.")
        return
    st.metric("Points in Last 5 League Matches", matches_data["points"])
    for match in matches_data["matches"]:
        match_date = match['date']
        opponent = match['opponent']
        result = match['result']
        st.markdown(
            f"<div class='match-line'>"
            f"<span class='match-date'>{match_date}</span>"
            f"<span class='match-opponent'>{opponent}</span>"
            f"<span class='match-result'>{result}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

# --- UI Styling & App Layout ---

# Load custom CSS
load_css("style.css")

st.markdown(
# ... (rest of markdown) ...
    """
    <div class="header">⚽ Elo Ratings Odds Studio</div>
    <div class="subheader">Track live ratings, surface the sharpest prices, and dive into form in one polished workspace.</div>
    """,
    unsafe_allow_html=True
)

with st.sidebar.expander("✨ Quick Guide", expanded=True):
# ... (rest of markdown) ...
    st.markdown(
        """
        - Select a **country + league** to pull the freshest ratings snapshot.
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
        with st.spinner(random.choice(SPINNER_MESSAGES)):
            home_table, away_table, league_table = fetch_table_data(country, league)
            soccer_stats_df = fetch_soccerstats_data() # Fetch new stats
            
            if isinstance(home_table, pd.DataFrame) and not home_table.empty:
                st.session_state.update({
                    "home_table": home_table,
                    "away_table": away_table,
                    "league_table": league_table,
                    "soccer_stats": soccer_stats_df, # Store new stats
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


# --- Main Content Area ---
if st.session_state.get('data_fetched', False):
    home_table = st.session_state.home_table
    away_table = st.session_state.away_table
    league_table = st.session_state.get("league_table")

    last_refresh = st.session_state.get("last_refresh")
    if last_refresh:
        refresh_text = datetime.utcfromtimestamp(last_refresh).strftime("%d %b %Y %H:%M UTC")
    else:
        refresh_text = "Awaiting refresh"

    st.markdown(
# ... (rest of markdown) ...
        f"""
        <div class="hero-card">
            <div class="hero-title">{selected_country} · {selected_league}</div>
            <div class="hero-subtitle">Explore the live blend of Elo strength, bookmaker prices, and matchup context.</div>
            <div class="hero-meta">
                <span class="hero-pill">Last synced: {refresh_text}</span>
                <span class="hero-pill">Interactive odds modelling</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Global Odds Inputs (Used by both tabs) ---
    with st.expander("📈 Analysis Inputs", expanded=True):
        # We need a default team selection for the initial rating display
        # This will be updated inside the "Single Match" tab
        default_home_team = home_table["Team"].iloc[0]
        default_away_team = away_table["Team"].iloc[0]

        home_team_name_from_state = st.session_state.get("home_team_select", default_home_team)
        away_team_name_from_state = st.session_state.get("away_team_select", default_away_team)
        
        # --- FIX for IndexError ---
        # Check if the team from session state is actually in the NEW table. 
        # If not, fall back to the default team for this league.
        if home_team_name_from_state in home_table["Team"].values:
            home_team_name_for_ratings = home_team_name_from_state
        else:
            home_team_name_for_ratings = default_home_team

        if away_team_name_from_state in away_table["Team"].values:
            away_team_name_for_ratings = away_team_name_from_state
        else:
            away_team_name_for_ratings = default_away_team
        # --- END FIX ---
        
        home_rating = home_table[home_table["Team"] == home_team_name_for_ratings].iloc[0]['Rating']
        away_rating = away_table[away_table["Team"] == away_team_name_for_ratings].iloc[0]['Rating']
        
        c1, c2 = st.columns(2)
        c1.metric(f"{home_team_name_for_ratings} Rating", f"{home_rating:.2f}")
        c2.metric(f"{away_team_name_for_ratings} Rating", f"{away_rating:.2f}")
        st.caption(f"Ratings displayed are for the teams selected in the 'Single Match Analysis' tab.")

        st.markdown("---")
        # Updated to pass the selected league info
        suggested_draw_rate = get_league_suggested_draw_rate(selected_country, selected_league)
        col_slider, col_info = st.columns([3, 1])
        
        draw_probability = col_slider.slider("Set Draw Probability:", 0.15, 0.45, suggested_draw_rate, 0.01, "%.2f", key="global_draw_prob")
        col_info.metric("League Avg", f"{suggested_draw_rate:.1%}")
        
        # margin = st.slider("Apply Global Bookmaker's Margin (%):", 0, 15, 5, 1, key="global_margin")
        # margin_decimal = margin / 100.0


    # --- Analysis Tabs ---
    tab1, tab2 = st.tabs(["Single Match Analysis", "Multi-Match Calculator"])

    with tab1:
        with st.expander("⚽ Matchup", expanded=True):
            col1, col2 = st.columns(2)
            home_team_name = col1.selectbox("Select Home Team:", home_table["Team"], key="home_team_select")
            away_team_name = col2.selectbox("Select Away Team:", away_table["Team"], key="away_team_select")
            
            home_team_data = home_table[home_table["Team"] == home_team_name].iloc[0]
            away_team_data = away_table[away_table["Team"] == away_team_name].iloc[0]
            
            # This triggers a rerun if the *ratings* in the global box need to update
            if (home_team_name != home_team_name_for_ratings) or (away_team_name != away_team_name_for_ratings):
                st.rerun()

        # --- Refactored Team Data Fetching ---
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
                
                time.sleep(1) # Keep the 1-second sleep for smoother UX
                st.rerun()
        # --- End Refactor ---

        with st.expander("🎯 Calculated Odds (Single Match)", expanded=True):
            p_home, p_draw, p_away = calculate_outcome_probabilities(home_rating, away_rating, draw_probability)
            
            st.markdown(f"**Calculated Fair Probabilities**")
            prob_cols = st.columns(3)
            prob_cols[0].metric("Home Win", f"{p_home:.2%}")
            prob_cols[1].metric("Draw", f"{p_draw:.2%}")
            prob_cols[2].metric("Away Win", f"{p_away:.2%}")
            
            st.markdown("---")
            # ADDED: Margin slider for this tab
            margin_single = st.slider("Apply Bookmaker's Margin (%):", 0, 15, 5, 1, key="single_margin")
            margin_decimal_single = margin_single / 100.0
            
            h_odds = 1 / (p_home * (1 + margin_decimal_single)) if p_home > 0 else 0
            d_odds = 1 / (p_draw * (1 + margin_decimal_single)) if p_draw > 0 else 0
            a_odds = 1 / (p_away * (1 + margin_decimal_single)) if p_away > 0 else 0
            
            st.write("**Calculated Odds with Margin:**")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='card'><div class='card-title'>Home (1)</div><div class='card-value'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-value'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='card'><div class='card-title'>Away (2)</div><div class='card-value'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)

            st.markdown("---")
            st.write("**Draw No Bet Odds:**")
            p_dnb_home = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0
            dnb_h_odds = 1 / (p_dnb_home * (1 + margin_decimal_single)) if p_dnb_home > 0 else 0
            dnb_a_odds = 1 / ((1 - p_dnb_home) * (1 + margin_decimal_single)) if (1-p_dnb_home) > 0 else 0
            dnb_c1, dnb_c2 = st.columns(2)
            dnb_c1.markdown(f"<div class='card'><div class='card-title'>Home (DNB)</div><div class='card-value'>{dnb_h_odds:.2f}</div></div>", unsafe_allow_html=True)
            dnb_c2.markdown(f"<div class='card'><div class='card-title'>Away (DNB)</div><div class='card-value'>{dnb_a_odds:.2f}</div></div>", unsafe_allow_html=True)

        with st.expander("📊 Team Statistics", expanded=False):
            if isinstance(league_table, pd.DataFrame):
                stat_col1, stat_col2 = st.columns(2)
                display_team_stats(home_team_name, league_table, stat_col1)
                display_team_stats(away_team_name, league_table, stat_col2)
            else:
                st.warning("League table not available for detailed statistics.")

        with st.expander("📋 Interactive Lineups", expanded=True):
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
    
    with tab2:
        st.subheader("Multi-Match Odds Viewer")
        st.write("Select matchups to see the calculated odds. The Draw % and Margin % from the inputs above will be applied.")

        # ADDED: Margin slider for this tab
        margin_multi = st.slider("Apply Bookmaker's Margin (%):", 0, 15, 5, 1, key="multi_margin")
        margin_decimal_multi = margin_multi / 100.0

        team_list = ["---"] + sorted(home_table["Team"].unique())
        num_teams = len(team_list) - 1
        num_rows = math.ceil(num_teams / 2)
        
        # REMOVED: pick_options and selections

        # New layout with headers
        st.markdown("---")
        header_cols = st.columns([3, 3, 2, 2, 2])
        header_cols[0].markdown("**Home Team**")
        header_cols[1].markdown("**Away Team**")
        header_cols[2].markdown("<div class='odds-display'><b>Home (1)</b></div>", unsafe_allow_html=True)
        header_cols[3].markdown("<div class='odds-display'><b>Draw (X)</b></div>", unsafe_allow_html=True)
        header_cols[4].markdown("<div class='odds-display'><b>Away (2)</b></div>", unsafe_allow_html=True)


        for i in range(num_rows):
            cols = st.columns([3, 3, 2, 2, 2])
            with cols[0]:
                home_selection = st.selectbox("Home Team", team_list, key=f"multi_home_{i}", index=0, label_visibility="collapsed")
            with cols[1]:
                away_selection = st.selectbox("Away Team", team_list, key=f"multi_away_{i}", index=0, label_visibility="collapsed")
            
            # Placeholders for odds
            odds_1_col = cols[2]
            odds_x_col = cols[3]
            odds_2_col = cols[4]

            # REMOVED: pick_selection
            
            # Now, calculate and display odds if teams are selected
            if home_selection != "---" and away_selection != "---":
                try:
                    home_rating = home_table[home_table["Team"] == home_selection].iloc[0]['Rating']
                    away_rating = away_table[away_table["Team"] == away_selection].iloc[0]['Rating']
                    
                    p_home, p_draw, p_away = calculate_outcome_probabilities(home_rating, away_rating, draw_probability)
                    
                    h_odds = 1 / (p_home * (1 + margin_decimal_multi)) if p_home > 0 else 0
                    d_odds = 1 / (p_draw * (1 + margin_decimal_multi)) if p_draw > 0 else 0
                    a_odds = 1 / (p_away * (1 + margin_decimal_multi)) if p_away > 0 else 0

                    # Use new .odds-box style
                    odds_1_col.markdown(f"<div class='odds-box'><div class='odds-box-title'>1</div><div class='odds-box-value'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
                    odds_x_col.markdown(f"<div class='odds-box'><div class='odds-box-title'>X</div><div class='odds-box-value'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
                    odds_2_col.markdown(f"<div class='odds-box'><div class='odds-box-title'>2</div><div class='odds-box-value'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)
                    
                    # REMOVED: Add to selections block

                except Exception:
                    # Handle error if team not found (shouldn't happen)
                    odds_1_col.markdown("<div class='odds-box'><div class='odds-box-value'>Err</div></div>", unsafe_allow_html=True)
                    odds_x_col.markdown("<div class='odds-box'><div class='odds-box-value'>Err</div></div>", unsafe_allow_html=True)
                    odds_2_col.markdown("<div class='odds-box'><div class='odds-box-value'>Err</div></div>", unsafe_allow_html=True)
            else:
                # Show empty boxes
                odds_1_col.markdown("<div class='odds-box'><div class='odds-box-value'>-</div></div>", unsafe_allow_html=True)
                odds_x_col.markdown("<div class='odds-box'><div class='odds-box-value'>-</div></div>", unsafe_allow_html=True)
                odds_2_col.markdown("<div class='odds-box'><div class='odds-box-value'>-</div></div>", unsafe_allow_html=True)

        
        st.markdown("---")
        # REMOVED: "Calculate Parlay Odds" button and all related logic


else:
    st.info("Please select a country and league in the sidebar to begin.")
