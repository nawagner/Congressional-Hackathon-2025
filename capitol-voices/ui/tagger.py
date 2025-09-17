import sqlite3, streamlit as st

DB_PATH = "data/hearings.db"

st.set_page_config(page_title="Manual Speaker Tagger", layout="centered")
st.title("🧩 Manual Speaker Tagger")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS speakers(hearing_id TEXT, speaker_key TEXT, display_name TEXT, role TEXT, PRIMARY KEY (hearing_id, speaker_key))")
    conn.commit()
    return conn

conn = init_db()

hid = st.text_input("Hearing ID", "demo-001")
if hid:
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT speaker_key FROM segments WHERE hearing_id=? ORDER BY speaker_key", (hid,))
    keys = [r[0] for r in cur.fetchall() if r[0]]
    st.write("Detected speaker keys:", keys or "(none)")

    st.subheader("Map keys → names/roles")
    for k in keys:
        with st.form(f"form_{k}"):
            cur.execute("SELECT display_name, role FROM speakers WHERE hearing_id=? AND speaker_key=?", (hid, k))
            row = cur.fetchone()
            name = st.text_input("Display name", value=row[0] if row else "", key=f"name_{k}")
            role = st.selectbox("Role", ["Chair", "Ranking Member", "Member", "Witness", "Staff", "Other"], index=5 if not row else ["Chair","Ranking Member","Member","Witness","Staff","Other"].index(row[1]) if row and row[1] in ["Chair","Ranking Member","Member","Witness","Staff","Other"] else 5, key=f"role_{k}")
            submitted = st.form_submit_button("Save mapping")
            if submitted:
                cur.execute("REPLACE INTO speakers(hearing_id, speaker_key, display_name, role) VALUES(?,?,?,?)", (hid, k, name, role))
                conn.commit()
                st.success(f"Saved mapping for {k} → {name} ({role})")

    st.subheader("Preview (first 30 lines)")
    cur.execute("SELECT start_s, speaker_key, text FROM segments WHERE hearing_id=? ORDER BY start_s LIMIT 30", (hid,))
    segs = cur.fetchall()
    for s in segs:
        cur.execute("SELECT display_name, role FROM speakers WHERE hearing_id=? AND speaker_key=?", (hid, s[1]))
        m = cur.fetchone()
        disp = m[0] if m and m[0] else s[1] or "Speaker"
        st.markdown(f"**[{int(s[0]//60):02d}:{int(s[0]%60):02d}] {disp}:** {s[2]}")
