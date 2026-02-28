# Review: Gartenbesitzerin & Gemeinschaftsgarten-Mitglied

**Erstellt von:** Ambitionierte Hobbygärtnerin (Subagent)
**Datum:** 2026-02-27
**Fokus:** Saisonale Beetplanung · Fruchtfolge · Überwinterung mehrjähriger Pflanzen · Gemeinschaftsgarten-Koordination · Ernteoptimierung
**Gärtner-Profil:** 400 m² Hausgarten + 80 m² Gemeinschaftsgarten-Parzelle, ~120 Pflanzen (40 mehrjährig), 15 Jahre Erfahrung

**Analysierte Dokumente:**
- `spec/req/REQ-001_Stammdatenverwaltung.md` bis `spec/req/REQ-026_Aquaponik-Management.md` (26 REQs)
- `spec/nfr/NFR-001_Separation-of-Concerns.md` bis `spec/nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md` (11 NFRs)
- `spec/ui-nfr/UI-NFR-001_Responsive-Design.md` bis `spec/ui-nfr/UI-NFR-013_Einwilligungsmanagement-Consent.md` (13 UI-NFRs)
- `spec/stack.md`

---

## 1. Gesamtbewertung

Kamerplanter ist ein faszinierendes System, das tief in die Pflanzenbiologie einsteigt. Aber ich sage das ganz ehrlich: In der jetzigen Form ist es vor allem ein Indoor-Growing-Werkzeug. Für meinen 400-m²-Garten mit Fruchtfolge, Obstbäumen, Beerensträuchern und dem Gemeinschaftsgarten fehlen die zentralen Outdoor-Planungsfunktionen. Das System kennt VPD und EC-Werte auf zwei Nachkommastellen, aber ob meine Dahlien vor dem ersten Frost ausgegraben werden müssen, weiss es nicht.

| Gartenbereich | Bewertung | Abdeckung |
|---|:---:|---|
| Stammdaten & Taxonomie | 4/5 | Exzellente botanische Grundlage, Lebenszyklus-Typen, Hardiness Zones vorhanden |
| Standortverwaltung & Beete | 3/5 | Outdoor-Beete sind vorgesehen, aber keine visuelle Beetplanung |
| Fruchtfolge & Rotation | 3/5 | 3-5-Jahres-Tracking und Warnungen spezifiziert, aber kein 4-Jahres-Rotationsplaner |
| Voranzucht & Aussaat | 2/5 | Phasensteuerung vorhanden, aber kein Aussaatkalender, keine Frostberechnung |
| Überwinterung | 1/5 | Fast komplett fehlend — Dormanz-Phase existiert, aber kein Winterschutz-Management |
| Mehrjährige Pflanzen & Gehölze | 2/5 | Perennial-Modus und Dormanz-Phasen spezifiziert, aber keine Schnittkalender |
| Gemeinschaftsgarten | 4/5 | Multi-Tenancy mit Parzellenzuweisung, Rollen, Einladungssystem — sehr gut |
| Düngung & Bodenpflege | 2/5 | Hydroponik-fokussiert (EC, Mischsequenz), organische Düngung nur am Rande |
| Schädlinge & Pflanzenschutz | 3/5 | IPM-System solide, Karenzzeiten, Nützlinge — aber zu wenig Freiland-Fokus |
| Ernte & Ertragsdokumentation | 3/5 | Gute Grundlage, aber Yield-per-m² und Sortenvergleich über Jahre fehlen |
| Kalender & Erinnerungen | 3/5 | Kalenderansicht und iCal-Export spezifiziert, aber kein saisonaler Gartenkalender |
| Vermehrung | 4/5 | Umfassend: Stecklinge, Teilung, Veredelung, Ableger — sehr nützlich |

**Gesamtnote: 2,8 / 5** — Das System hat eine brillante technische Grundlage, aber die Outdoor-Garten-Perspektive fehlt in vielen Kernbereichen.

---

## 2. Fehlt komplett — Ohne das kann ich meinen Garten nicht planen

### G-001: Aussaatkalender mit regionaler Frostberechnung

**Schweregrad:** Kritisch
**Betroffene REQs:** REQ-003, REQ-006, REQ-015

Ich brauche einen Aussaatkalender, der mir sagt: "Tomaten-Voranzucht ab 15. Februar, Direktsaat Möhren ab 20. März, Eisheilige 11.-15. Mai." Das System kennt zwar GDD und Phasensteuerung (REQ-003), aber es gibt keinen regionalen Aussaatkalender, der:

- Den letzten Frost / die Eisheiligen berücksichtigt
- Rückwärtsrechnung macht (Tomaten brauchen 8 Wochen Voranzucht → Start am X)
- Zwischen Voranzucht-Indoor und Direktsaat-Outdoor unterscheidet
- Regionale Klimadaten nutzt (USDA-Zone ist vorhanden, aber nicht aktiviert)

**Vorschlag:** Neues Modul "Saisonale Anbauplanung" oder Erweiterung von REQ-015 (Kalenderansicht) um einen Aussaatkalender-Modus. Species-Stammdaten (REQ-001) müssen um `sowing_indoor_weeks_before_last_frost`, `sowing_outdoor_after_last_frost_days` und `frost_sensitivity: Literal['hardy', 'half_hardy', 'tender']` erweitert werden.

### G-002: Überwinterungsmanagement — DAS Killer-Feature für Freilandgärtner

