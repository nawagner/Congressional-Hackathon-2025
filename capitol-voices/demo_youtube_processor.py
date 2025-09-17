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
        value="https://www.youtube.com/watch?v=HhQ-tgm9vXQ",
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
            hearing_id = st.text_input("Hearing ID", value="fauci-hearing-june-2024")
            title = st.text_input("Title", value="A Hearing with Dr. Anthony Fauci")
            committee = st.text_input("Committee", value="Select Subcommittee on the Coronavirus Pandemic")
        
        with col2:
            date = st.date_input("Date", value=datetime(2024, 6, 3))
            duration_minutes = st.number_input("Expected Duration (minutes)", min_value=1, max_value=480, value=210)
            expected_speakers = st.number_input("Expected Speakers", min_value=1, max_value=50, value=15)
        
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
                    {"time": "00:10:01", "speaker": "Dr. Brad Wenstrup (Chair)", "text": "The Select Subcommittee on the Coronavirus Pandemic will come to order. I want to welcome everyone this morning."},
                    {"time": "00:10:15", "speaker": "Dr. Brad Wenstrup (Chair)", "text": "Good morning. And welcome, Dr. Fauci. First, I want to thank you for your decades of public service."},
                    {"time": "00:10:45", "speaker": "Dr. Anthony Fauci (Witness)", "text": "Thank you, Mr. Chairman. I appreciate the opportunity to appear before this subcommittee voluntarily."},
                    {"time": "00:11:20", "speaker": "Dr. Brad Wenstrup (Chair)", "text": "Dr. Fauci, we're here to investigate the COVID-19 pandemic and to explore lessons learned, positive or negative."},
                    {"time": "00:12:05", "speaker": "Dr. Anthony Fauci (Witness)", "text": "I believe transparency and accountability are crucial for maintaining public trust in our health institutions."}
                ]
                
                for segment in sample_segments:
                    st.write(f"**[{segment['time']}] {segment['speaker']}:** {segment['text']}")
                
                st.caption("... and 242 more segments")
                
                # Show simulated summary
                st.subheader("Generated Summary")
                
                st.write("**Executive Summary:**")
                st.write("The Select Subcommittee on the Coronavirus Pandemic held a hearing with Dr. Anthony Fauci on June 3, 2024. The hearing focused on investigating the COVID-19 pandemic response, exploring lessons learned, and examining the role of public health officials during the crisis.")
                
                st.write("**Key Points (timestamp-verified):**")
                summary_bullets = [
                    "[00:10:01–00:10:15] Chairman Wenstrup opened the hearing and welcomed Dr. Fauci, acknowledging his decades of public service",
                    "[00:10:45–00:11:20] Dr. Fauci expressed appreciation for the opportunity to appear voluntarily before the subcommittee",
                    "[00:11:20–00:12:05] Chairman Wenstrup outlined the hearing's purpose: investigating COVID-19 response and exploring lessons learned",
                    "[00:12:05–00:12:45] Dr. Fauci emphasized the importance of transparency and accountability in maintaining public trust",
                    "[00:13:00–00:13:30] Discussion began on the challenges of public health communication during the pandemic"
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
                    
                    # Insert demo segments based on real hearing
                    demo_segments = [
                        (hearing_id, 601.0, 615.0, "chair", "The Select Subcommittee on the Coronavirus Pandemic will come to order. I want to welcome everyone this morning."),
                        (hearing_id, 615.0, 630.0, "chair", "Good morning. And welcome, Dr. Fauci. First, I want to thank you for your decades of public service."),
                        (hearing_id, 645.0, 660.0, "witness", "Thank you, Mr. Chairman. I appreciate the opportunity to appear before this subcommittee voluntarily."),
                        (hearing_id, 680.0, 695.0, "chair", "Dr. Fauci, we're here to investigate the COVID-19 pandemic and to explore lessons learned, positive or negative."),
                        (hearing_id, 725.0, 740.0, "witness", "I believe transparency and accountability are crucial for maintaining public trust in our health institutions.")
                    ]
                    
                    # Clear existing segments for this hearing first
                    cur.execute("DELETE FROM segments WHERE hearing_id = ?", (hearing_id,))
                    
                    for segment in demo_segments:
                        cur.execute("""
                            INSERT INTO segments (hearing_id, start_s, end_s, speaker_key, text)
                            VALUES (?, ?, ?, ?, ?)
                        """, segment)
                    
                    # Clear existing summary for this hearing first
                    cur.execute("DELETE FROM summaries WHERE hearing_id = ? AND type = ?", (hearing_id, "default"))
                    
                    # Insert demo summary based on real hearing
                    demo_summary = {
                        "executive": "The Select Subcommittee on the Coronavirus Pandemic held a hearing with Dr. Anthony Fauci on June 3, 2024. The hearing focused on investigating the COVID-19 pandemic response, exploring lessons learned, and examining the role of public health officials during the crisis.",
                        "bullets": summary_bullets,
                        "by_speaker": [
                            {
                                "speaker": "Dr. Brad Wenstrup (Chair)",
                                "points": ["Opened hearing and welcomed Dr. Fauci", "Acknowledged decades of public service", "Outlined hearing purpose: investigating COVID-19 response"]
                            },
                            {
                                "speaker": "Dr. Anthony Fauci (Witness)", 
                                "points": ["Expressed appreciation for voluntary appearance", "Emphasized importance of transparency and accountability", "Discussed challenges of public health communication"]
                            }
                        ]
                    }
                    
                    cur.execute("""
                        INSERT INTO summaries (hearing_id, type, content_json)
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
