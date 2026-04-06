# Grafik-Prompt: GitHub Repository Social Preview

> **Typ:** hero
> **Erstellt:** 2026-03-23
> **Varianten:** Light (Hauptvariante) + Dark
> **Zielgroesse:** 1280x640px (2:1 Seitenverhaeltnis)
> **Format:** PNG (ohne Transparenz — fester Hintergrund)
> **Einsatzort:** GitHub Repository Social Preview (Open Graph Image), LinkedIn-Share, Twitter-Card
> **Safe Zone:** Alle relevanten Elemente innerhalb 40pt Innenabstand von allen Kanten

---

## Kontext

Repraesentiert das Kamerplanter-Projekt auf GitHub und sozialen Netzwerken. Das Bild erscheint als Preview-Karte wenn der Repository-Link geteilt wird. GitHub schneidet das Bild bei manchen Viewports leicht zu — daher gilt eine strikte Safe Zone von 40pt an allen Seiten.

Kami steht prominent und zentriert, begruesst die Besucher einladend mit der "EINLADEND / WILLKOMMEN"-Emotion aus dem Emotionskatalog. Unterhalb von Kami wird Platz fuer zwei Typografie-Ebenen freigehalten: Haupttitel "Kamerplanter" und Untertitel "Plant Lifecycle Management". Beide Texte werden NICHT im Bild generiert — sie werden nachtraeglich als Roboto-Overlay gesetzt.

Stimmung: einladend, professionell, warm — "Willkommen bei Kamerplanter".

---

## Gemini Prompt — Light Mode

```
A 2:1 landscape format illustration for a GitHub repository social preview card of a plant management application. Output size: 1280x640 pixels.

Centered composition. The mascot "Kami" — a friendly anthropomorphic green seedling character growing in a terracotta flower pot — is placed in the upper-center of the canvas, occupying approximately the top 55% of the image height. All of Kami's body must be fully visible and kept within a safe zone of at least 40 pixels from all four edges.

Kami has a welcoming inviting expression: leaves perked upward and lively, large bright wide eyes with white highlight glints, broad warm smile. One arm extended and waving in greeting (raised, open hand), other arm relaxed at side. Open, inviting body language.

Kami's exact character colors:
- Leaves main fill: #66bb6a
- Leaves highlight near tips: #98ee99
- Leaves shadow near stem base: #2e7d32
- Stem: #43a047
- Pot body: #8d6e63
- Pot decorative horizontal band: #a1887f
- Pot underside shadow: #6d4c41
- Visible soil surface at pot rim: #795548
- Eyes: solid black circles with small white highlight dot in upper-left of each eye
- Mouth: curved upward arc in dark green #1b5e20
- All outlines: very dark green #1b5e20, uniform 2.5px outer contour, 1.5px inner details, round line caps and joins

Kami's proportions: leaves span 45% of total character height, stem/neck 10-15%, trapezoidal pot 35-40%. Two symmetrical teardrop-shaped leaves at top, each angled 10 degrees outward. Pot wider at top than bottom, with single horizontal decorative stripe at mid-height.

The lower 40% of the canvas (below Kami) is clean empty space reserved for text overlay. This area must remain unobstructed and contain only the faintest decorative background texture — a few tiny simplified leaf silhouettes (6-8 shapes) in very light green (#c8e6c9) at 15% opacity, scattered loosely across the full canvas width, barely visible, creating a subtle organic feel without competing with future text.

Around Kami, 4-5 tiny floating accent elements suggest the app's scope — all very small (4-6% of Kami's height), positioned within the safe zone:
- A small water droplet shape in sky blue (#4fc3f7) near the upper left of Kami
- A tiny four-pointed sparkle star in warm gold (#ffa726) near upper right of Kami
- One small simplified leaf silhouette in medium green (#81c784) drifting gently to Kami's left
- A tiny circular dot accent in indigo (#5c6bc0) to the lower right of the pot — suggesting the tech/science side of the app

Background: solid soft warm light gray (#f5f5f5). A very subtle, barely perceptible vignette — the background is slightly warmer at the bottom third (#f0ebe7 at 20% opacity blend), transitioning smoothly upward. No sharp gradient lines. The background must look essentially flat and clean.

Style: clean flat 2D vector illustration, cute cartoon character with kawaii influence but professional tone. Flat solid color fills with subtle 10-15% darker inner shading near form edges (no gradients). Clean crisp edges suitable for PNG output. The character is the clear focal point — all surrounding elements are supportive and minimal. No photorealism, no 3D rendering.

Composition rule: Kami's visual center of gravity sits at approximately 35-40% from the top of the canvas. The bottom 40% of the canvas is intentionally open and clear for typography overlay.

Avoid: photorealistic textures, 3D effects, hard drop shadows, gradient fills on Kami, any text or letters or numbers or symbols that could be read as typography, watermarks, clip-art style, busy backgrounds, multiple character figures, black outlines anywhere (use only dark green #1b5e20), anti-aliasing artifacts, elements outside the 40px safe zone, more than 10 distinct colors total.
```

---

## Gemini Prompt — Dark Mode

