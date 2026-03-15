# Grafik-Prompts: Kami Phasen-Zeitstrahl

> **Typ:** Timeline-Illustrationen (Serie von 5)
> **Erstellt:** 2026-03-02
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund
> **Zielgroesse:** 256x256px (primaer), skalierbar auf 64x64 und 512x512
> **Format:** PNG (transparent), SVG-tauglich
> **Einsatzort:** Phasen-Timeline in PlantInstanceDetailPage, Gantt-Charts, Phasen-Badges, Phasen-Header
> **Referenz:** Design Guide Abschnitt 2.2 (Phasenfarben), Abschnitt 5 (Kami), REQ-003 (Phasensteuerung)

---

## Kontext

Fuenf Illustrationen von Kami (dem Kamerplanter-Maskottchen), die jeweils eine Wachstumsphase
symbolisieren. Kami waechst dabei mit — von einem winzigen Keim zu einer erntebereiten Pflanze.
Jedes Bild zeigt Kami im gleichen Terracotta-Topf, mit dem gleichen freundlichen Gesicht,
aber in fortschreitendem Wachstumsstadium. Die Bilder werden nebeneinander auf einem
horizontalen Zeitstrahl platziert und muessen daher:

- Exakt gleiche Gesamthoehe und -breite haben (1:1)
- Den Topf immer an derselben vertikalen Position zeigen (unteres Drittel)
- Visuell zusammengehoeren (gleicher Stil, gleiche Outline-Staerke)
- Einzeln erkennbar und unterscheidbar sein
- Bei 64x64px noch als Phase identifizierbar sein

---

## Gemeinsame Stilregeln (fuer ALLE 5 Bilder)

```
STIL:
- Flat-Vector Comic-Illustration, cute cartoon character
- Klare, gleichmaessige Outlines: 2.5px Aussenkontur, 1.5px innere Details
- Outline-Farbe: dunkles Gruen #1b5e20 (NICHT schwarz)
- Flaechige Farbfuellung, KEINE Gradienten
- Weiche Schatten: 10-15% dunkler als Basisfarbe innerhalb der Form
- Kawaii-inspiriert aber professionell

KAMI-GRUNDFORM (in allen Bildern gleich):
- Terracotta-Topf: trapezfoermig, konisch, mit hellerem Dekostreifen
  Topf-Farben: Basis #8d6e63, Streifen #a1887f, Schatten #6d4c41
- Gesicht: Grosse runde Punkt-Augen (schwarz mit weissem Glanzpunkt),
  kleiner laechelnder Mund (nach oben gebogene Linie)
- Duenne Stiel-Arme seitlich am Topf
- Erdreich im Topf sichtbar: #795548

KOMPOSITION:
- Zentriert, 1:1 Seitenverhaeltnis
- Topf steht im unteren Drittel
- Grosszuegiger Freiraum (Padding ca. 10-15%)
- Transparenter Hintergrund (PNG alpha)

VERMEIDEN:
- Photorealismus, 3D-Render, realistische Texturen
- Text, Buchstaben, Beschriftungen im Bild
- Harte Schlagschatten, komplexe Hintergruende
- Schwarze Outlines (immer dunkles Gruen #1b5e20)
- Unterschiedliche Topfgroessen zwischen den Phasen
```

---

## Phase 1: Keimung (Germination)

> **Phasenfarbe:** `#a5d6a7` Zartgruen
> **Dateiname:** `timeline-kami-phase-germination.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A tiny sprouting seedling just emerging from soil inside a small terracotta pot.
The seedling is very small — just a pale green curved stem barely poking out of
the brown soil, with a tiny seed shell still attached to the tip. The pot has
a friendly minimal face with small dot eyes and a curious expression, looking
up at its own tiny sprout. The pot has a decorative lighter stripe around the
middle. Very small thin stick-arms at the sides of the pot, held close.

The seedling sprout is pale soft green (#a5d6a7). The soil is visible inside
the pot, dark brown (#795548). The pot is terracotta: base (#8d6e63), stripe
highlight (#a1887f), shadow areas (#6d4c41). All outlines are dark green
(#1b5e20), uniform 2-3px weight, rounded ends. The face details (eyes, mouth)
use thinner lines.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading for depth. No gradients.
Centered composition, square format, generous padding.
Transparent background, no shadows outside the character.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 1 — Keimung:
Kami ist noch ganz klein. Aus der Erde im Topf ragt nur ein winziger,
blassgruener (#a5d6a7) gebogener Keim hervor, an dessen Spitze noch eine
Samenschale haengt. Das Gesicht ist auf dem Topf — neugierig nach oben
schauend zu seinem eigenen Trieb. Die Arme sind angelegt, zurueckhaltend.
Gesamteindruck: Anfang, Erwartung, zartes Erwachen.
```

