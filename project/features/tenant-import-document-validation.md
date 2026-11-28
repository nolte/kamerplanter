---
id: F-32
title: Dokumentprüfung beim Import gegen das Datenmodell
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-28
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-28
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:1212
      resolution: proceed
      evidence: "Kanten werden nach remap_edge ungeprüft geschrieben (:1212-1227); für Kanten gibt es keine Modelle. acceptance-4 auf Dokument-Collections begrenzt, Kanten als ausdrückliche Ausnahme, auch für REQ-056 §12.4 (acceptance-5)."
    - kind: drift
      target: src/backend/app/domain/services/tenant_service.py:419
      resolution: proceed
      evidence: "Die Angaben aus tenant.json gehen roh in Tenant(...) (:419-428); ein ungültiger Wert scheitert erst im Lauf als IMPORT_FAILED (tenant_export_service.py:1037-1039). Neues Kriterium acceptance-6."
    - kind: prior-art
      target: src/backend/tests/unit/guards/test_tenant_export_covers_the_inventory.py:105
      resolution: proceed
      evidence: "Die Ableitung liefert je Collection eine Liste von Modellen (:105-119). Festgelegt: Jedes gebundene Modell muss den Datensatz annehmen (acceptance-1, Consistency notes)."
    - kind: prior-art
      target: src/backend/app/domain/models/site.py:588
      resolution: proceed
      evidence: "Strukturstrenge Modelle ('model_config = {\"extra\": \"forbid\"}', LocationLighting :576-588) sind das eigentliche Risiko für acceptance-3; der Lauf mit einem echten Garten liegt vor dem Merge von F-32 (Hook zu acceptance-3)."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "Aus dem ersten Agentenlauf nachgetragen: F-32 füllt das Detailfeld, das F-15 acceptance-6 einführt. Begründung in den Consistency notes (manueller Durchgang, 'Überschneidung mit F-15')."
    - kind: overlap
      target: F-33
      resolution: proceed
      evidence: "Aus dem ersten Agentenlauf nachgetragen (dort gegen F-17): Die fehlgeschlagene Vorprüfung mit den Einträgen aus F-32 zeigt seit der Teilung F-33 acceptance-2 in der Importliste. Begründung in den Consistency notes."
    - kind: drift
      target: src/backend/app/domain/services/tenant_export_service.py:1162
      resolution: proceed
      evidence: "Zweiter Lauf: import_archive ersetzt heute still: Beschreibung falschen Typs → None, Einstellungen → {{}} (:1162-1165), fehlender Name → 'Imported garden' (:1182). acceptance-6 macht daraus eine Ablehnung mit Code und Feldname (Vorgabe der Hauptsitzung)."
---

## Description

Beim Import eines Mandanten-Archivs prüft Kamerplanter heute, ob jeder
Datensatz zum archivierten Garten gehört und ob seine Verweise auflösbar sind.
Ob der Inhalt eines Datensatzes zum Datenmodell passt, prüft der Import nicht.
Ein von Hand verändertes oder beschädigtes Archiv kann deshalb einen Wert
einspielen, den die Anwendung nicht kennt, etwa eine Ausfallursache oder eine
Bodengefahr außerhalb der erlaubten Liste. Der Import meldet Erfolg, und erst
später schlägt das Öffnen der betroffenen Pflanze oder des Beets fehl.

Nach dieser Änderung prüft der Hintergrundprozess jeden Datensatz des Archivs
gegen das Datenmodell, bevor ein Garten angelegt wird. Passt ein Datensatz
nicht, wird das ganze Archiv abgelehnt und nichts geschrieben. Der
Plattform-Admin sieht in der Statusanzeige des Imports und, sobald es sie gibt,
in der Vorprüfung, welche Datensätze und welche Felder betroffen sind. Ein
unverändertes Archiv aus der eigenen Installation besteht die Prüfung.

## Acceptance criteria

