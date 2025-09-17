# Congressional Hearings Scraper - Modal Deployment

High-performance scraper using all 82 Congress.gov API keys with parallel processing.

## 🚀 Features

- **82 API Key Rotation**: Uses all your Congress.gov API keys for maximum throughput
- **Parallel Processing**: Multiple Modal containers running simultaneously  
- **Smart Rate Limiting**: Optimized to avoid API limits
- **Witness Extraction**: Parses HTML documents to extract witness lists
- **Supabase Integration**: Direct insertion into your congressional_hearings table
- **Error Handling**: Robust error handling with detailed logging

## 📋 Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Modal CLI**: Install and authenticate
   ```bash
   pip install modal
   modal token new
   ```

3. **Supabase Database**: Ensure your `congressional_hearings` table exists

## 🔧 Setup Instructions

### 1. Create Modal Secrets

Create a Modal secret with your environment variables:

```bash
modal secret create congressional-secrets \
  SUPABASE_URL="https://your-project.supabase.co" \
  SUPABASE_SERVICE_ROLE_KEY="your-service-role-key" \
  CONGRESS_GOV_API_KEY="your-first-api-key" \
  CONGRESS_GOV_API_KEY_2="your-second-api-key" \
  # ... (continue for all 82 keys)
```

**Or use the batch script below:**

### 2. Batch Secret Creation Script

Create a file `setup_modal_secrets.py`:

```python
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Extract all API keys from .env
api_keys = {}
for i in range(1, 83):
    key_name = f"CONGRESS_GOV_API_KEY" if i == 1 else f"CONGRESS_GOV_API_KEY_{i}"
    key_value = os.getenv(key_name)
    if key_value:
        api_keys[key_name] = key_value

# Add Supabase credentials
secrets = {
    'SUPABASE_URL': os.getenv('SUPABASE_URL'),
    'SUPABASE_SERVICE_ROLE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
    **api_keys
}

# Build modal secret command
cmd = ['modal', 'secret', 'create', 'congressional-secrets']
for key, value in secrets.items():
    if value:
        cmd.extend([f'{key}={value}'])

print(f"Creating Modal secret with {len(secrets)} environment variables...")
subprocess.run(cmd)
print("✅ Modal secrets created!")
```

Run it:
```bash
python setup_modal_secrets.py
```

### 3. Deploy and Run

```bash
# Deploy to Modal
modal deploy modal_launch/congressional_hearings_modal.py

# Run the scraper
modal run modal_launch/congressional_hearings_modal.py
```

## 📊 Expected Performance

- **API Keys**: 82 keys rotating for maximum throughput
- **Rate Limits**: ~82 requests/second (1 per key per second)
- **Parallel Processing**: 4-6 Modal containers running simultaneously
- **Expected Volume**: 
  - House hearings: ~200-500 per congress
  - Senate hearings: ~300-600 per congress  
  - Total: ~1000-2000 hearings per run
- **Runtime**: 10-20 minutes for comprehensive scraping

## 🎯 What Gets Scraped

### Congress Sessions
- **Congress 116** (2019-2020)
- **Congress 117** (2021-2022) 
- **Congress 118** (2023-2024)

### Data Fields Populated
- ✅ `congress` - Congress session number
- ✅ `hearing_type` - 'house' or 'senate'
- ✅ `hearing_subtype` - 'subcommittee' if applicable
- ✅ `committee` - Full committee name
- ✅ `hearing_date` - Date of hearing
- ✅ `hearing_name` - Title of hearing
- ✅ `serial_no` - Hearing jacket number
- ✅ `detail_url` - Congress.gov API URL
- ✅ `document_url` - PDF document URL
- ✅ `witnesses` - Extracted witness names (JSONB array)
- ⚠️ `members` - Empty (not available from API)
- ⚠️ `bill_numbers` - Empty (could be enhanced)

## 🔍 Monitoring Progress

The scraper provides real-time progress updates:

```
🏛️  Processing HOUSE hearings...
📋 Found 150 house hearings for Congress 118
✅ Scraped 150 hearings total
📊 Total house hearings scraped: 150
💾 Inserting 150 hearings to database...
✅ Successfully inserted: 120, Skipped: 30, Failed: 0
```

## 🗃️ Database Queries

After scraping, query your data:

```sql
-- Total hearings
SELECT COUNT(*) FROM congressional_hearings;

-- By committee
SELECT committee, COUNT(*) as hearing_count 
FROM congressional_hearings 
GROUP BY committee 
ORDER BY hearing_count DESC;

-- Hearings with most witnesses
SELECT hearing_name, jsonb_array_length(witnesses) as witness_count
FROM congressional_hearings 
WHERE jsonb_array_length(witnesses) > 5
ORDER BY witness_count DESC;

-- Recent hearings
SELECT hearing_name, hearing_date, committee, jsonb_array_length(witnesses) as witnesses
FROM congressional_hearings 
ORDER BY hearing_date DESC 
LIMIT 20;

-- Senate vs House breakdown
SELECT hearing_type, COUNT(*) as count, AVG(jsonb_array_length(witnesses)) as avg_witnesses
FROM congressional_hearings 
GROUP BY hearing_type;
```

## 🛠️ Troubleshooting

### Common Issues

1. **Secret Creation Failed**
   ```bash
   # Check existing secrets
   modal secret list
   
   # Delete and recreate if needed
   modal secret delete congressional-secrets
   ```

2. **API Rate Limits**
   - The scraper automatically handles rate limits
   - With 82 keys, you should rarely hit limits
   - If you do, the scraper will pause and retry

3. **Database Connection Issues**
   - Verify Supabase credentials in Modal secrets
   - Check that your service role key has insert permissions
   - Ensure the `congressional_hearings` table exists

4. **Witness Extraction Issues**
   - Some hearings may not have witness lists in HTML format
   - This is normal - witnesses array will be empty for those hearings
   - Success rate is typically 60-80% for witness extraction

## 📈 Optimization Tips

1. **Increase Batch Size**: Modify `batch_size = 100` to `200` for faster processing
2. **Add More Congress Sessions**: Add older congress numbers to `congress_sessions` list
3. **Enable Bill Number Extraction**: Enhance the scraper to extract bill references
4. **Add Member Lists**: Integrate with committee membership APIs

## 🎉 Success Metrics

A successful run should yield:
- **1000+ hearings** across both chambers
- **60-80% with witness data** (witnesses array populated)
- **<5% failed insertions** (due to duplicates/errors)
- **10-20 minute runtime** for full scraping

Your `congressional_hearings` table will be comprehensively populated with recent congressional hearing data!