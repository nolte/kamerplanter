# UI-Komponenten-Review: kamerplanter-plant-card und Pflege-Dashboard
**Erstellt von:** Frontend-Design-Reviewer
**Datum:** 2026-04-03
**Fokus:** Responsive Design, Kiosk-Modus, Mobile, Barrierefreiheit, Praxistauglichkeit
**Analysierte Dateien:**
- `custom_components/kamerplanter/www/kamerplanter-plant-card.js`
- `src/frontend/src/pages/pflege/PflegeDashboardPage.tsx`
- `src/frontend/src/pages/pflege/components/CareProfileEditDialog.tsx`
- `src/frontend/src/pages/pflege/components/CareConfirmDialog.tsx`

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| HA-Card: Responsive Design | 3/5 | Timeline-Overflow auf Smartphone kritisch, Rest solide |
| HA-Card: HA-Theme-Integration | 5/5 | CSS Custom Properties konsequent eingesetzt, vorbildlich |
| HA-Card: Touch-Tauglichkeit | 2/5 | Keine Touch-Targets, reine Anzeigecard — aber Labels zu klein |
| HA-Card: Barrierefreiheit | 2/5 | alt-Attribute teilweise leer, Kontrast nicht garantierbar |
| HA-Card: Mobile Lesbarkeit | 2/5 | 0.62em/0.7em Schriftgroessen auf Smartphone unlesbar |
| Pflege-Dashboard: Mobile-First | 3/5 | Grundstruktur responsiv, aber Action-Buttons zu klein |
| Pflege-Dashboard: Kiosk-Modus | 2/5 | IconButton size="small" nicht kiosk-tauglich |
| CareProfileEditDialog: Usability | 3/5 | Gute Struktur, aber Slider + 12 Monat-Buttons problematisch |
| CareProfileEditDialog: Mobile | 3/5 | fullScreen on mobile gesetzt, aber Slider-Bedienung hakelig |
| CareConfirmDialog: Usability | 4/5 | Klarer Fokus, guter Preset-Mechanismus |
| i18n-Konsistenz | 4/5 | Durchgehend i18n, kleiner Fehler bei ml/L-Label |

Die Implementierungen zeigen solides Handwerk: Theme-Integration, fullScreen-Dialoge auf Mobile, useMemo-Stabilisierung und die progressive Struktur des CareProfileEditDialog sind gut. Kritisch sind drei Bereiche: die Timeline-Schriftgroessen der HA-Card werden auf Smartphones unlesbar (0.62em), die Action-Buttons im Pflege-Dashboard verfehlen die Mindest-Touch-Target-Groesse fuer Kiosk-Szenarien erheblich (24px statt 64px), und das CareProfileEditDialog hat mit 18 unabhaengigen useState-Variablen eine Zustandsverwaltung, die bei Erweiterungen fehleranfaellig wird. Alle Probleme sind behebbar ohne architekturelle Aenderungen.

---

## Kritisch - Sofortiger Korrekturbedarf

### K-001: Timeline-Schriftgroessen unlesbar auf Smartphones
**Datei:** `custom_components/kamerplanter/www/kamerplanter-plant-card.js`, Zeile 363-385
**Bedienkontext:** Smartphone (HA Mobile App, Browser)
**Problem:**
Die Timeline verwendet drei verschiedene Schriftgroessen unterhalb der Lesbarkeitsgrenze:
- `.kp-step__name`: `font-size: 0.72em` (circa 11.5px bei 16px Basis)
- `.kp-step__date`: `font-size: 0.62em` (circa 9.9px)
- `.kp-step__duration`: `font-size: 0.62em` (circa 9.9px)

Auf einem Smartphone mit 360px Breite und 6 Phasen-Schritten hat jeder Step ca. 55px Breite. Bei `overflow-x: auto` scrollt die Timeline, aber die Labels bleiben nach wie vor bei 9-10px — das ist weit unterhalb der WHO-Empfehlung von mindestens 12px und der WCAG-Mindestanforderung fuer normale Textgroesse.

Die Detail-Tabellen-Header (`.kp-details__header`) haben ebenfalls `font-size: 0.7em` (ca. 11.2px), und `.kp-stats__label` liegt bei `0.7em`.

**Auswirkung:** Phasennamen, Startdaten und Dauern werden auf mobilen Geraeten de facto unlesbar. Da HA-Dashboards haeufig auf dem Smartphone genutzt werden (unterwegs, im Gewaechshaus), ist das ein echtes Nutzungsproblem.

**Loesung:** Absolute Mindestgroessen setzen, die nicht durch das Cascading unterschritten werden koennen:

```css
/* Statt relative em-Kaskaden: absolute rem-Mindestwerte */
.kp-step__name     { font-size: max(0.72em, 11px); }
.kp-step__date,
.kp-step__duration { font-size: max(0.65em, 10px); }
.kp-stats__label   { font-size: max(0.72em, 11px); }
.kp-details__header { font-size: max(0.72em, 11px); }
.kp-details__row   { font-size: max(0.88em, 13px); }
```

Besser: Timeline-Labels ab einer Kartenbreite unter 300px ausblenden und nur Marker + Icon zeigen (via Container Query oder ResizeObserver).

---

### K-002: Pflege-Dashboard Action-Buttons verfehlen Touch-Target-Mindestgroesse
**Datei:** `src/frontend/src/pages/pflege/PflegeDashboardPage.tsx`, Zeile 276-318
**Bedienkontext:** Kiosk, Mobile, Tablet
**Problem:**
Alle drei Aktionsbuttons pro Pflegekarte (Profil bearbeiten, Bestaetigen, Snooze) verwenden `size="small"` IconButtons. MUI IconButton small hat eine Standardgroesse von 24px Icon + minimales Padding = effektiv ca. 28-32px Touch-Target. Das ist weit unter dem empfohlenen Minimum von 48px (Standard-Mobile) und erst recht unter 64px (Kiosk-Modus gemaess UI-NFR-011).

Im Gewaechshaus mit nassen oder schmutzigen Haenden sind diese Buttons kaum treffsicher bedienbar. Der Abstand zwischen den drei Buttons betraegt `gap: 0.5` = 4px — auch das ist mit Handschuhen nicht differenzierbar.

**Auswirkung:** Fehlbedienungen (falscher Button getippt), Frustration, Arbeitsverzug. Das "Bestaetigen"-Feature — der wichtigste Workflow auf der Seite — wird unter Feldbedingungen zum Hindernis.

**Loesung:**
```tsx
// Vorher: size="small" mit gap={0.5}
<Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
  <IconButton size="small" ...>

// Nachher: Standard-Groesse mit ausreichendem Abstand
<Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
  <IconButton size="medium" ...>
  // IconButton medium = 40px Touch-Target — Mindeststandard Mobile
```

Fuer Kiosk-Modus gemaess UI-NFR-011 zusaetzlich:
```tsx
// Wenn kiosk-Modus aktiv (z.B. via URL-Parameter oder User-Setting):
<IconButton sx={{ minWidth: 64, minHeight: 64 }} ...>
```

Wireframe der verbesserten Card-Aktionszone:
```
+---------------------------------------------------+
|  [Icon] Pflanze XY        (Chip: Ueberfaellig)    |
|         Gaertnern (Typ)                           |
|         02.04.2026 (gestern)                      |
|                                                    |
|  [  Bearbeiten  ]  [  Bestaetigen  ]  [ Snooze ]  |
|   (40px min)        (40px min)        (40px min)  |
|   gap: 12px         gap: 12px                     |
+---------------------------------------------------+
```

---

### K-003: Timeline-Overflow ohne Hinweis auf Scrollbarkeit
**Datei:** `custom_components/kamerplanter/www/kamerplanter-plant-card.js`, Zeile 237-251
**Bedienkontext:** Smartphone, Tablet
**Problem:**
Die Timeline verwendet `overflow-x: auto` mit `scrollbar-width: none` (alle Browser). Das bedeutet: Bei mehr als 5-6 Phasen auf einem Smartphone (360px Breite) werden rechts liegende Phasen abgeschnitten und die Scrollbarkeit ist voellig unsichtbar. Der Nutzer sieht nicht, dass da noch mehr ist — und scroll-Gesten im HA-Dashboard koennen mit dem Page-Scroll interferieren (beide reagieren auf horizontales Swipe).

Bei 14 definierten Phasen (PHASE_LABELS) ist dieser Fall bei mehrjaehrigen Pflanzen (dormancy, juvenile, climbing, senescence) oder Vollzyklen realistisch.

**Auswirkung:** Phasenverlauf wird auf Smartphones unvollstaendig angezeigt ohne dass der Nutzer es merkt. Wichtige Phase-Uebergaenge werden unsichtbar.

**Loesung:**
Option A — Scroll-Indikator: Scrollbar nicht vollstaendig verstecken, sondern `scrollbar-width: thin` verwenden und/oder einen Fade-Gradient am rechten Rand einblenden:
```css
.kp-timeline-wrapper {
  position: relative;
}
.kp-timeline-wrapper::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 24px;
  background: linear-gradient(to right, transparent, var(--card-background-color, white));
  pointer-events: none;
}
```

