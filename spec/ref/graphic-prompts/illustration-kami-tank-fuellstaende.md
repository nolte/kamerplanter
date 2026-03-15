# Grafik-Prompt: Kami — Tank-Fuellstand-Serie (6 Stufen)

> **Typ:** illustration-serie
> **Erstellt:** 2026-03-09
> **Varianten:** 6 Fuellstaende (0%, 20%, 40%, 60%, 80%, 100%), nur Light Mode
> **Zielgroesse:** 320x240px (primaer), spaeter SVG-Konvertierung via vtracer
> **Format:** PNG (transparent) → SVG
> **Einsatzort:** TankDetailPage Fuellstand-Anzeige, TankListPage Statusicon, TankStateCreateDialog Illustration
> **Referenz:** Design Guide Abschnitt 5 (Kami-Anatomie), illustration-kami-tankmanagement.md, REQ-014

---

## Kontext

Serie von 6 Illustrationen die denselben Tank mit unterschiedlichem Fuellstand zeigen.
Kami reagiert emotional passend zum Fuellstand — von panisch (leer) bis stolz-zufrieden (voll).
Alle Bilder haben identische Komposition und Proportionen, nur Fluessigkeitshoehe und
Kamis Ausdruck/Pose aendern sich. Die Konsistenz ist entscheidend, da die Bilder als
zusammengehoerende Serie in der UI erscheinen.

Da die PNGs spaeter mit vtracer zu SVGs vektorisiert werden, muessen die Formen
besonders sauber sein: klare Kanten, keine feinen Details unter 3px, kein Anti-Aliasing-Rauschen.

---

## Gemeinsame Stilregeln (fuer alle 6 Bilder identisch)

```
KAMI-GRUNDFORM:
- Anthropomorpher Keimling in Terracotta-Topf
- Topf: trapezfoermig (oben breiter), konisch, dekorativer Mittelstreifen
  Topf-Farben: Basis #8d6e63, Streifen #a1887f, Schatten #6d4c41
- Gesicht: Grosse runde Punkt-Augen (schwarz mit weissem Glanzpunkt),
  Mund variiert je Fuellstand (siehe Prompts)
- Zwei gruene Blaetter oben (#66bb6a, Highlight #98ee99, Schatten #2e7d32)
- Duenne Stiel-Arme seitlich am Topf

TANK-GRUNDFORM:
- Einfacher Zylinder, ca. 2x Kamis Hoehe
- Tank-Wand: helles Grau #bdbdbd, Deckelrand #9e9e9e, Bodenring #757575
- Fuellstand-Fenster: vertikaler transparenter Streifen auf der Vorderseite
- Naehrloesung: Teal #4dd0e1, Oberflaeche heller #b2ebf2
- Kleines Ventil unten: braun #795548

KOMPOSITION (Querformat 4:3):
- Kami links (ca. 30% der Breite), Tank rechts (ca. 50% der Breite)
- Beide auf gleicher Grundlinie stehend
- Kein Schlauch, keine Messgeraete, keine Zusatzelemente — nur Kami + Tank
- Transparenter Hintergrund (PNG alpha)
- Padding 8-10% an allen Seiten
- WICHTIG: Identische Proportionen und Positionen in allen 6 Bildern

STIL:
- Flat-Vector Comic-Illustration
- Klare, gleichmaessige Outlines: 2.5px Aussenkontur, 1.5px innere Details
- Outline-Farbe: dunkles Gruen #1b5e20 (NICHT schwarz)
- Flaechige Farbfuellung, KEINE Gradienten
- Weiche Schatten: 10-15% dunkler als Basisfarbe innerhalb der Form
- Minimale Details — SVG-tauglich: keine Strukturen unter 3px
- Kawaii-inspiriert aber professionell

FARBEN (alle 6 identisch ausser Fluessigkeitshoehe und Gesicht):
- Kami Blaetter: #66bb6a, Highlight #98ee99, Schatten #2e7d32
- Kami Topf: #8d6e63, Streifen #a1887f, Schatten #6d4c41
- Tank: #bdbdbd Wand, #9e9e9e Deckel, #757575 Boden
- Fluessigkeit: #4dd0e1, Oberflaeche #b2ebf2
- Ventil: #795548
- Outlines: #1b5e20
```

---

## Prompt 1 — Fuellstand 0% (Leer)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left, looking at a large cylindrical tank on the right. The tank is completely
empty — the fill level window shows no liquid at all, just empty gray interior. Kami has a
panicked, distressed expression: eyes are wide with tiny sweat drops floating near the head,
mouth is a small open circle of shock, both arms raised to the cheeks in a classic
oh-no gesture. Both leaves droop downward limply, suggesting alarm.

