# BM-003: Self-Hosted Einzelnutzer

**Version:** 1.0
**Datum:** 2026-07-25
**Status:** Aktiv verfolgt — durch Mission und Outcome O-5 (`project/goals.md`) verankert
**Kurzname:** Heimbetrieb / Einzelinstanz

---

## 1. Definition und Abgrenzung

Eine **Privatperson** betreibt Kamerplanter für sich selbst — auf einem
Raspberry Pi, einem NAS, einem alten Laptop oder per Docker Compose auf dem
Arbeitsrechner. Betreiber und Endnutzer sind **dieselbe Person**. Mitnutzende
Haushaltsangehörige teilen sich in der Regel denselben Zugang oder haben eigene
Konten im selben Haushalt.

**Erkennungsmerkmale:**

- Es gibt keine fremden Nutzer — nur die betreibende Person und ihr Haushalt
- Die Instanz läuft im LAN, hinter der Router-Firewall oder über VPN
- Kein Port-Forwarding, keine öffentliche Domain
- Niemand außer der betreibenden Person trägt Verantwortung, und niemand erwartet Support

**Abgrenzung zu [BM-002](BM-002_Self-Hosted-Mehrnutzer.md):** Sobald Personen
außerhalb des eigenen Haushalts eigene Konten bekommen — auch nur ein Nachbar,
auch unentgeltlich —, endet BM-003 und BM-002 beginnt. Der Übergang ist
rechtlich scharf (§6.1), nicht graduell.

**Grenzfall Haushalt:** Mehrere Personen desselben Haushalts sind noch BM-003 —
die Haushaltsausnahme spricht ausdrücklich von „persönlichen oder familiären
Tätigkeiten". Wer im Haushalt getrennte Konten will (etwa um Aufgaben
zuzuordnen), kann `full` fahren, ohne das Modell zu wechseln.

**Grenzfall öffentliche Erreichbarkeit:** Wer die eigene Instanz für den Zugriff
von unterwegs ins Internet stellt, bleibt BM-003 — aber der `light`-Modus ist
dann nicht mehr vertretbar, weil jeder mit der URL vollen Zugriff hätte.
Konsequenz: `full`-Modus, auch als Einzelnutzer.

---

## 2. Beteiligte Rollen

| Rolle | Wer | Anmerkung |
|-------|-----|-----------|
| **Betreiber = Endnutzer** | Die nutzende Person | Personalunion — das ist das definierende Merkmal |
| **Mitnutzende im Haushalt** | Partner, Familie | Teilen den Zugang (`light`) oder haben eigene Konten (`full`) |
| **System-Nutzer** | Automatisch angelegt im `light`-Modus | Kein echtes Konto; trägt die Daten und die Platform-Admin-Rechte (REQ-027 §1.1) |

Die Rollen- und Rechtekonzepte sind hier **inhaltlich leer**: Es gibt niemanden,
vor dem etwas zu schützen wäre. Genau deshalb existiert der `light`-Modus — die
Konzepte Mandant, Mitgliedschaft, Einladung und Consent sind für diese Person
reiner Overhead ([REQ-027](../req/REQ-027_Light-Modus.md), Finding F-003).

**Leer heißt nicht abwesend.** [REQ-049](../req/REQ-049_Rollenmodell-und-Vokabular.md)
P3 stellt ausdrücklich fest, dass es **keinen Sonderfall „persönlicher Mandant"**
gibt: Ein privater Garten ist derselbe Mandantentyp wie ein Kleingartenverein —
nur mit genau einem Mitglied, das die fachliche Rolle **Leitung** sowie **beide**
administrativen Zusatzberechtigungen (Verwaltung, Technik) besitzt. `tenant_type`
ist eine Anzeigeeigenschaft, keine Fallunterscheidung.

Daraus folgt eine für dieses Modell zentrale Unterscheidung:

| Ausgangslage | Weg nach BM-002 |
|---|---|
| BM-003 im **`full`-Modus** | **Nahtlos.** Weitere Mitglieder werden einfach eingeladen — ohne Umstellung, Migration oder Moduswechsel (REQ-049 P3). Nur die *rechtliche* Lage ändert sich (§6.1). |
| BM-003 im **`light`-Modus** | **Bruch.** Es gibt kein echtes Nutzerkonto, nur den System-Nutzer. Der Weg führt über das Upgrade Light → Full (REQ-027 §1.1, Szenario 5–8), bei dem der erste registrierte Nutzer den System-Mandanten übernimmt. |

