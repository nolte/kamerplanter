# Issue #1735 — Voranalyse

- **Issue:** #1735 „HF-pin guard accepts a self-referential sha256 checklist and does not pair kept files with hash lines" (Autor: nolte, trusted)
- **Klasse:** `bug` (sekundär `security`) — die Wache prüft weniger, als sie behauptet; kein Live-Defekt im Baum.
- **Requirements-Gate:** Operator-Override (Repository-Owner, 2026-09-24, volle Autonomie). Die Akzeptanzkriterien im Issue sind maschinell prüfbar und reichen als Anforderung.
- **Route:** direkt (ein Ergebnis, ein PR-Strang, kein Roadmap-Item).

## Nachgemessene Ursache (established)

- `_fetch_is_verified` (test_hf_model_fetches_pin_a_revision.py:318–370) akzeptiert jeden `sha256sum -c`, der die Shell-Modell-Bedingungen erfüllt; woher die Checkliste stammt, wird nicht gelesen → Befund 1 bestätigt.
- Keine Stelle vergleicht die per `mv` in `/model` gelegten Pfade mit den Hash-Zeilen → Befund 2 bestätigt.
- Alle sechs Download-Stages (docker/embedding-service: 4, docker/reranker-service: 2) haben die Form `mkdir /model && mv … /model/ && printf '%s\n' '<hex>  /model/<f>' … > /tmp/model.sha256 && sha256sum -c --strict …` — gelesen, nicht vermutet.

## Arbeitspakete

| ID | Problem | AK | Dateien | Spezialist |
|----|---------|----|---------|-----------|
| WP-1 | Regel A: Checkliste nur aus 64-hex-Literalen im selben RUN | selbstreferenzielle Checkliste rot, printf/echo/cat-heredoc grün, Selbsttest je Schreibweise | guards/test_hf_model_fetches_pin_a_revision.py | generalist (kein Spezialist besitzt Guard-Scanner-Logik) |
| WP-2 | Regel B: Mengengleichheit kept ↔ Hash-Zeilen | fehlende/überzählige Zeile rot, beide Richtungen, Selbsttest je Schreibweise | dito | generalist |
| WP-3 | Baum-Sweep | alle Dockerfiles grün, Guard-Lane grün | — | generalist |

Abhängigkeit: WP-1 → WP-2 → WP-3.
