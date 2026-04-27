# Anforderungs-Widerspruchsanalyse — Kamerplanter
**Erstellt:** 2026-04-26
**Analysierte Dokumente:** 48 (32 REQ + 13 NFR + 1 stack.md, zzgl. 18 UI-NFRs)
**Gefundene Anforderungen (relevant für Analyse):** ~160 funktionale Anforderungen, ~90 non-funktionale Anforderungen
**Widersprüche gesamt:** 22 (4 kritisch, 7 hoch, 7 mittel, 4 niedrig)

---

## Resolution-Status (Stand 2026-04-27)

Alle 22 Widersprüche wurden bearbeitet. Übersicht:

| Status | Anzahl | Bedeutung |
|--------|--------|-----------|
| ✅ Resolved | 18 | Direkt in Specs eingearbeitet |
| ✅ Resolved via ADR | 3 | Persistente Architekturentscheidung in `spec/decisions/` |
| ⚠️ Misclassified | 1 | W-020 — REQ-009-Spec existierte bereits bei Berichts-Erstellung; konsolidiert via v2.1 |

| ID | Schweregrad | Status | Wo behandelt |
|----|-------------|--------|--------------|
| W-001 | KRITISCH | ✅ Resolved | REQ-027 v1.4 §6.1.1 (AI-Provider-Guard) |
| W-002 | KRITISCH | ✅ Resolved | REQ-025 v1.3 §3.1 (Tombstone-Pseudonymisierung) + NFR-011 v1.4 R-06 |
| W-003 | KRITISCH | ✅ Resolved | REQ-003 v2.5 §3 (Run-Membership-Guard) + REQ-013 v2.3 |
| W-004 | KRITISCH | ✅ Resolved | REQ-023 v1.10 §3.2a (Refresh-Token Family + Grace-Window) + UI-NFR-012 v2.2 R-049a/b |
| W-005 | HOCH | ✅ Resolved | UI-NFR-012 v2.2 R-020a (Begründung präzisiert) |
| W-006 | HOCH | ✅ Resolved via ADR | **ADR-002** Tenant-Species im Knowledge Service + Export — REQ-001 v4.1, REQ-024, REQ-025 v1.3, REQ-031 v2.2 |
| W-007 | KRITISCH (im Top-5) | ✅ Resolved | REQ-025 v1.3 §3.1 (Phase 0 Storage-Cleanup) + NFR-013 v1.1 §4.2/§6.2 |
| W-008 | HOCH | ✅ Resolved | stack.md / NFR-011 v1.4 / NFR-012 / CLAUDE.md (Valkey 8.0+ als primär, Redis-Wire-kompatibel) |
| W-009 | HOCH | ✅ Resolved via ADR | **ADR-001** Karenz-Gate für detachte PlantInstances — REQ-007 v2.4, REQ-010 v1.1, REQ-013 v2.3, NFR-011 v1.4 |
| W-010 | HOCH | ✅ Resolved | REQ-022 v2.5 §1 (Run-Owned CareProfile + Detach-Snapshot) + REQ-013 v2.3 |
| W-011 | HOCH | ✅ Resolved | UI-NFR-012 v2.2 R-042a/R-042b (KI-Features Online-only) + REQ-031 v2.2 §1 |
| W-012 | MITTEL | ✅ Resolved | REQ-027 v1.4 §1 (Klarstellungs-Tabelle DSGVO-Maßnahmen) |
| W-013 | MITTEL | ✅ Resolved | CLAUDE.md (Mischsequenz via `mixing_priority`-Feld, nicht hard-coded) |
| W-014 | MITTEL | ✅ Resolved via ADR | **ADR-003** Sensor-Retention für Perennials — NFR-011 v1.4 R-14, REQ-002 v4.3 (`data_classification`), REQ-003 v2.5 (`sensor_aggregates`), REQ-005 v2.7 |
| W-015 | MITTEL | ✅ Resolved | REQ-027 v1.4 §2.1 (Service Accounts deaktiviert im Light-Modus) + REQ-023 v1.10 §3.7 |
| W-016 | MITTEL | ✅ Resolved | UI-NFR-003 v1.1 §4 (Bundle-Budget auf 300KB harmonisiert) |
| W-017 | MITTEL | ✅ Resolved | REQ-015 v1.6 CF-007 + REQ-027 v1.4 §6.1/§6.2 (iCal-Token aktiv im Light-Modus) |
| W-018 | MITTEL | ✅ Resolved | NFR-008 v1.1 §2.2/§2.3 (Coverage-Schwellen messbar + CI-Gate) |
| W-019 | NIEDRIG | ✅ Resolved | UI-NFR-011 Kiosk-Modus → `UI-NFR-019_Kiosk-Modus.md` (v1.2) umbenannt; alle Verweise umgebogen |
| W-020 | NIEDRIG | ⚠️ Misclassified → ✅ Resolved | **Spec existierte bereits**: REQ-009 v2.0 war 1373 Zeilen lang, vom Bericht aber als „nicht spezifiziert" markiert. Konsolidiert zu **v2.1** mit Cross-Refs zu jüngeren Specs (REQ-021/022/024/027/031/032, UI-NFR-019) |
| W-021 | NIEDRIG | ✅ Resolved | REQ-014 v1.6 §1 (Wasserquellen-Kaskade auf REQ-004 `WaterMixCalculator` delegiert) |
| W-022 | NIEDRIG | ✅ Resolved | NFR-001 §6.1 + §11.2 (python-jose-Verweis durch Authlib ersetzt; DEPRECATED-Markierung verschärft) |

> **Hinweis zu Versions-Spalten:** Wo eine Spec in mehreren Schritten erhöht wurde (z.B. NFR-011 1.0→1.1→1.2→1.3→1.4), zeigt diese Tabelle die **finale** Version nach allen Resolutions. Der einzelne Fix-Eintrag in der Spec selbst ist im Changelog der Spec datiert nachvollziehbar.

**Workflow-Notiz:** Drei Wegwerf-Arbeitsdokumente wurden während der Bearbeitung erstellt und am Ende gelöscht (`spec-updates-2026-04-26.md` für die 5 kritischen Fixes, `pending-decisions-2026-04-27.md` für die 7 Sammel-Themen). Die persistente Form lebt in den eigentlichen Specs + den 3 ADRs.

**Verbleibende offene Themen:** Keine Widersprüche aus diesem Bericht offen. Die in Empfehlungen §3 erwähnten Folgevorhaben (REQ-009 Vollausbau, NFR-013 Tracked-State, Mobile-App) sind außerhalb der Widerspruchsanalyse.

---

## Executive Summary

Die Anforderungsbasis von Kamerplanter ist insgesamt kohärent und zeigt eine durchdachte Architektur. Die kritischsten Probleme konzentrieren sich auf drei Bereiche: (1) der konzeptionelle Konflikt zwischen Multi-Tenant-Pflicht und angestrebter Auth-Freiheit im Light-Modus ist zwar explizit adressiert, aber in zwei Spezifikationen unterschiedlich beschrieben; (2) die duale Phasenzuständigkeit zwischen REQ-003 und REQ-013 v2.0 ist architektonisch aufgelöst, aber in den AQL-Beispielen nicht vollständig konsistent; (3) die PWA-Offline-Anforderung (UI-NFR-012) steht in einem fundamentalen, impliziten Widerspruch zum kurzen JWT-Access-Token-TTL (15 Minuten aus REQ-023) in Verbindung mit Offline-Szenarien im Growraum. Sofortiger Klärungsbedarf besteht bei W-001 (KI-Cloud-Processing im Light-Modus), W-004 (Token-Lifetime vs. Offline) und W-008 (Stack.md nennt Valkey, alle anderen Dokumente Redis).

---

## Kritische Widersprüche

