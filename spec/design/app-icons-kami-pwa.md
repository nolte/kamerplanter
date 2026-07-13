# Grafik-Prompts: Kami — PWA App-Icons & App-Logo

> **Typ:** app-icon (maskable) + logo (Serie von 3)
> **Erstellt:** 2026-07-13
> **Varianten:** App-Icons opak/maskable (einfarbiger Markenhintergrund, themeneutral); App-Logo transparent Light + Dark
> **Zielgroesse:** 512x512px + 192x192px (App-Icons, maskable), 512x512px (Logo, transparent)
> **Format:** PNG (App-Icons opak/maskable); SVG-primaer + PNG (Logo, transparent)
> **Einsatzort:** `public/manifest.json` → `icons[].src = /icons/icon-512.png` & `/icons/icon-192.png` (`purpose: "any maskable"`); Homescreen-/Installations-Icon; App-Logo in Header/Splash
> **Referenz:** KAMI-CHARACTER-REFERENCE.md §4.2 (Happy), §5 (Groessen-Leiter), §6.2 (Quadrat-Komposition), §9
> **Audit-Referenz:** `spec/analysis/kami-illustration-audit-2026-07.md` — **G-01** (Critical, 512), **G-02** (Critical, 192); Logo als zugehoerige Marken-Fläche

---

## Kontext

Der Ordner `public/icons/` existiert **nicht** → die Manifest-Referenzen `/icons/icon-192.png`
und `/icons/icon-512.png` sind gebrochen (404 beim Installieren der PWA). Dieses Doc liefert die
Prompts fuer beide maskable App-Icons (G-01/G-02, Critical) sowie ein zugehoeriges,
transparentes **App-Logo** (Marken-Doppel-Gap laut Auftrag), fuer das bislang **kein** Prompt-Doc
existiert.

**Zweck** (laut Audit): Marken-Wiedererkennung auf Homescreen/Task-Switcher; behebt die
gebrochene Manifest-Referenz. Alle drei Motive nutzen die Standard-Emotion **Happy** (§4.2) als
Default-Markenzeichen.

**Maskable-Besonderheit:** App-Icons sind **opak** (voller Markenhintergrund) mit einer
Safe-Zone (~40px bei 512px), damit runde/squircle-Beschnitte auf verschiedenen Plattformen die
Kernform nicht anschneiden. Das Motiv sitzt formatfuellend, aber vollstaendig innerhalb der
Safe-Zone. Da opak, genuegt **eine** Variante je Icon (kein separates Dark). Das transparente
**Logo** rendert auf Light- und Dark-Flaechen → Light + Dark (Outline-Swap §3.2).

---

## Gemeinsamer Stil-Block

```
STIL: Flat-Vector Comic, professional; Outlines 2.5px aussen / 1.5px innen;
flaechige Farben, keine Gradienten, weiche Innenschatten; Quadrat 1:1.
Icon-Reduktion gemaess §5: formatfuellende, wiedererkennbare Silhouette.

KAMI-FARBEN (immer identisch):
- Blaetter #66bb6a (Highlight #98ee99, Schatten #2e7d32), Stiel #43a047
- Topf #8d6e63 (Streifen #a1887f, Schatten #6d4c41), Erde #795548
- Augen schwarz mit weissem Glanzpunkt, Mund #1b5e20
- Marken-Hintergrund (nur App-Icons, opak): hell #f5f5f5
```

---

## Prompt 1 — App-Icon 512x512 (maskable)

```
A cute comic-style mascot app icon for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, centered
and upright, filling the frame as a recognizable app icon. Frontal, symmetrical: two leaves
pointing straight upward, pot in the lower third, arms omitted for icon reduction. Kami has a
Happy expression: leaves pointing straight upward, large round dot eyes with white highlight
glints, small curved upward smile. Keep the entire character within a central safe zone
(~40px inset) so circular/squircle maskable cropping never clips the leaves or pot.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
highlight glints, mouth #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: solid light brand background #f5f5f5, fully opaque (no transparency) — flat, edge
to edge, filling the full square for maskable cropping. Square 1:1.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, transparency in the safe zone, elements smaller than
3px, anti-aliasing artifacts.
```

## Prompt 2 — App-Icon 192x192 (maskable, reduziert)

```
A cute comic-style mascot app icon for a plant management app, square 1:1 format.

Scene: A reduced version of the 512px icon for smaller renders. A small anthropomorphic green
seedling character (Kami) in a terracotta pot, centered, upright, frontal, filling the frame.
Simplified silhouette per the size ladder (§5, 128px stage): single-tone leaves (#66bb6a),
single-tone pot (#8d6e63) with one decorative stripe, eyes as simple dots, no mouth detail,
no arms. Happy overall impression. Keep the character within a central safe zone (~15px inset)
for maskable cropping.

Kami: leaves #66bb6a, pot #8d6e63 with stripe #a1887f. Eyes as two black dots with tiny white
highlight.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: solid light brand background #f5f5f5, fully opaque, filling the full square.
Square 1:1.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors. Strongly
reduced detail for sharp small rendering. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, facial detail, arms, transparency in the safe zone,
anti-aliasing artifacts.
```

