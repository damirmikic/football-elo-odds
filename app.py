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

# --- Hardcoded League Statistical Data ---
# This data is manually parsed from the user-provided stats.
SOCCERSTATS_DATA = {
    "Albania - Abissnet Superiore": {"GP": 50, "HomeW%": 0.44, "Draw%": 0.30, "AwayW%": 0.26, "AvgGoals": 1.92, "AvgHG": 1.10, "AvgAG": 0.82},
    "Andorra - Primera Divisio": {"GP": 21, "HomeW%": 0.43, "Draw%": 0.29, "AwayW%": 0.29, "AvgGoals": 2.24, "AvgHG": 1.19, "AvgAG": 1.05},
    "Argentina - Liga Profesional - Apertura": {"GP": 240, "HomeW%": 0.44, "Draw%": 0.31, "AwayW%": 0.25, "AvgGoals": 2.00, "AvgHG": 1.18, "AvgAG": 0.81},
    "Argentina - Liga Profesional - Clausura": {"GP": 210, "HomeW%": 0.38, "Draw%": 0.33, "AwayW%": 0.29, "AvgGoals": 1.96, "AvgHG": 1.06, "AvgAG": 0.90},
    "Argentina - Primera B - Apertura": {"GP": 210, "HomeW%": 0.40, "Draw%": 0.34, "AwayW%": 0.26, "AvgGoals": 1.99, "AvgHG": 1.16, "AvgAG": 0.82},
    "Argentina - Primera B - Clausura": {"GP": 190, "HomeW%": 0.38, "Draw%": 0.35, "AwayW%": 0.26, "AvgGoals": 2.10, "AvgHG": 1.17, "AvgAG": 0.93},
    "Armenia - Premier League": {"GP": 58, "HomeW%": 0.45, "Draw%": 0.22, "AwayW%": 0.33, "AvgGoals": 2.60, "AvgHG": 1.57, "AvgAG": 1.03},
    "Australia - A-League": {"GP": 18, "HomeW%": 0.56, "Draw%": 0.33, "AwayW%": 0.11, "AvgGoals": 2.72, "AvgHG": 1.67, "AvgAG": 1.06},
    "Australia - A-League Women": {"GP": 5, "HomeW%": 0.40, "Draw%": 0.20, "AwayW%": 0.40, "AvgGoals": 3.80, "AvgHG": 2.00, "AvgAG": 1.80},
    "Australia - NPL Victoria": {"GP": 182, "HomeW%": 0.45, "Draw%": 0.21, "AwayW%": 0.35, "AvgGoals": 3.30, "AvgHG": 1.81, "AvgAG": 1.49},
    "Australia - NPL Western Australia": {"GP": 132, "HomeW%": 0.38, "Draw%": 0.21, "AwayW%": 0.41, "AvgGoals": 3.39, "AvgHG": 1.68, "AvgAG": 1.71},
    "Australia - NPL South Australia": {"GP": 132, "HomeW%": 0.45, "Draw%": 0.14, "AwayW%": 0.41, "AvgGoals": 3.42, "AvgHG": 1.80, "AvgAG": 1.62},
    "Australia - NPL Tasmania": {"GP": 84, "HomeW%": 0.44, "Draw%": 0.11, "AwayW%": 0.45, "AvgGoals": 4.63, "AvgHG": 2.27, "AvgAG": 2.36},
    "Australia - NPL New South Wales": {"GP": 240, "HomeW%": 0.42, "Draw%": 0.23, "AwayW%": 0.35, "AvgGoals": 2.98, "AvgHG": 1.56, "AvgAG": 1.42},
    "Austria - Bundesliga": {"GP": 71, "HomeW%": 0.37, "Draw%": 0.23, "AwayW%": 0.41, "AvgGoals": 2.72, "AvgHG": 1.35, "AvgAG": 1.37},
    "Austria - 2. Liga": {"GP": 96, "HomeW%": 0.34, "Draw%": 0.31, "AwayW%": 0.34, "AvgGoals": 2.82, "AvgHG": 1.42, "AvgAG": 1.41},
    "Austria - Regionalliga West": {"GP": 119, "HomeW%": 0.43, "Draw%": 0.20, "AwayW%": 0.37, "AvgGoals": 3.28, "AvgHG": 1.76, "AvgAG": 1.52},
    "Austria - Regionalliga Mitte": {"GP": 111, "HomeW%": 0.43, "Draw%": 0.23, "AwayW%": 0.34, "AvgGoals": 3.71, "AvgHG": 1.96, "AvgAG": 1.75},
    "Austria - Regionalliga Ost": {"GP": 111, "HomeW%": 0.48, "Draw%": 0.23, "AwayW%": 0.30, "AvgGoals": 2.91, "AvgHG": 1.72, "AvgAG": 1.19},
    "Austria - Bundesliga Women": {"GP": 55, "HomeW%": 0.35, "Draw%": 0.13, "AwayW%": 0.53, "AvgGoals": 3.40, "AvgHG": 1.53, "AvgAG": 1.87},
    "Azerbaijan - Premier League": {"GP": 59, "HomeW%": 0.36, "Draw%": 0.27, "AwayW%": 0.37, "AvgGoals": 2.53, "AvgHG": 1.31, "AvgAG": 1.22},
    "Bahrain - Premier League": {"GP": 35, "HomeW%": 0.34, "Draw%": 0.34, "AwayW%": 0.31, "AvgGoals": 2.40, "AvgHG": 1.31, "AvgAG": 1.09},
    "Bangladesh - Premier League": {"GP": 10, "HomeW%": 0.20, "Draw%": 0.40, "AwayW%": 0.40, "AvgGoals": 2.00, "AvgHG": 0.90, "AvgAG": 1.10},
    "Belarus - Vysshaya Liga": {"GP": 216, "HomeW%": 0.43, "Draw%": 0.22, "AwayW%": 0.35, "AvgGoals": 2.54, "AvgHG": 1.38, "AvgAG": 1.16},
    "Belgium - Pro League": {"GP": 104, "HomeW%": 0.44, "Draw%": 0.27, "AwayW%": 0.29, "AvgGoals": 2.58, "AvgHG": 1.47, "AvgAG": 1.11},
    "Belgium - Challenger Pro League": {"GP": 96, "HomeW%": 0.34, "Draw%": 0.27, "AwayW%": 0.39, "AvgGoals": 2.76, "AvgHG": 1.33, "AvgAG": 1.43},
    "Bolivia - Division Profesional": {"GP": 191, "HomeW%": 0.52, "Draw%": 0.23, "AwayW%": 0.26, "AvgGoals": 3.42, "AvgHG": 2.09, "AvgAG": 1.34},
    "Bosnia and Herzegovina - Premier Liga": {"GP": 64, "HomeW%": 0.52, "Draw%": 0.25, "AwayW%": 0.23, "AvgGoals": 2.33, "AvgHG": 1.47, "AvgAG": 0.86},
    "Brazil - Serie A": {"GP": 314, "HomeW%": 0.50, "Draw%": 0.26, "AwayW%": 0.24, "AvgGoals": 2.41, "AvgHG": 1.46, "AvgAG": 0.95},
    "Brazil - Serie B": {"GP": 350, "HomeW%": 0.45, "Draw%": 0.30, "AwayW%": 0.24, "AvgGoals": 2.22, "AvgHG": 1.29, "AvgAG": 0.94},
    "Brazil - Serie C": {"GP": 190, "HomeW%": 0.46, "Draw%": 0.32, "AwayW%": 0.23, "AvgGoals": 2.06, "AvgHG": 1.17, "AvgAG": 0.89},
    "Brazil - Brasileiro Women": {"GP": 120, "HomeW%": 0.45, "Draw%": 0.26, "AwayW%": 0.29, "AvgGoals": 3.10, "AvgHG": 1.78, "AvgAG": 1.33},
    "Brazil - Carioca": {"GP": 66, "HomeW%": 0.41, "Draw%": 0.32, "AwayW%": 0.27, "AvgGoals": 2.18, "AvgHG": 1.20, "AvgAG": 0.98},
    "Brazil - Gaucho": {"GP": 48, "HomeW%": 0.42, "Draw%": 0.33, "AwayW%": 0.25, "AvgGoals": 2.15, "AvgHG": 1.29, "AvgAG": 0.85},
    "Bulgaria - Parva Liga": {"GP": 111, "HomeW%": 0.40, "Draw%": 0.33, "AwayW%": 0.27, "AvgGoals": 2.39, "AvgHG": 1.34, "AvgAG": 1.05},
    "Bulgaria - Vtora Liga": {"GP": 111, "HomeW%": 0.42, "Draw%": 0.29, "AwayW%": 0.29, "AvgGoals": 2.46, "AvgHG": 1.41, "AvgAG": 1.05},
    "Canada - Premier League": {"GP": 112, "HomeW%": 0.44, "Draw%": 0.29, "AwayW%": 0.27, "AvgGoals": 3.00, "AvgHG": 1.71, "AvgAG": 1.29},
    "Chile - Liga de Primera": {"GP": 208, "HomeW%": 0.51, "Draw%": 0.23, "AwayW%": 0.26, "AvgGoals": 2.61, "AvgHG": 1.54, "AvgAG": 1.07},
    "Chile - Liga de Ascenso": {"GP": 240, "HomeW%": 0.42, "Draw%": 0.30, "AwayW%": 0.27, "AvgGoals": 2.34, "AvgHG": 1.38, "AvgAG": 0.96},
    "China - Super League": {"GP": 232, "HomeW%": 0.47, "Draw%": 0.25, "AwayW%": 0.27, "AvgGoals": 3.21, "AvgHG": 1.81, "AvgAG": 1.40},
    "China - League One": {"GP": 231, "HomeW%": 0.45, "Draw%": 0.27, "AwayW%": 0.28, "AvgGoals": 2.56, "AvgHG": 1.44, "AvgAG": 1.12},
    "China - League Two": {"GP": 359, "HomeW%": 0.40, "Draw%": 0.28, "AwayW%": 0.32, "AvgGoals": 2.26, "AvgHG": 1.23, "AvgAG": 1.03},
    "Colombia - Primera A - Apertura": {"GP": 200, "HomeW%": 0.48, "Draw%": 0.29, "AwayW%": 0.23, "AvgGoals": 2.19, "AvgHG": 1.31, "AvgAG": 0.88},
    "Colombia - Primera A - Clausura": {"GP": 179, "HomeW%": 0.45, "Draw%": 0.28, "AwayW%": 0.26, "AvgGoals": 2.49, "AvgHG": 1.41, "AvgAG": 1.08},
    "Colombia - Primera B - Apertura": {"GP": 128, "HomeW%": 0.45, "Draw%": 0.27, "AwayW%": 0.29, "AvgGoals": 2.41, "AvgHG": 1.43, "AvgAG": 0.98},
    "Costa Rica - Primera Div. - Apertura": {"GP": 74, "HomeW%": 0.41, "Draw%": 0.31, "AwayW%": 0.28, "AvgGoals": 2.43, "AvgHG": 1.32, "AvgAG": 1.11},
    "Costa Rica - Primera Div. - Clausura": {"GP": 132, "HomeW%": 0.40, "Draw%": 0.30, "AwayW%": 0.30, "AvgGoals": 2.25, "AvgHG": 1.25, "AvgAG": 1.00},
    "Croatia - 1. HNL": {"GP": 60, "HomeW%": 0.45, "Draw%": 0.27, "AwayW%": 0.28, "AvgGoals": 2.60, "AvgHG": 1.45, "AvgAG": 1.15},
    "Croatia - 1. NL": {"GP": 79, "HomeW%": 0.46, "Draw%": 0.29, "AwayW%": 0.25, "AvgGoals": 2.14, "AvgHG": 1.24, "AvgAG": 0.90},
    "Cyprus - Cyprus League": {"GP": 63, "HomeW%": 0.46, "Draw%": 0.19, "AwayW%": 0.35, "AvgGoals": 2.60, "AvgHG": 1.44, "AvgAG": 1.16},
    "Cyprus - Division 2": {"GP": 54, "HomeW%": 0.33, "Draw%": 0.20, "AwayW%": 0.46, "AvgGoals": 2.59, "AvgHG": 1.22, "AvgAG": 1.37},
    "Czech Republic - 1. Liga": {"GP": 112, "HomeW%": 0.36, "Draw%": 0.32, "AwayW%": 0.32, "AvgGoals": 2.46, "AvgHG": 1.22, "AvgAG": 1.24},
    "Czech Republic - FNL": {"GP": 116, "HomeW%": 0.46, "Draw%": 0.20, "AwayW%": 0.34, "AvgGoals": 2.82, "AvgHG": 1.60, "AvgAG": 1.22},
    "Czech Republic - 1. Liga Women": {"GP": 36, "HomeW%": 0.53, "Draw%": 0.11, "AwayW%": 0.36, "AvgGoals": 4.31, "AvgHG": 2.72, "AvgAG": 1.58},
    "Denmark - Superligaen": {"GP": 84, "HomeW%": 0.45, "Draw%": 0.19, "AwayW%": 0.36, "AvgGoals": 3.24, "AvgHG": 1.69, "AvgAG": 1.55},
    "Denmark - 1st Division": {"GP": 90, "HomeW%": 0.41, "Draw%": 0.28, "AwayW%": 0.31, "AvgGoals": 2.77, "AvgHG": 1.50, "AvgAG": 1.27},
    "Denmark - 2nd Division": {"GP": 84, "HomeW%": 0.46, "Draw%": 0.17, "AwayW%": 0.37, "AvgGoals": 2.76, "AvgHG": 1.57, "AvgAG": 1.19},
    "Ecuador - Liga Pro": {"GP": 269, "HomeW%": 0.41, "Draw%": 0.29, "AwayW%": 0.30, "AvgGoals": 2.55, "AvgHG": 1.38, "AvgAG": 1.17},
    "Egypt - Premier League": {"GP": 127, "HomeW%": 0.31, "Draw%": 0.39, "AwayW%": 0.29, "AvgGoals": 1.86, "AvgHG": 0.94, "AvgAG": 0.92},
    "England - Premier League": {"GP": 100, "HomeW%": 0.51, "Draw%": 0.21, "AwayW%": 0.28, "AvgGoals": 2.68, "AvgHG": 1.55, "AvgAG": 1.13},
    "England - Championship": {"GP": 167, "HomeW%": 0.39, "Draw%": 0.29, "AwayW%": 0.32, "AvgGoals": 2.49, "AvgHG": 1.28, "AvgAG": 1.20},
    "England - League One": {"GP": 164, "HomeW%": 0.48, "Draw%": 0.22, "AwayW%": 0.30, "AvgGoals": 2.43, "AvgHG": 1.40, "AvgAG": 1.03},
    "England - League Two": {"GP": 168, "HomeW%": 0.42, "Draw%": 0.24, "AwayW%": 0.33, "AvgGoals": 2.63, "AvgHG": 1.43, "AvgAG": 1.19},
    "England - National League": {"GP": 199, "HomeW%": 0.41, "Draw%": 0.27, "AwayW%": 0.32, "AvgGoals": 2.75, "AvgHG": 1.52, "AvgAG": 1.23},
    "England - National L. North": {"GP": 180, "HomeW%": 0.44, "Draw%": 0.23, "AwayW%": 0.33, "AvgGoals": 3.02, "AvgHG": 1.59, "AvgAG": 1.43},
    "England - National L. South": {"GP": 180, "HomeW%": 0.41, "Draw%": 0.28, "AwayW%": 0.31, "AvgGoals": 2.57, "AvgHG": 1.38, "AvgAG": 1.19},
    "England - Women Super League": {"GP": 41, "HomeW%": 0.46, "Draw%": 0.17, "AwayW%": 0.37, "AvgGoals": 2.88, "AvgHG": 1.34, "AvgAG": 1.54},
    "England - WSL 2": {"GP": 42, "HomeW%": 0.33, "Draw%": 0.24, "AwayW%": 0.43, "AvgGoals": 3.21, "AvgHG": 1.55, "AvgAG": 1.67},
    "Estonia - Meistriliiga": {"GP": 175, "HomeW%": 0.47, "Draw%": 0.13, "AwayW%": 0.41, "AvgGoals": 3.19, "AvgHG": 1.75, "AvgAG": 1.44},
    "FaroeIslands - Premier League": {"GP": 135, "HomeW%": 0.40, "Draw%": 0.20, "AwayW%": 0.40, "AvgGoals": 3.63, "AvgHG": 1.81, "AvgAG": 1.82},
    "Finland - Veikkausliiga": {"GP": 174, "HomeW%": 0.40, "Draw%": 0.23, "AwayW%": 0.37, "AvgGoals": 3.31, "AvgHG": 1.66, "AvgAG": 1.65},
    "Finland - Ykkosliga": {"GP": 135, "HomeW%": 0.43, "Draw%": 0.26, "AwayW%": 0.31, "AvgGoals": 3.28, "AvgHG": 1.74, "AvgAG": 1.54},
    "Finland - Ykkonen": {"GP": 162, "HomeW%": 0.52, "Draw%": 0.19, "AwayW%": 0.29, "AvgGoals": 3.48, "AvgHG": 2.02, "AvgAG": 1.46},
    "Finland - Kakkonen Group A": {"GP": 90, "HomeW%": 0.52, "Draw%": 0.12, "AwayW%": 0.36, "AvgGoals": 4.32, "AvgHG": 2.43, "AvgAG": 1.89},
    "Finland - Kakkonen Group B": {"GP": 90, "HomeW%": 0.44, "Draw%": 0.17, "AwayW%": 0.39, "AvgGoals": 3.84, "AvgHG": 2.12, "AvgAG": 1.72},
    "Finland - Kakkonen Group C": {"GP": 72, "HomeW%": 0.51, "Draw%": 0.10, "AwayW%": 0.39, "AvgGoals": 4.43, "AvgHG": 2.56, "AvgAG": 1.88},
    "Finland - Kansallinen Liiga Women": {"GP": 56, "HomeW%": 0.48, "Draw%": 0.16, "AwayW%": 0.36, "AvgGoals": 3.52, "AvgHG": 1.82, "AvgAG": 1.70},
    "France - Ligue 1": {"GP": 99, "HomeW%": 0.52, "Draw%": 0.23, "AwayW%": 0.25, "AvgGoals": 2.93, "AvgHG": 1.77, "AvgAG": 1.16},
    "France - Ligue 2": {"GP": 116, "HomeW%": 0.37, "Draw%": 0.29, "AwayW%": 0.34, "AvgGoals": 2.57, "AvgHG": 1.35, "AvgAG": 1.22},
    "France - National": {"GP": 96, "HomeW%": 0.41, "Draw%": 0.32, "AwayW%": 0.27, "AvgGoals": 2.34, "AvgHG": 1.33, "AvgAG": 1.01},
    "France - Premiere Ligue Women": {"GP": 36, "HomeW%": 0.53, "Draw%": 0.17, "AwayW%": 0.31, "AvgGoals": 3.44, "AvgHG": 1.97, "AvgAG": 1.47},
    "Georgia - Erovnuli Liga": {"GP": 154, "HomeW%": 0.40, "Draw%": 0.25, "AwayW%": 0.36, "AvgGoals": 2.53, "AvgHG": 1.35, "AvgAG": 1.18},
    "Georgia - Erovnuli Liga 2": {"GP": 155, "HomeW%": 0.37, "Draw%": 0.34, "AwayW%": 0.28, "AvgGoals": 2.41, "AvgHG": 1.29, "AvgAG": 1.12},
    "Germany - Bundesliga": {"GP": 81, "HomeW%": 0.42, "Draw%": 0.20, "AwayW%": 0.38, "AvgGoals": 3.17, "AvgHG": 1.63, "AvgAG": 1.54},
    "Germany - 2. Bundesliga": {"GP": 99, "HomeW%": 0.46, "Draw%": 0.19, "AwayW%": 0.34, "AvgGoals": 2.88, "AvgHG": 1.51, "AvgAG": 1.37},
    "Germany - 3. Liga": {"GP": 130, "HomeW%": 0.45, "Draw%": 0.25, "AwayW%": 0.31, "AvgGoals": 3.18, "AvgHG": 1.71, "AvgAG": 1.47},
    "Germany - Regionalliga Nord": {"GP": 149, "HomeW%": 0.44, "Draw%": 0.18, "AwayW%": 0.38, "AvgGoals": 3.75, "AvgHG": 2.01, "AvgAG": 1.74},
    "Germany - Regionalliga Nordost": {"GP": 123, "HomeW%": 0.47, "Draw%": 0.24, "AwayW%": 0.29, "AvgGoals": 2.78, "AvgHG": 1.55, "AvgAG": 1.23},
    "Germany - Regionalliga West": {"GP": 129, "HomeW%": 0.37, "Draw%": 0.27, "AwayW%": 0.36, "AvgGoals": 3.25, "AvgHG": 1.71, "AvgAG": 1.53},
    "Germany - Regionalliga Sudwest": {"GP": 135, "HomeW%": 0.41, "Draw%": 0.27, "AwayW%": 0.33, "AvgGoals": 3.69, "AvgHG": 1.99, "AvgAG": 1.70},
    "Germany - Regionalliga Bayern": {"GP": 141, "HomeW%": 0.40, "Draw%": 0.25, "AwayW%": 0.35, "AvgGoals": 3.09, "AvgHG": 1.57, "AvgAG": 1.52},
    "Germany - Bundesliga Women": {"GP": 61, "HomeW%": 0.46, "Draw%": 0.16, "AwayW%": 0.38, "AvgGoals": 3.66, "AvgHG": 1.87, "AvgAG": 1.79},
    "Germany - 2. Bundesliga Women": {"GP": 62, "HomeW%": 0.39, "Draw%": 0.29, "AwayW%": 0.32, "AvgGoals": 3.50, "AvgHG": 2.10, "AvgAG": 1.40},
    "Gibraltar - Premier Division": {"GP": 56, "HomeW%": 0.39, "Draw%": 0.12, "AwayW%": 0.48, "AvgGoals": 3.61, "AvgHG": 1.73, "AvgAG": 1.88},
    "Greece - Super League": {"GP": 62, "HomeW%": 0.44, "Draw%": 0.24, "AwayW%": 0.32, "AvgGoals": 2.77, "AvgHG": 1.52, "AvgAG": 1.26},
    "Guatemala - Liga Nacional - Apertura": {"GP": 105, "HomeW%": 0.56, "Draw%": 0.22, "AwayW%": 0.22, "AvgGoals": 2.49, "AvgHG": 1.57, "AvgAG": 0.91},
    "Guatemala - Liga Nacional - Clausura": {"GP": 110, "HomeW%": 0.55, "Draw%": 0.25, "AwayW%": 0.19, "AvgGoals": 2.42, "AvgHG": 1.51, "AvgAG": 0.91},
    "Hong Kong - Premier League": {"GP": 108, "HomeW%": 0.43, "Draw%": 0.18, "AwayW%": 0.40, "AvgGoals": 3.62, "AvgHG": 1.90, "AvgAG": 1.72},
    "Hungary - NB I": {"GP": 71, "HomeW%": 0.34, "Draw%": 0.31, "AwayW%": 0.35, "AvgGoals": 3.20, "AvgHG": 1.63, "AvgAG": 1.56},
    "Hungary - NB II": {"GP": 96, "HomeW%": 0.51, "Draw%": 0.25, "AwayW%": 0.24, "AvgGoals": 2.63, "AvgHG": 1.50, "AvgAG": 1.13},
    "Iceland - Besta deild": {"GP": 132, "HomeW%": 0.54, "Draw%": 0.22, "AwayW%": 0.24, "AvgGoals": 3.23, "AvgHG": 1.91, "AvgAG": 1.32},
    "Iceland - 1. Deild": {"GP": 132, "HomeW%": 0.39, "Draw%": 0.20, "AwayW%": 0.41, "AvgGoals": 3.56, "AvgHG": 1.81, "AvgAG": 1.75},
    "Iceland - 2. Deild": {"GP": 132, "HomeW%": 0.47, "Draw%": 0.17, "AwayW%": 0.36, "AvgGoals": 3.58, "AvgHG": 1.91, "AvgAG": 1.67},
    "Iceland - Besta deild Women": {"GP": 111, "HomeW%": 0.52, "Draw%": 0.11, "AwayW%": 0.37, "AvgGoals": 3.83, "AvgHG": 2.10, "AvgAG": 1.73},
    "India - Super League": {"GP": 156, "HomeW%": 0.42, "Draw%": 0.24, "AwayW%": 0.33, "AvgGoals": 2.87, "AvgHG": 1.49, "AvgAG": 1.38},
    "India - I-League": {"GP": 132, "HomeW%": 0.43, "Draw%": 0.27, "AwayW%": 0.30, "AvgGoals": 3.17, "AvgHG": 1.83, "AvgAG": 1.34},
    "Indonesia - Liga 1": {"GP": 89, "HomeW%": 0.39, "Draw%": 0.25, "AwayW%": 0.36, "AvgGoals": 2.53, "AvgHG": 1.36, "AvgAG": 1.17},
    "Iran - Pro League": {"GP": 70, "HomeW%": 0.31, "Draw%": 0.43, "AwayW%": 0.26, "AvgGoals": 1.87, "AvgHG": 0.97, "AvgAG": 0.90},
    "Ireland - Premier Division": {"GP": 180, "HomeW%": 0.43, "Draw%": 0.29, "AwayW%": 0.28, "AvgGoals": 2.43, "AvgHG": 1.38, "AvgAG": 1.05},
    "Ireland - First Division": {"GP": 179, "HomeW%": 0.45, "Draw%": 0.23, "AwayW%": 0.32, "AvgGoals": 2.80, "AvgHG": 1.54, "AvgAG": 1.26},
    "Ireland - Women National League": {"GP": 130, "HomeW%": 0.47, "Draw%": 0.12, "AwayW%": 0.41, "AvgGoals": 3.49, "AvgHG": 1.77, "AvgAG": 1.72},
    "Israel - Ligat HaAl": {"GP": 63, "HomeW%": 0.41, "Draw%": 0.22, "AwayW%": 0.37, "AvgGoals": 3.08, "AvgHG": 1.62, "AvgAG": 1.46},
    "Italy - Serie A": {"GP": 100, "HomeW%": 0.37, "Draw%": 0.33, "AwayW%": 0.30, "AvgGoals": 2.26, "AvgHG": 1.23, "AvgAG": 1.03},
    "Italy - Serie B": {"GP": 109, "HomeW%": 0.42, "Draw%": 0.36, "AwayW%": 0.22, "AvgGoals": 2.57, "AvgHG": 1.48, "AvgAG": 1.09},
    "Italy - Serie C - Group A": {"GP": 120, "HomeW%": 0.33, "Draw%": 0.34, "AwayW%": 0.32, "AvgGoals": 2.34, "AvgHG": 1.25, "AvgAG": 1.09},
    "Italy - Serie C - Group B": {"GP": 120, "HomeW%": 0.36, "Draw%": 0.26, "AwayW%": 0.38, "AvgGoals": 2.29, "AvgHG": 1.13, "AvgAG": 1.16},
    "Italy - Serie C - Group C": {"GP": 120, "HomeW%": 0.41, "Draw%": 0.29, "AwayW%": 0.30, "AvgGoals": 2.63, "AvgHG": 1.51, "AvgAG": 1.12},
    "Italy - Serie A Women": {"GP": 24, "HomeW%": 0.50, "Draw%": 0.17, "AwayW%": 0.33, "AvgGoals": 3.00, "AvgHG": 1.79, "AvgAG": 1.21},
    "Jamaica - Premier League": {"GP": 56, "HomeW%": 0.36, "Draw%": 0.29, "AwayW%": 0.36, "AvgGoals": 2.57, "AvgHG": 1.34, "AvgAG": 1.23},
    "Japan - J1 League": {"GP": 350, "HomeW%": 0.44, "Draw%": 0.26, "AwayW%": 0.30, "AvgGoals": 2.39, "AvgHG": 1.31, "AvgAG": 1.08},
    "Japan - J2 League": {"GP": 350, "HomeW%": 0.37, "Draw%": 0.28, "AwayW%": 0.35, "AvgGoals": 2.45, "AvgHG": 1.26, "AvgAG": 1.19},
    "Japan - J3 League": {"GP": 340, "HomeW%": 0.46, "Draw%": 0.24, "AwayW%": 0.30, "AvgGoals": 2.52, "AvgHG": 1.39, "AvgAG": 1.13},
    "Japan - WE League": {"GP": 73, "HomeW%": 0.42, "Draw%": 0.25, "AwayW%": 0.33, "AvgGoals": 2.70, "AvgHG": 1.56, "AvgAG": 1.14},
    "Japan - Nadeshiko League 1": {"GP": 132, "HomeW%": 0.42, "Draw%": 0.30, "AwayW%": 0.28, "AvgGoals": 2.56, "AvgHG": 1.41, "AvgAG": 1.15},
    "Jordan - Premier League": {"GP": 49, "HomeW%": 0.41, "Draw%": 0.20, "AwayW%": 0.39, "AvgGoals": 2.59, "AvgHG": 1.27, "AvgAG": 1.33},
    "Kazakhstan - Premier League": {"GP": 182, "HomeW%": 0.42, "Draw%": 0.28, "AwayW%": 0.30, "AvgGoals": 2.73, "AvgHG": 1.52, "AvgAG": 1.20},
    "Kuwait - Premier League": {"GP": 35, "HomeW%": 0.34, "Draw%": 0.29, "AwayW%": 0.37, "AvgGoals": 2.14, "AvgHG": 1.09, "AvgAG": 1.06},
    "Latvia - Virsliga": {"GP": 175, "HomeW%": 0.46, "Draw%": 0.23, "AwayW%": 0.31, "AvgGoals": 2.94, "AvgHG": 1.66, "AvgAG": 1.28},
    "Latvia - 1. Liga": {"GP": 175, "HomeW%": 0.45, "Draw%": 0.21, "AwayW%": 0.34, "AvgGoals": 3.29, "AvgHG": 1.82, "AvgAG": 1.47},
    "Lithuania - A Lyga": {"GP": 175, "HomeW%": 0.41, "Draw%": 0.23, "AwayW%": 0.36, "AvgGoals": 2.66, "AvgHG": 1.43, "AvgAG": 1.23},
    "Lithuania - 1st League": {"GP": 232, "HomeW%": 0.39, "Draw%": 0.17, "AwayW%": 0.44, "AvgGoals": 3.02, "AvgHG": 1.47, "AvgAG": 1.55},
    "Malaysia - Super League": {"GP": 52, "HomeW%": 0.40, "Draw%": 0.27, "AwayW%": 0.33, "AvgGoals": 3.35, "AvgHG": 1.87, "AvgAG": 1.48},
    "Mexico - Liga MX - Apertura": {"GP": 144, "HomeW%": 0.47, "Draw%": 0.26, "AwayW%": 0.28, "AvgGoals": 3.10, "AvgHG": 1.78, "AvgAG": 1.33},
    "Mexico - Liga MX - Clausura": {"GP": 153, "HomeW%": 0.48, "Draw%": 0.20, "AwayW%": 0.31, "AvgGoals": 2.86, "AvgHG": 1.56, "AvgAG": 1.30},
    "Moldova - Divizia Nationala": {"GP": 72, "HomeW%": 0.43, "Draw%": 0.18, "AwayW%": 0.39, "AvgGoals": 3.11, "AvgHG": 1.64, "AvgAG": 1.47},
    "Montenegro - First League": {"GP": 66, "HomeW%": 0.45, "Draw%": 0.30, "AwayW%": 0.24, "AvgGoals": 2.73, "AvgHG": 1.64, "AvgAG": 1.09},
    "Morocco - Botola Pro": {"GP": 54, "HomeW%": 0.37, "Draw%": 0.37, "AwayW%": 0.26, "AvgGoals": 2.22, "AvgHG": 1.17, "AvgAG": 1.06},
    "Netherlands - Eredivisie": {"GP": 99, "HomeW%": 0.48, "Draw%": 0.21, "AwayW%": 0.30, "AvgGoals": 3.43, "AvgHG": 1.90, "AvgAG": 1.54},
    "Netherlands - Eerste Divisie": {"GP": 138, "HomeW%": 0.45, "Draw%": 0.21, "AwayW%": 0.34, "AvgGoals": 3.23, "AvgHG": 1.80, "AvgAG": 1.43},
    "Netherlands - Tweede Divisie": {"GP": 98, "HomeW%": 0.49, "Draw%": 0.17, "AwayW%": 0.34, "AvgGoals": 3.19, "AvgHG": 1.77, "AvgAG": 1.43},
    "Netherlands - Eredivisie Women": {"GP": 36, "HomeW%": 0.33, "Draw%": 0.14, "AwayW%": 0.53, "AvgGoals": 3.56, "AvgHG": 1.72, "AvgAG": 1.83},
    "Northern Ireland - NIFL Premiership": {"GP": 77, "HomeW%": 0.49, "Draw%": 0.10, "AwayW%": 0.40, "AvgGoals": 2.65, "AvgHG": 1.39, "AvgAG": 1.26},
    "Northern Ireland - NIFL Championship": {"GP": 84, "HomeW%": 0.43, "Draw%": 0.26, "AwayW%": 0.31, "AvgGoals": 2.85, "AvgHG": 1.54, "AvgAG": 1.31},
    "North Macedonia - First League": {"GP": 70, "HomeW%": 0.44, "Draw%": 0.21, "AwayW%": 0.34, "AvgGoals": 3.01, "AvgHG": 1.64, "AvgAG": 1.37},
    "Norway - Eliteserien": {"GP": 216, "HomeW%": 0.48, "Draw%": 0.20, "AwayW%": 0.32, "AvgGoals": 3.16, "AvgHG": 1.76, "AvgAG": 1.39},
    "Norway - 1st Division": {"GP": 232, "HomeW%": 0.41, "Draw%": 0.26, "AwayW%": 0.33, "AvgGoals": 3.22, "AvgHG": 1.67, "AvgAG": 1.54},
    "Norway - Division 2 - Gr. 1": {"GP": 182, "HomeW%": 0.46, "Draw%": 0.30, "AwayW%": 0.24, "AvgGoals": 3.37, "AvgHG": 1.99, "AvgAG": 1.38},
    "Norway - Division 2 - Gr. 2": {"GP": 182, "HomeW%": 0.51, "Draw%": 0.14, "AwayW%": 0.35, "AvgGoals": 3.70, "AvgHG": 2.08, "AvgAG": 1.62},
    "Norway - Toppserien Women": {"GP": 125, "HomeW%": 0.50, "Draw%": 0.14, "AwayW%": 0.36, "AvgGoals": 3.16, "AvgHG": 1.81, "AvgAG": 1.35},
    "Norway - 1. Division Women": {"GP": 132, "HomeW%": 0.48, "Draw%": 0.22, "AwayW%": 0.30, "AvgGoals": 3.21, "AvgHG": 1.81, "AvgAG": 1.40},
    "Paraguay - Primera Div. - Apertura": {"GP": 132, "HomeW%": 0.33, "Draw%": 0.36, "AwayW%": 0.32, "AvgGoals": 2.18, "AvgHG": 1.06, "AvgAG": 1.12},
    "Paraguay - Primera Div. - Clausura": {"GP": 114, "HomeW%": 0.42, "Draw%": 0.27, "AwayW%": 0.31, "AvgGoals": 2.60, "AvgHG": 1.42, "AvgAG": 1.18},
    "Peru - Liga 1 - Apertura": {"GP": 171, "HomeW%": 0.49, "Draw%": 0.26, "AwayW%": 0.26, "AvgGoals": 2.71, "AvgHG": 1.65, "AvgAG": 1.06},
    "Peru - Liga 1 - Clausura": {"GP": 142, "HomeW%": 0.47, "Draw%": 0.25, "AwayW%": 0.28, "AvgGoals": 2.52, "AvgHG": 1.49, "AvgAG": 1.03},
    "Poland - Ekstraklasa": {"GP": 121, "HomeW%": 0.49, "Draw%": 0.28, "AwayW%": 0.23, "AvgGoals": 2.88, "AvgHG": 1.71, "AvgAG": 1.17},
    "Poland - 1. Liga": {"GP": 134, "HomeW%": 0.44, "Draw%": 0.28, "AwayW%": 0.28, "AvgGoals": 3.10, "AvgHG": 1.72, "AvgAG": 1.38},
    "Poland - 2. Liga": {"GP": 135, "HomeW%": 0.38, "Draw%": 0.31, "AwayW%": 0.31, "AvgGoals": 3.02, "AvgHG": 1.57, "AvgAG": 1.45},
    "Poland - Ekstraliga Women": {"GP": 57, "HomeW%": 0.46, "Draw%": 0.16, "AwayW%": 0.39, "AvgGoals": 3.18, "AvgHG": 1.68, "AvgAG": 1.49},
    "Portugal - Liga Portugal": {"GP": 90, "HomeW%": 0.37, "Draw%": 0.24, "AwayW%": 0.39, "AvgGoals": 2.66, "AvgHG": 1.37, "AvgAG": 1.29},
    "Portugal - Liga Portugal 2": {"GP": 87, "HomeW%": 0.39, "Draw%": 0.29, "AwayW%": 0.32, "AvgGoals": 2.61, "AvgHG": 1.36, "AvgAG": 1.25},
    "Portugal - First Division Women": {"GP": 25, "HomeW%": 0.24, "Draw%": 0.28, "AwayW%": 0.48, "AvgGoals": 3.20, "AvgHG": 1.40, "AvgAG": 1.80},
    "Qatar - Stars League": {"GP": 49, "HomeW%": 0.53, "Draw%": 0.16, "AwayW%": 0.31, "AvgGoals": 3.20, "AvgHG": 1.76, "AvgAG": 1.45},
    "Qatar - Division 2": {"GP": 20, "HomeW%": 0.45, "Draw%": 0.25, "AwayW%": 0.30, "AvgGoals": 3.00, "AvgHG": 1.55, "AvgAG": 1.45},
    "Romania - Liga 1": {"GP": 120, "HomeW%": 0.38, "Draw%": 0.32, "AwayW%": 0.29, "AvgGoals": 2.56, "AvgHG": 1.38, "AvgAG": 1.18},
    "Romania - Liga 2": {"GP": 131, "HomeW%": 0.47, "Draw%": 0.22, "AwayW%": 0.31, "AvgGoals": 2.78, "AvgHG": 1.62, "AvgAG": 1.16},
    "Romania - Superliga Women": {"GP": 40, "HomeW%": 0.50, "Draw%": 0.20, "AwayW%": 0.30, "AvgGoals": 3.33, "AvgHG": 1.95, "AvgAG": 1.38},
    "Russia - Premier League": {"GP": 112, "HomeW%": 0.46, "Draw%": 0.30, "AwayW%": 0.24, "AvgGoals": 2.64, "AvgHG": 1.46, "AvgAG": 1.18},
    "Russia - FNL": {"GP": 153, "HomeW%": 0.41, "Draw%": 0.33, "AwayW%": 0.26, "AvgGoals": 2.29, "AvgHG": 1.28, "AvgAG": 1.01},
    "Rwanda - Premier League": {"GP": 46, "HomeW%": 0.35, "Draw%": 0.37, "AwayW%": 0.28, "AvgGoals": 1.67, "AvgHG": 0.85, "AvgAG": 0.83},
    "SanMarino - Campionato Sammarinese": {"GP": 64, "HomeW%": 0.42, "Draw%": 0.23, "AwayW%": 0.34, "AvgGoals": 2.73, "AvgHG": 1.38, "AvgAG": 1.36},
    "Saudi Arabia - Professional League": {"GP": 63, "HomeW%": 0.40, "Draw%": 0.24, "AwayW%": 0.37, "AvgGoals": 3.10, "AvgHG": 1.62, "AvgAG": 1.48},
    "Saudi Arabia - Division 1": {"GP": 61, "HomeW%": 0.30, "Draw%": 0.26, "AwayW%": 0.44, "AvgGoals": 2.87, "AvgHG": 1.25, "AvgAG": 1.62},
    "Scotland - Premiership": {"GP": 63, "HomeW%": 0.37, "Draw%": 0.35, "AwayW%": 0.29, "AvgGoals": 2.73, "AvgHG": 1.57, "AvgAG": 1.16},
    "Scotland - Championship": {"GP": 65, "HomeW%": 0.35, "Draw%": 0.35, "AwayW%": 0.29, "AvgGoals": 2.42, "AvgHG": 1.31, "AvgAG": 1.11},
    "Scotland - League One": {"GP": 60, "HomeW%": 0.42, "Draw%": 0.18, "AwayW%": 0.40, "AvgGoals": 2.55, "AvgHG": 1.28, "AvgAG": 1.27},
    "Scotland - League Two": {"GP": 55, "HomeW%": 0.35, "Draw%": 0.25, "AwayW%": 0.40, "AvgGoals": 3.00, "AvgHG": 1.49, "AvgAG": 1.51},
    "Scotland - SWPL 1 Women": {"GP": 50, "HomeW%": 0.44, "Draw%": 0.12, "AwayW%": 0.44, "AvgGoals": 3.96, "AvgHG": 2.16, "AvgAG": 1.80},
    "Serbia - Super Liga": {"GP": 110, "HomeW%": 0.50, "Draw%": 0.24, "AwayW%": 0.26, "AvgGoals": 2.91, "AvgHG": 1.67, "AvgAG": 1.24},
    "Serbia - Prva Liga": {"GP": 127, "HomeW%": 0.42, "Draw%": 0.33, "AwayW%": 0.25, "AvgGoals": 2.30, "AvgHG": 1.36, "AvgAG": 0.94},
    "Singapore - Premier League": {"GP": 19, "HomeW%": 0.32, "Draw%": 0.16, "AwayW%": 0.53, "AvgGoals": 3.63, "AvgHG": 1.42, "AvgAG": 2.21},
    "Slovakia - 1. Liga": {"GP": 76, "HomeW%": 0.37, "Draw%": 0.26, "AwayW%": 0.37, "AvgGoals": 3.05, "AvgHG": 1.54, "AvgAG": 1.51},
    "Slovakia - 2. Liga": {"GP": 121, "HomeW%": 0.50, "Draw%": 0.24, "AwayW%": 0.26, "AvgGoals": 3.12, "AvgHG": 1.78, "AvgAG": 1.35},
    "Slovakia - 1.Liga Women": {"GP": 58, "HomeW%": 0.41, "Draw%": 0.16, "AwayW%": 0.43, "AvgGoals": 3.62, "AvgHG": 1.91, "AvgAG": 1.71},
    "Slovenia - Prva Liga": {"GP": 70, "HomeW%": 0.43, "Draw%": 0.21, "AwayW%": 0.36, "AvgGoals": 3.20, "AvgHG": 1.64, "AvgAG": 1.56},
    "South Africa - Premier Division": {"GP": 93, "HomeW%": 0.53, "Draw%": 0.25, "AwayW%": 0.23, "AvgGoals": 2.00, "AvgHG": 1.19, "AvgAG": 0.81},
    "South Africa - First Division": {"GP": 78, "HomeW%": 0.42, "Draw%": 0.32, "AwayW%": 0.26, "AvgGoals": 2.15, "AvgHG": 1.22, "AvgAG": 0.94},
    "South Korea - K League 1": {"GP": 198, "HomeW%": 0.42, "Draw%": 0.26, "AwayW%": 0.32, "AvgGoals": 2.59, "AvgHG": 1.39, "AvgAG": 1.20},
    "South Korea - K League 2": {"GP": 259, "HomeW%": 0.35, "Draw%": 0.30, "AwayW%": 0.35, "AvgGoals": 2.52, "AvgHG": 1.32, "AvgAG": 1.20},
    "South Korea - WK League Women": {"GP": 112, "HomeW%": 0.41, "Draw%": 0.29, "AwayW%": 0.30, "AvgGoals": 2.63, "AvgHG": 1.40, "AvgAG": 1.23},
    "Spain - LaLiga": {"GP": 110, "HomeW%": 0.48, "Draw%": 0.25, "AwayW%": 0.26, "AvgGoals": 2.66, "AvgHG": 1.53, "AvgAG": 1.14},
    "Spain - LaLiga2": {"GP": 132, "HomeW%": 0.42, "Draw%": 0.29, "AwayW%": 0.29, "AvgGoals": 2.48, "AvgHG": 1.37, "AvgAG": 1.11},
    "Spain - Liga F Women": {"GP": 72, "HomeW%": 0.32, "Draw%": 0.32, "AwayW%": 0.36, "AvgGoals": 2.63, "AvgHG": 1.24, "AvgAG": 1.39},
    "Spain - Primera F. Women": {"GP": 56, "HomeW%": 0.48, "Draw%": 0.23, "AwayW%": 0.29, "AvgGoals": 2.38, "AvgHG": 1.45, "AvgAG": 0.93},
    "Sweden - Allsvenskan": {"GP": 232, "HomeW%": 0.39, "Draw%": 0.23, "AwayW%": 0.38, "AvgGoals": 2.84, "AvgHG": 1.47, "AvgAG": 1.38},
    "Sweden - Superettan": {"GP": 232, "HomeW%": 0.42, "Draw%": 0.27, "AwayW%": 0.31, "AvgGoals": 2.82, "AvgHG": 1.58, "AvgAG": 1.24},
    "Sweden - Div 1 - Norra": {"GP": 232, "HomeW%": 0.47, "Draw%": 0.19, "AwayW%": 0.34, "AvgGoals": 3.36, "AvgHG": 1.89, "AvgAG": 1.47},
    "Sweden - Div 1 - Sodra": {"GP": 232, "HomeW%": 0.45, "Draw%": 0.23, "AwayW%": 0.32, "AvgGoals": 3.00, "AvgHG": 1.65, "AvgAG": 1.34},
    "Sweden - Allsvenskan Women": {"GP": 168, "HomeW%": 0.47, "Draw%": 0.14, "AwayW%": 0.39, "AvgGoals": 3.32, "AvgHG": 1.69, "AvgAG": 1.63},
    "Sweden - Elitetan Women": {"GP": 167, "HomeW%": 0.44, "Draw%": 0.17, "AwayW%": 0.38, "AvgGoals": 3.15, "AvgHG": 1.69, "AvgAG": 1.46},
    "Switzerland - Super League": {"GP": 71, "HomeW%": 0.45, "Draw%": 0.20, "AwayW%": 0.35, "AvgGoals": 3.42, "AvgHG": 1.99, "AvgAG": 1.44},
    "Switzerland - Challenge League": {"GP": 60, "HomeW%": 0.50, "Draw%": 0.20, "AwayW%": 0.30, "AvgGoals": 2.95, "AvgHG": 1.62, "AvgAG": 1.33},
    "Switzerland - Women Super League": {"GP": 45, "HomeW%": 0.38, "Draw%": 0.22, "AwayW%": 0.40, "AvgGoals": 3.02, "AvgHG": 1.42, "AvgAG": 1.60},
    "Thailand - Thai League 1": {"GP": 78, "HomeW%": 0.40, "Draw%": 0.32, "AwayW%": 0.28, "AvgGoals": 2.76, "AvgHG": 1.56, "AvgAG": 1.19},
    "Turkey - Super Lig": {"GP": 99, "HomeW%": 0.37, "Draw%": 0.28, "AwayW%": 0.34, "AvgGoals": 2.52, "AvgHG": 1.23, "AvgAG": 1.28},
    "Turkey - 1. Lig": {"GP": 120, "HomeW%": 0.41, "Draw%": 0.34, "AwayW%": 0.25, "AvgGoals": 2.83, "AvgHG": 1.57, "AvgAG": 1.27},
    "Turkey - 2. Lig White Group": {"GP": 99, "HomeW%": 0.38, "Draw%": 0.21, "AwayW%": 0.40, "AvgGoals": 2.80, "AvgHG": 1.33, "AvgAG": 1.46},
    "Turkey - 2. Lig Red Group": {"GP": 99, "HomeW%": 0.48, "Draw%": 0.24, "AwayW%": 0.27, "AvgGoals": 3.14, "AvgHG": 1.74, "AvgAG": 1.40},
    "Turkey - 3. Lig Group 1": {"GP": 72, "HomeW%": 0.38, "Draw%": 0.19, "AwayW%": 0.43, "AvgGoals": 2.44, "AvgHG": 1.18, "AvgAG": 1.26},
    "Turkey - 3. Lig Group 2": {"GP": 72, "HomeW%": 0.31, "Draw%": 0.44, "AwayW%": 0.25, "AvgGoals": 2.32, "AvgHG": 1.19, "AvgAG": 1.13},
    "Turkey - 3. Lig Group 3": {"GP": 72, "HomeW%": 0.43, "Draw%": 0.28, "AwayW%": 0.29, "AvgGoals": 2.71, "AvgHG": 1.50, "AvgAG": 1.21},
    "Turkey - 3. Lig Group 4": {"GP": 72, "HomeW%": 0.44, "Draw%": 0.26, "AwayW%": 0.29, "AvgGoals": 2.69, "AvgHG": 1.49, "AvgAG": 1.21},
    "UAE - Pro League": {"GP": 49, "HomeW%": 0.43, "Draw%": 0.18, "AwayW%": 0.39, "AvgGoals": 2.45, "AvgHG": 1.31, "AvgAG": 1.14},
    "Ukraine - Premier League": {"GP": 88, "HomeW%": 0.34, "Draw%": 0.28, "AwayW%": 0.38, "AvgGoals": 2.57, "AvgHG": 1.23, "AvgAG": 1.34},
    "Ukraine - Persha Liga": {"GP": 109, "HomeW%": 0.39, "Draw%": 0.24, "AwayW%": 0.38, "AvgGoals": 2.23, "AvgHG": 1.13, "AvgAG": 1.10},
    "Uruguay - Liga AUF Uruguaya - Apertura": {"GP": 120, "HomeW%": 0.35, "Draw%": 0.32, "AwayW%": 0.33, "AvgGoals": 2.27, "AvgHG": 1.17, "AvgAG": 1.10},
    "Uruguay - Liga AUF Uruguaya - Intermediate": {"GP": 56, "HomeW%": 0.54, "Draw%": 0.23, "AwayW%": 0.23, "AvgGoals": 2.59, "AvgHG": 1.57, "AvgAG": 1.02},
    "Uruguay - Liga AUF Uruguaya - Clausura": {"GP": 112, "HomeW%": 0.43, "Draw%": 0.25, "AwayW%": 0.32, "AvgGoals": 2.31, "AvgHG": 1.29, "AvgAG": 1.03},
    "USA - MLS": {"GP": 510, "HomeW%": 0.44, "Draw%": 0.25, "AwayW%": 0.31, "AvgGoals": 3.00, "AvgHG": 1.64, "AvgAG": 1.36},
    "USA - USL Championship": {"GP": 360, "HomeW%": 0.44, "Draw%": 0.26, "AwayW%": 0.29, "AvgGoals": 2.70, "AvgHG": 1.51, "AvgAG": 1.19},
    "USA - USL League One": {"GP": 210, "HomeW%": 0.45, "Draw%": 0.29, "AwayW%": 0.26, "AvgGoals": 2.84, "AvgHG": 1.61, "AvgAG": 1.23},
    "USA - NWSL": {"GP": 182, "HomeW%": 0.39, "Draw%": 0.28, "AwayW%": 0.33, "AvgGoals": 2.66, "AvgHG": 1.40, "AvgAG": 1.26},
    "USA - USL Super League": {"GP": 40, "HomeW%": 0.28, "Draw%": 0.45, "AwayW%": 0.28, "AvgGoals": 3.10, "AvgHG": 1.70, "AvgAG": 1.40},
    "Venezuela - Liga FUTVE - Apertura": {"GP": 91, "HomeW%": 0.45, "Draw%": 0.29, "AwayW%": 0.26, "AvgGoals": 2.29, "AvgHG": 1.25, "AvgAG": 1.03},
    "Venezuela - Liga FUTVE - Clausura": {"GP": 91, "HomeW%": 0.54, "Draw%": 0.18, "AwayW%": 0.29, "AvgGoals": 2.38, "AvgHG": 1.46, "AvgAG": 0.92},
    "Vietnam - V League": {"GP": 67, "HomeW%": 0.42, "Draw%": 0.31, "AwayW%": 0.27, "AvgGoals": 2.55, "AvgHG": 1.40, "AvgAG": 1.15},
    "Vietnam - National League Women": {"GP": 30, "HomeW%": 0.37, "Draw%": 0.27, "AwayW%": 0.37, "AvgGoals": 2.07, "AvgHG": 1.00, "AvgAG": 1.07},
    "Wales - Cymru Premier": {"GP": 88, "HomeW%": 0.33, "Draw%": 0.25, "AwayW%": 0.42, "AvgGoals": 3.13, "AvgHG": 1.57, "AvgAG": 1.56},
}

