# Grafik-Prompt: Kami Phasenicon — Kurztag-Induktion (Short Day Induction)

> **Typ:** Timeline-Illustration (Erweiterung der Phasen-Serie)
> **Erstellt:** 2026-04-02
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund
> **Zielgroesse:** 256x256px (primaer), skalierbar auf 64x64 und 512x512
> **Format:** PNG (transparent), SVG-tauglich
> **Einsatzort:** Phasen-Timeline in PlantInstanceDetailPage fuer Weihnachtsstern (Euphorbia pulcherrima), Poinsettia und andere Kurztag-Pflanzen; Anzeige der aktiven Verdunkelungsphase
> **Referenz:** `spec/design/timeline-kami-phasen.md` (Phasen 1–5), `spec/design/timeline-kami-phasen-erweitert.md` (Phasen 6–11), `spec/design/timeline-kami-phase-flushing.md`, `KAMI-CHARACTER-REFERENCE.md` v1.0

---

## Phasenfarbe

| Phase | Farbe | Hex | Begruendung |
|-------|-------|-----|-------------|
| Kurztag-Induktion | Tiefes Indigo-Violett | `#7e57c2` | Deep Purple 400 — dunkles, geheimnisvolles Violett das Dunkelheit und Nacht evoziert. Klar unterschiedlich von Phase 4 Bluete (`#ab47bc`, helles Magenta-Violett): `#7e57c2` ist kuehler, dunkler, blaustichiger. Evoziert Daemmerung, Nachtstunden, das Geheimnis des Lichtsteuerungsprozesses — exakt das Konzept der erzwungenen Dunkelheit zur Bluehinduktion. |

---

## Kontext

Kurztag-Induktion ist der gezielte Prozess, eine Pflanze durch kuenstlich verlaengerte Dunkelperioden (12–14 Stunden taegliche Dunkelheit) zur Bluehbereitschaft zu zwingen. Klassisches Beispiel: der Weihnachtsstern (Euphorbia pulcherrima) wird 6–8 Wochen lang taeglich unter einen lichtdichten Behaelter gestellt, um die Bluetenbildung auszuloesen. Die Pflanze "glaubt", der Winter naehe — und reagiert mit Bluetenbildung. Das ist aktive, wissende Kontrolle: Kami entscheidet, wann Nacht ist.

Biologisch: Photoperiodismus-Reaktion auf den Phytochrom-Mechanismus der Pflanze. Der Grower manipuliert das Licht-Dunkel-Verhaeltnis, um einen Kurztag (weniger als 12 Stunden Licht) zu simulieren, der die Blueteninitiierung ausloest. Die Verdunkelungsphase muss jeden Tag strikt eingehalten werden — eine einzige Lichtunterbrechung waehrend der Dunkelperiode kann den gesamten Prozess zunichte machen.

Die visuelle Komposition zeigt Kami, der mit wissendem, geheimnisvollem Ausdruck eine schwarze, lichtdichte Haube oder einen dunklen Topf ueber eine Pflanze setzt. Mond und Sterne deuten die kuenstlich erschaffene "Nacht" an. Die Stimmung ist: geheimnisvoll aber freundlich — Kami weiss genau, was er tut.

---

## Farbpalette fuer dieses Icon

| Element | Hex | Verwendung |
|---------|-----|------------|
| Phasenfarbe / Verdunkelungshaube | `#7e57c2` | Hauptfarbe der Dunkelhaube/Abdeckung |
| Haube Highlight | `#9575cd` | Helle Flaeche auf Haube (Kurvenreflexion) |
| Haube Schatten | `#512da8` | Dunkle Unterseite / Schatten der Haube |
| Mond | `#fff9c4` | Kleiner Halbmond (Mondsichel) neben der Szene |
| Sterne | `#ffe082` | 2–3 winzige vierzackige Sternpunkte |
| Pflanze unter Haube (angedeutet) | `#43a047` | Sichtbarer Blattanteil unter/neben Haube |
| Kami-Blaetter Basis | `#66bb6a` | Hauptfarbe von Kamis eigenen Blaettern |
| Kami-Blaetter Highlight | `#98ee99` | Helle Stellen nahe Blattspitze |
| Kami-Blaetter Schatten | `#2e7d32` | Dunkle Stellen nahe Stiel-Ansatz |
| Stiel | `#43a047` | Verbindung Kopf–Topf |
| Topf Basis | `#8d6e63` | Hauptfarbe Terracotta |
| Topf Dekostreifen | `#a1887f` | Hellerer Ring auf Topfmitte |
| Topf Schatten | `#6d4c41` | Unterseite, dunkle Bereiche |
| Erde (Topfrand) | `#795548` | Sichtbare Erdoberflaeche |
| Haube-Griff / Griff oben | `#6d4c41` | Kleiner Knauf oder Griff oben auf der Haube |
| Outlines | `#1b5e20` | Standard Dunkelgruen, 2.5px aussen / 1.5px innen |