- [ ] **acceptance-1** Ein Archiv mit einem Datensatz, den eines der Datenmodelle seiner Collection nicht annimmt — ein Wert außerhalb des Wertebereichs (auch in einem verschachtelten Feld wie der Bodengefahr eines Beets), ein fehlendes Pflichtfeld oder ein falscher Typ —, endet in der Hintergrundprüfung als fehlgeschlagen mit dem neuen Code `IMPORT_DOCUMENT_INVALID`; es entsteht kein Garten, und kein Datensatz des Archivs ist geschrieben.
- [ ] **acceptance-2** Die Statusanzeige des Imports nennt für jeden abgelehnten Datensatz Collection, Schlüssel und Feld (höchstens 200 Einträge) und zeigt nie den abgelehnten Wert.
- [ ] **acceptance-3** Ein unverändertes Archiv aus dieser Installation besteht die Prüfung, auch wenn es Datensätze enthält, denen später eingeführte Felder fehlen; die importierten Datensätze stehen danach so in der Datenbank wie im Archiv (bis auf Schlüssel und Mandant).
- [ ] **acceptance-4** Die Prüfung erfasst jede Dokument-Collection, die ein Archiv enthalten kann; Collections ohne Datenmodell sind einzeln mit Begründung ausgenommen, und eine neue Dokument-Collection im Archiv ohne diese Entscheidung lässt einen Guard fehlschlagen. Kanten sind ausdrücklich ausgenommen: Für sie gelten weiter nur die Regeln für importierbare Kanten und ihre Enden.
- [ ] **acceptance-5** Oberfläche und Runbook (DE + EN, Tabelle „Wenn der Import ablehnt“) erklären den neuen Code und was zu tun ist; REQ-056 §12.4, §8.4 Schritt 1 und §16.4 (neues Abnahmekriterium) beschreiben die Dokumentprüfung, ihre Ausnahmen (Kanten, Collections ohne Modell) und dass sie im Hintergrundprozess läuft.
- [ ] **acceptance-6** Ein Archiv, dessen Angaben zum Garten selbst (`tenant.json`: Name, Kurzname, Beschreibung, Einstellungen) fehlen oder den falschen Typ haben, endet in der Hintergrundprüfung mit `IMPORT_DOCUMENT_INVALID` und nennt das Feld; der Import ersetzt solche Angaben nicht mehr stillschweigend durch einen Vorgabewert.

## Test hooks

