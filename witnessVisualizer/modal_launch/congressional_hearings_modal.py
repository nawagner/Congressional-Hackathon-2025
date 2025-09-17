"""
Modal Deployment for Congressional Hearings Scraper

High-performance scraper using all 82 Congress.gov API keys with parallel processing.
Scrapes hearings data and populates the congressional_hearings table.
"""

import modal
import os
import re
import asyncio
import requests
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Tuple
import json
from dataclasses import dataclass, asdict
import time
import random
from bs4 import BeautifulSoup

# Modal app definition
app = modal.App("congressional-hearings-scraper")

# Modal image with dependencies
image = modal.Image.debian_slim().pip_install([
    "requests",
    "beautifulsoup4", 
    "supabase==2.18.1",
    "python-dotenv",
    "lxml"
])

# Modal secrets for environment variables
secrets = [
    modal.Secret.from_name("database-credentials"),  # Supabase credentials
    modal.Secret.from_name("congress-api-credentials"),  # Congress.gov API keys
]

@dataclass
class CongressionalHearing:
    """Data structure for congressional hearings"""
    congress: int
    hearing_type: str
    hearing_subtype: Optional[str]
    committee: str
    hearing_date: str  # ISO format for JSON serialization
    hearing_name: str
    serial_no: Optional[str]
    detail_url: str
    document_url: Optional[str]
    members: List[str]
    witnesses: List[Dict[str, str]]
    bill_numbers: List[str]

class APIKeyManager:
    """Manages rotation across all 82 Congress.gov API keys"""
    
    def __init__(self):
        # Extract all Congress.gov API keys from environment
        self.api_keys = []
        missing_keys = []
        for i in range(1, 83):  # Keys 1-82
            key_name = f"CONGRESS_GOV_API_KEY" if i == 1 else f"CONGRESS_GOV_API_KEY_{i}"
            key_value = os.getenv(key_name)
            if key_value:
                self.api_keys.append(key_value)
            else:
                missing_keys.append(key_name)
        
        print(f"🔑 Loaded {len(self.api_keys)} Congress.gov API keys")
        if missing_keys:
            print(f"⚠️  Missing keys: {missing_keys[:5]}..." if len(missing_keys) > 5 else f"⚠️  Missing keys: {missing_keys}")
        
        self.current_index = 0
        self.request_counts = {key: 0 for key in self.api_keys}
    
    def get_next_key(self) -> str:
        """Get next API key in rotation"""
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        key = self.api_keys[self.current_index]
        self.request_counts[key] += 1
        
        # Rotate to next key
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        
        return key
    
    def get_random_key(self) -> str:
        """Get random API key for parallel processing"""
        return random.choice(self.api_keys)

