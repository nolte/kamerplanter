---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "1751"
classification: "bug"
secondary-classes: ["infra"]
route: "direct"
status: approved
created: "2026-09-25"
---

# Issue Orchestration — Pre-analysis #1751

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #1751 — knowledge-service: long-chunk reranks exceed the 25 s deadline and silently fall back to unranked results
- **URL**: https://github.com/nolte/kamerplanter/issues/1751
- **Labels**: backend
- **Linked items**: #1725, #1739 (Deadline eingeführt); parallel PR #1765 (Golden-Outputs des Sidecars bei 512-Token-Fenster — Sidecar deshalb unverändert)
- **Prior art checked**: keine offene PR zu #1751; `reranker_fallback`-Warnung existierte bereits (ohne Grund-Feld)
- **Autor**: nolte (Repo-Owner, trusted)

## Classification

- **Primary class**: bug
- **Secondary class(es)**: infra
- **Rationale**: Reranking ist im deployten Profil funktional tot (Deadline feuert immer), plus Latenzstrafe von ~27 s je Suche.
- **Asserted cause verified**:
  - Behauptung „Typical chunks are much shorter" (Issue + `docker/reranker-service/limits.py`) — **refuted**: Korpus 432 Chunks, `title\ncontent` Median 430 Tokens (bge-Tokenizer), p90 630, max 995, 115/432 > 512; bei realer Retrieval (100 Benchmark-Fragen, Hybrid-Top-20) erreichen 44 % der Paare die 512-Kappung, Paar-Median 488.
  - „Wie oft, nicht ob" — **refuted in Richtung schlimmer**: 10/10 reale HTTP-Probes gegen lokal gebautes Image (`--cpus 2 -m 4g`, Deadline 25 s) → 503 `timeout` nach 25,6–28,6 s; Vorhersage aus Kalibrierung 54/54 Fragen.
  - „silently" — **teilweise refuted**: `reranker_fallback`-Warnung existierte, aber ohne maschinenlesbaren Grund (deadline/busy/timeout nicht unterscheidbar); zusätzlich warf ein fehlerhafter 2xx-Body durch (500) statt zu degradieren.
  - „truncates to 512 — so why 50 s?" — **established**: Zeit ist reine Modell-Rechenzeit (XLM-R-large, 24 Layer, FP32): 0,23 s @64, 1,31 s @256, 2,26 s @384, 3,04 s @512 Tokens je Paar bei 2 CPUs; Tokenisierung ~2 ms/Paar. Die 512-Kappung greift, bindet aber nicht, weil die Chunks ohnehin ~450–512 Tokens haben.

## Scope

