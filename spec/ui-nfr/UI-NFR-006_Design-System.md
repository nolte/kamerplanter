---

ID: UI-NFR-006
Titel: Theming & Design-System
Kategorie: UI-Verhalten Unterkategorie: Design-System, Theming, Konsistenz
Technologie: React, TypeScript, MUI, Flutter
Status: Entwurf
Priorität: Mittel
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [design-system, theming, dark-mode, tokens, typography, spacing, colors]
Abhängigkeiten: [UI-NFR-001, UI-NFR-002]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-006: Theming & Design-System

## 1. Business Case

### 1.1 User Story

**Als** Endanwender
**möchte ich** zwischen einem hellen und einem dunklen Modus wählen können
**um** die Anwendung an meine Lichtverhältnisse und persönlichen Präferenzen anzupassen.

**Als** Frontend-Entwickler
**möchte ich** ein konsistentes Design-System mit definierten Tokens
**um** neue Komponenten schnell und einheitlich implementieren zu können.

**Als** Designer
**möchte ich** dass alle UI-Elemente einem gemeinsamen Regelwerk folgen
**um** eine visuell kohärente und professionelle Anwendung sicherzustellen.

### 1.2 Geschäftliche Motivation

Ein konsistentes Design-System reduziert Entwicklungszeit und verbessert die Benutzererfahrung:

1. **Konsistenz** — Nutzer lernen das Interface schneller, wenn alle Elemente gleich aussehen und sich gleich verhalten
2. **Entwicklungsgeschwindigkeit** — Vordefinierte Tokens und Komponenten beschleunigen die Implementierung
3. **Wartbarkeit** — Zentrale Änderungen am Theme wirken sich auf die gesamte Anwendung aus
4. **Barrierefreiheit** — Ein geprüftes Farbsystem stellt sicher, dass Kontraste eingehalten werden

---

## 2. Anforderungen

### 2.1 Light/Dark-Mode

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS einen Light- und einen Dark-Mode unterstützen. | MUSS |
| R-002 | Beim ersten Besuch MUSS die System-Präferenz des Betriebssystems erkannt und angewendet werden (`prefers-color-scheme`). | MUSS |
| R-003 | Der Nutzer MUSS den Modus manuell wechseln können (Toggle in der UI). | MUSS |
| R-004 | Die manuelle Wahl MUSS persistent gespeichert werden (z.B. LocalStorage) und die System-Präferenz überschreiben. | MUSS |
| R-005 | Der Moduswechsel MUSS ohne Flackern (FOUC) oder Neuladen der Seite erfolgen. | MUSS |
| R-006 | Beide Modi MÜSSEN die Kontrast-Anforderungen aus UI-NFR-002 erfüllen. | MUSS |

### 2.2 Farbsystem

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Das Farbsystem MUSS die folgenden semantischen Farbrollen definieren: Primary, Secondary, Error, Warning, Success, Info, Background, Surface, On-Primary, On-Secondary, On-Background, On-Surface. | MUSS |
| R-008 | Jede Farbrolle MUSS für Light- und Dark-Mode separat definiert sein. | MUSS |
| R-009 | Farben DÜRFEN NICHT als direkte Hex-/RGB-Werte in Komponenten verwendet werden — ausschließlich über Design-Tokens. | MUSS |
| R-010 | Das Farbsystem SOLL auf einem HSL-basierten Ansatz aufbauen, um konsistente Varianten (Hover, Active, Disabled) ableiten zu können. | SOLL |

### 2.3 Spacing

| # | Regel | Stufe |
|---|-------|-------|
| R-011 | Alle Abstände MÜSSEN auf einem 4px-Basisraster basieren: 4, 8, 12, 16, 24, 32, 48, 64px. | MUSS |
| R-012 | Spacing-Werte MÜSSEN über Design-Tokens referenziert werden (z.B. `spacing.sm = 8px`, `spacing.md = 16px`). | MUSS |
| R-013 | Komponenten-interne Abstände und Komponenten-externe Abstände SOLLEN unterschiedliche Token-Ebenen verwenden. | SOLL |

### 2.4 Typografie

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Die Anwendung MUSS eine Typografie-Hierarchie definieren: H1, H2, H3, H4, H5, H6, Body1, Body2, Caption, Overline, Button. | MUSS |
| R-015 | Jede Typografie-Stufe MUSS Schriftgröße, Zeilenhöhe, Schriftstärke und Buchstabenabstand definieren. | MUSS |
| R-016 | Schriftgrößen MÜSSEN in rem definiert werden (Basis: 1rem = 16px). | MUSS |
| R-017 | Maximal zwei Schriftfamilien SOLLEN verwendet werden (eine für Überschriften, eine für Fließtext — oder eine einzige durchgängig). | SOLL |
| R-018 | Systemschriften (System-UI-Font-Stack) SOLLEN als Fallback verwendet werden, um zusätzliche Font-Downloads zu vermeiden. | SOLL |

### 2.5 Icons

| # | Regel | Stufe |
|---|-------|-------|
| R-019 | Die Anwendung MUSS ein einziges, konsistentes Icon-Set verwenden (nicht verschiedene Icon-Bibliotheken mischen). | MUSS |
| R-020 | Icons MÜSSEN in verschiedenen Größen verfügbar sein (16, 20, 24, 32px). | MUSS |
| R-021 | Icons mit funktionaler Bedeutung MÜSSEN einen `aria-label` oder begleitenden Text haben. | MUSS |
| R-022 | Dekorative Icons MÜSSEN `aria-hidden="true"` verwenden. | MUSS |

### 2.6 Border-Radii & Schatten

