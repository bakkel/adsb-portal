# Changelog

## 2026-09-04
- Added an MIT `LICENSE`, now that the repository is public.
- Added a footer link to the GitHub repo on all pages, and made the repository public.
- Rewrote git history to permanently remove `CLAUDE.md` and `adsb-receiver-piaware5.md` from all past commits (they had only been untracked going forward, not purged from history) — required before making the repo public, since those files contained a real FR24 sharing key, FlightAware feeder/site ID, GPS location and SSH details. History was force-pushed; commit hashes changed as a result.
- Added an alternative Docker deployment: `Dockerfile` + `docker-compose.yml` (host networking, so the container reaches `fr24feed` on `localhost:8754` without extra config) plus a `.dockerignore` that excludes the private infra notes. `server.py` now reads `PORT`, `FR24_BASE` and `DB_PATH` from environment variables (falling back to the existing defaults), so the same script runs unchanged on bare metal or in a container. This does not replace the existing systemd/rsync deployment — it's offered as an option for self-hosters who prefer Docker.
- Translated the entire project (UI, README, changelog) to English and removed personal branding, in preparation for making the repository public on GitHub.
- Renamed the portal from "FR24 Portal" to "ADS-B Portal" throughout the UI. The home page header now shows the feeder's own alias (e.g. `T-EHRD632`), fetched live from a new `GET /api/station` endpoint that reads `fr24feed`'s local `config.json` — only the alias is exposed server-side, the sharing key is never proxied to the client.
- Merged the landing page into the map page — `portal.html` is now `index.html` and serves as the home page; the separate landing page was removed.
- `CLAUDE.md` and `adsb-receiver-piaware5.md` (personal infrastructure notes: IP, SSH port, FR24 sharing key, FlightAware feeder/site ID, GPS location) are no longer tracked in git and excluded from `deploy.sh`.
- Project split off from the combined "FR24 Portal + Space Tracker" setup (previously the `Flightradar24` repo). This project now contains only the ADS-B aircraft portal (map, statistics, squawk codes) — the space section moved to the separate `space-tracker` project.
- Deployment switched from cron-based `git pull` on the Pi to a local `deploy.sh` script (`rsync` over SSH via the `flight2` alias) that restarts the service.
- Cross-links to the space-tracker pages removed from `stats.html` and `squawk.html`.
