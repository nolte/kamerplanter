# Frontend-Design-Review: REQ-045 — Individualisierbares Dashboard & Widget-Personalisierung
**Erstellt von:** Frontend-Design-Reviewer (Subagent)
**Datum:** 2026-07-04
**Fokus:** Responsive Design · Barrierefreiheit (Drag-and-Drop-Alternative) · Kiosk-Abgrenzung · Bearbeiten-Modus-UX · Bundle-Budget
**Analysierte Dokumente:** `spec/req/REQ-045_Individualisierbares-Dashboard.md`, `spec/req/REQ-009_Dashboard.md` (v2.1), `spec/req/REQ-042_Modulare-Feature-Sichtbarkeit.md`, `spec/req/REQ-021_UI-Erfahrungsstufen.md`, `spec/ui-nfr/UI-NFR-001_Responsive-Design.md`, `spec/ui-nfr/UI-NFR-002_Barrierefreiheit.md`, `spec/ui-nfr/UI-NFR-003_Performance.md`, `spec/ui-nfr/UI-NFR-019_Kiosk-Modus.md`; Code-Glance: `src/frontend/src/pages/DashboardPage.tsx`, `src/frontend/src/pages/auth/ModulesSettingsTab.tsx`, `src/frontend/src/config/moduleCatalog.ts`, `src/frontend/src/api/types.ts`

> **Status (2026-07-04): aufgelöst.** Alle kritischen und wichtigen Findings sind in REQ-045 v1.1/v1.2
> eingearbeitet (K-001, K-002, U-001–U-006, O-001, O-003). Die drei strategischen UI-NFR-Empfehlungen wurden
> umgesetzt: **UI-NFR-002 R-024..R-027** (Drag-and-Drop-Alternativen, Handles nicht im Tab-Index,
> Meaningful Sequence dynamischer Grids, ARIA-Live bei Reorder) und **UI-NFR-003 R-028** (route-spezifisches
> Bundle-Budget). Verbleibendes Implementierungs-Follow-up in Issue #368.

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Responsive Design (Mobile) | ⭐⭐⭐⭐☆ | Mobile-Stapelung + DnD-Deaktivierung durchdacht; Touch-Target-Wert widerspricht UI-NFR-001 |
| Responsive Design (Tablet/Desktop) | ⭐⭐⭐☆☆ | Kein Wort zu Resize-Handle-Größe auf Touch-Tablets |
| Kiosk-Abgrenzung | ⭐⭐⭐⭐⭐ | Sauber, mehrfach explizit ausgenommen, keine Widersprüche gefunden |
| Barrierefreiheit — Settings-Alternative | ⭐⭐⭐☆☆ | Reorder-/Resize-Buttons vorhanden, aber Fokus-/Live-Region-/DOM-Order-Fragen ungeklärt |
| Barrierefreiheit — Bearbeiten-Modus | ⭐⭐☆☆☆ | Direktmanipulationsfläche selbst ist laut Spec-Text nicht tastaturbedienbar (nur Settings ist es) |
| Bearbeiten-Modus-UX / Discoverability | ⭐⭐⭐☆☆ | Kein Onboarding-Hinweis, kein sichtbarer Einstiegspunkt von `/dashboard` zu Settings-Config |
| Bundle-Budget (UI-NFR-003) | ⭐⭐☆☆☆ | Interner Widerspruch: §3.4 verspricht Lazy-Load "erst im Bearbeiten-Modus", §3.9 lädt react-grid-layout aber auch read-only bei jedem Dashboard-Aufruf |
| Empty-/Error-States | ⭐⭐⭐☆☆ | Error-Isolation gut spezifiziert; Leer-Dashboard (0 Widgets) nicht behandelt |

**Gesamteinschätzung:** REQ-045 ist strukturell sehr sauber an das erprobte REQ-042-Muster (Katalog/Registry/Contract-Test/localStorage-Migration) angelehnt und trennt Kiosk vs. Standard-Dashboard vorbildlich. Die größte Schwäche liegt darin, dass Barrierefreiheit nur als Querverweis ("Fokusführung; ARIA für Grid-Items") erwähnt, aber an keiner Stelle im Fließtext, in der Technik-Sektion oder in den Testszenarien konkretisiert wird — insbesondere fehlt eine Aussage dazu, was ein Tastaturnutzer *innerhalb* des Bearbeiten-Modus auf `/dashboard` selbst tun kann. Zusätzlich widerspricht sich die Spec bei der Bundle-Budget-Mitigation selbst (§3.4 vs. §3.9), was das zentrale Performance-Argument für den Einsatz von react-grid-layout entwertet.

