# Congress.gov API Hearings & Witness Data Analysis

## Summary

**Key Finding**: The Congress.gov JSON API does **not include witness information directly**, but witness lists are available in the HTML format documents linked from the API response.

## API Structure Analysis

### JSON API Response
- **Endpoint**: `https://api.congress.gov/v3/hearing/{congress}/{chamber}/{hearing_id}`
- **Contains**: Metadata, dates, committees, format links
- **Missing**: Direct witness information

### Available Data Sources

#### 1. JSON API (Limited for Witnesses)
```json
{
  "hearing": {
    "title": "ECONOMIC OPPORTUNITIES FROM LOCAL AGRICULTURAL MARKETS",
    "congress": 116,
    "chamber": "House", 
    "dates": [{"date": "2020-02-11"}],
    "committees": [...],
    "formats": [
      {"type": "Formatted Text", "url": "...htm"},
      {"type": "PDF", "url": "...pdf"}
    ]
  }
}
```

#### 2. HTML Format (Contains Witnesses)
- **URL**: Available via `formats[].url` where type is "Formatted Text"
- **Structure**: Congressional hearing transcript with witness section
- **Content**: Names, titles, organizations, locations, prepared statement pages

#### 3. PDF Format (Contains Witnesses)
- **URL**: Available via `formats[].url` where type is "PDF" 
- **Content**: Same as HTML but requires PDF parsing
- **Size**: ~261KB for sample hearing

## Witness Extraction Results

### Sample Hearing: 116th Congress, House, ID 41365
**Title**: "Economic Opportunities From Local Agricultural Markets"  
**Date**: February 11, 2020  
**Committee**: House Agriculture Committee, Subcommittee on Biotechnology, Horticulture, and Research

### Extracted Witnesses:
1. **Sommer Sibilly-Brown**
   - Title: Founder and Executive Director
   - Organization: Virgin Islands Good Food Coalition
   - Location: Kingshill, St. Croix, VI

2. **Kathy Zeman**
   - Title: Executive Director  
   - Organization: Minnesota Farmers Market Association
   - Location: Minneapolis, MN

3. **Clay Oliver**
   - Title: Owner
   - Organization: Oliver Oil Company LLC
   - Location: Pitts, GA

4. **Bret Erickson**
   - Title: Senior Vice President for Business Affairs
   - Organization: J&D Edinburg Produce Inc.
   - Location: TX

## Technical Implementation

### Successful Approach
1. **API Call**: Get hearing metadata from JSON API
2. **HTML Parsing**: Extract witness list from "Formatted Text" URL
3. **Text Processing**: Parse witness section using pattern recognition

### Code Structure
```python
class CongressHearingsAPI:
    def get_hearing(self, congress, chamber, hearing_id):
        # Get JSON metadata
        # Extract HTML format URL
        # Parse witnesses from HTML
        # Return structured data
```

### Parsing Challenges
- **Format Variations**: Different hearing HTML structures
- **Text Artifacts**: Page numbers, formatting dots mixed with content
- **Name Parsing**: "Last, First, Title, Organization, Location" pattern
- **Section Boundaries**: Identifying start/end of witness sections

## Data Quality Assessment

### Strengths
✅ **Comprehensive**: Full witness names, titles, organizations  
✅ **Structured**: Consistent format across hearings  
✅ **Accessible**: Public API with multiple keys available  
✅ **Current**: Real-time data from active hearings  

### Limitations
⚠️ **Indirect Access**: Requires HTML parsing, not direct JSON  
⚠️ **Parsing Complexity**: Text extraction needs refinement  
⚠️ **Format Dependency**: Relies on consistent HTML structure  
⚠️ **Rate Limits**: API calls limited (though multiple keys available)  

## Recommended Implementation Strategy

### For Witness Visualizer Integration

1. **Primary Data Source**: Congress.gov API for hearing metadata
2. **Witness Extraction**: HTML parsing from format links
3. **Fallback**: PDF parsing if HTML fails
4. **Caching**: Store extracted witness data to minimize API calls
5. **Data Validation**: Cross-reference with existing house_witness_scraper.py

### Integration Points
- **Complement Existing**: Enhance current House.gov scraper
- **Data Enrichment**: Add Congress.gov metadata to scraped witnesses
- **Verification**: Cross-validate witness information
- **Expansion**: Access Senate hearings (not available via House.gov scraper)

## Sample API Usage

```python
from congress_hearings_api import CongressHearingsAPI

api = CongressHearingsAPI()
hearing = api.get_hearing("116", "house", "41365")

print(f"Title: {hearing.title}")
print(f"Witnesses: {len(hearing.witnesses)}")
for witness in hearing.witnesses:
    print(f"- {witness.name} ({witness.organization})")
```

## Next Steps for Implementation

1. **Refine HTML Parser**: Improve witness extraction accuracy
2. **Add Error Handling**: Graceful failure for malformed HTML
3. **Implement Caching**: Reduce API calls for processed hearings
4. **Add Batch Processing**: Handle multiple hearings efficiently
5. **Integration Testing**: Combine with existing witness scraper
6. **Documentation**: API usage examples and best practices

## Conclusion

The Congress.gov API provides a valuable **complementary data source** for the Witness Visualizer project. While witness information requires HTML parsing rather than direct JSON access, the comprehensive metadata and structured format make it a reliable source for enhancing the existing House.gov scraper capabilities.

**Recommendation**: Implement as secondary data source to enrich witness information and provide access to Senate hearings.