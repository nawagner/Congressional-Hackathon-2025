#!/usr/bin/env python3
"""
Generate demo transcript and summary data for CapitolVoices
This creates realistic Congressional hearing data without requiring AI processing
"""

import sqlite3
import json
import time
from datetime import datetime

# Demo transcript segments (realistic Congressional hearing content)
DEMO_SEGMENTS = [
    {
        "start_s": 0.0,
        "end_s": 15.5,
        "speaker_key": "chair",
        "text": "Good morning. I call this hearing of the House Committee on Oversight and Accountability to order. Today we will examine federal agency accountability and transparency measures. I want to thank our witnesses for appearing before the committee today."
    },
    {
        "start_s": 15.5,
        "end_s": 28.2,
        "speaker_key": "ranking",
        "text": "Thank you, Mr. Chairman. I appreciate the opportunity to participate in this important discussion about government transparency and accountability. These are fundamental principles that should guide all federal agencies."
    },
    {
        "start_s": 28.2,
        "end_s": 45.8,
        "speaker_key": "witness_1",
        "text": "Thank you, Chairman Comer and Ranking Member Raskin. I'm Dr. Anthony Fauci, and I'm here to discuss the importance of scientific integrity and transparency in federal health agencies. The American people deserve to have confidence in the scientific process."
    },
    {
        "start_s": 45.8,
        "end_s": 62.1,
        "speaker_key": "chair",
        "text": "Dr. Fauci, I want to start with a question about the transparency of decision-making processes. Can you explain how the agency ensures that scientific recommendations are based on the best available evidence?"
    },
    {
        "start_s": 62.1,
        "end_s": 78.4,
        "speaker_key": "witness_1",
        "text": "Absolutely, Mr. Chairman. Our agency follows a rigorous peer-review process for all scientific recommendations. We publish our methodologies, data sources, and reasoning in peer-reviewed journals and make them publicly available."
    },
    {
        "start_s": 78.4,
        "end_s": 95.2,
        "speaker_key": "ranking",
        "text": "Dr. Fauci, I appreciate your commitment to transparency. However, I'm concerned about recent reports suggesting that some scientific communications may have been influenced by political considerations. How do you address these concerns?"
    },
    {
        "start_s": 95.2,
        "end_s": 112.7,
        "speaker_key": "witness_1",
        "text": "Ranking Member Raskin, I can assure you that our scientific recommendations are based solely on the best available scientific evidence. We have strict protocols in place to prevent political interference in scientific decision-making."
    },
    {
        "start_s": 112.7,
        "end_s": 128.9,
        "speaker_key": "witness_2",
        "text": "I'd like to add to Dr. Fauci's comments. I'm Dr. Francis Collins, and I can speak to the importance of maintaining scientific integrity across all federal health agencies. We have implemented comprehensive oversight mechanisms."
    },
    {
        "start_s": 128.9,
        "end_s": 145.3,
        "speaker_key": "chair",
        "text": "Dr. Collins, thank you for that. I want to turn to the issue of data sharing. How can we ensure that federal agencies are sharing data in a timely and transparent manner with the public and with other agencies?"
    },
    {
        "start_s": 145.3,
        "end_s": 162.8,
        "speaker_key": "witness_2",
        "text": "Mr. Chairman, data sharing is a critical component of government transparency. We have established data sharing agreements with other agencies and have implemented open data initiatives that make non-sensitive information publicly available."
    },
    {
        "start_s": 162.8,
        "end_s": 178.1,
        "speaker_key": "witness_3",
        "text": "I'm Dr. Lawrence Tabak, and I want to emphasize the importance of protecting sensitive information while maintaining transparency. We must balance the public's right to know with the need to protect national security and personal privacy."
    },
    {
        "start_s": 178.1,
        "end_s": 195.4,
        "speaker_key": "ranking",
        "text": "Dr. Tabak, that's an important point. How do you ensure that the classification of information is appropriate and not used to avoid legitimate oversight and transparency requirements?"
    },
    {
        "start_s": 195.4,
        "end_s": 212.7,
        "speaker_key": "witness_3",
        "text": "We have established clear criteria for information classification and regular review processes. All classification decisions are subject to oversight and can be challenged through established procedures."
    },
    {
        "start_s": 212.7,
        "end_s": 228.9,
        "speaker_key": "chair",
        "text": "I want to thank all of our witnesses for their testimony today. This has been a productive discussion about the importance of transparency and accountability in federal agencies. We will continue to monitor these issues closely."
    },
    {
        "start_s": 228.9,
        "end_s": 245.2,
        "speaker_key": "ranking",
        "text": "Thank you, Mr. Chairman. I agree that this has been an important discussion. I look forward to continuing our work to ensure that federal agencies operate with the highest standards of transparency and accountability."
    }
]

