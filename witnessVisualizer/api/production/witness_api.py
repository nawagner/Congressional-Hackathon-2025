#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os
from supabase import create_client, Client
from pydantic import BaseModel
from datetime import datetime, date
import json

# Initialize FastAPI app
app = FastAPI(
    title="Congressional Witness API",
    description="API for accessing congressional witness testimony data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client - try witness database first, then fallback to general
supabase_url = os.getenv("WITNESS_SUPABASE_URL") or os.getenv("SUPABASE_URL")
supabase_key = os.getenv("WITNESS_SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase credentials not found. Please set WITNESS_SUPABASE_URL and WITNESS_SUPABASE_SERVICE_ROLE_KEY or SUPABASE_URL and SUPABASE_KEY environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Pydantic models for API responses
class WitnessResponse(BaseModel):
    id: str
    witness_id: str
    name: str
    title: str
    witness_type: str
    organization_name: Optional[str] = None
    tribal_affiliation: Optional[str] = None
    topics: List[str] = []
    keywords: List[str] = []
    expertise_areas: List[str] = []
    document_count: int = 0
    created_at: datetime

class HearingResponse(BaseModel):
    id: str
    event_id: str
    title: str
    hearing_date: date
    hearing_time: Optional[str] = None
    location: str
    committee_name: str
    committee_code: str
    witness_count: int = 0
    created_at: datetime

class CommitteeResponse(BaseModel):
    id: str
    committee_code: str
    name: str
    parent_committee_id: Optional[str] = None
    created_at: datetime

class OrganizationResponse(BaseModel):
    id: str
    name: str
    organization_type: str
    location: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime

class TopicResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    document_type: str
    url: str
    title: str
    file_format: str
    created_at: datetime

class RelationshipResponse(BaseModel):
    id: str
    source_witness_name: str
    target_witness_name: str
    relationship_type: str
    strength: float
    context: Optional[str] = None

class StatsResponse(BaseModel):
    total_witnesses: int
    total_hearings: int
    total_committees: int
    total_organizations: int
    total_documents: int
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None

class CongressionalHearingResponse(BaseModel):
    id: int
    congress: int
    hearing_type: str
    hearing_subtype: Optional[str] = None
    committee: str
    hearing_date: str
    hearing_name: str
    serial_no: Optional[str] = None
    detail_url: str
    document_url: Optional[str] = None
    members: List[Any] = []
    witnesses: List[Any] = []
    bill_numbers: List[str] = []
    created_at: datetime
    updated_at: datetime

# API Endpoints

@app.get("/", summary="API Health Check")
async def root():
    """Health check endpoint"""
    return {"message": "Congressional Witness API is running", "version": "1.0.0"}

@app.get("/stats", response_model=StatsResponse, summary="Get Database Statistics")
async def get_stats():
    """Get overall database statistics"""
    try:
        # Get counts from congressional_hearings table
        hearings = supabase.table('congressional_hearings').select('id', count='exact').execute()
        
        # Get witness count by extracting from JSONB witnesses field
        witnesses_result = supabase.table('congressional_hearings').select('witnesses').execute()
        total_witnesses = 0
        for hearing in witnesses_result.data:
            if hearing.get('witnesses'):
                total_witnesses += len(hearing['witnesses'])
        
        # For now, set default values for other stats
        committees = type('obj', (object,), {'count': 50})()
        organizations = type('obj', (object,), {'count': 200})()
        documents = type('obj', (object,), {'count': 1000})()
        
        # Get date range
        date_range = supabase.table('congressional_hearings').select('hearing_date').order('hearing_date').execute()
        
        start_date = None
        end_date = None
        if date_range.data:
            start_date = date_range.data[0]['hearing_date']
            end_date = date_range.data[-1]['hearing_date']
        
        return StatsResponse(
            total_witnesses=total_witnesses,
            total_hearings=hearings.count or 0,
            total_committees=committees.count or 0,
            total_organizations=organizations.count or 0,
            total_documents=documents.count or 0,
            date_range_start=start_date,
            date_range_end=end_date
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@app.get("/witnesses", response_model=List[WitnessResponse], summary="Get All Witnesses")
async def get_witnesses(
    limit: int = Query(100, ge=1, le=1000, description="Number of witnesses to return"),
    offset: int = Query(0, ge=0, description="Number of witnesses to skip"),
    witness_type: Optional[str] = Query(None, description="Filter by witness type"),
    organization: Optional[str] = Query(None, description="Filter by organization name"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    search: Optional[str] = Query(None, description="Search witness names and titles")
):
    """Get witnesses with optional filtering and pagination"""
    try:
        query = supabase.table('congressional_hearings').select('witnesses,hearing_name,committee,hearing_date')
        
        # Apply filters
        if witness_type:
            query = query.eq('witness_type', witness_type)
        
        if organization:
            query = query.ilike('organization_name', f'%{organization}%')
        
        if topic:
            query = query.contains('topics', [topic])
        
        if search:
            query = query.or_(f'name.ilike.%{search}%,title.ilike.%{search}%')
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        witnesses = []
        for row in result.data:
            witnesses.append(WitnessResponse(
                id=row['id'],
                witness_id=row['witness_id'],
                name=row['name'],
                title=row['title'] or '',
                witness_type=row['witness_type'],
                organization_name=row['organization_name'],
                tribal_affiliation=row['tribal_affiliation'],
                topics=row['topics'] or [],
                keywords=row['keywords'] or [],
                expertise_areas=row['expertise_areas'] or [],
                document_count=row['document_count'] or 0,
                created_at=row['created_at']
            ))
        
        return witnesses
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witnesses: {str(e)}")

@app.get("/witnesses/{witness_id}", response_model=WitnessResponse, summary="Get Witness by ID")
async def get_witness(witness_id: str):
    """Get a specific witness by their ID"""
    try:
        result = supabase.table('congressional_hearings').select('witnesses,hearing_name,committee,hearing_date').execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Witness not found")
        
        row = result.data[0]
        return WitnessResponse(
            id=row['id'],
            witness_id=row['witness_id'],
            name=row['name'],
            title=row['title'] or '',
            witness_type=row['witness_type'],
            organization_name=row['organization_name'],
            tribal_affiliation=row['tribal_affiliation'],
            topics=row['topics'] or [],
            keywords=row['keywords'] or [],
            expertise_areas=row['expertise_areas'] or [],
            document_count=row['document_count'] or 0,
            created_at=row['created_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witness: {str(e)}")

@app.get("/hearings", response_model=List[HearingResponse], summary="Get All Hearings")
async def get_hearings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    committee: Optional[str] = Query(None, description="Filter by committee name"),
    start_date: Optional[date] = Query(None, description="Filter hearings after this date"),
    end_date: Optional[date] = Query(None, description="Filter hearings before this date")
):
    """Get hearings with optional filtering and pagination"""
    try:
        query = supabase.table('hearing_details_view').select('*')
        
        if committee:
            query = query.ilike('committee_name', f'%{committee}%')
        
        if start_date:
            query = query.gte('hearing_date', start_date.isoformat())
        
        if end_date:
            query = query.lte('hearing_date', end_date.isoformat())
        
        query = query.order('hearing_date', desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        hearings = []
        for row in result.data:
            hearings.append(HearingResponse(
                id=row['id'],
                event_id=row['event_id'],
                title=row['title'],
                hearing_date=row['hearing_date'],
                hearing_time=row['hearing_time'],
                location=row['location'] or '',
                committee_name=row['committee_name'],
                committee_code=row['committee_code'],
                witness_count=row['witness_count'] or 0,
                created_at=row['created_at']
            ))
        
        return hearings
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving hearings: {str(e)}")

@app.get("/hearings/{event_id}/witnesses", response_model=List[WitnessResponse], summary="Get Witnesses for Hearing")
async def get_hearing_witnesses(event_id: str):
    """Get all witnesses who testified at a specific hearing"""
    try:
        # First check if hearing exists
        hearing_result = supabase.table('hearings').select('id').eq('event_id', event_id).execute()
        if not hearing_result.data:
            raise HTTPException(status_code=404, detail="Hearing not found")
        
        hearing_id = hearing_result.data[0]['id']
        
        # Get witnesses for this hearing
        result = supabase.table('congressional_hearings').select('witnesses,hearing_name,committee,hearing_date') \
            .in_('id', 
                 supabase.table('witness_hearings').select('witness_id').eq('hearing_id', hearing_id).execute().data
            ).execute()
        
        witnesses = []
        for row in result.data:
            witnesses.append(WitnessResponse(
                id=row['id'],
                witness_id=row['witness_id'],
                name=row['name'],
                title=row['title'] or '',
                witness_type=row['witness_type'],
                organization_name=row['organization_name'],
                tribal_affiliation=row['tribal_affiliation'],
                topics=row['topics'] or [],
                keywords=row['keywords'] or [],
                expertise_areas=row['expertise_areas'] or [],
                document_count=row['document_count'] or 0,
                created_at=row['created_at']
            ))
        
        return witnesses
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving hearing witnesses: {str(e)}")

@app.get("/committees", response_model=List[CommitteeResponse], summary="Get All Committees")
async def get_committees():
    """Get all committees"""
    try:
        result = supabase.table('committees').select('*').order('name').execute()
        
        committees = []
        for row in result.data:
            committees.append(CommitteeResponse(
                id=row['id'],
                committee_code=row['committee_code'],
                name=row['name'],
                parent_committee_id=row.get('parent_committee_id'),
                created_at=row['created_at']
            ))
        
        return committees
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving committees: {str(e)}")

@app.get("/organizations", response_model=List[OrganizationResponse], summary="Get All Organizations")
async def get_organizations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all organizations with pagination"""
    try:
        result = supabase.table('organizations').select('*') \
            .order('name').range(offset, offset + limit - 1).execute()
        
        organizations = []
        for row in result.data:
            organizations.append(OrganizationResponse(
                id=row['id'],
                name=row['name'],
                organization_type=row['organization_type'] or '',
                location=row.get('location'),
                website=row.get('website'),
                created_at=row['created_at']
            ))
        
        return organizations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving organizations: {str(e)}")

@app.get("/topics", response_model=List[TopicResponse], summary="Get All Topics")
async def get_topics():
    """Get all available topics"""
    try:
        result = supabase.table('topics').select('*').order('display_name').execute()
        
        topics = []
        for row in result.data:
            topics.append(TopicResponse(
                id=row['id'],
                name=row['name'],
                display_name=row['display_name'] or row['name'],
                description=row.get('description')
            ))
        
        return topics
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving topics: {str(e)}")

@app.get("/witnesses/{witness_id}/documents", response_model=List[DocumentResponse], summary="Get Witness Documents")
async def get_witness_documents(witness_id: str):
    """Get all documents for a specific witness"""
    try:
        # First get the internal witness ID
        witness_result = supabase.table('witnesses').select('id').eq('witness_id', witness_id).execute()
        if not witness_result.data:
            raise HTTPException(status_code=404, detail="Witness not found")
        
        internal_id = witness_result.data[0]['id']
        
        result = supabase.table('documents').select('*').eq('witness_id', internal_id).execute()
        
        documents = []
        for row in result.data:
            documents.append(DocumentResponse(
                id=row['id'],
                document_type=row['document_type'],
                url=row['url'],
                title=row['title'],
                file_format=row['file_format'] or 'PDF',
                created_at=row['created_at']
            ))
        
        return documents
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witness documents: {str(e)}")

@app.get("/witnesses/{witness_id}/relationships", response_model=List[RelationshipResponse], summary="Get Witness Relationships")
async def get_witness_relationships(witness_id: str):
    """Get all relationships for a specific witness"""
    try:
        # Get internal witness ID
        witness_result = supabase.table('witnesses').select('id').eq('witness_id', witness_id).execute()
        if not witness_result.data:
            raise HTTPException(status_code=404, detail="Witness not found")
        
        internal_id = witness_result.data[0]['id']
        
        # Get relationships where this witness is source or target
        relationships_query = f"""
        SELECT 
            wr.id,
            w1.name as source_witness_name,
            w2.name as target_witness_name,
            wr.relationship_type,
            wr.strength,
            wr.context
        FROM witness_relationships wr
        JOIN witnesses w1 ON wr.source_witness_id = w1.id
        JOIN witnesses w2 ON wr.target_witness_id = w2.id
        WHERE wr.source_witness_id = '{internal_id}' OR wr.target_witness_id = '{internal_id}'
        """
        
        result = supabase.rpc('execute_sql', {'query': relationships_query}).execute()
        
        relationships = []
        for row in result.data:
            relationships.append(RelationshipResponse(
                id=row['id'],
                source_witness_name=row['source_witness_name'],
                target_witness_name=row['target_witness_name'],
                relationship_type=row['relationship_type'],
                strength=row['strength'],
                context=row.get('context')
            ))
        
        return relationships
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witness relationships: {str(e)}")

@app.get("/search", summary="Global Search")
async def search_all(
    q: str = Query(..., description="Search query"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type: witnesses, hearings, committees, organizations"),
    limit: int = Query(50, ge=1, le=200)
):
    """Global search across all entities"""
    try:
        results = {
            "query": q,
            "results": {}
        }
        
        if not entity_type or entity_type == "witnesses":
            witnesses = supabase.table('congressional_hearings').select('witnesses,hearing_name,committee') \
                .or_(f'name.ilike.%{q}%,title.ilike.%{q}%,organization_name.ilike.%{q}%') \
                .limit(limit).execute()
            results["results"]["witnesses"] = witnesses.data
        
        if not entity_type or entity_type == "hearings":
            hearings = supabase.table('hearing_details_view').select('event_id,title,committee_name,hearing_date') \
                .or_(f'title.ilike.%{q}%,committee_name.ilike.%{q}%') \
                .limit(limit).execute()
            results["results"]["hearings"] = hearings.data
        
        if not entity_type or entity_type == "committees":
            committees = supabase.table('committees').select('committee_code,name') \
                .or_(f'name.ilike.%{q}%,committee_code.ilike.%{q}%') \
                .limit(limit).execute()
            results["results"]["committees"] = committees.data
        
        if not entity_type or entity_type == "organizations":
            organizations = supabase.table('organizations').select('name,organization_type,location') \
                .ilike('name', f'%{q}%') \
                .limit(limit).execute()
            results["results"]["organizations"] = organizations.data
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")

# Congressional Hearings Endpoints
@app.get("/congressional-hearings", response_model=List[CongressionalHearingResponse], summary="Get Congressional Hearings")
async def get_congressional_hearings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    committee: Optional[str] = Query(None, description="Filter by committee name"),
    hearing_type: Optional[str] = Query(None, description="Filter by hearing type"),
    start_date: Optional[date] = Query(None, description="Filter hearings after this date"),
    end_date: Optional[date] = Query(None, description="Filter hearings before this date")
):
    """Get congressional hearings with optional filtering and pagination"""
    try:
        query = supabase.table('congressional_hearings').select('*')
        
        if committee:
            query = query.ilike('committee', f'%{committee}%')
        
        if hearing_type:
            query = query.eq('hearing_type', hearing_type)
        
        if start_date:
            query = query.gte('hearing_date', start_date.isoformat())
        
        if end_date:
            query = query.lte('hearing_date', end_date.isoformat())
        
        query = query.order('hearing_date', desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return result.data or []
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving congressional hearings: {str(e)}")

@app.get("/congressional-hearings/{hearing_id}", response_model=CongressionalHearingResponse, summary="Get Congressional Hearing by ID")
async def get_congressional_hearing(hearing_id: int):
    """Get a specific congressional hearing by ID"""
    try:
        result = supabase.table('congressional_hearings').select('*').eq('id', hearing_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Congressional hearing not found")
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving congressional hearing: {str(e)}")

@app.get("/congressional-hearings/stats", summary="Get Congressional Hearings Statistics")
async def get_congressional_hearings_stats():
    """Get statistics for congressional hearings"""
    try:
        # Total hearings count
        hearings_count = supabase.table('congressional_hearings').select('id', count='exact').execute()
        
        # Count unique witnesses across all hearings
        witnesses_data = supabase.table('congressional_hearings').select('witnesses').execute()
        all_witnesses = set()
        for hearing in witnesses_data.data or []:
            for witness in hearing.get('witnesses', []):
                if witness.get('name'):
                    all_witnesses.add(witness['name'])
        
        # Count unique committees
        committees_data = supabase.table('congressional_hearings').select('committee').execute()
        unique_committees = set(h['committee'] for h in committees_data.data or [])
        
        # Count total documents
        documents_data = supabase.table('congressional_hearings').select('document_url, witnesses').execute()
        total_documents = 0
        for hearing in documents_data.data or []:
            if hearing.get('document_url'):
                total_documents += 1
            for witness in hearing.get('witnesses', []):
                if witness.get('documents'):
                    total_documents += len(witness['documents'])
        
        return {
            "total_hearings": hearings_count.count or 0,
            "total_witnesses": len(all_witnesses),
            "total_committees": len(unique_committees),
            "total_documents": total_documents
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving congressional hearings stats: {str(e)}")

@app.get("/congressional-hearings/{hearing_id}/witnesses", summary="Get Witnesses for Congressional Hearing")
async def get_congressional_hearing_witnesses(hearing_id: int):
    """Get all witnesses for a specific congressional hearing"""
    try:
        result = supabase.table('congressional_hearings').select('witnesses').eq('id', hearing_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Congressional hearing not found")
        
        return result.data[0].get('witnesses', [])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving congressional hearing witnesses: {str(e)}")

@app.get("/committees/congressional", summary="Get Committee Statistics from Congressional Hearings")
async def get_congressional_committee_stats():
    """Get committee statistics from congressional hearings data"""
    try:
        result = supabase.table('congressional_hearings').select('committee, hearing_type').execute()
        
        committee_counts = {}
        for hearing in result.data or []:
            committee = hearing['committee']
            committee_counts[committee] = committee_counts.get(committee, 0) + 1
        
        return [
            {"name": committee, "count": count}
            for committee, count in sorted(committee_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving committee stats: {str(e)}")

@app.get("/witnesses/congressional", summary="Get All Witnesses from Congressional Hearings")
async def get_congressional_witnesses():
    """Get all unique witnesses from congressional hearings"""
    try:
        result = supabase.table('congressional_hearings').select('witnesses, hearing_name, committee, hearing_date').execute()
        
        all_witnesses = {}
        for hearing in result.data or []:
            for witness in hearing.get('witnesses', []):
                if witness.get('name'):
                    witness_name = witness['name']
                    if witness_name not in all_witnesses:
                        all_witnesses[witness_name] = {
                            "name": witness_name,
                            "title": witness.get('title', ''),
                            "organization": witness.get('organization', ''),
                            "hearings": [],
                            "committees": set(),
                            "topics": witness.get('topics', [])
                        }
                    
                    all_witnesses[witness_name]["hearings"].append(hearing['hearing_name'])
                    all_witnesses[witness_name]["committees"].add(hearing['committee'])
        
        # Convert sets to lists for JSON serialization
        for witness in all_witnesses.values():
            witness["committees"] = list(witness["committees"])
        
        return list(all_witnesses.values())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving congressional witnesses: {str(e)}")

# Simple metrics endpoints for frontend compatibility
@app.get("/metrics/hearings-number", summary="Get Total Hearings Count")
async def get_hearings_count():
    """Get total number of hearings (compatible with existing frontend)"""
    try:
        result = supabase.table('congressional_hearings').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        return 0

@app.get("/metrics/witnesses-number", summary="Get Total Witnesses Count")
async def get_witnesses_count():
    """Get total number of unique witnesses (compatible with existing frontend)"""
    try:
        result = supabase.table('congressional_hearings').select('witnesses').execute()
        all_witnesses = set()
        for hearing in result.data or []:
            for witness in hearing.get('witnesses', []):
                if witness.get('name'):
                    all_witnesses.add(witness['name'])
        return len(all_witnesses)
    except Exception as e:
        return 0

@app.get("/witnesses/all-simple", summary="Get All Witnesses Simple Format")
async def get_all_witnesses_simple():
    """Get all witnesses in simple format (follows same pattern as working metrics endpoints)"""
    try:
        result = supabase.table('congressional_hearings').select('witnesses, hearing_name, committee').execute()
        witnesses_list = []
        seen_witnesses = set()
        
        for hearing in result.data or []:
            hearing_name = hearing.get('hearing_name', '')
            committee = hearing.get('committee', '')
            
            for witness in hearing.get('witnesses', []):
                witness_name = witness.get('name', '').strip()
                if witness_name and witness_name not in seen_witnesses:
                    seen_witnesses.add(witness_name)
                    witnesses_list.append({
                        'name': witness_name,
                        'title': witness.get('title', ''),
                        'organization': witness.get('organization', ''),
                        'first_seen_hearing': hearing_name,
                        'first_seen_committee': committee
                    })
        
        return witnesses_list
    except Exception as e:
        return []

@app.get("/api/witnesses/all", summary="Get All Real Witnesses from Database")
async def get_all_witnesses():
    """Get all unique witnesses with their details from congressional hearings"""
    try:
        # Fetch all congressional hearings with witnesses data
        result = supabase.table('congressional_hearings').select('witnesses, hearing_name, committee, hearing_date').execute()
        
        # Dictionary to collect unique witnesses with aggregated data
        witnesses_map = {}
        
        for hearing in result.data or []:
            hearing_name = hearing.get('hearing_name', '')
            committee = hearing.get('committee', '')
            hearing_date = hearing.get('hearing_date', '')
            
            for witness in hearing.get('witnesses', []):
                if not witness.get('name'):
                    continue
                    
                witness_name = witness['name'].strip()
                
                if witness_name not in witnesses_map:
                    witnesses_map[witness_name] = {
                        'name': witness_name,
                        'title': witness.get('title', '').strip(),
                        'organization': witness.get('organization', '').strip(),
                        'topics': [],
                        'hearings': [],
                        'committees': set(),
                        'hearing_dates': []
                    }
                
                # Aggregate data for this witness
                witness_data = witnesses_map[witness_name]
                
                # Add hearing info
                if hearing_name:
                    witness_data['hearings'].append(hearing_name)
                    
                # Add committee
                if committee:
                    witness_data['committees'].add(committee)
                    
                # Add hearing date
                if hearing_date:
                    witness_data['hearing_dates'].append(hearing_date)
                
                # Extract topics from witness data if available
                if witness.get('topics'):
                    if isinstance(witness['topics'], list):
                        witness_data['topics'].extend(witness['topics'])
                    elif isinstance(witness['topics'], str):
                        witness_data['topics'].append(witness['topics'])
        
        # Convert to final format and clean up data
        witnesses_list = []
        for witness_name, data in witnesses_map.items():
            # Convert sets to lists and deduplicate
            committees_list = list(data['committees'])
            topics_list = list(set(data['topics'])) if data['topics'] else []
            
            # Infer topics from committee names if no explicit topics
            if not topics_list and committees_list:
                inferred_topics = []
                for committee in committees_list:
                    committee_lower = committee.lower()
                    if any(keyword in committee_lower for keyword in ['judiciary', 'justice', 'legal']):
                        inferred_topics.append('Legal Affairs')
                    elif any(keyword in committee_lower for keyword in ['energy', 'commerce', 'trade']):
                        inferred_topics.append('Energy & Commerce')
                    elif any(keyword in committee_lower for keyword in ['homeland', 'security', 'defense']):
                        inferred_topics.append('Security')
                    elif any(keyword in committee_lower for keyword in ['education', 'labor']):
                        inferred_topics.append('Education')
                    elif any(keyword in committee_lower for keyword in ['health', 'medical']):
                        inferred_topics.append('Healthcare')
                    elif any(keyword in committee_lower for keyword in ['technology', 'science', 'innovation']):
                        inferred_topics.append('Technology')
                    elif any(keyword in committee_lower for keyword in ['finance', 'banking', 'economic']):
                        inferred_topics.append('Finance')
                    elif any(keyword in committee_lower for keyword in ['environment', 'climate']):
                        inferred_topics.append('Environment')
                    else:
                        inferred_topics.append('Policy')
                        
                topics_list = list(set(inferred_topics))
            
            witness_record = {
                'name': data['name'],
                'title': data['title'],
                'organization': data['organization'],
                'topics': topics_list,
                'hearings': data['hearings'],
                'committees': committees_list,
                'hearing_count': len(data['hearings']),
                'most_recent_hearing': max(data['hearing_dates']) if data['hearing_dates'] else None
            }
            
            witnesses_list.append(witness_record)
        
        # Sort by number of hearings (most active witnesses first)
        witnesses_list.sort(key=lambda x: x['hearing_count'], reverse=True)
        
        return {
            'total_witnesses': len(witnesses_list),
            'witnesses': witnesses_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witnesses: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)