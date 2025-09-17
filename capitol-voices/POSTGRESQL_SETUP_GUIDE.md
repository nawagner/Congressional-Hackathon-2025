# PostgreSQL Setup Guide for CapitolVoices

## 🐘 Why PostgreSQL for Congressional Hearings?

PostgreSQL provides significant advantages over SQLite for handling Congressional hearing data:

### **Performance Benefits**
- **Concurrent access**: Multiple users can access transcripts simultaneously
- **Full-text search**: Advanced search capabilities across all hearings
- **JSONB support**: Flexible metadata storage for committee information
- **Indexing**: Optimized queries for large datasets
- **Scalability**: Handle thousands of hearings efficiently

### **YouTube Video Integration**
- **Large datasets**: Better handling of long hearing videos (2+ hours)
- **Complex queries**: Search across multiple hearings and committees
- **Metadata storage**: Rich committee and speaker information
- **Backup & recovery**: Professional-grade data protection

## 🚀 Quick Setup

### 1. Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Run the installer and follow the setup wizard

### 2. Run CapitolVoices PostgreSQL Setup

```bash
cd capitol-voices
python setup_postgresql.py
```

This script will:
- ✅ Check PostgreSQL installation
- ✅ Create database and user
- ✅ Install Python dependencies
- ✅ Create configuration files
- ✅ Test the connection

### 3. Configure Environment

The setup script creates a `.env` file:
```bash
# CapitolVoices PostgreSQL Configuration
STORAGE_ENGINE=postgresql
POSTGRESQL_CONNECTION_STRING=postgresql://capitol_voices:capitol_voices_password@localhost:5432/capitol_voices
POSTGRESQL_SCHEMA=capitol_voices

# HuggingFace token for PyAnnote (required)
HF_TOKEN=your_huggingface_token_here
```

**Update the HF_TOKEN** with your HuggingFace token for PyAnnote diarization.

### 4. Run Demo with PostgreSQL

```bash
python demo_postgresql_setup.py
streamlit run ui/app.py
```

## 🏗️ Database Schema

### **Hearings Table**
```sql
CREATE TABLE capitol_voices.hearings (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    committee VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    video_url TEXT,
    youtube_video_id VARCHAR(50),
    duration_seconds INTEGER,
    duration_minutes INTEGER,
    expected_speakers INTEGER,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);
```

### **Speakers Table**
```sql
CREATE TABLE capitol_voices.speakers (
    hearing_id VARCHAR(255) REFERENCES hearings(id) ON DELETE CASCADE,
    speaker_key VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(100),
    committee_position VARCHAR(100),
    party VARCHAR(50),
    state VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (hearing_id, speaker_key)
);
```

### **Segments Table**
```sql
CREATE TABLE capitol_voices.segments (
    id SERIAL PRIMARY KEY,
    hearing_id VARCHAR(255) REFERENCES hearings(id) ON DELETE CASCADE,
    start_s DECIMAL(10,3) NOT NULL,
    end_s DECIMAL(10,3) NOT NULL,
    speaker_key VARCHAR(100),
    text TEXT NOT NULL,
    confidence DECIMAL(5,4),
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Indexes for Performance**
```sql
-- Full-text search index
CREATE INDEX idx_segments_text_search 
ON segments USING gin(to_tsvector('english', text));

-- Timestamp range queries
CREATE INDEX idx_segments_timestamp 
ON segments(hearing_id, start_s, end_s);

-- Speaker queries
CREATE INDEX idx_segments_speaker 
ON segments(hearing_id, speaker_key);

-- Committee and date queries
CREATE INDEX idx_hearings_committee 
ON hearings(committee);

CREATE INDEX idx_hearings_date 
ON hearings(date);
```

## 🔍 Advanced Features

### **Full-Text Search**
```python
# Search across all hearings
results = storage.search_hearings(
    query="accountability transparency",
    committee="House Oversight",
    date_from="2025-01-01",
    date_to="2025-12-31"
)
```

### **Hearing Statistics**
```python
# Get comprehensive statistics
stats = storage.get_hearing_statistics("house-oversight-2025-01-15")
print(f"Total segments: {stats['total_segments']}")
print(f"Unique speakers: {stats['unique_speakers']}")
print(f"Total words: {stats['total_words']}")
```

### **Complex Queries**
```sql
-- Find all hearings by a specific committee
SELECT h.title, h.date, COUNT(s.id) as segment_count
FROM hearings h
LEFT JOIN segments s ON h.id = s.hearing_id
WHERE h.committee = 'House Committee on Oversight and Accountability'
GROUP BY h.id, h.title, h.date
ORDER BY h.date DESC;

-- Search for specific topics across all hearings
SELECT h.title, h.committee, h.date, s.text
FROM hearings h
JOIN segments s ON h.id = s.hearing_id
WHERE to_tsvector('english', s.text) @@ plainto_tsquery('english', 'cybersecurity privacy')
ORDER BY h.date DESC, s.start_s;
```

## 📊 Performance Comparison

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Concurrent Users** | 1 | 100+ |
| **Full-Text Search** | Basic | Advanced |
| **JSON Support** | Limited | Native JSONB |
| **Indexing** | Basic | Advanced |
| **Backup** | File copy | Professional tools |
| **Scalability** | Single file | Distributed |
| **YouTube Videos** | Limited | Optimized |

## 🛠️ Configuration Options

### **Connection Pooling**
```yaml
postgresql:
  max_connections: 20
  connection_timeout: 30
  enable_full_text_search: true
  enable_jsonb_indexing: true
```

### **Performance Tuning**
```sql
-- Optimize for Congressional hearing workloads
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

## 🔧 Troubleshooting

### **Connection Issues**
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql
# or
sudo systemctl status postgresql

# Test connection
psql -h localhost -U capitol_voices -d capitol_voices
```

### **Permission Issues**
```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE capitol_voices TO capitol_voices;
GRANT ALL PRIVILEGES ON SCHEMA capitol_voices TO capitol_voices;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA capitol_voices TO capitol_voices;
```

### **Performance Issues**
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE capitol_voices.segments;
ANALYZE capitol_voices.hearings;
```

## 🚀 Production Deployment

### **Docker Setup**
```dockerfile
FROM postgres:15
COPY init.sql /docker-entrypoint-initdb.d/
ENV POSTGRES_DB=capitol_voices
ENV POSTGRES_USER=capitol_voices
ENV POSTGRES_PASSWORD=secure_password
```

### **Backup Strategy**
```bash
# Daily backup
pg_dump -h localhost -U capitol_voices capitol_voices > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h localhost -U capitol_voices capitol_voices < backup_20250115.sql
```

### **Monitoring**
```sql
-- Monitor database size
SELECT pg_size_pretty(pg_database_size('capitol_voices'));

-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'capitol_voices'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🎯 Congressional Use Cases

### **Committee Staff**
- Search across all hearings for specific topics
- Track member participation over time
- Generate reports on hearing activity

### **Public Access**
- Full-text search across all public hearings
- Browse by committee, date, or topic
- Export transcripts in multiple formats

### **Analytics**
- Speaker participation statistics
- Topic trend analysis
- Committee activity reports

---

*PostgreSQL provides the robust foundation needed for professional Congressional hearing management at scale.* 🏛️💻
