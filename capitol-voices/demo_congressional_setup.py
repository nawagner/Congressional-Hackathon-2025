#!/usr/bin/env python3
"""
Congressional Demo Setup for CapitolVoices
Downloads and processes a sample Congressional hearing for hackathon demonstration
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Optional imports for demo setup
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("⚠️  yt-dlp not available. Install with: pip install yt-dlp")

try:
    from pipelines.runner import run_pipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    print("⚠️  Pipeline not available. Install dependencies with: pip install -r requirements.txt")

# Sample Congressional hearing for demo (based on real committee structure)
DEMO_HEARING = {
    "hearing_id": "house-oversight-demo-2025",
    "title": "House Oversight Committee - Federal Agency Accountability and Transparency",
    "committee": "House Committee on Oversight and Accountability", 
    "date": "2025-01-15",
    "youtube_url": "https://www.youtube.com/watch?v=DEMO_HEARING_URL",  # Demo URL
    "duration_minutes": 120,
    "expected_speakers": 8,
    "description": "Demo hearing showcasing CapitolVoices capabilities with realistic Congressional structure"
}

# Committee roster for demo
DEMO_ROSTER = {
    "hearing_id": "house-oversight-demo-2025",
    "committee": "House Committee on Oversight and Accountability",
    "chair": {
        "name": "Rep. James Comer",
        "aliases": ["Chairman Comer", "Chair Comer", "Mr. Chairman"]
    },
    "ranking": {
        "name": "Rep. Jamie Raskin",
        "aliases": ["Ranking Member Raskin", "Mr. Raskin"]
    },
    "members": [
        "Rep. Andy Biggs", "Rep. Lauren Boebert", "Rep. Byron Donalds",
        "Rep. Anna Paulina Luna", "Rep. Nancy Mace", "Rep. Marjorie Taylor Greene"
    ],
    "witnesses": [
        "Dr. Anthony Fauci", "Dr. Francis Collins", "Dr. Lawrence Tabak"
    ]
}

def setup_directories():
    """Create necessary directories for demo"""
    dirs = ["data", "data/audio", "data/transcripts", "configs/rosters", "artifacts"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Created demo directories")

def download_demo_audio():
    """Download audio from demo Congressional hearing"""
    print("🎵 Downloading demo hearing audio...")
    
    # For demo purposes, we'll create a placeholder
    # In production, this would download from the actual YouTube URL
    audio_path = Path("data/audio/house-oversight-demo-2025.wav")
    
    if not audio_path.exists():
        print("⚠️  Demo audio file not found. Please provide a sample hearing audio file.")
        print("   Expected location: data/audio/house-oversight-demo-2025.wav")
        print("   You can download from a Congressional hearing YouTube URL using:")
        print("   yt-dlp --extract-audio --audio-format wav <youtube_url>")
        return None
    
    print(f"✅ Audio file ready: {audio_path}")
    return audio_path

def setup_demo_roster():
    """Create demo roster configuration"""
    roster_path = Path("configs/rosters/house-oversight-demo.json")
    
    with open(roster_path, 'w') as f:
        json.dump(DEMO_ROSTER, f, indent=2)
    
    print(f"✅ Created demo roster: {roster_path}")
    return roster_path

def setup_demo_database():
    """Initialize database with demo hearing metadata"""
    db_path = "data/hearings.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create tables if they don't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hearings(
            id TEXT PRIMARY KEY, 
            title TEXT, 
            committee TEXT, 
            date TEXT, 
            video_url TEXT,
            duration_minutes INTEGER,
            expected_speakers INTEGER
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS summaries(
            hearing_id TEXT, 
            type TEXT, 
            content_json TEXT, 
            PRIMARY KEY (hearing_id, type)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS segments(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            hearing_id TEXT, 
            start_s REAL, 
            end_s REAL, 
            speaker_key TEXT, 
            text TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS speakers(
            hearing_id TEXT,
            speaker_key TEXT,
            display_name TEXT,
            role TEXT,
            PRIMARY KEY (hearing_id, speaker_key)
        )
    """)
    
    # Insert demo hearing
    cur.execute("""
        REPLACE INTO hearings(id, title, committee, date, video_url, duration_minutes, expected_speakers)
        VALUES(?, ?, ?, ?, ?, ?, ?)
    """, (
        DEMO_HEARING["hearing_id"],
        DEMO_HEARING["title"], 
        DEMO_HEARING["committee"],
        DEMO_HEARING["date"],
        DEMO_HEARING["youtube_url"],
        DEMO_HEARING["duration_minutes"],
        DEMO_HEARING["expected_speakers"]
    ))
    
    # Insert speaker mappings
    speakers = [
        (DEMO_HEARING["hearing_id"], "chair", "Rep. James Comer", "Chair"),
        (DEMO_HEARING["hearing_id"], "ranking", "Rep. Jamie Raskin", "Ranking Member"),
        (DEMO_HEARING["hearing_id"], "witness_1", "Dr. Anthony Fauci", "Witness"),
        (DEMO_HEARING["hearing_id"], "witness_2", "Dr. Francis Collins", "Witness"),
        (DEMO_HEARING["hearing_id"], "witness_3", "Dr. Lawrence Tabak", "Witness"),
    ]
    
    for speaker in speakers:
        cur.execute("""
            REPLACE INTO speakers(hearing_id, speaker_key, display_name, role)
            VALUES(?, ?, ?, ?)
        """, speaker)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Initialized database with demo hearing: {DEMO_HEARING['hearing_id']}")

