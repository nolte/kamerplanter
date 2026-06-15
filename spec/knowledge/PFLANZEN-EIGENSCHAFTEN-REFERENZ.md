# Pflanzen-Eigenschaften — art-übergreifende Domänenreferenz

**Erstellt:** 2026-06-15
**Status:** Fundament-Dokument (allgemeingültig, nicht sortenspezifisch)
**Zweck:** Verifizierte fachliche Grundlage, damit Stammdaten (REQ-001) und Oberflächen (REQ-021) **zielgenau** entwickelt werden — abgeleitet aus den realen Unterscheidungsmerkmalen von Pflanzen, nicht aus Einzelarten.

---

## 0. Wie dieses Dokument zu lesen ist

Dieses Dokument beschreibt **Eigenschafts-Dimensionen** von Pflanzen, keine konkreten Arten oder Sorten. Konkrete Pflanzen erscheinen ausschließlich als **Beispiel**. Es bildet die fachliche Begründung hinter den Stammdaten-Feldern und macht sichtbar, **welche Felder zwingend nötig sind, welche orthogonal getrennt gehören und wo das bestehende Modell Lücken hat**.

Jeder Befund ist mehrquellig verifiziert (RHS, USDA/ARS, DWD, University Extension Services, ASPCA, peer-reviewte Literatur). Quellenwidersprüche wurden **nicht geglättet**, sondern in §10 ausgewiesen — sie sind selbst eine Modellierungs-Anforderung (z. B. „Quelle/Methode pro Wert speichern").

### Das Kernprinzip: orthogonale Dimensionen

> **Die wichtigste Designentscheidung dieses Dokuments: Die vier Hauptdimensionen sind voneinander unabhängig (orthogonal) und müssen als getrennte Felder modelliert werden — niemals als ein einziges „Pflanzentyp"-Feld.**

Eine Tomate ist *gleichzeitig*:

- **Nutzpflanze** (Fruchtgemüse) — Dimension 1 (Klassifikation)
- **krautige Pflanze**, botanisch mehrjährig, **in Kultur einjährig** — Dimension 2 (Lebensdauer)
- über **Aussaat** vermehrbar (samenfest) oder als F1-Hybride nur per Neukauf — Dimension 3 (Vermehrung)
- **kontinuierlich/indeterminiert oder einmalig/determiniert** beerntbar — Dimension 4 (Ernte)
- frostempfindlich, vollsonnig, Starkzehrer — Querschnitt (Anbau-Anforderungen)

Ein `single-select`-„Kategorie"-Feld vermischt diese fünf verschiedenen Fragen und kollabiert an jedem Mischfall (immergrüne Staude, laubabwerfendes Gehölz, essbare Zierpflanze). Die folgenden Abschnitte führen jede Dimension einzeln und schließen mit dem **konsolidierten Feldmodell** (§8).

---

## 1. Dimension 1 — Klassifikation (Nutzungstyp · Wuchsform · Standort · Taxonomie)

Diese Dimension zerfällt selbst in **vier unabhängige Achsen**. Ihr gemeinsamer Nenner: Sie beschreiben *was die Pflanze ist / wozu sie dient*, nicht *wie lange sie lebt* oder *wie man sie erntet*.

### 1.1 Achse A — Nutzungs-/Zweck-Klassifikation (kulturell, nicht botanisch)

Folgt der **menschlichen Verwendung**, nicht der Pflanzenverwandtschaft. Oberste Ebene: **Nutzpflanze** (Ertrag/Nutzen) vs. **Zierpflanze** (Ästhetik).

**Nutzpflanzen-Untergruppen** — Gemüse wird nach dem **essbaren Pflanzenteil** gegliedert:

| Untergruppe | Essbarer Teil | Beispiel |
|---|---|---|
| Fruchtgemüse | Frucht aus Blüte | Tomate, Gurke, Paprika |
| Blatt-/Stängelgemüse | Blätter/Blattstiele | Salat, Spinat, Mangold |
| Wurzelgemüse | Wurzel/Speicherwurzel | Karotte, Pastinake |
| Knollengemüse | Spross-/Hypokotylknolle | Kartoffel, Kohlrabi |
| Hülsengemüse | Samen aus Hülse (*Fabaceae*) | Erbse, Bohne, Linse |
| Zwiebelgemüse | Zwiebel/Lauch (*Allium*) | Zwiebel, Knoblauch |

Weitere Klassen: **Kräuter/Gewürzpflanzen**, **Obst** (Baum-/Strauch-/Beerenobst), **Getreide**, **Heilpflanzen**, **Öl-/Faser-/Futterpflanzen**. **Zierpflanzen-Untergruppen**: Beet-/Balkonpflanzen, Stauden, Zimmerpflanzen, Schnittblumen, Ziergehölze, Zwiebelblumen.

> **Zentrale Datenmodell-Konsequenz — Mehrfachzuordnung:** Eine Pflanze kann **mehreren Nutzungstypen gleichzeitig** angehören. Kapuzinerkresse ist Zierpflanze **und** essbar **und** Heilpflanze **und** Begleitpflanze. → Nutzungstyp ist ein **mehrwertiges Feld (Tag-Set / many-to-many)**, kein single-select-Enum. (Im bestehenden Modell bereits korrekt als `Species.traits: list[str]` mit Werten wie `ornamental`, `edible`, `medicinal`, `fragrant`, `bee_friendly` gelöst.)
>
> Quellen: Britannica „Vegetable"; Plantura „Gemüsearten"; Wikipedia „Liste von Nutzpflanzen"; BZfE „Gewürze und Kräuter"; RHS „Plant types"; UConn IPM „Edible Landscapes".

### 1.2 Achse B — Botanische Wuchsform / Habitus

Orthogonal zum Nutzungstyp; beschreibt den **morphologischen Aufbau**. Grundachse darunter: **verholzt (woody, sekundäres Dickenwachstum) vs. krautig (herbaceous)**. Geschlossenes Vokabular (an USDA-PLANTS-„growth habit" angelehnt, erweitert):

- **Baum** — ein dominanter Stamm, Krone
- **Strauch** — mehrere bodennahe Triebe
- **Halbstrauch (Subshrub)** — nur basal verholzt, oberer Teil krautig (Lavendel, Thymian)
- **Krautige Pflanze / Staude (Forb)** — nicht verholzt
- **Gras/Süßgras (Graminoid)** — *Poaceae* u. a.
- **Kletterpflanze/Ranker** — braucht Stütze (verholzt = Liane, krautig = Vine)
- **Sukkulente/Kaktus** — Wasserspeicher-Funktionsgruppe (Kaktus = Familie *Cactaceae*; nicht jede Sukkulente ist Kaktus)
- **Zwiebel-/Knollengeophyt** — unterirdisches Speicherorgan
- **Farn** · **Moos** · **Wasser-/Sumpfpflanze** · **Epiphyt** (aufsitzend, nicht parasitisch)

> **Achtung — zwei verschiedene Systeme:** Der oben genannte *physiognomische Habitus* ist nicht zu verwechseln mit dem *funktionalen* **Raunkiær-System** (Klassifikation nach Position der Überdauerungsknospen: Phanero-/Chamae-/Hemikrypto-/Krypto-/Therophyt). Die Systeme decken sich **nicht** (ein Phanerophyt umfasst Baum *und* Strauch). Empfehlung: Habitus als geschlossenes Enum führen; Raunkiær-Lebensform optional als zweites, wissenschaftliches Feld.
>
> Quellen: USDA PLANTS growth-habit; RHS „Plant types"; Wikipedia „Pflanzenwuchsform" / „Raunkiær plant life-form"; Wikipedia „Succulent plant".

> **⚠ Lücke gegenüber Bestand:** `Species.growth_habit` führt heute nur `herb | shrub | tree | vine | groundcover`. Das deckt Gräser, Sukkulenten, Geophyten, Farne, Wasserpflanzen, Epiphyten, Halbsträucher **nicht** ab — obwohl die Pflege (Bewässerung, Stütze, Pflanztiefe) genau daran hängt. Siehe §9 (Empfehlung E1).

### 1.3 Achse C — Standort-/Umfeld-Klasse & Winterhärte

**Standortklassen:** Zimmerpflanze (indoor) · Freiland (outdoor) · Gewächshaus/geschützt · Kübel/Container (Querschnitt). „Zimmerpflanze" ist **keine botanische, sondern eine kultivierungsbedingte** Kategorie — viele Zimmerpflanzen sind tropische Epiphyten/Sukkulenten, die *deshalb* indoor stehen, weil sie nicht winterhart sind.

**Winterhärte — zwei nicht-ineinander-umrechenbare Skalen:**

- **USDA Plant Hardiness Zones (1–13, a/b):** klassifizieren einen **Ort** nach der **durchschnittlichen jährlichen Tiefsttemperatur** (nicht dem absoluten Rekord). 10-°F-Zonen, 5-°F-Halbzonen. Deutschland überwiegend WHZ 6–8.
- **RHS Hardiness Rating (H1a–H7):** bewertet eine **Pflanze** nach **absoluter** Minimaltemperatur (°C) und kodiert die Schutzumgebung ins Label (H1a > 15 °C „beheiztes Gewächshaus tropisch" … H7 < −20 °C „sehr hart"). *tender* = H1a–H2.
- **Mitteleuropa/WHZ:** Heinze & Schreiber (1984), DWD-basiert, °C-Übersetzung der USDA-Zonen.

> **Datenmodell-Konsequenz:** **Pflanzen-Winterhärte** (Eigenschaft der Art/Sorte) und **Standort-Zone des Nutzers/Beets** getrennt führen; die Überwinterungslogik *vergleicht* beide. USDA-Zone und RHS-Rating ggf. getrennt speichern, **nicht** konvertieren. (Bestand bildet das bereits ab: `Species.hardiness_zones: list[str]`, `frost_sensitivity: hardy | half_hardy | tender`, `hardiness_detail`.)
>
> Quellen: USDA/ARS „2023 Plant Hardiness Zone Map"; RHS „Hardiness Rating" (PDF); DWD „Winterhärtezonen"; Wikipedia „Hardiness zone".

### 1.4 Achse D — Botanische Taxonomie-Ebenen

**Familie → Gattung → Art → [Unterart/Varietät] → Sorte/Kultivar.** Die maßgebliche Frage fürs Datenmodell: **welche Eigenschaft gilt auf welcher Ebene?**

- **Familienebene:** **Fruchtfolge/Crop-Rotation** und **breite Schädlings-/Krankheitsanfälligkeit**. Pflanzen einer Familie teilen Schaderreger → gleiche Familie nicht 3–4 Jahre am selben Platz. → **Familie ist ein erstklassiges Stammdatum mit eigenem Lookup** (Bestand: `BotanicalFamily` mit `rotation_category`, `nitrogen_fixing`, `common_pests`, `common_diseases`, `typical_nutrient_demand`).
- **Art-/Sortenebene (die meisten Eigenschaften):** Wuchshöhe/-breite, Winterhärte, Reife-/Erntezeit, Krankheitsresistenz. Sorten werden *für* solche Merkmale selektiert und behalten sie bei vegetativer Vermehrung. → **Eigenschafts-Vererbung** Art → Sorte, mit Override auf Sortenebene.

> Quellen: ICN/ICNCP (Nomenklatur); Iowa State / UMN / Cornell Extension (Crop-Rotation by family); Plantura „Pflanzenarten & -sorten".
>
> **Quellenabweichung (echt):** Rettich/Radieschen/Steckrübe sind nach *essbarteil-Systematik* **Wurzelgemüse**, nach *RHS-Crop-Rotation* aber **Brassicas** (für die Fruchtfolge zählt die Familie). → **Gemüse-Untergruppe (Verwendung) und Familie (Rotation) sind verschiedene Felder und dürfen widersprechen.**

---

## 2. Dimension 2 — Lebensdauer / Lebenszyklus

Sagt aus, **über wie viele Vegetationsperioden** eine Pflanze lebt. Unabhängig von Frosthärte, Blattverhalten, Dormanz — mit denen sie im Alltag oft vermischt wird.

### 2.1 Die Kategorien

- **Einjährig (annuell):** ganzer Zyklus Keimung→Blüte→Samen→Tod in **einer** Vegetationsperiode; echte Annuelle (Therophyten) verholzen nie, bilden keine Überdauerungsorgane.
  - *Sommerannuell* (keimt Frühjahr, stirbt vor Winter) vs. *Winterannuell* (keimt Herbst, überwintert als Rosette, blüht Folgefrühjahr, ~12 Mt.; braucht oft Vernalisation).
- **Zweijährig (biennal):** **zwei** Vegetationsperioden — Jahr 1 Blattrosette + Speicherorgan → Überwinterung/**Vernalisation** → Jahr 2 Schossen/Blüte/Samen → Tod.
- **Mehrjährig/ausdauernd (perennierend):** lebt > 2 Jahre, treibt jährlich neu aus.
  - *Krautige Staude* (zieht im Winter ein, überdauert über Wurzel/Rhizom/Knolle/Zwiebel) vs. *Gehölz* (verholzt, dauerhafte Holzstruktur).

> **Sonderfall „einjährig in Kultur" / tender perennial:** botanisch mehrjährige Pflanzen (in frostfreier Heimat ausdauernd), die in kühlen Klimaten **wie einjährig** kultiviert werden, weil **Frost sie abtötet** (Tomate, viele Balkonpflanzen). Das Etikett „einjährig" ist hier **Kultur-Praxis, nicht Genetik** — *klimaabhängig*. **Dies verlangt zwei getrennte Felder** (botanische Lebensdauer ≠ Lebensdauer-in-Kultur). Siehe §9 (E2).

### 2.2 Blüh-Strategie (orthogonale Reproduktions-Achse)

- **Monokarp (hapaxanth):** blüht **einmal im Leben**, stirbt dann. **Kann ausdauernd sein** — Agave lebt Jahrzehnte vegetativ, viele Bambusse blühen synchron nach Jahrzehnten und sterben.
- **Polykarp (pollakanth):** blüht mehrfach über Jahre (Normalfall bei Stauden/Gehölzen).

> Monokarpie (einmal vs. mehrfach Blühen) ist eine **eigene Achse** neben der Lebensdauer. Ein mehrjährig wirkender Bestand mit `monokarp` braucht ein Terminal-Ereignis „blüht einmal, stirbt danach". Siehe §9 (E3).

### 2.3 Zusammenhängende, aber eigenständige Eigenschaften

| Eigenschaft | Werte | Bemerkung |
|---|---|---|
| **Frosttoleranz** | frosthart / halbhart / frostempfindlich | nicht statisch — junges Frühjahrsgewebe ist wieder empfindlich → Auspflanz-Regel „nach Eisheiligen/letztem Frost" |
| **Blattverhalten (Laubrhythmus)** | sommergrün/laubabwerfend · wintergrün · immergrün · halbimmergrün | wintergrün ≠ immergrün (Blattalter ≈ 1 vs. > 1 Vegetationsperiode) |
| **Dormanz / Einziehen** | Winterruhe; bei Gehölzen Para-/Endo-/Ökodormanz + Kältebedarf (chilling) | Endodormanz endet erst nach erfülltem Kältebedarf |
| **Vernalisation** | Kältereiz (~0–10 °C, Wochen) zur Blühinduktion | löst Schossen bei Biennalen/Winterannuellen |

> **Konsequenz Ernte vs. Samengewinnung (Biennale):** Die essbare Ernte ist das **vegetative Speicherorgan aus Jahr 1**; Samengewinnung verlangt Überwinterung + Blüte in Jahr 2. → Zwei verschiedene Nutzungsmodi mit unterschiedlichen Phasenplänen.
>
> Quellen: Wikipedia/RHS „Annual/Biennial/Perennial plant"; Oregon State/Missouri/UMN Extension; NC State (Tomate als tender perennial); Pflanzenforschung.de (Vernalisation); DWD/RHS (Winterhärte); Wikipedia „Monocarpy" / „Laubrhythmus"; PMC „Bud Dormancy".

> **Bestand:** `LifecycleConfig.cycle_type: annual | biennial | perennial`, `typical_lifespan_years`, `dormancy_required`, `vernalization_required`, `vernalization_min_days`; `GrowthPhase.is_recurring`. **Gut abgedeckt** — Lücken nur bei „in-Kultur"-Split und Blüh-Strategie (§9).

---

## 3. Dimension 3 — Vermehrung (Propagation)

Grundunterscheidung **generativ vs. vegetativ** — das wichtigste Begriffspaar, weil es über **Sortenechtheit** entscheidet:

| | **Generativ (Samen)** | **Vegetativ (Klon)** |
|---|---|---|
| Genetik | Variation (zwei Eltern) | exakter Klon |
| Sortenecht | nur bei samenfesten Sorten, **nicht** bei F1-Hybriden | immer |
| Erhält Sortenmerkmale | nein (bei F1) | ja (einziger Weg bei sterilen/F1-Sorten) |

### 3.1 Generative Vermehrung (Aussaat) — relevante Parameter

Keimtemperatur (Faustregel 18–24 °C), **Licht- vs. Dunkelkeimer**, **Saattiefe** (2–4× Saatkorndurchmesser; Lichtkeimer nicht bedecken), **Dormanzbrechung** (Skarifikation / Kalt- bzw. Warmstratifikation / Doppeldormanz mit zwingender Reihenfolge), **Direktsaat vs. Vorkultur+Pikieren** (4–12 Wochen vor letztem Frost) + **Härten (hardening off)**.

> **Samenfest vs. F1-Hybride:** samenfest (open-pollinated) = „true to type", Eigensaatgut sinnvoll. F1-Hybride = uniform/vigorös, aber **Eigensaatgut scheitert** (F2 spaltet auf) → jährlicher Nachkauf oder vegetativ. → Eigenes **Sorten**-Feld (`seed_type`), das steuert, ob `seed` als Erhaltungsmethode taugt. (Bestand: `Cultivar.seed_type: open_pollinated | f1_hybrid | f2 | landrace | clone` — vorhanden.)

### 3.2 Vegetative Methoden (Taxonomie)

Stecklinge (Trieb nach Verholzungsgrad: **krautig / Weichholz Mai–Juli / halbreif Juli–Frühherbst / Hartholz=Steckholz Dormanz**; dazu Blatt-, Blattknospen-, Cane-, **Wurzelstecklinge**) · **Teilung** (Stauden, Frühjahr/Herbst) · **Absenker/Ableger** (einfach/Spitze/Schlangen/Abrisse/**Abmoosen**) · **Ausläufer/Stolonen/Kindel** · **Zwiebeln/Brutzwiebeln/Knollen/Rhizome (Separation)** · **Veredelung/Pfropfen + Okulation** (Edelreis + Unterlage; Obst, Rosen) · **Meristem-/Gewebekultur** (in vitro).

### 3.3 Konsequenzen für Datenmodell & UI (direkt branch-relevant)

Dieser Block fundiert die aktuell auf `feat/species-propagation-methods` eingeführten Felder `propagation_methods` / `propagation_months` / `propagation_notes`:

- **`propagation_methods` = Mehrfachauswahl (1..n)** aus kontrolliertem Vokabular — pro Art sind regelmäßig **mehrere** Methoden zulässig (Rose: Aussaat + Steckholz + Wurzelsteckling + Okulation; Erdbeere: Aussaat + Ausläufer + Teilung).
- **⚠ Parameter sind methoden-spezifisch, nicht art-global.** Zeitfenster und Hinweise gelten **pro Methode**, nicht pro Art — sonst geht Information verloren (Weichholzsteckling Mai–Juli *vs.* Teilung Herbst bei derselben Art). **Empfehlung:** `propagation_methods` als **Liste von Objekten** `{ method, months[], notes }` modellieren. Die heutige flache Triade (`methods` + globale `months` + globale `notes`) koppelt die Monate fälschlich an die Art statt an die Methode. Siehe §9 (E4) — **dies betrifft die laufende Branch-Arbeit unmittelbar.**

```yaml
# empfohlene Struktur (statt flacher paralleler Felder)
propagation_methods:
  - method: cutting_softwood
    months: [5, 6, 7]
    notes: "Bewurzelungshormon empfohlen; hohe Luftfeuchte."
  - method: division
    months: [3, 4, 9, 10]
    notes: "Frühjahr oder 6–8 Wochen vor Bodenfrost."
```

> Quellen: NC State Extension Gardener Handbook Kap. 13 (Hauptanker); RHS „Propagation"; UMN „Dividing perennials"; Penn State „Bulbs, Corms, Rhizomes and Tubers"; Iowa State (semi-hardwood); Britannica „Propagation"; RHS „F1 hybrids".

---

## 4. Dimension 4 — Ernteverhalten

### 4.1 Erntemuster über die Zeit (Kern-Enum)

- **Einmalernte / determiniert** — Ertrag auf einen Zeitpunkt konzentriert, oft ganze Pflanze (Kopfsalat, Zwiebel, Getreide, determinierte Tomate/Buschbohne, Blumenkohl, Kartoffel). Botanisch z. B. determinierte Tomate = *SELF-PRUNING*-Mutation → gleichzeitige Reife.
- **Mehrfach-/Durchpflück-Ernte / indeterminiert** — kontinuierlich über Wochen/Monate **einer** Saison (indeterminierte Tomate, Gurke, Zucchini, Stangenbohne, Paprika; Sonderform „cut-and-come-again" bei Pflücksalat/Spinat). Kausal: regelmäßiges Abernten hält die Pflanze im Ertragsmodus; stehenbleibende reife Frucht drosselt die Produktion.
- **Mehrjährig-wiederkehrend** — über Jahre, mit **Juvenilphase / Ertragsbeginn nach Standjahren** (Spargel ab J. 4, Rhabarber ab J. 3, Obstbaum je Unterlage 2–10 J., Beerensträucher). Pflanzgut und Unterlage verschieben den Beginn.

### 4.2 Geernteter Pflanzenteil bestimmt das Muster

**Leitprinzip:** Terminales Organ (ganze Pflanze, Kopf, Bulbe, Knolle, Hauptkopf) → **Einmalernte**. Iteratives/seitliches Organ (Einzelblätter, Früchte indeterminierter Pflanzen, perennierende Sprosse) → **Mehrfachernte**.

> **Orthogonalität:** Erntemuster und geernteter Teil sind **nicht voneinander ableitbar** — dieselbe Teil-Kategorie zeigt beide Muster (Blatt: Kopfsalat=einmal vs. Pflücksalat=kontinuierlich; Blütenknospe: Blumenkohl=einmal vs. Brokkoli=kontinuierlich). → **Beide unabhängig erfassen.**

### 4.3 Reife- & Erntekriterien

Farbe/Größe/Festigkeit · **Days to Maturity (DTM)** · **Wärmesumme (GDD)** als robusterer Prädiktor als Kalendertage · **physiologische vs. Genussreife** · **klimakterisch vs. nicht-klimakterisch** (nachreifend vs. nicht) · **Bolting/Schossen** als Ernte-Ende-Signal.

> **⚠ Zwei load-bearing Modellierungs-Anforderungen aus der Verifikation:**
> 1. **DTM braucht einen Bezugspunkt-Schalter** (`dtm_reference: direct_seed | transplant`). Die Konvention divergiert nachweislich zwischen Saatgutfirmen — ohne Bezugspunkt ist `days_to_maturity` mehrdeutig.
> 2. **Klimakterik braucht einen dritten Wert** (`climacteric | non_climacteric | atypical/uncertain`). Honigmelone, Blaubeere, Paprika, Feige sind echte Grenzfälle mit Quellenwiderspruch (MSU vs. Mehrheit). Eine erzwungene Binär-Einordnung kodifiziert Falschwissen. Siehe §9 (E5).

### 4.4 Nachernte (Post-Harvest)

Lagerfähigkeit (sofort-verderblich vs. monatelang lagerbar; Lagergruppen kalt-feucht / kalt-trocken / kühl-trocken) · **Curing/Aushärten** (Zwiebel, Knoblauch, Kürbis, Süßkartoffel, Kartoffel — jeweils eigene Temp/rF/Dauer) · **Trocknung/Fermentation** · **Karenzzeit/PHI** (gesetzliche Wartezeit nach Pflanzenschutz — bestimmt den **frühestmöglichen** Erntetermin mit).

> **PHI ist nicht art-, sondern mittel × kultur-spezifisch** — gehört konzeptuell an die *Behandlung*, nicht an die Pflanzenart als Stammdatum.
>
> Quellen: UC Davis Postharvest; Penn State / Cornell / Illinois / MSU Extension; RHS; FAO; BVL (PHI amtlich); BZfE (Lagerung); LfL; peer-reviewt (JXB, BMC Plant Biology).

> **Bestand:** `harvest_type: partial | final | continuous`, `harvest_indicators` (color/size/foliage/gdd/days_since_flowering/…), Post-Harvest-Protokolle (`drying | curing | aging | hardening | storage` mit Temp/rF/Dauer), `Cultivar.years_to_first_harvest`, `berry_type`. **Klimakterik-Feld fehlt** (relevant fürs Nachreifen/Lagern) → §9.

---

## 5. Querschnitt — Welche Informationen sind für erfolgreichen Anbau ZWINGEND?

Priorisiert nach **Ausfall-Effekt** (was passiert, wenn die Information fehlt/falsch ist), nicht nach Mess-Eleganz.

### 5.1 Klasse A — ZWINGEND erfolgskritisch (Fehlen ⇒ Tod oder Sicherheits-/Rechtsschaden)

| # | Parameter | Skala (Anfänger-tauglich) | Warum kritisch |
|---|---|---|---|
| A1 | **Lichtbedarf** | Vollsonne ≥6 h / Halbschatten 3–6 h / Schatten <3 h | Energie-Input; falsche Zuordnung → Vergeilung oder Verbrennung |
| A2 | **Wasserbedarf + Regime** | niedrig/mittel/hoch + „antrocknen lassen vs. feucht halten" | **Überwässerung = häufigste Todesursache** (Wurzelfäule); Symptom wird mit Trockenheit verwechselt |
| A3 | **Frosttoleranz / Winterhärtezone** | °C-Untergrenze + Zone | ein Frostereignis tötet frostempfindliche Pflanzen vollständig |
| A4 | **Standortbindung** | Zimmer / Freiland / Gewächshaus | falsche Grundzuordnung macht alle anderen Parameter wirkungslos |
| A5 | **Toxizität / Giftigkeit** | Warnbadge Katze/Hund/Kind (+ RHS-Schweregrad A/B/C) | **einziger Parameter, dessen Ausfall Menschen/Tiere statt nur die Pflanze schädigt** (z. B. Lilien tödlich für Katzen) |
| A6 | **Substrat-Drainage** | gut dräniert / durchschnittlich / staunass | Verstärker von A2 — auch korrektes Gießen tötet ohne Drainage |

### 5.2 Klasse B — WICHTIG (Fehlen ⇒ deutlich schlechtere Ergebnisse, aber Überleben)

Optimaler Temperaturbereich + Hitzestress (B1) · **Boden-pH** (B2, Zielband 6–7) · **Nährstoff-/Zehrer-Klasse + phasenabhängige NPK** (B3) · **Endgröße & Pflanzabstand** (B4) · Topf-/Wurzelraum + Umtopfen (B5) · Aussaat-/Pflanzparameter (B6) · Keimtemperatur (B7) · **Schädlinge/Krankheiten + IPM** (B8) · Invasivität (B9, Freiland) · **Photoperiodismus** (B10, blühabhängige Arten) · Pflegeeingriffe Schnitt/Stützen/Ausgeizen (B11).

### 5.3 Klasse C — OPTIONAL / FORTGESCHRITTEN (Optimierung / Controlled-Environment)

Luftfeuchte % (C1) · **VPD** kPa (C2) · **PPFD/DLI** (C3, nur Kunstlicht) · EC/Salzgehalt (C4) · organischer Bodenanteil (C5) · Sekundär-/Mikronährstoff-Diagnostik (C6).

> **Sicherheits-Sonderregel:** A5 (Toxizität) ist der einzige Parameter, der **unabhängig von der Erfahrungsstufe** prominent und nicht ausblendbar sein muss — er schützt Menschen/Tiere, nicht die Pflanze.
>
> Quellen: RHS (Watering/Shade/Hardiness/Nutrient Deficiencies); USDA/ARS; UC/UMD/OSU/Penn State/Alabama Extension; ASPCA (Toxic Plants); EPA; CSIRO-Metaanalyse (Topfgröße); peer-reviewt.

---

## 6. Erfahrungsstufen-Mapping (REQ-021)

Prinzip **Progressive Disclosure**: Anfänger sehen genau das Minimum über Leben/Tod und Sicherheit (Klasse A, qualitative Skalen); jede höhere Stufe ergänzt Parameter und schaltet feinere (numerische) Skalen frei.

| Stufe | Sichtbare Parameter | Skalen |
|---|---|---|
| **Anfänger** | gesamte Klasse A + Endgröße (B4) + ggf. Saattiefe/Pflanzzeit (B6) | qualitativ (Symbole, Stufen) |
| **Fortgeschritten** | + gesamte Klasse B | numerisch (°C-Bereiche, pH, NPK-Verhältnis) |
| **Experte** | + gesamte Klasse C | volle Messtechnik (kPa, µmol/m²/s, dS/m) |

A5 (Toxizität) **immer sichtbar**, stufenunabhängig.

---

## 7. Konsolidiertes Stammdaten-Feldmodell (Dimension → Feld → Status)

Abgleich der vier Dimensionen + Querschnitt mit dem **realen** kamerplanter-Modell (REQ-001/-003/-007/-008/-017/-022). Status: ✅ vorhanden · ⚠ vorhanden, aber Lücke/Refinement · ❌ fehlt.

| Dimension | Eigenschaft | Bestehendes Feld | Status |
|---|---|---|---|
| **1A** Nutzungstyp | mehrwertig | `Species.traits: list[str]` | ✅ |
| **1A** Gemüse-Untergruppe | nach essbarem Teil | — (nur generisch in `traits`) | ⚠ ggf. eigenes Vokabular |
| **1B** Wuchsform | geschlossenes Enum | `Species.growth_habit` (5 Werte) | ⚠ zu eng (E1) |
| **1C** Standort | indoor/outdoor/GH/Kübel | über `care_style` / Standort impliziert | ⚠ explizites Feld prüfen |
| **1C** Winterhärte | Zone + Sensitivität | `hardiness_zones`, `frost_sensitivity`, `hardiness_detail` | ✅ |
| **1D** Familie/Rotation | erstklassiges Lookup | `BotanicalFamily` (+ `rotation_category`, `nitrogen_fixing`) | ✅ |
| **2** Lebensdauer | annual/biennial/perennial | `LifecycleConfig.cycle_type` | ✅ |
| **2** „in Kultur"-Split | botanisch ≠ Praxis | — | ❌ (E2) |
| **2** Blüh-Strategie | monokarp/polykarp | — | ❌ (E3) |
| **2** Blattverhalten | sommer-/winter-/immergrün | — | ❌ optional |
| **2** Dormanz/Vernalisation | Flags | `dormancy_required`, `vernalization_required` | ✅ |
| **3** Vermehrungsmethoden | Mehrfach + je-Methode-Parameter | `propagation_methods` + flache `propagation_months`/`notes` | ⚠ Parameter pro Methode (E4) |
| **3** Samenfest/F1 | Sortenfeld | `Cultivar.seed_type` | ✅ |
| **4** Erntemuster | single/continuous/perennial | `harvest_type: partial/final/continuous` | ⚠ Semantik schärfen (E5) |
| **4** geernteter Teil | Enum | über `harvest_indicators` impliziert | ⚠ explizites Feld prüfen |
| **4** DTM + Bezugspunkt | Tage + Referenz | `harvest_indicators` (days), kein `dtm_reference` | ❌ Bezugspunkt (E5) |
| **4** Klimakterik | 3-wertig | — | ❌ (E5) |
| **4** Post-Harvest | Curing/Lagerung | Protokolle `drying/curing/aging/...` | ✅ |
| **4** PHI/Karenz | mittel×kultur | über IPM (REQ-010) | ✅ (an Behandlung) |
| **5/A** Anbau-Kernparameter | Licht/Wasser/Frost/Gift/Drainage | `care_style`, Frost-Felder, `toxicity` | ✅ größtenteils |
| **5/B** pH, Zehrer, Photoperiode | numerisch | `soil_ph_preference`, `nutrient_demand_level`, `photoperiod_type` | ✅ |

---

## 8. UI-Implikationen (REQ-021)

- **Nutzungstyp = essbar** blendet **Ernte-Felder** ein; **= Zier** blendet sie aus → datengetriebene Formulare statt fixer Masken.
- **Wuchsform** steuert kontextuelle Felder: verholzt → Rückschnitt; Kletterpflanze → Stütze/Rankhilfe; Geophyt → Pflanztiefe/Einzug; Sukkulente → seltene Bewässerung als Default; Wasserpflanze → Wasserzone.
- **Lebensdauer** steuert das Phasen-/Zyklusmodell: einjährig = linearer Einmal-Ablauf; zweijährig = zwei Saisons mit Überwinterungs-Schritt + Modus „Ernte vs. Samengewinnung"; mehrjährig = wiederkehrende Jahreszyklen + Überwinterungs-Hinweise; `monokarp` = Terminal-Ereignis.
- **Vermehrung**: Mehrfachauswahl-Widget + je Methode aufklappbares Parameterpanel (Monats-Mehrfachauswahl, da Zeitfenster oft zweigeteilt sind: Frühjahr **und** Herbst).
- **Ernte**: `harvest_pattern` und `harvested_part` als getrennte Eingaben; Reifekriterien als Korridore (`_min`/`_max`), nicht als Schwellen.
- **Auspflanz-Hinweis** „nach Eisheiligen/letztem Frost" **nur** wenn `frostempfindlich` — abgeleitet aus dem orthogonalen Frost-Feld, nicht aus der Lebensdauer.
- **Toxizitäts-Badge** immer sichtbar (Sicherheits-Sonderregel).

---

## 9. Lücken & Empfehlungen gegenüber dem bestehenden Modell

Priorisiert; jede Empfehlung ist durch §1–§5 fachlich belegt.

- **E1 — `growth_habit`-Enum erweitern (mittel).** Heute 5 Werte (`herb/shrub/tree/vine/groundcover`). Ergänzen: `grass`, `succulent`, `bulb_geophyte`, `fern`, `aquatic`, `epiphyte`, `subshrub`. Begründung: kontextuelle Pflege-Felder (Bewässerung, Stütze, Pflanztiefe) hängen daran.
- **E2 — Lebensdauer-Split „botanisch vs. in Kultur" (hoch).** Zweites Feld neben `cycle_type`, das die *Kultur-Praxis* abbildet (tender perennial = botanisch mehrjährig, in Kultur einjährig). Treibt korrekte Überwinterungs- und Saison-Ende-Hinweise.
- **E3 — Blüh-Strategie `monocarp | polycarp` (niedrig–mittel).** Für „blüht einmal, stirbt danach"-Arten (Agave, viele Bambusse), die sonst fälschlich als dauerhaft mehrjährig erscheinen.
- **E4 — Vermehrungs-Parameter pro Methode (hoch, branch-aktuell).** `propagation_months`/`propagation_notes` von der Art an die **Methode** koppeln (Liste von `{method, months, notes}`). Betrifft direkt `feat/species-propagation-methods`. Falls die flache Triade bleiben muss: als **indexgekoppelte parallele Listen** gleicher Länge dokumentieren (fragiler).
- **E5 — Ernte-Semantik schärfen (mittel).** (a) `harvest_type`-Werte gegen das Muster `single | continuous | perennial` prüfen (heute `partial/final/continuous` — `partial/final` beschreibt den Einzel-Erntevorgang, nicht das Lebensmuster). (b) `dtm_reference: direct_seed | transplant` ergänzen. (c) `climacteric: climacteric | non_climacteric | atypical` ergänzen (Nachreif-/Lagerlogik).
- **E6 — Quelle/Methode pro Wert (niedrig, querschnittlich).** Wegen der in §10 dokumentierten Quellenwidersprüche: bei strittigen Werten (Klimakterik, GDD-Basistemperatur, Standjahre) ein optionales Quell-/Methodenfeld; pro Sorte überschreibbar.

---

## 10. Verifikation, Unsicherheiten & Quellenabweichungen

**Methodik:** Recherche über sechs parallele Stränge (Klassifikation, Lebensdauer, Vermehrung, Ernte, Anbau-Anforderungen, Bestandsmodell), jede load-bearing Aussage gegen ≥2 unabhängige seriöse Quellen geprüft; Direkt-Fetch der Primäranker (RHS-Härte-PDF, RHS-Crop-Rotation, USDA/ARS, DWD, NC State Handbook, Pflanzenforschung.de). Quellenwidersprüche wurden bewusst **nicht** geglättet.

**Echte, verifizierte Quellenabweichungen (selbst eine Modellierungs-Anforderung):**

1. **Rettich/Rübe**: Wurzelgemüse (Verwendung) vs. Brassica (Fruchtfolge) — verschiedene Felder, dürfen widersprechen.
2. **Obst vs. Gemüse**: botanisch vs. kulinarisch (Tomate, Rhabarber; *Nix v. Hedden* 1893) — kulinarische Konvention, nicht als botanische Wahrheit speichern.
3. **Zwiebelfamilie** *Alliaceae* vs. *Amaryllidaceae* — Familien-Lookup sollte Umschreibungs-Synonyme kennen.
4. **Fruchtfolge-Intervall** 2 vs. 3–4 vs. 5+ Jahre — konfigurierbar, nicht hartcodiert.
5. **USDA-Zone ≠ RHS-Rating** (gemitteltes vs. absolutes Minimum) — getrennt speichern, nicht umrechnen.
6. **Klimakterik** ist ein Kontinuum: MSU listet Blaubeere/Honigmelone als klimakterisch entgegen der Mehrheit; Feige/Paprika/Pflaume sind Grenzfälle → dritter Wert `atypical` nötig.
7. **DTM-Bezugspunkt** uneinheitlich (Johnny's ab Direktsaat vs. Industrie ab Auspflanzen) → expliziter Bezugspunkt-Schalter.
8. **GDD-Basistemperaturen** US- vs. DE-Modellkonventionen (Erbse 4,4/1,8 °C; Mais 10/6 °C) → modellabhängig, mit Quelle speichern.
9. **Standjahre Mehrjähriger** sind Zählkonventionen mit Spannen → als Korridor (`_min`/`_max`), nicht als Fixwert.
10. **Agave/Bambus monokarp** nur auf Rosetten-/Art-Ebene bzw. „die meisten, nicht alle" → vorsichtig formulieren.

**Methodische Einschränkungen:** UC-Davis-Postharvest-Volltexte waren teils Cloudflare/403-blockiert (Curing-/Klimakterik-Werte über zitierende Extension-Quellen + Snippets gedoppelt, nicht alle verbatim). Deutschsprachige Behördenquellen (BZfE/LfL/JKI) sind dünner vertreten als RHS/US-Extension; die Mechanik ist sprach-/länderunabhängig, aber **regionale** Frost-/Aussaattermine und **Invasivitätslisten** sollten gegen DE/EU-Quellen (LfL, regionale Neophyten-Listen) ergänzt werden. Einige numerische Detailwerte (PPFD-Tabellen, VPD-Phasenbänder) stammen aus kommerziellen Grow-Quellen — als Orientierung tragfähig, für Produktionsentscheidungen gegen Extension-Primärquellen gegenprüfen.

---

## 11. Primärquellen (Auswahl)

- **RHS** — Plant types, Hardiness Rating (PDF), Crop Rotation, Propagation, F1 hybrids, Watering, Nutrient Deficiencies, Shade Gardening
- **USDA/ARS** — 2023 Plant Hardiness Zone Map; **USDA PLANTS** growth-habit; **USDA NRCS** Soil Texture
- **DWD** — Winterhärtezonen (Heinze & Schreiber 1984)
- **University Extension Services** — NC State (Extension Gardener Handbook Kap. 13), Penn State, UMN, Iowa State, Oregon State, UC Davis Postharvest, Cornell, UC Master Gardener/IPM, Alabama, Maryland, Illinois, MSU, Missouri
- **ASPCA** — Toxic & Non-Toxic Plants (Cats/Dogs)
- **BVL** (PHI/Wartezeit) · **BZfE** · **LfL Bayern** · **FAO** · **EPA**
- **Peer-reviewt** — JXB, BMC Plant Biology, PMC (Dormanz, Klimakterik, Triploidie); CSIRO (Topfgröße-Metaanalyse)
- **Nomenklatur** — ICN, ICNCP
- **Referenz/Lexika** — Britannica, Wikipedia (DE/EN) als Sekundär-Korroboration

---

*Dieses Dokument ist art-übergreifend und sorten-neutral. Konkrete Pflanzen dienen nur der Illustration. Sortenspezifische Werte gehören in die Per-Art-Steckbriefe unter `spec/knowledge/plants/` bzw. an die `Cultivar`-Ebene.*
