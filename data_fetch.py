import logging
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import ProxyError

BASE_URL = "https://www.soccer-rating.com/"
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

logger = logging.getLogger(__name__)

_retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])


def _build_session(*, trust_env: bool) -> requests.Session:
    session = requests.Session()
    session.trust_env = trust_env
    session.mount("https://", HTTPAdapter(max_retries=_retries))
    session.mount("http://", HTTPAdapter(max_retries=_retries))
    return session


_session = _build_session(trust_env=True)
_session_no_proxy = _build_session(trust_env=False)


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
    try:
        response = _session.get(url, headers=headers, timeout=timeout)
    except ProxyError:
        logger.warning("Proxy request failed, retrying without environment proxies.")
        response = _session_no_proxy.get(url, headers=headers, timeout=timeout)
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
