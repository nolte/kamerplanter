# Grafik-Prompts: Kami Phasen-Zeitstrahl (Erweiterung)

> **Typ:** Timeline-Illustrationen (Serie von 6, Erweiterung der bestehenden 5er-Serie)
> **Erstellt:** 2026-03-06
> **Varianten:** Light (primaer), Dark-Mode-tauglich durch transparenten Hintergrund
> **Zielgroesse:** 256x256px (primaer), skalierbar auf 64x64 und 512x512
> **Format:** PNG (transparent), SVG-tauglich
> **Einsatzort:** Phasen-Timeline in PlantInstanceDetailPage, Pflegeprofil-Badges, Dormanz-Anzeige, Zimmer- und Klettergewaeches-Profile, Seneszenz-Anzeige fuer annuelle Lebensende-Phase
> **Referenz:** `spec/ref/graphic-prompts/timeline-kami-phasen.md` (Phasen 1–5), Design Guide Abschnitt 2.2 (Phasenfarben), REQ-003 (Phasensteuerung), REQ-022 (Pflegeerinnerungen)

---

## Kontext

Diese Datei erweitert die bestehende 5er-Serie (Phasen 1–5 in `timeline-kami-phasen.md`) um sechs
zusaetzliche Wachstumszustaende. Die neuen Phasen decken Lebenszyklen ab, die in der Basisreihe nicht
adressiert wurden: die Nachreife zwischen Bluete und Ernte (Phase 6), die Jungpflanzenphase zwischen
Saemling und Vegetativ (Phase 7), die Kletterphase fuer Lianen und Rankpflanzen (Phase 8), den Zustand
der voll ausgereiften Dauerkultur ohne Fruchtbildung (Phase 9), die Winterruhe/Dormanz (Phase 10),
und der irreversible Alterungsprozess am Lebensende einer Pflanze: Seneszenz (Phase 11).

Alle elf Illustrationen sollen zusammen eine lueckenlose Phasen-Bibliothek ergeben. Nicht jede Pflanze
durchlaeuft alle elf Phasen — der Anwender waehlt im Lifecycle-Profil die relevante Teilmenge.
Die Bilder werden daher sowohl einzeln als auch in verschiedenen Teilreihen kombiniert eingesetzt.

**Wichtig:** Kami waechst NICHT linear ueber alle elf Bilder hinweg. Jede Phase zeigt einen
eigenstaendigen, in sich abgeschlossenen Zustand. Die optische Verbindung entsteht ausschliesslich
durch den identischen Topf, die identische Komposition und den identischen Illustrationsstil.

---

## Gemeinsame Stilregeln fuer alle Phasen 6–11

Alle stilistischen Regeln — Outline-Staerke, Topffarben, Gesichtskonstruktion, Arm-Positionen,
Flat-Vector-Stil, Kawaii-Einfluss, Kompositionsregeln — sind in der Originaldatei vollstaendig
dokumentiert.

Siehe: `spec/ref/graphic-prompts/timeline-kami-phasen.md`, Abschnitt "Gemeinsame Stilregeln"

Die folgenden Prompts integrieren alle Stilregeln vollstaendig und sind copy-paste-fertig.

---

## Phase 6: Ripening (Nachreife/Fruchtreifung)

