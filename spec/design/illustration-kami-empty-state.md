# Grafik-Prompt: Kami — Generischer Empty-/Such-/Kein-Ergebnis-State

> **Typ:** illustration (Empty-State, Einzelmotiv)
> **Erstellt:** 2026-07-13
> **Varianten:** Light + Dark (Fallback rendert app-weit auf beiden Themes)
> **Zielgroesse:** ≤180px (max-height im `EmptyState`-Consumer bereits 180)
> **Format:** SVG-primaer + PNG-Fallback (transparent)
> **Einsatzort:** `components/common/EmptyState.tsx` (Fallback-Zweig `InboxIcon`) → wirkt in ~25 Aufrufen ohne `illustration=` (u.a. `GlossaryPage`, `EnvironmentControlPage`, `PlantIdentificationPage`, diverse Detail-Sektionen)
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Neugierig/Suchend), §5 (Groessen), §9, §10
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-12** (Medium)

---

## Kontext

Neutraler Kami mit Lupe/Fragezeichen als Default-Empty-State statt des generischen `InboxIcon`.
Der `EmptyState`-Fallback-Zweig faellt aktuell auf ein Material-Icon zurueck, wenn kein
domaenenspezifisches `illustration=`-Prop uebergeben wird. Dieses Motiv liefert einen
markentypischen, freundlichen Default-Leerzustand und deckt zentral **alle** Listen ohne
eigene Feature-Illustration ab (**Zweck** laut Audit).

Da der Fallback app-weit greift (Light + Dark), werden beide Outline-Varianten geliefert.
Zielgroesse ist klein (≤180px) → Details gemaess §5 reduziert halten (128px-Detailstufe als
Vorlage).

---

## Gemeinsamer Stil-Block

```
STIL: Flat-Vector Comic, professional; Outlines 2.5px aussen / 1.5px innen;
flaechige Farben, keine Gradienten, weiche Innenschatten; transparenter Hintergrund;
Quadrat 1:1, Padding 12-15%. Reduzierte Detailstufe (Zielgroesse ≤180px).

KAMI-FARBEN (immer identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20
- Lupe: Griff Grau #9e9e9e, Glaskreis klar mit leichtem Glanz
```

---

## Prompt — Empty-State (Light Mode)

```
A cute comic-style mascot illustration for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
centered, looking around inquisitively as if searching an empty list. Kami has a
Curious/Searching expression: leaves tilted slightly forward and sideways, one eye slightly
larger than the other with curiosity, small "oh" mouth or gentle smile. One arm at chin or
holding a small magnifying glass. A small simple question mark shape floats above one leaf.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
highlight glints, mouth #1b5e20. Magnifying glass: gray handle #9e9e9e, clear glass circle.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 14%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

## Prompt — Empty-State (Dark Mode)

Identisch, nur Outline-Zeile ersetzen (§3.2):

```
Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 14%.
```

---

## Uebersicht

| Motiv | Pose | Emotion (§4.2) | Usage |
|---|---|---|---|
| Empty-State | Blaetter leicht nach vorn geneigt, ein Arm am Kinn oder Lupe haltend; Fragezeichen ueber einem Blatt | **Neugierig/Suchend** | `EmptyState`-Fallback (Listen/Sektionen ohne `illustration=`) |

---

## Technische Hinweise

1. **Klein-Zielgroesse:** Da der Consumer auf ≤180px begrenzt, Details gemaess §5 reduzieren —
   Fragezeichen und Lupe muessen bei 128px noch als Form lesbar sein (nicht duenner als 3px).
2. **Abgrenzung G-17:** Dieses Motiv adressiert leere/ergebnislose Zustaende; der Loading-Kami
   (`illustration-kami-loading.md`, G-17) deckt Wartezeiten ab — visuell verwandt, aber separat.
3. **Fragezeichen** als einzelne `<path>`-Form, keine feinen Serifen.

---

## Nachbearbeitung Checkliste

- [ ] PNG auf 360x360px zuschneiden (fuer scharfe ≤180px-Darstellung), Hintergrund transparent
- [ ] Auf 180px und 96px skalieren, Erkennbarkeit von Lupe/Fragezeichen pruefen
- [ ] Farbwerte gegen §3 Palette pruefen
- [ ] Light- **und** Dark-Outline-Variante erzeugen
- [ ] SVG-Konvertierung via vtracer
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/states/`
- [ ] Dateinamen: `state-kami-empty.svg` (+ `.png`), Dark: `state-kami-empty-dark.svg`
- [ ] Barrel-Export in `index.ts` ergaenzen (`kamiEmpty`); als Default in `EmptyState.tsx` verdrahten
