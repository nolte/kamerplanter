# Bilderkennung in Betrieb nehmen (Inferenz-Service)

Diese Seite beschreibt die Inbetriebnahme des `inference-service` für die selbst gehostete Pflanzen-Bilderkennung (interne Anforderungsreferenz REQ-029-A). Der Inferenz-Service ist eine optionale Komponente — Kamerplanter funktioniert vollständig ohne sie; die Bilderkennung ist dann nicht verfügbar.

---

## Überblick: Was wird installiert?

Der Inferenz-Service (`src/inference-service/`) ist ein eigenständiger FastAPI-Microservice, der:

- das DINOv2-Modell (ViT-S/14, Apache-2.0, ~21 M Parameter) als ONNX-Artefakt (Open Neural Network Exchange) lädt,
- Bilder vorverarbeitet und in Embedding-Vektoren (384 Dimensionen) umrechnet,
- diese Vektoren gegen einen **Referenz-Index** in pgvector abgleicht und die ähnlichsten Pflanzenarten zurückgibt.

Der Service ist ein **optionales, eigenständiges** Modul. Er läuft im eigenen Helm-Release `kamerplanter-recognition` (Skaffold-Profil `recognition`) und ist nur clusterintern erreichbar (ClusterIP). Damit lässt sich die Bilderkennung unabhängig vom RAG-Stack (dem Retrieval-Augmented-Generation-Stack des Knowledge-Service) betreiben oder ganz weglassen. Den pgvector-Speicher teilt er sich mit dem Knowledge-Service: die Datenbank `kamerplanter_vectors` aus dem `kamerplanter-ki`-Release, darin aber eine eigene Tabelle (`species_embeddings`). Die `kamerplanter-ki`-vectordb muss daher laufen, wenn das `recognition`-Profil startet.

---

## Aktivierungsreihenfolge

!!! warning "Reihenfolge einhalten"
    Die drei Schritte müssen in der angegebenen Reihenfolge ausgeführt werden. Wird `INFERENCE_SERVICE_ENABLED=true` gesetzt, bevor der Referenz-Index befüllt ist, ist die lokale Erkennung nicht verfügbar — das Backend fällt dann direkt auf Pl@ntNet zurück (sofern konfiguriert).

### Schritt 1: Inferenz-Service starten (Skaffold)

```bash
# Im Projektverzeichnis (Entwicklung):
# Das recognition-Profil teilt sich die pgvector-DB mit dem ki-Stack,
# daher beide Module zusammen starten:
skaffold dev -m ki -m recognition
```

Das `recognition`-Profil startet ausschließlich den `inference-service` (eigenes Release `kamerplanter-recognition`); das `ki`-Profil stellt die gemeinsam genutzte pgvector-DB bereit. Beim ersten Start wird das ONNX-Modell im Build-Schritt exportiert — das dauert je nach Hardware 5–15 Minuten.

!!! tip "Modell-Export wird gecacht"
    Nach dem ersten Build liegt das Modell im Layer-Cache. Folgestarts sind in wenigen Sekunden abgeschlossen.

**Prüfen, ob der Service läuft:**

```bash
# Port-Forward (lokale Entwicklung):
kubectl port-forward svc/kamerplanter-recognition 8090:8000 -n default

# Readiness prüfen (ist das Modell geladen?):
curl http://localhost:8090/ready
# Erwartete Antwort: {"status": "ok"}

# Modellinformationen abrufen:
curl http://localhost:8090/modelinfo
# Antwort enthält: model, dim, input_size, license, checksum
```

### Schritt 2: Referenz-Index befüllen

Der Referenz-Index enthält Embedding-Vektoren für alle Pflanzenarten aus den Stammdaten. Er wird durch einen Celery-Task befüllt, der Referenzbilder von GBIF (Global Biodiversity Information Facility) und Wikimedia Commons abruft (nur CC0/CC-BY-Lizenzen), einbettet und die Vektoren in pgvector speichert. **Originalbilder werden dabei nicht persistiert.**

