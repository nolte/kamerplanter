---

ID: NFR-013
Titel: Speicheranbindung & Object-Storage-Adapter
Kategorie: Infrastruktur / Persistenz Unterkategorie: Object Storage, Binaerdaten, Adapter-Pattern, Multi-Backend
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14+, FastAPI, Helm, Kubernetes 1.28+, S3-kompatibles Object Storage, ReadWriteMany-PVs
Status: Genehmigt
Prioritaet: Hoch
Version: 1.2 (category `plant` fuer REQ-034 Pflanzenfoto-Galerie)
Autor: Business Analyst - Agrotech
Datum: 2026-04-27
Tags: [storage, object-storage, s3, minio, local-fs, adapter, photos, attachments, dsgvo, multi-tenant]
Abhaengigkeiten: [NFR-001, NFR-002, NFR-011, NFR-012, REQ-006, REQ-007, REQ-008, REQ-010, REQ-012, REQ-013, REQ-024, REQ-025 v1.2, REQ-027, REQ-032, REQ-034]
Betroffene Module: [backend.app.adapters.storage, backend.app.services.attachment, frontend.upload, helm.values, infra.k8s]
---

# NFR-013: Speicheranbindung & Object-Storage-Adapter

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.2 | 2026-06-19 | **category `plant` (REQ-034 Pflanzenfoto-Galerie):** `category`-Enum in §4.3 und Default-Mime-Whitelist in §5.2 um `plant` ergänzt (Foto-Whitelist `image/jpeg,png,webp,heic`, 25 MB). Storage-Key-Schema, Thumbnails, Pre-Sign, DSGVO-Erasure unverändert — REQ-034-Fotos hängen an der Pflanzeninstanz (REQ-013) und werden im Erasure als Scope `user_diary_attachments` klassifiziert. Kein Eingriff in den Adapter-Vertrag. |
| 1.1 | 2026-04-27 | **W-007 Fix (DSGVO-Erasure-Adapter-Methoden):** `delete_for_user(tenant_key, user_key, scope)` und `strip_exif_for_user(tenant_key, user_key, scope)` in §4.2 Adapter-Vertrag ergänzt. §6.2 Aufruf-Reihenfolge präzisiert: Storage-Cleanup MUSS als Phase 0 des Erasure-Tasks erfolgen, vor der ArangoDB-Löschung — sonst sind die `attachments`-Metadaten beim Lookup nicht mehr verfügbar. |
| 1.0 | 2026-04-25 | Erstversion — Adapter-Pattern, local-fs + S3 als Phase 1, Tenant-Isolation, Pfadschema, DSGVO-Konformitäts-Sektion. |

## 1. Business Case

### 1.1 User Stories

**Als** Self-Hosted-Betreiber
**moechte ich** Kamerplanter ohne externes Object-Storage-Konto starten koennen
**um** auf einem Heimserver oder einem Single-Node-K3s ohne Cloud-Abhaengigkeit zu arbeiten.

**Als** DevOps Engineer eines Enterprise-Tenants
**moechte ich** Binaerdaten (Tagebuch-Fotos, Exporte, Importe) auf einem dedizierten S3-Bucket ablegen
**um** Backups, Verschluesselung und Geo-Redundanz unabhaengig vom Cluster-Storage zu steuern.

**Als** Datenschutzbeauftragter
**moechte ich** dass jede Binaerdatei eindeutig einem Tenant zugeordnet ist und bei Tenant-Loeschung deterministisch entfernt wird
**um** DSGVO Art. 17 (Recht auf Loeschung) auch fuer Bild- und Anhangsdaten zu erfuellen.

**Als** Gaertner
**moechte ich** Fotos zu Tagebuch-Eintraegen, IPM-Inspektionen, Ernten und Aufgaben ablegen koennen
**ohne** mich um den darunterliegenden Speicher kuemmern zu muessen.

**Als** Hobbygaertner
**moechte ich** spaeter optional meinen eigenen Cloud-Speicher (Google Drive, Nextcloud) anbinden
**um** alle Pflanzendaten in meiner gewohnten Datenablage zu konsolidieren.

### 1.2 Geschaeftliche Motivation

Kamerplanter erzeugt eine wachsende Menge an **Binaerdaten** ausserhalb der relationalen/graph-basierten Stammdaten:

1. **Foto-Anhaenge:** Tagebuch (REQ-013), IPM-Inspektion (REQ-010), Erntefotos (REQ-007), Post-Harvest (REQ-008), Aufgaben-Belege (REQ-006), Pflanzenidentifikation (REQ-029)
2. **Importdateien:** CSV/Excel-Uploads (REQ-012)
3. **Exporte:** PDF-Druckansichten und CSV-Exporte (REQ-032)
4. **Backups & Snapshots:** Konfiguration, Tenant-Datenexporte (REQ-025)
5. **Optionale KI-Daten:** Embedding-Caches, Modell-Artefakte, Trainingsdaten

Diese Daten gehoeren **nicht** in ArangoDB, TimescaleDB oder PostgreSQL (Performance, Storage-Kosten, Backup-Fenster). Eine **abstrahierte, austauschbare Speicheranbindung** ist erforderlich, weil die Zielgruppen unterschiedliche Erwartungen haben:

- **Light-Modus / Self-Hosted (REQ-027):** Lokales Volume, keine externe Konfiguration noetig
- **Community Garden / SMB:** S3-kompatibel (MinIO im Cluster, Hetzner Object Storage)
- **Enterprise:** AWS S3, GCS, Azure Blob mit Cloud-KMS und Cross-Region-Replication
- **Privatnutzer (Zukunft):** Eigene Cloud (Google Drive, Dropbox, Nextcloud/WebDAV)

