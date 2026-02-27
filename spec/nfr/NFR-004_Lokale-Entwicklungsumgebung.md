---

ID: NFR-004
Titel: Lokale Entwicklungsumgebung mit Skaffold
Kategorie: Entwicklungsumgebung / Developer Experience Unterkategorie: Local Development, Hot Reload, DevOps Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Skaffold, Kubernetes, Docker, Helm
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-25
Tags: [developer-experience, local-development, skaffold, hot-reload, kubernetes-dev]
Abhängigkeiten: [NFR-002, NFR-003]
Betroffene Module: [ALL]
---

# NFR-004: Lokale Entwicklungsumgebung mit Skaffold

## 1. Business Case

### 1.1 User Stories

**Als** Entwickler  
**möchte ich** dass meine lokale Entwicklungsumgebung der Production-Infrastruktur entspricht  
**um** "Works on my machine"-Probleme zu vermeiden und schneller entwickeln zu können.

**Als** Backend-Entwickler  
**möchte ich** dass Code-Änderungen automatisch im Kubernetes-Cluster deployed werden  
**um** Feedback-Zyklen von Minuten auf Sekunden zu reduzieren.

**Als** DevOps Engineer  
**möchte ich** dass alle Entwickler die gleiche standardisierte Umgebung nutzen  
**um** Onboarding zu beschleunigen und Troubleshooting zu vereinfachen.

**Als** Tech Lead  
**möchte ich** dass Entwickler lokal mit realistischen Microservices-Abhängigkeiten arbeiten  
**um** Integrationsprobleme früh zu erkennen.

### 1.2 Geschäftliche Motivation

**Produktivitätssteigerung**:
- Reduzierung der Feedback-Loop von 5-10 Minuten auf 10-30 Sekunden
- Automatisches Hot-Reload bei Code-Änderungen
- Debugging im Kubernetes-Kontext (nicht nur Docker Compose)

**Kosteneffizienz**:
- Keine Cloud-Kosten für Dev-Environments
- Entwickler arbeiten offline (Zug, Flugzeug)
- Schnelleres Onboarding (< 1 Tag statt 1 Woche)

**Qualitätssicherung**:
- Production-Parity: Gleiche Helm Charts wie Production
- Frühe Erkennung von K8s-spezifischen Problemen
- Realistische Performance-Tests lokal möglich

### 1.3 Fachliche Beschreibung

**Problem ohne Skaffold**:

```bash
# Manueller Workflow (5-10 Minuten pro Änderung)
1. Code ändern in backend/irrigation.py
2. Docker Build: docker build -t agrotech/backend:dev .
3. Push zu Registry: docker push agrotech/backend:dev
4. Update Deployment: kubectl set image deployment/backend backend=agrotech/backend:dev
5. Warten auf Pod-Neustart: kubectl rollout status deployment/backend
6. Logs anschauen: kubectl logs -f deployment/backend
7. Bei Fehler: Zurück zu Schritt 1
```

**Lösung mit Skaffold** (10-30 Sekunden):

```bash
# Einmaliges Setup
skaffold dev

# Workflow
1. Code ändern in backend/irrigation.py
2. Skaffold erkennt Änderung automatisch
3. Rebuild nur der geänderten Layer (Docker Cache)
4. Deploy zu lokalem Minikube
5. Port-Forward + Log-Stream automatisch
6. Hot-Reload im Container (FastAPI Auto-Reload)
```

---

## 2. Skaffold Architektur & Konzepte

### 2.1 Skaffold Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    DEVELOPER WORKFLOW                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   skaffold dev         │  ← Einmaliger Command
         └────────────┬───────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌────────┐      ┌──────────┐      ┌─────────┐
│ WATCH  │      │  BUILD   │      │ DEPLOY  │
│ Files  │ ───▶ │  Docker  │ ───▶ │  Helm   │
└────────┘      └──────────┘      └─────────┘
    │                 │                 │
    │                 │                 │
    ▼                 ▼                 ▼
Code Change    Incremental      Hot-Reload
Detected       Build (Layer     in Pod
               Cache)           (10-30s)
                      │
                      ▼
         ┌────────────────────────┐
         │  PORT-FORWARD + LOGS   │
         │  http://localhost:8000 │
         └────────────────────────┘
```

### 2.2 Skaffold Modi

| Modus | Use Case | Hot-Reload | Teardown |
|-------|----------|------------|----------|
| **skaffold dev** | Aktive Entwicklung | ✅ Ja | Automatisch bei Ctrl+C |
| **skaffold debug** | Debugging mit IDE | ✅ Ja | Automatisch bei Ctrl+C |
| **skaffold run** | Einmalig deployen | ❌ Nein | Manuell |
| **skaffold build** | Nur Images bauen | ❌ Nein | - |
| **skaffold render** | Manifests generieren | ❌ Nein | - |

### 2.3 File Sync vs. Rebuild

```yaml
# skaffold.yaml
build:
  artifacts:
  - image: agrotech/backend
    sync:
      manual:
        - src: 'src/**/*.py'
          dest: /app/src
          # Sync ohne Rebuild für Python-Dateien
    docker:
      dockerfile: Dockerfile
```

**File Sync** (1-5 Sekunden):
- Python-Dateien direkt in Container kopieren
- Kein Docker Build nötig
- FastAPI Auto-Reload greift

**Rebuild** (20-60 Sekunden):
- Neue Dependency in requirements.txt
- Dockerfile-Änderung
- Statische Assets

---

## 3. Lokale Kubernetes-Cluster

### 3.1 Cluster-Optionen

| Tool | Pros | Cons | Empfehlung |
|------|------|------|------------|
| **Kind** | Schnell, CI-freundlich, Multi-Node | Kein LoadBalancer (nutze Port-Mapping) | ✅ Primär |
| **Minikube** | Stabil, Feature-reich, GUI | Ressourcen-intensiv, langsamer | ⚠️ Alternative |
| **k3s/k3d** | Leichtgewichtig, Production-like | Komplexeres Setup | ⚠️ Advanced |
| **Docker Desktop** | Einfach, GUI | Mac/Windows only, langsam | ❌ Nicht empfohlen |

### 3.2 Kind Setup

**Installation (macOS/Linux)**:

```bash
# macOS
brew install kind kubectl helm skaffold

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify
kind version
kubectl version --client
helm version
skaffold version
```

**Kind Cluster erstellen**:

```bash
# Einfacher Cluster
kind create cluster --name agrotech

