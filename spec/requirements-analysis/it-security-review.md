# IT-Security-Review: Kamerplanter Anforderungsdokumente

```yaml
Reviewer: IT-Security-Architekt & Datenschutzexperte
Datum: 2026-02-27
Scope: Alle REQ-001 bis REQ-024, NFR-001 bis NFR-010, UI-NFR-001 bis UI-NFR-012, stack.md
Methodik: OWASP Top 10, STRIDE, DSGVO Art. 5-20, BSI IT-Grundschutz
Status: Erstbewertung
```

---

## 1. Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Authentifizierung | 4/5 | REQ-023 ist umfassend spezifiziert (Bcrypt, JWT, PKCE, Token-Rotation) |
| Autorisierung | 3/5 | REQ-024 definiert Rollenmodell, aber viele REQs referenzieren Auth nicht |
| API-Sicherheit | 4/5 | NFR-006 vorbildlich, Rate Limiting spezifiziert, CORS definiert |
| Datensparsamkeit | 2/5 | Erhebliche Luecken: keine Loeschfristen, IP-Speicherung ohne Zweckbindung |
| DSGVO-Konformitaet | 1/5 | Betroffenenrechte kaum spezifiziert, kein Loeschkonzept, kein AVV |
| Verschluesselung | 4/5 | TLS, Bcrypt, SHA-256, AES-256/Fernet gut spezifiziert |
| Infrastruktur-Sicherheit | 3/5 | Container non-root in stack.md, aber Security Contexts unvollstaendig |
| Eingabevalidierung | 3/5 | Pydantic-Validierung vorhanden, aber max. Feldlaengen fehlen |

---

## 2. Kritische Befunde (Rot)

### SEC-K-001: Keine Loeschfristen / Retention Policy fuer personenbezogene Daten

- **Schweregrad:** KRITISCH
- **OWASP:** A01:2021 Broken Access Control
- **STRIDE:** Information Disclosure
- **DSGVO:** Art. 5 Abs. 1 lit. e (Speicherbegrenzung), Art. 17 (Recht auf Loeschung)
- **Betroffene Dokumente:**
  - `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 163-182): User-Daten (`email`, `display_name`, `avatar_url`, `last_login_at`, `ip_address`) ohne definierte Loeschfristen
  - `spec/req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md` (Zeile 164-209): Membership-Daten, Invitation-Daten ohne Retention Policy
- **Beschreibung:** Keines der 24 REQ-Dokumente oder 10 NFR-Dokumente definiert Aufbewahrungsfristen fuer personenbezogene Daten. REQ-023 spezifiziert zwar Soft-Delete fuer User-Accounts (Zeile 472-476) und Cleanup unbestaetigter Accounts nach 7 Tagen (Zeile 555), aber es fehlt:
  - Loeschfrist fuer Soft-Deleted Accounts (wann wird endgueltig geloescht?)
  - Loeschfrist fuer Audit-Logs mit personenbezogenen Daten
  - Loeschfrist fuer IP-Adressen in RefreshToken-Collection
  - Loeschfrist fuer `last_login_at`, `failed_login_attempts`, `locked_until`
  - Loeschfrist fuer Sensor-Daten mit Personenbezug (CO2-Kurven, Bewegungsmuster)
- **Massnahme:** Retention-Policy-Dokument erstellen mit konkreten Fristen pro Datenkategorie. Celery-Tasks fuer automatische Bereinigung implementieren.

### SEC-K-002: IP-Adressen in RefreshToken-Collection ohne Zweckbindung und Loeschkonzept

- **Schweregrad:** KRITISCH
- **STRIDE:** Information Disclosure
- **DSGVO:** Art. 5 Abs. 1 lit. b (Zweckbindung), Art. 5 Abs. 1 lit. c (Datenminimierung)
- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 198-207)
- **Beschreibung:** Die `RefreshToken`-Collection speichert `ip_address: Optional[str]` und `device_info: Optional[str]` (User-Agent). Beide Felder sind personenbezogene Daten im Sinne der DSGVO. Der Zweck ist als "Fuer 'Aktive Sessions'-Uebersicht" angegeben (Zeile 203), aber:
  - Keine explizite Rechtsgrundlage definiert (Art. 6 DSGVO)
  - Keine Loeschfrist (IP-Adressen muessen nach Zweckerfuellung geloescht werden)
  - TTL-Index auf `expires_at` (Zeile 250) loescht nur abgelaufene Tokens, aber nicht die IP-Daten nach kuerzerer Frist
  - Kein Anonymisierungskonzept (z.B. IP-Truncation nach 7 Tagen)
- **Massnahme:** Rechtsgrundlage dokumentieren (berechtigtes Interesse Art. 6 Abs. 1 lit. f), IP-Adressen nach 7 Tagen auf Subnet truncieren (`192.168.1.xxx`), Device-Info nach Token-Ablauf loeschen.

### SEC-K-003: Keine DSGVO-Betroffenenrechte spezifiziert (Art. 15, 16, 17, 20)

- **Schweregrad:** KRITISCH
- **DSGVO:** Art. 15 (Auskunft), Art. 16 (Berichtigung), Art. 17 (Loeschung), Art. 20 (Datenportabilitaet)
- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md`, `spec/req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md`
- **Beschreibung:** REQ-023 spezifiziert Account-Loeschung (Zeile 508) und Profil-Aktualisierung (Zeile 468-469), aber es fehlen:
  - **Art. 15 Auskunftsrecht:** Kein API-Endpunkt fuer vollstaendigen Datenexport aller gespeicherten personenbezogenen Daten (User-Daten, Auth-Provider, Sessions, Memberships, erstellte Ressourcen)
  - **Art. 20 Datenportabilitaet:** Kein Export in maschinenlesbarem Format (JSON/CSV)
  - **Art. 16 Berichtigung:** Nur `display_name`, `avatar_url`, `locale`, `timezone` aenderbar (Zeile 469). E-Mail-Aenderung fehlt vollstaendig
  - **Art. 17 Loeschung:** Soft-Delete spezifiziert, aber Hard-Delete nach Ablauf fehlt
  - REQ-024 Zeile 858-861: "DSGVO-Export pro Tenant -> zukuenftig, nach Audit-Log" -- explizit aus Scope ausgeklammert
