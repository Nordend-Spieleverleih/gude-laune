"""Baut die Gude-Laune-Wochenausgabe.

Liest data/ausgabe.json + data/anzeigen.json und erzeugt:
  ausgabe.html  – Zeitungsseite 800 x 1130 (Vorlage für das Bild)
  ausgabe.png   – das WhatsApp-Wochenbild (nur mit --png)
  index.html    – die Webseite gude-laune.de

Optionen:
  --wetter   holt die Tagestemperaturen von Open-Meteo (braucht Internet)
  --bilder   lädt Bilder mit http-Adresse herunter nach img/
  --png      rendert ausgabe.png mit Playwright
"""
import json, sys, datetime, html, re, urllib.request, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data/ausgabe.json").read_text(encoding="utf-8"))
ADS = json.loads((ROOT / "data/anzeigen.json").read_text(encoding="utf-8"))
ARGS = set(sys.argv[1:])

B, A, PAPER = "#1B3B73", "#E25D4A", "#F5F2EA"
WD = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WDS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MON = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
e = lambda s: html.escape(str(s or ""))
d = datetime.date.fromisoformat

# ---------------------------------------------------------------- Wetter
def wetter_holen():
    url = ("https://api.open-meteo.com/v1/forecast?latitude=50.11&longitude=8.68"
           "&daily=temperature_2m_max,weather_code&timezone=Europe%2FBerlin"
           f"&start_date={D['von']}&end_date={D['bis']}")
    with urllib.request.urlopen(url, timeout=20) as r:
        j = json.load(r)
    def sym(c):
        if c in (0, 1): return "sonne"
        if c == 2: return "heiter"
        if c in (3, 45, 48): return "wolke"
        if c in (71, 73, 75, 77, 85, 86): return "schnee"
        return "regen"
    D["wetter"] = [{"datum": t, "temp": round(x), "symbol": sym(c)}
                   for t, x, c in zip(j["daily"]["time"], j["daily"]["temperature_2m_max"], j["daily"]["weather_code"])]
    D["wetter_echt"] = True

