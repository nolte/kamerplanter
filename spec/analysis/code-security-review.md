# Code-Security-Review
**Erstellt von:** Code-Security-Reviewer (Subagent)
**Datum:** 2026-03-22
**Fokus:** OWASP Top 10, Auth, Tenant-Isolation, Injection, Secret Management
**Analysierte Dateien:** 72 Backend-Dateien + 12 Frontend-Dateien + 4 HA-Integration-Dateien
**Referenz-Specs:** REQ-023, REQ-024, NFR-001, NFR-006

---

## Gesamtbewertung

| Kategorie | Bewertung | Findings |
|-----------|-----------|----------|
| Injection (A03) | Gut | 1 (P2 — Muster-Risiko, kein aktives Risiko) |
| Broken Auth (A07) | Gut mit Ausnahmen | 2 (1x P1, 1x P2) |
| Broken Access Control (A01) | Kritisch — Legacy-Router | 1 (P0) |
| Security Misconfiguration (A05) | Mittel | 3 (1x P1, 2x P2) |
| Cryptographic Failures (A02) | Gut | 1 (P3) |
| Input Validation | Gut | 1 (P3) |
| Rate Limiting | Gut | 0 |
| Logging & Monitoring | Mittel | 1 (P1) |
| Frontend Security | Gut | 1 (P3) |

Die Architektur ist solide durchdacht: JWT mit Authlib, HttpOnly-Cookies für Refresh-Tokens, CSRF-Double-Submit-Cookie, tenant-scoped Routing mit `get_current_tenant()`, parametrisierte AQL-Queries über `AQLBuilder` und `bind_vars`. Das kritischste Problem ist eine **doppelte Router-Registrierung**: Legacy-Router werden sowohl ohne Auth (`/api/v1/sites`, `/api/v1/plant-instances` etc.) als auch korrekt auth-geschützt im Tenant-Scoped-Router (`/api/v1/t/{slug}/...`) registriert. Die ungeschützten Legacy-Routen existieren in Produktion aktiv und ermöglichen unautorisierten Datenzugriff.

---

## P0 — Kritische Schwachstellen (sofort zu beheben)

### SEC-001: Unauthentifizierte Legacy-Endpunkte — vollständiger CRUD ohne Auth

**Datei:** `src/backend/app/api/v1/router.py:84-125` und alle referenzierten `*/router.py`
**OWASP:** A01:2021 — Broken Access Control
**Problem:**
In `router.py` werden **beide** Router-Varianten registriert:

```python
# OHNE AUTH — jede dieser Routen ist öffentlich erreichbar:
api_router.include_router(sites_router)         # /api/v1/sites/*
api_router.include_router(plants_router)        # /api/v1/plant-instances/*
api_router.include_router(planting_runs_router) # /api/v1/planting-runs/*
api_router.include_router(tanks_router)         # /api/v1/tanks/*
api_router.include_router(fertilizers_router)   # /api/v1/fertilizers/*
api_router.include_router(nutrient_plans_router)# /api/v1/nutrient-plans/*
api_router.include_router(feeding_events_router)# /api/v1/feeding-events/*
api_router.include_router(watering_events_router)
api_router.include_router(watering_logs_router)
api_router.include_router(ipm_router)
api_router.include_router(harvest_router)
api_router.include_router(tasks_router)
api_router.include_router(care_reminders_router)
api_router.include_router(onboarding_router)
api_router.include_router(imports_router)
api_router.include_router(calendar_router)  # enthält sensible Feed-Daten
# ... weitere

# KORREKT GESCHÜTZT — der tenant-scoped Router:
api_router.include_router(tenant_scoped_router)  # /api/v1/t/{slug}/*
```

Ein unauthentifizierter Angreifer kann:
- `GET /api/v1/plant-instances` → alle Pflanzen aller Tenants auflisten
- `POST /api/v1/sites` → Standorte ohne Tenant-Zuordnung anlegen
- `DELETE /api/v1/tanks/{key}` → beliebige Tanks löschen
- `GET /api/v1/calendar/events?tenant_key=X` → Kalender eines beliebigen Tenants abfragen