# Demo summary
DEMO_SUMMARY = {
    "executive": "The House Committee on Oversight and Accountability held a hearing on federal agency accountability and transparency. Witnesses Dr. Anthony Fauci, Dr. Francis Collins, and Dr. Lawrence Tabak discussed scientific integrity, data sharing, and information classification processes. The hearing emphasized the importance of balancing transparency with the protection of sensitive information.",
    "bullets": [
        "[00:00:00–00:15:30] Chairman Comer opened the hearing on federal agency accountability and transparency",
        "[00:28:12–00:45:48] Dr. Fauci emphasized scientific integrity and peer-review processes for federal health agencies",
        "[00:78:24–00:95:12] Ranking Member Raskin raised concerns about potential political influence on scientific communications",
        "[00:112:42–00:128:54] Dr. Collins discussed comprehensive oversight mechanisms for scientific integrity",
        "[00:145:18–00:162:48] Dr. Collins explained data sharing agreements and open data initiatives",
        "[00:178:06–00:195:24] Dr. Tabak addressed the balance between transparency and information protection",
        "[00:195:24–00:212:42] Dr. Tabak described classification criteria and review processes"
    ],
    "by_speaker": [
        {
            "speaker": "Rep. James Comer (Chair)",
            "points": [
                "Opened hearing on federal agency accountability and transparency",
                "Questioned witnesses about decision-making processes and data sharing",
                "Emphasized continued oversight of transparency issues"
            ]
        },
        {
            "speaker": "Rep. Jamie Raskin (Ranking Member)",
            "points": [
                "Emphasized importance of government transparency and accountability",
                "Raised concerns about political influence on scientific communications",
                "Questioned information classification practices"
            ]
        },
        {
            "speaker": "Dr. Anthony Fauci (Witness)",
            "points": [
                "Discussed scientific integrity and peer-review processes",
                "Addressed concerns about political interference in scientific decision-making",
                "Emphasized evidence-based recommendations"
            ]
        },
        {
            "speaker": "Dr. Francis Collins (Witness)",
            "points": [
                "Described oversight mechanisms for scientific integrity",
                "Explained data sharing agreements and open data initiatives",
                "Emphasized collaboration between federal agencies"
            ]
        },
        {
            "speaker": "Dr. Lawrence Tabak (Witness)",
            "points": [
                "Addressed balance between transparency and information protection",
                "Described classification criteria and review processes",
                "Emphasized protection of national security and privacy"
            ]
        }
    ]
}

def generate_demo_data():
    """Generate demo transcript and summary data"""
    print("🏛️  Generating CapitolVoices Demo Data")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect("data/hearings.db")
    cur = conn.cursor()
    
    # Clear existing segments and summary for demo hearing
    cur.execute("DELETE FROM segments WHERE hearing_id = ?", ("house-oversight-demo-2025",))
    cur.execute("DELETE FROM summaries WHERE hearing_id = ?", ("house-oversight-demo-2025",))
    
    # Insert demo segments
    print("📝 Generating transcript segments...")
    for segment in DEMO_SEGMENTS:
        cur.execute("""
            INSERT INTO segments (hearing_id, start_s, end_s, speaker_key, text)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "house-oversight-demo-2025",
            segment["start_s"],
            segment["end_s"],
            segment["speaker_key"],
            segment["text"]
        ))
    
    print(f"✅ Created {len(DEMO_SEGMENTS)} transcript segments")
    
    # Insert demo summary
    print("📊 Generating summary...")
    cur.execute("""
        INSERT INTO summaries (hearing_id, type, content_json)
        VALUES (?, ?, ?)
    """, (
        "house-oversight-demo-2025",
        "default",
        json.dumps(DEMO_SUMMARY)
    ))
    
    print("✅ Created timestamp-verified summary")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n🎉 Demo data generation complete!")
    print("\nDemo includes:")
    print(f"  - {len(DEMO_SEGMENTS)} transcript segments")
    print(f"  - {len(DEMO_SUMMARY['bullets'])} timestamp-verified summary bullets")
    print(f"  - {len(DEMO_SUMMARY['by_speaker'])} speaker summaries")
    print(f"  - Total duration: {DEMO_SEGMENTS[-1]['end_s']:.1f} seconds")
    
    print("\n🚀 Refresh your Streamlit app to see the results!")
    print("   Go to: http://localhost:8501")

if __name__ == "__main__":
    generate_demo_data()
