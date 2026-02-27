# Agrarbiologisches Anforderungsreview

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Fokus:** Indoor-Anbau, Zimmerpflanzen, Hydroponik, geschuetzter Anbau (Outdoor ergaenzend)
**Analysierte Dokumente:** REQ-001 bis REQ-022 (22 Spezifikationen)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Solide pflanzenphysiologische Grundlage; wenige fachliche Fehler, meist Praezisierungsbedarf |
| Indoor-Vollstaendigkeit | 5/5 | Hervorragende Abdeckung von Growbox, Hydroponik, Klimasteuerung |
| Zimmerpflanzen-Abdeckung | 4/5 | Seit REQ-020/021/022 deutlich verbessert; einige Luecken bei Taxonomie-Tiefe |
| Hydroponik-Tiefe | 5/5 | Exzellent — EC/pH/DO/ORP, Tankkaskaden, Rezirkulation, Substrattypen differenziert |
| Messbarkeit der Parameter | 5/5 | Durchgehend messbare Werte (PPFD, DLI, VPD, EC, pH) statt vager Angaben |
| Praktische Umsetzbarkeit | 4/5 | Sehr ambitioniert; einige Bereiche sind datenseitig schwer zu befuellen |

Die Spezifikation ist fachlich auf einem bemerkenswert hohen Niveau. Der Schwerpunkt liegt klar auf Indoor-Nutzpflanzenanbau (Cannabis, Gemuese) und Hydroponik, wo die Detailtiefe professionellen Anforderungen genuegt. Die juengsten Erweiterungen (REQ-020 bis REQ-022) schliessen die Zimmerpflanzen-Luecke wirkungsvoll. VPD wird als gekoppelter Regelkreis korrekt modelliert (REQ-018), nicht als isolierter Parameter — das ist eine haeufige Schwachstelle anderer Systeme, die hier vorbildlich geloest ist. Die kritische Mischreihenfolge fuer Duenger (REQ-004) ist chemisch korrekt und praxisrelevant. Verbesserungspotenzial besteht bei der Zimmerpflanzen-Taxonomie, fehlenden Toxizitaetsdaten auf Species-Ebene und der Halbbkugel-Abhaengigkeit saisonaler Parameter.

---

## Fachlich Falsch — Sofortiger Korrekturbedarf

### F-001: Basilikum ist keine Kurztagspflanze

**Anforderung:** "GIVEN: Basilikum (Ocimum basilicum) als einjaehrige Kurztagspflanze" (`REQ-001_Stammdatenverwaltung.md`, Zeile ~726, Szenario 1)
**Problem:** Basilikum (*Ocimum basilicum*) ist eine quantitative Langtagspflanze, keine Kurztagspflanze. Langtagsbedingungen (>14h Licht) foerdern die Bluetenbildung und damit das Schossen. Unter Kurztagsbedingungen bleibt Basilikum laenger vegetativ — das Gegenteil einer Kurztagspflanze. In der Praxis will man bei Basilikum das Schossen verhindern, nicht ausloesen.
**Korrekte Formulierung:** "GIVEN: Basilikum (Ocimum basilicum) als einjaehrige Langtagspflanze (bzw. tagneutral mit Langtagstendenz)"
**Gilt fuer Anbaukontext:** Indoor, Outdoor

### F-002: Cannabis-Photoperiodismus-Vereinfachung

**Anforderung:** "Cannabis (Cannabis sativa) als Kurztagspflanze, kritische Tageslaenge: 14h" (`REQ-001`, Zeile ~755, Szenario 4)
**Problem:** Die kritische Tageslaenge von 14h ist fuer viele photoperiodische Cannabis-Sorten zu hoch angesetzt. Die meisten Indica-dominanten Sorten beginnen die Bluetenbildung erst bei 12-13h Licht (bzw. 11-12h ununterbrochener Dunkelheit). Die Angabe von 14h wuerde bedeuten, dass Pflanzen bereits im Juli in Bluete gehen, was in der Praxis nicht beobachtet wird. Zudem gibt es tagneutrale Autoflower-Sorten (*Cannabis sativa* var. *ruderalis*-Hybriden), die hier nicht erwaehnt werden.
**Korrekte Formulierung:** "Cannabis sativa (photoperiodische Sorten) als Kurztagspflanze, kritische Tageslaenge: 12-13h. Autoflowering-Sorten (ruderalis-Hybriden): tagneutral, bluetenunabhaengig von Photoperiode."
**Gilt fuer Anbaukontext:** Indoor (Growbox), Gewaechshaus

### F-003: Vernalisation bei Zweijahrigen zu pauschal

**Anforderung:** "Zweijaehrige Pflanzen benoetigen typischerweise Vernalisation" (`REQ-001`, Zeile ~537, Validator)
**Problem:** Die Validierungsregel `biennial + !vernalization_required = Fehler` ist biologisch zu streng. Nicht alle Zweijahrigen benoetigen Vernalisation. Beispiele: *Beta vulgaris* (Mangold/Rote Bete) kann unter Langtagsbedingungen auch ohne Kaelteperiode schossen. Manche Zweijahrige (z.B. Petersilie) benoetigen nur eine moderate Kaelteperiode, aber nicht alle Cultivare gleich stark. Die Validierung sollte eine Warnung statt eines Fehlers erzeugen.
**Korrekte Formulierung:** "Zweijahrige Pflanzen benoetigen HAEUFIG Vernalisation. Wenn `vernalization_required=false` bei `cycle_type='biennial'`, Warnung ausgeben ('Zweijahrige ohne Vernalisation — bitte pruefen'), aber nicht blockieren."
**Gilt fuer Anbaukontext:** Outdoor, Gewaechshaus

