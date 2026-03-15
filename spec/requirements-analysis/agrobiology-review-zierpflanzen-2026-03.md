# Agrarbiologisches Anforderungsreview — Zierpflanzen & Balkonblumen
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-01
**Fokus:** Zierpflanzen, Balkonblumen, Voranzucht, Pflegeautomatisierung
**Analysierte Dokumente:**
- `spec/req/REQ-001_Stammdatenverwaltung.md` (v3.0)
- `spec/req/REQ-003_Phasensteuerung.md` (v2.1)
- `spec/req/REQ-013_Pflanzdurchlauf.md` (v1.2)
- `spec/req/REQ-015_Kalenderansicht.md` (v1.3)
- `spec/req/REQ-020_Onboarding-Wizard.md` (v1.2)
- `spec/req/REQ-022_Pflegeerinnerungen.md` (v2.3)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 3/5 | Mehrere botanische Fehler in den Seed-Daten, taxonomische Inkonsistenzen |
| Indoor-Vollständigkeit | 4/5 | Voranzucht gut abgedeckt, Lichtdaten fehlen in Zierpflanzen-Profilen |
| Zimmerpflanzen-Abdeckung | 4/5 | Care-Presets biologisch korrekt; Orchideen-Unterpraesenz |
| Hydroponik-Tiefe | 3/5 | Nicht relevant fuer Zierpflanzen, aber Substrat-Spezifika fuer Balkonkaesten fehlen |
| Messbarkeit der Parameter | 3/5 | Giesserintervalle konkret; PPFD/DLI fuer Voranzucht fehlt |
| Praktische Umsetzbarkeit | 4/5 | Konzept solid, aber kritische Modell-Inkonsistenz beim ORNAMENTAL-Trait |

Die Zierpflanzen-Erweiterung ist konzeptionell gut durchdacht und deckt den typischen Balkonblumen-Use-Case ab. Es bestehen jedoch mehrere fachliche Fehler in den Seed-Daten, eine kritische Modell-Inkonsistenz beim ORNAMENTAL-Trait sowie agronomische Luecken bei Voranzucht-Lichtdaten und der Behandlung von Pelargonium als Dauerpflanze. Die Befunde sind ueberwiegend im mittleren Schweregrad und gut korrigierbar.

---

## Fachlich Falsch -- Sofortiger Korrekturbedarf

### AB-001: Calibrachoa ist eine eigenstaendige Gattung, nicht Solanaceae
**Anforderung:** `| *Calibrachoa* | Zauberglöckchen, Calibrachoa | Solanaceae | ...` (`REQ-001_Stammdatenverwaltung.md`, Zeile 350)

**Problem:** *Calibrachoa* (Zauberglöckchen) wird in der Seed-Tabelle der Familie Solanaceae (Nachtschattengewächse) zugeordnet. Dies war historisch zwar diskutiert worden, weil *Calibrachoa* morphologische Ähnlichkeiten mit *Petunia* aufweist und beide früher als Petunien-Verwandte galten. Jedoch ist *Calibrachoa* nach aktuellem APG IV-Standard eine eigenständige Gattung innerhalb der Familie **Solanaceae** -- dieser Teil stimmt also. Die eigentliche Fehlerquelle ist die Verwendung von nur `*Calibrachoa*` als scientific_name: Es fehlt das Art-Epitheton. Der korrekte wissenschaftliche Name fuer Zucht-Calibrachoas ist `*Calibrachoa × hybrida*` (Hybride, kreuzungsmarkiert mit ×) oder genauer, da es verschiedene Ursprungsarten gibt, ein Kultivargruppenname. Ohne Art-Epitheton verletzt der Eintrag die Binomialnomenklatur.

**Korrekte Formulierung:**
```
scientific_name: Calibrachoa × hybrida (Hortensia-Hybriden)
oder: Calibrachoa 'Superbells' (wenn Sortenebene gemeint)
```
Hinweis: Da Calibrachoa tatsächlich zu Solanaceae gehört (molekulargenetisch bestätigt, APG IV), ist die Familienzuordnung korrekt. Nur der fehlende Artepithet und das fehlende Hybridzeichen × müssen korrigiert werden.

**Gilt für Anbaukontext:** Balkon, Outdoor, Voranzucht Indoor

---

### AB-002: `Primulaceae` in der Ordnung `Ericales` -- korrekt aber überraschend (Hinweis nötig)
**Anforderung:** `| Primulaceae | Primelgewächse | Primrose family | Ericales | ...` (`REQ-001_Stammdatenverwaltung.md`, Zeile 360)

**Problem:** Die Zuordnung von Primulaceae zu Ericales ist nach APG IV korrekt (seit APG III 2009), war aber lange Zeit als eigene Ordnung Primulales geführt. Kein inhaltlicher Fehler, jedoch sollte ein Kommentar in den Seed-Daten die unerwartete Einordnung erklären, um Verwechslungen bei manuellen Datenpflegemaßnahmen zu vermeiden. Ähnliches gilt für Balsaminaceae (Ericales statt einer eigenständigen Ordnung).

Kritischer: Das Attribut `soil_ph_preference` fehlt für beide neuen Familien in der Seed-Tabelle. Primulaceae bevorzugen leicht saure bis neutrale Böden (pH 5,5–6,5), was für die Substrat-Empfehlung im Balkonkasten relevant ist.

