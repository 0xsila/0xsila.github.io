#!/usr/bin/env python3
"""Static site build: renders writeups-src/*.md -> writeups/*.html and fills
the writeups section of index.template.html -> index.html.

Run from the repo root:  python3 tools/build.py
Requires: pip install markdown
"""
import html
import re
import shutil
from pathlib import Path
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "writeups-src"
OUT = ROOT / "writeups"

NEXTHUNT_REPO = "https://github.com/0xsila/nexus-nexthunt-ctf-2025-challenges/tree/main/"
NEXTRACE_REPO = "https://github.com/0xsila/nexus-nextrace-2025-challenges/tree/main/"

# kind: bounty | ctf ; group is the label shown on cards
WRITEUPS = [
    # ---- Bug bounty (HackerOne) ----
    dict(kind="bounty", group="Bug bounty", src="bounty/01-change-one-number-idor-series.md",
         slug="idor-series", title="Change One Number, Own Someone Else's Data",
         summary="Four IDORs in one private program: edit profiles, delete plans and comments, and the empty hubId trick.",
         tags=["IDOR", "Access control", "HackerOne"], badge="4 bugs"),
    dict(kind="bounty", group="Bug bounty", src="bounty/02-one-json-field-invisible-owner-mass-assignment.md",
         slug="mass-assignment", title="One JSON Field, One Invisible Project Owner",
         summary="The server copied everything I sent onto its objects. I told it who created a project (nobody) and when a comment was written (2001).",
         tags=["Mass assignment", "API", "HackerOne"], badge="3 bugs"),
    dict(kind="bounty", group="Bug bounty", src="bounty/03-server-said-no-i-said-yes-response-manipulation.md",
         slug="response-manipulation", title="The Server Said No. I Said Yes.",
         summary="Four response-manipulation bugs: password-protected share links, locked features and three flavours of OTP bypass.",
         tags=["Response manipulation", "OTP bypass", "HackerOne"], badge="4 bugs"),
    dict(kind="bounty", group="Bug bounty", src="bounty/04-free-trial-that-never-ended-business-logic.md",
         slug="business-logic", title="The Free Trial That Never Ended",
         summary="Business logic bugs that print money: endless trials, plan toggles, member caps and one account with many workspaces.",
         tags=["Business logic", "Billing", "HackerOne"], badge="4 bugs"),
    # ---- CTF authored: NEXTHUNT 2025 ----
    dict(kind="ctf", group="NEXTHUNT 2025", src="nexthunt/1xbet.md", slug="1xbet", title="1xbet",
         summary="A rigged casino. Mass assignment, content-type confusion and a frontend that trusts status codes.",
         tags=["Mass assignment", "Response manipulation", "Business logic"], badge="web",
         repo=NEXTHUNT_REPO + "1xbet"),
    dict(kind="ctf", group="NEXTHUNT 2025", src="nexthunt/dz-kitab.md", slug="dz-kitab", title="Dz-Kitab",
         summary="IDOR protected by a naive check, broken with a FAT GET plus HTTP parameter pollution.",
         tags=["IDOR", "FAT GET", "HPP"], badge="web", repo=NEXTHUNT_REPO + "Dz-Kitab"),
    dict(kind="ctf", group="NEXTHUNT 2025", src="nexthunt/gofrita.md", slug="gofrita", title="gofrita",
         summary="Iframe injection escalated to SSRF over the gopher protocol, then an X-Original-URL header bypass.",
         tags=["SSRF", "Gopher", "Impact escalation"], badge="web", repo=NEXTHUNT_REPO + "gofrita"),
    dict(kind="ctf", group="NEXTHUNT 2025", src="nexthunt/web-daveloper.md", slug="web-daveloper", title="web daveloper",
         summary="A WebDAV endpoint that only allows GET: method override, PROPFIND enumeration and a final header bypass.",
         tags=["WebDAV", "Method override", "Access control"], badge="web", repo=NEXTHUNT_REPO + "web_daveloper"),
    # ---- CTF authored: NEXTRACE 2025 (one combined writeup) ----
    dict(kind="ctf", group="NEXTRACE 2025", src="nextrace/nextrace-2025.md", slug="nextrace-2025",
         title="NEXTRACE 2025: six web challenges",
         summary="All six beginner challenges in one writeup: DevTools, response manipulation, headers, HPP and a web-cache PURGE bypass.",
         tags=["Response manipulation", "HPP", "Web cache", "Headers"], badge="6 challenges",
         repo="https://github.com/0xsila/nexus-nextrace-2025-challenges"),
]

GIPHY = re.compile(r"giphy", re.I)


