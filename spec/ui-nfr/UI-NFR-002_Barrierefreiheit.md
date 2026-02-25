---

ID: UI-NFR-002
Titel: Barrierefreiheit (Accessibility)
Kategorie: UI-Verhalten Unterkategorie: Accessibility, Inklusion
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [accessibility, wcag, aria, keyboard-navigation, screenreader, a11y]
Abhängigkeiten: [UI-NFR-001]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-002: Barrierefreiheit (Accessibility)

## 1. Business Case

### 1.1 User Story

**Als** Nutzer mit eingeschränktem Sehvermögen
**möchte ich** die Anwendung mit einem Screenreader bedienen können
**um** alle Funktionen gleichberechtigt nutzen zu können.

**Als** Nutzer mit motorischen Einschränkungen
**möchte ich** die Anwendung vollständig per Tastatur bedienen können
**um** nicht auf eine Maus angewiesen zu sein.

**Als** Produktmanager
**möchte ich** dass die Anwendung die WCAG 2.1 AA-Richtlinien erfüllt
**um** gesetzliche Anforderungen einzuhalten und die Nutzerbasis zu maximieren.

### 1.2 Geschäftliche Motivation

Barrierefreiheit ist nicht nur eine rechtliche Anforderung, sondern verbessert die Benutzererfahrung für alle Nutzer:

1. **Gesetzliche Pflicht** — In vielen Regionen ist WCAG-Konformität für Web-Anwendungen vorgeschrieben
2. **Erweiterte Nutzerbasis** — Ca. 15% der Weltbevölkerung leben mit einer Behinderung
3. **Verbesserte UX für alle** — Tastaturnavigation, klare Kontraste und strukturierte Inhalte helfen allen Nutzern
4. **SEO-Vorteile** — Semantisches HTML und ARIA-Landmarks verbessern die Auffindbarkeit

---

## 2. Anforderungen

### 2.1 WCAG-Konformität

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS die WCAG 2.1 Level AA Richtlinien vollständig erfüllen. | MUSS |
| R-002 | WCAG 2.1 Level AAA Kriterien SOLLEN wo möglich erfüllt werden, sind aber nicht verpflichtend. | SOLL |

### 2.2 Tastaturnavigation

| # | Regel | Stufe |
|---|-------|-------|
| R-003 | Alle interaktiven Elemente MÜSSEN per Tastatur (Tab, Shift+Tab, Enter, Space, Escape, Pfeiltasten) erreichbar und bedienbar sein. | MUSS |
| R-004 | Die Tab-Reihenfolge MUSS der visuellen Lesereihenfolge entsprechen (logische Reihenfolge im DOM). | MUSS |
| R-005 | Der aktuell fokussierte Element MUSS einen deutlich sichtbaren Focus-Indikator haben (mindestens 2px Outline, Kontrastunterschied ≥3:1 zum Hintergrund). | MUSS |
| R-006 | Focus DARF NICHT in Modalen, Dropdowns oder anderen Overlay-Elementen gefangen werden — Escape MUSS das Overlay schließen und den Fokus zurücksetzen. | MUSS |
| R-007 | Skip-Links MÜSSEN implementiert werden, um die Hauptnavigation zu überspringen und direkt zum Hauptinhalt zu gelangen. | MUSS |
| R-008 | Tastaturfallen (Focus-Traps) DÜRFEN nur in Modalen eingesetzt werden und MÜSSEN per Escape verlassen werden können. | MUSS |

### 2.3 Screenreader-Kompatibilität

| # | Regel | Stufe |
|---|-------|-------|
| R-009 | Alle interaktiven Elemente MÜSSEN aussagekräftige ARIA-Labels oder sichtbare Labels haben. | MUSS |
| R-010 | Die Seitenstruktur MUSS ARIA-Landmarks verwenden (`banner`, `navigation`, `main`, `contentinfo`). | MUSS |
| R-011 | Dynamische Inhaltsänderungen MÜSSEN über ARIA-Live-Regions (`aria-live="polite"` oder `aria-live="assertive"`) angekündigt werden. | MUSS |
| R-012 | Bilder MÜSSEN aussagekräftige `alt`-Texte haben. Dekorative Bilder MÜSSEN `alt=""` und `aria-hidden="true"` verwenden. | MUSS |
| R-013 | Formulare MÜSSEN Labels haben, die programmatisch mit dem zugehörigen Eingabefeld verknüpft sind (`<label for="...">`). | MUSS |
| R-014 | Fehlermeldungen MÜSSEN programmatisch mit dem betroffenen Feld verknüpft sein (`aria-describedby`). | MUSS |

### 2.4 Farbkontraste

| # | Regel | Stufe |
|---|-------|-------|
| R-015 | Text MUSS ein Kontrastverhältnis von mindestens 4.5:1 gegenüber dem Hintergrund haben (WCAG AA). | MUSS |
| R-016 | Großer Text (≥18pt oder ≥14pt fett) MUSS ein Kontrastverhältnis von mindestens 3:1 haben. | MUSS |
| R-017 | UI-Komponenten und grafische Objekte MÜSSEN ein Kontrastverhältnis von mindestens 3:1 gegenüber angrenzenden Farben haben. | MUSS |
| R-018 | Informationen DÜRFEN NICHT ausschließlich über Farbe vermittelt werden — zusätzliche Indikatoren (Icons, Muster, Text) MÜSSEN verwendet werden. | MUSS |

