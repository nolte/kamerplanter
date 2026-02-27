# Agrobiology-Review — Gesamtübersicht

> **Datum:** 2026-02-27
> **Reviewer:** Agrarbiologie-Experte (KI-Subagent, Fokus Indoor/Zimmerpflanzen/Hydroponik)
> **Status:** Alle Findings behoben (4 Commits: `915f9caf`, `97d9b294`, `8a0ee11c`, `abd6bc19`)

---

## 1. Review-Umfang

| # | Review-Datei | Geprüfte REQs | Analysierte Version |
|---|---|---|---|
| 1 | `agrobiology-review.md` | REQ-001–022 (Querschnitt) | Diverse |
| 2 | `agrobiology-review-REQ-005.md` | REQ-005 Hybrid-Sensorik | v2.0 → v2.2 |
| 3 | `agrobiology-review-REQ-006.md` | REQ-006 Aufgabenplanung | v2.0 → v2.2 |
| 4 | `agrobiology-review-REQ-007.md` | REQ-007 Erntemanagement | v2.0 → v2.2 |
| 5 | `agrobiology-review-REQ-008.md` | REQ-008 Post-Harvest | v2.0 → v2.2 |
| 6 | `agrobiology-review-REQ-014.md` | REQ-014 Tankmanagement | v1.0 → v1.2 |
| 7 | `agrobiology-review-REQ-017.md` | REQ-017 Vermehrungsmanagement | v1.0 → v1.2 |
| 8 | `agrobiology-review-REQ-020-021.md` | REQ-020/021, UI-NFR-011 | v1 → v2 Re-Review |
| 9 | `agrobiology-review-REQ-022.md` | REQ-022 Pflegeerinnerungen | v1.0 → v2.1 |

---

## 2. Bewertungen je Review

### Querschnitt-Review (alle REQs)

| Dimension | Bewertung |
|---|---|
| Fachliche Korrektheit | 4/5 |
| Indoor-Vollständigkeit | 5/5 |
| Zimmerpflanzen-Abdeckung | 4/5 |
| Hydroponik-Tiefe | 5/5 |
| Messbarkeit der Parameter | 5/5 |
| Praktische Umsetzbarkeit | 4/5 |

### Per-REQ Bewertungen

| Dimension | REQ-005 | REQ-006 | REQ-007 | REQ-008 | REQ-014 | REQ-017 | REQ-022 |
|---|---|---|---|---|---|---|---|
| Fachliche Korrektheit | 4/5 | 4/5 | 4/5 | 3/5 | 4/5 | 4/5 | 4/5 |
| Indoor-Vollständigkeit | 3/5 | 4/5 | 4/5 | 3/5 | — | 4/5 | 3/5 |
| Zimmerpflanzen-Abdeckung | 2/5 | 1/5 | — | — | — | 2/5 | 3/5 |
| Hydroponik-Tiefe | 4/5 | 2/5 | 4/5 | 1/5 | 5/5 | 3/5 | — |
| Messbarkeit der Parameter | 4/5 | 4/5 | 4/5 | 4/5 | 5/5 | 4/5 | 4/5 |
| Praktische Umsetzbarkeit | 4/5 | 4/5 | 4/5 | 3/5 | 4/5 | 4/5 | 4/5 |

### REQ-020/021 (v1 → v2 Verbesserung)

| Dimension | v1 | v2 |
|---|---|---|
| Fachliche Korrektheit | 4/5 | 5/5 |
| Starter-Kit-Qualität | 3/5 | 4/5 |
| Glossar-Korrektheit | 4/5 | 5/5 |
| Feld-Sichtbarkeitslogik | 4/5 | 5/5 |
| Default-Werte-Qualität | 3/5 | 5/5 |
| Glossar-Vollständigkeit | 3/5 | 5/5 |

---

## 3. Findings-Statistik

### Gesamtzahlen

| Kategorie | Beschreibung | Anzahl | Status |
|---|---|---|---|
| **F** | Fachlich falsch | 38 | ✅ Alle behoben |
| **U** | Unvollständig | 60 | ✅ Alle behoben |
| **P** | Unpräzise | 42 | ✅ Alle behoben |
| **K** | Konsistenz | 3 | ✅ Alle behoben |
| **H** | Positiv/Hinweise | 40 | ℹ️ Informativ |
| **Gesamt** | | **183** | **143 behoben, 40 informativ** |

