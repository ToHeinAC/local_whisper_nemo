# local_whisper_nemo

Portables Windows-11-Push-to-Talk-Diktat, vollständig offline.

Halte `Strg+Shift` gedrückt, sprich (am besten in ein Headset), lass los — der
Text wird direkt dort eingetippt, wo dein Cursor steht (Word, Browser, Chat, …).
Die Spracherkennung läuft lokal mit NVIDIAs
[nemotron-3.5-asr-streaming-0.6b](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b)
(40 Sprachen, Deutsch und Englisch inklusive).

> Nichts verlässt deinen Rechner: Das Modell liegt im App-Ordner, und die laufende
> Anwendung stellt keine einzige Netzwerkanfrage.

## Inbetriebnahme

Doppelklick auf `install.bat`. Das Skript legt ein portables `uv` und ein
verwaltetes Python in `tools\` ab, installiert die Abhängigkeiten, lädt das Modell
nach `models\` und erstellt eine Desktop-Verknüpfung.

Du brauchst weder **Admin-Rechte** noch ein **systemweites Python**. Netzwerkzugriff
ist nur für diese einmalige Installation nötig — danach läuft alles offline.

## Verwendung

Starte über die Desktop-Verknüpfung (oder `run.bat`). Die App läuft im Hintergrund
und zeigt nur ein Icon im System-Tray.

- **Halten** von `Strg+Shift` → eine kleine Wellenform-Anzeige erscheint, solange aufgenommen wird.
- **Loslassen** → der Text wird transkribiert und an der Cursorposition eingetippt; die Anzeige verschwindet.
- **Beenden** über das Tray-Icon.

Beim ersten Start dauert es rund 45 Sekunden, bis das Modell im Speicher ist —
erst danach reagiert der Hotkey.

> Wenn du **mehr als ein Tastaturlayout** installiert hast, benutzt Windows
> `Strg+Shift` selbst zum Umschalten zwischen den Layouts. Trage in dem Fall in
> der `.env` einen anderen `HOTKEY` ein (z. B. `ctrl+alt+space`).

Gesprochene Formatierungsbefehle: *new line*, *next line*, *new paragraph*, *tab*.

## Konfiguration

Kopiere `.env.example` nach `.env` und passe an, was du brauchst — Modell, Sprache
(`de-DE`, `en-US`, `auto`), Gerät (`cpu`/`cuda`) und Hotkey. Details in
[docs/configuration.md](docs/configuration.md).

Tipp: Wenn du ausschließlich Deutsch diktierst, setze `ASR_LANGUAGE=de-DE`. Das
spart die Spracherkennung und verhindert, dass das Modell mitten im Satz die
Sprache wechselt.

## Entwicklung

```
uv sync
uv run pytest -m "not slow"    # schnelle Unit-Tests
uv run pytest -m slow          # lädt das echte Modell
uv run python -m src.main      # aus dem Quellcode starten
```

## Dokumentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) — aktueller Implementierungsstand
- [docs/](docs/) — Details auf Komponentenebene

## Lizenz

Apache-2.0. Das ASR-Modell wird von NVIDIA unter OpenMDW-1.1 bereitgestellt.
