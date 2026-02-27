# Agrarbiologisches Anforderungsreview: REQ-022 Pflegeerinnerungen

**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-02-27
**Aktualisiert:** 2026-02-27 (F-003 als behoben markiert nach Konsistenz-Korrektur)
**Fokus:** Zimmerpflanzen, Indoor-Anbau, Pflegeintervall-Biologie
**Analysiertes Dokument:** `spec/req/REQ-022_Pflegeerinnerungen.md` (v1.0)
**Kontext-Dokumente:** REQ-001, REQ-003, REQ-006, REQ-020

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Fachliche Korrektheit | 4/5 | Biologische Begruendungen sind ueberwiegend korrekt; wenige aber relevante Fehler bei Detailwerten |
| Indoor-Vollstaendigkeit | 3/5 | Gute Basis, aber wichtige Zimmerpflanzen-Kategorien fehlen im Preset-System |
| Zimmerpflanzen-Abdeckung | 3/5 | 6 Presets decken die haeufigsten, aber nicht alle relevanten Pflegemuster ab |
| Messbarkeit der Parameter | 4/5 | Intervalle sind klar quantifiziert; saisonale Logik sinnvoll definiert |
| Praktische Umsetzbarkeit | 4/5 | Technisch solide; Adaptive Learning hat ein konzeptionelles Risiko |
| Biologische Sicherheit | 3/5 | Adaptive Learning und fehlende Saisonanpassung beim Giessen koennen zu Pflanzenschaeden fuehren |

**Gesamteinschaetzung:** REQ-022 ist eine durchdachte Spezifikation, die das komplexe Thema Zimmerpflanzenpflege auf ein benutzerfreundliches Erinnerungssystem reduziert. Die biologischen Begruendungen sind groesstenteils korrekt und zeigen echtes Domaenenwissen. Es gibt jedoch zwei kritische Luecken: (1) Die festen Giessintervalle ignorieren den dominanten Einfluss von Jahreszeit, Substrat und Topfgroesse auf den tatsaechlichen Wasserbedarf. (2) Das Adaptive Learning hat keine Untergrenze, die biologisch sichere Mindest-Giessfrequenzen garantiert. ~~(3) Die DORMANCY_PHASES sind nicht mit den in REQ-020 definierten Zimmerpflanzen-Phasen abgeglichen.~~ **(3) BEHOBEN:** DORMANCY_PHASES in REQ-022 enthaelt jetzt `maintenance`, `acclimatization`, `repotting_recovery`. Zusaetzlich wurde REQ-003 PhaseType um die Zimmerpflanzen-Phasen erweitert.

---

## 1. Bewertung der care_style-Presets

### 1.1 Tropical (Monstera, Philodendron, Ficus)

| Parameter | Preset-Wert | Agrobiologische Bewertung |
|-----------|-------------|---------------------------|
| Giessen | 7 Tage | Problematisch als Festwert -- siehe F-001 |
| Duengen | 14 Tage (Maer-Okt) | Korrekt fuer Fluessigduenger in halber Konzentration; bei voller Konzentration waere monatlich ausreichend |
| Umtopfen | 18 Monate | Akzeptabel; schnellwuechsige Arten (Monstera, Philodendron) benoetigen teils jaehrliches Umtopfen |
| Schaedlingskontrolle | 14 Tage | Korrekt |

**Biologische Korrektheit der Begruendung:** Die Beschreibung "gleichmaessig feuchte Waelder" ist korrekt fuer die meisten tropischen Folienpflanzen. Die Erlaeuterung zu Salzakkumulation im Winter ist fachlich exzellent.

**Fehlende Differenzierung:** Die Kategorie "tropical" umfasst ein extrem breites Spektrum. Eine Monstera deliciosa (Halbepiphyt mit dicken Luftwurzeln) hat grundlegend andere Wasserspeicherkapazitaet als ein Ficus lyrata (terrestrisch, duennere Wurzeln) oder ein Spathiphyllum (Sumpfpflanze, hoher Wasserbedarf). Ein 7-Tage-Intervall ist fuer Spathiphyllum zu lang und fuer eine grosse Monstera im Winter zu kurz bemessen (zu haeufig).

### 1.2 Succulent (Echeveria, Haworthia, Aloe)

| Parameter | Preset-Wert | Agrobiologische Bewertung |
|-----------|-------------|---------------------------|
| Giessen | 14 Tage | Im Sommer korrekt; im Winter deutlich zu haeufig (21-30 Tage waeren angemessen) |
| Duengen | 30 Tage (Apr-Sep) | Korrekt; Sukkulenten sind Schwachzehrer |
| Umtopfen | 24 Monate | Korrekt; langsames Wurzelwachstum |
| Schaedlingskontrolle | 21 Tage | Akzeptabel; Wollaeuse sind Hauptproblem, entwickeln sich langsam |

**Biologische Korrektheit der Begruendung:** Der Verweis auf CAM-Metabolismus (Crassulacean Acid Metabolism) ist korrekt und zeigt Fachkenntnis. Allerdings ist CAM nicht bei allen Sukkulenten vorhanden -- Aloe und Haworthia nutzen teils C3-Photosynthese. Die Begruendung ist daher leicht uebergeneralisiert, aber die Pflegeempfehlung (laengere Trockenperioden) ist dennoch korrekt.

