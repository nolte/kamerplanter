# Spezifikation: REQ-036 - Strukturierter KI-Diagnose-Assistent

```yaml
ID: REQ-036
Titel: Strukturierter KI-Diagnose-Assistent (Multi-Step, Symptom-Katalog, Foto-Anhang)
Kategorie: KI & Beratung
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Redis, Celery, React 19, TypeScript 5.9, MUI 7
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-001 v5.0 (Stammdaten), REQ-010 v1.0 (IPM), REQ-013 v2.0 (Pflanzdurchlauf), REQ-021 v1.0 (Erfahrungsstufen), REQ-024 v1.4 (Mandantenverwaltung), REQ-025 v1.0 (DSGVO), REQ-029 v1.0 (Bilderkennung — optional), REQ-031 v2.0 (KI-Assistent / Knowledge Service)
Wird benoetigt von: —
```

## Versionshistorie

| Version | Datum | Aenderung |
|---------|-------|-----------|
| 1.0 | 2026-04-25 | Initialer Entwurf — auf Basis Knowledge-Service-Realität (REQ-031 v2.0) und IPM (REQ-010) |

## 1. Business Case

**User Story (Casual User — schnelle Hilfe):** "Als Zimmerpflanzen-Besitzer ohne botanisches Wissen moechte ich bei einem Pflanzenproblem nicht eine offene Chat-Frage stellen muessen, sondern aus einer Liste 'gelbe Blaetter', 'Welken', 'braune Flecken' auswaehlen koennen — damit ich auch ohne Fachbegriffe schnell zur Diagnose komme."

**User Story (Grower — gefuehrte Diagnose):** "Als Grower moechte ich in 3 Schritten (Symptom waehlen, Pflanzen-Kontext bestaetigen, optional Foto anhaengen) zu einer Top-3-Diagnose mit konkreten Maßnahmen kommen — damit ich weniger Fehlentscheidungen treffe und meine Diagnose-Historie spaeter nachvollziehen kann."

**User Story (Verlauf-Nutzer):** "Als regelmaessiger Nutzer moechte ich eine Diagnose-Historie pro Pflanze einsehen koennen — damit ich Muster ueber die Zeit erkenne (z. B. immer wieder Naehrstoffmangel an derselben Pflanze)."

**User Story (Datenschutz-bewusst):** "Als datenschutzbewusster Nutzer moechte ich entscheiden koennen, ob meine Diagnose-Sessions kurz (30 Tage) oder lang (1 Jahr) gespeichert werden — damit ich Verlaeufe behalten kann, ohne unnoetig Daten anzusammeln."

**User Story (IPM-Bruecke):** "Als Grower moechte ich von einer Diagnose direkt einen Treatment-Vorschlag aus dem IPM-System (REQ-010) sehen — damit ich von 'Diagnose: Spinnmilbenbefall' direkt zur passenden Behandlung springe, mit korrekter Karenzzeit."

**User Story (Foto-bereit fuer KI-Erkennung):** "Als Nutzer moechte ich heute schon Fotos zu meinen Diagnose-Sessions hochladen koennen, auch wenn die Bilderkennung noch nicht alles auswertet — damit meine Sessions vollstaendig sind, sobald die Foto-KI verfuegbar ist."

**Beschreibung:**

REQ-036 fuehrt einen **strukturierten Diagnose-Workflow** ein, der ueber den Chat-Assistenten aus REQ-031 v2.0 hinausgeht. Statt freier Chat-Frage fuehrt der Nutzer einen kurzen, gefuehrten Multi-Step-Dialog:

1. **Schritt 1 — Symptom auswaehlen:** Aus einem kuratierten Katalog (~30 Eintraege).
2. **Schritt 2 — Pflanzen-Kontext bestaetigen / praezisieren:** Pflanze, Phase, Substrat, juengste Werte werden vorausgewaehlt; Nutzer kann ergaenzen.
3. **Schritt 3 — Optional Foto anhaengen:** Anhang wird gespeichert; falls REQ-029 aktiv und Consent vorhanden, automatische Bilderkennung als zusaetzlicher Kontext.
4. **Schritt 4 — KI-Analyse:** Knowledge Service liefert Top-3 Verdachtsdiagnosen mit Konfidenz, Begruendung und konkreten Massnahmen.
5. **Schritt 5 — Aktion:** Nutzer kann eine Diagnose als zutreffend markieren, einen Treatment-Vorschlag aus IPM (REQ-010) starten oder die Session als "ungeklaert" archivieren.

Sessions werden persistiert (`diagnosis_sessions`-Collection), pro Pflanze gruppiert und in der Pflanzen-Detailseite als Historie dargestellt.

**Grundprinzipien:**

