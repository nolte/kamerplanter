# Unveröffentlicht

Änderungen, die noch nicht in einem Release veröffentlicht wurden.

## Hinzugefügt

### Backend

- **REQ-001** Stammdatenverwaltung: Botanische Familien, Arten, Sorten, Lebenszyklen (ArangoDB); Feld `propagation_methods` (13 Vermehrungsarten, Mehrfachauswahl) im Arten-Steckbrief — alle 143 Kulturpflanzen-Seed-Daten befüllt
- **REQ-002** Standortverwaltung: Sites, Locations (rekursive Hierarchie), Slots, Standorttypen
- **REQ-003** Phasensteuerung: Phasen-State-Machine (Keimung → Ernte), GDD/VPD/Photoperiod-Berechnung
- **REQ-004** Dünge-Logik: Düngemittel, Nährstoffpläne, Dosierungen, Mischsicherheit, Spülung, Runoff, EC-Budget, Wasserquelle/CalMag-Korrektur
- **REQ-006** Aufgabenplanung: Workflow-Templates, Tasks, Queue, Abhängigkeiten, HST-Validator
- **REQ-007** Erntemanagement: Ernte-Indikatoren, Beobachtungen, Batches, Qualitätsbewertung, Karenz-Gate
- **REQ-010** IPM-System: Schädlinge, Krankheiten, Behandlungen, Inspektionen, Resistenzmanager
- **REQ-011** Externe Stammdatenanreicherung: GBIF + Perenual Adapter, Enrichment-Engine, Celery-Tasks
- **REQ-012** Stammdaten-Import: CSV-Upload, Validierung, Vorschau, Bestätigung
- **REQ-013** Pflanzdurchlauf: PlantingRun, Batch-Operationen, State-Machine
- **REQ-014** Tankmanagement: Tanks, Tankzustände, Befüllungen, Wartung, Sensoren
- **REQ-015** Kalenderansicht: iCal-Feeds, Aggregation, Token-basierter Zugriff
- **REQ-019** Substratverwaltung: Erweiterte Substrattypen, Lebenszyklus-Manager, Wiederverwendung
- **REQ-020** Onboarding-Wizard: 5-Schritte-Assistent, 9 Starter-Kits, Erfahrungsstufen
- **REQ-022** Pflegeerinnerungen: 9 Pflegeprofile, FAMILY_CARE_MAP, adaptive Intervalle, Celery-Task
- **REQ-023** Authentifizierung: Lokale Konten (bcrypt), JWT (authlib), Refresh-Token-Rotation
- **REQ-024** Mandantenverwaltung: Tenant-Isolation, Mitgliedschaften, Einladungen, RBAC
- **REQ-028** Mischkultur & Companion Planting: Graph-basierte Kompatibilität
- **REQ-031** KI-Assistent: RAG-basierte Wissensdatenbank, LLM-Adapter (Anthropic/Ollama/OpenAI-kompatibel), Hybrid-Search

### Frontend

- Alle REQ-001 bis REQ-024 Frontend-Seiten implementiert
- **REQ-020** Onboarding-Wizard (5-Step MUI Stepper)
- **REQ-021** UI-Erfahrungsstufen: Feldkonfiguration, Navigation-Tiering, ExperienceLevelSwitcher
- **REQ-022** Pflege-Dashboard mit Urgency-Gruppierung
- Light/Dark Theme mit localStorage-Persistenz
- i18n Deutsch/Englisch (react-i18next)

### Infrastruktur

- MkDocs-Dokumentationsinfrastruktur mit Material Theme und DE/EN i18n (NFR-005)
- ADR-001 bis ADR-006: Architektur-Entscheidungen dokumentiert
- Skaffold-basierter Entwicklungsworkflow mit Kubernetes/Helm
- pgvector + Embedding-Service für RAG-Pipeline
- Knowledge-Container für YAML-basierte Wissensbasis
- GitHub Actions CI/CD (Docker Lint/Build, Skaffold Verify)

## Geändert

### Frontend

