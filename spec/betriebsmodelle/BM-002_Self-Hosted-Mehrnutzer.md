# BM-002: Self-Hosted Mehrnutzer

**Version:** 1.0
**Datum:** 2026-07-25
**Status:** Aktiv verfolgt — durch Outcome O-4 (`project/goals.md`) verankert
**Kurzname:** Gemeinschaftsbetrieb / Vereinsinstanz

---

## 1. Definition und Abgrenzung

Eine **Gemeinschaft** — Kleingartenverein, Gemeinschaftsgarten, Cannabis Social
Club, Schulklasse, Gärtnerei-Team — betreibt eine eigene Kamerplanter-Instanz
für **ihre Mitglieder**. Der Betreiber ist selbst Teil der Gemeinschaft, nicht
ein außenstehender Dienstleister. Neue Nutzer kommen über Einladung hinein, nicht
über offene Registrierung.

**Erkennungsmerkmale:**

- Die Nutzer kennen sich persönlich und gehören zur selben Organisation
- Zugang erfolgt über Einladung, nicht über offene Selbstregistrierung
- Der Betreiber ist ein Mitglied mit technischem Interesse — kein IT-Dienstleister
- Es gibt einen realen Grund, warum Daten *geteilt* werden: gemeinsame Beete, Gießdienst, Aufgaben

**Abgrenzung zu [BM-001](BM-001_Oeffentlicher-Managed-Service.md):** Sobald die
Registrierung für Beliebige offensteht, ist es BM-001 — auch ohne Bezahlung.
Umgekehrt bleibt eine Vereinsinstanz auf einem gemieteten Cloud-Server BM-002,
solange sie geschlossen ist.

**Abgrenzung zu [BM-003](BM-003_Self-Hosted-Einzelnutzer.md):** Sobald Personen
außerhalb des eigenen Haushalts eigene Konten haben, ist es BM-002 — auch bei
nur zwei Nutzern. Der Übergang ist rechtlich scharf, nicht graduell (§6.1).

---

## 2. Beteiligte Rollen

Rollenbezeichnungen nach dem zweiachsigen Modell aus
[REQ-049](../req/REQ-049_Rollenmodell-und-Vokabular.md): fachliche Rolle
(Beobachter/Gärtner/Leitung) plus administrative Zusatzberechtigung
(Verwaltung/Technik).

| Beteiligter | Wer | Fachliche Rolle | Zusatzberechtigung | Verantwortung |
|---|---|---|---|---|
| **Betreiber** | Technikaffines Mitglied, oft ehrenamtlich | — (außerhalb der App) | — | Server, Container, Secrets, Backups; faktisch auch Datenschutz — meist ohne es zu wissen |
| **Vorstand / Koordination** | Vereinsvorstand, Garten-Koordinator | Leitung | Verwaltung | Mitglieder einladen, Rollen vergeben, Standortstruktur, Mandanten-Einstellungen |
| **Technikwart** | Das Mitglied, das die Sensorik betreut | Gärtner | Technik | Home-Assistant-Anbindung dieses Mandanten, Sensoren, Import — **ohne** Zugriff auf die Mitgliederverwaltung |
| **Aktives Mitglied** | Parzellenpächter, Mitarbeitende | Gärtner | — | Fachdaten anlegen und ändern, Aufgaben erledigen; **kein Löschen** |
| **Passives Mitglied** | Neue oder ruhende Mitglieder, Buchhaltung | Beobachter | — | Lesen, drucken, exportieren |

**Die kritische Besonderheit dieses Modells:** Der **Betreiber** der Instanz
taucht in diesem Rollenmodell gar nicht auf — er arbeitet unterhalb der
Anwendung, auf Server- und Container-Ebene. Vorstand (Verwaltung) und
Technikwart (Technik) sind zudem regelmäßig **verschiedene Personen mit
unterschiedlicher Kompetenz**: der eine kennt die Mitglieder, der andere kann
Docker. Und der rechtlich Verantwortliche — der Verein als Körperschaft — ist
**keiner von beiden**. Genau diese Aufspaltung begründet, warum REQ-049
Verwaltung und Technik als getrennte Zusatzberechtigungen führt: Sonst müsste
jeder Verein dem Technikbetreuer die Mitgliederliste öffnen oder auf Sensorik
verzichten. In BM-001 und BM-003 fällt diese Trennung weg.

---

## 3. Endnutzer

