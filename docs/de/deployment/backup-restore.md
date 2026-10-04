# Backup & Wiederherstellung (Kubernetes)

Das Helm-Chart bringt eine Sicherung der ArangoDB-Datenbank mit: einen CronJob, der die Anwendungsdatenbank mit `arangodump` sichert und den Dump in einen S3-Bucket hochlädt. Diese Seite zeigt dir, wie du die Sicherung einschaltest, wie du den letzten Sicherungszeitpunkt prüfst und wie du eine Sicherung in einen leeren Namespace zurückspielst.

Für Docker Compose gilt [Docker Compose Dauerbetrieb](docker-dauerbetrieb.md).

---

## Was gesichert wird — und was nicht

| Daten | Gesichert durch | Hinweis |
|---|---|---|
| ArangoDB (alle Fachdaten, Konten, Mandanten) | CronJob `kamerplanter-arangodb-backup` | Dump der Anwendungsdatenbank inkl. Graph-Definition und Indizes |
| Anhänge (Fotos, Exporte) mit `storage.backend: s3` | Versionierung bzw. Replikation des Buckets | Am Bucket einstellen, nicht im Chart |
| Anhänge mit `storage.backend: local-fs` | **nicht** durch das Chart | VolumeSnapshot des PVC `backend-attachments` über deinen CSI-Treiber |
| `kamerplanter-secrets` | **nicht** durch das Chart | Getrennt sichern, z. B. im Secret-Store des External Secrets Operators |
| TimescaleDB | **nicht** durch das Chart | Gehört nicht zu den Produktions-Values des Charts |
| Valkey | nicht nötig | Cache und Task-Warteschlange, keine Fachdaten |

!!! danger "Ohne die alten Secrets ist eine Wiederherstellung unvollständig"
    Einige Felder in der Datenbank sind mit `FERNET_KEY` verschlüsselt (zum Beispiel hinterlegte Zugangsdaten für Home Assistant oder Wetterdienste), und Löschnachweise hängen an `ERASURE_TOMBSTONE_SALT`. Spielst du einen Dump mit neu erzeugten Werten zurück, sind diese Felder nicht mehr lesbar. Sichere `kamerplanter-secrets` deshalb zusammen mit den Dumps und stelle beim Wiederherstellen dieselben Werte bereit.

---

## Sicherung einschalten

### 1. Bucket und Zugangsdaten vorbereiten

Lege einen Bucket an (Versionierung und Standard-Verschlüsselung am Bucket sind empfohlen) und einen Zugangsschlüssel, der in diesem Bucket nur lesen, schreiben, auflisten und löschen darf. Das Chart legt keinen Bucket an.

```bash
kubectl create secret generic kamerplanter-backup-s3 \
  --namespace kamerplanter \
  --from-literal=AWS_ACCESS_KEY_ID="dein-access-key" \
  --from-literal=AWS_SECRET_ACCESS_KEY="dein-secret-key"
```

Für GitOps erzeugst du das Secret besser mit dem External Secrets Operator (siehe [ArgoCD](argocd.md)).

### 2. Values setzen

```yaml title="values-production.yaml"
backup:
  enabled: true
  schedule: "15 2 * * *"        # täglich 02:15 (Zeitzone des Clusters)
  retentionDays: 30             # ältere Dumps werden gelöscht, der neueste nie
  scratchSize: 10Gi             # Platz für einen Dump auf der Node-Disk
  s3:
    provider: AWS               # rclone-Providername: AWS, Minio, Ceph, Cloudflare, Other
    endpointUrl: https://s3.eu-central-1.amazonaws.com
    region: eu-central-1
    bucket: mein-kamerplanter-backup
    prefix: kamerplanter/arangodb
    serverSideEncryption: AES256   # oder aws:kms mit kmsKeyId, oder "" bei Anbietern ohne SSE
    credentialsRef:
      secretName: kamerplanter-backup-s3
```

Ohne `backup.s3.bucket` bricht das Rendern mit einer Meldung ab — eine eingeschaltete Sicherung ohne Ziel würde jede Nacht still scheitern.

So arbeitet ein Lauf:

1. Der Init-Container `dump` (dasselbe ArangoDB-Image wie die Datenbank) sichert die Anwendungsdatenbank mit dem Konto der Anwendung nach `/backup/<Zeitstempel>/`.
2. Der Container `main` (rclone) lädt den Dump nach `s3://<bucket>/<prefix>/<Zeitstempel>/` und schreibt den Zeitstempel in `<prefix>/LATEST`.
3. Danach löscht er Dump-Verzeichnisse, die älter als `retentionDays` sind — nie das gerade geschriebene. Fällt die Sicherung länger aus, bleibt der letzte gute Dump also erhalten.

Kein Passwort steht auf einer Kommandozeile; `arangodump` liest es selbst aus der Umgebung. Die Pods laufen ohne Root-Rechte mit schreibgeschütztem Dateisystem und eigener NetworkPolicy (ArangoDB, DNS und Port 443 nach außen).

!!! warning "S3 im Cluster oder im privaten Netz"
    Die NetworkPolicy des Backup-Pods schließt wie die des Backends die privaten Netze (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) und `169.254.0.0/16` aus. Ein MinIO oder Ceph RGW im Cluster erreichst du erst mit einer zusätzlichen Egress-Regel in `networkpolicies.arangodb-backup.rules.egress`.

