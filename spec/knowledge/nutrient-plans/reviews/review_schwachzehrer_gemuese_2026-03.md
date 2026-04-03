# Fachliches Review: Naehrstoffplaene Schwachzehrer/Mittelzehrer-Gemuese
**Erstellt von:** Agrarbiologie-Subagent (Fachspezialist Outdoor-Anbau, Gartenbau, Gemuese)
**Datum:** 2026-03-06
**Geprueft:** 4 Naehrstoffplaene + 4 Pflanzensteckbriefe

---

## Analysierte Dokumente

| Naehrstoffplan | Pflanzensteckbrief | Status |
|---------------|-------------------|--------|
| `salat_plagron_terra.md` | `lactuca_sativa.md` | geprueft |
| `moehre_plagron_terra.md` | `daucus_carota.md` | geprueft |
| `radieschen_plagron_terra.md` | `raphanus_sativus_var_sativus.md` | geprueft |
| `chicoree_plagron_terra.md` | `cichorium_intybus.md` | geprueft |

**Referenz EC-Werte (Vorgabe):**
- Terra Grow: 0.08 mS/cm pro ml/L
- Terra Bloom: 0.10 mS/cm pro ml/L
- Pure Zym: 0.00 mS/cm pro ml/L

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Biologische Korrektheit | 4.5/5 | Sehr gut; wenige, behebbare Luecken |
| NPK-Logik / Produktauswahl | 4/5 | Gut; ein systematischer Schwachpunkt bei Salat |
| EC-Budget-Genauigkeit | 5/5 | Alle Kalkulationen mathematisch korrekt |
| Phasenkontinuitaet | 4.5/5 | Lueckenlos; Chicoree hat eine Modellierungs-Anmerkung |
| Saisonplan Mitteleuropa | 5/5 | Realistisch und praezise |
| Sicherheitshinweise | 3.5/5 | Salat Oxalsaeure-Analogie fehlt; Bor-Risiko bei Radieschen fehlt |
| Steckbrief-Konsistenz | 4/5 | EC-Werte im Plan konservativ gegenueber Steckbrief -- begruendet, aber dokumentationsbeduerftig |

Alle vier Plaene sind qualitativ solide und koennen als Referenzdaten in Kamerplanter importiert werden. Die identifizierten Maengel sind ueberwiegend Ergaenzungen (fehlende Warnhinweise, fehlende Begruendungen fuer bewusste Abweichungen), keine fachlichen Fehler. Kritischster Punkt: der Salat-Plan gehoert als "Mittelzehrer" kategorisiert, aber das Produkt-NPK-Verhaeltnis ist fuer einen reinen N-betonten Wachstumsduenger suboptimal -- die Begru-endung, dass Salat vor der Bluete geerntet wird und daher kein Terra Bloom benoetigt, ist fachlich vertretbar, sollte aber expliziter dokumentiert sein.

---

## Befunde nach Prioritaet

---

### KRITISCH (K) -- Fachlich korrekturbeduerftiger Befund

#### K-001: Salat -- Lichtkeimer vs. Dunkelkeimer-Widerspruch bei Moehre nicht auf Salat uebertragen (kein echter Fehler, aber Klarstellungsbedarf)

Dieser Punkt betrifft NICHT Salat selbst, sondern die interne Konsistenz der Produktgruppe: Salat wird korrekt als Lichtkeimer behandelt (Plan: "nur leicht andruecken"). Moehre wird im Plan korrekt als Lichtkeimer behandelt, obwohl der Steckbrief sagt "nur leicht mit feinem Sand/Erde abdecken (max. 1 cm)" -- das ist biologisch korrekt fuer Moehren (Halbdunkl-Keimer, nicht Lichtkeimer im strengen Sinne). Kein Korrekturbedarf am Plan, aber der Steckbrief-Eintrag fuer Daucus carota sollte prazisiert werden: Moehre ist ein "Halbdunkel-Keimer" (toleriert 0.5--1 cm Erdabdeckung) und kein echter Lichtkeimer wie Salat (0 cm Abdeckung). Im Plan steht korrekt "Samen nur 1 cm tief" -- das ist biologisch korrekt.

**Bewertung:** Kein Korrekturbedarf am Naehrstoffplan. Steckbrief-Notiz empfohlen.

---

#### K-002: Salat -- Steckbrief-EC optimum vs. Plan-EC erheblich abweichend, ohne vollstaendige Begruendung

**Betroffener Plan:** `salat_plagron_terra.md`, Abschnitt 4.3 VEGETATIVE
**Steckbrief-EC vegetativ:** 1.0--1.6 mS/cm (lactuca_sativa.md, Tabelle 2.3)
**Plan EC-Ziel vegetativ:** 0.60 mS/cm (inkl. Basiswasser 0.4)
**Abweichung:** Plan liegt ca. 40--60% unter dem Steckbrief-Optimum

