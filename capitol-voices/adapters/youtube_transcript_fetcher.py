from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from core.interfaces import Segment

class YouTubeTranscriptFetcher:
    """Fetch and process YouTube transcripts for Congressional hearings"""
    
    def __init__(self):
        self.formatter = TextFormatter()
    
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        
        return None
    
    def fetch_transcript(self, youtube_url: str, language_codes: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch transcript from YouTube video"""
        if language_codes is None:
            language_codes = ['en', 'en-US', 'en-GB']
        
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
        
        try:
            # Try to get transcript in preferred languages
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, 
                languages=language_codes
            )
            return transcript
        except Exception as e:
            raise Exception(f"Failed to fetch transcript for video {video_id}: {str(e)}")
    
    def convert_to_segments(self, transcript_data: List[Dict[str, Any]], hearing_id: str) -> List[Segment]:
        """Convert YouTube transcript data to CapitolVoices segments"""
        segments = []
        
        for item in transcript_data:
            segment = {
                "hearing_id": hearing_id,
                "start_s": float(item['start']),
                "end_s": float(item['start'] + item['duration']),
                "text": item['text'].strip(),
                "speaker_key": None  # Will be filled by speaker identification
            }
            segments.append(segment)
        
        return segments
    
    def get_available_languages(self, youtube_url: str) -> List[str]:
        """Get list of available transcript languages for a video"""
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
        
        try:
            # Try to get transcript in common languages to check availability
            common_languages = ['en', 'en-US', 'en-GB', 'es', 'fr', 'de']
            available_languages = []
            
            for lang in common_languages:
                try:
                    YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                    available_languages.append(lang)
                except:
                    continue
            
            return available_languages
        except Exception as e:
            raise Exception(f"Failed to get available languages for video {video_id}: {str(e)}")
    
    def fetch_with_fallback(self, youtube_url: str) -> List[Segment]:
        """Fetch transcript with automatic language fallback"""
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
        
        # Try different language combinations
        language_attempts = [
            ['en', 'en-US', 'en-GB'],
            ['en'],
            ['en-US'],
            ['en-GB']
        ]
        
        for languages in language_attempts:
            try:
                transcript_data = self.fetch_transcript(youtube_url, languages)
                return self.convert_to_segments(transcript_data, f"youtube-{video_id}")
            except Exception:
                continue
        
        # If all attempts fail, try to get any available transcript
        try:
            available_languages = self.get_available_languages(youtube_url)
            if available_languages:
                transcript_data = self.fetch_transcript(youtube_url, available_languages[:1])
                return self.convert_to_segments(transcript_data, f"youtube-{video_id}")
        except Exception:
            pass
        
        raise Exception(f"No transcript available for video {video_id}")

class CongressionalYouTubeProcessor:
    """Process Congressional hearing YouTube videos with transcript integration"""
    
    def __init__(self):
        self.transcript_fetcher = YouTubeTranscriptFetcher()
    
    def process_congressional_video(self, youtube_url: str, hearing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Congressional hearing YouTube video"""
        try:
            # Fetch transcript
            segments = self.transcript_fetcher.fetch_with_fallback(youtube_url)
            
            # Add hearing metadata to segments
            for segment in segments:
                segment["hearing_id"] = hearing_metadata.get("hearing_id", f"youtube-{self.transcript_fetcher.extract_video_id(youtube_url)}")
            
            # Calculate statistics
            total_duration = max(seg["end_s"] for seg in segments) if segments else 0
            total_segments = len(segments)
            total_words = sum(len(seg["text"].split()) for seg in segments)
            
            return {
                "success": True,
                "segments": segments,
                "statistics": {
                    "total_duration_seconds": total_duration,
                    "total_duration_minutes": total_duration / 60,
                    "total_segments": total_segments,
                    "total_words": total_words,
                    "average_words_per_segment": total_words / total_segments if total_segments > 0 else 0
                },
                "metadata": {
                    "video_id": self.transcript_fetcher.extract_video_id(youtube_url),
                    "youtube_url": youtube_url,
                    "transcript_source": "youtube_api"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "segments": [],
                "statistics": {},
                "metadata": {
                    "video_id": self.transcript_fetcher.extract_video_id(youtube_url),
                    "youtube_url": youtube_url,
                    "transcript_source": "youtube_api"
                }
            }
    
    def get_video_info(self, youtube_url: str) -> Dict[str, Any]:
        """Get basic information about a YouTube video"""
        video_id = self.transcript_fetcher.extract_video_id(youtube_url)
        if not video_id:
            return {"error": "Invalid YouTube URL"}
        
        try:
            available_languages = self.transcript_fetcher.get_available_languages(youtube_url)
            return {
                "video_id": video_id,
                "available_languages": available_languages,
                "has_transcript": len(available_languages) > 0,
                "youtube_url": youtube_url
            }
        except Exception as e:
            return {
                "video_id": video_id,
                "error": str(e),
                "has_transcript": False,
                "youtube_url": youtube_url
            }
