# Agrarbiologisches Review REQ-053 v1.1 (Grafische Garten- und Beetplanung)

**Datum:** 2026-10-04 · **Reviewer:** `agrobiology-requirements-reviewer` (read-only; Bericht vom Aufrufer abgelegt) · **Prüfumfang:** REQ-053 §§1–16, 20, 29, Teile von 30; REQ-001 §2, REQ-002 (Rotation), REQ-004 §1, REQ-037; Seed-Schemas `species.schema.yaml`, `_defs.schema.yaml`, `plant_info.schema.yaml`, `botanical_families.schema.yaml`. REQ-013 und REQ-028 nicht neu gelesen.

**Belegstand:** Befunde, die direkt in Spec oder Schema nachgemessen wurden, sind als **[belegt-intern]** markiert. Agronomische Aussagen ohne externe Quellenprüfung stehen mit ⚠️ in der Tabelle R-001 ff. am Ende.

**Einarbeitung (Stand REQ-053 v1.2, 2026-10-04):**

| Befund | Status | Wo |
|--------|--------|----|
| K-001 | eingearbeitet — Betreiber hat O-07 revidiert | §16.3 GP-FR-138/139, GP-ACC-049 |
| K-002, K-003 | eingearbeitet | §15.1 (`soil_texture`, `growing_medium_kind`, `conditions[]`, `target_ph` abgeleitet) |
| K-004 | eingearbeitet | GP-FR-131 (`rotation_pause_years`, Obergrenze 8) |
| W-001 | eingearbeitet | GP-FR-061 nutzt vorhandene Schemafelder |
| W-002, W-003, W-004, W-005 | eingearbeitet | §11.1, GP-FR-060/062/073, `trellis`, `depth_kind`, `sowing_spacing_cm` |
| W-006, W-007 | eingearbeitet (Enum-Wert `ausgeizen` bleibt, Anzeigename geändert) | §12.1 |
| W-008 | eingearbeitet | R-7.2, GP-FR-080 |
| W-009, W-010, W-011, W-012 | eingearbeitet | §15.1, GP-FR-125 |
| W-013 | eingearbeitet | GP-FR-131/135/137, `rotation_exempt` |
| W-014 | eingearbeitet — Betreiberentscheid | §7.4 (`season_state` abgeleitet) |
| W-015 | eingearbeitet | §11.3 (`sown`, in Ernte, ausgefallen) |
| W-016 | 1, 5, 8 eingearbeitet (MVP); 2, 3, 6 als SHOULD; 4, 7 als Regel | §9.2a, Issue 63 |
| W-017, W-018 | eingearbeitet | GP-FR-113/114/119/130, Issue 64 |
| H-001…H-007 | H-002/H-006 eingearbeitet; Rest als Bündel-Notiz | §15.1, §29, Anhang A |
| §29-Felder | 1–8 eingearbeitet (optional/SHOULD); 9/10 bestätigt | §9.5, §29 |
| R-001…R-013 | **offen** — Recherche vor Welle 3 (Issue 2 Folge) | — |


## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|---|---|---|
| Fachliche Korrektheit | ⭐⭐⭐ | Grundstruktur tragfähig. `FeederLevel` (§16.3), `soil_type`/`condition` (§15.1) und die Nachbarschaftsregel haben echte Modellfehler. |
| Freiland/Beet-Vollständigkeit | ⭐⭐⭐ | Endgröße, Reihenrichtung, Hochbeet-Anlagejahr, Anbaupausen und Dauerkulturen fehlen. |
| Zimmerpflanzen/Zelt | ⭐⭐ | O-01 ist modelltechnisch elegant, ignoriert aber Licht-Hotspot, Topfvolumen, Etagen und gemeinsame Photoperiode. |
| Messbarkeit | ⭐⭐⭐ | Meist messbar. `pH` ohne Methode, Nährstoffeinheit mg/L und `sun_exposure` ohne Stundenschwellen sind es nicht. |
| Schema-Spec-Konsistenz | ⭐⭐ | GP-FR-061 dupliziert vorhandene Schemafelder. Das Zehrer-Enum würde `nitrogen_fixing` doppeln. |

