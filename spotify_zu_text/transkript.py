"""Audio lokal mit Whisper in Text umwandeln (kostenlos, läuft auf dem eigenen PC)."""

from pathlib import Path


def zeit(sekunden: float) -> str:
    s = int(sekunden)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"


def transkribieren(audio: Path, modell: str = "small", sprache: str | None = None) -> str:
    """Gibt das Transkript mit Zeitmarken zurück, z.B. «[12:34] Text …»."""
    from faster_whisper import WhisperModel  # erst hier laden: grosses Paket

    whisper = WhisperModel(modell, device="auto", compute_type="int8")
    segmente, info = whisper.transcribe(str(audio), language=sprache, vad_filter=True)
    zeilen = []
    for seg in segmente:
        zeilen.append(f"[{zeit(seg.start)}] {seg.text.strip()}")
        print(f"\r  Transkribiert bis {zeit(seg.end)} / {zeit(info.duration)}", end="", flush=True)
    print()
    return "\n".join(zeilen)
