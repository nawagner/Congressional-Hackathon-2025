"""
Modal deployment for witness scraper processing.
Runs witness scraping on Modal's infrastructure for scalable processing.
"""

import modal
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Modal app setup
app = modal.App("witness-scraper")

# Modal image with required dependencies
image = modal.Image.debian_slim().pip_install([
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0", 
    "lxml>=4.9.0",
    "python-dateutil>=2.8.0",
    "networkx>=3.0",
    "matplotlib>=3.7.0",
    "plotly>=5.17.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "python-dotenv>=1.0.0",
    "supabase>=2.0.0"
]).add_local_dir(
    str(Path(__file__).parent.parent),
    remote_path="/app"
)

# Modal volumes for data persistence
volumes = {
    "/data": modal.Volume.from_name("witness-data", create_if_missing=True)
}

@app.function(
    image=image,
    volumes=volumes,
    secrets=[
        modal.Secret.from_name("database-credentials")
    ],
    timeout=3600,  # 1 hour timeout
    cpu=2.0,
    memory=4096
)
def scrape_house_witnesses(max_events: int = 10, save_to_supabase: bool = True):
    """
    Scrape House witness data using Modal infrastructure.
    
    Args:
        max_events: Maximum number of events to scrape
        save_to_supabase: Whether to save data to Supabase
        
    Returns:
        Dict with scraping results and output file path
    """
    import sys
    import os
    from pathlib import Path
    
    # Add app directory to Python path
    sys.path.insert(0, "/app")
    
    try:
        # Import the scraper modules from mounted files
        from scrapers.house_witness_scraper import HouseWitnessScraper
        from models.witness_data_schema import WitnessDatabase
        
        # Initialize scraper
        scraper = HouseWitnessScraper()
        
        # Run scraping
        print(f"Starting scraping of {max_events} events...")
        database = scraper.scrape_all_witnesses(max_events=max_events)
        
        # Save to volume as JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"/data/house_witnesses_{timestamp}.json"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(database.to_json(), f, indent=2, ensure_ascii=False)
        
        result = {
            "success": True,
            "witnesses_found": database.total_witnesses,
            "committees": len(database.committees),
            "hearings": len(database.hearings),
            "output_file": output_filename,
            "scrape_date": database.scrape_date.isoformat(),
            "supabase_saved": False
        }
        
        # Save to Supabase if requested and credentials available
        if save_to_supabase and os.getenv("SUPABASE_URL"):
            try:
                supabase_result = save_to_supabase_db(database)
                result["supabase_saved"] = True
                result["supabase_records"] = supabase_result
                print(f"✅ Data saved to Supabase: {supabase_result} records")
            except Exception as e:
                result["supabase_error"] = str(e)
                print(f"⚠️ Failed to save to Supabase: {e}")
        
        return result
        
    except Exception as e:
        import traceback
        return {"error": f"Scraping failed: {str(e)}", "traceback": traceback.format_exc()}