- **Strukturierter Pfad statt offener Chat:** Symptom-Katalog reduziert kognitive Last, Eingabefehler und Halluzinationsrisiko der KI.
- **Kuratierter Symptom-Katalog:** ~30 Eintraege in `spec/knowledge/symptoms/seed_symptoms.yaml`, redaktionell gepflegt.
- **Auch ohne KI nutzbar:** Bei deaktivierter KI funktioniert der Workflow als reine Symptom-Pflanze-Foto-Erfassung; statt LLM-Antwort wird auf manuelle Diagnose / IPM-Suche verwiesen.
- **Foto-Anhang ist heute Datenpunkt, morgen KI-Input:** Speicherung erfolgt jetzt schon via REQ-029-kompatiblen `ImageRecognitionAdapter`-Vertrag; auto-Erkennung wird stufenweise aktiviert.
- **DSGVO-konform:** Default-Retention 90 Tage, Nutzer kann pro Session "archivieren" (1 Jahr) oder "loeschen" (sofort).
- **IPM-Bruecke:** Diagnosen, die mit `Pest`- oder `Disease`-Stammdaten matchen, generieren einen 1-Klick-Vorschlag fuer ein `Treatment` aus REQ-010 mit korrektem Karenz-Gate.
- **Nachvollziehbar:** Jede Session zeigt Quellen-Chunks der KI-Antwort, Modell, KB-Version, Zeitstempel.

### 1.1 Abgrenzung zu benachbarten REQs

| REQ | Beziehung |
|-----|-----------|
| **REQ-031** v2.0 | Wissens-Foundation. Diagnose-Engine ruft Knowledge Service mit kuratierten Diagnose-Prompts. |
| **REQ-010** (IPM) | Diagnose-Ergebnisse koennen IPM-Treatment-Vorschlaege ausloesen; Karenz-Gate aus REQ-010 wird respektiert. |
| **REQ-029** (Bilderkennung) | Optional. Wenn aktiv und Consent erteilt, wird Foto an Plant.id zur Krankheits-/Schadbild-Erkennung gesendet; Ergebnis fliesst als Kontext in den Diagnose-Prompt. |
| **REQ-035** (Glossar) | Symptom-Bezeichnungen verwenden Glossar-Slugs, sodass Hover-Tooltips Erklaerungen liefern. |
| **REQ-027** (Light-Modus) | NICHT verfuegbar im Light-Modus. Eine Diagnose braucht Pflanzen-Kontext und ist tenant-scoped. Im Light-Modus erscheint ein Hinweis "Anmelden, um Diagnose zu nutzen". |
| **REQ-013** v2.0 (Pflanzdurchlauf) | Sessions sind primaer einer `PlantInstance` zugeordnet; alternativ einem `PlantingRun`, wenn die Pflanze keinem Run angehoert. |

## 2. Datenmodell (ArangoDB)

### 2.1 Document Collection: `symptoms`

Kuratierter Symptom-Katalog. Wird beim Backend-Start aus `spec/knowledge/symptoms/seed_symptoms.yaml` geseeded.

