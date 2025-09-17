from __future__ import annotations
import sqlite3, json
from typing import Iterable, List, Optional, Dict, Any
from core.interfaces import Segment, Storage

SCHEMA = [
"""CREATE TABLE IF NOT EXISTS hearings(
    id TEXT PRIMARY KEY, title TEXT, committee TEXT, date TEXT, video_url TEXT
)""",
"""CREATE TABLE IF NOT EXISTS speakers(
    hearing_id TEXT, speaker_key TEXT, display_name TEXT, role TEXT,
    PRIMARY KEY (hearing_id, speaker_key)
)""",
"""CREATE TABLE IF NOT EXISTS segments(
    id INTEGER PRIMARY KEY AUTOINCREMENT, hearing_id TEXT, start_s REAL, end_s REAL,
    speaker_key TEXT, text TEXT
)""",
"""CREATE TABLE IF NOT EXISTS summaries(
    hearing_id TEXT, type TEXT, content_json TEXT,
    PRIMARY KEY (hearing_id, type)
)""",
"""CREATE TABLE IF NOT EXISTS runs(
    run_id TEXT PRIMARY KEY, hearing_id TEXT, started_at REAL, finished_at REAL,
    asr_engine TEXT, asr_model TEXT, diar_engine TEXT, summarizer TEXT, git_sha TEXT,
    audio_sha256 TEXT, config_json TEXT
)"""
]

class SQLiteStorage(Storage):
    def __init__(self, db_path: str = "data/hearings.db"):
        self.db_path = db_path
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        for stmt in SCHEMA:
            cur.execute(stmt)
        conn.commit(); conn.close()

    def write_segments(self, hearing_id: str, segments: Iterable[Segment]) -> None:
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        cur.execute("DELETE FROM segments WHERE hearing_id=?", (hearing_id,))
        cur.executemany("INSERT INTO segments(hearing_id,start_s,end_s,speaker_key,text) VALUES(?,?,?,?,?)",
                        [(hearing_id, s["start_s"], s["end_s"], s.get("speaker_key"), s.get("text","")) for s in segments])
        conn.commit(); conn.close()

    def write_summary(self, hearing_id: str, summary: Dict[str, Any]) -> None:
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        cur.execute("REPLACE INTO summaries(hearing_id,type,content_json) VALUES(?,?,?)",
                    (hearing_id, "default", json.dumps(summary)))
        conn.commit(); conn.close()

    def read_segments(self, hearing_id: str) -> List[Segment]:
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        cur.execute("SELECT start_s,end_s,speaker_key,text FROM segments WHERE hearing_id=? ORDER BY start_s", (hearing_id,))
        rows = cur.fetchall(); conn.close()
        return [{"hearing_id": hearing_id, "start_s": r[0], "end_s": r[1], "speaker_key": r[2], "text": r[3]} for r in rows]

    def read_summary(self, hearing_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        cur.execute("SELECT content_json FROM summaries WHERE hearing_id=? AND type='default'", (hearing_id,))
        row = cur.fetchone(); conn.close()
        return json.loads(row[0]) if row else None

    # Provenance writes
    def write_run(self, meta_json: str) -> None:
        data = json.loads(meta_json)
        conn = sqlite3.connect(self.db_path); cur = conn.cursor()
        cur.execute("REPLACE INTO runs(run_id, hearing_id, started_at, finished_at, asr_engine, asr_model, diar_engine, summarizer, git_sha, audio_sha256, config_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (data.get("run_id"), data.get("hearing_id"), data.get("started_at"), data.get("finished_at"), data.get("asr_engine"),
                     data.get("asr_model"), data.get("diar_engine"), data.get("summarizer"), data.get("git_sha"), data.get("audio_sha256"), data.get("config_json")))
        conn.commit(); conn.close()
