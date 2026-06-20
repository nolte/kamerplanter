# Implementierungs-Vorbereitung: Bildbasierte Schädlingserkennung (REQ-044) & Health-Vision (REQ-043)

**Stand:** Juni 2026 (Recherche-Cutoff)
**Zweck:** Klärt die offenen Punkte aus REQ-044 §10 und REQ-043 §10, damit eine spätere Implementierung mit konkreten, begründeten Technik-Entscheidungen starten kann. Dieses Dokument ist **Entscheidungs-Vorbereitung**, kein Spec-Ersatz — es speist Korrekturen/Konkretisierungen zurück in REQ-044 §10 und REQ-043 §10 (siehe §9).
**Methode:** Fokussierte Mehrquellen-Web-Recherche über vier Stränge (Datensätze/Few-Shot · CPU-ONNX-Detektoren/Tiling · Kindwise-DSGVO · Kalibrierung/Abstention/CPU-VLM), aufbauend auf den breiten Recherchen `pest-detection-research.md` und `plant-health-vision-research.md`. Unsichere/anwaltlich zu prüfende Punkte sind markiert.
**Rahmenbedingung (aus dem Repo, nicht neu erforscht):** REQ-029-A legt die Self-Hosted-Inferenz fest — eigener Microservice `src/inference-service/` (FastAPI + ONNX Runtime, **CPU Execution Provider Default**, CUDA optional), DINOv2 ViT-S/14 als CPU-MVP, **Celery-Offloading** (asynchrone Einzelfoto-Analyse, Multi-Sekunden-Latenz akzeptabel), GBIF-Beschaffungs-Pipeline, kalibrierte Konfidenz-Schwellenfunktion (§7). Schädlingserkennung baut auf genau dieser Infrastruktur auf.

---

## 1. Executive Summary der Klärung

1. **Architektur-Kernentscheidung: zwei getrennte Bilddomänen, ein gemeinsamer DINOv2-Backbone.** Die Forschung zerfällt sauber in (A) **on-leaf** (Nutzer fotografiert Schädling/Schadbild am Blatt) und (B) **Sticky-Trap/Gelbtafel** (frontale Makroaufnahme zum Zählen). Beide dürfen **nicht** dasselbe Modell teilen. Glücklicher Befund: Der **DINOv2-Backbone aus REQ-029-A** trägt beide Pfade — als Few-Shot-Embedding-Klassifikator (on-leaf) **und** als Backbone des empfohlenen Detektors (RF-DETR baut auf DINOv2 auf). Das macht Schädlingserkennung zu einer **Erweiterung des bestehenden Inferenz-Service**, nicht zu einem Neubau.

