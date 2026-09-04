"""Render the insight list into an HTML email body."""
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from insights.rules import Insight

TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


def render_digest(insights: list[Insight], scoring: str, news: list[dict] | None = None, narrative: str | None = None) -> str:
    template = _env.get_template("digest.html.j2")
    return template.render(
        generated_at=datetime.now(timezone.utc).strftime("%a %b %d, %Y %H:%M UTC"),
        scoring=scoring,
        movers=[i for i in insights if i.type == "mover"],
        injuries=[i for i in insights if i.type == "injury"],
        disagreements=[i for i in insights if i.type == "disagreement"],
        news=news or [],
        narrative=narrative,
    )


if __name__ == "__main__":
    import config
    from storage import db
    from insights.rules import generate_insights

    conn = db.get_connection()
    insights = generate_insights(conn, config.SEASON, config.SCORING, config.POSITIONS)
    conn.close()

    html = render_digest(insights, config.SCORING)
    out_path = Path("digest_preview.html")
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path.resolve()} ({len(insights)} insights)")
