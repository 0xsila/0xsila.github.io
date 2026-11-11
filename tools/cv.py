#!/usr/bin/env python3
"""Generate ATS-friendly CVs: assets/CV_Sila_Yahia_EN.pdf and _FR.pdf.

Single column, plain text, black on white, standard section headings, no icons,
no tables, no images. Run from the repo root:  python3 tools/cv.py
"""
import html
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

T = {
    "en": dict(
        lang="en", title="Junior Penetration Tester | Computer Science Student (L3)",
        seek="Seeking a 3-month internship starting April 2027 in cybersecurity, networks or systems.",
        h=dict(sum="SUMMARY", exp="EXPERIENCE", edu="EDUCATION", cert="CERTIFICATIONS", skills="SKILLS", lang="LANGUAGES", proj="CTF AUTHORING AND COMPETITIONS"),
        summary=("Third-year Computer Science student at Université de Lille, focused on penetration testing and vulnerability research. "
                 "eJPT and CRTA certified. Active bug bounty hunter on HackerOne: 93 reports submitted, 25 resolved, 15 bounties awarded, 500+ reputation points. "
                 "Publishes technical writeups at 0xsila.github.io."),
        exp=[("Bug Bounty Hunter", "Independent (HackerOne)", "Dec 2024 - Present",
              ["Submitted 93 vulnerability reports to bug bounty and vulnerability disclosure programs; 25 resolved, 15 rewarded with bounties.",
               "Tested web applications and APIs: reconnaissance, endpoint discovery, broken access control (IDOR), mass assignment, response manipulation, OTP bypass and business logic flaws.",
               "Wrote public writeups on resolved findings and on CTF challenges (0xsila.github.io)."]),
             ("Technical Manager", "Nexus Security Club", "Sep 2025 - Present",
              ["Organised cybersecurity events and CTF competitions.",
               "Deployed challenges and set up the technical infrastructure.",
               "Ran workshops and training sessions on cybersecurity and web security."])],
        edu=[("Université de Lille", "Bachelor's degree in Computer Science (Licence Informatique, L3)", "2026 - Present"),
             ("ESTIN, Higher School of Computer Science and Technology", "Computer Science studies", "2023 - 2026")],
        cert=[("eJPT, eLearnSecurity Junior Penetration Tester", "INE Security, June 2026. Network and web penetration testing."),
              ("CRTA, Certified Red Team Analyst", "CyberWarfare Labs, 2026.")],
        skills=[("Security", "Web application penetration testing, network penetration testing, API security, OWASP Top 10, reconnaissance, vulnerability assessment, responsible disclosure"),
                ("Tools", "Burp Suite, Nmap, Wireshark, Metasploit"),
                ("Networks", "TCP/IP, Cisco, network administration and security"),
                ("Systems", "Linux, Windows"),
                ("Scripting", "Python, Bash")],
        langs="Arabic (native), Kabyle (native), French (B2), English (B2)",
        proj=["CTF challenge author: NEXZERO (2026), NEXTHUNT (2025, 4 web challenges), NEXTRACE (2025, 6 web challenges).",
              "Hackini 2.0 (2026): 2nd place.",
              "Active on Hack The Box and TryHackMe."],
    ),
    "fr": dict(
        lang="fr", title="Pentester junior | Étudiant en Licence Informatique (L3)",
        seek="Recherche un stage de 3 mois à partir d'avril 2027 en cybersécurité, réseaux ou systèmes.",
        h=dict(sum="PROFIL", exp="EXPÉRIENCE", edu="FORMATION", cert="CERTIFICATIONS", skills="COMPÉTENCES", lang="LANGUES", proj="CHALLENGES CTF ET COMPÉTITIONS"),
        summary=("Étudiant en 3e année de Licence Informatique à l'Université de Lille, spécialisé en tests d'intrusion et recherche de vulnérabilités. "
                 "Certifié eJPT et CRTA. Chasseur de bugs actif sur HackerOne : 93 rapports soumis, 25 résolus, 15 primes obtenues, 500+ points de réputation. "
                 "Publie des writeups techniques sur 0xsila.github.io."),
        exp=[("Bug Bounty Hunter", "Indépendant (HackerOne)", "Déc. 2024 - Présent",
              ["93 rapports de vulnérabilités soumis à des programmes de bug bounty et de divulgation de vulnérabilités ; 25 résolus, 15 récompensés par une prime.",
               "Tests d'applications web et d'API : reconnaissance, découverte d'endpoints, contrôle d'accès (IDOR), mass assignment, manipulation de réponses, contournement d'OTP et failles de logique métier.",
               "Rédaction de writeups publics sur des failles résolues et sur des challenges CTF (0xsila.github.io)."]),
             ("Manager technique", "Nexus Security Club", "Sep. 2025 - Présent",
              ["Organisation d'événements de cybersécurité et de compétitions CTF.",
               "Déploiement des challenges et mise en place de l'infrastructure technique.",
               "Animation d'ateliers et de formations en cybersécurité et sécurité web."])],
        edu=[("Université de Lille", "Licence Informatique (L3)", "2026 - Présent"),
             ("ESTIN, École supérieure en Sciences et Technologies de l'Informatique", "Études en informatique", "2023 - 2026")],
        cert=[("eJPT, eLearnSecurity Junior Penetration Tester", "INE Security, juin 2026. Tests d'intrusion réseau et web."),
              ("CRTA, Certified Red Team Analyst", "CyberWarfare Labs, 2026.")],
        skills=[("Sécurité", "Tests d'intrusion web, tests d'intrusion réseau, sécurité des API, OWASP Top 10, reconnaissance, évaluation de vulnérabilités, divulgation responsable"),
                ("Outils", "Burp Suite, Nmap, Wireshark, Metasploit"),
                ("Réseaux", "TCP/IP, Cisco, administration et sécurité réseau"),
                ("Systèmes", "Linux, Windows"),
                ("Scripting", "Python, Bash")],
        langs="Arabe (langue maternelle), Kabyle (langue maternelle), Français (B2), Anglais (B2)",
        proj=["Auteur de challenges CTF : NEXZERO (2026), NEXTHUNT (2025, 4 challenges web), NEXTRACE (2025, 6 challenges web).",
              "Hackini 2.0 (2026) : 2e place.",
              "Actif sur Hack The Box et TryHackMe."],
    ),
}

