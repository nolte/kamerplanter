# Agrarbiologisches Review: Aktivitäten-Beschreibungen
**Erstellt von:** Agrarbiologie-Experte (Subagent)
**Datum:** 2026-03-12
**Dokument:** `src/backend/app/migrations/seed_data/activities.yaml`
**Scope:** 43 Aktivitäten — biologische Korrektheit der Beschreibungen, Phasen-Logik, Artenkompatibilität, Stress-Level, Werkzeuge

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Biologische Korrektheit | 4/5 | Grundlagen solide; einige Mechanismus-Ungenauigkeiten und ein inhaltlicher Widerspruch |
| Phasen-Einschraenkungen | 3/5 | Mehrere inkonsistente oder biologisch nicht begruendete Sperren |
| Artenkompatibilitaet | 4/5 | Weitgehend korrekt; Cannabis-Beschraenkung bei LST/SCROG zu eng |
| Stress-Level-Einschaetzung | 4/5 | Supercropping und Lollipopping in einem Detail diskutierbar |
| Werkzeug-Angaben | 3/5 | Mehrere Luecken, insbesondere bei Handtechniken |
| Sprachliche Praezision | 4/5 | Fachbegriffe ueberwiegend korrekt; ein terminologischer Fehler |

**Fazit:** Die Beschreibungen sind insgesamt fachlich solide und praxistauglich. Sie enthalten jedoch
einen inhaltlichen Widerspruch (Heavy Defoliation), mehrere biologisch nicht korrekte Phasensperren,
einen taxonomischen Fehler (Celeriac-Anatomie) sowie Luecken bei Werkzeugangaben. Die Texte sind
klar und verstaendlich formuliert — der Bildungsanspruch ist hoch. Korrekturbedarf in 7 Punkten.

---

## Kritische Fehler (sofortiger Korrekturbedarf)

### K-001: Heavy Defoliation — Widerspruch forbidden_phases vs. Zeitempfehlung
**Aktivitaet:** `Heavy Defoliation` (sort_order: 8)
**Problem:** Die `forbidden_phases`-Liste schliesst `"flowering"` aus — die Beschreibung empfiehlt
die Massnahme jedoch explizit zu Blutebeginn (Tag 1-3) und Tag 21:
> "Typically performed at the onset of flowering (day 1-3) and again around day 21."

Das ist ein direkter logischer Widerspruch: Die Aktivitaet ist fuer eine Phase gesperrt, fuer die
sie laut Beschreibung primaer gedacht ist. Die Praxis entspricht dabei dem Stand der Technik —
schwere Entlaubung zu Blutebeginn ist im Cannabis-Anbau etabliert (Pre-Flower-Defoliation).

**Biologische Einordnung:** Biologisch ist die Massnahme zu Blutebeginn vertretbar: Die Pflanze
hat ihre vegetative Struktur abgeschlossen, das Blattwerk ist maximal entwickelt, und die
Umleitung von Photoassimilaten zu Blutensites ist physiologisch sinnvoll. Die Kritik an der
Methode betrifft die Intensitaet und Pflanzengesundheit, nicht den Zeitpunkt an sich.

**Korrekte Loesung:** `forbidden_phases` anpassen: `["late_flower", "harvest", "ripening",
"dormancy", "germination", "senescence"]`. Alternativ `restricted_sub_phases: ["mid_flower",
"late_flower"]` verwenden und `flowering` aus den gesperrten Phasen entfernen.

---

### K-002: Celeriac-Anatomie — Hypokotyl vs. Sprossknolle
**Aktivitaet:** `Celeriac Leaf Stripping` und `Celeriac Side Root Removal`
**Problem:** Beide Beschreibungen bezeichnen das erntbare Organ als "swollen hypocotyl" bzw.
"verdicktes Hypokotyl". Dies ist botanisch ungenau. Die Knolle des Knollenselleries
(*Apium graveolens* var. *rapaceum*) besteht anatomisch aus drei Zonen:
- Hypokotyl (unterer Bereich)
- Sprossknolle (Hauptvolumen, epidermaler Ursprung)
- Eingewachsene Wurzelbasis

Der praezise botanische Begriff ist "Sprossknolle" (hypocotyl-derived swollen stem base). Die
ausschliessliche Bezeichnung als "Hypokotyl" ist eine vereinfachende und in Fachkreisen
diskutierte Einordnung, da morphologische Studien zeigen, dass das Hypokotyl nur den unteren
Anteil des verdickten Organs bildet.