**Korrekte Formulierung:** Kommentar ergänzen: `# APG IV: Primulaceae in Ericales (seit APG III 2009, früher Primulales)`. Soil-pH-Defaults ergänzen.

**Gilt für Anbaukontext:** Outdoor, Balkon

---

### AB-003: `Pelargonium zonale` als `perennial` mit `cycle_type` ist biologisch korrekt, aber im Kontext irreführend
**Anforderung:** `| *Pelargonium zonale* | Geranie, Stehende Geranie | Geraniaceae | herb | fibrous | tender | perennial | 12 | ...` (`REQ-001_Stammdatenverwaltung.md`, Zeile 345)

**Problem:** *Pelargonium zonale* ist botanisch eine mehrjährige Pflanze (Perennial), in deutschen Klimazonen aber frostempfindlich (`tender`) und wird daher im Regelfall als einjährige Balkonpflanze kultiviert oder muss eingewintert werden. Das System weist korrekt `frost_sensitivity: tender` aus. Das Problem entsteht an der Schnittstelle:

1. REQ-022 ordnet Geraniaceae dem Preset `outdoor_annual_ornamental` zu (Zeile 431). Dieses Preset hat `winter_watering_multiplier: 1.0` (kein Winter) und `repotting_interval_months: 0` (kein Umtopfen). Das ist für Einwinter-Geranien falsch: Überwinterte Pelargonien brauchen in der Ruhephase (Nov–Feb) reduziertes Gießen, Schnitt im Frühjahr und jährliches Umtopfen vor dem Wiederausstellen.
2. REQ-022 ordnet Geraniaceae dem Preset `outdoor_annual_ornamental` zu, das eigentlich für echte Annuelle ohne Winterquartier konzipiert ist. Für eine überwinterte Geranie ist dieses Preset falsch.

**Korrekte Formulierung:**
- Für Standardfall (Geranie als Annuelle entsorgt): `outdoor_annual_ornamental` ist korrekt.
- Für Einwinterungs-Szenario: Ein eigener Preset oder OverwinteringProfile (REQ-022) mit `hardiness_rating: 'frost_free'` und `winter_quarter_temp_min: 5.0, winter_quarter_temp_max: 10.0` muss gesetzt werden.
- Empfehlung: Im Onboarding-Kit `balkon-blumen` explizit den Einwinterungs-Hinweis für Geranien ergänzen: "Geranien können eingewintert werden (hell, 5–10°C) oder werden jährlich neu gekauft."

**Gilt für Anbaukontext:** Outdoor (Balkon), Winterquartier

---

### AB-004: ORNAMENTAL-Trait ist auf Cultivar-Ebene definiert, wird aber auf Species-Ebene referenziert
**Anforderung:** REQ-015 (`Kalenderansicht.md`, Zeilen 1041–1244): `traits: ['ORNAMENTAL']` auf Species-Ebene; REQ-001 (`Stammdatenverwaltung.md`, Zeile 884): `'ornamental'` als valider Trait in `Cultivar.traits`.

**Problem:** Dies ist ein kritischer Modell-Widerspruch:
- In REQ-001 ist `traits` ausschliesslich ein Feld der `:Cultivar`-Node (Zeile 77), nicht der `:Species`-Node. Die Validator-Logik (`validate_traits`) ist ebenfalls auf der `Cultivar`-Klasse implementiert.
- In REQ-015 und REQ-022 wird aber `traits: ['ORNAMENTAL']` auf Species-Ebene referenziert, um Zierpflanzen zu identifizieren (`is_ornamental = "ORNAMENTAL" in species.get("traits", [])`).
- Der Trait-Wert heisst in REQ-001 `'ornamental'` (Kleinbuchstaben), in REQ-015 `'ORNAMENTAL'` (Grossbuchstaben).

Diese Inkonsistenz führt zu einem Datenbankabfrage-Fehler: Der `SowingCalendarEngine`-Code in REQ-015 wird niemals Zierpflanzen erkennen, weil er `traits` auf der falschen Entitätsebene sucht und zudem eine falsche Gross-/Kleinschreibung verwendet.

**Korrekte Formulierung:**
Option A (empfohlen): Das Feld `traits: list[str]` analog zu Cultivar auch auf `:Species` ergänzen. Damit können übergeordnete Eigenschaften auf Art-Ebene definiert werden, ohne jede Sorte einzeln taggen zu müssen. Valider Trait: `'ornamental'` (Kleinbuchstaben, konsistent mit Cultivar-Validator). Seed-Daten für alle 10 Zierpflanzen-Species ergänzen: `traits: ['ornamental']`.

Option B: Ein dediziertes boolesches Feld `is_ornamental: bool = False` auf der `:Species`-Node, wie es in der `SowingCalendarEntry`-Klasse bereits als `is_ornamental: bool = False` vorhanden ist. Dieses Feld wird dann direkt in der Datenbank gepflegt.

In beiden Fällen muss die Gross-/Kleinschreibung konsolidiert werden: entweder überall `'ornamental'` (lowercase) oder überall `'ORNAMENTAL'` (uppercase).

**Gilt für Anbaukontext:** Indoor (Voranzucht), Outdoor (Balkon), Kalenderansicht

---

