---
name: ha-derive
description: "Leitet aus einem bestehenden REQ-Dokument konkrete Home-Assistant-Integrationsanforderungen ab (Entity-Designs, API-Abhaengigkeiten, Coordinator-Erweiterungen, Blueprints). Nutze diesen Skill wenn HA-spezifische Anforderungen aus funktionalen Requirements abgeleitet werden sollen."
argument-hint: "[REQ-nnn]"
disable-model-invocation: true
---

# HA-Integrationsanforderungen ableiten: $ARGUMENTS

## Schritt 1: Kontext laden

1. Lies die bestehende HA-Referenzarchitektur:
   - `spec/ha-integration/HA-CUSTOM-INTEGRATION.md`
2. Lies das angegebene REQ-Dokument:
   - Suche `spec/req/$ARGUMENTS_*.md` (Glob-Pattern, z.B. `spec/req/REQ-005_*.md`)
3. Lies die relevanten NFRs fuer Kontext:
   - `spec/nfr/NFR-001_Separation-of-Concerns.md` (Architektur-Schichten)
   - `spec/stack.md` (Tech-Stack)
4. Pruefe ob bereits ein HA-Dokument fuer dieses REQ existiert:
   - Suche `spec/ha-integration/HA-$ARGUMENTS_*.md`

Falls das REQ-Dokument nicht gefunden wird, melde den Fehler und brich ab.

## Schritt 2: Ableitung durchfuehren

Starte einen Task mit dem `ha-integration-requirements-engineer` Agent (aus `.claude/agents/`):

**Prompt:**
"Analysiere das REQ-Dokument `{dateipfad}` und leite daraus konkrete HA-Integrationsanforderungen ab. Nutze die bestehende HA-CUSTOM-INTEGRATION.md als Referenzarchitektur. Strukturiere die Ausgabe nach dem Drei-Seiten-Modell (A: KP→HA Export, B: HA→KP Import, C: KP→HA Aktorik)."

## Schritt 3: Ergebnis schreiben

Schreibe das Ergebnis als Markdown-Datei nach:

```
spec/ha-integration/HA-{REQ-nnn}_{kurztitel}.md
```

Dabei:
- `{REQ-nnn}` = die REQ-Nummer aus dem Argument (z.B. `REQ-005`)
- `{kurztitel}` = Kurztitel aus dem REQ-Dokument, Kebab-Case (z.B. `Hybrid-Sensorik`)

Das Dokument MUSS folgende Struktur haben:

```markdown
# HA-{REQ-nnn}: {Titel} — Home Assistant Integration

> Abgeleitet aus: {REQ-nnn} {Titel} v{version}
> Referenz: HA-CUSTOM-INTEGRATION.md
> Erstellt: {datum}

## 1. Uebersicht
{Zusammenfassung der HA-relevanten Aspekte dieses REQs}

## 2. Seite A: KP → HA Export (Entities)
{Entity-Designs mit device_class, state_class, unit_of_measurement, Attributen}

## 3. Seite B: HA → KP Import (Sensordaten, Events)
{API-Abhaengigkeiten, Coordinator-Erweiterungen, Polling-Intervalle}

## 4. Seite C: KP → HA Aktorik (Services, Automations)
{Service-Definitionen, Automation-Blueprints, Event-Trigger}

## 5. API-Abhaengigkeiten
{Bestehende und neue API-Endpoints die benoetigt werden}

## 6. Coordinator-Erweiterungen
{Neue DataUpdateCoordinator-Domaenen oder Erweiterungen bestehender}

## 7. Offene Fragen
{Ungeloeste Designentscheidungen}
```

## Schritt 4: Bestaetigung

Melde dem Nutzer:
- Dateipfad des erstellten Dokuments
- Anzahl der abgeleiteten Entities, Services und Blueprints
- Offene Fragen die noch geklaert werden muessen