- **Massnahme:** REQ-025 "DSGVO-Betroffenenrechte" erstellen mit Endpunkten: `GET /users/me/data-export`, `POST /users/me/data-deletion-request`, `PATCH /users/me/email`. 30-Tage-Frist fuer Bearbeitung dokumentieren.

### SEC-K-004: CSRF-Schutz fuer Cookie-basierte Refresh-Token-Authentifizierung nicht spezifiziert

- **Schweregrad:** KRITISCH
- **OWASP:** A01:2021 Broken Access Control
- **STRIDE:** Elevation of Privilege
- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 82-87)
- **Beschreibung:** REQ-023 spezifiziert Refresh Tokens als `HttpOnly/Secure/SameSite=Strict Cookie` (Zeile 86). Der `SameSite=Strict`-Wert bietet guten CSRF-Schutz, ABER:
  - Der OAuth-Callback-Flow (`GET /auth/oauth/{provider_slug}/callback`, Zeile 494) ist ein Cross-Origin-Redirect von einem externen Provider. `SameSite=Strict` blockiert den Cookie bei Cross-Origin-Navigation, was den OAuth-Flow brechen koennte.
  - Keine explizite Spezifikation, ob `SameSite=Lax` stattdessen verwendet wird (was CSRF-Schutz fuer POST-Requests reduziert)
  - Der OAuth-State-Parameter (Redis, 5 Min TTL, Zeile 432-433) schuetzt den OAuth-Flow, aber nicht andere Cookie-basierte Endpunkte
  - `POST /auth/refresh` (Zeile 488) verwendet den Cookie -- CSRF-Schutz hier kritisch
- **Massnahme:** Explizit dokumentieren: `SameSite=Lax` fuer OAuth-Kompatibilitaet ODER `SameSite=Strict` mit separatem Token-Exchange nach OAuth-Redirect. Zusaetzlich Double-Submit-Cookie-Pattern oder CSRF-Token-Header fuer alle zustandsaendernden Cookie-Endpunkte spezifizieren.

### SEC-K-005: Sensordaten koennen Rueckschluesse auf Personen erlauben -- keine Datenschutz-Folgenabschaetzung

- **Schweregrad:** KRITISCH
- **DSGVO:** Art. 35 (Datenschutz-Folgenabschaetzung)
- **Betroffene Dokumente:**
  - `spec/req/REQ-005_Hybrid-Sensorik.md` (Zeile 27-35): CO2-Konzentration, Luftbewegung, Temperatur
  - `spec/req/REQ-018_Umgebungssteuerung.md` (Zeile 27-31): Aktor-Steuerungsdaten
- **Beschreibung:** Folgende Sensordaten koennen Rueckschluesse auf Anwesenheit und Verhalten von Personen erlauben:
  - **CO2-Kurven:** CO2-Konzentration in einem Raum korreliert direkt mit der Anzahl anwesender Personen und deren Aktivitaetsgrad
  - **Bewegungssensoren:** Luftbewegung (m/s) kann durch Personen verursacht werden
  - **Temperatur-Anomalien:** Koerperswaerme beeinflusst Raumtemperatur in kleinen Raeumen (Growzelte)
  - **Aktor-Logs:** Manuelle Overrides (REQ-018) dokumentieren implizit Anwesenheitszeiten
  - Diese Daten werden in TimescaleDB als Zeitreihen gespeichert (stack.md, Zeile 493-500) -- potenziell unbegrenzt
- **Massnahme:** Datenschutz-Folgenabschaetzung (DSFA) durchfuehren. Sensordaten als potenziell personenbezogen klassifizieren. Aggregierung (statt Rohdaten) nach definierter Frist. Downsampling-Policy in TimescaleDB spezifizieren (z.B. Stundenmittel nach 30 Tagen, Tagesmittel nach 1 Jahr).

---

## 3. Hohe Befunde (Orange)

### SEC-H-001: REQ-001 bis REQ-022 referenzieren keine Authentifizierungs-/Autorisierungsanforderungen [BEHOBEN]

- **Schweregrad:** HOCH
- **OWASP:** A01:2021 Broken Access Control
- **Betroffene Dokumente:** Alle REQ-001 bis REQ-022
- **Status:** **BEHOBEN** — Alle 22 REQ-Dokumente um Abschnitt "Authentifizierung & Autorisierung" ergaenzt. REQs mit Markdown-API-Tabellen (REQ-013, REQ-015, REQ-016, REQ-020, REQ-022) erhielten zusaetzlich eine Auth-Spalte inline. Auth-Werte: Nein (oeffentlich), Ja (authentifiziert), Mitglied (Tenant-Mitgliedschaft), Admin (Admin-Rolle).
- **Beschreibung:** Die 22 aelteren REQ-Dokumente wurden vor REQ-023/024 erstellt und enthielten keine Auth-Anforderungen.
- **Massnahme:** Alle REQ-Dokumente um eine Auth-Spalte in den API-Tabellen ergaenzt. Standardregel: Alle Endpunkte erfordern Authentifizierung, es sei denn explizit als public markiert (Seed-Daten, Health-Checks).

### SEC-H-002: Kein globales API-Rate-Limiting definiert -- nur fragmentarisch in REQ-023 und NFR-001

- **Schweregrad:** HOCH
- **OWASP:** A04:2021 Insecure Design
- **STRIDE:** Denial of Service
- **Betroffene Dokumente:**
  - `spec/nfr/NFR-001_Separation-of-Concerns.md` (Zeile 524-536): Rate Limiting 100/min per IP als Beispiel
  - `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 94): Login-Throttle 5 Versuche/15 Min
  - `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 717): "Alle Auth-Endpunkte haben Rate Limiting (100/min pro IP)"
- **Beschreibung:** Rate Limiting ist nur fragmentarisch spezifiziert:
  - NFR-001 zeigt ein Beispiel (100/min), aber als Code-Snippet, nicht als Anforderung
  - REQ-023 definiert Login-Throttle und Auth-Endpoint-Limits
  - Fuer alle anderen ~200 Endpunkte (REQ-001 bis REQ-022) ist kein Rate Limiting spezifiziert
  - Kein differenziertes Limiting (authentifiziert vs. anonym, Read vs. Write)
  - CSV-Import (REQ-012) ohne Upload-Groessenbegrenzung oder Rate-Limit
