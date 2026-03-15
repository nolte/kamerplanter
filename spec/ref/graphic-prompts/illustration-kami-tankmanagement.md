# Grafik-Prompt: Kami — Tankmanagement (REQ-014)

> **Typ:** illustration
> **Erstellt:** 2026-03-08
> **Varianten:** Light + Dark
> **Zielgroesse:** 320×240px (primaer), skalierbar auf 640×480 und 160×120
> **Format:** PNG (transparent)
> **Einsatzort:** TankListPage Header, TankDetailPage Deko, TankCreateDialog Empty State, WateringEventPage Kontext-Illustration
> **Referenz:** Design Guide Abschnitt 5 (Kami-Anatomie), Abschnitt 6.1 (Illustrationsstil), Abschnitt 8.2 (Tankmanagement-Feature-Icon), REQ-014 (Tankmanagement)

---

## Kontext

REQ-014 modelliert Naehrloesung-Tanks mit pH-Wert, EC-Wert, Fuellstand, Wasserquelle
(Leitungswasser/Osmosewasser) und Mischverhaeltnis. Die Illustration soll diesen
technischen, aber lebendigen Prozess zeigen: Kami beobachtet stolz einen grossen
Naehrloesung-Tank dessen Fuellstand sichtbar ist. An der Seite haengen zwei kleine
Mess-Symbole fuer pH und EC — erkennbar als stilisierte Icons, nicht als lesbare Zahlen.
Eine duenne Rohrleitung oder ein Schlauch fuehrt vom Tank zu einem kleinen Pflanzentopf
daneben. Die Stimmung ist: organisiert, technisch versiert, aber warm und freundlich.

Diese Illustration geht deutlich ueber den generischen Tanks-Prompt in
`feature-kami-kernfunktionen.md` (Nr. 12) hinaus: mehr Szenen-Tiefe,
Naehrloesung-Kontext (gruenliches Wasser), pH/EC-Messgeraete als Requisiten
und eine Rohrverbindung zur Pflanze.

---

## Gemeinsame Stilregeln

```
KAMI-GRUNDFORM (in allen Varianten identisch):
- Anthropomorpher Keimling in Terracotta-Topf
- Topf: trapezfoermig (oben breiter), konisch, dekorativer Mittelstreifen
  Topf-Farben: Basis #8d6e63, Streifen #a1887f, Schatten #6d4c41
- Gesicht: Grosse runde Punkt-Augen (schwarz mit weissem Glanzpunkt),
  kleiner Mund (hier: beeindruckt-stolzes Laecheln)
- Zwei gruene Blaetter oben (#66bb6a, Highlight #98ee99, Schatten #2e7d32)
- Duenne Stiel-Arme seitlich am Topf

STIL:
- Flat-Vector Comic-Illustration
- Klare, gleichmaessige Outlines: 2.5px Aussenkontur, 1.5px innere Details
- Outline-Farbe: dunkles Gruen #1b5e20 (NICHT schwarz)
- Flaechige Farbfuellung, KEINE Gradienten
- Weiche Schatten: 10-15% dunkler als Basisfarbe innerhalb der Form
- Kawaii-inspiriert aber professionell, kein kindlicher Cartoon

KOMPOSITION (Querformat 4:3):
- Kami steht links (ca. 20-30% der Breite), schaut nach rechts zum Tank
- Tank: gross, zentral-rechts, ca. 60-75% der Bildhoehe
- Messgeraete-Symbole: klein, neben oder vor dem Tank haengend
- Rohrleitung: duenne Verbindungslinie vom Tank-Boden zu einem winzigen Pflanzentopf
- Transparenter Hintergrund (PNG alpha)
- Padding ca. 8-10% an allen Seiten
```

---

## Gemini Prompt — Light Mode

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left side, looking impressed and proud at a large nutrient solution tank on
the right. Kami's right arm points at the tank with an approving gesture, left arm rests
relaxed at the side. Expression: wide bright eyes, small proud smile, leaves perked upward.

