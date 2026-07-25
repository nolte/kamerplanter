# BM-001: Öffentlicher Managed Service

**Version:** 1.0
**Datum:** 2026-07-25
**Status:** Beschrieben, produktstrategisch **nicht verankert** (siehe §9.1)
**Kurzname:** Managed Service / SaaS / zentral gehostetes Angebot

---

## 1. Definition und Abgrenzung

Ein **Anbieter** betreibt eine zentrale Kamerplanter-Instanz und stellt sie
**fremden Endnutzern** als Dienst zur Verfügung. Die Endnutzer registrieren sich
selbst, kennen den Anbieter nicht persönlich und haben keinerlei Zugriff auf die
Infrastruktur. Ob der Dienst kostenlos, werbefrei, spendenfinanziert oder
kostenpflichtig ist, ändert am Modell nichts.

**Erkennungsmerkmale:**

- Registrierung steht Unbeliebigen offen (oder ist nur durch eine Warteliste begrenzt)
- Endnutzer und Betreiber stehen in keinem persönlichen Verhältnis
- Mandanten sind einander fremd — ein Mandant darf einen anderen nicht einmal *sehen*
- Der Betreiber ist eine Organisation mit IT-Betrieb, nicht eine Privatperson

**Abgrenzung zu [BM-002](BM-002_Self-Hosted-Mehrnutzer.md):** Dort kennen sich
alle Nutzer, gehören zur selben Organisation und der Betreiber ist selbst
Mitglied. Ein Kleingartenverein, der *nur seine eigenen Mitglieder* auf einem
gemieteten Server verwaltet, ist BM-002 — auch wenn der Server in der Cloud
steht. Öffnet derselbe Verein die Registrierung für die Allgemeinheit, wird
daraus BM-001.

**Abgrenzung zu [BM-003](BM-003_Self-Hosted-Einzelnutzer.md):** Dort sind
Betreiber und Nutzer dieselbe Person.

---

## 2. Beteiligte Rollen

Rollenbezeichnungen nach dem zweiachsigen Modell aus
[REQ-049](../req/REQ-049_Rollenmodell-und-Vokabular.md).

| Beteiligter | Wer | Ebene / Rolle | Verantwortung |
|---|---|---|---|
| **Anbieter/Betreiber** | Organisation mit IT-Betrieb | außerhalb der App | Verfügbarkeit, Sicherheit, Backups, Updates, Rechtskonformität |
| **Plattform-Administrator** | Angestellte des Anbieters | Plattform-Rolle `platform_admin` | Globaler Stammdaten-Katalog, global konfigurierte externe Dienste samt Schlüsseln, Mandanten sperren/reaktivieren, Missbrauchsbearbeitung |
| **Plattform-Betrachter** | Support-Mitarbeitende | `platform_viewer` (REQ-024 §1a.4, nur lesend) | Support 1st Level ohne Änderungsrechte |
| **Mandanten-Leitung** | Der Endkunde selbst | Leitung + Verwaltung (+ Technik) in *seinem* Mandanten | Eigene Mitglieder, eigene Daten, eigene Integrationen |
| **Endnutzer** | Registrierte Person | Gärtner oder Beobachter im jeweiligen Mandanten | Eigene Pflanzen und Beete |

