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
import json
from pathlib import Path
from datetime import datetime

from odds import calculate_poisson_markets_from_dnb

# Set page title and icon
st.set_page_config(page_title="Elo Ratings Odds Calculator", page_icon="odds_icon.png")

# --- App Constants ---

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
DEFAULT_AVG_GOALS = 2.6
# Optional weight for blending the observed league draw rate back into the
# Poisson-derived draw probability. Default keeps the Poisson result.
DRAW_OBS_WEIGHT = 0.0
# Global multiplier applied to the Bradley-Terry draw ratio. Values above 1
# lift draw probabilities (default bumps them ~10%), values below 1 trim them.
DRAW_RATE_SCALE = 1.1

# Elo-based scaling parameters for adjusting the expected goal total before
# computing the Poisson draw probability. The factor is applied to the rating
# gap (normalised by the divisor) and capped to avoid extreme totals.
ELO_GOAL_SCALE_FACTOR = 0.35
ELO_GOAL_SCALE_DIVISOR = 400
ELO_GOAL_SCALE_CAP = 0.6


def modified_bessel_i0(x: float) -> float:
    """Compute the modified Bessel function I0 with a pure-Python fallback."""

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


# --- League Statistical Data Loader ---
LEAGUE_STATS_PATH = Path(__file__).resolve().parent / "data" / "league_stats.json"


def normalize_league_key(name: str) -> str:
    # Ensure league names use a consistent format for lookups.
    return re.sub(r"\s+", " ", str(name)).strip()


@st.cache_data
def load_league_stats(path: str = str(LEAGUE_STATS_PATH)):
    # Load league statistics from a JSON or CSV source.
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