### Findings je Review-Datei

| Review | F | U | P | K | H | Gesamt |
|---|---|---|---|---|---|---|
| Querschnitt | 5 | 8 | 6 | 3 | 8 | 30 |
| REQ-005 | 3 | 8 | 6 | — | 7 | 24 |
| REQ-006 | 4 | 8 | 5 | — | 5 | 22 |
| REQ-007 | 6 | 7 | 6 | — | 7 | 26 |
| REQ-008 | 6 | 8 | 5 | — | 5 | 24 |
| REQ-014 | 3 | 6 | 5 | — | 5 | 19 |
| REQ-017 | 4 | 8 | 4 | — | 5 | 21 |
| REQ-020/021 | 5 | 11 | 11 | — | 4 | 31 |
| REQ-022 | 5 | 5 | 3 | — | 5 | 18 |
| **Summe** | **41** | **69** | **51** | **3** | **51** | **215** |

> Hinweis: Die Gesamtsumme (215) weicht von der deduplizierten Zählung (183) ab, da einige Findings file-übergreifend doppelt erfasst sind (z.B. F-003 Basilikum in Querschnitt + REQ-017 + REQ-020).

### Schweregrad-Verteilung (F/U/P/K ohne H)

| Schweregrad | Anzahl | Beispiele |
|---|---|---|
| **Critical** | 2 | REQ-022 F-001 (saisonale Gießintervalle), F-002 (herb-Preset) |
| **High** | 47 | VPD-Werte, Karenzzeit-Gates, Taxonomie, EC-Bereiche |
| **Medium** | 67 | Spektrum-Parameter, Templates, Fermentationsdetails |
| **Low** | 27 | Allergenpotenzial, Mondkalender, Inzuchtkoeffizient |

---

## 4. Wiederkehrende Themen

### 4.1 Zimmerpflanzen-Lücke (6 REQs betroffen)
Das Projekt heißt „Kamerplanter" (Zimmerpflanzen), aber die frühen Specs waren Cannabis-/Nutzpflanzen-zentriert. Behoben durch:
- 6 neue Vermehrungsmethoden (Blattsteckling, Offset, Luftschicht etc.) → REQ-017
- 4 Zimmerpflanzen-Workflow-Templates (Umtopf, Überwinterung etc.) → REQ-006
- Gießmethode + Wasserqualitäts-Hinweise → REQ-022
- DLI-Zielwerte für Zimmerpflanzen → REQ-005
- Zimmerpflanzen-Substrate (Orchideenrinde, Pon, Sphagnum) → REQ-019

### 4.2 Saisonale Differenzierung (3 REQs betroffen)
Feste Parameter ohne Sommer/Winter-Anpassung:
- `winter_watering_multiplier` ergänzt → REQ-022
- Hemisphären-Abhängigkeit dokumentiert → Querschnitt
- PhaseAlertProfile für dynamische Schwellwerte → REQ-005

### 4.3 Karenzzeit-Integration (2 REQs betroffen)
REQ-010 IPM-Sicherheitsintervalle fehlten als Gate vor Ernte und Nacherntebehandlung:
- Karenz-Gate in REQ-007 Ernte-Workflow → behoben
- REQ-010 als Dependency in REQ-008 → behoben

### 4.4 Single Source of Truth (3 Konsistenz-Findings)
- K-001: VPD-Werte in CLAUDE.md vs. REQ-003/018 → CLAUDE.md korrigiert
- K-002: Flushing-Dauern in REQ-004/007 → REQ-004 als einzige Quelle
- K-003: WateringEvent/FeedingEvent Überlappung → Abgrenzung dokumentiert

### 4.5 Hydroponik-Spezifika (REQ-005, REQ-014)
- EC-Bereich 0–5 → 0–15 mS/cm für Ablaufwasser
- DO, ORP, water_temp, flow_rate als Sensorparameter
- Differenzierte Kalibrierungsintervalle nach Tanktyp
- Chloramin vs. freies Chlor unterschieden

---

## 5. Wichtigste Korrekturen (Top 10)

