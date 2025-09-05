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

# --- Data Fetching and Parsing Functions ---

@st.cache_data(ttl=3600) # Cache data for 1 hour
def fetch_table(country, league, table_type="home"):
    """Fetches and parses the main ratings table and the league table."""
    url = f"https://www.soccer-rating.com/{country}/{league}/{table_type}/"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Parse Ratings Table
        rating_table_element = None
        for table in soup.find_all('table', class_='rattab'):
            header = table.find('th')
            if header and table_type.capitalize() in header.get_text():
                rating_table_element = table
                break
        
        rating_table = None
        if rating_table_element:
            teams_data = []
            for row in rating_table_element.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) == 5:
                    team_link = cols[1].find('a')
                    if team_link and team_link.has_attr('href'):
                        team_url = team_link['href']
                        name_from_url = team_url.split('/')[1].replace('-', ' ')
                        rating = float(cols[4].get_text(strip=True))
                        teams_data.append({"Team": name_from_url, "Rating": rating, "URL": team_url})
            rating_table = pd.DataFrame(teams_data)

        # Parse League Table
        league_table = None
        html_io = io.StringIO(str(soup))
        all_html_tables = pd.read_html(html_io, flavor="lxml")
        expected_columns = {"Home", "Away", "Home.4", "Away.4"}
        for candidate in all_html_tables:
            if expected_columns.issubset(set(candidate.columns.astype(str))):
                league_table = candidate
                break
                    
        return rating_table, league_table

    except Exception:
        # Silently fail on fetch_table error to allow app to run
        return None, None

def find_section_header(soup, header_text):
    """Robustly finds a header tag containing specific text."""
    for header in soup.find_all('th'):
        if header_text in header.get_text():
            return header
    return None

def get_correct_table(soup, target_team_name, header_text, table_id_1, table_id_2):
    """Finds the correct data table by matching the visible team name."""
    header = find_section_header(soup, header_text)
    if not header: return None 

    team_name_row = header.find_next('tr')
    if not team_name_row: return None

    team_links = team_name_row.find_all('a')
    
    if len(team_links) >= 1:
        header_team1 = re.sub(r'\s*\([^)]*\)', '', team_links[0].get_text(strip=True)).strip()
        if target_team_name.lower() in header_team1.lower() or header_team1.lower() in target_team_name.lower():
            return soup.find("table", id=table_id_1)
            
    if len(team_links) == 2:
        header_team2 = re.sub(r'\s*\([^)]*\)', '', team_links[1].get_text(strip=True)).strip()
        if target_team_name.lower() in header_team2.lower() or header_team2.lower() in target_team_name.lower():
            return soup.find("table", id=table_id_2)
            
    return None

@st.cache_data(ttl=3600)
def fetch_team_lineup(team_name, team_url):
    """Fetches and parses the expected lineup for a single team."""
    def parse_lineup_table(lineup_table):
        player_list = []
        if not lineup_table: return player_list
        for row in lineup_table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) == 4:
                try:
                    player_div = cols[1].find("div", class_="nomobil")
                    if not player_div: continue
                    img_tag = player_div.find('img')
                    full_text = (img_tag.next_sibling.strip() if img_tag and img_tag.next_sibling else player_div.get_text(strip=True))
                    match = re.match(r'(.+?)\s*\((.+)\)', full_text)
                    name, position = (match.group(1).strip(), match.group(2).strip()) if match else (full_text.strip(), "N/A")
                    stats = cols[2].get_text(strip=True)
                    rating = int(cols[3].get_text(strip=True))
                    player_list.append({"name": name, "position": position, "stats": stats, "rating": rating})
                except (ValueError, IndexError): continue
        return player_list

    try:
        url = f"https://www.soccer-rating.com{team_url}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        correct_table = get_correct_table(soup, team_name, 'Expected Lineup', 'line1', 'line2')
        return parse_lineup_table(correct_table)
    except Exception:
        return None

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
    st.write("1. **Select Country and League** from the dropdowns.")
    st.write("2. **Click 'Get Ratings'** to load the league data.")
    st.write("3. **Select Home and Away Teams** to see the matchup analysis.")
    st.write("4. Lineups will be fetched automatically.")
    st.write("5. **Interact with the lineups** to see how player changes affect the total rating.")

st.sidebar.header("⚽ Select Match Details")
selected_country = st.sidebar.selectbox("Select Country:", list(leagues_dict.keys()), index=0)
selected_league = st.sidebar.selectbox("Select League:", leagues_dict[selected_country], index=0)

