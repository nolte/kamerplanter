# Grafik-Prompts: Kami Navigations-Icon-Serie (Sidebar)

> **Typ:** nav-icon (Serie von 27)
> **Erstellt:** 2026-03-09
> **Varianten:** Light Mode (primaer, SVG-Konvertierung vorgesehen)
> **Zielgroesse:** 128×128px (primaer), muss bei 32×32px noch lesbar sein
> **Format:** PNG (transparent), SVG-tauglich
> **Einsatzort:** Sidebar-Navigation, ersetzt MUI Material Icons
> **Referenz:** KAMI-CHARACTER-REFERENCE.md v1.0, feature-kami-kernfunktionen.md, Sidebar.tsx

---

## Kontext

27 quadratische Navigations-Icons fuer die Kamerplanter-Sidebar. Jedes Icon zeigt Kami in
einer thematischen Mini-Szene, die den jeweiligen Navigationsbereich sofort kommuniziert.
Die Icons ersetzen generische MUI-Icons und geben der Navigation eine unverwechselbare
Kamerplanter-Persoenlichkeit.

Der entscheidende Unterschied zu den Kernfunktions-Illustrationen (feature-kami-*.png):
Icons sind quadratisch (1:1), wesentlich kompakter, die Requisite ist auf das absolute
Minimum reduziert und Kami ist noch kleiner relativ zur Gesamt-Flaeche. Bei 32×32px
muss die Silhouette noch das Thema vermitteln.

**Abgrenzung zu bestehenden Dateien:** Die feature-kami-kernfunktionen.md deckt 12 Themen
als Querformat-Illustrationen ab. Diese Datei erstellt eigenstaendige 1:1-Icon-Prompts
fuer alle 27 Sidebar-Eintraege — kein Duplikat, anderes Format, anderer Einsatzort.

---

## Gemeinsamer Stil-Block (fuer ALLE 27 Icons)

Dieser Block ist in jedem einzelnen Icon-Prompt integriert. Er wird hier einmal
vollstaendig definiert und in den Einzelprompts als kompakter Inline-Block referenziert.

```
GEMEINSAME KAMI-NAVIGATION-ICON STILREGELN:

FORMAT: Square 1:1 aspect ratio. 128x128px primary output.
Fully transparent PNG background (alpha channel). No background fill, no
ground shadow beneath the pot.

KAMI-KOERPER (identisch in allen 27 Icons):
- Anthropomorphic green seedling in terracotta pot
- Pot: trapezoidal (wider at top), flat base
  Colors: base #8d6e63, decorative stripe #a1887f, shadow side #6d4c41
- Two leaf-shaped forms growing from top of stem
  Colors: #66bb6a (main), highlight inner area #98ee99, base shadow #2e7d32
- Thin curved stem connecting pot to face/leaves
  Color: #43a047
- Face positioned between leaves and pot rim: two round dot eyes (#000000
  with white highlight glint #ffffff), small curved mouth (expression varies)
- Thin stick arms at pot sides (omit at 32px render)
- Visible soil surface at pot top: #795548

ICON-KOMPOSITION (1:1 quadratisch):
- Kami centered horizontally, occupies lower 55-60% of icon height
- Requisite/context element in upper area or alongside, max 1 element
- Padding: 12-15% on all sides — no element touches the icon edge
- Kami height: approx 50-60% of total icon height
- Requisite scale: small enough to read as a symbol, not compete with Kami

OUTLINE-SYSTEM:
- All outlines: dark green #1b5e20
- Outer contour: 2.5px
- Inner details: 1.5px
- Line ends: round cap, round join
- NO black outlines anywhere

STIL:
- Flat vector illustration, clean comic style, kawaii-influenced but professional
- Solid fill colors ONLY — no gradients, no textures, no hatching
- Subtle inner shading: 10-15% darker than base color near form edges only
  (achieved via slightly darker solid shape, not gradient)
- Maximum 8 distinct colors per icon
- Minimum element size: 3px at 128px render
- Total path count target: under 40 paths per icon

IMMER VERMEIDEN:
- Text, numbers, letters anywhere in the image
- Gradients or color transitions
- Drop shadows (hard or soft)
- Photorealism, 3D rendering, realistic textures
- Black outlines (always dark green #1b5e20)
- Complex backgrounds or environment details
- More than 8 distinct colors
- Elements smaller than 3px
- Anti-aliasing artifacts (clean edges for vtracer conversion)
- Clip-art style, childish infantile cartoon style
- Watermarks
```

---

## Groessen-Vereinfachungsregeln fuer Icons

| Rendergroesse | Kami-Details | Requisite |
|---------------|--------------|-----------|
| 128px | Voll: Gesicht, Arme, Dekostreifen, Blatt-Highlights, Erde | Vollstaendig dargestellt |
| 64px | Reduziert: Gesicht (2 Punkte + Strich), kein Dekostreifen, keine Erde | Auf Silhouette reduziert |
| 32px | Minimal: Blatt-Silhouetten + Topf-Trapez, 2 Punkt-Augen, keine Arme | Nur dominante Form |

---

## Emotions-Zuweisung — Planungsmatrix

