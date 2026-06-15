# Bilderkennung in Betrieb nehmen (Inferenz-Service)

Diese Seite beschreibt die Inbetriebnahme des `inference-service` für die self-hosted Pflanzen-Bilderkennung (REQ-029-A). Der Inferenz-Service ist eine optionale Komponente — Kamerplanter funktioniert vollständig ohne sie; die Bilderkennung ist dann nicht verfügbar.

---

## Überblick: Was wird installiert?

Der Inferenz-Service (`src/inference-service/`) ist ein eigenständiger FastAPI-Microservice, der:

- das DINOv2-Modell (ViT-S/14, Apache-2.0, ~21 M Parameter) als ONNX-Artefakt lädt,
- Bilder vorverarbeitet und in Embedding-Vektoren (384 Dimensionen) umrechnet,
- diese Vektoren gegen einen **Referenz-Index** in pgvector abgleicht und die ähnlichsten Pflanzenarten zurückgibt.

Der Service läuft als separater Pod im `kamerplanter-ki`-Helm-Release und ist nur intern erreichbar (ClusterIP). Er kommuniziert mit derselben pgvector-Datenbank, die auch der Knowledge-Service nutzt (`kamerplanter_vectors`), aber in einer eigenen Tabelle (`species_embeddings`).

---

## Aktivierungsreihenfolge

!!! warning "Reihenfolge einhalten"
    Die drei Schritte müssen in der angegebenen Reihenfolge ausgeführt werden. Wenn du `INFERENCE_SERVICE_ENABLED=true` setzt, bevor der Referenz-Index befüllt ist, ist die lokale Erkennung nicht verfügbar — das Backend fällt dann direkt auf Pl@ntNet zurück (sofern konfiguriert).

### Schritt 1: Inferenz-Service starten (Skaffold)

```bash
# Im Projektverzeichnis (Entwicklung):
skaffold dev -m ki
```

Das `ki`-Profil startet den `inference-service` zusammen mit dem Knowledge-Service und dem Reranker-Service. Beim ersten Start wird das ONNX-Modell im Build-Schritt exportiert — das dauert je nach Hardware 5–15 Minuten.

!!! tip "Modell-Export wird gecacht"
    Nach dem ersten Build liegt das Modell im Layer-Cache. Folgestarts sind in wenigen Sekunden abgeschlossen.

**Prüfen, ob der Service läuft:**

```bash
# Port-Forward (lokale Entwicklung):
kubectl port-forward svc/kamerplanter-ki-inference-service 8090:8000 -n default

# Readiness prüfen:
curl http://localhost:8090/ready
# Erwartete Antwort: {"status": "ready", "model": "dinov2_vits14", "dim": 384}

# Modellinformationen abrufen:
curl http://localhost:8090/modelinfo
```

### Schritt 2: Referenz-Index befüllen

Der Referenz-Index enthält Embedding-Vektoren für alle Pflanzenarten aus den Stammdaten. Er wird durch einen Celery-Task befüllt, der Referenzbilder von GBIF abruft (nur CC0/CC-BY-Lizenzen), einbettet und die Vektoren in pgvector speichert. **Originalbilder werden dabei nicht persistiert.**

```bash
# Celery-Task für alle Arten starten (einmalig, dauert je nach Artenzahl mehrere Stunden):
kubectl exec -it deploy/kamerplanter-backend -n default -- \
  python -m celery -A app.celery_app call \
  app.tasks.reference_image_tasks.acquire_all_reference_images_task

# Alternativ: über die Backend-API (Admin-Endpoint):
curl -X POST http://localhost:8000/api/v1/admin/reference-images/acquire-all \
  -H "Authorization: Bearer <admin-token>"
```

**Fortschritt verfolgen:**

```bash
# Abdeckungs-Report abfragen (wie viele Arten sind erkennbar?):
curl http://localhost:8000/api/v1/admin/reference-images/coverage \
  -H "Authorization: Bearer <admin-token>"
```