**Schweregrad:** Kritisch
**Betroffene REQs:** REQ-003, REQ-006, REQ-022

In meinem Garten ist die Überwinterung der grösste organisatorische Aufwand des Jahres. Ich muss:

- **Frostempfindliche Pflanzen rechtzeitig schützen** (Vlies, Reisig, Anhäufeln)
- **Kübelpflanzen einräumen** (Oleander, Schmucklilie, Zitrusbäumchen)
- **Knollen/Zwiebeln ausgraben** (Dahlien, Gladiolen, Canna)
- **Im Frühling alles wieder auspacken/einsetzen**

Das System hat zwar eine `dormancy`-Phase (REQ-003) und REQ-022 erwähnt einen "Überwinterungs-Workflow" und "Standort-Check" im Oktober/März, aber es fehlt:

- **Winterhärte-Ampel pro Pflanze** (Grün = winterhart in meiner Zone, Gelb = Schutz nötig, Rot = muss rein)
- **Winterquartier-Verwaltung** (Keller 5°C, Garage 8°C, Fensterbank 15°C)
- **Überwinterungs-Protokoll pro Pflanzentyp** (Rosen: anhäufeln + Vlies; Dahlien: ausgraben, trocknen, einlagern; Feige: Jungpflanzen komplett einpacken)
- **Frost-Warnungen** (Wetteranbindung: "Nachtfrost vorhergesagt! 12 Pflanzen brauchen Schutz")
- **Frühlings-Erinnerungen** (März: "Rosen abhäufeln", April: "Dahlien vorziehen", Mai: "Kübelpflanzen rausstellen")
- **Knollen/Zwiebeln-Zyklus** (Ausgraben-Trocknen-Einlagern-Kontrollieren-Vorziehen-Auspflanzen)

**Vorschlag:** Eigene REQ "Überwinterungsmanagement" oder massive Erweiterung von REQ-022 mit Fokus auf Freiland-Winterschutz. Dies wäre DAS Unterscheidungsmerkmal gegenüber Fryd und anderen Garten-Apps.

### G-003: Visuelle Beetplanung mit Flächenzuordnung

**Schweregrad:** Kritisch
**Betroffene REQs:** REQ-002, REQ-013

REQ-002 definiert Sites → Locations → Slots, und das ist eine solide Hierarchie. Aber was mir fehlt, ist eine **visuelle Beetplanung**:

- Beetflächen als 2D-Grundriss zeichnen (auch grob: Rechteck 3×1,2m)
- Pflanzen auf dem Beet positionieren (Reihen, Abstände)
- Mischkultur-Partner visuell nebeneinander sehen
- Historische Ansicht: "Was stand 2025 auf Beet B3?"
- Fruchtfolge-Rotation visuell planen (Beet durchfärben nach Starkzehrer/Mittelzehrer/etc.)

Das aktuelle Slot-System ist eher für Indoor-Growzelte mit festen Raster-Positionen gedacht. Ein Gartenbeet funktioniert anders — es hat Reihen mit unterschiedlichen Abständen, und ich muss 20 Pflanzen auf 3m² visuell planen.

**Vorschlag:** Erweiterung von REQ-002 um einen "Beetplaner"-Modus mit einfacher 2D-Darstellung. Muss nicht CAD-Level sein, aber Rechtecke mit Pflanzen-Icons und Abstandsanzeige.

### G-004: Systematischer 4-Jahres-Fruchtfolgeplan

**Schweregrad:** Hoch
**Betroffene REQs:** REQ-002, REQ-001

REQ-002 spezifiziert eine "Fruchtfolge-Engine" mit 3-5 Jahren Tracking und Warnungen bei kritischen Wiederholungen. Das ist ein guter Ansatz, aber für meine Praxis fehlt:

- **Explizite Nährstoffbedarfs-Rotation** (Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung)
- **Visuelle Rotationsmatrix** pro Beet über 4 Jahre
- **Vorschläge** was als nächstes in ein Beet kann (basierend auf Familienhistorie UND Nährstoffbedarf)
- **Gründüngung als Fruchtfolge-Glied** (Phacelia, Senf, Lupine — nicht nur als Pflanzung, sondern als Bodenverbesserungs-Phase)
- **Vor-/Nachfrucht-Kompatibilität** (Kartoffeln nach Kohl → schlecht; Bohnen vor Kohl → gut wegen Stickstoff)

REQ-001 hat bereits `nutrient_demand: Literal['heavy', 'medium', 'light']` auf BotanicalFamily, und das Crop-Rotation-System basiert auf Familien-Rotation. Aber es fehlt die **Starkzehrer/Mittelzehrer/Schwachzehrer-Zuordnung** als visuelles Feature und die Gründüngung als 4. Phase.

### G-005: Phänologischer Gartenkalender — "Was ist JETZT zu tun?"

**Schweregrad:** Hoch
**Betroffene REQs:** REQ-015, REQ-006

REQ-015 (Kalenderansicht) aggregiert Tasks und Timeline-Events — das ist technisch sauber. Aber was mir als Gärtnerin fehlt, ist ein **saisonaler 12-Monats-Gartenkalender**, der mir sagt:

- **Januar:** Obstbaum-Schnittplanung, Saatgut bestellen
- **Februar:** Voranzucht Tomaten/Paprika starten, Beerensträucher schneiden
- **März:** Rosen abhäufeln, Kompost ausbringen, Starkzehrer-Beete vorbereiten
- **April:** Direktsaat frostfeste Gemüse, Kartoffeln legen
- **Phänologische Zeiger** (Forsythienblüte = Rosen schneiden, Holunderblüte = Bohnen säen)
- **Regionale Anpassung** basierend auf Klimazone

Das System hat den Task-Mechanismus (REQ-006) und könnte solche Aufgaben automatisch generieren, aber es fehlt das **Gartenkalender-Template** für Freilandgärtner. Die vorhandenen Workflow-Templates sind auf Cannabis, Zimmerpflanzen und Hydroponik fokussiert.

**Vorschlag:** Erweiterung von REQ-006 um Outdoor-Freiland-Templates (Obstbaum-Schnitt, Beetvorbereitung, Gründüngung, Wintervorbereitung) und von REQ-015 um eine "Monatsübersicht"-Ansicht mit saisonalen Empfehlungen.

### G-006: Obstbaum- und Beerensträucher-Verwaltung

**Schweregrad:** Hoch
**Betroffene REQs:** REQ-001, REQ-003, REQ-007

Meine Obstbäume und Beerensträucher sind langfristige Investitionen. Ich brauche:

- **Unterlage dokumentieren** (z.B. "Apfel Elstar auf M9-Unterlage")
- **Befruchter-Zuordnung** (Welcher Apfel befruchtet welchen?)
- **Ertragsbeginn** (Standjahr, wann wird erstmals geerntet?)
- **Alternanz-Tracking** (Jedes zweite Jahr weniger Ertrag)
- **Schnitttermine** (Kernobst: Februar; Steinobst: nach der Ernte; Beerensträucher: sortenabhängig)
- **Beerensträucher differenziert** (Himbeeren: Herbsthimbeeren = komplett bodennah schneiden; Sommerhimbeeren = nur abgetragene Ruten)

REQ-001 hat ein solides Stammdaten-Modell mit Cultivar und Species, aber ohne die Obstbau-spezifischen Felder (Unterlage, Befruchtersorte, Alternanz). REQ-017 (Vermehrungsmanagement) deckt Veredelung ab und prüft sogar Graft-Kompatibilität — das ist super! Aber die laufende Obstbaumpflege (Schnitt, Ertrag über Jahre) fehlt.

---

## 3. Unvollständig — Grundidee stimmt, aber es fehlen Freiland-Details

### G-007: Organische Düngung unterrepräsentiert

**Betroffene REQ:** REQ-004
**Status:** Grundstruktur vorhanden, Fokus falsch

REQ-004 ist ein Meisterwerk der Hydroponik-Düngung — EC-Budget, Mischsequenz, CalMag-vor-Sulfate, Flushing-Strategien. Aber für meinen Garten brauche ich:

- **Kompost-Gaben** dokumentieren (Wie viel, wohin, wann)
- **Brennnesselsud / Beinwell-Jauche** als Dünger-Typ
- **Hornspäne, Hornmehl** mit unterschiedlicher Freisetzungszeit
- **Bokashi** und Effektive Mikroorganismen
- **Starkzehrer/Mittelzehrer-Zuordnung** als Dünge-Empfehlung
- **Bodenanalyse** als Ausgangspunkt (pH des Bodens, nicht der Nährlösung)

REQ-004 hat bereits `is_organic: bool` und `application_method: 'top_dress'` — das ist ein Anfang. Aber die gesamte Kalkulations-Engine (EC-Budget, mixing_priority) ist auf mineralische Flüssigdünger ausgelegt. Für organische Feststoffe brauche ich eher eine **Ausbringungsmenge pro m²** als ml/Liter.

### G-008: Mischkultur nur als Graph-Edges, nicht als Planungswerkzeug

**Betroffene REQ:** REQ-001, REQ-013
**Status:** Daten vorhanden, Feature fehlt

REQ-001 hat `compatible_with` und `incompatible_with`-Edges für Companion Planting. REQ-013 hat `mixed_culture`-Runs mit Rollen (primary, companion, trap_crop). Die Datengrundlage ist da!

Was fehlt: Ein **Mischkultur-Berater**, der mir beim Beetplannen sagt:
- "Tomaten + Basilikum = gute Partner"
- "Tomaten + Fenchel = schlecht"
- "Du hast Möhren geplant — wie wäre es mit Zwiebeln dazwischen?"
- Visuelle Darstellung der Kompatibilitäten auf dem Beet

### G-009: Sukzessive Aussaaten nicht explizit unterstützt

**Betroffene REQ:** REQ-013
**Status:** Indirekt möglich, aber kein dediziertes Feature

Als Freilandgärtnerin säe ich Salat alle 2-3 Wochen, Radieschen alle 2 Wochen, Bohnen in 3 Sätzen. REQ-013 hat `clone_from_run_key` für "Staffelanbau/Succession Planting", was in die richtige Richtung geht. Aber es fehlt:

- Automatische Erinnerung "Nächste Salat-Aussaat in 10 Tagen"
- Überblick: "3 Sätze Buschbohnen geplant, Satz 1 gepflanzt, Satz 2 in 2 Wochen"
- Template: "Salat-Sukzession: alle 3 Wochen von April bis August"

### G-010: Wetter-Integration fehlt komplett