---

## 🔴 Kritisch — Sofortiger Korrekturbedarf

### K-001: Bundle-Budget-Mitigation widerspricht sich selbst (§3.4 vs. §3.9)
**Anforderung:** §3.4: *"eine Registry … die jedem WidgetKey eine lazy geladene React-Komponente zuordnet (Bundle-Budget UI-NFR-003, §5)"* und §5-Dependency-Zeile: *"`react-grid-layout` und Widget-Komponenten lazy; nur im Dashboard-Chunk / **erst im Bearbeiten-Modus geladen**"* — versus §3.9: *"`DashboardPage.tsx` rendert das effektive Layout … über `react-grid-layout` (**Read-Only außerhalb des Bearbeiten-Modus**)"*.
**Bedienkontext:** 🌐 Multi-Kontext — betrifft jeden `/dashboard`-Aufruf, nicht nur den Editiervorgang.
**Problem:** Wenn `react-grid-layout` auch für die reine Read-Only-Darstellung verwendet wird, lädt es bei **jedem** Besuch der Startseite — nicht "erst im Bearbeiten-Modus", wie an anderer Stelle als Mitigation für das 300-KB-Bundle-Budget (UI-NFR-003) versprochen wird. `/dashboard` ist die häufigst aufgerufene Seite der App (Post-Login-Landingpage), FCP/LCP/TTI-Ziele (UI-NFR-003 R-001–003) gelten hier am schärfsten.
**Auswirkung:** Die im DoD behauptete Einhaltung des 300-KB-Budgets ("react-grid-layout … lazy; 300-KB-Budget des Dashboard-Chunks eingehalten") ist mit dem in §3.9 beschriebenen Rendering-Ansatz nicht erreichbar — react-grid-layout (+ Kern-Abhängigkeiten react-draggable/react-resizable) liegt real bei ca. 35–50 KB gzip und würde bei jedem Seitenaufruf mitgeladen.
**Lösungsvorschlag:** Read-Only-Darstellung **ohne** react-grid-layout implementieren — z.B. reines CSS-Grid (`grid-column`/`grid-row` aus `x/y/w/h` berechnet, DOM-Reihenfolge = Widget-Array-Reihenfolge). `react-grid-layout` (+ react-draggable/react-resizable) wird dann tatsächlich erst per `React.lazy()` beim Aktivieren des "Bearbeiten"-Toggles nachgeladen. Das löst gleichzeitig K-002 (DOM-Order/Screenreader-Reihenfolge).

### K-002: Touch-Target-Wert widerspricht UI-NFR-001 (44px vs. 48px MUSS)
**Anforderung:** REQ-045 §5 und DoD: *"Touch-Targets ≥ 44 px"* (zweimal).
**Bedienkontext:** 📱 Mobile / 📋 Tablet.
**Problem:** UI-NFR-001 R-011 definiert für das gesamte Frontend verbindlich (MUSS) **48×48px** als Mindestgröße für Touch-Targets; 36px ist nur auf Desktop mit Maus-Fokus zulässig (R-013). REQ-045 zitiert stattdessen den WCAG-2.5.5-AA-Wert (44px), der niedriger ist als der projektweite Standard.
**Auswirkung:** Entwickler, die sich strikt an REQ-045 halten, bauen Reorder-/Resize-Buttons und Widget-Toggle-Switches mit 44px — das unterläuft den projektweiten UI-NFR-001-Standard und würde in einem Accessibility-/Design-System-Audit als Regression auffallen (vgl. wie `ModulesSettingsTab.tsx` bereits explizit auf 44/48px kommentiert).
**Lösungsvorschlag:** REQ-045 auf **48×48px** (UI-NFR-001 R-011) korrigieren, konsistent mit dem Rest der Spec-Referenzen im Repository.

---

## 🟠 Unvollständig — Wichtige Aspekte fehlen

