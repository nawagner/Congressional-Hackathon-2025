# Congressional Witness Knowledge Graph Visualizer

This project scrapes witness testimony data from the U.S. House of Representatives documentation website (docs.house.gov) and creates interactive knowledge graph visualizations to explore relationships between witnesses, committees, topics, and organizations.

## Features

- **Web Scraping**: Automated extraction of witness information from House committee hearings
- **Data Schema**: Structured data model for witnesses, hearings, committees, and organizations
- **Knowledge Graph**: Network analysis of relationships between entities
- **Interactive Visualizations**: Web-based interactive graphs and analysis dashboards
- **Export Capabilities**: JSON export for further analysis or integration

## Components

### 1. Data Schema (`witness_data_schema.py`)
Defines the data structures for:
- **Witness**: Individual testimony providers with metadata
- **Hearing**: Congressional hearing events
- **Committee**: House committees and subcommittees
- **Organization**: Affiliated institutions
- **Document**: Associated testimony documents
- **KnowledgeGraph**: Network representation for visualization

### 2. Web Scraper (`house_witness_scraper.py`)
Features:
- Scrapes witness data from docs.house.gov
- Extracts witness names, titles, affiliations, and documents
- Classifies witness types (governmental, academic, tribal, etc.)
- Identifies topics and themes from hearing titles
- Rate-limited and respectful scraping
- JSON export functionality

### 3. Knowledge Graph Visualizer (`knowledge_graph_visualizer.py`)
Creates:
- **Interactive Network Graph**: Plotly-based visualization showing connections
- **Analysis Dashboard**: Statistical summaries and charts
- **Summary Reports**: Text-based analysis of the data

### 4. Testing (`test_scraper.py`)
Validates scraper functionality with known test cases

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd witnessVisualizer
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Scraping

1. **Test the scraper**:
   ```bash
   python test_scraper.py
   ```

2. **Run full scraping**:
   ```bash
   python house_witness_scraper.py
   ```
   This will create a JSON file with timestamp: `house_witnesses_YYYYMMDD_HHMMSS.json`

### Creating Visualizations

1. **Generate interactive knowledge graph**:
   ```bash
   python knowledge_graph_visualizer.py your_data_file.json
   ```

2. **Custom output files**:
   ```bash
   python knowledge_graph_visualizer.py data.json \
     --output-graph custom_graph.html \
     --output-dashboard custom_dashboard.html \
     --output-report custom_report.txt
   ```

### Output Files

- **Interactive Graph** (`witness_knowledge_graph.html`): Network visualization
- **Analysis Dashboard** (`witness_analysis_dashboard.html`): Statistical charts
- **Summary Report** (`witness_analysis_report.txt`): Text analysis

## Data Structure

### Witness Data Schema
```python
{
  "name": "Witness Name",
  "title": "Position/Title",
  "witness_type": "governmental|academic|tribal|private_sector|nonprofit",
  "organization": "Affiliated Organization",
  "hearing": {
    "event_id": "117214",
    "title": "Hearing Title",
    "committee": "Committee Name",
    "date": "2025-02-25",
    "location": "2008 RHOB"
  },
  "documents": [
    {
      "document_type": "witness_statement|biography|truth_in_testimony",
      "url": "https://docs.house.gov/...",
      "title": "Document Title"
    }
  ],
  "topics": ["environment", "tribal_affairs"],
  "keywords": ["extracted", "keywords"]
}
```

### Knowledge Graph Relationships
- **Witnesses ↔ Witnesses**: Testified together in same hearing
- **Witnesses ↔ Topics**: Testified about specific topics
- **Witnesses ↔ Organizations**: Employment/affiliation
- **Witnesses ↔ Committees**: Appeared before committee

## Visualization Features

### Interactive Network Graph
- **Node Types**: Different colors for witnesses, committees, topics, organizations
- **Node Sizes**: Based on document count or activity level
- **Hover Information**: Detailed metadata on mouse-over
- **Zoom/Pan**: Interactive exploration
- **Legend**: Clear identification of entity types

### Analysis Dashboard
- **Witness Type Distribution**: Pie chart of governmental vs. non-governmental
- **Top Organizations**: Bar chart of most frequent affiliations
- **Topic Frequency**: Most common hearing topics
- **Committee Activity**: Most active committees

### Network Analysis
- **Centrality Measures**: Identify most connected entities
- **Community Detection**: Find clusters of related witnesses
- **Path Analysis**: Shortest paths between entities
- **Density Metrics**: Network connectivity statistics

## Sample Use Cases

1. **Lobbying Analysis**: Track which organizations frequently testify
2. **Expert Networks**: Identify subject matter experts by topic
3. **Committee Focus**: Understand committee priorities through witness selection
4. **Temporal Analysis**: Track changing witness patterns over time
5. **Influence Mapping**: Identify key players in policy discussions

## Data Sources

- **Primary**: docs.house.gov Committee Repository
- **Document Types**: Witness statements, biographies, Truth in Testimony forms
- **Coverage**: All available committee hearings with witness testimony
- **Update Frequency**: Manual scraping (can be automated)

## Technical Details

### Scraping Approach
- Respectful scraping with rate limiting (1 second delays)
- BeautifulSoup for HTML parsing
- Pattern matching for witness name extraction
- Automatic classification based on context

### Graph Construction
- NetworkX for graph structure
- Plotly for interactive visualizations
- Pandas for data analysis
- Automatic relationship inference

### Performance
- Typical scraping: 10-50 witnesses per hearing
- Processing time: ~1-2 seconds per hearing page
- Memory usage: Scales linearly with witness count
- Visualization: Handles 1000+ nodes efficiently

## Limitations

- **Data Availability**: Limited to publicly available docs.house.gov content
- **Parsing Accuracy**: Some witness names/titles may be incorrectly extracted
- **Historical Coverage**: Depends on digital availability of older hearings
- **Update Frequency**: Manual scraping required for new data

## Future Enhancements

1. **Automated Scheduling**: Regular scraping automation
2. **Senate Integration**: Include Senate witness data
3. **Temporal Visualizations**: Time-series analysis
4. **Text Analysis**: NLP on witness statements
5. **API Integration**: Direct access to government APIs if available
6. **Machine Learning**: Automatic topic extraction and classification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational and research purposes. Please respect the terms of service of data sources and use responsibly.

## Support

For issues or questions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include sample data and error messages

---

**Note**: This tool is designed for research and transparency purposes. Please use responsibly and in accordance with all applicable terms of service and legal requirements.