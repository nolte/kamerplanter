---
req_id: UI-NFR-002
title: Barrierefreiheit — axe-core gegen die zusammengesetzte Anwendung
category: Qualitaetssicherung / Barrierefreiheit
test_count: 2
coverage_areas:
  - axe-core-Durchlauf gegen die laufende Anwendung (nicht gegen Einzelkomponenten)
  - Negativkontrolle — ein gesaeter Verstoß macht den Durchlauf rot
generated: 2026-08-22
version: "1.0"
---

# TC-UI-NFR-002: Barrierefreiheit der zusammengesetzten Seite

Diese Testfaelle decken die Luecke, die **`vitest-axe` auf Komponentenebene nicht
sehen kann**. Ein Komponententest rendert eine Komponente in einen leeren
Container; Landmark-Struktur, Ueberschriften-Reihenfolge ueber eine ganze Seite
und der Kontrast zwischen der Farbe einer Komponente und dem Hintergrund, den ein
Vorfahre gemalt hat, entstehen erst, wenn die Seite zusammengesetzt ist.

Aus Issue #1095, dem E2E-Strang der Folgearbeiten zu #1060.

## TC-UINFR002-001: axe-Durchlauf ueber die Kernroute

**Anforderung**: UI-NFR-002
**Prioritaet**: Mittel
**Kategorie**: Barrierefreiheit / zusammengesetzte Seite
**Vorbedingungen**:
- Der Stapel laeuft; ein Nutzer ist angemeldet

**Testschritte**:
1. Nutzer oeffnet die Pflanzenliste
2. Der axe-Durchlauf wird gegen die gerenderte Seite ausgefuehrt
3. Nutzer legt ueber den echten Anlegen-Dialog eine Pflanzeninstanz an (Selbstversorgung nach NFR-008a §2)
4. Der axe-Durchlauf wird gegen die Detailseite dieser Instanz ausgefuehrt

**Erwartetes Ergebnis**:
- Beide Seiten werden **tatsaechlich** gescannt: die Detailseite zeigt die
  Instanz-ID der eben angelegten Pflanze, sodass der zweite Durchlauf nicht
  versehentlich dieselbe Seite ein zweites Mal misst
- Gefundene Verstoesse werden mit Regel, Wirkung und **Selektor** protokolliert
- Der Durchlauf ist zunaechst **beratend**: Befunde machen den Lauf nicht rot
  (Beforderung nach gemessener Historie, NFR-018 §4)

**Nachbedingungen**:
- Das Protokoll enthaelt je gescannter Seite die Zahl der Verstoesse

**Tags**: [ui-nfr-002, barrierefreiheit, axe, journey]

---

## TC-UINFR002-002: Negativkontrolle — ein gesaeter Verstoß wird gemeldet

**Anforderung**: UI-NFR-002
**Prioritaet**: Hoch
**Kategorie**: Barrierefreiheit / Selbstpruefung des Testmittels
**Vorbedingungen**:
- Der Stapel laeuft

**Testschritte**:
1. Der axe-Durchlauf wird gegen die Landeseite ausgefuehrt und stellt fest,
   dass `color-contrast` dort **nicht** bereits verletzt ist
2. Ein Absatz mit hellgrauer Schrift auf Weiß wird in die Seite eingefuegt
3. Der axe-Durchlauf wird erneut ausgefuehrt

**Erwartetes Ergebnis**:
- Der zweite Durchlauf meldet `color-contrast`, und der gemeldete Selektor
  benennt das eingefuegte Element
- Faellt Schritt 1 aus — die Landeseite verletzt die Regel bereits —, schlaegt
  der Testfall mit einer Meldung fehl, die zum Saeen einer anderen Regel auffordert:
  eine Kontrolle, die einen vorbestehenden Verstoss nicht vom gesaeten
  unterscheiden kann, kontrolliert nichts

**Nachbedingungen**:
- Das eingefuegte Element verschwindet mit der naechsten Navigation; es wird
  nirgends persistiert

**Warum dieser Testfall existiert**: Ein Durchlauf, von dem nie gezeigt wurde,
dass er fehlschlagen **kann**, ist nicht von einem zu unterscheiden, der es
nicht kann. Ohne diesen Fall beweist ein gruenes TC-UINFR002-001 nur, dass eine
Funktion eine Liste zurueckgegeben hat.

**Tags**: [ui-nfr-002, barrierefreiheit, axe, negativkontrolle]
