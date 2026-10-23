#!/usr/bin/env python3
"""Fail if any mailto: href has a subject or body that is not fully percent-encoded.

Checks every .html file under the repo root. A mailto href fails when its
subject or body contains a raw &, #, space, newline, or an unencoded "?" or "+",
or when the query string has a parameter that is not subject, body, cc or bcc
(which is what a raw & in the text produces: the text after it becomes a stray
parameter and the email body is cut off).

Usage: python3 scripts/check-mailto.py
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
HREF = re.compile(r'href\s*=\s*(["\'])(mailto:.*?)\1', re.I | re.S)
ALLOWED = {"subject", "body", "cc", "bcc"}
problems = []
count = 0

for path in sorted(ROOT.rglob("*.html")):
    if ".git" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    for m in HREF.finditer(text):
        href = m.group(2)
        count += 1
        line = text.count("\n", 0, m.start()) + 1
        rel = path.relative_to(ROOT)
        if "?" not in href:
            continue
        query = href.split("?", 1)[1]
        if "?" in query:
            problems.append((rel, line, "raw ? in query", href))
        for part in query.split("&"):
            key, _, val = part.partition("=")
            if key.lower() not in ALLOWED:
                problems.append((rel, line, f"stray parameter '{key[:30]}' (raw & or # earlier in subject/body)", href))
                continue
            if re.search(r"[#\s+]|\n", val):
                problems.append((rel, line, f"unencoded #, +, space or newline in {key}", href))
            if "&amp;" in val:
                problems.append((rel, line, f"raw &amp; in {key}", href))

print(f"Checked {count} mailto links.")
if problems:
    print(f"FAIL: {len(problems)} problem(s)")
    for rel, line, why, href in problems:
        print(f"  {rel}:{line}  {why}\n    {unquote(href)[:160]}")
    sys.exit(1)
print("OK: every mailto subject and body is fully percent-encoded.")