**Problem:** 14 Tage Giessintervall im Winter ist zu haeufig. Bei niedrigen Temperaturen (15-18 Grad C typisch in Wohnungen am Fensterbrett) und reduzierter Lichtmenge verlangsamt sich der Stoffwechsel erheblich. Wurzelfaeule durch Ueberwaaesserung im Winter ist die haeufigste Todesursache bei Sukkulenten.

### 1.3 Orchid (Phalaenopsis, Dendrobium)

| Parameter | Preset-Wert | Agrobiologische Bewertung |
|-----------|-------------|---------------------------|
| Giessen | 7 Tage (Tauchbad) | Korrekt fuer Phalaenopsis; Dendrobium nobile braucht weniger in der Ruhephase |
| Duengen | 14 Tage (Maer-Okt) | Haeufigkeit korrekt, aber Orchideenduenger (geringes NPK, z.B. 3-3-3) sollte erwaehnt werden |
| Umtopfen | 24 Monate | Korrekt; Substratabbau (Rindenmulch) bestimmt den Zeitpunkt |
| Schaedlingskontrolle | 14 Tage | Korrekt; Schildlaeuse und Wollaeuse sind Hauptprobleme |

**Biologische Korrektheit der Begruendung:** Velamen-Wurzeln und zyklisches Durchnaessen/Abtrocknen -- fachlich exzellent beschrieben. Tauchbad-Methode als Standard ist korrekt.

**Fehlend:** Dendrobium nobile (zweitpopulaerste Orchideen-Gattung im Handel) benoetigt eine kuehle, trockene Ruhephase (November-Februar, 10-15 Grad C, kaum giessen) fuer die Bluetenbildung. Das 7-Tage-Intervall wuerde diese Ruhephase konterkarieren. Der Duenge-Guard fuer Dormanz muesste hier greifen, aber der Phasen-Name muesste in DORMANCY_PHASES enthalten sein.

### 1.4 Calathea (Calathea, Maranta, Ctenanthe)

| Parameter | Preset-Wert | Agrobiologische Bewertung |
|-----------|-------------|---------------------------|
| Giessen | 5 Tage | Korrekt; Calatheen sind extrem austrocknungsempfindlich |
| Duengen | 14 Tage (Maer-Sep) | Korrekt; Schwachzehrer, empfindlich gegen Ueberdüngung. September-Ende ist sinnvoll |
| Umtopfen | 12 Monate | Etwas haeufig; 18 Monate waere realistischer (langsames Wurzelwachstum) |
| Schaedlingskontrolle | 7 Tage | Korrekt und sehr wichtig -- Spinnmilben sind bei Calatheen das Hauptproblem |

**Biologische Korrektheit der Begruendung:** Unterwuchspflanzen tropischer Regenwaelder, Spinnmilben bei trockener Heizungsluft -- fachlich korrekt und praxisrelevant. Die kuerzeren Schaedlingskontroll-Intervalle sind agrobiologisch begruendet.

**Ergaenzung noetig:** Calatheen sind extrem kalkempfindlich. Ein Hinweis auf Regenwasser/entkalktes Wasser fehlt. Dies koennte als `notes`-Default im Preset hinterlegt werden.

### 1.5 Herb (Basilikum, Minze, Rosmarin)

| Parameter | Preset-Wert | Agrobiologische Bewertung |
|-----------|-------------|---------------------------|
| Giessen | 3 Tage | Fuer Basilikum und Minze korrekt; fuer Rosmarin, Thymian, Salbei FALSCH -- siehe F-002 |
| Duengen | 21 Tage (Maer-Okt) | Korrekt fuer die meisten Kuechenkraeuter |
| Umtopfen | 12 Monate | Fuer mehrjaehrige Kraeuter korrekt; Basilikum ist einjaerig (kein Umtopfen noetig) |
| Schaedlingskontrolle | 14 Tage | Korrekt; Blattlaeuse und Weisse Fliege sind typische Probleme |

**Kritischer Fehler:** Die Kategorie "herb" fasst zwei fundamental verschiedene Pflegegruppen zusammen:
- **Feuchtigkeitsliebende Kraeuter** (Basilikum, Minze, Petersilie, Schnittlauch): 3 Tage korrekt
- **Mediterrane Kraeuter** (Rosmarin, Thymian, Salbei, Oregano, Lavendel): Benoetigen 7-10 Tage Giessintervall, durchlaessiges mineralisches Substrat, volle Sonne. 3 Tage wuerde zu Wurzelfaeule fuehren.

### 1.6 Cactus (Kakteen, Lithops)