- **Massnahme:** Zentrale Rate-Limiting-Policy in NFR-001 oder als eigenes NFR-Dokument definieren: Anonym 30/min, Authentifiziert 100/min, Write-Operationen 20/min, Login 5/15min, CSV-Upload 5/Stunde + max. 10MB.

### SEC-H-003: Fehlende Eingabevalidierung -- keine maximalen Feldlaengen definiert

- **Schweregrad:** HOCH
- **OWASP:** A03:2021 Injection
- **STRIDE:** Tampering
- **Betroffene Dokumente:** Alle REQ-Dokumente mit Datenmodellen
- **Beschreibung:** Die Pydantic-Modelle in den REQ-Dokumenten definieren Typen (`str`, `int`, `float`), aber fast nie maximale Feldlaengen:
  - REQ-001: `scientific_name: str`, `common_names: list[str]` -- keine max. Laenge
  - REQ-002: `name: str` fuer Sites/Locations -- keine max. Laenge
  - REQ-004: `notes: Optional[str]` -- unbegrenzt
  - REQ-007: `notes: Optional[str]`, `photo_refs: list[str]` -- unbegrenzt
  - REQ-023: `display_name: str` -- keine max. Laenge (nur Passwort hat min. 10)
  - REQ-024: `description: Optional[str]` -- unbegrenzt
  - Ausnahme: REQ-024 TenantEngine (Zeile 400-401): "Min 2, Max 100 Zeichen" fuer Tenant-Name
- **Risiko:** Ohne Feldlaengen-Begrenzung sind ReDoS-Angriffe, Speicher-Exhaustion und DB-Overflow moeglich.
- **Massnahme:** Zentrale Feldlaengen-Policy definieren: name/title max. 200, description max. 5000, notes max. 10000, URL max. 2083, email max. 254, list max. 100 Eintraege. In Pydantic-Modellen mit `Field(max_length=...)` und `Field(max_items=...)` erzwingen.

### SEC-H-004: CalendarFeed-Token ohne Authentifizierung -- unautorisierter Datenzugriff moeglich

- **Schweregrad:** HOCH
- **OWASP:** A01:2021 Broken Access Control
- **Betroffenes Dokument:** `spec/req/REQ-015_Kalenderansicht.md` (Zeile 50-66)
- **Beschreibung:** CalendarFeeds verwenden einen URL-Token (32 Zeichen hex) fuer Zugriff durch externe Kalender-Apps. Probleme:
  - Token wird als Klartext gespeichert (`token: str`, Zeile 54), nicht als Hash
  - Kein Zusammenhang mit User-Authentifizierung spezifiziert (Zeile 64-66: "aktuell ohne Auth global")
  - Feed-URL (`/api/v1/calendar-feeds/{token}/events.ics`) exponiert potenziell alle Tasks, Phasentransitionen, Duenge- und Erntetermine
  - Token-Revocation nicht spezifiziert
  - Kein Rate-Limiting auf Feed-Endpunkt
- **Massnahme:** Token als SHA-256-Hash speichern. Feed an User-Kontext binden. Token-Rotation ermoeglichen. Rate-Limiting (10/min) auf Feed-Endpunkt. Feed-Token als "Langzeit-Bearer-Token" behandeln und in DSGVO-Dokumentation aufnehmen.

### SEC-H-005: InvenTree-Integration speichert API-Token ohne Verschluesselungsspezifikation

- **Schweregrad:** HOCH
- **OWASP:** A02:2021 Cryptographic Failures
- **Betroffenes Dokument:** `spec/req/REQ-016_InvenTree-Integration.md` (Zeile 53-54)
- **Beschreibung:** Die InvenTree-Integration verwendet Token-basierte Authentifizierung (`Authorization: Token <api_key>`). Es ist nicht spezifiziert:
  - Wie der API-Token gespeichert wird (Klartext? Verschluesselt?)
  - Ob der Token in der Datenbank oder als Kubernetes Secret verwaltet wird
  - Ob Token-Rotation unterstuetzt wird
  - REQ-023 spezifiziert Fernet/AES-256-Verschluesselung fuer OAuth-Secrets (Zeile 753), aber REQ-016 referenziert dieses Pattern nicht
- **Massnahme:** InvenTree-API-Token mit Fernet-Verschluesselung speichern (analog zu OIDC Client Secrets in REQ-023). Token-Rotation und Ablaufdatum unterstuetzen.

### SEC-H-006: MQTT-Kommunikation ohne Authentifizierung/Verschluesselung spezifiziert

- **Schweregrad:** HOCH
- **OWASP:** A02:2021 Cryptographic Failures
- **STRIDE:** Spoofing, Tampering, Information Disclosure
- **Betroffene Dokumente:**
  - `spec/req/REQ-005_Hybrid-Sensorik.md`: MQTT als Sensor-Datenquelle
  - `spec/req/REQ-018_Umgebungssteuerung.md` (Zeile 31): MQTT fuer direkte Aktor-Steuerung
- **Beschreibung:** MQTT wird als Kommunikationsprotokoll fuer Sensoren und Aktoren spezifiziert, aber:
  - Keine MQTT-Authentifizierung (Username/Password oder Zertifikate)
  - Keine TLS-Verschluesselung fuer MQTT-Verbindungen (Port 1883 vs. 8883)
  - Keine Topic-ACLs (wer darf welche Topics lesen/schreiben)
  - REQ-018 ermoeglicht direkte Aktor-Steuerung ueber MQTT -- ein kompromittierter MQTT-Client koennte Bewaesserung, Beleuchtung oder CO2-Zufuhr manipulieren
  - Potenzielle Sachschaeden durch unbefugte Aktor-Steuerung (Ueberschwemmung, Hitze, CO2-Vergiftung)
- **Massnahme:** MQTT-Security-Anforderungen definieren: TLS obligatorisch (Port 8883), Client-Zertifikate oder Username/Password, Topic-ACLs pro Device, keine Wildcard-Subscriptions fuer Steuerungstopics.