class CongressAPIClient:
    """Enhanced Congress.gov API client with multi-key support"""
    
    def __init__(self, key_manager: APIKeyManager):
        self.key_manager = key_manager
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CongressionalHearingsBot/1.0 (Educational Research)'
        })
    
    def search_hearings(self, congress: str, chamber: str, limit: int = 250) -> List[Dict[str, Any]]:
        """Search for hearings with API key rotation"""
        api_key = self.key_manager.get_next_key()
        url = f"{self.base_url}/hearing"
        params = {
            'api_key': api_key,
            'format': 'json',
            'congress': congress,
            'chamber': chamber,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('hearings', [])
            
        except Exception as e:
            print(f"⚠️  Error searching hearings: {e}")
            return []
    
    def get_hearing_details(self, congress: str, chamber: str, hearing_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed hearing information"""
        api_key = self.key_manager.get_next_key()
        url = f"{self.base_url}/hearing/{congress}/{chamber}/{hearing_id}"
        params = {'api_key': api_key, 'format': 'json'}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('hearing', {})
            
        except Exception as e:
            print(f"⚠️  Error getting hearing details for {hearing_id}: {e}")
            return None
    
    def get_witnesses_from_html(self, html_url: str) -> List[Dict[str, str]]:
        """Extract witnesses from hearing HTML document"""
        if not html_url:
            return []
        
        try:
            api_key = self.key_manager.get_next_key()
            
            # Add API key to URL if needed
            if 'api_key=' not in html_url:
                separator = '&' if '?' in html_url else '?'
                html_url = f"{html_url}{separator}api_key={api_key}"
            
            response = self.session.get(html_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            witnesses = []
            
            # Look for witnesses section
            lines = text.split('\n')
            in_witnesses_section = False
            
            for line in lines:
                line = line.strip()
                
                # Start of witnesses section
                if re.match(r'^\s*Witnesses\s*$', line, re.IGNORECASE):
                    in_witnesses_section = True
                    continue
                
                # End of witnesses section
                if in_witnesses_section and any(marker in line.lower() for marker in [
                    'opening statement', 'prepared statement', 'discussion', 'questions'
                ]):
                    break
                
                # Extract witness names
                if in_witnesses_section and line:
                    # Look for name patterns (usually comma-separated with titles)
                    if ',' in line and len(line) < 200:
                        parts = [part.strip() for part in line.split(',')]
                        if len(parts) >= 2:
                            # First part is usually the name
                            name = parts[0].strip()
                            # Skip if it looks like a page number or header
                            if (name and 
                                not re.match(r'^\d+$', name) and 
                                len(name) > 2 and 
                                not name.lower().startswith('page')):
                                # Create structured witness object (matching house_gov_scraper format)
                                witness_obj = {
                                    "name": name,
                                    "title": parts[1].strip() if len(parts) > 1 else "",
                                    "organization": parts[2].strip() if len(parts) > 2 else ""
                                }
                                witnesses.append(witness_obj)
            
            return witnesses[:10]  # Limit to reasonable number
            
        except Exception as e:
            print(f"⚠️  Error extracting witnesses from HTML: {e}")
            return []

@app.function(
    image=image,
    secrets=secrets,
    timeout=3600,  # 1 hour timeout
    cpu=2.0,
    memory=4096
)
def scrape_congress_hearings_batch(congress_list: List[int], chamber: str, batch_size: int = 50) -> List[Dict[str, Any]]:
    """Scrape hearings for multiple congress sessions"""
    from supabase import create_client
    
    # Initialize components
    key_manager = APIKeyManager()
    api_client = CongressAPIClient(key_manager)
    
    # Initialize Supabase - use witness database
    supabase_url = os.environ.get('WITNESS_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('WITNESS_SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    print(f"🔗 Connecting to Supabase: {supabase_url}")
    supabase = create_client(supabase_url, supabase_key)
    
    all_hearings = []
    
    for congress in congress_list:
        print(f"🏛️  Scraping {chamber} hearings for Congress {congress}...")
        
        # Search for hearings
        hearing_summaries = api_client.search_hearings(str(congress), chamber, limit=batch_size)
        print(f"📋 Found {len(hearing_summaries)} {chamber} hearings for Congress {congress}")
        
        processed_count = 0
        error_count = 0
        
        for summary in hearing_summaries:
            try:
                hearing_id = summary.get('jacketNumber', '')
                if not hearing_id:
                    continue
                
                # Get detailed hearing info
                hearing_details = api_client.get_hearing_details(str(congress), chamber, str(hearing_id))
                
                if not hearing_details:
                    error_count += 1
                    continue
                
                # Extract basic info
                title = hearing_details.get('title', '')
                dates = hearing_details.get('dates', [])
                committees = hearing_details.get('committees', [])
                formats = hearing_details.get('formats', [])
                
                # Parse date
                hearing_date = None
                if dates and len(dates) > 0:
                    date_str = dates[0].get('date', '')
                    if date_str:
                        try:
                            hearing_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            continue
                
                if not hearing_date:
                    continue
                
                # Extract committee
                committee_name = ""
                if committees and len(committees) > 0:
                    committee_name = committees[0].get('name', '')
                
                # Determine subtype
                hearing_subtype = None
                if 'subcommittee' in title.lower():
                    hearing_subtype = 'subcommittee'
                
                # Get document URLs
                document_url = None
                html_url = None
                
                for format_info in formats:
                    format_type = format_info.get('type', '').lower()
                    url = format_info.get('url', '')
                    
                    if 'pdf' in format_type:
                        document_url = url
                    elif 'html' in format_type or 'formatted text' in format_type:
                        html_url = url
                
                # Extract witnesses from HTML
                witnesses = []
                if html_url:
                    witnesses = api_client.get_witnesses_from_html(html_url)
                
                # Create hearing object
                hearing = CongressionalHearing(
                    congress=congress,
                    hearing_type=chamber,
                    hearing_subtype=hearing_subtype,
                    committee=committee_name,
                    hearing_date=hearing_date.isoformat(),
                    hearing_name=title,
                    serial_no=str(hearing_id),
                    detail_url=f"https://api.congress.gov/v3/hearing/{congress}/{chamber}/{hearing_id}",
                    document_url=document_url,
                    members=[],  # Not available from API
                    witnesses=witnesses,
                    bill_numbers=[]  # Could extract from content
                )
                
                hearing_dict = asdict(hearing)
                all_hearings.append(hearing_dict)
                processed_count += 1
                
                # Log successful hearing processing
                print(f"✅ Processed: {title[:50]}... (Congress {congress}, {len(witnesses)} witnesses)")
                
                # Rate limiting per key
                time.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                print(f"⚠️  Error processing hearing {hearing_id}: {e}")
                continue
        
        print(f"📊 Congress {congress} {chamber} summary: {processed_count} processed, {error_count} errors")
        
        # Only continue if we got at least some valid hearings
        if processed_count == 0:
            print(f"⚠️  No valid hearings found for Congress {congress} {chamber} - skipping database insertion")
            return []
    
    print(f"✅ Scraped {len(all_hearings)} hearings total")
    return all_hearings

@app.function(
    image=image,
    secrets=secrets,
    timeout=300,  # 5 minute timeout
    cpu=1.0,
    memory=2048
)
def insert_hearings_to_supabase(hearings: List[Dict[str, Any]]) -> Dict[str, int]:
    """Insert hearings into Supabase database"""
    from supabase import create_client
    
    supabase_url = os.environ.get('WITNESS_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('WITNESS_SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    supabase = create_client(supabase_url, supabase_key)
    
    results = {
        'total': len(hearings),
        'inserted': 0,
        'skipped': 0,
        'failed': 0
    }
    
    print(f"🔍 Starting insertion of {len(hearings)} hearings...")
    
    for i, hearing in enumerate(hearings):
        try:
            # Check if hearing already exists
            detail_url = hearing['detail_url']
            existing = supabase.table('congressional_hearings').select('id, hearing_name, created_at').eq('detail_url', detail_url).execute()
            
            if existing.data:
                results['skipped'] += 1
                existing_hearing = existing.data[0]
                print(f"⏭️  DUPLICATE FOUND:")
                print(f"     New: {hearing.get('hearing_name', 'Unknown')[:50]}...")
                print(f"     Existing: {existing_hearing.get('hearing_name', 'Unknown')[:50]}...")
                print(f"     URL: {detail_url}")
                print(f"     Created: {existing_hearing.get('created_at', 'Unknown')}")
                continue
            
            # LOG THE EXACT DATA BEING INSERTED
            print(f"📝 INSERTING HEARING DATA:")
            print(f"   Name: {hearing.get('hearing_name', 'Unknown')}")
            print(f"   Congress: {hearing.get('congress')}")
            print(f"   Type: {hearing.get('hearing_type')}")
            print(f"   Committee: {hearing.get('committee')}")
            print(f"   Date: {hearing.get('hearing_date')}")
            print(f"   Witnesses: {hearing.get('witnesses', [])}")
            print(f"   Witness Count: {len(hearing.get('witnesses', []))}")
            print(f"   Full Data Structure: {hearing}")
            
            # Insert hearing
            result = supabase.table('congressional_hearings').insert(hearing).execute()
            
            if result.data:
                results['inserted'] += 1
                record_id = result.data[0].get('id')
                print(f"✅ SUCCESS: Inserted hearing ID {record_id}")
                print(f"   Name: {hearing.get('hearing_name', 'Unknown')[:50]}...")
            else:
                results['failed'] += 1
                print(f"❌ FAILED: No data returned from insert")
                print(f"   Hearing: {hearing.get('hearing_name', 'Unknown')}")
                print(f"   Result object: {result}")
                print(f"   Result data: {getattr(result, 'data', 'No data attr')}")
                print(f"   Result error: {getattr(result, 'error', 'No error attr')}")
                
        except Exception as e:
            print(f"❌ DATABASE EXCEPTION for '{hearing.get('hearing_name', 'Unknown')[:30]}...':")
            print(f"   Error: {e}")
            print(f"   Error type: {type(e)}")
            print(f"   Hearing data keys: {list(hearing.keys())}")
            print(f"   Hearing data sample: {dict(list(hearing.items())[:3])}")
            if hasattr(e, 'details'):
                print(f"   Error details: {e.details}")
            if hasattr(e, 'message'):
                print(f"   Error message: {e.message}")
            results['failed'] += 1
    
    print(f"📊 Batch results: {results['inserted']} inserted, {results['skipped']} skipped, {results['failed']} failed")
    
    return results

@app.local_entrypoint()
def main():
    """Main entry point for Modal deployment"""
    print("🚀 Congressional Hearings Scraper - Modal Deployment")
    print("=" * 60)
    
    # Configuration - test run to verify fix
    congress_sessions = [118]  # Just current congress for testing
    chambers = ['house']  # Just house for testing  
    batch_size = 10  # Small batch for testing
    
    total_results = {
        'total_scraped': 0,
        'total_inserted': 0,
        'total_skipped': 0,
        'total_failed': 0
    }
    
    for chamber in chambers:
        print(f"\n🏛️  Processing {chamber.upper()} hearings...")
        
        # Scrape hearings in parallel batches
        scraping_jobs = []
        
        # Split congress sessions into batches for parallel processing
        for i in range(0, len(congress_sessions), 2):  # Process 2 congress sessions per batch
            batch_congress = congress_sessions[i:i+2]
            job = scrape_congress_hearings_batch.spawn(batch_congress, chamber, batch_size)
            scraping_jobs.append(job)
        
        # Collect results from parallel jobs
        all_chamber_hearings = []
        for job in scraping_jobs:
            batch_hearings = job.get()
            all_chamber_hearings.extend(batch_hearings)
        
        print(f"📊 Total {chamber} hearings scraped: {len(all_chamber_hearings)}")
        total_results['total_scraped'] += len(all_chamber_hearings)
        
        # Insert hearings to database in batches
        if all_chamber_hearings:
            # Split into chunks for parallel insertion
            chunk_size = 50
            insertion_jobs = []
            
            for i in range(0, len(all_chamber_hearings), chunk_size):
                chunk = all_chamber_hearings[i:i+chunk_size]
                job = insert_hearings_to_supabase.spawn(chunk)
                insertion_jobs.append(job)
            
            # Collect insertion results
            for job in insertion_jobs:
                results = job.get()
                total_results['total_inserted'] += results['inserted']
                total_results['total_skipped'] += results['skipped']
                total_results['total_failed'] += results['failed']
    
    # Final results
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Total hearings scraped: {total_results['total_scraped']}")
    print(f"   Successfully inserted: {total_results['total_inserted']}")
    print(f"   Already existed (skipped): {total_results['total_skipped']}")
    print(f"   Failed insertions: {total_results['total_failed']}")
    
    efficiency = (total_results['total_inserted'] / max(total_results['total_scraped'], 1)) * 100
    print(f"   Insertion efficiency: {efficiency:.1f}%")
    
    print(f"\n💡 Your congressional_hearings table has been populated!")
    print(f"🔍 Next steps:")
    print(f"   1. Query your data: SELECT COUNT(*) FROM congressional_hearings;")
    print(f"   2. Check witness counts: SELECT hearing_name, jsonb_array_length(witnesses) FROM congressional_hearings;")
    print(f"   3. Analyze by committee: SELECT committee, COUNT(*) FROM congressional_hearings GROUP BY committee;")

if __name__ == "__main__":
    main()