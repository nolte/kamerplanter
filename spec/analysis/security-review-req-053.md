# Security Requirements Review — REQ-053 v1.1 (Grafische Garten- und Beetplanung)

**Datum:** 2026-10-04 · **Reviewer:** `nolte-shared:security-requirements-reviewer` (read-only; Bericht vom Aufrufer abgelegt) · **Gelesen:** REQ-053 §1–§32 (Fokus §13, §14, §18, §20–§23, §25–§27, §30–§31); REQ-049 (Rollen, Technik), NFR-011 (Retention-Matrix); `src/backend/app/domain/engines/print_engine.py:172`. **Baseline:** REQ-024, REQ-049, REQ-025/NFR-011, NFR-006, NFR-013; Durchsetzungsstand laut CLAUDE.md (`resource`-Argument von `require_permission` entscheidet heute nichts). **Annahmen:** Location/Slot ohne `tenant_key` (REQ-053 §20.13). **Nachgemessen vom Aufrufer (2026-10-04):** `print_engine.py:172` ohne `url_fetcher` ✔; NFR-011 ohne Zeile für `watering_events`/`feeding_events`/Pflegeprotokoll ✔.

**Einarbeitung:** REQ-053 v1.2 Changelog; Status je Befund in der Tabelle „Priorisierte Empfehlungen".

## Gesamtbewertung

| Dimension | Bewertung | Notiz |
|---|---|---|
| Datenminimierung | mittel | Geometrie sauber. Freitexte und Personenbezug in `care_events` nicht eingegrenzt. |
| Authentifizierung | gut | Alles unter `/t/{slug}`, Akteur aus dem Token (GP-NFR-054). |
| Autorisierung / RBAC | **schwach** | Batch-`delete` umgeht „Nur Leitung". Widersprüche §21.1–§21.7 ↔ §21.8. Datenabhängige Regeln über `require_permission` nicht ausdrückbar. |
| Mandanten-Isolation | **schwach** | §22.3 sagt nicht, woher `site_key` stammt. Body-Querverweise werden nicht aufgelöst. |
| API-Sicherheit | **schwach** | Layout ohne Obergrenze, keine Batch-Komplexitätsgrenze, Rate-Limits nur auf 2 von ~40 Endpunkten. |
| DSGVO | **schwach** | Retention-Referenz zeigt ins Leere; Kaskade unvollständig; Art. 15/20 ohne `care_events`; append-only blockiert Art. 16/17 für Freitext. |