### U-001: Bearbeiten-Modus selbst ist laut Spec-Text nicht tastaturbedienbar
**Bedienkontext:** 🖥️ Desktop / 📋 Tablet (mit angeschlossener Tastatur).
**Fehlende Spezifikation:** Design-Prinzip erklärt explizit: *"Konfiguration in den Einstellungen (Primärfläche) … Das ist die verbindliche, vollständig tastaturbedienbare Konfigurationsfläche."* Der Bearbeiten-Modus auf `/dashboard` selbst wird nirgends als tastaturbedienbar beschrieben — react-grid-layout-Drag-Handles sind reine Maus-/Touch-Interaktion. Es fehlt eine Aussage dazu, was passiert, wenn ein Tastaturnutzer den "Bearbeiten"-Toggle aktiviert: Bekommt er fokussierbare, aber funktionslose Drag-Handles (WCAG 2.1.1/4.1.2-Risiko)? Oder ist der Toggle selbst per `aria-disabled`/Hinweistext auf "nur Maus/Touch" beschränkt, mit sichtbarem Link zu Settings?
**Begründung:** Ohne diese Festlegung besteht das reale Risiko, dass react-grid-layout-DOM-Elemente (`.react-draggable`, `.react-resizable-handle`) im Tab-Index landen, aber auf Tastendruck nichts tun — ein klassischer, in Audits häufig gefundener A11y-Fehler bei DnD-Bibliotheken.
**Vorschlag:**
```
Bearbeiten-Modus (Desktop, Tastaturfokus auf Widget-Karte):
┌───────────────────────────────────────┐
│ 🌡️ Sensor Live            [⋮ Menü]  │  ← Kebab-Menü statt Drag-Handle
│                                       │     im Tab-Index; öffnet Popover:
│  [Werte …]                            │     "↑ Nach oben" "↓ Nach unten"
│                                       │     "− Kleiner" "+ Größer"
└───────────────────────────────────────┘     "⚙ Konfigurieren" (falls hasConfig)
```
Drag-Handle selbst erhält `tabIndex={-1}` (nicht fokussierbar), das Kebab-Menü liefert die vollständige Tastatur-Parität direkt in-place — ohne Navigation zu Settings.

### U-002: Kein Umgang mit DOM-Order vs. visueller Grid-Position (Screenreader-Lesereihenfolge)
**Bedienkontext:** 🌐 Multi-Kontext (betrifft Screenreader unabhängig vom Gerät).
**Fehlende Spezifikation:** `x`/`y` bestimmen die visuelle Position, `widgets`-Array-Reihenfolge nur den Mobile-Stacking-Fallback. Es fehlt eine Festlegung, dass die **DOM-Reihenfolge** (und damit Tab-/Screenreader-Reihenfolge) auf Desktop/Tablet ebenfalls der logischen Array-Reihenfolge folgt — unabhängig von `x/y`. react-grid-layout positioniert Kinder standardmäßig absolut nach `x/y`, DOM-Reihenfolge = Einfügereihenfolge der `children`-Prop; wird diese nicht explizit an die visuelle Lesereihenfolge gekoppelt, können Screenreader-Nutzer Widgets in einer Reihenfolge vorgelesen bekommen, die nicht der visuellen "oben-links-zuerst"-Anordnung entspricht.
**Begründung:** WCAG 2.1 SC 1.3.2 (Meaningful Sequence) — Kernanforderung von UI-NFR-002 R-004 ("Tab-Reihenfolge MUSS der visuellen Lesereihenfolge entsprechen").
**Vorschlag:** Explizite Regel ergänzen: *"Die `children`-Prop von `react-grid-layout` MUSS nach `(y, x)` sortiert an die DOM übergeben werden — unabhängig von der Einfügereihenfolge im `widgets`-Array."*

### U-003: Leer-Dashboard (0 Widgets) nicht spezifiziert
**Bedienkontext:** 🌐 Multi-Kontext.
**Fehlende Spezifikation:** DoD erlaubt uneingeschränktes Entfernen von Widgets ("Hinzufügen/Entfernen: Nutzer kann Widgets … an-/abwählen"). Es gibt keine Minimum-Widget-Regel und keinen spezifizierten Empty-State für den Fall `dashboard_layout.widgets == []`. Ein Nutzer könnte versehentlich alle Widgets deaktivieren und landet auf einer leeren `/dashboard`-Seite ohne Handlungsaufforderung.
**Begründung:** UI-NFR-003 R-006 verlangt für Ladezustände "keine leeren Seiten" — analog sollte auch für den *bewusst leeren* Zustand ein Empty-State mit CTA existieren, sonst wirkt die App nach dem letzten Widget-Entfernen "kaputt".
**Vorschlag:**
```
┌─────────────────────────────────────────┐
│                                         │
│         📋  Dein Dashboard ist leer     │
│                                         │
│   Füge Widgets aus dem Katalog hinzu,   │
│   um deine Startseite zu gestalten.     │
│                                         │
│   [ Widgets auswählen ]  [ Standard     │
│                            wiederherst. ]│
└─────────────────────────────────────────┘
```

