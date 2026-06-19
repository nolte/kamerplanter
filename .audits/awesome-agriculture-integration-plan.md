# Integrationsplan: awesome-agriculture-Projekte → Kamerplanter

```yaml
Dokument: Integrations- & Umsetzungsplan
Bezug: REQ-037, REQ-038, REQ-039, REQ-040, REQ-041
Grundlagen:
  - spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md (Lizenzprüfung)
  - spec/req/REQ-037..041 (Integrations-Anforderungen)
Maßstab: Kamerplanter = MIT, öffentlich verteilt, self-hosted (K8s/Helm), Zielmarkt DACH.
Status: Plan (Entwurf)
Datum: 2026-06-20
```

## 1. Auswahllogik — was „zahlt direkt ein"?

Ein Projekt **zahlt direkt auf Kamerplanter ein**, wenn es (a) eine bereits spezifizierte,
aber unausgefüllte Lücke schließt, (b) lizenzrechtlich sauber zur MIT-Codebasis passt und
(c) mit vertretbarem Aufwand an bestehende Patterns andockt. Bewertet nach vier Achsen:

| Integration | Fachl. Nutzen | Lizenz-Sicherheit | Aufwand | Hebel (entsperrt anderes) | Direkt-Einzahler? |
|-------------|:---:|:---:|:---:|:---:|:---:|
| **REQ-041 NASA POWER** | hoch | 🟢 CC-BY-4.0 | M | **hoch** (Strahlung→ET₀, Normalen→Zonen) | ⭐ **Ja** |
| **REQ-037 Evapotranspiration** | hoch | 🟢 BSD-3 | S–M | mittel (→ REQ-022 adaptive) | ⭐ **Ja** |
| **REQ-039 Winterhärtezonen (DACH)** | hoch | 🟢 DWD/Open-Meteo | M | mittel (→ REQ-022 Überwinterung) | ⭐ **Ja** |
| **REQ-038 CV-Diagnose** | hoch | 🟢 PlantCV+PlantDoc¹ | **L** | gering | ⭐ Ja, aber eigene Initiative |
| **REQ-040 Enrichment** | gering–mittel | 🟠 gemischt² | S–M | gering | ◻ Nur eingeschränkt |

¹ PlantVillage-Lizenz ungeklärt → nur PlantDoc/Eigendaten. · ² OpenFarm-Server tot, Growstuff CC-BY-SA.
Aufwand: S=klein, M=mittel, L=groß.

### Kennzeichnung

- ⭐ **DIREKT-EINZAHLER, Integration lohnt sich** → REQ-041, REQ-037, REQ-039 (license-clean,
  fachlich tragend, greifen ineinander) + REQ-038 (hoher Nutzen, aber eigenständiges ML-Projekt).
- ◻ **Optional / niedrige Priorität** → REQ-040 (nur OpenFarm-CC0-Dump als sauberer Teilgewinn;
  Growstuff nur als Mapping-Idee).
- 🔴 **Ausgeschlossen** → pyTSEB (GPL-3.0), USDA/PHZM-Daten (proprietär/US-only), Growstuff-Datenmerge.

## 2. Abhängigkeits-Reihenfolge

```
Welle 1 (Outdoor-Fundament, license-clean, selbstverstärkend)
  REQ-041 NASA POWER ──► liefert solar_radiation_mj_m2 ──► REQ-037 ET₀
        │                                                      │
        └──► liefert ClimateNormal (coldest_month) ──► REQ-039 Winterhärtezonen
                                                               │
  REQ-037 + REQ-039 ──► speisen REQ-022 (adaptive Gießerinnerung, Winterhärte-Ampel)

Welle 2 (eigenständige ML-Initiative)
  REQ-038 CV-Diagnose ──► ergänzt REQ-010 IPM + REQ-036 Diagnose-Assistent

Welle 3 (optional)
  REQ-040 OpenFarm-CC0-Dump (einmaliger Import) — Growstuff nur als Vorlage
```

**Empfohlene Sequenz:** REQ-041 → REQ-037 → REQ-039 (Welle 1), dann REQ-038 (Welle 2),
REQ-040 nur bei Bedarf (Welle 3). NASA POWER zuerst, weil es Strahlungs- und Klimanormalen-
Input für die beiden folgenden Integrationen liefert — größter Hebel.

