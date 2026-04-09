# Grafik-Prompt: Kami — Home Assistant Integration Banner

> **Typ:** hero
> **Erstellt:** 2026-03-07
> **Aktualisiert:** 2026-04-09 (Haus-Silhouette statt Diamant — bessere Smart-Home-Erkennbarkeit)
> **Varianten:** Light + Dark + Kompakt
> **Zielgroesse:** 1920x480px (README-Header), 1200x630px (HACS-Store Social Preview), 800x200px (HA-Docs)
> **Format:** PNG (ohne Transparenz — fester Hintergrund)
> **Einsatzort:** Repository `HA_README.md` Header, HACS-Store-Listing, HA-Community-Forum-Posts, Dokumentations-Header
> **Referenz:** Design Guide Abschnitt 5 (Kami), HA-CUSTOM-INTEGRATION.md, ha-integration-icon-kami.md

---

## Kontext

Banner fuer die Home Assistant Custom Integration im Kamerplanter Monorepo. Dieses Banner unterscheidet sich vom Hauptapplikations-Banner durch einen klaren Smart-Home-/Automatisierungs-Bezug. Kami waechst in einer stilisierten Haus-Silhouette — das zentrale visuelle Element kommuniziert unmissverstaendlich „Pflanze trifft Smart Home". Das Home-Assistant-Logo wird nicht direkt verwendet (Markenrecht), stattdessen steht ein geometrisches Haus mit Connectivity-Arcs als universelles Smart-Home-Symbol.

