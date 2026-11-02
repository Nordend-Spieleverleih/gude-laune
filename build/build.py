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
SPIELE = json.loads((ROOT / "data/spiele.json").read_text(encoding="utf-8"))["spiele"] if (ROOT / "data/spiele.json").exists() else []
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
def spiele_laden():
    """Lädt die Fotos aller Spiele vom Spieleverleih nach ads/spiele/ (verkleinert)."""
    from io import BytesIO
    from PIL import Image
    ziel = ROOT / "ads" / "spiele"; ziel.mkdir(parents=True, exist_ok=True)
    for sp in SPIELE:
        f = ziel / f'{sp["id"]}.jpg'
        if not sp.get("quelle") or f.exists(): continue
        try:
            req = urllib.request.Request(sp["quelle"], headers={"User-Agent": "GudeLauneBot/1.0 (gude-laune.de)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                im = Image.open(BytesIO(r.read())).convert("RGB")
            im.thumbnail((700, 700)); im.save(f, quality=82, optimize=True)
        except Exception as ex:
            print("Spiel-Foto nicht geladen:", sp["id"], ex)

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
    weitere = "".join(f'<div class="more"><div class="mt">{link(x, e(x["titel"]))}{(" <span style='font-weight:600;color:#666;font-size:13px'>· " + e(x["stadtteil"]) + "</span>") if x.get("stadtteil") else ""}</div><div class="mx">{e(x["text"])}</div></div>' for x in ev.get("weitere", []))
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
    ziel = a.get("link", "https://nordend-spieleverleih.de/")
    return (f'<a class="ad" href="{e(ziel)}"><div class="adimg" role="img" aria-label="{e(a["alt"])}" style="background-image:url({e(a["bild"])})"></div>'
            f'<div class="adt"><div class="k" style="opacity:.8">Anzeige · Nordend-Spieleverleih</div>'
            f'<div class="adh">{e(a["titel"])}</div><div class="adx">{e(a["text"])}</div>'
            f'<div class="adl">{e(a.get("linktext", "nordend-spieleverleih.de"))}</div></div></a>')

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
GOOGLE_CSS = "https://fonts.googleapis.com/css2?family=Caveat+Brush&family=Libre+Caslon+Text:ital@1&family=Nunito:wght@400;600;700;800;900&display=swap"

def fonts_laden():
    """Lädt die Schriften einmalig nach fonts/ – danach werden sie von gude-laune.de selbst ausgeliefert (keine Verbindung zu Google)."""
    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
    with urllib.request.urlopen(urllib.request.Request(GOOGLE_CSS, headers=ua), timeout=30) as r:
        css = r.read().decode()
    (ROOT / "fonts").mkdir(exist_ok=True)
    def ersetze(m):
        url = m.group(1)
        name = hashlib.sha1(url.encode()).hexdigest()[:12] + ".woff2"
        ziel = ROOT / "fonts" / name
        if not ziel.exists():
            with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=30) as r:
                ziel.write_bytes(r.read())
        return f"url({name})"
    css = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", ersetze, css)
    (ROOT / "fonts" / "fonts.css").write_text(css, encoding="utf-8")

def fonts_link():
    if (ROOT / "fonts" / "fonts.css").exists():
        return '<link href="fonts/fonts.css" rel="stylesheet">'
    return f'<link href="{GOOGLE_CSS}" rel="stylesheet">'

FONTS = fonts_link()

def seite_bild():
    return f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">{FONTS}<style>{CSS}
body{{width:800px;height:1130px}} .paper{{width:800px;height:1130px}}</style></head><body>{zeitung()}</body></html>'''


WHATSAPP = "https://whatsapp.com/channel/0029VbDjF5W4inos5DFyo101"

def banner():
    """Zwei feste Werbebanner für den Nordend-Spieleverleih (nur auf der Webseite)."""
    keys = [k for k in ADS["reihenfolge"] if k != "schnitzeljagd"]
    a = ADS["anzeigen"][keys[(D["nr"] + 1) % len(keys)]]  # anderes Spiel als in der Zeitungs-Anzeige
    return f"""<div class="banners">
<a class="bn" href="https://nordend-spieleverleih.de/spieleauswahl/"><div class="bi" role="img" aria-label="{e(a["alt"])}" style="background-image:url({e(a["bild"])})"></div>
<div class="bt"><div class="k blue">Nordend-Spieleverleih</div><div class="bh">Spiele für Geburtstag &amp; Gartenfest</div><div class="bx">Cornhole, Mölkky, Kubb &amp; mehr – im Paket ab 75 €, Abholung im Nordend oder Lieferung.</div><span class="bc">Zur Spieleauswahl →</span></div></a>
<a class="bn sj" href="https://nordend-spieleverleih.de/schnitzeljagd/"><div class="bi" role="img" aria-label="Titelseite einer Schnitzeljagd für den Günthersburgpark mit Fuchs" style="background-image:url(ads/schnitzeljagd-cover.jpg)"></div>
<div class="bt"><div class="k acc">Jetzt erhältlich</div><div class="bh">Schnitzeljagd für Frankfurter Parks</div><div class="bx">Günthersburgpark und Wasserpark – als PDF zum Ausdrucken, je 12,90 €.</div><span class="bc">Zum Schnitzeljagd-Shop →</span></div></a>
</div>"""

RECHT_CSS = f"""*{{box-sizing:border-box}} body{{margin:0;background:#E9E4D8;font-family:Nunito,system-ui,sans-serif;color:#161616}}
.r{{max-width:760px;margin:20px auto;background:{PAPER};padding:30px 36px;border-radius:4px;line-height:1.55;font-size:15px}}
.r h1{{font-size:28px;margin:0 0 4px}} .r h2{{font-size:18px;margin:24px 0 6px}} .r a{{color:{B}}}
.r a.logo{{font-family:'Caveat Brush',cursive;font-size:48px;color:{A};text-decoration:none;display:inline-block;transform:rotate(-3deg)}}
@media (max-width:640px){{.r{{margin:0;padding:20px 16px}}}}"""

def rechtsseite(titel, inhalt):
    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel} – Gude Laune</title><meta name="robots" content="noindex">{FONTS}<style>{RECHT_CSS}</style></head>
<body><div class="r"><a class="logo" href="./">Gude Laune</a>{inhalt}
<p style="margin-top:30px"><a href="./">← Zur aktuellen Ausgabe</a></p></div></body></html>"""

IMPRESSUM = """<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2>
<p>Sebastian Widuch<br>Nordend-Spieleverleih<br>Vogelsbergstraße 18<br>60316 Frankfurt am Main</p>
<h2>Kontakt</h2>
<p>Telefon: 069-87201148<br>E-Mail: <a href="mailto:info@nordend-spieleverleih.de">info@nordend-spieleverleih.de</a><br>Website: <a href="https://nordend-spieleverleih.de/">www.nordend-spieleverleih.de</a></p>
<h2>Steuerangaben</h2>
<p>W-IdNr.: DE465238783<br>Umsatzsteuer wird aufgrund der Kleinunternehmerregelung gemäß § 19 UStG nicht ausgewiesen.</p>
<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
<p>Sebastian Widuch, Vogelsbergstraße 18, 60316 Frankfurt am Main</p>
<h2>Hinweis zu den Terminen</h2>
<p>Alle Termine werden sorgfältig recherchiert, trotzdem ohne Gewähr. Maßgeblich sind die Angaben der jeweiligen Veranstalter, auf deren Seiten wir verlinken. Für die Inhalte verlinkter Seiten sind ausschließlich deren Betreiber verantwortlich.</p>
<h2>Bildnachweise</h2>
<p>Fotos zu Veranstaltungen stammen, soweit angegeben, von Wikimedia Commons und stehen unter der jeweils genannten freien Lizenz (Urheber und Lizenz stehen direkt am Bild). Produktfotos: Nordend-Spieleverleih.</p>"""

DATENSCHUTZ = """<h1>Datenschutzerklärung</h1>
<p>Stand: November 2026</p>
<h2>1. Verantwortlicher</h2>
<p>Sebastian Widuch, Nordend-Spieleverleih, Vogelsbergstraße 18, 60316 Frankfurt am Main<br>E-Mail: <a href="mailto:info@nordend-spieleverleih.de">info@nordend-spieleverleih.de</a>, Telefon: 069-87201148</p>
<h2>2. Das Wichtigste in Kürze</h2>
<p>gude-laune.de ist eine reine Informationsseite. Wir setzen keine Cookies, kein Tracking, keine Analyse-Tools und keine Werbenetzwerke ein. Es gibt keine Formulare und keine Benutzerkonten. Schriften und Bilder werden direkt von dieser Seite geladen, nicht von Drittanbietern.</p>
<h2>3. Hosting und Server-Logfiles</h2>
<p>Die Seite wird über GitHub Pages bereitgestellt (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA, ein Unternehmen der Microsoft Corporation). Beim Aufruf der Seite verarbeitet GitHub technisch notwendige Daten wie Ihre IP-Adresse, Datum und Uhrzeit des Abrufs, die aufgerufene Seite und Angaben zum Browser, um die Seite auszuliefern und die Sicherheit des Dienstes zu gewährleisten. Rechtsgrundlage ist unser berechtigtes Interesse an einer sicheren und zuverlässigen Bereitstellung der Seite (Art. 6 Abs. 1 lit. f DSGVO). Dabei kann eine Übermittlung in die USA erfolgen; GitHub ist nach dem EU-US Data Privacy Framework zertifiziert. Weitere Informationen: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement">Datenschutzerklärung von GitHub</a>.</p>
<h2>4. Kontakt per E-Mail oder Telefon</h2>
<p>Wenn Sie uns kontaktieren, verarbeiten wir Ihre Angaben nur, um Ihre Anfrage zu beantworten (Art. 6 Abs. 1 lit. b bzw. f DSGVO), und löschen sie, sobald sie dafür nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<h2>5. WhatsApp-Kanal und externe Links</h2>
<p>Auf dieser Seite verlinken wir auf unseren WhatsApp-Kanal sowie auf Seiten von Veranstaltern und auf nordend-spieleverleih.de. Erst wenn Sie einen solchen Link anklicken, werden Daten an den jeweiligen Anbieter übertragen; dafür gelten dessen Datenschutzbestimmungen. Für den WhatsApp-Kanal ist das die WhatsApp Ireland Limited (Meta). Als Betreiber des Kanals sehen wir die Telefonnummern der Abonnenten nicht.</p>
<h2>6. Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch gegen Verarbeitungen auf Grundlage berechtigter Interessen (Art. 15–21 DSGVO). Wenden Sie sich dazu an die oben genannte Kontaktadresse. Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, zum Beispiel beim Hessischen Beauftragten für Datenschutz und Informationsfreiheit, Gustav-Stresemann-Ring 1, 65189 Wiesbaden.</p>"""


SITE = "https://gude-laune.de/"

def slug(t):
    t = t.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

def alle_termine(ausgabe):
    """Alle Termine einer Ausgabe als flache Liste (mit Art)."""
    out = []
    for tag in ("samstag", "sonntag"):
        h = ausgabe["wochenende"][tag]
        datum = ausgabe["bis"] if tag == "sonntag" else (d(ausgabe["bis"]) - datetime.timedelta(days=1)).isoformat()
        out.append(dict(h, datum=h.get("datum", datum), art="wochenende"))
        for w in h.get("weitere", []):
            out.append(dict(w, datum=w.get("datum", datum), stadtteil=w.get("stadtteil", h.get("stadtteil", "")), art="wochenende"))
    out += [dict(x, art="woche") for x in ausgabe.get("woche", [])]
    out += [dict(x, art="flohmarkt", stadtteil=x.get("stadtteil", "")) for x in ausgabe.get("flohmarkt", [])]
    return out

def jsonld():
    """Strukturierte Daten (schema.org/Event) für Google."""
    items = []
    for t in alle_termine(D):
        ev = {"@type": "Event", "name": t["titel"], "startDate": t["datum"], "description": t.get("text", ""),
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "eventStatus": "https://schema.org/EventScheduled",
              "location": {"@type": "Place", "name": f'{t.get("stadtteil") or "Frankfurt"}, Frankfurt am Main',
                           "address": {"@type": "PostalAddress", "addressLocality": "Frankfurt am Main", "addressRegion": "Hessen", "addressCountry": "DE"}}}
        if t.get("link"): ev["url"] = t["link"]
        if t.get("gratis"): ev["isAccessibleForFree"] = True
        if t.get("bild") and not str(t["bild"]).startswith("http"): ev["image"] = SITE + t["bild"]
        items.append(ev)
    data = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Gude Laune", "url": SITE,
             "description": "Die Wochenzeitung für Frankfurter Familien: Kinder-Events, Flohmärkte und Wetter."}]
    data.append({"@context": "https://schema.org", "@type": "ItemList", "name": f'Kinder-Events in Frankfurt, Ausgabe {D["nr"]}/{D["jahr"]}',
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": ev} for i, ev in enumerate(items)]})
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

THEMEN = {}  # wird in archivieren() gefüllt: datei -> (titel, ...)

def themen_links():
    if not THEMEN: return ""
    links = " ".join(f'<a href="{f}">{e(v[0])}</a>' for f, v in THEMEN.items())
    return f'<div class="themen"><b>Themen:</b> {links}</div>'

def themen_seiten(ausgaben):
    """Dauerhafte Themenseiten, die mit jeder Ausgabe wachsen."""
    heute = datetime.date.today().isoformat()
    alle = []
    seen = set()
    for a in ausgaben:
        for t in alle_termine(a):
            k = (t["datum"], t["titel"])
            if k in seen: continue
            seen.add(k); alle.append(t)
    alle.sort(key=lambda t: t["datum"])
    def liste(ts):
        kommend = [t for t in ts if t["datum"] >= heute]
        vorbei = [t for t in reversed(ts) if t["datum"] < heute][:30]
        def li(t):
            dt_ = d(t["datum"])
            titel = f'<a href="{e(t["link"])}" rel="nofollow">{e(t["titel"])}</a>' if t.get("link") else e(t["titel"])
            return (f'<li><span class="dt">{WD[dt_.weekday()]}, {dt_.day}.{dt_.month}.{dt_.year}</span> · <b>{titel}</b>'
                    f'{" <span class=g>gratis</span>" if t.get("gratis") else ""}<br><span class="st">{e(t.get("stadtteil",""))}</span> – {e(t.get("text",""))}</li>')
        h = '<h2>Demnächst</h2><ul>' + ("".join(li(t) for t in kommend) or "<li>Neue Termine erscheinen jeden Montag.</li>") + "</ul>"
        if vorbei: h += '<h2>Zuletzt bei Gude Laune</h2><ul class="alt">' + "".join(li(t) for t in vorbei) + "</ul>"
        return h
    seiten = {
        "flohmaerkte-frankfurt.html": ("Flohmärkte", "Kinderflohmärkte in Frankfurt – aktuelle Termine",
            "Kinderflohmärkte und Flohmärkte mit Kindersachen in Frankfurt am Main: Termine nach Datum, mit Stadtteil.",
            "Kinderkleidung, Spielzeug, Bücher und Fahrräder aus zweiter Hand: Hier sammeln wir jede Woche die Kinder- und Kindersachen-Flohmärkte in Frankfurt – von Kita-Basaren bis zum großen Flohmarkt am Mainufer.",
            [t for t in alle if t["art"] == "flohmarkt"]),
        "gratis-kinder-events-frankfurt.html": ("Gratis", "Kostenlose Kinder-Events in Frankfurt",
            "Kostenlose Veranstaltungen für Kinder und Familien in Frankfurt am Main – jede Woche neu zusammengestellt.",
            "Gute Ausflüge müssen nichts kosten: Museen mit freiem Eintritt für Kinder, Feste, Bibliotheken und Mitmach-Aktionen in Frankfurt, bei denen der Eintritt frei ist.",
            [t for t in alle if t.get("gratis")]),
    }
    drinnen = [t for t in alle if t.get("drinnen")]
    if drinnen:
        seiten["regentag-mit-kind-frankfurt.html"] = ("Bei Regen", "Mit Kind bei Regen in Frankfurt – Indoor-Tipps",
            "Was tun mit Kindern bei Regenwetter in Frankfurt? Indoor-Veranstaltungen, Museen und Theater für Familien.",
            "Wenn es draußen grau ist: Theater, Museen, Werkstätten und Konzerte für Kinder in Frankfurt, die drinnen stattfinden.", drinnen)
    stadtteile = sorted({t.get("stadtteil") for t in alle if t.get("stadtteil")})
    for st in stadtteile:
        ts = [t for t in alle if t.get("stadtteil") == st]
        if len(ts) < 2: continue
        seiten[f"stadtteil-{slug(st)}.html"] = (st, f"Kinder-Events in {st} – Frankfurt am Main",
            f"Veranstaltungen für Kinder und Familien in Frankfurt-{st}: aktuelle Termine von Gude Laune.",
            f"Was ist los mit Kindern in {st}? Hier stehen alle Tipps aus Frankfurt-{st}, die bei Gude Laune erschienen sind – Theater, Museen, Feste und Flohmärkte.", ts)
    THEMEN.clear()
    for datei, (kurz, titel, desc, intro, ts) in seiten.items():
        THEMEN[datei] = (kurz,)
        (ROOT / datei).write_text(f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titel)} | Gude Laune</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{datei}">{FONTS}
<style>{RECHT_CSS} .r ul{{list-style:none;padding:0}} .r li{{padding:10px 0;border-bottom:1px solid #D8D2C6;font-size:14px}} .r .alt li{{opacity:.75}}
.dt{{color:{A};font-weight:800}} .st{{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:{B}}} .g{{font-size:11px;font-weight:800;color:#fff;background:{B};border-radius:3px;padding:1px 5px}}</style></head>
<body><div class="r"><a class="logo" href="./">Gude Laune</a><h1>{e(titel)}</h1><p>{e(intro)}</p>{liste(ts)}
<p style="margin-top:24px"><a href="./">Zur aktuellen Wochenausgabe</a> · <a href="archiv/">Archiv</a></p>
<p style="font-size:12px;color:#666">Alle Angaben ohne Gewähr. Maßgeblich sind die Seiten der Veranstalter. · <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></p></div></body></html>""", encoding="utf-8")

def sitemap(archiv_keys):
    heute = datetime.date.today().isoformat()
    urls = [(SITE, "weekly", "1.0"), (SITE + "archiv/", "weekly", "0.6")]
    urls += [(SITE + f, "weekly", "0.8") for f in THEMEN]
    urls += [(SITE + f"archiv/{k}.html", "yearly", "0.4") for k in archiv_keys]
    body = "".join(f"<url><loc>{u}</loc><lastmod>{heute}</lastmod><changefreq>{c}</changefreq><priority>{p}</priority></url>" for u, c, p in urls)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /ausgabe.html\nDisallow: /data/\nDisallow: /build/\n\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")

def archivieren(png_vorhanden):
    """Speichert die aktuelle Ausgabe dauerhaft unter archiv/ und baut die Archiv-Übersicht."""
    global D
    arch = ROOT / "archiv"; arch.mkdir(exist_ok=True)
    key = f'{D["jahr"]}-{D["nr"]:02d}'
    (arch / f"{key}.json").write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
    if png_vorhanden and (ROOT / "ausgabe.png").exists():
        (arch / f"{key}.png").write_bytes((ROOT / "ausgabe.png").read_bytes())
    aktuell = D
    ausgaben = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(arch.glob("*.json"))]
    themen_seiten(ausgaben)
    eintraege = []
    keys = []
    for f in sorted(arch.glob("*.json"), reverse=True):
        D = json.loads(f.read_text(encoding="utf-8"))
        k = f.stem
        png = f"archiv/{k}.png" if (arch / f"{k}.png").exists() else "ausgabe.png"
        keys.append(k)
        (arch / f"{k}.html").write_text(seite_web(base="../", png=png, canonical=f"{SITE}archiv/{k}.html"), encoding="utf-8")
        von, bis = d(D["von"]), d(D["bis"])
        sa = D["wochenende"]["samstag"]["titel"]; so = D["wochenende"]["sonntag"]["titel"]
        eintraege.append(f'<li><a href="{k}.html"><b>Ausgabe {D["nr"]} / {D["jahr"]}</b> · {von.day}.{von.month}. – {bis.day}.{bis.month}.{bis.year}</a><br><span>Wochenende: {e(sa)} · {e(so)}</span></li>')
    D = aktuell
    (ROOT / "index.html").write_text(seite_web(), encoding="utf-8")  # neu, damit die Themen-Links drin sind
    sitemap(keys)
    liste = "".join(eintraege)
    (arch / "index.html").write_text(f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<base href="../"><title>Archiv – Gude Laune</title><link rel="canonical" href="https://gude-laune.de/archiv/"><meta name="description" content="Alle bisherigen Ausgaben von Gude Laune, der Wochenzeitung für Frankfurter Familien.">{FONTS}
<style>{RECHT_CSS} .r ul{{list-style:none;padding:0}} .r li{{padding:10px 0;border-bottom:1px solid #D8D2C6}} .r li span{{font-size:13px;color:#555}} .r li a{{text-decoration:none}}</style></head>
<body><div class="r"><a class="logo" href="./">Gude Laune</a><h1>Archiv</h1><p>Alle bisherigen Ausgaben der Wochenzeitung für Frankfurter Familien.</p><ul>{liste}</ul>
<p><a href="./">← Zur aktuellen Ausgabe</a> · <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></p></div></body></html>""", encoding="utf-8")

def teilen_menue(url, png):
    text = urllib.parse.quote(f"Gude Laune – die Kinder-Events der Woche in Frankfurt: {url}")
    u = urllib.parse.quote(url, safe="")
    return f"""<div class="sharebox"><button class="btn share" type="button" aria-haspopup="true" aria-expanded="false" id="teilen">Teilen</button>
<div class="sharemenu" id="teilenmenue" role="menu">
<button type="button" role="menuitem" id="bildteilen" hidden>Wochenbild teilen (Handy) …</button>
<a role="menuitem" href="https://wa.me/?text={text}" target="_blank" rel="noopener">In einem WhatsApp-Chat teilen</a>
<a role="menuitem" href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Auf Facebook teilen</a>
<a role="menuitem" href="https://t.me/share/url?url={u}&amp;text={urllib.parse.quote('Gude Laune – Kinder-Events in Frankfurt')}" target="_blank" rel="noopener">Bei Telegram teilen</a>
<a role="menuitem" href="mailto:?subject={urllib.parse.quote('Kinder-Events in Frankfurt diese Woche')}&amp;body={text}">Per E-Mail teilen</a>
<button type="button" role="menuitem" id="linkkopieren">Link kopieren</button>
<small>Für Instagram: „Wochenbild herunterladen“ und als Story posten – oder am Handy „Wochenbild teilen“.</small>
</div></div>"""

def rotation_js(png):
    """Wechselndes Werbebanner (alle 5 Sekunden ein anderes Spiel) + Teilen-Menü."""
    spiele = [dict(id=sp["id"], name=sp["name"], text=sp["text"], alt=sp["alt"], bild=f'ads/spiele/{sp["id"]}.jpg')
              for sp in SPIELE if (ROOT / "ads" / "spiele" / f'{sp["id"]}.jpg').exists()]
    return f"""<script>
(function(){{
var SP={json.dumps(spiele, ensure_ascii=False)};
var ad=document.querySelector('.ad');
if(ad&&SP.length>1){{
 for(var i=SP.length-1;i>0;i--){{var j=Math.floor(Math.random()*(i+1));var t=SP[i];SP[i]=SP[j];SP[j]=t;}}
 SP.forEach(function(s){{var im=new Image();im.src=s.bild;}});
 var n=0,pause=false;ad.addEventListener('mouseenter',function(){{pause=true}});ad.addEventListener('mouseleave',function(){{pause=false}});
 ad.href='https://nordend-spieleverleih.de/spieleauswahl/';
 setInterval(function(){{
  if(pause||document.hidden)return;var s=SP[n++%SP.length];ad.classList.add('wechsel');
  setTimeout(function(){{var b=ad.querySelector('.adimg');b.style.backgroundImage='url('+s.bild+')';b.setAttribute('aria-label',s.alt);
   ad.querySelector('.adh').textContent=s.name;ad.querySelector('.adx').textContent=s.text+' Im Paket mit weiteren Spielen ab 75 €.';ad.classList.remove('wechsel');}},350);
 }},5000);
}}
var btn=document.getElementById('teilen'),m=document.getElementById('teilenmenue');
if(btn){{
 btn.addEventListener('click',function(ev){{ev.stopPropagation();var o=m.classList.toggle('offen');btn.setAttribute('aria-expanded',o);}});
 document.addEventListener('click',function(){{m.classList.remove('offen');btn.setAttribute('aria-expanded','false');}});
 var url=document.querySelector('link[rel=canonical]').href;
 document.getElementById('linkkopieren').addEventListener('click',function(ev){{ev.stopPropagation();
  (navigator.clipboard?navigator.clipboard.writeText(url):Promise.reject()).then(function(){{ev.target.textContent='Link kopiert ✓';}},function(){{window.prompt('Link kopieren:',url);}});}});
 var bt=document.getElementById('bildteilen');
 if(navigator.share){{bt.hidden=false;bt.addEventListener('click',function(ev){{ev.stopPropagation();
  fetch('{png}').then(function(r){{return r.blob()}}).then(function(bl){{var f=new File([bl],'gude-laune-wochenausgabe.png',{{type:'image/png'}});
   var d={{title:'Gude Laune',text:'Die Kinder-Events der Woche in Frankfurt: '+url}};
   if(navigator.canShare&&navigator.canShare({{files:[f]}}))d.files=[f];else d.url=url;return navigator.share(d);}}).catch(function(){{}});}});}}
}}
}})();
</script>"""

def seite_web(base='', png='ausgabe.png', canonical=SITE):
    von, bis = d(D["von"]), d(D["bis"])
    titel = f"Gude Laune – Kinder-Events in Frankfurt, {von.day}.–{bis.day}. {MON[bis.month]} {bis.year}"
    return f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
{f'<base href="{base}">' if base else ""}<title>{e(titel)}</title>
<meta name="description" content="Was ist los mit Kindern in Frankfurt? Die Wochenzeitung für Frankfurter Familien: Kinder-Events, Flohmärkte und Wetter – jede Woche neu, nach Stadtteilen.">
<link rel="canonical" href="{canonical}"><meta property="og:title" content="{e(titel)}"><meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}{png}">
<script type="application/ld+json">{jsonld()}</script>
{FONTS}<style>{CSS}
body{{background:#E9E4D8}}
.wrap{{max-width:800px;margin:0 auto;padding:16px 0 40px}}
.paper{{box-shadow:0 2px 18px rgba(0,0,0,.08)}}
.ad{{margin-top:16px}}
.dl{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:18px 12px 0}}
.btn{{background:{B};color:#fff;font-weight:800;padding:11px 18px;border-radius:8px;border:0;font:inherit;font-weight:800;font-size:16px;cursor:pointer}} .btn.alt{{background:#25A366}} .btn.share{{background:{A}}}
.sharebox{{position:relative;display:inline-block}}
.sharemenu{{display:none;position:absolute;left:50%;transform:translateX(-50%);bottom:calc(100% + 8px);background:#fff;border:1px solid #D8D2C6;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.15);padding:6px;min-width:230px;z-index:10;text-align:left}}
.sharemenu.offen{{display:block}} .sharemenu [hidden]{{display:none}}
.sharemenu a,.sharemenu button{{display:block;width:100%;text-align:left;padding:10px 12px;border-radius:6px;font:inherit;font-weight:700;font-size:15px;color:#161616;background:none;border:0;cursor:pointer}}
.sharemenu a:hover,.sharemenu button:hover{{background:#F5F2EA}}
.sharemenu small{{display:block;padding:6px 12px 4px;color:#777;font-size:11.5px;line-height:1.35}}
.ad{{transition:opacity .35s}} .ad.wechsel{{opacity:.15}}
.legal{{text-align:center;font-size:12px;color:#666;margin-top:22px}} .legal a{{text-decoration:underline}}
.strip{{display:block;background:{B};color:#fff;text-align:center;font-weight:700;font-size:14px;padding:9px 12px;border-radius:6px;margin:0 0 12px}}
.strip b{{color:#FFC9BF}}
.banners{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:18px 0 0}}
.bn{{display:grid;grid-template-columns:120px 1fr;background:#fff;border:2px solid {B};border-radius:8px;overflow:hidden;min-height:130px}}
.bn .bi{{background-size:cover;background-position:center}}
.bn .bt{{padding:12px 14px}} .bn .bh{{font-weight:900;font-size:19px;line-height:1.15;margin:4px 0}} .bn .bx{{font-size:13px;line-height:1.4}}
.bn .bc{{display:inline-block;margin-top:8px;font-weight:800;font-size:13px;color:{A}}}
.bn.sj{{border-color:{A}}} .bn.sj .bi{{background-color:#FBF3E4;background-size:cover;background-position:center top}}
.themen{{text-align:center;font-size:13px;margin-top:10px;color:#444;line-height:1.8;padding:0 10px}} .themen a{{color:{B};text-decoration:underline;margin:0 4px}}
.archivlink{{text-align:center;margin-top:16px;font-weight:800}} .archivlink a{{color:{B};text-decoration:underline}}
.wk a:hover,.wh a:hover,.mt a:hover{{text-decoration:underline}}
@media (max-width:640px){{
 .paper{{padding:18px 14px}} .mast{{grid-template-columns:1fr}} .ear{{display:none}} .logo{{font-size:60px}}
 .dateline{{flex-direction:column;align-items:center;text-align:center}} .weather{{gap:1px}} .wd span{{display:block}}
 .wgrid,.wkgrid{{grid-template-columns:1fr}} .wcol+.wcol{{padding-left:0;border-left:0;border-top:1px solid #D8D2C6;margin-top:12px;padding-top:12px}} .wcol:first-child{{padding-right:0}}
 .ad{{grid-template-columns:110px 1fr}} .banners{{grid-template-columns:1fr}} .sharemenu{{left:auto;right:0;transform:none}} .wrap{{padding:10px 8px 30px}}
}}
</style></head><body><div class="wrap">
<a class="strip" href="https://nordend-spieleverleih.de/">Kindergeburtstag oder Sommerfest geplant? <b>Outdoor-Spiele ausleihen beim Nordend-Spieleverleih →</b></a>
{zeitung()}
<div class="dl"><a class="btn" href="{png}" download>Wochenbild herunterladen</a><a class="btn alt" href="{WHATSAPP}">WhatsApp-Kanal folgen</a>{teilen_menue(canonical, png)}</div>
{banner()}
<div class="archivlink"><a href="archiv/">Alle bisherigen Ausgaben im Archiv →</a></div>
{themen_links()}
<div class="legal">Ein Angebot von <a href="https://nordend-spieleverleih.de/">Nordend-Spieleverleih</a> · <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></div>
</div>{rotation_js(png)}</body></html>'''

if __name__ == "__main__":
    if "--wetter" in ARGS:
        try: wetter_holen()
        except Exception as ex: print("Wetter nicht geladen:", ex)
    if "--fonts" in ARGS:
        try: fonts_laden(); FONTS = fonts_link()
        except Exception as ex: print("Schriften nicht geladen:", ex)
    if "--bilder" in ARGS:
        bilder_laden()
        spiele_laden()
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
    (ROOT / "impressum.html").write_text(rechtsseite("Impressum", IMPRESSUM), encoding="utf-8")
    (ROOT / "datenschutz.html").write_text(rechtsseite("Datenschutz", DATENSCHUTZ), encoding="utf-8")
    archivieren("--png" in ARGS)
    print("Ausgabe", D["nr"], "gebaut")
