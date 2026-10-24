#!/usr/bin/env python3
"""Render the site's share image (Open Graph and X card) at 1200x630.

The design is option A, chosen by James on 2026-10-24: the dark homepage hero,
the cutout portrait on the right and the headline in gold. It renders through
headless Chrome with Satoshi embedded, so the output matches the live site.

    python3 tools/og-image.py            # writes assets/images/og-default.png

After changing the image, bump IMAGE_VERSION below and run with --tags, which
points every page's og:image and twitter:image at the new versioned URL so
social platforms refetch instead of serving their cached copy.
"""
import argparse, base64, pathlib, re, subprocess, tempfile, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "images" / "og-default.png"
IMAGE_VERSION = "20261024"
IMAGE_URL = f"https://jamespraise.xyz/assets/images/og-default.png?v={IMAGE_VERSION}"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_CSS = "https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap"
CACHE = pathlib.Path.home() / ".cache" / "mia-og-fonts"

CSS = """html,body{margin:0;width:1200px;height:630px;overflow:hidden}*{box-sizing:border-box}
body{font-family:'Satoshi',sans-serif;position:relative;-webkit-font-smoothing:antialiased;background:#100a16;color:#f7f4fa}
h1{margin:0;font-weight:900;letter-spacing:-.025em;line-height:1.05;font-size:64px}h1 span{color:#f1de71}p{margin:0}
.glow{position:absolute;right:-120px;top:-60px;width:720px;height:720px;border-radius:50%;background:radial-gradient(circle,rgba(113,132,241,.28),rgba(16,10,22,0) 65%)}
.copy{position:absolute;left:72px;top:96px;width:640px}
.hi{font-size:26px;font-weight:500;color:rgba(247,244,250,.72);margin-bottom:18px}
.sub{margin-top:26px;font-size:24px;line-height:1.38;font-weight:500;color:rgba(247,244,250,.78)}
.url{position:absolute;left:72px;bottom:56px;font-size:21px;font-weight:700;color:#f1de71}
img{position:absolute;right:20px;bottom:0;height:590px}"""

BODY = """<div class="glow"></div><div class="copy"><p class="hi">Hi, I'm James Praise.</p>
<h1>I build systems that <span>grow revenue predictably.</span></h1>
<p class="sub">I'm a go-to-market operator working on customer acquisition, product launches and growth.</p></div>
<p class="url">jamespraise.xyz</p><img src="{portrait}">"""


def font_css() -> str:
    """Satoshi @font-face rules with the woff2 files embedded as data URIs."""
    CACHE.mkdir(parents=True, exist_ok=True)
    css_file = CACHE / "satoshi.css"
    if not css_file.exists():
        req = urllib.request.Request(FONT_CSS, headers={"User-Agent": "Mozilla/5.0 Chrome/120"})
        css_file.write_text(urllib.request.urlopen(req, timeout=30).read().decode())
    out = []
    for block in re.findall(r"@font-face\s*{[^}]*}", css_file.read_text()):
        url = re.search(r"url\('(//[^']+\.woff2)'\)", block).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
        f = CACHE / url.rsplit("/", 1)[1]
        if not f.exists():
            f.write_bytes(urllib.request.urlopen("https:" + url, timeout=30).read())
        b64 = base64.b64encode(f.read_bytes()).decode()
        out.append("@font-face{font-family:'Satoshi';font-weight:%s;src:url(data:font/woff2;base64,%s) format('woff2')}" % (weight, b64))
    return "\n".join(out)


def render() -> None:
    portrait = "data:image/png;base64," + base64.b64encode(
        (ROOT / "assets" / "images" / "james-portrait-transparent.png").read_bytes()).decode()
    page = f"<!doctype html><html><head><meta charset='utf-8'><style>{font_css()}\n{CSS}</style></head><body>{BODY.format(portrait=portrait)}</body></html>"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page)
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--virtual-time-budget=3000", "--window-size=1200,630",
                    f"--screenshot={OUT}", f"file://{f.name}"], check=True, capture_output=True)
    print(f"wrote {OUT.relative_to(ROOT)}")


def tags() -> None:
    """Point every page's share image at IMAGE_URL and use the large X card."""
    img = re.compile(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*(")')
    changed = 0
    for page in ROOT.rglob("*.html"):
        if any(part.startswith(".") for part in page.relative_to(ROOT).parts):
            continue
        t = page.read_text()
        if "og:image" not in t:
            continue
        new = img.sub(rf"\g<1>{IMAGE_URL}\g<2>", t)
        new = new.replace('<meta name="twitter:card" content="summary" />', '<meta name="twitter:card" content="summary_large_image" />')
        if "twitter:image" not in new:
            new = new.replace('<meta name="twitter:card" content="summary_large_image" />',
                              f'<meta name="twitter:card" content="summary_large_image" />\n<meta name="twitter:image" content="{IMAGE_URL}" />', 1)
        if new != t:
            page.write_text(new)
            changed += 1
    print(f"updated {changed} pages")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", action="store_true", help="also rewrite the share tags on every page")
    a = ap.parse_args()
    render()
    if a.tags:
        tags()