### F-004: VPD-Wertebereiche fuer Cannabis-Bluetephase

**Anforderung:** CLAUDE.md gibt an: "VPD 0.4-0.8 kPa flowering"
**Problem:** Ein VPD von 0.4 kPa waehrend der Bluetephase ist fuer Cannabis zu niedrig und wuerde das Botrytis-Risiko erheblich erhoehen — dichtes Bluetenmaterial bei hoher Luftfeuchtigkeit ist die Hauptursache fuer Schimmelbefall. Der empfohlene Bereich fuer Cannabis-Bluete liegt bei 0.8-1.2 kPa (spaete Bluete eher 1.0-1.4 kPa). Der Wert 0.4-0.8 kPa waere eher fuer Stecklinge/Saemling-Phase korrekt.
**Korrekte Formulierung:** "VPD Keimung/Stecklinge: 0.4-0.8 kPa; Vegetativ: 0.8-1.2 kPa; Fruehe Bluete: 0.8-1.2 kPa; Spaete Bluete: 1.0-1.4 kPa"
**Gilt fuer Anbaukontext:** Indoor (Growbox)

### F-005: Dracaena trifasciata Toxizitaet fuer Kinder

**Anforderung:** Starter-Kit `zimmerpflanzen` enthaelt `toxicity_warning: {"children": "caution"}` (`REQ-020`, Zeile ~263)
**Problem:** *Dracaena trifasciata* (Bogenhanf) enthaelt Saponine, die bei Verschlucken zu Uebelkeit und Erbrechen fuehren koennen. *Monstera deliciosa* und *Epipremnum aureum* enthalten Calciumoxalat-Raphide, die Schleimhautschwellungen verursachen. Fuer Kleinkinder (orale Explorationsphase) waere `"warning"` die angemessenere Einstufung statt `"caution"`, da Vergiftungszentralen regelmaessig Anfragen zu diesen Pflanzen erhalten.
**Korrekte Formulierung:** `{"cats": "warning", "dogs": "warning", "children": "warning"}`
**Gilt fuer Anbaukontext:** Zimmerpflanzen

---

## Unvollstaendig — Wichtige Aspekte fehlen

### U-001: Toxizitaetsdaten fehlen auf Species-Ebene

**Anbaukontext:** Zimmerpflanzen
**Fehlende Parameter:**
- `toxicity_pets: dict` (z.B. `{"cats": "toxic", "dogs": "mild", "rodents": "unknown"}`)
- `toxicity_humans: dict` (z.B. `{"adults": "mild", "children": "toxic"}`)
- `toxic_compounds: list[str]` (z.B. `["calcium_oxalate_raphides", "saponins"]`)
- `toxic_parts: list[str]` (z.B. `["leaves", "stems", "roots"]`)

**Begruendung:** Toxizitaet ist eine der kritischsten Informationen fuer Zimmerpflanzenhalter mit Haustieren oder Kleinkindern. Aktuell existieren Toxizitaetswarnungen nur auf Starter-Kit-Ebene (REQ-020), nicht auf Species-Ebene (REQ-001). Das bedeutet, dass eine einzeln angelegte *Dieffenbachia* keinerlei Toxizitaetswarnung erhaelt — obwohl diese hochgiftig ist. Die ASPCA Poison Control Database (aspca.org) listet ueber 1.000 Pflanzenarten mit Toxizitaetsdaten fuer Hunde, Katzen und Pferde.

**Formulierungsvorschlag:** Species-Modell in REQ-001 um `toxicity`-Embedded-Objekt erweitern:
```python
class ToxicityInfo(BaseModel):
    is_toxic_cats: bool = False
    is_toxic_dogs: bool = False
    is_toxic_children: bool = False
    toxic_compounds: list[str] = Field(default_factory=list)
    toxic_parts: list[str] = Field(default_factory=list)
    severity: Literal['none', 'mild', 'moderate', 'severe'] = 'none'
    source: str = ''  # z.B. "ASPCA", "Giftnotruf"
```

### U-002: Hemisphaerenabhaengigkeit saisonaler Parameter

**Anbaukontext:** Indoor, Zimmerpflanzen
**Fehlende Parameter:** Referenz-Hemishaere und automatische Monatsumrechnung

**Begruendung:** Saemtliche saisonalen Parameter in REQ-022 (Wintermonate November-Februar, Duengesaison Maerz-Oktober) und REQ-020 (Standort-Check Oktober/Maerz) sind auf die noerdliche Halbkugel fixiert. Nutzer auf der suedlichen Halbkugel (Australien, Suedamerika, Suedafrika) erhalten falsche Erinnerungen. Die CareProfile-Presets in REQ-022 verwenden hart kodierte Monatslisten (`fertilizing_active_months: [3, 4, 5, 6, 7, 8, 9, 10]`).

