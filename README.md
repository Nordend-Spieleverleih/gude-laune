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
