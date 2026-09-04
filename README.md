# ff-digest

Automated fantasy football email digest built on the [FantasyPros public API](https://api.fantasypros.com/public/v2/json).

Fetches current NFL rankings/injuries -> generates rules-based insights (ranking
movers, injury status changes, expert disagreement) -> optionally narrates them
with Claude -> renders an HTML email -> sends via Resend -> runs on a schedule
via GitHub Actions.

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
python main.py             # fetches, generates insights, and sends a real email
```

## Notes

- **`FANTASYPROS_API_KEY` free tier is limited to ~10 players per position per
  pull** (`public_api_limited: true` in the API response). Insight rules and
  templates work fine at that scale; upgrade the key for full-roster coverage.
- Package is named `mailer/`, not `email/` -- `email` is a Python stdlib
  module name and shadowing it breaks `httpx` (which imports `email.parser`
  internally).
- The LLM narrative layer is feature-flagged: it's skipped automatically if
  `ANTHROPIC_API_KEY` is unset, and any API error falls back to the rules-only
  email rather than failing the whole run.
- `.github/workflows/digest.yml` runs on `workflow_dispatch` and a Tue/Sun
  cron; set the four secrets (`FANTASYPROS_API_KEY`, `EMAIL_PROVIDER_API_KEY`,
  `EMAIL_FROM`, `EMAIL_TO`) plus optionally `ANTHROPIC_API_KEY` in the repo's
  Actions secrets. The SQLite DB is cached between runs via `actions/cache` so
  rankings-mover comparisons have history to diff against.