def create_demo_config():
    """Create demo configuration file"""
    config = {
        "hearing": {
            "id": DEMO_HEARING["hearing_id"],
            "committee": DEMO_HEARING["committee"],
            "title": DEMO_HEARING["title"],
            "date": DEMO_HEARING["date"],
            "video_url": DEMO_HEARING["youtube_url"]
        },
        "asr": {
            "engine": "whisper",
            "model": "large-v3",
            "vad": True,
            "beam_size": 5,
            "chunk_seconds": 600
        },
        "diarization": {
            "engine": "pyannote",
            "min_speakers": 3,
            "max_speakers": 12
        },
        "summary": {
            "mode": "extractive",
            "max_tokens": 1200
        },
        "storage": {
            "db_path": "data/hearings.db",
            "artifacts_dir": "artifacts"
        },
        "naming": {
            "roster_path": "configs/rosters/house-oversight-demo.json"
        }
    }
    
    config_path = Path("configs/demo_congressional.yaml")
    import yaml
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Created demo config: {config_path}")

def run_demo_processing():
    """Run the full pipeline on demo data"""
    print("🚀 Starting CapitolVoices processing pipeline...")
    
    if not PIPELINE_AVAILABLE:
        print("❌ Pipeline not available. Install dependencies first.")
        return False
    
    audio_path = Path("data/audio/house-oversight-demo-2025.wav")
    
    if not audio_path.exists():
        print("❌ Demo audio file not found. Please run download_demo_audio() first.")
        return False
    
    try:
        # Run the full pipeline
        run_pipeline(DEMO_HEARING["hearing_id"], str(audio_path))
        print("✅ Demo processing completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Demo processing failed: {e}")
        return False

def verify_demo_results():
    """Verify that demo processing produced expected results"""
    print("🔍 Verifying demo results...")
    
    conn = sqlite3.connect("data/hearings.db")
    cur = conn.cursor()
    
    # Check segments
    cur.execute("SELECT COUNT(*) FROM segments WHERE hearing_id = ?", (DEMO_HEARING["hearing_id"],))
    segment_count = cur.fetchone()[0]
    
    # Check summary
    cur.execute("SELECT content_json FROM summaries WHERE hearing_id = ? AND type = 'default'", (DEMO_HEARING["hearing_id"],))
    summary = cur.fetchone()
    
    # Check speakers
    cur.execute("SELECT COUNT(*) FROM speakers WHERE hearing_id = ?", (DEMO_HEARING["hearing_id"],))
    speaker_count = cur.fetchone()[0]
    
    conn.close()
    
    print(f"📊 Demo Results:")
    print(f"   - Segments generated: {segment_count}")
    print(f"   - Summary created: {'✅' if summary else '❌'}")
    print(f"   - Speakers identified: {speaker_count}")
    
    if segment_count > 0 and summary and speaker_count > 0:
        print("✅ Demo verification passed!")
        return True
    else:
        print("❌ Demo verification failed!")
        return False

def main():
    """Main demo setup function"""
    print("🏛️  CapitolVoices Congressional Demo Setup")
    print("=" * 50)
    
    # Setup steps
    setup_directories()
    setup_demo_roster()
    setup_demo_database()
    create_demo_config()
    
    # Download audio (placeholder for demo)
    audio_path = download_demo_audio()
    
    if audio_path and audio_path.exists():
        # Run processing
        success = run_demo_processing()
        
        if success:
            verify_demo_results()
            print("\n🎉 Demo setup complete!")
            print("\nNext steps:")
            print("1. Launch the web interface: streamlit run ui/app.py")
            print("2. Select 'house-oversight-demo-2025' from the dropdown")
            print("3. View the generated transcript and summary")
        else:
            print("\n❌ Demo setup failed during processing")
    else:
        print("\n⚠️  Demo setup incomplete - audio file needed")
        print("Please provide a sample Congressional hearing audio file at:")
        print("data/audio/house-oversight-demo-2025.wav")

if __name__ == "__main__":
    main()