Option B — Komprimierung: Ab mehr als 6 Phasen nur Marker ohne Labels anzeigen (Tooltip-on-hover bleibt moeglich), und die aktuelle Phase prominent in der Mitte platzieren.

Option C — Paginierung: "Zeige letzte 4 Phasen" mit Expand-Button. Einfachste Loesung fuer mobile Faelle.

---

## Unvollstaendig - Wichtige Aspekte fehlen

### U-001: CareProfileEditDialog - Kein Ladeindikator waehrend Profil-Fetch
**Datei:** `src/frontend/src/pages/pflege/PflegeDashboardPage.tsx`, Zeile 197-203
**Bedienkontext:** Mobile, Tablet, Kiosk
**Problem:**
Der Edit-Dialog oeffnet sich sofort, aber das Profil wird asynchron per `dispatch(fetchProfile({ plantKey }))` geladen. Die Komponente prueft `{currentProfile && editPlantKey}` als Render-Bedingung (Zeile 379) — das bedeutet der Dialog erscheint erst wenn das Profil geladen ist, aber es gibt keinen sichtbaren Lade-Feedback-State zwischen dem Klick auf "Bearbeiten" und dem Erscheinen des Dialogs.

Auf langsamen Verbindungen (Growraum mit schlechtem WLAN) kann das 1-3 Sekunden dauern. Der Nutzer tippt den Button und "nichts passiert" — typische Ursache fuer Doppelklick und Frustration.

**Loesung:**
```tsx
// In PflegeDashboardPage: Lade-State fuer Profile-Fetch
const [profileLoading, setProfileLoading] = useState(false);

const handleEditProfile = useCallback(async (plantKey: string) => {
  setProfileLoading(true);
  setEditPlantKey(plantKey);
  await dispatch(fetchProfile({ plantKey }));
  setProfileLoading(false);
  setEditDialogOpen(true);
}, [dispatch]);

// Im IconButton:
<IconButton
  size="medium"
  onClick={() => handleEditProfile(entry.plant_key)}
  disabled={profileLoading && editPlantKey === entry.plant_key}
>
  {profileLoading && editPlantKey === entry.plant_key
    ? <CircularProgress size={20} />
    : <EditIcon />}
</IconButton>
```

---

### U-002: CareConfirmDialog - ml/L-Label nicht internationalisiert
**Datei:** `src/frontend/src/pages/pflege/components/CareConfirmDialog.tsx`, Zeile 285-287
**Bedienkontext:** Alle
**Problem:**
Das Label `"ml/L"` ist als hartkodierter String ohne i18n-Schluesseln implementiert:
```tsx
<TextField label="ml/L" ...>
```
Alle anderen Beschriftungen in beiden Dialogen verwenden korrekt `t(...)`. Dieser Ausreisser unterbricht die i18n-Konsistenz und wuerde bei einer EN-Lokalisierung als "ml/L" unveraendert erscheinen (was zufallig korrekt ist, aber das Pattern bricht).

**Loesung:** `label={t('pages.pflege.mlPerLiter')}` und einen entsprechenden i18n-Key anlegen.

---

### U-003: HA-Card - Leere alt-Attribute bei Kami-Phasen-Icons in Timeline
**Datei:** `custom_components/kamerplanter/www/kamerplanter-plant-card.js`, Zeile 1070 und 1037
**Bedienkontext:** Screenreader, assistive Technologien
**Problem:**
In `_renderDetails()` haben alle Kami-SVG-Bilder leere alt-Attribute:
```javascript
${svg ? `<img src="${svg}" alt="" />` : ""}
```
In `_renderTimeline()` hat das aktuelle Phase-Icon ebenfalls ein leeres alt, waehrend der Phasenname als separater `kp-step__name`-Span vorhanden ist — das ist in diesem Fall akzeptabel (dekoratives Bild mit danebenliegendem Text). Fuer die Detail-Tabelle jedoch fehlt der Phasenname beim Bild-Alt komplett wenn kein Text-Fallback vorhanden ist.

In der Phasen-Detail-Tabelle steht das Bild vor dem Phasennamen-Text — fuer sehende Nutzer ist das kontextual, fuer Screenreader ist das Bild leer. Das ist aber nur dann ein Problem, wenn das Bild die einzige visuelle Unterscheidung waere. Da der Phasenname als Text folgt, ist `alt=""` hier vertretbar. Die Empfehlung bleibt: explizit dokumentieren warum `alt=""` gewollt ist (decorative).

