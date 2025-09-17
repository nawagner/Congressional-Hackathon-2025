#!/usr/bin/env python3
"""Scrape hearing details from docs.house.gov and output JSON."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib import request
from urllib.error import HTTPError, URLError

import sys

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency check
    raise SystemExit(
        "beautifulsoup4 is required. Install it with 'pip install beautifulsoup4'."
    ) from exc


DEFAULT_URL = "https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID=118596"
DEFAULT_DB_PATH = Path(__file__).resolve().with_name("hearings.db")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_html(url: str) -> str:
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    with request.urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Unexpected response status {resp.status} for {url}")
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def parse_hearing(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    panel = soup.find("div", id="previewPanel")
    if panel is None:
        raise ValueError("Could not locate hearing preview panel in page")

    title = extract_title(panel)
    date_info = extract_date_time(panel)
    location = extract_location(panel)
    witnesses = extract_witnesses(panel)

    data = {
        "title": title,
        "date": date_info["date"],
        "time": date_info["time"],
        "datetime": date_info["datetime"],
        "location": location,
        "witnesses": witnesses,
    }
    return data


def extract_title(panel: BeautifulSoup) -> str:
    header = panel.find("h1")
    if header is None:
        raise ValueError("Missing hearing title header")

    raw_text = header.find(string=True, recursive=False)
    if raw_text:
        text = raw_text.strip()
    else:
        text = header.get_text(separator=" ", strip=True)

    if text.lower().startswith("hearing:"):
        text = text.split(":", 1)[1].strip()

    return " ".join(text.split())


def extract_date_time(panel: BeautifulSoup) -> Dict[str, str]:
    time_node = panel.find("p", class_="meetingTime")
    if time_node is None:
        raise ValueError("Missing meeting time block")

    display_text = " ".join(time_node.get_text(strip=True).split())
    try:
        dt_obj = datetime.strptime(display_text, "%A, %B %d, %Y (%I:%M %p)")
    except ValueError as exc:
        raise ValueError(f"Unable to parse meeting time: '{display_text}'") from exc

    return {
        "date": dt_obj.strftime("%Y-%m-%d"),
        "time": dt_obj.strftime("%H:%M"),
        "datetime": dt_obj.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def extract_location(panel: BeautifulSoup) -> str:
    location_node = panel.find("blockquote", class_="location")
    if location_node is None:
        raise ValueError("Missing location blockquote")

    parts = list(location_node.stripped_strings)
    return ", ".join(parts)


def extract_witnesses(panel: BeautifulSoup) -> List[Dict[str, str]]:
    witnesses: List[Dict[str, str]] = []
    for block in panel.find_all("div", class_="witnessPanel"):
        info = block.find("p")
        if info is None:
            continue

        name_node = info.find("strong")
        name = name_node.get_text(" ", strip=True) if name_node else ""

        title_node = info.find("small")
        title = title_node.get_text(" ", strip=True) if title_node else ""

        if name:
            witnesses.append({"name": name, "title": title})
    return witnesses


def run(url: str) -> Dict[str, Any]:
    html = fetch_html(url)
    return parse_hearing(html)


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS hearings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            date TEXT,
            time TEXT,
            datetime TEXT,
            location TEXT,
            scraped_at TEXT
        );

        CREATE TABLE IF NOT EXISTS witnesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hearing_id INTEGER NOT NULL,
            name TEXT,
            title TEXT,
            FOREIGN KEY (hearing_id) REFERENCES hearings(id) ON DELETE CASCADE
        );
        """
    )


def store_hearing(conn: sqlite3.Connection, url: str, data: Dict[str, Any]) -> None:
    ensure_schema(conn)

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conn.execute(
        """
        INSERT INTO hearings (url, title, date, time, datetime, location, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title = excluded.title,
            date = excluded.date,
            time = excluded.time,
            datetime = excluded.datetime,
            location = excluded.location,
            scraped_at = excluded.scraped_at
        """,
        (
            url,
            data.get("title"),
            data.get("date"),
            data.get("time"),
            data.get("datetime"),
            data.get("location"),
            scraped_at,
        ),
    )

    hearing_id = conn.execute(
        "SELECT id FROM hearings WHERE url = ?",
        (url,),
    ).fetchone()[0]

    conn.execute("DELETE FROM witnesses WHERE hearing_id = ?", (hearing_id,))
    conn.executemany(
        "INSERT INTO witnesses (hearing_id, name, title) VALUES (?, ?, ?)",
        (
            (hearing_id, witness.get("name"), witness.get("title"))
            for witness in data.get("witnesses", [])
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Hearing page to scrape")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="SQLite database file to write results (default: %(default)s)",
    )
    args = parser.parse_args()

    try:
        data = run(args.url)
    except (HTTPError, URLError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    with sqlite3.connect(args.db) as conn:
        store_hearing(conn, args.url, data)
        conn.commit()

    json.dump(data, fp=sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
