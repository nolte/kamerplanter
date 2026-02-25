---

ID: NFR-007
Titel: Betriebsstabilität & Monitoring — SLIs/SLOs, Alerting, Incident Response, Resilience
Kategorie: Betrieb / Observability Unterkategorie: SLA, Alerting, Incident Management, Resilience Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Prometheus, Alertmanager, Grafana, Python, FastAPI, Kubernetes
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-26
Tags: [sli, slo, alerting, incident-response, resilience, circuit-breaker, monitoring, operational-stability]
Abhängigkeiten: [NFR-001, NFR-002, NFR-006]
Betroffene Module: [ALL]
---

# NFR-007: Betriebsstabilität & Monitoring

## Abgrenzung zu bestehenden NFRs

| NFR | Fokus | Definiert |
|---|---|---|
| NFR-001 (Abschnitt 8) | Prometheus-Metriken, structlog, Sentry | **Was** gemessen wird |
| NFR-002 (Abschnitt 3.4, 6, 8) | Kubernetes-Probes, Observability-Stack, Backup/DR | **Infrastruktur** |
| NFR-006 | Error-IDs, Log-Korrelation, Error-Response-Schema | **Fehlerformat** |
| **NFR-007 (dieses Dokument)** | SLIs/SLOs, Alerting-Regeln, Incident Response, Resilience | **Betriebsziele & Reaktion** |

NFR-007 definiert **wie** die in NFR-001/002/006 beschriebene Monitoring-Infrastruktur für Betriebsstabilität eingesetzt wird: messbare Ziele, Alarmierung, Eskalationsprozesse und Resilience-Patterns.

---

## 1. Business Case

### 1.1 User Stories

**Als** Site Reliability Engineer (SRE)
**möchte ich** klar definierte SLIs und SLOs für alle kritischen Services
**um** datenbasiert entscheiden zu können, ob wir neue Features deployen oder Stabilität priorisieren (Error Budget).

**Als** DevOps Engineer
**möchte ich** automatische Alerting-Regeln mit klaren Eskalationsstufen
**um** bei Störungen sofort benachrichtigt zu werden, ohne von Alert-Rauschen überflutet zu werden.

**Als** Produktmanager
**möchte ich** eine Statuspage und definierte Reaktionszeiten pro Schweregrad
**um** gegenüber Stakeholdern verbindliche Verfügbarkeitszusagen machen zu können.

**Als** Endanwender
**möchte ich** dass das System bei Teilausfällen graceful degradiert statt vollständig auszufallen
**um** auch bei Störungen weiterhin grundlegende Funktionen nutzen zu können.

### 1.2 Geschäftliche Motivation

Ohne definierte Betriebsziele und Reaktionsprozesse:

1. **Keine messbaren Verfügbarkeitszusagen** — Stakeholder haben keine Grundlage für Verträge oder Erwartungen
2. **Reaktive statt proaktive Störungsbehebung** — Fehler werden erst bemerkt, wenn Anwender sich beschweren
3. **Hoher MTTR (Mean Time to Resolve)** — Ohne Eskalationsprozesse verzögert sich die Fehlerbehebung
4. **Alert Fatigue** — Ohne Strukturierung werden Benachrichtigungen ignoriert
5. **Kaskadierende Ausfälle** — Ohne Resilience-Patterns kann ein einzelner Dienst das gesamte System lahmlegen
6. **Fehlende Kapazitätsplanung** — Ressourcenengpässe werden zu spät erkannt

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: ArangoDB antwortet 3 Sekunden lang nicht (z.B. durch Compaction).
> **Ohne NFR-007**: API-Requests blockieren, Timeouts kaskadieren, alle Requests in der Queue stauen sich, Gesamtsystem fällt aus.
> **Mit NFR-007**: Circuit Breaker öffnet nach 5 Fehlern, API liefert sofort 503 mit Retry-After-Header, Alarm wird an On-Call gesendet, Anwender sieht "Service vorübergehend eingeschränkt" statt endlos ladendem Spinner.

---

## 2. Service Level Indicators (SLI) & Objectives (SLO)

### 2.1 SLI-Definitionen

Alle SLIs basieren auf Prometheus-Metriken (vgl. NFR-001 Abschnitt 8.1, NFR-002 Abschnitt 6.1).

