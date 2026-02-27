# Agrarbiologisches Anforderungsreview: REQ-007 Erntemanagement

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Indoor-Anbau, Hydroponik, Gewaechshauskultur, Outdoor (ergaenzend)
**Analysiertes Dokument:** `spec/req/REQ-007_Erntemanagement.md` (Version 2.0)
**Kontext-Dokumente:** REQ-001, REQ-003, REQ-004, REQ-008, REQ-010, REQ-013

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Solide Grundlage mit einigen korrekturbeduerfigen Detailfehlern |
| Indoor-Vollstaendigkeit | 4/5 | Cannabis/Hydroponik sehr gut abgedeckt, Zimmerpflanzen fehlen |
| Gemuese/Nutzpflanzen-Abdeckung | 3/5 | Grundstruktur vorhanden, artspezifische Tiefe fehlt |
| Hydroponik-Tiefe | 4/5 | Flushing und EC gut, Substrat-Differenzierung ausbaufaehig |
| Messbarkeit der Parameter | 4/5 | Brix und Trichome messbar, Aroma/Textur subjektiv |
| Praktische Umsetzbarkeit | 4/5 | Factory-Pattern sinnvoll, Datenquellen fuer Referenzwerte duenn |

REQ-007 ist ein fachlich solides und ambitioniertes Dokument, das die Ernteplanung konsequent polymorph und artspezifisch angeht. Die Cannabis-spezifischen Indikatoren (Trichom-Mikroskopie, Multi-Standort-Sampling, Flushing) sind auf hohem Niveau und praxisnah formuliert. Besonders positiv hervorzuheben sind die korrekte Markierung von Flushing als "wissenschaftlich umstritten" mit Verweis auf die Guelph-Studie (2020), die Unterscheidung klimakterischer und nicht-klimakterischer Fruechte sowie die artspezifischen Wassergehalte fuer die Trockengewichtschaetzung. Korrekturbeduerftig sind einzelne biologische Detailfehler, fehlende Karenzzeit-Integration in den Ernte-Workflow, und die unvollstaendige Abdeckung von Dauerkulturen (Perenniale) und Cut-and-Come-Again-Kulturen.

---

## Rot -- Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: Paprika als nicht-klimakterisch klassifiziert -- nur teilweise korrekt [BEHOBEN]

**Anforderung:** `EthyleneRipeningClassifier.NON_CLIMACTERIC_SPECIES` enthaelt `'pepper'` (Zeile ~1008-1011)
**Problem:** Paprika (*Capsicum annuum*) ist ein biologischer Grenzfall. Reife Paprika zeigen klimakterisches Verhalten -- sie produzieren Ethylen waehrend der Farbumfaerbung (Breaker-Stage) und koennen in begrenztem Mass nachreifen, insbesondere wenn sie bereits den Farbumschlag begonnen haben. Unreife gruene Paprika sind dagegen praktisch nicht-klimakterisch. Die pauschale Klassifikation als "nicht-klimakterisch" ist daher fuer Paprika im Farbumschlag falsch und fuehrt zu suboptimalen Ernteempfehlungen: Paprika im Breaker-Stadium koennen durchaus geerntet und nachgereift werden (gaengige Praxis im kommerziellen Anbau).
**Korrekte Formulierung:** Paprika sollte als "bedingt klimakterisch" oder "schwach klimakterisch" gefuehrt werden. Empfehlung: Eine dritte Kategorie `WEAKLY_CLIMACTERIC` einfuehren, oder die `classify()`-Methode um einen Reifegrad-Parameter erweitern, der den aktuellen Farbumschlag-Status beruecksichtigt.
**Gilt fuer Anbaukontext:** Indoor, Gewaechshaus, Outdoor

### F-002: Feige als klimakterisch -- korrekt, aber Ananas als nicht-klimakterisch ist falsch [BEHOBEN]

**Anforderung:** `NON_CLIMACTERIC_SPECIES` enthaelt `'pineapple'` (Zeile ~1011)
**Problem:** Die Ananas (*Ananas comosus*) wird in der Literatur je nach Quelle unterschiedlich klassifiziert. Die International Society for Horticultural Science und neuere Studien (z.B. Paull & Chen, 2003) klassifizieren Ananas als nicht-klimakterisch, allerdings zeigt sie unter bestimmten Bedingungen schwache klimakterische Muster (endogene Ethylen-Produktion bei Reife). In der Praxis ist die Klassifikation als nicht-klimakterisch vertretbar, sollte aber mit einem Hinweis versehen werden, dass Ananas auf exogenes Ethylen reagiert (Ethylen-Begasung wird kommerziell zur Blueteninduktion verwendet -- nicht zur Nachreifung, aber der Mechanismus existiert).
**Korrekte Formulierung:** Ananas in `NON_CLIMACTERIC_SPECIES` belassen, aber in der `classify()`-Rueckgabe einen Hinweis ergaenzen: "Reagiert auf exogenes Ethylen (Blueteninduktion), reift aber nach Ernte nicht signifikant nach."
**Gilt fuer Anbaukontext:** Gewaechshaus, Indoor (tropisch)