# Mit Custom-Config (empfohlen)
cat > kind-config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: agrotech

# Multi-Node Setup
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 8000
    hostPort: 8000
    protocol: TCP
  - containerPort: 3000
    hostPort: 3000
    protocol: TCP
  - containerPort: 8529
    hostPort: 8529
    protocol: TCP
- role: worker
- role: worker

# Networking
networking:
  apiServerAddress: "127.0.0.1"
  apiServerPort: 6443
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
EOF

kind create cluster --config kind-config.yaml

# Verify
kubectl cluster-info --context kind-agrotech
kubectl get nodes
```

**Ingress Controller (Nginx)**:

```bash
# Nginx Ingress installieren
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Warten bis ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Verify
kubectl get pods -n ingress-nginx
```

**Metrics Server**:

```bash
# Metrics Server für HPA
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch für insecure TLS (nur für Kind)
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# Verify
kubectl top nodes
```

**Lokales Docker Registry (optional)**:

```bash
# Registry Container erstellen
docker run -d --restart=always -p 5001:5000 --name kind-registry registry:2

# Registry mit Kind verbinden
docker network connect kind kind-registry

# Cluster konfigurieren für Registry
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:5001"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF
```

### 3.3 Cluster-Management

**Cluster-Operationen**:

```bash
# Cluster auflisten
kind get clusters

# Cluster-Info
kubectl cluster-info --context kind-agrotech

# Nodes anzeigen
kubectl get nodes

# Cluster löschen
kind delete cluster --name agrotech

# Cluster neu erstellen
kind create cluster --config kind-config.yaml

# Export kubeconfig
kind export kubeconfig --name agrotech

# Laden eines Images in Kind
kind load docker-image agrotech/backend:dev --name agrotech
```

**Multi-Cluster Management**:

```bash
# Dev-Cluster
kind create cluster --name agrotech-dev --config kind-config-dev.yaml

# Test-Cluster
kind create cluster --name agrotech-test --config kind-config-test.yaml

# Context wechseln
kubectl config use-context kind-agrotech-dev
kubectl config use-context kind-agrotech-test

# Alle Cluster löschen
kind delete clusters --all
```

**Cleanup & Ressourcen**:

```bash
# Cluster stoppen (Kind hat kein pause)
# Stattdessen: Container stoppen
docker stop agrotech-control-plane agrotech-worker agrotech-worker2

# Container starten
docker start agrotech-control-plane agrotech-worker agrotech-worker2

# Disk-Space freigeben
kind delete cluster --name agrotech
docker system prune -a --volumes

# Logs anschauen
docker logs agrotech-control-plane
```

### 3.4 Kind Best Practices

**1. Persistent Storage**:

```yaml
# kind-config.yaml - Lokale Verzeichnisse mounten
nodes:
- role: control-plane
  extraMounts:
  - hostPath: /tmp/agrotech-data
    containerPath: /data
    readOnly: false
    selinuxRelabel: false
    propagation: None
```

```bash
# Nutzung in PV
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteOnce
  hostPath:
    path: /data
    type: DirectoryOrCreate
```

**2. Image Preloading für schnellere Starts**:

```bash
# Script: preload-images.sh
#!/bin/bash

IMAGES=(
  "python:3.14-slim"
  "arangodb:3.11"
  "redis:7.2"
  "nginx:alpine"
)

for image in "${IMAGES[@]}"; do
  echo "Loading $image..."
  docker pull $image
  kind load docker-image $image --name agrotech
done

echo "✅ All images preloaded"
```

**3. Automatisches Cluster-Reset**:

```bash
# Script: reset-cluster.sh
#!/bin/bash
set -e

echo "🔄 Resetting Kind cluster..."

# Delete
kind delete cluster --name agrotech

# Recreate
kind create cluster --config kind-config.yaml --name agrotech

# Reinstall Ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for Ingress
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "✅ Cluster reset complete"
```

**4. Entwickler-freundliche Aliases**:

```bash
# ~/.zshrc oder ~/.bashrc
alias k='kubectl'
alias kx='kubectl config use-context'
alias kns='kubectl config set-context --current --namespace'

# Kind-spezifisch
alias kind-start='kind create cluster --config kind-config.yaml --name agrotech'
alias kind-stop='kind delete cluster --name agrotech'
alias kind-load='kind load docker-image'
alias kind-logs='docker logs agrotech-control-plane'

# Skaffold
alias sd='skaffold dev'
alias sdb='skaffold debug'
alias sr='skaffold run'
alias sc='skaffold delete'
```

---

## 4. Skaffold Konfiguration

### 4.1 Projekt-Struktur

```
agrotech/
├── skaffold.yaml              # Root Skaffold Config
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.dev         # Development-optimiert
│   ├── skaffold.yaml          # Backend-spezifisch
│   ├── src/
│   └── helm/
│       └── values-dev.yaml
├── frontend/
│   ├── Dockerfile.dev
│   ├── skaffold.yaml
│   └── helm/
│       └── values-dev.yaml
├── arangodb/
│   └── helm/
│       └── values-dev.yaml
└── helm/
    └── agrotech-umbrella/
        └── values-dev.yaml
```

### 4.2 Root skaffold.yaml

**Haupt-Konfiguration**:

```yaml
# skaffold.yaml
apiVersion: skaffold/v4beta13
kind: Config

metadata:
  name: kamerplanter

# Build-Konfiguration
build:
  artifacts:

  # Backend
  - image: kamerplanter-backend
    context: src/backend
    docker:
      dockerfile: Dockerfile.dev
    sync:
      manual:
        - src: 'app/**/*.py'
          dest: /app

  # Frontend
  - image: kamerplanter-frontend
    context: src/frontend
    docker:
      dockerfile: Dockerfile.dev
    sync:
      manual:
        - src: 'src/**/*.ts'
          dest: /app
        - src: 'src/**/*.tsx'
          dest: /app
        - src: 'src/**/*.css'
          dest: /app

  # Lokales Build für Kind
  local:
    push: false
    concurrency: 2