**Betroffene REQ:** REQ-005, REQ-022
**Status:** Nicht spezifiziert

REQ-005 (Hybrid-Sensorik) ist auf Indoor-Sensoren fokussiert (Home Assistant, MQTT). Für den Freilandgarten bräuchte ich:

- **Wettervorhersage-Integration** (OpenWeatherMap, DWD-API)
- **Frost-Warnungen** basierend auf Vorhersage
- **Witterungsangepasste Giesserinnerungen** (Es hat gestern geregnet → Giessen verschieben)
- **Hitzewarnungen** (Über 35°C: Salat schiesst, Mulchen!)

REQ-022 hat saisonale Giessmultiplikatoren, aber keine Wetter-Reaktivität.

---

## 4. Zu komplex / Indoor-lastig — Das brauche ich nicht so

### G-011: EC/pH-Mischsequenz-Kalkulation (REQ-004)

Die gesamte Mischsequenz-Validierung (CalMag vor Sulfate, A+B getrennt mischen, EC-Budget pro Phase) ist für Hydro-Grower essentiell. Für mich als Erde-Gärtnerin ist das irrelevant — ich giesse mit der Giessskanne und werfe Hornspäne aufs Beet. Das REQ-021 Erfahrungsstufen-System blendet das korrekt aus, also ist das gut gelöst.

### G-012: Tank-Management (REQ-014)

Nährstofftanks mit pH-Drift, DO-Monitoring, Rezirkulationstanks, Stammlösungen — das ist reine Hydroponik. Mein "Tank" ist eine 1000L IBC-Regenwassertonne. REQ-014 unterstützt zwar den Typ `reservoir` und `irrigation` (Giesswasser), aber die gesamte Kalkulations-Engine drumherum ist überdimensioniert.

### G-013: Canopy-Management und SCROG (REQ-006)

Training-Events, SCROG-Fill-Percentage, Mainlining — das ist Cannabis-Indoor. Für meinen Garten komplett irrelevant. Aber gut: Es gibt ja die Erfahrungsstufen (REQ-021), die das ausblenden.

### G-014: Post-Harvest Curing und Burping (REQ-008)

Jar-Curing, Burping-Schedule, Trichom-Analyse — klar, Cannabis-Nachbehandlung. Was ich davon bräuchte: Lagerverwaltung für Ernte (Kartoffeln im Keller, Zwiebeln im Netz, Äpfel im Kühllager). Die Grundstruktur von REQ-008 (StorageLocation, StorageCondition, Temperaturzonen) passt dafür, ist aber auf Cannabis/Kräuter-Trocknung fokussiert.

### G-015: Aquaponik (REQ-026)

Fisch-Pflanzen-Kreislaufsysteme, Stickstoffzyklus, Biofilter-Cycling — spannendes Nischenthema, aber für 99% der Freilandgärtner irrelevant. Trotzdem gut, dass es als separates REQ existiert und nicht die Kern-Features überfrachtet.

---

## 5. Gut gelöst — Das hilft mir direkt

### G-016: Multi-Tenancy für Gemeinschaftsgarten (REQ-024)

Exzellent! Die Szenarien in REQ-024 könnten 1:1 aus meinem Alltag in der "Grünen Oase" stammen:
- Parzellen-Zuweisung an Mitglieder
- Gemeinschaftsflächen (Kompost, Gewächshaus) für alle
- Einladungslinks per WhatsApp teilen
- Privater Garten bleibt separat

Die Rollen (Admin/Gärtner/Beobachter) passen perfekt. Einziger Wunsch: Eine **Giessdienst-Rotation** wäre noch das Tüpfelchen auf dem i (wer giesst diese Woche die Gemeinschaftsbeete?).

### G-017: Onboarding-Wizard mit Starter-Kits (REQ-020)

Super Idee! "Balkon-Tomaten" als Starter-Kit, 3 Minuten bis zur ersten Pflanze im System. Die `site_type`-Auswahl (outdoor, balcony, greenhouse, windowsill) spricht auch Freilandgärtner an. Allerdings fehlt ein Starter-Kit "Hausgarten Gemüse" oder "Gemeinschaftsgarten-Parzelle".

### G-018: Erfahrungsstufen-System (REQ-021)

Das ist genau, was das System braucht. Als Fortgeschrittene will ich Fruchtfolge und Mischkultur sehen, aber nicht EC-Budget und SCROG-Fill. Die Navigation-Tiering (Einsteiger: 5 Menüpunkte, Fortgeschrittene: 8, Experte: alle) ist durchdacht. Der "Mehr anzeigen"-Toggle ist elegant.

### G-019: Vermehrungsmanagement (REQ-017)

Für mich sehr nützlich! Stecklingnahme (Buxus, Lavendel, Hortensie), Teilung (Stauden im Herbst), Ableger (Erdbeeren), Absenker (Brombeeren) — alles abgedeckt. Die Phänotyp-Notizen und Erfolgsraten-Tracking pro Vermehrungsmethode helfen mir, meine Technik zu verbessern.

### G-020: Pflegeerinnerungen mit saisonaler Anpassung (REQ-022)

Die Care-Style-Presets (tropical, succulent, orchid etc.) sind für Zimmerpflanzen gedacht, aber der Mechanismus (saisonale Multiplikatoren, adaptive Learning) ist universell nützlich. Die Giessmethoden-Hinweise (Tauchbad für Orchideen, Drench&Drain für Sukkulenten) sind didaktisch wertvoll.