### F-003: Melone als klimakterisch -- differenzierungspflichtig [BEHOBEN]

**Anforderung:** `CLIMACTERIC_SPECIES` enthaelt `'melon'` (Zeile ~1006)
**Problem:** Nicht alle Melonen sind klimakterisch. Wassermelonen (*Citrullus lanatus*) sind nicht-klimakterisch und reifen nach der Ernte nicht nach. Nur Cantaloupe-Typ-Melonen (*Cucumis melo* var. *cantalupensis*) und Honigmelonen sind klimakterisch. Die pauschale Klassifikation "melon = klimakterisch" fuehrt bei Wassermelonen zu falschen Ernteempfehlungen ("kann im Breaker-Stadium geerntet werden" -- falsch fuer Wassermelone).
**Korrekte Formulierung:** Melonen muessen auf Species-Ebene differenziert werden. Vorschlag: `'cantaloupe'` und `'honeydew'` in `CLIMACTERIC_SPECIES`, `'watermelon'` in `NON_CLIMACTERIC_SPECIES`. Alternativ: Die Klassifikation nicht ueber generische Strings sondern ueber die Species-ID aus REQ-001 steuern.
**Gilt fuer Anbaukontext:** Gewaechshaus, Outdoor

### F-004: Trichom-Prozent-Validierung erlaubt unrealistische Werte [BEHOBEN]

**Anforderung:** `if abs(total - 100) > 5:` -- Toleranz von 5% (Zeile ~678)
**Problem:** Eine Toleranz von 5 Prozentpunkten ist biologisch und messtechnisch sinnvoll (Trichome sind nicht immer eindeutig kategorisierbar). Allerdings fehlt eine Validierung der Einzelwerte: Negative Prozentwerte oder Werte ueber 100% pro Kategorie werden nicht abgefangen. Zudem fehlt die vierte Kategorie "degradiert/braun/abgebrochen" (dead/degraded trichomes), die bei ueberreifen oder mechanisch beschaedigten Pflanzen relevant ist und als separate Kategorie von "amber" unterschieden werden sollte.
**Korrekte Formulierung:** Einzelwert-Validierung hinzufuegen (`0 <= value <= 100` fuer jede Kategorie). Optional: Eine vierte Kategorie `'degraded_percent'` fuer abgestorbene/abgebrochene Trichome einfuehren, die bei der Qualitaetsbewertung als negativer Faktor einfliesst.
**Gilt fuer Anbaukontext:** Indoor

### F-005: Brix-Messung "Mittags (hoechster Zuckergehalt)" -- biologisch ungenau [BEHOBEN]

**Anforderung:** `'best_time': 'Mittags (hoechster Zuckergehalt)'` (Zeile ~975)
**Problem:** Der Zuckergehalt in Fruechten schwankt tageszeitlich nur geringfuegig und ist primaer vom Reifegrad, nicht von der Tageszeit abhaengig. Was tatsaechlich tageszeitlich schwankt, ist der Wassergehalt der Frucht: Morgens nach der Nacht haben Fruechte den hoechsten Turgor (Wasserdruck), was den Brix-Wert leicht verduennt. Mittags bei hoeherer Transpiration ist der Wassergehalt etwas niedriger, was den Brix-Wert leicht konzentriert -- aber dies ist ein Messartefakt, kein hoeherer Zuckergehalt. Fuer reproduzierbare Ergebnisse ist eine konsistente Messzeit wichtiger als die spezifische Uhrzeit.
**Korrekte Formulierung:** `'best_time': 'Immer zur gleichen Tageszeit messen fuer Vergleichbarkeit. Morgens vor Bewaesserung liefert den repraesentativsten Wert (hoechster Turgor, weniger Varianz durch Transpiration).'`
**Gilt fuer Anbaukontext:** Indoor, Gewaechshaus, Outdoor

### F-006: Rack-Dry-Korrektur "3-5% weniger Verlust" ist biologisch fragwuerdig [BEHOBEN]