**Fuer die Zielgruppe (Hobbygaertner und Semiprofis):** Die Vereinfachung ist tolerierbar,
sollte aber zumindest durch "hypocotyl-derived storage organ" oder "swollen stem base" praezisiert
werden, um keine falschen Vorstellungen zu erzeugen.

**Empfehlung:** Formulierung aendern zu: "a swollen storage organ formed primarily from the
hypocotyl and stem base" / "ein verdicktes Speicherorgan, das hauptsaechlich aus dem Hypokotyl
und der Stängelbasis gebildet wird".

---

## Biologische Ungenauigkeiten (Korrekturbedarf)

### B-001: Auxinrezeptoren an der Nodie — unpraezise Formulierung
**Aktivitaet:** `Cloning` (sort_order: 18)
**Problem:** Die Beschreibung behauptet: "just below a node, where the highest concentration of
natural auxin receptors exists." Das ist physiologisch nicht praezise. Auxin (IAA) wird im
Apikalmeristem und in jungen Blaettern *produziert* und polarer basipetal transportiert. An der
Nodie ist nicht die Konzentration der Auxin*rezeptoren* erhoert, sondern die Konzentration des
transportierten Auxins selbst — was die Kompetenz des Kambiums zur Wurzelinitiation foerdert.
Die Verwechslung von Hormonkonzentration und Rezeptordichte ist ein verbreiteter, aber falscher
Vereinfachungsansatz.

**Korrekte Formulierung (EN):** "just below a node, where auxin concentration is highest due to
polar transport from the shoot tip — this promotes root initiation competence in the cambial cells."

**Korrekte Formulierung (DE):** "knapp unterhalb einer Nodie, wo die Auxin-Konzentration durch
den polaren Transport von der Triebspitze am hoechsten ist — dies foerdert die
Wurzelinitierungskompetenz der Kambiumzellen."

---

### B-002: Gibberellin-Anstieg beim Deadheading — Mechanismus zu vereinfacht
**Aktivitaet:** `Deadheading` (sort_order: 15)
**Problem:** "without the seed-development signal (gibberellin surge), the plant continues to
produce new flower buds." Der beschriebene Mechanismus ist teilweise korrekt, aber zu vereinfacht.
Gibberelline spielen bei der Samenreifung eine Rolle (GA3, GA4), aber die primaere hormonelle
Bremse fuer Neubluetenbildung bei verbluhten Pflanzen ist die Cytokinin/Ethylen-Balance, nicht
allein ein Gibberellin-Anstieg. Ethylen, das von alternden Blueten und Samen produziert wird,
hemmt Blutenknospeninitiierung systemisc. Deadheading reduziert primaer den Ethylenspiegel im
Gesamtsystem.

**Praezisere Formulierung (EN):** "By removing spent flowers promptly, ethylene levels in the
plant drop significantly — ethylene produced by aging petals and developing seeds systemically
inhibits new flower bud formation. This, combined with the removal of the dominant gibberellin
sink (the developing seed), allows the plant to reinitiate flowering."

**Korrekte Formulierung (DE):** "Durch promptes Entfernen verbluhter Bluten sinkt der Ethylenspiegel
in der Pflanze erheblich — Ethylen aus alternden Blutenblaetern und Samen hemmt systemisch die
Neublutenknospenbildung. Kombiniert mit der Entfernung der dominanten Gibberellin-Senke
(Samenanlage) kann die Pflanze die Bluetenbildung neu initiieren."

---