### 2.5 Schriftgrößen & Zoom

| # | Regel | Stufe |
|---|-------|-------|
| R-019 | Die Anwendung MUSS bei einer Schriftvergrößerung bis 200% vollständig nutzbar bleiben (kein Verlust von Inhalten oder Funktionalität). | MUSS |
| R-020 | Schriftgrößen MÜSSEN in relativen Einheiten (rem, em) definiert werden, nicht in absoluten Pixelwerten. | MUSS |
| R-021 | Die Anwendung SOLL bei Browser-Zoom bis 400% im Reflow-Modus nutzbar bleiben (WCAG 1.4.10). | SOLL |

### 2.6 Animationen & Bewegung

| # | Regel | Stufe |
|---|-------|-------|
| R-022 | Die Anwendung MUSS die `prefers-reduced-motion` Media-Query respektieren und Animationen reduzieren oder deaktivieren. | MUSS |
| R-023 | Kein Inhalt DARF mehr als dreimal pro Sekunde blinken (Epilepsie-Prävention). | MUSS |

---

## 3. Wireframe-Beispiele

### 3.1 Skip-Link-Verhalten

```
┌──────────────────────────────────┐
│ ┌──────────────────────────────┐ │
│ │ Zum Hauptinhalt springen ➜  │ │  ← Nur bei Tab sichtbar
│ └──────────────────────────────┘ │
│  Logo   Nav1   Nav2   Nav3  👤  │
├──────────────────────────────────┤
│                                  │
│  Hauptinhalt                     │  ← Fokus springt hierhin
│                                  │
└──────────────────────────────────┘
```

### 3.2 Focus-Indikator

```
  Nicht fokussiert:           Fokussiert:
  ┌──────────────┐           ╔══════════════╗
  │  Button      │           ║  Button      ║  ← 2px Outline
  └──────────────┘           ╚══════════════╝
                              ↑ Kontrastreich
```

### 3.3 Farbe + zusätzlicher Indikator

```
  ❌ Nur Farbe:               ✅ Farbe + Icon:
  ┌──────────────┐           ┌──────────────┐
  │  ● Erfolg    │           │  ✓ Erfolg    │
  │  ● Fehler    │           │  ✗ Fehler    │
  │  ● Warnung   │           │  ⚠ Warnung   │
  └──────────────┘           └──────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **WCAG-Konformität**
    - [ ] Automatisierte WCAG 2.1 AA Prüfung besteht (z.B. axe-core, Lighthouse)
    - [ ] Manuelle Prüfung der Tastaturnavigation auf allen Seiten
    - [ ] Screenreader-Test mit mindestens einem Tool (z.B. NVDA, VoiceOver)
- [ ] **Tastaturnavigation**
    - [ ] Alle Seiten sind vollständig per Tastatur bedienbar
    - [ ] Tab-Reihenfolge ist logisch und konsistent
    - [ ] Focus-Indikator ist auf allen interaktiven Elementen sichtbar
    - [ ] Skip-Links sind implementiert und funktional
    - [ ] Modale können per Escape geschlossen werden
- [ ] **Screenreader**
    - [ ] ARIA-Landmarks sind auf jeder Seite gesetzt
    - [ ] Alle Bilder haben `alt`-Texte
    - [ ] Formularfelder haben programmatisch verknüpfte Labels
    - [ ] Dynamische Änderungen werden über Live-Regions angekündigt
- [ ] **Kontraste**
    - [ ] Alle Texte erfüllen das 4.5:1 Kontrastverhältnis
    - [ ] Keine Information wird ausschließlich über Farbe vermittelt
- [ ] **Schriftgrößen**
    - [ ] Anwendung bleibt bei 200% Zoom vollständig nutzbar
    - [ ] Schriftgrößen sind in rem/em definiert
- [ ] **Testing**
    - [ ] axe-core oder Lighthouse Accessibility-Score ≥90
    - [ ] Manuelle Tests mit Tastatur und Screenreader durchgeführt
    - [ ] Automatisierte Accessibility-Tests in CI-Pipeline integriert

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Rechtliche Konsequenzen** | Klagen wegen mangelnder Barrierefreiheit | Mittel | WCAG-Compliance automatisiert prüfen |
| **Nutzerausschluss** | 15% der potenziellen Nutzer können die Anwendung nicht verwenden | Hoch | Accessibility von Anfang an mitdenken |
| **Schlechte Tastaturnavigation** | Power-User und Nutzer mit Einschränkungen können nicht effizient arbeiten | Hoch | Tab-Reihenfolge bei jedem Feature prüfen |
| **Unlesbare Texte** | Texte bei schlechtem Kontrast oder kleiner Schrift nicht lesbar | Mittel | Design-System mit geprüften Farbkombinationen |
| **Fehlende Screenreader-Unterstützung** | Blinde und sehbehinderte Nutzer können die Anwendung nicht verwenden | Mittel | ARIA-Labels als Teil der Komponenten-Checklist |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
