import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time
import logging
from urllib.parse import urljoin, urlparse
try:
    # Try relative import first (for package usage)
    from ..models.witness_data_schema import (
        Witness, Hearing, Committee, Organization, Document, WitnessDatabase,
        WitnessType, DocumentType, KnowledgeGraph, Relationship
    )
except ImportError:
    # Fallback to direct import (for Modal or standalone usage)
    from models.witness_data_schema import (
        Witness, Hearing, Committee, Organization, Document, WitnessDatabase,
        WitnessType, DocumentType, KnowledgeGraph, Relationship
    )

class HouseWitnessScraper:
    """Scraper for House.gov witness testimony and hearing data"""
    
    def __init__(self, base_url: str = "https://docs.house.gov"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.witnesses: List[Witness] = []
        self.committees: Dict[str, Committee] = {}
        self.hearings: Dict[str, Hearing] = {}
        self.organizations: Dict[str, Organization] = {}
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        
    def search_witness_events(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
        """Search for committee events that likely contain witness testimony"""
        self.logger.info("Searching for witness events...")
        
        # Use Google search to find committee events with witnesses
        search_queries = [
            f"site:{self.base_url} witness testimony",
            f"site:{self.base_url} committee hearing witness",
            f"site:{self.base_url} public witness",
            f"site:{self.base_url} truth in testimony"
        ]
        
        event_urls = set()
        
        for query in search_queries:
            try:
                # This would typically use a search API, but for now we'll use known patterns
                self.logger.info(f"Searching with query: {query}")
                time.sleep(self.request_delay)
                
            except Exception as e:
                self.logger.error(f"Error searching for events: {e}")
                
        # For now, let's manually add some known event URLs from our earlier research
        known_event_urls = [
            f"{self.base_url}/Committee/Calendar/ByEvent.aspx?EventID=117214",
            f"{self.base_url}/Committee/Calendar/ByEvent.aspx?EventID=101762",
            f"{self.base_url}/Committee/Calendar/ByEvent.aspx?EventID=112625"
        ]
        
        return list(set(known_event_urls))
    
    def extract_event_id_from_url(self, url: str) -> Optional[str]:
        """Extract EventID from committee event URL"""
        match = re.search(r'EventID=(\d+)', url)
        return match.group(1) if match else None
    
    def scrape_committee_event(self, event_url: str) -> Optional[Hearing]:
        """Scrape a single committee event page for witness information"""
        try:
            self.logger.info(f"Scraping event: {event_url}")
            response = self.session.get(event_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic hearing information
            event_id = self.extract_event_id_from_url(event_url)
            if not event_id:
                self.logger.warning(f"Could not extract event ID from {event_url}")
                return None
            
            # Extract hearing title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else f"Hearing {event_id}"
            
            # Extract committee information
            committee_name = self._extract_committee_name(soup)
            committee_code = self._extract_committee_code(soup)
            
            # Extract hearing date and time
            hearing_date, hearing_time = self._extract_date_time(soup)
            
            # Extract location
            location = self._extract_location(soup)
            
            # Create committee object
            committee = Committee(
                name=committee_name,
                committee_code=committee_code or f"UNK_{event_id}"
            )
            self.committees[committee.committee_code] = committee
            
            # Create hearing object
            hearing = Hearing(
                event_id=event_id,
                title=title,
                committee=committee,
                date=hearing_date,
                time=hearing_time,
                location=location
            )
            self.hearings[event_id] = hearing
            
            # Extract witness information
            witnesses = self._extract_witnesses(soup, hearing)
            self.witnesses.extend(witnesses)
            
            time.sleep(self.request_delay)
            return hearing
            
        except Exception as e:
            self.logger.error(f"Error scraping event {event_url}: {e}")
            return None
    
    def _extract_committee_name(self, soup: BeautifulSoup) -> str:
        """Extract committee name from the page"""
        # Look for committee name in various locations
        selectors = [
            '.committee-name',
            '.CommitteeInfo',
            'h1',
            'h2'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if 'committee' in text.lower() or 'subcommittee' in text.lower():
                    return text
        
        return "Unknown Committee"
    
    def _extract_committee_code(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract committee code from the page or URL patterns"""
        # Look for committee codes in various formats
        text = soup.get_text()
        
        # Common patterns: JU05, IF14, etc.
        code_match = re.search(r'\b([A-Z]{2}\d{2})\b', text)
        if code_match:
            return code_match.group(1)
        
        return None
    
    def _extract_date_time(self, soup: BeautifulSoup) -> Tuple[datetime, Optional[str]]:
        """Extract hearing date and time from the page"""
        # Look for date patterns
        date_patterns = [
            r'(\w+ \d{1,2}, \d{4})',  # February 25, 2025
            r'(\d{1,2}/\d{1,2}/\d{4})',  # 2/25/2025
            r'(\d{4}-\d{2}-\d{2})'  # 2025-02-25
        ]
        
        text = soup.get_text()
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse the date
                    for fmt in ['%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            hearing_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        hearing_date = datetime.now()  # fallback
                        
                    # Look for time
                    time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)', text, re.IGNORECASE)
                    hearing_time = time_match.group(1) if time_match else None
                    
                    return hearing_date, hearing_time
                except Exception as e:
                    self.logger.warning(f"Error parsing date: {e}")
        
        return datetime.now(), None  # fallback
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract hearing location from the page"""
        text = soup.get_text()
        
        # Look for room numbers and building codes
        location_patterns = [
            r'(\d{4}\s+[A-Z]{3,5})',  # 2008 RHOB
            r'Room\s+(\d+)',
            r'([A-Z]+\s+\d+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "Unknown Location"
    
    def _extract_witnesses(self, soup: BeautifulSoup, hearing: Hearing) -> List[Witness]:
        """Extract witness information from the hearing page"""
        witnesses = []
        
        # Look for witness panels or lists
        witness_sections = soup.find_all(['div', 'section', 'table'], 
                                       class_=re.compile(r'witness|panel|testimony', re.I))
        
        if not witness_sections:
            # Fallback: look for any links to witness documents
            witness_sections = [soup]
        
        panel_number = 1
        
        for section in witness_sections:
            # Find witness names and associated documents
            witness_links = section.find_all('a', href=re.compile(r'\.pdf$', re.I))
            
            current_witness = None
            
            for link in witness_links:
                href = link.get('href')
                if not href:
                    continue
                
                # Make URL absolute
                doc_url = urljoin(self.base_url, href)
                
                # Extract document type from filename/text
                doc_type = self._classify_document(link.get_text(), href)
                
                # Extract witness name from filename or surrounding text
                witness_name = self._extract_witness_name_from_link(link, href)
                
                if witness_name:
                    # Check if this is a new witness or additional document for current witness
                    if not current_witness or current_witness.name != witness_name:
                        # Create new witness
                        current_witness = Witness(
                            name=witness_name,
                            title=self._extract_witness_title(link, section),
                            witness_type=self._classify_witness_type(witness_name, link.get_text()),
                            hearing=hearing,
                            documents=[],
                            expertise_areas=[],
                            previous_testimonies=[],
                            topics=self._extract_topics_from_hearing(hearing),
                            keywords=[],
                            related_witnesses=[],
                            source_url=hearing.event_id,
                            scraped_date=datetime.now(),
                            witness_id=f"{hearing.event_id}_{len(witnesses)}",
                            panel_number=panel_number
                        )
                        witnesses.append(current_witness)
                    
                    # Add document to current witness
                    document = Document(
                        document_type=doc_type,
                        url=doc_url,
                        title=link.get_text(strip=True),
                        file_format="PDF"
                    )
                    current_witness.documents.append(document)
            
            panel_number += 1
        
        self.logger.info(f"Extracted {len(witnesses)} witnesses from hearing {hearing.event_id}")
        return witnesses
    
    def _classify_document(self, link_text: str, href: str) -> DocumentType:
        """Classify document type based on filename and text"""
        text_lower = link_text.lower()
        href_lower = href.lower()
        
        if 'ttf' in href_lower or 'truth' in text_lower:
            return DocumentType.TRUTH_IN_TESTIMONY
        elif 'bio' in text_lower or 'biography' in text_lower:
            return DocumentType.BIOGRAPHY
        elif 'cv' in text_lower or 'curriculum' in text_lower:
            return DocumentType.CURRICULUM_VITAE
        elif 'transcript' in text_lower:
            return DocumentType.TRANSCRIPT
        else:
            return DocumentType.WITNESS_STATEMENT
    
    def _extract_witness_name_from_link(self, link, href: str) -> Optional[str]:
        """Extract witness name from document link or filename"""
        # Try to extract from filename
        filename = href.split('/')[-1]
        
        # Common patterns in House document filenames
        name_patterns = [
            r'-([A-Z][a-z]+[A-Z])-',  # -SurnameF-
            r'Wstate-([A-Za-z]+)-',   # Wstate-Surname-
            r'TTF-([A-Za-z]+)-'       # TTF-Surname-
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, filename)
            if match:
                return self._format_witness_name(match.group(1))
        
        # Fallback: try to extract from link text
        link_text = link.get_text(strip=True)
        if len(link_text) > 3 and len(link_text) < 50:
            return link_text
        
        return None
    
    def _format_witness_name(self, raw_name: str) -> str:
        """Format witness name from filename format to readable format"""
        # Convert from formats like "SurnameF" to "F. Surname"
        if len(raw_name) > 2 and raw_name[-1].isupper():
            surname = raw_name[:-1]
            first_initial = raw_name[-1]
            return f"{first_initial}. {surname}"
        
        return raw_name
    
    def _extract_witness_title(self, link, section) -> str:
        """Extract witness title/position from surrounding context"""
        # Look for title in surrounding text
        parent = link.parent
        if parent:
            text = parent.get_text(strip=True)
            # Look for common title patterns
            title_patterns = [
                r'(Chief|Director|President|CEO|Professor|Dr\.)\s+[^,\n]+',
                r'([^,\n]+ of [^,\n]+)',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
        
        return "Witness"
    
    def _classify_witness_type(self, name: str, context: str) -> WitnessType:
        """Classify witness type based on context"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['tribal', 'tribe', 'nation', 'chief']):
            return WitnessType.TRIBAL
        elif any(word in context_lower for word in ['university', 'professor', 'research']):
            return WitnessType.ACADEMIC
        elif any(word in context_lower for word in ['government', 'agency', 'federal']):
            return WitnessType.GOVERNMENTAL
        elif any(word in context_lower for word in ['corporation', 'company', 'inc', 'llc']):
            return WitnessType.PRIVATE_SECTOR
        elif any(word in context_lower for word in ['foundation', 'nonprofit', 'organization']):
            return WitnessType.NONPROFIT
        else:
            return WitnessType.NON_GOVERNMENTAL
    
    def _extract_topics_from_hearing(self, hearing: Hearing) -> List[str]:
        """Extract topic areas from hearing title and committee"""
        topics = []
        
        # Extract from hearing title
        title_lower = hearing.title.lower()
        
        topic_keywords = {
            'environment': ['environment', 'climate', 'pollution', 'conservation'],
            'healthcare': ['health', 'medical', 'medicare', 'medicaid'],
            'education': ['education', 'school', 'university', 'learning'],
            'technology': ['technology', 'cyber', 'digital', 'internet', 'ai'],
            'defense': ['defense', 'military', 'security', 'armed forces'],
            'energy': ['energy', 'oil', 'gas', 'renewable', 'power'],
            'finance': ['finance', 'banking', 'money', 'budget', 'tax'],
            'immigration': ['immigration', 'border', 'visa', 'refugee'],
            'judiciary': ['justice', 'court', 'legal', 'law', 'judicial'],
            'agriculture': ['agriculture', 'farming', 'food', 'rural'],
            'transportation': ['transportation', 'highway', 'aviation', 'rail'],
            'tribal_affairs': ['tribal', 'indian', 'native', 'indigenous']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['general']
    
    def scrape_all_witnesses(self, max_events: int = 50) -> WitnessDatabase:
        """Scrape witness data from multiple committee events"""
        self.logger.info(f"Starting to scrape witness data (max {max_events} events)")
        
        # Get list of event URLs
        event_urls = self.search_witness_events()
        
        if not event_urls:
            self.logger.warning("No event URLs found")
            return self._create_database()
        
        # Scrape each event
        scraped_count = 0
        for url in event_urls[:max_events]:
            try:
                hearing = self.scrape_committee_event(url)
                if hearing:
                    scraped_count += 1
                    self.logger.info(f"Successfully scraped event {hearing.event_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to scrape event {url}: {e}")
                continue
        
        self.logger.info(f"Scraping complete. Processed {scraped_count} events, found {len(self.witnesses)} witnesses")
        
        return self._create_database()
    
    def _create_database(self) -> WitnessDatabase:
        """Create WitnessDatabase object from scraped data"""
        if not self.witnesses:
            # Create empty database with current date
            return WitnessDatabase(
                witnesses=[],
                committees=list(self.committees.values()),
                hearings=list(self.hearings.values()),
                organizations=list(self.organizations.values()),
                scrape_date=datetime.now(),
                total_witnesses=0,
                date_range=(datetime.now(), datetime.now())
            )
        
        # Calculate date range
        hearing_dates = [w.hearing.date for w in self.witnesses]
        min_date = min(hearing_dates)
        max_date = max(hearing_dates)
        
        return WitnessDatabase(
            witnesses=self.witnesses,
            committees=list(self.committees.values()),
            hearings=list(self.hearings.values()),
            organizations=list(self.organizations.values()),
            scrape_date=datetime.now(),
            total_witnesses=len(self.witnesses),
            date_range=(min_date, max_date)
        )
    
    def export_to_json(self, filename: str, database: WitnessDatabase):
        """Export scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(database.to_json(), f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data exported to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")

def main():
    """Main function to run the scraper"""
    scraper = HouseWitnessScraper()
    
    # Scrape witness data
    database = scraper.scrape_all_witnesses(max_events=10)
    
    # Export to JSON
    output_filename = f"house_witnesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.export_to_json(output_filename, database)
    
    print(f"Scraping complete!")
    print(f"Total witnesses found: {database.total_witnesses}")
    print(f"Total committees: {len(database.committees)}")
    print(f"Total hearings: {len(database.hearings)}")
    print(f"Data exported to: {output_filename}")

if __name__ == "__main__":
    main()