**Loesung:** In `_renderDetails()` das `alt`-Attribut mit dem Phasennamen fuellen oder `role="presentation"` hinzufuegen:
```javascript
${svg ? `<img src="${svg}" alt="${escapeHtml(phaseLabel(p.name))}" role="img" />` : ""}
```

---

### U-004: CareProfileEditDialog - 18 separate useState ohne Formular-Abstraktion
**Datei:** `src/frontend/src/pages/pflege/components/CareProfileEditDialog.tsx`, Zeile 136-187
**Bedienkontext:** Alle (Entwickler-Usability, Wartbarkeit)
**Problem:**
Der Dialog verwaltet 18 separate useState-Aufrufe fuer Formularfelder. Das fuehrt zu:
1. Zweimal dieselbe Liste schreiben (einmal im useState-Init, einmal im useEffect zum Reset bei Dialog-Open, Zeile 193-215)
2. Einem useCallback mit 14 Abhaengigkeiten (Zeile 262-288)
3. Keiner zentralen Validierungslogik (aktuell keine Validierung)

Wenn weitere CareProfile-Felder hinzukommen (was gemaess REQ-022 v2.3 Outdoor-Erweiterungen wahrscheinlich ist: OverwinteringProfile-Felder, Phaenologie-Trigger), wird dieses Pattern schnell unkontrollierbar.

**Empfehlung:** Zusammenfassen in ein einziges `formState`-Objekt mit `useReducer` oder `useState`:
```tsx
const [form, setForm] = useState(() => ({
  careStyle: profile.care_style,
  wateringInterval: profile.watering_interval_days,
  // ... alle anderen Felder
}));

// Update-Helper:
const setField = useCallback(<K extends keyof typeof form>(key: K, value: typeof form[K]) => {
  setForm(prev => ({ ...prev, [key]: value }));
}, []);
```
Das reduziert den Reset-useEffect von 18 Zeilen auf eine Zeile und den handleSave-useCallback von 14 Abhaengigkeiten auf 2 (`form`, `profile.plant_key`).

---

### U-005: HA-Card - Keine ARIA-Live-Region bei Sensor-Updates
**Datei:** `custom_components/kamerplanter/www/kamerplanter-plant-card.js`, ab Zeile 782
**Bedienkontext:** Screenreader
**Problem:**
Die Card wird bei jedem `set hass(hass)` vollstaendig neu gerendert (DOM-Patching). Fuer Screenreader gibt es keine `aria-live`-Region, die auf Aenderungen hinweist. Da sich HA-Sensor-States regelmaessig aendern, kann das bei Screenreader-Nutzern zu staendigem Unterbrechungs-Rauschen fuehren — oder umgekehrt komplett lautlos bleiben.

**Loesung:** Das aktuelle Phase + Tage-Badge als `aria-live="polite"` markieren, alle anderen Bereiche als statisch lassen:
```javascript
// Im _ensureDom():
const daysEl = this.shadowRoot.getElementById("daysBadge");
daysEl.setAttribute("aria-live", "polite");
daysEl.setAttribute("aria-atomic", "true");
```

---

## Optimierungspotenzial - Verbesserungen empfohlen

### O-001: HA-Card - Days-Badge-Lesbarkeit auf kleinen Cards
**Aktuell:** `font-size: 1.15em; font-weight: 700` mit `<small>d</small>` bei `font-size: 0.6em`
**Problem:** Das "d" fuer "Tage" ist bei 0.6em * 1.15em * 16px = circa 11px schwer lesbar. Die Abkuerzung "d" ist zudem nur fuer deutschsprachige Nutzer intuitiv.
**Bessere Alternative:** "Tag 5" statt "5d" oder zumindest "5 d" mit Leerzeichen. Das verbessert auch die Screenreader-Ausgabe ("fuenf dee" vs. "fuenf Tage").

### O-002: Pflege-Dashboard - Urgency-Chips nehmen wertvollen Platz weg
**Aktuell:** Jede Card zeigt einen `Chip` mit dem Urgency-Label (z.B. "Ueberfaellig"), obwohl diese Information bereits durch den Section-Header (`Typography variant="h6"` in roter/gelber/blauer Farbe) kommuniziert wird.
**Problem:** Doppelte Information, verschwendet horizontalen Platz der fuer mobile Darstellung benoetigt wird.
**Bessere Alternative:** Chip nur anzeigen wenn der Eintrag in einer anderen Sektion als erwartet auftaucht (z.B. ein Eintrag aus einer anderen Gruppe), oder den Chip ganz weglassen und stattdessen einen farbigen linken Randstreifen auf der Card verwenden:
```tsx
<Card sx={{ mb: 1, borderLeft: 3, borderColor: urgencySectionColorMap[entry.urgency] }}>
```
Das spart Platz und kommuniziert Urgency visuell ohne Text.

