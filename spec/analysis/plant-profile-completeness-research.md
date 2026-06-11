# Pflanzensteckbrief — Vollständigkeits-Recherche

> **Frage:** Welche Informationen muss ein professioneller Pflanzen-Steckbrief zusätzlich
> erfassen, um vollständige Pflanzenpflege unter **unterschiedlichen Umgebungsbedingungen**
> (Indoor, Growzelt/Cannabis, Hydro/Coco/Soil, Gewächshaus, Freiland, Balkon/Kübel,
> Klimazonen, Lichtregime) zu ermöglichen?
> **Methodik:** Deep-Research-Harness — 5 Suchwinkel, 24 Quellen gefetcht, 100 Aussagen
> extrahiert, 25 adversarial verifiziert (3-Stimmen, 2/3-Refute-Schwelle) → 22 bestätigt, 3 widerlegt.
> **Erstellt:** 2026-06-11
> **Status:** Recherchebefund (kein REQ-Entscheid) — Grundlage für Feld-Ergänzungen in REQ-001/003/004
> **Bezug:** Ergänzt die vorausgehende Steckbrief-Lücken-Analyse (Datenmodell-Abgleich gegen Generator-Vorlage)

---

## 1. Kernbefund

Der heutige Steckbrief deckt die **Stammdaten und Phasen-Zielwerte** (PPFD, Photoperiode,
Temp, rF, VPD, CO₂, NPK, EC, pH, Ca/Mg/S/Fe/B) gut ab. Für **professionelle Pflege über
alle Umgebungen** fehlt eine **physiologische Steuer-Schicht**, die heute komplett fehlt.
Die Recherche identifiziert vier Feld-Gruppen:

1. **Licht** — DLI (ableitbar), Lichtkompensationspunkt (LCP), Far-Red-Fraction/Shade-Trait
2. **Wasser/Wurzel-Physik** — umweltabhängige Wurzeltiefe, Staunässe-/Oxygen-Stress-Toleranz
3. **Mikroklima/Physiologie** — T_opt der Photosynthese, artspezifische VPD-Schwelle, Salztoleranz, C3/C4-Typ
4. **Substrat/Nährstoff** — Mikronährstoffe Mn/Zn/Cu/Mo + pH-gegatete Bioverfügbarkeit

---

## 2. Priorisierte Parameter

### 2.1 MUST-HAVE

| # | Parameter | Einheit / Wertebereich | Ermöglicht (Pflege-/Automatisierungs-Entscheidung) | Umgebung | KA-Modell (Vorschlag) | Konfidenz |
|---|---|---|---|---|---|---|
| M1 | **DLI-Zielwert** | mol·m⁻²·d⁻¹; abgeleitet `DLI = PPFD × 3600 × h / 1e6` | Tageslicht-Budget statt Momentan-PPFD; Lichtampel je Standort. **Kein neuer Sensor** — reine Ableitung. | alle | `RequirementProfile.dli_target_mol` | hoch (3-0) |
| M2 | **Lichtkompensationspunkt (LCP)** | PPFD-**Range** µmol·m⁻²·s⁻¹ (z.B. *Ficus* 6–17, Indoor generell 10–15) | Standort-Eignungscheck/Warnung „Platz zu dunkel"; verfügbares Licht muss LCP unter Sommer-Worst-Case übersteigen (~20 % Puffer über 12 h). „Wichtigster physiologischer Parameter" für Schattenplatzierung. | Indoor/Zimmerpflanze, Balkon/Kübel | `Species.light_compensation_point_ppfd_min/max` | hoch (3-0) |
| M3 | **Artspezifische VPD-Schwelle / Stomata-Sensitivität** | kPa-Schwelle + Sensitivitäts-Slope, je Phase | Echte VPD-Automatik statt globalem Zielwert; Crop-Steering-Trigger; verhindert Carbon-Starvation/hydraulisches Versagen | Growzelt, Gewächshaus, Indoor | `RequirementProfile.vpd_threshold_kpa` | hoch (3-0) |
| M4 | **Effektive Wurzeltiefe + Staunässe-/Oxygen-Stress-Toleranz** | Tiefe cm (**umweltabhängig**, nicht fix) + Trait-Enum | Bewässerungstiefe, Crop-Steering, Drainage-Bedarf; Push-Pull aus Infiltration (oben) und Grundwasser (unten) | Freiland, Kübel, Hydro/Coco | `Species.effective_root_depth_cm`, `Species.waterlogging_tolerance` | hoch (3-0) |

