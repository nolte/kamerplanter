---

ID: NFR-002
Titel: Kubernetes-basierte Ausführungsplattform
Kategorie: Infrastruktur / Deployment Unterkategorie: Container-Orchestrierung, Skalierung, CI/CD Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14, ArangoDB, Kubernetes 1.28+, Helm, Docker, Traefik
Status: Entwurf
Priorität: Kritisch
Version: 2.1
Autor: Business Analyst - Agrotech
Datum: 2026-02-27
Tags: [kubernetes, helm, docker, deployment, scaling, high-availability, ci-cd, network-policies, seccomp, container-security]
Abhängigkeiten: [NFR-001]
Betroffene Module: [ALL]
---

# NFR-002: Kubernetes-basierte Ausführungsplattform

## 1. Business Case

### 1.1 User Stories

**Als** DevOps Engineer  
**möchte ich** dass die Agrotech-Anwendung vollständig containerisiert auf Kubernetes läuft  
**um** horizontale Skalierung, Hochverfügbarkeit und automatisierte Rollouts zu ermöglichen.

**Als** Systemadministrator  
**möchte ich** dass alle Komponenten über Helm Charts deploybar sind  
**um** konsistente Deployments über Dev/Staging/Production zu gewährleisten.

**Als** Entwickler  
**möchte ich** dass die lokale Entwicklungsumgebung der Production-Infrastruktur ähnelt  
**um** "Works on my machine"-Probleme zu vermeiden.

### 1.2 Geschäftliche Motivation

Die Kubernetes-basierte Plattform ermöglicht:

1. **Cloud-Unabhängigkeit**: Deployment auf AWS, GCP, Azure oder On-Premise
2. **Kosteneffizienz**: Automatische Skalierung verhindert Over-Provisioning
3. **Zero-Downtime Deployments**: Rolling Updates ohne Service-Unterbrechung
4. **Disaster Recovery**: Schnelle Wiederherstellung durch deklarative Manifests
5. **Multi-Tenancy**: Isolierte Namespaces für verschiedene Kunden/Farmen

### 1.3 Fachliche Beschreibung

**Szenario**: Eine kommerzielle Farm betreibt 5 Gewächshäuser mit jeweils 200 Pflanzen.

- **Normale Last**: 3 Backend-Pods, 2 Worker-Pods
- **Erntezeit** (hohe Aktivität): Automatische Skalierung auf 10 Backend-Pods
- **Nachts** (niedrige Last): Scale-down auf 2 Pods zur Kostenoptimierung

Kubernetes orchestriert dies automatisch basierend auf CPU/Memory/Custom-Metrics.

---

## 2. Architekturprinzipien

### 2.1 Containerisierungspflicht

**12-Factor-App Compliance**:

|Faktor|Implementierung|
|---|---|
|**I. Codebase**|Git Repository, ein Codebase pro Service|
|**II. Dependencies**|requirements.txt, package.json|
|**III. Config**|ConfigMaps, Secrets (nie im Code)|
|**IV. Backing Services**|ArangoDB, Redis als attachable Resources|
|**V. Build/Release/Run**|Docker Build → Helm Release → K8s Run|
|**VI. Processes**|Stateless Pods, State in Datenbanken|
|**VII. Port Binding**|Services exponieren Ports (8000, 8529)|
|**VIII. Concurrency**|HPA für horizontale Skalierung|
|**IX. Disposability**|Graceful Shutdown, Fast Startup|
|**X. Dev/Prod Parity**|Gleiche Container in allen Umgebungen|
|**XI. Logs**|stdout/stderr → Fluentd → Elasticsearch|
|**XII. Admin Processes**|Kubernetes Jobs für Migrationen|

### 2.2 Stateless vs. Stateful

```
┌─────────────────────────────────────────────────────────┐
│                    STATELESS TIER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Backend Pod │  │  Backend Pod │  │  Backend Pod │ │
│  │  (Replica 1) │  │  (Replica 2) │  │  (Replica 3) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓ Deployment (kann gekillt werden)             │
└─────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────┐
│                    STATEFUL TIER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  ArangoDB-0  │  │  ArangoDB-1  │  │  ArangoDB-2  │ │
│  │     PVC-0    │  │     PVC-1    │  │     PVC-2    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓ StatefulSet (geordnete Identitäten)          │
└─────────────────────────────────────────────────────────┘
```

**Stateless Components** (Deployment):

- FastAPI Backend
- Frontend (Nginx)
- Celery Worker

**Stateful Components** (StatefulSet):

- ArangoDB Cluster
- Redis (optional, kann auch Deployment sein)
- TimescaleDB

---

