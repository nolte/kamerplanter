# Recherchebericht: Automatisierte Einschätzung der Pflanzengesundheit anhand von Bildern

**Stand:** Juni 2026 (Recherche-Cutoff)
**Kontext:** Entscheidungsgrundlage für ein Bilderkennungs-Feature in Kamerplanter — selbst-hostbar, datenschutzorientiert, Domänen: Zimmerpflanzen, Gemüse, Kräuter, Cannabis. Ziel: Erkennung/Einschätzung von Krankheiten, Schädlingsbefall, Nährstoffmängeln und allgemeinem Pflanzenstress per Foto.
**Methode:** Fan-out-Web-Recherche über 5 Themen-Forks (Kategorien A–E), je 8–22 Suchen/Fetches, Mehrquellen-Verifikation für Preise/Lizenzen/Genauigkeit.

---

## 1. Executive Summary (Kernerkenntnisse)

1. **Der „Reliability Gap" ist das beherrschende Problem, nicht die Modellwahl.** Reine Bild-Klassifikation ist im Labor faktisch „gelöst" (>99 % auf PlantVillage), bricht aber „in the wild" dramatisch ein — in der aktuellsten Cross-Domain-Studie von **99,73 % auf 32,05 %** (−67,7 Prozentpunkte), bei gleichzeitig **überkonfidenter** Vorhersage (Ø 79,76 % Konfidenz). **Keine** der getesteten Standard-Gegenmaßnahmen (Temperature Scaling, Selective Prediction, Domain Adaptation, OOD-Rejection, Ensembles) schließt diese Lücke. Jede Produkt-Entscheidung muss von dieser Realität ausgehen, nicht von Labor-Benchmarks.

