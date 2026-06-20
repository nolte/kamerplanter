# Recherchebericht: Bildbasierte Schädlingserkennung bei Pflanzen

**Stand:** Juni 2026 (Recherche-Cutoff)
**Kontext:** Entscheidungsgrundlage für eine dedizierte Spec **REQ-044 (Schädlingserkennung)** in Kamerplanter — selbst-hostbar, datenschutzorientiert, Domänen: Zimmerpflanzen, Gemüse, Kräuter, Cannabis. Abgegrenzt vom allgemeinen Gesundheits-Assessment (REQ-043) und der CV-Pflanzendiagnose (REQ-038); liefert ein **Schädlings-Bild-Signal** in IPM (REQ-010) und Health-Fusion (REQ-043).
**Scope (mit Auftraggeber abgestimmt):** Zwei Erkennungsmodi — **(1)** Schädling direkt auf dem Foto (Insekten/Milben als Small-Object-Detektion) und **(2)** Schadbild/Symptom-Erkennung (Fraß-/Saugschäden, Gespinste, Honigtau, Verfärbungen). **Nicht** im Scope: Klebefallen-/Trap-Monitoring.
**Methode:** Fan-out-Web-Recherche über 6 Themen-Forks (Kategorien A–E), 28 Quellen gefetcht → 136 Claims extrahiert → 25 priorisiert → adversariale 3-Stimmen-Verifikation (2/3-Widerlegung killt) → 22 bestätigt, 3 widerlegt. Widerlegte Claims sind in §6 dokumentiert und werden **nicht** als Belege verwendet.

---

## 1. Executive Summary (Kernerkenntnisse)

1. **Direkte Schädlingserkennung (Modus 1) ist primär ein Small-Object-Detection-Problem — das ist der zentrale technische Engpass.** In realistischen In-the-wild-Benchmarks belegen Schädlinge nur **Bruchteile eines Prozents** der Bildfläche (AgriPest: Ø **0,16 %** vs. 7,74 % in MS COCO, 16,76 % in PASCAL VOC; Pest24 mehrheitlich < 0,4 %). Tiefe Detektoren übersehen so kleine Objekte systematisch. Genau Kamerplanters relevante Indoor-Schädlinge (Spinnmilben, Thripse, Trauermücken) sind winzig — die Modellwahl allein löst das nicht.

2. **Die realistisch erreichbare Genauigkeit ist moderat, nicht „gelöst".** Auf den maßgeblichen In-the-wild-Benchmarks erreichen Standard-Detektoren nur **~63–71 % mAP@0.5** (AgriPest: Cascade R-CNN 70,83 %, FPN 70,20 %, SSD512 63,38 %; Pest24-Originalstudie: YOLOv3 ~63,54 % als bester von vier). Auf AgriPest schlagen **zweistufige** Detektoren (Cascade R-CNN, FPN) die einstufigen. Das deckelt selbstgehostete Modus-1-Detektion klar unter Labor-Niveau.

3. **Der Lab-vs-Field-Reliability-Gap ist über alle Ansätze hinweg verbindlich einzuplanen.** State-of-the-Art-Klassifikatoren erreichen > 95 % auf kontrollierten Labordaten (einfacher Hintergrund), brechen im Feld aber drastisch ein. Konkretes kommerzielles Beispiel: **Kindwise crop.health 93 % Top-3 / 85 % Top-1 intern, aber nur 66 % Top-3 auf realen Twitter-Bildern.** → Kalibrierung, Abstention, Disclaimer und Human-in-the-Loop sind nicht optional, sondern konstitutiv.

4. **Schadbild-/Symptom-Erkennung (Modus 2) ist machbar, leidet aber am selben Klein-Objekt-Problem auf Canopy-Ebene — Image-Tiling/Slicing ist ein Pflicht-Baustein.** Symptomregionen erscheinen auf Gesamtpflanzen-Fotos klein; das Aufteilen des Bildes in Kacheln vor der Detektion ist eine etablierte, nachweislich wirksame Gegenmaßnahme. Modus 2 ist der pragmatischere Weg, *wenn das Insekt selbst nicht sichtbar ist* — aber kein Ersatz für die Differenzialdiagnose.

