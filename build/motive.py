"""Eigene Illustrationen (SVG) im Gude-Laune-Stil.

Jeder Tipp bekommt automatisch ein kleines Motiv, passend zu Titel und Text.
Optional kann ein Eintrag in data/ausgabe.json das Motiv mit "motiv": "<name>" festlegen.
Alle Motive sind selbst gezeichnet – keine fremden Bildrechte.
"""
import re

R, BL, Y, G, P, K, BR = "#E25D4A", "#1B3B73", "#F2B33D", "#4E9A6B", "#F5F2EA", "#161616", "#A8693F"
S = f'stroke="{K}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"'

MOTIVE = {
    "laterne": f'''<path d="M12 8H52" stroke="{BR}" stroke-width="3" stroke-linecap="round"/><path d="M32 8v6" stroke="{K}" stroke-width="2"/>
<ellipse cx="32" cy="34" rx="16" ry="17" fill="{Y}" {S}/><circle cx="32" cy="34" r="7" fill="#FFF3C4"/>
<path d="M25 19q-5 15 0 30M39 19q5 15 0 30" fill="none" stroke="{R}" stroke-width="2"/>
<rect x="23" y="14" width="18" height="6" rx="2" fill="{R}" {S}/><rect x="23" y="48" width="18" height="6" rx="2" fill="{R}" {S}/>''',
    "theater": f'''<rect x="6" y="10" width="52" height="46" rx="3" fill="{BL}" {S}/><circle cx="32" cy="38" r="5" fill="{Y}"/>
<path d="M6 10h21q-8 22 0 46H6z" fill="{R}" {S}/><path d="M58 10H37q8 22 0 46h21z" fill="{R}" {S}/>
<path d="M6 10h52v7q-6.5 5-13 0-6.5 5-13 0-6.5 5-13 0-6.5 5-13 0z" fill="{R}" {S}/>''',
    "musik": f'''<path d="M22 46V16l26-6v30" fill="none" stroke="{BL}" stroke-width="4"/><path d="M22 16l26-6v8l-26 6z" fill="{BL}"/>
<ellipse cx="17" cy="47" rx="7" ry="5.5" fill="{R}" {S}/><ellipse cx="43" cy="41" rx="7" ry="5.5" fill="{R}" {S}/>''',
    "dino": f'''<path d="M15 41q-9 1-11 10" fill="none" stroke="{G}" stroke-width="6" stroke-linecap="round"/>
<path d="M41 36q6-12 8-22" fill="none" stroke="{G}" stroke-width="8" stroke-linecap="round"/>
<rect x="19" y="44" width="6" height="12" rx="2" fill="{G}" {S}/><rect x="35" y="44" width="6" height="12" rx="2" fill="{G}" {S}/>
<ellipse cx="30" cy="40" rx="17" ry="11" fill="{G}" {S}/><ellipse cx="51" cy="12" rx="7" ry="5" fill="{G}" {S}/>
<circle cx="53" cy="10.5" r="1.3" fill="{K}"/><circle cx="25" cy="36" r="2.5" fill="{Y}"/><circle cx="33" cy="34" r="2" fill="{Y}"/><circle cx="31" cy="42" r="2.5" fill="{Y}"/>''',
    "museum": f'''<path d="M7 22L32 8l25 14z" fill="{R}" {S}/><rect x="9" y="22" width="46" height="4" fill="{BL}" {S}/>
<g fill="{P}" {S}><rect x="12" y="27" width="6" height="22"/><rect x="23" y="27" width="6" height="22"/><rect x="35" y="27" width="6" height="22"/><rect x="46" y="27" width="6" height="22"/></g>
<rect x="7" y="49" width="50" height="7" fill="{BL}" {S}/>''',
    "teddy": f'''<circle cx="21" cy="15" r="6" fill="{BR}" {S}/><circle cx="43" cy="15" r="6" fill="{BR}" {S}/>
<ellipse cx="32" cy="47" rx="14" ry="12" fill="{BR}" {S}/><ellipse cx="32" cy="49" rx="7" ry="6" fill="#E3B98F"/>
<circle cx="32" cy="25" r="12" fill="{BR}" {S}/><ellipse cx="32" cy="29" rx="5.5" ry="4" fill="#E3B98F"/>
<circle cx="27.5" cy="22" r="1.5" fill="{K}"/><circle cx="36.5" cy="22" r="1.5" fill="{K}"/><circle cx="32" cy="27.5" r="1.6" fill="{K}"/>
<path d="M46 38l9-3 3 8-9 3z" fill="{R}" {S}/><circle cx="49" cy="39" r="1" fill="{P}"/>''',
    "tier": f'''<ellipse cx="32" cy="38" rx="15" ry="19" fill="{BL}" {S}/><ellipse cx="32" cy="42" rx="9" ry="13" fill="#FFFFFF"/>
<circle cx="27" cy="27" r="2" fill="{K}"/><circle cx="37" cy="27" r="2" fill="{K}"/><path d="M28 31l4 5 4-5z" fill="{Y}" {S}/>
<path d="M22 57h8M34 57h8" stroke="{Y}" stroke-width="4" stroke-linecap="round"/><path d="M17 36q-6 6-4 12M47 36q6 6 4 12" fill="none" stroke="{BL}" stroke-width="5" stroke-linecap="round"/>''',
    "palme": f'''<circle cx="50" cy="13" r="6" fill="{Y}"/><path d="M33 58q2-18-2-36" fill="none" stroke="{BR}" stroke-width="5" stroke-linecap="round"/>
<g fill="{G}" {S}><path d="M31 22q-12-10-24-4 12 0 24 4z"/><path d="M31 22q10-12 24-8-13 1-24 8z"/><path d="M31 22q-14 2-18 14 7-9 18-14z"/><path d="M31 22q13 1 17 13-7-9-17-13z"/></g>
<path d="M14 58h36" stroke="{G}" stroke-width="3" stroke-linecap="round"/>''',
    "baum": f'''<rect x="29" y="38" width="6" height="18" fill="{BR}" {S}/><circle cx="22" cy="30" r="11" fill="{G}" {S}/><circle cx="42" cy="30" r="11" fill="{G}" {S}/>
<circle cx="32" cy="20" r="13" fill="{G}" {S}/><circle cx="26" cy="23" r="2.2" fill="{R}"/><circle cx="39" cy="18" r="2.2" fill="{R}"/><circle cx="41" cy="33" r="2.2" fill="{R}"/>
<path d="M12 57h40" stroke="{G}" stroke-width="3" stroke-linecap="round"/>''',
    "buch": f'''<path d="M6 18q13-6 26 2v34q-13-8-26-2z" fill="#FFFFFF" {S}/><path d="M58 18q-13-6-26 2v34q13-8 26-2z" fill="#FFFFFF" {S}/>
<path d="M4 52q14-6 28 4 14-10 28-4v4q-14-6-28 4-14-10-28-4z" fill="{R}" {S}/>
<path d="M11 26q8-3 15 1M11 33q8-3 15 1M11 40q8-3 15 1M38 27q7-4 15-1M38 34q7-4 15-1M38 41q7-4 15-1" fill="none" stroke="{BL}" stroke-width="1.6"/>''',
    "basteln": f'''<path d="M32 8C16 8 6 19 6 31s9 22 20 22c5 0 6-4 4-7s-1-7 4-7h8c9 0 16-5 16-13C58 16 46 8 32 8z" fill="#EAD2A6" {S}/>
<circle cx="20" cy="22" r="4" fill="{R}"/><circle cx="32" cy="17" r="4" fill="{Y}"/><circle cx="44" cy="21" r="4" fill="{BL}"/><circle cx="17" cy="35" r="4" fill="{G}"/>
<path d="M40 58l14-22" stroke="{BR}" stroke-width="4" stroke-linecap="round"/><path d="M54 36l3-6-6 3z" fill="{R}" {S}/>''',
    "forschen": f'''<path d="M25 8h14M27 8v16L12 50q-2 6 4 6h32q6 0 4-6L37 24V8" fill="#FFFFFF" {S}/>
<path d="M17 42h30l5 9q1 4-3 4H15q-4 0-3-4z" fill="{G}"/><circle cx="27" cy="34" r="2.5" fill="{G}"/><circle cx="35" cy="28" r="2" fill="{G}"/><circle cx="33" cy="47" r="2" fill="#FFFFFF"/>
<path d="M27 8v16L12 50q-2 6 4 6h32q6 0 4-6L37 24V8" fill="none" {S}/>''',
    "eis": f'''<path d="M14 10h18v22l14 6q6 3 6 9v3H14z" fill="{BL}" {S}/><path d="M20 16h8M20 22h8" stroke="#FFFFFF" stroke-width="2"/>
<path d="M10 56h44q4 0 5-4" fill="none" stroke="{K}" stroke-width="3" stroke-linecap="round"/><path d="M20 50v6M44 50v6" stroke="{K}" stroke-width="2.5"/>''',
    "weihnacht": f'''<path d="M32 8L16 30h7L12 46h40L41 30h7z" fill="{G}" {S}/><rect x="28" y="46" width="8" height="9" fill="{BR}" {S}/>
<path d="M32 3l2 4 4 .5-3 3 1 4-4-2-4 2 1-4-3-3 4-.5z" fill="{Y}" {S}/>
<circle cx="26" cy="27" r="2.4" fill="{R}"/><circle cx="38" cy="36" r="2.4" fill="{R}"/><circle cx="24" cy="41" r="2.4" fill="{Y}"/><circle cx="36" cy="20" r="2" fill="{Y}"/>''',
    "fasching": f'''<path d="M6 24q26-10 52 0-2 18-14 18-8 0-12-7-4 7-12 7-12 0-14-18z" fill="{R}" {S}/>
<ellipse cx="21" cy="29" rx="5" ry="3.5" fill="{P}" {S}/><ellipse cx="43" cy="29" rx="5" ry="3.5" fill="{P}" {S}/>
<circle cx="12" cy="12" r="2" fill="{Y}"/><circle cx="50" cy="10" r="2" fill="{BL}"/><circle cx="32" cy="52" r="2" fill="{G}"/><circle cx="16" cy="52" r="2" fill="{Y}"/><circle cx="48" cy="52" r="2" fill="{R}"/>''',
    "ostern": f'''<ellipse cx="32" cy="34" rx="16" ry="21" fill="{Y}" {S}/><path d="M17 30q5-4 10 0t10 0 10 0" fill="none" stroke="{R}" stroke-width="3"/>
<path d="M17 40q5 4 10 0t10 0 10 0" fill="none" stroke="{BL}" stroke-width="3"/><circle cx="32" cy="22" r="2.5" fill="{G}"/><circle cx="32" cy="49" r="2.5" fill="{G}"/>''',
    "kino": f'''<rect x="8" y="24" width="48" height="30" rx="3" fill="{K}"/><path d="M8 14l46-8 2 10-46 8z" fill="#FFFFFF" {S}/>
<path d="M17 12.5l4 10M29 10.5l4 10M41 8.5l4 10" stroke="{K}" stroke-width="4"/><path d="M28 32v14l12-7z" fill="{Y}"/>''',
    "feuer": f'''<path d="M32 6q14 14 12 28 4-4 4-10 8 10 4 22-4 10-20 10T12 46q-4-12 4-22 0 6 4 10-2-14 12-28z" fill="{R}" {S}/>
<path d="M32 26q8 8 6 18-1 6-6 6t-6-6q-2-10 6-18z" fill="{Y}"/><path d="M10 58l44-6M10 52l44 6" stroke="{BR}" stroke-width="4" stroke-linecap="round"/>''',
    "roboter": f'''<path d="M32 6v6" stroke="{K}" stroke-width="2"/><circle cx="32" cy="5" r="3" fill="{R}" {S}/>
<rect x="16" y="12" width="32" height="22" rx="6" fill="#FFFFFF" {S}/><circle cx="25" cy="23" r="4" fill="{BL}"/><circle cx="39" cy="23" r="4" fill="{BL}"/>
<path d="M27 30h10" stroke="{K}" stroke-width="2"/><rect x="12" y="20" width="4" height="8" rx="2" fill="{R}" {S}/><rect x="48" y="20" width="4" height="8" rx="2" fill="{R}" {S}/>
<rect x="20" y="36" width="24" height="18" rx="4" fill="{BL}" {S}/><circle cx="32" cy="45" r="4" fill="{Y}"/>
<path d="M20 40l-8 8M44 40l8 8" stroke="{K}" stroke-width="3" stroke-linecap="round"/><path d="M26 54v5M38 54v5" stroke="{K}" stroke-width="3" stroke-linecap="round"/>''',
    "ballon": f'''<path d="M24 40q-2 8 4 18M42 36q2 10-6 22" fill="none" stroke="{K}" stroke-width="1.5"/>
<ellipse cx="24" cy="24" rx="12" ry="15" fill="{R}" {S}/><ellipse cx="42" cy="21" rx="11" ry="14" fill="{BL}" {S}/>
<path d="M22 39l2 2 2-2zM40 35l2 2 2-2z" fill="{K}"/><path d="M19 17q2-5 6-6M38 14q2-4 5-5" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>''',
}