!!! info "Dieser Schritt befüllt auch die UI-Bilder in der Artenansicht"
    Nach Abschluss dieses Tasks erscheinen in der **Artenliste** Thumbnails und auf der **Artdetailseite** eine vollständige Referenzbild-Galerie. Beide Ansichten zeigen vor dem ersten Beschaffungslauf einen Platzhalter-Hinweis. Lizenz-Attribution (CC-BY) wird automatisch in den Metadaten mitgeführt und im UI angezeigt. Weitere Informationen: [Referenzbilder in der Artenansicht](../user-guide/plant-management.md#referenzbilder-in-der-artenansicht).

```bash
# Celery-Task für alle Arten starten (einmalig, dauert je nach Artenzahl mehrere Stunden):
kubectl exec -it deploy/kamerplanter-backend -n default -- \
  celery -A app.tasks call \
  app.tasks.reference_image_tasks.acquire_all_reference_images_task

# Alternativ: über die Backend-API (Admin-Endpoint):
curl -X POST http://localhost:8000/api/v1/admin/reference-images/acquire \
  -H "Authorization: Bearer <admin-token>"
```

**Fortschritt verfolgen:**

```bash
# Abdeckungs-Report abfragen (wie viele Arten sind erkennbar?):
curl http://localhost:8000/api/v1/admin/reference-images/coverage \
  -H "Authorization: Bearer <admin-token>"
```

Die Antwort zeigt pro Art, wie viele Referenzbilder akzeptiert wurden und ob die Art als "erkennbar" gilt (`usable_for_recognition`, mindestens 5 akzeptierte Referenzen):

```json
{
  "total_species": 66,
  "usable_species": 48,
  "entries": [
    {
      "species_key": "species_alocasia_zebrina",
      "scientific_name": "Alocasia zebrina",
      "accepted": 2,
      "candidates_found": 7,
      "usable_for_recognition": false,
      "license_breakdown": {"CC0": 1, "CC_BY": 1}
    }
  ]
}
```

!!! note "Abdeckungslücken"
    Arten mit weniger als 5 akzeptierten Referenzbildern erscheinen nicht in Erkennungsergebnissen. Das System kommuniziert dies ehrlich im UI. Häufige Ursachen für Lücken: seltene Arten, exotische Zimmerpflanzen oder Arten ohne CC0/CC-BY-Fotos in GBIF.

**Admin-API-Endpunkte für die Referenzbild-Beschaffung (Übersicht):**

| Methode | Endpunkt | Beschreibung |
|---------|----------|-------------|
| `POST` | `/api/v1/admin/reference-images/acquire` | Beschaffungslauf für alle Arten starten |
| `POST` | `/api/v1/admin/reference-images/acquire/{species_key}` | Beschaffungslauf für eine einzelne Art starten oder wiederholen |
| `GET` | `/api/v1/admin/reference-images/coverage` | Abdeckungs-Report: erkennbare Arten, Arten unter Schwellenwert |

Alle drei Endpunkte erfordern einen gültigen Admin-Token (`Authorization: Bearer <admin-token>`). Die Endpunkte sind über den regulären Backend-Ingress erreichbar — es ist kein separater Port-Forward nötig.

### Schritt 3: Lokalen Pfad aktivieren

Setze die Umgebungsvariable im Backend:

```bash
# Backend-Env (values-dev.yaml) oder Umgebungsvariable:
INFERENCE_SERVICE_ENABLED=true
```

!!! danger "Nur aktivieren wenn Index befüllt ist"
    Wenn `INFERENCE_SERVICE_ENABLED=true` gesetzt ist und der Referenz-Index leer ist, fällt das System auf Pl@ntNet zurück — aber **nur, wenn ein Pl@ntNet-Key konfiguriert und die Einwilligung erteilt ist**. Ist beides nicht der Fall, liefert die Erkennung keine Ergebnisse.

---

## Helm-Konfiguration (Produktion)

Der Inferenz-Service hat ein eigenes Helm-Release `kamerplanter-recognition`. Die Konfiguration erfolgt in `values-dev-recognition.yaml`:

```yaml
# helm/kamerplanter/values-dev-recognition.yaml

inference-service:
  controllers:
    main:
      containers:
        main:
          image:
            repository: ghcr.io/nolte/kamerplanter-inference-service
            tag: latest              # In Produktion: feste Version verwenden
          env:
            VECTORDB_HOST: "kamerplanter-ki-vectordb"
            VECTORDB_PORT: "5432"
            VECTORDB_DATABASE: "kamerplanter_vectors"
            VECTORDB_USERNAME: "..."
            VECTORDB_PASSWORD: "..."
            MODEL_NAME: "dinov2_vits14"
            CONFIDENCE_AUTO_ACCEPT: "0.85"
            CONFIDENCE_SHOW_RESULTS: "0.10"
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "2"
              memory: 1Gi           # DINOv2 ViT-S/14 + ONNX Runtime

  service:
    main:
      type: ClusterIP
      ports:
        http:
          port: 8000

# Backend — Inference-Service-Verbindung
backend:
  env:
    INFERENCE_SERVICE_ENABLED: "true"
    INFERENCE_SERVICE_URL: "http://kamerplanter-recognition:8000"
```

### Ressourcenbedarf

| Szenario | RAM | CPU | Latenz/Anfrage |
|----------|-----|-----|---------------|
| DINOv2 ViT-S/14 | 512 MB – 1 GB | 0,5–2 Kerne | 500ms–2s (CPU) |

!!! tip "Raspberry Pi / ARM"
    DINOv2 ViT-S/14 läuft auf ARM64 (Raspberry Pi 4/5, Apple Silicon). Die Latenz ist höher (~3–8s), aber für Batch-Indexierung und interaktive Erkennung ausreichend.

---

## Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|----------|:-------:|----------|-------------|
| `VECTORDB_HOST` | Nein | `localhost` | Hostname der pgvector-Datenbank (im Cluster: `kamerplanter-ki-vectordb`) |
| `VECTORDB_PORT` | Nein | `5432` | Port der pgvector-Datenbank |
| `VECTORDB_DATABASE` | Nein | `kamerplanter_vectors` | Datenbankname |
| `VECTORDB_USERNAME` | Nein | `postgres` | Datenbankbenutzer |
| `VECTORDB_PASSWORD` | Nein | `changeme` | Datenbankpasswort (in Produktion zwingend überschreiben) |
| `MODEL_NAME` | Nein | `dinov2_vits14` | ONNX-Modellname |
| `MODEL_PATH` | Nein | `/app/models/dinov2` | Verzeichnis mit dem ONNX-Modellartefakt (`model.onnx`) |
| `CONFIDENCE_AUTO_ACCEPT` | Nein | `0.85` | Konfidenz-Schwelle für direkte Übernahme |
| `CONFIDENCE_SHOW_RESULTS` | Nein | `0.10` | Minimale Konfidenz für Anzeige in der Liste |

| Variable (Backend) | Pflicht | Standard | Beschreibung |
|--------------------|:-------:|----------|-------------|
| `INFERENCE_SERVICE_ENABLED` | Nein | `false` | Lokalen Inferenz-Pfad aktivieren |
| `INFERENCE_SERVICE_URL` | Nein | `http://kamerplanter-recognition:8000` | Interne URL des Inferenz-Service |
| `PLANTNET_API_KEY` | Nein | — | Pl@ntNet API-Key für Fallback (optional) |

---

## Endpunkte des Inferenz-Service (intern)

Die Endpunkte sind nur clusterintern erreichbar und nicht über den Ingress exponiert.

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `POST` | `/embed` | Einzelbild → Embedding-Vektor |
| `POST` | `/embed/batch` | Mehrere Bilder → Embedding-Vektoren (Beschaffung) |
| `POST` | `/match` | Bild → Top-k ähnlichste Arten mit Konfidenz (Query-Param `k`, Standard `5`, max. `50`) |
| `POST` | `/reference` | Embedding + Provenienz in pgvector speichern |
| `GET` | `/reference/{species_key}` | Indexierte Referenzen einer Art abrufen |
| `DELETE` | `/reference/{species_key}` | Referenzen einer Art löschen (Re-Index) |
| `GET` | `/health` | Liveness-Probe |
| `GET` | `/ready` | Readiness-Probe (Modell geladen?) |
| `GET` | `/modelinfo` | Modellname, Dimension, Eingabegröße, Lizenz, Prüfsumme |

---

## Lizenzen und Rechtliches

| Komponente | Lizenz | Hinweis |
|------------|--------|---------|
| DINOv2 Basis-Backbone (Meta) | Apache-2.0 | Vor Produktivnahme LICENSE im offiziellen Repo verifizieren |
| ONNX Runtime (Microsoft) | MIT | — |
| Referenzbilder (GBIF) | CC0 / CC-BY | Nur diese Lizenzen werden indexiert |
| PlantCLEF Fine-tune-Gewichte | CC-BY-NC | **Werden nicht verwendet** (nicht-kommerzielle Einschränkung) |
| Pl@ntNet API (Fallback) | ToS, frei ≤500/Tag | Nur mit Nutzer-Consent, nur als Fallback |

!!! danger "PlantCLEF-Gewichte nicht verwenden"
    Die auf dem PlantCLEF-2024-Datensatz fein abgestimmten DINOv2-Gewichte stehen unter CC-BY-NC-Lizenz (nicht-kommerziell). Diese Gewichte werden **nicht** verwendet. Kamerplanter nutzt ausschließlich das Apache-2.0-lizenzierte Basis-Backbone von `facebookresearch/dinov2`.

---

## Fehlerbehebung

??? question "Der Inferenz-Service startet nicht — Fehler: Modell nicht gefunden"
    Das ONNX-Artefakt wurde möglicherweise nicht exportiert. Prüfe den Build-Log des `inference-service`-Images auf den Schritt `export_dinov2_onnx.py`. Führe `skaffold build -m recognition` erneut aus.

??? question "Erkennung liefert immer 'keine Ergebnisse' obwohl der Service läuft"
    Prüfe, ob der Referenz-Index befüllt ist (`/api/v1/admin/reference-images/coverage`). Ein leerer Index liefert keine Treffer. Führe `acquire_all_reference_images_task` aus (Schritt 2).

??? question "Die Celery-Task läuft sehr lange — ist das normal?"
    Ja. Der GBIF-Abruf für alle angelegten Arten — mit je bis zu 40 Bild-Kandidaten, anschließender Embedding-Berechnung und Indexierung — kann je nach Artenzahl, Hardware und Netzwerkgeschwindigkeit mehrere Stunden dauern. Der Task ist idempotent — bei Abbruch lässt er sich erneut starten.

??? question "Wie aktualisiere ich den Referenz-Index für eine einzelne Art?"
    Nutze den Admin-Endpoint `POST /api/v1/admin/reference-images/acquire/{species_key}` — er löst intern den Celery-Task `acquire_reference_images_task` für die Art aus.

---

## Siehe auch

- [Pflanzen-Bilderkennung verwenden](../user-guide/plant-identification.md)
- [Architektur der Bilderkennung](../architecture/ai-architecture.md#bilderkennung-dinov2)
- [Betriebsprofile](betriebsprofile.md) — Welche KI-Komponenten sind in welchem Profil enthalten?
- [Helm Charts](helm.md) — Allgemeine Helm-Konfiguration
- [Umgebungsvariablen](../reference/environment-variables.md)