### G-021: iCal-Export (REQ-015)

Meinen Gartenkalender in Thunderbird abonnieren — das ist genau, was ich brauche! Die Farbkodierung pro Kategorie und die Filtermöglichkeiten (nur meine Parzelle im Gemeinschaftsgarten) sind durchdacht.

### G-022: Fachbegriff-Erklärungen (UI-NFR-011)

Endlich eine App, die VPD, EC und NPK erklärt! Das Glossar-System mit mehrstufigen Erklärungen (Kurztext, Langtext, Einsteiger-Tipp) ist genau richtig. Ich kenne NPK vage, aber die Einheit "meq/100g" für Kationenaustauschkapazität hätte ich ohne Tooltip nie verstanden.

### G-023: PWA / Offline-Fähigkeit (UI-NFR-012)

Im Garten habe ich nicht immer gutes Internet. Die Offline-Erfassung mit automatischer Synchronisation ist Gold wert — Erntemengen direkt am Beet eintragen, Schädlingsbefall fotografieren, Giessen bestätigen.

---

## 6. Wunschliste

### G-024: Phänologische Zeiger-Integration

Forsythienblüte = Rosen schneiden. Holunderblüte = Bohnen säen. Apfelblüte = Kartoffeln legen. Das ist traditionelles Gärtnerwissen und viel zuverlässiger als feste Kalenderdaten, weil es das lokale Mikroklima reflektiert.

**Vorschlag:** Optionales Phänologie-Tagebuch — ich dokumentiere "Forsythie blüht heute" und das System leitet daraus regionale Empfehlungen ab.

### G-025: Blühkalender für Bienen/Insekten

Welche meiner Pflanzen blüht wann? Habe ich von März bis Oktober durchgehend Nahrung für Bienen? Blühlücken identifizieren und Vorschläge machen.

### G-026: Saatgut-Verwaltung

Welches Saatgut habe ich noch? Wie alt ist es (Keimfähigkeit nimmt ab)? Was muss ich nachbestellen? REQ-016 (InvenTree) könnte das prinzipiell abdecken, ist aber überdimensioniert. Ein einfaches Saatgut-Inventar wäre nützlicher.

### G-027: Mondkalender (optional)

In REQ-006 als "Future Feature (niedrige Priorität)" erwähnt. Für Anthroposoph-Gärtner relevant, für mich persönlich nice-to-have. Gut, dass es als optional konzipiert ist.

### G-028: Foto-Tagebuch / Garten-Chronik

Ich fotografiere meinen Garten ständig — vorher/nachher, Schädlinge, Ernten, schöne Blüten. Ein Foto-Tagebuch mit Timeline und Pflanzen-Zuordnung wäre toll. REQ-006 hat `photo_refs` auf Tasks, aber keine chronologische Foto-Galerie.

### G-029: Wasserverbrauch-Tracking für Regentonne

Meine IBC-Regenwassertonne (1000L) muss ich im Auge behalten. Wie viel verbrauche ich pro Woche? Wann muss ich auf Leitungswasser umsteigen? REQ-014 hat Tank-Füllstandstracking, aber für die Regentonne fehlt die Verbrauchsprognose.

---

## 7. Feature-Relevanz-Matrix

| REQ | Titel | Relevanz für Outdoor-Garten | Bemerkung |
|-----|-------|:---:|---|
| REQ-001 | Stammdatenverwaltung | 5/5 | Basis aller Planung, botanische Daten exzellent |
| REQ-002 | Standortverwaltung | 4/5 | Outdoor-Beete vorhanden, visuelle Planung fehlt |
| REQ-003 | Phasensteuerung | 3/5 | Perennial-Modus nützlich, aber zu Indoor-fokussiert |
| REQ-004 | Dünge-Logik | 2/5 | Hydroponik-lastig, organische Düngung unterrepräsentiert |
| REQ-005 | Hybrid-Sensorik | 1/5 | Indoor-Sensoren, kein Wetter-API |
| REQ-006 | Aufgabenplanung | 4/5 | Sehr nützlich! Outdoor-Templates fehlen |
| REQ-007 | Erntemanagement | 4/5 | Gute Basis, Ertragsvergleich über Jahre fehlt |
| REQ-008 | Post-Harvest | 2/5 | Lagerverwaltung nützlich, Cannabis-Curing irrelevant |
| REQ-009 | Dashboard | 3/5 | Harvest-Calendar und Task-Queue nützlich |
| REQ-010 | IPM-System | 4/5 | Solide Basis, Schnecken/Blattläuse/Biogarten-Fokus fehlt |
| REQ-011 | Externe Stammdatenanreicherung | 3/5 | Hardiness Zones, Companion Planting — nützlich |
| REQ-012 | Stammdaten-Import | 2/5 | Für Erstbefüllung nützlich |
| REQ-013 | Pflanzdurchlauf | 4/5 | Mischkultur-Runs, Succession Planting — relevant |
| REQ-014 | Tankmanagement | 1/5 | Regentonne wäre nützlich, Rest Hydroponik |
| REQ-015 | Kalenderansicht | 4/5 | iCal-Export super, saisonaler Kalender fehlt |
| REQ-016 | InvenTree-Integration | 1/5 | Overkill für Hobbygärtner |
| REQ-017 | Vermehrungsmanagement | 4/5 | Stecklinge, Teilung, Veredelung — sehr relevant |
| REQ-018 | Umgebungssteuerung | 0/5 | Reine Indoor-Automatisierung |
| REQ-019 | Substratverwaltung | 2/5 | Für Hochbeete/Kübel relevant, Rest Indoor |
| REQ-020 | Onboarding-Wizard | 4/5 | Gut, braucht Outdoor-Starter-Kits |
| REQ-021 | UI-Erfahrungsstufen | 5/5 | Essentiell — blendet Komplexität richtig aus |
| REQ-022 | Pflegeerinnerungen | 4/5 | Guter Mechanismus, braucht Outdoor-Erweiterung |
| REQ-023 | Benutzerverwaltung | 3/5 | Basis für Gemeinschaftsgarten |
| REQ-024 | Mandantenverwaltung | 5/5 | Perfekt für Gemeinschaftsgarten + Privat |
| REQ-025 | Datenschutz / DSGVO | 2/5 | Nötig, aber nicht Alltagsrelevant |
| REQ-026 | Aquaponik | 0/5 | Nischenthema, irrelevant |

