---

ID: NFR-018
Titel: CI/CD-Pipeline-Integrität — Prüfungen müssen messen, was sie behaupten
Kategorie: Qualitätssicherung / Betrieb
Unterkategorie: Gate-Integrität, Reproduzierbarkeit, Auslieferungsgarantien
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: GitHub Actions, pre-commit, Docker, Helm, SLSA-Provenance
Status: Genehmigt
Priorität: Hoch
Version: 1.1
Autor: nolte
Datum: 2026-08-08
Tags: [ci, cd, pipeline, gate-integrity, reproducibility, provenance, supply-chain, vacuous-success]
Abhängigkeiten: [NFR-003, NFR-008, NFR-009, NFR-014, NFR-015]
Betroffene Module: [.github/workflows, .pre-commit-config.yaml, scripts/security, helm]
---

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.1 | 2026-08-08 | §2.1 (Ratchet-Baselines werden berechnet, nicht versioniert — Herleitung #973, bis dahin nur ein `Taskfile.yaml`-Kommentar) und §2.2 (eine überwiegend abgebrochene Lane existiert nicht — Verallgemeinerung der Analyse aus NFR-014 §4.1, #993/#1013) ergänzt. Beide aus der Issue-Muster-Analyse vom 2026-08-08, Maßnahmen P5.6/P5.3. |
| 1.0 | 2026-08-01 | Erstversion. Entstanden aus dem CI/CD-Audit vom 2026-08-01, das 21 Befunde ergab — von denen die Mehrzahl derselben Fehlerklasse angehörte. Diese NFR hält die Klasse und die daraus abgeleiteten Regeln fest, damit sie nicht bei jedem Audit neu entdeckt werden muss. |

# NFR-018: CI/CD-Pipeline-Integrität

## Abgrenzung zu bestehenden Specs

| Quelle | Fokus | Definiert |
|---|---|---|
| NFR-003 | Ruff, ESLint, TypeScript | **Welche** statischen Prüfungen laufen |
| NFR-008 / NFR-008a | Testpyramide, Testprotokoll, E2E-Konventionen | **Was** die Tests prüfen |
| NFR-009 | Dependency-Lifecycle, CVE- und Lizenz-Scanning | **Welche** Supply-Chain-Pflichten bestehen |
| NFR-014 / NFR-015 | Nuclei, OWASP ZAP | **Welche** DAST-Prüfungen bestehen |
| **NFR-018 (dieses Dokument)** | Eigenschaften, die jede dieser Prüfungen als *Gate* erfüllen muss | **Ob** eine grüne Prüfung etwas bedeutet |

Die anderen NFRs beschreiben, *was* geprüft wird. Keine beschreibt, *unter welchen
Bedingungen ein grünes Ergebnis eine Aussage ist*. Genau in dieser Lücke sind alle
unten katalogisierten Defekte entstanden: Jeder einzelne war ein Gate, das seine
Anforderung formal erfüllte und inhaltlich nichts prüfte.

---

## 1. Die Fehlerklasse

> **Eine Prüfung, die Erfolg meldet ohne zu messen, ist von einer Prüfung, die
> gar nicht läuft, nicht zu unterscheiden — und schlimmer als deren Fehlen, weil
> sie Abdeckung vortäuscht.**

Das ist keine abstrakte Sorge. Das CI/CD-Audit vom 2026-08-01 fand die folgenden
Instanzen, alle gleichzeitig aktiv, alle über Monate unbemerkt:

| # | Ort | Konstruktion | Folge |
|---|---|---|---|
| 1 | `scripts/frontend_hook.sh` (vor #814) | `test -d node_modules \|\| exit 0` | pre-commit meldete `Passed`; nicht kompilierender Code erreichte `develop` |
| 2 | `.pre-commit-config.yaml`, Hook `nuclei-validate` | `command -v nuclei \|\| exit 0` | Auf dem **einzigen required Check** meldete die Template-Validierung Erfolg, ohne je zu validieren — nuclei ist im Python-only-Runner nie installiert |
| 3 | `security-zap-baseline.yml` | drei `test -f` statt eines Scans | NFR-015 galt als in Kraft; es lief nie ein ZAP |
| 4 | `skaffold-verify.yml` | `skaffold render … \|\| true` | Der Schritt scheiterte **jedes Mal** (`does the image exist remotely?`), verwarf den Fehler und lud ein leeres Artefakt hoch |
| 5 | `skaffold-verify.yml` | `if: steps.check.outputs.exists == 'true'` auf allen Schritten | Wäre `skaffold.yaml` je gefehlt, hätte der Job alles übersprungen und grün gemeldet |
| 6 | `frontend.yml`, Job `lint-test-build` | Steps gaten nur auf `needs.changes.outputs.frontend` | Bei fehlgeschlagenem `changes`-Job: alle Steps skipped → Job `success` → **required Check grün ohne tsc, ESLint, vitest, Build** |
| 7 | `security-nuclei-nightly.yml` | Ziel aus nie gesetzter `vars.STAGING_BASE_URL` | Jeder Nachtlauf scheiterte am ersten Schritt; der Melde-Step meldete dabei `success`, weil ohne `results.jsonl` nur eine Notice abgesetzt wird |
| 8 | `nuclei -validate` über ein leeres Verzeichnis | Exit 0 | Löschen des Template-Sets hätte das Gate grün gemacht |
| 9 | `docker-publish.yml` | `sed -i "s/tag: latest/…/"` ohne Verifikation | Ändert sich der Default in `values.yaml`, greift die Ersetzung nicht mehr, der Schritt bleibt Exit 0, und das Release liefert einen beweglichen Tag aus |

Die Klasse hat drei wiederkehrende Formen:

1. **Der wohlmeinende Skip.** `|| exit 0`, wenn ein Werkzeug fehlt. Lokal
   nachvollziehbar, in CI strukturell — und damit dauerhaft.
2. **Der verschluckte Fehler.** `|| true`, `continue-on-error`, ein `if: always()`
   nach einem gescheiterten Schritt.
3. **Der leere Erfolg.** Kein Input, kein Testfall, kein Treffer — und das
   Werkzeug beendet sich mit 0.

---

## 2. Regeln für Gates

**MUSS**: Jedes Gate MUSS fehlschlagen können. Ein Gate, dessen Fehlermodus
„grün" ist, gilt als Defekt, nicht als Konfiguration.

**MUSS**: Ein Gate, das seinen Prüfgegenstand nicht vorfindet — keine Datei, kein
Testfall, kein Template, ein leeres Verzeichnis — MUSS fehlschlagen. Ein leerer
Input ist kein bestandener Test.

**MUSS**: `|| true`, `continue-on-error: true` und gleichwertige Konstruktionen
sind in einem Gate verboten. Zulässig bleiben sie ausschließlich für
Diagnose-Schritte, die den Prüfgegenstand nicht berühren (Log-Ausgabe,
Aufräumarbeiten) — erkennbar daran, dass ihr Fehlschlag die Aussage des Jobs
nicht verändert.

**MUSS**: Wenn ein Gate in CI übersprungen wird, weil sein Werkzeug dort
strukturell nicht verfügbar ist, dann MUSS der Skip
1. angekündigt werden (sichtbare Ausgabe, nicht stilles Exit 0),
2. einen **namentlich benannten Backstop** nennen, der dieselbe Fläche abdeckt, und
3. die Bedingung nennen, unter der der Skip ungültig wird.

  Der Backstop MUSS existieren. Vor diesem Dokument nannte der `nuclei-validate`-Hook
  „den CI-Workflow" als autoritatives Gate — dieses Gate gab es nicht.
  `scripts/frontend_hook.sh` ist die Referenzimplementierung dieser Regel.

**MUSS**: Ein Job, dessen Schritte sämtlich übersprungen wurden, MUSS als
Fehlschlag gelten, wenn er ein required Check ist. Praktisch heißt das: Die
Bedingung, die Schritte überspringt, MUSS den Ausfall der Vorbedingung
mitbehandeln — in GitHub Actions über `needs.<job>.result != 'success'`, nicht
nur über dessen Outputs. Ein leerer Output einer fehlgeschlagenen Abhängigkeit
lässt jeden Vergleich falsch werden und macht das Gate lautlos grün.

**SOLL**: Die Prüfung, ob eine Prüfung wirkt, gehört zur Prüfung. Wo praktikabel,
MUSS ein Gate eine Negativkontrolle haben — ein Fall, in dem es nachweislich rot
wird. Für Skripte heißt das ein Test, für Workflows eine bewusst kaputte
Eingabe während der Entwicklung.

### 2.1 Ratchet-Baselines werden berechnet, nicht versioniert

**MUSS**: Eine Ratchet-Baseline — die Zahl, gegen die ein „no-growth"-Gate den
Ist-Zustand vergleicht — MUSS aus dem Ist-Zustand berechnet werden und DARF NICHT
als versionierte Konstante gepflegt werden.

Der Grund ist mechanisch. Eine eingecheckte Baseline verwandelt jedes
Aufräumen in einen Merge-Konflikt: Wer einen Verstoß beseitigt, muss die
Konstante senken, und zwei parallele Pull Requests, die beide aufräumen,
kollidieren an genau dieser Zeile. Der Effekt ist eine Prämie aufs Nichtstun.
Schlimmer ist der zweite Effekt — eine gesenkte Konstante macht **fremde**,
bereits geöffnete Pull Requests rot, ohne dass sich an ihnen etwas geändert
hätte. Das ist die Fehlerklasse aus §1, eine Ebene höher: Das Gate meldet einen
Defekt, den es selbst erzeugt hat.

Die geltende Bauform:

- Die Obergrenze wird zur Laufzeit aus dem Repository ermittelt (Zählung über
  denselben Scan, den das Gate ohnehin ausführt).
- **Rot nur bei Wachstum.** Ein Rückgang ist grün und wird als gewonnener
  Spielraum ausgegeben, nie als Fehler.
- Die Zahl kommt aus dem Prüf-Target selbst, nicht aus einer Datei, die man
  bearbeiten könnte. `task check:schema-examples` (`scripts/check_schema_examples.py`,
  #850/#973) ist die Referenzimplementierung; `scripts/check_utc_calendar_day.py`
  ist der Grenzfall am anderen Ende: eine Fläche ohne Altbestand bekommt gar
  keine Baseline, sondern die harte Null.

Hergeleitet aus #973. Die Lektion stand bis dahin nur als Kommentar im
`Taskfile.yaml` — also genau dort, wo sie niemand liest, der ein neues Gate baut.

### 2.2 Eine überwiegend abgebrochene Lane existiert nicht

**MUSS**: Für jede gatende **oder** berichtende Lane MUSS die Abbruchrate
beobachtet werden. Eine Lane, deren Läufe überwiegend als `cancelled` enden,
meldet nichts und ist wie eine **nicht existierende Lane** zu behandeln — sie
darf weder in einer DoD noch in einem Audit als vorhandene Abdeckung gezählt
werden.

**MUSS**: Das Mittel ist die **Umplatzierung des Triggers**, nicht
`cancel-in-progress: false`. Ein Lauf, der nie verdrängt wird, scannt jeden
Zwischenstand einer Commit-Serie in voller Laufzeit und verliert am Ende trotzdem
gegen den Merge seines eigenen Pull Requests; ein engerer `paths:`-Filter
bestimmt, wie **oft** die Lane startet, nicht, ob ein gestarteter Lauf sein
Urteil erreicht. Die Variable ist die Laufzeit im Verhältnis zum Merge-Takt —
unter `strict: true` plus `automerge` verliert jeder Job, der länger braucht als
die required Checks.

**Messgröße.** Die Rate wird über ein benanntes Fenster jüngster Läufe erhoben
(`gh run list --workflow <name> --json conclusion`), zusammen mit einer
Vergleichs-Lane ähnlicher Laufzeit im selben Merge-Train. Ohne diesen Vergleich
lässt sich nicht unterscheiden, ob die Concurrency-Form oder die Dauer das
Problem ist.

Diese Regel ist die Verallgemeinerung der Analyse in **NFR-014 §4.1**, die für
die Nuclei-Lane 85 % abgebrochene Läufe gemessen und den Trigger auf
`push`-nach-Merge verschoben hat (#993). #1013 ist dieselbe Form an der
ZAP-Lane (44 %) — der Beleg dafür, dass die Erkenntnis pro Lane angewandt statt
als Regel gehoben worden war. Eine bewusste Verringerung der Abdeckung durch
Umplatzierung ist nach §4 zu benennen, nicht als Reparatur auszugeben.

---

## 3. Reproduzierbarkeit der Werkzeugkette

**MUSS**: Die Werkzeugkette wird **vollständig** gepinnt, nicht teilweise. Ein
halb gepinnter Toolchain ist nicht gepinnt.

> **Beleg.** `backend.yml` pinnte `pip-tools==7.5.3` unter einem ausführlichen
> Reproduzierbarkeits-Kommentar — und rief eine Zeile darüber
> `pip install --upgrade pip` ohne Pin auf. Am 2026-07-29 entfernte pip 26.2
> `pip._internal.utils.compat.stdlib_pkgs`, das pip-tools importiert.
> `pip-compile` starb daraufhin mit einem `ImportError`, bevor es Arbeit
> verrichtete, und das Lockfile-Gate war für jeden Backend-PR rot — ohne dass
> sich am Repository etwas geändert hätte. Die ungepinnte Hälfte zerbrach die
> gepinnte.

**MUSS**: Jede externe Referenz wird unveränderlich gepinnt: Third-Party-Actions
per Full-Length-Commit-Digest mit Versionskommentar, Reusable Workflows per
unveränderlicher Referenz, Container-Basis-Images per Digest, Abhängigkeiten per
committetem Lockfile.

**MUSS**: Ein Tag gilt **nicht** als unveränderlich, auch nicht bei einem
vertrauenswürdigen Herausgeber. Der `tj-actions/changed-files`-Vorfall vom
März 2025 verschob bestehende Tags auf bösartigen Code; digest-gepinnte
Konsumenten waren nicht betroffen.

**MUSS**: Jeder inline gepinnte Wert MUSS von der Update-Automatisierung erfasst
sein. Ein veralteter Pin und eine bewegliche Referenz verfehlen dasselbe
Reproduzierbarkeitsziel aus entgegengesetzten Richtungen; ohne Renovate-Anbindung
tauscht ein Pin nur das eine Problem gegen das andere.

**SOLL**: Ein Cache ist ein Beschleuniger. Ein Lauf mit kaltem und einer mit
warmem Cache MÜSSEN auf demselben Commit zum selben Urteil kommen. Build-Outputs
und Testergebnisse werden nicht gecacht — sie sind die Aussage der Pipeline über
den Commit.

---

## 4. Required Checks und advisory Checks

**MUSS**: Ein Check ist entweder required — dann blockiert er — oder advisory —
dann blockiert er nicht. Ein required Check, der nicht fehlschlagen kann, ist die
schlechteste der drei Möglichkeiten.

**MUSS**: Die Dokumentation MUSS beschreiben, was tatsächlich gilt. Steht in
`CLAUDE.md` oder einer NFR, ein Befund blockiere den Merge, dann MUSS der
zugehörige Kontext in `.github/settings.yml` required sein — oder die Aussage
wird korrigiert. Geprüft wird am Live-Zustand:

```bash
gh api repos/nolte/kamerplanter/branches/develop/protection \
  --jq '.required_status_checks.contexts'
```

**MUSS**: Die Promotion eines Checks zu required wird an **gemessener Historie**
begründet, nicht an Meinung: Anzahl der Läufe, Anzahl der Fehlschläge, und für
jeden Fehlschlag die Zuordnung zu einem echten Defekt oder zu Flakiness. Ein
flakiger required Check blockiert jeden PR im Repository und ist ein schlechterer
Fehlermodus als die Lücke, die er schließen soll. Die Kommentare in
`.github/settings.yml` sind die Referenz für diese Begründungsform.

**MUSS NICHT**: Ein langsamer Check wird nicht dadurch repariert, dass man ihn
aus dem required-Set entfernt und die Doku unverändert lässt. Entweder wird die
Abdeckung nachweislich anderswo erbracht — dann ist das zu benennen — oder die
Reduktion ist eine bewusste, dokumentierte Verringerung der Abdeckung.

---

## 5. Auslieferungsgarantien

**MUSS**: Jedes veröffentlichte Artefakt trägt von der Plattform erzeugte,
signierte Build-Provenance (`actions/attest-build-provenance`). Erzeugt wird sie
**von der Plattform**, nicht von einem Schritt innerhalb des attestierten Builds:
Ein Build, der sich selbst attestiert, kann seine eigene Kompromittierung nicht
erkennen.

**MUSS**: Provenance belegt **Herkunft**, nicht Sicherheit. Ein attestiertes
Artefakt ist eines, dessen Bauweg bekannt ist — nicht eines, das als sicher
beurteilt wurde. Diese Unterscheidung MUSS überall dort stehen, wo Provenance
gegenüber Nutzern erwähnt wird.

**MUSS**: Für jede ausgelieferte Artefaktklasse existiert eine benannte Stage,
die sie absichert, mit mindestens einer benannten Garantie
(`built-from-source`, `integrity`, `provenance`, `policy-cleared`). Die Zuordnung
MUSS lesbar sein, ohne sie aus Workflow-Dateien zu rekonstruieren — sie steht in
`docs/<lang>/deployment/ci-cd.md`. Eine Artefaktklasse ohne sichernde Stage ist
ein Defekt im Pipeline-Entwurf, keine akzeptable Auslassung. Bekannte Lücken
MÜSSEN als solche verzeichnet sein.

**MUSS**: Eine veröffentlichte Versionsreferenz löst dauerhaft auf dieselben
Bytes auf. `latest` erfüllt das nicht und darf von keinem Deployment konsumiert
werden. Deployments pinnen einen Versions-Tag oder einen Digest.

**MUSS**: Eine Ersetzung, von der die Unveränderlichkeit eines Artefakts abhängt,
MUSS **verifiziert** werden. Ein `sed`, das still nichts tut, wenn sich der
Default ändert, ist keine Garantie. Die Pinning-Schritte in `docker-publish.yml`
adressieren die Images über ihren YAML-Pfad und prüfen anschließend nach, dass
kein Image der Ersetzung entkommen ist.

**MUSS NICHT**: Rollback wird nicht als Neubau eines älteren Commits definiert.
Ein Neubau löst Eingaben zur Bauzeit auf und erzeugt damit ein anderes Artefakt
als das bekannt gute.

---

## 6. Supply-Chain-Gates

**MUSS**: Beide Ökosysteme werden gleich behandelt. NFR-009 §4.1 und §4.3
forderten CVE- und Lizenz-Prüfung für Frontend **und** Backend; implementiert war
über lange Zeit nur das Backend, und Trivy erreichte `package-lock.json` nur auf
Stufe `CRITICAL`. Eine High-Severity-Advisory in ausgelieferter JavaScript-Ware
war dadurch für jedes Gate im Repository unsichtbar — und eine lag vor.

**MUSS**: Eine bewusst akzeptierte Advisory wird als Eintrag mit **Begründung und
Ablaufdatum** geführt, nicht durch Absenken der Schwelle. Die Begründung MUSS
einen Mechanismus nennen, warum der verwundbare Codepfad in dieser Anwendung
nicht existiert; „nicht ausnutzbar" ohne Mechanismus ist keine Begründung.

**MUSS**: Das Ablaufdatum ist verpflichtend. Ein Eintrag, der nie verfällt, ist
keine Entscheidung mehr, sondern Inventar — und eine veraltete Unterdrückung ist
von einer unbemerkten Schwachstelle nicht zu unterscheiden.

**SOLL**: Das Gate warnt über Einträge, die auf keine aktuelle Advisory mehr
passen, damit eine behobene Abhängigkeit keine Unterdrückung zurücklässt.

---

## 7. Definition of Done

- [ ] **Gate-Integrität**
    - [ ] Kein Gate im Repository enthält `|| true` oder `continue-on-error` auf einem Schritt, der seinen Prüfgegenstand berührt
    - [ ] Jedes Gate schlägt bei leerem Prüfgegenstand fehl
    - [ ] Jeder CI-Skip ist angekündigt und nennt einen **existierenden** Backstop
    - [ ] Jeder required Check behandelt den Ausfall seiner Vorbedingungen (`needs.<job>.result`)
- [ ] **Reproduzierbarkeit**
    - [ ] Keine bewegliche Referenz in `.github/workflows/` — weder Action-Tag noch Branch noch unbeschränkte Toolversion
    - [ ] Jeder inline gepinnte Wert ist von Renovate erfasst
    - [ ] Die Werkzeugkette ist vollständig gepinnt, inklusive der Installer selbst (`pip`, `npm`)
- [ ] **Required Checks**
    - [ ] `gh api …/branches/develop/protection` deckt sich mit dem, was CLAUDE.md und die NFRs behaupten
    - [ ] Für jeden required Check existiert eine gemessene Begründung
- [ ] **Auslieferung**
    - [ ] Jedes Image und der Helm-Chart tragen signierte Provenance
    - [ ] Die Artefakt-zu-Stage-Matrix ist in `docs/<lang>/deployment/ci-cd.md` gepflegt, inklusive bekannter Lücken
    - [ ] Kein Deployment konsumiert `latest`
    - [ ] Jede unveränderlichkeitsrelevante Ersetzung wird verifiziert
- [ ] **Supply Chain**
    - [ ] CVE- und Lizenz-Gates existieren für beide Ökosysteme
    - [ ] Jede akzeptierte Advisory hat Begründung und Ablaufdatum

---

## 8. Offene Punkte

- Die Regel „kalter und warmer Cache liefern dasselbe Urteil" ist als Invariante
  formuliert, aber durch nichts verifiziert. Ob ein periodischer cache-freier
  Lauf die Kosten wert ist, ist offen.
- `nolte/gh-plumbing` liefert die Reusables, die den einzigen required Check
  tragen. Sie referenzierten intern `aquasecurity/trivy-action@master` sowie
  `hassfest@master` und `vale-action@reviewdog` — drei bewegliche Branches — und
  im Übrigen Tags statt Digests.

  **Upstream behoben** am 2026-08-01 (`nolte/gh-plumbing#389`, Issue #388):
  alle 30 Workflow-Dateien dort sind digest-gepinnt, verifiziert am Inhalt und
  nicht nur an der Commit-Meldung; keine bewegliche Referenz verbleibt.

  **Hier noch nicht wirksam.** Dieses Repository pinnt `v1.1.26`, und *diese*
  Fassung enthält weiterhin die ungepinnten Reusables. `v1.1.27` ist ein Draft,
  der Tag existiert noch nicht als Git-Ref. Bis der Bump erfolgt, ist §3 für
  diese Kette weiterhin nur auf der Consumer-Seite erfüllt — die Lücke ist
  gelöst, aber nicht geschlossen. Prüfen mit:

  ```bash
  gh api "repos/nolte/gh-plumbing/contents/.github/workflows/reusable-trivy.yaml?ref=v1.1.27" \
    --jq '.content' | base64 -d | grep 'trivy-action'
  ```
- Ein Linter, der die DoD dieses Dokuments maschinell prüft, existiert nicht.
  Derzeit trägt die Prüfung ein Audit, kein Gate — was auf ein Dokument über
  Gate-Integrität eine unangenehme, aber ehrliche Pointe ist.
