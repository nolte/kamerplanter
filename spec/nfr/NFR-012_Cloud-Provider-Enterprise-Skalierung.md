---

ID: NFR-012
Titel: Cloud-Provider-Anforderungen & Enterprise-Skalierung
Kategorie: Infrastruktur / Cloud Unterkategorie: Cloud-Provider, Skalierung, HA, DSGVO-Hosting
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Kubernetes 1.28+, ArangoDB 3.11+, TimescaleDB 2.13+, PostgreSQL 18, Redis 7.2+, Traefik, Prometheus, Grafana
Status: Entwurf
Prioritaet: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-31
Tags: [cloud, enterprise, scaling, ha, dsgvo, backup, disaster-recovery, cost-estimation, sla]
Abhaengigkeiten: [NFR-001, NFR-002, NFR-007, NFR-011, REQ-023, REQ-024, REQ-025]
Betroffene Module: [ALL]
---

# NFR-012: Cloud-Provider-Anforderungen & Enterprise-Skalierung

## 1. Business Case

### 1.1 User Stories

**Als** CTO / IT-Leiter
**moechte ich** klar definierte Mindestanforderungen an einen Cloud-Provider
**um** eine fundierte Entscheidung fuer den Enterprise-Betrieb von Kamerplanter treffen zu koennen.

**Als** DevOps Engineer
**moechte ich** eine Referenzarchitektur mit konkreten Ressourcen-Spezifikationen
**um** die Infrastruktur reproduzierbar aufzusetzen und zu skalieren.

**Als** Datenschutzbeauftragter
**moechte ich** dass der Cloud-Provider alle DSGVO-Anforderungen nachweislich erfuellt
**um** die Compliance gegenueber Aufsichtsbehoerden sicherzustellen.

### 1.2 Geschaeftliche Motivation

Diese NFR definiert die **Mindestanforderungen an einen Cloud-Provider** und die **Skalierungsstrategie** fuer den Enterprise-Betrieb. Sie bildet die Grundlage fuer:

1. **Provider-Auswahl**: Bewertungsmatrix fuer AWS, GCP, Azure und kostenguenstige Alternativen
2. **Kapazitaetsplanung**: Konkrete Ressourcen-Spezifikationen pro Skalierungsstufe
3. **Kostensteuerung**: Transparente Kalkulation fuer Budget-Entscheidungen
4. **Compliance**: DSGVO-konforme Hosting-Anforderungen
5. **Disaster Recovery**: Verbindliche RPO/RTO-Ziele

### 1.3 Abgrenzung

| Dokument | Fokus | Abgrenzung |
|----------|-------|------------|
| NFR-002 | Kubernetes-Plattform & Helm | **Wie** deployed wird |
| NFR-007 | SLIs/SLOs, Alerting, Resilience | **Welche** Betriebsziele gelten |
| NFR-011 | Retention, DSGVO-Loeschfristen | **Welche** Daten wie lange gespeichert werden |
| **NFR-012 (dieses Dokument)** | Cloud-Provider & Skalierung | **Wo** und **mit welchen Ressourcen** betrieben wird |

---

## 2. Kubernetes (Managed)

### 2.1 Anforderungen

| Anforderung | Minimum | Empfehlung |
|-------------|---------|------------|
| **Managed K8s** | Kubernetes 1.28+ | GKE Autopilot / EKS / AKS |
| **Node Pools** | 3 Nodes (Stateless), 3 Nodes (Stateful/DB) | Separate Pools mit Taints/Tolerations |
| **Autoscaling** | HPA (CPU/Memory) | HPA + VPA + Cluster Autoscaler (0 bis N) |
| **Namespaces** | dev, staging, prod | + Preview-Environments pro PR |
| **Ingress** | Traefik (bereits spezifiziert, NFR-002) | Traefik + Cloud-LB davor |
| **Node-Sizing (Stateless)** | 4 vCPU / 8 GB RAM | 8 vCPU / 16 GB (fuer Celery-Burst) |
| **Node-Sizing (Stateful)** | 4 vCPU / 16 GB RAM | 8 vCPU / 32 GB (ArangoDB Cluster) |

**Begruendung:** NFR-002 fordert horizontale Skalierung, Rolling Updates und Multi-Namespace-Isolierung. Das Referenzszenario (5 Gewaechshaeuser, 200 Pflanzen je) skaliert von 3 auf 10 Backend-Pods in Erntezeit.

