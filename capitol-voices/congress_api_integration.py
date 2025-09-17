#!/usr/bin/env python3
"""
Congress.gov API Integration for CapitolVoices
Fetches real Congressional hearing data from the official API
"""

import requests
import streamlit as st
import sqlite3
import json
from datetime import datetime
import time

class CongressAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.congress.gov/v3"
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def get_hearing(self, congress, chamber, hearing_id):
        """Get hearing details from Congress.gov API"""
        url = f"{self.base_url}/hearing/{congress}/{chamber}/{hearing_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None
    
    def search_hearings(self, congress=None, chamber=None, committee=None, limit=10):
        """Search for hearings"""
        url = f"{self.base_url}/hearing"
        params = {"limit": limit}
        
        if congress:
            params["congress"] = congress
        if chamber:
            params["chamber"] = chamber
        if committee:
            params["committee"] = committee
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None
    
    def get_committee_hearings(self, congress, committee_id, limit=10):
        """Get hearings for a specific committee"""
        url = f"{self.base_url}/hearing"
        params = {
            "congress": congress,
            "committee": committee_id,
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None

def store_hearing_in_db(hearing_data):
    """Store hearing data from Congress.gov API in database"""
    try:
        conn = sqlite3.connect("data/hearings.db")
        cur = conn.cursor()
        
        # Extract hearing information
        hearing = hearing_data.get("hearing", {})
        hearing_id = f"congress-{hearing.get('congress', '')}-{hearing.get('chamber', '')}-{hearing.get('hearingId', '')}"
        title = hearing.get("title", "Unknown Title")
        committee = hearing.get("committee", {}).get("name", "Unknown Committee")
        date = hearing.get("date", "")
        
        # Store hearing
        cur.execute("""
            REPLACE INTO hearings(id, title, committee, date, video_url)
            VALUES(?, ?, ?, ?, ?)
        """, (hearing_id, title, committee, date, ""))
        
        conn.commit()
        conn.close()
        
        return True, hearing_id
        
    except Exception as e:
        return False, f"Error storing hearing: {e}"

def congress_api_interface():
    """Streamlit interface for Congress.gov API integration"""
    
    st.header("🏛️ Congress.gov API Integration")
    st.caption("Fetch real Congressional hearing data from the official API")
    
    # API Key input
    api_key = st.text_input(
        "Congress.gov API Key",
        value="M48cj9inQcpQxtlQQM0tfobTP3YSr0fUG9niaC3G",
        type="password",
        help="Your Congress.gov API key"
    )
    
    if not api_key:
        st.warning("Please enter your Congress.gov API key")
        return
    
    # Initialize API client
    api = CongressAPI(api_key)
    
    # Search options
    st.subheader("🔍 Search Hearings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        congress = st.selectbox("Congress", [116, 117, 118, 119], index=2)  # Default to 118th Congress
    
    with col2:
        chamber = st.selectbox("Chamber", ["house", "senate", "joint"])
    
    with col3:
        limit = st.number_input("Results Limit", min_value=1, max_value=50, value=10)
    
    # Search button
    if st.button("🔍 Search Hearings", type="primary"):
        with st.spinner("Searching Congress.gov API..."):
            results = api.search_hearings(congress=congress, chamber=chamber, limit=limit)
        
        if results and "hearings" in results:
            hearings = results["hearings"]
            st.success(f"✅ Found {len(hearings)} hearings")
            
            # Display results
            for i, hearing in enumerate(hearings):
                with st.expander(f"📋 {hearing.get('title', 'Unknown Title')}"):
                    st.write(f"**Committee**: {hearing.get('committee', {}).get('name', 'Unknown')}")
                    st.write(f"**Date**: {hearing.get('date', 'Unknown')}")
                    st.write(f"**Chamber**: {hearing.get('chamber', 'Unknown')}")
                    st.write(f"**Congress**: {hearing.get('congress', 'Unknown')}")
                    st.write(f"**Hearing ID**: {hearing.get('hearingId', 'Unknown')}")
                    
                    if st.button(f"💾 Store in Database", key=f"store_{i}"):
                        with st.spinner("Storing hearing in database..."):
                            success, result = store_hearing_in_db({"hearing": hearing})
                        
                        if success:
                            st.success(f"✅ Stored as: {result}")
                        else:
                            st.error(f"❌ {result}")
        else:
            st.error("❌ No hearings found or API error")
    
    # Specific hearing lookup
    st.subheader("🎯 Lookup Specific Hearing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        specific_congress = st.selectbox("Congress", [116, 117, 118, 119], index=2, key="specific_congress")
    
    with col2:
        specific_chamber = st.selectbox("Chamber", ["house", "senate", "joint"], key="specific_chamber")
    
    with col3:
        hearing_id = st.text_input("Hearing ID", value="41365", help="Enter the hearing ID")
    
    if st.button("🔍 Lookup Hearing", type="primary"):
        if not hearing_id:
            st.error("Please enter a hearing ID")
        else:
            with st.spinner("Fetching hearing details..."):
                hearing_data = api.get_hearing(specific_congress, specific_chamber, hearing_id)
            
            if hearing_data and "hearing" in hearing_data:
                hearing = hearing_data["hearing"]
                st.success("✅ Hearing found!")
                
                # Display hearing details
                st.subheader("📋 Hearing Details")
                st.write(f"**Title**: {hearing.get('title', 'Unknown')}")
                st.write(f"**Committee**: {hearing.get('committee', {}).get('name', 'Unknown')}")
                st.write(f"**Date**: {hearing.get('date', 'Unknown')}")
                st.write(f"**Chamber**: {hearing.get('chamber', 'Unknown')}")
                st.write(f"**Congress**: {hearing.get('congress', 'Unknown')}")
                st.write(f"**Hearing ID**: {hearing.get('hearingId', 'Unknown')}")
                
                # Show additional details if available
                if "description" in hearing:
                    st.write(f"**Description**: {hearing['description']}")
                
                if "location" in hearing:
                    st.write(f"**Location**: {hearing['location']}")
                
                # Store button
                if st.button("💾 Store This Hearing", type="primary"):
                    with st.spinner("Storing hearing in database..."):
                        success, result = store_hearing_in_db(hearing_data)
                    
                    if success:
                        st.success(f"✅ Stored as: {result}")
                        st.info("You can now view this hearing in the Hearing Browser tab")
                    else:
                        st.error(f"❌ {result}")
            else:
                st.error("❌ Hearing not found or API error")
    
    # API Status
    st.subheader("📊 API Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("API Key", "✅ Configured" if api_key else "❌ Missing")
        st.metric("Base URL", "https://api.congress.gov/v3")
    
    with col2:
        st.metric("Rate Limit", "5,000 requests/day")
        st.metric("Data Source", "Official Congress.gov")
    
    # Usage instructions
    with st.expander("ℹ️ Usage Instructions"):
        st.write("""
        **Congress.gov API Integration:**
        
        1. **Search Hearings**: Use the search form to find hearings by Congress, chamber, and other criteria
        2. **Lookup Specific Hearing**: Enter a specific hearing ID to get detailed information
        3. **Store in Database**: Save hearings to your local database for processing
        4. **View in Browser**: Check the Hearing Browser tab to see stored hearings
        
        **API Features:**
        - Real Congressional hearing data
        - Official committee information
        - Accurate dates and titles
        - Integration with CapitolVoices processing pipeline
        
        **Rate Limits:**
        - 5,000 requests per day
        - 1 request per second
        - Free tier available
        """)

if __name__ == "__main__":
    congress_api_interface()