Stark: GP-NFR-050–055 (404-Muster, Key-Neuvergabe beim Import, SVG-Escaping, Token-Akteur, EXIF-Strip, „GPS nie gespeichert").

## Critical

**SR-001 Batch-`delete` umgeht „Löschen: Nur Leitung".** §21.8 gatet den Batch mit `Action.UPDATE`, das Beispiel enthält `delete`; §21.8 verlangt für Beet/Objekt „Nur Leitung". Op-Liste nicht abschließend. → Op-Werte abschließend aufzählen; jede Op einzeln gegen §21.8 prüfen, vor der Domain-Validierung; ein Batch mit einer Op über der Rolle → 403 `batch.operation_forbidden {op_index}`.

**SR-002 §22.3 sagt nicht, woher `site_key` stammt.** Auf `/locations/{key}`, `/slots/{key}`, `/garden-objects/{key}` steht keine Site im Pfad; aus Body/Query genommen besteht ein Angreifer mit eigener Site + fremdem Key die Prüfung. Batch prüft nicht, dass jeder Op-Key (inkl. `parent_location_key`) zur Pfad-Site gehört. → `site_key` **immer aus dem gespeicherten Dokument ableiten**; `resource.site_key == path.site_key`; jede Referenz vor Geometrie-/Containment-Prüfung auflösen; 404/422 `reference.not_found` ohne Unterscheidung fremd/fehlt.

**SR-003 Body-Querverweise ungeprüft.** `care_events.plant_keys`, `photo_refs`, `product_ref`, `supersedes_key`, `source_ref`; `water_source_key`, `actuator_key`, `flow_rate_ha_entity_id`; Zone `location_keys[]`; `plan-slots` `slot_keys[]`; Task-Keys im Batch; `template_key`, `species_key`/`cultivar_key`; `substrate_key`/`substrate_batch_key`. → neue **GP-NFR-058 (MUST)**: jeder Body-Key wird gegen den aktiven Tenant aufgelöst (globale Stammdaten `tenant_key = null` nur für `species`, `cultivar`, `fertilizer`, `substrate`, `bed_template`); Teilmengenregeln (`plant_keys` ⊆ Teilbaum des Beets, `slot_keys` ⊆ Run-Location, `location_keys` ⊆ Zone-Site, `water_source_key` = GardenObject derselben Site, `photo_refs` = eigene/zielgebundene Attachments, `supersedes_key` = gleiches Beet, `source_ref` nur serverseitig); Negativtest je Feld.

**SR-004 Layout ohne harte Obergrenze.** 1 000 × 1 000 m bei 5 cm → ~4·10⁸ Positionen je Preview, für alle Rollen, 60/min; persistierende Pfade ohne Quote. → `compute_layout` bricht bei > 2 000 Positionen ab (Vorab-Schätzung Fläche ÷ Abstand², 422 `layout.too_many_positions`); Quoten: Slots ≤ 2 000/Beet, ≤ 8 000/Site; Locations + GardenObjects ≤ 500/Site; §25.1 Belastungsgrenze → harte Quote (422 `plan.quota_exceeded`); Quick-Planting `quantity` ≤ 500.

**SR-005 Retention für `care_events` zeigt ins Leere.** GP-NFR-055 „wie `watering_events`" — NFR-011 hat keine solche Zeile. → NFR-011 R-xx `care_events` (Frist: DPO-Entscheid, z. B. 5 Jahre analog GP-FR-103; danach Personenfelder/Freitexte anonymisiert, Kategorie/Zeit/Menge/Beet bleiben; PflSchG-Vorbehalt für Behandlungen); R-yy `garden_plan_audit` 1 Jahr, dann Hard-Delete.

**SR-006 Append-only blockiert Art. 16/17 für Freitexte.** Kaskade greift nur beim Account des Ausführenden; Namen Dritter in `performed_by_label`/`summary`/`reason`/`observed_outcome` und Personen auf Fotos sind weder berichtigbar noch löschbar. → **GP-FR-109 (MUST) Redaktion:** Leitung/Kaskade ersetzt Freitexte und `photo_refs` eines Events und seiner Supersede-Kette durch `[redacted]` (`redacted_at/by/reason`), Attachments gelöscht; einzige Mutation neben Supersede/Void; `performed_by_label` ≤ 80 Zeichen, UI-Hilfe „keine vollständigen Namen"; Mitglieder per `performed_for_user_key` statt Freitext.

## Warning

**SR-007 Kaskade unvollständig:** `care_events.created_by`, `garden_objects.created_by`, `Site.plan.plan_updated_by`, 409-`changed_by`, Filter `performed_by`, `bed_templates`-Ersteller, `voided_by` (fehlt). → alle `_by`/`_user_key`-Felder in `ErasureEngine.ANONYMIZE_COLLECTIONS`; Inventar-Test.
**SR-008 Art. 15/20 ohne `care_events`.** → DSGVO-Export enthält `care_events` (performed_by/created_by = Betroffener) + `garden_plan_audit`.
**SR-009 Client kann `trigger` setzen** (umgeht V-11 via `backfill`). → Client nur `manual`/`observation`; Rest serverseitig; Supersede übernimmt `performed_by_user_key`, Korrigierender in `created_by`; „Eigene" = `created_by == Nutzer`.
**SR-010 Matrix-Widersprüche:** GP-API-022 „Ab Gärtner" vs. §21.8 „Nur Leitung"; Import `merge` unklar; „Aktor-Befehl: Technik" widerspricht REQ-049 §2 (Technik konfiguriert, bedient nicht); datenabhängige Regeln (belegt/eigene) nicht via `require_permission` ausdrückbar. → angleichen; datenabhängige Regeln im Service; Negativtest je Zeile und Rolle.
**SR-011 Kein Pflicht-Audit für destruktive Aktionen;** `replace --force`-Semantik offen. → `garden_plan_audit` MUST für delete/retired/replace, atomar; `force` hebt nur die Leer-Bedingung für Beete ohne aktive Pflanzen auf, V-09 gilt immer; Snapshot vor `replace` MUST.
**SR-012 Batch-Komplexität nur nach Anzahl.** 500 × 200 Punkte × 500 Geschwister → ~10¹⁰ Segmentpaare in einer Stream-Transaktion. → Σ Punkte ≤ 20 000/Batch, 10 s Zeitbudget, 422 `batch.too_complex`; Containment/Overlap **vor** der Transaktion; Body ≤ 2 MB.
**SR-013 Prüfreihenfolge als Orakel.** → feste Reihenfolge Auth → Tenant/Referenzen → Rolle je Op → Pydantic → Domain → Revision; fremder Kontext immer 404 ohne Details; `changed_by` = Anzeigename.
**SR-014 `flow_rate_ha_entity_id` unvalidiert, von Gärtnern setzbar;** Pfad-/SSRF-Risiko, `person.*`-Bindung leakt Anwesenheit. → Regex `^sensor\.[a-z0-9_]{1,64}$`, in Entitätsliste der Tenant-HA, `device_class ∈ {water, volume_flow_rate}`, nur Technik, nur abgeleiteter Liter-Wert an den Client.
**SR-015 PDF/SVG:** `print_engine.py:172` ohne `url_fetcher` (Default lädt `http(s)://`, `file://` → SSRF/Local File Read); Attribut-Escaping, `color`-Whitelist, Enum-Query-Parameter, Jinja-Autoescape, Element-Allowlist, `data:`-only Bilder, CSP/`nosniff` beim SVG-Download. Betrifft auch bestehende `/print/*`.
**SR-016 CSV-Formel-Injection.** → Zellen mit `= + - @ Tab CR` präfixieren; `performed_by` als Anzeigename; ≤ 50 000 Zeilen.
**SR-017 Rate-Limits fehlen** auf PDF/SVG/Export/CSV/Import/Quick-Planting/slots-batch/care-events/log-watering/tasks-batch/`as_of`. → Staffel je Nutzer/Tenant, 429 mit `Retry-After`.
**SR-018 Import nur nach Bytes begrenzt.** → Quoten aus SR-004, ≤ 10 Ebenen, alle V-Regeln + SR-003, `dropped_references[]` im Dry-Run, `flow_rate_ha_entity_id`/`actuator_key` beim Import immer verwerfen; Export ohne `*_by`.
**SR-019 Eigenposition/Sentry/Cache.** → Eigenposition nur im flüchtigen Komponentenzustand; Sentry nur mit Einwilligung, Breadcrumbs ohne Namen/Keys/Koordinaten, Redux-State nicht an Sentry; Cache-Schlüssel `user_key`+`tenant_key`, Logout/Tenant-Wechsel leeren.
**SR-020 `performed_by`-Filter ermöglicht Aktivitätsprofile** (Gemeinschaftsgarten). → nur Leitung oder `performed_by=me`; DPO-Frage.

## Suggestion
**SR-021** Adjacency-Job nur `location_key` im Payload, Site/Tenant aus DB. **SR-022** `tenant_key` auf `locations`/`slots` in v0072 stempeln + Index — schließt die Klasse SR-002/003/021 strukturell. **SR-023** QR nur relativer Pfad, Rücksprung same-origin, Nicht-Mitglied → 404. **SR-024** PDF/SVG/PNG ohne Mitgliedernamen/Zuweisungen/Notizen/GPS; GeoJSON nur Leitung. **SR-025** Payloads/422-Inputs/Dateinamen nie loggen.

## Info
SR-026 XXE nicht im Scope (nur JSON). SR-027 GP-NFR-053/054 gut; AKs für SR-003/SR-010 fehlen. SR-028 `ha_publish` nur Tenant-HA, Kopplung = Technik.

## Priorisierte Empfehlungen

| # | Severity | Maßnahme | Betroffen | Status v1.2 |
|---|---|---|---|---|
| 1 | Critical | Rollenprüfung je Batch-Op, abschließende Op-Liste | GP-API-003, §21.8 | eingearbeitet |
| 2 | Critical | `site_key` aus Dokument, Zugehörigkeit je Referenz | §22.3 | eingearbeitet |
| 3 | Critical | GP-NFR-058 Referenzauflösung | §21, §14, §15 | eingearbeitet |
| 4 | Critical | Layout-Obergrenze, Plan-Quoten | GP-FR-062/073, §25.1 | eingearbeitet |
| 5 | Critical | NFR-011-Zeilen | GP-NFR-055 | eingearbeitet (Frist: Betreiberentscheid) |
| 6 | Critical | Redaktion GP-FR-109 | GP-FR-101, V-12 | eingearbeitet |
| 7–19 | Warning | siehe oben | — | eingearbeitet |
| 20 | Suggestion | `tenant_key` auf Location/Slot | v0072 | Betreiberentscheid |

## Caller follow-ups (Rechts-/DPO-Fragen)
- Frist für `care_events` mit PflSchG-Vorbehalt (SR-005).
- `performed_by`-Filter für Beobachter: berechtigtes Interesse oder DSFA (SR-020).
- Namen Dritter in `performed_by_label`, Informationspflicht Art. 14 (SR-006).
- Code-Seite: fehlender `url_fetcher` in `print_engine.py:172` betrifft bestehende `/print/*` → Kandidat `code-security-reviewer` / eigenes Issue.
