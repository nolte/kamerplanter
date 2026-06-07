# Umgebungsvariablen

Alle Konfigurationsparameter des Kamerplanter-Backends werden über Umgebungsvariablen gesteuert. Die Variablen werden von `pydantic-settings` geladen — Groß-/Kleinschreibung ist nicht relevant.

!!! tip "Lokale Konfiguration"
    Für die Docker-Compose-Umgebung alle Werte in eine `.env`-Datei im Repository-Wurzelverzeichnis eintragen. Eine Vorlage liegt als `.env.example` bereit:
    ```bash
    cp .env.example .env
    ```

---

## Datenbankverbindung

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `ARANGODB_HOST` | `localhost` | Ja | Hostname oder IP-Adresse der ArangoDB-Instanz |
| `ARANGODB_PORT` | `8529` | Nein | TCP-Port der ArangoDB |
| `ARANGODB_DATABASE` | `kamerplanter` | Ja | Name der Zieldatenbank |
| `ARANGODB_USERNAME` | `root` | Ja | Datenbanknutzer |
| `ARANGODB_PASSWORD` | — | Ja | Passwort des Datenbanknutzers |
| `ARANGO_ROOT_PASSWORD` | — | Ja* | Root-Passwort für den ArangoDB-Container (nur Docker) |

*`ARANGO_ROOT_PASSWORD` wird direkt an den ArangoDB-Container übergeben und ist für den Start der Datenbank erforderlich.

!!! warning "Produktionspasswörter"
    Verwenden Sie niemals den Standardwert `rootpassword` in produktiven Umgebungen. Generieren Sie sichere Passwörter: `openssl rand -hex 32`

---

## Cache und Aufgaben-Queue

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Ja | Verbindungs-URL für Redis oder Valkey (Celery Broker und Backend-Cache) |

**Format:** `redis://[user]:[password]@[host]:[port]/[db]`

**Beispiele:**
```
redis://localhost:6379/0                    # Lokal ohne Auth
redis://:meinpasswort@redis:6379/0          # Mit Passwort
rediss://user:pass@redis-host:6380/1        # TLS (rediss://)
```

---

## Sicherheit und Authentifizierung

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-in-production-...` | Ja | Geheimer Schlüssel für JWT-Signierung (HS256) |
| `JWT_ALGORITHM` | `HS256` | Nein | JWT-Signaturalgorithmus |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Nein | Gültigkeitsdauer des JWT-Access-Tokens in Minuten |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Nein | Gültigkeitsdauer des Refresh-Tokens in Tagen |
| `FERNET_KEY` | — | Nein | Fernet-Schlüssel zum Verschlüsseln von OIDC-Provider-Secrets |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Nein | E-Mail-Verifikation bei Registrierung erzwingen |
| `HIBP_ENABLED` | `false` | Nein | "Have I Been Pwned"-Prüfung bei Passwortänderung aktivieren |

!!! danger "JWT_SECRET_KEY in Produktion ändern"
    Der Standardwert `change-me-in-production-use-openssl-rand-hex-32` darf in produktiven Umgebungen **nicht** verwendet werden. Generieren Sie einen sicheren Wert:
    ```bash
    openssl rand -hex 32
    ```
    Änderungen des `JWT_SECRET_KEY` machen alle aktiven Tokens ungültig — alle Nutzer werden abgemeldet.

---

## Betriebsmodus

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `KAMERPLANTER_MODE` | `full` | Nein | Betriebsmodus: `full` (Auth + Mandanten) oder `light` (kein Auth, lokale Einzelnutzung) |
| `DEBUG` | `false` | Nein | Debug-Logging aktivieren (verbose, nie in Produktion) |
| `FRONTEND_URL` | `http://localhost:5173` | Nein | URL des Frontends (wird für E-Mail-Links verwendet) |

### Light-Modus (`KAMERPLANTER_MODE=light`)

Im Light-Modus entfällt die Token-Authentifizierung. Die API ist ohne Anmeldung verwendbar. Dieser Modus ist für lokale Einzelinstallationen ohne Internet-Exposition gedacht.

!!! danger "Light-Modus nicht öffentlich exponieren"
    Der Light-Modus deaktiviert alle Authentifizierungsschichten. Niemals mit einem öffentlich erreichbaren Port betreiben.

---

## CORS-Konfiguration

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Nein | JSON-Array erlaubter Origins für CORS |

**Format:** Immer als JSON-Array im String-Format:
```bash
CORS_ORIGINS='["https://app.example.com","https://app2.example.com"]'
```

---

## E-Mail

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `EMAIL_ADAPTER` | `console` | Nein | E-Mail-Adapter: `console` (Ausgabe im Log), `smtp`, `resend` |
| `SMTP_HOST` | `localhost` | Nein | SMTP-Server-Hostname |
| `SMTP_PORT` | `587` | Nein | SMTP-Port |
| `SMTP_USERNAME` | — | Nein | SMTP-Benutzername |
| `SMTP_PASSWORD` | — | Nein | SMTP-Passwort |
| `SMTP_FROM_EMAIL` | `noreply@kamerplanter.example` | Nein | Absenderadresse für System-E-Mails |
| `SMTP_USE_TLS` | `true` | Nein | STARTTLS für SMTP aktivieren |

