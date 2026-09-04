"""Optional Claude-generated narrative summary of the insight list.

Feature-flagged: only runs if ANTHROPIC_API_KEY is set. Fails gracefully
(returns None) on any error so main.py can fall back to the rules-only email.
The prompt is constrained to only narrate what's in the structured insight
list -- no invented stats, no outside knowledge.
"""
import anthropic

import config
from insights.rules import Insight

SYSTEM_PROMPT = (
    "You write a short, punchy narrative summary for a fantasy football email digest. "
    "You will be given a structured list of insights (ranking movers, injury status "
    "changes, expert disagreement). Only narrate facts present in that list -- never "
    "invent stats, rankings, or context not given to you. If the list is empty, say "
    "there's nothing notable this week. Keep it to 3-5 sentences, conversational tone."
)


def _format_insights(insights: list[Insight]) -> str:
    if not insights:
        return "(no insights this pull)"
    return "\n".join(f"- [{i.type}] {i.player_name} ({i.position}): {i.detail}" for i in insights)


def generate_narrative(insights: list[Insight]) -> str | None:
    if not config.ANTHROPIC_API_KEY:
        return None

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _format_insights(insights)}],
        )
        return next((b.text for b in response.content if b.type == "text"), None)
    except Exception as e:
        print(f"llm_summary: falling back to rules-only email ({e})")
        return None


if __name__ == "__main__":
    from storage import db
    from insights.rules import generate_insights

    conn = db.get_connection()
    insights = generate_insights(conn, config.SEASON, config.SCORING, config.POSITIONS)
    conn.close()

    narrative = generate_narrative(insights)
    print(narrative or "(no narrative -- ANTHROPIC_API_KEY not set or call failed)")
