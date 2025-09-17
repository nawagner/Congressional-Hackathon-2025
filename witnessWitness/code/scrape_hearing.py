#!/usr/bin/env python3
"""Scrape hearing details from docs.house.gov and output JSON."""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
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
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "hearings.db"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
EVENT_URL_TEMPLATE = "https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID={event_id:d}"


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
    committee = extract_committee(panel)

    return {
        "title": title,
        "date": date_info["date"],
        "time": date_info["time"],
        "datetime": date_info["datetime"],
        "location": location,
        "witnesses": witnesses,
        "committee": committee,
    }


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
            truth_pdf = extract_truth_in_testimony(block)
            witnesses.append(
                {
                    "name": name,
                    "title": title,
                    "truth_in_testimony_pdf": truth_pdf,
                }
            )
    return witnesses


def extract_committee(panel: BeautifulSoup) -> Optional[str]:
    header = panel.find("h1")
    if header is None:
        return None

    committee_texts: List[str] = []
    for block in header.find_all("blockquote"):
        text = " ".join(block.stripped_strings)
        normalized = " ".join(text.split())
        if normalized:
            committee_texts.append(normalized)

    if committee_texts:
        return "; ".join(dict.fromkeys(committee_texts))

    fallback = panel.find("p", class_="committeeName")
    if fallback:
        text = " ".join(fallback.stripped_strings)
        normalized = " ".join(text.split())
        if normalized:
            return normalized

    return None