## 3. Kubernetes-Ressourcen

### 3.1 Namespaces (Umgebungsisolation)

```yaml
# k8s/base/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agrotech-dev
  labels:
    environment: development
    team: agrotech
---
apiVersion: v1
kind: Namespace
metadata:
  name: agrotech-staging
  labels:
    environment: staging
    team: agrotech
---
apiVersion: v1
kind: Namespace
metadata:
  name: agrotech-prod
  labels:
    environment: production
    team: agrotech
    monitoring: enabled
```

**Namespace-Strategie**:

- **dev**: Entwickler-Testing, keine Ressourcen-Limits
- **staging**: Pre-Production, identisch zu Prod
- **prod**: Production, strenge Limits, Monitoring

### 3.2 Deployments (Stateless Workloads)

**Beispiel: Backend API Deployment (ohne Helm)**:

```yaml
# k8s/backend/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agrotech-backend
  namespace: agrotech-prod
  labels:
    app: backend
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Maximal 4 Pods während Update
      maxUnavailable: 0  # Mindestens 3 Pods immer verfügbar
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      # Service Account für RBAC
      serviceAccountName: backend-sa
      
      # Security Context (Pod-Level)
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      
      # Init Container (z.B. DB-Migrations)
      initContainers:
      - name: wait-for-arangodb
        image: busybox:1.36
        command:
          - sh
          - -c
          - |
            until nc -z arangodb 8529; do
              echo "Waiting for ArangoDB..."
              sleep 2
            done
      
      # Main Container
      containers:
      - name: backend
        image: agrotech/backend:1.0.0
        imagePullPolicy: IfNotPresent
        
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        
        # Environment Variables
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: ARANGODB_URL
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: url
        - name: ARANGODB_USER
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: user
        - name: ARANGODB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: password
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: jwt-secret
        
        # Probes
        livenessProbe:
          httpGet:
            path: /health/live
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        startupProbe:
          httpGet:
            path: /health/startup
            port: http
          initialDelaySeconds: 0
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 30  # 150 Sekunden max Startup-Zeit
        
        # Resource Management
        resources:
          requests:
            cpu: 250m      # 0.25 CPU cores
            memory: 512Mi
          limits:
            cpu: 1000m     # 1 CPU core
            memory: 1Gi
        
        # Security Context (Container-Level) — SEC-M-004
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          seccompProfile:
            type: RuntimeDefault
          capabilities:
            drop:
              - ALL
        
        # Volume Mounts
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/.cache
      
      # Volumes
      volumes:
      - name: tmp
        emptyDir:
          medium: Memory
      - name: cache
        emptyDir: {}
      
      # Pod Disruption Budget (separat definiert)
      # Node Affinity (optional für Multi-Zone)
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - backend
              topologyKey: kubernetes.io/hostname
```

**Health Check Endpoints (FastAPI)**:

```python
# backend/main.py
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness():
    """
    Liveness Probe: Ist der Container am Leben?
    Gibt 200 zurück wenn der Prozess läuft.
    """
    return {"status": "alive"}

@app.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness():
    """
    Readiness Probe: Ist der Service bereit Traffic zu empfangen?
    Prüft DB-Verbindung, Cache, etc.
    """
    # Prüfe kritische Dependencies
    try:
        await check_arangodb_connection()
        await check_redis_connection()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/health/startup", status_code=status.HTTP_200_OK)
async def startup():
    """
    Startup Probe: Ist die Applikation vollständig gestartet?
    Erlaubt längere Startup-Zeiten.
    """
    if not app_fully_initialized:
        raise HTTPException(status_code=503, detail="Still starting")
    return {"status": "started"}
```

### 3.3 StatefulSets (Stateful Workloads)

**ArangoDB Cluster StatefulSet**:

```yaml
# k8s/arangodb/statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: arangodb
  namespace: agrotech-prod
spec:
  serviceName: arangodb-headless
  replicas: 3
  selector:
    matchLabels:
      app: arangodb
  template:
    metadata:
      labels:
        app: arangodb
    spec:
      containers:
      - name: arangodb
        image: arangodb:3.11
        ports:
        - containerPort: 8529
          name: http
        env:
        - name: ARANGO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arangodb-credentials
              key: password
        - name: ARANGO_STORAGE_ENGINE
          value: "rocksdb"
        volumeMounts:
        - name: data
          mountPath: /var/lib/arangodb3
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

**Wichtig bei StatefulSets**:

- **Geordnete Identitäten**: arangodb-0, arangodb-1, arangodb-2
- **Persistente PVCs**: Überleben Pod-Neustarts
- **Headless Service**: Für Cluster-Kommunikation

### 3.4 Services

**ClusterIP Service (intern)**:

```yaml
# k8s/backend/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: agrotech-prod
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: http
    protocol: TCP
    name: http
