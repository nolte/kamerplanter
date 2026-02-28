# Spezifikation: REQ-004 - Dünge-Logik

```yaml
ID: REQ-004
Titel: Dynamische Nährstoff- und Dünge-Engine
Kategorie: Bewässerung & Düngung
Fokus: Nutzpflanze (Indoor/Hydro)
Technologie: Python, ArangoDB, Regelbasierte Logik
Status: Entwurf
Version: 3.0 (Multi-Channel Delivery)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich präzise Mischverhältnisse für Reservoirs, Tanks und Gießkannen berechnen, um Nährstoffmangel, Überdüngung und Salzakkumulation zu verhindern, während ich komplexe Multi-Part-Dünger korrekt mische."

**Beschreibung:**
Das System verwaltet die gesamte Nährstoffversorgung von der Planung bis zur Dokumentation mit Fokus auf:

**Multi-Part-Fertilizer-Management:**
- **Base-Nutrients:** A+B-Komponenten (Mikro/Makro getrennt wegen Ausfällungen)
- **Supplements:** CalMag, Enzyme, Fulvin-/Huminsäure, Silizium
- **Boosters:** PK 13-14 (Blüte-Booster), Root-Stimulatoren, Top-Max
- **Biologische Zusätze:** Mykorrhiza, Trichoderma, Beneficial Bacteria

**Kritische Misch-Reihenfolge:**
1. Wasser mit Basistemperatur (18-22°C)
2. Silizium-Zusätze (pH-instabil, zuerst!)
3. CalMag (verhindert Ca-P-Ausfällung)
4. Base A (typisch: Calcium + Mikronährstoffe)
5. Base B (typisch: Phosphor + Schwefel + Magnesium)
6. Weitere Zusätze nach Priorität
7. pH-Korrektur (pH Down/Up) als letzter Schritt

**Hinweis:** Die Zuordnung A/B variiert je nach Hersteller. Die tatsächliche Reihenfolge wird über das `mixing_priority`-Feld des Fertilizer-Modells gesteuert, nicht über eine feste A/B-Konvention.

**EC-Budget-Management:**
- Gesamtziel-EC (z.B. 1.8 mS) minus Wasser-Basis-EC
- Proportionale Verteilung auf Komponenten basierend auf NPK-Beitrag
- Berücksichtigung von EC-Beiträgen durch pH-Korrekturen

**Substrat-spezifische Logik:**
- **Hydroponik:** Höhere EC-Toleranz (1.4-2.4 mS), präzise Dosierung
- **Coco:** Moderate EC (1.2-1.8 mS), CalMag-Pufferung wichtig
- **Soil:** Niedrige EC (0.8-1.4 mS), organische Zusätze bevorzugt
- **Living Soil:** Minimale Intervention, Komposttee, Mikrobiom-Fokus

<!-- Quelle: Outdoor-Garden-Planner Review G-007 -->
**Organische Freiland-Düngung:**

Freilandgärtner arbeiten primär mit organischen Düngern und Bodenverbesserern. Im Gegensatz zur Hydroponik-Kalkulation (EC-Budget, ml/L) wird im Freiland nach **Ausbringungsmenge pro Flächeneinheit** (g/m² oder L/m²) dosiert. Das System unterstützt beide Paradigmen parallel:

**Organische Dünger-Kategorien:**
- **Kompost:** Reifkompost (2-4 L/m² im Frühjahr), Halbkompost (nur im Herbst als Mulch)
- **Pflanzenjauchen:** Brennnesseljauche (1:10 verdünnt, alle 2 Wochen Mai-August), Beinwell-Jauche (kaliumreich, ideal für Fruchtgemüse)
- **Hornprodukte:** Hornspäne (langsame N-Freisetzung, 50-80 g/m²), Hornmehl (schnellere Freisetzung, 30-50 g/m²), Horngrieß (mittel)
- **Guano/Tierdünger:** Schafwollpellets, Hühnertrockenmist (vorsichtig dosieren — Verbrennung!)
- **Bokashi/EM:** Fermentierte Küchenabfälle, Effektive Mikroorganismen — Bodenlebens-Aktivierung
- **Gründüngung:** Phacelia, Senf, Inkarnatklee, Lupine — Nährstoff-Fixierung durch Pflanzenanbau (Verknüpfung mit REQ-001 `green_manure_suitable` und REQ-002 Fruchtfolge)
- **Gesteinsmehl:** Urgesteinsmehl (Spurenelemente, Bodenstruktur), Algenkalk (pH-Anhebung)

**Ausbringungs-Modell (Freiland):**
Für organische Feststoff-Dünger und Bodenhilfsstoffe wird die Dosierung **pro Fläche** statt pro Volumen berechnet:
- `application_rate_g_per_m2: Optional[float]` — Gramm pro Quadratmeter (Feststoffe)
- `application_rate_l_per_m2: Optional[float]` — Liter pro Quadratmeter (Kompost, Mulch)
- `dilution_ratio: Optional[str]` — Verdünnungsverhältnis für Jauchen/Brühen (z.B. "1:10", "1:20")
- `application_season: Optional[list[Literal['spring', 'summer', 'autumn', 'winter']]]` — Empfohlene Ausbringungszeit
- `nutrient_release_speed: Literal['immediate', 'weeks', 'months', 'season_long']` — Freisetzungsgeschwindigkeit

**Nährstoffbedarfs-Empfehlung nach Pflanzenkategorie:**
Statt EC-Zielwerte empfiehlt das System für Freilandpflanzen eine vereinfachte Düngestrategie basierend auf dem `nutrient_demand_level` (REQ-001):

| Nährstoffbedarf | Typische Pflanzen | Empfehlung |
|----------------|-------------------|------------|
| `heavy_feeder` (Starkzehrer) | Tomate, Kürbis, Kohl, Zucchini, Mais | Kompost (3-4 L/m²) + Hornspäne (80 g/m²) + Jauche alle 2 Wo |
| `medium_feeder` (Mittelzehrer) | Möhre, Fenchel, Salat, Zwiebel, Kohlrabi | Kompost (2-3 L/m²) + Hornspäne (40 g/m²), Jauche optional |
| `light_feeder` (Schwachzehrer) | Bohne, Erbse, Radieschen, Kräuter (mediterran) | Kompost (1-2 L/m²), kein weiterer Dünger nötig |
| `nitrogen_fixer` (N-Fixierer) | Bohne, Erbse, Lupine, Klee | Kein N-Dünger! Nur Kalium/Phosphor bei Bedarf |

**Bodenanalyse als Ausgangspunkt:**
Für Freilandgärten empfiehlt das System eine optionale Bodenanalyse als Startpunkt:
- `soil_ph: Optional[float]` — pH-Wert des Gartenbodens (Ziel: 6.0-7.0 für Gemüse)
- `soil_type: Optional[Literal['sandy', 'loamy', 'clay', 'silty', 'humus_rich', 'raised_bed_mix']]`
- `soil_analysis_date: Optional[date]` — Datum der letzten Bodenanalyse
- `soil_notes: Optional[str]` — Freitext für Besonderheiten

**Abgrenzung Hydro/Freiland:**
Die bestehende EC-Budget-Kalkulation und Mischsequenz-Validierung gelten weiterhin für `substrate_type IN ('hydro', 'coco', 'dwc', 'aeroponics')`. Für `substrate_type IN ('soil', 'living_soil', 'raised_bed_mix')` wird die organische Freiland-Düngung empfohlen. Das UI blendet im Anfänger-/Fortgeschrittenen-Modus (REQ-021) die EC/pH-Mischlogik aus und zeigt stattdessen die vereinfachte Düngeempfehlung.

**Applikationsmethoden & ergänzende Handdüngung:**
Nicht alle Dünger eignen sich für die Ausbringung über Tank/Tropfer-Systeme. Organische Dünger (Komposttee, Fischemulsion, Wurmhumus-Extrakt, Mykorrhiza-Suspensionen) enthalten Schwebstoffe, die Tropfer verstopfen, und biologische Kulturen, die im Tank Biofilm verursachen können. Daher unterstützt das System **ergänzendes manuelles Gießen per Gießkanne** auch bei Locations mit automatischer Bewässerung:

- **Fertigation (Tank/Tropfer):** Mineralische und tank-sichere Dünger über das Bewässerungssystem — automatisch oder manuell aus dem Tank
- **Drench (Gießkanne):** Manuelle Substrat-Durchspülung — typisch für organische Flüssigdünger, Komposttee, Spezialbehandlungen
- **Foliar (Blattdüngung):** Spray-Applikation auf Blätter — für Mikronährstoffe, Kalzium, Silikat
- **Top Dress (Oberfläche):** Feste organische Zusätze auf die Substratoberfläche — Wurmhumus, Guano, Langzeitdünger

Das `Fertilizer`-Modell enthält `tank_safe: bool` und `recommended_application`, um bei der Düngung die passende Applikationsmethode vorzuschlagen und vor Tank-Kontamination zu warnen.

<!-- Quelle: Cannabis Indoor Grower Review G-013 -->
**Phasenbasierte Foliar-Warnung (Blüte):**
Blattdüngung (`foliar`) in der Blütephase ab Woche 2 ist fachlich kritisch: Sprühnebel auf Blütenständen (Buds) fördert **Schimmelbildung** (Botrytis, Mehltau), verursacht **Geschmacksverunreinigung** und hinterlässt bei Räuchergut **Rückstände auf dem Erntegut**. Das System implementiert daher eine **phasenbasierte Soft-Warnung** für Foliar-Applikation:

- **Regellogik:** Wenn `application_method = 'foliar'` UND aktuelle Phase = `flowering` UND Blütewoche ≥ 2 → Soft-Warnung anzeigen
- **Warnstufe:** `WARNING` (kein Hardblock) — die Aktion bleibt ausführbar, wird aber mit deutlichem Warnhinweis versehen
- **Warntext:** _„Foliar-Feeding in der Blüte (ab Woche 2) vermeiden! Schimmelrisiko auf Buds, Geschmacksverunreinigung und Rückstände auf Erntegut. Blattdüngung nur in Vegetationsphase oder maximal Blütewoche 1."_
- **Kein Hardblock**, weil IPM-Notfallbehandlungen (z.B. Kaliumbicarbonat gegen Echten Mehltau) auch in der Blüte per Spray appliziert werden müssen. Solche Behandlungen werden über REQ-010 (IPM-System) als `emergency_treatment` gekennzeichnet und sind von der Warnung ausgenommen
- **Ausnahmeregel:** Wenn das FeedingEvent mit einem `TreatmentApplication` (REQ-010) verknüpft ist und `is_emergency: true` gesetzt ist, wird die Warnung unterdrückt
- **Phasen-Erlaubnis:** In `germination`, `seedling` und `vegetative` ist Foliar uneingeschränkt erlaubt. In `flowering` Woche 1 wird ein informativer Hinweis angezeigt (Severity: `INFO`), ab Woche 2 die volle Warnung (Severity: `WARNING`)
- **UI-Darstellung:** Gelbes Warnsymbol (⚠) neben dem Applikationsmethoden-Dropdown, wenn `foliar` in der Blütephase ab Woche 2 ausgewählt wird. Der Warntext wird als expandierbarer Alert-Banner über dem Formular angezeigt
- **API-Response:** Bei Erstellung eines FeedingEvent mit `application_method='foliar'` in der Blütephase ab Woche 2 enthält die Response ein `warnings`-Array mit dem Warnhinweis (HTTP 201, nicht 422)

**Flushing-Strategien:**
- **Pre-Harvest Flush:** 7-14 Tage vor Ernte, graduelle EC-Reduktion
- **Mid-Cycle Flush:** Bei Salzakkumulation (EC-Runaway)
- **Transplant Flush:** Vor Umtopfen zur Substrat-Reinigung

**Nährstoffprofil-Verwaltung (Lifecycle Nutrient Plans):**

**User Story:** "Als Gärtner möchte ich wiederverwendbare Nährstoffpläne über den gesamten Lebenszyklus einer Pflanze erstellen, um bewährte Düngeprogramme zu speichern, zu teilen und auf neue Pflanzen anzuwenden."

**Beschreibung:**
Das System ermöglicht die Erstellung und Verwaltung von Lifecycle-Nährstoffplänen, die alle Phasen einer Pflanze abdecken — von Keimung bis Ernte — mit konkreten Zielwerten, Produkten, Dosierungen und Zeitplänen.

- **Frei erstellbar:** Nutzer-definierte Pläne, unabhängig von Species (z.B. "Tomato Heavy Coco", "Auto Light Feed", "Organic Veg Cycle")
- **Phasenabdeckung:** Jeder Plan enthält Phase-Entries für alle relevanten Wachstumsphasen mit spezifischen NPK-Zielen, EC/pH-Bereichen und Düngerzuweisungen
- **Substrat-Empfehlung:** Optional kann ein empfohlener Substrattyp hinterlegt werden (nicht erzwungen)
- **Klonen/Varianten-Funktion:** Bestehende Pläne können als Deep-Copy geklont und unabhängig angepasst werden
- **Zuweisung zu PlantInstance:** Ein Plan wird 1:1 einer PlantInstance zugewiesen (wechselbar). Das System leitet daraus die aktuellen Dosierungen für die jeweilige Phase ab
- **Template-System:** Pläne können als Template markiert werden, um als Vorlage für andere Nutzer zu dienen

**Gantt-Diagramm-Visualisierung (Nährstoffplan-Timeline):**

**User Story:** "Als Gärtner möchte ich meinen Nährstoffplan als Gantt-Diagramm sehen, damit ich auf einen Blick erkenne, welche Dünger in welcher Phase über welchen Zeitraum eingesetzt werden — und bei Hover auf eine Phase die vollständigen Details erhalte."

**Beschreibung:**
Das System stellt jeden Nährstoffplan als interaktives Gantt-Diagramm dar. Die X-Achse bildet den Wochen-Zeitstrahl des gesamten Plans ab (`week_start` bis `week_end` über alle Phase-Entries), die Y-Achse listet alle im Plan genutzten Dünger auf.

**Diagramm-Aufbau:**
- **X-Achse (Zeitstrahl):** Wochen von `min(week_start)` bis `max(week_end)` aller Phase-Entries. Jede Woche ist eine Spalte. Phasengrenzen werden durch vertikale Trennlinien oder Farbwechsel im Hintergrund visualisiert
- **Y-Achse (Dünger-Zeilen):** Jeder im Plan genutzte Dünger (`FertilizerDosage.fertilizer_key`) erhält eine eigene Zeile. Der Düngername wird aus dem Fertilizer-Katalog aufgelöst (`brand` + `product_name`)
- **Balken:** Pro Dünger und Phase-Entry ein horizontaler Balken von `week_start` bis `week_end`. Die Balkenbeschriftung zeigt die Dosierung (`ml_per_liter`). Optionale Dünger (`optional: true`) werden mit gestricheltem Rahmen oder reduzierter Opazität dargestellt
- **Phasen-Farbcodierung:** Jeder Balken erhält die Farbe der zugehörigen Wachstumsphase (z.B. Germination=grün, Seedling=hellgrün, Vegetative=blau, Flowering=lila, Harvest=orange). Die Phasennamen werden als Legende und optional als Hintergrund-Bänder über dem Zeitstrahl angezeigt
- **Phasen-Header-Zeile:** Über den Dünger-Zeilen wird eine zusammenfassende Zeile dargestellt, die jede Phase als durchgehenden Balken über ihren Wochenzeitraum zeigt — mit Phasenname, Ziel-EC und Ziel-pH als Beschriftung

**Hover-Tooltip (Phase-Detail):**
Wenn der Nutzer mit der Maus über einen Phasen-Balken (Header-Zeile) oder einen Dünger-Balken fährt, erscheint ein Tooltip mit den vollständigen Details des zugehörigen Phase-Entry:
- **Phasenname** (übersetzt) und Wochenzeitraum (`Woche X–Y`)
- **Zielwerte:** EC (mS), pH, NPK-Ratio (N-P-K)
- **Optionale Nährstoffe:** Calcium (ppm), Magnesium (ppm) — sofern definiert
- **Fütterungsplan:** Frequenz pro Woche, Volumen pro Fütterung (Liter) — sofern definiert
- **Alle Dünger der Phase:** Tabellarische Auflistung aller `fertilizer_dosages` mit Düngername, Dosierung (ml/L), optional-Flag und `mixing_priority` (Reihenfolge)
- **Notizen:** Phase-Entry-Notizen — sofern vorhanden
- **EC-Budget-Status:** Wenn Validierungsdaten vorliegen (`PlanValidationResult.ec_budgets`), wird der EC-Budget-Status angezeigt (✓ gültig / ✗ Abweichung mit Delta)

**Interaktion:**
- **Responsive:** Das Diagramm passt sich der verfügbaren Breite an. Bei vielen Wochen (>16) wird horizontal gescrollt
- **Legende:** Unterhalb oder seitlich des Diagramms wird eine Phasen-Farbcodierungs-Legende angezeigt
- **Lücken-Erkennung:** Wochen ohne Phase-Entry werden als leere Spalten (grauer Hintergrund) dargestellt, um fehlende Phasenabdeckung visuell hervorzuheben
- **Überlappungs-Erkennung:** Überlappende Phase-Entries werden als gestapelte Balken dargestellt, mit visueller Warnung (roter Rahmen)

**Integration in NutrientPlanDetailPage:**
Das Gantt-Diagramm wird als zusätzlicher Tab „Zeitplan" (Timeline) auf der NutrientPlanDetailPage dargestellt — neben den bestehenden Tabs für Phase-Entries, Validierung und Bearbeitung. Alternativ kann das Diagramm über einen Toggle-Button (Listenansicht ↔ Gantt-Ansicht) im Phase-Entries-Tab eingeblendet werden.

**Abgrenzung NutrientProfile vs. NutrientPlan:**

| Aspekt | NutrientProfile (REQ-003) | NutrientPlan (REQ-004) |
|--------|---------------------------|------------------------|
| Scope | Species-gebunden, wissenschaftlich | Nutzer-definiert, praxisorientiert |
| Inhalt | Nur Zielwerte (NPK-Ratio, EC, pH) | Zielwerte + konkrete Produkte + Dosierungen + Zeitplan |
| Erstellung | Automatisch aus Species-Daten | Manuell durch Nutzer |
| Zuordnung | Species → NutrientProfile | PlantInstance → NutrientPlan |
| Zweck | "Was braucht die Pflanze?" | "Wie dünge ich konkret?" |

## 2. ArangoDB-Modellierung

### Document-Collections:
- **`Fertilizer`** - Dünger-Produkt
  - Properties:
    - `brand: str` (z.B. "General Hydroponics")
    - `product_name: str` (z.B. "FloraGro")
    - `type: Literal['base', 'supplement', 'booster', 'biological', 'ph_adjuster']`
    - `is_organic: bool` (Organisches Produkt — z.B. Komposttee, Wurmhumus, Fischemulsion)
    - `tank_safe: bool` (Kann sicher über Tank/Tropfer/Pumpen appliziert werden — `false` bei organischen Feststoffen, dickflüssigen Extrakten oder Produkten mit Schwebstoffen, die Tropfer verstopfen oder Biofilm im Tank verursachen)
    - `recommended_application: Literal['fertigation', 'drench', 'foliar', 'top_dress', 'any']` (Empfohlene Applikationsmethode — Default: `'any'` für tank-sichere Produkte, `'drench'` für nicht-tanksichere Flüssigdünger, `'top_dress'` für Feststoffe)
    - `npk_ratio: tuple[float, float, float]` (Analysewerte in %)
    - `ec_contribution_per_ml: float` (mS pro ml/L)
    - `mixing_priority: int` (1=zuerst, 100=zuletzt)
    - `ph_effect: Literal['acidic', 'alkaline', 'neutral']`
    - `shelf_life_days: int`
    - `storage_temp_range: tuple[float, float]`
    <!-- Quelle: Outdoor-Garden-Planner Review G-007 -->
    - `application_rate_g_per_m2: Optional[float]` (Gramm pro m² für Feststoff-Dünger)
    - `application_rate_l_per_m2: Optional[float]` (Liter pro m² für Kompost/Mulch)
    - `dilution_ratio: Optional[str]` (Verdünnungsverhältnis für Jauchen, z.B. "1:10")
    - `application_season: Optional[list[Literal['spring', 'summer', 'autumn', 'winter']]]`
    - `nutrient_release_speed: Literal['immediate', 'weeks', 'months', 'season_long'] = 'immediate'`
    - `suitable_for_demand_level: Optional[list[Literal['heavy_feeder', 'medium_feeder', 'light_feeder']]]` (Für welche Nährstoffbedarfs-Stufe geeignet)
    - `homemade: bool = False` (Selbst hergestellt — Brennnesseljauche, Kompost, Bokashi)
    - `homemade_recipe: Optional[str]` (Herstellungsanleitung für homemade Dünger)

- **`Component`** - Einzelner Nährstoff
  - Properties:
    - `name: str` (z.B. "Nitrogen", "Calcium", "Iron")
    - `chemical_form: str` (z.B. "NO3-", "Ca2+", "Fe-EDTA")
    - `concentration_percent: float`
    - `bioavailability: Literal['immediate', 'slow_release', 'microbial_dependent']`

- **`MixingInstruction`** - Spezifische Misch-Regel
  - Properties:
    - `instruction_text: str`
    - `wait_time_minutes: Optional[int]` (Wartezeit nach Zugabe)
    - `mixing_method: Literal['stir', 'circulate', 'rest']`
    - `temperature_sensitive: bool`

- **`Incompatibility`** - Unverträglichkeiten
  - Properties:
    - `reason: str` (z.B. "Calcium-Phosphat-Ausfällung")
    - `severity: Literal['critical', 'warning', 'minor']`
    - `workaround: Optional[str]`

- **`FeedingSchedule`** - Wochenplan
  - Properties:
    - `week_number: int`
    - `phase: str`
    - `frequency_per_week: int`
    - `volume_per_feeding_liters: float`

- **`FeedingEvent`** - Tatsächliche Düngung/Bewässerung auf Pflanzenlevel
  - **Abgrenzung zu WateringEvent (REQ-014):** Ein `FeedingEvent` dokumentiert die Nährstoffaufnahme pro **einzelner Pflanze** (für Bilanzierung und NutrientPlan-Tracking). Ein `WateringEvent` (REQ-014) dokumentiert den physischen **Gießvorgang** auf Slot-Ebene (kann mehrere Pflanzen umfassen). Ein WateringEvent erzeugt automatisch FeedingEvents für jede betroffene PlantInstance.
  - Properties:
    - `timestamp: datetime`
    - `watering_event_key: Optional[str]` (Referenz auf WateringEvent aus REQ-014, wenn das FeedingEvent automatisch aus einem Gießvorgang erzeugt wurde)
    - `application_method: Literal['fertigation', 'drench', 'foliar', 'top_dress']` (Art der Ausbringung — `fertigation` = via Tank/Tropfer, `drench` = manuelles Gießen per Gießkanne, `foliar` = Blattdüngung per Sprüher, `top_dress` = Feststoff-Aufbringung auf Substratoberfläche)
    - `is_supplemental: bool` (Ergänzende Handdüngung zusätzlich zur Tank-Bewässerung — z.B. organische Dünger per Gießkanne bei Pflanzen, die primär über Drip versorgt werden)
    - `tank_fill_event_key: Optional[str]` (Referenz auf TankFillEvent aus REQ-014, wenn die Düngung aus einer dokumentierten Tankbefüllung stammt)
    - `volume_applied_liters: float`
    - `measured_ec_before: Optional[float]`
    - `measured_ec_after: Optional[float]`
    - `measured_ph_before: Optional[float]`
    - `measured_ph_after: Optional[float]`
    - `runoff_ec: Optional[float]` (bei Drain-to-Waste)
    - `runoff_ph: Optional[float]`

- **`NutrientPlan`** - Wiederverwendbarer Lifecycle-Nährstoffplan
  - Properties:
    - `name: str` (z.B. "Tomato Heavy Coco", "Auto Light Feed")
    - `description: Optional[str]`
    - `recommended_substrate_type: Optional[Literal['hydro', 'coco', 'soil', 'living_soil']]`
    - `author: str`
    - `is_template: bool` (als Vorlage für andere nutzbar)
    - `version: int` (Versionierung bei Änderungen)
    - `tags: list[str]` (z.B. ["organic", "autoflower", "heavy-feeder"])
    - `watering_schedule: Optional[WateringSchedule]` (Gießplan-Konfiguration für manuelle Bewässerung — siehe eingebettetes Modell unten; `null` = Plan ohne Terminplanung, rein als Dosierungsvorlage nutzbar)

- **`WateringSchedule`** - Eingebettetes Modell (kein eigenes Dokument) innerhalb von `NutrientPlan`
  - Beschreibung: Definiert *wann* und *wie* manuell gegossen wird. Unterstützt zwei Modi: feste Wochentage (z.B. Mo/Mi/Fr) oder Intervall-basiert (z.B. alle 3 Tage). Die Kombination aus NutrientPlan (was/wieviel) und WateringSchedule (wann/wie) ergibt einen vollständigen Gießplan.
  - Properties:
    - `schedule_mode: Literal['weekdays', 'interval']` (Terminplanungs-Modus)
    - `weekday_schedule: Optional[list[int]]` (0=Montag..6=Sonntag; Pflicht bei `mode='weekdays'`, ignoriert bei `mode='interval'`; 1–7 Tage wählbar, keine Duplikate)
    - `interval_days: Optional[int]` (1–90 Tage; Pflicht bei `mode='interval'`, ignoriert bei `mode='weekdays'`)
    - `preferred_time: Optional[str]` (HH:MM Format, z.B. "08:00"; für Erinnerungs-Timing und Task-`scheduled_time`)
    - `application_method: Literal['drench', 'foliar', 'top_dress']` (Default: `'drench'`; `'fertigation'` ist bewusst ausgeschlossen — Tank-Bewässerung wird über REQ-014 TankFillEvent gesteuert, nicht über den manuellen Gießplan)
    - `reminder_hours_before: int` (0–24, Default: 2; Stunden vor `preferred_time`, zu der die Erinnerung/Task erscheinen soll; 0 = Erinnerung zum Gießzeitpunkt)
  - Validatoren:
    - `mode='weekdays'` → `weekday_schedule` muss nicht-leer sein, alle Werte 0–6, keine Duplikate
    - `mode='interval'` → `interval_days` muss gesetzt sein, 1–90
    - `preferred_time` → Format-Validierung HH:MM (00:00–23:59)
    - `application_method` → darf NICHT `'fertigation'` sein (Geschäftsregel: Fertigation = Tank-basiert, nicht manuell schedulbar)

- **`NutrientPlanPhaseEntry`** - Phasen-spezifische Konfiguration innerhalb eines Plans
  - Properties:
    - `phase_name: Literal['germination', 'seedling', 'vegetative', 'flowering', 'harvest']`
    - `sequence_order: int` (Reihenfolge innerhalb des Plans)
    - `week_start: int` (ab welcher Woche)
    - `week_end: int` (bis welcher Woche)
    - `npk_ratio: tuple[float, float, float]` (Ziel-NPK-Verhältnis)
    - `target_ec_ms: float` (Ziel-EC für diese Phase)
    - `target_ph: float` (Ziel-pH für diese Phase)
    - `calcium_ppm: Optional[float]`
    - `magnesium_ppm: Optional[float]`
    - `sulfur_ppm: Optional[float]`
    - `iron_ppm: Optional[float]` (Fe-Mangel = häufigste Mikronährstoff-Chlorose in Hydro/Coco)
    - `boron_ppm: Optional[float]` (B-Mangel = Wachstumsstörungen, besonders bei Ca-reicher Düngung)
    - `feeding_frequency_per_week: int`
    - `volume_per_feeding_liters: float`
    - `notes: Optional[str]`

- **`FertilizerStock`** - Inventar-Tracking
  - Properties:
    - `current_volume_ml: float`
    - `purchase_date: date`
    - `expiry_date: date`
    - `batch_number: str`
    - `cost_per_liter: float`

### Edge-Collections:
```
CONTAINS:              Fertilizer -> Component            {amount_percent: float}
INCOMPATIBLE_WITH:     Fertilizer -> Fertilizer           {severity: str, reason: str}
MIXED_AFTER:           Fertilizer -> Fertilizer           {min_wait_minutes: int}
USES_DOSAGE:           GrowthPhase -> Fertilizer          {ml_per_liter: float, frequency: str}
FED_BY:                PlantInstance -> FeedingEvent       {}
USED:                  FeedingEvent -> Fertilizer          {ml_applied: float}
TRIGGERED_BY:          FeedingEvent -> WateringEvent       {}  // REQ-014 — FeedingEvent wurde aus WateringEvent erzeugt
PRESCRIBES:            FeedingSchedule -> Fertilizer       {}
HAS_STOCK:             Fertilizer -> FertilizerStock       {}
FOR_FERTILIZER:        MixingInstruction -> Fertilizer     {}