### 2.2 SHOULD-HAVE

| # | Parameter | Einheit / Wertebereich | Ermöglicht | Umgebung | KA-Modell (Vorschlag) | Konfidenz |
|---|---|---|---|---|---|---|
| S1 | **Far-Red-Fraction** `FR/(R+FR)` (0–1) + **Shade-Tolerance-Trait** | dimensionslos 0–1 (besser als R:FR, das unter LED → ∞) + Enum | Morphologie-/Blütesteuerung: Streckung, Blattflächen-Expansion, Shade-Avoidance | Growzelt/LED, Gewächshaus, Mischlicht | `RequirementProfile.far_red_fraction`, `Species.shade_tolerance` | hoch (3-0) |
| S2 | **Photosynthetisches Temperaturoptimum T_opt** | °C (**akklimatisationsplastisch**), je Phase | Klimasteuerung getrennt von generischen Tag/Nacht-Zielen; max. Photosyntheserate | Growzelt, Gewächshaus, Indoor | `RequirementProfile.photosynthesis_temp_opt_c` | hoch (3-0) |
| S3 | **Salztoleranz (Maas-Hoffman)** | ECe-Threshold dS/m + Slope %/dS/m + 4-Klassen-Enum (S/MS/MT/T); `Yr = 100 − b(ECe − a)` | Art-individuelle EC-Grenze statt globalem Ziel-EC; Leitungswasser-/Düngesalz-Toleranz; Versalzungs-Warnung | Freiland-Boden, Hydro/Coco, Kübel | `Species.salt_tolerance_ece_threshold/_slope/_class` | hoch (3-0) |
| S4 | **Mikronährstoffe Mn, Zn, Cu, Mo** (ggf. Cl, Ni) + **Boden-pH-Präferenz als Verfügbarkeits-Gate** | ppm/mg·l⁻¹ je Element + pH-Range | Mangel-Vorhersage/Düngeempfehlung **gegated durch pH** (meiste Mikros bei pH 6,0–6,5 verfügbar; Mo umgekehrt) | Freiland, Coco/Soil, Hydro, Kübel | `NutrientProfile.manganese/zinc/copper/molybdenum_ppm`; `Species.soil_ph_pref_min/max` | hoch (3-0) |
| S5 | **Photosynthesetyp C3/C4** ⚠️ | Enum (C3/C4/CAM) | WUE-/Transpirations-**Modifikator** für VPD/Bewässerung — **nicht** als Hauptsteuergröße (siehe §3) | VPD-/Klimasteuerung | `Species.photosynthesis_type` | mittel (split) |
| S6 | **Cannabis Post-Harvest: getrennte Trocknung vs. Curing** | je Temp °C / rF % / Dauer d (Trocknung 18–21 °C/50–55 %; Curing 18 °C/60 %/14 d) | Automatisierbare Trockenraum-/Curing-Ziele | Growzelt/Cannabis | neues Post-Harvest-Profil (REQ-008) | hoch/mittel |

### 2.3 NICE-TO-HAVE / aus Vorab-Analyse bestätigt

Die vorherige Datenmodell-Analyse bleibt gültig und wird fachlich gestützt; ergänzend zu
erfassen (niedrigere Priorität bzw. bereits dort dokumentiert): **Vernalisation/Kältebedürfnis,
kritische Tageslänge, Dormanz-Bedarf, GDD-Basistemperatur, Bestäubung/Selbstfruchtbarkeit/
Befruchtersorte, Lebensdauer & Ernte/Blüte-ab-Jahr, pH-Effekt von Düngern, PSA bei Pflanzenschutz.**

---

