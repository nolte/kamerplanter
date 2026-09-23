# DEVTOOL-002: `task precommit` unter parallelen Arbeitskopien

**Status:** Messbericht (verbindlich für die Bewertung von Gate-Ausgaben)
**Anlass:** Issues #1641 und #1649
**Gemessen am:** 2026-09-21 / 2026-09-23

## Frage

Dieses Repository arbeitet planmäßig in mehreren Arbeitskopien gleichzeitig
(`task worktree:add`). Alle teilen sich **einen** pre-commit-Store unter
`~/.cache/pre-commit`. #1641 berichtete, dass zwei gleichzeitige
`pre-commit run --all-files` aus zwei Arbeitskopien einander falsche Ergebnisse
lieferten: `ruff` meldete `E501` in Dateien, die in der meldenden Arbeitskopie
nachweislich sauber waren.

Entscheidend ist dabei nicht das beobachtete falsche Rot — das meldet sich
selbst. Entscheidend ist, ob ein **falsches Grün** möglich ist: ein Hook, der
`Passed` für eine Datei meldet, die er nicht geprüft hat. Das würde jeden
Bericht schwächen, der die Ausgabe dieses Kommandos als Beleg zitiert.

## Antwort in einem Satz

**Ja, ein falsches Grün ist möglich — aber nicht durch den geteilten Store.**
Der Auslöser ist ein *zweiter Schreiber in derselben Arbeitskopie* (#1649), nicht
eine zweite Arbeitskopie (#1641). Beides wurde gemessen; die Reihenfolge der
beiden Kapitel unten ist die Reihenfolge, in der es geprüft wurde.

## Teil 1 — zwei Arbeitskopien, geteilter Store (#1641)

Alle Läufe: zwei Arbeitskopien desselben Repositories auf demselben Commit
(`e2347b9b2`), beide `pre-commit run --all-files`, verglichen gegen serielle
Läufe derselben Bäume.

Der Prüfling war eine **gesetzte Verletzung**: Arbeitskopie A enthielt eine
Datei mit einer 202 Zeichen langen Zeile (`E501`, Grenze 120), Arbeitskopie B
war sauber. A muss also *immer* `Failed` melden, B *immer* `Passed`. Jede
Abweichung ist entweder ein falsches Grün (A meldet `Passed`) oder ein falsches
Rot (B meldet `Failed`).

| Lauf | Bedingung | Paare | Falsches Grün | Falsches Rot |
|------|-----------|-------|---------------|--------------|
| 1 | `ruff-lint`, warmer Store, saubere Bäume | 30 | 0 | 0 |
| 2 | `ruff-lint`, zusätzlich unstaged Änderungen in beiden Bäumen | 30 | 0 | 0 |
| 3 | `ruff-lint`, `pre-commit clean` vor jedem Paar (beide müssen die Hook-Umgebung gleichzeitig bauen) | 10 | 0 | 0 |
| 4 | `ruff-lint`, unter voller CPU-Auslastung (8 Busy-Loops auf 8 Kernen) | 100 | 0 | 0 |
| 5 | **volle Hook-Suite** (41 Hooks), gleichzeitig | 5 | 0 | 0 |

Lauf 5 wurde nicht nur am Exit-Code verglichen, sondern Hook für Hook: der
Ergebnisvektor aller 41 Hooks war in allen 5 Paaren **identisch** mit dem
seriellen Referenzlauf derselben Arbeitskopie.

**Über diesen Weg konnte kein falsches Grün erzeugt werden.** Die gesetzte
`E501`-Verletzung wurde in 175 von 175 gleichzeitigen Läufen gefunden.

Lauf 4 bildet die Bedingung nach, unter der die Ursprungsbeobachtung entstand
(die Maschine trug zu dem Zeitpunkt 16 verwaiste Busy-Loop-Shells).

## Teil 2 — zwei Schreiber in EINER Arbeitskopie (#1649)

#1649 belegte hier ein falsches **Rot**: der Hook `e2e-selftest` meldete `files
were modified by this hook`, obwohl er wegen `-p no:cacheprovider` nichts
schreiben kann und sein `files:`-Filter die tatsächlich geänderte Markdown-Datei
nicht trifft. Beide Richtungen wurden daraufhin absichtlich hergestellt.

Jeder Lauf protokolliert Start- und Endzeit von A sowie den Zeitstempel des
zweiten Schreibers — ein Schreiber, der *nach* A feuert, beweist nichts. (Der
erste Anlauf dieser Messung hatte genau diesen Fehler: A lief 0,5 s, der
Schreiber wartete 3 s, und das „falsche Grün" war schlicht eine Datei, die es
zum Messzeitpunkt noch nicht gab.)

### FG-1 — neue Datei, während des Laufs gestaged → **falsches Grün, bewiesen**

```
[A]      10:02:56  pre-commit run --all-files startet
[writer] 10:03:41  staged eine NEUE getrackte Datei mit E501
[A]      10:12:07  fertig, exit 0
[A]      ruff check (backend).................................Passed
[A]      Anzahl Failed im gesamten Lauf: 0
[serial] 10:12:07  derselbe Baum, nichts nebenher:
[serial] ruff check (backend).................................Failed
```

Die volle Suite meldete **0 Failed und exit 0** über einen Baum, den der
unmittelbar folgende Lauf rot nennt. Der Schreibvorgang lag nachweislich
*innerhalb* des Fensters.

### FG-2 — bestehende Datei, geändert bevor der Hook lief → **gefangen**

Schreiber bei +45 s, `ruff-lint` läuft erst an Position ~30 der Suite: die
Änderung war da, als der Hook die Datei las, und er meldete korrekt `Failed`.
Dieser Lauf reproduzierte nebenbei **#1649 im Kontrollversuch**: derselbe Lauf
meldete zusätzlich

```
E2E harness self-tests (browser-free,...............................Failed
- hook id: e2e-selftest
- files were modified by this hook
352 passed
```

für einen Schreibvorgang an `src/backend/app/main.py` — einem Pfad, den der
`files:`-Filter dieses Hooks nicht trifft, durch einen Hook, der nicht schreiben
kann. Damit ist der erste Haken von #1649 („absichtlich reproduzieren") eingelöst.

### FG-3 — bestehende Datei, geändert *nachdem* der Hook gemeldet hatte → **falsches Grün auf Hook-Ebene**

```
[A]      10:22:45  pre-commit run --all-files startet
[writer] 10:29:24  hängt E501 an, NACHDEM ruff-lint bereits gemeldet hatte
[A]      10:31:07  fertig
[A]      ruff check (backend).................................Passed
[A]      zusätzlich Failed: e2e-selftest, mypy (kp_vectordb)  — beide
         „files were modified by this hook", beide für einen Schreibvorgang an
         src/backend/app/main.py, den keiner von beiden ausgeführt haben kann
[serial] ruff check (backend).................................Failed
```

`ruff-lint` meldete `Passed` für eine Datei, die am Ende des Laufs eine
Verletzung trug — ein falsches Grün auf Hook-Ebene. Der Lauf insgesamt wurde rot,
aber über **zwei** falsch beschuldigte Hooks: das ist #1649, in einem Lauf zweimal
und beide Male mit dem falschen Namen. Wer dieser Ausgabe folgt, sucht in
`tests/e2e_selftest/` und in `src/libs/kp_vectordb/` nach einem Defekt, während
der echte Befund in `app/main.py` steht und von keinem Hook genannt wird.

### Warum FG-1 durchkommt und FG-2 nicht — der benannte Mechanismus

Zwei verschiedene Fenster, und nur eines ist bewacht:

1. **Die Dateiliste** wird *einmal* am Anfang mit `git ls-files` erhoben.
   Alles, was danach entsteht, ist in keinem Hook-Aufruf enthalten.
2. **Der Nachher-Vergleich** von pre-commit ist ein `git diff` (Arbeitsbaum
   gegen Index). Er bemerkt *Inhaltsänderungen* an getrackten Dateien — und
   schreibt sie demjenigen Hook zu, der gerade lief, was #1649 ist. Eine neu
   **gestagte** Datei ändert aber den Index, nicht den Diff: sie ist für diesen
   Vergleich unsichtbar.

FG-1 fällt durch beide Maschen und erzeugt deshalb ein sauberes falsches Grün.
FG-3 fällt nur durch die erste: der Inhaltsvergleich merkt, dass *etwas*
geschrieben wurde, und benennt den Falschen — der geprüfte Hook bleibt grün.

## Mechanismus

### Was geteilt wird — und was nicht

- **Geteilt:** ausschließlich `~/.cache/pre-commit` (Hook-Umgebungen und
  `db.db`).
- **Nicht geteilt:** `.ruff_cache`, `.mypy_cache`, `.pytest_cache`,
  `node_modules` — sie liegen alle *innerhalb* der Arbeitskopie, weil pre-commit
  jeden Hook mit der Arbeitskopie als Arbeitsverzeichnis startet (der
  Backend-ruff-Hook zusätzlich nach `cd src/backend`). Zwei Arbeitskopien haben
  also zwei getrennte ruff-Caches; ein gemeinsamer `cache-dir` ist nirgends
  konfiguriert.

### Die Patch-Klasse trifft dieses Kommando nicht

pre-commit legt bei unstaged Änderungen einen Patch unter
`~/.cache/pre-commit/patch<zeit>-<pid>` ab und spielt ihn danach zurück — die
Klasse, an der dieses Repository schon einmal Arbeit verloren hat.

Sie ist hier **strukturell ausgeschlossen**: `pre-commit run --all-files` betritt
diesen Pfad überhaupt nicht.

```python
# pre_commit/commands/run.py (4.5.0), Zeile 344
stash = not args.all_files and not args.files
```

`task precommit` übergibt immer `--all-files`. Zusätzlich enthält der Dateiname
seit langem die PID, eine Kollision zweier Läufe wäre also auch sonst nicht
möglich.

### Jede Mutation des Stores steht unter einem Lock

Neue Repo-Verzeichnisse (`Store._new_repo`) und Hook-Umgebungen
(`repository.install_hook_envs`) werden unter `Store.exclusive_lock()` angelegt,
einem `fcntl.flock` auf `~/.cache/pre-commit/.lock`. Lauf 3 zielt genau darauf:
mit geleertem Store müssen beide Prozesse die Umgebung gleichzeitig bauen — das
Lock serialisiert sie, der zweite findet sie danach fertig vor.

### Ein Restrisiko, das real ist, aber nicht durch zwei Arbeitskopien ausgelöst wird

`install_hook_envs` nimmt das Lock **nur, wenn der aufrufende Prozess selbst
etwas installieren muss**:

```python
if not _need_installed():
    return
with store.exclusive_lock():
    for hook in _need_installed():
        _hook_install(hook)
```

Ein Prozess, der alle Umgebungen für gesund hält, führt die Hooks also **ohne
Lock** aus — während `_hook_install` mit `rmtree(venv)` auf dasselbe gemeinsame
Verzeichnis beginnt. Der Lesende ist gegen eine gleichzeitige Neuinstallation
nicht geschützt.

Auslösen lässt sich das nur, wenn zwei Prozesse den Gesundheitszustand derselben
Umgebung *im selben Moment* unterschiedlich beurteilen. Zwei Arbeitskopien mit
identischer `.pre-commit-config.yaml` können das nicht: gleiche
`additional_dependencies` ergeben dasselbe Zustandsfile, unterschiedliche ergeben
getrennte Verzeichnisse. Erreichbar ist es über ein `pre-commit clean`/`gc`
nebenher oder über eine abgebrochene Installation, die eine kaputte Umgebung
hinterlässt. Das ist ein Upstream-Verhalten, kein Defekt dieses Repositories, und
es erzeugt einen Absturz, kein falsches `Passed`.

## Folgerungen

1. **Kein per-Arbeitskopie-`PRE_COMMIT_HOME`.** Der in #1641 vorgeschlagene Fix
   wurde bewusst nicht umgesetzt, und zwar aus zwei getrennten Gründen. Erstens
   kostet er gemessen **253 MB und 1:26 Aufbauzeit pro Arbeitskopie** (41 auf
   dieser Maschine, also rund 10 GB und knapp eine Stunde einmalig). Zweitens —
   und das ist der entscheidende Grund — **hätte er das einzige nachgewiesene
   falsche Grün nicht verhindert**: FG-1 spielt sich vollständig innerhalb *einer*
   Arbeitskopie ab und rührt den geteilten Store nicht an. Getrennte Stores hätten
   gegen den einen Weg geholfen, der sich in 175 Läufen als unauffällig erwies,
   und gegen den, der nachweislich trägt, gar nicht.
2. **CI ist nicht betroffen — geprüft, nicht vermutet.** Der erforderliche
   `static / Static CI Tests`-Job läuft über
   `nolte/gh-plumbing/.github/workflows/reusable-pre-commit.yaml` mit
   `runs-on: ubuntu-latest`, also auf einer eigenen, kurzlebigen VM mit eigenem
   Dateisystem und genau einem `pre-commit/action`-Schritt. Zwei gleichzeitige
   Läufe teilen sich dort nichts; `concurrency: static-${{ github.ref }}` mit
   `cancel-in-progress` lässt pro Ref ohnehin nur einen laufen.
3. **Die Isolation wird ab sofort beobachtet, nicht behauptet.**
   `scripts/precommit_sibling_notice.sh` meldet zwei Dinge, die das Verdikt
   selbst nicht tragen kann: einen überlappenden Geschwisterlauf (über
   Lebendigkeit einer registrierten PID, an beiden Enden geprüft) und — der
   #1649-Weg — **jede Veränderung des Baums während des Laufs**, mit den
   betroffenen Pfaden. Genau diese Pfadliste ist der Wert: hätte sie in #1649
   vorgelegen, wäre `spec/nfr/NFR-009_…md` darin gestanden und niemand hätte in
   `tests/e2e_selftest/` nach einem Defekt gesucht, den es nicht gibt. Der
   Fingerabdruck (`git status --porcelain -uall` plus Größe und mtime jeder
   getrackten Datei) kostet gemessen **0,07–0,17 s**. Verdikt und Exit-Code
   bleiben unberührt.

4. **Eine Warnung ist schwächer als eine Isolierung — bewusst.** Erzwungene
   Serialisierung (`flock` um den Lauf) wäre die starke Variante. Sie wurde
   verworfen, weil sie das gemessene Problem nicht trifft: der nachgewiesene
   Weg ist ein *Editor* oder ein zweiter Agent im selben Baum, kein zweites
   `task precommit` — und gegen einen schreibenden Editor kann dieses Kommando
   nichts sperren. Was es kann, ist hinterher sagen, dass geschrieben wurde. Die
   verbindliche Regel bleibt organisatorisch (*ein Schreiber pro Arbeitskopie*,
   `spec/project/parallel-working-copies/`); die Meldung macht ihren Bruch
   sichtbar, statt ihn zu verhüten.

## Was offen bleibt

Die Ursprungsbeobachtung aus #1641 — `ruff` meldet `E501` in sauberen Dateien —
konnte über den Zwei-Arbeitskopien-Weg nicht reproduziert werden, und es gibt
keine Aufzeichnung der damaligen Ausgabe. Möglich bleibt, dass die beiden
Arbeitskopien damals **nicht** auf demselben Commit standen — dann hätte die
zweite Kopie die langen Zeilen tatsächlich enthalten und die Meldung wäre korrekt
gewesen. Diese Messung schließt das nicht aus; sie zeigt nur, dass der geteilte
Store bei gleichem Commit kein falsches Ergebnis erzeugt.

Sollte der Fehler erneut auftreten, ist das Nötige: die vollständige Ausgabe
**beider** Läufe, `git rev-parse HEAD` in beiden Arbeitskopien und
`ls -la ~/.cache/pre-commit`, aufgezeichnet vor dem nächsten Lauf.
