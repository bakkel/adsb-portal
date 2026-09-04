#!/usr/bin/env python3
"""ADS-B Portal — proxy server + SQLite history recorder + stats."""
import http.server
import socketserver
import urllib.request
import sqlite3
import threading
import time
import json
import os
from datetime import datetime

PORT       = int(os.environ.get("PORT", 8081))
FR24_BASE  = os.environ.get("FR24_BASE", "http://localhost:8754")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DB_PATH    = os.environ.get("DB_PATH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "fr24portal.db")

# Flights.json field indices
F_ALT, F_SPEED, F_SQK, F_GROUND, F_VRATE, F_CS = 4, 5, 6, 14, 15, 16

AIRLINES = {
    "EZY":"easyJet","RYR":"Ryanair","KLM":"KLM Royal Dutch Airlines",
    "TRA":"Transavia","HV":"Transavia","VLG":"Vueling","IBE":"Iberia",
    "DLH":"Lufthansa","AFR":"Air France","BAW":"British Airways",
    "SWR":"Swiss International","AUA":"Austrian Airlines",
    "BEL":"Brussels Airlines","WZZ":"Wizz Air","EXS":"Jet2",
    "TOM":"TUI Airways","TFL":"TUI fly Netherlands","DAL":"Delta Air Lines",
    "UAL":"United Airlines","AAL":"American Airlines","THY":"Turkish Airlines",
    "PGT":"Pegasus Airlines","SXS":"SunExpress","NAX":"Norwegian",
    "FIN":"Finnair","SAS":"SAS Scandinavian","TAP":"TAP Air Portugal",
    "LOT":"LOT Polish Airlines","UAE":"Emirates","QTR":"Qatar Airways",
    "ETD":"Etihad Airways","SIA":"Singapore Airlines","ETH":"Ethiopian Airlines",
    "MPH":"Martinair","CLX":"Cargolux","DHX":"DHL Aviation",
    "UPS":"UPS Airlines","FDX":"FedEx Express","GEC":"Lufthansa Cargo",
    "EWG":"Eurowings","SCW":"Scandinavian","AFG":"Ariana Afghan",
    "CPA":"Cathay Pacific","ANA":"All Nippon Airways","JAL":"Japan Airlines",
    "CSN":"China Southern","CCA":"Air China","CES":"China Eastern",
    "SVR":"Silver Air","BCS":"European Air Charter",
}


# ── DATABASE ──────────────────────────────────────────────────────────────────

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS sightings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                icao       TEXT    NOT NULL,
                callsign   TEXT,
                airline    TEXT,
                date       TEXT    NOT NULL,
                first_seen INTEGER NOT NULL,
                last_seen  INTEGER NOT NULL,
                max_alt    INTEGER DEFAULT 0,
                max_speed  INTEGER DEFAULT 0,
                squawk     TEXT
            )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_date ON sightings(date)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_icao ON sightings(icao)")
        db.commit()


# ── RECORDER ─────────────────────────────────────────────────────────────────

_active      = {}   # icao → entry dict
_active_lock = threading.Lock()


def _airline_from_callsign(cs):
    if not cs or len(cs) < 3:
        return None
    return AIRLINES.get(cs[:3].upper()) or AIRLINES.get(cs[:2].upper())


def recorder_loop():
    while True:
        try:
            _record_tick()
        except Exception as e:
            print(f"[recorder] {e}")
        time.sleep(10)


def _record_tick():
    now = int(time.time() * 1000)
    try:
        with urllib.request.urlopen(FR24_BASE + "/flights.json", timeout=5) as r:
            flights = json.load(r)
    except Exception:
        return

    seen = set(flights.keys())

    with _active_lock:
        for icao, ac in flights.items():
            alt   = ac[F_ALT]   or 0
            speed = ac[F_SPEED] or 0
            cs    = ac[F_CS]    or ""
            sqk   = ac[F_SQK]  or ""
            if icao not in _active:
                _active[icao] = {
                    "callsign":  cs,
                    "airline":   _airline_from_callsign(cs),
                    "first_seen": now,
                    "last_seen":  now,
                    "max_alt":   alt,
                    "max_speed": speed,
                    "squawk":    sqk,
                }
            else:
                e = _active[icao]
                e["last_seen"]  = now
                e["max_alt"]    = max(e["max_alt"],   alt)
                e["max_speed"]  = max(e["max_speed"], speed)
                if cs and not e["callsign"]:
                    e["callsign"] = cs
                    e["airline"]  = _airline_from_callsign(cs)
                if sqk and sqk not in ("0000", "1000"):
                    e["squawk"] = sqk

        # Flush aircraft gone > 60 s
        gone_cutoff = now - 60_000
        to_flush = [
            icao for icao, e in _active.items()
            if e["last_seen"] < gone_cutoff and icao not in seen
        ]
        for icao in to_flush:
            _flush(icao, _active.pop(icao))


