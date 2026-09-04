# ff-digest

An automated fantasy football digest: fetches live NFL data, applies
rules-based analysis to flag what's actually worth reading, optionally
narrates it with Claude, and emails it out on a schedule -- with every past
digest archived on a small live site.

**Live archive:** https://dantep77.github.io/ff-digest/

## What it does

```
FantasyPros API -> SQLite -> insight rules -> HTML email -> Resend
                                  |                |
                                  v                v
                          (optional) Claude    report JSON -> React archive
                            narrative              (GitHub Pages)
```

Twice a week (Tuesday, after Monday Night Football; Friday, after the final
injury report), a GitHub Actions workflow:

1. **Fetches** current rankings, injuries, and news from the
   [FantasyPros public API](https://api.fantasypros.com/public/v2/json) and
   stores them in SQLite, building up history pull over pull.
2. **Flags what changed**, not just what's true right now: ranking movers
   (>5 spots since the last pull), new/changed injury statuses, and
   players where the experts genuinely disagree -- named by source
   (e.g. "highest: Chris Towers (CBS) #1, lowest: Matthew Berry (ESPN) #16"),
   not just a std-dev number.
3. **Tunes signal vs. noise per position** -- kickers and defenses swing
   on rankings/expert-disagreement metrics far more than skill positions do
   as a matter of course, so they need a much wider bar (2x the threshold)
   before they're worth flagging.
4. **Optionally narrates** the insight list in 3-5 sentences via Claude,
   constrained to only describe what's in the structured list -- no invented
   stats. Skipped automatically if no API key is set, and any API failure
   falls back to the rules-only email rather than breaking the run.
5. **Sends** the digest via Resend, and **archives** it as a JSON report
   that a small React static site (no backend, no router library, just
   `fetch()` against static JSON on GitHub Pages) renders for browsing past
   sends.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in FANTASYPROS_API_KEY at minimum; see .env.example for the rest
```

## Usage

Run each stage standalone:

```bash
python -m fetcher.fantasypros_client   # sanity check: prints top 10 RB rankings
python -m fetcher.ingest               # fetch + store rankings & injuries in SQLite
python -m insights.rules               # print generated insights
python -m mailer.render                # render digest_preview.html locally
python -m insights.llm_summary         # print an LLM narrative (requires ANTHROPIC_API_KEY)
```

Run the full pipeline:

```bash
python main.py --dry-run   # writes digest_preview.html instead of sending
python main.py             # fetches, generates insights, sends a real email, archives the report
```

Run the web archive locally:

```bash
cd web && npm install && npm run dev
```

## Notes

- **`FANTASYPROS_API_KEY` free tier is limited to ~10 players per position per
  pull** (`public_api_limited: true` in the API response). Insight rules and
  templates work fine at that scale; see `doc/SCALING.md` for what changes
  at a paid tier.
- Package is named `mailer/`, not `email/` -- `email` is a Python stdlib
  module name and shadowing it breaks `httpx` (which imports `email.parser`
  internally).
- `.github/workflows/digest.yml` runs on `workflow_dispatch` and a Tue/Fri
  cron; set `FANTASYPROS_API_KEY`, `EMAIL_PROVIDER_API_KEY`, `EMAIL_FROM`,
  `EMAIL_TO`, and optionally `ANTHROPIC_API_KEY` as repo Actions secrets. The
  SQLite DB is cached between runs via `actions/cache` so mover/injury-change
  comparisons have history to diff against.
- `.github/workflows/pages.yml` builds and deploys `web/` to GitHub Pages
  whenever a digest run commits a new report -- the archive site updates
  itself, no manual step.
