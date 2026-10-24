#!/usr/bin/env python3
"""Render a 1200x630 share card for every /work page from the page's own title.

Three page kinds get a card: proof pages (/work/<slug>/proof/), application
microsites (the noindex "Hello <Company>" decks) and case studies (client and
side-project pages, labelled from data-tags on the Work grid). Every other page
keeps the site-wide image from tools/og-image.py.

    python3 tools/og-work-cards.py --look a|b|c --out DIR work/lightsprint/proof ...   # preview
    python3 tools/og-work-cards.py --apply [work/<slug> ...]                          # ship
    python3 tools/og-work-cards.py --check                                            # pre-commit

--apply renders each card to assets/images/og/work/<slug>[-proof].jpg and points the
page's og:image and twitter:image at it, adding the full set of share tags to pages
that have none. With no pages named it covers every /work page. The local server must
be running on port 8080 only for look b, which screenshots the page itself.
"""
import argparse, base64, html, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from importlib import import_module
og = import_module("og-image")

LOCAL = "http://localhost:8080"


LOOK = "c"
CARD_DIR = ROOT / "assets" / "images" / "og" / "work"


def page_info(rel: str) -> dict:
    rel = rel.strip("/")
    t = (ROOT / rel / "index.html").read_text()
    title = html.unescape(re.search(r"<title>([^<]*)</title>", t).group(1))
    title = re.sub(r"\s*[—|]\s*James Praise\s*$", "", title).strip()
    slug = rel.split("/")[1]
    if rel.endswith("/proof"):
        kind, label = "proof", "BREAKDOWN"
    elif 'name="robots" content="noindex' in t and title.startswith("Hello "):
        kind, label = "pitch", "PITCH"
    else:
        grid = (ROOT / "work" / "index.html").read_text()
        m = re.search(r'data-tags="([^"]*)"[^>]*href="/work/%s/"' % re.escape(slug), grid)
        if not m:
            return None
        kind = "case"
        label = ("SIDE PROJECT" if m and "side" in m.group(1) else "CASE STUDY") + " · " + title.upper()
        # A case study's page title is only the client's name, so the card leads with its headline.
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        if h1:
            title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", h1.group(1)))).strip()
    return {"rel": rel, "title": title, "kind": kind, "label": label, "url": f"jamespraise.xyz/{rel}/"}