- **acceptance-1** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py` and `src/backend/tests/unit/domain/engines/test_tenant_import_engine.py`: archives with `plant_instances.failure_cause_class` outside the enum, a bed whose `soil_hazards[].hazard` is not in the list, a missing required field, a wrong type and a document one of two bound models refuses each end `failed`/`IMPORT_DOCUMENT_INVALID` in `run_import`, with no tenant founded and no document written; the upload itself still answers 202 (F-15 acceptance-5); `src/backend/tests/integration/test_tenant_export_roundtrip.py`: a manipulated enum is refused against a real database and leaves no row — pending
- **acceptance-2** — unit test on the record (entries `<collection>/<key>: <field path>`, capped at 200, the offending value never in the record, the log or the audit) + vitest `src/frontend/src/test/components/TenantImportStatusCard.test.tsx` (entries listed, code text DE/EN) — pending
- **acceptance-3** — `src/backend/tests/integration/test_tenant_export_roundtrip.py` (AK-32 stays green with the check on; fixture rows without the fields added by F-19/F-20, `plant_instance.py:44-62`, `site.py:719-722`, and rows of the structure-strict models, e.g. `site.py:576-588`); manual, **before F-32 is merged** (the later features build on it): run the check against an export of an existing garden of the installation and confirm it is not refused — pending
- **acceptance-4** — `src/backend/tests/unit/guards/test_tenant_export_covers_the_inventory.py`: the runtime mapping collection → models equals the derived one (`models_by_collection`, `:105-119`), every exception carries a reason, a new exported document collection without a decision fails; a unit test pins that edges are not model-checked — pending
- **acceptance-5** — i18n completeness (new failure code under `pages.tenantImports.failure.*`) + `mkdocs build --strict` + spec diff review — pending
- **acceptance-6** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: an archive whose `tenant.json` has no name, a description that is not a string or settings that are not an object ends `failed`/`IMPORT_DOCUMENT_INVALID` naming the field in the background check, before `TenantService` is asked to found the tenant; the same archive is imported today with `None`, `{}` and "Imported garden" (`tenant_export_service.py:1162-1165`, `:1182`), which the test pins as removed — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte).

Geltend sind Beschreibung, Kriterien, Hooks und der jüngste Abschnitt dieser Notizen („Stand nach dem zweiten Agentenlauf“). Alle älteren Abschnitte sind Verlauf: Ihre Kriteriennummern, Feature-Zuschnitte und Aussagen geben den Stand ihres Laufs wieder.

Manueller, rein lesender Durchgang gegen develop `17e1034d2`, zusammen für F-15, F-32, F-17 und F-16. Es lief kein Test; jede Aussage über heutiges Verhalten stammt aus dem Lesen der genannten Stelle. Abweichung vom Regelweg: Der Agent `feature-consistency-reviewer` ist verfügbar, der Auftrag kam aber an einen Subagenten, der selbst keinen Agenten starten darf. Nach `spec/project/feature/` §Consistency check ist das ein Workflow-Health-Befund; der Lauf über den Agenten ist nachzuholen, sobald sich an den Kriterien etwas ändert.

**§12.4 verspricht die Prüfung, der Code liefert sie nicht (drift, proceed).** Established: REQ-056 §12.4 (`:480`) nennt als Gegenmaßnahme gegen ein präpariertes Archiv die „Schema-Validierung jedes Dokuments gegen das Domänenmodell (`422`)“; die Moduldoku des Dienstes schließt sie ausdrücklich aus (`tenant_export_service.py:52-53`). Das Feature liefert sie. Weil die Prüfung nach F-15 nur noch im Hintergrundprozess läuft, wird aus der `422`-Antwort ein fehlgeschlagener Import mit Code; acceptance-5 korrigiert §12.4 entsprechend.

**Die bestehende Prüfung ist der Einhängepunkt (prior-art, proceed).** Established: `_verified_archive` (`tenant_export_service.py:847-882`) liest das Archiv, prüft Struktur, Besitz und Verweise (`validate_documents`, Aufruf `:859`, Definition `tenant_import_engine.py:167-183`), Objekte und Katalog; der Worker ruft es in `run_import` auf (`:1013`), der Antrag heute noch zusätzlich (`:774`, entfällt mit F-15). Die Dokumentprüfung ist ein weiterer Schritt derselben Prüfung, vor der Gründung des Mandanten.

**Collection → Modell gibt es nur im Test (prior-art, proceed).** Established: Die Fixture `models_by_collection` (`test_tenant_export_covers_the_inventory.py:105-119`) leitet je exportierter Collection eine Liste von Modellen ab, `_MODELS_BY_HAND` (`:48-61`) ergänzt `ha_publish_settings` und nennt für `diagnosis_requests` und `care_events` einen Grund statt eines Modells. Im Produktivcode von Export und Import gibt es keine solche Zuordnung (Suche nach `collection_models`, `_MODELS`, `MODEL_OF` und `model_for` in `tenant_export_engine.py`, `tenant_import_engine.py` und `tenant_export_service.py` ohne Treffer). acceptance-4 verlangt die Zuordnung zur Laufzeit und bindet sie per Guard an die abgeleitete. Die Fixture liefert je Collection eine Liste; wie die Prüfung mit mehreren Modellen einer Collection umgeht, ist Sache der Umsetzung, solange acceptance-3 hält. [Überholt, was mehrere Modelle angeht: Festgelegt ist „jedes gebundene Modell muss passen“, acceptance-1.]

**Enum-Felder reisen als Rohdokument (prior-art, proceed).** Established: `PlantInstance` trägt seit F-19 `failure_cause_class`, `failure_pathogen` und `failure_pathogen_source` als Enum-Felder (`plant_instance.py:47-62`), `Location` seit F-20 `soil_hazards` mit einem Validator (`site.py:722-734`; der Lauf vom 27.11. nannte `site.py:709`, die Zeile ist seither verrutscht). Der Roundtrip-Test validiert nur ein gutes Beet nachträglich (`test_tenant_export_roundtrip.py:498`); ein manipulierter Wert wird heute geschrieben.

**Überschneidung mit F-15 (overlap, proceed).** Begründung für `proceed`: F-15 acceptance-6 führt das Detailfeld am Import-Datensatz ein und zeigt es an der Statuskarte; F-32 liefert einen weiteren Ablehnungsgrund und füllt dasselbe Feld. Es entsteht kein zweites Feld und keine zweite Anzeige. Deshalb steht F-32 in der Reihenfolge nach F-15.

**Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: Die Betreiberentscheidung vom 2026-11-27 lautet „die Vorprüfung zeigt das Ergebnis“. F-17 acceptance-6 zeigt jede fehlgeschlagene Vorprüfung mit Code und Einträgen in der Importliste (Entscheidung D1); die abgelehnten Dokumente aus F-32 erscheinen dort ohne eigenes Kriterium in F-17. F-32 ist vor F-17 fertig und allein über die Statuskarte prüfbar. [Seit der Teilung von F-17: Die Importliste liefert F-33, gemeint ist F-33 acceptance-2.]

**Ältere Archive (drift, revisit-after, nicht blockierend).** Established: §8.4 Schritt 1 (`REQ-056:379`) verspricht, ältere Archive durch Migrationen zu heben; der Dienst lehnt nur ein neueres Archiv ab (`tenant_export_service.py:869-870`) und hebt nichts. Unestablished: ob es Archive gibt, deren Datensätze nach einer seitherigen Migration nicht mehr zum Modell passen; das würde ein Import eines solchen Archivs zeigen (nicht durchgeführt). Folge dieses Features: Ein solches Archiv wird künftig mit Angabe der Datensätze abgelehnt, statt mit später brechenden Datensätzen importiert zu werden. Das Heben selbst gehört nicht zu F-32 (siehe „Out of scope“ und „Offene Punkte“).

**Kanten (prior-art, proceed).** Established: Kanten prüft der Import über `remap_edge(dry_run=True)` (`tenant_import_engine.py:179-182`) und die Liste der importierbaren Kanten (REQ-056 §8.4 Schritt 2). Unestablished: ob es für Kanten Datenmodelle gibt; das würde eine Suche nach Kanten-Modellen unter `src/backend/app/domain/models/` zeigen (nicht durchgeführt). F-32 prüft Dokumente der Collections; Kanten bleiben bei den bestehenden Regeln.

**Ergebnis:** Die beiden Überschneidungen sind begründet aufgelöst, der Befund zu älteren Archiven blockiert nicht; F-32 ist `ready`.

### Agentenlauf 2026-11-28

Lauf des `feature-consistency-reviewer` (`agent_version: feature-consistency-reviewer@unknown`) am 2026-11-28 gegen den Stand `3a8c33e43`, von der Hauptsitzung gestartet; die Befunde stehen sinngemäß im Frontmatter. Damit ist der im manuellen Durchgang vermerkte Workflow-Health-Befund erledigt. Die Einarbeitung unten stammt vom selben Subagenten wie der manuelle Durchgang; die zitierten Stellen wurden nachgelesen, ein Test lief nicht. Nach dieser Einarbeitung lässt die Hauptsitzung den Agenten erneut laufen.

Der Block des manuellen Durchgangs vom 2026-11-28, wie er bis zu diesem Lauf im Frontmatter stand:

```yaml
consistency_check:
  performed_at: 2026-11-28
  agent_version: manual-2026-11-28
  findings:
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:480
      resolution: proceed
      evidence: "§12.4 'Präpariertes Archiv beim Import': '… Schema-Validierung jedes Dokuments gegen das Domänenmodell (422) …' gegen tenant_export_service.py:52-53 'Not part of this slice (REQ-056 AK Stand, #2138): importing readings, the per-document validation against the domain models, and the frontend.' — dieses Feature schließt die Lücke; acceptance-5 zieht §12.4 nach."
    - kind: prior-art
      target: src/backend/app/domain/engines/tenant_import_engine.py:167
      resolution: proceed
      evidence: "validate_documents (:167-183) prüft je Zeile nur Besitz (_check_ownership) und Verweise (remap_document) und je Kante remap_edge(dry_run=True); _verified_archive ruft es in :859 auf (tenant_export_service.py:847-882). Die Dokumentprüfung kommt als weiterer Schritt in dieselbe Prüfung."
    - kind: prior-art
      target: src/backend/tests/unit/guards/test_tenant_export_covers_the_inventory.py:105
      resolution: proceed
      evidence: "Die Zuordnung Collection → Modell existiert nur zur Testzeit: Fixture models_by_collection (:105-119) leitet sie über build_inventory ab (Import :43; collection_models in test_tenant_scoped_reads_are_derived.py:430), _MODELS_BY_HAND (:48-61) nennt zwei Collections ohne gebundenes Modell (diagnosis_requests, care_events); test_every_exported_collection_has_a_model_or_a_reason (:161-163). Das Feature braucht dieselbe Zuordnung zur Laufzeit (acceptance-4)."
    - kind: prior-art
      target: src/backend/tests/integration/test_tenant_export_roundtrip.py:498
      resolution: proceed
      evidence: "Der Roundtrip validiert heute genau ein gutes Dokument nachträglich: 'Location.model_validate(imported_bed).soil_hazards' (:498). Enum-Felder, die als Rohdokument reisen: plant_instance.py:47-62 (failure_cause_class, failure_pathogen, failure_pathogen_source), site.py:722 (soil_hazards)."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "Die abgelehnten Dokumente stehen im Detailfeld des Import-Datensatzes, das F-15 acceptance-6 einführt (heute nur fehlende Katalogeinträge, tenant_export_service.py:1105); Begründung in den Consistency notes."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "'Die Vorprüfung zeigt das Ergebnis': F-17 acceptance-6 zeigt eine fehlgeschlagene Vorprüfung mit Code und Einträgen in der Importliste; Begründung in den Consistency notes."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:379
      resolution: revisit-after Betreiber benennt einen Besitzer für das Heben älterer Archive (nicht blockierend, siehe Offene Punkte)
      evidence: "§8.4 Schritt 1: 'ältere Archive werden durch die Migrationen gehoben, die sich auf Archive anwenden lassen' gegen tenant_export_service.py:869-870, das nur ein neueres Archiv ablehnt; ein älteres wird unverändert geprüft."
