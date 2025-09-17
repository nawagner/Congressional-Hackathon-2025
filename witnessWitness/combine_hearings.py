#!/usr/bin/env python3
"""Merge House and Senate hearings databases into a unified schema."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
HOUSE_DB = BASE_DIR / "hearings.db"
SENATE_DB = BASE_DIR / "senate_hearings.sqlite"
TARGET_DB = BASE_DIR / "hearings_combined.db"


def normalize_date(raw: Optional[str]) -> Optional[str]:
    """Convert incoming date strings to ISO format (YYYY-MM-DD) when possible."""
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None

    # House data already uses ISO dates, so accept it as-is.
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw  # Fall back to the original string if it is in an unknown format.


def init_target_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        DROP TABLE IF EXISTS witnesses;
        DROP TABLE IF EXISTS hearings;

        CREATE TABLE hearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chamber TEXT NOT NULL,
            source_hearing_id TEXT,
            event_id INTEGER,
            url TEXT,
            title TEXT,
            date TEXT,
            time TEXT,
            datetime TEXT,
            location TEXT,
            committee TEXT,
            tags TEXT,
            scraped_at TEXT,
            witness_list_pdf TEXT
        );

        CREATE TABLE witnesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hearing_id INTEGER NOT NULL,
            name TEXT,
            title TEXT,
            truth_in_testimony_pdf TEXT,
            FOREIGN KEY (hearing_id) REFERENCES hearings(id) ON DELETE CASCADE
        );

        CREATE INDEX idx_hearings_chamber_source ON hearings(chamber, source_hearing_id);
        CREATE INDEX idx_witnesses_hearing ON witnesses(hearing_id);
        """
    )
    conn.commit()


def merge_house_data(house_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> Dict[int, int]:
    mapping: Dict[int, int] = {}
    house_conn.row_factory = sqlite3.Row
    cur = house_conn.cursor()

    hearings = cur.execute(
        """
        SELECT id, url, event_id, title, date, time, datetime, location, scraped_at, witness_list_pdf
        FROM hearings
        ORDER BY id
        """
    ).fetchall()

    insert_hearing = target_conn.execute
    for row in hearings:
        cursor = insert_hearing(
            """
            INSERT INTO hearings (
                chamber, source_hearing_id, event_id, url, title, date, time, datetime,
                location, committee, tags, scraped_at, witness_list_pdf
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "house",
                str(row["event_id"]) if row["event_id"] is not None else None,
                row["event_id"],
                row["url"],
                row["title"],
                normalize_date(row["date"]),
                row["time"],
                row["datetime"],
                row["location"],
                None,
                None,
                row["scraped_at"],
                row["witness_list_pdf"],
            ),
        )
        mapping[row["id"]] = cursor.lastrowid

    target_conn.commit()

    witnesses = cur.execute(
        """
        SELECT hearing_id, name, title, truth_in_testimony_pdf
        FROM witnesses
        ORDER BY id
        """
    ).fetchall()

    target_conn.executemany(
        """
        INSERT INTO witnesses (hearing_id, name, title, truth_in_testimony_pdf)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                mapping[row["hearing_id"]],
                row["name"],
                row["title"],
                row["truth_in_testimony_pdf"],
            )
            for row in witnesses
        ],
    )

    target_conn.commit()
    return mapping


def merge_senate_data(senate_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> None:
    senate_conn.row_factory = sqlite3.Row
    cur = senate_conn.cursor()

    hearings = cur.execute(
        """
        SELECT hearing_id, title, hearing_date, committee, tags
        FROM hearings
        ORDER BY hearing_id
        """
    ).fetchall()

    insert_hearing = target_conn.execute
    senate_id_map: Dict[int, int] = {}

    for row in hearings:
        cursor = insert_hearing(
            """
            INSERT INTO hearings (
                chamber, source_hearing_id, event_id, url, title, date, time, datetime,
                location, committee, tags, scraped_at, witness_list_pdf
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "senate",
                str(row["hearing_id"]),
                None,
                None,
                row["title"],
                normalize_date(row["hearing_date"]),
                None,
                None,
                None,
                row["committee"],
                row["tags"],
                None,
                None,
            ),
        )
        senate_id_map[row["hearing_id"]] = cursor.lastrowid

    target_conn.commit()

    witness_rows = []
    for hearing_id, combined_id in senate_id_map.items():
        witnesses = cur.execute(
            """
            SELECT w.name
            FROM hearing_witnesses hw
            JOIN witnesses w ON w.witness_id = hw.witness_id
            WHERE hw.hearing_id = ?
            ORDER BY w.name
            """,
            (hearing_id,),
        ).fetchall()
        for witness in witnesses:
            witness_rows.append((combined_id, witness["name"], None, None))

    if witness_rows:
        target_conn.executemany(
            """
            INSERT INTO witnesses (hearing_id, name, title, truth_in_testimony_pdf)
            VALUES (?, ?, ?, ?)
            """,
            witness_rows,
        )
        target_conn.commit()


def main() -> None:
    if not HOUSE_DB.exists():
        raise FileNotFoundError(f"House database not found at {HOUSE_DB}")
    if not SENATE_DB.exists():
        raise FileNotFoundError(f"Senate database not found at {SENATE_DB}")

    if TARGET_DB.exists():
        TARGET_DB.unlink()

    with sqlite3.connect(HOUSE_DB) as house_conn, sqlite3.connect(SENATE_DB) as senate_conn, sqlite3.connect(TARGET_DB) as target_conn:
        init_target_db(target_conn)
        merge_house_data(house_conn, target_conn)
        merge_senate_data(senate_conn, target_conn)


if __name__ == "__main__":
    main()