---

## 8. Überwinterungs-Checkliste — Was das System pro Pflanzengruppe können müsste

| # | Pflanzengruppe | Beispiele | Winterschutz-Aktion | Frühlings-Aktion | Status im System |
|---|---|---|---|---|---|
| 1 | Frostempfindliche Knollen | Dahlien, Gladiolen, Canna, Begonien | Ausgraben, trocknen, frostfrei einlagern (5-10°C) | Ab April vorziehen, nach Eisheiligen auspflanzen | FEHLT |
| 2 | Frostempfindliche Kübelpflanzen | Oleander, Zitrus, Schmucklilie, Engelstrompete | Ins Winterquartier (5-12°C, hell), wenig giessen | Ab Mai schrittweise abhärten und rausstellen | FEHLT |
| 3 | Bedingt winterharte Stauden | Lavendel, Salbei, Rosmarin, Fuchsien | Wurzelbereich mulchen, Vlies bei Kahlfrost | Ab März Winterschutz entfernen, Rückschnitt | TEILWEISE (Dormanz-Phase) |
| 4 | Rosen | Beet-, Strauch-, Kletterrosen | Anhäufeln (20-30 cm), Vlies bei Kahlfrost, NICHT schneiden | März: abhäufeln, Rückschnitt auf 3-5 Augen | FEHLT |
| 5 | Obstbäume | Apfel, Birne, Kirsche, Pflaume | Stammschutz (Kalkanstrich gegen Frostrisse), Leimringe | Feb/März: Kernobst-Schnitt; Juli/Aug: Steinobst-Schnitt | FEHLT |
| 6 | Beerensträucher | Himbeeren, Johannisbeeren, Stachelbeeren | Winterhart, aber: abgetragene Ruten schneiden | Feb: Schnitt je nach Sorte, Mulchen | FEHLT |
| 7 | Hochbeet-/Balkonkästen | Kräuter, Salate, Blumen | Kästen isolieren (Noppenfolie), immergrüne Bepflanzung | März: Erdtausch/Auffüllung, Neubepflanzung | FEHLT |
| 8 | Wintergemüse | Grünkohl, Feldsalat, Winterpostelein | Vlies bei starkem Frost, sonst draussen lassen | Ernte bis März, dann Beet für Fruchtfolge räumen | FEHLT |
| 9 | Teichpflanzen | Seerosen, Hechtkraut, Schilf | Frostempfindliche Sorten in tiefere Zone senken | Altes Laub entfernen, Düngung ab Mai | FEHLT |
| 10 | Zwiebel-/Knollenpflanzen (winterhart) | Tulpen, Narzissen, Krokusse | Setzen im Oktober, Laub als Schutz | Nicht zu früh aufräumen (Laub einziehen lassen) | FEHLT |

**Fazit:** 9 von 10 Pflanzengruppen haben KEINEN spezifischen Überwinterungs-Support. Das ist für Freilandgärtner in Mitteleuropa ein fundamentales Defizit.

---

## 9. Saisonkalender — Was ich Monat für Monat brauche