```

**Headless Service (für StatefulSets)**:

```yaml
# k8s/arangodb/service-headless.yaml
apiVersion: v1
kind: Service
metadata:
  name: arangodb-headless
  namespace: agrotech-prod
spec:
  clusterIP: None  # Headless!
  selector:
    app: arangodb
  ports:
  - port: 8529
    name: http
```

**DNS-Auflösung in Headless Services**:

```
arangodb-0.arangodb-headless.agrotech-prod.svc.cluster.local
arangodb-1.arangodb-headless.agrotech-prod.svc.cluster.local
arangodb-2.arangodb-headless.agrotech-prod.svc.cluster.local
```

### 3.5 Ingress (Externer Zugriff)

**Traefik Ingress für API**:

```yaml
# k8s/backend/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
  namespace: agrotech-prod
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.middlewares: |
      default-ratelimit@kubernetescrd,
      default-compress@kubernetescrd,
      default-security-headers@kubernetescrd
spec:
  ingressClassName: traefik
  tls:
  - hosts:
    - api.agrotech.example.com
    secretName: api-tls
  rules:
  - host: api.agrotech.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

**Traefik Middleware (Rate Limiting)**:

```yaml
# k8s/traefik/middleware-ratelimit.yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: ratelimit
  namespace: default
spec:
  rateLimit:
    average: 100
    period: 1m
    burst: 50
```

### 3.6 ConfigMaps

```yaml
# k8s/backend/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: agrotech-prod
data:
  # Application Settings
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
  
  # Feature Flags
  FEATURE_ML_PREDICTIONS: "true"
  FEATURE_WEATHER_API: "true"
  
  # Non-sensitive URLs
  SENTRY_DSN: "https://public@sentry.io/12345"
  
  # Config Files
  app-config.yaml: |
    server:
      port: 8000
      workers: 4
    
    gdd:
      calculation_interval: 3600  # 1 hour
    
    irrigation:
      check_interval: 900  # 15 minutes
```

**Nutzung in Pods**:

```yaml
# Als Environment Variables
env:
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: backend-config
      key: LOG_LEVEL

# Als Volume (für Config Files)
volumes:
- name: config
  configMap:
    name: backend-config
    items:
    - key: app-config.yaml
      path: config.yaml
```

### 3.7 Secrets

```yaml
# k8s/backend/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
  namespace: agrotech-prod
type: Opaque
stringData:
  jwt-secret: "supersecret-change-in-production"
  sentry-auth-token: "token-here"
```

**WICHTIG**: Secrets sollten **NIEMALS** im Git-Repository liegen!

**Alternativen**:

1. **Sealed Secrets**: Verschlüsselte Secrets in Git
2. **External Secrets Operator**: Sync von Vault/AWS Secrets Manager
3. **SOPS**: Verschlüsselung mit Age/PGP

---

## 4. Skalierungsanforderungen

### 4.1 Horizontal Pod Autoscaler (HPA)

```yaml
# k8s/backend/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: agrotech-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agrotech-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 Minuten
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

**Custom Metrics (Prometheus Adapter)**:

```yaml
# k8s/monitoring/prometheus-adapter-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: adapter-config
  namespace: monitoring
data:
  config.yaml: |
    rules:
    - seriesQuery: 'http_requests_total{namespace="agrotech-prod"}'
      resources:
        overrides:
          namespace: {resource: "namespace"}
          pod: {resource: "pod"}
      name:
        matches: "^(.*)_total$"
        as: "${1}_per_second"
      metricsQuery: 'sum(rate(<<.Series>>{<<.LabelMatchers>>}[2m])) by (<<.GroupBy>>)'
```

### 4.2 Vertical Pod Autoscaler (VPA)

```yaml
# k8s/backend/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
  namespace: agrotech-prod
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agrotech-backend
  updatePolicy:
    updateMode: "Auto"  # "Initial", "Recreate", "Off"
  resourcePolicy:
    containerPolicies:
    - containerName: backend
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2000m
        memory: 2Gi
      controlledResources:
      - cpu
      - memory
```

**WICHTIG**: HPA und VPA nicht gleichzeitig auf CPU/Memory verwenden!

### 4.3 Pod Disruption Budget (PDB)

```yaml
# k8s/backend/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
  namespace: agrotech-prod
spec:
  minAvailable: 2  # Mindestens 2 Pods müssen immer laufen
  selector:
    matchLabels:
      app: backend
