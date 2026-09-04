# Changelog

## 2026-09-04
- Project losgekoppeld van de gecombineerde "FR24 Portal + Space Tracker" opzet (voorheen `Flightradar24`-repo). Dit project bevat voortaan alleen de ADS-B vliegtuigportal (kaart, statistieken, squawk codes) — het ruimtevaart-gedeelte is verhuisd naar het aparte `space-tracker`-project.
- Deployment omgezet van cron-based `git pull` op de Pi naar een lokaal `deploy.sh`-script (`rsync` over SSH via de `flight2`-alias) dat de service herstart.
- Kruislinks naar de space-tracker-pagina's verwijderd uit `stats.html` en `squawk.html`.