def save_to_supabase_db(database):
    """Save witness database to congressional_hearings table"""
    from supabase import create_client, Client
    import os
    import json
    import re
    
    url = os.getenv("WITNESS_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = os.getenv("WITNESS_SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise Exception("Missing Supabase credentials")
    
    supabase: Client = create_client(url, key)
    
    records_inserted = 0
    
    print(f"📊 Starting congressional_hearings insert: {len(database.hearings)} hearings with {len(database.witnesses)} total witnesses")
    
    # Process each hearing and its witnesses
    for hearing in database.hearings:
        try:
            # Get witnesses for this hearing
            hearing_witnesses = [w for w in database.witnesses if w.hearing.event_id == hearing.event_id]
            
            # Prepare witnesses JSONB data
            witnesses_json = []
            for witness in hearing_witnesses:
                witness_data = {
                    "name": witness.name,
                    "title": witness.title,
                    "witness_type": witness.witness_type.value,
                    "panel_number": witness.panel_number,
                    "organization": witness.organization.name if witness.organization else None,
                    "organization_type": witness.organization.organization_type if witness.organization else None,
                    "tribal_affiliation": witness.tribal_affiliation,
                    "expertise_areas": witness.expertise_areas,
                    "topics": witness.topics,
                    "keywords": witness.keywords,
                    "documents": [
                        {
                            "type": doc.document_type.value,
                            "url": doc.url,
                            "title": doc.title,
                            "format": doc.file_format
                        } for doc in witness.documents
                    ]
                }
                witnesses_json.append(witness_data)
            
            # Extract congress number from hearing event_id or title
            congress_number = 118  # Default to current congress
            if hearing.event_id:
                # Try to extract from event ID patterns
                match = re.search(r'(\d{3})', hearing.event_id)
                if match:
                    potential_congress = int(match.group(1))
                    if 100 <= potential_congress <= 120:  # Reasonable congress range
                        congress_number = potential_congress
            
            # Determine hearing type (House/Senate/Joint) from committee name
            hearing_type = "house"  # Default
            committee_name = hearing.committee.name.lower()
            if "senate" in committee_name:
                hearing_type = "senate"
            elif "joint" in committee_name:
                hearing_type = "joint"
            
            # Prepare hearing data for congressional_hearings table
            hearing_data = {
                "congress": congress_number,
                "hearing_type": hearing_type,
                "hearing_subtype": None,  # Could be extracted from title if needed
                "committee": hearing.committee.name,
                "hearing_date": hearing.date.date().isoformat(),
                "hearing_name": hearing.title,
                "serial_no": None,  # Not available from our scraper
                "detail_url": f"https://docs.house.gov/Committee/Calendar/ByEvent.aspx?EventID={hearing.event_id}",
                "document_url": None,  # Not available from our scraper
                "members": json.dumps([]),  # Empty for now, could be populated later
                "witnesses": json.dumps(witnesses_json),
                "bill_numbers": []  # Empty for now, could be extracted from titles
            }
            
            # Upsert hearing (update if exists, insert if new)
            result = supabase.table("congressional_hearings").upsert(
                hearing_data, 
                on_conflict="detail_url"
            ).execute()
            
            records_inserted += 1
            print(f"✅ Hearing: {hearing.title[:50]}... ({len(hearing_witnesses)} witnesses)")
            
        except Exception as e:
            print(f"❌ Error inserting hearing {hearing.event_id}: {e}")
    
    print(f"📊 Congressional hearings insert complete: {records_inserted} hearings with witness data")
    return records_inserted

@app.function(
    image=image,
    timeout=1800,  # 30 minutes
    cpu=1.0
)
def test_scraper_connection():
    """Test basic scraper connectivity and dependencies."""
    import sys
    sys.path.insert(0, "/app")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Test basic HTTP request
        response = requests.get("https://docs.house.gov", timeout=10)
        
        # Test scraper imports
        try:
            # Check what files are available
            import os
            files_available = os.listdir("/app")
            
            from scrapers.house_witness_scraper import HouseWitnessScraper
            from models.witness_data_schema import WitnessDatabase
            scraper_imports = True
        except ImportError as e:
            files_available = os.listdir("/app") if os.path.exists("/app") else ["No /app directory"]
            scraper_imports = f"Import error: {e}. Files in /app: {files_available}"
        
        return {
            "success": True,
            "status_code": response.status_code,
            "scraper_imports": scraper_imports,
            "message": "Scraper dependencies working correctly"
        }
    except Exception as e:
        return {"error": f"Connection test failed: {str(e)}"}

@app.local_entrypoint()
def main(max_events: int = 10, test_only: bool = False):
    """
    Main entry point for running the witness scraper on Modal.
    
    Usage:
        modal run modal_witness_scraper.py --max-events 20
        modal run modal_witness_scraper.py --test-only
    """
    print(f"🚀 Starting witness scraper on Modal...")
    
    if test_only:
        print("Running connectivity test...")
        result = test_scraper_connection.remote()
        print(f"Test result: {result}")
        return
    
    print(f"Scraping up to {max_events} events...")
    result = scrape_house_witnesses.remote(max_events)
    
    if result.get("success"):
        print("✅ Scraping completed successfully!")
        print(f"   Witnesses found: {result['witnesses_found']}")
        print(f"   Committees: {result['committees']}")
        print(f"   Hearings: {result['hearings']}")
        print(f"   Output file: {result['output_file']}")
        print(f"   Scrape date: {result['scrape_date']}")
    else:
        print(f"❌ Scraping failed: {result.get('error')}")

if __name__ == "__main__":
    # For local testing
    main()