```

**Verhindert**:

- Zu viele Pods werden gleichzeitig während Node-Drains entfernt
- Service-Unterbrechungen bei Cluster-Upgrades

---

## 5. Helm Charts Integration

### 5.1 Warum Helm?

**Vorteile**:

- **Templating**: Wiederverwendbare Manifests
- **Versionierung**: Rollback zu vorherigen Versionen
- **Parametrisierung**: Unterschiedliche Values für Dev/Staging/Prod
- **Dependency Management**: Sub-Charts (z.B. Redis, PostgreSQL)

### 5.2 Backend Helm Chart mit bjw-s/common

**Chart.yaml**:

```yaml
# helm/agrotech-backend/Chart.yaml
apiVersion: v2
name: agrotech-backend
description: Agrotech Plant Care Backend API
type: application
version: 1.0.0
appVersion: "1.0.0"

dependencies:
  - name: common
    repository: https://bjw-s.github.io/helm-charts
    version: 3.0.0
```

**values.yaml** (vereinfacht mit bjw-s/common):

```yaml
# helm/agrotech-backend/values.yaml
controllers:
  main:
    type: deployment
    replicas: 3
    
    strategy:
      type: RollingUpdate
    
    containers:
      main:
        image:
          repository: agrotech/backend
          tag: "1.0.0"
        
        env:
          - name: ARANGODB_URL
            valueFrom:
              secretKeyRef:
                name: arangodb-credentials
                key: url
          - name: REDIS_URL
            value: "redis://redis:6379/0"
        
        probes:
          liveness:
            enabled: true
            type: http
            path: /health/live
            port: 8000
          readiness:
            enabled: true
            type: http
            path: /health/ready
            port: 8000
          startup:
            enabled: true
            type: http
            path: /health/startup
            port: 8000
        
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi

service:
  main:
    controller: main
    type: ClusterIP
    ports:
      http:
        port: 8000

ingress:
  main:
    enabled: true
    className: traefik
    hosts:
      - host: api.agrotech.example.com
        paths:
          - path: /
            pathType: Prefix
            service:
              identifier: main
              port: http

autoscaling:
  enabled: true
  target: main
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

**Deployment**:

```bash
# Dependencies installieren
helm dependency build helm/agrotech-backend

# Deployment
helm upgrade --install agrotech-backend \
  ./helm/agrotech-backend \
  --namespace agrotech-prod \
  --create-namespace \
  --values ./helm/agrotech-backend/values-prod.yaml \
  --atomic \
  --timeout 10m
```

---

## 6. Observability & Monitoring

### 6.1 Prometheus & Grafana

**ServiceMonitor für Prometheus Operator**:

```yaml
# k8s/monitoring/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-metrics
  namespace: agrotech-prod
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

**Prometheus Metrics im Backend**:

```python
# backend/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Duration',
    ['method', 'endpoint']
)

active_plants_total = Gauge(
    'active_plants_total',
    'Number of active plants'
)

irrigation_events_total = Counter(
    'irrigation_events_total',
    'Total irrigation events',
    ['location', 'manual']
)

# Endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 6.2 Logging (Fluentd → Elasticsearch → Kibana)

**Fluentd DaemonSet**:

```yaml
# k8s/logging/fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      serviceAccountName: fluentd
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch.logging.svc.cluster.local"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        - name: FLUENT_ELASTICSEARCH_SCHEME
          value: "http"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: containers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: containers
        hostPath:
          path: /var/lib/docker/containers
```

**Strukturiertes Logging im Backend**:

```python
# backend/logging_config.py
import structlog
import logging

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()  # JSON für Elasticsearch
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Verwendung
logger.info(
    "plant_created",
    plant_id="abc-123",
    species="tomato",
    location="greenhouse-a",
    user_id="user-456"
)
```

### 6.3 Distributed Tracing (Jaeger)

```yaml
# k8s/monitoring/jaeger.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:1.51
        env:
        - name: COLLECTOR_OTLP_ENABLED
          value: "true"
        ports:
        - containerPort: 16686  # UI
        - containerPort: 4318   # OTLP HTTP
```

**OpenTelemetry im Backend**:

```python
# backend/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def init_tracing():
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    # Auto-Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

# Verwendung
tracer = trace.get_tracer(__name__)

@app.get("/plants/{plant_id}")
async def get_plant(plant_id: str):
    with tracer.start_as_current_span("get_plant") as span:
        span.set_attribute("plant.id", plant_id)
        # ... Business Logic
```

---

## 7. Security Best Practices

### 7.1 Network Policies

> **Referenz:** SEC-M-004 (IT-Security-Review)

**Default-Deny-Policy (Namespace-Level):**