### B-003: Supercropping stress_level "medium" — moeglicherweise zu niedrig eingestuft
**Aktivitaet:** `Supercropping` (sort_order: 4)
**Problem:** Das Dokument klassifiziert Supercropping als `stress_level: "medium"`, waehrend
Topping und FIM als `"high"` eingestuft sind. In der Praxis ist Supercropping bei starkerer
Ausfuehrung (inneres Gewebe beschaedigt, sichtbarer Knick mit Saftaustritt) vergleichbar
stressintensiv wie Topping. Die Einstufung als "medium" ist vertretbar fuer sanftes Biegen
ohne Jauchenaustritt, aber die Beschreibung beschreibt gerade das Knicken ("partially crushed
between the fingers"), was eher "high" rechtfertigt.

**Empfehlung:** Entweder stress_level auf "high" anheben, oder die Beschreibung zwischen
"gentle bending" (LST-nah, medium) und "hard supercropping" (HST-nah, high) differenzieren.

---

### B-004: Lollipopping — restricted_sub_phases mid_flower ohne late_flower-Sperrung inkonsistent
**Aktivitaet:** `Lollipopping` (sort_order: 9)
**Problem:** `restricted_sub_phases: ["mid_flower"]`, aber die Beschreibung sagt:
"Avoid removing growth after week 3 of flowering" — Woche 3 ist typischerweise der Uebergang
von early zu mid_flower. Die Sperrung sollte konsequenterweise auch `"late_flower"` umfassen,
da die Beschreibung klar auf eine zeitliche Grenze bei ca. Woche 3 hinweist.

**Empfehlung:** `restricted_sub_phases: ["mid_flower", "late_flower"]` setzen — analog zur
Behandlung in Transplanting und Repotting.

---

### B-005: Root Pruning — Cytokinin-Mechanismus vereinfacht
**Aktivitaet:** `Root Pruning` (sort_order: 17)
**Problem:** "Root pruning triggers a hormonal reset: cytokinin production increases in new root
tips, promoting shoot growth above." Das ist grundsaetzlich korrekt — Cytokinine werden in
aktiven Wurzelspitzen synthetisiert und foerdern Sproesswachstum. Die Formulierung impliziert
jedoch, dass das Entfernen alter Wurzeln *direkt* die Cytokinin-Produktion steigert. Praeziser
ist: Neue Feinwurzeln, die nach dem Pruning gebildet werden, sind die Hauptquelle fuer
Cytokinine. Der Effekt tritt also erst nach 1-2 Wochen ein, wenn neue Wurzelspitzen gebildet
wurden — nicht sofort.

**Empfehlung:** Erganzen: "Once new feeder roots regenerate (after 1-2 weeks), cytokinin
production rises in the new root tips, stimulating shoot growth — the same mechanism that
drives spring growth after natural root dieback."

---

### B-006: Bromeliad Cup Filling — Trichom-Funktion praezisierungswuerdig
**Aktivitaet:** `Bromeliad Cup Filling` (sort_order: 45)
**Problem:** "absorbing it through specialized trichomes (scale-like structures) on the inner
leaf surfaces." Technisch korrekt, aber Trichome bei Bromelien sind abgestorbene, tote
Schildhaarstrukturen (peltate trichomes) — sie sind nicht lebende absorbierende Zellen wie
Wurzelhaarzellenm, sondern kapillare Saug- und Benetzungsstrukturen. Das Wort "absorbing"
klingt nach aktivem Transport durch lebende Zellen. Der Mechanismus ist physikalisch (Kapillarwirkung
und Diffusion durch tote Schuppenzellen in lebende Mesophyllzellen).

**Empfehlung:** "absorbing it passively through specialized peltate trichomes (dead, shield-shaped
scale structures) that channel water via capillary action into the living leaf tissue."

---

### B-007: Monstera Fenestration und vertikale Stütze
**Aktivitaet:** `Moss Pole Extension` (sort_order: 41)
**Problem:** "Without continued upward support, the heavy stem arches over and produces smaller,
unfenestrated leaves — the plant reverts to its juvenile 'ground-crawling' growth habit when it
loses vertical support." Dies ist teilweise korrekt, sollte aber praezisiert werden. Monstera
deliciosa zeigt Skototropismus in der Jugendphase (wachst auf dunkle Bereiche, also zum
Baumstamm hin). Die Fenestration ist primaer eine Funktion der Blattgroesse und des Lichts
(Positiver Zusammenhang mit Blattflaeche) und weniger direkt von der Vertikalen abhangig.
Kleine, unfenestrierte Blatter bei einem arch-over-Stiel sind eher eine Folge reduzierter
Lichtaufnahme (beschattete Blattstellung) als fehlender Vertikaler per se.

**Empfehlung:** Formulierung anpassen: "produces smaller, less-fenestrated leaves — partly
because the stem can no longer reach higher light levels, and partly because the plant shifts
toward its juvenile growth program when upright climbing is not possible."

---

## Inkorrekte oder inkonsistente Phasen-Einschraenkungen

### P-001: LST — species_compatible zu eng auf Cannabis beschraenkt
**Aktivitaet:** `LST` (sort_order: 5)
**Problem:** `species_compatible: ["Cannabis", "Hanf"]` — aber LST ist eine artenunabhaengige
Trainingstechnik. Sie wird standardmaessig bei Tomaten, Paprika, Orchideen, Zimmerpflanzen und
vielen anderen Kulturen eingesetzt. Die Beschraenkung auf Cannabis ist sachlich falsch und
limitiert die Verwendbarkeit der Aktivitaet im System erheblich.

**Empfehlung:** `species_compatible` entweder entfernen (keine Einschraenkung) oder auf eine
breite Liste erweitern: `["Cannabis", "Solanum lycopersicum", "Capsicum", "Monstera"]`.

---