| SLI | Metrik | Messmethode |
|---|---|---|
| **Verfügbarkeit** | Anteil erfolgreicher Health-Check-Responses (`/health/ready`) | `probe_success` von externem Prober (nicht Kubernetes-Probe) |
| **Latenz** | Request-Dauer für API-Requests | `http_request_duration_seconds` (Histogram) |
| **Error Rate** | Anteil der Requests mit HTTP 5xx | `http_requests_total{status=~"5.."}` / `http_requests_total` |
| **Throughput** | Requests pro Sekunde unter Last | `rate(http_requests_total[5m])` |

### 2.2 SLO-Definitionen

**MUSS**: Folgende SLOs gelten für die Production-Umgebung.

| SLO | Ziel | Error Budget (30 Tage) |
|---|---|---|
| **Verfügbarkeit** | ≥ 99,5 % | 3 Stunden 36 Minuten Downtime |
| **Latenz P50** | < 200 ms | — |
| **Latenz P95** | < 500 ms | — |
| **Latenz P99** | < 1.000 ms | — |
| **Error Rate** | < 1 % der Requests mit 5xx | — |
| **Throughput** | ≥ 50 Requests/s ohne Degradation | — |

### 2.3 SLO-Messzeitraum

- **MUSS**: SLOs werden über einen rollierenden 30-Tage-Zeitraum gemessen
- **MUSS**: Geplante Wartungsfenster werden aus der SLO-Berechnung herausgerechnet
- **SOLL**: SLO-Berichte werden wöchentlich automatisch generiert (Grafana-Report)

### 2.4 Error Budgets

**MUSS**: Für jedes SLO wird ein Error Budget berechnet:

```
Error Budget = 1 - SLO-Ziel
Beispiel Verfügbarkeit: 1 - 0,995 = 0,005 = 0,5 % = 3h 36min / 30 Tage
```

**MUSS**: Error-Budget-Regeln:

| Error Budget verbraucht | Maßnahme |
|---|---|
| < 50 % | Normaler Betrieb, Feature-Releases erlaubt |
| 50 – 75 % | Erhöhte Vorsicht, nur getestete Releases |
| 75 – 100 % | Feature Freeze, nur Bugfixes und Stabilitätsverbesserungen |
| 100 % (aufgebraucht) | Deployment-Stop bis Budget regeneriert, Fokus auf Reliability |

**SOLL**: Error-Budget-Verbrauch wird als Gauge-Metrik in Grafana visualisiert.

### 2.5 SLO-Prometheus-Recording-Rules

```yaml
# k8s/monitoring/slo-recording-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: slo-recording-rules
  namespace: monitoring
spec:
  groups:
  - name: slo.rules
    interval: 30s
    rules:
    # Verfügbarkeit (30 Tage rollierend)
    - record: slo:availability:ratio_30d
      expr: |
        1 - (
          sum(increase(http_requests_total{status=~"5..", job="backend"}[30d]))
          /
          sum(increase(http_requests_total{job="backend"}[30d]))
        )

    # Error Rate (5 Minuten)
    - record: slo:error_rate:ratio_5m
      expr: |
        sum(rate(http_requests_total{status=~"5..", job="backend"}[5m]))
        /
        sum(rate(http_requests_total{job="backend"}[5m]))

    # Latenz P95 (5 Minuten)
    - record: slo:latency_p95:seconds_5m
      expr: |
        histogram_quantile(0.95,
          sum(rate(http_request_duration_seconds_bucket{job="backend"}[5m])) by (le)
        )

    # Latenz P99 (5 Minuten)
    - record: slo:latency_p99:seconds_5m
      expr: |
        histogram_quantile(0.99,
          sum(rate(http_request_duration_seconds_bucket{job="backend"}[5m])) by (le)
        )

    # Error Budget verbleibend (30 Tage, Ziel 99,5%)
    - record: slo:error_budget:remaining_ratio
      expr: |
        1 - (
          (1 - slo:availability:ratio_30d)
          /
          (1 - 0.995)
        )
```

---

## 3. Alerting & Eskalation

### 3.1 Alerting-Schweregrade

**MUSS**: Alerts werden in drei Schweregrade eingeteilt:

| Schweregrad | Beschreibung | Reaktionszeit | Benachrichtigung |
|---|---|---|---|
| **Critical** | Totalausfall oder SLO-Verletzung | ≤ 15 Minuten | PagerDuty/OpsGenie + Slack `#incidents` |
| **Warning** | Drohende SLO-Verletzung oder Degradation | ≤ 1 Stunde | Slack `#alerts` + E-Mail |
| **Info** | Auffälligkeit ohne unmittelbare Auswirkung | Nächster Arbeitstag | Slack `#monitoring` |

