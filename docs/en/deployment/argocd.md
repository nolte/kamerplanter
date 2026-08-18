# ArgoCD

Kamerplanter can be managed as a GitOps deployment with [ArgoCD](https://argo-cd.readthedocs.io/). Since the Helm chart is published as an OCI artifact on the GitHub Container Registry, ArgoCD can reference it directly as a Helm source.

---

## Prerequisites

ArgoCD
:   Version 2.8+ (OCI Helm support)

Kubernetes cluster
:   Version 1.28+

Ingress controller
:   Traefik, nginx-ingress, or comparable

---

## Prepare the Secret

All following examples expect a Kubernetes Secret containing the sensitive credentials. Create it **before** creating the ArgoCD Application:

```bash
kubectl create namespace kamerplanter

kubectl create secret generic kamerplanter-secrets \
  --namespace kamerplanter \
  --from-literal=ARANGODB_PASSWORD=your-secure-password \
  --from-literal=ARANGO_ROOT_PASSWORD=your-secure-password \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=FERNET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  --from-literal=ERASURE_TOMBSTONE_SALT="$(openssl rand -hex 32)"
```

The Secret is referenced by both backend and ArangoDB via `envFrom` — no passwords appear in ArgoCD manifests or Git history.

!!! danger "Without the last three values the backend pod won't start"
    `JWT_SECRET_KEY`, `FERNET_KEY` and `ERASURE_TOMBSTONE_SALT` are independent boot blockers — separate from `ARANGODB_PASSWORD`/`ARANGO_ROOT_PASSWORD`: the backend aborts with `SystemExit` when `DEBUG=false` if any of the three is missing, or (for `ERASURE_TOMBSTONE_SALT`) shorter than 32 characters. Full overview: [Configuration Matrix — Mandatory secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

!!! tip "Declarative secret management"
    Instead of running `kubectl create secret` manually, consider these options for GitOps workflows:

    - [Sealed Secrets](https://sealed-secrets.netlify.app/) — encrypted secrets in Git repositories
    - [External Secrets Operator](https://external-secrets.io/) — secrets from Vault, AWS SSM, etc.
    - [ArgoCD Vault Plugin](https://argocd-vault-plugin.readthedocs.io/) — inline secret substitution

---

## Basic Application

Minimal ArgoCD `Application` manifest without Ingress:

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
                  CORS_ORIGINS: '["https://plants.example.com"]'
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

1. `ARANGODB_PASSWORD` is injected from the `kamerplanter-secrets` Secret.
2. `ARANGO_ROOT_PASSWORD` is injected from the same Secret.

!!! warning "Do not override `image.tag` in `valuesObject`"

    The published chart pins every Kamerplanter image to
    `<version>@sha256:<digest>` — the digest names the bytes and cannot move. An
    `image.tag` of your own in `valuesObject` beats that default and replaces it
    with a moving reference; together with `pullPolicy: IfNotPresent` the node
    then serves whatever it happens to have cached. Division of responsibility:
    `targetRevision` selects the **chart version**, the chart selects the
    **bytes**. Why this went wrong twice, measured:
    [CI/CD — Invariant: no `image.tag` in the overlay](ci-cd.md#invariant-no-image-tag).

!!! danger "Never point `targetRevision` at the `-dev` channel"

    The `0.2.0` above is the version of a **published** release — with one
    caveat, at the end of this box. Alongside it there is a second channel: the
    `develop` tree carries a pre-release with the `-dev` suffix (`0.2.1-dev` at
    the moment), and that OCI tag is overwritten by every merge into `develop`
    that touches `helm/`. That is exactly what it is for. Only the `dev`
    identifier is enforced, not the number in front of it: the `-dev` version is
    not guaranteed to lead the published line.

    An `Application` pointing at it no longer has a fixed state: on the next
    merge ArgoCD syncs different bytes under an unchanged `targetRevision`, and
    nothing changes in the GitOps repository that anyone could catch in review.
    An overlay therefore anchors only a bare version number without a suffix —
    or the manifest digest. Conversely, the `dev` pre-release identifier is
    refused for release tags, so a `-dev` state can never accidentally become a
    release. The channel separation in detail:
    [CI/CD — Two channels](ci-cd.md#two-channels).
    <!-- #1222 -->

    The caveat: `charts/kamerplanter:0.2.0` of all tags is the one where exactly
    that went wrong, before the two checks existed. It was re-pushed from
    `develop` on 2026-08-18 (manifest annotation
    `org.opencontainers.image.created: 2026-08-18T14:09:14Z`), five days after
    release `v0.2.0` was published — and it is deliberately not repaired,
    because another push under the same version reference would be the same
    mistake again. A `targetRevision: 0.2.0` therefore syncs a `develop` build.
    `0.1.0` is the newest chart tag whose manifest still carries its release
    timestamp; otherwise pin the manifest digest, or wait for the first release
    created under both checks (`v0.2.1`, a draft at the moment).
    <!-- #1222 -->

---

## Ingress with TLS

Complete example with Ingress, TLS via cert-manager, and Traefik as Ingress controller:

!!! warning "`targetRevision: 0.2.0` carries the same caveat"

    That chart tag was overwritten from `develop`; see
    [Basic Application](#basic-application).
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
                  CORS_ORIGINS: '["https://plants.example.com"]'
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
              - host: plants.example.com                        # (3)!
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
                  - plants.example.com

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

1. For nginx-ingress: use `className: nginx` and replace the Traefik annotations with `nginx.ingress.kubernetes.io/proxy-body-size: "10m"`.
2. Requires a `ClusterIssuer` named `letsencrypt-prod` in the cluster. If you already have a wildcard certificate, remove this annotation and reference the existing TLS secret directly.
3. Your desired hostname. The DNS record must point to the Ingress controller.
4. cert-manager creates this Secret automatically. For an existing wildcard certificate: use the name of the existing secret (e.g. `wildcard-example-com-tls`).

---

## External values file

Instead of maintaining all values inline in the Application manifest, you can use a separate values file from a Git repository:

!!! warning "`targetRevision: 0.2.0` carries the same caveat"

    That chart tag was overwritten from `develop`; see
    [Basic Application](#basic-application).
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
    - repoURL: https://github.com/your-user/homelab-config.git
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

This keeps environment-specific configuration in your own repository. The values file also uses `envFrom` with the Secret — no passwords in Git.

---

## See also

- [Helm Charts](helm.md) — Chart structure and configuration reference
- [Kubernetes Deployment](kubernetes.md) — Manual deployment with `helm install`
- [CI/CD](ci-cd.md) — Automated builds with GitHub Actions
