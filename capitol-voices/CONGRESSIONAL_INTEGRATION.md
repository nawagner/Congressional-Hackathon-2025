# Congressional Committee Integration Guide

## 🏛️ Connecting CapitolVoices to Congressional Data Sources

This guide shows how to integrate CapitolVoices with official Congressional committee YouTube channels and data sources.

## 📺 Committee YouTube Channels

The hackathon repository provides a comprehensive list of Committee YouTube Channels in `Committee-Youtube-Channels.json`. Here's how to integrate them:

### 1. Parse Committee Data

```python
import json
from pathlib import Path

def load_committee_channels():
    """Load committee YouTube channels from hackathon data"""
    with open('Committee-Youtube-Channels.json', 'r') as f:
        return json.load(f)

# Example usage
committees = load_committee_channels()
for committee in committees:
    print(f"{committee['name']}: {committee['youtube_url']}")
```

### 2. Enhanced Ingest Pipeline

```python
# pipelines/congressional_ingest.py
import yt_dlp
import json
from datetime import datetime
from pathlib import Path

class CongressionalIngest:
    def __init__(self, committee_data_path: str):
        self.committees = self.load_committees(committee_data_path)
    
    def download_hearing(self, youtube_url: str, hearing_id: str):
        """Download audio from Congressional hearing YouTube URL"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'data/audio/{hearing_id}.%(ext)s',
            'extractaudio': True,
            'audioformat': 'wav',
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            
        return {
            'hearing_id': hearing_id,
            'title': info.get('title', ''),
            'upload_date': info.get('upload_date', ''),
            'duration': info.get('duration', 0),
            'committee': self.identify_committee(youtube_url)
        }
    
    def identify_committee(self, youtube_url: str):
        """Identify committee from YouTube URL"""
        for committee in self.committees:
            if committee['youtube_url'] in youtube_url:
                return committee['name']
        return 'Unknown Committee'
```

## 🎯 Committee-Specific Rosters

### House Committee Rosters

```json
{
  "hearing_id": "house-oversight-2025-01-15",
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
```

### Senate Committee Rosters

```json
{
  "hearing_id": "senate-judiciary-2025-01-20",
  "committee": "Senate Committee on the Judiciary",
  "chair": {
    "name": "Sen. Dick Durbin",
    "aliases": ["Chairman Durbin", "Chair Durbin", "Mr. Chairman"]
  },
  "ranking": {
    "name": "Sen. Lindsey Graham",
    "aliases": ["Ranking Member Graham", "Mr. Graham"]
  },
  "members": [
    "Sen. Chuck Grassley", "Sen. John Cornyn", "Sen. Mike Lee",
    "Sen. Ted Cruz", "Sen. Ben Sasse", "Sen. Josh Hawley"
  ],
  "witnesses": [
    "Attorney General Merrick Garland", "FBI Director Christopher Wray"
  ]
}
```

## 🔄 Automated Processing Workflow

### 1. Hearing Discovery

```python
def discover_recent_hearings(committee_name: str, days_back: int = 7):
    """Discover recent hearings from committee YouTube channel"""
    committee = next(c for c in committees if c['name'] == committee_name)
    
    # Use YouTube API or yt-dlp to get recent videos
    # Filter for hearing-like titles
    # Return list of hearing metadata
    pass
```

### 2. Batch Processing

```python
def process_committee_hearings(committee_name: str):
    """Process all recent hearings for a committee"""
    hearings = discover_recent_hearings(committee_name)
    
    for hearing in hearings:
        # Download audio
        metadata = download_hearing(hearing['url'], hearing['id'])
        
        # Run transcription pipeline
        run_pipeline(hearing['id'], f"data/audio/{hearing['id']}.wav")
        
        # Store metadata
        store_hearing_metadata(metadata)
```

## 📊 Committee-Specific Configurations