Alle Pods im Namespace starten ohne jegliche Netzwerkverbindung. Erlaubte Verbindungen werden explizit durch die nachfolgenden Policies freigeschaltet.

```yaml
# k8s/network-policies/default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: agrotech-prod
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

**Backend Network Policy:**

```yaml
# k8s/network-policies/backend-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: agrotech-prod
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress

  ingress:
  # Nur Traefik darf auf Backend zugreifen
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          app: traefik
    ports:
    - protocol: TCP
      port: 8000

  egress:
  # Backend → ArangoDB
  - to:
    - podSelector:
        matchLabels:
          app: arangodb
    ports:
    - protocol: TCP
      port: 8529
  # Backend → Redis
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # Backend → TimescaleDB
  - to:
    - podSelector:
        matchLabels:
          app: timescaledb
    ports:
    - protocol: TCP
      port: 5432
  # Backend → MQTT-Broker
  - to:
    - podSelector:
        matchLabels:
          app: mqtt
    ports:
    - protocol: TCP
      port: 8883
  # Backend → DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
  # Backend → Externe APIs (GBIF, Perenual, OIDC-Provider, Sentry, HIBP)
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 10.0.0.0/8
        - 172.16.0.0/12
        - 192.168.0.0/16
    ports:
    - protocol: TCP
      port: 443
```

**Frontend Network Policy:**

```yaml
# k8s/network-policies/frontend-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-policy
  namespace: agrotech-prod
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  - Egress

  ingress:
  # Nur Traefik darf auf Frontend zugreifen
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          app: traefik
    ports:
    - protocol: TCP
      port: 80

  egress:
  # Frontend (Nginx) braucht keine Egress-Verbindungen
  # Statische Assets werden direkt ausgeliefert
  # DNS für Health-Checks
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

**Hinweis:** Die Egress-Regel für externe APIs (`0.0.0.0/0:443`) erlaubt dem Backend HTTPS-Verbindungen zu Diensten wie GBIF, Perenual (REQ-011), OIDC-Providern (REQ-023), HaveIBeenPwned (REQ-023), und Sentry (NFR-001 §8.3). Private IP-Bereiche werden explizit ausgeschlossen, um Lateral Movement zu verhindern.

### 7.2 Pod Security Standards

```yaml
# k8s/backend/pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agrotech-prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Restricted Profile erfordert**:

- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`
- `capabilities: drop: [ALL]`
- `seccompProfile: type: RuntimeDefault`

### 7.3 RBAC (Role-Based Access Control)

```yaml
# k8s/backend/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: agrotech-prod
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: agrotech-prod
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-rolebinding
  namespace: agrotech-prod
subjects:
- kind: ServiceAccount
  name: backend-sa
roleRef:
  kind: Role
  name: backend-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 8. Disaster Recovery & Backup

### 8.1 Velero (Backup & Restore)

```yaml
# k8s/backup/velero-schedule.yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: agrotech-daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 02:00 Uhr täglich
  template:
    includedNamespaces:
    - agrotech-prod
    storageLocation: default
    volumeSnapshotLocations:
    - default
    ttl: 720h  # 30 Tage
```

**Installation**:

```bash
# Velero CLI installieren
brew install velero

# Velero in Cluster installieren
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket agrotech-backups \
  --secret-file ./credentials-velero \
  --backup-location-config region=eu-central-1
```

**Restore**:

```bash
# Liste Backups
velero backup get

# Restore kompletter Namespace
velero restore create --from-backup agrotech-daily-backup-20260225020000

# Restore einzelne Resource
velero restore create --from-backup agrotech-daily-backup-20260225020000 \
  --include-resources persistentvolumeclaims \
  --selector app=arangodb
```

### 8.2 ArangoDB Backup CronJob

```yaml
# k8s/arangodb/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: arangodb-backup
  namespace: agrotech-prod
spec:
  schedule: "0 3 * * *"  # 03:00 Uhr täglich
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: arangodb:3.11
            command:
            - /bin/sh
            - -c
            - |
              arangodump \
                --server.endpoint tcp://arangodb-0.arangodb-headless:8529 \
                --server.database agrotech_db \
                --server.username root \
                --server.password "$ARANGO_PASSWORD" \
                --output-directory /backup/$(date +%Y%m%d_%H%M%S)
              
              # Upload zu S3
              aws s3 sync /backup s3://agrotech-backups/arangodb/
            env:
            - name: ARANGO_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: arangodb-credentials
                  key: password
            volumeMounts:
            - name: backup
              mountPath: /backup
          volumes:
          - name: backup
            emptyDir: {}
