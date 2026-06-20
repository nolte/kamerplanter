# Speicher konfigurieren (Object Storage)

Kamerplanter speichert alle Binärdaten — Fotos, Importe, Exporte und Backups — über einen austauschbaren Speicher-Adapter. Als Platform-Admin wählst du das passende Backend für deine Infrastruktur: ein lokales Dateisystem (empfohlen für Self-Hosted-Installationen und den Light-Modus) oder einen S3-kompatiblen Object-Storage-Dienst (für Produktion, Community- und Enterprise-Setups).

!!! note "Nur für Platform-Admins"
    Die Speicher-Einstellungen sind ausschließlich für Nutzer mit der Plattform-Rolle **admin** zugänglich. Im Light-Modus ist die Seite ohne Login direkt erreichbar.

---

## Voraussetzungen

- Plattform-Rolle **admin** (Full-Modus) oder Light-Modus-Betrieb
- Zugang über **Admin-Einstellungen > Speicher**

---

## Die zwei Storage-Backends

| Backend | Schlüssel | Einsatzszenario |
|---------|-----------|----------------|
| **Lokales Dateisystem** | `local-fs` | Light-Modus, Self-Hosted, Homelab, Raspberry Pi — keine externe Abhängigkeit |
| **S3-kompatibel** | `s3` | Produktion, Community Garden, Enterprise — AWS S3, MinIO, Hetzner Object Storage, Backblaze B2, Cloudflare R2, Wasabi, DigitalOcean Spaces, Google Cloud Storage (S3-API) |

Das aktive Backend ist plattformweit. Alle Mandanten verwenden denselben Storage-Adapter — die Mandanten-Isolation erfolgt durch das Key-Schema `t/{tenant_key}/...` im Storage.

---

## Backend konfigurieren

Öffne **Admin-Einstellungen > Speicher**. Die Seite zeigt:

- Das aktuell aktive Backend (`local-fs` oder `s3`)
- Den Verbindungsstatus (grün = erreichbar, rot = Fehler)
- Die nicht-geheimen Konfigurationsfelder des aktiven Backends

### Lokales Dateisystem (`local-fs`)

Das lokale Dateisystem ist das Standard-Backend und benötigt keine externe Konfiguration. Dateien werden auf einem persistenten Volume im Container-Pfad `/data/attachments` gespeichert.

!!! tip "Light-Modus und Self-Hosted"
    Im Light-Modus und auf Einzelknoten-Installationen ist `local-fs` die richtige Wahl. Kein Cloud-Account, kein API-Key — die Daten bleiben auf deinem Server.

**Einschränkung bei mehreren Replicas (Kubernetes):**

Wenn das Backend mit mehr als einer Replica läuft, muss das Persistent Volume den Zugriffsmodus `ReadWriteMany` (RWX) unterstützen (z. B. NFS, Longhorn, CephFS). Bei `ReadWriteOnce` (RWO) ist nur eine Replica möglich.

!!! warning "Signing-Secret bei mehreren Replicas setzen"
    Ohne gesetztes `STORAGE_LOCALFS_SIGNING_SECRET` generiert jeder Backend-Pod ein eigenes ephemeres Secret beim Start. Token-Downloads schlagen dann fehl, wenn die Anfrage bei einem anderen Pod landet als die Signierung. Setze das Secret als Kubernetes Secret und referenziere es über `envFrom`.

### S3-kompatibel (`s3`)

Die Admin-UI erlaubt es, alle nicht-geheimen S3-Parameter direkt zu setzen:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| **Endpoint-URL** | Vollständige URL des S3-Endpunkts | `https://s3.eu-central-1.amazonaws.com` |
| **Region** | AWS-Region oder MinIO-Region | `eu-central-1` |
| **Bucket** | Bucket-Name (muss vorab angelegt sein) | `kamerplanter-prod` |
| **Path-Style** | `true` für MinIO und die meisten Nicht-AWS-Anbieter | Ein/Aus |
| **TLS erzwingen** | Plain-HTTP verbieten (empfohlen: ein) | Ein/Aus |
| **KMS-Key-ID** | Optionaler Customer-Managed Key für serverseitige Verschlüsselung | ARN oder Key-ID |

