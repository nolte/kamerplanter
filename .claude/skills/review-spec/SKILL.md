---
name: review-spec
description: "Startet ein paralleles Spec-Review mit mehreren spezialisierten Reviewer-Agents (Agrarbiologie, IT-Security, Widerspruchsanalyse, optional Smart-Home). Nutze diesen Skill wenn ein Anforderungsdokument (REQ oder NFR) auf fachliche Korrektheit, Sicherheit und Konsistenz geprueft werden soll."
argument-hint: "[REQ-nnn oder NFR-nnn]"
disable-model-invocation: true
---

# Spec-Review: $ARGUMENTS

## Schritt 1: Dokument aufloesen

Bestimme den Dateipfad anhand des Arguments `$ARGUMENTS`:

- `REQ-nnn` → suche `spec/req/REQ-{nnn}_*.md` (Glob-Pattern)
- `NFR-nnn` → suche `spec/nfr/NFR-{nnn}_*.md` (Glob-Pattern)

Lies das gefundene Dokument. Falls kein Dokument gefunden wird, melde den Fehler und brich ab.

## Schritt 2: Reviewer-Agents parallel starten

Starte die folgenden Reviewer-Agents **parallel** via Task-Tool:

### Immer starten:

1. **agrobiology-requirements-reviewer** (nur bei REQ-*, nicht bei NFR-*)
   - Prompt: "Pruefe das folgende Anforderungsdokument auf agrarbiologische Korrektheit, fachliche Vollstaendigkeit und Praxistauglichkeit: `{dateipfad}`"

2. **it-security-requirements-reviewer** (Custom Agent aus `.claude/agents/`)
   - Prompt: "Pruefe das folgende Anforderungsdokument auf IT-Sicherheitsaspekte, Authentifizierung, Autorisierung, Datenschutz und OWASP-relevante Risiken: `{dateipfad}`"

3. **requirements-contradiction-analyzer**
   - Prompt: "Analysiere das Anforderungsdokument `{dateipfad}` auf Widersprueche zu anderen REQ- und NFR-Dokumenten im Repository."

### Bedingt starten:

4. **smart-home-ha-reviewer** — NUR wenn `$ARGUMENTS` eine der folgenden REQs ist:
   REQ-003, REQ-005, REQ-006, REQ-007, REQ-014, REQ-015, REQ-018, REQ-022, REQ-027
   - Prompt: "Pruefe das Anforderungsdokument `{dateipfad}` auf Home-Assistant-Integrationsaspekte, Sensor/Aktor-Anbindung und Smart-Home-Kompatibilitaet."

## Schritt 3: Ergebnisse zusammenfassen

Warte auf alle gestarteten Agents. Fasse die Ergebnisse in folgendem Format zusammen:

```markdown
# Spec-Review: {REQ/NFR-Nummer} — {Titel}

## Zusammenfassung
{1-3 Saetze Gesamtbewertung}

## Agrarbiologie-Review
{Zusammenfassung der Findings, gruppiert nach Kritikalitaet}

## IT-Security-Review
{Zusammenfassung der Findings}

## Widerspruchsanalyse
{Gefundene Widersprueche oder "Keine Widersprueche gefunden"}

## Smart-Home/HA-Review (falls durchgefuehrt)
{Zusammenfassung der HA-relevanten Findings}

## Handlungsempfehlungen
{Priorisierte Liste der empfohlenen Aenderungen}
```
