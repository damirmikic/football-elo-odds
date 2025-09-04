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

def fetch_table(country, league, table_type="home"):
    url = f"https://www.soccer-rating.com/{country}/{league}/{table_type}/"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        rating_table_element = None
        candidate_tables = soup.find_all('table', class_='rattab')
        for table in candidate_tables:
            header = table.find('th')
            if header and table_type.capitalize() in header.get_text():
                rating_table_element = table
                break
        
        if rating_table_element:
            teams_data = []
            rows = rating_table_element.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 5:
                    team_cell = cols[1]
                    rating_cell = cols[4]
                    team_link = team_cell.find('a')

                    if team_link and team_link.has_attr('href'):
                        team_url = team_link['href']
                        rating = float(rating_cell.get_text(strip=True))
                        
                        try:
                            name_from_url = team_url.split('/')[1].replace('-', ' ')
                        except IndexError:
                            name_from_url = team_link.get_text(strip=True)
                        
                        teams_data.append({"Team": name_from_url, "Rating": rating, "URL": team_url})

            rating_table = pd.DataFrame(teams_data)
        else:
            rating_table = None

        html_io = io.StringIO(str(soup))
        all_html_tables = pd.read_html(html_io, flavor="lxml")
        expected_columns = {"Home", "Away", "Home.4", "Away.4"}
        league_table = None
        for candidate in all_html_tables:
            if expected_columns.issubset(set(candidate.columns.astype(str))):
                league_table = candidate
                break
                    
        return rating_table, league_table

    except Exception as e:
        st.error(f"Error during data fetching: {e}")
        return None, None

def find_section_header(soup, header_text):
    """More robustly finds a header tag containing specific text."""
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None

def get_correct_table(soup, target_team_name, header_text, table_id_1, table_id_2):
    """Finds the correct data table by matching the visible team name in the header."""
    header = find_section_header(soup, header_text)
    if not header:
        return None 

    team_name_row = header.find_next('tr')
    if not team_name_row:
        return None

    team_links = team_name_row.find_all('a')
    
    if len(team_links) >= 1:
        header_team1_raw = team_links[0].get_text(strip=True)
        header_team1 = re.sub(r'\s*\([^)]*\)', '', header_team1_raw).strip()
        
        tn_lower = target_team_name.lower()
        h1_lower = header_team1.lower()
        
        if tn_lower in h1_lower or h1_lower in tn_lower:
            return soup.find("table", id=table_id_1)
            
    if len(team_links) == 2:
        header_team2_raw = team_links[1].get_text(strip=True)
        header_team2 = re.sub(r'\s*\([^)]*\)', '', header_team2_raw).strip()
        
        tn_lower = target_team_name.lower()
        h2_lower = header_team2.lower()
        
        if tn_lower in h2_lower or h2_lower in tn_lower:
            return soup.find("table", id=table_id_2)
            
    return None