# --- League Mapping ("Rosetta Stone") ---
# Maps (country_key, league_code) from leagues_data to the string key in the loaded stats
LEAGUE_STATS_MAP = {
    ("Albania", "AL1"): "Albania - Abissnet Superiore",
    ("Andorra", "AD1"): "Andorra - Primera Divisio",
    ("Argentina", "AR1"): "Argentina - Liga Profesional - Apertura", # Assuming AR1 is Apertura
    ("Argentina", "AR2"): "Argentina - Primera B - Apertura", # Assuming AR2 is Primera B Apertura
    ("Armenia", "AM1"): "Armenia - Premier League",
    ("Australia", "AU1"): "Australia - A-League",
    ("Australia", "AU2V"): "Australia - NPL Victoria",
    ("Australia", "AU2NSW"): "Australia - NPL New South Wales",
    ("Australia", "AU2S"): "Australia - NPL South Australia",
    ("Australia", "AU2W"): "Australia - NPL Western Australia",
    ("Australia-Women", "AW1"): "Australia - A-League Women",
    ("Austria", "AT1"): "Austria - Bundesliga",
    ("Austria", "AT2"): "Austria - 2. Liga",
    ("Austria", "AT3W"): "Austria - Regionalliga West",
    ("Austria", "AT3M"): "Austria - Regionalliga Mitte",
    ("Austria", "AT3O"): "Austria - Regionalliga Ost",
    ("Austria-Women", "AW1"): "Austria - Bundesliga Women", # Guessed mapping
    ("Azerbaijan", "AZ1"): "Azerbaijan - Premier League",
    ("Bahrain", "BH1"): "Bahrain - Premier League",
    ("Bangladesh", "BD1"): "Bangladesh - Premier League",
    ("Belarus", "BY1"): "Belarus - Vysshaya Liga",
    ("Belgium", "BE1"): "Belgium - Pro League",
    ("Belgium", "BE2"): "Belgium - Challenger Pro League",
    ("Bolivia", "BO1"): "Bolivia - Division Profesional",
    ("Bosnia-Herzegovina", "BA1"): "Bosnia and Herzegovina - Premier Liga",
    ("Brazil", "BR1"): "Brazil - Serie A",
    ("Brazil", "BR2"): "Brazil - Serie B",
    ("Brazil", "BR3"): "Brazil - Serie C",
    ("Brazil", "BRC"): "Brazil - Carioca", # Assuming BRC is Carioca
    ("Brazil", "BRGA"): "Brazil - Gaucho", # Assuming BRGA is Gaucho
    ("Brazil-Women", "FB1"): "Brazil - Brasileiro Women",
    ("Bulgaria", "BG1"): "Bulgaria - Parva Liga",
    ("Bulgaria", "BG2"): "Bulgaria - Vtora Liga",
    ("Canada", "CA1"): "Canada - Premier League",
    ("Chile", "CL1"): "Chile - Liga de Primera",
    ("Chile", "CL2"): "Chile - Liga de Ascenso",
    ("China", "CN1"): "China - Super League",
    ("China", "CN2"): "China - League One",
    ("China", "CN3"): "China - League Two",
    ("Colombia", "CO1"): "Colombia - Primera A - Apertura",
    ("Colombia", "CO2"): "Colombia - Primera B - Apertura",
    ("Costa-Rica", "CR1"): "Costa Rica - Primera Div. - Apertura",
    ("Croatia", "HR1"): "Croatia - 1. HNL",
    ("Croatia", "HR2"): "Croatia - 1. NL",
    ("Cyprus", "CY1"): "Cyprus - Cyprus League",
    ("Cyprus", "CY2"): "Cyprus - Division 2",
    ("Czech-Republic", "CZ1"): "Czech Republic - 1. Liga",
    ("Czech-Republic", "CZ2"): "Czech Republic - FNL",
    ("Czech-Republic-Women", "LZ1"): "Czech Republic - 1. Liga Women",
    ("Denmark", "DK1"): "Denmark - Superligaen",
    ("Denmark", "DK2"): "Denmark - 1st Division",
    ("Denmark", "DK3"): "Denmark - 2nd Division",
    ("Ecuador", "EC1"): "Ecuador - Liga Pro",
    ("Egypt", "EG1"): "Egypt - Premier League",
    ("England", "UK1"): "England - Premier League",
    ("England", "UK2"): "England - Championship",
    ("England", "UK3"): "England - League One",
    ("England", "UK4"): "England - League Two",
    ("England", "UK5"): "England - National League",
    ("England", "UK6N"): "England - National L. North",
    ("England", "UK6S"): "England - National L. South",
    ("England-Women", "UW1"): "England - Women Super League",
    ("England-Women", "UW2"): "England - WSL 2",
    ("Estonia", "EE1"): "Estonia - Meistriliiga",
    ("Färöer", "FA1"): "FaroeIslands - Premier League",
    ("Finland", "FI1"): "Finland - Veikkausliiga",
    ("Finland", "FI2"): "Finland - Ykkosliga",
    ("Finland", "FI3"): "Finland - Ykkonen",
    ("Finland", "FI4A"): "Finland - Kakkonen Group A",
    ("Finland", "FI4B"): "Finland - Kakkonen Group B",
    ("Finland", "FI4C"): "Finland - Kakkonen Group C",
    ("Finland-Women", "FW1"): "Finland - Kansallinen Liiga Women",
    ("France", "FR1"): "France - Ligue 1",
    ("France", "FR2"): "France - Ligue 2",
    ("France", "FR3"): "France - National",
    ("France-Women", "FF1"): "France - Premiere Ligue Women",
    ("Georgia", "GE1"): "Georgia - Erovnuli Liga",
    ("Georgia", "GE2"): "Georgia - Erovnuli Liga 2",
    ("Germany", "DE1"): "Germany - Bundesliga",
    ("Germany", "DE2"): "Germany - 2. Bundesliga",
    ("Germany", "DE3"): "Germany - 3. Liga",
    ("Germany", "DE4N"): "Germany - Regionalliga Nord",
    ("Germany", "DE4NO"): "Germany - Regionalliga Nordost",
    ("Germany", "DE4W"): "Germany - Regionalliga West",
    ("Germany", "DE4SW"): "Germany - Regionalliga Sudwest",
    ("Germany", "DE4B"): "Germany - Regionalliga Bayern",
    ("Germany-Women", "GW1"): "Germany - Bundesliga Women",
    ("Germany-Women", "GW2"): "Germany - 2. Bundesliga Women",
    ("Gibraltar", "GI1"): "Gibraltar - Premier Division",
    ("Greece", "GR1"): "Greece - Super League",
    ("Guatemala", "GT1"): "Guatemala - Liga Nacional - Apertura",
    ("Hong Kong", "HK1"): "Hong Kong - Premier League",
    ("Hungary", "HU1"): "Hungary - NB I",
    ("Hungary", "HU2"): "Hungary - NB II",
    ("Iceland", "IS1"): "Iceland - Besta deild",
    ("Iceland", "IS2"): "Iceland - 1. Deild",
    ("Iceland", "IS3"): "Iceland - 2. Deild",
    ("Iceland-Women", "IW1"): "Iceland - Besta deild Women",
    ("India", "IN1"): "India - Super League",
    ("India", "IN2"): "India - I-League",
    ("Indonesia", "ID1"): "Indonesia - Liga 1",
    ("Iran", "IA1"): "Iran - Pro League",
    ("Ireland", "IR1"): "Ireland - Premier Division",
    ("Ireland", "IR2"): "Ireland - First Division",
    ("Israel", "IL1"): "Israel - Ligat HaAl",
    ("Italy", "IT1"): "Italy - Serie A",
    ("Italy", "IT2"): "Italy - Serie B",
    ("Italy", "IT3A"): "Italy - Serie C - Group A",
    ("Italy", "IT3B"): "Italy - Serie C - Group B",
    ("Italy", "IT3C"): "Italy - Serie C - Group C",
    ("Italy-Women", "IF1"): "Italy - Serie A Women",
    ("Jamaica", "JM1"): "Jamaica - Premier League",
    ("Japan", "JP1"): "Japan - J1 League",
    ("Japan", "JP2"): "Japan - J2 League",
    ("Japan", "JP3"): "Japan - J3 League",
    ("Japan-Women", "JW1"): "Japan - WE League",
    ("Japan-Women", "JW2"): "Japan - Nadeshiko League 1",
    ("Jordan", "JO1"): "Jordan - Premier League",
    ("Kazakhstan", "KZ1"): "Kazakhstan - Premier League",
    ("Kuwait", "KW1"): "Kuwait - Premier League",
    ("Latvia", "LA1"): "Latvia - Virsliga",
    ("Latvia", "LA2"): "Latvia - 1. Liga",
    ("Lithuania", "LT1"): "Lithuania - A Lyga",
    ("Lithuania", "LT2"): "Lithuania - 1st League",
    ("Malaysia", "MY1"): "Malaysia - Super League",
    ("Mexico", "MX1"): "Mexico - Liga MX - Apertura",
    ("Mexico-Women", "MF1"): "Mexico - Liga MX - Apertura", # No women's stats, mapping to men's
    ("Moldova", "MD1"): "Moldova - Divizia Nationala",
    ("Montenegro", "MN1"): "Montenegro - First League",
    ("Morocco", "MA1"): "Morocco - Botola Pro",
    ("Netherlands", "NL1"): "Netherlands - Eredivisie",
    ("Netherlands", "NL2"): "Netherlands - Eerste Divisie",
    ("Netherlands", "NL3"): "Netherlands - Tweede Divisie",
    ("Netherlands-Women", "NV1"): "Netherlands - Eredivisie Women",
    ("Northern-Ireland", "NI1"): "Northern Ireland - NIFL Premiership",
    ("Northern-Ireland", "NI2"): "Northern Ireland - NIFL Championship",
    ("North-Macedonia", "MK1"): "North Macedonia - First League",
    ("Norway", "NO1"): "Norway - Eliteserien",
    ("Norway", "NO2"): "Norway - 1st Division",
    ("Norway", "NO3G1"): "Norway - Division 2 - Gr. 1",
    ("Norway", "NO3G2"): "Norway - Division 2 - Gr. 2",
    ("Norway-Women", "NW1"): "Norway - Toppserien Women",
    ("Norway-Women", "NW2"): "Norway - 1. Division Women",
    ("Paraguay", "PY1"): "Paraguay - Primera Div. - Apertura",
    ("Peru", "PE1"): "Peru - Liga 1 - Apertura",
    ("Poland", "PL1"): "Poland - Ekstraklasa",
    ("Poland", "PL2"): "Poland - 1. Liga",
    ("Poland", "PL3"): "Poland - 2. Liga",
    ("Portugal", "PT1"): "Portugal - Liga Portugal",
    ("Portugal", "PT2"): "Portugal - Liga Portugal 2",
    ("Qatar", "QA1"): "Qatar - Stars League",
    ("Qatar", "QA2"): "Qatar - Division 2",
    ("Romania", "RO1"): "Romania - Liga 1",
    ("Romania", "RO2"): "Romania - Liga 2",
    ("Russia", "RU1"): "Russia - Premier League",
    ("Russia", "RU2"): "Russia - FNL",
    ("Rwanda", "RW1"): "Rwanda - Premier League",
    ("San-Marino", "SM1"): "SanMarino - Campionato Sammarinese",
    ("Saudi-Arabia", "SA1"): "Saudi Arabia - Professional League",
    ("Saudi-Arabia", "SA2"): "Saudi Arabia - Division 1",
    ("Scotland", "SC1"): "Scotland - Premiership",
    ("Scotland", "SC2"): "Scotland - Championship",
    ("Scotland", "SC3"): "Scotland - League One",
    ("Scotland", "SC4"): "Scotland - League Two",
    ("Scotland-Women", "SP1"): "Scotland - SWPL 1 Women",
    ("Serbia", "CS1"): "Serbia - Super Liga",
    ("Serbia", "CS2"): "Serbia - Prva Liga",
    ("Singapore", "SG1"): "Singapore - Premier League",
    ("Slovakia", "SK1"): "Slovakia - 1. Liga",
    ("Slovakia", "SK2"): "Slovakia - 2. Liga",
    ("Slovenia", "SI1"): "Slovenia - Prva Liga",
    ("South-Africa", "ZA1"): "South Africa - Premier Division",
    ("South-Africa", "ZA2"): "South Africa - First Division",
    ("South-Korea", "KR1"): "South Korea - K League 1",
    ("South-Korea", "KR2"): "South Korea - K League 2",
    ("South-Korea-Women", "KX1"): "South Korea - WK League Women",
    ("Spain", "ES1"): "Spain - LaLiga",
    ("Spain", "ES2"): "Spain - LaLiga2",
    ("Spain-Women", "EW1"): "Spain - Liga F Women",
    ("Spain-Women", "EW2"): "Spain - Primera F. Women",
    ("Sweden", "SW1"): "Sweden - Allsvenskan",
    ("Sweden", "SW2"): "Sweden - Superettan",
    ("Sweden", "SW3N"): "Sweden - Div 1 - Norra",
    ("Sweden", "SW3S"): "Sweden - Div 1 - Sodra",
    ("Sweden-Women", "SX1"): "Sweden - Allsvenskan Women",
    ("Sweden-Women", "SX2"): "Sweden - Elitetan Women",
    ("Switzerland", "CH1"): "Switzerland - Super League",
    ("Switzerland", "CH2"): "Switzerland - Challenge League",
    ("Thailand", "TH1"): "Thailand - Thai League 1",
    ("Turkey", "TU1"): "Turkey - Super Lig",
    ("Turkey", "TU2"): "Turkey - 1. Lig",
    ("Turkey", "TU3B"): "Turkey - 2. Lig White Group", # Guessed mapping
    ("Turkey", "TU3K"): "Turkey - 2. Lig Red Group", # Guessed mapping
    ("UAE - Pro League", "AE1"): "UAE - Pro League",
    ("Ukraine", "UA1"): "Ukraine - Premier League",
    ("Ukraine", "UA2"): "Ukraine - Persha Liga",
    ("Uruguay", "UY1"): "Uruguay - Liga AUF Uruguaya - Apertura",
    ("Uruguay", "UY2"): "Uruguay - Liga AUF Uruguaya - Clausura", # Guessed
    ("USA", "US1"): "USA - MLS",
    ("USA", "US2"): "USA - USL Championship",
    ("USA", "US3"): "USA - USL League One",
    ("USA-Women", "UV1"): "USA - NWSL",
    ("USA-Women", "UV2"): "USA - USL Super League",
    ("Venezuela", "VE1"): "Venezuela - Liga FUTVE - Apertura",
    ("Vietnam", "VN1"): "Vietnam - V League",
    ("Vietnam", "VN2"): "Vietnam - National League Women", # Guessed
    ("Wales", "WL1"): "Wales - Cymru Premier",
}