| Monat | Garten-Aufgaben | System-Unterstützung benötigt |
|---|---|---|
| **Januar** | Saatgutbestellung planen, Obstbaumschnitt bei frostfreiem Wetter | Saatgut-Inventar, Schnitt-Erinnerung |
| **Februar** | Voranzucht Tomaten/Paprika/Chili, Beerensträucher-Schnitt, Rosen-Winterschutz prüfen | Aussaatkalender, Schnitt-Templates |
| **März** | Rosen abhäufeln, Kompost ausbringen, Kartoffeln vorkeimen, Direktsaat Erbsen/Spinat | Winterschutz-Erinnerungen, Aussaatplan |
| **April** | Direktsaat Möhren/Radieschen, Kartoffeln legen, Staudenteilung, Rasen vertikutieren | Beetplan, Fruchtfolge-Check, Vermehrungs-Tracking |
| **Mai** | Eisheilige beachten! Kübelpflanzen raus, Tomaten pflanzen, Mischkultur anlegen | Frost-Warnung, Abhärtungs-Tracker, Mischkultur-Berater |
| **Juni** | Erdbeerernte, Ausgeizen Tomaten, Sukzessions-Aussaat Salat/Bohnen, Schädlingskontrolle | Ernte-Tracking, Ausgeizen-Erinnerung, IPM-Inspektionen |
| **Juli** | Haupterntezeit! Steinobstschnitt, Ableger Erdbeeren, Bewässerung intensiv | Ernte-Dokumentation, Wasserverbrauch, Vermehrung |
| **August** | Ernte fortsetzen, Herbstaussaat planen, Gründüngung auf leere Beete | Aussaat-Erinnerung, Gründüngungsplanung |
| **September** | Erntedoku abschliessen, Herbstpflanzungen, Knoblauch stecken, Äpfel/Birnen ernten | Ernte-Statistiken, Fruchtfolge-Vorschau |
| **Oktober** | Dahlien ausgraben, Kübelpflanzen einräumen, Beete mulchen, Wintergemüse schützen | WINTERSCHUTZ-MANAGEMENT (G-002) |
| **November** | Rosen anhäufeln, Laub als Winterschutz nutzen, Kompost umsetzen, Werkzeuge pflegen | Überwinterungs-Checkliste, Kompost-Tracking |
| **Dezember** | Gartenruhe, Planung nächstes Jahr, Saatgutkataloge studieren | Jahres-Rückblick, Ertrags-Vergleich, Beetplanung |

**Ergebnis:** Das System deckt aktuell ca. 30% dieser Monatsaufgaben ab (hauptsächlich über REQ-006 Tasks und REQ-022 Pflege-Erinnerungen). Die fehlenden 70% betreffen vor allem Winterschutz, Beetplanung, Aussaatkalender und Obstbaumpflege.

---

## 10. Gemeinschaftsgarten-Anforderungen

| # | Anforderung | Status | Bewertung |
|---|---|---|---|
| 1 | Multi-Tenancy für Gemeinschaftsgarten | REQ-024 | Exzellent |
| 2 | Mehrere Mitglieder mit Rollen | REQ-024 (admin/grower/viewer) | Gut |
| 3 | Parzellenzuweisung | REQ-024 (LocationAssignment) | Gut |
| 4 | Gemeinschaftsflächen vs. Privatparzellen | REQ-024 (keine Zuweisung = Gemeinschaft) | Gut |
| 5 | Einladungssystem | REQ-024 (E-Mail + Link) | Sehr gut |
| 6 | Privater Bereich bleibt privat | REQ-024 (persönlicher Tenant) | Sehr gut |
| 7 | **Aufgabenverteilung / Giessdienst-Rotation** | Nicht spezifiziert | **FEHLT** |
| 8 | **Aktivitäts-Feed / Pinnwand** | Nicht spezifiziert | **FEHLT** |
| 9 | **Gemeinsame Bestellungen** (Saatgut, Dünger) | Nicht spezifiziert | **FEHLT** |
| 10 | **Ernteverteilung** (Wer bekommt wie viel?) | Nicht spezifiziert | **FEHLT** |

**Fazit:** Die Grundinfrastruktur (Multi-Tenancy, Rollen, Parzellen) ist hervorragend. Was fehlt, sind die **kollaborativen Features**: Giessdienst-Rotation, gemeinsame Einkaufsliste, Aktivitäts-Feed ("Max hat die Tomaten gegossen", "Lisa hat 3kg Zucchini geerntet").

### G-030: Giessdienst-Rotation

Im Gemeinschaftsgarten haben wir einen rotierenden Giessdienst — jede Woche ist ein anderes Mitglied für die Gemeinschaftsbeete zuständig. Das System könnte:

- Automatische Wochenplan-Rotation generieren
- Erinnerung an das diensthabende Mitglied
- Tausch-Anfragen ("Kann jemand nächste Woche für mich übernehmen?")
- Erledigung bestätigen (mit Foto)

### G-031: Gemeinschafts-Pinnwand

"Wer hat Mulch übrig?" "Die Schnecken sind dieses Jahr schlimm — bitte Bierfallen aufstellen" "Am Samstag gemeinsames Kompost-Umsetzen" — ein einfacher Nachrichten-Feed innerhalb des Tenants.

---

## 11. Top-5-Massnahmen — Prioritäten für die Outdoor-Erweiterung

| Prio | Massnahme | Aufwand | Wirkung | Betroffene REQs |
|:---:|---|---|---|---|
| **1** | **Überwinterungsmanagement** (G-002) — Winterhärte-Ampel, Winterquartiere, Frost-Erinnerungen, Knollen-Zyklus | Mittel | Sehr hoch — DAS Unterscheidungsmerkmal | Neue REQ oder REQ-022 erweitern |
| **2** | **Aussaatkalender mit Frostberechnung** (G-001) — Regionale Aussaatzeiten, Voranzucht-Rückrechnung, Eisheilige-Warnung | Mittel | Sehr hoch — Kernfunktion für Gemüsegärtner | REQ-015 + REQ-001 erweitern |
| **3** | **Organische Düngung und Bodenpflege** (G-007) — Kompost, Jauche, Hornspäne, Bodenanalyse, Ausbringung pro m² | Mittel | Hoch — betrifft 80% der Freilandgärtner | REQ-004 erweitern |
| **4** | **Saisonaler Gartenkalender** (G-005) — 12-Monats-Aufgabenplan, phänologische Zeiger, Outdoor-Workflow-Templates | Gering-Mittel | Hoch — täglicher Nutzen | REQ-006 + REQ-015 erweitern |
| **5** | **Obstbaum-/Beerensträucher-Verwaltung** (G-006) — Unterlage, Befruchter, Schnittkalender, Ertrags-Tracking | Mittel | Mittel-Hoch — langfristig wertvoll | REQ-001 + REQ-003 erweitern |