| Parameter | Preset-Wert | Agrobiologische Bewertung |
|-----------|-------------|---------------------------|
| Giessen | 21 Tage | Im Sommer korrekt; im Winter sind 30-45 Tage angemessen, manche Kakteen werden gar nicht gegossen |
| Duengen | 30 Tage (Mai-Aug) | Korrekt; kurze Aktivphase, Schwachzehrer |
| Umtopfen | 36 Monate | Korrekt; langsames Wachstum |
| Schaedlingskontrolle | 30 Tage | Korrekt; Wollaeuse und Schildlaeuse, langsame Entwicklung |

**Biologische Korrektheit:** Die Aktivmonate Mai-Aug sind korrekt fuer Kakteen -- kuerzeste Duengesaison aller Presets.

**Problem:** Lithops (Lebende Steine) werden hier mit Standard-Kakteen zusammengefasst, haben aber einen voellig anderen Giesszyklus: In der Hautungsphase (Fruehling) duerfen sie UEBERHAUPT NICHT gegossen werden. 21-Tage-Intervall waere in dieser Phase toedlich. Lithops sollten entweder ein eigenes Preset bekommen oder aus der Beispielliste entfernt werden.

---

## 2. Bewertung der Default-Intervalle: Saisonale Differenzierung

### Problem: Feste Giessintervalle ignorieren Saisonalitaet

Dies ist das gravierendste biologische Problem der gesamten Spezifikation. Alle Presets definieren einen einzigen `watering_interval_days`-Wert, der ganzjaehrig gilt. In der Realitaet schwankt der Wasserbedarf von Zimmerpflanzen zwischen Sommer und Winter um den Faktor 1,5 bis 3:

| Pflanzenkategorie | Sommer-Intervall | Winter-Intervall | Faktor |
|-------------------|-----------------|-----------------|--------|
| Tropical | 5-7 Tage | 10-14 Tage | 2x |
| Succulent | 10-14 Tage | 21-45 Tage | 2-3x |
| Cactus | 14-21 Tage | 30-60 Tage (oder gar nicht) | 2-3x |
| Calathea | 4-5 Tage | 7-10 Tage | 1,5-2x |
| Herb | 2-3 Tage | 5-7 Tage | 2x |
| Orchid | 5-7 Tage | 10-14 Tage | 2x |

**Biologische Begruendung:** Im Winter sinkt der Wasserbedarf durch drei simultan wirkende Faktoren:
1. **Reduzierte Lichtmenge** (bis zu 80% weniger als im Sommer) verlangsamt die Photosynthese und damit die Transpiration
2. **Kuerzere Tage** (8h vs. 16h) halbieren die Photoperiode
3. **Heizungsluft** trocknet das Substrat zwar schneller aus, aber die Pflanzenwurzeln nehmen bei reduziertem Stoffwechsel weniger Wasser auf -- das Substrat trocknet oberhalb, bleibt aber im Wurzelbereich nass (Faeulanisrisiko)

Die Spezifikation loest dieses Problem derzeit nur ueber Adaptive Learning, was 3+ Zyklen dauert und den Nutzer im ersten Winter mit falschen Intervallen allein laesst.

---

## 3. Bewertung des Duenge-Guards

### 3.1 Aktivmonate

| Preset | Aktivmonate | Bewertung |
|--------|-------------|-----------|
| tropical | Maer-Okt (3-10) | Korrekt |
| succulent | Apr-Sep (4-9) | Korrekt |
| orchid | Maer-Okt (3-10) | Korrekt, aber Dendrobium sollte kuerzere Saison haben |
| calathea | Maer-Sep (3-9) | Korrekt; Ende September ist sinnvoll wegen hoher Empfindlichkeit |
| herb | Maer-Okt (3-10) | Korrekt fuer Kuechenkraeuter in Kultur |
| cactus | Mai-Aug (5-8) | Korrekt; kuerzeste Saison, biologisch begruendet |

Die Aktivmonate sind insgesamt gut gewaehlt und zeigen eine sinnvolle Differenzierung zwischen den Presets.

### 3.2 Dormanz-Phasen — BEHOBEN

~~Die `DORMANCY_PHASES = frozenset(['dormancy', 'dormant', 'senescence', 'hardening_off'])` werden als Duenge-Sperre verwendet.~~

**Status: BEHOBEN.** Die DORMANCY_PHASES in REQ-022 enthalten jetzt alle relevanten Phasen:
- `dormancy` — Winterruhe (REQ-003)
- `senescence` — Alterungsphase (REQ-003)
- `hardening_off` — Abhaertung (REQ-003, jetzt auch im PhaseType-Literal)
- `maintenance` — Winter-Erhaltungspflege bei Zimmerpflanzen (REQ-020)
- `acclimatization` — Eingewoehnung nach Kauf/Transport (REQ-020)
- `repotting_recovery` — Erholung nach Umtopfen (REQ-020)

Zusaetzlich wurde REQ-003 `PhaseType` um alle Zimmerpflanzen-Phasen (`acclimatization`, `active_growth`, `maintenance`, `repotting_recovery`) und `hardening_off` erweitert.