### W-001: KI-Cloud-Provider im Light-Modus — Consent ohne User
**Typ:** Impliziter Widerspruch (technisch nicht erfüllbar)
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `REQ-031 §1` (v2.0) in `spec/req/REQ-031_KI-Assistent-Pflanzenberatung.md`: "Cloud-Provider sind optional und erfordern explizite Einwilligung (REQ-025, neuer Consent-Purpose `ai_cloud_processing`)."
- `REQ-027 §2.1` in `spec/req/REQ-027_Light-Modus.md`: "KI-Verhalten im Light-Modus: Im Light-Modus laufen KI-Anfragen ausschließlich über System-Default-Provider (typischerweise lokales Ollama). `AI_PUBLIC_PROVIDER_KEY` muss auf einen lokalen Provider zeigen — Cloud-Provider sind im Light-Modus NICHT verwendbar, weil kein Nutzer einen Consent erteilen kann."
- `REQ-025 §5` in `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md`: Consent-Seed-Daten definieren `ai_cloud_processing` als erfordert für Cloud-KI.

**Konflikt:** REQ-031 v2.0 verbietet Cloud-Provider im Light-Modus korrekt, weil kein Consent-Mechanismus existiert. Jedoch enthält REQ-027 §2.1 die Aussage "Cloud-Provider sind im Light-Modus NICHT verwendbar" als rein dokumentarischen Hinweis, ohne dass ein technischer Enforcement-Mechanismus spezifiziert ist. Es fehlt eine explizite Backend-Guard-Anforderung: Wenn `KAMERPLANTER_MODE=light` UND `AI_FEATURES_ENABLED=true` UND ein Operator irrtümlich einen Cloud-Provider als `AI_PUBLIC_PROVIDER_KEY` konfiguriert, dann werden Anfragen an Cloud-Provider ohne Consent gesendet. Kein Spec-Dokument verlangt explizit einen Startup-Check, der diese Fehlkonfiguration verhindert.

**Auswirkung:** DSGVO-Verstoß durch Übermittlung von Anfragen (inkl. möglicher Pflanzendaten) an Drittland-Provider ohne Einwilligung. Direkte Haftungsexposition für den Betreiber.

**Lösungsoptionen:**
1. **Technischer Enforcement (empfohlen):** REQ-027 muss eine Startup-Validierung fordern: Wenn `KAMERPLANTER_MODE=light` und `AI_FEATURES_ENABLED=true`, muss geprüft werden, ob der konfigurierte Provider `provider_type='local'` hat. Andernfalls: Startup-Fehler mit expliziter Fehlermeldung. Knowledge Service muss Konfiguration ablehnen.
2. **Dokumentarischer Ansatz:** Deployment-Dokumentation prominent warnen + Default `AI_FEATURES_ENABLED=false` im Light-Modus setzen. Risiko: Operator-Fehler möglich.

---

### W-002: DSGVO-Volltext-Audit-Log vs. Recht auf Löschung
**Typ:** Impliziter Widerspruch (CAP-ähnlich: Vollständigkeit vs. Löschbarkeit)
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `REQ-025 §3.1` (`ErasureEngine.DELETE_ORDER`): "Phase 3: User selbst (zuletzt)" — der Account wird hart gelöscht.
- `NFR-011 §2.1 R-06`: "Erasure-Audit-Logs (`erasure_requests`) — 1 Jahr nach Abschluss — Hard-Delete."
- `REQ-025 §3.5 Celery-Task execute_scheduled_erasures`: Der Task löscht u.a. die Collection `erasure_requests`, aber erst nach 1 Jahr.
- `REQ-025 §6 AK-10`: "Erasure-Audit-Log wird für 1 Jahr aufbewahrt."

**Konflikt:** Die `erasure_requests`-Collection enthält `user_key: str` als explizites Referenzfeld. Wenn ein User durch die `execute_scheduled_erasures`-Task endgültig gelöscht wird (Hard-Delete nach 90 Tagen), bleibt der `user_key` für bis zu 1 Jahr in `erasure_requests` gespeichert — als direkter personenbezogener Identifikator. Dies ist kein anonymisierter Verweis (im Gegensatz zu den Erntedaten, die explizit anonymisiert werden). Der `user_key` erlaubt zwar keinen Rückschluss auf die Person mehr (wenn der User-Datensatz gelöscht ist), aber wenn E-Mail-Hashes zur Duplikatprüfung behalten werden (NFR-011 R-01: "E-Mail-Hash für Duplikatprüfung behalten"), besteht in Kombination ein potentielles Pseudonymisierungs-Problem.

**Auswirkung:** Potenzieller DSGVO Art. 5(1)(e) Verstoß (Speicherbegrenzung). Datenschutz-Aufsichtsbehörden könnten die Kombination aus user_key + email_hash als nicht ausreichend anonymisierten Datensatz einstufen.

**Lösungsoptionen:**
1. **Empfohlen:** `user_key` im `erasure_requests`-Dokument nach dem Hard-Delete des Users durch eine UUID-Tombstone ersetzen (Pseudonymisierung). Den `ErasureEngine.DELETE_ORDER` entsprechend anpassen: In Phase 2 wird `user_key` in `erasure_requests` auf `[anon_{hash}]` gesetzt, bevor Phase 3 den User löscht. REQ-025 und NFR-011 ergänzen.
2. **Alternativ:** Audit-Log-Retention auf 30 Tage reduzieren (statt 1 Jahr) und stattdessen nur aggregierte Metriken (Anzahl Löschungen pro Tag) für Compliance behalten.

---

### W-003: Phasensteuerung — doppelte Zuständigkeit REQ-003 vs. REQ-013
**Typ:** Scope-Widerspruch / Eigentumsfrage
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `REQ-003 §2` (v2.3), Edge Collection `current_phase`: "current_phase: planting_runs|plant_instances → growth_phases (Dual-Support: Run primär, standalone Plant als Fallback; REQ-013 v2.0)"
- `REQ-013 §1` (v2.0): "PlantingRun besitzt Phasen, Aufgaben, Nährstoffpläne, Pflege, IPM-Inspektionen und Ernte." und "Phase: vom Run (run.current_phase_key)"
- `REQ-013 §2 PlantingRun.Properties`: `current_phase_key: Optional[str]` auf dem Run-Dokument (denormalisiert).
- `REQ-013 §2 PlantInstance.Properties` (innerhalb eines Runs): "Felder wie `current_phase_key`, `current_phase_started_at` existieren weiterhin auf dem Model für den Standalone-Modus, werden aber ignoriert solange die Pflanze Mitglied eines aktiven Runs ist."

**Konflikt:** REQ-013 v2.0 spezifiziert klar, dass der Run der Phaseneigentümer ist. REQ-003 hat das Dual-Support-Modell als Annotation eingebaut, aber die AQL-Beispiellogik in REQ-003 (Auto-Transition-Kandidaten) iteriert über `planting_runs` UND `plant_instances` mit identischem Mechanismus. Die Phasenübergangs-Engine (REQ-003 `PhaseTransitionEngine`) ist nicht spezifiziert, wie sie entscheidet, ob ein Transition-Request für einen Run oder eine standalone Plant gilt — insbesondere wenn eine PlantInstance-Phase irrtümlich direkt angesprochen wird (z.B. via direkter API-Endpoint-Nutzung), obwohl die Pflanze in einem aktiven Run ist.

**Spezifisches Problem:** Es existiert keine Anforderung, die explizit verbietet, `PUT /plant-instances/{key}/phase` auf einer Run-gebundenen Plant aufzurufen. REQ-013 sagt "keine Einzelbearbeitung möglich", aber REQ-003 spezifiziert keinen Guard, der das technisch durchsetzt. Das führt zu einem Datenkonsistenz-Risiko: `plant_instance.current_phase_key` könnte von `planting_run.current_phase_key` abweichen.