### 1.3 Abgrenzung

| Dokument | Fokus | Abgrenzung |
|----------|-------|------------|
| NFR-002 | Kubernetes-Plattform | **Wie** Workloads laufen — definiert Persistent Volumes als Mechanismus |
| NFR-011 | Retention & Aufbewahrungsfristen | **Wie lange** Daten gespeichert werden — gilt auch fuer Binaerdaten |
| NFR-012 | Cloud-Provider & Skalierung | **Wo** der Cluster laeuft — referenziert Object Storage als Cloud-Komponente |
| **NFR-013 (dieses Dokument)** | Speicheranbindung fuer Binaerdaten | **Welche Backends** unterstuetzt werden, **wie** der Adapter ausgetauscht wird |
| REQ-025 | Datenschutz / Betroffenenrechte | **Welche Rechte** Nutzer auf ihre Daten haben — verlangt Loeschung auch von Anhaengen |

NFR-013 definiert ausschliesslich die **Anbindung an externe Speicher fuer Binaerdaten**. Die strukturierten Domaenendaten (Pflanzen, Phasen, Sensoren, Tasks) bleiben in den definierten Datenbanken (NFR-001, NFR-012).

---

## 2. Architekturprinzipien

### 2.1 Adapter-Pattern (verbindlich)

Konsistent mit dem etablierten Projekt-Pattern (External Enrichment, Notification, LLM-Adapter) wird die Speicheranbindung als **austauschbarer Adapter** implementiert:

- **Interface (ABC):** `domain/interfaces/object_storage_adapter.py`
- **Implementierungen:** `data_access/storage/<backend>_adapter.py`
- **Registry:** `data_access/storage/registry.py` — Class-Level-Decorator-Pattern, Auswahl per Konfigurations-Schluessel
- **Service-Layer:** `services/attachment_service.py` — kennt nur das Interface, niemals ein konkretes Backend
- **Dependency Injection:** FastAPI `Depends(get_object_storage)` liefert den per Konfiguration aktivierten Adapter

**Begruendung:** Weder Service- noch API-Layer duerfen einen Backend-Wechsel beruehren. Ein neues Backend (z.B. Google Drive) wird durch einen einzelnen Adapter realisiert, nicht durch Aenderungen quer durch den Stack.

### 2.2 Trennung von Metadaten und Inhalt

Jede Binaerdatei wird durch **zwei** Persistenz-Ebenen beschrieben:

| Ebene | Inhalt | Persistenz |
|-------|--------|------------|
| **Metadaten** | `attachment_id`, `tenant_key`, `mime_type`, `byte_size`, `sha256`, `original_filename`, `created_at`, `created_by`, `category`, `storage_key` | ArangoDB (`attachments` Collection) |
| **Inhalt (Bytes)** | Die eigentliche Datei | Object Storage (Backend gemaess Konfiguration) |

Existierende Felder wie `photo_refs: list[str]` (REQ-006, REQ-007, REQ-008, REQ-010, REQ-013) werden als **Liste von `attachment_id`** gefuehrt — nicht mehr als rohe S3-URLs. Die in REQ-013 referenzierte `s3://kamerplanter/diary/...`-Form ist eine **vorlaeufige Notation** und wird durch dieses NFR konkretisiert.

### 2.3 Tenant-Isolation auf Storage-Ebene

Der Schluessel-Aufbau erzwingt die Tenant-Trennung **physisch** im Storage-Layout:

```
t/{tenant_key}/{category}/{yyyy}/{mm}/{attachment_id}.{ext}
```

Beispiele:

```
t/personal_max/diary/2026/04/01HQ8X9V3J7P5K2N4M6T8R0S2W.jpg
t/community_volkspark/ipm/2026/04/01HQ8X9V3J7P5K2N4M6T8R0S2X.jpg
t/personal_max/exports/2026/04/01HQ8X9V3J7P5K2N4M6T8R0S2Y.pdf
```

**Begruendung:**

- Tenant-Loeschung (REQ-024, REQ-025) wird durch `delete_prefix("t/{tenant_key}/")` deterministisch — kein Scan ueber Metadaten
- Bucket-Policies / Pfad-basierte IAM-Regeln moeglich
- Migration zwischen Backends erfolgt prefix-basiert
- Keine PII im Pfad (Tenant-Key ist ein opakes Slug)

### 2.4 Niemals Direct-Access vom Frontend zur Datenbank oder zum Storage

Streng konform zu NFR-001:

- Frontend kennt kein Storage-Backend, keine Bucket-Namen, keine Region
- Uploads laufen entweder ueber das Backend (`POST /api/v1/t/{tenant_slug}/attachments`) oder via **Pre-Signed URL**, die das Backend kurzlebig (max. 15 min) signiert
- Downloads laufen entweder als gestreamter Backend-Response oder via Pre-Signed Download-URL
- Das Backend setzt die ACL — das Storage-Backend ist niemals oeffentlich oder anonym lesbar

---

## 3. Unterstuetzte Backends

### 3.1 Phase 1 — Mindestumfang (verbindlich, in v1.0 implementiert)

| Backend | Schluessel | Anwendungsfall | Voraussetzungen |
|---------|-----------|----------------|-----------------|
| **Local Filesystem (PV)** | `local-fs` | Light-Modus (REQ-027), Self-Hosted, Single-Node, Dev | Kubernetes-Volume mit `ReadWriteMany` (RWX) bei >1 Replica; sonst `ReadWriteOnce` (RWO) |
| **S3-kompatibles Object Storage** | `s3` | Production / Community / Enterprise; deckt MinIO, AWS S3, Hetzner Object Storage, Backblaze B2, Wasabi, Cloudflare R2, Scaleway, GCS (S3-API), DigitalOcean Spaces ab | Endpoint, Region, Bucket, Access-Key, Secret-Key, optional KMS-Key |

