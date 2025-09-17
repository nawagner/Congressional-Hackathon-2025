# Witness Witness

This is a proof of concept for creating a tracker history of Congressional hearing witnesses. 


## Senate

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