**Auswirkung:** Datenkonsistenzprobleme, falsche Phase-History, potentiell fehlerhafte Karenz-Gates (REQ-010) und Ernte-Freigaben (REQ-007) basierend auf falscher Phasen-Information.

**Lösungsoptionen:**
1. **Empfohlen:** REQ-003 muss explizit definieren: Wenn eine PlantInstance Teil eines aktiven PlantingRuns ist (`run_contains`-Edge mit `detached_at=null`), MUSS jeder direkte Phasenwechsel-Versuch auf der PlantInstance mit HTTP 409 (Conflict) abgelehnt werden: "Phase wird vom PlantingRun verwaltet. Phasenwechsel über den Run-Endpoint auslösen."
2. **Alternativ:** Die `current_phase_key`-Felder auf PlantInstance werden entfernt, wenn die Pflanze einem Run zugewiesen wird (beim Detach wieder gesetzt via Kopie aus Run).

---

### W-004: JWT-Access-Token-TTL 15 Minuten vs. PWA-Offline-Szenario
**Typ:** Impliziter Widerspruch (technisch konfliktär)
**Schweregrad:** KRITISCH

**Betroffene Anforderungen:**
- `REQ-023 §1` (v1.8): "Access Token: 15 Minuten (Memory, Frontend). Automatisch via Refresh Token."
- `UI-NFR-012 §3.9 R-050`: "Während einer Offline-Phase MUSS die App den Nutzer NICHT ausloggen, auch wenn der Access Token abgelaufen ist. Die lokale Authentifizierung MUSS auf dem letzten gültigen Auth-State basieren."
- `UI-NFR-012 §3.9 R-049`: "Wenn der Access Token während einer Offline-Phase abläuft (15 min TTL, REQ-023), MUSS die App beim nächsten Online-Zugriff automatisch einen Token-Refresh versuchen, bevor ein Re-Login erzwungen wird."
- `NFR-007 §2.2`: "Latenz P95 < 500 ms" — impliziert, dass Online-Sync-Versuche schnell antworten müssen.

**Konflikt:** UI-NFR-012 löst das Problem auf Applikations-Ebene korrekt (offline kein Ausloggen, Refresh beim Reconnect). Jedoch fehlt in REQ-023 eine explizite Anforderung an das Backend: Wenn ein Nutzer den Growraum für 4+ Stunden ohne Verbindung betritt und beim Wiederherstellen der Verbindung ein Refresh-Token-Rotation stattfindet, muss das Backend garantieren, dass der Refresh-Endpunkt `POST /auth/refresh` auch nach einer langen Offline-Phase (bis zu 30 Tagen bei `remember_me=true`) ohne Race-Condition funktioniert. Das Problem: Wenn zwei Geräte dasselbe Refresh-Token teilen (Tablet im Growraum + Desktop), kann Token-Rotation zu einem "Used Token"-Fehler führen, der einen Re-Login erzwingt — obwohl UI-NFR-012 R-050 dies explizit verbietet.

**Auswirkung:** Datenverlust: Offline erfasste Messwerte können beim Sync nicht zugeordnet werden, wenn ein erzwungener Re-Login die App-State löscht. Frustrierendes UX im Kern-Nutzungsszenario (Growraum im Keller).

**Lösungsoptionen:**
1. **Empfohlen:** REQ-023 muss eine explizite Anforderung für "Refresh-Token-Replay-Tolerance" ergänzen: Bei Offline-Szenarien muss das Backend ein "Grace Window" von X Minuten akzeptieren, in dem ein bereits rotiertes Refresh-Token noch einmal verwendet werden kann (Idempotenz-Key basierend auf device_id). Alternativ: Session-Tokens sind gerätgebunden (device fingerprint).
2. **Alternativ:** UI-NFR-012 R-048 präzisieren: Access Token wird in IndexedDB persistiert und für Offline-Auth genutzt — kein Backend-Kontakt nötig. Sicherheitsrisiko: abgelaufenes Token in lokalem Storage.
3. **Pragmatisch:** Growraum-Nutzern wird empfohlen, `remember_me=true` zu setzen und ein einziges Gerät pro Instanz zu nutzen.

---

## Hohe Widersprüche

### W-005: Phasen-Rückwärts-Transition — REQ-003 vs. Offline-Schutz
**Typ:** Direkter Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `REQ-003 §2` Transition-Engine-Kommentar: "Rückwärts-Kompatibilität: Support für Spezies ohne definierte Phasen" und `is_cycle_restart: bool` auf `phase_transition_rules` — erlaubt Rückwärts-Transition explizit für Dauerkulturen (Seneszenz → Dormanz).
- `UI-NFR-012 §3.3a R-020a`: "Phasenwechsel DÜRFEN NICHT offline ausgeführt werden — die Phasen-Zustandsmaschine verbietet Rückwärts-Transitionen, die serverseitig validiert werden. Offline könnte Last-Write-Wins eine verbotene Rückwärts-Transition erzwingen."

**Konflikt:** UI-NFR-012 begründet das Online-Pflicht für Phasenwechsel explizit mit "verbotenen Rückwärts-Transitionen". REQ-003 erlaubt jedoch für Dauerkulturen (Perennials) ausdrücklich Rückwärts-Transitionen via `is_cycle_restart: true`. Die Begründung in UI-NFR-012 ist damit für Dauerkultur-Phasenwechsel sachlich falsch — was jedoch die Anforderung selbst (Online-Pflicht für alle Phasenwechsel) nicht zwingend falsifiziert. Es besteht aber eine Inkonsistenz in der Begründungslogik, die bei der Implementierung zu falschen Entscheidungen führen kann.

**Auswirkung:** Entwickler könnten aus der fehlerhaften Begründung schlussfolgern, Rückwärts-Transitionen grundsätzlich zu verbieten — was bei Perennials fachlich falsch wäre (Dormanz nach Seneszenz ist korrekt und gewünscht).

**Lösungsoptionen:**
1. UI-NFR-012 R-020a Begründung korrigieren: "Phasenwechsel erfordern serverseitige Validierung zur Durchsetzung der phasenspezifischen Regeln (Reihenfolge, erlaubte Transitionen, inklusive `is_cycle_restart`-Ausnahmen für Dauerkulturen)."
2. REQ-003 explizit dokumentieren, welche Transitionen auch rückwärts erlaubt sind, und diese in einer Whitelist führen.

---

### W-006: Stammdaten-Scoping — Tenant-eigene Species vs. Globale Standardisierung
**Typ:** Scope-Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `REQ-001 v4.0 §1`: `origin: Literal['system', 'enrichment', 'import', 'tenant']` — Tenants können eigene Species anlegen.
- `REQ-024 v1.3 §1` (Platform-Tenant & Stammdaten-Scoping): "Ressourcen gehören immer zu genau einem Tenant (kein Cross-Tenant-Sharing)" und "tenant_has_access-Kanten für Sichtbarkeitssteuerung globaler Stammdaten."
- `REQ-013 v2.0 §1` PlantingRun: `species_key: str` (Referenz auf Species) — ohne Einschränkung auf globale oder tenant-eigene Species.
- `REQ-017` (Vermehrungsmanagement, nicht vollständig gelesen): Lineage-Graph nutzt `descended_from`-Edges zwischen PlantInstances verschiedener Species.

