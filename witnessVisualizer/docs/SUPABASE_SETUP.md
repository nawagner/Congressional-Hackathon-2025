# Supabase Database Setup for Congressional Witness Visualizer

This guide walks you through setting up a Supabase database to store congressional witness data and loading data from the scraper.

## Prerequisites

1. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
2. **Python Environment**: Ensure you have the project dependencies installed

## Step 1: Create Supabase Project

1. Log in to your Supabase dashboard
2. Click "New Project"
3. Choose your organization
4. Set a project name (e.g., "congressional-witnesses")
5. Set a strong database password
6. Choose a region close to you
7. Click "Create new project"

## Step 2: Get Connection Details

From your Supabase project dashboard:

1. Go to **Settings** → **API**
2. Note down:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **API Key** (use the `service_role` key for full access)

## Step 3: Create Database Schema

1. In your Supabase dashboard, go to **SQL Editor**
2. Copy the entire contents of `supabase_schema.sql`
3. Paste into the SQL Editor and click "Run"

This will create:
- **13 main tables** for witnesses, hearings, committees, documents, etc.
- **Indexes** for performance
- **Row Level Security (RLS)** policies
- **Triggers** for automatic timestamp updates
- **Views** for easy data access
- **Default topic data**

## Step 4: Install Python Dependencies

```bash
# In the witnessVisualizer directory
source ../venv/bin/activate  # or your virtual environment
pip install supabase
```

## Step 5: Load Data into Supabase

### From JSON File

```bash
python supabase_loader.py test_output.json \
  --supabase-url "https://YOUR-PROJECT.supabase.co" \
  --supabase-key "YOUR-SERVICE-ROLE-KEY" \
  --notes "Initial test data load"
```

### Environment Variables (Recommended)

Create a `.env` file:
```bash
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_KEY=YOUR-SERVICE-ROLE-KEY
```

Then use:
```bash
export SUPABASE_URL="https://YOUR-PROJECT.supabase.co"
export SUPABASE_KEY="YOUR-SERVICE-ROLE-KEY"

python supabase_loader.py test_output.json \
  --supabase-url "$SUPABASE_URL" \
  --supabase-key "$SUPABASE_KEY"
```

## Database Schema Overview

### Core Tables

1. **witnesses** - Individual testimony providers
   - `id`, `witness_id`, `name`, `title`, `witness_type`
   - `organization_id` (FK), `tribal_affiliation`, `background`

2. **hearings** - Congressional hearing events
   - `id`, `event_id`, `title`, `hearing_date`, `location`
   - `committee_id` (FK), `status`

3. **committees** - House committees and subcommittees
   - `id`, `committee_code`, `name`, `parent_committee_id`

4. **organizations** - Affiliated institutions
   - `id`, `name`, `organization_type`, `location`

5. **documents** - Testimony documents
   - `id`, `witness_id` (FK), `document_type`, `url`, `title`

### Relationship Tables

- **witness_hearings** - Links witnesses to hearings (many-to-many)
- **witness_topics** - Links witnesses to topics (many-to-many)
- **witness_relationships** - Captures connections between witnesses

### Analysis Tables

- **keywords** - Extracted keywords from testimony
- **expertise_areas** - Subject matter expertise
- **previous_testimonies** - Historical testimony tracking

## Step 6: Query Your Data

### Using Supabase Dashboard

1. Go to **Table Editor** to browse data
2. Use **SQL Editor** for custom queries

### Example Queries

**Get all witnesses for a specific hearing:**
```sql
SELECT w.name, w.title, o.name as organization
FROM witness_details_view w
JOIN witness_hearings wh ON w.id = wh.witness_id
JOIN hearings h ON wh.hearing_id = h.id
WHERE h.event_id = '117214';
```

**Find most active organizations:**
```sql
SELECT o.name, COUNT(w.id) as witness_count
FROM organizations o
JOIN witnesses w ON o.id = w.organization_id
GROUP BY o.id, o.name
ORDER BY witness_count DESC
LIMIT 10;
```

