# Spotify zu Text

Macht aus einer Podcast-Folge (z.B. Finanz-Podcast auf Spotify):

1. **`transkript.md`** – der ganze gesprochene Text mit Zeitmarken
2. **`notizen.md`** – Kurzfassung, wichtigste Erkenntnisse, erwähnte Aktien/ETFs/Zahlen, **Aufgaben-Checkliste**, kritische Punkte und Begriffserklärungen

## So funktioniert es

```
Spotify-Link → Titel & Show nachschlagen → gleiche Folge im öffentlichen RSS-Feed finden
→ MP3 laden → Whisper (Spracherkennung, lokal & gratis) → Claude (KI) schreibt Notizen
```

Spotify-Audio ist kopiergeschützt und darf nicht heruntergeladen werden. Fast alle Podcasts stellen dieselben Folgen aber frei über einen RSS-Feed (Abo-Adresse für Podcast-Apps) bereit – das Tool nimmt die MP3 von dort.

## Einrichten (einmalig)

Voraussetzung: [Python](https://www.python.org/downloads/) 3.10+ und [ffmpeg](https://ffmpeg.org/download.html).

```bash
git clone https://github.com/roniz1360/spotify-zu-text.git
cd spotify-zu-text
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

API-Schlüssel (API = Programmierschnittstelle) für die Notizen von [console.anthropic.com](https://console.anthropic.com) holen und setzen:

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # Windows: set ANTHROPIC_API_KEY=sk-ant-...
```

Optional, zuverlässiger beim Nachschlagen: kostenlose App auf [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) anlegen und `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` setzen.

## Benutzen

In Spotify bei der Folge: **Teilen → Link kopieren**, dann:

```bash
python -m spotify_zu_text "https://open.spotify.com/episode/..."
```

Ergebnis liegt in `notizen/<datum>_<titel>/`.

| Fall | Befehl |
|---|---|
| Nur Text, ohne KI-Notizen (gratis) | `python -m spotify_zu_text "<link>" --nur-transkript` |
| Eigene Audiodatei | `python -m spotify_zu_text folge.mp3` |
| Text schon vorhanden (z.B. aus Spotify-App kopiert) | `python -m spotify_zu_text folge.txt` |
| Genauer (langsamer) | `--modell medium` oder `--modell large-v3` |
| Sprache festlegen | `--sprache de` |

### Folge ist «Spotify-exklusiv»?

Dann gibt es keinen freien Feed. Lösung: In der Spotify-App bei der Folge den Reiter **Transkript** öffnen, Text kopieren, als `folge.txt` speichern und `python -m spotify_zu_text folge.txt` ausführen.

## Kosten & Dauer

- Transkript: gratis, läuft auf deinem PC. Eine Stunde Podcast ≈ 5–20 Min. (je nach PC und Modell).
- Notizen: Claude-API, meist wenige Rappen pro Folge.

## Tests

```bash
pip install pytest && python -m pytest
```

> Die Notizen sind Zusammenfassungen, keine Anlageberatung.
