# Datenschutz & DSGVO

!!! note "Teilweise verfügbar"
    Die DSGVO-Betroffenenrechte (intern verfolgt als REQ-025) sind als **API-Self-Service unter `/api/v1/privacy/`** vollständig implementiert und produktiv nutzbar. Die **grafische Oberfläche** ("Konto-Einstellungen > Datenschutz") folgt noch — die auf dieser Seite beschriebenen Klickstrecken sind daher im Futur formuliert und beschreiben das geplante UI-Verhalten. Bis die Oberfläche verfügbar ist, lassen sich alle Funktionen bereits heute direkt über die API nutzen (siehe [Zugriff über die API](#fur-technische-nutzer-zugriff-uber-die-api-schon-heute-nutzbar)).

Kamerplanter ist nach dem Prinzip **Datenschutz durch Technikgestaltung** (Privacy by Design) entwickelt. Du hast die volle Kontrolle über deine persönlichen Daten: Du kannst sie jederzeit exportieren, berichtigen oder löschen lassen. Alle Betroffenenrechte nach DSGVO Art. 15–21 sind als Self-Service-Funktionen erreichbar.

---

## Für technische Nutzer: Zugriff über die API (schon heute nutzbar)

Dieser Abschnitt richtet sich an technische Nutzer und Self-Hoster. Alle unten beschriebenen Funktionen stehen bereits als REST-Endpunkte unter `/api/v1/privacy/` zur Verfügung. Eine angemeldete Sitzung (Bearer-Token) ist erforderlich, außer bei `GET /api/v1/privacy/policy`.

!!! info "Nur über API / Betreiber-Konfiguration"
    Am einfachsten lassen sich die Endpunkte über die interaktive API-Dokumentation unter `/docs` (OpenAPI/Swagger) ausprobieren — dort können Anfragen direkt im Browser ausgeführt werden. Alternativ per `curl`, z.B. für den Datenexport:
    ```bash
    curl -X POST https://<deine-instanz>/api/v1/privacy/export \
      -H "Authorization: Bearer <dein-access-token>"
    ```

| Endpunkt | Zweck |
|----------|-------|
| `POST /api/v1/privacy/export` | Datenexport anfordern (Art. 15/20) |
| `GET /api/v1/privacy/export/{export_key}` | Export-Status abfragen |
| `GET /api/v1/privacy/export/{export_key}/download` | Export herunterladen |
| `POST /api/v1/privacy/email-change` | E-Mail-Änderung anfordern (Art. 16) |
| `POST /api/v1/privacy/email-change/confirm` | E-Mail-Änderung per Token bestätigen |
| `POST /api/v1/privacy/erasure` | Account-Löschung anfordern (Art. 17) |
| `GET /api/v1/privacy/erasure/{erasure_key}` | Löschstatus abfragen |
| `POST /api/v1/privacy/restrict` | Verarbeitung einschränken (Art. 18) |
| `DELETE /api/v1/privacy/restrict/{restriction_key}` | Einschränkung aufheben |
| `POST /api/v1/privacy/object` | Widerspruch einlegen (Art. 21) |
| `GET /api/v1/privacy/consents` | Einwilligungen auflisten (Art. 7) |
| `POST /api/v1/privacy/consents` | Einwilligung erteilen |
| `DELETE /api/v1/privacy/consents/{purpose}` | Einwilligung widerrufen |
| `GET /api/v1/privacy/policy` | Datenschutzerklärung abrufen (kein Login nötig) |

---

## Datenschutz-Einstellungen öffnen (geplante Oberfläche)

Sobald die Oberfläche verfügbar ist, wird sich der Datenschutz-Bereich so öffnen lassen:

1. Oben rechts auf das Profilbild oder die Initialen klicken
2. **Konto-Einstellungen** wählen
3. Auf den Tab **Datenschutz** klicken

Der Datenschutz-Bereich wird vier Tabs haben: **Meine Daten**, **Einwilligungen**, **Verarbeitung einschränken** und **Account löschen**.

---

## Meine Daten exportieren (Art. 15 & 20 DSGVO)

Du hast das Recht zu erfahren, welche Daten das System über dich gespeichert hat, und diese in einem maschinenlesbaren Format zu erhalten.

### Datenexport anfordern

Sobald die Oberfläche verfügbar ist:

1. Zu **Datenschutz** > **Meine Daten** navigieren
2. Auf **Daten exportieren** klicken
3. Das System erstellt den Export asynchron (dauert je nach Datenmenge 1–5 Minuten)
4. Eine Benachrichtigung (In-App oder E-Mail) informiert, wenn der Export bereit ist
5. Die JSON-Datei herunterladen — der Link ist **72 Stunden** gültig

Schon heute per API: `POST /api/v1/privacy/export` startet den Export, `GET /api/v1/privacy/export/{export_key}` liefert den Status, `GET /api/v1/privacy/export/{export_key}/download` liefert die Download-Metadaten.

Der Export enthält alle Daten, die dem System über dich bekannt sind:
- Profildaten (Name, E-Mail, Einstellungen)
- Alle angelegten Pflanzen, Standorte, Aufgaben und Ernten
- Pflegeerinnerungen und Bestätigungshistorie
- Sensordaten (wenn du welche hast)
- Einwilligungshistorie

!!! tip "Datenportabilität"
    Die JSON-Export-Datei entspricht DSGVO Art. 20 (Datenportabilität). Du kannst sie nutzen, um deine Daten in ein anderes System zu übertragen.

---

## E-Mail-Adresse ändern (Art. 16 DSGVO)

Du hast das Recht, deine Daten zu berichtigen.

Sobald die Oberfläche verfügbar ist:

1. Zu **Datenschutz** > **Meine Daten** > **E-Mail ändern** navigieren
2. Die neue E-Mail-Adresse eingeben
3. Das System sendet einen **Verifikationslink an die neue Adresse**
4. Auf den Link in der E-Mail klicken
5. Die neue E-Mail ist danach aktiv — alle aktiven Sitzungen werden beendet

Schon heute per API: `POST /api/v1/privacy/email-change` initiiert die Änderung, `POST /api/v1/privacy/email-change/confirm` bestätigt sie per Token (kein Login nötig).

!!! note "Sicherheitshinweis"
    Nach der Bestätigung der neuen E-Mail werden alle offenen Sitzungen (Browser, App) beendet. Du musst dich neu anmelden. Deine alte E-Mail erhält eine Informations-Mail über die Änderung.

---

## Verarbeitung einschränken (Art. 18 DSGVO)

Du kannst die Verarbeitung deiner Daten für bestimmte Zwecke einschränken — zum Beispiel, wenn du die Richtigkeit deiner Daten bestreitest oder die Verarbeitung für unrechtmäßig hältst.

Sobald die Oberfläche verfügbar ist:

1. Zu **Datenschutz** > **Verarbeitung einschränken** navigieren
2. Den Verarbeitungszweck aus der Liste wählen
3. Auf **Einschränken** klicken

Während einer Einschränkung werden die betroffenen Daten nicht mehr aktiv verarbeitet. Die Einschränkung kann jederzeit aufgehoben werden.

Schon heute per API: `POST /api/v1/privacy/restrict` legt eine Einschränkung an, `DELETE /api/v1/privacy/restrict/{restriction_key}` hebt sie wieder auf.

---

## Einwilligungen verwalten (Art. 7 DSGVO)

Für die Grundfunktionen des Systems ist keine optionale Einwilligung nötig. Einige Zusatzfunktionen erfordern jedoch deine Zustimmung.

### Einwilligungsarten

| Zweck | Typ | Widerrufbar |
|-------|-----|:-----------:|
| **Grundfunktionen** (Pflanzenverwaltung, Erinnerungen) | Pflicht | Nein |
| **Fehler-Tracking (Sentry)** | Optional | Ja |
| **HaveIBeenPwned Passwort-Check** | Optional | Ja |
| **Externe Stammdatenanreicherung** (GBIF, Perenual) | Optional | Ja |
| **Foto-Identifikation** (Pl@ntNet) | Optional | Ja |
| **Cloud-basierte Schädlingserkennung** (Kindwise plant.health) | Optional | Ja |
| **Foto-Beitrag zur Pflanzenerkennung** (eigene Referenzfotos) | Optional | Ja |

### Einwilligung widerrufen

Sobald die Oberfläche verfügbar ist:

1. Zu **Datenschutz** > **Einwilligungen** navigieren
2. Alle erteilten Einwilligungen mit Datum ansehen
3. Neben der optionalen Einwilligung auf **Widerrufen** klicken
4. Der Widerruf wird mit Zeitstempel gespeichert und gilt ab sofort

Schon heute per API: `GET /api/v1/privacy/consents` listet alle Zwecke mit aktuellem Status, `POST /api/v1/privacy/consents` erteilt eine Einwilligung, `DELETE /api/v1/privacy/consents/{purpose}` widerruft sie.

!!! warning "Auswirkungen eines Widerrufs"
    Wenn du die Einwilligung für externe Stammdatenanreicherung widerrufst, werden keine neuen Daten mehr von GBIF oder Perenual abgerufen. Bestehende angereicherte Daten bleiben erhalten.

### Foto-Identifikation (plant_identification)

Die [Pflanzenerkennung per Foto](plant-identification.md) sendet dein Bild zur Analyse an Pl@ntNet (CIRAD/INRIA, Frankreich/EU). Die Einwilligung ist erforderlich, weil das Foto die Kamerplanter-Instanz kurzzeitig verlässt.

!!! note "Einwilligungs-Verhalten je Modus"
    **Full-Modus:** Die Einwilligung wird als Consent-Record im Backend gespeichert (Tabelle weiter unten) und bleibt über Browser und Geräte hinweg erhalten. Widerrufbar ist sie schon heute über `DELETE /api/v1/privacy/consents/plant_identification`; sobald die Datenschutz-Oberfläche verfügbar ist, wird das auch dort möglich sein.

    **Light-Modus:** Das Consent-Subsystem steht im [Light-Modus](light-mode.md) nicht zur Verfügung. Die Einwilligung wird stattdessen **clientseitig im Browser** (localStorage) eingeholt und gespeichert. Der Einwilligungs-Dialog erscheint beim ersten Upload in der jeweiligen Browser-Sitzung. Dieselben Transparenzinformationen (Foto geht an Pl@ntNet/Frankreich, EXIF-Daten werden entfernt, keine dauerhafte Speicherung) werden in beiden Modi angezeigt.

**Was beim Widerruf passiert:**

- Alle Kamera-Schaltflächen werden sofort ausgeblendet
- Neue Foto-Anfragen werden mit HTTP 403 abgelehnt (Full-Modus) bzw. im Browser blockiert (Light-Modus)
- Dein Identifikations-Verlauf bleibt erhalten (er enthält keine Fotos, nur Ergebnisse)
- Die Einwilligung kann jederzeit erneut erteilt werden

**Datenfluss bei aktiver Einwilligung:**

| Datum | Speicherort | Aufbewahrung |
|-------|------------|-------------|
| Bilddaten | Nur im Arbeitsspeicher während des API-Aufrufs | Keine dauerhafte Speicherung |
| Bild-Prüfwert (SHA-256-Hash) | `identification_requests`-Collection | 90 Tage, dann automatisch gelöscht |
| Erkennungsergebnis (Artvorschläge) | `identification_requests`-Collection | 90 Tage, dann automatisch gelöscht |
| Ausgewählte Art | Verknüpfung mit der angelegten Pflanze | Lebenszeit der Pflanze |

Vor der Übertragung an Pl@ntNet werden alle EXIF-Metadaten entfernt (GPS-Koordinaten, Kameramodell, Aufnahmezeitpunkt).

### Cloud-basierte Schädlingserkennung (pest_detection_cloud)

Die [Schädlingserkennung per Foto](pest-detection.md) sendet dein Bild — je nach Betreiber-Konfiguration — entweder an eine self-hosted Erkennung (keine Einwilligung nötig) oder an den Cloud-Dienst Kindwise plant.health. Diese Einwilligung ist nur erforderlich, wenn der Cloud-Adapter aktiv ist. Wie bei der Pflanzenidentifikation wird das Foto vor dem Versand von EXIF-Metadaten bereinigt und nicht dauerhaft gespeichert.

---

## Widerspruch einlegen (Art. 21 DSGVO)

Du kannst der Verarbeitung deiner Daten zu bestimmten Zwecken widersprechen, wenn die Verarbeitung auf berechtigtem Interesse basiert.

Sobald die Oberfläche verfügbar ist:

1. Zu **Datenschutz** > **Verarbeitung einschränken** navigieren
2. Den Verarbeitungszweck wählen
3. Auf **Widerspruch einlegen** klicken

Das System prüft den Widerspruch. Bei Verarbeitungen auf Basis von Art. 6(1)(f) DSGVO (berechtigtes Interesse) wird die Verarbeitung eingestellt, sofern keine zwingenden legitimen Gründe vorliegen.

Schon heute per API: `POST /api/v1/privacy/object`.

---

## Account löschen (Art. 17 DSGVO)

Du hast das Recht auf Löschung deiner Daten.

!!! danger "Account-Löschung ist endgültig"
    Die Löschung kann nicht rückgängig gemacht werden. Lade vorher deinen Datenexport herunter, wenn du deine Daten sichern möchtest.

### Ablauf der Löschung

Sobald die Oberfläche verfügbar ist:

1. Zu **Datenschutz** > **Account löschen** navigieren
2. Mit Passwort bestätigen (oder OAuth Re-Authentifizierung)
3. Auf **Account endgültig löschen** klicken

Schon heute per API: `POST /api/v1/privacy/erasure` (Passwort im Request-Body) startet die Löschung, `GET /api/v1/privacy/erasure/{erasure_key}` liefert den Status.

Was dann passiert:

```
Sofort:
- Soft-Delete des Accounts (status: deleted)
- Alle aktiven Sitzungen werden beendet
- Du kannst dich nicht mehr anmelden

Persoenliche Daten (Art. 17 DSGVO):
- Werden sofort anonymisiert oder nach 90 Tagen geloescht

Gesetzlich geschuetzte Daten (Art. 17 Abs. 3 lit. b):
- Ernte-Dokumentation und IPM-Behandlungsnachweise:
  Werden anonymisiert (Nutzer-Referenz entfernt),
  die Daten selbst bleiben erhalten (CanG, PflSchG)

Nach 90 Tagen:
- Hard-Delete aller verbleibenden persoenlichen Daten
```

!!! note "Warum werden Erntedaten nicht vollständig gelöscht?"
    Das Cannabisgesetz (CanG) und das Pflanzenschutzmittelgesetz (PflSchG) schreiben vor, dass Ernte- und Behandlungsdaten für Prüf- und Nachweiszwecke aufbewahrt werden müssen. Dein Name und deine Kontaktdaten werden entfernt, die Mengen- und Behandlungsdaten bleiben als anonymisierte Einträge erhalten. Dies ist rechtlich durch Art. 17 Abs. 3 lit. b DSGVO gedeckt.

---

## Fotos und Anhänge (Object Storage)

Kamerplanter speichert Fotos und Dateien über einen Storage-Adapter, der vom Plattformbetreiber konfiguriert wird. Als Nutzer ist für dich relevant:

### EXIF-Daten

Beim Upload von Fotos entfernt das Backend standardmäßig alle EXIF-Metadaten, bevor die Datei im Storage abgelegt wird. Das umfasst:

- GPS-Koordinaten (Aufnahmeort)
- Kameramodell und Seriennummer
- Aufnahmezeitpunkt (aus dem EXIF-Header)

Der Betreiber kann die EXIF-Beibehaltung pro Kategorie aktivieren — in diesem Fall wird darauf in den Datenschutzhinweisen der Instanz hingewiesen.

### Fotos und Nutzerlöschung (Account löschen)

Wenn du deinen Account löschst, unterscheidet das System zwischen zwei Foto-Typen:

| Foto-Typ | Was passiert |
|----------|-------------|
| **Persönliche Fotos** (Profilbild, private Notizen) | Hart gelöscht — sowohl die Datei im Storage als auch der Metadateneintrag werden entfernt |
| **Dokumentierende Fotos** (Tagebucheinträge, IPM-Inspektionen, Erntefotos, Pflanzenfotos) | Bleiben erhalten, werden aber von deinem Account entkoppelt — `erstellt von` wird auf `_anonymized` gesetzt. Sind EXIF-Daten vorhanden, werden sie in diesem Schritt ebenfalls entfernt. |

Die Dateien verbleiben, weil sie zum Pflanzendatensatz gehören und ggf. gesetzlichen Aufbewahrungspflichten (CanG, PflSchG) unterliegen. Dein Name ist nach der Anonymisierung nicht mehr mit den Fotos verknüpft.

!!! note "Reihenfolge der Löschung"
    Die Storage-Bereinigung (Schritt 0) erfolgt vor der Datenbankbereinigung. Nur so kann das System die Metadaten noch abrufen, die für die Zuordnung Datei ↔ Nutzer nötig sind.

### Mandantenlöschung

Wenn ein Mandant gelöscht wird (durch den Platform-Admin oder auf Anfrage), werden alle Binärdaten des Mandanten vollständig aus dem Storage entfernt — unabhängig vom verwendeten Backend (local-fs oder S3). Das geschieht durch Löschen aller Objekte mit dem Präfix `t/{tenant_key}/`. Das Ergebnis wird im Audit-Log dokumentiert.

### Datenportabilität (Art. 20 DSGVO)

Dein Datenexport enthält alle gespeicherten Anhänge als ZIP-Archiv. Das Archiv enthält:

- Alle Dateien in der relativen Ordnerstruktur des Storage-Schemas
- Ein `manifest.json` mit Zuordnung `attachment_id → Dateipfad → Metadaten`

---

## Datenspeicherung und Aufbewahrungsfristen

Kamerplanter speichert verschiedene Datenkategorien mit unterschiedlichen Aufbewahrungsfristen:

| Datenkategorie | Aufbewahrungsfrist | Begründung |
|----------------|-------------------|-------------|
| Persönliche Profildaten | Bis zur Löschung + 90 Tage | DSGVO |
| Sensordaten (roh) | 90 Tage | NFR-011 |
| Sensordaten (stündlich aggregiert) | 2 Jahre | NFR-011 |
| Sensordaten (täglich aggregiert) | 5 Jahre | NFR-011 |
| IP-Adressen | 7 Tage, dann anonymisiert | Datensparsamkeit |
| Ernte-/Behandlungsdaten | Gesetzliche Mindestfrist | CanG / PflSchG |
| Einwilligungs-Log | 3 Jahre nach Widerruf | Nachweispflicht |
| Löschungs-Audit-Log | 1 Jahr | Nachweispflicht |

### Sensor-Daten-Downsampling

Sensordaten werden automatisch in Stufen verdichtet:

```
0–90 Tage:     Rohdaten (jeder Messwert)
90 Tage–2 Jahre: Stündliche Aggregate (Min/Max/Avg)
2–5 Jahre:     Täglich Aggregate (Min/Max/Avg)
Nach 5 Jahren: Automatische Löschung
```

!!! info "Warum Downsampling?"
    Rohe Sensordaten können sehr viel Speicherplatz beanspruchen. Nach 90 Tagen sind Minutenwerte für die meisten Auswertungen nicht mehr relevant. Das Downsampling reduziert den Speicherverbrauch erheblich, ohne wichtige Langzeittrends zu verlieren.

---

## IP-Anonymisierung

IP-Adressen werden grundsätzlich nur für 7 Tage im Klartext gespeichert. Danach werden sie auf das /24-Subnetz anonymisiert (die letzten 8 Bits auf 0 gesetzt), sodass keine individuelle Zuordnung mehr möglich ist.

---

## Sensor-Daten und Privatsphäre (DSFA)

Bestimmte Sensor-Daten können Rückschlüsse auf Anwesenheitsmuster erlauben (CO₂-Konzentration, Bewegungsmelder, manuelle Übersteuerungen). Für solche Daten wurde eine **Datenschutz-Folgenabschätzung (DSFA)** durchgeführt. Die wesentlichen Maßnahmen:

- Sensordaten sind grundsätzlich **nicht** mit anderen Tenants oder Dritten geteilt
- Der Plattformbetreiber kann Sensordaten nur nach expliziter Support-Anfrage und mit deiner Zustimmung einsehen
- Aggregierte Statistiken (ohne Personenbezug) können zur Systemverbesserung genutzt werden — dies kannst du in den Einwilligungen deaktivieren

---

## Häufige Fragen

??? question "Werden meine Pflanzendaten für kommerzielle Zwecke genutzt?"
    Nein. Deine Pflanzendaten werden nicht an Dritte weitergegeben oder für kommerzielle Zwecke genutzt. Die Datenschutzerklärung regelt dies verbindlich.

??? question "Wie lange dauert ein Datenexport?"
    Je nach Datenmenge dauert der Export 1–5 Minuten. Du erhältst eine Benachrichtigung, wenn er abgeschlossen ist. Der Download-Link ist 72 Stunden gültig.

??? question "Kann ich einzelne Pflanzendaten löschen, ohne den Account zu löschen?"
    Ja. Du kannst einzelne Pflanzen, Standorte und Aufgaben jederzeit löschen. Die Account-Löschung ist nur nötig, wenn du alle deine Daten auf einmal entfernen möchtest.

??? question "Was passiert mit meinen Daten, wenn der Dienst eingestellt wird?"
    Du wirst mindestens 30 Tage vorher informiert und hast die Möglichkeit, alle deine Daten zu exportieren. Nach Abschaltung werden alle personenbezogenen Daten innerhalb von 90 Tagen gelöscht.

---

## Siehe auch

- [Konto-Einstellungen](../api/authentication.md)
- [Mandanten & Gärten](tenants.md)