### SEC-H-007: Audit-Log nur als Idee erwaehnt -- keine Spezifikation fuer sicherheitsrelevante Ereignisse

- **Schweregrad:** HOCH
- **OWASP:** A09:2021 Security Logging and Monitoring Failures
- **Betroffene Dokumente:**
  - `spec/nfr/NFR-001_Separation-of-Concerns.md` (Zeile 984-1026): Audit-Trail als Beispiel-Code, nicht als Anforderung
  - `spec/req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md` (Zeile 828): "Audit-Log -> zukuenftig"
- **Beschreibung:** Sicherheitsrelevante Ereignisse werden nicht systematisch geloggt:
  - Fehlgeschlagene Login-Versuche (REQ-023 tracked `failed_login_attempts`, aber kein permanentes Log)
  - Rollenweaenderungen (REQ-024 -- wer hat wem Admin-Rechte gegeben?)
  - Datenloeschungen (insbesondere Tenant-Loeschung mit allen Ressourcen)
  - OIDC-Provider-Konfigurationsaenderungen (Admin-Endpunkte)
  - Account-Linking/-Unlinking
  - Token-Revocations
  - NFR-001 zeigt Audit-Trail nur als technisches Beispiel (Zeile 984-1026), nicht als verbindliche Anforderung
- **Massnahme:** Security-Audit-Log als verbindliche Anforderung definieren. Mindestens: Auth-Events (Login/Logout/Failure/Lockout), Autorisierungsaenderungen (Rollen, Memberships), Datenloeschungen, Admin-Aktionen.

### SEC-H-008: Drittanbieter-API-Aufrufe ohne Datenschutz-Bewertung

- **Schweregrad:** HOCH
- **DSGVO:** Art. 28 (Auftragsverarbeitung), Art. 44-49 (Datenuebermittlung in Drittlaender)
- **Betroffene Dokumente:**
  - `spec/req/REQ-011_Externe-Stammdatenanreicherung.md` (Zeile 30-36): GBIF, Perenual, OpenFarm, Trefle, Otreeba
  - `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 93): HaveIBeenPwned API
  - `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 56-63): Google, GitHub, Apple als OIDC-Provider
- **Beschreibung:** Folgende Drittanbieter-Dienste werden genutzt, ohne Datenschutz-Bewertung:
  - **HaveIBeenPwned:** Sendet SHA-1-Prefix des Passworts an externen Dienst (k-Anonymity). Ist als "optional" markiert, aber keine Einwilligungslogik spezifiziert.
  - **GBIF/Perenual/Trefle/Otreeba:** Senden Anfragen mit IP-Adresse des Servers. Kein AVV noetig, da nur botanische Daten abgefragt werden -- aber Dokumentation fehlt.
  - **Google/GitHub/Apple OAuth:** Leiten Nutzer an US-Dienste weiter. EU-US Data Privacy Framework relevant. Keine Datenschutzhinweise spezifiziert.
  - **QR-Code-Generierung (REQ-007, Zeile 409):** `api.qrserver.com` -- externer Dienst, sendet Batch-ID an Drittanbieter. Datenschutzrelevant falls Batch-IDs personenbezogene Informationen enthalten.
- **Massnahme:** Datenschutz-Bewertung pro Drittanbieter erstellen. QR-Code-Generierung auf lokale Bibliothek umstellen (z.B. `python-qrcode`). HaveIBeenPwned-Nutzung im Datenschutzhinweis erwaehnen. AVV-Pflicht fuer jeden Dienst pruefen.

### SEC-H-009: Account-Enumeration ueber Registrierungs-Endpunkt moeglich

- **Schweregrad:** HOCH
- **OWASP:** A01:2021 Broken Access Control
- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md`
- **Beschreibung:** REQ-023 spezifiziert Enumeration-Schutz fuer Passwort-Reset (Zeile 423: "KEIN Fehler wenn E-Mail nicht existiert"), aber:
  - **Registrierung (Zeile 406-411):** `register_local()` prueft E-Mail-Eindeutigkeit und gibt bei Duplikat einen Fehler zurueck. Damit kann ein Angreifer herausfinden, ob eine E-Mail registriert ist.
  - **Einladung (REQ-024):** E-Mail-Einladungen koennen an beliebige Adressen gesendet werden -- kein Enumeration-Problem, aber Spam-Risiko
  - Login-Endpunkt ist nicht explizit spezifiziert bezueglich Enumeration-Schutz (unterschiedliche Fehlermeldungen fuer "User nicht gefunden" vs. "Passwort falsch"?)
- **Massnahme:** Registrierung: Bei existierender E-Mail eine generische Antwort senden ("Wenn diese E-Mail nicht registriert ist, erhalten Sie eine Verifizierungs-E-Mail"). Login: Einheitliche Fehlermeldung "Anmeldedaten ungueltig" statt spezifischer Fehler.

---

## 4. Mittlere Befunde (Gelb)

### SEC-M-001: Access Token enthaelt personenbezogene Daten (email, display_name)

- **Schweregrad:** MITTEL
- **DSGVO:** Art. 5 Abs. 1 lit. c (Datenminimierung)
- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 85, 334)
- **Beschreibung:** Der Access Token enthaelt `email` und `display_name` im Payload. JWTs werden clientseitig im Memory gespeichert und koennen von JavaScript gelesen werden (nicht HttpOnly). Dies exponiert personenbezogene Daten:
  - `email` ist direkt personenbezogen
  - `display_name` kann den vollen Namen enthalten
  - `tenant_roles` offenbart Organisationszugehoerigkeit
  - JWT-Payload ist Base64-kodiert, nicht verschluesselt -- jeder mit Zugriff auf den Token kann die Daten lesen
- **Massnahme:** Access Token auf `sub` (user_key), `tenant_roles`, `exp`, `iat`, `type` reduzieren. `email` und `display_name` aus dem Token entfernen und bei Bedarf ueber `/users/me` abfragen. Alternativ: JWE (verschluesselte JWTs) evaluieren.

### SEC-M-002: HS256-Algorithmus fuer JWT -- Shared Secret statt asymmetrische Kryptographie

- **Schweregrad:** MITTEL
- **OWASP:** A02:2021 Cryptographic Failures
- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 335)
- **Beschreibung:** JWT-Signierung verwendet HS256 (HMAC-SHA256) mit einem Shared Secret. Probleme:
  - Bei Microservice-Architektur (NFR-001, Zeile 1201-1214) muesste jeder Service das gleiche Secret kennen
  - Kein Token-Verifier kann Tokens verifizieren, ohne das Signing-Secret zu kennen
  - RS256/ES256 (asymmetrisch) wuerde erlauben, dass nur der Auth-Service signiert und alle anderen Services mit dem Public Key verifizieren
- **Massnahme:** Langfristig auf RS256 oder ES256 migrieren. Kurzfristig: JWT-Secret-Rotation spezifizieren (Key-Rotation-Strategie), Secret-Laenge >= 256 Bit dokumentieren.

### SEC-M-003: Keine explizite Spezifikation von Content-Security-Policy (CSP) und Security-Headern

- **Schweregrad:** MITTEL
- **OWASP:** A05:2021 Security Misconfiguration
- **Betroffene Dokumente:** `spec/nfr/NFR-001_Separation-of-Concerns.md`, `spec/nfr/NFR-002_Kubernetes-Plattform.md`
- **Beschreibung:** Keine der Spezifikationen definiert HTTP-Security-Header:
  - `Content-Security-Policy` (XSS-Schutz)
  - `Strict-Transport-Security` (HSTS)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy`
  - `Permissions-Policy`
  - NFR-001 definiert CORS (Zeile 500-520), aber keine weiteren Security-Header
