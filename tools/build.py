#!/usr/bin/env python3
"""Static site build. Plain HTML, no JavaScript.

  writeups-src/*.md  ->  writeups/*.html
  data/reports.json  ->  report tables (per writeup) and the reports section
  data/bounties.json ->  bounty amounts in USD, filled by hand (key -> number)
  index.html         <-  generated here

Run from the repo root:  python3 tools/build.py      (pip install markdown)
"""
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "writeups-src"
OUT = ROOT / "writeups"
E = html.escape

NEXTHUNT_REPO = "https://github.com/0xsila/nexus-nexthunt-ctf-2025-challenges"
NEXTRACE_REPO = "https://github.com/0xsila/nexus-nextrace-2025-challenges"
NEXZERO_REPO = "https://github.com/n3xusss/nexzero-26v"
VDP_POINTS = 7  # reputation points for a resolved VDP report

WRITEUPS = [
    dict(kind="bounty", src="bounty/01-change-one-number-idor-series.md", slug="idor-series",
         title="Change One Number, Own Someone Else's Data",
         summary="Four IDORs in one private program: profile edits, plans, comments and the empty hubId trick.",
         tags=["idor", "access-control", "hackerone"]),
    dict(kind="bounty", src="bounty/02-one-json-field-invisible-owner-mass-assignment.md", slug="mass-assignment",
         title="One JSON Field, One Invisible Project Owner",
         summary="Mass assignment: forging the owner of a project and the timestamps of comments and wiki pages.",
         tags=["mass-assignment", "api", "hackerone"]),
    dict(kind="bounty", src="bounty/03-server-said-no-i-said-yes-response-manipulation.md", slug="response-manipulation",
         title="The Server Said No. I Said Yes.",
         summary="Four response manipulation bugs: protected share links, locked features and OTP bypasses.",
         tags=["response-manipulation", "otp-bypass", "hackerone"]),
    dict(kind="bounty", src="bounty/04-free-trial-that-never-ended-business-logic.md", slug="business-logic",
         title="The Free Trial That Never Ended",
         summary="Business logic bugs: endless trials, plan toggles, member caps and many workspaces on one account.",
         tags=["business-logic", "billing", "hackerone"]),
    dict(kind="ctf", event="NEXTHUNT 2025", src="nexthunt/1xbet.md", slug="1xbet", title="1xbet",
         summary="Mass assignment, content-type confusion and a frontend that trusts status codes.",
         repo=NEXTHUNT_REPO + "/tree/main/1xbet", tags=["mass-assignment", "response-manipulation"]),
    dict(kind="ctf", event="NEXTHUNT 2025", src="nexthunt/dz-kitab.md", slug="dz-kitab", title="Dz-Kitab",
         summary="IDOR protected by a naive check, broken with FAT GET and HTTP parameter pollution.",
         repo=NEXTHUNT_REPO + "/tree/main/Dz-Kitab", tags=["idor", "hpp", "fat-get"]),
    dict(kind="ctf", event="NEXTHUNT 2025", src="nexthunt/gofrita.md", slug="gofrita", title="gofrita",
         summary="Iframe injection to SSRF over gopher, then an X-Original-URL bypass.",
         repo=NEXTHUNT_REPO + "/tree/main/gofrita", tags=["ssrf", "gopher", "impact-escalation"]),
    dict(kind="ctf", event="NEXTHUNT 2025", src="nexthunt/web-daveloper.md", slug="web-daveloper", title="web daveloper",
         summary="WebDAV: method override, PROPFIND enumeration and a header bypass.",
         repo=NEXTHUNT_REPO + "/tree/main/web_daveloper", tags=["webdav", "method-override"]),
    dict(kind="ctf", event="NEXTRACE 2025", src="nextrace/nextrace-2025.md", slug="nextrace-2025",
         title="NEXTRACE 2025: the six web challenges",
         summary="DevTools, response manipulation, headers, HPP and a web cache PURGE bypass.",
         repo=NEXTRACE_REPO, tags=["response-manipulation", "hpp", "web-cache"]),
    dict(kind="ctf", event="NEXZERO 2026", src="nexzero/philosofy.md", slug="philosofy",
         title="philosofy",
         summary="A Host-header allow-list bypassed with wildcard DNS, chained into SSRF and an open redirect back to localhost.",
         repo=NEXZERO_REPO + "/tree/main/web/philosofy", tags=["ssrf", "host-header", "open-redirect"]),
    dict(kind="ctf", event="ICT CTF 2026", src="ict2026/codemy.md", slug="codemy",
         title="Codemy: stealing an admin session through chained cache poisoning",
         summary="Self-XSS, a cache/origin path-parsing mismatch and a WAF race condition chained to steal an admin session.",
         tags=["xss", "cache-poisoning", "race-condition"]),
]

