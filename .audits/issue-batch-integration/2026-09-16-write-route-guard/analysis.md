# Gruppe `2026-09-16-write-route-guard`

Status: freigegeben 2026-09-16 · Scheibe 1 verifiziert und gemergt · Scheibe 2 in Arbeit

Gemessen gegen `origin/develop` @ `234a032bf` (2026-09-16).

## Die Frage, auf die die Research-Phase gescoped war

Entscheidet der Write-Route-Sweep aus dem, was ein Handler tatsächlich persistiert —
und wenn nein, welche Route hat diese Lücke bereits benutzt?

## Die eine logische Änderung

Der Write-Route-Sweep entscheidet aus dem, was ein Handler tatsächlich persistiert,
statt aus Methodenname und Allowlist-Prosa — und die eine Route, deren Prosa ein nicht
existierendes Gate behauptete, bekommt es.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1441** | `bug`, `security`, `backend` | geteilte Berührungsfläche | `src/backend/tests/unit/api/test_write_route_gates.py:143-149` trägt den Allowlist-Eintrag `notifications.tenant_router.mark_acted`, dessen Begründung repariert werden muss |
| **#1443** | `backend`, `test` | geteilte Berührungsfläche | `src/backend/tests/unit/api/test_write_route_gates.py:42-60` trägt `WRITE_METHODS` samt Kommentar, der die Lücke selbst benennt |

Beide Fixes ändern **dieselbe Datei** — #1443 ihren Detektor, #1441 den Eintrag, den
dieser Detektor künftig überflüssig machen soll. Das ist geteilte Berührungsfläche im
Sinne von §A, nicht ein gemeinsames Zeitfenster.

## Was gemessen wurde, und wo der Issue-Text danebenliegt

### #1441 — die Begründung ist Prosa, die nichts prüft

`grep -n "require_" src/backend/app/api/v1/notifications/tenant_router.py` liefert
**null Treffer**. Jede der 14 Routen der Datei hängt allein an
`get_current_tenant` (`:26`, und je Route `:77 :104 :124 :147 :193 :215 :251 :275 :311
:320 :337`) — das prüft Mitgliedschaft, nicht Rang.

`mark_acted` (`:144`) erreicht bei einer `care.*`-Notification mit Bestätigungs-Aktion
`care_service.confirm_reminder(...)` (`:173`), was eine `CareConfirmation` und einen
`WateringLog` erzeugt. Die direkte Route dafür,
`src/backend/app/api/v1/watering_logs/tenant_router.py:57`, ist mit
`require_permission('watering-log', CREATE)` gegatet.

**Ein Viewer, der eine Pflege-Benachrichtigung erhält, kann sie also mit einem Tipp
bestätigen und erzeugt genau die Schreibvorgänge, die ihm auf dem direkten Weg
verweigert werden.**

Der Allowlist-Eintrag in `test_write_route_gates.py:145-149` behauptet wörtlich:

> „That branch is gated inline on the domain role"

Diese Aussage ist unwahr und war es immer. Sie ist der Grund, warum der Sweep die Route
für geprüft hält. Entgegen der Erwartung im Issue-Text hat PR #1440 sie **nicht**
korrigiert.

**Frontend-Hälfte, im Issue nicht erwähnt:**
`src/frontend/src/components/layout/NotificationDrawer.tsx:36` liest
`notification.actions?.[0]` und rendert den Button ohne jede Rollenprüfung — die Datei
ruft `useTenantPermissions` überhaupt nicht auf. Ein Viewer bekommt den Knopf also
angeboten. Dieselbe Form wie #1425, andere Komponente.

### #1443 — die Quelle ist repariert, der Detektor fehlt

`WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}`
(`test_write_route_gates.py:60`). Ein `GET`, der persistiert, ist für diesen Sweep
unsichtbar.