Der Plan begruendet die Reduzierung mit "Nitrat-Akkumulation vermeiden" -- das ist fachlich korrekt und ein legitimes Ziel bei Freiland-Salat. Jedoch ist die Begruendung im Plan nicht vollstaendig: EC 0.6 mS/cm liegt sogar deutlich unter dem Steckbrief-Minimum (1.0 mS/cm). Fuer Freiland-Erde (mit Grundnaehrstoffversorgung aus dem Boden) ist das vertretbar, da Terra Grow die Boden-Grundversorgung erhaelt. Fuer einen Nutzer, der auf naehrstoffarmen Boden (z.B. frisch angelegtes Beet) oder in Toepfen arbeitet, koennte EC 0.6 mS/cm zu niedrig sein.

**Korrekturempfehlung:** Einen Hinweis erganzen: "Bei normaler Gartenerde (vorgedungt oder humusreich) ist EC 0.6 mS/cm ausreichend. Auf naehrstoffarmem Boden oder bei Topfkultur Terra Grow auf 3.0--3.5 ml/L erhoehen (EC gesamt ~0.7--0.8 mS/cm)."

---

### WICHTIG (W) -- Fachliche Luecken, die Anwendersicherheit oder Vollstaendigkeit betreffen

#### W-001: Salat -- Nitrat-Grenzwerte unvollstaendig

**Betroffener Plan:** `salat_plagron_terra.md`, Abschnitt 6 und 8
**Befund:** Der Plan erwaehnt EU-Grenzwerte fuer Nitrat "3000--5000 mg NO3/kg Frischgewicht (saisonal/sortenabhaengig)". Die saisonale Differenzierung fehlt teilweise.

**Prazisierung erforderlich:** Gemaess EU-Verordnung (EG) Nr. 1881/2006 und den laufenden Aktualisierungen gelten fuer Freiland-Salat folgende Grenzwerte:
- Freiland-Ernteware Sommer (1. April -- 30. September): 3500 mg NO3/kg FG
- Freiland-Ernteware Winter (1. Oktober -- 31. Maerz): 4000 mg NO3/kg FG
- Unter Glas/Folie Sommer: 4500 mg NO3/kg FG
- Unter Glas/Folie Winter: 5000 mg NO3/kg FG

Der Plan listet 3000--5000 mg als Range -- das ist als Faustwert in Ordnung, aber die saisonale Richtung ist umgekehrt dargestellt (Sommer hat niedrigeren Grenzwert, nicht hoehere -- Sommer = mehr Licht = mehr Photosynthese = weniger Nitrat-Akkumulation, daher ist der Grenzwert strenger). Eine Anmerkung, dass Sommerernte tendenziell niedrigere Nitratwerte hat (wegen hoeherem Lichtniveau und Photosyntheserate), waere fachlich wertvoll.

**Korrektheit der Massnahmen im Plan:** Korrekt. "Letzte Duengung 7 Tage vor Ernte" und "morgens ernten" sind valide Nitrat-Reduktionsmassnahmen.

---

#### W-002: Moehre -- Bor-Mangel als Qualitaetsrisiko fehlt im Naehrstoffplan

**Betroffener Plan:** `moehre_plagron_terra.md`
**Befund:** Der Steckbrief (daucus_carota.md) erwaehnt explizit: "Bor-Empfindlichkeit: Bor-Mangel verursacht Risse/Hohlraeume in der Wurzel. Bei bekanntem Mangel: 1 g Borax / 10 L Wasser als Blattspruehung." Der Naehrstoffplan erwaehnt diesen Punkt mit keinem Wort.

Terra Bloom enthaelt 0.48% Bor (sehr hoher Anteil) -- wuerde aber im Moehren-Plan eingesetzt. Bei reiner Terra Bloom-Anwendung ist Bor-Unterversorgung dadurch abgedeckt. Jedoch: Terra Grow (wird nicht eingesetzt, korrekt) enthaelt keine deklarierten Bor-Werte. Da der Plan ausschliesslich Terra Bloom verwendet, ist die Bor-Versorgung durch das Produkt faktisch gegeben. Dennoch fehlt ein Hinweis fuer Nutzer, die das Duengen weglassen ("kein frischer Stallmist, aber Bor-Mangel beachten").

**Korrekturempfehlung:** Ergaenzung in Abschnitt 6 oder 8: "Terra Bloom enthaelt 0.48% Bor -- Bor-Mangel-Risiko (Risse in der Wurzel) bei regelmaessiger Duengung nicht relevant. Bei ungednten Boeden (Plan ohne Duengung): Bor-Status beachten; ggf. 1g Borax/10L als einmalige Blattspruehung in der vegetativen Phase."

---

#### W-003: Radieschen -- Bor-Mangel-Risiko nicht erwaehnt

**Betroffener Plan:** `radieschen_plagron_terra.md`
**Befund:** Der Steckbrief (raphanus_sativus_var_sativus.md, Abschnitt 3.4) erwaehnt explizit: "Bor-Mangel: Fuehrt zu hohlen, rissigen Knollen mit braunem Kerngewebe. In bor-armen Boeden 1 g Borax pro 10 m2 einarbeiten."