---

## 3. Plan mit benötigten Erweiterungen

Legende Aufwand: S ≈ 1–2 Tage · M ≈ 3–5 Tage · L ≈ > 1 Woche. Jede Erweiterung folgt dem
5-Layer-Pattern (API → Service → Engine/Calculator → Repository → ArangoDB) und NFR-003 (Code Englisch).

### Welle 1 · REQ-041 — NASA POWER Wetter-/Klimaquelle ⭐ [Aufwand M]

Andockpunkt: bestehende REQ-005-`WeatherAdapterRegistry` + `weather_forecasts`.

- [ ] **Data Access:** `NasaPowerWeatherAdapter(WeatherAdapter)` in `data_access/external/`,
      gegen REST-API `power.larc.nasa.gov` (keyless), Parameter-Mapping
      `ALLSKY_SFC_SW_DWN→solar_radiation_mj_m2`, `T2M_MIN/MAX`, `PRECTOTCORR`, `WS2M`, `RH2M`.
- [ ] **Persistenz:** Feld `solar_radiation_mj_m2` + `data_kind="reanalysis"` an `weather_forecasts`;
      neue Collection `climate_normals` + Edge `has_climate_normal` (Site → Normalen, inkl.
      `coldest_month_min_c` für REQ-039).
- [ ] **Engine/Service:** Quellen-Priorität pro Site (POWER = Ergänzung, kein Frühwarn-Trigger →
      `check_frost_warnings` ignoriert `data_kind="reanalysis"`).
- [ ] **Celery:** `fetch_climate_normals` (selten, Cache-lang); Einreihung in `fetch_weather_forecasts`.
- [ ] **Infra/Compliance:** clientseitiges Caching + Throttle (HTTP 429, keine Mehrfach-Requests je
      0.5°-Zelle); **POWER-Attribution** in UI/Export (CC-BY-4.0).
- [ ] **Frontend:** Quellen-Auswahl/-Anzeige im Standort-Detail; Klimanormale anzeigen.
- [ ] **Tests:** Adapter-Mapping, Caching, Attribution-Rendering.

### Welle 1 · REQ-037 — Evapotranspiration & Bewässerung ⭐ [Aufwand S–M]

Andockpunkt: REQ-004 (Bewässerung), REQ-005 (Wetterinput), REQ-019 (Substrat-WHC).