Der Kommentar darüber (`:42-59`) benennt das selbst und nennt die zwei Routen, die es
bereits gab: `GET /care-reminders/plants/{key}/profile` und
`GET /t/{slug}/care-reminders/dashboard`, beide erreichten `get_or_create_profile`.
Beide sind an der Quelle repariert (`care_reminder_service.py:255-281` — `may_create`
keyword-only ohne Default, und `:1070-1080`), der Detektor fehlt weiterhin.

**Abweichung vom Issue-Text:** Das Issue nennt als Option 3 eine lokale
`READ_ONLY_ROUTES`-Tabelle „nach dem Vorbild in derselben Datei". Ein solches Vorbild
existiert dort **nicht** — die Datei trägt nur `_TENANT_ALLOWLIST`. Wer Option 3 wählt,
baut sie neu, statt einem Muster zu folgen.

## Strukturbefund über die Mitglieder hinweg (§E)

**Klassifikation: Klassen-Cluster.** Defektklasse: *ein Wächter modelliert eine Form
und schließt stillschweigend eine andere aus* — dieselbe Klasse wie #948 und #1042.
Bei #1443 ist die ausgeschlossene Form die schreibende `GET`; bei #1441 die
Ausnahmebegründung, die sich selbst zertifiziert, ohne dass etwas sie prüft.

Der Sweep hat damit **zwei** Wege, an einer ungegateten Schreibroute vorbeizulaufen.
#1402 hat den ersten teilweise geschlossen (Selektorbreite); der zweite — eine
Freitext-Begründung, die niemand gegen den Code hält — ist hier zum ersten Mal
gemessen.

### Prozessbefund (§E), eigenes Issue

Über die zehn Nachzügler-Issues hinweg zeigt sich ein wiederkehrendes Muster: **ein
erkannter Defekt wird im Code kommentiert statt behoben oder an einen Guard gebunden.**

| Fundstelle | Selbst-Widerruf |
|---|---|
| `test_write_route_gates.py:42-59` | „that detector does not exist yet" |
| `app/migrations/migrate_photo_refs.py:55` | „This module's central premise is false" |
| `src/frontend/src/components/common/PhotoUpload.tsx:190` | „Known limitation" |
| `.github/workflows/backend.yml:204` | „deliberately still absent" |

**Vorbeugende Änderung:** eine Regel, die einen solchen Selbst-Widerruf im Code an einen
**roten Guard** bindet statt nur an eine Issue-Nummer — etwa ein Marker
(`# SELF-REVOKED: #NNNN`), den eine Lane zählt und die rot wird, wenn ein Marker ohne
offenes Issue oder ohne fehlschlagenden `xfail` existiert.

Dieser Befund gilt **nicht** als erledigt, wenn #1441 und #1443 repariert sind. Er ist
als **#1456** gegen `spec/project/defect-class-guards/` angelegt, mit Verweis auf diese
Gruppen-Id, und speist die Klasse in den `continuous-improvement`-Loop.

## Stufe und Scheiben

**Stufe 3** nach `spec/claude/research-plan-implement/` — die Gruppe ändert eine
Autorisierungsgrenze, also einen veröffentlichten Vertrag.

Damit gelten beide Stufe-3-Pflichten:

**Designentscheidung (das *Wo*, vor dem *Wie*)** — offen, siehe unten. Sie wird vom
Operator entschieden, bevor der Plan das Wie beschreibt.

**Unabhängig verifizierbare Scheiben:** die Mitgliedsreihenfolge. Scheibe 1 ist #1441
mit grünen erklärten Prüfungen, Scheibe 2 ist #1443.

**Verifikationsdurchgang durch einen fremden Kontext:** `security-review` gegen den
Kopf des Integrationsbranches, ausgeführt **aus dem Worktree**, nach beiden Mitgliedern.

## Modus

**Modus B — Sub-Branch je Mitglied.** Begründung: #1441 ist ein `security`-Mitglied,
dessen Fixform von einem noch ausstehenden `security-review` abgelehnt werden kann.
Modus B macht es durch Fallenlassen eines einzigen Merges herauslösbar.