| # | Regel | Stufe |
|---|-------|-------|
| R-023 | Border-Radii MÜSSEN über Design-Tokens definiert werden (z.B. `radius.sm = 4px`, `radius.md = 8px`, `radius.lg = 12px`, `radius.full = 9999px`). | MUSS |
| R-024 | Schatten (Elevation) MÜSSEN in definierten Stufen verwendet werden (z.B. `elevation.1`, `elevation.2`, `elevation.3`) — keine willkürlichen Box-Shadow-Werte. | MUSS |
| R-025 | Im Dark-Mode SOLLEN Schatten durch subtilere Farb- oder Border-Unterschiede ersetzt werden, da Schatten auf dunklen Hintergründen schlecht sichtbar sind. | SOLL |

### 2.7 Token-basiertes Design

| # | Regel | Stufe |
|---|-------|-------|
| R-026 | Alle visuellen Eigenschaften (Farben, Abstände, Schriftgrößen, Radii, Schatten) MÜSSEN über Design-Tokens definiert werden. | MUSS |
| R-027 | Design-Tokens MÜSSEN in einer zentralen Datei oder einem Modul definiert werden, nicht verstreut in einzelnen Komponenten. | MUSS |
| R-028 | Die Token-Struktur SOLL drei Ebenen umfassen: Primitive Tokens (Rohwerte) → Semantic Tokens (Bedeutung) → Component Tokens (komponentenspezifisch). | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Light-Mode vs. Dark-Mode

```
  Light-Mode:                     Dark-Mode:
  ┌────────────────────┐          ┌────────────────────┐
  │ ▓▓ App    [☀/🌙]  │          │ ░░ App    [☀/🌙]  │
  ├────────────────────┤          ├────────────────────┤
  │                    │          │ ░░░░░░░░░░░░░░░░░░ │
  │  Heller            │          │  Dunkler           │
  │  Hintergrund       │          │  Hintergrund       │
  │                    │          │                    │
  │  ┌──────────────┐  │          │  ┌──────────────┐  │
  │  │ Surface Card │  │          │  │ Surface Card │  │
  │  └──────────────┘  │          │  └──────────────┘  │
  │                    │          │                    │
  └────────────────────┘          └────────────────────┘
```

### 3.2 Spacing-Raster (4px-Basis)

```
  4px   ┊
  8px   ┊┊
  12px  ┊┊┊
  16px  ┊┊┊┊
  24px  ┊┊┊┊┊┊
  32px  ┊┊┊┊┊┊┊┊
  48px  ┊┊┊┊┊┊┊┊┊┊┊┊
  64px  ┊┊┊┊┊┊┊┊┊┊┊┊┊┊┊┊
```

### 3.3 Typografie-Hierarchie

```
  H1  ─────────  32px / 2rem     Bold
  H2  ────────   28px / 1.75rem  Bold
  H3  ───────    24px / 1.5rem   Semi-Bold
  H4  ──────     20px / 1.25rem  Semi-Bold
  H5  ─────      18px / 1.125rem Medium
  H6  ────       16px / 1rem     Medium
  Body1 ───      16px / 1rem     Regular
  Body2 ──       14px / 0.875rem Regular
  Caption ─      12px / 0.75rem  Regular
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **Light/Dark-Mode**
    - [ ] Beide Modi sind implementiert und vollständig gestaltet
    - [ ] System-Präferenz wird beim ersten Besuch erkannt
    - [ ] Manueller Toggle ist vorhanden und persistent
    - [ ] Kein Flackern beim Moduswechsel
    - [ ] Beide Modi erfüllen Kontrast-Anforderungen
- [ ] **Farbsystem**
    - [ ] Alle semantischen Farbrollen sind definiert
    - [ ] Keine direkten Farbwerte in Komponenten
    - [ ] Farben für Light- und Dark-Mode separat definiert
- [ ] **Spacing & Typografie**
    - [ ] 4px-Raster wird durchgängig verwendet
    - [ ] Typografie-Hierarchie ist definiert und dokumentiert
    - [ ] Schriftgrößen sind in rem definiert
- [ ] **Icons**
    - [ ] Ein einziges Icon-Set wird verwendet
    - [ ] Funktionale Icons haben `aria-label`
    - [ ] Dekorative Icons sind `aria-hidden`
- [ ] **Design-Tokens**
    - [ ] Alle visuellen Eigenschaften sind tokenisiert
    - [ ] Tokens sind zentral definiert
    - [ ] Token-Struktur ist dokumentiert
- [ ] **Testing**
    - [ ] Visueller Regressionstest (Snapshot-Tests) für Light- und Dark-Mode
    - [ ] Kontrast-Checks für beide Modi
    - [ ] Keine hardcodierten Farb-/Spacing-Werte in Komponenten (Lint-Regel)

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Inkonsistentes Design** | Anwendung wirkt unprofessionell, Nutzervertrauen sinkt | Hoch | Token-basiertes Design-System, Lint-Regeln |
| **Dark-Mode-Kontrast-Probleme** | Texte im Dark-Mode nicht lesbar | Mittel | Separates Farbset für Dark-Mode, automatisierte Kontrast-Checks |
| **Wildwuchs bei Farben/Abständen** | Jede Komponente sieht anders aus | Hoch | Zentrale Tokens, Code-Review-Checkliste |
| **Inkonsistente Icons** | Unterschiedliche Icon-Stile verwirren den Nutzer | Mittel | Ein Icon-Set als Abhängigkeit festlegen |
| **Schwierige Theme-Änderungen** | Globale Änderungen erfordern Anpassungen in vielen Dateien | Hoch | Alle Werte über Tokens referenzieren |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
