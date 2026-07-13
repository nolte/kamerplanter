# Grafik-Prompts: Kami Fachmodul-Illustrationen (10 neuere Module)

> **Typ:** Feature-Illustrationen (Serie von 10)
> **Erstellt:** 2026-07-13
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund (Outline-Swap #c8e6c9)
> **Zielgroesse:** 320x240px (primaer), skalierbar auf 160x120 und 640x480
> **Format:** SVG-primaer + PNG-Fallback (transparent)
> **Einsatzort:** Header / Empty-State der Module `aquaponik`, `environment`, `ki-assistent`, `ki-diagnose`, `ki-recognition`, `post-harvest`, `propagation`, `ueberwinterung`, `inventree`, `glossar` — deren `EmptyState`-Aufrufe fallen aktuell auf `InboxIcon` zurueck
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2, §6, §9; `feature-kami-kernfunktionen.md` (Referenzmuster der bestehenden 12)
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-06** (High)

---

## Kontext

Je eine Feature-Illustration fuer 10 neuere Fachmodule, die aktuell **0** Kami-Referenzen tragen
— analog den bestehenden 12 (`feature-kami-kernfunktionen.md`): Kami mit modultypischem Requisit,
Querformat 4:3, fuer Seiten-Header und Empty-State. **Zweck** (laut Audit): visuelle
Gleichbehandlung der neuen Module mit den etablierten 12; konsistente Empty-States statt
generischem Posteingangs-Icon.

Die Emotion ist **modulabhaengig** gemaess Audit-Zuweisung (siehe Gesamtuebersicht). Wie die
bestehende Feature-Serie: Light primaer, Dark-Mode via transparentem Hintergrund; fuer explizite
Dark-Varianten Outline auf `#c8e6c9` wechseln (§3.2).

---

## Gemeinsamer Stil-Block (fuer ALLE 10 Bilder)

```
STIL: Flat-Vector Comic, professional; Outlines 2.5px aussen / 1.5px innen (dunkelgruen #1b5e20);
flaechige Farben, KEINE Gradienten, weiche Innenschatten (10-15% dunkler); Kawaii-inspiriert
aber professionell.

KOMPOSITION: Querformat 4:3; Kami links oder zentral, Modul-Requisit rechts/daneben; Padding
ca. 10%; transparenter Hintergrund (PNG alpha); max. 1-2 Requisiten (nicht ueberladen).

KAMI-FARBEN (in allen 10 Bildern identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20

VERMEIDEN: Photorealismus, 3D, Text/Buchstaben/Zahlen, harte Schlagschatten, komplexe
Hintergruende, schwarze Outlines, >8 Farben pro Bild, Elemente unter 3px.
```

---

## 1. Aquaponik

> **Pfad:** `/aquaponik` | **Dateiname:** `feature-kami-aquaponik.svg` | **Farb-Akzent:** Wasser #4fc3f7

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, standing
beside a simplified aquaponics loop — a small fish tank with one stylized cartoon fish (#4fc3f7)
and a curved pipe carrying water up toward Kami's pot, suggesting a closed water cycle. Kami has
an Energetic/Powerful expression: leaves standing upright and taut, eyes wide open and gleaming
with energy, confident broad smile. Both stick-arms raised outward in a flexing strongman pose.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Fish tank: light gray #bdbdbd frame, teal water #4dd0e1, fish #4fc3f7.
Pipe: gray #9e9e9e.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami neben Fisch-Wasser-Kreislauf, kraftvolle Flexing-Pose. Symbolisiert das
geschlossene Aquaponik-System (Fisch ⇄ Pflanze).

---

## 2. Umgebungssteuerung (Environment)

> **Pfad:** `/environment` | **Dateiname:** `feature-kami-environment.svg` | **Farb-Akzent:** Indigo #5c6bc0

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, next to a
simplified climate control panel — a rounded rectangle with a round gauge dial and two toggle
sliders (no readable text or numbers). Kami has a Focused/Determined expression: leaves upright
and slightly tilted forward, eyes narrowed with concentration, mouth as a tight determined line
or with tiny tongue tip showing. Arms engaged with the task — one arm reaching toward a slider.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Panel: white body, indigo header #5c6bc0, gauge needle #5c6bc0,
slider tracks #bdbdbd.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami stellt konzentriert an einem Klima-/Regler-Panel (Gauge + Slider).
Symbolisiert Umgebungssteuerung & Aktorik (REQ-018).

---

## 3. KI-Assistent

> **Pfad:** `/ki-assistent` | **Dateiname:** `feature-kami-ki-assistent.svg` | **Farb-Akzent:** Indigo #5c6bc0

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, with a
speech bubble floating beside its head containing a simple green leaf glyph (no text). Kami is
helpfully answering a question. Kami has a Happy expression: leaves pointing straight upward,
large round dot eyes with white highlight glints, small curved upward smile. Arms relaxed at
sides, one hand raised slightly as if presenting the bubble.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Speech bubble: white with indigo outline #5c6bc0, small leaf glyph #66bb6a inside.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami mit Sprechblase (Blatt-Glyph, kein Text). Symbolisiert den
konversationellen KI-Assistenten.

---

## 4. KI-Diagnose

> **Pfad:** `/ki-diagnose` | **Dateiname:** `feature-kami-ki-diagnose.svg` | **Farb-Akzent:** Warnung #ed6c02

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, holding up a
magnifying glass over a single detached leaf that shows a small discolored spot (#ed6c02),
inspecting it for problems. Kami has a Curious/Searching expression: leaves tilted slightly
forward and sideways, one eye slightly larger than the other with curiosity, small "oh" mouth or
gentle smile. One arm holding the magnifying glass. A small question mark floats above one leaf.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Magnifying glass: gray handle #9e9e9e, clear glass circle. Leaf under inspection:
#66bb6a with an orange spot #ed6c02.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami untersucht mit Lupe ein Blatt mit Fleck. Symbolisiert die
KI-gestuetzte Schaden-/Krankheitsdiagnose (REQ-044).

---

## 5. KI-Erkennung (Recognition)

> **Pfad:** `/ki-recognition` | **Dateiname:** `feature-kami-ki-recognition.svg` | **Farb-Akzent:** Indigo #5c6bc0

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, next to a
simplified camera/viewfinder frame (rounded rectangle with corner brackets) aimed at a small
potted plant, as if identifying it. Kami has a Curious/Searching expression: leaves tilted
slightly forward and sideways, one eye slightly larger than the other with curiosity, small "oh"
mouth or gentle smile. One arm at chin, the other gesturing toward the viewfinder.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Viewfinder frame: indigo corner brackets #5c6bc0. Small plant inside:
leaves #a5d6a7, pot #a1887f.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami richtet einen Sucher-Rahmen auf eine Pflanze. Symbolisiert die
Foto-Pflanzenerkennung (REQ-043).

---

## 6. Post-Harvest (Modul-Header)

> **Pfad:** `/post-harvest` | **Dateiname:** `feature-kami-post-harvest.svg` | **Farb-Akzent:** Gold #ffa726

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, beside a
storage jar with a lid and, above, a short drying line with 2 hanging golden-brown bundles
(#ffa726), representing post-harvest processing. Kami has a Peaceful/Serene expression: leaves
relaxed and gently spread outward, eyes half-closed in a dreamy content manner, soft gentle
smile. Arms relaxed, one arm gently touching the jar lid. Overall calm satisfaction.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes half-closed crescents, mouth #1b5e20.
Jar: clear glass with gray rim #bdbdbd, lid #9e9e9e, golden-brown contents #ffa726.
Hanging bundles: #ffa726 (shadow #f57c00), line #9e9e9e.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami mit Vorratsglas + Trockengestell. Modul-Header fuer die
Nacherntebehandlung (REQ-008); ergaenzt die Phasen-Motive `drying`/`curing` (G-11).

---

## 7. Vermehrung (Propagation)

> **Pfad:** `/propagation` | **Dateiname:** `feature-kami-propagation.svg` | **Farb-Akzent:** Primary Gruen #2e7d32

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, beside a
small clear glass of water holding a cutting with tiny white roots (#e0e0e0) growing from a
green stem, representing propagation. Kami has an Energetic/Powerful expression: leaves standing
upright and taut, eyes wide open and gleaming with energy, confident broad smile. Both stick-arms
raised outward in a flexing strongman pose.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Water glass: clear body, teal water #4dd0e1. Cutting: green stem #66bb6a,
small white roots #e0e0e0.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami neben Steckling im Wasserglas (mit Wurzeln), kraftvolle Pose.
Symbolisiert Vermehrungsmanagement (REQ-017).

---

## 8. Ueberwinterung

> **Pfad:** `/ueberwinterung` | **Dateiname:** `feature-kami-ueberwinterung.svg` | **Farb-Akzent:** Eisblau #b3e5fc

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, wrapped
cozily in a light protective fleece cover around the pot, with one simple six-pointed snowflake
(#b3e5fc) floating nearby, representing overwintering protection. Kami has a Peaceful/Serene
expression: leaves relaxed and gently spread outward, eyes half-closed in a dreamy content
manner, soft gentle smile. Arms relaxed, one arm gently holding the edge of the fleece.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes half-closed crescents, mouth #1b5e20.
Fleece cover: off-white #fafafa with soft gray folds #e0e0e0. Snowflake: pale blue #b3e5fc.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami mit Vlies-Schutz und Schneeflocke, ruhig. Symbolisiert die
Ueberwinterungs-Automatik (REQ-047).

---

## 9. InvenTree (Inventar)

> **Pfad:** `/inventree` | **Dateiname:** `feature-kami-inventree.svg` | **Farb-Akzent:** Braun #795548

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, beside a
small open storage crate holding a couple of simple supply items (a rounded bottle and a small
sack) and a blank label tag hanging on the crate (no text). Kami is organizing inventory. Kami
has a Happy expression: leaves pointing straight upward, large round dot eyes with white
highlight glints, small curved upward smile. Arms relaxed at sides, one hand resting on the crate.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Crate: warm brown #795548 with lighter slats #a1887f. Items: bottle #bdbdbd,
sack #a1887f. Label tag: white with brown string #795548.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami organisiert eine Lagerkiste mit leerem Etikett (kein Text).
Symbolisiert die optionale InvenTree-Integration (REQ-016).

---

## 10. Glossar

> **Pfad:** `/glossar` | **Dateiname:** `feature-kami-glossar.svg` | **Farb-Akzent:** Indigo #5c6bc0

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, beside an
open book with a small ribbon bookmark, and a tiny lightbulb (#ffb74d) floating above one leaf
signalling understanding (no readable text on the pages — only a simple leaf sketch). Kami has a
Happy expression: leaves pointing straight upward, large round dot eyes with white highlight
glints, small curved upward smile. Arms relaxed at sides, one hand resting on the open book.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63
(stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white highlight glints,
mouth #1b5e20. Book: cream pages #fafaf5, indigo cover #5c6bc0, ribbon #ab47bc,
page sketch #bdbdbd. Lightbulb: #ffb74d.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading. Minimal detail — clean shapes suitable for SVG conversion. No fine textures,
no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

**Beschreibung:** Kami mit aufgeschlagenem Buch + Gluehbirne (Idee), kein Text. Symbolisiert
das Fachbegriff-Glossar. (Abgrenzung: `feature-kami-masterdata` = Artenkatalog/Nachschlagewerk;
Glossar = Begriffserklaerung mit Aha-Moment.)

---

## Gesamtuebersicht

| # | Modul | Requisit | Pose | Emotion (§4.2) | Farb-Akzent | Dateiname |
|---|---|---|---|---|---|---|
| 1 | aquaponik | Fisch + Wasserkreislauf | Flexing-Pose | **Energisch/Kraftvoll** | #4fc3f7 | `feature-kami-aquaponik` |
| 2 | environment | Regler-Panel (Gauge+Slider) | Arm am Slider | **Konzentriert/Fokussiert** | #5c6bc0 | `feature-kami-environment` |
| 3 | ki-assistent | Sprechblase (Blatt-Glyph) | Hand praesentiert Bubble | **Happy** | #5c6bc0 | `feature-kami-ki-assistent` |
| 4 | ki-diagnose | Lupe ueber Blatt mit Fleck | Lupe haltend, Fragezeichen | **Neugierig/Suchend** | #ed6c02 | `feature-kami-ki-diagnose` |
| 5 | ki-recognition | Kamera-Sucher auf Pflanze | Arm am Kinn, zeigt auf Sucher | **Neugierig/Suchend** | #5c6bc0 | `feature-kami-ki-recognition` |
| 6 | post-harvest | Vorratsglas + Trockengestell | Arm am Deckel, ruhig | **Friedlich/Geniesserisch** | #ffa726 | `feature-kami-post-harvest` |
| 7 | propagation | Steckling im Wasserglas | Flexing-Pose | **Energisch/Kraftvoll** | #2e7d32 | `feature-kami-propagation` |
| 8 | ueberwinterung | Vlies + Schneeflocke | Arm haelt Vlies, ruhig | **Friedlich/Geniesserisch** | #b3e5fc | `feature-kami-ueberwinterung` |
| 9 | inventree | Lagerkiste + leeres Etikett | Hand auf Kiste | **Happy** | #795548 | `feature-kami-inventree` |
| 10 | glossar | Buch + Lesezeichen + Gluehbirne | Hand auf Buch | **Happy** | #5c6bc0 | `feature-kami-glossar` |

---

## Technische Hinweise

1. **Konsistenz mit den bestehenden 12:** Gleicher Kami, gleiche Outline-Staerke, Querformat 4:3.
   Bei Stil-Drift zuerst ein Grid-Referenzbild (analog `feature-kami-kernfunktionen.md`) erzeugen.
2. **Emotion verbatim:** Jeder Prompt uebernimmt das englische §4.2-Fragment der zugewiesenen
   Emotion wortgleich. Requisiten stehen neben Kami, wo eine Emotion beide Arme belegt
   (Flexing-Pose bei aquaponik/propagation).
3. **Skalierung 160x120:** Kami + Hauptrequisit muessen erkennbar bleiben; Feindetails
   (Etikett-Schnur, Wurzeln, Gauge-Nadel) duerfen verschwinden.
4. **Dark-Mode:** Transparenter Hintergrund genuegt fuer beide Modi; explizite Dark-Varianten
   mit Outline #c8e6c9.

---

## Nachbearbeitung Checkliste

- [ ] Alle 10 Bilder auf exakt 320x240px zuschneiden, Hintergrund transparent
- [ ] Kami-Proportionen zwischen den 10 und gegen die bestehenden 12 vergleichen/angleichen
- [ ] Auf 160x120 (Erkennbarkeit) und 640x480 (HiDPI) skalieren
- [ ] Farbwerte gegen §3 Palette pruefen (max. 8 Farben pro Bild)
- [ ] Optional: Dark-Mode-Varianten mit hellen Outlines (#c8e6c9)
- [ ] SVG-Konvertierung via vtracer
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/features/`
- [ ] Namenskonvention: `feature-kami-{modul}.svg` (+ `.png`)
- [ ] Barrel-Export in `index.ts` ergaenzen (`kamiAquaponik`, `kamiEnvironment`, `kamiKiAssistent`, `kamiKiDiagnose`, `kamiKiRecognition`, `kamiPostHarvest`, `kamiPropagation`, `kamiUeberwinterung`, `kamiInventree`, `kamiGlossar`)
- [ ] Je Modul-`EmptyState` das `illustration=`-Prop verdrahten (ersetzt `InboxIcon`-Fallback)
