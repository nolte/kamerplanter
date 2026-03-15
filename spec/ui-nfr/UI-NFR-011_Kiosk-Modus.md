---

ID: UI-NFR-011
Titel: Kiosk-Modus & Gewächshaus-Bedienung
Kategorie: UI-Verhalten Unterkategorie: Kiosk, Touch, Gewächshaus, Feldmodus
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.1
Autor: Business Analyst - Agrotech
Datum: 2026-02-28
Tags: [kiosk, touch-targets, greenhouse, dirty-hands, gloves, simplified-ui, auto-timeout, high-contrast]
Abhängigkeiten: [UI-NFR-001, UI-NFR-002, UI-NFR-004, UI-NFR-005, UI-NFR-006]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-011: Kiosk-Modus & Gewächshaus-Bedienung

## 1. Business Case

### 1.1 User Story

**Als** Grower im Gewächshaus
**möchte ich** die Anwendung bedienen können, auch wenn meine Hände mit Erde, Nährlösung oder Pflanzensäften verschmutzt sind
**um** meinen Arbeitsfluss nicht unterbrechen zu müssen.

**Als** Grower mit Handschuhen
**möchte ich** alle kritischen Funktionen (Bewässerung erfassen, Pflanze scannen, Problem melden) mit großen Touch-Flächen bedienen können
**um** die Handschuhe nicht ausziehen zu müssen.

**Als** Betreiber eines Growraums
**möchte ich** ein fest installiertes Tablet als Kiosk-Station einrichten können
**um** allen Mitarbeitern eine einfache Datenerfassung ohne eigenes Gerät zu ermöglichen.

**Als** Grower in einer Notsituation (beide Hände voll, verschmutzt)
**möchte ich** die wichtigsten Aktionen notfalls mit der Nase, dem Ellenbogen oder dem Handrücken auslösen können
**um** nicht erst zum Waschbecken gehen zu müssen.

### 1.2 Geschäftliche Motivation

Kamerplanter ist eine Agrartechnologie-Anwendung, die primär in Gewächshäusern, Growräumen und auf dem Balkon eingesetzt wird. In diesen Umgebungen gelten besondere physische Bedingungen:

1. **Verschmutzte Hände** — Erde, Substrate, Nährlösungen, Pflanzensäfte und Wasser sind allgegenwärtig
2. **Handschuhe** — Nitril-, Latex- oder Gartenhandschuhe reduzieren die Touch-Präzision erheblich
3. **Feuchtigkeit** — Kapazitive Touchscreens reagieren bei nassen Fingern unzuverlässig (Phantom-Touches, fehlende Erkennung)
4. **Variable Lichtverhältnisse** — Direkte Sonneneinstrahlung im Gewächshaus, dunkle Ecken im Growraum, UV-Licht durch Natriumdampflampen oder LED-Panels
5. **Eingeschränkte Aufmerksamkeit** — Der Blick liegt auf der Pflanze, nicht auf dem Bildschirm

Ohne Kiosk-Modus wird die Anwendung in der primären Arbeitsumgebung nicht praxistauglich genutzt — Nutzer weichen auf Papiernotizen aus und tragen Daten nachträglich am Desktop ein, was zu Verzögerungen, Fehlern und unvollständiger Dokumentation führt.

---

## 2. Anforderungen

