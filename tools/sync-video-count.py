#!/usr/bin/env python3
"""Keeps the Signal to Build video count on the site equal to the gallery manifest.

The count is the number of entries in work/signal-to-build/videos.json. Every mention on the
site is marked with an invisible comment straight after the number, like 40<!--s2b:videos-->,
and this script rewrites each marked number to the manifest's count.

Usage:
  python3 tools/sync-video-count.py          rewrite stale marked numbers, report changed files
  python3 tools/sync-video-count.py --check  exit 1 if any marked number is stale (pre-commit hook)

The motion kit's publish script (site-motion-kit/scripts/publish-signal-to-build.mjs) runs this
after it writes the manifest, so a new video updates the count in the same step.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "work/signal-to-build/videos.json")
MARK = re.compile(r"\d+(?=<!--s2b:videos-->)")


def main() -> int:
    check = "--check" in sys.argv[1:]
    count = str(len(json.load(open(MANIFEST))["videos"]))
    stale = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "assets")]
        for f in fn:
            if not f.endswith(".html"):
                continue
            path = os.path.join(dp, f)
            src = open(path, encoding="utf-8").read()
            new = MARK.sub(count, src)
            if new != src:
                stale.append(os.path.relpath(path, ROOT))
                if not check:
                    open(path, "w", encoding="utf-8").write(new)
    if check and stale:
        print(f"Signal to Build video count is stale (manifest has {count}) in: {', '.join(stale)}")
        print("Run: python3 tools/sync-video-count.py")
        return 1
    if stale:
        print(f"Signal to Build video count set to {count} in: {', '.join(stale)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
