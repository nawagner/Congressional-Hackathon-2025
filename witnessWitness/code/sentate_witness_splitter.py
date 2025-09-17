import sys, os, re, json, uuid
import pandas as pd

def main(csv_path, out_dir="witness_json"):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    # Detect columns
    def pick(cols, prefer_contains=None, fallback_idx=0):
        if prefer_contains:
            for c in cols:
                if prefer_contains(c): return c
        return cols[0] if cols else (df.columns[fallback_idx] if len(df.columns) > fallback_idx else df.columns[0])

    witness_col = pick([c for c in df.columns if c.lower() in {"witness", "witnesses", "name", "witness name"}])
    date_col    = next((c for c in df.columns if c.lower() in {"date", "hearing date"}), None)
    title_col   = None
    maybe_titles = [c for c in df.columns if "title" in c.lower() or "hearing" in c.lower()]
    for c in maybe_titles:
        if "title" in c.lower():
            title_col = c; break
    if title_col is None:
        title_col = maybe_titles[0] if maybe_titles else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    tags_col    = next((c for c in df.columns if "tag" in c.lower() or "topics" in c.lower()), None)

    SPLIT_REGEX = re.compile(r"(?:\s*[;|]\s*|\s*,\s*|\s*\n+\s*)")

    def split_multi(cell):
        if pd.isna(cell): return []
        s = str(cell).strip()
        if not s: return []
        parts = [p.strip() for p in SPLIT_REGEX.split(s) if p.strip()]
        return parts if parts else [s]

    def to_iso_date(val):
        if pd.isna(val): return None
        s = str(val).strip()
        if not s: return None
        try:
            return pd.to_datetime(s).date().isoformat()
        except Exception:
            return s

    witness_map = {}
    for _, row in df.iterrows():
        witnesses = split_multi(row.get(witness_col, None))
        if not witnesses:  # skip rows without any witness parsed
            continue
        date_val = to_iso_date(row.get(date_col, None)) if date_col else None
        title_val = str(row.get(title_col, "")).strip()
        tags = split_multi(row.get(tags_col, None)) if tags_col else []

        for w in witnesses:
            w = w.strip()
            if not w: continue
            if w not in witness_map:
                witness_map[w] = {"name": w, "uuid": str(uuid.uuid4()), "hearings": []}
            witness_map[w]["hearings"].append({"date": date_val, "title": title_val, "tags": tags})

    os.makedirs(out_dir, exist_ok=True)

    def safe_filename(name, uid):
        base = re.sub(r"[^\w\-. ]+", "", name).strip()
        base = re.sub(r"\s+", " ", base) or "unnamed"
        if len(base) > 60: base = base[:60].rstrip()
        short_uid = uid.split("-")[0]
        return f"{base}__{short_uid}.json"

    manifest = []
    # Clear directory in case of re-run
    for f in os.listdir(out_dir):
        try: os.remove(os.path.join(out_dir, f))
        except Exception: pass

    for wname, payload in witness_map.items():
        fname = safe_filename(wname, payload["uuid"])
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        manifest.append({"witness": wname, "uuid": payload["uuid"], "file": os.path.join(out_dir, fname)})

    pd.DataFrame(manifest).sort_values("witness").to_csv("witness_manifest.csv", index=False)
    with open("witness_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Done. Wrote {len(manifest)} JSON files to '{out_dir}'.")
    print("Created 'witness_manifest.csv' and 'witness_manifest.json'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python witness_splitter.py <path/to/CSV> [out_dir]")
        sys.exit(1)
    csv_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "witness_json"
    main(csv_path, out_dir)
