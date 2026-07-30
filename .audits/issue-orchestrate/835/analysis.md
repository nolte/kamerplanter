---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "835"
classification: "refactor"
secondary-classes: ["infra"]
route: "direct"
status: approved
created: "2026-07-30"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #835 — Remove implicitly_wait(3) from the E2E driver — needs its own verification round
- **URL**: https://github.com/nolte/kamerplanter/issues/835
- **Labels**: chore, test
- **Linked items**: abgespalten aus #778 (C6); Vorarbeit gelandet in #871, #874, #875. Kein
  schließender PR — `closedByPullRequestsReferences` ist leer.
- **Prior art checked**: `project/requirements/e2e-full-run-stabilization.md`,
  `e2e-selenium-executability.md`, `e2e-ci-selenium.md`, `e2e-smoke-merge-gate.md` — keines
  deckt #835 ab. Kein offener PR adressiert die Entfernung. **Nicht self-resolved:** die Zeile
  steht unverändert auf `develop` (`tests/e2e/conftest.py:1084`).
- **Base commit**: `1d98bf3ca`; Arbeitszweig `chore/e2e-element-proxy`
- **Trust boundary**: Der re-scoping-Kommentar stammt von `nolte` (`association: owner`) →
  vertrauenswürdiger Autor, sein Inhalt darf die Zerlegung steuern.

## Classification

- **Primary class**: refactor
- **Secondary class(es)**: infra
- **Rationale**: Umstellung des Interaktionsmodells der E2E-Suite (capture-then-use →
  selbst-auflösende Referenzen) ohne Änderung am Produktverhalten; betrifft ausschließlich
  Testinfrastruktur.

## Requirements-Gate

Kein Artefakt unter `project/requirements/` für #835. **Expliziter Operator-Override**
(2026-07-30): der Owner-Kommentar am Issue liefert Problemanalyse, Fünf-Lauf-Messung, zwei
begründete Lösungswege und das Abnahmekriterium (Sieben-Profil-Grün) — inhaltlich das, was
`requirements-elicit` erheben würde. `requirements-elicit` wurde daher nicht vorgeschaltet.

## Scope

- **In scope**: der `WebElement`-Subklassen-Proxy; Verdrahtung der drei elementliefernden
  wait-Helper; Lückenschluss auf dem `find_elements`-Pfad; Entfernung von
  `implicitly_wait(3)` samt Neufassung des Kommentarblocks und der veralteten Docstrings;
  lokale Messschleife; Suite-Review und Python-Review; Sieben-Profil-Nachlauf gegen Baseline.
- **Out of scope**: Pfad B (231 Call-Site-Konvertierungen) — vom Operator verworfen, bleibt
  nur als Rückfalloption im Risikoabschnitt. Backend-/Frontend-Produktcode. Neue E2E-Fälle.
  Änderungen an der `e2e-nightly.yml`-Matrix. Die 31 singulären `find_element(`-Stellen
  (als Restrisiko benannt, nicht behoben).

## Route

- **Decision**: direct
- **Rationale**: ein kohärentes Ergebnis (die Zeile fällt, die Suite bleibt grün), ein
  PR-Strang, kein neues oder umgehängtes Roadmap-Item.

## Widerlegung der Ausgangsannahme (verifiziert)

Die Routenbeschreibung des Issues — „ein dünner Proxy, der `(locator, condition)` hält" mit
`__getattr__`-Weiterleitung — **ist so nicht implementierbar**. Nachgeprüft gegen die lokal
installierte Selenium-Version 4.46.0 (Repo pinnt `>=4.25.0`):