# Deployment mit Helm
# WICHTIG: Helm-Releases gehören unter deploy.helm (nicht manifests.helm),
# damit Skaffold den vollen Helm-Lifecycle (install/upgrade/uninstall) verwaltet.
deploy:
  helm:
    releases:

    # ArangoDB
    - name: kamerplanter-arangodb
      chartPath: helm/kamerplanter-arangodb
      namespace: default
      valuesFiles:
        - helm/kamerplanter-arangodb/values-dev.yaml

    # Redis
    - name: redis
      remoteChart: bitnami/redis
      version: 24.1.0
      namespace: default
      setValues:
        architecture: standalone
        auth.enabled: false
        master.persistence.size: 1Gi

    # Backend
    # WICHTIG: setValueTemplates statt setValues für Image-Referenzen verwenden.
    # Skaffold injiziert Repository und Tag aus dem Build-Schritt über Template-
    # Variablen. Statische setValues mit leerem image.tag führen zu
    # InvalidImageName-Fehlern (z.B. "kamerplanter-backend:" ohne Tag).
    - name: kamerplanter-backend
      chartPath: helm/kamerplanter-backend
      namespace: default
      valuesFiles:
        - helm/kamerplanter-backend/values-dev.yaml
      setValueTemplates:
        image.repository: "{{.IMAGE_REPO_kamerplanter_backend}}"
        image.tag: "{{.IMAGE_TAG_kamerplanter_backend}}"

    # Frontend
    - name: kamerplanter-frontend
      chartPath: helm/kamerplanter-frontend
      namespace: default
      valuesFiles:
        - helm/kamerplanter-frontend/values-dev.yaml
      setValueTemplates:
        image.repository: "{{.IMAGE_REPO_kamerplanter_frontend}}"
        image.tag: "{{.IMAGE_TAG_kamerplanter_frontend}}"

# Port-Forwarding
portForward:
  - resourceType: service
    resourceName: kamerplanter-backend
    namespace: default
    port: 8000
    localPort: 8000

  - resourceType: service
    resourceName: kamerplanter-frontend
    namespace: default
    port: 5173
    localPort: 3000

  - resourceType: service
    resourceName: kamerplanter-arangodb
    namespace: default
    port: 8529
    localPort: 8529

# Profiles für verschiedene Workflows
profiles:

  # Nur Backend entwickeln
  - name: backend-only
    patches:
      - op: remove
        path: /build/artifacts/1
      - op: remove
        path: /deploy/helm/releases/3
      - op: remove
        path: /portForward/1

  # Nur Frontend entwickeln
  - name: frontend-only
    patches:
      - op: remove
        path: /build/artifacts/0
      - op: remove
        path: /deploy/helm/releases/0
      - op: remove
        path: /deploy/helm/releases/0
      - op: remove
        path: /portForward/0
      - op: remove
        path: /portForward/1

  # Debug-Modus
  - name: debug
    activation:
      - command: debug
    patches:
      - op: add
        path: /build/artifacts/0/docker/buildArgs
        value:
          DEBUGPY_ENABLED: "true"
```

### 4.3 Development Dockerfile

**backend/Dockerfile.dev**:

```dockerfile
# Development-optimiertes Dockerfile für Kind
FROM python:3.14-slim-bookworm AS base

WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Hot-Reload für Development
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV WATCHFILES_FORCE_POLLING=true

# User für Security (Kind unterstützt runAsUser)
RUN useradd -m -u 1000 -s /bin/bash appuser

# Code wird via Skaffold File Sync gemountet
COPY --chown=appuser:appuser . .

USER appuser

# Health Check
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

# Development Server mit Auto-Reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]
```

**Unterschiede zu Production Dockerfile**:

| Feature | Development | Production |
|---------|-------------|------------|
| **Base Image** | `python:3.14-slim` | `python:3.14-slim` (multi-stage) |
| **Dependencies** | requirements-dev.txt included | Nur requirements.txt |
| **Server** | uvicorn --reload | uvicorn (no reload) |
| **Workers** | 1 | 4 |
| **Debug Tools** | curl, vim installiert | Minimale Tools |
| **Layer Caching** | Optimiert für schnelle Rebuilds | Optimiert für kleine Size |

### 4.4 Helm Values für Development

**helm/agrotech-backend/values-dev.yaml**:

```yaml
# Development-spezifische Overrides
controllers:
  main:
    replicas: 1  # Single Pod für dev
    
    strategy:
      type: Recreate  # Schneller für dev
    
    containers:
      main:
        image:
          pullPolicy: IfNotPresent  # Kein Pull bei lokalem Build
        
        env:
          - name: ENVIRONMENT
            value: "development"
          - name: LOG_LEVEL
            value: "DEBUG"
          - name: RELOAD
            value: "true"
          - name: ARANGODB_URL
            value: "http://arangodb-main:8529"
          - name: REDIS_URL
            value: "redis://redis-master:6379/0"
        
        probes:
          liveness:
            initialDelaySeconds: 5  # Schneller für dev
            periodSeconds: 5
          readiness:
            initialDelaySeconds: 3
            periodSeconds: 3
          startup:
            initialDelaySeconds: 0
            periodSeconds: 2
            failureThreshold: 30
        
        resources:
          requests:
            cpu: 100m      # Weniger für dev
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        
        securityContext:
          runAsNonRoot: false  # Relaxed für dev (File Sync)
          readOnlyRootFilesystem: false

# Service
service:
  main:
    type: ClusterIP

# Ingress disabled (nutze Port-Forward)
ingress:
  main:
    enabled: false

# Autoscaling disabled
autoscaling:
  enabled: false

# ServiceMonitor disabled (kein Prometheus lokal)
serviceMonitor:
  main:
    enabled: false

# Debug-Features
persistence:
  logs:
    enabled: true
    type: emptyDir
    globalMounts:
      - path: /app/logs
