# Congressional Law vs Campaign Objectives Analyzer

This app compares passed laws against their sponsors' campaign objectives using LLM analysis. It scrapes campaign websites, extracts objectives using AI, and provides detailed alignment analysis.

## Features

- **Law Data Loading**: Parses JSON files containing law information
- **Campaign Website Scraping**: Extracts content from sponsor websites
- **LLM Analysis**: Uses OpenAI or Anthropic APIs to analyze campaign objectives
- **Alignment Comparison**: Compares laws against extracted objectives
- **Interactive Web Interface**: Streamlit-based UI for exploration
- **Batch Processing**: Command-line tool for analyzing all laws at once

## Setup

1. **Install Dependencies**:

   ```bash
   pip install -e .
   ```

2. **Set up API Keys**:
   Copy `.env.example` to `.env` and add your API keys:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add either:

   - `OPENAI_API_KEY=your_openai_api_key_here`
   - `ANTHROPIC_API_KEY=your_anthropic_api_key_here`

3. **Run the Web App**:

   ```bash
   streamlit run app.py
   ```

4. **Run Batch Analysis**:
   ```bash
   python batch_analyzer.py
   ```

## Data Structure

The app expects law data in JSON format with this structure:

```json
{
  "title": "Law Title",
  "sponsor": {
    "name": "Sponsor Name",
    "websiteUrl": "https://sponsor-website.com",
    "state": "State",
    "bioguideId": "B001234"
  },
  "text": "Full law text...",
  "actions": [...],
  "congress": 119,
  "number": "123",
  "originChamberCode": "H"
}
```

## Usage

### Web Interface

1. Open the Streamlit app
2. Select a law from the dropdown
3. Click "Analyze Campaign Objectives" to:
   - Scrape the sponsor's website
   - Extract campaign objectives using LLM
   - Compare the law against objectives
   - View alignment score and detailed analysis

### Batch Processing

Run `batch_analyzer.py` to analyze all laws and generate:

- `law_campaign_analysis_results.json`: Detailed results for each law
- `law_campaign_analysis_summary.csv`: Summary statistics

## Output

The analysis provides:

- **Alignment Score**: 0-100 score of how well the law aligns with campaign objectives
- **Supporting Objectives**: Campaign objectives that the law supports
- **Conflicting Objectives**: Campaign objectives that might conflict with the law
- **Detailed Assessment**: AI-generated analysis of the alignment

## Example Results

- **High Alignment (70-100)**: Law strongly supports campaign objectives
- **Medium Alignment (40-69)**: Law partially aligns with some objectives
- **Low Alignment (0-39)**: Law conflicts with or doesn't support campaign objectives

## Technical Details

- **Web Scraping**: Uses BeautifulSoup with respectful delays
- **LLM Integration**: Supports both OpenAI GPT and Anthropic Claude
- **Data Processing**: Handles large JSON files efficiently
- **Error Handling**: Graceful fallbacks when websites are unavailable
- **Rate Limiting**: Built-in delays to respect API limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Congressional Hackathon 2025.
