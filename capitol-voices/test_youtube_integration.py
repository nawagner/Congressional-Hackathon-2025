#!/usr/bin/env python3
"""
Test YouTube transcript integration for CapitolVoices
"""

from adapters.youtube_transcript_fetcher import CongressionalYouTubeProcessor

def test_youtube_integration():
    """Test the YouTube transcript integration"""
    print("🎥 Testing YouTube Transcript Integration")
    print("=" * 50)
    
    processor = CongressionalYouTubeProcessor()
    
    # Test with a sample YouTube URL (you can replace this with a real Congressional hearing)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with real Congressional hearing
    
    print(f"Testing URL: {test_url}")
    
    try:
        # Test video info
        print("\n1. Testing video info retrieval...")
        video_info = processor.get_video_info(test_url)
        
        if video_info.get("error"):
            print(f"❌ Error: {video_info['error']}")
            return False
        
        print(f"✅ Video ID: {video_info.get('video_id')}")
        print(f"✅ Has transcript: {video_info.get('has_transcript')}")
        print(f"✅ Available languages: {video_info.get('available_languages', [])}")
        
        if not video_info.get("has_transcript"):
            print("⚠️  This video doesn't have transcripts available")
            print("   Try with a different YouTube video that has captions")
            return False
        
        # Test transcript fetching
        print("\n2. Testing transcript fetching...")
        result = processor.process_congressional_video(test_url, {
            "hearing_id": "test-youtube-hearing",
            "title": "Test Congressional Hearing",
            "committee": "Test Committee",
            "date": "2025-01-01"
        })
        
        if result["success"]:
            print(f"✅ Successfully fetched {len(result['segments'])} segments")
            print(f"✅ Duration: {result['statistics']['total_duration_minutes']:.1f} minutes")
            print(f"✅ Total words: {result['statistics']['total_words']}")
            
            # Show sample segments
            print("\n3. Sample transcript segments:")
            for i, segment in enumerate(result["segments"][:3]):
                start_time = f"{int(segment['start_s']//60):02d}:{int(segment['start_s']%60):02d}"
                print(f"   [{start_time}] {segment['text'][:100]}...")
            
            return True
        else:
            print(f"❌ Failed to process video: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_with_real_congressional_video():
    """Test with a real Congressional hearing video (if available)"""
    print("\n🏛️  Testing with Real Congressional Video")
    print("=" * 50)
    
    # Example Congressional hearing URLs (these may or may not have transcripts)
    congressional_urls = [
        "https://www.youtube.com/watch?v=EXAMPLE_HOUSE_OVERSIGHT_VIDEO",
        "https://www.youtube.com/watch?v=EXAMPLE_SENATE_JUDICIARY_VIDEO",
        # Add real Congressional hearing URLs here
    ]
    
    processor = CongressionalYouTubeProcessor()
    
    for url in congressional_urls:
        if "EXAMPLE" in url:
            continue  # Skip example URLs
            
        print(f"\nTesting: {url}")
        try:
            video_info = processor.get_video_info(url)
            if video_info.get("has_transcript"):
                print(f"✅ Has transcript in languages: {video_info.get('available_languages')}")
                
                # Process the video
                result = processor.process_congressional_video(url, {
                    "hearing_id": f"congressional-{video_info['video_id']}",
                    "title": "Congressional Hearing",
                    "committee": "Congressional Committee",
                    "date": "2025-01-01"
                })
                
                if result["success"]:
                    print(f"✅ Processed {len(result['segments'])} segments")
                    print(f"✅ Duration: {result['statistics']['total_duration_minutes']:.1f} minutes")
                else:
                    print(f"❌ Processing failed: {result.get('error')}")
            else:
                print("❌ No transcript available")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 CapitolVoices YouTube Integration Test")
    print("=" * 60)
    
    # Test basic integration
    success = test_youtube_integration()
    
    if success:
        print("\n✅ YouTube integration test passed!")
        print("\nNext steps:")
        print("1. Find a real Congressional hearing YouTube video with captions")
        print("2. Use the YouTube Processor tab in the Streamlit app")
        print("3. Process the video to see real transcripts and summaries")
    else:
        print("\n❌ YouTube integration test failed")
        print("\nTroubleshooting:")
        print("1. Make sure youtube-transcript-api is installed")
        print("2. Try with a different YouTube video that has captions")
        print("3. Check your internet connection")
    
    # Test with real Congressional videos (if any are provided)
    test_with_real_congressional_video()
