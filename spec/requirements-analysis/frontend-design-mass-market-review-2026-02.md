# Frontend-Design-Review: Massentauglichkeit
**Erstellt von:** Frontend-Design-Reviewer (Subagent)
**Datum:** 2026-02-28
**Fokus:** Responsive Design - Kiosk-Modus - Mobile - Barrierefreiheit - Onboarding-UX - Nicht-Experten-Bedienung
**Analysierte Dokumente:**
- spec/ui-nfr/UI-NFR-001 bis UI-NFR-014 (alle UI-NFRs)
- spec/nfr/NFR-010 (UI-Pflegemasken)
- spec/req/REQ-001 bis REQ-027 (alle funktionalen Anforderungen)
- spec/stack.md / CLAUDE.md
- src/frontend/src/components/ (gesamter Komponentenbaum)
- src/frontend/src/pages/ (alle Seitenkomponenten)
- src/frontend/src/theme/ (Design-System)
- src/frontend/src/layouts/ (MainLayout, Sidebar)

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Responsive Design (Mobile) | 3/5 | Breakpoints definiert, aber keine Bottom-Navigation, kein Card-Layout für Listen auf Mobile |
| Responsive Design (Tablet) | 3/5 | Sidebar-Kollaps vorhanden; kein Split-View, kein Landscape-First fuer Tablet |
| Responsive Design (Desktop) | 4/5 | Sidebar + Fluid Grid gut umgesetzt; max-width fehlt noch |
| Kiosk-Modus - Touch-Targets | 5/5 | UI-NFR-011 ist vollstaendig und praezise spezifiziert |
| Kiosk-Modus - Vereinfachung | 5/5 | Quick-Select, 2-Ebenen-Navigation, Auto-Timeout alle spezifiziert |
| Kiosk-Modus - Umgebungstauglichkeit | 4/5 | High-Contrast-Theme spezifiziert; Hardware-Touch (resistiv) nicht adressiert |
| Mobile Vor-Ort-Szenarien | 2/5 | Kamera-Integration fehlt in Spezifikation; QR-Scan nur im Kiosk-Kontext |
| Barrierefreiheit (WCAG) | 4/5 | UI-NFR-002 solid; Skip-Link in MainLayout vorhanden; ARIA-live fehlt noch |
| UI-Konsistenz | 4/5 | DataTable, ExpertiseFieldWrapper, FormComponents gut; HelpTooltip noch nicht implementiert |
| Designsystem-Konformität | 4/5 | tokens.ts, typography.ts, theme.ts vorhanden; kein High-Contrast-Theme, keine Container Queries |

Die Spezifikationslage ist fuer ein Agrartechnologie-Produkt bemerkenswert stark: UI-NFR-011 (Kiosk-Modus) und UI-NFR-012 (PWA/Offline) sind auf einem Niveau, das industrielle Anforderungen ernsthaft adressiert. REQ-021 (Erfahrungsstufen) und REQ-027 (Light-Modus) zeigen ein durchdachtes Verstaendnis der breiten Zielgruppe. Die grossen Luecken liegen in der Implementation: Kiosk-Modus, PWA/Offline und HelpTooltip sind spezifiziert aber noch nicht umgesetzt. Das Dashboard (REQ-009) ist inhaltlich ueberdimensioniert fuer Einsteiger und fehlt eine klare mobile Variante. Die mobile Navigation ist der kritischste strukturelle Fehler - eine Sidebar ohne Bottom-Navigation ist auf Smartphones nicht praxistauglich.

---

## Kritisch - Sofortiger Korrekturbedarf

### K-001: Keine Bottom-Navigation fuer Mobile - Sidebar ist auf Smartphones unbrauchbar
**Anforderung:** "Die Hauptnavigation MUSS auf allen Seiten persistent sichtbar sein (Desktop: Sidebar oder Top-Navigation, Mobile: Bottom-Navigation oder Hamburger-Menue)" (UI-NFR-005 R-010)
**Bedienkontext:** Mobile
**Problem:** Die aktuelle Implementierung verwendet ausschliesslich eine Desktop-Sidebar (Drawer) auch auf Mobile. Der Hamburger-Icon im AppBar oeffnet denselben Sidebar-Drawer - das ist ein Hamburger-Menue, kein Bottom-Navigation-Pattern. Im Gewachshaus mit einer Hand in der Erde ist die Daumen-Zone oben-links die am schlechtesten erreichbare Zone eines Smartphones.
**Auswirkung:** Grower mit Smartphone koennen die wichtigsten Seiten (Pflegeerinnerungen, Aufgaben, aktuelle Pflanze) nicht mit dem Daumen einer Hand erreichen. Die App wirkt wie eine Desktop-Anwendung auf dem Handy - klassischer Grund fuer Nicht-Adoption.
**Lösungsvorschlag:** Bottom-Navigation fuer Mobile (unter 768px) mit 4-5 Tabs, die den wichtigsten Bedienkontexten entsprechen:

```
Einsteiger-Bottom-Nav (4 Tabs, < 768px):
┌─────────────────────────────────────────┐
│                                         │
│  [Seiteninhalt]                         │
│                                         │
├─────────┬─────────┬─────────┬───────────┤
│         │         │         │           │
│  🏠     │  🌱    │  ✅    │  ⚙        │
│ Start   │Pflanzen │Aufgaben │Einst.     │
│         │         │         │           │
└─────────┴─────────┴─────────┴───────────┘
                     ↑ Daumen-Zone (unten)
```

Experten-Bottom-Nav (5 Tabs) ergaenzt durch "Mehr"-Tab fuer weiteren Zugriff.

---

### K-002: Kiosk-Modus vollstaendig fehlend in Implementation
**Anforderung:** "Die Anwendung MUSS einen dedizierten Kiosk-Modus bereitstellen, der ueber eine URL (/kiosk) oder einen Toggle aktiviert werden kann" (UI-NFR-011 R-001)
**Bedienkontext:** Kiosk
**Problem:** Die gesamte UI-NFR-011 (56 Einzelanforderungen) ist nicht implementiert. Kein `/kiosk`-Route, kein Kiosk-Toggle, keine Quick-Action-Kacheln, kein Auto-Timeout, kein High-Contrast-Theme, keine Quick-Select-Kacheln fuer EC/pH. Der Kiosk-Modus ist die prioritaere Anforderung fuer den professionellen Einsatz im Growraum.
**Auswirkung:** Professionelle Grower, die ein Tablet fest im Gewachshaus montieren moechten, koennen das System nicht praxistauglich betreiben. Die Standardoberflaeche mit 48px-Touch-Targets und komplexer Sidebar-Navigation ist mit Gartenhandschuhen nicht bedienbar.
**Lösungsvorschlag:** Prioritaer implementieren: `/kiosk`-Route mit Startseite, KioskProvider-Context fuer Groessen-Scaling, Quick-Action-Kacheln, Auto-Timeout-Hook. Reihenfolge gemaess UI-NFR-011: Erst Grundstruktur (R-001 bis R-003), dann Touch-Targets (R-007 bis R-013), dann Navigation (R-014 bis R-021).