### 3.2 PrometheusRule-Definitionen

**MUSS**: Mindestens folgende Alerting-Regeln sind definiert:

```yaml
# k8s/monitoring/alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: backend-alerts
  namespace: monitoring
spec:
  groups:
  - name: availability.rules
    rules:
    # Verfügbarkeit unter SLO
    - alert: AvailabilityBelowSLO
      expr: slo:availability:ratio_30d < 0.995
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Verfügbarkeit unter SLO ({{ $value | humanizePercentage }})"
        description: "Die 30-Tage-Verfügbarkeit ist unter 99,5% gefallen."
        runbook_url: "https://wiki.internal/runbooks/availability-below-slo"

    # Error Rate kritisch
    - alert: HighErrorRate
      expr: slo:error_rate:ratio_5m > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Error Rate über 5% ({{ $value | humanizePercentage }})"
        description: "Mehr als 5% der Requests liefern 5xx seit 5 Minuten."
        runbook_url: "https://wiki.internal/runbooks/high-error-rate"

    # Error Rate warnung
    - alert: ElevatedErrorRate
      expr: slo:error_rate:ratio_5m > 0.01
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Error Rate über 1% ({{ $value | humanizePercentage }})"
        description: "Error Rate übersteigt SLO-Ziel seit 10 Minuten."
        runbook_url: "https://wiki.internal/runbooks/elevated-error-rate"

  - name: latency.rules
    rules:
    # Latenz P95 über SLO
    - alert: HighLatencyP95
      expr: slo:latency_p95:seconds_5m > 0.5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "P95 Latenz über 500ms ({{ $value | humanizeDuration }})"
        description: "Die P95-Latenz übersteigt das SLO-Ziel seit 5 Minuten."
        runbook_url: "https://wiki.internal/runbooks/high-latency"

    # Latenz P99 über SLO
    - alert: HighLatencyP99
      expr: slo:latency_p99:seconds_5m > 1.0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "P99 Latenz über 1s ({{ $value | humanizeDuration }})"
        description: "Die P99-Latenz übersteigt das SLO-Ziel seit 5 Minuten."
        runbook_url: "https://wiki.internal/runbooks/high-latency-critical"

  - name: resource.rules
    rules:
    # CPU sustained hoch
    - alert: HighCPUUsage
      expr: |
        avg(rate(container_cpu_usage_seconds_total{namespace="agrotech-prod", container="backend"}[5m]))
        /
        avg(kube_pod_container_resource_limits{namespace="agrotech-prod", container="backend", resource="cpu"})
        > 0.8
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "Backend CPU > 80% seit 15 Minuten"
        description: "Sustained hohe CPU-Last deutet auf Kapazitätsengpass hin."
        runbook_url: "https://wiki.internal/runbooks/high-cpu"

    # Memory sustained hoch
    - alert: HighMemoryUsage
      expr: |
        avg(container_memory_working_set_bytes{namespace="agrotech-prod", container="backend"})
        /
        avg(kube_pod_container_resource_limits{namespace="agrotech-prod", container="backend", resource="memory"})
        > 0.8
      for: 15m
      labels:
        severity: warning
      annotations:
        summary: "Backend Memory > 80% seit 15 Minuten"
        description: "Sustained hoher Speicherverbrauch deutet auf Memory Leak oder Kapazitätsengpass hin."
        runbook_url: "https://wiki.internal/runbooks/high-memory"

  - name: dependency.rules
    rules:
    # ArangoDB nicht erreichbar
    - alert: ArangoDBDown
      expr: probe_success{job="arangodb-probe"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "ArangoDB nicht erreichbar"
        description: "ArangoDB Health-Check schlägt seit 1 Minute fehl."
        runbook_url: "https://wiki.internal/runbooks/arangodb-down"

    # Redis nicht erreichbar
    - alert: RedisDown
      expr: probe_success{job="redis-probe"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Redis nicht erreichbar"
        description: "Redis Health-Check schlägt seit 1 Minute fehl."
        runbook_url: "https://wiki.internal/runbooks/redis-down"

    # Error Budget unter 25%
    - alert: ErrorBudgetLow
      expr: slo:error_budget:remaining_ratio < 0.25
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Error Budget unter 25% ({{ $value | humanizePercentage }} verbleibend)"
        description: "Weniger als 25% des Error Budgets verbleiben. Feature Freeze empfohlen."
        runbook_url: "https://wiki.internal/runbooks/error-budget-low"

    # Error Budget aufgebraucht
    - alert: ErrorBudgetExhausted
      expr: slo:error_budget:remaining_ratio <= 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Error Budget aufgebraucht"
        description: "Das Error Budget ist vollständig aufgebraucht. Deployment-Stop erforderlich."
        runbook_url: "https://wiki.internal/runbooks/error-budget-exhausted"
```