!!! danger "S3-Credentials werden NICHT über die UI gesetzt"
    `Access Key ID` und `Secret Access Key` sind Secrets und werden **ausschließlich** über Umgebungsvariablen oder den External Secrets Operator (ESO) konfiguriert — nie über die Admin-UI. Weitere Details findest du unter [Umgebungsvariablen — Object Storage](../reference/environment-variables.md#object-storage-nfr-013) und [Helm Charts — Storage-Konfiguration](../deployment/helm.md#storage-konfiguration-nfr-013).

#### Verbindung testen

Nach dem Speichern der S3-Parameter kannst du auf **Verbindung prüfen** klicken. Das Backend führt folgende Prüfungen durch:

1. Verbindungsaufbau zum Endpunkt (TLS-Handshake)
2. Prüfung, ob der Bucket erreichbar ist (HEAD-Anfrage)
3. Rückmeldung der Zielregion (relevant für DSGVO-Prüfung)

Der Verbindungstest schreibt keine Daten und verändert den Bucket-Inhalt nicht.

#### DSGVO-Hinweis: Zielregion

Die Admin-UI zeigt nach einem erfolgreichen Verbindungstest die **Zielregion** des konfigurierten Backends an. Für EU-Tenants sollte die Region innerhalb der EU/EWR liegen. Bei Backends außerhalb der EU ist ein Auftragsverarbeitungsvertrag (AVV) mit dem Anbieter erforderlich (DSGVO Art. 28, Art. 46).

---

## Wie Anhänge im System funktionieren

Das Frontend kennt weder Bucket-Namen noch S3-URLs. Nutzer sehen ausschließlich stabile API-Adressen der Form:

```
/api/v1/t/{tenant-slug}/attachments/{attachment-id}
```

Alle Uploads, Downloads und Löschungen laufen ausschließlich über das Backend. Fotos, Importdateien und Exporte werden im Storage unter dem Pfadschema

```
t/{tenant_key}/{kategorie}/{yyyy}/{mm}/{ulid}.{ext}
```

abgelegt. Die Kategorie ist eines von: `diary`, `ipm`, `harvest`, `post_harvest`, `task`, `import`, `export`, `id_recognition`, `tenant_export`, `plant`.

!!! note "Thumbnails"
    Beim Hochladen von Bildern erzeugt Kamerplanter asynchron bis zu drei Thumbnail-Varianten (128 px, 512 px, 1280 px) und speichert sie im selben Backend.

---

## Health-Check und Monitoring

Der Storage-Status ist Teil des `/health/ready`-Endpunkts. Ist das konfigurierte Backend nicht erreichbar, antwortet der Endpunkt mit HTTP 503 — der Pod wird nicht als bereit markiert und erhält keinen Traffic.

Prometheus-Metriken (wenn aktiviert):

| Metrik | Beschreibung |
|--------|-------------|
| `kp_storage_health_status` | 1 = erreichbar, 0 = Fehler |
| `kp_storage_upload_total` | Uploads nach Backend, Kategorie, Status |
| `kp_storage_upload_bytes` | Upload-Volumen |
| `kp_storage_object_count` | Objektanzahl pro Mandant (täglich) |

---

## Migration zwischen Backends

Wenn du von `local-fs` zu S3 (oder umgekehrt) wechseln möchtest, stellt Kamerplanter ein CLI-Migrationsskript bereit:

```bash
# Dry-Run: zeigt alle Operationen ohne zu schreiben
python -m scripts.storage.migrate --from local-fs --to s3 --dry-run

# Verlustfreie Migration mit Prüfsummen-Verifikation
python -m scripts.storage.migrate --from local-fs --to s3 --checksum-verify

# Provider-Wechsel innerhalb S3
python -m scripts.storage.migrate --from s3 --to s3 --target-bucket=neuer-bucket

# Rückmigration
python -m scripts.storage.migrate --from s3 --to local-fs --checksum-verify
```

Die Migration läuft als Celery-Task mit Fortschrittsanzeige und kann bei Unterbrechung wieder aufgenommen werden. Ein Audit-Log dokumentiert jedes migrierte Objekt.

!!! warning "Backend erst umschalten, wenn Migration abgeschlossen"
    Schalte das Backend in den Admin-Einstellungen erst auf das neue Ziel um, wenn das Migrationsskript abgeschlossen und der Prüfsummen-Vergleich grün ist. Neue Uploads landen sonst im neuen Backend, während alte Dateien noch im alten Backend liegen.

---

## Häufige Fragen

??? question "Was passiert mit Anhängen, wenn ein Mandant gelöscht wird?"
    Kamerplanter löscht alle Binärdaten des Mandanten über `delete_prefix("t/{tenant_key}/")` im konfigurierten Storage-Backend. Dies geschieht bevor die ArangoDB-Einträge entfernt werden, damit die Metadaten noch abrufbar sind. Das Ergebnis wird im Audit-Log dokumentiert. Weitere Details: [Datenschutz (DSGVO) — Account und Mandanten löschen](privacy.md#account-loschen-art-17-dsgvo).

??? question "Kann ich MinIO im Cluster als S3-Backend verwenden?"
    Ja. Konfiguriere `STORAGE_S3_ENDPOINT_URL` auf die interne MinIO-Adresse (z. B. `http://minio.kamerplanter.svc:9000`), setze `STORAGE_S3_USE_PATH_STYLE=true` und `STORAGE_S3_ALLOW_PRIVATE_ENDPOINT=true`. Letztere Variable erlaubt es dem Backend, einen privaten (nicht öffentlich erreichbaren) Endpunkt anzusprechen. Weitere Details: [Umgebungsvariablen — Object Storage](../reference/environment-variables.md#object-storage-nfr-013).

??? question "Muss ich für local-fs ein PVC manuell anlegen?"
    Nein. Das Helm-Chart legt das PVC `backend-attachments` automatisch an, sofern `storage.backend: local-fs` gesetzt ist. Standardmäßig mit 100 Gi und `ReadWriteOnce`. Für Multi-Replica-Setups muss `storage.localFs.pvc.accessMode: ReadWriteMany` und eine passende Storage-Class (z. B. `longhorn` oder `nfs`) gesetzt werden.

??? question "Wie sehe ich, wie viel Speicherplatz belegt ist?"
    Die Admin-Statistikseite zeigt den geschätzten Speicherverbrauch pro Mandant (auf Basis der täglich aktualisierten Prometheus-Gauge `kp_storage_object_size_bytes`). Für lokales Dateisystem kann auch der PVC-Verbrauch direkt im Kubernetes-Dashboard oder mit `kubectl get pvc backend-attachments` abgelesen werden.

??? question "Werden EXIF-Daten aus Fotos entfernt?"
    Ja. Beim Upload entfernt das Backend standardmäßig alle EXIF-Metadaten (GPS-Koordinaten, Kameramodell, Aufnahmezeitpunkt). Wenn ein Mandant EXIF-Daten behalten möchte (z. B. für professionelle Dokumentation), kann dies pro Kategorie über `STORAGE_KEEP_EXIF_<CATEGORY>=true` aktiviert werden.

---

## Siehe auch

- [Umgebungsvariablen — Object Storage](../reference/environment-variables.md#object-storage-nfr-013)
- [Helm Charts — Storage-Konfiguration](../deployment/helm.md#storage-konfiguration-nfr-013)
- [Datenschutz (DSGVO)](privacy.md) — Datenlöschung, EXIF-Strip, Portabilität
- [Plattform-Admin](admin.md) — Gesamtübersicht Admin-Bereich
- [Betriebsprofile](../deployment/betriebsprofile.md) — Welches Profil brauche ich?