// Nährstoffplan-Verwaltung
HAS_PHASE_ENTRY:       NutrientPlan -> NutrientPlanPhaseEntry      {sequence: int}
USES_FERTILIZER:       NutrientPlanPhaseEntry -> Fertilizer        {ml_per_liter: float, optional: bool}
FOLLOWS_PLAN:          PlantInstance -> NutrientPlan               {assigned_at: datetime, assigned_by: str}
CLONED_FROM:           NutrientPlan -> NutrientPlan                {cloned_at: datetime}

// Gießplan-Workflow: PlantingRun → NutrientPlan Zuweisung (REQ-013 Integration)
RUN_FOLLOWS_PLAN:      PlantingRun -> NutrientPlan                 {assigned_at: datetime, assigned_by: str}
// Abgrenzung zu FOLLOWS_PLAN: FOLLOWS_PLAN ist die 1:1-Zuweisung einer einzelnen
// PlantInstance zu einem NutrientPlan. RUN_FOLLOWS_PLAN ist die Run-weite Zuweisung,
// die als Default für alle Pflanzen im Run gilt. Bei create_plants (REQ-013) werden
// automatisch FOLLOWS_PLAN-Edges für die einzelnen Pflanzen erzeugt.
```

### AQL-Beispiellogik:

**Misch-Reihenfolge für aktuelle Phase generieren:**
```aql
// Aktuelle Phase der Pflanze ermitteln
LET plant = DOCUMENT(CONCAT("PlantInstance/", @plant_id))
LET phase = FIRST(
  FOR v, e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    FILTER IS_SAME_COLLECTION("GrowthPhase", v)
    FILTER e._id LIKE "CURRENT_PHASE/%"
    RETURN v
)

// Dünger mit Dosierungen für diese Phase laden
FOR v, e IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
  FILTER IS_SAME_COLLECTION("Fertilizer", v)
  FILTER e._id LIKE "USES_DOSAGE/%"
  LET fert = v
  LET dosage = e

  // Misch-Reihenfolge: welche Dünger müssen vorher gemischt werden?
  LET mix_after = (
    FOR before IN 1..1 OUTBOUND fert GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION("Fertilizer", before)
      FILTER before._id LIKE "MIXED_AFTER/%"
      RETURN DISTINCT before.product_name
  )

  // Inkompatible Dünger, die ebenfalls in dieser Phase verwendet werden
  LET incompatibilities = (
    FOR incomp IN 1..1 OUTBOUND fert GRAPH 'kamerplanter_graph'
      FILTER IS_SAME_COLLECTION("Fertilizer", incomp)
      FILTER incomp._id LIKE "INCOMPATIBLE_WITH/%"
      FILTER LENGTH(
        FOR v2, e2 IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
          FILTER v2._id == incomp._id
          FILTER e2._id LIKE "USES_DOSAGE/%"
          RETURN 1
      ) > 0
      RETURN DISTINCT incomp.product_name
  )

  SORT fert.mixing_priority ASC
  RETURN {
    fertilizer: fert.product_name,
    dosage: dosage.ml_per_liter,
    priority: fert.mixing_priority,
    ec_contrib: fert.ec_contribution_per_ml,
    incompatibilities: incompatibilities,
    mix_after: mix_after
  }
```

**EC-Budget-Aufteilung berechnen:**
```aql
// Phase mit NutrientProfile laden
LET phase = FIRST(
  FOR doc IN GrowthPhase FILTER doc.name == @phase_name RETURN doc
)
LET nutr = FIRST(
  FOR v, e IN 2..2 OUTBOUND phase REQUIRES_PROFILE, USES_NUTRIENTS
    FILTER IS_SAME_COLLECTION("NutrientProfile", v)
    RETURN v
)

// Dünger mit Dosierungen für diese Phase
LET fertilizers = (
  FOR fert, dosage IN 1..1 OUTBOUND phase USES_DOSAGE
    RETURN {
      fert: fert.product_name,
      ec_per_ml: fert.ec_contribution_per_ml,
      dosage: dosage.ml_per_liter
    }
)

LET target_ec = nutr.target_ec_ms
LET total_ec_contribution = SUM(
  FOR f IN fertilizers RETURN f.ec_per_ml * f.dosage
)
LET ec_deviation = ABS(target_ec - total_ec_contribution)

RETURN {
  target_ec: target_ec,
  total_ec_contribution: total_ec_contribution,
  ec_deviation: ec_deviation,
  status: ec_deviation > 0.2 ? 'ADJUST_DOSAGES' : 'OK',
  fertilizers: fertilizers
}
```

**Flushing-Schedule für Ernte:**
```aql
LET plant = DOCUMENT(CONCAT("PlantInstance/", @plant_id))

// Aktuelle Phase prüfen (muss Ernte erlauben)
LET phase = FIRST(
  FOR v IN 1..1 OUTBOUND plant CURRENT_PHASE
    FILTER v.allows_harvest == true
    RETURN v
)

// Substrattyp ermitteln
LET substrate_info = FIRST(
  FOR sb IN 1..1 OUTBOUND plant GROWN_IN
    FOR st IN 1..1 OUTBOUND sb USES_TYPE
      RETURN st
)
LET substrate_type = substrate_info.type

LET flush_duration_days = (
  substrate_type == 'hydro_solution' ? 10 :
  substrate_type == 'coco' ? 14 :
  substrate_type == 'soil' ? 28 :
  14
)

// Letzte Düngung ermitteln (höchster Timestamp)
LET last_feeding = FIRST(
  FOR fe IN 1..1 OUTBOUND plant FED_BY
    SORT fe.timestamp DESC
    LIMIT 1
    RETURN fe
)
LET current_ec = last_feeding.measured_ec_after

RETURN {
  flush_duration_days: flush_duration_days,
  flush_schedule: (
    FOR day IN 0..flush_duration_days
      RETURN {
        day: day,
        target_ec: current_ec * (1 - day / flush_duration_days),
        action: day < flush_duration_days / 2 ? 'Reduced dose' : 'Water only'
      }
  )
}
```

**Inventar-Warnung bei niedrigem Stock:**
```aql
FOR fert IN Fertilizer
  FOR stock IN 1..1 OUTBOUND fert HAS_STOCK
    FILTER stock.current_volume_ml < 500
       OR stock.expiry_date < DATE_ADD(DATE_NOW(), 30, "day")

    // Durchschnittliche Dosierung über alle Phasen
    LET dosages = (
      FOR phase, dosage IN 1..1 INBOUND fert USES_DOSAGE
        RETURN dosage.ml_per_liter
    )
    LET avg_dosage_per_liter = AVERAGE(dosages)

    // Anzahl Feeding-Events für diesen Dünger
    LET feeding_count = LENGTH(
      FOR fe, e IN 1..1 INBOUND fert USED
        RETURN 1
    )

    LET weeks_remaining = (
      avg_dosage_per_liter > 0 AND feeding_count > 0
        ? stock.current_volume_ml / (avg_dosage_per_liter * feeding_count * 10)
        : null
    )

    FILTER weeks_remaining != null AND weeks_remaining < 2

    SORT weeks_remaining ASC
    RETURN {
      product_name: fert.product_name,
      remaining_ml: stock.current_volume_ml,
      expiry_date: stock.expiry_date,
      weeks_remaining: weeks_remaining,
      alert: 'REORDER_NEEDED'
    }
```

**Nährstoffplan mit allen Phasen und Düngern laden:**
```aql
LET plan = DOCUMENT(CONCAT("NutrientPlan/", @plan_key))

LET phase_entries = (
  FOR entry, he IN 1..1 OUTBOUND plan HAS_PHASE_ENTRY
    LET fertilizers = (
      FOR fert, uf IN 1..1 OUTBOUND entry USES_FERTILIZER
        RETURN {
          fertilizer: fert.product_name,
          brand: fert.brand,
          ml_per_liter: uf.ml_per_liter,
          optional: uf.optional
        }
    )
    SORT he.sequence ASC
    RETURN {
      phase: entry.phase_name,
      weeks: [entry.week_start, entry.week_end],
      target_ec: entry.target_ec_ms,
      target_ph: entry.target_ph,
      npk_ratio: entry.npk_ratio,
      feeding_frequency: entry.feeding_frequency_per_week,
      fertilizers: fertilizers
    }
)

RETURN {
  plan_name: plan.name,
  substrate: plan.recommended_substrate_type,
  tags: plan.tags,
  phase_entries: phase_entries
}
```

**Aktuelle Dosierungen für PlantInstance aus zugewiesenem Plan ableiten:**
```aql
LET plant = DOCUMENT(CONCAT("PlantInstance/", @plant_key))

// Zugewiesenen Plan laden
LET plan = FIRST(
  FOR v IN 1..1 OUTBOUND plant FOLLOWS_PLAN
    RETURN v
)

// Aktuelle Phase der Pflanze
LET phase = FIRST(
  FOR v IN 1..1 OUTBOUND plant CURRENT_PHASE
    RETURN v
)

// Phase-Entry des Plans passend zur aktuellen Phase
LET entry = FIRST(
  FOR v IN 1..1 OUTBOUND plan HAS_PHASE_ENTRY
    FILTER v.phase_name == phase.name
    RETURN v
)

// Dünger-Dosierungen für diese Phase-Entry
LET dosages = (
  FOR fert, uf IN 1..1 OUTBOUND entry USES_FERTILIZER
    SORT fert.mixing_priority ASC
    RETURN {
      fertilizer: fert.product_name,
      ml_per_liter: uf.ml_per_liter,
      optional: uf.optional,
      mixing_priority: fert.mixing_priority
    }
)

RETURN {
  plant_key: plant._key,
  plan_name: plan.name,
  current_phase: entry.phase_name,
  target_ec: entry.target_ec_ms,
  target_ph: entry.target_ph,
  frequency: entry.feeding_frequency_per_week,
  volume: entry.volume_per_feeding_liters,
  dosages: dosages
}
```

**Plan klonen (Deep Copy):**
```aql
LET source_plan = DOCUMENT(CONCAT("NutrientPlan/", @source_plan_key))

// 1. Neuen Plan erstellen
LET new_plan = FIRST(
  INSERT {
    name: CONCAT(source_plan.name, " (Kopie)"),
    description: source_plan.description,
    recommended_substrate_type: source_plan.recommended_substrate_type,
    author: @current_user,
    is_template: false,
    version: 1,
    tags: source_plan.tags,
    created_at: DATE_ISO8601(DATE_NOW())
  } INTO NutrientPlan RETURN NEW
)

// 2. Phase-Entries kopieren und Edges erstellen
LET copied_entries = (
  FOR entry, he IN 1..1 OUTBOUND source_plan HAS_PHASE_ENTRY
    LET new_entry = FIRST(
      INSERT UNSET(entry, "_key", "_id", "_rev") INTO NutrientPlanPhaseEntry RETURN NEW
    )
    // HAS_PHASE_ENTRY-Edge zum neuen Plan
    LET edge = FIRST(
      INSERT { _from: new_plan._id, _to: new_entry._id, sequence: entry.sequence_order }
        INTO HAS_PHASE_ENTRY RETURN NEW
    )
    // Dünger-Zuweisungen kopieren
    LET fert_edges = (
      FOR fert, uf IN 1..1 OUTBOUND entry USES_FERTILIZER
        INSERT { _from: new_entry._id, _to: fert._id, ml_per_liter: uf.ml_per_liter, optional: uf.optional }
          INTO USES_FERTILIZER RETURN NEW
    )
    RETURN new_entry
)

