# Spezifikation: REQ-029-A - Self-Hosted Bilderkennung: DINOv2-Embedding-Matching & Referenzbild-Beschaffung

```yaml
ID: REQ-029-A
Titel: Self-Hosted Pflanzen-Bilderkennung (DINOv2-Embedding-Matching) & Referenzbild-Beschaffung
Kategorie: Integration / KI
Fokus: Backend (Inferenz-Microservice), Datenbeschaffung, Architektur
Technologie: Python 3.14+, ONNX Runtime, FastAPI, ArangoDB (Vektor-Index), Celery, React/TypeScript
Status: Entwurf
Version: 1.1
Quelle: spec/analysis/n-001-pflanzenerkennung-bilderkennung-research.md (Deep-Research, 2026-06-15)
Korrigiert: REQ-029 v1.0 (primärer Dienst Plant.id ist kostenpflichtig → disqualifiziert; siehe §0)
Geändert (v1.1): Roll-out in zwei Phasen — Pl@ntNet-Free-Tier-Adapter als sofort lauffähiger Phase-1-Primäradapter, DINOv2-Embedding-Matching als Phase-2-Zielarchitektur (siehe §0.1)
Abhängigkeit: REQ-001 v5.0 (Stammdaten/Species), REQ-010 v1.0 (IPM), REQ-011 v1.0 (Adapter-Pattern), REQ-025 (Datenschutz), REQ-029 v1.0 (Adapter-Interface, Consent, EXIF, Frontend — wiederverwendet)
```

---

## 0. Verhältnis zu REQ-029 v1.0 (Korrektur der Architekturprämisse)

REQ-029 v1.0 spezifiziert Bilderkennung mit **Plant.id (Kindwise) als primärem Dienst** und PlantNet als Fallback. Die Deep-Research (`spec/analysis/n-001-pflanzenerkennung-bilderkennung-research.md`) hat diese Prämisse **widerlegt** gegen die harten Projektvorgaben:

| Vorgabe | REQ-029 v1.0 (Plant.id primär) | Bewertung |
|---|---|---|
| **Keine Zusatzkosten für Endnutzer** | Plant.id: nur 100 Test-IDs, danach pro-Request kostenpflichtig (ab 0,05 €/ID, 29–99 €/Monat lt. eigener Kostenübersicht) | ❌ **verletzt** |
| **Lizenztechnisch frei verwendbar** | Externer Closed-Source-Dienst, kein self-hostbarer Erkennungspfad | ❌ nicht erfüllbar |
| **DSGVO / Datenhoheit** | Nutzerfotos verlassen die Infrastruktur (Drittland-Verarbeitung) | ⚠️ nur mit AVV + Consent |

**REQ-029-A definiert daher die verbindliche Ziel-Architektur neu:**