```json
{
  "_key": "leaves_yellowing_lower",
  "slug": "leaves_yellowing_lower",
  "labels": {
    "de": "Untere Blaetter werden gelb",
    "en": "Lower leaves turning yellow"
  },
  "category": "leaf_color_change",
  "common_causes_hint": ["nutrient_deficiency_n", "overwatering", "natural_senescence_late_flowering"],
  "applicable_phases": ["seedling", "vegetative", "flowering"],
  "icon": "leaf-yellow",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

**Initial-Symptom-Liste (v1.0, mind. 30):**

| Kategorie | Slugs |
|-----------|-------|
| **leaf_color_change** | leaves_yellowing_lower, leaves_yellowing_upper, leaves_yellowing_uniform, leaves_purple_stems, leaves_brown_tips, leaves_brown_spots, leaves_white_spots, leaves_pale_uniform |
| **leaf_shape_change** | leaves_curling_up, leaves_curling_down, leaves_wrinkled, leaves_dropping, leaves_wilting |
| **growth_anomaly** | growth_stunted, growth_leggy_stretching, internodes_too_long, no_new_growth |
| **pest_visible** | small_white_dots_underside, webs_visible, sticky_residue, small_flying_insects, fungus_gnats_in_soil |
| **disease_visible** | mold_on_soil, mold_on_leaves, root_rot_visible, stem_rot, powdery_white_coating |
| **flowering_issue** | flowers_falling, no_flowering, flowers_browning |
| **environmental** | leaves_burned_tips, leaves_sunburn, frost_damage_visible |

Indexes:
- Unique auf `slug`
- Persistent auf `category`, `is_active`

### 2.2 Document Collection: `diagnosis_sessions`

```json
{
  "_key": "uuid",
  "tenant_key": "string",
  "user_key": "string",
  "plant_instance_key": "string | null",
  "planting_run_key": "string | null",
  "selected_symptoms": ["leaves_yellowing_lower"],
  "context_snapshot": {
    "species_name": "Solanum lycopersicum",
    "cultivar_name": "San Marzano",
    "phase": "flowering",
    "phase_day": 21,
    "substrate_type": "soil",
    "latest_ec_ms": 1.2,
    "latest_ph": 5.8,
    "latest_vpd_kpa": 1.1,
    "active_ipm_events": [],
    "extra_notes": "Stand vor 2 Tagen draussen, war 8 Grad kalt"
  },
  "photo_attachments": [
    {
      "attachment_key": "uuid",
      "image_hash": "sha256:...",
      "uploaded_at": "...",
      "image_recognition_status": "pending | done | skipped | error",
      "image_recognition_result": {
        "adapter_key": "plant_id",
        "matched_disease_keys": ["disease_powdery_mildew"],
        "confidence": 0.84,
        "raw_response_id": "..."
      } | null
    }
  ],
  "kb_query": "Symptom 'untere Blaetter werden gelb' bei Solanum lycopersicum (San Marzano) in Phase flowering Tag 21, Substrat Erde, EC 1.2, pH 5.8. Stand vor 2 Tagen draussen 8 Grad. Top 3 Diagnosen mit Begruendung und Massnahmen.",
  "kb_response": {
    "answer_text": "...",
    "diagnoses": [
      {
        "rank": 1,
        "title": "Stickstoffmangel (N)",
        "confidence": "high",
        "rationale": "Untere Blaetter gelb bei niedrigem EC 1.2 in flowering ist klassisch ...",
        "matched_pest_keys": [],
        "matched_disease_keys": [],
        "matched_treatment_suggestion": null,
        "actions": ["EC auf 1.4-1.6 anheben", "pH auf 6.0-6.5 korrigieren"]
      },
      {
        "rank": 2,
        "title": "Natuerliche Seneszenz (Spaetbluete)",
        "confidence": "medium",
        "rationale": "...",
        "actions": ["beobachten, normalerweise harmlos"]
      },
      {
        "rank": 3,
        "title": "Ueberwaesserung",
        "confidence": "low",
        "rationale": "...",
        "actions": ["Substratfeuchte pruefen", "Drainage verbessern"]
      }
    ],
    "sources": [
      { "source_key": "diagnostik/naehrstoffmangel-symptome#mangel-stickstoff", "source_type": "care_rule", "score": 0.93, "language": "de" }
    ],
    "language": "de",
    "language_mismatch_warning": false,
    "model_name": "gemma3:12b",
    "provider_type": "ollama",
    "kb_version": "ks-1.4.2-idx-20260420"
  },
  "user_feedback": {
    "selected_diagnosis_rank": 1,
    "marked_as_resolved_at": null,
    "user_notes": null,
    "started_treatment_key": null
  },
  "status": "draft | analyzing | answered | resolved | archived | unresolved",
  "retention_class": "default_90d | extended_1y",
  "created_at": "...",
  "updated_at": "...",
  "expires_at": "..."
}
```

**Felder erklaert:**

- `selected_symptoms`: 1-3 Symptom-Slugs (Multi-Select).
- `context_snapshot`: Backend-seitig befuellt aus PlantInstance / PlantingRun zum Zeitpunkt des Sessionsbeginns; vom Nutzer ergaenzbar.
- `photo_attachments`: 0-3 Anhaenge, jeweils einzeln per REQ-029-Adapter ausgewertet (oder skipped, wenn REQ-029 nicht aktiv).
- `kb_query`: Wirklich abgesendete Frage an den Knowledge Service (zur Nachvollziehbarkeit / Audit).
- `kb_response.diagnoses`: Strukturierte Top-3-Liste; das LLM wird ueber den Prompt zu diesem Format gezwungen (JSON-Output-Format).
- `user_feedback`: Nutzeraktionen nach der Antwort.
- `status`: State-Machine s. §2.3.
- `retention_class`: Bestimmt `expires_at` (90 Tage / 365 Tage).

**Indexes:**
- Persistent auf `tenant_key + user_key`
- Persistent auf `plant_instance_key`
- Persistent auf `planting_run_key`
- Persistent auf `expires_at` (Cleanup)
- Persistent auf `status`

### 2.3 Status-State-Machine

```
draft (Multi-Step im Wizard) ---> analyzing (KS-Aufruf laeuft) ---> answered ---> resolved (User markiert)
                                       |                              |
                                       |                              +-> unresolved (User schliesst ohne Diagnose)
                                       |                              |
                                       |                              +-> archived (Retention extended)
                                       |
                                       +-> error (KS-Fehler, manuell wiederholbar)
