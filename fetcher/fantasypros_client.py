"""Thin wrapper around the FantasyPros public API (NFL endpoints only).

Docs: doc/fantasypros_v2_public.yml
Base URL: https://api.fantasypros.com/public/v2/json
Auth: x-api-key header
"""
import httpx

import config


class FantasyProsError(RuntimeError):
    pass


def _get(path: str, params: dict | None = None) -> dict:
    if not config.FANTASYPROS_API_KEY:
        raise FantasyProsError("FANTASYPROS_API_KEY is not set")

    url = f"{config.FANTASYPROS_BASE_URL}{path}"
    resp = httpx.get(
        url,
        headers={"x-api-key": config.FANTASYPROS_API_KEY},
        params={k: v for k, v in (params or {}).items() if v is not None},
        timeout=30.0,
    )
    if resp.status_code >= 400:
        raise FantasyProsError(f"{resp.status_code} {resp.request.url}: {resp.text}")
    return resp.json()


def get_rankings(
    season: str = config.SEASON,
    week: int = 0,
    position: str | None = None,
    scoring: str = config.SCORING,
    experts: str | None = "show",
) -> dict:
    """Consensus rankings for a season/week, optionally filtered by position.

    Set week=0 for draft/preseason rankings, or the NFL week number for
    weekly rankings. `experts="show"` includes per-expert rank detail, which
    powers the expert-disagreement insight.
    """
    return _get(
        f"/nfl/{season}/consensus-rankings",
        {"position": position, "scoring": scoring, "week": week, "experts": experts},
    )


def get_projections(season: str = config.SEASON, week: int = 0, position: str | None = None, scoring: str = config.SCORING) -> dict:
    return _get(f"/nfl/{season}/projections", {"week": week, "position": position, "scoring": scoring})


def get_news(limit: int = 25, category: str | None = None, fpid: int | None = None) -> dict:
    return _get("/nfl/news", {"limit": limit, "category": category, "fpid": fpid})


def get_injuries(year: str = config.SEASON, week: int | None = None, include_probabilities: str | None = None) -> dict:
    return _get("/nfl/injuries", {"year": year, "week": week, "include_probabilities": include_probabilities})


def get_players(player: int | None = None, update: str | None = None) -> dict:
    return _get("/nfl/players", {"player": player, "update": update})


if __name__ == "__main__":
    data = get_rankings(position="RB")
    players = data.get("players", [])
    print(f"Fetched {len(players)} RB rankings for {data.get('year')} week {data.get('week')}")
    for p in players[:10]:
        print(f"  {p.get('rank_ecr'):>3} {p.get('player_name'):25} {p.get('player_team_id')}")