## Prompt 3 — App-Logo (transparent, Light Mode)

```
A cute comic-style mascot logo mark for a plant management app, square 1:1 format.

Scene: A small anthropomorphic green seedling character (Kami) in a terracotta pot, centered,
upright, frontal — a clean logo mark with full detail. Kami has a Happy expression: leaves
pointing straight upward, large round dot eyes with white highlight glints, small curved
upward smile. Arms relaxed at sides. No wordmark, no lettering — mascot mark only.

Kami: leaves #66bb6a (highlight #98ee99, shadow #2e7d32), stem #43a047,
pot #8d6e63 (stripe #a1887f, shadow #6d4c41), soil #795548. Eyes black with white
highlight glints, mouth #1b5e20.

Outlines: dark green #1b5e20, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 10%.

Style: flat vector illustration, cute cartoon, professional. Flat solid colors, subtle soft
inner shading (10-15% darker near form edges). Minimal detail — clean shapes suitable for
SVG conversion. No fine textures, no elements smaller than 3px.

Avoid: text, numbers, letters, wordmark, gradients, photorealism, 3D rendering, black outlines,
hard drop shadows, complex backgrounds, elements smaller than 3px, anti-aliasing artifacts.
```

### App-Logo — Dark Mode

Identisch zu Prompt 3, nur Outline-Zeile ersetzen (§3.2):

```
Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps.
Background: fully transparent PNG. Square 1:1, padding 10%.
```

---

## Uebersicht

| # | Motiv | Groesse | Pose | Emotion (§4.2) | Hintergrund | Usage |
|---|---|---|---|---|---|---|
| 1 | App-Icon (maskable) | 512x512 | Frontal aufrecht, Blaetter gerade hoch, keine Arme, Topf unteres Drittel, Safe-Zone ~40px | **Happy** | opak #f5f5f5 | `manifest.json` `/icons/icon-512.png` |
| 2 | App-Icon (maskable) | 192x192 | Wie #1, vereinfachte Silhouette, Augen als Punkte, kein Mund | **Happy** | opak #f5f5f5 | `manifest.json` `/icons/icon-192.png` |
| 3 | App-Logo | 512x512 | Frontal aufrecht, volle Details, Arme locker | **Happy** | transparent (Light+Dark) | Header/Splash/Marke |

---

## Technische Hinweise

1. **Maskable Safe-Zone:** Kernform bei 512px innerhalb ~40px-Rand halten (Android-Adaptive,
   iOS-Squircle beschneiden unterschiedlich). Der opake Markenhintergrund fuellt den vollen
   Rahmen bis zur Kante.
2. **192px-Reduktion:** Gemaess §5 (128px-Stufe) — einfarbige Blaetter/Topf, Augen als Punkte,
   kein Mund-Detail, keine Arme. Scharf bei Android-Adaptive/Notification-Badge.
3. **Opak vs. transparent:** App-Icons opak (PNG ohne Alpha in der Safe-Zone) — deshalb **kein**
   Dark-Icon noetig. Das Logo ist transparent → Light + Dark (Outline-Swap).
4. **Optional zusaetzliche Groessen:** Aus dem 512px-Master koennen 384/256/144/96/72/48px
   abgeleitet werden, falls das Manifest spaeter erweitert wird (out of scope dieses Docs).

---

## Nachbearbeitung Checkliste

- [ ] `public/icons/` anlegen (Ordner fehlt aktuell → Ursache der gebrochenen Manifest-Referenz)
- [ ] App-Icon 512 und 192 als **opake** PNGs exportieren (kein Alpha), Safe-Zone visuell pruefen
- [ ] Maskable-Beschnitt testen (rund + squircle) — Blaetter/Topf duerfen nicht angeschnitten werden
- [ ] Logo transparent, Light- **und** Dark-Outline-Variante erzeugen
- [ ] Farbwerte gegen §3 Palette pruefen (#f5f5f5 Hintergrund, Kami-Farben)
- [ ] Ablage App-Icons: `public/icons/icon-512.png`, `public/icons/icon-192.png`
- [ ] Ablage Logo: `src/frontend/src/assets/brand/logo/logo-kami.svg` (+ `.png`, + `-dark`)
- [ ] `public/manifest.json` gegen die abgelegten Dateien verifizieren (Pfad, Groesse, `purpose`)
