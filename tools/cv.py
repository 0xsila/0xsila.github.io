#!/usr/bin/env python3
"""Generate assets/CV_Sila_Yahia_FR.pdf and _EN.pdf (A4, one page) with Playwright/Chromium.

Run from the repo root:  python3 tools/cv.py
"""
import html
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

LINKS = [
    ("linkedin.com/in/0xsila", "https://www.linkedin.com/in/0xsila"),
    ("github.com/0xsila", "https://github.com/0xsila"),
    ("hackerone.com/0xsila", "https://hackerone.com/0xsila"),
    ("tryhackme.com/p/0xsila", "https://tryhackme.com/p/0xsila"),
    ("0xsila.github.io", "https://0xsila.github.io"),
]

T = {
    "fr": dict(
        lang="fr",
        role="Pentester junior · Étudiant L3 Informatique",
        seek="Recherche de stage · 3 mois à partir d'avril 2027 · Cybersécurité, Réseaux, Systèmes",
        loc="Lille, France",
        h_profile="Profil",
        profile=("Étudiant en 3<sup>e</sup> année de Licence Informatique à l'Université de Lille, spécialisé en tests "
                 "d'intrusion et recherche de vulnérabilités. Certifié <b>eJPT</b> et <b>CRTA</b>, chasseur de bugs actif sur "
                 "<b>HackerOne (500+ points de réputation)</b>, 2<sup>e</sup> au Hackini 2.0 et auteur de challenges CTF pour "
                 "trois compétitions. Je publie mes writeups sur 0xsila.github.io."),
        h_cert="Certifications",
        certs=[("eJPT — Junior Penetration Tester", "INE Security", "juin 2026", "Pentest réseau et web, examen pratique"),
               ("CRTA — Certified Red Team Analyst", "CyberWarfare Labs", "2026", "Examen de certification")],
        h_exp="Expérience",
        exp=[("Bug Bounty Hunter", "Indépendant · HackerOne", "Déc. 2024 – Présent",
              ["Plus de 500 points de réputation grâce à la divulgation responsable de vulnérabilités.",
               "Tests de sécurité d'applications web et d'API : reconnaissance, découverte d'endpoints, contrôle d'accès (IDOR), mass assignment, manipulation de réponses, logique métier.",
               "Rédaction de writeups publics sur des failles résolues (4 séries)."]),
             ("Manager technique", "Nexus Security Club", "Sep. 2025 – Présent",
              ["Organisation d'événements cybersécurité et de compétitions CTF.",
               "Déploiement des challenges et mise en place de l'infrastructure technique.",
               "Animation d'ateliers et de sessions de formation en cybersécurité et sécurité web."])],
        h_proj="Compétitions & réalisations",
        proj=[("2<sup>e</sup> place — Hackini 2.0", "2026", ""),
              ("Auteur de challenges CTF — NEXZERO", "2026", ""),
              ("Auteur de challenges CTF — NEXHUNT", "2025", "4 challenges web : 1xbet, Dz-Kitab, gofrita, web daveloper"),
              ("Auteur de challenges CTF — NEXTRACE", "2025", "6 challenges web : HPP, Headers, Passw0rd, cache web, Inspect"),
              ("Joueur actif — Hack The Box, TryHackMe", "", "")],
        h_edu="Formation",
        edu=[("Université de Lille — Licence Informatique (L3)", "2026 – Présent"),
             ("ESTIN — École supérieure en Sciences et Technologies de l'Informatique", "2023 – 2026")],
        h_skills="Compétences techniques",
        skills=[("Offensif", "Pentest web et réseau, OWASP Top 10, sécurité des API, reconnaissance, évaluation de vulnérabilités"),
                ("Outils", "Burp Suite, Nmap, Wireshark, Metasploit"),
                ("Réseaux", "TCP/IP, Cisco, administration et sécurité réseau"),
                ("Systèmes", "Linux, Windows"),
                ("Scripting", "Python, Bash")],
        h_lang="Langues",
        langs=[("Arabe", "Langue maternelle"), ("Kabyle", "Langue maternelle"), ("Français", "B2"), ("Anglais", "B2")],
        h_soft="Savoir-être",
        soft="Travail d'équipe · Pédagogie et communication technique · Rigueur et esprit d'analyse · Autonomie · Apprentissage rapide · Esprit d'initiative",
    ),
    "en": dict(
        lang="en",
        role="Junior Penetration Tester · L3 Computer Science student",
        seek="Seeking a 3-month internship from April 2027 · Cybersecurity, Networks, Systems",
        loc="Lille, France",
        h_profile="Profile",
        profile=("Third-year Computer Science undergraduate (L3) at Université de Lille, specialised in penetration testing "
                 "and vulnerability research. <b>eJPT</b> and <b>CRTA</b> certified, active bug bounty hunter on "
                 "<b>HackerOne (500+ reputation points)</b>, 2<sup>nd</sup> place at Hackini 2.0 and CTF challenge author for "
                 "three competitions. I publish my writeups at 0xsila.github.io."),
        h_cert="Certifications",
        certs=[("eJPT — Junior Penetration Tester", "INE Security", "June 2026", "Network and web pentesting, practical exam"),
               ("CRTA — Certified Red Team Analyst", "CyberWarfare Labs", "2026", "Certification exam")],
        h_exp="Experience",
        exp=[("Bug Bounty Hunter", "Independent · HackerOne", "Dec 2024 – Present",
              ["500+ reputation points earned through responsible vulnerability disclosure.",
               "Web application and API security testing: recon, endpoint discovery, access control (IDOR), mass assignment, response manipulation, business logic.",
               "Publishes public writeups of resolved findings (4 series)."]),
             ("Technical Manager", "Nexus Security Club", "Sep 2025 – Present",
              ["Helps organise cybersecurity events and CTF competitions.",
               "Deploys challenges and sets up the technical infrastructure.",
               "Runs workshops and training sessions on cybersecurity and web security."])],
        h_proj="Competitions & achievements",
        proj=[("2<sup>nd</sup> place — Hackini 2.0", "2026", ""),
              ("CTF challenge author — NEXZERO", "2026", ""),
              ("CTF challenge author — NEXHUNT", "2025", "4 web challenges: 1xbet, Dz-Kitab, gofrita, web daveloper"),
              ("CTF challenge author — NEXTRACE", "2025", "6 web challenges: HPP, Headers, Passw0rd, web cache, Inspect"),
              ("Active player — Hack The Box, TryHackMe", "", "")],
        h_edu="Education",
        edu=[("Université de Lille — Bachelor in Computer Science (L3)", "2026 – Present"),
             ("ESTIN — Higher School of Computer Science and Technology", "2023 – 2026")],
        h_skills="Technical skills",
        skills=[("Offensive", "Web and network pentesting, OWASP Top 10, API security, recon, vulnerability assessment"),
                ("Tools", "Burp Suite, Nmap, Wireshark, Metasploit"),
                ("Networks", "TCP/IP, Cisco, network administration and security"),
                ("Systems", "Linux, Windows"),
                ("Scripting", "Python, Bash")],
        h_lang="Languages",
        langs=[("Arabic", "Native"), ("Kabyle", "Native"), ("French", "B2"), ("English", "B2")],
        h_soft="Soft skills",
        soft="Teamwork · Technical communication and teaching · Rigour and analytical mindset · Autonomy · Fast learner · Initiative",
    ),
}