// 3. CLONED_FROM-Edge setzen
INSERT { _from: new_plan._id, _to: source_plan._id, cloned_at: DATE_ISO8601(DATE_NOW()) }
  INTO CLONED_FROM

RETURN new_plan
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**0. Gießplan-Scheduling (WateringSchedule):**
```python
from enum import StrEnum
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional
from datetime import date, time

class ScheduleMode(StrEnum):
    """Terminplanungs-Modus für Gießpläne"""
    WEEKDAYS = "weekdays"   # Feste Wochentage (z.B. Mo/Mi/Fr)
    INTERVAL = "interval"   # Intervall-basiert (z.B. alle 3 Tage)

class ApplicationMethod(StrEnum):
    """Applikationsmethode (Subset für manuelles Gießen)"""
    DRENCH = "drench"       # Gießkanne — Substrat-Durchspülung
    FOLIAR = "foliar"       # Blattdüngung per Sprüher
    TOP_DRESS = "top_dress" # Feststoff-Aufbringung auf Substrat

class WateringSchedule(BaseModel):
    """
    Gießplan-Konfiguration: Wann und wie manuell gegossen wird.
    Eingebettetes Modell innerhalb von NutrientPlan.
    """

    schedule_mode: ScheduleMode
    weekday_schedule: Optional[list[int]] = Field(
        None,
        description="Wochentage (0=Mo..6=So). Pflicht bei mode='weekdays'."
    )
    interval_days: Optional[int] = Field(
        None, ge=1, le=90,
        description="Gieß-Intervall in Tagen. Pflicht bei mode='interval'."
    )
    preferred_time: Optional[str] = Field(
        None,
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="Bevorzugte Gießzeit im Format HH:MM"
    )
    application_method: ApplicationMethod = Field(
        default=ApplicationMethod.DRENCH,
        description="Applikationsmethode für manuelle Bewässerung"
    )
    reminder_hours_before: int = Field(
        default=2, ge=0, le=24,
        description="Stunden vor preferred_time für Erinnerung"
    )

    @model_validator(mode='after')
    def validate_mode_fields(self):
        """Mode-abhängige Pflichtfelder prüfen"""
        if self.schedule_mode == ScheduleMode.WEEKDAYS:
            if not self.weekday_schedule:
                raise ValueError("weekday_schedule ist Pflicht bei mode='weekdays'")
            if len(self.weekday_schedule) < 1 or len(self.weekday_schedule) > 7:
                raise ValueError("weekday_schedule muss 1–7 Tage enthalten")
            if len(set(self.weekday_schedule)) != len(self.weekday_schedule):
                raise ValueError("weekday_schedule darf keine Duplikate enthalten")
            if not all(0 <= d <= 6 for d in self.weekday_schedule):
                raise ValueError("Wochentage müssen 0–6 sein (Mo–So)")
        elif self.schedule_mode == ScheduleMode.INTERVAL:
            if self.interval_days is None:
                raise ValueError("interval_days ist Pflicht bei mode='interval'")
        return self
```

**1. Nutrient Solution Calculator:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Tuple
from datetime import datetime

class FertilizerComponent(BaseModel):
    """Einzelner Dünger mit allen Eigenschaften"""
    
    id: str
    product_name: str
    brand: str
    npk: Tuple[float, float, float]  # N-P-K in %
    ec_contribution_per_ml: float = Field(ge=0, le=1.0, description="mS pro ml/L")
    mixing_priority: int = Field(ge=1, le=100)
    incompatible_with: list[str] = Field(default_factory=list)
    ph_effect: Literal['acidic', 'alkaline', 'neutral'] = 'neutral'
    type: Literal['base', 'supplement', 'booster', 'biological', 'ph_adjuster']
    
    @field_validator('npk')
    @classmethod
    def validate_npk_sum(cls, v):
        n, p, k = v
        total = n + p + k
        if total > 100:
            raise ValueError(f"NPK-Summe ({total}%) darf 100% nicht überschreiten")
        return v

class NutrientSolutionCalculator(BaseModel):
    """Berechnet optimale Mischverhältnisse"""
    
    target_volume_liters: float = Field(gt=0, le=10000)
    target_ec_ms: float = Field(ge=0.5, le=4.0)
    target_ph: float = Field(ge=4.0, le=8.0)
    base_water_ec_ms: float = Field(default=0.0, ge=0, le=1.0)
    base_water_ph: float = Field(default=7.0, ge=4.0, le=9.0)
    base_water_alkalinity_ppm: Optional[float] = Field(
        default=None, ge=0, le=500,
        description="Karbonat-Alkalinität (CaCO₃-Äquivalent) in ppm. "
                    "Bestimmt die Pufferkapazität des Wassers und damit die "
                    "benötigte Menge pH-Korrektur. Weiches Wasser ~30 ppm, "
                    "hartes Wasser ~250 ppm."
    )
    fertilizers: list[FertilizerComponent]
    substrate_type: Literal['hydro', 'coco', 'soil', 'living_soil']
    
    @field_validator('target_ec_ms')
    @classmethod
    def validate_ec_for_substrate(cls, v, info):
        substrate = info.data.get('substrate_type')
        ec_limits = {
            'hydro': (0.8, 3.0),
            'coco': (0.8, 2.2),
            'soil': (0.4, 1.6),
            'living_soil': (0.0, 1.5)  # Komposttee/Wurmhumus-Drench kann 1.0-1.5 erreichen
        }
        min_ec, max_ec = ec_limits.get(substrate, (0.5, 3.0))
        if not (min_ec <= v <= max_ec):
            raise ValueError(f"EC {v} außerhalb empfohlenen Bereichs für {substrate}: {min_ec}-{max_ec} mS")
        return v
    
    def calculate_dosages(self) -> dict:
        """
        Hauptfunktion: Berechnet ml pro Dünger
        Returns: Detailliertes Mischprotokoll
        """
        
        # 1. Sortiere nach Mischreihenfolge
        sorted_ferts = sorted(self.fertilizers, key=lambda f: f.mixing_priority)
        
        # 2. Verfügbares EC-Budget
        available_ec = self.target_ec_ms - self.base_water_ec_ms
        if available_ec < 0:
            raise ValueError(f"Wasser-EC ({self.base_water_ec_ms}) bereits über Ziel ({self.target_ec_ms})")
        
        # 3. Prüfe auf Inkompatibilitäten
        incompatibility_warnings = self._check_incompatibilities(sorted_ferts)
        
        # 4. Berechne Dosierungen
        dosages = []
        accumulated_ec = self.base_water_ec_ms

        for fert in sorted_ferts:
            # pH-Adjuster werden separat in _estimate_ph_adjustment behandelt,
            # aber ihr EC-Beitrag wird dort geschätzt und im Ergebnis ausgewiesen
            if fert.type == 'ph_adjuster':
                continue
            
            # EC-Beitrag dieses Düngers
            # Vereinfachte Verteilung: Proportional zu NPK-Summe
            npk_sum = sum(fert.npk)
            total_npk = sum(sum(f.npk) for f in sorted_ferts if f.type != 'ph_adjuster')
            
            if total_npk > 0:
                ec_allocation = available_ec * (npk_sum / total_npk)
            else:
                ec_allocation = 0
            
            # Berechne ml/L basierend auf EC-Beitrag
            if fert.ec_contribution_per_ml > 0:
                ml_per_liter = min(
                    ec_allocation / fert.ec_contribution_per_ml,
                    20.0  # Max 20ml/L Sicherheitslimit
                )
            else:
                ml_per_liter = 0
            
            total_ml = ml_per_liter * self.target_volume_liters
            ec_contrib = ml_per_liter * fert.ec_contribution_per_ml
            accumulated_ec += ec_contrib
            
            dosages.append({
                'fertilizer_id': fert.id,
                'product_name': fert.product_name,
                'ml_per_liter': round(ml_per_liter, 2),
                'total_ml': round(total_ml, 1),
                'add_order': fert.mixing_priority,
                'ec_contribution': round(ec_contrib, 3),
                'npk_contribution': tuple(round(ml_per_liter * n / 100, 3) for n in fert.npk)
            })
        
        # 5. pH-Korrektur schätzen
        ph_adjustment = self._estimate_ph_adjustment(
            self.base_water_ph,
            self.target_ph,
            sorted_ferts,
            dosages
        )
        
        # EC-Beitrag der pH-Korrektur einrechnen (typisch 0.02-0.05 mS/ml)
        ph_ec = ph_adjustment.get('estimated_ec_contribution', 0.0)
        total_ec = accumulated_ec + ph_ec

        return {
            'dosages': dosages,
            'water_volume_liters': self.target_volume_liters,
            'base_water_ec': self.base_water_ec_ms,
            'target_ec': self.target_ec_ms,
            'calculated_ec': round(total_ec, 2),
            'calculated_ec_without_ph': round(accumulated_ec, 2),
            'ph_ec_contribution': round(ph_ec, 3),
            'ec_deviation': round(abs(self.target_ec_ms - total_ec), 3),
            'ph_adjustment': ph_adjustment,
            'incompatibility_warnings': incompatibility_warnings,
            'mixing_instructions': self._generate_step_by_step(dosages, ph_adjustment),
            'total_cost': self._calculate_cost(dosages)
        }
    
    def _check_incompatibilities(self, fertilizers: list[FertilizerComponent]) -> list[dict]:
        """Prüft auf chemische Unverträglichkeiten"""
        warnings = []
        
        for i, fert1 in enumerate(fertilizers):
            for fert2 in fertilizers[i+1:]:
                if fert2.id in fert1.incompatible_with:
                    warnings.append({
                        'fert1': fert1.product_name,
                        'fert2': fert2.product_name,
                        'severity': 'CRITICAL',
                        'message': f"NICHT zusammen mischen: {fert1.product_name} + {fert2.product_name}"
                    })
        
        return warnings
    
    def _estimate_ph_adjustment(
        self,
        base_ph: float,
        target_ph: float,
        fertilizers: list[FertilizerComponent],
        dosages: list[dict]
    ) -> dict:
        """
        Schätzt benötigte pH-Korrektur.

        ACHTUNG: pH-Verschiebungen sind logarithmisch, nicht linear.
        Die Pufferkapazität (Alkalinität/KH) des Wassers bestimmt maßgeblich,
        wie stark eine Säure/Base den pH verschiebt:
        - Weiches Wasser (30 ppm CaCO₃): 1ml pH-Down → pH-Shift 1.0-2.0
        - Hartes Wasser (300 ppm CaCO₃): 1ml pH-Down → pH-Shift 0.1-0.2

        Diese Schätzung ist daher nur eine Grob-Orientierung.
        Messung nach Zugabe ist OBLIGATORISCH.
        """

        # Berechne pH-Shift durch Dünger (grobe Näherung)
        ph_shift = 0
        for fert, dosage in zip(fertilizers, dosages):
            if fert.ph_effect == 'acidic':
                ph_shift -= dosage['ml_per_liter'] * 0.05
            elif fert.ph_effect == 'alkaline':
                ph_shift += dosage['ml_per_liter'] * 0.05

        estimated_ph = base_ph + ph_shift
        ph_difference = target_ph - estimated_ph

        # Alkalinität-basierte Skalierung der benötigten pH-Korrektur
        alkalinity = self.base_water_alkalinity_ppm
        if alkalinity is not None and alkalinity > 0:
            # Höhere Alkalinität → mehr Säure/Base nötig
            buffer_factor = alkalinity / 100  # Normalisiert auf ~1.0 bei 100 ppm
        else:
            buffer_factor = 1.0  # Default ohne Alkalinitätsdaten

        if abs(ph_difference) > 0.1:
            adjuster_type = 'pH Down' if ph_difference < 0 else 'pH Up'
            ml_needed = abs(ph_difference) * 2 * self.target_volume_liters / 10 * buffer_factor

            # Geschätzter EC-Beitrag der pH-Korrektur (typisch 0.02-0.05 mS/ml)
            ph_ec_contribution = ml_needed / self.target_volume_liters * 0.03

            return {
                'needed': True,
                'type': adjuster_type,
                'estimated_ml': round(ml_needed, 1),
                'estimated_ec_contribution': round(ph_ec_contribution, 3),
                'current_ph_estimate': round(estimated_ph, 2),
                'target_ph': target_ph,
                'alkalinity_known': alkalinity is not None,
                'confidence': 'low' if alkalinity is None else 'medium',
                'note': 'GROB-SCHÄTZUNG: pH-Korrektur schrittweise zugeben und nach '
                        'jeder Zugabe messen! Die tatsächliche Menge hängt stark von '
                        'der Wasserhärte/Alkalinität ab.'
            }

        return {
            'needed': False,
            'current_ph_estimate': round(estimated_ph, 2),
            'target_ph': target_ph
        }
    
    def _generate_step_by_step(
        self,
        dosages: list[dict],
        ph_adjustment: dict
    ) -> list[str]:
        """Generiert menschenlesbare Misch-Anleitung"""
        
        instructions = [
            f"1. Fülle {self.target_volume_liters}L Wasser in Tank/Gießkanne",
            f"   - Wasser-Temperatur: 18-22°C optimal",
            f"   - Basis-EC: {self.base_water_ec_ms} mS, Basis-pH: {self.base_water_ph}"
        ]
        
        for idx, dosage in enumerate(dosages, start=2):
            instructions.append(
                f"{idx}. Füge {dosage['total_ml']}ml {dosage['product_name']} hinzu "
                f"({dosage['ml_per_liter']}ml/L)"
            )
            instructions.append(f"   - GRÜNDLICH RÜHREN (30 Sekunden)")
            
            if idx == 2:  # Nach erstem Dünger
                instructions.append(f"   - Warte 2 Minuten vor nächster Zugabe")
        
        if ph_adjustment['needed']:
            instructions.append(
                f"{len(dosages)+2}. pH-Korrektur: {ph_adjustment['type']} "
                f"~{ph_adjustment['estimated_ml']}ml (schrittweise zugeben!)"
            )
            instructions.append(f"   - Ziel-pH: {ph_adjustment['target_ph']}")
        
        instructions.append(f"{len(dosages)+3}. FINALE MESSUNG:")
        instructions.append(f"   - EC: {self.target_ec_ms} mS (±0.2)")
        instructions.append(f"   - pH: {self.target_ph} (±0.3)")
        
        return instructions
    
    def _calculate_cost(self, dosages: list[dict]) -> float:
        """Berechnet Kosten pro Düngung (wenn Preise hinterlegt)"""
        # Placeholder für Kostenberechnung
        return 0.0

class FlushingProtocol(BaseModel):
    """Nährstoffreduktion vor Ernte"""
    
    plant_id: str
    current_ec: float = Field(ge=0, le=4.0)
    days_until_harvest: int = Field(ge=0, le=60)
    substrate_type: Literal['hydro', 'coco', 'soil']
    
    def get_schedule(self) -> dict:
        """Erstellt schrittweisen Flush-Plan"""
        
        # Flush-Dauer nach Substrat
        durations = {
            'hydro': {'min': 7, 'optimal': 10, 'max': 14},
            'coco': {'min': 10, 'optimal': 14, 'max': 21},
            'soil': {'min': 21, 'optimal': 28, 'max': 42}  # Hohe CEC bindet Salze stärker
        }
        
        duration_map = durations[self.substrate_type]
        flush_days = duration_map['optimal']
        
        # Validierung
        if self.days_until_harvest < duration_map['min']:
            return {
                'status': 'TOO_LATE',
                'warning': f"Nur noch {self.days_until_harvest} Tage - Minimum: {duration_map['min']}",
                'recommendation': 'Notfall-Flush (nur Wasser, täglich spülen)'
            }
        
        if self.days_until_harvest > flush_days:
            flush_days = min(self.days_until_harvest, duration_map['max'])
        
        # Gradueller EC-Abbau
        steps = []
        ec_reduction_per_day = self.current_ec / flush_days
        
        for day in range(flush_days + 1):
            target_ec = max(0, self.current_ec - (ec_reduction_per_day * day))
            
            # Strategie basierend auf Tag
            if day == 0:
                action = f"Letzte normale Düngung (EC {target_ec:.1f})"
                dosage_percent = 100
            elif day <= flush_days // 3:
                action = f"Reduzierte Dosis (EC {target_ec:.1f})"
                dosage_percent = 50
            elif day <= 2 * flush_days // 3:
                action = f"Minimale Dosis (EC {target_ec:.1f})"
                dosage_percent = 25
            else:
                action = "Nur Wasser (EC ~0.0)"
                dosage_percent = 0
                target_ec = 0.0
            
            steps.append({
                'day': day,
                'days_to_harvest': self.days_until_harvest - day,
                'target_ec': round(target_ec, 2),
                'action': action,
                'dosage_percent': dosage_percent,
                'measurement_required': day % 3 == 0  # Alle 3 Tage messen
            })
        
        return {
            'status': 'OK',
            'total_flush_days': flush_days,
            'start_ec': self.current_ec,
            'substrate_type': self.substrate_type,
            'schedule': steps,
            'notes': [
                f"Starte Flush {flush_days} Tage vor Ernte",
                "Täglich wässern mit pH-korrigiertem Wasser",
                "Runoff-EC überwachen (sollte < 0.5 mS werden)",
                "Blätter beginnen zu vergilben = Normal!"
            ]
        }

class ECBudgetOptimizer(BaseModel):
    """Optimiert Dünger-Dosierungen für Ziel-EC"""
    
    target_ec: float
    current_ec: float
    fertilizers: list[FertilizerComponent]
    optimization_goal: Literal['match_ec', 'match_npk_ratio', 'minimize_cost']
    
    def optimize(self, target_npk_ratio: Optional[Tuple[int, int, int]] = None) -> dict:
        """
        Iterative Optimierung der Dosierungen
        """
        
        if self.optimization_goal == 'match_ec':
            return self._optimize_for_ec()
        elif self.optimization_goal == 'match_npk_ratio':
            if not target_npk_ratio:
                raise ValueError("NPK-Ratio erforderlich für match_npk_ratio")
            return self._optimize_for_npk(target_npk_ratio)
        else:
            return self._optimize_for_cost()
    
    def _optimize_for_ec(self) -> dict:
        """Einfache proportionale Skalierung"""
        
        ec_gap = self.target_ec - self.current_ec
        
        # Berechne aktuelle EC-Summe der Dünger
        total_ec_contrib = sum(f.ec_contribution_per_ml for f in self.fertilizers)
        
        if total_ec_contrib == 0:
            return {'error': 'Keine EC-Beiträge definiert'}
        
        # Skalierungsfaktor
        scale_factor = ec_gap / total_ec_contrib
        
        optimized = []
        for fert in self.fertilizers:
            ml_per_liter = fert.ec_contribution_per_ml * scale_factor
            optimized.append({
                'fertilizer': fert.product_name,
                'ml_per_liter': round(ml_per_liter, 2),
                'ec_contribution': round(fert.ec_contribution_per_ml * ml_per_liter, 3)
            })
        
        return {
            'method': 'ec_optimization',
            'target_ec': self.target_ec,
            'optimized_dosages': optimized,
            'estimated_total_ec': round(self.current_ec + sum(d['ec_contribution'] for d in optimized), 2)
        }
    
    def _optimize_for_npk(self, target_ratio: Tuple[int, int, int]) -> dict:
        """Optimiert für NPK-Verhältnis (komplex - hier vereinfacht)"""
        # Placeholder für lineare Optimierung
        return {'status': 'Not implemented - requires scipy.optimize'}
    
    def _optimize_for_cost(self) -> dict:
        """Minimiert Kosten bei Einhaltung der EC"""
        return {'status': 'Not implemented - requires cost data'}
```

**2. Mixing Safety Validator:**
```python
from typing import Literal

