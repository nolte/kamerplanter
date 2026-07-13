# Grafik-Prompt: Kami — Erfolg / Celebration

> **Typ:** illustration (Feedback-Motiv, Einzelmotiv)
> **Erstellt:** 2026-07-13
> **Varianten:** Light + Dark (Success-Dialog/Snackbar rendern auf beiden Themes)
> **Zielgroesse:** 320x240px (primaer), skalierbar auf ≤180px fuer Success-Dialog/Snackbar
> **Format:** SVG-primaer + PNG-Fallback (transparent)
> **Einsatzort:** Feedback-Pfad bei „Ernte abgeschlossen" (`PlantingRunDetailPage`/`HarvestBatchDetailPage`), „Aufgabe erledigt" (`TaskQueuePage`), Phasenwechsel-Erfolg, „Tank aufgefuellt"
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Triumphierend/Feiernd), §9, §10
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-10** (Medium)

---

## Kontext

Feiernder Kami (Siegerfaust, Glitzer-Sterne) fuer Erfolgs-Momente. Im aktuellen Feedback-Pfad
existiert **kein** dedizierter Success-Kami — erreichte Meilensteine (Ernte, erledigte Aufgabe,
Phasenwechsel, aufgefuellter Tank) werden nur textuell/mit MUI-Snackbar quittiert. Das Motiv
liefert positive Verstaerkung und erhoeht Bindung/Motivation (**Zweck** laut Audit).

Ein einziges, wiederverwendbares Kern-Motiv deckt alle vier Erfolgs-Ausloeser ab (gleiche
Emotion). Es rendert in Success-Dialog und Snackbar auf beiden Themes → Light + Dark.

---

## Gemeinsamer Stil-Block

```
STIL: Flat-Vector Comic, professional; Outlines 2.5px aussen / 1.5px innen;
flaechige Farben, keine Gradienten, weiche Innenschatten (10-15% dunkler);
transparenter Hintergrund; Quadrat oder Querformat, Padding 10-12%.

KAMI-FARBEN (immer identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20
- Glitzer-Sterne #fff9c4 (blasses Gelb), Ernte-/Erfolgs-Gold #ffa726
```

---

## Prompt — Celebration (Light Mode)

```
A cute comic-style mascot illustration for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta flower pot,
centered, celebrating a success. Kami has a Triumphant/Celebrating expression: leaves standing
straight and tall, eyes sparkling with star-shaped white highlights, big confident victory
grin. One arm raised in fist pump victory pose, other arm on hip in power stance.
2-3 small four-pointed sparkle stars (#fff9c4) floating nearby.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
star-shaped highlights, mouth #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 12%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

## Prompt — Celebration (Dark Mode)

Identisch, nur Outline-Zeile ersetzen (§3.2):

```
Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 12%.
```

---

## Uebersicht

| Motiv | Pose | Emotion (§4.2) | Usage |
|---|---|---|---|
| Celebration | Ein Arm Siegerfaust nach oben, anderer an der Huefte (Power-Pose), 2–3 Glitzer-Sterne #fff9c4 | **Triumphierend/Feiernd** | Ernte abgeschlossen, Aufgabe erledigt, Phasenwechsel-Erfolg, Tank aufgefuellt |

---

## Technische Hinweise

1. **Ein Motiv, vier Ausloeser:** Bewusst generisch gehalten (kein Ernte-spezifisches Requisit),
   damit dasselbe Asset in allen vier Erfolgs-Kontexten wiederverwendbar ist. Fuer ein
   ernte-spezifisches Feier-Motiv existiert bereits `feature-kami-harvest` (Erntekorb).
2. **Quadrat-Format:** In Snackbar/Dialog wird das Motiv klein (≤180px) neben Text gezeigt →
   1:1 rendert dort robuster als 4:3.
3. **Glitzer-Sterne** als einfache vierzackige `<path>`-Formen (#fff9c4), keine Glow-Effekte
   (SVG-tauglich, §7).

---

## Nachbearbeitung Checkliste

- [ ] PNG auf 320x240px (bzw. 320x320 Quadrat) zuschneiden, Hintergrund transparent
- [ ] Auf ≤180px skalieren (Snackbar/Dialog) und Erkennbarkeit pruefen
- [ ] Farbwerte gegen §3 Palette pruefen (Glitzer #fff9c4)
- [ ] Light- **und** Dark-Outline-Variante erzeugen
- [ ] SVG-Konvertierung via vtracer
- [ ] Ablage: `src/frontend/src/assets/brand/illustrations/states/`
- [ ] Dateinamen: `state-kami-celebration.svg` (+ `.png`), Dark: `state-kami-celebration-dark.svg`
- [ ] Barrel-Export in `index.ts` ergaenzen (`kamiCelebration`)