---

## Phase 2: Saemling (Seedling)

> **Phasenfarbe:** `#66bb6a` Fruehlings-Gruen
> **Dateiname:** `timeline-kami-phase-seedling.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A small young seedling growing from a terracotta pot. The seedling has a
short thin green stem with two small cotyledon leaves (round, simple shape)
and two tiny true leaves just emerging between them. The plant is small but
clearly alive and growing. The pot has a friendly face with happy dot eyes
and a small smile, looking proud. Small thin stick-arms at the sides,
one arm slightly raised in a gentle wave.

The leaves are fresh spring green (#66bb6a) with lighter highlights (#98ee99).
The stem is medium green (#43a047). Soil visible in pot (#795548). Pot is
terracotta: base (#8d6e63), stripe (#a1887f), shadow (#6d4c41). All outlines
dark green (#1b5e20), 2-3px uniform, rounded. Face uses thinner detail lines.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 2 — Saemling:
Kami waechst! Ein kurzer gruener Stiel traegt zwei runde Keimblaetter und
dazwischen spriessen zwei winzige echte Blaetter. Alles in frischem
Fruehlings-Gruen (#66bb6a). Das Gesicht auf dem Topf schaut stolz und
froehlich. Ein Arm ist leicht angehoben — „Schau, ich wachse!".
Gesamteindruck: Jugend, erste Kraft, Zuversicht.
```

---

## Phase 3: Vegetativ (Vegetative)

> **Phasenfarbe:** `#2e7d32` Sattes Blattgruen
> **Dateiname:** `timeline-kami-phase-vegetative.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A bushy, healthy plant growing vigorously from a terracotta pot. The plant
has a sturdy green stem with multiple pairs of lush leaves — about 6-8
leaves total, in various sizes, the lower ones larger. The leaves are
full, round-tipped, with visible simplified leaf veins (1-2 lines each).
The plant fills the upper two-thirds of the image. The pot has a confident
happy face with bright dot eyes and a wide smile. Both stick-arms are
raised outward in a strong, energetic pose — flexing.

The leaves are rich deep green (#2e7d32) as the dominant color, with some
lighter leaves (#66bb6a) at the tips and darker shadows (#005005) at the
base. Stem is medium green (#43a047). Soil in pot (#795548). Pot terracotta:
base (#8d6e63), stripe (#a1887f), shadow (#6d4c41). Outlines dark green
(#1b5e20), 2-3px, rounded. A few tiny leaf highlights in light green (#81c784).

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 3 — Vegetativ:
Kami ist jetzt kraeftig und buschig! Viele satte, dunkelgruene (#2e7d32)
Blaetter in verschiedenen Groessen. Der Stiel ist stabil. Die Arme sind
nach aussen gestreckt in einer selbstbewussten „Flexing"-Pose. Das Gesicht
strahlt vor Energie und Selbstbewusstsein.
Gesamteindruck: Kraft, volles Wachstum, Vitalitaet, Hoehepunkt der
vegetativen Phase.
```

---

## Phase 4: Bluete (Flowering)