class MixingSafetyValidator:
    """Verhindert gefährliche Dünger-Kombinationen"""
    
    # Kritische Inkompatibilitäten
    CRITICAL_INCOMPATIBILITIES = {
        ('calcium', 'sulfate'): 'Gips-Ausfällung (CaSO4)',
        ('calcium', 'phosphate'): 'Calcium-Phosphat-Ausfällung',
        ('iron_chelate', 'high_ph'): 'Eisen-Chelat zerfällt bei pH > 7',
        ('silicate', 'acidic'): 'Siliziumdioxid fällt aus bei niedrigem pH',
        ('mycorrhiza', 'high_phosphate'): 'Hohe P-Konzentration (>20 ppm verfügbar) unterdrückt Mykorrhiza-Symbiose',
        ('trichoderma', 'peroxide'): 'H₂O₂-Produkte töten Trichoderma-Kulturen ab',
        ('beneficial_bacteria', 'chlorine'): 'Chlor/Chloramin im Wasser tötet Mikrobiom ab'
    }
    
    @staticmethod
    def validate_combination(
        fert1_components: list[str],
        fert2_components: list[str],
        mixing_order: Literal['simultaneous', 'sequential']
    ) -> dict:
        """
        Prüft ob zwei Dünger zusammen gemischt werden können
        """
        
        warnings = []
        
        # Prüfe auf kritische Kombinationen
        for comp1 in fert1_components:
            for comp2 in fert2_components:
                key = tuple(sorted([comp1, comp2]))
                if key in MixingSafetyValidator.CRITICAL_INCOMPATIBILITIES:
                    reason = MixingSafetyValidator.CRITICAL_INCOMPATIBILITIES[key]
                    
                    if mixing_order == 'simultaneous':
                        warnings.append({
                            'severity': 'CRITICAL',
                            'message': f"NIEMALS gleichzeitig mischen: {reason}",
                            'mitigation': 'Sequenziell mit Rührpause zugeben'
                        })
                    else:
                        warnings.append({
                            'severity': 'WARNING',
                            'message': f"Vorsicht: {reason}",
                            'mitigation': 'Gut rühren zwischen Zugaben'
                        })
        
        return {
            'safe': len([w for w in warnings if w['severity'] == 'CRITICAL']) == 0,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_temperature(
        water_temp_c: float,
        fertilizer_type: str
    ) -> dict:
        """Prüft Temperatur-Kompatibilität"""
        
        temp_ranges = {
            'biological': (15, 25),  # Bakterien/Pilze sterben bei Extremen
            'enzyme': (10, 30),
            'chelate': (5, 35),
            'salt_based': (10, 40)
        }
        
        min_temp, max_temp = temp_ranges.get(fertilizer_type, (5, 40))
        
        if water_temp_c < min_temp:
            return {
                'ok': False,
                'message': f"Wasser zu kalt ({water_temp_c}°C) - Minimum: {min_temp}°C",
                'risk': 'Ausfällungen oder Inaktivierung biologischer Zusätze'
            }
        elif water_temp_c > max_temp:
            return {
                'ok': False,
                'message': f"Wasser zu warm ({water_temp_c}°C) - Maximum: {max_temp}°C",
                'risk': 'Zersetzung oder Denaturierung'
            }
        
        return {'ok': True}
```

**3. Runoff Analysis (Drain-to-Waste):**
```python
from pydantic import BaseModel

class RunoffAnalyzer(BaseModel):
    """Analysiert Abfluss bei DTW-Systemen"""
    
    input_ec: float
    input_ph: float
    runoff_ec: float
    runoff_ph: float
    input_volume_liters: float
    runoff_volume_liters: float
    
    def analyze(self) -> dict:
        """
        Bewertet Nährstoff-Aufnahme und Substrat-Zustand
        """
        
        # 1. EC-Analyse
        ec_diff = self.runoff_ec - self.input_ec
        
        if ec_diff > 0.5:
            ec_status = 'SALT_BUILDUP'
            ec_action = 'Flush erforderlich - Salzakkumulation im Substrat'
        elif ec_diff > 0.2:
            ec_status = 'WARNING'
            ec_action = 'Leichte Akkumulation - Dosierung reduzieren oder häufiger wässern'
        elif ec_diff < -0.3:
            ec_status = 'HEAVY_FEEDING'
            ec_action = 'Pflanze nimmt viel auf - evtl. Dosierung erhöhen'
        else:
            ec_status = 'OK'
            ec_action = 'Nährstoffaufnahme im normalen Bereich'
        
        # 2. pH-Analyse
        ph_diff = self.runoff_ph - self.input_ph
        
        if abs(ph_diff) > 1.0:
            ph_status = 'CRITICAL'
            ph_action = 'Starke pH-Drift - Substrat-Pufferung erschöpft?'
        elif abs(ph_diff) > 0.5:
            ph_status = 'WARNING'
            ph_action = 'pH-Drift beobachten'
        else:
            ph_status = 'OK'
            ph_action = 'pH stabil'
        
        # 3. Runoff-Prozentsatz
        runoff_percent = (self.runoff_volume_liters / self.input_volume_liters) * 100
        
        if runoff_percent < 10:
            runoff_status = 'TOO_LOW'
            runoff_action = 'Zu wenig Runoff - erhöhe Wassermenge (Ziel: 15-20%)'
        elif runoff_percent > 30:
            runoff_status = 'TOO_HIGH'
            runoff_action = 'Zu viel Runoff - Wasser-/Nährstoffverschwendung'
        else:
            runoff_status = 'OK'
            runoff_action = f'Runoff im Zielbereich ({runoff_percent:.1f}%)'
        
        return {
            'ec_analysis': {
                'status': ec_status,
                'input_ec': self.input_ec,
                'runoff_ec': self.runoff_ec,
                'difference': round(ec_diff, 2),
                'action': ec_action
            },
            'ph_analysis': {
                'status': ph_status,
                'input_ph': self.input_ph,
                'runoff_ph': self.runoff_ph,
                'difference': round(ph_diff, 2),
                'action': ph_action
            },
            'runoff_volume': {
                'status': runoff_status,
                'percent': round(runoff_percent, 1),
                'action': runoff_action
            },
            'overall_health': self._calculate_overall_health(ec_status, ph_status, runoff_status)
        }
    
    def _calculate_overall_health(self, ec_status: str, ph_status: str, runoff_status: str) -> str:
        """Gesamtbewertung"""
        
        critical_count = sum(1 for s in [ec_status, ph_status, runoff_status] if s == 'CRITICAL')
        warning_count = sum(1 for s in [ec_status, ph_status, runoff_status] if s in ['WARNING', 'TOO_LOW', 'TOO_HIGH', 'SALT_BUILDUP', 'HEAVY_FEEDING'])
        
        if critical_count > 0:
            return 'CRITICAL - Sofortmaßnahmen erforderlich'
        elif warning_count >= 2:
            return 'WARNING - Anpassungen empfohlen'
        elif warning_count == 1:
            return 'ATTENTION - Überwachen'
        else:
            return 'HEALTHY - Alles im grünen Bereich'
```

**4. Nutrient Plan Management:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Tuple
from datetime import datetime

PhaseNameType = Literal['germination', 'seedling', 'vegetative', 'flowering', 'harvest']

class FertilizerDosage(BaseModel):
    """Dünger-Zuweisung innerhalb einer Phase-Entry"""

    fertilizer_key: str = Field(description="ArangoDB _key des Fertilizer-Dokuments")
    ml_per_liter: float = Field(gt=0, le=50.0, description="Dosierung in ml pro Liter")
    optional: bool = Field(default=False, description="Optionaler Zusatz (z.B. Booster)")

class NutrientPlanPhaseEntry(BaseModel):
    """Phasen-spezifische Konfiguration innerhalb eines Nährstoffplans"""

    phase_name: PhaseNameType
    sequence_order: int = Field(ge=1, le=10)
    week_start: int = Field(ge=0, le=52)
    week_end: int = Field(ge=1, le=52)
    npk_ratio: Tuple[float, float, float] = Field(description="Ziel-NPK-Verhältnis")
    target_ec_ms: float = Field(ge=0.0, le=4.0)
    target_ph: float = Field(ge=4.0, le=8.0)
    calcium_ppm: Optional[float] = Field(None, ge=0, le=500)
    magnesium_ppm: Optional[float] = Field(None, ge=0, le=200)
    sulfur_ppm: Optional[float] = Field(None, ge=0, le=300)
    iron_ppm: Optional[float] = Field(None, ge=0, le=20)  # Fe-Mangel = häufigste Chlorose in Hydro/Coco
    boron_ppm: Optional[float] = Field(None, ge=0, le=5)   # B-Mangel bei Ca-reicher Düngung
    feeding_frequency_per_week: int = Field(ge=1, le=14)
    volume_per_feeding_liters: float = Field(gt=0, le=1000)
    notes: Optional[str] = Field(None, max_length=2000)
    fertilizer_dosages: list[FertilizerDosage] = Field(default_factory=list)

    @field_validator('week_end')
    @classmethod
    def validate_week_range(cls, v, info):
        week_start = info.data.get('week_start', 0)
        if v <= week_start:
            raise ValueError(f"week_end ({v}) muss größer als week_start ({week_start}) sein")
        return v

    @field_validator('npk_ratio')
    @classmethod
    def validate_npk_ratio(cls, v):
        n, p, k = v
        if any(x < 0 for x in v):
            raise ValueError("NPK-Werte dürfen nicht negativ sein")
        if sum(v) == 0:
            raise ValueError("NPK-Summe darf nicht 0 sein")
        return v

class NutrientPlan(BaseModel):
    """Wiederverwendbarer Lifecycle-Nährstoffplan"""

    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    recommended_substrate_type: Optional[Literal['hydro', 'coco', 'soil', 'living_soil']] = None
    author: str = Field(min_length=1, max_length=100)
    is_template: bool = Field(default=False)
    version: int = Field(default=1, ge=1)
    tags: list[str] = Field(default_factory=list, max_length=20)
    phase_entries: list[NutrientPlanPhaseEntry] = Field(default_factory=list)
    watering_schedule: Optional[WateringSchedule] = Field(
        None,
        description="Gießplan-Konfiguration für manuelle Bewässerung. "
                    "null = Plan ohne Terminplanung (rein als Dosierungsvorlage)."
    )

    @field_validator('tags')
    @classmethod
    def validate_tag_format(cls, v):
        # Pydantic v2: each_item entfernt, Validierung über gesamte Liste
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag darf maximal 50 Zeichen lang sein")
        return [tag.lower().strip() for tag in v]

class NutrientPlanService:
    """Service für CRUD und Geschäftslogik rund um Nährstoffpläne"""

    def __init__(self, db, graph):
        self.db = db
        self.graph = graph

    async def create_plan(self, plan: NutrientPlan) -> dict:
        """Erstellt einen neuen Nährstoffplan mit Phase-Entries"""
        ...

    async def get_plan(self, plan_key: str) -> dict:
        """Lädt Plan mit allen Phase-Entries und Dünger-Zuweisungen"""
        ...

    async def update_plan(self, plan_key: str, updates: dict) -> dict:
        """Aktualisiert Plan-Metadaten (Version wird inkrementiert)"""
        ...

    async def delete_plan(self, plan_key: str) -> None:
        """Löscht Plan inkl. aller Phase-Entries und Edges"""
        ...

    async def clone_plan(self, source_key: str, new_name: str, author: str) -> dict:
        """Deep-Copy eines Plans: Plan + alle Entries + Dünger-Zuweisungen"""
        ...

    async def add_phase_entry(self, plan_key: str, entry: NutrientPlanPhaseEntry) -> dict:
        """Fügt eine Phase-Entry zum Plan hinzu"""
        ...

    async def update_phase_entry(self, entry_key: str, updates: dict) -> dict:
        """Aktualisiert eine Phase-Entry"""
        ...

    async def delete_phase_entry(self, plan_key: str, entry_key: str) -> None:
        """Entfernt eine Phase-Entry und zugehörige Dünger-Edges"""
        ...

    async def assign_fertilizer_to_entry(
        self, entry_key: str, dosage: FertilizerDosage
    ) -> dict:
        """Weist einen Dünger mit Dosierung einer Phase-Entry zu"""
        ...

    async def remove_fertilizer_from_entry(
        self, entry_key: str, fertilizer_key: str
    ) -> None:
        """Entfernt Dünger-Zuweisung von einer Phase-Entry"""
        ...

    async def assign_plan_to_plant(
        self, plant_key: str, plan_key: str, assigned_by: str
    ) -> dict:
        """
        Weist Plan einer PlantInstance zu (1:1).
        Entfernt vorherige Zuweisung falls vorhanden.
        """
        ...

    async def get_plant_plan(self, plant_key: str) -> Optional[dict]:
        """Gibt den aktuell zugewiesenen Plan einer PlantInstance zurück"""
        ...

    async def remove_plan_from_plant(self, plant_key: str) -> None:
        """Entfernt die Plan-Zuweisung von einer PlantInstance"""
        ...

    async def get_current_dosages(self, plant_key: str) -> dict:
        """
        Leitet aktuelle Dosierungen aus zugewiesenem Plan + aktueller Phase ab.
        Kombiniert Phase-Entry-Daten mit Fertilizer-Details und Mixing-Reihenfolge.
        """
        ...

    async def list_plans(
        self,
        substrate_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        is_template: Optional[bool] = None
    ) -> list[dict]:
        """Filtert Pläne nach Substrat, Tags, Template-Status"""
        ...

class NutrientPlanValidator:
    """Validiert Nährstoffpläne auf Vollständigkeit und Konsistenz"""

    MANDATORY_PHASES: list[PhaseNameType] = ['seedling', 'vegetative', 'flowering']

    def validate_completeness(self, plan: NutrientPlan) -> dict:
        """
        Prüft ob alle Pflichtphasen im Plan abgedeckt sind.
        Returns: {complete: bool, missing_phases: list, warnings: list}
        """
        covered_phases = {e.phase_name for e in plan.phase_entries}
        missing = [p for p in self.MANDATORY_PHASES if p not in covered_phases]

        warnings = []
        if missing:
            warnings.append(f"Fehlende Pflichtphasen: {', '.join(missing)}")

        # Prüfe auf Lücken in der Wochenabdeckung
        entries_sorted = sorted(plan.phase_entries, key=lambda e: e.week_start)
        for i in range(len(entries_sorted) - 1):
            current_end = entries_sorted[i].week_end
            next_start = entries_sorted[i + 1].week_start
            if next_start > current_end + 1:
                warnings.append(
                    f"Lücke zwischen Woche {current_end} und {next_start}"
                )

        return {
            'complete': len(missing) == 0,
            'missing_phases': missing,
            'warnings': warnings
        }

    def validate_ec_budget(
        self,
        entry: NutrientPlanPhaseEntry,
        fertilizers: list[FertilizerComponent]
    ) -> dict:
        """
        Prüft ob die Summe der Dünger-EC-Beiträge zum Ziel-EC der Phase passt.
        Returns: {valid: bool, target_ec: float, calculated_ec: float, deviation: float}
        """
        fert_map = {f.id: f for f in fertilizers}
        calculated_ec = 0.0

        for dosage in entry.fertilizer_dosages:
            fert = fert_map.get(dosage.fertilizer_key)
            if fert:
                calculated_ec += fert.ec_contribution_per_ml * dosage.ml_per_liter

        deviation = abs(entry.target_ec_ms - calculated_ec)

        return {
            'valid': deviation <= 0.3,  # Toleranz: ±0.3 mS
            'target_ec': entry.target_ec_ms,
            'calculated_ec': round(calculated_ec, 2),
            'deviation': round(deviation, 2),
            'status': 'OK' if deviation <= 0.3 else 'EC_BUDGET_MISMATCH',
            'recommendation': (
                f"Dosierungen anpassen: Ziel {entry.target_ec_ms} mS, "
                f"berechnet {calculated_ec:.2f} mS (Abweichung {deviation:.2f})"
                if deviation > 0.3 else None
            )
        }
```

**5. WateringScheduleEngine (Gießplan-Terminierung):**
```python
from datetime import date, timedelta
from typing import Optional

class WateringScheduleEngine:
    """
    Berechnet Gießtermine aus WateringSchedule-Konfiguration.
    Reine Logik ohne DB-Zugriff — wird von Services und Celery-Tasks genutzt.
    """

    @staticmethod
    def is_watering_due(
        schedule: WateringSchedule,
        check_date: date,
        last_watering_date: Optional[date] = None
    ) -> bool:
        """
        Prüft ob am check_date gegossen werden soll.

        Bei mode='weekdays': check_date.weekday() muss in weekday_schedule sein.
        Bei mode='interval': Differenz seit last_watering_date muss >= interval_days sein.
            Wenn last_watering_date None: immer True (erster Gießtermin).
        """
        if schedule.schedule_mode == ScheduleMode.WEEKDAYS:
            return check_date.weekday() in schedule.weekday_schedule
        elif schedule.schedule_mode == ScheduleMode.INTERVAL:
            if last_watering_date is None:
                return True
            days_since = (check_date - last_watering_date).days
            return days_since >= schedule.interval_days
        return False

    @staticmethod
    def get_next_watering_dates(
        schedule: WateringSchedule,
        from_date: date,
        days_ahead: int = 14,
        last_watering_date: Optional[date] = None
    ) -> list[date]:
        """
        Berechnet die nächsten Gießtermine innerhalb eines Zeitfensters.
        Returns: Liste von Datumswerten, sortiert aufsteigend.

        Bei mode='weekdays': Alle Tage im Fenster die in weekday_schedule liegen.
        Bei mode='interval': Jeder interval_days-te Tag ab last_watering_date
            (oder ab from_date wenn kein letztes Gießdatum).
        """
        dates = []
        if schedule.schedule_mode == ScheduleMode.WEEKDAYS:
            for offset in range(days_ahead):
                check = from_date + timedelta(days=offset)
                if check.weekday() in schedule.weekday_schedule:
                    dates.append(check)
        elif schedule.schedule_mode == ScheduleMode.INTERVAL:
            anchor = last_watering_date or from_date
            # Nächster Termin nach anchor
            next_date = anchor + timedelta(days=schedule.interval_days)
            while next_date < from_date:
                next_date += timedelta(days=schedule.interval_days)
            while next_date < from_date + timedelta(days=days_ahead):
                dates.append(next_date)
                next_date += timedelta(days=schedule.interval_days)
        return dates

    @staticmethod
    def resolve_dosages_for_run(
        plan: 'NutrientPlan',
        entries: list['NutrientPlanPhaseEntry'],
        plants_by_phase: dict[str, list[str]]
    ) -> dict:
        """
        Gruppiert Pflanzen nach Phase und liefert phasen-spezifische Dosierungen.

        Args:
            plan: Der zugewiesene NutrientPlan
            entries: Phase-Entries des Plans (vorgeladen)
            plants_by_phase: {phase_name: [plant_key, ...]} — aktuelle Phasenzuordnung

        Returns: {
            phase_name: {
                'plant_keys': [...],
                'target_ec_ms': float,
                'target_ph': float,
                'volume_per_feeding_liters': float,
                'fertilizer_dosages': [{fertilizer_key, ml_per_liter, optional, mixing_priority}]
            }
        }

        Pflanzen in Phasen ohne Phase-Entry im Plan werden unter 'unmatched' gruppiert.
        """
        entry_map = {e.phase_name: e for e in entries}
        result = {}

        for phase_name, plant_keys in plants_by_phase.items():
            entry = entry_map.get(phase_name)
            if entry:
                result[phase_name] = {
                    'plant_keys': plant_keys,
                    'target_ec_ms': entry.target_ec_ms,
                    'target_ph': entry.target_ph,
                    'volume_per_feeding_liters': entry.volume_per_feeding_liters,
                    'fertilizer_dosages': [
                        {
                            'fertilizer_key': d.fertilizer_key,
                            'ml_per_liter': d.ml_per_liter,
                            'optional': d.optional,
                            'mixing_priority': d.mixing_priority
                        }
                        for d in entry.fertilizer_dosages
                    ]
                }
            else:
                unmatched = result.setdefault('unmatched', {'plant_keys': []})
                unmatched['plant_keys'].extend(plant_keys)

        return result
```

**API-Schemas für Nährstoffplan-Verwaltung:**
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NutrientPlanCreateRequest(BaseModel):
    """Request-Schema für Plan-Erstellung"""
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    recommended_substrate_type: Optional[str] = None
    is_template: bool = False
    tags: list[str] = Field(default_factory=list)

class NutrientPlanResponse(BaseModel):
    """Response-Schema für Plan"""
    key: str
    name: str
    description: Optional[str]
    recommended_substrate_type: Optional[str]
    author: str
    is_template: bool
    version: int
    tags: list[str]
    phase_entry_count: int
    created_at: datetime
    updated_at: datetime

class PhaseEntryCreateRequest(BaseModel):
    """Request-Schema für Phase-Entry-Erstellung"""
    phase_name: str
    sequence_order: int
    week_start: int
    week_end: int
    npk_ratio: tuple[float, float, float]
    target_ec_ms: float
    target_ph: float
    calcium_ppm: Optional[float] = None
    magnesium_ppm: Optional[float] = None
    feeding_frequency_per_week: int
    volume_per_feeding_liters: float
    notes: Optional[str] = None

class PhaseEntryResponse(BaseModel):
    """Response-Schema für Phase-Entry"""
    key: str
    phase_name: str
    sequence_order: int
    week_start: int
    week_end: int
    npk_ratio: tuple[float, float, float]
    target_ec_ms: float
    target_ph: float
    calcium_ppm: Optional[float]
    magnesium_ppm: Optional[float]
    feeding_frequency_per_week: int
    volume_per_feeding_liters: float
    notes: Optional[str]
    fertilizer_dosages: list[dict]

class FertilizerDosageRequest(BaseModel):
    """Request-Schema für Dünger-Zuweisung"""
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50.0)
    optional: bool = False

