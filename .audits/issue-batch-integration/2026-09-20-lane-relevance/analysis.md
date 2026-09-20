# Gruppe 2026-09-20-lane-relevance

**Transientes Artefakt.** Vor dem Bündel-PR mit `git rm -r` entfernen; der dauerhafte Nachweis ist der PR-Body.

## Frage dieser Research-Phase
Wo darf eine Lane ausdrücken, dass eine Änderung sie nicht betrifft — und wie, ohne dass ein Pflicht-Kontext hinter einen Pfadfilter gerät und damit als erfüllt gilt, ohne je zu melden?

## Die eine logische Änderung
Relevanz wird dort ausgedrückt, wo die Lane sie kennt — im Filter der beratenden Lane und im Job der Pflicht-Lane — ohne dass je ein Pflicht-Kontext hinter einen `on:`-Pfadfilter gerät.

## Aufnahmeprädikat
| Issue | Prädikat | Beleg (gemessen gegen `origin/develop`) |
|---|---|---|
| #1577 | geteilte Fläche + Abhängigkeitskette | `.github/workflows/e2e-smoke.yml:84-104` ist die Vorlage, die #1578 auf zwei weitere Lanes überträgt; `git grep -n "helm\|skaffold" -- docker-compose.e2e*.yml scripts/run-e2e.sh` ist **leer**, der Compose-Stack liest also weder Helm noch Skaffold |
| #1578 | thematische Kopplung + geteilte Fläche | beide ändern ausschließlich `dorny/paths-filter`-Relevanzlogik in `.github/workflows/`, beide hängen an `test_required_contexts_are_unfiltered.py:106` und an derselben `needs.<job>.result`-Falle |

## Clusterart
**Klassen-Cluster**: „eine Lane misst etwas, das der Diff nicht ändern kann". Ein `## Class sweep` auf Gruppenebene. Prädikat-Kandidat: jede Lane mit Pfad- oder Relevanzfilter, deren Ausschlussliste nicht gegen das gemessene Eingabeset des Jobs gehalten ist.

## Modus und Reihenfolge
**Modus B** (Sub-Branch je Mitglied). #1578 muss herauslösbar bleiben: es fasst zwei **Pflicht-Kontexte** an, ein Fehler schaltet ein Gate still ab, und die Fork-Einschränkung ist ein offener Punkt. #1577 muss ohne #1578 mergen können.
Reihenfolge: **#1577** (billig, in beide Richtungen falsifizierbar, liefert das Muster) → **#1578**.
**Stufe 3**: die Änderung berührt Pflicht-Kontexte, also einen veröffentlichten Vertrag (Branch-Protection). Designfrage VOR dem Wie: bekommt `Write-route and tree guards` überhaupt ein Erkennungs-Gate? Sein Eingabeset ist breiter, als es aussieht — es liest Workflow-Dateien, `renovate.json5`, `.github/settings.yml` und den Migrationsbaum.

## Vollständigkeitsmatrix
| Posten | Workflow | Gegenprobe rot | Gegenprobe grün | Guard | Doku |
|---|---|---|---|---|---|
| #1577 Helm im Rauchtest | `e2e-smoke.yml` `runtime`-Ausschluss um `helm/**` erweitert, mit Begründung | Scratch-Branch, der nur `src/backend/` ändert, MUSS die Suite laufen lassen | Scratch-Branch, der nur `helm/` ändert, MUSS sie überspringen | `predicate-quantifier: 'every'` bleibt unangetastet und wird im PR benannt | Kommentar nennt den Grund (Compose statt Helm), nicht nur die Regel |
| #1578 Pflicht-Lane | Erkennungs-Job in `backend-guards.yml`, Pflicht-Job gated auf `needs.<job>.result` | Diff, der die Lane betrifft, MUSS sie laufen lassen | Diff, der sie nicht betrifft, MUSS sie überspringen und den Kontext trotzdem melden | `test_required_contexts_are_unfiltered.py` bleibt grün (prüft nur `on:`-Ebene, gemessen: `:106`) | die Fork-Einschränkung (`push` feuert nicht für Fork-Branches) wird im PR benannt |
| Klassen-Sweep | — | — | — | ein Sweep über alle Lanes mit Relevanzfilter | Prädikat im Guard-Docstring |

## Risiken
- **Ein übersprungener Job meldet seinen Pflicht-Kontext als erfolgreich.** Die `needs.<job>.result`-Klausel ist deshalb load-bearing; ein fehlgeschlagener Erkennungsschritt MUSS den teuren Job laufen lassen. Vorbild mit ausgeschriebener Begründung: `e2e-smoke.yml:105-121`.
- Der `runtime`-Filter ist ausdrücklich fail-open dokumentiert: ein zu breiter Ausschluss deaktiviert das Gate still.
- Beide Lanes triggern auf `push`, was für Fork-Branches nie feuert. Vorbestehend, gehört benannt, nicht hier repariert.

## Außerhalb des Scopes
Die Merge-Queue-Frage und das Fallenlassen von `strict` (#1584, zurückgewiesen als unbeschränkt). Das Vorziehen von Regeln nach `spec/project/quality-gate/`.

## Offene Fragen
Die Stufe-3-Designfrage oben wird vom Strang per Messung beantwortet und im PR protokolliert.