- **Massnahme:** Security-Header-Policy in NFR-001 oder NFR-002 aufnehmen. Mindestens: HSTS, CSP, X-Content-Type-Options, X-Frame-Options.

### SEC-M-004: Kubernetes-Deployments ohne Security Contexts spezifiziert

- **Schweregrad:** MITTEL
- **Betroffene Dokumente:**
  - `spec/nfr/NFR-002_Kubernetes-Plattform.md`: Kubernetes-Manifests
  - `spec/stack.md` (Zeile 170-214): Dockerfile mit non-root User
- **Beschreibung:** stack.md definiert einen non-root User in der Dockerfile (Zeile 193-206, `USER appuser`), aber die Kubernetes-Deployments in NFR-002 enthalten keine `securityContext`:
  - Kein `runAsNonRoot: true`
  - Kein `readOnlyRootFilesystem: true`
  - Kein `allowPrivilegeEscalation: false`
  - Keine `capabilities.drop: ["ALL"]`
  - Keine `seccompProfile`
  - Network Policies nicht definiert (Pod-zu-Pod-Kommunikation uneingeschraenkt)
- **Massnahme:** Security Contexts in alle Kubernetes-Manifests aufnehmen. Network Policies definieren (Backend -> ArangoDB/Redis erlaubt, Frontend -> Backend erlaubt, alle anderen blockiert).

### SEC-M-005: Sentry-Integration koennte personenbezogene Daten an US-Dienst senden

- **Schweregrad:** MITTEL
- **DSGVO:** Art. 44-49 (Drittlandtransfer)
- **Betroffenes Dokument:** `spec/nfr/NFR-001_Separation-of-Concerns.md` (Zeile 794-833)
- **Beschreibung:** NFR-001 spezifiziert Sentry fuer Frontend Error Tracking (Zeile 796-807). Sentry kann bei Fehler-Reports Folgendes uebertragen:
  - URL mit Tenant-Slug (`/t/gruene-oase/...`)
  - User-Agent
  - IP-Adresse
  - Session-Replay (Zeile 806: `replaysSessionSampleRate: 0.1`) -- zeichnet Nutzerinteraktionen auf
  - Error Context kann API-Response-Daten enthalten
- **Massnahme:** Sentry-Self-Hosting evaluieren oder Sentry-EU-Rechenzentrum nutzen. Session-Replay nur mit expliziter Einwilligung. PII-Scrubbing konfigurieren. Alternative: GlitchTip als DSGVO-konformer Sentry-Fork.

### SEC-M-006: Onboarding-State ohne User-Zuordnung (Single-User-Artefakt)

- **Schweregrad:** MITTEL
- **OWASP:** A01:2021 Broken Access Control
- **Betroffenes Dokument:** `spec/req/REQ-020_Onboarding-Wizard.md` (Zeile 65-74)
- **Beschreibung:** `OnboardingState` und `UserPreference` Collections haben keinen expliziten User-Bezug (kein `user_key`-Feld). REQ-020 Zeile 38 sagt: "der Wizard setzt ein existierendes (ggf. anonymes) System voraus". Dies ist ein Single-User-Artefakt, das mit Multi-Tenancy (REQ-024) inkompatibel ist:
  - Ohne `user_key` kann jeder Nutzer die Onboarding-Einstellungen anderer lesen/aendern
  - `experience_level` beeinflusst UI-Darstellung (REQ-021) -- muss pro User gespeichert werden
- **Massnahme:** `user_key` als Pflichtfeld in `onboarding_states` und `user_preferences` aufnehmen. Alternativ in `users`-Collection als embedded Feld.

### SEC-M-007: Kein Einwilligungsmanagement (TTDSG) fuer Cookies und lokale Speicherung

- **Schweregrad:** MITTEL
- **Rechtlich:** TTDSG ss 25 (Telemedien-Gesetz)
- **Betroffene Dokumente:**
  - `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md`: Refresh Token als Cookie
  - UI-NFR-011: localStorage fuer Kiosk-Modus-Praeferenz
  - UI-NFR-012: IndexedDB und Service Worker Cache
  - Frontend allgemein: localStorage fuer Theme, Tenant, Sprache
- **Beschreibung:** Kein Dokument spezifiziert ein Cookie-/Consent-Banner:
  - Refresh Token als HttpOnly Cookie ist technisch notwendig (keine Einwilligung noetig)
  - localStorage fuer Theme/Sprache ist ebenfalls funktional
  - ABER: Sentry-Tracking (NFR-001), Session-Replay, Fehler-Reporting erfordern Einwilligung
  - PWA Service Worker Cache (UI-NFR-012) speichert Inhalte auf dem Geraet
