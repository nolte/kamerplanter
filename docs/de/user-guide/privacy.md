# Datenschutz & DSGVO

!!! warning "Noch nicht implementiert"
    Die auf dieser Seite beschriebenen DSGVO-Funktionen (REQ-025) sind **spezifiziert, aber noch nicht implementiert**. Diese Dokumentation beschreibt das geplante Verhalten.

Kamerplanter ist nach dem Prinzip **Datenschutz durch Technikgestaltung** (Privacy by Design) entwickelt. Du hast die volle Kontrolle ueber deine persoenlichen Daten: Du kannst sie jederzeit exportieren, berichtigen oder loeschen lassen. Alle Betroffenenrechte nach DSGVO Art. 15–21 sind als Self-Service-Funktionen direkt in deinem Konto erreichbar.

---

## Datenschutz-Einstellungen oeffnen

1. Klicke oben rechts auf dein Profilbild oder die Initialen
2. Waehle **Konto-Einstellungen**
3. Klicke auf den Tab **Datenschutz**

Der Datenschutz-Bereich hat vier Tabs: **Meine Daten**, **Einwilligungen**, **Verarbeitung einschraenken** und **Account loeschen**.

---

## Meine Daten exportieren (Art. 15 & 20 DSGVO)

Du hast das Recht zu erfahren, welche Daten das System ueber dich gespeichert hat, und diese in einem maschinenlesbaren Format zu erhalten.

### Datenexport anfordern

1. Navigiere zu **Datenschutz** > **Meine Daten**
2. Klicke auf **Daten exportieren**
3. Das System erstellt den Export asynchron (dauert je nach Datenmenge 1–5 Minuten)
4. Du erhaeltst eine Benachrichtigung (In-App oder E-Mail), wenn der Export bereit ist
5. Lade die JSON-Datei herunter — der Link ist **72 Stunden** gueltig

Der Export enthaelt alle Daten, die dem System ueber dich bekannt sind:
- Profildaten (Name, E-Mail, Einstellungen)
- Alle angelegten Pflanzen, Standorte, Aufgaben und Ernten
- Pflegeerinnerungen und Bestaedigungshistorie
- Sensordaten (wenn du welche hast)
- Einwilligungshistorie

!!! tip "Datenportabilitaet"
    Die JSON-Export-Datei entspricht DSGVO Art. 20 (Datenportabilitaet). Du kannst sie nutzen, um deine Daten in ein anderes System zu uebertragen.

---

## E-Mail-Adresse aendern (Art. 16 DSGVO)

Du hast das Recht, deine Daten zu berichtigen.

1. Navigiere zu **Datenschutz** > **Meine Daten** > **E-Mail aendern**
2. Gib deine neue E-Mail-Adresse ein
3. Das System sendet einen **Verifikationslink an die neue Adresse**
4. Klicke auf den Link in der E-Mail
5. Die neue E-Mail ist jetzt aktiv — alle aktiven Sitzungen werden beendet

!!! note "Sicherheitshinweis"
    Nach der Bestaeigung der neuen E-Mail werden alle offenen Sitzungen (Browser, App) beendet. Du musst dich neu anmelden. Deine alte E-Mail erhaelt eine Informations-Mail ueber die Aenderung.

---

## Verarbeitung einschraenken (Art. 18 DSGVO)

Du kannst die Verarbeitung deiner Daten fuer bestimmte Zwecke einschraenken — zum Beispiel wenn du die Richtigkeit deiner Daten bestreitest oder die Verarbeitung fuer unrechtmaessig haeltst.

1. Navigiere zu **Datenschutz** > **Verarbeitung einschraenken**
2. Waehle den Verarbeitungszweck aus der Liste
3. Klicke auf **Einschraenken**

Waehrend einer Einschraenkung werden die betroffenen Daten nicht mehr aktiv verarbeitet. Die Einschraenkung kann jederzeit aufgehoben werden.

---

## Einwilligungen verwalten (Art. 7 DSGVO)

Fuer die Grundfunktionen des Systems ist keine optionale Einwilligung noetig. Einige Zusatzfunktionen erfordern jedoch deine Zustimmung.

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
    Wenn du die Einwilligung fuer externe Stammdatenanreicherung widerrufst, werden keine neuen Daten mehr von GBIF oder Perenual abgerufen. Bestehende angereicherte Daten bleiben erhalten.

---

## Widerspruch einlegen (Art. 21 DSGVO)

Du kannst der Verarbeitung deiner Daten zu bestimmten Zwecken widersprechen, wenn die Verarbeitung auf berechtigtem Interesse basiert.

1. Navigiere zu **Datenschutz** > **Verarbeitung einschraenken**
2. Waehle den Verarbeitungszweck
3. Klicke auf **Widerspruch einlegen**

Das System prueft den Widerspruch. Bei Verarbeitungen auf Basis von Art. 6(1)(f) DSGVO (berechtigtes Interesse) wird die Verarbeitung eingestellt, sofern keine zwingenden legitimen Gruende vorliegen.

---

## Account loeschen (Art. 17 DSGVO)

Du hast das Recht auf Loeschung deiner Daten.

