# Datenschutz & DSGVO

!!! note "Teilweise verfügbar"
    Die DSGVO-Betroffenenrechte sind als **API-Self-Service unter `/api/v1/privacy/`** vollständig implementiert und produktiv nutzbar. Die **grafische Oberfläche** ist jetzt ebenfalls verfügbar — erreichbar über das Benutzermenü (Klick auf dein Profilbild oder deine Initialen) > **Datenschutz**, nur im Voll-Modus (nicht im anonymen [Light-Modus](light-mode.md)). Sie deckt die wichtigsten Klickstrecken ab: Datenexport anfordern, Konto löschen, Verarbeitungseinschränkung anlegen, Einwilligungen einsehen. Einzelne Teilschritte (z. B. Einwilligung per Klick widerrufen, E-Mail-Adresse ändern) sind aktuell nur über die API möglich — an der jeweiligen Stelle dieser Seite markiert (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)). <!-- REQ-025 -->

Kamerplanter ist nach dem Prinzip **Datenschutz durch Technikgestaltung** (Privacy by Design) entwickelt. Du hast die volle Kontrolle über deine persönlichen Daten: Du kannst sie jederzeit exportieren, berichtigen oder löschen lassen. Alle Betroffenenrechte nach DSGVO Art. 15–21 sind als Self-Service-Funktionen erreichbar.

---

## Für technische Nutzer / Self-Hoster {#fuer-technische-nutzer-self-hoster}

Dieser Abschnitt richtet sich an technische Nutzer und Self-Hoster. Alle unten beschriebenen DSGVO-Funktionen stehen als REST-Endpunkte unter `/api/v1/privacy/` zur Verfügung. Ein Teil davon ist zusätzlich direkt in der grafischen Oberfläche nutzbar (siehe die jeweiligen Abschnitte weiter unten); einige Endpunkte — E-Mail-Änderung, Widerspruch, Einwilligung per Klick erteilen/widerrufen, Einschränkung aufheben, Export-Status/-Download — sind aktuell ausschließlich über die API erreichbar. Eine angemeldete Sitzung (Bearer-Token) ist erforderlich, außer bei `GET /api/v1/privacy/policy`.

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

## Datenschutz-Einstellungen öffnen

So öffnest du den Datenschutz-Bereich:

1. Oben rechts auf dein Profilbild oder deine Initialen klicken
2. Im Menü auf **Datenschutz** klicken

Der Datenschutz-Bereich hat vier Tabs: **Einwilligungen**, **Datenexport**, **Konto löschen** und **Verarbeitungseinschränkung**.

!!! note "Nur im Voll-Modus"
    Der Menüpunkt **Datenschutz** erscheint nur im **Voll-Modus** mit registriertem Konto. Im anonymen [Light-Modus](light-mode.md) gibt es kein Benutzerkonto und damit keinen Datenschutz-Bereich.

---

## Meine Daten exportieren (Art. 15 & 20 DSGVO)

Du hast das Recht zu erfahren, welche Daten das System über dich gespeichert hat, und diese in einem maschinenlesbaren Format zu erhalten.

### Datenexport anfordern

1. Zu **Datenschutz** > Tab **Datenexport** navigieren
2. Auf **Export anfordern** klicken
3. Die Oberfläche bestätigt die Anfrage mit dem aktuellen Status

Der Export läuft danach asynchron im Hintergrund (dauert je nach Datenmenge 1–5 Minuten); der spätere Download-Link ist **72 Stunden** gültig.

!!! info "Nur über API: Status prüfen & Datei herunterladen"
    Den Fortschritt einer laufenden Export-Anfrage abzufragen und die fertige Datei herunterzuladen ist in der Oberfläche noch nicht verdrahtet — dafür aktuell nur über die API: `GET /api/v1/privacy/export/{export_key}` liefert den Status, `GET /api/v1/privacy/export/{export_key}/download` liefert die Download-Metadaten (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)).

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

Du hast das Recht, deine Daten berichtigen zu lassen.

!!! info "Nur über API: E-Mail-Adresse ändern"
    Die Kontoeinstellungen zeigen deine E-Mail-Adresse aktuell nur schreibgeschützt an — ändern lässt sie sich bislang ausschließlich über die API: `POST /api/v1/privacy/email-change` initiiert die Änderung und sendet einen **Verifikationslink an die neue Adresse**, `POST /api/v1/privacy/email-change/confirm` bestätigt sie per Token (kein Login nötig). Details siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster).

Die neue E-Mail ist nach der Bestätigung aktiv — alle aktiven Sitzungen werden beendet.