def _flush(icao, e):
    date = datetime.fromtimestamp(e["first_seen"] / 1000).strftime("%Y-%m-%d")
    try:
        with sqlite3.connect(DB_PATH) as db:
            db.execute(
                "INSERT INTO sightings "
                "(icao,callsign,airline,date,first_seen,last_seen,max_alt,max_speed,squawk) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (icao, e["callsign"] or None, e["airline"] or None, date,
                 e["first_seen"], e["last_seen"],
                 e["max_alt"], e["max_speed"], e["squawk"] or None))
            db.commit()
    except Exception as ex:
        print(f"[db] flush {icao}: {ex}")


# ── STATS ─────────────────────────────────────────────────────────────────────

def get_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row

        today_total = db.execute(
            "SELECT COUNT(*) n FROM sightings WHERE date=?", (today,)
        ).fetchone()["n"]

        top_callsigns = db.execute(
            "SELECT callsign, COUNT(*) n FROM sightings "
            "WHERE date=? AND callsign IS NOT NULL AND callsign != '' "
            "GROUP BY callsign ORDER BY n DESC LIMIT 10", (today,)
        ).fetchall()

        top_airlines = db.execute(
            "SELECT airline, COUNT(*) n FROM sightings "
            "WHERE date=? AND airline IS NOT NULL "
            "GROUP BY airline ORDER BY n DESC LIMIT 10", (today,)
        ).fetchall()

        rows_today = db.execute(
            "SELECT first_seen FROM sightings WHERE date=?", (today,)
        ).fetchall()
        by_hour = [0] * 24
        for row in rows_today:
            h = datetime.fromtimestamp(row["first_seen"] / 1000).hour
            by_hour[h] += 1

        max_alt_row = db.execute(
            "SELECT icao, callsign, max_alt FROM sightings "
            "WHERE date=? ORDER BY max_alt DESC LIMIT 1", (today,)
        ).fetchone()

        alltime_total = db.execute(
            "SELECT COUNT(*) n FROM sightings"
        ).fetchone()["n"]

        first_date = db.execute(
            "SELECT MIN(date) d FROM sightings"
        ).fetchone()["d"]

        recent = db.execute(
            "SELECT icao,callsign,airline,first_seen,last_seen,max_alt,max_speed,squawk "
            "FROM sightings ORDER BY last_seen DESC LIMIT 50"
        ).fetchall()

        daily = db.execute(
            "SELECT date, COUNT(*) n FROM sightings "
            "WHERE date >= date('now','-30 days') "
            "GROUP BY date ORDER BY date"
        ).fetchall()

    with _active_lock:
        active_count = len(_active)

    return {
        "today": {
            "date":          today,
            "total":         today_total,
            "active":        active_count,
            "top_callsigns": [[r["callsign"], r["n"]] for r in top_callsigns],
            "top_airlines":  [[r["airline"],  r["n"]] for r in top_airlines],
            "by_hour":       by_hour,
            "max_alt":       dict(max_alt_row) if max_alt_row else None,
        },
        "alltime": {
            "total":      alltime_total,
            "first_date": first_date,
        },
        "daily":  [[r["date"], r["n"]] for r in daily],
        "recent": [dict(r) for r in recent],
    }


# ── STATION INFO ────────────────────────────────────────────────────────────

def get_station():
    """Feeder alias (e.g. 'T-EHRD632') from fr24feed's local config.json.

    config.json also contains the fr24key (sharing key) in plain text, so we
    deliberately extract only the alias here instead of proxying it whole.
    """
    try:
        with urllib.request.urlopen(FR24_BASE + "/config.json", timeout=3) as r:
            cfg = json.load(r)
        monitor = cfg.get("monitor", {})
        return {
            "station": monitor.get("feed_alias") or None,
            "status":  monitor.get("feed_status") or None,
        }
    except Exception:
        return {"station": None, "status": None}


# ── HTTP HANDLER ──────────────────────────────────────────────────────────────

class ADSBHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/flights"):
            self._proxy(FR24_BASE + "/flights.json")
        elif self.path.startswith("/api/logs"):
            self._proxy(FR24_BASE + "/logs.bin")
        elif self.path.startswith("/api/stats"):
            self._json(get_stats())
        elif self.path.startswith("/api/station"):
            self._json(get_station())
        else:
            super().do_GET()

    def _proxy(self, url):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
                ct = resp.headers.get("Content-Type", "application/json")
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())

    def _json(self, data):
        body = json.dumps(data, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


# ── MAIN ─────────────────────────────────────────────────────────────────────

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    threading.Thread(target=recorder_loop, daemon=True).start()
    print(f"ADS-B Portal → http://0.0.0.0:{PORT}")
    with ThreadingHTTPServer(("0.0.0.0", PORT), ADSBHandler) as httpd:
        httpd.serve_forever()