Der Radieschen-Plan basiert auf dem Prinzip "fast keine Duengung noetig". Damit wird auch kein bor-haltiges Produkt (Terra Bloom hat 0.48% B) eingesetzt. Auf bor-armen Boeden (haufig in Deutschland: Sandboeden, saure Boeden nach Kalkung) kann Bor-Mangel zu hohlen, rissigen Knollen fuehren -- genau das, was Nutzer als Qualitaetsproblem wahrnehmen.

**Korrekturempfehlung:** In Abschnitt 6 ("Praxis-Hinweise") ergaenzen: "Hohlknolle / rissige Knolle: Neben Trockenstress kann Bor-Mangel hohle Knollen mit braunem Kerngewebe verursachen. Auf bor-armen Boeden (Sandboeden, stark gekalkter Boden) vorbeugend 1 g Borax pro 10 m2 einarbeiten."

---

#### W-004: Chicoree -- VEGETATIVE Phase hat zwei verschiedene Duengerprodukte, aber nur eine delivery_channel-Konfiguration im JSON

**Betroffener Plan:** `chicoree_plagron_terra.md`, Abschnitt 4.3 VEGETATIVE und 7.2 JSON
**Befund:** Die Textbeschreibung der VEGETATIVE-Phase ist korrekt und biologisch sinnvoll: Wochen 8--12 Terra Grow (N-betont fuer Blattaufbau), ab Woche 13 Umstellung auf Terra Bloom (K-betont fuer Wurzelaufbau). Das ist eine fundierte agronomische Entscheidung.

Das JSON-Datenmodell (Abschnitt 7.2) bildet die VEGETATIVE-Phase jedoch mit einem einzigen NutrientPlanPhaseEntry ab, der nur Terra Bloom + Pure Zym enthalt. Terra Grow fuer Wochen 8--12 erscheint im JSON nicht. Das Kamerplanter-System unterstuetzt pro PhaseEntry nur einen Satz `fertilizer_dosages` -- die zweiphasige Duengerstrategie kann nicht direkt modelliert werden.

**Bewertung:** Das ist ein Modellierungsproblem, kein biologischer Fehler. Die Praxis-Hinweise im Freitext beschreiben das korrekte Vorgehen.

**Empfehlung:** Zwei Optionen:
1. Akzeptierter Kompromiss: Im JSON nur Terra Bloom (dominante Phase) hinterlegen und in den `notes` des PhaseEntry klar dokumentieren: "Woche 8--12: Terra Grow 2.5 ml/L statt Terra Bloom verwenden. Ab Woche 13: Terra Bloom 2.5 ml/L."
2. Die Phase in VEGETATIVE_EARLY (W8--12) und VEGETATIVE_LATE (W13--20) aufteilen und als separate PhaseEntries modellieren. Das Kamerplanter-Datenmodell unterstuetzt mehrere Phasen-Eintraege mit demselben `phase_name`-Wert nicht direkt -- zwei separate `sequence_order`-Eintraege mit dem gleichen PhaseName-Enum wuerden den Phasenwechsel-Automaten stoeren.

**Kurzfristige Massnahme:** Option 1 ist der pragmatische Weg. Kommentar im `notes`-Feld erganzen.

---

#### W-005: Chicoree -- Oxalsaeure-Analogon: Intybin-Sicherheitshinweis unvollstaendig

**Betroffener Plan:** `chicoree_plagron_terra.md`, Abschnitt 8
**Befund:** Der Plan erwahnt korrekt, dass Intybin den Gallenfluss anregt. Es fehlt jedoch ein Hinweis fuer spezifische Risikogruppen: Personen mit Gallensteinen oder Gallenwegserkrankungen sollten Chicoree in grossen Mengen meiden, da Intybin (und verwandte Sesquiterpenlactone) die Gallenkontraktion stimulieren und Koliken ausloesen koennen.

Ausserdem fehlt der Hinweis zur Sesquiterpenlacton-Kreuzallergie: Personen mit Allergie gegen andere Asteraceae (Kamille, Beifuss, Arnika) koennen auf Chicoree kreuzallergisch reagieren.

**Korrekturempfehlung:** In Abschnitt 8 erganzen:
- "Kontraindikation: Personen mit Gallensteinen oder Gallenwegserkrankungen sollten Chicoree (frische Blaetter, Treibware) nur in kleinen Mengen konsumieren -- Intybin stimuliert den Gallenfluss."
- "Kreuzallergie: Bitte beachten: Asteraceae-Allergie (Kamille, Beifuss, Sonnenblume, Arnika) kann zu Kreuzreaktion auf Chicoree/Zichorie fuehren."

---

#### W-006: Moehre -- Furanocumarin-Warnung fuer Verarbeitung fehlt im Plan