Wer absehbar Mitglieder aufnehmen wird, wählt daher besser von Anfang an `full` —
der `light`-Modus spart Bedienaufwand, erkauft ihn aber mit einem
Migrationsschritt.

---

## 3. Endnutzer

Dies ist das **breiteste** Modell — fast jede Zielgruppe kommt hier vor, sobald
sie allein arbeitet:

| Zielgruppe | Relevanz | Anmerkung |
|-----------|----------|-----------|
| [ZG-001 Cannabis Indoor Grower](../target-audiences/ZG-001_Cannabis-Indoor-Grower.md) | **Primär** | Datensouveränität ist hier oft der Hauptgrund für Self-Hosting; hohe Tech-Affinität |
| [ZG-003 Zimmerpflanzen-Enthusiast](../target-audiences/ZG-003_Zimmerpflanzen-Enthusiast.md) | **Primär** | Das Referenzszenario aus REQ-027: „5 Pflanzen auf einem Raspberry Pi" |
| [ZG-002 Freilandgärtner](../target-audiences/ZG-002_Freilandgaertner.md) | **Primär** | Eigener Garten, saisonale Planung, geringe Tech-Affinität |
| [ZG-006 Hydroponik-Betreiber](../target-audiences/ZG-006_Hydroponik-Betreiber.md) | Hoch | Hohe Tech-Affinität, oft mit Home-Assistant-Anbindung |
| [UZG-004 Pflanzensammler](../target-audiences/UZG-004_Pflanzensammler.md) | Hoch | Umfangreiche Sammlung, eine Person |
| [UZG-001 Casual Hobby-Nutzer](../target-audiences/UZG-001_Casual-Hobby-Nutzer.md) | **Gering** | Wird eine Instanz niemals selbst betreiben — diese Gruppe erreicht nur BM-001 |
| [UZG-006 Microgreens-Produzent](../target-audiences/UZG-006_Microgreens-Produzent.md) | Mittel | Ein-Personen-Betrieb, kurze Zyklen |

**Spannung, die daraus folgt:** BM-003 ist das Modell mit der höchsten
Zielgruppenabdeckung — aber es setzt eine Fähigkeit voraus (Container starten,
Netzwerk verstehen), die genau der Gruppe mit dem größten Potenzial (UZG-001)
fehlt. Diese Lücke schließt technisch nur BM-001.

---

## 4. Technische Ausprägung

| Aspekt | Festlegung |
|--------|-----------|
| **Betriebsmodus** | `KAMERPLANTER_MODE=light` (Standard) oder `full` bei getrennten Haushaltskonten bzw. Interneterreichbarkeit |
| **Betriebsprofil** | Minimal (~1 GB RAM) oder Hobby (~3 GB RAM, mit lokaler KI) |
| **Infrastruktur** | Docker Compose auf Raspberry Pi 4/5, NAS, NUC oder Laptop |
| **Mandanten** | Im `light`-Modus genau einer: der automatisch erzeugte System-Tenant mit Zugriff auf alle globalen Stammdaten (REQ-027 §1.1) |
| **KI-Provider** | **Nur lokal** — im `light`-Modus erzwingt eine Startup-Validierung `ollama` oder einen loopback-gebundenen OpenAI-kompatiblen Endpunkt; Cloud-Provider führen zum Hard-Crash (REQ-027 §6.1) |
| **Zeitreihen** | TimescaleDB meist aus; Sensordaten optional über Home Assistant |
| **Home Assistant** | Häufig — der typische Self-Hoster betreibt bereits HA im selben Netz |
| **Erreichbarkeit** | LAN, VPN oder localhost. **Kein** Port-Forwarding im `light`-Modus |

---

## 5. Verantwortungsverteilung

Die Verantwortung liegt vollständig bei einer Person, die zugleich die einzige
Betroffene ist. Das macht dieses Modell operativ am einfachsten und
gleichzeitig am fehlertolerantesten:

| Aufgabe | Verantwortlich | Erwartungshaltung |
|---------|----------------|-------------------|
| Installation und Updates | Die nutzende Person | Selbsthilfe über Doku |
| Backups | Die nutzende Person | Datenverlust trifft nur sie selbst |
| Netzwerkabsicherung | Die nutzende Person | Router-Firewall, kein Port-Forwarding |
| Datenschutz | Entfällt (§6.1) | — |
| Support | Niemand | Doku, Issues, Community |

