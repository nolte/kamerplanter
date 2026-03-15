# Kami — Verbindliche Charakter-Referenz fuer Bildgenerierung

> **Version:** 1.0
> **Erstellt:** 2026-03-09
> **Zweck:** Einheitliche Kami-Darstellung ueber ALLE generierten Grafiken hinweg. Dieses Dokument ist die primaere Referenz fuer den Gemini-Graphic-Prompt-Generator-Agent und MUSS bei JEDER Bildgenerierung vollstaendig beruecksichtigt werden.
> **Quellen:** Design Guide (spec/ui-nfr/assets/design-guide.md), feature-kami-kernfunktionen.md, timeline-kami-phasen.md, ha-integration-icon-kami.md, banner-kami-hauptapplikation.md, illustration-kami-tankmanagement.md, illustration-kami-tank-fuellstaende.md

---

## 1. Identitaet

| Eigenschaft | Wert |
|------------|------|
| **Name** | Kami (Kurzform von Kamerplanter) |
| **Art** | Anthropomorpher Keimling in Terracotta-Topf |
| **Charakter** | Froehlich, hilfsbereit, neugierig, etwas tollpatschig |
| **Stilrichtung** | Kawaii-beeinflusst, professionell — kein reiner Kawaii, kein Kinderspielzeug |

---

## 2. Anatomie — SVG-optimierte Grundform

Alle Koerperteile bestehen aus einfachen geometrischen Grundformen. Dies garantiert saubere Vektorisierung mit vtracer und konsistente Darstellung ueber alle Groessen.

```
ANATOMIE-SCHEMA:

         ╱╲    ╱╲         BLAETTER (2 Stueck)
        ╱  ╲  ╱  ╲        Form: Tropfenfoermig (Ellipse + Spitze)
       ╱    ╲╱    ╲       Symmetrisch angeordnet, je 10° nach aussen geneigt
      ╱      ╲      ╲     SVG: Einfache Ellipse, oben spitz zulaufend
       ╲    ╱  ╲    ╱
        ╲  ╱    ╲  ╱
         ╲╱      ╲╱
           ╲    ╱
      ┌─────╲──╱─────┐
      │      ││      │    KOPF-/GESICHTSBEREICH
      │   ●     ●    │    Zwischen Blaettern und Topfrand
      │      ◡       │    Augen + Mund sitzen hier
      └──────┬┬──────┘
             ││               STIEL/HALS
             ││               Duenn, leicht geschwungen
      ┌──────┴┴──────┐
     ╱│              │╲   ARME: Duenne Linien seitlich am Topfkoerper
      │              │    (bei 32px und kleiner: WEGLASSEN)
      │   ════════   │    DEKOSTREIFEN: Einzelne Linie, hellerer Ton
      │              │    TOPF: Konische Trapezform
      └──────────────┘    (oben breiter als unten)
```

### 2.1 Proportionen (verbindlich)

| Koerperteil | Anteil Gesamthoehe | Hinweis |
|------------|-------------------|---------|
| Blaetter (Spitze bis Basis) | 45% | Dominantes Element, Markenzeichen |
| Stiel/Hals | 10–15% | Duenn, verbindet Kopf mit Topf |
| Topf (Oberkante bis Boden) | 35–40% | Stabiler Sockel |
| Blaetter-Spannweite | 80% der Kopfbreite | Nicht breiter als der Topf |
| Auge (einzeln) | 25% der Kopfbreite | Gross, ausdrucksstark |

### 2.2 Einzelteil-Geometrie (SVG-tauglich)