**Konflikt:** Eine tenant-eigene Species (`origin='tenant'`) hat eine `tenant_key`-Zuordnung und ist nur innerhalb dieses Tenants sichtbar. Wenn ein Nutzer eine PlantInstance mit einer tenant-eigenen Species anlegt und dann einen Datenexport (REQ-025 Art. 15/20) abruft, enthält der Export `species_key`, aber der Knowledge Service (REQ-031) kann diese Species nicht auflösen (sie ist nicht in der globalen Wissensbasis). Zudem: Wenn ein KA-Admin eine tenant-eigene Species "promotet" (zu `origin='system'`), ändern sich alle bestehenden `species_key`-Referenzen nicht — aber die Species ist nun für alle Tenants sichtbar, während zugehörige PlantInstances nur im ursprünglichen Tenant liegen. Die REQ-025 Export-Manifest enthält keine Logik, die auf tenant-eigene Species hinweist.

**Auswirkung:** Unvollständige Datenexporte (Art. 15 DSGVO), fehlerhafte KI-Kontextualisierung, potentielle Promotion-Race-Conditions.

**Lösungsoptionen:**
1. REQ-025 `DataExportEngine.USER_DATA_MANIFEST` um `tenant_species_config`-Collection ergänzen, die tenant-eigene Species-Overlays und Origins enthält.
2. REQ-031 `KnowledgeServiceAdapter` muss tenant-eigene Species als Fallback aus ArangoDB statt pgvector abrufen — oder explizit als "nicht im Wissenssystem" markieren.
3. Promotion-Workflow in REQ-001 muss einen Lock-Mechanismus definieren, der verhindert, dass während der Promotion neue Referenzen auf die zu promotende Species entstehen.

---

### W-007: Object-Storage-Adapter (NFR-013) vs. DSGVO-Löschung (REQ-025)
**Typ:** Impliziter Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `NFR-013 §1` (v1.0): Definiert Object-Storage-Adapter für Binärdaten (Fotos, Exports, Importe). Dateipfad-Schema: `/{tenant_key}/{entity_type}/{entity_key}/{filename}`.
- `REQ-025 §3.1 ErasureEngine.DELETE_ORDER`: Enthält keine Referenz auf Object-Storage-Bereinigung. Delete-Reihenfolge endet mit "users" Collection — Dateisystem/S3-Objekte werden nicht erwähnt.
- `REQ-025 §6 AK-08`: "Erntedaten und Behandlungsanwendungen werden anonymisiert, nicht gelöscht." — aber zugehörige Fotos (in S3/Object-Storage) sind nicht adressiert.
- `NFR-013 §1`: "bei Tenant-Löschung deterministisch entfernt wird" — Löschung bei Tenant-Löschung spezifiziert, aber nicht bei User-Löschung.

**Konflikt:** REQ-025 definiert den Löschprozess für ArangoDB-Dokumente vollständig, aber ignoriert vollständig die in NFR-013 eingeführte Object-Storage-Schicht. Wenn ein Nutzer Fotos zu Tagebuch-Einträgen (REQ-013), IPM-Inspektionen (REQ-010) oder Ernten (REQ-007) hochlädt und anschließend einen Löschantrag stellt (Art. 17 DSGVO), werden die ArangoDB-Dokumente korrekt gelöscht oder anonymisiert — aber die zugehörigen Binärdaten in S3/lokalem Dateisystem bleiben bestehen. Speziell problematisch: Fotos können Persönlichkeitsrechte berühren (Fotos von Pflanzen in privaten Räumen, die den Wohnraum zeigen).

**Auswirkung:** DSGVO Art. 17 Verstoß: Löschrecht wird für Binärdaten nicht erfüllt. Potenziell dauerhaftes Verbleiben personenbezogener Fotos nach Account-Löschung.

**Lösungsoptionen:**
1. **Empfohlen:** REQ-025 `ErasureEngine` muss um eine Phase 0 ("Storage Cleanup") ergänzt werden: Vor der ArangoDB-Löschung werden alle Object-Storage-Referenzen (`photo_refs`-Felder in allen Collections) gesammelt und via `IStorageAdapter.delete(path)` gelöscht. NFR-013 muss einen `delete_for_user(tenant_key, user_key)` Adapter-Methode spezifizieren.
2. **Bei Anonymisierung:** Fotos, die zu gesetzlich aufbewahrungspflichtigen Datensätzen gehören (Erntedokumentation, IPM-Behandlungen), müssen ebenfalls anonymisiert werden: Datei bleibt, Pfad wird umbenannt (ohne user_key im Pfad), ArangoDB-Referenz angepasst.

---

### W-008: Tech-Stack — Redis vs. Valkey
**Typ:** Direkter Widerspruch (Technologie-Inkonsistenz)
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `spec/stack.md §1.1` Systemarchitektur-Diagramm: "Valkey — Cache" als Technologie im Data Layer.
- `NFR-011 §1` yaml-Header: "Technologie: Python, Celery, ArangoDB, TimescaleDB, **Redis**"
- `NFR-012 §3.4`: "Redis 7.2+" als Heading, explizit: "Rollen: Cache, Celery Broker/Backend, Rate Limiting, OAuth State (TTL)"
- `CLAUDE.md` Projekt-Anweisungen: "Cache/Queue: Redis 7.2+"
- `REQ-023 §3.2` OAuth-State: "Redis (5 Minuten, Redis TTL) — Automatische Bereinigung"
- `NFR-007` referenziert implizit Redis via Celery-Beat

**Konflikt:** `stack.md` nennt "Valkey" (ein Redis-Fork, entstanden nach Redis-Lizenzkontroverse 2024) im Architekturdiagramm, während alle anderen Dokumente (NFR-011, NFR-012, REQ-023, CLAUDE.md) konsistent "Redis 7.2+" nennen. Valkey ist zwar Redis-kompatibel, hat aber eigene Versionierung und Support-Lifecycle. Im Enterprise-Einsatz können Cloud-Provider-SLAs (NFR-012 §3.4 referenziert "ElastiCache/Memorystore") nur für Redis, nicht für Valkey garantiert werden.

**Auswirkung:** Unklarheit bei Infrastruktur-Entscheidungen. Wenn Entwickler stack.md als verbindlich interpretieren, wählen sie Valkey-Images; wenn sie NFR-012 interpretieren, Redis-Images. Divergierende Helm-Charts.

**Lösungsoptionen:**
1. **Empfohlen:** stack.md synchronisieren: Entweder "Redis 7.2+ (oder Valkey als Drop-in-Ersatz)" oder eine bewusste Entscheidung treffen und alle Dokumente anpassen.
2. In NFR-002 (Helm-Charts) eine explizite Entscheidung dokumentieren, welches Image verwendet wird.

---

### W-009: REQ-013 v2.0 "Run-Level IPM" vs. REQ-010 Plant-Level Karenz-Gate
**Typ:** Impliziter Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `REQ-013 v2.0 §2` Edge Collections: "inspected_by (planting_runs|plant_instances → inspections)" und "to_run (treatment_applications → planting_runs) [REQ-013 v2.0: Run-Level (ex to_plant)]"
- `REQ-010 §2` Edge Collections: "inspected_by (planting_runs|plant_instances → inspections)" — Dual-Support ist eingetragen.
- `REQ-007 §1` Karenz-Gate: "KarenzViolationError 422" — aber welche Entity wird als Bezugspunkt verwendet? PlantInstance oder PlantingRun?

**Konflikt:** REQ-013 v2.0 verschiebt Treatment-Applications auf Run-Level (`to_run`-Edge statt `to_plant`). Das Karenz-Gate in REQ-007/REQ-010 prüft, ob aktive IPM-Behandlungen die Ernte blockieren. Wenn eine Behandlung gegen einen Run registriert ist (`to_run`-Edge), aber einzelne Pflanzen aus dem Run detached wurden (standalone PlantInstances), ist unklar: Gilt die Karenzzeit der Run-Behandlung auch für die detachten Pflanzen? REQ-010 definiert `SafetyIntervalValidator`, aber dessen Lookup-Logik (`requires_harvest_delay`-Edge) ist nicht angepasst: Der Edge geht von `treatment_applications → harvests`, aber `harvests` können jetzt auf Run- ODER Plant-Level verweisen. Die Validierungslogik muss beide Pfade abdecken.