---

## Emotion: SKEPTISCH / NACHDENKLICH (Skeptical / Thinking)

Aus dem Emotionskatalog (KAMI-CHARACTER-REFERENCE.md, Abschnitt 4.2):

| Kanal | Auspraegung |
|-------|-------------|
| Blaetter | Asymmetrisch (eines hoch, eines tiefer) — wissend, etwas verschmitzt |
| Augen | Asymmetrisch (eines groesser, eines kleiner/zusammengekniffen) — berechnender Ausdruck |
| Mund | Diagonale Linie ("hmm") — konzentriert, mit einem Hauch von "ich weiss genau was ich tue" |
| Arme | Ein Arm haelt die Verdunkelungshaube, anderer Arm leicht nach vorne gestreckt oder an der Huefte |

**Begruendung:** Die Kurztag-Induktion erfordert prazises Wissen und Timing. Kami ist kein Zufalls-Gaertner — er manipuliert bewusst den Lichtrhythmus. Der skeptisch-nachdenkliche Ausdruck mit dem verschmitzten Unterton ("ich weiss was ich tue, auch wenn es seltsam aussieht") passt perfekt zu einer Handlung, die nach aussen wie Sabotage aussieht, aber strategisch brillant ist. Der asymmetrische Blick erzeugt Spannung und Geheimnisvolles — exakt die Stimmung der "geheimen Dunkelheit".

**Prompt-Fragment (verbatim aus Referenz):**
```
Skeptical thinking expression: leaves asymmetric (one perked up, one at neutral
angle), eyes open and alert with one slightly higher than the other, mouth as a
small diagonal line. One arm on hip, other arm raised with index finger pointing
upward in a "we should act soon" gesture.
```

**Anpassung fuer diese Szene:** Der erhobene Arm haelt statt des zeigenden Fingers die Verdunkelungshaube. Der Ausdruck bleibt identisch — asymmetrische Blaetter, ein Auge etwas groesser, diagonaler Mund.

---

## Gemini Prompt — Light Mode