### AB-005: `repotting_interval_months: 0` ist nicht validierbar -- Feld-Constraint verletzt
**Anforderung:** CARE_STYLE_PRESETS `'outdoor_annual_ornamental'`: `'repotting_interval_months': 0` (`REQ-022_Pflegeerinnerungen.md`, Zeile 581)

**Problem:** Das Pydantic-Modell `CareProfile` hat den Validator `repotting_interval_months: int = Field(ge=6, le=60)` (Zeile 632). Der Wert `0` verletzt diese Constraint (ge=6) und führt zu einem Pydantic `ValidationError` beim Erstellen des Profils aus dem `outdoor_annual_ornamental`-Preset.

Der inhaltliche Gedanke ist richtig: Annuelle Zierpflanzen werden nicht umgetopft. Aber der Modell-Constraint erlaubt diesen Wert nicht.

**Korrekte Formulierung:** Zwei Optionen:
Option A: Den Validator auf `ge=0` ändern und Wert `0` als Sentinel für "kein Umtopfen" interpretieren. Dann muss die Reminder-Generierungslogik `if profile.repotting_interval_months == 0: skip` entsprechend angepasst werden.
Option B: `repotting_interval_months` als `Optional[int] = Field(None, ge=6, le=60)` definieren, wobei `None` "kein Umtopfen" bedeutet. Konsistenter mit dem Null-Konzept. Empfohlen.

Das Feld im `CareProfileUpdate`-Modell (Zeile 703) hat bereits `Optional[int] = Field(None, ge=6, le=60)` -- dort ist eine Null-Logik also vorgesehen. Die Inkonsistenz zwischen Basis-Modell und Update-Modell sollte bereinigt werden.

**Gilt für Anbaukontext:** Outdoor (Balkon), Zierpflanzen

---

## Unvollstaendig -- Wichtige Aspekte fehlen

### AB-006: Voranzucht-Lichtdaten fuer Zierpflanzen fehlen im RequirementProfile
**Anbaukontext:** Indoor (Voranzucht), Fensterbank

**Fehlende Parameter:** PPFD (µmol/m²/s), DLI (mol/m²/d) und Lichtspektrum für die Keimungs- und Saemlings-Phasen der Balkonblumen-Voranzucht.

**Begründung:** Das Kit `balkon-blumen-voranzucht` (REQ-020) erzeugt Phasen: `germination → seedling → vegetative → flowering → senescence`. Die RequirementProfiles (REQ-003) dieser Phasen müssen Lichtwerte enthalten, um agronomisch korrekte Kulturführung zu ermöglichen:

- **Keimung** (Viola, Petunia, Lobelia): Licht nicht zwingend nötig bis Auflaufen (Dunkelkeimer vs. Lichtkeimer). Viola und Lobelia sind Lichtkeimer (Licht fördert Keimung): 10–50 µmol/m²/s PPFD, 16 Stunden Photoperiode. Petunia ist ebenfalls Lichtkeimer.
- **Sämling** (alle Balkonblumen): 100–200 µmol/m²/s PPFD, DLI 8–12 mol/m²/d. Zu geringe Lichtstärke führt zu Geilerung (Etiolierung) -- besonders kritisch für Petunia und Lobelia.
- **Vegetativ** (Pikierung bis Abhärtung): 150–300 µmol/m²/s PPFD, DLI 12–18 mol/m²/d.

Nordfenster in Deutschland im Februar liefert ca. 1–3 mol/m²/d DLI -- erheblich unter dem Minimum für gesunde Sämlingsentwicklung. Ohne Pflanzenlicht wird die Voranzucht am Nordfenster scheitern. Diese Information MUSS im Onboarding-Kit kommuniziert werden.

**Formulierungsvorschlag:** In den RequirementProfiles der Phasen `germination`, `seedling` und `vegetative` für das `balkon-blumen-voranzucht`-Kit:
```
germination:  light_ppfd_target: 30, dli_min_mol: 2.0, photoperiod_hours: 16
seedling:     light_ppfd_target: 150, dli_min_mol: 8.0, photoperiod_hours: 16
vegetative:   light_ppfd_target: 250, dli_min_mol: 14.0, photoperiod_hours: 14
```
Hinweis im Kit: "Fuer erfolgreiche Voranzucht wird ein Pflanzenlichtsystem empfohlen (DLI min. 8 mol/m²/d). Fensterbank-Aufzucht nur bei Südfenster mit direkter Sonne von Februar an."

---

### AB-007: Keimtemperatur fuer Balkonblumen-Voranzucht nicht spezifiziert
**Anbaukontext:** Indoor (Voranzucht)

**Fehlende Parameter:** Keimtemperaturen und Bodenwärme-Anforderungen für die Zierpflanzen-Voranzucht.

**Begründung:** Balkonblumen haben sehr unterschiedliche Keimtemperaturen:
- *Viola x wittrockiana* (Stiefmütterchen): Keimung optimal bei 15–18°C, nicht über 20°C (Thermoinhibition! Temperaturempfindlich). Kühle Voranzucht auf der ungeheizten Fensterbank im Februar/März fördert die Keimung.
- *Petunia x hybrida*: Keimung optimal bei 22–25°C, Mindestemperatur 18°C. Braucht Bodenwärme (Heizplatte empfohlen).
- *Lobelia erinus*: Keimung optimal bei 20–22°C.
- *Tagetes patula*: Keimung optimal bei 20–25°C, sehr schnell (3–5 Tage).
- *Impatiens walleriana*: Keimung optimal bei 22–25°C, Licht notwendig (Lichtkeimer!).

