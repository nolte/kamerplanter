# Spezifikation: REQ-049 - Rollenmodell & verbindliches Rechte-Vokabular

```yaml
ID: REQ-049
Titel: Rollenmodell & verbindliches Rechte-Vokabular — zweiachsiges Berechtigungsmodell (fachliche Rolle + administrative Zusatzberechtigung), Plattform-Ebene, Kontoart und das normative Vokabular für alle Rechte-Tabellen
Kategorie: Plattform & Sicherheit
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, React 19, TypeScript 5.9
Status: Entwurf
Version: 1.3
Abhängigkeit: REQ-024 (Mandantenverwaltung — Permission-Matrix §1a, wird hier im Vokabular abgelöst und im Rollenumfang erweitert), REQ-023 (Authentifizierung — Kontoart, Dienstkonten), REQ-027 (Light-Modus — Einzelkonto), REQ-030 (Benachrichtigungssystem — übernimmt die Empfängerregel §2.8), REQ-022 (Pflegeerinnerungen — dieselbe Empfängerregel), REQ-046 (Wetterdienste — wandern auf die globale Ebene §2.9), REQ-005 + REQ-018 (Home Assistant — wandert auf die Mandantenebene §2.9), NFR-001 (Schichtenarchitektur), NFR-015 (OWASP-ZAP — Permission-Matrix-Tests), NFR-016 (Versioniertes Migrations-Framework — Datenmigration der Mitgliedschaften)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.3 | 2026-07-25 | Offenen Punkt aus §2.9 entschieden und als §2.10 ausgeführt: Trennung von **Angebot** (global, Plattform-Admin), **Anbindung** (pro Mandant, Technik) und **Auswahl** (pro Standort, Leitung). Ein global eingerichteter Dienst ist auswählbar, wirkt aber nur, wo er ausgewählt wurde. Das globale Angebot darf leer sein — Home-Assistant-Sensoren sind eine vollwertige Wetterquelle ohne jeden externen Dienst, und umgekehrt. AK-23 korrigiert (Angebot ≠ automatische Wirkung), AK-25 bis AK-29 ergänzt. |
| 1.2 | 2026-07-25 | Leitprinzip P5 ergänzt: Die Konfigurationsebene eines externen Dienstes folgt seiner Zugehörigkeit (Betreiberdienst → global/Plattform-Admin, Mandantendienst → pro Mandant/Technik). Neue §2.9 mit der Einordnung je Dienst und der normativen Festlegung, dass eine Installation **mehrere unabhängige Home-Assistant-Instanzen** gleichzeitig anbindet (zentrale Vereinsinstallation und private Installation nebeneinander). Wetterdienste wandern damit auf die globale Ebene, Home Assistant auf die Mandantenebene — beide verletzen P5 heute, in entgegengesetzter Richtung. AK-20 bis AK-24 ergänzt. Offener Punkt: Auswahl und Priorität der Wetterquellen je Standort. |
| 1.1 | 2026-07-25 | Leitprinzipien P1–P4 als Soll-Zustand ergänzt (§2.1): Der Mandant ist die gemeinsame Arbeitsmenge, Trennung nur an der Mandantengrenze, kein Sonderfall persönlicher Mandant. Daraus abgeleitet: normative Empfängerregel für Benachrichtigungen (§2.8, bisher in REQ-030 undefiniert) und Auflösung der zuweisungsbasierten Schreibkontrolle (§3.5, ersetzt REQ-024 §1a.5). „Zugewiesene" von erlaubtem zu verbotenem Vokabular verschoben, „Eigene" auf verfasste Beiträge eingegrenzt. AK-13 bis AK-19 ergänzt. |
| 1.0 | 2026-07-25 | Initialer Entwurf. Führt das zweiachsige Rollenmodell (fachliche Rolle + administrative Zusatzberechtigung) ein und legt das verbindliche Vokabular für alle Rechte-Tabellen fest. Grundlage: Spec-Audit vom 2026-07-25, das zwei konkurrierende Rollenmodelle nachwies — REQ-024 §1 (`admin`/`grower`/`viewer`) gegen die nachträglich per SEC-H-001 eingezogenen Abschnitte „Authentifizierung & Autorisierung" in 31 Fach-REQs (`Mitglied`/`Admin`). Rollenbedarf abgeleitet aus UZG-002, UZG-003, UZG-005, ZG-004, ZG-005. |

## 1. Business Case

### User Stories

- **Als Biologielehrerin** möchte ich meinen Schülern erlauben, Messwerte und Fotos zu erfassen, ohne dass sie versehentlich eine Pflanze oder ein ganzes Beet löschen können — damit ein Versuchsprotokoll über ein Schuljahr belastbar bleibt.
- **Als Gewächshaus-Inhaber** möchte ich meinem Meister erlauben, Aufgaben zu verteilen und Fehleingaben zu korrigieren, ohne ihm Personalhoheit über die Mitgliederliste zu geben.
- **Als Vorstand eines Kleingartenvereins** möchte ich unserem technikaffinen Mitglied die Anbindung der Sensorik überlassen, ohne ihm die Verwaltung der Mitgliedschaften zu übertragen.
- **Als Vorstandsvorsitzende einer Anbauvereinigung** möchte ich unserem Buchhalter Einblick in Erträge und Verbrauch geben, ohne dass er im Anbau etwas verändern kann.
- **Als Entwickler** möchte ich in jedem Anforderungsdokument dieselben Rollenbegriffe vorfinden, damit aus einer Rechte-Tabelle eindeutig hervorgeht, welche Prüfung im Code zu implementieren ist.

### Problem

Kamerplanter kennt heute zwei Rollenmodelle nebeneinander:

1. **REQ-024 §1** definiert drei Mandanten-Rollen — `admin`, `grower`, `viewer` — in einer strengen Rangfolge und schreibt dem Beobachter ausdrücklich reinen Lesezugriff zu.
2. **Die Abschnitte „Authentifizierung & Autorisierung"** in 31 Fach-REQs (nachträglich per Sammelmaßnahme SEC-H-001 ergänzt) benutzen stattdessen die zwei Werte `Mitglied` und `Admin`. In 25 der ausgewerteten Abschnitte kommt der Beobachter überhaupt nicht vor.

Da `Mitglied` alle drei Rollen umfasst, erlaubt jede Zeile der Form `| Ressource | Mitglied | Mitglied | Admin |` dem Beobachter das **Schreiben** — im direkten Widerspruch zu REQ-024. Betroffen sind unter anderem Erntedokumentation, Tankmanagement, Pflanzenschutz-Behandlungen und die Aktorik, dort einschließlich Not-Aus.

Hinzu kommen zwei strukturelle Lücken:

- **`Admin` bedeutet in den Fach-REQs überwiegend nichts Administratives.** Bei rund 30 von 45 Admin-Zeilen steht `Admin` allein in der Spalte „Löschen". Gemeint ist eine fachliche Befugnis (Datensätze entfernen), nicht Mandantenverwaltung.
- **Technische Konfiguration innerhalb eines Mandanten hat keine eigene Zuordnung.** Home-Assistant-Anbindung, InvenTree-Verbindung, Sensorkonfiguration, CSV-Import und Anreicherungsquellen verlangen heute dieselbe Rolle wie die Mitgliederverwaltung.

### Beschreibung

REQ-049 löst das auf, indem es Berechtigungen auf **zwei unabhängige Achsen** verteilt statt auf eine einzige Rangfolge:

- **Achse 1 — die fachliche Rolle:** was jemand *im Garten* tun darf. Dreistufig, mit klarer Rangfolge.
- **Achse 2 — administrative Zusatzberechtigungen:** was jemand *am Mandanten* verwalten darf. Additiv, unabhängig von Achse 1 vergebbar.

Damit werden Kombinationen ausdrückbar, die die Zielgruppen verlangen und die eine einzige Rangfolge nicht abbilden kann — etwa „verwaltet Mitglieder, arbeitet aber nicht im Garten" oder „richtet die Technik ein, ohne Personalhoheit".

Darüber hinaus legt dieses Dokument das **verbindliche Vokabular** (§3) fest, das in allen Rechte-Tabellen des Repositoriums zu verwenden ist. Es ist die normative Quelle; REQ-024 §1a bleibt die ausführliche Permission-Matrix, benutzt aber ab sofort dieses Vokabular.

## 2. Rollenmodell

### 2.1 Leitprinzipien

Diese fünf Sätze sind der Soll-Zustand. Jede Regel in diesem Dokument und jede Rechte-Tabelle im Repositorium muss sich an ihnen messen lassen; eine Anforderung, die einem davon widerspricht, ist zurückzuweisen oder das Prinzip ist bewusst zu ändern.

**P1 — Der Mandant ist die gemeinsame Arbeitsmenge.**
Alle Pflanzen, Standorte und Aufgaben eines Mandanten werden von **allen** Gärtnern dieses Mandanten gepflegt. Es gibt innerhalb eines Mandanten keine Aufteilung der Fachdaten auf einzelne Mitglieder. Daraus folgt unmittelbar die Benachrichtigungsregel: Wird eine Aufgabe oder Pflegeerinnerung fällig, werden **alle** Mitglieder mit fachlicher Rolle Gärtner oder Leitung benachrichtigt — nicht nur ein Ersteller oder ein Zugewiesener.

**P2 — Trennung erfolgt an der Mandantengrenze, nicht innerhalb eines Mandanten.**
Wer etwas nicht teilen will, legt es in einen anderen Mandanten. Innerhalb eines Mandanten gibt es keine privaten Bereiche, keine für Mitglieder unsichtbaren Datensätze und keine auf einzelne Mitglieder beschränkten Schreibrechte auf Fachdaten. Das macht die Sichtbarkeit für Nutzer vorhersagbar: Was im Garten liegt, sehen und pflegen alle im Garten.

**P3 — Es gibt keinen Sonderfall „persönlicher Mandant".**
Ein privater Garten ist derselbe Mandantentyp wie ein Kleingartenverein — nur mit genau einem Mitglied, das die fachliche Rolle Leitung sowie beide administrativen Zusatzberechtigungen besitzt. Er unterliegt denselben Regeln, denselben Endpunkten und denselben Benachrichtigungen. Er kann **jederzeit** weitere Mitglieder aufnehmen, ohne Umstellung, Migration oder Moduswechsel. Umgekehrt darf kein Verhalten daran hängen, ob ein Mandant als persönlich oder als Organisation angelegt wurde; `tenant_type` ist eine Anzeigeeigenschaft, keine Fallunterscheidung.

**P4 — Keine Berechtigung entsteht aus einer anderen.**
Die Leitung erhält durch ihre fachliche Rolle keine Verwaltungsrechte. Ein Plattform-Admin erhält durch seine Plattform-Rolle keinen Lesezugriff auf die Fachdaten eines fremden Mandanten. Jede Berechtigung wird ausdrücklich vergeben.

**P5 — Die Konfigurationsebene eines externen Dienstes folgt seiner Zugehörigkeit.**
Gehört der angebundene Dienst dem **Betreiber** — eine Instanz für alle, ein Zugangsschlüssel, für alle Mandanten identische Daten —, wird er global konfiguriert und wirkt auf alle Mandanten. Gehört er dem **Mandanten** — eigene Installation, eigene Zugangsdaten, mandantenspezifische Daten —, wird er pro Mandant konfiguriert. Daraus ergibt sich unmittelbar die zuständige Rolle: global → Plattform-Admin, mandantenbezogen → Zusatzberechtigung Technik. Die Ausprägung je Dienst steht in §2.9.

**Konsequenz für Kollaborationsfunktionen:** Dienstpläne, Pinnwand und gemeinsame Einkaufsliste sind aus P3 heraus in **jedem** Mandanten verfügbar. Sie sind nicht an einen Mandantentyp gebunden — in einem Ein-Personen-Garten sind sie lediglich meist nicht sinnvoll und dürfen dort ausgeblendet, aber nicht gesperrt werden.

### 2.2 Die drei Ebenen im Überblick

| Ebene | Gilt | Frage, die sie beantwortet | Werte |
|-------|------|---------------------------|-------|
| **Fachliche Rolle** | pro Mandant, genau eine | Was darf die Person im Garten tun? | Beobachter, Gärtner, Leitung |
| **Administrative Zusatzberechtigung** | pro Mandant, keine, eine oder beide | Was darf die Person am Mandanten verwalten? | Verwaltung, Technik |
| **Plattform-Rolle** | einmal für die Installation | Was darf die Person an der Instanz verwalten? | Plattform-Admin |

Quer dazu steht die **Kontoart** (§2.6): Nutzerkonto oder Dienstkonto. Sie ändert nicht, *was* erlaubt ist, sondern *wie* sich das Konto anmeldet.

### 2.3 Achse 1 — Fachliche Rollen

Jedes Mitglied hat pro Mandant **genau eine** fachliche Rolle. Sie bilden eine Rangfolge: Leitung schließt Gärtner ein, Gärtner schließt Beobachter ein.

| Rolle | Schlüssel | Rang | Darf zusätzlich zur darunterliegenden Rolle | Typische Besetzung |
|-------|-----------|:----:|---------------------------------------------|--------------------|
| **Beobachter** | `viewer` | 0 | Alle Fachdaten des Mandanten lesen, drucken und exportieren | Buchhalter, Prüfer, Angehörige, Anzeige-Bildschirm im Kiosk-Modus |
| **Gärtner** | `grower` | 1 | Fachdaten anlegen und ändern: Pflanzen, Dokumentation von Gießen/Düngen/Ernte/Behandlung, Fotos, Beobachtungen, Aufgaben erledigen, Pflegeerinnerungen bestätigen, Phasen weiterschalten. **Kein Löschen.** | Vereinsmitglied, Schüler, Junior-Grower, Saisonkraft, Mitarbeiter |
| **Leitung** | `lead` | 2 | Fachdaten **löschen**; Aufgaben an andere zuweisen; Standortstruktur (Sites, Bereiche, Stellplätze) anlegen und umbauen; Vorlagen (Workflows, Substrattypen) pflegen; Batch-Operationen über fremde Datensätze | Meister, Head-Grower, Parzellenwart, Betriebsleiter |

**Begründung der Grenze zwischen Gärtner und Leitung:** Sie verläuft entlang der *Nicht-Umkehrbarkeit*. Ein Gärtner kann Fehler korrigieren, indem er einen Wert überschreibt; er kann keine Historie vernichten. Genau das verlangen UZG-003 („Schüler als Grower mit eingeschränkten Rechten") und ZG-005 („2 Junior-Grower im Team"). Sie deckt sich außerdem mit REQ-024 §1a.1, wo für `grower` durchgängig „❌D" steht.

### 2.4 Achse 2 — Administrative Zusatzberechtigungen

Diese Berechtigungen werden **zusätzlich** zur fachlichen Rolle vergeben. Ein Mitglied kann keine, eine oder beide besitzen. Sie sind unabhängig vom Rang auf Achse 1 — auch ein Beobachter kann Verwaltung erhalten.

| Zusatzberechtigung | Schlüssel | Umfasst | Typische Besetzung |
|--------------------|-----------|---------|--------------------|
| **Verwaltung** | `management` | Mitglieder einladen, Rollen ändern, Mitglieder entfernen; Einladungslinks erstellen und widerrufen; Mandanten-Einstellungen (Name, Kurzname, Stammdaten-Zuweisung); Standort-Zuweisungen; Dienstkonten; Mandanten löschen | Vorstand, Lehrkraft, Inhaber, Schriftführer |
| **Technik** | `technical` | **Mandanteneigene** Integrationen einrichten: die Home-Assistant-Instanz dieses Mandanten, MQTT, InvenTree; Sensoren und Aktoren konfigurieren (nicht: bedienen); CSV-Import ausführen; Anreicherungsquellen und Sync-Trigger; KI-Provider des Mandanten; Benachrichtigungskanäle des Mandanten | Technikwart, IT-Verantwortlicher, betreuender Dienstleister |

Nicht enthalten sind **global konfigurierte** externe Dienste — sie gehören zur Plattform-Ebene (§2.5) und folgen der Regel aus §2.9.

**Begründung für zwei getrennte Zusatzberechtigungen:** Personalhoheit und Technikzugriff fallen in der Praxis auseinander. ZG-004 und ZG-005 beschreiben beide Konstellationen unabhängig voneinander. Wer beide zusammenlegt, zwingt jeden Verein, dem Technikbetreuer die Mitgliederliste zu öffnen — oder auf die Sensorik zu verzichten.

**Sicherheitsregel:** `technical` gewährt keinen Klartext-Zugriff auf gespeicherte Zugangsschlüssel. Schlüssel bleiben verschlüsselt und werden über die API stets maskiert zurückgegeben (siehe REQ-046 §5).

### 2.5 Plattform-Ebene

Die Plattform-Rolle wird über eine Admin-Mitgliedschaft im technischen Mandanten `platform` abgebildet und gilt einmal für die gesamte Installation.

| Rolle | Schlüssel | Darf |
|-------|-----------|------|
| **Plattform-Admin** | `platform_admin` | Globalen Stammdaten-Katalog pflegen (Arten, Sorten, botanische Familien, Schädlinge, Krankheiten, Behandlungsmittel, globale Düngemittel und Nährstoffpläne); `tenant_has_access`-Zuweisungen; Arten und Sorten aus einem Mandanten in den globalen Katalog übernehmen; Companion- und Fruchtfolge-Graphkanten; **global konfigurierte externe Dienste samt Zugangsschlüsseln** (§2.9); Mandanten- und Nutzerübersicht; Anmeldeanbieter konfigurieren; Bilderkennung aktivieren; Mandanten und Konten sperren, reaktivieren und Notfall-Admins ernennen |

**Abgrenzung:** Der Plattform-Admin sieht *Verwaltungsdaten* über Mandanten hinweg (Existenz, Name, Mitgliederliste). Er erhält dadurch **keinen** Lesezugriff auf die Fachdaten eines Mandanten. Wer dorthin Zugriff braucht, muss regulär als Mitglied aufgenommen werden.

Eine reine Lese-Variante (`platform_viewer`) für Monitoring und Prüfungen ist in REQ-024 §1a.4 vorgesehen und bleibt dort spezifiziert; sie ist nicht Gegenstand dieses Dokuments.

### 2.6 Kontoart

| Kontoart | Schlüssel | Bedeutung |
|----------|-----------|-----------|
| **Nutzerkonto** | `user` | Mensch. Meldet sich interaktiv an (lokal oder föderiert). |
| **Dienstkonto** | `service` | Maschine (Home Assistant, Auswertungs-Dashboard, KI-Assistent, CI/CD). Kein Passwort, keine interaktive Anmeldung; ausschließlich Schlüssel-Authentifizierung mit optionaler IP-Freigabeliste und Ratenbegrenzung. |

Die Kontoart ändert **keine** Rechte: Ein Dienstkonto mit der Rolle Gärtner darf exakt, was ein menschlicher Gärtner darf. Für die Einrichtung gilt das Prinzip der geringsten Berechtigung — ein Anzeige-Dashboard erhält Beobachter, ein protokollierender Automatisierungsdienst Gärtner.

### 2.7 Zusammenspiel der Achsen

```
Berechtigt(Person, Aktion, Mandant) =
      Aktion ist fachlich   → Rang(fachliche Rolle) >= Mindestrang(Aktion)
    ODER
      Aktion ist administrativ → benötigte Zusatzberechtigung ∈ zusatzberechtigungen
    ODER
      Aktion ist plattformweit → Person ist Plattform-Admin