# --- League Mapping ("Rosetta Stone") ---
# Maps (country_key, league_code) from leagues_data to the string key in SOCCERSTATS_DATA
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
    Retrieves the hardcoded stats for a given league using the mapping.
    Returns a dictionary of the stats.
    """
    map_key = (country_key, league_code)
    league_name = LEAGUE_STATS_MAP.get(map_key)
    
    if league_name:
        stats = SOCCERSTATS_DATA.get(league_name)
        if stats:
            # Convert percentages to floats
            stats_processed = stats.copy()
            stats_processed['HomeW%'] = safe_float(stats.get('HomeW%'), 0.0)
            stats_processed['Draw%'] = safe_float(stats.get('Draw%'), 0.0)
            stats_processed['AwayW%'] = safe_float(stats.get('AwayW%'), 0.0)
            return stats_processed
    
    # Fallback if no specific league map is found
    # Try to find the primary league for the country
    primary_league_code = leagues_data.get(country_key, {}).get(next(iter(leagues_data.get(country_key, {}))), [None])[0]
    if primary_league_code:
        map_key = (country_key, primary_league_code)
        league_name = LEAGUE_STATS_MAP.get(map_key)
        if league_name and SOCCERSTATS_DATA.get(league_name):
            return SOCCERSTATS_DATA.get(league_name)

    return None

def get_league_suggested_draw_rate(country_key, league_code):
    """
    Analyzes the league table to suggest a realistic draw rate.
    Returns a suggested draw probability based on league data.
    """
    stats = get_league_stats(country_key, league_code)
    if stats and 'Draw%' in stats:
        return safe_float(stats['Draw%'], DEFAULT_DRAW_RATE)
    
    return DEFAULT_DRAW_RATE

def calculate_outcome_probabilities(home_rating, away_rating, base_draw_prob):
    """
    Calculates home, draw, and away probabilities using an Elo-based dynamic draw rate.
    """
    home_advantage = 0
    adjusted_rating_diff = home_rating - away_rating + home_advantage
    
    # Elo-based draw model: Reduce draw prob based on Elo difference
    elo_diff = abs(adjusted_rating_diff)
    draw_probability = base_draw_prob * math.exp(-elo_diff * DRAW_DECAY_FACTOR)
    
    p_home_vs_away = 1 / (1 + 10**(-adjusted_rating_diff / 400))
    
    remaining_prob = 1 - draw_probability
    p_home = p_home_vs_away * remaining_prob
    p_away = (1 - p_home_vs_away) * remaining_prob
    
    # Normalize to ensure sum is 1 (it should be, but good practice)
    total = p_home + draw_probability + p_away
    if total == 0: return 0, 0, 0
    return p_home / total, draw_probability / total, p_away / total

def apply_margin(probabilities, margin_percent):
    """
    Applies a bookmaker's margin to a list of probabilities
    using proportional scaling.
    """
    if not probabilities or sum(probabilities) == 0:
        return [0] * len(probabilities)

    target_overround = 1 + (margin_percent / 100.0)
    
    # Handle potential edge case where probabilities don't sum to 1
    # This shouldn't happen with our logic, but good to normalize
    total_prob = sum(probabilities)
    normalized_probs = [p / total_prob for p in probabilities]

    # Simple proportional scaling
    # We find a scaling factor 'k' such that sum(k * p_i) = target_overround
    # This simplifies to k = target_overround / sum(p_i)
    # Since sum(p_i) is 1, k = target_overround
    
    # No, that's wrong. We need to adjust the probabilities *before* inverting.
    # The odds are 1/p'. The sum of inverse odds is the overround.
    # sum(1/p_i') = target_overround
    # Let p_i' = p_i / k (this is multiplicative scaling, not proportional)
    # sum(k / p_i) = target_overround
    
    # Let's use the standard method:
    # p_i' = p_i * target_overround
    # This scales the sum of probabilities to the target overround.
    
    adjusted_probs = [p * target_overround for p in normalized_probs]
    
    # Re-normalize just in case
    total_adjusted_prob = sum(adjusted_probs)
    if total_adjusted_prob == 0:
        return [0] * len(probabilities)
        
    final_probs = [p / total_adjusted_prob for p in adjusted_probs]
    
    # Calculate odds
    odds = [1 / p if p > 0 else 0 for p in final_probs]
    
    # Let's re-verify the logic.
    # If p = [0.5, 0.3, 0.2] and margin = 5% (target = 1.05)
    # p_adj = [0.5 * 1.05, 0.3 * 1.05, 0.2 * 1.05] = [0.525, 0.315, 0.21]
    # sum(p_adj) = 1.05. This is correct.
    # odds = [1/0.525, 1/0.315, 1/0.21] = [1.905, 3.175, 4.762]
    # sum(1/odds) = 0.525 + 0.315 + 0.21 = 1.05.
    # This is the correct method.
    
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

    # Get the static league-wide suggested draw rate
    league_avg_draw = get_league_suggested_draw_rate(selected_country, selected_league)
    
    # --- Main Tabs ---
    tab1, tab2 = st.tabs(["Single Match Analysis", "Multi-Match Calculator"])

    with tab1:
        with st.expander("📈 League-Wide Stats", expanded=True):
            league_stats = get_league_stats(selected_country, selected_league)
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
        p_home, p_draw, p_away = calculate_outcome_probabilities(home_rating, away_rating, league_avg_draw)
        
        # Apply margin for 1x2 odds
        odds_1x2 = apply_margin([p_home, p_draw, p_away], margin)
        h_odds, d_odds, a_odds = odds_1x2[0], odds_1x2[1], odds_1x2[2]

        # Apply margin for DNB odds
        p_dnb_home = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0
        p_dnb_away = 1 - p_dnb_home
        odds_dnb = apply_margin([p_dnb_home, p_dnb_away], margin)
        dnb_h_odds, dnb_a_odds = odds_dnb[0], odds_dnb[1]


        with st.expander("🎯 Calculated Odds", expanded=True):
            st.markdown(f"**Calculated Fair Probabilities (Dynamic Draw: {p_draw:.1%})**")
            prob_cols = st.columns(3)
            prob_cols[0].metric("Home Win", f"{p_home:.2%}")
            prob_cols[1].metric("Draw", f"{p_draw:.2%}")
            prob_cols[2].metric("Away Win", f"{p_away:.2%}")
            
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
            league_stats = get_league_stats(selected_country, selected_league)
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

            col1, col2, col3, col4, col5 = st.columns([3, 3, 1, 1, 1])
            
            sel_home = col1.selectbox(f"Home Team {i+1}", team_list_with_blank, index=default_home_index, key=key_home, label_visibility="collapsed")
            sel_away = col2.selectbox(f"Away Team {i+1}", team_list_with_blank, index=default_away_index, key=key_away, label_visibility="collapsed")

            # Store selections
            st.session_state['multi_match_selections'][key_home] = sel_home
            st.session_state['multi_match_selections'][key_away] = sel_away

            odds_1, odds_x, odds_2 = "-", "-", "-"
            
            if sel_home != "---" and sel_away != "---" and sel_home != sel_away:
                try:
                    h_rating = home_table[home_table["Team"] == sel_home].iloc[0]['Rating']
                    a_rating = away_table[away_table["Team"] == sel_away].iloc[0]['Rating']
                    
                    p_h, p_d, p_a = calculate_outcome_probabilities(h_rating, a_rating, league_avg_draw)
                    odds = apply_margin([p_h, p_d, p_a], multi_margin)
                    
                    odds_1 = f"{odds[0]:.2f}"
                    odds_x = f"{odds[1]:.2f}"
                    odds_2 = f"{odds[2]:.2f}"
                except (IndexError, TypeError):
                    # One of the teams might not be in the table (e.g., if lists differ)
                    odds_1, odds_x, odds_2 = "Err", "Err", "Err"

            with col3:
                st.markdown(f"""
                <div class="odds-box">
                    <div class="odds-box-title">1</div>
                    <div class="odds-box-value">{odds_1}</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="odds-box">
                    <div class="odds-box-title">X</div>
                    <div class="odds-box-value">{odds_x}</div>
                </div>
                """, unsafe_allow_html=True)
            with col5:
                st.markdown(f"""
                <div class="odds-box">
                    <div class="odds-box-title">2</div>
                    <div class="odds-box-value">{odds_2}</div>
                </div>
                """, unsafe_allow_html=True)


else:
    st.info("Please select a country and league in the sidebar to begin.")