> **Phasenfarbe:** `#ab47bc` Violett/Magenta
> **Dateiname:** `timeline-kami-phase-flowering.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A beautiful flowering plant in a terracotta pot. The plant has a sturdy stem
with several green leaves AND 3 open flowers and 2 small buds. The flowers
are simple, stylized 5-petal blossoms in violet-magenta (#ab47bc) with tiny
yellow-orange centers (#ffb74d). One large flower at the top, two smaller ones
to the sides, two closed buds. The leaves are still green but slightly fewer
than the vegetative phase. The pot has a gentle, peaceful face with half-closed
happy eyes and a serene smile — enjoying the blooming. Arms relaxed at sides,
one arm gently touching a flower petal.

Flowers: violet-magenta (#ab47bc) petals, lighter highlights (#ce93d8),
yellow-orange centers (#ffb74d). Leaves: medium green (#43a047), some darker
(#2e7d32). Stem: #43a047. Pot terracotta: base (#8d6e63), stripe (#a1887f),
shadow (#6d4c41). Outlines dark green (#1b5e20), 2-3px, rounded.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 4 — Bluete:
Kami blueht! Drei einfache, stilisierte Blueten in Violett-Magenta (#ab47bc)
mit gelb-orangen Mitten (#ffb74d). Dazu zwei geschlossene Knospen. Die
Blaetter sind weiterhin gruen, aber etwas weniger dominant. Das Gesicht
zeigt einen friedlichen, geniesserischen Ausdruck mit halb geschlossenen
Augen. Ein Arm beruehrt sanft ein Bluetenblatt.
Gesamteindruck: Schoenheit, Reife, friedliche Erfuellung, Stolz.
```

---

## Phase 5: Ernte (Harvest)

> **Phasenfarbe:** `#ffa726` Goldgelb
> **Dateiname:** `timeline-kami-phase-harvest.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A mature plant with ripe golden fruits in a terracotta pot. The plant has
a sturdy stem with some green leaves and 3-4 round golden-orange fruits
hanging from short stems. The fruits are plump, round, and glowing in
warm golden-orange (#ffa726) with subtle lighter highlights (#ffcc80).
The leaves are fewer now, some slightly yellowish-green, showing natural
maturity. The pot has an excited, celebrating face — eyes wide with joy,
big open smile. Both stick-arms raised high in celebration, one arm holding
a tiny golden fruit that just fell off.

Fruits: golden-orange (#ffa726), highlights (#ffcc80), subtle shadow (#f57c00).
Leaves: yellowish-green mix — some #66bb6a, some #c5e1a5 (mature/yellowing).
Stem: #43a047. Pot terracotta: base (#8d6e63), stripe (#a1887f), shadow (#6d4c41).
Outlines dark green (#1b5e20), 2-3px, rounded. Optional: tiny golden sparkle
accents near the fruits.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 5 — Ernte:
Kami traegt Fruechte! 3-4 runde, goldgelbe (#ffa726) Fruechte haengen an
der Pflanze, strahlend und reif. Die Blaetter sind weniger und teilweise
gelblich-gruen — natuerliche Reife. Das Gesicht ist aufgeregt und feiert
mit weit offenen Augen und grossem Laecheln. Beide Arme sind hochgerissen,
ein Arm haelt eine kleine goldene Frucht die gerade abgefallen ist.
Optional winzige goldene Funkeln neben den Fruechten.
Gesamteindruck: Erfolg, Belohnung, Feier, Hoehepunkt des Zyklus.
```

---

## Gesamtuebersicht: Zeitstrahl-Reihe

```
  Phase 1        Phase 2        Phase 3        Phase 4        Phase 5
  Keimung        Saemling       Vegetativ      Bluete         Ernte
  #a5d6a7        #66bb6a        #2e7d32        #ab47bc        #ffa726

  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
  │  tiny   │    │ small  │    │ bushy  │    │flowers │    │fruits  │
  │  sprout │    │seedling│    │ plant  │    │& leaves│    │& leaves│
  │   ·     │    │  ��    │    │ 🌿🌿🌿 │    │ 🌸🌿🌸 │    │ 🍊🌿🍊 │
  │  ◉ ◉   │    │  ◉ ◉   │    │  ◉ ◉   │    │  ◡ ◡   │    │  ◉ ◉   │
  │   ◡    │    │   ◡    │    │   😄   │    │   ◡    │    │   😃   │
  │  ═══   │    │  ═══   │    │  ═══   │    │  ═══   │    │  ═══   │
  └────────┘    └────────┘    └────────┘    └────────┘    └────────┘
  neugierig      stolz        energisch     friedlich     feiernd
```