```

Uebergaenge:
- `draft -> analyzing`: User klickt "Analysieren" im letzten Wizard-Step
- `analyzing -> answered`: KS-Antwort eingetroffen, parsed, persistiert
- `analyzing -> error`: KS-Fehler oder Timeout — Retry-Button im Frontend
- `answered -> resolved`: User markiert eine Diagnose als zutreffend (`selected_diagnosis_rank` gesetzt) oder nimmt eine Maßnahme an
- `answered -> unresolved`: User schliesst Session ohne Bestaetigung
- `* -> archived`: User waehlt explizit "Archivieren" (Retention 1 Jahr)

### 2.4 Edge Collections

```
diagnosis_session_about_plant   diagnosis_sessions -> plant_instances
diagnosis_session_about_run     diagnosis_sessions -> planting_runs
diagnosis_session_used_pest     diagnosis_sessions -> pests              (gesetzt wenn matched_pest_keys existiert)
diagnosis_session_used_disease  diagnosis_sessions -> diseases           (gesetzt wenn matched_disease_keys existiert)
diagnosis_session_started_treatment  diagnosis_sessions -> treatments    (gesetzt wenn user_feedback.started_treatment_key)
```

### 2.5 Foto-Anhaenge (Storage)

Fotos werden im S3-kompatiblen Object Storage (`MinIO` im Cluster) abgelegt unter Pfad:

```
diagnosis-attachments/{tenant_key}/{session_key}/{attachment_key}.{ext}
```

Maximale Groesse: 10 MB pro Foto, max 3 Fotos pro Session. EXIF wird vor dem Upload entfernt (Frontend + Backend doppelt). MinIO-Bucket ist tenant-scoped per IAM-Policy.

## 3. Backend-API

Alle Endpoints unter `/api/v1/t/{tenant_slug}/diagnosis/`. Authentifiziert ueber JWT + Tenant-Membership.

| Methode | Pfad | Beschreibung | Berechtigung | Consent |
|---------|------|-------------|--------------|---------|
| `POST` | `/sessions` | Neue Session anlegen (Status `draft`) | Grower, Admin | (siehe unten) |
| `GET` | `/sessions` | Sessions des Users auflisten (Filter: `?plant_instance_key=&status=`) | Grower, Admin | — |
| `GET` | `/sessions/{key}` | Session-Details laden | Grower, Admin | — |
| `PATCH` | `/sessions/{key}` | Wizard-Felder aktualisieren (`selected_symptoms`, `context_snapshot.extra_notes`) — nur im Status `draft` | Grower, Admin | — |
| `POST` | `/sessions/{key}/attachments` | Foto-Anhang hochladen (multipart) | Grower, Admin | — |
| `DELETE` | `/sessions/{key}/attachments/{attachment_key}` | Anhang loeschen | Grower, Admin | — |
| `POST` | `/sessions/{key}/analyze` | Wizard abschliessen, KS-Aufruf starten (sync: HTTP 200 mit Spinner-Hinweis im Frontend; alternativ async mit Polling) | Grower, Admin | `ai_tenant_data_access` |
| `POST` | `/sessions/{key}/feedback` | Diagnose-Auswahl + Notizen setzen | Grower, Admin | — |
| `POST` | `/sessions/{key}/start-treatment` | Treatment aus IPM-Vorschlag starten — leitet an REQ-010 weiter | Grower, Admin | — |
| `PATCH` | `/sessions/{key}/retention` | Retention-Klasse aendern (`default_90d`, `extended_1y`) | Grower, Admin | — |
| `DELETE` | `/sessions/{key}` | Session sofort loeschen (DSGVO Art. 17) | Grower, Admin | — |

### 3.1 Symptom-Katalog-Endpoints (oeffentlich pro Tenant)

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/api/v1/t/{slug}/diagnosis/symptoms` | Aktive Symptome (Filter: `?category=&phase=&language=`) | Viewer, Grower, Admin |

### 3.2 Platform-Admin

| Methode | Pfad | Beschreibung | Berechtigung |
|---------|------|-------------|--------------|
| `GET` | `/api/v1/admin/diagnosis/symptoms` | Komplette Symptomliste inkl. inactive | Platform-Admin |
| `POST/PUT/DELETE` | `/api/v1/admin/diagnosis/symptoms[/{slug}]` | Symptom-CRUD | Platform-Admin |

## 4. Backend-Komponenten

### 4.1 SymptomCatalog

`src/backend/app/domain/services/symptom_catalog.py`. Liefert Liste + Lookup, geseeded aus `spec/knowledge/symptoms/seed_symptoms.yaml` beim Backend-Start (analog zu REQ-035 Glossar-Seed).

### 4.2 DiagnosisService

`src/backend/app/domain/services/diagnosis_service.py`. Orchestriert den Workflow:

- `create_session(tenant, user, plant_instance_key|planting_run_key)` — legt `draft` an, schnappt `context_snapshot`
- `update_session(...)` — Wizard-Patches im `draft`
- `add_attachment(...)` / `remove_attachment(...)` — Foto-Mgmt, ggf. Trigger fuer Bild-Erkennung
- `analyze(session_key)` — siehe §4.3
- `set_feedback(...)` / `start_treatment(...)` / `set_retention(...)` / `delete(...)`

