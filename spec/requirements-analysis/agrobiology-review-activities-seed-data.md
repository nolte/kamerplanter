# Agrarbiologisches Review: activities.yaml — Seed-Daten Gesamtbewertung
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-15
**Dokument:** `src/backend/app/migrations/seed_data/activities.yaml`
**Engine:** `src/backend/app/domain/engines/activity_plan_engine.py`
**Service:** `src/backend/app/domain/services/activity_plan_service.py`
**Scope:** 43 Aktivitaeten — vollstaendige Systemanalyse inkl. Filterfelder, Erholungszeiten,
Skill/Stress-Einstufung, Werkzeuge, Phasensperren und fehlende Aktivitaeten

**Abgrenzung zu Vorgaenger-Reviews:**
Dieses Review schliesst an die bestehenden Reviews
`agrobiology-review-activity-descriptions-2026-03.md` (biologische Korrektheit der Texte)
und `agrobiology-review-activity-plans-2026-03.md` (Phasen-Konformitaet) an.
Bereits dokumentierte Befunde werden hier als Referenz zitiert, aber nicht doppelt ausgefuehrt.
Der Schwerpunkt liegt auf: (1) strukturellen Filterfeldern (`applicable_growth_habits`,
`applicable_families`, `requires_support`, `requires_container`), (2) `recovery_days`-Logik,
(3) engine-seitigen Konsequenzen, und (4) fehlenden Aktivitaeten fuer die abgedeckten Arten.

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Grundlagen solide; ca. 8 biologische Ungenauigkeiten (Details in Vorgaenger-Reviews) |
| `applicable_growth_habits`-Abdeckung | 2/5 | Nur 5 von 43 Aktivitaeten nutzen das Feld; viele universelle Aktivitaeten ungefiltert |
| `applicable_families`-Abdeckung | 1/5 | Feld in keiner einzigen Aktivitaet gesetzt — komplett ungenutzt |
| `requires_support` / `requires_container` | 3/5 | Nur 3 Aktivitaeten genutzt; logisch korrekt, aber Potenzial nicht ausgeschoepft |
| `recovery_days`-Kalibrierung | 4/5 | Ueberwiegend realistisch; zwei Ausreisser (Lollipopping, Tuber Division) |
| `stress_level`-Einstufung | 4/5 | Weitgehend korrekt; Supercropping-Grenzfall (detail in Vorgaenger-Review B-003) |
| `skill_level`-Einstufung | 4/5 | Konsistent; Dahlia Staking als beginner korrekt |
| `tools_required`-Vollstaendigkeit | 3/5 | 6 Luecken (detail in Vorgaenger-Review W-001--W-006) |
| `forbidden_phases`-Korrektheit | 3/5 | 7+ Fehler dokumentiert; Topping/FIM `budding`-Phase fehlt |
| Fehlende Aktivitaeten | 2/5 | Mehrere wichtige Pflegemassnahmen fuer abgedeckte Arten fehlen |

**Gesamteinschaetzung:** Der Katalog leistet gute Arbeit fuer Cannabis und Geophyten. Die
strukturellen Filterfelder (`applicable_growth_habits`, `applicable_families`) sind fast
vollstaendig ungenutzt — das fuehrt dazu, dass der `ActivityPlanEngine` generische Aktivitaeten
ohne artenspezifische Einschraenkung ausgibt, was bei der Planerstellung zu irrelevanten
Vorschlaegen fuehrt (z.B. "Root Pruning" fuer krautige Einjahrige, "Cloning" fuer Geophyten).
Acht wichtige Aktivitaeten fehlen komplett fuer die abgedeckten Arten.

---

## Rot — Fachlich Falsch: Sofortiger Korrekturbedarf

### F-001: Topping und FIM — `forbidden_phases` schliesst `budding` nicht aus
**Aktivitaeten:** `Topping` (sort_order: 1), `FIM` (sort_order: 2)
**Problem:** Beide Aktivitaeten sperren `["flowering", "harvest", "ripening", "senescence",
"dormancy", "budding", "corm_ripening"]`. Der Phasenname `budding` ist korrekt fuer Cannabis
(Vorblute-Periode). Die `forbidden_phases`-Liste enthaelt `budding` bereits — das ist korrekt.
Jedoch fehlt bei `Mainlining` (sort_order: 3) das `budding` in `forbidden_phases`:
`forbidden_phases: ["flowering", "harvest", "ripening", "senescence", "dormancy"]`.

