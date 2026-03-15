# Grafik-Prompt: Kami HTTP-Fehlerseiten-Serie

> **Typ:** illustration
> **Erstellt:** 2026-03-09
> **Varianten:** Light (alle Bilder)
> **Zielgröße:** 800×600px (4:3)
> **Format:** PNG (transparent)
> **Einsatzort:** HTTP-Fehlerseiten in der Kamerplanter-Webanwendung (400, 401, 403, 404, 408, 429, 500, 502, 503)

---

## Kontext

Kami tritt als sympathische Fehler-Begleitung auf Fehlerseiten der Kamerplanter-App auf. Jede Illustration kommuniziert ohne Text den jeweiligen HTTP-Fehler visuell — der HTTP-Code und die Fehlermeldung werden nachträglich als Typografie-Overlay ergänzt. Die neun Bilder bilden eine kohärente Serie: gleicher Illustrationsstil, gleiche Proportionen, gleiche Strichstärken, gleiche Farbpalette, Kami immer links oder mittig-links, Requisit rechts oder mittig-rechts auf gemeinsamer Grundlinie.

**Konsistenzregeln für die gesamte Serie:**
- Kami-Höhe immer ca. 50–60% der Bildhöhe, vertikal im unteren Bilddrittel geerdet
- Alle Requisiten im gleichen flat-vector Stil wie Kami
- Requisiten-Outlines: identische Strichstärke wie Kami (2.5px außen, 1.5px innen, dark green `#1b5e20`)
- Hintergrund immer transparent
- Maximal 9 distinkte Farben pro Bild (Kami-Palette zählt als Grundlage)
- Keine Texte, Zahlen oder Buchstaben im Bild

---

## Serienstil-Baustein (in alle Prompts einbetten)

```
Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion with vtracer. No element
smaller than 3px at 800px width. Maximum 9 distinct colors total per image.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks, clip-art style.
```

---

## Fehler 400 — Bad Request

> **Emotion:** SKEPTISCH / NACHDENKLICH
> **Szene:** Kami hält ein zerknittertes, unlesbares Dokument (leere Seite mit Fragezeichen-Symbol) und betrachtet es ratlos. Das Dokument ist wirr zusammengeknüllt, Kami neigt den Kopf skeptisch zur Seite.

### Gemini Prompt — 400 Bad Request

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands on the left, holding a crumpled paper document
in one arm. The crumpled paper has a single large bold question mark symbol drawn on
it (flat icon, not text). Kami tilts toward the document with a confused, skeptical
expression, head cocked to one side. The document floats slightly to Kami's right,
both resting on a shared invisible baseline.

Kami has a SKEPTICAL THINKING expression: leaves asymmetric — one leaf perked up,
one at a lower neutral angle. Eyes open and alert with one slightly higher than the
other. Mouth as a small diagonal line. One arm holds the crumpled paper up, other
arm raised with index finger near chin in a puzzled "hmm, what is this?" gesture.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Mouth outline #1b5e20.

Crumpled paper document: flat white #f5f5f5 fill, folded crease lines in light gray
#bdbdbd, large question mark icon in dark gray #616161, outline #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami positioned left-center, document right-center, both on shared ground baseline.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 401 — Unauthorized

> **Emotion:** BESORGT / UNSICHER
> **Szene:** Kami steht vor einer geschlossenen Holztür mit einem großen Vorhängeschloss. Kami hält keinen Schlüssel — die Hände leer, nervöser Blick auf das Schloss. Die Tür ist deutlich größer als Kami.

### Gemini Prompt — 401 Unauthorized

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands on the left, facing a large closed wooden door
on the right. The door has a prominent padlock symbol on it — a simple flat padlock
icon in dark metallic gray. Kami looks at the padlock with a worried expression,
hands empty, clearly unable to enter. The door is approximately 200% of Kami's height.
Both Kami and the door base rest on a shared ground baseline.