def clean_markdown(text: str, slug: str) -> str:
    """Drop the first H1, giphy embeds and their captions; fix image paths."""
    lines = text.splitlines()
    # drop first H1
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            del lines[i]
            break
    out, skip_caption = [], False
    for ln in lines:
        if GIPHY.search(ln):
            skip_caption = True
            continue
        if skip_caption:
            if ln.strip().startswith("<p><em>") or not ln.strip():
                if ln.strip():
                    skip_caption = False
                continue
            skip_caption = False
        out.append(ln)
    text = "\n".join(out)
    # raw payload lines like <iframe src="gopher://..."> must be shown, not rendered
    text = re.sub(r"^[ \t]*(<iframe[^\n]*)$", lambda m: "```html\n" + m.group(1).strip() + "\n```", text, flags=re.M)
    text = re.sub(r"!\[([^\]]*)\]\((image[^)]*\.png)\)", rf"![\1](../assets/writeups/{slug}/\2)", text)
    # CTF writeups use "## Challenge Name" blocks: keep them, they are the originals.
    return text.strip() + "\n"


MD = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br", "sane_lists"])


def render(text: str) -> str:
    MD.reset()
    return MD.convert(text)


NAV = """<header class="nav"><div class="wrap nav-in">
  <a class="brand" href="{r}index.html"><span class="brand-dot"></span>0xsila</a>
  <nav><a href="{r}index.html#certs">Certs</a><a href="{r}index.html#experience">Experience</a><a href="{r}index.html#writeups">Writeups</a><a href="{r}index.html#contact">Contact</a></nav>
</div></header>"""


def page(w, body_html, prev_w, next_w):
    tags = "".join(f"<span class='tag'>{html.escape(t)}</span>" for t in w["tags"])
    repo = (f"<a class='btn ghost' href='{w['repo']}' target='_blank' rel='noopener'>Challenge source &rarr;</a>"
            if w.get("repo") else "")
    h1 = (f"<a class='btn ghost' href='https://hackerone.com/0xsila' target='_blank' rel='noopener'>HackerOne profile &rarr;</a>"
          if w["kind"] == "bounty" else "")

    def nav(x, label):
        if not x:
            return "<span></span>"
        return f"<a class='pn' href='{x['slug']}.html'><small>{label}</small><b>{html.escape(x['title'])}</b></a>"

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(w['title'])} · 0xsila</title>
<meta name="description" content="{html.escape(w['summary'])}">
<meta name="theme-color" content="#0a0a0c">
<link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/css/style.css">
</head><body class="post-page">
<div class="glow" aria-hidden="true"></div>
{NAV.format(r='../')}
<main class="wrap post">
  <a class="back" href="../index.html#writeups">&larr; All writeups</a>
  <p class="eyebrow">{html.escape(w['group'])}</p>
  <h1>{html.escape(w['title'])}</h1>
  <p class="lede">{html.escape(w['summary'])}</p>
  <div class="tags">{tags}</div>
  <article class="prose">{body_html}</article>
  <div class="post-cta">{repo}{h1}<a class="btn ghost" href="../index.html#contact">Get in touch</a></div>
  <div class="pn-row">{nav(prev_w, 'Previous')}{nav(next_w, 'Next')}</div>
</main>
<footer class="foot"><div class="wrap"><span>&copy; 2026 Sila Yahia · 0xsila</span><span>Hunt responsibly.</span></div></footer>
</body></html>
"""


def card(w):
    tags = "".join(f"<span class='tag'>{html.escape(t)}</span>" for t in w["tags"][:3])
    return f"""<a class="wu" data-kind="{w['kind']}" data-group="{html.escape(w['group'])}" href="writeups/{w['slug']}.html">
  <div class="wu-top"><span class="wu-group">{html.escape(w['group'])}</span><span class="wu-badge">{html.escape(w['badge'])}</span></div>
  <h3>{html.escape(w['title'])}</h3>
  <p>{html.escape(w['summary'])}</p>
  <div class="tags">{tags}</div>
  <span class="wu-go">Read writeup <i>&rarr;</i></span>
</a>"""


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.html"):
        old.unlink()
    shutil.rmtree(ROOT / "assets" / "writeups", ignore_errors=True)

    for i, w in enumerate(WRITEUPS):
        md_path = SRC / w["src"]
        text = clean_markdown(md_path.read_text(encoding="utf-8"), w["slug"])
        # copy referenced images
        for img in re.findall(r"\(\.\./assets/writeups/[^/]+/([^)]+)\)", text):
            dst = ROOT / "assets" / "writeups" / w["slug"]
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy(md_path.parent / img, dst / img)
        prev_w = WRITEUPS[i - 1] if i > 0 else None
        next_w = WRITEUPS[i + 1] if i < len(WRITEUPS) - 1 else None
        (OUT / f"{w['slug']}.html").write_text(page(w, render(text), prev_w, next_w), encoding="utf-8")

    cards = "\n".join(card(w) for w in WRITEUPS)
    tpl = (ROOT / "tools" / "index.template.html").read_text(encoding="utf-8")
    n_b = sum(1 for w in WRITEUPS if w["kind"] == "bounty")
    n_c = len(WRITEUPS) - n_b
    tpl = (tpl.replace("{{WRITEUPS}}", cards)
              .replace("{{N_ALL}}", str(len(WRITEUPS)))
              .replace("{{N_BOUNTY}}", str(n_b))
              .replace("{{N_CTF}}", str(n_c)))
    (ROOT / "index.html").write_text(tpl, encoding="utf-8")
    print(f"built {len(WRITEUPS)} writeups + index.html")


if __name__ == "__main__":
    main()
