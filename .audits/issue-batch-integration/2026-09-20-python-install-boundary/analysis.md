# Gruppe 2026-09-20-python-install-boundary

**Transientes Artefakt.** Vor dem Bündel-PR mit `git rm -r` entfernen.

## Frage dieser Research-Phase
Welcher Python-Install muss Hashes tragen, welcher nur einen Pin — und welche dieser Installationen wird vor dem Merge überhaupt geprüft?

## Die eine logische Änderung
Die Grenze „welcher Python-Install muss Hashes tragen" wird einmal festgeschrieben und bekommt die zwei Prüfungen, die ihr fehlen: einen Pre-Merge-Konsumenten samt Klammer zwischen Quelle und kompilierter Liste für die Dokumentation, und einen Wächter über die Hook-Abhängigkeiten.

## Aufnahmeprädikat
| Issue | Prädikat | Beleg (gemessen) |
|---|---|---|
| #1572 | thematische Kopplung + Abhängigkeitskette | entstand im Review von PR #1567; `.pre-commit-config.yaml:129` installiert `selenium>=4.25.0,<5` und `pytest>=8.3.0` in einem **Pflicht**-Check |
| #1571 | dieselbe, plus geteilte Entscheidungsfläche | `git grep -n "docs/requirements" -- .github/` liefert genau einen Konsumenten: `release-cd-deliver-docs.yml:14`, Trigger `release: published` |

## Clusterart
**Klassen-Cluster**: „ein Install ist gepinnt oder gehasht, aber nichts prüft das vor dem Merge". Sweep-Prädikat: jede Stelle, die Python-Pakete installiert und weder durch einen Lock-Wächter noch durch eine Pre-Merge-Lane fällt.

## Modus und Reihenfolge
**Modus A**. Kein Mitglied herauslösbar; beide sind additive Prüfungen ohne ausstehendes Fremdreview.
Reihenfolge: **Grenzentscheidung zuerst** (gehört zu #1572) → **#1571** (eng, billig, klar falsifizierbar) → **#1572s Wächter** (teuer wegen der Fundstellenzahl).
**Stufe 2**.

## Vollständigkeitsmatrix
| Posten | Änderung | Gegenprobe | Guard | Doku |
|---|---|---|---|---|
| Grenze | normativ festhalten, welcher Install Hashes braucht und welcher einen Pin | — | — | am Ort des Sweeps, nicht nur im PR |
| #1571 Pre-Merge-Konsument | pfadgefilterter, **beratender** Job auf `docs/requirements.*` | kaputte Hash-Zeile MUSS die neue Lane rot machen | Drift-Check zwischen Quelle und kompilierter Liste (neu kompilieren und vergleichen) | Verweis auf die Hash-Strenge in `.taskfiles/docs.yaml:21-36` |
| #1572 Wächter | Wächter über **alle** `additional_dependencies`-Einträge | einen Eintrag lockern MUSS rot werden | der Wächter MUSS alle Einträge sehen, nicht nur den einen Hook | die drei Schreibweisen, die er nicht trifft, stehen am Guard |
| Klassen-Sweep | — | — | Prädikat im Docstring | — |

## Risiken, alle drei load-bearing
1. **Die Diagnose von #1572 ist an einem Punkt falsch.** Die behauptete Formulierung „every Python install" existiert an HEAD nicht mehr (`git grep -rn "every Python install" -- src scripts .taskfiles` ist leer); der reale Wächter beschreibt seinen Umfang korrekt. Die Arbeit ist, die Grenze **normativ zu setzen**, nicht eine Übertreibung zu korrigieren.
2. **Der Umfang von #1572 ist größer als das Issue sagt.** `.pre-commit-config.yaml` trägt **17** `additional_dependencies`-Einträge mit offenen Ranges (ruff 4×, PyYAML 9×, mypy 4×, jsonschema, referencing), nicht einen. Ein Wächter, der nur den E2E-Hook bindet, ist die Opt-in-Liste, die G6 verbietet.
3. **Der neue Docs-Job ist beratend und pfadgefiltert** und darf kein Pflicht-Kontext werden — ein pfadgefilterter Pflicht-Check meldet nie und gilt damit als erfüllt (`backend-guards.yml:55-58`).

## Außerhalb des Scopes
Die Runner-Werkzeug-Installationen in Workflow-`run:`-Blöcken (gepinnt, erreichen kein ausgeliefertes Artefakt) — benannt, nicht repariert. Das Notebook.

## Offene Fragen
Keine; die Grenzentscheidung trifft der Strang und protokolliert sie.
