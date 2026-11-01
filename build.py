"""Baut aus events.json die Event-Seite (index.html) und das WhatsApp-Bild (whatsapp.html -> whatsapp.png)."""
import json, datetime, html, sys
from pathlib import Path

BASE = Path(__file__).parent
data = json.loads((BASE / "events.json").read_text(encoding="utf-8"))
events = sorted(data["events"], key=lambda e: (e["date"], e["time"]))

WD = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WD_S = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MON = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

def d(s): return datetime.date.fromisoformat(s)
def esc(s): return html.escape(s or "")

# ---------- Kategorie-Illustrationen (eigene, einfache SVG-Motive) ----------
CAT = {
  "theater":  ("#F6D6DE", "Theater"),
  "musik":    ("#D9E8F7", "Musik"),
  "museum":   ("#E4E0F5", "Museum & Wissen"),
  "basteln":  ("#FCE7C8", "Basteln"),
  "sport":    ("#D6F0EE", "Sport"),
  "flohmarkt":("#E6EFD3", "Flohmarkt"),
}
def illu(cat):
    bg = CAT[cat][0]
    shapes = {
     "theater": '<path d="M8 10h84v10H8z" fill="#B23A5B"/><path d="M8 20c10 0 14 30 6 62H8z" fill="#D2557A"/><path d="M92 20c-10 0-14 30-6 62h6z" fill="#D2557A"/><circle cx="42" cy="52" r="13" fill="#FFF6E5"/><circle cx="37" cy="49" r="2" fill="#3A2A2F"/><circle cx="47" cy="49" r="2" fill="#3A2A2F"/><path d="M36 56q6 6 12 0" stroke="#3A2A2F" stroke-width="2" fill="none"/><circle cx="60" cy="60" r="11" fill="#FFD25E"/><circle cx="56" cy="58" r="1.8" fill="#3A2A2F"/><circle cx="64" cy="58" r="1.8" fill="#3A2A2F"/><path d="M55 66q5-4 10 0" stroke="#3A2A2F" stroke-width="2" fill="none"/>',
     "musik": '<path d="M38 26l34-8v40" stroke="#2F5D8A" stroke-width="5" fill="none"/><path d="M38 26v44" stroke="#2F5D8A" stroke-width="5"/><ellipse cx="31" cy="71" rx="9" ry="7" fill="#2F5D8A"/><ellipse cx="65" cy="60" rx="9" ry="7" fill="#2F5D8A"/><circle cx="80" cy="30" r="4" fill="#F2A541"/><circle cx="22" cy="36" r="3" fill="#E5677F"/>',
     "museum": '<path d="M50 14l36 18H14z" fill="#6A5ACD"/><rect x="18" y="34" width="64" height="5" fill="#8B7FE0"/><rect x="22" y="42" width="7" height="30" fill="#FFFFFF"/><rect x="38" y="42" width="7" height="30" fill="#FFFFFF"/><rect x="55" y="42" width="7" height="30" fill="#FFFFFF"/><rect x="71" y="42" width="7" height="30" fill="#FFFFFF"/><rect x="14" y="74" width="72" height="7" fill="#6A5ACD"/>',
     "basteln": '<circle cx="30" cy="66" r="9" fill="none" stroke="#D9822B" stroke-width="5"/><circle cx="50" cy="70" r="9" fill="none" stroke="#D9822B" stroke-width="5"/><path d="M35 58l28-40M46 62l8-44" stroke="#8C5A2B" stroke-width="4"/><rect x="66" y="30" width="10" height="44" rx="3" transform="rotate(20 71 52)" fill="#E5677F"/><circle cx="78" cy="22" r="5" fill="#4CAF8E"/>',
     "sport": '<path d="M30 22h22v22l20 8c6 3 8 7 8 12v4H30z" fill="#1F8A84"/><path d="M36 30h10M36 37h10" stroke="#9AD3CF" stroke-width="3"/><path d="M24 74h60" stroke="#2C3E50" stroke-width="4" stroke-linecap="round"/><path d="M38 68v6M70 68v6" stroke="#2C3E50" stroke-width="3"/><circle cx="80" cy="22" r="6" fill="#F2A541"/>',
     "flohmarkt": '<rect x="18" y="46" width="64" height="32" rx="3" fill="#C98B4E"/><path d="M18 46l8-10h48l8 10z" fill="#E0A96D"/><circle cx="42" cy="36" r="10" fill="#B07A4A"/><circle cx="34" cy="28" r="4" fill="#B07A4A"/><circle cx="50" cy="28" r="4" fill="#B07A4A"/><circle cx="39" cy="35" r="1.5" fill="#2B1D12"/><circle cx="45" cy="35" r="1.5" fill="#2B1D12"/><rect x="58" y="26" width="16" height="20" rx="2" fill="#5B8C3A"/>',
    }[cat]
    return f'<svg viewBox="0 0 100 92" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="100" height="92" rx="14" fill="{bg}"/>{shapes}</svg>'

