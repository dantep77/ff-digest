"""Fetch from FantasyPros and persist into SQLite (raw + normalized)."""
import json

from fetcher import fantasypros_client as fp
from storage import db


def _to_int(value):
    if value is None or value == "":
        return None
    return int(float(value))


def _to_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _normalize_player(row: dict) -> dict:
    return {
        "player_id": row["player_id"],
        "player_name": row.get("player_name"),
        "team_id": row.get("player_team_id"),
        "position": row.get("player_position_id") or row.get("player_positions"),
        "bye_week": row.get("player_bye_week"),
        "page_url": row.get("player_page_url"),
    }


def _normalize_ranking_row(row: dict) -> dict:
    return {
        "player_id": row["player_id"],
        "rank_ecr": _to_int(row.get("rank_ecr")),
        "pos_rank": row.get("pos_rank"),
        "rank_min": _to_int(row.get("rank_min")),
        "rank_max": _to_int(row.get("rank_max")),
        "rank_ave": _to_float(row.get("rank_ave")),
        "rank_std": _to_float(row.get("rank_std")),
        "tier": row.get("tier"),
        "experts_json": json.dumps(row.get("experts") or {}),
    }


def fetch_and_store_rankings(conn, season: str, position: str, scoring: str, week: int = 0) -> int:
    data = fp.get_rankings(season=season, week=week, position=position, scoring=scoring)
    players = data.get("players", [])

    pull_id = db.insert_raw_pull(conn, "consensus-rankings", {"season": season, "position": position, "scoring": scoring, "week": week}, data)
    db.upsert_players(conn, [_normalize_player(p) for p in players])

    expert_names = data.get("expert_names") or {}
    expert_twitter = data.get("expert_twitter") or {}
    if expert_names:
        db.upsert_experts(
            conn,
            [{"expert_id": int(eid), "name": name, "twitter": expert_twitter.get(eid)} for eid, name in expert_names.items()],
        )

    db.insert_rankings(conn, pull_id, str(data.get("year", season)), str(data.get("week", week)), position, scoring, [_normalize_ranking_row(p) for p in players])
    return len(players)


def _normalize_injury_row(row: dict) -> dict:
    return {
        "player_id": row["player_id"],
        "status": row.get("status"),
        "status_short": row.get("status_short"),
        "injury_type": row.get("injury_type"),
        "comment": row.get("comment"),
        "injury_update_date": row.get("injury_update_date"),
    }


def fetch_and_store_injuries(conn, year: str, week: int | None = None) -> int:
    data = fp.get_injuries(year=year, week=week)
    injuries = data.get("injuries", [])

    pull_id = db.insert_raw_pull(conn, "injuries", {"year": year, "week": week}, data)
    db.upsert_players(
        conn,
        [
            {
                "player_id": row["player_id"],
                "player_name": row.get("name"),
                "team_id": None,
                "position": None,
                "bye_week": None,
                "page_url": None,
            }
            for row in injuries
        ],
    )
    db.insert_injuries(conn, pull_id, [_normalize_injury_row(row) for row in injuries])
    return len(injuries)


if __name__ == "__main__":
    import config as cfg

    conn = db.get_connection()
    db.init_db(conn)

    total = 0
    for position in cfg.POSITIONS:
        n = fetch_and_store_rankings(conn, season=cfg.SEASON, position=position, scoring=cfg.SCORING)
        print(f"Stored {n} {position} rankings")
        total += n

    n_injuries = fetch_and_store_injuries(conn, year=cfg.SEASON)
    print(f"Stored {n_injuries} injuries")

    conn.close()
    print(f"Done. {total} ranking rows, {n_injuries} injury rows stored.")
