from unittest import mock

import pytest

from spotify_zu_text import cli, feed, spotify
from spotify_zu_text.feed import FeedEpisode
from spotify_zu_text.spotify import Episode
from spotify_zu_text.transkript import zeit

ID = "4rOoJ6Egrf8K2IrywzwOMk"


@pytest.mark.parametrize("link", [
    f"https://open.spotify.com/episode/{ID}?si=abc",
    f"https://open.spotify.com/intl-de/episode/{ID}",
    f"spotify:episode:{ID}",
])
def test_episode_id(link):
    assert spotify.episode_id(link) == ID


def test_episode_id_falsch():
    with pytest.raises(ValueError):
        spotify.episode_id("https://open.spotify.com/show/xyz")


def test_parse_webseite():
    seite = (
        '<meta property="og:title" content="ETF &amp; Säule 3a erklärt"/>'
        '<meta name="description" content="Listen to this episode from Finanzfluss on Spotify. Heute …"/>'
        '<meta name="music:release_date" content="2026-10-01T00:00:00Z"/>'
    )
    ep = spotify.parse_webseite(ID, seite)
    assert (ep.titel, ep.show, ep.datum) == ("ETF & Säule 3a erklärt", "Finanzfluss", "2026-10-01")


def test_bester_treffer():
    ep = Episode(ID, "#512 ETF & Säule 3a erklärt", "Finanzfluss", "2026-10-01")
    folgen = [
        FeedEpisode("#511 Gold kaufen?", "a.mp3", "2026-09-24"),
        FeedEpisode("#512 ETF & Saeule 3a erklaert", "b.mp3", "2026-10-01"),
    ]
    assert feed.bester_treffer(ep, folgen).audio_url == "b.mp3"
    assert feed.bester_treffer(Episode(ID, "Ganz anderes Thema", "X"), folgen) is None


def test_zeit():
    assert zeit(75) == "01:15"
    assert zeit(3725) == "01:02:05"


def test_cli_mit_textdatei(tmp_path):
    t = tmp_path / "folge.txt"
    t.write_text("[00:01] Hallo", encoding="utf-8")
    with mock.patch.object(cli, "notizen_erstellen", return_value="## Kurzfassung\nTest") as n:
        assert cli.main([str(t), "--ausgabe", str(tmp_path / "out")]) == 0
    n.assert_called_once()
    ergebnis = list((tmp_path / "out").glob("*/notizen.md"))
    assert ergebnis and "Kurzfassung" in ergebnis[0].read_text(encoding="utf-8")