AD = {
  "kicker": "Anzeige · aus dem Nordend",
  "title": "Kindergeburtstag im Park?",
  "text": "Bald gibt es hier fertige Schnitzeljagden für Frankfurter Parks – zum Ausdrucken, mit Rätseln und Stationen. Den Anfang macht der Günthersburgpark.",
  "cta": "Spiele für Feste ausleihen: nordend-spieleverleih.de",
  "url": "https://nordend-spieleverleih.de/",
}

# ------------------------------- Webseite ------------------------------------
def card(e):
    badges = [f'<span class="b">{esc(e["age"])}</span>']
    badges.append(f'<span class="b {"free" if e["free"] else ""}">{esc(e["price"])}</span>')
    if e["indoor"]: badges.append('<span class="b in">drinnen</span>')
    if e.get("check"): badges.append('<span class="b warn" title="Diese Angabe vor Veröffentlichung prüfen">⚠ prüfen</span>')
    place = esc(e["venue"]) + (f', {esc(e["address"])}' if e["address"] else "")
    dd = d(e["date"])
    attrs = f'data-free="{int(e["free"])}" data-in="{int(e["indoor"])}" data-we="{int(dd.weekday()>=5)}" data-age="{esc(e["age"])}"'
    return f'''<article class="ev" {attrs}>
  <div class="pic">{illu(e["cat"])}<span class="cat">{CAT[e["cat"]][1]}</span></div>
  <div class="body">
    <div class="time">{esc(e["time"])}{(" · " + esc(e["range"])) if e.get("range") else ""}</div>
    <h3>{esc(e["title"])}</h3>
    <div class="place">{place} · <b>{esc(e["district"])}</b></div>
    <p>{esc(e["text"])}</p>
    <div class="badges">{"".join(badges)}</div>
    <a class="src" href="{esc(e["url"])}" target="_blank" rel="noopener">Zum Veranstalter →</a>
  </div>
</article>'''

days = {}
for e in events: days.setdefault(e["date"], []).append(e)

sections = []
for i, (ds, evs) in enumerate(days.items()):
    dd = d(ds)
    sections.append(f'<section class="day" data-date="{ds}"><h2><span>{WD[dd.weekday()]}</span> {dd.day}. {MON[dd.month]}</h2>' + "".join(card(e) for e in evs) + "</section>")
    if dd.weekday() == 5:  # Werbung nach Samstag
        sections.append(f'''<aside class="ad"><div class="adk">{AD["kicker"]}</div><h3>{AD["title"]}</h3><p>{AD["text"]}</p><a href="{AD["url"]}" target="_blank" rel="noopener">{AD["cta"]} →</a></aside>''')

