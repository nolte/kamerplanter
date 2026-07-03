# Umsetzungspläne — Fable-5-Code-Review (Juli 2026)

Detaillierte, **am echten Code verankerte** Implementierungspläne zu den Arbeitspaketen aus
[`../code-review-fable5-2026-07.md`](../code-review-fable5-2026-07.md). Jeder Plan enthält
Ziel + Anforderungsbezug, Root-Cause mit `file:line`, Lösungsdesign, konkrete Datei-Änderungen
(vorher/nachher), Testplan (konkrete Testdateien + Fälle), Akzeptanzkriterien, PR-Schnitt und Risiko.

Erstellt von sechs parallelen Fable-5-Agenten, die die zitierten Dateien vor dem Planen gelesen
und verifiziert haben — daher enthalten die Pläne mehrere **Befund-Korrekturen** gegenüber dem
Review-Report (unten markiert).

## Plandateien

| Datei | APs | Prio | Aufwand | Inhalt |
|-------|-----|------|---------|--------|
| [AP-01-datetime-hardening.md](AP-01-datetime-hardening.md) | AP-1 | 🔴 P0 | ~0,5 PT | tz-Bug in Karenz/Resistance/HST → `common/datetimes.py` (`now_utc`/`ensure_aware_utc`), Regressionstests 500→422 |
| [AP-02-03-13-backend-gaps.md](AP-02-03-13-backend-gaps.md) | AP-2/3/13 | 🟠 P1/P2 | S+S+M | DSGVO-Export-Dispatch + Redispatch-Safety-Net + Retry; `species_key`/`quantity`/`id_prefix`-Placeholder-Fix + Species-Edge-Sync; E-Mail-Digest real |
| [AP-04-05-06-08-09-19-security.md](AP-04-05-06-08-09-19-security.md) | AP-4/5/6/8/9/19 | 🟠🟡 P1/P2/P3 | M je | Microservice-Auth + Fail-Fast; `validate_ha_url` (SSRF, LAN-tauglich); JWT-Allowlist+type-Claim; Tenant-Isolation erzwingen; NetworkPolicy-Restlücken; SHA-Pin + RAG-Delimiter |
| [AP-07-12-14-16-20-frontend.md](AP-07-12-14-16-20-frontend.md) | AP-7/12/14/16/20 | 🟠🟡🟢 | M/M/S/M/L | OAuth frontend-first auf Cookie-Flow; `useAsyncOptions`/`resolveOrigin`/Attrappen; useMemo-Pflicht; i18n + `createListSlice`; Detail-Seiten-Zerlegung |
| [AP-10-11-nutrient-domain.md](AP-10-11-nutrient-domain.md) | AP-10/11 | 🟡 P2 | M | `EcBudgetCalculator` als Referenz, `NutrientSolutionCalculator` löschen; `fertilizer_classification.py` (CalMag); `AreaDosingCalculator` (g/m²) |
| [AP-15-17-18-backend-refactoring.md](AP-15-17-18-backend-refactoring.md) | AP-15/17/18 | 🟡🟢 P2/P3 | L | Generische `BaseArangoRepository[TModel]` (8-PR-Migration); `PaginationParams` + LIMIT-bind_vars; `to_response`/`run_async_task`/`kp_vectordb` |
| [AP-21-audit-hygiene.md](AP-21-audit-hygiene.md) | AP-21 | 📋 | S | REQ-014/015-DRIFTs schließen; Coverage-Audit-Warnbox ausweiten |

## Empfohlene Reihenfolge
1. **AP-1** (P0, isolierter PR) — höchstes Nutzer-Risiko, klein.
2. **AP-2 + AP-3** (DSGVO/Datenintegrität, je S).
3. **AP-4 + AP-5 + AP-6** (Security-Bündel) vor nächstem Prod-Deploy; **AP-7** parallel.
4. P2 nach Kapazität; **AP-15** als Refactoring-Fundament früh, da es spätere APs verkleinert.
5. **AP-21** jederzeit (reine Doku).

## Befund-Korrekturen aus der Code-Verifikation
Beim code-nahen Planen haben sich einige Report-Annahmen präzisiert — bei Umsetzung diese
Fassung nutzen:

- **AP-9 (NetworkPolicies):** existieren **bereits** per-Controller (`helm/kamerplanter/values.yaml:991-1355`).
  Echte Restlücken: Default-Deny-Baseline, Valkey-Ingress, fehlender `169.254.0.0/16`-except beim celery-worker.
- **AP-5 (SSRF):** `validate_server_side_url` erzwingt https + Public-IP → für LAN-HA (http/RFC1918) zu strikt.
  Plan führt `validate_ha_url` mit opt-in-Private-Modus ein (Metadata-Range bleibt hart geblockt).
- **AP-7 (OAuth):** Backend setzt das HttpOnly-Refresh-Cookie im Callback **schon** (`auth/router.py:196-229`);
  Fix ist frontend-first auf `refreshAccessToken()`, Backend-Fragment-Entfernung als rückwärtskompatibler Zusatz.
- **AP-3:** Placeholder-Defaults betreffen auch `quantity=1`/`id_prefix="XX"`; Species-Edge wird bei
  Entry-Updates nie nachgezogen; Test `test_placeholder_returns_zero` zementiert das No-Op und muss ersetzt werden.
- **AP-12:** origin-TODO ist 9-fach (nicht 8); stumme `catch(()=>{})` sind 101 (Pilot: 15 Options-Lader);
  `ErrorDisplay.translateError` existiert bereits als Regex-Fallback (darauf aufbauen).
- **AP-15/17/18:** `app/common/pagination.py` und `async_bridge.run_async` existieren bereits ungenutzt
  (Anker für AP-17/18); der `AQLBuilder` selbst interpoliert `LIMIT` per f-String (SEC-B5 betrifft ihn auch);
  vectordb-Repositories sind fachlich verschieden — dedupliziert wird nur die Infrastrukturschicht.