**Formulierungsvorschlag:** Site-Modell in REQ-002 um `hemisphere: Literal['northern', 'southern']` erweitern (ableitbar aus GPS-Breitengrad). CareReminderEngine muss bei `hemisphere='southern'` alle Monatslisten um 6 Monate verschieben. Alternative: Nutzer konfiguriert `winter_months` explizit.

### U-003: DLI-Berechnung fuer Zimmerpflanzen fehlt

**Anbaukontext:** Zimmerpflanzen
**Fehlende Parameter:**
- DLI-Zielwerte fuer dekorative Zimmerpflanzen
- Fenster-Transmissionsgrad (typisch 50-70% je nach Verglasung)
- Himmelsrichtungs-basierte Lichtschaetzung

**Begruendung:** REQ-003 definiert DLI-Zielwerte nur fuer Nutzpflanzen (Salat 12-17, Kraeuter 15-20, Tomaten 20-30, Cannabis 35-45). Fuer Zimmerpflanzen fehlen DLI-Angaben komplett. Typische DLI-Bereiche:
- Schattentolerante Pflanzen (*Aspidistra*, *Sansevieria*): 2-4 mol/m2/d
- Halbschatten (*Philodendron*, *Pothos*): 4-8 mol/m2/d
- Helles indirektes Licht (*Ficus*, *Monstera*): 6-12 mol/m2/d
- Volle Sonne (*Kakteen*, *Sukkulenten*): 12-20 mol/m2/d

Ein Nordfenster in Deutschland liefert im Winter nur ca. 1-2 mol/m2/d — unter dem Minimum fuer fast alle Zimmerpflanzen. Diese Information ist essentiell fuer Standortempfehlungen.

**Formulierungsvorschlag:** RequirementProfile in REQ-003 um `dli_min_mol` und `dli_optimal_mol` erweitern. REQ-002 Location um `window_orientation` und `glazing_transmission_factor` ergaenzen. Berechnung: `estimated_dli = outdoor_dli * transmission_factor * orientation_factor`.

### U-004: Zimmerpflanzen-Substrattypen unzureichend

**Anbaukontext:** Zimmerpflanzen
**Fehlende Substrattypen in REQ-019:**
- `orchid_bark` — Pinienrinde fuer Epiphyten (Phalaenopsis, Dendrobium); hohe Luftdurchlaessigkeit, pH 5.5-6.5
- `sphagnum` — Torfmoos fuer Karnivoren und manche Orchideen; pH 4.0-5.0
- `pon` / `seramis` — Mineralische Zimmerpflanzensubstrate (Lechuza Pon, Seramis); strukturstabil, semi-hydroponisch
- `akadama` — Japanisches Tongranulat fuer Bonsai; pH 6.5-7.0
- `pumice` — Bimsstein, haeufig in Sukkulenten-Mischungen

**Begruendung:** REQ-019 vermerkt korrekt, dass Zimmerpflanzen-Substrate "derzeit nicht im Primaerfokus" stehen und ueber den Typ `soil` abgebildet werden koennen. Diese Einschraenkung wird mit der Zimmerpflanzen-Erweiterung (REQ-020-022) zunehmend problematisch: Ein Nutzer, der eine Orchidee im Starter-Kit `zimmerpflanzen` erhaelt, kann kein adaequates Substrat zuweisen. Orchideensubstrat (Rinde + Sphagnum + Perlite) verhaelt sich fundamental anders als Erde — Giesshaeufigkeit, pH-Bereich und EC-Toleranz unterscheiden sich massiv.

**Formulierungsvorschlag:** SubstrateType-Enum um mindestens `orchid_bark`, `pon_mineral` und `sphagnum` erweitern. IRRIGATION_STRATEGY_MAP entsprechend ergaenzen: `orchid_bark: 'infrequent'` (Tauchbad-Methode, komplett abtrocknen lassen), `pon_mineral: 'moderate'`, `sphagnum: 'frequent'`.

### U-005: Fehlende Lichtspektrum-Empfehlungen fuer Zimmerpflanzen

**Anbaukontext:** Indoor, Zimmerpflanzen
**Fehlende Parameter:**
- Empfehlungen fuer Zusatzbeleuchtung-Spektrum
- R:FR-Verhaeltnis (Rot:Fernrot) fuer Streckungswachstum-Steuerung

**Begruendung:** REQ-003 definiert `light_spectrum: dict` mit Blau/Gruen/Rot/Far-Red-Anteilen, aber nur fuer Nutzpflanzen. Zimmerpflanzen unter Kunstlicht (insbesondere in dunklen Wintermonaten) benoetigen spezifische Spektralempfehlungen:
- Tropische Grünpflanzen: Hoher Blau-Anteil (400-500 nm) fuer kompakten Wuchs
- Sukkulenten: Hoher Rot-Anteil + UV fuer Stressfaerbung (Anthocyane)
- Blühende Zimmerpflanzen: R:FR-Verhaeltnis > 1.5 fuer Kompaktheit

Fuer Zimmerpflanzenbesitzer, die LED-Pflanzenlampen kaufen moechten, sind diese Informationen kaufentscheidend.

### U-006: Luftreinigungseigenschaften fehlen

**Anbaukontext:** Zimmerpflanzen
**Fehlende Parameter auf Species-Ebene:**
- `air_purification: bool`
- `removes_compounds: list[str]` (z.B. `["formaldehyde", "benzene", "toluene"]`)
- `air_purification_caveat: str`