Die Antwort zeigt pro Art, wie viele Referenzbilder indexiert wurden und ob die Art als "erkennbar" gilt (mindestens 5 Referenzen):

```json
{
  "total_species": 210,
  "usable_for_recognition": 187,
  "not_usable": 23,
  "species_below_threshold": [
    {"species_key": "species_alocasia_zebrina", "references": 2},
    ...
  ]
}
```

!!! note "Abdeckungslücken"
    Arten mit weniger als 5 Referenzbildern erscheinen nicht in Erkennungsergebnissen. Das System kommuniziert dies ehrlich im UI. Häufige Ursachen für Lücken: seltene Arten, exotische Zimmerpflanzen oder Arten ohne CC0/CC-BY-Fotos in GBIF.

### Schritt 3: Lokalen Pfad aktivieren

Setze die Umgebungsvariable im Backend:

```bash
# values-dev-ki.yaml oder Umgebungsvariable:
INFERENCE_SERVICE_ENABLED=true
```

!!! danger "Nur aktivieren wenn Index befüllt ist"
    Wenn `INFERENCE_SERVICE_ENABLED=true` gesetzt ist und der Referenz-Index leer ist, fällt das System auf Pl@ntNet zurück — aber **nur wenn ein Pl@ntNet-Key konfiguriert und Consent erteilt ist**. Ist beides nicht der Fall, liefert die Erkennung keine Ergebnisse.

---

## Helm-Konfiguration (Produktion)

Der Inferenz-Service ist Teil des `kamerplanter-ki` Helm-Release. Die Konfiguration erfolgt in `values-ki.yaml`:

```yaml
# helm/kamerplanter-ki/values-ki.yaml

inference-service:
  controllers:
    main:
      containers:
        main:
          image:
            repository: ghcr.io/nolte/kamerplanter-inference-service
            tag: latest              # In Produktion: feste Version verwenden
          env:
            VECTORDB_HOST: "kamerplanter-timescaledb"
            VECTORDB_PORT: "5432"
            VECTORDB_DATABASE: "kamerplanter_vectors"
            VECTORDB_USER: "..."
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
    INFERENCE_SERVICE_URL: "http://kamerplanter-ki-inference-service:8000"
```

### Ressourcenbedarf

| Szenario | RAM | CPU | Latenz/Anfrage |
|----------|-----|-----|---------------|
| DINOv2 ViT-S/14 (MVP) | 512 MB – 1 GB | 0,5–2 Kerne | 500ms–2s (CPU) |
| DINOv2 ViT-B/14 (genauer) | 1–2 GB | 1–4 Kerne | 1–4s (CPU) |

!!! tip "Raspberry Pi / ARM"
    DINOv2 ViT-S/14 läuft auf ARM64 (Raspberry Pi 4/5, Apple Silicon). Die Latenz ist höher (~3–8s), aber für Batch-Indexierung und interaktive Erkennung ausreichend.

---

## Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|----------|:-------:|----------|-------------|
| `VECTORDB_HOST` | Ja | — | Hostname der pgvector-Datenbank |
| `VECTORDB_PORT` | Nein | `5432` | Port der pgvector-Datenbank |
| `VECTORDB_DATABASE` | Ja | `kamerplanter_vectors` | Datenbankname |
| `VECTORDB_USER` | Ja | — | Datenbankbenutzer |
| `VECTORDB_PASSWORD` | Ja | — | Datenbankpasswort |
| `MODEL_NAME` | Nein | `dinov2_vits14` | ONNX-Modellname (`dinov2_vits14` oder `dinov2_vitb14`) |
| `MODEL_PATH` | Nein | `/app/models/model.onnx` | Pfad zum ONNX-Modellartefakt |
| `CONFIDENCE_AUTO_ACCEPT` | Nein | `0.85` | Konfidenz-Schwelle für direkte Übernahme |
| `CONFIDENCE_SHOW_RESULTS` | Nein | `0.10` | Minimale Konfidenz für Anzeige in der Liste |
| `MAX_RESULTS` | Nein | `5` | Maximale Anzahl Vorschläge pro Anfrage |

