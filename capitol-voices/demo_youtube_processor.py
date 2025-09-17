#!/usr/bin/env python3
"""
Demo YouTube processor that simulates processing without requiring actual transcripts
Perfect for hackathon demonstrations
"""

import streamlit as st
import json
import sqlite3
import time
from datetime import datetime

def demo_youtube_processor_interface():
    """Demo YouTube processor interface for hackathon"""
    
    st.header("🎥 YouTube Transcript Processor")
    st.caption("Process Congressional hearing videos directly from YouTube")
    
    # Demo mode indicator
    st.info("🎭 **Demo Mode**: This simulates YouTube processing for demonstration purposes")
    
    # YouTube URL input
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Enter any YouTube URL - this demo will simulate processing"
    )
    
    if youtube_url:
        # Simulate video info
        st.subheader("📹 Video Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Video ID", "DEMO_VIDEO_123")
            st.metric("Has Transcript", "✅ Yes")
        
        with col2:
            st.metric("Available Languages", "3")
            st.write("Languages: en, en-US, en-GB")
        
        # Hearing metadata form
        st.subheader("Hearing Information")
        col1, col2 = st.columns(2)
        
        with col1:
            hearing_id = st.text_input("Hearing ID", value="demo-youtube-hearing-2025")
            title = st.text_input("Title", value="House Oversight Committee - Federal Agency Accountability")
            committee = st.text_input("Committee", value="House Committee on Oversight and Accountability")
        
        with col2:
            date = st.date_input("Date", value=datetime(2025, 1, 15))
            duration_minutes = st.number_input("Expected Duration (minutes)", min_value=1, max_value=480, value=120)
            expected_speakers = st.number_input("Expected Speakers", min_value=1, max_value=50, value=8)
        
        # Process button
        if st.button("🚀 Process YouTube Video (Demo)", type="primary"):
            if not youtube_url or not hearing_id or not title or not committee:
                st.error("Please fill in all required fields")
            else:
                # Simulate processing
                with st.spinner("Processing YouTube video..."):
                    time.sleep(2)  # Simulate processing time
                
                # Simulate successful results
                st.success("✅ Video processed successfully!")
                
                # Display simulated results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Segments", "247")
                with col2:
                    st.metric("Duration", "2.1 hours")
                with col3:
                    st.metric("Words", "15,420")
                
                # Show sample segments
                st.subheader("Sample Transcript Segments")
                
                sample_segments = [
                    {"time": "00:15:23", "speaker": "Rep. James Comer (Chair)", "text": "Good morning. I call this hearing of the House Committee on Oversight and Accountability to order."},
                    {"time": "00:15:45", "speaker": "Rep. Jamie Raskin (Ranking Member)", "text": "Thank you, Mr. Chairman. I appreciate the opportunity to participate in this important discussion."},
                    {"time": "00:16:12", "speaker": "Dr. Anthony Fauci (Witness)", "text": "Thank you, Chairman Comer and Ranking Member Raskin. I'm here to discuss scientific integrity and transparency."},
                    {"time": "00:16:35", "speaker": "Rep. James Comer (Chair)", "text": "Dr. Fauci, I want to start with a question about the transparency of decision-making processes."},
                    {"time": "00:17:02", "speaker": "Dr. Anthony Fauci (Witness)", "text": "Absolutely, Mr. Chairman. Our agency follows a rigorous peer-review process for all scientific recommendations."}
                ]
                
                for segment in sample_segments:
                    st.write(f"**[{segment['time']}] {segment['speaker']}:** {segment['text']}")
                
                st.caption("... and 242 more segments")
                
                # Show simulated summary
                st.subheader("Generated Summary")
                
                st.write("**Executive Summary:**")
                st.write("The House Committee on Oversight and Accountability held a hearing on federal agency accountability and transparency. Witnesses Dr. Anthony Fauci, Dr. Francis Collins, and Dr. Lawrence Tabak discussed scientific integrity, data sharing, and information classification processes.")
                
                st.write("**Key Points (timestamp-verified):**")
                summary_bullets = [
                    "[00:15:23–00:15:45] Chairman Comer opened the hearing on federal agency accountability and transparency",
                    "[00:16:12–00:16:35] Dr. Fauci emphasized scientific integrity and peer-review processes for federal health agencies",
                    "[00:17:02–00:17:25] Dr. Fauci addressed transparency in decision-making processes",
                    "[00:18:15–00:18:42] Ranking Member Raskin raised concerns about political influence on scientific communications",
                    "[00:19:30–00:19:55] Dr. Collins discussed comprehensive oversight mechanisms for scientific integrity"
                ]
                
                for bullet in summary_bullets:
                    st.write(f"• {bullet}")
                
                # Store demo data in database
                try:
                    conn = sqlite3.connect("data/hearings.db")
                    cur = conn.cursor()
                    
                    # Insert demo hearing
                    cur.execute("""
                        REPLACE INTO hearings(id, title, committee, date, video_url)
                        VALUES(?, ?, ?, ?, ?)
                    """, (hearing_id, title, committee, str(date), youtube_url))
                    
                    # Insert demo segments
                    demo_segments = [
                        (hearing_id, 0.0, 15.5, "chair", "Good morning. I call this hearing of the House Committee on Oversight and Accountability to order."),
                        (hearing_id, 15.5, 28.2, "ranking", "Thank you, Mr. Chairman. I appreciate the opportunity to participate in this important discussion."),
                        (hearing_id, 28.2, 45.8, "witness_1", "Thank you, Chairman Comer and Ranking Member Raskin. I'm here to discuss scientific integrity and transparency."),
                        (hearing_id, 45.8, 62.1, "chair", "Dr. Fauci, I want to start with a question about the transparency of decision-making processes."),
                        (hearing_id, 62.1, 78.4, "witness_1", "Absolutely, Mr. Chairman. Our agency follows a rigorous peer-review process for all scientific recommendations.")
                    ]
                    
                    # Clear existing segments for this hearing first
                    cur.execute("DELETE FROM segments WHERE hearing_id = ?", (hearing_id,))
                    
                    for segment in demo_segments:
                        cur.execute("""
                            INSERT INTO segments (hearing_id, start_s, end_s, speaker_key, text)
                            VALUES (?, ?, ?, ?, ?)
                        """, segment)
                    
                    # Insert demo summary
                    demo_summary = {
                        "executive": "The House Committee on Oversight and Accountability held a hearing on federal agency accountability and transparency. Witnesses discussed scientific integrity, data sharing, and information classification processes.",
                        "bullets": summary_bullets,
                        "by_speaker": [
                            {
                                "speaker": "Rep. James Comer (Chair)",
                                "points": ["Opened hearing on federal agency accountability", "Questioned witnesses about decision-making processes"]
                            },
                            {
                                "speaker": "Rep. Jamie Raskin (Ranking Member)", 
                                "points": ["Emphasized importance of government transparency", "Raised concerns about political influence"]
                            },
                            {
                                "speaker": "Dr. Anthony Fauci (Witness)",
                                "points": ["Discussed scientific integrity and peer-review processes", "Addressed transparency in decision-making"]
                            }
                        ]
                    }
                    
                    cur.execute("""
                        REPLACE INTO summaries (hearing_id, type, content_json)
                        VALUES (?, ?, ?)
                    """, (hearing_id, "default", json.dumps(demo_summary)))
                    
                    conn.commit()
                    conn.close()
                    
                    st.info("🎉 Demo processing complete! The hearing is now available in the main interface.")
                    
                except Exception as e:
                    st.warning(f"Demo data created, but database storage failed: {e}")
    
    # Example URLs section
    with st.expander("📋 Example Congressional YouTube URLs"):
        st.write("""
        **House Committee on Oversight and Accountability:**
        - https://www.youtube.com/c/HouseOversightCommittee
        
        **Senate Committee on the Judiciary:**
        - https://www.youtube.com/c/SenateJudiciary
        
        **House Committee on Energy and Commerce:**
        - https://www.youtube.com/c/HouseEnergyCommerce
        
        **Note:** This demo mode works with any YouTube URL for demonstration purposes.
        """)
    
    # Instructions
    with st.expander("ℹ️ Demo Mode Instructions"):
        st.write("""
        **Demo Mode Features:**
        1. **Works with any YouTube URL** - no transcript required
        2. **Simulates real processing** with progress indicators
        3. **Generates realistic results** with sample segments and summaries
        4. **Stores demo data** in the database for viewing in the main interface
        5. **Perfect for hackathon demonstrations** without dependency on external data
        
        **How to Use:**
        1. Enter any YouTube URL (real or fake)
        2. Fill in the hearing information
        3. Click "Process YouTube Video (Demo)"
        4. View the simulated results
        5. Check the main interface to see the stored data
        
        **For Real Processing:** Use videos with actual transcripts/captions enabled.
        """)

if __name__ == "__main__":
    demo_youtube_processor_interface()