```

### 4.5 Backend-URL Konfiguration (Frontend → Backend)

Das Frontend muss in verschiedenen Umgebungen unterschiedliche Backend-Endpunkte nutzen. Dafür gibt es **drei Netzwerk-Ebenen** mit jeweils eigener Lösung:

#### Architektur-Überblick

```
┌─────────────────────────────────────────────────────────────┐
│                    NETZWERK-EBENEN                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Lokale Entwicklung (npm run dev, kein K8s)              │
│     Browser → Vite Dev Server (:5173)                       │
│            └─ proxy /api → http://127.0.0.1:8000            │
│               (VITE_BACKEND_URL oder Default)               │
│                                                             │
│  2. Skaffold Dev (K8s, Vite im Pod)                         │
│     Browser → Port-Forward → Ingress                        │
│            └─ /api → kamerplanter-backend:8000 (K8s-DNS)    │
│     Vite-Proxy im Pod:                                      │
│            └─ Env-Var VITE_BACKEND_URL aus Helm-Values      │
│               → http://kamerplanter-backend:8000            │
│                                                             │
│  3. Produktion (K8s, nginx im Pod)                          │
│     Browser → Ingress/LB → nginx (:80)                     │
│            └─ proxy_pass → kamerplanter-backend:8000        │
│               (ConfigMap überschreibt Image-nginx.conf)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Helm Values

Der Backend-Host und -Port sind im Frontend-Helm-Chart konfigurierbar:

**helm/kamerplanter-frontend/values.yaml** (Defaults):
```yaml
backend:
  host: kamerplanter-backend
  port: 8000
```

Überschreibbar pro Umgebung in `values-dev.yaml`, `values-staging.yaml` etc. oder per Skaffold `setValues`:

```yaml
# skaffold.yaml (Beispiel)
- name: kamerplanter-frontend
  setValues:
    backend.host: mein-anderer-host
    backend.port: "9000"
```

#### nginx-ConfigMap (Produktion)

Die nginx-Konfiguration wird als **Helm-ConfigMap** (`configmap-nginx.yaml`) gerendert, nicht im Docker-Image eingebacken:

```yaml
# templates/configmap-nginx.yaml (vereinfacht)
data:
  default.conf: |
    location /api/ {
        proxy_pass http://{{ .Values.backend.host }}:{{ .Values.backend.port }};
    }
```

Das Deployment mountet die ConfigMap als Volume auf `/etc/nginx/conf.d/default.conf` (subPath-Mount). Die Pod-Annotation `checksum/nginx-config` erzwingt einen automatischen Restart bei Konfigurationsänderung:

```yaml
# templates/deployment.yaml (Auszug)
template:
  metadata:
    annotations:
      checksum/nginx-config: {{ include (...) | sha256sum }}
  spec:
    containers:
      - volumeMounts:
          - name: nginx-config
            mountPath: /etc/nginx/conf.d/default.conf
            subPath: default.conf
    volumes:
      - name: nginx-config
        configMap:
          name: {{ fullname }}-nginx
```

**Fallback**: Die Datei `src/frontend/nginx.conf` im Docker-Image bleibt erhalten und wird in Docker-Compose-Setups genutzt (dort heißt der Backend-Service `backend`).

#### Vite-Proxy (Entwicklung)

Der Vite Dev Server liest die Backend-URL aus der Environment-Variable `VITE_BACKEND_URL`:

```ts
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: process.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8000',
    },
  },
}
```

| Kontext | VITE_BACKEND_URL | Resultat |
|---------|-----------------|----------|
| `npm run dev` (lokal) | nicht gesetzt | `http://127.0.0.1:8000` (Default) |
| Skaffold Dev (Pod) | aus Helm Deployment-Env | `http://kamerplanter-backend:8000` |
| Manuell überschrieben | `VITE_BACKEND_URL=http://192.168.1.50:8000 npm run dev` | Benutzerdefiniert |

Im Helm-Deployment wird die Env-Var automatisch aus den Backend-Values injiziert:

```yaml
# templates/deployment.yaml (Auszug)
env:
  - name: VITE_BACKEND_URL
    value: "http://{{ .Values.backend.host }}:{{ .Values.backend.port }}"
```

---

## 5. Workflow & Commands

### 5.1 Täglicher Development-Workflow

**Morning Routine**:

```bash
# 1. Kind Cluster starten (falls nicht running)
kind get clusters | grep agrotech || kind create cluster --config kind-config.yaml --name agrotech

# 2. Verify Cluster
kubectl cluster-info --context kind-agrotech

# 3. Skaffold Dev starten
cd ~/projects/agrotech
skaffold dev

# Output:
# Listing files to watch...
# - agrotech/backend
# - agrotech/frontend
# Generating tags...
# - agrotech/backend -> agrotech/backend:latest
# Checking cache...
# - agrotech/backend: Not found. Building
# Building [agrotech/backend]...
# [+] Building 45.2s (12/12) FINISHED
# Loading images into Kind cluster nodes...
# - agrotech/backend -> Loaded
# Tags used in deployment:
# - agrotech/backend -> agrotech/backend:latest@sha256:abc123
# Starting deploy...
# Helm release backend not installed. Installing...
# Port forwarding service/backend-main in namespace agrotech-dev, remote port 8000 -> http://127.0.0.1:8000
# [backend] INFO:     Uvicorn running on http://0.0.0.0:8000
# [backend] INFO:     Application startup complete
# Watching for changes...
```

**Code ändern**:

```bash
# Terminal 1: skaffold dev läuft

# Terminal 2: Code ändern
vim backend/src/services/irrigation.py

# Skaffold erkennt Änderung automatisch:
# File sync:
# - backend/src/services/irrigation.py
# [backend] INFO:     Detected file change, reloading...
# [backend] INFO:     Application startup complete
```

**Testing**:

```bash
# Terminal 3: API testen
curl http://localhost:8000/health/live
curl http://localhost:8000/api/v1/plants

# Logs anschauen (bereits im Terminal 1)

# Debugging
skaffold debug  # Startet mit Debug-Port
# Dann in VS Code: Attach to Process
```

**Cleanup**:

```bash
# Ctrl+C in Terminal 1
# Skaffold räumt automatisch auf:
# Cleaning up...
# Helm release backend deleted
# Helm release frontend deleted
```

### 5.2 Spezielle Workflows

**Nur Backend entwickeln**:

```bash
export SKAFFOLD_PROFILE=backend-only
skaffold dev
```

**Production-like testen**:

```bash
skaffold dev --profile=prod-like
# 3 Backend Replicas, HPA enabled
```

**Einmalig deployen (ohne Watch)**:

```bash
skaffold run
# Deploy einmal, dann exit
```