| # | Befund | Beleg | Status |
|---|---|---|---|
| R2a | `_wrap_value` erkennt Elemente über `isinstance(value, _web_element_cls)` und serialisiert dann `value.id`; alles andere fällt in die JSON-Serialisierung durch | `selenium/webdriver/remote/webdriver.py:410-411`, Durchfall `:416` | bestätigt |
| R2b | `EC.element_to_be_clickable` und `EC.visibility_of_element_located` packen ein Nicht-`WebElement` **als Locator-Tupel aus** | `expected_conditions.py:459`, `:517` | bestätigt |
| R3 | Alle Element-Kommandos laufen über `WebElement._execute`, das `self._id` **direkt** liest — nicht die öffentliche `id`-Property. Ebenso `__eq__` (`:489`) und `__hash__` (`:559`). `__init__` weist `self._id` zu (`:73`), `_id` kann also nicht ohne Weiteres Property werden | `webelement.py:507`, `:489`, `:559`, `:73` | bestätigt |
| R5 | Der Proxy ist im required-Gate nicht unit-testbar: `Static CI Tests` fährt `pytest tests/unit/` unter `src/backend`, und dieser Tier hat eine **erzwungene** Selenium-Sperre | `src/backend/tests/unit/test_gherkin_line_classification.py` — `assert selenium_modules == []` | bestätigt |

⇒ **Der Proxy MUSS von `WebElement` erben**, und die Re-Auflösung muss an `_execute` bzw. an
der Frischhaltung von `_id` hängen, nicht an der `id`-Property allein.

**Korrekturen an den Messwerten** (selbst nachgemessen auf `1d98bf3ca`):

| Signal | Issue-Kommentar | Messung `1d98bf3ca` | Anmerkung |
|---|---:|---:|---|
| Capture-Sites | 437 | **459** | 437 ist die Zahl im `conftest.py`-Kommentar, erhoben *vor* #874/#875 |
| `find_present`-Aufrufe | — | **49** | ohne die `def`-Zeile |
| `retry_on_stale`-Aufrufe | — | **3** | **alle drei innerhalb `base_page.py`** (`:1641`, `:1666`, `:1859`) — null Adoption in Page-Objects |
| `isinstance(…, WebElement)` in der Suite | — | **0** | das genannte Risiko existiert in der Suite nicht; es existiert *in Selenium* und kehrt sich dadurch um (R2) |
| Interaktionen / `find_elements` / `find_element(` / Page-Objects | 231 / 789 / 75 / — | 389 / 801 / 31 / 62 | |

**R4 — Einschränkung gegenüber dem Erstbefund:** die drei zeilenbasierten Helper
(`get_column_texts` `:1641`, `find_row_by_text` `:1666`, `click_row/_click` `:1859`) lösen ihre
Zeilen über `self.driver.find_elements(...)` auf, gehen also am Proxy vorbei — **sind aber
bereits in `retry_on_stale` gekapselt**. Sie sind nicht ungeschützt, sondern über einen
anderen Mechanismus geschützt. P4 bleibt berechtigt als Lückenschluss für die
`find_elements`-Stellen *außerhalb* dieser drei, nicht als Rettung eines offenen Lochs.

