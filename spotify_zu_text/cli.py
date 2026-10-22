"""Befehlszeile: Spotify-Link (oder Audio-/Textdatei) rein → Transkript + Notizen raus."""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from . import feed, spotify
from .notizen import notizen_erstellen
from .transkript import transkribieren

AUDIO_ENDUNGEN = {".mp3", ".m4a", ".wav", ".ogg", ".aac", ".flac", ".mp4", ".webm"}
TEXT_ENDUNGEN = {".txt", ".md"}


def ordnername(titel: str, datum: str = "") -> str:
    slug = re.sub(r"[^\w]+", "-", titel.lower()).strip("-")[:60] or "folge"
    return f"{datum or date.today().isoformat()}_{slug}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="spotify-zu-text",
        description="Wandelt Podcast-Folgen in Text um und erstellt Zusammenfassung, Notizen und Aufgaben.",
    )
    p.add_argument("quelle", help="Spotify-Episoden-Link, Audiodatei (.mp3 …) oder Transkript (.txt/.md)")
    p.add_argument("--ausgabe", default="notizen", help="Zielordner (Standard: notizen)")
    p.add_argument("--modell", default="small", help="Whisper-Modell: tiny, base, small, medium, large-v3 (Standard: small)")
    p.add_argument("--sprache", default=None, help="Sprache der Folge, z.B. de oder en (Standard: automatisch)")
    p.add_argument("--nur-transkript", action="store_true", help="Nur Text erstellen, keine Notizen (braucht keinen API-Schlüssel)")
    a = p.parse_args(argv)

    quelle = Path(a.quelle)
    titel, show, datum = quelle.stem, "", ""
    try:
        if quelle.suffix.lower() in TEXT_ENDUNGEN and quelle.exists():
            ordner = Path(a.ausgabe) / ordnername(titel)
            transkript = quelle.read_text(encoding="utf-8")
        else:
            if quelle.suffix.lower() in AUDIO_ENDUNGEN and quelle.exists():
                audio = quelle
            else:
                print("1/4  Episode bei Spotify nachschlagen …")
                ep = spotify.episode_infos(a.quelle)
                titel, show, datum = ep.titel, ep.show, ep.datum
                print(f"     «{titel}» – {show}")
                print("2/4  Folge im öffentlichen Podcast-Feed suchen …")
                treffer = feed.episode_finden(ep)
                datum = datum or treffer.datum
                audio = Path(a.ausgabe) / ordnername(titel, datum) / "audio.mp3"
                print("     Herunterladen …")
                feed.herunterladen(treffer.audio_url, audio)
            ordner = Path(a.ausgabe) / ordnername(titel, datum)
            print(f"3/4  In Text umwandeln (Whisper «{a.modell}», kann einige Minuten dauern) …")
            transkript = transkribieren(audio, a.modell, a.sprache)
            ordner.mkdir(parents=True, exist_ok=True)
            kopf = f"# Transkript: {titel}\n\n" + (f"**Podcast:** {show}  \n" if show else "") + (f"**Datum:** {datum}\n\n" if datum else "\n")
            (ordner / "transkript.md").write_text(kopf + transkript + "\n", encoding="utf-8")
            print(f"     Gespeichert: {ordner / 'transkript.md'}")

        if a.nur_transkript:
            return 0
        print("4/4  Zusammenfassung, Notizen und Aufgaben erstellen …")
        notizen = notizen_erstellen(transkript, titel, show)
        ordner.mkdir(parents=True, exist_ok=True)
        ziel = ordner / "notizen.md"
        ziel.write_text(f"# {titel}\n\n" + (f"**Podcast:** {show}  \n" if show else "") + (f"**Datum:** {datum}\n\n" if datum else "\n") + notizen + "\n", encoding="utf-8")
        print(f"Fertig: {ziel}")
        return 0
    except Exception as fehler:  # verständliche Meldung statt langem Fehlertext
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