5. **Self-Hosting-First ist tragfähig, aber CPU-only-Inferenz großer Modelle ist unpraktikabel.** Open-Source-Assets (AgriPest, Pest24, IP102; ONNX-fähige Detektoren) tragen den Self-Hosted-Pfad. Aber große Modelle (YOLOv8l, RT-DETR-l) sind CPU-only auf Edge-Hardware (Raspberry Pi 5) wegen Multi-Sekunden-Latenz unbrauchbar. **Für Kamerplanters asynchronen Einzelfoto-Flow** (Celery) ist Multi-Sekunden-Latenz pro Bild jedoch akzeptabel — die 25-FPS-Video-Echtzeitschranke ist hier irrelevant. Schlüssel: **kleine/quantisierte ONNX-Modelle** + Tiling.

6. **Die vorhandenen Open-Source-Schädlingsdatensätze decken Kamerplanters Indoor-Saugschädlinge NICHT ab.** AgriPest (14 Arten) und Pest24 (24 Klassen) sind auf **Feldkulturen** (Weizen/Reis/Mais/Raps, Lichtfallen-Insekten) ausgerichtet. Für Spinnmilben, Thripse, Trauermücken, Schmierläuse, Weiße Fliege, Blattläuse ist ein **eigenes Indoor-Datenset bzw. eine Few-Shot-/Finetuning-Strategie** nötig.

7. **Cloud-Opt-in (Kindwise) ist ein sinnvolles Upgrade, aber mit unbelegter Indoor-Abdeckung.** Kindwise (EU-orientiert, DSGVO-beworben) bietet dedizierte APIs (plant.health, crop.health, insect.id), transparente Credit-Preise (€0,05 → €0,01/Call) und crop.health deckt 288 Krankheiten/Schädlinge (~180 Schädlinge) über 23 Kulturen ab. **Aber:** DSGVO-Konformität und Genauigkeitswerte sind Vendor-Selbstauskunft; insect.id ist als Biodiversitäts-Generalist (>14.000 Taxa) positioniert ohne nachgewiesene Spezialisierung auf die konkreten Indoor-Saugschädlinge.

8. **VLM/VLM+RAG taugt als Erklärungs-/Differenzierungs-Layer, nicht als primärer Klassifikator.** End-to-End-Pipelines (CLIP + Grounding DINO + SAM) sind konzeptionell für Erklärung und Schädling↔Nützling↔Krankheit↔Mangel-Differenzierung geeignet, brechen aber unter Domain-Shift dramatisch ein (CLIP-Zero-Shot bis **6,77 %** auf PlantDoc). → VLM als RAG-gestützter Triage-/Erklärungs-Layer, niemals als alleiniger Erkenner.

**Empfehlung in einem Satz:** Self-Hosted-First-Phasenstrategie — (Phase 1) ein **schadbild-/symptomorientierter** Vision-Adapter (Modus 2) mit Tiling als robuster Einstieg, der pragmatisch das liefert, was ohne sichtbares Insekt erkennbar ist, plus optionaler Kindwise-Cloud-Opt-in; (Phase 2) ein **kleiner, quantisierter, ONNX-basierter Direkt-Detektor** (Modus 1) mit Tiling, trainiert auf einem eigenen Indoor-Schädlings-Datenset via Few-Shot/Finetuning; (Querschnitt) RAG-(V)LM nur zur Erklärung, durchgängig kalibrierte Konfidenz mit Abstention, Human-in-the-Loop und Disclaimer — Einspeisung als Bild-Signal in IPM/Health, **nie** Auto-Treatment.

---

## 2. Detaillierte Befunde

Konfidenz-Markierung pro Befund: **[hoch]** = adversariale Verifikation 3-0 bestätigt, **[mittel]** = 2-1 bestätigt.

### A. Kommerzielle Cloud-APIs mit Schädlings-Fokus

#### Kindwise (relevanteste EU-orientierte Opt-in-Option) **[hoch]**

