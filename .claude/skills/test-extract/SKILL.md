---
name: test-extract
description: "Extrahiert aus einem REQ-Dokument alle testbaren End-to-End-Szenarien und erstellt strukturierte Testfall-Dokumente. Nutze diesen Skill wenn E2E-Testfaelle aus Anforderungen abgeleitet, Testabdeckung geprueft oder Testfall-Dokumentation erstellt werden soll."
argument-hint: "[REQ-nnn]"
disable-model-invocation: true
---

# E2E-Testfaelle extrahieren: $ARGUMENTS

## Schritt 1: Kontext laden

1. Lies das angegebene REQ-Dokument:
   - Suche `spec/req/$ARGUMENTS_*.md` (Glob-Pattern)
2. Lies relevante NFRs:
   - `spec/nfr/NFR-008_*.md` (Testing-Anforderungen, falls vorhanden)
   - `spec/nfr/NFR-001_*.md` (Architektur — fuer Schicht-Verstaendnis)
3. Pruefe bestehende Testfaelle:
   - Suche `tests/e2e/testcases/TC-$ARGUMENTS_*.md`
   - Suche `tests/e2e/test_${req_lower}*.py` fuer bereits implementierte Tests
4. Pruefe bestehende Page Objects:
   - Suche `tests/e2e/pages/*.py`

Falls das REQ-Dokument nicht gefunden wird, melde den Fehler und brich ab.

## Schritt 2: Testfaelle extrahieren

Starte einen Task mit dem `e2e-testcase-extractor` Agent:

**Prompt:**
"Extrahiere aus dem REQ-Dokument `{dateipfad}` alle testbaren End-to-End-Szenarien. Beruecksichtige dabei die bestehenden Page Objects und bereits implementierten Tests. Erstelle RAG-optimierte Testfall-Dokumente."

## Schritt 3: Ergebnis schreiben

Stelle sicher, dass das Verzeichnis `tests/e2e/testcases/` existiert.

Schreibe das Ergebnis nach:
```
tests/e2e/testcases/TC-{REQ-nnn}_{kurztitel}.md
```

Jedes Testfall-Dokument MUSS folgende Struktur haben:

```markdown
# Testfaelle: {REQ-nnn} — {Titel}

> Quelle: {REQ-nnn} {Titel} v{version}
> Erstellt: {datum}
> Anzahl Testfaelle: {n}

## Uebersicht
{Zusammenfassung der abgedeckten Funktionsbereiche}

## Testfaelle

### TC-{REQ-nnn}-001: {Testfall-Titel}
- **Prioritaet:** Hoch/Mittel/Niedrig
- **Vorbedingungen:** {Setup-Schritte}
- **Schritte:**
  1. {Schritt 1}
  2. {Schritt 2}
- **Erwartetes Ergebnis:** {Was soll passieren}
- **Abgedeckte Anforderungen:** {REQ-Abschnitt-Referenzen}

### TC-{REQ-nnn}-002: ...

## Abdeckungsmatrix
| REQ-Abschnitt | Testfaelle | Status |
|---------------|-----------|--------|
| §X.Y Titel    | TC-001, TC-003 | Abgedeckt |

## Nicht testbare Anforderungen
{Anforderungen die nicht als E2E-Test abbildbar sind, mit Begruendung}
```

## Schritt 4: Bestaetigung

Melde dem Nutzer:
- Dateipfad des erstellten Dokuments
- Anzahl extrahierter Testfaelle (nach Prioritaet)
- Abdeckungsgrad gegenueber den REQ-Abschnitten
- Bereits implementierte Tests die gefunden wurden