```

Die drei Zweige sind **disjunkt**: Jede Aktion gehört zu genau einer Kategorie. Eine Aktion darf niemals über zwei Zweige gleichzeitig erreichbar sein — sonst entsteht wieder die heutige Vermischung.

**Beispielbesetzungen:**

| Person | Fachliche Rolle | Zusatzberechtigungen | Ergebnis |
|--------|-----------------|----------------------|----------|
| Vereinsvorstand, gärtnert selbst | Leitung | Verwaltung | Darf alles im Garten und verwaltet Mitglieder; Technik bleibt außen vor |
| Schriftführerin, gärtnert nicht | Beobachter | Verwaltung | Pflegt die Mitgliederliste, verändert im Garten nichts |
| Technikwart | Gärtner | Technik | Bindet Sensorik an, dokumentiert mit, sieht die Mitgliederliste nur lesend |
| Schüler im Projektkurs | Gärtner | — | Dokumentiert Messwerte, kann nichts löschen |
| Buchhalter der Anbauvereinigung | Beobachter | — | Liest und exportiert Erträge und Verbrauch |
| Home Assistant (Dienstkonto) | Gärtner | — | Schreibt Sensorwerte und Gießvorgänge |
| Persönlicher Garten nach Registrierung | Leitung | Verwaltung, Technik | Alleiniger Nutzer, alles erlaubt |

### 2.8 Benachrichtigungsempfänger

Diese Regel folgt aus P1 und ist die normative Vorgabe für REQ-030 und REQ-022, die sie bisher nicht definieren.

```
Empfänger einer Aufgaben- oder Pflegebenachrichtigung im Mandanten
= alle aktiven Mitgliedschaften mit fachlicher Rolle Gärtner oder Leitung
```

Präzisierungen:

- **Beobachter erhalten keine Handlungsaufforderungen.** Sie dürfen nicht handeln, also wäre die Benachrichtigung folgenlos. Reine Informationsmeldungen (etwa Frostwarnungen) dürfen sie erhalten.
- **Eine Zuweisung ändert den Empfängerkreis nicht, nur die Darstellung.** Ist eine Aufgabe jemandem zugewiesen, wird sie dieser Person hervorgehoben angezeigt; die übrigen Gärtner bleiben informiert.
- **Übernahme schließt die Meldung bei allen.** Sobald ein Mitglied die Aufgabe übernimmt oder erledigt, wird die Benachrichtigung bei allen anderen Empfängern geschlossen. Das verhindert das in REQ-024 §1 beschriebene „dreimal gegossen", ohne den Empfängerkreis einzuschränken.
- **Keine stille Unterdrückung.** Es darf keinen Zustand geben, in dem eine fällige Aufgabe **niemanden** erreicht, weil kein Ersteller und kein Zugewiesener ermittelbar war. Fehlt eine Zuweisung, ist das der Normalfall — nicht der Ausnahmefall.
- **Skalierung.** Ab einer konfigurierbaren Mandantengröße tritt die Tagesübersicht an die Stelle von Einzelmeldungen. Der Empfängerkreis bleibt davon unberührt; nur die Zustellform ändert sich.

Im Ein-Personen-Mandanten fällt diese Regel mit dem heutigen Verhalten zusammen: ein Gärtner, ein Empfänger. Das ist die in P3 geforderte Einheitlichkeit — kein Sonderpfad.

### 2.9 Externe Dienste: Konfigurationsebene und zuständige Rolle

Anwendung von P5 auf die angebundenen Dienste. Die Spalte „Zuständig" ergibt sich zwingend aus der Spalte „Ebene" — sie ist keine eigenständige Entscheidung.

| Dienst | Ebene | Zuständig | Begründung |
|--------|-------|-----------|------------|
| Öffentliche Wetterdienste (Open-Meteo, DWD, OpenWeatherMap, NASA POWER) | **Global** | Plattform-Admin | Ein Zugangsschlüssel je Anbieter, für alle Mandanten dieselbe Datenquelle |
| Pflanzenerkennung (Pl@ntNet, Erkennungsdienste) | **Global** | Plattform-Admin | Instanzweiter Schlüssel, mandantenunabhängiges Modell |
| Objektspeicher | **Global** | Plattform-Admin | Speicher-Backend der Installation |
| Anmeldeanbieter (OIDC) | **Global** | Plattform-Admin | Identitätsquelle der Installation |
| Stammdaten-Anreicherung (OpenFarm, Growstuff) | **Global** | Plattform-Admin | Schreibt in den globalen Katalog |
| **Home Assistant** | **Pro Mandant** | Technik | Gehört dem Mandanten; mehrere Instanzen gleichzeitig |
| MQTT-Broker | **Pro Mandant** | Technik | Eigene Broker-Instanz je Mandant |
| InvenTree | **Pro Mandant** | Technik | Eigenes Warenwirtschaftssystem des Mandanten |
| Benachrichtigungskanäle | **Pro Mandant** | Technik | Eigene Zustellwege je Mandant |
| KI-Provider | **Hybrid** | Plattform-Admin (Vorgabe), Technik (Überschreibung) | Globale Systemvorgabe, die ein Mandant durch eigene Zugangsdaten ersetzen darf |

**Mehrere Home-Assistant-Instanzen an einer Installation.** Aus der Einordnung „pro Mandant" folgt die tragende Fähigkeit: Eine Kamerplanter-Installation bindet **gleichzeitig mehrere, voneinander unabhängige** Home-Assistant-Instanzen an — die zentrale Installation des Kleingartenvereins in dessen Mandanten und die private Installation eines Mitglieds in dessen persönlichem Mandanten. Daraus folgt normativ:

- Es gibt **keine** instanzweite Home-Assistant-Konfiguration mehr. Endpunkt, Zugangstoken und Zeitüberschreitung hängen am Mandanten.
- Jede Sensor-, Aktor- und Veröffentlichungsoperation löst ihre Home-Assistant-Verbindung **aus dem Mandantenkontext** auf, nie aus einer globalen Einstellung.
- Der Ausfall einer Instanz darf andere Mandanten nicht beeinträchtigen. Eine nicht auflösbare Adresse darf insbesondere **nicht** den Anwendungsstart verhindern.
- Ein Mandant ohne Home-Assistant-Anbindung ist der Normalfall, kein Fehlerzustand.

**Zugangsschlüssel** bleiben auf beiden Ebenen verschlüsselt und werden über die Schnittstelle stets maskiert zurückgegeben. Weder die Zusatzberechtigung Technik noch die Plattform-Rolle gewähren Klartext-Zugriff.

### 2.10 Angebot und Auswahl: die Wetterquellen als Musterfall

P5 ordnet die *Bereitstellung* eines Dienstes ein, nicht seine *Nutzung*. Beides ist zu trennen, und die Wetterquellen sind der Musterfall dafür. Es gibt drei Ebenen mit je eigener Zuständigkeit:

| Ebene | Was dort entschieden wird | Zuständig |
|-------|---------------------------|-----------|
| **Angebot** (global) | Welche externen Wetterdienste stehen der Installation zur Verfügung, mit welchen Zugangsdaten | Plattform-Admin |
| **Anbindung** (pro Mandant) | Ist eine Home-Assistant-Instanz verbunden, und welche Entitäten liefert sie | Technik |
| **Auswahl** (pro Standort) | Welche der verfügbaren Quellen dieser Standort in welcher Reihenfolge nutzt | Leitung |

**Ein global eingerichteter Dienst ist ein Angebot, keine Vorgabe.** Er wird dadurch in jedem Mandanten *auswählbar* — er wird keinem Standort aufgezwungen und wirkt nicht automatisch. Die Entscheidung, ob und wo er genutzt wird, trifft der Mandant je Standort.

**Das Angebot darf leer sein.** Ein global eingerichteter externer Dienst ist **keine Voraussetzung** für Wetterdaten. Hat ein Mandant eine Home-Assistant-Instanz angebunden, kann er deren Sensoren als Wetterquelle nutzen, **ohne dass irgendein externer Dienst eingerichtet ist**. Umgekehrt gilt genauso: Ein Mandant ohne Home Assistant nutzt allein die global angebotenen Dienste. Beide Wege sind vollwertig und voneinander unabhängig.

Daraus folgt normativ:

- Die Quellenauswahl eines Standorts speist sich aus **zwei unabhängigen Töpfen**: den global angebotenen externen Diensten und den Entitäten der mandanteneigenen Home-Assistant-Instanz. Beide Töpfe dürfen einzeln leer sein.
- Sind beide leer, hat der Standort keine automatischen Wetterdaten. Das ist ein **gültiger Zustand**, kein Fehler — die manuelle Erfassung bleibt der Rückfallweg.
- Entfällt ein global angebotener Dienst oder wird sein Zugangsschlüssel entzogen, greift an jedem betroffenen Standort die nächste konfigurierte Priorität. Der Standort ist nicht defekt, und die Herkunftskennzeichnung der Daten macht den Wechsel nachvollziehbar.
- Beobachter sehen die Auswahl, ändern sie nicht. Gärtner sehen sie ebenfalls; geändert wird sie von der Leitung.

Diese Dreiteilung ist auf jeden weiteren Dienst übertragbar, der sowohl betreiberseitig angeboten als auch mandantenseitig ersetzt werden kann — beim KI-Provider gilt sie bereits (§2.9, Zeile „Hybrid").

## 3. Verbindliches Vokabular

Dieser Abschnitt ist die normative Grundlage für **jede** Rechte-Tabelle im Repositorium — in REQ-Dokumenten, ADRs, Code-Kommentaren und der Endnutzer-Dokumentation.

### 3.1 Erlaubte Begriffe

| Begriff | Bedeutung | Zulässig in |
|---------|-----------|-------------|
| **Beobachter** / `viewer` | genau diese Rolle | allen Spalten |
| **Gärtner** / `grower` | genau diese Rolle | allen Spalten |
| **Leitung** / `lead` | genau diese Rolle | allen Spalten |
| **Alle Rollen** | Beobachter + Gärtner + Leitung | **nur** in Lese-, Druck- und Export-Zeilen |
| **Ab Gärtner** | Gärtner + Leitung | Standardangabe für schreibende Aktionen |
| **Nur Leitung** | ausschließlich Leitung | löschende und strukturverändernde Aktionen |
| **Verwaltung** | Zusatzberechtigung `management`, unabhängig von der fachlichen Rolle | administrative Aktionen |
| **Technik** | Zusatzberechtigung `technical`, unabhängig von der fachlichen Rolle | Integrations- und Konfigurationsaktionen |
| **Plattform-Admin** | Plattform-Ebene | globale Stammdaten und Instanzverwaltung |
| **Eigene** | zusätzliche Einschränkung auf selbst verfasste Beiträge | **ausschließlich** bei verfassten Inhalten (Pinnwand-Beiträge, Kommentare, eigene Betroffenenanfragen) — **nie** bei Fachdaten, siehe P1 |
| **—** | Aktion existiert für diese Ressource nicht | allen Spalten |

### 3.2 Verbotene Begriffe

| Verboten | Warum | Stattdessen |
|----------|-------|-------------|
| **Mitglied** | Mehrdeutig — umfasst den Beobachter und hat dadurch die Widersprüche verursacht | „Alle Rollen" beim Lesen, „Ab Gärtner" beim Schreiben |
| **Admin** (unqualifiziert) | Mehrdeutig zwischen Leitung, Verwaltung und Plattform-Admin | Den gemeinten Begriff nennen |
| **Nutzer**, **User**, **Benutzer** | Kontoart, keine Rechteangabe | Die zutreffende Rolle nennen |
| **Tenant-Admin** | Bezeichnet im alten Modell Rolle und Verwaltung zugleich | „Verwaltung" oder „Leitung", je nach gemeinter Aktion |
| **Berechtigter**, **Verantwortlicher** | Unbestimmt | Die zutreffende Rolle nennen |
| **Zugewiesene** (als Rechteangabe) | Verstößt gegen P1 — die Standort-Zuweisung schränkt keine Schreibrechte ein | „Ab Gärtner"; die Zuweisung ist reine Koordination, siehe §3.5 |

### 3.3 Tabellenschema für Fach-REQs

Jedes REQ mit eigenen Ressourcen führt einen Abschnitt `## Autorisierung` mit genau diesem Schema:

```markdown
## Autorisierung

**Standardregel:** Alle Endpunkte dieses Dokuments erfordern Anmeldung und
Mitgliedschaft im adressierten Mandanten, sofern nicht anders angegeben.

| Ressource | Lesen | Anlegen | Ändern | Löschen | Sonderaktionen |
|-----------|-------|---------|--------|---------|----------------|
| <Name>    | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | <Aktion>: <Rolle> |
```

Die Spalte „Schreiben" wird in „Anlegen" und „Ändern" aufgeteilt, weil beide Aktionen sich für einzelne Ressourcen unterscheiden (etwa Pflegeprofile: anlegen nein, bestätigen ja).

### 3.4 Migrationsregeln für bestehende Tabellen

Die 31 vorhandenen Abschnitte werden nach diesen Regeln umgeschrieben. Die Zuordnung ist mechanisch; jede Abweichung ist im jeweiligen Dokument zu begründen.

| Alt | Neu | Bedingung |
|-----|-----|-----------|
| `Mitglied` in der Spalte Lesen | **Alle Rollen** | immer |
| `Mitglied` in der Spalte Schreiben | **Ab Gärtner** | immer |
| `Mitglied` in der Spalte Löschen | **Nur Leitung** | immer |
| `Admin` in der Spalte Löschen | **Nur Leitung** | fachliche Ressource |
| `Admin` bei Integrationen, Sensorkonfiguration, Import, Anreicherung | **Technik** | technische Konfiguration |
| `Admin` bei Mitgliedern, Einladungen, Mandanten-Einstellungen, Zuweisungen | **Verwaltung** | Mandantenverwaltung |
| `Admin` bei globalen Stammdaten | **Plattform-Admin** | mandantenübergreifend |
| `Grower` | **Ab Gärtner** bzw. **Gärtner**, je nach Kontext | immer |
| `Platform-Admin`, `Tenant-Admin` (REQ-001) | **Plattform-Admin** bzw. **Verwaltung** | immer |