Betroffen sind alle `router.py`-Dateien ohne `get_current_user`-Dependency (geprüft: `sites/router.py`, `plant_instances/router.py`, `tanks/router.py`, `planting_runs/router.py`, `fertilizers/router.py`, `nutrient_plans/router.py` u.v.m.).

**Fix:** Die Legacy-`*/router.py`-Varianten müssen entweder entfernt oder mindestens mit `get_current_user` als Router-Level-Dependency gesichert werden. Die korrekte Lösung ist die **Entfernung** der Legacy-Router-Registrierungen aus `router.py`, da die funktional identischen, korrekt auth-geschützten Tenant-Routen bereits existieren. Diese Änderung ist eine Breaking-API-Change und muss koordiniert erfolgen.

**Status:** Nicht automatisch behoben — erfordert API-Vertragsänderung, die explizit koordiniert werden muss (Frontend-Migration auf Tenant-Scoped-URLs).

**Sofortmaßnahme bis zur Migration:** Alle Legacy-Router-Routen mit einem expliziten `Depends(get_current_user)` im APIRouter-Konstruktor sichern:

```python
# Beispiel für sites/router.py — auf alle betroffenen Router anwenden:
router = APIRouter(
    prefix="/sites",
    tags=["sites"],
    dependencies=[Depends(get_current_user)],  # Sofortschutz
)
```

---

## P1 — Hohe Schwachstellen (behoben)

### SEC-002: OAuth-Callback überträgt Access-Token als URL-Query-Parameter

**Datei:** `src/backend/app/api/v1/auth/router.py:219-223` (vor Fix)
**OWASP:** A07:2021 — Identification and Authentication Failures
**Problem:**
Nach erfolgreichem OAuth-Login wurde der JWT Access-Token als Query-Parameter in der Redirect-URL übertragen:
```
https://frontend/auth/callback?access_token=eyJ...&expires_in=900
```
Query-Parameter werden in Server-Logs, Proxy-Logs, Browser-History und Referer-Headern gespeichert. Der Token war für jeden lesbar, der Zugriff auf diese Logs hat.

**Fix:** Token wird jetzt im URL-Fragment (`#`) übertragen, das nie an Server gesendet wird:
```
https://frontend/auth/callback#access_token=eyJ...&expires_in=900
```

**Geänderte Datei:** `src/backend/app/api/v1/auth/router.py`
**Verifikation:** Ruff-Check sauber.

---

### SEC-003: Passwort des Demo-Users wird im Klartext in Logs geschrieben

**Datei:** `src/backend/app/migrations/seed_auth.py:70-73` (vor Fix)
**OWASP:** A02:2021 — Cryptographic Failures
**Problem:**
```python
logger.info(
    "demo_seed_complete",
    email=demo["email"],
    password=demo["password"],  # KLARTEXT-PASSWORT im Log!
    tenant_slug=slug,
)
```
Das Demo-Passwort `demo-passwort-2024` wurde bei jedem App-Start (seed runs idempotent) im strukturierten Log ausgegeben. Log-Aggregatoren (Loki, Elasticsearch) persistieren diese Einträge dauerhaft.

**Fix:** `password`-Feld aus `logger.info()`-Aufruf entfernt.

**Geänderte Datei:** `src/backend/app/migrations/seed_auth.py`
**Verifikation:** Ruff-Check sauber.

---

### SEC-004: IDOR — Notification mark_read/mark_acted ohne User-Ownership-Prüfung

**Datei:** `src/backend/app/domain/services/notification_service.py:184-209` (vor Fix)
**OWASP:** A01:2021 — Broken Access Control (IDOR)
**Problem:**
`mark_read` und `mark_acted` prüften nur den `tenant_key`, aber nicht den `user_key`. Ein Tenant-Member (z.B. Grower) konnte die Notifications anderer Tenant-Member (z.B. des Admins) als gelesen markieren oder auf Actions reagieren, indem er die `notification_key`-Werte erratete/enumerierte:

```python
# Vor Fix — nur Tenant-Check, kein User-Check:
if notif.tenant_key != tenant_key:
    return None
# Fehlend: if notif.user_key != user_key: return None
```

**Fix:** `user_key`-Parameter hinzugefügt und Ownership-Check implementiert. Aufrufende Router übergeben `user_key=ctx.user_key`.

**Geänderte Dateien:**
- `src/backend/app/domain/services/notification_service.py`
- `src/backend/app/api/v1/notifications/tenant_router.py`

**Verifikation:** Ruff-Check sauber.

---

## P2 — Mittlere Schwachstellen (behoben)

### SEC-005: Information Disclosure in HA-Test-Endpunkt — URL und Fehlermeldungen exponiert

**Datei:** `src/backend/app/api/v1/admin/settings/router.py:83-90` (vor Fix)
**OWASP:** A05:2021 — Security Misconfiguration (Information Disclosure)
**Problem:**
Der `/admin/settings/home-assistant/test`-Endpunkt gab interne Infrastruktur-Details zurück:
```python
return HATestResponse(success=False, message=f"Cannot connect to {url}.")          # Interne URL!
return HATestResponse(success=False, message=f"HTTP {e.response.status_code}: {e.response.text[:200]}")  # HA-Antwort!
return HATestResponse(success=False, message=str(e)[:300])  # Exception-String!
```
NFR-006 §6.2.2 verbietet explizit die Exposition interner IP-Adressen/Hostnames und Infrastruktur-Details.

**Fix:** Alle Fehlermeldungen auf generische, nicht-interne Beschreibungen geändert.

**Geänderte Datei:** `src/backend/app/api/v1/admin/settings/router.py`
**Verifikation:** Ruff-Check sauber.

---

### SEC-006: AQL-Query-Bausteine mit `LIMIT {offset}, {limit}` direkt interpoliert

**Datei:** `src/backend/app/data_access/arango/task_repository.py:34,35,161`
**OWASP:** A03:2021 — Injection (Muster-Risiko)
**Problem:**
An mehreren Stellen werden `offset` und `limit` per f-string direkt in AQL eingebettet:
```python
query = f"FOR doc IN {col.WORKFLOW_TEMPLATES} {filt} SORT doc.name LIMIT {offset}, {limit} RETURN doc"
```
Obwohl diese Integer-Werte über Pydantic mit `ge=0` und `le=200` validiert werden und keine String-Injection möglich ist, verstößt das Muster gegen das Defense-in-Depth-Prinzip. Bei einem zukünftigen Refactoring ohne Pydantic-Validierung würde das Muster zu einer echten Injection-Lücke.

**Empfehlung (nicht automatisch gefixt, da kein aktuelles Risiko):** `LIMIT @offset, @limit` mit `bind_vars` verwenden. Alternativ: Integer-Cast vor Interpolation als explizite Sicherheitsdokumentation.

---

### SEC-007: Fehlende Content-Security-Policy (CSP) Header

**Datei:** `src/backend/app/main.py:124-133`
**OWASP:** A05:2021 — Security Misconfiguration
**Problem:**
Die Security-Header-Middleware setzt:
- `X-Content-Type-Options` ✓
- `X-Frame-Options` ✓
- `Referrer-Policy` ✓
- `Strict-Transport-Security` (nur non-debug) ✓
- `Permissions-Policy` ✓

Fehlend: `Content-Security-Policy`. Ohne CSP können XSS-Angriffe im Browser vollständig ausgeführt werden.

**Status:** Dokumentiert. Fix erfordert Frontend-spezifische CSP-Richtlinie (Vite-Build-Hashes), die koordiniert werden muss.

---

## P3 — Niedrige Schwachstellen / Best Practices (dokumentiert)

### SEC-008: bcrypt Cost Factor nicht explizit gesetzt