Tank anatomy:
- Large cylinder shape, about 2.5 times Kami's height, positioned center-right.
- Tank body: light gray (#bdbdbd) outer walls, slightly darker rim at top (#9e9e9e)
  and base ring (#757575). Flat circular lid on top.
- Visible fill level window or transparent strip on the tank side showing the liquid
  level at approximately 65% full. The nutrient liquid inside is a soft blue-green
  (#4fc3f7 blended with a hint of #66bb6a, resulting in a teal-ish #4dd0e1) —
  suggesting a mineral nutrient solution, not plain water.
- A small faucet or valve nozzle at the lower side of the tank, in warm brown (#795548).
- A thin tube or hose leads from the faucet downward and curves toward a tiny simple
  plant pot at the very bottom right corner (a small terracotta pot with a single
  green sprout, no face, no arms — just a simple plant icon).

Two small measurement gauge symbols hanging on the tank side or floating near it:
- Left gauge: a small round dial shape with a pH label replaced by a simple water-drop
  symbol on its face (no readable text). Dial needle points to a calm position.
  Colors: white face, light indigo needle (#5c6bc0), gray frame (#9e9e9e).
- Right gauge: a small rectangular display with a simple lightning-bolt or wave symbol
  (suggesting EC / electrical conductivity). No readable numbers.
  Colors: white face, indigo symbol (#5c6bc0), gray frame.

Exact colors:
- Kami leaves: main #66bb6a, highlight #98ee99, shadow #2e7d32
- Kami pot: base #8d6e63, decorative stripe #a1887f, shadow #6d4c41
- Tank body: #bdbdbd with #9e9e9e rim and #757575 base ring
- Nutrient liquid: #4dd0e1 (teal-blue-green, partially transparent-looking behind level window)
- Liquid level highlight (surface): very light teal #b2ebf2
- Faucet/valve: warm brown #795548
- Hose/tube: thin line in #9e9e9e
- Small target plant pot (bottom right): terracotta #8d6e63, sprout #a5d6a7
- Measurement gauges frame: #9e9e9e, faces white, accents #5c6bc0
- Water-drop symbol on pH gauge: #4fc3f7
- Outlines on all elements: dark green #1b5e20, 2.5px outer, 1.5px inner details,
  rounded line caps and joins

Background: fully transparent PNG with alpha channel.

Composition: Kami on the left third, tank on the right two thirds, hose curves at
the bottom connecting tank to tiny plant pot, gauges near upper-middle tank area.
Generous padding 8% on all sides. Landscape 4:3 format.

Style: flat vector illustration, cute cartoon character, professional agrtech aesthetic.
Flat solid colors, subtle soft inner shading (10-15% darker near form edges). No gradients,
no photorealistic textures, no 3D render look.

Avoid: photorealism, 3D rendering, hard drop shadows, gradient fills, any readable text
or numbers, watermarks, black outlines (use dark green #1b5e20 only), complex background
patterns, childish crayon style, more than 8 distinct colors total.
```

---

## Gemini Prompt — Dark Mode

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format,
designed for display on dark backgrounds (#1e1e1e to #121212).

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands on the left side, looking at a large nutrient solution tank on the right with a
proud, satisfied expression. One arm points at the tank approvingly. Leaves perked upward,
wide bright eyes, small confident smile.

Tank anatomy:
- Large cylinder shape, about 2.5 times Kami's height, positioned center-right.
- Tank body: dark gray (#424242) outer walls with a slightly lighter rim (#616161)
  at the top and base — the tank reads as industrial equipment in a dark environment.
- Visible fill level window on the tank side showing nutrient liquid at approximately
  65% full. The liquid glows softly in bright teal-green (#4dd0e1) — on dark background
  this should appear slightly luminous, like a backlit display.
- A thin glowing edge highlight (#80deea) outlines the liquid surface inside the window.
- Small faucet or valve nozzle at the lower tank side: warm terracotta-brown (#8d6e63).
- A thin hose or tube leads from the faucet to a small plant pot at the bottom right
  corner (simple sprout, no face, no arms). Hose color: #616161.

Two small measurement gauge symbols near the tank:
- Left gauge: round dial with water-drop symbol (no text). Dark face (#37474f),
  bright indigo needle (#9fa8da), lighter rim (#616161).
- Right gauge: rectangular panel with wave/bolt symbol (no text). Same dark styling,
  accent (#9fa8da).

Exact colors for dark mode:
- Kami leaves: main #66bb6a (bright vivid green), highlight #98ee99, shadow #338a3e
- Kami pot: base #8d6e63, decorative stripe #a1887f, shadow #6d4c41
  (Kami pot stays warm terracotta — warm against dark background)
- Tank body: #424242 main, #616161 rim, #37474f deep shadow areas
- Nutrient liquid: #4dd0e1 with soft inner glow effect suggestion (lighter #80deea at surface)
- Faucet: #8d6e63
- Hose: #616161
- Target plant pot: #8d6e63, sprout #66bb6a
- Gauge frames: #616161, face #37474f, accent #9fa8da
- Outlines: dark mode uses white-green #c8e6c9 for Kami's main outlines, #ffffff for
  the finest accent details — or keep #1b5e20 with a soft white glow offset if the
  generator supports it. Priority: Kami must read clearly against dark background.

Background: fully transparent PNG. No background fill. The illustration must work
composited on #1e1e1e (Paper dark) and #121212 (Background dark).

Composition: identical to light variant — Kami left third, tank right two thirds,
hose at bottom, gauges upper-center of tank. Landscape 4:3, 8% padding all sides.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors with
subtle inner shading. Colors optimized for dark-background contrast: no muddy dark-on-dark
combinations, all elements must have clearly distinct values from the dark background.

Avoid: dark outlines that disappear on dark backgrounds, photorealism, 3D rendering,
gradient fills, any readable text or numbers, watermarks, hard drop shadows,
complex decorative backgrounds.
```

---

## Variationen

### Variante A: Mischvorgang — Kami giesst Konzentrat in Tank

Fokus auf den Mischvorgang (WaterMixCalculator, REQ-004/REQ-014): Kami haelt eine kleine
Duengerflasche und giesst einen winzigen Strahl in den offenen Tank-Deckel.

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami — small anthropomorphic green seedling in a terracotta pot — stands on a
small step stool next to a large cylindrical nutrient tank. Kami reaches up with one
arm holding a tiny dark bottle (fertilizer concentrate bottle, no label text, small
droplet symbol on the bottle body) and tilts it to pour a thin stream of green drops
into the open tank lid at the top. The other arm steadies against the tank rim.
Expression: focused, concentrated, tip-of-the-tongue-out or squinting eye — the effort
of precision mixing. Leaves slightly asymmetric (one raised, one lower) suggesting
active movement.

Step stool: a simple two-step cube in warm brown #795548 with #a1887f highlight.
Bottle: dark indigo #26418f bottle body, small droplet symbol in #4fc3f7, #5c6bc0 cap.
Pour stream: three to four small green droplets in arc, color #66bb6a.
Tank: identical to main prompt (light gray #bdbdbd body, teal liquid #4dd0e1 at 55% fill,
visible level window, faucet #795548 at base).
Tank lid: open circle at top, inner edge visible.

Exact colors follow main light-mode specification.
Outlines: dark green #1b5e20, 2.5px, rounded ends.
Background: transparent. Landscape 4:3 format.

Style: flat vector, cute cartoon, professional. Flat colors, soft inner shading.
Avoid: text, labels on bottle, photorealism, hard shadows, gradients.
```

### Variante B: Fuellstand-Check — Kami mit Klemmbrett schaut auf fast-leeren Tank

Fuer den Empty State oder Niedrig-Fuellstand-Warnung in der App.

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: Kami — small anthropomorphic green seedling in a terracotta pot — stands next to
a large cylindrical tank that is nearly empty (fill level at about 15%, only a small
puddle of teal liquid #4dd0e1 visible at the bottom of the level window). Kami looks
at the tank with a concerned, slightly worried expression: eyebrows furrowed (leaf angle
downward-inward), mouth as a small uncertain "o" shape. One arm holds a tiny clipboard
with a simplified level-bar graphic (three bars: bottom bar filled in gray, top two bars
empty, no readable text). The other arm points at the low fill level on the tank.

A small warning symbol — a simple triangle outline with an exclamation dot inside —
floats above the tank in warning orange (#ed6c02). Keep the warning symbol simple and
iconic, no text.

Tank: same cylinder, light gray #bdbdbd, but the level window shows almost-empty —
only 15% teal liquid at the very bottom.
Warning symbol: orange #ed6c02 triangle, outline only with filled exclamation circle.
Clipboard: white, bars in #bdbdbd (empty) and #9e9e9e (partially filled), frame #795548.
Kami pose: leaves angled slightly downward (worried), eyes concerned.
Kami colors: standard (leaves #66bb6a, pot #8d6e63).
Outlines: dark green #1b5e20, 2.5px.
Background: transparent. Landscape 4:3.

Style: flat vector, cute cartoon, professional but with worried mood — sympathetic
concern, not alarm. The scene should feel "actionable" not catastrophic.
Avoid: text, red color (use warning orange #ed6c02 not error red), photorealism.
```

---

## Technische Hinweise

- **Abgrenzung zu feature-kami-kernfunktionen.md Nr. 12:** Der dort beschriebene Tanks-Prompt zeigt Kami mit Daumen hoch neben einem generischen Wassertank (kein Naehrloesung-Fokus, keine Messgeraete, kein Schlauch). Diese Illustration hier ist die tiefere, kontextreichere Version fuer TankDetailPage und spezifische Tank-Workflows. Beide koennen parallel existieren.
- **Teal-Farbe der Naehrloesung:** `#4dd0e1` (Cyan 300 aus Material Design) ist bewusst nicht im Design-System als Standardfarbe, aber passt zum Kamerplanter-Farbklima und unterscheidet Naehrloesung visuell eindeutig von blauem Leitungswasser (#4fc3f7). Bei der Generierung darauf achten, dass der Unterschied erkennbar bleibt.
- **Messgeraete-Symbole:** pH und EC NICHT als lesbare Buchstaben/Zahlen generieren — KI-Typografie ist unzuverlaessig. Stattdessen ikonische Symbole: Wassertropfen fuer pH, Blitz/Welle fuer EC. Die Funktion der Geraete wird durch Form und Kontext klar.
- **Rohrleitung/Schlauch:** Soll duenn und dezent sein — eine Linie, kein Hingucker. Zeigt nur die Verbindung Tank→Pflanze.
- **Skalierung:** Bei 160×120px koennen die kleinen Messgeraete verschwinden — Kami und Tank als Hauptelemente muessen erkennbar bleiben.
- **Konsistenz mit der Serie:** Gleiche Kami-Proportionen wie in `feature-kami-kernfunktionen.md`. Denselben Stil-Referenz-Prompt (Grid, letzter Abschnitt dieser Datei) als Stil-Anker verwenden falls generierter Kami stark abweicht.
- **Dark Mode Outline-Regel:** Im Dark-Mode-Prompt wird `#c8e6c9` als Outline-Farbe empfohlen (helles Gruen statt dunkles Gruen), damit Kami vor `#1e1e1e`/`#121212` sichtbar bleibt. Dies ist die einzige Abweichung vom Standard-Outline-System.

---

## Nachbearbeitung

- [ ] Auf exakt 320×240px zuschneiden (Haupt-Export)
- [ ] Auf 160×120px skalieren — pruefen ob Kami + Tank noch erkennbar (Messgeraete duerfen verschwinden)
- [ ] Auf 640×480px skalieren fuer Retina/HiDPI
- [ ] Hintergrund auf vollstaendige Transparenz pruefen (kein weisser Halo an Outline-Kanten)
- [ ] Teal-Farbe der Naehrloesung gegen #4dd0e1 validieren — muss eindeutig unterschiedlich von klarem Blau (#4fc3f7) wirken
- [ ] Kami-Proportionen gegen `feature-kami-kernfunktionen.md` vergleichen (gleiche Blatt-/Topf-Groesse)
- [ ] Farbwerte stichprobenartig gegen Design Guide Palette validieren
- [ ] Dark-Mode-Variante: auf #1e1e1e-Hintergrund compositen und Lesbarkeit aller Elemente pruefen
- [ ] Datei ablegen unter: `assets/brand/illustrations/features/feature-kami-tanks-detail.png`
- [ ] Variante A ablegen als: `feature-kami-tanks-mixing.png`
- [ ] Variante B ablegen als: `feature-kami-tanks-empty.png`
