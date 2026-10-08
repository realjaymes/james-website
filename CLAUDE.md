# jamespraise.xyz: working notes for Claude Code

The project notes live in James's Obsidian vault in `Areas/Work/James Website/` (architecture and build plan, analytics). Read them before starting, and update the relevant note at the end of every build session.

GitHub Pages serves the site from `main`, and `.github/workflows/static.yml` regenerates the sitemap on each deploy. Preview locally with `python3 -m http.server 8080`.

The service filters on `/work/` come from the career-outreach case study proof bank (`~/.claude/skills/career-outreach/references/case-study-proof-bank.md`, section "jamespraise.xyz Work Filters"), never from a hand-picked list. When a case study or side project ships, give its proof bank entry a Public URL row and a Capability tags line, add the card, and run `python3 tools/check-work-tags.py --fix` to write the card's `data-service`. Client pages also show filter chips, which you edit by hand to match the card. The check runs as a pre-commit hook (`git config core.hooksPath .githooks`, set once per clone) and as a Claude Code hook on edits to the proof bank or any `work/` page.
