# Congressional Witness Visualizer - Claude Code Guide

This file provides Claude Code with essential information about the Congressional Witness Visualizer project structure, commands, and usage patterns.

## Project Overview

**Purpose**: Scrape congressional witness testimony data from House.gov and create interactive knowledge graph visualizations to analyze relationships between witnesses, committees, topics, and organizations.

**Tech Stack**: Python, FastAPI, Supabase (PostgreSQL), Plotly, NetworkX, BeautifulSoup, Modal (cloud deployment)

## Project Structure

```
witnessVisualizer/
├── main.py                       # Main CLI entry point - USE THIS FOR COMMANDS
├── requirements.txt              # Python dependencies
├── scrapers/                     # Web scraping components
│   ├── house_witness_scraper.py  # Main House.gov scraper
│   ├── house_gov_scraper.py      # Additional scraper
│   └── congressional_api.py      # API client
├── models/                       # Data models and schemas
│   └── witness_data_schema.py    # Pydantic data models
├── database/                     # Database components
│   └── supabase_loader.py        # Data loading utilities
├── api/                         # REST API components
│   └── production/              # Production API endpoints
│       ├── witness_api.py       # Main FastAPI endpoints
│       └── simple_witness_api.py # Simplified API
├── visualization/               # Interactive visualizations
│   └── knowledge_graph_visualizer.py # Graph generator
├── modal_launch/               # Cloud deployment
├── v0-frontend/               # Next.js frontend application
│   ├── app/                   # Next.js app directory
│   │   ├── page.tsx          # Main dashboard page
│   │   └── witnesses/        # Witnesses page
│   └── components/           # React components
│       ├── organization-timeline.tsx
│       ├── stats-overview.tsx
│       └── ui/              # UI components
└── docs/                   # Documentation
```

## Common Commands

### Testing and Development
```bash
# Test the scraper (recommended first step)
python main.py test

# Run scraper to collect data (start with small number)
python main.py scrape --max-events 5

# Create visualizations from scraped data
python main.py visualize test_output.json
```

### API and Database
```bash
# Start API server for web access
python main.py api --port 8000

# Load data into Supabase (requires credentials)
python main.py load data.json --supabase-url "https://xxx.supabase.co" --supabase-key "xxx"
```

### Installation
```bash
# Install all dependencies
pip install -r requirements.txt

# For development with auto-reload
pip install -r requirements.txt && python main.py api --reload
```

## File Purposes and When to Use

### Primary Entry Points
- **`main.py`** - ALWAYS use this for CLI commands (scrape, test, visualize, api, load)
- **`scrapers/house_witness_scraper.py`** - Main scraper logic, use for understanding scraping
- **`api/witness_api.py`** - REST API endpoints for web integration

### Data Flow
1. **Scrape**: `main.py scrape` → Extracts data from House.gov → Saves JSON
2. **Store**: `main.py load` → Loads JSON into Supabase PostgreSQL database
3. **Access**: `main.py api` → Provides REST API for data access
4. **Visualize**: `main.py visualize` → Creates interactive knowledge graphs

### Key Files to Read for Understanding
- **`models/witness_data_schema.py`** - Understanding data structure
- **`database/supabase_schema.sql`** - Database table structure
- **`docs/README.md`** - Comprehensive project documentation
- **`docs/SUPABASE_SETUP.md`** - Database setup instructions

## Environment Variables Needed

```bash
# For Supabase database operations
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Optional: For enhanced scraping
USER_AGENT=your-custom-user-agent
```

## Common Development Tasks

### Adding New Scrapers
- Place in `scrapers/` folder
- Follow pattern of `house_witness_scraper.py`
- Use data models from `models/witness_data_schema.py`
- Add test in `scrapers/test_scraper.py`

### Extending API
- Add endpoints to `api/witness_api.py`
- Use Pydantic models for request/response validation
- Test with FastAPI auto-docs at `/docs`

### New Visualizations
- Add to `visualization/` folder
- Use existing data loading from `knowledge_graph_visualizer.py`
- Integrate with `main.py` CLI

### Database Changes
- Update `database/supabase_schema.sql`
- Modify `database/supabase_loader.py` for data loading
- Update `models/witness_data_schema.py` for new fields

## Debugging and Troubleshooting

### Common Issues
1. **Import Errors**: Use relative imports (`from ..models import`) within packages
2. **Database Connection**: Check SUPABASE_URL and SUPABASE_KEY environment variables
3. **Scraping Failures**: Test with `python main.py test` first
4. **API Errors**: Check FastAPI logs when running `python main.py api`

### Useful Debug Commands
```bash
# Test specific scraper functionality
python -m scrapers.test_scraper

# Check API health
curl http://localhost:8000/

# Validate JSON data structure
python -c "import json; print(json.load(open('test_output.json'))['metadata'])"
```

### Log Locations
- Scraper logs: Console output with timestamps
- API logs: Console output when running `main.py api`
- Database operations: Logged in supabase_loader.py

## Data Schema Overview

### Core Entities
- **Witness**: Individual who testifies (name, title, organization, type)
- **Hearing**: Congressional hearing event (date, committee, location)
- **Committee**: House committee/subcommittee (name, code)
- **Organization**: Affiliated institution (name, type)
- **Document**: Testimony documents (URL, type, title)

### Relationships
- Witnesses ↔ Hearings (many-to-many)
- Witnesses ↔ Topics (many-to-many)
- Witnesses ↔ Organizations (many-to-one)
- Hearings ↔ Committees (many-to-one)

## Performance Notes

### Scraping
- Rate limited to 1 second between requests
- Typical: 10-50 witnesses per hearing
- Memory usage scales linearly with witness count

### Database
- Optimized with indexes for common queries
- Full-text search enabled on names and titles
- Handles 10,000+ witnesses efficiently

### Visualizations
- Interactive graphs handle 1000+ nodes
- Large datasets may require filtering for performance

## Security Considerations

- **Row Level Security (RLS)** enabled on Supabase tables
- **Service role key** required for data loading
- **Anonymous key** for read-only API access
- **Rate limiting** on scraping to respect source servers

## Integration Points

### For Web Applications
- Use REST API endpoints at `/api/*`
- JSON data format for easy integration
- CORS enabled for cross-origin requests

### For Data Analysis
- Export JSON data for external analysis
- PostgreSQL database for SQL queries
- CSV export capabilities in visualizer

### For Cloud Deployment
- Modal deployment in `modal_launch/` folder
- Environment variable configuration
- Scalable processing for large datasets

## Quick Start Checklist

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Test scraper: `python main.py test`
3. ✅ Scrape sample data: `python main.py scrape --max-events 3`
4. ✅ Create visualization: `python main.py visualize test_output.json`
5. ✅ Start API server: `python main.py api`
6. ✅ View API docs: http://localhost:8000/docs

This covers the essential information for understanding and working with the Congressional Witness Visualizer project effectively.