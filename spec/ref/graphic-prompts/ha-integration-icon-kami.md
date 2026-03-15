# Grafik-Prompt: Kami — Home Assistant Integration Icon

> **Typ:** app-icon
> **Erstellt:** 2026-03-06
> **Varianten:** Neutral (funktioniert auf Light und Dark HA-Theme), Kompakt (32px-Variante)
> **Zielgroesse:** 512×512px (icon@2x.png), 256×256px (icon.png), Ableitung auf 32px pruefen
> **Format:** PNG (transparent)
> **Einsatzort:** `custom_components/kamerplanter/` — erscheint im HA-Integrations-Menü, auf Device-Karten, in der HACS-Store-Ansicht
> **Referenz:** Design Guide Abschnitt 3.2 (Bildmarke), Abschnitt 4.2 (Logo-Aufbau), Abschnitt 5.2 (Kami-Anatomie), Abschnitt 10.2 (Groeßen-Vereinfachung), HA-CUSTOM-INTEGRATION.md §2.1

---

## Kontext

Das Icon repraesentiert die Kamerplanter Custom Integration im Home Assistant Integrations-Menü und in der HACS-Store-Ansicht. Es wird sowohl auf hellem HA-Default-Theme als auch auf dunklen HA-Themes angezeigt, und in Entity-Cards in variablen Groessen. Das Icon muss:

- Auf weissem (#ffffff), hellgrauem (#f5f5f5), dunkelgrauem (#1c1c1c) und schwarzem (#000000) Hintergrund gleichermassen lesbar sein
- Bei 32×32px noch als Keimling-im-Topf erkennbar sein (markante Silhouette)
- Die HA-Icon-Aesthtik (klar, funktional, nicht verspielt) respektieren — Kami in seiner ruhigsten Happy-Pose, kein Aktionismus
- Kein Text, keine Beschriftung, keine Badges

Zielstimmung: freundlich-professionell. Kami steht aufrecht in seinem Topf, Blaetter nach oben, offene Augen. Die Integrations-Identitaet "Kamerplanter trifft Home Assistant" soll auf einen Blick erkennbar sein.

---

## Gemini Prompt — Standard (icon@2x.png, 512×512)

```
Flat vector cartoon icon of a small friendly anthropomorphic plant seedling growing in a terracotta flower pot. This is the mascot "Kami" for a plant management app. Happy pose: upright stance, two teardrop-shaped leaves pointing upward symmetrically, large round dot eyes with a white highlight glint, small curved smile line as mouth, thin stick arms relaxed at the sides of the pot.

Character anatomy:
- Two leaves at the top: organic teardrop shape, slightly asymmetric, left leaf tilts 10 degrees left, right leaf tilts 10 degrees right. Leaves are the dominant element, spanning about 80% of total character width.
- Thin curved stem connecting the leaf area to the pot rim.
- Pot: trapezoidal shape (wider at top than bottom), flat base, slightly rounded top rim. A lighter decorative horizontal band runs around the middle third of the pot. Small visible soil surface inside the pot rim in dark brown.
- Stick arms: thin curved lines extending sideways from the upper pot body, arms hang relaxed downward (not raised).

Exact colors:
- Leaves main: fresh green (#66bb6a)
- Leaves highlight (lighter area near tip): bright green (#98ee99)
- Leaves shadow (near stem base): deep green (#2e7d32)
- Stem: medium green (#43a047)
- Pot base: terracotta (#8d6e63)
- Pot decorative band: light terracotta (#a1887f)
- Pot shadow underside: dark terracotta (#6d4c41)
- Soil surface: dark brown (#795548)
- Outline on all elements: very dark green (#1b5e20), uniform 3px thickness, round line caps and joins
- Eyes: solid black circles with small white dot highlight at top-left
- Mouth: small curved upward arc, dark green (#1b5e20), 1.5px stroke

Background: fully transparent PNG with alpha channel. No background fill, no drop shadow extending beyond the character silhouette.

Composition: perfectly centered on a 1:1 square canvas. The pot base sits at approximately 15% from the bottom edge. The leaf tips reach approximately 15% from the top edge. The character occupies about 70% of the canvas width. Generous equal padding on all four sides.

Soft inner shading: use flat color fills only with a subtle 10-15% darker inner shadow area on the underside of leaves and lower pot body — no gradient, no photorealistic lighting.

Style: clean flat 2D vector illustration, kawaii-influenced but professional. Consistent outline weight throughout. No hatching, no texture, no grain. Suitable for SVG tracing.

Avoid: photorealistic textures, 3D rendering, hard drop shadows, gradient fills, any text or letters, watermarks, clip-art style, childish crayon aesthetic, multiple conflicting light sources, black outlines (use dark green #1b5e20 only), blurry edges.
```

---

## Gemini Prompt — Kompaktvariante (32px-Silhouette-Studie)

```
Extremely simplified flat cartoon silhouette icon of a seedling in a flower pot, optimized for very small sizes (32×32 pixels). The design must read instantly at thumbnail scale.

Simplified anatomy:
- Two large bold teardrop leaves at the top, clearly separated from each other, with a visible gap between them. Leaves take up roughly 55% of the total height.
- Short thick stem (10% of height).
- Wide trapezoidal pot body (35% of height), slightly wider at top. No internal details — just the pot silhouette with a single thin lighter horizontal line as the decorative band.
- No stick arms (too thin at this scale, omit entirely).
- No facial features (eyes and mouth are too small at 32px, omit entirely).
- No soil detail inside pot rim.

Exact colors:
- Leaves: bold fresh green (#66bb6a) with a single 15% darker shade (#2e7d32) on the inner lower quarter of each leaf
- Pot: terracotta (#8d6e63) with a slightly lighter band line (#a1887f)
- Outline: very dark green (#1b5e20), 2px uniform, round caps
- Background: fully transparent PNG

Composition: centered on 1:1 square. Pot base at 12% from bottom. Leaf tips at 12% from top. Character fills about 75% of canvas width for maximum silhouette impact at small size.

Style: bold, graphic, icon-weight. The silhouette must be immediately readable as "plant in pot" without any fine detail. Think Material Design icon simplified to pure form.

Avoid: gradients, textures, fine details, text, multiple colors per element (maximum 3 flat tones: leaf green, pot terracotta, dark outline), hard shadows, photorealism, any element thinner than 2px at 512px canvas size.
```

---

## Gemini Prompt — Hochkontrast-Variante (fuer dunkle HA-Themes)

```
Flat vector cartoon icon of the mascot "Kami" — a small friendly anthropomorphic green seedling in a terracotta pot — optimized for display on very dark backgrounds (near-black #1c1c1c to black #000000). Happy pose: upright, two teardrop leaves pointing up, large round eyes, small smile.

High-contrast color choices for dark background visibility:
- Leaves main: bright vivid green (#66bb6a) — must stand out strongly against dark background
- Leaves highlight: very bright green (#98ee99) as a secondary tone near the leaf tips
- Leaves shadow: medium green (#43a047) — not too dark, must stay readable
- Stem: medium green (#43a047)
- Pot base: warm terracotta (#8d6e63) — remains warm against dark background
- Pot decorative band: lighter terracotta (#a1887f) for definition
- Pot shadow: only very subtle darker terracotta (#6d4c41) as a thin 10% inner shadow at the very bottom of the pot — avoid making the pot too dark
- Outline: white (#ffffff) at 2.5px uniform thickness — this is the exception to the standard dark-green outline rule, necessary for visibility on dark HA backgrounds
- Eyes: white circles (#ffffff) with a dark green fill (#1b5e20) inside, plus white highlight dot
- Mouth: white curved arc (#ffffff), 1.5px

Rationale: the standard dark green outline (#1b5e20) would disappear on #1c1c1c backgrounds. White outline creates the necessary contrast for icon legibility in HA dark mode dashboards.

Background: fully transparent PNG. No background fill at all.

Composition: centered, 1:1 square, pot base at 15% from bottom, leaf tips at 15% from top, character fills 70% of canvas width.

Style: flat 2D vector cartoon, clean and professional. No gradients, no 3D, no texture.

Avoid: dark green outlines (must use white #ffffff outline in this variant), black outlines, photorealism, text, hard drop shadows, busy decoration.
```

---

## Variationen

### Variante A: Kami mit minimalem HA-Symbol-Element

Falls eine sta erkere HA-Integrations-Assoziation gewuenscht wird — Kami haelt ein kleines stilisiertes Home-Assistant-Raute-Symbol (sehr vereinfacht, nicht branded) in einem Arm:

```
Flat vector cartoon icon of the mascot "Kami" — a friendly green seedling in a terracotta pot. Happy pose. In the raised right stick arm, Kami holds a tiny simple geometric diamond/rhombus shape in white or light indigo (#8e99f3) — a minimal abstract icon suggesting smart home connectivity.

Keep the held object very small (about 12% of character height) and stylized — it should read as "technology" not as any specific brand logo. The focus stays on Kami. The diamond shape has a thin dark green outline (#1b5e20) and a light indigo fill (#8e99f3).

All other elements follow standard Kami specification:
- Leaves: fresh green (#66bb6a) main, bright (#98ee99) highlight, deep (#2e7d32) shadow
- Pot: terracotta (#8d6e63), band (#a1887f), shadow (#6d4c41)
- Outline: dark green (#1b5e20), 2.5px uniform
- Transparent background, 1:1 square, centered composition.

Style: flat 2D vector, kawaii-influenced but professional. No text, no HA logo, no photorealism.
```

### Variante B: Nur Topf und Blaetter (ohne Gesicht) — maximale Icon-Klarheit

Fuer den Fall, dass der Kawaii-Charakter-Stil im HA-Kontext zu verspielt wirkt:

```
Minimal flat vector plant icon: a small fresh green seedling with two teardrop-shaped leaves growing from a terracotta flower pot. No face, no arms, no anthropomorphic elements. Pure botanical icon in comic style.

Leaves: two slightly asymmetric teardrops, left leaf angled 12 degrees left, right angled 12 degrees right. Each leaf has one simple curved vein line in slightly darker green (#2e7d32) at 1.5px — no other internal detail.
Stem: thin, slightly curved, medium green (#43a047).
Pot: clean trapezoid, terracotta (#8d6e63), single lighter decorative horizontal band (#a1887f) at 40% height. Flat base. Tiny dark brown soil surface (#795548) visible at pot rim.
Outline: dark green (#1b5e20), 2.5px uniform, round caps.
Background: transparent PNG.
Composition: centered 1:1, generous 15% padding on all sides.

Colors match exactly: leaves #66bb6a (fill), #98ee99 (highlight spot near tip), #2e7d32 (vein and shadow base), pot #8d6e63, band #a1887f, outline #1b5e20.

Style: clean flat vector icon, professional, suitable for 32px to 512px rendering. No gradients, no texture, no photorealism, no text.
```

---

## Technische Hinweise

- **Ausgabedateinamen in HA:** `icon.png` (256×256) und `icon@2x.png` (512×512). Beide liegen in `custom_components/kamerplanter/`. Home Assistant laedt `icon@2x.png` wenn das Display-Scaling es erlaubt.
- **HA-Icon-Anzeige:** Im Integrations-Menü wird das Icon auf einem weissem oder sehr hellem Hintergrund (#f5f5f5) angezeigt. In Entity-Cards und Dashboards kann der Hintergrund beliebig sein. Der Standard-Prompt (weiße/transparente Version) reicht fuer den Haupteinsatz.
- **Silhouetten-Test:** Das generierte 512×512-Bild muss auf 32×32 skaliert werden und dann the "Topf-plus-Blaetter"-Form noch eindeutig erkennbar sein. Ist das nicht der Fall, Kompaktvariante (Prompt 2) verwenden.
- **Outline-Entscheidung:** Im HA Light Theme ist die Standard-Outline `#1b5e20` optimal. Fuer Dark-Theme-Setups die Hochkontrast-Variante mit weisser Outline verwenden. Beide Varianten erzeugen und je nach HA-Setup deployen.
- **HACS-Anforderung:** HACS erwartet `hacs.json` mit korrektem `icon`-Feld oder liest `icon.png` automatisch aus dem Repo-Root oder `custom_components/kamerplanter/`. Kein SVG — nur PNG.
- **Keine Logos Dritter:** Das HA-Logo oder das HACS-Logo duerfen NICHT in das Icon integriert werden. Variante A verwendet ein abstraktes Rauten-Symbol, kein HA-Markenelement.
- **Kami-Konsistenz:** Die generierten Icons muessen visuell zur restlichen Kami-Serie passen (`timeline-kami-phasen.md`, `feature-kami-kernfunktionen.md`). Gleiche Outline-Staerke, gleiche Topf-Proportionen, gleiche Augen-Groesse.

---

## Nachbearbeitung

- [ ] 512×512-Ergebnis auf 256×256 skalieren (Bicubic-Resampling) — als `icon.png` speichern
- [ ] 512×512-Ergebnis als `icon@2x.png` speichern (unveraendert)
- [ ] Beide Dateien auf 32×32 skalieren und Silhouetten-Erkennbarkeit pruefen — bei Unklarheit Kompaktvariante (Prompt 2) nutzen
- [ ] Hintergrund auf vollstaendige Transparenz pruefen (kein weisser Halo-Effekt an Outline-Kanten)
- [ ] Farbwerte stichprobenartig gegen Palette validieren: Blatt-Gruen muss der #66bb6a-Familie entstammen, Topf muss #8d6e63-Familie sein
- [ ] Im HA Light Theme (weisser Hintergrund) auf Lesbarkeit testen — Screenshot im HA Integrations-Menü
- [ ] Im HA Dark Theme auf dunklem Hintergrund testen — bei mangelndem Kontrast Hochkontrast-Variante (Prompt 3) deploylen
- [ ] Icon mit bestehenden Kami-Grafiken (`mascot-kami-happy.svg` sobald erstellt) auf visuelle Konsistenz vergleichen — Topf-Proportionen, Augen-Groesse, Outline-Staerke muessen uebereinstimmen