Die Farbwelt erhaelt deutlich mehr Indigo-Anteil (#5c6bc0) als das Hauptbanner, da Indigo im Design-System den Technologie-/Wissenschafts-Aspekt repraesentiert. Kami steht als Bruecke zwischen der organischen Pflanzenwelt und der digitalen Smart-Home-Welt.

Stimmung: technisch-kompetent aber freundlich. „Deine Pflanzen, vernetzt."

---

## Gemini Prompt — Light Mode

```
A wide panoramic hero banner illustration for a smart home plant integration. Landscape format, 4:1 aspect ratio, 1920x480 pixels. The theme is "plants meet smart home — connected growing".

Left third: the mascot "Kami" — a friendly anthropomorphic green seedling character growing in a terracotta flower pot. Kami stands upright, happy and confident. Two large teardrop-shaped leaves pointing upward, large round dot eyes with white highlight, warm confident smile. Kami's body is round/oval, growing from the pot like a sprout. Thin stick arms. One arm raised, touching or resting on the edge of a large stylized house silhouette behind Kami. The other arm gives a thumbs-up.

Character colors (strict):
- Leaves: fresh green (#66bb6a) main, bright green (#98ee99) highlights near tips, deep green (#2e7d32) shadows near stem
- Stem: medium green (#43a047)
- Pot: terracotta (#8d6e63), decorative band (#a1887f), shadow (#6d4c41)
- Soil: dark brown (#795548)
- Outline: very dark green (#1b5e20), uniform 2.5px, round caps
- Eyes: solid black with white highlight dot
- Mouth: curved smile, dark green (#1b5e20)

The key visual element — a clearly visible stylized house outline behind and around Kami: a simple geometric house shape (triangle roof on a rectangle) drawn with a thick 4px rounded stroke in indigo (#5c6bc0). The house is about 1.5x Kami's height, positioned so Kami appears to be growing INSIDE the house — the pot sits on the house's "floor line". This creates the unmistakable message: "your plant, in your smart home". The house outline is solid and clearly readable, not faint or transparent.

From the house roof peak, 3-4 small concentric arc lines radiate upward in lighter indigo (#7986cb at 60% opacity), like a connectivity/signal symbol — suggesting the house is "connected" and "smart". These arcs are clean and geometric.

Center area: a visual bridge of 3 thin gently curving dotted connection lines in indigo (#9fa8da at 50% opacity) flowing from the house toward the right side. Along the lines, 4-5 small circular nodes (6-8px) in alternating green (#66bb6a) and indigo (#5c6bc0), suggesting data points flowing between the plant system and the smart home.

Right two-thirds: empty space reserved for text overlay. Clean and uncluttered.

Background: clean light gray (#f5f5f5). Very subtle gradient at bottom — warm earth tone (#efebe9 at 20% opacity) on left transitioning to cool blue-gray (#e8eaf6 at 25% opacity) on right, reinforcing the nature-to-technology bridge.

Style: clean flat 2D vector illustration, cute cartoon character, professional. Flat colors, subtle 10-15% inner shading. The house outline is the dominant compositional element besides Kami — it must be immediately recognizable as a house shape.

Avoid: photorealistic textures, 3D rendering, hard shadows, gradient fills, any text or letters, the Home Assistant logo or any third-party brand marks, Wi-Fi fan symbols, realistic circuit boards, busy tech backgrounds, black outlines (use #1b5e20 for Kami, #5c6bc0 for house), clip-art style, tiny or barely visible house shapes.
```

---

## Gemini Prompt — Dark Mode

```
A wide panoramic hero banner illustration for a smart home plant integration. Landscape format, 4:1 aspect ratio, 1920x480 pixels. Designed for dark backgrounds. Theme: "plants meet smart home — connected growing".

Left third: the mascot "Kami" — a friendly anthropomorphic green seedling in a terracotta pot. Proud confident pose, two teardrop leaves up, happy face. One arm raised touching the edge of a large stylized house silhouette behind Kami. The other arm gives a thumbs-up.

High-contrast colors for dark background:
- Leaves: bright vivid green (#66bb6a), very bright highlights (#98ee99), medium shadow (#43a047)
- Stem: #43a047
- Pot: terracotta (#8d6e63), band (#a1887f), subtle shadow (#6d4c41)
- Soil: #795548
- Outline: light green (#c8e6c9), 2.5px uniform — contrast against dark background
- Eyes: white circles with dark green fill (#1b5e20), white highlight
- Mouth: light green (#c8e6c9) curved arc

The key visual element — a clearly visible stylized house outline behind and around Kami: a simple geometric house shape (triangle roof on a rectangle) drawn with a thick 4px rounded stroke in light lavender (#9fa8da). The house is about 1.5x Kami's height, Kami grows INSIDE the house — pot on the floor line. The house outline glows subtly against the dark background — brighter than in light mode.

From the house roof peak, 3-4 small concentric arc lines radiate upward in lavender (#b0bec5 at 60% opacity), connectivity/signal symbol. Clean and geometric.

Center: 3 thin curving dotted connection lines in lavender (#9fa8da at 50% opacity) flowing from house to right. 4-5 small circular nodes (6-8px) in alternating green (#66bb6a) and lavender (#9fa8da) with subtle glow rings.

Right two-thirds: empty text space. Clean.

Background: deep dark gray (#1e1e1e). Subtle gradient at bottom — warm dark brown (#3e2723 at 12% opacity) left transitioning to cool dark indigo (#1a237e at 12% opacity) right.

Style: flat 2D vector, cute cartoon, professional. The house outline and connection lines glow subtly, adding a modern connected feel.

Avoid: photorealistic textures, 3D, hard shadows, gradients on character, any text, Home Assistant logo or third-party marks, dark green outlines (use #c8e6c9 for Kami, #9fa8da for house), busy backgrounds, Wi-Fi fan symbols, realistic tech elements, tiny or barely visible house shapes.
```

---

## Varianten

### Variante A: Sensor-Szene (Kami mit Hologramm-Display im Haus)

```
A wide panoramic banner, 4:1 aspect ratio. Left side: the mascot "Kami" — a friendly green seedling in a terracotta pot inside a stylized house outline (thick 4px indigo #5c6bc0 stroke, triangle roof on rectangle). Kami looks attentively at a tiny floating holographic-style display panel next to the right leaf. The panel is a simplified rounded rectangle in light indigo (#8e99f3 fill, 70% opacity) with two tiny abstract gauge indicators inside (simple arc shapes — one in green #66bb6a, one in sky blue #4fc3f7). No numbers or text on the panel.

Kami's expression is focused and curious — eyes looking at the panel, slight open-mouth wonder. One arm points at the panel.

From the house roof peak, 3 small connectivity arcs in lighter indigo (#7986cb at 50% opacity).

A thin dotted line (#9fa8da at 30% opacity) connects from below the panel downward, suggesting data coming from the smart home.

Right two-thirds: empty space for text. Background: light gray #f5f5f5.

Character colors: standard Kami palette — leaves #66bb6a, pot #8d6e63, outline #1b5e20, 2.5px.

Style: flat vector, cute cartoon, professional. The house + floating panel + connectivity arcs together tell the story of smart plant monitoring.

Avoid: text, numbers, realistic screens, HA logo, 3D, photorealism, tiny or faint house shapes.
```

### Variante B: Minimalistisch (Kami im Haus + Netzwerk-Punkte)

```
A wide panoramic banner, 4:1 aspect ratio. Ultra-clean composition.

Left third: Kami — green seedling in terracotta pot, happy wave pose. Standard colors: leaves #66bb6a, pot #8d6e63, outline #1b5e20. Behind Kami: a clean geometric house outline in indigo (#5c6bc0), thick 4px stroke, triangle roof on rectangle. Kami grows inside the house, pot on the floor line.

Around the house: 5-6 small circles in varying sizes (6-10px) scattered in a loose constellation pattern. Circles alternate between green (#66bb6a) and indigo (#5c6bc0). Very thin connection lines (#9fa8da at 30% opacity) link some circles to each other and to the house, forming a minimal abstract network graph. The house with Kami is at the center/origin of this network.

From the roof peak, 2-3 small connectivity arcs (#7986cb at 50% opacity).

Right two-thirds: completely empty for text. Background: #f5f5f5.

Style: extremely minimal flat vector. The house outline + network dots create an immediately readable "connected smart home" visual. Clean and modern.

Avoid: text, realistic elements, busy compositions, gradients, 3D, tiny or faint house shapes.
```

---

## Technische Hinweise

- **Kein Text im generierten Bild:** Titel „Kamerplanter" und Untertitel „Home Assistant Integration" werden nachtraeglich als Overlay gesetzt. Schriftart Roboto 600, Titel in Primary (#2e7d32 light / #66bb6a dark), Untertitel in Secondary (#5c6bc0 light / #9fa8da dark).
- **Keine Drittanbieter-Logos:** Das Home-Assistant-Logo darf NICHT im Banner erscheinen (Markenrecht). Die Haus-Silhouette ist ein generisches Smart-Home-Symbol, kein HA-Logo-Derivat.
- **Haus-Silhouette ist das Kernelement:** Im Gegensatz zum Hauptbanner (Kami allein mit Floating-Elements) definiert hier die Haus-Silhouette + Connectivity-Arcs den Kontext. Das Haus muss gross genug und kontrastreich genug sein, um auch bei 800x200 sofort als Haus erkennbar zu sein.
- **Indigo-Anteil hoeher:** Ca. 20-25% der Farbflaeche ist Indigo (Haus, Arcs, Nodes) vs. 5% im Hauptbanner.
- **HACS-Store:** Der HACS-Store zeigt Repository-Bilder als 1200x630 Social Preview. Kami + Haus duerfen nicht am Rand abgeschnitten werden.
- **Konsistenz mit HA-Icon:** Der Kami in diesem Banner muss zum `ha-integration-icon-kami.md` Icon passen — gleiche Topf-Proportionen, Augengroesse, Blattform.
- **Abgrenzung zum Hauptbanner:** Hauptbanner = warm, organisch, Gruen-dominant, Kami allein. HA-Banner = Kami im Haus, Indigo-Akzente, Connectivity-Arcs, Netzwerk-Nodes.

## Nachbearbeitung

- [ ] Titel „Kamerplanter" als Overlay (Roboto 600, Primary) rechts platzieren
- [ ] Untertitel „Home Assistant Integration" in Secondary (#5c6bc0 light / #9fa8da dark) darunter
- [ ] Optional: „HACS" Badge-Element nachtraeglich hinzufuegen (kein KI-generierter Text)
- [ ] Hintergrundfarbe validieren (#f5f5f5 light / #1e1e1e dark)
- [ ] Kami-Proportionen mit HA-Icon und Hauptbanner vergleichen
- [ ] Haus-Silhouette auf Lesbarkeit bei 800x200 pruefen
- [ ] 1200x630 HACS-Store-Crop erstellen — Kami + Haus duerfen nicht abgeschnitten werden
- [ ] 800x200 Docs-Header-Crop erstellen
- [ ] Dateien ablegen unter: `docs/img/banners/`
- [ ] Namenskonvention: `banner-ha-integration-{light|dark}-{groesse}.png`