**Anforderung:** `moisture_loss_percent = max(0, moisture_loss_percent - 4)` (Zeile ~1297)
**Problem:** Die Begruendung "Wet Trim entfernt Blattmaterial mit hoeherem Wasseranteil vor der Trocknung" ist nur halb korrekt. Wet Trim entfernt Blattmaterial, was das Nassgewicht VOR der Trocknung reduziert -- nicht den prozentualen Wasserverlust des verbleibenden Materials. Der prozentuale Feuchtegehalt der Blueten aendert sich durch das Entfernen von Blaettern nicht. Was sich aendert, ist die absolute Menge des Nassgewichts (trim_weight wird separat erfasst). Die Korrektur von -4% auf den moisture_loss_percent fuehrt zu einer systematischen Ueberschaetzung des Trockengewichts.
**Korrekte Formulierung:** Die estimate_dry_weight-Funktion sollte fuer Rack-Dry/Wet-Trim nicht den moisture_loss_percent anpassen, sondern stattdessen das wet_weight_g vor der Berechnung um das geschaetzte Trim-Gewicht reduzieren. Vorschlag: `adjusted_wet = self.wet_weight_g - estimated_trim_weight; dry_weight = adjusted_wet * (1 - moisture/100)`. Der aktuelle `calculate_trim_waste()` erfasst das Trim-Gewicht bereits -- diese beiden Funktionen muessen verknuepft werden.
**Gilt fuer Anbaukontext:** Indoor

---

## Orange -- Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: Karenzzeit-Pruefung fehlt im Ernte-Workflow [BEHOBEN]

**Anbaukontext:** Indoor, Gewaechshaus, Outdoor
**Fehlende Parameter:** Karenzzeit-Validierung als Pflicht-Schritt vor Batch-Erstellung
**Begruendung:** REQ-010 definiert `requires_harvest_delay` als Edge-Collection und einen Karenzzeit-Validator. REQ-007 erwaehnt die Abhaengigkeit zu REQ-010 nur in Zeile 1737 ("Karenzzeit-Validierung vor Ernte"), aber der eigentliche Ernte-Workflow (Batch-Erstellung, AQL-Logik, Python-Code) enthaelt keinen Karenzzeit-Check. Ein Nutzer koennte einen Batch fuer eine Pflanze erstellen, die 10 Tage zuvor mit einem Pestizid behandelt wurde (Karenzzeit 21 Tage), ohne Warnung. Dies ist ein lebensmittelsicherheitsrelevanter Fehler.
**Formulierungsvorschlag:** In der Batch-Erstellungslogik (sowohl AQL als auch Python) muss ein Karenzzeit-Check eingebaut werden:
- Vor `INSERT INTO batches`: Query auf `treatment_applications` mit `safety_interval_days` aus REQ-010
- Wenn `DATE_NOW() < applied_at + safety_interval_days`: Batch-Erstellung blockieren mit Fehlermeldung
- Optional: "Force Override" mit expliziter Bestaetigung und Dokumentation (fuer Zierpflanzen / nicht-essbare Kulturen)

### U-002: Dauerkulturen (Perenniale) und wiederholte Ernte nicht modelliert [BEHOBEN]

**Anbaukontext:** Gewaechshaus, Outdoor, Indoor (Kraeuter)
**Fehlende Parameter:** Ernte-Logik fuer mehrjaehrige Pflanzen mit jaehrlich wiederkehrender Ernte
**Begruendung:** REQ-003 definiert ausdruecklich einen Perennial-Modus mit saisonalen Zyklen (Dormanz -> Austrieb -> Vegetativ -> Bluete -> Fruchtentwicklung -> Reife -> Seneszenz -> Dormanz). REQ-007 modelliert Ernte jedoch ausschliesslich als einmaliges oder gestaffeltes Ereignis innerhalb eines linearen Lebenszyklus. Mehrjaehrige Kulturen (Obstbaeume, Beerensstraeucher, Rhabarber, Spargel, Artischocke) haben folgende Besonderheiten:
- Jaehrliche Ernte-Saisons mit eigenen Batch-Serien
- Ertragsentwicklung ueber die Jahre (Jungpflanze liefert weniger als etablierte Pflanze)
- Saison-bezogene Yield-Metriken (Ertrag pro Saison, nicht pro Lebenszyklus)
- Fruchtausduernnnung (Thinning) als Pre-Harvest-Massnahme (Aepfel, Pfirsiche)
**Formulierungsvorschlag:** Ein `season_id` oder `harvest_season: int` Feld in der Batch-Collection einfuehren. Yield-Metriken muessen saisonal aggregierbar sein. Ein neues Pre-Harvest-Protokoll `thinning` (Fruchtausduernnnung) ergaenzen.