CSS = """
@page{size:A4;margin:11mm 15mm}
*{margin:0;padding:0;box-sizing:border-box}
body{font:9.5pt/1.3 Arial,Helvetica,sans-serif;color:#000;background:#fff}
h1{font-size:20pt;font-weight:700;margin-bottom:1mm}
.t{font-size:11pt;font-weight:700}
.c{margin-top:1.5mm}
h2{font-size:10pt;font-weight:700;margin:3mm 0 1mm;padding-bottom:.6mm;border-bottom:1px solid #000}
.j{margin-top:1.4mm;font-weight:700}
ul{list-style:none;margin:.4mm 0 0 0}
li{margin-top:.4mm;padding-left:4mm;text-indent:-4mm}
li::before{content:"• "}
p{margin-top:.6mm}
"""


def cv_html(d):
    e = html.escape
    exp = "".join(f"<p class='j'>{e(t)}, {e(o)} | {e(dt)}</p><ul>{''.join(f'<li>{e(b)}</li>' for b in bl)}</ul>" for t, o, dt, bl in d["exp"])
    edu = "".join(f"<p class='j'>{e(s)} | {e(y)}</p><p>{e(deg)}</p>" for s, deg, y in d["edu"])
    cert = "".join(f"<p class='j'>{e(n)}</p><p>{e(x)}</p>" for n, x in d["cert"])
    skills = "".join(f"<p><b>{e(k)}:</b> {e(v)}</p>" for k, v in d["skills"])
    proj = "<ul>" + "".join(f"<li>{e(x)}</li>" for x in d["proj"]) + "</ul>"
    h = d["h"]
    return f"""<!doctype html><html lang="{d['lang']}"><head><meta charset="utf-8"><title>Sila Yahia - CV</title><style>{CSS}</style></head><body>
<h1>Sila Yahia</h1>
<div class="t">{e(d['title'])}</div>
<div class="c">Lille, France | 07 59 14 81 41 | silayahia7@gmail.com</div>
<div class="c">LinkedIn: linkedin.com/in/0xsila | GitHub: github.com/0xsila | HackerOne: hackerone.com/0xsila | TryHackMe: tryhackme.com/p/0xsila | Portfolio: 0xsila.github.io</div>
<p class="c">{e(d['seek'])}</p>
<h2>{h['sum']}</h2><p>{e(d['summary'])}</p>
<h2>{h['exp']}</h2>{exp}
<h2>{h['edu']}</h2>{edu}
<h2>{h['cert']}</h2>{cert}
<h2>{h['skills']}</h2>{skills}
<h2>{h['proj']}</h2>{proj}
<h2>{h['lang']}</h2><p>{e(d['langs'])}</p>
</body></html>"""


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        for code, d in T.items():
            pg = b.new_page()
            pg.set_content(cv_html(d))
            out = ROOT / "assets" / f"CV_Sila_Yahia_{code.upper()}.pdf"
            pg.pdf(path=str(out), format="A4", print_background=False, prefer_css_page_size=True)
            print("wrote", out)
        b.close()


if __name__ == "__main__":
    main()