**Nur Images bauen**:

```bash
skaffold build --file-output=build.json
# Baut alle Images, speichert Tags in build.json
```

**Manifests generieren (ohne Deploy)**:

```bash
skaffold render > manifests.yaml
# Generiert finale K8s Manifests
```

### 5.3 Debugging

**Debug-Modus aktivieren**:

```bash
skaffold debug
```

**Python Debugger (debugpy)**:

```yaml
# skaffold.yaml - debug profile
profiles:
  - name: debug
    patches:
      - op: add
        path: /build/artifacts/0/docker/buildArgs/DEBUGPY
        value: "true"
```

**Dockerfile.dev mit Debug-Support**:

```dockerfile
# Optional: debugpy installieren
ARG DEBUGPY=false
RUN if [ "$DEBUGPY" = "true" ]; then \
        pip install debugpy; \
    fi

# Start Command mit debugpy
CMD if [ "$DEBUGPY" = "true" ]; then \
        python -m debugpy --listen 0.0.0.0:5678 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload; \
    else \
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload; \
    fi
```

**VS Code Launch Configuration**:

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Attach to Skaffold",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/backend",
          "remoteRoot": "/app"
        }
      ]
    }
  ]
}
```

---

## 6. Performance-Optimierung

### 6.1 Docker Build Cache

**Layer Caching**:

```dockerfile
# ✅ OPTIMAL - Dependencies zuerst (ändern sich selten)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# Code ändert sich oft, nutzt Cache von oben

# ❌ SUBOPTIMAL - Alles zusammen
COPY . .
RUN pip install -r requirements.txt
# Jede Code-Änderung rebuilt dependencies
```

**BuildKit Features**:

```yaml
# skaffold.yaml
build:
  local:
    useBuildkit: true
    concurrency: 2  # Parallel builds
```

```dockerfile
# Dockerfile.dev
# syntax=docker/dockerfile:1.4

# Cache Mounts (BuildKit)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### 6.2 File Sync Patterns

**Optimale Sync-Konfiguration**:

```yaml
# skaffold.yaml
sync:
  manual:
    # Python Source (hot-reload)
    - src: 'src/**/*.py'
      dest: /app/src
      strip: src/
    
    # Templates (FastAPI Jinja2)
    - src: 'templates/**/*.html'
      dest: /app/templates
    
    # Static Assets
    - src: 'static/**/*'
      dest: /app/static
    
  # Rebuild bei diesen Änderungen
  infer:
    - requirements.txt
    - pyproject.toml
    - Dockerfile*
```

**File Sync vs. Rebuild Decision**:

| Datei | File Sync | Rebuild |
|-------|-----------|---------|
| `src/**/*.py` | ✅ Ja (1-5s) | ❌ |
| `templates/**/*.html` | ✅ Ja | ❌ |
| `requirements.txt` | ❌ | ✅ Ja (30-60s) |
| `Dockerfile` | ❌ | ✅ Ja |
| `.env` | ✅ Ja (ConfigMap) | ❌ |

### 6.3 Kind Performance

**Ressourcen-Tuning**:

```bash
# Kind nutzt Docker-Ressourcen
# Docker Desktop Settings:
# - CPUs: 6
# - Memory: 12GB
# - Disk: 100GB

# Verify Docker Resources
docker system info | grep -E "CPUs|Total Memory"

# Kind Cluster mit mehr Nodes (parallel processing)
# kind-config.yaml:
# nodes:
# - role: control-plane
# - role: worker
# - role: worker
# - role: worker  # 4 Worker = mehr Parallelität
```

**Image Loading Optimization**:

```bash
# Preload häufig genutzte Images
docker pull python:3.14-slim
docker pull arangodb:3.11
docker pull redis:7.2

# In Kind laden
kind load docker-image python:3.14-slim --name agrotech
kind load docker-image arangodb:3.11 --name agrotech
kind load docker-image redis:7.2 --name agrotech

# Oder: Lokales Registry nutzen (schneller)
# Siehe Sektion 3.2 "Lokales Docker Registry"
```

**Build Cache**:

```bash
# Docker BuildKit Cache nutzen
export DOCKER_BUILDKIT=1

# Build Cache Volume (persistent)
docker volume create buildkit-cache

# In Dockerfile.dev
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install -r requirements.txt
```

**Kind-spezifische Optimierungen**:

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4

# Disable default CNI (schnellerer Start)
networking:
  disableDefaultCNI: false
  kubeProxyMode: "iptables"  # Schneller als ipvs für dev

# Feature Gates
featureGates:
  "EphemeralContainers": true

# Runtime Config
runtimeConfig:
  "api/all": "true"
```

---

## 7. Troubleshooting

### 7.1 Häufige Probleme

**Problem: Skaffold kann Images nicht in Kind laden**

```bash
# Symptom
Error: failed to load image into cluster

# Lösung: Images explizit laden
kind load docker-image agrotech/backend:latest --name agrotech

# Oder: Skaffold Config anpassen
# skaffold.yaml:
# deploy:
#   kubectl: {}
#   kubeContext: kind-agrotech
```

**Problem: Port-Forwarding schlägt fehl**

```bash
# Symptom
Error: unable to forward port

# Lösung 1: Prüfe Kind extraPortMappings
# kind-config.yaml muss enthalten:
# extraPortMappings:
# - containerPort: 8000
#   hostPort: 8000

# Lösung 2: NodePort Service nutzen
# values-dev.yaml:
# service:
#   main:
#     type: NodePort
#     ports:
#       http:
#         nodePort: 30080
```

**Problem: Ingress funktioniert nicht**

```bash
# Symptom
curl http://localhost/api/health → Connection refused

# Lösung: Nginx Ingress neu installieren
kubectl delete -A ValidatingWebhookConfiguration ingress-nginx-admission
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Verify
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

**Problem: Pods hängen in ImagePullBackOff**

```bash
# Symptom
kubectl get pods
# NAME               READY   STATUS             RESTARTS
# backend-abc123     0/1     ImagePullBackOff   0

# Lösung: Image in Kind laden
kind load docker-image agrotech/backend:latest --name agrotech

# Oder: imagePullPolicy anpassen
# values-dev.yaml:
# controllers:
#   main:
#     containers:
#       main:
#         image:
#           pullPolicy: Never  # Nie pullen, nur lokal
```