### U-003: Cut-and-Come-Again-Kulturen (CACA) nur erwaehnt, nicht modelliert [BEHOBEN]

**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Erntelogik fuer kontinuierliche Ernte bei Blattgemuese und Kraeutern
**Begruendung:** REQ-007 erwaehnt "Kontinuierliche Ernte bei Cut & Come Again Kulturen" (Zeile 56) und fuehrt `harvest_type: Literal['partial', 'final', 'continuous']` (Zeile 125), aber die gesamte Logik ist fuer einmalige oder gestaffelte Ernten ausgelegt. CACA-Kulturen (Basilikum, Schnittsalat, Pfluckslaat, Rucola, Mangold, Petersilie) haben fundamental andere Anforderungen:
- Ernte ist kein Terminal-Ereignis, sondern ein wiederkehrender Eingriff
- Die Pflanze bleibt nach der Ernte in der vegetativen Phase (kein Statuswechsel)
- Erntefrequenz (z.B. alle 5-7 Tage) ist ein Steuerparameter
- Schnitthoehe ist artspezifisch und qualitaetsrelevant (zu tief = Pflanzentod)
- Kumulative Yield-Metriken ueber die gesamte Ernteperiode
**Formulierungsvorschlag:** Einen eigenen `ContinuousHarvestIndicator` erstellen, der folgende Parameter modelliert: `cut_height_cm`, `regrowth_days`, `max_harvests_before_replant`, `cumulative_yield_g`. Der Batch-Status darf bei `harvest_type == 'continuous'` die Pflanze nicht auf 'harvested' setzen.

### U-004: Umweltbedingungen bei Ernte nicht strukturiert erfasst [BEHOBEN]

**Anbaukontext:** Indoor, Gewaechshaus, Outdoor
**Fehlende Parameter:** Strukturierte Erfassung von Umweltdaten zum Erntezeitpunkt
**Begruendung:** Das Feld `weather_conditions: Optional[str]` (Zeile 131) ist ein Freitext-Feld. Fuer eine sinnvolle Datenanalyse (z.B. "Korrelation zwischen VPD bei Ernte und Trocknungsdauer") muessen die Umweltbedingungen strukturiert erfasst werden. Insbesondere:
- Temperatur und Luftfeuchtigkeit zum Erntezeitpunkt beeinflussen die sofortige Nacherntequalitaet
- Bei Outdoor: Niederschlag der letzten 24-48h erhoet Schimmelrisiko beim Trocknen
- VPD zum Erntezeitpunkt korreliert mit dem initialen Feuchtegehalt der Ernte
**Formulierungsvorschlag:** `weather_conditions` ersetzen durch strukturiertes Objekt:
```python
harvest_environment: Optional[HarvestEnvironment] = None

class HarvestEnvironment(BaseModel):
    temperature_c: Optional[float]
    humidity_rh: Optional[float]
    vpd_kpa: Optional[float]
    precipitation_last_24h: Optional[bool]  # Outdoor
    light_status: Optional[Literal['dark_period', 'lights_on', 'natural_light']]
```

### U-005: Pilzkulturen (Fungi) als Erntekategorie fehlen [BEHOBEN]

**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Pilzspezifische Ernteindikatoren
**Begruendung:** REQ-008 (Post-Harvest) erwaehnt explizit Speisepilze und Heilpilze als eigene Trocknungskategorie. REQ-007 hat jedoch keinen Ernte-Indikator fuer Pilze. Pilze haben fundamental andere Reifekriterien als Gefaesspflanzen:
- Hutdurchmesser und Hutform (Champignon: geschlossener Hut = unreif, offener Hut = reif)
- Velum-Riss (bei Agaricus: universelles Reifesignal)
- Sporenabwurf (beginnt bei Vollreife -- unerwuenscht fuer Speisepilze)
- Flush-Nummer (1. Flush = hoechster Ertrag, 3./4. Flush = abnehmend)
- Substrat-Erschoepfung (Biological Efficiency = Frischgewicht / Substrat-Trockengewicht)
**Formulierungsvorschlag:** Einen `MushroomIndicator(HarvestIndicator)` erstellen mit Feldern fuer `cap_diameter_cm`, `veil_status: Literal['intact', 'partial', 'broken']`, `spore_drop: bool`, `flush_number: int`, `biological_efficiency_percent: float`.

### U-006: GDD-Integration in Ernteprognose fehlt [BEHOBEN]