### O-003: CareProfileEditDialog - Slider-Bedienung auf Touch unzuverlaessig
**Aktuell:** MUI Slider in `TaskTypeRow` mit `flex: 1`
**Problem:** MUI Sliders sind auf Touch-Geraeten mit feuchten Haenden notorisch unzuverlaessig. Der Draggable-Bereich des Thumbs ist 20px — weit unter dem Kiosk-Minimum von 64px. Im Gewaechshaus (feuchte Haende) wird der Slider-Thumb oft nicht getroffen.
**Bessere Alternative:** Neben dem Slider "+/-"-Buttons anbieten:
```tsx
<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
  <IconButton size="small" onClick={() => onChange(Math.max(min, value - 1))}>-</IconButton>
  <Slider ... />
  <IconButton size="small" onClick={() => onChange(Math.min(max, value + 1))}>+</IconButton>
  <Typography ...>{value} {unit}</Typography>
</Box>
```
Die Quick-Marks (1, 7, 14, 30) im Slider koennen alternativ als separate ToggleButtons ausserhalb des Sliders angeboten werden.

### O-004: CareConfirmDialog - "Futterdetails"-Abschnitt immer sichtbar fuer Watering
**Aktuell:** `showFeedingSection = FEEDING_TYPES.includes(reminderType)` => bei 'watering' immer expanded toggle sichtbar
**Problem:** Bei einem einfachen Giessvorgang ohne Duenger ist der "Futtermitteldetails"-Akkordeon-Toggle verwirrend — der Nutzer muss aktiv entscheiden ob er es aufklappt oder nicht.
**Bessere Alternative:** Default bleibt zugeklappt (aktuell korrekt wenn keine Presets), aber die Ueberschrift klarer formulieren: "Messungen & Naehrmittel (optional)" statt nur "Futtermitteldetails". Der `hasPresets`-Check der automatisch aufklappt ist gut — das sollte beibehalten werden.

### O-005: HA-Card - Stats-Label "Gesamtwoche" ohne i18n
**Aktuell:** Alle drei Stats-Labels sind hartkodiert deutsch: "Gesamtwoche", "Phasenwoche", "bis Ernte"
**Problem:** Die HA-Card hat keine i18n-Infrastruktur (kein i18next), aber die Kamerplanter-App ist fuer DE/EN konzipiert. Bei internationalen HA-Nutzern bleiben die Labels deutsch.
**Empfehlung:** Entweder PHASE_LABELS und Stats-Labels als konfigurierbares Objekt mit language-Parameter auslagern, oder die Labels aus HA-Sensor-Attributen beziehen (die serverseitig lokalisiert werden koennen).

### O-006: CareProfileEditDialog - Monat-Toggle-Buttons zu klein fuer Touch
**Aktuell:** `ToggleButton sx={{ px: 1, py: 0.25, minWidth: 32 }}` — das ergibt circa 32x28px Touch-Target
**Problem:** 12 eng gestapelte Monats-Buttons mit je 32px Breite und 28px Hoehe und `gap: 0.5` (4px) sind auf Mobile kaum treffsicher bedienbar. Das gilt sowohl fuer fertilizingActiveMonths als auch fuer locationCheckMonths.
**Loesung:** `py: 0.75, minWidth: 40` und `gap: 1` setzen. Auf sehr schmalen Viewports koennen die Monate als Zahlen in einer 4x3-Grid-Anordnung statt als flache Zeile dargestellt werden.

---

## Positiv - Best Practices gut umgesetzt

**HA-Card:**
- Konsequente Nutzung von CSS Custom Properties (`--primary-color`, `--secondary-text-color`, `--card-background-color`) — die Card passt sich automatisch an HA Light/Dark Theme an, ohne eigene Theme-Logik.
- Shadow DOM korrekt nur fuer die Card, nicht fuer den Editor (gemaess UI-NFR-015 R-021/R-022).
- `ha-form` + deklaratives Schema fuer den Editor (gemaess UI-NFR-015 R-001/R-002) — keine manuelle DOM-Manipulation im Editor.
- Lazy Loading Singleton `_haFormReadyPlant` korrekt implementiert (gemaess UI-NFR-015 R-006/R-007).
- `getGridOptions()` mit `min_columns: 3` verhindert zu schmale Darstellung im HA-Dashboard.
- `getCardSize()` gibt 8 zurueck — korrekte Schatzung fuer ein langes Card-Layout.
- `getStubConfig()` mit Geraete-Autodiscovery aus `hass.entities` — exzellente User Experience beim ersten Hinzufuegen der Card.
- HTML-Escaping via `escapeHtml()` fuer alle user-supplied Strings (Sicherheit).
- Transistions auf Progress-Fill (`transition: width 0.5s ease`) und Step-Markers (`transition: transform 0.2s ease`) — vermittelt visuelles Feedback.
- Pulse-Animation auf dem aktiven Step kommuniziert "lebt noch" auch fuer Nutzer die kurz weggeschaut haben.

