from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class WitnessType(Enum):
    GOVERNMENTAL = "governmental"
    NON_GOVERNMENTAL = "non_governmental"
    TRIBAL = "tribal"
    PRIVATE_SECTOR = "private_sector"
    ACADEMIC = "academic"
    NONPROFIT = "nonprofit"

class DocumentType(Enum):
    WITNESS_STATEMENT = "witness_statement"
    BIOGRAPHY = "biography"
    TRUTH_IN_TESTIMONY = "truth_in_testimony"
    TRANSCRIPT = "transcript"
    CURRICULUM_VITAE = "curriculum_vitae"

@dataclass
class Document:
    """Represents a document associated with a witness"""
    document_type: DocumentType
    url: str
    title: str
    file_format: str  # PDF, DOC, etc.
    added_date: Optional[datetime] = None
    size_bytes: Optional[int] = None

@dataclass
class Committee:
    """Represents a House committee or subcommittee"""
    name: str
    committee_code: str  # e.g., "JU05", "IF14"
    parent_committee: Optional[str] = None
    
@dataclass
class Hearing:
    """Represents a congressional hearing event"""
    event_id: str
    title: str
    committee: Committee
    date: datetime
    location: str
    time: Optional[str] = None
    room: Optional[str] = None
    hearing_type: Optional[str] = None
    status: str = "scheduled"  # scheduled, completed, cancelled
    
@dataclass
class Organization:
    """Represents an organization a witness is affiliated with"""
    name: str
    organization_type: str  # tribal_government, corporation, university, etc.
    location: Optional[str] = None
    website: Optional[str] = None

@dataclass
class Witness:
    """Main witness data structure for knowledge mapping"""
    # Core Identity
    name: str
    title: str
    witness_type: WitnessType
    hearing: Hearing
    documents: List[Document]
    expertise_areas: List[str]
    previous_testimonies: List[str]  # URLs to previous appearances
    topics: List[str]  # Issue areas the witness testified about
    keywords: List[str]  # Extracted from testimony
    related_witnesses: List[str]  # Names of witnesses on same panels/topics
    source_url: str
    scraped_date: datetime
    
    # Optional fields with defaults
    witness_id: Optional[str] = None  # Generated unique ID
    panel_number: Optional[int] = None
    organization: Optional[Organization] = None
    tribal_affiliation: Optional[str] = None
    added_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    background: Optional[str] = None

@dataclass
class WitnessDatabase:
    """Container for all scraped witness data"""
    witnesses: List[Witness]
    committees: List[Committee] 
    hearings: List[Hearing]
    organizations: List[Organization]
    
    # Metadata
    scrape_date: datetime
    total_witnesses: int
    date_range: tuple[datetime, datetime]  # (earliest, latest hearing)
    
    def to_json(self) -> Dict[str, Any]:
        """Export data for knowledge mapping visualization"""
        return {
            "metadata": {
                "scrape_date": self.scrape_date.isoformat(),
                "total_witnesses": self.total_witnesses,
                "date_range": [self.date_range[0].isoformat(), self.date_range[1].isoformat()]
            },
            "witnesses": [self._witness_to_dict(w) for w in self.witnesses],
            "committees": [self._committee_to_dict(c) for c in self.committees],
            "hearings": [self._hearing_to_dict(h) for h in self.hearings],
            "organizations": [self._org_to_dict(o) for o in self.organizations]
        }
    
    def _witness_to_dict(self, witness: Witness) -> Dict[str, Any]:
        return {
            "id": witness.witness_id,
            "name": witness.name,
            "title": witness.title,
            "type": witness.witness_type.value,
            "organization": witness.organization.name if witness.organization else None,
            "hearing_id": witness.hearing.event_id,
            "topics": witness.topics,
            "keywords": witness.keywords,
            "documents": len(witness.documents),
            "panel": witness.panel_number
        }
    
    def _committee_to_dict(self, committee: Committee) -> Dict[str, Any]:
        return {
            "name": committee.name,
            "code": committee.committee_code,
            "parent": committee.parent_committee
        }
    
    def _hearing_to_dict(self, hearing: Hearing) -> Dict[str, Any]:
        return {
            "id": hearing.event_id,
            "title": hearing.title,
            "committee": hearing.committee.name,
            "date": hearing.date.isoformat(),
            "location": hearing.location
        }
    
    def _org_to_dict(self, org: Organization) -> Dict[str, Any]:
        return {
            "name": org.name,
            "type": org.organization_type,
            "location": org.location
        }

# Knowledge Graph Relationship Schema
@dataclass
class Relationship:
    """Represents connections between entities for knowledge mapping"""
    source_id: str
    target_id: str
    relationship_type: str  # "testified_with", "works_for", "appeared_before", etc.
    strength: float  # 0.0 to 1.0, for visualization weighting
    context: Optional[str] = None  # Additional context about the relationship

@dataclass
class KnowledgeGraph:
    """Complete knowledge graph for visualization"""
    nodes: Dict[str, Dict[str, Any]]  # node_id -> node_data
    edges: List[Relationship]
    
    def add_witness_node(self, witness: Witness):
        """Add a witness as a node in the knowledge graph"""
        self.nodes[witness.witness_id] = {
            "id": witness.witness_id,
            "name": witness.name,
            "type": "witness",
            "organization": witness.organization.name if witness.organization else None,
            "topics": witness.topics,
            "hearings": [witness.hearing.event_id]
        }
    
    def add_organization_node(self, org: Organization):
        """Add an organization as a node in the knowledge graph"""
        self.nodes[org.name] = {
            "id": org.name,
            "name": org.name,
            "type": "organization",
            "org_type": org.organization_type
        }
    
    def add_topic_node(self, topic: str):
        """Add a topic/issue area as a node"""
        if topic not in self.nodes:
            self.nodes[topic] = {
                "id": topic,
                "name": topic,
                "type": "topic"
            }