**Begruendung Phase-1-Auswahl:**

- `local-fs` deckt alle Deployments **ohne** externe Abhaengigkeit ab — entscheidend fuer den Light-Modus (REQ-027) und die Hetzner-Empfehlung in NFR-012
- `s3` deckt mit einer einzigen Adapter-Implementierung praktisch alle relevanten Cloud-Anbieter ab, weil sich AWS/GCP/Azure (via Tools)/MinIO/Hetzner/Backblaze auf das S3-Protokoll geeinigt haben

### 3.2 Phase 2 — Geplante Erweiterungen (Roadmap, nicht in v1.0)

Folgende Backends sind **architektonisch vorgesehen**, aber nicht Teil von v1.0. Sie werden zu spaeteren Releases als zusaetzliche Adapter ausgeliefert. Der Adapter-Vertrag (Abschnitt 4.2) ist so geschnitten, dass jedes dieser Backends ohne API-Aenderung nachgezogen werden kann.

| Backend | Schluessel | Anwendungsfall | Besonderheiten / Risiken |
|---------|-----------|----------------|--------------------------|
| **Azure Blob Storage** (nativ) | `azure-blob` | Enterprise-Kunden mit bestehender Azure-Infrastruktur, Customer-Managed-Keys via Azure Key Vault | Eigenes SDK; Container statt Bucket; Soft-Delete-Support |
| **Google Cloud Storage** (nativ) | `gcs` | Enterprise-Kunden auf GCP, native IAM-Integration mit Workload Identity | Eigenes SDK; HMAC-Keys oder Workload Identity; Object Versioning |
| **Nextcloud / WebDAV** | `webdav` | Privatnutzer / Hobbygaertner mit eigener Nextcloud, Self-Hosted-Communities, Datensouveraenitaet | WebDAV ist **kein** Object-Store; keine Pre-Signed URLs, kein atomares Multi-Part — Streaming-only; PROPFIND fuer Metadaten |
| **Google Drive** | `gdrive` | Privatnutzer mit Google-Konto, geringe Einstiegshuerde | OAuth2-Flow pro Nutzer, nicht pro Tenant; API-Quotas; *kein klassisches Pre-Sign* — Tokens sind kurzlebig; Benennungs-Kollisionen moeglich |
| **Dropbox** | `dropbox` | Privatnutzer, einfache UX | OAuth2; Long-Polling fuer Aenderungen statt Webhooks; pfadbasiert, kein Bucket-Konzept |
| **Microsoft OneDrive / SharePoint** | `onedrive` | Enterprise-Kunden mit M365, Privatnutzer mit Office-Abo | Microsoft Graph API; Tenant-spezifische App-Registrierung; Drive-IDs |
| **Backblaze B2 (nativ)** | `b2` | Kostenoptimierte Backups, Cold-Storage | Native API ergaenzt die S3-API-Kompatibilitaet; oft guenstiger via native API |
| **IPFS / S3-Gateway** | `ipfs` | Forschung und Communities mit dezentralem Anspruch | Content-Adressing statt Pfade; **keine** Loeschung im klassischen Sinn — DSGVO-Bewertung erforderlich, vermutlich nicht Tenant-loeschungs-konform |
| **FTP / SFTP** | `sftp` | Legacy-Integrationen, Heim-NAS-Geraete | Kein natives Pre-Sign; Streaming-only; Verbindungspooling notwendig |

**Hinweis zu Cloud-Konten privater Nutzer (Google Drive, Dropbox, OneDrive):** Diese Backends sind **pro Nutzer**, nicht **pro Tenant** authentifiziert. Eine OAuth-Token-Verwaltung pro `Membership` ist Voraussetzung. Tenant-Loeschung kann diese externen Daten **nur** dann entfernen, wenn Kamerplanter zur Loeschzeit noch ein gueltiges Token besitzt — andernfalls greift die DSGVO-Verantwortung des externen Anbieters. Diese Einschraenkung muss dem Nutzer im Einstellungs-UI explizit angezeigt werden.

**Hinweis zu IPFS:** Aufgrund der Content-Addressing-Eigenschaft ist ein Loeschauftrag nach DSGVO Art. 17 technisch nicht garantiert. IPFS wird daher **nicht** als Default-Backend empfohlen und ist fuer personenbezogene Daten nur in Pinning-Setups mit dokumentierter Garbage-Collection-Strategie zulaessig.

### 3.3 Phase 3 — Optional / explizit nicht geplant

| Backend | Begruendung gegen Aufnahme |
|---------|----------------------------|
| **iCloud Drive** | Keine offene API fuer Server-zu-Server-Zugriff |
| **Mega.nz** | Eingeschraenkte API, ungewoehnliche Krypto-Architektur erschwert Adapter-Implementierung |
| **Rohes HTTP-Hosting** | Keine standardisierte Schreib-Schnittstelle |

---

## 4. Adapter-Vertrag

### 4.1 Konfigurationsschnittstelle

Die Auswahl des Backends erfolgt **ausschliesslich** ueber Konfiguration — niemals ueber Code-Aenderungen. Konfigurationsquellen in Reihenfolge der Praezedenz:

1. Umgebungsvariablen (Container-Runtime)
2. Helm-Values (`storage.backend`, `storage.s3.*`, `storage.localFs.*`)
3. Default (`local-fs`) fuer Light-Modus / Dev

