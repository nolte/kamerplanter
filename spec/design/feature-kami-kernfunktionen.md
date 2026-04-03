# Grafik-Prompts: Kami Kernfunktions-Illustrationen

> **Typ:** Feature-Illustrationen (Serie von 12)
> **Erstellt:** 2026-03-02
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund
> **Zielgroesse:** 320x240px (primaer), skalierbar auf 160x120 und 640x480
> **Format:** PNG (transparent), SVG-tauglich
> **Einsatzort:** Seiten-Header, Willkommens-Bereich auf Listenseiten, Empty States, Onboarding-Kontext
> **Referenz:** Design Guide Abschnitt 5 (Kami), Abschnitt 6 (Illustrationsstil), Sidebar.tsx Navigation

---

## Kontext

Zwoelf Illustrationen von Kami, die jeweils eine Kernfunktion der Applikation
symbolisieren. Jedes Bild zeigt Kami in einer zur Funktion passenden Szene
oder mit einem passenden Gegenstand. Die Bilder lockern die jeweiligen Seiten
auf — sie koennen als Seiten-Header-Dekoration, neben Ueberschriften oder
als Empty-State-Grafik eingesetzt werden.

Alle Bilder muessen:
- Visuell zusammengehoeren (gleicher Stil, gleiche Outline-Staerke, gleicher Kami)
- Im Querformat sein (4:3) damit sie neben Seitenheadern Platz finden
- Bei 160x120px noch erkennbar sein
- Einen klaren visuellen Bezug zur jeweiligen Funktion haben

---

## Gemeinsame Stilregeln (fuer ALLE 12 Bilder)

```
STIL:
- Flat-Vector Comic-Illustration, cute cartoon character
- Klare, gleichmaessige Outlines: 2.5px Aussenkontur, 1.5px innere Details
- Outline-Farbe: dunkles Gruen #1b5e20 (NICHT schwarz)
- Flaechige Farbfuellung, KEINE Gradienten
- Weiche Schatten: 10-15% dunkler als Basisfarbe innerhalb der Form
- Kawaii-inspiriert aber professionell

KAMI-GRUNDFORM (in allen Bildern identisch):
- Anthropomorpher Keimling in Terracotta-Topf
- Terracotta-Topf: trapezfoermig, konisch, Dekostreifen
  Topf-Farben: Basis #8d6e63, Streifen #a1887f, Schatten #6d4c41
- Gesicht: Grosse runde Punkt-Augen (schwarz mit weissem Glanzpunkt),
  kleiner Mund (Ausdruck variiert je Szene)
- Zwei gruene Blaetter oben (#66bb6a, Highlight #98ee99, Schatten #2e7d32)
- Duenne Stiel-Arme seitlich am Topf

KOMPOSITION:
- Querformat 4:3
- Kami steht links oder zentral, Funktions-Requisite rechts oder um ihn herum
- Grosszuegiger Freiraum (Padding ca. 10%)
- Transparenter Hintergrund (PNG alpha)
- Maximal 1-2 Requisiten neben Kami (nicht ueberladen)

VERMEIDEN:
- Photorealismus, 3D-Render, realistische Texturen
- Text, Buchstaben, Beschriftungen im Bild
- Harte Schlagschatten, komplexe Hintergruende
- Schwarze Outlines (immer dunkles Gruen #1b5e20)
- Mehr als 8 Farben pro Illustration
```

---

## 1. Dashboard (Uebersicht)