**Problem: Cluster startet nicht**

```bash
# Symptom
kind create cluster → timeout

# Lösung 1: Docker neu starten
docker system prune -a
killall Docker  # macOS
sudo systemctl restart docker  # Linux

# Lösung 2: Alte Cluster löschen
kind delete clusters --all
docker rm -f $(docker ps -aq)

# Lösung 3: Kind Version prüfen
kind version
# Upgrade: brew upgrade kind
```

### 7.2 Debug-Commands

**Skaffold Diagnostics**:

```bash
# Verbose Logs
skaffold dev -v trace

# Build-Probleme debuggen
skaffold build -v debug

# Render ohne Deploy
skaffold render

# Config validieren
skaffold diagnose
```

**Kubernetes Debugging**:

```bash
# Pod-Status
kubectl get pods -n agrotech-dev

# Pod-Logs
kubectl logs -f -n agrotech-dev deployment/backend

# Pod-Events
kubectl describe pod -n agrotech-dev <pod-name>

# In Pod einloggen
kubectl exec -it -n agrotech-dev <pod-name> -- /bin/bash

# Port-Forward manuell
kubectl port-forward -n agrotech-dev svc/backend-main 8000:8000

# Über NodePort zugreifen (wenn Service NodePort ist)
kubectl get svc -n agrotech-dev backend-main
# Dann: http://localhost:<nodePort>
```

**Kind Debugging**:

```bash
# Cluster Status
kind get clusters

# Cluster Details
docker ps --filter name=agrotech

# Logs von Control-Plane Node
docker logs agrotech-control-plane

# Logs von Worker Node
docker logs agrotech-worker

# In Kind Node einloggen
docker exec -it agrotech-control-plane bash

# Images im Kind Cluster
docker exec -it agrotech-control-plane crictl images

# Kind Cluster neu erstellen (bei Problemen)
kind delete cluster --name agrotech
kind create cluster --config kind-config.yaml --name agrotech
```

---

## 8. Team-Onboarding

### 8.1 Onboarding-Checkliste

**Neuer Entwickler - Setup (< 1 Stunde)**:

```markdown
## Agrotech Development Setup

### 1. Prerequisites
- [ ] macOS / Linux (Windows WSL2 auch möglich)
- [ ] Docker Desktop installiert und running
- [ ] 16GB RAM minimum (empfohlen: 32GB)
- [ ] 50GB freier Disk Space

### 2. Tools installieren
```bash
# macOS
brew install minikube kubectl helm skaffold

# Linux
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
```

### 3. Repository clonen
```bash
git clone https://github.com/agrotech/backend.git
cd backend
```

### 4. Kind Cluster starten
```bash
# Kind Config erstellen
cat > kind-config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: agrotech
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
  - containerPort: 8000
    hostPort: 8000
  - containerPort: 3000
    hostPort: 3000
- role: worker
EOF

# Cluster erstellen
kind create cluster --config kind-config.yaml

# Ingress installieren
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

### 5. Erste Entwicklungssession
```bash
# Skaffold Dev
skaffold dev

# In neuem Terminal: API testen
curl http://localhost:8000/health/live

# In neuem Terminal: Frontend öffnen
open http://localhost:5173
```

### 6. Verify
- [ ] Backend erreichbar unter http://localhost:8000
- [ ] Frontend erreichbar unter http://localhost:5173
- [ ] ArangoDB UI unter http://localhost:8529
- [ ] Code-Änderung wird automatisch deployed (< 30s)
```

### 8.2 Onboarding-Script

**scripts/dev-setup.sh**:

```bash
#!/bin/bash
set -e

echo "🚀 Agrotech Development Setup"
echo "=============================="

# Check Prerequisites
echo "📋 Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install Docker Desktop first."; exit 1; }
command -v kind >/dev/null 2>&1 || { echo "❌ kind not found. Run: brew install kind"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found. Run: brew install kubectl"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ helm not found. Run: brew install helm"; exit 1; }
command -v skaffold >/dev/null 2>&1 || { echo "❌ skaffold not found. Run: brew install skaffold"; exit 1; }

echo "✅ All prerequisites installed"

# Create Kind Config
echo ""
echo "📝 Creating Kind config..."
cat > kind-config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: agrotech
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
  - containerPort: 8000
    hostPort: 8000
  - containerPort: 3000
    hostPort: 3000
  - containerPort: 8529
    hostPort: 8529
- role: worker
- role: worker
EOF

# Start Kind Cluster
echo ""
echo "🎯 Starting Kind cluster..."
if kind get clusters | grep -q "^agrotech$"; then
    echo "✅ Kind cluster already running"
else
    kind create cluster --config kind-config.yaml
    echo "✅ Kind cluster started"
fi

# Install Ingress Controller
echo ""
echo "🌐 Installing Nginx Ingress..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for Ingress
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "✅ Ingress controller ready"

# Install Metrics Server
echo ""
echo "📊 Installing Metrics Server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "✅ Metrics server installed"

# Add Helm Repos
echo ""
echo "📦 Adding Helm repositories..."
helm repo add bjw-s https://bjw-s.github.io/helm-charts
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
echo "✅ Helm repos added"

# Setup VS Code (optional)
if command -v code >/dev/null 2>&1; then
    echo ""
    echo "🔧 Setting up VS Code..."
    code --install-extension ms-python.python
    code --install-extension ms-kubernetes-tools.vscode-kubernetes-tools
    code --install-extension ms-azuretools.vscode-docker
    echo "✅ VS Code extensions installed"
fi

