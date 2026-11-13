#!/usr/bin/env python3
"""Check that every side project page that explains a running process has a system map.

A side project page is a /work page whose breadcrumb links to /work/#type=side.
It passes when it holds a map injected by the system-map generator
(`<!-- smap:ID -->` markers, see ~/Documents/system-map/) or when it is listed in
NO_MAP below with the reason it has none. Maps are for processes only: a page that
describes a product, a site or a set of offers goes in NO_MAP.

Usage: python3 tools/check-system-maps.py   (exit 1 lists the pages that fail)
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

NO_MAP = {
    "james-website": "describes the site itself, not a running process",
    "marketing-agent-skills": "describes a public skills library",
    "mia-academy": "describes a set of programs and offers",
    "mia-gtm": "describes a set of service offers",
    "mia-newsletter": "describes a publication",
    "mia-website-build": "describes a site build",
    "personal-ai-stack": "describes a set of tools",
}

SIDE = re.compile(r'class="cs-breadcrumb"[^\n]*href="/work/#type=side"')


def main():
    missing, stale = [], []
    for page in sorted(ROOT.glob("work/*/index.html")):
        slug = page.parent.name
        html = page.read_text()
        if not SIDE.search(html):
            continue
        has_map = "<!-- smap:" in html
        if slug in NO_MAP:
            if has_map:
                stale.append(slug)
        elif not has_map:
            missing.append(slug)
    for slug in missing:
        print(f"work/{slug}/: side project with no system map. Build one with "
              f"~/Documents/system-map/sysmap.py --inject, or add the slug to NO_MAP "
              f"in tools/check-system-maps.py with the reason it has no running process.")
    for slug in stale:
        print(f"work/{slug}/: has a map but is listed in NO_MAP. Remove it from NO_MAP.")
    if missing or stale:
        sys.exit(1)
    print("system maps OK")


if __name__ == "__main__":
    main()