> **Phasenfarbe:** `#e65100` Tiefes Bernstein-Orange (Deep Orange 900)
> **Dateiname:** `timeline-kami-phase-ripening.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A plant in a terracotta pot in the ripening phase — fruits are changing color
from green to deep amber-orange, caught mid-transition. The plant has a few
sturdy green leaves and 3-4 fruits in different stages of ripening: one still
green, two turning orange-amber (#e65100) with lighter orange highlights
(#ff8f00), and one fully ripened in deep amber-orange (#e65100). The fruits
are round and plump, hanging from short stems. The pot has a patient,
watchful face — eyes focused and slightly narrowed in concentration, as if
carefully observing the ripening. One arm raised slightly with a tiny magnifying
glass gesture (index finger and thumb forming a circle), the other arm relaxed
at the side.

Fruit colors: deep amber-orange (#e65100) for ripe, (#ff8f00) for transition,
medium green (#66bb6a) for unripe. Fruit highlights: (#ff8f00) on ripe fruit.
Leaves: medium green (#43a047), a few darker (#2e7d32). Stem (#43a047).
Soil in pot (#795548). Pot terracotta: base (#8d6e63), stripe (#a1887f),
shadow (#6d4c41). All outlines dark green (#1b5e20), 2-3px uniform weight,
rounded ends. Face detail lines thinner.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading for depth. No gradients.
Centered composition, square format, generous padding.
Transparent background, no shadows outside the character.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 6 — Ripening:
Kami beobachtet geduldig den Reifeprozess. Drei bis vier Fruechte haengen an
der Pflanze in verschiedenen Reifestadien — eine noch gruen (#66bb6a), zwei
im Uebergang und eine bereits voll ausgereift in tiefem Bernstein-Orange
(#e65100). Das Gesicht zeigt konzentrierte Aufmerksamkeit, die Augen leicht
zusammengekniffen — ein aufmerksamer Beobachter. Ein Arm ist leicht angehoben
in einer pruefenden Geste, der andere haengt entspannt.
Gesamteindruck: Geduld, Aufmerksamkeit, Spannung des Wartens, bald-fertig.
```

---

## Phase 7: Juvenil (Jungpflanzenphase)

> **Phasenfarbe:** `#26a69a` Frisches Teal-Gruen (Teal 600)
> **Dateiname:** `timeline-kami-phase-juvenile.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A juvenile plant growing from a terracotta pot — past the seedling stage but
not yet fully mature. The plant has a slender upright stem with 3-4 small
leaves that are clearly the characteristic leaf shape of the species (longer
and more defined than round cotyledons, with slight serration or lobing), but
still small and proportionally large for the stem. One leaf is slightly larger
than the others, showing uneven natural juvenile growth. The plant leans very
slightly to one side — not wilting, just the natural asymmetry of young growth.
The pot has a curious, slightly wide-eyed face with big round dot eyes and a
small open-mouthed expression of wonder, tilted slightly to one side to match
the plant's lean. Arms are slightly awkward — one reaching out toward a leaf
with curiosity, the other bent at a quirky angle.

Leaves: teal-green (#26a69a) with lighter highlights (#80cbc4), darker areas
(#00796b). Stem (#43a047) medium green. Soil (#795548). Pot terracotta: base
(#8d6e63), stripe (#a1887f), shadow (#6d4c41). Outlines dark green (#1b5e20),
2-3px uniform, rounded. Face uses thinner detail lines.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 7 — Juvenil:
Kami ist nicht mehr Saemling aber noch kein Erwachsener. Drei bis vier
charakteristisch geformte Blaetter in Teal-Gruen (#26a69a), definitiv groesser
und definierter als Keimblaetter, aber noch klein und etwas ungleichmaessig
gewachsen. Die Pflanze neigt sich leicht zur Seite — jugendliche Unbeholfenheit.
Das Gesicht spiegelt das: Augen weit aufgerissen vor Neugier, Mund leicht
geoeffnet, der Kopf (Topf) auch ein bisschen seitlich geneigt. Die Arme
wirken ein wenig unkoordiniert — einer streckt sich neugierig zu einem Blatt.
Gesamteindruck: Neugier, Abenteuergeist, Unbekultiviertheit, junges Erkunden.
```

---

## Phase 8: Kletterphase (Climbing/Vining)

