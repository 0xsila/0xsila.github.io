#!/usr/bin/env python3
"""Turn a HackerOne reports export into a sanitized data/reports.json for the site.

Usage: python3 tools/reports_data.py path/to/reports_readable.json
The raw export is NOT committed. The output has no report ids, no company or
product names, only neutral labels, severity, state, dates and program type.
Bounty amounts live in data/bounties.json (slug -> amount in USD), filled by hand.
"""
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOUNTY_PROGRAM = "73499"  # the paid private program; everything else is a VDP

# writeup slug -> list of (episode, label, [report ids], slug_key)
MAP = {
    "idor-series": [
        ("Episode 1", "Edit any user's profile: name, bio, image, title, company, industry, address, website, language, communications", "profile",
         ["2978368", "2978587", "2978609", "2978639", "2978647", "2978652", "2978662", "2978666", "2981199", "2981206"]),
        ("Episode 2", "Delete a plan", "plan-delete", ["3062087"]),
        ("Episode 2", "Edit a plan", "plan-edit", ["3062096"]),
        ("Episode 2", "Archive a plan", "plan-archive", ["3063110"]),
        ("Episode 2", "Unarchive a plan", "plan-unarchive", ["3063439"]),
        ("Episode 2", "Rename a plan", "plan-rename", ["3064062"]),
        ("Episode 2", "Leak the transfer-ownership email", "plan-transfer-email", ["3064100"]),
        ("Episode 2", "Cancel a transfer-ownership request", "plan-transfer-cancel", ["3064108"]),
        ("Episode 2", "Edit or delete notes", "plan-notes", ["3062052"]),
        ("Episode 2", "Share the assessment of any project", "plan-share", ["3145382"]),
        ("Episode 2", "Plan IDOR variants rejected or duplicated", "plan-other", ["3061954", "3062035", "3111190"]),
        ("Episode 3", "Delete comments of any file", "comments-delete", ["3357014"]),
        ("Episode 3", "Same bug, duplicate", "comments-delete-dup", ["3358297"]),
        ("Episode 4", "Create a version in someone else's file (empty hubId)", "hubid", ["3402819"]),
        ("Episode 4", "Same empty hubId trick, duplicate", "hubid-dup", ["3402833"]),
        ("Episode 4", "Change a version description through history", "version-description", ["3401483"]),
    ],
    "mass-assignment": [
        ("Bug #1", "Hide the project creator (Owner field)", "owner-hidden", ["3355871"]),
        ("Bug #2", "Backdate comments with a forged timestamp", "comment-timestamp", ["3380870"]),
        ("Bug #3", "Backdate wiki pages with forged timestamps", "wiki-timestamp", ["3381422"]),
        ("Bonus", "Client-chosen id breaks later deletes", "id-sequence", ["3205306"]),
    ],
    "response-manipulation": [
        ("Episode 1", "Password-protected share link bypass", "share-password", ["3357124"]),
        ("Episode 2", "Same wall, different door (second product)", "share-password-2", ["3401518"]),
        ("Episode 3", "Locked feature flips to unlocked (hasAccess)", "has-access", ["3360515"]),
        ("Episode 4", "OTP bypass when changing an email", "otp-email", ["2994567"]),
        ("Episode 4", "OTP bypass when verifying a phone number", "otp-phone", ["3072716"]),
        ("Episode 4", "Email/OTP verification bypass at signup", "otp-signup", ["3965487"]),
    ],
    "business-logic": [
        ("Episode 1", "Trial that never ends: product access kept after expiry (7 products)", "trial",
         ["3074661", "3074694", "3137570", "3139396", "3167444", "3181617", "3260681"]),
        ("Episode 1", "Trial variant through GraphQL", "trial-graphql", ["3387605"]),
        ("Episode 2", "Premium-only feature enabled on a lower plan", "premium-toggle", ["4098468"]),
        ("Episode 3", "Race condition passes the 15-member cap", "member-cap", ["3310436"]),
        ("Episode 3", "Member cap race, second report", "member-cap-2", ["3578934"]),
        ("Episode 4", "Race condition creates multiple workspaces on one account", "multi-hub", ["3355951"]),
    ],
}


# bounty reports that are not part of a published writeup yet: id -> (key, neutral label)
OTHER = {
    "3293154": ("role-downgrade", "Manager can downgrade admins (broken access control)"),
    "3369943": ("viewer-create", "Viewers can create items in projects (broken access control)"),
    "3371257": ("file-modify", "Unauthorized modification of files (broken access control)"),
    "3557305": ("legacy-api", "Legacy project API bypasses access control"),
    "3579810": ("badge-notification", "Persistent notification injection via invalid badge assignment"),
}