| Nr | Seite | Emotion | Begruendung |
|----|-------|---------|-------------|
| 1 | Dashboard | STOLZ/ZUFRIEDEN | Kontrolle, alles im Blick |
| 2 | Pflege | FRIEDLICH/GENIESSERISCH | Fuersorgliche Pflege, ruhiger Rhythmus |
| 3 | Kalender | NEUGIERIG/SUCHEND | Was steht an? Termine erkunden |
| 4 | Meine Pflanzen | EINLADEND/WILLKOMMEN | Sammlung praesentieren |
| 5 | Berechnungen | KONZENTRIERT/FOKUSSIERT | Praezise numerische Arbeit |
| 6 | Aufgaben-Warteschlange | KONZENTRIERT/FOKUSSIERT | Abarbeiten, To-Do erledigen |
| 7 | Workflows | SKEPTISCH/NACHDENKLICH | Planung, Analyse, Struktur |
| 8 | Botanische Familien | HAPPY | Taxonomie, Ordnung, Wissen |
| 9 | Arten | NEUGIERIG/SUCHEND | Lexikon durchstoebern |
| 10 | Mischkultur | GLUECKLICH/BEGEISTERT | Symbiose, Gemeinschaft |
| 11 | Fruchtfolge | SKEPTISCH/NACHDENKLICH | Planung, Zyklus-Denken |
| 12 | Import | KONZENTRIERT/FOKUSSIERT | Daten einladen, praezise Arbeit |
| 13 | Standorte | STOLZ/ZUFRIEDEN | Anbauplaetze, Heimat |
| 14 | Substrate | NEUGIERIG/SUCHEND | Medien untersuchen |
| 15 | Tanks | STOLZ/ZUFRIEDEN | Vorrat, Kontrolle |
| 16 | Bewaesserungs-Ereignisse | FRIEDLICH/GENIESSERISCH | Giessen als ruhiges Ritual |
| 17 | Duengemittel | ENERGISCH/KRAFTVOLL | Naehrstoffe = Kraft |
| 18 | Naehrstoffplaene | SKEPTISCH/NACHDENKLICH | Dosierung planen, abwaegen |
| 19 | Duenge-Ereignisse | KONZENTRIERT/FOKUSSIERT | Praezises Protokollieren |
| 20 | Naehrstoff-Berechnungen | KONZENTRIERT/FOKUSSIERT | EC/pH-Kalkulation |
| 21 | Schaedlinge | PANISCH/ERSCHROCKEN | Bedrohung erkennen |
| 22 | Krankheiten | BESORGT/UNSICHER | Diagnose, Sorge |
| 23 | Behandlungen | ENERGISCH/KRAFTVOLL | Aktiv gegensteuern |
| 24 | Ernte-Chargen | TRIUMPHIEREND/FEIERND | Groesster Erfolg |
| 25 | Pflanzdurchlaeufe | STOLZ/ZUFRIEDEN | Gruppen-Leadership |
| 26 | Admin-Einstellungen | SKEPTISCH/NACHDENKLICH | Konfiguration, Analyse |
| 27 | Einstellungen | HAPPY | Persoenliche Anpassung |

---

## Icon 01 — Dashboard