**Pflicht-Variablen (allgemein):**

| Variable | Beispielwerte | Default |
|----------|---------------|---------|
| `STORAGE_BACKEND` | `local-fs`, `s3` | `local-fs` |
| `STORAGE_MAX_FILE_SIZE_MB` | `25` | `25` |
| `STORAGE_PRESIGN_TTL_SECONDS` | `900` | `900` (15 min) |
| `STORAGE_ALLOWED_MIME_TYPES` | `image/jpeg,image/png,image/webp,application/pdf,text/csv` | siehe Abschnitt 5.2 |
| `STORAGE_VIRUS_SCAN_ENABLED` | `true`/`false` | `false` |
| `STORAGE_VIRUS_SCAN_ENDPOINT` | URL zum ClamAV-REST-Wrapper | leer |

**Backend `local-fs`:**

| Variable | Beschreibung |
|----------|--------------|
| `STORAGE_LOCAL_FS_ROOT` | Mount-Pfad innerhalb des Containers, z.B. `/data/attachments` |
| `STORAGE_LOCAL_FS_PUBLIC_BASE_URL` | Base-URL des internen Backend-Endpunkts, der die Datei gestreamt ausliefert (z.B. `https://api.kamerplanter.local/api/v1/attachments`) |

**Backend `s3`:**

| Variable | Beschreibung |
|----------|--------------|
| `STORAGE_S3_ENDPOINT_URL` | z.B. `https://s3.eu-central-1.amazonaws.com` oder `http://minio.kamerplanter.svc:9000` |
| `STORAGE_S3_REGION` | z.B. `eu-central-1` (auch bei MinIO erforderlich) |
| `STORAGE_S3_BUCKET` | Bucket-Name |
| `STORAGE_S3_ACCESS_KEY_ID` | aus External Secrets Operator |
| `STORAGE_S3_SECRET_ACCESS_KEY` | aus External Secrets Operator |
| `STORAGE_S3_USE_PATH_STYLE` | `true` fuer MinIO und die meisten Nicht-AWS-Anbieter |
| `STORAGE_S3_KMS_KEY_ID` | optional, Customer-Managed Key (DSGVO Art. 32) |
| `STORAGE_S3_FORCE_TLS` | `true` (Default), Verbot von Plain-HTTP ausserhalb von Dev |

**Verboten:** Secrets im Klartext in Helm-Values, ConfigMaps oder Git. Konsistent mit NFR-012 §5.2 erfolgt die Secret-Aufloesung ueber den External Secrets Operator.

### 4.2 Interface-Definition

Das Adapter-Interface ist Backend-unabhaengig. Jeder Adapter aus Phase 1 oder Phase 2 muss exakt diese Methoden bedienen — wenn ein Backend eine Methode nicht nativ unterstuetzt, ist die im Vertrag genannte Fallback-Strategie umzusetzen:

| Methode | Verhalten | Fallback-Strategie (Backends ohne native Unterstuetzung) |
|---------|-----------|-----------------------------------------------------------|
| `put_object(key, stream, mime_type, metadata)` | Schreibt Bytes, Rueckgabe: `ObjectRef` (Key, ETag, Size) | Pflicht — kein Fallback. Backends ohne Streaming-Schreiben sind nicht unterstuetzt. |
| `get_object(key) -> Stream` | Liefert Bytes als async Stream | Pflicht. |
| `delete_object(key)` | Loescht eine einzelne Datei. Idempotent. | Pflicht. |
| `delete_prefix(prefix) -> int` | Loescht alle Objekte mit gegebenem Praefix, Rueckgabe: Anzahl. | Falls nicht nativ: `list_objects(prefix)` + Schleife mit `delete_object`. |
| `list_objects(prefix, page_token) -> Page` | Paginiertes Listing. | Pflicht. |
| `head_object(key) -> ObjectMetadata` | Metadaten ohne Body. | Falls nicht nativ: `get_object` mit Range-Request 0–0. |
| `presign_upload_url(key, mime_type, ttl) -> str` | Pre-Signed PUT-URL fuer Frontend-Direct-Upload. | Wenn Backend keine Pre-Sign-Mechanik hat (WebDAV, FTP, Google Drive): Adapter signalisiert `presign_supported = False`; Frontend faellt auf Backend-Proxy-Upload zurueck. |
| `presign_download_url(key, ttl, response_disposition) -> str` | Pre-Signed GET-URL. | Wenn nicht nativ: Adapter erzeugt eine Backend-interne signierte Token-URL (`/api/v1/attachments/{token}`), die der Backend-Endpunkt einloest und streamt. |
| `copy_object(src_key, dst_key)` | Server-seitiges Kopieren. | Falls nicht nativ: Stream-Pipe `get_object` → `put_object`. |
| `health_check() -> HealthStatus` | Connectivity-Probe fuer SLO-Monitoring (NFR-007). | Pflicht. |
| `delete_for_user(tenant_key, user_key, scope) -> int` <!-- W-007 --> | DSGVO-Erasure Phase 0 (REQ-025 §3.1, §3.5). Loescht alle Objekte, deren Metadaten in `attachments` `tenant_key + created_by == user_key` matchen, gefiltert nach `scope` (`user_personal` → Hard-Delete von Profil-/Notiz-Fotos). Rueckgabe: Anzahl geloeschter Objekte. | Falls keine Metadaten-Indexe nativ vorhanden: Fallback ueber `attachments`-Repository (ArangoDB-Lookup) + Schleife mit `delete_object`. |
| `strip_exif_for_user(tenant_key, user_key, scope) -> int` <!-- W-007 --> | DSGVO-Erasure Phase 0 (REQ-025). Entfernt EXIF-Daten (GPS, Kamera-Seriennummer, Aufnahmezeit) aus allen Bilddateien, deren Metadaten `tenant_key + created_by == user_key` matchen UND deren Tenant `STORAGE_KEEP_EXIF_<category>=true` gesetzt hat (NFR-013 §6.4). Bilder ohne EXIF und Tenants ohne Keep-EXIF werden uebersprungen. Rueckgabe: Anzahl modifizierter Bilder. | Falls Adapter kein In-Place-Editing unterstuetzt: `get_object` → EXIF entfernen → `put_object` mit gleichem Key (überschreiben). Atomic via Backend-Native-Copy wo möglich. |