### 4.3 DiagnosisAnalysisEngine

`src/backend/app/domain/engines/diagnosis_analysis_engine.py`. Methode `analyze(session)`:

1. Status auf `analyzing` setzen.
2. Ggf. fehlende Foto-Erkennungen abwarten (max 30s, danach `image_recognition_status=skipped`).
3. KB-Query bauen: kuratiertes Prompt-Template (`spec/knowledge/diagnosis-prompts/`) + Slot-Filling aus `context_snapshot`, `selected_symptoms`, `photo_attachments[].image_recognition_result`.
4. KnowledgeServiceAdapter `/ask` aufrufen mit:
   - `prompt_language` = User-Locale
   - `doc_language` = "all"
   - `top_k` = 8
   - `context` = Subset von `context_snapshot` (nur Stammwerte, ohne `extra_notes` Klartext — analog REQ-031 §7.2)
   - System-Prompt erzwingt JSON-Output mit `diagnoses[]`
5. Antwort parsen, validieren (Pydantic `DiagnosisAnswer`), persistieren.
6. IPM-Matching: `matched_pest_keys` und `matched_disease_keys` werden gegen `pests`/`diseases`-Collections aufgeloest; bei Match wird `matched_treatment_suggestion` mit einem Treatment-Vorschlag aus REQ-010 angereichert.
7. Status auf `answered` setzen.
8. Audit-Log via `ai_audit_log` (REQ-031 §3.1).

### 4.4 ImageRecognitionDispatcher

`src/backend/app/domain/services/image_recognition_dispatcher.py`. Bridge zu REQ-029.

- Wenn REQ-029 nicht aktiv (Adapter nicht registriert oder Tenant-Setting deaktiviert): Anhang wird gespeichert, Status `skipped`.
- Wenn REQ-029 aktiv und User-Consent vorhanden: Adapter wird async via Celery aufgerufen, Status `pending` -> `done | error`.
- Ergebnis wird in `photo_attachments[i].image_recognition_result` zurueckgeschrieben.

### 4.5 Celery-Tasks

| Task | Schedule | Zweck |
|------|----------|-------|
| `diagnosis.cleanup_expired_sessions` | taeglich 02:50 UTC | Loescht `diagnosis_sessions` mit `expires_at < now()`, inkl. Foto-Anhaenge (MinIO) und Edges |
| `diagnosis.dispatch_image_recognition` | event-getriggert | Auswertung eines Foto-Anhangs |

## 5. Frontend-Komponenten (React/MUI)

### 5.1 `<DiagnosisWizard>`

Pfad: `src/frontend/src/components/diagnosis/DiagnosisWizard.tsx`

MUI Stepper mit 4 sichtbaren Schritten + Ergebnis:

1. **Symptom auswaehlen** — `SymptomPicker` (Multi-Select, Suche, Kategorie-Filter, Icons)
2. **Pflanze und Kontext** — `ContextForm` (Pflanze-/Run-Auswahl, Phase-Bestaetigung, optionale Freitext-Notiz "extra_notes")
3. **Optional: Fotos** — `PhotoUploader` (Drag&Drop, max 3, max 10 MB, EXIF-Strip, Preview, Reorder)
4. **Analyse starten** — Button "Analysieren" (Spinner-Variante; siehe REQ-031 §5.4 — kein Streaming bei diesem Endpunkt)
5. **Ergebnis** — `DiagnosisResultsPanel` (siehe 5.2)

State-Mgmt: Redux Toolkit Slice `diagnosisWizard`. Persistente `draft`-Session ueber Backend, sodass Browser-Refresh den Stand erhaelt.

### 5.2 `<DiagnosisResultsPanel>`

Pfad: `src/frontend/src/components/diagnosis/DiagnosisResultsPanel.tsx`

Top-3-Diagnosen als Karten:

- Header: Titel + Konfidenz-Badge (high/medium/low farbig)
- Body: Begruendung (`rationale`) — gerendert in `<AIResponse>`-Huelle (REQ-031 §6.1)
- Aktionen-Liste: Bullet-Points
- Bei `matched_treatment_suggestion`: Prominent-Button "Treatment starten" (oeffnet REQ-010-Treatment-Dialog mit vorausgefuellten Werten + Karenz-Hinweis)
- Pro Karte: Radio "Diese Diagnose ist zutreffend" -> `set_feedback`

Footer:
- "Als geloest markieren" (`status=resolved`)
- "Ungeklaert lassen" (`status=unresolved`)
- "Archivieren (1 Jahr Aufbewahrung)" (`retention_class=extended_1y`)

### 5.3 `<DiagnosisHistoryList>`

Pfad: `src/frontend/src/components/diagnosis/DiagnosisHistoryList.tsx`

Liste der Sessions pro Pflanze (eingebaut in `PlantInstanceDetailPage` und `PlantingRunDetailPage`):