**Support-Erwartung:** keine. Das ist kein Nachteil, sondern Teil des
Selbstverständnisses — dieser Nutzer sucht Kontrolle, nicht Betreuung. Was er
stattdessen braucht: verständliche Fehlermeldungen, eine ehrliche
Troubleshooting-Doku und ein Update, das seine Daten nicht zerstört.

---

## 6. Rechtlicher Rahmen

### 6.1 DSGVO-Haushaltsausnahme

BM-003 stützt sich auf **Art. 2 Abs. 2 lit. c DSGVO**: Die Verordnung findet
keine Anwendung auf die Verarbeitung personenbezogener Daten durch natürliche
Personen zur Ausübung ausschließlich persönlicher oder familiärer Tätigkeiten.
Das ist die rechtliche Grundlage dafür, dass der `light`-Modus überhaupt
existieren darf — REQ-027 §1 führt das im Detail aus.

**Die Ausnahme trägt nur unter allen folgenden Bedingungen:**

- ausschließlich private, nicht gewerbliche Nutzung
- keine Nutzerkonten für Personen außerhalb des Haushalts
- kein öffentlicher Zugang aus dem Internet

**Fällt eine Bedingung weg, endet die Ausnahme sofort.** Dann gilt entweder
BM-002 (fremde Nutzer) oder mindestens `full`-Modus mit Authentifizierung
(öffentliche Erreichbarkeit). Das System kann das **nicht erzwingen** — die
Deployment-Doku muss den Sachverhalt prominent darstellen (REQ-027 §1).

### 6.2 Was trotz Ausnahme aktiv bleibt

Der `light`-Modus deaktiviert die *consent-basierten* DSGVO-Mechanismen, nicht
die technischen Schutzmaßnahmen. Aktiv bleiben unabhängig vom Modus
(REQ-027 §1, W-012):

| Maßnahme | Warum auch im Heimbetrieb |
|---|---|
| GPS-Rundung auf 2 Dezimalstellen vor Wetter-API-Aufrufen | Verhindert Klartext-Standortübertragung an Drittland-Provider |
| IP-Anonymisierung in Logs | Datensparsamkeit, kleinere Logs |
| EXIF-Strip beim Foto-Upload | Verhindert GPS-Daten in Backups |
| HTTPS-Enforcement | Schützt vor Mitlesen durch andere Geräte im LAN |
| Rate Limiting | Schutz, falls die Instanz versehentlich exponiert wird |
| Input-Validation | Generelle Sicherheit |

### 6.3 Gewerbliche Nutzung als Einzelperson

Ein Ein-Personen-Marktgartenbetrieb oder Microgreens-Produzent nutzt die
Software **gewerblich**. Für die eigenen Daten bleibt das unkritisch (keine
fremden Betroffenen), aber die Haushaltsausnahme ist begrifflich nicht mehr
einschlägig. Sobald Kundendaten (Abo-Kunden, Lieferadressen) erfasst würden,
gälte volles Datenschutzrecht — Kamerplanter erfasst solche Daten derzeit nicht.

---

## 7. Konsequenzen für Anforderungen

| Anforderung | Status in BM-003 |
|---|---|
| [REQ-027](../req/REQ-027_Light-Modus.md) Light-Modus | **Kernanforderung dieses Modells** |
| [REQ-020](../req/REQ-020_Onboarding-Wizard.md) Onboarding-Wizard | **Hoch** — muss ohne vorheriges Konto durchlaufbar sein (REQ-027) |
| [REQ-021](../req/REQ-021_UI-Erfahrungsstufen.md)/[REQ-042](../req/REQ-042_Modulare-Feature-Sichtbarkeit.md) Erfahrungsstufen, Modul-Sichtbarkeit | **Hoch** — eine Person muss ~40 Funktionen auf ihren Bedarf reduzieren können |
| [REQ-023](../req/REQ-023_Benutzerverwaltung-Authentifizierung.md) Auth | Deaktiviert im `light`-Modus; Pflicht bei Interneterreichbarkeit |
| [REQ-024](../req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md) Mandanten | **Inhaltlich irrelevant** — ein Mandant, keine fremden Nutzer |
| [REQ-049](../req/REQ-049_Rollenmodell-und-Vokabular.md) Rollenmodell | Wirksam, aber unsichtbar — eine Person mit Leitung und beiden Zusatzberechtigungen (P3). Darf nicht als Sonderfall implementiert werden |
| [REQ-025](../req/REQ-025_Datenschutz-Betroffenenrechte.md) DSGVO-Self-Service | **Nicht registriert** im `light`-Modus |
| [REQ-005](../req/REQ-005_Hybrid-Sensorik.md) Hybrid-Sensorik / [REQ-018](../req/REQ-018_Umgebungssteuerung.md) Aktorik | Hoch — Home Assistant ist im Heimbetrieb der Normalfall |
| KI-Assistent (REQ-031 ff.) | Nur mit lokalem Modell — Cloud-Provider werden hart blockiert (REQ-027 §6.1) |
| [NFR-004](../nfr/NFR-004_Lokale-Entwicklungsumgebung.md) Lokale Umgebung / Ressourcenbedarf | **Hoch** — ein Raspberry Pi mit 2 GB ist die Untergrenze, nicht der Komfortfall |
| Backup-Werkzeug für Laien | **Lücke** — dieselbe Lücke wie in BM-002, hier mit geringerer Schadenshöhe |