| Zielgruppe | Relevanz | Anmerkung |
|-----------|----------|-----------|
| [ZG-004 Gemeinschaftsgarten](../target-audiences/ZG-004_Gemeinschaftsgarten.md) | **Primär** | Das Referenzszenario: Admin-Persona (Tom) + Mitglied-Persona (Aisha) |
| [ZG-005 Cannabis Social Club](../target-audiences/ZG-005_Cannabis-Social-Club.md) | **Primär** | 10–500 Mitglieder, CanG-Dokumentationspflicht, Datensouveränität als Kernanforderung |
| [UZG-003 Bildungseinrichtungen](../target-audiences/UZG-003_Bildungseinrichtungen.md) | Hoch | Lehrkraft als Admin, Schüler als `grower`/`viewer`; Minderjährige verschärfen die DSGVO-Lage |
| [UZG-002 Marktgärtner / CSA](../target-audiences/UZG-002_Marktgaertner.md) | Hoch | Mitarbeitende statt Mitglieder — arbeitsrechtliche Mitbestimmung beachten |
| [UZG-005 Gewächshaus-Betrieb](../target-audiences/UZG-005_Gewaechshaus-Betrieb.md) | Mittel | Schichtteams, mehrere Standorte |
| [ZG-002 Freilandgärtner](../target-audiences/ZG-002_Freilandgaertner.md) | Mittel | Als Mitglied eines Vereins, nicht als Einzelperson |

Die Endnutzer sind in diesem Modell **heterogener als in jedem anderen**: Im
selben Tenant sitzen ein technikaffiner Vorstand und ein 70-jähriges Mitglied,
das die App auf einem alten Smartphone im Garten bedient. Alles, was nur mit
Erklärung funktioniert, funktioniert hier nicht.

---

## 4. Technische Ausprägung

| Aspekt | Festlegung |
|--------|-----------|
| **Betriebsmodus** | `KAMERPLANTER_MODE=full` — **zwingend**, siehe §6.1 |
| **Betriebsprofil** | Standard (kleine Gemeinschaft) bis Profi (große Gemeinschaft, Indoor-Anbau) |
| **Infrastruktur** | Docker Compose auf VPS oder NAS; seltener kleines Kubernetes |
| **Mandanten** | Ein Tenant vom Typ `organization`; bei Verbänden mehrere |
| **Datenteilung** | Der Mandant ist die gemeinsame Arbeitsmenge: **alle** Gärtner pflegen **alle** Fachdaten (REQ-049 P1/P2). Wer etwas nicht teilen will, legt einen zweiten Mandanten an — nicht eine Zuweisung innerhalb desselben |
| **KI-Provider** | Ollama lokal, wenn Hardware es zulässt; sonst Cloud-LLM mit Information der Mitglieder |
| **Zeitreihen** | TimescaleDB optional (Standard) bis aktiv (Profi) |
| **Erreichbarkeit** | Meist öffentlich über TLS, damit Mitglieder von unterwegs zugreifen — damit gelten alle Härtungsanforderungen |

---

## 5. Verantwortungsverteilung

| Aufgabe | Betreiber | Verwaltung | Technik | Gärtner |
|---------|:---------:|:----------:|:-------:|:-------:|
| Server, Container, Updates | ✅ | — | — | — |
| Backups und Wiederherstellungstest | ✅ | — | — | — |
| TLS-Zertifikate, Erreichbarkeit | ✅ | — | — | — |
| Mitglieder einladen und entfernen | — | ✅ | — | — |
| Rollen und Zusatzberechtigungen vergeben | — | ✅ | — | — |
| Sensorik, Home Assistant, Importe einrichten | — | — | ✅ | — |
| Datenschutzerklärung gegenüber Mitgliedern | ✅ (fachlich: Verein) | ✅ | — | — |
| Betroffenenanfragen beantworten | ✅ | ✅ | — | Stellt Antrag |
| Fachdaten des Gartens pflegen | — | — | — | ✅ |

**Der wunde Punkt:** Diese Verantwortung ist **unbezahlt und personengebunden**.
Wenn das Mitglied, das den Server aufgesetzt hat, den Verein verlässt, steht die
Gemeinschaft ohne Zugang zu Secrets, Backups und Update-Wissen da. Ein
Betriebsmodell-Dokument nützt hier mehr als jedes Feature: Der Verein sollte
Zugangsdaten, Backup-Ort und Wiederherstellungsweg schriftlich außerhalb des
Kopfes dieser einen Person halten.

