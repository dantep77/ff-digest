# Scaling ff-digest past a single recipient

This project was built for one recipient (you) on free-tier API keys. This
doc covers what actually breaks first if you want to run it for real users,
and what to upgrade to fix it.

## 1. FantasyPros API key

**Current limitation (free tier):** every endpoint response is silently
truncated to 10 items, regardless of how many actually exist
(`"limit": 10, "public_api_limited": true` in every response body). Verified
against rankings, injuries, news, and projections -- it's a blanket cap, not
per-endpoint.

**What this breaks at scale:**
- Rankings only cover the top ~10 players per position -- fine for "who's hot
  this week" content, useless for deep-league or bench/waiver-wire insights.
- Injuries/news are capped at the 10 most recent leaguewide, out of hundreds
  -- most subscribers' rostered players won't be covered.
- Serving many users off one free key means everyone sees the *same*
  truncated top-10 data; there's no per-user personalization possible at this
  tier since the data itself is the bottleneck, not the request volume.

**What to do:** request a paid tier at
https://secure.fantasypros.com/api-keys/request/ (or contact FantasyPros
sales for their partner/commercial API tier -- the public signup page is for
the free tier only; higher tiers are typically negotiated). No code changes
are required on upgrade -- the `limit` and `public_api_limited` fields are
purely server-side; `fetcher/fantasypros_client.py` and `fetcher/ingest.py`
already parse and store however many players the response actually contains.

**Also confirm at that point:**
- Actual rate limits (requests/minute or /day) for the paid tier -- the
  public OpenAPI spec (`doc/fantasypros_v2_public.yml`) doesn't document
  these; they come with the commercial agreement. Fetching 6 positions +
  injuries per digest run is only ~7 requests, but N subscribers with
  per-league personalization could multiply that fast if you fetch per-user
  instead of once and fanning out.
- Whether player pool coverage (all rostered players, not just top-N) is
  actually included at the tier you pick.

## 2. Resend (email delivery)

**Current setup:** `EMAIL_FROM` uses Resend's shared sandbox domain
(`onboarding@resend.dev` or any local-part `@resend.dev`), sending to a
single hardcoded `EMAIL_TO` in `.env`. This is Resend's free/test path and
is not meant for sending to arbitrary recipients.

**What breaks at scale:**
- The `@resend.dev` sandbox domain is rate-limited and intended for testing
  -- Resend's terms restrict it from being used to send to real, varied
  recipient lists.
- Deliverability: sending to unrelated inboxes from a shared sandbox domain
  will hit spam filters fast. Real subscribers need mail from a domain you
  control with proper authentication.
- No unsubscribe handling, no bounce/complaint handling, no per-recipient
  personalization pipeline -- `mailer/send.py` currently does one
  synchronous POST per run with a single hardcoded recipient.

**What to do:**
1. **Verify a real sending domain in Resend** (Resend dashboard -> Domains):
   add the SPF, DKIM, and (recommended) DMARC records at your DNS provider.
   Once verified, set `EMAIL_FROM=digest@yourdomain.com`.
2. **Move to a paid Resend plan** once volume passes the free tier's monthly
   send cap (check current limits in the Resend pricing page -- they change
   over time, don't hardcode a number here).
3. **Build a subscriber list** -- replace the single `EMAIL_TO` env var with
   a `subscribers` table (email, league/scoring preferences, active flag)
   in SQLite or a real database, and loop `send_via_resend()` per
   subscriber (or use Resend's batch send API for efficiency once you're
   past a handful of recipients).
4. **Handle unsubscribes/bounces** -- Resend supports webhooks for
   `email.bounced`, `email.complained`, etc. Wire those to flip a
   subscriber's `active` flag rather than continuing to send into a bounce.

## 3. Other things that stop being "solo project" shaped

These aren't blockers today, but come up quickly once there's more than one
recipient:

- **Per-league personalization**: right now positions/scoring are fixed in
  `config.py` (`SCORING = "PPR"`, all 6 standard positions). Multi-user
  means these become per-subscriber settings, which means the insight
  generation and rendering pipeline needs to run per-subscriber-config
  rather than once globally -- watch the FantasyPros request-volume
  implication above if you do this per-user instead of caching one pull per
  distinct scoring format.
- **SQLite -> real database**: SQLite is fine for one recipient's history.
  Concurrent writes from multiple scheduled runs, or a subscriber table with
  real write traffic (signups/unsubscribes), is a good trigger to move to
  Postgres.
- **Secrets**: currently 4-5 GitHub Actions repo secrets. A subscriber list
  and per-user config should not live in secrets -- that's a database
  concern, not a `.env`/secrets-manager concern.