### P-002: SCROG Setup — species_compatible zu eng
**Aktivitaet:** `SCROG Setup` (sort_order: 6)
**Problem:** `species_compatible: ["Cannabis", "Hanf"]` — SCROG-Netze werden auch fuer Tomaten
(haengend, DWC), Gurken, Chili und andere rankende oder klimmende Arten verwendet. Die
Beschraenkung auf Cannabis ist praxisfern.

**Empfehlung:** Analog zu P-001 — entweder Beschraenkung aufheben oder erweitern.

---

### P-003: Dahlia Disbudding — forbidden_phases schliesst vegetative Phase aus, aber Knospen enstehen erst waehrend budding
**Aktivitaet:** `Dahlia Disbudding` (sort_order: 21)
**Problem:** `forbidden_phases: ["dormancy", "sprouting", "senescence", "vegetative"]` — dies ist
korrekt und entspricht dem Text. Aber die Beschreibung sagt "Disbud during budding phase" —
es fehlt das explizite Erlauben der Blutephase (`flowering`). Falls `flowering` nicht in
`forbidden_phases` steht, ist es implizit erlaubt, was richtig ist. Das ist keine Fehler, aber
es sollte dokumentiert sein, dass `budding` und `flowering` (fruehy) die Zielphasen sind.

---

### P-004: Tuber Inspection — forbidden_phases schliesst sprouting aus, aber Kontrolle waehrend Austreibung sinnvoll
**Aktivitaet:** `Tuber Inspection` (sort_order: 30)
**Problem:** `forbidden_phases: ["vegetative", "flowering", "sprouting", "hardening_off"]` — das
Ausschliessen von `sprouting` ist biologisch nicht begrundet. Gerade am Anfang des Austriebs
(wenn Augen schwellen und erste Triebe erscheinen) ist eine Kontrolle auf Faeulnis und
Austrocknung besonders wichtig, da das Gewebe empfindlicher ist. Eine Kontrolle waehrend
`sprouting` ist nicht nur erlaubt, sondern empfehlenswert.

**Empfehlung:** `sprouting` aus `forbidden_phases` entfernen.

---

### P-005: Corm Separation — forbidden_phases schliesst dormancy aus, aber Durchfuehrung waehrend dormancy biologisch sinnvoll
**Aktivitaet:** `Corm Separation` (sort_order: 33)
**Problem:** `forbidden_phases: ["flowering", "vegetative", "sprouting", "dormancy"]` —
die Beschreibung sagt: "Separate them gently by hand after the mother corm has dried for a few
days" — das geschieht nach dem Ausheben, also **waehrend der Lagerperiode**, die
`dormancy` entspricht. Die Trennung von Brutkormen ist primaer eine Aufgabe waehrend oder
unmittelbar nach dem Einlagern (also waehrend oder am Uebergang zu `dormancy`).

**Empfehlung:** `dormancy` aus `forbidden_phases` entfernen. Stattdessen
`restricted_sub_phases: ["early_dormancy"]` verwenden falls ein Fruehruhe-Fenster ausgeschlossen
werden soll (frisch ausgegrabene Kormen muessen erst trocken, dann getrennt werden).

---

### P-006: Strawberry Old Leaf Removal — forbidden_phases fehlt "ripening"
**Aktivitaet:** `Strawberry Old Leaf Removal` (sort_order: 35)
**Problem:** `forbidden_phases: ["germination", "dormancy"]` — das Entfernen von Blattern
waehrend der Fruchtreife (ripening) ist physiologisch problematisch, da die Blatter in dieser
Phase primaere Photosyntheseorgane fuer Fruchtzuckerbildung sind. Ein Blattverlust waehrend
Fruchtreife reduziert Brix und Fruchtgroesse direkt. Die Beschreibung erwaehnt zwar
"after harvest" als Zeitpunkt, aber `ripening` als Phase sollte gesperrt sein.

**Empfehlung:** `"ripening"` zu `forbidden_phases` hinzufuegen.

---

### P-007: Hardening Off — forbidden_phases schliesst flowering aus, aber manche Arten werden waehrend Blute abgehaertet
**Aktivitaet:** `Hardening Off` (sort_order: 50)
**Problem:** `forbidden_phases: ["dormancy", "ripening", "harvest", "senescence", "flowering"]`
— das Ausschliessen von `flowering` ist bei Sommerblumern und Beet-Annuellen problematisch.
Petunien, Stiefmuetterchen und andere Einjahrige werden haeufig als bluhende Jungpflanzen
(in Blute) vom Gewachshaus in den Garten uebertragen — dies erfordert Abharten waehrend der
`flowering`-Phase.