### U-004: Kein sichtbarer Einstiegspunkt von `/dashboard` zu `Einstellungen → Dashboard`
**Bedienkontext:** 🌐 Multi-Kontext (Discoverability).
**Fehlende Spezifikation:** Die Personalisierungs-Primärfläche (`/settings#dashboard`) wird nur über die generische Einstellungen-Navigation erreicht. §3.8 erwähnt keinen direkten Link/Icon auf `/dashboard` selbst (z.B. Zahnrad-Icon im Seiten-Header neben "Bearbeiten"-Toggle), der gezielt zur Dashboard-Settings dorthin führt. Für Widgets mit `hasConfig` (z.B. Standortauswahl bei `sensor_live`) ist unklar, ob der Konfigurations-Dialog auch inline aus dem Bearbeiten-Modus heraus erreichbar ist oder zwingend über Settings navigiert werden muss.
**Begründung:** Ein Feature, das nur über einen mehrstufigen Menüpfad (Einstellungen → Tab "Dashboard") erreichbar ist, wird erfahrungsgemäß von einem großen Teil der Nutzer nie gefunden.
**Vorschlag:** Auf `/dashboard` neben dem "Bearbeiten"-Toggle einen zweiten Icon-Button "⚙ Widgets verwalten" mit Deep-Link zu `/settings#dashboard` ergänzen; zusätzlich pro Widget im Bearbeiten-Modus ein Kebab-Menü mit direktem "Konfigurieren"-Eintrag (öffnet denselben Dialog wie Settings, ohne Navigation).

### U-005: Kein First-Use-Hinweis / Onboarding-Bezug (REQ-020)
**Bedienkontext:** 📱 Mobile / 🖥️ Desktop (Erstnutzung).
**Fehlende Spezifikation:** REQ-045 wird nirgends mit dem Onboarding-Wizard (REQ-020) verknüpft, obwohl `onboarding_progress` als Default-Widget für Beginner existiert. Es fehlt ein einmaliger Coachmark/Tooltip beim ersten Dashboard-Besuch, der auf die Personalisierbarkeit hinweist.
**Begründung:** Ohne Discoverability-Maßnahme bleibt das aufwendig gebaute Feature für einen Großteil der Beginner-Nutzer unsichtbar — besonders relevant, da Beginner das kleinste Widget-Set sehen und am meisten von zusätzlichen Widgets profitieren könnten.
**Vorschlag:** Ergänzung eines einmaligen, dismissable Hinweis-Banners/Coachmarks (localStorage-Flag `dashboard_personalization_hint_dismissed`).

### U-006: Fehlende Aussage zur Größe des Resize-Handles (Touch)
**Bedienkontext:** 📋 Tablet (Touch, Standard-Modus — nicht Kiosk).
**Fehlende Spezifikation:** react-grid-layout rendert standardmäßig ein kleines `.react-resizable-handle` (typischerweise ~20×20px, unteres rechtes Eck). REQ-045 sagt nichts zur notwendigen CSS-Anpassung dieses Handles auf mindestens 48×48px (UI-NFR-001 R-011), obwohl der Bearbeiten-Modus laut DoD "per Maus/Touch verschieben und in der Größe … ändern" explizit für Touch vorgesehen ist.
**Begründung:** Ein zu kleines Resize-Handle ist auf Tablets mit Finger praktisch nicht präzise treffbar.
**Vorschlag:** Explizite CSS-Override-Regel für `.react-resizable-handle` auf min. 48×48px Touch-Fläche mit vergrößertem, aber optisch kleinerem Sichtbereich (größere unsichtbare Hit-Area analog zu MUI `IconButton`-Padding-Pattern).

---

## 🟡 Optimierungspotenzial

### O-001: Request-Waterfall beim Initial-Load (Catalog → Layout → Aggregated)
**Aktuelle Spezifikation:** Drei potenziell sequenzielle Endpunkte (`GET user-preferences`, `GET dashboard/widgets/catalog`, `GET dashboard/aggregated?widgets=…`).
**Problem:** Falls diese drei Calls sequenziell statt parallel ausgeführt werden, verlängert sich die Time-to-Interactive der meistbesuchten Seite der App — Konflikt mit UI-NFR-003 TTI<3.5s.
**Bessere Alternative:** `catalog` und `user-preferences` parallel laden (kein Abhängigkeitsverhältnis), `aggregated` mit den *rohen* `widget_key`s aus `dashboard_layout.widgets` sofort parallel mitstarten (nicht auf `catalog.available` warten) und erst beim Rendern client-seitig gegen `catalog` filtern. Sollte in §3.2/§3.9 explizit als "parallel, nicht sequenziell" festgehalten werden.