Bekannter Preis: beide Mitglieder fassen `test_write_route_gates.py` an, und
`references/mode-gate.md` hält fest, dass Modus B bei überlappender Fläche
Merge-Konflikte herstellt statt sie zu vermeiden. Hier ist der Preis gering, weil die
Regionen disjunkt sind — #1441 der Allowlist-Eintrag (`:143-149`), #1443 `WRITE_METHODS`
und sein Kommentar (`:42-60`).

## Reihenfolge

1. **#1441** — die offene Autorisierungslücke zuerst; sie ist ausnutzbar, solange sie offen ist.
2. **#1443** — der Detektor danach, weil er die Allowlist-Einträge messbar macht, die #1441 hinterlässt.

Ergebnis von #1441 wird festgehalten, bevor #1443 startet.

## Vollständigkeitsmatrix

Spalten abgeleitet aus dem Repository: `src/backend/pyproject.toml` und
`src/frontend/package.json` (Quellcode), `spec/`-Baum (Spec), `src/backend/tests/` +
`src/frontend/src/test/` (Tests), `mkdocs.yml` + `docs/` (Doku), `.github/workflows/` +
`.taskfiles/` (Config), `docs/catalog-sources.yml` → `scripts/docs/gen_catalog.py`
(generierter Katalog).

| Mitglied | Backend-Quellcode | Frontend-Quellcode | Spec | Tests | Doku | Config / Workflows | Generierter Katalog |
|---|---|---|---|---|---|---|---|
| **#1441** | `notifications/tenant_router.py:144` — Rangprüfung vor dem `confirm_reminder`-Zweig; Prüfung: `pytest src/backend/tests/unit/api/test_write_route_gates.py` | `NotificationDrawer.tsx:36` — Aktionsknopf an `useTenantPermissions().canEdit` binden; Prüfung: `vitest run src/frontend/src/test/components/NotificationDrawer*` | `spec/req/REQ-030.md` §4.2 — Rangbedingung der Bestätigungs-Aktion ergänzen; Prüfung: `pre-commit run check-section-refs` | neuer Negativtest „Viewer erhält 403 auf `POST …/act` mit Bestätigungs-Aktion"; Prüfung: derselbe pytest-Lauf | *nicht zutreffend* — keine Endnutzerseite beschreibt diese Route | *nicht zutreffend* — keine Lane ändert sich | *nicht zutreffend* — kein `.claude/`-Artefakt berührt |
| **#1443** | *nicht zutreffend* — Quelle ist bereits repariert (`care_reminder_service.py:255-281`) | *nicht zutreffend* — reiner Backend-Wächter | *nicht zutreffend* — kein Spec-Topic regelt den Detektor | `test_write_route_gates.py:42-60` — Entscheidung aus dem Aufrufgraph statt aus der Methode, **plus** Selbsttest, der eine künstliche schreibende `GET` rot macht; Prüfung: der Selbsttest muss gegen den heutigen Stand **rot** sein, bevor er grün wird | *nicht zutreffend* — internes Testwerkzeug | *nicht zutreffend* — läuft in der bestehenden `backend-guards`-Lane | *nicht zutreffend* — kein `.claude/`-Artefakt berührt |

## Risiken

- **Der Detektor aus #1443 ist selbst driftanfällig** — er ist ein Wächter über Wächter. Ohne einen Selbsttest, der ihn gegen eine künstlich eingebaute schreibende `GET` laufen lässt, zertifiziert er sich genauso selbst wie die Prosa, die er ersetzt. Der Selbsttest ist deshalb Pflicht, nicht Kür, und er muss **zuerst rot** sein.
- **Ein Aufrufgraph-Detektor kann falsch-positiv werden** und Leserouten röten, die nur zufällig einen schreibenden Helfer erwähnen. Gegenmaßnahme: Lauf gegen den vollständigen heutigen Routenbestand, jeder neue Treffer wird einzeln bewertet, bevor die Lane scharf geht.
- **#1441s Rangwahl ist eine Designfrage, keine Implementierungsfrage** (siehe offene Fragen). Eine falsche Wahl bricht entweder einen legitimen Nutzungspfad oder lässt die Lücke offen.