Mainlining besteht aus mehrfachem Topping und muss daher denselben Phasensperren unterliegen
wie Topping. Der Beginn der Knospenbildung (budding) waehrend Mainlining wuerde die
Technik biologisch sinnlos machen, da die Pflanze keine neuen vegetativen Strukturen mehr
ausbildet.

**Korrekte Formulierung:** `Mainlining.forbidden_phases` erganzen: `["flowering", "harvest",
"ripening", "senescence", "dormancy", "budding", "corm_ripening"]`

---

### F-002: `Heavy Defoliation` — `forbidden_phases` schliesst `flowering` aus (Widerspruch zur Beschreibung)
**Referenz:** Bereits als K-001 in `agrobiology-review-activity-descriptions-2026-03.md`
dokumentiert. Zur Vollstaendigkeit: `forbidden_phases` muss `"flowering"` entfernen und stattdessen
`restricted_sub_phases: ["mid_flower", "late_flower"]` verwenden, da die Anwendung zu
Blutebeginn (Tag 1-3) die Hauptanwendung der Methode ist.

---

### F-003: `Lollipopping` — `restricted_sub_phases` unvollstaendig
**Referenz:** Bereits als B-004 in `agrobiology-review-activity-descriptions-2026-03.md`
dokumentiert. `"late_flower"` fehlt in `restricted_sub_phases`.

---

### F-004: `Repotting` — generelles `flowering`-Verbot biologisch falsch fuer Zimmerpflanzen
**Referenz:** Bereits als F-003 in `agrobiology-review-activity-plans-2026-03.md` dokumentiert.
Das generelle `flowering`-Verbot in `forbidden_phases` ist fuer Cannabis korrekt, blockiert aber
sinnvolle Pflegemassnahmen bei dauerbluhenden Zimmerpflanzen (Spathiphyllum, Chlorophytum).

---

### F-005: `Petunia Pinching` — `flowering` in `forbidden_phases` macht Aktivitaet wertlos
**Referenz:** Bereits als F-001 in `agrobiology-review-activity-plans-2026-03.md` dokumentiert.
Das Entspitzen waehrend der Bluete ist die Hauptanwendung der Technik bei Petunien.

---

## Orange — Strukturelle Probleme: Wichtige Korrekturen

### S-001: `applicable_growth_habits` — systematisch untergenutzt
**Problem:** Von 43 Aktivitaeten setzen nur 5 das Feld `applicable_growth_habits`:
- `Light Defoliation`: `["herb", "shrub", "vine"]` — korrekt
- `Pruning (General)`: `["herb", "shrub", "tree", "vine"]` — korrekt
- `Pinching`: `["herb", "groundcover"]` — korrekt, aber fehlend: `"shrub"` (Chrysanthemen, Basilikum)
- `Root Pruning`: `["tree", "shrub"]` — korrekt
- `Cloning`: `["herb", "shrub", "vine"]` — korrekt

**Konsequenz fuer den Engine:** Die `_filter_activities`-Methode des `ActivityPlanEngine` wendet
den `applicable_growth_habits`-Filter nur an, wenn `species_compatible` leer ist (generische
Aktivitaeten). Wenn beide Felder leer sind, wird die Aktivitaet fuer jede Art vorgeschlagen.
Das fuehrt zu biologisch sinnlosen Plan-Eintraegen:

| Aktivitaet | Vorgeschlagen fuer | Problem |
|------------|-------------------|---------|
| `Deadheading` | Succulenten, Kakteen, Geophyten (Ruhe) | Sinnlos fuer Pflanzen ohne Dauerblute |
| `Runner Removal` | Cannabis, Monstera, Sellerie | Nur fuer Fragaria relevant |
| `Hardening Off` | Indoor-Zimmerpflanzen | Sinnlos ohne Aussenbereich |
| `Pansy Deadheading` | Alle Pflanzen ohne `species_compatible` | Hat `species_compatible`, also ok |
| `Transplanting` / `Repotting` | Alle Arten | `requires_container: true` filtert korrekt |

**Fehlende `applicable_growth_habits`-Eintrage (Empfehlungen):**

| Aktivitaet | Empfohlenes Feld |
|------------|-----------------|
| `Deadheading` | `applicable_growth_habits: ["herb", "shrub", "groundcover"]` |
| `Hardening Off` | kein growth_habit-Filter noetig, aber `applicable_families` auf Outdoor-Arten beschraenken |
| `Pinching` | `shrub` hinzufuegen (Chrysanthemen, Basilikum sind Straucher oder krautige Straucher) |