```

---

## 9. Multi-Environment Setup

### 9.1 Kustomize Overlays

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    │       └── deployment.yaml
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patches/
    └── prod/
        ├── kustomization.yaml
        └── patches/
            ├── deployment.yaml
            └── resources.yaml
```

**base/kustomization.yaml**:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
- configmap.yaml

commonLabels:
  app: backend
  managed-by: kustomize
```

**overlays/prod/kustomization.yaml**:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
- ../../base

namespace: agrotech-prod

replicas:
- name: agrotech-backend
  count: 5

images:
- name: agrotech/backend
  newTag: v1.0.0

patches:
- path: patches/resources.yaml
```

**Deployment**:

```bash
# Dev
kubectl apply -k k8s/overlays/dev

# Staging
kubectl apply -k k8s/overlays/staging

# Prod
kubectl apply -k k8s/overlays/prod
```

### 9.2 Helmfile (Multi-Chart Management)

```yaml
# helmfile.yaml
repositories:
- name: bjw-s
  url: https://bjw-s.github.io/helm-charts
- name: bitnami
  url: https://charts.bitnami.com/bitnami

environments:
  dev:
    values:
    - environments/dev.yaml
  staging:
    values:
    - environments/staging.yaml
  prod:
    values:
    - environments/prod.yaml

releases:
- name: agrotech-backend
  namespace: agrotech-{{ .Environment.Name }}
  chart: ./helm/agrotech-backend
  values:
  - helm/agrotech-backend/values.yaml
  - helm/agrotech-backend/values-{{ .Environment.Name }}.yaml

- name: redis
  namespace: agrotech-{{ .Environment.Name }}
  chart: bitnami/redis
  version: 18.0.0
  values:
  - helm/redis/values.yaml

- name: arangodb
  namespace: agrotech-{{ .Environment.Name }}
  chart: ./helm/agrotech-arangodb
  values:
  - helm/agrotech-arangodb/values.yaml
```

**Deployment**:

```bash
# Alle Releases in Production
helmfile -e prod sync

# Nur Backend
helmfile -e prod -l name=agrotech-backend sync

# Diff vor Deployment
helmfile -e prod diff
```

---

## 10. Cost Optimization

### 10.1 Cluster Autoscaler

```yaml
# k8s/autoscaling/cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.28.0
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --cloud-provider=aws
        - --namespace=kube-system
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/agrotech-prod
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

**Skaliert Nodes basierend auf**:

- Pending Pods (scale up)
- Unterausgelastete Nodes (scale down)

### 10.2 Spot Instances (AWS)

```yaml
# terraform/eks-node-groups.tf
resource "aws_eks_node_group" "spot" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "agrotech-spot"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids

  capacity_type = "SPOT"  # Bis zu 90% günstiger!

  scaling_config {
    desired_size = 2
    max_size     = 10
    min_size     = 1
  }

  instance_types = ["t3.medium", "t3a.medium"]  # Mehrere Typen für bessere Verfügbarkeit

  labels = {
    workload = "stateless"
    capacity = "spot"
  }

  taints {
    key    = "spot"
    value  = "true"
    effect = "NoSchedule"
  }
}
```

**Pods für Spot Instances**:

```yaml
# Backend toleriert Spot Instances
spec:
  tolerations:
  - key: "spot"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  
  nodeSelector:
    workload: stateless
```

### 10.3 Resource Quotas

```yaml
# k8s/namespaces/resourcequota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: agrotech-dev
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "5"
    pods: "50"
```

**Verhindert**:

- Entwickler überprovisionieren Dev-Umgebung
- Einzelner Service monopolisiert Cluster

---

## 11. Akzeptanzkriterien

### Definition of Done

- [ ] **Containerisierung**
    
    - [ ] Alle Services als Docker Container
    - [ ] Multi-Stage Builds für kleinere Images
    - [ ] Non-Root User in Containern
    - [ ] Health Checks implementiert
- [ ] **Kubernetes Resources**
    
    - [ ] Deployments für stateless Workloads
    - [ ] StatefulSets für Datenbanken
    - [ ] Services (ClusterIP, LoadBalancer)
    - [ ] Ingress mit TLS konfiguriert
- [ ] **Helm Charts**
    
    - [ ] Charts basieren auf bjw-s/common
    - [ ] Values für Dev/Staging/Prod
    - [ ] Dependencies definiert
    - [ ] Helm Tests vorhanden
- [ ] **Skalierung**
    
    - [ ] HPA konfiguriert (min 3, max 10 Pods)
    - [ ] PDB verhindert kompletten Ausfall
    - [ ] Resource Limits gesetzt
- [ ] **Security**

    - [ ] Default-Deny Network Policy aktiv im Namespace
    - [ ] Backend Network Policy aktiv (Ingress: nur Traefik, Egress: nur DB/Redis/MQTT/DNS/externe HTTPS)
    - [ ] Frontend Network Policy aktiv (Ingress: nur Traefik, Egress: nur DNS)
    - [ ] `seccompProfile: RuntimeDefault` in allen Container-Security-Contexts
    - [ ] Pod Security Standards enforced (`restricted` Profile)
    - [ ] RBAC konfiguriert
    - [ ] Secrets nicht in Git
- [ ] **Observability**
    
    - [ ] Prometheus Metrics exportiert
    - [ ] Strukturiertes Logging (JSON)
    - [ ] Distributed Tracing (Jaeger)
    - [ ] Grafana Dashboards
- [ ] **Backup & Recovery**
    
    - [ ] Velero konfiguriert
    - [ ] Tägliche Backups (02:00 Uhr)
    - [ ] Restore getestet
    - [ ] RTO < 2 Stunden

### Testszenarien

#### Szenario 1: Rolling Update ohne Downtime

```bash
# 1. Aktuelles Deployment
kubectl get pods -n agrotech-prod -l app=backend
# Output: 3 Pods running (v1.0.0)

