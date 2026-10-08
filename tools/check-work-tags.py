#!/usr/bin/env python3
"""Keeps the /work/ filter tags in line with the case study proof bank.

Every client and side-project card on work/index.html carries a
data-service list that drives the service filters (GTM Engineering &
Automation, Paid Acquisition, and so on). Those tags come from the proof
bank, not from memory: each proof bank entry that links a
jamespraise.xyz/work/[slug]/ page has a "**Capability tags:**" line, and the
"jamespraise.xyz Work Filters" table in the proof bank maps capability tags
to site filters. This script derives each card's filters from that and
checks:

  1. every client/side card has a proof bank entry linking its slug
  2. the card's data-service equals the filters derived from that entry
  3. the filter chips on the case study page itself (where the page has
     them) match the card
  4. every filter key in use exists as a filter button, and the map table
     covers every filter button

Blueprint (microsite) cards are skipped; they only show under Blueprints.

Usage:
  python3 tools/check-work-tags.py          # report, exit 1 on any problem
  python3 tools/check-work-tags.py --fix    # rewrite card data-service from the proof bank

When the proof bank is not on this machine, only checks 3 and 4 run.
Override its location with PROOF_BANK=/path/to/case-study-proof-bank.md.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "work", "index.html")
PROOF_BANK = os.environ.get("PROOF_BANK") or os.path.expanduser(
    "~/.claude/skills/career-outreach/references/case-study-proof-bank.md")
MAP_HEADING = "## jamespraise.xyz Work Filters"

CARD_RE = re.compile(
    r'(<a class="case-study-card-v2[^"]*" data-tags="([^"]*)")'
    r'(?: data-service="([^"]*)")?( href="/work/([^/"]+)/")')


def norm(tag):
    tag = re.sub(r"\([^)]*\)", "", tag)
    return re.sub(r"[^a-z0-9]", "", tag.lower())


def filter_buttons(index_html):
    return re.findall(r'data-filter-dim="service" data-filter="([a-z-]+)"', index_html)


def load_proof_bank():
    if not os.path.exists(PROOF_BANK):
        return None, None
    text = open(PROOF_BANK, encoding="utf-8").read()
    if MAP_HEADING not in text:
        sys.exit(f"Proof bank has no '{MAP_HEADING}' table: {PROOF_BANK}")
    section = text.split(MAP_HEADING, 1)[1].split("\n## ", 1)[0]
    tag_to_filters = {}
    for row in section.splitlines():
        m = re.match(r"\|\s*`([a-z-]+)`\s*\|[^|]*\|([^|]*)\|", row)
        if not m:
            continue
        for tag in m.group(2).split(","):
            if tag.strip():
                tag_to_filters.setdefault(norm(tag), set()).add(m.group(1))

    slug_tags = {}
    for entry in re.split(r"\n(?=### )", text):
        if not entry.startswith("### "):
            continue
        tags_line = re.search(r"\*\*Capability tags:\*\*(.*)", entry)
        slugs = set(re.findall(r"jamespraise\.xyz/work/([a-z0-9-]+)/(?!proof)", entry))
        for slug in slugs:
            entry_tags = slug_tags.setdefault(slug, set())
            if tags_line:
                entry_tags.update(t.strip().rstrip(".") for t in tags_line.group(1).split(",") if t.strip())
    return tag_to_filters, slug_tags


def derive(tags, tag_to_filters, order):
    out = set()
    for tag in tags:
        out |= tag_to_filters.get(norm(tag), set())
    return [f for f in order if f in out]


def page_chips(slug):
    path = os.path.join(ROOT, "work", slug, "index.html")
    if not os.path.exists(path):
        return None
    return re.findall(r'href="/work/#filter=([a-z-]+)"', open(path, encoding="utf-8").read())


def main():
    fix = "--fix" in sys.argv
    index_html = open(INDEX, encoding="utf-8").read()
    order = filter_buttons(index_html)
    tag_to_filters, slug_tags = load_proof_bank()
    problems, notes = [], []

    if tag_to_filters is not None:
        mapped = set().union(*tag_to_filters.values()) if tag_to_filters else set()
        for key in set(order) - mapped:
            problems.append(f"filter button '{key}' has no row in the proof bank map table")
        for key in mapped - set(order):
            problems.append(f"proof bank map uses '{key}', which is not a filter button on /work/")
    else:
        notes.append(f"proof bank not found at {PROOF_BANK}; ran the site-only checks")

    def fix_card(m):
        prefix, types, service, href, slug = m.groups()
        if "microsite" in types.split():
            return m.group(0)
        current = (service or "").split()
        for key in current:
            if key not in order:
                problems.append(f"{slug}: card uses unknown filter '{key}'")
        target = None
        if slug_tags is not None:
            if slug not in slug_tags:
                problems.append(f"{slug}: no proof bank entry links jamespraise.xyz/work/{slug}/")
            else:
                target = derive(slug_tags[slug], tag_to_filters, order)
                if set(target) != set(current):
                    missing = [f for f in target if f not in current]
                    extra = [f for f in current if f not in target]
                    msg = f"{slug}: card filters differ from proof bank"
                    if missing:
                        msg += f"; add {', '.join(missing)}"
                    if extra:
                        msg += f"; remove {', '.join(extra)} (or add the capability tag to the proof bank entry)"
                    if fix:
                        notes.append(f"{slug}: set filters to [{' '.join(target)}]")
                    else:
                        problems.append(msg)
        final = target if (fix and target is not None) else current
        chips = page_chips(slug)
        if chips is None:
            problems.append(f"{slug}: card links /work/{slug}/ but the page does not exist")
        elif chips and set(chips) != set(final):
            problems.append(f"{slug}: page filter chips [{' '.join(chips)}] differ from card [{' '.join(final)}]")
        if fix and target is not None:
            attr = f' data-service="{" ".join(target)}"' if target else ""
            return f"{prefix}{attr}{href}"
        return m.group(0)

    new_html = CARD_RE.sub(fix_card, index_html)
    if fix and new_html != index_html:
        open(INDEX, "w", encoding="utf-8").write(new_html)

    for n in notes:
        print(f"note: {n}")
    if problems:
        print("Work filter tags are out of sync with the proof bank:")
        for p in problems:
            print(f"  - {p}")
        print("Fix the proof bank entry's Capability tags line (or the map table), then run "
              "python3 tools/check-work-tags.py --fix. Page chips are edited by hand.")
        sys.exit(1)
    print("work filter tags OK")


if __name__ == "__main__":
    main()