# Combined dictionary for both Men's and Women's leagues
leagues_data = {
    "Men's": {
        "England": ["UK1", "UK2", "UK3", "UK4", "UK5", "UK6N", "UK6S"],
        "Germany": ["DE1", "DE2", "DE3", "DE4SW", "DE4W", "DE4N", "DE4NO", "DE4B"],
        "Italy": ["IT1", "IT2", "IT3C", "IT3B", "IT3A"],
        "Spain": ["ES1", "ES2"],
        "France": ["FR1", "FR2", "FR3"],
        "Sweden": ["SW1", "SW2", "SW3S", "SW3N"],
        "Netherlands": ["NL1", "NL2", "NL3"],
        "Russia": ["RU1", "RU2"],
        "Portugal": ["PT1", "PT2"],
        "Austria": ["AT1", "AT2", "AT3O", "AT3M", "AT3W"],
        "Denmark": ["DK1", "DK2", "DK3"],
        "Greece": ["GR1"],
        "Norway": ["NO1", "NO2", "NO3G1", "NO3G2"],
        "Czech Republic": ["CZ1", "CZ2"],
        "Turkey": ["TU1", "TU2", "TU3B", "TU3K"],
        "Belgium": ["BE1", "BE2"],
        "Scotland": ["SC1", "SC2", "SC3", "SC4"],
        "Switzerland": ["CH1", "CH2"],
        "Finland": ["FI1", "FI2", "FI3"],
        "Ukraine": ["UA1", "UA2"],
        "Romania": ["RO1", "RO2"],
        "Poland": ["PL1", "PL2", "PL3"],
        "Croatia": ["HR1", "HR2"],
        "Belarus": ["BY1"],
        "Israel": ["IL1"],
        "Iceland": ["IS1", "IS2", "IS3"],
        "Cyprus": ["CY1", "CY2"],
        "Serbia": ["CS1", "CS2"],
        "Bulgaria": ["BG1", "BG2"],
        "Slovakia": ["SK1", "SK2"],
        "Hungary": ["HU1", "HU2"],
        "Kazakhstan": ["KZ1"],
        "Bosnia-Herzegovina": ["BA1"],
        "Slovenia": ["SI1"],
        "Azerbaijan": ["AZ1"],
        "Ireland": ["IR1", "IR2"],
        "Latvia": ["LA1", "LA2"],
        "Georgia": ["GE1", "GE2"],
        "Albania": ["AL1"],
        "Lithuania": ["LT1", "LT2"],
        "North-Macedonia": ["MK1"],
        "Armenia": ["AM1"],
        "Estonia": ["EE1"],
        "Northern-Ireland": ["NI1", "NI2"],
        "Wales": ["WL1"],
        "Montenegro": ["MN1"],
        "Moldova": ["MD1"],
        "Färöer": ["FA1"],
        "Gibraltar": ["GI1"],
        "Andorra": ["AD1"],
        "San-Marino": ["SM1"],
        "Brazil": ["BR1", "BR2", "BR3", "BRC", "BRGA"],
        "Mexico": ["MX1"],
        "Argentina": ["AR1", "AR2"],
        "USA": ["US1", "US2", "US3"],
        "Colombia": ["CO1", "CO2"],
        "Ecuador": ["EC1"],
        "Paraguay": ["PY1"],
        "Chile": ["CL1", "CL2"],
        "Uruguay": ["UY1", "UY2"],
        "Costa-Rica": ["CR1"],
        "Bolivia": ["BO1"],
        "Guatemala": ["GT1"],
        "Venezuela": ["VE1"],
        "Peru": ["PE1"],
        "Jamaica": ["JM1"],
        "Canada": ["CA1"],
        "Japan": ["JP1", "JP2", "JP3"],
        "South-Korea": ["KR1", "KR2"],
        "China": ["CN1", "CN2", "CN3"],
        "Iran": ["IA1"],
        "Australia": ["AU1", "AU2V", "AU2NSW", "AU2S", "AU2W"],
        "Saudi-Arabia": ["SA1", "SA2"],
        "Thailand": ["TH1"],
        "Qatar": ["QA1", "QA2"],
        "United Arab Emirates": ["AE1"],
        "Indonesia": ["ID1"],
        "Jordan": ["JO1"],
        "Malaysia": ["MY1"],
        "Vietnam": ["VN1"],
        "Kuwait": ["KW1"],
        "Bahrain": ["BH1"],
        "India": ["IN1", "IN2"],
        "Hong Kong": ["HK1"],
        "Singapore": ["SG1"],
        "Bangladesh": ["BD1"],
        "Egypt": ["EG1"],
        "Morocco": ["MA1"],
        "South-Africa": ["ZA1", "ZA2"],
        "Rwanda": ["RW1"],
    },
    "Women's": {
        "England-Women": ["UW1", "UW2"],
        "Spain-Women": ["EW1", "EW2"],
        "Germany-Women": ["GW1", "GW2"],
        "Brazil-Women": ["FB1"],
        "France-Women": ["FF1"],
        "Italy-Women": ["IF1"],
        "Sweden-Women": ["SX1","SX2"],
        "Norway-Women": ["NW1", "NW2"],
        "Iceland-Women": ["IW1"],
        "Scotland-Women": ["SP1"],
        "Netherlands-Women": ["NV1"],
        "Japan-Women": ["JW1", "JW2"],
        "Finland-Women": ["FW1"],
        "Mexico-Women": ["MF1"],
        "Czech-Republic-Women": ["LZ1"],
        "USA-Women": ["UV1", "UV2"],
        "Australia-Women": ["AW1"],
        "South-Korea-Women": ["KX1"]
    }
}