Im Entwicklungsmodus (`EMAIL_ADAPTER=console`) werden E-Mails nicht gesendet, sondern im Backend-Log ausgegeben.

---

## Externe Datenanreicherung (REQ-011)

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `PERENUAL_API_KEY` | — | Nein | API-Schlüssel für Perenual-Pflanzendatenbank |
| `TREFLE_API_KEY` | — | Nein | API-Schlüssel für Tréflé-Pflanzendatenbank |
| `ENRICHMENT_HTTP_TIMEOUT` | `30` | Nein | HTTP-Timeout für externe API-Anfragen (Sekunden) |

GBIF wird ohne API-Key verwendet (öffentliche API). Perenual und Tréflé erfordern kostenlose Registrierung.

---

## Knowledge Service — Re-Ranking (optional)

Diese Variablen konfigurieren den optionalen Cross-Encoder-Re-Ranker des Knowledge Service. Ist `RERANKER_URL` leer, arbeitet der Knowledge Service im Hybrid-Search-only-Modus (Graceful Degradation). Siehe [ADR-007](../adr/007-cross-encoder-reranking.md).

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `RERANKER_URL` | `` (leer) | Nein | HTTP-URL des Reranker-Microservice, z. B. `http://reranker-service:8081`. Leer = Re-Ranking deaktiviert. |
| `RERANKER_INITIAL_K` | `20` | Nein | Anzahl der Chunks, die aus dem Hybrid-Search-Schritt abgerufen werden (Over-Retrieval). |
| `RERANKER_TOP_K` | `5` | Nein | Anzahl der Chunks, die nach dem Re-Ranking an den LLM-Kontext übergeben werden. |
| `RERANKER_MODEL` | `bge-reranker-v2-m3` | Nein | ONNX-Modellname im Reranker-Service-Container (Verzeichnis unter `/app/models/onnx/`). |

!!! note "RERANKER_MODEL gehört zum Reranker-Service, nicht zum Knowledge Service"
    `RERANKER_MODEL` wird als Umgebungsvariable am `reranker-service`-Container gesetzt — nicht am `knowledge-service`. Die anderen drei Variablen (`RERANKER_URL`, `RERANKER_INITIAL_K`, `RERANKER_TOP_K`) gehören zum Knowledge Service.

!!! tip "Ressourcenbedarf"
    Der Reranker-Service benötigt 1,5–4 GB RAM (je nach Modell) und addiert ~500ms Latenz pro Anfrage. Für Raspberry Pi und ressourcenarme Umgebungen empfiehlt sich, `RERANKER_URL` leer zu lassen.

---

## mDNS / Zeroconf Discovery

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `MDNS_ENABLED` | `false` | Nein | mDNS-Service-Announcement aktivieren (`_kamerplanter._tcp.local.`) |
| `INSTANCE_ID` | *(auto)* | Nein | Eindeutige Instanz-ID (z. B. `kp-abc123`). Wird beim Start automatisch generiert, wenn leer. |

Wenn aktiviert, annonciert das Backend einen `_kamerplanter._tcp.local.`-Service im lokalen Netzwerk. Home Assistant erkennt diesen Service automatisch und bietet die Einrichtung der Kamerplanter-Integration an.

!!! info "Stabile Instanz-ID"
    Die `INSTANCE_ID` wird für die Duplikat-Erkennung in Home Assistant verwendet. Wenn sie leer bleibt, wird bei jedem Neustart eine neue ID generiert. Für stabile Discovery sollte ein fester Wert gesetzt werden, z. B. `INSTANCE_ID=kp-mein-server`.

### mDNS und Kubernetes

mDNS basiert auf Multicast-UDP (Port 5353) im lokalen Layer-2-Netzwerk. In Standard-Kubernetes-Clustern funktioniert mDNS **nicht**, da:

1. **Overlay-Netzwerk blockiert Multicast** — Standard-CNIs (Calico, Cilium, Flannel) routen nur L3-Traffic. Multicast-Pakete aus einem Pod erreichen das physische LAN nicht — Home Assistant sieht die Announcements nie.
2. **Pod-IP ist nicht LAN-erreichbar** — Selbst bei funktionierendem Multicast wuerde die annoncierte Pod-IP (z. B. `10.42.x.x`) von ausserhalb des Clusters nicht erreichbar sein.