def extract_truth_in_testimony(block: BeautifulSoup) -> Optional[str]:
    for li in block.find_all("li"):
        text = li.get_text(" ", strip=True).lower()
        if "truth in testimony" in text:
            link = li.find("a", href=True)
            if link:
                return link["href"].strip()
    return None


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
            event_id INTEGER,
            title TEXT,
            date TEXT,
            time TEXT,
            datetime TEXT,
            location TEXT,
            committee TEXT,
            scraped_at TEXT
        );

        CREATE TABLE IF NOT EXISTS witnesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hearing_id INTEGER NOT NULL,
            name TEXT,
            title TEXT,
            truth_in_testimony_pdf TEXT,
            FOREIGN KEY (hearing_id) REFERENCES hearings(id) ON DELETE CASCADE
        );
        """
    )

    _ensure_hearings_columns(conn)
    _ensure_witness_columns(conn)


def _ensure_hearings_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(hearings)")}
    if "event_id" not in columns:
        conn.execute("ALTER TABLE hearings ADD COLUMN event_id INTEGER")
    if "committee" not in columns:
        conn.execute("ALTER TABLE hearings ADD COLUMN committee TEXT")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_hearings_event_id ON hearings(event_id)"
    )


def _ensure_witness_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(witnesses)")}
    if "truth_in_testimony_pdf" not in columns:
        conn.execute("ALTER TABLE witnesses ADD COLUMN truth_in_testimony_pdf TEXT")


def store_hearing(
    conn: sqlite3.Connection, url: str, event_id: Optional[int], data: Dict[str, Any]
) -> None:
    ensure_schema(conn)

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    conn.execute(
        """
        INSERT INTO hearings (url, event_id, title, date, time, datetime, location, committee, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            event_id = COALESCE(excluded.event_id, hearings.event_id),
            title = excluded.title,
            date = excluded.date,
            time = excluded.time,
            datetime = excluded.datetime,
            location = excluded.location,
            committee = excluded.committee,
            scraped_at = excluded.scraped_at
        """,
        (
            url,
            event_id,
            data.get("title"),
            data.get("date"),
            data.get("time"),
            data.get("datetime"),
            data.get("location"),
            data.get("committee"),
            scraped_at,
        ),
    )

    hearing_id = conn.execute(
        "SELECT id FROM hearings WHERE url = ?",
        (url,),
    ).fetchone()[0]

    conn.execute("DELETE FROM witnesses WHERE hearing_id = ?", (hearing_id,))
    conn.executemany(
        "INSERT INTO witnesses (hearing_id, name, title, truth_in_testimony_pdf) VALUES (?, ?, ?, ?)",
        (
            (
                hearing_id,
                witness.get("name"),
                witness.get("title"),
                witness.get("truth_in_testimony_pdf"),
            )
            for witness in data.get("witnesses", [])
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Scrape a single hearing URL (default: latest known)")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="SQLite database file to write results (default: %(default)s)",
    )
    parser.add_argument(
        "--start-id",
        type=int,
        help="First EventID (inclusive) to scrape when crawling a range",
    )
    parser.add_argument(
        "--end-id",
        type=int,
        help="Last EventID (inclusive) to scrape when crawling a range",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to sleep between requests when crawling a range",
    )
    parser.add_argument(
        "--checkpoint-dir",
        help="Directory to write checkpoint batches and progress when crawling a range",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Number of successful scrapes between checkpoints (default: %(default)s)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of concurrent requests when crawling a range (default: %(default)s)",
    )
    args = parser.parse_args()

    if args.start_id is not None or args.end_id is not None:
        if args.start_id is None or args.end_id is None:
            parser.error("--start-id and --end-id must be provided together")
        if args.start_id > args.end_id:
            parser.error("--start-id must be less than or equal to --end-id")
        if args.batch_size <= 0:
            parser.error("--batch-size must be a positive integer")
        if args.workers <= 0:
            parser.error("--workers must be a positive integer")

        results = crawl_range(
            start_id=args.start_id,
            end_id=args.end_id,
            db_path=args.db,
            delay=args.delay,
            checkpoint_dir=args.checkpoint_dir,
            batch_size=args.batch_size,
            workers=args.workers,
        )
    else:
        url = args.url or DEFAULT_URL
        try:
            data = run(url)
        except (HTTPError, URLError, RuntimeError, ValueError) as exc:
            parser.error(str(exc))
        event_id = extract_event_id(url)
        with sqlite3.connect(args.db) as conn:
            store_hearing(conn, url, event_id, data)
            conn.commit()
        data_with_meta = {**data, "url": url, "event_id": event_id}
        results = data_with_meta

    json.dump(results, fp=sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def scrape_event(event_id: int) -> Optional[Dict[str, Any]]:
    url = EVENT_URL_TEMPLATE.format(event_id=event_id)
    try:
        data = run(url)
    except HTTPError as exc:
        if getattr(exc, "code", None) == 404:
            return None
        _log_error(f"HTTP error for {event_id} ({url}): {exc}")
        return None
    except (URLError, RuntimeError, ValueError) as exc:
        _log_error(f"Failed to scrape {event_id} ({url}): {exc}")
        return None

    return {"event_id": event_id, "url": url, "data": data}


def crawl_range(
    start_id: int,
    end_id: int,
    db_path: str,
    delay: float = 0.0,
    checkpoint_dir: Optional[str] = None,
    batch_size: int = 200,
    workers: int = 1,
) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    checkpoint_path = Path(checkpoint_dir).resolve() if checkpoint_dir else None
    if checkpoint_path:
        checkpoint_path.mkdir(parents=True, exist_ok=True)

    batch_records: List[Dict[str, Any]] = []
    batch_index = 1
    total_success = 0
    max_event_id: Optional[int] = None

    event_ids = list(range(start_id, end_id + 1))

    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)

        def process(result: Dict[str, Any]) -> None:
            nonlocal batch_records, batch_index, total_success, max_event_id

            event_id = result["event_id"]
            url = result["url"]
            data = result["data"]

            store_hearing(conn, url, event_id, data)
            conn.commit()

            record = {**data, "url": url, "event_id": event_id}
            collected.append(record)
            batch_records.append(record)
            total_success += 1
            max_event_id = event_id if max_event_id is None else max(max_event_id, event_id)

            if checkpoint_path:
                write_progress_checkpoint(
                    checkpoint_path,
                    event_id,
                    total_success,
                    max_event_id,
                )
                if len(batch_records) >= batch_size:
                    write_batch_checkpoint(
                        checkpoint_path,
                        batch_index,
                        batch_records,
                        total_success=total_success,
                        final=False,
                    )
                    batch_records = []
                    batch_index += 1

            if delay > 0:
                time.sleep(delay)

        if workers <= 1:
            for event_id in event_ids:
                result = scrape_event(event_id)
                if result is None:
                    continue
                process(result)
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(scrape_event, event_id): event_id for event_id in event_ids
                }
                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as exc:  # pragma: no cover - defensive
                        event_id = futures[future]
                        _log_error(f"Worker failed for {event_id}: {exc}")
                        continue
                    if result is None:
                        continue
                    process(result)

    if checkpoint_path and batch_records:
        write_batch_checkpoint(
            checkpoint_path,
            batch_index,
            batch_records,
            total_success=total_success,
            final=True,
        )

    collected.sort(key=lambda item: item.get("event_id", 0))
    return collected


def extract_event_id(url: str) -> Optional[int]:
    try:
        return int(url.rsplit("=", 1)[-1])
    except ValueError:
        return None


def write_progress_checkpoint(
    checkpoint_dir: Path,
    event_id: int,
    total_success: int,
    max_event_id: Optional[int],
) -> None:
    payload = {
        "last_event_id": event_id,
        "total_successful": total_success,
        "max_event_id": max_event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    progress_path = checkpoint_dir / "progress.json"
    with progress_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def write_batch_checkpoint(
    checkpoint_dir: Path,
    batch_index: int,
    records: List[Dict[str, Any]],
    *,
    total_success: int,
    final: bool,
) -> None:
    if not records:
        return

    sorted_records = sorted(records, key=lambda r: r.get("event_id", 0))
    first_event = sorted_records[0].get("event_id")
    last_event = sorted_records[-1].get("event_id")
    suffix = "_partial" if final else ""
    filename = (
        f"batch_{batch_index:04d}_{first_event}-{last_event}{suffix}.json"
        if first_event is not None and last_event is not None
        else f"batch_{batch_index:04d}{suffix}.json"
    )
    checkpoint_file = checkpoint_dir / filename
    payload = {
        "batch_index": batch_index,
        "count": len(records),
        "first_event_id": first_event,
        "last_event_id": last_event,
        "total_successful": total_success,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "records": sorted_records,
    }
    with checkpoint_file.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def _log_error(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == "__main__":
    main()