```
Kiosk-Startseite (Mindest-MVP):
┌────────────────────────────────────────────────────┐
│  Kamerplanter                        [Kiosk] [🏠]  │
├────────────────────────────────────────────────────┤
│                                                    │
│   ┌──────────────────┐   ┌──────────────────┐     │
│   │                  │   │                  │     │
│   │  [QR-Icon 48px]  │   │  [Wasser 48px]   │     │
│   │  Pflanze scannen │   │  Bewaesserung    │     │
│   │    min. 80x80px  │   │  erfassen        │     │
│   └──────────────────┘   └──────────────────┘     │
│                 24px Abstand                        │
│   ┌──────────────────┐   ┌──────────────────┐     │
│   │  Rundgang        │   │  Problem melden  │     │
│   │  starten         │   │  [Warn 48px]     │     │
│   └──────────────────┘   └──────────────────┘     │
│                                                    │
│   ┌──────────────────────────────────────────┐    │
│   │  Aktueller Status: 3 offene Aufgaben     │    │
│   └──────────────────────────────────────────┘    │
├────────────────────────────────────────────────────┤
│  Letzte Aktivitaet: vor 12 min                     │
└────────────────────────────────────────────────────┘
```

---

### K-003: PWA/Offline vollstaendig fehlend - App unbrauchbar im Keller/Growraum
**Anforderung:** "Die Anwendung MUSS als Progressive Web App installierbar sein" / "Die Anwendung MUSS im Offline-Zustand das Erfassen folgender Daten ermoeglichen: Messwerte (EC, pH, Temperatur), Bewaesserungsereignisse, Problembeobachtungen, Aufgaben-Status-Updates" (UI-NFR-012 R-001, R-015)
**Bedienkontext:** Mobile, Kiosk
**Problem:** Kein Service Worker, kein Web App Manifest, keine IndexedDB-Integration, kein Konnektivitaets-Indikator. Die App ist vollstaendig online-abhaengig. Growraeume im Keller haben typischerweise keinen oder instabilen Mobilfunkempfang.
**Auswirkung:** Im Hauptanwendungsfall "Messwerte im Growraum erfassen" funktioniert die App bei schlechtem WLAN/Mobilfunk nicht. Nutzer weichen auf Papiernotizen aus - die Kernanforderung der App wird untergraben.
**Lösungsvorschlag:** Implementation gemaess UI-NFR-012: vite-plugin-pwa + Workbox fuer Service Worker, IndexedDB (via Dexie) fuer Offline-Queue, Background Sync API. Mindest-MVP: Web App Manifest + Offline-Kachel fuer Kiosk-Startseite + Offline-Eingabe fuer Bewaesserungsereignisse.

---

### K-004: HelpTooltip / Fachbegriff-Erklaerungen fehlen komplett
**Anforderung:** "Jeder Fachbegriff im gesamten UI MUSS kontextuell erklaert werden. [...] Ein Formularfeld ohne HelpTooltip fuer einen Fachbegriff ist ein Review-Blocker." (UI-NFR-011/Fachbegriffe R-001, R-006.3)
**Bedienkontext:** Multi-Kontext (alle Nutzer, besonders Einsteiger)
**Problem:** Kein `HelpTooltip`-Komponente existiert in der Codebasis. Felder wie "EC (mS/cm)", "VPD (kPa)", "PPFD", "NPK-Ratio" werden ohne jede Erklaerung angezeigt. Das betrifft saemtliche Duegungs-, Sensorik- und Kultivierungsseiten.
**Auswirkung:** Hobby-Gaertner und Einsteiger (die gemaess Casual-Houseplant-User-Review die groesste potenzielle Zielgruppe sind) scheitern an den ersten Formularen. 16 unerklarte Fachbegriffe wurden im Review identifiziert - das ist eine kritische Barriere fuer Massentauglichkeit.
**Lösungsvorschlag:** `HelpTooltip`-Komponente implementieren gemaess UI-NFR-011/Fachbegriffe §4. Glossar-Daten als i18n-Schluessel bereits vollstaendig in der Spec definiert (38 Pflicht-Begriffe in DE+EN). Prioritaet: Duegungs-Seiten (EC, pH, NPK, CalMag), dann Sensorik (VPD, PPFD, DLI).

```
Formularfeld mit HelpTooltip (Korrekt):
┌─────────────────────────────────────┐
│  EC-Wert (mS/cm) [?]               │  ← Info-Icon oeffnet Tooltip
│  ┌─────────────────────────────┐   │
│  │  2.0                        │   │
│  └─────────────────────────────┘   │
│  Naehrstoffkonzentration der        │
│  Naehrloesung                      │
└─────────────────────────────────────┘

Tooltip-Inhalt (Einsteiger-Modus):
┌──────────────────────────────────────┐
│  Leitfaehigkeit - wie viel Duenger  │
│  im Wasser ist                       │
│                                      │
│  Deutschen Leitungswasser hat ca.   │
│  0,3-0,8 mS/cm. Fuer Topfpflanzen  │
│  Gesamt-EC 1,0-2,0 mS/cm.          │
│                                      │
│  Einsteiger-Tipp: Ohne EC-Messgeraet │
│  an die Dosierungsempfehlung auf der │
│  Duenger-Flasche halten.            │
│                                      │
│  Einheit: mS/cm - Typisch: 0,5-3,5 │
│  [Im Glossar oeffnen]               │
└──────────────────────────────────────┘
```

---

## Unvollstaendig - Wichtige Aspekte fehlen