**Go/No-go:** Bedingtes PASS. K-001 bis K-004 vor Umsetzung der Wellen 0/1 korrigieren.

---

## 🔴 Kritisch

### K-001: `FeederLevel` mischt zwei Achsen (GP-FR-138, §16.3)
`nitrogen_fixer` ist keine Zehrer-Stufe, sondern ein orthogonales Merkmal. REQ-001 §2 sagt selbst, N-Fixierer seien Schwach- oder Mittelzehrer, und `BotanicalFamily.nitrogen_fixing` (bool) existiert bereits. Folge: Eine Erbse kann nicht gleichzeitig `light_feeder` und N-Fixierer sein; Fabaceae hätte nach der Migration zwei widersprüchliche Repräsentationen.
**Vorschlag:** `nutrient_demand ∈ {heavy_feeder, medium_feeder, light_feeder}` + Bool `nitrogen_fixing` (an Familie vorhanden, an Spezies ersetzt es den Enum-Wert); eigener Plan-Enum `PlanRole ∈ {main_crop, green_manure, fallow}` für `CropRotationPlan`. GP-FR-139: `nitrogen_fixer` → `nitrogen_fixing = true` + Zehrerstufe aus dem Steckbrief (nicht ableitbar). `_defs.schema.yaml`, `species.schema.yaml`, `plant_info.schema.yaml` führen `nitrogen_fixer` heute im Enum.

### K-002: `soil_type` vermischt Bodenart, Füllmedium und Eigenschaft (§15.1)
`sandy/loamy/clay/silty` sind Korngrößen-Bodenarten, `humus_rich` eine Eigenschaft (redundant zu `humus_percent`), `raised_bed_mix`/`potting_mix` Substrate. Ein Bodenbeet ist „sandiger Lehm mit viel Humus" — mit einem Enum nicht abbildbar.
**Vorschlag:** `soil_texture ∈ {sand, loamy_sand, sandy_loam, loam, silt_loam, clay_loam, clay, unknown}` (Hobby: 4-Klassen + Fingerprobe als Erfassungshilfe); `growing_medium_kind ∈ {native_soil, raised_bed_mix, potting_mix, mineral_substrate, other}`; `humus_rich` entfällt; `stone_content_class` ergänzen; Bodentyp (Braunerde …) bewusst nicht.

### K-003: `condition` ist Einfach-Enum mit Überschneidungen (§15.1)
`compacted` (physikalisch), `depleted` (chemisch), `waterlogged` (transient, überschneidet `drainage`/`moisture_class`), `needs_lime` (abgeleitet aus pH/Textur) treffen gleichzeitig zu; `needs_lime` kann dem gespeicherten `ph` widersprechen. Ziel-pH hängt von der Textur ab (Sand niedriger als Ton).
**Vorschlag:** `conditions: list[ConditionFlag]` mit `compacted | depleted | waterlogged | crusting | stony`; `needs_lime` abgeleitet aus `ph`, `soil_texture`, `target_ph`.

### K-004: Rotationsfenster 1–5 Jahre zu grob (§16, REQ-002 `rotation_window_years` default 3, max 5)
Anbaupausen sind erreger-/familienabhängig (Kohlhernie-Dauersporen, Zystennematoden, Erbsenmüdigkeit). Default 3 ist für Kohl und Erbse zu kurz, Obergrenze 5 knapp. Der Validator zeigt „ok" an phytosanitär problematischen Beeten.
**Vorschlag:** `BotanicalFamily.rotation_pause_years` (Default je Familie) mit Spezies-Override; `rotation_window_years` als Fallback; Obergrenze ≥ 8; Warnung nennt den Grund. ⚠️ R-003.

---

## 🟠 Wichtig

