"""Spotify-Link lesen und Episoden-Infos (Titel, Show, Datum) holen."""

import base64
import html
import os
import re
from dataclasses import dataclass

import requests

_EPISODE_RE = re.compile(r"(?:open\.spotify\.com/(?:intl-[a-z]{2}/)?episode/|spotify:episode:)([A-Za-z0-9]{22})")


@dataclass
class Episode:
    id: str
    titel: str
    show: str
    datum: str = ""  # JJJJ-MM-TT, falls bekannt
    beschreibung: str = ""


def episode_id(link: str) -> str:
    """Holt die 22-stellige Episoden-ID aus einem Spotify-Link."""
    m = _EPISODE_RE.search(link)
    if not m:
        raise ValueError(
            "Kein Spotify-Episoden-Link erkannt. Erwartet z.B. "
            "https://open.spotify.com/episode/<ID> (Teilen > Link kopieren)."
        )
    return m.group(1)


def episode_infos(link: str) -> Episode:
    """Episoden-Infos holen: über die Spotify-API (falls Schlüssel gesetzt), sonst über die öffentliche Webseite."""
    eid = episode_id(link)
    if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"):
        return _ueber_api(eid)
    return _ueber_webseite(eid)


def _ueber_api(eid: str) -> Episode:
    creds = f"{os.environ['SPOTIFY_CLIENT_ID']}:{os.environ['SPOTIFY_CLIENT_SECRET']}"
    token = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        headers={"Authorization": "Basic " + base64.b64encode(creds.encode()).decode()},
        timeout=20,
    )
    token.raise_for_status()
    r = requests.get(
        f"https://api.spotify.com/v1/episodes/{eid}",
        params={"market": os.getenv("SPOTIFY_MARKET", "CH")},
        headers={"Authorization": "Bearer " + token.json()["access_token"]},
        timeout=20,
    )
    r.raise_for_status()
    d = r.json()
    return Episode(
        id=eid,
        titel=d["name"],
        show=d["show"]["name"],
        datum=d.get("release_date", ""),
        beschreibung=d.get("description", ""),
    )


def _meta(seite: str, name: str) -> str:
    m = re.search(rf'<meta[^>]+(?:property|name)="{re.escape(name)}"[^>]+content="([^"]*)"', seite)
    return html.unescape(m.group(1)) if m else ""


def parse_webseite(eid: str, seite: str) -> Episode:
    """Liest Titel, Show und Datum aus dem HTML der Spotify-Episodenseite."""
    titel = _meta(seite, "og:title")
    beschreibung = _meta(seite, "description") or _meta(seite, "og:description")
    show = ""
    m = re.search(r"(?:Listen to this episode from|Hör dir diese Folge von) (.+?) (?:on|auf) Spotify", beschreibung)
    if m:
        show = m.group(1)
    datum = _meta(seite, "music:release_date")[:10]
    if not titel:
        raise RuntimeError("Episodentitel nicht gefunden. Tipp: SPOTIFY_CLIENT_ID/SECRET setzen (siehe README).")
    return Episode(id=eid, titel=titel, show=show, datum=datum, beschreibung=beschreibung)


def _ueber_webseite(eid: str) -> Episode:
    r = requests.get(
        f"https://open.spotify.com/episode/{eid}",
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"},
        timeout=20,
    )
    r.raise_for_status()
    return parse_webseite(eid, r.text)