**Auswirkung:** Karenz-Gate-Bypass für detachte Pflanzen möglich. Ernten könnten trotz aktiver Run-Level-Behandlung als "sicher" eingestuft werden. Rechtliches Risiko (CanG, PflSchG).

**Lösungsoptionen:**
1. REQ-010 `SafetyIntervalValidator` muss explizit spezifizieren: "Bei Ernte einer standalone PlantInstance, die vor dem Detach Teil eines Runs war, werden auch alle Run-Level-Treatments des vorherigen Runs in die Karenz-Berechnung einbezogen. Lookup: PlantInstance → phase_history → früherer Run → Run-Level-Treatments."
2. REQ-013 v2.0 `detach`-Operation muss die Karenz-relevanten Treatment-Applications auf die standalone PlantInstance kopieren (Snapshot).

---

### W-010: REQ-022 Pflegeerinnerungen vs. REQ-013 Run-Owned Care
**Typ:** Scope-Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `REQ-013 v2.0 §1`: "Care: vom Run (has_care_profile: Run → ...)" — Care-Profile gehören dem Run, nicht einzelnen PlantInstances innerhalb eines Runs.
- `REQ-022 §1`: "Jede `PlantInstance` erhält ein `CareProfile`" — CareProfile ist auf PlantInstance-Ebene spezifiziert.

**Konflikt:** REQ-013 v2.0 definiert Care als Run-Eigenschaft (alle Pflanzen im Run teilen das CareProfile). REQ-022 spezifiziert hingegen CareProfile als PlantInstance-Eigenschaft. Für Runs-Pflanzen entsteht ein Widerspruch: Hat eine PlantInstance, die einem aktiven Run angehört, ein eigenes CareProfile (REQ-022) oder teilt sie das des Runs (REQ-013)? Die Implementierung in MEMORY.md beschreibt REQ-022 als PlantInstance-Ebene, aber das widerspricht dem Run-Ownership-Prinzip.

**Auswirkung:** Duplizierte oder konfliktäre Pflegeerinnerungen für Run-Pflanzen. Verwirrende UX: Ein Nutzer sieht Erinnerungen für einzelne Pflanzen, die eigentlich über den Run verwaltet werden sollten.

**Lösungsoptionen:**
1. REQ-022 muss einen Dual-Support-Abschnitt ergänzen: "Für PlantInstances innerhalb eines aktiven Runs wird das CareProfile des Runs verwendet. Eigene CareProfiles auf PlantInstance-Ebene sind nur für standalone PlantInstances aktiv."
2. Alternativ: CareReminders werden für Runs als Run-Level-Erinnerungen generiert (1 Erinnerung für den Run, nicht N Erinnerungen für N Pflanzen).

---

### W-011: PWA-Offline vs. KI-Feature-Toggle
**Typ:** Impliziter Widerspruch
**Schweregrad:** HOCH

**Betroffene Anforderungen:**
- `UI-NFR-012 §3.3a R-020`: "Pflanzenstammdaten (Arten, Sorten, Standorte) MÜSSEN offline lesbar sein — diese Daten werden beim letzten Online-Zugriff vorab gecacht."
- `REQ-031 §1` (v2.0): "Graceful Degradation: Bei nicht erreichbarem Knowledge Service oder Provider werden regelbasierte Fallback-Tipps generiert."
- `REQ-031 §1.1` Architekturüberblick: Knowledge Service als externes Microservice — eigene PostgreSQL+pgvector-Persistenz, eigenes Helm-Release.

**Konflikt:** UI-NFR-012 fordert Offline-Lesezugriff auf Stammdaten. REQ-031 fordert Graceful Degradation bei Knowledge-Service-Ausfall. Aber: REQ-031 spezifiziert "regelbasierte Fallback-Tipps", ohne zu definieren, welche Daten dafür offline vorhanden sein müssen. Im PWA-Offline-Cache (UI-NFR-012 IndexedDB) sind Species-Stammdaten cached — aber nicht die pgvector-Embeddings oder die Knowledge-Chunks. Der Offline-Cache kann daher keine "regelbasierten Fallback-Tipps" generieren, wenn er keinen Zugriff auf die Wissensgrundlage hat. UI-NFR-012 Tabelle "Offline-fähig vs. Online-only" listet "Echtzeit-Sensorwerte" als Online-only, aber KI-Tipps sind gar nicht erwähnt.

**Auswirkung:** Im Offline-Modus fehlen KI-Tipps vollständig, obwohl REQ-031 Graceful Degradation mit Fallback-Tipps verspricht. Nutzer-Erwartung wird nicht erfüllt.

**Lösungsoptionen:**
1. UI-NFR-012 Offline-Tabelle erweitern: "KI-Tipps" als "Online-only (Fallback: Keine Anzeige oder statischer Hinweis)" klassifizieren.
2. REQ-031 "regelbasierte Fallback-Tipps" präzisieren: Diese Tipps werden aus gecachten Species-Stammdaten und fixen Regeltexten (in IndexedDB) generiert — kein Knowledge-Service nötig. Entsprechende Offline-Caching-Anforderung hinzufügen.

---

## Mittlere Widersprüche

### W-012: REQ-027 Light-Modus — "DSGVO deaktiviert" vs. Wetter-API GPS-Übertragung
**Typ:** Direkter Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `REQ-027 §1`: "Beschreibung: Der Light-Modus ist ein Deployment-Modus [...] Er deaktiviert Auth, Tenants und DSGVO-Consent auf Konfigurationsebene."
- `REQ-025 §9 DP-002`: "GPS-Koordinaten MÜSSEN vor Übertragung an Wetter-APIs auf maximal 2 Dezimalstellen gerundet werden."
- `REQ-005 v2.3` (Wetter-Integration): DWD/OpenWeatherMap/Open-Meteo als Wetter-Datenquellen — GPS-Übertragung bei Freiland-Standorten.
- `REQ-025 §9`: Wetter-APIs sind als "kein Personenbezug" klassifiziert (Koordinaten auf 2 Stellen gerundet).

**Konflikt:** REQ-027 "deaktiviert DSGVO-Consent", was impliziert, dass keine DSGVO-Regeln angewendet werden. Aber REQ-025 DP-002 schreibt GPS-Rundung als technische Maßnahme vor — unabhängig vom Consent-Mechanismus. REQ-027 spezifiziert nicht explizit, dass technische Datenschutzmaßnahmen (GPS-Rundung) auch im Light-Modus erhalten bleiben. Wenn ein Entwickler "DSGVO deaktiviert" als "alle Datenschutzregeln deaktiviert" interpretiert, könnten GPS-Koordinaten im Klartext an Wetter-APIs gesendet werden.

**Lösungsoptionen:**
1. REQ-027 präzisieren: "DSGVO-Consent-Mechanismen (Banner, Einwilligungserfassung) sind deaktiviert. Technische Datenschutzmaßnahmen (GPS-Rundung DP-002, IP-Anonymisierung) BLEIBEN aktiv — sie sind implementierungsseitig, nicht consent-abhängig."

---

### W-013: REQ-004 "CalMag zuerst" vs. explizite Mischsequenz-Variabilität
**Typ:** Redaktionelle Inkonsistenz mit funktionalem Einfluss
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `REQ-004 §1` (v3.4): "Empfohlene Standard-Misch-Reihenfolge: 1. Wasser, 2. Silizium, 3. CalMag, 4. Base A, 5. Base B..." mit Kommentar "Widerspruchsanalyse W-016 — Klarstellung: Beispiel, nicht normativ"
- `REQ-004 §1`: "Silizium-Zusätze (pH-instabil, zuerst!)" — mit Ausrufezeichen, suggeriert normativ.
- `CLAUDE.md` Key Architectural Decisions: "CalMag before sulfates to prevent precipitation" — suggeriert eine absolute Regel.
- `REQ-004 §1 Absatz 2`: "Die tatsächliche Reihenfolge im System wird ausschließlich über das `mixing_priority`-Feld des Fertilizer-Modells gesteuert — nicht durch diese Liste."