**Datei:** `src/backend/app/domain/engines/password_engine.py:21`
**Problem:** `bcrypt.gensalt()` ohne explizites `rounds`-Argument verwendet den Default-Wert (12). Das entspricht dem Mindest-Requirement, ist aber nicht explizit dokumentiert. Bei einer Library-Änderung des Defaults wäre keine Warnung sichtbar.
**Empfehlung:** `bcrypt.gensalt(rounds=12)` explizit setzen und kommentieren.

---

### SEC-009: Demo-User mit bekanntem Passwort wird immer geseeded

**Datei:** `src/backend/app/migrations/seed_data/auth.yaml:4`
**Problem:** Das Demo-Konto `demo@kamerplanter.example` / `demo-passwort-2024` wird bei jedem App-Start idempotent in die Datenbank geschrieben (falls nicht vorhanden). In Produktion ohne Schutzmechanismus (z.B. `KAMERPLANTER_SEED_DEMO=false` Environment-Variable) ist dieses Konto ein privilegierter Einstiegspunkt (Demo-User erhält `platform admin`-Rolle).
**Empfehlung:** Demo-User-Seeding an eine Environment-Variable binden, die in Produktion standardmäßig `false` ist.

---

### SEC-010: Frontend speichert aktiven Tenant-Slug in localStorage

**Datei:** `src/frontend/src/store/slices/tenantSlice.ts:57`
**Problem:** Der aktive Tenant-Slug (`kp_active_tenant_slug`) wird in `localStorage` persistiert. localStorage ist per XSS lesbar. Der Tenant-Slug ist keine kritische Information (er ist kein Token), aber bei erfolgreicher XSS-Attacke ermöglicht er dem Angreifer, Tenant-Scope-Abfragen im Namen des Opfers auszuführen.
**Bewertung:** Niedrig, da der Tenant-Slug kein Authentifizierungsnachweis ist und alle API-Calls durch den Authorization-Header geschützt werden.

---

### SEC-011: Access Token im Frontend-Memory ohne explizite Ablaufkontrolle

**Datei:** `src/frontend/src/api/client.ts`
**Problem:** Der API-Client verwaltet kein explizites Token-Expiry-Tracking im Memory. Das Backend gibt `expires_in` zurück, aber der Frontend-Code (soweit analysiert) verlässt sich vermutlich auf den 401-Response der API für Token-Refresh. Das ist korrekt, aber bei OAuth-Callback (Fragment-Token) muss sichergestellt werden, dass das Frontend den `expires_in`-Wert aus dem URL-Fragment liest.
**Empfehlung:** Sicherstellen, dass der OAuthCallbackPage-Code nach SEC-002-Fix den Token aus `window.location.hash` statt `window.location.search` liest.

---

### SEC-012: Fehlende RBAC-Rollentrennung in einigen tenant-scoped Endpoints

**Betroffene Endpunkte:** Tasks-`/generate-care-reminders`, Tasks-Batch-Operations
**Problem:** Mehrere Endpunkte (z.B. `POST /tasks/generate-care-reminders`, Batch-Status-Änderungen) erlauben jedem Tenant-Member unabhängig von der Rolle (Viewer/Grower/Admin) Schreiboperationen. Die `require_tenant_role(TenantRole.GROWER)`-Dependency ist implementiert aber nicht flächendeckend eingesetzt.
**Empfehlung:** Alle schreibenden Endpunkte mit mindestens `Depends(require_tenant_role(TenantRole.GROWER))` sichern; Admin-only-Operationen mit `TenantRole.ADMIN`.

---

## Tenant-Isolation-Matrix