# Summary
echo ""
echo "✅ Setup complete!"
echo ""
echo "Kind cluster info:"
kind get clusters
kubectl cluster-info --context kind-agrotech
echo ""
echo "Next steps:"
echo "  1. Start development: skaffold dev"
echo "  2. Open backend: http://localhost:8000"
echo "  3. Open frontend: http://localhost:5173"
echo ""
echo "Useful commands:"
echo "  - skaffold dev                         # Start development"
echo "  - kubectl get pods -A                  # List all pods"
echo "  - kind delete cluster --name agrotech  # Delete cluster"
echo "  - kind load docker-image <image>       # Load image into Kind"
```

### 8.3 VS Code Integration

**.vscode/tasks.json**:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Skaffold Dev",
      "type": "shell",
      "command": "skaffold dev",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Skaffold Debug",
      "type": "shell",
      "command": "skaffold debug",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Kind Start",
      "type": "shell",
      "command": "kind create cluster --config kind-config.yaml --name agrotech",
      "problemMatcher": []
    },
    {
      "label": "Kind Stop",
      "type": "shell",
      "command": "kind delete cluster --name agrotech",
      "problemMatcher": []
    },
    {
      "label": "Kind Load Image",
      "type": "shell",
      "command": "kind load docker-image ${input:imageName} --name agrotech",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "imageName",
      "type": "promptString",
      "description": "Image name to load (e.g., agrotech/backend:latest)"
    }
  ]
}
```

**.vscode/extensions.json**:

```json
{
  "recommendations": [
    "ms-kubernetes-tools.vscode-kubernetes-tools",
    "ms-azuretools.vscode-docker",
    "GoogleCloudTools.cloudcode",
    "ms-python.python",
    "ms-python.vscode-pylance"
  ]
}
```

---

## 9. Continuous Integration

### 9.1 Skaffold in GitHub Actions

**.github/workflows/skaffold-verify.yml**:

```yaml
name: Skaffold Verify

on:
  pull_request:
    branches: [main, develop]

jobs:
  skaffold-build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Skaffold
        run: |
          curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64
          chmod +x skaffold
          sudo mv skaffold /usr/local/bin/
      
      - name: Setup Kind
        uses: helm/kind-action@v1.8.0
        with:
          cluster_name: skaffold-test
      
      - name: Skaffold Build
        run: |
          skaffold build --file-output=build.json
      
      - name: Skaffold Render
        run: |
          skaffold render --build-artifacts=build.json > manifests.yaml
      
      - name: Upload Manifests
        uses: actions/upload-artifact@v3
        with:
          name: k8s-manifests
          path: manifests.yaml
```

### 9.2 Lokale Pre-Push Checks

**.git/hooks/pre-push**:

```bash
#!/bin/bash
set -e

echo "🔍 Running pre-push checks..."

# Skaffold Build Test
echo "Building images..."
skaffold build --quiet

# Skaffold Render Test
echo "Rendering manifests..."
skaffold render > /tmp/manifests.yaml

# Validate Manifests
echo "Validating Kubernetes manifests..."
kubectl apply --dry-run=client -f /tmp/manifests.yaml

echo "✅ All checks passed!"
```

---

## 10. Akzeptanzkriterien

### Definition of Done

- [ ] **Kind Setup**
  - [ ] Dokumentiertes Setup-Script
  - [ ] kind-config.yaml mit extraPortMappings
  - [ ] Multi-Node Cluster (1 Control-Plane + 2 Worker)
  - [ ] Nginx Ingress Controller installiert

- [ ] **Skaffold Konfiguration**
  - [ ] Root skaffold.yaml funktioniert
  - [ ] Backend Hot-Reload < 30s
  - [ ] Frontend Hot-Reload < 30s
  - [ ] File Sync für Python/JS/TS konfiguriert

- [ ] **Development Dockerfiles**
  - [ ] Dockerfile.dev für Backend
  - [ ] Dockerfile.dev für Frontend
  - [ ] BuildKit Cache Mounts
  - [ ] Health Checks

- [ ] **Helm Integration**
  - [ ] values-dev.yaml für alle Charts
  - [ ] Resource Limits für dev optimiert
  - [ ] Ingress disabled (Port-Forward)

- [ ] **Port-Forwarding**
  - [ ] Backend: localhost:8000
  - [ ] Frontend: localhost:5173
  - [ ] ArangoDB: localhost:8529

- [ ] **Debugging**
  - [ ] skaffold debug funktioniert
  - [ ] VS Code Attach Configuration
  - [ ] Python debugpy integration

- [ ] **Performance**
  - [ ] Initial Build < 5 Minuten
  - [ ] Incremental Build < 1 Minute
  - [ ] File Sync < 10 Sekunden
  - [ ] Hot-Reload < 30 Sekunden

- [ ] **Onboarding**
  - [ ] Setup-Script erstellt
  - [ ] Onboarding-Dokumentation
  - [ ] VS Code Tasks konfiguriert
  - [ ] Neuer Entwickler: Setup < 1 Stunde

### Testszenarien

#### Szenario 1: Cold Start (Erster Start)

```bash
# Clean State
kind delete cluster --name agrotech
docker system prune -a --volumes -f

# Start
time ./scripts/dev-setup.sh
time skaffold dev

# Erwartung:
# - Setup: < 3 Minuten (Kind ist schneller als Minikube)
# - Initial Build: < 5 Minuten
# - Backend erreichbar: http://localhost:8000/health/live → 200 OK
# - Frontend erreichbar: http://localhost:5173 → 200 OK
```

#### Szenario 2: Hot-Reload (Code-Änderung)

```bash
# Skaffold läuft

# Python-Datei ändern
echo "# Comment" >> backend/src/services/irrigation.py

# Erwartung:
# - File Sync: < 5 Sekunden
# - FastAPI Reload: < 10 Sekunden
# - API verfügbar: < 30 Sekunden gesamt
```

#### Szenario 3: Dependency-Änderung

```bash
# requirements.txt ändern
echo "httpx==0.26.0" >> backend/requirements.txt

# Erwartung:
# - Rebuild getriggert
# - BuildKit Cache genutzt
# - Rebuild: < 60 Sekunden
# - Deploy: < 30 Sekunden
```

#### Szenario 4: Multi-Service Development

```bash
# Backend + Frontend gleichzeitig
skaffold dev

# Backend ändern
vim backend/src/api/plants.py

# Frontend ändern
vim frontend/src/components/PlantCard.tsx

# Erwartung:
# - Beide Services reloaden parallel
# - Keine gegenseitige Blockierung
# - Gesamt-Zeit: < 45 Sekunden
```

#### Szenario 5: Debug-Session

```bash
# Debug-Modus starten
skaffold debug

# VS Code: Attach to Process
# Breakpoint setzen in irrigation.py:calculate_water_demand()

# API-Call triggern
curl http://localhost:8000/api/v1/irrigation/calculate

# Erwartung:
# - Debugger hält an Breakpoint
# - Variables inspectable
# - Step-through funktioniert
```