```
A 2:1 landscape format illustration for a GitHub repository social preview card of a plant management application. Output size: 1280x640 pixels. Designed for dark backgrounds.

Centered composition. The mascot "Kami" — a friendly anthropomorphic green seedling character growing in a terracotta flower pot — is placed in the upper-center of the canvas, occupying approximately the top 55% of the image height. All of Kami's body must be fully visible and kept within a safe zone of at least 40 pixels from all four edges.

Kami has a welcoming inviting expression: leaves perked upward and lively, large bright wide eyes with white highlight glints, broad warm smile. One arm extended and waving in greeting (raised, open hand), other arm relaxed at side. Open, inviting body language.

Kami's exact character colors for dark background display — same palette, enhanced contrast:
- Leaves main fill: #66bb6a (vivid, must pop against dark background)
- Leaves highlight near tips: #98ee99 (bright, slightly luminous feeling)
- Leaves shadow near stem base: #338a3e (not too dark — stays readable against dark bg)
- Stem: #43a047
- Pot body: #8d6e63
- Pot decorative horizontal band: #a1887f
- Pot underside shadow: #6d4c41
- Visible soil surface at pot rim: #795548
- Eyes: white-filled circles with dark green (#1b5e20) pupil fill and small white highlight dot — reversed for dark mode legibility
- Mouth: curved upward arc in light green #c8e6c9
- All outlines: light green #c8e6c9, uniform 2.5px outer contour, 1.5px inner details, round line caps and joins — provides contrast against the dark background

Kami's proportions: leaves span 45% of total character height, stem/neck 10-15%, trapezoidal pot 35-40%. Two symmetrical teardrop-shaped leaves at top, each angled 10 degrees outward. Pot wider at top than bottom, with single horizontal decorative stripe at mid-height.

The lower 40% of the canvas (below Kami) is clean empty space reserved for text overlay. This area must remain unobstructed and contain only the faintest decorative background texture — a few tiny simplified leaf silhouettes (6-8 shapes) in very dark muted green (#2e7d32) at 12% opacity, scattered loosely across the full canvas width. Barely visible. No competing elements.

Around Kami, 4-5 tiny floating accent elements — slightly more luminous than in light mode to glow against the dark background:
- A small water droplet in bright sky blue (#4fc3f7) near upper left of Kami
- A tiny four-pointed sparkle star in warm gold (#ffa726) near upper right of Kami — slightly larger than light variant to maintain visual weight
- One small simplified leaf silhouette in medium green (#81c784) to Kami's left
- A tiny circular dot in lavender (#9fa8da) to the lower right of the pot — the tech/science accent in dark mode secondary color

Background: solid deep dark gray (#1e1e1e). A very subtle warm undertone at the very bottom edge of the canvas (#3e2723 at 12% opacity), transitioning smoothly and imperceptibly upward — suggesting earth warmth from below. The background must appear essentially flat and solid at normal viewing size.

Style: clean flat 2D vector illustration, cute cartoon character with kawaii influence but professional tone. Flat solid color fills with subtle inner shading. Crisp clean edges. Character is the clear focal point. No photorealism, no 3D rendering.

Composition rule: Kami's visual center of gravity sits at approximately 35-40% from the top of the canvas. The bottom 40% of the canvas is intentionally open and clear for typography overlay.

Avoid: photorealistic textures, 3D effects, hard drop shadows, gradient fills on Kami, any text or letters or numbers or symbols that could be read as typography, watermarks, clip-art style, busy backgrounds, multiple character figures, dark green outlines (this variant uses light green #c8e6c9 outlines only), anti-aliasing artifacts, elements outside the 40px safe zone, more than 10 distinct colors total.
```

---

## Variationen

### Variante A: Minimale Version (maximale Kompatibilitaet)

Fuer den Fall dass der Hauptprompt zu viele Details generiert und die Komposition unruhig wirkt:

```
A 2:1 landscape format illustration, 1280x640 pixels, for a software project's GitHub social preview card.

Centered composition on a clean soft light gray background (#f5f5f5).

The single subject is "Kami" — a cute anthropomorphic green seedling mascot in a terracotta pot, placed in the upper center of the canvas. Kami occupies the top 50% of the image. The bottom 40% is completely empty clean background — reserved for text overlay, no elements at all in this zone.

Kami's welcoming expression: two teardrop-shaped leaves pointing straight upward, large round black dot eyes with small white highlight glints, broad warm smile as an upward arc. One arm raised in a gentle wave greeting, other arm relaxed at side.

Colors — Kami: leaves #66bb6a (tips #98ee99, base shadow #2e7d32), stem #43a047, pot #8d6e63 (band #a1887f, shadow bottom #6d4c41), soil rim #795548. Outlines: #1b5e20 at 2.5px, round caps.

Only 3 tiny floating accent shapes near Kami: one water drop (#4fc3f7), one sparkle star (#ffa726), one small leaf (#81c784). Each accent is no larger than 5% of Kami's height.

Style: flat vector illustration, cute cartoon, professional. Solid flat colors, minimal shading. No gradients, no textures, no photorealism, no text.

Avoid: any typography, gradients, 3D, photorealism, black outlines, busy background, elements in the bottom 40% of the canvas.
```

