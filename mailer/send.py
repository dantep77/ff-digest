"""Send the rendered digest via Resend."""
import httpx

import config


class SendError(RuntimeError):
    pass


def send_via_resend(subject: str, html: str, to: str = config.EMAIL_TO, from_addr: str = config.EMAIL_FROM) -> dict:
    if not config.EMAIL_PROVIDER_API_KEY:
        raise SendError("EMAIL_PROVIDER_API_KEY is not set")
    if not to or not from_addr:
        raise SendError("EMAIL_TO and EMAIL_FROM must both be set")

    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {config.EMAIL_PROVIDER_API_KEY}"},
        json={"from": from_addr, "to": [to], "subject": subject, "html": html},
        timeout=30.0,
    )
    if resp.status_code >= 400:
        raise SendError(f"{resp.status_code}: {resp.text}")
    return resp.json()


if __name__ == "__main__":
    from mailer.render import render_digest
    from insights.rules import generate_insights
    from storage import db

    conn = db.get_connection()
    insights = generate_insights(conn, config.SEASON, config.SCORING, config.POSITIONS)
    conn.close()

    html = render_digest(insights, config.SCORING)
    result = send_via_resend(subject="Your FF Digest", html=html)
    print(f"Sent. id={result.get('id')}")
