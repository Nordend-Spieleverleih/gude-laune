# Gude Laune – Die Wochenzeitung für Frankfurter Familien

Wöchentliche Kinder-Events in Frankfurt als Zeitungsseite (WhatsApp-Bild) und Webseite.
Ein Angebot von [Nordend-Spieleverleih](https://nordend-spieleverleih.de/).

## So funktioniert's
1. `data/ausgabe.json` enthält die Termine der Woche (wird wöchentlich neu geschrieben).
2. Bei jeder Änderung baut GitHub automatisch (`.github/workflows/ausgabe.yml`):
   echtes Wetter von Open-Meteo holen, Bilder laden, `ausgabe.png` und `index.html` erzeugen.
3. Das Wochenbild liegt danach unter https://gude-laune.de/ausgabe.png

- `data/anzeigen.json` – die Anzeigen für den Spieleverleih (wechseln wöchentlich)
- `ads/` – Produktfotos aus dem Shop
- `img/` – Bilder der Wochenend-Tipps (nur freie Lizenzen oder eigene Fotos, mit Quellenangabe)
- `build/build.py` – die Vorlage

## Neu
- `archiv/` – jede Ausgabe wird automatisch dauerhaft gespeichert (Seite, Bild, Daten); Übersicht unter gude-laune.de/archiv/
- `impressum.html`, `datenschutz.html` – Rechtstexte (werden mitgebaut)
- `fonts/` – Schriften werden selbst ausgeliefert (keine Verbindung zu Google Fonts)
- Werbebanner für den Nordend-Spieleverleih auf der Webseite (Funktion `banner()` in `build/build.py`), Link zum WhatsApp-Kanal: `WHATSAPP` in `build/build.py`
- `data/spiele.json` – alle Spiele des Spieleverleihs für das wechselnde Werbebanner (alle 5 Sekunden ein anderes Spiel, nur auf der Webseite). Fotos lädt der Bau nach `ads/spiele/`.
- Teilen-Button mit Menü (WhatsApp, Facebook, Telegram, E-Mail, Link kopieren, am Handy: Wochenbild direkt teilen)
- `data/bilder.json` + `img/bib/` – Bildbibliothek: frei lizenzierte Fotos (Wikimedia Commons) von Orten, die oft vorkommen (Museen, Parks, Palmengarten, Zoo, Oper …), mit Urheber und Lizenz. Für die Wochenend-Haupt-Tipps zuerst hier nachsehen.
- `build/motive.py` – eigene Illustrationen (SVG): Jeder Tipp bekommt automatisch ein kleines Motiv (Laterne, Theater, Dino, Teddy …), passend zu Titel und Text. Optional per `"motiv": "<name>"` im Eintrag festlegen. Hat ein Wochenend-Tipp kein Foto, erscheint eine große Illustration.
- Das Wochenbild ist 800 px breit und mindestens 1130 px hoch; bei viel Text wird es länger (bis 1360 px), damit Anzeige und Fußzeile nie abgeschnitten werden.
