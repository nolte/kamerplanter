---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "771"
classification: "bug"
secondary-classes: ["refactor"]
route: "direct"
status: draft
created: "2026-07-26"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #771 — fix(e2e): Gherkin tag parser can misread a docstring line and abort the whole collection
- **URL**: https://github.com/nolte/kamerplanter/issues/771
- **Labels**: bug, test
- **Author trust**: `nolte` — Repository-Owner, also im Trusted-Author-Set
  (`spec/claude/trusted-author-injection-guard/`). Keine Kommentare vorhanden,
  keine Fremdtexte im Body.
- **Linked items**: entstanden im Review von PR #770 (BDD-E2E-PoC, Issue #761);
  #770 ist am 2026-07-25 gemergt. `closedByPullRequestsReferences` ist leer.
- **Prior art checked**: keine offene PR adressiert das Thema
  (#787 Audits, #759 E2E-Stabilisierung, #750 Renovate — alle ohne Bezug).
  Kein `project/features/`-Eintrag, kein `project/roadmap.md`-Item.
  Der Defekt ist auf `origin/develop` (93408f76b) reproduzierbar vorhanden.

### Requirements-Gate (Operator-Override)

Es existiert **kein** Requirement-Artefakt unter `project/requirements/` für
dieses Issue, und `requirements-elicit` wurde **nicht** dispatched.

**Expliziter Operator-Override, erteilt am 2026-07-26.** Begründung: Das Issue
ist vom Repository-Owner selbst verfasst und enthält vier bereits testbar
formulierte Akzeptanzkriterien sowie einen konkreten Lösungsvorschlag; der
Verständnisgrad liegt de facto über `τ_high`, ein Elicitation-Interview würde
keine zusätzliche Information erzeugen. Die Dekomposition unten referenziert
die Issue-AK 1:1 (siehe Spalte *Traces to* je Paket).

## Classification

- **Primary class**: `bug`
- **Secondary class(es)**: `refactor` (die DRY-Extraktion, die die Driftursache beseitigt)
- **Rationale**: Ein Parser in produktivem Test-Harness-Code liest Gherkin
  falsch und bricht bei Auslösung die gesamte E2E-Collection ab (exit 2) — ein
  Defekt an bestehendem Verhalten, keine neue Fähigkeit.

### Verifizierter Befund (Code-Grundierung, `origin/develop`)

| Ort | Zustand |
| --- | --- |
| `tests/e2e/conftest.py:176` | `_TAG_LINE = re.compile(r"^\s*@\S+(?:[ \t]+@\S+)*[ \t]*$")` |
| `tests/e2e/conftest.py:190-203` | `_collect_feature_tags` iteriert `splitlines()` **ohne jeden Docstring-State** |
| `tests/e2e/conftest.py:180-187` | `_is_known_tag` akzeptiert nur vier Tag-Formen |
| `tests/e2e/conftest.py:296-300` | unbekanntes Tag → `pytest.UsageError` in `pytest_configure` → Collection-Abbruch |
| `scripts/check_bdd_traceability.py:56` | **identische** `_TAG_LINE`-Regex (Kommentar verweist explizit auf conftest) |
| `scripts/check_bdd_traceability.py:229,250-258` | `docstring_delimiter`-State-Machine für `"""` und ` ``` ` — korrekt |
| `tests/e2e/features/watering_cross_view_consistency.feature` | einzige `.feature`, enthält **keinen** Docstring → heute latent |

Die beiden Parser derselben Syntax sind auseinandergelaufen; die conftest-Hälfte
ist die gefährliche. `check_bdd_traceability.py` importiert bereits heute
`TC_ID_PATTERN` aus dem e2e-Protokoll-Plugin (`_load_tc_pattern`) — es gibt also
**Präzedenz** dafür, dass das Skript Code aus `tests/e2e/` konsumiert. Damit ist
eine SSOT unter `tests/e2e/` der Weg des geringsten Widerstands.

## Scope

- **In scope**
  1. Docstring-State (`"""` und ` ``` `) in der Tag-Erkennung des conftest-Parsers,
     sodass eine Docstring-Zeile aus reinen `@token` kein Marker mehr wird.
  2. Extraktion der geteilten Gherkin-Zeilenklassifikation in **ein** Modul
     (SSOT), das beide Parser konsumieren — beseitigt die Driftursache.
  3. Unit-Test-Abdeckung für die SSOT und den conftest-Collector, `tmp_path`-basiert.
  4. Verhaltensparität des Traceability-Checks (`task` → `scripts/check_bdd_traceability.py`)
     nach der Umverdrahtung.
  5. Erhalt des Typo-Guards: ein unbekanntes Tag **außerhalb** eines Docstrings
     muss weiterhin laut scheitern.

- **Out of scope**
  - Neue `.feature`-Szenarien oder BDD-Ausweitung (das ist Folge-Issue #769).
  - Vollständige Gherkin-Dialektunterstützung über das hinaus, was die beiden
    Parser heute abdecken.
  - Änderungen am E2E-Runtime-Verhalten (Selenium, Profile, Protokoll-Plugin).
  - Ein Fixture-`.feature` im echten `tests/e2e/features/`-Baum — bewusst
    verworfen, weil es sonst den Traceability-Check als „untagged scenario"
    triggern würde (Operator-Entscheidung: `tmp_path`-Unit-Test).

## Route

- **Decision**: `direct`
- **Rationale**: Ein kohärentes Outcome (der Parser liest Gherkin korrekt),
  ein einzelner PR-Strang, kein neues oder retargetiertes Roadmap-Item, keine
  Berührung eines zweiten Goal-Outcomes. Damit *bounded* im Sinne von
  `spec/project/issue-orchestration/` §Routing.
- **Pipeline hand-off**: entfällt.

## Work packages

### P1 — Geteiltes Gherkin-Zeilenklassifikations-Modul (SSOT) + conftest-Fix

- **Problem statement**: `_collect_feature_tags` in `tests/e2e/conftest.py`
  erkennt Tag-Zeilen ohne Docstring-Kontext und registriert dadurch `@token`-
  Zeilen aus einem Gherkin-Docstring als Marker, was über `_is_known_tag` in
  einen `pytest.UsageError` und damit in einen Collection-Abbruch der gesamten
  E2E-Suite läuft. Die Ursache ist strukturell: zwei unabhängige Parser derselben
  Syntax. Ein neues Modul wird zur einzigen Quelle der Zeilenklassifikation
  (Tag-Zeile-Regex + Docstring-Open/Close-State), und der conftest-Collector wird
  darauf umverdrahtet.
- **Acceptance criteria**
  1. Ein neues Modul (Vorschlag: `tests/e2e/_gherkin.py`) exportiert die
     Tag-Zeilen-Regex und eine Zeilen-Iteration bzw. State-Machine, die Zeilen
     innerhalb eines `"""`- oder ` ``` `-Docstrings als Nicht-Tag klassifiziert.
     Das Modul ist ohne Selenium-/E2E-Laufzeitabhängigkeiten importierbar.
  2. `_collect_feature_tags` nutzt ausschließlich dieses Modul; die lokale
     `_TAG_LINE`-Definition in `conftest.py` verschwindet oder wird zum Re-Export.
  3. Eine `.feature` mit einer Docstring-Zeile, die nur `@example` enthält,
     liefert aus `_collect_feature_tags` **keinen** Tag `example` und löst in
     `pytest_configure` **keinen** `UsageError` aus.
  4. Echte Tag-Zeilen (Feature-, Rule-, Scenario- und `Examples:`-Tags) außerhalb
     von Docstrings werden unverändert erkannt; ein unbekanntes Tag außerhalb
     eines Docstrings scheitert weiterhin hart mit `pytest.UsageError`, der den
     Tag-Namen und die Datei nennt.
  5. Beide Docstring-Delimiter (`"""` und ` ``` `) werden behandelt, und ein
     nicht geschlossener Docstring am Dateiende führt nicht zu einer Exception.
- **Traces to**: Issue-AK 1, 3 sowie „Suggested fix" (Faktorisierung).
- **Touched files / artifacts**: `tests/e2e/_gherkin.py` (neu),
  `tests/e2e/conftest.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### P2 — `check_bdd_traceability.py` auf die SSOT umverdrahten

- **Problem statement**: Das Traceability-Skript trägt heute eine eigene Kopie
  der `_TAG_LINE`-Regex und eine eigene Docstring-State-Machine. Solange beide
  Kopien bestehen, kann derselbe Drift erneut entstehen. Das Skript wird auf das
  in P1 geschaffene Modul umgestellt — nach dem bereits etablierten Muster, mit
  dem es `TC_ID_PATTERN` aus dem e2e-Plugin lädt.
- **Acceptance criteria**
  1. `scripts/check_bdd_traceability.py` definiert `_TAG_LINE` und die
     Docstring-Erkennung nicht mehr selbst, sondern konsumiert das Modul aus P1.
  2. `task` -Ziel bzw. `python3 scripts/check_bdd_traceability.py` läuft auf dem
     unveränderten `.feature`-Bestand mit **identischem** Exit-Code und
     identischer Ausgabe wie vor der Änderung (Verhaltensparität, vorher/nachher
     verglichen).
  3. Die Erkennung von Feature-/Rule-/`Examples:`-Tag-Vererbung, orphan tags und
     untagged scenarios bleibt unverändert.
- **Traces to**: Issue „Suggested fix" — „factoring the shared line-classification
  into one place so they cannot drift again".
- **Touched files / artifacts**: `scripts/check_bdd_traceability.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P1

### P3 — Regressions- und Unit-Test-Abdeckung (`tmp_path`)

- **Problem statement**: Für keinen der beiden Parser existiert heute ein
  Unit-Test; der Defekt konnte deshalb unbemerkt einziehen. Es braucht eine
  Abdeckung, die im normalen pytest-Gate läuft (nicht nur im E2E-Profil) und die
  konkrete Regression festnagelt.
- **Acceptance criteria**
  1. Ein Test schreibt eine `.feature` nach `tmp_path`, deren Docstring eine
     Zeile mit ausschließlich `@example` enthält, und assertet, dass
     `_collect_feature_tags` diesen Tag **nicht** meldet.
  2. Ein Test deckt die Gegenrichtung ab: echte Tag-Zeilen (inkl. Mehrfach-Tags
     auf einer Zeile und `Examples:`-Tags) werden weiterhin gemeldet.
  3. Ein Test deckt den Typo-Guard ab: ein unbekanntes Tag außerhalb eines
     Docstrings führt weiterhin zum harten Fehler.
  4. Ein Test deckt beide Delimiter (`"""` und ` ``` `) und den nicht
     geschlossenen Docstring ab.
  5. Die Tests laufen ohne Selenium/Browser und ohne laufendes Backend; sie sind
     Teil des regulären Backend-/Repo-Testlaufs, den `quality-gate` ausführt.
- **Traces to**: Issue-AK 2 („a regression test covers it") und AK 3.
- **Touched files / artifacts**: neue Testdatei (Ablage passend zur
  Repo-Konvention, z. B. `tests/e2e/test_gherkin_line_classification.py` oder
  unter `src/backend/tests/unit/`, je nach dem, welcher Lauf das Modul
  tatsächlich erfasst)
- **Specialist**: `nolte-engineering:unit-test-generator`
- **Depends on**: P1, P2

### P4 — E2E-Suite-Konformitätsreview + Collection-Count-Verifikation

- **Problem statement**: Die Änderung greift in den Collection-Pfad der gesamten
  E2E-Suite ein. Vor dem PR muss belegt sein, dass die Collection unverändert
  zählt und fehlerfrei bleibt, und dass die Änderung den Konventionen von
  `spec/project/e2e-test-automation/` und `spec/project/e2e-test-stability/`
  entspricht.
- **Acceptance criteria**
  1. `pytest --collect-only` aus `tests/e2e/` liefert dieselbe Testanzahl wie vor
     der Änderung, bei **0 errors**. Der Vorher-Wert wird im Dispatch-Log
     festgehalten; ist die lokale Umgebung dafür nicht lauffähig, wird das
     explizit als Limitation vermerkt statt stillschweigend übergangen.
  2. Der Reviewer bestätigt per Checkliste die Konformität der geänderten Dateien
     (keine Skip/xfail-Hygiene-Verletzung, keine neuen Laufzeitabhängigkeiten im
     Collection-Pfad).
  3. Etwaige Befunde werden entweder als minimaler chirurgischer Fix angewandt
     oder im Dispatch-Log als bewusst offen mit Begründung dokumentiert.
- **Traces to**: Issue-AK 4 („`pytest --collect-only` from `tests/e2e/` stays at
  its current count with 0 errors").
- **Touched files / artifacts**: review-only über P1–P3, minimale Fixes erlaubt
- **Specialist**: `nolte-engineering:e2e-test-reviewer`
  (im Issue selbst als Wunschspezialist genannt)
- **Depends on**: P1, P2, P3

## Dependency ordering

```
P1 → P2 → P3 → P4
```

Streng sequenziell: P2 kann erst umverdrahten, wenn die SSOT aus P1 existiert;
P3 testet gegen die finale Modul-API beider Konsumenten; P4 reviewt das
Gesamtergebnis. Alle vier Pakete landen auf **einem** Feature-Branch als **ein**
Pull Request.

## Risks

| Risiko | Mitigation |
| --- | --- |
| Ablageort der SSOT: `scripts/` darf nicht hart von `tests/` abhängen, wenn das Skript standalone in CI läuft | P1 folgt dem bestehenden Muster von `_load_tc_pattern` (Pfad-basiertes Laden aus `tests/e2e/`); P2-AK2 verlangt Verhaltensparität, was einen Import-Bruch sofort sichtbar macht |
| Der `tmp_path`-Unit-Test findet keinen Lauf, der ihn tatsächlich ausführt (Modul liegt unter `tests/e2e/`, das E2E-Profil läuft nicht im Standard-Gate) | P3-AK5 macht die Erfassung durch den regulären Lauf zur expliziten Bedingung; P4 verifiziert zusätzlich die Collection |
| Lokale pytest-Umgebung unvollständig (bekannte Lücke: leeres `.venv`, fehlendes `boto3`) → Collect-Count nicht ermittelbar | P4-AK1 verlangt in diesem Fall eine ausdrückliche Limitation-Notiz statt eines stillen Übergehens; der CI-Lauf am PR ist der Rückfall |
| Verschärfung statt Behebung: eine zu aggressive Docstring-Erkennung könnte echte Tags schlucken | P1-AK4 und P3-AK2/AK3 nageln die Gegenrichtung explizit fest |
| Nicht geschlossener Docstring am Dateiende führt zu Endlos-/Fehlzustand | P1-AK5 und P3-AK4 decken den Fall ab |

**Security**: Keine sicherheitssensitive Pfadberührung — die Änderung betrifft
ausschließlich Test-Harness-Parsing ohne Auth, Netzwerk, Persistenz oder
Nutzerdaten. `code-security-reviewer` und `security-review` sind daher **nicht**
verpflichtend; sollte ein Paket wider Erwarten einen sicherheitsrelevanten Pfad
berühren, wird die Audit→Fix→Verify-Kette nachgezogen.

## Open questions

Keine. Die drei offenen Entscheidungen wurden vor der Dekomposition vom Operator
beantwortet (2026-07-26):

1. Requirements-Gate → expliziter Override statt `requirements-elicit`.
2. Scope → Fix **plus** DRY-Extraktion der geteilten Zeilenklassifikation.
3. Testform → `tmp_path`-basierter Unit-Test statt Fixture-`.feature` im
   echten `features/`-Baum.

## Dispatch log

<!-- <YYYY-MM-DD> P<k> dispatched to <subagent_type> — <result one-liner> -->