### 2.2 Stateless vs. Stateful Zuordnung

**Stateless Components** (Deployment, horizontal skalierbar):

- FastAPI Backend
- Frontend (Nginx)
- Celery Worker
- Embedding Service (ONNX)
- LLM Adapter

**Stateful Components** (StatefulSet, PVC-gebunden):

- ArangoDB Cluster (3 Nodes)
- TimescaleDB (Primary + Replica)
- PostgreSQL 18 + pgvector
- Redis (optional als Deployment)

---

## 3. Datenbanken (Stateful Services)

### 3.1 ArangoDB (Primary — Multi-Model)

| Anforderung | Spezifikation |
|-------------|---------------|
| **Deployment** | 3-Node Cluster (StatefulSet) oder ArangoDB Oasis (Managed) |
| **Storage** | 50 GB SSD/NVMe pro Node (PVC, ReadWriteOnce) |
| **IOPS** | >= 3.000 IOPS (RocksDB-Workload) |
| **Backup** | Taeglicher Snapshot + Point-in-Time Recovery |
| **Encryption** | At-rest (Volume-Level) + in-transit (TLS) |

**Begruendung:** 54 Document- und 75 Edge-Collections erfordern performante Graph-Traversals (Mischkultur-Kompatibilitaet, genetische Lineage, Companion Planting, rekursive Standort-Hierarchien).

### 3.2 TimescaleDB (Time-Series)

| Anforderung | Spezifikation |
|-------------|---------------|
| **Managed** | Timescale Cloud oder PostgreSQL 18 + Extension |
| **Storage** | 100 GB+ (Continuous Aggregates, 3-Stufen-Downsampling) |
| **Retention** | 90d raw, 2y hourly, 5y daily (NFR-011 §2.2) |
| **HA** | Streaming Replication mit automatischem Failover |

**Begruendung:** Sensor-Readings (Temperatur, Luftfeuchtigkeit, pH, EC, PPFD) erfordern minutengenaue Erfassung mit automatischer Aggregation. Das 3-Stufen-Downsampling (NFR-011) spart langfristig Storage bei gleichzeitiger Bewahrung historischer Trends.

### 3.3 PostgreSQL 18 + pgvector (RAG/Vector)

| Anforderung | Spezifikation |
|-------------|---------------|
| **Extension** | pgvector fuer Embedding-Suche (1024-dim, HNSW-Index) |
| **Storage** | 20 GB+ |
| **RAM** | >= 4 GB (HNSW-Index im Speicher) |

**Begruendung:** Wissensbasierte Pflanzenpflege-Empfehlungen ueber RAG-Pipeline (Embedding Service + LLM Adapter).

### 3.4 Redis 7.2+

| Anforderung | Spezifikation |
|-------------|---------------|
| **Rollen** | Cache, Celery Broker/Backend, Rate Limiting, OAuth State (TTL) |
| **HA** | Redis Sentinel oder Managed (ElastiCache/Memorystore) |
| **Memory** | >= 2 GB |
| **Persistenz** | Optional (RDB-Snapshots), primaer ephemeral |

---

## 4. Compute (Application Layer)

### 4.1 Pod-Spezifikationen (Production)

| Komponente | Replicas | CPU/Memory pro Pod | Autoscaling-Trigger |
|------------|----------|---------------------|---------------------|
| **FastAPI Backend** | 3–10 | 1 CPU / 2 GB | HPA: CPU > 70% |
| **Celery Workers** | 2–8 | 1 CPU / 2 GB | HPA: Queue-Length |
| **Celery Beat** | 1 (Singleton) | 0.25 CPU / 512 MB | — (kein Scaling) |
| **Frontend (Nginx)** | 2–4 | 0.25 CPU / 256 MB | HPA: RPS |
| **Embedding Service (ONNX)** | 1–3 | 2 CPU / 4 GB | HPA: Latenz P95 > 500ms |
| **LLM Adapter** | 1–2 | 1 CPU / 2 GB | Optional GPU-Node |

### 4.2 GPU-Anforderungen (Optional)

Fuer lokale LLM-Inferenz (Ollama/vLLM) statt Cloud-API:

| Anforderung | Spezifikation |
|-------------|---------------|
| **GPU-Typ** | NVIDIA T4 (Minimum) / L4 / A10G |
| **VRAM** | >= 16 GB |
| **Einsatz** | LLM-Adapter, optional Embedding Service |
| **Fallback** | Cloud-LLM-API (Anthropic/OpenAI) ohne GPU |

