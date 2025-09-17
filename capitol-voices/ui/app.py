import os, json, sqlite3, time, validators
import streamlit as st
from pathlib import Path

DB_PATH = "data/hearings.db"

st.set_page_config(page_title="CapitolVoices", layout="wide")
st.title("📜 CapitolVoices")
st.caption("machine-generated transcripts and summaries with timestamp verification.")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS hearings(id TEXT PRIMARY KEY, title TEXT, committee TEXT, date TEXT, video_url TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS summaries(hearing_id TEXT, type TEXT, content_json TEXT, PRIMARY KEY (hearing_id, type))")
    cur.execute("CREATE TABLE IF NOT EXISTS segments(id INTEGER PRIMARY KEY AUTOINCREMENT, hearing_id TEXT, start_s REAL, end_s REAL, speaker_key TEXT, text TEXT)")
    conn.commit(); return conn

conn = init_db()

with st.sidebar:
    st.header("Register Hearing")
    hid = st.text_input("Hearing ID", "demo-001")
    title = st.text_input("Title", "Demo Hearing")
    committee = st.text_input("Committee", "House Oversight")
    date = st.text_input("Date", "2025-09-10")
    url = st.text_input("YouTube URL", "")
    if st.button("Save"):
        cur = conn.cursor()
        cur.execute("REPLACE INTO hearings(id,title,committee,date,video_url) VALUES(?,?,?,?,?)", (hid,title,committee,date,url))
        conn.commit()
        st.success("Saved")

st.subheader("Hearing Browser")
cur = conn.cursor()
cur.execute("SELECT id,title,committee,date,video_url FROM hearings ORDER BY date DESC")
rows = cur.fetchall()
sel = st.selectbox("Select", [r[0] for r in rows]) if rows else None
if sel:
    row = next(r for r in rows if r[0]==sel)
    st.markdown(f"**{row[1]}**  \n{row[2]} • {row[3]}")
    if row[4] and validators.url(row[4]):
        st.video(row[4])
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("### Transcript")
        cur.execute("SELECT start_s,end_s,speaker_key,text FROM segments WHERE hearing_id=? ORDER BY start_s", (sel,))
        segs = cur.fetchall()
        q = st.text_input("Search", "")
        for s in segs:
            if not q or q.lower() in (s[3] or "").lower():
                ts = time.strftime('%H:%M:%S', time.gmtime(int(s[0] or 0)))
                cur2 = conn.cursor(); cur2.execute("SELECT display_name FROM speakers WHERE hearing_id=? AND speaker_key=?", (sel, s[2])); m = cur2.fetchone(); disp = m[0] if m and m[0] else (s[2] or 'Speaker'); st.markdown(f"**[{ts}] {disp}:** {s[3]}")
    with col2:
        st.markdown("### Summary")
        cur.execute("SELECT content_json FROM summaries WHERE hearing_id=? AND type='default'", (sel,))
        r = cur.fetchone()
        if r:
            summary = json.loads(r[0])
            st.write(summary.get("executive","(none)"))
            if "bullets" in summary:
                st.markdown("**Key Bullets (timestamp-verified)**")
                for b in summary["bullets"]:
                    st.markdown(f"- {b}")
            st.markdown("**By Speaker**")
            for item in summary.get("by_speaker", []):
                st.markdown(f"- **{item.get('speaker','?')}**")
                for p in item.get("points", []):
                    st.markdown(f"  - {p}")
