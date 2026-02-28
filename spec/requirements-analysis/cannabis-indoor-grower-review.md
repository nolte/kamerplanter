# Indoor-Cannabis-Grower Praxisreview
**Erstellt von:** Professioneller Indoor-Grower (Subagent)
**Datum:** 2026-02-27
**Fokus:** Growzelt-Workflow · Ertragsoptimierung · Qualitäts-Tracking · Praxistauglichkeit
**Analysierte Dokumente:** REQ-001 bis REQ-025, NFR-001 bis NFR-011, UI-NFR-001 bis UI-NFR-013, GLOSSAR, stack.md
**Grower-Profil:** 120x120cm Zelt, 480W LED (Samsung LM301H), Coco/Perlite 70/30, 500-700g/m2 Zielertrag

---

## Gesamtbewertung: Kann ich damit meinen Grow managen?

| Workflow-Bereich | Abdeckung | Kommentar |
|-----------------|-----------|-----------|
| Keimung -> Ernte Lifecycle | 4/5 | Phasensteuerung (REQ-003) ist solide, GDD-basierte Transitions sind top. Autoflower-spezifische Lichtzyklen (20/4) nicht explizit als Phase-Preset vorhanden. |
| Post-Harvest (Trocknung/Curing) | 5/5 | REQ-008 ist beeindruckend detailliert: Slow-Dry 7-14 Tage, Burping-Schedule mit abnehmender Frequenz, Boveda-Packs, Gewichtsverlust-Tracking. Cannabis-spezifisch ausgearbeitet. |
| Nahrstoff-Mixing Workflow | 5/5 | REQ-004 ist das Herzstuck. Misch-Reihenfolge korrekt (Si -> CalMag -> Base A -> B -> Booster -> pH), EC-Budget mit Basiswasser-Abzug, Runoff-Analyse, Flushing-Protokolle substratspezifisch. Genau so mische ich. |
| Training & Canopy-Management | 3/5 | HST-Validator in REQ-006 kennt Topping/FIM/Supercropping als Aufgaben. SCROG-Netz-Setup, Mainlining-Planung und Canopy-Gleichmaessigkeit fehlen als trackbare Parameter. Kein dediziertes Training-Modul. |
| Umgebungskontrolle (VPD-zentrisch) | 5/5 | REQ-005 + REQ-018 zusammen sind exzellent. VPD mit Blatttemperatur-Korrektur, LED-spezifischer Offset (-1 Grad C), Hysterese-Steuerung, DLI-basierte Lichtsteuerung, CO2-PPFD-Kopplung. Genau die Stellschrauben die zahlen. |
| Pflanzenschutz (IPM) Indoor | 4/5 | REQ-010 ist solide: 3-Tier IPM, Nutzlinge, Karenzeit. Aber: Indoor-spezifische Probleme (Trauermucken als #1, PM auf Buds, Bud Rot) koennte man noch deutlicher als Cannabis-Risikoprofile vorkonfigurieren. |
| Genetik & Pheno-Hunting | 5/5 | REQ-017 ist ein Traum. 12 Vermehrungsmethoden, Stecklingstypen, Bewurzelungsprotokolle, Phanotyp-Notizen, genetische Linie uber Graph-Kanten. Mutterpflanzen-Management mit Health-Score und Retirement. Das fehlt bei GrowDiaries komplett. |
| Ertrag & Qualitats-Tracking | 4/5 | REQ-007 hat Trichom-Mikroskopie, Multi-Location-Sampling, Batch-Tracking mit QR-Codes. REQ-009 spezifiziert g/Watt und g/m2. Aber: Cure-Bewertung ueber Zeit (wie entwickelt sich Geschmack nach 2/4/8 Wochen?) fehlt als strukturiertes Feature. |
| Run-Vergleich & Optimierung | 4/5 | REQ-013 PlantingRun als Gruppierungs-Container ist korrekt konzipiert. REQ-009 Dashboard hat Strain-Vergleich und Yield-Forecasting. Aber: Kein explizites "Side-by-Side Run Comparison" Feature spezifiziert, das denselben Strain unter verschiedenen Bedingungen direkt gegenueberstellt. |
| CanG-Compliance | 2/5 | REQ-024 Multi-Tenancy koennte Anbauvereinigungen abbilden. NFR-011 hat CanG 5-Jahre Aufbewahrungspflicht. Aber: Keine Pflanzenzahl-Warnung (max. 3 bluhende), kein Besitzmenge-Tracking (50g), keine Abgabelimits fur Social Clubs. Das Gesetz wird referenziert aber nicht operativ umgesetzt. |
| Tagliche UX (Schnelligkeit, Workflow) | 4/5 | UI-NFR-011 Kiosk-Modus mit 64px Touch-Targets fur schmutzige Hande ist genial. PWA-Offline (UI-NFR-012) fur den Keller-Grow. Aber: Kein dezidierter "Morning Check" Quick-Flow (pH/EC messen, VPD checken, Pflanzen inspizieren) als Ein-Screen-Workflow. |

**Gesamteinschatzung:** Kamerplanter ist die mit Abstand ambitionierteste Grow-Software-Spezifikation die ich je gesehen habe. Die Nahrstoff-Engine (REQ-004) allein ist besser als alles was GrowDiaries, Jane oder Growy bieten. Post-Harvest ist tatsachlich vollstandig spezifiziert — das hat sonst niemand. Die Genetik-Verwaltung uber den ArangoDB-Graphen ist ein echtes Alleinstellungsmerkmal fur Pheno-Hunter. Was mich als taglichen Nutzer noch storen wurde: CanG-Compliance ist nur Datenaufbewahrung, nicht operative Unterstutzung. Und ein Morning-Check-Dashboard fur den ersten Blick ins Zelt fehlt als dedizierter Workflow.

---

## Fehlt komplett — Ohne das kann ich nicht growen

### ~~G-001: CanG Pflanzenzahl-Tracking und Warnung~~ [ZURÜCKGESTELLT — Nutzer-Eigenverantwortung]
**Was ich als Grower brauche:** Das System muss wissen, wie viele bluhende Pflanzen ich aktuell habe, und mich warnen, wenn ich die gesetzliche Grenze ueberschreite. Seit April 2024 darf ein Privatperson max. 3 bluhende Cannabis-Pflanzen gleichzeitig besitzen (CanG § 3 Abs. 2).
**Welcher Workflow ist betroffen:** Blute, Tracking & Optimierung
**Warum das kritisch ist:** Wenn ich 4 Pflanzen in die Blute schicke, begehe ich eine Ordnungswidrigkeit. Eine Grow-App die "legal anbauen" verspricht MUSS mich davor warnen. Das ist kein Nice-to-Have, das ist Compliance.
**Vorschlag:** Neues Subsystem in REQ-023 oder eigenstandiges REQ: Zahle alle PlantInstances mit `current_phase = flowering` (oder Folge-Phasen bis Ernte) pro Tenant. Bei Phasenubergang zu "Blute" -> Warnung wenn Limit erreicht. Konfigurierbar pro Tenant (3 fur Privat, hoher fur Anbauvereinigung mit Lizenz). Hardblock optional, Softwarning als Default.
> **Entscheidung:** Zurückgestellt — der Nutzer zählt seine Pflanzen selbst. Ggf. in späterem Release als optionales Feature.

### ~~G-002: Besitzmenge-Tracking (50g Limit)~~ [ZURÜCKGESTELLT — Nutzer-Eigenverantwortung]
**Was ich als Grower brauche:** Nach der Ernte muss ich wissen, wie viel getrocknetes Cannabis ich besitze. CanG erlaubt max. 50g zu Hause und 25g unterwegs.
**Welcher Workflow ist betroffen:** Ernte & Post-Harvest, Tracking & Optimierung
**Warum das kritisch ist:** Wenn ich 3 Pflanzen ernte die jeweils 200g bringen, habe ich 600g — 550g uber dem Limit. Ich muss planen, wie ich das legal handhabe (z.B. uber Anbauvereinigung abgeben, falls Mitglied).
**Vorschlag:** Aggregierter Bestand aus allen HarvestBatches mit Status "stored" minus "consumed" (neues Feld). Warnung bei Annaherung an 50g. Optional: Verbrauchs-Tracking (simple Entnahme-Buchung aus Lagerbestand).
> **Entscheidung:** Zurückgestellt — der Nutzer trackt seinen Bestand selbst. Ggf. in späterem Release als optionales Feature.

### G-003: Equipment-Inventar (Licht, Lufter, Zelt, Messgerate)
**Was ich als Grower brauche:** Ich will mein Setup dokumentieren: Welche Lampe (480W, Samsung LM301H), welcher Lufter (6" AC Infinity), welches Zelt (120x120x200). Ohne das kann ich g/Watt nicht sinnvoll berechnen und Runs nicht vergleichen.
**Welcher Workflow ist betroffen:** Umgebungskontrolle, Tracking & Optimierung
**Warum das kritisch ist:** g/Watt ist DIE Effizienzmetrik. Wenn das System meine Lampen-Wattage nicht kennt, kann es g/Watt nicht berechnen. REQ-009 spezifiziert g/Watt als Dashboard-KPI, aber es gibt kein Equipment-Modell das die Watt-Zahl liefert.
**Vorschlag:** Neues Domain-Modell `Equipment` mit Typ (light/fan/tent/sensor/filter), Spezifikationen (Watt, Durchmesser, Volumen), Zuordnung zu Location/Slot. Muss nicht komplex sein — ein einfaches Inventar reicht, Hauptsache die Lampen-Wattage ist im System.

---

## Unvollstandig — Funktioniert, aber mir fehlt etwas Wichtiges

### ~~G-004: Training-Methoden nicht als dediziertes Modul (REQ-003/REQ-006)~~ [BEHOBEN — REQ-006 v2.6]
**Vorhandene Anforderung:** `REQ-006` (Aufgabenplanung) definiert den HST-Validator der Topping/FIM/Supercropping in bestimmten Phasen verbietet. `REQ-003` hat Stress-Phasen.
**Was fehlt aus Praxis-Sicht:** Ein dediziertes Training-Tracking mit:
- SCROG-Netz als Equipment-Typ mit Netz-Hohe und Fullgrad als messbare Parameter
- Mainlining-Plan: "Node 3 toppen, dann symmetrisch aufbauen" als Workflow-Template
- Canopy-Gleichmaessigkeit als Score (Differenz hochster/niedrigster Trieb in cm)
- Recovery-Timer nach HST (zeige an: "2 Tage seit Topping, noch 1-3 Tage Erholungsphase")
- Autoflower-Warnung: "Topping nicht empfohlen bei Autoflower" automatisch basierend auf Cultivar-Typ
**Typisches Szenario:** Ich toppe am Tag 21, will LST ab Tag 25 planen und SCROG-Netz in Woche 5 einsetzen. Das ist ein zusammenhangender Trainingsplan, kein loser Haufen Einzeltasks.
**Erganzungsvorschlag:** Neues Subsystem "Training Plan" in REQ-006 oder als Erweiterung: Vordefinierte Training-Strategien (LST-Only, Top+SCROG, Mainlining, SOG) als Templates, Canopy-Height als trackbarer Messwert in REQ-005.

### ~~G-005: Feeding-Chart-Import fehlt (REQ-004/REQ-012)~~ [BEHOBEN — REQ-012]
**Vorhandene Anforderung:** `REQ-012` (Stammdaten-Import) hat CSV/JSON-Import fur Pflanzen. `REQ-004` hat NutrientPlan mit Phase-Entries und Fertilizer-Zuordnung.
**Was fehlt aus Praxis-Sicht:** Kein Import von Hersteller-Feeding-Charts. Canna Coco, BioBizz, Advanced Nutrients, Athena Pro Line, GHE/Terra Aquatica — jeder dieser Hersteller hat einen wochenbasierten Dungeplan den Tausende Grower nutzen. Diese manuell abtippen ist unzumutbar.
**Typisches Szenario:** Ich kaufe Canna Coco A+B, CalMag, PK 13-14 und will den offiziellen Canna-Schedule als Startpunkt. Dann passe ich an: "75% der Herstellerangabe in Woche 1-2, 100% ab Woche 3".
**Erganzungsvorschlag:** Import-Schnittstelle fur NutrientPlans aus CSV/JSON mit Spalten: Woche, Phase, Produkt-Name, Dosierung (ml/L), Ziel-EC, Ziel-pH. Community-Templates als Seed-Daten (die 5 meistgenutzten Charts vorinstallieren).

### G-006: Cure-Bewertung uber Zeit fehlt (REQ-008)
**Vorhandene Anforderung:** `REQ-008` hat Curing-Protokoll mit Burping-Schedule und Boveda-Packs. Alles korrekt.
**Was fehlt aus Praxis-Sicht:** Es gibt keine strukturierte Bewertung die dokumentiert, wie sich Geschmack und Qualitat uber die Cure-Dauer entwickeln. Jeder erfahrene Grower weiss: Nach 2 Wochen schmeckt es okay, nach 4 Wochen gut, nach 8 Wochen grossartig.
**Typisches Szenario:** Ich cure meinen White Widow Pheno #3. Nach 2 Wochen probiere ich: "noch etwas chlorophyll-lastig, zitrus kommt durch". Nach 4 Wochen: "deutlich besser, Terpen-Profil entwickelt sich". Nach 8 Wochen: "perfekt, nussig-zitrus, glatter Rauch". Diese Progression will ich dokumentieren und uber Strains vergleichen.
**Erganzungsvorschlag:** Neues Sub-Modell `CureAssessment` am HarvestBatch: cure_week (int), aroma_notes (text), smoothness_score (1-5), overall_score (1-5), tasting_notes (text). Timeline-View im Frontend.

### G-007: Strom-/Kostenrechnung fehlt komplett
**Vorhandene Anforderung:** `REQ-009` (Dashboard) spezifiziert "Kosten pro Gramm" und "Energieverbrauch" als Dashboard-Widgets.
**Was fehlt aus Praxis-Sicht:** Es gibt kein Datenmodell fur Stromverbrauch und Kosten. Die Dashboard-KPIs konnen nicht berechnet werden ohne Eingabedaten. Ein 480W LED lauft 18h/Tag in Veg (8.64 kWh/Tag) und 12h in Blute (5.76 kWh/Tag) — uber einen 4-Monats-Zyklus sind das 150-200 Euro Strom.
**Typisches Szenario:** Ich will nach dem Run wissen: 180 Euro Strom + 40 Euro Nahrstoffe + 15 Euro Substrat = 235 Euro Gesamtkosten / 480g Ertrag = 0.49 Euro/Gramm.
**Erganzungsvorschlag:** Minimales Kosten-Modell: Equipment-Wattage (siehe G-003) x Betriebsstunden (aus Phasen-Historie) x Strompreis (Einstellung) = Stromkosten. Plus: manuelle Kostenbuchungen fur Verbrauchsmaterial. Berechnung automatisch aus vorhandenen Daten.

### G-008: VPD-Chart/Referenztabelle in der App (REQ-009)
**Vorhandene Anforderung:** `REQ-009` spezifiziert einen VPD-Calculator als Dashboard-Widget. `REQ-005` misst VPD.
**Was fehlt aus Praxis-Sicht:** Kein visuelles VPD-Chart (die klassische Farb-Matrix mit Temperatur auf X-Achse, rH auf Y-Achse, VPD als Farbcode). Das ist DAS Referenz-Tool fur jeden Grower — PulseGrow und Vivosun-App haben das, es ist der Grund warum viele Leute diese Apps uberhaupt installieren.
**Typisches Szenario:** Mein Hygrometer zeigt 26 Grad C und 55% rH. Ich schaue auf das VPD-Chart und sehe sofort: gruner Bereich fur Blute, perfekt. Oder: roter Bereich, ich muss den Befeuchter hochdrehen.
**Erganzungsvorschlag:** Interaktives VPD-Chart als permanentes Dashboard-Widget. Farb-Zonen konfigurierbar (Keimling/Veg/Blute). Aktueller Messwert als Punkt auf dem Chart. Optional: Blatttemperatur-Korrektur-Toggle (Air-VPD vs. Leaf-VPD).

### ~~G-009: Autoflower vs. Photoperiodisch als Cultivar-Eigenschaft~~ [BEHOBEN — REQ-001 + REQ-003]
**Vorhandene Anforderung:** `REQ-001` (Stammdaten) hat Cultivar-Modell mit `flowering_type` (nicht explizit vorhanden). `REQ-003` hat Phase-Transitions aber ohne Autoflower-spezifische Logik.
**Was fehlt aus Praxis-Sicht:** Autoflower brauchen komplett andere Handhabung: kein 12/12-Flip (bluten automatisch nach 3-4 Wochen), 20/4 oder 18/6 Licht durchgehend, kein Topping empfohlen (zu wenig Erholungszeit), kurzerer Zyklus (60-90 Tage total), geringerer Ertrag aber schnellere Rotation. Das muss als Systemeigenschaft abgebildet sein.
**Typisches Szenario:** Ich lege einen Run mit "Mephisto Genetics - Forgotten Strawberries" an (Autoflower). Das System sollte automatisch: 20/4 Licht vorschlagen, Topping-Warnung anzeigen, kurzere Phasendauern setzen, keinen manuellen Flip-Trigger anbieten.
**Erganzungsvorschlag:** Feld `photoperiod_type: Literal['photoperiodic', 'autoflower', 'day_neutral']` am Cultivar. Phase-Transition-Rules autoflower-spezifisch: keine manuelle Blute-Einleitung, zeitbasierte automatische Blute nach N Tagen. Training-Einschrankungen: Warnung bei HST fur Autoflower.

### ~~G-010: Hermaphrodismus-Erkennung und Dokumentation~~ [BEHOBEN — REQ-010]
**Vorhandene Anforderung:** `REQ-007` hat Trichom-Mikroskopie und Ernte-Indikatoren, aber keine Hermie-Erkennung.
**Was fehlt aus Praxis-Sicht:** Hermaphrodismus (Nanners/Pollensacke) ist einer der grossten Angste jedes Cannabis-Growers. Eine einzige Hermie kann den ganzen Run bestauben und die Ernte ruinieren. Das muss als Befund in der IPM-Inspektion dokumentierbar sein mit Sofortmassnahmen.
**Typisches Szenario:** Woche 5 Blute: Ich entdecke eine gelbe "Banane" (Nanner) in einer Cola. Sofortmassnahme: Pflanze isolieren oder entfernen, restliche Pflanzen auf Bestaubung prufen. Dokumentation: Welcher Phano, bei welchem Stresslevel (Lichtleck? Hitze?), genetische Disposition notieren fur kunftige Runs.
**Erganzungsvorschlag:** Neuer Befund-Typ `hermaphroditism` in REQ-010 IPM, mit Subtypen (nanners, pollen_sacs, mixed). Schweregrad (isolated, spreading, critical). Verknupfung zu Stress-Events (Lichtleck, Hitzestress, Training-Stress). Genetische Markierung am Cultivar/Phenotyp: "hermie_prone = true" nach Befall.

---

## Praxis-fern — Funktioniert theoretisch, aber so nutzt das keiner

### G-011: GDD-basierte Phasenubergange fur Indoor-Cannabis
**Anforderung:** REQ-003 bietet `gdd_based` als Trigger-Typ fur Phasenubergange. "Growing Degree Days — biologisch akkurater als Kalendertage."
**Praxis-Problem:** Indoor-Cannabis wachst bei konstanter Temperatur (24-26 Grad C Tag, 18-20 Grad C Nacht). GDD akkumuliert bei konstantem Klima vollig linear — es ist identisch mit Kalendertagen, nur komplizierter zu verstehen. GDD ist relevant fur Outdoor/Gewachshaus mit schwankenden Temperaturen, aber im kontrollierten Growzelt nutzlos.
**Wie Grower es wirklich machen:** Indoor-Cannabis-Grower zahlen Wochen seit Keimung (Veg) bzw. Wochen seit Flip (Blute). "Meine White Widow ist in Woche 7 der Blute, noch 1-2 Wochen." Das ist der universelle Standard in jeder Grow-Community.
**Vorschlag:** GDD als Option belassen (fur Outdoor/Gewachshaus sinnvoll), aber fur Indoor-Cannabis "Wochen seit Phasenbeginn" als primares Display-Format anbieten. Autoflower: "Tag X von ~75" als Fortschrittsbalken.

### G-012: Phasenname "Seneszenz" statt "Ripen/Flush"
**Anforderung:** REQ-003 Phasensequenz: "Keimung -> Samling -> Vegetativ -> Blute -> Fruchtreife -> Seneszenz"
**Praxis-Problem:** Kein Cannabis-Grower sagt "Seneszenz". Die letzte Phase vor der Ernte heisst "Ripen" oder "Flush" oder "Late Flower". "Fruchtreife" ist botanisch korrekt fur Tomaten, aber Cannabis hat keine Fruchte — die "Reife" bezieht sich auf Trichom-Entwicklung.
**Wie Grower es wirklich machen:** Blute wird unterteilt in: Stretch (Woche 1-3), Bulk/Swell (Woche 3-6), Ripen (Woche 7+), Optional Flush (letzte 1-2 Wochen).
**Vorschlag:** Erlaube spezies-spezifische Phasen-Aliase. Cannabis: Stretch -> Bulk -> Ripen -> Flush (optional) -> Harvest. Das generische Modell bleibt, aber die Anzeige nutzt Cannabis-ubliche Begriffe. REQ-003 unterstutzt das prinzipiell uber frei definierbare Phasen, aber es fehlen Cannabis-spezifische Presets.

### ~~G-013: Foliar-Feeding-Warnung in Blute (REQ-004)~~ [BEHOBEN — REQ-004]
**Anforderung:** REQ-004 erwahnt `foliar` als Applikationsmethode neben Fertigation, Drench und Top Dress.
**Praxis-Problem:** Die Spezifikation erwahnt Foliar korrekt, aber es fehlt eine automatische Warnung: "Kein Foliar-Feeding auf Buds in der Blute!" Das ist eine der haufigsten Anfangerfehler — Blattdungung in der Blute fuhrt zu Schimmel auf den Buds und Geschmacksverunreinigung.
**Wie Grower es wirklich machen:** Foliar nur in Veg und maximal fruher Blute (Woche 1). Ab Woche 2 der Blute NIE auf die Pflanze spruhen. Ausnahme: Kaliumbicarbonat gegen PM als Notfallbehandlung.
**Vorschlag:** Phase-basierte Warnung in REQ-004: Wenn Applikationsmethode = foliar UND aktuelle Phase = flowering (ab Woche 2) -> Warnung anzeigen. Kein Hardblock (Notfallbehandlung muss moglich sein), aber deutliche Warnung.

---

## Gut gelost — Das brauche ich genau so

### REQ-004: Nahrstoff-Engine mit Misch-Reihenfolge
Die Misch-Reihenfolge (Silizium -> CalMag -> Base A -> Base B -> Booster -> pH) ist exakt korrekt und wird uber `mixing_priority` flexibel gesteuert. EC-Budget-Management mit Basiswasser-Abzug ist praxisgerecht. Die Unterscheidung von Applikationsmethoden (Fertigation/Drench/Foliar/Top-Dress) mit `tank_safe`-Flag ist vorbildlich — organische Dunger in den Tank kippen ist ein haufiger Fehler den das System verhindert. Die substratspezifischen EC-Bereiche (Hydro: 1.4-2.4, Coco: 1.2-1.8, Soil: 0.8-1.4) stimmen genau. Flushing als optional mit Referenz zur Guelph-Studie ist ehrlich und wissenschaftlich korrekt.

### REQ-008: Post-Harvest mit Trocknungs- und Curing-Protokoll
Endlich eine Grow-Software die Post-Harvest ernst nimmt. Slow-Dry 7-14 Tage bei 15-21 Grad C und 45-55% rH ist korrekt. Burping-Schedule mit abnehmender Frequenz (2x taglich -> 1x taglich -> wochentlich) ist genau so wie ich es mache. Boveda 62% als Ziel-rH. Gewichtsverlust-Tracking (75-80%). Die Abdeckung verschiedener Spezies (Cannabis, Chili, Pilze, Tabak, Sauerkraut) zeigt, dass das System nicht nur Cannabis kann, aber Cannabis die Premium-Abdeckung hat.

### REQ-017: Vermehrungsmanagement und Genetik-Graph
Die 12 Vermehrungsmethoden decken alles ab: Stecklinge (8 Typen!), Samen, Veredlung, Teilung. Bewurzelungsprotokolle mit Hormon-Typ, Medium, Temperatur und Bewurzelungsdauer. Mutterpflanzen-Management mit Health-Score, Recovery-Time nach Stecklingsnahme und Retirement-Kriterien. Der genetische Lineage-Graph uber ArangoDB-Kanten (`descended_from`) ist das Feature das Kamerplanter von jeder anderen Grow-Software unterscheidet. Pheno-Hunting wird damit erstmals softwaregestutzt moglich: Seeds -> nummerierte Phanos -> Selektion -> Mutterpflanze aus bester Genetik.

### REQ-007: Trichom-basierte Ernte-Indikatoren
Multi-Location-Sampling (Calyxen, nicht Zuckerblattern!) ist korrekt und zeigt echtes Domain-Wissen. Die drei Stadien (klar/milchig/bernstein) mit prozentualer Verteilung und Nutzer-Praferenz (energetisch vs. sedierend) ermoglichen personalisierte Ernte-Entscheidungen. Pistil-Verfarbung als sekundarer Indikator. Dark Period und Fruh-Morgens-Ernte als Optionen. Partial Harvest (Top-Buds zuerst, Lower-Buds 7-10 Tage spater) — genau so mache ich das.

### REQ-005 + REQ-018: Sensor-Aktor-Regelkreis mit VPD-Focus
VPD als ubergeordneter Regelkreis statt isolierter Temperatur/Luftfeuchte-Steuerung ist die richtige Architektur-Entscheidung. Blatttemperatur-Offset pro Lichttyp (LED: -1 Grad C, HPS: -3 Grad C) zeigt Verstandnis fur reale Grow-Setups. Hysterese mit Mindestlaufzeit/Mindestpause verhindert Aktor-Oszillation. DLI-basierte Lichtsteuerung ist PPFD-Zeitprogrammen uberlegen. CO2-PPFD-Kopplung (CO2 nur sinnvoll uber 800 umol) ist wissenschaftlich korrekt. Home-Assistant-Integration mit Graceful Degradation zu manuellen Tasks — perfekt fur den Hobbygrower der schrittweise automatisiert.

### REQ-010: IPM mit Karenzeit-Gate
Der 3-Tier-Ansatz (Pravention -> Monitoring -> Intervention) ist korrekt. Nutzlinge mit Ausbringungsrate pro m2 und Etablierungszeit. Die Karenz-Gate-API die eine Ernte blockiert wenn die Sicherheitsintervalle nicht eingehalten sind — das ist nicht nur smart, das ist lebensnotwendig bei Cannabis das geraucht wird. Resistenz-Manager mit max. 3 aufeinanderfolgenden gleichen Wirkstoffen in 90 Tagen verhindert Resistenzbildung.

### UI-NFR-011: Kiosk-Modus fur Growzelt
64x64px Touch-Targets fur schmutzige Hande/Handschuhe, vereinfachte Navigation (max 2 Ebenen), High-Contrast-Theme, Auto-Timeout. Das ist exakt der Use-Case den ich habe: Ich stehe im Zelt mit nassen Coco-Fingern und will schnell den pH-Wert einer Messung eintragen. Genial.

### UI-NFR-012: PWA mit Offline-Fahigkeit
IndexedDB fur Offline-Dateneingabe mit Background-Sync. Mein Growzelt steht im Keller — da ist WLAN-Empfang nicht garantiert. Offline messen, Werte eintragen, synchronisieren wenn ich wieder oben bin. Essentiell.

---

## Wunschliste — Nice-to-Have fur Power-User

### W-001: Community-Templates fur Nahrstoffplane
Moglichkeit, bewahrte NutrientPlans als Community-Templates zu teilen (ahnlich wie Growers Network Feeding Charts). "Canna Coco Classic — bewiesen uber 20 Runs" als One-Click-Import.

### W-002: Trichom-Foto-Integration
Smartphone-Kamera + Clip-Mikroscope (60-120x) Foto direkt in die Harvest-Observation einbetten. Bildvergleich uber Tage hinweg: "Tag 55 vs. Tag 60 vs. Tag 65 — Bernstein-Anteil steigt." Optional: Computer Vision fur automatische Clear/Milky/Amber-Erkennung (REQ-007 erwahnt CV als optional — das ware die Killer-Feature-Implementierung).

### W-003: LED-PPFD-Map pro Zelt
Nicht jeder Punkt im Zelt bekommt gleich viel Licht. Eck-Pflanzen bekommen weniger als Mitte-Pflanzen. Ein PPFD-Grid (3x3 oder 5x5 Messpunkte) pro Location das die Lichtverteilung dokumentiert. Hilft bei Platz-Optimierung und erklart Ertragsdifferenzen innerhalb eines Runs.

### W-004: Smoke Report / Consumption Notes
Optionales Freitext-Modul nach dem Cure fur die Endprodukt-Bewertung: Effekt (relaxed/euphoric/creative/sleepy), Dauer, Geschmack, Geruch, Smoothness, Potency (subjektiv 1-10). Nicht wissenschaftlich, aber exakt das was jeder Grower auf GrowDiaries postet.

### W-005: Sorten-Empfehlung basierend auf Setup
"Dein Zelt ist 120x120, 480W LED, Coco. Diese Sorten haben bei ahnlichen Setups die besten Ergebnisse gebracht:" — Machine-Learning-Feature fur die Zukunft, aber das Datenmodell (Equipment + Run-History + Ertrag) muss jetzt schon stimmen damit es spater moglich ist.

### ~~W-006: Timer/Countdown-Integration~~ [BEHOBEN — REQ-006 v2.5]
Einfache Timer: "Nahrloesung mischen: CalMag 2 Minuten umruehren, dann Base A dazu." Oder: "Foliar-Spray: 30 Minuten vor Licht-Aus." Oder: "Burping-Reminder: Glaser offnen, 15 Minuten Timer." Klingt trivial, aber im Growzelt verliert man das Zeitgefuhl.

### ~~W-007: Ernte-Fenster-Vorhersage~~ [BEHOBEN — REQ-007 v2.3]
Basierend auf Sorte, Phase-Historie und Trichom-Beobachtungen: "Geschatztes Erntefenster: Tag 62-68 (4-10 Tage)." Die Daten sind alle da (REQ-003 Phase-Historie, REQ-007 Trichom-Observations, REQ-001 Cultivar-Blutezeit), die Logik muss sie nur kombinieren.

---

## Workflow-Coverage-Matrix

| Taglicher Workflow | REQ(s) | Abdeckung | Fehlend |
|-------------------|--------|-----------|---------|
| Morgen-Check (pH/EC messen, Pflanzen inspizieren) | REQ-005, REQ-010, REQ-022 | ⚠️ | Kein dedizierter "Morning Check" One-Screen-Flow. Daten konnen erfasst werden (Manual Mode REQ-005, Inspektion REQ-010, Care Reminder REQ-022), aber kein aggregierter Quick-View. |
| Nahrloesung mischen (EC/pH Target, Produkte dosieren) | REQ-004, REQ-014 | ✅ | NutrientSolutionCalculator berechnet Dosierungen, MixingSafetyValidator pruft Reihenfolge. Tank-Integration vorhanden. Feeding-Chart-Import fehlt (G-005). |
| Giessen/Fertigation (Runoff messen, dokumentieren) | REQ-004, REQ-005 | ✅ | FeedingEvent dokumentiert Applikation mit Runoff-EC/pH. RunoffAnalyzer erkennt Salzakkumulation. |
| Environment checken (VPD, Temp, rH, PPFD) | REQ-005, REQ-009 | ✅ | Hybrid-Sensorik mit 3 Modi. VPD-Calculator im Dashboard. VPD-Chart als Referenz fehlt (G-008). |
| IPM-Inspektion (Blattunterseiten, Gelbtafeln) | REQ-010 | ✅ | Vollstandiges Inspektions-System mit Pressure-Level, Foto-Referenzen. Nutzlinge und Karenzeit. Hermie-Erkennung fehlt (G-010). |
| Training (Binden, Entblattern, Netz-Check) | REQ-006 | ⚠️ | HST als Tasks planbar, aber kein Training-Plan-Modul. Kein Canopy-Height-Tracking. Kein SCROG-Management (G-004). |
| Trichom-Check (ab Woche 6 Blute, taglich) | REQ-007 | ✅ | Multi-Location-Sampling, Clear/Milky/Amber-Prozent. Foto-Integration als Wunsch (W-002). |
| Ernte (Schneiden, Trimmen, Aufhangen) | REQ-007 | ✅ | Partial/Final Harvest, Batch-Tracking, QR-Codes. Wet/Dry-Trim als Methode. Trim-Gewicht vs. Bud-Gewicht dokumentierbar. |
| Trocknung (Temp/rH loggen, Branch-Snap-Test) | REQ-008 | ✅ | Slow-Dry-Protokoll mit Umgebungskontrolle. Gewichtsverlust-Tracking. Snap-Test als Checkpoint. |
| Curing (Burpen, rH kontrollieren, Bewertung) | REQ-008 | ⚠️ | Burping-Schedule und Boveda sind da. Cure-Bewertung uber Zeit fehlt (G-006). |
| Run abschliessen (Ertrag, Qualitat, Lessons Learned) | REQ-013, REQ-007, REQ-009 | ⚠️ | PlantingRun hat Status-Machine bis "completed". Yield-Metriken vorhanden. Side-by-Side-Run-Vergleich nicht explizit spezifiziert. |

---

## Ertrags-Relevanz-Matrix

| Anforderung | Ertrags-Einfluss | Qualitats-Einfluss | Prioritat fur Grower |
|------------|-----------------|--------------------|--------------------|
| VPD-Steuerung (REQ-005/018) | Hoch (+10-20%) | Hoch (Schimmelpravention) | P1 |
| Nahrstoffplan (REQ-004) | Hoch (+15-25%) | Mittel (Geschmack bei richtigem Flush) | P1 |
| Training-Tracking (REQ-006) | Hoch (+30-50% vs. untrainiert) | Niedrig | P1 |
| Trichom-Timing (REQ-007) | Niedrig | Sehr hoch (THC/CBN-Ratio) | P1 |
| Post-Harvest Cure (REQ-008) | Niedrig | Sehr hoch (Terpen-Erhalt) | P1 |
| Pheno-Hunting (REQ-017) | Mittel (langfristig +20-30%) | Hoch (langfristig) | P2 |
| Run-Vergleich (REQ-013/009) | Mittel (Lerneffekt) | Mittel (Lerneffekt) | P2 |
| CanG-Compliance (fehlt!) | Keiner | Keiner | P1 (rechtlich!) |
| Equipment-Inventar (fehlt!) | Indirekt (g/Watt-Berechnung) | Keiner | P2 |
| CO2-Supplementierung (REQ-018) | Mittel (+10-30% bei >800 umol) | Niedrig | P3 |
| Kiosk-Modus (UI-NFR-011) | Keiner | Keiner | P2 (Workflow-Effizienz) |
| Offline-PWA (UI-NFR-012) | Keiner | Keiner | P2 (Datenerfassung) |

---

## Empfohlene Datenquellen

| Bereich | Quelle | Relevanz |
|---------|--------|----------|
| Strain-Datenbank | Seedfinder.eu | Genetik, Blutezeit, Ertrag, Breeder-Info |
| Nahrstoff-Charts | Canna.com, BioBizz.com, Athena Ag | Feeding-Schedules fur Import |
| VPD-Referenz | PulseGrow VPD Chart | Zielwerte pro Phase, visuelles Chart-Vorbild |
| Anbaurecht DE | CanG (BGBl. 2024 I Nr. 109) | Pflanzenzahl, Besitzmenge, Abgabelimits |
| IPM Cannabis | Koppert.com, BioBest.com | Nutzlinge fur Indoor, Ausbringungsraten |
| Trichom-Referenz | GrowWeedEasy.com Trichome Guide | Mikro-Fotos der Stadien fur Referenz-Bilder |
| Stecklinge/Klone | Royal Queen Seeds Clone Guide | Bewurzelungsprotokolle, Erfolgskriterien |
| Substrat-Spezifika | Coco for Cannabis (cocoforcannabis.com) | CalMag-Pufferung, DTW-Frequenz, EC-Management |

---

## Glossar — So spricht der Grower

- **Flip:** Umstellung der Photoperiode von 18/6 auf 12/12 -> Bluteinleitung
- **Stretch:** Wachstumsschub in den ersten 2-3 Wochen nach dem Flip (50-200% Hohenzuwachs)
- **Topping:** Abschneiden des Haupttriebs uber einem Node -> zwei neue Haupttriebe
- **FIM (Fuck I Missed):** Unvollstandiges Topping -> 3-4+ neue Triebe
- **LST:** Low Stress Training — Biegen und Fixieren von Trieben fur gleichmassige Canopy
- **SCROG:** Screen of Green — horizontales Netz, durch das Triebe gewebt werden
- **Lollipopping:** Entfernen der unteren Triebe/Blatter (unteres 1/3) fur Canopy-Fokus
- **Defoliation:** Strategisches Entfernen grosser Facherblattern fur Licht-/Luftdurchdringung
- **Mainlining:** Symmetrische Aufteilung in gleich starke Triebe ab der 3. Node
- **Supercropping:** Kontrolliertes Knicken eines Triebs -> Hormon-Response -> starkeres Wachstum
- **Nanners/Bananas:** Mannliche Pollen-Staubblattern an weiblicher Pflanze (Hermaphrodismus-Zeichen)
- **Hermie:** Hermaphroditische Pflanze — entwickelt mannliche und weibliche Bluten
- **Cola:** Blutenstand — Haupt-Cola (Topbud) + Seiten-Colas
- **Calyx:** Einzelnes Blutenhullblatt — Trichome auf Calyxen sind der Ernte-Indikator
- **Trichom:** Harzdrise — enthalt Cannabinoide und Terpene
- **Boveda/Integra:** Zwei-Wege-Feuchtigkeitsregler (62% rH) fur Curing-Glaser
- **Burping:** Offnen der Cure-Glaser zum Gasaustausch
- **DTW:** Drain-to-Waste — Giessmethode bei der uberschussige Nahrlosung abfliesst
- **Runoff:** Ablaufende Nahrlosung nach dem Giessen — EC/pH des Runoffs = Substrat-Feedback
- **Pheno/Phanotyp:** Individuelle Auspragung einer Genetik — jeder Seed kann anders wachsen
- **Mutterpflanze:** Pflanze die dauerhaft in Veg gehalten wird zur Stecklingsgewinnung
- **Steckling/Clone:** Genetisch identische Kopie der Mutterpflanze
- **CanG:** Cannabis-Gesetz (Deutschland) — regelt legalen Eigenanbau seit April 2024
- **DLI:** Daily Light Integral — Gesamtlichtmenge pro Tag in mol/m2/d
- **VPD:** Vapor Pressure Deficit — Differenz zwischen Sattigungs- und tatsachlichem Dampfdruck, zentrale Steuerungsgrosse
- **EC:** Electrical Conductivity — Nahrstoffkonzentration in mS/cm
- **PPFD:** Photosynthetic Photon Flux Density — Lichtintensitat in umol/m2/s
- **CalMag:** Calcium-Magnesium-Erganzung, essentiell bei Coco-Substrat

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Abgeschlossen
**Letzte Aktualisierung**: 2026-02-27
**Review**: Abgeschlossen
**Erstellt durch**: Cannabis Indoor Grower Reviewer Agent