| Phase (REQ-020) | In DORMANCY_PHASES? | Sollte Duengung blockiert werden? |
|-----------------|--------------------|---------------------------------|
| `maintenance` | JA | JA -- entspricht der Winterruhe bei Zimmerpflanzen |
| `acclimatization` | JA | JA -- Pflanze nach Kauf/Umtopfen nicht duengen |
| `repotting_recovery` | JA | JA -- frisches Substrat enthaelt Depotduenger; zusaetzliche Duengung kann Wurzeln verbrennen |
| `active_growth` | NEIN | NEIN -- korrekt, in dieser Phase wird geduengt |

### 3.3 Biologische Begruendung des Duenge-Guards

Die Begruendung im Dokument ist fachlich korrekt und gut formuliert:
> "Duengung waehrend Dormanz kann Salzstress verursachen, da die Pflanze keine aktive Naehrstoffaufnahme betreibt."

**Ergaenzung:** Ueberschuessige Salze koennen auch die Wurzel-Mikrobiom-Balance stoeren und zu sekundaerer Wurzelfaeule fuehren. Bei Epiphyten (Orchideen) sind die Velamen-Wurzeln besonders empfindlich gegen Salzschaeden.

---

## 4. Bewertung des Adaptive Learning

### 4.1 Algorithmus-Bewertung

Der Algorithmus (3 konsistente Signale, 1 Tag Anpassung, max. +-30%) ist konservativ und grundsaetzlich sinnvoll. Die Frage ist, ob er biologisch sicher ist.

### 4.2 Risikoszenarien

**Szenario A: Vergesslicher Nutzer (hoechstes Risiko)**

Ein Nutzer vergisst regelmaessig das Giessen und bestaetigt erst 2-3 Tage nach Faelligkeit. Nach 3 verspaeteten Bestaetigungen erhoeht das System das Intervall um 1 Tag. Nach 9 verspaeteten Bestaetigungen ist das Intervall um 3 Tage gestiegen.

- Tropical (7 Tage Basis): Maximum durch +-30%-Grenze: 9,1 Tage. Fuer die meisten tropischen Pflanzen im Sommer bereits grenzwertig, aber ueberlebbar. Im Winter waere es akzeptabel.
- Calathea (5 Tage Basis): Maximum: 6,5 Tage. Calatheen zeigen bei 6-7 Tagen ohne Wasser im Sommer bereits irreversible Blattrandnekrosen. Die 30%-Grenze ist hier zu grosszuegig.
- Herb (3 Tage Basis): Maximum: 3,9 Tage. Fuer Basilikum im Hochsommer kann selbst 4 Tage zu lang sein (Welke, Bluetenbildung als Stressreaktion).

**Szenario B: Bewusstes Anpassen (beabsichtigter Nutzen)**

Ein erfahrener Nutzer giesst seine Monstera im Winter bewusst alle 10 statt 7 Tage. Das System lernt nach 3 Zyklen. Dies ist der beabsichtigte und sinnvolle Use Case. Das System funktioniert hier korrekt.

**Szenario C: Saisonaler Wechsel**

Ein Nutzer hat ueber den Winter ein Intervall von 9 Tagen (statt 7) "angelernt". Im Fruehjahr steigt der Wasserbedarf zurueck auf 5-7 Tage. Das System braucht erneut 3 Zyklen (= 15-21 Tage), um zurueckzuadaptieren. In dieser Uebergangszeit erhaelt die Pflanze zu wenig Wasser.

### 4.3 Bewertung: Ist Adaptive Learning biologisch sicher?

Grundsaetzlich ja, aber mit Einschraenkungen:
- Die +-30%-Grenze ist fuer trockenheitsempfindliche Arten (Calathea, Basilikum, Farne) zu grosszuegig
- Es fehlt ein Mechanismus zur saisonalen Rueckstellung (gelerntes Intervall sollte bei Saisonwechsel resettet oder zumindest ueberpruefen werden)
- Die Unterscheidung zwischen "Nutzer giesst spaeter weil er es weiss" und "Nutzer vergisst und die Pflanze leidet" ist algorithmisch nicht moeglich

---

## 5. Fehlende Pflegeaspekte fuer Zimmerpflanzenbesitzer

### 5.1 Fehlende Presets

| Preset-Vorschlag | Typische Pflanzen | Begruendung |
|-------------------|-------------------|-------------|
| `fern` | Nephrolepis, Adiantum, Asplenium | Hoechster Feuchtigkeitsbedarf aller Zimmerpflanzen; benoetigen taegliches Bespreuhen oder Luftbefeuchter; 3-4 Tage Giessintervall; extrem saisonsensitiv |
| `mediterranean` | Rosmarin, Olivenbaum, Oleander, Zitrus, Lorbeer | Gegenteil von "tropical": durchlaessiges Substrat, volle Sonne, sparsam giessen, kalktolerante Duengung, kuehle Ueberwinterung (5-10 Grad C) |
| `carnivorous` | Dionaea, Sarracenia, Nepenthes | Kein Duenger (NIEMALS!), nur Regenwasser/destilliertes Wasser, saures Substrat (Sphagnum), hohe Luftfeuchte -- widersprechen mehreren Grundannahmen des Duenge-Systems |

### 5.2 Fehlende Erinnerungstypen