> **Seite:** `/dashboard`
> **Dateiname:** `feature-kami-dashboard.png`
> **Farb-Akzent:** Primary Gruen #2e7d32

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
standing next to a tiny clipboard or whiteboard showing simple chart symbols:
a small bar chart with 3 bars in green shades and a tiny upward arrow.
Kami looks proud and organized, one arm pointing at the chart, the other
arm on the hip. Happy confident expression with bright eyes and a smile.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Chart/clipboard: white with green bars (#a5d6a7, #66bb6a, #2e7d32).
Arrow accent: #2e7d32. Clipboard border: #795548.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels, no numbers on chart.
```

### Beschreibung

```
Kami steht neben einem kleinen Whiteboard/Klemmbrett mit vereinfachten
Balkendiagramm-Symbolen. Selbstbewusste Pose — „Alles im Blick".
Symbolisiert: Ueberblick, Kontrolle, Status aller Pflanzen.
```

---

## 2. Pflege & Erinnerungen (Care Reminders)

> **Seite:** `/pflege`
> **Dateiname:** `feature-kami-care.png`
> **Farb-Akzent:** Himmelblau #4fc3f7

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
holding a tiny watering can in one arm and a small bell or notification
symbol floating above the other arm. Kami has a caring, attentive expression
with gentle eyes and a warm smile. A few blue water droplets (#4fc3f7) fall
from the watering can. The bell has a tiny exclamation mark.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Watering can: light gray #bdbdbd with blue water drops #4fc3f7.
Bell/notification: golden #ffa726 with tiny white exclamation.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami haelt eine Giesskanne (Wasser tropft) und ueber dem anderen Arm
schwebt eine kleine Benachrichtigungs-Glocke. Fuersorglicher Ausdruck.
Symbolisiert: Pflegeerinnerungen, Giessen, rechtzeitige Pflege.
```

---

## 3. Kalender

> **Seite:** `/kalender`
> **Dateiname:** `feature-kami-calendar.png`
> **Farb-Akzent:** Secondary Indigo #5c6bc0

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
peeking out from behind a large simplified calendar page. The calendar shows
a grid pattern (no readable text or numbers) with a few colored dots on
some cells: green dots (#66bb6a), violet dots (#ab47bc), golden dots (#ffa726).
Kami peeks from the left side with curious eyes and one arm resting on the
calendar edge. The calendar header area is indigo (#5c6bc0).

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Calendar: white paper, header bar #5c6bc0, grid lines light gray #e0e0e0.
Colored event dots: #66bb6a, #ab47bc, #ffa726.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no numbers, no readable dates.
```

### Beschreibung

```
Kami schaut hinter einem grossen Kalenderblatt hervor. Der Kalender hat
ein vereinfachtes Raster mit farbigen Punkten (Gruen, Violett, Gold) als
Ereignisse. Neugieriger Ausdruck.
Symbolisiert: Terminplanung, Uebersicht ueber Aufgaben und Phasen.
```

---

## 4. Meine Pflanzen (Plant Instances)

> **Seite:** `/pflanzen/plant-instances`
> **Dateiname:** `feature-kami-plants.png`
> **Farb-Akzent:** Primary Gruen #2e7d32

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
standing among two other small plants in different pots. One neighbor plant
is taller with broader leaves, the other is a small succulent in a round pot.
Kami has both arms open wide in a welcoming gesture, happy face, as if
introducing friends. The three plants form a small group, Kami in the center.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Kami pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Tall plant: darker green #2e7d32 leaves, lighter pot #a1887f.
Succulent: pale green #a5d6a7, round terracotta pot #8d6e63.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami steht inmitten von zwei anderen (nicht-anthropomorphen) Topfpflanzen
und breitet einladend die Arme aus — „Das sind meine Freunde".
Symbolisiert: Pflanzensammlung, Bestandsuebersicht, Vielfalt.
```

---

## 5. Aufgaben (Tasks & Workflows)

> **Seite:** `/aufgaben/queue`
> **Dateiname:** `feature-kami-tasks.png`
> **Farb-Akzent:** Primary Gruen #2e7d32

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
wearing a tiny construction hard hat (yellow #ffa726) on top of the leaves.
One arm holds a small checklist card with three lines — top line has a green
checkmark (#2e7d32), middle line has a green checkmark, bottom line is empty
(still to do). Kami looks determined and focused, with a confident little smile.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Hard hat: #ffa726 with subtle highlight #ffcc80.
Checklist card: white, checkmarks #2e7d32, empty circle #bdbdbd.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no readable words on checklist.
```

### Beschreibung

```
Kami traegt einen kleinen Bauhelm und haelt eine Checkliste mit
zwei erledigten (gruene Haken) und einer offenen Aufgabe.
Entschlossener, fokussierter Ausdruck.
Symbolisiert: Aufgabenplanung, To-Dos, Workflow-Abarbeitung.
```

---

## 6. Stammdaten (Master Data / Species)

> **Seite:** `/stammdaten/species`
> **Dateiname:** `feature-kami-masterdata.png`
> **Farb-Akzent:** Secondary Indigo #5c6bc0

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
sitting next to an open book. The book is large relative to Kami (about same
height as the pot). On the visible page there are simplified botanical
sketches — a small leaf outline and a tiny flower outline (no readable text).
Kami wears tiny round glasses perched on the face and looks scholarly and
pleased, one arm resting on the book page.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Book: cream-white pages #fafaf5, indigo cover #5c6bc0, spine darker #26418f.
Page sketches: light gray #bdbdbd outlines of leaf and flower shapes.
Glasses: thin dark green frames #1b5e20.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No readable text on book pages.
```

### Beschreibung

```
Kami sitzt neben einem grossen aufgeschlagenen Buch mit vereinfachten
botanischen Skizzen und traegt eine winzige Brille. Gelehrter, zufriedener
Ausdruck.
Symbolisiert: Wissen, Artenkatalog, botanische Daten, Nachschlagewerk.
```

---

## 7. Standorte & Gewaechshaus (Sites / Locations)

> **Seite:** `/standorte/sites`
> **Dateiname:** `feature-kami-locations.png`
> **Farb-Akzent:** Terracotta #8d6e63

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
standing inside a simplified miniature greenhouse frame. The greenhouse is
drawn as a simple A-frame or dome outline with thin structural lines, showing
a pointed roof with a small window panel. Kami stands inside with a happy
expression, arms open, feeling at home. A tiny sun (#ffb74d) peeks from
the upper right corner.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Greenhouse frame: warm brown #a1887f structural lines, glass panels
suggested by very faint light blue tint #e1f5fe.
Sun: #ffb74d with rays #ffa726.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami steht in einem vereinfachten Miniatur-Gewaechshaus-Rahmen,
Arme offen, „Hier bin ich zuhause". Kleine Sonne oben rechts.
Symbolisiert: Standorte, Anbauflaechen, Gewaechshaus, Indoor/Outdoor.
```

---

## 8. Duengung & Naehrstoffe (Fertilization)

> **Seite:** `/duengung/fertilizers`
> **Dateiname:** `feature-kami-fertilizer.png`
> **Farb-Akzent:** Indigo #5c6bc0

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
acting as a scientist. Kami holds a small test tube or beaker in one arm,
filled with bright green liquid (#66bb6a). Next to Kami stands a tiny bottle
labeled with a simple droplet symbol (no text). Kami wears a miniature lab
coat (white #ffffff with indigo collar #5c6bc0) and has a focused, excited
expression — eyes wide with curiosity, small open mouth.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Test tube: clear glass outline with green liquid #66bb6a inside.
Bottle: white with indigo cap #5c6bc0 and droplet symbol.
Lab coat: white #ffffff, collar #5c6bc0.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels on bottles.
```

### Beschreibung

```
Kami als kleiner Wissenschaftler im Laborkittel, haelt ein Reagenzglas
mit gruener Naehrloesung. Daneben eine Duengerflasche.
Aufgeregter, neugieriger Ausdruck.
Symbolisiert: Duengung, Naehrstoffmischung, EC/pH, Wissenschaft.
```

---

## 9. Pflanzenschutz / IPM

> **Seite:** `/pflanzenschutz/pests`
> **Dateiname:** `feature-kami-ipm.png`
> **Farb-Akzent:** Error Rot #d32f2f + Primary Gruen #2e7d32

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
holding a tiny shield in one arm. The shield is green (#2e7d32) with a
small leaf emblem on it. With the other arm Kami holds up a tiny magnifying
glass. Kami has a brave, protective expression — determined eyes, small
confident smile. A tiny stylized cartoon bug (very simple: round body,
dot eyes, antennae) in red-orange (#d32f2f) sits near the bottom, looking
nervous and backing away from the shield.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Shield: green #2e7d32 with lighter leaf emblem #81c784.
Magnifying glass: gray handle #9e9e9e, glass circle clear with slight glint.
Cartoon bug: #d32f2f body, thin dark legs, dot eyes, tiny antennae.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami als Beschuetzer: haelt einen kleinen gruenen Schild mit Blatt-Emblem
und eine Lupe. Ein winziger, stilisierter Comic-Kaefer weicht zurueck.
Mutiger, entschlossener Ausdruck.
Symbolisiert: Pflanzenschutz, Schaedlingsabwehr, IPM, Inspektion.
```

---

## 10. Ernte (Harvest)

> **Seite:** `/ernte/batches`
> **Dateiname:** `feature-kami-harvest.png`
> **Farb-Akzent:** Goldgelb #ffa726

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
standing next to a small woven harvest basket. The basket contains 3-4
round golden-orange fruits (#ffa726) and one red tomato-like fruit (#d32f2f),
overflowing slightly. Kami is celebrating — both arms raised, eyes closed
in joy, big happy smile, leaves perked up. A few tiny golden sparkles
float around the basket.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Basket: woven pattern in #a1887f and #8d6e63.
Golden fruits: #ffa726, highlight #ffcc80, shadow #f57c00.
Red fruit: #d32f2f, highlight #ef5350.
Sparkles: #ffa726 tiny star shapes.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami feiert neben einem kleinen Erntekorb voller goldener und roter
Fruechte. Arme hoch, Augen zu vor Freude, goldene Funkeln.
Symbolisiert: Ernte, Ertrag, Erfolg, Belohnung fuer die Arbeit.
```

---

## 11. Pflanzdurchlaeufe (Planting Runs / Batches)

> **Seite:** `/durchlaeufe/planting-runs`
> **Dateiname:** `feature-kami-planting-runs.png`
> **Farb-Akzent:** Primary Gruen #2e7d32

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
standing at the head of a row of 3 smaller identical seedling pots behind
it. The 3 background pots are simpler (no faces, just small green sprouts)
and arranged in a diagonal line receding to the right, getting slightly
smaller to suggest depth. Kami stands in front like a group leader, one arm
raised as if giving a signal to start. Proud, leadership expression.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Kami pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Background seedlings: simpler, leaves #a5d6a7, pots #a1887f, no faces.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami steht als Anfuehrer vor einer Reihe von 3 kleineren Keimlingen
in Toepfen (ohne Gesichter). Fuehrungspose, ein Arm erhoben.
Symbolisiert: Gruppenverwaltung, Chargen, Pflanzdurchlaeufe als Batch.
```

---

## 12. Tankmanagement & Bewaesserung (Tanks / Watering)

> **Seite:** `/standorte/tanks`
> **Dateiname:** `feature-kami-tanks.png`
> **Farb-Akzent:** Himmelblau #4fc3f7

### Prompt

```
A cute comic-style mascot illustration for a plant management app.
A small anthropomorphic green seedling character (Kami) in a terracotta pot,
standing next to a simplified water tank or barrel. The tank is round,
about twice Kami's height, drawn as a simple cylinder with a small faucet
at the bottom. The tank is partially filled with blue water (#4fc3f7),
visible through a transparent section or water level line. A few water
droplets drip from the faucet. Kami looks up at the tank with an impressed,
satisfied expression, one arm giving a thumbs-up gesture.

Colors: Kami leaves #66bb6a, highlights #98ee99, shadows #2e7d32.
Pot: #8d6e63, stripe #a1887f, shadow #6d4c41.
Tank: light gray #bdbdbd body, darker rim #9e9e9e, faucet #795548.
Water inside: #4fc3f7 with lighter surface highlight #b3e5fc.
Water drops: #4fc3f7.
Outlines: dark green #1b5e20, 2-3px, rounded ends.

Style: flat vector illustration, cute cartoon, professional.
Flat colors, subtle soft shading. Landscape 4:3 format.
Transparent background. No text, no labels.
```

### Beschreibung

```
Kami steht neben einem grossen, vereinfachten Wassertank mit sichtbarem
Fuellstand (blau). Aus dem Hahn tropft Wasser. Kami schaut beeindruckt
nach oben und zeigt Daumen hoch.
Symbolisiert: Tankmanagement, Wasservorrat, Bewaesserungssystem.
```

---

## Gesamtuebersicht

```
  Nr  Funktion           Requisit                  Kami-Ausdruck     Farb-Akzent
  ──  ─────────────────  ────────────────────────  ────────────────  ──────────
   1  Dashboard          Whiteboard + Balkendiag.  Selbstbewusst     #2e7d32
   2  Pflege             Giesskanne + Glocke       Fuersorglich      #4fc3f7
   3  Kalender           Kalenderblatt + Punkte    Neugierig         #5c6bc0
   4  Meine Pflanzen     2 Nachbar-Topfpflanzen    Einladend         #2e7d32
   5  Aufgaben           Bauhelm + Checkliste      Entschlossen      #ffa726
   6  Stammdaten         Buch + Brille             Gelehrt           #5c6bc0
   7  Standorte          Gewaechshaus-Rahmen       Zufrieden         #8d6e63
   8  Duengung           Laborkittel + Reagenzgl.  Aufgeregt         #5c6bc0
   9  Pflanzenschutz     Schild + Lupe + Kaefer    Mutig             #d32f2f
  10  Ernte              Erntekorb + Fruechte      Feiernd           #ffa726
  11  Durchlaeufe        3 Keimlings-Reihe         Anfuehrer         #2e7d32
  12  Tanks              Wassertank + Tropfen      Beeindruckt       #4fc3f7
```

---

## Zusammenhaengende Reihe (Alternative: ein Prompt fuer konsistenten Stil)

Falls Einzelgenerierung zu inkonsistente Stile erzeugt, diesen Meta-Prompt verwenden um den Stil zu etablieren und dann Einzelbilder nachzugenerieren:

### Stil-Referenz-Prompt (alle 12 als Grid)

```
A grid of 12 small character illustrations in identical cute comic style,
arranged in a 4x3 grid. Each shows the same mascot character — a small
anthropomorphic green seedling with two leaves growing from a terracotta pot,
with a friendly face (dot eyes, small mouth), thin stick-arms.

The 12 scenes (left to right, top to bottom):
1. Standing next to a small whiteboard with bar chart symbols
2. Holding a watering can with blue water drops, notification bell floating
3. Peeking behind a calendar page with colored dots
4. Surrounded by two other small potted plants, arms open
5. Wearing a tiny yellow hard hat, holding a checklist
6. Sitting next to an open book, wearing tiny glasses
7. Standing inside a miniature greenhouse frame
8. Wearing a lab coat, holding a green test tube
9. Holding a green shield and magnifying glass, tiny red bug nearby
10. Celebrating next to a basket of golden fruits
11. Leading a row of 3 smaller seedling pots
12. Thumbs up next to a tall water tank with blue water

All scenes use identical character proportions, outline weight (2-3px dark
green #1b5e20), and flat color style. Terracotta pots (#8d6e63). Green
leaves (#66bb6a). Flat vector illustration, cartoon style, transparent or
white background. No text in any image.
```

---

## Technische Hinweise

1. **Konsistenz:** Kami muss in allen 12 Bildern identisch aussehen (gleiche Proportionen, Augengroesse, Topfform). Bei starken Abweichungen: Stil-Referenz-Prompt (Grid) zuerst generieren, dann als Style-Reference fuer Einzelbilder verwenden.
2. **Querformat:** 4:3 ist wichtig fuer die Platzierung neben Seiten-Headern. Hochformat funktioniert nicht im Layout.
3. **Requisiten-Groesse:** Requisiten (Buch, Tank, Kalender etc.) sollten relativ zu Kami proportioniert sein — nicht riesig, nicht winzig. Richtwert: 50-120% von Kamis Hoehe.
4. **Farbkonsistenz:** Kami selbst hat in ALLEN Bildern die gleichen Farben. Nur die Requisiten/Kontext-Elemente variieren.
5. **Skalierung:** Bei 160x120px muessen Kami + Hauptrequisit noch erkennbar sein. Feine Details (Brillengestell, Checklist-Linien) duerfen verschwinden.
6. **Dark-Mode:** Transparenter Hintergrund reicht fuer beide Modi. Fuer explizite Dark-Varianten Outlines auf #c8e6c9 aendern.

## Nachbearbeitung Checkliste

- [ ] Alle 12 Bilder auf exakt gleiche Groesse zuschneiden (320x240px)
- [ ] Kami-Proportionen zwischen Bildern vergleichen und ggf. angleichen
- [ ] Hintergrund sauber transparent
- [ ] Auf 160x120 skalieren und Erkennbarkeit pruefen
- [ ] Auf 640x480 skalieren fuer Retina/HiDPI
- [ ] Farbwerte gegen Design-Guide-Palette pruefen
- [ ] Optional: Dark-Mode-Varianten mit hellen Outlines (#c8e6c9) erstellen
- [ ] Dateien ablegen unter: `assets/brand/illustrations/features/`
- [ ] Namenskonvention: `feature-kami-{name}.{format}`

## Einsatzorte in der App

| Bild | Primaerer Einsatz | Sekundaerer Einsatz |
|------|-------------------|---------------------|
| dashboard | Dashboard-Header | Onboarding Schritt „Fertig" |
| care | PflegeDashboardPage Header | Empty State: keine Erinnerungen |
| calendar | CalendarPage Header | Empty State: keine Termine |
| plants | PlantInstanceListPage Header | Empty State: keine Pflanzen |
| tasks | TaskQueuePage Header | Empty State: keine Aufgaben |
| masterdata | SpeciesListPage Header | Empty State: keine Arten |
| locations | SiteListPage Header | Empty State: keine Standorte |
| fertilizer | FertilizerListPage Header | NutrientPlanListPage Deko |
| ipm | PestListPage Header | DiseaseListPage, TreatmentListPage |
| harvest | HarvestBatchListPage Header | Empty State: keine Ernten |
| planting-runs | PlantingRunListPage Header | Empty State: keine Durchlaeufe |
| tanks | TankListPage Header | WateringEventPage Deko |