---

## Zusammenhaengende Reihe (Alternative: ein Prompt fuer alle 5)

Falls der Generator konsistentere Ergebnisse liefert wenn alle 5 Phasen in einem Bild erzeugt werden:

### Prompt (Gesamtreihe)

```
Five stages of the same cute comic plant mascot character growing in matching
terracotta pots, arranged in a horizontal row from left to right. Each pot
has a friendly face with dot eyes and a small mouth. The character is an
anthropomorphic plant that grows through five phases:

(1) GERMINATION: Tiny pale green (#a5d6a7) curved sprout barely emerging from
soil, seed shell on tip. Face is curious, looking up. Arms held close.

(2) SEEDLING: Small stem with two round cotyledon leaves and two tiny true
leaves in spring green (#66bb6a). Face is proud, one arm gently waving.

(3) VEGETATIVE: Bushy plant with 6-8 rich deep green (#2e7d32) leaves of
various sizes. Face is confident and energetic, both arms flexing outward.

(4) FLOWERING: Plant with 3 violet-magenta (#ab47bc) five-petal flowers with
yellow-orange (#ffb74d) centers, plus 2 buds. Fewer leaves. Face is peaceful
with half-closed happy eyes. One arm touching a petal.

(5) HARVEST: Plant with 3-4 round golden-orange (#ffa726) fruits, some
yellowish-green leaves showing maturity. Face is celebrating excitedly,
both arms raised, one holding a tiny fallen fruit.

All pots identical: terracotta base (#8d6e63), lighter stripe (#a1887f),
shadow (#6d4c41). Soil visible (#795548). Dark green outlines (#1b5e20),
2-3px uniform weight, rounded ends. Flat vector illustration, cute cartoon
style, flat color fills, subtle soft shading for depth. White or transparent
background. No text, no labels. Aspect ratio 5:1 (wide horizontal strip).
```

---

## Technische Hinweise

1. **Konsistenz priorisieren:** Falls Einzelbilder stilistisch zu stark variieren, die Gesamtreihe als ein Bild generieren und anschliessend in 5 Einzelbilder zuschneiden.
2. **Groessen-Reduktion:** Bei 64x64px die Blaetter/Blueten/Fruechte als einfache Farbflaechen ohne innere Details darstellen — Blattadern und Bluetenmitten sind dann nicht mehr sichtbar.
3. **Transparenz pruefen:** Nach Generierung sicherstellen, dass der Hintergrund sauber transparent ist (Alpha-Kanal). Bei Generatoren die keinen transparenten Hintergrund unterstuetzen: auf weissem Hintergrund generieren und anschliessend mit Hintergrundentfernung (remove.bg, GIMP, Photoshop) nachbearbeiten.
4. **SVG-Konvertierung:** Fuer Timeline-Einsatz in der App die PNG-Ergebnisse mit Vectorizer.ai oder Inkscape Trace Bitmap in SVG konvertieren.
5. **Dark-Mode:** Durch transparenten Hintergrund funktionieren die Bilder auf hellem UND dunklem Hintergrund. Die dunklen Gruen-Outlines (#1b5e20) sind auf dunklem Hintergrund ggf. schlecht sichtbar — fuer eine explizite Dark-Mode-Variante die Outlines auf #c8e6c9 (helles Gruen) aendern.

## Nachbearbeitung Checkliste

- [ ] Alle 5 Bilder auf exakt gleiche Groesse zuschneiden (256x256px)
- [ ] Topf-Position vertikal angleichen (unteres Drittel)
- [ ] Hintergrund sauber transparent
- [ ] Farbwerte gegen Phasenfarben-Palette validieren
- [ ] Auf 64x64 skalieren und Erkennbarkeit pruefen
- [ ] Auf 512x512 skalieren fuer Retina/HiDPI
- [ ] Optional: Dark-Mode-Varianten mit hellen Outlines (#c8e6c9) erstellen
- [ ] Dateien ablegen unter: `assets/brand/illustrations/phases/`
- [ ] Namenskonvention: `timeline-kami-phase-{name}.{format}`