**Nebenbefund — Defekt bereits auf `develop`:** die Docstrings von
`IMPLICIT_WAIT_EQUIVALENT` (`base_page.py:27-50`) und `find_present` (`:550-553`) beschreiben
die Entfernung im Perfekt („the explicit counterpart to the driver-level implicit wait #835
removed"), während die Zeile steht. Wird in P6 mitgezogen.

## Work packages

### P1 — Re-auflösender Element-Proxy

- **Problem statement**: Es gibt keinen Elementtyp, der seine verlorene Referenz selbst neu
  beschafft. Jede der 459 Capture-Sites kann ihr Element zwischen Auflösung und Benutzung
  verlieren, sobald der implizite Wait die React-Tabelle nicht mehr hat aussitzen lassen.
- **Acceptance criteria**: Neues Modul; der Proxy **erbt von `WebElement`**; die
  Re-Auflösung hängt an `_execute` bzw. an der Frischhaltung von `_id` (R3), nicht allein an
  der `id`-Property; `isinstance(proxy, WebElement)` ist `True`; `_wrap_value` serialisiert
  die **nach** der Re-Auflösung gültige id; `__eq__`/`__hash__` bleiben konsistent; das
  Zeitbudget ist auf **jedem** Pfad nachweislich begrenzt (kein unbegrenztes Retry);
  ruff und mypy grün. **Zusätzlich (Q3):** `tests/e2e/requirements.txt` pinnt Selenium auf
  `>=4.25.0,<5`, mit einer Begründung am Pin, warum die Obergrenze an dieses Modul gebunden ist.
- **Touched files / artifacts**: `tests/e2e/pages/_element_proxy.py` (neu),
  `tests/e2e/requirements.txt`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: none

### P2 — Verifikation des Proxy-Verhaltens

- **Problem statement**: Ein falscher Proxy ändert das Verhalten überall **still**. Der
  required-Gate-Unit-Tier kann ihn nicht abdecken (R5).
- **Acceptance criteria**: Testmodul unter `tests/e2e/`, das abdeckt: echte Stale-Referenz →
  Re-Auflösung; `isinstance`-Kompatibilität; Marshalling über
  `execute_script("arguments[0]…", proxy)` (die Stellen `base_page.py:925`, `:1259`,
  `sensor_create_dialog_page.py:110`); ein in `EC.*` hineingereichter Proxy wird **nicht** als
  Locator ausgepackt; erschöpftes Budget propagiert als Fehler statt still zu schlucken.
  Grün unter `--profile light`. Ein Docstring begründet, warum das Modul nicht unter
  `src/backend/tests/unit/` liegt.
- **Touched files / artifacts**: `tests/e2e/test_element_proxy.py` (neu)
- **Specialist**: `nolte-engineering:fullstack-developer` *(siehe Q4 — Zusammenlegung mit P1
  zur Entscheidung gestellt)*
- **Depends on**: P1

### P3 — Die drei wait-Helper liefern den Proxy

- **Problem statement**: `wait_for_element`, `wait_for_element_visible` und
  `wait_for_element_clickable` liefern rohe Elemente, die 459 Capture-Sites über einen
  Re-Render hinweg halten.
- **Acceptance criteria**: Die drei liefern den Proxy, jeder mit **seiner eigenen** Condition;
  `wait_for_element_hidden` bleibt **unverändert** (liefert `None`); `find_present` (49
  Stellen) und `find_by_testid` erben das Verhalten nachweislich über die Aufrufkette;
  `--profile light` grün **bei noch gesetztem `implicitly_wait(3)`** — die Isolation, die die
  Wirkung des Proxys von der Wirkung der Entfernung trennt.
- **Touched files / artifacts**: `tests/e2e/pages/base_page.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P1

### P4 — Lückenschluss auf dem `find_elements`-Pfad

- **Problem statement**: Der Proxy umfasst nur die drei singulären Rückgaben. Die
  `find_elements`-Aufrufe außerhalb der drei bereits `retry_on_stale`-gekapselten Helper
  bleiben roh.
- **Acceptance criteria**: `get_column_texts`, `find_row_by_text` und `click_row` überstehen
  einen Re-Render mitten in der Benutzung, ohne `StaleElementReferenceException` nach außen zu
  lassen — belegt durch einen gezielten Test; der gewählte Hebel ist im Code begründet; die
  identitätsbasierte Zeilen-Wiederfindung (`:1845-1857`) bleibt **erhalten**, kein Rückfall auf
  den Index; `--profile light` grün.
- **Touched files / artifacts**: `tests/e2e/pages/base_page.py`, ggf. `_element_proxy.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P1

### P5 — `implicitly_wait(3)` entfernen

- **Problem statement**: Der eigentliche Auftrag des Issues — erst nach P3 und P4 gefahrlos.
- **Acceptance criteria**: `grep -rn "implicitly_wait" tests/` liefert **nichts**; der
  Kommentarblock `conftest.py:1057-1083` ist neu gefasst und beschreibt, was an die Stelle
  getreten ist (er beschreibt sonst eine Zeile, die es nicht mehr gibt); `--profile light`
  und `--profile smoke` grün.
- **Touched files / artifacts**: `tests/e2e/conftest.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P3, P4

### P6 — Docstrings auf den tatsächlichen Zustand bringen

- **Problem statement**: Zwei Docstrings beschreiben die Entfernung im Perfekt, obwohl sie
  noch nicht stattgefunden hat (Nebenbefund, bereits auf `develop`).
- **Acceptance criteria**: Beide Docstrings beschreiben den Zustand nach diesem PR mit den
  korrigierten Zahlen aus diesem Artefakt; kein Docstring unter `tests/e2e/` behauptet einen
  Zustand, den ein `grep` widerlegt (geprüft auf `implicit wait`, `implicitly_wait`, `#835`).
- **Touched files / artifacts**: `tests/e2e/pages/base_page.py`
- **Specialist**: `nolte-engineering:fullstack-developer`
- **Depends on**: P5

### P7 — Lokale Messschleife: schrumpft die Fehlermenge oder wandert sie?

- **Problem statement**: Das Abbruchkriterium der fünf Vorläufe war, dass die Fehlermenge
  *wanderte* statt zu schrumpfen. Ohne diese Unterscheidung ist ein Nachlauf nicht deutbar.
- **Acceptance criteria**: `--profile light`, `--profile smoke` und `--profile mobile` (Q1)
  je **zweimal** gefahren
  (Image-Neubau eingerechnet, `scripts/run-e2e.sh:195`); jeder Nicht-Pass klassifiziert
  (echter Defekt / Flake / Testfehler) mit `file:line`; **explizites Verdikt: schrumpft oder
  wandert?** Wandert sie, blockiert das P10 und fällt auf P4 zurück.
- **Touched files / artifacts**: keine (Messung)
- **Specialist**: `nolte-engineering:test-result-analyzer`
- **Depends on**: P5, P6

### P8 — Suite-Review gegen die Stabilitäts-Spec

- **Problem statement**: Grün ist nicht dasselbe wie „prüft noch". Ein Proxy, der eine echte
  Zusicherung maskiert, macht die Suite grün und wertlos.
- **Acceptance criteria**: Verdikt je Checklistenpunkt gegen `e2e-test-automation` und
  `e2e-test-stability`; **ausdrücklich**: maskiert der Proxy irgendeine echte Zusicherung —
  kann ein Test noch dort fehlschlagen, wo er vorher fehlschlug? Jede Stelle, an der die
  Re-Auflösung ein legitimes „das Element ist weg" in ein Warten verwandeln könnte, ist
  benannt; blockierende Befunde behoben. Die 31 singulären `find_element(`-Stellen sind als
  Restrisiko dokumentiert.
- **Touched files / artifacts**: `tests/e2e/` (minimal-chirurgisch)
- **Specialist**: `nolte-engineering:e2e-test-reviewer`
- **Depends on**: P5, P6

### P9 — Python-Review des Proxys

- **Problem statement**: Der Proxy fasst Selenium-Interna an (`_execute`, `_id`); die brechen
  bei einem Upgrade still.
- **Acceptance criteria**: Review gegen `source-code-review` (Kern + Python-Profil); geht
  ausdrücklich auf das Verhalten bei Selenium-Minor-Upgrades ein (nur `>=4.25.0` gepinnt) —
  welche Interna, wie laut scheitert es; Criticals behoben.
- **Touched files / artifacts**: `tests/e2e/pages/_element_proxy.py`
- **Specialist**: `nolte-engineering:python-code-reviewer`
- **Depends on**: P1

### P10 — Sieben-Profil-Nachlauf gegen Baseline

- **Problem statement**: Der operator-bestätigte Abnahmevertrag.
- **Acceptance criteria**: `gh workflow run e2e-nightly.yml --ref chore/e2e-element-proxy -f
  profile=all` gefahren, alle sieben Profile haben ein Ergebnis; Tabelle je Profil gegen
  Baseline-Lauf `30563107760` (`1d98bf3ca`); **Abnahmeregel: kein in der Baseline grüner Test
  ist auf dem Branch rot** — ein Netto-Gewinn mit einem neuen Fehler besteht **nicht**; der
  Commit des Laufs ist festgehalten, und **ein Rebase macht das Grünfenster ungültig**.
- **Touched files / artifacts**: keine (Verifikation)
- **Specialist**: `nolte-engineering:test-result-analyzer`
- **Depends on**: P7, P8, P9

## Dependency ordering

```
P1 ─┬─> P2
    ├─> P3 ─┐
    ├─> P4 ─┼─> P5 ──> P6 ─┬─> P7 ─┐
    └─> P9 ─┘              ├─> P8 ─┼─> P10
                           └───────┘
```

Serialisiert: **P1 → P2 → P3 → P4 → P5 → P6 → (P7, P8, P9) → P10**.

P2, P3 und P4 fassen `base_page.py` bzw. denselben Baum an und werden **sequenziell**
disponiert, nicht parallel (Projektregel: schreibende Agenten auf geteiltem Tree
serialisieren, sonst git-stash-Konflikt).

## Risks

- **Der Proxy maskiert echte Fehlschläge** — die teuerste Ausprägung des projektbekannten
  Musters „die Prüfung leistet weniger, als sie behauptet". → P8 prüft es als benannten Punkt;
  P10 verlangt, dass kein zuvor grüner Test rot wird.
- **Selenium-Interna sind nicht öffentlich** (`_execute`, `_id`); nur `>=4.25.0` gepinnt. →
  P9 adressiert es, P2 scheitert beim nächsten Image-Neubau laut. Siehe Q3.
- **P4 unterschätzt** → bleibt der Plural-Pfad ungedeckt, reproduzieren P7/P10 die Läufe 1 und
  5, und die Ursache wird dem Proxy zugeschrieben. Gemildert dadurch, dass P4 ein eigenes
  Paket *vor* P5 ist und P7 das Schrumpft-oder-wandert-Verdikt erzwingt.
- **Ein Rebase macht das Grünfenster ungültig** → P10 muss nach jedem Rebase oder
  `develop`-Merge vor dem Merge wiederholt werden.
- **Restfläche**: 31 singuläre `find_element(`-Stellen (teils verschachtelt
  `element.find_element(...)`) liefern weiter rohe Elemente. Bewusst außerhalb des Scopes,
  in P8 als Restrisiko zu benennen.
- **Pfad B als Rückfall**: nicht geplant. Auslöser für eine Re-Eskalation wäre ein Nachweis in
  P1/P2, dass die `WebElement`-Subklasse nicht transparent zu bekommen ist.
- **Keine Sicherheitsrelevanz** — reine Testinfrastruktur. `code-security-reviewer` und die
  `security-review`-Skill sind für diesen Lauf **nicht** erforderlich.

## Open questions — vom Operator entschieden (2026-07-30)

1. **Q1 — entschieden: `mobile` ergänzen.** Das lokale Vor-Gate in P7 fährt `light`, `smoke`
   **und `mobile`**. Begründung: `find_row_by_text` ist ausdrücklich layout-tolerant
   (Desktop-Tabelle vs. mobile Card-Liste), die Fehlerklasse „falsche Pflanze geöffnet" aus
   den Läufen 2 und 5 ist damit plausibel viewport-abhängig und würde von `light` + `smoke`
   allein nicht gefangen.
2. **Q2 — entschieden: blockieren.** Kein in der Baseline grüner Test darf auf dem Branch rot
   sein, auch nicht bei Netto-Gewinn. Ein neuer Fehlschlag blockiert P10 und damit den PR.
3. **Q3 — entschieden: ja, `<5` pinnen.** `tests/e2e/requirements.txt` auf `>=4.25.0,<5`.
   Wird als Akzeptanzkriterium in **P1** mitgeführt (der Pin gehört zum Modul, das die Interna
   anfasst).
4. **Q4 — entschieden: P2 bleibt eigenständig**, Spezialist `nolte-engineering:fullstack-developer`.
   Die Verifikation des Proxys ist die reviewbare Einheit, an der ein stiller Verhaltensfehler
   auffällt; in P1 aufgelöst würde sie mit dem Entwurf verschmelzen, den sie prüfen soll.

## Approval

- **Operator-Freigabe**: 2026-07-30, Route A bestätigt, Artefakt zur Disposition freigegeben.
- **Requirements-Override**: bestätigt (siehe §Requirements-Gate).
- **Verifikationstiefe**: Baseline + Nachlauf, beide Sieben-Profil (`profile=all`).
- **Baseline-Lauf**: [30563107760](https://github.com/nolte/kamerplanter/actions/runs/30563107760) auf `1d98bf3ca`.

## Dispatch log

### P1 — `nolte-engineering:fullstack-developer` — **erledigt** (`771cfab42`)

Geliefert: `tests/e2e/pages/_element_proxy.py` (455 Zeilen, `ReResolvingElement`,
`ElementReResolutionError`, `resolve_element()`), Selenium-Pin `>=4.25.0,<5`.
`ruff check` und `ruff format --check` vom Orchestrator nachgefahren: grün.

**Korrektur am Plan (angenommen):** Das Akzeptanzkriterium sagte „`_execute` **oder**
Frischhaltung von `_id`". Beides allein genügt nicht — es sind **drei** Hooks nötig:
`_id` bleibt gewöhnliches Attribut und wird bei Heilung in place überschrieben (einzige
Wahrheitsquelle für `_execute`/`id`/`__eq__`/`__hash__`/`__repr__`); `_execute` fängt den
Stale und wiederholt; **und** die öffentliche `id`-Property prüft vor der Antwort auf
Lebendigkeit, weil `_wrap_value` (`webdriver.py:411`) genau sie liest und dabei nie
`_execute` aufruft. Ohne den dritten Hook würde `execute_script("arguments[0]…", element)`
eine tote ID an den Treiber marshallen, wo kein Proxy mehr heilen kann.

**Korrektur an der Mengenangabe:** Der Auftrag nannte 3 `execute_script`-Stellen mit
gefangenem Element; es sind ~20 `execute_script`-Aufrufe in den Page-Objects, die meisten
mit Element. Der Marshalling-Pfad ist breiter als angenommen — das rechtfertigt den
Liveness-Probe-Hook, kostet aber **einen Roundtrip je marshalliertem Element**.

**Vom Orchestrator gefundene Konsequenz — an P8 und P9 weiterzureichen:**
`ElementReResolutionError` erbt bewusst von `StaleElementReferenceException`, damit
`retry_on_stale` und `POLL_TRANSIENTS` weiter greifen. `POLL_TRANSIENTS`
(`base_page.py:50`) enthält aber genau `StaleElementReferenceException` — **erschöpft der
Proxy sein Budget innerhalb eines `poll()`, schluckt der äußere Poll die Diagnose und
ersetzt sie nach `DEFAULT_TIMEOUT` (15 s) durch einen generischen `TimeoutException`.**
Das Kriterium „scheitert laut" gilt damit am Modulrand, nicht im Einsatz. Verteidigbar
(der äußere Poll löst ohnehin über den Locator neu auf), aber eine bewusste Entscheidung:
P9 bewertet sie, P8 prüft, ob dadurch eine echte Zusicherung maskiert wird.

**Vom Agenten benanntes Restrisiko für P3/P8:**
`BasePage.is_displayed_in_scroll_container` (`base_page.py:881-887`) behandelt Staleness
ausdrücklich als *Verdikt* („a stale element is genuinely gone, hence `False`"); bekommt
es einen Proxy, antwortet der geheilte Ersatz statt `False`. Dasselbe gilt für
`_read_select_value`. Das ist die konkreteste Stelle, an der die Re-Auflösung eine echte
Zusicherung verschieben könnte.

**Nicht widerlegt:** die naive `__getattr__`-Route bleibt nachweislich unbaubar; kein
Rückfall auf Pfad B nötig. `staleness_of` kommt in der Suite **nicht** vor (0 Treffer) —
die naheliegendste Maskierungsgefahr existiert hier also nicht.