**Pflege-Dashboard:**
- `LoadingSkeleton variant="card"` fuer den Loading-State — kein leerer Screen.
- `EmptyState` mit Illustration (`kamiCare`) und handlungsaufforderender Message fuer den Null-Zustand.
- Urgency-Gruppierung (`overdue` > `due_today` > `upcoming`) mit farbiger Section-Ueberschrift — visuelle Prioritaets-Hierarchie auf einen Blick.
- `formatDueDate()` mit relativem Indikator (gestern/heute/morgen/in N Tagen) — praxisnahe Darstellung.
- `useCallback`-Wrapping aller Handler korrekt mit vollstaendigen Dependency-Arrays.
- `useMemo` fuer das `grouped`-Objekt korrekt stabilisiert.
- `data-testid` auf allen interaktiven Elementen — gute Testabdeckbarkeit.
- `PrintButton` fuer Pflege-Checklisten-Export — durchdachte Offline-Nutzung.

**CareProfileEditDialog:**
- `fullScreen = useMediaQuery(theme.breakpoints.down('sm'))` — Vollbild-Dialog auf Mobile korrekt implementiert.
- `TaskTypeRow`-Subkomponente mit Toggle + Collapse-Animation — gute Progressivitaet (nur relevante Felder sichtbar wenn aktiviert).
- Accordion fuer Advanced-Settings und History — reduziert Komplexitaet fuer den Standardnutzer.
- History wird lazy geladen (nur beim ersten Expand) — `onChange={(_, expanded) => { if (expanded && history.length === 0) loadHistory(); }}`.
- Learned-Intervals als read-only Chips — transparente Anzeige was das adaptive System gelernt hat.
- Reset-Button in DialogActions mit `color="warning"` — visuell von "Speichern" differenziert, aber noch kein Bestaetigungs-Dialog (Risiko).

**CareConfirmDialog:**
- Preset-Mechanismus aus Naehrstoffplan (`defaultDosages`, `hasPresets`) — reduziert Eingabeaufwand erheblich.
- `defaultVolumeLiters` mit erklaerenden `volumeHint` — kontextsensitives Feedback ohne modale Unterbrechung.
- Target-EC/pH im Label anzeigen wenn vorhanden (`EC — Ziel: 2.1 mS/cm`) — Soll-Ist-Vergleich direkt im Feld-Label.
- `inputMode: 'decimal'` auf numerischen Felder — korrekte Tastatur auf iOS.
- Fertilizer-Redux-Fetch nur wenn nicht via Prop bereitgestellt (`availableFertilizers`-Fallback) — flexible API.

---

## Kiosk-Modus - Detailbewertung

### Bedienbarkeit mit eingeschränkter Motorik

| Szenario | Bewertung | Anmerkung |
|----------|-----------|-----------|
| Bedienung mit Handschuhen (Pflege-Dashboard) | Unzureichend | IconButton size="small" = ca. 28-32px, zu klein |
| Bedienung mit nassen Haenden (Pflege-Dashboard) | Unzureichend | Slider in CareProfileEditDialog nicht bedienbar |
| Bedienung mit verschmutzten Haenden (Alle) | Unzureichend | Gleiche Probleme wie nasse Haende |
| Bedienung mit Nase/Ellenbogen (Notfall) | Nicht moeglich | Targets zu klein fuer grobe Motorik |
| Bedienung mit nur einer Hand (Dashboard) | Akzeptabel | Layout ist vertikal, Buttons erreichbar aber klein |
| HA-Card (reine Anzeige) | Akzeptabel | Keine Interaktion noetig, nur Lesbarkeit relevant |

### Kiosk-Workflows - Kritische Pfade