page = f'''<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gude Laune – Kinder-Events in Frankfurt (Entwurf)</title>
<meta name="description" content="Was ist los mit Kindern in Frankfurt? Die besten Kinder-Events der Woche, nach Tagen sortiert – kurz, übersichtlich, jede Woche neu.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Poppins:wght@700;800&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1F2A2E;--mute:#5E6B70;--line:#E7E2D8;--bg:#FFFBF3;--sun:#FFC83D;--green:#1E7A5A;--card:#fff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Nunito,system-ui,sans-serif}}
.wrap{{max-width:760px;margin:0 auto;padding:0 18px}}
header{{padding:28px 0 8px}}
.logo{{font:800 30px/1 Poppins,sans-serif;letter-spacing:-.5px;display:flex;align-items:center;gap:10px}}
.logo i{{width:34px;height:34px;border-radius:50%;background:var(--sun);display:inline-block;box-shadow:0 0 0 6px #FFE9A8}}
.tag{{color:var(--mute);margin:8px 0 0;font-weight:600}}
.draft{{background:#FFF1C9;border:1px dashed #E0B341;border-radius:12px;padding:10px 14px;font-size:14px;margin:16px 0 0}}
.week{{display:flex;justify-content:space-between;align-items:end;margin:26px 0 10px;gap:12px;flex-wrap:wrap}}
.week h1{{font:800 26px/1.15 Poppins,sans-serif;margin:0}} .week small{{color:var(--mute);font-weight:700}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 18px;position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:5}}
.chip{{border:1.5px solid var(--line);background:#fff;border-radius:999px;padding:7px 14px;font:700 14px Nunito,sans-serif;cursor:pointer;color:var(--ink)}}
.chip[aria-pressed=true]{{background:var(--ink);color:#fff;border-color:var(--ink)}}
.wa{{display:flex;gap:14px;align-items:center;background:#E7F6EE;border-radius:16px;padding:14px 16px;margin:0 0 22px}}
.wa b{{display:block}} .wa a{{margin-left:auto;background:#25A366;color:#fff;text-decoration:none;font-weight:800;padding:9px 14px;border-radius:10px;white-space:nowrap}}
.day h2{{font:800 19px Poppins,sans-serif;margin:28px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--line)}} .day h2 span{{color:var(--green)}}
.ev{{display:grid;grid-template-columns:110px 1fr;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:14px;margin:0 0 12px}}
.pic{{position:relative}} .pic svg{{width:110px;height:101px;display:block}}
.cat{{display:block;text-align:center;font-size:12px;color:var(--mute);font-weight:700;margin-top:4px}}
.time{{font-weight:800;color:var(--green);font-size:14px}}
.ev h3{{margin:2px 0 2px;font:700 18px/1.25 Poppins,sans-serif}}
.place{{color:var(--mute);font-size:14px}} .ev p{{margin:8px 0 10px;font-size:15px}}
.badges{{display:flex;gap:6px;flex-wrap:wrap}} .b{{font-size:12.5px;font-weight:700;background:#F3EFE6;border-radius:8px;padding:3px 8px}}
.b.free{{background:#DDF3E6;color:#14603F}} .b.in{{background:#E3EEF9;color:#24527E}} .b.warn{{background:#FFE3D6;color:#9A3B12}}
.src{{display:inline-block;margin-top:10px;font-weight:800;color:var(--ink);font-size:14px}}
.ad{{background:linear-gradient(135deg,#FFE48A,#FFC83D);border-radius:18px;padding:18px 20px;margin:18px 0 4px}}
.adk{{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;opacity:.7}}
.ad h3{{font:800 21px Poppins,sans-serif;margin:4px 0}} .ad p{{margin:0 0 10px}} .ad a{{font-weight:800;color:var(--ink)}}
.empty{{display:none;color:var(--mute);text-align:center;padding:30px}}
footer{{color:var(--mute);font-size:13.5px;padding:34px 0 50px;border-top:1px solid var(--line);margin-top:30px}} footer a{{color:var(--mute)}}
@media (max-width:520px){{.ev{{grid-template-columns:76px 1fr;gap:12px}} .pic svg{{width:76px;height:70px}} .cat{{display:none}} .wa{{flex-wrap:wrap}} .wa a{{margin-left:0}}}}
</style></head><body><div class="wrap">
<header>
  <div class="logo"><i></i>Gude Laune</div>
  <p class="tag">Kinder-Events in Frankfurt – jede Woche frisch, ohne Schnickschnack.</p>
  <div class="draft"><b>Entwurf / Probelauf.</b> Alle Termine wurden automatisch recherchiert. Einträge mit „⚠ prüfen“ haben unsichere Angaben und würden vor Veröffentlichung kontrolliert.</div>
</header>
<div class="week"><h1>Diese Woche mit Kind</h1><small>{data["week"]["label"]} · {len(events)} Tipps</small></div>
<div class="wa"><div><b>Die Wochentipps aufs Handy</b>Jeden Donnerstag eine Übersicht als Bild – zum Weiterleiten in die Kita-Gruppe.</div><a href="#">WhatsApp-Kanal folgen</a></div>
<div class="chips" role="group" aria-label="Filter">
  <button class="chip" data-f="all" aria-pressed="true">Alle</button>
  <button class="chip" data-f="we" aria-pressed="false">Wochenende</button>
  <button class="chip" data-f="free" aria-pressed="false">Kostenlos</button>
  <button class="chip" data-f="in" aria-pressed="false">Bei Regen (drinnen)</button>
  <button class="chip" data-f="small" aria-pressed="false">Unter 3</button>
  <button class="chip" data-f="kita" aria-pressed="false">Kita-Alter</button>
</div>
<main>{"".join(sections)}<div class="empty">Für diesen Filter gibt es diese Woche nichts – probier einen anderen.</div></main>
<footer>Alle Angaben ohne Gewähr – bitte vor dem Besuch beim Veranstalter prüfen. Texte sind eigene Zusammenfassungen, Bilder sind Symbolbilder.<br>
Ein Angebot von <a href="https://nordend-spieleverleih.de/">Nordend-Spieleverleih</a> · Impressum · Datenschutz</footer>
</div>
<script>
const chips=[...document.querySelectorAll('.chip')];
function ok(el,f){{const a=el.dataset.age;
 if(f==='all')return true; if(f==='we')return el.dataset.we==='1'; if(f==='free')return el.dataset.free==='1'; if(f==='in')return el.dataset.in==='1';
 if(f==='small')return /0–3|alle|Familien/.test(a); if(f==='kita')return /3–6|ab 3|ab 4|alle|Familien|Kinder/.test(a); return true}}
chips.forEach(c=>c.addEventListener('click',()=>{{chips.forEach(x=>x.setAttribute('aria-pressed',x===c));const f=c.dataset.f;let n=0;
 document.querySelectorAll('.day').forEach(s=>{{let v=0;s.querySelectorAll('.ev').forEach(e=>{{const s2=ok(e,f);e.style.display=s2?'':'none';v+=s2}});s.style.display=v?'':'none';n+=v}});
 document.querySelector('.empty').style.display=n?'none':'block'}}));
</script></body></html>'''
(BASE / "index.html").write_text(page, encoding="utf-8")