### 3.3 Alertmanager-Konfiguration

**MUSS**: Benachrichtigungskanäle und Routing:

```yaml
# k8s/monitoring/alertmanager-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-config
  namespace: monitoring
stringData:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      receiver: 'default'
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      routes:
      - match:
          severity: critical
        receiver: 'critical'
        group_wait: 10s
        repeat_interval: 1h
      - match:
          severity: warning
        receiver: 'warning'
        repeat_interval: 4h
      - match:
          severity: info
        receiver: 'info'
        repeat_interval: 24h

    receivers:
    - name: 'critical'
      pagerduty_configs:
      - service_key_file: /etc/alertmanager/secrets/pagerduty-key
        severity: critical
      slack_configs:
      - api_url_file: /etc/alertmanager/secrets/slack-webhook
        channel: '#incidents'
        title: '🔴 CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

    - name: 'warning'
      slack_configs:
      - api_url_file: /etc/alertmanager/secrets/slack-webhook
        channel: '#alerts'
        title: '🟡 WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
      email_configs:
      - to: 'oncall@kamerplanter.example.com'

    - name: 'info'
      slack_configs:
      - api_url_file: /etc/alertmanager/secrets/slack-webhook
        channel: '#monitoring'
        title: 'ℹ️ INFO: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

    - name: 'default'
      slack_configs:
      - api_url_file: /etc/alertmanager/secrets/slack-webhook
        channel: '#monitoring'

    inhibit_rules:
    # Unterdrücke Warning wenn Critical für gleichen Service aktiv
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['alertname', 'namespace']
```

### 3.4 Eskalationsstufen

**MUSS**: Bei Critical-Alerts greift folgende Eskalation:

| Stufe | Zeitrahmen | Aktion |
|---|---|---|
| **L1 — Automatisch** | Sofort | PagerDuty/OpsGenie benachrichtigt On-Call-Engineer |
| **L2 — On-Call** | 15 Minuten ohne Acknowledge | Eskalation an Backup-On-Call |
| **L3 — Team-Lead** | 30 Minuten ohne Fortschritt | Team-Lead wird einbezogen, War Room eröffnet |
| **L4 — Management** | 1 Stunde bei SEV-1/SEV-2 | CTO/VP Engineering informiert |

### 3.5 Alert-Fatigue-Prävention

**MUSS**: Folgende Maßnahmen gegen Alert Fatigue:

1. **Gruppierung**: Zusammengehörige Alerts werden gruppiert (z.B. alle Latenz-Alerts eines Services)
2. **Inhibition**: Warning-Alerts werden unterdrückt, wenn ein Critical-Alert für denselben Service aktiv ist
3. **Silencing**: Geplante Wartungsfenster werden vorab als Silence in Alertmanager eingetragen

**SOLL**: Quartalsweise Alert-Review — ungenutzte oder häufig ignorierte Alerts werden angepasst oder entfernt.

### 3.6 Runbook-Pflicht

**MUSS**: Jeder Alert enthält in `annotations.runbook_url` einen Link zu einem Runbook mit:

- Beschreibung des Problems
- Diagnostische Schritte
- Behebungsmaßnahmen
- Eskalationspfad

---

## 4. Resilience-Patterns

### 4.1 Circuit Breaker

**MUSS**: Für alle externen Abhängigkeiten (ArangoDB, Redis, externe APIs) wird ein Circuit Breaker implementiert.

**Zustandsübergänge**:

```
        Fehler > Schwellwert
  CLOSED ──────────────────► OPEN
    ▲                          │
    │ Erfolg                   │ Timeout (30s)
    │                          ▼
    └───────────────────── HALF-OPEN
        Probe erfolgreich
```

**Konfigurationsparameter**:

| Parameter | Wert | Beschreibung |
|---|---|---|
| `failure_threshold` | 5 | Fehler bis Circuit öffnet |
| `success_threshold` | 3 | Erfolge in Half-Open bis Circuit schließt |
| `timeout` | 30s | Wartezeit bis Half-Open |
| `excluded_exceptions` | `ValidationError` | Werden nicht als Circuit-Breaker-Fehler gezählt |

**Implementierungsbeispiel**:

```python
# app/common/resilience.py
import time
import threading
from enum import Enum

import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and time.monotonic() - self._last_failure_time >= self.timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info("circuit_breaker_half_open", name=self.name)
            return self._state

    def record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info("circuit_breaker_closed", name=self.name)
            else:
                self._failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_opened",
                    name=self.name,
                    failure_count=self._failure_count,
                )

    def allow_request(self) -> bool:
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            return True
        return False
```

**MUSS**: Circuit-Breaker-Zustand wird als Prometheus-Gauge exportiert:

```python
from prometheus_client import Gauge

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit Breaker State (0=closed, 1=half_open, 2=open)",
    ["dependency"],
)
```

### 4.2 Retry-Policies

**MUSS**: Fehlgeschlagene Netzwerkoperationen werden mit Exponential Backoff und Jitter wiederholt.

| Parameter | Wert | Beschreibung |
|---|---|---|
| `max_retries` | 3 | Maximale Wiederholungsversuche |
| `base_delay` | 0,5s | Initiale Wartezeit |
| `max_delay` | 10s | Maximale Wartezeit |
| `backoff_factor` | 2 | Exponent für Backoff |
| `jitter` | ±25 % | Zufällige Variation zur Vermeidung von Thundering Herd |

**Retryable Fehler**: Verbindungsabbrüche, Timeouts, HTTP 503, HTTP 429 (mit Retry-After).
**Nicht-retryable Fehler**: HTTP 4xx (außer 429), Validierungsfehler, Authentifizierungsfehler.

```python
# app/common/retry.py
import random
import asyncio

import structlog

logger = structlog.get_logger()


async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.25,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError),
):
    """Retry mit Exponential Backoff und Jitter."""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retryable_exceptions as exc:
            if attempt == max_retries:
                logger.error(
                    "retry_exhausted",
                    attempts=attempt + 1,
                    error=str(exc),
                )
                raise
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            delay *= 1 + random.uniform(-jitter, jitter)
            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_seconds=round(delay, 2),
                error=str(exc),
            )
            await asyncio.sleep(delay)
```

### 4.3 Timeouts

**MUSS**: Alle Netzwerkaufrufe haben explizite Timeouts.

| Ziel | Connect-Timeout | Read-Timeout | Gesamt-Timeout |
|---|---|---|---|
| ArangoDB | 2s | 10s | 15s |
| Redis | 1s | 5s | 7s |
| Externe APIs (Home Assistant) | 3s | 15s | 20s |
| Interne Services | 1s | 5s | 7s |

**MUSS**: Kein Netzwerkaufruf darf ohne Timeout erfolgen. Standard-Timeout (falls nicht explizit gesetzt): 30s.

### 4.4 Bulkhead-Pattern

**MUSS**: Kritische Ressourcenpools werden isoliert, damit ein überlasteter Dienst nicht alle Verbindungen blockiert.

| Pool | Max. Verbindungen | Beschreibung |
|---|---|---|
| ArangoDB Connection Pool | 20 | Primärdatenbank |
| Redis Connection Pool | 10 | Cache und Celery Broker |
| HTTP Client Pool (extern) | 10 | Home Assistant, externe APIs |

**MUSS**: Connection-Pool-Auslastung wird als Prometheus-Gauge exportiert:

```python
from prometheus_client import Gauge

connection_pool_usage = Gauge(
    "connection_pool_active_connections",
    "Active connections in pool",
    ["pool_name"],
)

connection_pool_max = Gauge(
    "connection_pool_max_connections",
    "Maximum connections in pool",
    ["pool_name"],
)
```

### 4.5 Graceful Degradation

**MUSS**: Bei Teilausfällen liefert das System eingeschränkte Funktionalität statt eines Totalausfalls.

| Ausgefallene Komponente | Degradiertes Verhalten |
|---|---|
| **Redis** | Cache-Bypass — Daten direkt aus ArangoDB, Celery-Tasks in Dead Letter Queue |
| **TimescaleDB** | Sensordaten werden gepuffert (Redis/File), Dashboards zeigen "Daten verzögert" |
| **Externer Sensor-Service** | Letzte bekannte Werte werden angezeigt (Stale-Markierung im UI) |
| **Celery Worker** | Synchrone Fallback-Verarbeitung für kritische Tasks (Phase-Transitions) |

**MUSS**: Degradierter Zustand wird über eine Metrik signalisiert:

```python
from prometheus_client import Gauge

service_degraded = Gauge(
    "service_degraded",
    "Service is in degraded mode (0=healthy, 1=degraded)",
    ["component"],
)
```