# ---------------------------------------------------------------- Bilder
def bilder_laden():
    (ROOT / "img").mkdir(exist_ok=True)
    for tag in ("samstag", "sonntag"):
        ev = D["wochenende"][tag]
        src = ev.get("bild", "")
        if src.startswith("http"):
            name = "img/" + hashlib.sha1(src.encode()).hexdigest()[:12] + ".jpg"
            req = urllib.request.Request(src, headers={"User-Agent": "GudeLauneBot/1.0 (gude-laune.de)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                (ROOT / name).write_bytes(r.read())
            ev["bild"] = name

# ---------------------------------------------------------------- Bausteine
def wicon(kind):
    sun = f'<circle cx="16" cy="13" r="6" fill="{A}"/><g stroke="{A}" stroke-width="2" stroke-linecap="round"><path d="M16 2v3M16 21v3M5 13h3M24 13h3M8 5l2 2M22 19l2 2M24 5l-2 2M10 19l-2 2"/></g>'
    cloud = '<path d="M8 24h16a5 5 0 0 0 0-10 7 7 0 0 0-13 2 4 4 0 0 0-3 8z" fill="#FFFFFF" stroke="#161616" stroke-width="1.5"/>'
    cloud_hi = '<path d="M8 21h16a5 5 0 0 0 0-10 7 7 0 0 0-13 2 4 4 0 0 0-3 8z" fill="#FFFFFF" stroke="#161616" stroke-width="1.5"/>'
    drops = f'<g stroke="{B}" stroke-width="2" stroke-linecap="round"><path d="M11 25l-1 4M17 25l-1 4M23 25l-1 4"/></g>'
    flakes = f'<g fill="{B}"><circle cx="11" cy="27" r="1.6"/><circle cx="17" cy="28" r="1.6"/><circle cx="23" cy="27" r="1.6"/></g>'
    body = {"sonne": sun, "wolke": cloud, "regen": cloud_hi + drops, "schnee": cloud_hi + flakes,
            "heiter": f'<circle cx="12" cy="11" r="6" fill="{A}"/>' + cloud}.get(kind, cloud)
    return f'<svg class="wi" width="30" height="30" viewBox="0 0 32 32" aria-label="{e(kind)}" role="img">{body}</svg>'

def gratis(flag):
    return ' <span class="gratis">GRATIS</span>' if flag else ""

def link(ev, inner):
    return f'<a href="{e(ev["link"])}">{inner}</a>' if ev.get("link") else inner

def wetterleiste():
    out = []
    for w in D["wetter"]:
        dt = d(w["datum"]); we = dt.weekday() >= 5
        out.append(f'<div class="wt{" we" if we else ""}"><div class="wd">{WDS[dt.weekday()]} <span>{dt.day}.{dt.month}.</span></div>'
                   f'<div class="tp">{w["temp"]}°</div>{wicon(w["symbol"])}</div>')
    return "".join(out)

def wochenend_spalte(tag, ev, dt):
    weitere = "".join(f'<div class="more"><div class="mt">{link(x, e(x["titel"]))}</div><div class="mx">{e(x["text"])}</div></div>' for x in ev.get("weitere", []))
    bild = (f'<div class="pic"><img src="{e(ev["bild"])}" alt="{e(ev["titel"])}"></div><div class="credit">{e(ev.get("bildquelle"))}</div>'
            if ev.get("bild") else "")
    return (f'<div class="wcol"><div class="k acc">{tag} · {e(ev["stadtteil"])}</div>{bild}'
            f'<div class="wh">{link(ev, e(ev["titel"]))}{gratis(ev.get("gratis"))}</div>'
            f'<div class="t">{e(ev["text"])}</div>{weitere}</div>')

def woche_eintrag(ev):
    dt = d(ev["datum"])
    return (f'<div class="wk"><div class="k blue">{WD[dt.weekday()]} · {e(ev["stadtteil"])}</div>'
            f'<div class="kh">{link(ev, e(ev["titel"]))}{gratis(ev.get("gratis"))}</div><div class="kx">{e(ev["text"])}</div></div>')

def flohmarkt():
    rows = "".join(f'<div class="fh">{WDS[d(f["datum"]).weekday()]} {d(f["datum"]).day}.{d(f["datum"]).month}. · {link(f, e(f["titel"]))}</div><div class="fx">{e(f["text"])}</div>' for f in D.get("flohmarkt", []))
    return f'<div class="floh"><div class="k acc">Flohmarkt-Ecke</div>{rows}<div class="fx">Weitere Flohmärkte auf gude-laune.de</div></div>' if rows else ""

def anzeige():
    key = D.get("anzeige") or ADS["reihenfolge"][D["nr"] % len(ADS["reihenfolge"])]
    a = ADS["anzeigen"][key]
    return (f'<a class="ad" href="https://nordend-spieleverleih.de/"><div class="adimg" role="img" aria-label="{e(a["alt"])}" style="background-image:url({e(a["bild"])})"></div>'
            f'<div class="adt"><div class="k" style="opacity:.8">Anzeige · Nordend-Spieleverleih</div>'
            f'<div class="adh">{e(a["titel"])}</div><div class="adx">{e(a["text"])}</div>'
            f'<div class="adl">nordend-spieleverleih.de</div></div></a>')

def zeitung():
    von, bis = d(D["von"]), d(D["bis"])
    sa, so = D["wochenende"]["samstag"], D["wochenende"]["sonntag"]
    alle = [sa, so] + sa.get("weitere", []) + so.get("weitere", []) + D["woche"] + D.get("flohmarkt", [])
    n_tipps = 2 + len(sa.get("weitere", [])) + len(so.get("weitere", [])) + len(D["woche"]) + len(D.get("flohmarkt", []))
    n_gratis = sum(1 for x in alle if x.get("gratis"))
    woche = D["woche"]
    half = (len(woche) + 1) // 2
    hinweis_wetter = "" if D.get("wetter_echt") else "Wetter: Beispielwerte · "
    return f'''<div class="paper">
<div class="mast">
<div class="ear"><div class="k blue">Diese Woche</div><div class="ex">{n_tipps} Tipps,<br>davon {n_gratis} gratis</div></div>
<div class="logo-wrap"><div class="logo">Gude Laune</div><div class="claim">Die Wochenzeitung für Frankfurter Familien</div></div>
<div class="ear r"><div class="k blue">Gratis</div><div class="ex">zum Weiterleiten in die Kita-Gruppe</div></div>
</div>
<div class="dateline"><span>Ausgabe Nr. {D["nr"]} / {D["jahr"]}</span><span>{WD[von.weekday()]}, {von.day}. bis {WD[bis.weekday()]}, {bis.day}. {MON[bis.month]} {bis.year}</span><span>Frankfurt am Main</span></div>
<div class="weather">{wetterleiste()}</div>
<div class="weekend">
<div class="wehead"><span class="brush">Das Wochenende</span><span class="k">Samstag, {(bis - datetime.timedelta(days=1)).day}. &amp; Sonntag, {bis.day}. {MON[bis.month]}</span></div>
<div class="wgrid">{wochenend_spalte("Samstag", sa, bis)}{wochenend_spalte("Sonntag", so, bis)}</div>
</div>
<div class="week">
<div class="weekhead"><span class="h">Unter der Woche</span><span class="k grey">Montag bis Freitag</span></div>
<div class="wkgrid"><div>{"".join(woche_eintrag(x) for x in woche[:half])}</div><div>{"".join(woche_eintrag(x) for x in woche[half:])}{flohmarkt()}</div></div>
</div>
{anzeige()}
<div class="foot"><span>Alle Termine: gude-laune.de</span><span>{hinweis_wetter}Angaben ohne Gewähr</span></div>
</div>'''

CSS = f'''
*{{box-sizing:border-box}}
body{{margin:0;font-family:Nunito,system-ui,sans-serif;color:#161616}}
a{{color:inherit;text-decoration:none}}
.paper{{background:{PAPER};padding:30px 40px;display:flex;flex-direction:column}}
.k{{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}}
.blue{{color:{B}}} .acc{{color:{A}}} .grey{{color:#666}}
.mast{{display:grid;grid-template-columns:140px 1fr 140px;align-items:center;gap:14px}}
.ear{{border:1px solid #161616;border-radius:4px;padding:8px 10px}} .ear.r{{text-align:right}}
.ex{{font-size:13px;line-height:1.35;margin-top:4px}}
.logo-wrap{{text-align:center}}
.logo{{font-family:'Caveat Brush',cursive;font-size:78px;line-height:.95;color:{A};transform:rotate(-3deg);display:inline-block;letter-spacing:.5px}}
.claim{{font-family:'Libre Caslon Text',Georgia,serif;font-style:italic;font-size:15px;color:{B}}}
.dateline{{margin-top:12px;border-top:3px solid #161616;border-bottom:1px solid #161616;padding:5px 0;display:flex;justify-content:space-between;font-size:12px;font-weight:700;gap:8px}}
.weather{{margin-top:10px;display:grid;grid-template-columns:repeat(7,1fr);gap:4px;border-bottom:1px solid #161616;padding-bottom:8px}}
.wt{{text-align:center;padding:6px 0;border-radius:4px}} .wt.we{{background:#FBE3DE}}
.wd{{font-size:12px;font-weight:800}} .wd span{{font-weight:400}} .wt.we .wd{{color:{A}}}
.tp{{font-size:17px;font-weight:800;margin:2px 0}} .wi{{display:block;margin:0 auto}}
.weekend{{margin-top:14px;border:2.5px solid {A};border-radius:6px;background:#fff;padding-bottom:14px}}
.wehead{{background:{A};color:#fff;padding:6px 14px;display:flex;justify-content:space-between;align-items:baseline;gap:8px}}
.brush{{font-family:'Caveat Brush',cursive;font-size:30px;line-height:1}}
.wgrid{{display:grid;grid-template-columns:1fr 1fr;padding:12px 14px 0}}
.wcol:first-child{{padding-right:14px}} .wcol+.wcol{{padding-left:14px;border-left:1px solid #D8D2C6}}
.pic{{margin:6px 0 4px;border-radius:4px;overflow:hidden;height:120px}} .pic img{{width:100%;height:120px;object-fit:cover;display:block}}
.credit{{font-size:9.5px;color:#777;margin-bottom:6px}}
.wh{{font-weight:800;font-size:21px;line-height:1.15}}
.t{{font-size:13.5px;line-height:1.45;margin-top:4px}}
.more{{border-top:1px dashed #B9B3A6;margin-top:10px;padding-top:8px}} .mt{{font-weight:800;font-size:16px;line-height:1.2}} .mx{{font-size:13px;line-height:1.4}}
.gratis{{font-size:11px;font-weight:800;color:#fff;background:{B};border-radius:3px;padding:2px 6px;vertical-align:3px;letter-spacing:.04em}}
.week{{margin-top:14px;margin-bottom:10px}}
.weekhead{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid #161616;padding-bottom:4px}} .weekhead .h{{font-weight:800;font-size:19px}}
.wkgrid{{display:grid;grid-template-columns:1fr 1fr;column-gap:22px}}
.wk{{padding:7px 0;border-bottom:1px solid #C9C4B8}} .kh{{font-weight:800;font-size:17px;line-height:1.2;margin:3px 0 2px}} .kx{{font-size:13px;line-height:1.4}}
.floh{{margin-top:9px;background:#EFEAE0;border-radius:4px;padding:9px 11px}} .fh{{font-weight:800;font-size:15px;line-height:1.25;margin:3px 0 2px}} .fx{{font-size:12.5px;line-height:1.4}}
.ad{{flex-shrink:0;margin-top:auto;background:{B};color:#fff;border-radius:4px;display:grid;grid-template-columns:150px 1fr;overflow:hidden}}
.adimg{{background-size:cover;background-position:center;min-height:118px}}
.adt{{padding:12px 16px}} .adh{{font-weight:800;font-size:23px;line-height:1.1;margin:5px 0}} .adx{{font-size:13.5px;line-height:1.4}} .adl{{font-weight:800;font-size:12.5px;margin-top:6px;color:#FFC9BF}}
.foot{{margin-top:8px;display:flex;justify-content:space-between;font-size:11px;color:#555;gap:8px}}
'''
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Caveat+Brush&family=Libre+Caslon+Text:ital@1&family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">'

def seite_bild():
    return f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">{FONTS}<style>{CSS}
body{{width:800px;height:1130px}} .paper{{width:800px;height:1130px}}</style></head><body>{zeitung()}</body></html>'''

def seite_web():
    von, bis = d(D["von"]), d(D["bis"])
    titel = f"Gude Laune – Kinder-Events in Frankfurt, {von.day}.–{bis.day}. {MON[bis.month]} {bis.year}"
    return f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titel)}</title>
<meta name="description" content="Was ist los mit Kindern in Frankfurt? Die Wochenzeitung für Frankfurter Familien: Kinder-Events, Flohmärkte und Wetter – jede Woche neu, nach Stadtteilen.">
<meta property="og:title" content="{e(titel)}"><meta property="og:image" content="https://gude-laune.de/ausgabe.png">
{FONTS}<style>{CSS}
body{{background:#E9E4D8}}
.wrap{{max-width:800px;margin:0 auto;padding:16px 0 40px}}
.paper{{box-shadow:0 2px 18px rgba(0,0,0,.08)}}
.ad{{margin-top:16px}}
.dl{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:18px 12px 0}}
.btn{{background:{B};color:#fff;font-weight:800;padding:11px 18px;border-radius:8px}} .btn.alt{{background:#25A366}}
.legal{{text-align:center;font-size:12px;color:#666;margin-top:22px}} .legal a{{text-decoration:underline}}
.wk a:hover,.wh a:hover,.mt a:hover{{text-decoration:underline}}
@media (max-width:640px){{
 .paper{{padding:18px 14px}} .mast{{grid-template-columns:1fr}} .ear{{display:none}} .logo{{font-size:60px}}
 .dateline{{flex-direction:column;align-items:center;text-align:center}} .weather{{gap:1px}} .wd span{{display:block}}
 .wgrid,.wkgrid{{grid-template-columns:1fr}} .wcol+.wcol{{padding-left:0;border-left:0;border-top:1px solid #D8D2C6;margin-top:12px;padding-top:12px}} .wcol:first-child{{padding-right:0}}
 .ad{{grid-template-columns:110px 1fr}}
}}
</style></head><body><div class="wrap">{zeitung()}
<div class="dl"><a class="btn" href="ausgabe.png" download>Wochenbild herunterladen</a><a class="btn alt" href="#">WhatsApp-Kanal folgen</a></div>
<div class="legal">Ein Angebot von <a href="https://nordend-spieleverleih.de/">Nordend-Spieleverleih</a> · <a href="https://nordend-spieleverleih.de/impressum/">Impressum</a> · <a href="https://nordend-spieleverleih.de/datenschutz/">Datenschutz</a></div>
</div></body></html>'''

if __name__ == "__main__":
    if "--wetter" in ARGS:
        try: wetter_holen()
        except Exception as ex: print("Wetter nicht geladen:", ex)
    if "--bilder" in ARGS: bilder_laden()
    (ROOT / "ausgabe.html").write_text(seite_bild(), encoding="utf-8")
    (ROOT / "index.html").write_text(seite_web(), encoding="utf-8")
    if "--png" in ARGS:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 800, "height": 1130}, device_scale_factor=2)
            pg.goto((ROOT / "ausgabe.html").as_uri())
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(ROOT / "ausgabe.png"))
            b.close()
    print("Ausgabe", D["nr"], "gebaut")
