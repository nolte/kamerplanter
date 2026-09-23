# DEVTOOL-003: Integrationstest-Datenbanken unter parallelen Arbeitskopien

**Status:** Messbericht (verbindlich für die Bewertung von Ausgaben des Integrations-Tiers)
**Anlass:** Issue #1661 (Familie von #1641 / #1649, DEVTOOL-002)
**Gemessen am:** 2026-09-23, Commit `bc7de7c58` (vorher) / `c60d7063e` (nachher)

## Frage

`src/backend/tests/integration/` misst die Repository- und AQL-Schicht gegen
eine **echte** ArangoDB. Auf einer Entwicklermaschine ist das eine Instanz
unter `localhost:8529`, die sich alle Arbeitskopien teilen — und parallele
Arbeitskopien sind der planmäßige Arbeitsmodus dieses Repositories
(`task worktree:add`, `spec/project/parallel-working-copies/`).

#1661 beobachtete zwei Fehler in einem Lauf, die vom Nachbarlauf stammten:
`[HTTP 404][ERR 1228] database not found`. Offen waren drei Dinge: **wie viele**
Module das betrifft, ob das Ganze auch in die **gefährliche Richtung** kippen
kann (ein Lauf sieht die Zeilen des anderen und besteht eine Zusicherung, die
er hätte verfehlen müssen), und ob **CI** betroffen ist.

## Antwort in einem Satz

**21 von 22 Modulen; ja, ein falsches Grün ist konstruierbar; CI ist nicht
betroffen.** Behoben durch einen pro-Prozess eindeutigen Datenbanknamen mit
Aufräumen, nicht durch eine Sperre.

## Teil 1 — die Klasse, aufgezählt

Jedes Modul des Tiers, das eine Datenbank unter **festem Namen** anlegt oder
löscht (`create_database` / `delete_database` / `has_database`,
`Settings(arangodb_database=…)`, `client.db(…)`):

| Schreibweise | Module |
|---|---|
| `_DB_NAME = "kamerplanter_…_test"` | 12 |
| `TEST_DATABASE = "kamerplanter_…_test"` / `"kp_test_…"` | 8 |
| Literal direkt am Aufruf (`"kamerplanter_test"`, `test_arango_integration.py`) | 1 |
| **Summe** | **21 von 22** (`test_perennial_cycle_loop.py` braucht keinen Server) |

Alle 21 tun bei Setup `if has_database: delete_database; create_database`
und bei Teardown `delete_database`. Zwei Sitzungen auf demselben Server
löschen einander also die Datenbank *unter dem laufenden Test weg*.

**Wo der Sweep blind war — benannt, nicht vermutet.** Die Frage „nenne eine
Schreibweise, die mein Muster nicht trifft" ergab:

- `ArangoConnection.connect()` (`app/data_access/arango/connection.py:26`)
  legt die Datenbank *selbst* an, wenn sie fehlt. Ein Modul, das nur
  `Settings(arangodb_database=…)` baut und nie `create_database` schreibt,
  erzeugt trotzdem eine — der Grep nach `create_database` allein hätte fünf
  Module übersehen.
- Ein Name aus einer **anderen Branch**: auf dem Entwicklungsserver lag
  `kamerplanter_privacy_export_evidence`, eine Datenbank ohne Quelle in
  irgendeiner Arbeitskopie dieser Maschine. Ein Sweep über `develop` sieht
  nur `develop`. Deshalb zählt der Guard (Teil 4) die *Klasse* und nicht die
  gefundenen Namen, und deshalb räumt das Fixture nur den eigenen Namensraum
  auf — diese Datenbank bleibt liegen, sie gehört niemandem Bekanntem.
- Der f-String: der erste Entwurf des Guards erkannte `f"{PREFIX}suffix"`
  nicht als fest (der Name steckt in `ast.FormattedValue`). Die gepflanzte
  Datei fand das; der Guard wurde korrigiert, bevor er je grün war.
- Außerhalb des Tiers: `docker-compose.e2e.yml` setzt `kamerplanter_e2e` /
  `kamerplanter_e2e_full` fest — aber in einem eigenen Compose-Projekt mit
  eigenem ArangoDB-Container; zwei E2E-Stacks kollidieren zuerst am Port.
  Nicht Gegenstand dieser Reparatur. TimescaleDB und Redis: kein Test des
  Tiers fasst sie an (gemessen per Grep über `tests/integration/` und
  `tests/support/`).

## Teil 2 — die Kollision, reproduziert

Zwei Checkouts desselben Commits (`bc7de7c58`: Primär-Checkout und
Arbeitskopie `test-db-probe`), beide `pytest tests/integration/ -q
--max-skipped 0`, gleichzeitig gestartet. Seriell davor: **269 passed, 0
errors, 205 s.**

| Paar | Seite | Ergebnis | Dauer |
|---|---|---|---|
| 1 | A | 202 passed, **67 errors** | 113 s |
| 1 | B | 187 passed, **18 failed, 64 errors** | 119 s |
| 2 | A | 208 passed, **61 errors** | 171 s |
| 2 | B | 183 passed, **1 failed, 85 errors** | 154 s |
| 3 | A | 187 passed, **18 failed, 65 errors** | 323 s |
| 3 | B | 244 passed, **3 failed, 23 errors** | 474 s |