class PlanAssignmentRequest(BaseModel):
    """Request-Schema für Plan-Zuweisung an PlantInstance"""
    plan_key: str

class PlanAssignmentResponse(BaseModel):
    """Response-Schema für Plan-Zuweisung"""
    plant_key: str
    plan_key: str
    plan_name: str
    assigned_at: datetime
    assigned_by: str

class CloneRequest(BaseModel):
    """Request-Schema für Plan-Klonen"""
    new_name: str = Field(min_length=1, max_length=200)

class CurrentDosagesResponse(BaseModel):
    """Response-Schema für aktuelle Dosierungen einer PlantInstance"""
    plant_key: str
    plan_name: str
    current_phase: str
    target_ec_ms: float
    target_ph: float
    feeding_frequency_per_week: int
    volume_per_feeding_liters: float
    dosages: list[dict]  # [{fertilizer_name, brand, ml_per_liter, optional, mixing_priority}]
    mixing_instructions: list[str]

class ValidationResponse(BaseModel):
    """Response-Schema für Plan-Validierung"""
    plan_key: str
    completeness: dict  # {complete, missing_phases, warnings}
    ec_budget_checks: list[dict]  # Pro Phase-Entry: {phase, valid, target_ec, calculated_ec}
    overall_valid: bool
```

**REST-Endpoints:**
```python
# Router: /api/v1/fertilizers

# Dünger-CRUD
GET    /api/v1/fertilizers                                  # List (Filter: fertilizer_type, brand, tank_safe, is_organic)
POST   /api/v1/fertilizers                                  # Create
GET    /api/v1/fertilizers/{key}                            # Detail
PUT    /api/v1/fertilizers/{key}                            # Update
DELETE /api/v1/fertilizers/{key}                            # Delete

# Stock-Verwaltung
GET    /api/v1/fertilizers/{key}/stocks                    # List Stocks
POST   /api/v1/fertilizers/{key}/stocks                    # Create Stock
PUT    /api/v1/fertilizers/{key}/stocks/{sk}               # Update Stock
DELETE /api/v1/fertilizers/{key}/stocks/{sk}               # Delete Stock

# Inkompatibilitäten
GET    /api/v1/fertilizers/{key}/incompatibilities         # List
POST   /api/v1/fertilizers/{key}/incompatibilities         # Add
DELETE /api/v1/fertilizers/{key}/incompatibilities/{other}  # Remove
```

**Düngemittel-Listenansicht — Filterung:**

Die Düngemittel-Tabelle (`GET /api/v1/fertilizers`) unterstützt folgende Query-Parameter zur serverseitigen Filterung:

| Query-Parameter | Typ | Beschreibung |
|----------------|-----|-------------|
| `fertilizer_type` | `string` | Filter nach Dünger-Typ (`base`, `supplement`, `booster`, `biological`, `ph_adjuster`, `organic`) |
| `brand` | `string` | Filter nach Hersteller/Marke (case-insensitive Teilstring-Suche, z.B. `?brand=hydro` findet "General Hydroponics") |
| `tank_safe` | `bool` | Filter nach Tank-Sicherheit (`true` = nur tanksichere Dünger, `false` = nur nicht-tanksichere) |
| `is_organic` | `bool` | Filter nach Bio-Zertifizierung (`true` = nur organische Dünger, `false` = nur konventionelle) |
| `offset` | `int` | Pagination-Offset (Default: 0) |
| `limit` | `int` | Pagination-Limit (Default: 50, Max: 200) |

Alle Filter sind optional und kombinierbar (AND-Verknüpfung). Ohne Filter wird die vollständige Düngerliste zurückgegeben.

```python
# Router: /api/v1/nutrient-plans

# Plan-CRUD
GET    /api/v1/nutrient-plans                              # List (Filter: substrate_type, tags, is_template)
POST   /api/v1/nutrient-plans                              # Create
GET    /api/v1/nutrient-plans/{key}                        # Detail (inkl. Phase-Entries + Dosages)
PUT    /api/v1/nutrient-plans/{key}                        # Update (Metadaten)
DELETE /api/v1/nutrient-plans/{key}                        # Delete (inkl. Entries + Edges)

# Clone
POST   /api/v1/nutrient-plans/{key}/clone                 # Deep-Clone → neuer Plan

# Phase-Entry-Verwaltung
GET    /api/v1/nutrient-plans/{plan_key}/entries           # List Phase-Entries
POST   /api/v1/nutrient-plans/{plan_key}/entries           # Create Phase-Entry
PUT    /api/v1/nutrient-plans/{plan_key}/entries/{entry_key}    # Update Phase-Entry
DELETE /api/v1/nutrient-plans/{plan_key}/entries/{entry_key}    # Delete Phase-Entry

# Dünger-Zuweisung innerhalb Phase-Entry
POST   /api/v1/nutrient-plans/entries/{entry_key}/fertilizers   # Dünger zuweisen
DELETE /api/v1/nutrient-plans/entries/{entry_key}/fertilizers    # Dünger entfernen

# Plan-Zuweisung an PlantInstance
POST   /api/v1/plant-instances/{plant_key}/nutrient-plan   # Plan zuweisen (1:1, ersetzt vorherige)
GET    /api/v1/plant-instances/{plant_key}/nutrient-plan   # Zugewiesenen Plan abrufen
DELETE /api/v1/plant-instances/{plant_key}/nutrient-plan   # Plan-Zuweisung entfernen

# Dosierungen + Validierung
GET    /api/v1/plant-instances/{plant_key}/current-dosages # Aktuelle Dosierungen aus Plan + Phase
GET    /api/v1/nutrient-plans/{key}/validate               # Vollständigkeits- + EC-Budget-Check
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime

FertilizerType = Literal['base', 'supplement', 'booster', 'biological', 'ph_adjuster', 'organic']
SubstrateType = Literal['hydro', 'coco', 'soil', 'living_soil', 'perlite', 'rockwool']
MixingMethod = Literal['stir', 'circulate', 'rest', 'aerate']

class FertilizerDefinition(BaseModel):
    """Vollständige Dünger-Definition"""
    
    product_name: str = Field(min_length=1, max_length=200)
    brand: str
    type: FertilizerType
    npk: Tuple[float, float, float] = Field(description="N-P-K in %")
    ec_contribution_per_ml: float = Field(ge=0, le=2.0)
    mixing_priority: int = Field(ge=1, le=100)
    shelf_life_months: int = Field(ge=1, le=60)
    organic_certified: bool = False
    
    @field_validator('npk')
    @classmethod
    def validate_npk_realistic(cls, v):
        n, p, k = v
        if n > 65 or p > 65 or k > 65:
            raise ValueError("Einzelne NPK-Werte über 65% unrealistisch")
            # K₂O bei KCl erreicht 60%, reine Salze können über 50% liegen
        if sum(v) > 80:
            raise ValueError("NPK-Summe über 80% unrealistisch")
        return v
    
    @field_validator('ec_contribution_per_ml')
    @classmethod
    def validate_ec_contribution(cls, v, info):
        npk_sum = sum(info.data.get('npk', (0, 0, 0)))
        # Höheres NPK sollte höheren EC-Beitrag haben
        if npk_sum > 20 and v < 0.01:
            raise ValueError("EC-Beitrag zu niedrig für NPK-Konzentration")
        return v

class ApplicationMethod(str, Enum):
    FERTIGATION = "fertigation"   # Über Tank/Tropfer/Pumpe (automatisch oder manuell aus Tank)
    DRENCH = "drench"             # Manuelles Gießen per Gießkanne (Substrat-Durchspülung)
    FOLIAR = "foliar"             # Blattdüngung per Sprüher
    TOP_DRESS = "top_dress"       # Feststoff auf Substratoberfläche (z.B. Wurmhumus, Guano)

class FeedingEventRecord(BaseModel):
    """Dokumentation einer Düngung/Bewässerung auf Pflanzenlevel"""

    plant_id: str
    timestamp: datetime
    application_method: ApplicationMethod = Field(
        description="Art der Ausbringung — fertigation (Tank/Tropfer), "
                    "drench (Gießkanne), foliar (Sprüher), top_dress (Feststoff)"
    )
    is_supplemental: bool = Field(
        default=False,
        description="Ergänzende Handdüngung zusätzlich zur Tank-Bewässerung — "
                    "z.B. Komposttee per Gießkanne bei Drip-versorgten Pflanzen"
    )
    watering_event_key: Optional[str] = Field(
        None,
        description="Referenz auf WateringEvent (REQ-014), "
                    "wenn FeedingEvent automatisch aus Gießvorgang erzeugt wurde"
    )
    tank_fill_event_key: Optional[str] = Field(
        None,
        description="Referenz auf TankFillEvent (REQ-014), "
                    "wenn Düngung aus dokumentierter Tankbefüllung stammt"
    )
    volume_applied_liters: float = Field(gt=0, le=1000)
    fertilizers_used: list[dict]  # [{fertilizer_id, ml_applied}]
    measured_ec_before: Optional[float] = Field(None, ge=0, le=5)
    measured_ec_after: Optional[float] = Field(None, ge=0, le=5)
    measured_ph_before: Optional[float] = Field(None, ge=0, le=14)
    measured_ph_after: Optional[float] = Field(None, ge=0, le=14)
    runoff_collected: bool = False
    runoff_ec: Optional[float] = None
    runoff_ph: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('measured_ec_after')
    @classmethod
    def validate_ec_change(cls, v, info):
        """
        EC-Abnahme nach Düngung ist kein Fehler — sie tritt auf bei:
        - Flushing (gewollt: EC soll sinken)
        - Verdünnter Lösung durch versalztes Substrat
        - Stark puffernden Substraten (Living Soil)
        Nur als Warnung loggen, nicht als Validierungsfehler.
        """
        import warnings
        ec_before = info.data.get('measured_ec_before')
        if ec_before and v:
            if v < ec_before and info.data.get('application_method') not in (
                ApplicationMethod.FOLIAR, ApplicationMethod.TOP_DRESS
            ):
                warnings.warn(
                    f"EC nach Applikation ({v}) niedriger als vorher ({ec_before}). "
                    f"Normal bei Flushing oder verdünnter Lösung.",
                    stacklevel=2
                )
        return v

    @model_validator(mode='after')
    def validate_tank_safe_consistency(self):
        """Bei fertigation muss tank_fill_event_key oder Notiz vorhanden sein."""
        if self.application_method == ApplicationMethod.FERTIGATION and not self.tank_fill_event_key:
            # Kein harter Fehler — Fertigation kann auch ohne dokumentiertes TankFillEvent stattfinden
            pass
        return self
```

## 4. Multi-Channel Delivery (Ausbringungskanäle)

### 4.1 Motivation & User Story

**User Story:** "Als Gärtner möchte ich pro Wachstumsphase mehrere parallele Ausbringungskanäle definieren — z.B. Tropfer für Base-Nährstoffe (3x/Tag), Gießkanne für Komposttee (1x/Woche) und Blattdüngung für Mikronährstoffe (alle 2 Wochen) — damit ich komplexe Düngeprogramme mit unterschiedlichen Methoden, Intervallen und Düngerlisten in einem einzigen Nährstoffplan abbilden kann."

**Problemstellung:**
Der aktuelle `NutrientPlanPhaseEntry` unterstützt pro Phase nur **eine** Kombination aus Ausbringungsmethode, Frequenz, Volumen und Düngerliste. In der Praxis verwenden Grower jedoch mehrere parallele Kanäle:

| Kanal | Methode | Frequenz | Dünger |
|---|---|---|---|
| Tropfer (Base) | Fertigation | 3x/Tag | FloraGro, FloraMicro, CalMag |
| Komposttee | Drench | 1x/Woche | Komposttee, Wurmhumus-Extrakt |
| Mikronährstoffe | Foliar | alle 14 Tage | Eisen-Chelat, Kalzium-Spray |
| Mykorrhiza | Top Dress | monatlich | Mykorrhiza-Granulat |

**Vergleich: Aktueller Stand vs. Zielzustand:**

| Aspekt | Aktuell (Single-Channel) | Ziel (Multi-Channel) |
|---|---|---|
| Ausbringungskanäle pro Phase | 1 | 1–n |
| Separate Schedules | Nein (Plan-Level) | Ja (pro Channel) |
| Eigene Düngerliste pro Kanal | Nein | Ja |
| Eigene EC/pH-Ziele pro Kanal | Nein | Ja (optional, Override) |
| Tank-Verknüpfung (REQ-014) | Nein | Ja (optional, Fertigation) |
| Legacy-Kompatibilität | — | Ja (`delivery_channels=[]`) |

### 4.2 Datenmodell

#### Neues Embedded Model: `DeliveryChannel`

`DeliveryChannel` wird als eingebettetes Modell (kein eigenes ArangoDB-Dokument) innerhalb von `NutrientPlanPhaseEntry` gespeichert. Jeder Channel beschreibt einen unabhängigen Ausbringungskanal mit eigener Methode, eigenem Schedule und eigenen Düngern.

**Gemeinsame Felder (alle Methoden):**

| Feld | Typ | Constraints | Beschreibung |
|---|---|---|---|
| `channel_id` | `str` | max 50, unique innerhalb Entry | Eindeutiger Bezeichner (z.B. `"dripper-base"`, `"compost-tea"`) |
| `label` | `str` | max 100 | Anzeigename (z.B. "Tropfer (Base Nutrients)") |
| `application_method` | `ApplicationMethod` | `fertigation\|drench\|foliar\|top_dress` | Ausbringungsmethode |
| `enabled` | `bool` | Default: `true` | Channel aktiv/deaktiviert (ohne Löschung) |
| `notes` | `Optional[str]` | max 500 | Freitext-Notizen |

**Methoden-spezifische Parameter (Discriminated Union per `application_method`):**

Jede Ausbringungsmethode besitzt spezifische Parameter, die nur für diese Methode gelten. Das Modell nutzt eine Discriminated Union (`fertigation_params`, `drench_params`, `foliar_params`, `top_dress_params`), wobei exakt das zur `application_method` passende Params-Objekt gesetzt sein muss.

**`FertigationParams`:**

| Feld | Typ | Constraints | Default | Beschreibung |
|---|---|---|---|---|
| `runs_per_day` | `int` | 1–24 | 1 | Anzahl Bewässerungszyklen pro Tag |
| `duration_minutes` | `float` | >0, ≤120 | 5.0 | Dauer pro Zyklus in Minuten |
| `flow_rate_ml_min` | `Optional[float]` | >0 | — | Durchflussrate (für Volumenberechnung) |
| `tank_key` | `Optional[str]` | — | — | Verknüpfung zu Tank (REQ-014) |

**`DrenchParams`:**

| Feld | Typ | Constraints | Default | Beschreibung |
|---|---|---|---|---|
| `volume_per_feeding_liters` | `float` | >0, ≤100 | — | Volumen pro Gießvorgang |

**`FoliarParams`:**

| Feld | Typ | Constraints | Default | Beschreibung |
|---|---|---|---|---|
| `volume_per_spray_liters` | `float` | >0, ≤10 | — | Sprühvolumen pro Anwendung |

**`TopDressParams`:**

| Feld | Typ | Constraints | Default | Beschreibung |
|---|---|---|---|---|
| `grams_per_plant` | `Optional[float]` | >0, ≤5000 | — | Gramm pro Pflanze |
| `grams_per_m2` | `Optional[float]` | >0, ≤10000 | — | Gramm pro Quadratmeter (Freiland) |

**Channel-Level Scheduling:**

| Feld | Typ | Constraints | Beschreibung |
|---|---|---|---|
| `schedule` | `Optional[WateringSchedule]` | — | Eigener Zeitplan (wiederverwendetes Modell). `null` = kein automatisches Scheduling. Bei Multi-Channel ist `fertigation` als `application_method` im Schedule **erlaubt** (Abweichung von Plan-Level WateringSchedule, wo Fertigation ausgeschlossen ist). Für Fertigation-Channels bestimmt der Schedule die **Gießtage**, wahrend `runs_per_day` + `duration_minutes` die Intra-Day-Frequenz steuern. |

**Channel-Level Targets & Dosierungen:**

| Feld | Typ | Constraints | Beschreibung |
|---|---|---|---|
| `target_ec_ms` | `Optional[float]` | 0.0–4.0 | Override für Phase-Level EC. `null` = Phase-EC gilt. |
| `target_ph` | `Optional[float]` | 4.0–8.0 | Override für Phase-Level pH. `null` = Phase-pH gilt. |
| `fertilizer_dosages` | `list[FertilizerDosage]` | — | Channel-eigene Düngerliste mit Dosierungen. Verwendet das bestehende `FertilizerDosage`-Modell. |

#### Modifiziert: `NutrientPlanPhaseEntry`

Erweiterung um ein neues Feld:

| Feld | Typ | Constraints | Default | Beschreibung |
|---|---|---|---|---|
| `delivery_channels` | `list[DeliveryChannel]` | max 10 Channels pro Entry | `[]` | Liste der Ausbringungskanäle |

**Legacy-Kompatibilität:** Die bestehenden Felder `feeding_frequency_per_week`, `volume_per_feeding_liters` und `fertilizer_dosages` (Phase-Level) bleiben erhalten.

**Geschäftsregel:** Wenn `delivery_channels` nicht leer ist (`len > 0`), werden die Legacy-Felder (`feeding_frequency_per_week`, `volume_per_feeding_liters`, Phase-Level `fertilizer_dosages`) **ignoriert**. Die Kanäle sind dann die alleinige Quelle für Scheduling, Volumina und Dosierungen.

**Mehrere Kanäle gleichen Typs:** Erlaubt — z.B. zwei `drench`-Kanäle mit unterschiedlichen Düngern (ein Kanal für Base-Nährstoffe, ein anderer für Komposttee).

#### Pydantic-Modell

```python
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal

class FertigationParams(BaseModel):
    """Parameter für Tank/Tropfer-basierte Ausbringung"""
    runs_per_day: int = Field(default=1, ge=1, le=24)
    duration_minutes: float = Field(default=5.0, gt=0, le=120)
    flow_rate_ml_min: Optional[float] = Field(None, gt=0)
    tank_key: Optional[str] = Field(
        None,
        description="Verknüpfung zu Tank (REQ-014). Aktiviert Tank-Safe-Prüfung."
    )

