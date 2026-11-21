#!/usr/bin/env python3
"""Analytics check for every jamespraise.xyz page. Runs in the pre-commit hook and the
GitHub Pages deploy workflow (.github/workflows/static.yml), which stops the deploy on a failure.

Fails when a page is missing Google Tag Manager GTM-WKSZ7DQC in <head>, is missing its
noscript iframe after <body>, or loads GA4 directly with a gtag.js G- snippet. GA4
G-NJ4XNKCBPD and Microsoft Clarity load through GTM, so a direct snippet counts visits twice.
Redirect stubs are skipped. Every other page carries tracking, microsites, proof pages,
hiring exercises and legal pages included (James, 2026-11-21).
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GTM = "GTM-WKSZ7DQC"

fails, n = [], 0
for p in sorted(ROOT.rglob("*.html")):
    rel = p.relative_to(ROOT).as_posix()
    if rel.split("/")[0] in {".git", "node_modules"}:
        continue
    s = p.read_text(encoding="utf8", errors="ignore")
    if 'http-equiv="refresh"' in s:
        continue
    n += 1
    head = s.split("</head>", 1)[0]
    body = re.search(r"<body[^>]*>", s)
    if "googletagmanager.com/gtm.js" not in head or GTM not in head:
        fails.append(f"{rel}: GTM {GTM} missing from <head>")
    if not body or f"ns.html?id={GTM}" not in s[body.end(): body.end() + 600]:
        fails.append(f"{rel}: GTM noscript iframe missing right after <body>")
    if re.search(r"gtag/js\?id=G-", s):
        fails.append(f"{rel}: loads GA4 with a gtag.js G- snippet; GA4 comes through GTM only")

for f in fails:
    print("FAIL", f)
if fails:
    print(f"check-analytics: {len(fails)} problem(s). Copy the GTM <head> snippet and the noscript "
          "iframe from index.html.", file=sys.stderr)
    sys.exit(1)
print(f"check-analytics: GTM wiring correct on all {n} pages")