**Support-Erwartung:** mittel, aber sozial verbindlich. Mitglieder wenden sich
an „den, der das aufgesetzt hat" — ohne SLA, aber mit persönlicher Erwartung.

---

## 6. Rechtlicher Rahmen

### 6.1 DSGVO-Rolle — die Haushaltsausnahme greift nicht

Der Verein bzw. die Organisation ist **Verantwortlicher** nach Art. 4 Nr. 7
DSGVO. Die **Haushaltsausnahme** (Art. 2 Abs. 2 lit. c) gilt ausdrücklich nur
für „ausschließlich persönliche oder familiäre Tätigkeiten" — Vereinsmitglieder
sind rechtlich **Dritte**, auch wenn man sich duzt und seit Jahren kennt.

**Konsequenz:** Der `light`-Modus ist in BM-002 **unzulässig**. Er ist genau für
den Fall gebaut, den dieses Modell nicht erfüllt. Wer eine Vereinsinstanz im
`light`-Modus betreibt, hat keine Zugriffskontrolle, keine Zuordnung von
Handlungen zu Personen und keine Rechtsgrundlage — REQ-027 §1 stellt diesen
Sachverhalt fest.

### 6.2 Pflichten, die aus BM-002 folgen

- Datenschutzerklärung gegenüber den Mitgliedern (Art. 13)
- Verzeichnis von Verarbeitungstätigkeiten (Art. 30) — für Vereine praxisnah gering, aber nicht null
- Beantwortung von Betroffenenanfragen ([REQ-025](../req/REQ-025_Datenschutz-Betroffenenrechte.md)) — ohne SLA, aber mit gesetzlicher Monatsfrist
- Löschung der Mitgliedsdaten bei Austritt, soweit keine Aufbewahrungspflicht entgegensteht
- Information über eingesetzte Drittdienste, insbesondere Cloud-KI-Provider

### 6.3 Branchenspezifisch

- **Cannabis Social Clubs (CanG):** Anbau- und Weitergabedokumentation unterliegt
  gesetzlichen Aufbewahrungs- und Nachweispflichten. Kamerplanter anonymisiert
  solche Daten statt sie zu löschen, wenn eine Aufbewahrungspflicht greift
  ([NFR-011](../nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md)) —
  das ist für BM-002 die praxisrelevanteste Retention-Regel.
- **Pflanzenschutz (PflSchG):** Behandlungsdokumentation und Karenzzeiten sind
  bei gemeinschaftlich genutzten Beeten ein *Sicherheitsthema*, weil eine Person
  behandelt und eine andere erntet.
- **Bildungseinrichtungen:** Bei minderjährigen Nutzern ist Art. 8 DSGVO
  (Einwilligung Erziehungsberechtigter) zu beachten.

---

## 7. Konsequenzen für Anforderungen

| Anforderung | Status in BM-002 |
|---|---|
| [REQ-023](../req/REQ-023_Benutzerverwaltung-Authentifizierung.md) Auth | **Pflicht** — lokale Konten genügen meist, föderiert ist Komfort |
| [REQ-024](../req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md) Mandanten | **Pflicht, sicherheitskritisch** — die Mandantengrenze ist nach REQ-049 P2 die *einzige* Trennlinie |
| [REQ-049](../req/REQ-049_Rollenmodell-und-Vokabular.md) Rollenmodell | **Pflicht, sicherheitskritisch** — die zwei getrennten Zusatzberechtigungen (Verwaltung ≠ Technik) sind aus genau diesem Modell abgeleitet |
| [REQ-025](../req/REQ-025_Datenschutz-Betroffenenrechte.md) DSGVO | **Pflicht** — Umfang geringer als BM-001, aber nicht optional |
| [REQ-027](../req/REQ-027_Light-Modus.md) Light-Modus | **Ausgeschlossen** |
| [REQ-022](../req/REQ-022_Pflegeerinnerungen.md) Pflegeerinnerungen | Hoch — Gießdienst-Rotation ist der Kern-Use-Case |
| [REQ-030](../req/REQ-030_Benachrichtigungssystem.md) Benachrichtigungen | Hoch — Koordination über Personengrenzen hinweg |
| [REQ-032](../req/REQ-032_Druckansichten-Export.md) Druck/Export | Hoch — Aushang am Gartenhaus für Mitglieder ohne Smartphone |
| [NFR-011](../nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md) Retention | **Pflicht**, insbesondere die Anonymisierungs-Sonderregel bei CanG/PflSchG |
| Backup-/Restore-Werkzeuge für Laien | **Lücke** — es gibt keine Anforderung, die einen bedienbaren Wiederherstellungsweg beschreibt |
| Betreiberwechsel / Übergabe | **Lücke** — kein spezifizierter Weg, eine Instanz an ein anderes Mitglied zu übergeben |

