# UI-NFR-020: Anbau-Zeitachse „Aussaat, Ernte & Blüte"

```yaml
ID: UI-NFR-020
Titel: Pflanzentyp-adaptive Monats-Zeitachse für Vermehrung, Aussaat, Wachstum, Ernte und Blüte
Kategorie: UI-Verhalten
Unterkategorie: Datenvisualisierung, Timeline, Stammdaten, Progressive Disclosure
Technologie: React, TypeScript, MUI, CSS-Grid
Status: Entwurf
Priorität: Hoch
Version: 1.0
Datum: 2026-06-15
Tags: [timeline, gantt, sowing, harvest, bloom, propagation, plant-type, seasonal, perennial, progressive-disclosure]
Abhängigkeiten: [REQ-001, REQ-015, REQ-021, UI-NFR-002, UI-NFR-006, UI-NFR-007, UI-NFR-011, UI-NFR-016]
Fachliche Grundlage: spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md
Betroffene Module: [Frontend]
Implementierende Komponente: src/frontend/src/pages/stammdaten/GrowingPeriodsSection.tsx
```

## Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.0 | 2026-06-15 | Erstfassung. Spezifiziert das „Aussaat, Ernte & Blüte"-Timetable auf der Arten-Detailseite (Tab „Aussaat & Ernte"): Spuren-Modell, pflanzentyp-adaptive Sichtbarkeit, Read-/Edit-Verhalten, Kontext-Hinweise, Erfahrungsstufen. Fachlich abgeleitet aus `PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` (vier orthogonale Pflanzendimensionen). |

---

## 1. Business Case

### 1.1 Zweck