Die Thermoinhibition von Stiefmütterchen (keine Keimung > 22°C) ist eine häufige Fehlerquelle für Anfänger, die alle Pflanzen auf der warmen Heizungsplatte ankeimen. Das System MUSS artspezifische Keimtemperaturen im RequirementProfile der Keimungsphase speichern.

**Formulierungsvorschlag:** Im `:GrowthPhase`-Modell (`temperature_day_c`) für die `germination`-Phase artspezifisch befüllen:
- Viola: `temperature_day_c: 16.0, temperature_night_c: 12.0`
- Petunia: `temperature_day_c: 23.0, temperature_night_c: 20.0`
- Lobelia: `temperature_day_c: 21.0, temperature_night_c: 18.0`
- Tagetes: `temperature_day_c: 22.0, temperature_night_c: 18.0`
- Impatiens: `temperature_day_c: 24.0, temperature_night_c: 21.0`

---

### AB-008: Pikier-Phase fehlt im Phasenmodell der Voranzucht
**Anbaukontext:** Indoor (Voranzucht), Fensterbank

**Fehlende Parameter:** Explizite Pikier-Phase (`pricking_out`) fehlt im Phasen-Modell für Balkonblumen.

**Begründung:** REQ-020 beschreibt den Voranzucht-Workflow als: `Aussaat (Feb) → Pikieren (Mär) → Abhärten (Apr) → Auspflanzen (Mai)`. Das Pikieren ist ein kritischer Schritt mit spezifischen Anforderungen:
- Nach dem Pikieren brauchen Pflanzen 3–5 Tage Erholungszeit (erhöhte Luftfeuchtigkeit 70–80%, gedämpftes Licht ca. 100 µmol/m²/s, keine direkte Sonne)
- Pikiererde (Anzuchterde mit niedrigem EC, pH 5,8–6,2) unterscheidet sich von der späteren Topferde
- Das Pikieren trennt die `seedling`-Phase von der `vegetative`-Phase

REQ-003 zeigt in der Phasensequenz für `balkon-blumen-voranzucht`: `germination → seedling → vegetative → flowering → senescence`. Das Pikieren ist implizit im Übergang `seedling → vegetative` enthalten, aber die Phase-spezifischen Ressourcenprofile (Licht, Feuchtigkeit) direkt nach dem Pikieren fehlen.

**Formulierungsvorschlag:** Entweder eine explizite Phase `pricking_recovery` (ähnlich `repotting_recovery` aus REQ-020 für Zimmerpflanzen) mit Dauer 5–7 Tage einführen, oder die Pikierpflege als Stress-Phase (analog `hardening_off`) modellieren.

---

### AB-009: Abhärtungs-Phase (hardening_off) fehlt in den Zierpflanzen-Phasensequenzen
**Anbaukontext:** Indoor-to-Outdoor-Uebergang

**Fehlende Parameter:** `hardening_off`-Phase fehlt in der expliziten Phasensequenz des `balkon-blumen-voranzucht`-Kits.

**Begründung:** REQ-020 erwähnt Abhärten (Apr) im Workflow-Text, aber in der definierten Phasensequenz (`germination → seedling → vegetative → flowering → senescence`) fehlt eine explizite `hardening_off`-Phase. Das Abhärten ist bei Balkonblumen kein optionaler Schritt -- es ist physiologisch notwendig, da:
- Kutikula-Verdickung zum UV-Schutz bei Indoor-gezogenen Pflanzen fehlt
- Stomata-Regulation unter Freiluftbedingungen (Wind, direkte Sonne) erst erlernt werden muss
- Zu abruptes Auspflanzen führt zu Sonnenbrand, Welke und Trockenstress innerhalb von 24 Stunden

Typisches Abhärte-Protokoll: 7–14 Tage, beginnend mit 2 Stunden geschützter Außenluft täglich, steigend bis zu vollem Freiluftaufenthalt.

**Formulierungsvorschlag:** `hardening_off` als Phase zwischen `vegetative` und `flowering` (outdoor) einfügen. RequirementProfile: schrittweise Reduzierung von PPFD (Indoor-Level zu Außen), steigende Windexposition, Temperaturen entsprechend Außenbedingungen.

---

### AB-010: Bloom_months von Viola x wittrockiana enthalten biologisch inkonsistente Frühjahrs-UND-Herbst-Blooms ohne Erklaerung
**Anbaukontext:** Outdoor (Balkon), Kalenderansicht

**Fehlende Parameter:** Erklaerung der zweiphasigen Blüte im Datenmodell.

**Begründung:** Die Seed-Daten zeigen für *Viola x wittrockiana*: `bloom_months: [3, 4, 5, 6, 9, 10]`. Diese zweigipflige Blüte ist botanisch korrekt -- Gartenviolen haben eine Frühjahrsblüte und (nach Sommerschnitt oder Selbstaussaat) eine Herbstblüte. Jedoch fehlt im Datenmodell die Möglichkeit, zwei separate Blühfenster auszudrücken. Ein einzelnes `bloom_months`-Array kann nicht kommunizieren, dass es sich um zwei getrennte Blühperioden mit einer Blühpause im Juli/August handelt.