**Konflikt:** Die CLAUDE.md-Architekturbeschreibung nennt "CalMag before sulfates" als absolute Regel. Die aktuelle REQ-004 v3.4 relativiert die Mischsequenz explizit als nicht-normativ und verweist auf `mixing_priority`. Der Kommentar `<!-- Quelle: Widerspruchsanalyse W-016 -->` zeigt, dass dieser Widerspruch intern bekannt ist, aber CLAUDE.md wurde nicht synchronisiert.

**Lösungsoptionen:**
1. CLAUDE.md-Eintrag korrigieren: "Mischsequenz wird über `mixing_priority`-Feld gesteuert. CalMag vor Sulfaten ist ein Standardwert, aber überschreibbar."

---

### W-014: NFR-011 Sensor-Retention 5 Jahre vs. DSGVO-Minimierungsprinzip für Perennials
**Typ:** Qualitäts-Widerspruch (NFAs gegeneinander)
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `NFR-011 §2.2 R-14`: "Sensordaten (Stufe 3): 2–5 Jahre: Tagesmittelwerte, danach löschen."
- `NFR-011 §2.2` Ausnahme: "Klimatische Extremwert-Events — dauerhaft archiviert" in ArangoDB als `ClimateEvent`.
- `REQ-003 §1`: "Dauerkulturen-Modus: Jedes Jahr bildet eine eigene Saison... Saison-Vergleich: Ertrag und Performance über Jahre hinweg vergleichbar."
- `DSGVO Art. 5(1)(e)` Speicherbegrenzung — referenziert in NFR-011 §1.2.

**Konflikt:** NFR-011 löscht Sensordaten nach 5 Jahren vollständig. REQ-003 fordert für Dauerkulturen (Obstbäume, Beerensträucher) "Saison-Vergleich über Jahre". Ein 20-jähriger Apfelbaum benötigt für aussagekräftige Ertragsprognosen idealerweise Sensordaten über viele Saisons. Die Klima-Event-Ausnahme (frost, heat, storm) adressiert nur Extremereignisse, nicht die normalen Wachstumsbedingungen (durchschnittliche VPD, DLI-Werte) die für Ertragsprognosen benötigt werden. Es gibt keine spezifizierte Möglichkeit, die 5-Jahres-Grenze für Perennial-Standorte zu erhöhen.

**Lösungsoptionen:**
1. NFR-011 §4 `RetentionSettings` um eine perennial-spezifische Konfiguration ergänzen: `PERENNIAL_SENSOR_RETENTION_YEARS: int = 10` (Default: 5), mit DSGVO-Hinweis, dass erhöhte Fristen nur für nicht-personenbezogene Sensordaten (Standort-bezogen, nicht Personen-bezogen) gültig sind.
2. REQ-003 `SeasonalCycle` als Aggregat-Speicher für saisonale Durchschnittswerte nutzen (EC, pH, VPD-Durchschnitt pro Saison als Felder auf `seasonal_cycles`) — dann sind Rohdaten nach 5 Jahren löschbar, aber Saison-Aggregate bleiben.

---

### W-015: REQ-023 Service Accounts vs. REQ-027 Light-Modus — API-Key ohne Auth
**Typ:** Scope-Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `REQ-023 v1.7` Service Accounts: "API-Key-only, keine Passwort/SSO-Fähigkeit. Tenant-scoped oder Platform-scoped."
- `REQ-027 §6.2`: "Im Light-Modus werden Auth-spezifische Router nicht registriert." und "`POST /auth/...` ist im Light-Modus nicht verfügbar."
- `REQ-027 §2.1` Feature-Visibility-Matrix: "JWT-Token: Nicht verwendet" im Light-Modus.

**Konflikt:** REQ-023 v1.7 Service Accounts verwenden API-Keys für M2M-Authentifizierung (Home Assistant, Grafana, CI/CD). Im Light-Modus wird Auth vollständig deaktiviert — aber was passiert mit Service Accounts im Light-Modus? REQ-027 spezifiziert nicht, ob Service Accounts im Light-Modus existieren dürfen. Ein Home Assistant, der für REQ-018 (Umgebungssteuerung) einen API-Key zum Abrufen von Sensor-Daten benötigt, würde im Light-Modus keinen Key brauchen (alles ist ohne Auth zugänglich). Aber wenn der Modus von Light auf Full gewechselt wird (Szenario 5), müssten Service Accounts neu erstellt werden. Es ist unklar, ob bestehende Home-Assistant-Konfigurationen nach einem Upgrade funktionieren.

**Lösungsoptionen:**
1. REQ-027 §2.1 Feature-Visibility-Matrix um Zeile "Service Accounts" ergänzen: Im Light-Modus deaktiviert (nicht nötig), im Full-Modus vollständig.
2. REQ-027 Upgrade-Prozess (Szenario 5) erweitern: Hinweis, dass nach Light→Full-Upgrade Home-Assistant-Integrationen Service Accounts anlegen müssen.

---

### W-016: UI-NFR-003 Performance-Budget vs. KI-Feature-Payload
**Typ:** Qualitäts-Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `UI-NFR-003 §2.4 R-013`: "Das initiale JavaScript-Bundle SOLL unter 300KB (gzipped) liegen."
- `UI-NFR-003 §4` Akzeptanzkriterien: "Initiales JS-Bundle < 200KB gzipped" — strengere Zahl als in §2.4.
- `REQ-031 v2.0 §1.1`: KI-Chat-Drawer, TipCardsPanel, DailyTipCard, WhyButton — neue Frontend-Komponenten für KI-Features.
- `NFR-012 §4.1`: "Embedding Service (ONNX): 2 CPU / 4 GB" als Compute-Anforderung — impliziert dass ONNX-Modell im Browser nicht läuft, aber SSE-Streaming für Chat-Antworten wird genutzt.

**Konflikt:** UI-NFR-003 nennt zwei verschiedene Bundle-Size-Ziele: §2.4 sagt "unter 300KB" und die Akzeptanzkriterien in §4 sagen "< 200KB gzipped". Das ist eine innerdokumentarische Inkonsistenz (MITTEL, nicht KRITISCH). Zusätzlich: Die KI-Features aus REQ-031 (SSE-Streaming für Chat, TipCards, Daily-Tip, WhyButton) erfordern zusätzliche Frontend-Abhängigkeiten (EventSource-Handling, neue Redux-Slices, neue Komponenten). Ohne Messung ist unklar, ob das 200KB-Ziel nach Integration der KI-Features noch erreichbar ist — zumal MUI-Komponenten (~180KB) bereits den Löwenanteil des Budgets verbrauchen.

**Lösungsoptionen:**
1. UI-NFR-003 §4 korrigieren: "< 300KB gzipped" (konsistent mit §2.4), oder §2.4 auf "< 200KB" reduzieren wenn dies das verbindliche Ziel ist.
2. Bundle-Analyse nach REQ-031-Integration als explizites Akzeptanzkriterium in REQ-031 hinzufügen.

---

### W-017: REQ-015 Kalenderansicht — iCal-Token-Auth vs. Light-Modus
**Typ:** Direkter Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `REQ-015` (gelesen via MEMORY.md): "CalendarFeed: Token-basierte iCal-Auth (kein JWT)."
- `REQ-027 §6.2`: Auth-Router wird im Light-Modus nicht registriert, inkl. Token-basierter Endpunkte.
- `REQ-027 §2.1` Feature-Visibility: "Phasensteuerung: Vollständig" im Light-Modus — Phasen-Events sollten im Kalender erscheinen.