CSS = """
@page{size:A4;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
body{font:9.6pt/1.38 'Helvetica Neue',Helvetica,Arial,sans-serif;color:#17171c;width:210mm;height:297mm;padding:13mm 15mm 11mm;position:relative}
body::before{content:"";position:absolute;left:0;top:0;bottom:0;width:5mm;background:#ff3d4f}
a{color:inherit;text-decoration:none}
header{border-bottom:1.5px solid #17171c;padding-bottom:3.5mm;margin-bottom:3.5mm}
h1{font-size:27pt;line-height:1;letter-spacing:-.03em;font-weight:800}
h1 span{color:#ff3d4f}
.role{font-size:11pt;font-weight:600;margin-top:2mm}
.seek{font-size:9pt;color:#555;margin-top:.6mm}
.contact{margin-top:2.4mm;font-size:8.4pt;color:#333;display:flex;flex-wrap:wrap;gap:1mm 4mm}
.contact b{color:#ff3d4f;font-weight:700}
h2{font-size:8.6pt;letter-spacing:.14em;text-transform:uppercase;color:#ff3d4f;font-weight:800;margin:3.4mm 0 1.4mm;display:flex;align-items:center;gap:2.5mm}
h2::after{content:"";flex:1;height:.5pt;background:#d6d6dd}
.row{display:flex;justify-content:space-between;gap:4mm;align-items:baseline}
.row b{font-weight:700}
.row i{font-style:normal;color:#666;font-size:8.6pt;white-space:nowrap}
.sub{color:#555}
ul{list-style:none;margin-top:.6mm}
li{padding-left:3.2mm;position:relative;margin-top:.5mm}
li::before{content:"›";position:absolute;left:0;color:#ff3d4f;font-weight:700}
.item+.item{margin-top:2.2mm}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:0 8mm}
.skill{display:grid;grid-template-columns:20mm 1fr;gap:2mm;margin-top:.6mm}
.skill b{font-weight:700}
.langs{display:flex;flex-wrap:wrap;gap:1mm 6mm}
.langs span{color:#555}
.cert .sub{font-size:8.8pt}
"""