- Admin: Nach dem Löschen einer Organisation meldet die Oberfläche „Löschung angenommen“ statt „Organisation gelöscht“ — die Löschung läuft im Hintergrund (Issue #1792)
- Pflanzinstanzen werden überall mit einem sprechenden Namen angezeigt (z. B. `BASIL-001 (Basilikum – Genovese)`) statt nur der technischen Instanz-ID; die Instanz-ID bleibt als sekundäre Information erhalten
- Aufgaben: Die Formulare in den Tabs **Bearbeiten** und **Abschließen** zeigen Validierungsfehler jetzt als Hinweistext direkt am betroffenen Feld statt als kurzlebige Browser-Sprechblase (`noValidate`)
- Konto: Die Seite zur E-Mail-Bestätigung bietet auch im Fehlerfall (ungültiger oder abgelaufener Link) einen **Anmelden**-Button — vorher war diese Seite eine Sackgasse

### Backend

- **BREAKING (API):** Die Konto-Löschung durch einen Plattform-Admin ist asynchron (Issue #1949, REQ-024 §1a.2, REQ-025 AK-IE-01). `DELETE /api/v1/admin/platform/users/{key}` antwortet jetzt mit `202 Accepted` und einem Body `{erasure_key, status, requested_at, message}` (zuvor `204` ohne Body). Die Anfrage prüft den Step-up, legt den Löschantrag an, deaktiviert das Konto, widerruft seine Sitzungen und benachrichtigt die anderen Mitglieder seiner persönlichen Gärten sofort (weiterhin ohne Karenzzeit); ein Celery-Task (`retention.run_account_erasure`) führt danach die Löschung aus — die persönlichen Mandanten in begrenzten Stapeln mit Lebenszeichen, dann den eigenen Plan des Kontos. Die Antworten `500 ERASURE_INCOMPLETE` und `502` dieses Endpunkts entfallen — ein fehlgeschlagener oder unvollständiger Lauf ist der Antragsstatus `partially_completed` (der tägliche Lauf wiederholt ihn), lesbar über das neue `GET /api/v1/admin/platform/erasures/{erasure_key}`. Weiter synchron entschieden: `401`/`403`/`404`/`422`/`429` (Step-up, Berechtigung), `409` (ein Lauf hält den Antrag) und `503` (das Deployment kann nicht löschen; nichts geändert). Aufrufer, die auf eine fertige Löschung warteten, müssen den Status abfragen. Löschungen, die die alte synchrone Route vor dem Deploy gestartet hat, enden wie bisher; der tägliche Lauf setzt eine abgebrochene fort
- **Sicherheit (API):** `PATCH /api/v1/admin/platform/users/{key}` verlangt jetzt das eigene Step-up des Administrators, sobald es `email_verified` oder `is_active` **ändert** — auch beim Senken (Issue #1992; zuvor nur beim Anheben). Bisher machte ein einziges `PATCH email_verified=false`, auch über einen API-Schlüssel, ein etabliertes lokales Konto zum Kandidaten der Bereinigung unbestätigter Konten im nächsten Lauf, die es ohne Step-up und ohne Hinweis an die anderen Mitglieder seines persönlichen Gartens löschte. Ein gesenktes `email_verified` wird jetzt vermerkt (`email_verified_lowered_at`), und die Bereinigung entfernt ein so vermerktes Konto nie; sie benachrichtigt außerdem die anderen Mitglieder eines persönlichen Gartens, bevor sie ihn löscht. Konten, die ein Administrator vor diesem Release herabgestuft hat, tragen keinen Vermerk — prüfe vor dem nächsten täglichen Lauf jedes unbestätigte Konto eines etablierten Nutzers
- **BREAKING (API):** Die Mandantenlöschung ist asynchron (Issue #1792, REQ-024 AK-53). `DELETE /api/v1/tenants/{slug}` und `DELETE /api/v1/admin/platform/tenants/{key}` antworten jetzt mit `202 Accepted` und einem Body `{tenant_key, status, requested_at, message}` (zuvor `200` mit `{"message": "Tenant deleted"}` bzw. `204` ohne Body). Die Anfrage prüft die Berechtigung und den Step-up, legt den Löschungs-Datensatz an und friert den Mandanten ein (Mitgliedschaften deaktiviert); ein Celery-Task (`app.tasks.tenant_tasks.run_tenant_erasure`) löscht danach in Stapeln zu je 1000 Datensätzen, jeder in einer eigenen ArangoDB-Transaktion, und meldet zwischen den Stapeln ein Lebenszeichen am Datensatz. Die Fehlerantworten `500 TENANT_ERASURE_INCOMPLETE` und `502` der Lösch-Endpunkte entfallen — Fehler des Laufs stehen am Datensatz und werden vom täglichen Lauf wiederholt; ab dem dritten erfolglosen Versuch erscheint das Log-Ereignis `tenant_erasure.escalated`. Aufrufer, die auf einen abgeschlossenen Löschvorgang warteten, müssen den Mandanten als eingefroren behandeln. Beim Deploy bereits laufende Löschungen übernimmt der tägliche Lauf nach sechs Stunden ohne Lebenszeichen
- Plant-Instance- und Pflanzdurchlauf-Pflanzen-Responses enthalten eingebettete `species`- und `cultivar`-Kurzinfos (Denormalisierung), damit das Frontend lesbare Namen ohne zusätzliche Abfragen bilden kann
- Ernte: `batch_id` ist in API-Responses nullbar (`string | null`) statt einer leeren Zeichenkette; der Eindeutigkeitsindex auf `harvest_batches.batch_id` ist `unique + sparse`. Bestandsdaten werden von Migration `v0030` angepasst
- Pflegeerinnerungen: Das Abschließen einer fälligen Gieß-Aufgabe legt die Folgeaufgabe unmittelbar an — zuvor entstand sie erst beim nächtlichen Planungslauf
- Pflegeerinnerungen: Eine Bestätigung schließt nur noch Pflegeaufgaben, die heute oder früher fällig sind; eine bereits eingeplante Folgeaufgabe bleibt erhalten

## In Entwicklung

- REQ-025 (Datenschutz/DSGVO): DSGVO Art. 15–21 Betroffenenrechte — spezifiziert, nicht implementiert
- REQ-027 (Light-Modus): Anonymer Zugang für lokale Instanzen — spezifiziert, nicht implementiert
- OAuth/OIDC: Vollständige Implementierung (Engine aktuell Stub)
- TimescaleDB-Integration: Repository und Migrations vorhanden, Feature-Flag gesteuert