Kami has a WORRIED UNCERTAIN expression: leaves angled slightly inward-downward,
eyes slightly squinted with concern, mouth as a small uncertain wavy line. One arm
scratches the back of the head nervously, other arm hangs at the side.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Mouth outline #1b5e20.

Door: warm brown flat fill #795548, door frame slightly darker #6d4c41, simple
rectangular wooden plank lines in #5d4037. Large padlock icon centered on door:
body #9e9e9e, shackle (arc) #757575, keyhole opening #424242. Padlock outline
#1b5e20.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami positioned left, door right-center, both on shared ground baseline.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 403 — Forbidden

> **Emotion:** TRAURIG / ENTTÄUSCHT
> **Szene:** Kami steht vor einem deutlichen Stopp-Schild (Achteck, Rotkreis mit Querstrich). Ein Arm ist ausgestreckt in Richtung des Schilds, wird aber durch das Schild symbolisch abgewiesen. Kami wirkt enttäuscht — nicht aggressiv, sondern traurig-resigniert.

### Gemini Prompt — 403 Forbidden

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands slightly left of center, one arm extended forward
reaching toward a large round prohibition sign on the right — a flat circle with a
diagonal bar through it (universal "no entry" / forbidden symbol), in bold red.
The sign appears to push Kami back. Kami looks at the sign with a sad, resigned
expression. The sign is approximately 100% of Kami's height and mounted on a short
flat post. Both Kami and the sign base rest on a shared ground baseline.

Kami has a SAD DISAPPOINTED expression: leaves drooping clearly downward, eyes
looking down with a small teardrop on one eye, mouth as a downward curved arc. The
reaching arm is extended toward the sign, other arm hanging limply. Overall posture
slightly slumped. Sympathetically sad — an "I'm sorry" expression, not aggressive.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Small teardrop on one eye in light blue #4fc3f7. Mouth outline #1b5e20.

Prohibition sign: circle fill #d32f2f, diagonal bar fill #d32f2f, white circle
interior #ffffff, sign post short rectangle #9e9e9e. Sign outline #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami center-left, sign right-center, both on shared ground baseline.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 404 — Not Found

> **Emotion:** NEUGIERIG / SUCHEND
> **Szene:** Kami hält eine große Lupe und schaut hindurch — die Lupe zeigt einen leeren Kreis (nichts dahinter). Am Boden liegen vereinzelt kleine Fragezeichen-Symbole verstreut. Kami lehnt sich leicht vor in Suchpose.

### Gemini Prompt — 404 Not Found

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands slightly left of center, holding a large
magnifying glass in one arm, leaning forward to peer through it. The magnifying
glass lens area is completely empty — showing only a slightly lighter circle,
symbolizing nothing was found. Two or three small flat question mark icons
(simple bold geometric shapes) are scattered on the ground near Kami's pot base.
The magnifying glass handle is held by one arm, the glass itself is to Kami's right,
approximately 60% of Kami's height.

Kami has a CURIOUS SEARCHING expression: leaves tilted slightly forward and sideways,
one eye slightly larger than the other with curiosity, small "oh" circular open mouth.
One arm holds the magnifying glass up toward the right, other arm slightly raised
near chin. Leaning forward in searching posture.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Mouth outline #1b5e20.

Magnifying glass: circular lens ring in neutral gray #9e9e9e (thick flat ring, 2.5px
outline), lens interior empty circle fill #f5f5f5 (slightly lighter than background),
handle in warm brown #795548. Question mark icons on ground: flat bold shapes in
light gray #bdbdbd, outline #9e9e9e.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami left-center leaning forward, magnifying glass held to the right, question
marks scattered at ground level.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 408 — Request Timeout