# --- Main App Logic ---
if st.sidebar.button("Get Ratings", key="fetch_button"):
    with st.spinner(random.choice(spinner_messages)):
        home_table, league_table = fetch_table(selected_country, selected_league, "home")
        away_table, _ = fetch_table(selected_country, selected_league, "away")
        
        if isinstance(home_table, pd.DataFrame) and isinstance(away_table, pd.DataFrame):
            st.session_state.update({
                "home_table": home_table, "away_table": away_table,
                "league_table": league_table, "data_fetched": True
            })
            for key in ['home_lineup', 'away_lineup']: st.session_state.pop(key, None)
            st.rerun() 
        else:
            st.error("Error fetching data. The source website might be unavailable or the structure may have changed.")
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

    # --- Display Team Stats ---
    if isinstance(league_table, pd.DataFrame):
        stat_col1, stat_col2 = st.columns(2)
        try:
            home_stats = league_table[league_table.iloc[:, 1] == home_team_name].iloc[0]
            goals_for, goals_against = home_stats['Home.4'].split(':')
            with stat_col1:
                st.markdown(f"**{home_team_name} (Home Stats)**")
                st.metric(label="League Position", value=f"#{int(home_stats.iloc[0])}")
                st.metric(label="Goals For", value=goals_for.strip())
                st.metric(label="Goals Against", value=goals_against.strip())
        except (IndexError, ValueError):
            stat_col1.warning(f"Home stats not available for {home_team_name}.")

        try:
            away_stats = league_table[league_table.iloc[:, 1] == away_team_name].iloc[0]
            goals_for, goals_against = away_stats['Away.4'].split(':')
            with stat_col2:
                st.markdown(f"**{away_team_name} (Away Stats)**")
                st.metric(label="League Position", value=f"#{int(away_stats.iloc[0])}")
                st.metric(label="Goals For", value=goals_for.strip())
                st.metric(label="Goals Against", value=goals_against.strip())
        except (IndexError, ValueError):
            stat_col2.warning(f"Away stats not available for {away_team_name}.")
    
    # --- Odds Calculation ---
    st.markdown('<div class="section-header">📈 Odds Analysis</div>', unsafe_allow_html=True)
    home_rating, away_rating = home_team_data['Rating'], away_team_data['Rating']
    home, away = 10**(home_rating / 400), 10**(away_rating / 400)
    home_win_prob, away_win_prob = home / (home + away), away / (home + away)
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{home_team_name} Rating", f"{home_rating:.2f}")
    c2.metric(f"{away_team_name} Rating", f"{away_rating:.2f}")
    
    d = 0.26 # Default draw prob
    draw_prob = st.slider("Select Draw Probability:", 0.05, 0.4, d, 0.01)
    
    h_win, a_win = home_win_prob * (1 - draw_prob), away_win_prob * (1 - draw_prob)
    h_odds, a_odds, d_odds = (1/p if p > 0 else 0 for p in [h_win, a_win, draw_prob])
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='card'><div class='card-title'>Home Win (1)</div><div class='card-value'>{h_odds:.2f}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='card'><div class='card-title'>Draw (X)</div><div class='card-value'>{d_odds:.2f}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='card'><div class='card-title'>Away Win (2)</div><div class='card-value'>{a_odds:.2f}</div></div>", unsafe_allow_html=True)

    # --- Automatic Lineup Fetching ---
    if 'last_home_team' not in st.session_state or st.session_state.last_home_team != home_team_name:
        with st.spinner(f"Fetching {home_team_name} lineup..."):
            st.session_state['home_lineup'] = fetch_team_lineup(home_team_name, home_team_data['URL'])
            st.session_state.last_home_team = home_team_name
            time.sleep(1) # Pause to avoid overloading server
            st.rerun()

    if 'last_away_team' not in st.session_state or st.session_state.last_away_team != away_team_name:
        with st.spinner(f"Fetching {away_team_name} lineup..."):
            st.session_state['away_lineup'] = fetch_team_lineup(away_team_name, away_team_data['URL'])
            st.session_state.last_away_team = away_team_name
            st.rerun()

    # --- Interactive Lineups Display ---
    st.markdown('<div class="section-header">📋 Interactive Lineups</div>', unsafe_allow_html=True)

    def display_interactive_lineup(team_name, team_key):
        st.subheader(f"{team_name}")
        lineup_data = st.session_state.get(team_key)

        if lineup_data is None:
            st.info("Fetching lineup...")
            return
        if not lineup_data:
            st.warning("Lineup data not available for this team.")
            return

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
        if num_selected != 11:
            st.warning(f"Please select exactly 11 starters ({num_selected} selected).")
        
        starters_rating_sum = sum(p['rating'] for p in selected_starters)
        avg_rating = starters_rating_sum / num_selected if num_selected > 0 else 0
        
        m1, m2 = st.columns(2)
        m1.metric("Total Starters Rating", starters_rating_sum)
        m2.metric("Average Starter Rating", f"{avg_rating:.2f}")

    display_col1, display_col2 = st.columns(2)
    with display_col1: display_interactive_lineup(f"{home_team_name} (Home)", "home_lineup")
    with display_col2: display_interactive_lineup(f"{away_team_name} (Away)", "away_lineup")

else:
    st.info("Please click 'Get Ratings' in the sidebar to begin.")
