# Gruppe 2026-09-21-spec-claims-vs-repository

- **group-id:** `2026-09-21-spec-claims-vs-repository`
- **tier:** 2 (mehrere Issues, mehrere Dateien, keine Repository-Grenze, kein veröffentlichter Vertrag)
- **mode:** A — ein Strang, kein Sub-Branch
- **members:** #1566, #1581
- **admitting predicate (beide):** thematic coupling

## Die Frage, auf die diese Research-Phase zugeschnitten war

Behaupten NFR-009 §3.2 und NFR-018 einen Repository-Zustand, den es nicht gibt — und
wenn ja, ist das zweimal derselbe Defekt oder zweimal ein anderer?

## Die eine logische Änderung

Die beiden abgedrifteten Spec-Dokumente wieder mit dem Repository in Deckung bringen,
das sie beschreiben.

## Mitglieder

| # | Behauptung des Issues | nachgemessen (2026-09-21, Worktree `spec-claims`) | Ergebnis |
|---|---|---|---|
| #1566 | NFR-009 §3.2 beschreibt eine `renovate.json5`, die es nicht gibt; sechs Top-Level-Keys mit je 0 Vorkommen | `grep -c` je Key gegen `renovate.json5`: `branchPrefix` 0, `schedule` 0, `commitMessagePrefix` 0, `dependencyDashboardTitle` 0, `lockFileMaintenance` 0, `prHourlyLimit` 0 | **bestätigt** |
| #1581 | „NFR-018 seit 2026-08-08 nicht fortgeschrieben" | `git log --since=2026-08-09 -- spec/nfr/NFR-018_*.md` → **genau ein Commit**: `d1f2226d3` (#1642, heute, §2.3) | **Schlagzeile überholt, Substanz offen** |

### Zu #1581, ausgeschrieben

Die Datumsbehauptung stimmt nicht mehr: das Dokument wurde heute angefasst. Die fünf
namentlich benannten Lücken sind davon **nicht** berührt — §2.3 trägt die Klasse aus
#1456 („ein Gate darf nicht über Code entscheiden, indem es rohen Quelltext matcht"),
und keine der fünf. Offen bleiben:

1. Ein Pflicht-Check in einem pfadgefilterten Workflow blockiert dauerhaft; ein Check,
   der nie meldet, gilt als erfüllt.
2. Ein übersprungener Job meldet seinen Pflicht-Kontext als erfolgreich.
3. Skips sind der Messwert, nicht Grün.
4. Ein roter advisory Check wurde gemergt, und der Default-Branch trug den Schaden
   unbemerkt.
5. Ein Ausnahmeregister altert per Default in eine dauerhafte Befreiung.