2. **Modellwahl korrigiert: YOLO ist lizenzrechtlich ausgeschlossen.** Ultralytics-YOLO (v8/v10/**v11**) steht unter **AGPL-3.0**; die Network-Use-Klausel (§13) zieht einen self-hosted HTTP-Inferenzdienst ins Copyleft. REQ-044 nannte „YOLO-/RT-DETR-tiny-Klasse" — **YOLO entfällt**. Empfehlung: **RF-DETR-Small (Apache-2.0)** als 1. Wahl (DINOv2-Backbone, beste belegte CPU-ONNX-Zahlen, stärkste Small-Object-Story), **D-FINE-S/N (Apache-2.0)** als compute-sparsame Alternative, **RT-DETRv2-S (Apache-2.0)** für maximale Code-Reife.

3. **on-leaf braucht primär keinen Detektor, sondern Few-Shot-Klassifikation.** Bei den realistisch verfügbaren <100 Bildern/Indoor-Art ist **frozen DINOv2 + Prototypical/kNN** der robusteste, self-hosting-freundlichste Weg: neue Art = neue Prototypen, **kein Retraining**. Ein echter Detektor (RF-DETR + SAHI-Tiling) lohnt nur dort, wo **lokalisiert/gezählt** werden muss — primär die Gelbtafel-Domäne.

4. **Datenlage ist ungleich: gut bei Weiße Fliege/Thripse, Lücke bei Trauermücken/Wollläusen.** Über eigene Datensätze (Roboflow/peer-reviewed) sind Weiße Fliege + Thripse gut, Spinnmilben brauchbar (oft nur als **Schadbild**, da <0,5 mm) abgedeckt; **Trauermücken = komplette Datenlücke, Wollläuse fast, Blattläuse-Indoor mittel**. Lücken werden über **iNaturalist/GBIF (CC0/CC-BY-gefiltert) + Human-in-the-Loop-Nutzerbilder** geschlossen — dieselbe GBIF-Pipeline wie REQ-029-A.

5. **Cloud-Produkt korrigiert: `plant.health`, nicht `crop.health`.** Für Indoor-Zierpflanzen ist Kindwise **`plant.health`** das richtige Produkt (548 Klassen, „*most annotations are for houseplants and ornamentals*"); `crop.health` deckt nur 23 essbare Feldkulturen ab. Der AVV (Art. 28 DSGVO) ist **öffentlich geklärt** (T&C Art. 20, automatisch mit Vertragsschluss). **Wundester Punkt:** 6-Monats-Bildspeicherung **mit vertraglicher Trainingsnutzung ohne dokumentiertes Opt-out**, Hosting auf Google Cloud + DigitalOcean (US-Konzerne) ohne EU-Residenz-Garantie. Vor Produktiveinsatz sind **9 konkrete Fragen** zu klären (§5.3).

6. **Abstention/Kalibrierung: `0,40` ist nur ein Tag-1-Platzhalter.** Prinzipientreu: **Temperature Scaling + Energy-OOD-Gate + klassenweise Schwelle, datengestützt über eine Risk-Coverage-Kurve auf Feld-Kalibrierungsdaten** zu einer Ziel-Precision (konservativ wegen Reliability-Gap). Plus **explizite `beneficial`- und `unknown`-Klasse** (~3 Accuracy-Punkte Kosten, klar gerechtfertigt). Conformal Prediction erst als Phase-2-Upgrade ab ~1000 Feld-Kalibrierungsbeispielen (mit SSBC + klassen-konditional).

7. **VLM-Erklärungs-Layer ist CPU-machbar — aber nur als „Sekunden-pro-Bild"-Feature.** Qwen2.5-VL-3B-Q4 / Moondream2 / SmolVLM2 laufen quantisiert auf x86-CPU mit Sekunden-Latenz → als **optionales, asynchrones Feature mit Graceful Degradation** spezifizieren. Interaktiv/Video braucht GPU. Der VLM bleibt **Erklärer, nie Erkenner**; RAG dämpft Halluzination, garantiert sie aber nicht.

---

## 2. Architektur-Kernentscheidung: zwei Domänen, ein Backbone

```
                         ┌───────────────────────────────────────────────┐
   on-leaf-Foto  ──────► │  Domäne B: Schädling/Schadbild am Blatt        │
   (Nutzerrealität)      │  → frozen DINOv2-Embedding (REQ-029-A Service) │──► Prototypical/kNN
                         │  → Klassifikation, KEIN Training pro neuer Art │     (pest|beneficial|symptom|unknown)
                         └───────────────────────────────────────────────┘
                         ┌───────────────────────────────────────────────┐
   Gelbtafel-Foto ─────► │  Domäne A: viele winzige Insekten zählen        │
   (opt., wenn Feature)  │  → RF-DETR-S (DINOv2-Backbone) + SAHI-Tiling   │──► Bounding-Boxen + Count
                         └───────────────────────────────────────────────┘
                                              gemeinsamer DINOv2-Backbone (Apache-2.0, REQ-029-A)
```

**Warum die Trennung verbindlich ist:** Ein Modell der Trap-Domäne (frontale, gleichmäßige Makroaufnahme) versagt in-the-wild am Blatt und umgekehrt. Die bestehende Datenlage spiegelt das (peer-reviewte Trap-Datensätze vs. dünnere on-leaf-Daten).

**Konsequenz für REQ-044:** Der `LocalPestDetectorAdapter` aus REQ-044 §3.2 wird präzisiert: Der **Default-on-leaf-Pfad ist ein Few-Shot-Embedding-Klassifikator** (kein Detektor), der **Detektor (RF-DETR + SAHI) ist der Gelbtafel-/Zähl-Pfad**. Das `PestDetectionResult`-Schema (mit `bounding_box: optional`, `mode: direct|symptom`) deckt beide bereits ab — die Box ist im on-leaf-Klassifikationspfad schlicht `null`.

---

## 3. Offener Punkt 1 — Indoor-Datenset & Few-Shot (REQ-044 §10)

### 3.1 Nutzbare Datensätze (Lizenz-Ampel)

🟢 klar nutzbar (CC0/CC-BY/Apache) · 🟡 mit Auflage / Bildherkunft prüfen · 🔴 nicht/unklar.

> **Lizenz-Falle Roboflow Universe:** Die pauschale `CC BY 4.0`-Angabe gilt für die Annotationen/das Re-Hosting, **nicht zwingend für die zugrunde liegenden Bilder**. Für ein ausgeliefertes Modell pro Datensatz die Bildherkunft prüfen → durchweg 🟡, wo unklar.

| Datensatz | Arten | ~Bilder | Domäne | Lizenz | Quelle |
|---|---|---|---|---|---|
| Yellow Sticky Traps (Nieuwenhuizen 2019) | Weiße Fliege | peer-reviewed | A | 🟢 (Original verifizieren) | Wageningen / Kaggle-Spiegel |
| Species-level thrips & whiteflies on YST (2025) | Thripse, Weiße Fliege (Art-Ebene) | balanciert | A | 🟢 peer-reviewed | PMC12669111 |
| Pest Detection Aphids/Thrips/Whitefly in Rose & Hibiscus | Blattläuse, Thripse, Weiße Fliege | ~1.117 | B (Zierpflanze!) | 🟡 | Roboflow `college-9tcuv` |
| Spider Mites | Spinnmilben | 1.414 | gemischt | 🟡 | Roboflow `ashok-kumar-k-s` |
| Red spider mite | Rote Spinnmilbe | 6.719 | gemischt | 🟡 | Roboflow `lance-eugene` |
| Tomato Two-Spotted Spider Mite | Spinnmilben-**Schadbild** | 200 | B | 🟡 | Roboflow `thesis-okplj` |
| Durian/Pineapple/Kusk Pests | Wollläuse (Nebenklasse) | wenige 100 | gemischt | 🟡 | Roboflow (diverse) |
| iNaturalist via GBIF | **alle 6** (inkl. Sciaridae) | viele, **unannotiert** | B | 🟡 pro Bild CC0/CC-BY/NC filtern | GBIF Dataset `50c9509d-…` |

### 3.2 Abdeckung pro Zielart

| Art | Lage | Bewertung |
|---|---|---|
| Weiße Fliege | dedizierte, art-aufgelöste, peer-reviewte Sets | 🟢 gut (Trap + on-leaf) |
| Thripse | YST-Sets auf Art-Ebene | 🟢 gut (Trap; on-leaf schwer, da winzig) |
| Spinnmilben | mehrere Sets, oft **Schadbild statt Tier** (<0,5 mm) | 🟢/🟡 brauchbar — Schadbild-Fallback einplanen |
| Blattläuse | Multi-Pest-Set + Feldkultur-dominiert | 🟡 mittel (Indoor unterrepräsentiert) |
| Wollläuse | nur Nebenklassen, wenige 100 | 🟡/🔴 dünn — Watte-Optik aber distinktiv → Eigenbau gut |
| **Trauermücken (Sciaridae)** | **kein** dediziertes Detektionsdataset | 🔴 **echte Lücke** — nur iNaturalist + HITL |

### 3.3 Few-Shot-Strategie (Empfehlung)

- **Stufe 1 (Default, on-leaf):** frozen DINOv2-ViT → Embedding → **Prototypical/kNN**. Brauchbar ab **~10–30 Bildern/Klasse**; inkrementell ohne Retraining. Optional LoRA/BitFit (<1 % Params) als Steigerung. **Nutzt direkt den REQ-029-A-Embedding-Service.**
- **Stufe 2 (Gelbtafel/Zählen):** RF-DETR-S + SAHI, warmgestartet von einem YST-Datensatz; IP102/AgriPest nur als **Backbone-Prior**, nie als Zielklassen.
- **Augmentation obligatorisch** (Zoom/Shear/Rotation/Flip, ggf. CutMix/MixUp): bei ~10 Seed-Bildern bis +25 % Accuracy.
- **Cold-Start** pro Lücken-Art über CC0/CC-BY-gefilterte iNaturalist/GBIF-Beobachtungen, dann HITL-Wachstum.

### 3.4 HITL-Datensatz-Aufbau

- Schwellen: **~30 Bilder/Klasse** → Proto-Klassifikator live; **150+** → eigener Detektor sinnvoll.
- Active-Learning-Loop: Modell prä-annotiert Nutzerbilder, Mensch korrigiert nur; Unsicherheits-Sampling priorisiert.
- Datenschutz: Opt-in-Bildbeitrag (Consent, REQ-025), serverseitig auf Schädlingsausschnitt zuschneiden, EXIF/Geo strippen **vor** Aufnahme ins Trainingsset.

---

## 4. Offener Punkt 2 — Modell / ONNX / Tiling / Quantisierung (REQ-044 §10)

### 4.1 Modellwahl (Lizenz ist der entscheidende Filter)

| Modell | Lizenz | Ampel | Begründung |
|---|---|---|---|
| Ultralytics YOLO v8/v10/**v11** | AGPL-3.0 | 🔴 | §13 Network-Use zieht HTTP-Inferenzdienst ins Copyleft |
| YOLOv9 | GPL-3.0 | 🟠 | Copyleft bei Container-Auslieferung |
| **RF-DETR-S** (Roboflow) | Apache-2.0 | 🟢 | **1. Wahl** — DINOv2-Backbone, ~180 ms@320px ONNX-CPU belegt, COCO mAP-small 53,0, bestes ONNX-Tooling |
| **D-FINE-S/N** (Peterande) | Apache-2.0 | 🟢 | compute-sparsame Alternative (N=4 M, S=10 M Params), niedrigste CPU-Latenz/Tile |
| **RT-DETRv2-S** (lyuwenyu) | Apache-2.0 | 🟢 | reifste Codebasis, ~67 ms@320px / ~286 ms@960px gemessen |
| LW-DETR | Apache-2.0 | 🟢 | permissive Reserve-Option |

> ⚠️ **Anwaltliche Prüfung vor Produktentscheidung** (AGPL-§13-Reichweite, Code- vs. Weights-Lizenz). RF-DETR-**XL/2XL** = PML-1.0 non-commercial → **meiden**, nur Nano–Large nutzen.

**Empfehlung:** **RF-DETR-Small** als Detektor (Gelbtafel-Pfad), DINOv2-Embedding als on-leaf-Klassifikator — beide teilen den DINOv2-Backbone.

### 4.2 Tiling (Pflicht-Baustein, REQ-044 §4.3)

- **SAHI** (obss/sahi), reifer Standard. Startparameter: `slice 512px` (oder 640 = Detektor-Eingabe matchen), `overlap 0.2`, `postprocess GREEDYNMM`, `match_metric IOS`, `match_threshold 0.5`.
- **ONNX-Realität:** SAHI hat keine turnkey generische ONNX-Klasse → **eigenen `DetectionModel`-Wrapper** für den ONNX-Detektor einplanen (Aufwand). Alternativ RF-DETRs nativen (PyTorch-)SAHI-Pfad nutzen.
- **Latenz-Kosten:** 1 Inferenz/Tile → Wall-Clock ≈ N× Vollbild (2×2≈4, 3×3≈9). Gewinn: +5–7 % AP (Inferenz), bis +12–14 % mit slicing-aided Fine-Tuning — konzentriert auf kleine Objekte (unser Profil).

### 4.3 Quantisierung

- **INT8 static (QDQ, S8S8, per-channel, ~100 Kalibrierbilder)** ist nur für **CNNs** überzeugend (~2–4× Speedup, ≤1 % mAP-Verlust) — **VNNI/AVX-512-abhängig** (ohne VNNI kann INT8 *langsamer* sein).
- **DETR-Vorbehalt:** Attention quantisiert schlecht → bei RF-DETR/D-FINE INT8 zurückhaltend, eher FP32 lassen und über Tiling-Parameter/Threads optimieren. **Im Multi-Sekunden-Budget ist INT8 optional, nicht Pflicht.**
- Tooling: `onnxruntime.quantization` → Olive (HW-Tuning) → Intel Neural Compressor (accuracy-aware).

### 4.4 Realistische Latenz

| Komponente | Erwartung |
|---|---|
| RF-DETR-S Vollbild ONNX-CPU | ~180–300 ms @320–512px |
| RT-DETRv2-S | ~67 ms@320 / ~286 ms@960 |
| **mit SAHI (N Tiles)** | **× N → typ. 1–5 s/Foto** |

→ **1–5 s/Foto** auf moderner CPU — genau im akzeptierten asynchronen Multi-Sekunden-Fenster (Celery).

---

## 5. Offener Punkt 3 — Kindwise AVV / EU-Hosting / Indoor-Eignung (REQ-044 §10, REQ-043 §10)

### 5.1 Geklärte Fakten

- **Vertragspartner:** FlowerChecker s.r.o., Brno/CZ (EU-Gesellschaft).
- **AVV (Art. 28 DSGVO):** **öffentlich geklärt** — Teil der T&C Art. 20, entsteht automatisch mit Vertragsschluss (kein separates Dokument), korrekte Controller(ihr)/Processor(Kindwise)-Rollen, Art.-32-TOMs, Betroffenenrechte-Unterstützung. Stand 01.07.2024 (Art. 28.3 + DSA Art. 14).
- **Produkt-Korrektur:** **`plant.health`** (548 Klassen, „houseplants and ornamentals") ist das richtige Indoor-Produkt; **`crop.health`** = nur 23 essbare Feldkulturen (das „93→66 %"-Argument betraf crop.health). `insect.id` deckt Milben (Acari) ab.
- **Hosting:** Google Cloud Storage (Bilder) + DigitalOcean (DB), „Central Europe" — **keine vertragliche EU-Residenz-Garantie**, US-Mutterkonzerne → CLOUD-Act/FISA-Restrisiko.
- **Retention:** 6 Monate, **Bilder werden vertraglich zur Trainingsverbesserung genutzt — kein dokumentiertes Opt-out** (§20.4); kreditfreier Lösch-Endpunkt vorhanden; „Anonymisierung" = v.a. Gesichts-Blurring.

### 5.2 Bewertung für self-hosted-first

Kindwise bleibt als **opt-in-Cloud-Adapter** sinnvoll (breite gepflegte Abdeckung, EU-Vertragspartner, sauberer AVV), aber die **Trainingsnutzung ohne Opt-out + fehlende EU-Residenz-Garantie** sind für eine datenschutz-souveräne App gewichtige Gründe, den Self-Hosted-Pfad als Default beizubehalten. Cloud nur mit granularem Consent + transparentem Datenschutzhinweis.

### 5.3 Fragen an Kindwise VOR Vertragsschluss (Aktions-Item)

1. Vollständige **Sub-Prozessoren-Liste** inkl. Region + Vorab-Widerspruchsrecht (Art. 28 Abs. 2)?
2. Vertragliche **EU-Datenresidenz-Zusicherung** für GCS + DigitalOcean (konkrete Region)?
3. **Drittland-Garantien** gegen US-Zugriff (SCCs, TIA/DTIA, DPF-Zertifizierung der Sub-Prozessoren)?
4. **Trainings-Opt-out / No-Training-Modus** per API-Flag (der entscheidende Hebel)?
5. **Sofort-Löschung** statt 6 Monate (delete-on-response, auch auf Backups/Trainingssets)?
6. Was umfasst **„Anonymisierung"** außer Gesichts-Blurring (Geo/IP/EXIF)? DSGVO-tauglich?
7. **plant.health-Klassenliste** mit namentlicher Bestätigung der 5 Zielschädlinge + Real-World-Genauigkeit?
8. Bestätigung **plant.health statt crop.health** + dessen Pricing/Genauigkeit.
9. Verwertbares **Audit-Zertifikat/TOM-Dokument** (Art. 32) für die DSFA (der „external audit" ist ein Masaryk-Uni-Pentest, kein ISO/SOC-2).

### 5.4 Alternative

**Plantix/PEAT (Berlin, DE-Sitz)** = klareres DSGVO-Heimatrecht, aber schwächere Indoor-Eignung (feldkultur-fokussiert) und intransparente Hosting-/Retention-Angaben (Firebase/Microsoft → US-Sub-Prozessoren möglich). **Flora Incognita** = nur Artbestimmung, keine Schädlingsdiagnose. **Es gibt keinen EU-Anbieter, der DSGVO-Klarheit UND Indoor-Saugschädling-Fokus kombiniert** → Self-Hosted bleibt strategisch richtig.

---

## 6. Offener Punkt 4 — Kalibrierung, Abstention & Nützling-Differenzierung (REQ-044 §10, REQ-043 §10)

### 6.1 Gestufte Empfehlung (alles CPU/ONNX-tauglich)

1. **Basis:** Modell aus DINOv2-Backbone finetunen mit **Entropy-Regularisation + Label-Smoothing** (senkt ECE ~50 % roh) → **Temperature Scaling** (ein Skalar auf Logits, Fit auf Kalibrierungs-Split) → **Energy-Score** als zusätzliches OOD-Gate. Alle drei Single-Forward-Pass, trivial ONNX-exportierbar.
   - ⚠️ Label-Smoothing kann Selective-Ranking verschlechtern → gegen die Risk-Coverage-Kurve gegenprüfen.
2. **Abstention-Schwelle:** **nicht** roh `0,40`, sondern auf **kalibrierten** Scores über eine **Risk-Coverage-Kurve auf Feld-Kalibrierungsdaten** zu einer **Ziel-Precision** (konservativ wegen Lab→Field-Gap). **Per-Klassen-Schwellen** statt global. `0,40` nur als dokumentierter Tag-1-Default, der nach erstem Feld-Datensatz ersetzt wird (empirische Operating-Points liegen eher ~0,72).
3. **Klassen-Architektur:** explizite **`beneficial`-Klasse** (Marienkäfer-/Schwebfliegenlarve, Raubmilbe) und **`unknown/other`-Klasse** + Detektor-Hintergrund-Negativklasse. Kosten ~3 Accuracy-Punkte, klar gerechtfertigt (Closed-Set zwingt Unbekanntes sonst in bekannte Klassen). Selbst im Labor werden ~3,6 % der Nützlinge fehlklassifiziert → Abstention ist der Schutz.
4. **Conformal Prediction nur Phase 2** — ab **~1000 Feld-Kalibrierungsbeispielen**, mit **SSBC-Korrektur** (training-conditional) und **klassen-konditionalen** Schwellen. Bei kleinem n trügerische Garantie (n=100, α=0,1 → ~45 % der Kalibrierungen unter Soll-Coverage), und Exchangeability bricht unter Shift.

### 6.2 Differenzierung Schädling↔Krankheit↔Mangel

- **Nährstoffmangel** ist visuell ~6 Punkte schwerer als Krankheit; eine publizierte Mangel↔Krankheit-Confusion-Matrix **fehlt** (Evidenzlücke).
- **Multi-Signal-Fusion** (Bild + Sensor + IPM + Pflege) ist physiologisch plausibel und der richtige Hebel (REQ-043), aber **quantifizierte** Fusion-Gewinne fehlen in der Literatur → **nicht überversprechen**, als Evidenzlücke markieren.

---

## 7. Offener Punkt 5 — VLM-Erklärungs-Layer auf CPU (REQ-044 §10, REQ-043 §10)

- **Machbar als „Sekunden-pro-Bild"-Feature**, nicht interaktiv. Empfohlen: **Qwen2.5-VL-3B Q4_K_M** (llama.cpp/libmtmd, ~2 GB + mmproj) als bester Qualität/Größe-Kompromiss; **Moondream2 4-bit** (~1,2 GB) oder **SmolVLM2-500M** (minimaler Footprint) als Alternativen. Florence-2 ist eher Detektion/Caption als Freitext-Differenzierung.
- ⚠️ Fast alle „schnellen CPU"-Zahlen sind real Apple-Silicon/GPU/NPU; saubere x86-CPU-VLM-Benchmarks sind rar; **mmproj-RAM ist additiv und unterberichtet** → vor Deployment auf x86-Zielhardware messen.
- **Spec-Konsequenz:** VLM-Erklärung als **opt-in/asynchrones Feature mit Graceful Degradation** (regel-/template-basierte Erklärung, wenn keine GPU/zu wenig CPU-Budget). VLM = **Erklärer, nie Erkenner**.
- **RAG-Kopplung:** retrievte Wissensbasis-Chunks (Steckbriefe, IPM-Daten) in den Prompt injizieren; Bounding-Box → Crop → fokussiertes Retrieval verbessert Alignment. **Aber:** RAG-Grounding ist notwendig, nicht hinreichend (kein Wahrheits-Zwang) → VLM **nur über den bereits klassifizierten, kalibrierten Befund** erklären lassen, Ausgabe als „advisory" kennzeichnen.

---

## 8. Offener Punkt 6/7 — Stammdaten & geplante Scans

- **`beneficials`/`deficiencies`-Collection (REQ-010-Lücke):** Die Klassen-Architektur (§6.1) braucht eine `beneficial`-Kategorie. Empfehlung: in REQ-010 eine **`beneficials`-Stammdaten-Collection** (Nützlinge: Marienkäfer, Florfliege, Raubmilbe, Schlupfwespe …) ergänzen, analog `pests`. Bis dahin bleibt `category=beneficial` ohne `matched_*_key` (Slug-basiert). Gleiches Muster für `deficiencies` (REQ-038/043-Lücke).
- **Proaktive geplante Scans:** Mit der asynchronen Celery-Inferenz (Multi-Sekunden, REQ-029-A) sind periodische Scans (`trigger=scheduled`) technisch tragbar. Empfehlung: **nicht** automatisch fotografieren, sondern bei vorhandenen Nutzerfotos/Galerie (REQ-034) re-evaluieren; Scheduling als Celery-Beat-Task analog REQ-022. Detail-Spec ist v2-Thema.

---

## 9. Rückwirkungen auf die Specs (umzusetzen)

### REQ-044 §10 — zu aktualisieren

| Bisheriger offener Punkt | Geklärt → |
|---|---|
| Indoor-Datenset | iNaturalist/GBIF-Cold-Start + HITL; Few-Shot DINOv2-Proto (~30 Bilder/Klasse); Trauermücken/Wollläuse = Lücke (§3) |
| Quantisierte ONNX-Variante | **RF-DETR-S (Apache-2.0)**, **YOLO entfällt (AGPL)**; SAHI 512/0.2; INT8 nur CNN/optional (§4) |
| Kindwise-Vertragslage | AVV öffentlich geklärt; **plant.health statt crop.health**; 9 Fragen vor Vertrag (§5) |
| Abstention-Schwelle 0,40 | nur Tag-1-Default; TS+Energy+Risk-Coverage, klassenweise (§6) |
| beneficials-Stammdaten | `beneficials`-Collection in REQ-010 ergänzen (§8) |
| RAG-(V)LM-Stufe | CPU-machbar als opt-in/async, Graceful Degradation (§7) |
| Architektur-Präzisierung (neu) | **zwei Domänen**: on-leaf = Few-Shot-Klassifikation (kein Detektor), Gelbtafel = RF-DETR+SAHI (§2) |

### REQ-043 §10 — zu aktualisieren

| Bisheriger offener Punkt | Geklärt → |
|---|---|
| Gewichtungs-Kalibrierung | Multi-Signal-Fusion-Gewinn nicht quantifiziert belegt → Gewichte als begründete Startannahme, datengestützt nachkalibrieren; nicht überversprechen (§6.2) |
| Kindwise-Benchmark | plant.health statt crop.health; eigener Stichproben-Test gegen Zieldomänen vor Produktivnahme (§5) |
| RAG-(V)LM-Erklärungsstufe | CPU-machbar (Qwen2.5-VL-3B-Q4 etc.), opt-in/async, Graceful Degradation (§7) |
| deficiencies-Stammdaten | `deficiencies`- + `beneficials`-Collection in REQ-010 ergänzen (§8) |
| Konfidenz/Abstention (quer) | TS+Energy+Risk-Coverage + beneficial/unknown-Klasse; Conformal Phase 2 (§6) |

---

## 10. Aktions-Items vor Implementierungsbeginn

**Recherchierbar abgeschlossen — verbleibend extern/empirisch:**

1. **[extern]** Kindwise die 9 Fragen aus §5.3 stellen (v.a. Trainings-Opt-out + EU-Residenz) und plant.health-Klassenliste anfordern. Parallel Plantix/PEAT als DE-Alternative anfragen.
2. **[rechtlich]** AGPL-§13-Reichweite + Code-vs-Weights-Lizenz von RF-DETR/D-FINE anwaltlich bestätigen lassen.
3. **[empirisch]** RF-DETR-S vs. D-FINE-S/N vs. RT-DETRv2-S auf der **konkreten Ziel-CPU** benchmarken (Latenz/mAP mit/ohne INT8, mit SAHI-Tiling) — VNNI-Verfügbarkeit prüfen.
4. **[Daten]** Cold-Start-Datensätze pro Art zusammenstellen (CC0/CC-BY-Gate), iNaturalist/GBIF-Export für Trauermücken/Wollläuse; HITL-Labeling-Loop aufsetzen (Ziel 30/Klasse → live, 150+ → Detektor).
5. **[Kalibrierung]** Feld-Kalibrierungs-Split anlegen, Risk-Coverage-Kurve ziehen, klassenweise Schwellen + Energy-OOD-Gate setzen (0,40 ersetzen).
6. **[Hardware]** x86-CPU-VLM-Latenz (Qwen2.5-VL-3B-Q4) auf Zielhardware messen → entscheiden, ob VLM-Erklärung default-an oder GPU-gated.

---

## 11. Quellen (Auswahl, mit URLs)

**Datensätze & Few-Shot:** Roboflow [Spider Mites](https://universe.roboflow.com/ashok-kumar-k-s/spider-mites-cqt0q) · [Red spider mite](https://universe.roboflow.com/lance-eugene/red-spider-mite) · [Rose/Hibiscus Pests](https://universe.roboflow.com/college-9tcuv/pest-detection-aphids-thrips-and-white-fly-in-rose-and-hibiscus-plants) · [Thrips/Whitefly YST (PMC12669111)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12669111/) · [Sticky-trap transfer+SAHI (PMC11624506)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11624506/) · [iNaturalist/GBIF](https://www.gbif.org/dataset/50c9509d-22c7-4a22-a47d-8c48425ef4a7) · [DINOv2](https://arxiv.org/html/2304.07193v2) · [AnomalyDINO](https://www.researchgate.net/publication/390594957_AnomalyDINO_Boosting_Patch-based_Few-Shot_Anomaly_Detection_with_DINOv2) · [Augmentation few-shot (arXiv 2208.12613)](https://arxiv.org/pdf/2208.12613) · [Semi-supervised AL (MDPI)](https://www.mdpi.com/2079-9292/12/2/375)

**CPU-Detektoren & Tiling:** [RF-DETR](https://github.com/roboflow/rf-detr) · [RF-DETR CPU #641](https://github.com/roboflow/rf-detr/issues/641) · [D-FINE](https://github.com/Peterande/D-FINE) · [RT-DETR](https://github.com/lyuwenyu/RT-DETR) · [LW-DETR](https://github.com/Atten4Vis/LW-DETR) · [Ultralytics License (AGPL)](https://www.ultralytics.com/license) · [SAHI](https://github.com/obss/sahi) · [ONNX Runtime Quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)

**Kindwise/DSGVO:** [kindwise FAQ](https://www.kindwise.com/faq) · [plant.health](https://www.kindwise.com/plant-health) · [crop.health](https://www.kindwise.com/crop-health) · [insect.id](https://www.kindwise.com/insect-id) · [T&C-Update Blog](https://www.kindwise.com/post/updated-t-c-and-sla-revamp-faster-responses-guaranteed) · [Plantix Privacy](https://plantix.net/en/imprint/privacy-policy/)

**Kalibrierung/Abstention/VLM:** [Guo et al. Calibration](https://arxiv.org/pdf/1706.04599) · [Energy-OOD](https://proceedings.neurips.cc/paper/2020/file/f5496252609c43eb8a3d147ab9b9c006-Paper.pdf) · [Conformal intro](https://arxiv.org/abs/2107.07511) · [RAPS](https://arxiv.org/abs/2009.14193) · [Post-hoc under shift](https://arxiv.org/html/2507.07780) · [Open-set fruit fly](https://www.sciencedirect.com/science/article/pii/S1476927123001937) · [Lab→Field ViT (PMC12213485)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12213485/) · [Qwen2.5-VL-3B GGUF](https://huggingface.co/Mungert/Qwen2.5-VL-3B-Instruct-GGUF) · [Moondream2 QAT](https://moondream.ai/blog/smaller-faster-moondream-with-qat) · [SmolVLM (arXiv 2504.05299)](https://arxiv.org/pdf/2504.05299)

---

### Vorbehalte

- Roboflow-Bildlizenzen auf Einzelbildebene nicht verifizierbar (HTTP 403); Bildzahlen aus Snippets — pro Datensatz vor Produktivnutzung bestätigen.
- CPU-Latenzen für D-FINE/LW-DETR nicht offiziell benchmarkt; alle Lizenz-Auslegungen (AGPL-§13, Weights vs. Code) bedürfen anwaltlicher Bestätigung.
- Kindwise-„Central Europe"-Region unbestätigt; plant.health-Indoor-Trefferquote ohne Klassenliste unbelegt.
- Mangel↔Krankheit-Confusion-Matrix und quantifizierte Multi-Signal-Fusion-Gewinne als Evidenzlücken markiert; x86-CPU-VLM-Latenz selbst zu messen.