# ----------------------------- WhatsApp-Bild ----------------------------------
tops = [e for e in events if e.get("top")]
for e in events:  # auffüllen auf 6 Highlights, möglichst verschiedene Tage
    if len(tops) >= 6: break
    if e not in tops and e["id"] not in ("donner-so", "mfk-so"): tops.append(e)
tops = sorted(tops[:6], key=lambda e: (e["date"], e["time"]))
free_in = [e for e in events if e["free"] and e not in tops]

def wa_item(e):
    dd = d(e["date"])
    return f'''<div class="it"><div class="dt"><b>{WD_S[dd.weekday()]}</b>{dd.day}.{dd.month}.</div>{illu(e["cat"])}
<div class="tx"><h3>{esc(e["title"])}</h3><div class="mt">{esc(e["time"])} · {esc(e["venue"].split(" (")[0])}, {esc(e["district"])}</div>
<div class="bg"><span>{esc(e["age"])}</span><span class="{'fr' if e['free'] else ''}">{esc(e["price"])}</span>{'<span class="in">drinnen</span>' if e["indoor"] else ''}</div></div></div>'''

wa = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}} body{{margin:0;width:1080px;height:1720px;background:#FFFBF3;font-family:Poppins,sans-serif;color:#1F2A2E}}
.hd{{background:#FFC83D;padding:46px 56px 40px;position:relative;overflow:hidden}}
.hd:after{{content:"";position:absolute;right:-90px;top:-90px;width:330px;height:330px;border-radius:50%;background:#FFE48A}}
.lg{{font-weight:800;font-size:38px;position:relative;z-index:1}} .lg i{{display:inline-block;width:30px;height:30px;border-radius:50%;background:#fff;margin-right:12px;vertical-align:-3px}}
h1{{font-size:68px;line-height:1.02;margin:16px 0 8px;position:relative;z-index:1;letter-spacing:-1px}}
.sub{{font-size:30px;font-weight:700;position:relative;z-index:1}}
.list{{padding:30px 46px 0}}
.it{{display:grid;grid-template-columns:96px 112px 1fr;gap:22px;align-items:center;background:#fff;border:2px solid #EFE9DD;border-radius:26px;padding:18px 22px;margin-bottom:16px}}
.it svg{{width:112px;height:103px}}
.dt{{text-align:center;font-size:24px;font-weight:700;color:#1E7A5A;line-height:1.1}} .dt b{{display:block;font-size:40px;font-weight:800}}
.tx h3{{font-size:31px;line-height:1.15;margin:0 0 6px}} .mt{{font-size:22px;color:#5E6B70;font-weight:600;line-height:1.3}}
.bg{{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}} .bg span{{font-size:19px;font-weight:700;background:#F3EFE6;border-radius:10px;padding:4px 12px}}
.bg .fr{{background:#DDF3E6;color:#14603F}} .bg .in{{background:#E3EEF9;color:#24527E}}
.ad{{margin:10px 46px 0;background:#1F2A2E;color:#fff;border-radius:26px;padding:26px 30px;display:flex;gap:24px;align-items:center}}
.ad .k{{font-size:18px;opacity:.6;font-weight:700;text-transform:uppercase;letter-spacing:.08em}} .ad h4{{font-size:32px;margin:4px 0}} .ad p{{font-size:22px;margin:0;opacity:.9;font-weight:500}}
.ad .s{{flex:none;width:92px;height:92px;border-radius:50%;background:#FFC83D;display:grid;place-items:center;font-size:46px}}
.ft{{padding:26px 56px;display:flex;justify-content:space-between;font-size:22px;font-weight:700;color:#5E6B70}}
.ft b{{color:#1E7A5A}}
</style></head><body>
<div class="hd"><div class="lg"><i></i>Gude Laune</div><h1>Kinder-Tipps<br>für Frankfurt</h1><div class="sub">{data["week"]["label"]} · die Highlights der Woche</div></div>
<div class="list">{"".join(wa_item(e) for e in tops)}</div>
<div class="ad"><div class="s">🧭</div><div><div class="k">Bald im Nordend</div><h4>Schnitzeljagd im Günthersburgpark</h4><p>Fertig zum Ausdrucken – für den nächsten Kindergeburtstag.</p></div></div>
<div class="ft"><span>Alle {len(events)} Termine: <b>gude-laune.de</b></span><span>Angaben ohne Gewähr</span></div>
</body></html>'''
(BASE / "whatsapp.html").write_text(wa, encoding="utf-8")
print("ok", len(events), "events,", len(tops), "highlights")
