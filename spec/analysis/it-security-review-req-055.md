# IT-Security Anforderungsreview — REQ-055 v1.1 (Plant Identity / Plant Social)

**Erstellt von:** IT-Security-Experte (Subagent `security-requirements-reviewer`, Kamerplanter-Spezialisierung)
**Datum:** 2026-10-04
**Fokus:** Öffentliche Endpunkte · OAuth/Token · Tenant-Isolation/RBAC · Datenschutz · Anti-Spam/Abuse · KI · Ereignis-Architektur · Provider-Daten/SSRF
**Analysiertes Dokument:** `spec/req/REQ-055_Plant-Identity-Plant-Social.md` v1.1 (§1–§37, Anhänge A–L, vollständig gelesen)
**Referenz-Sicherheitsspezifikationen:** REQ-023 (Auth), REQ-024 (Mandanten), REQ-025 + NFR-011 (DSGVO/Retention), REQ-051 (Tagebuch), REQ-052/NFR-013 (Fotos/EXIF), NFR-006 (Fehler), NFR-007 §4.7 (Prompt-Injection)
**Im Code nachgemessen (2026-10-04):**
- `src/backend/app/data_access/storage/local_fs_adapter.py:640-668`: Das Download-Token ist `base64url(JSON).HMAC`. Der Payload ist **lesbar** und enthält `key` (`t/{tenant_key}/…`), `tenant_key` und `aid`.
- `src/backend/app/api/v1/attachments/token_router.py:71`: Antworten tragen `Cache-Control: private, max-age=86400`.
- `src/backend/app/data_access/external/redis_oauth_state.py`: Der State ist ein reiner Redis-Schlüssel (Präfix `kp:oauth:state:`) **ohne Bindung an die Browser-Sitzung**.
- `src/backend/app/common/url_safety.py:238`: DNS-Rebinding gilt ausdrücklich als Restrisiko, weil die IP nicht festgehalten wird.
- `spec/nfr/NFR-011`: R-26/R-27 sind belegt, R-28 ist frei.

**Annahmen, die vor Welle 3 nachzumessen sind (zu O-02):**
- (a) Mastodon überspringt den Zustimmungsdialog, wenn für dieselbe App und dieselben Scopes schon ein gültiges Token des Nutzers existiert, solange `force_login` nicht gesetzt ist.
- (b) Mastodon hält `Idempotency-Key`-Einträge etwa 1 Stunde vor.