### 3.5 Zuweisungen sind Koordination, keine Rechte

Aus P1 und P2 folgt, dass weder die Standort-Zuweisung noch die Aufgabenzuweisung den Zugriff einschränkt. Beide bleiben erhalten, aber ihre Bedeutung ist eine andere:

| Konstrukt | Bedeutung im Soll-Zustand | Ausdrücklich **nicht** |
|-----------|---------------------------|------------------------|
| **Standort-Zuweisung** | Hinweis, wer sich um eine Parzelle kümmert; Grundlage für Sortierung, Filter und die persönliche Ansicht „meine Parzelle" | Keine Schreibgrenze. Jeder Gärtner darf jeden Standort des Mandanten bearbeiten. |
| **Aufgabenzuweisung** (`assigned_to`) | Absprache, wer eine Aufgabe übernimmt; steuert Hervorhebung und Reihenfolge | Kein Ausschluss. Jeder Gärtner darf eine fremd zugewiesene Aufgabe erledigen — etwa wenn die zugewiesene Person ausfällt. |

**Damit entfällt REQ-024 §1a.5** (zuweisungsbasierte Write-Kontrolle) ersatzlos. Die dort definierte Funktion `can_write(user, resource, tenant)` reduziert sich auf die Rangprüfung der fachlichen Rolle. Die Felder `valid_from`/`valid_until` an der Zuweisung bleiben für die saisonale Darstellung erhalten, wirken aber nicht mehr auf Berechtigungen.