Entscheidend: **Betreiber und Endnutzer sind vollständig getrennt.** REQ-049 P4
(„Keine Berechtigung entsteht aus einer anderen") ist hier die tragende Zusage:
Ein Plattform-Admin erhält durch seine Plattform-Rolle **keinen** Lesezugriff auf
die Fachdaten eines fremden Mandanten. Jede Vermischung — etwa ein
Support-Mitarbeitender, der zur Fehlersuche in Mandantendaten schaut — braucht
eine dokumentierte Rechtsgrundlage und eine Protokollierung.

Der Umkehrschluss aus REQ-049 §2.9/P5 ist für dieses Modell betriebswirtschaftlich
relevant: Global konfigurierte Dienste (Cloud-KI, Wetterdienste,
Anreicherungsquellen) laufen über **einen** Zugangsschlüssel des Anbieters und
wirken auf alle Mandanten — der Anbieter trägt also deren Kosten und deren
Drittland-Transferverantwortung zentral, nicht der einzelne Kunde.

---

## 3. Endnutzer

Managed Hosting senkt die Einstiegshürde auf null — es adressiert genau die
Zielgruppen, die an der Selbst-Hosting-Hürde scheitern:

| Zielgruppe | Relevanz | Warum dieses Modell |
|-----------|----------|---------------------|
| [UZG-001 Casual Hobby-Nutzer](../target-audiences/UZG-001_Casual-Hobby-Nutzer.md) | **Sehr hoch** | Würde nie einen Container starten; will eine App öffnen und loslegen |
| [ZG-003 Zimmerpflanzen-Enthusiast](../target-audiences/ZG-003_Zimmerpflanzen-Enthusiast.md) | Hoch | Geringe Tech-Affinität, hohe Nutzungsfrequenz |
| [ZG-002 Freilandgärtner](../target-audiences/ZG-002_Freilandgaertner.md) | Hoch | Saisonale Nutzung, kein Interesse an Serverwartung |
| [UZG-002 Marktgärtner / CSA](../target-audiences/UZG-002_Marktgaertner.md) | Mittel | Betriebliche Nutzung, aber keine IT-Abteilung |
| [ZG-001 Cannabis Indoor Grower](../target-audiences/ZG-001_Cannabis-Indoor-Grower.md) | **Gering** | Will Anbaudaten typischerweise gerade *nicht* bei einem Dritten liegen haben |
| [ZG-005 Cannabis Social Club](../target-audiences/ZG-005_Cannabis-Social-Club.md) | **Kritisch** | CanG-Dokumentationspflichten bei einem Dritten zu hosten wirft eigene Rechtsfragen auf (§7.3) |

---

## 4. Technische Ausprägung

| Aspekt | Festlegung |
|--------|-----------|
| **Betriebsmodus** | `KAMERPLANTER_MODE=full` — zwingend, kein Ermessen |
| **Betriebsprofil** | SaaS (siehe `docs/de/deployment/betriebsprofile.md`) |
| **Infrastruktur** | Kubernetes mit Autoscaling, mehrere Replicas je Dienst |
| **Datenbanken** | Managed-Dienste empfohlen (ArangoDB Oasis, Managed PostgreSQL) |
| **Mandanten** | Viele; Personal-Tenant wird bei Registrierung automatisch angelegt (REQ-024) |
| **KI-Provider** | Cloud-LLM (Anthropic / OpenAI-kompatibel) am Knowledge Service; Ollama je Mandant unwirtschaftlich |
| **Zeitreihen** | TimescaleDB aktiv — Downsampling-Stufen sind bei vielen Mandanten kostenrelevant |
| **Skalierung** | [NFR-012](../nfr/NFR-012_Cloud-Provider-Enterprise-Skalierung.md) |
| **Erreichbarkeit** | Öffentlich, TLS-terminiert, WAF/Rate-Limiting vorgelagert |

---

## 5. Verantwortungsverteilung

| Aufgabe | Anbieter | Endnutzer |
|---------|:--------:|:---------:|
| Verfügbarkeit, Monitoring, Incident-Response | ✅ | — |
| Backups und Wiederherstellung | ✅ | — |
| Sicherheitsupdates, CVE-Behandlung | ✅ | — |
| Mandantentrennung | ✅ | — |
| Rechtstexte (Impressum, Datenschutzerklärung, AGB) | ✅ | — |
| Beantwortung von Betroffenenanfragen | ✅ (mit Frist) | Stellt Antrag |
| Richtigkeit der eingegebenen Pflanzendaten | — | ✅ |
| Rollenvergabe innerhalb des eigenen Mandanten | — | ✅ |
| Export der eigenen Daten vor Kündigung | Stellt bereit | ✅ |

**Support-Erwartung:** hoch. Endnutzer eines gehosteten Dienstes erwarten
Reaktion innerhalb von Stunden, verständliche Fehlermeldungen und eine
Statusseite bei Störungen. Das ist der teuerste Teil dieses Modells — nicht die
Infrastruktur.

---

## 6. Rechtlicher Rahmen

### 6.1 DSGVO-Rolle

Der Anbieter ist **Verantwortlicher** im Sinne von Art. 4 Nr. 7 DSGVO für die
Daten seiner Endnutzer (Konto, E-Mail, Login-Metadaten, Nutzungsdaten). Für die
Inhaltsdaten, die ein Mandant über *seine* Mitglieder erfasst, kann der Anbieter
zusätzlich **Auftragsverarbeiter** sein — dann ist ein AV-Vertrag nach Art. 28
DSGVO mit jedem solchen Mandanten erforderlich.

Die **Haushaltsausnahme** (Art. 2 Abs. 2 lit. c) greift hier ausdrücklich
**nicht**. Der `light`-Modus ist in diesem Modell unzulässig — REQ-027 §1 stellt
das explizit fest.

### 6.2 Pflichten, die aus BM-001 folgen

- Vollständiges Consent-Management ([REQ-025](../req/REQ-025_Datenschutz-Betroffenenrechte.md)) inklusive widerrufbarer optionaler Einwilligungen
- Betroffenenrechte-Self-Service unter `/api/v1/privacy/` mit Bearbeitung binnen Monatsfrist (Art. 12 Abs. 3)
- Verzeichnis von Verarbeitungstätigkeiten (Art. 30)
- Meldepflicht bei Datenschutzvorfällen binnen 72 Stunden (Art. 33)
- Durchgesetzte Aufbewahrungsfristen ([NFR-011](../nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md))
- **DSFA** (Art. 35) für Sensordaten, die Anwesenheitsmuster erkennen lassen (CO₂, Bewegung, manuelle Overrides)
- Drittlandtransfer-Prüfung für jeden Cloud-KI-Provider und jeden externen Anreicherungsdienst (GBIF, Perenual, Wetterdienste), inklusive Transparenz gegenüber den Endnutzern
- Rechtstexte: Impressum, Datenschutzerklärung, bei Entgelt zusätzlich AGB und Widerrufsbelehrung

### 6.3 Branchenspezifische Sonderlage

Anbaudokumentation für Cannabis (CanG) und Pflanzenschutzmittel-Anwendungen
(PflSchG) unterliegen eigenen Aufbewahrungs- und teilweise Vorlagepflichten. Wer
solche Daten für Dritte hostet, wird zur zentralen Auskunftsstelle für Behörden
und macht die Instanz zu einem attraktiven Angriffsziel. Das ist der Grund,
warum ZG-001 und ZG-005 dieses Modell eher meiden als suchen.

---

## 7. Konsequenzen für Anforderungen

| Anforderung | Status in BM-001 |
|---|---|
| [REQ-023](../req/REQ-023_Benutzerverwaltung-Authentifizierung.md) Auth | **Pflicht** — inkl. föderierter Anmeldung, Refresh-Token-Rotation |
| [REQ-024](../req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md) Mandanten | **Pflicht, sicherheitskritisch** — Mandantentrennung ist die Kernzusage |
| [REQ-049](../req/REQ-049_Rollenmodell-und-Vokabular.md) Rollenmodell | **Pflicht** — insbesondere P4: die Plattform-Rolle darf keinen Fachdatenzugriff erzeugen |
| [REQ-025](../req/REQ-025_Datenschutz-Betroffenenrechte.md) DSGVO | **Pflicht, vollständig** |
| [REQ-027](../req/REQ-027_Light-Modus.md) Light-Modus | **Ausgeschlossen** |
| [NFR-011](../nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md) Retention | **Pflicht** — Celery-Enforcement muss nachweisbar laufen |
| [NFR-012](../nfr/NFR-012_Cloud-Provider-Enterprise-Skalierung.md) Skalierung | **Pflicht** |
| [NFR-014](../nfr/NFR-014_Nuclei-Security-Scanning.md)/[NFR-015](../nfr/NFR-015_OWASP-ZAP-Security-Scanning.md) DAST | **Pflicht** — Cross-Tenant-Negativtests sind das zentrale Gate |
| Service Accounts (REQ-023) | Sinnvoll — Mandanten binden ihre eigene Home-Assistant-Instanz an |
| Abrechnung, Kontingente, Kündigungs-Export | **Fehlt vollständig** — in keinem REQ spezifiziert |

**Die größte Lücke:** Es gibt keine Anforderung, die Kontingente, Abrechnung,
Vertragsende oder Datenmitnahme beschreibt. Ohne diese ist BM-001 nicht
betreibbar, sondern nur technisch startbar.

---

## 8. Entscheidungshilfe

**Für BM-001 spricht:**

- Es ist das einzige Modell, das UZG-001 (Casual Hobby-Nutzer, „sehr hohes
  Potenzial") überhaupt erreicht — diese Gruppe wird niemals selbst hosten
- Zentrale Wissensbasis und Cloud-KI amortisieren sich über viele Mandanten
- Fehler werden einmal zentral behoben statt in n Selbst-Hoster-Installationen

**Gegen BM-001 spricht:**

- Es widerspricht der aktuellen Mission („vollständig in eigener Hand betreibbar")
- Es verlagert Rechts-, Sicherheits- und Supportverantwortung vollständig auf den Betreiber
- Der Betriebsaufwand ist dauerhaft und personengebunden, nicht projektartig
- Es macht gerade jene Zielgruppen unerreichbar, die Datensouveränität als Kaufgrund haben (ZG-001, ZG-005)

**Nicht wählen, wenn** der Betreiber keine belastbare Antwort auf
Betroffenenanfragen, Vorfallsmeldung und 24/7-Erreichbarkeit hat.

---

## 9. Risiken und offene Punkte

### 9.1 Produktstrategische Verankerung fehlt

`project/mission.md` und `project/goals.md` beschreiben Kamerplanter als
selbst-gehostetes System. Es existiert **kein Outcome** und **keine Audience**
für Managed-Service-Kunden. Das SaaS-Betriebsprofil in der Deployment-Doku ist
derzeit die einzige Spur dieses Modells. Solange das so bleibt, ist BM-001 eine
*technische Möglichkeit*, kein Produktziel.

### 9.2 Weitere offene Punkte

| Risiko | Beschreibung |
|---|---|
| **Mandantentrennung** | Eine einzige fehlende Autorisierungsprüfung ist hier ein meldepflichtiger Vorfall. Die Permission-Matrix aus REQ-024 muss lückenlos und automatisiert getestet durchgesetzt sein. |
| **Drittland-Transfer** | Cloud-KI, Perenual, Wetterdienste — jeder Aufruf mit Standort- oder Nutzerbezug braucht eine Rechtsgrundlage und Transparenz. |
| **Kostendynamik** | LLM-Aufrufe und Sensordaten skalieren mit der Mandantenzahl, Einnahmen ggf. nicht. Ohne Kontingente ist das offen. |
| **Vendor-Lock-in-Vorwurf** | Ohne vollständigen Datenexport widerspricht ein Hosting-Angebot dem Selbstverständnis des Projekts. |
| **Support-Last** | Nicht technisch lösbar, sondern personell — der am häufigsten unterschätzte Posten. |

---

## 10. Verwandte Dokumente

- [Übersicht Betriebsmodelle](README.md)
- [BM-002 Self-Hosted Mehrnutzer](BM-002_Self-Hosted-Mehrnutzer.md)
- [BM-003 Self-Hosted Einzelnutzer](BM-003_Self-Hosted-Einzelnutzer.md)
- `docs/de/deployment/betriebsprofile.md` — Profil „SaaS / Multi-Tenant"