- **Produktpalette:** `plant.id`, `plant.health`, `insect.id`, `mushroom.id`, **`crop.health`**. Für Schädlingserkennung relevant: crop.health (Schadbild/Modus 2) und insect.id (direkte Insektenbestimmung/Modus 1).
- **crop.health:** deckt **288 Krankheiten/Schädlinge** ab (~180 Schädlinge, ~80 Pilz-, ~20 viral, ~20 bakteriell) über **23 Kulturen**; liefert pro Identifikation Symptome, Schweregrad, Repräsentativbilder und Behandlungshinweise → passend zu **Modus 2**. Interne Validierung **93 % Top-3 / 85 % Top-1**, aber nur **66 % Top-3 auf realen Twitter-Bildern** (Beleg für den Reliability-Gap).
- **insect.id:** deckt **> 14.000 Taxa** (Insekten + terrestrische Wirbellose inkl. Spinnen, Milben, Schnecken) ab, meldet **92 % Genauigkeit (Top-3)** — aber **[mittel, 2-1]** nur auf interner Validierung, nicht in-the-wild. Positionierung als **Biodiversitäts-/Generalisten-Tool** (Schmetterlinge, Spinnen, Käfer, Libellen, Schnecken), **keine** ausgewiesene Spezialisierung auf Spinnmilben, Thripse, Trauermücken, Blattläuse, Schmierläuse, Weiße Fliege → **Eignung für Kamerplanters Use-Case unbelegt**.
- **Preismodell:** kreditbasiert, 1 Credit/Call, volumengestaffelt von **€0,05 (1.000+)** bis **€0,01 (1.500.000+)** pro Credit.
- **Datenschutz:** bewirbt „GDPR-compliant and secure system" und „externally audited". **⚠️ Caveat:** Vendor-Selbstauskunft — AVV/DPA, garantiertes EU-Hosting und konkreter Serverstandort sind vor Produktiveinsatz separat vertraglich zu verifizieren.

#### Plantix (Sekundärquelle)

- B2B-API-Toolkit, sehr breite Krankheits-/Schädlingsabdeckung, aber crop-/acker-fokussiert (wenig Zimmerpflanzen), keine öffentlichen Preise, Vertrag erforderlich. Für Kamerplanters Indoor-Domäne nachrangig (konsistent mit dem REQ-043-Befund).

**Konsequenz für REQ-044:** Cloud-Opt-in über Kindwise als optionales Upgrade vorsehen (Adapter), aber die Indoor-Schädling-Abdeckung **vor produktivem Einsatz empirisch testen** und das AVV/EU-Hosting separat absichern.

### B. Open-Source-Modelle & Datensätze (Self-Hosting)

#### Datensätze **[hoch]**

| Datensatz | Größe | Klassen | Bedingungen | Domänen-Fokus | Eignung für Kamerplanter |
|---|---|---|---|---|---|
| **AgriPest** | 49,7K Bilder, 264,7K Bounding-Boxes | 14 Arten | in-the-wild, 7 J. Feld, expertenannotiert | Feldkulturen | small-object-Training, aber **falsche Arten** |
| **Pest24** | 25.378 Bilder, >190K Instanzen | 24 Klassen | in-the-wild, automatisierte Lichtfallen | Feldkulturen | small-object-Training, aber **falsche Arten** |
| **IP102** | ~75K Bilder | 102 Klassen | gemischt | Feldkulturen/Cash-Crops | breite Klassifikations-Baseline |

- **Zentrale Limitierung:** Alle drei sind **feldkultur-fokussiert** (Weizen/Reis/Mais/Raps). Kamerplanters Indoor-Saugschädlinge sind **nicht** abgedeckt → eigenes Indoor-Datenset oder Few-Shot/Finetuning zwingend (offene Frage §7).
- **Small-Object-Charakteristik [hoch]:** AgriPest-Schädlinge Ø 0,16 % Bildfläche; Pest24 mehrheitlich < 0,4 %. Tiefe Feature-Extraktionsnetze übersehen so kleine Objekte regelmäßig.

#### Detektor-Genauigkeit (In-the-wild-Baselines) **[hoch]**

- **AgriPest:** Cascade R-CNN **70,83 %** mAP@0.5 (best), FPN **70,20 %**, SSD512 **63,38 %**. Zweistufig > einstufig.
- **Pest24** (Originalstudie, 4 Detektoren): YOLOv3 **~63,54 %** mAP (höchster Wert).
- **⚠️ Zeitbezug:** Diese Zahlen sind ältere Baselines (2020/2021). Neuere YOLO11/RT-DETR/DINOv2-Ansätze *könnten* besser sein, sind hier aber **nicht robust belegt** (siehe §6 — zwei YOLO11/YOLO-NAS-Claims wurden 0-3 widerlegt). REQ-044 darf keine „>90 %"-Erwartung aus solchen Quellen kommunizieren.