| Variable (Backend) | Pflicht | Standard | Beschreibung |
|--------------------|:-------:|----------|-------------|
| `INFERENCE_SERVICE_ENABLED` | Nein | `false` | Lokalen Inferenz-Pfad aktivieren |
| `INFERENCE_SERVICE_URL` | Nein | `http://kamerplanter-ki-inference-service:8000` | Interne URL des Inferenz-Service |
| `PLANTNET_API_KEY` | Nein | — | Pl@ntNet API-Key für Fallback (optional) |

---

## Endpunkte des Inferenz-Service (intern)

Die Endpunkte sind nur clusterintern erreichbar und nicht über den Ingress exponiert.

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `POST` | `/embed` | Einzelbild → Embedding-Vektor |
| `POST` | `/embed/batch` | Mehrere Bilder → Embedding-Vektoren (Beschaffung) |
| `POST` | `/match` | Bild → Top-k ähnlichste Arten mit Konfidenz |
| `POST` | `/reference` | Embedding + Provenienz in pgvector speichern |
| `DELETE` | `/reference/{species_key}` | Referenzen einer Art löschen (Re-Index) |
| `GET` | `/health` | Liveness-Probe |
| `GET` | `/ready` | Readiness-Probe (Modell geladen?) |
| `GET` | `/modelinfo` | Modellname, Dimension, Lizenz, Prüfsumme |

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
    Die auf dem PlantCLEF-2024-Datensatz feinabgestimmten DINOv2-Gewichte stehen unter CC-BY-NC-Lizenz (nicht-kommerziell). Diese Gewichte werden **nicht** verwendet. Kamerplanter nutzt ausschließlich das Apache-2.0-lizenzierte Basis-Backbone von `facebookresearch/dinov2`.

---

## Fehlerbehebung

??? question "Der Inferenz-Service startet nicht — Fehler: Modell nicht gefunden"
    Das ONNX-Artefakt wurde möglicherweise nicht exportiert. Prüfe den Build-Log des `inference-service`-Images auf den Schritt `export_dinov2_onnx.py`. Führe `skaffold build -m ki` erneut aus.

??? question "Erkennung liefert immer 'keine Ergebnisse' obwohl der Service läuft"
    Prüfe ob der Referenz-Index befüllt ist (`/api/v1/admin/reference-images/coverage`). Ein leerer Index liefert keine Treffer. Führe `acquire_all_reference_images_task` aus (Schritt 2).

??? question "Die Celery-Task läuft sehr lange — ist das normal?"
    Ja. Der GBIF-Abruf für ~210 Arten mit je bis zu 40 Bild-Kandidaten, anschließender Embedding-Berechnung und HNSW-Indexierung dauert 2–8 Stunden, abhängig von Hardware und Netzwerkgeschwindigkeit. Der Task ist idempotent — du kannst ihn bei Abbruch erneut starten.

??? question "Wie aktualisiere ich den Referenz-Index für eine einzelne Art?"
    Rufe `acquire_reference_images_task` mit dem `species_key` der Art auf oder nutze den Admin-Endpoint `POST /api/v1/admin/reference-images/acquire/{species_key}`.

---

## Siehe auch

- [Pflanzen-Bilderkennung verwenden](../user-guide/plant-identification.md)
- [Architektur der Bilderkennung](../architecture/ai-architecture.md#bilderkennung-dinov2)
- [Betriebsprofile](betriebsprofile.md) — Welche KI-Komponenten sind in welchem Profil enthalten?
- [Helm Charts](helm.md) — Allgemeine Helm-Konfiguration
- [Umgebungsvariablen](../reference/environment-variables.md)