- **Massnahme:** Zwischen technisch notwendigen (keine Einwilligung) und Analyse-/Tracking-Cookies/-Speicher unterscheiden. Cookie-Banner fuer Sentry/Analytics implementieren. Dokumentation der Rechtsgrundlagen pro Speicher-Nutzung.

### SEC-M-008: CSV-Import ohne Sicherheitsbeschraenkungen

- **Schweregrad:** MITTEL
- **OWASP:** A03:2021 Injection
- **Betroffenes Dokument:** `spec/req/REQ-012_Stammdaten-Import.md` (Zeile 17-27)
- **Beschreibung:** REQ-012 spezifiziert CSV-Import ohne Sicherheitsbeschraenkungen:
  - Keine maximale Dateigroesse definiert
  - Keine maximale Zeilenanzahl
  - Keine Einschraenkung auf bestimmte Rollen (Admin-Only?)
  - CSV-Injection nicht adressiert (z.B. `=CMD()` in Zellen)
  - Encoding-Handling (UTF-8) spezifiziert, aber keine Pruefung auf binaere Inhalte
- **Massnahme:** Admin-Only-Berechtigung fuer CSV-Import. Maximale Dateigroesse (10 MB). Maximale Zeilenanzahl (10.000). CSV-Injection-Sanitisierung (Felder die mit `=`, `+`, `-`, `@` beginnen, escapen). MIME-Type-Validierung.

---

## 5. Hinweise & Best Practices (Gruen)

### SEC-G-001: Bcrypt Cost Factor 12 -- gute Wahl, Upgrade-Pfad dokumentieren

- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 92, 316-317)
- **Bewertung:** Bcrypt mit Cost Factor 12 entspricht der NIST 800-63B-Empfehlung (2023) und OWASP-Empfehlung (Minimum 10). Gut: Passwort-Policy folgt NIST-Richtlinien (Laenge > Komplexitaet, Zeile 91). Empfehlung: Upgrade-Pfad auf Argon2id dokumentieren fuer zukuenftige Migration.

### SEC-G-002: Token-Rotation bei Refresh -- vorbildlich

- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 86, 206-207)
- **Bewertung:** Token-Rotation mit `replaced_by`-Tracking ist Best Practice. Erkennung von Token-Reuse (wenn ein bereits rotiertes Token verwendet wird) sollte alle Sessions des Users invalidieren (Compromise-Detection).

### SEC-G-003: PKCE fuer alle OAuth-Flows -- vorbildlich

- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 714)
- **Bewertung:** PKCE (S256) fuer alle OAuth-Flows ist gemaess OAuth 2.1 Best Current Practice obligatorisch. Gut spezifiziert.

### SEC-G-004: NFR-006 Fehlerbehandlung -- vorbildliches Information-Leakage-Konzept

- **Betroffenes Dokument:** `spec/nfr/NFR-006_API-Fehlerbehandlung.md` (Zeile 411-512)
- **Bewertung:** Die Spezifikation der verbotenen vs. erlaubten Fehlerinhalte (Abschnitt 6.2) ist aeusserst gruendlich. Die Kategorisierung in Software-Infos, Infrastruktur-Infos und Geschaeftslogik-Interna ist vorbildlich. Der Enforcement-Abschnitt (Zeile 506-511) mit CI-Pipeline-Checks ist Best Practice.

### SEC-G-005: Refresh Token als SHA-256-Hash gespeichert -- korrekt

- **Betroffenes Dokument:** `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` (Zeile 201, 337-339, 712)
- **Bewertung:** SHA-256-Hashing von Refresh Tokens vor Speicherung verhindert Token-Diebstahl bei DB-Kompromittierung. Gut: Auch Einladungstokens (REQ-024, Zeile 192) und Verifizierungstokens (REQ-023, Zeile 173) werden gehasht.

### SEC-G-006: Container mit Non-Root-User -- gute Basis

- **Betroffenes Dokument:** `spec/stack.md` (Zeile 193-206)
- **Bewertung:** Dockerfile verwendet Multi-Stage-Build und non-root User (`appuser`, UID 1000). Dies sollte durch Kubernetes Security Contexts verstaerkt werden (siehe SEC-M-004).

---

## 6. Datensparsamkeits-Matrix

| REQ | Erfasste Daten | Personenbezogen | Zweck definiert | Loeschfrist | Bewertung |
|-----|---------------|-----------------|-----------------|-------------|-----------|
| REQ-001 | Botanische Stammdaten | Nein | Ja | N/A | OK |
| REQ-002 | Standortdaten (GPS) | Nein* | Ja | Nein | *GPS kann Wohnadresse offenbaren |
| REQ-003 | Phasendaten | Nein | Ja | N/A | OK |
| REQ-004 | Duengedaten, Feeding-Events | Nein | Ja | N/A | OK |
| REQ-005 | Sensordaten (CO2, Temp, RH, Bewegung) | Indirekt** | Ja | Nein | **CO2/Bewegung = Anwesenheitsdaten |
| REQ-006 | Tasks mit `assigned_to` (User-ID), Erledigungszeiten | Ja | Ja | Nein | Verhaltens-Tracking |
| REQ-007 | `harvester` (User-ID), Erntezeiten | Ja | Ja | Nein | Arbeitszeiterfassung |
| REQ-008 | `observer` (User-ID), Beobachtungszeiten | Ja | Ja | Nein | Arbeitszeiterfassung |
| REQ-009 | Dashboard-Configs, `created_by` (User-ID) | Ja | Ja | Nein | Nutzungsmuster |
| REQ-010 | `inspector` (User-ID), Inspektionszeiten | Ja | Ja | Nein | Arbeitszeiterfassung |
| REQ-011 | Server-IP bei API-Aufrufen | Nein | Ja | N/A | OK (kein Personenbezug) |
| REQ-012 | Import-Jobs mit `uploaded_by` | Ja | Ja | Nein | - |
| REQ-013 | Planting-Run-Daten | Nein | Ja | N/A | OK |
| REQ-014 | Tank-Daten | Nein | Ja | N/A | OK |
| REQ-015 | CalendarFeed mit Token, `last_accessed_at` | Ja | Ja | Nein | Nutzungsverhalten |
| REQ-016 | InvenTree API-Token | Ja (Credential) | Ja | Nein | Credential-Schutz noetig |
| REQ-017 | Vermehrungsdaten | Nein | Ja | N/A | OK |
| REQ-018 | Aktor-Logs, manuelle Overrides | Indirekt | Ja | Nein | Anwesenheit/Verhalten |
| REQ-019 | Substratdaten | Nein | Ja | N/A | OK |
| REQ-020 | Onboarding-Praefeenzen | Ja | Ja | Nein | Nutzer-Profiling |
| REQ-021 | Erfahrungsstufe | Ja | Ja | Nein | Nutzer-Profiling |
| REQ-022 | Care-Actions mit Zeitstempeln | Indirekt | Ja | Nein | Verhaltens-Tracking |
| REQ-023 | E-Mail, Name, Avatar, IP, Device-Info, Login-Zeiten | Ja | Teilweise | Teilweise*** | ***7 Tage fuer unbestaetigte Accounts |
| REQ-024 | Memberships, `invited_by`, `display_name_override` | Ja | Ja | Nein | - |