| Teil | Geometrische Grundform | SVG-Hinweis |
|------|----------------------|-------------|
| **Blatt** | Ellipse mit spitz zulaufendem oberen Ende | Ein `<path>` pro Blatt, max. 4 Kontrollpunkte |
| **Topf** | Trapez (Rechteck mit schraegen Seiten) | `<polygon>` oder `<path>` mit 4 Eckpunkten + abgerundeter Oberkante |
| **Dekostreifen** | Horizontales Rechteck auf Topfmitte | Einfaches `<rect>` |
| **Auge** | Kreis (gefuellt schwarz, weisser Highlight-Punkt) | `<circle>` + kleiner weisser `<circle>` |
| **Mund** | Bogen-Linie (quadratische Bezier-Kurve) | Einzelnes `<path>` mit 1 Kontrollpunkt |
| **Arm** | Duenne Linie, leicht geschwungen | `<path>` mit 1–2 Kontrollpunkten, Stroke only |
| **Stiel** | Duenne vertikale Linie, leicht geschwungen | `<path>`, Stroke only |

**SVG-Komplexitaet pro Kami (Zielwert):** < 25 Pfade gesamt.

---

## 3. Verbindliche Farbpalette

### 3.1 Kami-Koerperfarben (in ALLEN Bildern identisch)

| Element | Hex | Rolle |
|---------|-----|-------|
| Blaetter Basis | `#66bb6a` | Hauptfarbe der Blaetter |
| Blaetter Highlight | `#98ee99` | Helle Stellen nahe Blattspitze |
| Blaetter Schatten | `#2e7d32` | Dunkle Stellen nahe Stiel-Ansatz |
| Stiel | `#43a047` | Verbindung Kopf–Topf |
| Topf Basis | `#8d6e63` | Hauptfarbe Terracotta |
| Topf Dekostreifen | `#a1887f` | Hellerer Ring auf Topfmitte |
| Topf Schatten | `#6d4c41` | Unterseite, dunkle Bereiche |
| Erde (Topfrand) | `#795548` | Sichtbare Erdoberflaeche |
| Augen | `#000000` | Gefuellte Kreise |
| Augen-Glanzpunkt | `#ffffff` | Kleiner weisser Punkt oben-links im Auge |
| Mund | `#1b5e20` | Gleiche Farbe wie Outline |

### 3.2 Outline-System

| Modus | Farbe | Staerke aussen | Staerke innen | Linienenden |
|-------|-------|---------------|--------------|-------------|
| **Light Mode** | `#1b5e20` (Dunkelgruen) | 2.5px | 1.5px | Round cap, round join |
| **Dark Mode** | `#c8e6c9` (Hellgruen) | 2.5px | 1.5px | Round cap, round join |
| **HA Dark Theme** | `#ffffff` (Weiss) | 2.5px | 1.5px | Round cap, round join |
| **Monochrom** | `#000000` oder `#ffffff` | 2.5px | 1.5px | Round cap, round join |

**WICHTIG:** Outlines sind IMMER dunkelgruen oder hellgruen/weiss — niemals reines Schwarz (ausser Monochrom-Variante).

### 3.3 Akzentfarben (nur fuer Requisiten und Kontext)

| Rolle | Hex | Einsatz |
|-------|-----|---------|
| Wasser/Bewaesserung | `#4fc3f7` | Wassertropfen, Giesskanne, reines Wasser |
| Naehrloesung | `#4dd0e1` | Tankinhalt, Naehrloesung (NICHT fuer reines Wasser) |
| Sonnenlicht | `#ffb74d` | Sonnenakzente, warme Highlights |
| Warnung | `#ed6c02` | Warn-Dreiecke, Aufmerksamkeits-Symbole |
| Fehler | `#d32f2f` | Schaedlinge, kritische Zustaende |
| Indigo/Technik | `#5c6bc0` | Wissenschaftliche Requisiten, Laborkittel-Kragen |
| Bluete | `#ab47bc` | Bluehphase, Bluetenfarbe |
| Ernte/Gold | `#ffa726` | Fruechte, Erfolgssymbole, Glitzer-Sterne |
| Neutral Grau | `#bdbdbd` | Tanks, technische Geraete, neutrale Objekte |
| Dunkelgrau | `#9e9e9e` | Raender, Rahmen, sekundaere Metallteile |
| Braun (Warm) | `#795548` | Ventile, Holzteile, Stufenhocker |

---