Die Kalenderdarstellung (REQ-015) würde einen durchgehenden pinken Balken von März bis Oktober zeigen, was Nutzern suggeriert, dass Stiefmütterchen 8 Monate durchgehend blühen -- das ist biologisch inkorrekt.

**Formulierungsvorschlag:** Option A: `bloom_months` als Liste ohne Kontinuitätsannahme interpretieren (Lücken im Array = keine Blüte). Der Kalender-Engine muss Lücken erkennen und getrennte Balken zeichnen. Option B: Das Datenmodell um `bloom_periods: Optional[list[dict]]` erweitern: `[{"start": 3, "end": 5}, {"start": 9, "end": 10}]`. Option A ist einfacher implementierbar.

---

### AB-011: Lobelie als `half_hardy` klassifiziert -- korrekte Einstufung unklar ohne Klimazonenangabe
**Anbaukontext:** Outdoor (Balkon), Frostmanagement

**Problem:** *Lobelia erinus* ist als `half_hardy` klassifiziert, was bedeutet "leichter Frost OK". Das stimmt fuer eine Kurzzeitexposition bei -1 bis -2°C und ausgewachsene Pflanzen, gilt aber nicht generell. Sämlinge und frisch pikierte Lobelien sind deutlich frostempfindlicher. Die `half_hardy`-Einstufung ist zudem ohne Referenz-Klimazone bedeutungslos.

**Formulierungsvorschlag:** Präzisieren in `hardiness_detail: "Toleriert kurzzeitig leichten Frost bis -2°C (ausgewachsene Pflanzen), Sämlinge sind frostempfindlich. In DE: Auspflanzen nach den Eisheiligen (Mitte Mai)."` Für die Aussaatkalender-Logik: Lobelien sollten wie frostempfindliche Pflanzen (`tender`) behandelt werden, was das Auspflanzen erst nach den Eisheiligen vorsieht.

---

### AB-012: `sowing_indoor_weeks_before_last_frost: 8` fuer Viola x wittrockiana ist zu kurz
**Anbaukontext:** Indoor (Voranzucht)

**Problem:** Die Seed-Daten empfehlen 8 Wochen Voranzucht für *Viola x wittrockiana* vor dem letzten Frost. Für Mitteleuropa mit letztem Frost ca. Mitte Mai bedeutet das: Aussaat ab Mitte März. Das ist biologisch zu kurz:

- Stiefmütterchen-Herbstware wird ab August/September ausgesät und bis Oktober/November verkauft (Herbstblüte). Der typische Frühjahrs-Handelstermin (fertige Ware ab März/April) erfordert eine Anzucht von Oktober bis Februar -- also 16–20 Wochen.
- Für den Hobby-Anzüchter, der Frühjahrs-Ware ab April haben möchte: 10–12 Wochen Voranzucht (Aussaat Dezember/Januar) ist realistisch.
- 8 Wochen ab Mitte März ergibt Auspflanzung Anfang Mai -- dann sind die Pflanzen noch sehr klein (5–8 cm) und zeigen kaum Blüten.

Der korrekte Wert aus kommerzieller Praxis: 12–16 Wochen vor geplantem Auspflanztermin.

**Formulierungsvorschlag:** `sowing_indoor_weeks_before_last_frost: 12` (Kompromiss zwischen Hobby und kommerziellem Standard). Zusätzlich Hinweis im Onboarding: "Für blühstarke Pflanzen ab April: Aussaat bereits im Dezember/Januar."

---

### AB-013: Tagetes patula: `sowing_indoor_weeks_before_last_frost: 6` ist korrekt aber unvollstaendig
**Anbaukontext:** Indoor (Voranzucht) / Direktsaat

**Problem:** *Tagetes patula* (Einjährige Studentenblume) wird in der Seed-Tabelle mit 6 Wochen Voranzucht geführt. Das ist korrekt, verschweigt aber dass Tagetes auch sehr erfolgreich als Direktsaat ab Mai (nach Eisheiligen) kultiviert werden kann -- mit nur leicht verspäteter Blüte (ca. 2–3 Wochen). Für Einsteiger im `balkon-blumen`-Kit (ohne Voranzucht) ist die Direktsaat-Option gar nicht abgebildet.

**Formulierungsvorschlag:** `direct_sow_months: [5, 6]` ergänzen (Mai nach Eisheiligen bis Juni). Der Aussaatkalender zeigt dann für Tagetes zwei Optionen: gelben Voranzucht-Balken ODER grünen Direktsaat-Balken je nach Nutzer-Wahl.

---

### AB-014: `outdoor_annual_ornamental` Preset: Gieassintervall 2 Tage ist ohne Substrat-Kontext nicht sinnvoll
**Anbaukontext:** Outdoor (Balkon)

**Problem:** Das Preset `outdoor_annual_ornamental` hat `watering_interval_days: 2` (alle 2 Tage giessen). Das ist als Pauschalwert problematisch, weil:
1. Balkonkasten-Grösse stark variiert (20 cm bis 120 cm Breite). Kleine Balkonkästen (20 cm) trocknen bei 30°C und Wind tatsächlich täglich aus. Grosse Kasten (80 cm) halten 3–4 Tage.
2. Substrat macht den grössten Unterschied: Torfbasiertes Balkonerde-Substrat hält weniger Wasser als kokosfaserbasierte Erde. Tongranulat im Substrat erhöht die Wasserkapazität.
3. Im Frühjahr (April/Mai, <15°C) brauchen Balkonpflanzen deutlich weniger Wasser als im Hochsommer.
4. Stiefmütterchen als froststabile Kaltkultur-Pflanze braucht im Frühjahr wesentlich seltener Giessen als Petunien im August.