# 2. Update auf neue Version
helm upgrade agrotech-backend ./helm/agrotech-backend \
  --set controllers.main.containers.main.image.tag=v1.1.0 \
  --namespace agrotech-prod

# 3. Watch Rollout
kubectl rollout status deployment/agrotech-backend -n agrotech-prod

# 4. Während Update: API bleibt erreichbar
while true; do curl -s https://api.agrotech.example.com/health/live; sleep 1; done
# Output: Durchgehend 200 OK

# 5. Verify neue Version
kubectl get pods -n agrotech-prod -l app=backend -o jsonpath='{.items[*].spec.containers[0].image}'
# Output: agrotech/backend:v1.1.0
```

#### Szenario 2: Auto-Scaling bei Last

```bash
# 1. Initiale Replicas
kubectl get hpa -n agrotech-prod
# Output: backend-hpa   3/10   50%   70%

# 2. Lasttest starten
kubectl run -it --rm load-generator --image=busybox /bin/sh
# In Pod:
while true; do wget -q -O- http://backend:8000/api/v1/plants; done

# 3. HPA beobachten
kubectl get hpa -n agrotech-prod --watch
# Output:
# backend-hpa   3/10   50%   → 75%   → 85%
# backend-hpa   5/10   (scaled up)
# backend-hpa   7/10   (scaled up)

# 4. Last stoppen
# Output:
# backend-hpa   7/10   85% → 60% → 45%
# backend-hpa   5/10   (scaled down after 5 min)
```

#### Szenario 3: Pod Failure Recovery

```bash
# 1. Lösche einen Pod
kubectl delete pod agrotech-backend-xyz123 -n agrotech-prod

# 2. Deployment erstellt automatisch neuen Pod
kubectl get pods -n agrotech-prod -l app=backend --watch
# Output:
# agrotech-backend-xyz123   1/1   Terminating
# agrotech-backend-abc789   0/1   ContainerCreating
# agrotech-backend-abc789   1/1   Running

# 3. Service bleibt verfügbar (PDB!)
curl https://api.agrotech.example.com/health/live
# Output: 200 OK
```

#### Szenario 4: Backup & Restore

```bash
# 1. Backup erstellen
velero backup create manual-backup --include-namespaces agrotech-prod

# 2. Simulate Disaster (Namespace löschen)
kubectl delete namespace agrotech-prod

# 3. Restore
velero restore create --from-backup manual-backup

# 4. Verify
kubectl get all -n agrotech-prod
# Output: Alle Resources wiederhergestellt
```

#### Szenario 5: Network Policy Enforcement

```bash
# 1. Test: Frontend kann Backend erreichen
kubectl run -it --rm test-frontend --image=busybox -n agrotech-prod -- wget -O- http://backend:8000/health/live
# Output: 200 OK (erlaubt durch Network Policy)