| # | Finding | REQ | Severity | Korrektur |
|---|---|---|---|---|
| 1 | Feste Gießintervalle ohne Saison | REQ-022 F-001 | Critical | `winter_watering_multiplier` + saisonale Anpassung |
| 2 | herb-Preset mischt inkompatible Pflanzen | REQ-022 F-002 | Critical | Trennung `herb_tropical` / `herb_mediterranean` |
| 3 | VPD 0.4–0.8 kPa Blüte = Botrytis-Risiko | Querschnitt F-004 | High | Korrektur auf 0.8–1.4 kPa artspezifisch |
| 4 | Basilikum ≠ Kurztagspflanze | Querschnitt F-001 | High | Taxonomische Korrektur in REQ-001 |
| 5 | Karenzzeit-Prüfung vor Ernte fehlte | REQ-007 U-001 | High | `KarenzViolationError` als Gate-Condition |
| 6 | EC-Validierung 0–5 zu eng | REQ-005 F-001 | High | Erweiterung auf 0–15 mS/cm |
| 7 | Genetische Drift ≠ klonale Mutation | REQ-017 F-001 | High | Terminologie: somatische Mutation + epigenetische Drift |
| 8 | Chloramin ≠ freies Chlor | REQ-014 F-003 | High | Ascorbinsäure/Aktivkohle statt „24h stehen lassen" |
| 9 | Cannabis Slow-Dry 60–65% → 75–80% | REQ-008 F-004 | High | Prosa-Wert an Code-Wert angeglichen |
| 10 | Aspergillus-Differenzierung fehlte | REQ-008 U-004 | High | niger/flavus/fumigatus mit Mykotoxin-Warnungen |

---

## 6. Positive Erkenntnisse (H-Findings Highlights)

Der Review identifizierte 40 positiv bewertete Aspekte. Die bemerkenswertesten:

| Finding | REQ | Beschreibung |
|---|---|---|
| H-001 | Querschnitt | VPD als gekoppelter Regelkreis (Temp + rH) in REQ-018 ist lehrbuchkonform |
| H-002 | Querschnitt | CO₂-PPFD-Kopplung korrekt nach Liebigs Minimumgesetz |
| H-005 | Querschnitt | CEC-Integration in Spülberechnung (REQ-019) — selten und fachlich herausragend |
| H-008 | Querschnitt | Veredelungskompatibilität mehrstufig (explizite Edges vor Taxonomie-Heuristik) |
| H-001 | REQ-007 | Flushing-Evidenz korrekt eingeordnet (Uni Guelph 2020) |
| H-002 | REQ-007 | Ethylen-Reiferklassifikation fachlich fundiert und selten in Garten-Apps |
| H-003 | REQ-014 | Chlor-Warnung bei biologischen Additiven (Mykorrhiza/Trichoderma) |
| H-001 | REQ-006 | Cannabis-Hermaphroditismus als HST-Risiko hervorragend modelliert |

---

## 7. Behebungs-Chronologie

| Commit | Beschreibung | Findings |
|---|---|---|
| `915f9caf` | Querschnitt-Review: F, U, P über 9 REQ-Specs | ~22 Findings |
| `97d9b294` | Konsistenz-Findings K-002, K-003 | 2 Findings |
| `0a065246` | REQ-022 Konsistenz-Check (9 Cross-REQ-Inkonsistenzen) | 9 Findings |
| `8a0ee11c` | Per-REQ F-Findings (Fachfehler) | ~26 Findings |
| `abd6bc19` | Per-REQ U/P-Findings (Unvollständig/Unpräzise) | ~64 Findings |
| `92858bbf` | Review-Dateien als [BEHOBEN] markiert | Dokumentation |

---

## 8. Verbleibende Implementierungslücken

Die Spec-Ebene ist vollständig. Folgende **Implementierungsaufgaben** ergeben sich:

| Bereich | Beschreibung | Quelle |
|---|---|---|
| Seed-Daten | 7 fehlende botanische Familien, 18 fehlende Species für Starter-Kits | REQ-020 U-001 |
| TimescaleDB | Downsampling-Strategie, Continuous Aggregates, DLI-Berechnung | REQ-005 U-007 |
| REQ-008 | Post-Harvest komplett (Batch-State-Machine, Trim, CO₂-Monitoring) | Noch nicht implementiert |
| REQ-005 | Sensor-Integration (PhaseAlertProfile, Lichtspektrum) | Noch nicht implementiert |
| REQ-017 | Zimmerpflanzen-Vermehrung (6 neue Methoden, IPM-Integration) | Noch nicht implementiert |
| REQ-022 | Pflegeerinnerungen (saisonale Anpassung, Gießmethode, Humidity-Check) | Noch nicht implementiert |
