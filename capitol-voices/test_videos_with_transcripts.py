#!/usr/bin/env python3
"""
Test YouTube videos that are known to have transcripts
"""

from adapters.youtube_transcript_fetcher import CongressionalYouTubeProcessor

def test_videos_with_transcripts():
    """Test various YouTube videos to find ones with transcripts"""
    
    processor = CongressionalYouTubeProcessor()
    
    # List of videos that commonly have transcripts
    test_videos = [
        # Educational content (often has transcripts)
        "https://www.youtube.com/watch?v=aircAruvnKk",  # 3Blue1Brown - Neural Networks
        "https://www.youtube.com/watch?v=WOoJh6oYAXE",  # Khan Academy
        "https://www.youtube.com/watch?v=9No-FiEInLA",  # Crash Course
        
        # TED Talks (usually have transcripts)
        "https://www.youtube.com/watch?v=8S0FDjFBj8o",  # TED Talk example
        "https://www.youtube.com/watch?v=Z7ZLUBCfp5o",  # Another TED Talk
        
        # News content (often has transcripts)
        "https://www.youtube.com/watch?v=example_news",  # Replace with real news video
        
        # Government/Educational channels
        "https://www.youtube.com/watch?v=example_gov",   # Replace with government video
    ]
    
    print("🔍 Testing YouTube videos for transcript availability...")
    print("=" * 60)
    
    working_videos = []
    
    for i, url in enumerate(test_videos, 1):
        try:
            print(f"{i}. Testing: {url}")
            video_info = processor.get_video_info(url)
            
            if video_info.get("has_transcript"):
                print(f"   ✅ HAS TRANSCRIPT!")
                print(f"   📝 Languages: {video_info.get('available_languages', [])}")
                working_videos.append(url)
            else:
                print(f"   ❌ No transcript available")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Results: {len(working_videos)} videos with transcripts found")
    
    if working_videos:
        print("\n✅ Videos with transcripts:")
        for url in working_videos:
            print(f"   - {url}")
    else:
        print("\n❌ No videos with transcripts found in test set")
        print("\n💡 Recommendations:")
        print("   1. Try TED Talks (usually have transcripts)")
        print("   2. Try educational channels (Khan Academy, Crash Course)")
        print("   3. Try news channels with captions")
        print("   4. Use the demo data instead for the hackathon")
    
    return working_videos

if __name__ == "__main__":
    working_videos = test_videos_with_transcripts()