| Workflow | Schritte (Soll) | Schritte (Ist) | Bewertung |
|----------|:---------------:|:--------------:|-----------|
| Pflegeerinnerung bestaetigen | 2 | 3 (Klick Button → Dialog → Confirm) | Akzeptabel |
| Pflegeerinnerung snoozen | 1 | 1 (direkter API-Call) | Gut |
| Care-Profile oeffnen | 2 | 2-3 (Klick → Ladewartezeit → Dialog) | Ausbaufaehig |
| Giessen mit Naehrstoff-Erfassung | 4 | 5 (Klick → Dialog → Expand → Felder → Confirm) | Akzeptabel |

---

## Responsive-Matrix

| Komponente | Mobile (Smartphone) | Tablet | Desktop | Kiosk |
|------------|:-------------------:|:------:|:-------:|:-----:|
| HA-Card: Header | Gut | Gut | Gut | Gut (nur Anzeige) |
| HA-Card: Stats | Gut | Gut | Gut | Gut (nur Anzeige) |
| HA-Card: Progress | Gut | Gut | Gut | Gut |
| HA-Card: Timeline (<=6 Phasen) | Akzeptabel | Gut | Gut | Nicht relevant |
| HA-Card: Timeline (>6 Phasen) | Unzureichend | Akzeptabel | Gut | Nicht relevant |
| HA-Card: Schriftgroessen | Unzureichend | Akzeptabel | Gut | Nicht relevant |
| Pflege-Dashboard: Liste | Gut | Gut | Gut | Unzureichend |
| Pflege-Dashboard: Action-Buttons | Akzeptabel | Akzeptabel | Gut | Unzureichend |
| CareProfileEditDialog: Layout | Gut (fullScreen) | Gut | Gut | Unzureichend |
| CareProfileEditDialog: Slider | Unzureichend | Akzeptabel | Gut | Nicht nutzbar |
| CareProfileEditDialog: Monat-Buttons | Unzureichend | Akzeptabel | Gut | Nicht nutzbar |
| CareConfirmDialog: Layout | Gut (fullScreen) | Gut | Gut | Akzeptabel |
| CareConfirmDialog: Felder | Gut | Gut | Gut | Akzeptabel |

---

## Touch-Target-Audit

| Komponente | Ist-Groesse | Soll Mobile (48px) | Soll Kiosk (64px) | Bewertung |
|-----------|:-----------:|:------------------:|:-----------------:|-----------|
| Pflege-Dashboard: Confirm-Button (small) | ~28-32px | 48px | 64px | Unzureichend |
| Pflege-Dashboard: Snooze-Button (small) | ~28-32px | 48px | 64px | Unzureichend |
| Pflege-Dashboard: Edit-Button (small) | ~28-32px | 48px | 64px | Unzureichend |
| CareConfirmDialog: Bestaetigen-Button (contained) | ~36px Hoehe | 48px | 64px | Akzeptabel |
| CareProfileEditDialog: Save-Button (contained) | ~36px Hoehe | 48px | 64px | Akzeptabel |
| CareProfileEditDialog: Monat-Buttons (32x28px) | ~28px | 48px | 64px | Unzureichend |
| CareProfileEditDialog: Slider-Thumb | ~20px | 48px | 64px | Unzureichend |
| CareProfileEditDialog: Delete-Fertilizer (small) | ~28px | 48px | 64px | Unzureichend |
| HA-Card: Keine interaktiven Elemente | n/a | n/a | n/a | Nicht relevant |

---

## Empfehlungen

### Sofort umsetzbar (Quick Wins)

1. **IconButton size auf "medium" anheben** (alle drei Buttons in renderCard): 2 Zeilen Code, behebt K-002 fuer Mobile. Kiosk-Verbesserung erfordert zusaetzlich `minHeight: 56`.

2. **Timeline-Schriftgroessen mit `max()` absichern**: 4 CSS-Zeilen in kamerplanter-plant-card.js, verhindert unlesbare Labels auf Smartphones.

3. **ml/L i18n-Key anlegen**: 1 Zeile in CareConfirmDialog.tsx + 1 Translation-Eintrag, schliesst i18n-Luecke (U-002).

4. **Urgency-Chip entfernen, stattdessen Karten-Randfarbe**: Reduziert Platzverbrauch auf Mobile, verbessert Scan-Geschwindigkeit (O-002).

5. **Reset-Button im CareProfileEditDialog mit Bestaetigungs-Dialog schuetzen**: Eine ungewollte Zuruecksetzung aller gelernten Intervalle ist destruktiv. `window.confirm()` oder ein kleiner AlertDialog als Zwischenschritt.

### Mittelfristig (Naechste Entwicklungsphase)

