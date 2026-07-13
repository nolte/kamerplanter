# Grafik-Prompts: Kami — Post-Harvest-Phasen (Trocknen & Curing)

> **Typ:** timeline-phase (Serie von 2)
> **Erstellt:** 2026-07-13
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund
> **Zielgroesse:** 256x256px (primaer), skalierbar auf 64x64 und 512x512
> **Format:** PNG (transparent) → SVG
> **Einsatzort:** `pages/durchlaeufe/PhaseKamiTimeline.tsx` — `PHASE_COLORS` definiert `drying`/`curing`, aber `KAMI_PHASE_IMAGES` hat **kein** Bild
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Friedlich/Geniesserisch), §5, §9; `timeline-kami-phasen-erweitert.md` (Referenzmuster); REQ-008 (Post-Harvest)
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-11** (Medium)

---

## Kontext

Zwei Timeline-Illustrationen fuer die Nachernte-Phasen **Trocknen** (`drying`) und **Curing**
(`curing`), analog zu den bestehenden 14 Phasen-Motiven. In `PhaseKamiTimeline.tsx` sind fuer
beide Keys bereits `PHASE_COLORS` gesetzt (Zeilen 75–76), aber `KAMI_PHASE_IMAGES` liefert
kein Bild → in der Timeline fehlt das Motiv. Diese Serie schliesst die Phasen-Abdeckung
lueckenlos bis in die Nacherntebehandlung (**Zweck** laut Audit).

Beide Phasen sind ruhige Reife-/Ruhemomente → Emotion **Friedlich/Geniesserisch** (§4.2). Wie
die uebrigen Phasen-Motive: Light primaer, Dark-Mode via transparentem Hintergrund; fuer
explizite Dark-Varianten Outline auf `#c8e6c9` wechseln (§3.2). Quadrat-Format (1:1), da
Timeline-Badges quadratisch gerendert werden.

---

## Gemeinsamer Stil-Block (fuer beide Bilder identisch)

```
STIL: Flat-Vector Comic, professional; Outlines 2.5px aussen / 1.5px innen;
flaechige Farben, keine Gradienten, weiche Innenschatten; transparenter Hintergrund;
Quadrat 1:1, Padding 12-15%. SVG-tauglich (keine Strukturen unter 3px).

KAMI-FARBEN (immer identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20
- Ernte-/Trocken-Gold #ffa726, Vorratsglas-Grau #bdbdbd
```

---

## Prompt 1 — `drying` (Trocknen)

```
A cute comic-style mascot illustration for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
standing patiently next to a simple drying rack — a horizontal line from which 2-3 harvested
bundles hang to dry (simplified golden-brown clusters #ffa726). Kami has a Peaceful/Serene
expression: leaves relaxed and gently spread outward, eyes half-closed in a dreamy content
manner, soft gentle smile. Arms relaxed, one arm gently touching a hanging bundle. Overall
feeling of calm satisfaction, patient waiting.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes half-closed crescents,
mouth #1b5e20. Hanging bundles: golden-brown #ffa726 (shadow #f57c00), thin line rack #9e9e9e.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 14%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

## Prompt 2 — `curing` (Curing / Reifung)

```
A cute comic-style mascot illustration for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
standing calmly next to a simple storage jar with a lid (curing jar). The jar is about the
same height as Kami and holds simplified golden-brown contents (#ffa726) visible through a
clear glass body. Kami has a Peaceful/Serene expression: leaves relaxed and gently spread
outward, eyes half-closed in a dreamy content manner, soft gentle smile. Arms relaxed, one
arm gently resting on the jar lid. Overall feeling of calm satisfaction.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes half-closed crescents,
mouth #1b5e20. Jar: clear glass body with light gray rim #bdbdbd and lid #9e9e9e,
golden-brown contents #ffa726.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 14%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

## Dark-Mode-Varianten

Beide Prompts identisch, nur Outline-Zeile ersetzen (§3.2):

```
Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps.
```

---

## Uebersicht der Serie

| Phase-Key | Motiv/Requisit | Pose | Emotion (§4.2) | PHASE_COLOR-Bezug |
|---|---|---|---|---|
| `drying` | Trockengestell mit haengender Ernte | Neben Gestell wartend, ein Arm beruehrt Buendel | **Friedlich/Geniesserisch** | `PhaseKamiTimeline.tsx` Z. 75 |
| `curing` | Vorratsglas mit Deckel | Ruhig neben Glas, Arm auf Deckel | **Friedlich/Geniesserisch** | `PhaseKamiTimeline.tsx` Z. 76 |

---

## Technische Hinweise

1. **Konsistenz mit den 14 Bestandsphasen:** Gleicher Kami, gleiche Outline-Staerke,
   Quadrat 1:1 wie die uebrigen `timeline-kami-phase-*`-Motive.
2. **Skalierung 64x64:** Bei kleinster Stufe (§5) nur Silhouette + Hauptrequisit erkennbar —
   Details (Deckel, Buendel-Struktur) duerfen verschwinden.
3. **Post-Harvest-Farbe:** Golden-braun #ffa726 signalisiert getrocknetes/gereiftes Erntegut,
   abgesetzt von den frischgruenen Wachstumsphasen.

---

## Nachbearbeitung Checkliste

- [ ] Beide PNGs auf exakt 256x256px zuschneiden, Hintergrund transparent
- [ ] Auf 64x64 und 512x512 skalieren, Erkennbarkeit pruefen
- [ ] Kami-Proportionen mit bestehenden Phasen-Motiven vergleichen und angleichen
- [ ] Farbwerte gegen §3 Palette pruefen
- [ ] Optional: Dark-Outline-Variante (#c8e6c9) erzeugen
- [ ] SVG-Konvertierung via vtracer
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/phases/`
- [ ] Dateinamen: `timeline-kami-phase-drying.svg`, `timeline-kami-phase-curing.svg`
- [ ] Barrel-Export in `index.ts` ergaenzen (`kamiPhaseDrying`, `kamiPhaseCuring`); in `KAMI_PHASE_IMAGES` verdrahten
