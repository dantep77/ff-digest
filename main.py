"""Orchestrates fetch -> insights -> render -> send."""
import argparse

import config
from fetcher.ingest import fetch_and_store_injuries, fetch_and_store_news, fetch_and_store_rankings
from insights.llm_summary import generate_narrative
from insights.rules import generate_insights
from mailer.render import render_digest
from mailer.report_store import save_report
from mailer.send import send_via_resend
from storage import db


def run(dry_run: bool = False) -> None:
    conn = db.get_connection()
    db.init_db(conn)

    for position in config.POSITIONS:
        n = fetch_and_store_rankings(conn, season=config.SEASON, position=position, scoring=config.SCORING)
        print(f"Fetched {n} {position} rankings")

    n_injuries = fetch_and_store_injuries(conn, year=config.SEASON)
    print(f"Fetched {n_injuries} injuries")

    news = fetch_and_store_news(conn)
    print(f"Found {len(news)} new news items")

    insights = generate_insights(conn, config.SEASON, config.SCORING, config.POSITIONS)
    print(f"Generated {len(insights)} insights")

    narrative = generate_narrative(insights)
    if narrative:
        print("Generated LLM narrative")

    top_news = news[:5]
    subject = "Your FF Digest"
    html = render_digest(insights, config.SCORING, news=top_news, narrative=narrative)

    if dry_run:
        from pathlib import Path
        out_path = Path("digest_preview.html")
        out_path.write_text(html, encoding="utf-8")
        print(f"Dry run: wrote {out_path.resolve()} instead of sending")
    else:
        result = send_via_resend(subject=subject, html=html)
        print(f"Sent. id={result.get('id')}")

        report = save_report(insights, top_news, config.SCORING, subject, resend_id=result.get("id"), narrative=narrative)
        print(f"Saved report {report['id']}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Render to a local HTML file instead of sending an email")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