- [ ] **Dependency:** `aquacropeto` (BSD-3) — `pip install aquacropeto`; **Py-3.14-Kompatibilität
      prüfen**, sonst Source vendored einbinden (Copyright-Notice „Mark Richards" erhalten).
      🔴 **pyTSEB NICHT verwenden** (GPL-3.0).
- [ ] **Engine:** `EvapotranspirationCalculator` (Layer Engine/Calculator): ET₀ via FAO-56
      Penman-Monteith wenn Strahlung+Wind+Feuchte vorhanden (NASA POWER!), sonst Hargreaves-Fallback;
      ETc = ET₀ × Kc; Netto-Bedarf = ETc − effektiver Niederschlag, gedeckelt durch
      `water_holding_capacity_percent`.
- [ ] **Persistenz:** Feld `crop_coefficient_kc` an GrowthPhase/Species + `KC_DEFAULTS`-Tabelle;
      Collection `irrigation_demands` (+ Edges).
- [ ] **Celery:** `compute_irrigation_demand` (06:15, nach Wetter-Update) je Outdoor-Site/Run.
- [ ] **Integration REQ-022:** Gießbedarf passt `watering_interval_days` / Gießerinnerung adaptiv an.
- [ ] **Scope-Guard:** **nur Outdoor** (ET₀ outdoor-relevant; Indoor bleibt VPD-/intervallbasiert).
- [ ] **Frontend:** Wasserbilanz pro Standort; Kc-Pflege im Expertenmodus (REQ-021).
- [ ] **Tests:** Methodenwahl PM↔Hargreaves, Wasserbilanz-Deckelung, Celery-Trigger.

### Welle 1 · REQ-039 — Winterhärtezonen (DACH) ⭐ [Aufwand M]

Andockpunkt: REQ-001 (`frost_sensitivity`, `hardiness_zones`), REQ-002 (Site/GPS), REQ-022 (Ampel).

- [ ] **Datenbasis (license-clean):** Zonenableitung aus **DWD Open Data** (GeoNutzV, Quelle
      „Datenbasis: Deutscher Wetterdienst") und/oder **Open-Meteo** (CC-BY-4.0) Klimanormalen —
      bzw. `climate_normals` aus REQ-041. 🔴 **USDA/PHZM-Daten NICHT einchecken** (proprietär, US-only).
- [ ] **Engine:** `HardinessZoneResolver` — berechnet Zone aus mittlerem Jahres-Tiefstwert
      (`coldest_month_min_c`); USDA-Zonen*schema* (1–13, a/b) als kanonisches Modell (bereits via
      `Site.climate_zone` regex `^\d{1,2}[a-b]$` etabliert).
- [ ] **Persistenz:** Referenz-Collection `hardiness_zones` + Edge `located_in_zone`; additive
      `Site`-Felder (Migrations-/Sync-Hinweis zum bestehenden `climate_zone`).
- [ ] **Integration REQ-022:** Winterhärte-Ampel (grün/gelb/rot) automatisch aus
      `Species.frost_sensitivity` ↔ `Site`-Zone; Frost-Defaults speisen REQ-015-A
      (`last_frost_date_avg`, `eisheilige_date`).
- [ ] **Optional:** `FrostlineUsAdapter` (MIT-Schema-Vorlage) nur falls US-Nutzer bedient werden —
      dann PRISM/OSU-Logo-/Disclaimer-Auflagen erfüllen.
- [ ] **Frontend:** Zonen-Anzeige + Ampel im Standort-/Pflanzen-Detail (i18n DE/EN).
- [ ] **Tests:** Zonenableitung aus Normalen, Ampel-Logik, climate_zone-Migration.

### Welle 2 · REQ-038 — CV-gestützte Pflanzendiagnose ⭐ [Aufwand L · eigene Initiative]

Andockpunkt: REQ-010 (IPM), REQ-029/-A (Bild-Pipeline/Inference-Service), REQ-036 (Diagnose-Assistent).

- [ ] **Lizenz-Gate:** PlantVillage **nicht** ohne fixierte Lizenz nutzen → **PlantDoc (CC-BY-4.0)**
      + Eigendaten als Trainingsbasis; PlantCV (MPL-2.0) **unverändert** als Library/Service
      (nicht in deren Dateien patchen; Notice mitliefern).
- [ ] **ML-Pipeline:** ONNX-Krankheitsklassifikator als zusätzlicher Endpunkt im bestehenden
      Inference-Service (REQ-029-A, kein neuer Microservice); Fine-Tuning gegen Realdaten (Domänen-Gap
      Lab→Feld!); PlantCV als deterministische Phänotyp-/Vorverarbeitung.
- [ ] **Persistenz:** Collection `plant_diagnosis_requests` (+ 4 Edges); Ergebnis verknüpft auf
      REQ-010 `diseases`/`pests` via `detected`-Edge.
- [ ] **DSGVO:** Consent `plant_diagnosis`, EXIF-Stripping (REQ-029 §5.4 wiederverwenden).
- [ ] **Sicherheits-/Haftungs-Guardrails:** Confidence-Schwellen; **immer** „nur Hypothese, keine
      Fachdiagnose"-Disclaimer in API + UI; CV-Treffer → IPM-Treatment-**Vorschlag** (nie Auto-Trigger,
      Karenz-Gate bleibt aktiv).
- [ ] **Offene fachl. Lücke:** REQ-010 hat keine `deficiency`-Collection → Mangel-Matching über
      REQ-036-Symptom-Slugs (oder Collection nachrüsten).
- [ ] **Frontend:** Foto-Upload-Diagnose im IPM-/Diagnose-Flow; Ergebnis + Disclaimer.
- [ ] **Tests:** Inferenz-Stub, Confidence-Gate, Treatment-Vorschlag ohne Auto-Trigger.

### Welle 3 · REQ-040 — Enrichment (optional) ◻ [Aufwand S–M]

Andockpunkt: REQ-011 (`ExternalSourceAdapter`/`AdapterRegistry`), REQ-028 (Companion), REQ-032 (Export).

- [ ] **OpenFarm (CC0):** **kein Live-Adapter** (Server tot seit 4/2025) → **einmaliger statischer
      CC0-Dump-Import** aus Mirror, falls Mehrwert > Pflegeaufwand. Auto-Accept 0.9 / Propose-only 0.7
      respektieren; lokale Hoheit unberührt.
- [ ] **Growstuff (CC-BY-SA 3.0):** ⚠️ **ShareAlike-Falle.** Entweder (a) Daten **strikt isoliert**
      (eigene Collection, kein Merge in Stammfelder), Per-Feld-Provenance, Attribution + CC-BY-SA in
      jedem Export/Druck (REQ-032!) — **oder** (b) Growstuff nur als **Mapping-Idee** (keine
      Wertübernahme), um die Wissensbasis CC-BY-SA-frei zu halten. **Empfehlung: (b)**, außer der
      fachliche Bedarf rechtfertigt die Export-Auflagen.
- [ ] **Companion-Daten:** falls Import → `CompanionImportService` befüllt REQ-028
      `compatible_with`-Edges (kuratierte Edges vor Downgrade schützen).
- [ ] **Begründung niedrige Prio:** Anbauzeitraum-Lücken laut Audit großteils geschlossen; GBIF+Perenual
      bereits vorhanden → marginaler Zusatznutzen bei realer Lizenzreibung.

---

## 4. Querschnitt-Aufgaben (vor/parallel zu Welle 1)

- [ ] **REQ-011 §1.1 Lizenzkorrektur:** OpenFarm CC-BY-4.0 → **CC0** (verifiziert).
- [ ] **REQ-Entwürfe schärfen** gemäß `awesome-agriculture-lizenz-und-nutzungsanalyse.md` §4:
      pyTSEB als 🔴 meiden (REQ-037); PlantDoc als primäre Trainingsquelle + PlantVillage-Risiko
      (REQ-038); frostline-Daten proprietär/DWD-Basis (REQ-039); OpenFarm-Live-Adapter streichen,
      Growstuff-Export-Konflikt (REQ-040).
- [ ] **Attribution-Mechanik:** generischer „data source attribution"-Baustein (UI + Export/Druck)
      für CC-BY-Quellen (NASA POWER, Open-Meteo, PlantDoc) — einmal bauen, mehrfach nutzen.
- [ ] **NFR-009/Dependency-Gate:** `aquacropeto` + ML-Stack (ONNX/PlantCV) in Dependency-Audit
      aufnehmen; Lizenz-Header/NOTICE pflegen.

## 5. Entscheidungs-Gates (Betreiber) — GETROFFEN 2026-06-20

| # | Entscheidung | Blockiert | ✅ Beschluss |
|---|--------------|-----------|--------------|
| G1 | PlantVillage: Lizenz fixieren **oder** fallenlassen | REQ-038 Training | ✅ **Fallengelassen** — nur PlantDoc (CC-BY-4.0) + Eigendaten |
| G2 | Growstuff: isolieren+SA-Export **oder** nur Mapping-Idee | REQ-040 | ✅ **Nur Mapping-Idee** — kein Wertimport, Wissensbasis bleibt CC-BY-SA-frei |
| G3 | OpenFarm: CC0-Dump importieren **oder** verzichten | REQ-040 | ✅ **Optionaler einmaliger CC0-Dump** (Server tot, kein Live-Adapter) |
| G4 | REQ-038 jetzt **oder** nach Welle 1 terminieren | Roadmap | ✅ **Nach Welle 1** (eigenständige ML-Initiative) |

Die Beschlüsse sind in die betroffenen REQ-Dokumente (REQ-038 v1.1, REQ-040 v1.1) und in
`spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md` §5 eingearbeitet.

## 6. Definition of Done (Gesamtinitiative)

- Welle 1 (REQ-041 → 037 → 039) implementiert, getestet, license-clean, Attribution sichtbar.
- REQ-022 nutzt ET₀-Gießbedarf + automatische Winterhärte-Ampel.
- REQ-038 als terminierte Folge-Initiative mit fixierter Datenlizenz (G1) eingeplant.
- REQ-040 entschieden (G2/G3) — umgesetzt oder bewusst zurückgestellt.
- 🔴-Liste (pyTSEB, USDA/PHZM-Daten, Growstuff-Merge) dokumentiert nicht verwendet.
```