def fetch_team_lineup(team_name, team_table):
    def parse_lineup_table(lineup_table):
        player_list = []
        if not lineup_table: return player_list
        rows = lineup_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 4:
                try:
                    player_div = cols[1].find("div", class_="nomobil")
                    if not player_div: continue
                    img_tag = player_div.find('img')
                    full_text = (img_tag.next_sibling.strip() if img_tag and img_tag.next_sibling and isinstance(img_tag.next_sibling, str) else player_div.get_text(strip=True))
                    match = re.match(r'(.+?)\s*\((.+)\)', full_text)
                    name, position = (match.group(1).strip(), match.group(2).strip()) if match else (full_text.strip(), "N/A")
                    rating = int(cols[3].get_text(strip=True))
                    player_list.append({"name": name, "position": position, "rating": rating})
                except (ValueError, IndexError): continue
        return player_list

    try:
        team_row = team_table.loc[team_table['Team'] == team_name]
        if team_row.empty: return None
        url_suffix = team_row['URL'].iloc[0]
        team_url = f"https://www.soccer-rating.com{url_suffix}"
        response = requests.get(team_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        
        correct_table = get_correct_table(soup, team_name, 'Expected Lineup', 'line1', 'line2')
        return parse_lineup_table(correct_table)
        
    except Exception as e:
        st.error(f"An error occurred while fetching lineup for {team_name}: {e}")
        return None

def fetch_team_squad(team_name, team_table):
    def parse_squad_table(squad_table):
        player_list = []
        if not squad_table: return player_list
        rows = squad_table.find_all('tr')
        for row in rows:
            if row.find('th') or row.find('hr'): continue
            cols = row.find_all('td')
            if len(cols) == 3:
                try:
                    player_div = cols[0].find("div", class_="nomobil")
                    if not player_div: continue
                    img_tag = player_div.find('img')
                    full_text = (img_tag.next_sibling.strip() if img_tag and img_tag.next_sibling and isinstance(img_tag.next_sibling, str) else player_div.get_text(strip=True))
                    match = re.match(r'(.+?)\s*\((\d+)\)', full_text)
                    name, age = (match.group(1).strip(), int(match.group(2))) if match else (full_text, "N/A")
                    rating = int(cols[2].get_text(strip=True))
                    player_list.append({"Name": name, "Age": age, "Rating": rating})
                except (ValueError, IndexError): continue
        return player_list

    try:
        team_row = team_table.loc[team_table['Team'] == team_name]
        if team_row.empty: return None
        url_suffix = team_row['URL'].iloc[0]
        team_url = f"https://www.soccer-rating.com{url_suffix}"
        response = requests.get(team_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        
        correct_table = get_correct_table(soup, team_name, 'Squad', 'squad1', 'squad2')
        return parse_squad_table(correct_table)
        
    except Exception as e:
        st.error(f"An error occurred while fetching squad for {team_name}: {e}")
        return None

# --- UI and App Logic ---

st.markdown("""
    <style>
        body { background-color: #f4f4f9; font-family: 'Arial', sans-serif; }
        .header { font-size: 32px; color: #3b5998; font-weight: bold; text-align: center; }
        .section-header { font-size: 20px; font-weight: 600; color: #007BFF; margin-top: 20px; }
        .card { background-color: #f8f9fa; border: 1px solid #007BFF; border-radius: 8px; padding: 20px; text-align: center; margin: 10px 0; transition: transform 0.2s; }
        .card:hover { transform: scale(1.05); }
        .card-title { color: #007BFF; font-weight: bold; font-size: 18px; }
        .card-odds { font-size: 24px; font-weight: bold; color: red; }
        .player-info { font-size: 14px; }
        .player-table-header { font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">⚽ Elo Ratings Odds Calculator</div>', unsafe_allow_html=True)

if "data_fetched" not in st.session_state:
    st.info("Use the sidebar to select a country and league, then click 'Get Ratings'.")

with st.sidebar.expander("How to Use This App", expanded=True):
    st.write("1. Select Country and League.")
    st.write("2. Click 'Get Ratings' to fetch data.")
    st.write("3. Select Home and Away Teams.")
    st.write("4. Click buttons to get lineups or squads.")

st.sidebar.header("⚽ Select Match Details")
selected_country = st.sidebar.selectbox("Select Country:", list(leagues_dict.keys()), index=0)
selected_league = st.sidebar.selectbox("Select League:", leagues_dict[selected_country], index=0)

tab1, tab2, tab3 = st.tabs(["Elo Ratings Odds Calculator", "Squad", "League Table"])

with tab1:
    if st.sidebar.button("Get Ratings", key="fetch_button"):
        with st.spinner(random.choice(spinner_messages)):
            home_table, league_table = fetch_table(selected_country, selected_league, "home")
            away_table, _ = fetch_table(selected_country, selected_league, "away")
            
            if isinstance(home_table, pd.DataFrame) and isinstance(away_table, pd.DataFrame):
                st.session_state.update({
                    "home_table": home_table, "away_table": away_table,
                    "league_table": league_table, "selected_league": selected_league
                })
                for key in ['home_lineup', 'away_lineup', 'home_squad', 'away_squad']:
                    st.session_state.pop(key, None)
                st.success("Data fetched successfully!")
                st.rerun() 
            else:
                st.error("Error fetching one or both tables. Please try again.")

    if "home_table" in st.session_state:
        st.markdown('<div class="section-header">⚽ Match Details</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        home_team = col1.selectbox("Select Home Team:", st.session_state["home_table"]["Team"], key="home_team_select")
        away_team = col2.selectbox("Select Away Team:", st.session_state["away_table"]["Team"], key="away_team_select")
        
        home_rating = st.session_state["home_table"][st.session_state["home_table"]["Team"] == home_team].iloc[0]['Rating']
        away_rating = st.session_state["away_table"][st.session_state["away_table"]["Team"] == away_team].iloc[0]['Rating']
        
        home, away = 10**(home_rating / 400), 10**(away_rating / 400)
        home_win_prob, away_win_prob = home / (home + away), away / (home + away)
        
        col1, col2 = st.columns(2)
        col1.write(f"{home_team} Home Rating: {home_rating}")
        col2.write(f"{away_team} Away Rating: {away_rating}")
        
        st.markdown('<div class="section-header">Win Probability (Draw No Bet)</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.write(f"**{home_team} Win:** {home_win_prob:.2%}")
        col2.write(f"**{away_team} Win:** {away_win_prob:.2%}")
        
        d = 0.26
        if 0.01 <= home_win_prob <= 0.99:
            prob_map = {0.10: 0.14, 0.19: 0.19, 0.25: 0.22, 0.35: 0.26, 0.45: 0.28, 0.70: 0.26, 0.75: 0.22, 0.80: 0.18, 0.90: 0.16, 0.95: 0.14, 0.99: 0.11}
            for prob, draw in prob_map.items():
                if home_win_prob <= prob:
                    d = draw
                    break
        
        draw_prob = st.slider("Select Draw Probability:", 0.05, 0.4, d, 0.01)
        
        rem_prob = 1 - draw_prob
        h_win, a_win = home_win_prob * rem_prob, away_win_prob * rem_prob
        h_odds = 1 / h_win if h_win > 0 else 0
        a_odds = 1 / a_win if a_win > 0 else 0
        d_odds = 1 / draw_prob if draw_prob > 0 else 0
        
        st.markdown('<div class="section-header">1X2 Betting Odds</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='card'><div class='card-title'>Home Win (1)</div><div class='card-odds'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-odds'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='card'><div class='card-title'>Away Win (2)</div><div class='card-odds'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)

        st.markdown('<div class="section-header">📋 Interactive Lineups</div>', unsafe_allow_html=True)
        
        lineup_col1, lineup_col2 = st.columns(2)
        if lineup_col1.button(f"Get {home_team} Lineup", key="get_home_lineup"):
            with st.spinner(f"Fetching {home_team} lineup..."):
                lineup_data = fetch_team_lineup(home_team, st.session_state["home_table"])
                st.session_state['home_lineup'] = lineup_data
                if not lineup_data:
                    st.warning(f"Lineup data not found on page for {home_team}.")
                st.rerun()
        
        if lineup_col2.button(f"Get {away_team} Lineup", key="get_away_lineup"):
            with st.spinner(f"Fetching {away_team} lineup..."):
                lineup_data = fetch_team_lineup(away_team, st.session_state["away_table"])
                st.session_state['away_lineup'] = lineup_data
                if not lineup_data:
                    st.warning(f"Lineup data not found on page for {away_team}.")
                st.rerun()

        def display_interactive_lineup(team_name, team_key):
            st.subheader(f"{team_name}")
            if team_key not in st.session_state or not st.session_state[team_key]:
                st.write("Click button to fetch lineup.")
                return

            all_players = st.session_state[team_key]
            st.write("**Starters Selection:**")
            
            c1, c2, c3, c4 = st.columns([1, 4, 2, 2])
            c1.markdown('<p class="player-table-header">On</p>', unsafe_allow_html=True)
            c2.markdown('<p class="player-table-header">Player</p>', unsafe_allow_html=True)
            c3.markdown('<p class="player-table-header">Position</p>', unsafe_allow_html=True)
            c4.markdown('<p class="player-table-header">Rating</p>', unsafe_allow_html=True)

            selected_starters = []
            for i, player in enumerate(all_players):
                p_c1, p_c2, p_c3, p_c4 = st.columns([1, 4, 2, 2])
                is_starter = p_c1.checkbox(
                    f"Select {player['name']}", 
                    value=(i < 11), 
                    key=f"check_{team_key}_{player['name']}_{i}", 
                    label_visibility="collapsed"
                )
                if is_starter: selected_starters.append(player)
                p_c2.write(player['name'])
                p_c3.write(player['position'])
                p_c4.write(f"**{player['rating']}**")
            
            substitutes = [p for p in all_players if p not in selected_starters]
            num_selected = len(selected_starters)
            if num_selected != 11:
                st.warning(f"Please select exactly 11 starters ({num_selected} selected).")
            st.metric("Total Starters Rating", sum(p['rating'] for p in selected_starters))

            st.write("**Substitutes:**")
            if substitutes:
                for p in substitutes:
                    st.markdown(f"<div class='player-info'>- {p['name']} ({p['position']}) | <b>{p['rating']}</b></div>", unsafe_allow_html=True)
            else: st.write("All available players selected as starters.")

        display_col1, display_col2 = st.columns(2)
        with display_col1: display_interactive_lineup(f"{home_team} (Home)", "home_lineup")
        with display_col2: display_interactive_lineup(f"{away_team} (Away)", "away_lineup")

with tab2:
    st.header("Team Squads")
    if "home_table" in st.session_state:
        home_team = st.session_state.get('home_team_select')
        away_team = st.session_state.get('away_team_select')
        squad_col1, squad_col2 = st.columns(2)
        with squad_col1:
            st.subheader(f"{home_team} (Home)")
            if st.button(f"Get {home_team} Squad", key="get_home_squad"):
                with st.spinner(f"Fetching {home_team} squad..."):
                    squad_data = fetch_team_squad(home_team, st.session_state["home_table"])
                    if squad_data:
                        st.session_state['home_squad'] = pd.DataFrame(squad_data)
                    else:
                        st.session_state['home_squad'] = pd.DataFrame()
                        st.warning(f"Squad data not found on page for {home_team}.")
                    st.rerun()
            if 'home_squad' in st.session_state and not st.session_state['home_squad'].empty:
                st.dataframe(st.session_state['home_squad'], use_container_width=True)
        with squad_col2:
            st.subheader(f"{away_team} (Away)")
            if st.button(f"Get {away_team} Squad", key="get_away_squad"):
                with st.spinner(f"Fetching {away_team} squad..."):
                    squad_data = fetch_team_squad(away_team, st.session_state["away_table"])
                    if squad_data:
                        st.session_state['away_squad'] = pd.DataFrame(squad_data)
                    else:
                        st.session_state['away_squad'] = pd.DataFrame()
                        st.warning(f"Squad data not found on page for {away_team}.")
                    st.rerun()
            if 'away_squad' in st.session_state and not st.session_state['away_squad'].empty:
                st.dataframe(st.session_state['away_squad'], use_container_width=True)
    else:
        st.write("Please fetch ratings on the main tab first.")

with tab3:
    st.header("League Table")
    if "league_table" in st.session_state and st.session_state["league_table"] is not None:
        st.dataframe(st.session_state["league_table"])
    else:
        st.write("No league table data available. Please fetch ratings first.")