## 3. ⚠️ Adversarial WIDERLEGT — nicht ins Datenmodell-Rationale übernehmen

| Widerlegte Aussage | Vote | Konsequenz |
|---|---|---|
| Crop-funktionsspezifische **DLI-Zielzahlen** (Fruchtgemüse 20–30, Kräuter 15–25 …) | 0:3 | Das **Feld DLI bleibt valide**, aber diese konkreten Artzahlen sind aus der Quelle nicht gedeckt → eigene art-/phasenspezifische Recherche nötig. |
| **C3/C4/CAM** determiniert fundamental die Klima-/VPD-Automation-Defaults | 1:2 | Typ nur als **Modifikator** speichern, nicht als Hauptsteuergröße. |
| Cannabis Ziel-**Restfeuchte ~11 %** / Wasseraktivität <0,3 als Lagerqualitätsfeld | 0:3 | Felder konzeptionell plausibel, diese **Zielzahlen nicht belegt**. |

---

## 4. Modellierungs-Hinweise

- **Plastizität:** `LCP`, `T_opt` und `effective_root_depth` sind akklimatisations-/umwelt­abhängig —
  **keine festen taxonomischen Konstanten.** Als **Range** oder umweltabhängige Funktion modellieren,
  idealerweise kalibrierbarer Default + adaptives Lernen (analog bestehender Care-Reminder-Lernmechanismus).
- **DLI** ist berechnet, nicht erhoben — als abgeleitetes Zielfeld/`computed` implementieren.
- **Far-Red-Fraction** dem R:FR-Verhältnis vorziehen (unter LED ist R:FR unbrauchbar, FR-Fraction bleibt 0–1 begrenzt).
- Mehrere Feld-Schlüsse sind **Engineering-Inferenzen** aus belegter Physiologie (nicht wörtliche
  Quellenaussagen) — physiologisch fundiert, aber als Hypothese für die Produktentscheidung zu behandeln.

---

## 5. Offene Fragen (Folge-Recherche)

1. **CAM-Pflanzen** (Sukkulenten, Orchideen, viele Zimmerpflanzen): nächtliche Stomata-Öffnung =
   invertierte VPD-Logik. Hochrelevant für Indoor, in dieser Runde nur am Rand berührt.
2. Belastbare **artspezifische DLI-Zielwerte** je Kultur/Phase (der pauschale Range wurde widerlegt).
3. **Lux↔PPFD-Umrechnung** für Casual-User mit Smartphone-/Lux-Sensoren (knüpft an N-001 an).
4. Datenmodell-Pattern für **plastische Felder** (Range vs. Funktion vs. adaptiver Default).

---

## 6. Quellen (verifizierte Findings)

- Virginia Tech Extension SPES-720 (DLI-Formel) · Wikipedia Daily Light Integral
- Frontiers Plant Sci 2023 (LCP, fpls.1271341) · PMC10582628
- ASHS JASHS 146(1) Kusuma & Bugbee 2021 (Far-Red-Fraction) · php.70098 · PMC5591575
- PNAS 2017 Fan et al. (Wurzeltiefe, pnas.1712381114) · Frontiers Plant Sci 2022 (fpls.1085409)
- Springer Photosynth. Res. 2014 Yamori/Hikosaka/Way (T_opt, s11120-013-9874-6) · PMC10869619
- New Phytologist 2020 Grossiord et al. Tansley Review (VPD-Schwelle, nph.16485) · Frontiers fpls.646144
- FAO Irrigation & Drainage Paper 29 (Maas-Hoffman) · Wikipedia Maas-Hoffman / Salt tolerance of crops
- MSU Extension Micronutrients · UF/IFAS HS1207 (Mikronährstoffe/pH)
- Molecules 2022 PMC8911901 (Cannabis Trocknung/Curing) · KSRE MF1175 (Reifeindikatoren) · edrosenthal (Trichom-Reife)

**Statistik:** 5 Winkel · 24 Quellen · 100 Aussagen · 25 verifiziert · 22 bestätigt · 3 widerlegt · 10 nach Synthese · 106 Agenten.
