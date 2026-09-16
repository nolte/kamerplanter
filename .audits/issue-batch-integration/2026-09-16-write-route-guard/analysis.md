# Gruppe `2026-09-16-write-route-guard`

Status: wartet auf Operator-Freigabe (Write-Gate nach `spec/project/issue-batch-integration/` §D)

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

Dieser Befund gilt **nicht** als erledigt, wenn #1441 und #1443 repariert sind. Er wird
als eigenes Issue gegen `spec/project/defect-class-guards/` angelegt, mit Verweis auf
diese Gruppen-Id, und speist die Klasse in den `continuous-improvement`-Loop.

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

## Offene Fragen an den Operator

1. **Welcher Rang darf über die Benachrichtigung bestätigen?** Die direkte Route verlangt `require_permission('watering-log', CREATE)`, was nach `MembershipEngine.can_edit_resource` **lead oder grower** bedeutet. Soll `mark_acted` denselben Rang verlangen (konsistent, aber ein Viewer verliert den Ein-Tipp-Weg vollständig), oder soll der Bestätigungszweig für einen Viewer still übersprungen werden, während Lesen/Acted-Stempeln weiterhin funktioniert (mildere Degradation, aber zwei Verhalten für denselben Knopf)?
2. **Welche Form soll der Detektor in #1443 haben?** Statische Aufrufgraph-Analyse über die Handler (AST, findet auch indirekte Pfade, aufwendiger) oder eine Laufzeit-Instrumentierung der Repository-Schreibmethoden während des bestehenden Routen-Sweeps (präziser, braucht aber eine laufende App)?