# Combine Men's and Women's league data into a single dictionary
all_leagues = {**leagues_data["Men's"], **leagues_data["Women's"]}
# Sort the combined list of countries/leagues alphabetically
sorted_countries = sorted(all_leagues.keys())


# --- Utility Functions ---

def load_css(file_name):
    """Loads a local CSS file."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please add it to the directory.")

def fetch_with_headers(url, referer=None, timeout=15):
    """Fetches a URL with custom headers to mimic a browser."""
    headers = BASE_HEADERS.copy()
    headers["Referer"] = referer or "https://www.soccer-rating.com/"
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response

def normalize_team_name(name):
    """Robustly cleans and standardizes a team name for reliable matching."""
    if not isinstance(name, str): return ""
    name = name.lower()
    name = name.replace('ö', 'oe').replace('ü', 'ue').replace('ä', 'ae')
    name = name.replace('ø', 'oe').replace('å', 'aa').replace('æ', 'ae')
    name = re.sub(r'[\&\-\.]+', ' ', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s\([ns]\)$', '', name)
    return ' '.join(name.split())

def safe_float(value, default=0.0):
    """Converts a value to float, handling percentage strings and errors."""
    try:
        if isinstance(value, str) and '%' in value:
            return float(value.replace('%', '')) / 100.0
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default

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

def find_section_header(soup, header_text):
    """Finds a table header element by its text."""
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

# --- Statistical & Odds Calculation Functions ---

def get_league_stats(country_key, league_code):
    """
    Retrieves the stored stats for a given league using the mapping.
    Returns a dictionary of the stats.
    """
    map_key = (country_key, league_code)
    league_name = LEAGUE_STATS_MAP.get(map_key)
    
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
    primary_league_code_key = next(iter(leagues_data.get(country_key, {})), None)
    if primary_league_code_key:
        primary_league_code = leagues_data[country_key][primary_league_code_key][0]
        map_key = (country_key, primary_league_code)
        league_name = LEAGUE_STATS_MAP.get(map_key)
        if league_name:
            normalized_league_name = normalize_league_key(league_name)
            stats = stats_data.get(normalized_league_name)
            if stats:
                stats_copy = stats.copy()
                stats_copy["League"] = league_name
                return stats_copy

    return None

def get_league_suggested_draw_rate(country_key, league_code, stats=None):
    """
    Analyzes the league table to suggest a realistic draw rate.
    Returns a suggested draw probability based on league data.
    """
    stats = stats or get_league_stats(country_key, league_code)
    if stats and 'Draw%' in stats:
        return safe_float(stats['Draw%'], DEFAULT_DRAW_RATE)

    return DEFAULT_DRAW_RATE


def get_league_average_goals(country_key, league_code, stats=None):
    """Return the league's average total goals per match for draw calibration."""
    stats = stats or get_league_stats(country_key, league_code)
    if stats and 'AvgGoals' in stats:
        return safe_float(stats['AvgGoals'], DEFAULT_AVG_GOALS)

    return DEFAULT_AVG_GOALS

