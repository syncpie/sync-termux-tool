import json
import sqlite3
from pathlib import Path
from config import DATABASE_PATH, HISTORY_LIMIT

class History:
    def __init__(self):
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY, time TEXT, cpu REAL, memory REAL, battery INTEGER)")
        self.db.commit()

    def add(self, snapshot):
        battery = snapshot.get("battery", {}).get("percent")
        self.db.execute("INSERT INTO samples(time,cpu,memory,battery) VALUES(?,?,?,?)",
                        (snapshot.get("time"), snapshot.get("cpu_percent", 0),
                         snapshot.get("memory_percent", 0), battery))
        self.db.execute("DELETE FROM samples WHERE id NOT IN (SELECT id FROM samples ORDER BY id DESC LIMIT ?)", (HISTORY_LIMIT,))
        self.db.commit()

    def recent(self, limit=120):
        rows = self.db.execute("SELECT time,cpu,memory,battery FROM samples ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"time": r[0], "cpu_percent": r[1], "memory_percent": r[2],
                 "battery": {"percent": r[3]}} for r in reversed(rows)]