---

### S-002: `applicable_families` — komplett ungenutzt
**Problem:** Das Feld `applicable_families` ist in KEINER der 43 Aktivitaeten gesetzt.
Der Engine-Code in `_filter_activities` prueft dieses Feld aktiv:
```python
if act.applicable_families and family_name:
    if not any(f.lower() in family_lower or family_lower in f.lower() for f in act.applicable_families):
        continue
```
Das Feld ist implementiert, aber nie genutzt. Fuer familien-spezifische Aktivitaeten, die
derzeit nur ueber `species_compatible` eingeschraenkt werden, waere `applicable_families`
praeziser und wartbarer.

**Konkrete Faelle wo `applicable_families` passend waere:**

| Aktivitaet | Derzeitiger Filter | Sinnvoller Familien-Filter |
|------------|-------------------|-----------------------------|
| `Ausgeizen` | `species_compatible: [Solanum lycopersicum, Capsicum...]` | `applicable_families: ["Solanaceae"]` |
| `Runner Removal` | `species_compatible: [Fragaria...]` | `applicable_families: ["Rosaceae"]` (nur mit `growth_habit: groundcover`) |
| `Bromeliad Cup Filling` | `species_compatible: [Guzmania, Bromelie]` | `applicable_families: ["Bromeliaceae"]` |
| `Bromeliad Pup Separation` | analog | `applicable_families: ["Bromeliaceae"]` |

**Empfehlung:** Fuer die naechste Iteration `applicable_families` befuellen und `species_compatible`
auf echte Artausnahmen beschraenken (z.B. wenn eine Aktivitaet nur fuer eine Art innerhalb einer
Familie gilt).

---

### S-003: `requires_support` — nicht genutzt, obwohl `Dahlia Staking` und `Sunflower Staking` passen
**Problem:** Das Feld `requires_support` ist im Model definiert und der Engine prueft es:
```python
if act.requires_support is True and not support_required:
    continue
```
Jedoch setzen `Dahlia Staking` und `Sunflower Staking` das Feld nicht — sie verwenden
stattdessen `species_compatible`. Das ist funktional korrekt, aber inkonsequent. Fuer generisches
Staking (z.B. "Anbinden und Stielen" ohne Artbindung) waere `requires_support: true` der
praezisere Filter.

**Konkret betroffen:**
- `Dahlia Staking`: `species_compatible` korrekt gesetzt — kein Fehler, aber Potenzial liegt brach
- `Sunflower Staking`: analog

**Empfehlung:** Eine neue generische Aktivitaet "Staking / Anbinden" ohne `species_compatible`,
dafuer mit `requires_support: true` einfuehren (siehe Abschnitt Fehlende Aktivitaeten).

---

### S-004: `recovery_days_by_species` — zu wenig genutzt
**Problem:** Nur drei Aktivitaeten nutzen `recovery_days_by_species`:
- `Topping`: `cannabis: 7` (default: 5) — biologisch korrekt
- `FIM`: `cannabis: 7` (default: 5) — biologisch korrekt
- `Mainlining`: `cannabis: 7` (default: 5) — biologisch korrekt

Fuer andere Arten mit bekannt unterschiedlichen Erholungszeiten fehlen Eintrage:

| Aktivitaet | Art | Empfohlener Wert | Begruendung |
|------------|-----|-----------------|-------------|
| `Transplanting` | Cannabis | 3 | Schnell wachsende, regenerative Art; weniger als Standardwert 5 |
| `Transplanting` | Sellerie | 7 | Halbierte Stressschwelle bei Jungpflanzen; Feinwurzel-Regeneration langsamer |
| `Root Pruning` | `bonsai` (Ficus, Zelkova) | 14 | Verholzte Arten regenerieren Feinwurzeln langsamer als krautige |
| `Cloning` | Cannabis | 14 | Steckling-Regenerationszeit fuer Mutterpflanze nach mehreren Schnitten |

---

## Gelb — Praezisierungsbedarf: Erholungszeiten und Einstufungen

### E-001: `Lollipopping` — `recovery_days_default: 5` zu gering fuer Hochstress-Massnahme
**Aktivitaet:** `Lollipopping` (sort_order: 9), `stress_level: "high"`
**Problem:** Lollipopping ist als `stress_level: "high"` eingestuft, hat aber denselben
`recovery_days_default: 5` wie Topping. Da Lollipopping waehrend der Bluete deutlich groessere
Biomasse entfernt als Topping (gesamter Unterwuchs vs. einzelner Triebspitz), ist eine
Erholungszeit von 5 Tagen zu gering. In der Praxis zeigen Cannabis-Pflanzen nach aggressivem
Lollipopping 7-10 Tage verringerten Blutenwachstum.