```
A cute comic-style mascot character illustration for a plant app phase timeline.
Square format, 1:1 aspect ratio.

Scene: Kami, the friendly plant-pot mascot, is carefully placing a dark dome-
shaped cover over a small plant to create an artificial night period — the
short day induction technique used to trigger flowering in photoperiod-sensitive
plants like poinsettia. The cover is a simple, rounded bell-jar or bucket shape,
smooth and lightly domed at the top with a small knob handle on top.

The dark covering dome is in deep indigo-violet (#7e57c2) — the dominant accent
color of this illustration. The dome has a lighter highlight area on its upper-
left curve (#9575cd) suggesting a smooth surface, and a darker shadow on the
lower edge and underside (#512da8). A small knob or rounded handle sits centered
on top of the dome in dark brown (#6d4c41). The dome covers a small plant
that is only slightly visible at the base — a hint of a green leaf (#43a047)
peeking out from the left or right side of the dome's lower edge, just enough
to show something living is beneath.

To the upper-right of the scene, floating freely: a small crescent moon shape
in pale cream-yellow (#fff9c4). Adjacent to the moon: 2-3 tiny four-pointed
star shapes in warm yellow (#ffe082). These are small — the moon is about
15% of the total image width. They represent the artificial "night" Kami has
created for the plant. They are flat, clean graphic shapes, not realistic.

Kami stands to the left of the dome, one arm extended forward holding or
placing the dome onto the plant below. Kami's expression is skeptical and
knowing: leaves asymmetric (one leaf pointing upward, one at a slight neutral-
downward angle), eyes open and alert with one eye slightly larger than the
other giving a sly knowing look, mouth as a small diagonal line — the
expression of someone who knows exactly what they are doing and why.

Kami body colors: leaves (#66bb6a) with highlight (#98ee99) near leaf tips and
shadow (#2e7d32) near the stem base. Stem (#43a047). Pot terracotta: base
(#8d6e63), horizontal stripe (#a1887f), shadow (#6d4c41). Soil visible at pot
top (#795548). Eyes: filled black circles with tiny white highlight dot. Mouth:
small diagonal line in dark green (#1b5e20).

Composition: Kami occupies the left 40% of the image, the dome-covered plant
occupies the right 45%, with generous 12% padding on all sides. Both figures
share the same ground baseline at the lower third. The moon and stars float
in the upper-right quadrant of negative space. The dome is slightly taller
than Kami's total height.

All outlines: dark green (#1b5e20), 2.5px for outer character edges, 1.5px for
inner detail lines, rounded line caps and joins throughout.

Style: flat vector illustration, cute cartoon, kawaii-influenced but
professional. Flat solid color fills with subtle soft inner shading (10–15%
darker near form edges for shape definition). No gradients, no textures,
no fine patterns. Clean geometric shapes suitable for SVG conversion.

Transparent background (PNG with alpha channel). No background elements,
no floor, no drop shadows outside character boundaries.
No text, no numbers, no labels anywhere in the image.

Avoid: photorealism, 3D rendering, gradient fills, black outlines (use dark
green #1b5e20 instead), hard drop shadows, complex backgrounds, text or
letters, watermarks, clip-art style, childish infantile cartoon style, elements
smaller than 3px, anti-aliasing artifacts, more than 10 distinct colors total.
```

---

## Gemini Prompt — Dark Mode

```
A cute comic-style mascot character illustration for a plant app phase timeline,
designed for display on a dark background (#1e1e1e). Square format, 1:1 aspect ratio.

Scene: Kami, the friendly plant-pot mascot, is carefully placing a dark dome-
shaped cover over a small plant to create an artificial night period — the
short day induction technique used to trigger flowering in photoperiod-sensitive
plants like poinsettia.

The dark covering dome is in deep indigo-violet (#7e57c2) — the dominant accent
color. The dome has a lighter highlight area on its upper-left curve (#9575cd),
and a darker shadow on the lower edge (#512da8). A small knob handle sits
centered on top in dark brown (#6d4c41). A hint of a green leaf (#66bb6a)
peeks out from the base of the dome on one side. Because the illustration
appears on a dark background, the dome outline must be clearly visible —
use light indigo (#9575cd) as the outer outline for the dome specifically,
while all other outlines remain light green (#c8e6c9).

To the upper-right of the scene, floating freely: a small crescent moon in
pale yellow (#fff9c4), and 2–3 tiny four-pointed stars in warm yellow (#ffe082).
These glow softly against the dark background — the moon is about 15% of the
total image width, clean flat shapes.

Kami stands to the left of the dome, one arm extended forward placing the
dome over the plant. Kami's expression is skeptical and knowing: leaves
asymmetric (one leaf pointing upward, one at a neutral angle), eyes open and
alert with one slightly larger than the other for a sly knowing look, mouth
as a small diagonal line.

Kami body colors for dark mode: leaves (#66bb6a) with brighter highlights
(#98ee99) near leaf tips — slightly more vivid than light mode to maintain
visual impact on dark backgrounds — and shadow (#338a3e) near stem base.
Stem (#66bb6a). Pot terracotta: base (#8d6e63), stripe (#a1887f), shadow
(#6d4c41). Soil (#795548). Eyes: filled black circles with white highlight dot.
Mouth: small diagonal line.

Composition: Kami occupies the left 40%, dome-covered plant the right 45%,
generous 12% padding. Shared ground baseline at the lower third. Moon and
stars float in upper-right negative space. Dome is slightly taller than Kami.

All outlines: light green (#c8e6c9) for dark mode, 2.5px outer edges, 1.5px
inner detail lines, rounded line caps and joins throughout. Exception: dome
outer outline in light indigo (#9575cd) to maintain contrast against dark bg.

Style: flat vector illustration, cute cartoon, kawaii-influenced but
professional. Flat solid color fills with subtle soft inner shading. No
gradients, no textures, no fine patterns. Clean shapes for SVG conversion.

Transparent background (PNG with alpha channel). No background elements,
no drop shadows outside character boundaries.
No text, no numbers, no labels anywhere in the image.

Avoid: photorealism, 3D rendering, gradient fills, hard drop shadows, complex
backgrounds, text or letters, watermarks, clip-art style, childish infantile
cartoon style, elements smaller than 3px, anti-aliasing artifacts, more than
10 distinct colors total.
```