def d(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def day(x):
    return x.date().isoformat() if x else None


def days(a, b):
    return None if not (a and b) else max(0, (b - a).days)


def row(r):
    a = r["attributes"]
    sev = (r["relationships"].get("severity") or {}).get("data")
    prog = r["relationships"]["program"]["data"]["id"]
    sub, tri, clo, bnt = d(a["submitted_at"]), d(a["triaged_at"]), d(a["closed_at"]), d(a["bounty_awarded_at"])
    first = d(a["first_program_activity_at"])
    state = a["state"]
    # HackerOne can re-triage later; keep triage only when it is consistent with the timeline
    if tri and ((bnt and tri > bnt) or (clo and state == "resolved" and tri > clo)):
        tri = None
    return dict(
        state=state, program="bounty" if prog == BOUNTY_PROGRAM else "vdp",
        severity=(sev or {}).get("attributes", {}).get("rating") if sev else None,
        reported=day(sub), first_response=day(first), triaged=day(tri),
        resolved=day(clo) if state == "resolved" else None,
        closed=day(clo), bounty=day(bnt),
        d_first=days(sub, first), d_triage=days(sub, tri),
        d_resolve=days(sub, clo) if state == "resolved" else None,
        d_bounty=days(sub, bnt),
    )


def main(path):
    raw = json.load(open(path, encoding="utf-8"))["data"]
    byid = {r["id"]: r for r in raw}
    rows = [row(r) for r in raw]

    # global stats
    st = {}
    st["total"] = len(rows)
    st["by_state"] = {k: sum(1 for x in rows if x["state"] == k) for k in sorted({x["state"] for x in rows})}
    st["bounty_reports"] = sum(1 for x in rows if x["program"] == "bounty")
    st["vdp_reports"] = sum(1 for x in rows if x["program"] == "vdp")
    st["bounties_awarded"] = sum(1 for x in rows if x["bounty"])
    st["vdp_resolved"] = sum(1 for x in rows if x["program"] == "vdp" and x["state"] == "resolved")
    st["bounty_resolved"] = sum(1 for x in rows if x["program"] == "bounty" and x["state"] == "resolved")
    st["triaged_or_resolved"] = sum(1 for x in rows if x["state"] in ("triaged", "resolved"))
    ft = [x["d_first"] for x in rows if x["d_first"] is not None]
    tr = [x["d_triage"] for x in rows if x["d_triage"] is not None]
    rs = [x["d_resolve"] for x in rows if x["d_resolve"] is not None]
    bt = [x["d_bounty"] for x in rows if x["d_bounty"] is not None]
    med = lambda l: int(statistics.median(l)) if l else None
    st["median_days_first_response"] = med(ft)
    st["median_days_triage"] = med(tr)
    st["median_days_resolve"] = med(rs)
    st["median_days_bounty"] = med(bt)
    st["first_report"] = min(x["reported"] for x in rows)
    st["last_report"] = max(x["reported"] for x in rows)
    bm = {}
    for x in rows:
        bm[x["reported"][:7]] = bm.get(x["reported"][:7], 0) + 1
    st["by_month"] = dict(sorted(bm.items()))
    st["severity"] = {k: sum(1 for x in rows if x["severity"] == k) for k in ("critical", "high", "medium", "low")}

    out = {"stats": st, "writeups": {}}
    used = set()
    for slug, groups in MAP.items():
        items = []
        for ep, label, key, ids in groups:
            rs_ = [row(byid[i]) for i in ids]
            used.update(ids)
            items.append(dict(episode=ep, label=label, key=key, count=len(rs_), reports=rs_))
        out["writeups"][slug] = items
    out["unmapped"] = len(raw) - len(used)
    # bounty ledger: every bounty-awarded report with a neutral label
    labels = {}
    for slug, groups in MAP.items():
        for ep, label, key, ids in groups:
            for i in ids:
                labels[i] = (key, label, slug)
    ledger = []
    for r in raw:
        i = r["id"]
        if not r["attributes"]["bounty_awarded_at"]:
            continue
        key, label, slug = labels[i] if i in labels else (*OTHER[i], None)
        ledger.append(dict(key=key, label=label, writeup=slug, **row(r)))
    ledger.sort(key=lambda x: x["bounty"])
    out["ledger"] = ledger
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "reports.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    bf = ROOT / "data" / "bounties.json"
    if not bf.exists():
        bf.write_text("{}\n", encoding="utf-8")
    print(json.dumps(st, indent=1))
    print("mapped", len(used), "unmapped", out["unmapped"])


if __name__ == "__main__":
    main(sys.argv[1])
