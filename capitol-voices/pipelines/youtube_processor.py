#!/usr/bin/env python3
"""
YouTube Transcript Processing Pipeline for CapitolVoices
Processes Congressional hearing YouTube videos using transcript API
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from adapters.youtube_transcript_fetcher import CongressionalYouTubeProcessor
from adapters.speaker_namer_roster import RosterSpeakerNamer
from adapters.sum_timestamped_llm import TimestampVerifiedSummarizer
from adapters.storage_sqlite import SQLiteStorage
from core.settings import AppSettings

class YouTubeProcessingPipeline:
    """Complete pipeline for processing Congressional YouTube videos"""
    
    def __init__(self, config: AppSettings = None):
        self.config = config or AppSettings()
        self.youtube_processor = CongressionalYouTubeProcessor()
        self.speaker_namer = RosterSpeakerNamer(self.config.roster_path)
        self.summarizer = TimestampVerifiedSummarizer(mode=self.config.llm_mode)
        self.storage = SQLiteStorage(self.config.db_path)
    
    def process_youtube_hearing(self, youtube_url: str, hearing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a complete Congressional hearing from YouTube"""
        print(f"🎥 Processing YouTube video: {youtube_url}")
        
        # Step 1: Get video info
        video_info = self.youtube_processor.get_video_info(youtube_url)
        if not video_info.get("has_transcript"):
            return {
                "success": False,
                "error": f"No transcript available for video: {video_info.get('error', 'Unknown error')}"
            }
        
        print(f"✅ Video has transcript in languages: {video_info.get('available_languages', [])}")
        
        # Step 2: Fetch and process transcript
        result = self.youtube_processor.process_congressional_video(youtube_url, hearing_metadata)
        if not result["success"]:
            return result
        
        segments = result["segments"]
        statistics = result["statistics"]
        
        print(f"📝 Fetched {len(segments)} transcript segments")
        print(f"⏱️  Total duration: {statistics['total_duration_minutes']:.1f} minutes")
        
        # Step 3: Speaker identification (if roster available)
        hearing_id = hearing_metadata.get("hearing_id", f"youtube-{video_info['video_id']}")
        try:
            named_segments = list(self.speaker_namer.name_speakers(hearing_id, segments))
            print(f"👥 Applied speaker identification to {len(named_segments)} segments")
        except Exception as e:
            print(f"⚠️  Speaker identification failed: {e}")
            named_segments = segments
        
        # Step 4: Generate summary
        try:
            summary = self.summarizer.summarize(named_segments)
            print("📊 Generated timestamp-verified summary")
        except Exception as e:
            print(f"⚠️  Summary generation failed: {e}")
            summary = {"error": str(e)}
        
        # Step 5: Store results
        try:
            # Store hearing metadata
            hearing_metadata.update({
                "youtube_url": youtube_url,
                "video_id": video_info["video_id"],
                "duration_seconds": statistics["total_duration_seconds"],
                "duration_minutes": statistics["total_duration_minutes"],
                "total_segments": statistics["total_segments"],
                "total_words": statistics["total_words"]
            })
            
            # Store in database
            self.storage.write_hearing_metadata(hearing_id, hearing_metadata)
            self.storage.write_segments(hearing_id, named_segments)
            self.storage.write_summary(hearing_id, summary)
            
            print(f"💾 Stored results in database: {hearing_id}")
            
        except Exception as e:
            print(f"❌ Database storage failed: {e}")
            return {
                "success": False,
                "error": f"Database storage failed: {str(e)}",
                "segments": named_segments,
                "summary": summary,
                "statistics": statistics
            }
        
        return {
            "success": True,
            "hearing_id": hearing_id,
            "segments": named_segments,
            "summary": summary,
            "statistics": statistics,
            "video_info": video_info
        }

def process_congressional_youtube_video(youtube_url: str, hearing_metadata: Dict[str, Any] = None):
    """Convenience function to process a Congressional YouTube video"""
    if hearing_metadata is None:
        hearing_metadata = {
            "hearing_id": f"youtube-{youtube_url.split('v=')[1].split('&')[0] if 'v=' in youtube_url else 'unknown'}",
            "title": "Congressional Hearing",
            "committee": "Unknown Committee",
            "date": "2025-01-01"
        }
    
    pipeline = YouTubeProcessingPipeline()
    return pipeline.process_youtube_hearing(youtube_url, hearing_metadata)

if __name__ == "__main__":
    # Example usage
    youtube_url = "https://www.youtube.com/watch?v=EXAMPLE_VIDEO_ID"
    hearing_metadata = {
        "hearing_id": "house-oversight-2025-01-15",
        "title": "House Oversight Committee - Federal Agency Accountability",
        "committee": "House Committee on Oversight and Accountability",
        "date": "2025-01-15"
    }
    
    result = process_congressional_youtube_video(youtube_url, hearing_metadata)
    print(json.dumps(result, indent=2))