#### Betrieb / Inferenz **[hoch]**

- CPU-only-Ausführung großer Modelle (YOLOv8l, RT-DETR-l) auf Raspberry Pi 5: Latenz von **mehreren Sekunden pro Frame** → für Video unpraktikabel; **keine** getestete Großmodell-Konfiguration erreichte die 25-FPS-Echtzeitschranke.
- **Aber für Kamerplanter entscheidend:** Der Use-Case ist **asynchrone Einzelfoto-Analyse** (Foto-Upload → Celery-Task), nicht Live-Video. Multi-Sekunden-Latenz pro Bild ist hier akzeptabel. → **kleine/quantisierte ONNX-Modelle** wählen, Inferenz asynchron via Celery; GPU optional als Beschleuniger.

### C. Multimodale VLMs / VLM+RAG (Erklärung & Differenzierung) **[hoch]**

- **End-to-End-Pipeline (Frontiers 2025):** CLIP (Zero-Shot-Klassifikation per Textprompt) + PaliGemma-2/Grounding DINO (Bounding-Box/Grounding) + SAM 2.1 (Segmentierung) → Diagnose + Schweregrad-Schätzung. Konzeptionell geeignet für Kamerplanters lokales **VLM+RAG zur Erklärung** und zur **Schädling↔Nützling↔Krankheit↔Mangel-Differenzierung**.
- **⚠️ Gravierender Vorbehalt:** Hohe Werte (98 %) gelten für **eine** Kultur (Dattelpalme, 9 Klassen, GAN-augmentiert). **CLIP-Zero-Shot bricht unter Domain-Shift dramatisch ein (bis 6,77 % auf PlantDoc)**; Grounding DINO ist für feinkörnige Insektenklassen unzureichend.
- **Architekturprinzip für REQ-044:** VLM als **Erklärungs-/Triage-Layer mit RAG** (nutzt die bestehende Wissensbasis REQ-031), **nicht** als zuverlässiger primärer Klassifikator. Konsistent mit dem REQ-043-Muster „Vision perzipiert → RAG-(V)LM erklärt".

### D. Wissenschaftlicher Stand (2023–2026)

- **Reliability-Gap (Lab → Feld) [hoch]:** Reviews dokumentieren > 95 % auf Lab-Daten (PlantVillage etc., abgelöste Blätter/einfacher Hintergrund), großer Domain-Gap im Feld (natürliches Licht, Hintergrundkomplexität, Wetter, saisonale Variation). → begründet die verbindlichen Anforderungen Kalibrierung/Abstention/Disclaimer/HITL.
- **Small-Object als konkrete Limitierung [hoch]:** kleinskalige Objekte/Läsionen werden von tiefen Netzen regelmäßig übersehen — gilt für Insekten (Modus 1) *und* kleine Symptomregionen (Modus 2).
- **Tiling als Gegenmaßnahme [hoch]:** Aufteilen großer Bilder in Kacheln mildert das Small-Object-Problem messbar (belegt an Canopy-Symptomerkennung). → Pflicht-Baustein für beide Modi.
- **Few-Shot für seltene Schädlinge:** als Strategie zur Schließung der Domänen-/Artenlücke gegenüber AgriPest/Pest24 angezeigt (offene Frage §7 — konkrete Strategie noch zu evaluieren).

### E. Datenschutz & Betrieb

- **EXIF/Metadaten:** Smartphone-Fotos betten GPS/Zeit/Gerät ein; GPS in EXIF ist personenbezogen. API-Uploads strippen EXIF **nicht** automatisch → **vor jeder Verarbeitung serverseitig strippen** (zusätzlich clientseitig), konsistent mit REQ-029 §5.4 und der REQ-043-Leitplanke.
- **On-Device/Self-Hosted vs. Cloud:** Self-Hosted → Daten verlassen das System nicht, kein Drittland-Transfer, kein AVV, keine Pro-Foto-Kosten, offline-fähig; Preis: eigener Betrieb + Modellqualität kleinerer Modelle. Cloud → stärkere/gepflegte Modelle, aber Upload an Dritt + AVV + ggf. Drittland + Consent. Empfohlenes Muster: **Self-Hosted Default, Cloud opt-in**.
- **ONNX Runtime:** etablierter Pfad für CPU/Edge-Inferenz; passt zur bestehenden REQ-029-A-Inferenz-Infrastruktur.