> **Phasenfarbe:** `#004d40` Tiefes Teal-Dunkelgruen (Teal 900)
> **Dateiname:** `timeline-kami-phase-climbing.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A climbing vining plant growing from a terracotta pot with a small moss pole
or support stake inside the pot. The plant has 2-3 long trailing stems that
wind upward, wrapping around the support stake with visible tendril curls.
The leaves are medium-sized heart-shaped or tropical leaves in two or three
pairs along the climbing stems. One or two small aerial roots are visible
hanging from a stem node. The tip of the tallest stem reaches toward the
upper edge of the image with clear upward momentum. The pot has a determined,
motivated face with firm focused eyes and a resolved small smile — looking
upward. Both stick-arms are reaching upward in a climbing gesture, like a
person scaling a wall.

Leaves: deep teal-green (#004d40) main color, lighter highlights (#26a69a),
inner vein lines in (#00695c). Stems: dark green (#1b5e20). Aerial roots:
light brown-beige (#bcaaa4). Support stake: light brown (#a1887f). Tendril
curls: dark green (#1b5e20), thin lines. Soil (#795548). Pot terracotta: base
(#8d6e63), stripe (#a1887f), shadow (#6d4c41). Outlines dark green (#1b5e20),
2-3px uniform, rounded.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 8 — Kletterphase:
Kami strebt nach oben! Ein Moosstab oder Rankstab steht im Topf, um den sich
lange Kletterstiele winden — mit sichtbaren Rankenspiralen und kleinen
herzfoermigen Blaettern in tiefem Teal-Dunkelgruen (#004d40). Ein oder zwei
kleine Luftwurzeln haengen von einem Stielknoten herab. Der Stiel-Tipp zeigt
entschlossen nach oben, fast aus dem Bild hinaus. Das Gesicht ist fokussiert
und entschlossen — Blick nach oben gerichtet. Beide Arme greifen nach oben
wie jemand der klettert.
Gesamteindruck: Entschlossenheit, Aufwaertsstreben, aktives Wachstum, Expansion.
```

---

## Phase 9: Reife Pflanze (Mature Plant)

> **Phasenfarbe:** `#33691e` Tiefes Waldgruen (Light Green 900)
> **Dateiname:** `timeline-kami-phase-mature.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A fully mature, lush established plant in a terracotta pot — the plant is at
its peak non-flowering beauty. The plant has 7-9 leaves of clearly different
sizes: 3 large wide leaves at the lower level, 3 medium leaves in the middle
tier, and 2-3 smaller leaves at the top. At least one leaf has a tropical
split or fenestration pattern (like a monstera leaf with one or two elongated
oval holes in it) to suggest a mature tropical houseplant character. The
composition is full and balanced, almost perfectly symmetrical, radiating from
the central stem. The pot has a contented, serene face with gently closed or
half-closed eyes and a small peaceful smile — the expression of deep satisfaction
and wisdom. Arms are relaxed and open, spread outward in a calm welcoming
gesture, like a wise tree opening its branches.

Leaves: dominant deep forest green (#33691e), medium leaves (#558b2f), young
top leaves (#7cb342), fenestration holes are transparent or show the pale
background through them. Stem (#43a047). Soil (#795548). Pot terracotta: base
(#8d6e63), stripe (#a1887f), shadow (#6d4c41). Outlines dark green (#1b5e20),
2-3px uniform, rounded.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 9 — Reife Pflanze:
Kami ist erwachsen und souveraen. Eine vollausgebildete, symmetrische Pflanze
mit neun Blaettern in drei Groessenebenen — tiefes Waldgruen (#33691e) dominiert.
Mindestens ein Blatt zeigt Fenestration (Monstera-artige Schlitze), die die
Reife der Pflanze symbolisieren. Die Komposition ist voll und ausgewogen.
Das Gesicht zeigt ruhige Zufriedenheit — halb geschlossene Augen, weises
Laecheln, Arme weit und offen wie ein alter Baum der seine Aeste ausbreitet.
Gesamteindruck: Souveraenitaet, Weisheit, stabile Schoenheit, Hoehepunkt ohne
Fruchtbildung.
```

---

## Phase 10: Dormanz (Dormancy)

