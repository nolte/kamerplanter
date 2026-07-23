# AP-21 — Audit-/Backlog-Hygiene (kein Produktivcode)

> Bezug: Befunde **GAP-B1**, **GAP-B17** aus `../code-review-fable5-2026-07.md`. Aufwand: **S**.
>
> **Status 2026-07-23 — erledigt durch Entfernung.** Der hier zu pflegende April-Audit-Layer
> (`.audits/req-coverage-audit.md`, `.audits/execution-roadmap.md`, `.audits/phase-0-drift-findings.md`,
> `.audits/implementation-plan.md`) wurde als veraltet/irreführend entfernt statt nachgepflegt. Das
> Aggregat ist bei Bedarf per `.claude/skills/req-coverage-audit/run_audit.py` neu erzeugbar. Die
> konkreten Schritte unten sind damit gegenstandslos und nur noch als Historie zu lesen.

## Ziel
Das Backlog spiegelt den echten Code-Stand wider, sodass die Priorisierung nicht durch
veraltete Drift-Marker oder ein irreführendes Aggregat verzerrt wird.

## Teil A — Geschlossene DRIFTs als geschlossen markieren (GAP-B17)

Im Code **bereits umgesetzt**, aber im Backlog noch als offen geführt:

- **REQ-014 v1.6** (`slot_keys`, `_ms`-Suffix, Wasserquellen-Kaskade)
  - Belege: `src/backend/app/domain/services/tank_service.py:125,242`, `src/backend/app/domain/models/plant_instance.py:16`
- **REQ-015 v1.6** (CF-005 `expires_at`/410, Light-iCal-Token, VALARM)
  - Belege: `src/backend/app/domain/services/calendar_service.py:308-313`, `src/backend/app/api/v1/calendar/tenant_router.py:38`

### Änderungen
1. `.audits/req-coverage-audit.md` + ggf. `.audits/req-coverage-audit/REQ-014*.md` / `REQ-015*.md`: Status/Drift-Marker auf „geschlossen" setzen, Code-Beleg verlinken.
2. `.audits/execution-roadmap.md`: REQ-014/REQ-015 aus offenen Buckets entfernen.
3. Falls `expectations.yaml`-Drift-Marker existieren: nach Verifikation gegen Code entfernen (gemäß MEMORY-Regel „Drift-Marker bleiben Quelle bis echtem Code-Sync" — der Sync ist hier erfolgt).
4. Auto-Memory `MEMORY.md`-Zeile „Offene DRIFTs" um REQ-014/REQ-015 kürzen.

> ⚠️ Vor dem Streichen jeweils die genannten `file:line` gegenprüfen (die Belege stammen aus
> dem Review, nicht aus einem Full-Diff).

## Teil B — Coverage-Audit-Aggregat entschärfen (GAP-B1)

`.audits/req-coverage-audit.md` meldet „72/72 = 100 % Implementiert", misst aber nur
**Artefakt-Präsenz** (Datei-Globs in `run_audit.py`), nicht Semantik. Mind. 8 REQs sind reine
Scaffolds (REQ-008/016/017/018/026/031/033/035/036).

### Änderungen
1. Die bestehende E1-Warnbox (nennt heute nur REQ-013/022) auf **alle** Scaffold-REQs ausweiten.
2. Optional: in `.claude/skills/req-coverage-audit/run_audit.py` einen Scaffold-Heuristik-Check
   ergänzen (Datei enthält `NotImplementedError`/`placeholder` → als „Scaffold" statt
   „Implementiert" klassifizieren). Nur wenn günstig; sonst rein dokumentarisch.

## Akzeptanzkriterien
- [ ] REQ-014/REQ-015 in `.audits/` + `MEMORY.md` nicht mehr als offener DRIFT geführt, mit Code-Beleg.
- [ ] Coverage-Audit-Warnbox listet alle Scaffold-REQs; „100 %" ist kontextualisiert.
- [ ] Kein Produktivcode angefasst (reine Doku/Audit-Änderung).

## Risiko
Minimal. Rein dokumentarisch. Einziges Risiko: versehentliches Schließen eines DRIFTs, der
doch noch offen ist → durch die `file:line`-Gegenprüfung in Teil A abgesichert.