### O-002: `daily_tip`- und `community_activity`-Sonderfälle im Settings-Tab nicht visuell demonstriert
**Aktuelle Spezifikation:** §3.3 beschreibt `available=false` mit `unavailable_reason` generisch als "ausgegraut mit Begründung".
**Problem:** Für Light-Modus-spezifische Begründungen fehlt ein konkretes Wireframe/Beispiel; Entwickler könnten Begründungstexte zu technisch formulieren.
**Bessere Alternative:** Ein Beispiel-Wireframe mit konkretem, laienverständlichem `unavailable_reason`-Text (z.B. *"Nicht verfügbar im Light-Modus — kostenlose KI-Funktion erst nach Registrierung"*).

### O-003: Kein Hinweis auf `prefers-reduced-motion` bei Drag/Resize-Animationen
**Aktuelle Spezifikation:** Keine.
**Problem:** react-grid-layout animiert Widget-Verschiebungen standardmäßig per CSS-Transition; UI-NFR-002 R-022 verlangt Respektierung von `prefers-reduced-motion`.
**Bessere Alternative:** Regel ergänzen, dass die CSS-Transition-Dauer bei `prefers-reduced-motion: reduce` auf 0 gesetzt wird (react-grid-layout `transitionDuration`-Prop-Override).

---

## 🟢 Positiv — Best Practices eingehalten

- **Kiosk-Abgrenzung ist sauber und mehrfach redundant abgesichert:** explizit in Business Case ("Abgrenzung"), in §5-Dependency-Zeile ("ausgenommen"), im DoD und in keinem der 8 Testszenarien vermischt — kein Widerspruch zu UI-NFR-019.
- **Mobile-Fallback ist konsistent zu Ende gedacht:** Sowohl im Bearbeiten-Modus als auch im Settings-Tab stehen unter 600px dieselben Reorder-Buttons zur Verfügung.
- **Set-Semantik und Toleranz gegenüber unbekannten Widget-Keys** ist 1:1 vom bewährten REQ-042-Muster übernommen (Contract-Test, `KNOWN_WIDGET_KEYS`, Sanitize-and-Log statt Hard-Reject).
- **Fehler-Isolation pro Widget** (ErrorBoundary + Retry) ist explizit übernommen und in Testszenario 8 verifizierbar.
- **Reset-Semantik** (`null` vs. "unset" über `exclude_unset=True`) ist technisch präzise und vermeidet einen Silent-Bug.
- **Gating-Kaskade** (REQ-042 + REQ-024 + REQ-027) wird konsistent über einen einzigen serverautoritativen `available`-Flag aufgelöst.

---

## Kiosk-Modus — Abgrenzung (Detailprüfung)

| Prüfpunkt | Ergebnis |
|-----------|----------|
| `/kiosk` bleibt festes Layout | ✅ explizit in Business Case, §5, DoD |
| Personalisierungs-Endpunkte auch unter `/kiosk` erreichbar? | ⚠️ nicht explizit ausgeschlossen — DoD sagt nur "`/kiosk` bleibt unverändert", spezifiziert aber nicht, dass die Kiosk-Startseite **keinen** Aufruf von `GET …/dashboard/widgets/catalog` oder `dashboard_layout` auslöst |
| Kiosk-Quick-Actions unverändert | ✅ konsistent mit UI-NFR-019 R-015 |
| Gemeinsamer Code-Pfad Risiko (`WinterProtectionWidget` als erster Registry-Eintrag) | ⚠️ zu prüfen, ob dieselbe Komponente künftig auch auf `/kiosk` verwendet wird (aktuell nicht vorgesehen, aber nicht explizit ausgeschlossen) |

**Empfehlung:** Expliziten DoD-Punkt ergänzen: *"Kein Aufruf von `dashboard/widgets/catalog` oder `PATCH dashboard_layout` von `/kiosk` aus — Kiosk-Startseite nutzt ausschließlich die in UI-NFR-019 §2.10 definierten Quick-Action-Komponenten."*

---

## Responsive-Matrix

