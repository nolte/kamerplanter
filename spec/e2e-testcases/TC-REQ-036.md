---
req_id: REQ-036
title: Strukturierter KI-Diagnose-Assistent (Multi-Step, Symptom-Katalog, Foto-Anhang)
category: KI & Beratung
test_count: 1
coverage_areas:
  - Route-Erreichbarkeit (Smoke) für die Diagnose-Einstiegsseite
generated: 2026-07-29
version: "0.1"
---

# TC-REQ-036: Strukturierter KI-Diagnose-Assistent

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-036 Strukturierter KI-Diagnose-Assistent (Multi-Step, Symptom-Katalog, Foto-Anhang) v1.0**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

**Hinweis zum Geltungsbereich dieses Dokuments:** Zum Zeitpunkt der Erstellung deckt dieses Dokument ausschließlich die Grunderreichbarkeit der Diagnose-Route ab (Smoke-Test-Ebene), da nur ein entsprechender Selenium-Scaffold-Test existiert (`tests/e2e/test_req036_diagnose.py`). Eine vollständige Ableitung aller Testfälle aus `spec/req/REQ-036_KI-Diagnose-Assistent.md` (Symptom-Katalog-Auswahl, Pflanzen-Kontext-Bestätigung, optionaler Foto-Anhang, Top-3-Diagnose, Diagnose-Historie, IPM-Brücke zu Behandlungsvorschlägen, Retention-Konfiguration) ist noch offen und nicht Gegenstand dieser Datei.

---

## 1. Route-Erreichbarkeit (Smoke)

### TC-036-001: Diagnose-Einstiegsseite ist erreichbar (Smoke)

**Requirement**: REQ-036 (Route-Verdrahtung als Voraussetzung für alle weiteren Diagnose-Fälle)
**Priority**: Medium
**Category**: Smoke
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zur Diagnose-Einstiegsseite (`/diagnose`)

**Erwartete Ergebnisse**:
- Die Seite lädt ohne Fehler
- Ein Markierungstext oder -bereich für "Diagnose" ist sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-036, diagnose, smoke, route-erreichbarkeit]

---

## Offene Abschnitte

Aus `spec/req/REQ-036_KI-Diagnose-Assistent.md` wurde noch kein Testfall für folgende Bereiche abgeleitet (keine automatisierten Tests vorhanden, aus denen sich der Geltungsbereich ableiten ließe):

- Schritt 1 — Symptom-Auswahl aus dem kuratierten Katalog
- Schritt 2 — Pflanzen-Kontext-Bestätigung/-Präzisierung (Pflanze, Phase, Substrat, jüngste Werte)
- Schritt 3 — optionaler Foto-Anhang
- Top-3-Diagnose mit konkreten Handlungsempfehlungen
- Diagnose-Historie pro Pflanze
- IPM-Brücke (REQ-010) von Diagnose zu Behandlungsvorschlag mit Karenzzeit
- Kurz- vs. Lang-Retention-Konfiguration für Diagnose-Sessions (30 Tage / 1 Jahr)

## Abdeckungsmatrix

| Spec-Abschnitt | Beschreibung | Testfälle |
|---|---|---|
| Route-Erreichbarkeit (Smoke) | Diagnose-Einstiegsseite | TC-036-001 |