**Konflikt:** REQ-015 verwendet Token-basierte Auth für iCal-Feeds (damit externe Kalender-Apps den Feed abonnieren können). REQ-027 deaktiviert Auth-Endpunkte im Light-Modus. Ob der iCal-Token-Mechanismus als "Auth-Endpunkt" gilt oder als funktionaler Feature-Endpunkt, ist nicht spezifiziert. Wenn iCal-Feeds im Light-Modus nicht funktionieren, fehlt eine nützliche Integration mit Google Calendar / Apple Kalender.

**Lösungsoptionen:**
1. REQ-027 §6.2 klarstellen: Der iCal-Feed-Endpunkt gilt nicht als "Auth-Endpunkt" und bleibt im Light-Modus aktiv — allerdings ohne Token-Validierung (oder mit einem statischen System-Token).
2. REQ-015 spezifizieren: Im Light-Modus ist der iCal-Feed ohne Token abrufbar (da kein Auth nötig), aber URL-basierte Isolierung muss dokumentiert werden.

---

### W-018: NFR-008 Teststrategie — 90% Coverage vs. 821 Tests für 35+ Endpoints
**Typ:** Qualitäts-Widerspruch
**Schweregrad:** MITTEL

**Betroffene Anforderungen:**
- `NFR-008` (Teststrategie, nicht vollständig gelesen): impliziert Testabdeckungs-Ziele.
- MEMORY.md: "821 backend tests passing" bei über 35 REQ-implementierten Modulen.
- `NFR-012 §8`: "Image Scanning: Trivy / Snyk bei jedem Build" — CI-Gate impliziert Testabdeckung.

**Konflikt:** NFR-008a spezifiziert Selenium E2E-Tests. Die tatsächlichen Backend-Tests (821) sind rein Unit/Integration-Tests laut MEMORY.md. Frontend hat 198 Vitest-Tests. Eine Mindest-Coverage-Schwelle ist in den gesichteten Dokumenten nicht explizit genannt, was Messbarkeit verhindert. Ohne messbares Coverage-Ziel kann die Teststrategie nicht als NFR durchgesetzt werden.

**Lösungsoptionen:**
1. NFR-008 um eine explizite Coverage-Vorgabe ergänzen (z.B. ">= 80% Line Coverage für Business Logic Layer", ">= 70% Statement Coverage gesamt").
2. CI-Gate in GitHub Actions für Coverage-Reporting konfigurieren.

---

## Niedrige Widersprüche / Redaktionelle Inkonsistenzen

### W-019: UI-NFR-011 Kiosk-Modus vs. UI-NFR-011 Fachbegriff-Erklärungen — Gleiche ID
**Typ:** Redaktionelle Inkonsistenz
**Schweregrad:** NIEDRIG

**Betroffene Dokumente:**
- `spec/ui-nfr/UI-NFR-011_Kiosk-Modus.md` — existiert
- `spec/ui-nfr/UI-NFR-011_Fachbegriff-Erklaerungen.md` — existiert

Beide Dokumente tragen die ID `UI-NFR-011`. Eine der Spezifikationen muss umnummeriert werden (z.B. Kiosk-Modus → UI-NFR-019 oder Fachbegriff-Erklärungen bleiben UI-NFR-011 da REQ-035 darauf verweist). Das ist ein Verwaltungsfehler ohne funktionale Auswirkung, aber er kann bei automatisierter Trace-Matrix-Generierung zu Fehlen führen.

**Lösungsoptionen:** UI-NFR-011 Kiosk-Modus auf UI-NFR-011a oder UI-NFR-019 umbenennen.

---

### W-020: REQ-009 Dashboard — Nicht spezifiziert, aber in Feature-Visibility-Matrix REQ-027 referenziert
**Typ:** Scope-Lücke
**Schweregrad:** NIEDRIG
**Status (2026-04-27):** ⚠️ **Misclassified** → ✅ **Resolved** (siehe unten)

REQ-009 (Dashboard) ist laut MEMORY.md "nicht implementiert (no spec)" und in der CLAUDE.md als "Specified But Not Yet Implemented" aufgelistet. REQ-031 v2.0 §1 referenziert REQ-009 als Abhängigkeit ("DailyTipCard auf Dashboard"). Wenn REQ-009 nicht existiert oder unvollständig ist, können REQ-031-Anforderungen (KI-Tipp auf Dashboard) nicht vollständig gegen eine Dashboard-Spezifikation validiert werden.

**Lösungsoptionen (ursprünglich):** REQ-009 priorisieren oder REQ-031 mit einer eigenständigen Dashboard-Integration-Sektion versehen.

> **Korrektur 2026-04-27:** Die Annahme „REQ-009 ist nicht spezifiziert" war **falsch**. `spec/req/REQ-009_Dashboard.md` existierte bereits als v2.0 „Maximal Erweitert" mit 1373 Zeilen — nur in MEMORY.md/CLAUDE.md nicht aktualisiert. Die existierende Spec hatte allerdings 7 Konfliktpunkte mit den seither erstellten jüngeren Specs (REQ-021/022/024/027/031, UI-NFR-003/012/019), die im Rahmen der Konsolidierung zu **REQ-009 v2.1** aufgelöst wurden:
>
> - WebSocket → REST-Polling (v1); WebSocket = Phase 2 (Konsistenz mit UI-NFR-012, W-011)
> - Drag-and-Drop → festes Layout pro Erfahrungsstufe (REQ-021); Drag-Drop = Phase 2
> - Plotly + D3.js → Recharts (UI-NFR-003 W-016 Bundle-Budget 300KB)
> - ML-Forecasts → REQ-031 KI-Daily-Tip nutzen
> - PDF-Export → Verweis auf REQ-032
> - Multi-User-Rollen → REQ-024 Permission-Matrix
> - Erfahrungsstufen-Sets + Light-Modus-Verhalten + Multi-Tenant-Filter ergänzt
>
> Bestehende Tiefe der v2.0-Spec bleibt erhalten; neue Sektionen §1.4–§1.7 dokumentieren die Konsolidierung. CLAUDE.md sollte den „Specified But Not Yet Implemented"-Eintrag für REQ-009 entfernen — Spec ist da, nur die Implementierung steht aus.

---

### W-021: REQ-004 v3.4 Single-Source-of-Truth vs. REQ-014 EC-Budget-Denormalisierung
**Typ:** Redaktionelle Inkonsistenz
**Schweregrad:** NIEDRIG

**Betroffene Anforderungen:**
- `REQ-004 §1` Kommentar: "REQ-004 ist die Single Source of Truth für die EC-Budget- und WaterMixCalculator-Logik; REQ-014 referenziert diese Berechnungen für TankFillEvent-Defaults."
- `REQ-014 §1` (Wasserquellen-Defaults-Kaskade): Beschreibt eine eigene 4-stufige Kaskade, die teils `WaterMixCalculator` aus REQ-004 aufruft, teils eigene Fallback-Logik definiert.

Der Kommentar in REQ-004 ist korrekt (Single Source of Truth), aber REQ-014 hat eigene Logik für die Kaskaden-Auflösung. Diese ist nicht direkt widersprüchlich, aber ohne Tests könnte die Kaskade in REQ-014 andere Ergebnisse liefern als der `WaterMixCalculator` in REQ-004. Kein kritischer Widerspruch, aber potenzielle Implementations-Drift.

**Lösungsoptionen:** REQ-014 §1 Wasserquellen-Kaskade explizit auf `WaterMixCalculator.resolve_water_defaults()` delegieren, statt eine eigene Kaskade zu beschreiben.