1. **Primär (MVP):** **Self-hosted DINOv2-Embedding-Matching** gegen die eigenen Stammdaten — vollständig kostenlos, lizenzsauber (Apache-2.0-Backbone), DSGVO-konform (Fotos verlassen die Infrastruktur nicht).
2. **Fallback (optional):** **Pl@ntNet Free-Tier** (≤500 IDs/Tag, Fotos nicht persistiert) — nur bei niedriger lokaler Konfidenz und nur mit Consent.
3. **Plant.id:** wird vom Default zum **rein optionalen Operator-Opt-in** herabgestuft („nur wenn Betreiber die Pro-Request-Kosten bewusst akzeptiert" — kein Standardpfad). Krankheitsdiagnose über Plant.id ist damit **nicht** der vorgesehene Weg für Aufgabe B (siehe §6).

**Wiederverwendet aus REQ-029 v1.0** (nicht erneut spezifiziert): `PlantIdentificationAdapter`-Interface (§3.1), `IdentificationAdapterRegistry` (§3.4), Consent-Mechanismus `plant_identification` (§5), EXIF-Stripping (§5.4), `PlantIdentificationDialog`-Frontend + Onboarding-/IPM-Integration (§4), `identification_requests`/`diagnosis_requests`-Collections (§2). REQ-029-A ergänzt einen **lokalen Adapter** in genau dieser Registry und ersetzt die Default-Priorisierung.

---

## 0.1 Roll-out in zwei Phasen (Pl@ntNet-first) — verbindlich ab v1.1

Die **Ziel-Architektur** (§0, §2) bleibt unverändert: langfristig ist der self-hosted `LocalEmbeddingAdapter` (DINOv2) der primäre, kosten- und datenschutzoptimale Erkennungspfad. Davon zu **unterscheiden** ist die **Roll-out-Reihenfolge**: Der DINOv2-Pfad erfordert einen neuen Inferenz-Microservice (§3), einen ONNX-Modell-Build (§2.3) und eine vollständig durchlaufene Referenzbild-Beschaffung (§4) — bis dahin gibt es keinen Referenz-Index, gegen den gematcht werden könnte. Um sofort ein **lauffähiges, kostenfreies** Erkennungsfeature auszuliefern, erfolgt die Umsetzung in zwei Phasen.

| | **Phase 1 — Pl@ntNet-first (MVP-Auslieferung)** | **Phase 2 — DINOv2-Zielarchitektur** |
|---|---|---|
| **Primäradapter (Prio 1)** | `PlantNetAdapter` (REQ-029 §3.3, Free-Tier ≤500/Tag) | `LocalEmbeddingAdapter` (REQ-029-A §3.4) |
| **Fallback (Prio 2)** | — (optional: Plant.id nur bei Operator-Opt-in) | `PlantNetAdapter` (rückt auf Prio 2) |
| **Neue Infrastruktur** | keine — nur App-Adapter + Frontend-Capture + Consent | Inferenz-Microservice, ONNX-Build, GBIF-Beschaffung, Vektor-Index |
| **Foto verlässt Instanz?** | ja → Pl@ntNet (Consent **Pflicht**, EXIF-Strip, opt-in) | nein im Primärpfad (lokal); Pl@ntNet nur als Consent-Fallback |
| **Scope** | Aufgabe A (Artbestimmung) | Aufgabe A lokal; B/C als Stufe 3/4 (§6) |

### 0.1.1 Verbindliche Festlegungen für Phase 1

1. **Adapter-Priorität ist konfigurierbar**, nicht hartkodiert. Die `IdentificationAdapterRegistry` (REQ-029 §3.4) liefert den bevorzugten Adapter über eine **Konfiguration** (`IDENTIFICATION_PRIMARY_ADAPTER`, Default in Phase 1 = `"plantnet"`). Der Wechsel auf `"local_embedding"` in Phase 2 ist eine reine Konfigurations-/Registrierungsänderung — **kein** Eingriff in Engine, Service, API oder Frontend.
2. **Pl@ntNet ist in Phase 1 kein Fallback, sondern Primärpfad.** Da das Nutzerfoto damit zwingend an einen Dritten geht, ist der Consent `plant_identification` (REQ-029 §5) in Phase 1 **harte Voraussetzung** für jede Identifikation (nicht nur für einen optionalen Fallback). Ohne Consent ist das Feature nicht nutzbar; der Datenschutzhinweis nennt Pl@ntNet als Empfänger und die Query-Metadaten-Speicherung. Das EXIF-Stripping (REQ-029 §5.4) gilt unverändert.
3. **Kandidaten-Auswahl ist Pflichtbestandteil von Phase 1** (Nutzer-Anforderung „zwischen verschiedenen Arten wählen"): Die `PlantNetAdapter`-Antwort liefert eine **Vorschlagsliste** (`IdentificationSuggestion[]`, nach `rank` sortiert). Das Frontend zeigt die Top-k zur **expliziten Auswahl** durch den Nutzer; die Auswahl wird über `select_result(selected_rank)` (REQ-029 §3.5) persistiert und mündet erst danach in „Pflanze anlegen". Es erfolgt **kein stilles Auto-Anlegen** der Top-1, auch nicht oberhalb `CONFIDENCE_AUTO_ACCEPT`.
4. **Bildquelle Webcam und Smartphone** (Nutzer-Anforderung): Das `PlantIdentificationDialog` (REQ-029 §4.1) bietet beide Erfassungswege an — `navigator.mediaDevices.getUserMedia()` für die Live-Webcam (Desktop/Kiosk) und `<input type="file" accept="image/*" capture="environment">` für die Smartphone-Rückkamera; zusätzlich Datei-Upload/Drag&Drop. Erfasste Bilder werden vor dem Versand auf das Pl@ntNet-Limit (Auflösung/Format) normalisiert und EXIF-gestript.
5. **Phase 1 darf keine Phase-2-Brücken verbauen:** API-Vertrag (`/identify`, Request/Response-Schemas), `identification_requests`-Collection und Frontend-Dialog werden so umgesetzt, dass Phase 2 ausschließlich einen weiteren Adapter registriert und die Default-Priorität umschaltet. Insbesondere bleibt das `external_id`-Schema adapterneutral (`plantnet:<gbifId>` bzw. später `local:<species_key>`), und die Engine bleibt gegen das `PlantIdentificationAdapter`-Interface programmiert.

### 0.1.2 Auswirkung auf die Definition of Done

Die DoD in §10 beschreibt den **Phase-2-Endzustand** (DINOv2). Für die **Phase-1-Auslieferung** gilt die reduzierte DoD in §10.1 (NEU). Die Phase-2-DoD bleibt der Zielzustand und wird nicht abgeschwächt.

---

## 1. Business Case

**User Story (N-001, Casual User):** „Als Zimmerpflanzen-Besitzer, der den Namen seiner Pflanze nicht kennt, möchte ich ein Foto machen und sofort die wahrscheinliche Art erfahren — ohne dass dabei laufende Kosten entstehen oder mein Foto an einen Drittanbieter geht."

**User Story (Betreiber/Self-Hosted):** „Als Betreiber einer Kamerplanter-Instanz möchte ich Bilderkennung anbieten können, ohne ein kostenpflichtiges API-Abo abschließen zu müssen — die Erkennung soll auf meiner eigenen Hardware laufen."

**User Story (Datenschutz):** „Als datenschutzbewusster Nutzer möchte ich, dass meine Pflanzenfotos die Instanz nicht verlassen."

**Kernprinzip:** Die Erkennung erzeugt aus einem Foto einen **Embedding-Vektor** (DINOv2) und sucht die ähnlichsten Referenz-Embeddings der bekannten Arten (ArangoDB-Vektorsuche). DINOv2 ist **kein Klassifikator** — die „Erkennung" entsteht durch Nearest-Neighbor-Matching gegen einen kuratierten Referenz-Index. Das funktioniert **few-shot** (wenige Referenzbilder pro Art genügen) und vermeidet das Training eines großen Klassifikators.

### 1.1 Drei Erkennungsaufgaben (Scope-Staging)

| Aufgabe | Beschreibung | Ansatz | Stufe |
|---|---|---|---|
| **A — Artbestimmung** | Species aus Foto (Kern, N-001) | DINOv2-Embedding-Matching gegen Referenz-Index | **MVP** |
| **B — Krankheit/Schädling** | Blattkrankheiten/Schädlinge (REQ-010 IPM) | Auf PlantDoc fine-getunter Klassifikator | Stufe 3 |
| **C — Zustand/Phänologie** | Wachstumsphase/Blühstadium/Erntereife (REQ-003) | Eigener Klassifikatorkopf auf DINOv2-Embeddings | Stufe 4 (Forschung) |

> **Cultivar-Erkennung ist explizit out of scope** — lizenzfreie, sortengenaue Referenzbilder existieren nicht in ausreichender Menge. Erkennung erfolgt auf **Art-Ebene** (Species).

---

## 2. Zielarchitektur

### 2.1 Komponentenübersicht

```
┌──────────────┐   Foto    ┌─────────────────────┐  Consent/RateLimit  ┌──────────────────────┐
│  React UI    │──────────▶│  Backend (FastAPI)   │────────────────────▶│  IdentificationService│
│ (REQ-029 §4) │           │  /identify Proxy     │   EXIF-Strip         │  (REQ-029 §3.6)       │
└──────────────┘           └─────────────────────┘                      └──────────┬───────────┘
                                                                                    │ get_preferred()
                                                                          ┌─────────▼──────────┐
                                                                          │ AdapterRegistry     │
                                                                          │ (REQ-029 §3.4)      │
                                                                          └─────┬───────┬───────┘
                                                          Prio 1 (lokal) │       │ Prio 2 (Fallback)
                                                       ┌─────────────────▼──┐  ┌─▼────────────────────┐
                                                       │ LocalEmbeddingAdapter│ │ PlantNetAdapter       │
                                                       │ (NEU, REQ-029-A)     │ │ (REQ-029 §3.3, frei)  │
                                                       └──────────┬───────────┘ └───────────────────────┘
                                            HTTP (intern)         │
                                              ┌───────────────────▼─────────────────┐
                                              │  Inference-Microservice (NEU)         │
                                              │  FastAPI + ONNX Runtime               │
                                              │  DINOv2 ViT-S/B (Apache-2.0)          │
                                              │  → liefert Embedding-Vektor (384/768) │
                                              └───────────────────┬───────────────────┘
                                                                  │ Vektor
                                              ┌───────────────────▼─────────────────┐
                                              │  ArangoDB Vektor-Index                │
                                              │  species_embeddings (Referenz-Index)  │
                                              │  → Top-k ähnlichste Arten + Distanz   │
                                              └───────────────────────────────────────┘
```

### 2.2 Architekturentscheidungen

| # | Entscheidung | Begründung (Research-Befund) |
|---|---|---|
| AE-1 | **DINOv2 als Embedding-Extraktor**, nicht als Klassifikator ausliefern | Basis-Backbone Apache-2.0 (ONNX-exportierbar); fertige PlantCLEF-Klassifikatorgewichte sind CC-BY-NC → disqualifiziert |
| AE-2 | **Eigener Inferenz-Microservice** analog `src/knowledge-service/` | Trennung der schweren ML-Abhängigkeiten vom Hauptbackend; ONNX-Runtime-Pattern bereits etabliert |
| AE-3 | **Embedding-Matching statt Klassifikation** für Aufgabe A | Few-shot-tauglich, kein Training nötig, neue Arten durch Hinzufügen von Referenzbildern erweiterbar |
| AE-4 | **ArangoDB-Vektorsuche** als Index | Polyglot-Persistenz vermeiden; n≈210 Arten ist klein → In-App-Cosine als Fallback wenn Vektor-Index der Cluster-Version fehlt (siehe §5.3) |
| AE-5 | **Nur Embeddings persistieren, keine fremden Bilder** | Entschärft CC-BY-SA-ShareAlike-Pflicht erheblich; Provenienz/Lizenz pro Referenzbild wird dennoch protokolliert |
| AE-6 | **CPU-Inferenz als Baseline** (ViT-S/B) | Kein GPU-Zwang → läuft auf Standard-Cluster; Celery-Offloading für Latenztoleranz |

### 2.3 Modellwahl

| Variante | Parameter | Embedding-Dim | Footprint | Empfehlung |
|---|---|---|---|---|
| DINOv2 ViT-S/14 | ~21 M | 384 | CPU, schnell | **MVP-Default** |
| DINOv2 ViT-B/14 | ~86 M | 768 | CPU ok, genauer | Ausbau (PlantCLEF-Standard) |
| DINOv2 ViT-L/14 | ~300 M | 1024 | GPU empfohlen | nur bei Bedarf |

**Verbindlich:** Es wird das **Apache-2.0-Basismodell** von Meta (`facebookresearch/dinov2`) verwendet. Vor Produktivnahme ist die `LICENSE` im offiziellen Repo zu verifizieren (RAG-Hinweis: Meta hat von CC-BY-NC auf Apache-2.0 relizenziert). PlantCLEF-2024-Fine-tune-Gewichte (CC-BY-NC) dürfen **nicht** ausgeliefert werden.

---

## 3. Inferenz-Microservice (NEU)

### 3.1 Aufbau

Eigenständiger Service unter `src/inference-service/` (Struktur analog `src/knowledge-service/`):

- **FastAPI** + **ONNX Runtime** (CPU Execution Provider als Default, CUDA optional).
- Lädt das nach ONNX exportierte DINOv2-Modell beim Start in eine `InferenceSession`.
- **Zustandslos**, horizontal skalierbar, eigenes Helm-Deployment.
- Interne Erreichbarkeit (ClusterIP) — **nicht** öffentlich exponiert.

### 3.2 Preprocessing-Contract (verbindlich, index- und query-identisch)

> **Kritisch:** Embeddings sind nur vergleichbar, wenn Referenz- und Query-Bilder **exakt gleich** vorverarbeitet werden. Abweichung = unbrauchbares Matching.

```python
# src/inference-service/app/preprocessing.py
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
INPUT_SIZE = 224  # Vielfaches von 14 (Patch-Größe); 518 für höhere Genauigkeit

def preprocess(image_bytes: bytes) -> "np.ndarray":
    """RGB → resize(kürzere Kante)→ center-crop(INPUT_SIZE) → ImageNet-Norm → CHW float32."""
    # 1. EXIF-Strip + RGB-Konvertierung (Orientierung anwenden)
    # 2. Resize kürzere Kante auf INPUT_SIZE, Center-Crop INPUT_SIZE×INPUT_SIZE
    # 3. /255.0, (x - MEAN) / STD
    # 4. HWC → CHW, Batch-Dim, float32
    ...
```

### 3.3 Endpunkte (intern)

```python
# POST /embed   — Body: multipart image  → { "embedding": [float, ...], "dim": 384, "model": "dinov2_vits14" }
# POST /embed/batch — mehrere Bilder (für Referenz-Indexierung)
# GET  /healthz — Liveness; GET /readyz — Modell geladen?
# GET  /modelinfo — { model, dim, input_size, license: "Apache-2.0", checksum }
```

### 3.4 LocalEmbeddingAdapter (im Hauptbackend, registriert in der REQ-029-Registry)

```python
class LocalEmbeddingAdapter(PlantIdentificationAdapter):  # Interface aus REQ-029 §3.1
    """Self-hosted Artbestimmung via DINOv2-Embedding-Matching.

    Ruft den internen Inference-Service auf, holt das Embedding und
    matched per ArangoDB-Vektorsuche gegen den Referenz-Index.
    """
    adapter_key = "local_embedding"
    supports_health_assessment = False  # Aufgabe B separat (§6)
    rate_limit_per_day = None           # self-hosted → kein externes Limit

    def __init__(self, inference_client, embedding_repo) -> None:
        self._inference = inference_client      # HTTP-Client zum Inference-Service
        self._embeddings = embedding_repo        # ArangoDB Vektorsuche

    async def identify(self, image_data, *, organ=PlantOrgan.AUTO,
                       max_results=5, include_health=False, language="de"):
        vector = await self._inference.embed(image_data)         # DINOv2-Embedding
        neighbours = await self._embeddings.search(vector, k=max_results)
        suggestions = [
            IdentificationSuggestion(
                rank=i + 1,
                scientific_name=n.scientific_name,
                common_names=n.common_names,
                confidence=cosine_to_confidence(n.distance),     # §3.5
                external_id=f"local:{n.species_key}",
            )
            for i, n in enumerate(neighbours)
        ]
        return IdentificationResult(suggestions=suggestions, is_plant=bool(suggestions))

    async def diagnose(self, image_data, *, language="de"):
        raise NotImplementedError("Health Assessment siehe REQ-029-A §6 (DiseaseClassifier).")

    async def health_check(self) -> bool:
        return await self._inference.is_ready()
```

### 3.5 Konfidenz-Kalibrierung

Cosine-Distanz ist keine Wahrscheinlichkeit. Die Umrechnung in eine angezeigte Konfidenz (0–1) erfolgt über eine kalibrierte Schwellenfunktion, deren Parameter aus der Eigen-Evaluierung (§7) stammen:

- `≥ CONFIDENCE_AUTO_ACCEPT` (Default 0.85): Art direkt vorschlagen.
- `≥ CONFIDENCE_SHOW_RESULTS` (Default 0.10): in Vorschlagsliste anzeigen.
- darunter: „unsicher" + manuelle Suche / Fallback-Adapter anbieten.

Die Schwellen werden aus REQ-029 §3.5 übernommen und durch Messung an den eigenen 210 Arten justiert (kein Literaturwert übernehmen).

---

## 4. Referenzbild-Beschaffung (Kern dieses Dokuments)

Damit das Matching funktioniert, braucht jede Art einen **kuratierten Referenz-Index**. Ziel: **~10–30 lizenzsaubere Referenzbilder pro Art** (few-shot genügt). Die Beschaffung erfolgt **automatisiert**, ohne eigene Fotografie.

### 4.1 Quellen & Lizenz-Filter

| Quelle | Lizenz-Filter | Eignung | Priorität |
|---|---|---|---|
| **GBIF Media-API** | pro Bild: **nur CC0 / CC-BY** übernehmen (CC-BY-NC verwerfen) | Backbone — programmatisch filterbar | 1 |
| **iNaturalist** (CC0/CC-BY-Teilmenge, via GBIF gespiegelt) | nur CC0/CC-BY | gute Bildqualität | 2 |
| **Wikimedia Commons** | CC0 / Public Domain bevorzugt; CC-BY-SA nur Embedding-only (§4.4) | kuratierte „typische" Artbilder | 3 |
| Pl@ntNet-Bilder | CC-BY-SA (ShareAlike) | **meiden** als gespeichertes Material | — |
| iNaturalist Default-Lizenz | CC-BY-NC | **ausschließen** (nicht-kommerziell) | — |

### 4.2 Beschaffungs-Pipeline (Celery-Task / Batch-Skript)

```
Für jede Species (scientific_name) aus REQ-001-Stammdaten:
  1. GBIF Occurrence/Media-API abfragen (taxonKey → media mit Lizenz-Metadaten)
  2. FILTER license ∈ {CC0, CC-BY}; verwerfe CC-BY-NC, CC-BY-SA, unklar
  3. Download Kandidatenbilder (Limit n_max pro Art, z.B. 40)
  4. Qualitäts-/Relevanz-Kuratierung:
       - Mindestauflösung, Seitenverhältnis-Plausibilität
       - optionaler Vor-Filter: DINOv2-Embedding-Ausreißererkennung
         (verwerfe Bilder, die weit vom Art-Clusterzentroid liegen → Habitat/Boden/Beleg)
  5. EXIF-Strip + Preprocessing-Contract (§3.2) anwenden
  6. Embedding via Inference-Service /embed/batch berechnen
  7. Embedding + Provenienz + Lizenz + Attribution in species_embeddings speichern
       (NUR Vektor + Metadaten — KEIN Originalbild persistieren, §4.4)
  8. Pro Art Abdeckungs-Report: Anzahl brauchbarer Referenzen, Lizenzverteilung
```

### 4.3 Erwartete Abdeckung (Research-Einschätzung)

| Artgruppe | Abdeckung | Hinweis |
|---|---|---|
| Gängige Zimmerpflanzen, Gemüse, Kräuter | **hoch (~80–90 %)** | gut in GBIF/iNaturalist (CC0/CC-BY) vertreten |
| Seltene/exotische Zimmerpflanzen | mittel | ggf. Wikimedia-Ergänzung; Lücken protokollieren |
| Cannabis | mittel | botanische DBs zeigen v.a. Freiland/Beleg, kaum Indoor-Stadien |
| Kultivare (Sorten) | **nicht abgedeckt** | out of scope → Art-Ebene |

→ **Verbindlich:** Arten ohne ausreichende Referenzbilder (z.B. < 5) werden im Index **als „nicht erkennbar" markiert** und im Frontend ehrlich kommuniziert (kein stiller Qualitätsverlust).

### 4.4 Lizenz- & Speicher-Strategie (DSGVO/Urheberrecht)

- **Persistiert wird nur der Embedding-Vektor** + Metadaten (Quelle, Lizenz, Urheber, URL) — **nicht** das Originalbild. Das entschärft die CC-BY-SA-ShareAlike-Pflicht erheblich (ShareAlike triggert auf Verteilung von Bild-Derivaten).
- **Attribution** für CC-BY wird in den Metadaten mitgeführt und (falls UI Referenzbilder zeigt) angezeigt.
- **Vor Produktivnahme rechtlich absegnen:** ob die Embedding-Berechnung aus CC-BY-SA/-NC-Bildern für einen ggf. kommerziellen Dienst zulässig ist. Default-sicher: **ausschließlich CC0/CC-BY**.

---

## 5. Datenmodell-Erweiterung (ArangoDB)

### 5.1 Neue Collection `species_embeddings` (Referenz-Index)

```json
{
  "_key": "emb_monstera_deliciosa_gbif_4711",
  "species_key": "species_monstera_deliciosa",
  "scientific_name": "Monstera deliciosa",
  "embedding": [0.0123, -0.456, ...],        // 384 (ViT-S) oder 768 (ViT-B)
  "model": "dinov2_vits14",
  "model_dim": 384,
  "organ": "leaf",
  "source": "gbif",
  "source_record_id": "4711",
  "license": "CC-BY",
  "attribution": "© Jane Doe, via GBIF/iNaturalist",
  "source_url": "https://...",
  "indexed_at": "2026-06-15T10:00:00Z"
}
```

### 5.2 Neue Collection `reference_image_jobs` (Beschaffungs-Protokoll)

```json
{
  "_key": "refjob_20260615_monstera",
  "species_key": "species_monstera_deliciosa",
  "status": "completed",
  "candidates_found": 38,
  "accepted": 22,
  "rejected_license": 11,
  "rejected_quality": 5,
  "license_breakdown": { "CC0": 6, "CC-BY": 16 },
  "usable_for_recognition": true,
  "created_at": "2026-06-15T09:50:00Z"
}
```

### 5.3 Vektorsuche

```aql
// ArangoDB Vektor-Index (ab 3.12+, ggf. --experimental-vector-index nötig)
FOR e IN species_embeddings
  FILTER e.model == @model
  LET dist = APPROX_NEAR_COSINE(e.embedding, @query_vector)
  SORT dist DESC
  LIMIT @k
  COLLECT species_key = e.species_key AGGREGATE best = MAX(dist)
  SORT best DESC
  RETURN { species_key, score: best }
```

> **Versions-Voraussetzung prüfen:** Unterstützt die Cluster-ArangoDB-Version (`3.11+` lt. Stack) keinen Vektor-Index, dient ein **In-App-Cosine über alle Referenz-Embeddings** als Fallback — bei n≈210 Arten × ~20 Embeddings (≈4.200 Vektoren) performant genug. Diese Entscheidung ist in der Implementierung zu treffen und zu dokumentieren.

---

## 6. Aufgabe B & C (Ausbaustufen)

### 6.1 Aufgabe B — Krankheits-/Schädlingserkennung (REQ-010 IPM)

- **Datensatz:** **PlantDoc** (2.598 reale Bilder, 13 Arten, 27 Klassen). Research-Befund: Fine-Tuning auf PlantDoc senkt den Klassifikationsfehler um **bis zu 31 %** gegenüber Labordaten (PlantVillage überträgt **nicht** auf Feldfotos; nur ergänzend für Studiobilder).
- **Ansatz:** Klassifikatorkopf auf DINOv2-Embeddings **oder** fine-getunter Vision-Backbone, als ONNX im selben Inference-Service. Ergebnis-Mapping gegen IPM-Stammdaten (REQ-010), Behandlungsvorschläge aus eigenen Daten.
- **Caveat:** PlantDoc deckt v.a. Gemüse/Obst ab, wenig Kräuter/Zimmerpflanzen; Detection moderat (mAP ~38,9). Abdeckung pro Art ehrlich kommunizieren.
- Ersetzt den in REQ-029 §3.2 vorgesehenen Plant.id-Health-Pfad als **kostenfreie, self-hosted Alternative**.

### 6.2 Aufgabe C — Zustand/Phänologie (REQ-003)

- **Kein fertiges freies Modell verfügbar** (Research: Abwesenheit von Evidenz, niedrige Konfidenz).
- **Ansatz:** überwachte Klassifikation auf projekteigenen Bildern entlang der REQ-003-Phasen (Keimung → Sämling → Vegetativ → Blüte → Ernte): leichter Klassifikatorkopf auf DINOv2-Embeddings.
- **Voraussetzung:** projekteigener, gelabelter Bilddatensatz (hier ist Eigenmaterial nötig — botanische DBs liefern keine Stadien-Labels). **Bis dahin reine Forschungsstufe.**

---

## 7. Lizenz- & Kosten-Risikomatrix

| Komponente | Lizenz | Kosten Endnutzer | Risiko | Maßnahme |
|---|---|---|---|---|
| DINOv2 Basis-Backbone | Apache-2.0 | 0 € | LICENSE vor Release re-verifizieren | §2.3 |
| PlantCLEF-Fine-tune-Gewichte | CC-BY-NC | — | nicht-kommerziell | **nicht verwenden** |
| ONNX Runtime | MIT | 0 € | — | — |
| GBIF CC0/CC-BY-Bilder (nur Embedding) | CC0/CC-BY | 0 € | Attribution (CC-BY) | Metadaten + ShareAlike meiden |
| PlantDoc-Datensatz | offen | 0 € | Arten-Abdeckung | ehrlich kommunizieren |
| Pl@ntNet API (Fallback) | ToS, ≤500/Tag | 0 € (im Limit) | kommerz. Nutzung kostenpflichtig; Query-Metadaten | nur Consent, nur Fallback |
| Plant.id (optional) | pro Request | **>0 €** | verletzt No-Cost | **Opt-in, kein Default** |
| Eigene Inferenz-Hardware (Betreiber) | — | Betriebskosten beim **Betreiber**, nicht Endnutzer | CPU genügt | ViT-S Baseline |

---

## 8. DSGVO-Konformität (REQ-025)

- **Self-hosted Inferenz = sicherste Variante:** Nutzerfotos verlassen die Instanz nicht; kein Drittland-Transfer, kein AVV nötig für den Primärpfad.
- **Bildverarbeitung:** Foto nur im RAM während Embedding-Berechnung; **keine persistente Speicherung** des Nutzerfotos (nur Embedding der Anfrage optional zur Historie, ohne Rückrechenbarkeit auf das Bild — zu bewerten).
- **EXIF-Stripping** vor jeder Verarbeitung (REQ-029 §5.4).
- **Fallback-Consent:** Nutzung des Pl@ntNet-Fallbacks erfordert separaten, expliziten Consent (`plant_identification`, REQ-029 §5) — Foto-Upload an Dritte ist opt-in und transparent; Query-Metadaten-Speicherung bei Pl@ntNet im Datenschutzhinweis nennen.
- **Referenzbild-Provenienz** (Quelle/Lizenz/Urheber) wird zu Nachweiszwecken gespeichert.

---

## 9. Abhängigkeiten

**Benötigt:**
- REQ-001 v5.0 (Species-Stammdaten als Matching-Ziel + Quelle der wissenschaftlichen Namen für Beschaffung)
- REQ-011 v1.0 (Adapter-Pattern / AdapterRegistry)
- REQ-025 (Consent für Fallback)
- REQ-029 v1.0 (Adapter-Interface, Registry, Consent, EXIF, Frontend-Dialog, Request-Collections — wiederverwendet)

**Optional (Synergie):**
- REQ-010 v1.0 (IPM-Mapping für Aufgabe B)
- REQ-003 (Phasen für Aufgabe C)
- REQ-020 (Onboarding-Integration), REQ-021 (Erfahrungsstufen), REQ-022 (CareProfile nach Erkennung)

**Systemabhängigkeiten (NEU):**
- Inferenz-Microservice (`src/inference-service/`): Python, FastAPI, ONNX Runtime, Pillow/numpy
- DINOv2-ONNX-Modellartefakt (Build-Schritt: Export aus PyTorch via optimum/torch.onnx)
- ArangoDB mit Vektor-Index **oder** In-App-Cosine-Fallback
- Celery (Beschaffungs-Pipeline + Inferenz-Offloading)
- Helm-Deployment für den Inference-Service

**Externe (optional):**
- GBIF Media-API (Beschaffung, kein Key nötig)
- Pl@ntNet API v2 (Fallback, freier Key)

---

## 10. Akzeptanzkriterien

### 10.1 Definition of Done — Phase 1 (Pl@ntNet-first, sofortige MVP-Auslieferung) — NEU v1.1

- [ ] **PlantNetAdapter** (REQ-029 §3.3) implementiert, in der `IdentificationAdapterRegistry` registriert und über `IDENTIFICATION_PRIMARY_ADAPTER="plantnet"` als **Prio 1** gesetzt
- [ ] **Pl@ntNet-API-Client:** Free-Tier (≤500/Tag), freier API-Key per Konfiguration; Rate-Limit-Handling + verständlicher Fehlerzustand bei Limit/Key-Fehlern
- [ ] **Consent als harte Voraussetzung:** ohne `plant_identification`-Consent (REQ-029 §5) keine Identifikation; Datenschutzhinweis nennt Pl@ntNet als Empfänger; **EXIF-Strip** vor jedem Versand
- [ ] **Frontend-Capture:** `PlantIdentificationDialog` mit (a) Webcam via `getUserMedia()`, (b) Smartphone-Rückkamera via `<input capture="environment">`, (c) Datei-Upload/Drag&Drop; Bildnormalisierung vor Versand
- [ ] **Kandidaten-Auswahl:** Top-k `IdentificationSuggestion` werden zur **expliziten Nutzerauswahl** angezeigt; `select_result(rank)` persistiert die Wahl; kein stilles Auto-Anlegen der Top-1
- [ ] **„Pflanze anlegen":** aus dem gewählten Vorschlag → PlantInstance/Species-Verknüpfung (Onboarding REQ-020 + jederzeit, REQ-029 §4.2)
- [ ] **identification_requests**-Collection (REQ-029 §2) schreibt Request + Ergebnisse + `selected_result_rank`; **kein** Nutzerfoto persistiert
- [ ] **Phase-2-Brücke intakt:** API-Vertrag, Response-Schema und `external_id` adapterneutral; Engine gegen `PlantIdentificationAdapter`-Interface; Umstieg auf Phase 2 = Adapter-Registrierung + Default-Priorität umschalten
- [ ] **Tests:** PlantNetAdapter (gemockte API, Mapping `IdentificationSuggestion`, Rate-Limit/Fehler), Consent-Gate, Capture-Komponente, Select-Result-Flow
- [ ] **i18n** (DE/EN) für Dialog, Kandidatenliste, Consent-Hinweis, Fehlerzustände

> Phase 1 enthält **keinen** Inferenz-Microservice, **keinen** ONNX-Build und **keine** Referenzbild-Beschaffung — diese sind ausschließlich Phase-2-Scope (§10.2).

### 10.2 Definition of Done — Phase 2 (DINOv2-Zielarchitektur, Aufgabe A):

- [ ] **Inference-Service:** `src/inference-service/` mit ONNX-DINOv2 (Apache-2.0), `/embed`, `/embed/batch`, `/healthz`, `/readyz`, `/modelinfo`
- [ ] **Preprocessing-Contract** zentral implementiert und index-/query-identisch verwendet
- [ ] **ONNX-Export** des DINOv2-Backbones reproduzierbar dokumentiert (Build-Skript)
- [ ] **species_embeddings**-Collection + Vektorsuche (oder In-App-Cosine-Fallback) implementiert
- [ ] **Beschaffungs-Pipeline:** GBIF-Abfrage, CC0/CC-BY-Filter, Kuratierung, Embedding-Indexierung, Provenienz-Protokoll
- [ ] **Abdeckungs-Report** je Art (brauchbare Referenzen, Lizenzverteilung); Arten < 5 Referenzen als „nicht erkennbar" markiert
- [ ] **LocalEmbeddingAdapter** in der REQ-029-Registry registriert, **Prio 1** vor Pl@ntNet
- [ ] **Fallback-Kette:** bei lokaler Konfidenz < Schwelle → Pl@ntNet (falls Consent + Key)
- [ ] **Nur Embeddings + Metadaten persistiert**, keine fremden Originalbilder
- [ ] **DSGVO:** Nutzerfoto nicht persistiert, EXIF-Strip, kein Drittland-Transfer im Primärpfad
- [ ] **Konfidenz-Kalibrierung** an eigenen Arten gemessen, Schwellen dokumentiert
- [ ] **Frontend:** nutzt bestehenden `PlantIdentificationDialog` (REQ-029 §4) unverändert über die Registry
- [ ] **Tests:** Inference-Service (Embedding-Determinismus), Adapter (gemockt), Vektorsuche, Beschaffungs-Filter (Lizenz)
- [ ] **Helm:** Inference-Service-Deployment, Skaffold-Integration

### Testszenarien:

**Szenario A1 — Erkennung Art im Index**
```
GIVEN: species_monstera_deliciosa hat 20 CC-BY-Referenz-Embeddings im Index
WHEN:  Nutzer lädt ein Monstera-Foto hoch
THEN:  Inference-Service liefert Embedding → Vektorsuche liefert Monstera deliciosa
       als Top-1 mit Konfidenz ≥ 0.85 → "Diese Pflanze anlegen" verfügbar
       UND das Nutzerfoto wird nicht persistiert (nur Request-Log ohne Bild)
```

**Szenario A2 — Art ohne ausreichende Referenzen**
```
GIVEN: species_alocasia_zebrina hat nur 2 Referenzbilder (< 5) → "nicht erkennbar"
WHEN:  Nutzer lädt ein Alocasia-zebrina-Foto hoch
THEN:  Art erscheint NICHT als sicherer Treffer; UI kommuniziert ehrlich
       UND Fallback (Pl@ntNet) wird angeboten, falls Consent erteilt
```

**Szenario A3 — Lizenz-Filter der Beschaffung**
```
GIVEN: GBIF liefert für eine Art 30 Bilder (10× CC0, 12× CC-BY, 8× CC-BY-NC)
WHEN:  Beschaffungs-Pipeline läuft
THEN:  nur 22 (CC0+CC-BY) werden eingebettet; 8 CC-BY-NC verworfen
       UND reference_image_jobs protokolliert die Lizenzverteilung
       UND kein Originalbild wird persistiert
```

**Szenario A4 — Fallback-Kette bei niedriger Konfidenz**
```
GIVEN: lokales Matching liefert Top-1-Konfidenz 0.40 (< AUTO_ACCEPT)
  AND: Pl@ntNet-Key konfiguriert, Consent erteilt
WHEN:  Nutzer identifiziert eine Pflanze
THEN:  lokale Vorschläge werden angezeigt UND Pl@ntNet als Zweitmeinung abgefragt
       (innerhalb 500/Tag-Limit), Ergebnisse zusammengeführt
```

**Szenario A5 — Self-hosted ohne jeden externen Key**
```
GIVEN: kein Pl@ntNet/Plant.id-Key gesetzt
WHEN:  Inference-Service läuft mit indexierten Referenzen
THEN:  Artbestimmung funktioniert vollständig lokal, kostenlos, ohne Internet
       UND es entsteht kein externer Request
```

**Szenario A6 — Preprocessing-Konsistenz**
```
GIVEN: dasselbe Bild wird über Beschaffungs-Pipeline und über /identify verarbeitet
WHEN:  beide Embeddings berechnet werden
THEN:  die Embeddings sind (bis auf Rundung) identisch (Determinismus-Test)
```

---

**Hinweise für RAG-Integration:**
- Keywords: Bilderkennung, Pflanzenidentifikation, DINOv2, Embedding, Vektorsuche, ONNX Runtime, self-hosted, Referenzbilder, GBIF, PlantDoc, Pl@ntNet, Few-Shot, Artbestimmung
- Fachbegriffe: Embedding-Matching, Nearest-Neighbor, Cosine-Distanz, Apache-2.0, CC-BY-NC, ShareAlike, Preprocessing-Contract, Konfidenz-Kalibrierung, Inferenz-Microservice
- Abgrenzung: korrigiert REQ-029 v1.0 (Plant.id primär, kostenpflichtig → disqualifiziert); definiert self-hosting-first-Architektur; wiederverwendet REQ-029-Adapter-/Consent-/Frontend-Bausteine
- Verknüpfung: nutzt REQ-001 (Species), REQ-011 (Adapter), REQ-025 (Consent); synergiert mit REQ-010 (IPM, Aufgabe B), REQ-003 (Phasen, Aufgabe C)
- Quelle der Architekturentscheidungen: spec/analysis/n-001-pflanzenerkennung-bilderkennung-research.md
```