| Erinnerungstyp | Beschreibung | Prioritaet |
|----------------|-------------|-----------|
| `humidity_check` | Luftfeuchte pruefen/erhoehen -- besonders relevant im Winter bei Heizungsluft (Calathea, Farne, tropische Pflanzen) | Hoch fuer bestimmte Presets |
| `leaf_cleaning` | Blattreinigung zur Staubentfernung -- verbessert Lichtabsorption und beugt Schaedlingsbefall vor. Empfehlung: alle 4-8 Wochen fuer grossblaettrige Pflanzen | Mittel |
| `rotation` | Pflanze um 90-180 Grad drehen, damit alle Seiten gleichmaessig Licht erhalten -- verhindert einseitiges Wachstum. Intervall: 7-14 Tage | Niedrig |
| `substrate_check` | Substratqualitaet pruefen (Verdichtung, Algenbildung, Salzablagerungen). Relevanter als fixe Umtopf-Intervalle | Mittel |

### 5.3 Fehlende Pflegeinformationen im CareProfile

| Feld | Beschreibung | Fachliche Begruendung |
|------|-------------|----------------------|
| `watering_method` | Giess-Methode (Tauchbad, Uebergiessen, Untersetzer, Bespreuhen) | Orchideen: Tauchbad; Sukkulenten: Durchgiessen mit Ablaufen lassen; Calathea: von unten oder Uebergiessen ohne Blaetter zu benaessen |
| `water_quality` | Wasserqualitaet (Leitungswasser OK, kalkarm, nur Regenwasser/destilliert) | Calathea: kalkempfindlich; Karnivoren: nur destilliert; Orchideen: kalkarm bevorzugt |
| `watering_interval_summer` / `watering_interval_winter` | Saisonale Giessintervall-Differenzierung | Siehe Abschnitt 2 -- biologisch notwendig |
| `toxicity_pets` | Giftigkeit fuer Haustiere (Katzen, Hunde) | REQ-020 hat Toxizitaetsdaten -- sollte ins CareProfile uebernommen werden fuer Warnungen |

---

## Befund-Register

### F-001: Feste Giessintervalle ohne saisonale Differenzierung (KRITISCH)

**Anforderung:** `watering_interval_days: int` als einziger Giesswert im CareProfile (`REQ-022_Pflegeerinnerungen.md`, Zeile ~95)
**Problem:** Der Wasserbedarf von Zimmerpflanzen schwankt zwischen Sommer und Winter um den Faktor 1,5 bis 3. Ein einziger Intervall-Wert fuehrt im Winter zu Ueberwaaesserung (Wurzelfaeule) oder im Sommer zu Unterwaaesserung (Trockenstress). Dies ist der haeufigste Pflegefehler bei Zimmerpflanzen.
**Korrekte Formulierung:** Zwei Felder: `watering_interval_summer_days: int` und `watering_interval_winter_days: int`, oder ein saisonaler Multiplikator `winter_watering_factor: float` (z.B. 0.5 = halbe Frequenz im Winter). Die Winter-Monate koennen analog zu `fertilizing_active_months` konfiguriert oder aus dem Standort abgeleitet werden.
**Gilt fuer Anbaukontext:** Zimmerpflanzen

**Alternative (einfacher):** Falls zwei Felder die Komplexitaet zu stark erhoehen: Ein `winter_watering_multiplier: float = 1.5` im Preset, der den Intervall automatisch im Zeitraum November-Februar verlaengert. Beispiel: Tropical Sommer 7 Tage, Winter 7 * 1.5 = 10.5 Tage, gerundet 11 Tage.

### F-002: Preset "herb" fasst inkompatible Pflegegruppen zusammen (KRITISCH)

**Anforderung:** `herb` Preset mit `watering_interval_days: 3` (`REQ-022_Pflegeerinnerungen.md`, Zeile ~44)
**Problem:** Mediterrane Kraeuter (Rosmarin, Thymian, Salbei, Oregano) benoetigen 7-10 Tage Giessintervall und durchlaessiges, mineralisches Substrat. Ein 3-Tage-Intervall fuehrt bei diesen Arten zuverlaessig zu Wurzelfaeule. Basilikum und Minze hingegen benoetigen tatsaechlich 2-3 Tage.
**Korrekte Formulierung:** Entweder (a) Preset aufteilen in `herb_moisture` (Basilikum, Minze, Petersilie: 3 Tage) und `herb_mediterranean` / `mediterranean` (Rosmarin, Thymian, Salbei: 10 Tage) oder (b) in der Mapping-Logik `get_or_create_profile` die Species-Herkunft (native_habitat: "Mediterranean") beruecksichtigen und automatisch den korrekten Preset zuweisen.
**Gilt fuer Anbaukontext:** Zimmerpflanzen

### ~~F-003: DORMANCY_PHASES nicht mit REQ-020 Zimmerpflanzen-Phasen abgeglichen~~ — BEHOBEN

**Status: BEHOBEN.** DORMANCY_PHASES in REQ-022 enthaelt jetzt `maintenance`, `acclimatization`, `repotting_recovery`. REQ-003 PhaseType wurde um alle Zimmerpflanzen-Phasen erweitert. Der Vorschlag zur Umbenennung in `NO_FERTILIZING_PHASES` bleibt als optionale Verbesserung bestehen.

