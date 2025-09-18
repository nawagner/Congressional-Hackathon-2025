"""
Simple YouTube processor for CapitolVoices Streamlit app
"""

import streamlit as st
import json
import sqlite3
from pathlib import Path

def youtube_processor_interface():
    """Simple YouTube processor interface"""
    
    st.header("🎥 YouTube Transcript Processor")
    st.caption("Process Congressional hearing videos directly from YouTube")
    
    # YouTube URL input
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Enter the URL of a Congressional hearing YouTube video"
    )
    
    if youtube_url:
        try:
            # Import the YouTube processor
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from adapters.youtube_transcript_fetcher import CongressionalYouTubeProcessor
            
            processor = CongressionalYouTubeProcessor()
            
            # Get video info
            with st.spinner("Checking video information..."):
                video_info = processor.get_video_info(youtube_url)
            
            if video_info.get("error"):
                st.error(f"Error: {video_info['error']}")
            else:
                # Display video info
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Video ID", video_info.get("video_id", "Unknown"))
                    st.metric("Has Transcript", "✅ Yes" if video_info.get("has_transcript") else "❌ No")
                
                with col2:
                    available_langs = video_info.get("available_languages", [])
                    st.metric("Available Languages", len(available_langs))
                    if available_langs:
                        st.write("Languages:", ", ".join(available_langs[:5]))
                
                # Hearing metadata form
                st.subheader("Hearing Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    hearing_id = st.text_input("Hearing ID", value=f"youtube-{video_info.get('video_id', 'unknown')}")
                    title = st.text_input("Title", placeholder="House Oversight Committee - Federal Agency Accountability")
                    committee = st.text_input("Committee", placeholder="House Committee on Oversight and Accountability")
                
                with col2:
                    date = st.date_input("Date")
                    duration_minutes = st.number_input("Expected Duration (minutes)", min_value=1, max_value=480, value=120)
                    expected_speakers = st.number_input("Expected Speakers", min_value=1, max_value=50, value=8)
                
                # Process button
                if st.button("🚀 Process YouTube Video", type="primary"):
                    if not youtube_url or not hearing_id or not title or not committee:
                        st.error("Please fill in all required fields")
                    else:
                        hearing_metadata = {
                            "hearing_id": hearing_id,
                            "title": title,
                            "committee": committee,
                            "date": str(date),
                            "duration_minutes": duration_minutes,
                            "expected_speakers": expected_speakers
                        }
                        
                        # Process the video
                        with st.spinner("Processing YouTube video..."):
                            result = processor.process_congressional_video(youtube_url, hearing_metadata)
                        
                        if result["success"]:
                            st.success("✅ Video processed successfully!")
                            
                            # Display results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Segments", result["statistics"]["total_segments"])
                            with col2:
                                st.metric("Duration", f"{result['statistics']['total_duration_minutes']:.1f} min")
                            with col3:
                                st.metric("Words", result["statistics"]["total_words"])
                            
                            # Show sample segments
                            st.subheader("Sample Transcript Segments")
                            segments = result["segments"][:5]  # Show first 5 segments
                            for i, segment in enumerate(segments):
                                start_time = f"{int(segment['start_s']//60):02d}:{int(segment['start_s']%60):02d}"
                                speaker = segment.get('speaker_key', 'Unknown')
                                st.write(f"**[{start_time}] {speaker}:** {segment['text']}")
                            
                            if len(result["segments"]) > 5:
                                st.caption(f"... and {len(result['segments']) - 5} more segments")
                            
                            st.info("🎉 Processing complete! The hearing is now available in the main interface.")
                            
                        else:
                            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        
        except ImportError as e:
            st.error(f"YouTube processor not available: {e}")
            st.info("Make sure youtube-transcript-api is installed: pip install youtube-transcript-api")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Example URLs section
    with st.expander("📋 Example Congressional YouTube URLs"):
        st.write("""
        **House Committee on Oversight and Accountability:**
        - https://www.youtube.com/c/HouseOversightCommittee
        
        **Senate Committee on the Judiciary:**
        - https://www.youtube.com/c/SenateJudiciary
        
        **House Committee on Energy and Commerce:**
        - https://www.youtube.com/c/HouseEnergyCommerce
        
        **Note:** Make sure the video has captions/transcripts enabled.
        """)
    
    # Instructions
    with st.expander("ℹ️ How to Use"):
        st.write("""
        1. **Find a Congressional hearing** on YouTube with captions/transcripts
        2. **Copy the YouTube URL** from the video
        3. **Fill in the hearing information** (title, committee, date, etc.)
        4. **Click "Process YouTube Video"** to fetch the transcript
        5. **View the results** in the main CapitolVoices interface
        
        **Requirements:**
        - The YouTube video must have captions/transcripts available
        - The video should be a Congressional hearing or similar content
        - Processing time depends on video length and transcript availability
        """)