**Empfehlung:** `recovery_days_default: 7`, `recovery_days_by_species: {cannabis: 10}`

---

### E-002: `Tuber Division` — `recovery_days_default: 7` bezieht sich auf falsche Einheit
**Aktivitaet:** `Tuber Division` (sort_order: 31)
**Problem:** Der Wert `recovery_days_default: 7` suggeriert, dass die Pflanze 7 Tage nach der
Knollenteilung "Erholung" braucht, bevor die naechste Aktivitaet stattfindet. Da die Teilung
aber WAEHREND der Dormanz erfolgt (und die Pflanze danach erst nach Wochen austreibt), ist der
Wert konzeptuell unklar. Der Engine-Recovery-Mechanismus soll verhindern, dass zwei hochstress-
Aktivitaeten direkt hintereinander stattfinden. In der Dormanz-Ruhephase macht dieser
Mechanismus keinen Sinn — es gibt keine naechste stressige Aktivitaet, die blockiert werden muss.

**Empfehlung:** `recovery_days_default: 0` (Recovery-Konzept entfaltet in der Dormanz keine
Wirkung; der Wert 7 fuehrt nur zu irrerefuehrender Plan-Ausgabe wenn Dormanz-Aktivitaeten
geplant werden).

---

### E-003: `Hardening Off` — `estimated_duration_minutes: 10` zu gering
**Aktivitaet:** `Hardening Off` (sort_order: 50)
**Problem:** Abharten ist ein Prozess der 7-10 Tage dauert (laut Beschreibung). Ein
einmaliger Zeitaufwand von 10 Minuten entspricht der Zeit fuer ein einzelnes Aus-/Hereintragen.
Wenn das Feld als "Zeit pro einzelner Abhartungs-Session" interpretiert wird, ist 10 Minuten
korrekt. Wenn es als Gesamtdauer der Massnahme interpretiert wird, ist es voellig unzureichend.
Der semantische Kontext des Felds in der Datenbank ist unklar.

**Empfehlung:** Entweder die Semantik des Felds als "Zeit pro Einzelsession" klarstellen, oder
auf `estimated_duration_minutes: 15` (realistische Einzelsession inkl. Weg) anpassen und
eine Wiederholungsangabe (`repeat_daily: 7-10 days`) im Modell ermoeglichen.

---

### E-004: `Celeriac Side Root Removal` — `recovery_days_default: 3` zu hoch
**Aktivitaet:** `Celeriac Side Root Removal` (sort_order: 52)
**Problem:** Das Abschneiden von Seitenwurzeln an der Knollenoberflaeche ist eine routinemaessige,
stressarme Massnahme (`stress_level: "low"`) — vergleichbar mit Nagelschneiden. Die Knolle
erleidet minimalen physiologischen Stress. Ein Recovery-Wert von 3 Tagen uebertreibt den Effekt;
realistisch ist 1 Tag (Wundverschluss der feinen Seitenwurzeln).

**Empfehlung:** `recovery_days_default: 1`

---

## Grun — Fehlende Aktivitaeten

### M-001: Cannabis — `Schwerkraftbiegen` (Gravity Bending) fehlt
**Anbaukontext:** Indoor, Growzelt
**Beschreibung:** Zweige in einem Winkel von 90-135 Grad gegen die Schwerkraft absenken und
fixieren, ohne den Stangel zu beschadigen. Kombiniert Elemente von LST und Supercropping;
geringerer Stress als volles Supercropping. Weit verbreitet als Alternative zu Supercropping
bei Patienten mit begrenzter Erfahrung.
**Fehlende Kategorie:** `training_lst` oder `training_hst` (je nach Intensitaet)
**Erwartete Parameter:** `stress_level: "low"`, `skill_level: "intermediate"`,
`recovery_days_default: 2`, `species_compatible: ["Cannabis"]`

---

### M-002: Cannabis — `Trichomkontrolle` (Trichome Inspection) fehlt
**Anbaukontext:** Indoor, Growbox
**Beschreibung:** Beurteilung des Trichomreifegrad unter der Lupe (40-100x) zur
Erntezeitpunkt-Bestimmung: milchig-weisse Trichome (unreif), opak-milchig (Ernte-Optimum),
bernsteinfarben (ueberreif, erhoehter CBN-Anteil). Kritisches Entscheidungswerkzeug;
von keiner anderen Aktivitaet abgedeckt.
**Fehlende Kategorie:** `harvest_prep`
**Erwartete Parameter:** `stress_level: "none"`, `skill_level: "intermediate"`,
`recovery_days_default: 0`, `tools_required: ["jewellers loupe 40x", "digital microscope"]`

