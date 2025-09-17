#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from supabase import create_client, Client
from ..models.witness_data_schema import WitnessDatabase, Witness, Hearing, Committee, Organization, Document

class SupabaseWitnessLoader:
    """Loads witness data from JSON into Supabase database"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Cache for IDs to avoid duplicates
        self.committee_cache = {}
        self.organization_cache = {}
        self.topic_cache = {}
        self.witness_cache = {}
        self.hearing_cache = {}
    
    def load_from_json(self, json_file: str, session_notes: str = None) -> Dict[str, int]:
        """Load witness data from JSON file into Supabase"""
        print(f"Loading data from {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create scraping session record
        session_id = self._create_scraping_session(data, session_notes)
        
        stats = {
            'committees': 0,
            'organizations': 0,
            'hearings': 0,
            'witnesses': 0,
            'documents': 0,
            'topics': 0,
            'relationships': 0
        }
        
        # Load data in dependency order
        stats['committees'] = self._load_committees(data.get('committees', []))
        stats['organizations'] = self._load_organizations(data.get('witnesses', []))
        stats['hearings'] = self._load_hearings(data.get('hearings', []))
        stats['witnesses'] = self._load_witnesses(data.get('witnesses', []))
        stats['documents'] = self._load_documents(data.get('witnesses', []))
        stats['topics'] = self._load_witness_topics(data.get('witnesses', []))
        stats['relationships'] = self._create_witness_relationships(data.get('witnesses', []))
        
        # Update session with final stats
        self._update_scraping_session(session_id, stats)
        
        print(f"Data loading complete. Session ID: {session_id}")
        return stats
    
    def _create_scraping_session(self, data: Dict, notes: str = None) -> str:
        """Create a new scraping session record"""
        metadata = data.get('metadata', {})
        
        session_data = {
            'session_date': datetime.now().isoformat(),
            'total_witnesses_scraped': len(data.get('witnesses', [])),
            'total_hearings_scraped': len(data.get('hearings', [])),
            'status': 'in_progress',
            'notes': notes or f"Automated load from JSON: {metadata.get('scrape_date', 'unknown date')}"
        }
        
        # Extract date range from witnesses
        witnesses = data.get('witnesses', [])
        if witnesses:
            dates = []
            for witness in witnesses:
                # Try to extract date from witness data structure
                if 'hearing' in witness and 'date' in witness['hearing']:
                    try:
                        date = datetime.fromisoformat(witness['hearing']['date'].replace('Z', '+00:00'))
                        dates.append(date.date())
                    except:
                        pass
            
            if dates:
                session_data['date_range_start'] = min(dates).isoformat()
                session_data['date_range_end'] = max(dates).isoformat()
        
        result = self.supabase.table('scraping_sessions').insert(session_data).execute()
        return result.data[0]['id']
    
    def _update_scraping_session(self, session_id: str, stats: Dict[str, int]):
        """Update scraping session with final statistics"""
        update_data = {
            'status': 'completed',
            'total_witnesses_scraped': stats['witnesses'],
            'total_hearings_scraped': stats['hearings']
        }
        
        self.supabase.table('scraping_sessions').update(update_data).eq('id', session_id).execute()
    
    def _load_committees(self, committees_data: List[Dict]) -> int:
        """Load committees into database"""
        if not committees_data:
            return 0
        
        print("Loading committees...")
        loaded_count = 0
        
        for committee_data in committees_data:
            committee_code = committee_data.get('code', '')
            if not committee_code:
                continue
            
            # Check if committee already exists
            existing = self.supabase.table('committees').select('id').eq('committee_code', committee_code).execute()
            
            if existing.data:
                self.committee_cache[committee_code] = existing.data[0]['id']
                continue
            
            # Insert new committee
            insert_data = {
                'committee_code': committee_code,
                'name': committee_data.get('name', ''),
                'parent_committee_id': None  # Handle parent relationships later if needed
            }
            
            result = self.supabase.table('committees').insert(insert_data).execute()
            self.committee_cache[committee_code] = result.data[0]['id']
            loaded_count += 1
        
        print(f"Loaded {loaded_count} committees")
        return loaded_count
    
    def _load_organizations(self, witnesses_data: List[Dict]) -> int:
        """Extract and load organizations from witness data"""
        print("Loading organizations...")
        
        organizations = set()
        for witness in witnesses_data:
            org_name = witness.get('organization')
            if org_name and org_name != 'None':
                organizations.add(org_name)
        
        loaded_count = 0
        for org_name in organizations:
            # Check if organization already exists
            existing = self.supabase.table('organizations').select('id').eq('name', org_name).execute()
            
            if existing.data:
                self.organization_cache[org_name] = existing.data[0]['id']
                continue
            
            # Insert new organization
            insert_data = {
                'name': org_name,
                'organization_type': 'unknown'  # Could be enhanced with classification
            }
            
            result = self.supabase.table('organizations').insert(insert_data).execute()
            self.organization_cache[org_name] = result.data[0]['id']
            loaded_count += 1
        
        print(f"Loaded {loaded_count} organizations")
        return loaded_count
    
    def _load_hearings(self, hearings_data: List[Dict]) -> int:
        """Load hearings into database"""
        if not hearings_data:
            return 0
        
        print("Loading hearings...")
        loaded_count = 0
        
        for hearing_data in hearings_data:
            event_id = hearing_data.get('id', '')
            if not event_id:
                continue
            
            # Check if hearing already exists
            existing = self.supabase.table('hearings').select('id').eq('event_id', event_id).execute()
            
            if existing.data:
                self.hearing_cache[event_id] = existing.data[0]['id']
                continue
            
            # Get committee ID
            committee_name = hearing_data.get('committee', '')
            committee_id = None
            for code, cached_id in self.committee_cache.items():
                # Find committee by name (this could be improved with better matching)
                committee_result = self.supabase.table('committees').select('id').eq('id', cached_id).execute()
                if committee_result.data and committee_result.data[0]['id'] == cached_id:
                    committee_id = cached_id
                    break
            
            if not committee_id and self.committee_cache:
                # Fallback to first committee if we can't match
                committee_id = list(self.committee_cache.values())[0]
            
            if not committee_id:
                print(f"Warning: No committee found for hearing {event_id}")
                continue
            
            # Parse date
            hearing_date = hearing_data.get('date', '')
            try:
                parsed_date = datetime.fromisoformat(hearing_date.replace('Z', '+00:00')).date()
            except:
                parsed_date = datetime.now().date()
            
            insert_data = {
                'event_id': event_id,
                'title': hearing_data.get('title', ''),
                'committee_id': committee_id,
                'hearing_date': parsed_date.isoformat(),
                'location': hearing_data.get('location', ''),
                'status': 'completed'
            }
            
            result = self.supabase.table('hearings').insert(insert_data).execute()
            self.hearing_cache[event_id] = result.data[0]['id']
            loaded_count += 1
        
        print(f"Loaded {loaded_count} hearings")
        return loaded_count
    
    def _load_witnesses(self, witnesses_data: List[Dict]) -> int:
        """Load witnesses into database"""
        if not witnesses_data:
            return 0
        
        print("Loading witnesses...")
        loaded_count = 0
        
        for witness_data in witnesses_data:
            witness_id = witness_data.get('id', '')
            if not witness_id:
                continue
            
            # Check if witness already exists
            existing = self.supabase.table('witnesses').select('id').eq('witness_id', witness_id).execute()
            
            if existing.data:
                self.witness_cache[witness_id] = existing.data[0]['id']
                continue
            
            # Get organization ID
            organization_id = None
            org_name = witness_data.get('organization')
            if org_name and org_name in self.organization_cache:
                organization_id = self.organization_cache[org_name]
            
            insert_data = {
                'witness_id': witness_id,
                'name': witness_data.get('name', ''),
                'title': witness_data.get('title', ''),
                'witness_type': witness_data.get('type', 'non_governmental'),
                'organization_id': organization_id,
                'panel_number': witness_data.get('panel'),
                'scraped_date': datetime.now().isoformat()
            }
            
            result = self.supabase.table('witnesses').insert(insert_data).execute()
            db_witness_id = result.data[0]['id']
            self.witness_cache[witness_id] = db_witness_id
            
            # Link witness to hearing
            hearing_id_from_data = witness_data.get('hearing_id')
            if hearing_id_from_data and hearing_id_from_data in self.hearing_cache:
                hearing_link_data = {
                    'witness_id': db_witness_id,
                    'hearing_id': self.hearing_cache[hearing_id_from_data],
                    'panel_number': witness_data.get('panel')
                }
                
                # Check if relationship already exists
                existing_link = self.supabase.table('witness_hearings').select('id').eq('witness_id', db_witness_id).eq('hearing_id', self.hearing_cache[hearing_id_from_data]).execute()
                
                if not existing_link.data:
                    self.supabase.table('witness_hearings').insert(hearing_link_data).execute()
            
            # Add expertise areas
            if witness_data.get('topics'):
                for topic in witness_data['topics']:
                    expertise_data = {
                        'witness_id': db_witness_id,
                        'area': topic.replace('_', ' ').title()
                    }
                    self.supabase.table('expertise_areas').insert(expertise_data).execute()
            
            # Add keywords
            if witness_data.get('keywords'):
                for keyword in witness_data['keywords']:
                    keyword_data = {
                        'witness_id': db_witness_id,
                        'keyword': keyword,
                        'source': 'scraped'
                    }
                    self.supabase.table('keywords').insert(keyword_data).execute()
            
            loaded_count += 1
        
        print(f"Loaded {loaded_count} witnesses")
        return loaded_count
    
    def _load_documents(self, witnesses_data: List[Dict]) -> int:
        """Load documents from witness data"""
        print("Loading documents...")
        loaded_count = 0
        
        for witness_data in witnesses_data:
            witness_id = witness_data.get('id', '')
            if not witness_id or witness_id not in self.witness_cache:
                continue
            
            db_witness_id = self.witness_cache[witness_id]
            document_count = witness_data.get('documents', 0)
            
            # Create placeholder documents based on count
            # In real implementation, you'd have actual document data
            for i in range(document_count):
                document_data = {
                    'witness_id': db_witness_id,
                    'document_type': 'witness_statement',
                    'url': f"https://docs.house.gov/placeholder/{witness_id}/doc_{i}",
                    'title': f"Document {i+1} for {witness_data.get('name', 'Unknown')}",
                    'file_format': 'PDF'
                }
                
                self.supabase.table('documents').insert(document_data).execute()
                loaded_count += 1
        
        print(f"Loaded {loaded_count} documents")
        return loaded_count
    
    def _load_witness_topics(self, witnesses_data: List[Dict]) -> int:
        """Load witness-topic relationships"""
        print("Loading witness-topic relationships...")
        loaded_count = 0
        
        # First, ensure all topics exist
        all_topics = set()
        for witness_data in witnesses_data:
            topics = witness_data.get('topics', [])
            all_topics.update(topics)
        
        for topic_name in all_topics:
            existing = self.supabase.table('topics').select('id').eq('name', topic_name).execute()
            if not existing.data:
                topic_data = {
                    'name': topic_name,
                    'display_name': topic_name.replace('_', ' ').title()
                }
                result = self.supabase.table('topics').insert(topic_data).execute()
                self.topic_cache[topic_name] = result.data[0]['id']
            else:
                self.topic_cache[topic_name] = existing.data[0]['id']
        
        # Link witnesses to topics
        for witness_data in witnesses_data:
            witness_id = witness_data.get('id', '')
            if not witness_id or witness_id not in self.witness_cache:
                continue
            
            db_witness_id = self.witness_cache[witness_id]
            topics = witness_data.get('topics', [])
            
            for topic_name in topics:
                if topic_name in self.topic_cache:
                    # Check if relationship already exists
                    existing = self.supabase.table('witness_topics').select('id').eq('witness_id', db_witness_id).eq('topic_id', self.topic_cache[topic_name]).execute()
                    
                    if not existing.data:
                        link_data = {
                            'witness_id': db_witness_id,
                            'topic_id': self.topic_cache[topic_name]
                        }
                        self.supabase.table('witness_topics').insert(link_data).execute()
                        loaded_count += 1
        
        print(f"Loaded {loaded_count} witness-topic relationships")
        return loaded_count
    
    def _create_witness_relationships(self, witnesses_data: List[Dict]) -> int:
        """Create witness-to-witness relationships based on shared hearings"""
        print("Creating witness relationships...")
        loaded_count = 0
        
        # Group witnesses by hearing
        hearing_witnesses = {}
        for witness_data in witnesses_data:
            hearing_id = witness_data.get('hearing_id')
            witness_id = witness_data.get('id')
            
            if hearing_id and witness_id and witness_id in self.witness_cache:
                if hearing_id not in hearing_witnesses:
                    hearing_witnesses[hearing_id] = []
                hearing_witnesses[hearing_id].append(self.witness_cache[witness_id])
        
        # Create relationships between witnesses who testified together
        for hearing_id, witness_ids in hearing_witnesses.items():
            for i, witness1_id in enumerate(witness_ids):
                for witness2_id in witness_ids[i+1:]:
                    # Check if relationship already exists
                    existing = self.supabase.table('witness_relationships').select('id').eq('source_witness_id', witness1_id).eq('target_witness_id', witness2_id).execute()
                    
                    if not existing.data:
                        relationship_data = {
                            'source_witness_id': witness1_id,
                            'target_witness_id': witness2_id,
                            'relationship_type': 'testified_together',
                            'strength': 1.0,
                            'context': f'Both testified in hearing {hearing_id}'
                        }
                        self.supabase.table('witness_relationships').insert(relationship_data).execute()
                        loaded_count += 1
        
        print(f"Created {loaded_count} witness relationships")
        return loaded_count
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics"""
        stats = {}
        
        tables = ['committees', 'organizations', 'hearings', 'witnesses', 
                 'documents', 'topics', 'witness_relationships']
        
        for table in tables:
            try:
                result = self.supabase.table(table).select('id', count='exact').execute()
                stats[table] = result.count
            except Exception as e:
                print(f"Error getting count for {table}: {e}")
                stats[table] = 0
        
        return stats

def main():
    """Main function to load data from JSON to Supabase"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load witness data from JSON into Supabase')
    parser.add_argument('json_file', help='JSON file containing scraped witness data')
    parser.add_argument('--supabase-url', required=True, help='Supabase project URL')
    parser.add_argument('--supabase-key', required=True, help='Supabase service role key')
    parser.add_argument('--notes', help='Optional notes for the scraping session')
    
    args = parser.parse_args()
    
    # Create loader and load data
    loader = SupabaseWitnessLoader(args.supabase_url, args.supabase_key)
    
    print("Loading witness data into Supabase...")
    stats = loader.load_from_json(args.json_file, args.notes)
    
    print("\nLoading Statistics:")
    for key, value in stats.items():
        print(f"  {key.title()}: {value}")
    
    print("\nDatabase Statistics:")
    db_stats = loader.get_database_stats()
    for table, count in db_stats.items():
        print(f"  {table}: {count} records")
    
    print("\nData loading complete!")

if __name__ == "__main__":
    main()