### F-004: Lithops als Beispiel im Cactus-Preset (FEHLER)

**Anforderung:** Cactus-Preset mit Lithops als typische Pflanze (`REQ-022_Pflegeerinnerungen.md`, Zeile ~45)
**Problem:** Lithops (Lebende Steine) sind taxonomisch keine Kakteen (Familie Aizoaceae, nicht Cactaceae) und haben einen voellig anderen Giesszyklus. Waehrend der Hautungsphase (typisch Februar-Mai) duerfen Lithops UEBERHAUPT NICHT gegossen werden -- jedes Giessen kann die Pflanze toeten. Ein 21-Tage-Intervall waere in dieser Phase fatal.
**Korrekte Formulierung:** Lithops aus der Beispielliste entfernen und durch tatsaechliche Kakteen ersetzen (z.B. Mammillaria, Echinocactus, Gymnocalycium). Lithops benoetigen ein eigenes Preset oder mindestens einen Warnhinweis.
**Gilt fuer Anbaukontext:** Zimmerpflanzen

### F-005: Calathea Umtopfintervall zu kurz (HINWEIS)

**Anforderung:** `calathea` Preset mit `repotting_interval_months: 12` (`REQ-022_Pflegeerinnerungen.md`, Zeile ~43)
**Problem:** Calatheen wachsen relativ langsam und reagieren empfindlich auf Stoerungen des Wurzelbereichs. Ein jaehrliches Umtopfen ist fuer die meisten Calathea-Arten unnoetig und kann Stress verursachen. 18-24 Monate ist praxisnaeh.
**Korrekte Formulierung:** `repotting_interval_months: 18`
**Gilt fuer Anbaukontext:** Zimmerpflanzen

---

## Unvollstaendig -- Wichtige Aspekte fehlen

### U-001: Saisonale Giessintervall-Anpassung fehlt

**Anbaukontext:** Zimmerpflanzen
**Fehlender Parameter:** `watering_interval_winter_days` oder `winter_watering_multiplier`
**Begruendung:** Siehe F-001. Ein fest konfigurierter Sommer-Intervall fuehrt im Winter zuverlaessig zu Ueberwaaesserung bei Sukkulenten, Kakteen und mediterranen Pflanzen. Das Adaptive Learning kann dies nicht rechtzeitig kompensieren (3 Zyklen Verzoegerung = 6-9 Wochen bei Kakteen).
**Formulierungsvorschlag:**
```python
CARE_STYLE_PRESETS = {
    'tropical': {
        'watering_interval_days': 7,
        'winter_watering_multiplier': 1.5,   # Winter: 10-11 Tage
        ...
    },
    'cactus': {
        'watering_interval_days': 21,
        'winter_watering_multiplier': 2.0,   # Winter: 42 Tage
        ...
    },
}
```

### U-002: Giessmethode fehlt im Erinnerungssystem

**Anbaukontext:** Zimmerpflanzen
**Fehlende Information:** Die Erinnerung sagt nur "Pflanze braucht Wasser", aber nicht WIE gegossen werden soll.
**Begruendung:** Die Giessmethode ist artspezifisch und fuer Einsteiger eine der haeufigsten Fehlerquellen:
- Orchideen: Tauchbad (10-15 Minuten), dann abtropfen lassen
- Sukkulenten: Kraeftig durchgiessen, vollstaendig ablaufen lassen, Untersetzer leeren
- Calathea: Von oben giessen, aber Blaetter nicht benaessen (Pilzgefahr)
- Farne: Einspreuhen + Giessen
**Formulierungsvorschlag:** `watering_method: Literal['soak', 'drench_and_drain', 'top_water', 'bottom_water']` im CareProfile, mit i18n-Anleitungstext in der ReminderCard.

### U-003: Wasserqualitaets-Hinweis fehlt

**Anbaukontext:** Zimmerpflanzen
**Fehlende Information:** `water_quality_note` im CareProfile
**Begruendung:** Bestimmte Pflanzengruppen reagieren empfindlich auf Kalk im Leitungswasser:
- Calathea/Maranta: Braune Blattspitzen bei kalkhaltigem Wasser
- Orchideen: Kalkablagerungen auf Velamen-Wurzeln blockieren Wasseraufnahme
- Azaleen, Kamelien: Kalkfreies Wasser erforderlich (saures Milieu)
- Karnivoren: Nur destilliertes Wasser oder Regenwasser
**Formulierungsvorschlag:** Ein optionaler `water_quality_hint: Optional[str]` im Preset, der als Tooltip in der ReminderCard angezeigt wird. Alternativ ein i18n-Key pro Preset.

### U-004: Luftfeuchtigkeits-Erinnerung fehlt