> **Emotion:** FRIEDLICH / GENIESSERISCH (schlafend, Wartepose)
> **Szene:** Kami ist beim Warten eingeschlafen — Kopf ist leicht zur Seite gesunken, Augen geschlossen in schläfriger Pose. Neben Kami steht ein großer flacher Wecker oder eine Sanduhr, die fast leer ist. Drei kleine "Z Z Z"-Symbole (als einfache geometrische Zickzack-Formen, keine Buchstaben) steigen über Kamis Kopf auf.

### Gemini Prompt — 408 Request Timeout

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands left-center with head drooping sideways in a
drowsy sleeping pose — clearly fallen asleep while waiting. To Kami's right stands a
large hourglass (sanduhr) with almost all sand in the bottom chamber, nearly empty
on top. Three small "Z" shapes (flat angular zigzag bolt shapes, NOT letters — purely
abstract geometric sleep symbols: three identical small angular bolt icons in
diminishing sizes) float rising above Kami's drooping head. The hourglass is
approximately 120% of Kami's height.

Kami has a PEACEFUL SERENE (sleeping) expression: leaves relaxed and drooping softly
to one side (asymmetric droop), eyes fully closed as horizontal flat lines or very
thin closed crescents, a soft small smile. Both arms hanging loosely at sides, body
slightly tilted to one side as if dozing while standing.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes closed as dark green lines #1b5e20. Mouth
outline #1b5e20.

Hourglass: frame top and bottom caps in warm brown #795548, glass body outline
#1b5e20, sand in bottom chamber #ffa726 (harvest gold), nearly empty top chamber
shows only a tiny triangle of sand remaining, center neck narrow. Sleep-Z shapes:
three flat angular bold bolt icons in light indigo #8e99f3 with outline #5c6bc0,
floating upward to the upper right above Kami's head, each slightly smaller than
the previous.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami left-center in sleeping tilt, hourglass right-center, Z-shapes drifting upper
area, all on shared ground baseline.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 429 — Too Many Requests

> **Emotion:** PANISCH / ERSCHROCKEN
> **Szene:** Kami ist von einer Flut kleiner identischer Umschlag-Icons (symbolisieren Anfragen) überwältigt, die von rechts einfliegen. Kami ist von mehreren solcher Umschläge umgeben, ein oder zwei haben Kami bereits getroffen. Beide Arme an den Wangen, Schweißtropfen, typische Überwältigungs-Pose.

### Gemini Prompt — 429 Too Many Requests

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands center-left, overwhelmed and panicking. From the
right side, a swarm of identical small flat envelope icons (simple geometric envelope
shapes — representing incoming requests) fly in from the right in a loose cluster
formation. Five to seven envelopes at various angles surround Kami — some mid-flight,
one or two touching Kami's leaves. The envelopes fly inward toward Kami from the
right. Kami is clearly overwhelmed by too many incoming requests at once.