### U-001: QR-Scan und Kamera-Integration nicht spezifiziert
**Bedienkontext:** Mobile, Kiosk
**Fehlende Spezifikation:** Kamera-Zugriff fuer QR-Code-Scanning (Pflanzen-Identifikation) und Foto-Dokumentation (IPM-Beobachtungen, Erntefotos) ist weder in den funktionalen Anforderungen noch in den UI-NFRs fuer das Web-Frontend spezifiziert. UI-NFR-011 R-015 erwaehnt "Pflanze scannen (QR)" als Quick-Action auf der Kiosk-Startseite, ohne die Web-Technologie zu definieren.
**Begruendung:** Im Gewachshaus ist QR-Scan der schnellste Weg, eine Pflanze zu identifizieren ohne in langen Listen scrollen zu muessen. Ohne Kamera-Integration ist die Kiosk-Quick-Action "Pflanze scannen" nicht realisierbar. Fuer IPM-Beobachtungen (REQ-010) sind Fotos als Dokumentation zentral.
**Vorschlag:** Neues UI-NFR fuer Kamera-Integration:
- Web API: `navigator.mediaDevices.getUserMedia()` + `BarcodeDetector API` (Chrome/Edge) mit Fallback auf `zxing-js` Library
- QR-Code-Scan: Dedizierter Scanner-Screen mit Fullscreen-Kamera-View, Fokus-Rechteck, akustischer Bestaetigung
- Foto-Upload: `<input type="file" accept="image/*" capture="environment">` als Progressive Enhancement
- Offline: Fotos in IndexedDB speichern (gemaess UI-NFR-012 R-043)
- PWA: `navigator.share` fuer Foto-Teilen

```
QR-Scanner (Mobile/Kiosk):
┌────────────────────────────────────┐
│  Pflanze scannen         [X]       │
├────────────────────────────────────┤
│                                    │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐  │
│  │   Kamera-Viewfinder         │  │
│  │                             │  │
│  │  ┌───────────────────────┐  │  │
│  │  │                       │  │  │
│  │  │  Fokus-Rechteck       │  │  │
│  │  │                       │  │  │
│  │  └───────────────────────┘  │  │
│  │                             │  │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘  │
│                                    │
│  Halte den QR-Code in den Rahmen  │
│                                    │
│  [Foto aufnehmen statt scannen]   │
└────────────────────────────────────┘
```

---

### U-002: Dashboard (REQ-009) ohne Einsteiger-Variante spezifiziert
**Bedienkontext:** Mobile, Desktop
**Fehlende Spezifikation:** REQ-009 spezifiziert ein hochkonfiguriertes Dashboard mit Widget-System, Drag-and-Drop, WebSocket-Updates, VPD-Heatmaps und Echtzeit-Charts - aber keine Einsteiger-Variante. Die "Role-Based Views" fuer Anfaenger/Fortgeschrittene/Experten werden im Business Case erwaehnt, aber nicht konkret spezifiziert.
**Begruendung:** Der aktuelle DashboardPage.tsx ist ein statisches Kachelgitter mit 6 Navigations-Shortcuts. Das ist fuer Einsteiger gut (einfach und klar), aber fuer den professionellen Use Case unzureichend. Das volle REQ-009-Dashboard (Charts, Sensor-Live-Daten, Alert-Center) ist fuer Einsteiger ueberfordernd. Es fehlt eine explizite Spec fuer den Uebergang.
**Vorschlag:** Dashboard-Varianten explizit in REQ-009 spezifizieren:
- Einsteiger: Kacheln fuer "Naechste Aufgabe", "Pflegestatus heute", "Wetter" (falls Aussenbeet), Pflanzen-Kurzliste
- Fortgeschritten: Aufgaben-Queue, letzte Messwerte, Kalender-Vorschau
- Experte: Volle Widget-Matrix wie in REQ-009 beschrieben

---

### U-003: Mobile-Formulare ohne spezifische Input-Type-Anforderungen
**Bedienkontext:** Mobile
**Fehlende Spezifikation:** UI-NFR-008 spezifiziert Formular-Verhalten (Dirty-State, Submit, Validierung), aber keine mobil-spezifischen Input-Attribute. Fuer Zahleneingaben im Growraum (EC, pH, Temperatur) fehlen: `inputmode="decimal"`, `type="number"`, Stepper-Komponenten.
**Begruendung:** Auf einem Smartphone oeffnet ein Standard-`<TextField>` die alphabetische Tastatur. Fuer die Eingabe "EC: 1.8" muss der Nutzer zur Zahlen-Ansicht wechseln - unnoetige Schritte mit nassen Haenden im Gewachshaus. Zudem werden negative Scrollbereiche (0-14 fuer pH) durch Freitext-Input nicht praezise kommuniziert.
**Vorschlag:** Explizite Anforderung in UI-NFR-008: Fuer alle Metriken-Felder (EC, pH, Temperatur, Luftfeuchte, CO2, PPM) MUSS `inputmode="decimal"` gesetzt werden. Fuer ganzzahlige Werte `inputmode="numeric"`. Quick-Select-Kacheln fuer haeufige Werte (gemaess Kiosk-Anforderung, aber auch im Normal-Modus als SOLL).

---

### U-004: Tablet-spezifisches Layout (Split-View) nicht spezifiziert
**Bedienkontext:** Tablet
**Fehlende Spezifikation:** UI-NFR-001 definiert drei Breakpoints und erwaehnt Tablet (768-1024px), aber kein Dokument spezifiziert Tablet-spezifische Layout-Patterns: kein Split-View (Master links, Detail rechts), keine Landscape-Orientierung als Primary Use Case, kein Drag-and-Drop fuer Planungsansichten.
**Begruendung:** Ein Tablet im Gewachshaus wird typischerweise im Landscape-Format verwendet. Die Sidebar nimmt in diesem Fall 240px von 1024px Breite ein - das ist 23% der Breite fuer Navigation. Ein Split-View (Pflanzenliste links | Detail rechts) waere fuer den Rundgang wesentlich effizienter.
**Vorschlag:** Tablet-Section in UI-NFR-001 ergaenzen:
- `lg`-Breakpoint (1024px) als Split-View-Trigger definieren
- Master-Detail-Layout fuer: PlantInstanceListPage + PlantInstanceDetailPage, TaskQueuePage + TaskDetailPage
- Landscape-Orientierung als primaerer Tablet-Kontext in Wireframes dokumentieren

---