**Begruendung:** Luftreinigung ist einer der haeufigsten Kaufgruende fuer Zimmerpflanzen. Die NASA Clean Air Study (1989) hat zwar spezifische Arten identifiziert (z.B. *Spathiphyllum*, *Dracaena*, *Chlorophytum*), aber die Effekte sind bei realistischen Pflanzendichten in Wohnraeumen vernachlaessigbar (Cummings & Waring, 2020). Das System sollte diese Eigenschaft erfassen, aber mit einem klaren Caveat versehen, um falsche Erwartungen zu vermeiden.

### U-007: Allergenpotenzial fehlt

**Anbaukontext:** Zimmerpflanzen
**Fehlende Parameter:**
- `latex_sap: bool` (Milchsaft — z.B. *Ficus*, *Euphorbia*: Kontaktdermatitis)
- `contact_allergen: bool` (Calciumoxalat-Raphide — *Dieffenbachia*, *Monstera*)
- `pollen_allergen: bool` (relevant fuer Blühpflanzen im Innenraum)

**Begruendung:** Latexallergie betrifft ca. 1-3% der Bevoelkerung. *Ficus benjamina* setzt nachweislich Latexproteine in die Raumluft frei, die Kreuzreaktionen bei Latexallergikern ausloesen koennen. *Ficus lyrata* (im Starter-Kit enthalten) gehoert zur selben Gattung. Ein Allergiehinweis waere medizinisch sinnvoll.

### U-008: Vegetative Vermehrung von Zimmerpflanzen

**Anbaukontext:** Zimmerpflanzen
**Fehlende Informationen:**
- Typische Vermehrungsmethoden pro Zimmerpflanzen-Art auf Species-Ebene
- Vereinfachte Vermehrungsanleitungen fuer Einsteiger

**Begruendung:** REQ-017 (Vermehrungsmanagement) ist exzellent fuer den professionellen Kontext, aber fuer Zimmerpflanzenhalter ueberdimensioniert. Viele Zimmerpflanzen werden durch einfache Methoden vermehrt (Blattsteckling, Absenker, Auslaeufer), die keine PropagationBatch-Verwaltung erfordern. Auf Species-Ebene sollte zumindest `typical_propagation_method: list[str]` und `propagation_difficulty: Literal['easy', 'moderate', 'difficult']` erfasst werden, um im Einsteiger-Modus (REQ-021) passende Tipps anzeigen zu koennen.

---

## Zu Ungenau — Praezisierung noetig

### P-001: Allelopathie-Score ohne Referenzrahmen

**Vage Anforderung:** "allelopathy_score: float (-1.0 = stark hemmend, 0 = neutral, 1.0 = foerdernd)" (`REQ-001`)
**Problem:** Ein Allelopathie-Score auf Species-Ebene ist wissenschaftlich problematisch, da allelopathische Wirkungen stark partner- und konzentrationsabhaengig sind. *Juglans nigra* (Schwarznuss) hemmt *Solanum lycopersicum* (Tomate) stark, hat aber kaum Wirkung auf *Phaseolus vulgaris* (Bohne). Ein skalarer Wert kann diese Paarungsabhaengigkeit nicht abbilden.
**Messbare Alternative:** Allelopathie als Graph-Eigenschaft modellieren (analog zu `compatible_with`/`incompatible_with`), nicht als skalaren Score auf Species-Ebene. Der bestehende Score koennte als "generelle allelopathische Tendenz" beibehalten werden, aber mit dem Hinweis, dass die paarspezifischen Edges die autoritativen Daten sind.

### P-002: Bewurzelungshormon-Konzentrationen unspezifisch

**Vage Anforderung:** "hormone_concentration_ppm: Optional[float]" (`REQ-017`)
**Problem:** Die Konzentration allein genuegt nicht — die Applikationsmethode (Quick-Dip, Powder, Long-Soak) bestimmt massgeblich den Effekt. 1000 ppm IBA als Quick-Dip (5 Sekunden) ist Standard fuer weiche Stecklinge, waehrend 3000-5000 ppm fuer verholzte Stecklinge noetig sein kann. Ohne Applikationsmethode ist die ppm-Angabe nicht reproduzierbar.
**Messbare Alternative:** PropagationEvent um `hormone_application_method: Literal['quick_dip', 'long_soak', 'powder', 'gel']` erweitern und Konzentrationsempfehlungen an die Methode koppeln.

### P-003: Flushing-Dauer in REQ-007 inkonsistent

**Vage Anforderung:** Hydro: "7-14 Tage nur pH-Wasser" vs. AQL: `substrate_type == 'hydro_solution' ? 10` (`REQ-007`, Zeile ~66 vs. ~326)
**Problem:** Der Fliesstext nennt "7-14 Tage" fuer Hydro-Flushing, der AQL-Code setzt fest 10 Tage. Fuer Coco gibt der Fliesstext "10-14 Tage", der Code setzt 14 Tage. Fuer Soil gibt der Fliesstext "21-28 Tage", der Code setzt 28 Tage. Die Code-Werte nehmen systematisch die Obergrenze oder darueber.
**Messbare Alternative:** Einheitlich die Referenzwerte aus REQ-004 FlushingProtocol als Single Source of Truth verwenden und in REQ-007 per Verweis referenzieren, nicht duplizieren. Die substrattyp-spezifischen Flush-Dauern sollten an genau einer Stelle definiert sein.

