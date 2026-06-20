# Implementierungs-Readiness: Bildbasierte Schädlingserkennung (REQ-044)

**Stand:** Juni 2026
**Zweck:** Schließt die **Klärungsphase** für REQ-044 ab. Übersetzt die in `pest-detection-implementation-prep.md` benannten externen/empirischen Aktions-Items in **ausführungsreife Arbeitspakete (WP)** mit fertigen Artefakten (Lizenz-Entscheidung, Benchmark-Protokoll, Daten-Beschaffung mit verifizierten GBIF-Keys, Kalibrierungs-Protokoll, Kindwise-Anfragetext, Stammdaten-Vorschlag). Nach diesem Dokument kann eine Implementierung **direkt starten**.
**Abgrenzung (verbindlich):** Dies ist **reine Vorbereitung** — **keine Implementierung**, **keine Änderung an `src/`**. Damit beeinträchtigt es **keine parallel laufende Implementierung** (z. B. REQ-034). Alle Code-/Schema-Artefakte hier sind **Vorschläge/Protokolle**, die erst im späteren Implementierungs-Sprint umgesetzt werden.
**Grundlage:** Verfeinert `pest-detection-implementation-prep.md` (#248) mit zwei live-verifizierten Detail-Recherchen (Modell-Lizenzen Code+Weights; finale Taxonomie + GBIF-Beschaffung).

---

## 0. Reihenfolge & Abhängigkeiten der Arbeitspakete

```
WP-7 Kindwise-Anfrage ──(extern, parallel, blockiert nichts)──► Entscheidung Cloud-Adapter ja/nein
WP-1 Lizenz-Entscheidung ──► WP-2 Benchmark ──► finale Modellwahl ──┐
WP-4 Klassen-Taxonomie ──► WP-3 Daten-Beschaffung ──► Cold-Start-Index ─┤──► IMPLEMENTIERUNG
WP-8 Stammdaten (beneficials/deficiencies, REQ-010) ──────────────────┤      (späterer Sprint)
WP-5 Kalibrierungs-Protokoll  ─(nach erstem Feld-Datensatz)───────────┤
WP-6 CPU-VLM-Eval ──(optional, GPU-gated)────────────────────────────┘
```

**Kritischer Pfad:** WP-1 (Lizenz/Anwalt) + WP-4→WP-3 (Daten) sind die zwei Stränge, die vor Implementierungsbeginn abgeschlossen sein müssen. WP-7 (Kindwise) läuft extern parallel und blockiert den Self-Hosted-Pfad nicht. WP-5/WP-6 sind nachgelagert (brauchen erste Daten/Modelle).

---

## WP-1 — Modell-Lizenz-Entscheidung (Code **und** Weights verifiziert)

### 1.1 Lizenz-Matrix

| Modell | Code-Lizenz | **Weights-Lizenz** | Backbone | OSS-self-hosted nutzbar | Quelle |
|---|---|---|---|---|---|
| **D-FINE-S/N** | Apache-2.0 | **Apache-2.0** (eine Repo-LICENSE, keine separate Weights-Klausel) | ResNet/HGNetV2 (CNN) | **✅ ja — am saubersten** | [LICENSE](https://github.com/Peterande/D-FINE/blob/master/LICENSE) |
| **RT-DETRv2-S** | Apache-2.0 | **Apache-2.0** (eine Repo-LICENSE) | ResNet (CNN) | **✅ ja** | [LICENSE](https://github.com/lyuwenyu/RT-DETR/blob/main/LICENSE) |
| **RF-DETR** N/S/M/L | Apache-2.0 | **Apache-2.0** (HF-Tag) | DINOv2-Style ViT (Apache, post-08/2023) | ✅ ja, **mit Guard** | [LICENSE](https://github.com/roboflow/rf-detr/blob/develop/LICENSE) |
| **RF-DETR XL/2XL** | PML-1.0 | **PML-1.0** (plattformgebunden, Telemetriepflicht) | dito | **❌ nein** (proprietär) | [PML-1.0](https://roboflow.com/platform-model-license-1-0) |
| Ultralytics YOLO v8/v10/v11 | AGPL-3.0 | AGPL-3.0 | — | **❌ nein** (§13 Network-Use) | [Ultralytics License](https://www.ultralytics.com/license) |

### 1.2 Entscheidung

- **Default-Kandidat (lizenzrechtlich sicherste Wahl): D-FINE-S** (alternativ -N). Begründung: **eine** Apache-2.0-Lizenz für Code **und** Weights (keine Bifurkation), **CNN-Backbone** → die gesamte DINOv2/v3-Backbone-Lizenzfrage entfällt; keine Plattform-/Telemetrie-Kopplung.
- **Technischer Vergleichskandidat: RF-DETR-S** (stärkere Small-Object-Story, DINOv2-Backbone passt zu REQ-029-A) — **nutzbar nur N/S/M/L**, mit **harter Build-Guard gegen XL/2XL** (Download-Allowlist) und DINOv2-(nicht-v3-)Provenienz-Check.
- **Finale Wahl erst nach WP-2-Benchmark + Anwalts-OK.** Beide bleiben für den Benchmark gesetzt.

### 1.3 Was die anwaltliche Prüfung noch bestätigen muss (nur echte Restrisiken)

1. **Weights ⊆ Apache:** Die extern (Release/Drive/HF) distribuierten **D-FINE/RT-DETR-Checkpoints** fallen unter die Repo-Apache-2.0 (Apache §1 „Work") — da keine separate Weights-Klausel existiert. (Risiko niedrig.)
2. **Objects365-Pretraining (wichtigster Restpunkt):** O365-Annotationen sind CC-BY-4.0, die **Bilder** unterliegen Flickr-ToU/Weiterverteilungsverbot. **Zu klären:** ob auf O365 vortrainierte **Gewichte** eine nachgelagerte Nutzungsbeschränkung erben. **Mitigation: COCO-only-Checkpoints ohne O365-Pretraining wählen** (entschärft den Punkt präventiv).
3. **RF-DETR DINOv2-Provenienz** (nur falls RF-DETR gewählt): bestätigen, dass die Apache-Checkpoints **DINOv2** (Apache, post-08/2023) und **nicht DINOv3** (restriktive Meta-Lizenz) inkorporieren.
4. **AGPL-§13-„combined work"** (nur zur Absicherung des YOLO-Ausschlusses): Einordnung, ob ein über HTTP getrennter Inferenz-Microservice „aggregate" oder „combined work" wäre. Für die empfohlenen Apache-Modelle **irrelevant**.

> **Aktions-Item (extern):** Punkte 1–4 als Lizenz-Memo an die Rechtsprüfung geben. Empfehlung: präventiv **COCO-only-Checkpoints** verwenden, dann reduziert sich die Prüfung faktisch auf Punkt 1 (niedriges Risiko).

---

## WP-2 — Modell-Benchmark-Protokoll (ausführungsreif)

Ziel: empirische Modell-/Parameterwahl auf der **konkreten Ziel-CPU** (Standard-K8s-Knoten, REQ-029-A), asynchroner Einzelfoto-Flow.

### 2.1 Kandidaten & Setup

- **Modelle:** D-FINE-S, D-FINE-N, RF-DETR-S (jeweils **COCO-only-Checkpoint**), optional RT-DETRv2-S.
- **Export:** PyTorch → ONNX (opset ≥ 17) → ONNX Runtime `CPUExecutionProvider`. Threads = Knoten-vCPUs.
- **Tiling:** SAHI, Parameter aus WP-3.2 (`slice 512`, `overlap 0.2`, `GREEDYNMM`, `IOS`).
- **Quantisierung:** zwei Läufe — FP32 und INT8-static (QDQ, S8S8, per-channel). **Erwartung:** INT8 nur bei VNNI/AVX-512 schneller; bei DETR Attention-Genauigkeitsverlust → INT8 nur übernehmen, wenn mAP-Verlust ≤ 1 PP.

### 2.2 Metriken & Akzeptanzkriterien

| Metrik | Messung | Akzeptanz (Start) |
|---|---|---|
| mAP@0.5 (eigene Val) | auf einem kleinen, gelabelten Indoor-Val-Set (WP-3) | dokumentieren; realistisch ~0,5–0,7 in-the-wild |
| Latenz/Foto (Vollbild) | ONNX-CPU, Median über 50 Bilder | < 1 s |
| Latenz/Foto (mit SAHI N Tiles) | ditto | **< 5 s** (Celery-Budget) |
| VNNI vorhanden? | `lscpu \| grep avx512_vnni` | dokumentieren (entscheidet INT8) |
| Small-Object-Recall | Recall für Objekte < 1 % Bildfläche | so hoch wie möglich; Hauptkriterium |

**Entscheidungsregel:** Wähle das Modell mit bestem **Small-Object-Recall** im **< 5 s**-Budget; bei Gleichstand das lizenzrechtlich sicherere (D-FINE).

### 2.3 SAHI-ONNX-Wrapper (Implementierungs-Hinweis)

SAHI hat keine turnkey generische ONNX-Klasse → eigene `DetectionModel`-Subklasse (load + predict + Result-Conversion) einplanen. Alternativ RF-DETRs nativen PyTorch-SAHI-Pfad für den Benchmark, ONNX-Wrapper erst für Produktion.

---

## WP-3 — Daten-Beschaffungsplan (verifizierte GBIF-Keys)

### 3.1 Kritische Lizenz-Mechanik (zwingend beachten)

GBIF führt **zwei getrennte Lizenz-Ebenen**: die **Occurrence-Lizenz** (`license`-Feld/-Filter) ≠ die **Bild-Lizenz** (pro Media-Eintrag im `multimedia`-Block). Bei iNaturalist sind Beobachtung (oft CC0/CC-BY) und Foto (oft **CC-BY-NC**) **unterschiedlich** lizenziert. **Der `license`-Filter filtert NUR die Occurrence-Lizenz.** → Pflicht-Pipelineschritt: nach dem Download pro Bild die **Media-Lizenz** prüfen und nur CC0/CC-BY-Bilder behalten.

### 3.2 GBIF-Download-Predicate (fertig)

POST `https://api.gbif.org/v1/occurrence/download/request` (Basic-Auth), Format **DWCA** (enthält `multimedia.txt` mit Bild-URLs + Bild-Lizenzen):

```json
{
  "creator": "<gbif-user>",
  "notificationAddresses": ["<mail>"],
  "format": "DWCA",
  "predicate": { "type": "and", "predicates": [
    { "type": "in", "key": "TAXON_KEY", "values": [
        "2130185","8351995","1420846","3525","3042","4534","2012132","2012126" ] },
    { "type": "equals", "key": "MEDIA_TYPE", "value": "StillImage" },
    { "type": "in", "key": "LICENSE", "values": ["CC0_1_0","CC_BY_4_0"] },
    { "type": "equals", "key": "DATASET_KEY",
      "value": "50c9509d-22c7-4a22-a47d-8c48425ef4a7" }
  ] }
}
```

- `TAXON_KEY` ist hierarchie-erweiternd (Familien-Key zieht alle Arten). Lizenz-Enums mit Unterstrich (`CC0_1_0`, `CC_BY_4_0`), **nicht** „CC BY 4.0".
- `DATASET_KEY 50c9509d-…` = iNaturalist Research-grade (nur dort parst GBIF Occurrence-Lizenzen record-by-record zuverlässig).
- **Pflicht danach:** `multimedia.txt` joinen → pro Bild `license` ∈ {CC0, CC-BY} filtern → erst dann Bild laden; Attribution (creator/rightsHolder/license-URL) je Bild für die CC-BY-Pflicht mitspeichern.

### 3.3 Tooling-Parameter (SAHI, aus Prep §4.2)

`slice 512px (oder 640 = Detektor-Input)` · `overlap 0.2` · `postprocess GREEDYNMM` · `match_metric IOS` · `match_threshold 0.5`.

### 3.4 Cold-Start- & HITL-Schwellen

- Pro Klasse CC0/CC-BY-Bilder aus GBIF seeden → **frozen-DINOv2-Prototypen** bilden (~30 Bilder/Klasse → on-leaf-Klassifikator live).
- HITL: Modell prä-annotiert Nutzerbilder, Mensch korrigiert; 150+ Labels/Klasse → eigener Detektor sinnvoll.
- **Larven-Hinweis:** Nützlings-Larven (Marienkäfer/Florfliege/Schwebfliege) bei iNaturalist seltener/schlechter annotiert → gezielt `lifeStage` filtern bzw. HITL priorisieren.

---

## WP-4 — Finale Klassen-Taxonomie (verifizierte GBIF-taxonKeys)

### 4.1 Schädlinge (`category=pest`) + Schadbilder (`category=symptom`)

| Slug (Vorschlag) | Dt. Name | Wiss. Name | GBIF taxonKey | Schadbild (Modus-2-Symptom) |
|---|---|---|---|---|
| `spider_mite` | Gemeine Spinnmilbe | *Tetranychus urticae* | **2130185** ✅ | helle Sprenkelung Blattoberseite, feine Gespinste Blattunterseite, Bronzefärbung |
| `thrips_frankliniella` | Kalifornischer Blütenthrips | *Frankliniella occidentalis* | **8351995** ✅ | silbrig-graue Saugflecken, schwarze Kotpünktchen, deformierte Blätter/Blüten (TSWV-Vektor) |
| `thrips_echinothrips` | Bunter Blütenthrips | *Echinothrips americanus* | **1420846** ✅ | silbrig-bronzene Saugflächen Blattoberseite |
| `fungus_gnat` | Trauermücken | *Sciaridae* (Fam.) / *Bradysia* | **3525** ✅ / **1488203** ✅ | schwarze Mücken über Substrat; weiße Larven im Substrat → Wurzelfraß |
| `aphid` | Blattläuse | *Aphididae* (Fam.) | **3042** ✅ | Honigtau/klebrig, Rußtau, gekräuselte Triebspitzen, Kolonien, Häutungshüllen |
| `mealybug` | Schmier-/Wollläuse | *Pseudococcidae* (Fam.) / *Planococcus citri* | **4534** ✅ / **5164206** ✅ | weiße Watte in Blattachseln, Honigtau + Rußtau |
| `whitefly` | Weiße Fliege | *Trialeurodes vaporariorum* / *Bemisia tabaci* | **2012132** ✅ / **2012126** ✅ | aufsteigende weiße Fliegen, Larven Blattunterseite, Honigtau/Rußtau |

Feinere Arten-Slugs (z. B. `aphid_myzus_persicae` 2076179, `mealybug_pseudococcus_longispinus` 2095283) optional als Untertypen. ⚠️ *Tetranychus*-Genus-Key `2130161` war **nicht** live verifiziert → vor Nutzung bestätigen.

### 4.2 Nützlinge (`category=beneficial`) — nie als Schädling melden

| Slug | Dt. Name | Wiss. Name | GBIF taxonKey |
|---|---|---|---|
| `ladybird` | Marienkäfer (+ Larven) | *Coccinellidae* / *Adalia bipunctata* | **7782** ✅ / **1043097** ✅ |
| `lacewing` | Florfliegen (Larven) | *Chrysopidae* | **9265** ✅ |
| `hoverfly` | Schwebfliegen (Larven) | *Syrphidae* | **6920** ✅ |
| `predatory_mite` | Raubmilben | *Phytoseiidae* / *Phytoseiulus persimilis* | **3511** ✅ / **2186348** ✅ |
| `parasitoid_wasp` | Schlupfwespen | *Encarsia formosa* / *Aphidius* | **1365418** ✅ / **1269075** ✅ |

### 4.3 Reststellen

- `category=unknown` — Reject-/Abstention-Klasse (Open-Set), siehe WP-5.
- Detektor: zusätzliche **Hintergrund-Negativklasse** (senkt False Positives).

---

## WP-5 — Kalibrierungs- & Abstention-Protokoll

1. **Training:** Klassifikator aus DINOv2-Backbone finetunen mit **Entropy-Regularisation + Label-Smoothing** (senkt ECE ~50 %). LS gegen die Risk-Coverage-Kurve gegenprüfen (kann Selective-Ranking verschlechtern).
2. **Post-hoc:** **Temperature Scaling** (ein Skalar, Fit auf Kalibrierungs-Split) + **Energy-Score** als OOD-Gate (für `unknown`). Beide Single-Forward-Pass, ONNX-exportierbar.
3. **Schwelle:** **nicht** fix `0,40`. Verfahren: Feld-Kalibrierungs-Split abspalten → TS fitten → **Risk-Coverage-Kurve** sweepen → **per-Klassen-Schwelle** auf **Ziel-Precision** (konservativ wegen Reliability-Gap). `0,40` nur als dokumentierter Tag-1-Default bis zum ersten Feld-Datensatz.
4. **Klassen:** explizite `beneficial`- und `unknown`-Klasse (~3 Accuracy-Punkte Kosten, gerechtfertigt — schützt vor Nützlings-Fehlklassifikation, ~3,6 % selbst im Labor).
5. **Phase 2:** Conformal Prediction (split/RAPS) erst ab **~1000 Feld-Kalibrierbeispielen**, mit **SSBC** (training-conditional) + **klassen-konditionalen** Schwellen.

---

## WP-6 — CPU-VLM-Erklärungs-Layer (Eval-Plan, optional)

- **Kandidaten:** Qwen2.5-VL-3B Q4_K_M (llama.cpp/libmtmd, ~2 GB + mmproj) · Moondream2 4-bit (~1,2 GB) · SmolVLM2-500M (minimal).
- **Messung auf x86-Zielhardware:** Latenz pro (Bild + Kurz-Prompt), RAM inkl. **mmproj** (additiv, unterberichtet), Qualität der Erklärung.
- **Entscheidungskriterium:** Latenz ≤ einige Sekunden auf Ziel-CPU → **default-an** als opt-in/asynchrones Feature; sonst **GPU-gated mit Graceful Degradation** (template-/regelbasierte Erklärung). VLM = **Erklärer, nie Erkenner**; nur über den bereits klassifizierten, kalibrierten Befund + RAG-Kontext, Ausgabe als „advisory".

---

## WP-7 — Kindwise-Anfrage (fertiger Text + Entscheidungskriterien)

### 7.1 Anfrage-Text (an Kindwise/FlowerChecker, EN)

> Subject: GDPR / data-processing questions before adopting plant.health for a self-hosted, privacy-first app
>
> We are evaluating Kindwise **plant.health** (and possibly insect.id) as an **optional, consent-gated** cloud adapter for indoor-houseplant pest detection. Our default is fully self-hosted; the cloud path is opt-in. Before signing, please clarify:
>
> 1. **Sub-processors:** full current list (Google Cloud, DigitalOcean, others?) incl. concrete region/datacenter, and is there a prior right to object to sub-processor changes (Art. 28(2) GDPR)?
> 2. **EU data residency:** can you contractually guarantee that image storage (GCS) and the relational DB (DigitalOcean) reside and remain in EU regions? Which region?
> 3. **Third-country transfer:** what safeguards against US access (Google/DigitalOcean as US parents) — SCCs, TIA/DTIA, DPF certification of sub-processors?
> 4. **Training opt-out:** §20.4 allows using submitted images to "improve services". Is there a contractual/technical **opt-out (zero-retention / no-training mode)**, ideally via an API flag?
> 5. **Immediate deletion:** can the 6-month storage be shortened per-request or contractually to delete-on-response, incl. backups/training sets? How binding is the deletion endpoint?
> 6. **Anonymization:** what exactly does "anonymization" cover beyond face-blurring (geolocation/IP per §20.5, EXIF)? Is it true anonymization under GDPR?
> 7. **plant.health class list:** full class list with explicit confirmation of *Tetranychus urticae*, thrips, *Sciaridae*, mealybugs, whitefly, aphids, and real-world (not internal-validation) accuracy for these.
> 8. **Product confirmation:** confirm plant.health (not crop.health) is the right product for indoor ornamentals, incl. pricing/accuracy.
> 9. **Audit artifact:** is there a usable audit certificate / Art. 32 TOM document for our DPIA (the external audit is a Masaryk-University pentest, not ISO-27001/SOC-2)?

### 7.2 Show-Stopper-Kriterien (für die Adapter-Entscheidung)

| Antwort | Konsequenz |
|---|---|
| **Kein** Trainings-Opt-out (Frage 4) | **Show-Stopper für Default-an.** Cloud-Adapter nur mit sehr prominenter Einwilligung + Hinweis „Bilder werden 6 Monate gespeichert & zum Training genutzt". |
| Keine EU-Residenz-Garantie (Frage 2/3) | Drittland-TIA/DSFA nötig; Self-Hosted bleibt Default. |
| plant.health deckt Zielschädlinge nicht belegt ab (Frage 7) | Cloud-Adapter-Mehrwert fraglich → ggf. ganz weglassen, rein self-hosted. |

---

## WP-8 — Stammdaten-Erweiterung REQ-010 (`beneficials` / `deficiencies`)

> **Vorschlag, kein Eingriff:** Diese Erweiterung gehört in eine bewusste REQ-010-Versionierung im Implementierungs-Sprint — hier nur als ausgearbeitetes Datenmodell, damit die Implementierung es direkt übernehmen kann. **Keine Änderung an implementiertem Code in diesem Schritt.**

```jsonc
// Neue Document Collection: beneficials  (analog pests)
{
  "_key": "beneficial_ladybird",
  "slug": "ladybird",
  "common_name": "Marienkäfer",
  "scientific_name": "Coccinellidae",
  "gbif_taxon_key": "7782",
  "preys_on": ["aphid", "spider_mite"],     // Bezug zu pests-Slugs
  "life_stages_relevant": ["adult", "larva"]
}
// Neue Document Collection: deficiencies  (Nährstoffmangel-Stammdaten, REQ-038/043-Lücke)
{
  "_key": "deficiency_nitrogen",
  "slug": "nitrogen_deficiency",
  "common_name": "Stickstoffmangel",
  "visual_symptoms": ["chlorosis_lower_leaves", "stunted_growth"],
  "confusable_with": ["disease_chlorosis", "overwatering"]   // Differenzialdiagnose
}
```

- `PestFinding.matched_pest_key` (REQ-044 §4.2) wird um `matched_beneficial_key` ergänzt; `category=beneficial` mappt dann gegen `beneficials`.
- Seed-Daten: die 5 Nützlinge aus WP-4.2 + gängige Mangel-Bilder aus der Wissensbasis (REQ-031).

---

## 12. „Bereit-für-Implementierung"-Checkliste

- [ ] **WP-1:** Lizenz-Memo (4 Punkte) an Rechtsprüfung; Entscheidung COCO-only-Checkpoints; Modell-Allowlist (kein RF-DETR-XL/2XL, kein YOLO).
- [ ] **WP-2:** Benchmark D-FINE-S/N vs. RF-DETR-S auf Ziel-CPU (Latenz/Small-Object-Recall, FP32 vs. INT8, mit SAHI); Modell final wählen.
- [ ] **WP-3:** GBIF-Download (Predicate fertig) + Bild-Lizenz-Filter-Pipeline; Attribution-Speicherung.
- [ ] **WP-4:** Klassen-Taxonomie als Enum/Seed übernehmen (Slugs + taxonKeys verifiziert).
- [ ] **WP-5:** nach erstem Feld-Datensatz: TS + Energy-Gate + Risk-Coverage-Schwellen; `0,40` ersetzen.
- [ ] **WP-6:** x86-CPU-VLM-Latenz messen → default-an oder GPU-gated entscheiden.
- [ ] **WP-7:** Kindwise-Anfrage senden (Text fertig); nach Antwort Adapter-Entscheidung per Show-Stopper-Tabelle.
- [ ] **WP-8:** REQ-010 um `beneficials`/`deficiencies` versionieren (Datenmodell fertig).

**Verbleibend rein extern (nicht weiter vorbereitbar):** Anwalts-Freigabe (WP-1), Kindwise-Antwort (WP-7), Benchmark-Lauf auf realer Hardware (WP-2), Annotations-Arbeit (WP-3) — alle mit fertigem Artefakt/Protokoll hinterlegt.

---

## 13. Quellen (Ergänzung zu prep/research)

**Lizenzen:** [D-FINE LICENSE](https://github.com/Peterande/D-FINE/blob/master/LICENSE) · [RT-DETR LICENSE](https://github.com/lyuwenyu/RT-DETR/blob/main/LICENSE) · [RF-DETR LICENSE](https://github.com/roboflow/rf-detr/blob/develop/LICENSE) · [RF-DETR+ PML-1.0](https://github.com/roboflow/rf-detr_plus/blob/main/LICENSE) · [PML-1.0](https://roboflow.com/platform-model-license-1-0) · [HF rf-detr-medium](https://huggingface.co/Roboflow/rf-detr-medium) · [Meta DINOv2-Relicense](https://ai.meta.com/blog/dinov2-facet-computer-vision-fairness-evaluation/) · [Objects365-Lizenz](https://docs.ultralytics.com/datasets/detect/objects365) · [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.en.html) · [FSF AGPL-FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)

**GBIF/Daten:** [GBIF Species Match](https://api.gbif.org/v1/species/match) (Keys live verifiziert) · [GBIF License Processing](https://data-blog.gbif.org/post/gbif-occurrence-license-processing/) · [GBIF Download Formats](https://techdocs.gbif.org/en/data-use/download-formats) · iNaturalist RG Dataset `50c9509d-22c7-4a22-a47d-8c48425ef4a7`

---

### Vorbehalte

- GBIF-Keys live verifiziert (ACCEPTED) **außer** *Tetranychus*-Genus `2130161` (heuristisch) — vor Nutzung bestätigen.
- Weights-⊆-Apache (D-FINE/RT-DETR) und Objects365-Pretraining-Vererbung bedürfen anwaltlicher Bestätigung; präventive Mitigation = COCO-only-Checkpoints.
- AGPL-§13-„combined work"-Reichweite juristisch unscharf (keine neutrale Primärquelle gefunden) — für die empfohlenen Apache-Modelle irrelevant.
- Kindwise-Antworten (WP-7) stehen aus; plant.health-Indoor-Trefferquote bleibt bis dahin unbelegt.
- CPU-Latenzen (WP-2) und x86-CPU-VLM-Latenz (WP-6) sind auf der realen Zielhardware zu messen.
