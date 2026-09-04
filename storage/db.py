"""SQLite schema initialization + read/write helpers."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str = config.DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_raw_pull(conn: sqlite3.Connection, endpoint: str, params: dict, response: dict) -> int:
    cur = conn.execute(
        "INSERT INTO raw_pulls (pulled_at, endpoint, params_json, response_json) VALUES (?, ?, ?, ?)",
        (_now(), endpoint, json.dumps(params), json.dumps(response)),
    )
    conn.commit()
    return cur.lastrowid


def upsert_players(conn: sqlite3.Connection, players: list[dict]) -> None:
    conn.executemany(
        """
        INSERT INTO players (player_id, player_name, team_id, position, bye_week, page_url)
        VALUES (:player_id, :player_name, :team_id, :position, :bye_week, :page_url)
        ON CONFLICT(player_id) DO UPDATE SET
            player_name = excluded.player_name,
            team_id = excluded.team_id,
            position = excluded.position,
            bye_week = excluded.bye_week,
            page_url = excluded.page_url
        """,
        players,
    )
    conn.commit()


def upsert_experts(conn: sqlite3.Connection, experts: list[dict]) -> None:
    conn.executemany(
        """
        INSERT INTO experts (expert_id, name, twitter)
        VALUES (:expert_id, :name, :twitter)
        ON CONFLICT(expert_id) DO UPDATE SET
            name = excluded.name,
            twitter = excluded.twitter
        """,
        experts,
    )
    conn.commit()


def get_expert_names(conn: sqlite3.Connection, expert_ids: list[int]) -> dict[int, str]:
    if not expert_ids:
        return {}
    placeholders = ",".join("?" * len(expert_ids))
    rows = conn.execute(f"SELECT expert_id, name FROM experts WHERE expert_id IN ({placeholders})", expert_ids).fetchall()
    return {r["expert_id"]: r["name"] for r in rows}


def insert_rankings(conn: sqlite3.Connection, pull_id: int, season: str, week: str, position: str, scoring: str, rows: list[dict]) -> None:
    pulled_at = _now()
    conn.executemany(
        """
        INSERT INTO rankings_history
            (pull_id, pulled_at, season, week, position, scoring, player_id,
             rank_ecr, pos_rank, rank_min, rank_max, rank_ave, rank_std, tier, experts_json)
        VALUES
            (:pull_id, :pulled_at, :season, :week, :position, :scoring, :player_id,
             :rank_ecr, :pos_rank, :rank_min, :rank_max, :rank_ave, :rank_std, :tier, :experts_json)
        """,
        [
            {
                "pull_id": pull_id,
                "pulled_at": pulled_at,
                "season": season,
                "week": week,
                "position": position,
                "scoring": scoring,
                **row,
            }
            for row in rows
        ],
    )
    conn.commit()


def insert_injuries(conn: sqlite3.Connection, pull_id: int, rows: list[dict]) -> None:
    pulled_at = _now()
    conn.executemany(
        """
        INSERT INTO injuries_history
            (pull_id, pulled_at, player_id, status, status_short, injury_type, comment, injury_update_date)
        VALUES
            (:pull_id, :pulled_at, :player_id, :status, :status_short, :injury_type, :comment, :injury_update_date)
        """,
        [{"pull_id": pull_id, "pulled_at": pulled_at, **row} for row in rows],
    )
    conn.commit()


def get_last_two_ranking_pulls(conn: sqlite3.Connection, season: str, position: str, scoring: str) -> tuple[str | None, str | None]:
    """Return (previous_pulled_at, latest_pulled_at) distinct pull timestamps for this slice, most recent last."""
    rows = conn.execute(
        """
        SELECT DISTINCT pulled_at FROM rankings_history
        WHERE season = ? AND position = ? AND scoring = ?
        ORDER BY pulled_at DESC LIMIT 2
        """,
        (season, position, scoring),
    ).fetchall()
    timestamps = [r["pulled_at"] for r in rows]
    if len(timestamps) < 2:
        return (None, timestamps[0] if timestamps else None)
    return (timestamps[1], timestamps[0])


def get_rankings_at(conn: sqlite3.Connection, season: str, position: str, scoring: str, pulled_at: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT rh.*, p.player_name, p.team_id
        FROM rankings_history rh
        JOIN players p ON p.player_id = rh.player_id
        WHERE rh.season = ? AND rh.position = ? AND rh.scoring = ? AND rh.pulled_at = ?
        """,
        (season, position, scoring, pulled_at),
    ).fetchall()


def get_last_two_injury_pulls(conn: sqlite3.Connection) -> tuple[str | None, str | None]:
    rows = conn.execute(
        "SELECT DISTINCT pulled_at FROM injuries_history ORDER BY pulled_at DESC LIMIT 2"
    ).fetchall()
    timestamps = [r["pulled_at"] for r in rows]
    if len(timestamps) < 2:
        return (None, timestamps[0] if timestamps else None)
    return (timestamps[1], timestamps[0])


def get_injuries_at(conn: sqlite3.Connection, pulled_at: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT ih.*, p.player_name, p.team_id
        FROM injuries_history ih
        JOIN players p ON p.player_id = ih.player_id
        WHERE ih.pulled_at = ?
        """,
        (pulled_at,),
    ).fetchall()