### W-001: GP-FR-061 dupliziert Schemafelder [belegt-intern]
`species.schema.yaml` Z. 156–174 hat `mature_height_cm` (Range-String „50--200"), `mature_width_cm`, `spacing_cm`, `support_required`, `recommended_container_volume_l`, `min_container_depth_cm`. GP-FR-061 will `spacing_cm_default`/`row_spacing_cm_default` neu einführen. **Vorschlag:** vorhandene Felder nutzen (Range numerisch parsen), nur `row_spacing_cm` ergänzen; `mature_width_cm` als Plausibilitätswarnung in `compute_layout`; `mature_height_cm` für Schatten/Rankhilfe; `support_required` im Dialog.

### W-002: Layout-Strategien präzisieren (§11.1, GP-FR-060/062)
- `grid` = quadratisch (`row_spacing = spacing`), sonst identisch mit `rows`.
- `triangular`: Gewinn 2/√3 ≈ 1,155 nur bei Reihenabstand = spacing × 0,866 und großen Flächen; `row_spacing_cm` ist dann abgeleitet, nicht frei; „~15 %" durch berechnete Zahl ersetzen.
- `edge_margin_cm`: entlang der Reihe spacing/2, quer row_spacing/2 → `edge_margin_along_cm` / `edge_margin_across_cm`.
- Reihenrichtung fehlt: `row_direction ∈ {along_length, along_width}` oder `row_angle_deg`; Hinweis „Reihen Nord-Süd" für hohe Kulturen (⚠️ R-009).
- Polygon/Kreis: Randabstand als Distanz zur Kante (Inset) prüfen, nicht nur Point-in-Polygon.

### W-003: Kapazitätsrechnung falsch für `rows` [belegt-intern]
`slot_capacity_calculator.calculate_plants_per_m2` rechnet 1/spacing², ignoriert Reihenabstand (Tomate 60×80: 2,08/m² statt 2,78). Spec muss `calculate_plants_per_m2(spacing_cm, row_spacing_cm=None, strategy)` vorschreiben; `triangular` 1/(spacing² × 0,866); Kapazitätsanzeige aus `compute_layout`, nicht aus Fläche.

### W-004: Obergrenze 300 cm blockiert Gehölze (GP-FR-060 vs. GP-FR-013 „Streuobstwiese")
Obergrenze auf 1000 cm oder Gehölze als Einzelslots mit `layout_strategy = free` ohne Abstandsgrenze.

### W-005: Verschattung, Rankhilfen, Saat vs. Pflanzung
Endhöhe im Dialog anzeigen; `support_required` → GardenObject `trellis` (polyline, `height_m`); `sowing_spacing_cm` + `thinning_to_cm` für Direktsaat; `planting_depth_cm` mit `depth_kind ∈ {sowing, planting}` oder getrennte Felder; `sowing_depth_cm` der Spezies existiert im Schema.

### W-006: Fehlende Pflegearten (§12.1)
`thinning` (Vereinzeln; `pricking_out` ist Anzucht), `hilling` (Anhäufeln), `tillage` (Umbrechen, Gründüngung einarbeiten), Gründüngung einsäen/umbrechen als eigene Pflegeart (Saat-/Umbruchdatum für Fruchtfolge), `covering` (Vlies/Netz/Folie/Frostschutz) + Lüften, allgemeines Ausbrechen/Entlauben/Fruchtausdünnen, Handbestäubung, Mähen, Niederschlagserfassung (Wasserbilanz); `ausgeizen` → `side_shoot_removal` (Sprachmischung).

### W-007: Pflegeart → Fachereignis (§12.1, GP-FR-124)
Hornspäne/Mist/Kompost sind organische N-Dünger → als `feeding_events` mit Flächendosierung oder `nutrient_content` am care_event, sonst sieht die Ampel sie nicht. Rindenmulch bindet N (⚠️ R-007). `liming` = Bodenbeet, `ph_adjustment` = Gießwasser/Nährlösung; pH-Absenkung über `soil_amendment` mit `sulfur`; Materialien ergänzen: `sulfur`, `rock_dust`, `wood_ash`, `perlite`, `coffee_grounds`; Kalkart als Produkt. Flush nur für `planter`/`tent`/`shelf`/Soilless. `soil_analysis` fehlt im Katalog §12.1. 1 l/m² = 1 mm als Einheit anbieten.

### W-008: R-7.2 verhindert Pflege an Kompost/Wasserquelle
Kompost umsetzen, Regentonne winterfest machen → `entity_type = garden_object` für Tasks, nur für `compost`, `water_source`, `storage`.

### W-009: Bodenanalyse-Messwerte (§15.1, GP-FR-122)
`ph_method ∈ {cacl2, h2o, probe_unknown}` Pflicht; Einheiten mg/L passen zu Nährlösung, nicht Boden — deutsche Labore: P/K/Mg als CAL mg/100 g mit Gehaltsklassen A–E, N als Nmin kg/ha; `unit`, `extraction_method`, `sample_depth_cm`, `source ∈ {lab, test_kit, sensor}` je Messwert; ergänzen CaCO₃ %, KAK (COULD), Salz/EC mit Methode; `ec_ms` → `ec_ms_cm`. ⚠️ R-006.

### W-010: Nährstoff-Ampel GP-FR-125
Vierter Zustand `insufficient_data`; `low` mehrdeutig; Inputs reichen nicht (Mineralisierung, Auswaschung, Vorfrucht-Gutschrift, Phase). Als „Düngebedarf wahrscheinlich" beschriften, VDLUFA-Klassen A–E als Eingang, immer `confidence` + Grundlage. ⚠️ R-004.

### W-011: Mulchwirkung im Bewässerungsbedarf fehlt
`mulch_factor` (0,5–1,0) im Beetprofil als Vorschlagsmodifikator (⚠️ R-005).

### W-012: Hochbeet-Anlagejahr/Schichtaufbau
`soil_profile.established_on`, optional `fill_layers[]`; Fruchtfolge kennt Anlagejahr; Substratwechsel setzt Historie zurück (`rotation_reset_at`).

### W-013: Fruchtfolge bei Mischbeeten, Vor-/Nachkulturen, Dauerkulturen
Rotationsmatrix-Zelle = Liste je Saison; Aggregationsregel für Mischbeet; Dauerkulturen (Spargel, Erdbeere, Beerensträucher) → `Location.rotation_exempt` oder je Run; Gründüngung nach Familie zählen (Senf/Ölrettich = Brassicaceae, Kohlhernie-Wirt).

### W-014: Beetstatus mischt Lebenszyklus und Saisonzustand (§7.4)
`fallow` ist Saisonzustand; §7.4 setzt Brache = Gründüngung, §16.3 trennt sie. Übergänge `planned → retired` und `retired → active` fehlen. **Vorschlag:** `bed_status ∈ {planned, active, retired}`; Saisonzustand abgeleitet `empty | planted | green_manure | fallow | winter_covered`.

### W-015: Pflanzungszustände (§11.3)
„geerntet" verlangt `removed_on` — Mehrfachernte bei stehender Pflanze → Zustand `harvesting`; `failed` (Ausfall, `termination_type = died` existiert [belegt-intern]) mit Nachpflanzung auf demselben Slot; Direktsaat → Zustand `sown` für `zone`/`row`-Slots, Pflanzen erst nach Vereinzeln.

### W-016: Zelt = Beet (§9.2a) — zwingende Unterschiede
1. Inkonsistenz: `tent` ist nicht `is_bed`, Bepflanzen/`compute_layout` hängen an Beeten → Regel „Layout gilt für `is_bed` oder `tent`", sonst GP-ACC-036 unerfüllbar.
2. Lichtverteilung: PPFD-Hotspot; Randabstand spacing/2 hat im Zelt keine Lichtbasis → Leuchte als Objekt/Property (`fixture_geometry`, `lamp_height_cm`, `canopy_distance_cm`), PPFD-Messpunkte optional.
3. Vertikale: `inner_height_cm`, `lamp_height_cm` am Location-Profil.
4. Etagen: eine Ebene = eine Location (child von `shelf`/`tent`), eigene Lampe/Klima/Photoperiode (⚠️ R-010).
5. Topfvolumen auf den **Slot** (`container_volume_l`); gegen `Species.recommended_container_volume_l`/`min_container_depth_cm` [belegt-intern] prüfen; `pitch_m = 0,30` für kleine Töpfe falsch → `migrated_grid` im UI als „geschätzt".
6. Photoperiode pro Lichtzone → Validierungshinweis `tent.photoperiod_conflict`.
7. Fruchtfolge: GP-FR-137 nur `planter`; `tent`/`shelf` ergänzen, Standard aus.
8. `adjacency_factor` pro Location überschreibbar (SCROG-Überlappung).

### W-017: Bewässerung (§14)
Rechnung mm × Fläche = Liter korrekt [belegt-intern, REQ-037 FAO-56]. Bezugsfläche = bepflanzte/bewässerte Fläche (REQ-037 `irrigated_area`), nicht Beetfläche; `application_efficiency` je `irrigation_type` (Tropf ~90 %, ⚠️ R-005) → Laufzeit = Brutto/`flow_rate`; Kübel/Hochbeet/Zelt: Wasserspeicher über Substratvolumen deckeln; GP-FR-117 `by_area` in Auswertungen nicht als gemessen; Doppelung `IrrigationZone.irrigation_type` vs. `Location.irrigation_system` → Konfliktregel; Quellenkapazität vs. Zonenbedarf; Frostschutz Tonne (REQ-047).

### W-018: Nachbarschaftsregel GP-FR-130
Faktor 1,5 plausibel (Diagonale √2 drin, übernächster Dreiecksnachbar 1,73 draußen). Fehler bei `rows`: Reihenabstand ignoriert → `max(spacing, row_spacing)`; ungleiche Größen (Radies 5 cm vs. Tomate 60 cm → 90 cm Radius) → Interaktionsradius aus `mature_width_cm/2` beider Arten; Dichtekulturen (Möhre 5 cm → 1400 Punkte) sprengen Kantenlimit → ab Schwelle Zonen statt Punkte; Evidenzgrad im Mischkultur-Graph anzeigen.

---

## 🟡 Hinweise
- H-001 Beetbreite > 1,2 m (beidseitig) / > 0,8 m (einseitig) warnen; Wegbreite ≥ 0,3–0,5 m (⚠️ R-009).
- H-002 `moisture_class` → `site_water_regime` (Standortansprache, nicht Sensorzustand).
- H-003 `drainage` vs. `site_water_regime` Dominanzregel.
- H-004 `FeederLevel` am Steckbrief mit `source`/`confidence`.
- H-005 `min_container_depth_cm`/`effective_root_depth_cm` [belegt-intern] gegen `height_m` prüfen.
- H-006 `sun_exposure` braucht Stundenschwellen (≥ 6 h / 3–6 h / < 3 h üblich, ⚠️ R-011).
- H-007 Lichtdurchlässigkeit der Eindeckung bei Gewächshaus/Tunnel.

## 🔬 §29 Sonnen-/Schattenberechnung — jetzt anzulegende Felder
1. `height_m` für `building`, `wall`, `fence`, `shrub`, `trellis`, `tree`; Dach `eave_height_m`/`ridge_height_m` oder `roof_type`.
2. Baum: `crown_base_height_m`, `foliage ∈ {deciduous, evergreen}`, optional `leaf_on_month`/`leaf_off_month`.
3. `opacity`/`permeability` für Zaun/Hecke.
4. `GardenObject.off_site = true` (Containment ausgenommen, Nachbargebäude als Kulisse); optional `Site.plan.horizon_profile`.
5. `Site.plan.terrain {slope_deg, aspect_deg}`, `Site.elevation_m`.
6. Frühbeet/Tunnel: `cover_material`, `light_transmission_percent`, `roof_tilt_deg`.
7. `north_angle_deg`: Drehrichtung nicht festgelegt (Kompassazimut läuft im Uhrzeigersinn, `rotation_deg` gegen); **geografisch Nord, nicht magnetisch** (Missweisung ⚠️ R-012).
8. `Location.sun_exposure_source ∈ {manual, computed}`, `sun_hours_direct`.
9. `Species.mature_height_cm` numerisch verfügbar machen.
10. `sun_calculator` nutzt `gps_coordinates` + `timezone` (vorhanden).

## 📐 Schema-Abgleich (geprüfter Ausschnitt)

| Befund | Stelle | Status |
|---|---|---|
| `spacing_cm_default`/`row_spacing_cm_default` neu geplant; `species.spacing_cm` (Range-String) existiert | GP-FR-061 vs. `species.schema.yaml:162` | Duplikat (W-001) |
| `mature_height_cm`/`mature_width_cm`/`support_required` vorhanden, ungenutzt | `species.schema.yaml:156–174` | nutzen |
| `nitrogen_fixer` im Enum + `BotanicalFamily.nitrogen_fixing` (Bool) | `_defs.schema.yaml:49–51`, REQ-001 §2 | Doppelrepräsentation (K-001) |
| `typical_nutrient_demand` light/medium/heavy | `botanical_families.schema.yaml:31` | Migration GP-FR-139 korrekt benannt, K-001 beachten |
| `sowing_depth_cm` (Spezies) vs. `planting_depth_cm` (Entry) | `species.schema.yaml:347` | klären (W-005) |
| `recommended_container_volume_l`/`min_container_depth_cm` | `species.schema.yaml:150–155` | gegen Slotvolumen prüfen (W-016) |
| `TerminationType` harvested/senesced/died/cancelled | `enums.py:294` | §11.3 anpassen (W-015) |

## 🔍 Offene Recherchepunkte — ⚠️ NICHT VERIFIZIERT

| Nr. | Aussage | Empfohlene Quellen |
|---|---|---|
| R-001 | Dreiecksraster 2/√3 ≈ 1,155 (geometrisch korrekt) | Fachbuch Pflanzverbände |
| R-002 | Textur-Klassen, Fingerprobe | KA5, USDA Texture Triangle, DIN 4220, LfL |
| R-003 | Anbaupausen Kohl 4+, Kartoffel 3–4, Erbse bis 6, Zwiebel/Möhre 3–4, Tomate 3–4 | JKI, LfL, LWK, Peer-Review Kohlhernie |
| R-004 | VDLUFA-Gehaltsklassen A–E, Nmin | VDLUFA, DüV §4 |
| R-005 | Mulch senkt Verdunstung; Tropf ~90 %, Beregnung niedriger | FAO-56 |
| R-006 | Ziel-pH nach Bodenart; CaCl₂ vs. H₂O | VDLUFA Kalkung, LfL |
| R-007 | Rindenmulch bindet N | Extension-Literatur, Bodenkunde |
| R-008 | Spülvolumen als Vielfaches des Topfvolumens | Hydroponik-Fachbuch |
| R-009 | Beetbreite ≤ 1,2 m, Nord-Süd-Reihen | RHS, Landesgartenbauämter |
| R-010 | Obere Regalebenen wärmer; PPFD-Gleichmäßigkeit | Hersteller-PPFD-Maps, CEA-Literatur |
| R-011 | Sonnenstundenschwellen | RHS, USDA — im Spec festlegen |
| R-012 | Magnetische Missweisung Mitteleuropa | NOAA WMM, BKG |
| R-013 | Zehrerklassen konkreter Kulturen variieren je Quelle | Landesanstalten; Quelle je Steckbrief |

## Dringendste Maßnahme
O-07 (GP-FR-138) vor Welle 1 überarbeiten, bevor M6 gebaut wird: `nutrient_demand` (3 Stufen) und `nitrogen_fixing` (Bool) trennen, `PlanRole` einführen. Gleichzeitig §15.1 (`soil_texture`, `growing_medium_kind`, `conditions[]`) korrigieren, solange keine Daten migriert sind.
