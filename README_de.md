# local_whisper_nemo

Portables Push-to-Talk-Diktat für Windows 11 und macOS, vollständig offline.

Halte `Strg+Shift` gedrückt, sprich (am besten in ein Headset), lass los — der
Text wird direkt dort eingetippt, wo dein Cursor steht (Word, Browser, Chat, …).
Die Spracherkennung läuft lokal mit NVIDIAs
[nemotron-3.5-asr-streaming-0.6b](https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b)
(40 Sprachen, Deutsch und Englisch inklusive).

> Nichts verlässt deinen Rechner: Das Modell liegt im App-Ordner, und die laufende
> Anwendung stellt keine einzige Netzwerkanfrage.

## Inbetriebnahme

**Windows** — Doppelklick auf `install.bat`.
**macOS** — `./install.sh` im Terminal ausführen.

Beide legen ein portables `uv` und ein verwaltetes Python in `tools/` ab,
installieren die Abhängigkeiten, laden das Modell nach `models/` und erstellen
(unter Windows) eine Desktop-Verknüpfung.

Du brauchst weder **Admin-Rechte** noch ein **systemweites Python**. Netzwerkzugriff
ist nur für diese einmalige Installation nötig — danach läuft alles offline.

## Verwendung

**Windows** — starte über die Desktop-Verknüpfung (oder `run.bat`). Die App läuft
im Hintergrund und zeigt nur ein Icon im System-Tray.
**macOS** — starte `./run.sh` im Terminal. Ein Tray-Icon gibt es dort nicht.

- **Halten** von `Strg+Shift` → eine kleine Wellenform-Anzeige erscheint, solange aufgenommen wird.
- **Loslassen** → der Text wird transkribiert und an der Cursorposition eingetippt; die Anzeige verschwindet.
- **Beenden** über das Tray-Icon (Windows) bzw. mit Strg+C im Terminal (macOS).

Beim ersten Start dauert es rund 45 Sekunden, bis das Modell im Speicher ist —
erst danach reagiert der Hotkey.

> **Berechtigungen unter macOS.** Gib dem Terminal, aus dem du startest, unter
> Systemeinstellungen → Datenschutz & Sicherheit die Rechte *Mikrofon*,
> *Eingabeüberwachung* und *Bedienungshilfen* und starte es danach neu. Ohne die
> letzten beiden reagiert der Hotkey nicht oder es wird nichts getippt — ohne
> jede Fehlermeldung. Details in
> [docs/deployment.md](docs/deployment.md#macos-permissions).

> Wenn du unter Windows **mehr als ein Tastaturlayout** installiert hast, benutzt
> Windows `Strg+Shift` selbst zum Umschalten zwischen den Layouts. Trage in dem
> Fall in der `.env` einen anderen `HOTKEY` ein (z. B. `ctrl+alt+space`).

Gesprochene Formatierungsbefehle, deutsch und englisch:

| du sagst | du bekommst |
|----------|-------------|
| *neue Zeile* / *nächste Zeile* / *new line* / *next line* | Zeilenumbruch |
| *neuer Absatz* / *new paragraph* | Leerzeile zwischen den Blöcken |
| *Tabulator* / *tab* | Tabulatorsprung |

Der Text wird vor dem Tippen außerdem aufgeräumt: Fülllaute (*äh*, *ähm*, *hm*, …)
fallen weg, und ausgeschriebene Zahlen werden zu Ziffern — *dreiundzwanzig* →
`23`, *der dritte* → `der 3.`, *drei Komma fünf* → `3,5`.

> *um* bleibt absichtlich stehen: im Deutschen ist es eine Präposition
> („…, um pünktlich zu sein“), und das lässt sich nicht zuverlässig vom
> englischen Füllwort unterscheiden.

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

Unter macOS nimm `./install.sh` (mindestens aber `scripts/bootstrap_python.sh`)
statt eines nackten `uv sync`: Das bindet das mitgelieferte uv-Python ein. Das
CPython von Homebrew ist ohne `_tkinter` gebaut, damit lässt sich die
Overlay-Anzeige nicht importieren.

## Dokumentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) — aktueller Implementierungsstand
- [docs/](docs/) — Details auf Komponentenebene

## Lizenz

Apache-2.0. Das ASR-Modell wird von NVIDIA unter OpenMDW-1.1 bereitgestellt.