## Bewusst außerhalb des Scopes

- Der per-User-Zustand von `mark_acted` (gelesen/acted stempeln) bleibt für **jedes** Mitglied erreichbar, auch für einen Viewer. Nur der Zweig, der eine `CareConfirmation` und einen `WateringLog` erzeugt, bekommt eine Rangbedingung.
- Die übrigen 13 Routen in `notifications/tenant_router.py` werden **nicht** gegatet; sie tragen per-User-Zustand, und der Allowlist-Eintrag dafür ist zutreffend.
- #1425 (Galerie-Delete im Frontend) hat dieselbe Form, ist aber eine andere Komponente und ein anderes Prädikat — Einzellauf, nicht Mitglied dieser Gruppe.
- Die übrigen Allowlist-Einträge werden **nicht** gegen den Code geprüft. Dass #1441s Eintrag unwahr war, legt nahe, dass andere es auch sind; das ist ein eigener Sweep und ein eigenes Issue, sobald #1443s Detektor existiert.

## Operator-Entscheidungen (2026-09-16, vor der Umsetzung)

1. **Rang für `mark_acted`:** *derselbe wie die Direktroute.* Der Bestätigungszweig
   verlangt `require_permission('watering-log', CREATE)` — nach
   `MembershipEngine.can_edit_resource` also **lead oder grower**. Ein Viewer erhält
   403. Begründung: eine prüfbare Grenze, konsistent mit
   `watering_logs/tenant_router.py:57`; die stille Variante hätte denselben Knopf für
   zwei Rollen Verschiedenes tun lassen, ohne dass der Viewer es merkt.
2. **Detektorform für #1443:** *statische Aufrufgraph-Analyse (AST).* Sie braucht keine
   laufende App, läuft damit in der bestehenden `backend-guards`-Lane und ist nicht von
   dem Integration-Tier abhängig, das laut #1432 in keinem CI-Gate läuft. Der Preis —
   mögliche Falsch-Positive — wird durch einen Lauf gegen den vollständigen heutigen
   Routenbestand vor dem Scharfschalten kontrolliert.

Das Artefakt wurde am 2026-09-16 freigegeben; die Umsetzung beginnt mit Scheibe 1.

## Ergebnisse je Scheibe

### Scheibe 1 — #1441 (Sub-Branch `fix/1441-notification-act-rank`, Merge `5de0dcd0b`)

Dispatchter Spezialist: `nolte-engineering:fullstack-developer`.

**Rot zuerst, gegen den unveränderten Handler** (`src/backend/.venv/bin/python -m pytest
tests/api/test_notification_act_role_gate.py -q`):

```
E       AssertionError: a CareConfirmation reached the repository
E       assert [CareConfirma...ated_at=None)] == []
E         Left contains one more item: CareConfirmation(key='confirmation1', plant_key='plant1',
E         ... watering_log_key='log1', ...)
E       assert 200 == 403
5 failed, 6 passed in 5.99s
```

Der Rekorder zeigt die **ausgeführte** Ausnutzung: ein `viewer` erzeugte
`CareConfirmation(…, watering_log_key='log1')` — Bestätigung und Gießprotokoll.

**Grün danach**, nachgemessen im Integrations-Worktree nach dem Merge:

```
tests/api/test_notification_act_role_gate.py tests/unit/api/test_write_route_gates.py
109 passed in 5.57s
```

Vom Spezialisten gemeldet, nicht von mir wiederholt: `tests/unit tests/api` →
9982 passed, 1 skipped; `vitest run` → 4085 passed; `tsc` 0 Fehler; `task precommit`
47 Hooks grün, 1 umgebungsbedingt rot (`nuclei` nicht auf PATH, Templates unberührt).