def uri(p: pathlib.Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def screenshot(rel: str) -> str:
    shot = pathlib.Path(tempfile.mkdtemp()) / "shot.png"
    subprocess.run([og.CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--virtual-time-budget=5000", "--window-size=1280,800",
                    f"--screenshot={shot}", f"{LOCAL}/{rel}/"], check=True, capture_output=True)
    return uri(shot, "image/png")


# The title starts at 64px and shrinks until it fits its box.
# It measures after Satoshi has loaded, because the fallback font wraps differently.
FIT = """<script>document.fonts.ready.then(()=>{const h=document.querySelector('h1');let s=parseFloat(getComputedStyle(h).fontSize);
while(h.offsetHeight>+h.dataset.max&&s>34){s-=2;h.style.fontSize=s+'px'}})</script>"""

LOOKS = {
"a": ("""body{background:#100a16;color:#f7f4fa}
.glow{position:absolute;right:-120px;top:-60px;width:720px;height:720px;border-radius:50%;background:radial-gradient(circle,rgba(113,132,241,.28),rgba(16,10,22,0) 65%)}
.pill{position:absolute;left:72px;top:72px;border:2px solid #f1de71;color:#f1de71;border-radius:999px;padding:6px 16px;font-weight:800;font-size:16px;letter-spacing:.06em}
.t{position:absolute;left:72px;top:140px;width:600px}h1{font-size:64px;line-height:1.06}
.by{position:absolute;left:72px;bottom:56px;font-size:21px;font-weight:500;color:rgba(247,244,250,.75)}.by b{color:#f1de71;font-weight:700}
.port{position:absolute;right:10px;bottom:0;height:540px}""",
"""<div class="glow"></div><div class="pill">{label}</div><div class="t"><h1 data-max="300">{title}</h1></div>
<p class="by">By James Praise · <b>{url}</b></p><img class="port" src="{portrait}">"""),
"b": ("""body{background:#100a16;color:#f7f4fa}
.pill{position:absolute;left:64px;top:68px;background:#f1de71;color:#100a16;border-radius:999px;padding:6px 16px;font-weight:800;font-size:16px;letter-spacing:.06em}
.t{position:absolute;left:64px;top:132px;width:470px}h1{font-size:56px;line-height:1.06}
.by{position:absolute;left:64px;bottom:52px;display:flex;align-items:center;gap:14px;font-size:19px;font-weight:500;color:rgba(247,244,250,.75)}
.by img{width:56px;height:56px;border-radius:50%;object-fit:cover;object-position:50% 12%;background:#2a2033;border:2px solid #f1de71}.by b{display:block;color:#f7f4fa;font-weight:700}
.shot{position:absolute;left:590px;top:70px;width:680px;border-radius:14px;overflow:hidden;border:2px solid rgba(247,244,250,.22);box-shadow:0 30px 80px rgba(0,0,0,.55)}
.bar{height:30px;background:#231a2c;display:flex;gap:7px;align-items:center;padding-left:14px}.bar i{width:10px;height:10px;border-radius:50%;background:rgba(247,244,250,.3)}
.shot img{display:block;width:100%}""",
"""<div class="pill">{label}</div><div class="t"><h1 data-max="290">{title}</h1></div>
<div class="by"><img src="{portrait}"><span><b>James Praise</b>{url}</span></div>
<div class="shot"><div class="bar"><i></i><i></i><i></i></div><img src="{shot}"></div>"""),
"c": ("""body{background:#F7F4FA;color:#100a16}
.card{position:absolute;left:64px;top:56px;right:64px;bottom:64px;background:#fff;border:4px solid #100a16;border-radius:26px;box-shadow:12px 12px 0 #100a16}
.pill{position:absolute;left:48px;top:40px;background:#f1de71;border:2px solid #100a16;border-radius:999px;padding:6px 16px;font-weight:800;font-size:16px;letter-spacing:.06em}
.t{position:absolute;left:48px;top:104px;width:930px}h1{font-size:62px;line-height:1.06}
.by{position:absolute;left:48px;bottom:36px;display:flex;align-items:center;gap:14px;font-size:20px;font-weight:500;color:rgba(16,10,22,.7)}
.by img{width:60px;height:60px;border-radius:50%;object-fit:cover;object-position:50% 12%;background:#f1de71;border:3px solid #100a16}.by b{display:block;color:#100a16;font-weight:800}
.rule{position:absolute;left:48px;right:48px;bottom:118px;height:4px;background:#7184f1}""",
"""<div class="card"><div class="pill">{label}</div><div class="t"><h1 data-max="250">{title}</h1></div>
<div class="rule"></div><div class="by"><img src="{portrait}"><span><b>James Praise</b>{url}</span></div></div>"""),
}

BASE = """html,body{margin:0;width:1200px;height:630px;overflow:hidden}*{box-sizing:border-box}
body{font-family:'Satoshi',sans-serif;position:relative;-webkit-font-smoothing:antialiased}h1{margin:0;font-weight:900;letter-spacing:-.025em}p{margin:0}"""


def render(info: dict, look: str, out: pathlib.Path) -> None:
    css, body = LOOKS[look]
    portrait = uri(ROOT / "assets/images/james-portrait-transparent.png", "image/png")
    shot = screenshot(info["rel"]) if "{shot}" in body else ""
    page = (f"<!doctype html><html><head><meta charset='utf-8'><style>{og.font_css()}\n{BASE}\n{css}</style></head><body>"
            + body.replace("{label}", info["label"]).replace("{title}", html.escape(info["title"]))
                  .replace("{url}", html.escape(info["url"])).replace("{portrait}", portrait).replace("{shot}", shot)
            + FIT + "</body></html>")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([og.CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--virtual-time-budget=3000", "--window-size=1200,630",
                    f"--screenshot={out}", f"file://{f.name}"], check=True, capture_output=True)


def card_pages() -> list:
    pages = []
    for f in sorted((ROOT / "work").glob("*/index.html")) + sorted((ROOT / "work").glob("*/proof/index.html")):
        if 'http-equiv="refresh"' in f.read_text():
            continue
        pages.append(str(f.parent.relative_to(ROOT)))
    return pages


def apply(rel: str) -> str:
    info = page_info(rel)
    if not info:
        return f"skip {rel} (no card on the Work grid)"
    name = info["rel"].split("/", 1)[1].replace("/", "-")
    png = pathlib.Path(tempfile.mkdtemp()) / "card.png"
    render(info, LOOK, png)
    jpg = CARD_DIR / f"{name}.jpg"
    jpg.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "86", str(png), "--out", str(jpg)],
                   check=True, capture_output=True)
    url = f"https://jamespraise.xyz/{jpg.relative_to(ROOT)}?v={og.IMAGE_VERSION}"
    f = ROOT / info["rel"] / "index.html"
    t = f.read_text()
    if "og:image" in t:
        t = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*(")', rf"\g<1>{url}\g<2>", t)
        t = t.replace('<meta name="twitter:card" content="summary" />', '<meta name="twitter:card" content="summary_large_image" />')
        if "twitter:image" not in t:
            t = t.replace('<meta name="twitter:card" content="summary_large_image" />',
                          f'<meta name="twitter:card" content="summary_large_image" />\n<meta name="twitter:image" content="{url}" />', 1)
    else:
        title = re.search(r"<title>([^<]*)</title>", t).group(1)
        desc = re.search(r'<meta name="description" content="([^"]*)"', t)
        desc = desc.group(1) if desc else ""
        page_url = f"https://jamespraise.xyz/{info['rel']}/"
        block = (f'<meta property="og:type" content="article" />\n<meta property="og:title" content="{title}" />\n'
                 f'<meta property="og:description" content="{desc}" />\n<meta property="og:url" content="{page_url}" />\n'
                 f'<meta property="og:image" content="{url}" />\n<meta name="twitter:card" content="summary_large_image" />\n'
                 f'<meta name="twitter:title" content="{title}" />\n<meta name="twitter:description" content="{desc}" />\n'
                 f'<meta name="twitter:image" content="{url}" />\n')
        anchor = re.search(r'<meta name="robots"[^>]*>\n|<meta name="description"[^>]*>\n', t)
        t = t[:anchor.end()] + block + t[anchor.end():]
    f.write_text(t)
    return f"{info['label']:<40} {jpg.relative_to(ROOT)}"


def check() -> int:
    """Fail when a /work page that should have a card points anywhere else, or its card file is missing."""
    bad = []
    for rel in card_pages():
        info = page_info(rel)
        if not info:
            continue
        name = info["rel"].split("/", 1)[1].replace("/", "-")
        t = (ROOT / rel / "index.html").read_text()
        if f"/assets/images/og/work/{name}.jpg" not in t or not (CARD_DIR / f"{name}.jpg").exists():
            bad.append(rel)
    for rel in bad:
        print(f"no share card: {rel}  (run: python3 tools/og-work-cards.py --apply {rel})")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    if "--apply" in sys.argv:
        for rel in [a for a in sys.argv[1:] if a != "--apply"] or card_pages():
            print(apply(rel))
        sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument("--look", default="a", choices=LOOKS)
    ap.add_argument("--out", required=True)
    ap.add_argument("pages", nargs="+")
    a = ap.parse_args()
    for rel in a.pages:
        info = page_info(rel)
        o = pathlib.Path(a.out) / f"{a.look}-{info['rel'].replace('/', '-')}.png"
        render(info, a.look, o)
        print(o, "|", info["label"], "|", info["title"])
