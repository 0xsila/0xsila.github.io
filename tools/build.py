#!/usr/bin/env python3
"""Static site build. A blog-focused portfolio, no JavaScript.

  writeups-src/*.md  ->  writeups/*.html
  index.html         <-  generated here

Run from the repo root:  python3 tools/build.py      (pip install markdown)
"""
import html
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "writeups-src"
OUT = ROOT / "writeups"
E = html.escape

NEXTHUNT_REPO = "https://github.com/0xsila/nexus-nexthunt-ctf-2025-challenges"
NEXTRACE_REPO = "https://github.com/0xsila/nexus-nextrace-2025-challenges"
NEXZERO_REPO = "https://github.com/n3xusss/nexzero-26v"

# Original line-icon per writeup (no photos/art - drawn here, 24x24, currentColor stroke),
# picked by the writeup's first tag. One per card, like a thumbnail.
ICONS = {
    "idor": '<path d="M7 11V8a5 5 0 0 1 9.5-2.2M7 11h10a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z"/><circle cx="12" cy="15" r="1.6"/>',
    "mass-assignment": '<path d="M9 4c-2 0-3 1-3 3v3c0 1-.5 2-2 2 1.5 0 2 1 2 2v3c0 2 1 3 3 3M15 4c2 0 3 1 3 3v3c0 1 .5 2 2 2-1.5 0-2 1-2 2v3c0 2-1 3-3 3"/>',
    "response-manipulation": '<path d="M4 8h13M13 5l4 3-4 3M20 16H7M11 13l-4 3 4 3"/>',
    "business-logic": '<path d="M7 12c0-2 1.5-3.5 3-3.5S12 10 12 12s1.5 3.5 3 3.5 3-1.5 3-3.5-1.5-3.5-3-3.5-3 1.5-3 3.5-1.5 3.5-3 3.5-3-1.5-3-3.5Z"/>',
    "ssrf": '<rect x="4" y="4" width="16" height="5" rx="1"/><rect x="4" y="15" width="16" height="5" rx="1"/><circle cx="7.5" cy="6.5" r=".6" fill="currentColor" stroke="none"/><circle cx="7.5" cy="17.5" r=".6" fill="currentColor" stroke="none"/><path d="M9 9v2a3 3 0 0 0 3 3h1m0 0-1.6-1.6M13 14l-1.6 1.6"/>',
    "webdav": '<path d="M4 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7Z"/><circle cx="15" cy="15" r="2.2"/><path d="M15 12.3v.6M15 16.1v.6M17.7 15h-.6M13.5 15h-.6M16.9 13.1l-.4.4M13.9 16.1l-.4.4M16.9 16.9l-.4-.4M13.9 13.9l-.4-.4"/>',
    "xss": '<path d="M8 7 3 12l5 5M16 7l5 5-5 5M13 5 11 19"/>',
    "generic": '<path d="M4 5h16M4 10h10M4 15h16M4 20h10"/>',
}

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
    # drop the trophy lines: they referred to the old per-report data tables
    text = re.sub(r"^> 🏆.*\n?", "", text, flags=re.M)

    # wrap bare <iframe ...> lines in a code fence, but never inside an
    # existing fenced block (double-fencing breaks the markdown parser)
    FENCE = re.compile(r"```.*?```", re.S)

    def fence_bare_iframes(segment):
        return re.sub(r"^[ \t]*(<iframe[^\n]*)$", lambda m: "```html\n" + m.group(1).strip() + "\n```",
                       segment, flags=re.M)

    parts = FENCE.split(text)
    fences = FENCE.findall(text)
    parts = [fence_bare_iframes(p) for p in parts]
    text = parts[0] + "".join(fe + part for fe, part in zip(fences, parts[1:]))

    text = re.sub(r"!\[([^\]]*)\]\((image[^)]*\.png)\)", rf"![\1](../assets/writeups/{slug}/\2)", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


MD = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br", "sane_lists"])


def render(text):
    MD.reset()
    return MD.convert(text)


# ---------------------------------------------------------------- pages
def head(title, desc, rel):
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#0a0a0f">
<meta name="color-scheme" content="dark">
<link rel="icon" href="{rel}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{rel}assets/css/style.css">
</head><body>
<div class="bg" aria-hidden="true"></div>
<div class="wrap">
<header class="top">
<a class="brand" href="{rel}index.html"><span class="blob" aria-hidden="true"></span>0xsila</a>
<nav><a href="{rel}index.html#writeups">writeups</a><a href="{rel}index.html#certifications">certifications</a><a href="{rel}index.html#contact">contact</a></nav>
</header>
"""


FOOT = '<footer class="foot"><span>Sila Yahia &middot; 0xsila</span><span><a href="mailto:silayahia7@gmail.com">silayahia7@gmail.com</a></span></footer></div></body></html>\n'


def tag_pills(tags):
    return "".join(f'<span class="tag">{E(t)}</span>' for t in tags)


def icon_svg(w, size=24):
    svg = ICONS.get(w["tags"][0], ICONS["generic"])
    return f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{svg}</svg>'


def post_page(w, body, prev_w, next_w):
    if w["kind"] == "bounty":
        kicker = "bug bounty &middot; HackerOne private program"
        links = '<p><a class="more" href="https://hackerone.com/0xsila">HackerOne profile &rarr;</a></p>'
    else:
        kicker = f"CTF writeup &middot; {E(w['event'])}"
        links = f'<p><a class="more" href="{w["repo"]}">Challenge source on GitHub &rarr;</a></p>' if w.get("repo") else ""
    meta = f"{kicker} &middot; {w['read']} min read"

    def nav(x, label):
        return f'<a class="pn-link" href="{x["slug"]}.html"><span class="mute">{label}</span><br>{E(x["title"])}</a>' if x else "<span></span>"

    return (head(f"{w['title']} - 0xsila", w["summary"], "../") +
            f'<article class="post">\n<p><a class="back" href="../index.html#writeups">&larr; writeups</a></p>\n'
            f'<div class="post-icon">{icon_svg(w, 30)}</div>\n'
            f'<p class="kicker">{meta}</p>\n<h1>{E(w["title"])}</h1>\n<p class="lede">{E(w["summary"])}</p>\n'
            f'<p class="tags">{tag_pills(w["tags"])}</p>\n<div class="prose">{body}</div>\n{links}\n</article>\n'
            f'<div class="pn">{nav(prev_w, "previous")}{nav(next_w, "next")}</div>\n' + FOOT)


def writeup_row(w):
    info = "bug bounty" if w["kind"] == "bounty" else E(w["event"])
    return (f'<li class="post"><a href="writeups/{w["slug"]}.html">'
            f'<span class="thumb">{icon_svg(w)}</span>'
            f'<span class="post-body">'
            f'<span class="post-title">{E(w["title"])}</span>'
            f'<span class="post-sum">{E(w["summary"])}</span>'
            f'<span class="post-meta"><span class="mute">{info} &middot; {w["read"]} min read</span>{tag_pills(w["tags"])}</span>'
            f'</span></a></li>')


def index_page():
    bounty_rows = "\n".join(writeup_row(w) for w in WRITEUPS if w["kind"] == "bounty")
    ctf_rows = "\n".join(writeup_row(w) for w in WRITEUPS if w["kind"] == "ctf")
    return head("Sila Yahia (0xsila) - Junior Penetration Tester",
                "Sila Yahia (0xsila): eJPT and CRTA certified junior penetration tester. Bug bounty and CTF writeups.", "") + f"""
<section class="hero">
<p class="pre">whoami</p>
<h1>Sila <span class="accent">Yahia</span></h1>
<p class="role">0xsila &middot; junior penetration tester &middot; Lille, France</p>
<p class="bio">I break web apps and APIs, report what I find on HackerOne, and write up how I found it. I also design and build CTF challenges. This page is where all of that lives.</p>
<p class="mute">Looking for a 3-month internship from April 2027 in cybersecurity, networks or systems.</p>
<p class="links">
<a class="btn" href="assets/CV_Sila_Yahia_EN.pdf">CV (EN)</a><a class="btn" href="assets/CV_Sila_Yahia_FR.pdf">CV (FR)</a>
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

<h2 id="certifications">Certifications</h2>
<div class="certs">
<a class="cert" href="assets/img/ejpt.png">
  <img src="assets/img/ejpt.png" alt="eJPT certificate" loading="lazy">
  <div><b>eJPT</b><span class="mute">Junior Penetration Tester &middot; INE Security &middot; 2026</span></div>
</a>
<a class="cert" href="assets/img/crta.png">
  <img src="assets/img/crta.png" alt="CRTA certificate" loading="lazy">
  <div><b>CRTA</b><span class="mute">Certified Red Team Analyst &middot; CyberWarfare Labs &middot; 2026</span></div>
</a>
</div>

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