def calculate_outcome_probabilities(home_rating, away_rating, base_draw_prob, avg_goals, draw_weight=DRAW_OBS_WEIGHT):
    """Calculate 1X2 probabilities via Bradley-Terry-Davidson anchored to league scoring."""

    rating_diff = safe_float(home_rating, 0) - safe_float(away_rating, 0)
    strength_ratio = 10 ** (rating_diff / 400)

    # Adjust the league scoring environment by scaling the average goals with
    # the Elo rating gap before computing the Poisson draw probability.
    mu = max(safe_float(avg_goals, DEFAULT_AVG_GOALS), 0)
    rating_gap = abs(rating_diff)
    gap_ratio = rating_gap / ELO_GOAL_SCALE_DIVISOR if ELO_GOAL_SCALE_DIVISOR else 0
    goal_scale = 1 + min(gap_ratio * ELO_GOAL_SCALE_FACTOR, ELO_GOAL_SCALE_CAP)
    mu_adjusted = mu * goal_scale
    poisson_draw = math.exp(-mu_adjusted) * modified_bessel_i0(mu_adjusted)

    alpha = 0.0 if draw_weight is None else min(max(draw_weight, 0.0), 1.0)
    observed_draw = min(max(safe_float(base_draw_prob, DEFAULT_DRAW_RATE), 0.0), 0.95)
    blended_draw = poisson_draw if alpha == 0 else (
        alpha * observed_draw + (1 - alpha) * poisson_draw
    )
    blended_draw = min(max(blended_draw, 1e-6), 0.999999)

    nu = blended_draw / (1 - blended_draw)
    nu = max(nu * max(DRAW_RATE_SCALE, 1e-6), 0.0)

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


