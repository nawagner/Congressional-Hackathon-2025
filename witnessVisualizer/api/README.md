# Congressional Witness API

This folder contains the API components for the Congressional Witness Visualizer, organized by purpose and maturity level.

## 📁 Organization Structure

```
api/
├── production/           # Production-ready API servers
│   ├── simple_witness_api.py    # ✅ ACTIVE: Current production API
│   └── witness_api.py           # Legacy comprehensive API
├── development/          # Development & experimental APIs
│   ├── congressional_api.py     # Alternative API implementations
│   ├── congress_hearings_api.py # Congressional hearings focused API
│   ├── extract_witnesses_from_html.py  # HTML parsing utilities
│   ├── improved_witness_extractor.py   # Enhanced extraction logic
│   └── hearing_html_snippet.html       # Sample HTML data
├── debug/               # Debug & investigation tools
│   ├── debug_api.py              # Debug endpoints
│   ├── api_debug_response.json   # Debug response samples
│   └── investigate_witness_sources.py  # Source investigation
├── __init__.py          # Package initialization
└── README.md           # This file
```

## 🚀 Current Production API

**`production/simple_witness_api.py`** - The current active API

### Key Features:
- ✅ **635 unique witnesses** with proper deduplication
- ✅ **Real data** from `congressional_hearings` table
- ✅ **Comprehensive endpoints** for frontend integration
- ✅ **Optimized performance** with shared caching logic

### Available Endpoints:
- `GET /` - Health check
- `GET /witnesses/all-simple` - All witnesses (simple format)
- `GET /witnesses/congressional` - Congressional witnesses (alias)
- `GET /witnesses` - Paginated witnesses
- `GET /witnesses/all` - Comprehensive witness data with metadata
- `GET /metrics/witnesses-number` - Total witness count
- `GET /metrics/hearings-number` - Total hearing count  
- `GET /metrics/organizations-number` - Total organization count

### Running the Production API:
```bash
cd /path/to/witnessVisualizer
export WITNESS_SUPABASE_URL="your-url"
export WITNESS_SUPABASE_SERVICE_ROLE_KEY="your-key"
python3 -m uvicorn api.production.simple_witness_api:app --port 8000 --reload
```

## 🔧 Development APIs

**`development/`** folder contains:
- **Alternative implementations** for testing different approaches
- **Experimental features** not yet ready for production
- **HTML parsing utilities** for data extraction research
- **Enhanced extraction logic** for improving witness identification

## 🐛 Debug Tools

**`debug/`** folder contains:
- **Investigation scripts** for data source analysis
- **Debug endpoints** for troubleshooting
- **Sample responses** for testing and validation

## 📊 Data Flow

1. **Data Source**: Supabase `congressional_hearings` table with JSONB witness data
2. **Processing**: Witness deduplication by name + organization
3. **API Response**: Structured JSON with hearings, committees, and organization info
4. **Frontend Integration**: Used by Next.js components for visualization

## 🔄 Migration Notes

If switching between API implementations:
1. Update the uvicorn command path
2. Ensure environment variables are set correctly
3. Test endpoints with curl before switching frontend
4. Update frontend API calls if endpoint signatures change

## 📝 Development Guidelines

- **Production changes**: Only modify `production/` files after thorough testing
- **New features**: Develop in `development/` folder first
- **Debug tools**: Add investigation scripts to `debug/` folder
- **Documentation**: Update this README when adding new APIs

The current setup provides a clean separation between stable production code and experimental development work.