### 4.6 Rate Limiting

**MUSS**: API-Endpunkte sind gegen Überlastung geschützt (vgl. NFR-006, Error-Code `RATE_LIMITED`).

| Scope | Limit | Zeitfenster |
|---|---|---|
| Global (alle Clients) | 1.000 Requests | 1 Minute |
| Per Client (IP/API-Key) | 100 Requests | 1 Minute |
| Per Endpunkt (Schreiboperationen) | 20 Requests | 1 Minute |

**MUSS**: Rate-Limit-Responses enthalten `Retry-After`-Header.
**MUSS**: Rate-Limit-Überschreitungen werden als Prometheus-Counter gezählt.

---

## 5. Incident Management

### 5.1 Incident-Schweregrade

**MUSS**: Incidents werden nach folgendem Schema klassifiziert:

| Schweregrad | Beschreibung | Beispiel |
|---|---|---|
| **SEV-1 — Totalausfall** | System ist vollständig nicht erreichbar | API liefert nur 503, keine DB-Verbindung |
| **SEV-2 — Teilausfall** | Kernfunktionalität eingeschränkt | Pflanzenverwaltung funktioniert, Sensordaten nicht |
| **SEV-3 — Degradation** | Performance oder Nebenfunktion beeinträchtigt | Latenz > SLO, Dashboard-Daten verzögert |
| **SEV-4 — Kosmetisch** | Minimale Auswirkung, kein Funktionsverlust | Falsche Formatierung, langsamer Report-Export |

### 5.2 Reaktionszeiten

**MUSS**: Folgende Reaktionszeiten (Time to Acknowledge) gelten:

| Schweregrad | Geschäftszeiten (Mo–Fr 08–18) | Außerhalb Geschäftszeiten |
|---|---|---|
| **SEV-1** | ≤ 15 Minuten | ≤ 30 Minuten |
| **SEV-2** | ≤ 30 Minuten | ≤ 2 Stunden |
| **SEV-3** | ≤ 4 Stunden | Nächster Arbeitstag |
| **SEV-4** | ≤ 1 Arbeitstag | Nächster Arbeitstag |

### 5.3 Incident-Lifecycle

```
  Erkennung     Acknowledge     Diagnose     Behebung     Abschluss
     │               │              │            │             │
     ▼               ▼              ▼            ▼             ▼
  ┌───────┐    ┌───────────┐   ┌────────┐   ┌────────┐   ┌────────┐
  │ Alert │───►│ Confirmed │──►│ Active │──►│Resolved│──►│ Closed │
  └───────┘    └───────────┘   └────────┘   └────────┘   └────────┘
                                    │                         │
                                    │     ┌──────────────┐    │
                                    └────►│ Post-Mortem  │◄───┘
                                          └──────────────┘
```

### 5.4 Post-Mortem-Pflicht

**MUSS**: Für jeden Incident ab SEV-2 wird innerhalb von 5 Arbeitstagen ein Post-Mortem erstellt.

**MUSS**: Post-Mortem-Inhalt:

1. **Zusammenfassung** — Was ist passiert?
2. **Timeline** — Chronologischer Ablauf (Erkennung → Behebung)
3. **Ursachenanalyse** — Root Cause (5-Why-Methode)
4. **Auswirkung** — Betroffene Nutzer, Dauer, SLO-Impact
5. **Action Items** — Konkrete Maßnahmen mit Verantwortlichen und Fristen
6. **Lessons Learned** — Was lief gut, was nicht?

**MUSS**: Post-Mortems sind blameless — Fokus auf Systemverbesserung, nicht auf individuelle Schuldzuweisung.

### 5.5 Statuspage

**SOLL**: Eine öffentliche Statuspage informiert Endanwender über den Systemzustand.

| Komponente | Angezeigte Status |
|---|---|
| API | Operational / Degraded / Outage |
| Web-Frontend | Operational / Degraded / Outage |
| Sensordaten-Erfassung | Operational / Delayed / Outage |
| Hintergrund-Verarbeitung | Operational / Delayed / Outage |

**SOLL**: Statuspage wird automatisch über Prometheus-Alerts aktualisiert (z.B. via Atlassian Statuspage API oder Cachet).

---

## 6. Synthetic Monitoring & Uptime Checks

### 6.1 Externe Health-Checks

**MUSS**: Die Verfügbarkeit wird zusätzlich zu den Kubernetes-Probes (vgl. NFR-002 Abschnitt 3.2) von einem **externen** Standort überwacht.