Das System müsste eigentlich nach Art differenzieren: Petunia, Impatiens und Lobelia vertrocknen schnell, Viola und Tagetes sind toleranter.

**Formulierungsvorschlag:** Mindestens saisonale Differenzierung im Preset:
- `watering_interval_days: 2` (Sommer, Jun–Aug)
- `winter_watering_multiplier: 1.5` (Frühjahr/Herbst: alle 3 Tage, da Temperaturen niedriger)
- Hinweistext: "Bei Temperaturen über 25°C und direkter Sonne täglich prüfen."
Darüber hinaus: Das System könnte den Standort-Typ `balcony` als Kontext nutzen, um kleinere Container-Standardgrössen anzunehmen.

---

### AB-015: Fehlende Toxizitätsdaten fuer Zierpflanzen-Starter-Kit-Species
**Anbaukontext:** Outdoor (Balkon), Sicherheit

**Fehlende Parameter:** Toxizitätsdaten für die 10 neuen Zierpflanzen-Species fehlen in den Seed-Daten.

**Begründung:** REQ-001 hat Toxizitätsdaten für Zimmerpflanzen und Nutzpflanzen (Zeilen 425–456), aber für die 10 Zierpflanzen-Species (Viola, Petunia, Pelargonium, Tagetes, Lobelia, Osteospermum, Impatiens, Calibrachoa, Primula) fehlen vergleichbare Einträge.

Wichtige bekannte Toxizitäten aus dieser Gruppe:
- *Tagetes patula*: Enthält Thiophen-Derivate und ätherische Öle; mild toxisch für Katzen (ASPCA: Tagetse sind als toxisch für Hunde und Katzen gelistet -- kutane Irritation, milde Gastroenteritis). Das Toxizitätswarnung im Starter-Kit `balkon-blumen` ist als `"safe"` für Katzen und Hunde markiert (REQ-020 Zeile 307), was eine Fehlinformation ist.
- *Lobelia erinus*: Enthält Lobeliin (Alkaloid); giftig für Mensch und Tier, besonders Samen und Milchsaft. Mittlere Toxizität.
- *Impatiens walleriana*: Niedrig toxisch, milde Symptome bei Verzehr.
- *Pelargonium zonale*: ASPCA listet Pelargonium als toxisch für Hunde und Katzen (Geraniol, Linalool).

**Formulierungsvorschlag:** Toxizitätsdaten für alle 10 Zierpflanzen-Species nach ASPCA-Standard ergänzen. Insbesondere die `toxicity_warning` im Kit `balkon-blumen` und `balkon-blumen-voranzucht` korrigieren: von `{"cats": "safe", "dogs": "safe", "children": "safe"}` zu mindestens `{"cats": "caution", "dogs": "caution", "children": "safe"}` wegen Tagetes und Lobelia.

---

## Zu Ungenau -- Praezisierung nötig

### AB-016: `deadheading_interval_days: 5` ohne Differenzierung nach Art und Blühtätigkeit
**Anforderung:** `'deadheading_interval_days': 5` im `outdoor_annual_ornamental`-Preset (`REQ-022_Pflegeerinnerungen.md`, Zeile 586)

**Problem:** Das Deadheading-Intervall von 5 Tagen gilt pauschal für alle Zierpflanzen mit `outdoor_annual_ornamental`-Preset. Biologisch sind die Unterschiede erheblich:
- *Petunia x hybrida*: Muss tatsächlich alle 5–7 Tage deadheaded werden, um kontinuierlich zu blühen. Self-cleaning-Sorten (Surfinia, Wave-Serie) weniger.
- *Viola x wittrockiana*: Reagiert sehr gut auf Deadheading (alle 5–7 Tage); ohne Deadheading Samenbildung und Blütereduktion.
- *Tagetes patula*: Ist teilweise selbstreinigend, profitiert aber von Deadheading.
- *Lobelia erinus*: Profitiert von Rückschnitt um ca. ein Drittel alle 4–6 Wochen (kein klassisches Deadheading, sondern Verjüngungsschnitt).
- *Calibrachoa*: Self-cleaning, kein Deadheading nötig.

Für Self-cleaning-Sorten (`'self_cleaning': true` als Cultivar-Trait) sollte kein Deadheading generiert werden.

**Messbare Alternative:** `deadheading_interval_days: 5` im Preset belassen, aber Cultivar-Trait `'self_cleaning'` ergänzen der das Deadheading automatisch deaktiviert. Hinweis in der UI: "Selfcleaning-Sorten (z.B. Calibrachoa, Surfinia-Petunien) brauchen kein Verblühtes-Entfernen."

---

### AB-017: `fertilizing_active_months: [4, 5, 6, 7, 8, 9]` im `outdoor_annual_ornamental`-Preset beginnt zu spät fuer Voranzucht
**Anforderung:** `'fertilizing_active_months': [4, 5, 6, 7, 8, 9]` (`REQ-022_Pflegeerinnerungen.md`, Zeile 580)