- Sortierung: neueste zuerst
- Pro Session: Datum, Symptom-Chips, gewaehlte Diagnose (falls), Status-Badge
- Klick oeffnet Read-Only-View (Wizard im Read-Modus)
- "Neue Diagnose"-Button oben rechts

### 5.4 Integration Sidebar / Navigation

- Neuer Sidebar-Eintrag "Diagnose" (ab Stufe 2 KI-aktiv) mit Liste aller Sessions des Tenants ueber alle Pflanzen.
- "Diagnose starten"-Button auf:
  - `PlantInstanceDetailPage` (oben, Quick-Action)
  - `PlantingRunDetailPage` (oben, Quick-Action)
  - Pflege-Dashboard (REQ-022) bei `CareReminderCard` mit Symptom-Hinweis (z. B. "Schaedlingskontrolle")

### 5.5 KI-deaktivierter Fallback

Wenn Stufe 1+2 KI nicht aktiv:
- Wizard funktioniert bis Schritt 3 normal (Symptom + Kontext + Foto erfasst).
- Statt Schritt 4/5 erscheint Hinweis: "KI-Diagnose nicht aktiv. Schritte werden gespeichert. Manuelle Diagnose ueber IPM-System (Verlinkung) oder spaeter aktivieren."
- Session bleibt im Status `draft` und kann spaeter analysiert werden, sobald KI aktiv ist.

## 6. Sicherheit & Datenschutz (REQ-025, NFR-007)

- **Consent:** `analyze`-Endpoint erfordert `ai_tenant_data_access`. Foto-Erkennung via REQ-029 erfordert zusaetzlich `external_image_recognition` (siehe REQ-029).
- **PII-Stripping:** `extra_notes`-Klartext wird NICHT an den Knowledge Service gesendet; stattdessen als zusaetzlicher KB-Query-Hinweis "Nutzer hat Anmerkungen zur Sitzung gemacht". Wer den Klartext mitanalysieren will, muss "Notizen freigeben" aktivieren (Session-spezifisch, separater Consent-Schritt im Wizard).
- **EXIF-Strip:** doppelt (Frontend + Backend). GPS-Daten erscheinen nicht in MinIO.
- **Retention:** Default 90 Tage, optional Extended 1 Jahr. Sofortige Loeschung via `DELETE /sessions/{key}` (DSGVO Art. 17), kaskadiert auf Foto-Anhaenge in MinIO.
- **Audit-Log:** Jeder `analyze`-Aufruf erscheint in `ai_audit_log`. `kb_query` ist im Session-Doc gespeichert (zur Nachvollziehbarkeit), aber NICHT im Audit-Log (dort nur Hash).
- **Tenant-Isolation:** `diagnosis_sessions` werden nie cross-tenant gelistet. Foto-Pfad enthaelt `tenant_key`.
- **DSGVO-Auskunft (REQ-025 Art. 15):** Auskunftsexport enthaelt alle `diagnosis_sessions` des Users inkl. Symptome, Kontext, Antwortinhalt und Foto-Hashes.

## 7. Multilingual

- Symptom-Labels DE+EN obligatorisch.
- Diagnose-Prompt-Templates in `spec/knowledge/diagnosis-prompts/{template}.{de|en}.txt`.
- KB-Antwort folgt User-Locale (Knowledge Service `prompt_language`).
- `language_mismatch_warning` wird im UI dargestellt, wenn Antwort-Sprache nicht User-Locale matcht.

## 8. Akzeptanzkriterien

### Definition of Done

- [ ] **`symptoms`-Collection** angelegt, mind. 30 Eintraege geseeded.
- [ ] **`diagnosis_sessions`-Collection** angelegt mit allen Feldern und Indexes.
- [ ] **`SymptomCatalog`-Service** liest Seed und liefert API-Listen.
- [ ] **`DiagnosisService`** mit allen Methoden funktional.
- [ ] **`DiagnosisAnalysisEngine`** ruft Knowledge Service mit kuratiertem JSON-Output-Prompt; Antwort wird als `diagnoses[]`-Liste validiert.
- [ ] **JSON-Output-Validierung**: Bei ungueltiger LLM-Antwort (kein parse-bares JSON) wird automatisch ein zweiter Versuch mit verschaerftem Prompt unternommen; bei erneutem Fehlschlag Status `error`.
- [ ] **IPM-Matching** mit Treatment-Vorschlag funktional (matched_pest/disease_keys -> Treatment).
- [ ] **Foto-Anhaenge**: Upload (multipart, EXIF-Strip), Speicherung in MinIO, Loeschung mit Foto-Cleanup.
- [ ] **Bild-Erkennung-Bridge**: Wenn REQ-029 aktiv + Consent, async Auswertung; Status reflektiert Pending/Done/Skipped/Error.
- [ ] **Wizard-Frontend** funktional, Step-Persistierung ueber Backend (draft).
- [ ] **DiagnosisHistoryList** in Plant- und Run-Detailseiten.
- [ ] **Treatment-Bruecke** ruft REQ-010-Dialog mit vorausgefuellten Werten auf, Karenz-Gate aktiv.
- [ ] **KI-deaktivierter Fallback**: Wizard funktioniert bis Schritt 3, danach Hinweis.
- [ ] **Audit-Log** schreibt jeden `analyze`-Aufruf ohne Klartext-PII.
- [ ] **Cleanup-Task** loescht abgelaufene Sessions inkl. MinIO-Anhaenge.
- [ ] **i18n** komplett DE+EN inkl. Symptom-Labels.
- [ ] **Vitest-Tests** fuer Wizard-State-Maschine, ResultsPanel, HistoryList.
- [ ] **Pytest-Tests** fuer DiagnosisService, AnalysisEngine (mit gemocktem Knowledge Service), Cleanup-Task.