### U-005: Fehlende Spezifikation fuer Touch-Target-Groessen in regulaeren Mobile-Formularen
**Bedienkontext:** Mobile
**Fehlende Spezifikation:** UI-NFR-001 fordert 48x48px fuer Touch-Targets allgemein. Die aktuelle theme.ts setzt `MuiTextField.defaultProps.size: 'small'` - das ergibt ca. 40px Hoehe, was unter der 48px-Mindestanforderung liegt.
**Begruendung:** Small-TextField in MUI hat ca. 40px Hoehe. Mit nassen Haenden im Gewachshaus erhoehen sich Fehleingaben signifikant. Die 8px Differenz klingt klein, macht aber bei einer Formular-Session mit 10+ Feldern einen deutlichen Unterschied in der Bediengenauigkeit.
**Vorschlag:** `MuiTextField.defaultProps.size: 'medium'` als Default setzen (52px), oder responsive: `size: { xs: 'medium', md: 'small' }`. Fuer Kiosk: size auf `'large'` gemaess UI-NFR-011 R-013.

---

### U-006: Keine Spezifikation fuer Sensor-Eingabe auf Mobile (REQ-005 UI-Seite)
**Bedienkontext:** Mobile, Kiosk
**Fehlende Spezifikation:** REQ-005 spezifiziert Hybrid-Sensorik mit manuellem Eingabe-Fallback, aber kein eigenes UI fuer schnelle Messwert-Erfassung vor Ort. Die manuelle Eingabe von EC, pH, Temperatur, Luftfeuchte ist als kritischste mobile Interaktion nicht dediziert spezifiziert.
**Begruendung:** Im Growraum-Alltag: Grower misst EC mit Messgeraet (1.8 mS/cm), will das schnell ins System eintippen. Dafuer kein dediziertes Screen, kein Quick-Entry-Pattern. Der Nutzer muss: Navigation oeffnen -> Durchlauf finden -> Messwerte-Tab -> Neuer Eintrag -> Formular ausfullen. Das sind zu viele Schritte fuer eine Routine-Aufgabe.
**Vorschlag:** Dedizierter "Messwert erfassen"-Flow als Kiosk-Quick-Action und als Bottom-Navigation-FAB auf Mobile. Maximal 3 Schritte: Pflanze/Run auswaehlen -> Wert eingeben (Quick-Select-Kacheln: 1.0/1.5/2.0/2.5 mS/cm + Manuell) -> Bestaetigen.

---

## Optimierungspotenzial - Verbesserungen empfohlen

### O-001: Breakpoint-Diskrepanz zwischen UI-NFR-001 und tokens.ts
**Aktuelle Spezifikation:** "R-001: Mobile (<=768px), Tablet (<=1024px), Desktop (>1024px)" (UI-NFR-001)
**Problem:** tokens.ts definiert `sm: 600, md: 768, lg: 1024` - das weicht vom MUI-Standard (sm=600, md=900, lg=1200) ab und stimmt mit der Spec-Definition nicht ueberein: `md=768` entspricht der Spec-"Mobile"-Grenze, aber MUI verwendet `md` intern fuer Tablet-Layouts. Das `sm: 600`-Breakpoint ist in der Spec nicht definiert und hat keine UI-Semantik.
**Bessere Alternative:** Breakpoint-Benennung in tokens.ts semantisch anpassen:
```typescript
export const breakpoints = {
  values: {
    xs: 0,      // < 600 - kleines Mobile
    sm: 600,    // 600-767 - grosses Mobile (Landscape-Smartphones)
    md: 768,    // 768-1023 - Tablet (exakt gemaess Spec)
    lg: 1024,   // >= 1024 - Desktop
    xl: 1440,   // >= 1440 - Grossbildschirm
  },
};
```
Und im Layout-Code konsequent `md` fuer Tablet/Mobile-Trennlinie verwenden.

---

### O-002: max-width fuer Desktop fehlt - Layouts zerfliessen auf breiten Monitors
**Aktuelle Spezifikation:** "R-008: Container MUESSEN eine Maximalbreite definieren (empfohlen: 1280px)" (UI-NFR-001)
**Problem:** Weder MainLayout.tsx noch die einzelnen Seitenkomponenten setzen eine `maxWidth`. Auf einem 2560px-Monitor (4K/UltraWide) werden Inhalte ueber die volle Breite gestreckt - Zeilenlangen von 200+ Zeichen sind nicht lesbar.
**Bessere Alternative:** Content-Container mit `maxWidth: 1280` und `mx: 'auto'` in MainLayout, oder MUI `Container maxWidth="xl"` als Wrapper fuer den Hauptinhalt.

---

### O-003: DashboardPage ist ein Stammdaten-Navigationsgitter, kein Action-Dashboard
**Aktuelle Spezifikation:** DashboardPage.tsx zeigt 6 Navigationskacheln zu: BotanicalFamilies, Species, Sites, Substrates, PlantInstances, Calculations.
**Problem:** Diese 6 Kacheln sind Stammdaten-Verwaltungs-Links - nicht die typischen Dashboard-Aktionen eines Growers. "Naechste Aufgabe", "Pflegeerinnerungen heute", "Warnungen", "Aktuelle Messwerte" fehlen. Gemaess REQ-009 ist das Dashboard als "Information at a Glance" konzipiert, die aktuelle Implementierung ist nur eine Navigations-Seite.
**Bessere Alternative:** Dashboard-Inhalt basierend auf Erfahrungsstufe (gemaess REQ-021):
- Einsteiger: "Heute zu tun" (Pflegeerinnerungen), "Meine Pflanzen" (3-4 Karten), Glossar-Link
- Expert: Volle Widget-Matrix gemaess REQ-009

---

### O-004: Kein High-Contrast-Theme implementiert - nur Light/Dark
**Aktuelle Spezifikation:** "R-039: Die Anwendung MUSS ein dediziertes High-Contrast-Theme bereitstellen" (UI-NFR-011)
**Problem:** theme.ts definiert nur `lightTheme` und `darkTheme`. Das High-Contrast-Theme fuer Kiosk und Outdoor-Nutzung (Kontrast >=7:1, keine Grauabstufungen fuer Flaechen, Schriftwert min. 500) fehlt vollstaendig. Im Gewachshaus mit direkter Sonneneinstrahlung ist auch das Light-Theme schwer lesbar.
**Bessere Alternative:** `highContrastTheme` in theme.ts ergaenzen:
- `background.default: '#000000'`, `background.paper: '#0a0a0a'`
- `text.primary: '#FFFFFF'`, alle Farbtextkontraste >=7:1
- Keine box-shadow, keine gradient backgrounds
- Button-Groessen im MUI-Theme auf `size: 'large'` defaulten

---

