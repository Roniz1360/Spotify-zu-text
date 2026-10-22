"""Aus dem Transkript mit Claude Zusammenfassung, Notizen und Aufgaben erstellen."""

import anthropic

MODELL = "claude-opus-5-5"

SYSTEM = """Du bist ein Assistent, der Finanz-Podcasts für eine Privatperson in der Schweiz \
aufbereitet. Schreibe auf Deutsch (Schweizer Schreibweise, «ss» statt «ß»), einfach und \
verständlich, auch für Anfänger. Erfinde nichts: Nutze nur, was im Transkript steht. \
Fachbegriffe erklärst du kurz in Klammern. Gib bei wichtigen Aussagen die Zeitmarke [mm:ss] an.

Antworte exakt in diesem Markdown-Format:

## Kurzfassung
3–5 Sätze: Worum geht es, was ist die Kernaussage?

## Wichtigste Erkenntnisse
Nummerierte Liste (max. 10), je 1–2 Sätze mit Zeitmarke.

## Erwähnte Anlagen, Zahlen & Fakten
Tabelle: | Name / Thema | Was wurde gesagt | Zeitmarke |
(Aktien, ETFs, Fonds, Zinsen, Kurse, Steuern, Säule 3a usw. Leer lassen, wenn nichts erwähnt.)

## Meine Aufgaben
Checkliste «- [ ] …» mit konkreten, umsetzbaren Schritten für mich (z.B. «Gebühren meines \
ETF prüfen», «Begriff X nachlesen»). Keine Kauf-/Verkaufsbefehle, sondern Prüf- und Lernschritte.

## Offene Fragen / kritisch prüfen
Aussagen, die einseitig, werblich oder nicht belegt sind, und was ich nachprüfen sollte.

## Begriffe einfach erklärt
Kurze Liste der Fachbegriffe aus der Folge.

> Hinweis: Zusammenfassung eines Podcasts, keine Anlageberatung."""


def notizen_erstellen(transkript: str, titel: str = "", show: str = "") -> str:
    client = anthropic.Anthropic()
    kopf = f"Podcast: {show}\nFolge: {titel}\n\n" if titel or show else ""
    with client.beta.messages.stream(
        model=MODELL,
        max_tokens=16000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": f"{kopf}<transkript>\n{transkript}\n</transkript>"}],
    ) as stream:
        antwort = stream.get_final_message()
    if antwort.stop_reason == "refusal":
        raise RuntimeError("Claude hat die Anfrage abgelehnt.")
    text = "".join(b.text for b in antwort.content if b.type == "text").strip()
    if antwort.stop_reason == "max_tokens":
        text += "\n\n_(Ausgabe wurde abgeschnitten.)_"
    return text
