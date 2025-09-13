# server/db.py
import sqlite3, pathlib, json, time
DB_PATH = pathlib.Path(__file__).with_name("triage.db")

def _conn():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS cases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL,
        description TEXT,
        resp_rate REAL,
        pulse TEXT,
        cap_refill TEXT,
        triage_level TEXT,
        reasoning TEXT
    )""")
    return con

def log_case(description, resp_rate, pulse, cap_refill, triage_level, reasoning):
    con = _conn()
    con.execute("INSERT INTO cases(ts,description,resp_rate,pulse,cap_refill,triage_level,reasoning) VALUES(?,?,?,?,?,?,?)",
                (time.time(), description, resp_rate, pulse, str(cap_refill), triage_level, reasoning))
    con.commit(); con.close()

def recent_cases(limit=20):
    con = _conn()
    rows = con.execute("""SELECT ts,description,resp_rate,pulse,cap_refill,triage_level,reasoning
                          FROM cases ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    con.close()
    return [dict(ts=r[0], description=r[1], resp_rate=r[2], pulse=r[3],
                 cap_refill=r[4], triage_level=r[5], reasoning=r[6]) for r in rows]