---

### W-022: NFR-001 §6.1 vs. REQ-023 — Veraltete Library-Referenz
**Typ:** Redaktionelle Inkonsistenz
**Schweregrad:** NIEDRIG

**Betroffene Anforderungen:**
- `REQ-023 §1` explizit: "Diese Spezifikation verwendet Authlib (aktiv maintained) anstelle von `python-jose` (letztes Release 2022, in NFR-001 §6.1 referenziert)."
- `NFR-001 §6.1` (nicht vollständig gelesen): Referenziert laut REQ-023 noch `python-jose`.

NFR-001 §6.1 wurde durch REQ-023 superseded, aber NFR-001 selbst enthält möglicherweise noch die alte Referenz. Da NFR-001 als "Produktionsreif" markiert ist, sollte ein Update die veraltete Library-Referenz entfernen.

**Lösungsoptionen:** NFR-001 §6.1 mit einem Hinweis versehen: "Superseded by REQ-023. Authlib wird verwendet."

---

## Anforderungs-Index (Konflikt-Trace-Matrix)

### Anforderungen nach Anzahl Konflikte (Top 10)

| Anforderung | Dokument | Konflikte | Widersprüche |
|-------------|----------|-----------|-------------|
| REQ-027 (Light-Modus) | `spec/req/REQ-027_Light-Modus.md` | 4 | W-001, W-012, W-015, W-017 |
| REQ-013 (Pflanzdurchlauf) | `spec/req/REQ-013_Pflanzdurchlauf.md` | 4 | W-003, W-009, W-010, W-021 |
| REQ-025 (DSGVO) | `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` | 3 | W-002, W-007, W-012 |
| REQ-023 (Auth) | `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` | 3 | W-004, W-015, W-022 |
| REQ-003 (Phasensteuerung) | `spec/req/REQ-003_Phasensteuerung.md` | 3 | W-003, W-005, W-014 |
| REQ-031 (KI-Assistent) | `spec/req/REQ-031_KI-Assistent-Pflanzenberatung.md` | 3 | W-001, W-011, W-016 |
| NFR-011 (Retention) | `spec/nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md` | 3 | W-002, W-007, W-014 |
| UI-NFR-012 (PWA) | `spec/ui-nfr/UI-NFR-012_PWA-Offline.md` | 3 | W-004, W-005, W-011 |
| REQ-010 (IPM) | `spec/req/REQ-010_IPM-System.md` | 2 | W-009, W-022 |
| REQ-004 (Dünge-Logik) | `spec/req/REQ-004_Duenge-Logik.md` | 2 | W-013, W-021 |

---

## Qualitätsbewertung der Anforderungen

### Nicht ausreichend messbare NFAs

| Anforderung | Problem | Empfehlung |
|-------------|---------|------------|
| NFR-007 §2.2 "Throughput >= 50 Req/s" | Kein Testverfahren spezifiziert, kein Bezug auf spezifische Endpunkte | Lasttest-Szenario definieren: "50 gleichzeitige Nutzer, Mix aus GET/POST-Requests, Messzeit 10 Minuten" |
| UI-NFR-003 §2.4 Bundle-Budget | Zwei verschiedene Zielwerte (300KB vs. 200KB) im gleichen Dokument | Einen verbindlichen Wert festlegen |
| NFR-008 Testabdeckung | Kein Prozentsatz-Ziel für Coverage | Coverage-Schwelle definieren (z.B. 80% Business Logic Layer) |
| REQ-031 "Graceful Degradation" | "regelbasierte Fallback-Tipps" ohne Spezifikation welcher Regeln | Fallback-Tipp-Katalog als Annex definieren |

### Fehlende Anforderungen (Lücken)

| Bereich | Fehlendes Dokument | Auswirkung |
|---------|-------------------|------------|
| REQ-009 Dashboard | Kein vollständiges Spec | REQ-031 KI-Tipps auf Dashboard nicht gegen Spec validierbar |
| Object-Storage Löschung bei User-Löschung | Nicht in REQ-025 oder NFR-013 | DSGVO Art. 17 nicht vollständig erfüllbar |
| Flutter Mobile App | In stack.md erwähnt, keine REQ | UI-NFR-012 empfiehlt PWA als Primärstrategie — Flutter-Entscheidung nicht formalisiert |
| REQ-033 MCP-Server | Spez-Datei vorhanden, aber nicht gelesen — Interdependenzen mit REQ-031 v2.0 unklar | Potenzielle weitere Widersprüche |

---

## Empfehlungen

### 1. Sofortiger Klärungsbedarf (vor Implementierungsstart)

| Priorität | Widerspruch | Stakeholder | Zeitrahmen |
|-----------|-------------|-------------|------------|
| 1 | **W-001** — KI-Cloud-Provider-Enforcement im Light-Modus | Architect + Security | Sprint 0 |
| 2 | **W-007** — Object-Storage-Bereinigung bei User-Löschung | DSGVO-Verantwortlicher + Backend | Sprint 0 |
| 3 | **W-003** — Phase-Guard für Run-gebundene PlantInstances | Backend-Architect | Sprint 1 |
| 4 | **W-004** — JWT-Offline-Refresh-Toleranz definieren | Backend + Frontend | Sprint 1 |

### 2. Redaktionelle Bereinigung (ohne Meeting)

- **W-008** (Redis vs. Valkey): stack.md synchronisieren — 30 Minuten Aufwand.
- **W-019** (UI-NFR-011 doppelt): Eine Datei umbenennen — 5 Minuten Aufwand.
- **W-022** (NFR-001 §6.1 veraltet): Kommentar ergänzen — 10 Minuten Aufwand.
- **W-013** (CLAUDE.md CalMag): Einen Satz aktualisieren — 5 Minuten Aufwand.

### 3. Architektur-Review-Workshop empfohlen

Folgende Widersprüche erfordern eine Entscheidung durch einen Workshop mit Tech Lead + Product Owner:

- **W-002** — Anonymisierung des user_key in Erasure-Audit-Logs (DSGVO-Rechtsfrage)
- **W-006** — Tenant-eigene Species im Knowledge Service (Architekturentscheidung)
- **W-009** — Karenz-Gate für detachte PlantInstances (Safety-kritisch)
- **W-014** — Sensor-Retention für Perennials (Datenschutz vs. Fachlichkeit)

### 4. Top-3-Strukturelle Verbesserungen

1. **Cross-Referenz-Konsistenz:** Alle REQ-Dokumente sollten bei Breaking Changes in abhängigen REQs eine Changelog-Zeile erhalten. REQ-013 v2.0 hat viele Abhängigkeiten (REQ-003, REQ-006, REQ-007, REQ-010, REQ-022), aber nicht alle haben ihre Spec aktualisiert.
2. **Object-Storage als Querschnittsthema:** NFR-013 ist neu (2026-04-25) und muss systematisch in alle REQs eingetragen werden, die Binärdaten erzeugen (REQ-006, REQ-007, REQ-008, REQ-010, REQ-012, REQ-013, REQ-025, REQ-032). Derzeit fehlt in den meisten REQs ein Verweis auf NFR-013.
3. **Offline-Schutzbereich komplettieren:** UI-NFR-012 §3.3a (Requires-Connectivity-Aktionen) ist eine gute Liste, aber sie fehlt als Referenz in den jeweiligen Fach-REQs (REQ-003 Phasenwechsel, REQ-007 Ernte, REQ-010 Behandlung, REQ-018 Aktoren). Eine bidirektionale Verlinkung würde Implementierungsfehler verhindern.

---

**Dokumenten-Ende**
**Version:** 1.0
**Analysedatum:** 2026-04-26
**Analysiert durch:** Requirements-Engineering-Agent (Claude Sonnet 4.6)