**Wichtigste Einsicht für die Priorisierung:** In BM-002 ist die
Rechtedurchsetzung kein Komfort-Feature. Sie schützt nicht Mitglieder
voreinander bei den Fachdaten — die teilen sich alle Gärtner bewusst
(REQ-049 P1) —, sondern sichert drei andere Grenzen: Beobachter dürfen nicht
schreiben, Gärtner nicht **löschen** (Nicht-Umkehrbarkeit), und Technik gewährt
keinen Zugriff auf die Mitgliederverwaltung. Eine Autorisierungslücke, die in
BM-003 folgenlos wäre, ist hier ein Vertrauensbruch in einer realen sozialen
Gruppe.

---

## 8. Entscheidungshilfe

**Für BM-002 spricht:**

- Datensouveränität bleibt bei der Gemeinschaft — der Kaufgrund für ZG-005 und datenschutzsensible Vereine
- Kosten sind planbar und niedrig (ein VPS oder NAS für die ganze Gemeinschaft)
- Die geteilte Nutzung ist der eigentliche Zweck: Gießdienst, Beetplanung, Wissenstransfer zwischen Mitgliedern
- Es ist das Modell, für das REQ-024 ursprünglich entworfen wurde

**Gegen BM-002 spricht:**

- Die Betriebsverantwortung liegt bei einer ehrenamtlichen Einzelperson — Bus-Faktor 1
- Rechtliche Pflichten treffen einen Verein, der sie meist nicht kennt
- Heterogene Nutzerschaft: die App muss ohne Erklärung bedienbar sein

**Nicht wählen, wenn** niemand in der Gemeinschaft dauerhaft Zeit für Updates und
Backups hat. Dann ist BM-001 ehrlicher — oder jedes Mitglied betreibt seine
eigene Instanz nach BM-003 und verzichtet auf die gemeinsamen Funktionen.

---

## 9. Risiken und offene Punkte

| Risiko | Beschreibung | Gegenmaßnahme |
|---|---|---|
| **Bus-Faktor 1** | Der Betreiber verlässt den Verein, niemand kennt Secrets und Backup-Ort | Zugangsdaten und Wiederherstellungsweg schriftlich beim Vorstand hinterlegen |
| **Unbewusste DSGVO-Verantwortung** | Der Verein weiß nicht, dass er Verantwortlicher ist | Deployment-Doku muss den Übergang BM-003 → BM-002 prominent benennen |
| **Versehentlicher `light`-Betrieb** | Aus einer Einzelnutzer-Installation wird eine Vereinsinstanz, ohne den Modus zu wechseln | Upgrade-Pfad Light → Full ist in REQ-027 §1.1 (Szenario 5) spezifiziert und muss in der Doku sichtbar sein |
| **Fehlende Rechtedurchsetzung** | Beobachter können schreiben, Gärtner löschen oder der Technikwart die Mitgliederliste ändern, wenn die Prüfung nicht greift | Automatisierte Negativtests je Rolle und Zusatzberechtigung; DAST-Cross-Tenant-Tests ([NFR-015](../nfr/NFR-015_OWASP-ZAP-Security-Scanning.md)) |
| **Kein Übergabeweg** | Instanzübergabe an ein anderes Mitglied ist nicht spezifiziert | Offener Punkt — kandidiert für eine eigene Anforderung |
| **Cloud-KI ohne Information** | Der Betreiber aktiviert einen Cloud-Provider, Mitgliederdaten fließen an Dritte | Betreiber-Doku muss die Informationspflicht benennen |

---

## 10. Verwandte Dokumente

- [Übersicht Betriebsmodelle](README.md)
- [BM-001 Öffentlicher Managed Service](BM-001_Oeffentlicher-Managed-Service.md)
- [BM-003 Self-Hosted Einzelnutzer](BM-003_Self-Hosted-Einzelnutzer.md)
- [ZG-004 Gemeinschaftsgarten](../target-audiences/ZG-004_Gemeinschaftsgarten.md)
- [ZG-005 Cannabis Social Club](../target-audiences/ZG-005_Cannabis-Social-Club.md)
- `docs/de/deployment/betriebsprofile.md` — Profile „Standard" und „Profi"