```

**Befunde und Einarbeitung** (der Agent hält F-32 für `ready`, mit zwei Präzisierungen).

- **Kanten (drift, proceed).** Established: Kanten werden nach `remap_edge` ohne Modellprüfung geschrieben (`tenant_export_service.py:1212-1227`). Die Frage aus dem manuellen Durchgang, ob es Kanten-Modelle gibt, hat der Agentenlauf beantwortet: nein. acceptance-4 gilt für Dokument-Collections und nennt Kanten als ausdrückliche Ausnahme; acceptance-5 trägt die Ausnahme in REQ-056 §12.4 ein, das heute „jedes Dokuments“ sagt.
- **`tenant.json` (drift, proceed).** Established: Name, Beschreibung und Einstellungen gehen beim Anlegen roh in `Tenant(...)` (`tenant_service.py:419-428`); ein Fehler dort ist im Lauf ein allgemeiner Fehler (`IMPORT_FAILED`, `tenant_export_service.py:1037-1039`). Neues Kriterium acceptance-6 zieht die Prüfung in die Hintergrundprüfung.
- **Mehrere Modelle je Collection (prior-art, proceed).** Festlegung der Planung: Jedes an die Collection gebundene Modell muss den Datensatz annehmen. Grund: Das Feature soll verhindern, dass ein späterer Lesezugriff bricht, und jeder Lesepfad nutzt eines dieser Modelle. Nimmt ein Modell echte, gültige Datensätze der Collection nicht an (etwa ein Teilmodell), wird es einzeln mit Begründung ausgenommen, wie eine Collection ohne Modell (acceptance-4).
- **Strukturstrenge Modelle (prior-art, proceed).** Established: `LocationLighting` verbietet unbekannte Felder (`site.py:588`). Unestablished: ob Datensätze im Bestand der Installation an einem solchen Modell scheitern; das zeigt nur der Lauf mit einem echten Garten (nicht durchgeführt). Er liegt jetzt vor dem Merge von F-32.

**Ergebnis:** beide Präzisierungen eingearbeitet; F-32 bleibt `ready`.

### Stand nach dem zweiten Agentenlauf (2026-11-28)

Zweiter Lauf des `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) am 2026-11-28 gegen `22ec65763`, von der Hauptsitzung gestartet; dazu ein Versuch der Hauptsitzung gegen TimescaleDB und drei Betreiberentscheidungen. Die Befunde beider Agentenläufe stehen im Frontmatter (angehängt, nicht ersetzt). Die Einarbeitung stammt vom Subagenten der Planungssitzung; die zitierten Stellen wurden nachgelesen, ein eigener Test lief nicht.

