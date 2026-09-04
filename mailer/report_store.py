"""Persist each real digest send as a JSON report for the web archive."""
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from insights.rules import Insight

REPORTS_DIR = Path(__file__).parent.parent / "web" / "public" / "reports"
INDEX_PATH = REPORTS_DIR / "index.json"


def _report_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _load_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def save_report(
    insights: list[Insight],
    news: list[dict],
    scoring: str,
    subject: str,
    resend_id: str | None = None,
    narrative: str | None = None,
) -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    movers = [asdict(i) for i in insights if i.type == "mover"]
    injuries = [asdict(i) for i in insights if i.type == "injury"]
    disagreements = [asdict(i) for i in insights if i.type == "disagreement"]

    report = {
        "id": _report_id(),
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "subject": subject,
        "scoring": scoring,
        "resend_id": resend_id,
        "movers": movers,
        "injuries": injuries,
        "disagreements": disagreements,
        "news": news,
        "narrative": narrative,
    }

    (REPORTS_DIR / f"{report['id']}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    index = _load_index()
    index.insert(
        0,
        {
            "id": report["id"],
            "sent_at": report["sent_at"],
            "subject": report["subject"],
            "mover_count": len(movers),
            "injury_count": len(injuries),
            "disagreement_count": len(disagreements),
            "news_count": len(news),
        },
    )
    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")

    return report
