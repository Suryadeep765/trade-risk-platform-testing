from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class StateStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS risk_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            pnl REAL NOT NULL,
            gross_exposure REAL NOT NULL,
            net_exposure REAL NOT NULL,
            delta REAL NOT NULL,
            gamma REAL NOT NULL,
            vega REAL NOT NULL,
            theta REAL NOT NULL,
            var95 REAL NOT NULL,
            anomaly_count INTEGER NOT NULL,
            positions_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def add_snapshot(self, snapshot):
        self.conn.execute(
            "INSERT INTO risk_snapshots VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?)",
            (snapshot["ts"], snapshot["pnl"], snapshot["gross_exposure"], snapshot["net_exposure"],
             snapshot["delta"], snapshot["gamma"], snapshot["vega"], snapshot["theta"],
             snapshot["var95"], snapshot["anomaly_count"], json.dumps(snapshot["positions"]))
        )
        self.conn.commit()

    def add_event(self, ts, event_type, payload):
        self.conn.execute("INSERT INTO events(ts,event_type,payload) VALUES(?,?,?)", (ts, event_type, json.dumps(payload)))
        self.conn.commit()

    def latest(self, limit=100):
        cur = self.conn.execute("SELECT * FROM risk_snapshots ORDER BY id DESC LIMIT ?", (limit,))
        cols = [x[0] for x in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return list(reversed(rows))