### O-005: Onboarding-Wizard ohne dedizierte Mobile-Optimierung
**Aktuelle Spezifikation:** "5.4 Responsive Design: < 768px (Mobile): Volle Breite, Kit-Grid 1 Spalte, Swipe zwischen Steps moeglich" (REQ-020 §5.4)
**Problem:** Die Swipe-Navigation zwischen Wizard-Steps ist in UI-NFR-011 R-028 explizit verboten: "Swipe-Gesten DUERFEN im Kiosk-Modus NICHT als einzige Interaktionsmethode verwendet werden". Selbst ausserhalb des Kiosk-Modus ist Swipe auf Mobile mit nassen Haenden unzuverlaessig. Der Wizard-Step-Wechsel per Swipe als optionale Interaktion ist vertretbar, muss aber eine Tap-Alternative haben - das ist in REQ-020 nicht explizit sichergestellt.
**Bessere Alternative:** Swipe als Enhancement, nicht als einzige Methode. Grosse "Weiter"-Buttons als Primary Method. Im MUI Stepper mobile-steps (`<MobileStepper>`) verwenden, der die Swipe-Alternative standardmaessig einbaut.

---

### O-006: Container Queries fuer komponentenbasierte Responsivitaet nicht genutzt
**Aktuelle Spezifikation:** UI-NFR-001 erwaehnt Container Queries nicht; die Implementierung nutzt ausschliesslich viewport-basierte Breakpoints.
**Problem:** Die `DataTable`-Komponente hat nur `hideBelowBreakpoint: 'md' | 'lg'` basierend auf Viewport-Breite. Wenn die Tabelle in einem 400px-Container auf einem Desktop angezeigt wird (z.B. in einem Dialog oder Split-View), werden Spalten nicht ausgeblendet, obwohl sie nicht lesbar sind.
**Bessere Alternative:** Container Queries (`@container`) als progressives Enhancement fuer Komponenten wie DataTable, PflegeDashboard-Karten, Onboarding-StarterKitCard. Gibt den Komponenten eigene Responsivitaet unabhaengig vom Viewport.

---

### O-007: Keine spezifizierte Vorgehensweise fuer Offline-erkennbare UI-Elemente
**Aktuelle Spezifikation:** UI-NFR-012 R-040/R-041 spezifizieren Deaktivierung und Greying-Out fuer offline-inkompatible Aktionen.
**Problem:** Welche Aktionen offline inkompatibel sind, ist nur in der Tabelle in UI-NFR-012 §6.2 aufgelistet, aber nicht als Anforderung an bestimmte UI-Elemente formuliert. Kein einzelnes REQ-Dokument referenziert die Offline-Einschraenkung ihrer Funktionen.
**Bessere Alternative:** Jedes REQ das eine Kern-Online-Aktion beschreibt (z.B. Neue Pflanzenart anlegen, Crop-Rotation validieren, Enrichment aufrufen) sollte explizit dokumentieren: "Diese Aktion ist im Offline-Modus nicht verfuegbar - der Button muss mit Offline-Icon und Tooltip gemaess UI-NFR-012 R-040 deaktiviert werden."

---

### O-008: ExperienceLevelSwitcher in AccountSettings - aber kein In-Context-Wechsel
**Aktuelle Spezifikation:** REQ-021 §3.8 spezifiziert einen ExperienceLevelSwitcher in AccountSettingsPage. Es gibt keinen In-Context-Wechsel direkt auf einer Seite mit komplexen Feldern.
**Problem:** Der "Mehr anzeigen"-Toggle (ShowAllFieldsToggle) existiert im Code, aber der naechste logische Schritt - "Ich bin bereit, dauerhaft zum Fortgeschritten-Modus zu wechseln" - erfordert einen Umweg ueber Einstellungen. Ein direkter Modus-Wechsel-CTA waere eleganter.
**Bessere Alternative:** Im `ShowAllFieldsToggle`-Dialog: Wenn Nutzer "Mehr anzeigen" aktiviert, erscheint unterhalb: "Immer mehr anzeigen? [Zu Fortgeschritten wechseln]" als Soft-Prompt (keine Pflicht).

---

### O-009: Fehlende Spezifikation fuer Meldungs-Aggregation bei mehreren gleichzeitigen Snackbars
**Aktuelle Spezifikation:** "R-006: Maximal drei Snackbars SOLLEN gleichzeitig sichtbar sein" (UI-NFR-004)
**Problem:** Bei der Synchronisation von 12 Offline-Eintraegen (UI-NFR-012) wuerden 12 einzelne Snackbars ausgeloest. UI-NFR-004 R-006 erlaubt maximal 3, aber wie die 9 weiteren aggregiert werden, ist nicht spezifiziert.
**Bessere Alternative:** Aggregations-Regel: Wenn >3 Notifications desselben Typs wartend sind, werden sie zusammengefasst: "12 Eintraege synchronisiert" statt 12 einzelne Meldungen. Das ist in UI-NFR-004 als zusaetzliche Regel zu ergaenzen.

---

## Positiv - Best Practices eingehalten

**REQ-021 Erfahrungsstufen (dreistufiger UI-Modus):**
Hervorragend durchdacht. Progressive Disclosure mit "Mehr anzeigen"-Override, serverseitige Persistierung der Praeferenz, Navigation-Tiering (5/8/alle Menupunkte), Auto-Fill fuer ausgeblendete Felder, Quick-Add-Plant fuer Einsteiger - alles spezifiziert und bereits in ExpertiseFieldWrapper + fieldConfigs.ts implementiert. Das ist Best Practice fuer inklusive UI-Design.

**UI-NFR-011 Kiosk-Modus (Spezifikationsqualitaet):**
Die Spezifikation selbst ist exzellent: 56 Einzelanforderungen, Wireframes, Akzeptanzkriterien fuer Bedienung mit Nase und Ellenbogen, Long-Press fuer destruktive Aktionen, 300ms Debouncing, Auto-Timeout mit Drafts-Sicherung. Das ist industrielle Qualitaet.

**UI-NFR-012 PWA/Offline (Vollstaendigkeit):**
Vollstaendige Spezifikation: Konflikt-Resolution (lokal vs. Server), exponential Backoff, FIFO-Sync, Foto-Komprimierung (1920px JPEG 80%), IndexedDB-Schema, iOS-Safari-Fallbacks - alle Edge Cases sind adressiert.

**REQ-027 Light-Modus:**
Elegante Loesung fuer das Einzelnutzer-Problem: Auth-Adapter-Pattern, System-User/-Tenant, idempotente Seed-Logik, Moduswechsel per Environment-Variable - minimaler Code-Aufwand fuer maximalen UX-Gewinn.

