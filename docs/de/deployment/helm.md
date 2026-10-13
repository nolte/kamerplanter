# Helm Charts

Das Kamerplanter Helm-Chart basiert auf der [bjw-s common library](https://bjw-s-labs.github.io/helm-charts/) und definiert alle Kubernetes-Ressourcen in einem einzigen Chart. Container-Images und das Chart selbst werden als OCI-Artefakte über die GitHub Container Registry bereitgestellt.

---

## Registry-Übersicht

| Artefakt | OCI-URL |
|----------|---------|
| Helm-Chart | `oci://ghcr.io/nolte/charts/kamerplanter` |
| Backend-Image | `ghcr.io/nolte/kamerplanter-backend` |
| Frontend-Image | `ghcr.io/nolte/kamerplanter-frontend` |

---

## Chart-Informationen

<!-- Quelle: helm/kamerplanter/Chart.yaml -->

```yaml
name: kamerplanter
type: application
version: 0.2.1-dev      # Chart-Version im develop-Baum — Vorabkanal
appVersion: "1.0.0"     # Anwendungs-Version
```

!!! danger "`-dev` ist der Entwicklungskanal, kein Release"

    Der Zusatz `-dev` ist kein Schreibfehler. Der `develop`-Baum trägt immer
    eine Vorabversion mit diesem Zusatz, und `helm push` leitet den OCI-Tag
    wörtlich aus dieser Zeile ab. Der Tag
    `oci://ghcr.io/nolte/charts/kamerplanter:0.2.1-dev` wird deshalb bei jedem
    Merge nach `develop` überschrieben, der `helm/` berührt — das ist der Zweck
    dieses Kanals.

    Ein Release publiziert dagegen unter der reinen Version ohne Zusatz, etwa
    `0.1.0`. Die beiden Kanäle sind disjunkt und können sich nicht überschneiden:
    Der Vorab-Bezeichner `dev` ist im Release-Pfad gesperrt, ein Tag `v0.3.0-dev`
    wird abgewiesen. `-rc` und `-beta` bleiben erlaubt.

    Erzwungen ist allein der Bezeichner `dev`, nicht die Nummer davor. `0.2.1`
    benennt das beabsichtigte nächste Release, ohne dass irgendetwas den Wert
    vor der veröffentlichten Linie hält — sobald `v0.2.1` erscheint, sortiert
    `0.2.1-dev` darunter, und kein Turnus hebt ihn an. Das ist Absicht: Jede
    `-dev`-Nummer ist kollisionssicher, ein regelmäßiger Bump brächte nichts.

    **Verwende in keinem Deployment eine `-dev`-Version.** Pinne eine
    veröffentlichte Version oder den Manifest-Digest. Warum das keine Theorie
    ist, und wie beide Kanäle abgesichert sind:
    [CI/CD — Zwei Kanäle](ci-cd.md#zwei-kanaele).
    <!-- #1222 -->

### Abhängigkeiten

| Dependency | Version | Quelle | Zweck |
|-----------|---------|--------|-------|
| common (bjw-s) | 5.2.1 | bjw-s-labs Helm-Charts | Library-Chart für einheitliche Kubernetes-Ressourcen |
| valkey | 0.12.0 | OCI: ghcr.io/valkey-io/valkey-helm | Redis-kompatibler Cache + Celery-Broker |
| ollama | 1.87.0 | `otwld/ollama-helm` | Lokale LLM-Inferenz, standardmäßig aus (`ollama.enabled: false`) |

<!-- Quelle: helm/kamerplanter/Chart.yaml -->

!!! note "Ollama-Subchart standardmäßig aus"
    Der Ollama-Helm-Chart (`otwld/ollama-helm`) ist als dritte Abhängigkeit eingetragen, wird aber nur mit `ollama.enabled: true` gerendert. Ohne diesen Schalter enthält das Release kein Ollama; wie die Betriebsprofile Ollama einsetzen, steht unter [Betriebsprofile → Profi](betriebsprofile.md#profi).

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
    ├── common-5.2.1.tgz  # bjw-s Common Library
    ├── valkey-0.12.0.tgz # Valkey Sub-Chart
    └── ollama-1.87.0.tgz # Ollama Sub-Chart (standardmäßig aus)
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
    replicas: 1                    # Chart-Default; für Produktion i. d. R. auf 2 erhöhen (siehe Kubernetes-Deployment)
    strategy: RollingUpdate
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-backend
          tag: 0.2.1@sha256:af9bec…    # unveränderlicher Digest, vom Release-Job gesetzt — siehe "Bestimmte Image-Version pinnen"
        envFrom:
          - secret: kamerplanter-secrets    # ARANGODB_PASSWORD, JWT_SECRET_KEY, FERNET_KEY, ERASURE_TOMBSTONE_SALT, LOG_PSEUDONYM_SALT
        env:
          ARANGODB_HOST: "..."
          ARANGODB_PORT: "8529"
          ARANGODB_DATABASE: "kamerplanter"
          ARANGODB_USERNAME: '{{ .Values.database.arangodb.appUsername }}'    # kamerplanter
          REDIS_URL: "redis://kamerplanter-valkey:6379/0"
          CORS_ORIGINS: '["..."]'
          DEBUG: "false"
          KAMERPLANTER_MODE: "light"    # oder "full" (Chart-Default)
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: "1"
            memory: 2Gi                 # Bild-Uploads (REQ-034) dekodieren im Speicher — 512Mi OOMKillt beim Upload
```

!!! danger "`ARANGODB_PASSWORD`, `JWT_SECRET_KEY`, `FERNET_KEY`, `ERASURE_TOMBSTONE_SALT`, `LOG_PSEUDONYM_SALT` kommen NIE aus `env:`"
    Der reale Chart deklariert diese fünf Werte absichtlich **nicht** im `env:`-Block — sie kommen ausschließlich per `envFrom: - secret: kamerplanter-secrets` aus einem vorher angelegten Kubernetes-Secret. Ohne dieses Secret (bzw. mit einem unveränderten Default-Wert darin) verweigert das Backend bei `DEBUG=false` den Start; der Celery-Worker-Controller bezieht dasselbe Secret und prüft `LOG_PSEUDONYM_SALT` ebenso streng. Details: [Kubernetes-Deployment — Pflicht-Secrets anlegen](kubernetes.md), [Konfigurationsmatrix — Pflicht-Secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

#### Celery-Worker {#celery-worker}

Der Worker verarbeitet drei Warteschlangen (Issue #2128):

| Queue | Inhalt |
|---|---|
| `critical` | Aufbewahrungsfristen und Löschungen (NFR-011), Sicherheits- und Datenschutz-Aufräumläufe, Benachrichtigungen, Frostwarnungen, Aktor-Regelkreis |
| `celery` | alles Übrige — Celerys Standard-Queue unter ihrem bisherigen Namen |
| `bulk` | lange, externe Läufe: Datensatz- und Referenzbild-Erfassung, Stammdaten-Anreicherung, Glossar-Vorwärmen, Storage-Migrationen |

Der Chart startet den Worker mit `-Q critical,celery,bulk`. **Eine Queue, die kein Worker liest, behält ihre Aufgaben für immer in Valkey** — ohne Fehlermeldung. Wenn du die Worker-`args` in deinen Values überschreibst, übernimm die Queue-Liste vollständig oder lass `-Q` ganz weg (dann liest der Worker alle Queues, die die Anwendung deklariert).

##### Ein Worker pro Queue {#celery-worker-pro-queue}

Mit einem Schalter bekommt jede Queue ihren eigenen Worker:

```yaml
celeryWorkers:
  dedicatedQueues: true
```

| Deployment | Queue |
|---|---|
| `celery-worker` | `critical` |
| `celery-worker-default` | `celery` |
| `celery-worker-bulk` | `bulk` |

Ohne den Schalter (Standard) liest der eine `celery-worker` alle drei Queues. Ein langer Lauf in `bulk` belegt dann einen seiner zwei Prozesse; der zweite arbeitet weiter. Mit dem Schalter kann eine Datensatz- oder Bilderfassung eine Erinnerung, eine Löschung oder eine Frostwarnung gar nicht mehr aufhalten.

Die beiden zusätzlichen Worker sind Kopien von `celery-worker`: Der Chart erzeugt sie beim Rendern aus den **zusammengeführten** Values. Alles, was du in einem Overlay, per `--set` oder im ArgoCD-`valuesObject` an `controllers.celery-worker` setzt (Image, Umgebung, `securityContext`, Probes, Ressourcen, Pod-Optionen) und an `networkpolicies.celery-worker` (Egress), gilt damit auch für die Kopien. Jede Policy, die `celery-worker` als Gegenstelle zulässt (ArangoDB, Valkey, inference-service), lässt auch die Kopien zu, und jedes Volume des Workers wird auch in die Kopien gemountet. Nur die Queue unterscheidet sich. Eine einzelne Kopie stimmst du über `controllers.<kopie>.<schlüssel>` ab, z. B. `controllers.celery-worker-bulk.containers.main.resources`; der Schlüssel wird über die Kopie gelegt. Ohne den Schalter gibt es keine Kopien, solche Schlüssel bleiben dann wirkungslos.

!!! warning "Zwei Pods mehr auf dem Node des Backends"
    Jeder zusätzliche Worker fordert wie `celery-worker` 100m CPU und 512 Mi Speicher an (Limit 2 Gi). Mit dem Standard-Volume `ReadWriteOnce` laufen alle Pods, die die Anhänge mounten, auf **einem** Node — dem des Backends. Plane dessen Speicher dafür ein, oder stelle auf [S3](#storage-konfiguration-nfr-013) um; dann verteilen sich die Worker frei.

Schaltet ein Profil `celery-worker` ab (die `ki`- und `recognition`-Overlays), entstehen auch keine Kopien. Überschreibst du die Worker-`args` selbst, gilt weiter: Jede Queue braucht mindestens einen Worker, der sie liest.

**Bestätigung erst nach dem Lauf.** Aufräumläufe, deren zweiter Durchlauf nichts mehr findet (abgelaufene Tokens, Einwilligungen, Audit-Einträge, Löschnachweise, IP-Anonymisierung, abgelaufene Overrides), bestätigen ihre Nachricht erst, wenn sie fertig sind. Verschwindet ein Worker-Pod mitten im Lauf, vergibt Valkey die Nachricht nach der Sichtbarkeitsfrist (gut vier Stunden) neu, statt den Lauf bis zum nächsten Tag zu verlieren. Benachrichtigungen, der Aktor-Regelkreis und Löschläufe bestätigen weiter beim Start — ein zweiter Lauf würde dort doppelt benachrichtigen oder schalten.

**Bereitschaft (Issue #2154).** Der Worker gilt erst als bereit, wenn er Aufgaben annimmt: Mit `WORKER_READY_FILE` prüft er beim Start seine ArangoDB-Anmeldung (bis zu 60 Sekunden), schreibt die Datei, sobald sein Consumer läuft, und Startup- und Readiness-Probe testen sie (`test -f`, kostet praktisch nichts). Kann sich ein neuer Worker nach einem Upgrade nicht anmelden — falsches Passwort, Anwendungskonto nicht angelegt —, beendet er sich, wird nie bereit, und der Rollout behält den alten Worker. Die Liveness-Probe fragt mit `inspect ping -d "celery@${HOSTNAME}"` gezielt den eigenen Worker; ein `inspect ping` ohne Ziel gelingt, solange irgendein Worker antwortet.

Jede Aufgabe hat ein Zeitlimit als Notbremse: 30 Minuten (weich, die Aufgabe kann aufräumen), nach 35 Minuten wird der Prozess beendet. Läufe, die fortsetzbar sind oder bewusst gestartet werden (Löschläufe, Datenexport, Storage-Migration, Datensatz-Erfassung), haben drei Stunden. Jeder Worker-Prozess reserviert nur noch eine Nachricht im Voraus statt vier.

#### Frontend

```yaml
controllers:
  frontend:
    type: deployment
    replicas: 1                    # Chart-Default; für Produktion i. d. R. auf 2 erhöhen
    containers:
      main:
        image:
          repository: ghcr.io/nolte/kamerplanter-frontend
          tag: latest@sha256:fea5a3…
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
          tag: "3.12.9"
        env:
          ARANGO_ROOT_PASSWORD:             # nur ARANGO_ROOT_PASSWORD, nicht das ganze Secret
            valueFrom:
              secretKeyRef:
                name: '{{ .Values.database.arangodb.rootPasswordSecret }}'
                key: ARANGO_ROOT_PASSWORD
                optional: true
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
          advancedMounts:
            main:
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
        port: 80          # Service-Port bleibt 80 (Ingress/DNS)
        targetPort: 8080  # nginx-unprivileged-Container lauscht auf 8080, nicht 80
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
    enabled: true                   # ohne hosts entsteht kein Ingress
    hosts:
      - host: pflanzen.example.com
        paths:
          - path: /              # auch /api: das Frontend-nginx leitet es ans Backend weiter
            pathType: Prefix
            service:
              identifier: frontend
```

Leite `/api` nicht direkt auf den Backend-Service: Die NetworkPolicy des Backends lässt nur das Frontend auf Port 8000 zu, und das Frontend-nginx setzt die Upload-Grenze sowie den `X-Forwarded-For`-Eintrag, auf den `TRUSTED_PROXY_HOPS: "1"` abgestimmt ist.

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

#### Upload-Grenze (Request-Body)

Das Frontend-nginx nimmt Request-Bodys bis `storage.maxFileSizeMb` + 1 MiB an (Standard: `26m`). Das zusätzliche MiB deckt die Multipart-Hülle eines Uploads ab: Ein Anhang mit der vollen erlaubten Größe kommt beim Backend an, ein etwas größerer bekommt dort eine verständliche `413`-Antwort, und alles über der Grenze lehnt nginx selbst mit `413` ab. Ohne diese Einstellung lag die Grenze bei nginx' Standard von 1 MiB, und jeder größere Upload scheiterte schon am Proxy.

Das Chart setzt am Ingress `main` dieselbe Grenze als Annotation `nginx.ingress.kubernetes.io/proxy-body-size`, weil ingress-nginx sonst ebenfalls bei 1 MiB abschneidet. Beides folgt `storage.maxFileSizeMb`: Wenn du die Upload-Grenze anhebst, wachsen nginx und Ingress mit. Traefik und Contour/Envoy werten die Annotation nicht aus und setzen von sich aus keine Body-Grenze; dort greift die Grenze des Frontend-nginx, solange `/` und `/api` über das Frontend laufen. Nutzt du einen Ingress unter einem anderen Schlüssel als `main` oder einen eigenen `HTTPProxy`, setze die Grenze dort selbst auf denselben Wert.

Das Backend setzt dieselbe Grenze noch einmal selbst, bevor es einen Upload liest. Das greift, wenn ein Request am Frontend-nginx vorbeikommt — über `kubectl port-forward`, aus dem Cluster oder über einen Ingress ohne Body-Grenze. Ein Upload mit größerer `Content-Length` bekommt `413` (`REQUEST_BODY_TOO_LARGE`), ohne dass das Backend ein Byte liest; ein Upload ohne Längenangabe wird an der Grenze abgebrochen. Alle anderen Requests (JSON, Formulare) dürfen höchstens 1 MiB groß sein.

Uploads über 1 MiB legt das Backend während des Lesens in `/tmp` ab, im Chart ein Speicher-Volume mit 64 MiB. Damit gleichzeitige Uploads es nicht füllen, teilen sie sich ein Budget von 52 MiB (`UPLOAD_SPOOL_BUDGET_MB`). Es zählt die Bytes, die schon angekommen sind: Bei der Standardgrenze laufen zwei volle Uploads gleichzeitig, ein weiterer wartet bis zu 30 Sekunden (`UPLOAD_SPOOL_WAIT_SECONDS`) und bekommt danach `503` mit `Retry-After`. Hebst du `storage.maxFileSizeMb` über 51 an, setzt das Chart das Budget auf eine volle Upload-Größe, also läuft nur noch ein großer Upload zur Zeit. Die Größe von `/tmp` folgt nicht automatisch: Ab etwa 60 MiB Upload-Grenze musst du `persistence.backend-tmp.sizeLimit` selbst anheben.

### Valkey (Redis-kompatibler Cache) {#valkey}

Valkey ist zugleich Cache und Celery-Broker: In ihm warten die Aufgaben auf den Worker. Das Chart bringt dafür diese Standardwerte mit:

```yaml title="values.yaml (Standard)"
valkey:
  deploymentStrategy: Recreate
  dataStorage:
    enabled: true
    requestedSize: 1Gi
    keepPvc: true
  valkeyConfig: |
    maxmemory 256mb
    maxmemory-policy noeviction
    appendonly yes
    appendfsync everysec
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      memory: 640Mi    # mindestens das Doppelte von maxmemory
```

- **Eigenes Volume:** Valkey legt seine Daten auf ein `PersistentVolumeClaim` (`kamerplanter-valkey`, 1 GiB, `ReadWriteOnce`). Es bleibt bei `helm uninstall` erhalten. Die Größe heißt im Valkey-Chart `requestedSize` — einen Schlüssel `size` liest es nicht.
- **`Recreate`:** Der alte Valkey-Pod endet, bevor der neue startet. Ein `ReadWriteOnce`-Volume hängt an einem Node; ein neuer Pod daneben käme auf einem anderen Node nicht an das Volume.
- **`noeviction` statt einer Verdrängungsstrategie:** Ist der Speicher voll, lehnt Valkey neue Schreibzugriffe ab, statt still wartende Aufgaben zu löschen. Ein voller Speicher fällt so als Fehler auf.
- **`appendonly yes`** schreibt jede Änderung mit (einmal pro Sekunde auf die Platte); nach einem Neustart sind auch die Aufgaben der letzten Sekunden wieder da.
- **Speicherlimit mindestens doppelt so groß wie `maxmemory`** (Standard 640 MiB bei 256 MB): Für das Umschreiben des Append-Only-Logs und für Snapshots startet Valkey einen Kindprozess, der den Datenbestand kopiert; jede Seite, die sich währenddessen ändert, belegt den Speicher doppelt. Dazu kommen der Puffer für das Umschreiben und die Puffer der Verbindungen, die nicht unter `maxmemory` zählen. Liegt das Limit zu knapp, beendet Kubernetes Valkey, bevor Valkey selbst ablehnen kann. Hebst du `maxmemory` an, hebe `resources.limits.memory` mit an — die Render-Prüfung des Charts verlangt mindestens das Doppelte.
- **Überwache den Speicher:** Mit `noeviction` meldet ein voller Valkey Fehler (`OOM command not allowed`), statt Aufgaben zu verlieren — Backend und Worker können dann keine Aufgaben mehr einreihen. Richte einen Alarm auf `used_memory` im Verhältnis zu `maxmemory` ein (zum Beispiel ab 80 %), damit du vorher eingreifst.

!!! info "Beim Upgrade"
    Bis zu dieser Version lag `/data` von Valkey auf einem flüchtigen `emptyDir`: Das Chart setzte `valkey.dataStorage.size`, einen Schlüssel, den das Valkey-Chart nicht kennt, und legte deshalb kein Volume an. Jeder Neustart von Valkey verlor die wartenden Aufgaben. Das Upgrade legt das Volume neu an und startet Valkey einmal neu (`Recreate`).

    - **Einmaliger Verlust wartender Aufgaben:** Was beim Neustart in der Warteschlange steht, geht verloren. Lass die Warteschlange vorher leerlaufen — etwa Celery Beat auf 0 skalieren (`kubectl scale deployment kamerplanter-celery-beat --replicas=0`), warten, bis der Worker alles abgearbeitet hat, dann upgraden; Beat startet mit dem Upgrade wieder. Geplante Aufgaben stellt Beat ohnehin beim nächsten Termin wieder ein.
    - **StorageClass ist Voraussetzung:** Das Volume nennt keine StorageClass. Hat dein Cluster keine Standard-StorageClass, bleibt das Volume und damit Valkey `Pending` — ohne Broker reiht keine Komponente mehr Aufgaben ein. Prüfe das mit `kubectl get storageclass` (Markierung `(default)`), oder nenne eine StorageClass ausdrücklich in `valkey.dataStorage.className`.
    - **Neuinstallation:** Das Volume bleibt bei `helm uninstall` erhalten. Valkey spielt beim Start sein Append-Only-Log ab — auch die Aufgaben einer alten Installation. Lösche das PVC `kamerplanter-valkey` vor einer Neuinstallation, wenn diese nicht weiterlaufen sollen.

!!! warning "Valkey ohne Passwort und ohne TLS"
    Backend, Worker und Beat verbinden sich über `REDIS_URL` (`redis://kamerplanter-valkey:6379/0`) ohne Passwort und ohne Verschlüsselung; der Valkey-Chart läuft mit seinem Standard ohne Anmeldung (`auth.enabled: false`) und ohne TLS. Geschützt ist Valkey nur durch die NetworkPolicies des Charts: Nur Backend, Worker und Beat dürfen den Valkey-Pod erreichen. Schalte die NetworkPolicies deshalb nicht ab, und betreibe Kamerplanter nur in einem Cluster, dessen CNI NetworkPolicies durchsetzt.

---

## Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|----------|:-------:|----------|-------------|
| `ARANGODB_HOST` | Ja | — | Hostname des ArangoDB-Service |
| `ARANGODB_PORT` | Ja | `8529` | Port des ArangoDB-Service |
| `ARANGODB_DATABASE` | Ja | `kamerplanter` | Datenbankname |
| `ARANGODB_USERNAME` | Ja | `kamerplanter` | Datenbank-Benutzer — im Chart das Anwendungskonto aus `database.arangodb.appUsername`, das der Container `app-user` im ArangoDB-Pod anlegt (Lese-/Schreibrecht nur auf der Anwendungsdatenbank). `root` stellt das alte Verhalten her. |
| `ARANGODB_PASSWORD` | Ja | — | Datenbank-Passwort. Kommt im Chart aus dem Secret `kamerplanter-secrets` (`envFrom`), **nicht** aus `env:`. |
| `ARANGO_ROOT_PASSWORD` | Ja | — | ArangoDB-Root-Passwort. Liest nur der ArangoDB-Pod (Secret aus `database.arangodb.rootPasswordSecret`, Standard `kamerplanter-secrets`). Ein eigener Wert, getrennt von `ARANGODB_PASSWORD`, wird empfohlen. |
| `JWT_SECRET_KEY` | Ja | — | JWT-Signierschlüssel, aus `kamerplanter-secrets`. Boot-Blocker bei `DEBUG=false`, wenn der Chart-interne Default unverändert bleibt. |
| `FERNET_KEY` | Ja | — | Verschlüsselungsschlüssel für OIDC-Provider-Secrets, aus `kamerplanter-secrets`. Boot-Blocker bei `DEBUG=false`, wenn leer oder ungültig — **auch für den Celery-Worker-Controller**, der denselben Wert wie das Backend per `envFrom` aus `kamerplanter-secrets` bezieht; Backend und Celery-Worker müssen denselben Schlüssel verwenden. |
| `ERASURE_TOMBSTONE_SALT` | Ja | — | DSGVO-Pseudonymisierungs-Salt (≥ 32 Zeichen) für Tombstone-Hash, Löschantrags-Schlüssel und Mandanten-Slug-Digest, aus `kamerplanter-secrets`. Boot-Blocker bei `DEBUG=false`, wenn leer oder zu kurz. Darf nach der ersten Kontolöschung nie mehr geändert werden. |
| `LOG_PSEUDONYM_SALT` | Ja | — | Salt (≥ 32 Zeichen) ausschließlich für die Log-Pseudonyme (`subject=`-Referenzen, `email_sha256`-Digests, `requested_by_subject`), aus `kamerplanter-secrets`. Boot-Blocker bei `DEBUG=false`, wenn leer oder zu kurz — **auch für den Celery-Worker-Controller**, der denselben Wert per `envFrom` bezieht. Darf im Gegensatz zu `ERASURE_TOMBSTONE_SALT` rotiert werden. |
| `INTERNAL_SERVICE_TOKEN` | Bedingt | — | Nur Pflicht, sobald `KNOWLEDGE_SERVICE_ENABLED=true` oder `INFERENCE_SERVICE_ENABLED=true` gesetzt ist, ebenfalls aus `kamerplanter-secrets`. Bei `INFERENCE_SERVICE_ENABLED` gilt dieselbe Pflicht **auch für den Celery-Worker-Controller** — er führt die planmäßige DSGVO-Löschung beigetragener Referenzbilder aus und braucht denselben Zugang wie das Backend, das sie schreibt (siehe [Bilderkennung in Betrieb nehmen](inference-service.md)). |
| `REDIS_URL` | Ja | — | Valkey/Redis-Verbindungs-URL |
| `CORS_ORIGINS` | Ja | — | Erlaubte Origins als JSON-Array |
| `DEBUG` | Nein | `false` | Debug-Modus aktivieren. Deaktiviert bei `true` zusätzlich den Boot-Blocker der sechs Zeilen oben — **niemals** in Produktion setzen. |
| `KAMERPLANTER_MODE` | Nein | `full` | `light` (ohne Auth, ein Nutzer) oder `full` (mit JWT-Auth und Mandantenverwaltung). Der Chart setzt diese Variable am Backend-Controller standardmäßig **nicht** — es gilt der Python-seitige Default `full`. Am Frontend-InitContainer ist sie fest auf `full` gesetzt und muss für den Light-Modus explizit überschrieben werden. |
| `REQUIRE_EMAIL_VERIFICATION` | Nein | `true` | E-Mail-Verifikation bei Registrierung. Ohne ausgehenden Mailversand (`EMAIL_ADAPTER` ist `console`) setzt du `false` ausdrücklich — sonst kann sich ein selbst registriertes Konto nicht anmelden, weil die Bestätigungsmail nie ankommt. |

Vollständige Liste aller Pflicht-Secrets je aktivierter Funktion: [Konfigurationsmatrix — Pflicht-Secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

---

## Entwicklungs-Overrides (values-dev.yaml)

Für die lokale Entwicklung existiert eine separate Values-Datei, die Skaffold automatisch verwendet:

<!-- Quelle: helm/kamerplanter/values.yaml, helm/kamerplanter/values-dev.yaml -->

| Einstellung | Produktion (`values.yaml`) | Entwicklung (`values-dev.yaml`) |
|------------|-----------|-------------|
| Replicas (Backend/Frontend) | 1 (Chart-Default — für Produktion i. d. R. manuell auf 2 erhöht, siehe [Kubernetes-Deployment](kubernetes.md)) | 1 |
| Update-Strategie | RollingUpdate | Recreate |
| DEBUG | false | true |
| Resource Limits | Streng | Großzügig |
| Frontend-Port | 80 (nginx) | 5173 (Vite Dev Server) |
| ArangoDB PVC | 5 Gi (Chart-Default) | 2 Gi |
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

Ein veröffentlichtes Chart bringt bereits gepinnte Digests mit (der Release-Job setzt sie beim Packen) — du überschreibst sie nur, wenn du eine andere Version willst als die, die das Chart mitliefert. Dann aber vollständig, also mit Digest:

```yaml
controllers:
  backend:
    containers:
      main:
        image:
          tag: "1.2.3@sha256:c6689b…"    # (1)!
  frontend:
    containers:
      main:
        image:
          tag: "1.2.3@sha256:6727d2…"
```

1. Digest ermitteln:
   `docker buildx imagetools inspect ghcr.io/nolte/kamerplanter-backend:1.2.3`

!!! danger "Ein Override ohne Digest macht das Pinning des Charts rückgängig"
    Der Override gewinnt gegen den Chart-Default. `tag: "1.2.3"` — ohne den Teil
    hinter dem `@` — ersetzt eine unveränderliche Referenz durch einen Namen, der
    neu gepusht werden kann. Zusammen mit `pullPolicy: IfNotPresent` liefert ein
    Node dann unter Umständen weiter alte Bytes aus, ohne dass es irgendwo
    auffällt. Genau daran hing der `inference-service`-Vorfall.

!!! tip "Und `latest` gar nicht"
    `latest` bewegt sich bei jedem Push auf `develop`. Eine Referenz, die sich
    bewegt, kann nicht zurückgerollt werden: „das vorherige Image" löst sich auf
    das aktuelle auf. Siehe [Deployment und Rollback](ci-cd.md#deployment-und-rollback).

---

## Storage-Konfiguration (NFR-013) {#storage-konfiguration-nfr-013}

Kamerplanter speichert alle Binärdaten (Fotos, Importe, Exporte) über einen austauschbaren Storage-Adapter. Die Wahl des Backends und die zugehörige Kubernetes-Persistenz steuerst du über den Block `storage` in deinen Values: Das Chart leitet daraus die `STORAGE_*`-Variablen von Backend und Celery-Worker, das PVC und dessen Mounts ab.

!!! warning "Ältere Chart-Stände lasen den Block `storage` nicht"
    Ältere Chart-Stände lasen den Block `storage` nicht: `storage.backend: s3` lieferte trotzdem `local-fs` mit PVC aus. Wer S3 bisher über eigene `env`-Einträge (`STORAGE_BACKEND`, `STORAGE_S3_*`) und ein zusätzliches `envFrom` eingerichtet hat, behält diese Einträge — sie überschreiben die Werte aus `storage`. Stelle beim nächsten Upgrade auf `storage.backend: s3` um, sonst legt das Chart weiterhin das (dann unbenutzte) PVC an.

!!! danger "Geteilter Betrieb: S3 ist Pflicht"
    Das PVC `backend-attachments` wird von Backend **und** Celery-Worker gemountet. Ein `ReadWriteOnce`-Volume hängt an genau einem Node: Landet ein zweiter Pod auf einem anderen Node, bleibt er mit `Multi-Attach error` in `ContainerCreating` hängen. Für mehr als eine Backend- oder Worker-Replica — und für jeden Betrieb mit mehreren Mandanten auf einem Cluster mit mehreren Nodes — nutze `storage.backend: s3`. Das Chart verweigert das Rendern, wenn `controllers.backend.replicas` oder `controllers.celery-worker.replicas` größer als 1 ist und die Anhänge auf einem `ReadWriteOnce`-Volume liegen. Ausweg ohne S3: `ReadWriteMany` mit einer RWX-fähigen StorageClass, oder — nur auf einem Cluster mit genau einem Node — `storage.localFs.singleNode: true`.

    Auch mit einer einzigen Replica gilt auf einem Cluster mit mehreren Nodes: Backend und Worker müssen auf demselben Node laufen, und ein Rolling Update (`maxSurge: 1`) startet den neuen Pod nur, wenn er auf demselben Node landet. Das Chart sorgt dafür (Issue #2153): Backend- und Worker-Pods tragen das Label `kamerplanter.io/attachments-volume` und verlangen per `podAffinity` einen Pod mit diesem Label auf demselben Node (`topologyKey: kubernetes.io/hostname`). Ein neuer Pod landet so auf dem Node, an dem das Volume hängt, und das Rolling Update bleibt unterbrechungsfrei — kein `Recreate` nötig. Passt der neue Pod dort nicht mehr hin (CPU, Speicher), bleibt er `Pending` mit `FailedScheduling` statt mit `Multi-Attach error`; der alte Pod läuft weiter. Mit `storage.backend: s3` oder `ReadWriteMany` rendert die Bedingung auf `kubernetes.io/os` — ein Label mit demselben Wert auf jedem Node, also keine Einschränkung.
    <!-- #2124 -->

### Local Filesystem (Standard)

Im Default-Betrieb legt das Chart automatisch das PVC `backend-attachments` an und mountet es in den Backend- und Celery-Worker-Pods unter `/data/attachments`. Das PVC trägt `helm.sh/resource-policy: keep` und die ArgoCD-Sync-Option `Prune=false,Delete=false`: Weder `helm uninstall` noch ein ArgoCD-Prune (etwa nach dem Umstellen auf S3) noch das Löschen der ArgoCD-Application löschen die Anhänge.

```yaml
storage:
  backend: local-fs                  # Standard; kein externes Storage nötig
  maxFileSizeMb: 25
  presignTtlSeconds: 900
  virusScan:
    enabled: false
    endpoint: ""

  localFs:
    root: /data/attachments           # Container-interner Mount-Pfad
    pvc:
      size: 20Gi                      # Chart-Default; nach Bedarf erhöhen
      accessMode: ReadWriteOnce       # Für Single-Replica (Standard)
      storageClass: ""                # Leer = Cluster-Default
    singleNode: false                 # true nur auf einem Cluster mit genau einem Node
```

**Multi-Replica-Betrieb** (Backend- oder Worker-Replicas > 1) ohne S3:

```yaml
storage:
  localFs:
    pvc:
      accessMode: ReadWriteMany       # RWX-fähige StorageClass erforderlich
      storageClass: longhorn          # Oder: nfs, cephfs, etc.
```

!!! warning "Signing-Secret bei RWX zwingend"
    Bei mehr als einer Backend-Replica muss `STORAGE_LOCALFS_SIGNING_SECRET` als stabiles Kubernetes-Secret gesetzt sein. Ohne dieses Secret generiert jeder Pod ein eigenes ephemeres Signing-Secret — Token-Downloads schlagen fehl, wenn die Validierungsanfrage einen anderen Pod erreicht als die Signierung.

    ```bash
    kubectl create secret generic kamerplanter-storage-signing \
      --from-literal=STORAGE_LOCALFS_SIGNING_SECRET="$(openssl rand -hex 32)" \
      --namespace kamerplanter
    ```

    Im Chart über `envFrom` referenzieren:

    ```yaml
    controllers:
      backend:
        containers:
          main:
            envFrom:
              - secretRef:
                  name: kamerplanter-storage-signing
    ```

### S3-kompatibel (Production)

Nicht-geheime S3-Parameter werden direkt in `values.yaml` gesetzt. Die Credentials kommen ausschließlich aus einem Secret — idealerweise vom External Secrets Operator (ESO) erzeugt, nie als Klartext in Git. Das Chart liest daraus genau die zwei in `credentialsRef` genannten Schlüssel (`secretKeyRef`), nicht das ganze Secret. Mit `storage.backend: s3` rendert das Chart kein PVC und keinen Mount.

!!! warning "Bestehende Anhänge zuerst migrieren"
    Beim Umstellen von `local-fs` auf `s3` liegen die bisherigen Dateien noch im PVC. Kopiere sie vor dem Umschalten mit dem Migrationswerkzeug im Backend-Pod (`python -m scripts.storage.migrate --from local-fs --to s3 --checksum-verify`, siehe [Speicher konfigurieren](../user-guide/object-storage.md#migration-zwischen-backends)). Erst danach `storage.backend: s3` setzen; das alte PVC bleibt stehen (siehe oben) und du löschst es von Hand, wenn der Prüfsummen-Vergleich grün ist.

```yaml
storage:
  backend: s3
  maxFileSizeMb: 25
  presignTtlSeconds: 900

  s3:
    endpointUrl: https://s3.eu-central-1.amazonaws.com
    region: eu-central-1
    bucket: kamerplanter-prod
    usePathStyle: false               # true für MinIO und Nicht-AWS-Anbieter
    forceTls: true
    kmsKeyId: ""                      # Optional: Customer-Managed Key (SSE-KMS)

    # S3-Credentials via External Secrets Operator (NIEMALS Klartext)
    credentialsRef:
      secretName: storage-s3-credentials
      accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
      secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
```

**External Secrets Operator — ESO-Secret:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: storage-s3-credentials
  namespace: kamerplanter
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend              # Oder AWS Secrets Manager, etc.
    kind: ClusterSecretStore
  target:
    name: storage-s3-credentials
    creationPolicy: Owner
  data:
    - secretKey: STORAGE_S3_ACCESS_KEY_ID
      remoteRef:
        key: kamerplanter/storage
        property: access_key_id
    - secretKey: STORAGE_S3_SECRET_ACCESS_KEY
      remoteRef:
        key: kamerplanter/storage
        property: secret_access_key
```

!!! tip "Ohne ESO: manuelles Kubernetes-Secret"
    Wenn kein External Secrets Operator verfügbar ist, lege das Secret manuell an:
    ```bash
    kubectl create secret generic storage-s3-credentials \
      --from-literal=STORAGE_S3_ACCESS_KEY_ID="dein-access-key" \
      --from-literal=STORAGE_S3_SECRET_ACCESS_KEY="dein-secret-key" \
      --namespace kamerplanter
    ```
    Das Secret sollte aus einem sicheren Vault kommen und **niemals** in Git gespeichert werden.

    Fehlt das Secret bei `storage.backend: s3`, starten die Pods trotzdem (die Referenzen sind `optional`, damit ein `local-fs`-Release ohne dieses Secret auskommt), aber der Storage-Health-Check schlägt fehl und der Pod wird nicht `Ready` — der Rollout bleibt stehen, die alten Pods bedienen weiter.

#### NetworkPolicy für S3-Endpoints

Eine eigene Storage-NetworkPolicy gibt es nicht. Backend und Celery-Worker erreichen einen öffentlichen S3-Endpunkt über ihre allgemeine Egress-Regel (`networkpolicies.backend` und `networkpolicies.celery-worker`: Ports 80/443 nach `0.0.0.0/0` ohne RFC1918-Netze und ohne `169.254.0.0/16` — die Cloud-Metadata-Adresse bleibt gesperrt). Ein Endpunkt im Cluster oder im privaten Netz (MinIO, Ceph RGW) ist damit **nicht** erreichbar: Ergänze in deinen Values eine Egress-Regel für genau diesen Endpunkt in beiden Policies.

#### MinIO im Cluster

```yaml
storage:
  backend: s3
  s3:
    endpointUrl: http://minio.kamerplanter.svc:9000
    region: us-east-1
    bucket: kamerplanter
    usePathStyle: true
    forceTls: false
    allowPrivateEndpoint: true       # Erlaubt nicht öffentlich erreichbaren Endpunkt
    credentialsRef:
      secretName: storage-s3-credentials
      accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
      secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
```

### Egress für Benachrichtigungskanäle (Apprise)

Kamerplanter prüft Apprise-Ziele beim Speichern und beim Senden (Schema-Positivliste, Literal-Hosts, aufgelöste Adressen von Gotify-, Matrix- und ntfy-Servern). Zwei Dinge liegen **außerhalb des Prozesses** und sind Sache der Netzwerk-Policy des Betreibers:

- Apprise folgt HTTP-Redirects und führt bei Matrix die `.well-known`-Erkennung selbst aus; beides lässt sich im Backend nicht kontrollieren.
- Zwischen der DNS-Prüfung und dem Verbindungsaufbau bleibt ein kleines Zeitfenster (DNS-Rebinding).

Die DNS-Auflösung dieser Prüfung ist begrenzt, damit ein Nutzer mit nie antwortenden Hostnamen andere nicht ausbremst: Speichern und Senden haben je einen eigenen Pool mit 8 Threads, ein Nutzer belegt darin höchstens 3 gleichzeitig, und eine Antwort muss innerhalb von 3 s kommen. Was darüber hinausgeht, wird sofort abgelehnt (fail closed), nicht eingereiht. Beim Speichern werden Antworten pro Hostname kurz zwischengespeichert (60 s, ein Fehlschlag 10 s); beim Senden löst Kamerplanter jedes Mal frisch auf und übernimmt aus dem Zwischenspeicher nur eine Sperre. Die Werte sind fest eingebaut; es gibt dafür keine Einstellung.

Ziele in privaten Netzen (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `100.64.0.0/10` und `fc00::/7`) lehnt Kamerplanter im `full`-Modus standardmäßig ab, beim Speichern und beim Senden. Im Cluster sind das keine Heimnetz-Geräte, sondern der API-Server, ArangoDB und Valkey auf Pod-IPs. Mit `APPRISE_ALLOW_PRIVATE_TARGETS=true` gibst du sie frei; im `light`-Modus sind sie ohne Einstellung erlaubt, mit `false` sperrst du sie auch dort. Loopback, Link-Local und Cloud-Metadaten bleiben immer gesperrt.

Das Chart schränkt den Egress von `backend` und `celery-worker` deshalb bereits ein (`networkpolicies.backend` und `networkpolicies.celery-worker` in `values.yaml`): Ziel `0.0.0.0/0` ohne `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` und `169.254.0.0/16`, nur auf den Ports 80, 443, 465 und 587. Das schließt Cloud-Metadaten und Cluster-interne Ziele aus, auch wenn eine Weiterleitung dorthin führt. `100.64.0.0/10` steht nicht in dieser Ausnahmeliste; liegen Pods deines Clusters dort, schützt nur die Prüfung im Backend.

!!! warning "LAN-Gotify oder -ntfy braucht zwei Freigaben"
    Ein Gotify oder ntfy im Heimnetz (`192.168.x.x`) lehnt Kamerplanter im `full`-Modus ab, und der Standard-Egress des Charts blockiert es zusätzlich. Setze `APPRISE_ALLOW_PRIVATE_TARGETS=true` in der Umgebung von `backend` und `celery-worker` und ergänze in deinem `valuesObject` eine Egress-Regel für genau diese Adresse und diesen Port in `networkpolicies.backend.rules.egress` und `networkpolicies.celery-worker.rules.egress`. Die Freigabe gilt für alle Nutzer und alle privaten Adressen, also auch für Pod-IPs im Cluster; die Egress-Regel ist dann die eigentliche Schranke. Ohne Cluster-NetworkPolicy (Docker Compose) gilt keine Egress-Schranke; dann bleibt nur die Prüfung im Backend.

### Ausgehende Verbindungen zu Home Assistant und InvenTree

Kamerplanter prüft die URL von Home Assistant und InvenTree nicht nur beim Speichern: Jede Verbindung prüft die Adressen, zu denen sie aufgebaut wird, und verbindet sich nur mit einer davon. Eine DNS-Antwort, die sich zwischen Prüfung und Verbindung ändert (DNS-Rebinding), führt deshalb nicht an eine interne Adresse. Cloud-Metadaten und Link-Local bleiben immer gesperrt, private Adressen nur mit `HA_ALLOW_PRIVATE_ENDPOINT` bzw. `INVENTREE_ALLOW_PRIVATE_ENDPOINT`. Weiterleitungen folgt keine dieser Verbindungen, Web-Push ebenfalls nicht.

!!! warning "Web-Push ist nicht angeheftet"
    Den Push-Endpunkt prüft Kamerplanter beim Speichern und vor jedem Senden, beim Verbinden wird der Name aber erneut aufgelöst. Ein Name, der dann auf eine interne Adresse zeigt, scheitert am TLS-Zertifikat, bevor ein HTTP-Request gesendet wird; die TCP-Verbindung dorthin wird aber geöffnet. Die Egress-Regel des Charts (ohne `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`) ist hier die eigentliche Schranke.

!!! note "Kein HTTP-Proxy für diese Verbindungen"
    Für Home Assistant und InvenTree gelten `HTTP_PROXY` und `HTTPS_PROXY` nicht: Ein Proxy würde den Namen selbst auflösen, und genau das soll die Verbindung nicht aus der Hand geben. Braucht dein Cluster für ausgehenden Verkehr einen Proxy, gib Home Assistant und InvenTree über eine Egress-Regel direkt frei.

### Virenscan (optional)

```yaml
storage:
  virusScan:
    enabled: true
    endpoint: http://clamav-rest.kamerplanter.svc:9000
```

ClamAV muss als separates Deployment im Cluster laufen. Das Backend blockiert einen Upload, wenn der Scanner einen Fund meldet.

### Häufige Provider-Konfigurationen

=== "Hetzner Object Storage"

    ```yaml
    storage:
      backend: s3
      s3:
        endpointUrl: https://fsn1.your-objectstorage.com
        region: eu-central
        bucket: mein-kamerplanter-bucket
        usePathStyle: false
        forceTls: true
        credentialsRef:
          secretName: storage-s3-credentials
          accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
          secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
    ```

=== "Cloudflare R2"

    ```yaml
    storage:
      backend: s3
      s3:
        endpointUrl: https://<account-id>.r2.cloudflarestorage.com
        region: auto
        bucket: kamerplanter
        usePathStyle: false
        forceTls: true
        credentialsRef:
          secretName: storage-s3-credentials
          accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
          secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
    ```

=== "Backblaze B2 (S3-API)"

    ```yaml
    storage:
      backend: s3
      s3:
        endpointUrl: https://s3.eu-central-003.backblazeb2.com
        region: eu-central-003
        bucket: kamerplanter
        usePathStyle: false
        forceTls: true
        credentialsRef:
          secretName: storage-s3-credentials
          accessKeyIdKey: STORAGE_S3_ACCESS_KEY_ID
          secretAccessKeyKey: STORAGE_S3_SECRET_ACCESS_KEY
    ```

---

## Metriken (Prometheus) {#metriken-prometheus}

Ein Schalter: `monitoring.enabled: true`. Damit setzt das Chart `METRICS_PORT=9464` am Backend, ergänzt den Service-Port `metrics`, legt einen `ServiceMonitor` an und die NetworkPolicy `backend-metrics`, die genau die Prometheus-Pods auf diesen Port lässt.

```yaml
monitoring:
  enabled: true
  scrapeInterval: 30s
  prometheus:
    namespace: monitoring          # Namespace, in dem Prometheus läuft
    podName: prometheus            # Wert des Labels app.kubernetes.io/name der Prometheus-Pods
    serviceMonitorLabels:
      release: kube-prometheus-stack   # was der serviceMonitorSelector des Operators erwartet
```

!!! warning "Prometheus Operator erforderlich"
    Der `ServiceMonitor` ist eine Ressource des Prometheus Operators (`monitoring.coreos.com/v1`). Fehlt dessen CRD im Cluster, schlägt die Installation mit eingeschaltetem `monitoring` fehl. Deshalb ist der Standard `false`.

Die Metriken sind **nicht öffentlich**: Sie laufen auf einem eigenen Port, nie als Route der API. Der Ingress führt `/` und `/api` zum Frontend-nginx, und der leitet nur an Port 8000 weiter. Die Backend-Policy lässt weiter nur das Frontend auf 8000 zu, sodass Prometheus über den Scrape-Weg nicht an nginx vorbei auf die API kommt.

Ausgeliefert werden `http_request_duration_seconds` (Histogramm) und `http_requests_total` mit den Labels `method`, `handler` (Routenmuster, nie der Pfad; `unmatched` für eine Anfrage ohne Route) und `status`, `http_requests_in_progress` sowie Prozess-Metriken (Speicher, CPU, Dateideskriptoren). Ein Mandant ist bewusst **kein** Label — das vervielfacht jede Zeitreihe mit der Mandantenzahl und legt die Mandantenliste jedem offen, der scrapen darf. Für die Sicht pro Mandant tragen die Logzeilen `tenant=ten_…`.

Dazu kommen die Längen der Celery-Warteschlangen: `celery_queue_length` mit dem Label `queue` (`critical`, `celery`, `bulk`) zählt die Aufgaben, die im Valkey auf einen Worker warten, und `celery_broker_up` ist `1`, wenn der letzte Lesezugriff auf Valkey geklappt hat. Das Backend liest die Längen beim Scrapen, nicht bei einer Anfrage, und höchstens alle 5 Sekunden. Ist Valkey nicht erreichbar, fehlen die Warteschlangen-Werte in diesem Scrape (kein alter Wert) und `celery_broker_up` steht auf `0`; der Scrape selbst schlägt nicht fehl. Jedes Backend-Replikat liefert dieselben Zahlen — fasse sie mit `max`, nicht mit `sum` zusammen.

Noch nicht enthalten: Metriken aus dem Celery-Worker selbst (Laufzeiten, Fehler je Aufgabe), Recording- und Alert-Regeln (`PrometheusRule`) aus NFR-007.

## Skalierung (HPA und PDB) {#skalierung}

Ohne weitere Einstellungen läuft jede Komponente mit einem Pod. Autoscaler (`HorizontalPodAutoscaler`) und Disruption-Budget (`PodDisruptionBudget`) schaltest du pro Controller dazu; das Chart rendert sie nur, wenn du sie setzt.

```yaml title="values-production.yaml (Ausschnitt)"
storage:
  backend: s3                      # Voraussetzung für mehr als einen Backend-Pod
  # ...

controllers:
  backend:
    horizontalPodAutoscaler:
      minReplicas: 2               # ersetzt replicas
      maxReplicas: 6
      metrics:
        - type: Resource
          resource:
            name: cpu
            target:
              type: Utilization
              averageUtilization: 70
    podDisruptionBudget:
      minAvailable: 1
  frontend:
    replicas: 2
    podDisruptionBudget:
      minAvailable: 1
```

- **Autoscaler:** Mit `horizontalPodAutoscaler` entfällt `replicas` aus dem Deployment; `minReplicas` übernimmt seine Rolle. So setzt ein `helm upgrade` oder ein ArgoCD-Sync die Pod-Zahl nicht auf den festen Wert zurück. Der Autoscaler braucht den metrics-server im Cluster.
- **Ein neuer Backend-Pod hilft erst nach seinem Start** — bis zu einigen Minuten, siehe [Startdauer des Backends](kubernetes.md#startdauer-des-backends). Kurze Lastspitzen fängt der Autoscaler deshalb nicht ab.
- **Celery-Worker:** CPU ist für den Worker das falsche Signal — er wartet meist auf externe Dienste. Skaliere ihn nach der Länge seiner Warteschlange, siehe [Worker-Autoscaling nach Queue-Länge](#worker-autoscaling-nach-queue-laenge).

Das Chart verweigert die Darstellung (`helm template`, `helm upgrade`, ArgoCD) mit einer Meldung, wenn eine Einstellung im Cluster still schiefgehen würde:

| Einstellung | Warum abgelehnt |
|-------------|-----------------|
| Backend oder Celery-Worker mit mehr als einem Pod (`replicas` oder `maxReplicas`) auf dem Standard-Volume `ReadWriteOnce` | Ein zweiter Pod auf einem anderen Node startet nie (`Multi-Attach error`). Lösung: [S3](#storage-konfiguration-nfr-013) oder `ReadWriteMany`. |
| Mehr als ein Pod oder ein Autoscaler für `celery-beat`, `arangodb`, `vectordb` oder `timescaledb` | Zwei Beat-Pods führen jede geplante Aufgabe doppelt aus, auch Lösch- und Aufbewahrungsläufe. Zwei ArangoDB-, VectorDB- oder TimescaleDB-Pods sind zwei getrennte Datenbanken, kein Cluster. |
| `podDisruptionBudget.minAvailable` gleich oder größer als die Pod-Zahl, auch als Prozentwert (`"100%"`; Kubernetes rundet auf ganze Pods auf, `"50%"` von einem Pod ist dieser Pod), oder `maxUnavailable: 0` bzw. `"0%"` | Kubernetes darf dann keinen Pod verdrängen; jedes Leeren eines Nodes und jedes Cluster-Upgrade bleibt hängen. Prozentwerte, die mindestens einen Pod verdrängbar lassen (`minAvailable: "50%"` bei zwei Pods, `maxUnavailable: "25%"`), sind erlaubt. |
| `minReplicas` gleich oder größer als `maxReplicas` bei einem Autoscaler | Der Autoscaler kann die Pod-Zahl nie ändern. Für eine feste Zahl setzt du `replicas`. |
| Eine Metrik `type: External` ohne `external.metric.name` oder ohne Ziel (`target.type: Value` mit `value` bzw. `AverageValue` mit `averageValue`) | Der Autoscaler liest nichts und skaliert nie. |

Der Celery-Beat bleibt immer ein einzelner Pod mit der Strategie `Recreate`: Der alte Pod endet, bevor der neue startet.

### Worker-Autoscaling nach Queue-Länge {#worker-autoscaling-nach-queue-laenge}

Die Celery-Worker kann das Chart nach der Zahl der wartenden Aufgaben skalieren. Dafür braucht es drei Dinge, von denen das Chart zwei mitbringt:

1. **Die Metrik** `celery_queue_length{queue}` vom Backend — eingeschaltet mit `monitoring.enabled: true` (siehe [Metriken](#metriken-prometheus)).
2. **Den [Prometheus Adapter](https://github.com/kubernetes-sigs/prometheus-adapter)** im Cluster, der diese Reihe als *External Metric* (`external.metrics.k8s.io`) bereitstellt. Den installierst und konfigurierst du selbst; das Chart installiert ihn **nicht**.
3. **Die Autoscaler** der Worker — eingeschaltet mit `celeryWorkers.queueAutoscaling.enabled: true`.

```yaml title="values-production.yaml (Ausschnitt)"
storage:
  backend: s3                      # Voraussetzung für mehr als einen Worker-Pod
  # ...

monitoring:
  enabled: true                    # Pflicht: liefert celery_queue_length

celeryWorkers:
  dedicatedQueues: true            # optional: ein Worker je Queue, siehe oben
  queueAutoscaling:
    enabled: true
    metricName: celery_queue_length   # Name, unter dem der Adapter die Reihe anbietet
    workers:
      celery-worker:               # liest critical (bzw. alle drei ohne dedicatedQueues)
        minReplicas: 1
        maxReplicas: 3
        targetPerReplica: 20       # wartende Aufgaben pro Worker-Pod
      celery-worker-default:       # liest celery
        minReplicas: 1
        maxReplicas: 3
        targetPerReplica: 20
      celery-worker-bulk:          # liest bulk
        minReplicas: 1
        maxReplicas: 2
        targetPerReplica: 5
```

Jeder Worker bekommt einen `HorizontalPodAutoscaler` (`autoscaling/v2`) mit genau einer Metrik vom Typ `External`. Welche Warteschlangen sie auswählt, liest das Chart aus dem `-Q` des Workers: Ohne `dedicatedQueues` skaliert der eine Worker nach der Summe aller drei Warteschlangen, mit `dedicatedQueues` jeder Worker nach seiner eigenen. Das Ziel ist `AverageValue`: wartende Aufgaben geteilt durch die Pods des Workers. Ein Eintrag für `celery-worker-default` oder `celery-worker-bulk` wirkt nur mit `dedicatedQueues: true`; mit `enabled: false` in einem Eintrag nimmst du einen einzelnen Worker heraus.

**Regel für den Prometheus Adapter** (Values des Charts `prometheus-community/prometheus-adapter`):

```yaml
rules:
  external:
    - seriesQuery: 'celery_queue_length{namespace!="",queue!=""}'
      resources:
        overrides:
          namespace: {resource: namespace}
      name:
        matches: "^celery_queue_length$"
        as: "celery_queue_length"     # = celeryWorkers.queueAutoscaling.metricName
      # Jedes Backend-Replikat meldet dieselben Zahlen: max, nicht sum.
      metricsQuery: 'max by (queue) (<<.Series>>{<<.LabelMatchers>>})'
```

Ob der Adapter die Reihe liefert, prüfst du so (Namespace anpassen):

```bash
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/kamerplanter/celery_queue_length?labelSelector=queue%20in%20(critical)"
kubectl describe hpa kamerplanter-celery-worker
```

!!! warning "Ohne Adapter skaliert nichts"
    Fehlt der Adapter oder seine Regel, meldet der Autoscaler `FailedGetExternalMetric` und behält die aktuelle Pod-Zahl. Dasselbe gilt, solange Valkey nicht erreichbar ist: Die Warteschlangen-Werte fehlen dann, und der Autoscaler skaliert weder hoch noch herunter.

!!! warning "Herunterskalieren beendet laufende Aufgaben"
    Ein Worker-Pod, der beim Herunterskalieren stoppt, beendet seine laufenden Aufgaben innerhalb der Termination-Grace-Period des Pods (ohne Einstellung 30 Sekunden); danach wird er beendet. Eine Aufgabe, die schon beim Start bestätigt wurde, ist dann verloren; eine, die erst nach dem Lauf bestätigt wird, läuft nach dem Visibility-Timeout erneut. Deshalb skaliert das Chart standardmäßig langsam herunter (`behavior`: 10 Minuten Stabilisierung, höchstens ein Pod je 5 Minuten). Für `celery-worker-bulk` mit Läufen bis zu 3 Stunden setzt du `controllers.celery-worker-bulk.pod.terminationGracePeriodSeconds` hoch oder hältst `minReplicas` auf der Zahl, die er normalerweise braucht.

Das Chart verweigert die Darstellung, wenn `queueAutoscaling.enabled` ohne `monitoring.enabled` oder ohne `metricName` gesetzt ist, ein Eintrag kein `maxReplicas` oder kein `targetPerReplica` über 0 hat, `minReplicas` kleiner als 1 oder nicht kleiner als `maxReplicas` ist, ein Worker zusätzlich einen eigenen `controllers.<worker>.horizontalPodAutoscaler` trägt oder der Name kein Worker des Charts ist. Mehr als ein Worker-Pod auf dem Standard-Volume `ReadWriteOnce` wird wie bei jedem Autoscaler abgelehnt.

## Secrets aus einem Secret-Store {#secrets-aus-einem-secret-store}

Statt `kamerplanter-secrets` von Hand anzulegen, kann der [External Secrets Operator](https://external-secrets.io/) es aus deinem Secret-Store (Vault, AWS Secrets Manager, …) schreiben. Das Chart bringt dafür ein `ExternalSecret` mit, das standardmäßig aus ist:

```yaml title="values-production.yaml (Ausschnitt)"
externalSecrets:
  app:
    enabled: true
    secretStoreRef:
      kind: ClusterSecretStore     # oder SecretStore im selben Namespace
      name: mein-secret-store
    dataFrom:
      - extract:
          key: kamerplanter/app    # Eintrag im Store mit den Pflicht-Schlüsseln, ohne ARANGO_ROOT_PASSWORD
```

- Jeder Schlüssel des Store-Eintrags wird ein Eintrag in `kamerplanter-secrets`, und Backend, Worker und Beat lesen dieses Secret vollständig per `envFrom`. Lege deshalb nur die Pflicht-Schlüssel in den Eintrag ([Pflicht-Secrets](kubernetes.md#2-pflicht-secrets-anlegen)), **nicht** `ARANGO_ROOT_PASSWORD`: Das Root-Passwort gehört in ein eigenes Secret (eigener Store-Eintrag mit einem zweiten `ExternalSecret` oder von Hand angelegt), das du in `database.arangodb.rootPasswordSecret` einträgst.
- Ein `ClusterSecretStore` liefert ohne Einschränkung an jeden Namespace im Cluster. Beschränke ihn über `spec.conditions` (`namespaces` oder `namespaceSelector`) auf den Kamerplanter-Namespace, oder nutze einen `SecretStore` im selben Namespace (`secretStoreRef.kind: SecretStore`).
- Ohne `secretStoreRef.name` bricht die Darstellung mit einer Meldung ab.
- Der Operator und seine CRDs (`external-secrets.io/v1`) müssen im Cluster installiert sein.
- Fehlt der Eintrag später im Store, bleibt das letzte Secret erhalten (`deletionPolicy: Retain`) — Pods starten weiter.
- `Retain` gilt nur für einen gelöschten Store-Eintrag. Bei `helm uninstall` verschwindet das `ExternalSecret`, und weil es mit `creationPolicy: Owner` Eigentümer von `kamerplanter-secrets` ist, löscht die Garbage Collection von Kubernetes das Secret mit. Brauchst du die Werte danach noch, liegen sie im Store.

!!! warning "Umstieg von einem handgemachten Secret"
    Mit `creationPolicy: Owner` (Standard) übernimmt der Operator ein bereits vorhandenes, von Hand angelegtes `kamerplanter-secrets` nicht ohne Weiteres. Lösche das alte Secret im selben Schritt (laufende Pods behalten ihre Werte bis zum nächsten Neustart), oder setze `externalSecrets.app.target.creationPolicy: Merge` — dann schreibt der Operator die Schlüssel in das vorhandene Secret.

Weitere Secrets — die S3-Zugangsdaten (`storage.s3.credentialsRef`), das Backup (`backup.s3.credentialsRef`) und das Root-Passwort der Datenbank (`database.arangodb.rootPasswordSecret`) — legst du auf dieselbe Weise als weitere Einträge unter `externalSecrets` an.

## TimescaleDB (Sensordaten) {#timescaledb}

TimescaleDB speichert Sensor-Zeitreihen. Sie ist optional und standardmäßig aus; ohne sie arbeitet Kamerplanter ohne Messreihen-Speicher. Du schaltest sie mit einem einzigen Wert ein:

```yaml title="values-production.yaml (Ausschnitt)"
controllers:
  timescaledb:
    enabled: true
```

Damit rendert das Chart die Datenbank (StatefulSet, ein Pod, 10 GiB Volume), ihren Service und ihre NetworkPolicy, und Backend, Worker und Beat erhalten `TIMESCALEDB_ENABLED=true` samt Adresse. Nur Backend und Worker dürfen die Datenbank auf Port 5432 erreichen.

Vorher ergänzt du in `kamerplanter-secrets` den Schlüssel `TIMESCALEDB_PASSWORD`:

```bash
kubectl patch secret kamerplanter-secrets -n kamerplanter --type merge \
  -p "{\"stringData\":{\"TIMESCALEDB_PASSWORD\":\"$(openssl rand -hex 24)\"}}"
```

- Die Datenbank liest nur diesen einen Schlüssel aus dem Secret; Backend und Worker erhalten ihn wie alle anderen über `envFrom`.
- Fehlt der Schlüssel, startet der Datenbank-Pod nicht (`CreateContainerConfigError`). Das Backend verweigert den Start mit dem eingebauten Standardpasswort, sobald `DEBUG=false` gilt.
- Mit `externalSecrets.app` legst du den Schlüssel in denselben Store-Eintrag wie die übrigen Pflicht-Schlüssel.
- Die Datenbank läuft ohne Root-Rechte (Benutzer `postgres`, uid 70) mit schreibgeschütztem Dateisystem; beschreibbar sind nur das Daten-Volume, das Socket-Verzeichnis und `/tmp`.
- Mehr als ein Pod ist nicht möglich: Ein zweiter Pod wäre eine zweite, getrennte Datenbank. Das Chart verweigert `replicas` über 1 und einen Autoscaler.
- Das Volume bleibt bei `helm uninstall` erhalten. Eine Sicherung der Messreihen bringt das Chart nicht mit (siehe [Backup und Wiederherstellung](backup-restore.md)).

## Externe Datenbanken {#externe-datenbanken}

Statt der mitgelieferten ArangoDB und des Valkey-Subcharts kannst du Datenbanken außerhalb des Charts anbinden, etwa einen verwalteten Dienst oder eine Instanz in einem anderen Namespace. Beide Schalter sind standardmäßig aus; ohne sie rendert das Chart wie bisher.

### ArangoDB

`database.arangodb.external.enabled: true` ist der einzige Schalter. Das ArangoDB-StatefulSet, sein Service, seine NetworkPolicy und seine Volumes entfallen. Backend, Celery-Worker, Celery-Beat und das Backup verbinden sich mit `scheme://host:port`:

```yaml
database:
  arangodb:
    appUsername: kamerplanter
    external:
      enabled: true
      host: arango.example.net    # nur der Hostname, ohne Schema
      port: 8529
      scheme: https               # http | https
      cidr: 203.0.113.10/32       # Adressbereich der Datenbank (NetworkPolicy)
```

- Das Chart legt in einer externen Datenbank nichts an. Die Anwendungsdatenbank (`kamerplanter`) und das Konto aus `appUsername` mit Lese-/Schreibrecht darauf müssen existieren; `ARANGODB_PASSWORD` in `kamerplanter-secrets` ist sein Passwort.
- `scheme: https` setzt `ARANGODB_SCHEME=https`. Das Backend prüft das Serverzertifikat gegen die Zertifikate im Image. Für eine eigene Zertifizierungsstelle legst du deren Zertifikat in den Container und nennst den Pfad in `REQUESTS_CA_BUNDLE`. Das gilt nur für die Anwendung: `arangodump` im Backup-Job liest diese Variable nicht, mit eigener Zertifizierungsstelle deckt das Chart das Backup also nicht ab.
- Das Backup (`backup.enabled`) sichert dann die externe Datenbank und verbindet sich bei `https` per TLS.

### Valkey

`valkey.enabled: false` schaltet das Valkey-Subchart ab. Backend, Worker und Beat bekommen dann `database.valkey.external.url` als `REDIS_URL`:

```yaml
valkey:
  enabled: false
database:
  valkey:
    external:
      url: "rediss://:$(VALKEY_PASSWORD)@valkey.example.net:6380/0"
      cidr: 203.0.113.20/32
```

- Erlaubt sind `redis://` und `rediss://` (TLS).
- Ein Passwort gehört nie in die Values. Lege es als Schlüssel in `kamerplanter-secrets` ab (hier `VALKEY_PASSWORD`) und verweise mit `$(SCHLÜSSEL)` darauf; Kubernetes setzt den Wert beim Containerstart ein. Die Zeichen `/ # ? @` im Passwort musst du URL-kodieren, sonst verweigert das Backend den Start.

### NetworkPolicies

Mit der Default-Deny-Basis erreichen die Pods eine externe Datenbank nur über eine eigene Egress-Policy. Das Chart rendert sie mit dem jeweiligen Schalter:

| Policy | Pods | Ziel | Ports |
|---|---|---|---|
| `arangodb-external` | Backend, alle Celery-Worker, Backup | `database.arangodb.external.cidr` | 8529, 443 |
| `valkey-external` | Backend, alle Celery-Worker, Celery-Beat | `database.valkey.external.cidr` | 6379, 6380 |

- `cidr` ist deshalb Pflicht. Erreichst du die Datenbank über einen Namespace- oder Pod-Selektor, ersetze `networkpolicies.<policy>.rules.egress` durch deine Regel, oder schalte die Policy mit `enabled: false` ab und bring deine eigene mit.
- Läuft die Datenbank auf einem anderen Port, ersetze ebenfalls `rules.egress`. Ports in einer NetworkPolicy müssen Zahlen sein; aus einem Template entstünde ein Text, den Kubernetes als Portnamen liest.

### Render-Prüfungen

Das Chart verweigert die Darstellung, wenn eine Kombination im Cluster still scheitern würde:

- externe ArangoDB ohne `host`, mit einem Schema im `host`, mit einem anderen Schema als `http`/`https` oder zusätzlich `controllers.arangodb.enabled: true`
- `valkey.enabled: false` ohne `url` oder mit einer URL, die nicht mit `redis://` bzw. `rediss://` beginnt, und eine gesetzte `url` bei laufendem Valkey-Subchart
- eine Egress-Policy ohne `cidr` oder ohne den Port, den du konfiguriert hast

## Siehe auch

- [Kubernetes-Deployment](kubernetes.md) — Schritt-für-Schritt-Anleitung
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Referenz aller Umgebungsvariablen
- [Speicher konfigurieren (Object Storage)](../user-guide/object-storage.md) — Admin-UI und Migration