---

### M-003: Allgemein — `Stielen / Anbinden` (Generic Staking) fehlt
**Anbaukontext:** Outdoor, Gewachshaus, Indoor
**Beschreibung:** Generische Stutzung schwacher Triebe oder junger Jungpflanzen mit
Bambusstabchen und Pflanzenbindern. Relevant fuer alle Arten die `requires_support: true` haben
(Tomaten, Paprika, Gladiolen, Rosen, Delphinien). Unterscheidet sich von den artspezifischen
`Dahlia Staking` und `Sunflower Staking`.
**Fehlende Kategorie:** `training_lst`
**Erwartete Parameter:** `stress_level: "none"`, `skill_level: "beginner"`,
`recovery_days_default: 0`, `requires_support: true`,
`tools_required: ["bamboo stake", "plant ties"]`
**Warum fehlend:** Mit `requires_support: true` wuerde dieser Eintrag nur fuer Arten ausgegeben
die Support benoetigen — das ist das korrekte Nutzungsmuster fuer dieses Filterfeld.

---

### M-004: Zimmerpflanzen — `Substratauflockerung` (Substrate Aeration) fehlt
**Anbaukontext:** Indoor, Zimmerpflanzen
**Beschreibung:** Vorsichtiges Aufstechen des Substrats mit einem Holzstab oder duennen Stab
(4-6 Stiche tief), um verdichtetes Substrat aufzulockern und die Sauerstoffversorgung der
Wurzelzone zu verbessern. Besonders wichtig bei Torfsubstraten die nach mehrmaligem Giessen
hydrophob werden (Wasser laeuft seitlich am Substrat vorbei). Vermeidet die Notwendigkeit
eines Umtopfens. Regelmaessige Massnahme fuer Monstera, Ficus, Spathiphyllum.
**Fehlende Kategorie:** `general`
**Erwartete Parameter:** `stress_level: "low"`, `skill_level: "beginner"`,
`recovery_days_default: 0`, `applicable_growth_habits: ["herb", "shrub", "vine"]`,
`requires_container: true`

---

### M-005: Geophyten — `Mulchen` (Mulching) fehlt
**Anbaukontext:** Outdoor
**Beschreibung:** Aufbringen einer 5-10 cm dicken Schicht organischen Materials (Rindenmulch,
Stroh, Kompost) um Dahlia- und Tigridia-Pflanzstellen zum Frostschutz und Feuchtigkeitserhalt.
Mulch isoliert den Boden und verzoegert Bodenfrost — relevant fuer Dahlien in milder
Klimazone (USDA Zone 8+), wo ein Einlagern optional ist. Schutzt ausserdem die entstehenden
Knollen vor Austrocknung im Sommer.
**Fehlende Kategorie:** `general`
**Erwartete Parameter:** `stress_level: "none"`, `skill_level: "beginner"`,
`recovery_days_default: 0`, `species_compatible: ["Dahlia", "Tigridia"]`,
`tools_required: ["bark mulch", "straw", "trowel"]`

---

### M-006: Erdbeere — `Stroh unterlegen` (Strawberry Straw Mulching) fehlt
**Anbaukontext:** Outdoor
**Beschreibung:** Einlegen von Stroh oder Holzchips unter Erdbeerfruchte vor dem Reifen,
um Bodenkontakt und damit Botrytis-Befall der Fruchte zu verhindern. Gleichzeitig Isolierung
des Bodens gegen Austrocknung und Unkrautunterdruckung. Zentrales Element im integrierten
Erdbeeranbau (IPM). Biologisch: Fruchtbedeckung durch Stroh reduziert Botrytis-Infektion
um 40-60% in Freilandversuchen.
**Fehlende Kategorie:** `general`
**Erwartete Parameter:** `stress_level: "none"`, `skill_level: "beginner"`,
`recovery_days_default: 0`, `species_compatible: ["Fragaria", "Erdbeere"]`,
`forbidden_phases: ["germination", "dormancy", "seedling"]`,
`tools_required: ["straw", "mulching material"]`

---

