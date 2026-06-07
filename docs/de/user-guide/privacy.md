# Datenschutz & DSGVO

!!! warning "Noch nicht implementiert"
    Die auf dieser Seite beschriebenen DSGVO-Funktionen (REQ-025) sind **spezifiziert, aber noch nicht implementiert**. Diese Dokumentation beschreibt das geplante Verhalten.

Kamerplanter ist nach dem Prinzip **Datenschutz durch Technikgestaltung** (Privacy by Design) entwickelt. Du hast die volle Kontrolle über deine persönlichen Daten: Du kannst sie jederzeit exportieren, berichtigen oder löschen lassen. Alle Betroffenenrechte nach DSGVO Art. 15–21 sind als Self-Service-Funktionen direkt in deinem Konto erreichbar.

---

## Datenschutz-Einstellungen öffnen

1. Klicke oben rechts auf dein Profilbild oder die Initialen
2. Wähle **Konto-Einstellungen**
3. Klicke auf den Tab **Datenschutz**

Der Datenschutz-Bereich hat vier Tabs: **Meine Daten**, **Einwilligungen**, **Verarbeitung einschränken** und **Account löschen**.

---

## Meine Daten exportieren (Art. 15 & 20 DSGVO)

Du hast das Recht zu erfahren, welche Daten das System über dich gespeichert hat, und diese in einem maschinenlesbaren Format zu erhalten.

### Datenexport anfordern

1. Navigiere zu **Datenschutz** > **Meine Daten**
2. Klicke auf **Daten exportieren**
3. Das System erstellt den Export asynchron (dauert je nach Datenmenge 1–5 Minuten)
4. Du erhältst eine Benachrichtigung (In-App oder E-Mail), wenn der Export bereit ist
5. Lade die JSON-Datei herunter — der Link ist **72 Stunden** gültig

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

1. Navigiere zu **Datenschutz** > **Meine Daten** > **E-Mail ändern**
2. Gib deine neue E-Mail-Adresse ein
3. Das System sendet einen **Verifikationslink an die neue Adresse**
4. Klicke auf den Link in der E-Mail
5. Die neue E-Mail ist jetzt aktiv — alle aktiven Sitzungen werden beendet

!!! note "Sicherheitshinweis"
    Nach der Bestätigung der neuen E-Mail werden alle offenen Sitzungen (Browser, App) beendet. Du musst dich neu anmelden. Deine alte E-Mail erhält eine Informations-Mail über die Änderung.

---

## Verarbeitung einschränken (Art. 18 DSGVO)

Du kannst die Verarbeitung deiner Daten für bestimmte Zwecke einschränken — zum Beispiel wenn du die Richtigkeit deiner Daten bestreitest oder die Verarbeitung für unrechtmäßig hältst.

1. Navigiere zu **Datenschutz** > **Verarbeitung einschränken**
2. Wähle den Verarbeitungszweck aus der Liste
3. Klicke auf **Einschränken**

Während einer Einschränkung werden die betroffenen Daten nicht mehr aktiv verarbeitet. Die Einschränkung kann jederzeit aufgehoben werden.

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

### Einwilligung widerrufen

1. Navigiere zu **Datenschutz** > **Einwilligungen**
2. Du siehst alle erteilten Einwilligungen mit Datum
3. Klicke neben der optionalen Einwilligung auf **Widerrufen**
4. Der Widerruf wird mit Zeitstempel gespeichert und gilt ab sofort

!!! warning "Auswirkungen eines Widerrufs"
    Wenn du die Einwilligung für externe Stammdatenanreicherung widerrufst, werden keine neuen Daten mehr von GBIF oder Perenual abgerufen. Bestehende angereicherte Daten bleiben erhalten.

---

## Widerspruch einlegen (Art. 21 DSGVO)

Du kannst der Verarbeitung deiner Daten zu bestimmten Zwecken widersprechen, wenn die Verarbeitung auf berechtigtem Interesse basiert.

1. Navigiere zu **Datenschutz** > **Verarbeitung einschränken**
2. Wähle den Verarbeitungszweck
3. Klicke auf **Widerspruch einlegen**

Das System prüft den Widerspruch. Bei Verarbeitungen auf Basis von Art. 6(1)(f) DSGVO (berechtigtes Interesse) wird die Verarbeitung eingestellt, sofern keine zwingenden legitimen Gründe vorliegen.

---

## Account löschen (Art. 17 DSGVO)

Du hast das Recht auf Löschung deiner Daten.

!!! danger "Account-Löschung ist endgültig"
    Die Löschung kann nicht rückgängig gemacht werden. Lade vorher deinen Datenexport herunter, wenn du deine Daten sichern möchtest.

### Ablauf der Löschung

1. Navigiere zu **Datenschutz** > **Account löschen**
2. Bestätigen mit Passwort (oder OAuth Re-Authentifizierung)
3. Klicke auf **Account endgültig löschen**

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