**Empfehlung:** `"flowering"` aus `forbidden_phases` entfernen. Stattdessen als
Nutzungshinweis in der Beschreibung erganzen: "For plants already in bloom, reduce hardening
intensity to avoid bloom drop."

---

## Fehlende oder unvollstaendige Werkzeug-Angaben

### W-001: Topping / FIM — Desinfektionsmittel fehlt
**Aktivitaeten:** `Topping`, `FIM`, `Mainlining` (sort_order: 1, 2, 3)
**Problem:** `tools_required: ["scissors", "gloves"]` — beim Schnitt an lebenden Pflanzen
ist Desinfektion der Schneidwerkzeuge kritisch, um Uebertragung von Viren (TMV, CMV) und
Bakterien zu verhindern. Bei Cannabis ist die Uebertragung von Pseudomonas durch unsterile
Schneidwerkzeuge dokumentiert.

**Empfehlung:** `"isopropyl alcohol / disinfectant"` zu `tools_required` hinzufuegen.

---

### W-002: Pruning (General) — nur "secateurs" gelistet, aber Saege fuer Holzpflanzen noetig
**Aktivitaet:** `Pruning (General)` (sort_order: 11)
**Problem:** `tools_required: ["secateurs"]` — fuer Gehölzschnitt (Bonsai, Rosen, Straucher,
Obstbaume) sind Baumsaegen und Astscheren (loppers) notwendig. Die allgemeine Aktivitaet ist
auf alle Arten anwendbar.

**Empfehlung:** `tools_required: ["secateurs", "loppers", "pruning saw (for woody stems)"]`

---

### W-003: FIM — keine Schutzhandschuhe erwaehnt, aber Cannabis reizt die Haut
**Aktivitaet:** `FIM` (sort_order: 2)
**Problem:** `tools_required: ["scissors", "gloves"]` — Handschuhe sind bereits gelistet,
was korrekt ist. Kein Fehler, nur Bestaetigug.

---

### W-004: Pinching / Petunia Pinching — Werkzeuge fehlen ganz
**Aktivitaeten:** `Pinching` (sort_order: 16), `Petunia Pinching` (sort_order: 20),
`Dahlia Pinching` (sort_order: 24)
**Problem:** Keine `tools_required`-Angabe — obwohl die Beschreibung "thumb and forefinger"
erwaehnt und damit explizit keine Werkzeuge braucht, sollte zumindest "no tools required
(fingernails)" oder ein leerer Array angegeben sein, damit das Fehlen der Werkzeuge nicht als
fehlende Daten interpretiert wird. Fuer Petunien-Pinching waehrend der Blute empfehlen viele
Praktiker dunne Handschuhe bei allergischer Disposition (Petunia-Harze).

**Empfehlung:** Felder explizit setzen: `tools_required: []` mit optionalem Kommentar, oder
`tools_required: ["fingernails / no tools required"]`.

---

### W-005: Runner Removal (Erdbeere) — Werkzeuge fehlen
**Aktivitaet:** `Runner Removal` (sort_order: 34)
**Problem:** Keine `tools_required`-Angabe. Fuer kleine Auslaeufer ist das vertretbar (per Hand
abzwicken), aber fuer verholzte oder laengere Stolone sind Schere oder Messer notwendig.

**Empfehlung:** `tools_required: ["scissors"]` erganzen.

---

### W-006: Celeriac Leaf Stripping — Werkzeuge fehlen
**Aktivitaet:** `Celeriac Leaf Stripping` (sort_order: 51)
**Problem:** Keine `tools_required`-Angabe. Aeltere Sellerie-Blatter sind harte Blattstiele
die mit blossen Haenden schwer zu entfernen sind, ohne die Krone zu beschaedigen.

**Empfehlung:** `tools_required: ["scissors"]` oder `["sharp knife"]` erganzen.

---

## Inhaltliche Praezisierungen (keine Fehler, aber Verbesserungen)

### I-001: Flushing — wissenschaftliche Evidenz soll klarer eingeordnet werden
**Aktivitaet:** `Flushing` (sort_order: 14)
**Problem:** Die Beschreibung prasentiert Flushing als etablierte Methode und erwaehnt den
Nutzen (weisse Asche, sauberer Geschmack) als "argument from proponents" — das ist ehrlich
formuliert. Eine 2019 veroffentlichte Studie (Moher et al., Cannabis Cannabinoid Res.) fand
keinen signifikanten Unterschied in der Mineralstoffkonzentration im Gewebe nach Flushing.
Die aktuelle wissenschaftliche Literatur ist kritisch bis ablehnend bezuglich der Wirksamkeit
von Flushing auf Endproduktqualitaet.