| Deployment | `MDNS_ENABLED` | Begruendung |
|------------|:-----------:|-------------|
| Docker Compose / Bare Metal | `true` | Backend laeuft direkt im LAN — `MDNS_ENABLED=true` setzen |
| K3s / MicroK8s Single-Node + `hostNetwork: true` | `true` | Pod teilt Host-Netzwerk — Multicast erreicht das LAN |
| Standard K8s Cluster | `false` | Overlay-Netzwerk blockiert Multicast — manueller Config Flow in HA als Fallback |
| Cloud (AWS, GCP, Azure) | `false` | Kein lokales Netzwerk vorhanden |

!!! warning "hostNetwork ist ein Trade-off"
    Mit `hostNetwork: true` teilt der Pod den Netzwerk-Namespace des Hosts. Multicast funktioniert, aber auf Kosten der Netzwerk-Isolation (Port-Konflikte möglich, keine NetworkPolicy-Enforcement). Nur für Homelab-/Raspberry-Pi-Szenarien empfohlen.

Im Helm-Chart ist `MDNS_ENABLED` standardmaessig auf `false` gesetzt. Der manuelle Config Flow in Home Assistant (URL-Eingabe) funktioniert in jedem Deployment-Szenario als Fallback.

---

## Home Assistant Integration (REQ-005)

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `HA_URL` | — | Nein | Home-Assistant-Basis-URL, z. B. `http://homeassistant.local:8123` |
| `HA_ACCESS_TOKEN` | — | Nein | Long-Lived Access Token aus Home Assistant |
| `HA_TIMEOUT` | `10` | Nein | HTTP-Timeout für HA-Anfragen (Sekunden) |

---

## Rate Limiting

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `RATE_LIMIT_AUTH` | `20/minute` | Nein | Rate-Limit für Authentifizierungsendpunkte |
| `RATE_LIMIT_GENERAL` | `100/minute` | Nein | Rate-Limit für allgemeine API-Endpunkte |

**Format:** `[anzahl]/[einheit]` — Einheiten: `second`, `minute`, `hour`, `day`

---

## Uploads

| Variable | Standard | Pflicht | Beschreibung |
|----------|---------|---------|-------------|
| `UPLOAD_DIR` | `uploads/tasks` | Nein | Verzeichnis für Datei-Uploads (relativ zum Backend-Arbeitsverzeichnis) |

---

## Verschachtelte Konfiguration (GBIF)

GBIF-Einstellungen können über den Unterstrich-Doppelpunkt-Delimiter verschachtelt werden:

| Variable | Standard | Beschreibung |
|----------|---------|-------------|
| `GBIF__BASE_URL` | `https://api.gbif.org/v1` | GBIF-API-Basis-URL |
| `GBIF__RATE_LIMIT_PER_MINUTE` | `60` | Anfragen pro Minute an GBIF |
| `GBIF__HTTP_TIMEOUT` | `30` | Timeout für GBIF-Anfragen (Sekunden) |

---

## Vollständiges .env-Beispiel

```bash
# Datenbank
ARANGO_ROOT_PASSWORD=sicheres-root-passwort
ARANGODB_HOST=arangodb
ARANGODB_PORT=8529
ARANGODB_DATABASE=kamerplanter
ARANGODB_USERNAME=root
ARANGODB_PASSWORD=sicheres-root-passwort

# Cache / Queue
REDIS_URL=redis://valkey:6379/0

# Sicherheit
JWT_SECRET_KEY=erzeugen-mit-openssl-rand-hex-32
REQUIRE_EMAIL_VERIFICATION=false

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Betriebsmodus
KAMERPLANTER_MODE=full
DEBUG=false

# E-Mail (Entwicklung)
EMAIL_ADAPTER=console

# mDNS Discovery (LAN-only, opt-in)
# MDNS_ENABLED=false
# INSTANCE_ID=

# Optionale externe APIs
PERENUAL_API_KEY=
HA_URL=
HA_ACCESS_TOKEN=

# Knowledge Service — Re-Ranking (leer = deaktiviert)
RERANKER_URL=
RERANKER_INITIAL_K=20
RERANKER_TOP_K=5
```

---

## Häufige Fragen

??? question "Kann ich Umgebungsvariablen in Kubernetes als Secrets hinterlegen?"
    Ja. Verwenden Sie Kubernetes Secrets für sensible Werte (`ARANGODB_PASSWORD`, `JWT_SECRET_KEY`) und referenzieren Sie sie im Deployment-Manifest über `valueFrom.secretKeyRef`.

??? question "Wo kann ich prüfen, welche Werte das Backend tatsächlich verwendet?"
    Mit `DEBUG=true` loggt das Backend beim Start alle geladenen Einstellungen. Alternativ im Container:
    ```bash
    docker compose exec backend python -c "from app.config.settings import settings; print(settings.model_dump())"
    ```
    Passwörter und Secrets werden dabei nicht im Klartext angezeigt.

---

## Siehe auch

- [Lokales Setup](../development/local-setup.md)
- [Fehlerbehebung](../guides/troubleshooting.md)
- [Deployment Kubernetes](../deployment/kubernetes.md)