**Problem:** Dieses Preset wird auch für Voranzucht-Pflanzen vergeben (via FAMILY_CARE_MAP für Violaceae, Geraniaceae etc.). Bei der Voranzucht (Keimung Februar, Sämling März) fällt die Düngungsphase ausserhalb von [4,5,6,7,8,9]. Sämling- und Junpflanzenanzucht (März/April) benötigen aber eine leichte Startdüngung ab der 4. Woche nach dem Keimen.

Für Freiland-Balkonpflanzen die bereits fertig gekauft werden, ist April als Start korrekt. Für Voranzucht-Pflanzen ist eine Anpassung auf `[3, 4, 5, 6, 7, 8, 9]` (März als Beginn für Sämlings-Flüssigdünger) sinnvoller.

**Messbare Alternative:** Das Preset `outdoor_annual_ornamental` auf `fertilizing_active_months: [3, 4, 5, 6, 7, 8, 9]` erweitern. Alternativ ein separates Preset `outdoor_annual_ornamental_indoor_start` für Voranzucht-Szenarien.

---

### AB-018: Viola cornuta als `perennial` wird vom `outdoor_annual_ornamental`-Preset abgedeckt -- fachlicher Widerspruch
**Anforderung:** REQ-001: `Viola cornuta` als `perennial`; REQ-022 ordnet Violaceae dem Preset `outdoor_annual_ornamental` zu.

**Problem:** *Viola cornuta* (Hornveilchen) ist eine ausdauernde Staude (Perennial), die in Mitteleuropa problemlos überwintert und mehrere Jahre wächst. Das Preset `outdoor_annual_ornamental` (mit `winter_watering_multiplier: 1.0` und `repotting_interval_months: 0`) ist für diese Art fachlich falsch:
- Hornveilchen sollte jedes Jahr nach der Hauptblüte zurückgeschnitten werden (fördert Kompaktwuchs und neue Blüte).
- Im Winter: kein besonderes Management notwendig (winterhart), aber das Substrat im Balkonkasten kann bei anhaltend strengem Frost einfrieren -- Schutz der Pflanzenwurzeln durch Vlies empfohlen.
- Umtopfen empfohlen alle 2–3 Jahre.

**Messbare Alternative:** Viola cornuta sollte entweder in die FAMILY_CARE_MAP unter einem eigenen Preset eingetragen werden, oder das `outdoor_annual_ornamental`-Preset erhält eine Ausnahme-Regel für `cycle_type: perennial`. Einfachste Lösung: `Violaceae` aus der FAMILY_CARE_MAP auf zwei Presets aufteilen: `Viola x wittrockiana` → `outdoor_annual_ornamental`; `Viola cornuta` → ein modifiziertes Perennial-Preset.

---

### AB-019: Blühkalender-Beispieldarstellung zeigt Stiefmütterchen mit Voranzucht ab Januar -- stimmt nicht mit Seed-Daten überein
**Anforderung:** REQ-015 (`Kalenderansicht.md`, Zeile 1080): `Stiefmütterchen  ·🟡🟡🟡🟡·····🟢🟢🔵🔵🩷🩷🩷🩷🩷🩷🩷·····`

**Problem:** In der Beispieldarstellung des Aussaatkalenders beginnt der Voranzucht-Balken für Stiefmütterchen im Januar (Monats-Position 1). Die Seed-Daten in REQ-001 sagen `sowing_indoor_weeks_before_last_frost: 8`. Bei einem letzten Frost am 15. Mai ergibt 8 Wochen rückwärts: Voranzuchtbeginn ca. 19. März. Der Balken müsste also im März beginnen, nicht im Januar.

Der Januar-Start wäre korrekt, wenn `sowing_indoor_weeks_before_last_frost: 16` stehen würde (was agronomisch wie in AB-012 begründet realistischer wäre). Hier besteht eine Inkonsistenz zwischen den Seed-Daten (8 Wochen) und der Beispieldarstellung (ca. 16 Wochen impliziert).

**Messbare Alternative:** Entweder die Seed-Daten auf 16 Wochen korrigieren (empfohlen, siehe AB-012) oder die Beispieldarstellung auf einen März-Start anpassen.

---

## Hinweise & Best Practices

### AB-020: Hinweis zu Gattungsname-only bei Calibrachoa -- Nomenklatur-Konvention
Gattungsnamen allein (Monomialnomenklatur wie nur `*Calibrachoa*`) verletzen die Binomialnomenklatur-Konvention. Das System sollte bei der Eingabe wissenschaftlicher Namen einen Validator einsetzen, der auf mindestens ein Leerzeichen (Genus Epithet) prüft. Der aktuelle Validator in REQ-001 prüft das Format mit einem Regex-Pattern, der sicherstellt, dass ein Leerzeichen im Namen vorkommt.

### AB-021: Empfehlung: Self-cleaning-Trait fuer Cultivare
Modernere Petunien- und Calibrachoa-Sorten (Surfinia, Wave, Million Bells) sind self-cleaning und benoetigen kein Deadheading. Das Cultivar-Trait-Set in REQ-001 sollte `'self_cleaning'` ergänzen, um die Deadheading-Logik in REQ-022 artgerecht zu steuern.