- **In scope**: Budget so wählen, dass der Rerank innerhalb der Deadline läuft; Fallback beobachtbar machen (strukturierter Grund); Doku; widerlegte Kommentar-Behauptung korrigieren.
- **Out of scope**: Sidecar-Tokenfenster (PR #1765 pinnt Goldens bei 512); Prometheus-Metriken (kein Service im Repo exportiert welche; NFR-007 §4.7.6 `knowledge_service_errors_total` ist eine eigene Lücke).

## Entscheidung (Operator-autorisiert, gemessen)

Optionen gegen 54 Fragen (9 Kategorien) bewertet; Qualitätsmaß = Anteil der `expected_topics` im Top-5-Kontext (Scorer `tools/rag-eval/eval_rag.topic_matches`):

| Konfiguration | Recall | Rerank p50 / max (Vorhersage) | Deadline-Feuer |
|---|---|---|---|
| Fallback (heute effektiv) | 0,927 | 0 s (+~27 s Wartezeit heute) | – |
| 512 Tok, k=20 (heute konfiguriert) | 0,927 | 53,9 / 59,9 s | 54/54 |
| 512 Tok, k=20 ohne Deadline (Referenz) | 0,982 | 53,9 / 59,9 s | – |
| 512 Tok, k=8 | 0,962 | 21,8 / 24,3 s | 0/54 (keine Marge) |
| 800 Zeichen, k=10 (erste Wahl, verworfen) | 0,969 | 13,3 / 15,7 s (HTTP gemessen p50 15,7 / max 24,4 s) | 0/54 |
| 600 Zeichen, k=15 | 0,978 | 14,6 / 16,6 s | 0/54 |
| 500 Zeichen, k=20 | 0,978 | 15,5 / 18,4 s | 0/54 |
| **500 Zeichen, k=15 (gewählt)** | **0,974** (top_k=10: 0,979) | **11,7 / 13,9 s; HTTP gemessen 100/100 → p50 12,9 / p90 15,0 / max 16,0 s** | **0/100** |
| 800 Zeichen, k=12 | 0,969 | 16,0 / 18,8 s | 0/54 |
| 800 Zeichen, k=15 | 0,974 | 19,9 / 23,2 s | 0/54 |

- Timeouts anheben: verworfen — Backend-Adapter `ai_knowledge_service_timeout_s = 60.0` (`src/backend/app/config/settings.py:419`); 55 s Rerank + LLM überschreiten das.
- Fallback akzeptieren: verworfen — kostet heute ~27 s je Suche ohne Nutzen.
- Kürzung clientseitig (Knowledge-Service), nicht im Sidecar: Sidecar-Vertrag/Goldens (#1765) bleiben unberührt.

## Work packages

### P1 — Rerank-Budget (k=15, 500 Zeichen) + Head/Tail-Semantik + Budget-Guard
- **Acceptance**: Settings-Defaults 10/800; gesendete Dokumente gekürzt, zurückgegebene Chunks voll; Helm-Wert 10 + neue Env-Var; Tests red-first.
- **Files**: `src/knowledge-service/app/{config,reranker,main}.py`, tests, `helm/kamerplanter/values-dev-ki.yaml`, Kommentar `docker/reranker-service/limits.py`
- **Specialist**: fullstack-developer (project agent)
- **Depends on**: P2

### P2 — Beobachtbarer Fallback
- **Acceptance**: genau ein `reranker_fallback` mit `reason` ∈ geschlossener Menge, `status_code`, `documents`, `elapsed_s`; kaputter 2xx degradiert statt 500; red-first.
- **Specialist**: fullstack-developer (project agent)

### P3 — Doku DE/EN
- **Specialist**: mkdocs-documentation (project agent)
- **Depends on**: P1, P2 (Zielzustand vorgegeben)

## Dependency ordering

P2 → P1 ; P3 parallel zu P1 (nur docs/).

## Class sweep / Guard-Entscheidung

Guard (G1/G3/G6): `RERANK_SCORED_CHARS_BUDGET = 7500` in config.py; `TestTheRerankBudgetHolds` prüft Defaults und JEDE YAML/env-Datei im Repo, die eine der Variablen setzt, und meldet unlesbare Schreibweisen rot. Ein exakter Zeit-Guard „k × Paarkosten ≤ Deadline" ist nicht möglich: Paarkosten hängen an der Tokenzahl, und die ist ohne Tokenizer (nicht in Backend-/Knowledge-Service-Umgebung) nicht aus Zeichen ableitbar; ein 2000-Zeichen-Query kappt jedes Paar auf 512 → 10 × 3,04 s > 25 s. Der Laufzeit-Beleg ist das `reason=deadline`-Feld (P2). Geschwister-Instanz Embedding-Ingest (16 Texte/Request, Deadline 110 s): siehe Dispatch-Log.

## Dispatch log

- 2026-09-25 P2 → fullstack-developer — Hypothese bestätigt (kein `reason`-Feld); zusätzlich: kaputter 2xx warf durch, negativer Index lief still durch. 7 Gründe, red-first 22 failed → grün.
- 2026-09-25 P1 → fullstack-developer — 10/800 umgesetzt; offener Punkt top_k>initial_k (Regression für MCP/`/search`) → Head/Tail-Invariante nachbeauftragt; danach Retune auf 15/500 + Budget-Guard (5 provozierte Überschreitungen rot).
- 2026-09-25 P3 → mkdocs-documentation — 8 Dateien DE/EN, ADR-007 nur datierter Nachtrag; `task docs:build` strict grün.
- Geschwister-Instanz Embedding-Ingest: 16 längste Chunks an e5-large (aktuelles Image, `--cpus 2`) 57–59 s (Last ~5) bzw. 72 s (Last 16) < Deadline 110 s / Client 120 s — passt, Marge ~1,9×. Der Kommentar in `docker/embedding-service/main.py` nennt 24,7 s für 16 Texte >512 Tokens; nicht reproduziert (unestablished, abweichende Last/Texte möglich).
- RAG-Eval-Smoke (LLM) nicht lauffähig: Ollama `192.168.178.130:31434` nicht erreichbar → Ersatzmaß: Benchmark-Scorer `topic_matches` auf den Retrieval-Kontext (54 Fragen, 9 Kategorien).