> **Phasenfarbe:** `#78909c` Gedaempftes Blau-Grau (Blue Grey 400)
> **Dateiname:** `timeline-kami-phase-dormancy.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A dormant plant in a terracotta pot during its winter rest phase. The plant
above soil is reduced to 1-2 bare woody sticks or dried stems — no leaves,
just the skeletal structure. At the base of one stick, almost invisible, is
a tiny bright green bud (a small teardrop shape in #66bb6a) — the promise of
next season, just barely visible. The pot wears a tiny sleeping cap (a small
pointed hat with a fluffy pompom, in muted blue-gray #78909c with a white
pompom) tilted to one side. The pot's face has peacefully closed eyes — simple
curved lines like closed arcs — and a very small content sleeping smile. Both
arms hang completely limp and relaxed at the sides, drooping slightly downward,
as if totally at rest.

Bare stems: gray-brown (#8d6e63), pale brown (#a1887f). Tiny future bud:
bright spring green (#66bb6a). Sleeping cap: blue-gray (#78909c), white pompom
(#f5f5f5), cap outline dark green (#1b5e20). Soil (#795548). Pot terracotta:
base (#8d6e63), stripe (#a1887f), shadow (#6d4c41). Outlines dark green
(#1b5e20), 2-3px uniform, rounded.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading. No gradients.
Centered, square format, generous padding, transparent background.
No shadows outside the character. No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 10 — Dormanz:
Kami schlaeft. Keine Blaetter, nur ein oder zwei kahle, braun-graue Stiele
ragen aus der Erde. An der Basis eines Stiels versteckt sich eine winzig
kleine gruene Knospe (#66bb6a) — kaum zu sehen, aber vorhanden: das Versprechen
des naechsten Zyklus. Auf dem Topf sitzt eine kleine Schlafmuetze in
Blau-Grau (#78909c) mit weissem Bommel, schief aufgesetzt. Das Gesicht zeigt
friedlich geschlossene Augen (Bogenlinien) und ein entspanntes Mini-Laecheln.
Die Arme haengen schlaff und vollig entspannt an den Seiten herab.
Gesamteindruck: Winterruhe, Stille, Erneuerung kuendigt sich an, friedlicher Schlaf.
```

---

## Phase 11: Seneszenz (Senescence)

> **Phasenfarbe:** `#d4a056` Warmes Herbstgold-Ocker (gedaempftes Amber)
> **Dateiname:** `timeline-kami-phase-senescence.png`

### Prompt

```
A cute comic-style mascot character illustration for a plant app timeline.
A plant in its natural senescence phase — the irreversible end-of-life aging
process — growing from a terracotta pot. The plant has a slender upright stem
with 5-6 leaves in various stages of autumn color change: one or two leaves
are still half-green transitioning to yellow, two or three leaves are fully
turned in warm golden-amber (#d4a056) and rusty orange-brown (#bf8040), and
one leaf at the very tip is a deeper dried brown (#a0522d). Two leaves are
gently detaching — one hangs from the stem at a steep diagonal angle, barely
attached, the other floats freely just beside the plant in mid-fall, not yet
touching the soil. At the base of the stem, a single small dried seed capsule
or dried seedhead hangs — a round, closed pod in pale straw-brown (#c8a96e),
symbolizing the return of nutrients to seed. The plant is still upright, not
drooping dramatically, but visibly less full and vital than the vegetative phase.

The pot's face carries a calm, dignified expression: eyes are gently half-closed
in a soft accepting gaze — not sad, not alarmed — the quiet wisdom of a life
well-lived. The mouth forms a small, serene and faintly knowing smile, the
corners barely upturned. Both arms rest gently at the sides, slightly angled
outward and downward in an open, surrendering posture — neither limp like
dormancy, nor raised like harvest: a quiet, composed stillness.

Leaf colors: warm golden-amber (#d4a056) dominant, rusty orange-brown (#bf8040)
for deeper tones, a few half-green (#8aab5a) transitioning leaves, dried brown
tip (#a0522d) for the oldest leaf. Fallen/falling leaf: golden-amber (#d4a056).
Dried seed capsule: straw-brown (#c8a96e), outline dark green (#1b5e20).
Stem: medium brown-green (#6d8b3a), slightly more muted than the vibrant green
of vegetative phases. Soil in pot (#795548). Pot terracotta: base (#8d6e63),
stripe (#a1887f), shadow (#6d4c41). All outlines dark green (#1b5e20), 2-3px
uniform weight, rounded ends. Face detail lines thinner.

Style: flat vector illustration, cute cartoon, kawaii-influenced but professional.
Flat color fills with subtle soft inner shading for depth. No gradients.
Centered composition, square format, generous padding.
Transparent background, no shadows outside the character.
No text, no labels, no background elements.
```

