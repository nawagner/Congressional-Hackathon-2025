"""
Congressional Hearings API for v0 Frontend
FastAPI backend that provides clean endpoints for the congressional_hearings table
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Congressional Hearings API",
    description="API for congressional hearings and witness data",
    version="1.0.0"
)

# CORS middleware for v0 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
def get_supabase_client():
    url = os.getenv("WITNESS_SUPABASE_URL")
    key = os.getenv("WITNESS_SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise HTTPException(status_code=500, detail="Missing Supabase configuration")
    
    return create_client(url, key)

# Pydantic models for API responses
class WitnessInfo(BaseModel):
    name: str
    title: Optional[str] = None
    witness_type: Optional[str] = None
    panel_number: Optional[int] = None
    organization: Optional[str] = None
    organization_type: Optional[str] = None
    tribal_affiliation: Optional[str] = None
    expertise_areas: List[str] = []
    topics: List[str] = []
    keywords: List[str] = []
    documents: List[Dict[str, Any]] = []

class HearingResponse(BaseModel):
    id: int
    congress: int
    hearing_type: str
    hearing_subtype: Optional[str] = None
    committee: str
    hearing_date: date
    hearing_name: str
    serial_no: Optional[str] = None
    detail_url: str
    document_url: Optional[str] = None
    members: List[Dict[str, Any]] = []
    witnesses: List[WitnessInfo] = []
    bill_numbers: List[str] = []
    created_at: datetime
    updated_at: datetime

class HearingSummary(BaseModel):
    id: int
    hearing_name: str
    committee: str
    hearing_date: date
    hearing_type: str
    witness_count: int
    detail_url: str

class CommitteeSummary(BaseModel):
    committee: str
    hearing_count: int
    total_witnesses: int
    latest_hearing: Optional[date] = None
    earliest_hearing: Optional[date] = None

class StatsResponse(BaseModel):
    total_hearings: int
    total_witnesses: int
    total_committees: int
    date_range: Dict[str, Optional[str]]
    hearing_types: Dict[str, int]
    top_committees: List[Dict[str, Any]]

# API Endpoints

@app.get("/", summary="API Health Check")
async def root():
    """Health check endpoint"""
    return {
        "message": "Congressional Hearings API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/hearings", response_model=List[HearingSummary], summary="List all hearings")
async def get_hearings(
    limit: int = Query(50, ge=1, le=500, description="Number of hearings to return"),
    offset: int = Query(0, ge=0, description="Number of hearings to skip"),
    committee: Optional[str] = Query(None, description="Filter by committee name"),
    hearing_type: Optional[str] = Query(None, description="Filter by hearing type (house/senate/joint)"),
    congress: Optional[int] = Query(None, description="Filter by congress number"),
    start_date: Optional[date] = Query(None, description="Filter hearings after this date"),
    end_date: Optional[date] = Query(None, description="Filter hearings before this date")
):
    """Get list of hearings with summary information"""
    
    supabase = get_supabase_client()
    
    try:
        # Build query
        query = supabase.table("congressional_hearings").select(
            "id, hearing_name, committee, hearing_date, hearing_type, detail_url, witnesses"
        )
        
        # Apply filters
        if committee:
            query = query.ilike("committee", f"%{committee}%")
        if hearing_type:
            query = query.eq("hearing_type", hearing_type)
        if congress:
            query = query.eq("congress", congress)
        if start_date:
            query = query.gte("hearing_date", start_date.isoformat())
        if end_date:
            query = query.lte("hearing_date", end_date.isoformat())
        
        # Order and paginate
        query = query.order("hearing_date", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        # Transform data
        hearings = []
        for hearing in result.data:
            witnesses = json.loads(hearing.get("witnesses", "[]"))
            hearings.append(HearingSummary(
                id=hearing["id"],
                hearing_name=hearing["hearing_name"],
                committee=hearing["committee"],
                hearing_date=datetime.fromisoformat(hearing["hearing_date"]).date(),
                hearing_type=hearing["hearing_type"],
                witness_count=len(witnesses),
                detail_url=hearing["detail_url"]
            ))
        
        return hearings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/hearings/{hearing_id}", response_model=HearingResponse, summary="Get hearing details")
async def get_hearing(hearing_id: int):
    """Get detailed information about a specific hearing"""
    
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("congressional_hearings").select("*").eq("id", hearing_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Hearing not found")
        
        hearing_data = result.data[0]
        
        # Parse JSON fields
        witnesses_json = json.loads(hearing_data.get("witnesses", "[]"))
        members_json = json.loads(hearing_data.get("members", "[]"))
        
        # Transform witnesses data
        witnesses = []
        for w in witnesses_json:
            witnesses.append(WitnessInfo(**w))
        
        return HearingResponse(
            id=hearing_data["id"],
            congress=hearing_data["congress"],
            hearing_type=hearing_data["hearing_type"],
            hearing_subtype=hearing_data.get("hearing_subtype"),
            committee=hearing_data["committee"],
            hearing_date=datetime.fromisoformat(hearing_data["hearing_date"]).date(),
            hearing_name=hearing_data["hearing_name"],
            serial_no=hearing_data.get("serial_no"),
            detail_url=hearing_data["detail_url"],
            document_url=hearing_data.get("document_url"),
            members=members_json,
            witnesses=witnesses,
            bill_numbers=hearing_data.get("bill_numbers", []),
            created_at=datetime.fromisoformat(hearing_data["created_at"]),
            updated_at=datetime.fromisoformat(hearing_data["updated_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/witnesses", summary="Search witnesses")
async def search_witnesses(
    query: Optional[str] = Query(None, description="Search term for witness names, titles, or organizations"),
    witness_type: Optional[str] = Query(None, description="Filter by witness type"),
    committee: Optional[str] = Query(None, description="Filter by committee"),
    limit: int = Query(50, ge=1, le=500)
):
    """Search for witnesses across all hearings"""
    
    supabase = get_supabase_client()
    
    try:
        # Get hearings data
        db_query = supabase.table("congressional_hearings").select("id, hearing_name, committee, hearing_date, witnesses")
        
        if committee:
            db_query = db_query.ilike("committee", f"%{committee}%")
        
        db_query = db_query.order("hearing_date", desc=True)
        result = db_query.execute()
        
        witnesses = []
        
        for hearing in result.data:
            witnesses_json = json.loads(hearing.get("witnesses", "[]"))
            
            for witness in witnesses_json:
                # Apply filters
                if witness_type and witness.get("witness_type") != witness_type:
                    continue
                
                if query:
                    searchable_text = (
                        witness.get("name", "") + " " +
                        witness.get("title", "") + " " +
                        witness.get("organization", "")
                    ).lower()
                    
                    if query.lower() not in searchable_text:
                        continue
                
                # Add hearing context
                witness_with_context = {
                    **witness,
                    "hearing_id": hearing["id"],
                    "hearing_name": hearing["hearing_name"],
                    "committee": hearing["committee"],
                    "hearing_date": hearing["hearing_date"]
                }
                
                witnesses.append(witness_with_context)
                
                if len(witnesses) >= limit:
                    break
            
            if len(witnesses) >= limit:
                break
        
        return witnesses[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/committees", response_model=List[CommitteeSummary], summary="Get committee statistics")
async def get_committees():
    """Get statistics for all committees"""
    
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("congressional_hearings").select("committee, hearing_date, witnesses").execute()
        
        committee_stats = {}
        
        for hearing in result.data:
            committee = hearing["committee"]
            hearing_date = datetime.fromisoformat(hearing["hearing_date"]).date()
            witnesses_count = len(json.loads(hearing.get("witnesses", "[]")))
            
            if committee not in committee_stats:
                committee_stats[committee] = {
                    "committee": committee,
                    "hearing_count": 0,
                    "total_witnesses": 0,
                    "earliest_hearing": hearing_date,
                    "latest_hearing": hearing_date
                }
            
            stats = committee_stats[committee]
            stats["hearing_count"] += 1
            stats["total_witnesses"] += witnesses_count
            
            if hearing_date < stats["earliest_hearing"]:
                stats["earliest_hearing"] = hearing_date
            if hearing_date > stats["latest_hearing"]:
                stats["latest_hearing"] = hearing_date
        
        # Convert to list and sort by hearing count
        committees = list(committee_stats.values())
        committees.sort(key=lambda x: x["hearing_count"], reverse=True)
        
        return [CommitteeSummary(**committee) for committee in committees]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/hearings-count", summary="Get total number of hearings")
async def get_hearings_count():
    """Get just the total count of hearings - perfect for v0 metrics"""
    
    supabase = get_supabase_client()
    
    try:
        # Simple count query
        result = supabase.table("congressional_hearings").select("id", count="exact").execute()
        
        return {
            "count": result.count,
            "message": "Total congressional hearings in database"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/hearings-number", summary="Get hearings count as plain number")
async def get_hearings_number():
    """Get just the number - simplest possible endpoint for v0"""
    
    supabase = get_supabase_client()
    
    try:
        # Simple count query
        result = supabase.table("congressional_hearings").select("id", count="exact").execute()
        
        # Return just the number
        return result.count
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/witnesses-count", summary="Get total number of unique witnesses")
async def get_unique_witnesses_count():
    """Get count of unique witnesses across all hearings - with pagination to get all records"""
    
    supabase = get_supabase_client()
    
    try:
        # Set to track unique witnesses (using name as identifier)
        unique_witnesses = set()
        
        # Pagination parameters
        page_size = 1000  # Supabase default max
        offset = 0
        
        while True:
            # Get batch of hearings with witnesses data
            result = supabase.table("congressional_hearings").select("witnesses").range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
                
            # Process witnesses in this batch
            for hearing in result.data:
                witnesses_data = hearing.get("witnesses", [])
                
                # Handle both string and array formats
                if isinstance(witnesses_data, str):
                    try:
                        witnesses = json.loads(witnesses_data)
                    except:
                        witnesses = []
                else:
                    witnesses = witnesses_data or []
                
                # Add unique witness names to set
                for witness in witnesses:
                    if isinstance(witness, dict) and witness.get("name"):
                        # Normalize name for deduplication (lowercase, strip whitespace)
                        normalized_name = witness["name"].lower().strip()
                        if normalized_name:
                            unique_witnesses.add(normalized_name)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        return {
            "count": len(unique_witnesses),
            "message": "Total unique witnesses across all congressional hearings"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/witnesses-number", summary="Get unique witnesses count as plain number")
async def get_unique_witnesses_number():
    """Get just the number of unique witnesses - simplest possible endpoint for v0"""
    
    supabase = get_supabase_client()
    
    try:
        # Set to track unique witnesses (using name as identifier)
        unique_witnesses = set()
        
        # Pagination parameters
        page_size = 1000  # Supabase default max
        offset = 0
        
        while True:
            # Get batch of hearings with witnesses data
            result = supabase.table("congressional_hearings").select("witnesses").range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
                
            # Process witnesses in this batch
            for hearing in result.data:
                witnesses_data = hearing.get("witnesses", [])
                
                # Handle both string and array formats
                if isinstance(witnesses_data, str):
                    try:
                        witnesses = json.loads(witnesses_data)
                    except:
                        witnesses = []
                else:
                    witnesses = witnesses_data or []
                
                # Add unique witness names to set
                for witness in witnesses:
                    if isinstance(witness, dict) and witness.get("name"):
                        # Normalize name for deduplication (lowercase, strip whitespace)
                        normalized_name = witness["name"].lower().strip()
                        if normalized_name:
                            unique_witnesses.add(normalized_name)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        # Return just the number
        return len(unique_witnesses)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/organizations-count", summary="Get total number of unique organizations")
async def get_unique_organizations_count():
    """Get count of unique organizations from witnesses across all hearings - with pagination to get all records"""
    
    supabase = get_supabase_client()
    
    try:
        # Set to track unique organizations (using organization name as identifier)
        unique_organizations = set()
        
        # Pagination parameters
        page_size = 1000  # Supabase default max
        offset = 0
        
        while True:
            # Get batch of hearings with witnesses data
            result = supabase.table("congressional_hearings").select("witnesses").range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
                
            # Process witnesses in this batch
            for hearing in result.data:
                witnesses_data = hearing.get("witnesses", [])
                
                # Handle both string and array formats
                if isinstance(witnesses_data, str):
                    try:
                        witnesses = json.loads(witnesses_data)
                    except:
                        witnesses = []
                else:
                    witnesses = witnesses_data or []
                
                # Add unique organization names to set
                for witness in witnesses:
                    if isinstance(witness, dict) and witness.get("organization"):
                        # Normalize organization name for deduplication (lowercase, strip whitespace)
                        normalized_org = witness["organization"].lower().strip()
                        if normalized_org:
                            unique_organizations.add(normalized_org)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        return {
            "count": len(unique_organizations),
            "message": "Total unique organizations from witness testimony data"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/metrics/organizations-number", summary="Get unique organizations count as plain number")
async def get_unique_organizations_number():
    """Get just the number of unique organizations - simplest possible endpoint for v0"""
    
    supabase = get_supabase_client()
    
    try:
        # Set to track unique organizations (using organization name as identifier)
        unique_organizations = set()
        
        # Pagination parameters
        page_size = 1000  # Supabase default max
        offset = 0
        
        while True:
            # Get batch of hearings with witnesses data
            result = supabase.table("congressional_hearings").select("witnesses").range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
                
            # Process witnesses in this batch
            for hearing in result.data:
                witnesses_data = hearing.get("witnesses", [])
                
                # Handle both string and array formats
                if isinstance(witnesses_data, str):
                    try:
                        witnesses = json.loads(witnesses_data)
                    except:
                        witnesses = []
                else:
                    witnesses = witnesses_data or []
                
                # Add unique organization names to set
                for witness in witnesses:
                    if isinstance(witness, dict) and witness.get("organization"):
                        # Normalize organization name for deduplication (lowercase, strip whitespace)
                        normalized_org = witness["organization"].lower().strip()
                        if normalized_org:
                            unique_organizations.add(normalized_org)
            
            # If we got less than page_size, we've reached the end
            if len(result.data) < page_size:
                break
                
            offset += page_size
        
        # Return just the number
        return len(unique_organizations)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/stats", response_model=StatsResponse, summary="Get overall statistics")
async def get_stats():
    """Get overall statistics about hearings and witnesses"""
    
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("congressional_hearings").select("*").execute()
        
        if not result.data:
            return StatsResponse(
                total_hearings=0,
                total_witnesses=0,
                total_committees=0,
                date_range={"earliest": None, "latest": None},
                hearing_types={},
                top_committees=[]
            )
        
        hearings = result.data
        total_hearings = len(hearings)
        total_witnesses = 0
        committees = set()
        hearing_types = {}
        committee_counts = {}
        dates = []
        
        for hearing in hearings:
            # Count witnesses
            witnesses_data = hearing.get("witnesses", [])
            if isinstance(witnesses_data, str):
                try:
                    witnesses = json.loads(witnesses_data)
                except:
                    witnesses = []
            else:
                witnesses = witnesses_data or []
            total_witnesses += len(witnesses)
            
            # Track committees
            committee = hearing["committee"]
            committees.add(committee)
            committee_counts[committee] = committee_counts.get(committee, 0) + 1
            
            # Track hearing types
            hearing_type = hearing["hearing_type"]
            hearing_types[hearing_type] = hearing_types.get(hearing_type, 0) + 1
            
            # Track dates
            dates.append(hearing["hearing_date"])
        
        # Date range
        dates.sort()
        date_range = {
            "earliest": dates[0] if dates else None,
            "latest": dates[-1] if dates else None
        }
        
        # Top committees
        top_committees = [
            {"committee": committee, "hearing_count": count}
            for committee, count in sorted(committee_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return StatsResponse(
            total_hearings=total_hearings,
            total_witnesses=total_witnesses,
            total_committees=len(committees),
            date_range=date_range,
            hearing_types=hearing_types,
            top_committees=top_committees
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Run the API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)