### P-004: Schimmel-Schwelle bei Post-Harvest zu pauschal

**Vage Anforderung:** "RH >65% for 6h" als Schimmel-Alarm (`REQ-008`, AQL Zeile ~359)
**Problem:** Die Wasseraktivitaet (a_w) waere der praezisere Indikator. REQ-008 erwaehnt a_w korrekt in den StorageCondition-Properties, verwendet im Schimmel-Alarm-AQL aber nur RH. Schimmelpilze (*Aspergillus*, *Penicillium*) wachsen ab a_w > 0.65, unabhaengig von der Raumluftfeuchte. Ein Jar bei 62% RH kann intern trotzdem a_w > 0.65 aufweisen, wenn feuchte Stellen vorhanden sind.
**Messbare Alternative:** Wenn a_w-Sensor vorhanden: Alarm auf `a_w > 0.65` (CRITICAL) und `a_w > 0.60` (WARNING) umstellen. RH-basierter Alarm als Fallback beibehalten, wenn kein a_w-Sensor.

### P-005: Wurzeltypen-Enum zu eingeschraenkt

**Vage Anforderung:** "root_type: Literal['fibrous', 'taproot', 'tuberous', 'bulbous']" (`REQ-001`)
**Problem:** Wichtige Wurzeltypen fuer Indoor-relevante Pflanzen fehlen:
- `rhizomatous` — Rhizom-bildend (Calathea, Ingwer, Iris, viele Farne)
- `adventitious` / `aerial` — Luftwurzeln (Monstera, Philodendron, Orchideen)
- `stoloniferous` — Auslaeufer-bildend (Erdbeere, Chlorophytum)
**Messbare Alternative:** Enum um mindestens `rhizomatous` und `aerial` erweitern. Optional: `root_adaptations: list[str]` fuer Mehrfachzuweisungen (z.B. Monstera hat Faserwurzeln UND Luftwurzeln).

### P-006: Fruchtfolge-Konzept nur fuer Outdoor relevant

**Vage Anforderung:** Umfangreiche Fruchtfolge-Engine mit 3-Jahres-Planung (`REQ-001`, `REQ-002`)
**Problem:** Die Fruchtfolge-Logik ist exzellent fuer Outdoor/Freiland-Anbau, aber fuer Indoor-Hydroponik und Zimmerpflanzen nicht anwendbar. In Hydroponik-Systemen gibt es keinen "Boden", der eine Fruchtfolge erfordert — das Substrat wird zwischen den Zyklen gewechselt oder sterilisiert (korrekt in REQ-019 beschrieben). Fuer Zimmerpflanzen steht die Pflanze dauerhaft im selben Topf. Die Fruchtfolge-Warnungen sollten kontextabhaengig nur bei Outdoor-/Soil-Locations angezeigt werden.
**Messbare Alternative:** CropRotationValidator um `skip_for_substrate_types = ['none', 'clay_pebbles', 'rockwool_slab', 'perlite']` erweitern oder Fruchtfolge-Warnungen nur bei `site.type == 'outdoor'` oder `substrate.type in ['soil', 'living_soil']` aktivieren.

---

## Hinweise & Best Practices

### H-001: Vorbildliche VPD-Modellierung

REQ-018 modelliert VPD korrekt als gekoppelten Regelkreis aus Temperatur und Luftfeuchtigkeit, nicht als isolierten Parameter. Die Ableitung von Schwellwerten fuer Befeuchter/Entfeuchter/Abluft aus dem Soll-VPD und die Beruecksichtigung der Blatttemperatur (Leaf-VPD vs. Air-VPD) in REQ-005 entsprechen dem aktuellen Stand der Pflanzenphysiologie. Empfehlung: Die Leaf-VPD-Berechnung als Differenz von 1-3 Grad C zur Lufttemperatur ist ein guter Naeherungswert, koennte aber durch das tatsaechliche PPFD-Level moduliert werden (hoehere Lichtintensitaet = kuehler durch Transpiration, bis Spaltschluss bei Trockenstress).

### H-002: CO2-PPFD-Kopplung ist fachlich korrekt

Die Kopplung von CO2-Anreicherung an PPFD-Schwellwerte in REQ-018 (kein CO2 unter 200 umol/m2/s, gestaffelte Anreicherung darueber) entspricht dem Liebig'schen Minimumgesetz. Ergaenzende Empfehlung: Bei CO2-Anreicherung ueber 800 ppm steigt auch der Wasserbedarf (erhoehte Stomata-Oeffnung), was in der Bewaesserungslogik beruecksichtigt werden sollte.

### H-003: DIF/DROP-Technik korrekt beschrieben

Die DIF-Steuerung (Differenz Tag-/Nachttemperatur) und DROP-Technik (kurzzeitige Temperaturabsenkung vor Lichtbeginn) in REQ-018 sind fachlich korrekt beschrieben. Die Gibberellin-basierte Erklaerung fuer das Streckungswachstum ist wissenschaftlich fundiert. Diese Technik wird in der kommerziellen Gewaechshaus-Produktion (Topfpflanzen, Zierpflanzen) als chemiefreie Wuchshemmung eingesetzt.

