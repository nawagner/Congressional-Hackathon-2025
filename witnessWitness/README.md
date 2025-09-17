# Witness Witness

This is a proof of concept for creating a tracker history of Congressional hearing witnesses. 


## Senate database

The SQL lite database 'senate_hearings.sqlite' contains everthing from 'Senate Committee Hearings .csv'.  

Example queries:

Exact name match
```sql
SELECT hearing_title, hearing_date, hearing_tags
FROM witness_hearings
WHERE witness_name = 'Jane Doe'
ORDER BY hearing_date DESC;
```

Case-insensitive partial match
```sql
SELECT witness_name, hearing_title, hearing_date, committee, hearing_tags
FROM witness_hearings
WHERE LOWER(witness_name) LIKE LOWER('%doe%')
ORDER BY hearing_date DESC;
```

All witnesses for hearings with “climate” in the title
```sql
SELECT w.name
FROM hearings h
JOIN hearing_witnesses hw USING(hearing_id)
JOIN witnesses w USING(witness_id)
WHERE LOWER(h.title) LIKE LOWER('%climate%');
```

## Run the explorer locally

1. From the repository root start a static server. Any option works; for example:
   - Python: `python3 -m http.server 8000 --directory witnessWitness`
   - uv: `uv run python -m http.server 8000 --directory witnessWitness`
   - npm http-server: `npx http-server witnessWitness` (after `npm init -y` and `npm install --save-dev http-server`)
2. Open your browser to `http://localhost:8000/` (or the port shown in the server output).
3. Interact with `index.html` to explore witnesses, filter hearings, and follow hearing links.

## Scrape hearing details

The repository includes `scrape_hearing.py` for pulling data from a House hearing page.

1. Install dependencies (with uv): `uv pip install -r requirements.txt`
   - Or with pip: `python3 -m pip install --user -r requirements.txt`
2. Run the scraper: `python3 scrape_hearing.py`
   - Use `--url` to target a different event, e.g. `python3 scrape_hearing.py --url https://docs.house.gov/...`
   - Use `--db` to store results in another SQLite file, e.g. `python3 scrape_hearing.py --db my_hearings.db`

Each run writes JSON to stdout and upserts the data into `hearings.db` (tables `hearings` and `witnesses`).
