# E2E-Tests

End-to-End-Tests (E2E) prüfen **komplette Nutzer-Workflows im echten Browser** — vom Klick über Frontend und Backend bis in die Datenbank. Sie stehen an der Spitze der [Testpyramide](index.md): am wenigsten zahlreich, am langsamsten, aber am realistischsten. E2E-Tests nutzen Selenium WebDriver mit dem Page-Object-Pattern und erzeugen Markdown-Testprotokolle mit Screenshots (interne Referenz: NFR-008). <!-- NFR-008 -->

## Was diese Stufe prüft

- **Durchgängige Abläufe:** z. B. Login → Datensatz anlegen → speichern → wiederfinden, quer durch alle Schichten.
- **Reales Zusammenspiel:** echter Browser, echtes Frontend (nginx), echtes Backend, echte Datenbank.

## Getestete Bereiche im Überblick

E2E-Suiten sind nach Anforderung (REQ) organisiert. Thematisch gebündelt:

| Bereich | Beispiel-Workflows | Umfang |
|---------|--------------------|--------|
| Stammdaten & Lebenszyklus | Arten/Sorten, Phasensteuerung, Pflanzdurchlauf | umfangreich |
| Bewässerung & Düngung | Nährlösung, Feeding, Tankmanagement | mittel |
| Aufgaben & Pflege | Task-Queue, Pflege-Dashboard, Erinnerungen | mittel |
| Ernte & Nachernte | Erntereife, Ernteliste, Post-Harvest | mittel |
| Pflanzenschutz | Schädlinge/Krankheiten, Foto-Erkennung, Diagnose | mittel |
| Plattform | Anmeldung, Mandanten, Datenschutz, Light-Modus | umfangreich |
| Weitere | Dashboard, Kalender, Onboarding, Mischkultur, Notifications, KI-Assistent, Druckansichten | mittel |

!!! note "Kuratierte Testfall-Spezifikationen"
    Detaillierte, nummerierte Testfälle liegen als Markdown-Dokumente unter `spec/e2e-testcases/` (`TC-REQ-*`, `TC-NFR-*`) samt `COVERAGE-REPORT.md`. Sie beschreiben je Anforderung Vorbedingungen, Schritte und erwartete Ergebnisse.

## Werkzeug & Ort

| | Wert |
|---|---|
| Werkzeug | Selenium WebDriver, pytest, Page-Object-Pattern |
| Ort | `tests/e2e/` |
| Locator | `data-testid`-Attribute (nie CSS-Struktur) |

!!! info "CI: Smoke-Gate pro PR + Nightly-Volllauf"
    Die Suite läuft auch in GitHub Actions — mit demselben Docker-Compose-Stack wie lokal: Der Workflow `e2e-smoke` führt das schnelle Smoke-Profil bei jedem Pull Request und bei Pushes nach `develop` aus. Er ist seit ADR-011 ein **Pflicht-Check** auf `develop` — neben `static / Static CI Tests`. Ob die Suite tatsächlich läuft, entscheidet ein Job im Workflow selbst und nicht ein Pfadfilter am Trigger: Ein per Pfadfilter übersprungener Pflicht-Workflow meldet nie ein Ergebnis und blockiert den Pull Request dauerhaft. Der Workflow `e2e-nightly` fährt nächtlich die vollständige Suite als Matrix über die Compose-Profile `light`, `full`, `mobile`, `tablet` und `full-mobile`; ein roter Lauf legt **kein** GitHub-Issue mehr an — Lauf-Status, gerenderter Check-Run je Profil und die Artifacts enthalten alles, was das automatische Issue nur wiederholt hat. Testprotokoll, Screenshots und Container-Logs hängen als Workflow-Artifacts an jedem Lauf.

## CI-Testberichte

Jeder Testlauf schreibt zusätzlich zu Protokoll und Screenshots einen JUnit-XML-Report (`junit-<profil>.xml`), der die TC-ID jedes Testfalls als `tc_id`-Property mitführt. In GitHub Actions rendert der Workflow `e2e-smoke` (pro Pull Request) sowie jedes Profil im `e2e-nightly`-Workflow diesen Report zusätzlich per `dorny/test-reporter` als GitHub-Check-Run und als Tabelle in der Job-Summary — mit der konkreten Fehlermeldung (Assertion-Text plus kurzer Traceback) je fehlgeschlagenem Test, statt nur einem grünen/roten Gesamtstatus.

!!! note "Fork-Pull-Requests: kein gerenderter Check"
    Bei Pull Requests aus Forks kann der Render-Schritt mit dem eingeschränkten `GITHUB_TOKEN` keinen Check-Run anlegen und wird übersprungen (`continue-on-error`). `e2e-smoke` erkennt das und schreibt in diesem Fall die Ergebnisübersicht samt fehlgeschlagener Tests aus dem Testprotokoll in die Job-Summary — sonst steht die Job-Summary nur als Zeiger auf das Artifact, damit dieselben Zahlen nicht doppelt erscheinen. Das `junit-*.xml`-Artifact gibt es in beiden Fällen.

Der gerenderte Check-Run ist eine CI-Ergänzung — er ersetzt nicht das Markdown-Testprotokoll (`protokoll.md`) mit den eingebetteten Screenshots, das weiterhin das menschenlesbare Nachweisdokument bleibt (NFR-008 §4.4).

## Ausführen

```bash
# Lokal gegen laufende App (Chrome headless, localhost:5173)
pytest tests/e2e/ -v

# Dedizierter, isolierter Docker-Stack (App + Selenium Grid)
./scripts/run-e2e.sh                    # volle light-Suite
./scripts/run-e2e.sh --smoke            # Smoke-Suite (~7 min)
./scripts/run-e2e.sh --profile mobile   # ein einzelnes Compose-Profil
```

Reports und Screenshots landen unter `test-reports/e2e/<timestamp>/`, darunter auch der JUnit-XML-Report — siehe [CI-Testberichte](#ci-testberichte). Der vollständige Stack, die Fixtures und das Protokoll-Format stehen im [Testkonzept → E2E-Tests](../index.md#e2e-tests-selenium).

## Konventionen

- Jedes Page Object erbt von `BasePage` und kapselt genau einen Bildschirm.
- Elemente ausschließlich über `data-testid`-Locator ansprechen — nie über brüchige CSS-Pfade.
- Screenshots an fachlichen Checkpoints explizit aufnehmen; bei Fehlern werden sie automatisch erfasst.