| Check | Endpunkt | Intervall | Timeout |
|---|---|---|---|
| API Liveness | `GET /health/live` | 30s | 5s |
| API Readiness | `GET /health/ready` | 60s | 10s |
| API Smoke | `GET /api/v1/botanical-families?limit=1` | 60s | 10s |
| Frontend Erreichbarkeit | `GET /` (HTTP 200) | 60s | 10s |

**MUSS**: Externe Checks nutzen einen dedizierten Prober (z.B. Prometheus Blackbox Exporter oder Uptime-Kuma), nicht die Kubernetes-internen Probes.

```yaml
# k8s/monitoring/blackbox-exporter-targets.yaml
apiVersion: monitoring.coreos.com/v1
kind: Probe
metadata:
  name: external-api-probe
  namespace: monitoring
spec:
  interval: 30s
  module: http_2xx
  prober:
    url: blackbox-exporter.monitoring.svc:9115
  targets:
    staticConfig:
      static:
      - https://api.kamerplanter.example.com/health/live
      - https://api.kamerplanter.example.com/health/ready
      - https://app.kamerplanter.example.com/
```

### 6.2 Smoke-Tests nach Deployment

**MUSS**: Nach jedem Deployment in Production werden automatisch Smoke-Tests ausgeführt.

```yaml
# k8s/tests/smoke-test-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: post-deploy-smoke-test
  annotations:
    helm.sh/hook: post-install,post-upgrade
    helm.sh/hook-weight: "5"
    helm.sh/hook-delete-policy: hook-succeeded
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: smoke-test
        image: curlimages/curl:8.5.0
        command:
        - /bin/sh
        - -c
        - |
          set -e
          echo "Smoke Test: Health Check"
          curl -sf http://backend:8000/health/ready

          echo "Smoke Test: API Response"
          curl -sf http://backend:8000/api/v1/botanical-families?limit=1

          echo "Smoke Test: Metrics Endpoint"
          curl -sf http://backend:8000/metrics | grep -q "http_requests_total"

          echo "All smoke tests passed"
```

**MUSS**: Fehlgeschlagene Smoke-Tests lösen automatisches Rollback aus (Helm `--atomic` Flag).

### 6.3 Canary Deployments

**SOLL**: Für kritische Änderungen wird ein Canary Deployment durchgeführt.

- 10 % des Traffics wird auf die neue Version geleitet
- Latenz und Error Rate der Canary werden mit der Baseline verglichen
- Automatisches Rollback bei Verschlechterung > 10 % gegenüber Baseline
- Schrittweise Traffic-Erhöhung: 10 % → 25 % → 50 % → 100 %

**KANN**: Integration mit Flagger oder Argo Rollouts für automatisierte Canary-Analyse.

---

## 7. Kapazitätsplanung & Dashboards

### 7.1 Dashboard-Pflicht

**MUSS**: Folgende Grafana-Dashboards sind eingerichtet:

| Dashboard | Inhalt |
|---|---|
| **System Overview** | SLO-Status, Error Budget, Service-Health aller Komponenten |
| **API Metrics** | Request Rate, Latenz-Percentile, Error Rate, Top-Endpunkte |
| **Infrastructure** | CPU, Memory, Disk, Netzwerk pro Pod/Node |
| **Business Metrics** | Aktive Pflanzen, Phase-Transitions/Tag, Sensor-Datenpunkte/Stunde |
| **Dependencies** | ArangoDB-Queries/s, Redis Hit-Rate, Circuit-Breaker-Status |

### 7.2 Kapazitätswarnungen

**MUSS**: Kapazitätswarnungen werden ausgelöst bei:

| Metrik | Warning-Schwelle | Critical-Schwelle | Sustained-Dauer |
|---|---|---|---|
| CPU-Nutzung | > 70 % | > 85 % | 15 Minuten |
| Memory-Nutzung | > 70 % | > 85 % | 15 Minuten |
| Disk-Nutzung (PVC) | > 75 % | > 90 % | 5 Minuten |
| ArangoDB Connections | > 70 % des Pools | > 90 % des Pools | 5 Minuten |

### 7.3 Trend-Analyse

**SOLL**: Wöchentliche automatische Reports über:

- Ressourcenverbrauch-Trend (letzte 4 Wochen)
- SLO-Einhallung pro Woche
- Top-5 langsamste Endpunkte
- Error-Budget-Verbrauch

**SOLL**: Prognose-Regeln (Prometheus `predict_linear`):