---

## 5. Netzwerk & Security

### 5.1 Netzwerk-Architektur

| Anforderung | Spezifikation |
|-------------|---------------|
| **TLS Termination** | Cert-Manager + Let's Encrypt (oder Cloud-CA) |
| **Network Policies** | Calico/Cilium — Namespace-Isolierung, DB-Pods nur von App-Pods erreichbar |
| **WAF** | Cloud-WAF vor Ingress (OWASP Top 10) |
| **DDoS Protection** | Cloud-native (AWS Shield / GCP Armor / Azure DDoS Protection) |
| **Private Subnets** | DB-Nodes nicht oeffentlich erreichbar |
| **MQTT Broker** | EMQX/Mosquitto fuer IoT-Sensorik (REQ-005, REQ-018) |

### 5.2 Secret Management

| Anforderung | Spezifikation |
|-------------|---------------|
| **Methode** | External Secrets Operator → Cloud KMS |
| **Optionen** | HashiCorp Vault / AWS Secrets Manager / GCP Secret Manager / Azure Key Vault |
| **Rotation** | Automatische Secret-Rotation fuer DB-Credentials |
| **Verbot** | Keine Secrets in Git, ConfigMaps oder Umgebungsvariablen im Klartext |

### 5.3 Pod Security

| Anforderung | Spezifikation |
|-------------|---------------|
| **Security Context** | runAsNonRoot, readOnlyRootFilesystem, allowPrivilegeEscalation: false |
| **Seccomp** | RuntimeDefault-Profil (NFR-002) |
| **RBAC** | K8s RBAC + Cloud IAM, ServiceAccounts pro Workload |
| **Image Policy** | Nur signierte Images aus privater Registry |

---

## 6. Observability (Referenz: NFR-007)

### 6.1 Monitoring-Stack

| Komponente | Zweck | Managed-Option |
|------------|-------|----------------|
| **Prometheus** | Metriken (SLIs: Verfuegbarkeit, Latenz, Error Rate) | Grafana Cloud / Datadog |
| **Alertmanager** | Eskalation (P1→P4 Severity) | PagerDuty-Integration |
| **Grafana** | Dashboards, SLO-Tracking, Error-Budget-Burn-Rate | Grafana Cloud |
| **Fluentd/Fluent Bit** | Log-Aggregation (stdout → zentrale Plattform) | Cloud Logging / ELK / Loki |
| **Sentry** | Error Tracking (optional, Consent-pflichtig gemaess REQ-025) | Sentry SaaS |
| **Statuspage** | Externe Verfuegbarkeitsanzeige fuer Stakeholder | Atlassian Statuspage / Instatus |

### 6.2 SLO-Ziele (aus NFR-007)

| SLO | Ziel | Error Budget (30 Tage) |
|-----|------|------------------------|
| **Verfuegbarkeit** | >= 99,5 % | 3 Stunden 36 Minuten Downtime |
| **Latenz P50** | < 200 ms | — |
| **Latenz P95** | < 500 ms | — |
| **Latenz P99** | < 1.000 ms | — |
| **Error Rate** | < 1 % der Requests mit 5xx | — |
| **Throughput** | >= 50 Requests/s ohne Degradation | — |

---

## 7. DSGVO & Compliance

### 7.1 Hosting-Anforderungen

| Anforderung | Spezifikation | Rechtsgrundlage |
|-------------|---------------|-----------------|
| **Datenstandort** | **EU-Region Pflicht** | DSGVO Art. 44ff |
| **Encryption at Rest** | AES-256 auf allen Volumes | Art. 32 DSGVO |
| **Encryption in Transit** | TLS 1.3 zwischen allen Services | Art. 32 DSGVO |
| **Backup-Verschluesselung** | Encrypted Snapshots, Geo-Redundanz innerhalb EU | Art. 32 DSGVO |
| **Audit Logging** | Cloud-Audit-Trail fuer alle Admin-Operationen | Art. 5(2) Rechenschaftspflicht |
| **Key Management** | Cloud KMS mit Customer-Managed Keys (CMK) | Art. 32 DSGVO |

### 7.2 Vertragliche Anforderungen