**Betroffener Plan:** `moehre_plagron_terra.md`, Abschnitt 8
**Befund:** Der Steckbrief (daucus_carota.md) erwaehnt korrekt: "Kraut enthaelt Furanocumarine -- phototoxisch bei Hautkontakt + Sonnenlicht" und "Falcarinol im Kraut kann Kontaktdermatitis ausloesen -- Handschuhe bei Empfindlichkeit". Im Naehrstoffplan (Abschnitt 8) fehlt dieser Praxis-Hinweis vollstaendig.

Bei der Gartenarbeit (Vereinzeln, Anhaeufeln, Ernte) kommt es zum intensiven Kontakt mit dem Kraut. Im Sommer (starke UV-Strahlung) kann das bei empfindlichen Personen zu phototoxischen Hautreaktionen fuehren.

**Korrekturempfehlung:** In Abschnitt 8 erganzen: "Kraut-Kontakt: Das Moehren-Kraut enthaelt Furanocumarine (phototoxisch: Kontakt + Sonnenlicht kann Haeutroetungen verursachen) sowie Falcarinol (Kontaktallergen). Bei Gartenarbeit (Vereinzeln, Ernte) bei empfindlicher Haut Handschuhe tragen, besonders an sonnigen Tagen."

---

### HINWEISE (H) -- Optimierungspotenzial ohne fachlichen Fehler

#### H-001: Salat -- Einstufung "Mittelzehrer" vs. "schwachzehrer" im Tag-Set widerspruechlich

**Betroffener Plan:** `salat_plagron_terra.md`, Zeile 21
**Befund:** Der Tag-Vektor enthalt sowohl "mittelzehrer" als auch "schwachzehrer". Der Steckbrief klassifiziert Lactuca sativa korrekt als "medium (Mittelzehrer -- Kopfsalat eher Mittelzehrer, Schnittsalat eher Schwachzehrer)". Das Tag-Set suggeriert, der Plan gilt gleichermassen fuer beide, was fuer Datenbankfilter zu Doppeltreffern fuehrt.

**Empfehlung:** Tags auf "mittelzehrer" reduzieren und im Beschreibungstext explizit notieren: "Schnittsalat-Typen gelten als Schwachzehrer -- Dosierungen koennen um 20--30% reduziert werden."

---

#### H-002: Moehre -- EC-Ziel 0.6 mS/cm liegt bewusst unter Steckbrief-Optimum, aber die Begruendung fehlt im Plan-Header

**Betroffener Plan:** `moehre_plagron_terra.md`, Abschnitt 4.3
**Befund:** Im Plan wird die EC-Abweichung am Ende von Abschnitt 4.3 korrekt als "EC-Abweichung vom Steckbrief" dokumentiert. Das ist vorbildlich. Der Abschnitt 4 (Einleitung) erwaehnt jedoch "Schwachzehrer-Strategie" als Begruendung, obwohl der Steckbrief Moehre als Mittelzehrer (medium_feeder) einstuft. Das ist keine Inkonsistenz (der Plan begruendet die reduzierte Dosierung agrarisch korrekt), aber der Begriff "Schwachzehrer-Strategie" koennte beim Import irrelevante Einordnungen erzeugen.

**Empfehlung:** Formulierung andern in: "konservative Mittelzehrer-Strategie mit K-Betonung" um die offizielle Steckbrief-Klassifikation (medium_feeder) beizubehalten.

---

#### H-003: Radieschen -- Phasenmodell SEEDLING entfaellt, aber das ist biologisch nicht ganz korrekt

**Betroffener Plan:** `radieschen_plagron_terra.md`, Abschnitt 2
**Befund:** Der Plan begruendet das Weglassen der SEEDLING-Phase mit "bei 4 Wochen Gesamtkultur ist eine separate Saemlingsphase unpraktisch". Das ist pragmatisch verstaendlich.

Biologisch korrekt ist: Radieschen haben eine ausgepragte Saemlings-Phase (Steckbrief: 7--10 Tage, in der Hypokotyl-Verdickung beginnt). Das Zusammenfassen in VEGETATIVE ist eine pragmatische Vereinfachung, die fachlich vertretbar ist -- jedoch sollte im `notes`-Feld explizit stehen, dass die "VEGETATIVE"-Phase hier die Saemlings-Phase integriert.

**Empfehlung:** Der Plan macht das in der Beschreibung bereits klar. Kein Korrekturbedarf, aber ein technischer Hinweis fuer den Kamerplanter-Import: Der PhaseName-Enum "SEEDLING" wird uebersprungen. Wenn das System eine fixe Phasensequenz erzwingt, koennte das zu Validierungsfehlern fuehren. Puffer-Hinweis im Import-Dokument ergaenzen.

---

#### H-004: Chicoree -- Treiberei-Temperatur und Vernalisation -- Prazisierung sinnvoll

**Betroffener Plan:** `chicoree_plagron_terra.md`, Abschnitt 4.4 DORMANCY
**Befund:** Der Plan erwaehnt korrekt "1--2 Wochen bei 0--5 degC lagern (Vernalisation-Impuls, nicht zwingend fuer Witloof-Treiberei aber foerdert Zapfenbildung)". Das ist biologisch weitgehend korrekt, aber die Formulierung "nicht zwingend" ist bei der klassischen Witloof-Treiberei tatsaechlich diskussionswuerdig.