class DrenchParams(BaseModel):
    """Parameter für manuelles Gießen per Gießkanne"""
    volume_per_feeding_liters: float = Field(gt=0, le=100)

class FoliarParams(BaseModel):
    """Parameter für Blattdüngung per Sprüher"""
    volume_per_spray_liters: float = Field(gt=0, le=10)

class TopDressParams(BaseModel):
    """Parameter für Feststoff-Aufbringung auf Substratoberfläche"""
    grams_per_plant: Optional[float] = Field(None, gt=0, le=5000)
    grams_per_m2: Optional[float] = Field(None, gt=0, le=10000)

    @model_validator(mode='after')
    def at_least_one_dosage(self):
        if self.grams_per_plant is None and self.grams_per_m2 is None:
            raise ValueError(
                "Mindestens grams_per_plant oder grams_per_m2 muss gesetzt sein"
            )
        return self

class DeliveryChannel(BaseModel):
    """
    Ausbringungskanal innerhalb einer NutrientPlanPhaseEntry.
    Eingebettetes Modell — kein eigenes ArangoDB-Dokument.
    """
    channel_id: str = Field(max_length=50)
    label: str = Field(max_length=100)
    application_method: Literal['fertigation', 'drench', 'foliar', 'top_dress']
    enabled: bool = Field(default=True)
    notes: Optional[str] = Field(None, max_length=500)

    # Methoden-spezifische Parameter (Discriminated Union)
    fertigation_params: Optional[FertigationParams] = None
    drench_params: Optional[DrenchParams] = None
    foliar_params: Optional[FoliarParams] = None
    top_dress_params: Optional[TopDressParams] = None

    # Channel-Level Scheduling
    schedule: Optional[WateringSchedule] = Field(
        None,
        description="Eigener Zeitplan. Bei Fertigation bestimmt der Schedule die "
                    "Gießtage, runs_per_day die Intra-Day-Frequenz."
    )

    # Channel-Level Targets (Overrides)
    target_ec_ms: Optional[float] = Field(None, ge=0.0, le=4.0)
    target_ph: Optional[float] = Field(None, ge=4.0, le=8.0)

    # Channel-Level Dosierungen
    fertilizer_dosages: list[FertilizerDosage] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_params_match_method(self):
        """Stellt sicher, dass exakt das passende Params-Objekt gesetzt ist."""
        method = self.application_method
        params_map = {
            'fertigation': self.fertigation_params,
            'drench': self.drench_params,
            'foliar': self.foliar_params,
            'top_dress': self.top_dress_params,
        }
        active = params_map.get(method)
        if active is None:
            raise ValueError(
                f"{method}_params ist erforderlich für application_method='{method}'"
            )
        # Alle anderen Params müssen None sein
        for other_method, other_params in params_map.items():
            if other_method != method and other_params is not None:
                raise ValueError(
                    f"{other_method}_params darf nicht gesetzt sein bei "
                    f"application_method='{method}'"
                )
        return self
```

### 4.3 Validierungsregeln (per Channel)

| Regel-ID | Regel | Channel-Typ | Severity | Beschreibung |
|---|---|---|---|---|
| MCD-V01 | Tank-Safe-Prüfung | fertigation | CRITICAL | Nur Dünger mit `tank_safe=true` erlaubt. Dünger mit `tank_safe=false` (organische Feststoffe, Schwebstoff-haltige Extrakte) verstopfen Tropfer und verursachen Biofilm im Tank. |
| MCD-V02 | EC-Budget | fertigation, drench | WARNING | Summe der Dünger-EC-Beiträge soll `target_ec +/- 0.3 mS` entsprechen. Überschreitung = Warnung "EC-Budget überschritten". |
| MCD-V03 | EC nicht anwendbar | top_dress | INFO | Kein EC-Budget für Feststoff-Dünger. Infohinweis: "EC-Budget-Prüfung nicht anwendbar für Top-Dress-Kanäle." |
| MCD-V04 | EC-Limit Foliar | foliar | INFO | Warnung bei `target_ec > 1.0 mS`: "Foliar-Lösungen über 1.0 mS können Blattverbrennungen verursachen." |
| MCD-V05 | Foliar Blüte-Warnung | foliar | WARNING | Phase=`flowering`, Woche >= 2: Schimmelrisiko (bestehende G-013-Regel, siehe Business Case). |
| MCD-V06 | IPM-Ausnahme Foliar | foliar | — | Wenn `is_emergency=true` auf verknüpftem TreatmentApplication (REQ-010) -> Blüte-Warnung (MCD-V05) wird unterdrückt. |
| MCD-V07 | Params-Match | alle | ERROR | `application_method='fertigation'` -> `fertigation_params` muss gesetzt sein; analog für drench, foliar, top_dress. Fehlende oder falsche Params -> Validierungsfehler 422. |
| MCD-V08 | Channel-ID unique | alle | ERROR | `channel_id` muss innerhalb eines `NutrientPlanPhaseEntry` eindeutig sein. Duplikate -> Validierungsfehler 422. |
| MCD-V09 | Schedule empfohlen | alle | WARNING | Channel ohne `schedule` (`null`) erzeugt keine automatischen Celery-Tasks. Warnung: "Channel ohne Schedule — keine automatische Task-Generierung." |
| MCD-V10 | `recommended_application` Match | alle | WARNING | Wenn ein Dünger `recommended_application` definiert hat und diese nicht zur Channel-Methode passt -> Warnung. Z.B. Dünger mit `recommended_application='top_dress'` in einem Fertigation-Channel. |
| MCD-V11 | Tank existiert | fertigation | ERROR | Wenn `tank_key` gesetzt ist, muss ein Tank-Dokument mit diesem Key in der `Tank`-Collection existieren (REQ-014). Nicht existierender Tank -> Validierungsfehler. |
| MCD-V12 | Max Channels | alle | ERROR | Maximal 10 Channels pro `NutrientPlanPhaseEntry`. Überschreitung -> Validierungsfehler 422. |

**Cross-Channel-Validierungen:**

| Regel-ID | Regel | Severity | Beschreibung |
|---|---|---|---|
| MCD-V20 | Dünger-Duplikat-Warnung | WARNING | Gleicher Dünger in mehreren Channels derselben Phase -> Warnung "Dünger {name} ist in {n} Channels zugewiesen — Gesamt-EC-Beitrag prüfen." |
| MCD-V21 | Gesamt-EC-Plausibilität | WARNING | Summe aller Channel-EC-Beiträge über alle Channels hinweg > Phase-Level `target_ec_ms` x 1.5 -> Warnung "Kumulierter EC-Beitrag aller Channels überschreitet Phase-Ziel deutlich." |
| MCD-V22 | Fertigation-Tank-Konflikt | WARNING | Mehrere Fertigation-Channels mit unterschiedlichen `tank_key`-Werten -> Warnung "Mehrere Tanks pro Phase — sicherstellen, dass Tropfer-Zonen korrekt zugeordnet sind." |

### 4.4 Edge-Collection Erweiterung

**Modifizierte Edge-Collection `USES_FERTILIZER`:**

```
USES_FERTILIZER: NutrientPlanPhaseEntry -> Fertilizer
  Bestehende Attribute:
    ml_per_liter: float
    optional: bool
  Neues Attribut:
    channel_id: Optional[str]  (null = Legacy / Phase-Level-Dosierung)
```

Wenn `channel_id` gesetzt ist, gehört diese Dünger-Zuweisung zum angegebenen Channel. Bei `channel_id=null` handelt es sich um eine Legacy-Zuweisung auf Phase-Level.

**Modifizierte Event-Dokumente:**

`WateringEvent` (REQ-014) und `FeedingEvent` erhalten ein neues optionales Feld:

| Feld | Typ | Beschreibung |
|---|---|---|
| `channel_id` | `Optional[str]` | Referenz auf den `DeliveryChannel.channel_id`, aus dem dieses Event erzeugt wurde. `null` = Legacy-Event ohne Channel-Zuordnung. |

### 4.5 Engine-Änderungen

**WateringScheduleEngine (Erweiterung):**

Neue Methode `get_due_channels()`:

```python
@staticmethod
def get_due_channels(
    entry: NutrientPlanPhaseEntry,
    check_date: date,
    last_dates: dict[str, Optional[date]]
) -> list[DeliveryChannel]:
    """
    Ermittelt alle Channels einer Phase-Entry, die am check_date fällig sind.

    Args:
        entry: Phase-Entry mit delivery_channels
        check_date: Zu prüfendes Datum
        last_dates: {channel_id: letztes Ausführungsdatum} — None = noch nie ausgeführt

    Returns:
        Liste fälliger DeliveryChannels (nur enabled Channels mit Schedule).
        Leere Liste wenn delivery_channels leer (Legacy-Modus).
    """
    if not entry.delivery_channels:
        return []  # Legacy-Modus — Fallback auf bestehende Logik

    due = []
    for channel in entry.delivery_channels:
        if not channel.enabled or channel.schedule is None:
            continue
        last = last_dates.get(channel.channel_id)
        if WateringScheduleEngine.is_watering_due(channel.schedule, check_date, last):
            due.append(channel)
    return due
```

**NutrientPlanValidator (Erweiterung):**

- `validate_ec_budget()`: Unterstützt Channel-Level-Validierung. Wenn `delivery_channels` vorhanden, wird EC-Budget **pro Channel** geprüft (nur für Channels mit `application_method in ('fertigation', 'drench')`).
- Neue Methode `validate_channels()`: Cross-Channel-Validierung (MCD-V20 bis MCD-V22).

**MixingSafetyValidator (Erweiterung):**

Neue Methode `validate_channel()`:

```python
@staticmethod
def validate_channel(
    channel: DeliveryChannel,
    fertilizer_catalog: dict[str, FertilizerComponent]
) -> list[dict]:
    """
    Validiert einen einzelnen Channel auf Misch-Sicherheit.

    Prüfungen:
    - Tank-Safe: Fertigation-Channel -> alle Dünger müssen tank_safe=true sein (MCD-V01)
    - recommended_application Match (MCD-V10)
    - Bestehende Inkompatibilitats-Prüfungen innerhalb der Channel-Dünger

    Returns: Liste von Validierungs-Warnungen/Fehlern
    """
    ...
```

**NutrientSolutionCalculator (Anpassung):**

`calculate_dosages()` akzeptiert optional Channel-Dosierungen statt Phase-Entry-Level-Dosierungen. Neue Signatur:

```python
def calculate_dosages(
    self,
    dosages_override: Optional[list[FertilizerDosage]] = None
) -> dict:
    """
    Berechnet Mischprotokoll.
    Wenn dosages_override gesetzt: verwendet Channel-Dosierungen
    statt self.fertilizers.
    """
    ...
```

**Neuer Helper: `get_effective_channels()`**

```python
def get_effective_channels(entry: NutrientPlanPhaseEntry) -> list[DeliveryChannel]:
    """
    Gibt die effektiven Channels zurück:
    - Wenn delivery_channels nicht leer -> direkt zurückgeben
    - Wenn delivery_channels leer -> Legacy-Felder zu synthetischem Channel konvertieren

    Synthetischer Legacy-Channel:
    - channel_id: "__legacy__"
    - label: "Standard"
    - application_method: "drench"
    - drench_params: DrenchParams(volume_per_feeding_liters=entry.volume_per_feeding_liters)
    - schedule: None (Legacy nutzt Plan-Level WateringSchedule)
    - fertilizer_dosages: entry.fertilizer_dosages (Phase-Level)
    - target_ec_ms: None (Phase-Level EC gilt)
    - target_ph: None (Phase-Level pH gilt)
    """
    ...
```

**Neuer: DeliveryChannelValidator:**

```python
class DeliveryChannelValidator:
    """
    Kanal-übergreifende Validierungen für Multi-Channel Delivery.
    Pruft Regeln MCD-V20 bis MCD-V22.
    """

    @staticmethod
    def validate_cross_channel(
        channels: list[DeliveryChannel],
        fertilizer_catalog: dict[str, FertilizerComponent],
        phase_target_ec: float
    ) -> list[dict]:
        """
        Cross-Channel-Validierungen:
        - MCD-V20: Dünger-Duplikat-Warnung
        - MCD-V21: Gesamt-EC-Plausibilität
        - MCD-V22: Fertigation-Tank-Konflikt

        Returns: Liste von {rule_id, severity, message}
        """
        ...
```

### 4.6 API-Endpunkte

**Neue Endpunkte:**

```
POST   /api/v1/nutrient-plans/{key}/entries/{ek}/channels
         -> Channel zu Phase-Entry hinzufügen
         Request: DeliveryChannelCreateRequest
         Response: 201 DeliveryChannelResponse

PUT    /api/v1/nutrient-plans/{key}/entries/{ek}/channels/{cid}
         -> Channel aktualisieren
         Request: DeliveryChannelUpdateRequest
         Response: 200 DeliveryChannelResponse

DELETE /api/v1/nutrient-plans/{key}/entries/{ek}/channels/{cid}
         -> Channel entfernen (inkl. zugehöriger USES_FERTILIZER-Edges mit channel_id)
         Response: 204 No Content

POST   /api/v1/nutrient-plans/entries/{ek}/channels/{cid}/fertilizers
         -> Dünger einem Channel zuweisen
         Request: FertilizerDosageRequest (bestehendes Schema)
         Response: 201 FertilizerDosageResponse

DELETE /api/v1/nutrient-plans/entries/{ek}/channels/{cid}/fertilizers/{fk}
         -> Dünger-Zuweisung von Channel entfernen
         Response: 204 No Content

POST   /api/v1/nutrient-plans/{key}/migrate-to-channels
         -> Legacy-Felder -> Channel-Konvertierung
         Request: {} (keine Parameter)
         Response: 200 {migrated_entries: int, channels_created: int}
         Logik: Für jede Phase-Entry mit delivery_channels=[] wird ein synthetischer
                Channel aus den Legacy-Feldern erstellt (method=drench, Schedule vom Plan).
                Legacy-Felder bleiben unverändert (Rollback möglich).
```

**Modifizierte Endpunkte:**

| Endpunkt | Änderung |
|---|---|
| `POST /api/v1/nutrient-plans/{plan_key}/entries` | Request akzeptiert optionales `delivery_channels[]` |
| `PUT /api/v1/nutrient-plans/{plan_key}/entries/{ek}` | Request akzeptiert optionales `delivery_channels[]` |
| `GET /api/v1/nutrient-plans/{key}/validate` | Response enthält zusätzliches `channel_validations: list[ChannelValidation]` mit per-Channel und Cross-Channel Validierungsergebnissen |
| `POST /api/v1/watering-events/confirm` | Request akzeptiert optionales `channel_id: str` zur Zuordnung des Events zu einem Channel |
| `POST /api/v1/watering-events/quick-confirm` | Request akzeptiert optionales `channel_id: str` |

**API-Schemas:**

```python
class DeliveryChannelCreateRequest(BaseModel):
    """Request-Schema für Channel-Erstellung"""
    channel_id: str = Field(max_length=50)
    label: str = Field(max_length=100)
    application_method: Literal['fertigation', 'drench', 'foliar', 'top_dress']
    enabled: bool = True
    notes: Optional[str] = Field(None, max_length=500)
    fertigation_params: Optional[FertigationParams] = None
    drench_params: Optional[DrenchParams] = None
    foliar_params: Optional[FoliarParams] = None
    top_dress_params: Optional[TopDressParams] = None
    schedule: Optional[WateringScheduleRequest] = None
    target_ec_ms: Optional[float] = Field(None, ge=0.0, le=4.0)
    target_ph: Optional[float] = Field(None, ge=4.0, le=8.0)
    fertilizer_dosages: list[FertilizerDosageRequest] = Field(default_factory=list)

class DeliveryChannelUpdateRequest(BaseModel):
    """Request-Schema für Channel-Aktualisierung (alle Felder optional)"""
    label: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    fertigation_params: Optional[FertigationParams] = None
    drench_params: Optional[DrenchParams] = None
    foliar_params: Optional[FoliarParams] = None
    top_dress_params: Optional[TopDressParams] = None
    schedule: Optional[WateringScheduleRequest] = None
    target_ec_ms: Optional[float] = Field(None, ge=0.0, le=4.0)
    target_ph: Optional[float] = Field(None, ge=4.0, le=8.0)

class DeliveryChannelResponse(BaseModel):
    """Response-Schema für Channel"""
    channel_id: str
    label: str
    application_method: str
    enabled: bool
    notes: Optional[str]
    fertigation_params: Optional[dict]
    drench_params: Optional[dict]
    foliar_params: Optional[dict]
    top_dress_params: Optional[dict]
    schedule: Optional[dict]
    target_ec_ms: Optional[float]
    target_ph: Optional[float]
    fertilizer_dosages: list[dict]

class ChannelValidation(BaseModel):
    """Validierungsergebnis für einen Channel"""
    channel_id: str
    label: str
    application_method: str
    issues: list[dict]  # [{rule_id, severity, message}]
    ec_budget: Optional[dict]  # {valid, target_ec, calculated_ec, deviation}

class MigrationResponse(BaseModel):
    """Response-Schema für Legacy-zu-Channel-Migration"""
    migrated_entries: int
    channels_created: int
```

### 4.7 Celery-Task Änderungen

**`generate_watering_tasks` (Anpassung):**

Der bestehende Celery-Beat-Task `watering-generate-tasks-daily` wird erweitert:

- **Legacy-Modus** (`delivery_channels=[]`): Verhalten bleibt unverändert — ein Task pro Run und Tag.
- **Multi-Channel-Modus** (`delivery_channels` nicht leer): Pro fälligem Channel ein separater Task.

**Task-Generierung im Multi-Channel-Modus:**

```
Für jeden PlantingRun mit zugewiesenem NutrientPlan:
  Für jede Phase-Entry passend zur aktuellen Phase:
    due_channels = WateringScheduleEngine.get_due_channels(entry, today, last_dates)
    Für jeden due_channel:
      -> Task erstellen mit:
        task_name: "watering:{run_key}:{channel_id}:{date}"
        description: "{label} — {application_method}"
        metadata: {
          channel_id: channel.channel_id,
          application_method: channel.application_method,
          target_ec_ms: channel.target_ec_ms or entry.target_ec_ms,
          fertilizer_count: len(channel.fertilizer_dosages)
        }
