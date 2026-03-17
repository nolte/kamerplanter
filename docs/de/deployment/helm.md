# Helm Charts

Das Kamerplanter Helm-Chart basiert auf der [bjw-s common library](https://bjw-s-labs.github.io/helm-charts/) und definiert alle Kubernetes-Ressourcen in einem einzigen Chart. Container-Images und das Chart selbst werden als OCI-Artefakte über die GitHub Container Registry bereitgestellt.

---

## Registry-Übersicht

| Artefakt | OCI-URL |
|----------|---------|
| Helm-Chart | `oci://ghcr.io/nolte/kamerplanter-helm/kamerplanter` |
| Backend-Image | `ghcr.io/nolte/kamerplanter-backend` |
| Frontend-Image | `ghcr.io/nolte/kamerplanter-frontend` |

---

## Chart-Informationen

```yaml
name: kamerplanter
type: application
version: 0.2.0          # Chart-Version (Helm-spezifisch)
appVersion: "1.0.0"     # Anwendungs-Version
```

### Abhängigkeiten

| Dependency | Version | Quelle | Zweck |
|-----------|---------|--------|-------|
| common (bjw-s) | 4.6.2 | bjw-s-labs Helm-Charts | Library-Chart für einheitliche Kubernetes-Ressourcen |
| valkey | 0.9.3 | OCI: ghcr.io/valkey-io/valkey-helm | Redis-kompatibler Cache + Celery-Broker |

---

## Chart-Struktur

```
helm/kamerplanter/
├── Chart.yaml            # Chart-Metadaten und Abhängigkeiten
├── Chart.lock            # Pinned Dependency-Versionen
├── values.yaml           # Standard-Werte (Produktion)
├── values-dev.yaml       # Override für Entwicklung
├── templates/
│   └── common.yaml       # bjw-s Library-Loader
└── charts/
    ├── common-4.6.2.tgz  # bjw-s Common Library
    └── valkey-0.9.3.tgz  # Valkey Sub-Chart
```

Das Chart nutzt den bjw-s `common.loader.all`-Ansatz: Alle Kubernetes-Ressourcen (Deployments, StatefulSets, Services, ConfigMaps, Ingress) werden deklarativ über `values.yaml` definiert — es gibt keine eigenen Templates.

---

## Konfigurationsreferenz

### Controller (Deployments & StatefulSets)

#### Backend

```yaml
controllers:
  backend:
    type: deployment
    replicas: 2                    # Anpassbar
    strategy: RollingUpdate
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-backend
          tag: latest              # In Produktion: feste Version verwenden
        env:
          ARANGODB_HOST: "..."
          ARANGODB_PORT: "8529"
          ARANGODB_DATABASE: "kamerplanter"
          ARANGODB_USERNAME: "root"
          ARANGODB_PASSWORD: "..."
          REDIS_URL: "redis://kamerplanter-valkey:6379/0"
          CORS_ORIGINS: '["..."]'
          DEBUG: "false"
          KAMERPLANTER_MODE: "light"    # oder "standard"
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: "1"
            memory: 512Mi
```

#### Frontend

```yaml
controllers:
  frontend:
    type: deployment
    replicas: 2
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-frontend
          tag: latest
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
```

Das Frontend wird hinter nginx ausgeliefert. Die nginx-Konfiguration wird automatisch als ConfigMap gemountet und leitet `/api/`-Anfragen an das Backend weiter.

#### ArangoDB

```yaml
controllers:
  arangodb:
    type: statefulset
    replicas: 1                    # Single-Node (kein Cluster)
    containers:
      main:
        image:
          repository: arangodb
          tag: "3.11"
        env:
          ARANGO_ROOT_PASSWORD: "..."
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: "1"
            memory: 1Gi
    statefulset:
      volumeClaimTemplates:
        - name: data
          accessMode: ReadWriteOnce
          size: 5Gi                 # Anpassbar
          globalMounts:
            - path: /var/lib/arangodb3
```

### Services

```yaml
service:
  backend:
    controller: backend
    ports:
      http:
        port: 8000
  frontend:
    controller: frontend
    ports:
      http:
        port: 80
  arangodb:
    controller: arangodb
    ports:
      http:
        port: 8529
```

### Ingress

```yaml
ingress:
  main:
    enabled: true                   # Standard: deaktiviert
    hosts:
      - host: pflanzen.example.com
        paths:
          - path: /api
            pathType: Prefix
            service:
              identifier: backend
          - path: /
            pathType: Prefix
            service:
              identifier: frontend
```

!!! tip "TLS"
    Für HTTPS füge eine `tls`-Sektion hinzu und verwende z.B. cert-manager mit Let's Encrypt:

    ```yaml
    ingress:
      main:
        enabled: true
        annotations:
          cert-manager.io/cluster-issuer: letsencrypt-prod
        hosts:
          - host: pflanzen.example.com
            paths: [...]
        tls:
          - secretName: kamerplanter-tls
            hosts:
              - pflanzen.example.com
    ```

### Valkey (Redis-kompatibler Cache)

```yaml
valkey:
  dataStorage:
    enabled: true
    size: 1Gi
```

---

## Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|----------|:-------:|----------|-------------|
| `ARANGODB_HOST` | Ja | — | Hostname des ArangoDB-Service |
| `ARANGODB_PORT` | Ja | `8529` | Port des ArangoDB-Service |
| `ARANGODB_DATABASE` | Ja | `kamerplanter` | Datenbankname |
| `ARANGODB_USERNAME` | Ja | `root` | Datenbank-Benutzer |
| `ARANGODB_PASSWORD` | Ja | — | Datenbank-Passwort |
| `ARANGO_ROOT_PASSWORD` | Ja | — | ArangoDB Root-Passwort (muss identisch mit `ARANGODB_PASSWORD` sein) |
| `REDIS_URL` | Ja | — | Valkey/Redis-Verbindungs-URL |
| `CORS_ORIGINS` | Ja | — | Erlaubte Origins als JSON-Array |
| `DEBUG` | Nein | `false` | Debug-Modus aktivieren |
| `KAMERPLANTER_MODE` | Nein | `light` | `light` (ohne Auth) oder `standard` (mit Auth) |
| `REQUIRE_EMAIL_VERIFICATION` | Nein | `false` | E-Mail-Verifikation bei Registrierung |

---

## Entwicklungs-Overrides (values-dev.yaml)

Für die lokale Entwicklung existiert eine separate Values-Datei, die Skaffold automatisch verwendet:

| Einstellung | Produktion | Entwicklung |
|------------|-----------|-------------|
| Replicas (Backend/Frontend) | 2 | 1 |
| Update-Strategie | RollingUpdate | Recreate |
| DEBUG | false | true |
| Resource Limits | Streng | Großzügig |
| Frontend-Port | 80 (nginx) | 5173 (Vite Dev Server) |
| ArangoDB PVC | 5 Gi | 2 Gi |
| Ingress-Host | (konfigurierbar) | `kamerplanter.local` |

---

## Häufige Anpassungen

### Ressourcen reduzieren (kleiner Cluster / Raspberry Pi)

```yaml
controllers:
  backend:
    replicas: 1
    containers:
      main:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
  frontend:
    replicas: 1
    containers:
      main:
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 250m
            memory: 128Mi
  arangodb:
    containers:
      main:
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Bestimmte Image-Version pinnen

```yaml
controllers:
  backend:
    containers:
      main:
        image:
          tag: "1.2.3"    # Statt "latest"
  frontend:
    containers:
      main:
        image:
          tag: "1.2.3"
```

!!! tip "Image-Tags"
    Verwende in Produktion immer feste Versions-Tags statt `latest`. So stellst du sicher, dass ein `helm upgrade` die erwartete Version deployt.

---

## Siehe auch

- [Kubernetes-Deployment](kubernetes.md) — Schritt-für-Schritt-Anleitung
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Referenz aller Umgebungsvariablen