### Visuelle Beschreibung

```
Phase 11 — Seneszenz:
Kami altert wuerdevoll. Fuenf bis sechs Blaetter in herbstlichen Verfaerbungs-
stadien bedecken den Stiel — von halb-gruen ueber warmes Goldocker (#d4a056)
und rostiges Braun-Orange (#bf8040) bis hin zu einem getrockneten Blatt an
der Spitze (#a0522d). Zwei Blaetter loesen sich gerade: eines haengt noch
schief am Stiel, das andere schwebt frei in der Luft neben der Pflanze —
noch im Fall begriffen, noch nicht am Boden. Am Stielansatz haengt eine
einzelne kleine getrocknete Samenkapsel (#c8a96e), die den Naehrstoffrueckzug
in den Samen symbolisiert. Die Pflanze steht noch aufrecht, wirkt aber weniger
voll als in der Vegetativphase.

Das Gesicht auf dem Topf: halb geschlossene Augen in ruhigem, akzeptierendem
Blick — weder traurig noch alarmiert. Der Mund formt ein kleines, weises,
leicht wissend anmutendes Laecheln. Beide Arme haengen sanft nach unten und
leicht auswaerts — offen, gelassen, eine stille Haltung des Loslassens.
NICHT schlaff wie Dormanz, NICHT triumphierend wie Ernte: eine ruhige Wuerde.

Gesamteindruck: Herbstliche Schoenheit, natuerlicher Kreislauf, Vergaenglichkeit
mit Wuerde, das gelassene Ende eines erfuellten Pflanzenlebens.
```

---

## Gesamtuebersicht: Vollstaendiger Zeitstrahl (alle 11 Phasen)

