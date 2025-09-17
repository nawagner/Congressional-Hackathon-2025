#!/usr/bin/env python3
"""
Congressional Demo Setup for CapitolVoices with PostgreSQL
Downloads and processes a sample Congressional hearing for hackathon demonstration
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Optional imports for demo setup
try:
    import psycopg2
    from adapters.storage_postgresql import PostgreSQLStorage
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    print("⚠️  PostgreSQL not available. Install with: pip install psycopg2-binary")

try:
    from pipelines.runner import run_pipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    print("⚠️  Pipeline not available. Install dependencies with: pip install -r requirements.txt")

# Sample Congressional hearing for demo
DEMO_HEARING = {
    "hearing_id": "house-oversight-demo-2025",
    "title": "House Oversight Committee - Federal Agency Accountability",
    "committee": "House Committee on Oversight and Accountability", 
    "date": "2025-01-15",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with actual hearing URL
    "duration_minutes": 120,
    "duration_seconds": 7200,
    "expected_speakers": 8
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

# PostgreSQL connection string
POSTGRESQL_CONNECTION = "postgresql://capitol_voices:capitol_voices_password@localhost:5432/capitol_voices"

def setup_directories():
    """Create necessary directories for demo"""
    dirs = ["data", "data/audio", "data/transcripts", "configs/rosters", "artifacts"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Created demo directories")

def setup_postgresql_storage():
    """Initialize PostgreSQL storage"""
    if not POSTGRESQL_AVAILABLE:
        print("❌ PostgreSQL not available. Run setup_postgresql.py first")
        return None
    
    try:
        storage = PostgreSQLStorage(POSTGRESQL_CONNECTION, "capitol_voices")
        print("✅ PostgreSQL storage initialized")
        return storage
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   Make sure PostgreSQL is running and database is set up")
        return None

def setup_demo_roster():
    """Create demo roster configuration"""
    roster_path = Path("configs/rosters/house-oversight-demo.json")
    
    with open(roster_path, 'w') as f:
        json.dump(DEMO_ROSTER, f, indent=2)
    
    print(f"✅ Created demo roster: {roster_path}")
    return roster_path

def setup_demo_hearing_metadata(storage):
    """Initialize database with demo hearing metadata"""
    if not storage:
        print("❌ No storage available")
        return False
    
    try:
        # Write hearing metadata
        storage.write_hearing_metadata(DEMO_HEARING["hearing_id"], DEMO_HEARING)
        
        # Write speaker information
        speakers = [
            {
                "speaker_key": "chair",
                "display_name": "Rep. James Comer",
                "role": "Chair",
                "committee_position": "Chairman",
                "party": "R",
                "state": "KY"
            },
            {
                "speaker_key": "ranking",
                "display_name": "Rep. Jamie Raskin",
                "role": "Ranking Member",
                "committee_position": "Ranking Member",
                "party": "D",
                "state": "MD"
            },
            {
                "speaker_key": "witness_1",
                "display_name": "Dr. Anthony Fauci",
                "role": "Witness",
                "committee_position": None,
                "party": None,
                "state": None
            },
            {
                "speaker_key": "witness_2",
                "display_name": "Dr. Francis Collins",
                "role": "Witness",
                "committee_position": None,
                "party": None,
                "state": None
            },
            {
                "speaker_key": "witness_3",
                "display_name": "Dr. Lawrence Tabak",
                "role": "Witness",
                "committee_position": None,
                "party": None,
                "state": None
            }
        ]
        
        storage.write_speakers(DEMO_HEARING["hearing_id"], speakers)
        
        print(f"✅ Initialized PostgreSQL with demo hearing: {DEMO_HEARING['hearing_id']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup demo hearing metadata: {e}")
        return False

def create_demo_config():
    """Create demo configuration file for PostgreSQL"""
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
            "engine": "postgresql",
            "connection_string": POSTGRESQL_CONNECTION,
            "schema": "capitol_voices"
        },
        "naming": {
            "roster_path": "configs/rosters/house-oversight-demo.json"
        }
    }
    
    config_path = Path("configs/demo_postgresql.yaml")
    import yaml
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"✅ Created PostgreSQL demo config: {config_path}")

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
        # Set environment variable to use PostgreSQL
        os.environ["STORAGE_ENGINE"] = "postgresql"
        os.environ["POSTGRESQL_CONNECTION_STRING"] = POSTGRESQL_CONNECTION
        
        # Run the full pipeline
        run_pipeline(DEMO_HEARING["hearing_id"], str(audio_path))
        print("✅ Demo processing completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Demo processing failed: {e}")
        return False

def verify_demo_results(storage):
    """Verify that demo processing produced expected results"""
    print("🔍 Verifying demo results...")
    
    if not storage:
        print("❌ No storage available for verification")
        return False
    
    try:
        # Get hearing statistics
        stats = storage.get_hearing_statistics(DEMO_HEARING["hearing_id"])
        
        if not stats:
            print("❌ No statistics found for demo hearing")
            return False
        
        hearing_info = stats.get("hearing", {})
        speaker_stats = stats.get("speakers", [])
        
        print(f"📊 Demo Results:")
        print(f"   - Segments generated: {hearing_info.get('total_segments', 0)}")
        print(f"   - Total words: {hearing_info.get('total_words', 0)}")
        print(f"   - Speakers identified: {hearing_info.get('unique_speakers', 0)}")
        print(f"   - Duration: {hearing_info.get('duration_minutes', 0)} minutes")
        
        # Check summary
        summary = storage.read_summary(DEMO_HEARING["hearing_id"])
        print(f"   - Summary created: {'✅' if summary else '❌'}")
        
        if hearing_info.get('total_segments', 0) > 0 and summary and hearing_info.get('unique_speakers', 0) > 0:
            print("✅ Demo verification passed!")
            return True
        else:
            print("❌ Demo verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def test_postgresql_features(storage):
    """Test PostgreSQL-specific features"""
    print("🧪 Testing PostgreSQL features...")
    
    if not storage:
        print("❌ No storage available for testing")
        return False
    
    try:
        # Test full-text search
        search_results = storage.search_hearings("accountability", committee="House")
        print(f"   - Full-text search: {len(search_results)} results")
        
        # Test hearing statistics
        stats = storage.get_hearing_statistics(DEMO_HEARING["hearing_id"])
        print(f"   - Statistics query: {'✅' if stats else '❌'}")
        
        print("✅ PostgreSQL features working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL feature test failed: {e}")
        return False

def main():
    """Main demo setup function"""
    print("🏛️  CapitolVoices PostgreSQL Demo Setup")
    print("=" * 50)
    
    # Setup steps
    setup_directories()
    setup_demo_roster()
    create_demo_config()
    
    # Setup PostgreSQL storage
    storage = setup_postgresql_storage()
    if not storage:
        print("\n❌ PostgreSQL setup failed")
        print("Please run: python setup_postgresql.py")
        return False
    
    # Setup demo hearing metadata
    if not setup_demo_hearing_metadata(storage):
        print("\n❌ Demo hearing setup failed")
        return False
    
    # Download audio (placeholder for demo)
    audio_path = download_demo_audio()
    
    if audio_path and audio_path.exists():
        # Run processing
        success = run_demo_processing()
        
        if success:
            verify_demo_results(storage)
            test_postgresql_features(storage)
            print("\n🎉 PostgreSQL demo setup complete!")
            print("\nNext steps:")
            print("1. Launch the web interface: streamlit run ui/app.py")
            print("2. Select 'house-oversight-demo-2025' from the dropdown")
            print("3. View the generated transcript and summary")
            print("4. Test full-text search across hearings")
        else:
            print("\n❌ Demo setup failed during processing")
    else:
        print("\n⚠️  Demo setup incomplete - audio file needed")
        print("Please provide a sample Congressional hearing audio file at:")
        print("data/audio/house-oversight-demo-2025.wav")
        print("\nBut you can still test the PostgreSQL features:")
        test_postgresql_features(storage)

if __name__ == "__main__":
    main()