Die Arten-Detailseite (`SpeciesDetailPage`, Tab „Aussaat & Ernte") enthält eine **Monats-Zeitachse**, die auf einen Blick zeigt, **wann im Jahr** die wichtigen gärtnerischen Tätigkeiten einer Pflanzenart stattfinden: Vermehrung, Aussaat, Wachstum, Ernte und Blüte. Die Zeitachse ist zugleich **Anzeige** (Nachschlagen) und **Editor** (Pflege der Stammdaten-Monate).

Das Kernproblem: Pflanzenarten sind **nicht gleichförmig**. Ein einjähriges Fruchtgemüse (Tomate), eine mehrjährige Kräuterstaude (Schnittlauch), eine rein vegetativ vermehrte Zimmer-Zierpflanze (Lippenstiftpflanze) und ein Beerenstrauch mit Juvenilphase haben **grundverschiedene** relevante Informationen. Eine starre Darstellung, die für alle Arten dieselben Spuren mit derselben Logik zeigt, erzeugt entweder leere, verwirrende Zeilen oder fachliche Widersprüche (z.B. „Ernte vor abgeschlossener Aussaat"). Diese UI-NFR definiert, **wie die Zeitachse sich an den Pflanzentyp anpasst**, damit jeder Nutzer genau die für *seine* Pflanze relevanten Informationen bestmöglich dargestellt bekommt.

### 1.2 User Stories

**Als** Gemüsegärtner mit einjährigen Kulturen
**möchte ich** Aussaat-, Wachstums- und Erntefenster als klare lineare Abfolge sehen,
**um** Vorkultur, Auspflanzung und Erntebeginn zu planen.

**Als** Stauden-/Kräutergärtner mit mehrjährigen Pflanzen
**möchte ich** verstehen, dass sich Aussaat (einmalige Erstanlage) und Ernte/Blüte (jährlich wiederkehrend an der etablierten Pflanze) überschneiden dürfen,
**um** die scheinbar widersprüchlichen Zeiträume nicht als Datenfehler misszuverstehen.

**Als** Zimmerpflanzen-Besitzer ohne Erntebezug
**möchte ich** die Vermehrungszeit und die Blütezeit sehen, aber **nicht** mit leeren Aussaat-/Ernte-Zeilen verwirrt werden,
**um** den besten Zeitpunkt für Stecklinge zu finden.

**Als** Obst-/Beeren-Gärtner mit Juvenilphase
**möchte ich** erkennen, dass die Ernte erst nach mehreren Standjahren beginnt,
**um** realistische Erwartungen an den Ertragsbeginn zu haben.

**Als** Anfänger
**möchte ich** nur die wenigen für mich relevanten Spuren in qualitativer Form sehen,
**um** nicht von einer dichten Expertenansicht überfordert zu werden.

### 1.3 Abgrenzung

| Thema | Zuständige Spezifikation |
|---|---|
| Generisches visuelles Vokabular für Phasen-/Zyklus-Visualisierungen (Phasenfarben, Tooltip-Regeln, Maskottchen, Gantt auf Kalenderseite, Saison-Ring) | **UI-NFR-016** |
| **Diese** Komponente: Anbau-Zeitachse auf der Arten-Detailseite, mit pflanzentyp-adaptiver Spur-Logik | **UI-NFR-020** (dieses Dokument) |
| Bearbeitung der Vermehrungs-Methoden/Monate/Hinweise in der „Vermehrung"-Karte oberhalb der Zeitachse | REQ-001, UI-NFR-018 (Herkunft) |
| Stammdatenfelder und ihre Semantik (`propagation_months`, `direct_sow_months`, `harvest_type`, `cycle_type`, …) | REQ-001 |
| Sichtbarkeit nach Erfahrungsstufe (Progressive Disclosure) | REQ-021, §6 von `PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` |

UI-NFR-020 ist eine **Spezialisierung** der in UI-NFR-016 §4.3 (V-003 Horizontaler Gantt) festgelegten Gantt-Grundform. Bei Konflikten zu Farbpalette, Tooltips, Responsive und Barrierefreiheit gilt UI-NFR-016; die pflanzentyp-adaptive Logik und das Spuren-Modell sind exklusiv in UI-NFR-020 geregelt.

---

## 2. Datengrundlage

Die Zeitachse liest ausschließlich vorhandene `Species`-Felder (REQ-001) bzw. die daraus synthetisierten `GrowingPeriod`-Einträge. Sie erfindet keine Daten.

| Spur | Primärfeld(er) | Herkunft |
|---|---|---|
| Vermehrung | `propagation_months: list[int]` | Species (global) |
| Aussaat | `direct_sow_months: list[int]`, abgeleitet aus `sowing_indoor_weeks_before_last_frost`, `sowing_outdoor_after_last_frost_days` | GrowingPeriod / Species-Legacy |
| Wachstum | `growth_months: list[int]` | GrowingPeriod |
| Ernte | `harvest_months: list[int]`, `harvest_from_year` | GrowingPeriod |
| Blüte | `bloom_months: list[int]`, `bloom_from_year` | GrowingPeriod |

Steuernde Eigenschaften für die **adaptive** Darstellung (vier Dimensionen aus `PFLANZEN-EIGENSCHAFTEN-REFERENZ.md`):

| Steuernde Eigenschaft | Feld | Dimension | Wirkung auf die Zeitachse |
|---|---|---|---|
| Nutzungstyp (essbar/Zier) | `Species.allows_harvest`, `Species.traits` (`edible`/`ornamental`) | D1A | Sichtbarkeit der Ernte-Spur |
| Wuchsform | `Species.growth_habit` | D1B | Spur-Kontext (z.B. Geophyt → Knollen/Einzug) |
| Standortbindung | abgeleitet (`care_style`, `frost_sensitivity`, `plant_category`) | D1C | Saison-/Frost-Bezug, aktueller-Monat-Marker |
| Lebensdauer | `LifecycleConfig.cycle_type` (`annual`/`biennial`/`perennial`) | D2 | Grundstruktur (linear vs. wiederkehrend) |
| Vermehrungsart | `Species.propagation_methods` | D3 | Eigenständigkeit der Vermehrungs-Spur vs. Aussaat |
| Erntemuster | `harvest_type` (`partial`/`final`/`continuous`) | D4 | Balkendarstellung der Ernte; Standjahr-Hinweis |

> **R-001 (MUSS):** Die Zeitachse MUSS jede Spur ausschließlich aus den oben genannten, gepflegten Feldern speisen. Fehlende Felddaten führen zu einer leeren (nicht zu einer erfundenen) Spur — vorbehaltlich der Sichtbarkeitsregeln in §4.

> **R-002 (SOLL):** Wenn `cycle_type` über `LifecycleConfig` nicht ermittelbar ist (heute häufig `null`), SOLL die Komponente die Lebensdauer **heuristisch** aus den Daten ableiten (z.B. Überlappung Aussaat ∩ Ernte/Blüte ⇒ wahrscheinlich perennierend) und konservativ darstellen, statt eine falsche lineare Sequenz zu erzwingen. Die Heuristik ist explizit als solche zu dokumentieren; die saubere Lösung ist E2 (§8).

---

## 3. Spuren-Modell (Grunddarstellung)

Die Zeitachse ist ein **CSS-Grid** mit einer Beschriftungsspalte und zwölf Monatsspalten (Jan–Dez). Innerhalb eines Anbauzeitraums (`GrowingPeriod`) wird je **Spur** eine Zeile gerendert. Eine Spur stellt die zu ihren Monaten gehörenden zusammenhängenden Bereiche als horizontale Balken dar.

### 3.1 Spuren-Katalog und Farben

| Spur | Schlüssel | Farbe (Hex) | Bedeutung | Editierbar |
|---|---|---|---|---|
| Vermehrung | `propagation` | Teal `#26A69A` | Beste Monate für vegetative/generative Vermehrung | **Nein** (read-only; Edit in der Vermehrungs-Karte) |
| Aussaat | `sow` | Grün `#66BB6A` | Direktsaat-/Aussaatfenster | Ja (Drag) |
| Wachstum | `growth` | Blau `#42A5F5` | Aktive Wachstumsphase | Ja (Drag) |
| Ernte | `harvest` | Orange `#FF8F00` | Erntefenster | Ja (Drag) |
| Blüte | `bloom` | Lila `#AB47BC` | Blütezeit | Ja (Drag) |

> **R-003 (MUSS):** Die Spur-Farben MÜSSEN über alle Arten und über Light-/Dark-Mode konsistent sein und mindestens 3:1-Kontrast gegen den Hintergrund bieten (WCAG AA für nicht-textuelle Elemente, vgl. UI-NFR-016 R-009).

> **R-004 (MUSS):** Spur-Farben sind **Aktivitäts-Farben** und eine **andere Achse** als die Lebenszyklus-Phasenfarben aus UI-NFR-016 §3.2 (germination/seedling/…). Sie dürfen nicht miteinander verwechselt oder vermischt werden; eine Aktivitäts-Spur ist kein Lebenszyklus-Phasenbalken.

> **R-005 (MUSS):** Jede Spur MUSS links einen farbigen Indikatorpunkt und ein lokalisiertes Label tragen (`pages.species.barKind.*`). Der laufende Kalendermonat MUSS in der Monatsachse hervorgehoben werden.

### 3.2 Read-only-Spuren

> **R-006 (MUSS):** Die Vermehrungs-Spur (`propagation`) ist **read-only**: keine Drag-Anfasser, keine Pointer-Editier-Listener, kein `touchAction: none`. Sie spiegelt live die in der „Vermehrung"-Karte gepflegten `propagation_months`.

> **R-007 (MUSS):** Read-only-Spuren MÜSSEN für Maus- und Screenreader-Nutzer als „nur Anzeige" erkennbar sein — über einen Tooltip/aria-Hinweis am Spur-Label (`pages.species.barKindReadOnlyHint`, z.B. „Nur Anzeige — in der Vermehrung-Karte oben bearbeiten"). Damit wird Frustration durch vergebliche Drag-Versuche vermieden.

---

## 4. Pflanzentyp-adaptive Spur-Sichtbarkeit (Kern dieser UI-NFR)

Nicht jede Spur ist für jede Pflanze relevant. Eine leere Ernte-Zeile bei einer Zierpflanze oder eine Aussaat-Zeile bei einer ausschließlich durch Teilung vermehrten Staude ist **kein neutraler Leerstand, sondern eine Fehlinformation** („wird nie geerntet" / „muss gesät werden"). Die Sichtbarkeit jeder Spur richtet sich nach den vier Dimensionen.

### 4.1 Ernte-Spur (Dimension 1A — Nutzungstyp)

> **R-010 (MUSS):** Die Ernte-Spur MUSS ausgeblendet werden, wenn die Art **nicht erntbar** ist (`allows_harvest == false` bzw. Nutzungstyp rein `ornamental` ohne `edible`). Eine Zierpflanze zeigt **keine** Ernte-Zeile.

> **R-011 (MUSS):** Ist die Art erntbar (`allows_harvest == true`), MUSS die Ernte-Spur sichtbar sein — auch wenn `harvest_months` (noch) leer ist (dann als leere, aber beschriftete Zeile, weil hier ein Pflege-Auftrag steckt).

> **R-012 (SOLL):** Der Spalten-/Sektionstitel MUSS die tatsächlich gezeigten Hauptspuren benennen. Für erntbare Arten lautet er sinngemäß „Aussaat, Ernte & Blüte"; für reine Zierpflanzen SOLL „Ernte" im Titel entfallen (z.B. „Aussaat & Blüte" oder „Vermehrung & Blüte"), damit der Titel nicht suggeriert, es gäbe eine Ernte, die fehlt. *(Begründung: Ein Titel, der die Ernte nennt, während keine Ernte-Spur existiert, wirkt widersprüchlich.)*

### 4.2 Aussaat-Spur (Dimension 3 — Vermehrung)

> **R-013 (MUSS):** Enthält `propagation_methods` **keine** generative Methode (`seed`) — die Art wird also ausschließlich vegetativ vermehrt (Steckling/Teilung/Offset/…) — und sind keine Aussaatmonate gepflegt, so MUSS die Aussaat-Spur ausgeblendet werden. Die Vermehrungs-Spur (`propagation`) übernimmt die zeitliche Information.

> **R-014 (SOLL):** Enthält `propagation_methods` sowohl `seed` als auch vegetative Methoden, SOLLEN **beide** Spuren sichtbar sein (Aussaat = generativ, Vermehrung = vegetativ), damit der Nutzer den Unterschied erkennt (vgl. `PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` §3 „generativ vs. vegetativ").

> **R-015 (KANN):** Decken sich `propagation_months` für eine rein generativ vermehrte Art weitgehend mit `direct_sow_months`, KANN die Vermehrungs-Spur zugunsten der Aussaat-Spur entfallen, um Redundanz zu vermeiden.

### 4.3 Grundstruktur nach Lebensdauer (Dimension 2)

> **R-016 (MUSS):** Die Grunddarstellung MUSS von der Lebensdauer (`cycle_type`, ersatzweise Heuristik nach R-002) abhängen:
>
> | Lebensdauer | Darstellung | Besonderheit |
> |---|---|---|
> | **Einjährig** (`annual`) | lineare Einmal-Sequenz Aussaat → Wachstum → Ernte/Blüte innerhalb **einer** Saison | keine Überlappungs-Erwartung; widersprüchliche Überlappungen sind hier echte Datenfehler |
> | **Zweijährig** (`biennial`) | zwei Saisons mit Überwinterungsschritt; Jahr 1 vegetativ/Ernte-Speicherorgan, Jahr 2 Blüte/Samengewinnung | Modus-Hinweis „Ernte (Jahr 1) vs. Samengewinnung (Jahr 2)" (vgl. §2.3 Referenz) |
> | **Mehrjährig** (`perennial`) | wiederkehrender Jahreszyklus; Aussaat = einmalige Erstanlage, Ernte/Blüte = jährlich an der etablierten Pflanze | Überlappung Aussaat ∩ Ernte/Blüte ist **normal**, kein Fehler (R-020) |

> **R-017 (SOLL):** Für **mehrjährige** Arten SOLL die Zeitachse als wiederkehrender Jahreszyklus lesbar sein (keine erzwungene „erst säen, dann ernten"-Sequenzierung/Clipping der Rohmonate). Die hinterlegten Monatsdaten sind die einzige Quelle der Wahrheit; es darf keine zweite, daraus „berechnete" und dazu widersprüchliche Zeitachse geben.

> **R-018 (KANN):** Für mehrjährige Arten mit ausgeprägter Saisonalität KANN ergänzend die Ring-Darstellung (UI-NFR-016 V-006 „Saisonaler Zyklus-Ring") angeboten werden. Die lineare Monatsachse bleibt die Grundform.

### 4.4 Standort/Frost (Dimension 1C)

> **R-019 (SOLL):** Saison- und Frostbezug SOLLEN nur für **freilandgebundene** Arten dargestellt werden. Für reine **Zimmerpflanzen** (indoor) entfallen Frost-/Eisheiligen-bezogene Auspflanz-Hinweise; die Monatsachse dient dann nur als ganzjähriger Orientierungsrahmen (Vermehrung/Blüte). Der Auspflanz-Hinweis „nach letztem Frost/Eisheiligen" wird **ausschließlich** aus `frost_sensitivity == tender/half_hardy` abgeleitet, **nicht** aus der Lebensdauer (vgl. Referenz §8).

---

## 5. Kontext-Hinweise (Erklärungen statt Widersprüche)

> **R-020 (MUSS):** Überschneiden sich Aussaatmonate mit Ernte-/Blütemonaten, MUSS oberhalb der Zeitachse ein erklärender Hinweis eingeblendet werden (`pages.species.sowHarvestOverlapHint`), der die Überlappung als normal für mehrjährige Pflanzen einordnet („Die Aussaat dient nur der Erstanlage; geerntet und geblüht wird an der etablierten Pflanze"). So wird die fachlich korrekte Überlappung nicht als Inkonsistenz fehlgedeutet.

> **R-021 (SOLL):** Erntemuster (Dimension 4, `harvest_type`) SOLL die Ernte-Darstellung differenzieren:
>
> | `harvest_type` | Erntemuster | Darstellung |
> |---|---|---|
> | `final` | Einmalernte (determiniert) | punktueller/schmaler Balken; Tooltip „Einmalernte" |
> | `continuous` | Durchpflück-/Mehrfachernte (indeterminiert) | durchgehender breiter Balken über das Fenster |
> | `partial` | Teil-/iterative Ernte | durchgehender Balken; Tooltip „mehrfach beerntbar" |

> **R-022 (SOLL):** Bei mehrjährig-wiederkehrender Ernte mit **Juvenilphase** (`harvest_from_year > 1` bzw. `Cultivar.years_to_first_harvest`) SOLL die Ernte-Spur einen Standjahr-Hinweis tragen (z.B. Chip „ab {n}. Standjahr"), damit der verzögerte Ertragsbeginn (Spargel ab Jahr 4, Beerenstrauch) sichtbar wird (Referenz §4.1).

> **R-023 (KANN):** Für **monokarpe** Arten (blüht einmal, stirbt danach; Referenz §2.2) KANN die Blüte-Spur als terminales Ereignis gekennzeichnet werden (Hinweis „blüht einmal, danach Absterben"). Erfordert das noch fehlende Feld E3 (§8).

> **R-024 (MUSS):** Sicherheits-Sonderregel: Ist die Art giftig (`toxicity`), MUSS der Toxizitäts-Hinweis erfahrungsstufen-**unabhängig** und unausblendbar sichtbar sein (vgl. Referenz §5.1 A5). Die Zeitachse darf diese Information nicht verdrängen (Darstellung primär über UI-NFR-018/Steckbrief; hier nur Nicht-Verdrängungs-Gebot).

---

## 6. Erfahrungsstufen (REQ-021 · Progressive Disclosure)

Mapping nach `PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` §6.

> **R-030 (SOLL):** Die Spur-Auswahl und der Detailgrad SOLLEN sich an der Erfahrungsstufe orientieren:
>
> | Stufe | Sichtbare Spuren / Detail |
> |---|---|
> | **Anfänger** | Reduziert auf die für die Art relevanten Kern-Spuren (z.B. Nutzpflanze: Aussaat, Ernte; Zierpflanze: Vermehrung, Blüte). Qualitativ, ohne Editier-Anfasser im Vordergrund. |
> | **Fortgeschritten** | Alle relevanten Spuren inkl. Wachstum, Vermehrung; Drag-Bearbeitung der editierbaren Spuren; Standjahr-/Erntemuster-Hinweise. |
> | **Experte** | Zusätzlich numerische Detailparameter (Vorkulturwochen, Tage-nach-letztem-Frost) im aufklappbaren Detailbereich des Anbauzeitraums. |

> **R-031 (MUSS):** Die Edit-Bearbeitung der Vermehrungsdaten erfolgt zentral in der „Vermehrung"-Karte (Lese-/Bearbeiten-Umschalter), **nicht** in der Zeitachse. Es darf **keine zweite, widersprüchliche** Editier-Stelle für dieselben Daten geben (Single Source of Edit).

---

## 7. Layout, Interaktion, Responsive & Barrierefreiheit

> **R-040 (MUSS):** Die Zeitachse MUSS als horizontal scrollbares CSS-Grid umgesetzt sein (eine Beschriftungsspalte + 12 Monatsspalten). Auf schmalen Viewports MUSS horizontales Scrollen ohne Layout-Bruch möglich sein (vgl. UI-NFR-001, UI-NFR-016 §5).

> **R-041 (MUSS):** Editierbare Balken MÜSSEN per Drag an den Enden anpassbar sein; Drag-Anfasser MÜSSEN ein Mindest-Tippziel gemäß UI-NFR-002 (44×44px Touch) bieten.

> **R-042 (MUSS):** Jeder Balken MUSS bei Hover/Touch einen Tooltip mit Spur-Name und Monatsbereich anzeigen (vgl. UI-NFR-016 R-016).

> **R-043 (MUSS):** Alle Beschriftungen, Hinweise und Tooltips MÜSSEN über i18n (de/en) lokalisiert sein (UI-NFR-007); keine hartkodierten Strings. Monatsnamen über `pages.species.months.*`, Spur-Labels über `pages.species.barKind.*`.

> **R-044 (MUSS):** Interaktive und read-only Elemente MÜSSEN korrekte ARIA-Semantik tragen (UI-NFR-002): editierbare Anfasser fokussier- und tastaturbedienbar; read-only Spuren als nicht-editierbar ausgewiesen; Moduswechsel (Lese-/Bearbeiten der Vermehrungs-Karte) über `aria-live` angekündigt.

> **R-045 (SOLL):** Fachbegriffe in Hinweistexten (z.B. „Vernalisation", „determiniert", „Standjahr") SOLLEN gemäß UI-NFR-011 mit einer kurzen Erklärung versehen werden.

---

## 8. Bekannte Lücken & Abhängigkeiten

Diese UI-NFR ist heute teilweise durch vorhandene Felder bedienbar; die folgenden Modell-Lücken (aus `PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` §9) begrenzen die volle Adaptivität und sind die empfohlenen Voraussetzungen:

| Lücke | Auswirkung auf die Zeitachse | Referenz |
|---|---|---|
| **E2** — Lebensdauer-Split „botanisch vs. in Kultur" | „tender perennial" (Tomate) korrekt als in-Kultur-einjährig **linear** darstellen, obwohl botanisch mehrjährig. Ohne E2 nur heuristisch (R-002). | Referenz §9 E2 |
| **E4** — Vermehrungs-Parameter **pro Methode** (`{method, months, notes}`) | Die Vermehrungs-Spur kann derzeit nur **eine** globale Monatsmenge zeigen. Methoden mit getrennten Fenstern (Weichholzsteckling Mai–Juli *vs.* Teilung Herbst) lassen sich nicht differenziert darstellen. | Referenz §9 E4 (branch-aktuell) |
| **E5** — Ernte-Semantik schärfen (`harvest_type` als Lebensmuster, `dtm_reference`, Klimakterik) | R-021 (Erntemuster-Differenzierung) und R-022 (Standjahr) brauchen ein sauberes Lebensmuster-Feld statt `partial/final/continuous`. | Referenz §9 E5 |
| **E3** — Blüh-Strategie `monocarp/polycarp` | R-023 (terminale Blüte) nur mit E3 zuverlässig. | Referenz §9 E3 |
| **E1** — `growth_habit`-Enum erweitern | Wuchsform-abhängige Spur-Hinweise (Geophyt-Einzug, Sukkulenten-Default) nur eingeschränkt. | Referenz §9 E1 |
| `cycle_type` nicht zuverlässig auf `Species` verfügbar | R-016/R-002: Lebensdauer-Grundstruktur heute oft nur heuristisch. | REQ-001 / LifecycleConfig |

> **R-050 (SOLL):** Solange E2/E4/E5 nicht umgesetzt sind, SOLL die Komponente datengetriebene Heuristiken (Überlappungserkennung, `allows_harvest`, `propagation_methods`-Inhalt) nutzen und ihre Annahmen transparent halten, statt eine falsche Sicherheit zu suggerieren.

---

## 9. Akzeptanzkriterien

### Definition of Done

- [ ] Spuren werden gemäß §3 mit den definierten Farben, Labels und Monats-Grid dargestellt; laufender Monat hervorgehoben (R-001, R-003, R-005).
- [ ] Vermehrungs-Spur ist read-only mit Hinweis; Editieren erfolgt nur in der Vermehrungs-Karte (R-006, R-007, R-031).
- [ ] Ernte-Spur wird bei nicht-erntbaren (Zier-)Arten ausgeblendet; Titel nennt dann keine Ernte (R-010, R-012).
- [ ] Aussaat-Spur wird bei rein vegetativ vermehrten Arten ohne Aussaatdaten ausgeblendet (R-013).
- [ ] Überlappung Aussaat ∩ Ernte/Blüte erzeugt den erklärenden Hinweis (R-020).
- [ ] Genau **eine** Zeitachse pro Art (keine zweite, berechnete, widersprüchliche Achse) (R-017).
- [ ] Mehrjährige Arten werden als wiederkehrender Zyklus dargestellt, ohne Rohmonate zu klippen (R-017).
- [ ] i18n (de/en) vollständig, A11y-konform, responsive (R-040–R-044).

### Testszenarien

| Szenario | Art (Beispiel) | Erwartung |
|---|---|---|
| Einjähriges Fruchtgemüse | Tomate | Aussaat, Wachstum, Ernte (continuous, breit), Blüte; lineare Lesart |
| Mehrjährige Kräuterstaude | Schnittlauch (*Allium schoenoprasum*) | Vermehrung + Aussaat + Ernte (Apr–Okt) + Blüte; Überlappungs-Hinweis sichtbar; **eine** Zeitachse; Titel nennt Ernte |
| Vegetative Zier-Zimmerpflanze | Lippenstiftpflanze (*Aeschynanthus radicans*) | Vermehrung (read-only) + Blüte; **keine** Ernte-Zeile; Aussaat-Zeile ausgeblendet; Titel ohne „Ernte" |
| Beeren-/Obststrauch mit Juvenilphase | Heidelbeere | Ernte-Spur mit Standjahr-Chip „ab n. Standjahr" |
| Zweijähriges Wurzelgemüse | Karotte/Petersilie | Jahr-1-Ernte vs. Jahr-2-Samengewinnung als getrennte Modi/Hinweis |
| Reine Zierpflanze ohne Vermehrungsdaten | beliebig | leere, aber sinnvoll beschriftete Darstellung ohne Fehlinformation |

---

## 10. Risiken bei Nicht-Einhaltung

- **Fehlinformation durch leere Spuren:** Eine permanente Ernte-Zeile bei Zierpflanzen suggeriert „wird nie geerntet"; eine Aussaat-Zeile bei rein vegetativer Vermehrung suggeriert eine nicht existierende Aussaat.
- **Wahrgenommener Datenfehler:** Sich überschneidende Aussaat-/Erntezeiten mehrjähriger Pflanzen wirken ohne Erklärung wie ein Bug.
- **Doppelte/widersprüchliche Zeitachsen:** Eine zusätzliche „berechnete" Achse, die die Rohmonate anders darstellt, untergräbt das Vertrauen in die Daten.
- **Editier-Konflikt:** Zwei Editier-Stellen für dieselben Vermehrungsdaten führen zu inkonsistentem State und Nutzerverwirrung.
- **Überforderung von Anfängern:** Eine dichte Expertenansicht ohne Progressive Disclosure widerspricht REQ-021.
```