---

## 3. Vergleichstabelle der Hauptansätze

Bewertung: ●●● = stark/gut, ●● = mittel, ● = schwach/problematisch.

| Kriterium | **A: Cloud-API** (Kindwise crop.health/insect.id) | **B: Self-Hosted Direkt-Detektor** (Modus 1, ONNX-Detektor + Tiling) | **C: Self-Hosted Schadbild** (Modus 2, Symptom-Detektor + Tiling) | **D: VLM/VLM+RAG** (Erklärungs-Layer) |
|---|---|---|---|---|
| **Genauigkeit** | ●● intern 85–93 % Top-3, real ~66 % Top-3 | ●● ~63–71 % mAP in-the-wild (Feldkulturen-Baseline) | ●● machbar mit Tiling; enge Kultur-Belege | ● Zero-Shot bricht unter Domain-Shift ein (bis 6,77 %) |
| **Kosten** | ●● €0,01–0,05/Call, kein Eigen-Training | ●●● ~null/Inferenz nach Training | ●●● ~null/Inferenz nach Training | ●● GPU lokal / Token-Kosten Cloud |
| **Datenschutz/DSGVO** | ●● EU-beworben, aber Upload an Dritt + AVV nötig (Selbstauskunft) | ●●● Daten bleiben im System | ●●● Daten bleiben im System | lokal ●●● / Cloud ● |
| **Offline-Fähigkeit** | ● erfordert Konnektivität | ●●● voll offline (CPU genügt, async) | ●●● voll offline (CPU genügt, async) | lokal ●● (GPU) / Cloud ● |
| **Wartungsaufwand** | ●●● Anbieter wartet | ●● eigenes Training + Indoor-Datenset + Tiling-Pipeline | ●● eigenes Training + Tiling-Pipeline | ● GPU-Betrieb + RAG-Kopplung |
| **Erklärbarkeit** | ●● Symptome/Schweregrad/Treatment-Hinweise | ● Klassen + Box, ggf. Grad-CAM | ●● Symptom-Region lokalisiert | ●●● natürliche Sprache + RAG-Kontext |
| **Integrationsaufwand** | ●●● REST/JSON, sofort | ●● ONNX-Dienst + Tiling + Datenset | ●● ONNX-Dienst + Tiling | ● höchster (VLM + RAG-Pipeline) |
| **Abdeckung Indoor-Schädlinge** | ●● breit, aber Indoor-Eignung **unbelegt** | ● Datensätze decken Indoor-Arten **nicht** ab → eigenes Set nötig | ●● symptomorientiert, artenagnostischer | ●● breit per Wissen, aber unsicher |

**Lesart:** Kein einzelner Ansatz dominiert. Modus-2-Schadbild (C) ist der robusteste *artenagnostische* Einstieg, weil er nicht von der Sichtbarkeit winziger Insekten abhängt; Modus-1-Direkt-Detektion (B) ist wertvoller, aber datensatz-/trainingsintensiv; Cloud (A) liefert sofort Breite, aber mit unbelegter Indoor-Eignung und Datenschutz-Kosten; VLM (D) ist ausschließlich Erklärungs-Layer.

---

## 4. Lösungsempfehlung (begründete Phasen-Strategie, Self-Hosted-First)

Konsistent zur REQ-043-Phasenstrategie und zum Adapter-Muster. **Self-Hosted ist Default; Cloud ist opt-in.** Das Ergebnis ist immer ein **Schädlings-Bild-Signal** (konfidenz-gewichtet, mit Abstention und Disclaimer), das in IPM (REQ-010) und Health-Fusion (REQ-043) einspeist und **nie** automatisch ein Treatment auslöst oder das Karenz-Gate umgeht.

### Phase 1 — Robuster, artenagnostischer Einstieg: Schadbild-Adapter (Modus 2, self-hosted) + Cloud-Opt-in