DATA = json.loads((ROOT / "data" / "reports.json").read_text(encoding="utf-8"))
BOUNTIES = json.loads((ROOT / "data" / "bounties.json").read_text(encoding="utf-8")) if (ROOT / "data" / "bounties.json").exists() else {}
ST = DATA["stats"]

# ---------------------------------------------------------------- markdown
GIPHY = re.compile(r"giphy", re.I)


def clean_markdown(text: str, slug: str) -> str:
    lines = text.replace("\r\n", "\n").splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            del lines[i]
            break
    out, skip = [], False
    for ln in lines:
        if GIPHY.search(ln):
            skip = True
            continue
        if skip:
            if ln.strip().startswith("<p><em>") or not ln.strip():
                if ln.strip():
                    skip = False
                continue
            skip = False
        out.append(ln)
    text = "\n".join(out)
    # drop the trophy lines: the data block under the post says it better
    text = re.sub(r"^> 🏆.*\n?", "", text, flags=re.M)
    text = re.sub(r"^[ \t]*(<iframe[^\n]*)$", lambda m: "```html\n" + m.group(1).strip() + "\n```", text, flags=re.M)
    text = re.sub(r"!\[([^\]]*)\]\((image[^)]*\.png)\)", rf"![\1](../assets/writeups/{slug}/\2)", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


MD = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br", "sane_lists"])


def render(text):
    MD.reset()
    return MD.convert(text)


# ---------------------------------------------------------------- report tables
def money(v):
    return f"${v:,.0f}"


def agg_rows(item):
    """Collapse the reports of one item into one display row."""
    rs = item["reports"]
    n = len(rs)
    states = {}
    for r in rs:
        states[r["state"]] = states.get(r["state"], 0) + 1
    first = min(r["reported"] for r in rs)
    tri = [r["triaged"] for r in rs if r["triaged"]]
    res = [r["resolved"] for r in rs if r["resolved"]]
    bnt = [r["bounty"] for r in rs if r["bounty"]]
    return dict(n=n, states=states, reported=first, triaged=min(tri) if tri else None,
                resolved=max(res) if res else None, bounty=min(bnt) if bnt else None,
                program=rs[0]["program"], severity=rs[0]["severity"],
                vdp_resolved=sum(1 for r in rs if r["program"] == "vdp" and r["state"] == "resolved"),
                bounties=len(bnt))


def dd(a, b):
    if not a or not b:
        return ""
    return f" (+{(date.fromisoformat(b) - date.fromisoformat(a)).days}d)"


SHORT = {"not-applicable": "n/a", "informative": "informative", "duplicate": "duplicate",
         "resolved": "resolved", "triaged": "triaged"}


def status_text(states):
    return ", ".join(f"{c} {SHORT[k]}" if len(states) > 1 or c > 1 else SHORT[k] for k, c in states.items())


def reward_cell(item, a):
    key = item["key"]
    if a["bounty"]:
        amt = BOUNTIES.get(key)
        s = money(amt) if amt is not None else "bounty"
        return f"{s}<br><span class='mute'>awarded {a['bounty']}{dd(a['reported'], a['bounty'])}</span>"
    if a["vdp_resolved"]:
        pts = VDP_POINTS * a["vdp_resolved"]
        return f"thanks, +{pts} points<br><span class='mute'>VDP, no bounty</span>"
    return "<span class='mute'>none</span>" + ("<br><span class='mute'>VDP</span>" if a["program"] == "vdp" else "")


def writeup_totals(slug):
    items = DATA["writeups"].get(slug, [])
    reports = sum(i["count"] for i in items)
    b = sum(a["bounties"] for a in map(agg_rows, items))
    v = sum(a["vdp_resolved"] for a in map(agg_rows, items))
    keys = [i["key"] for i in items if any(r["bounty"] for r in i["reports"])]
    amounts = [BOUNTIES.get(k) for k in keys]
    total = sum(amounts) if keys and all(x is not None for x in amounts) else None
    return dict(reports=reports, bounties=b, vdp=v, total=total)


def reports_block(slug):
    items = DATA["writeups"].get(slug)
    if not items:
        return ""
    t = writeup_totals(slug)
    rows = []
    for it in items:
        a = agg_rows(it)
        n = f" <span class='mute'>x{a['n']}</span>" if a["n"] > 1 else ""
        rows.append(
            f"<tr><td class='f'><span class='mute'>{E(it['episode'])} &middot; {'bounty program' if a['program'] == 'bounty' else 'VDP'}</span><br>{E(it['label'])}{n}</td>"
            f"<td>{E(a['severity'] or '-')}</td><td>{E(status_text(a['states']))}</td>"
            f"<td class='n'>{a['reported']}</td>"
            f"<td class='n'>{(a['triaged'] + dd(a['reported'], a['triaged'])) if a['triaged'] else '-'}</td>"
            f"<td class='n'>{(a['resolved'] + dd(a['reported'], a['resolved'])) if a['resolved'] else '-'}</td>"
            f"<td>{reward_cell(it, a)}</td></tr>")
    total = (f"{t['bounties']} bounties" + (f", {money(t['total'])} in total" if t["total"] is not None else "")
             + f"; {t['vdp']} resolved VDP reports (thanks and {VDP_POINTS} points each).")
    return f"""<h2>Reports behind this writeup</h2>
<p class="small mute">{t['reports']} reports on HackerOne. Dates are the day of the event; (+Nd) is the number of days after the report.
Bounty program = paid private program. VDP = vulnerability disclosure program: a thank you and {VDP_POINTS} reputation points per resolved report, which helps get invited to private programs.
Several reports of the same pattern share one row.</p>
<div class="tw"><table>
<thead><tr><th>Finding</th><th>Severity</th><th>Status</th><th>Reported</th><th>Triaged</th><th>Resolved</th><th>Reward</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
<tfoot><tr><td colspan="7">{total}</td></tr></tfoot>
</table></div>"""


# ---------------------------------------------------------------- pages
def head(title, desc, rel):
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="color-scheme" content="dark light">
<link rel="icon" href="{rel}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{rel}assets/css/style.css">
</head><body><div class="wrap">
<header class="top">
<a class="brand" href="{rel}index.html"><span class="mono-mark">0x</span>sila</a>
<nav><a href="{rel}index.html#writeups">writeups</a><a href="{rel}index.html#reports">reports</a><a href="{rel}index.html#certifications">certifications</a><a href="{rel}index.html#contact">contact</a></nav>
</header>
"""


FOOT = '<footer class="foot"><span>Sila Yahia &middot; 0xsila</span><span><a href="mailto:silayahia7@gmail.com">silayahia7@gmail.com</a></span></footer></div></body></html>\n'


def tag_pills(tags):
    return "".join(f'<span class="tag">{E(t)}</span>' for t in tags)


def post_page(w, body, prev_w, next_w):
    if w["kind"] == "bounty":
        t = writeup_totals(w["slug"])
        kicker = "bug bounty &middot; HackerOne private program"
        links = '<p><a href="https://hackerone.com/0xsila">HackerOne profile &rarr;</a></p>'
    else:
        kicker = f"CTF writeup &middot; {E(w['event'])}"
        links = f'<p><a href="{w["repo"]}">Challenge source on GitHub &rarr;</a></p>' if w.get("repo") else ""
    meta = f"{kicker} &middot; {w['read']} min read"

    def nav(x, label):
        return f'<a class="pn-link" href="{x["slug"]}.html"><span class="mute">{label}</span><br>{E(x["title"])}</a>' if x else "<span></span>"

    return (head(f"{w['title']} - 0xsila", w["summary"], "../") +
            f'<article class="post">\n<p><a class="back" href="../index.html#writeups">&larr; writeups</a></p>\n'
            f'<p class="kicker">{meta}</p>\n<h1>{E(w["title"])}</h1>\n<p class="lede">{E(w["summary"])}</p>\n'
            f'<p class="tags">{tag_pills(w["tags"])}</p>\n<div class="prose">{body}</div>\n{reports_block(w["slug"])}\n{links}\n</article>\n'
            f'<div class="pn">{nav(prev_w, "previous")}{nav(next_w, "next")}</div>\n' + FOOT)


def writeup_row(w):
    if w["kind"] == "bounty":
        t = writeup_totals(w["slug"])
        info = f"{t['bounties']} bounties &middot; {t['vdp']} VDP resolved"
        if t["total"] is not None:
            info = f"{money(t['total'])} &middot; " + info
    else:
        info = E(w["event"])
    return (f'<li class="post"><a href="writeups/{w["slug"]}.html">'
            f'<span class="post-title">{E(w["title"])}</span>'
            f'<span class="post-sum">{E(w["summary"])}</span>'
            f'<span class="post-meta"><span class="mute">{info} &middot; {w["read"]} min</span>{tag_pills(w["tags"])}</span>'
            f'</a></li>')


def month_hist():
    bm = ST["by_month"]
    mx = max(bm.values())
    out = []
    for m, c in bm.items():
        out.append(f"{m}  {'#' * round(c * 28 / mx):<28} {c}")
    return "\n".join(out)


def ledger_table():
    rows, total, known = [], 0, 0
    for x in DATA["ledger"]:
        amt = BOUNTIES.get(x["key"])
        if amt is not None:
            total += amt
            known += 1
        link = (f'<a href="writeups/{x["writeup"]}.html">{E(x["label"])}</a>' if x["writeup"] else E(x["label"]))
        rows.append(
            f"<tr><td class='n'>{x['bounty']}</td><td>{link}</td><td>{E(x['severity'] or '-')}</td>"
            f"<td>{E(SHORT[x['state']])}</td><td class='n'>{x['d_bounty']}d</td>"
            f"<td class='n'>{money(amt) if amt is not None else '-'}</td></tr>")
    foot = (f"<tfoot><tr><td colspan='5'>Total, {known} of {len(DATA['ledger'])} amounts filled in</td>"
            f"<td class='n'>{money(total) if known == len(DATA['ledger']) else '-'}</td></tr></tfoot>")
    return ("<div class='tw'><table><thead><tr><th>Awarded</th><th>Finding</th><th>Severity</th><th>Status</th>"
            "<th>Report to bounty</th><th>Bounty</th></tr></thead><tbody>" + "".join(rows) + "</tbody>" + foot + "</table></div>")


def index_page():
    bounty_rows = "\n".join(writeup_row(w) for w in WRITEUPS if w["kind"] == "bounty")
    ctf_rows = "\n".join(writeup_row(w) for w in WRITEUPS if w["kind"] == "ctf")
    s = ST
    sev = s["severity"]
    return head("Sila Yahia (0xsila) - Junior Penetration Tester",
                "Sila Yahia (0xsila): eJPT and CRTA certified junior penetration tester. Bug bounty and CTF writeups.", "") + f"""
<section class="hero">
<div class="avatar" aria-hidden="true">0x</div>
<h1>Sila Yahia</h1>
<p class="role">0xsila &middot; junior penetration tester &middot; Lille, France</p>
<p>Third-year Computer Science student at Université de Lille, certified <b>eJPT</b> and <b>CRTA</b>. I test web applications and APIs, report what I find on HackerOne, and write down how I found it. This page is where I share it.</p>
<p class="mute">Looking for a 3-month internship from April 2027 in cybersecurity, networks or systems.</p>
<p class="links">
<a href="assets/CV_Sila_Yahia_EN.pdf">CV (EN)</a><a href="assets/CV_Sila_Yahia_FR.pdf">CV (FR)</a>
<a href="https://hackerone.com/0xsila">HackerOne</a><a href="https://www.linkedin.com/in/0xsila">LinkedIn</a>
<a href="https://github.com/0xsila">GitHub</a><a href="https://tryhackme.com/p/0xsila">TryHackMe</a>
</p>
</section>

<h2 id="writeups">Writeups</h2>
<h3>Bug bounty</h3>
<ul class="posts">
{bounty_rows}
</ul>
<h3>CTF challenges I wrote</h3>
<ul class="posts">
{ctf_rows}
</ul>

<h2 id="reports">HackerOne reports</h2>
<p class="small mute">Numbers from my own HackerOne export, {s['first_report']} to {s['last_report']}. Program and company names are not published.</p>
<dl class="kv">
<dt>submitted</dt><dd>{s['total']} reports</dd>
<dt>resolved</dt><dd>{s['by_state'].get('resolved', 0)}, plus {s['by_state'].get('triaged', 0)} triaged and waiting</dd>
<dt>bounties</dt><dd>{s['bounties_awarded']} awarded in a private bounty program</dd>
<dt>VDP</dt><dd>{s['vdp_resolved']} resolved reports: a thank you and {VDP_POINTS} points each, which helps toward private program invitations</dd>
<dt>not accepted</dt><dd>{s['by_state'].get('duplicate', 0)} duplicates, {s['by_state'].get('informative', 0)} informative, {s['by_state'].get('not-applicable', 0)} not applicable</dd>
<dt>severity</dt><dd>{sev['critical']} critical, {sev['high']} high, {sev['medium']} medium, {sev['low']} low (as rated on the report)</dd>
<dt>median time</dt><dd>first response {s['median_days_first_response']} days, triage {s['median_days_triage']} days, resolution {s['median_days_resolve']} days, bounty {s['median_days_bounty']} days after the report</dd>
</dl>
<h3>Reports per month</h3>
<pre class="hist">{month_hist()}</pre>
<h3>Bounties</h3>
{ledger_table()}

<h2 id="certifications">Certifications</h2>
<div class="cert"><a href="assets/img/ejpt.png"><img src="assets/img/ejpt.png" alt="eJPT certificate" loading="lazy"></a>
<div><b>eJPT, Junior Penetration Tester</b><p>INE Security. Network and web penetration testing, practical exam.</p><p>Awarded June 10, 2026 &middot; ID 184946744</p></div></div>
<div class="cert"><a href="assets/img/crta.png"><img src="assets/img/crta.png" alt="CRTA certificate" loading="lazy"></a>
<div><b>CRTA, Certified Red Team Analyst</b><p>CyberWarfare Labs. Certification exam.</p><p>Issued Oct 2026 &middot; ID CRTA-6acd5677a8a9c04f32d91f74</p></div></div>

<h2>Experience</h2>
<ul class="rows">
<li><span class="t">Bug Bounty Hunter, independent</span><span class="r">Dec 2024 - present</span><span class="d">Web application and API testing on HackerOne: recon, endpoint discovery, access control, mass assignment, business logic. Responsible disclosure and public writeups.</span></li>
<li><span class="t">Technical Manager, Nexus Security Club</span><span class="r">Sep 2025 - present</span><span class="d">Organising security events and CTFs, deploying challenges and infrastructure, running workshops on web security. Author of the NEXZERO (2026), NEXTHUNT (2025) and NEXTRACE (2025) challenges.</span></li>
</ul>

<h2>Education</h2>
<ul class="rows">
<li><span class="t">Université de Lille, Licence Informatique (L3)</span><span class="r">2026 - present</span></li>
<li><span class="t">ESTIN, École supérieure en Sciences et Technologies de l'Informatique</span><span class="r">2023 - 2026</span></li>
</ul>

<h2>Skills</h2>
<dl class="kv">
<dt>security</dt><dd>web and network penetration testing, OWASP Top 10, API security, recon, vulnerability assessment</dd>
<dt>tools</dt><dd>Burp Suite, Nmap, Wireshark, Metasploit</dd>
<dt>networks</dt><dd>TCP/IP, Cisco</dd>
<dt>systems</dt><dd>Linux, Windows</dd>
<dt>scripting</dt><dd>Python, Bash</dd>
<dt>languages</dt><dd>Arabic and Kabyle (native), French (B2), English (B2)</dd>
<dt>other</dt><dd>Hack The Box and TryHackMe player; Hackini 2.0 (2026), 2nd place</dd>
</dl>

<h2 id="contact">Contact</h2>
<p><a href="mailto:silayahia7@gmail.com">silayahia7@gmail.com</a> &middot; <a href="https://www.linkedin.com/in/0xsila">linkedin.com/in/0xsila</a> &middot; <a href="https://hackerone.com/0xsila">hackerone.com/0xsila</a></p>
""" + FOOT


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.html"):
        old.unlink()
    shutil.rmtree(ROOT / "assets" / "writeups", ignore_errors=True)
    for i, w in enumerate(WRITEUPS):
        mdp = SRC / w["src"]
        text = clean_markdown(mdp.read_text(encoding="utf-8"), w["slug"])
        w["read"] = max(1, round(len(text.split()) / 200))
        for img in re.findall(r"\(\.\./assets/writeups/[^/]+/([^)]+)\)", text):
            dst = ROOT / "assets" / "writeups" / w["slug"]
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy(mdp.parent / img, dst / img)
        prev_w = WRITEUPS[i - 1] if i else None
        next_w = WRITEUPS[i + 1] if i < len(WRITEUPS) - 1 else None
        (OUT / f"{w['slug']}.html").write_text(post_page(w, render(text), prev_w, next_w), encoding="utf-8")
    (ROOT / "index.html").write_text(index_page(), encoding="utf-8")
    print(f"built {len(WRITEUPS)} writeups + index.html")


if __name__ == "__main__":
    main()