## 4. Emotionssystem — Stimmung durch Form

Kamis Emotionen werden durch DREI Ausdrucks-Kanaele gesteuert. Jede Emotion ist eine eindeutige Kombination dieser drei Kanaele.

### 4.1 Ausdrucks-Kanaele

```
KANAL 1 — BLAETTER (fungieren als "Ohren/Haare"):
  ↑↑  Aufrecht nach oben ........... Positiv, energisch, stolz
  ↗↖  Leicht nach aussen ........... Entspannt, zufrieden, praesentierend
  →←  Weit nach aussen gespreizt ... Ueberrascht, feiernd, aufgeregt
  ↘↙  Nach unten haengend .......... Traurig, muede, besorgt
  ↗↙  Asymmetrisch (einer hoch) .... Nachdenklich, skeptisch, verwirrt
  ↑↑  Steif gerade hoch ............ Schreck, Alarm

KANAL 2 — AUGEN:
  ● ●  Grosse runde Punkte .......... Standard, aufmerksam, neugierig
  ● ●  Extra-gross .................. Ueberrascht, beeindruckt, erschrocken
  ◠ ◠  Halbkreise nach oben (^^) .... Gluecklich, geniesserisch, lachend
  ◡ ◡  Halbmond nach unten .......... Friedlich, zufrieden, traeumend
  ● •  Asymmetrisch (gross/klein) ... Skeptisch, zweifelnd
  ✦ ✦  Stern-Highlights ............. Begeistert, triumphierend
  ● ●  Mit Schweissttropfen daneben . Nervoes, peinlich, angestrengt

KANAL 3 — MUND:
  ◡    Einfacher Aufwaerts-Bogen .... Standard-Laecheln (happy)
  ◡◡   Breites Laecheln ............. Grosse Freude, Stolz
  ○    Kleiner offener Kreis ........ Ueberraschung, Schock, Staunen
  ~    Wellige Linie ................ Unsicherheit, Sorge, Unbehagen
  ╱    Diagonale Linie .............. Skeptisch, nachdenklich, "hmm"
  ∪    Grosses offenes U ............ Begeisterung, Feiern, Lachen
  ─    Gerade Linie ................. Ernst, konzentriert, neutral
  ◠    Abwaerts-Bogen ............... Traurig, enttaeuscht
```

### 4.2 Emotions-Katalog (verbindlich)

Jede Emotion definiert die exakte Kombination aller drei Kanaele plus Armhaltung. Bei der Bildgenerierung MUSS die hier definierte Kombination verwendet werden.

---

#### HAPPY (Standard)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Aufrecht nach oben |
| Augen | ● ● Standard-Punkte mit Glanzpunkt |
| Mund | ◡ Einfacher Aufwaerts-Bogen |
| Arme | Locker seitlich, entspannt |
| Einsatz | Default, neutrale Zustaende, Profilbild |

**Prompt-Fragment:**
```
Happy expression: leaves pointing straight upward, large round dot eyes
with white highlight glints, small curved upward smile. Arms relaxed at sides.
```

---

#### STOLZ / ZUFRIEDEN (Proud / Content)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Aufrecht, leicht nach aussen |
| Augen | ● ● Standard, leicht verengt (zuversichtlich) |
| Mund | ◡◡ Breites zufriedenes Laecheln |
| Arme | Ein Arm Daumen-hoch ODER Hand an Huefte |
| Einsatz | Guter Zustand, Mission erfuellt, 60% Fuellstand, korrekte Werte |

**Prompt-Fragment:**
```
Proud content expression: leaves perked upward, eyes slightly narrowed with
confidence, broad satisfied smile. One arm giving thumbs-up, other arm on hip
or relaxed at side.
```

---

#### GLUECKLICH / BEGEISTERT (Joyful / Delighted)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | →← Weit nach aussen gespreizt, energisch |
| Augen | ◠ ◠ Geschlossene Halbkreise (^^), Freude-Augen |
| Mund | ∪ Grosses offenes Laecheln |
| Arme | Beide Arme seitlich ausgebreitet, praesentierend |
| Einsatz | Sehr guter Zustand, 80% Fuellstand, Aufgabe erledigt |

