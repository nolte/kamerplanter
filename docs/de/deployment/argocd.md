# ArgoCD

Kamerplanter lässt sich mit [ArgoCD](https://argo-cd.readthedocs.io/) als GitOps-Deployment verwalten. Da das Helm-Chart als OCI-Artefakt in der GitHub Container Registry liegt, kann ArgoCD es direkt als Helm-Source referenzieren.

---

## Voraussetzungen

ArgoCD
:   Version 2.8+ (OCI-Helm-Support)

Kubernetes-Cluster
:   Version 1.28+

Ingress-Controller
:   Traefik, nginx-ingress oder vergleichbar

---

## Secret vorbereiten

Alle folgenden Beispiele setzen ein Kubernetes Secret voraus, das die sensiblen Zugangsdaten enthält. Erstelle es **vor** dem Anlegen der ArgoCD Application:

```bash
kubectl create namespace kamerplanter

kubectl create secret generic kamerplanter-secrets \
  --namespace kamerplanter \
  --from-literal=ARANGODB_PASSWORD=dein-sicheres-passwort \
  --from-literal=ARANGO_ROOT_PASSWORD=dein-sicheres-passwort
```

Das Secret wird von Backend und ArangoDB per `envFrom` referenziert — so tauchen keine Passwörter im ArgoCD-Manifest oder in der Git-History auf.

!!! tip "Deklaratives Secret-Management"
    Statt `kubectl create secret` manuell auszuführen, empfehlen sich für GitOps-Workflows:

    - [Sealed Secrets](https://sealed-secrets.netlify.app/) — verschlüsselte Secrets im Git-Repository
    - [External Secrets Operator](https://external-secrets.io/) — Secrets aus Vault, AWS SSM, etc.
    - [ArgoCD Vault Plugin](https://argocd-vault-plugin.readthedocs.io/) — inline Secret-Ersetzung

---

## Basis-Application

Minimales ArgoCD `Application`-Manifest ohne Ingress:

```yaml title="argocd/kamerplanter.yaml"
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kamerplanter
  namespace: argocd
spec:
  project: default
  source:
    chart: kamerplanter
    repoURL: oci://ghcr.io/nolte/charts/kamerplanter
    targetRevision: 0.2.0
    helm:
      valuesObject:
        controllers:
          backend:
            containers:
              main:
                envFrom:                                        # (1)!
                  - secretRef:
                      name: kamerplanter-secrets
                env:
                  ARANGODB_HOST: kamerplanter-arangodb
                  ARANGODB_PORT: "8529"
                  ARANGODB_DATABASE: kamerplanter
                  ARANGODB_USERNAME: root
                  REDIS_URL: redis://kamerplanter-valkey:6379/0
                  CORS_ORIGINS: '["https://pflanzen.example.com"]'
                  KAMERPLANTER_MODE: light
          arangodb:
            containers:
              main:
                envFrom:                                        # (2)!
                  - secretRef:
                      name: kamerplanter-secrets
  destination:
    server: https://kubernetes.default.svc
    namespace: kamerplanter
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

1. `ARANGODB_PASSWORD` wird aus dem Secret `kamerplanter-secrets` injiziert.
2. `ARANGO_ROOT_PASSWORD` wird aus demselben Secret injiziert.

---

## Ingress mit TLS

Vollständiges Beispiel mit Ingress, TLS über cert-manager und Traefik als Ingress-Controller:

```yaml title="argocd/kamerplanter-ingress-tls.yaml"
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kamerplanter
  namespace: argocd
spec:
  project: default
  source:
    chart: kamerplanter
    repoURL: oci://ghcr.io/nolte/charts/kamerplanter
    targetRevision: 0.2.0
    helm:
      valuesObject:
        controllers:
          backend:
            containers:
              main:
                envFrom:
                  - secretRef:
                      name: kamerplanter-secrets
                env:
                  ARANGODB_HOST: kamerplanter-arangodb
                  ARANGODB_PORT: "8529"
                  ARANGODB_DATABASE: kamerplanter
                  ARANGODB_USERNAME: root
                  REDIS_URL: redis://kamerplanter-valkey:6379/0
                  CORS_ORIGINS: '["https://pflanzen.example.com"]'
                  KAMERPLANTER_MODE: standard
          arangodb:
            containers:
              main:
                envFrom:
                  - secretRef:
                      name: kamerplanter-secrets

        ingress:
          main:
            enabled: true
            className: traefik                                  # (1)!
            annotations:
              cert-manager.io/cluster-issuer: letsencrypt-prod  # (2)!
              traefik.ingress.kubernetes.io/router.entrypoints: websecure
              traefik.ingress.kubernetes.io/router.tls: "true"
            hosts:
              - host: pflanzen.example.com                      # (3)!
                paths:
                  - path: /api
                    pathType: Prefix
                    service:
                      identifier: backend
                  - path: /
                    pathType: Prefix
                    service:
                      identifier: frontend
            tls:
              - secretName: kamerplanter-tls                    # (4)!
                hosts:
                  - pflanzen.example.com

  destination:
    server: https://kubernetes.default.svc
    namespace: kamerplanter
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

1. Für nginx-ingress: `className: nginx` verwenden und die Traefik-Annotations durch `nginx.ingress.kubernetes.io/proxy-body-size: "10m"` ersetzen.
2. Setzt voraus, dass ein `ClusterIssuer` namens `letsencrypt-prod` im Cluster existiert. Falls du bereits ein Wildcard-Zertifikat hast, entferne diese Annotation und referenziere das bestehende TLS-Secret direkt.
3. Dein gewünschter Hostname. Der DNS-Eintrag muss auf den Ingress-Controller zeigen.
4. cert-manager erstellt dieses Secret automatisch. Bei einem bestehenden Wildcard-Zertifikat: den Namen des vorhandenen Secrets verwenden (z.B. `wildcard-example-com-tls`).

---

## Externe Values-Datei

Statt alle Values inline im Application-Manifest zu pflegen, kannst du eine separate Values-Datei in einem Git-Repository verwenden:

```yaml title="argocd/kamerplanter-multi-source.yaml"
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kamerplanter
  namespace: argocd
spec:
  project: default
  sources:
    - repoURL: https://github.com/dein-user/homelab-config.git
      targetRevision: main
      ref: values
    - chart: kamerplanter
      repoURL: oci://ghcr.io/nolte/charts/kamerplanter
      targetRevision: 0.2.0
      helm:
        valueFiles:
          - $values/kamerplanter/values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: kamerplanter
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

So bleiben umgebungsspezifische Konfiguration im eigenen Repository. Die Values-Datei nutzt ebenfalls `envFrom` mit dem Secret — keine Passwörter im Git.

---

## Siehe auch

- [Helm Charts](helm.md) — Chart-Struktur und Konfigurationsreferenz
- [Kubernetes-Deployment](kubernetes.md) — Manuelles Deployment mit `helm install`
- [CI/CD](ci-cd.md) — Automatische Builds mit GitHub Actions