### H-004: Flushing-Evidenz korrekt eingeordnet

REQ-007 referenziert korrekt die University of Guelph-Studie (2020), die keinen signifikanten Unterschied zwischen geflushten und ungeflushten Cannabis-Proben fand. Die Einordnung als "optionales Protokoll" mit Abraten bei Living Soil ist fachlich ausgewogen. Die Studie von Danziger & Bernstein (2021) koennte als zusaetzliche Referenz ergaenzt werden.

### H-005: CEC-Integration in Spuelberechnung ist herausragend

Die Verknuepfung der Kationenaustauschkapazitaet (CEC) des Substrats mit der Spueldauer und -menge in REQ-019 ist ein selten gesehenes Detail, das fachlich korrekt ist. Substrate mit hoher CEC (Erde: 100-200, Living Soil: 150-300 meq/100g) benoetigen tatsaechlich deutlich mehr Spuelvolumen als inerte Substrate (Steinwolle: 0-2, Perlite: 1-3), weil die gebundenen Ionen langsamer freigesetzt werden.

### H-006: Zimmerpflanzen-Phasen in REQ-020 biologisch sinnvoll

Die spezifischen Zimmerpflanzen-Phasen (acclimatization, active_growth, maintenance, repotting_recovery) in REQ-020 sind biologisch wesentlich sinnvoller als die Standard-Nutzpflanzen-Phasen. Die Erholungsphase nach Umtopfen (7-14 Tage) entspricht der typischen Zeitspanne, die Wurzeln benoetigen, um neues Substrat zu besiedeln (Wurzelhaar-Neubildung).

### H-007: Mediterrane Kraeuter korrekt getrennt von tropischen

REQ-022 trennt korrekt zwischen `herb_tropical` (Basilikum, Minze) und `mediterranean` (Rosmarin, Lavendel, Thymian) mit der expliziten Warnung, dass Rosmarin bei 3-Tage-Giessintervall Wurzelfaeule entwickelt. Dies ist einer der haeufigsten Pflegefehler bei Zimmerkraeutern und die Trennung ist fachlich essentiell.

### H-008: Veredelungskompatibilitaet mehrstufig modelliert

Die mehrstufige Kompatibilitaetspruefung in REQ-017 (explizite Graph-Edges vor Taxonomie-Heuristik) ist der korrekte Ansatz. Taxonomische Naehe ist ein notwendiges, aber nicht hinreichendes Kriterium fuer Veredelungserfolg. Der Hinweis, dass nicht alle Cucurbitaceae fuereinander geeignet sind, ist praxisrelevant (z.B. *Cucumis sativus* auf *Cucurbita* sp. hat niedrigere Erfolgsraten als auf *Cucumis* sp.).

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|--------------------|-----------|
| PPFD (umol/m2/s) | Ja (REQ-003, REQ-005) | artspezifisch | -- |
| DLI (mol/m2/d) | Ja (REQ-003, REQ-005, REQ-018) | artspezifisch, Zimmerpflanzen fehlen | Hoch |
| VPD (kPa) | Ja (REQ-003, REQ-005, REQ-018) | 0.4-1.4 phasenabhaengig | -- |
| EC-Wert (mS/cm) | Ja (REQ-004, REQ-005, REQ-014, REQ-019) | systemabhaengig | -- |
| pH Naehrloesung | Ja (REQ-004, REQ-014) | 5.5-6.5 (Hydro), 6.0-7.0 (Erde) | -- |
| rH% | Ja (REQ-003, REQ-005) | artspezifisch | -- |
| CO2 (ppm) | Ja (REQ-003, REQ-005, REQ-018) | 400-1200 ppm | -- |
| DO (mg/L) | Ja (REQ-014) | >6 mg/L optimal | -- |
| ORP (mV) | Ja (REQ-014) | >700 mV (steril) | -- |
| Blatttemperatur (Grad C) | Ja (REQ-005) | Luft -1 bis -3 Grad C | -- |
| Wasseraktivitaet (a_w) | Ja (REQ-008) | <0.65 (Schimmelgrenze) | -- |
| CEC (meq/100g) | Ja (REQ-019) | substrattyp-abhaengig | -- |
| Substrattemperatur (Grad C) | Ja (REQ-019) | 18-24 Grad C (Optimum), >12 Grad C (Minimum) | -- |
| DLI Zimmerpflanzen | FEHLT | 2-20 mol/m2/d je nach Art | Hoch |
| Toxizitaet (Species-Ebene) | FEHLT | boolean + Schweregrad | Hoch |
| Fenster-Transmission (%) | FEHLT | 50-70% je nach Verglasung | Mittel |
| R:FR-Verhaeltnis | Teilweise (REQ-005) | 0.5-3.0 je nach Ziel | Niedrig |
| Luftbewegung (m/s) | Ja (REQ-005) | 0.3-1.0 m/s (sanfte Brise) | -- |

---

## Konsistenz zwischen Dokumenten

### K-001: VPD-Bereiche inkonsistent

