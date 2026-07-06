# Plan: Wetter-Konfiguration nutzbar machen (Follow-up zu REQ-046)

Branch: `feat/weather-config-admin` (von develop, inkl. REQ-046 #403)
Worktree: `~/repos/.worktrees/kamerplanter/weather-config-admin`

## Problem
REQ-046 (#403) gated die Wetterquelle-UI auf `site.type ∈ {outdoor,greenhouse}` && `gps_coordinates != null`,
aber das Standort-Formular kann Typ/GPS gar nicht setzen → Wetterquelle nie erreichbar. Zudem fehlt eine
zentrale Admin-Pflege der öffentlichen Wetterdienste (bisher nur Env-Variablen).

## Scope (2 Teile, 1 PR)
- **A — Standort-Formular:** Typ (SiteType-Select) + GPS (lat/lon) im `SiteCreateDialog` UND im
  `SiteDetailPage`-Edit-Formular. Backend akzeptiert beides schon (`sites/schemas.py:45-46,59-60`).
- **B — Admin-Pflegemaske „Wetterdienste":** system-settings-backed (Env-Fallback wie HA-Settings),
  plattform-admin-geschützt. **Voll inkl. globalem OWM-Fallback-Key** (User bestätigt):
  - Pro Provider (open-meteo/dwd/openweathermap): Ein/Aus + Basis-URL-Override + Verbindungstest.
  - Globaler OpenWeatherMap-Key (Fernet), Fallback wenn Standort keinen eigenen setzt.
  - Fetch-Settings (Timeout, Default-Quelle), Attributionen.
  - Resolver/Adapter lesen **effektive** Config (DB-Override → Env-Fallback); OWM-Key: per-Site → global-Fallback.

## Muster / Anker
- SystemSettings: `SystemSettingsService.get_effective_ha_settings` (DB-Override+Env-Fallback), `SYSTEM_SETTINGS`-Collection.
- Admin-Router + Fernet: `app/api/v1/admin/oidc_providers/router.py` (`require_platform_admin`, `encryption.encrypt`, Masking).
- Effektive Enable-Flags: `WeatherSourceService.available_sources` nutzt aktuell `settings.<p>_enabled` → auf effektiv umstellen.
- Resolver OWM-Key: `WeatherSourceResolver._build` (openweathermap) → globalen Key als Fallback ziehen.
- Attributionen: `data_access/external/weather_attributions.py`.

## Wellen
1. Backend: WeatherSettingsService (system-settings) + Admin-Endpunkte + Resolver/Adapter-Integration + Tests.
2. Frontend: A (Site-Formular Typ+GPS) + B (Admin-Pflegemaske-Seite + Routing/Nav + API) + i18n + Tests.
3. UI-Review + Security-Review → volle Suites → Doku → PR nach develop.

## Invarianten
- English-only Code; i18n DE-default+EN; 5-Layer; ruff (`except … as exc`); tenant vs. platform-admin sauber trennen.
- Globaler OWM-Key nie im Klartext in Response/Log (Fernet, Masking) — SEC-001-Lehre.
- HA/Wetter bleibt optional; Env-Fallback muss ohne DB-Config funktionieren.

## Status / resume anchor
- [x] Worktree angelegt, Scope + Pflegemaske-Design (globaler Key) bestätigt.
- [x] Welle 1 Backend: `WeatherSettingsService` (system-settings, Env-Fallback) + Admin-Endpunkte `/admin/weather-providers` (GET/PUT/test) + globaler OWM-Fallback-Key (Fernet, maskiert) + Resolver/Service auf effektive Config. Verifiziert: ruff clean, 2 Routen, 54 Tests grün.
- [x] Welle 2 Frontend: Site-Formular Typ+GPS (Create+Edit, `siteForm.ts` shared) + Admin-Tab „Wetterdienste" (`WeatherProvidersSettingsTab` in `AccountSettingsPage`, `canManageStorage`-gated) + i18n + Tests. Verifiziert: tsc clean, 16 Tests grün.
- [x] Welle 3 UI-Review (`frontend-usability-optimizer`): Live-Typ-Hinweis (Wetter nur outdoor/greenhouse), Enable-Toggle-Erklärung, Attribution-Label. tsc/eslint/25 Tests grün.
- [x] Welle 3 Security-Review (`code-security-reviewer`): nichts Critical/High. **SEC-W1 (Medium SSRF via operator-base_url) behoben** (`validate_server_side_url` im PUT-Handler, wie HA/Storage-Admin) + SEC-W2 (max_length) + Regressionstest. SEC-W3/W4 = dokumentierte Info (Follow-up). Positiv: Global-Key verlässt Backend nie, Masking/Preserve/AuthZ/Light-Mode/Redaction sauber. Verifiziert: 12 Admin-Tests grün.
- [ ] **← LÄUFT:** volle Suites (Merge-Gate) + MkDocs-Doku.
- [ ] PR nach develop (pull-request-create) — nach Nutzer-Freigabe.