**Begründung:** Eine Schreibgrenze innerhalb eines Mandanten erzeugt genau die Unvorhersehbarkeit, die P2 vermeiden soll — Mitglieder sehen Datensätze, die sie nicht bearbeiten dürfen, ohne dass die Oberfläche den Grund erklären kann. Wer echte Trennung braucht, bekommt einen eigenen Mandanten; das ist billig, sofort verfügbar und für den Nutzer verständlich.

## 4. Nachschlagetabelle: Welche Rolle brauche ich wofür?

Diese Tabelle ist die anwenderseitige Umkehrung von §2 — sortiert nach Tätigkeit statt nach Rolle.

### 4.1 Im Garten

| Ich möchte … | Ich brauche |
|--------------|-------------|
| Pflanzen, Standorte, Aufgaben, Ernten ansehen | Beobachter |
| Verlauf, Kennzahlen und Diagramme ansehen | Beobachter |
| Gießplan, Etiketten oder Berichte drucken und exportieren | Beobachter |
| Eine Pflanze anlegen oder umtopfen | Gärtner |
| Gießen, Düngen, Behandlung oder Ernte dokumentieren | Gärtner |
| Ein Foto hochladen | Gärtner |
| Eine mir zugewiesene Aufgabe erledigen | Gärtner |
| Eine Pflegeerinnerung bestätigen oder verschieben | Gärtner |
| Eine Pflanze in die nächste Wachstumsphase schalten | Gärtner |
| Eine Beobachtung oder einen Tagebucheintrag erfassen | Gärtner |
| Eine Pflanze, Ernte oder einen Standort **löschen** | Leitung |
| Eine Aufgabe **einer anderen Person** zuweisen | Leitung |
| Die Standortstruktur anlegen oder umbauen | Leitung |
| Arbeitsablauf-Vorlagen oder Substrattypen pflegen | Leitung |
| Mehrere Datensätze gesammelt bearbeiten | Leitung |