Beides habe ich aus dem Mastodon-Verhalten und der Doku abgeleitet. Es ist nicht im Mock bestätigt.

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Datensparsamkeit | ⭐⭐⭐⭐ | Allowlist-Projektion, Payload-Klassen und `since_precision` sind vorbildlich. Zwei Freitext-Kanäle werden trotzdem automatisch öffentlich: `milestone.title` und `caption` als Alt-Text (S-007). |
| Authentifizierung | ⭐⭐⭐ | Der OAuth-Callback ist nicht an die Browser-Sitzung gebunden, die den Flow gestartet hat. Das ermöglicht Account-Linking-CSRF (S-001). Sonst solide: PKCE, One-Time-State, kein Code in der URL. |
| Autorisierung / RBAC | ⭐⭐⭐ | Die Matrix ist vollständig ausformuliert. Eine Gärtnerin kann die Freigabe durch die Leitung aber umgehen (S-005). Datenabhängige Regeln („Ersteller", `review_by`) lassen sich über `require_permission` nicht ausdrücken. |
| Tenant-Isolation | ⭐⭐⭐ | Der Anker Pflanze ist richtig gewählt. Querverweise im Body (`connection_key`, `identity_key`, `event_key`) und in verschachtelten Pfaden sind nicht als Pflichtauflösung spezifiziert (S-006). Die signierten Bild-URLs legen `tenant_key` offen (S-002). |
| KI/AI-Sicherheit | ⭐⭐⭐⭐ | Faktenliste plus Fact-Check, der verwirft statt repariert. Das ist stark. Die Aussage „strukturell unmöglich" stimmt nicht ganz (S-020). Nicht MVP. |
| API-Sicherheit | ⭐⭐⭐ | Die 404-Gleichbehandlung ist unvollständig und widersprüchlich (S-011). `unlisted` ist erratbar (S-004). Authentifizierte Endpunkte mit Aufwand oder ausgehendem Netzverkehr haben keine Limits (S-013). |
| Verschlüsselung | ⭐⭐⭐⭐ | Fernet mit Startup-Guard, Guard für tokenfreie Responses. Offen sind Schlüsseltrennung und Rotation des App-Secrets (S-022). |
| DSGVO-Konformität | ⭐⭐⭐ | Export, Erasure und Retention sind vorgesehen. Lücken: `plant_events.actor.user_key` (S-008), unklare Rechtsgrundlage und Consent-Träger, Fotos anderer Mitglieder (S-019), fehlende Fristen (S-023). |
| Infrastruktur-Sicherheit | ⭐⭐⭐⭐ | Kein Inbound, Egress-NetworkPolicy, eigene Queue, Kill-Switch. Offen sind DNS-Rebinding bei späteren Task-Aufrufen (S-014) und die Semantik des Kill-Switch (S-021). |

Für eine v1.1 ist das Dokument auffallend sicherheitsbewusst. Die Kernentscheidungen tragen:
- Allowlist statt Blocklist
- kein Inbound
- keine Follow-/Reply-Methoden im Port
- Bot-Flag-Pflicht
- Review-Pflicht für die ersten zehn Posts
- Celery-Tasks bekommen nur Keys

Die Schwächen liegen an den Nahtstellen:
- zwischen OAuth-Callback und Browser-Sitzung
- zwischen bestehender Attachment-Infrastruktur und öffentlicher Projektion (Token-Inhalt, EXIF)
- zwischen Rollenmatrix und Freigabe-Governance
- zwischen Body-Referenzen und dem Anker-Prinzip

Vor Welle 2 müssen S-002, S-003, S-004, S-007 und S-008 umgesetzt sein, vor Welle 3 S-001, S-005, S-006 und S-010. Keiner der Befunde stellt die Architektur in Frage. Alle lassen sich als zusätzliche PS-Anforderungen formulieren.

### Was das Dokument bereits gut löst (kurz)

- **Allowlist-Projektion mit drei Feldklassen.** Dazu Guard-Tests: Klassifikation vollständig (PS-ACC-012), keine Standort-Imports (PS-ACC-034), Vorlagen-Platzhalter fail-closed (PS-ACC-027). Fehler fallen damit in der CI auf und nicht erst in der Review.
- **`location_disclosure` nie aus Koordinaten.** `since_precision = month`; `user_key` und `created_by` sind nie öffentlich.
- **Token-Handling.** Fernet, Startup-Guard ohne `FERNET_KEY` (PS-NFR-011), Guard über die Response-Modelle (PS-ACC-050), Log-Redaction. Revoke überschreibt das Token statt es nur als ungültig zu markieren. Task-Argumente sind nur Keys (PS-SEC-011).
- **Minimal-Scopes** ohne `read`, `follow`, `push` und `admin:*`. `write:accounts` gibt es nur als zweiten Consent-Schritt.
- **Kein eingehender Webhook**, keine Reply-, Follow- oder Boost-Methoden im Port (PS-SOC-050, ADR-PS-12). Was es nicht gibt, kann niemand missbrauchen.
- **Anti-Spam als Kernfunktion.** Ceilings über der Policy, Burst-Pause, Digest, Cooldown, keine Posts aus Backfill oder Import.
- **Zweiter EXIF-Strip auf Renditions** mit Byte-Prüfung gegen ein GPS-Fixture (PS-ACC-033).
- **Provider-Antworten werden als Daten behandelt** (PS-SEC-006). SSRF-Validierung, `follow_redirects=False`, Größen- und Zeitlimits (PS-SEC-005).
- **KI-Fact-Check verwirft statt zu reparieren.** Review bis 20 Freigaben, Kennzeichnung im Post selbst.
- **Cannabis-Sperre als Default** mit Betreiber-Opt-in. Die bekannte `require_permission`-Lücke ist offen benannt (R-12) und mit einem Matrix-Guard belegt (PS-SEC-031).

---

## 🔴 Kritisch — Sicherheitslücke / Compliance-Verstoß

### S-001: OAuth-Callback nicht an die initiierende Browser-Sitzung gebunden (Account-Linking-CSRF)

**Anforderung:** PS-MAS-020 („`state` + `code_verifier` im `RedisOAuthStateStore` … zusätzlich `tenant_key`, `identity_key|null`, `user_key`"), PS-SEC-001, §23.5 Callback mit Rolle „—", PS-UX-030 („`state` ist nicht an Tab/Fenster gebunden").

**Sicherheitsproblem:** Der Callback ist global und unauthentifiziert. Das Bearer-Token steckt im SPA-Speicher und geht bei einer Top-Level-Navigation nicht mit. Wer den Callback mit gültigem `code` und `state` aufruft, verknüpft das Mastodon-Konto, **dessen Browser** den Code geliefert hat, mit dem Mandanten, **der den State erzeugt hat**. Der bestehende `RedisOAuthStateStore` bindet den State an keine Sitzung.

Ablauf des Angriffs:
1. Ein Angreifer mit eigenem Mandanten ruft `POST /social/mastodon/connect` auf.
2. Er schickt die `authorization_url` einem Opfer, z. B. einer Mastodon-Nutzerin, die Kamerplanter schon einmal verbunden hat.
3. Das Opfer klickt und stimmt zu.
4. Das Token des Opfers mit `write:statuses` und `write:media` landet im Mandanten des Angreifers.
5. Das Bot-Flag bremst den Angriff nicht, weil Option (c) „nur manuelles Posten" ausdrücklich erlaubt ist.

Verschärfend teilen sich alle Mandanten einer Kamerplanter-Instanz die App-Registrierung je Mastodon-Instanz (PS-MAS-012). Hat das Opfer die App schon autorisiert, entfällt nach Annahme (a) der Zustimmungsdialog. Dann reicht ein einziger Klick ohne sichtbare Rückfrage.

**Risiko:** Ein Angreifer bekommt Schreibzugriff auf das Fediverse-Konto einer dritten Person: Identitätsmissbrauch, Spam, Rufschaden für Nutzerin und Betreiber, Sperre der Kamerplanter-App durch Instanz-Admins (R-01).

**OWASP/STRIDE:** A01:2021 Broken Access Control / A07 Identification and Authentication Failures; STRIDE Spoofing + Elevation of Privilege; RFC 9700 §4.7 (CSRF), §2.1.

**Empfohlene Maßnahme (neue Anforderung):**
> **PS-SEC-016 (MUST, MVP) Sitzungsbindung des Social-OAuth-Flows.**
> - `POST /social/{provider}/connect` setzt ein Cookie `kp_social_oauth`:
>   - Inhalt: 32 Byte Zufall
>   - Attribute: `HttpOnly; Secure; SameSite=Lax; Path=/api/v1/social/; Max-Age=300`
>   - Im Redis-State wird nur `sha256(nonce)` abgelegt.
> - Der Callback verlangt das Cookie und vergleicht den Hash in konstanter Zeit. Danach löscht er das Cookie. Fehlt es oder passt es nicht: 400 `connection.state_invalid`, kein Token-Tausch und Audit `connection.state_mismatch`.
> - Der Callback prüft **zum Zeitpunkt des Callbacks** erneut:
>   - Mitgliedschaft und Rolle von `user_key` im `tenant_key`
>   - Existenz und Mandant von `identity_key`
>   - Regulierungs-Sperre
>   - Consent `social_publishing`
>   - Light-Modus, `SOCIAL_ENABLED`, Allowlist und Denylist
> - Die Verbindung entsteht zunächst als `pending_confirmation`. Erst die eingeloggte, initiierende Person bestätigt sie in der SPA mit `POST /social/connections/{key}/confirm` (Bearer, `user_key` = State-Initiator); dabei sieht sie Handle und Instanz.
> - Für den Mobile-Client (PS-UX-033) gilt dasselbe Prinzip mit einem App-gebundenen Nonce statt Cookie.
> - Optional (Betreiber-Schalter `SOCIAL_OAUTH_FORCE_LOGIN`, Default `false`): `force_login=true` an `/oauth/authorize`.

**Testfall-Vorschlag (PS-ACC-052, I):**
- *Given* State S, erzeugt von Nutzer A (Cookie in Session A), *When* der Callback mit gültigem `code` und S **ohne** bzw. mit fremdem Cookie aufgerufen wird, *Then* 400 `connection.state_invalid`, kein Aufruf `POST /oauth/token` am Mock, kein `social_connections`-Dokument, Audit `connection.state_mismatch`.
- *Given* A wird zwischen Connect und Callback zum Beobachter herabgestuft, *Then* 403 und kein Token-Tausch.

---

## 🟠 Hoch — Fehlende Sicherheitsanforderung

### S-002: Signierte Bild-URLs des öffentlichen Profils legen `tenant_key`, Storage-Key und `attachment_id` offen

**Betroffene Anforderung:** §23.6 (`avatar_url`/`header_url` „signierte Rendition-URLs … TTL 60 min", Fotos der Ereignisse), PS-ACC-030 („keine Schlüssel mit Suffix `_key`, kein `tenant`").

**Fehlende Spezifikation:** Wird für die öffentlichen URLs der bestehende Mechanismus wiederverwendet (§3.1 nennt `/attachments/token/{token}`), dann legt der Token-Body Folgendes offen (gemessen in `local_fs_adapter.py:640-668`):
- `key = t/{tenant_key}/…`
- `tenant_key`
- `aid`

Der Body ist nur base64-kodiert, nicht verschlüsselt. Bei S3 steht der Objektpfad im Klartext in der Presigned-URL. Der Schema-Snapshot-Test PS-ACC-030 prüft das JSON und decodiert keine URL-Inhalte. Er bliebe also grün.

**Sicherheitsrisiko:**
- **Verknüpfbarkeit:** Zwei scheinbar unabhängige öffentliche Profile lassen sich demselben Haushalt bzw. Mandanten zuordnen. Das hebelt `location_disclosure = none` teilweise aus: Ein Profil mit `city` plus ein zweites ohne ergibt den Ort für beide.
- Das Token gilt für das Objekt, nicht für die Veröffentlichung. Nach `unpublish`, `suspend` oder Löschung bleibt das Bild bis zu 60 min abrufbar, im Browser-Cache wegen `max-age=86400` bis zu 24 h.

**Empfehlung:**
> **PS-PRI-014 (MUST, MVP) Öffentliche Medien-URLs sind opak und an die Veröffentlichung gebunden.**
> - Öffentliche Bilder laufen über einen eigenen Endpunkt `GET /api/v1/public/media/{opaque_id}`.
> - Die `opaque_id` hat zwei zulässige Formen:
>   - zufälliger, serverseitig gemappter Bezeichner mit ≥ 128 Bit, Mapping in Redis oder DB mit TTL
>   - authentifiziert verschlüsselter Token (AES-GCM/Fernet), der keinen lesbaren Inhalt hat
> - Der Endpunkt
>   - liefert nur die Renditions 512 und 1280, nie das Original,
>   - prüft bei **jedem** Abruf, dass die Identität `visibility ∈ {unlisted, public}` und `status ∉ {deleted, suspended}` hat und das Ereignis effektiv öffentlich ist,
>   - bindet die ID an `identity.publication_epoch`; das Feld wird bei jedem Sichtbarkeitswechsel, Slug-Wechsel und Suspend erhöht.
> - Response-Header: `Cache-Control: public, max-age=300` (nicht länger), `X-Content-Type-Options: nosniff`, `Content-Disposition: inline` nur für Bild-MIME-Typen.
> - Weder S3-Presigned-URLs noch `/attachments/token/` dürfen in öffentlichen Responses vorkommen.

**Testfall (PS-ACC-038, I):**
- *Given* eine öffentliche Identität mit Avatar, *When* alle URL-Werte der Antwort von `/public/plants/{slug}` und `/events` base64- und URL-dekodiert werden, *Then* enthält kein dekodierter Teil `tenant_key`, `t/`, `att_` oder `_key`.
- *When* die Identität auf `internal` gesetzt wird, *Then* liefert die zuvor ausgegebene Medien-URL sofort 404.

### S-003: Bilder des öffentlichen Profils sind nicht vom zweiten EXIF-Strip abgedeckt

**Betroffene Anforderung:** PS-SOC-030, PS-PRI-012 und PS-ACC-033 decken nur die Publish-Pipeline zu Mastodon ab. AB-09 nennt den Strip als Gegenmaßnahme. Avatar, Header und Ereignisfotos unter `/p/{slug}` (§23.6) haben keinen Strip.

**Fehlende Spezifikation:** Hat die Instanz `storage_strip_exif=False` gesetzt, ist offen, ob die bestehenden Renditions EXIF, XMP oder ICC-Kommentare mitnehmen. Das hängt davon ab, wie der Thumbnail-Generator speichert, und ist nirgends als Invariante festgelegt.

**Sicherheitsrisiko:** Der Fall, den AB-09 adressiert („EXIF-Leak bei `storage_strip_exif=False`"), tritt beim öffentlichen Profil ungeschützt ein: GPS-Koordinaten des Wohnorts landen im Netz. Das ist genau der Totalschaden, den §17 verhindern soll.

**Empfehlung:**
> **PS-PRI-015 (MUST, MVP)** Jedes Bild, das ein unauthentifizierter Endpunkt ausliefert, ist eine re-enkodierte Rendition ohne EXIF-, XMP-, IPTC-, GPS- und Kommentar-Segmente. Das gilt unabhängig von `storage_strip_exif`. Die Invariante ist in der Rendition-Erzeugung verankert, wenn eine Rendition für öffentliche Auslieferung erzeugt oder ausgeliefert wird.

**Testfall:** PS-ACC-033 erweitern.
- *Given* `storage_strip_exif=False` und ein GPS-Fixture als Avatar und Ereignisfoto, *When* die Bytes über `/api/v1/public/media/{id}` geladen werden, *Then* keine EXIF-, XMP- und GPS-Segmente (Byte-Prüfung) und Dimensionen ≤ 1280.

### S-004: `unlisted` ist erratbar, und der Referer verrät den Link

**Betroffene Anforderung:** §17.1 („Unlisted — jeder mit dem Link `/p/{slug}`"), PS-PI-010 (Slug-Vorschlag aus `display_name` und Trivialname der Art, z. B. `mona-monstera`), Persona Lena, PS-SEC-010 (60 Anfragen/min je IP).

**Fehlende Spezifikation:**
- „Unlisted" klingt nach geheimem Link. Der Slug ist aber aus Kosename und Art ableitbar. Mit einem Wörterbuch aus Kosenamen und Arten lassen sich bei 60/min je IP und rotierenden IPs (IPv6) sehr viele Profile in Stunden auffinden.
- Externe `links[]` und Bildabrufe senden ohne Referrer-Policy die Profil-URL an Dritte.

**Sicherheitsrisiko:** Die Nutzerin erwartet, dass nur ihre Freunde das Profil sehen. Tatsächlich ist es auffindbar. Fotos aus der Wohnung und der Wohnort (`city`) verlassen den erwarteten Kreis (Art. 5 Abs. 1 lit. f, Art. 25 DSGVO).

**Empfehlung:**
> **PS-PRI-016 (MUST, MVP) `unlisted` ist ein Capability-Link.**
> - Bei `visibility = unlisted` lautet die öffentliche Adresse `/p/{slug}~{access_token}`; `access_token` hat ≥ 96 Bit Zufall, base32.
> - `/p/{slug}` ohne gültiges Token antwortet für `unlisted` identisch zu „unbekannt" (404).
> - „Link neu erzeugen" invalidiert den alten Link. Das ist als Gärtner-Aktion im Audit erfasst.
> - Für `public` entfällt das Token.
> - Das öffentliche Profil setzt `Referrer-Policy: no-referrer`. Externe Links tragen `rel="noopener noreferrer nofollow ugc"`.
> - Die UI erklärt `unlisted` als „nur mit diesem Link auffindbar, nicht geheim".

**Testfall (PS-ACC-039, I):**
- *Given* eine `unlisted`-Identität, *When* `GET /api/v1/public/plants/{slug}` ohne Token, *Then* 404 mit identischem Body wie für einen unbekannten Slug; mit Token 200.
- *When* „Link neu erzeugen", *Then* das alte Token gibt 404.

### S-005: Gärtner können die Freigabe durch die Leitung umgehen (Governance-Lücke)

**Betroffene Anforderung:** §19.1, §21-Matrix, §23.2 (`PUT …/policy`: Gärtner+), §23.4 (manueller Post `publish_now: bool`: Gärtner+), PS-SOC-003 („Nutzer kann den Wert … senken (min 0)"), O-20 (`review_by` „je Mandant umstellbar"). Personas UZG-003 („Schüler dürfen nicht selbst veröffentlichen") und ZG-004 („Tom gibt frei").

**Fehlende Spezifikation:**
- `review_by` steht nicht im Policy-Schema §12.3. Es ist offen, wo der Wert liegt und wer ihn ändern darf.
- Selbst bei `review_by = lead` stehen einer Gärtnerin drei Umgehungswege offen:
  - (a) Policy-Modus auf `auto` setzen
  - (b) `review_required_until_posts` auf 0 senken
  - (c) manuellen Post mit `publish_now = true` senden
- In allen drei Fällen entsteht kein Entwurf und die Leitungsfreigabe wird nie gefragt.
- Dasselbe gilt für `provider_visibility`, `mentions` und `hashtags.base`, Inhalte also, die die Leitung freigeben soll.

**Sicherheitsrisiko:** Privilege Escalation innerhalb des Mandanten (A01). Der Freigabe-Workflow, auf dem die Personas „Schule" und „Gemeinschaftsgarten" aufbauen, ist reine Kosmetik. In BM-002 haftet der Verein für Posts, die nie jemand freigegeben hat.

**Empfehlung:**
> **PS-SEC-035 (MUST, MVP) Freigabe-Governance auf Mandantenebene.**
> - `Tenant.settings.social.governance` enthält:
>   - `review_by ∈ {anyone, lead}` (Default nach O-20)
>   - `grower_may_set_auto: bool` (Default: `personal` → `true`, `organization` → `false`)
>   - `grower_may_publish_now: bool` (gleiche Defaults)
>   - `min_reviewed_posts` (≥ `SOCIAL_MIN_REVIEWED_POSTS`)
> - Lesen dürfen alle Rollen. Ändern darf nur die **Leitung**; jede Änderung wird auditiert (`governance.changed`).
> - Ist `review_by = lead`, gilt Folgendes:
>   - (a) Ein Gärtner-`PUT …/policy`, der einen Modus auf `auto` oder `digest_mode = auto` setzt, `review_required_until_posts` unter `min_reviewed_posts` senkt oder `mentions`/`provider_visibility` erweitert, ergibt 403 `policy.requires_lead`.
>   - (b) Manuelle Posts von Gärtnern entstehen immer als `draft`; `publish_now` wird ignoriert und die Response enthält einen Hinweis.
>   - (c) Für `auto`-Regeln, die eine Gärtnerin vor einer Governance-Verschärfung gesetzt hat, gilt ab der Verschärfung `review`.
> - Die Prüfung liegt im Service, nicht im Router (datenabhängig, durch `require_permission` nicht ausdrückbar), mit Negativtest je Umgehungsweg.

**Testfall (PS-ACC-065, I):**
- *Given* ein Organisations-Mandant mit `review_by = lead`, *When* ein Gärtner (a) `PUT …/policy {new_leaf: auto}`, (b) `{review_required_until_posts: 0}`, (c) `POST …/social/posts {publish_now: true}` sendet, *Then* (a) und (b) ergeben 403 `policy.requires_lead`, (c) ergibt 201 mit `status = draft`.
- Der Mock-Provider erhält in allen drei Fällen keinen `POST /api/v1/statuses`.

### S-006: Querverweise in Body und Pfad werden nicht gegen den Anker aufgelöst (IDOR innerhalb und über Mandanten)

**Betroffene Anforderung:** PS-SEC-009 und PS-SEC-031 (Anker Pflanze), §23.4 manueller Post `{event_key?, connection_key?, attachments[]}`, `compose {event_key}`, §23.5 `connect {identity_key}`, `disconnect {connection_key}`, verschachtelte Pfade `…/plant-instances/{key}/social/posts/{post_key}` und `…/timeline/events/{event_key}`.

**Fehlende Spezifikation:** PS-SEC-008 regelt nur `attachment_id`. Für folgende Prüfungen gibt es keine Anforderung:
- `connection_key` muss die eigene `identity`-Verbindung der Identität **oder** die Mandanten-Verbindung bei `use_tenant_connection = true` sein.
- `event_key` muss zur Pflanze `{key}` gehören.
- `post_key` und `event_key` im Pfad müssen zu `{key}` gehören (Elternschlüssel).
- `identity_key` beim Connect muss zum aktiven Mandanten gehören.

Laut Memory-Kernmuster („Guard opt-in am Aufrufort → Drift zwischen Geschwistern") ist genau diese Klasse im Projekt mehrfach aufgetreten.

**Sicherheitsrisiko:**
- Eine Gärtnerin postet über `connection_key` auf das Mastodon-Konto einer **anderen** Identität desselben Mandanten. Das kann das private Konto einer Mitbewohnerin sein.
- Bei fehlender Mandantenprüfung landet ein Post sogar auf dem Konto eines fremden Mandanten.
- Über `event_key` lassen sich die Payloads fremder Pflanzen in einen eigenen Post rendern: Informationsabfluss über `compose`.

**Empfehlung:**
> **PS-SEC-034 (MUST, MVP) Jede Referenz wird serverseitig über den Anker aufgelöst.**
> - Jeder Pfad- und Body-Schlüssel wird geladen und geprüft: `tenant_key` des Dokuments = aktiver Mandant **und** Kettenbezug zum Anker. Die Kettenregeln:
>   - `post.identity_key → identity.plant_instance_key == {key}`
>   - `event.plant_instance_key == {key}`
>   - `connection` ∈ {Verbindung mit `identity_key` = Identität von `{key}`, Mandantenverbindung mit `use_tenant_connection = true`}
> - Bei Verstoß: 404 `…not_found`, ohne Unterschied zwischen „fremd" und „fehlt".
> - Repository-Methoden nehmen Elternschlüssel und `tenant_key` als keyword-only-Parameter ohne Default (Memory: Prädikat in den Service).
> - Ein AST-Guard prüft, dass jede Social- und Timeline-Route mit ≥ 2 Pfadsegmenten jedes Segment in einem Lookup verwendet.

**Testfall (PS-ACC-066, I):**
- *Given* die Identitäten X und Y im selben Mandanten, jede mit eigener Verbindung, *When* `POST …/plant-instances/{X}/social/posts {connection_key: conn_Y}`, *Then* 404, und der Mock erhält keinen Upload und keinen Status.
- Analog `GET …/plant-instances/{X}/social/posts/{post_of_Y}` ergibt 404, ebenso `compose {event_key: event_of_Y}` und `connect {identity_key: identity_of_other_tenant}`.

### S-007: Freitext gelangt doch automatisch an die Öffentlichkeit (`milestone.title`, `caption` als Alt-Text)

**Betroffene Anforderung:**
- §11.2: `milestone` mit `public_safe = title`, `journal_entry` mit `title`
- §23.6: Events-Endpunkt mit `alt_text` „aus dem zugehörigen Post oder `caption`"
- PS-SOC-031: Alt-Text-Vorschlag aus `caption`
- §27: Ohne Provider steuert die Policy, ob ein Ereignis auf `/p/{slug}` erscheint
- dagegen PS-PRI-002 und AB-08 („Freitext nie automatisch")

**Fehlende Spezifikation:**
- `title` eines Tagebucheintrags ist Freitext, geschrieben für den internen Gebrauch, etwa „Problem nach Besuch von Familie Meier, Ostweg 3". Er ist als `public_safe` klassifiziert, nicht als `optional`.
- `caption` ist für `photo_added` korrekt opt-in (§11.2). §23.6 nutzt die `caption` aber als Alt-Text-Fallback für **alle** öffentlichen Fotos, ohne Opt-in.
- Auf dem Profilpfad ohne Provider läuft keine Regelprüfung nach §19.4 (Namen, Adress-Heuristik), denn §19.4 gilt „vor jedem Senden".

**Sicherheitsrisiko:** Personenbezogene Daten Dritter und Adressen werden ohne bewusste Freigabe veröffentlicht (Art. 5 Abs. 1 lit. c, Art. 25 DSGVO). Das widerspricht der zentralen Zusage aus Z-3.

**Empfehlung:**
> **Änderung §11.2 / PS-EVT-014:** `title` (bei `milestone` und `journal_entry`) und `caption` sind Klasse `optional`, Default nicht freigegeben. Der Alt-Text auf `/p/{slug}` stammt ausschließlich (1) aus einem veröffentlichten Post oder (2) aus dem Vorlagen-Alt-Text nach PS-SOC-031 (2), niemals ungeprüft aus `caption`.
>
> **PS-SOC-072 (MUST, MVP)** Die Regelprüfung nach §19.4 (Schritte 2, 4, 5 und Adress-Heuristik nach PS-PRI-011) läuft auch:
> - vor jeder Erhöhung der Sichtbarkeit einer Identität
> - bei jeder Änderung von `bio`, `origin_text`, `ambience_text`, `links[].label` oder `display_name` an einer nicht-`internal` Identität
> - vor der Aufnahme eines Ereignisses mit `optional`-Freitextfeldern in die öffentliche Projektion
>
> Ein Treffer bei `auto` führt zu Hold bzw. Nicht-Veröffentlichung; bei manueller Aktion erscheint ein Hinweis mit Bestätigung.

**Testfall (PS-ACC-067, I):**
- *Given* ein Meilenstein mit `title = "Ostweg 3 – Besuch Meier"` und Policy `milestone: auto` ohne Provider, *When* `GET /public/plants/{slug}/events`, *Then* erscheint der Titel nicht. Der Vorlagentext erscheint ohne `title`.
- *Given* ein Foto mit `caption = "Malte gießt"`, *Then* ist der öffentliche Alt-Text der Vorlagen-Alt-Text.

### S-008: Art.-17-Lücke — `plant_events.actor` und weitere Personenbezüge fehlen in Erasure und Export

**Betroffene Anforderung:** PS-PRI-051, PS-PRI-052, §11.1 (`actor {user_key?, label?}`), §22.8 (`details`), §22.5 (`created_by`), §22.6 (`last_error`), Z-8.

**Fehlende Spezifikation:**
- PS-PRI-052 anonymisiert `social_connections`, `social_posts`, `plant_identities.created_by` und `social_audit_events.actor_user_key`. Bei **`plant_events.actor.user_key` und `actor.label`** passiert nichts, obwohl jedes Ereignis mit `origin = user` die handelnde Person enthält.
- Nach §17.6 folgt `plant_events` „der Pflanze". Bleibt der Mandant bestehen, bleibt der Personenbezug unbegrenzt erhalten.
- Im Export (Art. 15) sind die `plant_events` nur mandantenbezogen erfasst, nicht als „Aktionen der betroffenen Person".
- Weitere unbehandelte Felder:
  - `social_audit_events.details` mit Freitext ≤ 200 Zeichen (§19.6)
  - `actor.label` (kann Klarnamen enthalten)
  - `SocialPost.approved_by` im 30-Tage-Nachweis gelöschter Verbindungen
  - die Rate-Limit-Schlüssel der Meldefunktion

Das Muster „Art. 15/17 waren Gerüste" (Welle 12, #1645) wiederholt sich hier.

**Sicherheitsrisiko:** Verstoß gegen Art. 17 und Art. 15 DSGVO. Eine Inventar-Guard-Lücke würde unbemerkt bleiben, weil der Guard nur Collections prüft, nicht Felder.

**Empfehlung:**
> **Änderung PS-PRI-052:** `ErasureEngine` anonymisiert bei Nutzerlöschung zusätzlich:
> - `plant_events.actor.user_key` → `_anonymized`
> - `actor.label` → `null`
> - `social_audit_events.details` → Freitext-Felder entfernen (vgl. S-026)
> - `social_connections.created_by`
>
> Der Inventar-Guard prüft **feldgenau**: Jedes Feld mit Suffix `_by`, `user_key` oder `actor` in einer Social-Collection hat einen Eintrag im Erasure-Plan.
>
> **Änderung PS-PRI-051:** `USER_DATA_MANIFEST` enthält `plant_events` mit dem Filter `actor.user_key = subject`, als personenbezogene Aktivität, zusätzlich zur Mandantensicht.

**Testfall:** PS-ACC-036 erweitern.
- *Then* existiert nach dem Art.-17-Lauf kein Dokument in `plant_events`, `social_posts`, `social_audit_events` oder `social_connections` mit dem `user_key` des Subjekts. Die Prüfung erfolgt per AQL über alle Felder, nicht nur über die bekannten.

### S-010: Austritt eines Mitglieds — Verbindungen zu dessen persönlichem Mastodon-Konto bleiben für den Mandanten nutzbar

**Betroffene Anforderung:** §12.9 (A nutzergeführt: Die Besitzerin legt den Account selbst an), §21 (Verbindung lesen und nutzen: alle Gärtner), PS-MAS-061 (nur Erasure), PS-PRI-050 (nur Consent-Widerruf).

**Fehlende Spezifikation:** Eine `identity`-Verbindung zeigt auf ein Konto, das eine **Person** besitzt (E-Mail und Passwort bei der Instanz). Diese Fälle sind ungeregelt:
- Das Mitglied verlässt den Mandanten (Membership entfernt, kein Erasure, kein Consent-Widerruf). Danach können die verbleibenden Mitglieder weiter in dessen Namen posten.
- Umgekehrt kann jede Gärtnerin auf das Konto einer Mitbewohnerin posten, die es verbunden hat. Das ist so gewollt, wird der Verbindenden aber nicht erklärt.

**Sicherheitsrisiko:** Unbefugte Nutzung eines fremden Kontos nach Ende der Mitgliedschaft (A01, Spoofing). Rechtlich wird weiter im Namen einer Person veröffentlicht, die nicht mehr zustimmt.

**Empfehlung:**
> **PS-SEC-036 (MUST, MVP)**
> - Endet die Mitgliedschaft von `created_by` einer Verbindung (Austritt, Entfernung, Rollenwechsel unter Gärtner), wechselt die Verbindung sofort in `paused` mit Grund `owner_left`. Die betroffenen Posts bleiben `queued`.
> - Die Leitung wird benachrichtigt (REQ-030) und entscheidet „trennen (revoke)" oder „Person neu verbinden lassen".
> - Die ausgetretene Person erhält per E-Mail einen Hinweis, wie sie die App in Mastodon widerruft.
> - Der Verbindungs-Assistent erklärt vor dem Verbinden: „Alle Gärtner und die Leitung dieses Gartens können über dieses Konto Beiträge veröffentlichen."

**Testfall (PS-ACC-068, I):**
- *Given* Gärtnerin B hat eine Identitätsverbindung angelegt, *When* die Leitung B aus dem Mandanten entfernt, *Then* Verbindung `paused(owner_left)`; ein fälliger Post wird nicht gesendet; die Leitung hat die Benachrichtigung `social.connection_owner_left`.

---

## 🟡 Mittel — Präzisierung nötig

### S-009: Idempotenz-Schlüssel — Kollision bei manuellen Posts und Zeitfenster kürzer als der Backoff

**Vage Anforderung:** PS-SOC-011: `idempotency_key = sha256(identity_key, event_key, payload_version, digest_window?)`. Index `idempotency_key` unique (§22.6). Backoff 1/5/15/60/240 min (§13.6).

**Sicherheitsrelevanz:**
- (1) Für manuelle Posts sind `event_key` und `payload_version` `null`. Alle manuellen Posts einer Identität bekommen damit denselben Schlüssel. Folgen:
  - Der Unique-Index lehnt den zweiten Post ab.
  - Innerhalb des Mastodon-Fensters liefert der Provider sogar den **ersten** Status zurück. Der zweite Post gilt dann als „published", obwohl nichts veröffentlicht wurde: Integritätsverlust ohne jede Meldung.
- (2) Löscht die Nutzerin einen Ereignis-Post und teilt dasselbe Ereignis erneut, entsteht derselbe Schlüssel.
- (3) Liegen die Wiederholungen 4 und 5 jenseits des Idempotenz-Fensters (Annahme b: ca. 1 h), führt ein mehrdeutiger Fehler (Timeout nach dem Absenden) zu einem Doppelpost. Doppelte Posts sind genau das Spam-Muster, das Instanz-Admins sperren (R-01).

**Empfohlene Präzisierung:**
> **PS-SOC-011 (Änderung)**
> - `idempotency_key` wird beim Anlegen des Posts als zufälliger Wert (ULID/UUIDv4) erzeugt und bleibt über alle Versuche stabil.
> - Die Deduplizierung von Ereignissen erfolgt getrennt über einen Unique-Index `(identity_key, event_key, payload_version)`, sparse für `kind = event`.
>
> **PS-MAS-051 (MUST, MVP)**
> - Endet ein Versuch mehrdeutig (Timeout oder Verbindungsabbruch nach dem Senden des Requests), erfolgt die Wiederholung **innerhalb** des Idempotenz-Fensters (≤ 30 min nach dem ersten Versuch).
> - Ist das Fenster überschritten, wechselt der Post auf `draft(ambiguous_result)` mit der Nutzerfrage „Ist der Beitrag auf Mastodon erschienen?"; Kamerplanter erstellt den Status nicht automatisch neu.

**Testfall:**
- *Given* zwei manuelle Posts derselben Identität innerhalb einer Minute, *Then* zwei unterschiedliche `idempotency_key` und zwei Remote-Status.
- *Given* ein Mock-Timeout nach dem Empfang von `POST /statuses` und eine Uhr bei +70 min, *Then* `draft(ambiguous_result)`, kein zweiter `POST`.

### S-011: 404-Gleichbehandlung unvollständig und widersprüchlich; Cache verlängert die Sichtbarkeit

**Vage Anforderung:** PS-SEC-010 („404 für `internal`/`archived`/unbekannt identisch … gleiche Antwortzeit-Klasse"). Dagegen stehen §9.5 („archived: Profil bleibt in seiner Sichtbarkeit lesbar") und PS-ACC-006 (archiviert, 200 mit `lifespan`). Dazu `Cache-Control: public, max-age=60` und 301 aus `slug_history`.

**Sicherheitsrelevanz:**
- `archived` ist in sich widersprüchlich: PS-SEC-010 verlangt 404, PS-ACC-006 erwartet 200.
- Nicht genannt sind `paused`, `suspended`, `deleted` (Tombstone), regulierte Art (nach einem Opt-out des Betreibers) und `SOCIAL_PUBLIC_PROFILES_ENABLED=false`.
- Der 301 aus `slug_history` verrät den neuen Slug auch dann, wenn die Identität inzwischen `internal` ist.
- Die authentifizierten Antworten 409 `identity.slug_taken` und `slug_recently_deleted` bilden ein Orakel für die Existenz interner Identitäten (PS-ACC-002). Jeder registrierte Nutzer in BM-001 kann es nutzen.
- „Gleiche Antwortzeit-Klasse" ist nicht prüfbar formuliert.
- `public, max-age=60` erlaubt Zwischen-Caches (CDN, Reverse Proxy). Nach `unpublish` oder `suspend` bleibt das Profil weiter auslieferbar, und ein Notfall-Takedown durch den Betreiber wirkt nicht sofort.

**Empfohlene Präzisierung:**
> **PS-SEC-010 (Neufassung)**
> - Der öffentliche Pfad antwortet genau dann mit 200, wenn alle Bedingungen erfüllt sind:
>   - `visibility ∈ {unlisted+Token, public}`
>   - `status ∈ {active, paused, archived}`
>   - `SOCIAL_PUBLIC_PROFILES_ENABLED`
>   - keine Regulierungssperre
> - Sonst antwortet er mit 404, und zwar mit byte-identischem Body, identischen Headern (ohne `ETag`) und derselben Code-Pfad-Länge: Die Identität wird immer per Slug geladen, auch wenn sie nicht existiert, und die Projektion wird nicht erst bei Existenz gestartet.
> - 301 aus `slug_history` nur, wenn das Ziel selbst 200 liefern würde; sonst 404.
> - `Cache-Control: public, max-age=60, s-maxage=0` bzw. `private` beim Einsatz geteilter Caches.
> - Sichtbarkeitswechsel und Suspend erhöhen `publication_epoch` (S-002), sodass der `ETag` sofort invalidiert wird.
> - Die Slug-Kollisionsantworten unterscheiden nicht zwischen intern und öffentlich. Sie sind auf 30/h je Nutzer begrenzt.
> - `slug-suggestions` liefert nur freie Vorschläge, nie „belegt von …".
> - `archived` verhält sich wie in PS-ACC-006 (200 mit `lifespan`). PS-SEC-010 ist entsprechend zu korrigieren.

**Testfall:** PS-ACC-058 erweitern.
- *Given* je eine Identität in `paused` + `internal`, `suspended`, `deleted` und eine unbekannte, *Then* vier byte-identische 404-Antworten ohne `ETag`.
- *Given* ein alter Slug einer jetzt internen Identität, *Then* 404 statt 301.

### S-012: Slug-Namensraum und Weiterleitung

**Vage Anforderung:** PS-PI-011 (alter Slug leitet ≥ 12 Monate weiter, „danach wird er frei"), PS-PI-013 (Tombstone 90 Tage), Indizes §22.2 (`public_slug` unique, `slug_history[*].slug` nur Array-Index).

**Sicherheitsrelevanz:**
- Aus dem Spec geht nicht hervor, dass die Eindeutigkeit **auch** gegen `slug_history` geprüft wird. Ein anderer Mandant kann den alten Slug sofort belegen. Dann kollidieren 301 und neues Profil: Impersonation oder Umleitung auf eine fremde Pflanze (AB-13).
- Nutzerinnen ändern die Adresse oft gerade, um eine Verfolgung zu beenden, etwa wenn der Link an die falsche Person ging. Die zwölfmonatige Weiterleitung macht genau das unmöglich.

**Empfohlene Präzisierung:**
> **PS-PI-016 (MUST, MVP)**
> - Die Slug-Vergabe prüft gegen `public_slug` ∪ alle aktiven `slug_history`-Einträge ∪ Tombstones.
> - Beim Slug-Wechsel wählt die Nutzerin „Alte Adresse weiterleiten" (Default) oder „Alte Adresse sofort ungültig machen". Im zweiten Fall bleibt der alte Slug 90 Tage gesperrt (wie ein Tombstone) und liefert 404.

**Testfall:** *Given* Identität A wechselt von `mona` zu `mona-2`, *When* Mandant B `mona` beansprucht, *Then* 409 `identity.slug_taken`.

### S-013: Rate-Limits fehlen auf aufwändigen und netzauslösenden Endpunkten; Missbrauch der Meldefunktion

**Vage Anforderung:** PS-SEC-010 (60/min je IP nur für den öffentlichen Pfad), PS-SOC-064 (Melden 5/Tag/IP), §23.3 `POST …/backfill`, §23.4 `compose`, §23.5 `connect`.

**Sicherheitsrelevanz:**
- `connect` löst bei einer neuen Domain `GET /api/v2/instance` und `POST /api/v1/apps` gegen **beliebige** öffentliche Hosts aus (Allowlist leer = alle). Ein Gärtner kann so:
  - Kamerplanter als Scanner oder Reflektor nutzen
  - `social_provider_apps` unbegrenzt füllen
  - Celery mit Discovery-Aufrufen beschäftigen
- `backfill` (auch ohne Dry-Run) über viele Pflanzen und `compose` (später mit KI-Tokenkosten) sind Hebel für authentifizierten DoS.
- Die IP-Limits ignorieren IPv6-Präfixe und das Vertrauen in Proxys (`X-Forwarded-For`).
- Die Meldefunktion leitet `message` an die Betreiber-E-Mail weiter. Daraus folgen Mail-Bombing und, ohne Feldbegrenzung, Header- und HTML-Injection in der Mail.

**Empfohlene Präzisierung:**
> **PS-SEC-037 (MUST, MVP) Limits für authentifizierte Endpunkte**
>
> | Endpunkt | Limit |
> |---|---|
> | `connect` | 10/h je Nutzer, 30/Tag je Mandant |
> | Neue App-Registrierungen (neue `instance_domain`) | 5/Tag je Mandant, `SOCIAL_MAX_PROVIDER_APPS` instanzweit (Default 200) |
> | `backfill` | 1 laufender Lauf je Pflanze, 20/h je Mandant |
> | `compose` | 60/h je Nutzer |
> | `slug-suggestions` | 60/h je Nutzer |
> | Callback | 30/min je IP |
>
> - Öffentliche Limits zählen IPv6 je /64.
> - IPs werden nur aus vertrauenswürdigen Proxy-Headern übernommen (bestehende Einstellung, ausdrücklich referenziert).
> - Zusätzlich gilt ein globales Budget `SOCIAL_PUBLIC_RATE_LIMIT_GLOBAL`.
>
> **PS-SOC-064 (Präzisierung)**
> - Felder: `reason` ist ein Enum, `message` ≤ 1 000 Zeichen Klartext; die Mail wird als `text/plain` versendet; Nutzerinhalt erscheint nie in Betreff oder Headern.
> - Zusätzlich zum IP-Limit: ≤ 20 Meldungen/Tag je Slug und ≤ 200/Tag instanzweit; Überschuss wird verworfen, mit Zähler.

**Testfall:** *Given* 6 Connects mit neuen Domains an einem Tag in einem Mandanten, *Then* der sechste ergibt 429 `social.limit_reached`, ohne ausgehenden Aufruf (Netzwerk-Sniffer-Fixture aus PS-ACC-055).

### S-014: Bösartige oder kompromittierte Mastodon-Instanz — Provider-Daten nur teilweise als „Daten" geregelt

**Vage Anforderung:** PS-SEC-005, PS-SEC-006, PS-MAS-011 (Capabilities), §13.6 (`X-RateLimit-Reset`), PS-MAS-025 (heuristische Fehlertexte), UI zeigt `account.url` und `external_url` als Link (PS-UX-007, PS-SOC-063).

**Sicherheitsrelevanz:** Wer eine Instanz betreibt, kontrolliert alle Antworten, und die Allowlist ist per Default leer. PS-SEC-006 regelt nur das Escaping von Text. Diese Angriffswege bleiben offen:
- `url`, `external_url` oder `avatar` mit `javascript:`/`data:` → XSS beim Klick in der Kamerplanter-UI.
- `max_characters`, `max_media_attachments` und `description_limit` mit Extremwerten → Composer-Fehlverhalten, Speicherverbrauch.
- `X-RateLimit-Reset` weit in der Zukunft (Post hängt für immer) oder in der Vergangenheit (enge Retry-Schleife gegen die eigene Queue).
- Media-Poll mit 202 als Dauerantwort.
- `validate_server_side_url` läuft laut Spec beim ersten Kontakt. Die Celery-Aufrufe folgen Stunden oder Tage später. Ein DNS-Wechsel auf eine interne Adresse ist dann möglich, und `url_safety.py:238` bestätigt, dass die IP nicht festgehalten wird.

**Empfohlene Präzisierung:**
> **PS-SEC-038 (MUST, MVP) Plausibilisierung von Provider-Daten**
> - **URLs:** Nur `https`. Der Host muss gleich `instance_domain` oder dessen Subdomain sein, sonst wird der Wert verworfen und kein Link gerendert.
> - **Capabilities** werden geklemmt:
>
>   | Wert | Bereich |
>   |---|---|
>   | `max_characters` | 100–10 000 |
>   | `max_media_attachments` | 0–10 |
>   | `description_limit` | 0–5 000 |
>   | `image_size_limit` | ≤ 40 MB |
>
>   Werte außerhalb werden auf die Grenze gesetzt, mit `capabilities_clamped = true`.
> - **Rate-Header:** `X-RateLimit-Reset`/`Retry-After` geklemmt auf 1 s bis 60 min.
> - **Polling:** Media-Poll höchstens 60 s (wie spezifiziert) und höchstens 10 Polls.
> - **Antworten:** JSON-Tiefe ≤ 20, Größe ≤ 2 MB (gestreamt abbrechen).
> - **Fehlertexte** werden nie im Klartext gespeichert, nur `message_redacted` mit ≤ 200 Zeichen und ohne Steuerzeichen.
> - **Jeder** ausgehende Aufruf, auch aus Celery, validiert die Ziel-IP erneut und verbindet sich mit genau der geprüften IP (IP-Pinning mit SNI/Host-Header). Das entspricht HELM-Egress und schließt die Rebinding-Lücke für diesen neuen, nutzergesteuerten Zielraum.

**Testfall:**
- *Given* der Mock liefert `account.url = "javascript:alert(1)"` und `X-RateLimit-Reset` = +30 Tage, *Then* `account.url = null` und `next_attempt_at ≤ +60 min`.
- *Given* die Domain löst beim Connect öffentlich auf und beim Publish auf `127.0.0.1`, *Then* `failed(instance_invalid_url)`, kein Verbindungsaufbau.

### S-015: OAuth-Mix-up mit vielen Autorisierungsservern hinter einem Callback; Reflexion von Fehlerparametern; `code` im Access-Log

**Vage Anforderung:** PS-MAS-012 (`redirect_uris = {APP_BASE_URL}/api/v1/social/mastodon/callback` für **alle** Instanzen), PS-SEC-001 („`code` wird nie geloggt"), §23.5 Callback 302 mit `result=error:<code>`.

**Sicherheitsrelevanz:**
- Kamerplanter spricht mit beliebig vielen, teils feindlichen Autorisierungsservern über einen einzigen Callback. Damit liegt der Mix-up-Fall nach RFC 9700 §4.4 vor. PKCE und das instanzspezifische `client_secret` mildern ihn ab, zuverlässig schließt ihn nur ein Callback je Server.
- Der Mastodon-Parameter `error`/`error_description` darf nicht in die Frontend-URL reflektiert werden (Phishing-Text).
- PS-SEC-001 schützt Applikations-Logs. `code` und `state` stehen aber auch in den Access-Logs von Ingress und Uvicorn.

**Empfohlene Präzisierung:**
> **PS-MAS-026 (MUST, MVP)**
> - Redirect-URI je App-Registrierung: `…/social/mastodon/callback/{provider_app_key}`.
> - Der Callback prüft `provider_app_key == state.provider_app_key` und nutzt für den Token-Tausch ausschließlich die Instanz aus dem State.
> - Liefert die Instanz einen `iss`-Parameter, muss er dem Issuer aus der Discovery entsprechen.
> - `result` ist ein festes Enum (`ok`, `denied`, `state_invalid`, `instance_error`, `bot_flag_required`); Provider-Fehlertexte werden nie reflektiert.
> - Access-Logs maskieren Query-Strings auf `/api/v1/social/*/callback*`; das ist im Helm-Chart und in der Uvicorn-Log-Konfiguration verankert.

### S-017: Reconciliation und nebenläufige Auswertung — verspätete Ereignisse fluten, doppelte Entwürfe

**Vage Anforderung:**
- PS-EVT-015 und PS-ACC-011: Reconcile erzeugt Ereignisse mit `origin = user`, nicht `backfill`.
- PS-NFR-002: `evaluated_at = null` älter als 10 min wird neu eingereiht.
- PS-SOC-023: nur `backfill`/`import` erzeugen nie Posts.

**Sicherheitsrelevanz:**
- War der Recorder z. B. eine Woche lang defekt, erzeugt der nächtliche Reconcile hunderte Ereignisse mit Herkunft `user`. Sie laufen in `auto`. Die Burst-Pause greift je Pflanze erst ab 20 in 10 min, und bei gleichmäßiger Verteilung über Pflanzen greift sie nicht. Folge: ein Posting-Schwall mit veralteten Inhalten (AB-01).
- Laufen `evaluate_event` aus dem Enqueue und aus dem Reconcile parallel, entstehen ohne atomaren Statuswechsel zwei Entwürfe oder Posts für dasselbe Ereignis.

**Empfohlene Präzisierung:**
> **PS-SOC-025 (MUST, MVP)**
> - Ereignisse, die Reconcile erzeugt oder neu auswertet und deren `occurred_at` älter als `SOCIAL_MAX_EVENT_AGE_FOR_AUTO` ist (Default 24 h), werden höchstens als `review` behandelt, nie als `auto`.
> - Sie tragen `recovered_by_reconcile = true`.
> - `evaluate_event` setzt `evaluated_at` per Compare-and-Set (`FILTER evaluated_at == null UPDATE … RETURN NEW`). Nur der Gewinner erzeugt einen Post.
> - Zusätzlich gilt der Unique-Index aus S-009.

**Testfall:** *Given* 50 Ereignisse über 10 Pflanzen, durch Reconcile mit `occurred_at` = −3 Tage erzeugt, Policy `auto`, *Then* 0 `queued`-Posts, ≤ 50 `draft`. *Given* zwei parallele `evaluate_event` für dasselbe Ereignis, *Then* genau ein Post.

### S-018: Zeitliche Muster — automatische Posts verraten Anwesenheit und Tagesablauf

**Vage Anforderung:** §17.3 (DSFA-Vermerk nur für Sensor-Posts), §23.6 (`occurred_on` taggenau, gut), PS-MAS-041 (`created_at` → `published_at` sekundengenau beim Provider), `quiet_hours` als Policy-Option.

**Sicherheitsrelevanz:** `auto`-Posts gehen Sekunden nach der Erfassung eines Meilensteins oder einer Ernte raus. Der öffentliche Zeitstempel bei Mastodon bildet damit die Anwesenheit und den Tagesrhythmus der Person ab, gerade bei Gießen und Pflege von Hand. Zusammen mit `city` lässt sich ein Abwesenheitsprofil erstellen (Einbruchsrisiko). Das betrifft nicht nur Sensoren.

**Empfohlene Präzisierung:**
> **PS-PRI-021 (MUST, MVP)**
> - `auto`-Posts werden nicht zum Ereigniszeitpunkt veröffentlicht, sondern im nächsten **Veröffentlichungsfenster** (`publish_slots`, Default täglich 12:00 und 18:00 in der Zeitzone der Identität, mit ±15 min Zufallsversatz).
> - `quiet_hours` sind per Default aktiv.
> - Manuelle Posts sind ausgenommen (Nutzerentscheidung).
> - Für das Gesamtfeature (öffentliches Profil + Provider) wird eine DSFA-Schwellwertprüfung nach Art. 35 DSGVO dokumentiert, nicht nur für `sensor_threshold`.

### S-019: Rechtsgrundlage, Consent-Träger, Drittland und Fotos anderer Mitglieder

**Vage Anforderung:** PS-PRI-050 („Consent-Zweck `social_publishing` … beim ersten Verbinden je Nutzer"), PS-SEC-008 (Medien des Mandanten), §17.4.

**Sicherheitsrelevanz:**
- **Wessen Consent zählt?** Unklar ist, ob es der Consent der verbindenden Person, der freigebenden Person oder der Person ist, die die Policy auf `auto` gestellt hat. Bei Celery-`auto` handelt niemand aktiv. Folge: Eine Person ohne Consent (oder nach Widerruf) kann über die Verbindung einer anderen Person Daten an Dritte übermitteln.
- **Rechtsgrundlage:** Für eine vom Nutzer gewollte Veröffentlichung trägt Art. 6 Abs. 1 lit. b DSGVO in der Regel besser als eine Einwilligung. Die Dokumentation sollte das klar trennen, sonst entsteht ein widerrufbarer Consent für eine Vertragsleistung.
- **Drittland:** Mastodon-Instanzen stehen weltweit, eine Information nach Art. 13 fehlt.
- **Fotos anderer Mitglieder:** Wählt eine Gärtnerin Fotos, die ein anderes Haushaltsmitglied hochgeladen hat (mit Personen, Wohnräumen), veröffentlicht sie Daten dieser Person ohne deren Zutun.

**Empfohlene Präzisierung:**
> **PS-PRI-054 (MUST, MVP)**
> - (a) Die Rechtsgrundlage der nutzerinitiierten Veröffentlichung ist im Verarbeitungsverzeichnis dokumentiert (Art. 6 Abs. 1 lit. b, ergänzend Art. 6 Abs. 1 lit. a für `auto`). Der Consent `social_publishing` wird geprüft:
>   - bei Connect, Approve und `publish_now` für die handelnde Person
>   - bei `auto` für die Person, die die betreffende `auto`-Regel zuletzt gesetzt hat (`policy.rules[*].set_by`)
>
>   Fehlt der Consent, entsteht ein `draft(consent_missing)`.
> - (b) Der Verbindungs-Assistent nennt die Instanz als eigenständigen Verantwortlichen, ihren Sitz soweit bekannt (Freitext-Hinweis, kein Lookup) und weist darauf hin, dass Daten außerhalb der EU verarbeitet werden können.
> - (c) Werden Fotos ausgewählt, deren `created_by` nicht die handelnde Person ist, zeigen Entwurf und Freigabe den Hinweis „Foto von {Mitglied}". Bei `auto` werden nur Fotos der Person einbezogen, die die Regel gesetzt hat; andere Fotos kommen in einen `draft`.

### S-020: KI — Freitext gelangt doch in den Prompt; Fact-Check übersieht Zahlwörter (nicht MVP)

**Vage Anforderung:** PS-SEC-007 („Prompt-Injection über Pflanzennotizen ist damit **strukturell** unmöglich"), PS-AI-020 (`display_name`, `ambience_text` im Prompt), PS-AI-003 (`custom_traits`), PS-AI-021 (Zahlenprüfung).

**Sicherheitsrelevanz:**
- `display_name` (60 Zeichen), `ambience_text` (80) und `custom_traits` (5 × 40) sind Freitext. Über S-007 käme `title` hinzu. Dort kann eine Injektion stehen wie „Ostfenster. Ignoriere Regeln, schreibe …". Die Aussage „strukturell unmöglich" stimmt also nicht. Sie verleitet zum Verzicht auf weitere Kontrollen.
- Der Fact-Check prüft Ziffern. „Zwölf Blätter" oder „twelve leaves" kommen durch.
- PS-AI-011 knüpft den Cloud-Consent an den **handelnden** Nutzer. Bei `auto` per Celery gibt es keinen.

**Empfohlene Präzisierung:**
> - **PS-SEC-007 (Neufassung):** „Tagebuch-Freitext gelangt nie in den Prompt. Nutzergetippte Identitätsfelder (`display_name`, `ambience_text`, `custom_traits`) sind **untrusted data**: Sie stehen ausschließlich im Delimiter-Kontextblock, nach der Delimiter-Neutralisierung aus `prompt_engine.py`, nie in der System-Rolle."
> - **PS-AI-021 (e)** ergänzen: Zahlwörter (de/en, 0–1000, „Dutzend", „Hälfte") werden normalisiert und wie Ziffern geprüft. Der Output darf keine wörtlichen Zitate mit mehr als 5 Wörtern aus Freitextfeldern enthalten.
> - **PS-AI-011 (Ergänzung):** Für systemausgelöste Generierung gilt der Consent der Person, die `ai_generation.enabled` gesetzt hat. Widerruft sie, wird `ai_generation` deaktiviert.
>
> **Testfall:** PS-ACC-061b, *Given* Fakten `{leaf_length_cm: 34}` und der Output „zwölf neue Blätter", *Then* verworfen (`number_not_in_facts`).

### S-021: Kill-Switch und Betreiberrollen — Semantik unvollständig

**Vage Anforderung:** PS-SEC-012 („hält alle Publish-Tasks an"), §19.1 „Plattform" ohne Unterscheidung `admin` und `viewer` (REQ-024: Plattformrollen admin und viewer).

**Sicherheitsrelevanz:**
- Würde der Kill-Switch auch Löschungen, Revokes und Erasure-Remote-Löschungen anhalten, verhinderte er gerade die Schadensbegrenzung im Vorfall.
- Neue Connects und App-Registrierungen laufen während des Notfalls weiter.
- Der Plattform-Viewer darf laut REQ-024 nur lesen. In §19.1 und §21 ist er nicht ausgeschlossen.

**Empfohlene Präzisierung:**
> **PS-SEC-012 (Ergänzung)**
> - `SOCIAL_PUBLISHING_PAUSED` hält `create_post`, `upload_media`, `update_profile` und `connect` an (503 `social.publishing_paused`).
> - `delete_post`, `revoke` und Erasure-Tasks laufen **immer** weiter.
> - Alle Betreiberaktionen erfordern `require_admin_scope` (schreibend). `platform_viewer` hat nur Lesezugriff auf die Instanzübersicht.

### S-022: Schlüsseltrennung und Rotation des App-Secrets

**Vage Anforderung:** PS-SEC-003 („Rotation = App neu registrieren (bestehende Tokens bleiben gültig, an die App gebunden)"), R-04 („Key-Rotation (bestehendes Verfahren)").

**Sicherheitsrelevanz:**
- Wird eine App neu registriert, entstehen neue `client_id` und neues `client_secret`. Die alten Tokens gehören weiter zur **alten** App, und `POST /oauth/revoke` braucht das **alte** Secret. Überschreibt man es, lassen sich die alten Tokens nicht mehr widerrufen.
- Alle Social-Tokens, OIDC-Secrets und KI-Keys hängen am selben `FERNET_KEY`. Wird der Schlüssel kompromittiert, sind alle Kategorien zugleich betroffen.

**Empfohlene Präzisierung:**
> **PS-SEC-039 (MUST, MVP)**
> - `social_provider_apps` ist versioniert (`app_version`). Jede Verbindung referenziert ihre Version.
> - Eine alte Version bleibt mit ihrem Secret erhalten, bis ihr keine Verbindung mehr zugeordnet ist. Erst dann wird das Secret überschrieben.
> - Die Rotation geschieht über ein Re-Connect der Nutzer, mit Hinweis in der UI.
> - Social-Geheimnisse werden mit einem per HKDF abgeleiteten Unterschlüssel (`info = "kp-social-v1"`) verschlüsselt oder mit eigenem `SOCIAL_FERNET_KEY`. `MultiFernet` ist für die Rotation vorgesehen, das Runbook ist in der Betreiberdoku verlinkt.

### S-023: Aufbewahrungslücken und Inkonsistenzen in R-28…R-33

**Vage Anforderung:** PS-PRI-053, §22.6 (`deleted` behält Text), PS-PI-011 (`slug_history`), PS-SOC-064 (Meldungen), R-32 (`oauth_state:*`).

**Sicherheitsrelevanz:**
- Für `social_posts` mit Status `published` oder `deleted` gibt es keine Frist. Gelöschte Posts behalten Text und Anhangsliste unbegrenzt, obwohl die Nutzerin sie bewusst gelöscht hat.
- `slug_history` hat keine Retention-Zeile.
- Für Meldungen (Mail beim Betreiber, IP-Zähler) gibt es keine Zeile.
- R-32 nennt `oauth_state:*`. Der Code nutzt `kp:oauth:state:` (gemessen), die Zeile zeigt also ins Leere.
- `last_error` hat keine Frist.

**Empfohlene Präzisierung (NFR-011):**

> | Zeile | Daten | Frist / Maßnahme |
> |---|---|---|
> | R-34 | `social_posts (status = deleted)` | `text`, `attachments`, `hashtags` und `mentions` nach 30 Tagen leeren; Stub (`external_id`, `deleted_remote_at`) bis R-31 |
> | R-35 | `plant_identities.slug_history` | Einträge mit `valid_until < now` entfernen |
> | R-36 | Meldungen | Rate-Limit-Schlüssel 24 h TTL; Betreiber-Postfach als eigene Verarbeitung im Betreiberleitfaden (14 Tage nach Bearbeitung) |
>
> - R-32 auf das tatsächliche Präfix korrigieren (`kp:oauth:state:*`, `purpose = social_connect`).
> - `last_error` wird bei Erfolg geleert.

### S-030: Abuse-Matrix §20 unvollständig

**Vage Anforderung:** PS-SEC-020 („Matrix ist Grundlage der Abuse-Testfälle").

**Sicherheitsrelevanz:** Mehrere realistische Fälle fehlen. Weil die Matrix die Testbasis ist, fehlen dann auch die Tests.

**Empfohlene Präzisierung (neue Zeilen):**

| # | Szenario | Gegenmaßnahme |
|---|----------|---------------|
| AB-18 | Account-Linking-CSRF / Konto eines Dritten verknüpfen | S-001 (PS-SEC-016) |
| AB-19 | Bösartige Instanz (Capabilities, Rate-Header, `javascript:`-URLs, Rebinding) | S-014 (PS-SEC-038), S-015 |
| AB-20 | Kamerplanter als Scanner/Reflektor über `connect`/App-Registrierung | S-013 (PS-SEC-037) |
| AB-21 | Interne Umgehung der Leitungsfreigabe | S-005 (PS-SEC-035) |
| AB-22 | Nutzung des Kontos eines ausgetretenen Mitglieds | S-010 (PS-SEC-036) |
| AB-23 | Deanonymisierung durch Verknüpfung (Token-Inhalt, Zeitmuster, Foto-Hintergründe, seltene Art + Stadt) | S-002, S-018, PS-PRI-013 |
| AB-24 | Auffinden von `unlisted`-Profilen / Referer-Leck | S-004 |
| AB-25 | Missbrauch der Meldefunktion (Mail-Bombing, Injection, Belästigung des Betreibers) | S-013 |
| AB-26 | Verspäteter Posting-Schwall nach Recorder-Ausfall | S-017 |
| AB-27 | Mandantenübergreifende Flut gegen **eine** Mastodon-Instanz (BM-001, viele Mandanten) | neue Grenze `SOCIAL_MAX_POSTS_PER_INSTANCE_DOMAIN_PER_HOUR` (Default 120), bei Überschreitung Verschiebung statt Verwerfen |
| AB-28 | Abbau des Sperrschutzes nach Ende der Weiterleitung von `slug_history` | S-012 |

Zusätzlich: ein Ceiling **je Verbindung** (`SOCIAL_MAX_POSTS_PER_CONNECTION_PER_DAY`, Default 10). Ein Garten-Account mit 50 Identitäten darf nicht das Mandanten-Ceiling von 30/Tag ausschöpfen.

---

## 🟢 Hinweise und Best Practices (niedrig)

- **S-024 Step-up als MUST statt SHOULD** (PS-SEC-014). Laut Betreiberentscheidung vom 2026-10-03 (#2009, „Step-up ja") gilt Step-up für: Connect mit `scope = tenant`, Löschen einer Identität, Ändern der Governance (S-005), Senken von `review_required_until_posts` auf 0. Das gilt in allen Betriebsmodellen, nicht nur BM-001.
- **S-025 Benachrichtigung bei neuer Verbindung.** AB-07 verweist darauf, es gibt aber keine PS-ID. → **PS-SOC-081 (MUST, MVP):** REQ-030-Typ `social.connection_created` an die Leitung und an die verbindende Person, mit Handle und Instanz.
- **S-026 Kein Freitext im Audit.** §19.6 erlaubt Freitext ≤ 200 Zeichen in `details`, über 365 Tage. → Nur Feldnamen, Enum-Werte, Hashes und Keys; Freitext wird nie gespeichert. Das vereinfacht S-008.
- **S-027 OpenGraph-HTML (Welle 3b).** Serverseitige HTML-Hülle:
  - Kontextgerechtes Escaping in Attributen: `og:description` aus `bio` per HTML-Attribut-Encoding.
  - Header: `Content-Security-Policy: default-src 'none'; img-src 'self'`, `X-Content-Type-Options: nosniff`.
  - `Vary: Accept, Accept-Language`.
  - Die öffentlichen API-Endpunkte senden CORS ohne `Allow-Credentials`.
- **S-028 Scope-Upgrade (`write:accounts`).** Ein neuer OAuth-Flow erzeugt ein neues Token, das alte wird widerrufen. Nach dem Tausch muss `granted_scopes ⊆ requested_scopes` gelten; mehr gewährte Scopes führen zum sofortigen Revoke und zu `connection.scope_excess`.
- **S-029 Redis-State mit `code_verifier` im Klartext.** Das ist akzeptabel (300 s). Der Schlüssel des States sollte aber `sha256(state)` sein, damit ein Redis-Dump keine verwendbaren States liefert. Das Log `state[:8]` ist in Ordnung.
- **S-031 Widerspruch zwischen §17.6 und PS-ACC-035.** PS-PRI-050 widerruft bei Widerruf des Consents „alle vom Nutzer angelegten Verbindungen". Dazu gehören auch `tenant`-Verbindungen, die eine Leitung für den Verein angelegt hat. Ein persönlicher Widerruf sollte die Garten-Verbindung pausieren und die anderen Leitungen benachrichtigen, statt sie sofort zu trennen. Diese Entscheidung ist explizit zu dokumentieren.
- **S-032 Light-Modus.** `/p/{slug}` funktioniert im Light-Modus (PS-SEC-033). Ist eine Light-Instanz versehentlich aus dem Internet erreichbar, sind die öffentlichen Profile ohne jede Anmeldeinfrastruktur öffentlich. Daher: `SOCIAL_PUBLIC_PROFILES_ENABLED` per Default `false` im Light-Modus, Opt-in mit Hinweis.

---

## Datensparsamkeits-Matrix

| Objekt / Feld (REQ-055) | Erfasste Daten | Personenbezogen? | Zweck definiert? | Löschfrist? | Bewertung |
|---|---|---|---|---|---|
| `PlantIdentity` Profilfelder (`display_name`, `bio`, `origin_text`, `ambience_text`, `links`) | Nutzertext | potenziell (Namen, Adressen im Freitext) | ja | mit Identität; Tombstone R-28 | ⚠️ Regelprüfung auch für das Profil nötig (S-007) |
| `PlantIdentity.location_disclosure/label` | Land/Region/Stadt | indirekt (Wohnort) | ja | mit Identität | ✅ vorbildlich (nie aus Koordinaten) |
| `PlantIdentity.since_date` | Monat | indirekt | ja | mit Identität | ✅ Präzision `month` |
| `PlantIdentity.created_by` | `user_key` | ja | Audit/DSGVO | Anonymisierung | ✅ |
| `PlantIdentity.slug_history` | alte Slugs | indirekt (Verfolgbarkeit) | ja | ❌ keine Zeile | ⚠️ S-012, S-023 |
| `PlantEvent.actor.user_key/label` | handelnde Person | ja | Herkunft | ❌ nicht in der Erasure | ❌ S-008 |
| `PlantEvent.payload` | fachliche Werte, klassifiziert | `never`-Felder ja | ja | mit Pflanze | ✅ Allowlist; ⚠️ `title`/`caption` (S-007) |
| `SocialConnection.account` | Handle, Anzeigename, Zähler des Fremdkontos | ja (Kontoinhaber) | ja | R-30 (30 d nach Trennung) | ✅ |
| `SocialConnection.access_token_encrypted` | OAuth-Token | ja (Zugriffsrecht) | ja | R-30 sofort | ✅ (S-022 Schlüsseltrennung) |
| `SocialPost.text/attachments` | veröffentlichter Inhalt | potenziell | ja | ❌ `published`/`deleted` ohne Frist | ⚠️ S-023 |
| `SocialPost.created_by/approved_by` | `user_key` | ja | Nachweis | Anonymisierung | ✅ |
| `SocialPost.stats` | Zähler | nein | ja | überschreibend (R-33) | ✅ |
| `SocialAuditEvent.details` | Freitext ≤ 200, Keys | potenziell | ja | R-31 (365 d) | ⚠️ S-026 |
| Follower-/Reply-Inhalte | — | — | — | — | ✅ werden nicht erfasst (PS-SOC-040) |
| Meldeformular | Grund, Nachricht, IP (Rate-Limit) | ja | ja | ❌ keine Zeile | ⚠️ S-013, S-023 |
| Redis OAuth-State | `user_key`, `tenant_key`, `code_verifier` | ja | ja | R-32 (300 s, Präfix falsch) | ⚠️ S-023 |
| Produktmetriken | Tageszähler | nein | ja | — | ✅ ohne IDs als Labels |
| Signierte Bild-URLs | `tenant_key`, Storage-Key, `aid` (im Token lesbar) | indirekt (Verknüpfbarkeit) | nein (Nebeneffekt) | TTL 60 min | ❌ S-002 |

---

## Autorisierungs-Matrix (Soll nach Review)

Legende: ✅ erlaubt · ❌ verboten · 🔶 bedingt (Bedingung in Spalte „Hinweis"). „Unauth" = nicht angemeldet. Rollen nach REQ-049 (Beobachter/Gärtner/Leitung); Plattform = `platform_admin`.

| Ressource / Endpunkt | Leitung | Gärtner | Beobachter | Plattform | Unauth | Spezifiziert in | Hinweis / Änderung |
|---|---|---|---|---|---|---|---|
| GET `…/identity`, `/preview`, `/identities` | ✅ | ✅ | ✅ | ❌ (nur über Admin-Übersicht) | ❌ | §23.1 | — |
| POST/PATCH `…/identity`, PUT `/slug` | ✅ | ✅ | ❌ | ❌ | ❌ | §23.1 | — |
| PUT `…/identity/visibility` | ✅ | 🔶 | ❌ | erzwingt `internal` | ❌ | §23.1, §19 | 🔶 Governance (S-005) für Organisations-Mandanten |
| DELETE `…/identity` | ✅ + Step-up | ❌ | ❌ | ✅ (Grund, Audit) | ❌ | §23.1 | Step-up MUST (S-024) |
| PUT `…/policy` | ✅ | 🔶 | ❌ | Ceilings | ❌ | §23.2 | 🔶 `auto`/Schwellen nur gemäß Governance (S-005) |
| `Tenant.settings.social.governance` | ✅ + Step-up | ❌ | ❌ | ❌ | ❌ | **neu** S-005 | — |
| GET `…/timeline`, `/events/{k}` | ✅ | ✅ | ✅ | ❌ | ❌ | §23.3 | Elternschlüssel prüfen (S-006) |
| PATCH Ereignis-Sichtbarkeit, POST `backfill`/`milestone` | ✅ | ✅ | ❌ | ❌ | ❌ | §23.3 | Limits für `backfill` (S-013) |
| POST `…/social/posts` (manuell) | ✅ | 🔶 | ❌ | ❌ | ❌ | §23.4 | 🔶 Gärtner → `draft` bei `review_by = lead`; `connection_key`/`event_key` auflösen (S-006) |
| PATCH/discard/resend Post | ✅ | 🔶 Ersteller | ❌ | ❌ | ❌ | §23.4 | Ownership im Service |
| POST `…/approve` | ✅ | 🔶 eigene bei `anyone` | ❌ | ❌ | ❌ | §19.1 | `review_by` nur Leitung änderbar |
| DELETE Post (remote) | ✅ | 🔶 Ersteller | ❌ | ✅ (Grund) | ❌ | §19.1 | läuft auch bei Kill-Switch (S-021) |
| POST `…/compose` | ✅ | ✅ | ❌ | ❌ | ❌ | §23.4 | `event_key` ⊆ Pflanze; Limit (S-013) |
| GET `/social/review`, `/connections` | ✅ | ✅ | ✅ (ohne Token) | ❌ | ❌ | §23.4/23.5 | — |
| POST `/social/{p}/connect` scope `identity` | ✅ | ✅ | ❌ | ❌ | ❌ | §23.5 | Sitzungsbindung (S-001), Limits (S-013) |
| POST `/social/{p}/connect` scope `tenant` | ✅ + Step-up | ❌ | ❌ | ❌ | ❌ | §23.5 | S-024 |
| GET `/social/{p}/callback` | — | — | — | — | 🔶 nur mit Sitzungs-Cookie + gültigem State | §23.5 | S-001, S-015 |
| POST `/connections/{k}/confirm` | 🔶 nur Initiator | 🔶 nur Initiator | ❌ | ❌ | ❌ | **neu** S-001 | — |
| verify / pause / resume | ✅ | ✅ | ❌ | ❌ | ❌ | §23.5 | — |
| profile-sync, disconnect | ✅ | 🔶 Ersteller | ❌ | ✅ (Notfall) | ❌ | §23.5 | — |
| GET `/social/audit` | ✅ (Mandant) | 🔶 eigene | ❌ | ✅ (alle) | ❌ | §19.1 | — |
| Admin: Kill-Switch, Denylist, Ceilings, Suspend | ❌ | ❌ | ❌ | ✅ `admin` (Viewer nur lesen) | ❌ | §25.1 | S-021 |
| GET `/public/plants/{slug}` (+`/events`, `/media`) | — | — | — | — | ✅ gemäß Sichtbarkeit (+Token bei `unlisted`) | §23.6 | S-002, S-004, S-011 |
| POST `/public/plants/{slug}/report` | — | — | — | — | ✅ Rate-Limit | §23.6 | S-013 |

---

## DSGVO-Checkliste

| Betroffenenrecht / Pflicht | Spezifiziert? | Wo? | Kommentar |
|---|---|---|---|
| Information (Art. 13/14) | ⚠️ teilweise | PS-PRI-050 (Consent-Hinweis) | Hinweis auf die Instanz als eigenständigen Verantwortlichen und Drittland fehlt (S-019) |
| Auskunft (Art. 15) | ⚠️ | PS-PRI-051 | `plant_events` nicht als Aktivität der Person (S-008) |
| Berichtigung (Art. 16) | ✅ | Profil editierbar; Remote-Edit manueller Posts SHOULD (PS-MAS-043) | Ereignis-Posts werden bewusst nicht editiert, Löschen ist möglich |
| Löschung (Art. 17) | ⚠️ | PS-PRI-052, PS-MAS-060/061 | `plant_events.actor`, Audit-Freitext und gelöschte Post-Texte fehlen (S-008, S-023); remote best-effort ist offen kommuniziert ✅ |
| Einschränkung (Art. 18) | ✅ (implizit) | Pause, `internal`, Archiv | — |
| Datenportabilität (Art. 20) | ✅ | PS-PI-014 | Export ohne Tokens, mit Gap-Hinweis ✅ |
| Widerspruch (Art. 21) | ⚠️ | Consent-Widerruf → Revoke | Rechtsgrundlage lit. b/lit. a ungeklärt (S-019); Sonderfall Garten-Verbindung (S-031) |
| Einwilligungsmanagement | ⚠️ | PS-PRI-050, PS-AI-011 | Unklar, wessen Consent zählt (Celery-`auto`, Approve) (S-019, S-020) |
| Privacy by Design/Default (Art. 25) | ✅/⚠️ | §17, ADR-PS-08 | Defaults stark; Lücken: `unlisted` erratbar, Zeitmuster, Token-Inhalt (S-004, S-018, S-002) |
| DSFA (Art. 35) | ⚠️ | §17.3 nur Sensor | Schwellwertprüfung für das Gesamtfeature (S-018) |
| Aufbewahrung (Art. 5 Abs. 1 lit. e) | ⚠️ | R-28…R-33 | R-34…R-36 ergänzen, R-32-Präfix korrigieren (S-023) |
| Auftragsverarbeitung / Drittanbieter | ⚠️ | — | Mastodon-Instanz ist kein Auftragsverarbeiter, sondern eigener Verantwortlicher der Nutzerin; im Betreiberleitfaden dokumentieren (S-019). KI-Cloud über bestehende `ai_cloud_processing` ✅ |

---

## Empfohlene Sicherheitsmaßnahmen (priorisiert)

| Prio | Maßnahme | Befund | Spätestens vor |
|---|---|---|---|
| **P1 — Sofort (Spec v1.2)** | Sitzungsbindung + Neuprüfung im Callback + `pending_confirmation` (PS-SEC-016) | S-001 | Welle 3 |
| **P1** | Opake, veröffentlichungsgebundene Medien-URLs; EXIF-Invariante für jede öffentliche Auslieferung (PS-PRI-014/015) | S-002, S-003 | Welle 2 |
| **P1** | `unlisted` als Capability-Link, `Referrer-Policy: no-referrer` (PS-PRI-016) | S-004 | Welle 2 |
| **P1** | `title`/`caption` auf `optional`; Regelprüfung auch für Profil und Projektion (PS-SOC-072) | S-007 | Welle 2 |
| **P1** | Erasure/Export feldgenau inkl. `plant_events.actor` (Inventar-Guard je Feld) | S-008 | Welle 2 |
| **P1** | Governance auf Mandantenebene, nur Leitung (PS-SEC-035) | S-005 | Welle 3 (Policy-Modell schon in Welle 2 vorbereiten) |
| **P1** | Auflösung jeder Referenz am Anker + AST-Guard (PS-SEC-034) | S-006 | Welle 2/3 |
| **P1** | Austritt eines Mitglieds → Verbindung `paused(owner_left)` (PS-SEC-036) | S-010 | Welle 3 |
| **P2 — Kurzfristig** | Idempotenz neu schneiden + mehrdeutige Ergebnisse (PS-MAS-051) | S-009 | Welle 3 |
| **P2** | 404-Parität, Cache, Slug-Orakel; Slug-Namensraum (PS-SEC-010 neu, PS-PI-016) | S-011, S-012 | Welle 2 |
| **P2** | Limits auf `connect`/App-Registrierung/`backfill`/`compose`; Härtung der Meldefunktion (PS-SEC-037) | S-013 | Welle 2/3 |
| **P2** | Plausibilisierung der Provider-Daten, IP-Pinning bei jedem Aufruf (PS-SEC-038); Callback je App (PS-MAS-026) | S-014, S-015 | Welle 3 |
| **P2** | Reconcile ohne `auto`, CAS bei der Auswertung (PS-SOC-025) | S-017 | Welle 3 |
| **P2** | Veröffentlichungsfenster + DSFA-Schwellwertprüfung (PS-PRI-021); Klärung von Rechtsgrundlage und Consent (PS-PRI-054) | S-018, S-019 | Welle 3 |
| **P2** | Abuse-Matrix AB-18…AB-28 + Ceilings je Verbindung und je Ziel-Instanz | S-030 | Welle 3 |
| **P3 — Mittelfristig** | Kill-Switch-Semantik, Plattform-Viewer (S-021); App-Versionierung, HKDF-Unterschlüssel (S-022); Retention R-34…R-36 (S-023) | S-021–S-023 | Welle 3 |
| **P3** | KI: Neufassung PS-SEC-007, Zahlwörter, Consent bei Systemauslösung | S-020 | Welle 5 |
| **P3** | Step-up MUST, Verbindungs-Benachrichtigung, Audit ohne Freitext, OG-Escaping, Scope-Upgrade, gehashte State-Schlüssel, Light-Modus-Default | S-024–S-032 | Welle 3/3b |

**Hinweis zur Nummerierung:** Die vorgeschlagenen PS-IDs (PS-SEC-016, -034…-039, PS-PRI-014…-016, -021, -054, PS-SOC-025, -072, -081, PS-MAS-026, -051, PS-PI-016, PS-ACC-038/039/052/065…068) sind derzeit nicht vergeben. Sie sind bei der Einarbeitung in REQ-055 v1.2 gegen den Bestand zu prüfen. Die Retention-Zeilen R-34…R-36 setzen voraus, dass R-28…R-33 wie in PS-PRI-053 übernommen werden.