1. **+/- Stepper-Buttons neben Slidern**: Bedienbarkeit auf Touch und Kiosk verbessern. Benoetigt Anpassung der `intervalSlider`-Hilfsfunktion in CareProfileEditDialog.

2. **18 useState zu einem formState-Objekt zusammenfassen**: Technische Schuld in CareProfileEditDialog abbauen, bevor weitere Outdoor-Felder hinzukommen (U-004).

3. **Profil-Fetch Loading-State sichtbar machen**: Vermeide "nichts passiert"-Momente nach Button-Klick (U-001).

4. **HA-Card: Fade-Gradient fuer Timeline-Overflow**: Macht horizontale Scrollbarkeit sichtbar ohne die Scrollbar anzuzeigen.

5. **Monat-Buttons in 4x3 Grid umbauen**: Bessere Touch-Treffsicherheit auf kleinen Viewports.

### Langfristig / Strategisch

1. **Kiosk-Modus fuer Pflege-Dashboard**: Gemaess UI-NFR-011 einen dedizierten Kiosk-Darstellungsmodus implementieren. Die wichtigsten Kiosk-Aktionen (Giessen bestaetigen, Snooze) als grosse Kacheln (min. 80x80px) auf einer vereinfachten Ansicht.

2. **HA-Card i18n**: Sprache aus HA-Frontend (`hass.language`) auslesen und Labels entsprechend setzen. Das ermoeglicht internationale Nutzung ohne Code-Aenderung.

3. **CareConfirmDialog als Bottom-Sheet auf Mobile**: Statt `fullScreen`-Dialog waere ein MUI-Drawer von unten natuerlicher fuer schnelle Aktions-Bestaetigung auf dem Smartphone (reduziert Kontextwechsel-Gefuehl).

---

## Fehlende Spezifikationen

| Thema | Beschreibung | Empfehlung |
|-------|-------------|------------|
| HA-Card: Mindest-Schriftgroessen | Keine Vorgabe in UI-NFR-015 fuer lesbare Karteninhalte | Ergaenzung in UI-NFR-015: min. 11px fuer sekundaere Labels, min. 13px fuer primaere Inhalte |
| Kiosk-Modus: Pflege-Dashboard | UI-NFR-011 definiert Kiosk-Anforderungen, aber PflegeDashboardPage hat keine kiosk-spezifische Variante | Kiosk-Ansicht als separate Route oder URL-Parameter dokumentieren |
| Touch-Target-Groessen: HA-Cards | UI-NFR-011 gilt fuer das React-Frontend; kein aequivalentes Dokument fuer HA-Cards | UI-NFR-015 um Display-Lesbarkeits-Anforderungen fuer HA-Cards erweitern |
| CareConfirmDialog: Validierung | Keine Validierungsregeln fuer Volume (max. realistischer Wert?), EC (0-10?), pH (0-14 ist definiert) | Validierungsregeln in REQ-022 ergaenzen |
| Reset-Aktion: Bestaetigungspflicht | Kein UI-NFR das destruktive Aktionen (Reset Learning) unter Bestaetigungspflicht stellt | In UI-NFR-004 (Feedback) ergaenzen: destruktive Aktionen mit Confirmation-Dialog |

---

## Glossar

- **Touch-Target**: Beruhrbarer Bereich eines interaktiven UI-Elements. Bei MUI IconButton "small" ist der Touch-Target die gesamte Box inklusive Padding, typisch 28-34px je nach Browser-Rendering.
- **Kiosk-Modus**: Vereinfachte Bedienoberfaeche fuer Standort-Tablets im Gewaechshaus. Definiert in UI-NFR-011 mit Mindest-Touch-Target von 64px.
- **CSS Custom Properties**: Variablen in CSS (`--primary-color`). Home Assistant definiert ein Set von Theme-Variablen die von Custom Cards konsumiert werden sollen.
- **Shadow DOM**: Web-Komponenten-Isolation. Der interne DOM einer Card ist vom Seiten-DOM getrennt — CSS-Variablen werden aber durch das Shadow DOM hindurch geerbt.
- **fullScreen-Dialog**: MUI-Dialog der auf kleinen Viewports den gesamten Bildschirm belegt. Korrekte Pattern fuer mobile Formulareingabe.
- **ha-form**: Home Assistant Frontend-Komponente die ein deklaratives Schema-Array als Formular rendert. Offizieller Standard fuer Lovelace-Card-Editoren.
- **Urgency**: Dringlichkeitsstufe einer Pflegeerinnerung (overdue/due_today/upcoming). Im Dashboard als Section-Gruppierung und Chip-Label kommuniziert.