A small simple warning triangle (outline only, orange #ed6c02) with an exclamation dot
floats above the tank.

Tank: large cylinder, about 2x Kami height. Light gray walls #bdbdbd, darker rim #9e9e9e
at top and base ring #757575. Fill level window on front side is completely empty — no teal
liquid visible. Small valve nozzle at bottom in brown #795548.

Kami: leaves #66bb6a drooping downward, pot #8d6e63 with stripe #a1887f. Eyes wide open
(black with white highlight dots), tiny blue sweat drops #4fc3f7 near head (2-3 small
droplet shapes). Mouth: small round open circle.

Warning triangle: simple outline in #ed6c02, small filled dot inside. Floats above tank lid.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner. Rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 8%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, gradients, photorealism, black outlines, complex backgrounds.
```

---

## Prompt 2 — Fuellstand 20% (Kritisch niedrig)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left, looking at a large cylindrical tank on the right. The tank is nearly
empty — the fill level window shows teal nutrient liquid at only 20% height, a thin layer
at the bottom. Kami has a worried, concerned expression: eyebrows furrowed (leaves angled
slightly inward-downward), mouth is a small uncertain wavy line, one arm scratches the back
of the head nervously, the other arm hangs at the side.

Tank: large cylinder, about 2x Kami height. Light gray walls #bdbdbd, darker rim #9e9e9e
at top and base ring #757575. Fill level window shows teal liquid #4dd0e1 filling only the
bottom 20%. Liquid surface highlighted with lighter teal #b2ebf2. Small valve at bottom
in brown #795548.

Kami: leaves #66bb6a angled slightly inward (worried), pot #8d6e63 with stripe #a1887f.
Eyes slightly squinted with concern (black with white highlights). Mouth: small wavy
uncertain line.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner. Rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 8%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, gradients, photorealism, black outlines, complex backgrounds.
```

---

## Prompt 3 — Fuellstand 40% (Niedrig)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left, looking at a large cylindrical tank on the right. The tank shows teal
nutrient liquid at 40% fill level — below half. Kami has a slightly skeptical, thinking
expression: one eyebrow raised (one leaf up, one slightly down), mouth is a small diagonal
line suggesting "hmm", one arm on hip, the other arm raised with index finger pointing
upward in a "we should refill soon" gesture.

Tank: large cylinder, about 2x Kami height. Light gray walls #bdbdbd, darker rim #9e9e9e
at top and base ring #757575. Fill level window shows teal liquid #4dd0e1 at 40% height.
Liquid surface highlighted with lighter teal #b2ebf2. Small valve at bottom in brown #795548.

Kami: leaves #66bb6a (one perked up, one at neutral angle), pot #8d6e63 with stripe #a1887f.
Eyes open and alert (black with white highlights), one slightly higher than the other
(skeptical asymmetry). Mouth: small diagonal line.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner. Rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 8%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, gradients, photorealism, black outlines, complex backgrounds.
```

---

## Prompt 4 — Fuellstand 60% (Mittel/OK)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left, looking at a large cylindrical tank on the right. The tank shows teal
nutrient liquid at 60% fill level — comfortably above half. Kami has a calm, content
expression: gentle smile, relaxed posture. One arm gives a casual thumbs-up toward the tank,
the other arm relaxed at the side. Leaves in a natural upward position, relaxed.

Tank: large cylinder, about 2x Kami height. Light gray walls #bdbdbd, darker rim #9e9e9e
at top and base ring #757575. Fill level window shows teal liquid #4dd0e1 at 60% height.
Liquid surface highlighted with lighter teal #b2ebf2. Small valve at bottom in brown #795548.

Kami: leaves #66bb6a in natural relaxed upward position, pot #8d6e63 with stripe #a1887f.
Eyes normal size, relaxed (black with white highlights). Mouth: gentle content smile.
One hand forming thumbs-up shape.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner. Rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 8%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, gradients, photorealism, black outlines, complex backgrounds.
```

---

## Prompt 5 — Fuellstand 80% (Gut)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left, looking happily at a large cylindrical tank on the right. The tank shows
teal nutrient liquid at 80% fill level — nearly full. Kami has a happy, satisfied expression:
bright wide smile, eyes curved upward in joy (happy anime-style closed crescents). Both arms
spread outward in a presenting gesture, as if proudly showing off the well-filled tank.
Leaves perked upward and slightly outward, energetic.

Tank: large cylinder, about 2x Kami height. Light gray walls #bdbdbd, darker rim #9e9e9e
at top and base ring #757575. Fill level window shows teal liquid #4dd0e1 at 80% height,
nearly reaching the top. Liquid surface highlighted with lighter teal #b2ebf2. Small valve
at bottom in brown #795548.