### AB-022: Substrat-Empfehlung fuer Balkonkästen fehlt
Für das `balkon-blumen`-Kit fehlt eine Substrat-Empfehlung. Biologisch optimal für Balkonkästen:
- Hochwertige Balkonblumenerde mit Langzeitdünger (3–6 Monate)
- Anteil 20–30% Perlite für Drainage (besonders Petunien sind staunässeempfindlich)
- pH 5,8–6,5 optimal für alle Balkonblumen
- Alternativ: Kokosfasern als Torfersatz (nachhaltiger)
Diese Informationen sollten im Onboarding-Text des Kits erscheinen.

### AB-023: Erklaerung warum annuelle Zierpflanzen keine `vernalization_required` benoetigen
REQ-001 hat `vernalization_required: bool` im LifecycleConfig. Fuer einjährige Zierpflanzen ist dies `false`. Fuer biennale Pflanzen (z.B. Stiefmütterchen, die als Biennial kultiviert werden koennen) und fuer Viola cornuta als Perennial im zweiten Jahr: `vernalization_required: false` (keine Vernalisierung nötig). Das System kann dieses Feld einfach `false` lassen, sollte aber für Züchter den Hinweis enthalten, dass einige Viola-Arten bevorzugt kühle Temperaturen für stärkere Blüte zeigen (Vernalisation-ähnlicher Effekt ohne physiologische Nwendigkeit).

---

## Parameter-Übersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Priorität |
|-----------|-----------|--------------------|-----------|
| PPFD (µmol/m²/s) Voranzucht-Phasen | Fehlend | Keimung: 30–50, Sämling: 100–200, Vegi: 200–300 | Hoch |
| DLI (mol/m²/d) Voranzucht | Fehlend | Keimung: 2–4, Sämling: 8–12, Vegi: 12–18 | Hoch |
| Keimtemperatur (°C) artspezifisch | Fehlend | Viola: 15–18, Petunia: 22–25, Lobelia: 20–22, Tagetes: 20–25 | Hoch |
| bloom_months Kontinuität-Handling | Konzept fehlt | Viola: zwei Perioden [3-5] und [9-10] separat darstellen | Mittel |
| Toxizitätsdaten Zierpflanzen | Fehlend | ASPCA: Tagetes/Lobelia toxisch fuer Tiere | Mittel |
| Substrat-pH Balkonkasten | Fehlend | 5,8–6,5 fuer alle Balkonblumen | Niedrig |
| Self-cleaning Cultivar-Trait | Fehlend | Boolean fuer Deadheading-Logik | Niedrig |

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Zierpflanzen-Toxizität | ASPCA Animal Poison Control | aspca.org/pet-care/animal-poison-control |
| Balkonpflanzen Aussaatzeiten | AMW (Arbeitsgemeinschaft Mitteleuropäischer Wildblumen) | — |
| Keimtemperaturen Balkonblumen | ISF / Saatguthersteller-Datenblätter | z.B. Syngenta Flowers, Benary |
| Taxonomie | Plants of the World Online (POWO) | powo.science.kew.org |
| Zierpflanzen-Kulturdaten | RHS (Royal Horticultural Society) | rhs.org.uk |
| Viola-Taxonomie | Euro+Med Plantbase | emplantbase.org |
| PPFD Voranzucht | Apogee Instruments Application Notes | apogeeinstruments.com |

---

## Glossar

- **Deadheading:** Entfernen verblühter Blütenköpfe zur Förderung neuer Blütenbildung. Verhindert Samenansatz, der die Blüteenergie der Pflanze bindet.
- **DLI** (Daily Light Integral): Tageslicht-Gesamtmenge in mol/m²/d -- PPFD × Photoperiode (h) × 3600 / 1.000.000. Massgebliche Grösse für Pflanzenwachstum unter Kunstlicht.
- **Etiolierung:** Geilerung -- überstrecktes Wachstum bei unzureichender Lichtversorgung. Typisches Symptom bei Voranzucht an zu dunklen Standorten.
- **Hardening off / Abhärten:** Schrittweise Gewöhnung von Indoor-Sämlingen an Freiluftbedingungen (UV, Wind, Temperaturschwankungen) vor dem endgültigen Auspflanzen.
- **Lichtkeimer:** Samen, die Licht zur Keimung benötigen (dürfen nicht tief in die Erde eingearbeitet werden). Viola, Petunia, Lobelia, Impatiens sind Lichtkeimer.
- **PPFD** (Photosynthetic Photon Flux Density): Photosynthetisch nutzbare Lichtintensität in µmol/m²/s -- korrekte Einheit für Pflanzenwachstum (nicht Lux!).
- **Self-cleaning:** Eigenschaft moderner Züchtungen, bei denen verblühte Blüten automatisch abfallen ohne Deadheading. Charakteristisch für Surfinia-Petunien, Calibrachoa.
- **Thermoinhibition:** Unterdrückung der Keimung durch zu hohe Temperaturen. Tritt bei Viola ab ca. 22°C auf.
- **Vernalisierung:** Kältestunden-Akkumulation zur Blüteninduktion. Bei einjährigen Zierpflanzen nicht erforderlich.
- **VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa -- beschreibt den "Durst" der Luft. Relevant für Voranzucht-Kammer und Gewächshaus, weniger für offene Balkon-Kultur.
