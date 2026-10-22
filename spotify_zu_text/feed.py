"""Die gleiche Episode im öffentlichen RSS-Feed des Podcasts finden und die MP3 laden.

Spotify-Audio selbst ist kopiergeschützt. Fast alle Podcasts veröffentlichen
die Folgen aber zusätzlich frei über einen RSS-Feed – den nutzen wir.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

import feedparser
import requests

from .spotify import Episode


@dataclass
class FeedEpisode:
    titel: str
    audio_url: str
    datum: str = ""


def _normal(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def feeds_suchen(show: str) -> list[str]:
    """Sucht RSS-Feed-Adressen zur Show über das kostenlose Apple-Podcast-Verzeichnis."""
    r = requests.get(
        "https://itunes.apple.com/search",
        params={"media": "podcast", "entity": "podcast", "term": show, "limit": 5},
        timeout=20,
    )
    r.raise_for_status()
    treffer = [t for t in r.json().get("results", []) if t.get("feedUrl")]
    # Shows mit (fast) gleichem Namen zuerst
    treffer.sort(key=lambda t: -SequenceMatcher(None, _normal(show), _normal(t.get("collectionName", ""))).ratio())
    return [t["feedUrl"] for t in treffer]


def feed_lesen(feed_url: str) -> list[FeedEpisode]:
    feed = feedparser.parse(feed_url)
    folgen = []
    for e in feed.entries:
        audio = next((l.href for l in e.get("enclosures", []) if "audio" in l.get("type", "audio")), "")
        if not audio:
            continue
        datum = ""
        if e.get("published_parsed"):
            datum = date(*e.published_parsed[:3]).isoformat()
        folgen.append(FeedEpisode(titel=e.get("title", ""), audio_url=audio, datum=datum))
    return folgen


def bester_treffer(episode: Episode, folgen: list[FeedEpisode], minimum: float = 0.6) -> FeedEpisode | None:
    """Wählt die Feed-Folge, deren Titel (und Datum) am besten zur Spotify-Episode passt."""
    ziel = _normal(episode.titel)
    beste, beste_punkte = None, 0.0
    for f in folgen:
        punkte = SequenceMatcher(None, ziel, _normal(f.titel)).ratio()
        if ziel and ziel in _normal(f.titel):
            punkte = max(punkte, 0.9)
        if episode.datum and f.datum:
            tage = abs((date.fromisoformat(episode.datum[:10]) - date.fromisoformat(f.datum)).days)
            punkte += 0.1 if tage <= 2 else -0.1
        if punkte > beste_punkte:
            beste, beste_punkte = f, punkte
    return beste if beste_punkte >= minimum else None


def episode_finden(episode: Episode) -> FeedEpisode:
    if not episode.show:
        raise RuntimeError("Show-Name unbekannt – RSS-Feed kann nicht gesucht werden.")
    for url in feeds_suchen(episode.show):
        treffer = bester_treffer(episode, feed_lesen(url))
        if treffer:
            return treffer
    raise RuntimeError(
        f"Folge «{episode.titel}» in keinem öffentlichen Feed gefunden "
        "(evtl. Spotify-exklusiv). Alternative: Transkript in der Spotify-App kopieren, "
        "als .txt speichern und diese Datei übergeben."
    )


def herunterladen(url: str, ziel: Path) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "spotify-zu-text"}) as r:
        r.raise_for_status()
        with open(ziel, "wb") as f:
            for teil in r.iter_content(1 << 16):
                f.write(teil)
    return ziel