**Biologischer Hintergrund:** Fuer die Witloof-Chicoree-Treiberei gilt:
- Vernalisation (Kaeltereiz) ist fuer die Treiberei der Kultursorte "Witloof" nicht zwingend erforderlich -- die Zapfenbildung ist primae-r durch Dunkelheit und Waerme gesteuert (Etiolierung).
- Eine Kurzkuehlung (4--8 Wochen bei 0--5 degC) verbessert jedoch Zapfenfestigkeit und verringert Bitterkeit bei einigen Sorten.
- Der Plan weist korrekt darauf hin, dass es sich um einen foerdernden, nicht zwingenden Schritt handelt.

**Bewertung:** Biologisch korrekt. Keine Korrektur erforderlich.

---

#### H-005: Alle Plaene -- Bewasserungsintervall bei Starkregen/nassem Wetter nicht thematisiert

**Betrifft:** Alle 4 Plaene
**Befund:** Die Plaene definieren Giessintervalle als feste Tagesangaben (2 Tage Salat, 3 Tage Moehre, 2 Tage Radieschen, 4 Tage Chicoree). Bei Freiland-Outdoor-Kultur in Mitteleuropa sind Niederschlaege der dominante Bewasserungsfaktor -- die Intervall-Angaben im System werden durch Regen uebersteuert.

**Empfehlung fuer alle Plaene:** Einen Hinweis ergaenzen: "Giessintervall gilt nur bei Trockenheit. Bei ausreichend Niederschlag (>5 mm/3 Tage) entfaellt die Zusatzbewasserung. Das Kamerplanter-System sollte Niederschlagsdaten (REQ-005 Wetter-Integration) bei der Giessplan-Generierung beruecksichtigen."

Dieser Hinweis ist auch fuer die REQ-005-Implementierung relevant (Wetter-API als Sensor-Fallback).

---

## EC-Budget-Nachrechnung (Vollstaendige Verifikation)

Alle EC-Berechnungen wurden mit den Referenzwerten (Terra Grow 0.08, Terra Bloom 0.10, Pure Zym 0.00 mS/cm pro ml/L) nachgerechnet:

### Salat (salat_plagron_terra.md)

| Phase | Terra Grow ml/L | Pure Zym ml/L | EC Duenger | EC Wasser (0.4) | EC gesamt Plan | EC-Check |
|-------|----------------|---------------|------------|-----------------|----------------|---------|
| GERMINATION | 0 | 0 | 0.00 | 0.40 | 0.40 | KORREKT |
| SEEDLING | 1.5 | 0 | 0.12 | 0.40 | 0.52 | KORREKT |
| VEGETATIVE | 2.5 | 1.0 | 0.20 | 0.40 | 0.60 | KORREKT |
| HARVEST | 1.5 | 1.0 | 0.12 | 0.40 | 0.52 | KORREKT |

Alle EC-Werte korrekt. Rechenfehler: keiner.

### Moehre (moehre_plagron_terra.md)

| Phase | Terra Bloom ml/L | Pure Zym ml/L | EC Duenger | EC Wasser (0.4) | EC gesamt Plan | EC-Check |
|-------|-----------------|---------------|------------|-----------------|----------------|---------|
| GERMINATION | 0 | 0 | 0.00 | 0.40 | 0.40 | KORREKT |
| SEEDLING | 0 | 0 | 0.00 | 0.40 | 0.40 | KORREKT |
| VEGETATIVE | 2.0 | 1.0 | 0.20 | 0.40 | 0.60 | KORREKT |
| HARVEST | 0 | 0 | 0.00 | 0.40 | 0.40 | KORREKT |

Alle EC-Werte korrekt. Rechenfehler: keiner.

### Radieschen (radieschen_plagron_terra.md)

| Phase | Terra Bloom ml/L | EC Duenger | EC Wasser (0.4) | EC gesamt Plan | EC-Check |
|-------|-----------------|------------|-----------------|----------------|---------|
| GERMINATION | 0 | 0.00 | 0.40 | 0.40 | KORREKT |
| VEGETATIVE (optional) | 1.5 | 0.15 | 0.40 | 0.55 | KORREKT |
| HARVEST | 0 | 0.00 | 0.40 | 0.40 | KORREKT |

Alle EC-Werte korrekt. Rechenfehler: keiner.

### Chicoree (chicoree_plagron_terra.md)

| Phase | Produkt ml/L | EC Duenger | EC Wasser (0.4) | EC gesamt Plan | EC-Check |
|-------|-------------|------------|-----------------|----------------|---------|
| GERMINATION | 0 | 0.00 | 0.40 | 0.40 | KORREKT |
| SEEDLING | TG 1.5 | 0.12 | 0.40 | 0.52 | KORREKT |
| VEG frueh (W8-12) | TG 2.5 + PZ 1.0 | 0.20 | 0.40 | 0.60 | KORREKT |
| VEG spaet (W13-17) | TB 2.5 + PZ 1.0 | 0.25 | 0.40 | 0.65 | KORREKT |
| DORMANCY | 0 | 0.00 | 0.40 | 0.40 | KORREKT |
| HARVEST | 0 | 0.00 | 0.40 | 0.40 | KORREKT |