**Was geändert wurde:**
- `app/api/v1/notifications/tenant_router.py:179-180` — `MembershipEngine.can_edit_resource(ctx.role)` im Bestätigungszweig, **vor** jedem Stempeln; dieselbe Prädikatsquelle, die `require_permission(…, CREATE)` auswertet (`app/common/auth.py:554-567`). Keine neue Rollenliste.
- `tests/api/test_notification_act_role_gate.py` (neu, 12 Fälle) — echter `CareReminderService` mit aufzeichnenden Repositories, damit „kein Schreibvorgang" ein abwesender Repository-Aufruf ist. Enthält einen Parity-Guard Backend↔Frontend für `_CARE_CONFIRM_ACTIONS`, per Mutation als nicht-vakuös nachgewiesen.
- `tests/unit/api/test_write_route_gates.py` — Allowlist-Begründung ersetzt; benennt jetzt Datei::Funktion, Prädikat und prüfende Testdatei.
- `src/frontend/src/utils/careConfirmActions.ts` (neu), `NotificationDrawer.tsx` — Bestätigungsknopf an `useTenantPermissions().canEdit`; 403-Pfad bleibt intakt.
- `spec/req/REQ-030_Benachrichtigungssystem.md` §7 — normative Regel; §3.11 und §4.2 verweisen darauf.

**Lokale Anpassungen (Aufnahme, Modus, Reihenfolge unberührt):**
1. Die Matrix nannte `spec/req/REQ-030.md §4.2`; die Datei heißt `REQ-030_Benachrichtigungssystem.md`, und §4.2 ist der HA-Rückruf. Die Regel liegt jetzt in §7 (Autorisierungstabelle), wo sie hingehört.
2. `pre-commit run check-section-refs` existiert in diesem Repository nicht (0 Treffer in 48 Hook-IDs). Ersatz: vollständiger `task precommit`.
3. Der Modus-B-Preis (Konflikt in `test_write_route_gates.py`) ist nicht eingetreten; die Zeilennummern des `WRITE_METHODS`-Blocks für Scheibe 2 sind unverändert, der Allowlist-Eintrag liegt jetzt bei `:143-166`.

**Nebenbefund**, kein Defekt: `canEdit` ist im Auth-Bootstrap-Fenster (`activeTenant: null`) `false`, anders als `<RequireRole>` es hält. Folgenlos, weil ohne aktiven Mandanten keine Benachrichtigungen geladen werden; bewusst fail-closed, weil das Backend die Grenze ist.