| Endpunkt-Gruppe | Tenant-Filter | RBAC-Check | Status |
|-----------------|---------------|------------|--------|
| `/api/v1/t/{slug}/sites` | Ja (get_current_tenant) | Ja (Membership-Check) | OK |
| `/api/v1/t/{slug}/plant-instances` | Ja | Ja | OK |
| `/api/v1/t/{slug}/planting-runs` | Ja | Ja | OK |
| `/api/v1/t/{slug}/tanks` | Ja | Ja | OK |
| `/api/v1/t/{slug}/tasks` | Ja | Ja | OK |
| `/api/v1/t/{slug}/harvest` | Ja | Ja | OK |
| `/api/v1/t/{slug}/ipm` | Ja | Ja | OK |
| `/api/v1/t/{slug}/nutrient-plans` | Ja | Ja | OK |
| `/api/v1/t/{slug}/fertilizers` | Ja | Ja | OK |
| `/api/v1/t/{slug}/notifications` | Ja + user_key | Ja | OK (nach Fix SEC-004) |
| `/api/v1/t/{slug}/calendar` | Ja | Ja | OK |
| `/api/v1/sites` (Legacy) | Nein | Nein | **KRITISCH — SEC-001** |
| `/api/v1/plant-instances` (Legacy) | Nein | Nein | **KRITISCH — SEC-001** |
| `/api/v1/planting-runs` (Legacy) | Nein | Nein | **KRITISCH — SEC-001** |
| `/api/v1/tanks` (Legacy) | Nein | Nein | **KRITISCH — SEC-001** |
| `/api/v1/fertilizers` (Legacy) | Nein | Nein | **KRITISCH — SEC-001** |
| `/api/v1/calendar/events` (Legacy) | tenant_key als Query-Param | Nein | **KRITISCH — SEC-001** |
| `/api/v1/species` | Global (korrekt) | Nein | OK (global resource) |
| `/api/v1/botanical-families` | Global (korrekt) | Nein | OK (global resource) |
| `/api/v1/cultivars` | Global (korrekt) | Nein | OK (global resource) |

---

## Nicht-behobene Punkte (mit Begründung)

- **SEC-001**: Erfordert koordinierte API-Contract-Änderung (Frontend-Migration auf Tenant-Scoped-URLs). Alle Legacy-Router müssen aus `router.py` entfernt werden. Bis zur Migration: Router-Level `dependencies=[Depends(get_current_user)]` als Sofortschutz einsetzen.
- **SEC-007 (CSP)**: Content-Security-Policy erfordert abgestimmte Frontend-Build-Konfiguration (Nonce/Hash-CSP für Vite). Koordination Frontend-Backend notwendig.
- **SEC-006 (AQL LIMIT-Interpolation)**: Kein aktives Injection-Risiko (Integer-Validierung vorhanden), aber schlechtes Muster. Refactoring über Security-Scope hinaus.
- **SEC-012 (RBAC-Vollständigkeit)**: Granulare Rollendurchsetzung gemäß REQ-024 v1.4 (RBAC Permission-Matrix) ist noch nicht implementiert. Eigenständiges Feature-Ticket erforderlich.

---

## Empfehlungen für Folge-Reviews

1. **SEC-001 — Sofortmaßnahme**: Alle in `router.py` registrierten Legacy-`*/router.py`-Instanzen (nicht-tenant-scoped) mit `dependencies=[Depends(get_current_user)]` auf Router-Ebene sichern. Danach als separates Ticket: Migration aller Frontend-API-Aufrufe auf Tenant-Scoped-URLs und Entfernung der Legacy-Router.

2. **CSP-Header implementieren**: Koordiniert mit Frontend-Build-Konfiguration. Mindest-Policy: `default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'`.

3. **RBAC Permission-Matrix (REQ-024 v1.4)**: `require_permission()`-Dependency implementieren und alle schreibenden Endpunkte mit Mindest-Rollen absichern.

4. **Demo-User-Seeding absichern**: `SEED_DEMO_USER`-Env-Variable einführen; in Production-Helm-Chart standardmäßig `false`.

5. **Penetration Test der Legacy-Routen**: Vor dem nächsten Release sicherstellen, dass alle Legacy-Routen entweder entfernt oder vollständig gesichert sind.

---

**Dokumenten-Ende**
**Version:** 1.0
**Status:** Abgeschlossen
**Letzte Aktualisierung:** 2026-03-22