```yaml
# Disk voll in < 7 Tagen
- alert: DiskFillingUp
  expr: |
    predict_linear(
      kubelet_volume_stats_available_bytes{namespace="agrotech-prod"}[7d], 7*24*3600
    ) < 0
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "PVC wird voraussichtlich in < 7 Tagen voll"
    runbook_url: "https://wiki.internal/runbooks/disk-filling-up"
```

---

## 8. Akzeptanzkriterien

### Definition of Done

- [ ] **SLIs & SLOs**
    - [ ] SLI-Metriken werden in Prometheus erfasst
    - [ ] SLO-Recording-Rules sind deployt und liefern korrekte Werte
    - [ ] Error-Budget wird berechnet und in Grafana visualisiert
    - [ ] SLO-Dashboard zeigt 30-Tage-Verfügbarkeit, Latenz-Percentile und Error Rate
- [ ] **Alerting**
    - [ ] PrometheusRules für alle definierten Alerts deployt
    - [ ] Alertmanager-Routing konfiguriert (Critical → PagerDuty, Warning → Slack, Info → Slack)
    - [ ] Inhibition-Rules aktiv (Warning unterdrückt bei Critical)
    - [ ] Jeder Alert hat eine `runbook_url`-Annotation
    - [ ] Alert-Test: Manuelles Auslösen eines Critical-Alerts erreicht On-Call innerhalb von 15 Minuten
- [ ] **Resilience**
    - [ ] Circuit Breaker für ArangoDB, Redis und externe APIs implementiert
    - [ ] Circuit-Breaker-Zustand als Prometheus-Gauge exportiert
    - [ ] Retry mit Exponential Backoff und Jitter für alle Netzwerkaufrufe
    - [ ] Explizite Timeouts für alle Netzwerkaufrufe konfiguriert
    - [ ] Connection Pools isoliert (Bulkhead)
    - [ ] Graceful Degradation bei Redis-Ausfall getestet
    - [ ] Rate Limiting aktiv, `Retry-After`-Header gesetzt
- [ ] **Incident Management**
    - [ ] Schweregrade (SEV-1 bis SEV-4) dokumentiert und im Team kommuniziert
    - [ ] Reaktionszeiten pro Schweregrad definiert
    - [ ] Post-Mortem-Template erstellt
    - [ ] On-Call-Rotation eingerichtet
- [ ] **Synthetic Monitoring**
    - [ ] Externer Health-Check (Blackbox Exporter oder Uptime-Kuma) aktiv
    - [ ] Smoke-Tests nach jedem Production-Deployment
    - [ ] Fehlgeschlagene Smoke-Tests lösen Rollback aus
- [ ] **Dashboards & Kapazität**
    - [ ] Alle fünf Pflicht-Dashboards in Grafana eingerichtet
    - [ ] Kapazitätswarnungen (CPU, Memory, Disk) konfiguriert
    - [ ] `predict_linear`-Rule für Disk-Filling deployt

---

## 9. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Keine SLOs definiert** | Keine messbaren Verfügbarkeitszusagen, Feature-Velocity vs. Stabilität unklar | Hoch | SLOs ab Tag 1, Error Budgets als Steuerungsinstrument |
| **Alert Fatigue** | On-Call ignoriert Alerts, echte Störungen werden übersehen | Hoch | Inhibition, Gruppierung, quartalsweiser Alert-Review |
| **Fehlende Circuit Breaker** | Kaskadierende Ausfälle bei Dependency-Problemen | Mittel | Circuit Breaker für alle externen Abhängigkeiten |
| **Keine Timeouts** | Threads/Connections blockieren endlos, Pool Exhaustion | Hoch | Verpflichtende Timeouts mit konservativen Defaults |
| **Kein Incident-Prozess** | Ad-hoc-Reaktion, keine Lerneffekte, wiederholte Fehler | Mittel | Schweregrade, Reaktionszeiten, Post-Mortem-Pflicht |
| **Keine externen Health-Checks** | Systemausfall wird erst durch Anwender bemerkt | Mittel | Externer Prober zusätzlich zu K8s-Probes |
| **Fehlende Kapazitätsplanung** | Ressourcenengpässe in Spitzenzeiten (z.B. Erntezeit) | Mittel | Trend-Analyse, `predict_linear`, Kapazitätswarnungen |
| **Kein Canary Deployment** | Fehlerhafte Releases betreffen sofort alle Anwender | Niedrig | Canary mit automatischem Rollback bei Degradation |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-26
**Review**: Pending
**Genehmigung**: Pending