Alle EC-Werte korrekt. Rechenfehler: keiner.

**Gesamtergebnis EC-Budget:** Alle 4 Plaene mathematisch fehlerfrei. Die Basiswasser-Annahme von 0.4 mS/cm ist ein realistischer Mittelwert fuer deutsches Leitungswasser (typischer Bereich: 0.2--0.8 mS/cm) und sollte als solche im System dokumentiert sein.

---

## NPK-Verhaeltnis-Plausibilitaet

### Salat

| Phase | Plan-NPK | Steckbrief-Optimum | Deckungsgrad | Anmerkung |
|-------|----------|-------------------|-------------|-----------|
| SEEDLING | 3-1-3 | 1-1-1 | mittel | Terra Grow NPK ist N-betont; als halbe Dosis vertretbar |
| VEGETATIVE | 3-1-2 | 3-1-2 | sehr gut | Plan-NPK exakt passend! |
| HARVEST | 2-1-2 | 2-1-2 | perfekt | N-Reduktion vor Ernte korrekt umgesetzt |

Das NPK-Verhaeltnis im SEEDLING entsteht durch die Terra Grow-Zusammensetzung (3-1-3), waehrend der Steckbrief 1-1-1 empfiehlt. Das ist eine produktbedingte Abweichung (Terra Grow kann nicht auf 1-1-1 umkonfiguriert werden), die durch die Viertel-Dosis (1.5 ml/L) abgemildert wird. Fachlich vertretbar.

### Moehre

| Phase | Plan-NPK | Steckbrief-Optimum | Deckungsgrad | Anmerkung |
|-------|----------|-------------------|-------------|-----------|
| SEEDLING | 0-0-0 | 1-1-1 | n/a | Kein Duenger; Steckbrief empfiehlt 1-1-1 aber bei EC 0.3-0.6. Freiland-Boden liefert. |
| VEGETATIVE | 2-2-4 | 1-1-2 | gut | K>N Verhaeltnis passt (beide K-betont). Plan hat hoeheren P-Anteil als Steckbrief-Ideal. |
| HARVEST | 0-0-0 | 0-1-2 | gut | Kein Duenger vs. geringer P+K-Bedarf laut Steckbrief. Konservative Wahl korrekt. |

Terra Bloom (2-2-4) hat doppelt so viel N und P wie das Steckbrief-Ideal (1-1-2) vorsieht. Bei der Freiland-Schwachzehrer-Strategie mit nur 2 ml/L Terra Bloom und 14-Tage-Intervall ist die absolute N-Menge pro Woche so gering, dass dies keine negative Auswirkung auf die Wurzelbildung haben sollte. Rechnung: 2 ml/L * 2.1% N * 0.5 L = 0.21 g N pro Giessgang pro Laufmeter. Das ist eine sehr geringe N-Gabe.

**Bewertung:** Vertretbar. Die Produktwahl (Terra Bloom statt Terra Grow) ist die korrekte Entscheidung fuer Wurzelgemuese.

### Radieschen

| Phase | Plan-NPK | Steckbrief-Optimum | Deckungsgrad | Anmerkung |
|-------|----------|-------------------|-------------|-----------|
| VEGETATIVE (optional) | 2-2-4 | 1-2-3 | befriedigend | Steckbrief will P>N, Plan hat N=P. Angesichts "optional, nur magerer Boden" vertretbar. |
| HARVEST | 0-0-0 | 0-1-2 | gut | Kein Duenger korrekt |

Das Steckbrief-Ideal fuer Knollenbildung ist 1-2-3 (P>N, K dominant). Terra Bloom (2-2-4) hat N=P, waehrend das Optimum P>N waere. Fuer eine Einzel-Optionalgabe auf magerem Boden ist das tolerabel -- es gibt kein Plagron-Produkt, das 1-2-3 oder aehnliches liefert. Die Produktauswahl ist das bestmoegliche im Terra-Sortiment.

### Chicoree

| Phase | Plan-NPK | Steckbrief-Optimum | Deckungsgrad | Anmerkung |
|-------|----------|-------------------|-------------|-----------|
| SEEDLING | 3-1-3 | 1-1-1 | mittel | Wie bei Salat: Terra Grow als Viertel-Dosis vertretbar |
| VEGETATIVE | 2-2-4 | 3-1-2 (vegsteckbr.) | befriedigend | Steckbrief will N>P>K (3-1-2), Plan liefert K>N>P (2-2-4). Umstellung auf TB ab W13 ist fachlich begruendet. |
| DORMANCY/HARVEST | 0-0-0 | 0-0-0 | perfekt | Korrekt |