---

## 11. Risiken & Mitigations

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|--------|------------|-------------------|------------|
| **Ressourcen-Mangel** | Minikube crasht, langsame Builds | Hoch | Mindest-RAM: 16GB, Dokumentation |
| **Docker-Probleme** | Builds schlagen fehl | Mittel | Diagnostics-Script, Troubleshooting-Guide |
| **File Sync Bugs** | Code-Änderungen nicht sichtbar | Niedrig | Fallback: Rebuild triggern |
| **Port-Konflikte** | Port-Forward schlägt fehl | Mittel | Flexible Ports, Konflikt-Erkennung |
| **Komplexität** | Steile Lernkurve für neue Devs | Hoch | Guided Onboarding, Scripts |

---

## 12. Alternativen & Vergleich

### 12.1 Warum nicht Docker Compose?

| Feature | Docker Compose | Skaffold + Minikube |
|---------|----------------|---------------------|
| **Production-Parity** | ❌ Niedrig | ✅ Hoch |
| **K8s Features** | ❌ Nein | ✅ Ja (HPA, Ingress, etc.) |
| **Helm Charts** | ❌ Nein | ✅ Ja |
| **Hot-Reload** | ✅ Ja | ✅ Ja |
| **Setup-Zeit** | ✅ 5 Minuten | ⚠️ 30 Minuten |
| **Ressourcen** | ✅ Leichtgewichtig | ⚠️ RAM-intensiv |

**Empfehlung**: Docker Compose für Quick Start, Skaffold für Production-like Development.

> **Hinweis:** Es MUSS mindestens Docker Compose File Format Version `3.8` (Compose Spec) verwendet werden. Ältere Versionen (< 3.8) unterstützen wichtige Features wie `healthcheck`-Konfiguration und erweiterte `depends_on`-Syntax nicht vollständig.

### 12.2 Warum Kind statt Minikube?

| Feature | Kind | Minikube |
|---------|------|----------|
| **Setup-Zeit** | ✅ 1-2 Minuten | ⚠️ 3-5 Minuten |
| **Ressourcen** | ✅ Leichtgewichtig | ⚠️ RAM-intensiv |
| **Multi-Node** | ✅ Einfach (Config) | ⚠️ Aufwändig |
| **CI/CD** | ✅ Perfekt | ⚠️ Suboptimal |
| **Port-Mapping** | ✅ Direkt (extraPortMappings) | ⚠️ Port-Forward nötig |
| **Docker Integration** | ✅ Native | ⚠️ Separate VM |
| **Startup** | ✅ Sehr schnell | ⚠️ Langsamer |
| **Dashboard** | ❌ Nein | ✅ Built-in |
| **Addons** | ⚠️ Manuell | ✅ Einfach |

**Empfehlung**: Kind für Production-like Development, Minikube für GUI-Liebhaber.

### 12.3 Warum nicht Tilt?

| Feature | Tilt | Skaffold |
|---------|------|----------|
| **UI** | ✅ Web-basiert | ❌ CLI |
| **Performance** | ✅ Sehr schnell | ✅ Schnell |
| **Complexity** | ⚠️ Eigene DSL (Starlark) | ✅ YAML |
| **Adoption** | ⚠️ Weniger verbreitet | ✅ Industry Standard |

**Empfehlung**: Skaffold für einfachere Onboarding, Tilt für Power-Users.

---

## Anhang A: Skaffold Cheat Sheet

### Grundlegende Commands

```bash
# Development (Watch + Hot-Reload)
skaffold dev

# Debug-Modus
skaffold debug

# Einmalig deployen
skaffold run

# Cleanup
skaffold delete

# Nur bauen
skaffold build

# Manifests generieren
skaffold render

# Config validieren
skaffold diagnose

# Version
skaffold version
```

### Profile-Nutzung

```bash
# Spezifisches Profil
skaffold dev --profile=backend-only

# Mehrere Profile
skaffold dev --profile=backend-only,debug

# Profile per Environment Variable
export SKAFFOLD_PROFILE=prod-like
skaffold dev
```

### Fortgeschrittene Optionen

```bash
# Verbose Logging
skaffold dev -v debug
skaffold dev -v trace

# Kein Port-Forward
skaffold dev --port-forward=off

# Kein Cleanup beim Exit
skaffold dev --cleanup=false

# Namespace override
skaffold dev --namespace=my-namespace

# Tail Logs
skaffold dev --tail

# Custom kubeconfig
skaffold dev --kubeconfig=~/.kube/config-custom
```

---

## Anhang B: Troubleshooting-Guide

### Build-Probleme

```bash
# Problem: BuildKit error
# Lösung:
export DOCKER_BUILDKIT=1
docker system prune -a

# Problem: Layer cache nicht genutzt
# Lösung: BuildKit aktivieren
skaffold.yaml:
  build:
    local:
      useBuildkit: true

# Problem: Image nicht in Kind Cluster
# Lösung:
kind load docker-image agrotech/backend:latest --name agrotech
```

### Deployment-Probleme

```bash
# Problem: Helm release fehlgeschlagen
# Lösung: Manuell aufräumen
helm uninstall -n agrotech-dev backend
skaffold dev

# Problem: Alte Pods bleiben
# Lösung: Force delete
kubectl delete pod -n agrotech-dev --all --force --grace-period=0

# Problem: Ingress nicht erreichbar
# Lösung: Port-Mappings prüfen
docker port agrotech-control-plane
# Sollte zeigen:
# 80/tcp -> 0.0.0.0:80
# 443/tcp -> 0.0.0.0:443
```

### Performance-Probleme

```bash
# Problem: Langsame Builds
# Lösung 1: Docker Ressourcen erhöhen
# Docker Desktop → Preferences → Resources
# CPUs: 6, Memory: 12GB

# Lösung 2: Mehr Worker Nodes
# kind-config.yaml:
# nodes:
# - role: control-plane
# - role: worker
# - role: worker
# - role: worker

# Lösung 3: Lokales Registry
docker run -d -p 5001:5000 --name kind-registry registry:2
docker network connect kind kind-registry
```

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-25
**Review**: Pending
**Genehmigung**: Pending