**UI-Review (Pflichtkette nach Frontend-Änderung), `nolte-engineering:frontend-usability-optimizer`:**
keine Änderung nötig. `vitest` 18/18 grün, `tsc` 0 Fehler, ESLint 0 Fehler / 1
vorbestehende Warnung (`NotificationDrawer.tsx:144`, `set-state-in-effect`, seit #752).
Stille beim fehlenden Knopf ist spec-gebunden (REQ-030 §7:1527-1528) und deckt sich mit
dem einzigen anderen rollen-gegateten Knopf (`PestScanButton.tsx:48-50`). Zwei
Beobachtungen, beide **Low**, bewusst nicht in diesem Bündel:
- Die 403-Meldung ist generisch („bitte versuche es erneut"), obwohl `useApiError.ts:80-83`
  einen `errors.forbidden`-Pfad hat; bei permanentem Rollenverlust ist „erneut" nutzlos.
- `useTenantPermissions` liefert im Auth-Bootstrap-Fenster `canEdit=false` für **jeden**
  Consumer (`PlantDiaryTab`, `PestScanButton`, `SpeciesListPage` …), nicht nur hier; ein
  Grower sieht den Knopf für < 1 s nicht. Sauberer Fix (`isLoading` aus dem Hook, Slot
  skelettieren) ändert `useTenantPermissions.ts` — außerhalb der Gruppe. Kandidat für ein
  Folge-Issue, entschieden beim Bündel.

### Scheibe 2 — #1443 (Sub-Branch `fix/1443-write-route-detector`)

Dispatchter Spezialist: `nolte-engineering:fullstack-developer`.

**Detektorform:** statische Aufrufgraph-Analyse (AST), wie in Operator-Entscheidung 2
festgelegt. Neues Modul `src/backend/tests/unit/api/_write_call_graph.py`; läuft in der
bestehenden `backend-guards`-Lane, keine Workflow-Änderung.

**Auflösung nach Empfängertyp, nicht nach Namen.** Vier Messungen haben die Form
bestimmt, jede davon war zuerst ein untauglicher Entwurf:

| Entwurf | Messung |
|---|---|
| Auflösung allein über den Methodennamen | **356 von 356** Leseoperationen als schreibend gemeldet (`api.mapping.to_response` kollidiert mit `BaseArangoRepository.update` auf `update`) |
| AQL-Erkennung über das Schlüsselwort | `BaseArangoRepository._to_doc` aus dem eigenen **Docstring** als Senke gesät → 2585 von 6047 Funktionen „schreibend" |
| Untypisierter Namens-Fallback ohne Einschränkung | `dict.update` machte `to_response` zum Schreiber → 181 Treffer |
| Modulglobale ignoriert | `router = APIRouter(...)` untypisiert → 160 Kanten aus `@router.delete(...)` |
| Aufwärts zur Basis und wieder abwärts | `create_profile` löste zu `ArangoWateringRepository.create` auf — jeder Pfad nannte die falsche Kollektion |

**Rot zuerst, zwei Beweise, beide per `cp`-Sicherung zurückgenommen:**

1. *Der Wandel selbst.* Mit auf die Methodenform zurückgesetztem Walk
   (`elif False:` statt der Erkennung):

```
E  AssertionError: the sweep's read half and the detector disagree:
E      in the sweep, not detected: []
E      detected, not in the sweep: ['auth.router.oauth_callback',
E      'dashboard.tenant_router.get_widget_catalog', 'glossar.public_router.public_get_term',
E      'glossar.router.get_term', 'ki_assistent.tenant_router.get_daily_tip',
E      'ki_assistent.tenant_router.get_tips', 'onboarding.tenant_router.get_onboarding_state',
E      'privacy.router.download_export', 'season.tenant_router.get_site_season_state',
E      'user_preferences.tenant_router.get_preferences']
1 failed, 8 passed
```

2. *Mutation des Detektors.* Senkenliste geleert (`_COLLECTION_MUTATORS = frozenset()`,
   `_QUERY_WRITE` trifft nichts) — **6 Tests rot**, darunter die künstliche schreibende
   `GET`, die `TestTheDetectorCanFail` als eigenen Mini-Baum auf die Platte schreibt und
   mit einem frischen Graphen parst:

```
FAILED TestTheDetectorCanFail::test_a_writing_get_is_found_although_nothing_lists_it
FAILED TestTheDetectorCanFail::test_a_detector_with_no_sinks_finds_nothing
FAILED TestPersistingReadsAreSweptLikeWrites::test_the_detector_agrees_with_the_method_convention_where_it_applies
FAILED TestPersistingReadsAreSweptLikeWrites::test_every_finding_is_still_a_persisting_read
FAILED TestPersistingReadsAreSweptLikeWrites::test_every_guarded_read_really_passes_its_guard
FAILED TestPersistingReadsAreSweptLikeWrites::test_a_guarded_read_would_be_reported_without_its_guard
6 failed, 104 passed
```

3. *Die historische Form.* `git archive c883367da^` (der Stand vor #1422) in einen
   Temp-Baum, Detektor darüber: beide Routen gefunden, mit Pfad —
   `care_reminders.router::get_or_create_profile` → `CareReminderService.get_or_create_profile`
   → `ArangoCareReminderRepository.create_profile` → `insert()`, und
   `care_reminders.tenant_router::get_care_dashboard` über
   `get_care_dashboard_for_tenant` auf denselben Schreibvorgang. Der Detektor **hätte**
   die Lücke von #1422 gefunden.

**Grün danach:** `tests/unit/api/test_write_route_gates.py` 110 passed in 8,3 s;
die Lane `tests/unit/api tests/unit/guards` 355 passed in **14,5 s** (Detektor baut den
Graphen einmal pro Session, ~3,3 s für 935 Module / 6047 Funktionen);
`tests/unit tests/api` 9995 passed, 1 skipped.

**Trefferliste gegen den heutigen Bestand: 13 von 356 Leseoperationen.**

*Zehn echte Schreibvorgänge auf einer `GET`* — gemeldet, **nicht** repariert (außerhalb
des Scopes dieser Scheibe), festgehalten in `_PERSISTING_READ_FINDINGS` als offene
Befunde mit Ratsche (≤ 10) und Obsoleszenzregel:

| Route | Schreibvorgang |
|---|---|
| `GET /api/v1/public/glossary/term/{slug}` | **anonym** — schreibt pro ungesehenem Slug eine `GlossaryTermCacheEntry` |
| `GET /api/v1/t/{slug}/glossary/term/{slug}` | dasselbe `_store_cache`, mandantengebunden |
| `GET /api/v1/t/{slug}/user-preferences` | legt das `UserPreference`-Singleton beim Kaltlesen an |
| `GET /api/v1/t/{slug}/dashboard/widgets/catalog` | erreicht dieselbe Auto-Anlage |
| `GET /api/v1/t/{slug}/onboarding/state` | legt das `OnboardingState`-Singleton an |
| `GET /api/v1/t/{slug}/ai/tips` | invalidiert den Tipp-Cache, legt die Karte an, schreibt einen Audit-Eintrag |
| `GET /api/v1/t/{slug}/ai/daily-tip` | dieselbe Form |
| `GET /api/v1/t/{slug}/sites/{key}/season-state` | `upsert` des berechneten `SeasonState` |
| `GET /api/v1/privacy/export/{key}/download` | erhöht und persistiert `download_count` |
| `GET /api/v1/auth/oauth/{slug}/callback` | legt User, AuthProvider-Verknüpfung und Refresh-Token an (OAuth2-Redirect kann nur `GET` sein) |

Sieben davon hängen an blankem `get_current_tenant`, zwei sind **ohne jede
Autorisierung** erreichbar — die Sweeps haben sie beim Scharfschalten sofort gemeldet.

*Drei Falsch-Positive*, und die Ausnahme ist **prüfbar statt Prosa**: der Detektor ist
pfadinsensitiv und kann `may_create=False` nicht auswerten.
`_GUARDED_PERSISTING_READS` trägt je Eintrag den Zeugen `(callee, keyword)`, und
`test_every_guarded_read_really_passes_its_guard` liest **jeden erreichbaren Aufruf**
zurück aus dem Quelltext und fällt um, sobald einer nicht literal `False` übergibt:
`care_reminders.router.get_or_create_profile`,
`care_reminders.tenant_router.get_care_dashboard`,
`print.tenant_router.export_care_checklist_pdf`.

**Was geändert wurde:**
- `src/backend/tests/unit/api/_write_call_graph.py` (neu, 769 Zeilen) — Detektor, Grenzen im Modul-Docstring benannt (dynamischer Dispatch, Celery-Tasks, untypisierte Empfänger, Argumentwerte, alles außerhalb von `app`).
- `src/backend/tests/unit/api/test_write_route_gates.py` — Kommentar `:42-59` ersetzt; `mounted_operations()` als **eine** Aufzählung, `mounted_write_operations()` filtert darüber; zwei neue Testklassen; Befund- und Ausnahmetabelle.

**Lokale Anpassungen:**
1. Der Auftrag nannte `mounted_write_operations()` als Enumerationsmechanismus. Der Walk musste trotzdem angefasst werden, weil er Leserouten gar nicht erst erzeugte — aufgeteilt in `mounted_operations()` (Walk) und `mounted_write_operations()` (Filter), *ein* Walker wie gefordert.
2. Eine Ceiling-Prüfung auf untypisierte Empfänger (9245 gemessen, Grenze 11000) ist hinzugekommen: der blinde Fleck des Detektors ist die einzige Stelle, über die er nicht selbst berichten kann.

**Umgebungsbedingt rot in `task precommit`** (48 Hooks, 45 grün): `ESLint (frontend)`
und `TypeScript check (frontend)` — `src/frontend/node_modules` fehlt im Worktree —
sowie `Nuclei template validate` — `nuclei` nicht auf PATH. Der Diff ist reiner
Backend-Testcode; keine Frontend- und keine Template-Datei berührt.

## Gate und Verifikationsdurchgang auf dem Integrationsbranch-Kopf (`eb43c76c3`)

**Quality-Gate, im Integrations-Worktree (frisches venv, `app` → dieser Baum):**

```
ruff check / format --check          All checks passed! / 1718 files already formatted
pytest tests/unit tests/api          9995 passed, 1 skipped in 372.59s
tsc -p tsconfig.build.json --noEmit  OK
eslint .                             OK
vitest run                           409 files, 4085 passed
```

**Security-Review (`nolte-engineering:code-security-reviewer`, fremder Kontext,
read-only):** die Autorisierungsreparatur (#1441) ist fail-closed und ohne Oracle —
jeder benannte Umgehungsweg einzeln gemessen (andere `action_id`, andere
`notification_type`-Schreibweise, fehlender `plant_key`, HA-Rückruf, Reihenfolge vor
jedem Stempeln). Kein Bypass. Ownership-Prüfung vor Rang-Check ist die richtige
Reihenfolge (REQ-049 §2.4 erfüllt, das 403 ist nur für den Adressaten seiner eigenen
Zeile erreichbar).

**Vier Warnings am Wächter (#1443), keine Critical — als lokale Anpassung in das
Bündel aufgenommen (Aufnahme, Modus, Reihenfolge unberührt):**

| # | Befund | Entscheidung |
|---|---|---|
| SEC-001 | Ratsche `len(...) <= 10` erlaubt einen *Austausch* (eine repariert, eine neue) | `frozenset` der gemessenen IDs statt Länge; Hinzufügen unmöglich, Entfernen frei |
| SEC-002 | `_GUARDED_PERSISTING_READS` ohne Deckel; der Zeuge muss nicht der Grund des Treffers sein — ein zweiter Schreibvorgang im selben Handler bliebe unsichtbar | Eintrag trägt zusätzlich die gemessene **Senke**; Deckel `<= 3` |
| SEC-003 | `_TENANT_ALLOWLIST`: 27 Einträge bleiben Prosa ohne Deckel — exakt die Form, die #1441 erzeugt hat | Deckel; die 11 „computation, no write"-Einträge werden mit `not persists(endpoint)` **gemessen** statt geglaubt |
| SEC-004 | Detektor sieht Modul-Level-Query-Literale nicht (gesamte TimescaleDB-Schreibfläche), Docstring behauptet das Gegenteil | Modul-Level-`Assign` gegen `_QUERY_WRITE` prüfen, Alias als Senke führen; mindestens: Blindfleck ehrlich benennen |

Suggestions SEC-005 (`BackgroundTasks.add_task` als unbenannter Blindfleck), SEC-006
(Frontend-Parität deckt das Typ-Präfix nicht), SEC-007 (`care.*` ohne `plant_key` für
einen Viewer unquittierbar — fail-closed, Docstring sagt es nicht) werden mit erledigt.

**Die zehn Befunde sind angelegt:** #1460 (anonymer Glossar-Schreibpfad, vom Review
auf *Warning* korrigiert — kuratierter Katalog + Ratenlimit deckeln die Zeilenzahl;
der Detektor-Befundtext „writes a row per unseen slug" überzeichnete) und #1461
(Klassen-Issue mit allen zehn, Schwere je Route). Die Nummern gehören in
`_PERSISTING_READ_FINDINGS`.
