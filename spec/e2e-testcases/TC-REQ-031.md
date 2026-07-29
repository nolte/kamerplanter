---
req_id: REQ-031
title: KI-Assistent & Wissensvermittlung (RAG-basiert)
category: KI & Beratung
test_count: 1
coverage_areas:
  - Route-Erreichbarkeit (Smoke) für die KI-Assistent-Einstiegsseite
generated: 2026-07-29
version: "0.1"
---

# TC-REQ-031: KI-Assistent & Wissensvermittlung

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-031 KI-Assistent & Wissensvermittlung (RAG-basiert) v2.0**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine API-Calls, HTTP-Statuscodes oder Datenbankabfragen erscheinen in diesen Testfällen. Alle Aussagen beschreiben, was der Nutzer sieht, anklickt, eintippt und auf dem Bildschirm erwartet.

**Hinweis zum Geltungsbereich dieses Dokuments:** Zum Zeitpunkt der Erstellung deckt dieses Dokument ausschließlich die Grunderreichbarkeit der KI-Assistent-Route ab (Smoke-Test-Ebene), da nur ein entsprechender Selenium-Scaffold-Test existiert (`tests/e2e/test_req031_ki_assistent.py`). Eine vollständige Ableitung aller Testfälle aus `spec/req/REQ-031_KI-Assistent-Pflanzenberatung.md` (Tipp-Karten, Tipp des Tages, Chat-Dialog, "Warum?"-Buttons, Consent-Workflow, Provider-Konfiguration) ist noch offen und nicht Gegenstand dieser Datei.

---

## 1. Route-Erreichbarkeit (Smoke)

### TC-031-001: KI-Assistent-Einstiegsseite ist erreichbar (Smoke)

**Requirement**: REQ-031 (Route-Verdrahtung als Voraussetzung für alle weiteren KI-Assistent-Fälle)
**Priority**: Medium
**Category**: Smoke
**Preconditions**:
- Nutzer ist eingeloggt

**Testschritte**:
1. Nutzer navigiert zur KI-Assistent-Einstiegsseite (`/ki-assistent`)

**Erwartete Ergebnisse**:
- Die Seite lädt ohne Fehler
- Ein Markierungstext oder -bereich für "KI" bzw. "ki-assistent" ist sichtbar

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-031, ki-assistent, smoke, route-erreichbarkeit]

---

## Offene Abschnitte

Aus `spec/req/REQ-031_KI-Assistent-Pflanzenberatung.md` wurde noch kein Testfall für folgende Bereiche abgeleitet (keine automatisierten Tests vorhanden, aus denen sich der Geltungsbereich ableiten ließe):

- Tipp-Karten auf der Pflanzen-Detailseite
- Tipp des Tages auf dem Dashboard
- Chat-Dialog mit Pflanzenkontext
- "Warum?"-Buttons auf KI-generierten Empfehlungen
- Dreistufiger Feature-Toggle (Deployment / Tenant / User-Consent)
- Provider- und Consent-Konfiguration (Ollama / Anthropic / OpenAI-kompatibel)
- Light-Modus-Verhalten des KI-Assistenten

## Abdeckungsmatrix

| Spec-Abschnitt | Beschreibung | Testfälle |
|---|---|---|
| Route-Erreichbarkeit (Smoke) | KI-Assistent-Einstiegsseite | TC-031-001 |