# 2. Test: External Pod kann Backend NICHT erreichen
kubectl run -it --rm test-external --image=busybox -n default -- wget -O- http://backend.agrotech-prod:8000/health/live
# Output: Timeout (blockiert durch Network Policy)
```

---

## 12. Risiken bei Nicht-Einhaltung

|Risiko|Auswirkung|Wahrscheinlichkeit|Mitigation|
|---|---|---|---|
|**Keine Resource Limits**|Out-of-Memory Crashes, Node-Ausfälle|Hoch|Verpflichtende Limits|
|**Fehlende Health Checks**|Pods bleiben trotz Fehler im Load Balancer|Mittel|Liveness/Readiness Probes|
|**Keine Network Policies**|Lateral Movement bei Breach|Mittel|Default Deny Policy|
|**Manuelle Deployments**|Inkonsistente Umgebungen|Hoch|Helm + GitOps|
|**Fehlende Backups**|Datenverlust bei Disaster|Niedrig|Velero + CronJobs|
|**Single Point of Failure**|Kompletter Ausfall bei Pod-Crash|Hoch|min 3 Replicas + PDB|

---

## 13. Migrations-Roadmap

### Phase 1: Docker Containerisierung (Woche 1-2) ✅

- [x] Dockerfile für Backend erstellen
- [x] Dockerfile für Frontend erstellen
- [x] Docker Compose für lokale Entwicklung (min. File Format Version `3.8`)
- [x] CI Pipeline für Image Builds
- [x] .dockerignore für Backend und Frontend

### Phase 2: Kubernetes Setup (Woche 3-4)

- [ ] Cluster provisionieren (EKS/GKE/On-Prem)
- [ ] Namespaces anlegen
- [ ] Secrets Management (Sealed Secrets)
- [ ] Ingress Controller (Traefik)

### Phase 3: Workload Migration (Woche 5-6)

- [ ] Backend Deployment
- [ ] ArangoDB StatefulSet
- [ ] Redis Deployment
- [ ] Frontend Deployment

### Phase 4: Helm Charts (Woche 7-8)

- [ ] Charts mit bjw-s/common erstellen
- [ ] Values für Environments
- [ ] CI/CD Integration
- [ ] Helmfile Setup

### Phase 5: Observability (Woche 9-10)

- [ ] Prometheus + Grafana
- [ ] Fluentd + Elasticsearch + Kibana
- [ ] Jaeger Tracing
- [ ] Alerting Rules

### Phase 6: Production Hardening (Woche 11-12)

- [ ] HPA + VPA
- [ ] Network Policies
- [ ] Pod Security Policies
- [ ] Disaster Recovery Tests

---

## Anhang A: Kubernetes Cheat Sheet

### Pod Management

```bash
# Liste alle Pods
kubectl get pods -n agrotech-prod

# Pod Details
kubectl describe pod <pod-name> -n agrotech-prod

# Logs anschauen
kubectl logs <pod-name> -n agrotech-prod -f

# In Pod einloggen
kubectl exec -it <pod-name> -n agrotech-prod -- /bin/bash

# Port-Forward
kubectl port-forward pod/<pod-name> 8000:8000 -n agrotech-prod
```

### Deployment Management

```bash
# Deployment skalieren
kubectl scale deployment/agrotech-backend --replicas=5 -n agrotech-prod

# Rollout Status
kubectl rollout status deployment/agrotech-backend -n agrotech-prod

# Rollback
kubectl rollout undo deployment/agrotech-backend -n agrotech-prod

# History
kubectl rollout history deployment/agrotech-backend -n agrotech-prod
```

### Debugging

```bash
# Events anschauen
kubectl get events -n agrotech-prod --sort-by='.lastTimestamp'

# Resource Usage
kubectl top pods -n agrotech-prod
kubectl top nodes

# Network Debugging
kubectl run -it --rm debug --image=nicolaka/netshoot -- /bin/bash
```

---

## Anhang B: Helm Commands

```bash
# Chart installieren
helm install <release-name> <chart-path> -n <namespace>

# Chart upgraden
helm upgrade <release-name> <chart-path> -n <namespace>

# Upgrade oder Install (idempotent)
helm upgrade --install <release-name> <chart-path> -n <namespace>

# Release löschen
helm uninstall <release-name> -n <namespace>

# Liste Releases
helm list -n <namespace>

# Rollback
helm rollback <release-name> <revision> -n <namespace>

# Values anzeigen
helm get values <release-name> -n <namespace>

# Manifests rendern (Dry-Run)
helm template <release-name> <chart-path>

# Dependencies verwalten
helm dependency update <chart-path>
helm dependency build <chart-path>
```

---

**Dokumenten-Ende**

**Version**: 2.1
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-27
**Review**: Pending
**Genehmigung**: Pending

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 2.1 | 2026-02-27 | IT-Security-Review-Findings eingearbeitet: §3.2 `seccompProfile: RuntimeDefault` ergänzt (SEC-M-004), §7.1 Default-Deny-Policy + Frontend-Network-Policy + Egress für externe APIs hinzugefügt (SEC-M-004), §11 Security-Akzeptanzkriterien erweitert |
| 2.0 | 2026-02-25 | Initiale produktionsreife Spezifikation |