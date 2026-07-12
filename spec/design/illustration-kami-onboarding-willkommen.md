# Grafik-Prompt: Kami — Onboarding- / Login-Willkommens-Hero

> **Typ:** illustration (Hero, Einzelmotiv)
> **Erstellt:** 2026-07-13
> **Varianten:** Light + Dark (Einsatzort rendert auf beiden Themes)
> **Zielgroesse:** 320x240px (primaer, neben Formular), skalierbar auf 640x480 fuer grossen Login-Split
> **Format:** SVG-primaer + PNG-Fallback (transparent)
> **Einsatzort:** `pages/auth/LoginPage.tsx`, `pages/auth/RegisterPage.tsx`, `pages/onboarding/OnboardingWizard.tsx` (erster Schritt)
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Einladend/Willkommen), §9 (Prompt-Baukasten), §10 (Emotion→Einsatzort)
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-03** (Critical)

---

## Kontext

Winkender Kami, der neue Nutzer begruesst — als Hero neben dem Login-/Register-Formular
bzw. im ersten Onboarding-Schritt. Aktuell tragen Login, Register und Onboarding **0**
Kami-Referenzen; die Emotion „Einladend/Willkommen" (§10 explizit fuer „Onboarding, Login,
Willkommen, erste Nutzung") ist bislang unrealisiert. Das Motiv schafft einen warmen ersten
Eindruck, senkt die Einstiegshuerde und etabliert das Maskottchen sofort bei Erstkontakt
(**Zweck** laut Audit).

Da Login/Register/Onboarding sowohl im Light- als auch im Dark-Theme rendern, werden beide
Outline-Varianten geliefert (§3.2). Der Hintergrund bleibt transparent, sodass das Motiv auf
dem jeweiligen Formular-/Split-Hintergrund sitzt.

---

## Gemeinsamer Stil-Block

```
STIL:
- Flat-Vector Comic-Illustration, cute cartoon, professional
- Klare, gleichmaessige Outlines: 2.5px Aussenkontur, 1.5px innere Details
- Flaechige Farbfuellung, KEINE Gradienten; weiche Innenschatten (10-15% dunkler)
- Kawaii-inspiriert aber professionell
- Transparenter Hintergrund (PNG alpha), Querformat 4:3, Padding ca. 10%

KAMI-FARBEN (immer identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20
```

---

## Prompt — Willkommens-Hero (Light Mode)

```
A cute comic-style mascot illustration for a plant management app, landscape 4:3 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot
stands centered-left, greeting the viewer. Generous free space to the right for a text
overlay. Kami has a Welcoming/Inviting expression: leaves perked upward and lively, large
bright wide eyes with highlight glints, broad warm smile. One arm extended and waving in
greeting, other arm relaxed at side. Open, inviting body language.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
highlight glints, mouth #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

## Prompt — Willkommens-Hero (Dark Mode)

Identisch zum Light-Prompt, nur die Outline-Zeile wird ersetzt (§3.2):

```
Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Landscape 4:3, padding 10%.
```

---

## Uebersicht

| Motiv | Pose | Emotion (§4.2) | Usage |
|---|---|---|---|
| Willkommens-Hero | Ein Arm winkend (angehoben, Hand offen), anderer locker; Blaetter aufrecht/lebendig; Freiraum rechts | **Einladend/Willkommen** | Login-/Register-Hero, Onboarding-Schritt 1 |

---

## Technische Hinweise

1. **Freiraum rechts:** Das Motiv steht bewusst links, damit im Login-Split rechts Formular
   bzw. Begruessungstext Platz hat. Bei 640x480 den Kami nicht groesser, sondern den Freiraum
   groesser skalieren.
2. **Zwei Outline-Varianten:** Light `#1b5e20`, Dark `#c8e6c9` — sonst identisch. Bei SVG kann
   die Outline-Farbe alternativ via CSS-`currentColor` themebar gemacht werden (Downstream-Entscheid).
3. **Konsistenz:** Gleicher Kami wie in `feature-kami-kernfunktionen.md` (Proportionen, Augengroesse).

---

## Nachbearbeitung Checkliste

- [ ] PNG auf 320x240px zuschneiden, Hintergrund vollstaendig transparent
- [ ] Auf 640x480 skalieren (Login-Split) und Erkennbarkeit pruefen
- [ ] Farbwerte gegen §3 Palette pruefen
- [ ] Light- **und** Dark-Outline-Variante erzeugen
- [ ] SVG-Konvertierung via vtracer, Pfad-Komplexitaet < 25 Pfade (Kami allein)
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/onboarding/`
- [ ] Dateinamen: `illustration-kami-willkommen.svg` (+ `.png`), Dark: `illustration-kami-willkommen-dark.svg`
- [ ] Barrel-Export in `assets/brand/illustrations/index.ts` ergaenzen (`kamiWelcome`)
