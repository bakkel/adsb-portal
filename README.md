# ADS-B Portal

A self-hosted web portal for your own ADS-B receiver on a Raspberry Pi. Shows live aircraft positions on an interactive map based on local ADS-B data.

## Features

- **Live map** (`index.html`) — Leaflet.js with Esri World Dark Gray Canvas tiles, aircraft icons with rotation, colored by altitude
- **Station badge** — the header automatically shows your feeder's alias (e.g. `T-EHRD632`), read from `fr24feed`'s local `config.json` via `/api/station`. Only the alias is exposed — the sharing key never leaves the server.
- **Altitude filter** — legend bands are clickable toggles; show/hide aircraft per altitude band on the map and table; "↺ All" resets; collapsed by default on mobile
- **10-minute trails** — position history as polylines per aircraft
- **Aircraft table** — columns: Callsign · ICAO · Airline · Altitude (meters); click to open the popup on the map
- **Popup** — callsign (link → flightradar24.com), ICAO, airline, altitude (m), speed (km/h), heading, squawk (clickable)
- **Squawk codes page** (`squawk.html`) — explains emergency, VFR, IFR and military codes; popup links directly to the matching code
- **Airport markers** — nearby airports with a toggle button (defaults to Dutch/Belgian airports — edit the `AIRPORTS` list in `index.html` for your own region)
- **Emergency squawk highlighting** — 7700 / 7600 / 7500 highlighted in red on the map and table
- **SQLite recorder** — every sighting stored with max altitude, max speed, callsign and airline
- **Statistics page** (`stats.html`) — flights per hour, 30-day trend, top callsigns/airlines, recent flights (Chart.js)
- **Feed status bar** — last 5 lines from the FR24 feeder systemd journal
- **PWA** — installable as a home screen app on iPhone; full screen, dark status bar
- **Mobile-friendly** — responsive layout, compact legend

## Architecture

```
Raspberry Pi
├── fr24feed (official FR24 feeder)      :8754  ← ADS-B receiver data
├── server.py (this portal)              :8081  ← serves the portal
│   ├── GET /api/flights  → proxy to :8754/flights.json
│   ├── GET /api/logs     → proxy to :8754/logs.bin
│   ├── GET /api/stats    → SQLite aggregates
│   └── GET /api/station  → feeder alias (e.g. "T-EHRD632") from :8754/config.json
└── fr24portal.db         (SQLite, created automatically)
```

The portal is served as static HTML from `static/` by a lightweight Python HTTP server. No frameworks, no build step.

## Requirements

- Raspberry Pi with the official FR24 feeder (`fr24feed`) on port 8754
- Python 3.7+

## Installation

```bash
git clone <repo-url> adsb-portal
cd adsb-portal
```

### Systemd service

```bash
sudo cp adsb-portal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable adsb-portal
sudo systemctl start adsb-portal
```

Edit the `User` and `WorkingDirectory` in `adsb-portal.service` to match your own system user and install path first.

### Deployment

`deploy.sh` syncs this project to the Pi via `rsync` over SSH and restarts the service:

```bash
./deploy.sh
```

Adjust `REMOTE`, `REMOTE_DIR` and `SERVICE` at the top of the script to match your own setup.

### Docker (alternative)

Instead of the systemd service, you can run the portal in a container:

```bash
docker compose up -d --build
```

This uses `network_mode: host`, so the container can reach `fr24feed` at `http://localhost:8754` on the same machine without extra network configuration — the same reason `fr24feed` itself isn't containerized: it needs direct USB SDR access. The SQLite database is persisted to `./data/fr24portal.db` via a bind mount.

## Configuration

At the top of `server.py` (or as environment variables, e.g. in `docker-compose.yml`):

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8081` | Port the portal listens on |
| `FR24_BASE` | `http://localhost:8754` | Local FR24 feeder address |
| `DB_PATH` | `<project dir>/fr24portal.db` | SQLite database location (`/data/fr24portal.db` in the Docker image) |

Map center and zoom are set at the top of `static/index.html`:

```javascript
const MAP_CENTER = [51.8133, 4.6903]; // ← your station location [lat, lon]
const MAP_ZOOM   = 8;                 // ← initial zoom level
```

## Data format

The FR24 feeder exposes aircraft as a JSON object, keyed by ICAO hex. Each value is an array:

```
[icao, lat, lon, track, alt_ft, speed_kts, squawk, ?, ?, ?, unix_ts, ?, ?, ?, on_ground, vrate_fpm, callsign]
 [0]   [1]  [2]  [3]    [4]     [5]        [6]                        [10]              [14]       [15]      [16]
```

## Project structure

```
adsb-portal/
├── server.py               Python HTTP server + SQLite recorder
├── adsb-portal.service      systemd unit file
├── deploy.sh               rsync-over-SSH deploy to the Pi
├── Dockerfile              Container image for the portal (alternative to systemd)
├── docker-compose.yml      Runs the portal via Docker with network_mode: host
├── static/
│   ├── index.html          Live map (home page: map + table + popup + altitude filter + feed log)
│   ├── stats.html          Statistics dashboard (Chart.js)
│   ├── squawk.html         Squawk code explanations
│   ├── manifest.json       PWA manifest (home screen app)
│   ├── icon-180.png        Apple touch icon
│   ├── icon-192.png        PWA icon
│   └── icon-512.png        PWA icon (large)
└── fr24portal.db           SQLite database (created automatically, not in repo)
```

## Usage

Open `http://<pi-ip>:8081` in a browser for the live map. Click an aircraft on the map or in the table to open a detail popup. The statistics page is available at `/stats.html`.

### Installing as an iPhone app (PWA)

1. Open the portal in **Safari** on your iPhone
2. Tap the **share icon** (↑) → **"Add to Home Screen"**
3. Confirm — the portal now appears as a full-screen app on your home screen

## License

MIT — see [LICENSE](LICENSE).