### 4.2 Am Mandanten

| Ich möchte … | Ich brauche |
|--------------|-------------|
| Ein Mitglied einladen oder entfernen | Verwaltung |
| Die Rolle eines Mitglieds ändern | Verwaltung |
| Einen Einladungslink erstellen oder widerrufen | Verwaltung |
| Namen, Kurznamen oder Stammdaten-Zuweisung ändern | Verwaltung |
| Eine Parzelle einem Mitglied zuweisen | Verwaltung |
| Ein Dienstkonto anlegen | Verwaltung |
| Den Mandanten löschen | Verwaltung |
| Die Home-Assistant-Instanz **dieses Gartens** anbinden | Technik |
| MQTT oder InvenTree anbinden | Technik |
| Einen Sensor oder Aktor **konfigurieren** (nicht bedienen) | Technik |
| Einen CSV-Import ausführen | Technik |
| Die Benachrichtigungskanäle des Gartens einrichten | Technik |
| Den KI-Provider des Gartens abweichend von der Systemvorgabe setzen | Technik |

### 4.3 An der Installation

| Ich möchte … | Ich brauche |
|--------------|-------------|
| Globale Arten, Sorten oder Schädlingsdaten pflegen | Plattform-Admin |
| Festlegen, welche globalen Arten ein Mandant sieht | Plattform-Admin |
| Eine mandanteneigene Art in den globalen Katalog übernehmen | Plattform-Admin |
| Anmeldeanbieter konfigurieren | Plattform-Admin |
| Einen Wetterdienst samt Zugangsschlüssel einrichten (wirkt auf alle Gärten) | Plattform-Admin |
| Die Stammdaten-Anreicherung (OpenFarm, Growstuff) einrichten | Plattform-Admin |
| Den Objektspeicher der Installation einrichten | Plattform-Admin |
| Die Systemvorgabe für den KI-Provider setzen | Plattform-Admin |