**Wichtigste Einsicht für die Priorisierung:** Autorisierungs- und
Mandantentrennungs-Findings sind in BM-003 **folgenlos** — es gibt keinen
Angreifer im eigenen LAN und keine fremden Daten. Umgekehrt wiegen
Ressourcenverbrauch, Startup-Robustheit und Update-Sicherheit hier schwerer als
in jedem anderen Modell: Ein Backend, das auf einem Pi nicht mehr startet, macht
die Software für die größte Nutzergruppe unbenutzbar.

---

## 8. Entscheidungshilfe

**Für BM-003 spricht:**

- Volle Datensouveränität, keinerlei Datenabfluss an Dritte
- Kein Login-Overhead, keine Consent-Banner, kein Mandantenkonzept
- Minimale laufende Kosten (Strom für einen Pi)
- Es ist das Modell, das die Mission wörtlich beschreibt
- Rechtlich der einfachste Fall — die DSGVO greift schlicht nicht

**Gegen BM-003 spricht:**

- Setzt Container- und Netzwerkgrundlagen voraus — die Hürde, an der UZG-001 scheitert
- Kein Zugriff auf Cloud-KI, damit schwächere KI-Funktionen ohne ausreichende lokale Hardware
- Backups sind Selbstdisziplin; Datenverlust ist realistisch
- Keine Zusammenarbeit möglich — wer Beete teilen will, braucht BM-002

**Nicht wählen, wenn** weitere Personen außerhalb des Haushalts eigene Konten
brauchen (→ BM-002) oder wenn die Instanz ohne VPN aus dem Internet erreichbar
sein soll (→ mindestens `full`-Modus).

---

## 9. Risiken und offene Punkte

| Risiko | Beschreibung | Gegenmaßnahme |
|---|---|---|
| **Versehentliche Exposition** | `light`-Instanz wird per Port-Forwarding erreichbar — jeder mit der URL hat Vollzugriff | Rate Limiting und HTTPS bleiben aktiv; die Deployment-Doku muss unmissverständlich warnen |
| **Stiller Übergang zu BM-002** | Ein Nachbar bekommt „auch mal einen Zugang" — rechtlich wechselt damit das Modell | Upgrade-Pfad Light → Full (REQ-027 §1.1, Szenario 5–8) und Doku-Hinweis |
| **Datenverlust** | Kein Backup, SD-Karte des Pi stirbt | Backup-Anleitung; ein bedienbares Export-Werkzeug fehlt als Anforderung |
| **Ressourcengrenze** | Neue Pflichtkomponenten heben den RAM-Bedarf über das Minimal-Profil | Ressourcenauswirkung jeder neuen Komponente in der Konfigurationsmatrix pflegen |
| **Downgrade-Datenverlust** | Rückweg Full → Light verwaist Multi-Tenant-Daten (REQ-027 §1.1, Szenario 8) | Als bewusst akzeptiert dokumentiert — vor dem Downgrade exportieren |

---

## 10. Verwandte Dokumente

- [Übersicht Betriebsmodelle](README.md)
- [BM-001 Öffentlicher Managed Service](BM-001_Oeffentlicher-Managed-Service.md)
- [BM-002 Self-Hosted Mehrnutzer](BM-002_Self-Hosted-Mehrnutzer.md)
- [REQ-027 Light-Modus](../req/REQ-027_Light-Modus.md) — die technische Grundlage dieses Modells
- `docs/de/deployment/betriebsprofile.md` — Profile „Minimal" und „Hobby"