| Quelle | VPD-Bereich Bluete | Bewertung |
|--------|-------------------|-----------|
| CLAUDE.md | 0.4-0.8 kPa | Zu niedrig (Botrytis-Risiko) |
| REQ-003 requirement_profiles | `vpd_target_kpa: float` (artspezifisch) | Korrekt (kein fester Wert) |
| REQ-018 PhaseControlProfile | `target_vpd_kpa: Optional[float]` | Korrekt (phasenabhaengig) |

**Empfehlung:** CLAUDE.md korrigieren. Die REQ-Dokumente selbst sind korrekt, da sie artspezifische/phasenspezifische Werte verwenden.

### K-002: Substrat-Flushing-Dauern mehrfach definiert

| Quelle | Hydro | Coco | Soil | Bewertung |
|--------|-------|------|------|-----------|
| REQ-004 (FlushingProtocol) | Referenz-Engine | Referenz-Engine | Referenz-Engine | Autoritativ |
| REQ-007 (Fliesstext) | 7-14 Tage | 10-14 Tage | 21-28 Tage | Kompatibel |
| REQ-007 (AQL) | 10 Tage | 14 Tage | 28 Tage | Festwerte, kein Bereich |

**Empfehlung:** REQ-007 AQL sollte aus REQ-004 FlushingProtocol lesen statt eigene Konstanten zu definieren.

### K-003: WateringEvent doppelt definiert

REQ-014 (Tankmanagement) definiert `WateringEvent` als Node mit umfangreichen Properties. REQ-004 definiert `FeedingEvent` fuer denselben Zweck (Duengung/Bewaesserung auf Pflanzenebene). Die beiden Konzepte ueberlappen:
- `WateringEvent.application_method` = `FeedingEvent.application_method`
- `WateringEvent.volume_liters` ~ `FeedingEvent.volume_applied_liters`
- `WateringEvent.measured_ec_ms` ~ `FeedingEvent.measured_ec_after`

**Empfehlung:** Klarere Abgrenzung oder Zusammenfuehrung. Aktuell ist im Fliesstext von REQ-014 eine Abgrenzungstabelle vorhanden (TankFillEvent vs. WateringEvent), aber die Beziehung WateringEvent-FeedingEvent ist nicht explizit geklaert.

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL | Relevanz |
|---------|--------|-----|----------|
| Zimmerpflanzen-Toxizitaet | ASPCA Animal Poison Control | aspca.org/pet-care/animal-poison-control | Hoch — Hunde, Katzen, Pferde |
| Kindertoxizitaet | Giftinformationszentrale Bonn | gizbonn.de | Hoch — deutschsprachig |
| Taxonomie (aktuell) | Plants of the World Online | powo.science.kew.org | Hoch — APG IV konform |
| Indoor-Schaedlinge | Julius Kuehn-Institut | julius-kuehn.de | Mittel |
| Pflanzenschutz EU | EPPO Global Database | gd.eppo.int | Mittel |
| Licht-Grundlagen / PPFD | Apogee Instruments Application Notes | apogeeinstruments.com | Mittel |
| Hydroponik-Naehrstoffe | University Extension Services (z.B. Cornell CEA) | cea.cals.cornell.edu | Hoch |
| Zimmerpflanzen-DLI | Michigan State University Floriculture | canr.msu.edu | Hoch — DLI-Datenbank fuer Zierpflanzen |
| Cannabis-Studien | University of Guelph / Cannabis Research | uoguelph.ca | Mittel |
| Substratphysik | International Substrate Handbook (Raviv & Lieth) | ISBN 978-0444529756 | Niedrig — Fachliteratur |

---

## Spezifische Empfehlungen nach Anbaukontext

### Indoor / Growbox

1. **REQ-018 Lichtsteuerung:** Die DLI-basierte Steuerung (statt reiner Photoperiode) ist der richtige Ansatz. Ergaenzend sollte bei Kurztagspflanzen ein harter "Lichtunterbrechungs-Alarm" implementiert werden — bereits 1 Minute Licht waehrend der Dunkelphase kann die Bluetenbildung bei Cannabis um Wochen verzoegern (Phytochrom-Rekonversion).

2. **REQ-004 Duengelogik:** Die Misch-Sicherheitsvalidierung (CalMag vor Sulfaten) ist chemisch korrekt und praxisrelevant. Ergaenzend: Bei Verwendung von Silizium-Produkten (Potassiumsilikat) sollte die pH-Erhoehung quantifiziert werden — Kaliumsilikat kann den pH um 1-2 Einheiten anheben, was die nachfolgende pH-Korrektur erschwert.

3. **REQ-014 Tankmanagement:** Die Q10-basierte Loesungsalter-Berechnung ist fachlich exzellent. Die differenzierte Entchlorungsempfehlung (freies Chlor vs. Chloramin) ist ein oft uebersehenes Detail, das in der Praxis relevant ist.

### Zimmerpflanzen

1. **REQ-022 Pflegeerinnerungen:** Die Care-Style-Presets sind biologisch gut begruendet. Ergaenzung: Ein `aroid`-Preset fuer Aronstabgewaechse (*Monstera*, *Philodendron*, *Alocasia*) waere sinnvoll — diese bilden die groesste Zimmerpflanzen-Familie und haben spezifische Anforderungen (hohe Luftfeuchte, chunky Substrat mit Rinde/Perlite, empfindlich gegen Staunaesse an der Basis).

