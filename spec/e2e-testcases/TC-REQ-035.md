---
req_id: REQ-035
title: KI-gestütztes Fachbegriff-Glossar mit On-Demand-Erklärungen
category: KI & Beratung
test_count: 1
coverage_areas:
  - Route-Erreichbarkeit (Smoke) für die Glossar-Einstiegsseite
generated: 2026-07-29
version: "0.1"
---

# TC-REQ-035: KI-gestütztes Fachbegriff-Glossar

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-035 KI-gestütztes Fachbegriff-Glossar mit On-Demand-Erklärungen v1.0**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

**Hinweis zum Geltungsbereich dieses Dokuments:** Zum Zeitpunkt der Erstellung deckt dieses Dokument ausschließlich die Grunderreichbarkeit der Glossar-Route ab (Smoke-Test-Ebene), da nur ein entsprechender Selenium-Scaffold-Test existiert (`tests/e2e/test_req035_glossar.py`). Eine vollständige Ableitung aller Testfälle aus `spec/req/REQ-035_KI-Fachbegriff-Glossar.md` (`<TermTooltip>`-Popover, Verlinkung verwandter Begriffe, Erfahrungsstufen-Anpassung, Light-Modus-Verfügbarkeit ohne Login) ist noch offen und nicht Gegenstand dieser Datei.

---

## 1. Route-Erreichbarkeit (Smoke)

### TC-035-001: Glossar-Einstiegsseite ist erreichbar (Smoke)

**Requirement**: REQ-035 (Route-Verdrahtung als Voraussetzung für alle weiteren Glossar-Fälle)
**Priority**: Medium
**Category**: Smoke
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zur Glossar-Einstiegsseite (`/glossar`)

**Erwartete Ergebnisse**:
- Die Seite lädt ohne Fehler
- Ein Markierungstext oder -bereich für "Glossar" ist sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-035, glossar, smoke, route-erreichbarkeit]

---

## Offene Abschnitte

Aus `spec/req/REQ-035_KI-Fachbegriff-Glossar.md` wurde noch kein Testfall für folgende Bereiche abgeleitet (keine automatisierten Tests vorhanden, aus denen sich der Geltungsbereich ableiten ließe):

- `<TermTooltip>`-Popover beim Klick auf das Fragezeichen-Icon
- Verlinkung und Weiterklicken zu verwandten Begriffen innerhalb der Erklärung
- Erfahrungsstufen-Anpassung der Erklärungstiefe (Beginner / Intermediate / Expert)
- Verfügbarkeit im Light-Modus ohne Login
- Konsistenz der Begriffsdefinitionen innerhalb eines Gemeinschaftsgarten-Tenants

## Abdeckungsmatrix

| Spec-Abschnitt | Beschreibung | Testfälle |
|---|---|---|
| Route-Erreichbarkeit (Smoke) | Glossar-Einstiegsseite | TC-035-001 |
