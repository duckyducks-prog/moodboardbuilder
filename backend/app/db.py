import json
import sqlite3
import time
import uuid

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS boards (
    id            TEXT PRIMARY KEY,
    vibes         TEXT NOT NULL,
    media_type    TEXT NOT NULL DEFAULT 'both',
    style_profile TEXT NOT NULL DEFAULT '{}',
    created_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS rounds (
    id              TEXT PRIMARY KEY,
    board_id        TEXT NOT NULL REFERENCES boards(id),
    idx             INTEGER NOT NULL,
    parent_round_id TEXT,
    query           TEXT NOT NULL,
    results         TEXT NOT NULL,
    created_at      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS selections (
    id         TEXT PRIMARY KEY,
    board_id   TEXT NOT NULL REFERENCES boards(id),
    round_id   TEXT NOT NULL REFERENCES rounds(id),
    result     TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def create_board(vibes: str, media_type: str) -> str:
    board_id = new_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO boards (id, vibes, media_type, style_profile, created_at) VALUES (?, ?, ?, '{}', ?)",
            (board_id, vibes, media_type, time.time()),
        )
    return board_id


def get_board(board_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM boards WHERE id = ?", (board_id,)).fetchone()
    return dict(row) if row else None


def update_style_profile(board_id: str, profile: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE boards SET style_profile = ? WHERE id = ?",
            (json.dumps(profile), board_id),
        )


def create_round(board_id: str, idx: int, query: str, results: list, parent_round_id: str | None = None) -> str:
    round_id = new_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rounds (id, board_id, idx, parent_round_id, query, results, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (round_id, board_id, idx, parent_round_id, query, json.dumps(results), time.time()),
        )
    return round_id


def get_round(round_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM rounds WHERE id = ?", (round_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["results"] = json.loads(d["results"])
    return d


def get_rounds_for_board(board_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM rounds WHERE board_id = ? ORDER BY created_at", (board_id,)
        ).fetchall()
    rounds = []
    for row in rows:
        d = dict(row)
        d["results"] = json.loads(d["results"])
        rounds.append(d)
    return rounds


def add_selections(board_id: str, round_id: str, results: list[dict]) -> None:
    with get_conn() as conn:
        for result in results:
            conn.execute(
                "INSERT INTO selections (id, board_id, round_id, result, created_at) VALUES (?, ?, ?, ?, ?)",
                (new_id(), board_id, round_id, json.dumps(result), time.time()),
            )


def get_selections_for_board(board_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM selections WHERE board_id = ? ORDER BY created_at", (board_id,)
        ).fetchall()
    selections = []
    for row in rows:
        d = dict(row)
        d["result"] = json.loads(d["result"])
        selections.append(d)
    return selections


def seen_urls_for_board(board_id: str) -> set[str]:
    """Every page URL and image URL the user has already been shown on this board."""
    seen: set[str] = set()
    for rnd in get_rounds_for_board(board_id):
        for result in rnd["results"]:
            if result.get("url"):
                seen.add(result["url"])
            if result.get("image_url"):
                seen.add(result["image_url"])
    return seen