**Anbaukontext:** Gewaechshaus, Outdoor
**Fehlende Parameter:** Growing Degree Days als Reife-Indikator
**Begruendung:** REQ-003 definiert GDD (Growing Degree Days) als zentralen Parameter fuer die Phasensteuerung. REQ-007 stuetzt die Ernteprognose jedoch ausschliesslich auf "Tage seit Bluete" (`DaysSinceFloweringIndicator`). GDD sind fuer die Erntezeitpunkt-Prognose biologisch korrekter als Kalendertage, da sie die tatsaechliche Waermeakkumulation beruecksichtigen. Besonders bei schwankenden Temperaturen (Gewaechshaus im Fruehjahr, Outdoor) sind Kalendertage ein ungenauer Proxy.
- Tomate: typisch 800-1200 GDD von Bluete bis Ernte (Basis 10C)
- Paprika: 600-900 GDD
- Cannabis: 700-1000 GDD (abhaengig von Sorte)
**Formulierungsvorschlag:** Einen `GDDIndicator(HarvestIndicator)` erstellen oder den `DaysSinceFloweringIndicator` um ein GDD-basiertes Assessment erweitern: `gdd_accumulated` und `gdd_target` als Felder, Berechnung ueber REQ-003/REQ-005 Sensordaten.

### U-007: Ernte-Ergonomie und Werkzeug-Dokumentation fehlt [BEHOBEN]

**Anbaukontext:** Indoor, Gewaechshaus
**Fehlende Parameter:** Erntewerkzeug und Hygiene-Protokoll
**Begruendung:** Fuer eine vollstaendige Ernte-Dokumentation und Qualitaetssicherung sollte das System folgende Aspekte mindestens optional erfassen:
- Erntewerkzeug (Schere, Messer, Maschinell) -- beeinflusst Schnittqualitaet und Kontaminationsrisiko
- Werkzeug-Desinfektion zwischen Pflanzen (Isopropanol, Flamme) -- kritisch bei Krankheitsbefall
- Handschuh-Verwendung (Cannabis: Harz-Kontamination; Lebensmittel: Hygiene)
- Erntegefaess/Behaelter (offenes Tablett vs. geschlossenes Glas -- Oxidation)
**Formulierungsvorschlag:** Optionale Felder im Batch-Modell: `harvest_tool: Optional[str]`, `tool_sanitized: bool = True`, `container_type: Optional[str]`.

---

## Gelb -- Zu Ungenau -- Praezisierung noetig

### P-001: Effekt-Profile sind keine Ernte-Indikatoren [BEHOBEN]

**Vage Anforderung:** `'effect_profile': 'Balanced - Peak THC, ausgewogene Effekte'` (Zeile ~705)
**Problem:** Die Effekt-Beschreibungen in TrichomeIndicator (`'Sehr sedierend, Couch-Lock'`, `'Eher zerebral, energetisch'`) sind Konsumenten-orientierte Marketingbegriffe, keine agrarbiologischen Parameter. Sie gehoeren nicht in einen Ernteindikator, sondern in die Produktbeschreibung (Post-Harvest/Lagerung). Zudem sind Effekte primaer vom Cannabinoid- und Terpen-Profil der Sorte abhaengig, nicht vom Erntezeitpunkt allein. Ein Indica-dominanter Strain mit 70% milchigen Trichomen hat andere Effekte als ein Sativa-dominanter Strain mit identischem Trichom-Profil.
**Messbare Alternative:** Effekt-Profile entfernen oder als separate, optionale Metadaten in die QualityAssessment-Collection verschieben. Im Indikator auf messbare Cannabinoid-Zustands-Beschreibungen beschraenken: `'cannabinoid_status': 'Peak THC concentration, minimal CBN degradation'`.

### P-002: Aroma-Intensitaet auf subjektiver 0-10-Skala [BEHOBEN]

**Vage Anforderung:** `'intensity': float (0-10, subjektive Skala)` (Zeile ~1082)
**Problem:** Eine subjektive 0-10-Skala ohne Kalibrierung ist nicht reproduzierbar und zwischen verschiedenen Beobachtern nicht vergleichbar. Zwei Beobachter koennten die gleiche Pflanze mit 5 bzw. 8 bewerten.
**Messbare Alternative:** Entweder eine ordinal-kategorische Skala mit verbaler Verankerung verwenden:
- 0-1: Kein wahrnehmbares Aroma (muss Bluete reiben)
- 2-3: Schwach (nur bei direktem Kontakt)
- 4-5: Moderat (wahrnehmbar bei 10 cm Abstand)
- 6-7: Stark (wahrnehmbar bei 30 cm Abstand, "Room Scent")
- 8-10: Sehr stark (ganzer Raum riecht, "Stank")

