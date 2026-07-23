# Teststufen

Kamerplanter organisiert seine automatisierten Tests in vier **Teststufen**. Jede Stufe hat einen eigenen Fokus, ein eigenes Werkzeug und eine eigene Laufzeit-Charakteristik. Zusammen bilden sie eine **Testpyramide**: je tiefer die Stufe, desto mehr Tests laufen und desto schneller sind sie; je höher, desto weniger Tests und desto realistischer das Szenario.

| Stufe | Fokus | Werkzeug | Ort | Läuft in CI |
|-------|-------|----------|-----|-------------|
| [Unit](unit.md) | Einzelne Funktionen/Klassen isoliert | pytest / vitest | `src/backend/tests/unit/`, `src/frontend/src/test/{store,hooks}/` | Ja |
| [Integration](integration.md) | Zusammenspiel mit echter Datenbank/API | pytest | `src/backend/tests/integration/`, `…/api/` | Ja (DB-abhängig übersprungen) |
| [Component](component.md) | React-Komponenten im gerenderten DOM | vitest + Testing Library | `src/frontend/src/test/components/` | Ja |
| [E2E](e2e.md) | Komplette Nutzer-Workflows im echten Browser | Selenium | `tests/e2e/` | Nein (lokal / auf Abruf) |

!!! tip "Praktische Anleitung"
    Wie du die jeweilige Suite installierst und ausführst, steht ausführlich im [Testkonzept](../index.md) — dort ist alles nach **Werkzeug** gegliedert. Auf diesen Seiten beschreiben wir *was* jede Stufe abdeckt und *warum*.

## Die Pyramide

- **Basis — Unit:** Viele, sehr schnelle Tests ohne externe Abhängigkeiten. Sie prüfen die Fachlogik (VPD-, GDD-, EC-Berechnungen, Reducer, Hooks) in Isolation und geben in Sekunden Rückmeldung.
- **Mitte — Integration & Component:** Weniger Tests, die echtes Zusammenspiel prüfen — auf dem Backend gegen eine laufende ArangoDB, im Frontend gegen den gerenderten DOM mit gemockter API (MSW).
- **Spitze — E2E:** Wenige, langsame Tests, die einen kompletten Nutzer-Workflow durch echten Browser, Frontend, Backend und Datenbank fahren.

## Wann welche Stufe?

- **Neue Fachlogik** (Berechnung, Engine, Service) → mindestens ein **Unit-Test**.
- **Neuer Repository-/DB-Zugriff oder API-Endpunkt** → ein **Integrationstest**.
- **Neue oder geänderte React-Komponente** → ein **Component-Test**.
- **Neuer durchgängiger Workflow** (z. B. Login → Anlegen → Speichern) → ein **E2E-Test**.

Faustregel: Schreibe den Test auf der **niedrigsten** Stufe, die den Fehler noch zuverlässig fängt. Das hält die Suite schnell und die Fehlermeldungen präzise.