| Anforderung | Spezifikation |
|-------------|---------------|
| **DPA** | Auftragsverarbeitungsvertrag (Art. 28 DSGVO) mit Cloud-Provider |
| **Zertifizierungen** | ISO 27001, SOC 2 Typ II, C5 (BSI) |
| **Sub-Auftragsverarbeiter** | Transparente Liste, Widerspruchsrecht |
| **Datenlokalisierung** | Keine Verarbeitung ausserhalb EU/EWR ohne Angemessenheitsbeschluss |

### 7.3 Technische DSGVO-Massnahmen

| Massnahme | Spezifikation | Referenz |
|-----------|---------------|----------|
| **IP-Anonymisierung** | IPv4 letztes Oktett → 0, IPv6 → /48-Praefix, nach 7 Tagen | NFR-011 R-03 |
| **Retention Enforcement** | Celery Master-Task, taegliche Ausfuehrung | NFR-011 §3 |
| **Sensordaten-Downsampling** | 90d raw → 2y hourly → 5y daily | NFR-011 §2.2 |
| **Consent-Middleware** | Optionale Features nur mit aktiver Einwilligung | REQ-025 |
| **Betroffenenrechte** | Self-Service API /api/v1/privacy/ (Art. 15–21) | REQ-025 |

---

## 8. CI/CD & DevOps

| Anforderung | Spezifikation |
|-------------|---------------|
| **Container Registry** | Private Registry (Harbor / ECR / GCR / ACR) |
| **CI** | GitHub Actions (bereits spezifiziert) |
| **CD** | Helm + Skaffold (bestehend), ArgoCD fuer GitOps empfohlen |
| **Image Scanning** | Trivy / Snyk bei jedem Build |
| **Preview Environments** | Ephemeral Namespace pro Pull Request |
| **Rollback** | Helm Rollback, Ziel: < 30s Rollback-Zeit |
| **Deployment-Strategie** | Rolling Update (maxSurge: 1, maxUnavailable: 0) |

---

## 9. Backup & Disaster Recovery

### 9.1 RPO/RTO-Ziele

| Kategorie | RPO | RTO | Backup-Methode |
|-----------|-----|-----|----------------|
| **ArangoDB** | 1h | 4h | Cluster-Replikation + taeglicher Snapshot |
| **TimescaleDB** | 1h | 4h | Streaming Replication + WAL Archiving |
| **pgvector/PostgreSQL** | 24h | 8h | Daily Snapshot |
| **Redis** | Ephemeral (kein RPO) | 15min | Neu aufbauen aus DB |
| **Konfiguration** | Git (RPO=0) | 30min | Helm re-deploy aus Git |

### 9.2 Disaster-Recovery-Strategie

| Massnahme | Spezifikation |
|-----------|---------------|
| **Multi-AZ** | Alle Stateful-Workloads ueber mindestens 2 Availability Zones |
| **Cross-Region Backup** | Taegliche Snapshot-Kopie in zweite EU-Region |
| **Recovery-Tests** | Quartalsweiser DR-Test mit dokumentiertem Ergebnis |
| **Runbook** | Dokumentierter Recovery-Prozess pro Service |

---

## 10. Skalierungsprofil

### 10.1 Skalierungsstufen

| Szenario | Tenant-Zahl | Pflanzen | Sensoren | Backend-Pods | DB-Storage |
|----------|-------------|----------|----------|-------------|------------|
| **Small** | 1–10 | 500 | 50 | 3 | 100 GB |
| **Medium** | 10–100 | 5.000 | 500 | 5–10 | 500 GB |
| **Large** | 100–1.000 | 50.000 | 5.000 | 10–30 | 2 TB |
| **Enterprise** | 1.000+ | 500.000+ | 50.000+ | 30–100 | 10 TB+ |

### 10.2 Skalierungstrigger

| Metrik | Schwellwert | Aktion |
|--------|------------|--------|
| CPU-Auslastung Backend | > 70% ueber 5 Minuten | HPA: +1 Pod |
| Celery Queue Length | > 100 pending Tasks | HPA: +1 Worker |
| ArangoDB Disk Usage | > 80% | Alert + Storage erweitern |
| TimescaleDB Disk Usage | > 75% | Alert + Retention pruefen |
| API Latenz P95 | > 500ms ueber 10 Minuten | HPA + Investigate |

---

## 11. Cloud-Provider-Vergleich

### 11.1 Feature-Matrix

