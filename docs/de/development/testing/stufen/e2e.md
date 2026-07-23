# E2E-Tests

End-to-End-Tests (E2E) prüfen **komplette Nutzer-Workflows im echten Browser** — vom Klick über Frontend und Backend bis in die Datenbank. Sie stehen an der Spitze der [Testpyramide](index.md): am wenigsten zahlreich, am langsamsten, aber am realistischsten. E2E-Tests nutzen Selenium WebDriver mit dem Page-Object-Pattern und erzeugen Markdown-Testprotokolle mit Screenshots (interne Referenz: NFR-008). <!-- NFR-008 -->

## Was diese Stufe prüft

- **Durchgängige Abläufe:** z. B. Login → Datensatz anlegen → speichern → wiederfinden, quer durch alle Schichten.
- **Reales Zusammenspiel:** echter Browser, echtes Frontend (nginx), echtes Backend, echte Datenbank.

## Werkzeug & Ort

| | Wert |
|---|---|
| Werkzeug | Selenium WebDriver, pytest, Page-Object-Pattern |
| Ort | `tests/e2e/` |
| Locator | `data-testid`-Attribute (nie CSS-Struktur) |

!!! info "Kein CI-Job — bewusst lokal / auf Abruf"
    Die E2E-Suite läuft **nicht** automatisch in der CI-Pipeline, sondern lokal bzw. auf Abruf über einen dedizierten Docker-Compose-Stack. Das ist eine bewusste Entscheidung (Laufzeit, Browser-Infrastruktur), keine Lücke.

## Ausführen

```bash
# Lokal gegen laufende App (Chrome headless, localhost:5173)
pytest tests/e2e/ -v

# Dedizierter, isolierter Docker-Stack (App + Selenium Grid)
./scripts/run-e2e.sh
```

Reports und Screenshots landen unter `test-reports/<timestamp>/`. Der vollständige Stack, die Fixtures und das Protokoll-Format stehen im [Testkonzept → E2E-Tests](../index.md#e2e-tests-selenium).

## Konventionen

- Jedes Page Object erbt von `BasePage` und kapselt genau einen Bildschirm.
- Elemente ausschließlich über `data-testid`-Locator ansprechen — nie über brüchige CSS-Pfade.
- Screenshots an fachlichen Checkpoints explizit aufnehmen; bei Fehlern werden sie automatisch erfasst.
