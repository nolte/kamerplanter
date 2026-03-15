# Agrarbiologisches Review: Aktivitaetenkatalog (activities.yaml)

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-11
**Quelle:** `src/backend/app/migrations/seed_data/activities.yaml`
**Gepruefte Arten:** Chlorophytum comosum, Guzmania lingulata, Monstera deliciosa, Spathiphyllum wallisii, Fragaria x ananassa, Helianthus annuus, Viola x wittrockiana, Dahlia pinnata (mehrere Sorten), Petunia x hybrida, Tigridia pavonia, Apium graveolens var. rapaceum
**Referenzdokumente:** REQ-003 v2.3, plant-info/*.md (11 Arten), activities.yaml (40 Eintraege)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 3/5 | Mehrere biologisch falsche forbidden_phases; Cannabis-Logik auf annuelle Zierpflanzen uebertragen |
| Phasen-Konformitaet | 3/5 | Phasennamen aus der YAML passen nicht immer zu den in den plant-info-Dokumenten definierten Phasen |
| Stress-Level-Einschaetzungen | 4/5 | Groesstenteils korrekt; ein signifikanter Ausreisser (Petunia Pinching) |
| Recovery-Tage | 4/5 | Korrekt fuer die meisten Eintraege; Besonderheiten fuer Geophyten fehlen |
| species_compatible Vollstaendigkeit | 3/5 | Systematisch unvollstaendig: fehlende Arten, falsche Inklusionen, falscher Scope |
| Kategorisierung | 4/5 | Weitgehend korrekt; ein Fehler bei Celeriac Earthing Up |
| Fehlende Aktivitaeten | 3/5 | Artspezifisch wichtige Massnahmen fehlen (Spathiphyllum, Chlorophytum, Sellerie) |

**Gesamteinschaetzung:** Der Aktivitaetenkatalog ist handwerklich solide aufgebaut und deckt die wichtigsten Gruppen gut ab. Die universellen Aktivitaeten (Topping, LST, Defoliation) sind korrekt modelliert und fuer den Cannabis-Kontext biologisch valide. Im Bereich annueller Zierpflanzen und Indoor-Tropenpflanzen sind mehrere fachliche Fehler aufgefallen, die zu inkorrekt gesperrten oder erlaubten Aktivitaeten fuehren. Besonders kritisch ist die falsche Behandlung der Petunia- und Viola-Phasennamen sowie die fehlende Differenzierung zwischen Knolle (Dahlia) und Korm (Tigridia) bei den Geophyten-Aktivitaeten.

---

## Roter Bereich: Fachlich Falsch -- Sofortiger Korrekturbedarf

### F-001: Petunia Pinching -- forbidden_phases schliesst flowering aus

**Aktivitaet:** `Petunia Pinching` (sort_order: 20)
**Aktuell:** `forbidden_phases: ["germination", "senescence", "flowering"]`
**Problem:** Das Entspitzen von Petunien-Triebspitzen ist in der Praxis eine Massnahme, die WAEHREND der Bluete angewendet wird, wenn Triebe verkahlen oder verlaengern. Die Phasenstruktur der Petunia x hybrida (plant-info: germination → seedling → vegetative → hardening_off → flowering → senescence) zeigt, dass die Bluetephase 120-180 Tage dauert. In dieser Zeit ist regelmaessiges Entspitzen/Zurueckschneiden die Standardmassnahme, um die Bluetenproduktion aufrechtzuerhalten. Das Sperren dieser Aktivitaet in der Bluetephase macht sie praktisch nutzlos, da sie ausserhalb der Keimung und Seneszenz nur in der sehr kurzen vegetativen Phase (14-21 Tage) anwendbar waere.

Biologische Korrektheit: Pinching bei Petunien ist eine Massnahme, die von Gaertnern BESODERS in der Bluetephase eingesetzt wird. Vgl. die beschriebene Massnahme `Petunia Cutting Back` (sort_order: 62), die korrekt nicht durch `flowering` gesperrt wird.

**Korrekte Formulierung:** `forbidden_phases: ["germination", "seedling", "senescence"]`
**Gilt fuer Anbaukontext:** Outdoor, Gewaechshaus, Balkon

---

### F-002: Dahlia Disbudding -- forbidden_phases schliesst vegetative aus, erlaubt sprouting nicht

**Aktivitaet:** `Dahlia Disbudding` (sort_order: 21)
**Aktuell:** `forbidden_phases: ["dormancy", "sprouting", "senescence", "vegetative"]`
**Problem:** Das Entknospten bei Dahlien ist eine Massnahme, die in der Knospenbildungsphase (budding) und zu Beginn der Bluetephase angewendet wird. Die Phasenstruktur der Dahlia (plant-info: Vorkultur/Austrieb → vegetatives Wachstum → Knospenbildung → Bluete → Seneszenz → Dormanz) zeigt, dass `vegetative` korrekt ausgeschlossen ist (keine Knospen vorhanden). Jedoch ist der Phasenname `sprouting` nicht in der Dahlia-Phasendefinition vorhanden -- dort heisst die erste Phase "Vorkultur/Austrieb". Wenn `sprouting` im System als Phase fuer Geophyten verwendet wird (Knollenaustreibung), ist der Ausschluss korrekt (keine Knospen). Jedoch sollte sichergestellt werden, dass `budding` (Knospenbildungsphase) NICHT in forbidden_phases steht -- die Aktivitaet soll genau dann stattfinden.

Pruefung der Dahlia-Phasennamen: Die plant-info-Datei definiert die Phasen als "Vorkultur/Austrieb", "vegetatives Wachstum", "Knospenbildung", "Bluete", "Seneszenz", "Dormanz". Diese koennen im System als `sprouting`, `vegetative`, `budding`, `flowering`, `senescence`, `dormancy` kodiert sein. Das Entknospten erfolgt in Phase `budding` und fruehe `flowering`. Keiner dieser Namen taucht in forbidden_phases auf -- das ist korrekt fuer diese Phasen.

**Befund:** Kein kritischer Fehler, aber `sprouting` als Phasenname ist nicht dokumentiert und sollte konsolidiert werden. Wenn `sprouting` = Knollenaustreibung (Vorkultur), ist der Ausschluss korrekt. Der eigentliche Fehler ist terminologischer Natur: Consistency zwischen Phasennamen in activities.yaml und growth_phases-Collection pruefen.

**Empfehlung:** Den Phasennamen `sprouting` (der in mehreren Aktivitaeten auftaucht: Disbudding, Tuber Inspection, Tuber Division, Tuber Lifting, Corm Separation) im System konsistent definieren und dokumentieren. Dieser Name erscheint nicht in REQ-003 v2.3.

---

### F-003: Repotting -- forbidden_phases schliesst flowering aus (biologisch falsch fuer Zimmerpflanzen)

**Aktivitaet:** `Repotting` (sort_order: 13)
**Aktuell:** `forbidden_phases: ["flowering", "dormancy", "senescence"]`
**Problem:** Das generelle Sperren von Umtopfen waehrend der Bluete ist fuer Cannabis und annuelle Nutzpflanzen korrekt und praxisbewaehrt. Fuer Zimmerpflanzen wie Spathiphyllum wallisii (Einblatt) oder Monstera deliciosa ist es jedoch zu restriktiv. Spathiphyllum bluetet unter Indoor-Bedingungen mehrfach im Jahr; ein Umtopf-Verbot waehrend der Bluete wuerde praktische Pflegemassnahmen unnoetig blockieren. Monstera und Chlorophytum haben keine klar definierte Bluetephase in der Systemlogik. Die Regel ist also korrekt fuer Cannabis und Nutzpflanzen, aber zu pauschal fuer die hier betrachteten Zimmerpflanzen.

**Empfehlung:** Diese Aktivitaet hat keinen `species_compatible`-Filter, gilt also als universell. Entweder:
1. Einen `species_compatible`-Filter hinzufuegen, der Zimmerpflanzen explizit einschliesst und `flowering` fuer diese Arten erlaubt, ODER
2. `flowering` aus forbidden_phases entfernen und stattdessen nur fuer Cannabis-Kontext als `restricted_sub_phases` modellieren.

**Gilt fuer Anbaukontext:** Indoor (Zimmerpflanzen)

---

### F-004: Celeriac Earthing Up -- Kategorie und fachliche Beschreibung fehlerhaft

**Aktivitaet:** `Celeriac Earthing Up` (sort_order: 52)
**Aktuell:**
```yaml
description: "Mound soil around the celeriac crown to prevent greening and promote smooth tuber surface."
category: "general"
```
**Problem (biologisch):** Die Beschreibung "Mound soil around the celeriac crown" ist fachlich FALSCH. Die plant-info-Datei zu Apium graveolens var. rapaceum stellt klar: "Die Knolle waechst zur Haelfte ueber der Erde, NICHT mit Erde anhaeufeln". Das Anhaeufeln von Erde um Knollensellerie ist eine Kulturmassnahme, die bei KARTOFFELN (Solanum tuberosum) angewendet wird, nicht bei Knollensellerie. Der korrekte Ansatz beim Sellerie ist: Seitenwurzeln an der Knollenoberflaeche abschneiden, um die Knolle glatt und rund zu halten.

Die Beschreibung verwechselt Knollensellerie-Kulturpraxis mit Kartoffel-Kulturpraxis. "Greening" (Gruenwerden durch Lichtexposition) ist ein Problem bei Kartoffeln (Solanin-Bildung), nicht bei Sellerie. Sellerieknollen haben keine Solanin-Problematik.

**Korrekte Beschreibung:** "Remove lateral surface roots emerging from the celeriac crown to promote a smooth, round bulb shape. Do not hill soil over the crown — celeriac grows half above ground level."
**Korrekte Kategorie:** `pruning` (da es sich um das Entfernen von Seitenwurzeln handelt), nicht `general`
**Korrekte Formulierung fuer name_de:** "Sellerie Seitenwurzeln entfernen" (statt "Sellerie anhaeufeln")

**Gilt fuer Anbaukontext:** Outdoor, Gewaechshaus

---

### F-005: Tuber Division -- forbidden_phases schliesst dormancy aus (biologisch falsch)

**Aktivitaet:** `Tuber Division` (sort_order: 31)
**Aktuell:** `forbidden_phases: ["flowering", "vegetative", "senescence", "dormancy"]`
**Problem:** Das Teilen von Dahlienknollen ist eine Massnahme, die AUSSCHLIESSLICH in der fruehen Vorkulturphase (vor dem Einpflanzen) durchgefuehrt wird. Der Zeitpunkt ist: Nach dem Ausgraben im Herbst UND wenn die Knollen im Fruehjahr zu treiben beginnen (Augen sichtbar). Laut plant-info und American Dahlia Society erfolgt die Knollenteilung in der Praxis im Maerz/April, wenn die Knollen aus der Lagerung genommen werden. Das Sperren dieser Aktivitaet waehrend der `dormancy`-Phase (= Winterlagerung) ist damit faktisch falsch: Genau zu Beginn des Auftauens aus der Dormanz ist der optimale Zeitpunkt.

Richtig ist: Die Teilung erfolgt beim Uebergang von Dormanz zu Austrieb -- also NACH der Dormanz, aber VOR dem Einpflanzen. Das System kann diesen Uebergangszeitpunkt als letzte Phase der Dormanz ODER erste Phase des Austrums modellieren. Durch den Ausschluss von `dormancy` wird der Nutzer gezwungen, zuerst in eine andere Phase zu wechseln -- das entspricht nicht der botanischen Realitaet.

**Korrekte Formulierung:** `forbidden_phases: ["flowering", "vegetative", "senescence"]`
**Hinweis:** `sprouting` (Knollenaustreibung im System) sollte ebenfalls NICHT in forbidden_phases stehen -- die Teilung ist genau dann moeglich und empfohlen, wenn die Augen sichtbar werden.

**Gilt fuer Anbaukontext:** Outdoor, Gewaechshaus

---

### F-006: Runner Removal -- Fruiting-Phase nicht gesperrt (Erdbeere)

**Aktivitaet:** `Runner Removal` (sort_order: 34)
**Aktuell:** `forbidden_phases: ["germination", "dormancy"]`
**Problem:** Das Entfernen von Auslaeufern bei Erdbeeren sollte NICHT waehrend der Erntephase (`harvest`, `fruiting`) erlaubt sein ohne Einschraenkung. In der Praxis gilt: Waehrend aktiver Fruchtbildung und Ernte sollten Auslaeufer entfernt werden (Energie auf Fruechte lenken). Das ist korrekt. Aber bei juengst ausgepflanzten Jungpflanzen waehrend der Etablierungsphase (im Sommer nach Herbstpflanzung) sollten Auslaeufer im ersten Jahr voelligentfernt werden, damit sich die Pflanze etabliert. Die fehlende Sperre fuer `seedling` und `establishment` ist ein Luecke.

Wichtiger Aspekt: Der Kontext des Auslaeufer-Entfernens ist dual: (1) Fruchtproduktion foerdern = richtig, (2) fuer neue Pflanzen bewurzeln = auch waehrend Bluete moeglich. Die YAML-Beschreibung adressiert beide Kontexte, aber die forbidden_phases-Logik unterscheidet nicht.

**Empfehlung:** `seedling`-Phase hinzufuegen fuer neu etablierte Pflanzen (Auslaeufer sollten in der ersten Saison nach Pflanzung immer entfernt werden, nicht bewertet werden koennen). Keine weitere Kritik an der Grundlogik.

---

## Orangener Bereich: Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: species_compatible fuer Ausgeizen fehlt Petunia

**Aktivitaet:** `Ausgeizen` (sort_order: 10)
**Aktuell:** `species_compatible: ["Solanum lycopersicum", "Capsicum", "Solanum melongena", "Tomate", "Paprika", "Aubergine"]`
**Problem:** Petunia x hybrida gehoert zur Familie Solanaceae und das Ausgeizen ist AUCH fuer Petunien relevant (Entfernen von Achselschoesslingen fuer kompakten Wuchs bei bestimmten Sorten). Gleichzeitig gibt es die separate Aktivitaet `Petunia Pinching` (sort_order: 20), die biologisch eine aehnliche Massnahme beschreibt. Die Doppelung fuer Petunien (Ausgeizen vs. Pinching) ist verwirrend.

**Empfehlung:** Entweder Petunia in `Ausgeizen` aufnehmen und `Petunia Pinching` aufloesen, oder `Petunia Pinching` als die massgebliche Petunien-Massnahme beibehalten und Ausgeizen explizit auf echte Tomaten/Paprika/Auberginen beschraenken. Bevorzugte Loesung: `Petunia Pinching` behalten, da Petunientrriebe anders behandelt werden als Tomatenseitentriebe (Werkzeugloser Fingerschnitt vs. hygienisches Ausbrechen).

---

### U-002: Bromeliad Cup Filling -- keine forbidden_phases definiert

**Aktivitaet:** `Bromeliad Cup Filling` (sort_order: 45)
**Aktuell:** Keine `forbidden_phases`, keine `species_compatible`
**Problem:** Diese Aktivitaet hat keinen `species_compatible`-Filter, obwohl sie ausschliesslich fuer Bromelien mit Trichtermorphologie relevant ist. Guzmania lingulata hat diese Trichtermorphologie. Aber nicht alle Bromelien bilden einen Trichter (z.B. Tillandsia, Cryptanthus haben keinen funktionalen Trichter in diesem Sinne).

Die fehlenden forbidden_phases sind dagegen kein Fehler: Das Befuellen des Trichters ist eine Routinemassnahme die in allen aktiven Phasen (Kindel-Etablierung, vegetatives Wachstum, Vorbluete, Bluete, Kindel-Bildung) durchgefuehrt werden soll. Nur waehrend der `pup_establishment`-Phase der abgesetzten Kindel selbst sollte der Trichter noch nicht voll bewaessert werden.

**Empfehlung:** `species_compatible: ["Guzmania", "Vriesea", "Neoregelia", "Aechmea"]` hinzufuegen, um nur Trichter-Bromelien abzudecken.

---

### U-003: Fehlende Aktivitaet -- Spathiphyllum Bluetenstiel entfernen

**Art:** Spathiphyllum wallisii
**Problem:** Fuer das Einblatt ist eine der wichtigsten Pflegemassnahmen das Entfernen verbluhter Bluetenstiele (Spadix und Spatha nach der Bluetzeit abschneiden). Diese Massnahme hat nichts mit dem allgemeinen `Deadheading` gemein, da beim Einblatt die Spadix (Bluetenstiel) auch nach dem Verblühen bestehen bleibt und Energie kostet. Das Entfernen verbluhter Blüten ist bei Spathiphyllum wichtiger als bei anderen Zimmerpflanzen, da Samenbildung viel Energie verbraucht und die naechste Bluetenbildung verzoegert.

Spathiphyllum hat keinen eigenen Eintrag in `species_compatible` fuer irgendeine artspezifische Aktivitaet im Katalog. Die art ist in `Leaf Cleaning` gelistet (species_compatible), aber das deckt nur Blattpflege ab.

**Empfehlung:** Neue Aktivitaet hinzufuegen:
```yaml
- name: "Peace Lily Flower Removal"
  name_de: "Einblatt Bluetenstiel entfernen"
  category: "pruning"
  stress_level: "none"
  skill_level: "beginner"
  recovery_days_default: 0
  species_compatible: ["Spathiphyllum", "Einblatt"]
  forbidden_phases: ["dormancy", "germination"]
```

---

### U-004: Fehlende Aktivitaet -- Chlorophytum Auslaeuferpflege

**Art:** Chlorophytum comosum
**Problem:** Die plant-info-Datei beschreibt, dass ueberzaehlige Stolonen (Auslaeufer) im Fruehjahr entfernt werden sollten, um die Mutterpflanze zu entlasten. Diese Massnahme ist artspezifisch und wird von `Runner Removal` nicht abgedeckt (das ist explizit auf Fragaria beschraenkt). Die Kindel-Aktivitaet (`Spider Plant Pup Separation`) deckt nur das Abtrennen etablierter Kindel ab, nicht das Entfernen ueberzaehlig. Auslaeufer-Management ist fuer Chlorophytum essenziell fuer die Plaetze von Ampelpflanzen.

**Empfehlung:** Diese Massnahme koennte durch eine Erweiterung von `Runner Removal` abgedeckt werden:
`species_compatible: ["Fragaria", "Erdbeere", "Strawberry", "Chlorophytum", "Gruenlilie"]`

Mit angepasster Beschreibung, die beide Verwendungskontexte erklaert.

---

### U-005: Fehlende Aktivitaet -- Hardening Off fuer Dahlie und Tigridia

**Art:** Dahlia pinnata, Tigridia pavonia
**Problem:** Die Aktivitaet `Hardening Off` (sort_order: 50) hat keine `species_compatible`-Einschraenkung (universell) und ist somit auch fuer Dahlien und Tigridias verfuegbar. Das ist korrekt. ABER: Die `forbidden_phases`-Liste schliesst `flowering` aus -- das ist fuer Dahlien richtig, da Abhaertung vor dem Aussetzen stattfindet. Die plant-info fuer Tigridia definiert explizit eine `hardening_off`-Phase (Phase 3: Abhaertung, 7-14 Tage), die bei Voranzucht relevant ist.

Kein kritischer Fehler, aber die Aktivitaet sollte fuer die Nutzer als `Abhärten (Voranzucht)` klar erkennbar sein, dass es eine Transition-Massnahme ist, keine Dauerpflege.

---

### U-006: Fehlende Aktivitaet -- Sellerie Blaetter entfernen benoetigt `vegetative_late` Entsprechung

**Aktivitaet:** `Celeriac Leaf Stripping` (sort_order: 51)
**Aktuell:** `forbidden_phases: ["germination", "seedling", "harvest"]`
**Problem:** Die plant-info-Datei fuer Apium graveolens var. rapaceum definiert die Phasen als: Keimung → Saemling → Vegetativ → Knollenbildung → Ernte. Das Blattentfernen ist in der Knollenbildungsphase (Phase 4) vorgesehen, nicht in der vegetativen Phase (Phase 3). Die aktuelle forbidden_phases-Liste sperrt nur `germination`, `seedling` und `harvest`, erlaubt aber `vegetative`. Das fuehrt dazu, dass die Aktivitaet auch in der fruehen vegetativen Phase zulaessig waere, wo sie kontraproduktiv ist (zu frueh = reduziert Photosynthese-Kapazitaet bevor Knolle gebildet hat).

**Empfehlung:** Entweder `vegetative` in forbidden_phases aufnehmen, oder einen Hinweis in der Beschreibung ergaenzen, dass die Massnahme erst ab ca. Mitte Juli (Knollenbildungsphase) erfolgen soll: "Remove outer leaves from mid-July during bulb formation phase only."

---

### U-007: Fehlende Aktivitaet -- Dahlie Pinching (Entspitzen beim Austrieb)

**Art:** Dahlia pinnata
**Problem:** Das obligatorische Pinching bei Dahlien (Entspitzen wenn 3-4 Blattpaarpaare vorhanden, ca. 25-30 cm Hoehe) ist aus der plant-info-Datei gut dokumentiert. Das allgemeine `Pinching` (sort_order: 16) existiert und ist prinzipiell auf Dahlien anwendbar, da es keine `species_compatible`-Einschraenkung hat. ABER: Das Dahlia-Pinching hat sehr spezifische Merkmale:
- Zeitpunkt streng definiert (nach 3. Blattknotenpaar, bei ca. 25-30 cm)
- Methode: Mit Fingernaegeln, nicht mit Schere (Fingerbruch)
- Stress-Konsequenz: Ohne Pinching 1 Hauptbluete statt 4-6 Seitenblueten
- Phasenspezifisch: Nur in der fruehen vegetativen Phase

Die generische `Pinching`-Aktivitaet ist zu vage fuer Dahlien. Eine artspezifische Aktivitaet `Dahlia Pinching` fehlt.

**Empfehlung:**
```yaml
- name: "Dahlia Pinching"
  name_de: "Dahlie entspitzen (Pinching)"
  description: "Pinch out the growing tip above the 3rd leaf pair (approx. 25-30cm height) to promote 4-6 lateral shoots, each bearing a flower."
  category: "pruning"
  stress_level: "low"
  skill_level: "beginner"
  recovery_days_default: 5
  species_compatible: ["Dahlia", "Dahlie"]
  forbidden_phases: ["dormancy", "sprouting", "budding", "flowering", "senescence"]
  estimated_duration_minutes: 5
```

---

## Gelber Bereich: Zu Ungenau -- Praezisierung noetig

### P-001: Mainlining -- forbidden_phases fehlt "budding"

**Aktivitaet:** `Mainlining` (sort_order: 3)
**Aktuell:** `forbidden_phases: ["flowering", "harvest", "ripening", "senescence", "dormancy"]`
**Problem:** Im Vergleich zu `Topping` und `FIM` fehlt in den forbidden_phases von Mainlining die Phasen `budding` und `corm_ripening`. Mainlining ist eine High-Stress-Technik (multiple Toppings), die ausschliesslich in der fruehen vegetativen Phase angewendet werden sollte. `budding` (sofern als eigene Phase im System vorhanden) sollte ebenfalls gesperrt sein, da Mainlining Zeit fuer Erholung benoetigt die in der Knospenbildungsphase nicht mehr zur Verfuegung steht.

**Empfehlung:** `forbidden_phases: ["flowering", "harvest", "ripening", "senescence", "dormancy", "budding", "corm_ripening"]` -- konsistent mit Topping und FIM.

---

### P-002: Supercropping -- restricted_sub_phases statt forbidden_phases

**Aktivitaet:** `Supercropping` (sort_order: 4)
**Aktuell:**
```yaml
restricted_sub_phases: ["mid_flower", "late_flower"]
forbidden_phases: ["senescence", "dormancy", "ripening"]
```
**Hinweis:** Supercropping kann in der fruehen Bluetephase noch sinnvoll sein (erste 2-3 Wochen), wird aber spaeter problematisch. Die Modellierung mit `restricted_sub_phases` ist korrekt und biologisch praeziser als ein Komplett-Verbot in `flowering`. Die fehlende Aufnahme von `harvest` in forbidden_phases ist eine kleine Luecke -- Supercropping vor der Ernte macht keinen Sinn.

**Empfehlung:** `harvest` zu forbidden_phases hinzufuegen.

---

### P-003: Light Defoliation -- Erlaubt in flowering ohne Einschraenkung

**Aktivitaet:** `Light Defoliation` (sort_order: 7)
**Aktuell:** `forbidden_phases: ["dormancy", "germination", "senescence"]`
**Problem:** Leichte Entlaubung waehrend der Bluetephase ist biologisch nicht grundsaetzlich verboten, aber artabhaengig sehr unterschiedlich zu beurteilen:
- Cannabis: Erlaubt in der fruehen Bluete (bis Woche 3-4), dann einschraenken
- Tomaten: Nicht waehrend der Bluete (Pollenverlust durch erhoehte Luftbewegung am Blutenstand)
- Dahlien: Sehr konservativ handhaben in der Bluetephase (Blaetter ernaehren Knollenspeicher)
- Zimmerpflanzen: Entlaubung waehrend der Bluete nicht sinnvoll

Die Aktivitaet hat keinen `species_compatible`-Filter und gilt universal. Ohne Einschraenkung in `flowering` wird das System eine leichte Entlaubung in allen Arten waehrend der Bluete als valide markieren, was fuer mehrere der 11 Arten hier fachlich falsch ist.

**Empfehlung:** Entweder `species_compatible` auf Cannabis/Tomaten einschraenken, oder in der Beschreibung klar kommunizieren, dass Defoliation waehrend der Bluete artabhaengig zu bewerten ist. Alternativ `restricted_sub_phases: ["late_flower"]` hinzufuegen.

---

### P-004: Bromeliad Pup Separation -- Stress-Level Medium erscheint hoch

**Aktivitaet:** `Bromeliad Pup Separation` (sort_order: 44)
**Aktuell:** `stress_level: "medium"`, `recovery_days_default: 5`
**Hinweis:** Das Abtrennen von Bromelienkindeln ist fuer die Mutterpflanze (die sowieso stirbt) tatsaechlich stress-neutral. Fuer das Kindel selbst ist `medium` angemessen -- das Kindel muss sich neu etablieren. Die 5 Erholungstage sind fuer das Kindel-Stadium korrekt. Kein kritischer Fehler, aber eine Klarstellung in der Beschreibung waere hilfreich: Der Stress trifft das Kindel, nicht die Mutterpflanze.

---

### P-005: Aerial Root Training -- Monstera-spezifisch, aber nicht fuer alle Monstera-Arten gleich

**Aktivitaet:** `Aerial Root Training` (sort_order: 40)
**Aktuell:** `species_compatible: ["Monstera", "Fensterblatt"]`
**Hinweis:** Luftwurzeln leiten ist fuer Monstera deliciosa und Monstera adansonii relevant, aber mit unterschiedlicher Intensitaet. Monstera adansonii hat schwaechere Luftwurzeln. Kein fundamentaler Fehler, aber `Monstera adansonii` koennte zur species_compatible-Liste hinzugefuegt werden, da diese Art ebenfalls Moosstab-Unterstuetzung benoetigt.

**Empfehlung:** `species_compatible: ["Monstera", "Fensterblatt", "Monstera deliciosa", "Monstera adansonii", "Rhaphidophora"]`

---

### P-006: Flushing -- Falsch kategorisiert als universal fuer Zimmerpflanzen

**Aktivitaet:** `Flushing` (sort_order: 14)
**Aktuell:** Keine `species_compatible`, `forbidden_phases: ["dormancy", "germination"]`
**Problem:** Das Pre-Harvest-Flushing (Spuelen des Substrats vor der Ernte) ist eine Cannabis/Hydroponik-spezifische Massnahme. REQ-003 v2.3 stellt klar: "Abgrenzung DORMANCY vs. FLUSHING: `flushing` ist eine aktive Kulturmassnahme (Pre-Harvest-Flush, Substrat-Entsalzung)." Das generelle Spaelen von Zimmerpflanzen-Substraten alle 3-4 Monate (wie in den plant-info-Dateien beschrieben) ist biologisch etwas anderes und sollte als separate Aktivitaet "Substrate Flushing (Salzauswaschung)" modelliert werden.

Die aktuelle Aktivitaet `Flushing` ohne `species_compatible`-Filter suggeriert, dass Monstera, Spathiphyllum und Erdbeeren den gleichen Pre-Harvest-Flush benoetigen wie Cannabis -- das ist biologisch irrelevant oder sogar kontraproduktiv fuer Zierpflanzen.

**Empfehlung:** Entweder `species_compatible` auf Cannabis/Hydroponiksysteme beschraenken, oder zwei separate Aktivitaeten erstellen:
1. `Flushing (Pre-Harvest)` -- Cannabis/Hydroponik, mit `allowed_phases: ["ripening", "late_flower"]`
2. `Substrate Salt Leaching` -- Zimmerpflanzen, periodische Salzauswaschung ohne Ernte-Bezug

---

### P-007: Pansy Rejuvenation Cut -- Timing-Formulierung ungenau

**Aktivitaet:** `Pansy Rejuvenation Cut` (sort_order: 61)
**Aktuell:** `description: "Cut back leggy pansy stems by half in midsummer..."`
**Problem:** Der Verjuengungsschnitt bei Stiefmuetterchen waehrend des Hochsommers ist biologisch korrekt (Juli-August). Aber: Die plant-info-Datei stellt klar, dass Viola x wittrockiana ab 22 C Thermoinhibition zeigt und die Bluete einstellt. Der "Verjuengungsschnitt im Hochsommer" ist damit nicht fuer alle Klimabedingungen gleich sinnvoll -- in heissen Regionen koennte die Pflanze die Erholungsphase nicht ueberleben. Fuer Mitteleuropa mit gemaessigtem Klima ist der Timing-Hinweis korrekt.

**Empfehlung:** Formulierung praezisieren: "Cut back leggy pansy stems by half in midsummer heat break (mid-July) to trigger a second flush of blooms in autumn. Avoid severe cutting during heat waves above 25 C."

---

### P-008: Sunflower Staking und Head Support -- ueberschneiden sich

**Aktivitaeten:** `Sunflower Staking` (sort_order: 23) und `Sunflower Head Support` (sort_order: 53)
**Problem:** Beide Aktivitaeten sind fuer Helianthus annuus und beschreiben Stuetz-Massnahmen. Die Unterscheidung ist:
- `Sunflower Staking`: Stab setzen fuer den Staengel (fruehe Vegetationsphase)
- `Sunflower Head Support`: Kopf stuetzen waehrend der Reife (Abreifephase)

Diese Unterscheidung ist korrekt und biologisch valide. Beide Aktivitaeten haben jedoch unterschiedliche `forbidden_phases`:
- Staking: gesperrt in `germination, senescence, ripening`
- Head Support: gesperrt in `germination, seedling, senescence`

Das `ripening` in den forbidden_phases von Staking ist falsch: Der Stab muss vor der Reife bereits gesetzt sein, kann aber AUCH in der Reifephase noch nachgeholt werden wenn noetig. Das Sperren in `ripening` verhindert das Nachbessern.

**Empfehlung:** `ripening` aus forbidden_phases von `Sunflower Staking` entfernen.

---

## Greuner Bereich: Hinweise und Best Practices

### H-001: Universal-Aktivitaeten -- Kein species_compatible Filter ist Design-Entscheidung

Die universellen Aktivitaeten (Topping, FIM, Mainlining, Supercropping, LST, SCROG, Light Defoliation, Heavy Defoliation, Lollipopping, Pruning General, Transplanting, Repotting, Flushing, Pinching, Root Pruning, Cloning) haben bewusst keinen `species_compatible`-Filter. Das ist eine explizite Design-Entscheidung: Die forbidden_phases und skill_levels regulieren den Zugang. Fachlich korrekt ist das fuer die meisten Cannabis-orientierten Techniken. Fuer den Einsatz mit Zimmerpflanzen und Outdoor-Arten sollte das System jedoch im UI klarstellen, ob eine Technik "allgemein" oder "cannabis-typisch" ist.

**Empfehlung:** Tags erweitem um Kontext-Tags: `["cannabis"]`, `["ornamental"]`, `["vegetable"]`, `["indoor"]`, `["outdoor"]`. Beispiel: Topping sollte `tags: ["hst", "branching", "cannabis"]` haben.

---

### H-002: recovery_days_by_species -- Nur Cannabis ist definiert

In mehreren High-Stress-Aktivitaeten (Topping, FIM) sind `recovery_days_by_species` nur fuer Cannabis definiert. Andere Arten wie Tomaten (Solanum lycopersicum) erholen sich ebenfalls unterschiedlich schnell. Fuer die 11 betrachteten Arten waeren folgende artspezifische Angaben biologisch sinnvoll:

| Aktivitaet | Art | Empfohlene Erholung |
|-----------|-----|---------------------|
| Topping | Petunia x hybrida | 3 Tage (robust, schnell) |
| Topping | Helianthus annuus | 5 Tage (kraeuselt sich, erholt sich gut) |
| Root Pruning | Monstera deliciosa | 14 Tage (langsam wachsend, Luftwurzeln) |
| Transplanting | Fragaria x ananassa | 7 Tage (Feingefuehliges Faserwurzelsystem) |
| Cloning | Monstera deliciosa | 21 Tage (langsame Bewurzelung) |

---

### H-003: Skill Level -- Dahlia Disbudding als intermediate korrekt eingestuft

Das Entknospten bei Dahlien als `intermediate` einzustufen ist korrekt. Anfaenger entfernen haeufig die falsche Knospe (Hauptterminalknospe statt Seitenknospen) was zum Verlust der Hauptbluete fuehrt. Die biologische Grundlage: Bei Dinner-Plate-Dahlien (wie 'Lavender Perfection') soll die zentrale Terminalknospe behalten werden, die beiden flankierenden Seitenknospen werden entfernt. Das erscheint kontraintuitiv (warum die kleinen entfernen?) und erfordert Erklaerung.

---

### H-004: Guzmania-Aktivitaet Bromeliad Cup Filling -- Wasserqualitaet fehlt in Beschreibung

**Aktivitaet:** `Bromeliad Cup Filling` (sort_order: 45)
**Aktuell:** Beschreibung erwaehnt "rainwater or distilled water" -- das ist biologisch korrekt. Kalkreiches Leitungswasser fuehrt bei Bromelien zu Mineraleinlagerungen im Trichter und kann langfristig schaedigen.

**Ergaenzung:** Die Beschreibung sollte auch Chlorid-Empfindlichkeit erwaehnen: "Avoid tap water with high chlorine or fluoride content. Rainwater, distilled water or RO water preferred. Hard water (>200 mg/L CaCO3) causes mineral deposits in the cup."

---

### H-005: Corm Separation fuer Tigridia -- Timing-Angabe fehlt

**Aktivitaet:** `Corm Separation` (sort_order: 33)
**Aktuell:** `forbidden_phases: ["flowering", "vegetative", "sprouting", "dormancy"]`
**Problem:** Diese forbidden_phases-Kombination erlaubt die Kormentrennung nur in der Phase, die der Abreife entspricht (nach Bluete, vor Dormanz). Das ist korrekt -- die Separation erfolgt beim Ausgraben im Herbst (Oktober). Aber die Beschreibung erwaehnt nur "after lifting", ohne zu spezifizieren, dass die Separation AUCH waehrend der Lagerung (Dormanz) erfolgen kann wenn die Knollen-Klumpen noch nicht getrennt wurden.

**Empfehlung:** `dormancy` aus forbidden_phases entfernen -- die Separation kann auch zu Beginn der Dormanz-Phase (beim Einlagern) erfolgen.

---

## Zusammenfassung der priorisierten Korrekturen

| ID | Aktivitaet | Typ | Prioritaet | Aufwand |
|----|-----------|-----|-----------|---------|
| F-001 | Petunia Pinching -- flowering erlauben | Fehler | Kritisch | Klein |
| F-004 | Celeriac Earthing Up -- Beschreibung und Kategorie korrigieren | Fehler | Kritisch | Mittel |
| F-005 | Tuber Division -- dormancy aus forbidden_phases entfernen | Fehler | Hoch | Klein |
| F-003 | Repotting -- flowering-Sperre fuer Zimmerpflanzen ueberdenken | Fehler | Hoch | Mittel |
| F-002 | Dahlia Disbudding -- Phasenname sprouting klaeren | Klarstellung | Mittel | Klein |
| F-006 | Runner Removal -- seedling in forbidden_phases | Luecke | Mittel | Klein |
| U-003 | Spathiphyllum Bluetenstiel-Aktivitaet hinzufuegen | Fehlen | Hoch | Klein |
| U-007 | Dahlia Pinching als eigenstaendige Aktivitaet | Fehlen | Hoch | Klein |
| P-006 | Flushing -- species_compatible oder Aufspaltung | Unschaerfe | Mittel | Mittel |
| P-001 | Mainlining -- budding und corm_ripening hinzufuegen | Luecke | Niedrig | Klein |
| P-008 | Sunflower Staking -- ripening aus forbidden_phases entfernen | Fehler | Niedrig | Klein |

---

## Artspezifische Zusammenfassung

### Chlorophytum comosum (Gruenlilie)
- `Spider Plant Pup Separation` korrekt modelliert
- Fehlend: Auslaeufer-Entfernung (Stolonen ohne Kindel)
- Fehlend: Blattpflege/Brauner Blattspitzen-Schnitt (artspezifisch wichtig wegen Fluorid-Empfindlichkeit)
- `Leaf Cleaning` als universelle Aktivitaet abgedeckt -- ausreichend

### Guzmania lingulata
- `Bromeliad Pup Separation` und `Bromeliad Cup Filling` gut modelliert
- Cup Filling benoetigt `species_compatible`-Filter fuer Trichter-Bromelien
- Pup Separation: forbidden_phases `pup_establishment` passt zu den definierten Guzmania-Phasen (pup_establishment, vegetative_growth, pre_bloom, blooming, pup_formation)

### Monstera deliciosa
- `Aerial Root Training` und `Moss Pole Extension` korrekt
- `Leaf Cleaning` korrekt
- `Repotting`-Einschraenkung in flowering waere fuer Monstera falsch (Monstera bluet Indoor kaum, aber theoretisch)
- Fehlend: Air Layering als Vermehrungsaktivitaet (Luftabsenker)

### Spathiphyllum wallisii
- Nur in `Leaf Cleaning` gelistet
- Keine artspezifische Aktivitaet vorhanden
- Kritisch fehlend: Bluetenstiel-Entfernung nach Verbluenung

### Fragaria x ananassa (Erdbeere)
- `Runner Removal` korrekt modelliert
- Erdbeerlaub-Rueckschnitt nach der Ernte (Julirueckschnitt) fehlt als Aktivitaet
- Recovery-Tage nach Transplanting (7 Tage) sollten artspezifisch erhoehen werden

### Helianthus annuus (Sonnenblume)
- `Sunflower Staking` und `Sunflower Head Support` gut modelliert
- `ripening`-Korrektur noetig bei Staking (F-008)
- Topping als Aktivitaet fuer verzweigende Sonnenblumensorten biologisch moeglich aber nicht abgedeckt (Nischenthema)

### Viola x wittrockiana (Stiefmuetterchen)
- `Pansy Deadheading` und `Pansy Rejuvenation Cut` korrekt modelliert
- Timing-Hinweis bei Rejuvenation Cut erweitem (s. P-007)
- Kein kritischer Fehler

### Dahlia pinnata (Dahlie)
- `Dahlia Disbudding`, `Dahlia Staking`, `Tuber Inspection`, `Tuber Division`, `Tuber Lifting` gut modelliert
- Kritisch fehlend: Dahlia Pinching (obligatorisch bei Dinner-Plate-Dahlien)
- `sprouting`-Phasenname klaerungsbeduerfte (s. F-002, F-005)

### Petunia x hybrida (Petunie)
- `Petunia Pinching` mit korrekt falscher forbidden_phase (s. F-001 -- kritischer Fehler)
- `Petunia Cutting Back` korrekt
- Kein weiterer kritischer Fehler

### Tigridia pavonia (Tigerblume/Pfauenblume)
- `Corm Separation` modelliert, aber `dormancy` sollte aus forbidden_phases entfernt werden
- `Tuber Lifting` abgedeckt (gemeinsam mit Dahlie)
- `Tuber Inspection` abgedeckt (gemeinsam mit Dahlie)

### Apium graveolens var. rapaceum (Knollensellerie)
- `Celeriac Leaf Stripping` korrekt vorhanden, aber Timing-Einschraenkung erweitem
- `Celeriac Earthing Up` mit kritisch falscher Beschreibung (s. F-004 -- muss korrigiert werden)
- Fehlend: Seitenwurzel-Entfernung an der Knollenoberflaeche (artspezifisch, wichtig)

---

## Empfohlene neue Aktivitaeten (Kurzzusammenfassung)

| Name | Art | Kategorie | Prioritaet |
|------|-----|-----------|-----------|
| Dahlia Pinching | Dahlia | pruning | Hoch |
| Peace Lily Flower Removal | Spathiphyllum | pruning | Hoch |
| Air Layering | Monstera, Ficus | propagation | Mittel |
| Celeriac Crown Root Removal | Apium | pruning | Hoch |
| Substrate Salt Leaching | Zimmerpflanzen allg. | general | Mittel |
| Strawberry Post-Harvest Cutback | Fragaria | pruning | Mittel |

---

## Glossar

- **Monokarpe Pflanze:** Pflanze, die nur einmal im Leben bluetet und danach abstirbt (z.B. Guzmania lingulata). Der Gesamtorganismus (mit Kindeln) ist perennial.
- **Korm (Corm):** Solides unterirdisches Speicherorgan ohne Schalen (Tigridia). Unterschied zur Zwiebel (Tunica, Schalen) und zur Dahlienknolle (Knollenbueschel mit Haupt- und Tochterknollen).
- **Ausgeizen:** Entfernen von Achselschoesslingen bei Tomaten und Paprika, um den Haupttrieb zu staerken. Verschieden vom Entspitzen (Pinching), bei dem die Triebspitze entfernt wird.
- **Disbudding (Entknospten):** Entfernen von Seitenknospen, damit eine Hauptknospe sich zur maximalen Blute entwickeln kann. Haeufig bei Dahlien, Chrysanthemen und Rosen.
- **Thermoinhibition:** Hemmung der Keimung oder Bluetenbildung bei Temperaturen ueber einem Schwellenwert. Typisch fuer Viola x wittrockiana (ab 22 C).
- **Vernalisation:** Kaealtereiz, der zur Bluteninduktion notwendig ist. Bei Biennialen (Sellerie) loest ungewollte Vernalisation vorzeitiges Schossen aus.
- **Stolone:** Oberirdischer kriechender Auslaeufer, an dessen Enden sich neue Pflanzen bilden (Erdbeere, Chlorophytum). Unterschied zum Rhizom (unterirdisch).
- **forbidden_phases:** Im Kamerplanter-System definierte Phasen, in denen eine Aktivitaet nicht angewendet werden darf. Verletzt der Nutzer diese Regel, gibt das System eine Warnung aus.
- **sprouting:** Phasenname fuer Knollenaustreibung (Geophyten), erscheint in der activities.yaml aber ist nicht in REQ-003 v2.3 als offizieller PhaseName-Enum-Wert definiert. Klaerungsbedarf.