### Variante B: Mit Wachstums-Requisiten (reichhaltigere Komposition)

Fuer eine Version mit mehr agrartechnischem Kontext um den Seiten:

```
A 2:1 landscape format illustration, 1280x640 pixels, GitHub social preview for a plant lifecycle management app.

Upper center: the mascot "Kami" — a friendly anthropomorphic green seedling in a terracotta pot. Welcoming expression: leaves up, bright eyes, warm smile, one arm waving. Colors: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047, pot #8d6e63 (band #a1887f), soil #795548. Outlines #1b5e20 at 2.5px round caps.

Flanking Kami symmetrically at mid-height (left and right, staying within safe zone):
- Left side: a small simplified grow light panel or LED bar in warm white-yellow (#fff9c4), mounted above a tiny seedling tray with 3 miniature sprout-silhouettes in light green (#a5d6a7)
- Right side: a small pH meter or EC sensor probe shape in indigo (#5c6bc0) with a simple digital display face (no readable numbers — just a dark rectangle with a horizontal line)

All flanking elements are smaller than Kami (about 40-60% of Kami's height) and use the same flat vector style with #1b5e20 outlines.

Background: #f5f5f5. Very subtle scattered leaf micro-silhouettes in #c8e6c9 at 15% opacity across the full canvas.

Bottom 40% of canvas: completely clean background only — reserved for text overlay.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors. No gradients, no text, no photorealism.

Avoid: text, gradients, 3D, photorealism, black outlines, elements in bottom 40% reserve zone.
```

---

## Technische Hinweise

- **Safe Zone:** GitHub empfiehlt 40pt Innenabstand an allen Seiten. Bei 1280x640px entspricht das ~53px bei 96dpi oder ~107px bei 192dpi (Retina). Sicherheitshalber 80px Abstand von allen Kanten als Generierungsregel setzen.
- **Text-Platzierung Light Mode:** Titel "Kamerplanter" in Roboto 600, Groesse ca. 64-72px, Farbe `#2e7d32` (Primary), vertikal zentriert in der unteren 35% Zone. Untertitel "Plant Lifecycle Management" in Roboto 400, 28-32px, Farbe `#5c6bc0` (Secondary), 12-16px Abstand unter dem Titel.
- **Text-Platzierung Dark Mode:** Titel in `#66bb6a` (Primary Dark Mode), Untertitel in `#9fa8da` (Secondary Dark Mode). Gleiche Schriftgroessen.
- **Konsistenz zu bestehenden Prompts:** Kami muss identische Proportionen wie in `banner-kami-hauptapplikation.md` und `feature-kami-kernfunktionen.md` haben — gleiche Topfform (Trapez, Dekostreifen), identische Augengroesse (25% der Kopfbreite), 2.5px Outlines, Blattform (Tropfen mit Spitze oben).
- **GitHub-Beschnitt:** GitHub schneidet die Social Preview auf bestimmten Aufloesung leicht zu. Der Kompositions-Ansatz (Kami zentral oben, Text-Platz unten) ueberlebt Beschnitte besser als seitlich angeordnete Layouts.
- **Twitter/X-Cards:** Fuer Twitter Large Image Cards (2:1) ist dieses Format direkt verwendbar. Fuer Standard-Twitter-Cards (1.91:1) wird der linke und rechte Rand minimal beschnitten — Safe Zone deckt das ab.
- **Distinction zum bestehenden Banner:** Das `banner-kami-hauptapplikation.md` verwendet eine 4:1-Komposition mit Kami links und Textplatz rechts. Dieses Prompt verwendet 2:1 mit zentrierter Komposition und Textplatz unten — das ist das korrekte Format fuer GitHub OG-Images.

## Nachbearbeitung

- [ ] Kami-Proportionen gegen bestehende Kami-Illustrationen pruefen (Topfform, Blattgroesse, Augengroesse)
- [ ] Farbwerte pruefen: Kami-Gruen muss #66bb6a sein, Topf #8d6e63, Outlines #1b5e20 (Light) / #c8e6c9 (Dark)
- [ ] Safe-Zone-Check: Alle Elemente sind mindestens 80px von allen Kanten entfernt
- [ ] Untere 40% der Canvas pruefen — muss frei von Hauptelementen sein (nur subtile Hintergrundtextur erlaubt)
- [ ] Titel "Kamerplanter" als Roboto-600-Overlay hinzufuegen (zentriert, untere Zone)
- [ ] Untertitel "Plant Lifecycle Management" in Secondary-Farbe darunter setzen
- [ ] Light-Mode-Version in GitHub Repository Settings unter "Social Preview" hochladen
- [ ] Vorschau in GitHub pruefen — Link teilen und Twitter/LinkedIn-Card-Vorschau kontrollieren
- [ ] Dark-Mode-Version fuer README-Dark-Mode-Block bereithalten (optional)
- [ ] Dateien ablegen unter: `docs/img/social/`
- [ ] Namenskonvention: `github-social-preview-{light|dark}.png`