!!! note "Sicherheitshinweis"
    Nach der Bestätigung der neuen E-Mail werden alle offenen Sitzungen (Browser, App) beendet. Du musst dich neu anmelden. Deine alte E-Mail erhält eine Informations-Mail über die Änderung.

---

## Verarbeitung einschränken (Art. 18 DSGVO)

Du kannst die Verarbeitung deiner Daten für bestimmte Zwecke einschränken — zum Beispiel, wenn du die Richtigkeit deiner Daten bestreitest oder die Verarbeitung für unrechtmäßig hältst.

1. Zu **Datenschutz** > Tab **Verarbeitungseinschränkung** navigieren
2. Betroffenen Datenbereich eingeben (z. B. `sensor_data`, `harvest_records`, `treatment_records`) und Grund auswählen
3. Auf **Einschränken** klicken

Die angelegte Einschränkung erscheint danach in der Liste **Aktive Einschränkungen** auf demselben Tab. Während einer Einschränkung werden die betroffenen Daten nicht mehr aktiv verarbeitet.

!!! info "Nur über API: Einschränkung aufheben"
    Eine bestehende Einschränkung wieder aufzuheben ist in der Oberfläche noch nicht verdrahtet — dafür aktuell nur über die API: `DELETE /api/v1/privacy/restrict/{restriction_key}` (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)).

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
| **KI-Zugriff auf deine Pflanzendaten** (`ai_tenant_data_access`) | Optional | Ja |
| **KI-Verarbeitung über Cloud-Provider** (`ai_cloud_processing`) | Optional | Ja |

### Einwilligung widerrufen

Der Tab **Einwilligungen** im Datenschutz-Bereich zeigt eine Übersicht aller Verarbeitungszwecke mit deinem aktuellen Status (**Erteilt** / **Nicht erteilt**) und, bei Pflicht-Einwilligungen, der Kennzeichnung **Pflicht**.

!!! info "Nur über API: Erteilen und Widerrufen per Klick"
    Der Tab ist aktuell **nur lesend** — einen Schalter zum direkten Erteilen oder Widerrufen einer Einwilligung gibt es in der Oberfläche noch nicht. Bis dahin funktioniert das nur über die API: `POST /api/v1/privacy/consents` erteilt eine Einwilligung, `DELETE /api/v1/privacy/consents/{purpose}` widerruft sie mit Zeitstempel, ab sofort wirksam. `GET /api/v1/privacy/consents` liefert dieselben Daten, die auch der Tab anzeigt (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)).

!!! warning "Auswirkungen eines Widerrufs"
    Wenn du die Einwilligung für externe Stammdatenanreicherung widerrufst, werden keine neuen Daten mehr von GBIF oder Perenual abgerufen. Bestehende angereicherte Daten bleiben erhalten.

### Foto-Identifikation (plant_identification)

Die [Pflanzenerkennung per Foto](plant-identification.md) sendet dein Bild zur Analyse an Pl@ntNet (CIRAD/INRIA, Frankreich/EU). Die Einwilligung ist erforderlich, weil das Foto die Kamerplanter-Instanz kurzzeitig verlässt.