Oder idealerweise auf GC/MS-Analyse verweisen (Terpen-Konzentration in mg/g) mit einer Fallback-Ordinalskala fuer Hobby-Gaertner.

### P-003: Qualitaets-Scoring-Gewichtung ist Cannabis-zentriert als Default [BEHOBEN]

**Vage Anforderung:** Default-Gewichtung: `appearance: 0.25, aroma: 0.25, trichome: 0.20, density: 0.15, color: 0.15` (Zeile ~1361-1367)
**Problem:** Obwohl artspezifische Profile existieren (Zeile 1429-1474), ist der Fallback in `calculate_overall_score()` Cannabis-zentriert. Fuer nicht-Cannabis-Pflanzen ohne Trichome oder Bud-Density wird `self.trichome_coverage_score or 50` verwendet (Zeile 1372) -- ein neutraler Default von 50 Punkten fuer eine nicht-existierende Dimension verzerrt den Score.
**Messbare Alternative:** `calculate_overall_score()` muss den `species_type` als Parameter akzeptieren und die Gewichtung aus `SPECIES_QUALITY_PROFILES` ziehen. Dimensionen die fuer eine Art nicht relevant sind, muessen mit Gewicht 0 bewertet werden (nicht mit Default 50).

### P-004: Flushing EC-Zielwert 0.0 ist unrealistisch [BEHOBEN]

**Vage Anforderung:** `'target_ec': 0.0` und `'ec_target': 0.0` (Zeile ~169, 345)
**Problem:** Ein EC-Wert von 0.0 mS/cm entspricht reinem destilliertem Wasser und ist in der Praxis nicht erreichbar. Leitungswasser hat typisch 0.2-0.8 mS/cm, Brunnenwasser oft 0.5-1.5 mS/cm. Das Ziel beim Flushing ist nicht EC 0.0 am Eingang, sondern ein Runoff-EC nahe dem Input-EC (was signalisiert, dass keine Salze mehr ausgewaschen werden). REQ-004 definiert `ec_net = target_ec - base_water_ec`, was bei target_ec 0.0 negativ waere.
**Messbare Alternative:** Flushing-Ziel als `target_ec: 'base_water_ec'` oder `target_ec_additional: 0.0` (additiv zum Basis-EC) formulieren. Runoff-Ziel: `runoff_ec_target: base_water_ec + 0.3` (max. 0.3 mS/cm ueber Input).

### P-005: Ertrags-Effizienz-Score ohne Artdifferenzierung [BEHOBEN]

**Vage Anforderung:** Score-Schwellwerte: `>= 1.5 g/m2/Tag = Excellent`, `>= 1.0 = Good`, `>= 0.7 = Average` (Zeile ~1716-1723)
**Problem:** Diese Schwellwerte sind Cannabis-spezifisch und fuer andere Kulturen nicht anwendbar:
- Tomate (Indoor): 3-6 g/m2/Tag ist normal (Nassgewicht)
- Salat (Hydroponik): 5-15 g/m2/Tag
- Erdbeere (Gewaechshaus): 1.5-3 g/m2/Tag (Nassgewicht)
- Cannabis (Indoor): 0.5-2.0 g/m2/Tag (Trockengewicht)
Die Metriken vergleichen zudem Nassgewicht (Tomate) mit Trockengewicht (Cannabis) -- ein fundamentaler Aepfel-mit-Birnen-Vergleich.
**Messbare Alternative:** Effizienz-Score muss artspezifisch kalibriert werden und zwischen Nass- und Trockengewicht-Basis unterscheiden. Vorschlag: `SPECIES_EFFICIENCY_BENCHMARKS: dict[str, dict[str, float]]` mit `{'cannabis': {'excellent': 1.5, 'good': 1.0, 'weight_basis': 'dry'}, 'tomato': {'excellent': 5.0, 'good': 3.0, 'weight_basis': 'wet'}, ...}`.

### P-006: Trichom-Pruef-Frequenz "taeglich ab Woche 7" zu starr [BEHOBEN]

**Vage Anforderung:** `'frequency': 'Taeglich ab Woche 7 der Bluete'` (Zeile ~834)
**Problem:** Cannabis-Sorten haben stark variierende Bluetezeiten: Autoflower 5-8 Wochen, Indica 7-9 Wochen, Sativa 10-16 Wochen. "Ab Woche 7" ist fuer Autoflower-Sorten viel zu spaet (dann ist die Ernte laengst ueberfaellig) und fuer Sativa-Sorten unnoetig frueh. Die Pruef-Frequenz muss sortenbezogen sein.
**Messbare Alternative:** `'frequency': 'Taeglich ab 75% der sortenspezifischen Bluetezeit. Beispiel: 8-Wochen-Sorte -> ab Woche 6; 12-Wochen-Sorte -> ab Woche 9. Autoflower: Ab Woche 5 oder bei ersten Amber-Trichomen.'`