---

## Variationen

### Variante A: Kami haelt Haube ueber Pflanze (Vogelperspektive-Andeutung)

Wenn der Arm-Haube-Arm schwierig zu generieren ist, alternativ: Kami steht
direkt neben dem bereits aufgestellten Dom, ein Arm ruht auf der Haube (wie
ein Schild-Beschuetzer), der andere Arm an der Huefte. Gleiche Emotion.

```
A cute comic-style mascot character illustration for a plant app phase timeline.
A plant in the short day induction phase — the deliberate daily darkness period
used to trigger flowering. Scene: Kami stands next to a dome-shaped dark cover
already placed over a small plant. One of Kami's thin stick-arms rests lightly
on top of the dome in a protective guardian pose. The other arm is on the hip
in a knowing stance.

The dome is in deep indigo-violet (#7e57c2) with highlight (#9575cd) on upper
left and shadow (#512da8) on lower edges. Small brown knob on top (#6d4c41).
A tiny green leaf hint (#43a047) peeks out at the dome's base.

Upper-right negative space: a crescent moon (#fff9c4) and 2 small four-pointed
stars (#ffe082) floating freely.

Kami expression — skeptical knowing: leaves asymmetric (one pointing up, one
at neutral angle), eyes open with one slightly larger for a sly look, mouth a
small diagonal line. Kami body: leaves (#66bb6a), highlights (#98ee99),
shadows (#2e7d32), stem (#43a047). Pot: base (#8d6e63), stripe (#a1887f),
shadow (#6d4c41), soil (#795548). Outlines (#1b5e20) 2.5px outer, 1.5px inner.

Style: flat vector illustration, cute cartoon, professional kawaii. Flat solid
fills, subtle soft shading at form edges. No gradients, no textures.
Centered composition, square 1:1, 12% padding. Transparent background.
No text, no labels.
Avoid: photorealism, gradients, 3D, black outlines, hard shadows, text,
elements under 3px.
```

### Variante B: Minimale Version (fuer 64x64 Badge-Einsatz)

Stark vereinfacht. Nur Topf mit Gesicht, Haube daneben, Mond oben.

```
A cute simple mascot icon for a plant phase badge.
A small plant-pot character with a friendly face stands next to a dark dome-
shaped cover. The dome is in deep indigo-violet (#7e57c2) with a small round
knob on top (#6d4c41). The pot has a simple asymmetric leaf arrangement (one
leaf higher than the other) and a diagonal-line mouth for a knowing expression.
In the upper corner: a tiny crescent moon shape (#fff9c4) and one star (#ffe082).
No arms in this simplified version. No text, no labels.

Dome: (#7e57c2) main, (#9575cd) highlight, (#512da8) shadow.
Pot: base (#8d6e63), stripe (#a1887f), shadow (#6d4c41), soil (#795548).
Leaves: (#66bb6a) flat, no inner shading.
Outlines: (#1b5e20) uniform 2px, rounded.

Style: flat vector icon, minimal cartoon, clean geometric shapes.
Square format, 10% padding, transparent background.
Avoid: gradients, complex details, photorealism, elements under 3px.
```

---

## Visuelle Beschreibung