**Kapazitaetsmerkmale (Capability Flags):**

Jeder Adapter deklariert seine Faehigkeiten, damit Service-Layer und UI sich anpassen:

```python
class StorageCapabilities(BaseModel):
    supports_presigned_upload: bool
    supports_presigned_download: bool
    supports_server_side_copy: bool
    supports_server_side_encryption: bool
    supports_versioning: bool
    supports_lifecycle_rules: bool
    max_object_size_bytes: int
    requires_per_user_oauth: bool  # True fuer gdrive/dropbox/onedrive
```

### 4.3 Ressourcen-Identifikation

**Storage-Key (intern, in DB persistiert):**

```
t/{tenant_key}/{category}/{yyyy}/{mm}/{ulid}.{ext}
```

- `tenant_key` — opaker Slug (REQ-024)
- `category` — Enum: `diary`, `ipm`, `harvest`, `post_harvest`, `task`, `import`, `export`, `id_recognition`, `tenant_export`, `plant` (`plant` = Pflanzenfoto-Galerie pro Pflanzeninstanz, REQ-034)
- `yyyy/mm` — Erstellungsdatum, ermoeglicht Lifecycle-Regeln und Backup-Pruning
- `ulid` — Universally Unique Lexicographically Sortable Identifier (zeitlich monoton, kollisionsfrei)
- `ext` — abgeleitet aus Mime-Type, niemals aus dem Original-Dateinamen (Schutz vor `..`/`\0`)

**Stable URI (Backend-API-Antwort):**

```
/api/v1/t/{tenant_slug}/attachments/{attachment_id}
```

Die Frontend-Anwendung kennt **nur** diese URI. Der Storage-Key ist eine implementierungsinterne Adresse.

---

## 5. Sicherheit & Validierung

### 5.1 Upload-Pipeline

Pflicht-Reihenfolge fuer jeden Upload:

1. **Authentifizierung** (REQ-023) — gueltiges Access-Token
2. **Autorisierung** (REQ-024) — `require_permission("attachment:create", scope=tenant)`
3. **Quota-Pruefung** — pro-Tenant- und pro-Mandant-Limit
4. **Mime-Type-Whitelist** — gegen `STORAGE_ALLOWED_MIME_TYPES`
5. **Magic-Byte-Validierung** — der erste Block wird gegen den deklarierten Mime-Type geprueft (Schutz vor maskierten Uploads)
6. **Groessenlimit** — gegen `STORAGE_MAX_FILE_SIZE_MB`
7. **Optional Virus-Scan** — wenn `STORAGE_VIRUS_SCAN_ENABLED=true`, ClamAV-Wrapper-Aufruf, Block auf Findings
8. **SHA-256-Hash-Berechnung** — Deduplizierung pro Tenant, Integritaet in `attachments`-Metadaten
9. **Schreiben** ueber Adapter
10. **Metadaten-Persistenz** in ArangoDB
11. **Audit-Log-Eintrag** — `who`, `when`, `tenant_key`, `attachment_id`, `category`, `byte_size`

Fehlschlaegt einer der Schritte 4–7, wird der Upload **vor** dem Schreiben ins Storage abgebrochen — es bleiben keine verwaisten Bytes zurueck.

### 5.2 Default Mime-Type-Whitelist

| Kategorie | Erlaubte Mime-Types | Max-Groesse (Default) |
|-----------|---------------------|------------------------|
| `diary`, `ipm`, `harvest`, `post_harvest`, `task`, `id_recognition`, `plant` | `image/jpeg`, `image/png`, `image/webp`, `image/heic` (server-seitige Konvertierung empfohlen) | 25 MB |
| `import` | `text/csv`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 50 MB |
| `export` | `application/pdf`, `text/csv`, `application/zip` | 200 MB |
| `tenant_export` | `application/zip` | 5 GB |

Whitelists sind ueber `STORAGE_ALLOWED_MIME_TYPES_<CATEGORY>` pro Kategorie ueberschreibbar.

### 5.3 Verschluesselung

| Ebene | Anforderung |
|-------|-------------|
| **In transit** | TLS 1.3 verbindlich (analog NFR-012 §7.1). Plain-HTTP ist nur in Dev-Profilen erlaubt und muss explizit per `STORAGE_S3_FORCE_TLS=false` aktiviert werden. |
| **At rest (S3)** | SSE-S3 als Minimum, SSE-KMS mit Customer-Managed Key fuer Production empfohlen. |
| **At rest (local-fs)** | LUKS-/dm-crypt-Verschluesselung des darunterliegenden Volumes (Cluster-Voraussetzung); Anwendungs-Layer-Verschluesselung optional, nur fuer Tenants mit aktivem Confidentiality-Mode. |
| **At rest (Drittanbieter)** | Vertraglich/technisch durch den jeweiligen Provider — siehe Abschnitt 7. |

### 5.4 Pre-Signed URL Hardening