!!! note "Einwilligungs-Verhalten je Modus"
    **Full-Modus:** Die Einwilligung wird als Consent-Record im Backend gespeichert (Tabelle weiter unten) und bleibt über Browser und Geräte hinweg erhalten. Der Einwilligungen-Tab der Datenschutz-Oberfläche zeigt den aktuellen Status an; widerrufen lässt sie sich aktuell nur über die API: `DELETE /api/v1/privacy/consents/plant_identification` (siehe [Einwilligung widerrufen](#einwilligung-widerrufen)).

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

### KI-Zugriff auf deine Pflanzendaten (ai_tenant_data_access)

Der [KI-Assistent](ai-assistant.md) beantwortet reine Wissensfragen ohne diese Einwilligung. Sobald eine Antwort deinen konkreten Pflanzenkontext nutzen soll — beim Chat, bei künftigen Tipp-Karten, dem Tipp des Tages und den „Warum?"-Erklärungen — ist diese Einwilligung erforderlich.

Übermittelt werden ausschließlich Stammwerte: wissenschaftlicher Pflanzenname, aktuelle Phase, Substrat, EC-/pH-Messwerte sowie aggregierte Kennzahlen (z. B. „3 überfällige Aufgaben"). Dein Name, deine E-Mail-Adresse und Freitext aus deinem Pflanztagebuch werden **nie** übermittelt.

!!! note "Widerruf"
    Nach einem Widerruf werden Tipp-Karten ausgeblendet, „Warum?"-Buttons unsichtbar und der Chat verweigert neue Nachrichten. Bereits geführte Chat-Verläufe bleiben sichtbar.

### KI-Verarbeitung über Cloud-Provider (ai_cloud_processing)

Zusätzlich zur vorherigen Einwilligung erforderlich, wenn deine Instanz einen externen Cloud-Provider (z. B. Anthropic, OpenAI) statt eines lokal betriebenen Modells (Ollama) für den KI-Assistenten einsetzt — das legt der Plattformbetreiber fest. Cloud-Provider können eine Drittland-Datenübermittlung bedeuten. Lokale Provider benötigen diese Einwilligung nicht.

---

## Widerspruch einlegen (Art. 21 DSGVO)

Du kannst der Verarbeitung deiner Daten zu bestimmten Zwecken widersprechen, wenn die Verarbeitung auf berechtigtem Interesse basiert.

!!! info "Nur über API: Widerspruch einlegen"
    Für den Widerspruch gibt es aktuell keinen eigenen Bereich in der Oberfläche — er lässt sich über `POST /api/v1/privacy/object` einlegen (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)).

Das System prüft den Widerspruch. Bei Verarbeitungen auf Basis von Art. 6(1)(f) DSGVO (berechtigtes Interesse) wird die Verarbeitung eingestellt, sofern keine zwingenden legitimen Gründe vorliegen.

---

## Account löschen (Art. 17 DSGVO)

Du hast das Recht auf Löschung deiner Daten.

!!! danger "Account-Löschung ist endgültig"
    Die Löschung kann nicht rückgängig gemacht werden. Lade vorher deinen Datenexport herunter, wenn du deine Daten sichern möchtest.

### Ablauf der Löschung

1. Zu **Datenschutz** > Tab **Konto löschen** navigieren
2. Auf **Konto löschen** klicken
3. Bei Konten mit **lokalem Passwort-Login** im Bestätigungsdialog das **aktuelle Passwort** eingeben (zur Autorisierung der Löschung). Bei Konten, die ausschließlich über einen externen Anbieter (Google, GitHub, Apple …) angemeldet sind, entfällt dieser Schritt.
4. Im Bestätigungsdialog auf **Ja, Konto löschen** klicken

!!! info "Passwortbestätigung"
    Für Konten mit lokalem Passwort ist die Eingabe des aktuellen Passworts verpflichtend. Ist das Passwort falsch, bleibt der Dialog geöffnet und zeigt einen Fehlerhinweis — das Konto wird dann **nicht** gelöscht.

Der gleiche Vorgang lässt sich auch direkt über die API auslösen: `POST /api/v1/privacy/erasure` startet die Löschung (bei lokalen Konten mit dem Feld `password`), `GET /api/v1/privacy/erasure/{erasure_key}` liefert den Status (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)).

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
| Sensordaten (roh) | 90 Tage | Speicherbegrenzung |
| Sensordaten (stündlich aggregiert) | 2 Jahre | Speicherbegrenzung |
| Sensordaten (täglich aggregiert) | 5 Jahre | Speicherbegrenzung |
| IP-Adressen | 7 Tage, dann anonymisiert | Datensparsamkeit |
| Ernte-/Behandlungsdaten | Gesetzliche Mindestfrist | CanG / PflSchG |
| Einwilligungs-Log | 3 Jahre nach Widerruf | Nachweispflicht |
| Löschungs-Audit-Log | 1 Jahr | Nachweispflicht |
| KI-Chatverläufe | 90 Tage | Speicherbegrenzung — täglicher Cleanup |
| KI-Tipp-Karten (Cache) | 7 Tage | Speicherbegrenzung |
| KI-Aufruf-Protokoll (gehasht, kein Klartext) | 30 Tage | Speicherbegrenzung — täglicher Cleanup |

<!-- NFR-011 -->

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
    Je nach Datenmenge dauert der Export 1–5 Minuten. Den Status prüfst und die fertige Datei lädst du aktuell über die API ab (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)). Der Download-Link ist 72 Stunden gültig.

??? question "Kann ich einzelne Pflanzendaten löschen, ohne den Account zu löschen?"
    Ja. Du kannst einzelne Pflanzen, Standorte und Aufgaben jederzeit löschen. Die Account-Löschung ist nur nötig, wenn du alle deine Daten auf einmal entfernen möchtest.

??? question "Was passiert mit meinen Daten, wenn der Dienst eingestellt wird?"
    Du wirst mindestens 30 Tage vorher informiert und hast die Möglichkeit, alle deine Daten zu exportieren. Nach Abschaltung werden alle personenbezogenen Daten innerhalb von 90 Tagen gelöscht.

---

## Siehe auch

- [Konto & Anmeldung](account.md)
- [Mandanten & Gärten](tenants.md)
- [KI-Assistent](ai-assistant.md)