Kami has a PANICKED ALARMED expression: leaves drooping downward limply, eyes wide
and large with shock, mouth as a small open circle. Both arms raised to cheeks in
classic "oh-no" gesture with hands framing the face. Two to three tiny blue sweat
drops (#4fc3f7) floating near Kami's head.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Mouth outline #1b5e20. Sweat drops #4fc3f7 outlined #1b5e20.

Envelope icons: flat geometric simple envelope shape (trapezoid flap top, rectangle
body), fill light indigo #8e99f3, envelope flap triangle fill slightly darker #5c6bc0,
outline #1b5e20. All envelopes identical in design, varied in angle and position.
Each envelope approximately 20–25% of Kami's height.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami center-left in panicked pose, envelopes flying in from the right across the
scene, all at roughly mid-height in the composition.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 500 — Internal Server Error

> **Emotion:** TRAURIG / ENTTÄUSCHT (mit Schreckelement)
> **Szene:** Kami steht neben einem kleinen Server-/Computergehäuse, aus dem Rauch aufsteigt und das erkennbar kaputt ist (eine seitliche Delle, ein Blitz-Symbol auf der Front). Kami schaut auf das kaputte Gerät herab mit einem echten "Es tut mir leid"-Ausdruck. Kleine rote Warndreiecke schweben um das Gerät.

### Gemini Prompt — 500 Internal Server Error

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands slightly left of center, looking down with a
sad apologetic expression at a small broken server box to Kami's right. The server
box (a simple flat rectangular box representing a computer/server) has a visible dent
on its side, a lightning bolt icon on its front face, and two small wispy smoke
puffs rising from the top. Two small flat red warning triangle icons (caution triangles
with exclamation mark shape, NOT text) float near the server. The server box is
approximately 80% of Kami's height.

Kami has a SAD DISAPPOINTED expression: leaves drooping clearly downward, eyes
looking down with a small teardrop on one eye, mouth as a downward curved arc. Arms
hanging limply at sides. Overall posture slightly slumped. Sympathetically sad —
an "I'm sorry, something broke" expression.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Small teardrop in light blue #4fc3f7. Mouth outline #1b5e20.

Server box: main body flat neutral gray #bdbdbd, dent shown as a darker depressed
area #9e9e9e with a sharp angular edge, front face slightly lighter #e0e0e0, lightning
bolt icon on front in warning orange #ed6c02 outlined #1b5e20, server box outline
#1b5e20. Smoke puffs: two small wispy cloud shapes in light gray #e0e0e0 rising from
top, outline #bdbdbd. Warning triangles: equilateral triangle fill #d32f2f, inner
exclamation mark shape in white #ffffff, outline #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami center-left looking down sadly, broken server right-center, warning triangles
floating near server, smoke rising above server.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 502 — Bad Gateway

> **Emotion:** BESORGT / UNSICHER
> **Szene:** Kami hält in beiden Händen je einen Steckverbinder (einfache Stecker-Symbole), die zwei komplett unterschiedliche Formen haben und offensichtlich nicht zusammenpassen. Kami schaut von einem zum anderen mit verwirrt-besorgtem Blick. Zwischen den Steckern ein kleines Blitz-Symbol das die fehlende Verbindung symbolisiert.

### Gemini Prompt — 502 Bad Gateway

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands center, holding two mismatched connector plugs —
one in each arm outstretched to the sides. The left plug is a flat rounded rectangular
connector shape. The right plug is a flat round circular connector shape. They clearly
do not match each other. A small flat lightning bolt icon floats in the gap between
the two connectors at chest height, symbolizing the broken connection. Kami looks
from one plug to the other with a worried, confused expression.

Kami has a WORRIED UNCERTAIN expression: leaves angled slightly inward-downward,
eyes slightly squinted with concern, mouth as a small uncertain wavy line. One arm
extends left holding the rectangular plug, other arm extends right holding the round
plug — both arms pointing outward displaying the incompatible connectors.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Mouth outline #1b5e20.

Left connector plug: flat rounded rectangle shape, body neutral gray #9e9e9e,
connector pins as simple short rectangles #616161, cable stub #757575, outline
#1b5e20. Right connector plug: flat circle shape, body neutral gray #9e9e9e,
connector holes as small dark circles #424242, cable stub #757575, outline #1b5e20.
Gap lightning bolt: bold flat zigzag bolt shape in warning orange #ed6c02, outline
#1b5e20. Each plug approximately 30% of Kami's height.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami centered, left plug extending left, right plug extending right, lightning bolt
centered between them.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Fehler 503 — Service Unavailable

> **Emotion:** KONZENTRIERT / FOKUSSIERT
> **Szene:** Kami trägt einen kleinen flachen Schutzhelm (Bauhelm-Silhouette) auf den Blättern und hält einen Schraubenschlüssel. Neben Kami steht ein Schild/Aufsteller mit einem einfachen Werkzeug-Icon (Schraubenschlüssel-Kreuz), das Wartungsarbeiten symbolisiert. Kami schaut konzentriert auf die Arbeit — Stimmung ist "Ich bin gerade dabei, das zu reparieren", positiv-konstruktiv.

### Gemini Prompt — 503 Service Unavailable

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands left-center wearing a small flat construction
helmet (hard hat silhouette) balanced between the two leaves on top. Kami holds a
large flat wrench tool in one arm. To Kami's right stands a simple flat diamond-shaped
road warning sign on a short post, with a wrench-and-screwdriver crossed-tools icon
on it (simple flat geometric tool cross symbol, NOT text). The sign indicates
maintenance in progress. The sign is approximately 110% of Kami's height.
Both Kami and sign rest on shared ground baseline.

Kami has a FOCUSED DETERMINED expression: leaves upright and slightly tilted forward,
eyes narrowed with concentration, mouth as a tight determined line. One arm holds
the wrench upward in a working pose, other arm on hip or steadying the body.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Mouth outline #1b5e20.

Construction helmet: flat rounded hard hat shape sitting above Kami's leaves,
fill warning orange #ed6c02, brim slightly darker #e65100, outline #1b5e20.
Wrench tool: flat geometric wrench silhouette, body neutral gray #9e9e9e, head
opening #757575, outline #1b5e20.
Warning sign: diamond shape (square rotated 45°) fill warning orange #ed6c02,
thin border stripe white #ffffff, sign post short rectangle #9e9e9e, crossed
wrench-and-screwdriver icon on sign face in white #ffffff as flat bold geometric
shapes, sign outline #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.
Kami left-center with helmet and wrench, maintenance sign right-center, shared
ground baseline.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px
at 800px width. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Technische Hinweise

- **SVG-Konvertierung:** Alle Prompts sind auf vtracer-Konvertierung ausgelegt. Die maximale Farbanzahl von 9 pro Bild stellt sicher, dass vtracer mit `--color-precision 6` saubere Pfade erzeugt.
- **Transparenz:** Alle Prompts fordern transparent PNG. Falls Gemini einen weißen Hintergrund generiert, muss dieser in GIMP (Farbe-nach-Alpha mit #ffffff) oder Inkscape entfernt werden, bevor die vtracer-Konvertierung startet.
- **Serienkonsistenz:** Vor der Verwendung alle 9 Bilder nebeneinander vergleichen — Kami-Größe, Strichstärke und Farbpalette müssen erkennbar zusammengehören. Bei Abweichungen den betroffenen Prompt mit dem Zusatz "Kami must be exactly the same character model as in the reference: terracotta pot mascot with two leaf sprouts, flat vector style" nachgenerieren.
- **Keine Z-Buchstaben beim 408-Bild:** Der Prompt beschreibt die Z-Symbole als "angular bolt shapes" und "abstract geometric sleep symbols" — nicht als Buchstaben. Trotzdem prüfen: Gemini könnte echte Z-Buchstaben generieren. Falls das passiert, Prompt-Variante A für 408 verwenden (siehe unten).
- **Schrift auf dem 503-Schild:** Das Kreuz-Werkzeug-Icon auf dem Wartungsschild darf keine Buchstaben enthalten. Gemini neigt dazu, hier Text zu setzen. Prüfen und bei Bedarf nachbearbeiten (Icon in Inkscape manuell ersetzen).
- **Strichstärken-Prüfung:** Bei 800px Ausgabe müssen alle Outlines mindestens 2px breit sein. Bei Unterschreitung: Bild in Inkscape nachbearbeiten oder Prompt mit "extra thick outlines, minimum 3px stroke weight" ergänzen.
- **Farbvalidierung:** Nach Generierung die Grüntöne der Blätter gegen `#66bb6a` und `#2e7d32` prüfen. Gemini weicht gelegentlich zu gelblichem oder blaulichem Grün ab.

---

## Varianten

### Variante A: 408 — Ohne Z-Symbole (falls Gemini Buchstaben generiert)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands left-center with head drooping sideways in a
drowsy sleeping pose — clearly fallen asleep while waiting. To Kami's right stands a
large hourglass with almost all sand in the bottom chamber. Three small identical
crescent moon shapes (simple flat half-moon icons, NOT letters or symbols) float
rising above Kami's drooping head in diminishing sizes, indicating deep sleep.

Kami has a PEACEFUL SERENE sleeping expression: leaves relaxed drooping softly to
one side, eyes fully closed as thin flat horizontal lines, soft small smile. Both
arms hanging loosely at sides, body slightly tilted sideways in a dozing standing
pose.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes closed as dark green lines #1b5e20. Mouth
outline #1b5e20.

Hourglass: frame caps warm brown #795548, glass body clear with outline #1b5e20,
bottom sand fill #ffa726, top nearly empty (tiny sand triangle only). Crescent moon
shapes: three identical simple crescent icons in light indigo #8e99f3 outline
#5c6bc0, floating in diminishing sizes above Kami's head toward upper right.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
Minimal detail, all shapes suitable for SVG conversion. No element smaller than 3px.
Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

### Variante B: 500 — Mit stärkerem Schreck-Element (für dramatischere Darstellung)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami the plant mascot stands slightly left, recoiling backward in shock from
a small broken server box to the right. The server box has a crack across its face,
a broken hinge, and three small spark shapes (flat star-burst shapes, NOT letters)
burst outward from the crack. Kami leans back with both hands raised to cheeks,
clearly shocked by the sudden breakdown.

Kami has a PANICKED ALARMED expression: leaves standing stiffly straight up in shock,
eyes wide and large, mouth as a small open circle. Both arms raised to cheeks in
classic "oh-no" gesture. Two small blue sweat drops (#4fc3f7) near head.

Kami body colors: leaves #66bb6a (highlight area #98ee99, shadow near stem #2e7d32),
stem #43a047, pot #8d6e63 (decorative stripe #a1887f, shadow underside #6d4c41),
visible soil at pot rim #795548. Eyes black #000000 with white highlight glint
#ffffff. Sweat drops #4fc3f7 outlined #1b5e20.

Server box: flat gray #bdbdbd body, crack as dark jagged line #616161, broken edge
#9e9e9e, spark shapes (four-pointed flat stars) in warning orange #ed6c02 and error
red #d32f2f, outline #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer strokes, 1.5px inner detail lines,
round line caps and joins throughout.

Background: fully transparent PNG. 4:3 landscape format, 8% padding all sides.

Style: flat vector illustration, cute cartoon mascot style, professional and friendly.
Flat solid colors only — no gradients, no textures. Subtle soft inner shading
(10–15% darker fill near form edges) for depth. Clean crisp outlines throughout.
No element smaller than 3px. Maximum 9 distinct colors total.
Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, fine textures, elements smaller than 3px,
anti-aliasing artifacts, watermarks.
```

---

## Nachbearbeitung

- [ ] Alle 9 Bilder nach Generierung nebeneinander legen und auf Stil-Konsistenz prüfen (Kami-Größe, Strichstärken, Grüntöne)
- [ ] Transparenz-Check: Weißen Hintergrund entfernen falls nicht korrekt transparent generiert
- [ ] Farbvalidierung: Kami-Blätter gegen `#66bb6a` prüfen, Terracotta-Topf gegen `#8d6e63`
- [ ] Auf echte Buchstaben/Zahlen im Bild prüfen — insbesondere 408 (Z-Symbole), 503 (Schild-Icon), 500 (Blitz auf Server)
- [ ] SVG-Konvertierung mit vtracer testen, Pfadanzahl pro Bild prüfen (Ziel: < 100 Pfade gesamt)
- [ ] Skalierungstest auf 400×300px: Kami und Requisit müssen auf halber Größe noch lesbar sein
- [ ] Bei zu ähnlichen Emotionen zwischen 400 und 503 (beide nachdenklich): 400-Prompt mit stärkerem Kopfneigen nachgenerieren um visuelle Unterscheidbarkeit zu gewährleisten
