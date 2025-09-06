import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
import math
import random
import time
import re

# Set page title and icon
st.set_page_config(page_title="Elo Ratings Odds Calculator", page_icon="odds_icon.png")

# Dictionary of countries and leagues
leagues_dict = {
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
    "Denmark": ["DK1", "DK2", "DK3G1", "DK3G2"],
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
}
spinner_messages = [
    "Fetching the latest football ratings...",
    "Hold tight, we're gathering the data...",
    "Just a moment, crunching the numbers...",
    "Loading the football magic...",
    "Almost there, preparing the stats..."
]

# --- Helper Functions ---
def normalize_team_name(name):
    """Robustly cleans and standardizes a team name for reliable matching."""
    if not isinstance(name, str): return ""
    name = name.lower()
    name = name.replace('ö', 'oe').replace('ü', 'ue').replace('ä', 'ae')
    name = name.replace('ø', 'oe').replace('å', 'aa').replace('æ', 'ae')
    name = re.sub(r'[\&\-\.]+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return ' '.join(name.split())

# --- Data Fetching and Parsing Functions ---

@st.cache_data(ttl=3600)
def fetch_table_data(country, league):
    """Fetches and parses ratings and league table in one go."""
    home_url = f"https://www.soccer-rating.com/{country}/{league}/home/"
    away_url = f"https://www.soccer-rating.com/{country}/{league}/away/"
    try:
        response_home = requests.get(home_url, headers={"User-Agent": "Mozilla/5.0"})
        response_home.raise_for_status()
        soup_home = BeautifulSoup(response_home.text, "lxml")
        
        response_away = requests.get(away_url, headers={"User-Agent": "Mozilla/5.0"})
        response_away.raise_for_status()
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
        expected_columns = {"M", "P.", "Goals", "Home", "Away", "Home.4", "Away.4"}
        for candidate in all_html_tables:
            if expected_columns.issubset(set(candidate.columns.astype(str))):
                league_table = candidate
                break
        return home_rating_table, away_rating_table, league_table
    except Exception:
        return None, None, None

def find_section_header(soup, header_text):
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None

def get_correct_table_by_url(soup, target_team_url, header_text, table_id_1, table_id_2):
    """Finds the correct data table by matching the team's unique URL."""
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
            
    return None

@st.cache_data(ttl=3600)
def fetch_team_page_data(team_name, team_url):
    """Fetches lineup, squad, and last matches from a single team page visit."""
    try:
        url = f"https://www.soccer-rating.com{team_url}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # --- Parse Lineup ---
        lineup_table = get_correct_table_by_url(soup, team_url, 'Expected Lineup', 'line1', 'line2')
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
        
        # --- Parse Squad ---
        squad_table = get_correct_table_by_url(soup, team_url, 'Squad', 'squad1', 'squad2')
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
        
        # --- Parse Last Matches ---
        last_matches_data = []
        points = 0
        matches_table = soup.find('table', {'class': 'bigtable', 'cellspacing': '0'})
        if matches_table:
            league_matches_count = 0
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
                            is_home_match = team_name in opponent.split('-')[0]
                            if (is_home_match and own_score > opp_score) or (not is_home_match and opp_score > own_score):
                                points += 3
                            elif own_score == opp_score:
                                points += 1
                        except (ValueError, IndexError): pass
                        league_matches_count += 1

        return lineup_data, squad_data, {"matches": last_matches_data, "points": points}

    except Exception:
        return None, None, None

def calculate_elo_based_draw(home_win_prob):
    """Estimates draw probability based on home team's win probability."""
    if 0.01 <= home_win_prob <= 0.99:
        prob_map = {0.10: 0.14, 0.19: 0.19, 0.25: 0.22, 0.35: 0.26, 0.45: 0.28, 0.70: 0.26, 0.75: 0.22, 0.80: 0.18, 0.90: 0.16, 0.95: 0.14, 0.99: 0.11}
        for prob, draw in prob_map.items():
            if home_win_prob <= prob:
                return draw
    return 0.26

def calculate_poisson_draw_prob(home_team_name, away_team_name, league_table):
    """Calculates draw probability using Poisson distribution."""
    try:
        total_home_goals, total_away_goals, total_matches = 0, 0, 0
        for i, row in league_table.iterrows():
            try:
                home_matches = int(row['Home'])
                home_gf, _ = map(int, row['Home.4'].split(':'))
                away_gf, _ = map(int, row['Away.4'].split(':'))
                total_home_goals += home_gf
                total_away_goals += away_gf
                total_matches += home_matches
            except (ValueError, TypeError): continue
        if total_matches == 0: return 0.25, None, None
        
        avg_league_home_goals = total_home_goals / total_matches
        avg_league_away_goals = total_away_goals / total_matches

        home_team_row = league_table[league_table.iloc[:, 1].apply(normalize_team_name) == normalize_team_name(home_team_name)].iloc[0]
        away_team_row = league_table[league_table.iloc[:, 1].apply(normalize_team_name) == normalize_team_name(away_team_name)].iloc[0]

        home_gf_h, home_ga_h = map(int, home_team_row['Home.4'].split(':'))
        away_gf_a, away_ga_a = map(int, away_team_row['Away.4'].split(':'))
        home_matches_h = int(home_team_row['Home'])
        away_matches_a = int(away_team_row['Away'])

        home_attack = (home_gf_h / home_matches_h) / avg_league_home_goals
        away_defense = (away_ga_a / away_matches_a) / avg_league_home_goals
        home_exp_goals = home_attack * away_defense * avg_league_home_goals

        away_attack = (away_gf_a / away_matches_a) / avg_league_away_goals
        home_defense = (home_ga_h / home_matches_h) / avg_league_away_goals
        away_exp_goals = away_attack * home_defense * avg_league_away_goals

        draw_prob = sum(((home_exp_goals**i * math.exp(-home_exp_goals)) / math.factorial(i)) * \
                        ((away_exp_goals**i * math.exp(-away_exp_goals)) / math.factorial(i)) for i in range(6))
        return draw_prob, home_exp_goals, away_exp_goals
    except (IndexError, ValueError, KeyError, ZeroDivisionError):
        return 0.25, None, None

# --- UI Styling ---
st.markdown("""
    <style>
        body { background-color: #f4f4f9; font-family: 'Arial', sans-serif; }
        .header { font-size: 32px; color: #3b5998; font-weight: bold; text-align: center; }
        .section-header { font-size: 20px; font-weight: 600; color: #007BFF; margin-top: 20px; border-bottom: 2px solid #007BFF; padding-bottom: 5px; }
        .card { background-color: #f8f9fa; border: 1px solid #007BFF; border-radius: 8px; padding: 15px; text-align: center; margin: 10px 0;}
        .card-title { color: #007BFF; font-weight: bold; font-size: 16px; }
        .card-value { font-size: 22px; font-weight: bold; color: #333; }
        .player-table-header { font-weight: bold; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- App Header and Sidebar ---
st.markdown('<div class="header">⚽ Elo Ratings Odds Calculator</div>', unsafe_allow_html=True)

with st.sidebar.expander("How to Use This App", expanded=True):
    st.write("1. **Select Country and League**.")
    st.write("2. **Click 'Get Ratings'** to load data.")
    st.write("3. **Select Teams** for analysis.")
    st.write("4. Data is fetched automatically.")

st.sidebar.header("⚽ Select Match Details")
selected_country = st.sidebar.selectbox("Select Country:", list(leagues_dict.keys()), index=0)
selected_league = st.sidebar.selectbox("Select League:", leagues_dict[selected_country], index=0)

# --- Main App Logic ---
if st.sidebar.button("Get Ratings", key="fetch_button"):
    with st.spinner(random.choice(spinner_messages)):
        home_table, away_table, league_table = fetch_table_data(selected_country, selected_league)
        if isinstance(home_table, pd.DataFrame) and isinstance(away_table, pd.DataFrame):
            st.session_state.update({
                "home_table": home_table, "away_table": away_table,
                "league_table": league_table, "data_fetched": True
            })
            for key in ['home_lineup', 'away_lineup', 'home_squad', 'away_squad', 'home_matches', 'away_matches']: 
                st.session_state.pop(key, None)
            st.rerun() 
        else:
            st.error("Error fetching data. Source may be unavailable or structure changed.")
            st.session_state['data_fetched'] = False

if st.session_state.get('data_fetched', False):
    home_table = st.session_state["home_table"]
    away_table = st.session_state["away_table"]
    league_table = st.session_state.get("league_table")

    st.markdown('<div class="section-header">⚽ Matchup</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    home_team_name = col1.selectbox("Select Home Team:", home_table["Team"], key="home_team_select")
    away_team_name = col2.selectbox("Select Away Team:", away_table["Team"], key="away_team_select")

    home_team_data = home_table[home_table["Team"] == home_team_name].iloc[0]
    away_team_data = away_table[away_table["Team"] == away_team_name].iloc[0]

    if 'last_home_team' not in st.session_state or st.session_state.last_home_team != home_team_name:
        with st.spinner(f"Fetching {home_team_name} data..."):
            lineup, squad, matches = fetch_team_page_data(home_team_name, home_team_data['URL'])
            st.session_state.update({
                'home_lineup': lineup, 'home_squad': squad, 'home_matches': matches,
                'last_home_team': home_team_name
            })
            time.sleep(1)
            st.rerun()

    if 'last_away_team' not in st.session_state or st.session_state.last_away_team != away_team_name:
        with st.spinner(f"Fetching {away_team_name} data..."):
            lineup, squad, matches = fetch_team_page_data(away_team_name, away_team_data['URL'])
            st.session_state.update({
                'away_lineup': lineup, 'away_squad': squad, 'away_matches': matches,
                'last_away_team': away_team_name
            })
            st.rerun()

    with st.expander("📊 Team Statistics", expanded=False):
        if isinstance(league_table, pd.DataFrame):
            stat_col1, stat_col2 = st.columns(2)
            def display_team_stats(team_name, table, column):
                try:
                    normalized_target = normalize_team_name(team_name)
                    table['normalized_name'] = table.iloc[:, 1].apply(normalize_team_name)
                    team_stats_row = table[table['normalized_name'] == normalized_target]
                    if team_stats_row.empty:
                        column.warning(f"Stats not found for {team_name}.")
                        return 0
                    team_stats = team_stats_row.iloc[0]
                    column.markdown(f"**{team_name}**")
                    column.metric(label="League Position", value=f"#{int(team_stats.iloc[0])}")
                    matches, points = int(team_stats['M']), int(team_stats['P.'])
                    gf, ga = map(int, team_stats['Goals'].split(':'))
                    column.markdown(f"**Global Averages**")
                    column.metric(label="Avg. Goals Scored", value=f"{gf/matches:.2f}")
                    column.metric(label="Avg. Goals Conceded", value=f"{ga/matches:.2f}")
                    column.metric(label="Avg. Goals per Match", value=f"{(gf + ga)/matches:.2f}")
                    column.metric(label="Avg. Points per Game", value=f"{points/matches:.2f}")
                    return matches
                except (IndexError, ValueError, KeyError, TypeError):
                    column.warning(f"Statistics unavailable for {team_name}.")
                    return 0
            matches_played = display_team_stats(home_team_name, league_table, stat_col1)
            display_team_stats(away_team_name, league_table, stat_col2)
        else:
            st.warning("League table not available for detailed statistics.")

    with st.expander("📈 Odds Analysis", expanded=True):
        home_rating, away_rating = home_team_data['Rating'], away_team_data['Rating']
        home, away = 10**(home_rating / 400), 10**(away_rating / 400)
        home_win_prob, away_win_prob = home / (home + away), away / (home + away)
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{home_team_name} Rating", f"{home_rating:.2f}")
        c3.metric(f"{away_team_name} Rating", f"{away_rating:.2f}")
        
        draw_model_info = ""
        matches_played = 0
        if isinstance(league_table, pd.DataFrame):
             normalized_target = normalize_team_name(home_team_name)
             league_table['normalized_name'] = league_table.iloc[:, 1].apply(normalize_team_name)
             team_stats_row = league_table[league_table['normalized_name'] == normalized_target]
             if not team_stats_row.empty:
                 matches_played = int(team_stats_row.iloc[0]['M'])

        if isinstance(league_table, pd.DataFrame) and matches_played >= 6:
            draw_model_info = "*(Using Poisson Model)*"
            poisson_draw, home_xg, away_xg = calculate_poisson_draw_prob(home_team_name, away_team_name, league_table)
            if home_xg is not None:
                c2.markdown(f"<div class='card' style='margin-top:0;'><div class='card-title'>Expected Goals (xG)</div><div class='card-value'>{home_xg:.2f} : {away_xg:.2f}</div></div>", unsafe_allow_html=True)
            default_draw = poisson_draw
        else:
            draw_model_info = "*(Using Elo-based estimate)*"
            default_draw = calculate_elo_based_draw(home_win_prob)

        st.markdown(f"**Draw Probability** {draw_model_info}")
        draw_prob = st.slider("Select Draw Probability", 0.05, 0.4, default_draw, 0.01, help=f"Data-driven estimate is {default_draw:.2%}", label_visibility="collapsed")
        
        h_win, a_win = home_win_prob * (1 - draw_prob), away_win_prob * (1 - draw_prob)
        h_odds, a_odds, d_odds = (1/p if p > 0 else 0 for p in [h_win, a_win, draw_prob])
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='card'><div class='card-title'>Home Win (1)</div><div class='card-value'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-value'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='card'><div class='card-title'>Away Win (2)</div><div class='card-value'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)

    with st.expander("📋 Interactive Lineups", expanded=True):
        def display_interactive_lineup(team_name, team_key):
            st.subheader(f"{team_name}")
            lineup_data = st.session_state.get(team_key)
            if lineup_data is None: st.info("Fetching lineup...")
            elif not lineup_data: st.warning("Lineup data not available.")
            else:
                c1, c2, c3, c4, c5 = st.columns([1, 4, 2, 2, 2])
                for col, title in zip([c1, c2, c3, c4, c5], ["On", "Player", "Position", "M/G", "Rating"]):
                    col.markdown(f'<p class="player-table-header">{title}</p>', unsafe_allow_html=True)

                selected_starters = []
                for i, player in enumerate(lineup_data):
                    p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns([1, 4, 2, 2, 2])
                    is_starter = p_c1.checkbox("", value=(i < 11), key=f"check_{team_key}_{i}", label_visibility="collapsed")
                    if is_starter: selected_starters.append(player)
                    p_c2.write(player['name'])
                    p_c3.write(player['position'])
                    p_c4.write(player['stats'])
                    p_c5.write(f"**{player['rating']}**")
                
                num_selected = len(selected_starters)
                if num_selected != 11: st.warning(f"Please select exactly 11 starters ({num_selected} selected).")
                
                total_matches, total_goals = 0, 0
                for player in selected_starters:
                    try:
                        matches, goals = map(int, player['stats'].split('/'))
                        total_matches += matches
                        total_goals += goals
                    except (ValueError, AttributeError): pass 
                
                starters_rating_sum = sum(p['rating'] for p in selected_starters)
                avg_rating = starters_rating_sum / num_selected if num_selected > 0 else 0
                
                st.markdown("---")
                st.write("**Starting Lineup Analysis**")
                m1, m2 = st.columns(2)
                m3, m4 = st.columns(2)
                m1.metric("Total Starters Rating", starters_rating_sum)
                m2.metric("Average Starter Rating", f"{avg_rating:.2f}")
                m3.metric("Total Matches (Starters)", total_matches)
                m4.metric("Total Goals (Starters)", total_goals)

        col1, col2 = st.columns(2)
        with col1: display_interactive_lineup(f"{home_team_name} (Home)", "home_lineup")
        with col2: display_interactive_lineup(f"{away_team_name} (Away)", "away_lineup")

    with st.expander("👥 Full Squads", expanded=False):
        def display_squad(team_name, squad_key):
            st.subheader(f"{team_name}")
            squad_data = st.session_state.get(squad_key)
            if squad_data is None: st.info("Fetching squad...")
            elif not squad_data: st.warning("Squad data not available.")
            else:
                c1, c2, c3 = st.columns([4, 2, 2])
                for col, title in zip([c1, c2, c3], ["Player", "Age", "Rating"]):
                    col.markdown(f'<p class="player-table-header">{title}</p>', unsafe_allow_html=True)
                for player in squad_data:
                    p_c1, p_c2, p_c3 = st.columns([4, 2, 2])
                    p_c1.write(player['name'])
                    p_c2.write(player['age'])
                    p_c3.write(f"**{player['rating']}**")

        col1, col2 = st.columns(2)
        with col1: display_squad(f"{home_team_name} (Home)", "home_squad")
        with col2: display_squad(f"{away_team_name} (Away)", "away_squad")

    with st.expander("📅 Last 5 League Matches", expanded=False):
        def display_last_matches(team_name, matches_key):
            st.subheader(f"{team_name}")
            matches_data = st.session_state.get(matches_key)
            if matches_data is None: st.info("Fetching matches...")
            elif not matches_data["matches"]: st.warning("Recent match data not available.")
            else:
                st.metric("Points in Last 5 League Matches", matches_data["points"])
                for match in matches_data["matches"]:
                    st.text(f"{match['date']}: {match['opponent']}  ({match['result']})")
        
        col1, col2 = st.columns(2)
        with col1: display_last_matches(f"{home_team_name} (Home)", "home_matches")
        with col2: display_last_matches(f"{away_team_name} (Away)", "away_matches")

else:
    st.info("Please click 'Get Ratings' in the sidebar to begin.")

