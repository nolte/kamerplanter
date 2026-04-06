---
name: check-slo
description: "Prueft die Betriebsstabilitaets-Konfiguration auf NFR-007-Konformitaet: SLI/SLO-Definitionen in Prometheus/Alertmanager, Circuit-Breaker-Pattern, Graceful-Degradation, Health-Endpoints. Nutze diesen Skill beim Setup von Monitoring oder nach Aenderungen an der Infrastruktur."
argument-hint: "[Komponenten-Name oder 'all', z.B. backend, worker]"
disable-model-invocation: true
---

# SLO/Monitoring-Check (NFR-007): $ARGUMENTS

## Schritt 1: Monitoring-Dateien laden

Suche die relevanten Dateien **parallel**:

1. **Prometheus-Alerts:** Glob `helm/**/alerting-rules*.yaml` oder `monitoring/alerts/*.yaml`
2. **Grafana-Dashboards:** Glob `monitoring/dashboards/*.json`
3. **Health-Endpoints:** Grep `health` in `src/backend/app/api/v1/*/router.py`
4. **Circuit-Breaker:** Grep `circuit_breaker\|CircuitBreaker\|tenacity` in `src/backend/`
5. **NFR-007-Referenz:** Lies `spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md` erste 80 Zeilen

## Schritt 2: SLO-Compliance pruefen

**Pflicht-SLOs aus NFR-007 §2.2:**

| SLO | Ziel | Prüfe in Prometheus-Config |
|-----|------|---------------------------|
| Verfügbarkeit | ≥ 99,5% | Alert bei `probe_success < 0.995` |
| Latenz P50 | < 200ms | Alert bei `histogram_quantile(0.5,...) > 0.2` |
| Latenz P95 | < 500ms | Alert bei `histogram_quantile(0.95,...) > 0.5` |
| Latenz P99 | < 1.000ms | Alert bei `histogram_quantile(0.99,...) > 1.0` |
| Error Rate | < 1% | Alert bei `rate(5xx) / rate(all) > 0.01` |
| Throughput | ≥ 50 req/s | Alert bei `rate(requests[5m]) < 50` |

Prüfe ob fuer jedes SLO eine entsprechende Prometheus-Alert-Rule existiert.

## Schritt 3: Health-Endpoints pruefen

**Pflicht-Endpoints (NFR-007 §2.1, NFR-002 §3.3):**

```python
# MUSS vorhanden sein:
GET /health/live   # Liveness — ist der Prozess am Leben?
GET /health/ready  # Readiness — kann Traffic entgegengenommen werden?

# SOLLTE vorhanden sein:
GET /health/startup  # Startup-Probe fuer langsam startende Komponenten
```

Prüfe:
- Liefern die Endpoints strukturierte JSON-Responses (nicht nur `{"status": "ok"}`)?
- Checken sie ArangoDB/Redis-Konnektivitaet bei `/health/ready`?
- Sind sie in den Kubernetes-Probes konfiguriert?

## Schritt 4: Resilience-Pattern pruefen

**Circuit Breaker (NFR-007 §4):**

```python
# SOLLTE fuer ArangoDB/Redis-Calls vorhanden sein:
# tenacity-basierter Retry mit exponential backoff
# oder eigene CircuitBreaker-Implementierung

@retry(
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True
)
async def _query_with_retry(self, ...): ...
```

Prüfe:
- Gibt es Retry-Logik fuer externe Datenbank-Calls?
- Gibt es Timeouts bei ArangoDB/Redis-Verbindungen?
- Gibt es Fallback-Behavior bei DB-Ausfall (z.B. Cache-only Mode)?

## Schritt 5: Alerting-Eskalation pruefen

Prüfe die Alertmanager-Konfiguration auf 3 Schweregrade:

| Schweregrad | Reaktionszeit | Route |
|-------------|--------------|-------|
| `critical` | < 15 Min | PagerDuty / SMS (On-Call) |
| `warning` | < 4 Stunden | Slack / E-Mail |
| `info` | Naechster Arbeitstag | Ticket-System |

## Schritt 6: Report ausgeben

```markdown
# SLO/Monitoring-Review: {Komponente}

## Health-Endpoints
{/health/live: ✅/❌ | /health/ready: ✅/❌ | DB-Check: ✅/❌}

## SLO-Alert-Coverage
{Tabelle: SLO → Alert-Rule vorhanden: ja/nein}

## Resilience-Patterns
{Circuit Breaker: ✅/❌ | Retry-Logic: ✅/❌ | Timeouts: ✅/❌}

## Alerting-Eskalation
{critical/warning/info-Routen: ✅/❌}

## Fehlende Monitoring-Konfigurationen
{Nummerierte Liste der Luecken}

## Bewertung
- ✅ NFR-007-konform / ❌ {N} Luecken identifiziert
```

## Hinweis

Falls kein Monitoring-Setup gefunden wird, erstelle eine Liste der minimal erforderlichen
Konfigurationen als Implementierungs-Checkliste.