### M-007: Sellerie — `Knollen abdecken` (Celeriac Blanching, optionale Variante) fehlt
**Anbaukontext:** Outdoor
**Beschreibung:** Lockeres Abdecken des freiliegenden Knollenoberteils mit Papier,
Zeitungspapier oder Vlies im Spaetsommer, um die Knollenoberflaeche vor UV-Bestrahlung
zu schutzen und Vergrunung zu verhindern. Anders als bei Kartoffeln (wo Gruen Solanin
bedeutet) gruent Sellerie ohne Qualitatsminderung, aber die Oberflaechenbeschaffenheit
wird besser handelsklassengerecht. Praxis bei kommerziellem Anbau.
**Hinweis:** Diese Massnahme ist nicht bei allen Sellerie-Anbauern etabliert und kann als
optionale Erweiterung betrachtet werden. Niedrige Prioritaet.
**Fehlende Kategorie:** `general`

---

### M-008: Cannabis Indoor — `CO2-Monitoring und Anpassung` fehlt
**Anbaukontext:** Indoor, Growbox, Gewachshaus
**Beschreibung:** Uberprufen und Anpassen der CO2-Konzentration im Anbaubereich.
Umgebungsluft enthalt ca. 400 ppm CO2; Cannabis-Pflanzen photosynthetisieren effizienter
bei 800-1200 ppm (bei ausreichend PPFD > 600 µmol/m²/s). Aktive CO2-Anreicherung erhoht
Trockengewichtszuwachs um 20-40%. Massnahme beinhaltet: CO2-Meter kalibrieren, Messung
zum Hoechststand (mittags), Anpassung der Zufuhr oder Ventilation.
**Fehlende Kategorie:** `general`
**Erwartete Parameter:** `stress_level: "none"`, `skill_level: "intermediate"`,
`recovery_days_default: 0`, `species_compatible: ["Cannabis"]`,
`tools_required: ["CO2 meter", "CO2 source"]`

---

## Systemische Beobachtungen: Engine-Logik

### O-001: Recovery-Calendar teilt HST-Aktivitaeten korrekt, aber LST-Slot nicht
**Engine:** `activity_plan_engine.py`, Zeile 215-230
Die Engine gruppiert `training_hst`-Aktivitaeten in einen gemeinsamen Recovery-Slot
(`recovery_group = "hst"`), sodass Topping, FIM und Mainlining nicht am selben Tag geplant
werden. LST-Aktivitaeten erhalten jedoch eigene Slots pro Kategorie (`cat_training_lst`).
Biologisch korrekt: LST verursacht keinen Wundheilungsstress, daher ist kein Recovery
notwendig und mehrere LST-Aktivitaeten am selben Tag sind physiologisch moglich
(z.B. SCROG-Aufbau + erste Pflanzenfuhrung gleichzeitig).

**Bewertung:** Korrekt. Kein Aenderungsbedarf.

---

### O-002: Skill-Gate im Engine — `advanced`-Aktivitaeten werden bei `skill_level=None` nicht gefiltert
**Engine:** `activity_plan_engine.py`, Zeile 67
```python
skill_max = _SKILL_RANK.get(skill_level or "", 999)
```
Wenn `skill_level` nicht gesetzt ist (None), wird `skill_max = 999`, was alle Aktivitaeten
inklusive `advanced`-Level erlaubt. Das ist eine bewusste Design-Entscheidung (kein Filter ohne
expliziten Skill-Level), aber nicht in der Dokumentation erwaehnt. Ein Nutzer ohne
Profil-Konfiguration erhaelt damit automatisch Aktivitaeten wie `Mainlining` und `FIM`
vorgeschlagen, die fuer Anfanger nicht geeignet sind.

**Empfehlung:** Den `skill_level`-Default auf `"intermediate"` setzen oder eine Warnung in der
Planausgabe ergaenzen, wenn `skill_level` nicht gesetzt wurde.

---

### O-003: Phase `"budding"` und `"sprouting"` — Verwendung in activities.yaml, aber nicht in REQ-003
**Problem:** Die Phase `"budding"` wird in 3 Aktivitaeten als `forbidden_phases`-Eintrag
verwendet (`Topping`, `FIM`, `Dahlia Disbudding`). `"sprouting"` kommt in 4 Aktivitaeten vor
(`Dahlia Disbudding`, `Tuber Division`, `Tuber Lifting`, `Corm Separation`).
REQ-003 v2.3 definiert die Standardphasen als:
`germination → seedling → vegetative → flowering → harvest`
Beide Phasennamen (`budding`, `sprouting`) sind artspezifische Erweiterungen, nicht im Standard
definierten Kernphasen. Wenn diese Phasen in der `growth_phases`-Collection fuer bestimmte
Arten nicht angelegt werden, bleiben die Forbidden-Phase-Sperren wirkungslos — der Engine
prueft nur auf exakte Uebereinstimmung des Phasennamens.