- TTL maximal 15 Minuten (Default). Konfigurations-Maximum 60 Minuten — laengere Fenster werden vom Backend abgelehnt.
- TTL fuer Tenant-Exporte (DSGVO Art. 20, REQ-025) maximal 24 Stunden mit Audit-Log.
- Signatur enthaelt erwarteten Mime-Type und maximale Groesse — der Adapter lehnt Uploads mit abweichendem Header ab.
- Pre-Signed URLs werden niemals geloggt (auch nicht in Debug-Logs).

---

## 6. DSGVO-Konformitaet

### 6.1 Tenant-Loeschung

Bei Loeschung eines Tenants (REQ-024, REQ-025):

1. Alle Metadaten in `attachments` mit `tenant_key == X` werden geloescht
2. `delete_prefix("t/{X}/")` wird ueber den aktiven Adapter ausgefuehrt
3. Bei Backends ohne nativen Prefix-Delete (Phase 2) erfolgt die List+Loop-Implementierung in einem Celery-Task mit Wiederaufnahme bei Fehler
4. Erfolg/Fehler wird im Audit-Log dokumentiert

### 6.2 Nutzer-Loeschung

Bei Loeschung eines Nutzers innerhalb eines Tenants (REQ-025):

1. Alle Anhaenge mit `created_by == user_key` werden auf **Anonymisierung** vs. **Loeschung** geprueft (Klassifizierung in REQ-025 §3.1 `STORAGE_CLEANUP_RULES`)
2. Persoenliche Anhaenge (Profilfoto, eigene Notiz-Fotos — Scope `user_personal`) werden hart geloescht via `delete_for_user(tenant_key, user_key, scope='user_personal')`
3. Tagebuch-/Inspektions-/Behandlungs-/Erntefotos (Scope `user_diary_attachments`) bleiben — `created_by` wird auf `_anonymized` gesetzt; die Foto-Datei bleibt, weil sie zum Pflanzen-Datensatz gehoert
4. Bei Konflikt mit Aufbewahrungsfristen (CanG, PflSchG, NFR-011) erfolgt Anonymisierung statt Loeschung
5. **EXIF-Strip-Pass:** Wenn ein Tenant `STORAGE_KEEP_EXIF_<category>=true` gesetzt hat (§6.4), wird zusätzlich `strip_exif_for_user(tenant_key, user_key, scope='user_diary_attachments')` aufgerufen, um GPS/Geräte-Identifier aus den verbleibenden Diary-Fotos zu entfernen. Damit ist die Datei vollständig vom User entkoppelt.

<!-- Quelle: Widerspruchsanalyse W-007 -->
**Aufruf-Reihenfolge (W-007):** Die Nutzer-Loeschung im Object-Storage MUSS als **Phase 0** des `ErasureEngine.execute_scheduled_erasures()`-Tasks erfolgen, BEVOR ArangoDB-Edges/Nodes geloescht werden. Andernfalls verliert der Storage-Adapter den Zugriff auf die `attachments`-Metadaten und kann den `created_by`-Filter nicht mehr ausfuehren — die Dateien wuerden verwaist im Storage zurueckbleiben.

Erasure-Phasen-Reihenfolge (REQ-025 §3.1 `DELETE_ORDER`):

```
Phase 0   _storage_cleanup            (W-007, Fix-5)  ← braucht Metadaten
Phase 1   Edges (has_session, …)
Phase 2   Documents (refresh_tokens, …)
Phase 2.5 _pseudonymize_audit_collections  (W-002)
Phase 3   users
```

Bei Fehlschlag in Phase 0 wird der Erasure-Status auf `partially_completed` gesetzt — die ArangoDB-Loeschung wird NICHT ausgefuehrt, damit ein Re-Run beim naechsten Celery-Lauf moeglich ist. Manuelle Untersuchung durch den Operator erforderlich.
<!-- /Quelle: Widerspruchsanalyse W-007 -->

### 6.3 DSGVO Art. 20 — Datenuebertragbarkeit

Tenant-Exporte (REQ-025) muessen alle Anhaenge enthalten:

- ZIP-Archiv mit relativen Pfaden gemaess Storage-Key-Schema
- Manifest-JSON mit Mapping `attachment_id → relative_path → metadata`
- Erstellung asynchron via Celery
- Bereitstellung via kurzlebige Pre-Signed Download-URL (Abschnitt 5.4)

### 6.4 Art. 32 — Pseudonymisierung in Pfaden

- **Tenant-Key** ist ein opaker Slug (REQ-024), nicht der Tenant-Name
- **Attachment-Id** ist ein ULID, nicht der Original-Dateiname
- **Original-Dateiname** wird ausschliesslich in der Metadaten-Tabelle gespeichert, nicht im Storage-Key
- **EXIF-Daten** mit GPS-Koordinaten oder Geraete-Identifiern werden beim Upload **standardmaessig entfernt**; der Tenant kann die Beibehaltung pro Kategorie aktivieren (`STORAGE_KEEP_EXIF_<CATEGORY>=true`).

### 6.5 Drittanbieter-Backends (Phase 2)

Fuer Backends mit Daten ausserhalb der EU/EWR (Google Drive, Dropbox-US, OneDrive) gilt:

- Diese Backends sind **opt-in** auf Tenant-Ebene und erfordern eine zusaetzliche Einwilligung gemaess REQ-025
- Default fuer EU-Tenants bleibt `local-fs` oder ein EU-S3-Bucket
- Im UI muss die Zielregion des konfigurierten Backends sichtbar sein
- Auftragsverarbeitungsvertrag (DPA) mit dem Drittanbieter ist Voraussetzung — der Tenant-Admin bestaetigt das beim Konfigurieren

---