**Sekundäre Massnahmen:**
- G-003 (Visuelle Beetplanung) — hoher Aufwand, aber differenzierend
- G-004 (4-Jahres-Fruchtfolgeplan) — Erweiterung des bestehenden Rotationssystems
- G-010 (Wetter-Integration) — transformativ, aber technisch aufwändig
- G-030 (Giessdienst-Rotation) — klein, aber hoher Gemeinschafts-Nutzen
- Outdoor-Starter-Kits für REQ-020 ("Hausgarten-Gemüse", "Kräuterbeet", "Hochbeet-Anfänger")

---

## 12. Wettbewerbsvergleich: Fryd, Gartenplaner.net, Permapeople

| Feature | Kamerplanter (aktuell) | Fryd | Gartenplaner.net | Permapeople |
|---|:---:|:---:|:---:|:---:|
| **Visuelle Beetplanung** | Nein | Ja (Kern-Feature) | Ja (Kern-Feature) | Nein |
| **Aussaatkalender** | Nein | Ja (regional) | Ja (regional) | Nein |
| **Fruchtfolge-Warnung** | Ja (Graph-basiert) | Ja (einfach) | Ja (einfach) | Nein |
| **Mischkultur-Berater** | Daten vorhanden | Ja (visuell) | Ja (Tabelle) | Ja (Kern-Feature) |
| **Überwinterung** | Nein | Nein | Nein | Nein |
| **Gemeinschaftsgarten** | Ja (Multi-Tenant!) | Beta | Nein | Community-Fokus |
| **Pflanzendatenbank** | Ja (erweiterbar via API) | Ja (gross) | Ja (mittel) | Ja (Community) |
| **Phasensteuerung** | Ja (State Machine) | Nein | Nein | Nein |
| **Ernte-Tracking** | Ja (detailliert) | Einfach | Nein | Nein |
| **Erfahrungsstufen** | Ja (3-stufig) | Nein | Nein | Nein |
| **Offline-Fähigkeit** | Ja (PWA geplant) | Nein | Nein | Nein |
| **Kalender-Export (iCal)** | Ja (spezifiziert) | Nein | Nein | Nein |
| **Indoor-Growing** | Ja (Kern-Feature) | Nein | Nein | Nein |
| **IPM / Pflanzenschutz** | Ja (umfassend) | Einfach | Nein | Teilweise |
| **Vermehrung** | Ja (umfassend) | Nein | Nein | Nein |
| **Multi-Sprache** | Ja (DE/EN) | DE/EN/FR+ | DE | EN (Community) |
| **Open Source** | Ja | Nein (SaaS) | Nein (SaaS) | Ja |

### Chancen von Kamerplanter gegenüber der Konkurrenz:

1. **Kein Wettbewerber hat Überwinterungsmanagement** — dies wäre ein echtes Alleinstellungsmerkmal
2. **Multi-Tenancy für Gemeinschaftsgärten** ist deutlich weiter als bei Fryd (Beta) und fehlt bei den anderen komplett
3. **Die Phasensteuerung (REQ-003)** mit Perennial-Modus und Dormanz ist einzigartig und könnte für mehrjährige Pflanzen zum Differenzierungsmerkmal werden
4. **Erfahrungsstufen** lösen das Komplexitätsproblem elegant — kein Wettbewerber hat das
5. **IPM-System** ist professioneller als alles, was Fryd bietet
6. **iCal-Export** und **PWA** sind technische Vorteile, die kein Wettbewerber hat

### Schwächen gegenüber der Konkurrenz:

1. **Keine visuelle Beetplanung** — Fryd und Gartenplaner.net machen das zur Kernfunktion
2. **Kein Aussaatkalender** — das ist Standard bei Garten-Apps
3. **Indoor-Bias** — wer "Kamerplanter" heisst, klingt nicht nach Freiland (Kamerplant = Zimmerpflanze auf Niederländisch)

---

## Zusammenfassung

Kamerplanter hat ein technisch überlegenes Fundament — die Graph-Datenbank für Fruchtfolge und Mischkultur, die Phasensteuerung mit Perennial-Modus, das IPM-System, die Multi-Tenancy. All das ist den Wettbewerbern Fryd und Gartenplaner.net meilenweit voraus.

Aber dieses Fundament wird aktuell primär für Indoor-Growing und Zimmerpflanzen genutzt. Um die grosse Zielgruppe der Freilandgärtner (15 Millionen Gartenbesitzer allein in Deutschland) zu erreichen, braucht es die in diesem Review identifizierten Erweiterungen — allen voran **Überwinterungsmanagement**, **Aussaatkalender** und **saisonale Gartenplanung**.

Die gute Nachricht: Die Architektur ist dafür vorbereitet. Species-Stammdaten können um Winterhärte-Felder erweitert werden, die Task-Engine kann saisonale Workflows generieren, und das Pflegeerinnerungs-System (REQ-022) kann um Outdoor-Pflegetypen ergänzt werden. Es fehlt nicht die technische Basis — es fehlt der Outdoor-Garten-Fokus in der Spezifikation.
