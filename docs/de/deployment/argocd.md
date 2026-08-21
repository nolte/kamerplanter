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
  --from-literal=ARANGO_ROOT_PASSWORD=dein-sicheres-passwort \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=FERNET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  --from-literal=ERASURE_TOMBSTONE_SALT="$(openssl rand -hex 32)"
```

Das Secret wird von Backend und ArangoDB per `envFrom` referenziert — so tauchen keine Passwörter im ArgoCD-Manifest oder in der Git-History auf.

!!! danger "Ohne die drei letzten Werte startet der Backend-Pod nicht"
    `JWT_SECRET_KEY`, `FERNET_KEY` und `ERASURE_TOMBSTONE_SALT` sind — unabhängig von `ARANGODB_PASSWORD`/`ARANGO_ROOT_PASSWORD` — eigenständige Boot-Blocker: Das Backend bricht bei `DEBUG=false` mit `SystemExit` ab, wenn einer der drei Werte fehlt oder (bei `ERASURE_TOMBSTONE_SALT`) kürzer als 32 Zeichen ist. Vollständige Übersicht: [Konfigurationsmatrix — Pflicht-Secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

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

!!! warning "Kein `image.tag` in `valuesObject` überschreiben"

    Das veröffentlichte Chart pinnt jedes Kamerplanter-Image auf
    `<version>@sha256:<digest>` — der Digest benennt die Bytes und kann sich
    nicht bewegen. Ein eigener `image.tag` in `valuesObject` gewinnt gegen
    diesen Default und ersetzt ihn durch eine bewegliche Referenz; zusammen mit
    `pullPolicy: IfNotPresent` liefert der Node dann aus, was er zufällig schon
    im Cache hat. Arbeitsteilung: `targetRevision` wählt die **Chart-Version**,
    das Chart wählt die **Bytes**. Warum das zweimal gemessen schiefging:
    [CI/CD — Invariante: kein `image.tag` im Overlay](ci-cd.md#invariante-kein-image-tag).

!!! danger "`targetRevision` niemals auf den `-dev`-Kanal"

    `0.2.0` oben ist die Version eines **veröffentlichten** Releases — mit einer
    Einschränkung, die am Ende dieses Kastens steht. Daneben gibt es einen zweiten
    Kanal: Der `develop`-Baum trägt eine Vorabversion mit dem Zusatz `-dev`
    (derzeit `0.2.1-dev`), und dieser OCI-Tag wird von jedem Merge nach `develop`
    überschrieben, der `helm/` berührt. Genau dafür ist er da. Erzwungen ist nur
    der Bezeichner `dev`, nicht die Nummer davor: Die `-dev`-Version muss der
    veröffentlichten Linie nicht voraus sein.

    Eine `Application`, die darauf zeigt, hat damit keinen festen Stand mehr:
    ArgoCD synct beim nächsten Merge andere Bytes unter unverändertem
    `targetRevision`, und im GitOps-Repository ändert sich dabei nichts, was
    jemand im Review sehen könnte. Ein Overlay verankert deshalb ausschließlich
    eine reine Versionsnummer ohne Zusatz — oder den Manifest-Digest. Der
    Vorab-Bezeichner `dev` ist umgekehrt für Release-Tags gesperrt, ein
    `-dev`-Stand kann also nie versehentlich zu einem Release werden. Die
    Kanaltrennung im Detail: [CI/CD — Zwei Kanäle](ci-cd.md#zwei-kanaele).
    <!-- #1222 -->

    Die Einschränkung: Ausgerechnet `charts/kamerplanter:0.2.0` ist der eine
    Tag, bei dem genau das schiefgegangen ist, bevor es die beiden Prüfungen
    gab. Er wurde am 18.08.2026 aus `develop` neu gepusht (Manifest-Annotation
    `org.opencontainers.image.created: 2026-08-18T14:09:14Z`), fünf Tage nach
    der Veröffentlichung des Releases `v0.2.0` — und wird bewusst nicht
    repariert, weil ein weiterer Push unter derselben Versionsreferenz derselbe
    Fehler wäre. Ein `targetRevision: 0.2.0` synct also einen `develop`-Stand.
    `0.2.1` — veröffentlicht am 19.08.2026 und das erste Release unter beiden
    Prüfungen — ist jetzt der jüngste Chart-Tag, dessen Manifest seinen
    eigenen Release-Zeitstempel trägt (`org.opencontainers.image.created:
    2026-08-19T13:53:11Z`); zuvor war `0.1.0` (erstellt am 06.08.2026) der
    jüngste solche Tag. Verankere dort, oder pinne ansonsten den
    Manifest-Digest.
    <!-- #1222 -->

---

## Ingress mit TLS

Vollständiges Beispiel mit Ingress, TLS über cert-manager und Traefik als Ingress-Controller:

!!! warning "`targetRevision: 0.2.0` trägt dieselbe Einschränkung"

    Dieser Chart-Tag wurde aus `develop` überschrieben; siehe
    [Basis-Application](#basis-application).
    <!-- #1222 -->

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
                  KAMERPLANTER_MODE: full
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

!!! warning "`targetRevision: 0.2.0` trägt dieselbe Einschränkung"

    Dieser Chart-Tag wurde aus `develop` überschrieben; siehe
    [Basis-Application](#basis-application).
    <!-- #1222 -->

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
