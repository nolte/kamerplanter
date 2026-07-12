# Grafik-Prompt: Kami — Loading-State

> **Typ:** illustration (Loading-State, Einzelmotiv)
> **Erstellt:** 2026-07-13
> **Varianten:** Light + Dark (globale Lade-/Suspense-Fallbacks rendern auf beiden Themes)
> **Zielgroesse:** ≤180px
> **Format:** SVG-primaer + PNG-Fallback (transparent)
> **Einsatzort:** globale Lade-/Suspense-Fallbacks (aktuell reiner Spinner, kein dediziertes Kami-Loading)
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Neugierig/Suchend, Konzentriert/Fokussiert), §5, §9, §10
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-17** (Low)

---

## Kontext

Kami-Motiv fuer laengere Ladevorgaenge statt eines reinen Spinners. §10 ordnet „Laden" der
Emotion **Neugierig/Suchend** (alternativ **Konzentriert/Fokussiert**) zu. Das Motiv ueberbrueckt
Wartezeit freundlich und markenkonform (**Zweck** laut Audit). Es rendert in globalen
Suspense-/Lade-Fallbacks auf beiden Themes → Light + Dark.

Das statische Motiv ist als Standbild spezifiziert; eine optionale dezente Animation (z.B.
sanft wippende Blaetter) ist Downstream-Sache und **out of scope** dieses Prompt-Docs.

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
```

---

## Prompt — Loading (Light Mode)

```
A cute comic-style mascot illustration for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
centered, waiting patiently while something loads. Kami has a Curious/Searching expression:
leaves tilted slightly forward and sideways, one eye slightly larger than the other with
curiosity, small "oh" mouth or gentle smile. One arm at chin in a watching, waiting pose.
Optional: three small simple dots in a row floating beside Kami suggesting an ongoing process
(no motion lines, no spinner ring).

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
highlight glints, mouth #1b5e20. Dots: soft green #a5d6a7.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 14%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, spinner rings, motion blur, elements smaller than 3px,
anti-aliasing artifacts.
```

## Prompt — Loading (Dark Mode)

Identisch, nur Outline-Zeile ersetzen (§3.2):

```
Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 14%.
```

---

## Uebersicht

| Motiv | Pose | Emotion (§4.2) | Usage |
|---|---|---|---|
| Loading | Blaetter leicht nach vorn, ein Arm am Kinn (wartend/beobachtend); optional 3 Punkte daneben | **Neugierig/Suchend** (alt. Konzentriert/Fokussiert) | Globale Lade-/Suspense-Fallbacks |

---

## Technische Hinweise

1. **Kein Spinner-Ring, keine Bewegungslinien** im Standbild — Animation ist Downstream-Thema.
2. **Abgrenzung G-12:** Visuell verwandt mit dem Empty-State-Kami (gleiche Grund-Emotion). Der
   Loading-Kami erhaelt die drei „Prozess-Punkte" als Unterscheidungsmerkmal; der Empty-State-Kami
   traegt Lupe + Fragezeichen.
3. **Klein-Zielgroesse:** Punkte nicht duenner als 3px bei Ziel 128px.

---

## Nachbearbeitung Checkliste

- [ ] PNG auf 360x360px zuschneiden, Hintergrund transparent
- [ ] Auf 180px und 96px skalieren, Erkennbarkeit pruefen
- [ ] Farbwerte gegen §3 Palette pruefen
- [ ] Light- **und** Dark-Outline-Variante erzeugen
- [ ] SVG-Konvertierung via vtracer
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/states/`
- [ ] Dateinamen: `state-kami-loading.svg` (+ `.png`), Dark: `state-kami-loading-dark.svg`
- [ ] Barrel-Export in `index.ts` ergaenzen (`kamiLoading`)
