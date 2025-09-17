# Congressional Witness Visualizer - Project Structure

This document outlines the organized folder structure and components of the Congressional Witness Visualizer system.

## 📁 Project Structure

```
witnessVisualizer/
├── 📄 __init__.py                    # Package initialization
├── 📄 main.py                        # Main CLI entry point
├── 📄 requirements.txt               # Python dependencies
├── 📄 PROJECT_STRUCTURE.md          # This file
├── 📄 test_output.json              # Sample scraped data
│
├── 📁 scrapers/                     # Web Scraping Components
│   ├── 📄 __init__.py
│   ├── 📄 house_witness_scraper.py  # Main House.gov scraper
│   └── 📄 test_scraper.py           # Scraper test suite
│
├── 📁 models/                       # Data Models & Schema
│   ├── 📄 __init__.py
│   └── 📄 witness_data_schema.py    # Pydantic data models
│
├── 📁 database/                     # Database Components
│   ├── 📄 supabase_schema.sql       # Database schema DDL
│   └── 📄 supabase_loader.py        # Data loading utilities
│
├── 📁 api/                          # REST API Components
│   ├── 📄 __init__.py
│   ├── 📄 witness_api.py            # FastAPI REST endpoints
│   ├── 📄 congress_hearings_api.py  # Additional API utilities
│   ├── 📄 debug_api.py              # API debugging tools
│   ├── 📄 investigate_witness_sources.py # Source investigation
│   ├── 📄 api_debug_response.json   # Debug response data
│   └── 📄 hearing_html_snippet.html # HTML sample data
│
├── 📁 visualization/                # Visualization Components
│   ├── 📄 knowledge_graph_visualizer.py    # Interactive graph generator
│   ├── 📄 witness_knowledge_graph.html     # Generated graph visualization
│   ├── 📄 witness_analysis_dashboard.html  # Analysis dashboard
│   └── 📄 witness_analysis_report.txt      # Text analysis report
│
├── 📁 modal_launch/                 # Modal Cloud Deployment
│   ├── 📄 README.md                 # Modal deployment guide
│   ├── 📄 modal_witness_scraper.py  # Modal cloud scraper
│   ├── 📄 modal_requirements.txt    # Modal dependencies
│   └── 📄 setup_modal.py           # Modal setup script
│
└── 📁 docs/                         # Documentation
    ├── 📄 README.md                 # Main project documentation
    └── 📄 SUPABASE_SETUP.md         # Database setup guide
```

## 🔧 Component Overview

### 🕷️ Scrapers (`/scrapers`)

**Purpose**: Extract witness testimony data from House.gov
- **`house_witness_scraper.py`**: Main scraper for docs.house.gov
- **`test_scraper.py`**: Test suite for scraper validation

**Key Features**:
- Respectful scraping with rate limiting
- Automatic witness name/title extraction
- Document classification (statements, biographies, Truth in Testimony)
- Topic categorization based on hearing content

### 🗄️ Models (`/models`)

**Purpose**: Define data structures and schemas
- **`witness_data_schema.py`**: Pydantic models for all data types

**Data Models**:
- `Witness`: Individual testimony providers
- `Hearing`: Congressional hearing events
- `Committee`: House committees/subcommittees
- `Organization`: Affiliated institutions
- `Document`: Associated testimony documents
- `KnowledgeGraph`: Network representation

### 🗂️ Database (`/database`)

**Purpose**: Database schema and data loading
- **`supabase_schema.sql`**: Complete PostgreSQL schema (13 tables)
- **`supabase_loader.py`**: JSON to Supabase data loader

**Database Features**:
- Normalized relational structure
- Full-text search capabilities
- Row-level security (RLS)
- Automatic timestamp triggers
- Performance-optimized indexes

### 🌐 API (`/api`)

**Purpose**: REST API for data access
- **`witness_api.py`**: FastAPI application with full CRUD operations
- **Supporting files**: Debugging and investigation utilities

**API Endpoints**:
- `/witnesses` - Get witnesses with filtering/pagination
- `/hearings` - Get hearings with date/committee filters
- `/committees` - Get all committees
- `/organizations` - Get organizations
- `/topics` - Get available topics
- `/search` - Global search across entities
- Plus relationship and document endpoints

### 📊 Visualization (`/visualization`)

**Purpose**: Interactive knowledge graph visualizations
- **`knowledge_graph_visualizer.py`**: Generate interactive visualizations

**Visualization Types**:
- Interactive network graphs (Plotly)
- Statistical analysis dashboards
- Text-based summary reports
- Knowledge graph relationship mapping

### ☁️ Modal Launch (`/modal_launch`)

**Purpose**: Cloud deployment on Modal platform
- **`modal_witness_scraper.py`**: Cloud-optimized scraper
- **`setup_modal.py`**: Deployment automation

**Cloud Features**:
- Scalable infrastructure
- Parallel processing capabilities
- Secure environment variable management
- Built-in monitoring and logging

### 📚 Documentation (`/docs`)

**Purpose**: Project documentation and setup guides
- **`README.md`**: Main project documentation
- **`SUPABASE_SETUP.md`**: Detailed database setup guide

## 🚀 Usage Patterns

### Command Line Interface

The main entry point (`main.py`) provides a unified CLI:

```bash
# Scrape witness data
python main.py scrape --max-events 10

# Test scraper functionality
python main.py test

# Create visualizations
python main.py visualize data.json

# Load data into Supabase
python main.py load data.json --supabase-url "..." --supabase-key "..."

# Start API server
python main.py api --port 8000
```

### Programmatic Usage

```python
# Import components
from scrapers.house_witness_scraper import HouseWitnessScraper
from database.supabase_loader import SupabaseWitnessLoader
from visualization.knowledge_graph_visualizer import WitnessKnowledgeGraphVisualizer
from api.witness_api import app

# Use individual components
scraper = HouseWitnessScraper()
data = scraper.scrape_all_witnesses()
```

## 🔄 Data Flow

1. **Scraping**: `scrapers/` → Extract data from House.gov
2. **Storage**: `database/` → Store in Supabase PostgreSQL
3. **API Access**: `api/` → REST API for data retrieval
4. **Visualization**: `visualization/` → Interactive knowledge graphs
5. **Cloud Processing**: `modal_launch/` → Scalable cloud execution

## 🎯 Key Benefits of Organization

### 📦 **Modularity**
- Each component is self-contained
- Clear separation of concerns
- Easy to test and maintain individual parts

### 🔧 **Extensibility**
- Add new scrapers in `/scrapers`
- Extend API endpoints in `/api`
- Create new visualizations in `/visualization`

### 🚀 **Deployment Options**
- Local development with CLI
- API server deployment
- Cloud scaling with Modal

### 📖 **Documentation**
- Clear structure documentation
- Setup guides for each component
- Examples and usage patterns

### 🧪 **Testing**
- Dedicated test files
- Sample data for validation
- Debug utilities

## 🔧 Development Workflow

1. **Setup**: Install dependencies from `requirements.txt`
2. **Development**: Work within appropriate folders
3. **Testing**: Use test files and sample data
4. **Database**: Set up Supabase with provided schema
5. **API**: Run FastAPI server for data access
6. **Visualization**: Generate interactive graphs
7. **Deployment**: Use Modal for cloud scaling

This organized structure provides a professional, maintainable, and scalable foundation for congressional witness data analysis.