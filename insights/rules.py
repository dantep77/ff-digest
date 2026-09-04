"""Rules-based insights: rankings movers, injury changes, expert disagreement.

All rules read from the two most recent pulls already stored in SQLite by
fetcher.ingest, and produce a plain list of Insight objects. No LLM involved.
"""
import json
from dataclasses import dataclass

from storage import db

MOVER_THRESHOLD = 5          # min |delta| in rank_ecr to flag as a mover
DISAGREEMENT_STD_THRESHOLD = 3.0   # min rank_std to flag as high expert disagreement


@dataclass
class Insight:
    type: str          # "mover" | "injury" | "disagreement"
    player_name: str
    position: str
    detail: str


def find_ranking_movers(conn, season: str, position: str, scoring: str) -> list[Insight]:
    prev_ts, latest_ts = db.get_last_two_ranking_pulls(conn, season, position, scoring)
    if prev_ts is None or latest_ts is None:
        return []

    prev_rows = {r["player_id"]: r for r in db.get_rankings_at(conn, season, position, scoring, prev_ts)}
    latest_rows = db.get_rankings_at(conn, season, position, scoring, latest_ts)

    insights = []
    for row in latest_rows:
        prev = prev_rows.get(row["player_id"])
        if prev is None or prev["rank_ecr"] is None or row["rank_ecr"] is None:
            continue
        delta = prev["rank_ecr"] - row["rank_ecr"]  # positive = moved up (better rank)
        if abs(delta) >= MOVER_THRESHOLD:
            direction = "up" if delta > 0 else "down"
            insights.append(
                Insight(
                    type="mover",
                    player_name=row["player_name"],
                    position=position,
                    detail=f"Moved {direction} {abs(delta)} spots ({prev['rank_ecr']} -> {row['rank_ecr']})",
                )
            )
    return insights


def find_injury_changes(conn) -> list[Insight]:
    prev_ts, latest_ts = db.get_last_two_injury_pulls(conn)
    if prev_ts is None or latest_ts is None:
        return []

    prev_rows = {r["player_id"]: r for r in db.get_injuries_at(conn, prev_ts)}
    latest_rows = db.get_injuries_at(conn, latest_ts)

    insights = []
    for row in latest_rows:
        prev = prev_rows.get(row["player_id"])
        if prev is None:
            insights.append(
                Insight(
                    type="injury",
                    player_name=row["player_name"],
                    position="",
                    detail=f"New injury status: {row['status']} ({row['injury_type']})",
                )
            )
        elif prev["status"] != row["status"]:
            insights.append(
                Insight(
                    type="injury",
                    player_name=row["player_name"],
                    position="",
                    detail=f"Status changed: {prev['status']} -> {row['status']}",
                )
            )
    return insights


def find_expert_disagreement(conn, season: str, position: str, scoring: str) -> list[Insight]:
    _, latest_ts = db.get_last_two_ranking_pulls(conn, season, position, scoring)
    if latest_ts is None:
        return []

    insights = []
    for row in db.get_rankings_at(conn, season, position, scoring, latest_ts):
        if row["rank_std"] is not None and row["rank_std"] >= DISAGREEMENT_STD_THRESHOLD:
            detail = f"High expert disagreement: rank {row['rank_min']}-{row['rank_max']} (std {row['rank_std']})"

            expert_ranks = json.loads(row["experts_json"] or "{}")
            if expert_ranks:
                highest_id = min(expert_ranks, key=lambda eid: int(expert_ranks[eid]))
                lowest_id = max(expert_ranks, key=lambda eid: int(expert_ranks[eid]))
                names = db.get_expert_names(conn, [int(highest_id), int(lowest_id)])
                highest_name = names.get(int(highest_id), f"Expert {highest_id}")
                lowest_name = names.get(int(lowest_id), f"Expert {lowest_id}")
                if highest_id != lowest_id:
                    detail += f" -- highest: {highest_name} (#{expert_ranks[highest_id]}), lowest: {lowest_name} (#{expert_ranks[lowest_id]})"

            insights.append(
                Insight(
                    type="disagreement",
                    player_name=row["player_name"],
                    position=position,
                    detail=detail,
                )
            )
    return insights


def generate_insights(conn, season: str, scoring: str, positions: list[str]) -> list[Insight]:
    insights: list[Insight] = []
    for position in positions:
        insights.extend(find_ranking_movers(conn, season, position, scoring))
        insights.extend(find_expert_disagreement(conn, season, position, scoring))
    insights.extend(find_injury_changes(conn))
    return insights


if __name__ == "__main__":
    import config

    conn = db.get_connection()
    for insight in generate_insights(conn, config.SEASON, config.SCORING, config.POSITIONS):
        print(f"[{insight.type}] {insight.player_name} ({insight.position}): {insight.detail}")
    conn.close()