**Prompt-Fragment:**
```
Joyful delighted expression: leaves spread outward energetically, eyes closed
in happy anime-style crescents (^^), wide open bright smile. Both arms spread
outward in a proud presenting gesture.
```

---

#### TRIUMPHIEREND / FEIERND (Triumphant / Celebrating)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Steif gerade nach oben, maximal aufrecht |
| Augen | ✦ ✦ Stern-Highlights oder extra-grosse glaenzende Augen |
| Mund | ∪ Grosses selbstbewusstes Grinsen |
| Arme | Ein Arm Siegerfaust nach oben, anderer Arm an Huefte (Power-Pose) |
| Akzente | Optionale Glitzer-Sterne (#fff9c4) in der Naehe |
| Einsatz | 100% Fuellstand, Ernte, Phasenwechsel-Erfolg, grosser Erfolg |

**Prompt-Fragment:**
```
Triumphant celebrating expression: leaves standing straight and tall, eyes
sparkling with star-shaped white highlights, big confident victory grin.
One arm raised in fist pump victory pose, other arm on hip in power stance.
Optional: 2-3 small four-pointed sparkle stars (#fff9c4) floating nearby.
```

---

#### BESORGT / UNSICHER (Worried / Uncertain)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↘↙ Leicht nach unten/innen geneigt |
| Augen | ● ● Leicht zusammengekniffen (Sorge) |
| Mund | ~ Wellige unsichere Linie |
| Arme | Ein Arm kratzt nervoes am Hinterkopf, anderer haengt |
| Einsatz | Niedriger Fuellstand (20%), unklarer Zustand, Problem erkannt |

**Prompt-Fragment:**
```
Worried uncertain expression: leaves angled slightly inward-downward, eyes
slightly squinted with concern, mouth as a small uncertain wavy line. One arm
scratches the back of the head nervously, other arm hangs at the side.
```

---

#### SKEPTISCH / NACHDENKLICH (Skeptical / Thinking)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↗↙ Asymmetrisch (eines hoch, eines tiefer) |
| Augen | ● • Asymmetrisch (eines groesser, eines kleiner/zusammengekniffen) |
| Mund | ╱ Diagonale Linie ("hmm") |
| Arme | Ein Arm an Huefte, anderer Arm erhoben mit zeigendem Finger |
| Einsatz | 40% Fuellstand, Hinweis "bald handeln", Suchvorgang, Analyse |

**Prompt-Fragment:**
```
Skeptical thinking expression: leaves asymmetric (one perked up, one at neutral
angle), eyes open and alert with one slightly higher than the other, mouth as a
small diagonal line. One arm on hip, other arm raised with index finger pointing
upward in a "we should act soon" gesture.
```

---

#### PANISCH / ERSCHROCKEN (Panicked / Alarmed)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Steif nach oben (Schreck) oder ↘↙ haengend (Verzweiflung) |
| Augen | ● ● Extra-gross, weit aufgerissen |
| Mund | ○ Kleiner offener Kreis (Schock) |
| Arme | Beide Arme an die Wangen (Oh-no-Geste) |
| Akzente | 2–3 kleine blaue Schweisstropfen (#4fc3f7) neben dem Kopf |
| Einsatz | 0% Fuellstand, kritischer Fehler, Notfall |

**Prompt-Fragment:**
```
Panicked alarmed expression: leaves drooping downward limply, eyes wide and
large with shock, mouth as a small open circle. Both arms raised to cheeks in
classic oh-no gesture. 2-3 tiny blue sweat drops (#4fc3f7) floating near head.
```

---

#### TRAURIG / ENTTAEUSCHT (Sad / Disappointed)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↘↙ Deutlich nach unten haengend |
| Augen | ● ● Nach unten gerichtet, kleine Traene an einem Auge |
| Mund | ◠ Abwaerts-Bogen |
| Arme | Haengen schlaff seitlich |
| Einsatz | Fehler, Verbindungsproblem, fehlgeschlagene Aktion |
| Hinweis | Sympathisch-traurig, nicht deprimierend. "Es tut mir leid"-Ausdruck |

**Prompt-Fragment:**
```
Sad disappointed expression: leaves drooping clearly downward, eyes looking
down with a small teardrop on one eye, mouth as a downward curved arc. Arms
hanging limply at sides. Overall posture slightly slumped. Sympathetically sad,
not depressing — an "I'm sorry" expression.
```

---

#### KONZENTRIERT / FOKUSSIERT (Focused / Determined)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Aufrecht, leicht nach vorne geneigt |
| Augen | ● ● Leicht verengt, fokussiert, ggf. Zungenspitze raus |
| Mund | ─ Gerade Linie oder leicht zusammengepresst |
| Arme | Kontextabhaengig (halten Werkzeug, zeigen auf Objekt) |
| Einsatz | Mischvorgang, praezise Arbeit, Aufgaben-Abarbeitung |

**Prompt-Fragment:**
```
Focused determined expression: leaves upright and slightly tilted forward, eyes
narrowed with concentration, mouth as a tight determined line or with tiny
tongue tip showing. Arms engaged with the task at hand.
```

---

#### NEUGIERIG / SUCHEND (Curious / Searching)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↗↖ Leicht schraeg, nach vorne geneigt |
| Augen | ● ● Ein Auge etwas groesser (neugieriger Ausdruck) |
| Mund | ○ Kleines "oh" oder ◡ leichtes Laecheln |
| Arme | Ein Arm am Kinn oder haelt Lupe |
| Akzente | Optional: Fragezeichen schwebt ueber einem Blatt |
| Einsatz | Leere Listen, Suche, Empty State, Laden |

**Prompt-Fragment:**
```
Curious searching expression: leaves tilted slightly forward and sideways, one
eye slightly larger than the other with curiosity, small "oh" mouth or gentle
smile. One arm at chin or holding a magnifying glass. Optional: small question
mark floating above one leaf.
```

---

#### EINLADEND / WILLKOMMEN (Welcoming / Inviting)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Aufrecht und lebendig |
| Augen | ● ● Gross, strahlend, offen |
| Mund | ◡◡ Breites warmes Laecheln |
| Arme | Ein Arm winkend (angehoben, Hand offen), anderer locker |
| Einsatz | Onboarding, Login, Willkommen, erste Nutzung |

**Prompt-Fragment:**
```
Welcoming inviting expression: leaves perked upward and lively, large bright
wide eyes with highlight glints, broad warm smile. One arm extended and waving
in greeting, other arm relaxed at side. Open, inviting body language.
```

---

#### FRIEDLICH / GENIESSERISCH (Peaceful / Serene)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↗↖ Entspannt nach aussen, weich |
| Augen | ◡ ◡ Halb geschlossen, traeumerisch |
| Mund | ◡ Sanftes zufriedenes Laecheln |
| Arme | Entspannt, ein Arm beruehrt sanft Requisit |
| Einsatz | Bluehphase, Genuss-Moment, erfolgreiche Pflege |

**Prompt-Fragment:**
```
Peaceful serene expression: leaves relaxed and gently spread outward, eyes
half-closed in a dreamy content manner, soft gentle smile. Arms relaxed, one
arm gently touching a nearby element. Overall feeling of calm satisfaction.
```

---

#### ENERGISCH / KRAFTVOLL (Energetic / Powerful)

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | ↑↑ Straff aufrecht, leicht wippend |
| Augen | ● ● Leuchtend, weit offen, voller Energie |
| Mund | ◡◡ Selbstbewusstes breites Laecheln |
| Arme | Beide Arme nach aussen gestreckt, "Flexing"-Pose |
| Einsatz | Vegetative Phase, volle Kraft, optimaler Zustand |

**Prompt-Fragment:**
```
Energetic powerful expression: leaves standing upright and taut, eyes wide open
and gleaming with energy, confident broad smile. Both stick-arms raised outward
in a flexing strongman pose.
```

---

## 5. Groessen-Vereinfachung

Kami wird bei verschiedenen Groessen unterschiedlich detailliert dargestellt. Kleinere Groessen erfordern weniger Details fuer Lesbarkeit und saubere SVGs.

| Groesse | Details | SVG-Komplexitaet |
|---------|---------|-------------------|
| **512px+** | Volle Details: Blatt-Highlights, Topf-Schatten, Dekostreifen, Augen mit Glanzpunkt, Mund, Arme, Erde sichtbar | ~25 Pfade |
| **256px** | Reduziert: Highlight nur als einzelne hellere Flaeche, Schatten vereinfacht, Erde als Linie | ~18 Pfade |
| **128px** | Stark reduziert: Blaetter einfarbig (#66bb6a), Topf einfarbig (#8d6e63) + Streifen, Augen als Punkte, Mund als Linie | ~12 Pfade |
| **64px** | Minimal: Blatt-Silhouetten + Topf-Silhouette, Augen als 2 Punkte, kein Mund, keine Arme | ~8 Pfade |
| **32px** | Nur Grundform: Zwei Blaetter + Trapez-Topf, keine Gesichtszuege, keine Arme, keine inneren Details | ~5 Pfade |

---

## 6. Komposition und Positionierung

### 6.1 Standard-Platzierung in Szenen

```
QUERFORMAT (4:3) — Kami mit Requisit:
┌──────────────────────────────────┐
│  8% Padding                      │
│   ┌─────┐      ┌──────────┐     │
│   │     │      │          │     │
│   │ KAMI│      │ REQUISIT │     │
│   │     │      │          │     │
│   │  30%│      │   50%    │     │
│   └──┬──┘      └────┬─────┘     │
│ ─────┴───────────────┴────────  │ ← Gemeinsame Grundlinie
│  8% Padding                      │
└──────────────────────────────────┘

QUADRAT (1:1) — Kami allein:
┌──────────────────┐
│  10-15% Padding  │
│                  │
│    Blaetter      │
│    Gesicht       │  ← Zentriert
│    Topf          │
│    (unteres 1/3) │
│                  │
└──────────────────┘
```

### 6.2 Kami-Groesse relativ zu Requisiten

| Requisit-Typ | Requisit-Hoehe relativ zu Kami |
|-------------|-------------------------------|
| Grosses Objekt (Tank, Kalender, Buch) | 150–250% von Kamis Hoehe |
| Mittleres Objekt (Giesskanne, Schild) | 50–100% von Kamis Hoehe |
| Kleines Objekt (Lupe, Reagenzglas, Flasche) | 20–40% von Kamis Hoehe |
| Gehaltes Objekt (Klemmbrett, Frucht) | 15–30% von Kamis Hoehe |

---

## 7. SVG-Optimierung — Verbindliche Regeln

Diese Regeln stellen sicher, dass generierte PNGs sauber zu SVGs konvertiert werden koennen:

| Regel | Beschreibung |
|-------|-------------|
| **Minimale Elementgroesse** | Kein Element unter 3px bei Zielgroesse 320px |
| **Flaechige Farben** | Solide Fills, KEINE Gradienten, KEINE Texturen |
| **Klare Kanten** | Deutliche Farbgrenzen zwischen allen Elementen |
| **Farbanzahl** | Maximal 8–10 distinkte Farben pro Bild |
| **Keine feinen Muster** | Keine Schraffuren, Punkte, Linien-Muster |
| **Outline-Konsistenz** | Gleichmaessige Strichstaerke, keine Ausfransung |
| **Kontrastgrenzen** | Benachbarte Flaechen muessen sich im Hex-Wert um mindestens 30% unterscheiden |
| **Pathcount-Ziel** | Gesamtes Bild < 100 Pfade, Kami allein < 25 Pfade |

---

## 8. Verbotsliste (AVOID in jedem Prompt)

Diese Elemente MUESSEN in jedem Bildgenerierungs-Prompt als "Avoid" aufgefuehrt werden:

```
IMMER VERMEIDEN:
- Photorealismus, 3D-Rendering, realistische Texturen
- Gradient-Fuellungen (Farbverlaeufe)
- Harte Schlagschatten (Drop Shadows)
- Text, Buchstaben, Zahlen, Labels im Bild
- Schwarze Outlines (immer Dunkelgruen #1b5e20 oder Kontextfarbe)
- Komplexe Hintergruende oder Szenerien
- Wasserzeichen
- Clip-Art-Stil (zu generisch)
- Kindlich-infantiler Cartoon-Stil (zu unserioes)
- Elemente duenner als 3px (SVG-inkompatibel)
- Mehr als 10 distinkte Farben pro Bild
- Anti-Aliasing-Rauschen (saubere Kanten fuer vtracer)
```

---

## 9. Prompt-Baukasten — Template

Jeder generierte Prompt MUSS diese Struktur einhalten:

```
[1] FORMAT + TYP
"A cute comic-style mascot illustration for a plant management app,
[landscape 4:3 | square 1:1 | wide 4:1] format."

[2] SZENE + EMOTION (aus Abschnitt 4.2)
"Scene: [Beschreibung]. Kami has a [EMOTION-NAME] expression:
[Prompt-Fragment aus Emotionskatalog]."

[3] REQUISITEN (falls vorhanden)
"[Requisit-Beschreibung mit exakten Farben]"

[4] KAMI-FARBEN (immer identisch)
"Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32),
pot #8d6e63 (stripe #a1887f, shadow #6d4c41)."

[5] OUTLINE + HINTERGRUND
"Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. [Format] format, padding [8-15]%."

[6] STIL
"Style: flat vector illustration, cute cartoon, professional. Flat solid colors,
subtle soft inner shading (10-15% darker near form edges). Minimal detail —
clean shapes suitable for SVG conversion. No fine textures, no elements
smaller than 3px."

[7] AVOID
"Avoid: text, numbers, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px,
anti-aliasing artifacts."
```

---

## 10. Quick-Reference: Emotion → Einsatzort

| Emotion | Typische Einsatzorte |
|---------|---------------------|
| Happy | Default, Profilbild, neutrale Zustaende |
| Stolz/Zufrieden | Fuellstand 60%, korrekte Werte, Daumen-hoch-Bestaetigung |
| Gluecklich/Begeistert | Fuellstand 80%, Aufgabe fast fertig, guter Fortschritt |
| Triumphierend/Feiernd | Fuellstand 100%, Ernte, Phasenwechsel, grosser Erfolg |
| Besorgt/Unsicher | Fuellstand 20%, unklarer Status, Warnung |
| Skeptisch/Nachdenklich | Fuellstand 40%, "bald handeln", Suche, Analyse |
| Panisch/Erschrocken | Fuellstand 0%, kritischer Fehler, Notfall |
| Traurig/Enttaeuscht | Fehler, Verbindungsproblem, Aktion fehlgeschlagen |
| Konzentriert/Fokussiert | Mischvorgang, praezise Arbeit, Aufgaben-Bearbeitung |
| Neugierig/Suchend | Leere Listen, Suchergebnisse, Empty State, Laden |
| Einladend/Willkommen | Onboarding, Login, Willkommen, erste Nutzung |
| Friedlich/Geniesserisch | Bluehphase, Genuss-Moment, ruhige Szene |
| Energisch/Kraftvoll | Vegetative Phase, optimaler Zustand, volle Kraft |

---

## 11. Aenderungshistorie

| Version | Datum | Aenderung |
|---------|-------|-----------|
| 1.0 | 2026-03-09 | Initiale Version. Konsolidierung aus Design Guide, allen bestehenden Prompt-Dokumenten. 13 Emotionen definiert, SVG-Optimierungsregeln, Prompt-Template. |
