#!/usr/bin/env python3
"""
YouTube Transcript Validator for CapitolVoices
Fetches transcript from YouTube video and compares with PDF reference
"""

import streamlit as st
import sqlite3
import json
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fetch_youtube_transcript(video_url):
    """Fetch transcript from YouTube video"""
    try:
        from adapters.youtube_transcript_fetcher import CongressionalYouTubeProcessor
        processor = CongressionalYouTubeProcessor()
        
        # Get video info
        video_info = processor.get_video_info(video_url)
        
        if not video_info.get("has_transcript"):
            return None, "No transcript available for this video"
        
        # Fetch transcript
        transcript_data = processor.fetch_transcript(video_url)
        
        return transcript_data, None
        
    except Exception as e:
        return None, f"Error fetching transcript: {str(e)}"

def store_transcript_in_db(hearing_id, transcript_data):
    """Store YouTube transcript in database"""
    try:
        conn = sqlite3.connect("data/hearings.db")
        cur = conn.cursor()
        
        # Clear existing segments for this hearing
        cur.execute("DELETE FROM segments WHERE hearing_id = ?", (hearing_id,))
        
        # Insert new segments
        for i, segment in enumerate(transcript_data.get("segments", [])):
            start_s = segment.get("start", 0)
            end_s = segment.get("start", 0) + segment.get("duration", 0)
            text = segment.get("text", "")
            speaker_key = f"speaker_{i % 3}"  # Simple speaker assignment for demo
            
            cur.execute("""
                INSERT INTO segments (hearing_id, start_s, end_s, speaker_key, text)
                VALUES (?, ?, ?, ?, ?)
            """, (hearing_id, start_s, end_s, speaker_key, text))
        
        conn.commit()
        conn.close()
        
        return True, None
        
    except Exception as e:
        return False, f"Error storing transcript: {str(e)}"

def youtube_transcript_validator_interface():
    """Streamlit interface for YouTube transcript validation"""
    
    st.header("🎥 YouTube Transcript Validator")
    st.caption("Fetch transcript from YouTube video and validate against PDF reference")
    
    # Video URL input
    video_url = st.text_input(
        "YouTube URL",
        value="https://www.youtube.com/watch?v=HhQ-tgm9vXQ",
        help="Enter the YouTube URL to fetch transcript from"
    )
    
    hearing_id = st.text_input(
        "Hearing ID",
        value="fauci-hearing-june-2024",
        help="Database ID for storing the transcript"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Fetch YouTube Transcript", type="primary"):
            if not video_url or not hearing_id:
                st.error("Please provide both YouTube URL and Hearing ID")
            else:
                with st.spinner("Fetching transcript from YouTube..."):
                    transcript_data, error = fetch_youtube_transcript(video_url)
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    st.success("✅ Transcript fetched successfully!")
                    
                    # Show transcript info
                    st.subheader("📊 Transcript Information")
                    st.write(f"**Video ID**: {transcript_data.get('video_id', 'Unknown')}")
                    st.write(f"**Language**: {transcript_data.get('language', 'Unknown')}")
                    st.write(f"**Segments**: {len(transcript_data.get('segments', []))}")
                    
                    # Show sample segments
                    st.subheader("📝 Sample Transcript Segments")
                    segments = transcript_data.get("segments", [])[:5]  # Show first 5 segments
                    
                    for i, segment in enumerate(segments):
                        start_time = segment.get("start", 0)
                        text = segment.get("text", "")
                        st.write(f"**[{start_time:.1f}s]** {text}")
                    
                    if len(transcript_data.get("segments", [])) > 5:
                        st.caption(f"... and {len(transcript_data.get('segments', [])) - 5} more segments")
                    
                    # Store in database
                    if st.button("💾 Store in Database"):
                        with st.spinner("Storing transcript in database..."):
                            success, error = store_transcript_in_db(hearing_id, transcript_data)
                        
                        if success:
                            st.success("✅ Transcript stored in database successfully!")
                            st.info("You can now view the transcript in the Hearing Browser tab")
                        else:
                            st.error(f"❌ {error}")
    
    with col2:
        st.subheader("📋 PDF Reference")
        st.info("**Official Transcript**: [Dr. Anthony Fauci Hearing](https://www.congress.gov/118/chrg/CHRG-118hhrg55830/CHRG-118hhrg55830.pdf)")
        
        st.write("**Validation Checklist**:")
        st.write("✅ **Speaker Identification**")
        st.write("• Compare speaker names in generated transcript vs PDF")
        st.write("• Verify speaker roles (Chair, Ranking Member, Witness)")
        
        st.write("✅ **Content Accuracy**")
        st.write("• Check opening statements match")
        st.write("• Verify key testimony points")
        st.write("• Compare question and answer flow")
        
        st.write("✅ **Timestamp Verification**")
        st.write("• Validate timing of major segments")
        st.write("• Check duration accuracy")
        
        st.write("✅ **Summary Quality**")
        st.write("• Verify executive summary accuracy")
        st.write("• Check key bullet points")
        st.write("• Validate speaker-specific summaries")
    
    # Show current database status
    st.subheader("🗄️ Database Status")
    try:
        conn = sqlite3.connect("data/hearings.db")
        cur = conn.cursor()
        
        # Check if hearing exists
        cur.execute("SELECT id, title, committee, date FROM hearings WHERE id = ?", (hearing_id,))
        hearing = cur.fetchone()
        
        if hearing:
            st.success(f"✅ Hearing found: {hearing[1]}")
            st.write(f"**Committee**: {hearing[2]}")
            st.write(f"**Date**: {hearing[3]}")
            
            # Check segments
            cur.execute("SELECT COUNT(*) FROM segments WHERE hearing_id = ?", (hearing_id,))
            segment_count = cur.fetchone()[0]
            st.write(f"**Segments**: {segment_count}")
            
            # Check summaries
            cur.execute("SELECT COUNT(*) FROM summaries WHERE hearing_id = ?", (hearing_id,))
            summary_count = cur.fetchone()[0]
            st.write(f"**Summaries**: {summary_count}")
            
        else:
            st.warning(f"⚠️ Hearing '{hearing_id}' not found in database")
            st.info("Use the Hearing Browser tab to register the hearing first")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Database error: {e}")

if __name__ == "__main__":
    youtube_transcript_validator_interface()
