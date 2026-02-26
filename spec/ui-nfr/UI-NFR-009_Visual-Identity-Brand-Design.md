---

ID: UI-NFR-009
Titel: Visuelle Identität & Markendesign
Kategorie: UI-Verhalten
Unterkategorie: Branding, Logo, Illustration, Visual Identity
Technologie: React, TypeScript, MUI, Flutter, SVG, Lottie
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [branding, logo, visual-identity, comic-style, nature-theme, illustration, mascot, favicon, app-icon]
Abhängigkeiten: [UI-NFR-002, UI-NFR-006]
Betroffene Module: [Frontend, Mobile, Marketing]
---

# UI-NFR-009: Visuelle Identität & Markendesign

## 1. Business Case

### 1.1 User Stories

**Als** Endanwender
**möchte ich** eine visuell ansprechende, moderne Anwendung mit Wiedererkennungswert nutzen
**um** mich mit dem Produkt zu identifizieren und die Nutzung als angenehmes Erlebnis wahrzunehmen.

**Als** neuer Besucher
**möchte ich** auf den ersten Blick erkennen, dass es sich um eine Pflanzen-/Agrartech-Anwendung handelt
**um** sofort zu verstehen, wofür das Produkt steht.

**Als** Designer / Illustrator
**möchte ich** klare Vorgaben für den visuellen Stil (Comic, Natur-Thematik, Farbwelt) erhalten
**um** konsistente Logos, Icons und Illustrationen generieren zu können.

**Als** Entwickler
**möchte ich** alle Branding-Assets in definierten Formaten und Varianten erhalten
**um** sie korrekt in Web, Mobile und Marketing-Materialien einzubinden.

### 1.2 Geschäftliche Motivation

Eine starke visuelle Identität ist entscheidend für die Wahrnehmung und den Erfolg der Anwendung:

1. **Wiedererkennung** — Ein einprägsames Logo und konsistenter visueller Stil schaffen Markenidentität und Vertrauen
2. **Modernität** — Zeitgemäßes Design signalisiert eine aktiv gepflegte, zukunftsorientierte Anwendung
3. **Emotionale Bindung** — Der Comic-Stil vermittelt Nahbarkeit und Freude an der Nutzung; die Natur-Thematik schafft thematische Kohärenz
4. **Differenzierung** — Im Agrartech-Umfeld heben sich verspielte, liebevolle Illustrationen deutlich von nüchternen Industrie-UIs ab
5. **Konsistenz** — Einheitliche Brand-Assets über alle Plattformen (Web, Mobile, E-Mail, Docs) verstärken den professionellen Eindruck

---

## 2. Designphilosophie

### 2.1 Leitmotiv: „Natur trifft Technologie"

Die Anwendung bewegt sich im Spannungsfeld zwischen **organischer Natur** und **moderner Agrartechnologie**. Das visuelle Design MUSS dieses Zusammenspiel widerspiegeln:

- **Organisch** — Weiche Formen, abgerundete Ecken, pflanzliche Motive, Blattstrukturen
- **Technisch** — Klare Layouts, datengetriebene Dashboards, präzise Visualisierungen
- **Lebendig** — Farbverläufe, subtile Animationen, lebendige (nicht sterile) Farbpalette
- **Einladend** — Freundliche Illustrationen, humorvolle Details, zugängliche Bildsprache

### 2.2 Stichworte für die Design-DNA

| Attribut | Beschreibung |
|----------|-------------|
| **Modern** | Flat Design mit Tiefe (Soft Shadows, Layering), keine Skeuomorphismen |
| **Natürlich** | Grüntöne dominieren, erdige Akzente, pflanzliche Formensprache |
| **Comic-artig** | Handgezeichneter Charme, klare Outlines, lebendige Farben |
| **Warm** | Einladende Tonalität, keine kalte Industrieästhetik |
| **Verspielt** | Kleine Überraschungen in Illustrationen, humorvolle Details |
| **Professionell** | Trotz Comic-Stil klar und funktional — kein Kinderspielzeug |

---

## 3. Anforderungen

