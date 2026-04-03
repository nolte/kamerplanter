# Grafik-Prompt: Kami Phasenicon — Flushing (Endspuelung)

> **Typ:** Timeline-Illustration (Erweiterung der Phasen-Serie)
> **Erstellt:** 2026-03-23
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund
> **Zielgroesse:** 256x256px (primaer), skalierbar auf 64x64 und 512x512
> **Format:** PNG (transparent), SVG-tauglich
> **Einsatzort:** Phasen-Timeline in PlantInstanceDetailPage, FlushingProtocol-Badge (REQ-004), Giesskalen-Ansicht kurz vor Ernte
> **Referenz:** `spec/design/timeline-kami-phasen.md` (Phasen 1–5), `spec/design/timeline-kami-phasen-erweitert.md` (Phasen 6–11), `KAMI-CHARACTER-REFERENCE.md` v1.0, REQ-004 (FlushingProtocol)

---

## Phasenfarbe

| Phase | Farbe | Hex | Begruendung |
|-------|-------|-----|-------------|
| Flushing | Reines Kanalblau | `#039be5` | Light Blue 600 — klares, sattes Wasserblau. Unterscheidet sich von Wasser-Requisit-Akzent (#4fc3f7, heller/zyaner), von Juvenil-Teal (#26a69a, gelblicher Teal), von Klettern-Dunkel (#004d40, fast schwarz-teal) und von allen Gruentoenen der Serie. Evoziert reines, sauberes Spuelwasser ohne Naehrstoffe — exakt das Flushing-Konzept. |

---

## Kontext

Flushing ist die bewusste Endspuelungsphase kurz vor der Ernte, in der die Pflanze ausschliesslich mit reinem Wasser (ohne Duenger) versorgt wird. Ziel: Naehrstoffreste aus Substrat und Pflanzengewebe herausspuelen fuer bessere Ernte-Qualitaet. Sichtbares Signal: untere Blaetter werden leicht gelblich (Naehrstoffmobilisierung), waehrend obere Blaetter noch gruen bleiben. Aus dem Topfboden tropft klares Wasser — das Ausspuelen ist aktiv sichtbar.

Kami zeigt einen konzentrierten, aufmerksamen Ausdruck. Das ist kein Leiden, kein Feiern — es ist ein bewusster, kontrollierter Prozess. Kami weiss: dieses kontrollierte Entziehen verbessert die Ernte. Die Pflanze ist noch vollstaendig lebendig, die Phase ist zeitlich begrenzt und zielgerichtet.

Im Backend ist diese Phase als `FlushingProtocol` in REQ-004 (Dünge-Logik) implementiert — mit definierter Spueldauer, Wasservolumen und Ablaufmessung.

---

## Farbpalette fuer dieses Icon

| Element | Hex | Verwendung |
|---------|-----|------------|
| Phasenfarbe / Wassertropfen | `#039be5` | Tropfen am Topfboden, Wasser-Akzent |
| Wasserglanz auf Tropfen | `#81d4fa` | Highlight auf dem Tropfen (25% heller Bereich) |
| Wasserschatten | `#0277bd` | Dunkler Rand des Tropfens |
| Obere Blaetter (noch gruen) | `#43a047` | Frisches Gruen, oben im Blattkranz |
| Obere Blaetter Highlight | `#66bb6a` | Hellere Flaechen der oberen Blaetter |
| Mittlere Blaetter (Uebergang) | `#8aab5a` | Leicht abgeblaesstes Gruen-Gelb |
| Untere Blaetter (vergilbend) | `#c5e1a5` | Deutlich gelblich-gruen, Naehrstoffmangel-Optik |
| Unterste Blaetter (stark vergilbt) | `#e6ee9c` | Fast gelb, stark vergilbt |
| Stiel | `#43a047` | Standard Kami-Stiel |
| Topf Basis | `#8d6e63` | Standard Terracotta |
| Topf Dekostreifen | `#a1887f` | Standard heller Ring |
| Topf Schatten | `#6d4c41` | Standard Topfschatten |
| Erde | `#795548` | Sichtbare Erdoberflaeche |
| Outlines | `#1b5e20` | Standard Dunkelgruen, 2.5px aussen / 1.5px innen |

---

## Emotion: KONZENTRIERT / FOKUSSIERT

Aus dem Emotionskatalog (KAMI-CHARACTER-REFERENCE.md, Abschnitt 4.2):

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | Aufrecht, leicht nach vorne geneigt — aktiv, wachsam |
| Augen | Leicht verengt, fokussiert |
| Mund | Gerade Linie oder leicht zusammengepresst — Ernst, Kontrolle |
| Arme | Im Einsatz: einer haelt eine kleine Giesskanne oder zeigt nach unten auf den Boden |

**Begruendung:** Flushing ist Praezisionsarbeit. Die bewusste Naehrstoffentziehung ist kein Unfall und kein Leiden — Kami weiss genau was er tut und warum. Der Fokus-Ausdruck signalisiert: "Kontrollierter Prozess, ich behalte das im Blick."

---

## Gemini Prompt — Light Mode

```
A cute comic-style mascot character illustration for a plant app timeline.
A plant in the flushing phase — the deliberate pre-harvest nutrient flush —
growing in a terracotta pot. The plant has a sturdy central stem with 7-8
leaves arranged in a gradient of color from bottom to top: the two lowest
leaves are clearly yellowing, almost pale yellow-green (#e6ee9c), the middle
two leaves are yellow-green (#c5e1a5) showing nutrient drawdown, and the top
3-4 leaves are still healthy green (#43a047) with lighter highlights (#66bb6a).
This deliberate top-green bottom-yellow gradient is the visual signature of
the flushing phase — the plant is actively mobilizing its stored nutrients.

Below the pot, a single round water droplet hangs from the drainage hole at
the very bottom center of the pot — clear, clean flushing water draining out.
The droplet is in pure canal blue (#039be5) with a small lighter highlight
circle on the upper-left (#81d4fa) and a slightly darker lower edge (#0277bd).
The droplet is teardrop-shaped, pointing downward, just about to fall.

The pot has a focused, concentrated face: leaves (acting as ear-like extensions)
pointing straight upward and slightly tilted forward, eyes are small dots
slightly narrowed with careful attention, mouth is a straight determined
horizontal line — the expression of someone precisely monitoring a controlled
process. One thin stick-arm is positioned slightly downward, pointing toward
the drainage area of the pot, as if tracking the outflow. The other stick-arm
is at the side, slightly bent.

Leaf colors top-to-bottom: upper (#43a047) highlight (#66bb6a), middle
transition (#8aab5a) and (#c5e1a5), lower yellowing (#e6ee9c). Stem (#43a047).
Water droplet: (#039be5) body, (#81d4fa) highlight, (#0277bd) lower edge.
Soil in pot (#795548). Pot terracotta: base (#8d6e63), stripe (#a1887f),
shadow (#6d4c41). All outlines dark green (#1b5e20), 2.5px outer edges,
1.5px inner detail lines, rounded ends and joins.

Style: flat vector illustration, cute cartoon, kawaii-influenced but
professional. Flat solid color fills with subtle soft inner shading (10-15%
darker near form edges for depth). No gradients, no textures.
Centered composition, square 1:1 format, generous 12% padding on all sides.
Transparent background (PNG with alpha channel), no shadows outside the
character boundary.
No text, no numbers, no labels, no background elements.

Avoid: photorealism, 3D rendering, gradient fills, black outlines,
hard drop shadows, complex backgrounds, text, watermarks, elements smaller
than 3px, anti-aliasing artifacts, childish or infantile cartoon style.
```

---

## Gemini Prompt — Dark Mode

```
A cute comic-style mascot character illustration for a plant app timeline,
designed for a dark background (#1e1e1e).
A plant in the flushing phase — the deliberate pre-harvest nutrient flush —
growing in a terracotta pot. The plant has a sturdy central stem with 7-8
leaves arranged in a gradient of color from bottom to top: the two lowest
leaves are clearly yellowing, almost pale yellow-green (#e6ee9c), the middle
two leaves are yellow-green (#c5e1a5) showing nutrient drawdown, and the top
3-4 leaves are still healthy and luminous green (#66bb6a) with bright
highlights (#98ee99) — slightly more vivid than the light-mode version to
maintain visual impact on dark backgrounds.

Below the pot, a single round water droplet hangs from the drainage hole at
the very bottom center of the pot — clear, clean flushing water draining out.
The droplet is in bright aqua-blue (#29b6f6) with a lighter highlight circle
(#81d4fa) and a medium-blue lower edge (#0288d1). The droplet is teardrop-
shaped, pointing downward, just about to fall. The droplet appears to glow
slightly against the dark background.

The pot has a focused, concentrated face: leaves pointing straight upward and
slightly tilted forward, eyes are small dots slightly narrowed with careful
attention, mouth is a straight determined horizontal line. One thin stick-arm
is positioned slightly downward pointing toward the drainage area, the other
stick-arm is at the side.

Leaf colors: upper bright green (#66bb6a), highlight (#98ee99), middle
transition (#8aab5a) and (#c5e1a5), lower yellowing (#e6ee9c).
Stem (#66bb6a). Water droplet: (#29b6f6) body, (#81d4fa) highlight,
(#0288d1) lower edge. Soil in pot (#795548). Pot terracotta: base (#8d6e63),
stripe (#a1887f), shadow (#6d4c41). All outlines light green (#c8e6c9)
for dark mode visibility, 2.5px outer edges, 1.5px inner detail lines,
rounded ends and joins.

Style: flat vector illustration, cute cartoon, kawaii-influenced but
professional. Flat solid color fills with subtle soft inner shading.
No gradients, no textures. Centered composition, square 1:1 format,
generous 12% padding on all sides. Transparent background (PNG with alpha
channel), no shadows outside the character boundary.
No text, no numbers, no labels, no background elements.

Avoid: photorealism, 3D rendering, gradient fills, hard drop shadows,
complex backgrounds, text, watermarks, elements smaller than 3px,
anti-aliasing artifacts, childish or infantile cartoon style.
```

---

## Variationen

### Variante A: Mit kleiner Giesskanne in der Hand

Wenn die Drainagezustand-Geste nicht klar genug wird, kann Kami alternativ
eine winzige stylisierte Giesskanne in einem Arm halten. Die Kanne ist in
reinem Blau (#039be5) — kein Gruen, kein Naehl-Teal, sondern explizit reines
Wasser ohne Naehrstoffe. Der zweite Arm zeigt nach unten auf den Boden.

```
A cute comic-style mascot character illustration for a plant app timeline.
A plant in the flushing phase growing in a terracotta pot. The plant has 7-8
leaves with a deliberate top-green bottom-yellow gradient: top leaves healthy
green (#43a047) with highlights (#66bb6a), middle leaves transitioning
yellow-green (#c5e1a5), lowest leaves clearly yellowing (#e6ee9c). A single
teardrop-shaped water droplet in clear blue (#039be5) with a lighter highlight
(#81d4fa) hangs from the bottom drainage hole of the pot.

One of Kami's thin stick-arms holds a tiny stylized watering can. The watering
can is small — about 20-25% of Kami's total height — in pure canal blue
(#039be5) with a slightly darker outline (#0277bd), and a single thin stream
of water (#81d4fa) pouring from the spout. The other stick-arm points
downward at a slight angle toward the drainage drip. The pot's face shows a
focused, concentrated expression: eyes narrowed attentively, mouth a straight
determined horizontal line, leaves tilted slightly forward with attention.

Leaf colors: upper (#43a047)/(#66bb6a), middle (#8aab5a)/(#c5e1a5), lower
(#e6ee9c). Watering can and droplet: (#039be5) main, (#81d4fa) highlights,
(#0277bd) shadow edges. Stem (#43a047). Soil (#795548). Pot: base (#8d6e63),
stripe (#a1887f), shadow (#6d4c41). Outlines (#1b5e20) 2.5px outer, 1.5px
inner, rounded caps.

Style: flat vector illustration, cute cartoon, kawaii-influenced but
professional. Flat solid fills, subtle soft shading, no gradients.
Centered, square format, 12% padding, transparent background.
No text, no labels, no background elements.
Avoid: photorealism, 3D rendering, gradients, black outlines, hard shadows,
text, elements under 3px, anti-aliasing artifacts.
```

### Variante B: Minimale Version (fuer 64x64 Badge-Einsatz)

Stark vereinfachte Version, bei der nur die essentiellen Details erhalten
bleiben: Topf mit Gesicht, zwei klar zweifarbig dargestellte Blattgruppen
(oben gruen / unten gelb), ein einzelner blauer Tropfen. Keine Arme, keine
Giesskanne, keine Blattadern.

```
A cute simple mascot icon for a plant phase badge.
A small plant in a terracotta pot with a friendly face. The plant has four
leaves total: the top two leaves are solid healthy green (#43a047), the
bottom two leaves are clearly yellowing (#c5e1a5) — a deliberate two-tone
top-green bottom-yellow pattern. Below the pot, a single small round
water droplet in blue (#039be5) with a white highlight dot hangs beneath
the drainage hole.

The pot has simple dot eyes and a straight mouth line — focused and attentive.
No arms in this simplified version.

Leaf colors: top (#43a047), bottom (#c5e1a5). Droplet (#039be5), highlight
(#ffffff). Pot: base (#8d6e63), stripe (#a1887f), shadow (#6d4c41).
Soil (#795548). Outlines (#1b5e20) uniform 2px, rounded.

Style: flat vector icon, minimal cartoon, clean geometric shapes.
Flat solid fills only, no gradients, no inner shading.
Centered, square format, 10% padding, transparent background.
No text, no labels, no background elements.
Avoid: photorealism, gradients, complex details, elements under 3px.
```

---

## Visuelle Beschreibung

```
Flushing-Phase — Endspuelung:
Kami betreut seine Pflanze waehrend der kontrollierten Naehrstoffentziehung.
Die Pflanze zeigt das charakteristische Flushing-Muster: obere Blaetter
noch in frischem Gruen (#43a047), die mittleren bereits leicht verblaesst
(#c5e1a5), die untersten deutlich gelblich (#e6ee9c). Dieses Farbgefaelle
von oben nach unten ist das visuelle Erkennungszeichen der Phase — die
Pflanze mobilisiert ihre Naehrstoffreserven aus den aelteren Blaettern.

Am Topfboden haengt ein einzelner klarer Tropfen (#039be5) — das Spuelwasser
drainiert durch das Substrat. Er ist rund, mit hellem Glanzpunkt, am Punkt
des Ablaufens. Klein aber prazise platziert, ein klares Symbol des Prozesses.

Das Gesicht auf dem Topf zeigt konzentrierten Fokus: Blaetter leicht nach
vorne geneigt (wachsam), Augen leicht verengt, Mund eine gerade Linie.
Kein Stress, kein Leiden — dieser Ausdruck sagt "Ich weiss was ich tue."
Die Armhaltung unterstreicht das: zeigend auf den Abfluss, den Prozess
beobachtend.

Gesamteindruck: Kontrolle, Praezision, bewusstes Handeln,
die ruhige Spannung kurz vor der Ernte.

Serienposition: Nach Ernte (Phase 5, #ffa726) oder Bluete (Phase 4, #ab47bc),
vor dem Erntestart. In der Hydroponik/Cannabis-Timeline typischerweise
letzte Phase vor dem Harvest-Icon.
```

---

## Einordnung in die Phasen-Bibliothek

```
Farb-Kollisionscheck Flushing (#039be5) gegen alle bestehenden Phasen:

  #039be5 (Flushing)  vs. #4fc3f7 (Wasser-Requisit)  — heller/zyaner, Flushing dunkler/saetter
  #039be5 (Flushing)  vs. #26a69a (Juvenil/Teal)      — Teal hat Gruenstich, Flushing ist klares Blau
  #039be5 (Flushing)  vs. #004d40 (Klettern)          — Klettern fast schwarz-teal, klar verschieden
  #039be5 (Flushing)  vs. #78909c (Dormanz)           — Dormanz ist blau-grau, Flushing ist sattes Blau
  #039be5 (Flushing)  vs. #5c6bc0 (Indigo/Technik)    — Indigo ist violett-blau, klar verschieden
  #039be5 (Flushing)  vs. alle Gruentoene             — kein Konflikt, Blau vs. Gruen
  #039be5 (Flushing)  vs. Orangetoene (#ffa726 etc.)  — kein Konflikt
  => Keine Farbkollision. #039be5 ist die einzige reine Blaufarbe in der Serie.

Erweiterte Timeline mit Flushing:

  Phase 1      Phase 2      Phase 3      Phase 4      Phase 5
  Keimung      Saemling     Vegetativ    Bluete       Ernte
  #a5d6a7      #66bb6a      #2e7d32      #ab47bc      #ffa726

  Phase 6      Phase 7      Phase 8      Phase 9      Phase 10
  Ripening     Juvenil      Klettern     Reife        Dormanz
  #e65100      #26a69a      #004d40      #33691e      #78909c

  Phase 11     Phase 12 (neu)
  Seneszenz    Flushing
  #d4a056      #039be5

  Flushing ordnet sich typischerweise zwischen Bluete (Phase 4) und
  Ernte (Phase 5) ein — oder als separate Post-Bluete-Phase in
  Hydroponik- und Cannabis-spezifischen Lifecycle-Profilen.
```

---

## Technische Hinweise

1. **Blattfarb-Gradient als Erkennungsmerkmal:** Das Top-Gruen / Bottom-Gelb Muster ist das visuelle Alleinstellungsmerkmal dieser Phase. Bei 64x64px darauf achten, dass mindestens zwei klar verschiedene Gruppen von Blaettern sichtbar sind — eine gruene Gruppe oben, eine gelbliche unten. Wenn das nicht moeglich ist, nur diese zwei Gruppen darstellen, alle anderen Details weglassen.

2. **Tropfen-Groesse:** Der Drainagetropfen muss bei 256px gross genug sein um erkennbar zu sein (mindestens 20-25px Durchmesser), aber nicht so gross dass er mit dem Topf konkurriert. Bei 64px kann der Tropfen auf einen einzelnen blauen Punkt (6-8px) vereinfacht werden — er bleibt als Farbakzent trotzdem lesbar.

3. **Gelb-Gruen-Spektrum:** Die Abstufung #43a047 → #8aab5a → #c5e1a5 → #e6ee9c muss in der Gesamt-Kamerplanter-UI nicht mit Warnfarben verwechselt werden. Vergilbung bei Flushing ist GEWOLLT und POSITIV, nicht ein Fehler-Signal. Das fokussierte Gesicht von Kami unterstreicht das — kein Panik-Ausdruck, kein Warndreieck.

4. **Phasenfarbe #039be5 als Badge-Hintergrund:** Im UI-Kontext als Chip/Badge-Hintergrundfarbe auf dunklem Text (#1e1e1e oder #000000) verwenden. WCAG-Kontrast bei 16px+ Text ausreichend. Bei sehr kleinen Badges (unter 20px) auf ausreichende Groesse achten.

5. **Drainagetropfen-Positionierung:** Der Tropfen haengt exakt unter der Mitte des Topfbodens — nicht seitlich. Das signalisiert das Durchspuelen durch das Substrat, nicht seitliches Auslaufen. Wichtig fuer die botanische Korrektheit des Konzepts (Drainage durch das Substrat = Flushing-Mechanismus).

6. **Dark-Mode-Outlines:** Wie alle anderen Phasen-Icons: Fuer explizite Dark-Mode-Varianten die Outlines von #1b5e20 auf #c8e6c9 aendern. Die Phasenfarbe #039be5 (Light Blue 600) ist bereits kontrastreich genug fuer dunkle Hintergruende (#1e1e1e), der Tropfen braucht keine separate Anpassung. Dark-Mode-Prompt-Variante liegt oben bereit.

7. **SVG-Konvertierung — Drainagetropfen:** Der runde Tropfen ist ein einfaches `<ellipse>` oder `<path>` mit 3-4 Kontrollpunkten (typische Tropfenform: runder Koerper + spitze Unterseite). Der Glanzpunkt ist ein kleiner `<circle>` mit 20-25% weisser Flaeche oben-links im Tropfen. Gesamt-Pathcount bleibt damit im Zielbereich (<25 Pfade fuer Kami allein).

8. **Abgrenzung zu Phase 5 (Ernte, #ffa726):** Flushing hat noch keine Ernte-Signale (keine goldenen Fruechte, keine Siegerposen). Kami ist fokussiert-arbeitend, nicht feiernd. Das ist der entscheidende emotionale Unterschied, der in kleinen Groessen durch den Mundausdruck (gerade Linie statt grosses Laecheln) signalisiert wird.

---

## Nachbearbeitung

- [ ] Auf exakt 256x256px zuschneiden
- [ ] Topf-Position mit bestehenden Phasen vertikal angleichen (unteres Drittel)
- [ ] Hintergrund sauber transparent (Alpha-Kanal, kein Weiss-Artefakt an Blattkanten)
- [ ] Blattfarb-Gradient pruefen: oben gruen (#43a047), unten deutlich gelblich (#c5e1a5–#e6ee9c)
- [ ] Drainagetropfen-Farbe gegen #039be5 validieren (kein Teal, kein Cyan-Abdrift)
- [ ] Drainagetropfen-Position: exakt unten-mittig am Topfboden, nicht seitlich
- [ ] Flushing vs. Ernte verwechslungsgefahr pruefen: kein goldenes Fruchtelemet, kein Feier-Ausdruck
- [ ] Auf 64x64 skalieren: Blattgradient erkennbar (gruen oben / gelb unten)? Tropfen als blauer Punkt sichtbar?
- [ ] Auf 512x512 skalieren fuer Retina/HiDPI
- [ ] Optional: Dark-Mode-Variante mit Outlines #c8e6c9 und Tropfen #29b6f6 generieren
- [ ] Visuelle Konsistenz mit Phase 4 (Bluete) und Phase 5 (Ernte) nebeneinander pruefen
- [ ] Dateien ablegen unter: `src/frontend/src/assets/illustrations/phases/`
- [ ] Namenskonvention: `timeline-kami-phase-flushing.png` und `timeline-kami-phase-flushing.svg`
- [ ] i18n-Schluessel eintragen: `phases.flushing` in `de/translation.json` und `en/translation.json`
- [ ] Backend: FlushingProtocol (REQ-004) Phasenfarbe-Konstante auf #039be5 setzen