### House Oversight Committee
```yaml
# configs/house-oversight.yaml
hearing:
  committee: "House Committee on Oversight and Accountability"
  typical_duration: 120  # minutes
  common_witnesses: ["agency_heads", "inspectors_general", "whistleblowers"]

asr:
  model: "large-v3"
  chunk_seconds: 600  # 10-minute chunks for long hearings

diarization:
  min_speakers: 5
  max_speakers: 15  # Large committees

naming:
  roster_path: "configs/rosters/house-oversight.json"
  priority_speakers: ["chair", "ranking", "witnesses"]
```

### Senate Judiciary Committee
```yaml
# configs/senate-judiciary.yaml
hearing:
  committee: "Senate Committee on the Judiciary"
  typical_duration: 180  # minutes
  common_witnesses: ["attorney_general", "fbi_director", "legal_experts"]

asr:
  model: "large-v3"
  chunk_seconds: 900  # 15-minute chunks

diarization:
  min_speakers: 8
  max_speakers: 25  # Very large committee

naming:
  roster_path: "configs/rosters/senate-judiciary.json"
  priority_speakers: ["chair", "ranking", "witnesses"]
```

## 🔍 Metadata Integration

### Congressional Data Sources

```python
def enrich_hearing_metadata(hearing_id: str):
    """Enrich hearing with Congressional data sources"""
    
    # Get committee information
    committee_info = get_committee_info(hearing_id)
    
    # Get member information from Congress.gov API
    members = get_committee_members(committee_info['committee_id'])
    
    # Get witness information
    witnesses = get_hearing_witnesses(hearing_id)
    
    # Get bill information if applicable
    bills = get_related_bills(hearing_id)
    
    return {
        'hearing_id': hearing_id,
        'committee': committee_info,
        'members': members,
        'witnesses': witnesses,
        'bills': bills,
        'processed_at': datetime.now().isoformat()
    }
```

## 🚀 Production Deployment

### 1. Scheduled Processing

```python
# Schedule regular processing of committee hearings
import schedule
import time

def process_all_committees():
    """Process recent hearings for all major committees"""
    major_committees = [
        "House Committee on Oversight and Accountability",
        "Senate Committee on the Judiciary", 
        "House Committee on Energy and Commerce",
        "Senate Committee on Finance"
    ]
    
    for committee in major_committees:
        try:
            process_committee_hearings(committee)
        except Exception as e:
            print(f"Error processing {committee}: {e}")

# Schedule every 6 hours
schedule.every(6).hours.do(process_all_committees)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. Real-time Monitoring

```python
def monitor_committee_channels():
    """Monitor committee YouTube channels for new hearings"""
    # Use YouTube API webhooks or polling
    # Detect new videos matching hearing patterns
    # Trigger automatic processing
    pass
```

## 📈 Analytics and Reporting

### Committee Performance Metrics

```python
def generate_committee_report(committee_name: str, date_range: tuple):
    """Generate analytics report for committee hearings"""
    
    hearings = get_hearings_in_range(committee_name, date_range)
    
    metrics = {
        'total_hearings': len(hearings),
        'total_duration': sum(h['duration'] for h in hearings),
        'average_processing_time': calculate_avg_processing_time(hearings),
        'speaker_accuracy': calculate_speaker_accuracy(hearings),
        'most_active_members': get_most_active_members(hearings),
        'common_topics': extract_common_topics(hearings)
    }
    
    return metrics
```

## 🔧 Configuration Management

### Environment Setup

```bash
# .env file for Congressional integration
CONGRESS_API_KEY=your_congress_api_key
YOUTUBE_API_KEY=your_youtube_api_key
HF_TOKEN=your_huggingface_token

# Committee-specific settings
DEFAULT_COMMITTEE=house-oversight
AUTO_PROCESS_NEW_HEARINGS=true
PROCESSING_SCHEDULE=every_6_hours
```

This integration guide provides the foundation for connecting CapitolVoices with official Congressional data sources, enabling automated processing of committee hearings at scale.