Fehlerarten je Seite (Paar 1, A): 20× `[ERR 1228] database not found`, 40×
`[ERR 1207] duplicate name` (beide legen dieselbe Collection an), 7×
`[ERR 1203] collection not found`.

**Die 18 `failed` sind das teure Ende.** Sie stammen aus
`test_plant_scoped_route_residue_tenant_scope.py` und lauten
`assert 500 == 404` bzw. `foreign key answered 500: Internal Server Error`:
die API antwortete 500, weil ihre Datenbank unter ihr verschwand — und das
liest sich exakt wie ein Mandanten-Isolationsdefekt in der Änderung unter
Review. Ein Fehler, der eine Datenbank *benennt*, ist diagnostizierbar; einer,
der eine *Route* benennt, schickt den nächsten Leser in die falsche Datei.

Paar 3 lief zusätzlich neben einem **dritten** Lauf aus einer fremden
Arbeitskopie (`relevance-reads`, gestartet 12:57:49, `task
test:backend:integration`), der nicht Teil der Messung war — die 323 s und
die Abweichung zu Paar 1/2 stammen daher. Dieser fremde Lauf wurde von der
Messung mit hoher Wahrscheinlichkeit selbst gerötet; das ist genau der
Befund, um den es geht.

## Teil 3 — das falsche Grün, konstruiert

Der Mechanismus ist kein Timing-Zufall: ein Datenbank-Handle in python-arango
ist ein **Name**, keine Identität. Löscht der Nachbar die Datenbank und legt
sie unter demselben Namen neu an, antwortet sie dem ersten Lauf weiter — mit
dem Zustand des Nachbarn.

Konstruktion (`falsepass.py`, Fixture-Form des Tiers: drop-if-exists → create
→ seed → Schreibzugriff → Lesen → drop), zwei Prozesse:

- **broken**: der Schreibzugriff unter Test ist ein **No-op** (gesetzter
  Defekt, den der Test finden *muss*), dann 8 s warten, dann lesen und
  `notes == "new"` zusichern. Allein gelaufen: `FAIL (notes was not updated)`
  — die Kontrolle.
- **intact**: startet 3 s später, bootstrappt **denselben Namen**, schreibt
  wirklich, hält die Datenbank 12 s (wie ein modulweites Fixture) und löscht
  sie dann.

```
[broken] 13:03:43.337 bootstrapped kamerplanter_falsepass_test, seeded notes='old'
[broken] 13:03:43.338 write under test: NO-OP (seeded defect)
[intact] 13:03:46.477 bootstrapped kamerplanter_falsepass_test, seeded notes='old'
[intact] 13:03:46.484 write under test: real update notes='new'
[broken] 13:03:51.347 read back: 'new'
[broken] 13:03:51.347 VERDICT: PASS  <-- a false green if you are reading this
```

**Der defekte Lauf meldete PASS.** Derselbe Aufbau mit `run_database_name()`:

```
[broken] 13:03:59.024 bootstrapped kp_it_falsepass__1790161438_11f067, seeded notes='old'
[intact] 13:04:01.970 bootstrapped kp_it_falsepass__1790161441_fb9536, seeded notes='old'
[broken] 13:04:07.028 read back: 'old'
[broken] 13:04:07.028 VERDICT: FAIL (notes was not updated)  <-- the defect was caught
```

Im echten Tier ist die Bedingung erfüllt: dieselben Module laufen in beiden
Sitzungen mit denselben deterministischen Schlüsseln (`tenant-alpha`,
`user-erika`, `profile-1`) und schreiben denselben Sollzustand. Ob ein
falsches Grün in den drei Paaren oben *tatsächlich* auftrat, lässt sich aus
einem grünen Testergebnis nicht ablesen — deshalb die Konstruktion.

## Teil 4 — Entscheidung: Suffix statt Sperre

| | Pro-Sitzung-Suffix (gewählt) | Sperre |
|---|---|---|
| Kosten | keine; `_system`-Handle existiert schon | serialisiert: jeder wartende Nachbar zahlt ~3,5 min |
| CI | unverändert (eigener Service-Container) | bräuchte einen geteilten Sperrort, den CI nicht hat |
| Leck bei abgeschossener Sitzung | ja — daher Aufräumen (unten) | nein (fester Name wird wiederverwendet) |
| Fremde Sitzung auf derselben Branch | isoliert | wartet |

`run_database_name(base)` in `tests/support/arango_integration.py` liefert
`kp_it_<base>__<epoch>_<hex6>`:

- **stabil** innerhalb eines Prozesses (`functools.cache`), **verschieden**
  über Prozesse (gemessen über eine echte Prozessgrenze im Guard);
- **nicht vererbt** über die Umgebung — ein Kind-pytest
  (`test_integration_tier_gate.py` startet welche) bekommt seinen eigenen
  Namensraum statt den des Elternprozesses, sonst wäre die Kollision nur
  verschoben;
