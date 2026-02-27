# Wichtige Prompts fuer die Arbeit mit Claude Code Agents

Kurzreferenz der effektivsten Prompts fuer das Kamerplanter-Projekt.

---

## Qualitaetssicherung

### Tech-Stack Konformitaet

> Stelle sicher, dass sich der Full-Stack-Entwickler Agent strikt an den in `spec/stack.md` definierten Technologie-Stack haelt (Python 3.14+, FastAPI, ArangoDB, React 18, TypeScript, MUI, Redux Toolkit).

### Architektur-Einhaltung

> Pruefe, ob die Implementierung die 5-Schichten-Architektur (NFR-001) einha: Presentation → API → Business Logic → Data Access → Persistence. Kein direkter DB-Zugriff aus dem Frontend.

### Sprachkonvention

> Quellcode muss vollstaendig auf Englisch sein (NFR-003). Dokumentation und Spezifikationen auf Deutsch.

---

## Anforderungsanalyse

### Widerspruchspruefung

> Analysiere die Anforderungsdokumente unter `spec/req/` auf Widersprueche zwischen funktionalen und non-funktionalen Anforderungen.

### Agrarbiologische Pruefung

> Pruefe die Anforderung REQ-XXX auf fachliche Korrektheit aus agrarbiologischer Sicht (Phasenmodelle, VPD-Bereiche, NPK-Profile, Karenz-Zeiten).

### Konsistenz zwischen REQs

> Pruefe REQ-XXX auf Konsistenz mit allen referenzierten Anforderungen. Identifiziere fehlende Schnittstellen oder widerspruechliche Definitionen.

---

## Implementierung

### Feature implementieren

> Implementiere REQ-XXX gemaess der Spezifikation unter `spec/req/REQ-XXX_*.md`. Beachte NFR-001 (Schichtarchitektur), NFR-003 (Englischer Code), NFR-006 (Error Handling) und den Tech-Stack in `spec/stack.md`.

### API-Endpunkt erstellen

> Erstelle die API-Endpunkte fuer [Feature]. Folge dem bestehenden Pattern: Router → Service → Engine → Repository. Validierung mit Pydantic v2.

### React-Seite erstellen

> Erstelle die Frontend-Seiten fuer REQ-XXX. Verwende MUI-Komponenten, Redux Toolkit fuer State, react-i18next fuer DE/EN Uebersetzungen, und folge dem bestehenden Seitenaufbau (List → Detail → Create Dialog).

---

## Testing

### E2E-Testfaelle ableiten

> Extrahiere alle E2E-Testfaelle aus REQ-XXX. Erstelle strukturierte, RAG-optimierte Testfall-Dokumente mit Traceability zur Anforderung.

### Selenium-Tests generieren

> Generiere NFR-008-konforme Selenium-Tests fuer REQ-XXX mit Page-Object-Pattern, Screenshot-Checkpoints und automatischer Testprotokoll-Generierung.

### Bestehende Tests reviewen

> Ueberpr\u00fcfe die Selenium-Tests unter `tests/e2e/test_req0XX_*.py` auf NFR-008-Konformitaet, Best Practices und Testabdeckung.

---

## Dokumentation

### MkDocs-Seite erstellen

> Erstelle eine endnutzerfreundliche Dokumentationsseite fuer [Thema] im MkDocs-Material-Format. Mehrsprachig (DE/EN) gemaess NFR-005.

### ADR schreiben

> Schreibe ein Architecture Decision Record (ADR) fuer die Entscheidung [Thema]. Dokumentiere Kontext, Optionen, Entscheidung und Konsequenzen.

---

## Kombinierte Workflows

### Neues Feature komplett umsetzen

> 1. Pruefe REQ-XXX auf Widersprueche mit bestehenden Anforderungen
> 2. Implementiere Backend (Engine + Service + API) und Frontend (Pages + Redux + i18n)
> 3. Leite E2E-Testfaelle ab und generiere Selenium-Tests
> 4. Erstelle die zugehoerige MkDocs-Dokumentation

### Release-Vorbereitung

> 1. Fuehre eine Widerspruchsanalyse ueber alle geaenderten REQs durch
> 2. Reviewe alle neuen Selenium-Tests auf NFR-008-Konformitaet
> 3. Pruefe Tech-Stack-Konformitaet der neuen Implementierungen
> 4. Aktualisiere den Agent-Katalog und die Dokumentation

---

## Tipps

- **REQ-Nummer immer angeben** — Agents arbeiten praeziser mit konkreter Anforderungsreferenz
- **NFRs explizit nennen** — besonders NFR-001 (Architektur), NFR-003 (Sprache), NFR-006 (Errors), NFR-008 (Testing)
- **Spec-Pfade referenzieren** — `spec/req/REQ-XXX_*.md` fuer Anforderungen, `spec/stack.md` fuer Tech-Stack
- **Bestehende Patterns erwaehnen** — "folge dem bestehenden Pattern" spart Rueckfragen
