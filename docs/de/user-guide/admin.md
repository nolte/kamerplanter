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

## Häufige Fragen

??? question "Wer kann die Plattform-Admin-Rolle vergeben?"
    Die Plattform-Admin-Rolle kann nur von einem bestehenden Platform-Admin vergeben werden — direkt über die API oder im Admin-Bereich. Beim ersten Setup wird der erste registrierte Nutzer automatisch als Platform-Admin konfiguriert.

??? question "Kann ein Platform-Admin auch Tenant-Daten einsehen?"
    Ja. Platform-Admins haben Lesezugriff auf alle mandantengebundenen Daten. Diese Berechtigung sollte auf vertrauenswürdige Personen beschränkt und mit einem Audit-Log versehen sein (REQ-024).

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

- [Mandanten & Gärten](tenants.md) — Mandantenverwaltung als Tenant-Admin (REQ-024)
- [Datenschutz (DSGVO)](privacy.md) — Betroffenenrechte und DSGVO-Compliance
- [Authentifizierung](../api/authentication.md) — JWT, OAuth2/OIDC, Service Accounts
- [Pflanze per Foto identifizieren](plant-identification.md) — Endnutzer-Anleitung
- [Umgebungsvariablen](../reference/environment-variables.md) — Vollständige Variablen-Referenz