Kami: leaves #66bb6a perked energetically upward and outward, pot #8d6e63 with stripe
#a1887f. Eyes: happy closed crescents (anime joy expression). Mouth: wide bright smile.
Arms spread outward in proud presenting gesture.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner. Rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 8%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, gradients, photorealism, black outlines, complex backgrounds.
```

---

## Prompt 6 — Fuellstand 100% (Voll)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left, looking triumphantly at a large cylindrical tank on the right. The tank
is completely full — teal nutrient liquid fills the entire level window to the very top.
Kami has a triumphant, proud expression: eyes sparkling (star-shaped white highlights in
black eyes), huge confident grin, one arm raised in a fist pump victory pose, the other arm
on hip in a power stance. Leaves standing straight up, tall and proud.

A small simple star shape or sparkle accent (#fff9c4 pale yellow) floats near the full
tank to emphasize perfection.

Tank: large cylinder, about 2x Kami height. Light gray walls #bdbdbd, darker rim #9e9e9e
at top and base ring #757575. Fill level window shows teal liquid #4dd0e1 filling 100%
of the visible area, all the way to the top. Liquid surface highlighted with lighter teal
#b2ebf2 at the very top edge. Small valve at bottom in brown #795548.

Kami: leaves #66bb6a standing straight and tall, pot #8d6e63 with stripe #a1887f.
Eyes: sparkling (black with star-shaped or cross-shaped white highlights). Mouth: big
confident grin. One arm raised in victory fist pump, other arm on hip.

Sparkle accents: 2-3 small four-pointed star shapes in pale yellow #fff9c4 near the
full tank. Simple geometric shapes, no complex glow effects.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner. Rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 8%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, gradients, photorealism, black outlines, complex backgrounds.
```

---

## Uebersicht der Serie

| # | Fuellstand | Kami-Emotion | Kami-Pose | Besonderheit |
|---|-----------|-------------|----------|--------------|
| 1 | 0% | Panik/Schock | Haende an Wangen, Blaetter haengend | Warn-Dreieck orange |
| 2 | 20% | Besorgt | Kopf kratzen, unsicher | — |
| 3 | 40% | Skeptisch/Nachdenklich | Hand an Huefte, Finger zeigt hoch | — |
| 4 | 60% | Zufrieden/Ruhig | Daumen hoch, entspannt | — |
| 5 | 80% | Gluecklich | Arme praesentierend, Freude-Augen | — |
| 6 | 100% | Triumphierend/Stolz | Siegerfaust, Power-Pose | Glitzer-Sterne |

---

## Technische Hinweise fuer SVG-Konvertierung

- **Minimale Details:** Alle Prompts vermeiden Elemente unter 3px. Feine Texturen,
  Anti-Aliasing-Artefakte und Mikro-Details werden bei vtracer zu Rauschen.
- **Klare Farbflaechen:** Maximal 8-10 distinkte Farben pro Bild. Vtracer segmentiert
  besser bei klaren Farbgrenzen ohne weiche Uebergaenge.
- **Keine Messgeraete/Schlaeuche:** Im Gegensatz zu illustration-kami-tankmanagement.md
  sind diese Bilder bewusst reduziert — nur Kami + Tank. Weniger Formen = saubereres SVG.
- **Konsistente Proportionen:** Alle 6 Bilder muessen identische Tank-Position und
  Kami-Groesse haben, damit sie in der UI austauschbar sind.
- **PNG-zu-SVG Pipeline:** PNG generieren → Schachbrett-Hintergrund entfernen (falls vorhanden)
  → vtracer mit konservativen Einstellungen (wenig Pfade, grosse Mindestflaeche).

---

## Nachbearbeitung

- [ ] Alle 6 PNGs auf exakt 320x240px zuschneiden
- [ ] Pruefen ob Tank-Position und Kami-Groesse in allen 6 Bildern uebereinstimmen
- [ ] Hintergrund auf vollstaendige Transparenz pruefen
- [ ] Teal-Farbe der Naehrloesung gegen #4dd0e1 validieren
- [ ] Fuellstandshoehen visuell pruefen (0/20/40/60/80/100%)
- [ ] SVG-Konvertierung mit png-to-transparent-svg Agent durchfuehren
- [ ] SVG-Dateien auf Pfad-Komplexitaet pruefen (< 500 Pfade pro Bild ideal)
- [ ] Dateinamen: `kami-tank-fill-000.svg`, `kami-tank-fill-020.svg`, etc.
- [ ] Ablage: `src/frontend/src/assets/illustrations/tank/`