- **Warum zuerst Modus 2:** Er hängt nicht von der Sichtbarkeit winziger Insekten ab, ist artenagnostischer und liefert auch dann ein Signal, wenn das Insekt nicht im Bild ist (Fraß-/Saugschäden, Gespinste, Honigtau, Verfärbung). Mit **Tiling/Slicing** als Pflicht-Baustein.
- **Cloud-Opt-in parallel:** `KindwiseHealthAdapter`-analoger `KindwisePestAdapter` (crop.health/insect.id) — **standardmäßig deaktiviert, einwilligungspflichtig** (Consent-Zweck, REQ-025), EXIF doppelt gestrippt, AVV/EU-Hosting vertraglich verifiziert. Liefert sofort breite Abdeckung ohne ML-Eigenbetrieb, mit dem Vorbehalt, die Indoor-Eignung empirisch zu testen.

### Phase 2 — Direkt-Detektor (Modus 1, self-hosted, das eigentliche Ziel)

1. **Modell:** kleiner, **quantisierter ONNX-Detektor** (YOLO-Familie/RT-DETR-tiny-Klasse) + **Tiling** auf hochauflösenden Uploads; asynchron via Celery (Multi-Sekunden-Latenz akzeptabel).
2. **Daten:** **eigenes Indoor-Schädlings-Datenset** für Spinnmilben, Thripse, Trauermücken, Schmierläuse, Weiße Fliege, Blattläuse — gespeist aus Nutzerbildern (mit Consent) + Few-Shot/Finetuning gegenüber AgriPest/Pest24/IP102-Backbones. AgriPest/Pest24 liefern small-object-Vortraining, **nicht** die Zielarten.
3. **Kalibrierung/Abstention:** wegen ~63–71 %-Decke und Reliability-Gap **kalibrierte Konfidenz + Abstention-Schwelle** zwingend; bei Unsicherheit „keine sichere Erkennung — bitte manuell prüfen" statt überkonfidenter Falschklasse.

### Querschnitt (für beide Phasen verbindlich)

