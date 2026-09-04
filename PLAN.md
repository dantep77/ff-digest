# ff-digest — build plan

Automated fantasy football email digest built on the FantasyPros public API.

## Goal (v1 scope)
A script that: fetches current FantasyPros data → generates rules-based insights →
renders an HTML email → sends it via an email provider → runs on a schedule.
Single recipient (you) to start. No web UI, no multi-user accounts yet.

## Tech stack
- Python 3.11+
- `httpx` or `requests` — API calls
- SQLite (via `sqlite3` or `sqlmodel`) — local cache/history, zero setup
- Jinja2 — HTML email templating
- Email: Resend or SES (pick one — Resend has the simplest API for a solo project)
- Optional: Anthropic API (`anthropic` SDK) for narrative summarization
- GitHub Actions — scheduling (cron trigger + repo secrets for API keys)

## Repo structure
```
ff-digest/
  fetcher/
    fantasypros_client.py     # thin wrapper around the FantasyPros API
  storage/
    db.py                     # SQLite schema + read/write helpers
    schema.sql
  insights/
    rules.py                  # ranking movers, injury flags, expert disagreement
    llm_summary.py            # optional Claude-generated narrative (behind a flag)
  mailer/                     # named "mailer", not "email" -- avoids shadowing
    templates/                # the stdlib "email" module (breaks httpx)
      digest.html.j2
    render.py
    send.py                   # provider-specific send logic
  config.py                   # env var loading, constants
  main.py                     # orchestrates fetch -> insights -> render -> send
  .env.example
  .github/workflows/digest.yml
  requirements.txt
  README.md
```

## Milestones (build in this order)

**1. Fetcher + storage (get real data flowing)**
- `fantasypros_client.py`: functions for rankings, projections, news, injuries
- `db.py`: SQLite tables — `raw_pulls`, `players`, `rankings_history`
- Test: run fetcher standalone, confirm data lands in SQLite
- Milestone done when: `python -m fetcher.fantasypros_client` prints real player data

**2. Insight rules (no LLM yet)**
- Compare this pull vs last pull in `rankings_history` → flag movers (>5 spot change)
- Flag any player with a new/changed injury status
- Flag high variance between expert rankings (if the API tier returns per-expert data)
- Output: a plain Python list of `Insight` objects (type, player, detail)
- Milestone done when: running insights against two stored pulls produces a sane list

**3. Email template + local send test**
- Jinja2 template rendering the insight list into clean HTML
- Send via Resend/SES to yourself, hardcoded recipient first
- Milestone done when: you receive a real email with real content

**4. Optional: LLM narrative layer**
- Pass the structured insight list (not raw data) to Claude API
- Prompt constrained to only narrate what's in the list — no invented stats
- Feature-flagged so it can fail gracefully and fall back to the rules-only email

**5. Scheduling**
- `.github/workflows/digest.yml` — cron triggers (e.g. Tue AM, Sun AM)
- Store `FANTASYPROS_API_KEY`, `RESEND_API_KEY` (or SES creds), `ANTHROPIC_API_KEY`
  as GitHub Actions repo secrets
- Milestone done when: a manual workflow_dispatch run sends a real email

**6. Polish (only after 1-5 work end to end)**
- Dedup so repeated news items don't reappear
- Multiple recipients / basic subscriber table
- Per-league scoring format (PPR vs standard) if personalizing

## Environment variables needed
```
FANTASYPROS_API_KEY=
EMAIL_PROVIDER_API_KEY=
EMAIL_FROM=
EMAIL_TO=
ANTHROPIC_API_KEY=        # optional, only if using LLM summaries
```

## Notes for the Claude Code session
- Build and test milestone 1 fully before moving to milestone 2 — each stage should
  run standalone from the command line.
- Keep the FantasyPros client isolated so API shape changes don't ripple everywhere.
- Don't commit `.env` — only `.env.example`.
- Confirm your FantasyPros API tier's rate limits before writing the fetch schedule.