## 7. Backup, Replikation, RPO/RTO

### 7.1 Backend-spezifische Strategien

| Backend | Backup-Mechanismus | RPO | RTO |
|---------|--------------------|-----|-----|
| `local-fs` | PV-Snapshot (CSI-Snapshotter) + taeglicher rsync auf zweites PV oder externes S3 | 24 h (taeglich) bis 1 h (stuendlich, optional) | 4 h |
| `s3` (AWS / GCS via S3 / Azure-via-Tools) | Object Versioning + Cross-Region-Replication | 1 h | 1 h |
| `s3` (MinIO im Cluster) | MinIO Site-Replication oder externes S3 als Replikationsziel | 1 h | 4 h |
| `s3` (Hetzner / Backblaze / R2) | Object Versioning + extern getriggerter `rclone sync` Cron-Job | 24 h | 4 h |

Diese Werte sind **Empfehlungen** — die verbindlichen RPO/RTO-Ziele pro Skalierungsstufe ergeben sich aus NFR-012 §9.1 und werden hier nicht ueberschrieben, sondern erfuellt.

### 7.2 Disaster-Recovery-Test

Quartalsweiser Test (analog NFR-012 §9.2):

1. Random-Sample von 100 Anhaengen aus dem Backup wiederherstellen
2. SHA-256-Hashes mit Metadaten-Eintrag vergleichen
3. Ergebnis dokumentieren

### 7.3 Migration zwischen Backends

Skript `scripts/storage/migrate.py` mit Modi:

- `--from local-fs --to s3` (Initialmigration vor Provider-Wechsel)
- `--from s3 --to local-fs` (Rueckmigration / Light-Modus-Wechsel)
- `--from s3 --to s3 --target-bucket=...` (Provider-Wechsel)
- `--dry-run` — listet Operationen ohne Schreiben
- `--checksum-verify` — vergleicht SHA-256 nach Migration

Migration laeuft als Celery-Task mit Wiederaufnahmen, Fortschrittsanzeige und Audit-Log.

---

## 8. Performance & Skalierung

### 8.1 Zielwerte

| Metrik | Ziel | Begruendung |
|--------|------|-------------|
| Upload P95 (5 MB Foto) | < 3 s ueber Backend-Proxy | UX-Anforderung Mobile-Upload |
| Upload P95 (5 MB Foto, Pre-Signed) | < 1.5 s direkt zum Storage | reduzierter Backend-Hop |
| Download P95 (Thumbnail) | < 200 ms | Listenansichten muessen fluessig laden |
| Listing P95 (1.000 Anhaenge eines Runs) | < 500 ms | Tagebuch-Aggregation REQ-013 |

### 8.2 Thumbnails

- Beim Upload werden bis zu **3 Thumbnail-Varianten** asynchron via Celery erzeugt (`128`, `512`, `1280` px lange Kante)
- Thumbnails werden im selben Storage-Backend abgelegt: `t/{tenant_key}/{category}/{yyyy}/{mm}/{ulid}_t{size}.webp`
- Verloren gegangene Thumbnails werden lazy beim ersten Zugriff regeneriert

### 8.3 Caching

- HTTP-Caching ueber `ETag` (= SHA-256) und `Cache-Control: private, max-age=86400` fuer Pre-Signed Downloads
- CDN-Anbindung optional — wenn aktiviert, wird die Pre-Signed-URL ueber den CDN-Distributor signiert (CloudFront, Cloud CDN)

### 8.4 Bandbreite und Egress-Kosten

- Pre-Signed Download-URLs reduzieren Backend-Bandbreite signifikant — verbindlich fuer Production
- Local-FS-Setups muessen das Backend-Streaming-Volumen in der Pod-Auslegung beruecksichtigen (NFR-012 §4.1)
- Hetzner Object Storage und MinIO im Cluster haben **keine** Egress-Gebuehren — fuer kostensensible Tenants empfohlen

---

## 9. Beobachtbarkeit (Referenz NFR-007)

### 9.1 Metriken (Prometheus)

| Metrik | Typ | Labels |
|--------|-----|--------|
| `kp_storage_upload_total` | Counter | `backend`, `category`, `tenant`, `status` |
| `kp_storage_upload_bytes` | Histogram | `backend`, `category` |
| `kp_storage_upload_duration_seconds` | Histogram | `backend`, `category` |
| `kp_storage_download_total` | Counter | `backend`, `category`, `delivery` (`proxy`/`presigned`) |
| `kp_storage_delete_total` | Counter | `backend`, `scope` (`object`/`prefix`) |
| `kp_storage_object_count` | Gauge (taeglich) | `backend`, `tenant` |
| `kp_storage_object_size_bytes` | Gauge (taeglich) | `backend`, `tenant` |
| `kp_storage_health_status` | Gauge (0/1) | `backend` |

### 9.2 Logs

- Strukturiertes Logging (NFR-007) — JSON mit `attachment_id`, `tenant_key`, `category`, `bytes`, `duration_ms`, `result`
- **Verbot:** Logs duerfen niemals den Datei-Inhalt, Pre-Signed-URLs oder Original-Dateinamen enthalten

### 9.3 Alerts

| Alert | Schwellwert | Severity |
|-------|------------|----------|
| Storage Health Probe fail | > 3 aufeinanderfolgende Fehler | P2 |
| Upload Error Rate | > 5 % ueber 10 min | P2 |
| Backend-Latenz P95 | > 5 s ueber 10 min | P3 |
| Tenant ueberschreitet Quota | > 100 % | P3 |
| Lokales PV ueber 80 % | dauerhaft | P2 |

---

## 10. Helm-Values-Skizze