2. **REQ-020 Starter-Kits:** Die Toxizitaetswarnungen pro Kit sind ein wichtiges Feature. Ergaenzung: Neben den aktuellen vier Zimmerpflanzen-Arten im Kit waere *Zamioculcas zamiifolia* (ZZ-Pflanze) ein geeigneter Kandidat — extrem pflegeleicht, aber maessig giftig (Calciumoxalat). Ein separates `zimmerpflanzen-schattenliebend`-Kit waere wertvoll fuer Nordfenster-Standorte.

3. **REQ-021 Erfahrungsstufen:** Die progressive Offenlegung ist fuer Zimmerpflanzenhalter essentiell. Im Einsteiger-Modus sollte der Fokus auf visuellen Indikatoren liegen ("Blaetter haengen = giessen", "gelbe Blaetter = zu viel Wasser oder Naehrstoffmangel"), nicht auf numerischen Werten.

### Hydroponik

1. **REQ-014/REQ-019:** Die Trennung von Substrat und Naehrloesung (`none` als Substrattyp fuer DWC/NFT, Tank als Naehrstoffbehaelter) ist sauber modelliert. Die DO-Grenzwerte (<4 mg/L kritisch, >6 mg/L optimal) sind korrekt. Ergaenzung: Wassertemperatur-Monitoring sollte mit dem Pythium-Risikomodell verknuepft werden — ueber 25 Grad C verdoppelt sich das Pythium-Risiko alle 2 Grad C.

2. **REQ-004 EC-Budget:** Die EC-netto-Berechnung (Ziel-EC minus Basiswasser-EC) ist korrekt und wird haeufig vergessen. Ergaenzung: Bei Rezirkulationssystemen (REQ-014 `recirculation`) steigt die EC durch Evaporation — das System sollte zwischen EC-Anstieg durch Verdunstung (kein Problem, nur Wasser nachfuellen) und EC-Anstieg durch Naehrstoffakkumulation (Problem, Loesungswechsel noetig) unterscheiden koennen.

---

## Glossar

- **PPFD** (Photosynthetic Photon Flux Density): Mass fuer die photosynthetisch nutzbare Lichtmenge in umol/m2/s — der korrekte Wert fuer Pflanzenwachstum (nicht Lux!)
- **DLI** (Daily Light Integral): Tageslicht-Gesamtmenge in mol/m2/d — PPFD x Stunden x 0.0036
- **VPD** (Vapor Pressure Deficit): Dampfdruckdefizit in kPa — beschreibt den "Durst" der Luft, abhaengig von Temperatur und Luftfeuchtigkeit. Steuert die Transpirationsrate der Pflanze.
- **EC** (Electrical Conductivity): Elektrische Leitfaehigkeit der Naehrloesung in mS/cm — Mass fuer die Naehrstoffkonzentration
- **DIF**: Differenz zwischen Tag- und Nachttemperatur — steuert Streckungswachstum ueber Gibberellin-Synthese
- **DROP**: Kurzzeitige Temperaturabsenkung vor Lichtbeginn — Alternative zu chemischen Wuchshemmern
- **CEA** (Controlled Environment Agriculture): Gesteuerter Anbau unter vollstaendig kontrollierten Bedingungen
- **IPM** (Integrated Pest Management): Integrierter Pflanzenschutz — kombinierter biologischer, physikalischer und chemischer Ansatz
- **Photoperiodismus**: Reaktion der Pflanze auf die Tageslaenge — steuert Bluetenbildung bei Kurztagspflanzen (Cannabis, Chrysanthemen) und Langtagspflanzen (Spinat, Radieschen)
- **Epiphyt**: Pflanze die auf anderen Pflanzen waechst (nicht parasitisch) — z.B. viele Orchideen, Tillandsia, Monstera (hemiepiphytisch)
- **CEC** (Cation Exchange Capacity): Kationenaustauschkapazitaet — Mass fuer die Faehigkeit eines Substrats, Naehrstoffe zu binden und langsam freizusetzen
- **a_w** (Water Activity): Wasseraktivitaet — biologisch relevanteres Mass fuer Schimmelrisiko als relative Luftfeuchtigkeit; Schimmelpilze ab a_w > 0.65
- **DO** (Dissolved Oxygen): Geloester Sauerstoff in der Naehrloesung — kritisch fuer Wurzelgesundheit in Hydroponik
- **ORP** (Oxidation-Reduction Potential): Redoxpotential — Indikator fuer die Sterilisationseffektivitaet in Rezirkulationssystemen
- **R:FR** (Red to Far-Red Ratio): Verhaeltnis von Rotlicht zu Fernrotlicht — steuert ueber Phytochrom-Gleichgewicht Streckungswachstum und Blueteninduktion
- **GDD** (Growing Degree Days): Gradtagsumme — akkumulierte Waermeeinheiten oberhalb einer Basistemperatur, biologisch praeziser als Kalendertage fuer Entwicklungsprognosen
- **Vernalisation**: Kaeltestimulus, der fuer die Bluetenbildung bestimmter Pflanzen (viele Zweijahrige, einige Perenniale) erforderlich ist
- **Allelopathie**: Chemische Wechselwirkung zwischen Pflanzen — Freisetzung von Hemmstoffen oder Foerderstoffen ueber Wurzeln oder Blaetter