**Empfehlung:** `"budding"` und `"sprouting"` in der Phase-Dokumentation und im Seed-Data
fuer Cannabis und Geophyten explizit definieren. Alternativ die Phasennamen aus
`forbidden_phases` der Aktivitaeten entfernen und durch etablierte Phasennamen ersetzen.

---

### O-004: Kategoriesystem fehlt `"inspection"` und `"monitoring"` als eigene Kategorien
**Problem:** Aktivitaeten wie `Tuber Inspection` (sort_order: 30) und die fehlende
`Trichomkontrolle` (M-002) werden der Kategorie `"general"` zugeordnet. Im Engine-Code
hat `"general"` den niedrigsten `_CATEGORY_PRIORITY`-Wert (6) und den niedrigsten
`_CATEGORY_DEFAULT_OFFSETS`-Wert (1), was Monitoring-Aktivitaeten kurz nach Phasenbeginn
einplant — biologisch sinnvoll fuer routinemaessige Inspektionen.

Das fehlende `"monitoring"` oder `"inspection"` als separate Kategorie verhindert jedoch
eine sinnvolle Filterung und Priorisierung auf der UI-Seite (z.B. "zeige mir nur
Inspektions-Aufgaben").

**Empfehlung:** Kategorie `"inspection"` in `ActivityCategory`-Enum ergaenzen und fuer
`Tuber Inspection`, `Bromeliad Cup Filling` (als Monitoring-Variante) und zukuenftige
Monitoring-Aktivitaeten verwenden.

---

## Zusammenfassung: Priorisierter Korrekturbedarf

### Kritisch (Fehlfunktion des Systems)

| ID | Aktivitaet | Problem | Aktion |
|----|------------|---------|--------|
| F-001 | Mainlining | `budding` fehlt in `forbidden_phases` | `forbidden_phases` anpassen |
| F-002 | Heavy Defoliation | `flowering` verboten, aber primaere Anwendungszeit (Ref. K-001) | Phase-Logik korrigieren |
| F-003 | Lollipopping | `late_flower` fehlt in `restricted_sub_phases` (Ref. B-004) | `restricted_sub_phases` erganzen |
| F-004 | Repotting | `flowering`-Verbot blockiert Zimmerpflanzen-Pflege (Ref. F-003) | Phase-Logik korrigieren |
| F-005 | Petunia Pinching | `flowering`-Verbot macht Aktivitaet wertlos (Ref. F-001) | Phase-Logik korrigieren |

### Hoch (Qualitaetsminderung)

| ID | Problem | Aktion |
|----|---------|--------|
| S-001 | `applicable_growth_habits` fuer universelle Aktivitaeten fehlt | Felder befuellen |
| S-002 | `applicable_families` komplett ungenutzt | Zunaechst fuer `Ausgeizen`, `Runner Removal`, Bromelien befuellen |
| O-002 | Skill-Level-Default erlaubt `advanced`-Aktivitaeten ohne Profil | Default auf `intermediate` setzen |
| O-003 | `budding`/`sprouting` als Phasennamen undokumentiert | In Phase-Seed-Daten definieren |
| M-003 | Generische `Staking`-Aktivitaet fehlt | Neue Aktivitaet mit `requires_support: true` |

### Mittel (Praezisierungsbedarf)

| ID | Problem | Aktion |
|----|---------|--------|
| S-004 | `recovery_days_by_species` fuer Sellerie, Bonsai fehlt | Werte ergaenzen |
| E-001 | `Lollipopping` recovery_days zu gering | `7` default, `10` cannabis |
| E-002 | `Tuber Division` recovery_days konzeptuell falsch | `0` setzen |
| E-003 | `Hardening Off` duration semantisch unklar | Semantik dokumentieren |
| E-004 | `Celeriac Side Root Removal` recovery_days zu hoch | `1` setzen |
| O-004 | Kategorie `"inspection"` fehlt | Enum erganzen |

### Niedrig (Erweiterungen)

| ID | Fehlende Aktivitaet | Prioritaet | Begruendung |
|----|---------------------|------------|-------------|
| M-001 | Cannabis Gravity Bending | Mittel | Haeufige Praxis, LST-Variante |
| M-002 | Cannabis Trichomkontrolle | Hoch | Kritisch fuer Erntezeitpunkt |
| M-004 | Substratauflockerung (Zimmerpflanzen) | Mittel | Haeufige Notwendigkeit bei Torf |
| M-005 | Mulchen Geophyten | Niedrig | Freiland-Winterschutz |
| M-006 | Stroh unterlegen Erdbeere | Mittel | IPM-Standardmassnahme Botrytis |
| M-007 | Sellerie Knollenabdecken | Niedrig | Optional, kommerziell relevant |
| M-008 | CO2-Monitoring Cannabis | Mittel | Relevant fuer Indoor-Profis |

---

## Referenz: Vorgaenger-Reviews

Folgende Befunde aus Vorgaenger-Reviews sind noch offen und sollten parallel bearbeitet werden:

| Review | ID | Problem | Status |
|--------|----|---------|--------|
| `agrobiology-review-activity-descriptions-2026-03.md` | K-001 | Heavy Defoliation flowering-Widerspruch | Offen |
| `agrobiology-review-activity-descriptions-2026-03.md` | K-002 | Celeriac Anatomie (Hypokotyl) | Offen |
| `agrobiology-review-activity-descriptions-2026-03.md` | B-001 | Cloning: Auxinrezeptoren vs. -konzentration | Offen |
| `agrobiology-review-activity-descriptions-2026-03.md` | B-006 | Bromeliad Trichom-Mechanismus | Offen |
| `agrobiology-review-activity-descriptions-2026-03.md` | I-006 | Spathiphyllum Auxin-Effekt falsch | Offen |
| `agrobiology-review-activity-descriptions-2026-03.md` | P-001/P-002 | LST/SCROG auf Cannabis beschraenkt | Offen |
| `agrobiology-review-activity-plans-2026-03.md` | F-004 | Celeriac Earthing Up: biologisch falsch | Offen |
| `agrobiology-review-activity-plans-2026-03.md` | diverse W-XXX | Werkzeug-Luecken | Offen |

---

## Glossar

- **PPFD** (Photosynthetic Photon Flux Density): Photosynthetisch nutzbare Lichtmenge in
  µmol/m²/s — der korrekte Messwert fuer Pflanzenwachstum (nicht Lux).
- **HST** (High Stress Training): Trainingstechniken mit Gewebeverletzung (Topping, FIM,
  Supercropping). Erfordern Erholungszeit.
- **LST** (Low Stress Training): Techniken ohne Gewebeverletzung (Biegen, Binden, SCROG).
  Keine Erholungszeit notwendig.
- **Apikaldominanz**: Hormoneller Mechanismus bei dem der Haupttrieb durch Auxin-Produktion
  das Wachstum der Seitentriebe hemmt.
- **Auxin** (IAA, Indol-3-Essigsaeure): Phytohormon das polar vom Apex zur Basis transportiert
  wird und Streckungswachstum sowie Apikaldominanz steuert.
- **Cytokinin**: Phytohormon das in aktiven Wurzelspitzen synthetisiert wird und Zellteilung
  sowie Knospenentfaltung foerdert.
- **Geophyt**: Pflanzen mit unterirdischen Ueberdauerungsorganen (Knollen, Zwiebeln, Kormen,
  Rhizome) — z.B. Dahlia (Knolle), Tigridia (Korm), Tulpe (Zwiebel).
- **Monokarp**: Pflanzen die einmalig bluehen und danach absterben — z.B. Guzmania-Rosetten
  (die Mutterpflanze stirbt nach der Blute, lebt durch Kindel weiter).
- **Fenestration**: Die charakteristischen Locher und Schlitze in ausgereiften
  Monstera-Blattern, die durch das Lichtklima im Regenwald evolviert sind.
- **Hemiepiphyt**: Pflanze die beide Lebensstrategie kombiniert — bodenbewohnend als Jungpflanze,
  kletternd als Erwachsenenpflanze (z.B. Monstera deliciosa).
- **recovery_days**: Anzahl Tage nach einer stressreichen Aktivitaet, bevor die naechste
  hochstress-Aktivitaet stattfinden sollte. Im Engine als "Sperrzeit" im Recovery-Calendar
  umgesetzt.
- **IPM** (Integrated Pest Management / Integrierter Pflanzenschutz): Kombinierter
  Ansatz aus biologischen, mechanischen und chemischen Massnahmen zur Schaedlingskontrolle.