### Testszenarien

**Szenario 1: Glatter Diagnose-Pfad ohne Foto**
```
GIVEN: User hat Pflanze "Tomate-1" (Phase flowering, Tag 21, EC 1.2)
  AND: Stufe 1+2 KI aktiv, ai_tenant_data_access Consent vorhanden
WHEN: User startet Diagnose, waehlt Symptom "leaves_yellowing_lower"
  AND: Bestaetigt Pflanzen-Kontext, ueberspringt Fotos, klickt "Analysieren"
THEN:
  - draft -> analyzing -> answered (synchron, mit Spinner im Frontend)
  - kb_response.diagnoses enthaelt 3 Eintraege, sortiert nach rank
  - rank 1 ist plausibel "Stickstoffmangel (N)" (Konfidenz high)
  - matched_treatment_suggestion = null (kein Pest/Disease)
  - Audit-Log: status=ok, uses_tenant_data=true, uses_cloud_provider=false
WHEN: User markiert rank 1 als zutreffend und klickt "Als geloest markieren"
THEN:
  - status=resolved, user_feedback.selected_diagnosis_rank=1
```

**Szenario 2: Diagnose mit Foto (REQ-029 inaktiv)**
```
GIVEN: REQ-029 nicht im Cluster aktiv
WHEN: User laedt Foto im Wizard hoch
THEN:
  - Foto wird in MinIO gespeichert
  - photo_attachments[i].image_recognition_status = "skipped"
WHEN: User klickt "Analysieren"
THEN:
  - kb_query enthaelt KEINE image_recognition_result-Hinweise
  - Antwort basiert nur auf Symptomen + Kontext
```

**Szenario 3: Diagnose mit Foto (REQ-029 aktiv, Consent vorhanden)**
```
GIVEN: REQ-029 aktiv, User hat Consent external_image_recognition
WHEN: User laedt Foto
THEN:
  - Async Celery-Task ruft Plant.id (oder Adapter) auf
  - Status pending -> done
  - image_recognition_result.matched_disease_keys = ["disease_powdery_mildew"], confidence 0.84
WHEN: User klickt "Analysieren" (Foto bereits ausgewertet)
THEN:
  - kb_query enthaelt Hinweis "Bilderkennung schlug 'Echter Mehltau' vor (Konfidenz 0.84)"
  - Antwort priorisiert vermutlich Mehltau-Diagnose
WHEN: matched_disease_keys -> diseases[powdery_mildew] hat Treatments im IPM
THEN:
  - matched_treatment_suggestion enthaelt vorgeschlagenes Treatment
  - "Treatment starten"-Button im ResultsPanel sichtbar
```

**Szenario 4: Treatment-Bruecke mit Karenz-Gate**
```
GIVEN: Diagnose schlaegt Treatment "Schwefel-Spritzung" vor
  AND: Pflanze hat juengstes Treatment "Neem-Oel" mit aktiver Karenzzeit (3 Tage)
WHEN: User klickt "Treatment starten"
THEN:
  - REQ-010-Dialog oeffnet
  - Karenz-Gate aus REQ-010 erkennt aktive Karenz aus Neem-Oel
  - Warnung "Karenzzeit aktiv bis YYYY-MM-DD" wird angezeigt
  - Treatment-Anwendung kann erst nach Karenz-Ende bestaetigt werden
```

**Szenario 5: Wizard-Persistenz ueber Browser-Refresh**
```
GIVEN: User ist im Wizard Schritt 2 (Kontext)
WHEN: Browser refresht
THEN:
  - draft-Session wird aus Backend geladen
  - Wizard zeigt Schritt 2 mit zuvor gewaehltem Symptom
  - Kontext-Form ist mit zuvor eingegebenen Werten vorausgefuellt
```