---

## 7. Autorisierungs-Matrix (Soll-Zustand nach REQ-024)

| Ressource | Admin | Grower | Viewer | Global | Spezifiziert |
|-----------|-------|--------|--------|--------|-------------|
| **Globale Stammdaten** | | | | | |
| BotanicalFamily (CRUD) | RW | RW | R | Ja | Nein -- keine Auth in REQ-001 |
| Species (CRUD) | RW | RW | R | Ja | Nein |
| Cultivar (CRUD) | RW | RW | R | Ja | Nein |
| Pests/Diseases/Treatments | RW | RW | R | Ja | Nein |
| **Tenant-scoped Ressourcen** | | | | | |
| Sites | RW | RW* | R | Nein | REQ-024 (Zeile 421-433) |
| Locations | RW | RW* | R | Nein | REQ-024 |
| PlantInstances | RW | RW* | R | Nein | Nein -- nicht explizit |
| PlantingRuns | RW | RW | R | Nein | Nein |
| Tasks | RW | RW | R | Nein | Nein -- `assigned_to` ohne Auth |
| HarvestBatches | RW | RW | R | Nein | Nein |
| Tanks | RW | RW | R | Nein | Nein |
| Fertilizers | RW | RW | R | Nein | Nein |
| NutrientPlans | RW | RW | R | Nein | Nein |
| Inspections | RW | RW | R | Nein | Nein |
| CalendarFeeds | RW | RW | R | Nein | Nein |
| **Tenant-Verwaltung** | | | | | |
| Tenant-Settings | RW | - | - | Nein | REQ-024 (Zeile 581) |
| Members | RW | - | - | Nein | REQ-024 (Zeile 584-591) |
| Invitations | RW | - | - | Nein | REQ-024 (Zeile 593-601) |
| Assignments | RW | - | - | Nein | REQ-024 (Zeile 603-610) |
| **System-Administration** | | | | | |
| OIDC-Provider-Config | System-Admin | - | - | Ja | REQ-023 (Zeile 510-519) |
| User-Admin | Nur eigenes Profil | - | - | Ja | REQ-023 (Zeile 496-508) |

*Grower: RW nur auf zugewiesene + Gemeinschafts-Locations (REQ-024, Zeile 421-433)*

**Fazit:** Von ca. 200 spezifizierten API-Endpunkten haben nur die ~41 Endpunkte aus REQ-023 (23) und REQ-024 (18) definierte Authentifizierungs-/Autorisierungsanforderungen. Alle anderen Endpunkte (REQ-001 bis REQ-022) muessen nachtraeglich um Auth-Anforderungen ergaenzt werden.

---

## 8. DSGVO-Checkliste

| Betroffenenrecht | DSGVO-Artikel | Spezifiziert | Dokument | Status |
|-----------------|---------------|-------------|----------|--------|
| Informationspflicht | Art. 13, 14 | Nein | - | Nicht adressiert |
| Auskunftsrecht | Art. 15 | Nein | - | Kein Datenexport-Endpunkt |
| Recht auf Berichtigung | Art. 16 | Teilweise | REQ-023 Zeile 468-469 | Nur Name/Avatar/Locale/Timezone, E-Mail fehlt |
| Recht auf Loeschung | Art. 17 | Teilweise | REQ-023 Zeile 472-476, 508 | Soft-Delete, kein Hard-Delete nach Frist |
| Recht auf Einschraenkung | Art. 18 | Nein | - | Nicht adressiert |
| Recht auf Datenportabilitaet | Art. 20 | Nein | - | Kein Export in maschinenlesbarem Format |
| Widerspruchsrecht | Art. 21 | Nein | - | Nicht adressiert |
| Datenschutz durch Technikgestaltung | Art. 25 | Teilweise | NFR-006 | Fehler-Minimierung ja, aber kein Privacy by Design |
| Verzeichnis von Verarbeitungstaetigkeiten | Art. 30 | Nein | - | Nicht adressiert |
| Datenschutz-Folgenabschaetzung | Art. 35 | Nein | - | Noetig fuer Sensor-/Verhaltensdaten |
| Auftragsverarbeitung | Art. 28 | Nein | - | AVV fuer Sentry, OIDC-Provider, HIBP fehlt |
| Datenuebermittlung Drittland | Art. 44-49 | Nein | - | Google/GitHub/Apple/Sentry = US-Dienste |
| Einwilligung (ePrivacy/TTDSG) | TTDSG ss 25 | Nein | - | Kein Cookie-/Consent-Banner |
| Datenschutzbeauftragter | Art. 37 | Nein | - | Bei >20 MA mit regelm. Datenverarbeitung |

---

## 9. Priorisierte Massnahmenliste