- **VLM+RAG nur als Erklärungs-/Differenzierungs-Layer** (optional, GPU-abhängig, Graceful Degradation): erklärt den Befund in natürlicher Sprache, ordnet Treatment-Optionen aus der RAG-Wissensbasis (REQ-031) zu und unterstützt die **Schädling↔Nützling↔Krankheit↔Mangel-Differenzierung** — niemals als alleiniger Erkenner.
- **Human-in-the-Loop:** Nutzer-Feedback („Schädling bestätigt / falsch / war Nützling") als Trainings-/Adaptionssignal und zum Aufbau des Indoor-Datensets.
- **Differenzierung gegen Nützlinge:** explizit als Klasse/Abstention behandeln (Marienkäfer-Larve, Florfliege, Raubmilbe nicht als Schädling melden) — Verwechslungsgefahr ist real.
- **Einspeisung, kein Auto-Treatment:** Ergebnis erzeugt höchstens einen `suggested_next_step` (IPM-Inspektion vorschlagen), umgeht **nie** das Karenz-Gate (REQ-010).
- **Disclaimer-Pflicht** durchgängig; besonders bei Cannabis.

---

## 5. Konkrete Hinweise für die REQ-044-Implementierung

- **Adapter-Vertrag** analog REQ-043 `HealthVisionAdapter`: ein `PestDetectionAdapter` mit Methoden für beide Modi; Implementierungen `KindwisePestAdapter` (Cloud, `requires_consent`) und `LocalPestDetectorAdapter` (self-hosted, kein Consent).
- **Tiling-Pipeline** als wiederverwendbarer Vorverarbeitungs-Baustein (hochauflösendes Bild → Kacheln → Detektion pro Kachel → Box-Merge) — Pflicht für beide Modi.
- **Ergebnis-Schema:** Liste von `PestFinding` (label, category `pest|beneficial|symptom|unknown`, common_name, confidence, bounding_box optional, matched_pest_key gegen REQ-010, mode `direct|symptom`), plus `is_confident`/Abstention-Flag und Pflicht-`disclaimer`.
- **IPM-Brücke (REQ-010):** Findings gegen `pests`-Stammdaten mappen; bei Bestätigung Vorschlag „Inspektion anlegen" (REQ-010 `inspections`) — kein automatischer `treatment_application`.
- **Health-Fusion-Brücke (REQ-043):** Schädlings-Signal als Befall-Signal-Verstärker in die `HealthAssessmentEngine` einspeisen (erhöht `ipm`-Teilscore-Gewicht bei bestätigtem Befund).
- **Persistenz:** Bilddaten nicht dauerhaft speichern (nur Hash + Ergebnis); EXIF doppelt strippen; Retention nach NFR-011; Cloud-Calls im `ai_audit_log` (REQ-031) ohne Klartext-PII.
- **Default-Privacy:** `pest_detection_enabled=False`; lokaler Adapter Default, Cloud opt-in; Light-Modus blockiert mit Hinweis (braucht Pflanzen-Kontext, tenant-scoped).
- **Tests:** Abstention bei niedriger Konfidenz, Tiling-Korrektheit, Nützling-nicht-als-Schädling, Cloud-ohne-Consent → 403, Disclaimer-Invariante, kein Auto-Treatment.
- **Kommunikation:** keine „>90 %"-Erwartung in UI/Marketing; realistische ~60–70 %-Größenordnung intern, nach außen als „Einschätzung mit Unsicherheit".

---

## 6. Widerlegte Claims (NICHT als Beleg verwenden)

Adversariale Verifikation hat folgende Aussagen verworfen — sie dürfen in REQ-044 **nicht** zitiert werden:

| Widerlegte Aussage | Votum | Quelle |
|---|---|---|
| YOLO11/YOLO-NAS erkennen 4 Gewächshaus-Schädlinge (Thripse/Weiße Fliege) auf Artebene mit mAP@50 ≥ 90 % (YOLO11x 95 %) | **0-3** | frontiersin.org/…/fpls.2025.1668795 |
| Generalisierung auf externes Testset kostet nur 10–20 % (bester Wert YOLO-NAS-L mAP@50 89 %) | **0-3** | frontiersin.org/…/fpls.2025.1668795 |
| Rußtau auf Zitrus-Canopy via YOLOv7 mit 75,6 % mAP / 69,8 % Recall zuverlässig detektierbar | **1-2** | pmc.ncbi.nlm.nih.gov/articles/PMC10610784 |

Aus der dritten Quelle bleibt **nur** das übergeordnete Prinzip robust: Tiling/Slicing mildert das Small-Object-Problem; die konkrete YOLOv7-Genauigkeitszahl überlebte die Verifikation nicht.

---

## 7. Offene Fragen (vor Produktivnahme zu klären)

1. **Indoor-Datenset:** Welche konkreten Open-Source-Quellen/Modelle decken Spinnmilben, Thripse, Trauermücken, Schmierläuse, Weiße Fliege, Blattläuse ab — und welche Few-Shot-/Finetuning-Strategie schließt die Lücke gegenüber den feldkultur-fokussierten AgriPest/Pest24/IP102?
2. **Kindwise-Vertragslage:** Gibt es ein belastbares AVV/DPA mit garantiertem EU-Hosting und nachgewiesener In-the-wild-Genauigkeit speziell für Indoor-Houseplant-Schädlinge (nicht nur Feldkulturen)?
3. **Quantisierte ONNX-Variante:** Welche Modellfamilie/Input-Auflösung/Tiling-Strategie erreicht auf Kamerplanters Ziel-CPU eine akzeptable Genauigkeit/Latenz-Balance für asynchrone Einzelfoto-Analyse?
4. **Verwechslungsgefahr quantifizieren:** Wie sind Schädling↔Nützling↔Krankheit↔Nährstoffmangel-Verwechslungen einzuschätzen und wie müssen Abstention-Schwellen/Kalibrierung gesetzt werden, damit das Bild-Signal in REQ-043/REQ-010 einspeist, ohne falsch-positive Interventionen zu provozieren?

---

## 8. Quellenliste

### A. Kommerzielle Cloud-APIs
- Kindwise Pricing — https://www.kindwise.com/pricing
- Kindwise crop.health — https://www.kindwise.com/crop-health
- Kindwise insect.id — https://www.kindwise.com/insect-id
- Plantix API Toolkit — https://plantix.net/en/b2b-solutions/api-toolkit/

### B. Open-Source-Modelle & Datensätze
- AgriPest (MDPI Sensors 21/5/1601) — https://www.mdpi.com/1424-8220/21/5/1601
- Pest24 (ResearchGate) — https://www.researchgate.net/publication/342959457_Pest24_A_large-scale_very_small_object_data_set_of_agricultural_pests_for_multi-target_detection
- IP102 (GitHub) — https://github.com/xpwu95/IP102
- Edge-Latenz-Benchmark (Scientific Reports 2026) — https://www.nature.com/articles/s41598-026-46453-6
- YOLO11/YOLO-NAS Gewächshaus-Schädlinge (Frontiers 2025) — https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1668795/full ⚠️ (Claims 0-3 widerlegt, siehe §6)

### C. VLMs / VLM+RAG
- CLIP+Grounding DINO+SAM Pipeline (Frontiers 2025) — https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1710188/full
- VLM/Generative Agri-Pipeline (ScienceDirect) — https://www.sciencedirect.com/science/article/pii/S2643651525001670
- Multimodal RAG Crop Disease (arXiv 2506.03168) — https://arxiv.org/pdf/2506.03168
- RAG-augmented Detection (arXiv 2505.21544) — https://arxiv.org/pdf/2505.21544
- Agentic Multimodal RAG (ReadyTensor) — https://app.readytensor.ai/publications/agentic-ai-for-smart-agriculture-a-multimodal-rag-system-for-crop-disease-detection-diagnosis-mLRSML10lEYd

### D. Wissenschaftlicher Stand
- Small-Object/Reliability-Gap Review (PMC11885274) — https://pmc.ncbi.nlm.nih.gov/articles/PMC11885274/
- Tiling/Canopy-Symptom (PMC10610784) — https://pmc.ncbi.nlm.nih.gov/articles/PMC10610784/ ⚠️ (YOLOv7-Zahl 1-2 widerlegt, nur Tiling-Prinzip robust)
- Symptom-Erkennung (Nature Sci Rep) — https://www.nature.com/articles/s41598-025-01908-0
- Domain-Gap Studie (ScienceDirect S0168169925008816) — https://www.sciencedirect.com/science/article/abs/pii/S0168169925008816
- Pest-Detection Review (ScienceDirect S0261219424004216) — https://www.sciencedirect.com/science/article/abs/pii/S0261219424004216
- Pest-Klassifikation (PMC9910215) — https://pmc.ncbi.nlm.nih.gov/articles/PMC9910215/

### E. Datenschutz & Betrieb
- ONNX Runtime IoT/Edge — https://onnxruntime.ai/docs/tutorials/iot-edge/
- ONNX Benchmarking (Arm Learn) — https://learn.arm.com/learning-paths/servers-and-cloud-computing/onnx-on-azure/benchmarking/
- EXIF-Daten-Risiken (Mochify 2026) — https://mochify.xyz/guides/exif-data-risks-image-compression-2026

---

### Vorbehalte / Verifikations-Hinweise

- **Benchmark-Zeitbezug:** AgriPest/Pest24-Zahlen (2020/2021) sind feste Datensatz-Statistiken (gültig), die Detektor-Genauigkeiten markieren aber ältere Baselines. Neuere Architekturen könnten besser sein — in dieser Recherche jedoch **nicht robust belegt** (zwei YOLO11/YOLO-NAS-Claims 0-3 widerlegt, §6).
- **Vendor-Aussagen (Kindwise):** DSGVO-Konformität, „externally audited", 92 %/85 % Genauigkeit sind Marketing-/Produktseiten-Selbstauskünfte — kein unabhängiger Beleg für In-the-wild-Performance, EU-Hosting, AVV/DPA oder Indoor-Schädling-Abdeckung.
- **Modus-2-Evidenz:** stützt sich teils auf Einzelquellen (Tiling: PMC10610784; VLM: Frontiers 2025) und enge Kulturen (Zitrus, Dattelpalme) — Generalisierbarkeit auf Zimmerpflanzen/Cannabis nicht direkt belegt.
- **Edge-Latenz:** Benchmark zielt auf 25-FPS-Video; für Kamerplanters asynchronen Einzelfoto-Flow nur teilweise relevant, Kernaussage (große Modelle CPU-only unpraktikabel) bleibt gültig.