- **aufgeräumt**: das Session-Fixture löscht beim Start jede
  laufgebundene Datenbank, deren Zeitstempel älter als
  `STALE_AFTER_SECONDS` (6 h) ist, und beim Ende jede mit dem eigenen Token —
  das deckt ein Modul ab, dessen Teardown nie lief. Beide Sweeps treffen nur
  Namen, die `RUN_DATABASE_PATTERN` erkennt; `kamerplanter` (Demo-Seed),
  `kamerplanter_e2e*` und handgeschriebene Namen liegen außerhalb;
- der `if has_database: delete_database`-Vorspann der Fixtures bleibt stehen;
  er schützt jetzt nichts mehr, tut aber auch nichts.

Der Guard `tests/unit/guards/test_integration_databases_are_run_scoped.py`
zählt die **Klasse**: jede feste Zeichenkette — Literal, Modulbindung,
f-String aus festen Teilen, Verkettung — die einen der genannten Aufrufe
erreicht, ist rot (`"_system"` per Wert ausgenommen); ein Boden von 15
Modulen, die `run_database_name(` im **ausführbaren** Text rufen
(`scripts/source_text.py`), fängt den schleichenden Rückbau. Auf dem
unbehobenen Baum: 21 Module rot, 0 Helfer-Aufrufe. Gepflanzte Dateien
beweisen, dass Kommentar und Docstring in keiner Richtung zählen.

## Teil 5 — nach der Reparatur

Gleiche Anordnung, Commit `c60d7063e` in beiden Checkouts:

| Paar | Seite | Ergebnis | Dauer |
|---|---|---|---|
| 1 | A | **269 passed, 0 failed, 0 errors** | 745 s |
| 1 | B | **269 passed, 0 failed, 0 errors** | 748 s |
| 2 | A | **269 passed, 0 failed, 0 errors** | 551 s |
| 2 | B | **269 passed, 0 failed, 0 errors** | 554 s |
| 3 | A | **269 passed, 0 failed, 0 errors** | 462 s |
| 3 | B | **269 passed, 0 failed, 0 errors** | 460 s |

Sechs von sechs Seiten identisch mit dem seriellen Referenzlauf (269 passed).
Die Dauer ist **nicht** vergleichbar mit den 205 s des seriellen Laufs: die
Maschine trug während der Messung eine Load von 14–17 auf 8 Kernen (weitere
Arbeitskopien, die Guard-Lane dieses Branches lief parallel zu Paar 1), und
zwei volle Läufe teilen sich einen `arangod`. Vorher liefen die Paare
*schneller* (113–171 s), weil die Kollision die meisten Module nach dem ersten
Fehler abbrach — die Zeit war der Preis für ein Ergebnis, das nichts bedeutete.
Nach dem Fix bleibt auf dem Server nichts zurück: nach jedem Paar listet
`_api/database` nur `_system` und die fremde
`kamerplanter_privacy_export_evidence`.

Seriell danach: **269 passed, 277 s** — mit einer vorher von Hand angelegten
verwaisten Datenbank `kp_it_planted_orphan__1700000000_abcdef` auf dem Server.
Der Lauf meldete in seiner zweiten Zeile

```
#1661: dropped 1 stale run-scoped database from an earlier session (older than 6 h counts as stale): kp_it_planted_orphan__1700000000_abcdef
```

und hinterließ nichts: `_api/database` listet danach `_system` und die fremde
`kamerplanter_privacy_export_evidence`, sonst nichts. Der Sweep am
Sitzungsende lief in allen Läufen leer (jedes Modul räumte selbst auf); sein
Prädikat ist im Guard gegen ein `_system`-Double geprüft, das Nachbar-,
Alt- und Fremdnamen nebeneinander hält.

## Teil 6 — CI, geprüft statt angenommen

- Das Tier läuft in genau **einem** Job: `backend-guards.yml` →
  `integration`, mit eigenem `services: arangodb` pro Job auf einem
  GitHub-gehosteten Runner (ein Job je VM) und `concurrency:
  backend-guards-${ref}` / `cancel-in-progress` je Branch.
- `backend.yml` (Coverage-Lane) übergibt `--ignore=tests/integration`; die
  Tiers `unit`, `contracts`, `api` enthalten das Verzeichnis nicht.
- Keiner der `schedule:`-Workflows (`e2e-nightly`, `security-*-nightly`,
  `release-*`, `renovate-health`) ruft pytest über das Backend.

CI war also nie betroffen; die Reparatur ändert dort nur die Namen.

## Konsequenz für Berichte

Ein Integrations-Lauf vor `c60d7063e`, der neben einem Nachbarn lief, ist
kein Beleg — weder für Rot noch für Grün. Ab `c60d7063e` gilt: ein Nachbar
kann den Lauf verlangsamen (Paar 3: 323 s statt 205 s), aber nicht mehr
sein Ergebnis ändern. Wer die Ausgabe zitiert, nennt weiterhin, ob ein
Geschwister-pytest lief (`pgrep -fa "pytest tests/integration"`), weil die
Laufzeit sonst nicht einzuordnen ist.