**Get witness network (who testified together):**
```sql
SELECT 
  w1.name as witness1,
  w2.name as witness2,
  wr.relationship_type,
  wr.context
FROM witness_relationships wr
JOIN witnesses w1 ON wr.source_witness_id = w1.id
JOIN witnesses w2 ON wr.target_witness_id = w2.id
WHERE wr.relationship_type = 'testified_together';
```

### Using Python Client

```python
from supabase import create_client

supabase = create_client(
    "https://YOUR-PROJECT.supabase.co",
    "YOUR-SERVICE-ROLE-KEY"
)

# Get all witnesses
witnesses = supabase.table('witness_details_view').select('*').execute()

# Get witnesses by topic
environmental_witnesses = supabase.table('witness_details_view') \
    .select('*') \
    .contains('topics', ['environment']) \
    .execute()

# Get hearing details
hearing = supabase.table('hearing_details_view') \
    .select('*') \
    .eq('event_id', '117214') \
    .execute()
```

## Step 7: Security Configuration

### Row Level Security (RLS)

The schema includes RLS policies:
- **Public read access** to all tables
- **Authenticated user access** for insert/update/delete

### Modify Access Policies

To restrict access, modify the RLS policies in SQL Editor:

```sql
-- Example: Restrict witness updates to specific users
DROP POLICY "Allow authenticated users to update" ON witnesses;

CREATE POLICY "Allow admin users to update" ON witnesses 
  FOR UPDATE TO authenticated 
  USING (auth.jwt() ->> 'role' = 'admin');
```

## Step 8: API Integration

### REST API

Supabase automatically generates REST APIs:

```bash
# Get all witnesses
curl "https://YOUR-PROJECT.supabase.co/rest/v1/witnesses" \
  -H "apikey: YOUR-ANON-KEY" \
  -H "Authorization: Bearer YOUR-ANON-KEY"

# Get witness by ID
curl "https://YOUR-PROJECT.supabase.co/rest/v1/witnesses?witness_id=eq.117214_0" \
  -H "apikey: YOUR-ANON-KEY" \
  -H "Authorization: Bearer YOUR-ANON-KEY"
```

### Real-time Subscriptions

```python
# Subscribe to new witnesses
def handle_witness_change(payload):
    print(f"New witness: {payload}")

supabase.table('witnesses').on('INSERT', handle_witness_change).subscribe()
```

## Performance Optimization

### Indexes

The schema includes optimized indexes for:
- Name searches
- Date range queries
- Topic filtering
- Organization lookups
- Full-text search

### Views

Pre-built views for common queries:
- `witness_details_view` - Complete witness information
- `hearing_details_view` - Hearing summaries with witness counts

## Backup and Migration

### Export Data

```bash
# Export as SQL
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" > backup.sql

# Export specific tables
supabase db dump --local > schema.sql
```

### Import Data

```bash
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" < backup.sql
```

## Troubleshooting

### Common Issues

1. **RLS Policy Errors**: Ensure you're using the `service_role` key for admin operations
2. **Foreign Key Violations**: Load data in dependency order (committees → organizations → hearings → witnesses)
3. **Unique Constraint Violations**: Check for duplicate `witness_id` or `event_id` values

### Debug Queries

```sql
-- Check data loading progress
SELECT * FROM scraping_sessions ORDER BY created_at DESC LIMIT 5;

-- Find missing relationships
SELECT w.name, w.witness_id 
FROM witnesses w 
LEFT JOIN witness_hearings wh ON w.id = wh.witness_id 
WHERE wh.id IS NULL;

-- Verify foreign key relationships
SELECT 
  (SELECT count(*) FROM witnesses WHERE organization_id IS NOT NULL) as witnesses_with_orgs,
  (SELECT count(*) FROM organizations) as total_orgs;
```

## Next Steps

1. **Automate Data Loading**: Set up scheduled scraping and loading
2. **Add Authentication**: Implement user authentication for data access
3. **Create Dashboard**: Build a web dashboard using the Supabase API
4. **Enhance Analysis**: Add NLP processing for document content
5. **Real-time Updates**: Set up real-time notifications for new testimony

## Support

- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **SQL Reference**: [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- **Project Issues**: Check GitHub issues for common problems

---

This database setup provides a solid foundation for analyzing congressional witness data with powerful querying, visualization, and analysis capabilities.