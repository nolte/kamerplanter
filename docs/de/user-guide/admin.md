# Plattform-Admin-Bereich

Der Plattform-Admin-Bereich ist ausschließlich für Nutzer mit der Plattform-Rolle **admin** zugänglich. Er ermöglicht die plattformweite Verwaltung aller Mandanten und Nutzer — unabhängig von der mandantengebundenen Tenant-Admin-Rolle.

---

## Voraussetzungen

- Plattform-Rolle **admin** (unterscheidet sich von der Tenant-Admin-Rolle)
- Zugang über `/admin/platform` (im Full-Modus)

!!! warning "Nicht mit Tenant-Admin verwechseln"
    Die Plattform-Admin-Rolle ist eine **plattformweite** Sonderrolle, die zum Zugriff auf Daten aller Mandanten berechtigt. Die Tenant-Admin-Rolle dagegen ist auf einen einzelnen Mandanten beschränkt und wird über **Einstellungen > Mandanten > Mitglieder** vergeben.

---

## Abgrenzung: Plattform-Admin vs. Tenant-Admin

| Funktion | Plattform-Admin | Tenant-Admin |
|---------|----------------|-------------|
| Alle Mandanten verwalten | Ja | Nein |
| Nutzerverwaltung plattformweit | Ja | Nein |
| Mandantenstatistiken einsehen | Ja | Nein |
| OIDC-Provider konfigurieren | Ja | Nein |
| Mitglieder des eigenen Mandanten verwalten | Ja | Ja |
| Standorte und Pflanzdaten des Mandanten | Ja | Ja |

---

## Mandantenverwaltung

Im Bereich **Admin > Mandanten** kannst du:

- Alle Mandanten der Plattform einsehen (Name, Slug, Mitgliederzahl, Erstellungsdatum)
- Einzelne Mandanten deaktivieren oder löschen
- Mandanten-Kontingente und Limits einsehen
- Mitglieder eines Mandanten stellvertretend verwalten

!!! danger "Mandanten löschen ist irreversibel"
    Das Löschen eines Mandanten entfernt alle zugehörigen Daten (Pflanzen, Durchläufe, Protokolle). Diese Aktion kann nicht rückgängig gemacht werden. Erstelle vorher einen Daten-Export für den betroffenen Mandanten.

---

## Nutzerverwaltung

Im Bereich **Admin > Nutzer** kannst du:

- Alle Nutzerkonten der Plattform einsehen
- Nutzerkonten sperren oder deaktivieren
- Plattform-Rollen zuweisen (`admin`, `viewer`)
- Passwort-Reset für Nutzer auslösen
- DSGVO-Anfragen (Datenlöschung, Datenauskunft) bearbeiten

!!! note "DSGVO-Anfragen"
    Betroffenenrechte nach Art. 15–21 DSGVO stehen Nutzern über die Self-Service-API unter `/api/v1/privacy/` zur Verfügung. Als Platform-Admin kannst du Anfragen im Admin-Bereich einsehen und bearbeiten. Weitere Informationen: [Datenschutz (DSGVO)](privacy.md).

---

## Statistiken

Der Bereich **Admin > Statistiken** bietet eine Übersicht über:

- Anzahl aktiver Mandanten und Nutzer
- Aktive Pflanzdurchläufe plattformweit
- Celery-Task-Queue-Status
- Speicherverbrauch (ArangoDB, TimescaleDB, Redis)

---

## OIDC-Provider

Unter **Admin > OIDC-Provider** konfigurierst du föderierte Authentifizierungs-Provider (z.B. Google, GitHub, firmeneigene OIDC-Instanzen). Diese Einstellungen gelten plattformweit für alle Mandanten.

Mehr dazu: [Authentifizierung](../api/authentication.md).

---

## Pflanzenerkennung per Foto aktivieren

Die [Foto-Identifikation](plant-identification.md) ist ein optionales Feature, das API-Zugangsdaten eines Drittanbieters erfordert. Solange kein Key konfiguriert ist, meldet das Backend `available: false` und die gesamte Kamera-/Upload-UI bleibt für alle Nutzer ausgeblendet.

Der Pl@ntNet-API-Key ist eine **instanzweite Einstellung** — ein einziger Key gilt für alle Nutzer der Instanz. Der Free-Tier erlaubt 500 Identifikationen pro Tag für die gesamte Instanz.