def cv_html(d):
    e = html.escape
    links = "".join(f'<a href="{u}"><b>›</b> {e(t)}</a>' for t, u in LINKS)
    certs = "".join(
        f'<div class="item cert"><div class="row"><b>{e(n)}</b><i>{e(dt)}</i></div><div class="sub">{e(org)} · {e(note)}</div></div>'
        for n, org, dt, note in d["certs"])
    exp = "".join(
        f'<div class="item"><div class="row"><b>{e(t)} <span class="sub" style="font-weight:400">— {e(o)}</span></b><i>{e(dt)}</i></div>'
        f'<ul>{"".join(f"<li>{e(x)}</li>" for x in bl)}</ul></div>'
        for t, o, dt, bl in d["exp"])
    proj = "".join(
        f'<li><b>{t}</b>{(" · " + e(y)) if y else ""}{(" — <span class=sub>" + e(n) + "</span>") if n else ""}</li>'
        for t, y, n in d["proj"])
    edu = "".join(f'<div class="row"><b>{e(n)}</b><i>{e(y)}</i></div>' for n, y in d["edu"])
    skills = "".join(f'<div class="skill"><b>{e(k)}</b><span>{e(v)}</span></div>' for k, v in d["skills"])
    langs = "".join(f'<span><b style="color:#17171c">{e(k)}</b> {e(v)}</span>' for k, v in d["langs"])
    return f"""<!doctype html><html lang="{d['lang']}"><head><meta charset="utf-8"><title>Sila Yahia — CV</title><style>{CSS}</style></head><body>
<header>
  <h1>SILA <span>YAHIA</span></h1>
  <div class="role">{e(d['role'])}</div>
  <div class="seek">{e(d['seek'])}</div>
  <div class="contact"><span><b>›</b> {e(d['loc'])}</span><span><b>›</b> 07 59 14 81 41</span><span><b>›</b> silayahia7@gmail.com</span>{links}</div>
</header>
<h2>{e(d['h_profile'])}</h2><p>{d['profile']}</p>
<h2>{e(d['h_cert'])}</h2>{certs}
<h2>{e(d['h_exp'])}</h2>{exp}
<h2>{e(d['h_proj'])}</h2><ul>{proj}</ul>
<h2>{e(d['h_edu'])}</h2>{edu}
<div class="grid"><div><h2>{e(d['h_skills'])}</h2>{skills}</div>
<div><h2>{e(d['h_lang'])}</h2><div class="langs">{langs}</div><h2>{e(d['h_soft'])}</h2><p>{e(d['soft'])}</p></div></div>
</body></html>"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        for code, d in T.items():
            pg = b.new_page()
            pg.set_content(cv_html(d))
            out = ROOT / "assets" / f"CV_Sila_Yahia_{code.upper()}.pdf"
            pg.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True)
            print("wrote", out)
        b.close()


if __name__ == "__main__":
    main()