**Anbaukontext:** Zimmerpflanzen (speziell Calathea, Farne, tropische Pflanzen)
**Fehlende Funktionalitaet:** Kein Erinnerungstyp fuer Luftfeuchtigkeits-Management
**Begruendung:** Heizungsperiode (Oktober-April) reduziert die relative Luftfeuchtigkeit in Wohnungen auf 20-35% rH. Tropische Pflanzen benoetigen 50-70% rH. Die Symptome (braune Blattspitzen, Spinnmilbenbefall) entwickeln sich schleichend und werden von Einsteigern nicht mit Luftfeuchtigkeit in Verbindung gebracht.
**Formulierungsvorschlag:** Ein saisonaler `humidity_check`-Erinnerungstyp fuer Presets `calathea` und `tropical`, aktiv Oktober-Maerz. Anweisungstext: "Luftfeuchtigkeit pruefen -- ggf. Luftbefeuchter aufstellen oder Kiesschale verwenden."

### U-005: Giess-Erinnerung fuer `acclimatization`-Phase fehlt Sonderbehandlung

**Anbaukontext:** Zimmerpflanzen
**Fehlende Logik:** Waehrend der `acclimatization`-Phase (14-28 Tage nach Kauf/Umtopfen, definiert in REQ-020) sollte das Giessintervall automatisch verlaengert werden (Faktor 1.3-1.5), da:
- Wurzeln durch Transport/Umtopfen geschaedigt sind
- Reduzierte Wasseraufnahmekapazitaet
- Substrat beim Kauf oft bereits durchfeuchtet
**Formulierungsvorschlag:** In `CareReminderEngine._get_effective_interval()`: Wenn `current_phase == 'acclimatization'`, dann Giessintervall * 1.3 zurueckgeben.

---

## Zu Ungenau -- Praezisierung noetig

### P-001: Vage Standort-Check-Logik

**Vage Anforderung:** "Oktober: Pflanzen vom Balkon holen / Winterquartier vorbereiten" (fest codiert auf 1.-15. Oktober)
**Problem:** Der optimale Zeitpunkt haengt von der Klimazone und dem aktuellen Wetter ab. In Suedbayern koennen erste Froeste bereits Mitte September auftreten; in milden Lagen (Koeln, Rheinland) koennen Pflanzen bis Ende Oktober draussen bleiben. Ein festes Datum ist fuer eine App mit potenziell internationaler Nutzerbasis ungeeignet.
**Messbare Alternative:** Standort-Check triggern wenn (a) Wettervorhersage am Standort Frost (<3 Grad C) ankuendigt oder (b) Durchschnittstemperatur der letzten 7 Tage unter 10 Grad C faellt. Falls keine Wetterdaten verfuegbar: Konfigurierbare Monate im CareProfile statt hardcodierter Oktober/Maerz.

### P-002: care_style-Mapping zu vage

**Vage Anforderung:** "Species mit native_habitat containing 'tropical' -> 'tropical'" und "Species mit common_names containing 'Orchid*' -> 'orchid'"
**Problem:** String-Matching auf `native_habitat` und `common_names` ist fehleranfaellig. "Tropical" koennte auch in "subtropical" oder in Beschreibungstexten vorkommen. Common-Name-Matching scheitert an Sprachvarianten (Orchidee/Orchid/Orquidea).
**Messbare Alternative:** Ein explizites `care_style: CareStyleType`-Feld auf der Species-Ebene (REQ-001) oder auf der BotanicalFamily-Ebene waere zuverlaessiger als Heuristiken ueber Textfelder.

### P-003: Repotting-Intervall als reine Zeitangabe

**Vage Anforderung:** `repotting_interval_months: int` (z.B. 18 Monate)
**Problem:** Der Umtopfbedarf wird nicht primaer durch Zeit bestimmt, sondern durch Wurzelwachstum (Pflanze ist "potbound"), Substratabbau und Nahrstofferschoepfung. Eine Pflanze in einem grossen Topf braucht seltener umgetopft zu werden als dieselbe Pflanze in einem kleinen Topf.
**Messbare Alternative:** Zusaetzlich zur Zeitangabe einen Hinweistext in der Umtopf-Erinnerung: "Pruefen Sie: (1) Wachsen Wurzeln aus dem Ablaufloch? (2) Trocknet das Substrat ungewoehnlich schnell aus? (3) Waechst die Pflanze merklich langsamer?" -- als `instruction_i18n_key` in der ReminderCard.

---

## Hinweise und Best Practices

### H-001: Empfehlung fuer saisonale Rueckstellung des Adaptive Learning

Das gelernte Intervall sollte beim Saisonwechsel (z.B. beim Uebergang der Duengemonate) automatisch zurueckgesetzt oder zumindest validiert werden. Konkret: Wenn ein Nutzer im Winter ein Giessintervall von 12 Tagen "angelernt" hat, sollte dieses im Maerz nicht mehr gelten, sondern auf den Preset-Wert zurueckfallen.

### H-002: Snooze als negatives Signal werten

Aktuell wird Snooze korrekt vom Adaptive Learning ausgenommen. Erwaegen Sie jedoch, wiederholt gesnoozete Erinnerungen als Signal zu werten: Wenn ein Nutzer die Giess-Erinnerung 3x in Folge snoozt statt bestaetigt, koennte das Intervall zu kurz sein.

