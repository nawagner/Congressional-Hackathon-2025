# Modal Launch for Witness Scrapers

This folder contains the Modal deployment setup for running witness scrapers on Modal's cloud infrastructure.

## Files

- `modal_witness_scraper.py` - Main Modal application for witness scraping
- `setup_modal.py` - Setup script to configure Modal secrets and deploy
- `modal_requirements.txt` - Python dependencies for Modal environment
- `.env` - Environment variables (copied from data-modeling project)
- `README.md` - This file

## Quick Start

1. **Install Modal CLI**:
   ```bash
   pip install modal
   ```

2. **Authenticate with Modal**:
   ```bash
   modal auth set-token <your-token>
   ```

3. **Run setup script**:
   ```bash
   python setup_modal.py
   ```

4. **Test the deployment**:
   ```bash
   modal run modal_witness_scraper.py --test-only
   ```

5. **Run the scraper**:
   ```bash
   modal run modal_witness_scraper.py --max-events 10
   ```

## What the Modal Setup Does

- **Scalable Infrastructure**: Runs scrapers on Modal's cloud infrastructure
- **Parallel Processing**: Can process multiple witness events simultaneously
- **Data Persistence**: Uses Modal volumes to store scraped data
- **Environment Management**: Securely manages environment variables and secrets
- **Resource Control**: Configures CPU, memory, and timeout settings

## Configuration

The setup automatically creates Modal secrets from your `.env` file:

- `database-credentials` - Database and Supabase credentials
- `aws-credentials` - AWS S3 configuration
- `proxy-credentials` - Proxy server settings
- `scraper-config` - Browser and logging configuration

## Usage Examples

### Basic scraping (10 events):
```bash
modal run modal_witness_scraper.py
```

### Scrape more events:
```bash
modal run modal_witness_scraper.py --max-events 50
```

### Test connectivity only:
```bash
modal run modal_witness_scraper.py --test-only
```

## Output

Scraped data is saved to Modal volumes at `/data/house_witnesses_{timestamp}.json`

You can download the results using Modal's volume management commands.

## Benefits of Using Modal

1. **Scalability**: Handle large scraping jobs without local resource limits
2. **Reliability**: Built-in retry mechanisms and error handling
3. **Cost-effective**: Pay only for compute time used
4. **No Infrastructure Management**: No need to manage servers or containers
5. **Easy Monitoring**: Built-in logging and monitoring tools

## Troubleshooting

If you encounter issues:

1. Check Modal CLI installation: `modal --version`
2. Verify authentication: `modal profile current`
3. Check deployment status: `modal app list`
4. View logs: `modal logs <app-name>`

For more help, see the [Modal documentation](https://modal.com/docs).