**Empfehlung:** Erganzung: "Note: peer-reviewed evidence for flushing improving end-product quality
is currently limited. The practice is primarily based on grower tradition and organoleptic
assessment." / "Hinweis: Wissenschaftliche Belege fuer eine Qualitaetsverbesserung durch Flushing
sind derzeit begrenzt. Die Praxis basiert primaer auf Grower-Tradition und sensorischer Bewertung."

---

### I-002: Aerial Root Training — "secondary nutrient uptake pathway" uebertrieben
**Aktivitaet:** `Aerial Root Training` (sort_order: 40)
**Problem:** "By directing them into a moist moss pole, the roots establish a secondary nutrient
uptake pathway, resulting in larger leaves, faster growth, and better fenestration." Die Beziehung
zwischen Moosstab-Luftwurzeln und Fenestration ist in der Literatur nicht eindeutig belegt.
Groeere Blatter bei Monstera mit Moosstab sind primaer auf die vertikale Wachstumsrichtung und
das dadurch erreichte hoehere Lichtniveau zurueckzufuehren, nicht direkt auf die Naehrstoffaufnahme
der Luftwurzeln.

**Empfehlung:** Formulierung abmildern: "potentially contributing to improved nutrient and water
uptake" statt "establish a secondary nutrient uptake pathway resulting in..."

---

### I-003: Heavy Defoliation — PPFD-Wert ohne Einheitenklarheit
**Aktivitaet:** `Heavy Defoliation` (sort_order: 8)
**Problem:** "adequate light intensity (>600 PPFD)" — der Wert 600 ohne Einheit ist unvollstaendig.
PPFD wird in µmol/m²/s gemessen. Fachkorrekte Angabe: ">600 µmol/m²/s PPFD".

**Empfehlung:** Einheit erganzen: ">600 µmol/m²/s PPFD" (DE: ">600 µmol/m²/s PPFD").

---

### I-004: Runner Removal — "long-day trigger" korrekt, aber praezisierungswuerdig
**Aktivitaet:** `Runner Removal` (sort_order: 34)
**Problem:** "Runner production is triggered by long days" — korrekt fuer die meisten
Sortengruppen. Jedoch: Remontiererende (Ever-bearing) und Tagneutrale (Day-neutral) Sorten wie
'Albion', 'Seascape' oder 'Portola' produzieren Auslaeufer weitgehend unabhaengig von der
Taglaenge. Die Aussage gilt uneingeschrankt nur fuer Junifruchtende (short-day/ long-day-induced
runner production) Sorten.

**Empfehlung:** Erganzen: "Runner production in June-bearing varieties is strongly promoted by
long days (>14 h light); everbearing and day-neutral varieties produce runners more continuously
regardless of photoperiod."

---

### I-005: Bromeliad Pup Separation — "monocarpic" korrekt, aber Timing-Angabe zu optimistisch
**Aktivitaet:** `Bromeliad Pup Separation` (sort_order: 44)
**Problem:** "Pups take 2-3 years to reach flowering maturity, assuming adequate warmth (18-24°C)
and indirect bright light." Die Reifezeit von 2-3 Jahren ist fuer Guzmania lingulata unter
optimalen Bedingungen (hohe Luftfeuchtigkeit, Temperaturen >20°C) erreichbar. Unter typischen
Zimmerbedingungen (trockene Heizungsluft, niedrige Wintertemperaturen) sind 3-5 Jahre realistischer.
Auch Ethylen-Behandlung (Apfeleinlegen) zur Bluehinduktion wird in der Praxis haeufig eingesetzt
und fehlt als Hinweis.

**Empfehlung:** Anpassen: "Pups typically take 2-5 years to reach flowering maturity depending on
conditions. Flowering can be induced with ethylene gas by placing a ripe apple near the plant and
covering with a plastic bag for 5-7 days."

---

### I-006: Spathiphyllum Flower Stalk Removal — Auxin-Cytokinin-Mechanismus vereinfacht
**Aktivitaet:** `Spathiphyllum Flower Stalk Removal` (sort_order: 46)
**Problem:** "the plant channels auxin and cytokinins into vegetative growth and new flower bud
initiation." Auxin hemmt typischerweise die laterale Knospenentfaltung (Apikaldominanz). Eine
hohere Auxin-Aktivitaet wuerde neue Seitenbluten *hemmen*, nicht foerdern. Die korrekte
Formulierung ist: Das Entfernen der Blute *senkt* den systemischen Auxin-Spiegel (der Blutenstiel
ist eine Auxin-Quelle), was Cytokinine relativ dominanter macht — die dann Knospenentfaltung
foerdern. Der Auxin-Teil der Formulierung ist missverstaendlich.