### 3. Sofort einen Lauf auslösen

```bash
kubectl create job --namespace kamerplanter \
  --from=cronjob/kamerplanter-arangodb-backup kamerplanter-arangodb-backup-manual
kubectl logs --namespace kamerplanter job/kamerplanter-arangodb-backup-manual -c main
```

Erwartete letzte Zeile: `backup <Zeitstempel> uploaded`.

---

## Sicherungszeitpunkt prüfen (RPO)

Der Zeitstempel in `<prefix>/LATEST` ist der Wiederherstellungspunkt. Die Differenz zur aktuellen Zeit ist dein tatsächlicher RPO:

```bash
# Mit einem lokal konfigurierten rclone-Remote "backup"
rclone cat backup:mein-kamerplanter-backup/kamerplanter/arangodb/LATEST

# Oder im Cluster
kubectl get cronjob --namespace kamerplanter kamerplanter-arangodb-backup \
  -o jsonpath='{.status.lastSuccessfulTime}'
```

Bei täglichem Zeitplan liegt der RPO bei höchstens 24 Stunden plus Laufzeit. Für einen kürzeren RPO setzt du `backup.schedule` entsprechend (zum Beispiel `"15 * * * *"` für stündlich).

---

## In einen leeren Namespace wiederherstellen

Diese Schritte stellen eine Sicherung in eine frische Installation her. Sie sind so am 2026-10-04 durchgespielt worden (Dump, Upload, Download, `arangorestore`, Neustart der Anwendung; alle 309 Collections mit identischer Dokumentanzahl und identischen Indizes).
<!-- #2122; Protokoll: test-reports/backup-restore/2026-10-04-arangodb-restore-drill.md -->

!!! warning "ArgoCD: automatischen Sync anhalten"
    Wird der Namespace von ArgoCD verwaltet, halte den automatischen Sync (und `selfHeal`) der Application während der Wiederherstellung an. Sonst skaliert ArgoCD die Deployments aus Schritt 2 sofort wieder hoch.

### 1. Chart installieren

Lege `kamerplanter-secrets` mit **denselben Werten** wie in der gesicherten Installation an und installiere das Chart wie unter [Kubernetes-Deployment](kubernetes.md) beschrieben. Warte, bis `kamerplanter-arangodb-0` bereit ist.

### 2. Anwendung anhalten

```bash
kubectl scale deployment --namespace kamerplanter \
  kamerplanter-backend kamerplanter-celery-worker kamerplanter-celery-beat --replicas=0
```

### 3. Dump holen

Auf deinem Rechner, mit einem rclone-Remote `backup` auf denselben Bucket:

```bash
STAMP="$(rclone cat backup:mein-kamerplanter-backup/kamerplanter/arangodb/LATEST)"
rclone copy "backup:mein-kamerplanter-backup/kamerplanter/arangodb/${STAMP}" "./restore/${STAMP}"
kubectl cp --namespace kamerplanter "./restore/${STAMP}" kamerplanter-arangodb-0:/tmp/restore -c main
```

Für einen älteren Stand ersetzt du `STAMP` durch einen der Verzeichnisnamen unter `<prefix>/`.

### 4. Zurückspielen

`arangorestore` läuft im ArangoDB-Container, der das Root-Passwort schon in seiner Umgebung hat; `@ARANGO_ROOT_PASSWORD@` liest es von dort, ohne dass es auf der Kommandozeile steht:

```bash
kubectl exec --namespace kamerplanter kamerplanter-arangodb-0 -c main -- \
  arangorestore \
    --server.endpoint tcp://127.0.0.1:8529 \
    --server.username root \
    --server.password @ARANGO_ROOT_PASSWORD@ \
    --server.database kamerplanter \
    --create-database true \
    --include-system-collections true \
    --overwrite true \
    --input-directory /tmp/restore

kubectl exec --namespace kamerplanter kamerplanter-arangodb-0 -c main -- rm -rf /tmp/restore
```

`--overwrite true` ersetzt die Collections, die die frische Installation beim ersten Start angelegt hat.

### 5. Anwendung starten

```bash
kubectl scale deployment --namespace kamerplanter kamerplanter-backend --replicas=1
kubectl scale deployment --namespace kamerplanter kamerplanter-celery-worker kamerplanter-celery-beat --replicas=1
```

Beim Start prüft das Backend den Migrationsstand; ein Dump aus derselben Version wendet keine Migration an, ein älterer Dump wird auf den aktuellen Stand migriert. Danach den automatischen Sync in ArgoCD wieder einschalten.

---

## Wiederherstellung üben

Spiele die Wiederherstellung regelmäßig (zum Beispiel quartalsweise) in einen Test-Namespace durch und vergleiche die Dokumentanzahl je Collection zwischen Quelle und Ziel. Ein Backup, dessen Wiederherstellung nie geübt wurde, ist kein belastbares Backup.

## Siehe auch

- [Helm Charts — Storage-Konfiguration](helm.md#storage-konfiguration-nfr-013)
- [Kubernetes-Deployment](kubernetes.md)
- [ArgoCD](argocd.md)