# Reihenfolge = Vorrang (geprüft werden Titel und Text).
REGELN = [
    ("laterne", r"martin|laterne"),
    ("weihnacht", r"weihnacht|advent|nikolaus|christkind|winterlich"),
    ("fasching", r"fasching|fastnacht|karneval|kostüm"),
    ("ostern", r"oster"),
    ("teddy", r"floh|trödel|basar|kindersachen"),
    ("feuer", r"lagerfeuer|stockbrot|feuer"),
    ("roboter", r"robot|coding|programmier|\bki\b|künstliche intelligenz"),
    ("eis", r"\beis\b|eislauf|schlittschuh|eishalle|eissport|on ice"),
    ("kino", r"kino|film"),
    ("theater", r"theater|märchen|puppen|bühne|papageno|vorstellung|\boper\b|zirkus|zauber"),
    ("musik", r"konzert|musik|sing|gitarre|orchester|lieder|band\b"),
    ("buch", r"lesung|buch|bücher|bibliothek|vorles|kibi|geschichten"),
    ("forschen", r"forsch|experiment|technik|labor|wissenschaft|robot|technothek"),
    ("dino", r"dino|saurier|senckenberg|t\. rex"),
    ("tier", r"zoo|tier|bauernhof|pinguin"),
    ("palme", r"palmengarten|palme|tropen"),
    ("basteln", r"werkstatt|bastel|kunst|malen|atelier|workshop|kreativ|gestalten"),
    ("museum", r"museum|ausstellung"),
    ("baum", r"park|garten|wald|natur|spaziergang|wanderung|herbst"),
]