**tokens.ts Design-System Grundlage:**
4px-Basisraster (spacing), semantische Breakpoints, Border-Radii - konsistent definiert. typography.ts nutzt rem-Werte. theme.ts verwendet ausschliesslich Design-Tokens (keine direkten Hex-Werte in Komponenten).

**MainLayout.tsx Skip-Link:**
Skip-to-Content-Link ist implementiert (WCAG 2.4.1 Level A). Das ist oft vergessen und hier korrekt umgesetzt.

**DataTable.tsx Responsive:**
`hideBelowBreakpoint`-Prop fuer Spalten ermoeglicht progressive Spalten-Deaktivierung auf Mobile - guter Ansatz, auch wenn Container Queries noch fehlen.

**HelpTooltip-Glossar-Daten vollstaendig spezifiziert:**
38 Pflicht-Begriffe in DE+EN mit `short`, `long`, `beginnerTip`, `unit`, `typicalRange` - komplett ausformuliert in UI-NFR-011/Fachbegriffe. Die Daten sind implementierungsbereit, nur die Komponente fehlt noch.

**i18n von Beginn an:**
Alle Texte ueber `useTranslation()` und i18n-Keys, DE als Default - korrekte Grundlage fuer spaetere Spracherweiterungen.

**UnsavedChangesGuard:**
Dirty-State-Warnung als eigenstaendige Komponente implementiert - gutes Pattern fuer Datenverlust-Praevention.

---

## Kiosk-Modus - Detailbewertung

### Bedienbarkeit mit eingeschraenkter Motorik

| Szenario | Bewertung | Anmerkung |
|----------|-----------|-----------|
| Bedienung mit Handschuhen | nicht erfuellt | Standard-Touch-Targets sind 40-48px (small TextFields), Kiosk-Modus nicht implementiert |
| Bedienung mit nassen Haenden | nicht erfuellt | Kein Debouncing, kein Long-Press fuer destruktive Aktionen |
| Bedienung mit verschmutzten Haenden | nicht erfuellt | Gleiche Problematik wie nasse Haende |
| Bedienung mit Nase/Ellenbogen (Notfall) | nicht erfuellt | Quick-Action-Kacheln (80x80px) fehlen vollstaendig |
| Bedienung mit nur einer Hand | teilweise | Bottom-Navigation fehlt (daumen-erreichbar); Sidebar-Toggle ist oben-links |

**Hinweis:** Die Bewertung bezieht sich auf den Implementierungsstand. Die Spezifikation (UI-NFR-011) adressiert alle Szenarien vollstaendig und korrekt.

### Kiosk-Workflows - Kritische Pfade

| Workflow | Schritte (Soll) | Schritte (Ist) | Bewertung |
|----------|:---------------:|:--------------:|-----------|
| Pflanze scannen und Status pruefen | <=3 | nicht moeglich (kein QR-Scan) | nicht implementiert |
| Bewaesserung erfassen | <=4 | 6-8 (Navigation + Formular) | zu viele Schritte |
| Problem melden | <=3 | 5-7 (IPM-Navigation + Beobachtung) | zu viele Schritte |
| Aufgabe als erledigt markieren | <=2 | 3-4 (Navigation + Klick + Confirm) | akzeptabel |

### Empfohlene Kiosk-Startseite (gemaess UI-NFR-011 §3.1, noch nicht implementiert)

```
┌────────────────────────────────────────────────────┐
│  Kamerplanter                        [Kiosk]  [🏠] │
├────────────────────────────────────────────────────┤
│                                                     │
│   ┌──────────────────┐   ┌──────────────────┐      │
│   │                  │   │                  │      │
│   │   [QR 48px]      │   │   [Wasser 48px]  │      │
│   │   Pflanze        │   │   Bewaesserung   │      │
│   │   scannen        │   │   erfassen       │      │
│   │   min. 80x80px   │   │   min. 80x80px   │      │
│   └──────────────────┘   └──────────────────┘      │
│              24px Mindestabstand                    │
│   ┌──────────────────┐   ┌──────────────────┐      │
│   │                  │   │                  │      │
│   │   [Liste 48px]   │   │   [Warn 48px]    │      │
│   │   Rundgang       │   │   Problem        │      │
│   │   starten        │   │   melden         │      │
│   └──────────────────┘   └──────────────────┘      │
│                                                     │
│   ┌────────────────────────────────────────┐       │
│   │   3 offene Aufgaben - 1 Warnung        │       │
│   │   Letzte Aktivitaet: vor 23 min        │       │
│   └────────────────────────────────────────┘       │
│                                                     │
├────────────────────────────────────────────────────┤
│  [<- Zurueck]                            [🏠 Home] │
└────────────────────────────────────────────────────┘
Alle Buttons: min. 64x64px Touch-Target, empfohlen 72x72px
Schrift: min. 18px Fliestext, 24px Labels
```

---

## Responsive-Matrix

| Anforderung/REQ | Mobile | Tablet | Desktop | Kiosk |
|----------------|:------:|:------:|:-------:|:-----:|
| REQ-009 Dashboard | teilweise | teilweise | teilweise | nicht |
| REQ-020 Onboarding-Wizard | teilweise | gut | gut | nicht |
| REQ-021 UI-Erfahrungsstufen | gut | gut | gut | nicht |
| REQ-022 Pflegeerinnerungen | teilweise | teilweise | gut | nicht |
| REQ-001 Stammdaten-Formulare | schlecht | teilweise | gut | nicht |
| REQ-004 Duegungs-Logik | schlecht | teilweise | gut | nicht |
| REQ-005 Sensorik manuell | nicht | nicht | teilweise | nicht |
| REQ-006 Aufgaben | teilweise | teilweise | gut | nicht |
| REQ-007 Ernte | teilweise | teilweise | gut | nicht |
| REQ-010 IPM | schlecht | teilweise | gut | nicht |
| REQ-013 Pflanzdurchlauf | teilweise | teilweise | gut | nicht |
| REQ-014 Tankmanagement | schlecht | teilweise | gut | nicht |
| REQ-027 Light-Modus | teilweise | teilweise | gut | nicht |

**Legende:** gut = spezifiziert und geeignet | teilweise = teilweise spezifiziert oder suboptimal | schlecht = nicht fuer Kontext geeignet | nicht = nicht spezifiziert oder fehlend

---

## Touch-Target-Audit