- **Stiller Ersatz in `import_archive` (drift, proceed; Vorgabe der Hauptsitzung).** Established: Heute wird eine Beschreibung, die kein Text ist, zu `None`, Einstellungen, die kein Objekt sind, zu `{}` (`tenant_export_service.py:1162-1165`), ein fehlender Name zu „Imported garden“ (`:1182`). acceptance-6 macht daraus eine Ablehnung mit Code und Feldname. Das ist eine Verhaltensänderung: Ein Archiv, das bisher mit Ersatzwerten importiert wurde, wird künftig abgelehnt.
- **Mehrere Modelle je Collection.** Festgelegt ist „jedes gebundene Modell muss passen“ (acceptance-1; Abschnitt „Agentenlauf 2026-11-28“). Der Satz im manuellen Durchgang, das sei Sache der Umsetzung, ist überholt und dort vermerkt.
- **Wo das Ergebnis angezeigt wird.** Seit der Teilung von F-17 zeigt F-33 acceptance-2 die fehlgeschlagene Vorprüfung in der Importliste; F-32 bleibt allein über die Statuskarte prüfbar. Die beiden Overlap-Befunde des ersten Agentenlaufs (F-15, damals F-17) sind im Frontmatter nachgetragen; ihre Begründung steht im manuellen Durchgang.