```

**Task-Metadaten:** `channel_id` und `application_method` werden als Metadaten am Task gespeichert, damit die UI den Task dem richtigen Channel zuordnen und kontextspezifische Aktionen anbieten kann (z.B. "Tank prüfen" für Fertigation, "Sprühflasche vorbereiten" für Foliar).

### 4.8 UI-Konzept

**PhaseEntry-Card (Zusammenfassung):**

- Bei Multi-Channel: Channel-Chips unterhalb der Phase-Zielwerte
- Jeder Chip zeigt: Icon (Fertigation/Drench/Foliar/Top Dress) + Label + Kurzinfo (z.B. "3x/Tag" für Fertigation, "Mo/Mi/Fr" für Drench)
- Deaktivierte Channels werden ausgegraut dargestellt

**Expandierte Ansicht (PhaseEntry-Detail):**

- Channel-Cards als MUI Accordion
- Jede Card enthält:
  - Header: Icon + Label + Application Method Badge + Enabled-Toggle
  - Schedule-Zusammenfassung (Wochentage oder Intervall)
  - Dünger-Tabelle mit Dosierungen und mixing_priority
  - EC/pH-Override-Anzeige (falls gesetzt, mit "Override"-Badge)
  - Tank-Verknüpfung (bei Fertigation, klickbar zu REQ-014 Tank-Detail)

**PhaseEntryDialog (Bearbeitung):**

- Neuer Accordion-Abschnitt "Ausbringungskanäle" unterhalb der bestehenden Phase-Felder
- Add-Button: "+ Channel hinzufügen" -> ChannelCreateDialog
- Pro Channel: Edit/Delete/Toggle-Enabled Aktionen
- ChannelCreateDialog: Step 1 (Methode wählen) -> Step 2 (Parameter) -> Step 3 (Schedule) -> Step 4 (Dünger)

**Legacy-Toggle:**

- Bei Phase-Entries mit `delivery_channels=[]`: Button "Zu Multi-Channel konvertieren"
- Klick ruft `POST .../migrate-to-channels` auf
- Erstellt einen synthetischen Channel aus den Legacy-Feldern
- Rückkonvertierung: Nicht vorgesehen (Legacy-Felder bleiben erhalten, werden nur ignoriert)

**Erfahrungsstufen (REQ-021):**

| Stufe | Sichtbarkeit |
|---|---|
| Beginner | Multi-Channel ausgeblendet — nur Legacy-Felder sichtbar |
| Intermediate | Multi-Channel verfügbar, aber als "Erweitert" markiert |
| Expert | Multi-Channel prominent, alle Parameter sichtbar |

### 4.9 Migrationsstrategie

Die Einführung von Multi-Channel Delivery erfolgt in 4 Phasen, um maximale Rückwärtskompatibilität sicherzustellen:

**Phase 1 — Additive Erweiterung (Initial-Release):**

- `delivery_channels` wird als neues Feld mit Default `[]` hinzugefügt
- Alle bestehenden Phase-Entries behalten `delivery_channels=[]`
- Legacy-Felder (`feeding_frequency_per_week`, `volume_per_feeding_liters`, Phase-Level `fertilizer_dosages`) funktionieren unverändert
- Engines prüfen `if entry.delivery_channels:` und verwenden Channel-Logik, sonst Legacy

**Phase 2 — Dual-Mode-Betrieb:**

- `get_effective_channels()` Helper verfügbar
- Services und Celery-Tasks nutzen `get_effective_channels()` als einheitlichen Einstiegspunkt
- Legacy-Felder werden intern zu synthetischem Channel konvertiert (ID: `__legacy__`)
- Keine Datenbank-Migration erforderlich

**Phase 3 — Optionale Migration:**

- Migrations-Endpoint `POST .../migrate-to-channels` verfügbar
- Nutzer können bestehende Pläne explizit konvertieren
- Legacy-Felder bleiben unverändert (kein Datenverlust)
- UI bietet "Konvertieren"-Button an

**Phase 4 — Deprecation (zukünftig):**

- Legacy-Felder werden als `deprecated` markiert (Pydantic `deprecated=True`)
- Neue Pläne werden standardmäßig mit einem Channel erstellt
- Bestehende Pläne mit `delivery_channels=[]` funktionieren weiterhin
- Kein harter Breaking Change — Legacy bleibt unbegrenzt unterstützt

### 4.10 AQL-Beispielabfragen

**Channel-spezifische Dosierungen für eine Pflanze:**

```aql
LET plant = DOCUMENT(CONCAT("PlantInstance/", @plant_key))

// Zugewiesenen Plan laden
LET plan = FIRST(
  FOR v IN 1..1 OUTBOUND plant FOLLOWS_PLAN
    RETURN v
)

// Aktuelle Phase
LET phase = FIRST(
  FOR v IN 1..1 OUTBOUND plant CURRENT_PHASE
    RETURN v
)

// Phase-Entry passend zur Phase
LET entry = FIRST(
  FOR v IN 1..1 OUTBOUND plan HAS_PHASE_ENTRY
    FILTER v.phase_name == phase.name
    RETURN v
)

// Channel-spezifische Dünger laden
LET channels = (
  FOR channel IN entry.delivery_channels
    FILTER channel.enabled == true
    LET ferts = (
      FOR fert, uf IN 1..1 OUTBOUND entry USES_FERTILIZER
        FILTER uf.channel_id == channel.channel_id
        SORT fert.mixing_priority ASC
        RETURN {
          fertilizer: fert.product_name,
          brand: fert.brand,
          ml_per_liter: uf.ml_per_liter,
          optional: uf.optional,
          tank_safe: fert.tank_safe
        }
    )
    RETURN {
      channel_id: channel.channel_id,
      label: channel.label,
      method: channel.application_method,
      target_ec: channel.target_ec_ms != null
        ? channel.target_ec_ms
        : entry.target_ec_ms,
      schedule: channel.schedule,
      fertilizers: ferts
    }
)

RETURN {
  plant_key: plant._key,
  plan_name: plan.name,
  phase: entry.phase_name,
  channels: channels
}
```

**Alle fälligen Channels für heute (Celery-Task Input):**

```aql
LET today = DATE_ISO8601(DATE_NOW())
LET today_weekday = DATE_DAYOFWEEK(DATE_NOW())
// DATE_DAYOFWEEK: 0=Sonntag..6=Samstag -> Konvertierung zu 0=Montag nötig

FOR run IN PlantingRun
  FILTER run.status == 'active'

  // NutrientPlan des Runs
  LET plan = FIRST(
    FOR v IN 1..1 OUTBOUND run RUN_FOLLOWS_PLAN
      RETURN v
  )
  FILTER plan != null

  // Phase-Entries mit Channels
  FOR entry, he IN 1..1 OUTBOUND plan HAS_PHASE_ENTRY
    FOR channel IN entry.delivery_channels
      FILTER channel.enabled == true
      FILTER channel.schedule != null
      FILTER (
        channel.schedule.schedule_mode == 'weekdays'
          // Konvertierung: DATE_DAYOFWEEK (0=So) -> weekday_schedule (0=Mo)
          ? ((today_weekday + 6) % 7) IN channel.schedule.weekday_schedule
          : true  // Intervall-Modus erfordert last_date — Prüfung in Python
      )
      RETURN {
        run_key: run._key,
        entry_key: entry._key,
        channel_id: channel.channel_id,
        channel_label: channel.label,
        method: channel.application_method,
        schedule: channel.schedule
      }
```

**Feeding-History gefiltert nach Channel:**

```aql
FOR event, fe IN 1..1 OUTBOUND DOCUMENT(CONCAT("PlantInstance/", @plant_key)) FED_BY
  FILTER event.channel_id == @channel_id
  SORT event.timestamp DESC
  LIMIT @limit
  RETURN {
    timestamp: event.timestamp,
    channel_id: event.channel_id,
    method: event.application_method,
    volume: event.volume_applied_liters,
    ec_before: event.measured_ec_before,
    ec_after: event.measured_ec_after,
    ph_before: event.measured_ph_before,
    ph_after: event.measured_ph_after
  }
```

## 5. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Fertilizers (globale Stammdaten) | Nein | Ja | Ja |
| NutrientPlans (Tenant-scoped) | Mitglied | Mitglied | Mitglied |
| FeedingEvents (Tenant-scoped) | Mitglied | Mitglied | Admin |
| WateringEvents (Tenant-scoped) | Mitglied | Mitglied | Admin |
| NutrientCalculations (zustandslos) | Nein | — | — |

## 6. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species für substrat-spezifische Empfehlungen
- REQ-002 (Standort): SubstrateBatch für EC/pH-Historie
- REQ-003 (Phasen): GrowthPhase für NPK-Profile, Flushing-Trigger
- REQ-005 (Sensorik): EC/pH-Messungen zur Validierung

**Wird benötigt von:**
- REQ-006 (Tasks): Automatische Feeding-Tasks; **HOCH** — `generate_watering_tasks` Celery-Task nutzt WateringSchedule + WateringScheduleEngine zur täglichen Gießplan-Task-Generierung
- REQ-007 (Ernte): Flushing-Protokoll vor Ernte
- REQ-009 (Dashboard): EC/pH-Ampeln, Kosten-Tracking
- REQ-013 (Pflanzdurchlauf): **HOCH** — NutrientPlan-Zuweisung an PlantingRun via `RUN_FOLLOWS_PLAN`-Edge; Cascade auf PlantInstances via `FOLLOWS_PLAN`
- REQ-014 (Tankmanagement): **HOCH** — MixingResult als Input für Tank-Befüllung; EC-Budget basiert auf Tank-Volumen; Gießplan-Bestätigungsflow (confirm/quick-confirm) nutzt NutrientPlan-Dosierungen
- REQ-022 (Pflegeerinnerungen): **MITTEL** — Duplikat-Vermeidung: Pflanzen mit aktivem NutrientPlan+WateringSchedule erhalten keine WATERING/FERTILIZING Care-Reminders

**Externe Integrationen:**
- Dünger-Datenbanken (NPK-Werte, Preise)
- Inventar-Management-Systeme

## 7. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Misch-Reihenfolge-Validierung:** System warnt bei simultaner Zugabe inkompatibler Dünger
- [ ] **EC-Budget-Kalkulation:** Automatische Verteilung der Ziel-EC auf Komponenten
- [ ] **Substrat-spezifische Grenzen:** EC-Limits für Hydro/Coco/Soil werden enforced
- [ ] **Flushing-Scheduler:** Graduelle EC-Reduktion über 7-21 Tage (substrat-abhängig)
- [ ] **Runoff-Analyse:** Interpretation von Input/Output-EC für DTW-Systeme
- [ ] **Inkompatibilitäten-Check:** CalMag + Sulfat, Ca + Phosphat werden erkannt
- [ ] **pH-Drift-Schätzung:** Automatische Berechnung benötigter pH-Korrektur
- [ ] **Step-by-Step-Anleitung:** Menschenlesbare Mixing-Instructions
- [ ] **Inventar-Tracking:** Warnung bei niedrigem Stock (<2 Wochen Vorrat)
- [ ] **Kosten-Tracking:** Berechnung der Düngekosten pro Feeding
- [ ] **Multi-Part-Support:** A+B-Dünger mit korrekter Reihenfolge
- [ ] **Biologische Zusätze:** Temperatur-Validierung für lebende Organismen
- [ ] **NPK-Balance:** Automatische Warnung bei Ungleichgewicht (z.B. zu viel N in Blüte)
- [ ] **Foliar-Warnung Blüte (G-013):** Soft-Warnung bei `application_method='foliar'` in Blütephase ab Woche 2 (Schimmelrisiko, Geschmacksverunreinigung). Kein Hardblock — IPM-Notfallbehandlungen (REQ-010, `is_emergency: true`) sind ausgenommen
- [ ] **Dosierungs-Historie:** Tracking aller Feedings mit EC/pH-Messungen
- [ ] **Recipe-Templates:** Speicherbare Dünge-Rezepte für wiederkehrende Setups
- [ ] **Nährstoffplan-CRUD:** Erstellen, Lesen, Aktualisieren, Löschen von Lifecycle-Nährstoffplänen
- [ ] **Phase-Entry-Verwaltung:** Pro Phase Zielwerte (NPK, EC, pH), Frequenz und Volumen definierbar
- [ ] **Dünger-Zuweisung mit Dosierungen:** Pro Phase-Entry konkrete Dünger mit ml/L zuweisbar
- [ ] **Plan-Zuweisung an PlantInstance:** 1:1-Zuweisung, wechselbar, aktuelle Dosierungen ableitbar
- [ ] **Plan-Klonen (Deep Copy):** Plan mit allen Entries und Dünger-Zuweisungen als unabhängige Kopie
- [ ] **Vollständigkeits-Validierung:** Warnung bei fehlenden Pflichtphasen (seedling, vegetative, flowering)
- [ ] **EC-Budget-Validierung:** Abgleich Dünger-EC-Summe vs. Ziel-EC pro Phase-Entry (Toleranz ±0.3 mS)
- [ ] **Plan-Filterung:** Filter nach Substrattyp, Tags und Template-Status
- [ ] **Düngemittel-Filterung:** Düngemittel-Tabelle filterbar nach Dünger-Typ (`fertilizer_type`), Hersteller (`brand`, Teilstring-Suche), Tank-Sicherheit (`tank_safe`) und Bio-Zertifizierung (`is_organic`). Alle Filter optional und kombinierbar (AND-Verknüpfung).
- [ ] **Gantt-Diagramm:** Nährstoffplan als interaktives Gantt-Diagramm mit Wochen-Zeitachse und Dünger-Zeilen
- [ ] **Gantt-Phasen-Header:** Zusammenfassende Phasenbalken über den Dünger-Zeilen mit EC/pH-Beschriftung
- [ ] **Gantt-Phasenfarben:** Farbcodierung nach Wachstumsphase (Germination, Seedling, Vegetative, Flowering, Harvest)
- [ ] **Gantt-Hover-Tooltip:** Vollständige Phase-Details bei Maus-Hover (Zielwerte, Dünger-Tabelle, EC-Budget-Status, Notizen)
- [ ] **Gantt-Dünger-Zeilen:** Alle im Plan genutzten Dünger als eigene Zeilen mit Dosierungs-Beschriftung auf den Balken
- [ ] **Gantt-Optionale-Dünger:** Optionale Dünger visuell unterscheidbar (gestrichelt/reduzierte Opazität)
- [ ] **Gantt-Lücken-Erkennung:** Wochen ohne Phase-Entry als leere Spalten (grauer Hintergrund) hervorgehoben
- [ ] **Gantt-Überlappung:** Überlappende Phase-Entries als gestapelte Balken mit Warnung dargestellt
- [ ] **WateringSchedule-Validierung:** Mode-abhängige Pflichtfelder werden korrekt enforced (weekdays → weekday_schedule, interval → interval_days)
- [ ] **WateringSchedule-Modus Weekdays:** Feste Wochentage (0–6) werden akzeptiert, Duplikate abgelehnt
- [ ] **WateringSchedule-Modus Interval:** Intervall 1–90 Tage wird akzeptiert, 0 oder >90 abgelehnt
- [ ] **WateringSchedule auf NutrientPlan:** Plan mit `watering_schedule=null` funktioniert wie bisher (Abwärtskompatibilität)
- [ ] **WateringScheduleEngine.is_watering_due:** Korrekte Prüfung für beide Modi (weekdays + interval)
- [ ] **WateringScheduleEngine.get_next_watering_dates:** Liefert korrekte Datumsliste für 14-Tage-Fenster
- [ ] **WateringScheduleEngine.resolve_dosages_for_run:** Pflanzen werden korrekt nach Phase gruppiert, unmatched-Phasen erkannt
- [ ] **RUN_FOLLOWS_PLAN-Edge:** PlantingRun → NutrientPlan Zuweisung wird als Edge mit assigned_at/assigned_by gespeichert
- [ ] **Fertigation-Ausschluss:** `application_method='fertigation'` wird in WateringSchedule abgelehnt (Tank-basiert, nicht manuell schedulbar)
- [ ] **Multi-Channel DeliveryChannel-Modell:** Embedded Model mit channel_id, application_method, methoden-spezifischen Params (FertigationParams/DrenchParams/FoliarParams/TopDressParams), Channel-Level Schedule, EC/pH-Override und eigener Düngerliste
- [ ] **Multi-Channel Legacy-Kompatibilität:** `delivery_channels=[]` -> Legacy-Felder aktiv; `delivery_channels` nicht leer -> Legacy-Felder ignoriert
- [ ] **Channel-ID Eindeutigkeit (MCD-V08):** channel_id muss innerhalb Phase-Entry eindeutig sein
- [ ] **Params-Match-Validierung (MCD-V07):** fertigation_params Pflicht bei method=fertigation, analog für alle Methoden
- [ ] **Tank-Safe-Prüfung (MCD-V01):** Fertigation-Channels erlauben nur Dünger mit `tank_safe=true`
- [ ] **EC-Budget per Channel (MCD-V02):** EC-Budget-Validierung pro Channel (fertigation, drench)
- [ ] **EC nicht anwendbar Top-Dress (MCD-V03):** Info-Hinweis bei Top-Dress-Channels
- [ ] **Foliar EC-Limit (MCD-V04):** Warnung bei target_ec > 1.0 mS auf Foliar-Channels
- [ ] **Cross-Channel-Validierung (MCD-V20-V22):** Dünger-Duplikat-Warnung, Gesamt-EC-Plausibilität, Tank-Konflikt
- [ ] **USES_FERTILIZER channel_id:** Edge-Attribut channel_id für Channel-spezifische Dünger-Zuweisungen (`null` = Legacy)
- [ ] **FeedingEvent/WateringEvent channel_id:** Optionales channel_id-Feld für Channel-Zuordnung
- [ ] **WateringScheduleEngine.get_due_channels:** Ermittelt fällige Channels am Prüfdatum, leere Liste bei Legacy-Modus
- [ ] **get_effective_channels() Helper:** Legacy-zu-Channel-Konvertierung (synthetischer `__legacy__` Channel) für einheitliche Verarbeitung
- [ ] **DeliveryChannelValidator:** Kanal-übergreifende Regeln (MCD-V20 bis MCD-V22)
- [ ] **Channel CRUD-Endpoints:** POST/PUT/DELETE für Channels und Channel-Dünger (6 neue Endpoints)
- [ ] **Migrations-Endpoint:** POST .../migrate-to-channels für Legacy-Konvertierung
- [ ] **Celery Multi-Channel Tasks:** Pro fälligem Channel ein separater Task mit channel_id und application_method in Metadaten
- [ ] **UI Channel-Chips:** Phase-Entry-Cards zeigen Channel-Zusammenfassung als Chips mit Icon und Kurzinfo
- [ ] **UI Channel-Accordion:** Expandierbare Channel-Cards mit Schedule, Dosierungen, EC/pH-Override und Tank-Link
- [ ] **UI Channel-Dialog:** ChannelCreateDialog mit 4-Step Wizard (Methode -> Parameter -> Schedule -> Dünger)
- [ ] **REQ-021 Stufen-Integration:** Multi-Channel ausgeblendet bei Beginner, "Erweitert" bei Intermediate, voll sichtbar bei Expert
- [ ] **Max Channels (MCD-V12):** Maximal 10 Channels pro NutrientPlanPhaseEntry
- [ ] **Fertigation Schedule-Erlaubnis:** In Channel-Level WateringSchedule ist `application_method='fertigation'` erlaubt (Abweichung von Plan-Level)
- [ ] **Fertigation Intra-Day:** `runs_per_day` + `duration_minutes` ergänzen den Tages-Schedule für Fertigation-Channels

### Testszenarien:

**Szenario 1: Multi-Part Base A+B Mixing**
```
GIVEN: Growzelt Hydro-Setup, Ziel-EC 1.8 mS, Wasser-EC 0.2 mS
WHEN: Calculator mit FloraGro (Base A) + FloraMicro (Base B) + CalMag
THEN:
  - Reihenfolge: 1) CalMag, 2) FloraMicro (A), 3) FloraGro (B)
  - Warnung wenn B vor A: "KRITISCH: Base A muss vor Base B"
  - EC-Summe: 1.8 ± 0.1 mS
  - Anleitung: "Rühre 30s nach jeder Zugabe"
```

**Szenario 2: Flushing vor Ernte**
```
GIVEN: Cannabis in Blüte, aktuelle EC 2.2 mS, 14 Tage bis Ernte, Coco-Substrat
WHEN: FlushingProtocol.get_schedule()
THEN:
  - Empfohlene Dauer: 10-14 Tage
  - Tag 0-4: Reduzierte Dosis (EC 1.5 → 1.0)
  - Tag 5-9: Minimale Dosis (EC 1.0 → 0.5)
  - Tag 10-14: Nur Wasser (EC 0.0)
  - Warnung: "Blätter vergilben = normal"
```

**Szenario 3: Salzakkumulation (Runoff-Analyse)**
```
GIVEN: Input EC 1.6 mS, Runoff EC 2.8 mS (Differenz +1.2)
WHEN: RunoffAnalyzer.analyze()
THEN:
  - Status: SALT_BUILDUP
  - Action: "Flush erforderlich - 3x Wasser-Volumen durchspülen"
  - Nächste Düngung: Dosierung um 30% reduzieren
```

**Szenario 4: Inkompatibilität CalMag + Sulfat**
```
GIVEN: Mischung enthält CalMag (15% Ca) + Bittersalz (MgSO4)
WHEN: MixingSafetyValidator.validate_combination()
THEN:
  - Severity: CRITICAL
  - Message: "Calcium-Sulfat-Ausfällung (Gips)"
  - Mitigation: "CalMag zuerst, 5min warten, dann Bittersalz"