| Prio | ID | Massnahme | Schweregrad | Aufwand | Betroffene Dokumente |
|------|-----|----------|-------------|---------|---------------------|
| 1 | SEC-K-003 | DSGVO-Betroffenenrechte spezifizieren (Art. 15, 16, 17, 20) | Kritisch | Hoch | Neues REQ-025 |
| 2 | SEC-K-001 | Retention Policy / Loeschfristen definieren | Kritisch | Mittel | Alle REQ, neues Policy-Dokument |
| 3 | SEC-K-004 | CSRF-Schutz fuer Cookie-basierte Auth klaeren | Kritisch | Mittel | REQ-023 |
| 4 | SEC-K-002 | IP-Adressen-Speicherung: Zweckbindung, Anonymisierung | Kritisch | Niedrig | REQ-023 |
| 5 | SEC-K-005 | Datenschutz-Folgenabschaetzung fuer Sensordaten | Kritisch | Mittel | REQ-005, REQ-018 |
| 6 | SEC-H-001 | Auth-Anforderungen in REQ-001 bis REQ-022 nachtragen | Hoch | Hoch | 22 REQ-Dokumente | **BEHOBEN** |
| 7 | SEC-H-006 | MQTT-Security spezifizieren (TLS, Auth, ACLs) | Hoch | Mittel | REQ-005, REQ-018 |
| 8 | SEC-H-002 | Globale Rate-Limiting-Policy definieren | Hoch | Niedrig | NFR-001 oder neues Dokument |
| 9 | SEC-H-003 | Maximale Feldlaengen in Pydantic-Modellen definieren | Hoch | Mittel | Alle REQ mit Datenmodellen |
| 10 | SEC-H-007 | Security-Audit-Log als verbindliche Anforderung | Hoch | Mittel | Neues NFR oder REQ-024 erweitern |
| 11 | SEC-H-004 | CalendarFeed-Token-Sicherheit verbessern | Hoch | Niedrig | REQ-015 |
| 12 | SEC-H-005 | InvenTree-Token-Verschluesselung spezifizieren | Hoch | Niedrig | REQ-016 |
| 13 | SEC-H-008 | Drittanbieter-Datenschutz-Bewertung erstellen | Hoch | Mittel | REQ-011, REQ-023, REQ-007 |
| 14 | SEC-H-009 | Account-Enumeration-Schutz bei Registrierung | Hoch | Niedrig | REQ-023 |
| 15 | SEC-M-001 | Personenbezogene Daten aus JWT-Payload entfernen | Mittel | Niedrig | REQ-023 |
| 16 | SEC-M-002 | JWT-Algorithmus-Upgrade-Pfad dokumentieren (HS256 -> RS256) | Mittel | Niedrig | REQ-023 |
| 17 | SEC-M-003 | HTTP-Security-Header spezifizieren (CSP, HSTS, etc.) | Mittel | Niedrig | NFR-001 |
| 18 | SEC-M-004 | Kubernetes Security Contexts und Network Policies | Mittel | Mittel | NFR-002 |
| 19 | SEC-M-005 | Sentry DSGVO-Konformitaet pruefen / Self-Hosting | Mittel | Mittel | NFR-001 |
| 20 | SEC-M-006 | User-Zuordnung fuer OnboardingState/UserPreference | Mittel | Niedrig | REQ-020 |
| 21 | SEC-M-007 | Cookie-/Consent-Banner spezifizieren | Mittel | Mittel | Neues UI-NFR |
| 22 | SEC-M-008 | CSV-Import-Sicherheit (Groesse, Rollen, Injection) | Mittel | Niedrig | REQ-012 |

---

## 10. Zusammenfassung

### Staerken

1. **REQ-023 (Authentifizierung)** ist umfassend und folgt aktuellen Best Practices (Bcrypt, PKCE, Token-Rotation, Enumeration-Schutz bei Reset, OIDC Discovery).
2. **REQ-024 (Autorisierung)** definiert ein klares 3-Rollen-Modell mit Tenant-Isolation und Location-Assignment-basierter Sichtbarkeit.
3. **NFR-006 (Fehlerbehandlung)** hat ein vorbildliches Konzept gegen Information Leakage mit expliziten Verbotslisten und CI-Enforcement.
4. **Kryptographische Entscheidungen** sind ueberwiegend korrekt (Bcrypt >= 12, SHA-256 fuer Token-Hashes, AES-256/Fernet fuer Secrets, PKCE S256).
5. **Container-Sicherheit** mit Non-Root-User im Dockerfile als gute Basis.

### Kritische Luecken

1. **DSGVO-Konformitaet ist der groesste Schwachpunkt.** Betroffenenrechte sind kaum spezifiziert, Loeschfristen fehlen vollstaendig, keine Datenschutz-Folgenabschaetzung fuer Sensordaten, kein Verzeichnis von Verarbeitungstaetigkeiten.
2. **Auth-Gap zwischen REQ-023/024 und allen anderen REQs.** 22 von 24 REQ-Dokumenten definieren keine Authentifizierungs-/Autorisierungsanforderungen. Dies ist historisch bedingt (aeltere Dokumente), muss aber vor der Implementierung geschlossen werden.
3. **IoT-Sicherheit (MQTT) ist nicht spezifiziert.** Bei einem System, das physische Aktoren steuern kann (Bewaesserung, CO2, Beleuchtung), ist fehlende MQTT-Sicherheit ein potenzielles Sicherheitsrisiko mit physischen Konsequenzen.
4. **Datensparsamkeit und Zweckbindung** sind nicht systematisch adressiert. Viele Collections erfassen User-IDs und Zeitstempel, ohne den datenschutzrechtlichen Zweck und die Aufbewahrungsdauer zu dokumentieren.

### Empfohlene naechste Schritte

1. **Sofort (vor v1.1-Implementierung):** Retention-Policy erstellen, CSRF-Schutz klaeren, Auth-Anforderungen in REQ-001-022 nachtragen
2. **Kurzfristig (parallel zu v1.1):** DSGVO-Betroffenenrechte als REQ-025 spezifizieren, MQTT-Security definieren, Security-Audit-Log spezifizieren
3. **Mittelfristig (nach v1.1):** Datenschutz-Folgenabschaetzung durchfuehren, HTTP-Security-Header implementieren, Kubernetes Security Contexts vervollstaendigen

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Erstbewertung
**Datum**: 2026-02-27
**Naechstes Review**: Nach Umsetzung der kritischen Massnahmen