!!! note "Plattform-Admin erforderlich"
    Nur Nutzer mit der Plattform-Rolle **admin** können den API-Key verwalten. Die Einstellung gilt plattformweit.

### Schritt 1: Kostenlosen Pl@ntNet-Key besorgen

1. Öffne [my.plantnet.org](https://my.plantnet.org) in einem Browser
2. Erstelle ein Konto oder melde dich an
3. Navigiere zu **Account** > **API key**
4. Kopiere den angezeigten API-Key

!!! warning "Nur für nicht-kommerzielle Nutzung"
    Der Pl@ntNet Free-Tier ist ausdrücklich für nicht-kommerzielle Nutzung lizenziert. Für kommerzielle Instanzen die Nutzungsbedingungen auf [my.plantnet.org](https://my.plantnet.org) prüfen.

### Schritt 2: Key über die Admin-UI eintragen (empfohlen)

Dies ist der **bevorzugte Weg** — kein Pod-Neustart, keine Datei-Änderung, wirkt sofort.

1. Melde dich als Plattform-Admin an
2. Öffne **Konto-Einstellungen** (oben rechts auf dein Profilbild klicken)
3. Wähle den Tab **Integrationen**
4. Scrolle zum Abschnitt **Pflanzenerkennung**
5. Gib den kopierten API-Key in das Feld **Pl@ntNet API-Key** ein
6. Klicke auf **Speichern**

Der Key wird maskiert gespeichert (nie im Klartext in Antworten oder Logs sichtbar). Das Feld zeigt an, ob der Key aus der Datenbank (UI-Eintrag), aus einer Umgebungsvariable oder gar nicht gesetzt ist.

**Optional: Key sofort prüfen**

Nach dem Speichern kannst du auf **Verbindung prüfen** klicken. Das Backend sendet eine Testanfrage an Pl@ntNet und meldet, ob der Key gültig ist und wie viele Anfragen heute noch verfügbar sind.

**Optional: Key entfernen**

Klicke auf **Entfernen**, um den in der Datenbank gespeicherten Key zu löschen. Ist keine Umgebungsvariable gesetzt, wird die Foto-Identifikation damit deaktiviert.

---

### Alternative: Key als Umgebungsvariable setzen

Die Umgebungsvariable `PLANTNET_API_KEY` bleibt weiterhin gültig — sie eignet sich für automatisierte Deployments, GitOps-Workflows oder wenn kein UI-Zugang genutzt werden soll.

!!! warning "Priorität: UI-Wert hat Vorrang"
    Ist in der Datenbank ein Key über die Admin-UI gespeichert, **überschreibt dieser den Wert der Umgebungsvariable** `PLANTNET_API_KEY`. Ein per UI gesetzter Key wirkt sofort ohne Pod-Neustart. Die Umgebungsvariable greift nur, wenn kein DB-Eintrag vorhanden ist.

=== "Produktion / Kubernetes"

    Lege einen Kubernetes-Secret an und lade ihn per `envFrom` ins Backend. **Niemals** den Key im Klartext in `values.yaml` committen.

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PLANTNET_API_KEY="dein-api-key" \
      --namespace kamerplanter
    ```

    Im Helm-Values referenzieren:

    ```yaml
    # helm/kamerplanter/values.yaml (Auszug)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

    Nach dem nächsten Rollout liest das Backend den Key automatisch aus der Secret-Umgebungsvariable.

=== "Lokales Dev (kind / Skaffold)"

    Für schnelle Tests ohne Kubernetes-Secret: die Variable direkt in den `env:`-Block des Backend-Containers in `helm/kamerplanter/values.yaml` eintragen. **Nicht committen.**

    ```yaml
    # helm/kamerplanter/values.yaml (lokal, nicht committen)
    backend:
      env:
        PLANTNET_API_KEY: "dein-api-key"
    ```

    Skaffold deployt die Änderung automatisch neu.

=== "Docker Compose"

    Trage den Key in die `.env`-Datei im Repository-Wurzelverzeichnis ein:

    ```bash
    # .env (nicht committen)
    PLANTNET_API_KEY=dein-api-key
    ```

    Starte den Stack neu:

    ```bash
    docker compose up -d
    ```

### Schritt 3: Aktivierung per API prüfen

Rufe den Status-Endpunkt auf:

```bash
curl -s http://localhost:8000/api/v1/recognition/status | python3 -m json.tool
```

Erwartete Antwort, wenn der Key korrekt gesetzt ist:

```json
{
  "available": true,
  "adapter": "plantnet",
  "daily_limit": 500,
  "remaining_today": 498
}
```

Nach erfolgreicher Konfiguration erscheinen in der UI automatisch die Kamera-/Upload-Funktion und die Schaltfläche **Per Foto hinzufügen** in der Artenübersicht. Nutzer sehen beim ersten Aufruf den Einwilligungs-Dialog — die Funktion ist ab diesem Moment vollständig nutzbar.

### Optionale Feineinstellung

Die folgenden Variablen müssen in der Regel nicht geändert werden. Sie sind mit sinnvollen Standardwerten vorbelegt. Eine vollständige Beschreibung findet sich in der [Umgebungsvariablen-Referenz](../reference/environment-variables.md#foto-identifikation-req-029):

| Variable | Standard | Zweck |
|----------|---------|-------|
| `IDENTIFICATION_PRIMARY_ADAPTER` | `plantnet` | Bevorzugter Adapter (erweiterbar) |
| `IDENTIFICATION_CONFIDENCE_AUTO_ACCEPT` | `0.85` | Schwelle für „sehr sicher"-Hervorhebung |
| `IDENTIFICATION_CONFIDENCE_MIN_SHOW` | `0.10` | Mindest-Übereinstimmung für Anzeige |
| `IDENTIFICATION_MAX_IMAGE_SIZE_MB` | `10` | Maximale Bildgröße in Megabyte |
| `IDENTIFICATION_RATE_LIMIT_PER_USER_DAY` | `0` | Max. Anfragen pro Nutzer/Tag (`0` = Adapter-Limit) |

### Datenschutz-Hinweis

Fotos werden **nicht** auf dem Kamerplanter-Server gespeichert — sie werden ausschließlich zur Analyse an Pl@ntNet (CIRAD/INRIA, Frankreich/EU) übertragen und danach verworfen. EXIF-Metadaten (GPS, Kameramodell) werden vor der Übertragung entfernt. Jeder Nutzer muss einmalig der Bildübertragung zustimmen. Weitere Details: [Datenschutz (DSGVO) — Foto-Identifikation](privacy.md#foto-identifikation-plant_identification).

---

## Schädlingserkennung aktivieren {#schaedlingserkennung-aktivieren}

Die [Schädlingserkennung](pest-detection.md) ist standardmäßig deaktiviert (`PEST_DETECTION_ENABLED=false`). Solange kein Adapter konfiguriert ist, meldet das Backend `adapter: null` und der Button „Auf Schädlinge prüfen" bleibt für alle Nutzer ausgeblendet.

!!! note "Plattform-Admin erforderlich"
    Nur Nutzer mit der Plattform-Rolle **admin** können die Schädlingserkennung konfigurieren. Die Einstellungen gelten plattformweit.

!!! note "Phase 1 — Self-Hosted-First"
    In der aktuellen Phase (Phase 1) stehen zwei Adapter zur Verfügung: der lokale **Schadbild-Adapter** (`local_pest_symptom`, erfordert keine externen Dienste oder Einwilligung) und der optionale **Cloud-Adapter** (Kindwise, einwilligungspflichtig). Ein Self-Hosted-Direkt-Detektor mit ONNX ist für Phase 2 in Vorbereitung.

### Adapter 1: Lokaler Schadbild-Adapter (Self-Hosted, empfohlen)

Der lokale Adapter erkennt Schadbilder und Symptome (Gespinste, Honigtau, Saugschäden) direkt auf der Instanz — kein Drittanbieter, kein Datenschutz-Consent für Nutzer erforderlich.

**Aktivieren via Umgebungsvariable:**

```bash
PEST_DETECTION_ENABLED=true
PEST_DETECTION_SYMPTOM_ENABLED=true
PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom
```

=== "Kubernetes / Helm"

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PEST_DETECTION_ENABLED="true" \
      --from-literal=PEST_DETECTION_SYMPTOM_ENABLED="true" \
      --from-literal=PEST_DETECTION_PRIMARY_ADAPTER="local_pest_symptom" \
      --namespace kamerplanter
    ```

    Im Helm-Values referenzieren:

    ```yaml
    # helm/kamerplanter/values.yaml (Auszug)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

=== "Docker Compose"

    ```bash
    # .env (nicht committen)
    PEST_DETECTION_ENABLED=true
    PEST_DETECTION_SYMPTOM_ENABLED=true
    PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom
    ```

    Starte den Stack neu:

    ```bash
    docker compose up -d
    ```

=== "Lokales Dev (kind / Skaffold)"

    ```yaml
    # helm/kamerplanter/values.yaml (lokal, nicht committen)
    backend:
      env:
        PEST_DETECTION_ENABLED: "true"
        PEST_DETECTION_SYMPTOM_ENABLED: "true"
        PEST_DETECTION_PRIMARY_ADAPTER: "local_pest_symptom"
    ```

!!! warning "Voraussetzung: Inferenz-Service + Few-Shot-Index"
    Der lokale Schadbild-Adapter erkennt über **Few-Shot-Klassifikation mit einem frozen DINOv2-Modell** (kein separates, lizenzkritisches Modell). Damit der Button erscheint und echte Befunde liefert, sind **zwei** Schritte nötig:

    1. **Inferenz-Service bereitstellen** (derselbe Dienst wie für die Pflanzenerkennung). Sobald er erreichbar ist, beantwortet er `GET /pest/ready`. <!-- REQ-029-A -->
    2. **Few-Shot-Index aufbauen** — einmalig pro Klasse ~30 CC0/CC-BY-Bilder von GBIF beschaffen und als Prototypen indizieren. **Keine GBIF-Zugangsdaten nötig** (öffentliche Occurrence-Suche):

        ```bash
        # im Backend-Container/-Umfeld, Inferenz-Service muss erreichbar sein
        python -m app.migrations.acquire_pest_dataset --manifest pest_reference_manifest.json
        ```

        Das Skript beschafft Bilder, filtert pro Bild auf CC0/CC-BY, indiziert die DINOv2-Prototypen im Inferenz-Service und schreibt ein **Attributions-Manifest** (CC-BY-Pflicht). Es werden **keine Bilder dauerhaft gespeichert**. Alternativ als Celery-Task `acquire_pest_dataset_task`.

    Solange der Index leer ist, meldet `/pest/detect` „keine Befunde" (kein Fehler). Der **Direkt-Detektor mit Bounding-Boxes** (Modus 1) bleibt für Phase 2 in Vorbereitung (extern blockiert: Modell-Lizenzfreigabe + Benchmark).

!!! tip "Nur Vorschau ohne Inferenz-Service"
    Zum reinen Ausprobieren der Oberfläche ohne Inferenz-Service den Demo-Adapter aktivieren: `PEST_DETECTION_ENABLED=true` + `PEST_DETECTION_DEMO_ENABLED=true`. Er liefert klar gekennzeichnete Platzhalter-Befunde — niemals für echte Entscheidungen.

### Adapter 2: Cloud-Erkennung (Kindwise — optional, einwilligungspflichtig)

Der Kindwise-Cloud-Adapter sendet Fotos zur Analyse an den Kindwise-Dienst (Brno, Tschechien — EU). Er ist standardmäßig deaktiviert und erfordert eine explizite Nutzereinwilligung (Consent-Zweck `pest_detection_cloud`).

!!! warning "Vertragsvoraussetzungen vor der Aktivierung prüfen"
    Vor der Aktivierung des Cloud-Adapters sind folgende Punkte zu klären:
    - Auftragsverarbeitungsvertrag (AVV nach Art. 28 DSGVO) mit Kindwise abschließen
    - EU-Hosting-Garantie und Datenaufbewahrungsdauer vertraglich bestätigen
    - Indoor-Eignung des `plant.health`-Produkts für die eigenen Schädlingsziel-Klassen empirisch testen
    Detaillierte Prüfpunkte: `spec/analysis/pest-detection-implementation-prep.md` §5.

**Aktivieren via Umgebungsvariablen:**

```bash
PEST_DETECTION_ENABLED=true
PEST_DETECTION_CLOUD_ENABLED=true
PEST_DETECTION_CLOUD_API_KEY=dein-kindwise-api-key
PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom   # lokal bleibt Default; Cloud als Fallback oder primär wählbar
```

Die Schaltfläche erscheint nach dem nächsten Backend-Neustart automatisch in der UI. Nutzer, die den Cloud-Adapter nutzen möchten, werden beim ersten Aufruf zur Einwilligung aufgefordert.

### Status prüfen

Rufe den Status-Endpunkt auf (tenant-scoped, JWT erforderlich):

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/t/{tenant_slug}/pests/status | python3 -m json.tool
```

Erwartete Antwort, wenn ein Adapter aktiv ist:

```json
{
  "adapter": "local_pest_symptom",
  "pest_detection_enabled": true,
  "symptom_enabled": true,
  "detector_enabled": false,
  "cloud_enabled": false
}
```

Ist `pest_detection_enabled: false` oder `adapter: null`, bleibt der Button in der UI ausgeblendet.

### Optionale Feineinstellungen

Die folgenden Variablen müssen in der Regel nicht geändert werden. Eine vollständige Beschreibung findet sich in der [Umgebungsvariablen-Referenz](../reference/environment-variables.md#schaedlingserkennung-req-044):

| Variable | Standard | Zweck |
|----------|---------|-------|
| `PEST_DETECTION_ENABLED` | `false` | Gesamtschalter — Feature ein/aus |
| `PEST_DETECTION_SYMPTOM_ENABLED` | `true` | Schadbild-Erkennung (Modus 2) ein/aus |
| `PEST_DETECTION_DETECTOR_ENABLED` | `false` | Direkt-Detektor (Modus 1, Phase 2) ein/aus |
| `PEST_DETECTION_CLOUD_ENABLED` | `false` | Cloud-Adapter ein/aus |
| `PEST_DETECTION_CLOUD_API_KEY` | — | API-Key für den Cloud-Adapter (Kindwise) |
| `PEST_DETECTION_PRIMARY_ADAPTER` | `local_pest_symptom` | Bevorzugter Adapter |
| `PEST_DETECTION_MAX_IMAGE_SIZE_MB` | `8` | Maximale Bildgröße in Megabyte |

### Datenschutz-Hinweis

- **Lokaler Adapter:** Fotos verlassen die Instanz nicht; kein Consent erforderlich; EXIF wird vor jeder Verarbeitung entfernt.
- **Cloud-Adapter:** Fotos gehen an Kindwise (EU); Nutzer müssen einmalig für den Zweck `pest_detection_cloud` einwilligen; AVV vertraglich erforderlich; EXIF zweifach gestrippt (Frontend + Backend).
- Fotos werden nie dauerhaft gespeichert — nur Erkennungsergebnis und anonymer Bild-Hash bleiben.

Weitere Details: [Datenschutz (DSGVO)](privacy.md).

---

## Referenzbilder für die Bilderkennung kuratieren

Die Self-Hosted-Bilderkennung (DINOv2) vergleicht Nutzer-Fotos mit einem gespeicherten **Referenz-Index**. Enthält dieser Index unscharfe, falsch bestimmte oder anderweitig ungeeignete Bilder, verschlechtert sich die Erkennungsgenauigkeit für die betroffene Art.

Als Platform-Admin kannst du einzelne Referenzbilder nach einem **Sichttest abwählen** — sie werden dann aus der Erkennung ausgeschlossen, bleiben aber im System erhalten (Soft-Delete, reaktivierbar). Die vollständige Anleitung einschließlich Coverage-Schwellenwert (< 5 aktive Bilder), API-Endpunkten und FAQ findest du auf der Seite:

**[Referenzbilder kuratieren](reference-image-curation.md)**

---

## Nutzer-Schädlingsbilder freigeben (Moderation)

Nutzer können in der [Schädlings-Detailseite](pest-detail.md) eigene Fotos zu einem Schädling beitragen. Diese Bilder sind zunächst **privat** (nur für den jeweiligen Garten/Mandanten sichtbar). Als Platform-Admin kannst du besonders gute Aufnahmen **global freigeben**.

Die Moderation findest du im Admin-Bereich in der Karte **„Beigesteuerte Schädlingsbilder"**:

1. Wähle den betreffenden Schädling aus.
2. Du siehst alle beigesteuerten Bilder **aller Mandanten** mit Vorschau, Herkunft (Nutzer/Mandant/Datum) und Status (privat/global).
3. Mit **Freigeben** wird ein Bild auf `global` gesetzt — es ist dann für alle Nutzer in der Galerie sichtbar (über einen globalen, schreibgeschützten Auslieferungspfad, der ausschließlich freigegebene Bilder bereitstellt). **Zurücknehmen** macht die Freigabe rückgängig (mit Bestätigung).

!!! tip "Abwählen direkt auf der Detailseite"
    Als Platform-Admin kannst du Bilder auch **direkt auf der [Schädlings-Detailseite](pest-detail.md)** kuratieren: Mit dem Schalter **„Abgewählte einblenden"** werden auch deaktivierte Bilder sichtbar, und je Bild kannst du es **abwählen** (deaktivieren statt löschen) bzw. **wieder aufnehmen**. Das gilt für Erkennungs-Referenzbilder und für beigesteuerte Bilder. Normale Nutzer sehen ausschließlich aktive Bilder. Abwählen ist reversibel; der Erkennungs-Index bleibt von einer reinen Galerie-Abwahl unberührt.

!!! note "Wirkung auf die KI-Erkennung"
    Wenn die [Schädlingserkennung](#schaedlingserkennung-aktivieren) aktiv ist (`PEST_DETECTION_ENABLED=true`), wird ein freigegebenes Bild zusätzlich als Few-Shot-Referenz (`source=user_contributed`) in den Erkennungs-Index aufgenommen — sofern der Schädling eine Erkennungsklasse (`detection_slug`) hat. Es wird nur das Embedding samt Herkunft gespeichert, **kein Originalbild**. Das Zurücknehmen deaktiviert die Referenz wieder.

!!! warning "Datenschutz"
    Beigesteuerte Bilder werden beim Löschen eines Nutzers oder Mandanten vollständig entfernt (Dokument **und** Bilddatei). Standortdaten (EXIF) werden bereits beim Hochladen entfernt.

---

## Häufige Fragen

??? question "Wer kann die Plattform-Admin-Rolle vergeben?"
    Die Plattform-Admin-Rolle kann nur von einem bestehenden Platform-Admin vergeben werden — direkt über die API oder im Admin-Bereich. Beim ersten Setup wird der erste registrierte Nutzer automatisch als Platform-Admin konfiguriert.

??? question "Kann ein Platform-Admin auch Tenant-Daten einsehen?"
    Ja. Platform-Admins haben Lesezugriff auf alle mandantengebundenen Daten. Diese Berechtigung sollte auf vertrauenswürdige Personen beschränkt und mit einem Audit-Log versehen sein. <!-- REQ-024 -->

??? question "Gibt es eine Viewer-Rolle für den Admin-Bereich?"
    Ja. Die Plattform-Rolle `viewer` bietet Lesezugriff auf alle Admin-Statistiken und Mandanten-Übersichten, jedoch keine Schreibberechtigungen.

??? question "Wo genau in der UI finde ich die Einstellung für den Pl@ntNet-Key?"
    Öffne **Konto-Einstellungen** (Klick auf dein Profilbild oben rechts) → Tab **Integrationen** → Abschnitt **Pflanzenerkennung**. Dort kannst du den Key eintragen, prüfen und entfernen. Die Einstellung ist nur für Nutzer mit der Plattform-Rolle **admin** sichtbar.

??? question "Kann ich den Key auch ohne UI als Umgebungsvariable setzen?"
    Ja. Die Umgebungsvariable `PLANTNET_API_KEY` ist weiterhin gültig und eignet sich für GitOps-Workflows oder automatisierte Deployments. Wichtig: Ein über die UI in der Datenbank gespeicherter Key hat **Vorrang** vor der Umgebungsvariable und wirkt sofort ohne Pod-Neustart.

??? question "Was passiert, wenn das Tages-Limit erschöpft ist?"
    Das Backend meldet `remaining_today: 0`. In der UI erscheint die Meldung „Tages-Limit für Bilderkennung erreicht. Morgen wieder verfügbar." Das Limit erneuert sich täglich um Mitternacht UTC. Alle anderen Funktionen bleiben uneingeschränkt verfügbar.

??? question "Kann ich einen anderen Erkennungsdienst als Pl@ntNet verwenden?"
    Aktuell ist Pl@ntNet der einzige implementierte Adapter (`IDENTIFICATION_PRIMARY_ADAPTER=plantnet`). Eine Phase-2-Erweiterung für lokale Offline-Erkennung (ohne Drittanbieter) ist geplant.

---

## Siehe auch

- [Mandanten & Gärten](tenants.md) — Mandantenverwaltung als Tenant-Admin <!-- REQ-024 -->
- [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md) — Abgrenzung Plattform-Rolle gegen Garten-Rolle
- [Datenschutz (DSGVO)](privacy.md) — Betroffenenrechte und DSGVO-Compliance
- [Authentifizierung](../api/authentication.md) — JWT, OAuth2/OIDC, Service Accounts
- [Pflanze per Foto identifizieren](plant-identification.md) — Endnutzer-Anleitung
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Variablen-Referenz