Anmerkung zur Chicoree VEGETATIVE: Das Steckbrief-Naehrstoffprofil vegetativ (3-1-2) entspricht einem N-betonten Blattaufbau, waehrend der Plan ab W13 auf K-Betonung (2-2-4) wechselt. Dieser Wechsel ist biologisch korrekt und agronomisch gut begruendet (Pfahlwurzelaufbau fuer Treiberei braucht K). Das Steckbrief-NPK-Profil gilt fuer die gesamte vegetative Phase als Mittelwert -- der Plan optimiert durch die zweistufige Strategie besser als der Steckbrief-Mittelwert.

---

## Phasenkontinuitaet-Check

### Salat
Lueckenlos-Check: GERMINATION (W1-2) + SEEDLING (W3-4) + VEGETATIVE (W5-8) + HARVEST (W9-10) = 10 Wochen.
Formel: 2 + 2 + 4 + 2 = 10. Korrekt, keine Luecken.

### Moehre
Lueckenlos-Check: GERMINATION (W1-3) + SEEDLING (W4-6) + VEGETATIVE (W7-14) + HARVEST (W15-18) = 18 Wochen.
Formel: 3 + 3 + 8 + 4 = 18. Korrekt, keine Luecken.

Kalendarische Prueefung: Start Anfang Maerz (Woche 1), Ende Mitte August (Woche 18) entspricht 4.5 Monaten. Fuer Nantes-Typ (70--90 Tage bis Erntereife) passt das exakt -- 18 Wochen = 126 Tage. Leicht konservativ bemessen, aber Spielraum fuer langsamere Keimung bei kuehleren Boeden ist sinnvoll.

### Radieschen
Lueckenlos-Check: GERMINATION (W1) + VEGETATIVE (W2-4) + HARVEST (W5) = 5 Wochen.
Formel: 1 + 3 + 1 = 5. Korrekt.

Anmerkung: Reale Kulturdauer kann 4 Wochen betragen (22--28 Tage bei optimalen Bedingungen). Woche 5 als HARVEST ist korrekt, aber der Plan sollte klarstellen, dass fruehe Sorten bereits in Woche 4--5 erntereif sein koennen und das HARVEST-Fenster tatsaechlich nur 3--5 Tage betraegt.

### Chicoree
Lueckenlos-Check: GERMINATION (W1-3) + SEEDLING (W4-7) + VEGETATIVE (W8-20) + DORMANCY (W21-24) + HARVEST (W25-28) = 28 Wochen.
Formel: 3 + 4 + 13 + 4 + 4 = 28. Korrekt.

Kalendarische Prueefung: Start Mai (W1) -- Dezember (W28). Mai + 28 Wochen = Anfang Dezember. Passt sehr gut mit dem realen Chicoree-Kalender fuer Mitteleuropa (Aussaat Mai/Juni, Treiberei November/Dezember).

---

## Saisonplan Mitteleuropa -- Plausibilitaetspruefung

### Salat

Der Plan sieht Fruehjahrsaussaat Indoor ab Anfang Maerz vor (Indoor-Vorkultur bei 12--16 degC). In Mitteleuropa (Zone 7--8) ist das realistisch:
- Anfang Maerz: Tageslange ~11h (Koeln), Bodentemperatur oft noch < 5 degC
- Indoor-Vorkultur bei 12--16 degC: korrekt, Thermodormanz bei 25 degC erwaehnt
- Auspflanzen April unter Vlies: korrekt, Nachtfrost bis Mitte April moeglich
- Ernte Mai/Juni: realistisch fuer Kopfsalat (55--70 Tage), knapp fuer Pfluecksalat (45 Tage)

Staffelsaat-Empfehlung (alle 2--3 Wochen) ist praxiserprobt und korrekt.

**Jahresplanplausibilitaet: Sehr gut.**

### Moehre

Direktsaat ab Anfang Maerz (ab 5 degC Bodentemperatur) in Mitteleuropa:
- Maerz in Mitteleuropa: Bodentemperatur 5 degC ist machbar, aber erst ab Mitte/Ende Maerz zuverlaessig
- Keimung 10--21 Tage: Bei 5--8 degC Bodentemperatur eher 21 Tage
- Ernte Juli--August fuer Nantes (70--90 Tage ab Saat): korrekt
- Ernte August (Woche 18 ab Anfang Maerz): entspricht ca. 18 Wochen = Mitte Juli. Das ist fuer fruehe Saaten leicht optimistisch, fuer normale Saaten realistisch.

**Jahresplanplausibilitaet: Gut. Hinweis ergaenzen, dass bei fruehester Aussaat Anfang Maerz (Boden noch kalt) die Keimung 3+ Wochen dauern kann und der Plan sich entsprechend verschiebt.**

### Radieschen

Aussaat ab Anfang Maerz bis September in Mitteleuropa:
- Maerz-Aussaat mit Vlies bei 5--8 degC Bodentemperatur: Keimung in 7--10 Tagen bei Vlisschutz. Realistisch.
- Sommerpause Juli--August (Schossgefahr): korrekt, >25 degC und >14h Taglaenge
- Herbstaussaat August--September: korrekt, kuerzere Tage verhindern Schossen
- Vlies bei fruehen Froesten September: korrekt