```yaml
storage:
  backend: s3   # local-fs | s3
  maxFileSizeMb: 25
  presignTtlSeconds: 900
  virusScan:
    enabled: false
    endpoint: ""

  localFs:
    root: /data/attachments
    pvc:
      size: 100Gi
      accessMode: ReadWriteMany
      storageClass: longhorn

  s3:
    endpointUrl: https://s3.eu-central-1.amazonaws.com
    region: eu-central-1
    bucket: kamerplanter-prod
    usePathStyle: false
    forceTls: true
    kmsKeyId: ""
    credentialsRef:
      secretName: storage-s3-credentials
      accessKeyIdKey: AWS_ACCESS_KEY_ID
      secretAccessKeyKey: AWS_SECRET_ACCESS_KEY
```

---

## 11. Akzeptanzkriterien

| ID | Kriterium |
|----|-----------|
| **AC-01** | Backend-Wechsel zwischen `local-fs` und `s3` erfordert ausschliesslich Konfigurations-Aenderungen, keine Code-Aenderungen. |
| **AC-02** | Light-Modus (REQ-027) startet ohne externe Storage-Konfiguration und nutzt `local-fs` als Default. |
| **AC-03** | Tenant-Loeschung entfernt alle zugehoerigen Binaerdaten beider Backends innerhalb von 24 Stunden vollstaendig (Audit-Log-Beleg). |
| **AC-04** | Frontend-Code referenziert keinerlei Storage-Backend, Bucket-Namen oder S3-URLs. Alle Referenzen laufen ueber `attachment_id` und `/api/v1/t/{tenant_slug}/attachments/...`. |
| **AC-05** | Pre-Signed URLs haben eine TTL von max. 15 Minuten (Default), Fehlversuche bei laengerer TTL werden vom Backend abgelehnt. |
| **AC-06** | Mime-Type- und Magic-Byte-Validierung blockiert alle Uploads, deren tatsaechlicher Inhalt nicht zur Whitelist passt. |
| **AC-07** | Migration zwischen `local-fs` und `s3` ist mit dem Migrations-Skript verlustfrei moeglich (SHA-256-Verify auf 100 % der Objekte). |
| **AC-08** | Storage-Health-Probe ist Teil des `/health/ready`-Endpunkts und blockiert Pod-Ready, wenn das konfigurierte Backend nicht erreichbar ist. |
| **AC-09** | Existierende `photo_refs`-Felder (REQ-006/007/008/010/013) werden auf `attachment_id`-Listen migriert; eine vorhandene Migrations-Routine konvertiert Bestandsdaten. |
| **AC-10** | Adapter-Vertrag (Abschnitt 4.2) ist als ABC implementiert und durch ein gemeinsames Test-Set verifiziert, das fuer jeden Adapter (Phase 1: `local-fs`, `s3`) gruen sein muss. |
| **AC-11** | Dokumentation enthaelt Adapter-Roadmap (Phase 2: `azure-blob`, `gcs`, `webdav`, `gdrive`, `dropbox`, `onedrive`, `b2`) als Erweiterungspunkt. |

---

## 12. Offene Punkte / Folge-Entscheidungen

| Nr. | Frage | Entscheider |
|-----|-------|-------------|
| O-01 | Soll Phase 2 nach Stabilisierung von v1.0 anhand des Nutzerbedarfs (Befragung) priorisiert werden oder fix nach Roadmap? | Produkt |
| O-02 | Wird ein eingebauter MinIO-Operator als Helm-Subchart fuer Self-Hosted ausgeliefert, oder bleibt MinIO eine externe Voraussetzung? | DevOps |
| O-03 | Welche Quota-Defaults gelten pro Skalierungsstufe (Small/Medium/Large/Enterprise gemaess NFR-012 §10)? | Produkt + Finance |
| O-04 | Wird Application-Layer-Encryption (zusaetzlich zu Storage-Layer) fuer "Confidentiality-Mode"-Tenants angeboten? | Security |
| O-05 | Sollen Phase-2-Backends in Privatnutzer-Konten (Google Drive, Dropbox) einer separaten Lizenz-/Tarif-Stufe vorbehalten sein? | Produkt |

---

## 13. Zusammenfassung

NFR-013 etabliert die **Speicheranbindung** als austauschbaren Adapter und legt die Mindestanforderungen fest:

1. **Phase 1** liefert `local-fs` (Light-Modus / Self-Hosted) und `s3` (S3-kompatibles Object Storage, deckt AWS, MinIO, Hetzner, Backblaze, R2, GCS, Wasabi, Spaces ab).
2. **Phase 2** ist architektonisch vorbereitet fuer native `azure-blob`, `gcs`, `webdav` (Nextcloud), `gdrive`, `dropbox`, `onedrive`, `b2` und weitere — alle ohne API-Aenderung anschliessbar.
3. Alle Anwendungsfaelle (Tagebuch, IPM, Ernte, Post-Harvest, Aufgaben, Importe, Exporte, KI-Bilderkennung) laufen ausschliesslich gegen das Adapter-Interface.
4. Tenant-Isolation erfolgt durch das Schluessel-Schema `t/{tenant_key}/...` — DSGVO-Loeschung wird durch `delete_prefix` deterministisch.
5. Pre-Signed URLs sind verbindlich fuer Production zur Bandbreitenentlastung; Backends ohne Pre-Sign-Faehigkeit fallen automatisch auf Backend-Proxy-Streaming zurueck.
6. Kein Frontend kennt ein Storage-Backend, einen Bucket-Namen oder eine S3-URL — der Backend-Endpunkt mit `attachment_id` ist die einzige stabile Adresse.

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Genehmigt
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