**Szenario 6: KI deaktiviert (Fallback)**
```
GIVEN: tenant.settings.ai_features_enabled=false
WHEN: User durchlaeuft Wizard bis Schritt 3
THEN:
  - Schritt 4 zeigt Hinweis "KI nicht aktiv"
  - "Analysieren"-Button ersetzt durch "Speichern und schliessen"
  - Session bleibt im Status draft
WHEN: Tenant-Admin aktiviert spaeter ai_features_enabled
  AND: User oeffnet die Session erneut
THEN:
  - Wizard zeigt Schritt 4 wieder verfuegbar
  - User kann analyze ausloesen
```

**Szenario 7: Retention extended**
```
GIVEN: Session ist resolved, default_90d
WHEN: User klickt "Archivieren"
THEN:
  - retention_class=extended_1y
  - expires_at wird auf created_at + 365d gesetzt
  - status=archived
WHEN: 95 Tage spaeter cleanup_expired_sessions laeuft
THEN:
  - Session bleibt erhalten (expires_at noch in Zukunft)
WHEN: 366 Tage nach created_at
THEN:
  - Session wird inkl. MinIO-Anhaengen geloescht
```

**Szenario 8: PII-Stripping bei extra_notes**
```
GIVEN: User hat extra_notes "Anna Mueller, Mueller-Strasse 5, 12345 Berlin — Pflanze stand draussen"
WHEN: analyze laeuft
THEN:
  - kb_query enthaelt KEINEN Klartext aus extra_notes
  - kb_query enthaelt nur Hinweis "Nutzer hat Anmerkungen gemacht"
  - context an Knowledge Service enthaelt KEINE PII
WHEN: User aktiviert "Notizen freigeben"-Toggle im Wizard
THEN:
  - Zusaetzlicher Consent-Step zeigt Klartext + Warnung
  - Bei Zustimmung wird extra_notes als zusaetzlicher Hinweis im kb_query mitgesendet
```

**Szenario 9: LLM antwortet kein parsebares JSON**
```
GIVEN: Knowledge Service liefert Antwort, deren Body kein gueltiges JSON ist
WHEN: AnalysisEngine versucht parse
THEN:
  - 1. Versuch fehlgeschlagen
  - Engine startet 2. Versuch mit verschaerftem System-Prompt ("Antworte AUSSCHLIESSLICH mit JSON-Array. Kein Markdown, kein Text davor/danach.")
WHEN: 2. Versuch ebenfalls kein JSON
THEN:
  - status=error
  - error_class="diagnosis.invalid_llm_output"
  - Frontend zeigt Retry-Button
  - Audit-Log: status=provider_error
```

**Szenario 10: Sofortige Loeschung (DSGVO Art. 17)**
```
WHEN: User klickt DELETE /sessions/{key}
THEN:
  - Session-Doc wird hard-deleted
  - Edges (about_plant, about_run, used_pest, used_disease, started_treatment) werden mitgeloescht
  - Foto-Anhaenge in MinIO werden geloescht
  - structlog: "diagnosis_session_deleted" ohne PII
  - HTTP 204 No Content
```

**Szenario 11: Light-Modus blockiert**
```
GIVEN: KAMERPLANTER_MODE=light
WHEN: Anonymer Aufruf POST /api/v1/t/.../diagnosis/sessions
THEN:
  - HTTP 401 Unauthorized
  - Frontend zeigt Hinweis "Diagnose erfordert Anmeldung"
  - Light-Modus-Glossar (REQ-035) bleibt verfuegbar
```

**Szenario 12: Symptomliste pro Phase gefiltert**
```
GIVEN: Pflanze in Phase germination
WHEN: GET /diagnosis/symptoms?phase=germination
THEN:
  - Liste enthaelt Symptome mit applicable_phases enthaeltend "germination"
  - "leaves_yellowing_lower" ist enthalten (vegetative + flowering enthaelt es auch)
  - "flowers_falling" ist NICHT enthalten (nur flowering)
```

## 9. Offene Punkte

- **Mehrere Symptome -> Multi-Aspekt-Diagnose:** v1.0 sendet alle gewaehlten Symptome gemeinsam an das LLM und vertraut auf die KB. Bei sehr divergenten Symptomen koennte spaeter eine Vorab-Cluster-Logik helfen.
- **Differential-Konfidenz-Schwelle:** Wenn rank 1 nur high und rank 2/3 nur low sind, soll UI vermutlich rank 2/3 ausblenden? Heuristik in v1.0 immer Top-3 zeigen, spaeter optional.
- **Voice-Input Symptome:** Dictation des Symptoms statt Picker — nicht in v1.0.
- **Sammel-Diagnose ueber mehrere Pflanzen:** "Alle meine Tomaten haben dasselbe Problem" — nicht in v1.0.
- **Trainings-Feedback-Loop:** Wenn User die Diagnose markiert, koennte das Backend zukuenftig die KB-Treffer als "war hilfreich" annotieren — Datengrundlage fuer KB-Verbesserung. In v1.0 nur als Audit, nicht als Lernsignal.