> **Pfad:** `/dashboard` | **MUI-Icon:** DashboardIcon
> **Emotion:** STOLZ/ZUFRIEDEN
> **Requisite:** Winziges Klemmbrett mit 3-Balken-Minidiagramm

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami, a small anthropomorphic green seedling in a terracotta pot, stands
centered in the lower half of the icon. Kami holds a tiny clipboard in one arm.
The clipboard displays a minimal 3-bar chart (3 solid rectangles of increasing
height: colors #a5d6a7, #66bb6a, #2e7d32) with a tiny upward-pointing arrow
above the tallest bar. The clipboard backing is white with a brown clip #795548.

Proud content expression: leaves perked upward, eyes slightly narrowed with
confidence, broad satisfied smile. One arm holding the clipboard out front,
other arm on hip.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Clipboard: white #ffffff body, clip #795548, chart bars #a5d6a7 / #66bb6a / #2e7d32,
arrow #2e7d32.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid fill colors
only, no gradients. Subtle inner shading 10-15% darker near edges. Square format,
12% padding on all sides. Max 8 colors. Min element size 3px.

Avoid: text, numbers on chart, gradients, black outlines, drop shadows, photorealism,
3D, complex backgrounds, elements under 3px, watermarks, anti-aliasing artifacts.
```

---

## Icon 02 — Pflege & Erinnerungen

> **Pfad:** `/pflege` | **MUI-Icon:** NotificationsActiveIcon
> **Emotion:** FRIEDLICH/GENIESSERISCH
> **Requisite:** Kleine Giesskanne, Benachrichtigungs-Glocke schwebend

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami, a small anthropomorphic green seedling in a terracotta pot, stands
centered. Kami holds a small watering can (#bdbdbd body, blue spout rim) in one
arm, tilted to pour. Three small blue water droplets (#4fc3f7) fall from the
spout. A tiny golden bell (#ffa726) floats above one of the leaves, slightly
off to the side, with small curved motion lines suggesting it is ringing.

Peaceful serene expression: leaves relaxed and gently spread outward, eyes
half-closed in a dreamy content manner, soft gentle smile. Arms relaxed, one
arm holding the watering can gently.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Watering can: #bdbdbd body, darker rim #9e9e9e, spout tip #9e9e9e.
Water droplets: #4fc3f7.
Bell: #ffa726 with highlight #ffcc80, small motion lines #ffa726.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 8 colors. Min 3px elements.

Avoid: text, numbers, gradients, black outlines, drop shadows, photorealism,
3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 03 — Kalender

> **Pfad:** `/kalender` | **MUI-Icon:** CalendarMonthIcon
> **Emotion:** NEUGIERIG/SUCHEND
> **Requisite:** Kleines Kalenderblatt mit Raster, Kami schaut darueber

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: A simplified calendar page occupies the upper-right portion of the icon,
slightly larger than Kami. The calendar has a solid indigo header bar (#5c6bc0),
a white body with a minimal 3x2 grid (light gray lines #e0e0e0), and 3 tiny
colored dots on cells: one green (#66bb6a), one violet (#ab47bc), one golden
(#ffa726). Kami peeks from the lower-left, one arm resting on the bottom edge
of the calendar, the other arm at chin in a curious gesture.

Curious searching expression: leaves tilted slightly forward and sideways, one
eye slightly larger than the other with curiosity, small open "oh" mouth.
One arm resting on calendar edge, other arm at chin.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Calendar: white #ffffff, header #5c6bc0, grid lines #e0e0e0.
Event dots: #66bb6a, #ab47bc, #ffa726.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 8 colors. Min 3px elements.

Avoid: text, numbers, readable dates, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 04 — Meine Pflanzen

> **Pfad:** `/pflanzen/plant-instances` | **MUI-Icon:** LocalFloristIcon
> **Emotion:** EINLADEND/WILLKOMMEN
> **Requisite:** Zwei kleinere Topfpflanzen (ohne Gesicht) neben Kami

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered at the bottom of the icon. To the left stands a small
faceless plant in a pot with two broad rounded leaves (#a5d6a7, smaller pot #a1887f).
To the right stands a tiny round succulent in a small round pot (#a5d6a7 plump
rosette shape, pot #8d6e63). All three plants share the same bottom baseline.
Kami has both arms spread outward in a welcoming presenting gesture, as if
introducing the two neighbor plants.

Welcoming inviting expression: leaves perked upward and lively, large bright
wide eyes with highlight glints, broad warm smile. Both arms extended outward
in greeting, open inviting body language.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Left plant: leaves #a5d6a7, pot #a1887f.
Right succulent: rosette #a5d6a7, pot #8d6e63.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 7 colors. Min 3px elements.

Avoid: faces on neighbor plants, text, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 05 — Berechnungen

> **Pfad:** `/pflanzen/calculations` | **MUI-Icon:** CalculateIcon
> **Emotion:** KONZENTRIERT/FOKUSSIERT
> **Requisite:** Winziger Taschenrechner

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered. Kami holds a tiny calculator in both arms, slightly
elevated and angled toward the viewer. The calculator is a simple rounded-rectangle
shape (#9e9e9e body, #bdbdbd front face) with a small dark display area (#424242)
at the top and a 2x3 grid of tiny round buttons below (#757575 buttons). No
readable numbers or symbols on the display.

Focused determined expression: leaves upright and slightly tilted forward, eyes
narrowed with concentration, mouth as a tight determined line with tiny tongue
tip visible. Both arms engaged with the calculator.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Calculator: body #9e9e9e, face panel #bdbdbd, display #424242, buttons #757575.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 7 colors. Min 3px elements.

Avoid: numbers, symbols, readable display content, gradients, black outlines,
drop shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 06 — Aufgaben-Warteschlange

> **Pfad:** `/aufgaben/queue` | **MUI-Icon:** TaskAltIcon
> **Emotion:** KONZENTRIERT/FOKUSSIERT
> **Requisite:** Checkliste mit 2 Haken und 1 offenem Punkt, kleiner Bauhelm

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered, wearing a tiny yellow hard hat (#ffa726, highlight
#ffcc80) balanced on top of the two leaves. Kami holds a small checklist card
(white #ffffff rectangle) in one arm. The checklist shows 3 horizontal lines:
the top two lines each have a small solid green checkmark (#2e7d32) on the left,
the bottom line has a small empty circle (#bdbdbd) — one task remaining.

Focused determined expression: leaves upright and slightly tilted forward, eyes
narrowed with concentration, mouth as a tight determined line. Arm holding
checklist angled outward for reading.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Hard hat: #ffa726, highlight #ffcc80, rim shadow #f57c00.
Checklist: white #ffffff, card edge #e0e0e0, checkmarks #2e7d32, open circle #bdbdbd.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 8 colors. Min 3px elements.

Avoid: text, readable words on checklist, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 07 — Workflows

> **Pfad:** `/aufgaben/workflows` | **MUI-Icon:** AccountTreeIcon
> **Emotion:** SKEPTISCH/NACHDENKLICH
> **Requisite:** Kleines Flussdiagramm mit 3 verbundenen Knoetchen

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands slightly left of center, looking up at a small flow diagram
floating in the upper-right area. The diagram shows 3 small circles connected
by thin lines with arrows: a top circle (#5c6bc0 indigo), a middle-left circle
(#66bb6a green), and a bottom circle (#8e99f3 light indigo), connected by thin
dark green lines with small arrowheads. The diagram is compact, clearly a
workflow symbol.

Skeptical thinking expression: leaves asymmetric (one perked up, one at neutral
angle), eyes open and alert with one slightly higher than the other, mouth as a
small diagonal line. One arm on hip, other arm raised with index finger pointing
upward toward the diagram.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Diagram nodes: #5c6bc0, #66bb6a, #8e99f3.
Diagram lines/arrows: #1b5e20 thin strokes.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 8 colors. Min 3px elements.

Avoid: text, labels on diagram nodes, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 08 — Botanische Familien

> **Pfad:** `/stammdaten/botanical-families` | **MUI-Icon:** ParkIcon
> **Emotion:** HAPPY
> **Requisite:** Kleines vereinfachtes Laubbaum-Symbol

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered at the bottom. Behind and slightly above Kami rises
a simple miniature tree: a brown trunk (#795548, narrow rectangle) topped by a
large rounded crown (a single filled circle #60ad5e with a subtle inner area
#81c784). The tree crown is about the same height as Kami. The tree does not
have internal detail — just the clean silhouette. Kami looks up happily at it.

Happy expression: leaves pointing straight upward, large round dot eyes with
white highlight glints, small curved upward smile. Arms relaxed at sides.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Tree trunk: #795548.
Tree crown: #60ad5e outer, inner lighter area #81c784.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 7 colors. Min 3px elements.

Avoid: text, leaf details in crown, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 09 — Arten (Species)

> **Pfad:** `/stammdaten/species` | **MUI-Icon:** ScienceIcon
> **Emotion:** NEUGIERIG/SUCHEND
> **Requisite:** Aufgeschlagenes kleines Buch mit botanischer Blatt-Skizze

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands left of center, leaning slightly forward with curiosity. Next
to Kami, slightly taller, stands an open book. The book has an indigo cover
(#5c6bc0 spine, #26418f back edge) and cream-white pages (#fafaf5). On the
visible page is a single simplified leaf outline sketch (thin gray lines #bdbdbd
in a leaf shape) — no other detail. Kami wears tiny round glasses (thin dark
green frames #1b5e20) perched on the face. One arm rests on the open book page.

Curious searching expression: leaves tilted slightly forward and sideways, one
eye slightly larger than the other with curiosity, small open mouth. One arm
resting on book, other arm at chin. Tiny round glasses on face.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Book cover spine: #5c6bc0, back: #26418f. Pages: #fafaf5.
Page sketch lines: #bdbdbd (leaf outline only).
Glasses: #1b5e20 thin frames.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 8 colors. Min 3px elements.

Avoid: text on book pages, readable botanical names, gradients, black outlines,
drop shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 10 — Mischkultur (Companion Planting)

> **Pfad:** `/stammdaten/companion-planting` | **MUI-Icon:** Diversity3Icon
> **Emotion:** GLUECKLICH/BEGEISTERT
> **Requisite:** Zwei kleine Topfpflanzen eng beieinander, Herz-Symbol schwebend

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered at the bottom. To the immediate left of Kami's pot
stands a small faceless herb plant (narrow leaves #a5d6a7, small pot #a1887f).
To the immediate right of Kami stands another small faceless plant with round
leaves (#81c784, small pot #8d6e63). All three pots touch or nearly touch at
the base. Above the group, centered, floats a small simple heart symbol
(#d32f2f or #ab47bc, flat filled heart shape). The three plants are cozy and
close together.

Joyful delighted expression: leaves spread outward energetically, eyes closed
in happy anime-style crescents (^^), wide open bright smile. Both arms spread
outward in a proud presenting gesture embracing the group.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Left herb plant: leaves #a5d6a7, pot #a1887f.
Right round-leaf plant: leaves #81c784, pot #8d6e63.
Floating heart: #ab47bc.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 8 colors. Min 3px elements.

Avoid: faces on neighbor plants, text, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 11 — Fruchtfolge (Crop Rotation)

> **Pfad:** `/stammdaten/crop-rotation` | **MUI-Icon:** LoopIcon
> **Emotion:** SKEPTISCH/NACHDENKLICH
> **Requisite:** Kreisfoermiger Pfeil (Rotations-Symbol) mit 4 kleinen Farb-Segmenten

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: A circular rotation arrow dominates the upper half of the icon — a thick
circular arc with an arrowhead at one end, rendered in dark green (#1b5e20),
suggesting a cycle. The arc is divided into 4 color segments by 4 small colored
dots placed on the arc: green (#66bb6a), golden (#ffa726), light brown (#a1887f),
and pale green (#c8e6c9). Kami stands in the lower center, looking up at the
rotation symbol with a planning expression. One arm raised with finger pointing
upward at the rotation symbol.

Skeptical thinking expression: leaves asymmetric (one perked up, one at neutral
angle), eyes open and alert with one slightly higher, mouth as a small diagonal
line. One arm raised with index finger pointing at the rotation arc.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Rotation arc: #1b5e20 thick stroke with arrowhead.
Segment dots: #66bb6a, #ffa726, #a1887f, #c8e6c9.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 7 colors. Min 3px elements.

Avoid: text, numbers, gradients, black outlines, drop shadows, photorealism,
3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 12 — Import

> **Pfad:** `/stammdaten/import` | **MUI-Icon:** FileUploadIcon
> **Emotion:** KONZENTRIERT/FOKUSSIERT
> **Requisite:** Kleines Dokument mit Aufwaerts-Pfeil (Upload-Symbol)

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered, holding a small document card in front with both
arms. The document is a simple white rectangle (#ffffff) with rounded top-right
corner folded (suggesting a file), with a solid upward-pointing arrow
(#2e7d32) centered on the face of the document. Below the arrow on the document
are 3 short horizontal lines (#e0e0e0) suggesting data rows — but no readable
content. The document is about 40% of Kami's total height.

Focused determined expression: leaves upright and slightly tilted forward, eyes
narrowed with concentration, mouth as a tight determined line. Both arms holding
document forward.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Document: white #ffffff, folded corner #e0e0e0, upload arrow #2e7d32.
Row lines on document: #e0e0e0.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 7 colors. Min 3px elements.

Avoid: text, readable filenames, CSV label, gradients, black outlines, drop
shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 13 — Standorte (Sites)

> **Pfad:** `/standorte/sites` | **MUI-Icon:** PlaceIcon
> **Emotion:** STOLZ/ZUFRIEDEN
> **Requisite:** Kleines vereinfachtes Gewaechshaus-Dach (A-Frame Silhouette)

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered at the bottom. Around Kami, partially framing the
scene, is a simplified miniature greenhouse A-frame structure: two diagonal brown
lines (#a1887f) meeting at a peak above Kami's leaves, like a tent or greenhouse
roof outline. The structure is minimal — just the two angled side lines and the
peak, with a small horizontal base line. A tiny golden sun (#ffb74d, simple
circle with 4 short ray lines) floats in the upper-right corner.

Proud content expression: leaves perked upward, eyes slightly narrowed with
confidence, broad satisfied smile. One arm giving thumbs-up, other arm on hip.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Greenhouse frame: #a1887f stroke lines, 2px weight.
Sun: #ffb74d circle, rays #ffa726.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 7 colors. Min 3px elements.

Avoid: text, complex greenhouse details, glass panes, gradients, black outlines,
drop shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 14 — Substrate

> **Pfad:** `/standorte/substrates` | **MUI-Icon:** LayersIcon
> **Emotion:** NEUGIERIG/SUCHEND
> **Requisite:** Drei uebereinander liegende Schichten (Schichten-Symbol), Kami schaut hin

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: To the right of Kami float three horizontal stacked layers, each a
rounded-rectangle strip, overlapping slightly like a layers icon:
- Top layer: sandy beige (#e8d5b7, suggesting perlite/sand)
- Middle layer: brown (#795548, suggesting potting mix)
- Bottom layer: dark brown (#5d4037, suggesting soil)
Each strip has a thin outline, clearly distinct by color. Kami leans slightly
forward, one arm at chin, examining the layers with curiosity.

Curious searching expression: leaves tilted slightly forward and sideways, one
eye slightly larger than the other with curiosity, small open "oh" mouth. One
arm at chin in examining gesture.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Layer top: #e8d5b7. Layer middle: #795548. Layer bottom: #5d4037.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 7 colors. Min 3px elements.

Avoid: text, realistic soil textures, grain patterns, gradients, black outlines,
drop shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 15 — Tanks

> **Pfad:** `/standorte/tanks` | **MUI-Icon:** WaterDropIcon
> **Emotion:** STOLZ/ZUFRIEDEN
> **Requisite:** Kleiner zylindrischer Wassertank mit sichtbarem Fuellstand

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands to the left, next to a simplified cylindrical tank. The tank
is about 80% of Kami's total height, drawn as a simple cylinder: round top with
a small cap, cylindrical body (#bdbdbd light gray), with a horizontal fill line
about 65% up from the bottom. Below the fill line the body shows light blue
(#4fc3f7) suggesting water. A tiny faucet knob (#795548) at the lower right of
the tank. Kami looks at the tank with satisfaction, one arm giving thumbs-up.

Proud content expression: leaves perked upward, eyes slightly narrowed with
confidence, broad satisfied smile. One arm thumbs-up toward the tank.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Tank body: #bdbdbd, rim #9e9e9e, water fill #4fc3f7, water surface highlight #b3e5fc.
Faucet: #795548.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 7 colors. Min 3px elements.

Avoid: text, EC/pH labels, pipe details, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 16 — Bewaesserungs-Ereignisse (Watering Events)

> **Pfad:** `/standorte/watering-events` | **MUI-Icon:** WaterIcon
> **Emotion:** FRIEDLICH/GENIESSERISCH
> **Requisite:** Grosse Giesskanne, Wasser-Regenbogen aus Brausekopf

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered at the bottom right of the icon, receiving water.
A large (relative to Kami) watering can tilted at 45 degrees occupies the upper
left — the can body is light gray (#bdbdbd), handle darker (#9e9e9e). From the
round sprinkler rose at the spout end, 5-6 small blue droplets (#4fc3f7) arc
downward in a gentle curve toward Kami. Kami has eyes half-closed in serene
enjoyment, face tilted slightly upward.

Peaceful serene expression: leaves relaxed and gently spread outward, eyes
half-closed in a dreamy content manner, soft gentle smile. Arms relaxed at sides,
face tilted up toward the water.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Watering can: #bdbdbd body, #9e9e9e handle and rim, sprinkler rose #9e9e9e.
Water droplets: #4fc3f7 (5-6 simple round drops).
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 6 colors. Min 3px elements.

Avoid: text, water volume indicators, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 17 — Duengemittel (Fertilizers)

> **Pfad:** `/duengung/fertilizers` | **MUI-Icon:** OpacityIcon
> **Emotion:** ENERGISCH/KRAFTVOLL
> **Requisite:** Laborkittel-Kragen, Reagenzglas mit gruener Fluessigkeit, Duengerflasche

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered, wearing a tiny white lab coat suggested by a white
collar/lapel at the pot rim level (#ffffff collar, indigo inner #5c6bc0).
One arm holds a small test tube tilted at 45 degrees with bright green liquid
(#66bb6a fill, clear glass outline). A tiny fertilizer bottle (#9e9e9e body,
#5c6bc0 cap, small droplet symbol on label area — no text) stands on the ground
next to the pot. Kami has an energetic powerful pose.

Energetic powerful expression: leaves standing upright and taut, eyes wide open
and gleaming with energy, confident broad smile. One arm raised with test tube,
other arm flexed outward in a strongman pose.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Lab coat collar: #ffffff with #5c6bc0 inner accent.
Test tube: clear outline #1b5e20, liquid fill #66bb6a.
Bottle: #9e9e9e body, #5c6bc0 cap, droplet symbol #4fc3f7 on body.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 8 colors. Min 3px elements.

Avoid: text on bottle, ingredient labels, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 18 — Naehrstoffplaene (Nutrient Plans)

> **Pfad:** `/duengung/plans` | **MUI-Icon:** ListAltIcon
> **Emotion:** SKEPTISCH/NACHDENKLICH
> **Requisite:** Klemmbrett mit Phasen-Balken (Gantt-aehnliche Streifen)

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands to the left, studying a clipboard held at arm's length. The
clipboard has a brown clip (#795548) at the top and a white body (#ffffff). On
the body are 3 horizontal colored bars of different lengths, stacked vertically,
suggesting a Gantt chart or phase timeline:
- Bar 1 (top, short): #a5d6a7 green
- Bar 2 (medium): #5c6bc0 indigo
- Bar 3 (long): #66bb6a green
The bars are on a light gray background (#f5f5f5), separated by thin lines.

Skeptical thinking expression: leaves asymmetric (one perked up, one at neutral
angle), eyes with one slightly higher, mouth as a small diagonal line. One arm
holds clipboard, other arm raised with finger pointing at a bar.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Clipboard: white #ffffff, clip #795548, background #f5f5f5.
Bars: #a5d6a7, #5c6bc0, #66bb6a.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 8 colors. Min 3px elements.

Avoid: text, numbers, readable labels on bars, gradients, black outlines, drop
shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 19 — Duenge-Ereignisse (Feeding Events)

> **Pfad:** `/duengung/feeding-events` | **MUI-Icon:** EventNoteIcon
> **Emotion:** KONZENTRIERT/FOKUSSIERT
> **Requisite:** Notizbuch mit aufgeschlagener Seite, Stift in der Hand

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered, holding an open notebook in one arm (the notebook
hangs slightly open, spine to the left). The notebook has a dark green cover
(#2e7d32) with cream-white pages (#fafaf5). On the open right page: 4 short
horizontal lines (#e0e0e0) suggesting log entries, and a small green dot
(#66bb6a) at the start of the top line — like a new entry being recorded.
Kami's other arm holds a tiny pen/pencil pointing at the notebook page, as if
actively writing. Expression: concentrated, precise.

Focused determined expression: leaves upright and slightly tilted forward, eyes
narrowed with concentration, mouth as a tight determined line. One arm holds
notebook open, other arm presses pencil to page.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Notebook cover: #2e7d32. Pages: #fafaf5. Lines: #e0e0e0. Entry dot: #66bb6a.
Pencil: #ffa726 body, #1b5e20 tip.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 8 colors. Min 3px elements.

Avoid: text, readable log entries, dates, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 20 — Naehrstoff-Berechnungen (Nutrient Calculations)

> **Pfad:** `/duengung/calculations` | **MUI-Icon:** BiotechIcon
> **Emotion:** KONZENTRIERT/FOKUSSIERT
> **Requisite:** Lupe ueber Reagenzglas-Staender (Mikroskop-artig)

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands to the left, holding a large magnifying glass (handle #795548,
glass ring #9e9e9e, interior slightly lighter #bdbdbd) up toward a small test
tube rack. The rack is a simple rectangular stand (#9e9e9e) holding two small
test tubes: left tube with teal liquid (#4dd0e1), right tube with green liquid
(#66bb6a). The scene evokes scientific analysis and EC/pH measurement.

Focused determined expression: leaves upright and slightly tilted forward, eyes
narrowed with concentration, mouth as tight determined line with tiny tongue tip
visible. Both arms engaged: one holding the magnifying glass up to the test tubes.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Magnifying glass: handle #795548, ring #9e9e9e, lens interior #bdbdbd.
Test tube rack: #9e9e9e. Left tube liquid: #4dd0e1. Right tube liquid: #66bb6a.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 8 colors. Min 3px elements.

Avoid: text, EC/pH numbers, measurement labels, gradients, black outlines, drop
shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 21 — Schaedlinge (Pests)

> **Pfad:** `/pflanzenschutz/pests` | **MUI-Icon:** BugReportIcon
> **Emotion:** PANISCH/ERSCHROCKEN
> **Requisite:** Grosser stilisierter Kaefer (Comic-Bug), Kami haelt sich die Wangen

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: In the upper portion of the icon sits a simplified cartoon insect: a round
oval body (#d32f2f red), 6 thin stick legs, two antennae (thin dark lines),
and two tiny dot eyes (#000000). The bug is larger than Kami — about 50% of the
icon height. It faces downward toward Kami. Kami stands at the bottom, in a
panicked pose, looking up at the bug.

Panicked alarmed expression: leaves drooping downward limply, eyes wide and
large with shock, mouth as a small open circle. Both arms raised to cheeks in
classic oh-no gesture. 2-3 tiny blue sweat drops (#4fc3f7) floating near
Kami's head.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Bug body: #d32f2f, legs #1b5e20 thin lines, antennae #1b5e20, eyes #000000.
Sweat drops: #4fc3f7.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 7 colors. Min 3px elements.

Avoid: realistic insect anatomy, text, species names, gradients, black outlines
on Kami (dark green only), drop shadows, photorealism, 3D, complex backgrounds,
anti-aliasing artifacts, watermarks.
```

---

## Icon 22 — Krankheiten (Diseases)

> **Pfad:** `/pflanzenschutz/diseases` | **MUI-Icon:** CoronavirusIcon
> **Emotion:** BESORGT/UNSICHER
> **Requisite:** Vereinfachtes Virus-Symbol (runde Form mit Dornen), Warn-Dreieck

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: In the upper right of the icon floats a simplified cartoon pathogen symbol:
a small circle (#d32f2f) with 6-8 short spike protrusions around it, rendered
flat in red. Below and to the left of it hangs a small orange warning triangle
(#ed6c02 filled, white interior exclamation dot #ffffff). Kami stands in the
lower-left, looking at the symbols with a worried expression, one arm scratching
the back of the head nervously.

Worried uncertain expression: leaves angled slightly inward-downward, eyes
slightly squinted with concern, mouth as a small uncertain wavy line. One arm
scratches the back of the head nervously, other arm hangs at side.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Pathogen symbol: #d32f2f circle body, same color spikes.
Warning triangle: #ed6c02 fill, white exclamation dot #ffffff.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 7 colors. Min 3px elements.

Avoid: text, species names, realistic pathogen imagery, gradients, black outlines,
drop shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 23 — Behandlungen (Treatments)

> **Pfad:** `/pflanzenschutz/treatments` | **MUI-Icon:** MedicationIcon
> **Emotion:** ENERGISCH/KRAFTVOLL
> **Requisite:** Kleine Spruehflasche, Schutzschild-Symbol

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands in a powerful pose. In one arm Kami holds a small spray bottle
(#bdbdbd body, #9e9e9e nozzle, with 3 tiny mist dots #4fc3f7 spraying outward to
the right). With the other arm Kami holds up a small green shield (#2e7d32 fill,
#60ad5e emblem — a simple plus/cross symbol suggesting treatment/medicine).
The shield is slightly raised, protective stance.

Energetic powerful expression: leaves standing upright and taut, eyes wide open
and gleaming with energy, confident broad smile. One arm raised with shield,
other arm extended with spray bottle.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Spray bottle: #bdbdbd body, #9e9e9e nozzle. Mist dots: #4fc3f7.
Shield: #2e7d32 fill, plus emblem #60ad5e, outline #1b5e20.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 7 colors. Min 3px elements.

Avoid: text, product labels, brand names, gradients, black outlines, drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 24 — Ernte-Chargen (Harvest Batches)

> **Pfad:** `/ernte/batches` | **MUI-Icon:** AgricultureIcon
> **Emotion:** TRIUMPHIEREND/FEIERND
> **Requisite:** Kleiner Ernte-Korb voll goldener Fruechte, Funkelsterne

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered in a triumphant victory pose. In front of and slightly
below Kami sits a small woven harvest basket (#a1887f weave pattern suggestion,
#8d6e63 base). The basket is overflowing with 3 golden round fruits (#ffa726,
highlight #ffcc80) and 1 red tomato-like fruit (#d32f2f, highlight #ef5350). Above
and around Kami: 2-3 four-pointed sparkle stars (#fff9c4 with thin #ffa726 outline)
float in the air.

Triumphant celebrating expression: leaves standing straight and tall, eyes sparkling
with star-shaped white highlights, big confident victory grin. One arm raised in
fist pump victory pose, other arm on hip in power stance.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Basket: #a1887f, #8d6e63.
Golden fruits: #ffa726, highlight #ffcc80. Red fruit: #d32f2f.
Sparkle stars: #fff9c4 fill, #ffa726 thin outline.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 9 colors (exception for festive
scene). Min 3px elements.

Avoid: text, weight/yield numbers, gradients, black outlines, hard drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Icon 25 — Pflanzdurchlaeufe (Planting Runs)

> **Pfad:** `/durchlaeufe/planting-runs` | **MUI-Icon:** PlaylistAddCheckIcon
> **Emotion:** STOLZ/ZUFRIEDEN
> **Requisite:** Zwei kleinere faceless Keimlings-Toepfe hinter Kami in Reihe

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands in the foreground center-left, slightly larger than the others,
acting as group leader. Behind Kami, in a diagonal line going to the upper right,
are 2 smaller faceless seedling pots (no eyes or mouth, just a simple sprout form
with two small leaves #a5d6a7, pot #a1887f), each slightly smaller than the one
in front suggesting depth/recession. All three share a common baseline. Kami has
one arm raised as if signaling the group to proceed.

Proud content expression: leaves perked upward, eyes slightly narrowed with
confidence, broad satisfied smile. One arm raised in a forward "let's go" signal
gesture, other arm on hip.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Background seedlings: leaves #a5d6a7, pots #a1887f. No faces on them.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 6 colors. Min 3px elements.

Avoid: faces on background seedlings, text, batch numbers, gradients, black
outlines, drop shadows, photorealism, 3D, complex backgrounds, anti-aliasing
artifacts, watermarks.
```

---

## Icon 26 — Admin-Einstellungen

> **Pfad:** `/admin/settings` | **MUI-Icon:** AdminPanelSettingsIcon
> **Emotion:** SKEPTISCH/NACHDENKLICH
> **Requisite:** Kleines Zahnrad-Symbol, Admin-Schluessel-Abzeichen

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: Kami stands centered. In one arm Kami holds a small key (#ffa726 body,
rounded bow end, rectangular shaft, #f57c00 shadow side). Floating above the
other leaf is a small gear/cogwheel (#9e9e9e body with 6 teeth, #bdbdbd face,
#757575 center hole circle). The key and gear together suggest admin/system access.
Kami examines both items with a thoughtful planning expression.

Skeptical thinking expression: leaves asymmetric (one perked up, one at neutral
angle), eyes open and alert with one slightly higher than the other, mouth as a
small diagonal line. One arm holds key out, other arm raised with finger pointing
at gear.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Key: #ffa726 body, #f57c00 shadow.
Gear: #9e9e9e teeth/body, #bdbdbd face, #757575 center hole.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 12% padding. Max 8 colors. Min 3px elements.

Avoid: text, admin labels, version numbers, gradients, black outlines, drop
shadows, photorealism, 3D, complex backgrounds, anti-aliasing artifacts.
```

---

## Icon 27 — Einstellungen (Settings)

> **Pfad:** `/settings` | **MUI-Icon:** SettingsIcon
> **Emotion:** HAPPY
> **Requisite:** Grosses Zahnrad im Hintergrund, Kami dreht daran

```
A cute comic-style navigation icon for a plant management app, square 1:1 format,
128x128px. Fully transparent background, no background fill.

Scene: A large gear/cogwheel (#e0e0e0 body, #bdbdbd teeth, #9e9e9e center hole)
occupies most of the upper portion of the icon as a background element. It has
8 teeth and is clearly a settings symbol. Kami stands at the bottom center,
one arm reaching up and touching the gear, as if turning it. The scene is light
and casual — personal settings, not intimidating.

Happy expression: leaves pointing straight upward, large round dot eyes with
white highlight glints, small curved upward smile. Arms relaxed, one arm
reaching up to touch the gear cheerfully.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), pot #8d6e63
(stripe #a1887f, shadow #6d4c41), stem #43a047, soil #795548.
Large gear: #e0e0e0 body, #bdbdbd teeth outer, #9e9e9e center hole.
Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, round caps.

Style: flat vector illustration, cute comic character, professional. Solid colors
only, no gradients. Square 1:1, 10% padding. Max 6 colors. Min 3px elements.

Avoid: text, settings labels, gradients, black outlines, hard drop shadows,
photorealism, 3D, complex backgrounds, anti-aliasing artifacts, watermarks.
```

---

## Konsistenz-Grid-Prompt (Stil-Referenz)

Wenn Einzelgenerierung zu inkonsistenten Stilen fuehrt, diesen Grid-Prompt zuerst
generieren und als visuelle Stil-Referenz fuer alle Einzelprompts nutzen.

```
A grid of 27 small square navigation icons in identical cute comic style,
arranged in a 9x3 grid layout. All icons share the same mascot character —
a small anthropomorphic green seedling (leaves #66bb6a) growing from a terracotta
pot (#8d6e63), with a friendly face, thin stick arms. Flat vector illustration
style, dark green outlines (#1b5e20), transparent background per icon cell.

The 27 icons (left to right, top to bottom):
Row 1: Dashboard (clipboard with bar chart), Care Reminders (watering can + bell),
  Calendar (peek behind calendar grid), My Plants (three plants grouped),
  Calculations (holding calculator), Task Queue (checklist + hard hat),
  Workflows (flow diagram with 3 nodes), Botanical Families (tree silhouette),
  Species (open book with glasses)
Row 2: Companion Planting (two plants + floating heart), Crop Rotation (circular
  arrow), Import (document with upload arrow), Sites (greenhouse frame + sun),
  Substrates (3 stacked soil layers), Tanks (cylinder tank with water level),
  Watering Events (large can raining drops on Kami), Fertilizers (lab coat +
  test tube), Nutrient Plans (clipboard with gantt bars)
Row 3: Feeding Events (notebook + pencil), Nutrient Calculations (magnifying
  glass + test tubes), Pests (shocked Kami + red bug above), Diseases (virus
  + warning triangle), Treatments (spray bottle + shield), Harvest Batches
  (victory pose + fruit basket + sparkles), Planting Runs (Kami leading 2
  seedlings), Admin Settings (key + gear), Settings (Kami touching large gear)

All icons: square 1:1, identical Kami proportions, 2.5px dark green outlines
(#1b5e20), flat solid colors, max 8 colors each, no text anywhere. Kawaii-
influenced professional cartoon style. Solid transparent background per cell.
No gradients, no photorealism, no black outlines.
```

---

## Gesamtuebersicht — Alle 27 Icons

```
  Nr  Navigationspunkt           Emotion                  Requisite (Kern)          Farb-Akzent
  ──  ─────────────────────────  ───────────────────────  ────────────────────────  ────────────
   1  Dashboard                  STOLZ/ZUFRIEDEN          Klemmbrett + Balkenchart  #2e7d32
   2  Pflege & Erinnerungen      FRIEDLICH/GENIESSERISCH  Giesskanne + Glocke       #4fc3f7 + #ffa726
   3  Kalender                   NEUGIERIG/SUCHEND        Kalenderblatt + Punkte    #5c6bc0 + #ab47bc
   4  Meine Pflanzen             EINLADEND/WILLKOMMEN     2 Nachbar-Topfpflanzen    #a5d6a7
   5  Berechnungen               KONZENTRIERT/FOKUSSIERT  Taschenrechner            #9e9e9e
   6  Aufgaben-Warteschlange     KONZENTRIERT/FOKUSSIERT  Bauhelm + Checkliste      #ffa726
   7  Workflows                  SKEPTISCH/NACHDENKLICH   Flussdiagramm 3 Knoten    #5c6bc0 + #8e99f3
   8  Botanische Familien        HAPPY                    Laubbaum-Silhouette       #60ad5e
   9  Arten                      NEUGIERIG/SUCHEND        Buch + Brille             #5c6bc0
  10  Mischkultur                GLUECKLICH/BEGEISTERT    2 Nachbarpflanzen + Herz  #ab47bc
  11  Fruchtfolge                SKEPTISCH/NACHDENKLICH   Rotations-Kreis + Punkte  #ffa726 + #a1887f
  12  Import                     KONZENTRIERT/FOKUSSIERT  Dokument + Upload-Pfeil   #2e7d32
  13  Standorte                  STOLZ/ZUFRIEDEN          GWH-Dach + Sonne          #ffb74d
  14  Substrate                  NEUGIERIG/SUCHEND        3 uebereinander Schichten  #795548
  15  Tanks                      STOLZ/ZUFRIEDEN          Zylinder-Tank + Wasser    #4fc3f7
  16  Bewaesserungs-Ereignisse   FRIEDLICH/GENIESSERISCH  Grosse Giesskanne + Regen #4fc3f7
  17  Duengemittel               ENERGISCH/KRAFTVOLL      Laborkittel + Reagenzgl.  #5c6bc0 + #66bb6a
  18  Naehrstoffplaene           SKEPTISCH/NACHDENKLICH   Klemmbrett + Gantt-Balken #5c6bc0 + #a5d6a7
  19  Duenge-Ereignisse          KONZENTRIERT/FOKUSSIERT  Notizbuch + Stift         #2e7d32 + #ffa726
  20  Naehrstoff-Berechnungen    KONZENTRIERT/FOKUSSIERT  Lupe + Reagenzglas-Staend #4dd0e1
  21  Schaedlinge                PANISCH/ERSCHROCKEN      Roter Kaefer ueber Kami   #d32f2f + #4fc3f7
  22  Krankheiten                BESORGT/UNSICHER         Virus-Symbol + Warn-Dreieck #d32f2f + #ed6c02
  23  Behandlungen               ENERGISCH/KRAFTVOLL      Spruehflasche + Schild    #4fc3f7 + #2e7d32
  24  Ernte-Chargen              TRIUMPHIEREND/FEIERND    Erntekorb + Fruechte + Funken #ffa726 + #d32f2f
  25  Pflanzdurchlaeufe          STOLZ/ZUFRIEDEN          2 faceless Keimlinge      #a5d6a7
  26  Admin-Einstellungen        SKEPTISCH/NACHDENKLICH   Schluessel + Zahnrad      #ffa726 + #9e9e9e
  27  Einstellungen              HAPPY                    Grosses Zahnrad (BG)      #e0e0e0
```

---

## Differenzierungs-Analyse

Icons die sich thematisch aehneln und bewusst unterschiedlich gestaltet sind:

| Paar | Unterscheidungsmerkmal |
|------|----------------------|
| Icon 05 (Berechnungen) vs. Icon 20 (Naehrstoff-Berechnungen) | Taschenrechner vs. Lupe + Reagenzglas-Staender — abstrakt vs. biochemisch |
| Icon 06 (Aufgaben) vs. Icon 19 (Duenge-Ereignisse) | Bauhelm + Checkliste vs. Notizbuch + Stift — Planung vs. Protokoll |
| Icon 15 (Tanks) vs. Icon 16 (Bewaesserung) | Tank mit Fuellstand vs. Giesskanne regnet auf Kami — Vorrat vs. Akt |
| Icon 17 (Duengemittel) vs. Icon 20 (Naehrstoff-Ber.) | Laborkittel + Reagenzglas vs. Lupe + Staender — Produkt vs. Analyse |
| Icon 21 (Schaedlinge) vs. Icon 22 (Krankheiten) | Roter Kaefer vs. Virus-Symbol + Warn-Dreieck — Tier vs. Pathogen |
| Icon 26 (Admin) vs. Icon 27 (Settings) | Schluessel + kleines Zahnrad vs. grosses Zahnrad Hintergrund — Zugang vs. Konfiguration |
| Icon 04 (Meine Pflanzen) vs. Icon 10 (Mischkultur) vs. Icon 25 (Durchlaeufe) | Arme offen + 2 Pflanzen vs. enggedraengt + Herz vs. Reihe + Anführer-Geste |

---

## Technische Hinweise

1. **Primaere Generierungsgroesse:** 512×512px oder 1024×1024px generieren, dann auf 128×128px downsamplen — schärfere Kanten als direkt in 128px.
2. **32×32px Test:** Nach Generierung und SVG-Konvertierung auf 32×32px skalieren und pruefen ob Kami-Silhouette + Requisit-Silhouette noch erkennbar.
3. **Farb-Budget:** Jedes Icon hat maximal 8 Farben (Ausnahme: Icon 24 Ernte mit 9). Kami selbst verbraucht bereits 6-7 Farben — die Requisite darf hoechstens 1-2 neue Farben hinzufuegen.
4. **Grid-Zuerst-Strategie:** Falls Einzelgenerierungen visuell inkonsistent sind, zuerst den Grid-Prompt generieren, dann Einzelprompts mit dem Hinweis "in the exact same style as the reference grid" nachgenerieren.
5. **Einheitliche Kami-Groesse:** Kami muss in allen 27 Icons die gleiche Hoehe relativ zum Icon einnehmen (50-60%). Die Requisite wird entsprechend skaliert.
6. **Keine Arme bei 32px:** Bei sehr kleiner Darstellung (32×32px im SVG) sollten Kami-Arme via SVG-Editor entfernt werden — sie werden zu duennen Artefakten.
7. **Differenzierungs-Test:** Alle 27 Icons in einer Reihe bei 32×32px anzeigen und pruefen ob jedes auf den ersten Blick eindeutig erkennbar ist. Bei Verwechslungsgefahr Requisite vereinfachen und dominanter machen.
8. **Naming-Konvention:** `nav-kami-{slug}.{format}` — z.B. `nav-kami-dashboard.png`, `nav-kami-pflege.png`

## Nachbearbeitung Checkliste

- [ ] Alle 27 Icons auf 128×128px zuschneiden (quadratisch, kein Weissraum)
- [ ] Hintergrund sauber transparent (PNG alpha channel)
- [ ] Auf 64×64px skalieren und Erkennbarkeit pruefen
- [ ] Auf 32×32px skalieren — Kami-Silhouette + Requisit-Silhouette lesbar?
- [ ] Farbwerte gegen Kamerplanter-Palette validieren (#66bb6a, #8d6e63, etc.)
- [ ] Alle 27 Icons nebeneinander in einem Dokument: visuelle Konsistenz pruefen
- [ ] Kami-Proportionen zwischen Icons angleichen falls notig
- [ ] SVG-Konvertierung via vtracer: Pfadanzahl pro Icon unter 40 halten
- [ ] Sidebar.tsx Icons ersetzen: `<img>` oder MUI `<SvgIcon>` statt Material Icons
- [ ] Dateien ablegen unter: `src/frontend/src/assets/icons/nav/`
- [ ] Namenskonvention: `nav-kami-{slug}.svg` und `.png`
