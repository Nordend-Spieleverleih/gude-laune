"""Erzeugt aus ausgabe.html zwei Karussell-Bilder (1080×1350, 4:5) für Instagram/Facebook
und die Bildunterschrift mit Hashtags.

  social/ausgabeNN-1.png  – Kopf, Wetter, Wochenende
  social/ausgabeNN-2.png  – Kopf, Unter der Woche, Flohmarkt, Anzeige
  social/ausgabeNN.txt    – Text für den Post (mit Hashtags)

Aufruf (nach build.py, damit ausgabe.html aktuell ist):  python build/social.py
"""
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "ausgabe.json").read_text(encoding="utf-8"))
OUT = ROOT / "social"
B, PAPER = "#1B3B73", "#F5F2EA"
W, H, BAR = 540, 675, 70  # CSS-Pixel, gerendert mit Faktor 2 -> 1080×1350

WD = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MON = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
       "September", "Oktober", "November", "Dezember"]

FOLIE = """(function(teil, unten){
  window.einpassen && window.einpassen();
  var p = document.querySelector('.paper');
  var weg = teil === 1 ? ['.week', '.ad', '.foot'] : ['.weather', '.weekend'];
  weg.forEach(function(s){ document.querySelectorAll(s).forEach(function(x){ x.style.display = 'none'; }); });
  p.style.minHeight = '0';
  document.body.style.cssText = 'margin:0;width:%(W)dpx;height:%(H)dpx;overflow:hidden;background:%(PAPER)s;position:relative';
  var platz = %(H)d - %(BAR)d;
  var r = p.getBoundingClientRect();
  var s = Math.min(%(W)d / r.width, platz / r.height);
  p.style.transformOrigin = 'top left';
  p.style.transform = 'scale(' + s + ')';
  p.style.position = 'absolute';
  p.style.left = ((%(W)d - r.width * s) / 2) + 'px';
  p.style.top = ((platz - r.height * s) / 2) + 'px';
  var bar = document.createElement('div');
  bar.style.cssText = 'position:absolute;left:30px;right:30px;bottom:0;height:%(BAR)dpx;border-top:1.5px solid #161616;' +
    'display:flex;align-items:center;justify-content:center;font:800 16.5px Nunito,system-ui,sans-serif;color:%(B)s';
  bar.textContent = unten;
  document.body.appendChild(bar);
})""" % dict(W=W, H=H, BAR=BAR, PAPER=PAPER, B=B)


def d(s):
    return datetime.date.fromisoformat(s)


def bilder():
    from playwright.sync_api import sync_playwright
    OUT.mkdir(exist_ok=True)
    texte = {1: "Unter der Woche: weiter wischen →",
             2: "Jeden Montag neu · gude-laune.de"}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for teil in (1, 2):
            pg = b.new_page(viewport={"width": 800, "height": 1130}, device_scale_factor=2)
            pg.goto((ROOT / "ausgabe.html").as_uri())
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.set_viewport_size({"width": W, "height": H})
            pg.evaluate(FOLIE + f"({teil}, {json.dumps(texte[teil])})")
            pg.wait_for_timeout(300)
            pfad = OUT / f"ausgabe{D['nr']}-{teil}.png"
            pg.screenshot(path=str(pfad), clip={"x": 0, "y": 0, "width": W, "height": H})
            pg.close()
            print("Social-Bild:", pfad.relative_to(ROOT))
        b.close()


def kurz(ev):
    return f'{ev["titel"]} ({ev["stadtteil"]})'


def hashtags():
    tags = ["#GudeLaune", "#FrankfurtMitKind", "#FrankfurtMitKindern", "#KinderEventsFrankfurt",
            "#FamilieFrankfurt", "#Frankfurt", "#FFM", "#Mainhattan", "#Wochenendtipps"]
    alle = [D["wochenende"]["samstag"], D["wochenende"]["sonntag"]] + \
        D["wochenende"]["samstag"].get("weitere", []) + D["wochenende"]["sonntag"].get("weitere", []) + \
        D["woche"] + D.get("flohmarkt", [])
    text = " ".join((x.get("titel", "") + " " + x.get("text", "") + " " + x.get("motiv", "")).lower() for x in alle)
    themen = [
        (("roboter", "robot", "coding", "technothek", "ki ", "programm"), ["#RobotikFürKinder", "#CodingFürKinder"]),
        (("forsch", "experiment", "mint", "senckenberg", "algen"), ["#MINT", "#ForschenMitKindern"]),
        (("lese", "vorlese", "buch", "bibliothek", "kibi"), ["#Vorlesen", "#Lesefreude"]),
        (("bastel", "werkstatt", "kreativ", "kunst"), ["#BastelnMitKindern"]),
        (("theater", "märchen", "papageno"), ["#Kindertheater"]),
        (("museum",), ["#MuseumMitKindern"]),
        (("flohmarkt",), ["#Flohmarkt"]),
        (("laterne", "martinsf", "sankt martin", "st. martin"), ["#SanktMartin"]),
        (("advent", "nikolaus", "weihnacht"), ["#AdventMitKindern"]),
    ]
    for worte, t in themen:
        if any(w in text for w in worte):
            tags += t
    teile = {x["stadtteil"] for x in alle if x.get("stadtteil")}
    for s in ("Nordend", "Westend", "Bornheim", "Sachsenhausen", "Ostend", "Bockenheim"):
        if s in teile:
            tags.append(f"#Frankfurt{s}")
    tags.append("#Kitagruppe")
    seen, out = set(), []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower()); out.append(t)
    return " ".join(out[:25])


def bildtext():
    von, bis = d(D["von"]), d(D["bis"])
    sa, so = D["wochenende"]["samstag"], D["wochenende"]["sonntag"]
    n_gratis = sum(1 for x in [sa, so] + sa.get("weitere", []) + so.get("weitere", []) + D["woche"] + D.get("flohmarkt", []) if x.get("gratis"))
    zeilen = [
        f"Gude Laune Nr. {D['nr']} ist da! 🗞️ Die Kinder-Tipps für Frankfurt vom {von.day}.{von.month}. bis {bis.day}.{bis.month}.{bis.year}.",
        "",
        f"👉 Samstag: {kurz(sa)}",
        f"👉 Sonntag: {kurz(so)}",
        "",
        "Unter der Woche:",
    ]
    for ev in D["woche"]:
        zeilen.append(f"• {WD[d(ev['datum']).weekday()][:2]}: {kurz(ev)}")
    for f in D.get("flohmarkt", []):
        zeilen.append(f"• {WD[d(f['datum']).weekday()][:2]}: {kurz(f)}")
    zeilen += [
        "",
        f"{n_gratis} Tipps sind gratis. Alle Uhrzeiten, Preise und Links: gude-laune.de (Link in der Bio) – "
        "gern in die Kita- oder Klassengruppe weiterleiten! 💛",
        "",
        "Wischen für die ganze Woche →",
        "",
        hashtags(),
    ]
    t = "\n".join(zeilen)
    pfad = OUT / f"ausgabe{D['nr']}.txt"
    pfad.write_text(t, encoding="utf-8")
    print("Bildtext:", pfad.relative_to(ROOT))
    return t


if __name__ == "__main__":
    bilder()
    print(bildtext())