**Ergebnis:** eingearbeitet; F-32 ist `ready`, vorbehaltlich des dritten Agentenlaufs.

## Risks

- **Altbestand.** Datensätze, die diese Installation heute fehlerfrei liest, könnten an einer strengen Prüfung scheitern, vor allem an Modellen, die unbekannte Felder verbieten (`site.py:588`); dann ließe sich ein eigenes Backup nicht mehr einspielen. acceptance-3 und der Lauf mit einem echten Garten vor dem Merge sichern das ab; Testdaten bilden nicht jede historische Form ab.
- **Alle Modelle müssen passen.** Die Regel kann einen gültigen Datensatz ablehnen, wenn ein an die Collection gebundenes Modell nur eine Teilmenge der Datensätze beschreibt; solche Modelle müssen einzeln ausgenommen werden.
- **`tenant.json` wird streng.** Ein Archiv ohne Namen oder mit Einstellungen falschen Typs wurde bisher mit Ersatzwerten importiert und wird künftig abgelehnt (acceptance-6).
- **Laufzeit.** Ein Archiv darf bis zu 1 000 000 Zeilen tragen (`tenant_export_engine.py:1012`); die Prüfung jeder Zeile verlängert die Hintergrundprüfung und muss das Lebenszeichen des Laufs setzen, sonst beendet der Stale-Sweep ihn nach sechs Stunden (`tenant_export_service.py:168`).
- **Unbekannte Felder.** Modelle, die unbekannte Felder ignorieren, lassen zusätzliche Felder eines veränderten Archivs durch; die Prüfung weist nur ungültige Werte bekannter Felder ab.
- **Kanten** werden weiter ohne Modellprüfung geschrieben; ein verändertes Archiv kann dort zusätzliche Felder einspielen.
- Ältere Archive, die bisher mit latent fehlerhaften Datensätzen importiert wurden, werden nach dieser Änderung abgelehnt.