```

**Szenario 5: Inventar-Warnung**
```
GIVEN: FloraGro Stock: 250ml, durchschnittlicher Verbrauch: 150ml/Woche
WHEN: Wöchentlicher Inventory-Check
THEN:
  - Alert: "REORDER_NEEDED"
  - Verbleibende Wochen: 1.7
  - Empfehlung: "Bestelle 1L Flasche (reicht 6 Wochen)"
```

**Szenario 6: Nährstoffplan erstellen mit 4 Phasen und Düngern**
```
GIVEN: Nutzer erstellt Plan "Tomato Heavy Coco" mit recommended_substrate_type "coco"
WHEN: 4 Phase-Entries (seedling, vegetative, flowering, harvest) mit je 2-3 Düngern
THEN:
  - Plan wird mit Version 1 erstellt
  - Seedling-Entry: EC 0.8, pH 6.0, NPK 2-1-2, CalMag 1ml/L + FloraGro 0.5ml/L
  - Vegetative-Entry: EC 1.4, pH 5.8, NPK 3-1-2, CalMag 1.5ml/L + FloraGro 2ml/L + FloraMicro 2ml/L
  - Flowering-Entry: EC 1.8, pH 6.0, NPK 1-3-3, CalMag 1ml/L + FloraBloom 3ml/L + PK 13-14 0.5ml/L
  - Harvest-Entry: EC 0.0, pH 6.0, keine Dünger (Flush-Phase)
  - Validierung: Plan vollständig (alle Pflichtphasen abgedeckt)
```

**Szenario 7: Plan einer PlantInstance zuweisen → aktuelle Dosierungen ableiten**
```
GIVEN: PlantInstance "Tomate-001" in Phase "vegetative", Plan "Tomato Heavy Coco" zugewiesen
WHEN: GET /api/v1/plant-instances/Tomate-001/current-dosages
THEN:
  - Rückgabe der vegetative Phase-Entry-Daten
  - target_ec: 1.4, target_ph: 5.8
  - dosages: [{CalMag, 1.5ml/L, prio 3}, {FloraMicro, 2ml/L, prio 4}, {FloraGro, 2ml/L, prio 5}]
  - mixing_instructions: Schritt-für-Schritt-Anleitung gemäß Mixing-Priority
```

**Szenario 8: Plan klonen und unabhängig anpassen**
```
GIVEN: Bestehender Plan "Tomato Heavy Coco" (Version 3, 4 Phase-Entries)
WHEN: POST /api/v1/nutrient-plans/{key}/clone mit new_name "Tomato Light Coco"
THEN:
  - Neuer Plan "Tomato Light Coco" (Version 1, eigener _key)
  - Alle 4 Phase-Entries als unabhängige Kopien
  - Alle Dünger-Zuweisungen (USES_FERTILIZER-Edges) kopiert
  - CLONED_FROM-Edge vom neuen zum Quell-Plan
  - Änderungen am Klon haben keinen Effekt auf das Original
```

**Szenario 9: Plan-Zuweisung wechseln**
```
GIVEN: PlantInstance "Tomate-001" folgt Plan "Tomato Heavy Coco"
WHEN: POST /api/v1/plant-instances/Tomate-001/nutrient-plan mit plan_key = "Auto Light Feed"
THEN:
  - Bisherige FOLLOWS_PLAN-Edge wird entfernt
  - Neue FOLLOWS_PLAN-Edge zu "Auto Light Feed" erstellt
  - assigned_at und assigned_by werden aktualisiert
  - Aktuelle Dosierungen basieren jetzt auf "Auto Light Feed"
```

**Szenario 10: Gantt-Diagramm — Vollständiger 4-Phasen-Plan**
```
GIVEN: NutrientPlan "Tomato Heavy Coco" mit 4 Phase-Entries:
       - Seedling:   Woche 1–2,  EC 0.8, CalMag (1ml/L) + FloraGro (0.5ml/L)
       - Vegetative:  Woche 3–6,  EC 1.4, CalMag (1.5ml/L) + FloraGro (2ml/L) + FloraMicro (2ml/L)
       - Flowering:   Woche 7–12, EC 1.8, CalMag (1ml/L) + FloraBloom (3ml/L) + PK 13-14 (0.5ml/L, optional)
       - Harvest:     Woche 13–14, EC 0.0, keine Dünger (Flush)
WHEN: Nutzer öffnet den Tab "Zeitplan" auf der NutrientPlanDetailPage
THEN:
  - X-Achse zeigt Wochen 1–14
  - Phasen-Header-Zeile: 4 farbcodierte Balken (Seedling W1–2, Vegetative W3–6, Flowering W7–12, Harvest W13–14)
  - Y-Achse zeigt 4 Dünger-Zeilen: CalMag, FloraGro, FloraMicro, FloraBloom, PK 13-14
  - CalMag-Zeile: 3 Balken (Seedling W1–2, Vegetative W3–6, Flowering W7–12) mit jeweiliger ml/L-Beschriftung
  - PK 13-14-Zeile: 1 gestrichelter Balken (Flowering W7–12, optional) mit 0.5ml/L
  - Harvest-Wochen (13–14): Keine Dünger-Balken, Phasen-Header zeigt "Harvest" in Orange
```

**Szenario 11: Gantt-Diagramm — Hover-Tooltip zeigt Phase-Details**
```
GIVEN: Gantt-Diagramm des Plans "Tomato Heavy Coco" ist gerendert
WHEN: Nutzer fährt mit Maus über den Flowering-Phasen-Header-Balken (Woche 7–12)
THEN: Tooltip zeigt:
  - "Flowering — Woche 7–12"
  - Zielwerte: EC 1.8 mS, pH 6.0, NPK 1-3-3
  - Dünger-Tabelle:
    | Dünger       | ml/L | Optional | Reihenfolge |
    | CalMag       | 1.0  | Nein     | 3           |
    | FloraBloom   | 3.0  | Nein     | 5           |
    | PK 13-14     | 0.5  | Ja       | 6           |
  - Fütterung: 2× pro Woche
  - EC-Budget: ✓ gültig (falls Validierungsdaten geladen)
```

**Szenario 12: Gantt-Diagramm — Lücken-Erkennung**
```
GIVEN: NutrientPlan "Quick Veg Only" mit nur 2 Phase-Entries:
       - Seedling:   Woche 1–2
       - Vegetative:  Woche 5–8  (Lücke: Woche 3–4 fehlt)
WHEN: Gantt-Diagramm wird gerendert
THEN:
  - Wochen 3–4 werden als leere Spalten mit grauem Hintergrund angezeigt
  - Kein Dünger-Balken in Woche 3–4
  - Visuell erkennbar, dass eine Lücke im Plan existiert
```

**Szenario 13: Vollständigkeits-Warnung bei fehlenden Pflichtphasen**
```
GIVEN: Plan "Quick Veg Only" mit nur 1 Phase-Entry (vegetative)
WHEN: GET /api/v1/nutrient-plans/{key}/validate
THEN:
  - completeness.complete: false
  - missing_phases: ["seedling", "flowering"]
  - warnings: ["Fehlende Pflichtphasen: seedling, flowering"]
  - overall_valid: false
```

**Szenario 14: EC-Budget-Abweichung erkennen**
```
GIVEN: Phase-Entry "flowering" mit target_ec 1.8 mS
       Dünger: FloraBloom (0.15 mS/ml × 3ml/L = 0.45) + PK 13-14 (0.2 mS/ml × 0.5ml/L = 0.1)
       Berechnete EC: 0.55 mS (deutlich unter 1.8 mS)
WHEN: GET /api/v1/nutrient-plans/{key}/validate
THEN:
  - ec_budget_checks für flowering: valid=false, deviation=1.25
  - status: "EC_BUDGET_MISMATCH"
  - recommendation: "Dosierungen anpassen: Ziel 1.8 mS, berechnet 0.55 mS (Abweichung 1.25)"
```

**Szenario 15: Gießplan mit Wochentags-Modus erstellen**
```
GIVEN: NutrientPlan "Tomato Heavy Coco" mit 4 Phase-Entries
WHEN: PUT /api/v1/nutrient-plans/{key} mit watering_schedule:
      { schedule_mode: "weekdays", weekday_schedule: [0, 2, 4],
        preferred_time: "08:00", application_method: "drench",
        reminder_hours_before: 2 }
THEN:
  - Plan wird aktualisiert mit watering_schedule
  - Gießtermine: jeden Montag, Mittwoch, Freitag um 08:00
  - Erinnerungen um 06:00 (2h vorher)
  - Version wird inkrementiert
```

**Szenario 16: Gießplan mit Intervall-Modus**
```
GIVEN: NutrientPlan "Orchid Soak Weekly" für Orchideen
WHEN: PUT /api/v1/nutrient-plans/{key} mit watering_schedule:
      { schedule_mode: "interval", interval_days: 7,
        preferred_time: "10:00", application_method: "drench" }
THEN:
  - Plan wird aktualisiert mit 7-Tage-Intervall
  - WateringScheduleEngine.get_next_watering_dates liefert [Tag 7, Tag 14] ab letztem Gießen
```

**Szenario 17: WateringSchedule-Validierungsfehler**
```
GIVEN: NutrientPlan
WHEN: Nutzer setzt schedule_mode="weekdays" ohne weekday_schedule
THEN: Validierungsfehler 422: "weekday_schedule ist Pflicht bei mode='weekdays'"

WHEN: Nutzer setzt schedule_mode="interval" mit interval_days=0
THEN: Validierungsfehler 422: "interval_days muss >= 1 sein"

WHEN: Nutzer setzt application_method="fertigation" in WateringSchedule
THEN: Validierungsfehler 422: "Fertigation wird über Tankmanagement (REQ-014) gesteuert"
```

<!-- Quelle: Cannabis Indoor Grower Review G-013 -->
**Szenario 18: Foliar-Warnung in der Blütephase**
```
GIVEN: PlantInstance "Cannabis-001" in Phase "flowering", Blütewoche 3
WHEN: POST /api/v1/feeding-events mit application_method="foliar", volume_applied_liters=0.5
THEN:
  - HTTP 201 Created (kein Block)
  - Response enthält warnings: ["Foliar-Feeding in der Blüte (ab Woche 2) vermeiden! Schimmelrisiko auf Buds, Geschmacksverunreinigung und Rückstände auf Erntegut."]
  - FeedingEvent wird trotz Warnung erstellt

GIVEN: PlantInstance "Cannabis-001" in Phase "flowering", Blütewoche 3
WHEN: POST /api/v1/feeding-events mit application_method="foliar", verknüpft mit TreatmentApplication (is_emergency=true)
THEN:
  - HTTP 201 Created
  - Response enthält KEINE Foliar-Warnung (IPM-Notfallbehandlung ausgenommen)

GIVEN: PlantInstance "Cannabis-001" in Phase "flowering", Blütewoche 1
WHEN: POST /api/v1/feeding-events mit application_method="foliar"
THEN:
  - HTTP 201 Created
  - Response enthält info: ["Blüte Woche 1: Foliar-Feeding noch möglich, ab Woche 2 nicht mehr empfohlen."]

GIVEN: PlantInstance "Cannabis-001" in Phase "vegetative"
WHEN: POST /api/v1/feeding-events mit application_method="foliar"
THEN:
  - HTTP 201 Created
  - Keine Warnung (Foliar in Vegetationsphase uneingeschränkt erlaubt)
```

**Szenario 19: Multi-Channel — Fertigation + Drench + Foliar in einer Phase**
```
GIVEN: NutrientPlan "Pro Hydro" mit Phase-Entry "vegetative" und 3 Channels:
       - Channel "dripper-base" (fertigation, 3x/Tag, 5min, Tank "main-tank"):
         CalMag 1.5ml/L, FloraGro 2ml/L, FloraMicro 2ml/L (alle tank_safe=true)
       - Channel "compost-tea" (drench, 0.5L/Feeding, Intervall 7 Tage):
         Komposttee 50ml/L (tank_safe=false)
       - Channel "micro-foliar" (foliar, 0.2L/Spray, Intervall 14 Tage):
         Eisen-Chelat 0.5ml/L, Kalzium-Spray 1ml/L
WHEN: GET /api/v1/nutrient-plans/{key}/validate
THEN:
  - channel_validations enthält 3 Einträge
  - "dripper-base": EC-Budget geprüft, Tank-Safe OK (alle Dünger tank_safe=true)
  - "compost-tea": EC-Budget geprüft, Komposttee tank_safe=false -> kein Fehler (Drench, nicht Fertigation)
  - "micro-foliar": EC-Budget INFO (Foliar), keine Blüte-Warnung (Phase=vegetative)
  - Cross-Channel: Keine Dünger-Duplikate, Gesamt-EC plausibel
```

**Szenario 20: Multi-Channel — Legacy-Kompatibilität bei leeren delivery_channels**
```
GIVEN: Bestehender Plan "Old Plan" mit Phase-Entry:
       feeding_frequency_per_week=3, volume_per_feeding_liters=2.0,
       fertilizer_dosages=[CalMag 1ml/L], delivery_channels=[]
WHEN: GET /api/v1/plant-instances/{key}/current-dosages
THEN:
  - Legacy-Felder werden verwendet (feeding_frequency=3, volume=2.0)
  - CalMag 1ml/L aus Phase-Level fertilizer_dosages
  - Keine Channels in Response
  - Verhalten identisch zu vor der Multi-Channel-Erweiterung
```

**Szenario 21: Tank-Safe-Validierung für Fertigation-Channel (MCD-V01)**
```
GIVEN: Phase-Entry mit Fertigation-Channel "dripper-main", Tank "main-tank"
WHEN: Dünger "Komposttee" (tank_safe=false) wird dem Channel zugewiesen
       POST /api/v1/nutrient-plans/entries/{ek}/channels/dripper-main/fertilizers
THEN:
  - Zuweisung wird gespeichert (kein Hardblock bei Zuweisung)
  - GET /api/v1/nutrient-plans/{key}/validate liefert:
    channel_validations: [{
      channel_id: "dripper-main",
      issues: [{rule_id: "MCD-V01", severity: "CRITICAL",
        message: "Komposttee ist nicht tank-safe — nicht für Fertigation geeignet.
                  Schwebstoffe verstopfen Tropfer und verursachen Biofilm im Tank."}]
    }]
```

**Szenario 22: Legacy-zu-Multi-Channel-Migration**
```
GIVEN: Plan "Tomato Heavy Coco" mit 4 Phase-Entries, alle mit delivery_channels=[],
       Plan-Level watering_schedule: {mode: "weekdays", weekday_schedule: [0,2,4]}
WHEN: POST /api/v1/nutrient-plans/{key}/migrate-to-channels
THEN:
  - 4 Phase-Entries erhalten je einen synthetischen Channel:
    channel_id="__legacy__", label="Standard", method="drench",
    drench_params={volume_per_feeding_liters: entry.volume_per_feeding_liters},
    schedule: kopiert von Plan-Level watering_schedule
  - Response: {migrated_entries: 4, channels_created: 4}
  - Legacy-Felder bleiben unverändert (Rollback durch Leeren von delivery_channels möglich)
```

**Szenario 23: Celery Task-Generierung mit Multi-Channel**
```
GIVEN: PlantingRun "run-001" folgt Plan mit Phase-Entry "vegetative":
       - Channel "dripper-base" (fertigation, Schedule: weekdays [0,2,4])
       - Channel "foliar-micro" (foliar, Schedule: interval 14, letztes Datum vor 14 Tagen)
       - Channel "top-dress" (top_dress, kein Schedule)
WHEN: Celery-Task "watering-generate-tasks-daily" läuft am Montag (weekday=0)
THEN:
  - 2 Tasks generiert:
    1. "watering:run-001:dripper-base:2026-02-27" (Fertigation fällig: Montag in weekday_schedule)
    2. "watering:run-001:foliar-micro:2026-02-27" (Foliar fällig: 14 Tage seit letztem)
  - Kein Task für "top-dress" (kein Schedule -> keine automatische Generierung, MCD-V09)
  - Task-Metadaten enthalten channel_id und application_method
```

**Szenario 24: Params-Match-Validierung (MCD-V07)**
```
GIVEN: Channel-Erstellung mit application_method="fertigation"
WHEN: POST mit drench_params statt fertigation_params:
      {channel_id: "test", label: "Test", application_method: "fertigation",
       drench_params: {volume_per_feeding_liters: 2.0}}
THEN:
  - Validierungsfehler 422: "fertigation_params ist erforderlich für application_method='fertigation'"
  - Zusätzlich: "drench_params darf nicht gesetzt sein bei application_method='fertigation'"
```

**Szenario 25: Cross-Channel Dünger-Duplikat-Warnung (MCD-V20)**
```
GIVEN: Phase-Entry "vegetative" mit 2 Channels:
       - Channel "dripper-base" (fertigation): CalMag 1.5ml/L
       - Channel "supplement" (drench): CalMag 2.0ml/L
WHEN: GET /api/v1/nutrient-plans/{key}/validate
THEN:
  - Cross-Channel-Warnung: "CalMag ist in 2 Channels zugewiesen — Gesamt-EC-Beitrag prüfen."
  - Severity: WARNING (kein Block)
```

**Szenario 26: Channel-Level EC/pH Override**
```
GIVEN: Phase-Entry "vegetative" mit target_ec=1.4 mS, target_ph=5.8
       - Channel "dripper-base" (fertigation): target_ec_ms=1.2 (Override)
       - Channel "foliar-micro" (foliar): target_ec_ms=null (Phase-Level gilt)
WHEN: GET /api/v1/nutrient-plans/{key}/validate
THEN:
  - "dripper-base" EC-Budget geprüft gegen target_ec=1.2 (Override)
  - "foliar-micro" EC-Budget geprüft gegen target_ec=1.4 (Phase-Level)
  - Override-Werte werden in Response als "Override" gekennzeichnet
```

---

**Hinweise für RAG-Integration:**
- Keywords: Düngung, NPK, EC, pH, Misch-Reihenfolge, Flushing, Runoff, Salzakkumulation, Nährstoffplan, NutrientPlan, Lifecycle-Plan, Phase-Entry, Dosierung, Plan-Zuweisung, Klonen, Deep-Copy, EC-Budget, Vollständigkeits-Validierung, Gantt-Diagramm, Gantt-Chart, Timeline, Zeitplan, Dünge-Timeline, Hover-Tooltip, Phasen-Farbcodierung, Dünger-Zeilen, Gießplan, WateringSchedule, Gießtermin, Wochentag, Intervall, ScheduleMode, WateringScheduleEngine, RUN_FOLLOWS_PLAN, Gießplan-Workflow, Foliar-Warnung, Blattdüngung-Blüte, Schimmelrisiko, Multi-Channel, DeliveryChannel, Ausbringungskanal, Fertigation, Drench, Foliar, TopDress, FertigationParams, DrenchParams, FoliarParams, TopDressParams, Channel-Schedule, Channel-EC-Override, Tank-Safe, get_due_channels, get_effective_channels, DeliveryChannelValidator, migrate-to-channels, channel_id
- Fachbegriffe: Elektrische Leitfähigkeit, Ausfällung, Chelat, Huminsäure, Osmose, Feeding-Schedule, Nutrient-Profile
- Verknüpfung: Zentral für REQ-003 (Phasen-NPK, NutrientProfile vs. NutrientPlan), REQ-005 (EC-Sensorik), REQ-007 (Pre-Harvest)
- Chemische Formeln: CaSO4, NO3-, Ca2+, Fe-EDTA
- API-Pfade: /nutrient-plans, /nutrient-plans/{key}/clone, /nutrient-plans/{plan_key}/entries, /nutrient-plans/{key}/entries/{ek}/channels, /nutrient-plans/{key}/entries/{ek}/channels/{cid}, /nutrient-plans/entries/{ek}/channels/{cid}/fertilizers, /nutrient-plans/{key}/migrate-to-channels, /plant-instances/{plant_key}/nutrient-plan, /plant-instances/{plant_key}/current-dosages