```
  Phase 1        Phase 2        Phase 3        Phase 4        Phase 5
  Keimung        Saemling       Vegetativ      Bluete         Ernte
  #a5d6a7        #66bb6a        #2e7d32        #ab47bc        #ffa726

  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
  │  tiny  │    │ small  │    │ bushy  │    │flowers │    │ fruits │
  │ sprout │    │seedling│    │ plant  │    │& buds  │    │& leave │
  │        │    │        │    │        │    │        │    │        │
  │  ◉ ◉  │    │  ◉ ◉  │    │  ◉ ◉  │    │  ◡ ◡  │    │  ◉ ◉  │
  │   ◡   │    │   ◡   │    │   ◡   │    │   ◡   │    │   ◡   │
  │  ═══  │    │  ═══  │    │  ═══  │    │  ═══  │    │  ═══  │
  └────────┘    └────────┘    └────────┘    └────────┘    └────────┘
  neugierig     stolz         energisch     friedlich     feiernd

  Phase 6        Phase 7        Phase 8        Phase 9        Phase 10
  Ripening       Juvenil        Klettern       Reife          Dormanz
  #e65100        #26a69a        #004d40        #33691e        #78909c

  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
  │ mixed  │    │ small  │    │vining  │    │ full   │    │  bare  │
  │ fruits │    │ lean.  │    │climbing│    │ lush   │    │ sticks │
  │ ripen. │    │        │    │ stake  │    │monstera│    │  zzz   │
  │  - ◡ -│    │  ◉ ◉  │    │  ◉ ◉  │    │  ◡ ◡  │    │  ◡ ◡  │
  │   ◡   │    │   O   │    │   ◡   │    │   ◡   │    │  (hat) │
  │  ═══  │    │  ═══  │    │  ═══  │    │  ═══  │    │  ═══  │
  └────────┘    └────────┘    └────────┘    └────────┘    └────────┘
  geduldig      neugierig     entschlossen  souveraen     schlafend

  Phase 11
  Seneszenz
  #d4a056

  ┌────────┐
  │autumn  │
  │leaves  │
  │falling │
  │  ◡ ◡  │
  │   ◡   │
  │  ═══  │
  └────────┘
  wuerdevoll

  Farb-Kollisionscheck (alle Phasen gegen alle):
  #e65100 (Ripening)   vs. #ffa726 (Harvest)   — beide orange, aber e65100 deutl. dunkler/roeter
  #26a69a (Juvenil)    vs. #66bb6a (Seedling)  — teal vs. gruen, klar unterscheidbar
  #004d40 (Climbing)   vs. #2e7d32 (Vegetativ) — beides dunkelgruen, aber teal-stich vs. reines gruen
  #33691e (Mature)     vs. #2e7d32 (Vegetativ) — beide waldgruen, Mature ist etwas heller/gelblicher
  #78909c (Dormanz)    vs. alle                — einziger grauer Farbton, eindeutig unterscheidbar
  #d4a056 (Seneszenz)  vs. #ffa726 (Harvest)   — beide gold-orange; Harvest ist heller/gesaettigter,
                                                  Seneszenz ist gedaempfter/erdiger — klar unterscheidbar
  #d4a056 (Seneszenz)  vs. #e65100 (Ripening)  — Ripening ist dunkelrot-orange, Seneszenz ist
                                                  warm-ocker/gold — visuell klar getrennt
  #d4a056 (Seneszenz)  vs. #8d6e63 (Topffarbe) — Aehnliche Braun-Familie! In der UI die
                                                  Phasen-Bezeichnung als Text begleiten.
                                                  Im Bild selbst kein Problem (Farbe ist am Blatt,
                                                  nicht am Topf). Als Badge-Farbe auf helles
                                                  #d4a056 vs. Topf-Kontext achten.
```

---

## Kombinations-Prompt (alle 6 neuen Phasen in einem Bild)

Falls der Generator konsistentere Ergebnisse liefert wenn alle 6 neuen Phasen in einem Bild
erzeugt und anschliessend in Einzelbilder zugeschnitten werden:

```
Six stages of the same cute comic plant mascot character, each growing in
identical terracotta pots, arranged in a horizontal row from left to right.
Each pot has a friendly face with dot eyes and a small mouth. The character
is an anthropomorphic plant pot mascot. All pots identical in size and shape:
terracotta base (#8d6e63), lighter decorative stripe (#a1887f), shadow areas
(#6d4c41), visible soil (#795548). Dark green outlines (#1b5e20) throughout,
2-3px uniform weight, rounded ends. Flat vector illustration, cute cartoon
style, flat color fills with subtle soft inner shading, no gradients.
Transparent background. No text, no labels. Aspect ratio 6:1 (wide horizontal).

(6) RIPENING: Plant with 3-4 fruits in different ripening stages — one green
(#66bb6a), two transitioning, one ripe deep amber-orange (#e65100). Patient
watchful face, eyes slightly narrowed in focused observation. One arm in
a gentle examining gesture, the other relaxed.

(7) JUVENILE: Slender plant with 3-4 characteristic-shaped leaves in teal-green
(#26a69a) — clearly not cotyledons, but still small and slightly asymmetrical.
Plant leans slightly to one side. Face wide-eyed with wonder, slightly tilted,
one arm reaching out curiously toward a leaf.

(8) CLIMBING: Plant with long vining stems winding around a small support stake
inside the pot. Heart-shaped leaves in deep teal (#004d40) along the climbing
stems. Small aerial roots visible at stem nodes. Plant tip reaching upward.
Face determined and focused, looking up, both arms reaching upward.

(9) MATURE: Full lush plant with 7-9 leaves in three tiers of size, deep forest
green (#33691e). At least one leaf has a monstera-style fenestration (oval
holes). Symmetrical and balanced composition. Face peacefully half-closed eyes
and a serene wise smile. Arms spread wide open in a calm welcoming gesture.

(10) DORMANCY: Only 1-2 bare gray-brown woody sticks above soil, a tiny bright
green bud (#66bb6a) barely visible at base. Pot wears a tiny blue-gray (#78909c)
sleeping cap with white pompom. Face with peacefully closed arc eyes and tiny
sleeping smile. Both arms hanging completely limp and relaxed at the sides.

(11) SENESCENCE: Plant with 5-6 leaves in autumn color transition — one or two
half-green leaves, two to three warm golden-amber (#d4a056) and rusty brown
(#bf8040) leaves, one dried brown tip leaf (#a0522d). One leaf hangs diagonally
barely attached to the stem, a second leaf floats freely mid-fall beside the
plant. A small dried seed capsule in straw-brown (#c8a96e) hangs at the base
of the stem. Plant still upright but visibly less full. Face carries calm half-
closed accepting eyes and a small serene knowing smile. Both arms resting
gently outward and downward in a quiet, composed open posture — dignified
stillness, neither limp nor raised.
```

---

## Technische Hinweise

1. **Farbkollision Phase 6 vs. Phase 5:** `#e65100` (Ripening) und `#ffa726` (Harvest) liegen
   im gleichen Orange-Spektrum. In der UI immer auch die Phasen-Bezeichnung als Text begleiten —
   die Farbe allein reicht bei kleinen Badge-Groessen nicht zur Unterscheidung. Bei 64x64px
   besonderen Wert auf unterschiedliche Blattstruktur und Frucht-Zustand legen.

2. **Phase 8 — Rankstab-Komplexitaet:** Der Moosstab im Topf fuegt ein weiteres visuelles Element
   hinzu. Bei 64x64px den Rankstab als einfache braune vertikale Linie vereinfachen — keine
   Textur, kein Moos-Detail. Lediglich eine Linie mit einem Kletterstiel darum.

3. **Phase 10 — Schlafmuetze-Erkennbarkeit:** Bei 64x64px kann die Schlafmuetze zu klein werden.
   Alternative fuer kleines Format: statt Muetze einfach drei kleine Punkte (...) ueber dem Topf
   als grafisches Schlaf-Signal verwenden — ohne Text, nur als Formakzent.

4. **Phase 9 — Fenestration-Darstellung:** Die Locher im Monstera-Blatt muessen als echte
   Transparenz (Alpha-Kanal) oder als heller Hintergrundton dargestellt werden, NICHT als weisse
   Flaechen. Bei dunklem Hintergrund (Dark Mode) sehen weisse Locher falsch aus.

5. **Konsistenz mit Phasen 1–5:** Vor der Generierung der neuen Phasen die Einzel-Prompts
   der bestehenden Serie (insbesondere Phase 3 Vegetativ) als Referenz-Output speichern. Den
   gleichen Generierungslauf oder dieselben Generator-Einstellungen verwenden.