## Out of scope

- Heben älterer Archive durch Migrationen (REQ-056 §8.4 Schritt 1) — hat weiterhin keinen Besitzer.
- Entfernen unbekannter Felder aus Datensätzen und Prüfung von Kanten gegen ein Modell (Kanten haben keine Datenmodelle; ausdrückliche Ausnahme in acceptance-4).
- Die Datenschutz-Befunde zum Archiv (eigene Lane, Betreiberentscheidung 2026-11-27).
- Reparieren eines abgelehnten Archivs; der Admin erhält die Liste der Datensätze, nicht ein Werkzeug.

## References

- Issue #3140, roadmap item R-19; REQ-056 §12.4
- `project/requirements/tenant-export-import-remainder.md` (R18, ergänzt 2026-11-28)
- Setzt F-15 voraus (Hintergrundprüfung, Detailfeld am Import-Datensatz); F-33 zeigt das Ergebnis in der Importliste

## Betreiberentscheidungen 2026-11-27

- **Die Dokumentvalidierung nach REQ-056 §12.4 wird ein eigenes kleines Feature in R-19.** Die Schema-Prüfung jedes Dokuments läuft im Hintergrundprozess (Worker), die Vorprüfung zeigt das Ergebnis; ein manipulierter Wert, etwa ein Enum außerhalb des Wertebereichs, wird abgelehnt statt geschrieben. Die Frage stand im Re-Run vom 2026-11-27 in `tenant-import-preflight.md`; die Alternative „dokumentierter Ausschluss mit Korrektur von §12.4“ ist verworfen.
- Reihenfolge der Umsetzung: F-15 → F-32 → F-17 → F-16.
- Es gibt nur eine Installation; die Datenschutz-Befunde zum Archiv laufen in einer eigenen Lane.

## Betreiberentscheidungen 2026-11-28

Keine eigene Entscheidung zu F-32. Aus der Runde vom 2026-11-28 gilt für den ganzen Sprint: Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend.

Dritte Runde am selben Tag:

- Vorgabe der Hauptsitzung zu acceptance-6: Aus dem stillen Ersatz von Angaben in `tenant.json` wird eine Ablehnung mit Code und Feldname.
- Teilung von F-17 und F-16 (Entscheidung A): neue Reihenfolge F-15 → F-32 → F-17 → F-33 → F-16 → F-34.

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-32.

- **Ältere Archive.** Nach F-32 wird ein Archiv abgelehnt, dessen Datensätze nicht mehr zum heutigen Modell passen, etwa ein Backup von vor einer Migration, die einen Wert abgeschafft hat. Vorher wurde es importiert und brach beim späteren Lesen. Das Heben solcher Archive (REQ-056 §8.4 Schritt 1) besitzt kein Feature. Blockiert niemanden in Sprint 5; der Betreiber sollte entscheiden, ob daraus ein Roadmap-Eintrag wird oder §8.4 Schritt 1 gestrichen wird.
- **Collections ohne Modell.** Heute betrifft das `diagnosis_requests` (kein Schreibpfad) und `care_events` (Modell vorhanden, im Guard noch nicht gebunden; `test_tenant_export_covers_the_inventory.py:48-61`). Festlegung der Planung: Sie bleiben mit Begründung ausgenommen und werden wie heute importiert; ob `care_events` gebunden wird, entscheidet die Umsetzung. Blockiert niemanden.
- **„Alle Modelle müssen passen“** ist eine Festlegung der Planung, keine Betreiberentscheidung. Blockiert niemanden.
