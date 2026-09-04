# ADS-B Portal

Een zelfgehoste webportal voor je eigen ADS-B ontvanger op een Raspberry Pi. Toont live vliegtuigposities op een interactieve kaart op basis van lokale ADS-B data.

## Functionaliteiten

- **Live kaart** (`portal.html`) — Leaflet.js met Esri World Dark Gray Canvas tiles, vliegtuigpictogrammen met rotatie, gekleurd per hoogte
- **Hoogte filter** — legendabanden zijn klikbare toggles; verberg/toon vliegtuigen per hoogtebereik op kaart en tabel; "↺ Alles" reset; op mobiel standaard ingeklapt
- **10-minuten trails** — positiegeschiedenis als polylijnen per vliegtuig
- **Vliegtuigtabel** — kolommen: Callsign · ICAO · Airline · Hoogte (meters); klik om het popup op de kaart te openen
- **Popup** — callsign (link → flightradar24.com), ICAO, airline, hoogte (m), snelheid (km/u), koers, squawk (klikbaar)
- **Squawk codes pagina** (`squawk.html`) — uitleg over nood-, VFR-, IFR- en militaire codes; popup linkt direct naar de juiste code
- **Vliegveld markeringen** — NL/BE vliegvelden met toggle-knop
- **Nood squawk markering** — 7700 / 7600 / 7500 rood gemarkeerd op kaart en tabel
- **SQLite recorder** — elke waarneming opgeslagen met max hoogte, max snelheid, callsign en airline
- **Statistiekenpagina** (`stats.html`) — vluchten per uur, 30-daagse trend, top callsigns/airlines, recente vluchten (Chart.js)
- **Feed statusbalk** — laatste 5 regels uit het FR24 feeder systemd journal
- **PWA** — installeerbaar als home screen app op iPhone; full screen, dark statusbalk
- **Mobielvriendelijk** — responsieve layout, compacte legenda

## Architectuur

```
Raspberry Pi
├── fr24feed (officiële FR24 feeder)     :8754  ← ADS-B ontvanger data
├── server.py (deze portal)              :8081  ← serveert de portal
│   ├── GET /api/flights  → proxy naar :8754/flights.json
│   ├── GET /api/logs     → proxy naar :8754/logs.bin
│   └── GET /api/stats    → SQLite aggregaten
└── fr24portal.db         (SQLite, automatisch aangemaakt)
```

De portal wordt geserveerd als statische HTML vanuit `static/` met een lichtgewicht Python HTTP server. Geen frameworks, geen build stap.

## Vereisten

- Raspberry Pi met de officiële FR24 feeder (`fr24feed`) op poort 8754
- Python 3.7+

## Installatie

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

### Deployment

`deploy.sh` synct dit project via `rsync` over SSH naar de Pi en herstart de service:

```bash
./deploy.sh
```

Pas `REMOTE`, `REMOTE_DIR` en `SERVICE` bovenaan het script aan naar je eigen situatie.

## Configuratie

Bovenaan `server.py`:

| Variabele | Standaard | Beschrijving |
|---|---|---|
| `PORT` | `8081` | Poort waarop de portal luistert |
| `FR24_BASE` | `http://localhost:8754` | Lokaal FR24 feeder adres |

Kaartcentrum en zoom staan bovenaan `static/portal.html`:

```javascript
const MAP_CENTER = [51.8133, 4.6903]; // ← locatie van je station [lat, lon]
const MAP_ZOOM   = 8;                 // ← startzoommiveau
```

## Dataformaat

De FR24 feeder stelt vliegtuigen beschikbaar als JSON object, gekeyed op ICAO hex. Elke waarde is een array:

```
[icao, lat, lon, track, alt_ft, speed_kts, squawk, ?, ?, ?, unix_ts, ?, ?, ?, on_ground, vrate_fpm, callsign]
 [0]   [1]  [2]  [3]    [4]     [5]        [6]                        [10]              [14]       [15]      [16]
```

## Bestandsstructuur

```
adsb-portal/
├── server.py               Python HTTP server + SQLite recorder
├── adsb-portal.service      systemd unit bestand
├── deploy.sh               rsync-over-SSH deploy naar de Pi
├── static/
│   ├── index.html          Landingspagina
│   ├── portal.html         Live kaart (kaart + tabel + popup + hoogte filter + feed log)
│   ├── stats.html          Statistieken dashboard (Chart.js)
│   ├── squawk.html         Uitleg squawk codes
│   ├── manifest.json       PWA manifest (home screen app)
│   ├── icon-180.png        Apple touch icon
│   ├── icon-192.png        PWA icon
│   └── icon-512.png        PWA icon (groot)
└── fr24portal.db           SQLite database (automatisch aangemaakt, niet in repo)
```

## Gebruik

Open `http://<pi-ip>:8081` in een browser voor de landingspagina, of direct `/portal.html` voor de kaart. Klik op een vliegtuig op de kaart of in de tabel om een detailpopup te openen. De statistiekenpagina is bereikbaar via `/stats.html`.

### Installeren als iPhone app (PWA)

1. Open de portal in **Safari** op je iPhone
2. Tik op het **deelicoon** (↑) → **"Zet op beginscherm"**
3. Bevestig — de portal verschijnt als volledig scherm app op je beginscherm