### 2.1 Kiosk-Modus — Aktivierung & Grundverhalten

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS einen dedizierten Kiosk-Modus bereitstellen, der über eine URL (`/kiosk`) oder einen Toggle in den Einstellungen aktiviert werden kann. | MUSS |
| R-002 | Der Kiosk-Modus MUSS als User-Präferenz persistent gespeichert werden (LocalStorage oder User-Einstellung). | MUSS |
| R-003 | Der Kiosk-Modus MUSS visuell erkennbar sein — ein permanenter Indikator (z.B. Badge „Kiosk" in der App-Bar) MUSS den aktiven Modus anzeigen. | MUSS |
| R-004 | Der Wechsel zwischen Kiosk- und Standard-Modus MUSS ohne Neuladen der Seite erfolgen. | MUSS |
| R-005 | Im Kiosk-Modus MUSS das High-Contrast-Theme (vgl. §2.7) als Default aktiviert werden. | MUSS |
| R-006 | Im Kiosk-Modus SOLL die Anwendung im Fullscreen-Modus (`Fullscreen API`) dargestellt werden können. | SOLL |

### 2.2 Touch-Targets — Kiosk-Dimensionierung

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Im Kiosk-Modus MÜSSEN alle interaktiven Elemente (Buttons, Links, Checkboxen, Toggles) eine Mindestgröße von **64×64px** für Touch-Targets einhalten. | MUSS |
| R-008 | Primäre Aktions-Buttons (Speichern, Bestätigen, Scannen) SOLLEN im Kiosk-Modus eine Zielgröße von **72×72px** haben. | SOLL |
| R-009 | Der Mindestabstand zwischen zwei interaktiven Elementen MUSS im Kiosk-Modus mindestens **16px** betragen, empfohlen sind **24px**. | MUSS |
| R-010 | Listeneinträge (Tabellenzeilen, Navigationseinträge) MÜSSEN im Kiosk-Modus eine Zeilenhöhe von mindestens **64px** haben. | MUSS |
| R-011 | Checkboxen und Toggles MÜSSEN im Kiosk-Modus einen Touch-Bereich von mindestens **64×64px** haben, unabhängig von der visuellen Größe des Elements. | MUSS |
| R-012 | Icons MÜSSEN im Kiosk-Modus mindestens **32px** groß dargestellt werden, empfohlen sind **48px** für Aktions-Icons. | MUSS |
| R-013 | Die MUI-Komponenten-Defaults MÜSSEN im Kiosk-Modus auf `size: 'large'` gesetzt werden (TextField, Button, IconButton, Select, Checkbox). | MUSS |

### 2.3 Vereinfachte Navigation

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Im Kiosk-Modus MUSS eine dedizierte Kiosk-Startseite angezeigt werden, die die wichtigsten Quick-Actions als große Kacheln (min. **80×80px**) darstellt. | MUSS |
| R-015 | Die Kiosk-Startseite MUSS mindestens folgende Quick-Actions enthalten: Pflanze scannen (QR), Bewässerung erfassen, Rundgang starten, Problem melden. | MUSS |
| R-016 | Die Kiosk-Startseite SOLL einen Bereich „Aktueller Status" enthalten, der die wichtigsten Kennzahlen (offene Aufgaben, letzte Aktivität, Warnungen) zusammenfasst. | SOLL |
| R-017 | Breadcrumbs MÜSSEN im Kiosk-Modus durch einen einzelnen großen „Zurück"-Button (min. 64px Höhe) am oberen Bildschirmrand ersetzt werden. | MUSS |
| R-018 | Ein permanenter „Home"-Button MUSS im Kiosk-Modus jederzeit sichtbar sein und zur Kiosk-Startseite zurückführen. | MUSS |
| R-019 | Die Navigationstiefe MUSS im Kiosk-Modus auf maximal **2 Ebenen** begrenzt sein (Startseite → Aktion → Bestätigung). | MUSS |
| R-020 | Dropdown-Menüs SOLLEN im Kiosk-Modus durch große, sichtbare Kachel-Auswahlen oder Fullscreen-Listen ersetzt werden. | SOLL |
| R-021 | Hamburger-Menüs DÜRFEN im Kiosk-Modus NICHT verwendet werden — alle verfügbaren Aktionen MÜSSEN direkt sichtbar sein. | MUSS |

### 2.4 Vereinfachte Eingabe

| # | Regel | Stufe |
|---|-------|-------|
| R-022 | Im Kiosk-Modus MÜSSEN Formulare auf Pflichtfelder reduziert werden — optionale Felder werden ausgeblendet oder in einen „Erweitert"-Bereich verschoben. | MUSS |
| R-023 | Texteingabe MUSS im Kiosk-Modus auf ein Minimum reduziert werden — zugunsten von Auswahllisten, QR-Scannern und vordefinierten Werten. | MUSS |
| R-024 | Numerische Eingabefelder für häufig verwendete Werte (EC, pH, Temperatur, Luftfeuchtigkeit) MÜSSEN im Kiosk-Modus **Quick-Select-Kacheln** mit vordefinierten Werten anbieten. | MUSS |
| R-025 | Quick-Select-Kacheln MÜSSEN mindestens **48×48px** groß sein und einen Mindestabstand von **12px** zueinander haben. | MUSS |
| R-026 | Neben den Quick-Select-Kacheln MUSS immer eine „Manuell"-Option für die freie Zahleneingabe verfügbar sein. | MUSS |
| R-027 | Für ganzzahlige Werte SOLLEN im Kiosk-Modus große +/− Stepper-Buttons (min. 56px) anstelle von Freitexteingabe verwendet werden. | SOLL |
| R-028 | Swipe-Gesten DÜRFEN im Kiosk-Modus NICHT als einzige Interaktionsmethode verwendet werden — sie sind mit nassen oder handschuhbehafteten Händen unzuverlässig. Jede Swipe-Aktion MUSS eine alternative Tap-Bedienung haben. | MUSS |

### 2.5 Debouncing & Fehlprävention

| # | Regel | Stufe |
|---|-------|-------|
| R-029 | Im Kiosk-Modus MUSS ein globales Touch-Debouncing von **300ms** für alle klickbaren Elemente aktiv sein, um versehentliche Doppel-Taps zu verhindern. | MUSS |
| R-030 | Destruktive Aktionen (Löschen, Abbrechen) MÜSSEN im Kiosk-Modus einen erhöhten Bestätigungsaufwand erfordern — der destruktive Button MUSS mindestens **2 Sekunden lang gedrückt** werden (Long-Press) oder durch einen zweistufigen Bestätigungsdialog geschützt sein. | MUSS |
| R-031 | Bei destruktiven Bestätigungsdialogen MUSS der Abstand zwischen „Bestätigen" und „Abbrechen" mindestens **32px** betragen, um versehentliches Drücken des falschen Buttons zu verhindern. | MUSS |
| R-032 | Scroll-Bereiche MÜSSEN im Kiosk-Modus deutliche visuelle Indikatoren anzeigen, dass mehr Inhalt vorhanden ist (Gradient-Fade oder Pfeil-Indikator am oberen/unteren Rand). | MUSS |

### 2.6 Auto-Timeout & Session-Management

| # | Regel | Stufe |
|---|-------|-------|
| R-033 | Im Kiosk-Modus MUSS nach einer konfigurierbaren Inaktivitätszeit (Standard: **120 Sekunden**) eine Timeout-Warnung angezeigt werden. | MUSS |
| R-034 | Die Timeout-Warnung MUSS als großflächiges Overlay (min. 50% der Bildschirmfläche) dargestellt werden mit einem Countdown und einem „Weiter arbeiten"-Button (min. 72px). | MUSS |
| R-035 | Wenn der Nutzer innerhalb von **30 Sekunden** nicht reagiert, MUSS die Anwendung automatisch zur Kiosk-Startseite zurückkehren. | MUSS |
| R-036 | Der Timeout-Timer MUSS bei jeder Touch-Interaktion zurückgesetzt werden. | MUSS |
| R-037 | Der Timeout-Wert SOLL in den Einstellungen konfigurierbar sein (Bereich: 60–600 Sekunden). | SOLL |
| R-038 | Ungespeicherte Eingaben MÜSSEN vor dem Timeout-Reset entweder automatisch als Entwurf gespeichert oder der Nutzer MUSS gewarnt werden. | MUSS |

### 2.7 High-Contrast-Theme für Kiosk & Outdoor

| # | Regel | Stufe |
|---|-------|-------|
| R-039 | Die Anwendung MUSS ein dediziertes **High-Contrast-Theme** bereitstellen, das im Kiosk-Modus automatisch aktiviert wird. | MUSS |
| R-040 | Das High-Contrast-Theme MUSS ein Kontrastverhältnis von mindestens **7:1** für alle Texte sicherstellen (WCAG AAA). | MUSS |
| R-041 | Hintergründe MÜSSEN im High-Contrast-Theme auf reine Schwarz/Weiß-Werte reduziert werden — keine Grauabstufungen für Flächenelemente. | MUSS |
| R-042 | Schriftstärke MUSS im High-Contrast-Theme mindestens **Medium (500)** betragen. | MUSS |
| R-043 | Subtile Schatten, Hover-Effekte und Gradient-Hintergründe MÜSSEN im High-Contrast-Theme deaktiviert werden. | MUSS |
| R-044 | Status-Informationen MÜSSEN im High-Contrast-Theme durch große, farbcodierte Indikatoren dargestellt werden (min. 24px Durchmesser) — zusätzlich zu Text und Icon (vgl. UI-NFR-002 R-018). | MUSS |
| R-045 | Das High-Contrast-Theme SOLL auch unabhängig vom Kiosk-Modus über die Einstellungen aktivierbar sein (z.B. für Outdoor-Nutzung auf dem Balkon). | SOLL |

### 2.8 Feedback im Kiosk-Modus

| # | Regel | Stufe |
|---|-------|-------|
| R-046 | Erfolgs- und Fehlermeldungen MÜSSEN im Kiosk-Modus als **großflächige Vollbild-Overlays** dargestellt werden — nicht als kleine Snackbars (Abweichung von UI-NFR-004 R-001 im Kiosk-Kontext). | MUSS |
| R-047 | Erfolgs-Overlays MÜSSEN ein großes Bestätigungssymbol (min. 96px) und eine kurze Nachricht (min. 24px Schriftgröße) enthalten und nach **3 Sekunden** automatisch verschwinden. | MUSS |
| R-048 | Fehler-Overlays MÜSSEN ein großes Warnsymbol (min. 96px), eine verständliche Fehlerbeschreibung und einen „Erneut versuchen"-Button (min. 64px Höhe) enthalten. | MUSS |
| R-049 | Fehler-Overlays DÜRFEN NICHT automatisch verschwinden — der Nutzer MUSS sie aktiv schließen. | MUSS |
| R-050 | Lade-Zustände MÜSSEN im Kiosk-Modus durch einen großen zentralen Spinner (min. 64px) dargestellt werden — nicht durch kleine Inline-Loader. | MUSS |
| R-051 | Die Anwendung SOLL im Kiosk-Modus optionale **Audio-Signale** als Feedback unterstützen: kurzer aufsteigender Ton bei Erfolg, kurzer tiefer Ton bei Fehler. | SOLL |
| R-052 | Audio-Signale MÜSSEN in den Einstellungen aktivierbar/deaktivierbar sein (Standard im Kiosk-Modus: aktiviert, Standard im Normal-Modus: deaktiviert). | MUSS |
| R-053 | Button-Presses MÜSSEN im Kiosk-Modus durch eine deutliche visuelle Reaktion bestätigt werden (Skalierung, Farbwechsel oder Ripple-Effekt mit min. 200ms Dauer). | MUSS |

### 2.9 Bildschirmschoner & Energiesparen

| # | Regel | Stufe |
|---|-------|-------|
| R-054 | Im Kiosk-Modus SOLL nach dem Timeout-Reset ein Bildschirmschoner oder ein gedimmter Zustand angezeigt werden, um den Bildschirm zu schonen und Energie zu sparen. | SOLL |
| R-055 | Der Bildschirmschoner SOLL die aktuelle Uhrzeit und den wichtigsten Status-Wert (z.B. Anzahl offener Aufgaben, letzter Sensorwert) in großer Schrift anzeigen. | SOLL |
| R-056 | Eine beliebige Touch-Interaktion MUSS den Bildschirmschoner beenden und die Kiosk-Startseite anzeigen. | MUSS |

<!-- Quelle: Frontend-Design-Review K-002 (Massentauglichkeit 2026-02-28) -->
### 2.10 Implementierungspriorität & MVP-Scope

**Begründung:** Die gesamte UI-NFR-011 (56 Einzelanforderungen) ist zum Stand 2026-02-28 nicht implementiert. Kein `/kiosk`-Route, kein Kiosk-Toggle, keine Quick-Action-Kacheln, kein Auto-Timeout, kein High-Contrast-Theme. Der Kiosk-Modus ist die prioritäre Anforderung für den professionellen Einsatz im Growraum — ohne ihn weichen Nutzer auf Papiernotizen aus. Die folgende Phasierung definiert den Mindestumfang (MVP) und die empfohlene Implementierungsreihenfolge.

| Phase | Umfang | Anforderungen | Begründung |
|-------|--------|---------------|------------|
| **Phase 1 — MVP** | `/kiosk`-Route, KioskProvider-Context, 4 Quick-Action-Kacheln (Pflanze scannen, Bewässerung erfassen, Rundgang starten, Problem melden), Kiosk-Badge in App-Bar, Auto-Timeout mit Warnung + Reset | R-001, R-002, R-003, R-014, R-015, R-033–R-036 | Grundstruktur ermöglicht erste praxistaugliche Nutzung im Gewächshaus. Ohne diese Basis hat der Kiosk-Modus keinen Wert. |
| **Phase 2 — Touch-Optimierung** | Touch-Target-Scaling (64px Minimum), MUI-Defaults auf `size: 'large'`, Debouncing (300ms), Long-Press für destruktive Aktionen, Scroll-Indikatoren | R-007–R-013, R-029–R-032 | Macht die Bedienung mit Handschuhen und verschmutzten Händen möglich. Ohne Touch-Scaling ist der Kiosk-Modus zwar erreichbar aber nicht bedienbar. |
| **Phase 3 — Navigation & Eingabe** | Zurück-Button statt Breadcrumbs, Home-Button, 2-Ebenen-Tiefe, Quick-Select-Kacheln (EC, pH, Temperatur), reduzierte Formulare, Stepper-Buttons, Fullscreen-API | R-004, R-006, R-017–R-028 | Vereinfacht den Workflow auf das Wesentliche. Quick-Select-Kacheln sind der zentrale Effizienzgewinn gegenüber Standard-Formularen. |
| **Phase 4 — Visual & Feedback** | High-Contrast-Theme (WCAG AAA), Vollbild-Overlays für Erfolg/Fehler, Audio-Signale, Button-Press-Feedback, Bildschirmschoner, konfigurierbarer Timeout | R-005, R-037–R-056 | Polishing für professionelle Dauerbetrieb-Szenarien. High-Contrast-Theme verbessert die Lesbarkeit bei Sonneneinstrahlung erheblich. |

**MVP-Definition (Mindestumfang für erste nutzbare Version):**

| Komponente | Beschreibung |
|-----------|-------------|
| `KioskProvider` | React Context der den Kiosk-Modus global verwaltet (isKiosk, toggleKiosk, timeoutConfig). MUI-Theme-Override für Touch-Target-Größen. |
| `/kiosk` Route | Dedizierte Route mit eigenem Layout (keine Sidebar, kein Breadcrumb). |
| `KioskStartPage` | 4 Quick-Action-Kacheln (min. 80×80px), Status-Zusammenfassung, letzte Aktivität. |
| `KioskAppBar` | Kiosk-Badge, Home-Button, Zurück-Button. |
| `useKioskTimeout` | Hook für Inaktivitäts-Timer (Touch-Event-Listener, Timeout-Warnung, Reset-zur-Startseite). |

---

## 3. Wireframe-Beispiele

### 3.1 Kiosk-Startseite

```
┌────────────────────────────────────────────────────────┐
│  🌿 Kamerplanter                      [Kiosk-Modus]   │
├────────────────────────────────────────────────────────┤
│                                                        │
│   ┌────────────────────┐   ┌────────────────────┐     │
│   │                    │   │                    │     │
│   │    📷 Pflanze      │   │    💧 Bewässerung  │     │
│   │    scannen         │   │    erfassen        │     │
│   │                    │   │                    │     │
│   │    (80×80px+)      │   │    (80×80px+)      │     │
│   └────────────────────┘   └────────────────────┘     │
│                    24px Abstand                        │
│   ┌────────────────────┐   ┌────────────────────┐     │
│   │                    │   │                    │     │
│   │    📋 Rundgang     │   │    ⚠️ Problem      │     │
│   │    starten         │   │    melden          │     │
│   │                    │   │                    │     │
│   │    (80×80px+)      │   │    (80×80px+)      │     │
│   └────────────────────┘   └────────────────────┘     │
│                                                        │
│   ┌────────────────────────────────────────────┐      │
│   │                                            │      │
│   │    📊 Aktueller Status                     │      │
│   │    3 offene Aufgaben · 1 Warnung           │      │
│   │                                            │      │
│   └────────────────────────────────────────────┘      │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Letzte Aktivität: Bewässerung Tank A — vor 23 min    │
└────────────────────────────────────────────────────────┘
```

### 3.2 Quick-Select-Kacheln (EC-Wert-Eingabe)

```
┌────────────────────────────────────────────────────────┐
│  [← Zurück]                            [🏠 Home]      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  EC-Wert der Nährlösung (mS/cm):                      │
│                                                        │
│   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐          │
│   │      │   │      │   │      │   │      │          │
│   │ 1.0  │   │ 1.5  │   │ 2.0  │   │ 2.5  │          │
│   │      │   │      │   │      │   │      │          │
│   └──────┘   └──────┘   └──────┘   └──────┘          │
│                                                        │
│   ┌──────┐   ┌──────────────────────────────┐          │
│   │      │   │                              │          │
│   │ 3.0  │   │  ⌨️ Manuell eingeben         │          │
│   │      │   │                              │          │
│   └──────┘   └──────────────────────────────┘          │
│                                                        │
│                                    48px Kacheln        │
│                                    12px Abstand        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.3 Kiosk-Bestätigungsdialog (destruktive Aktion)

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │                                                  │  │
│  │              ⚠️ (96px)                           │  │
│  │                                                  │  │
│  │    Pflanze „GH1-042" wirklich entfernen?         │  │
│  │                                                  │  │
│  │    Diese Aktion kann nicht rückgängig             │  │
│  │    gemacht werden.                               │  │
│  │                                                  │  │
│  │                                                  │  │
│  │  ┌──────────────────┐                            │  │
│  │  │                  │     32px                    │  │
│  │  │  Abbrechen       │    Abstand                 │  │
│  │  │  (64px Höhe)     │                            │  │
│  │  └──────────────────┘                            │  │
│  │                          ┌──────────────────┐    │  │
│  │                          │                  │    │  │
│  │                          │  Entfernen       │    │  │
│  │                          │  (64px, rot)     │    │  │
│  │                          │  halten (2s)     │    │  │
│  │                          └──────────────────┘    │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.4 Erfolgs-Overlay (Kiosk)

```
┌────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░┌──────────────────────────────┐░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│          ✅ (96px)           │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│    Bewässerung erfasst!      │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│    Tank A — 12.5 L           │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│    (verschwindet in 3s)      │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░└──────────────────────────────┘░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└────────────────────────────────────────────────────────┘
```

### 3.5 Timeout-Warnung

```
┌────────────────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░┌──────────────────────────────┐░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│          ⏱️ (96px)           │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│    Noch aktiv?               │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│    Rückkehr zum Start        │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│    in 25 Sekunden            │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│  ┌──────────────────────┐    │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│  │                      │    │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│  │  Weiter arbeiten     │    │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│  │  (72px Höhe)         │    │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│  └──────────────────────┘    │░░░░░░░░░░░░░ │
│ ░░░░░░░░░│                              │░░░░░░░░░░░░░ │
│ ░░░░░░░░░└──────────────────────────────┘░░░░░░░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└────────────────────────────────────────────────────────┘
```

### 3.6 Bildschirmschoner (gedimmt)

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│                                                        │
│                                                        │
│                                                        │
│                    14:32                                │
│                                                        │
│              3 offene Aufgaben                         │
│              Letzte Messung: 14:15                     │
│                                                        │
│                                                        │
│                                                        │
│           Bildschirm berühren zum Starten              │
│                                                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Kiosk-Modus — Aktivierung**
    - [ ] Kiosk-Modus ist über `/kiosk` und über Einstellungen-Toggle erreichbar
    - [ ] Modus-Präferenz wird persistent gespeichert
    - [ ] Visueller Indikator „Kiosk" ist im aktiven Modus sichtbar
    - [ ] Wechsel erfolgt ohne Seitenneuladen
    - [ ] High-Contrast-Theme ist im Kiosk-Modus automatisch aktiv
- [ ] **Touch-Targets**
    - [ ] Alle interaktiven Elemente haben im Kiosk-Modus min. 64×64px Touch-Target
    - [ ] Primäre Aktions-Buttons haben 72×72px
    - [ ] Mindestabstand zwischen Elementen ist 16px (gemessen)
    - [ ] MUI-Defaults sind im Kiosk-Modus auf `size: 'large'` gesetzt
    - [ ] Manuelle Tests: Bedienung mit Gartenhandschuhen auf realem Tablet bestanden
    - [ ] Manuelle Tests: Bedienung mit Nase auf realem Tablet bestanden (primäre Quick-Actions)
- [ ] **Navigation**
    - [ ] Kiosk-Startseite zeigt Quick-Actions als große Kacheln
    - [ ] „Zurück"-Button ist auf jeder Unterseite sichtbar (min. 64px)
    - [ ] „Home"-Button ist permanent sichtbar
    - [ ] Navigationstiefe ist auf 2 Ebenen begrenzt
    - [ ] Keine Hamburger-Menüs im Kiosk-Modus
- [ ] **Eingabe**
    - [ ] Formulare zeigen im Kiosk-Modus nur Pflichtfelder
    - [ ] Quick-Select-Kacheln für EC, pH, Temperatur sind vorhanden
    - [ ] „Manuell"-Option ist bei allen Quick-Selects vorhanden
    - [ ] Keine Swipe-Aktionen ohne Tap-Alternative
- [ ] **Debouncing & Fehlprävention**
    - [ ] 300ms Touch-Debouncing ist im Kiosk-Modus aktiv
    - [ ] Destruktive Aktionen erfordern Long-Press oder zweistufige Bestätigung
    - [ ] Abstand zwischen Bestätigen/Abbrechen ist min. 32px
- [ ] **Timeout**
    - [ ] Timeout-Warnung erscheint nach 120s Inaktivität
    - [ ] Countdown-Overlay ist großflächig und zeigt „Weiter arbeiten"-Button
    - [ ] Automatische Rückkehr zur Startseite nach 30s ohne Interaktion
    - [ ] Ungespeicherte Eingaben werden als Entwurf gesichert oder gewarnt
- [ ] **High-Contrast-Theme**
    - [ ] Kontrastverhältnis ≥7:1 für alle Texte
    - [ ] Keine Grauabstufungen für Flächenelemente
    - [ ] Schriftstärke min. Medium (500)
    - [ ] Keine subtilen Schatten oder Gradient-Hintergründe
    - [ ] Theme ist auch außerhalb des Kiosk-Modus aktivierbar
- [ ] **Feedback**
    - [ ] Erfolgs-/Fehlermeldungen werden als großflächige Overlays dargestellt
    - [ ] Audio-Feedback ist aktivierbar
    - [ ] Button-Presses zeigen deutliche visuelle Reaktion
- [ ] **Testing**
    - [ ] End-to-End-Test: Vollständiger Kiosk-Workflow (Startseite → Aktion → Bestätigung → Startseite)
    - [ ] Usability-Test mit mindestens 2 Personen im Gewächshaus mit echten Arbeitsbedingungen
    - [ ] Test auf Tablets (10" und 7") und fest montierten Kiosk-Displays
    - [ ] Test bei direkter Sonneneinstrahlung (Lesbarkeit High-Contrast-Theme)
    - [ ] Touch-Target-Messungen mit Chrome DevTools / axe-core

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Anwendung wird im Gewächshaus nicht genutzt** | Nutzer weichen auf Papier aus, Datenqualität sinkt dramatisch | Sehr hoch | Kiosk-Modus als prioritäres Feature implementieren |
| **Fehleingaben durch zu kleine Touch-Targets** | Falsche Messwerte, falsche Pflanzen bearbeitet, versehentliches Löschen | Hoch | 64px Minimum, 72px für primäre Aktionen, 300ms Debouncing |
| **Frustration durch komplexe Navigation** | Grower bricht Dateneingabe ab, trägt Daten nachträglich am Desktop ein (oder gar nicht) | Hoch | Max. 2 Ebenen Tiefe, große Quick-Action-Kacheln, permanenter Home-Button |
| **Unlesbare Anzeige bei Sonneneinstrahlung** | Messwerte, Status-Informationen und Warnungen werden übersehen | Hoch | High-Contrast-Theme (7:1), keine subtilen Grautöne, große Schrift |
| **Verwaiste Kiosk-Sessions** | Nachfolgender Nutzer sieht/ändert Daten des Vorgängers | Mittel | Auto-Timeout mit Warnung und automatischer Rückkehr zur Startseite |
| **Phantom-Touches bei Feuchtigkeit** | Unbeabsichtigte Aktionen durch Wassertropfen auf dem Screen | Mittel | Debouncing, Long-Press für destruktive Aktionen, kein Swipe |

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-28
**Review**: Pending
**Genehmigung**: Pending