### 3.1 Logo

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Das Primärlogo MUSS ein **Wortbild-Logo** (Kombination aus Bildmarke + Schriftzug „Kamerplanter") sein. | MUSS |
| R-002 | Die Bildmarke MUSS ein stilisiertes Pflanzenmotiv enthalten (z.B. Blatt, Keimling, Topfpflanze). | MUSS |
| R-003 | Die Bildmarke MUSS im **Comic-/Illustrated-Stil** gehalten sein: klare Outlines (2–3px), flächige Farbfüllung, leichte Schatten für Tiefe. | MUSS |
| R-004 | Das Logo MUSS in folgenden **Varianten** bereitgestellt werden: Primär (horizontal), Gestapelt (vertikal), Bildmarke allein (Icon), Monochrom (Schwarz), Monochrom (Weiß). | MUSS |
| R-005 | Das Logo MUSS auf hellen UND dunklen Hintergründen funktionieren. | MUSS |
| R-006 | Das Logo SOLL einen leichten **3D-Comic-Effekt** haben (z.B. leichter Drop-Shadow, Highlight-Kante), der Tiefe ohne Fotorealismus erzeugt. | SOLL |
| R-007 | Das Logo DARF NICHT mehr als **4 Farben** (exklusive Schwarz/Weiß) verwenden. | MUSS |
| R-008 | Die Schrift im Logo SOLL eine **gerundete Sans-Serif** sein, die den freundlichen, organischen Charakter unterstreicht (z.B. Nunito, Quicksand, Comfortaa oder vergleichbar). | SOLL |

### 3.2 App-Icon & Favicon

| # | Regel | Stufe |
|---|-------|-------|
| R-009 | Das App-Icon MUSS die **Bildmarke des Logos** (ohne Schriftzug) verwenden. | MUSS |
| R-010 | Das App-Icon MUSS in folgenden Größen bereitgestellt werden: 16×16, 32×32, 48×48, 64×64, 128×128, 192×192, 256×256, 512×512 Pixel. | MUSS |
| R-011 | Das App-Icon MUSS als **SVG** (Vektor) und **PNG** (Raster) verfügbar sein. | MUSS |
| R-012 | Das Favicon MUSS das App-Icon in vereinfachter Form (weniger Details) für kleine Größen (16×16, 32×32) verwenden. | MUSS |
| R-013 | Für Mobile (Android/iOS) MÜSSEN zusätzlich **Adaptive Icons** mit korrektem Safe-Area-Padding bereitgestellt werden. | MUSS |

### 3.3 Illustrationsstil (Comic-Stil-Richtlinien)

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Alle anwendungseigenen Illustrationen MÜSSEN einem **einheitlichen Comic-Stil** folgen. | MUSS |
| R-015 | Der Illustrationsstil MUSS folgende Merkmale aufweisen: **Klare Outlines** (gleichmäßige Strichstärke, leicht abgerundet), **Flächige Farbfüllung** (keine fotorealistischen Texturen), **Begrenzte Farbpalette** (aus dem definierten Farbsystem), **Weiche Schatten** (kein harter Schlagschatten). | MUSS |
| R-016 | Pflanzen-Illustrationen SOLLEN **freundlich und lebendig** wirken — leicht überproportionierte Blätter, lebendige Grüntöne, optionale „Gesichter" oder anthropomorphe Züge auf Pflanzen. | SOLL |
| R-017 | Empty States, Onboarding-Screens und Fehlerseiten SOLLEN mit **ganzseitigen Comic-Illustrationen** versehen werden. | SOLL |
| R-018 | Illustrationen MÜSSEN als **SVG** oder **Lottie-Animation** bereitgestellt werden (kein Raster-Format außer für Fallbacks). | MUSS |
| R-019 | Animierte Illustrationen (z.B. wachsende Pflanze, Gießkanne) SOLLEN als **Lottie-Dateien** mit max. 5 Sekunden Dauer und < 100 KB Dateigröße bereitgestellt werden. | SOLL |

### 3.4 Natur-Thematik im UI

| # | Regel | Stufe |
|---|-------|-------|
| R-020 | Die **Primärfarbe** MUSS ein lebendiges, mittleres Grün sein, das an frisches Blattgrün erinnert. | MUSS |
| R-021 | Die **Sekundärfarbe** SOLL ein warmer Erdton sein (z.B. Terracotta, Lehm oder warmes Braun). | SOLL |
| R-022 | Akzentfarben SOLLEN von natürlichen Elementen abgeleitet werden: Blütenfarben (Violett, Gelb), Himmelblau, Sonnenuntergangstöne. | SOLL |
| R-023 | Hintergrundflächen im Light-Mode SOLLEN einen **leichten Warmton** haben (kein reines Weiß #FFFFFF, sondern z.B. #FAFAF5 oder ähnlich). | SOLL |
| R-024 | Dekorative Hintergrund-Elemente (z.B. subtile Blattsilhouetten, Ranken-Pattern) KÖNNEN auf ausgewählten Seiten eingesetzt werden, DÜRFEN aber NICHT die Lesbarkeit beeinträchtigen. | KANN |
| R-025 | Ladeanimationen SOLLEN pflanzliche Motive verwenden (z.B. wachsender Keimling, sich öffnende Blüte, Blätter im Wind). | SOLL |
| R-026 | Phasenwechsel im Pflanzenlebenszyklus SOLLEN visuell durch passende Illustrationen der jeweiligen Wachstumsphase dargestellt werden. | SOLL |

### 3.5 Maskottchen / Charakter

| # | Regel | Stufe |
|---|-------|-------|
| R-027 | Die Anwendung SOLL ein **Maskottchen** im Comic-Stil besitzen, das als visueller Begleiter fungiert. | SOLL |
| R-028 | Das Maskottchen SOLL eine **anthropomorphe Pflanze** sein (z.B. ein freundlicher Keimling mit Gesicht, eine Topfpflanze mit Armen/Beinen, ein Blatt-Charakter). | SOLL |
| R-029 | Das Maskottchen MUSS in mindestens folgenden **Stimmungen/Posen** bereitgestellt werden: Neutral/Fröhlich (Standard), Feiernd (Erfolg), Nachdenklich (Ladezustand), Traurig/Besorgt (Fehler), Winkend (Onboarding/Willkommen). | MUSS |
| R-030 | Maskottchen-Varianten SOLLEN als **Lottie-Animationen** mit Idle-Loop (Blinzeln, leichtes Wippen) verfügbar sein. | SOLL |
| R-031 | Das Maskottchen KANN in Benachrichtigungen, Tooltips und leeren Zuständen verwendet werden, um Informationen freundlich zu vermitteln. | KANN |

### 3.6 Asset-Formate & Dateiorganisation

| # | Regel | Stufe |
|---|-------|-------|
| R-032 | Alle Brand-Assets MÜSSEN in einem zentralen Verzeichnis `assets/brand/` organisiert sein. | MUSS |
| R-033 | Die Verzeichnisstruktur MUSS folgendes Schema einhalten: `assets/brand/logo/`, `assets/brand/icon/`, `assets/brand/mascot/`, `assets/brand/illustrations/`, `assets/brand/patterns/`. | MUSS |
| R-034 | Jede Illustration MUSS in folgenden Formaten vorliegen: **SVG** (Primärformat), **PNG @1x, @2x, @3x** (Raster-Fallback), **WebP** (optimierter Fallback). | MUSS |
| R-035 | SVG-Dateien MÜSSEN optimiert sein (svgo) und DÜRFEN keine eingebetteten Rastergrafiken enthalten. | MUSS |
| R-036 | Alle Assets MÜSSEN eine **einheitliche Namenskonvention** verwenden: `[typ]-[name]-[variante].[format]` (z.B. `logo-kamerplanter-horizontal.svg`, `mascot-keimling-happy.svg`). | MUSS |

---

## 4. Farbpalette (Natur-inspiriert)

### 4.1 Kernfarben

Die folgenden Farbwerte dienen als **Richtlinie für die Logo- und Illustrationsgenerierung**. Die exakten Token-Werte werden in UI-NFR-006 definiert und können nach Fertigstellung der Logos feinjustiert werden.

```
  Primärgrün (Blattgrün)
  ┌─────────────────────────────────────────────┐
  │  #4CAF50 (Basis)                            │
  │  hsl(122, 39%, 49%)                         │
  │  Verwendung: Logo-Hauptfarbe, CTAs, Links   │
  │                                             │
  │  Heller:  #81C784  Dunkler:  #388E3C        │
  └─────────────────────────────────────────────┘

  Sekundär (Erdton / Terracotta)
  ┌─────────────────────────────────────────────┐
  │  #8D6E63 (Basis)                            │
  │  hsl(16, 18%, 47%)                          │
  │  Verwendung: Sekundäre Elemente, Erde,      │
  │  Substrat-Visualisierungen                  │
  │                                             │
  │  Heller:  #A1887F  Dunkler:  #6D4C41        │
  └─────────────────────────────────────────────┘

  Akzent 1 (Blüte / Violett)
  ┌─────────────────────────────────────────────┐
  │  #AB47BC (Basis)                            │
  │  hsl(291, 47%, 51%)                         │
  │  Verwendung: Blütephase, Highlights,        │
  │  Akzentelemente                             │
  └─────────────────────────────────────────────┘

  Akzent 2 (Sonne / Warmgelb)
  ┌─────────────────────────────────────────────┐
  │  #FFB74D (Basis)                            │
  │  hsl(33, 100%, 65%)                         │
  │  Verwendung: Licht-/Photosynthese-Bezug,    │
  │  Warnungen, Highlights                      │
  └─────────────────────────────────────────────┘

  Himmelblau (Wasser)
  ┌─────────────────────────────────────────────┐
  │  #4FC3F7 (Basis)                            │
  │  hsl(199, 92%, 64%)                         │
  │  Verwendung: Bewässerung, Sensor-Daten,     │
  │  Info-Elemente                              │
  └─────────────────────────────────────────────┘
```

### 4.2 Phasenfarben (Pflanzenlebenszyklus)

Jede Wachstumsphase erhält eine **eigene Akzentfarbe**, die in Illustrationen und UI-Elementen verwendet wird:

```
  Keimung        ──▶  Zartgrün       #A5D6A7
  Setzling       ──▶  Frühlingsgrün  #66BB6A
  Vegetativ      ──▶  Sattes Grün    #43A047
  Blüte          ──▶  Violett/Magenta #AB47BC
  Ernte          ──▶  Goldgelb       #FFA726
```

---

## 5. Logo-Konzeptbeschreibungen (für Generierung)

Die folgenden Beschreibungen dienen als **Prompt-Vorlage** für die Logo-Generierung (z.B. via Midjourney, DALL-E, Illustrator oder ähnliche Tools).

### 5.1 Konzept A: „Keim im Topf"

```
  Beschreibung:
  Ein kleiner, fröhlicher Keimling mit zwei Blättern,
  der aus einem Pflanztopf herausschaut. Der Topf hat
  eine leichte Textur (Terracotta-Optik). Der Keimling
  hat ein freundliches Gesicht (optionales Maskottchen-
  Element). Darunter oder daneben der Schriftzug
  „Kamerplanter" in einer gerundeten Sans-Serif.

  Stil: Comic/Flat mit leichtem 3D-Effekt
  Farben: Grün (#4CAF50), Terracotta (#8D6E63), Weiß
  Strichstärke: 2-3px, gleichmäßig, leicht abgerundet

  ┌─────────────────────────────────────┐
  │              🌱                      │
  │           ╱    ╲                     │
  │          🍃    🍃                    │
  │           │                          │
  │       ┌───┴───┐                      │
  │       │       │  ← Topf (Terracotta) │
  │       │  ◠‿◠  │  ← optionales       │
  │       └───────┘    Gesicht           │
  │                                      │
  │     K a m e r p l a n t e r          │
  └─────────────────────────────────────┘
```

### 5.2 Konzept B: „Blatt-Technologie-Fusion"

```
  Beschreibung:
  Ein stilisiertes Blatt, dessen Blattadern an ein
  Schaltkreis-Layout erinnern — die Verbindung von
  Natur und Technologie. Die Outline ist im Comic-Stil
  gehalten (gleichmäßig, abgerundet). Innerhalb des
  Blatts ein dezentes Muster aus Leiterbahnen.

  Stil: Flat-Design mit Comic-Outlines
  Farben: Grün (#4CAF50), Akzentgrün (#81C784),
          dezente Circuit-Linien in Dunkelgrün (#2E7D32)

  ┌─────────────────────────────────────┐
  │          ╱╲                          │
  │         ╱──╲                         │
  │        ╱ ┄┄ ╲  ← Blattadern als     │
  │       ╱ ┄┄┄┄ ╲   Schaltkreislinien  │
  │      ╱ ┄┄┄┄┄┄ ╲                     │
  │      ╲ ┄┄┄┄┄┄ ╱                     │
  │       ╲ ┄┄┄┄ ╱                      │
  │        ╲ ┄┄ ╱                        │
  │         ╲──╱                         │
  │          ╲╱                          │
  │                                      │
  │     K a m e r p l a n t e r          │
  └─────────────────────────────────────┘
```

### 5.3 Konzept C: „Grüner Kreis mit Pflanze"

```
  Beschreibung:
  Ein kreisförmiges Badge/Emblem mit einer stilisierten
  Pflanze in der Mitte. Der Kreis-Rand hat eine leichte
  Blattstruktur. Die Pflanze zeigt mehrere Wachstums-
  phasen gleichzeitig (Wurzel → Stiel → Blätter → Blüte).

  Stil: Badge-Logo im Comic-Stil, Emblem-Charakter
  Farben: Grün-Gradient im Kreis, Pflanze mehrfarbig
          (Phasenfarben), weißer Hintergrund

  ┌─────────────────────────────────────┐
  │        ╭──────────╮                  │
  │       ╱   🌸       ╲                 │
  │      │   🍃│🍃      │                │
  │      │     │        │                │
  │      │    ╌│╌       │  ← Wurzeln     │
  │       ╲   ╌│╌      ╱                 │
  │        ╰──────────╯                  │
  │                                      │
  │     K a m e r p l a n t e r          │
  └─────────────────────────────────────┘
```

---

## 6. Maskottchen-Konzeptbeschreibung

### 6.1 „Kami" — der Kamerplanter-Keimling

```
  Name: Kami (Kurzform von Kamerplanter)
  Art: Anthropomorpher Keimling / junge Topfpflanze
  Charakter: Fröhlich, hilfsbereit, neugierig, etwas tollpatschig

  Grundform:
  ┌─────────────────────────────────────────────┐
  │                                             │
  │         🍃    🍃   ← Zwei Blätter als       │
  │          ╲  ╱        „Haare/Ohren"          │
  │           ╲╱                                │
  │        ┌──────┐                             │
  │        │ ◉  ◉ │  ← Große, ausdrucksstarke  │
  │        │  ◡   │     Comic-Augen             │
  │        └──┬───┘                             │
  │           │      ← Dünner Stiel als „Hals"  │
  │       ┌───┴───┐                             │
  │      ╱│       │╲ ← Optionale kleine Arme    │
  │       │  ═══  │  ← Terracotta-Topf mit      │
  │       │       │     Deko-Streifen            │
  │       └───────┘                             │
  │                                             │
  └─────────────────────────────────────────────┘

  Stimmungsvarianten:
  ┌──────────┬──────────┬──────────┬──────────┬──────────┐
  │ HAPPY    │ SUCCESS  │ THINKING │ SAD      │ WAVING   │
  │          │          │          │          │          │
  │  ◉  ◉   │  ◉  ◉   │  ◉  ◉   │  ◉  ◉   │  ◉  ◉   │
  │   ◡     │   ◡ ✿   │   ∿     │   ◠     │   ◡     │
  │          │  \│/     │   /│    │   │      │  \│╱    │
  │   │      │   │      │   │     │   │      │   │     │
  │  ═══    │  ═══    │  ═══    │  ═══    │  ═══    │
  │          │  🎉      │   ?     │   💧     │   👋     │
  └──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 6.2 Einsatzszenarien für das Maskottchen

| Szenario | Pose | Kontext |
|----------|------|---------|
| **Onboarding** | Winkend | „Willkommen bei Kamerplanter!" |
| **Leerer Zustand** | Nachdenklich | „Noch keine Pflanzen angelegt. Füge deine erste hinzu!" |
| **Erfolg** | Feiernd | „Pflanze erfolgreich in die Blütephase gewechselt!" |
| **Fehler** | Traurig | „Etwas ist schiefgelaufen. Bitte versuche es erneut." |
| **Ladevorgang** | Gießkanne haltend | Lottie-Animation: Kami gießt sich selbst |
| **Keine Daten** | Lupe haltend | „Keine Sensordaten für diesen Zeitraum gefunden." |
| **Tipp/Hinweis** | Zeigend | Tooltip-Begleiter für kontextuelle Hilfe |

---

## 7. Wireframe-Beispiele: Integration in die UI

### 7.1 Splash Screen / Login

```
  ┌──────────────────────────────────────┐
  │                                      │
  │            ╭──────────╮              │
  │           ╱            ╲             │
  │          │   🌱 LOGO    │            │
  │           ╲            ╱             │
  │            ╰──────────╯              │
  │                                      │
  │        K a m e r p l a n t e r       │
  │     „Dein digitaler Pflanzenmanager" │
  │                                      │
  │  ┌──────────────────────────────┐    │
  │  │ 📧 E-Mail                    │    │
  │  └──────────────────────────────┘    │
  │  ┌──────────────────────────────┐    │
  │  │ 🔒 Passwort                  │    │
  │  └──────────────────────────────┘    │
  │                                      │
  │  ┌──────────────────────────────┐    │
  │  │        ▶ ANMELDEN            │    │
  │  └──────────────────────────────┘    │
  │                                      │
  │  ╌╌╌ subtiles Blatt-Pattern ╌╌╌╌    │
  │  ╌╌╌ im Hintergrund        ╌╌╌╌    │
  └──────────────────────────────────────┘
```

### 7.2 Empty State mit Maskottchen

```
  ┌──────────────────────────────────────┐
  │  ▓▓ Kamerplanter    [☀/🌙] [👤]    │
  ├──────────────────────────────────────┤
  │                                      │
  │                                      │
  │          ┌──────────┐                │
  │          │  Kami     │                │
  │          │  (Lupe)  │                │
  │          │  ◉  ◉    │                │
  │          │   ◡  🔍  │                │
  │          └──────────┘                │
  │                                      │
  │    Noch keine Pflanzen angelegt.     │
  │                                      │
  │    ┌────────────────────────┐        │
  │    │ 🌱 Erste Pflanze       │        │
  │    │    hinzufügen          │        │
  │    └────────────────────────┘        │
  │                                      │
  └──────────────────────────────────────┘
```

### 7.3 Dashboard Header mit Logo und Naturthematik

```
  ┌──────────────────────────────────────────────────────┐
  │  🌱 Kamerplanter               [🔍] [🔔] [☀/🌙] [👤] │
  ├──────────────────────────────────────────────────────┤
  │                                                      │
  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │
  │  │ 🌿 12      │ │ 🌡 23.5°C  │ │ 💧 65%     │       │
  │  │ Pflanzen   │ │ Temperatur │ │ Luftfeucht.│       │
  │  │ aktiv      │ │ Durchschn. │ │ Durchschn. │       │
  │  └────────────┘ └────────────┘ └────────────┘       │
  │                                                      │
  │  ┌──────────────────────────────────────────────┐    │
  │  │ Deine Pflanzen                               │    │
  │  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │    │
  │  │ │🌱    │ │🍃    │ │🌸    │ │🌾    │         │    │
  │  │ │Comic │ │Comic │ │Comic │ │Comic │         │    │
  │  │ │Illus.│ │Illus.│ │Illus.│ │Illus.│         │    │
  │  │ │      │ │      │ │      │ │      │         │    │
  │  │ │Tomate│ │Basil.│ │Laven.│ │Weizen│         │    │
  │  │ └──────┘ └──────┘ └──────┘ └──────┘         │    │
  │  └──────────────────────────────────────────────┘    │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

---

## 8. Typografie-Empfehlung für Branding

Die folgenden Schriftarten ergänzen den Comic-Natur-Stil und SOLLEN für die Logo-Generierung und Marketing-Materialien verwendet werden. Die finalen Schriftarten für die Anwendung selbst werden in UI-NFR-006 definiert.

| Verwendung | Empfehlung | Fallback | Begründung |
|-----------|------------|----------|------------|
| **Logo-Schrift** | Quicksand Bold / Comfortaa Bold | Nunito Bold | Gerundet, modern, organisch, gute Lesbarkeit |
| **Überschriften** | Nunito / Quicksand | System-UI | Friendly, warm, passt zum Comic-Stil |
| **Fließtext** | Inter / Open Sans | System-UI | Klar, neutral, gute Lesbarkeit bei kleinen Größen |
| **Monospace (Code/Daten)** | JetBrains Mono | Fira Code | Für Sensordaten, Messwerte, Konfigurationen |

---

## 9. Akzeptanzkriterien

### Definition of Done

- [ ] **Logo**
    - [ ] Primärlogo (Bildmarke + Schriftzug) ist erstellt
    - [ ] Alle 5 Varianten (horizontal, vertikal, Icon, mono-schwarz, mono-weiß) sind vorhanden
    - [ ] Logo funktioniert auf hellem und dunklem Hintergrund
    - [ ] Logo verwendet maximal 4 Farben (+ Schwarz/Weiß)
    - [ ] Comic-Stil mit klaren Outlines und flächiger Füllung
    - [ ] Logo ist in SVG und PNG (alle Größen) exportiert
- [ ] **App-Icon & Favicon**
    - [ ] App-Icon in allen erforderlichen Größen (16px bis 512px)
    - [ ] Favicon ist in vereinfachter Form für kleine Größen optimiert
    - [ ] Adaptive Icons für Android/iOS bereitgestellt
    - [ ] Alle Formate (SVG, PNG, WebP) vorhanden
- [ ] **Illustrationsstil**
    - [ ] Styleguide für Comic-Illustrationen ist dokumentiert
    - [ ] Mindestens 5 Beispiel-Illustrationen im definierten Stil
    - [ ] Einheitliche Strichstärke, Farben und Schatten
    - [ ] SVG-Dateien sind optimiert (svgo)
- [ ] **Maskottchen „Kami"**
    - [ ] Alle 5 Stimmungsvarianten sind illustriert
    - [ ] Mindestens eine Lottie-Animation (Idle-Loop)
    - [ ] Maskottchen ist in mindestens 3 UI-Kontexten einsetzbar
- [ ] **Farbpalette**
    - [ ] Alle Kernfarben und Phasenfarben sind definiert
    - [ ] Farben sind im Kontext des Logos und der Illustrationen getestet
    - [ ] Farben erfüllen Kontrast-Anforderungen (→ UI-NFR-002, UI-NFR-006)
- [ ] **Asset-Organisation**
    - [ ] `assets/brand/`-Struktur ist eingerichtet
    - [ ] Namenskonvention wird eingehalten
    - [ ] Alle Assets sind in den erforderlichen Formaten vorhanden

### Testszenarien

**GIVEN** das Logo wird in der Navbar auf hellem Hintergrund angezeigt
**WHEN** der Nutzer auf Dark-Mode wechselt
**THEN** wird die korrekte Logo-Variante (für dunklen Hintergrund) angezeigt, ohne Layoutverschiebung.

**GIVEN** ein Empty State ohne Pflanzen
**WHEN** der Nutzer die Pflanzenliste öffnet
**THEN** wird das Maskottchen „Kami" in der Pose „Nachdenklich mit Lupe" angezeigt, inklusive Call-to-Action.

**GIVEN** eine Pflanze wechselt in die Blütephase
**WHEN** die Erfolgsmeldung angezeigt wird
**THEN** erscheint das Maskottchen „Kami" in der Pose „Feiernd" neben der Benachrichtigung.

**GIVEN** die Anwendung lädt Daten
**WHEN** der Nutzer eine Ladeanimation sieht
**THEN** wird eine pflanzliche Lottie-Animation abgespielt (kein generischer Spinner).

---

## 10. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Inkonsistenter Illustrationsstil** | Anwendung wirkt zusammengestückelt und unprofessionell | Hoch | Detaillierter Styleguide, alle Illustrationen von einer Quelle/einem Stil |
| **Logo ohne Wiedererkennungswert** | Marke bleibt in Erinnerung der Nutzer nicht haften | Mittel | Mehrere Konzepte testen, Feedback einholen, A/B-Tests |
| **Natur-Thematik zu dominant** | UI wirkt verspielt statt professionell, reduziert Vertrauen bei Profi-Nutzern | Mittel | Natur-Elemente dezent einsetzen, auf Funktionalität fokussieren, Nutzertest |
| **Comic-Stil wirkt unseriös** | Professionelle Anwender nehmen das Tool nicht ernst | Niedrig | Comic-Elemente auf Illustrationen/Mascot beschränken, Kern-UI bleibt clean |
| **Fehlende Asset-Varianten** | Logo/Icons sehen auf bestimmten Hintergründen/Größen schlecht aus | Hoch | Alle Varianten von Anfang an einplanen, in CI/CD Asset-Vollständigkeit prüfen |
| **Zu große Lottie-Dateien** | Performance-Probleme, langsame Ladezeiten | Mittel | Dateigröße-Limit (< 100 KB), Lazy Loading, Fallback auf statisches SVG |

---

## 11. Generierungs-Prompts (Referenz)

Die folgenden Texte können als Basis-Prompts für KI-gestützte Bildgenerierung verwendet werden. Sie SOLLEN an das jeweilige Tool (Midjourney, DALL-E, Stable Diffusion, etc.) angepasst werden.

### 11.1 Logo-Generierung

```
Prompt (EN):
"A modern, flat-design logo for an agricultural technology app called
'Kamerplanter'. The logo features a cute, comic-style sprouting plant
in a terracotta pot. Clean outlines (2-3px), flat color fills with
subtle shading. Color palette: fresh green (#4CAF50), terracotta brown
(#8D6E63), white background. The plant has two small leaves. Below or
beside the plant, the text 'Kamerplanter' in a rounded sans-serif font
(like Quicksand or Comfortaa). Style: vector illustration, comic/cartoon,
professional yet friendly. No photorealism. Transparent background."
```

### 11.2 Maskottchen-Generierung

```
Prompt (EN):
"A cute, comic-style mascot character for a plant management app.
The character is an anthropomorphic sprouting seedling growing from a
small terracotta pot. It has two green leaves on top (like hair/ears),
big expressive cartoon eyes, a small happy mouth, and tiny arms.
The pot has a decorative stripe. Style: flat vector illustration,
clean outlines, kawaii-influenced but not childish, professional
cartoon style. Colors: fresh green (#4CAF50), terracotta (#8D6E63),
warm highlights. Multiple poses: happy, celebrating, thinking, sad,
waving. Transparent background, suitable for app UI."
```

### 11.3 UI-Illustrationen (Empty States)

```
Prompt (EN):
"A set of illustration scenes for an agricultural tech app in a
consistent comic/cartoon style: (1) An empty garden scene with a
smiling seedling mascot holding a magnifying glass, (2) A celebration
scene with confetti and a blooming plant, (3) A rainy scene with a
sad plant holding an umbrella (error state), (4) A cozy greenhouse
scene with plants on shelves (loading state). Style: flat vector,
clean outlines, nature-inspired palette (greens, terracotta, warm
yellows), modern and friendly. No photorealism."
```

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
