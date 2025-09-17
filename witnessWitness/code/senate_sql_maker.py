# Read the uploaded CSV, inspect its columns, and build a normalized SQLite database
import pandas as pd
import sqlite3
import os
from pathlib import Path
import re

# Path to the uploaded CSV
csv_path = "/mnt/data/Senate Committee Hearings.csv"

# Load CSV (let pandas infer newline-in-field correctly)
df = pd.read_csv(csv_path)

# Show basic info
cols = df.columns.tolist()
head = df.head(10)

# Create/overwrite SQLite DB
db_path = "/mnt/data/senate_hearings.sqlite"
if os.path.exists(db_path):
    os.remove(db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Helper: clean whitespace and normalize name spacing
def clean_str(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    # collapse internal whitespace
    s = re.sub(r'\s+', ' ', s)
    return s if s else None

# Try to infer likely column names
# We'll attempt to map common possibilities:
colmap = {
    "title": None,
    "date": None,
    "witnesses": None,
    "tags": None,
    "committee": None
}
lower_cols = {c.lower(): c for c in cols}

# Guess columns by keywords
for want, keys in [
    ("title", ["title", "hearing title", "hearing_title", "name"]),
    ("date", ["date", "hearing date", "hearing_date"]),
    ("witnesses", ["witnesses", "witness", "witness list", "witness_list"]),
    ("tags", ["tags", "topics", "subject"]),
    ("committee", ["committee", "senate committee", "committee_name"]),
]:
    for k in keys:
        if k in lower_cols and colmap[want] is None:
            colmap[want] = lower_cols[k]
            break

# Build normalized schema
cur.executescript(
"""
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE hearings (
    hearing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    hearing_date TEXT,
    committee TEXT,
    tags TEXT
);

CREATE TABLE witnesses (
    witness_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
);

CREATE TABLE hearing_witnesses (
    hearing_id INTEGER NOT NULL REFERENCES hearings(hearing_id) ON DELETE CASCADE,
    witness_id INTEGER NOT NULL REFERENCES witnesses(witness_id) ON DELETE CASCADE,
    PRIMARY KEY (hearing_id, witness_id)
);

-- A convenience view for searching by witness name
CREATE VIEW IF NOT EXISTS witness_hearings AS
SELECT
    w.name AS witness_name,
    h.title AS hearing_title,
    h.hearing_date AS hearing_date,
    h.tags AS hearing_tags,
    h.committee AS committee
FROM hearing_witnesses hw
JOIN witnesses w ON w.witness_id = hw.witness_id
JOIN hearings h ON h.hearing_id = hw.hearing_id;
"""
)

# Insert hearings
hearing_rows = []
for _, row in df.iterrows():
    title_val = clean_str(row.get(colmap["title"])) if colmap["title"] else None
    date_val = clean_str(row.get(colmap["date"])) if colmap["date"] else None
    committee_val = clean_str(row.get(colmap["committee"])) if colmap["committee"] else None
    tags_val = clean_str(row.get(colmap["tags"])) if colmap["tags"] else None
    hearing_rows.append((title_val, date_val, committee_val, tags_val))

cur.executemany(
    "INSERT INTO hearings (title, hearing_date, committee, tags) VALUES (?, ?, ?, ?);",
    hearing_rows
)
conn.commit()

# Fetch hearing_ids back in the original row order to align with witnesses splitting
cur.execute("SELECT hearing_id FROM hearings ORDER BY hearing_id;")
hearing_ids = [r[0] for r in cur.fetchall()]

# Insert witnesses and junctions
witness_name_to_id = {}

def get_or_create_witness_id(name):
    if name in witness_name_to_id:
        return witness_name_to_id[name]
    # Try insert, ignore if exists
    cur.execute("INSERT OR IGNORE INTO witnesses (name) VALUES (?);", (name,))
    # Retrieve id
    cur.execute("SELECT witness_id FROM witnesses WHERE name = ?;", (name,))
    wid = cur.fetchone()[0]
    witness_name_to_id[name] = wid
    return wid

# Split witnesses per hearing (one name per line inside the field)
# Accept \n, \r\n separators; also handle semicolons/commas just in case
split_pattern = re.compile(r"(?:\r\n|\n|;|,)+")

for idx, (_, row) in enumerate(df.iterrows()):
    witnesses_field = row.get(colmap["witnesses"]) if colmap["witnesses"] else None
    if pd.isna(witnesses_field) or str(witnesses_field).strip() == "":
        continue
    raw = str(witnesses_field)
    parts = [clean_str(p) for p in split_pattern.split(raw) if clean_str(p)]
    for name in parts:
        wid = get_or_create_witness_id(name)
        cur.execute(
            "INSERT OR IGNORE INTO hearing_witnesses (hearing_id, witness_id) VALUES (?, ?);",
            (hearing_ids[idx], wid)
        )

conn.commit()

# Quick sanity query: how many hearings, witnesses, and links
cur.execute("SELECT COUNT(*) FROM hearings;")
n_hearings = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM witnesses;")
n_witnesses = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM hearing_witnesses;")
n_links = cur.fetchone()[0]

# Example search: all hearings for a sample witness if available
example_results = pd.DataFrame()
if n_witnesses > 0:
    cur.execute("SELECT name FROM witnesses ORDER BY name LIMIT 1;")
    sample_name = cur.fetchone()[0]
    example_results = pd.read_sql_query(
        "SELECT witness_name, hearing_title, hearing_date, committee, hearing_tags "
        "FROM witness_hearings WHERE witness_name = ? ORDER BY hearing_date;",
        conn, params=(sample_name,)
    )

# Save a small README with usage examples
readme_path = "/mnt/data/README - Senate Hearings DB.txt"
with open(readme_path, "w") as f:
    f.write(
        "Senate Hearings SQLite Database\n"
        "================================\n\n"
        f"File: {Path(db_path).name}\n"
        f"Hearings: {n_hearings}\nWitnesses: {n_witnesses}\nLinks: {n_links}\n\n"
        "Schema:\n"
        "  hearings(hearing_id, title, hearing_date, committee, tags)\n"
        "  witnesses(witness_id, name)\n"
        "  hearing_witnesses(hearing_id, witness_id)\n\n"
        "Convenience view:\n"
        "  witness_hearings(witness_name, hearing_title, hearing_date, hearing_tags, committee)\n\n"
        "Common queries:\n"
        "1) Find all hearings for a witness name (case-sensitive exact match):\n"
        "   SELECT hearing_title, hearing_date, hearing_tags\n"
        "   FROM witness_hearings\n"
        "   WHERE witness_name = 'Jane Doe'\n"
        "   ORDER BY hearing_date DESC;\n\n"
        "2) Case-insensitive / partial match:\n"
        "   SELECT * FROM witness_hearings\n"
        "   WHERE LOWER(witness_name) LIKE LOWER('%doe%')\n"
        "   ORDER BY hearing_date DESC;\n\n"
        "3) All witnesses in a given hearing title substring:\n"
        "   SELECT w.name\n"
        "   FROM hearings h\n"
        "   JOIN hearing_witnesses hw USING(hearing_id)\n"
        "   JOIN witnesses w USING(witness_id)\n"
        "   WHERE LOWER(h.title) LIKE LOWER('%climate%');\n\n"
        "Notes:\n"
        "- Multiple witnesses per hearing in the CSV are split on newlines, semicolons, or commas.\n"
        "- Dates are stored as text exactly as provided in the CSV.\n"
        "- If you need stricter date parsing, you can cast/normalize hearing_date to ISO 8601 in a follow-up.\n"
    )

import caas_jupyter_tools
# Show a peek at the data and example query results to the user
caas_jupyter_tools.display_dataframe_to_user("CSV preview (first 10 rows)", head)
if not example_results.empty:
    caas_jupyter_tools.display_dataframe_to_user("Example: results for one witness", example_results)

# Final confirmation outputs
(db_path, readme_path, n_hearings, n_witnesses, n_links, colmap, cols)