| Komponente | Standard-Groesse (ist) | Kiosk-Groesse (soll) | Abstand | Bewertung |
|-----------|:-------------------:|:-------------------:|:-------:|-----------|
| MuiTextField (small, default) | ~40px Hoehe | 64px | 8px | nicht erfuellt (40 < 48) |
| MuiButton (standard) | 36px Hoehe | 72px | 8px | nicht erfuellt (36 < 48) |
| DataTable Zeilen | 52px Zeilenhoehe | 64px | 0px | akzeptabel Standard, Kiosk fehlt |
| Sidebar ListItemButton | 48px | 64px | 4px | Standard OK, Abstand zu gering |
| Dialog Action Buttons | 36-40px | 64px | 8px | knapp unter Minimum |
| FAB (Floating Action Button) | 56px | 72px | 16px | Standard-FAB vorhanden, Kiosk-Groesse fehlt |
| Onboarding-Kacheln (StarterKit) | ~120px | 80px (Min) | 16px | gut (groesser als Minimum) |
| ExperienceLevel-Kacheln | ~100px | 80px (Min) | 16px | gut |

**Problem-Pattern:** MUI's default `size="small"` fuer TextField und Button fuehrt zu Touch-Targets unter der 48px-Mindestanforderung von UI-NFR-001. Die theme.ts setzt `MuiTextField.defaultProps.size: 'small'` global.

---

## Empfehlungen

### Sofort umsetzbar (Quick Wins)

1. **MuiTextField default size auf 'medium' aendern** (theme.ts): Von `size: 'small'` auf `size: 'medium'` wechseln. Touch-Target steigt von ~40px auf ~52px. Kein Aufwand, sofortiger Gewinn fuer alle Formulare auf Mobile. Betroffener Kontext: Mobile, Kiosk.

2. **max-width Container in MainLayout**: `maxWidth: 1280` und `mx: 'auto'` im Content-Bereich hinzufuegen. 2 Zeilen Code, verhindert unleserliche Layouts auf Breitbildmonitors. Betroffener Kontext: Desktop.

3. **HelpTooltip-Komponente (Skeleton)**: Eine minimale `HelpTooltip`-Komponente erstellen, die initial nur `short`-Text anzeigt. Dann iterativ die 5 kritischsten Fachbegriff-Felder belegen (EC, pH, VPD, PPFD, NPK). Die i18n-Daten sind bereits vollstaendig spezifiziert. Betroffener Kontext: Alle, besonders Einsteiger.

4. **`/kiosk`-Route anlegen (Redirect zu Kiosk-Startseite)**: Eine leere Kiosk-Startseite mit den 4 Quick-Action-Kacheln (ohne Funktion) ist ein sichtbarer Fortschritt und erlaubt fruehe Usability-Tests. Betroffener Kontext: Kiosk.

5. **Bottom-Navigation-Wrapper fuer Mobile**: `MuiBottomNavigation` mit 4 Tabs unter 768px anzeigen, Sidebar auf diesem Breakpoint ausblenden. Das ist ein Layout-Wrapper ohne Logik-Aenderungen. Betroffener Kontext: Mobile.

### Mittelfristig (Naechste Entwicklungsphase)

1. **Kiosk-Provider implementieren**: React-Context der `isKioskMode`, `useKioskTouchTarget`, `useAutoTimeout` bereitstellt. Damit wird die Groessen-Skalierung aller MUI-Komponenten zentral steuerbar (UI-NFR-011 R-013: `size: 'large'` als Default). Benoetigt neue UI-NFR-Umsetzung.

2. **PWA-Grundkonfiguration**: `vite-plugin-pwa` einrichten, Web App Manifest erstellen, Service Worker fuer statische Assets. Damit wird die App auf Android installierbar und laeuft im Standalone-Modus. IndexedDB-Integration als Folgeschritt. Benoetigt UI-NFR-012-Umsetzung.

3. **Offline-Queue fuer Bewaesserungsereignisse**: Als ersten Offline-Datenpunkt Bewaesserungsereignisse in IndexedDB puffern. Das ist die haeufigste mobile Aktion und der beste Test fuer das Offline-Pattern. Benoetigt UI-NFR-012 R-015/R-016.

4. **Quick-Select-Kacheln fuer EC/pH/Temperatur**: Numerische Eingabe-Komponente mit vordefinierten Kacheln + Manuell-Option. Sowohl fuer Kiosk-Modus als auch fuer Mobile-Formulare nutzen. Benoetigt UI-NFR-011 R-024 bis R-027.

5. **Mobile-spezifische Sensor-Eingabe**: Dedizierter "Messwert erfassen"-Dialog als FAB-Action auf PlantInstanceDetailPage. 3-Schritte-Flow: Pflanze (vorbelegt) -> Messwert-Kacheln -> Bestaetigen. Benoetigt neue UI-Komponente, aber keine Backend-Aenderungen.

### Langfristig / Strategisch

1. **Container Queries als Ergaenzung zu Viewport Breakpoints**: CSS Container Queries in DataTable, PflegeDashboard-Karten und Onboarding-Wizard einsetzen. Das macht Komponenten portabler zwischen Sidebar/Fullscreen/Dialog-Kontext und bereitet auf zukuenftige Widget-Layouts (REQ-009) vor.

2. **Dedizierte Kiosk-Testinfrastruktur**: Manuelle Usability-Tests mit echten Gartenhandschuhen auf 10" und 7" Tablets im Gewachshaus. Accessibility-Tests mit axe-core fuer Touch-Target-Groessen. Dies ist in UI-NFR-011 §4 bereits als Akzeptanzkriterium definiert, aber die Test-Infrastruktur fehlt.

3. **High-Contrast-Theme fuer Outdoor-Nutzung**: Drittes Theme (neben Light und Dark) implementieren. Besonders relevant fuer Balkon/Garten-Nutzer und Kiosk-Stationen mit Sonneneinstrahlung. Kontrastverhaltnis >=7:1 gemaess UI-NFR-011 R-040.

4. **Foto-basierte Pflanzenerkennung (N-001)**: Im Casual-Houseplant-User-Review als Dealbreaker fuer Gelegenheitsnutzer identifiziert. Kamera-Integration (U-001 dieses Reviews) ist Voraussetzung. KI-API-Integration (PlantNet, Google Vision) als Backend-Adapter.

---

## Fehlende UI-NFR-Spezifikationen

