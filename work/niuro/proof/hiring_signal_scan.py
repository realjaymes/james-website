#!/usr/bin/env python3
"""
hiring_signal_scan.py

Reads the public job boards of a seed list of companies (Greenhouse, Ashby and
Lever all expose an unauthenticated JSON feed) and scores each company on how
strongly its open engineering roles signal a hiring problem a talent partner
could solve.

Built for the Niuro GTM Engineer application (2026-11-10) as a working sample
of "spot a hiring signal, build the workflow", and kept here because the same
scan feeds any outbound aimed at companies that are hiring.

Signals per company (engineering roles only):
  open_eng        open engineering roles
  fresh_eng       engineering roles first published in the last FRESH_DAYS days
  stuck_eng       engineering roles open STALE_DAYS to EVERGREEN_DAYS days (a
                  real requisition that has not filled, the strongest pain signal)
  evergreen_eng   engineering roles open longer than EVERGREEN_DAYS days. These
                  are standing pipeline posts, not unfilled roles, so they score
                  nothing. The first version counted them as stale and ranked
                  Linear (a 2,022-day-old posting) as a company in pain.
  ai_backend      roles in the stack a nearshore engineering partner places
                  most often (AI, ML, backend, platform, data, infrastructure)
  remote_eng      engineering roles marked remote
  score           2*stuck + 1*fresh (each capped at 8) + 4*AI/backend share
                  + 2*remote share
  tier            1 = 5 to 40 open engineering roles with at least 2 stuck: big
                  enough to need outside help, small enough not to run a large
                  recruiting team. 2 = more than 40 open: in-house recruiting
                  exists, so the pitch is overflow capacity. 3 = everything else.

A board that answers with zero roles is logged as a failure, because it
usually means the company moved to another ATS, not that it stopped hiring.

Dates: Ashby gives publishedAt and Lever gives createdAt, both true first-post
dates. Greenhouse's public feed gives first_published on most boards and only
updated_at on some; when first_published is missing the role is counted as
open but never as fresh or stale, because updated_at moves whenever a recruiter
edits the post.

Usage:
  python3 hiring_signal_scan.py --seeds seeds.txt --out scan.json [--md scan.md]
  seeds.txt: one "ats:slug:Company Name" per line, e.g. "ashby:linear:Linear"

Standard library only. One request at a time with a short pause, so it never
hammers a board.
"""
import argparse, datetime as dt, json, re, sys, time, urllib.request, urllib.error

FRESH_DAYS = 21
STALE_DAYS = 60
EVERGREEN_DAYS = 365
UA = "hiring-signal-scan/1.0 (public job board reader)"