6. **Dark-Mode-Outlines:** Wie bei der Originalserie: Die dunklen Gruen-Outlines (#1b5e20)
   koennen auf sehr dunklem Hintergrund (#121212) schlecht sichtbar sein. Fuer explizite
   Dark-Mode-Varianten die Outlines auf #c8e6c9 (helles Gruen) aendern — betrifft alle 11 Phasen.

7. **Phase 7 vs. Phase 2 — Visueller Unterschied:** Beide Phasen zeigen kleine Pflanzen, aber
   Phase 2 (Saemling) hat noch runde Keimblaetter in Hellgruen (#66bb6a), Phase 7 (Juvenil)
   zeigt bereits die arttypische Blattform in Teal (#26a69a). Die Blattform ist das
   Unterscheidungsmerkmal — in kleinen Groessen auf sehr verschiedene Blattsilhouetten achten.

8. **Phase 11 — Seneszenz vs. Dormanz-Unterschied:** Beide Phasen zeigen eine reduzierte Pflanze,
   aber der visuelle Kontrast ist klar: Dormanz (10) hat KEINE Blaetter mehr — nur kahle Stiele;
   Seneszenz (11) hat noch Blaetter, aber verfaerbt und fallend. Der entscheidende Unterschied
   ist das Vorhandensein von Blaettern (auch wenn verfaerbt). Das Gesicht unterstreicht das:
   Dormanz schlaeft (geschlossene Augen, Schlafmuetze), Seneszenz ist wach und wuerdevoll
   (halb offene Augen, wissendes Laecheln). Fuer 64x64px-Erkennbarkeit: die fallenden Blaetter
   als das Alleinstellungsmerkmal herausarbeiten — ein sichtbar fallendes Blatt neben dem Stiel.

9. **Phase 11 — Farbnaeher zum Topf:** `#d4a056` (Seneszenz-Goldocker) und `#8d6e63` (Topfbasis)
   liegen beide im Braun-Spektrum. Im Bild ist das kein Problem, da die Farben an verschiedenen
   Elementen sitzen. Als UI-Badge-Farbe bei sehr kleinen Groessen jedoch auf ausreichenden
   Kontrast zum Hintergrund achten — `#d4a056` auf weissem Hintergrund hat genuegend Kontrast
   (WCAG AA bei ausreichend grossem Text/Symbol). Als Chip-Hintergrundfarbe auf dunklem Text
   verwenden.

10. **Phase 11 — Samenkapsel-Detail:** Die getrocknete Samenkapsel ist ein bewusstes
    ikonografisches Element — sie unterscheidet Seneszenz von blossem Blattverlust (Herbstlaubfall)
    und signalisiert den Naehrstoffrueckzug ins Saatgut. Bei 64x64px kann das Detail entfallen —
    dann genuegen die verfaerbten und fallenden Blaetter als visuelles Signal.

---

## Nachbearbeitung Checkliste

- [ ] Alle 6 neuen Bilder auf exakt 256x256px zuschneiden
- [ ] Topf-Position mit bestehenden Phasen 1–5 vertikal angleichen (unteres Drittel)
- [ ] Hintergrund sauber transparent (Alpha-Kanal, kein Weiss)
- [ ] Phase 9: Fenestration-Locher auf Transparenz pruefen (nicht Weiss)
- [ ] Phase 11: Fallendes Blatt schwebt frei neben der Pflanze — kein Bodenkontakt
- [ ] Farbwerte gegen obige Phasenfarben validieren (Hex-Picker auf Hauptflaechen)
- [ ] Auf 64x64 skalieren: Phase 8 Rankstab erkennbar? Phase 10 Schlafmuetze erkennbar?
      Phase 11 fallendes Blatt erkennbar?
- [ ] Auf 512x512 skalieren fuer Retina/HiDPI
- [ ] Visuelle Konsistenz aller 11 Phasen nebeneinander pruefen (Screenshot-Reihe)
- [ ] Seneszenz vs. Dormanz Verwechslungsgefahr pruefen: Blaetter sichtbar (11) vs. keine (10)
- [ ] Optional: Dark-Mode-Varianten aller 11 Phasen mit Outlines #c8e6c9 erstellen
- [ ] Dateien ablegen unter: `src/frontend/src/assets/illustrations/phases/`
- [ ] Namenskonvention: `timeline-kami-phase-{name}.png` und `timeline-kami-phase-{name}.svg`
- [ ] i18n-Schluesselpruefung: Phasennamen in `de/translation.json` eintragen (ripening,
      juvenile, climbing, mature, dormancy, senescence)