| Thema | Beschreibung | Vorgeschlagene UI-NFR |
|-------|-------------|----------------------|
| QR-Scan und Kamera-Integration | Web-API fuer QR-Code-Scan (BarcodeDetector + zxing-js Fallback), Foto-Capture (`capture="environment"`), Offline-Foto-Speicherung | UI-NFR-015: Kamera-Integration |
| Touch-Target-Grossenspezifikation fuer Nicht-Kiosk | Standard-Mobile-Formulare haben 40-48px Targets (zu klein). Explizite Anforderung fuer `size: 'medium'` als Mobile-Default fehlt | UI-NFR-001 Ergaenzung: Mobile Touch-Targets |
| Tablet Split-View Layout | Master-Detail-Layout fuer Listen+Detail auf Tablet/Landscape nicht definiert | UI-NFR-001 Ergaenzung: Tablet-Layouts |
| Mobile Messwert-Schnelleingabe | Dedizierter Quick-Entry-Flow fuer manuelle Sensor-Messwerte vor Ort - kein Standard-Formular, sondern optimierter 3-Schritte-Flow | UI-NFR-016: Mobile Schnelleingabe |
| Notification-Kanal und Push-Benachrichtigungen | REQ-022 generiert Celery-Tasks, aber kein Zustellkanal definiert. Mehrere Reviews identifizieren Push als fehlendes Feature | UI-NFR-012 Ergaenzung: Push-Notifications |
| Audio-Feedback-Einstellungen | UI-NFR-011 R-051/R-052 spezifiziert optionales Audio im Kiosk-Modus. Kein UI fuer Audio-Einstellungen (Volume, Tone, Enable/Disable) spezifiziert | UI-NFR-011 Ergaenzung: Audio-Einstellungen |

---

## Bewertung nach Nutzergruppen (Massentauglichkeit)

### Hobby-Gaertner / Zimmerplanzen-Einsteiger
- **Staerken:** REQ-021 Erfahrungsstufen, REQ-027 Light-Modus, REQ-020 Onboarding-Wizard, UI-NFR-011/Fachbegriffe Glossar
- **Luecken:** HelpTooltip nicht implementiert, Quick-Add-Plant-Dialog laut Memory noch nicht implementiert, Dashboard zeigt Stammdaten-Links statt "Heute zu tun"
- **Massentauglichkeit:** 3/5 - Konzept gut, Implementation teilweise fehlend

### Grower im Gewachshaus (professionell)
- **Staerken:** REQ-004 Duegungs-Logik (EC-net, Misch-Reihenfolge), REQ-014 Tankmanagement, REQ-010 IPM
- **Luecken:** Kiosk-Modus nicht implementiert, Offline nicht implementiert, Mobile-Formulare suboptimal
- **Massentauglichkeit:** 2/5 - Fachliche Tiefe gut, aber Feldtauglichkeit fehlt

### Balkon-/Outdoor-Gaertner
- **Staerken:** REQ-002 Beetplanung, REQ-022 Ueberwinterung, REQ-006 Saisonaler Gartenkalender, REQ-015 Aussaatkalender
- **Luecken:** Outdoor-Dashboard-Widgets fehlen, Wetter-Integration (REQ-005 v2.3) nicht implementiert
- **Massentauglichkeit:** 3/5 - Spec vollstaendig, Implementation ausstehend

### Community-Gaertner / Gemeinschaftsgaerten
- **Staerken:** REQ-024 vollstaendig (Mitgliederverwaltung, Einladungen, Rollen), Pinnwand und Giessdienst-Rotation spezifiziert
- **Luecken:** Collaboration-Features (Pinnwand, Ernte-Teilen) noch nicht implementiert
- **Massentauglichkeit:** 3/5 - Basis vorhanden

---

## Glossar

- **Touch-Target**: Beruehrbarer Bereich eines interaktiven UI-Elements. Nicht identisch mit der visuellen Groesse - Padding zaehlt mit. MUI `size="small"` Button hat visuell 28px Hoehe, aber 36px Touch-Target durch minimales Padding.
- **Kiosk-Modus**: Vereinfachte Bedienoberflaiche fuer den Einsatz an festen Standorten mit eingeschraenkter Eingabemoeglichkeit. In Kamerplanter: feste Tablet-Station im Gewachshaus, bedienbar mit Handschuhen.
- **Mobile-First**: Design-Strategie, bei der zuerst die mobile Darstellung gestaltet wird. Kamerplanter hat Mobile-First in der Spec (UI-NFR-001 R-002), aber die MUI-Defaults (size="small", Sidebar-Layout) widersprechen dem.
- **Progressive Web App (PWA)**: Web-Anwendung mit nativen App-Eigenschaften: installierbar, Offline-faehig, Push-Notifications. In Kamerplanter vollstaendig in UI-NFR-012 spezifiziert, noch nicht implementiert.
- **Bottom-Navigation**: MUI `BottomNavigation`-Komponente - fixierte Tab-Leiste am unteren Bildschirmrand. Ergonomisch optimal fuer Einhand-Bedienung auf Smartphones (Daumen-Zone).
- **Container Query**: CSS-Feature das Komponenten-Responsivitaet anhand des Elterncontainers statt des Viewports steuert. Erlaubt Komponenten, sich in verschiedenen Layout-Kontexten (Dialog, Sidebar, Fullscreen) korrekt anzupassen.
- **Quick-Select-Kacheln**: Vordefiniete Auswahl-Buttons fuer haeufige Werte (z.B. EC: 1.0/1.5/2.0/2.5 mS/cm). Ersetzen Freitext-Eingabe fuer bekannte Wertesets im Kiosk-Modus.
- **High-Contrast-Theme**: Farbschema mit maximierten Kontrastwerten fuer Lesbarkeit bei direkter Sonneneinstrahlung oder eingeschraenktem Sehvermoegen. WCAG AAA: >=7:1 Kontrast.
- **Split-View**: Master-Detail-Layout auf Tablet: Liste links (Auswahl), Detail rechts (Inhalt). Eliminiert Navigationswechsel zwischen Listen- und Detail-Ansicht.
- **Skeleton Screen**: Platzhalter-Layout waehrend des Ladens, das die Inhaltsstruktur vorwegnimmt. Verhindert Layout-Shift und kommuniziert, dass Inhalt geladen wird.
- **Debouncing**: Verzoegeung einer Aktion bis zur Ruhe der Eingabe (300ms fuer Touch im Kiosk-Modus). Verhindert versehentliche Mehrfachausloesung durch Phantom-Touches bei nassen Haenden.

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Final
**Erstellt**: 2026-02-28
**Naechste Ueberpruefung**: Nach Implementierung von Kiosk-Modus und PWA-Grundkonfiguration