| Kriterium | AWS | GCP | Azure | Hetzner Cloud |
|-----------|-----|-----|-------|---------------|
| **Managed K8s** | EKS | GKE (Autopilot) | AKS | k3s (self-managed) |
| **ArangoDB Managed** | Oasis | Oasis | Oasis | Self-hosted |
| **TimescaleDB Managed** | Timescale Cloud | Timescale Cloud | Timescale Cloud | Self-hosted |
| **Redis Managed** | ElastiCache | Memorystore | Azure Cache | Self-hosted |
| **EU-Region** | Frankfurt (eu-central-1) | europe-west3 (Frankfurt) | West Europe (NL) | Falkenstein/Nuernberg |
| **DPA/C5** | Ja | Ja | Ja | Ja (eingeschraenkt) |
| **GPU (LLM)** | p4d/g5 | L4/T4 | NC-Series | Nein |
| **WAF** | AWS WAF | Cloud Armor | Azure WAF | Nein (extern noetig) |
| **Secret Manager** | Secrets Manager | Secret Manager | Key Vault | Nein (Vault noetig) |

### 11.2 Kostenschaetzung (monatlich, Medium-Szenario)

| Posten | AWS | GCP | Azure | Hetzner |
|--------|-----|-----|-------|---------|
| **Managed K8s (6 Nodes)** | ~600 EUR | ~550 EUR | ~600 EUR | ~150 EUR |
| **ArangoDB Cluster (3x50GB)** | ~300 EUR | ~300 EUR | ~300 EUR | ~80 EUR |
| **TimescaleDB (100GB)** | ~200 EUR | ~200 EUR | ~200 EUR | ~40 EUR |
| **Redis (2GB)** | ~80 EUR | ~70 EUR | ~80 EUR | ~10 EUR |
| **Load Balancer + Ingress** | ~50 EUR | ~30 EUR | ~50 EUR | ~20 EUR |
| **Storage (SSD)** | ~100 EUR | ~90 EUR | ~100 EUR | ~30 EUR |
| **Monitoring (Grafana Cloud)** | ~100 EUR | ~100 EUR | ~100 EUR | ~100 EUR |
| **Summe (geschaetzt)** | **~1.430 EUR** | **~1.340 EUR** | **~1.430 EUR** | **~430 EUR** |

**Hinweis:** Hetzner erfordert signifikant hoeheren Ops-Aufwand (Self-Managed Datenbanken, kein managed Redis/TimescaleDB, kein Cloud-WAF). Die Kostenersparnis wird teilweise durch Personalkosten kompensiert.

### 11.3 Empfehlung

| Szenario | Empfohlener Provider | Begruendung |
|----------|---------------------|-------------|
| **Startup/Small** | Hetzner Cloud + k3s | Kostenguenstig, EU-Standort, ausreichend fuer <10 Tenants |
| **Medium** | GKE Autopilot | Bestes Preis-Leistungs-Verhaeltnis, starkes Autoscaling |
| **Large/Enterprise** | EKS oder GKE | Volle Managed-Services, GPU-Verfuegbarkeit, SLA-Garantien |
| **Reguliert (CanG)** | AWS (C5) oder Azure | Hoechste Zertifizierungsdichte, Compliance-Tools |

---

## 12. Zusammenfassung der Mindestanforderungen

Ein Cloud-Provider fuer den Enterprise-Betrieb von Kamerplanter **MUSS** folgende Anforderungen erfuellen:

1. **Managed Kubernetes** (1.28+) mit Autoscaling und NetworkPolicies
2. **EU-Rechenzentrum** (DSGVO-Pflicht) mit DPA und ISO 27001 / C5
3. **Persistent SSD-Storage** (>= 3.000 IOPS) fuer ArangoDB und TimescaleDB
4. **Private Networking** — Datenbanken nicht oeffentlich erreichbar
5. **Secret Management** via Cloud KMS (keine Secrets in Git oder ConfigMaps)
6. **Observability-Stack** (Prometheus/Grafana/Alertmanager) fuer SLO-Tracking
7. **Backup mit RPO <= 1h** fuer alle Stateful Services
8. **TLS 1.3** auf allen Verbindungen (Ingress, Service-to-Service, DB)
9. **Container Registry** mit automatischem Image-Scanning
10. **Mindestens 6 Nodes** (3 Stateless + 3 Stateful) fuer Production-HA