2. **Krankheit, Schädling und Nährstoffmangel sind visuell oft nicht trennscharf — selbst für Pflanzenpathologen.** Reine Bildmerkmale reichen für eine belastbare Differenzialdiagnose häufig nicht. Genau das ist der Kern des angefragten Features (alle drei Symptomklassen plus „allgemeiner Stress") und der härteste fachliche Knoten. VLMs (GPT-4-vision) räumen explizit ein, abiotischen Stress nicht zuverlässig von Krankheit unterscheiden zu können.

3. **Die zwei wirksamsten Hebel sind multimodale Fusion und Human-in-the-Loop.** Bild + Symptombeschreibung/Kontext hebt die Genauigkeit messbar (Bild+Text-Fusion: +9,78 PP gegenüber nur-Bild, +21,11 PP gegenüber nur-Text). Der State-of-the-Art-Umgang mit VLM-Halluzination ist expert-verifiziertes Reasoning. Für Kamerplanter heißt das: Pflanzen-Kontext (Art, Phase, Standort, Sensordaten) als zusätzliches Signal nutzen und das Ergebnis als **Einschätzung mit Konfidenz und Disclaimer**, nicht als Diagnose ausspielen.

4. **Es gibt genau eine produktionsreife, breit abdeckende, EU-ansässige Cloud-API: Plant.id / Kindwise (Plant.Health).** Sie deckt Krankheit + Schädling + abiotischen Stress (548 Klassen) ab, sitzt in der EU (Brno/Prag, Rechenzentrum Zentraleuropa), hat Art.-28-Auftragsverarbeitungsverträge und klare Credit-Preise (€0,01–0,05/Credit). Pl@ntNet-Disease ist zu eng, Plantix B2B-only ohne öffentliche Preise und crop-fokussiert, Google/Azure erfordern teures Eigen-Training, Nyckel nur grob (5 Klassen), Flora Incognita hat kein Health-Modul.

5. **Reine Self-Hosting-Klassifikatoren (PlantVillage-CNNs) sind für „in the wild" untauglich, Foundation-Modelle aber tragfähig.** Klassische CNNs erben den Hintergrund-Bias (ein Modell auf nur 8 Hintergrund-Pixeln erreicht 49 % statt 2,6 % Zufall). Tragfähiger sind self-supervised Backbones (DINOv2, Apache-2.0), in-the-wild-Datensätze (PlantWild: 67,2 %) und domänenspezifische Open-Source-VLMs (Agri-LLaVA). CPU-Inferenz mit ONNX Runtime ist für Lightweight-CNNs problemlos (einstellige ms); ein lokales VLM braucht GPU (LLaVA-/Qwen2.5-VL-7B: ~16–24 GB VRAM).

**Empfehlung in einem Satz:** Phasen-Strategie aus (Phase 1) datenschutzfreundlicher Kindwise-EU-API mit EXIF-Strippen + Consent für schnellen Produktwert, parallel (Phase 2) self-hosted Hybrid aus Vision-Backbone für Erkennung + RAG-gestütztem (V)LM auf der bestehenden Krankheits-/Schädlings-Wissensbasis für Erklärung — immer als konfidenz-gewichtete Einschätzung mit Human-in-the-Loop, nie als verbindliche Diagnose.

---

## 2. Detaillierte Befunde

### A. Kommerzielle Cloud-APIs

#### Plant.id / Kindwise — Plant.Health API (führend für diesen Use-Case)

Anbieter: **Kindwise s.r.o.**, HQ Brno/Prag, Tschechien (EU-Jurisdiktion → DSGVO-relevant vorteilhaft).

- **Funktionsumfang:** Echte Pflanzengesundheits-Diagnose (nicht nur Plant-ID). Das Modell unterscheidet **548 Klassen** (zuvor 90) über **Pilze, Bakterien, Viren, Insekten/Schädlinge, abiotische Störungen (Nährstoffmängel/Stress)** und nicht-schädliche Look-alikes. Separates `is_healthy`-Modell; `disease_level=general` für vereinfachte Antworten. 2025 neu: automatisierte „follow-up questions" (Experten-Rückfragen zur Diagnose-Verfeinerung) — passt direkt zum Multi-Signal-Gedanken. Annotation durch echte Pflanzenpathologen, mehrsprachige Knowledge-Base.
- **Genauigkeit:** Anbieterangabe **>73 % korrekte Diagnose in den Top-3-Ergebnissen**. (Selbstauskunft, kein unabhängiger Benchmark.)
- **Preismodell:** Credit-basiert. **1 Credit pro Disease-Diagnose**, **2 Credits** bei kombinierter plant.id + plant.health-Abfrage. Basispreis **€0,05/Credit (€50/1.000)**, volumenabhängig sinkend bis **€0,01/Credit (€10/1.000)**. **100 Free-Credits** bei Signup; Demo ohne API-Key: **10 Identifikationen/Monat**. Prepaid oder retroaktive Monatsabrechnung.
- **DSGVO/Datenschutz:** Rechenzentrum in **Zentraleuropa**; HTTPS/TLS, server-side encryption, IAM-Policy. Zum **01.07.2024** wurden **Auftragsverarbeitungsverträge nach Art. 28.3 DSGVO** aktualisiert. Datenschutzaussage: „No photos younger than six months will be displayed back to anyone before anonymization" → Bilder werden **mind. 6 Monate gespeichert** und vor Wiederverwendung anonymisiert; Lösch-/Abruf-Endpunkte (ohne Credit-Kosten) vorhanden. Externes Security-Audit durchlaufen. ⚠️ Konkreter Serverstandort wird öffentlich nicht namentlich genannt — vor Produktiveinsatz im AVV verifizieren.
- **API-Format:** REST/JSON (v3), Postman-dokumentiert, optimale Bildauflösung 1–2 MP, bis 10 Vorschläge mit Confidence-Score.

#### Pl@ntNet API

- **Funktionsumfang:** Primär Arterkennung. Es **existiert** ein Disease-Endpoint (`POST /v2/diseases/identify`), aber **eng begrenzt** auf „nur eine begrenzte Liste von Species und Pathologien" (abrufbar via `/v2/diseases`), Ergebnisse mit EPPO-Codes + Confidence. Nicht produktionsreif als breite Health-Lösung.
- **Lizenz/Kosten:** Disease-Identify kostet 1 Credit; **kostenlos bis 500 Identifikationen/Tag**, darüber kommerziell kostenpflichtig (kommerzielles Agreement nötig).
- **Fazit:** Stärke bleibt Arterkennung (relevant für N-001/REQ-029, nicht für Health-Assessment).

#### Google Cloud Vision / Vertex AI

- **Eignung:** **Kein** out-of-the-box Pflanzenkrankheits-Label. Custom-Training über Vertex AI AutoML zwingend (~1.000 Bilder/Label empfohlen).
- **Kosten:** AutoML-Image-Training **$3,465/h**, deployter Endpoint **$1,375/h** (Dauerkosten), generische Object-Detection-Inferenz ~**$1,50/1.000 Bilder**. → Hoher Eigenaufwand + laufende Endpoint-Kosten.

#### Microsoft Azure Custom Vision

- **Eignung:** Ebenfalls Custom-Training nötig (kein Werk-Modell).
- **Kosten:** Training **$10/h**, Storage **$0,70/1.000 Bilder**, Predictions **$2/1.000**.

#### Weitere Anbieter

- **Plantix (PEAT GmbH, Berlin):** Sehr breit (**>780 Pflanzenkrankheiten**, field-tested mit ~8 Mio. Farmern), aber **B2B-only über Sales/Partnerschaft**, keine öffentlichen Preise, **crop-/acker-fokussiert** (wenig Zimmerpflanzen). Deutscher Ursprung potenziell DSGVO-vorteilhaft, aber Vertrag erforderlich.
- **Flora Incognita (TU Ilmenau/MPI):** Reine Arterkennung (>30.000 Arten), **keine Krankheitserkennung**, API nur für registrierte Clients. Für Health ungeeignet.
- **Nyckel:** Generische Classifier-Plattform mit vortrainiertem Plant-Health-Classifier, aber nur **5 grobe Labels** (Damaged, Dead, Diseased, Dying, Healthy) — keine konkrete Diagnose. Free-Tier, eigene Custom-Classifier trainierbar.

### B. Open-Source-Modelle & Datensätze (Self-Hosting)

#### Datensätze

| Datensatz | Größe | Klassen / Arten | Bedingungen | In-the-wild-Genauigkeit | Lizenz |
|---|---|---|---|---|---|
| **PlantVillage** | ~54.303 Bilder | 38 Klassen / 14 Arten | Labor (uniformer Hintergrund) | n/a (Lab >99 %) | „research/educational", **CC0 NICHT eindeutig** ⚠️ |
| **PlantDoc** | 2.569 Bilder | 30 Klassen / 13 Arten | Feld (Internet-Scrape) | hebt Genauigkeit bis +31 % | **CC-BY-4.0** |
| **PlantWild** | 18.542 Bilder | 89 Typen (56 krank + 33 gesund) | in-the-wild | Baseline **67,20 %** | keine explizite Lizenz ⚠️ |
| **iNaturalist Open** | ~859k (Subset) | 5.000+ Arten | gemischt | **Arterkennung, nicht Krankheit** | CC0/CC-BY/CC-BY-NC (gemischt) |

**Zentrale Limitierung PlantVillage:** Background-/Capture-Bias — ein nur auf **8 Hintergrund-Pixeln** trainiertes Modell erreicht **49,0 % Accuracy** (Zufall 2,6 %). Modelle lernen labelkorrelierte Hintergrundartefakte statt Symptome; Domain-Shift lässt Accuracy von 99 % auf ~31 % fallen. Hintergrundentfernung + Lab/Feld-Mischung hebt auf ~77,5–80,3 % — bleibt aber unter Labor-Niveau.

#### Modelle & Foundation-Ansätze

- **Klassische CNNs (ResNet/EfficientNet/MobileNet) auf PlantVillage:** >99 % im Lab, aber erben den Bias → **untauglich für „in the wild"** ohne Domänen-Daten.
- **DINOv2 (Meta):** Self-supervised ViT-Backbone, seit Aug. 2023 **Apache 2.0** (kommerziell nutzbar). In der Cross-Domain-Studie das **robusteste Backbone** (DINOv2-Ensemble: bestes selektives Risiko, ~43 % Accuracy im Feld-Worst-Case). ⚠️ DINOv3 (2025) ist NICHT Apache-lizenziert. PlantCLEF-2024-DINOv2-Gewichte sind **CC-BY-NC-4.0** (nicht-kommerziell) und nur Artbestimmung.
- **Few-Shot:** QLoRA + DINOv2-S + Prototypical Network tunt ~1 % der Parameter; Domain-Adapted Lightweight Ensemble erreicht auf echtem Feld-Datensatz nur **15-shot 69,28 %** — Few-Shot „in the wild" noch mäßig.
- **HuggingFace-Modelle:** z. B. `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification` (95,41 % Lab, 38 Klassen, Lizenz „other" ⚠️), `wambugu71/crop_leaf_diseases_vit`. **Lizenzen pro Modellkarte einzeln prüfen** — viele undeklariert. ONNX-Export für MobileNetV2/V3 problemlos.

#### Self-Hosting-Anforderungen

- **CPU-Inferenz für Lightweight-CNNs absolut machbar:** ONNX Runtime (XNNPACK) → einstellige Millisekunden-Latenz auf Server-CPU. Modellgrößen: MobileNetV3-Small ~6,1 MB, MobileNetV2 ~13,4 MB, Ensemble ~40 MB (~1,12 GFLOPs). **Keine GPU nötig** für CNN-Inferenz.
- DINOv2-ViT-base und lokale VLMs sind deutlich teurer → GPU empfehlenswert (siehe C).

### C. Multimodale LLMs / Vision-Language-Models (VLM)

#### Cloud-VLMs (GPT-4o, Gemini, Claude)

**Kernbefund: Zero-Shot schwach, Few-Shot/Fine-Tuned stark, aber ohne Spezialisierung unzuverlässig.**

- **Zero-Shot deutlich schlechter als Spezialmodelle:** GPT-4o ~**56 %** globale Accuracy; Gemini-pro-1.5 Zero-Shot F1 **50,45 %**, GPT-4o Few-Shot F1 **73,37 %** (Few-Shot hebt massiv: +15,38 % durch relevante Beispiele).
- **Fine-Tuned kann CNNs schlagen:** fine-getuntes GPT-4o **98,12 %** vs. ResNet-50 96,88 % auf Apfelblättern — aber nur nach Fine-Tuning.
- **Modellprofile:** **Claude-3.5-Sonnet** führte in einem Plant-Stress-Review bei Klassifikation und Quantifizierung; GPT-4o bestes Few-Shot; Gemini-pro-1.5 stark im Zero-Shot bei einzelnen Aufgaben.
- **AgroBench:** GPT-4o ~73,45 % Overall; **Disease-Identification bei ALLEN Modellen niedriger als Disease-Management** (Wissen vorhanden, visuelle Fein-Diagnose schwach).
- **Stärken:** natürliche Sprache, kontextuelle Erklärung, Bild+Text-Kombination, Treatment-Empfehlungen, Decision-Support für Laien.
- **Schwächen:** Halluzination („fabricated or misleading content", in Agrar gefährlich), Überkonfidenz, fehlende präzise Lokalisierung/Quantifizierung, schwache Fein-Granularität, **kann Krankheit nicht zuverlässig von abiotischem Stress/Nährstoffmangel trennen**, keine standardisierte Zuverlässigkeitsmessung.

#### Lokale offene VLMs (Self-Hosting)

| Modell | Größe | VRAM | Eignung |
|---|---|---|---|
| **LLaVA-1.5 7B** | 7B | ~8 GB RAM (CPU via Ollama machbar) | Generalist, Basis vieler Agrar-Fine-Tunes |
| **Qwen2.5-VL 7B** | 7B | 16 GB (4-bit) / 24 GB (FP16, RTX 3090/4090) | Stark, single-GPU |
| **Qwen2.5-VL 72B** | 72B | ~384 GB (Cluster) | Nur Server-Cluster |
| **Agri-LLaVA** | 7B | wie LLaVA | **domänenspezifisch: 221 Schädlings-/Krankheitstypen** |

- **Agri-LLaVA** (open-source, GitHub): zweistufiges Training, ~400k Alignment-Samples über 221 Schädlings-/Krankheitstypen; **60,05 % VQA-Accuracy** (vs. LLaVA 55,18 %), erreicht 55,4 % der GPT-4-Performance. Stärkster domänenspezifischer Open-Source-Kandidat.
- **AgriGPT-VL** (2025): **70,10 %** auf AgriBench, schlägt InternVL-3-8B/LLaVA-7B, open-source angekündigt.
- **SCOLD** (CLIP-basiert, leaf-disease, HuggingFace `enalis/scold`, CC-BY-SA-4.0). CLIP-ViT-B/16 Zero-Shot F1 **66,29 %** bei kleinem Footprint.

#### VLM + RAG (Wissensbasis als Kontext)

**Dominantes Muster: Vision-Modell perzipiert → (V)LM + RAG erklärt/empfiehlt.**

- **RAG-augmented YOLOv8 (Coffee):** YOLOv8 detektiert + lokalisiert die Krankheit, RAG holt kuratiertes Agrarwissen und generiert farmer-gerechte Erklärung — **getrennte Optimierung von Perzeption und Erklärung**.
- RAG „mindert unzuverlässige/halluzinierte Outputs" und integriert hochdimensionale biologische Daten.
- **PhenoGPT-Befund:** GPT-4o allein liefert „inconsistent results"; erst kombiniert mit task-spezifischen Vision-Modellen zuverlässig. → Architekturprinzip: pretrained Vision-Modell für Recognition, LLM für contextual reasoning + Reports.
- **Direkte Relevanz für Kamerplanter:** Die bestehende RAG-Wissensbasis (`spec/knowledge/rag/`, Knowledge-Service) ist genau die Komponente, die ein VLM zur erklärenden, halluzinations-gedämpften Ausgabe braucht.

### D. Wissenschaftlicher / methodischer Stand (2023–2025)

#### Der „Reliability Gap" (Lab vs. Feld) — zentrales Ergebnis

Aktuellste Cross-Domain-Studie (Frontiers in Plant Science, PlantVillage→PlantDoc):

- Accuracy bricht von **99,73 % (Labor) auf 32,05 % (Feld)** ein (−67,7 PP).
- Modell bleibt **überkonfident**: Ø vorhergesagte Konfidenz **79,76 %** trotz nahezu zufälliger Trefferquote.
- Grad-CAM: Aufmerksamkeit verschiebt sich von Läsionen auf **Hintergrund-Clutter**.
- **Keine Standard-Gegenmaßnahme schließt die Lücke:** Temperature Scaling (bei 80 % Coverage noch 64,3 % Fehler), Selective Prediction (Coverage 0,29 % für 5–15 % Zielrisiko → unbrauchbar), Domain Adaptation (max. 36,6 %; adversariell sogar schlechter), OOD-Rejection (AUROC ~0,61 ≈ Zufall), Ensembles (bestes DINOv2-Ensemble 43,8 %, Risiko bei 80 % Coverage 51,7 %). Stärkere self-supervised Repräsentationen (DINOv2) helfen am meisten, schließen die Lücke aber nicht.

#### Bekannte Probleme

- **Datensatz-Bias/Background-Leakage** (PlantVillage, s. B): 8-Pixel-Modell 49 % Accuracy.
- **Domain-Shift, Beleuchtung, Hintergrund:** massive Distributionsunterschiede (Cohen's d bis 3,90 für Sättigung).
- **Krankheit ↔ Schädling ↔ Nährstoffmangel ↔ mechanischer Schaden:** visuell so ähnlich, dass „even plant pathologists have faced trouble" — reine Bildmerkmale oft unzureichend. Fehlklassifikationen v. a. zwischen morphologisch ähnlichen Läsionen (z. B. Tomate Septoria vs. Kraut-/Braunfäule).
- **Frühe vs. späte Stadien:** Frühstadien schwer erkennbar (implizit in den Domain-Gaps).

#### Nährstoffmangel-Erkennung per Bild

Hohe Genauigkeit, aber **überwiegend unter kontrollierten Bedingungen / isolierten Datensätzen**:
- Soja N/P/K mit YOLOv8s: Precision **90,03–96,54 %**.
- EfficientNet + Transfer Learning: Orange **98,52 %**, Zuckerrübe **98,65 %**.
- PND-Net (GCN): Banane-Mangel 90,00 %, Kaffee-Mangel 90,54 %, aber **Mangel und Krankheit als getrennte Tasks auf getrennten Datensätzen** — die eigentliche Differenzierung Mangel-vs-Krankheit wird *nicht* adressiert.

#### Wirksamste Hebel: Multimodalität & Human-in-the-Loop

- **Multimodale Fusion verbessert messbar:** Bild+Text-Fusion **98,33 %** (+9,78 PP gegenüber nur-Bild, +21,11 PP gegenüber nur-Text). Transformer-Ansätze integrieren Bild + Text + Sensordaten und senken den Bedarf an gelabelten Daten.
- **Human-in-the-Loop ist State-of-the-Art gegen Halluzination:** Expert-verified Reasoning Chains (VLM entwirft Rationale → Agrarexperte verifiziert → offenes VLM fine-tunen).
- **Konfidenz/Kalibrierung:** Softmax neigt zu Overconfidence bei OOD; Energy-Score weniger anfällig. Kalibrierte Konfidenz, OOD-Abstention und klare Disclaimer sind für ein Produkt **zwingend**.

### E. Datenschutz (DSGVO) & Betrieb

#### Bilder als personenbezogene Daten

- Bilder werden personenbezogen, sobald eine Person **direkt** (Gesicht) oder **indirekt** (Kleidung, Tattoos, identifizierbarer Innenraum) erkennbar ist. Bei Indoor-/Growroom-Fotos realistisch. Biometrische Verarbeitung → **Art. 9 DSGVO** (besondere Kategorien) — für reine Pflanzendiagnose nicht einschlägig, aber als Abgrenzung relevant.

#### EXIF-/Metadaten-Risiko

- **GPS-Koordinaten in EXIF gelten als personenbezogene Daten;** Smartphone-Fotos betten GPS/Zeit/Gerät standardmäßig ein → Standort = Wohnung des Nutzers.
- **Kritische API-Falle:** EXIF wird bei **API-basierten Uploads oft NICHT automatisch entfernt** (anders als bei Web-/App-Frontends großer Plattformen). Selbst Plattformen, die EXIF aus dem öffentlichen Bild strippen, lesen GPS oft vorher serverseitig aus.
- **Einziger zuverlässiger Schutz: Metadaten VOR dem Upload entfernen**, idealerweise clientseitig (Bild verlässt das Gerät metadatenfrei).

#### Drittland-Transfer (USA), Stand 2025/2026

- **EU-US Data Privacy Framework (DPF)** wurde am **03.09.2025** vom EU-Gericht (Latombe-Klage) bestätigt — bleibt aber **CJEU-revisionsgefährdet** („Schrems III" gilt als wahrscheinlich). → Drittland-Transfer ist heute zulässig (DPF-Zertifizierung oder SCCs + TIA), aber **regulatorisches Klumpenrisiko**. EU-Hosting/Self-Hosting eliminiert es vollständig.

#### Auftragsverarbeitung

- Dritt-API = Auftragsverarbeiter → **AVV nach Art. 28 DSGVO Pflicht**. Kindwise/Plant.id erfüllt dies (Art. 28.3, Stand 01.07.2024), speichert Bilder aber mind. 6 Monate vor Anonymisierung.

#### On-Device/Self-Hosted vs. Cloud — Trade-offs

| Kriterium | On-Device / Self-Hosted | Cloud-API (Dritt) |
|---|---|---|
| **Privacy/DSGVO** | Daten verlassen das System nicht → kein Drittland-Transfer, kein AVV, minimales Risiko | Bild + Metadaten an Dritten; AVV + ggf. Drittland-Transfer + Consent nötig |
| **Latenz** | konsistent, netzunabhängig | netzwerkabhängig |
| **Kosten** | ~null marginale Kosten/Inferenz (nur Infrastruktur) | Per-Call-Gebühren, skalieren mit Volumen |
| **Offline** | funktioniert ohne Internet | erfordert Konnektivität |
| **Modellqualität** | kleineres lokales Modell = mehr Fehler | größere, stärkere Modelle |
| **Wartung** | eigener Betrieb/Updates/ggf. GPU | Anbieter wartet |

Empfohlenes Muster der Quellen: **Hybrid** — Routine lokal, komplexe/seltene Fälle Cloud.

#### Best Practices

1. EXIF/Metadaten **clientseitig oder beim Ingest sofort strippen** (vor jeder Weitergabe).
2. **Explizite, granulare Einwilligung** für jede Drittverarbeitung (Opt-in ohne Vorauswahl, widerrufbar, dokumentiert, Art. 7) — passt zum bestehenden Consent-Record-Mechanismus (REQ-025).
3. Lawful Basis (Art. 6), Verschlüsselung at-rest/in-transit, RBAC + Audit-Logs, klare Aufbewahrungsfristen.
4. **Default-Privacy:** Self-Hosting als Default, Cloud-API nur als optionales, consent-gesteuertes Upgrade.

---

## 3. Vergleichstabelle der Hauptansätze

Bewertung: ●●● = stark/gut, ●● = mittel, ● = schwach/problematisch.

| Kriterium | **Cloud-API** (Kindwise Plant.Health) | **Self-Hosted CNN/ViT** (PlantVillage/PlantWild + DINOv2) | **VLM/LLM** (Cloud GPT-4o/Claude/Gemini *oder* lokal LLaVA/Qwen-VL/Agri-LLaVA) | **Hybrid** (Vision-Backbone + RAG-(V)LM, self-hosted) |
|---|---|---|---|---|
| **Genauigkeit** | ●●● >73 % Top-3 (Anbieter), breit annotiert | ●● Lab >99 %, Feld ~32–67 % (Reliability Gap) | ●● Zero-Shot schwach (~56 %), Few-Shot/Fine-Tuned stark (73–98 %) | ●●● best-of-both: spezialisierte Erkennung + erklärende Diagnose |
| **Kosten** | ●● €0,01–0,05/Diagnose, kein Eigen-Training | ●●● ~null/Inferenz nach Training | ●/●● Cloud: Per-Call-Token; lokal: GPU-Infrastruktur | ●● GPU-Infrastruktur, kein Per-Call (außer optionale Cloud-Eskalation) |
| **Datenschutz/DSGVO** | ●● EU-Sitz + AVV, aber Bild-Upload an Dritt + 6-Mon.-Speicherung | ●●● Daten bleiben im System | Cloud ●/lokal ●●● | ●●● Daten bleiben im System |
| **Offline-Fähigkeit** | ● erfordert Konnektivität | ●●● voll offline (CPU genügt) | Cloud ●/lokal ●●● (GPU) | ●●● voll offline (GPU) |
| **Wartungsaufwand** | ●●● Anbieter wartet Modell | ●● eigenes (Re-)Training, Daten-Pflege | lokal ● (GPU-Betrieb, Updates) | ● höchster Aufwand (zwei Komponenten + Wissensbasis) |
| **Erklärbarkeit** | ●● Confidence + Knowledge-Base + Follow-up-Fragen | ● reine Klassen-Wahrscheinlichkeit, ggf. Grad-CAM | ●●● natürliche Sprache, Kontext, Treatment | ●●● erklärend + lokalisiert + RAG-gestützt |
| **Integrationsaufwand** | ●●● REST/JSON, sofort nutzbar | ●● ONNX-Inferenz-Dienst aufzusetzen | ●● Cloud-SDK / lokaler Serving-Stack | ● höchster (Pipeline aus Vision + RAG + (V)LM) |
| **Abdeckung (Krankheit/Schädling/Mangel)** | ●●● alle drei + abiotischer Stress (548 Klassen) | ●● v. a. Krankheit; Mangel nur in Spezial-Modellen, getrennt | ●● breit per Wissen, aber Mangel-vs-Krankheit unsicher | ●●● breit + RAG-Kontext, Mangel-Differenzierung über Multi-Signal verbessert |

---

## 4. Empfehlung (begründete Phasen-Strategie)

Für eine **selbst-hostbare, datenschutzorientierte** Anwendung wie Kamerplanter ist **kein einzelner Ansatz** optimal — die Befunde sprechen klar für eine **Phasen-Strategie**, die schnellen Produktwert mit langfristiger Datenschutz-Souveränität verbindet.

### Phase 1 — Schneller, datenschutzkonformer Produktwert: Kindwise Plant.Health als opt-in-Cloud-Adapter

- **Warum:** Einzige produktionsreife API, die Krankheit + Schädling + abiotischen Stress breit abdeckt, EU-ansässig, mit Art.-28-AVV und klaren Preisen. REST/JSON integriert sich nahtlos in das bestehende External-Adapter-Pattern (`domain/interfaces/` ABC + `data_access/external/`, wie bei GBIF/Perenual/Pl@ntNet).
- **Pflicht-Leitplanken:**
  - **EXIF/Metadaten serverseitig beim Ingest strippen**, bevor irgendein Byte die Anwendung verlässt (clientseitig zusätzlich erwünscht).
  - **Explizite, granulare Einwilligung** (Consent-Record, REQ-025) als Gate für die Drittverarbeitung — analog zum bestehenden Consent-Middleware-Muster (HIBP/Sentry/Enrichment).
  - AVV mit Kindwise abschließen, Serverstandort verifizieren, 6-Monats-Speicherung im Datenschutzhinweis transparent machen.
  - Ergebnis als **konfidenz-gewichtete Einschätzung mit Disclaimer** ausgeben, nicht als verbindliche Diagnose; Kindwise-„follow-up questions" als Multi-Signal-Verfeinerung nutzen.

### Phase 2 — Datenschutz-souveräner Self-Hosted-Hybrid (das eigentliche Ziel)

Architektur nach dem belegten State-of-the-Art-Muster **„Vision-Modell perzipiert → RAG-(V)LM erklärt"**:

1. **Erkennungs-Stufe (Vision):** kein PlantVillage-only-CNN (Reliability Gap!). Stattdessen **self-supervised Backbone (DINOv2, Apache-2.0)** + Klassifikator/kNN, trainiert/feingetunt auf **in-the-wild-Daten (PlantWild/PlantDoc)** und eigenen Nutzerbildern. Lightweight-Variante per ONNX Runtime CPU-fähig; DINOv2-Embeddings für Few-Shot auf seltene Cannabis-/Zimmerpflanzen-Krankheiten.
2. **Erklärungs-Stufe (RAG-(V)LM):** **lokales VLM** (LLaVA-7B / Qwen2.5-VL-7B, ~16–24 GB VRAM; oder domänenspezifisch **Agri-LLaVA**) gekoppelt an die **bestehende RAG-Wissensbasis** (`spec/knowledge/rag/`, Knowledge-Service). Das (V)LM erklärt, ordnet Treatment-Optionen zu und dämpft Halluzination durch den abgerufenen Wissens-Kontext.
3. **Multi-Signal-Fusion (der Genauigkeits-Hebel):** Foto **plus** Pflanzen-Kontext aus Kamerplanter (Art/Cultivar, Phase, Substrat, Standort, **Sensordaten** VPD/EC/pH, jüngste IPM-/Feeding-Events) als zusätzliche Modalität — belegt +10–21 PP und der einzige praktikable Weg, Mangel/Krankheit/Schädling-Verwechslung zu reduzieren.

### Querschnitt (für beide Phasen verbindlich)

- **Human-in-the-Loop + Konfidenz/Abstention:** kalibrierte Konfidenz anzeigen, bei niedriger Konfidenz **abstain** statt überkonfidenter Falschdiagnose, Nutzer-Feedback („richtig/falsch") als Trainings-/Adaptionssignal — passt zum bestehenden adaptiven-Learning-Muster (CareReminderEngine).
- **Disclaimer-Pflicht:** durchgängig als „Einschätzung", nie als gesicherte Diagnose; insbesondere bei Cannabis (rechtliche Sensibilität) und bei Pflanzenschutz-/Karenz-Empfehlungen (Verknüpfung mit IPM/Karenz-Gate).
- **Adapter-Abstraktion:** Vision-Health als austauschbarer Adapter (Cloud Kindwise ⇄ Self-Hosted Hybrid), sodass Light-Modus/On-Prem-Deployments rein lokal laufen und Cloud nur ein opt-in-Upgrade ist — Default-Privacy.

**Begründung der Reihenfolge:** Phase 1 liefert sofort breite, gepflegte Abdeckung ohne ML-Eigenbetrieb und ist DSGVO-tragbar (EU + Consent + EXIF-Strip). Phase 2 ist aufwändiger (zwei Komponenten + Wissensbasis-Kopplung + GPU), erreicht aber die eigentliche Zielsetzung „selbst-hostbar + datenschutz-souverän + offline" und nutzt mit der vorhandenen RAG-Wissensbasis und den Sensordaten genau die Assets, die Kamerplanter bereits hat und die laut Forschung den größten Genauigkeits-Hebel darstellen.

---

## 5. Quellenliste

### A. Kommerzielle Cloud-APIs
- Kindwise plant.health — https://www.kindwise.com/plant-health
- Kindwise FAQ (GDPR, Serverstandort, Retention) — https://www.kindwise.com/faq
- Kindwise Pricing — https://www.kindwise.com/pricing
- Kindwise plant.health follow-up questions (2025) — https://www.kindwise.com/post/new-plant-health-feature-follow-up-questions
- Kindwise — Wikipedia — https://en.wikipedia.org/wiki/Kindwise
- Pl@ntNet API — Diseases identification — https://my.plantnet.org/doc/api/diseases
- Pl@ntNet API — Terms of Use — https://my.plantnet.org/terms_of_use
- Cloud Vision API Pricing — https://cloud.google.com/vision/pricing
- Vertex AI Pricing (nOps) — https://www.nops.io/blog/vertex-ai-pricing/
- Azure Custom Vision Pricing — https://azure.microsoft.com/en-us/pricing/details/cognitive-services/custom-vision-service/
- Plantix Vision API — https://plantix.net/en/business/plantix-vision-api/
- Plantix API Toolkit — https://plantix.net/en/b2b-solutions/api-toolkit/
- Flora Incognita — https://floraincognita.com/
- Nyckel Plant Health Classifier — https://www.nyckel.com/pretrained-classifiers/plant-health/

### B. Open-Source-Modelle & Datensätze
- PlantVillage — IEEE DataPort — https://ieee-dataport.org/documents/plantvillage-plant-disease-classification-dataset
- PlantVillage — Kaggle — https://www.kaggle.com/datasets/mohitsingh1804/plantvillage
- Uncovering bias in PlantVillage (Noyan, arXiv:2206.04374) — https://arxiv.org/abs/2206.04374
- PlantDoc (arXiv:1911.10317) — https://arxiv.org/abs/1911.10317
- PlantDoc — Roboflow — https://public.roboflow.com/object-detection/plantdoc
- PlantWild (arXiv:2408.03120) — https://arxiv.org/html/2408.03120v1
- Plant disease recognition datasets review (PMC11466843) — https://pmc.ncbi.nlm.nih.gov/articles/PMC11466843/
- iNaturalist Developers/Licensing — https://www.inaturalist.org/pages/developers
- Meta DINOv2 (Apache 2.0) — https://ai.meta.com/blog/dinov2-facet-computer-vision-fairness-evaluation/
- DINOv2 PlantCLEF 2024 weights — https://huggingface.co/vincent-espitalier/dino-v2-reg4-with-plantclef2024-weights
- Few-Shot QLoRA + DINOv2 — https://www.researchsquare.com/article/rs-9014055/v1
- Domain-Adapted Lightweight Ensemble (arXiv:2512.13428) — https://arxiv.org/html/2512.13428v1
- HF mobilenet_v2 plant-disease — https://huggingface.co/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification
- HF crop_leaf_diseases_vit — https://huggingface.co/wambugu71/crop_leaf_diseases_vit
- ONNX Runtime Serving Performance — https://martynassubonis.substack.com/p/optimize-for-speed-and-savings-high
- ONNX Model Zoo — https://github.com/onnx/models

### C. VLMs / Vision-Language-Models
- AI Plant Doctor (GPT4-vision) — https://www.online-rpd.org/journal/view.php?number=1837&viewtype=pubreader
- Integration of LLMs/VLMs in plant stress phenotyping (PMC13109329) — https://pmc.ncbi.nlm.nih.gov/articles/PMC13109329/
- Plant Disease Detection via Multimodal LLMs & CNNs (ResearchGate) — https://www.researchgate.net/publication/391282315_Plant_Disease_Detection_through_Multimodal_Large_Language_Models_and_Convolutional_Neural_Networks
- PlantVillageVQA (arXiv:2508.17117) — https://arxiv.org/abs/2508.17117
- AgroBench (arXiv:2507.20519) — https://arxiv.org/abs/2507.20519
- AgriGPT-VL (arXiv:2510.04002) — https://arxiv.org/abs/2510.04002
- Agri-LLaVA (arXiv:2412.02158) — https://arxiv.org/html/2412.02158v2
- RAG-Augmented YOLOv8 for Coffee Disease (arXiv:2505.21544) — https://arxiv.org/pdf/2505.21544
- SCOLD VL Foundation Model (arXiv:2505.07019) — https://arxiv.org/pdf/2505.07019
- Qwen VRAM Requirements — https://gigagpu.com/qwen-vram-requirements/
- Qwen2.5-VL 72B VRAM — https://blogs.novita.ai/qwen2-5-vl-72b-vram/
- LLaVA open-source (TDS) — https://medium.com/data-science/llava-an-open-source-alternative-to-gpt-4v-ision-b06f88ce8efa
- Ollama System Requirements — https://localaimaster.com/blog/ollama-system-requirements

### D. Wissenschaftlicher Stand
- Quantifying the Reliability Gap in Cross-Domain Plant Disease Classification (Frontiers, 2026) — https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2026.1826962/abstract
- AI-Driven Plant Disease Detection & Diagnosis (PMC13066816) — https://pmc.ncbi.nlm.nih.gov/articles/PMC13066816/
- Cross-Modal Data Fusion via VLM for Crop Disease (MDPI Sensors 25/13/4096) — https://www.mdpi.com/1424-8220/25/13/4096
- Soybean nutrient deficiencies YOLOv8s (Sci Reports) — https://www.nature.com/articles/s41598-024-83295-6
- EfficientNet nutrient deficiency (ScienceDirect) — https://www.sciencedirect.com/science/article/abs/pii/S0168169922001855
- PND-Net (PMC11226607) — https://pmc.ncbi.nlm.nih.gov/articles/PMC11226607/
- Fine-tuning paradigms / unknown disease recognition (Sci Reports) — https://www.nature.com/articles/s41598-024-66958-2
- Unsupervised Domain Adaptation in the Wild (Plant Phenomics) — https://spj.science.org/doi/10.34133/plantphenomics.0038

### E. Datenschutz & Betrieb
- Geolocation metadata extraction (Fastio) — https://fast.io/resources/geolocation-metadata-extraction-from-photos/
- EXIF data privacy (Proton) — https://proton.me/blog/exif-data
- GDPR for Images (GDPRLocal) — https://gdprlocal.com/gdpr-for-images/
- Does X remove EXIF (PrivacyStrip) — https://privacystrip.com/blog/does-x-remove-exif-data/
- Remove EXIF before sharing (EXIFData.org) — https://exifdata.org/blog/photo-privacy-checklist-remove-exif-data-before-sharing
- Kindwise updated T&C / Art. 28 (Blog) — https://www.kindwise.com/post/updated-t-c-and-sla-revamp-faster-responses-guaranteed
- EU-US DPF judicial review (WilmerHale) — https://www.wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/20251201-european-court-of-justice-to-review-challenge-to-eu-us-data-privacy-framework
- DPF survives first challenge (Freshfields) — https://www.freshfields.com/en/our-thinking/blogs/technology-quotient/eu-us-data-privacy-framework-survives-its-first-judicial-challenge-but-more-are-102l4m1
- On-Device vs Cloud AI Economics (MindStudio) — https://www.mindstudio.ai/blog/on-device-ai-vs-cloud-ai-economics
- Comparing Cloud and On-Device Inference (Roboflow) — https://blog.roboflow.com/comparing-cloud-and-on-device-inference/

---

### Vorbehalte / Verifikations-Hinweise

- Kindwise „>73 % Top-3" und „548 Klassen" sind **Anbieter-Selbstauskunft**, kein unabhängiger Benchmark.
- Plantix „>780 Krankheiten" teils aus Drittquellen; exakte Zahl anbieterintern variabel; keine öffentlichen Preise.
- AgroBench-Zahl (73,45 %) und einige VLM-Werte stammen teils aus Such-Snippets/ResearchGate (PDF-Volltext nicht extrahierbar) — bei Zitation gegenprüfen.
- Eine kursierende „88 % Halluzinationsrate Gemini 3" stammt aus Marketing-Quelle und wurde als **nicht belastbar verworfen**.
- DPF-Rechtslage ist in Bewegung („Schrems III" möglich) — vor Produktiveinsatz aktuellen Stand prüfen.
- Lizenzstatus mehrerer HuggingFace-Modelle und von PlantVillage (CC0?) ist **nicht eindeutig** — vor kommerzieller Nutzung pro Artefakt verifizieren.