Ein global eingerichteter Dienst wird dadurch **auswählbar**, nicht wirksam. Welche Quelle ein einzelner Standort tatsächlich nutzt, entscheidet die Leitung des jeweiligen Gartens (§2.10).

### 4.4 Wetterquellen: wer entscheidet was?

| Ich möchte … | Ich brauche |
|--------------|-------------|
| Einen externen Wetterdienst überhaupt verfügbar machen (einmalig, für alle Gärten) | Plattform-Admin |
| Die Home-Assistant-Instanz meines Gartens verbinden, damit ihre Sensoren als Wetterquelle taugen | Technik |
| Für einen Standort festlegen, welche Quelle in welcher Reihenfolge genutzt wird | Leitung |
| Sehen, woher die Wetterdaten eines Standorts stammen | Beobachter |
| Wetterdaten manuell erfassen, wenn keine Quelle verfügbar ist | Gärtner |
| Alle Mandanten und Konten überblicken, sperren, reaktivieren | Plattform-Admin |
| Bilderkennung aktivieren und Referenzbilder freigeben | Plattform-Admin |

## 5. Datenmodell

Die Erweiterung betrifft ausschließlich die bestehende `memberships`-Collection (REQ-024 §2).

```python
class Membership(BaseModel):
    """Verknüpft einen User mit einem Tenant (REQ-024) und trägt beide
    Berechtigungsachsen (REQ-049 §2)."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    tenant_key: str

    # Achse 1 — fachliche Rolle, genau eine
    role: Literal["viewer", "grower", "lead"]

    # Achse 2 — administrative Zusatzberechtigungen, keine bis beide
    admin_scopes: list[Literal["management", "technical"]] = Field(default_factory=list)

    is_active: bool = True
    joined_at: datetime
```

**Invarianten:**