---

## Gruen -- Hinweise und Best Practices

### H-001: Flushing-Wissenschafts-Referenz ist vorbildlich

Die explizite Nennung der University of Guelph Studie (2020) und die Markierung von Flushing als "wissenschaftlich umstritten" (Zeile 64-70) ist fachlich vorbildlich und hebt dieses Dokument von typischen Cannabis-Grow-Dokumentationen positiv ab. Die Option `protocol_type: 'none'` fuer bewusstes Nicht-Flushing ist korrekt und wichtig.

### H-002: Ethylen-Klassifikation ist ein wertvoller Beitrag

Die `EthyleneRipeningClassifier`-Klasse (Zeile 987-1056) ist ein fachlich fundierter und praxisrelevanter Baustein, der in vielen Gartenbau-Anwendungen fehlt. Die Unterscheidung zwischen klimakterischen und nicht-klimakterischen Fruechten ist fundamental fuer korrekte Erntezeitpunkt-Empfehlungen und Nachernte-Handling. Die Lager-Hinweise ("Nicht mit nicht-klimakterischen Fruechten lagern") sind korrekt und praxisrelevant.

### H-003: Multi-Standort-Trichom-Sampling ist Best Practice

Das gewichtete Multi-Standort-Sampling (top_cola: 0.5, mid_canopy: 0.3, lower_branch: 0.2) mit automatischer Partial-Harvest-Empfehlung (Zeile 742-804) ist eine exzellente Umsetzung, die die Praxis korrekt abbildet: Top-Colas reifen 1-2 Wochen vor den unteren Branches, was gestaffelte Ernte ermoeglicht.

### H-004: Artspezifische Wassergehalte sind korrekt

Die `SPECIES_MOISTURE_CONTENT`-Tabelle (Zeile 1249-1263) ist fachlich korrekt und deckt die wichtigsten Kulturen ab. Die Werte stimmen mit USDA FoodData Central ueberein (Tomate 94%, Gurke 96%, Kartoffel 80%). Empfehlung: Quelle (USDA) als Referenz im Dokument angeben.

### H-005: Konsistenz mit REQ-004 Flushing-Dauern

Die Flushing-Dauern (Hydro 7-14d, Coco 10-21d, Soil 21-42d) sind konsistent mit REQ-004 und beruecksichtigen die Kationenaustauschkapazitaet (CEC) der Substrate korrekt: Soil mit hoher CEC braucht laenger als Hydro mit CEC = 0. Die Living-Soil-Ausnahme ist biologisch korrekt begruendet (Mikrobiom-Schutz).

### H-006: Empfehlung -- Sensorintegration fuer automatisierte Reife-Erkennung

Fuer zukuenftige Versionen waere eine Integration mit REQ-005 (Sensoren) und REQ-018 (Umgebungssteuerung) sinnvoll:
- Bodenfeuchte-Sensoren fuer automatisierte Flushing-Ueberwachung (Runoff-EC)
- Kamerasystem fuer Computer Vision (bereits als optional erwaehnt)
- NDVI-Sensoren (Normalized Difference Vegetation Index) fuer Reife-Erkennung bei Fruchtgemuese
- Gewichtssensoren unter Containern fuer automatisiertes Yield-Tracking

### H-007: Fehlende Referenz-Datenquellen fuer Brix-Zielwerte