```
Kurztag-Induktion — Short Day Induction:
Kami weiss was er tut. Mit einem verschmitzten, leicht asymmetrischen Ausdruck
setzt er eine lichtdichte Haube in tiefem Indigo-Violett (#7e57c2) ueber eine
Pflanze — und erschafft damit kuenstliche Nacht. Die Haube ist der bildliche
Mittelpunkt: ein klarer, einfacher Dom mit kleinem Griff oben, unter dem
das gruenem Blatt gerade noch lugt.

Oben rechts, im Freiraum: ein zarter Halbmond (#fff9c4) und zwei Sternpunkte
(#ffe082) — die "Nacht" die Kami erschafft. Nicht dramatisch gross, aber klar
lesbar. Sie erklaeren das Konzept ohne Text.

Das Gesicht auf Kamis Topf zeigt den skeptisch-wissenden Ausdruck:
asymmetrische Blaetter (eines hoch, eines neutral), ein Auge etwas groesser
als das andere, Mund als diagonale Linie. Dieser Ausdruck sagt: "Ich weiss
genau, was ich hier tue — auch wenn es seltsam aussieht."

Gesamteindruck: Kontrolle, Geheimnis, Praezision. Keine Angst, kein Stress.
Kamis Haltung strahlt aus: "Das ist Absicht. Vertrau mir."

Serienposition: Spezialphase fuer Kurztag-Pflanzen (Weihnachtsstern,
Kalanchoe, Chrysantheme) zwischen Vegetativ und Bluete. Ordnet sich farblich
mit #7e57c2 eindeutig zwischen Phase 3 Vegetativ (#2e7d32, dunkelgruen) und
Phase 4 Bluete (#ab47bc, Magenta-Violett) ein — alle drei klar unterscheidbar.
```

---

## Einordnung in die Phasen-Bibliothek

```
Farb-Kollisionscheck Short Day Induction (#7e57c2) gegen alle bestehenden Phasen:

  #7e57c2 (ShortDay)  vs. #a5d6a7 (Keimung)      — Pastell-Mintgruen, kein Konflikt
  #7e57c2 (ShortDay)  vs. #66bb6a (Saemling)      — Fruehlings-Gruen, kein Konflikt
  #7e57c2 (ShortDay)  vs. #2e7d32 (Vegetativ)     — Dunkelgruen, kein Konflikt
  #7e57c2 (ShortDay)  vs. #ab47bc (Bluete)         — #ab47bc ist Magenta-Violett, heller und
                                                      pinker. #7e57c2 ist deutlich kuehler/blaustichiger
                                                      Indigo. Unterschied: ~40 Grad Farbton + 25%
                                                      Helligkeits-Delta. Ausreichend verschieden.
  #7e57c2 (ShortDay)  vs. #ffa726 (Ernte)          — Goldgelb, kein Konflikt
  #7e57c2 (ShortDay)  vs. #e65100 (Ripening)       — Tiefes Orange, kein Konflikt
  #7e57c2 (ShortDay)  vs. #26a69a (Juvenil)        — Frisches Teal, kein Konflikt
  #7e57c2 (ShortDay)  vs. #004d40 (Klettern)       — Fast schwarz-teal, kein Konflikt
  #7e57c2 (ShortDay)  vs. #33691e (Reife)          — Waldgruen, kein Konflikt
  #7e57c2 (ShortDay)  vs. #78909c (Dormanz)        — Blau-Grau, aehnliche Helligkeit aber
                                                      klar anderer Farbton (Grau vs. Violett)
  #7e57c2 (ShortDay)  vs. #d4a056 (Seneszenz)      — Ocker-Gold, kein Konflikt
  #7e57c2 (ShortDay)  vs. #039be5 (Flushing)       — Sattes Blau, kein Konflikt
  => Grenzfall Bluete (#ab47bc): visuell ausreichend unterschiedlich durch
     Farbton-Shift (Magenta vs. Indigo) und Helligkeits-Delta.
     Grenzfall Dormanz (#78909c): unterschiedlicher Farbton (Violett vs. Grau).

Erweiterter Phasen-Ueberblick mit Short Day Induction:

  Kern-Phasen:
  Keimung      Saemling     Vegetativ    Bluete       Ernte
  #a5d6a7      #66bb6a      #2e7d32      #ab47bc      #ffa726

  Erweiterte Phasen:
  Ripening     Juvenil      Klettern     Reife        Dormanz      Seneszenz    Flushing
  #e65100      #26a69a      #004d40      #33691e      #78909c      #d4a056      #039be5

  Spezial-Phasen:
  ShortDay     [leaf_phase]
  #7e57c2      #81c784
```