- **INV-1:** Ein Mandant hat jederzeit mindestens eine aktive Mitgliedschaft mit `management` in `admin_scopes`. Das Entfernen oder Herabstufen der letzten solchen Mitgliedschaft wird abgelehnt (ersetzt die bisherige „letzter Admin"-Regel aus REQ-024).
- **INV-2:** `admin_scopes` ist duplikatfrei und enthält ausschließlich definierte Werte.
- **INV-3:** Die fachliche Rolle ist unabhängig von `admin_scopes` gültig — jede der sechs Kombinationen ist erlaubt.

**Index:** Bestehender Index auf `[user_key, tenant_key]` bleibt. Zusätzlich ein Persistent-Index auf `[tenant_key, admin_scopes[*]]`, damit INV-1 ohne vollen Collection-Scan prüfbar ist.

## 6. Migration bestehender Daten

Die Migration läuft über das versionierte Migrations-Framework (NFR-016) und ist verlustfrei.

| Bestand | Ziel |
|---------|------|
| `role: "admin"` | `role: "lead"`, `admin_scopes: ["management", "technical"]` |
| `role: "grower"` | `role: "grower"`, `admin_scopes: []` |
| `role: "viewer"` | `role: "viewer"`, `admin_scopes: []` |

**Verhaltensänderung, die dabei bewusst eintritt:** Bisher konnte ein `grower` in der Umsetzung Fachdaten löschen, obwohl REQ-024 §1a.1 das nie vorsah. Nach der Migration kann er es nicht mehr. Das ist die beabsichtigte Korrektur, keine Regression — sie ist in den Freigabehinweisen anzukündigen.

**Persönliche Mandanten:** Bei der Registrierung angelegte persönliche Mandanten erhalten `role: "lead"` und beide Zusatzberechtigungen, damit der Alleinnutzer uneingeschränkt arbeiten kann.

**Light-Modus:** Das einzige Konto erhält `role: "lead"`, beide Zusatzberechtigungen und die Plattform-Rolle (REQ-027 bleibt im Übrigen unberührt).

## 7. Akzeptanzkriterien

| ID | Kriterium | Teststufe |
|----|-----------|-----------|
| AK-01 | Ein Beobachter erhält auf **jedem** schreibenden mandantenbezogenen Endpunkt `403` | Integration |
| AK-02 | Ein Gärtner kann Fachdaten anlegen und ändern, erhält beim Löschen `403` | Integration |
| AK-03 | Eine Leitung kann Fachdaten löschen | Integration |
| AK-04 | Ein Mitglied mit `management`, aber fachlicher Rolle Beobachter, kann Mitglieder einladen und erhält beim Anlegen einer Pflanze `403` | Integration |
| AK-05 | Ein Mitglied mit `technical`, aber ohne `management`, kann die HA-Anbindung konfigurieren und erhält bei der Mitgliederverwaltung `403` | Integration |
| AK-06 | Das Entfernen der letzten Mitgliedschaft mit `management` wird abgelehnt (INV-1) | Unit + Integration |
| AK-07 | Die Migration überführt jedes bestehende `admin` nach `lead` + beide Zusatzberechtigungen, ohne Mitgliedschaften zu verlieren | Migration |
| AK-08 | Ein Dienstkonto mit Rolle Gärtner hat exakt die Rechte eines menschlichen Gärtners | Integration |
| AK-09 | Ein Plattform-Admin ohne Mitgliedschaft erhält auf Fachdaten eines fremden Mandanten `404` | Integration |
| AK-10 | Kein REQ-Dokument enthält in einer Rechte-Tabelle einen der in §3.2 verbotenen Begriffe | CI-Prüfung |
| AK-11 | Jede in einem REQ definierte mandantenbezogene Ressource kommt in REQ-024 §1a.1 vor | CI-Prüfung |
| AK-12 | Die Oberfläche blendet Aktionen aus, die die aktuelle Rolle nicht ausführen darf — für beide Achsen | Komponente |
| AK-13 | Eine fällig werdende Aufgabe ohne Ersteller und ohne Zuweisung erzeugt eine Benachrichtigung für **jeden** Gärtner und jede Leitung des Mandanten (P1, §2.8) | Integration |
| AK-14 | Übernimmt ein Mitglied eine Aufgabe, wird die zugehörige Benachrichtigung bei allen übrigen Empfängern geschlossen | Integration |
| AK-15 | Ein Beobachter erhält keine Handlungsaufforderung, wohl aber reine Informationsmeldungen | Integration |
| AK-16 | Ein Gärtner kann einen Standort bearbeiten, der einem anderen Mitglied zugewiesen ist (P1, §3.5) | Integration |
| AK-17 | Ein Gärtner kann eine Aufgabe erledigen, die einem anderen Mitglied zugewiesen ist | Integration |
| AK-18 | Kein Endpunkt und keine Oberflächenfunktion verzweigt auf `tenant_type` (P3) | CI-Prüfung |
| AK-19 | Ein persönlicher Mandant kann ohne Umstellung ein weiteres Mitglied aufnehmen; danach gelten unverändert dieselben Regeln (P3) | Integration |
| AK-20 | Zwei Mandanten mit **unterschiedlichen** Home-Assistant-Instanzen arbeiten gleichzeitig; Sensorwerte und Schaltbefehle landen jeweils bei der richtigen Instanz (P5, §2.9) | Integration |
| AK-21 | Es existiert keine instanzweite Home-Assistant-Konfiguration mehr; eine nicht auflösbare Adresse eines Mandanten verhindert weder den Anwendungsstart noch beeinträchtigt sie andere Mandanten | Integration |
| AK-22 | Ein Mandant ohne Home-Assistant-Anbindung ist funktionsfähig und erzeugt keine Fehlermeldung | Integration |
| AK-23 | Ein global eingerichteter Wetterdienst ist in **jedem** Mandanten auswählbar, wirkt aber an keinem Standort, solange er dort nicht ausgewählt wurde (§2.10) | Integration |
| AK-24 | Weder die Zusatzberechtigung Technik noch die Plattform-Rolle liefert einen Zugangsschlüssel im Klartext zurück | Integration |
| AK-25 | Ein Standort liefert Wetterdaten aus Home-Assistant-Sensoren, **ohne** dass ein externer Wetterdienst global eingerichtet ist (§2.10) | Integration |
| AK-26 | Ein Standort liefert Wetterdaten aus einem global angebotenen Dienst, **ohne** dass der Mandant Home Assistant angebunden hat | Integration |
| AK-27 | Sind beide Quellentöpfe leer, ist der Standort funktionsfähig und weist auf die manuelle Erfassung hin — keine Fehlermeldung | Integration |
| AK-28 | Wird ein global angebotener Dienst entfernt, greift an betroffenen Standorten die nächste konfigurierte Priorität; die Herkunftskennzeichnung weist die neue Quelle aus | Integration |
| AK-29 | Die Quellenauswahl eines Standorts ist für Beobachter und Gärtner sichtbar und nur durch die Leitung änderbar | Integration |

## 8. Abhängigkeiten

**Erforderliche Module:**

- **REQ-023 (Authentifizierung):** liefert Konto und Kontoart; die Rollenauflösung setzt eine authentifizierte Identität voraus.
- **REQ-024 (Mandantenverwaltung):** liefert Mandant und Mitgliedschaft. REQ-049 erweitert die Mitgliedschaft um `admin_scopes` und löst das Vokabular von §1a ab; die ausführliche Permission-Matrix bleibt dort.
- **NFR-016 (Migrations-Framework):** trägt die Datenmigration aus §6.

**Wird benötigt von:**

- **Alle Fach-REQs mit eigenen Ressourcen:** **HOCH** — sie übernehmen das Vokabular aus §3 und das Tabellenschema aus §3.3.
- **NFR-015 (OWASP ZAP):** **HOCH** — die dort vorgesehenen Permission-Matrix-Tests brauchen je ein Testkonto pro Kombination aus §2.7.
- **REQ-030 (Benachrichtigungssystem):** **HOCH** — übernimmt die Empfängerregel aus §2.8; das Dokument definiert bisher keine Empfängerermittlung.
- **REQ-022 (Pflegeerinnerungen):** **HOCH** — Pflegeerinnerungen folgen derselben Empfängerregel.
- **REQ-006 (Aufgabenplanung):** **MITTEL** — `assigned_to` verliert jede Rechtewirkung und wird zur Koordinationsangabe (§3.5).
- **REQ-005 (Hybrid-Sensorik) und REQ-018 (Umgebungssteuerung):** **HOCH** — die Home-Assistant-Anbindung wandert von der instanzweiten Einstellung an den Mandanten (§2.9). Betrifft Verbindungsauflösung, Ausfallverhalten und Startverhalten.
- **REQ-046 (Wetterdienst-Datenquellen):** **HOCH** — Anbieter und Zugangsschlüssel wandern auf die globale Ebene (§2.9); die Auswahl und Priorität je Standort bleibt beim Mandanten (§2.10). Die bestehende `:WeatherSourceConfig` je Standort bleibt damit erhalten, verliert aber die Anbieter-Zugangsdaten und referenziert stattdessen das globale Angebot.
- **REQ-029/REQ-029-A, REQ-040, NFR-013:** **NIEDRIG** — bereits global konfiguriert, bestätigen P5 nur.
- **REQ-027 (Light-Modus):** **NIEDRIG** — nur die Zuordnung des Einzelkontos.

**Auswirkung auf die bestehende Umsetzung:**

- `TenantRole` erhält den Wert `lead`; `admin` entfällt zugunsten der Zusatzberechtigungen.
- Die Rangfolge-Prüfung bleibt für Achse 1; für Achse 2 kommt eine eigene Prüfung hinzu.
- Der Berechtigungs-Hook im Frontend liefert künftig beide Achsen.

## 9. Abgrenzung

Nicht Gegenstand dieses Dokuments:

- **Befristete Mitgliedschaft / Urlaubsvertretung** — eigenes Vorhaben. Sie wird als *zeitliche Begrenzung einer bestehenden Mitgliedschaft* modelliert, nicht als weitere Rolle, damit die Rechtelogik nicht dupliziert wird.
- **Untergruppen innerhalb eines Mandanten** (Klassen, Semester-Gruppen aus UZG-003) — eigenes Feature, keine Rollenfrage.
- **Die ausführliche Permission-Matrix je Ressource** — bleibt REQ-024 §1a und wird dort auf dieses Vokabular umgestellt.
- **Die Behebung der im Audit gefundenen Durchsetzungslücken im Code** — eigenes Vorhaben; REQ-049 liefert dafür die Sollvorgabe.