**Korrekte Formulierung (EN):** "the plant redirects cytokinins toward vegetative growth and new
flower bud initiation. Auxin levels drop as the scape (a major auxin source) is removed,
allowing lateral buds to escape apical inhibition."

**Korrekte Formulierung (DE):** "die Pflanze leitet Cytokinine in vegetatives Wachstum und neue
Bluetenknospeninitierung um. Da der Blutenstiel (Scape) als Auxin-Quelle entfernt wird, sinkt
der Auxin-Spiegel systemisch — laterale Knospen werden dadurch von der apikalen Hemmung befreit."

---

## Zusammenfassung: Priorisierter Korrekturbedarf

| Prioritaet | ID | Aktivitaet | Problem |
|------------|----|------------|---------|
| Kritisch | K-001 | Heavy Defoliation | Direkter Widerspruch: flowering verboten, aber primaere Anwendungszeit |
| Kritisch | K-002 | Celeriac Leaf Stripping / Side Root Removal | Botanisch ungenauer Anatomie-Begriff |
| Hoch | B-001 | Cloning | Auxinrezeptoren vs. Auxinkonzentration verwechselt |
| Hoch | B-006 | Bromeliad Cup Filling | Trichom-Absorptionsmechanismus ungenau |
| Hoch | I-006 | Spathiphyllum Flower Stalk Removal | Auxin-Effekt falsch herum beschrieben |
| Hoch | P-001 | LST | species_compatible unnoetig auf Cannabis beschraenkt |
| Hoch | P-002 | SCROG Setup | species_compatible unnoetig auf Cannabis beschraenkt |
| Mittel | B-002 | Deadheading | Gibberellin-Mechanismus zu vereinfacht (Ethylen primaerer) |
| Mittel | P-004 | Tuber Inspection | sprouting zu Unrecht aus forbidden_phases ausgeschlossen |
| Mittel | P-005 | Corm Separation | dormancy zu Unrecht verboten (Zeitpunkt der Durchfuehrung) |
| Mittel | P-006 | Strawberry Old Leaf Removal | ripening fehlt in forbidden_phases |
| Mittel | P-007 | Hardening Off | flowering verboten, aber Einjahrige werden in Blute abgehaertet |
| Mittel | B-004 | Lollipopping | late_flower fehlt in restricted_sub_phases |
| Mittel | W-001 | Topping / FIM / Mainlining | Desinfektion fehlt in tools_required |
| Niedrig | B-003 | Supercropping | stress_level "medium" ggf. zu gering |
| Niedrig | B-005 | Root Pruning | Zeitverzoegerung des Cytokinin-Effekts nicht erwaehnt |
| Niedrig | B-007 | Moss Pole Extension | Fenestration-Kausalitaet zu direkt beschrieben |
| Niedrig | I-001 | Flushing | Wissenschaftliche Evidenzlage nicht erwaehnt |
| Niedrig | I-002 | Aerial Root Training | Naehrstoffaufnahme-Wirkung uebertrieben |
| Niedrig | I-003 | Heavy Defoliation | PPFD-Einheit fehlt |
| Niedrig | I-004 | Runner Removal | Taglaengen-Einschraenkung gilt nicht fuer alle Sorten |
| Niedrig | I-005 | Bromeliad Pup Separation | Reifzeit-Angabe zu optimistisch |
| Niedrig | W-002 | Pruning (General) | Saege fuer Holzschnitt nicht erwaehnt |
| Niedrig | W-004 | Pinching-Varianten | Werkzeugfeld fehlt (sollte explizit leer sein) |
| Niedrig | W-005 | Runner Removal | tools_required leer |
| Niedrig | W-006 | Celeriac Leaf Stripping | tools_required leer |

---

## Aktivitaeten ohne Befund (fachlich korrekt)

Die folgenden Aktivitaeten wurden geprueft und sind fachlich korrekt, vollstaendig und ohne
Widersprueche:

- **Topping** — Apikaldominanz-Mechanismus korrekt beschrieben
- **FIM** — Partielle Meristem-Entfernung und Variabilitaet korrekt
- **Mainlining** — Symmetrische Gefaessarchitektur korrekt erklaert
- **LST** — Auxin-Umverteilung bei Horizontalpositionierung korrekt
- **Light Defoliation** — Pathogen-Eintrittspforten und 10-20%-Regel korrekt
- **Pruning (General)** — Apikaldominanz-Aufhebung an Zweigen korrekt
- **Transplanting** — Wurzelhaarbeschaedigung und 2-4cm-Topfregel korrekt
- **Repotting** — Substratdegradation, Torfverdichtung, Perlitewanderung korrekt
- **Pinching** — Apikaldominanz-Mechanismus und Erholungszeit korrekt
- **Ausgeizen (Solanaceae)** — Assimilat-Konkurrenz und 5cm-Regel korrekt
- **Petunia Pinching** — Indeterminate Bluher korrekt klassifiziert
- **Deadheading** — Kernmechanismus (Samenentwicklung = Ressourcensenke) korrekt
- **Dahlia Disbudding** — Knospentreffenstruktur korrekt
- **Dahlia Staking** — Phloem-Unterbindung durch stramme Bindung korrekt erwaehnt
- **Dahlia Pinching** — 30-40cm-Zeitpunkt und 4-6 Seitentriebe korrekt
- **Sunflower Staking** — Capitulum-Gewicht und Lignifizierungsrueckgang korrekt
- **Sunflower Head Support** — Heliotropismus-Stop bei Reife korrekt
- **Tuber Division** — Augen-Pruefung und Kallus-Bildung korrekt
- **Tuber Lifting** — Frosttoleranz und Nicht-Waschen-Empfehlung korrekt
- **Tuber Inspection** — Lagerparameter 5-8°C / 60-70% korrekt
- **Spider Plant Pup Separation** — Stolon-Biologie und in-situ-Bewurzelung korrekt
- **Hardening Off** — Kutikula/Anthocyan/Lignin-Anpassungen korrekt
- **Celeriac Leaf Stripping** — Blatterhaltungsgrenze 8-10 korrekt
- **Celeriac Side Root Removal** — Solanin-Abgrenzung korrekt (wichtig!)
- **Pansy Deadheading** — Samenkapsel-Entfernung und Timing korrekt
- **Pansy Rejuvenation Cut** — Dormante Knospen-Aktivierung korrekt
- **Petunia Cutting Back** — Axillarknospen-Reaktion korrekt
- **Strawberry Old Leaf Removal** — Botrytis-Verlustraten und Renovationsschnitt korrekt
- **Strawberry Runner Removal** — 30-40% Assimilat-Umlenkung korrekt (mit Einschraenkung I-004)
- **Bromeliad Pup Separation** — Monokarpie und 1/3-Regel korrekt

---

## Glossar verwendeter Fachbegriffe

- **Apikaldominanz:** Hemmung der Seitenknospenentfaltung durch den wachsenden Haupttrieb via polaren Auxintransport
- **IAA (Indol-3-Essigsaeure):** Primaeres natuerliches Auxin; polarer Transport von Spross-Apex basipetal
- **IBA (Indol-3-Buttersaeure):** Synthetisches Auxin-Analogon; foerdert adventive Wurzelinitiation; Hauptwirkstoff in Bewurzelungspulvern
- **Cytokinine:** Phytohormone, die in aktiven Wurzelspitzen synthetisiert werden; foerdern Zelleilung und Knospenentfaltung; antagonistisch zu Auxin bezueglich Apikaldominanz
- **Ethylen:** Gasfoermiges Phytohormon; foerdert Alterung, Fruchtreife, Abscission; hemmt Blutenknospenentwicklung
- **Gibberelline (GA):** Phytohormone; foerdern Streckunswachstum, Keimung, Fruchtentwicklung
- **Peltate Trichome:** Tot-schuppige Haarstrukturen auf Bromelien-Blattern; ermoglichen Kapillar-Absorption von Wasser und Mineralstoffen
- **Kapitelum (Capitulum):** Bluetenstand der Compositen (Asteraceae); bei Sonnenblumen der gesamte "Bluetenkopf" mit Scheiben- und Strahlenbluten
- **Pedunkel:** Bluetenstiel; bei Sonnenblumen der Hals unterhalb des Capitulum
- **Skototropismus:** Wachstum in Richtung Dunkelheit (bei juvenilen Monstera: Wachstum auf Baumstaemme zu)
- **Hemiepiphyt:** Pflanze, die teils terrestrisch, teils epiphytisch lebt (z.B. juvenile Monstera terrestrisch, adulte epiphytisch kletternd)
- **Fenestration:** Blattloecher bei Monstera; dienen als Windschutz und erhoehen effektive Lichtflaeche im Kronendach
- **Monokarp:** Pflanze, die einmalig bueht und dann abstirbt; bei Bromelien auf Rosettenebene (nicht auf Artebene, da Kindel die Art weiterfuehren)