def apply_margin(probabilities, margin_percent):
    """
    Applies a bookmaker's margin to a list of probabilities
    using proportional scaling.
    """
    if not probabilities or sum(probabilities) == 0:
        return [0] * len(probabilities)

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

def display_league_stats(stats_row):
    """Renders the soccerstats data in a compact, multi-column format."""
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

def display_team_stats(team_name, table, column):
    """Displays key stats for a single team from the league table."""
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

def display_interactive_lineup(team_name, team_key):
    """Displays an interactive checklist of the team's lineup."""
    st.subheader(f"{team_name}")
    lineup_data = st.session_state.get(team_key)
    if not lineup_data: 
        st.warning("Lineup data not available.")
        return 0, 0
    
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

def display_squad(team_name, squad_key, lineup_key):
    """Displays the full squad, highlighting starters."""
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

def fetch_data_for_selection(country, league):
    """Callback to fetch all data for a newly selected league."""
    current_selection = f"{country}_{league}"
    if st.session_state.get('current_selection') != current_selection or not st.session_state.get('data_fetched', False):
        st.session_state['current_selection'] = current_selection
        with st.spinner(random.choice(SPINNER_MESSAGES)):
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

        st.subheader("Multi-Match Odds Calculator")
        
        multi_margin = st.slider("Apply Bookmaker's Margin (%):", 0.0, 15.0, 5.0, 0.5, format="%.1f%%", key="multi_margin")
        st.markdown("---")

        num_teams = len(team_list)
        num_rows = math.ceil(num_teams / 2)
        
        if 'multi_match_selections' not in st.session_state:
            st.session_state['multi_match_selections'] = {}

        # Use "---" as a blank option
        team_list_with_blank = ["---"] + team_list

        for i in range(num_rows):
            key_home = f"multi_home_{i}"
            key_away = f"multi_away_{i}"
            
            # Set defaults
            default_home = st.session_state['multi_match_selections'].get(key_home, "---")
            default_away = st.session_state['multi_match_selections'].get(key_away, "---")

            # Ensure defaults are valid
            default_home_index = team_list_with_blank.index(default_home) if default_home in team_list_with_blank else 0
            default_away_index = team_list_with_blank.index(default_away) if default_away in team_list_with_blank else 0

            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 3, 1.05, 1.05, 1.05, 1.05, 1.05])
            
            sel_home = col1.selectbox(f"Home Team {i+1}", team_list_with_blank, index=default_home_index, key=key_home, label_visibility="collapsed")
            sel_away = col2.selectbox(f"Away Team {i+1}", team_list_with_blank, index=default_away_index, key=key_away, label_visibility="collapsed")

            # Store selections
            st.session_state['multi_match_selections'][key_home] = sel_home
            st.session_state['multi_match_selections'][key_away] = sel_away

            odds_home_1x2, odds_draw_1x2, odds_away_1x2 = "-", "-", "-"
            odds_dnb_home, odds_dnb_away = "-", "-"
            
            if sel_home != "---" and sel_away != "---" and sel_home != sel_away:
                try:
                    h_rating = home_table[home_table["Team"] == sel_home].iloc[0]['Rating']
                    a_rating = away_table[away_table["Team"] == sel_away].iloc[0]['Rating']
                    
                    p_h, _, p_a = calculate_outcome_probabilities(
                        h_rating,
                        a_rating,
                        league_avg_draw,
                        league_avg_goals,
                    )
                    p_dnb_home = p_h / (p_h + p_a) if (p_h + p_a) > 0 else 0.5
                    p_dnb_away = 1 - p_dnb_home

                    odds_1x2 = apply_margin([p_h, p_draw, p_a], multi_margin)
                    dnb_probs = [p_dnb_home, p_dnb_away]
                    adjusted_dnb = apply_margin(dnb_probs, multi_margin)

                    odds_home_1x2 = f"{odds_1x2[0]:.2f}"
                    odds_draw_1x2 = f"{odds_1x2[1]:.2f}"
                    odds_away_1x2 = f"{odds_1x2[2]:.2f}"
                    odds_dnb_home = f"{adjusted_dnb[0]:.2f}"
                    odds_dnb_away = f"{adjusted_dnb[1]:.2f}"
                except (IndexError, TypeError):
                    # One of the teams might not be in the table (e.g., if lists differ)
                    odds_home_1x2, odds_draw_1x2, odds_away_1x2 = "Err", "Err", "Err"
                    odds_dnb_home, odds_dnb_away = "Err", "Err"

            with col3:
                st.markdown(
                    f"""
                <div class="odds-box odds-box--compact">
                    <div class="odds-box-title">1X2</div>
                    <div class="odds-box-subtitle">Home</div>
                    <div class="odds-box-value">{odds_home_1x2}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            with col4:
                st.markdown(
                    f"""
                <div class="odds-box odds-box--compact">
                    <div class="odds-box-title">1X2</div>
                    <div class="odds-box-subtitle">Draw</div>
                    <div class="odds-box-value">{odds_draw_1x2}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            with col5:
                st.markdown(
                    f"""
                <div class="odds-box odds-box--compact">
                    <div class="odds-box-title">1X2</div>
                    <div class="odds-box-subtitle">Away</div>
                    <div class="odds-box-value">{odds_away_1x2}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            with col6:
                st.markdown(
                    f"""
                <div class="odds-box odds-box--compact">
                    <div class="odds-box-title">AH 0</div>
                    <div class="odds-box-subtitle">Home</div>
                    <div class="odds-box-value">{odds_dnb_home}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            with col7:
                st.markdown(
                    f"""
                <div class="odds-box odds-box--compact">
                    <div class="odds-box-title">AH 0</div>
                    <div class="odds-box-subtitle">Away</div>
                    <div class="odds-box-value">{odds_dnb_away}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )


else:
    st.info("Please select a country and league in the sidebar to begin.")
