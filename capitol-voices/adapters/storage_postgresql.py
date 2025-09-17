from __future__ import annotations
import json
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Iterable, Dict, Any, List, Optional
from datetime import datetime
from core.interfaces import Segment, Storage

class PostgreSQLStorage(Storage):
    """PostgreSQL storage adapter for Congressional hearing data.
    
    Optimized for handling large datasets from YouTube videos with:
    - Full-text search capabilities
    - Efficient indexing for timestamps and speakers
    - Support for complex queries across hearings
    - JSON storage for flexible metadata
    """
    
    def __init__(self, connection_string: str, schema: str = "capitol_voices"):
        self.connection_string = connection_string
        self.schema = schema
        self._init_database()
    
    def _get_connection(self):
        """Get database connection with proper configuration"""
        conn = psycopg2.connect(self.connection_string)
        conn.autocommit = False
        return conn
    
    def _init_database(self):
        """Initialize database schema and tables"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Create schema if it doesn't exist
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
                
                # Create hearings table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.hearings (
                        id VARCHAR(255) PRIMARY KEY,
                        title TEXT NOT NULL,
                        committee VARCHAR(255) NOT NULL,
                        date DATE NOT NULL,
                        video_url TEXT,
                        youtube_video_id VARCHAR(50),
                        duration_seconds INTEGER,
                        duration_minutes INTEGER,
                        expected_speakers INTEGER,
                        processing_status VARCHAR(50) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB
                    )
                """)
                
                # Create speakers table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.speakers (
                        hearing_id VARCHAR(255) REFERENCES {self.schema}.hearings(id) ON DELETE CASCADE,
                        speaker_key VARCHAR(100) NOT NULL,
                        display_name VARCHAR(255),
                        role VARCHAR(100),
                        committee_position VARCHAR(100),
                        party VARCHAR(50),
                        state VARCHAR(10),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (hearing_id, speaker_key)
                    )
                """)
                
                # Create segments table with optimized indexing
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.segments (
                        id SERIAL PRIMARY KEY,
                        hearing_id VARCHAR(255) REFERENCES {self.schema}.hearings(id) ON DELETE CASCADE,
                        start_s DECIMAL(10,3) NOT NULL,
                        end_s DECIMAL(10,3) NOT NULL,
                        speaker_key VARCHAR(100),
                        text TEXT NOT NULL,
                        confidence DECIMAL(5,4),
                        word_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create summaries table
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.summaries (
                        hearing_id VARCHAR(255) REFERENCES {self.schema}.hearings(id) ON DELETE CASCADE,
                        type VARCHAR(50) NOT NULL,
                        content_json JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (hearing_id, type)
                    )
                """)
                
                # Create processing runs table for provenance
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.processing_runs (
                        id SERIAL PRIMARY KEY,
                        hearing_id VARCHAR(255) REFERENCES {self.schema}.hearings(id) ON DELETE CASCADE,
                        run_type VARCHAR(50) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        duration_seconds INTEGER,
                        metadata JSONB,
                        error_message TEXT
                    )
                """)
                
                # Create indexes for performance
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_segments_hearing_id 
                    ON {self.schema}.segments(hearing_id)
                """)
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_segments_timestamp 
                    ON {self.schema}.segments(hearing_id, start_s, end_s)
                """)
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_segments_speaker 
                    ON {self.schema}.segments(hearing_id, speaker_key)
                """)
                
                # Full-text search index
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_segments_text_search 
                    ON {self.schema}.segments USING gin(to_tsvector('english', text))
                """)
                
                # Committee and date indexes
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_hearings_committee 
                    ON {self.schema}.hearings(committee)
                """)
                
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_hearings_date 
                    ON {self.schema}.hearings(date)
                """)
                
                # JSONB indexes for metadata
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_hearings_metadata 
                    ON {self.schema}.hearings USING gin(metadata)
                """)
                
                conn.commit()
    
    def write_segments(self, hearing_id: str, segments: Iterable[Segment]) -> None:
        """Write segments to PostgreSQL with batch processing"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Prepare batch insert data
                segment_data = []
                for seg in segments:
                    word_count = len(seg.get("text", "").split()) if seg.get("text") else 0
                    segment_data.append((
                        hearing_id,
                        seg.get("start_s", 0.0),
                        seg.get("end_s", 0.0),
                        seg.get("speaker_key"),
                        seg.get("text", ""),
                        seg.get("confidence"),
                        word_count
                    ))
                
                # Batch insert
                cur.executemany(f"""
                    INSERT INTO {self.schema}.segments 
                    (hearing_id, start_s, end_s, speaker_key, text, confidence, word_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, segment_data)
                
                conn.commit()
    
    def write_summary(self, hearing_id: str, summary: Dict[str, Any]) -> None:
        """Write summary to PostgreSQL"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.schema}.summaries (hearing_id, type, content_json)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (hearing_id, type) 
                    DO UPDATE SET 
                        content_json = EXCLUDED.content_json,
                        updated_at = CURRENT_TIMESTAMP
                """, (hearing_id, "default", json.dumps(summary)))
                
                conn.commit()
    
    def read_segments(self, hearing_id: str) -> List[Segment]:
        """Read segments from PostgreSQL"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT start_s, end_s, speaker_key, text, confidence
                    FROM {self.schema}.segments
                    WHERE hearing_id = %s
                    ORDER BY start_s
                """, (hearing_id,))
                
                segments = []
                for row in cur.fetchall():
                    segments.append({
                        "hearing_id": hearing_id,
                        "start_s": float(row["start_s"]),
                        "end_s": float(row["end_s"]),
                        "speaker_key": row["speaker_key"],
                        "text": row["text"],
                        "confidence": float(row["confidence"]) if row["confidence"] else None
                    })
                
                return segments
    
    def read_summary(self, hearing_id: str) -> Optional[Dict[str, Any]]:
        """Read summary from PostgreSQL"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT content_json
                    FROM {self.schema}.summaries
                    WHERE hearing_id = %s AND type = 'default'
                """, (hearing_id,))
                
                row = cur.fetchone()
                if row:
                    return json.loads(row[0])
                return None
    
    def write_hearing_metadata(self, hearing_id: str, metadata: Dict[str, Any]) -> None:
        """Write hearing metadata to PostgreSQL"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Extract YouTube video ID from URL
                youtube_video_id = None
                if metadata.get("video_url"):
                    import re
                    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)', metadata["video_url"])
                    if match:
                        youtube_video_id = match.group(1)
                
                cur.execute(f"""
                    INSERT INTO {self.schema}.hearings 
                    (id, title, committee, date, video_url, youtube_video_id, 
                     duration_seconds, duration_minutes, expected_speakers, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        committee = EXCLUDED.committee,
                        date = EXCLUDED.date,
                        video_url = EXCLUDED.video_url,
                        youtube_video_id = EXCLUDED.youtube_video_id,
                        duration_seconds = EXCLUDED.duration_seconds,
                        duration_minutes = EXCLUDED.duration_minutes,
                        expected_speakers = EXCLUDED.expected_speakers,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    hearing_id,
                    metadata.get("title", ""),
                    metadata.get("committee", ""),
                    metadata.get("date"),
                    metadata.get("video_url"),
                    youtube_video_id,
                    metadata.get("duration_seconds"),
                    metadata.get("duration_minutes"),
                    metadata.get("expected_speakers"),
                    json.dumps(metadata)
                ))
                
                conn.commit()
    
    def write_speakers(self, hearing_id: str, speakers: List[Dict[str, Any]]) -> None:
        """Write speaker information to PostgreSQL"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Clear existing speakers for this hearing
                cur.execute(f"""
                    DELETE FROM {self.schema}.speakers WHERE hearing_id = %s
                """, (hearing_id,))
                
                # Insert new speakers
                speaker_data = []
                for speaker in speakers:
                    speaker_data.append((
                        hearing_id,
                        speaker.get("speaker_key"),
                        speaker.get("display_name"),
                        speaker.get("role"),
                        speaker.get("committee_position"),
                        speaker.get("party"),
                        speaker.get("state")
                    ))
                
                cur.executemany(f"""
                    INSERT INTO {self.schema}.speakers 
                    (hearing_id, speaker_key, display_name, role, committee_position, party, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, speaker_data)
                
                conn.commit()
    
    def search_hearings(self, query: str, committee: str = None, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """Search hearings with full-text search and filters"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                sql = f"""
                    SELECT DISTINCT h.id, h.title, h.committee, h.date, h.video_url, h.duration_minutes
                    FROM {self.schema}.hearings h
                    JOIN {self.schema}.segments s ON h.id = s.hearing_id
                    WHERE to_tsvector('english', s.text) @@ plainto_tsquery('english', %s)
                """
                params = [query]
                
                if committee:
                    sql += " AND h.committee ILIKE %s"
                    params.append(f"%{committee}%")
                
                if date_from:
                    sql += " AND h.date >= %s"
                    params.append(date_from)
                
                if date_to:
                    sql += " AND h.date <= %s"
                    params.append(date_to)
                
                sql += " ORDER BY h.date DESC, h.title"
                
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]
    
    def get_hearing_statistics(self, hearing_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a hearing"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Basic hearing info
                cur.execute(f"""
                    SELECT h.*, COUNT(DISTINCT s.speaker_key) as unique_speakers,
                           COUNT(s.id) as total_segments,
                           SUM(s.word_count) as total_words,
                           AVG(s.word_count) as avg_words_per_segment
                    FROM {self.schema}.hearings h
                    LEFT JOIN {self.schema}.segments s ON h.id = s.hearing_id
                    WHERE h.id = %s
                    GROUP BY h.id
                """, (hearing_id,))
                
                hearing_stats = cur.fetchone()
                if not hearing_stats:
                    return {}
                
                # Speaker statistics
                cur.execute(f"""
                    SELECT speaker_key, COUNT(*) as segment_count, 
                           SUM(word_count) as word_count,
                           MIN(start_s) as first_speech,
                           MAX(end_s) as last_speech
                    FROM {self.schema}.segments
                    WHERE hearing_id = %s AND speaker_key IS NOT NULL
                    GROUP BY speaker_key
                    ORDER BY word_count DESC
                """, (hearing_id,))
                
                speaker_stats = [dict(row) for row in cur.fetchall()]
                
                return {
                    "hearing": dict(hearing_stats),
                    "speakers": speaker_stats,
                    "total_duration": hearing_stats["duration_seconds"],
                    "total_segments": hearing_stats["total_segments"],
                    "total_words": hearing_stats["total_words"],
                    "unique_speakers": hearing_stats["unique_speakers"]
                }
    
    def write_run(self, run_data: str) -> None:
        """Write processing run metadata"""
        try:
            run_info = json.loads(run_data)
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        INSERT INTO {self.schema}.processing_runs 
                        (hearing_id, run_type, status, duration_seconds, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        run_info.get("hearing_id"),
                        run_info.get("run_type", "full_pipeline"),
                        run_info.get("status", "completed"),
                        run_info.get("duration_seconds"),
                        run_info
                    ))
                    conn.commit()
        except Exception as e:
            print(f"Warning: Could not write run data: {e}")
