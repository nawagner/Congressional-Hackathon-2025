#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
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
    allow_origins=["*"],
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
class WitnessSimple(BaseModel):
    name: str
    title: Optional[str] = None
    organization: Optional[str] = None
    topics: List[str] = []
    hearings: List[str] = []
    committees: List[str] = []

class StatsResponse(BaseModel):
    total_witnesses: int
    total_hearings: int
    total_organizations: int
    total_documents: int

# API Endpoints

@app.get("/", summary="API Health Check")
async def root():
    """Health check endpoint"""
    return {"message": "Congressional Witness API is running", "version": "1.0.0"}

async def _get_deduplicated_witnesses():
    """Internal function to get deduplicated witnesses - shared logic for all endpoints"""
    # Get all hearings with witness data
    result = supabase.table('congressional_hearings').select('witnesses,hearing_name,committee,hearing_date').execute()
    
    witness_dict = {}
    
    for hearing in result.data:
        witnesses = hearing.get('witnesses', [])
        hearing_name = hearing.get('hearing_name', '')
        committee = hearing.get('committee', '')
        
        for witness in witnesses:
            if isinstance(witness, dict):
                name = witness.get('name', '')
                if name:
                    name = name.strip()
                organization = witness.get('organization', '') or ''
                if organization:
                    organization = organization.strip()
                
                if name:
                    # Create a unique key combining name and organization for better deduplication
                    # This handles cases where same person might have slight org variations
                    unique_key = f"{name}|{organization}".lower()
                    
                    if unique_key not in witness_dict:
                        witness_dict[unique_key] = {
                            'name': name,
                            'title': witness.get('title', ''),
                            'organization': organization,
                            'topics': [],
                            'hearings': [],
                            'committees': []
                        }
                    else:
                        # Update title if current one is empty but new one has content
                        current_title = witness_dict[unique_key]['title']
                        new_title = witness.get('title', '')
                        if not current_title and new_title:
                            witness_dict[unique_key]['title'] = new_title
                    
                    # Add hearing and committee if not already present
                    if hearing_name and hearing_name not in witness_dict[unique_key]['hearings']:
                        witness_dict[unique_key]['hearings'].append(hearing_name)
                    if committee and committee not in witness_dict[unique_key]['committees']:
                        witness_dict[unique_key]['committees'].append(committee)
    
    # Convert to list
    return list(witness_dict.values())

@app.get("/witnesses/all-simple", response_model=List[WitnessSimple], summary="Get All Witnesses (Simple)")
async def get_all_witnesses_simple():
    """Get all witnesses extracted from congressional hearings JSONB data"""
    try:
        return await _get_deduplicated_witnesses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witnesses: {str(e)}")

@app.get("/witnesses/congressional", response_model=List[WitnessSimple], summary="Get Congressional Witnesses")
async def get_congressional_witnesses():
    """Alias for get_all_witnesses_simple"""
    try:
        return await _get_deduplicated_witnesses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witnesses: {str(e)}")

@app.get("/witnesses", response_model=List[WitnessSimple], summary="Get Witnesses with Pagination")
async def get_witnesses(limit: int = 50, offset: int = 0):
    """Get witnesses with pagination"""
    try:
        all_witnesses = await _get_deduplicated_witnesses()
        return all_witnesses[offset:offset + limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witnesses: {str(e)}")

@app.get("/witnesses/all", summary="Get All Witnesses (Comprehensive)")
async def get_all_witnesses_comprehensive():
    """Get all witnesses with comprehensive data structure"""
    try:
        witnesses = await _get_deduplicated_witnesses()
        return {
            "witnesses": witnesses,
            "count": len(witnesses),
            "metadata": {
                "source": "congressional_hearings",
                "extracted_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving witnesses: {str(e)}")

@app.get("/metrics/witnesses-number", summary="Get Total Witness Count")
async def get_witness_count():
    """Get total number of unique witnesses"""
    try:
        witnesses = await _get_deduplicated_witnesses()
        return len(witnesses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting witnesses: {str(e)}")

@app.get("/metrics/hearings-number", summary="Get Total Hearing Count")
async def get_hearing_count():
    """Get total number of hearings"""
    try:
        result = supabase.table('congressional_hearings').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting hearings: {str(e)}")

@app.get("/metrics/organizations-number", summary="Get Total Organization Count")
async def get_organization_count():
    """Get total number of unique organizations"""
    try:
        witnesses = await _get_deduplicated_witnesses()
        organizations = set()
        for witness in witnesses:
            if witness['organization'] and witness['organization'].strip():
                organizations.add(witness['organization'].strip())
        return len(organizations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting organizations: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)