**Jahresplanplausibilitaet: Sehr gut. Vollstaendig und korrekt fuer Mitteleuropa.**

### Chicoree

Direktsaat ab Mai in Mitteleuropa:
- Mai-Aussaat: Bodentemperatur 15--18 degC, realistisch. Dunkelkeimer, 10--21 Tage Keimung.
- Vegetative Phase Juli--Oktober: korrekt
- Rodung Oktober/November: korrekt, vor ersten starken Froesten (-5 degC gefaehrdet Pfahlwurzel)
- Treiberei November--Dezember bei 15--18 degC: In Keller/Hauswirtschaftsraum gut realisierbar.
- ABSOLUT DUNKEL-Bedingung fuer Chicoreezapfen: korrekt und prominent kommuniziert.

**Jahresplanplausibilitaet: Sehr gut. Der zweiteilige Freiland+Treiberei-Ansatz ist biologisch praezise und fuer Mitteleuropa-Gartenpraxis korrekt.**

---

## Sicherheitshinweise -- Vollstaendigkeitspruefung

| Pflanze | Ungiftig Menschen | Ungiftig Katze/Hund | Duengemittel-Warnung | Naehrstoff-Sicherheit | Kontaktallergen-Warnung | Bewertung |
|---------|------------------|--------------------|--------------------|----------------------|------------------------|-----------|
| Salat | ja | ja | ja | Nitrat-Grenzwert erwaehnt (mit Praezisierungsbedarf, W-001) | entfaellt (kein Allergen) | gut |
| Moehre | Speicherwurzel ja | ja | ja | Karenz 4 Wo vor Ernte | Furanocumarin-Warnung fehlt (W-006) | lueckenhaft |
| Radieschen | ja | ja (mit Vorbehalt bei grossen Mengen, korrekt) | ja | keine Karenz noetig | entfaellt | gut |
| Chicoree | ja | ja | ja | Gallenfluss-Kontraindikation fehlt (W-005) | Sesquiterpenlacton-Kreuzallergie fehlt (W-005) | lueckenhaft |

**Spezifische Pruefung Oxalsaeure/analoge Verbindungen:**

Die Fragestellung erwaehnt Oxalsaeure bei Mangold. Bei den geprueften Plaenen:
- Salat: Lactucin (minimale Mengen in Kultursorten, korrekt als "vernachlaessigbar" eingestuft). Kein Oxalsaeure-Problem.
- Moehre: Furanocumarine und Falcarinol im Kraut -- relevant (W-006).
- Radieschen: Glucosinolate/Senfoele -- korrekt als gesundheitsfoerdernd eingestuft. Keine toxikologische Relevanz.
- Chicoree: Intybin und Sesquiterpenlactone -- Gallenfluss-Stimulation relevant fuer Risikogruppen (W-005).

---

## Import-Empfehlung fuer Kamerplanter

| Plan | Import-Empfehlung | Bedingung |
|------|------------------|-----------|
| salat_plagron_terra.md | Freigegeben mit Vorbehalt | K-002 (EC-Begruendung erganzen), W-001 (Nitrat-Grenzwert praezisieren) vor Import |
| moehre_plagron_terra.md | Freigegeben mit Erweiterung | W-002 (Bor-Hinweis), W-006 (Furanocumarin-Warnung) ergaenzen |
| radieschen_plagron_terra.md | Freigegeben | W-003 (Bor-Hinweis) als optionale Ergaenzung empfohlen |
| chicoree_plagron_terra.md | Freigegeben mit Vorbehalt | W-004 (JSON-Modellierung VEGETATIVE praezisieren), W-005 (Intybin-Kontraindikation) vor Import |

Alle vier Plaene haben korrekte EC-Budgets, biologisch sinnvolle Phasenstrukturen und praxistaugliche Saisonplaene fuer Mitteleuropa. Die identifizierten Luecken sind ergaenzungswuerdig, blockieren aber nicht den Import.

---

## Querverweise auf andere Reviews

- REQ-004-A (EC-Budget-Kalkulation): EC-Budget-Methodik dieser Plaene stimmt mit `spec/requirements-analysis/agrobiology-review-REQ-004-A.md` ueberein.
- Outdoor-Garden-Planner Review (G-001 bis G-031): Die Bodenanalyse-Integration (G-XXX) und phenologische Trigger (Bodentemperatur statt Kalender) werden in den Plaenen partiell umgesetzt (Moehre: "ab 5 degC Bodentemperatur") -- das ist lobenswert.
- plant-info-agrobiology-review-batch3-vegetables-2026-03.md: Sollte auf Konsistenz mit den hier geprueften Steckbriefen abgeglichen werden.

---

**Dokumentversion:** 1.0
**Erstellt:** 2026-03-06
**Geprueft durch:** Agrarbiologie-Subagent (Outdoor/Gemuese-Spezialist)
