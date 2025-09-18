#!/usr/bin/env python3
"""
House.gov Hearings Scraper

Scrapes hearing details and witnesses from docs.house.gov pages and integrates with
the existing congressional_hearings table structure.
"""

import os
import re
import requests
import time
import random
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Tuple
from bs4 import BeautifulSoup
from supabase import create_client
from dataclasses import dataclass
import logging

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None  # Fallback if python-dotenv not installed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HouseHearing:
    """Data structure for House.gov hearings"""
    hearing_id: str
    title: str
    hearing_date: date
    location: str
    witnesses: List[Dict[str, str]]
    committee: str
    time: str
    source_url: str

class HouseGovScraper:
    """Scraper for House.gov hearing pages"""
    
    def __init__(self):
        self.base_url = "https://docs.house.gov/Committee/Calendar/ByEvent.aspx"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Initialize Supabase - load from .env if needed
        load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
        
        # Use the witness Supabase credentials
        supabase_url = os.environ.get('WITNESS_SUPABASE_URL')
        supabase_key = os.environ.get('WITNESS_SUPABASE_SERVICE_ROLE_KEY')
        
        logger.info(f"🔍 Debug - URL: {supabase_url}")
        logger.info(f"🔍 Debug - Key ends with: ...{supabase_key[-10:] if supabase_key else 'None'}")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials. Set WITNESS_SUPABASE_URL/SUPABASE_URL and WITNESS_SUPABASE_SERVICE_ROLE_KEY/SUPABASE_SERVICE_ROLE_KEY")
        
        self.supabase = create_client(supabase_url, supabase_key)
        logger.info(f"🔗 Connected to Supabase: {supabase_url}")
    
    def scrape_hearing(self, hearing_id: str) -> Optional[HouseHearing]:
        """Scrape a single hearing by ID"""
        url = f"{self.base_url}?EventID={hearing_id}"
        
        try:
            logger.info(f"🕷️  Scraping hearing {hearing_id}...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the preview panel
            panel = soup.find("div", id="previewPanel")
            if not panel:
                logger.warning(f"⚠️  No preview panel found for hearing {hearing_id}")
                return None
            
            # Extract basic information
            title = self._extract_title(panel)
            date_info = self._extract_date_time(panel)
            location = self._extract_location(panel)
            witnesses = self._extract_witnesses(panel)
            committee = self._extract_committee(panel, title)
            
            if not title or not date_info:
                logger.warning(f"⚠️  Missing essential data for hearing {hearing_id}")
                return None
            
            hearing = HouseHearing(
                hearing_id=hearing_id,
                title=title,
                hearing_date=date_info['date'],
                location=location,
                witnesses=witnesses,
                committee=committee,
                time=date_info['time'],
                source_url=url
            )
            
            logger.info(f"✅ Successfully scraped hearing {hearing_id}: {title[:50]}... ({len(witnesses)} witnesses)")
            return hearing
            
        except Exception as e:
            logger.error(f"❌ Error scraping hearing {hearing_id}: {e}")
            return None
    
    def _extract_title(self, panel: BeautifulSoup) -> str:
        """Extract hearing title"""
        header = panel.find("h1")
        if not header:
            return ""
        
        raw_text = header.find(string=True, recursive=False)
        if raw_text:
            text = raw_text.strip()
        else:
            text = header.get_text(separator=" ", strip=True)
        
        # Clean up title
        if text.lower().startswith("hearing:"):
            text = text.split(":", 1)[1].strip()
        
        return " ".join(text.split())
    
    def _extract_date_time(self, panel: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract hearing date and time"""
        time_node = panel.find("p", class_="meetingTime")
        if not time_node:
            return None
        
        display_text = " ".join(time_node.get_text(strip=True).split())
        
        try:
            # Try parsing the expected format
            dt_obj = datetime.strptime(display_text, "%A, %B %d, %Y (%I:%M %p)")
            return {
                "date": dt_obj.date(),
                "time": dt_obj.strftime("%H:%M"),
                "datetime": dt_obj
            }
        except ValueError:
            # Try alternative formats
            for fmt in ["%B %d, %Y (%I:%M %p)", "%A, %B %d, %Y", "%B %d, %Y"]:
                try:
                    dt_obj = datetime.strptime(display_text, fmt)
                    return {
                        "date": dt_obj.date(),
                        "time": dt_obj.strftime("%H:%M") if "%I:%M" in fmt else "00:00",
                        "datetime": dt_obj
                    }
                except ValueError:
                    continue
            
            logger.warning(f"⚠️  Could not parse date/time: '{display_text}'")
            return None
    
    def _extract_location(self, panel: BeautifulSoup) -> str:
        """Extract hearing location"""
        location_node = panel.find("blockquote", class_="location")
        if not location_node:
            return ""
        
        parts = list(location_node.stripped_strings)
        return ", ".join(parts)
    
    def _extract_witnesses(self, panel: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract witnesses from the hearing page"""
        witnesses = []
        
        for block in panel.find_all("div", class_="witnessPanel"):
            info = block.find("p")
            if not info:
                continue
            
            name_node = info.find("strong")
            name = name_node.get_text(" ", strip=True) if name_node else ""
            
            title_node = info.find("small")
            title = title_node.get_text(" ", strip=True) if title_node else ""
            
            if name:
                witnesses.append({
                    "name": name,
                    "title": title,
                    "organization": self._extract_organization(title)
                })
        
        return witnesses
    
    def _extract_organization(self, title: str) -> str:
        """Extract organization from witness title"""
        if not title:
            return ""
        
        # Common patterns for organization extraction
        # Look for patterns like "at Company Name" or "from Organization"
        patterns = [
            r'\bat\s+(.+?)(?:\s*,|$)',
            r'\bfrom\s+(.+?)(?:\s*,|$)',
            r'\bof\s+(?:the\s+)?(.+?)(?:\s*,|$)',
            r',\s*(.+?)(?:\s*,|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                org = match.group(1).strip()
                # Filter out common titles that aren't organizations
                if not any(word in org.lower() for word in ['director', 'president', 'ceo', 'chairman', 'officer']):
                    return org
        
        return ""
    
    def _extract_committee(self, panel: BeautifulSoup, title: str) -> str:
        """Extract committee name from panel or title"""
        # Look for committee in breadcrumb or title
        breadcrumb = panel.find("div", class_="breadcrumb")
        if breadcrumb:
            committee_text = breadcrumb.get_text(strip=True)
            if "committee" in committee_text.lower():
                return committee_text
        
        # Extract from title if it contains committee information
        title_lower = title.lower()
        for committee_name in ["financial services", "judiciary", "homeland security", "energy and commerce", "oversight", "ways and means", "education and workforce", "natural resources", "transportation and infrastructure", "appropriations", "foreign affairs", "intelligence", "veterans affairs", "agriculture", "science space and technology", "small business", "house administration", "ethics", "rules", "armed services"]:
            if committee_name in title_lower:
                return f"Committee on {committee_name.title()}"
        
        return "Unknown Committee"
    
    def save_to_database(self, hearing: HouseHearing) -> bool:
        """Save hearing to congressional_hearings table"""
        try:
            # Check if hearing already exists
            existing = self.supabase.table('congressional_hearings').select('id').eq('detail_url', hearing.source_url).execute()
            
            if existing.data:
                logger.info(f"⏭️  Hearing {hearing.hearing_id} already exists in database")
                return False
            
            # Prepare data for insertion
            hearing_data = {
                'congress': self._determine_congress(hearing.hearing_date),
                'hearing_type': 'house',
                'hearing_subtype': 'subcommittee' if 'subcommittee' in hearing.title.lower() else None,
                'committee': hearing.committee,
                'hearing_date': hearing.hearing_date.isoformat(),
                'hearing_name': hearing.title,
                'serial_no': hearing.hearing_id,
                'detail_url': hearing.source_url,
                'document_url': None,  # House.gov doesn't typically provide direct document URLs
                'members': [],  # Not available from House.gov scraper
                'witnesses': hearing.witnesses,  # Store as JSONB
                'bill_numbers': []  # Could be enhanced to extract from content
            }
            
            # Insert into database
            result = self.supabase.table('congressional_hearings').insert(hearing_data).execute()
            
            if result.data:
                logger.info(f"✅ Successfully inserted hearing {hearing.hearing_id} into database")
                return True
            else:
                logger.error(f"❌ Failed to insert hearing {hearing.hearing_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database error for hearing {hearing.hearing_id}: {e}")
            return False
    
    def _determine_congress(self, hearing_date: date) -> int:
        """Determine congress number from hearing date"""
        year = hearing_date.year
        
        # Congress sessions run for 2 years starting in odd years
        # 117th Congress: 2021-2022
        # 118th Congress: 2023-2024
        # 119th Congress: 2025-2026
        
        if year >= 2025:
            return 119
        elif year >= 2023:
            return 118
        elif year >= 2021:
            return 117
        elif year >= 2019:
            return 116
        else:
            return 115  # Default for older dates
    
    def scrape_multiple_hearings(self, hearing_ids: List[str], delay_range: Tuple[float, float] = (1.0, 3.0)) -> Dict[str, int]:
        """Scrape multiple hearings with rate limiting"""
        results = {
            'total': len(hearing_ids),
            'scraped': 0,
            'inserted': 0,
            'skipped': 0,
            'failed': 0
        }
        
        logger.info(f"🚀 Starting scrape of {len(hearing_ids)} House.gov hearings...")
        
        for i, hearing_id in enumerate(hearing_ids, 1):
            logger.info(f"📋 Processing hearing {i}/{len(hearing_ids)}: {hearing_id}")
            
            hearing = self.scrape_hearing(hearing_id)
            
            if hearing:
                results['scraped'] += 1
                
                if self.save_to_database(hearing):
                    results['inserted'] += 1
                else:
                    results['skipped'] += 1
            else:
                results['failed'] += 1
            
            # Rate limiting - random delay between requests
            if i < len(hearing_ids):  # Don't delay after last item
                delay = random.uniform(*delay_range)
                time.sleep(delay)
        
        logger.info(f"🎯 Scraping complete: {results['scraped']} scraped, {results['inserted']} inserted, {results['skipped']} skipped, {results['failed']} failed")
        return results

def extract_hearing_ids_from_transcripts(transcript_dir: str) -> List[str]:
    """Extract hearing IDs from transcript filenames"""
    import os
    hearing_ids = []
    
    if not os.path.exists(transcript_dir):
        return hearing_ids
    
    for filename in os.listdir(transcript_dir):
        if filename.endswith('.txt'):
            # Extract ID from patterns like "118577-2025-09-10.ts-ssmlupna.txt"
            match = re.search(r'(\d{6})-\d{4}-\d{2}-\d{2}', filename)
            if match:
                hearing_ids.append(match.group(1))
    
    return list(set(hearing_ids))  # Remove duplicates

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape House.gov hearings")
    parser.add_argument("--hearing-ids", nargs="+", help="Specific hearing IDs to scrape")
    parser.add_argument("--from-transcripts", help="Extract hearing IDs from transcript directory")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds)")
    
    args = parser.parse_args()
    
    scraper = HouseGovScraper()
    
    if args.from_transcripts:
        hearing_ids = extract_hearing_ids_from_transcripts(args.from_transcripts)
        logger.info(f"📁 Found {len(hearing_ids)} hearing IDs from transcripts")
    elif args.hearing_ids:
        hearing_ids = args.hearing_ids
    else:
        # Default set of recent hearing IDs
        hearing_ids = ["118596", "118577", "118574", "118573", "118572"]
    
    if hearing_ids:
        results = scraper.scrape_multiple_hearings(hearing_ids, delay_range=(args.delay, args.delay + 1.0))
        print(f"\n🎯 Final Results:")
        print(f"   Total processed: {results['total']}")
        print(f"   Successfully scraped: {results['scraped']}")
        print(f"   Inserted to database: {results['inserted']}")
        print(f"   Skipped (duplicates): {results['skipped']}")
        print(f"   Failed: {results['failed']}")
    else:
        print("❌ No hearing IDs provided")