ENG = re.compile(r"\b(engineer|engineering|developer|sre|devops|architect|scientist|ml|machine learning|data|backend|back-end|frontend|front-end|full[- ]?stack|platform|infrastructure|security engineer|mobile|ios|android)\b", re.I)
NOT_ENG = re.compile(r"\b(sales|solutions engineer|solutions architect|customer|support|recruit|account|marketing|designer|product manager|program manager|gtm|go-to-market|forward deployed|deployment engineer|developer relations|devrel|head of|director)\b", re.I)
AI_BACKEND = re.compile(r"\b(ai|ml|machine learning|llm|backend|back-end|platform|infrastructure|infra|data|distributed|systems|python|go|rust)\b", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # network, bad JSON
        return None, type(e).__name__


def parse_date(s):
    if not s:
        return None
    if isinstance(s, (int, float)):  # Lever: epoch ms
        return dt.datetime.fromtimestamp(s / 1000, dt.timezone.utc)
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch(ats, slug):
    """Return (list of {title, posted, remote, location}, error)."""
    if ats == "greenhouse":
        data, err = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        if err:
            return None, err
        jobs = []
        for j in data.get("jobs", []):
            loc = (j.get("location") or {}).get("name", "")
            jobs.append({"title": j.get("title", ""), "posted": parse_date(j.get("first_published")),
                         "remote": "remote" in loc.lower(), "location": loc})
        return jobs, None
    if ats == "ashby":
        data, err = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        if err:
            return None, err
        jobs = []
        for j in data.get("jobs", []):
            if j.get("isListed") is False:
                continue
            jobs.append({"title": j.get("title", ""), "posted": parse_date(j.get("publishedAt")),
                         "remote": bool(j.get("isRemote")), "location": j.get("location", "")})
        return jobs, None
    if ats == "lever":
        data, err = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        if err:
            return None, err
        jobs = []
        for j in data if isinstance(data, list) else []:
            cat = j.get("categories") or {}
            loc = cat.get("location", "") or ""
            jobs.append({"title": j.get("text", ""), "posted": parse_date(j.get("createdAt")),
                         "remote": "remote" in loc.lower() or j.get("workplaceType") == "remote", "location": loc})
        return jobs, None
    return None, f"unknown ATS {ats}"


def score_company(jobs, now):
    eng = [j for j in jobs if ENG.search(j["title"]) and not NOT_ENG.search(j["title"])]
    dated = [j for j in eng if j["posted"]]

    def age(j):
        return (now - j["posted"]).days

    fresh = [j for j in dated if age(j) <= FRESH_DAYS]
    stuck = [j for j in dated if STALE_DAYS < age(j) <= EVERGREEN_DAYS]
    evergreen = [j for j in dated if age(j) > EVERGREEN_DAYS]
    ai_b = [j for j in eng if AI_BACKEND.search(j["title"])]
    remote = [j for j in eng if j["remote"]]
    n = len(eng) or 1
    score = 0.0
    if eng:
        score = round(2 * min(len(stuck), 8) + min(len(fresh), 8) + 4 * len(ai_b) / n + 2 * len(remote) / n, 1)
    if 5 <= len(eng) <= 40 and len(stuck) >= 2:
        tier = 1
    elif len(eng) > 40:
        tier = 2
    else:
        tier = 3
    example = sorted(stuck, key=lambda j: j["posted"])[:1]
    return {
        "open_total": len(jobs), "open_eng": len(eng), "dated_eng": len(dated),
        "fresh_eng": len(fresh), "stuck_eng": len(stuck), "evergreen_eng": len(evergreen),
        "ai_backend": len(ai_b), "remote_eng": len(remote), "score": score, "tier": tier,
        "example_role": example[0]["title"].strip() if example else "",
        "example_age_days": age(example[0]) if example else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md")
    ap.add_argument("--pause", type=float, default=0.6)
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    rows, failures = [], []
    for line in open(a.seeds):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ats, slug, name = (line.split(":", 2) + [""])[:3]
        jobs, err = fetch(ats, slug)
        time.sleep(a.pause)
        if not err and not jobs:
            err = "zero roles on the board (likely moved to another ATS)"
        if err:
            failures.append({"company": name or slug, "ats": ats, "slug": slug, "error": err})
            print(f"  FAIL {name or slug:28} {ats}:{slug} {err}", file=sys.stderr)
            continue
        r = {"company": name or slug, "ats": ats, "slug": slug, **score_company(jobs, now)}
        rows.append(r)
        print(f"  ok   {r['company']:28} eng {r['open_eng']:3} fresh {r['fresh_eng']:2} stuck {r['stuck_eng']:2} evergreen {r['evergreen_eng']:2} tier {r['tier']} score {r['score']}", file=sys.stderr)
    rows.sort(key=lambda r: (r["tier"], -r["score"]))
    json.dump({"run_at": now.isoformat(timespec="seconds"), "fresh_days": FRESH_DAYS, "stale_days": STALE_DAYS,
               "evergreen_days": EVERGREEN_DAYS,
               "companies": rows, "failures": failures}, open(a.out, "w"), indent=1)
    if a.md:
        with open(a.md, "w") as f:
            f.write("| Tier | Company | Board | Eng roles open | Posted in 21 days | Stuck 60 to 365 days | Evergreen 365+ | AI or backend | Remote | Score | Oldest stuck role |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
            for r in rows:
                ex = r["example_role"] + (f" ({r['example_age_days']} days)" if r["example_age_days"] is not None else "")
                f.write(f"| {r['tier']} | {r['company']} | {r['ats']} | {r['open_eng']} | {r['fresh_eng']} | {r['stuck_eng']} | {r['evergreen_eng']} | {r['ai_backend']} | {r['remote_eng']} | {r['score']} | {ex} |\n")
    print(f"{len(rows)} companies scored, {len(failures)} boards failed -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