!!! danger "Account-Loeschung ist endgueltig"
    Die Loeschung kann nicht rueckgaengig gemacht werden. Lade vorher deinen Datenexport herunter, wenn du deine Daten sichern moechtest.

### Ablauf der Loeschung

1. Navigiere zu **Datenschutz** > **Account loeschen**
2. Bestaetigen mit Passwort (oder OAuth Re-Authentifizierung)
3. Klicke auf **Account endgueltig loeschen**

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

!!! note "Warum werden Erntedaten nicht vollstaendig geloescht?"
    Das Cannabisgesetz (CanG) und das Pflanzenschutzmittelgesetz (PflSchG) schreiben vor, dass Ernte- und Behandlungsdaten fuer Pruef- und Nachweiszwecke aufbewahrt werden muessen. Dein Name und deine Kontaktdaten werden entfernt, die Mengen- und Behandlungsdaten bleiben als anonymisierte Eintraege erhalten. Dies ist rechtlich durch Art. 17 Abs. 3 lit. b DSGVO gedeckt.

---

## Datenspeicherung und Aufbewahrungsfristen

Kamerplanter speichert verschiedene Datenkategorien mit unterschiedlichen Aufbewahrungsfristen:

| Datenkategorie | Aufbewahrungsfrist | Begruendung |
|----------------|-------------------|-------------|
| Persoenliche Profildaten | Bis zur Loeschung + 90 Tage | DSGVO |
| Sensordaten (roh) | 90 Tage | NFR-011 |
| Sensordaten (stuendlich aggregiert) | 2 Jahre | NFR-011 |
| Sensordaten (taeglich aggregiert) | 5 Jahre | NFR-011 |
| IP-Adressen | 7 Tage, dann anonymisiert | Datensparsamkeit |
| Ernte-/Behandlungsdaten | Gesetzliche Mindestfrist | CanG / PflSchG |
| Einwilligungs-Log | 3 Jahre nach Widerruf | Nachweispflicht |
| Loeschungs-Audit-Log | 1 Jahr | Nachweispflicht |

### Sensor-Daten-Downsampling

Sensordaten werden automatisch in Stufen verdichtet:

```
0–90 Tage:     Rohdaten (jeder Messwert)
90 Tage–2 Jahre: Stuendliche Aggregate (Min/Max/Avg)
2–5 Jahre:     Taeglich Aggregate (Min/Max/Avg)
Nach 5 Jahren: Automatische Loeschung
```

!!! info "Warum Downsampling?"
    Rohe Sensordaten koennen sehr viel Speicherplatz beanspruchen. Nach 90 Tagen sind Minutenwerte fuer die meisten Auswertungen nicht mehr relevant. Das Downsampling reduziert den Speicherverbrauch erheblich, ohne wichtige Langzeittrends zu verlieren.

---

## IP-Anonymisierung

IP-Adressen werden grundsaetzlich nur fuer 7 Tage im Klartext gespeichert. Danach werden sie auf das /24-Subnetz anonymisiert (die letzten 8 Bits auf 0 gesetzt), sodass keine individuelle Zuordnung mehr moeglich ist.

---

## Sensor-Daten und Privatsphaere (DSFA)

Bestimmte Sensor-Daten koennen Rueckschluesse auf Anwesenheitsmuster erlauben (CO₂-Konzentration, Bewegungsmelder, manuelle Uebersteuerungen). Fuer solche Daten wurde eine **Datenschutz-Folgenabschaetzung (DSFA)** durchgefuehrt. Die wesentlichen Massnahmen:

- Sensordaten sind grundsaetzlich **nicht** mit anderen Tenants oder Dritten geteilt
- Der Plattformbetreiber kann Sensordaten nur nach expliziter Support-Anfrage und mit deiner Zustimmung einsehen
- Aggregierte Statistiken (ohne Personenbezug) koennen zur Systemverbesserung genutzt werden — dies kannst du in den Einwilligungen deaktivieren

---

## Haeufige Fragen

??? question "Werden meine Pflanzendaten fuer kommerzielle Zwecke genutzt?"
    Nein. Deine Pflanzendaten werden nicht an Dritte weitergegeben oder fuer kommerzielle Zwecke genutzt. Die Datenschutzerklaerung regelt dies verbindlich.

??? question "Wie lange dauert ein Datenexport?"
    Je nach Datenmenge dauert der Export 1–5 Minuten. Du erhaeltst eine Benachrichtigung, wenn er abgeschlossen ist. Der Download-Link ist 72 Stunden gueltig.

??? question "Kann ich einzelne Pflanzendaten loeschen, ohne den Account zu loeschen?"
    Ja. Du kannst einzelne Pflanzen, Standorte und Aufgaben jederzeit loeschen. Die Account-Loeschung ist nur noetig, wenn du alle deine Daten auf einmal entfernen moechtest.

??? question "Was passiert mit meinen Daten, wenn der Dienst eingestellt wird?"
    Du wirst mindestens 30 Tage vorher informiert und hast die Moeglichkeit, alle deine Daten zu exportieren. Nach Abschaltung werden alle personenbezogenen Daten innerhalb von 90 Tagen geloescht.

---

## Siehe auch

- [Konto-Einstellungen](../api/authentication.md)
- [Mandanten & Gaerten](tenants.md)
