# CongressTrack 🏛️

A comprehensive tool for analyzing Congressional laws and comparing them against sponsors' campaign objectives using AI-powered analysis.

## Overview

CongressTrack is designed to provide transparency and accountability in government by analyzing how well Congressional members' legislative actions align with their stated campaign objectives. The tool uses web scraping, natural language processing, and LLM analysis to extract campaign objectives from official websites and compare them against actual legislation.

## Features

### 🎯 Campaign Objectives Analysis

- **Web Scraping**: Automatically discovers and scrapes Congressional members' official campaign websites
- **AI-Powered Extraction**: Uses OpenAI GPT or Anthropic Claude to extract campaign objectives from website content
- **Objective Classification**: Identifies key policy areas, priorities, and campaign promises

### 📊 Law Analysis & Comparison

- **Legislative Data**: Processes Congressional law data from the official Congress.gov API
- **Alignment Scoring**: Provides quantitative scores (0-100) for how well laws align with campaign objectives
- **Detailed Analysis**: Identifies supporting and conflicting objectives for each law

### 📈 Interactive Visualizations

- **Congressional Leaderboard**: Beautiful leaderboard showing most active law sponsors
- **Chamber Comparison**: Visual breakdown of House vs Senate legislative activity
- **State Analysis**: Geographic distribution of legislative activity
- **Achievement Badges**: Recognition for top performers in different categories

### 🔍 Individual Law Analysis

- **Law Details**: Complete information about each law including sponsor, text, and legislative history
- **Campaign Comparison**: Side-by-side analysis of law content vs campaign objectives
- **Timeline View**: Legislative actions and progress tracking

## Data Sources

- **Congress.gov API**: Official Congressional data including laws, sponsors, and legislative actions
- **Campaign Websites**: Official websites of Congressional members
- **Legislative Text**: Full text of passed laws and bills

## Technology Stack

- **Frontend**: Streamlit for interactive web interface
- **Data Processing**: Pandas for data manipulation and analysis
- **Web Scraping**: BeautifulSoup4 and requests for website content extraction
- **AI Analysis**: OpenAI GPT and Anthropic Claude for natural language processing
- **Visualization**: Plotly for interactive charts and graphs
- **Search**: DuckDuckGo Search API for discovering campaign websites

## Installation

### Prerequisites

- Python 3.13 or higher
- API keys for OpenAI or Anthropic (for AI analysis)

### Setup

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd congresstrack
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   # or using uv (recommended)
   uv sync
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:

   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Usage

### Web Interface

1. **Launch the app**: Run `streamlit run app.py` and open your browser to the provided URL
2. **Choose analysis mode**:
   - **Law vs Campaign Analysis**: Analyze individual laws against campaign objectives
   - **Sponsor Visualization**: View the Congressional leaderboard and statistics

### Command Line Analysis

For batch processing of all laws:

```bash
python batch_analyzer.py
```

This will:

- Analyze all laws in the data directory
- Generate a comprehensive report
- Save results to `law_campaign_analysis_results.json`
- Create a CSV summary file

### Data Pipeline

To fetch new Congressional data:

```bash
python passed_law_pipeline.py
```

This script:

- Connects to the Congress.gov API
- Downloads law data for the 119th Congress
- Processes sponsor information and legislative text
- Saves structured JSON files to the `data/` directory

## Project Structure

```
congresstrack/
├── app.py                      # Main Streamlit application
├── batch_analyzer.py          # Batch analysis script
├── passed_law_pipeline.py     # Data collection pipeline
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
├── data/                     # Congressional law data (JSON files)
│   ├── H.119.*.json         # House bills
│   └── S.119.*.json         # Senate bills
└── notebooks/               # Jupyter notebooks for data exploration
```

## Key Components

### LawDataLoader

- Loads and parses Congressional law data from JSON files
- Handles data validation and error management
- Provides structured access to law metadata and content

### CampaignScraper

- Discovers campaign websites using web search
- Scrapes website content and extracts relevant text
- Handles various website formats and structures

### LLMAnalyzer

- Integrates with OpenAI GPT and Anthropic Claude APIs
- Extracts campaign objectives from website content
- Compares laws against objectives with detailed analysis

### SponsorAnalyzer

- Creates visualizations and statistics for Congressional activity
- Generates leaderboards and comparative analysis
- Provides data export capabilities

## Data Format

Laws are stored as JSON files with the following structure:

```json
{
  "title": "Law Title",
  "sponsor": {
    "name": "Sponsor Name",
    "websiteUrl": "https://example.com",
    "state": "TX",
    "bioguideId": "A000000"
  },
  "text": "Full law text...",
  "actions": [...],
  "congress": 119,
  "number": "1",
  "originChamberCode": "H"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m "Add feature"`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Congress.gov API**: Official Congressional data source
- **OpenAI & Anthropic**: AI analysis capabilities
- **Streamlit**: Web application framework
- **Congressional Hackathon 2025**: Project inspiration and context

## Support

For questions, issues, or contributions, please:

- Open an issue on GitHub
- Contact the development team
- Check the documentation for common solutions

---

**CongressTrack** - Bringing transparency to Congressional accountability through AI-powered analysis.
