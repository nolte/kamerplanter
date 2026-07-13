# Grafik-Prompt: Kami — Dashboard Willkommens- / Leerzustand-Hero

> **Typ:** illustration (Hero + Empty-State, 2 Motive)
> **Erstellt:** 2026-07-13
> **Varianten:** Light + Dark (Dashboard rendert auf beiden Themes)
> **Zielgroesse:** 320x240px (Willkommens-Hero), ≤180px (Widget-Leerzustand)
> **Format:** SVG-primaer + PNG-Fallback (transparent)
> **Einsatzort:** `pages/DashboardPage.tsx` + `components/dashboard/widgets/*` (aktuell 0 Kami)
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Gluecklich/Begeistert, Neugierig/Suchend), §9, §10
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-09** (Medium); Housekeeping-Bezug **G-16** (toter Export `kamiDashboard`)

---

## Kontext

Freundlicher Kami als Willkommens-Element bzw. Leerzustand („noch keine Pflanzen/Widgets") auf
dem Dashboard. Die Hauptseite traegt aktuell **0** Kami-Referenzen. Zwei Motive:

- **Willkommen** (positiver Start) — Emotion **Gluecklich/Begeistert**.
- **Leerzustand** (keine Daten/Widgets) — Emotion **Neugierig/Suchend**.

**Bezug G-16 (Housekeeping):** Das bereits existierende, aber unkonsumierte Asset
`feature-kami-dashboard.svg` (Barrel-Export `kamiDashboard`) sollte **primaer** als
Dashboard-Hero wiederverwendet werden, statt es zu loeschen. Dieses Doc liefert zwei
**ergaenzende** Motive fuer den persoenlichen Willkommens-Ton bzw. den Widget-Leerzustand,
die das generische Feature-Motiv nicht abdeckt. Downstream entscheidet, ob `kamiDashboard`
(Hero) + `kamiDashboardEmpty` (Widget-Empty) kombiniert werden.

---

## Gemeinsamer Stil-Block

```
STIL: Flat-Vector Comic, professional; Outlines 2.5px aussen / 1.5px innen;
flaechige Farben, keine Gradienten, weiche Innenschatten; transparenter Hintergrund;
Padding 10-14%.

KAMI-FARBEN (immer identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20
```

---

## Prompt 1 — Willkommens-Hero (Light Mode)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
standing centered, presenting the dashboard with pride. Kami has a Joyful/Delighted expression:
leaves spread outward energetically, eyes closed in happy anime-style crescents (^^), wide
open bright smile. Both arms spread outward in a proud presenting gesture.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes as happy closed crescents,
mouth #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

## Prompt 2 — Widget-Leerzustand (Light Mode)

```
A cute comic-style mascot illustration for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
centered, looking curiously at an empty dashboard widget. Kami has a Curious/Searching
expression: leaves tilted slightly forward and sideways, one eye slightly larger than the
other with curiosity, small "oh" mouth or gentle smile. One arm at chin, the other gesturing
toward a small empty rounded rectangle (an empty widget card outline, light gray #e0e0e0)
beside Kami. Optional: small question mark floating above one leaf.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
highlight glints, mouth #1b5e20. Empty widget card: thin outline #e0e0e0, no fill.

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

## Uebersicht

| # | Motiv | Pose | Emotion (§4.2) | Usage |
|---|---|---|---|---|
| 1 | Willkommens-Hero | Aufrecht, Arme ausgebreitet praesentierend | **Gluecklich/Begeistert** | `DashboardPage` Kopf/Willkommen |
| 2 | Widget-Leerzustand | Ein Arm am Kinn, anderer zeigt auf leeres Widget; Fragezeichen | **Neugierig/Suchend** | leeres Widget („keine Pflanzen/Widgets") |

---

## Technische Hinweise

1. **G-16 zuerst pruefen:** Vor Neu-Generierung des Hero pruefen, ob `kamiDashboard`
   (`feature-kami-dashboard.svg`) als Hero ausreicht — dann nur Motiv 2 (Widget-Empty) neu
   erzeugen und den toten Export konsumieren.
2. **Abgrenzung G-12:** Motiv 2 ist dashboard-spezifisch (leeres Widget-Requisit); der
   generische Empty-State-Kami (G-12) bleibt der app-weite `EmptyState`-Fallback.
3. **Widget-Empty klein:** ≤180px → Details reduzieren (§5).

---

## Nachbearbeitung Checkliste

- [ ] Motiv 1 auf 320x240px, Motiv 2 auf 360x360px zuschneiden, Hintergrund transparent
- [ ] Motiv 2 auf 180px skalieren, Erkennbarkeit pruefen
- [ ] Farbwerte gegen §3 Palette pruefen
- [ ] Light- **und** Dark-Outline-Variante je Motiv erzeugen
- [ ] SVG-Konvertierung via vtracer
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/states/`
- [ ] Dateinamen: `state-kami-dashboard-welcome.svg`, `state-kami-dashboard-empty.svg` (+ `.png`, + `-dark`)
- [ ] Barrel-Export in `index.ts` ergaenzen (`kamiDashboardWelcome`, `kamiDashboardEmpty`)
