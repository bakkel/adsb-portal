# Changelog

## 2026-09-04
- Translated the entire project (UI, README, changelog) to English and removed personal branding, in preparation for making the repository public on GitHub.
- Renamed the portal from "FR24 Portal" to "ADS-B Portal" throughout the UI. The home page header now shows the feeder's own alias (e.g. `T-EHRD632`), fetched live from a new `GET /api/station` endpoint that reads `fr24feed`'s local `config.json` — only the alias is exposed server-side, the sharing key is never proxied to the client.
- Merged the landing page into the map page — `portal.html` is now `index.html` and serves as the home page; the separate landing page was removed.
- `CLAUDE.md` and `adsb-receiver-piaware5.md` (personal infrastructure notes: IP, SSH port, FR24 sharing key, FlightAware feeder/site ID, GPS location) are no longer tracked in git and excluded from `deploy.sh`.
- Project split off from the combined "FR24 Portal + Space Tracker" setup (previously the `Flightradar24` repo). This project now contains only the ADS-B aircraft portal (map, statistics, squawk codes) — the space section moved to the separate `space-tracker` project.
- Deployment switched from cron-based `git pull` on the Pi to a local `deploy.sh` script (`rsync` over SSH via the `flight2` alias) that restarts the service.
- Cross-links to the space-tracker pages removed from `stats.html` and `squawk.html`.
