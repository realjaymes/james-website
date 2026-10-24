# jamespraise.xyz: working notes for Claude Code

The project notes live in James's Obsidian vault in `Areas/Work/James Website/` (architecture and build plan, analytics). Read them before starting, and update the relevant note at the end of every build session.

GitHub Pages serves the site from `main`, and `.github/workflows/static.yml` regenerates the sitemap on each deploy. Preview locally with `python3 -m http.server 8080`.

The service filters on `/work/` come from the career-outreach case study proof bank (`~/.claude/skills/career-outreach/references/case-study-proof-bank.md`, section "jamespraise.xyz Work Filters"), never from a hand-picked list. When a case study or side project ships, give its proof bank entry a Public URL row and a Capability tags line, add the card, and run `python3 tools/check-work-tags.py --fix` to write the card's `data-service`. Client pages also show filter chips, which you edit by hand to match the card. The check runs as a pre-commit hook (`git config core.hooksPath .githooks`, set once per clone) and as a Claude Code hook on edits to the proof bank or any `work/` page.

Never type the Signal to Build video count by hand. Write any mention as `40<!--s2b:videos-->` and run `python3 tools/sync-video-count.py`, which sets every marked number to the entry count in `work/signal-to-build/videos.json`. The motion kit's publish script runs it after each new video, and the pre-commit hook blocks a commit while a marked count is stale.

Every /work page (proof page, pitch, case study, side project) has its own share card, rendered from the page's title by `python3 tools/og-work-cards.py --apply work/<slug>` into `assets/images/og/work/`. Run it whenever a /work page is added or its title or headline changes. The pre-commit hook runs `--check` and blocks a commit while a /work page has no card. Every other page uses the site-wide image from `tools/og-image.py`; bump `IMAGE_VERSION` there whenever either set of images changes, so platforms refetch.