Der Korpus dafür ist seit dem Schreiben des Issues **gewachsen**, nicht geschrumpft:
Punkt 4 ist genau der Vorfall, der den Merge-Zug dieses Sweeps zweimal korrigiert hat
(#1547 mit rotem `Skaffold Verify`, dann #1617, wo ein Re-Run den HOLD aufhob), und
Punkt 5 hat mit dem `# prose-permeable:`-Marker aus #1642 erstmals eine gebaute Form
(„eine Ausnahme, die nichts entschuldigt, ist rot") — normativ ist sie nirgends.

## Strukturelle Analyse

**Class cluster**, nicht symptom cluster. Beide Mitglieder sind dieselbe Defektklasse,
die NFR-018 §1 selbst katalogisiert: *Prosa beschreibt einen Zielzustand in der
Gegenwartsform*. Sie unterscheiden sich nur in der Richtung des Auseinanderlaufens —
#1566 ist Text, der einmal geschrieben und nie nachgemessen wurde; #1581 ist Text, der
stehen blieb, während die Befunde weiterkamen.

**Prozessbefund (eigener Posten, nicht durch diese Reparatur erledigt):** Für Code über
Code hat dieses Repository inzwischen eine durchgesetzte Antwort — `check_gate_text_assertions.py`
aus #1642 macht eine Gate-Aussage falsifizierbar. Für **Spec über Repository** gibt es
nichts Vergleichbares: ein Spec-Absatz, der einen Konfigurationsschlüssel nennt, hat
keinen Mechanismus, der prüft, ob es den Schlüssel gibt. #1566 ist der Beleg, dass das
220 Zeilen lang unbemerkt bleiben kann. Ob ein solcher Wächter gebaut werden soll, ist
eine eigene Entscheidung mit eigenem Zuschnitt — er wird hier **benannt, nicht gebaut**.

## Reihenfolge

#1566 zuerst, #1581 danach. Grund: #1566 ist eine abgeschlossene Messung gegen eine
Datei; #1581 schreibt Befunde fort, zu denen der #1566-Befund selbst gehört (ein
Spec-Text, der eine nicht existierende Konfiguration beschreibt, ist ein Exemplar von
NFR-018 §1). Andersherum müsste #1581 zweimal geschrieben werden.

## Geteilte Berührungsfläche

`spec/nfr/NFR-009_Dependency-Management.md` §3.2 · `spec/nfr/NFR-018_CI-CD-Pipeline-Integritaet.md`
Kein Produktionscode. Kein Workflow. Keine Migration.

## Vollständigkeitsmatrix

| Gegenstand | #1566 | #1581 |
|---|---|---|
| Spec-Text (DE, kanonisch) | §3.2 ersetzt durch den gemessenen Ist-Zustand | fünf Lücken normativ gefasst |
| Doku `docs/` | `not applicable` — NFR-Dokumente werden nicht nach `docs/` gespiegelt | `not applicable`, gleicher Grund |
| Produktionscode | `not applicable` — die Änderung stellt Text auf gemessenen Zustand um, sie ändert kein Verhalten | `not applicable`, gleicher Grund |
| Tests / Wächter | `not applicable` — ein Spec-Wächter ist der benannte, bewusst nicht gebaute Prozessbefund | `not applicable`, gleicher Grund |
| Messbeleg im Text | `grep -c` je Key, Ausgabe im Absatz zitiert | je Lücke die Messung, die sie belegt, mit Datum |
| Vale / Prosa-Gate | `task precommit` über den Baum, tatsächliche Ausgabe im PR | dito |
| Migration | `not applicable` | `not applicable` |

## Risiken

- **#1581 hat keine scharfe Außenkante.** „Fortschreiben" kann beliebig wachsen. Grenze:
  ausschließlich die fünf im Issue benannten Lücken, jede mit ihrer Messung. Alles
  weitere wird als Posten notiert, nicht geschrieben.
- **Die Referenz-Konfiguration in #1566 könnte ein Soll und kein Ist sein.** Dann wäre
  Löschen falsch und Kennzeichnen richtig. Vor dem Ersetzen ist zu klären, ob §3.2 je
  als Zielbild gemeint war; das Issue liest sie als Ist-Beschreibung, und zwei Keys sind
  durch beobachtetes Verhalten widerlegt (`renovate/…` statt `deps/…`), was für Ist
  spricht. Wird beim Mitglied verifiziert, nicht hier entschieden.
- **Zwei Spec-Texte in einem PR** sind für einen Reviewer zwei Lesevorgänge. Akzeptiert:
  die Klasse ist dieselbe, und getrennt würde #1581 den #1566-Befund doppelt behandeln.

## Außerhalb des Zuschnitts

- Ein Wächter, der Spec-Behauptungen gegen das Repository falsifiziert (Prozessbefund
  oben) — eigener Posten.
- #1584 (Entscheidungs-Issue zum Kostenmodell) und #1596 (Relevanzfilter prüft Erwähnung
  statt Lesezugriff) — bei der Aufnahme geprüft und **nicht** aufgenommen.
- Jede Änderung an `renovate.json5` selbst. Diese Gruppe ändert Text über die Datei,
  nie die Datei.

## Offene Fragen

1. Ist NFR-009 §3.2 als Ist-Beschreibung oder als Zielbild geschrieben? (Mitglied #1566
   klärt das am Text, bevor es ersetzt.)
2. Soll Punkt 5 aus #1581 (Ausnahmeregister mit Verfallsdatum) den `# prose-permeable:`-Marker
   aus #1642 normativ machen — oder bleibt der bewusst eine dauerhafte Entscheidung ohne
   Verfall, wie #1456 entschieden hat? Das ist eine Betreiberfrage, keine Schreibfrage.
