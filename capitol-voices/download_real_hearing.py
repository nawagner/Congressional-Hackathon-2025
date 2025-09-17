#!/usr/bin/env python3
"""
Download and process a real Congressional hearing for CapitolVoices demo
"""

import os
import json
import yt_dlp
from pathlib import Path
from datetime import datetime

# Real Congressional hearing examples (you can replace these with actual URLs)
REAL_HEARINGS = {
    "house_oversight_2024": {
        "hearing_id": "house-oversight-2024-12-15",
        "title": "House Oversight Committee - Federal Agency Oversight",
        "committee": "House Committee on Oversight and Accountability",
        "date": "2024-12-15",
        "youtube_url": "https://www.youtube.com/watch?v=REPLACE_WITH_REAL_URL",
        "expected_speakers": 8,
        "roster": {
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
    }
}

def download_hearing_audio(youtube_url: str, output_path: str):
    """Download audio from YouTube URL"""
    print(f"🎵 Downloading audio from: {youtube_url}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'extractaudio': True,
        'audioformat': 'wav',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            print(f"✅ Downloaded: {info.get('title', 'Unknown')}")
            print(f"   Duration: {info.get('duration', 0)} seconds")
            return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def create_real_roster(hearing_data: dict):
    """Create roster file for real hearing"""
    roster_path = Path(f"configs/rosters/{hearing_data['hearing_id']}.json")
    
    with open(roster_path, 'w') as f:
        json.dump(hearing_data['roster'], f, indent=2)
    
    print(f"✅ Created roster: {roster_path}")
    return roster_path

def setup_real_hearing(hearing_key: str = "house_oversight_2024"):
    """Setup a real Congressional hearing"""
    if hearing_key not in REAL_HEARINGS:
        print(f"❌ Unknown hearing: {hearing_key}")
        return False
    
    hearing_data = REAL_HEARINGS[hearing_key]
    
    print(f"🏛️  Setting up real hearing: {hearing_data['title']}")
    print(f"   Committee: {hearing_data['committee']}")
    print(f"   Date: {hearing_data['date']}")
    
    # Create directories
    Path("data/audio").mkdir(parents=True, exist_ok=True)
    Path("configs/rosters").mkdir(parents=True, exist_ok=True)
    
    # Download audio
    audio_path = f"data/audio/{hearing_data['hearing_id']}.wav"
    if not Path(audio_path).exists():
        if download_hearing_audio(hearing_data['youtube_url'], audio_path):
            print(f"✅ Audio ready: {audio_path}")
        else:
            print("❌ Audio download failed")
            return False
    else:
        print(f"✅ Audio already exists: {audio_path}")
    
    # Create roster
    create_real_roster(hearing_data)
    
    # Create config
    config = {
        "hearing": hearing_data,
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
            "engine": "sqlite",  # or "postgresql"
            "db_path": "data/hearings.db"
        },
        "naming": {
            "roster_path": f"configs/rosters/{hearing_data['hearing_id']}.json"
        }
    }
    
    config_path = Path(f"configs/{hearing_data['hearing_id']}.yaml")
    import yaml
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Created config: {config_path}")
    
    return True

def main():
    """Main function"""
    print("🏛️  Real Congressional Hearing Setup")
    print("=" * 50)
    
    print("Available hearings:")
    for key, hearing in REAL_HEARINGS.items():
        print(f"  - {key}: {hearing['title']}")
    
    print("\n⚠️  Note: You need to replace the YouTube URLs with real Congressional hearing URLs")
    print("   Find real hearings at: https://www.youtube.com/c/HouseOversightCommittee")
    
    # For now, just show the setup process
    print("\n🔧 Setup process:")
    print("1. Find a real Congressional hearing YouTube URL")
    print("2. Replace the URL in REAL_HEARINGS")
    print("3. Run: python download_real_hearing.py")
    print("4. Process: python -c \"from pipelines.runner import run_pipeline; run_pipeline('house-oversight-2024-12-15', 'data/audio/house-oversight-2024-12-15.wav')\"")

if __name__ == "__main__":
    main()