Die Brix-Zielwerte in `get_measurement_instructions()` (Zeile 976-984) sind plausibel, aber ohne Quellenangabe. Empfohlene Referenzen:
- Refractometer.com Brix Chart (Obst/Gemuese)
- USDA National Nutrient Database
- Kader et al. (2002): "Flavor quality of fresh market tomatoes as influenced by harvest maturity"

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|--------------------|-----------|
| Trichom-Prozente (%) | Ja | klar/milchig/bernstein summiert 100% | -- |
| Brix (Grad Brix) | Ja | artspezifisch (Tomate 8-14, Paprika 7-9) | -- |
| EC-Flushing (mS/cm) | Ja | Runoff <= base_water_ec + 0.3 | Korrektur noetig |
| GDD bis Ernte | Nein | artspezifisch (Tomate 800-1200, Cannabis 700-1000) | Hoch |
| Karenzzeit (Tage) | Nein (nur Verweis) | wirkstoffspezifisch (REQ-010) | Hoch |
| VPD bei Ernte (kPa) | Nein | 0.8-1.2 kPa fuer Qualitaetsernte | Mittel |
| Temperatur bei Ernte (C) | Nein | artspezifisch | Mittel |
| Schnitthoehe CACA (cm) | Nein | artspezifisch (Basilikum 2. Blattpaar, Salat 3-5 cm) | Mittel |
| Pilz-Hutdurchmesser (cm) | Nein | artspezifisch (Champignon 3-5 cm, Shiitake 5-8 cm) | Mittel |
| Flush-Nummer (Pilze) | Nein | 1-4 je nach Art | Mittel |
| Saison-ID (Perenniale) | Nein | jaehrlich | Mittel |
| Ernte-Werkzeug | Nein | Schere/Messer/Maschine | Niedrig |
| Degraded Trichomes (%) | Nein | <5% optimal, >15% Qualitaetsverlust | Niedrig |

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL / Referenz |
|---------|--------|----------------|
| Wassergehalt Gemuese/Obst | USDA FoodData Central | fdc.nal.usda.gov |
| Brix-Referenzwerte | Refractometer.com | refractometer.com/brix-chart |
| Klimakterium-Klassifikation | Kader (2002), Postharvest Technology | ISBN 978-0-12-374112-7 |
| Cannabis-Trichom-Entwicklung | Clarke (1981), Marijuana Botany | Klassiker, weiterhin referenziert |
| Flushing-Evidenz | Stemeroff et al. (2020), Univ. of Guelph | DOI: bereits korrekt zitiert |
| Ernte-Timing GDD | Lorenz & Maynard (1988), Knott's Handbook | Standard-Referenz Gemuese-GDD |
| Pilz-Ernteparameter | Stamets (2000), Growing Gourmet Mushrooms | ISBN 978-1-58008-175-8 |
| Karenzzeiten EU | BVL Pflanzenschutzmittel-Verzeichnis | bvl.bund.de |

---

## Konsistenz mit anderen REQ-Dokumenten

| Abhaengigkeit | Status | Anmerkung |
|---------------|--------|-----------|
| REQ-001 (Stammdaten) | Konsistent | Species-Verknuepfung ueber has_harvest_indicator korrekt |
| REQ-003 (Phasen) | Teilweise | Perennial-Modus nicht in REQ-007 reflektiert (U-002) |
| REQ-004 (Duengung) | Konsistent | Flushing-Dauern abgeglichen, FlushingProtocol referenziert |
| REQ-008 (Post-Harvest) | Konsistent | Batch-Uebergabe ueber stored_in Edge korrekt |
| REQ-010 (IPM) | Luecke | Karenzzeit-Check fehlt im Workflow (U-001) |
| REQ-013 (Pflanzdurchlauf) | Konsistent | Batch-Harvest aus PlantingRun erwaehnt |

---

## Glossar

- **Brix** (Grad Brix): Mass fuer den Zuckergehalt in Fruechten, gemessen mit Refraktometer. 1 Grad Brix = 1 g Saccharose in 100 g Loesung.
- **Klimakterisch**: Fruechte die nach der Ernte weiterreifen (Ethylen-Produktion). Gegenteil: nicht-klimakterisch.
- **Trichom**: Haar-aehnliche Druesen auf der Pflanzeoberflaeche. Bei Cannabis: Harzdrruesen die Cannabinoide und Terpene produzieren.
- **Flushing**: Ausspuelen von Naehrstoffsalzen aus dem Substrat vor der Ernte durch Giessen mit reinem Wasser.
- **CEC** (Cation Exchange Capacity): Kationenaustauschkapazitaet des Substrats. Hohe CEC (Erde) = speichert mehr Salze = laengeres Flushing noetig.
- **CACA** (Cut and Come Again): Erntemethode bei der nur Teile der Pflanze geerntet werden, die nachwachsen.
- **GDD** (Growing Degree Days): Akkumulierte Waermeeinheiten, berechnet als Tagesmittel minus Basistemperatur. Biologisch genauer als Kalendertage.
- **Velum**: Haeutige Huelle bei Pilzen, die den Hut mit dem Stiel verbindet. Der Riss des Velums signalisiert Erntereife.
- **Biological Efficiency** (BE): Pilz-Ertragsmetrik: (Frischgewicht Pilze / Trockengewicht Substrat) * 100%.
- **Runoff-EC**: Elektrische Leitfaehigkeit des Abflusswassers nach dem Giessen. Differenz zum Input-EC zeigt Salzakkumulation.