---

## Technische Hinweise

1. **Haube als Hauptelement:** Die Verdunkelungshaube ist bildlich wichtiger als die Pflanze darunter. Sie muss klar als lichtdichte Abdeckung lesbar sein — ein einfacher, halbrunder Dom mit glattem Profil. Kein Gitterwerk, keine Luftloecher, keine Transparenz. Die geschlossene, undurchdringliche Form ist das Konzept.

2. **Mondgroesse bewusst klein halten:** Mond und Sterne sind erklaerende Akzente, keine Hauptmotive. Bei 256px sollte der Mond etwa 35–40px Breite haben. Bei 64px kann der Mond auf einen einzelnen hellen Punkt oder Sichel-Strich vereinfacht werden.

3. **Abgrenzung zu Phase 4 (Bluete, #ab47bc):** Beide sind violett, aber Short Day hat kein Bluetenzeichen (keine Bluetenblaetter, keine Staubgefaesse). Das Konzept ist die VORBEREITUNG auf die Bluete, nicht die Bluete selbst. Kami zeigt Konzentration/Wissen, nicht die Friedlichkeit der Bluete-Phase.

4. **SVG-Konvertierung — Haube:** Die Haube ist ideal fuer vtracer: ein einfaches `<path>` fuer den Haubenkoerper (halbrunder Bogen + gerade Unterkante), ein `<rect>` fuer den Griff. Maximal 3 Pfade fuer die gesamte Haube. Der Glanzpunkt ist eine kleine helle Ellipse (#9575cd) im oberen Drittel der Haube.

5. **Phasenfarbe #7e57c2 als Badge-Hintergrund:** Im UI auf hellem Text (#ffffff) pruefen — WCAG AA bei 16px Schrift ausreichend (Kontrastverhaltnis ca. 4.8:1). Bei Dark-Mode-Badges dark text (#1e1e1e) verwenden.

6. **Arm-Pose-Fallback:** Wenn die KI die Arm-Haube-Interaktion nicht sauber generiert, ist Variante A (Arm auf Haube liegend) einfacher zu regenerieren. Die Emotion bleibt identisch.

7. **Konsistenz-Check Emotion:** Der "skeptisch-wissende" Ausdruck mit asymmetrischen Blaettern und diagonalem Mund ist auch bei anderen Icons der Serie — bei diesem Icon ist er korrekt eingesetzt, da Kami hier eine ungewoehnliche, aber wissentliche Handlung ausfuehrt.

---

## Nachbearbeitung

- [ ] Auf exakt 256x256px zuschneiden
- [ ] Topf-Position mit bestehenden Phasen vertikal angleichen (unteres Drittel)
- [ ] Hintergrund sauber transparent (Alpha-Kanal, kein Weiss-Artefakt an Blattkanten)
- [ ] Haubenfarbe gegen #7e57c2 validieren (kein Pink-Drift Richtung #ab47bc)
- [ ] Mond-Farbe gegen #fff9c4 validieren (nicht weiss, nicht gelb — zart cremig-gelb)
- [ ] Emotionsausdruck pruefen: Blaetter asymmetrisch? Mund als diagonale Linie?
- [ ] Auf 64x64 skalieren: Haube erkennbar? Mond als Punkt lesbar?
- [ ] Auf 512x512 skalieren fuer Retina/HiDPI
- [ ] Farb-Kollision gegen Phase 4 (Bluete) im direkten Nebeneinander-Vergleich pruefen
- [ ] Dateien ablegen unter: `src/frontend/src/assets/brand/illustrations/phases/`
- [ ] Namenskonvention: `timeline-kami-phase-short-day-induction.png` + `.svg`
- [ ] i18n-Schluessel eintragen: `phases.short_day_induction` in `de/translation.json` und `en/translation.json`