### H-003: Erste Giess-Erinnerung nach Pflanzenkauf

Die Spezifikation gibt bei fehlender Bestaetigungshistorie `days_since = 999` zurueck, was sofortige Faelligkeit bedeutet. Fuer Pflanzen, die gerade gekauft wurden (und typischerweise von der Gaertnerei frisch gegossen sind), ist das eine Fehlalarme. Erwaegen Sie, bei Pflanzen in der `acclimatization`-Phase die erste Erinnerung auf `watering_interval_days / 2` zu verzoegern.

### H-004: Orchideen-Tauchbad im Erinnerungstext

Der i18n-Key `pages.care.instructions.watering` sagt generisch "braucht Wasser". Fuer Orchideen waere ein spezifischerer Text sinnvoll: "Tauchbad-Zeit: Topf 10-15 Minuten in zimmerwarmes Wasser stellen, abtropfen lassen." Dies koennte ueber den `care_style` differenziert werden.

### H-005: Integration mit REQ-005 Sensorik

Falls REQ-005 (Hybrid-Sensorik) implementiert wird, sollten Bodenfeuchte-Sensordaten die Giess-Erinnerungen uebersteuern koennen. Ein Sensor, der ausreichende Bodenfeuchte meldet, sollte die Erinnerung automatisch verschieben. Dies waere die biologisch korrekteste Loesung, da der Wasserbedarf von Dutzenden Faktoren abhaengt (Temperatur, Licht, Luftfeuchtigkeit, Topfgroesse, Substrattyp, Pflanzengroesse), die ein festes Intervall nicht erfassen kann.

---

## Parameter-Uebersicht: Fehlende Messwerte

| Parameter | Vorhanden? | Empfohlener Bereich | Prioritaet |
|-----------|-----------|--------------------|-----------|
| Giessintervall Sommer (Tage) | Teilweise (als einziger Wert) | artspezifisch | Hoch |
| Giessintervall Winter (Tage) | NEIN | artspezifisch, Faktor 1.5-3x | Hoch |
| Giessmethode | NEIN | soak/drench/top/bottom | Mittel |
| Wasserqualitaet | NEIN | tap_ok/low_lime/distilled | Mittel |
| Luftfeuchte-Bedarf (rH%) | NEIN | artspezifisch | Mittel |
| Toxizitaet Haustiere | NEIN (in REQ-020 vorhanden) | safe/caution/warning/danger | Hoch |
| Winter-Giess-Multiplikator | NEIN | 1.3-2.5 je nach Preset | Hoch |
| Saisonale Phase (Sommer/Winter) | Nur fuer Duengung | Auch fuer Bewaaesserung noetig | Hoch |

---

## Empfohlene Datenquellen

| Bereich | Quelle | URL |
|---------|--------|-----|
| Zimmerpflanzen-Toxizitaet | ASPCA | aspca.org/pet-care/animal-poison-control |
| Giessmethoden | Royal Horticultural Society | rhs.org.uk/plants/types/houseplants |
| Kakteen-Pflege | Deutsche Kakteen-Gesellschaft (DKG) | dkg.eu |
| Orchideen-Pflege | Deutsche Orchideen-Gesellschaft (DOG) | orchidee.de |
| Zimmerpflanzen allgemein | Bayerische Landesanstalt fuer Weinbau und Gartenbau | lwg.bayern.de |
| Substrat-Wissen | Gesellschaft der Staudenfreunde | gds-staudenfreunde.de |

---

## Zusammenfassung der Aenderungsempfehlungen nach Prioritaet

### Prioritaet 1 (vor Implementierung beheben)

1. ~~**F-003: DORMANCY_PHASES erweitern**~~ — **BEHOBEN** (DORMANCY_PHASES und REQ-003 PhaseType korrigiert)
2. **F-001: Saisonale Giessintervalle** einfuehren (mindestens `winter_watering_multiplier`) -- verhindert die haeufigste Zimmerpflanzen-Todesursache (Ueberwaaesserung im Winter)
3. **F-002: Herb-Preset aufteilen** oder Mediterranean-Preset ergaenzen -- 3-Tage-Giessintervall ist fuer Rosmarin/Thymian/Salbei schaedlich

### Prioritaet 2 (sollte vor Release behoben werden)

4. **F-004: Lithops entfernen** aus Cactus-Beispielen
5. **U-002: Giessmethode** als Information in der ReminderCard anzeigen
6. **U-003: Wasserqualitaets-Hinweis** fuer kalkempfindliche Presets (calathea, orchid)
7. **U-005: Acclimatization-Phase** beruecksichtigen in der Giessintervall-Berechnung

### Prioritaet 3 (Erweiterungen fuer spaetere Versionen)

8. **U-001: Weitere Presets** (fern, mediterranean, carnivorous)
9. **U-004: Luftfeuchtigkeits-Erinnerung** als saisonaler Typ
10. **H-001: Saisonale Rueckstellung** des Adaptive Learning
11. **H-005: Sensorintegration** mit REQ-005 fuer feuchtebasierte Erinnerungen