def motiv_name(ev):
    if ev.get("motiv") in MOTIVE:
        return ev["motiv"]
    # Das spezifischste Motiv aus Titel oder Text gewinnt (Reihenfolge in REGELN)
    s = ((ev.get("titel") or "") + " " + (ev.get("text") or "")).lower()
    for name, rx in REGELN:
        if re.search(rx, s):
            return name
    return "ballon"

def svg(name, size=34, cls="mo"):
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">'
            f'{MOTIVE.get(name, MOTIVE["ballon"])}</svg>')

def icon(ev, size=34):
    return svg(motiv_name(ev), size)

# Hintergrundfarben für die große Illustration (wenn ein Wochenend-Tipp kein Foto hat)
FLAECHE = {"laterne": "#1B3B73", "feuer": "#1B3B73", "weihnacht": "#1B3B73", "kino": "#F2B33D",
           "theater": "#FBE3DE", "musik": "#FBE3DE", "dino": "#E6F0E4", "palme": "#E6F0E4", "baum": "#E6F0E4",
           "tier": "#E3EAF5", "eis": "#E3EAF5", "buch": "#F7EBCB", "basteln": "#F7EBCB", "forschen": "#E3EAF5", "roboter": "#E3EAF5"}

def illustration(ev):
    """Breite Illustration als Ersatz für ein fehlendes Foto: großes Motiv mit Konfetti."""
    n = motiv_name(ev)
    bg = FLAECHE.get(n, "#FBE3DE")
    dunkel = bg == "#1B3B73"
    punkte = "#F2B33D" if dunkel else "#E25D4A"
    konf = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" opacity=".55"/>' for x, y, r, c in [
        (30, 22, 4, punkte), (70, 90, 3, BL if not dunkel else "#FFFFFF"), (120, 30, 2.5, G), (250, 25, 3, punkte),
        (285, 95, 4, Y), (215, 100, 2.5, BL if not dunkel else "#FFFFFF"), (95, 60, 2, punkte), (190, 18, 2, G)])
    seiten = "".join(f'<g transform="translate({x} {y}) scale({s})" opacity=".35">{MOTIVE[n]}</g>' for x, y, s in [(18, 44, .9), (248, 30, .8)])
    return (f'<svg class="illu" viewBox="0 0 320 120" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration">'
            f'<rect width="320" height="120" fill="{bg}"/>{konf}{seiten}'
            f'<g transform="translate(115 5) scale(1.72)">{MOTIVE[n]}</g></svg>')