| Aspekt | 📱 Mobile (<600px) | 📋 Tablet (600–1199px) | 🖥️ Desktop (≥1200px) | 🖲️ Kiosk |
|--------|:---:|:---:|:---:|:---:|
| Widget-Anordnung (DnD) | ❌ (bewusst deaktiviert) | ✅ | ✅ | 🚫 n/a (ausgenommen) |
| Widget-Anordnung (Buttons) | ✅ inline + Settings | 🔲 nur Settings spezifiziert | 🔲 nur Settings spezifiziert | 🚫 n/a |
| Resize (Drag-Handle) | ❌ (kein Sinn bei 1 Spalte) | 🔲 Handle-Größe nicht spezifiziert (U-006) | ✅ | 🚫 n/a |
| Resize (Stepper-Buttons) | ✅ Settings | ✅ Settings | ✅ Settings | 🚫 n/a |
| Per-Widget-Konfiguration | 🔲 nur Settings, kein Inline-Zugriff (U-004) | 🔲 gleich | 🔲 gleich | 🚫 n/a |
| Touch-Target-Wert | ❌ Spec nennt 44px statt 48px (K-002) | ❌ gleich | n/a (Maus) | 🚫 n/a |
| Empty-State (0 Widgets) | ❌ nicht spezifiziert (U-003) | ❌ | ❌ | 🚫 n/a |

✅ = spezifiziert & geeignet · 🔲 = teilweise/unklar · ❌ = nicht spezifiziert/lückenhaft · 🚫 n/a = bewusst ausgenommen (korrekt)

---

## Empfehlungen

### Sofort umsetzbar (Quick Wins)
1. **K-002 korrigieren:** "44 px" → "48 px" in §5 und DoD, konsistent mit UI-NFR-001 R-011.
2. **K-001 auflösen:** Read-Only-Rendering explizit von react-grid-layout entkoppeln (CSS-Grid ohne DnD-Library), damit die Lazy-Load-Behauptung tatsächlich zutrifft.
3. **U-003:** Empty-State-Wireframe für "0 Widgets" in §3.9 ergänzen (+ 1 Testszenario).

### Mittelfristig (nächste Spec-Iteration)
1. **U-001/U-002:** Kebab-Menü pro Widget im Bearbeiten-Modus als vollwertige Inline-Tastaturalternative; DOM-Order-Regel `(y, x)`-Sortierung explizit festhalten.
2. **U-004/U-005:** Deep-Link-Icon auf `/dashboard` + First-Use-Coachmark als eigenes Akzeptanzkriterium.
3. **U-006:** CSS-Override für `.react-resizable-handle` als Technik-Detail in §3.8.

### Langfristig / Strategisch
1. **Neues UI-NFR "Reorderable-List-Pattern":** wiederverwendbares Muster (DnD + Button-Alternative + Fokus-Erhalt + Live-Region) als generische Ergänzung zu UI-NFR-002.
2. **Route-Level-Bundle-Budget:** eigenes Chunk-Budget für hochfrequentierte Landingpages wie `/dashboard` in UI-NFR-003, um Bibliotheks-Wildwuchs in CI früh zu erkennen.

---

## Fehlende UI-NFR-Spezifikationen

| Thema | Beschreibung | Vorgeschlagene UI-NFR-Erweiterung |
|-------|-------------|----------------------------------|
| DOM-Order bei absolut positionierten Grids | Keine Regel dazu, dass visuelle Grid-Position und Lesereihenfolge auseinanderfallen können | UI-NFR-002 — Meaningful Sequence bei dynamischen Grid-Layouts |
| Tastatur-Parität für Direktmanipulations-UIs (DnD) | UI-NFR-002 behandelt nur klassische Formulare/Navigation | UI-NFR-002 — Unterabschnitt "Drag-and-Drop-Alternativen" |
| Route-spezifisches Bundle-Budget | UI-NFR-003 kennt nur ein globales initiales Bundle-Budget | UI-NFR-003 — §2.4 |
| Empty-State bei nutzerinduzierter Leerung | UI-NFR-003 R-006 deckt nur Ladezustände ab | UI-NFR-004 oder REQ-045 selbst |

---

## Go/No-Go-Einschätzung

**FAIL (mit klarem Korrekturpfad).** Die Spec ist strukturell reif und lehnt sich sinnvoll an das bewährte REQ-042-Muster an, enthält aber einen echten technischen Selbstwiderspruch (Bundle-Budget K-001) sowie eine ungeklärte Tastaturbedienbarkeits-Lücke im Bearbeiten-Modus selbst (U-001) — beides sollte vor Implementierungsbeginn in der Spec aufgelöst werden, ist aber mit den Quick Wins in unter einem Tag Spec-Nacharbeit behebbar.
</content>
</invoke>
