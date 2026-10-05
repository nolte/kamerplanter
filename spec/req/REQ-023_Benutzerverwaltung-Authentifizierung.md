# Spezifikation: REQ-023 - Benutzerverwaltung & Authentifizierung

```yaml
ID: REQ-023
Titel: Benutzerverwaltung & Authentifizierung
Kategorie: Plattform & Sicherheit
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Authlib, React, TypeScript, MUI
Status: Entwurf
Version: 1.46 (§5a Plattform-Rolle auf `lead` nachgezogen, `tenant_roles` im Token informativ, Umsetzungsstand der Plattform-Admin-Rechte und AK-18/AK-42–AK-55; #2121); 1.44 (Token-Familie mit Replay-Erkennung, Access Token endet mit seiner Sitzung, gehashte Reset-/Bestätigungs-Tokens; #2116, #2158); 1.43 (§5a.5.1/§5a.5.2 Notfall-Verwaltung gestrichen, ersetzt durch Übergabe/`orphaned` bei der Kontolöschung, #2134; Step-up `tenant_erasure_cancel`, #2123); 1.42 (Registrierungsmodus `REGISTRATION_MODE` und Domain-Allowlist, §3.2d, AK-56; #2132); 1.41 (Step-up `admin_membership_add`, #2106); 1.40 (Restbefunde #2062: Valkey-Clients, Token-Reihenfolge, Summe je Postfach); 1.39 (Admin-Seite für OIDC-Provider, #1906); 1.38 (Bestätigungsnachweis `email_confirmed_at`, #1948); 1.37 (Step-up für Rollenwechsel und Mitglieder-Entfernen, #2032); 1.36 (Bereinigung abgebrochener lokaler Registrierungen: Trockenlauf, #2010); 1.35 (Anonyme Routen und Reset-Budget nach den Prüfungen von #2043/#2045 gehärtet, #2048/#2052/#2058/#2059/#2060); 1.34 (Wartezeit der Mail-Budgets bei hängendem Valkey begrenzt, Aussagen der Bündel-Prüfung korrigiert, #2045/#2043/#2046); 1.33 (Login-Ablehnung `EMAIL_NOT_VERIFIED` mit korrektem Passwort verschickt den neuen Bestätigungslink selbst, #2046); 1.32 (Budget je Adresse für `POST /auth/password-reset/request`, #2043); 1.31 (IP-Rate-Limits zählen in geteiltem Speicher, #2045); 1.30 (Neuer Bestätigungslink per `POST /auth/resend-verification`, #2037); 1.29 (SEC-H-009 Bedingung 1 an den neuen Default angepasst, #1948)
Abhängigkeit: REQ-024 v1.4 (Permission-Matrix), UI-NFR-012 (PWA-Offline)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.46 | 2026-10-05 | **#2121 (MT-025, Spec an den Code angeglichen; reine Spec-Änderung).** Gemessen gegen `develop` (`b064e63b7`): (1) **§5a nannte die Plattform-Rolle `role: admin`** (Beispiel §5a.1, Ableitung §5a.2, Dependency §5a.3, Szenario §5a.6, §5b.3, AK-18, AK-28/AK-29) — seit Migration `v0032` heißt sie `lead` (`app.common.auth.is_platform_admin`: aktive Mitgliedschaft mit `TenantRole.LEAD` im Mandanten `platform`; REQ-049 §2.5). Alle Stellen auf `lead` umgestellt, auch im gestrichenen §5a.5.2 (Vokabular, keine Wiederbelebung). (2) **`tenant_roles` im Access Token ist informativ:** `AuthService` stellt das Token mit leerem `tenant_roles` aus; `is_platform_admin` wird beim Ausstellen aus der gespeicherten Mitgliedschaft abgeleitet. Keine Autorisierungsentscheidung liest einen der beiden Claims — die Wächter lesen Mitgliedschaften zur Laufzeit (§2 Abweichungstabelle, §3.1, §5a.2, AK-19). (3) **Plattform-Viewer** (`viewer` im Mandanten `platform`, §5a.1) ist **nicht implementiert** (#2179): eine solche Mitgliedschaft gewährt keinerlei Admin-Zugriff (REQ-024 §1a.4). (4) **§5a.4 Umsetzungsstand** und **AK-42–AK-55** mit Status: Notfall-Verwaltung gestrichen (v1.43), Mandanten-Sperre über den Zustand `suspended` (#2105, #2123), Konto-Sperre über `PATCH /admin/platform/users/{key}` (`is_active`, beendet Sitzungen, #2116); offen: Selbstsperre/letzter Plattform-Admin (#2144), Celery-Pause gesperrter Mandanten (#2143). Neuer Guard: `test_spec_literal_discriminators_match_models.py` prüft Rollen-Literale in REQ-023/024/049 gegen `TenantRole`/`AdminScope`. |
| 1.44 | 2026-10-05 | **Sitzungs- und Token-Lebenszyklus (#2158, #2116, MT-019).** (1) **#2158:** Die Spezifikation verlangte für `email_verification_token` und `password_reset_token` schon „gehashed gespeichert"; gemessen wurde der Klartext gespeichert und per Wert gesucht (echter Dienst gegen echte ArangoDB, Dokument-Dump). Die Felder heißen jetzt `email_verification_token_hash` / `password_reset_token_hash` und halten den SHA-256-Hex-Digest (`TokenEngine.hash_token`, wie Refresh-Token und API-Keys; kein HMAC — 256 Bit Zufall sind ohne Schlüssel nicht zu erraten); die Suche hasht den vorgelegten Link. Ablauf und Einmalnutzung unverändert. Migration `v0086` hasht gespeicherte Klartexte per AQL `SHA256()` und entfernt die alten Attribute — vor dem Update verschickte Links funktionieren noch genau einmal (Entscheidung: hashen statt löschen, weil ein verlorener Bestätigungslink die Anmeldung blockiert, §3.2b). (2) **#2116, §3.2a umgesetzt** mit den unten im Abschnitt „Umsetzungsstand" genannten Abweichungen vom Pseudocode (kein Hard Cutover, Client-Abgleich über `User-Agent` statt `device_id`, Gnadenpfad gibt nur ein Access Token aus, kein eigener Fehlercode, keine Prometheus-Zähler). Rotierte Tokens bleiben bis zu ihrem eigenen `expires_at` gespeichert (Replay-Signal; NFR-011 R-11 v1.41). (3) **AK-14 gilt jetzt auch für Access Tokens:** `users.session_generation` und `users.access_token_generation` (§Datenmodell); jedes Access Token trägt `gen` (und `sid` = Family); `FullAuthProvider` lehnt ein Token ab, dessen `gen` nicht der des Kontos entspricht — ohne zusätzlichen Lesezugriff (gemessen: 1 Konto-Lesezugriff je Anfrage vorher wie nachher, der Vergleich kostet < 1 µs). Jeder Widerruf erhöht die Generation: Logout (Family), Session-Widerruf (Family), Logout-all, Passwort-Reset und -Wechsel, E-Mail-Wechsel und Rücknahme, Art.-17-Antrag, Admin-Deaktivierung (neu: beendet jetzt auch die Sitzungen), erkannter Replay. Ein Generationszähler statt `sessions_invalid_before`/`iat`-Zeitstempel: `iat` hat Sekundenauflösung und Replikas können in der Uhr abweichen; ein Zähler ist exakt. Rollenentzug braucht keinen Schnitt: Rollen und Plattform-Admin werden je Anfrage aus der Mitgliedschaft gelesen, nicht aus dem Token. Nur das Refresh-Token-Repository schreibt die Zähler (in derselben AQL-Anweisung wie der Widerruf); das User-Repository lässt sie aus jedem Schreibvorgang heraus, damit ein `update_fields` mit vor dem Widerruf gelesenem Konto sie nicht zurücksetzt. |
| 1.43 | 2026-10-05 | **#2134 (MT-038) — §5a.5.1 Verwaist-Erkennung und §5a.5.2 Emergency-Admin-Ernennung gestrichen (Entscheidung „streichen“, nicht umsetzen).** Gemessen: Weder der wöchentliche Celery-Task noch `POST /admin/tenants/{tenant_key}/emergency-admin` noch `orphaned_since` existieren im Code; die Plattform-Admin-Routen kennen keine Vergabe des Scopes `management`. Die beiden Wege, auf denen eine Organisation ihre letzte Verwaltung verliert, sind jetzt geschlossen statt nachträglich repariert: freiwillig (Entfernen, Austritt, Scope-Entzug) verhindert INV-1 (REQ-024), und die Kontolöschung — der einzige Weg ohne INV-1 — übergibt die Verwaltung an die dienstälteste Leitung oder setzt die Organisation auf `orphaned` und plant ihre Löschung mit der Gnadenfrist (REQ-025 §3.1.3 Regel 4, REQ-024 AK-52/AK-65). Eine verwaiste Organisation wird nicht wiederbelebt (kein Notfall-Admin, kein Abbruch der Löschung); Mitglieder und Plattform-Admins werden benachrichtigt, das Admin-Panel zeigt sie. §5a.5.3 (Suspendierung) ist mit #2105/#2123 als Zustand `suspended` umgesetzt. **#2123 (§3.9):** neue Step-up-Aktion `tenant_erasure_cancel` (Abbruch einer geplanten Mandantenlöschung), gebunden an den Mandantenschlüssel; Zielprüfung wie `tenant_deletion`. |
| 1.42 | 2026-10-05 | **#2132 (MT-036, §3.2d, AK-56):** Im Full-Modus legte `POST /auth/register` — und ebenso die erste OIDC-Anmeldung einer unbekannten Adresse — für jeden ein Konto an; es gab keinen Schalter. Neu (**Betreiberentscheidung 2026-10-04**): `REGISTRATION_MODE` = `open` (Default, unverändertes Verhalten) \| `invite_only` \| `closed` und eine optionale Domain-Allowlist `REGISTRATION_ALLOWED_DOMAINS`. Gelesen gilt: Eine **E-Mail-Einladung** (offen, nicht abgelaufen, für genau diese Adresse) ist die Ausnahme von `invite_only` und von der Allowlist — lokal bewiesen durch ihr Token (`invitation_token` im Registrierungs-Body), bei der ersten OIDC-Anmeldung durch die vom Anbieter bestätigte Adresse (`email_verified`); **`closed` lässt niemanden zu, auch nicht mit Einladung** (sonst wären `closed` und `invite_only` derselbe Modus). Eine Link-Einladung öffnet keine Registrierung. Jede Ablehnung ist dieselbe `403 REGISTRATION_NOT_ALLOWED`, entschieden vor jedem Lesen gespeicherter Konten (kein Enumerations-Orakel). `GET /mode` meldet `registration: {mode, domain_restricted}`; Login- und Registrierungsseite passen sich an. Bestehende Konten melden sich in jedem Modus an. Light-Modus unberührt (keine `/auth`-Routen; `/mode` meldet dort `closed`). Guard: `test_account_creation_asks_the_registration_policy.py` — jede Funktion, die ein Konto anlegt, fragt die eine Prüfstelle. |
| 1.41 | 2026-10-04 | **#2106 (§3.9):** Eine weitere Aktion läuft durch den Step-up: `admin_membership_add` (das Hinzufügen eines Kontos zu einem Mandanten durch einen Plattform-Admin, `POST /admin/platform/tenants/{key}/members` und `…/users/{key}/memberships`), gebunden an das Paar `<tenant_key>|<user_key>` (die Mitgliedschaft gibt es noch nicht; `|` ist kein Zeichen eines Dokumentschlüssels, das Paar ist eindeutig). Die Zielprüfung beim Ausstellen verlangt einen Plattform-Admin sowie einen vorhandenen Mandanten und ein vorhandenes Konto (403 vor 404). Die Registrierung nimmt ein angelegtes Konto zurück, wenn der Anbieter- oder Mandant-Schreibvorgang scheitert (#2118). |
| 1.40 | 2026-10-04 | **Restbefunde aus #2043/#2045/#2046 (#2062):** (1) **Alle Valkey-Clients der Request-Pfade warten höchstens 0,5 s** (§3.2c): `_get_redis_client()` (Geräte-Kopplung, API-Key-Limiter, MCP-Sitzungen, Identifikations-Limiter) und der OAuth-State-Store nutzten die redis-py-Vorgabe von 5 s je Socket-Operation — gemessen gegen einen Socket, der annimmt und nie antwortet: 5,01 s je Aufruf, die anonyme Kopplungs-Einlösung 10,10 s; jetzt 0,50 s und 1,10 s. Ein Guard verlangt `bounded_redis_client_options()` von jedem in `app/` gebauten Valkey-Client. (2) **Reihenfolge von Token und Mail** (§3.2b): Token-Schreiben und Versand laufen je Konto und Tokenart unter einem Prozess-Lock; vorher konnte die zuletzt eintreffende Mail ein bereits überschriebenes Token tragen (deterministisch reproduziert, Bestätigung und Reset). Je Prozess, nicht je Replik. (3) **Summe je Postfach gemessen** (§3.2b): 16 Mails in einem Fenster (3 anonym, 3 bewiesen, 10 Reset), nicht „bis zu 9“; bewusst kein gemeinsames Budget (ein Squatter könnte sonst den Reset der Inhaberin verbrauchen, vgl. §3.2c „Aussperren durch Dritte“). (4) **Valkey ohne AUTH** (§3.2c): Entscheidung für den Betreiber festgehalten. (5) Guard `anonymous_mail_routes`: anonym heißt „kein `get_current_user` im Abhängigkeitsbaum“ (vorher: Namenspräfix `require_*`/`get_current_*`), `async def`-Methoden werden gelesen. |
| 1.39 | 2026-10-04 | **#1906 (§4.1, §3.9):** Die OIDC-Provider-Konfigurationen haben eine eigene Admin-Seite `/admin/oidc-providers` (Plattform-Admin, erreichbar im Tab „Plattform-Modus" der Kontoeinstellungen): Liste, Anlegen, Bearbeiten, Löschen und Discovery-Test über `/api/v1/admin/oidc-providers`. Anlegen, Löschen und jede Änderung außer `display_name` und `icon_url` laufen im Dialog `StepUpConfirmDialog` mit der Aktion `oidc_provider_change` (Ziel: Schlüssel der Konfiguration, beim Anlegen `new:<slug>`); `display_name` und `icon_url` speichern ohne Dialog. Das Client-Secret ist schreibgeschützt: Die Schnittstelle gibt es nie zurück, die Seite zeigt es nie an, ein leeres Feld beim Bearbeiten behält das gespeicherte. Feste Endpunkte (`authorization_url`, `token_url`, `userinfo_url`, `jwks_url`) und der Standard-Mandant lassen sich beim Anlegen setzen; die Antwort enthält sie nicht, die Seite zeigt sie später nicht an. Die Aussage „nur über die API verwaltbar" im Admin-Handbuch (#1980) entfällt. Testfälle TC-023-077 bis TC-023-079. |
| 1.38 | 2026-10-04 | **Bestätigungsnachweis (#1948):** `users.email_confirmed_at` hält fest, dass der Inhaber der Adresse sie belegt hat. Gesetzt nur vom Bestätigungslink (`POST /auth/verify-email`), der Bestätigung des E-Mail-Wechsels, dessen Revert-Link und von einem OIDC-Provider, der `email_verified` behauptet. `email_verified` allein belegt nichts: die Registrierung mit `REQUIRE_EMAIL_VERIFICATION=false` setzt es ohne Bestätigung, und das Umstellen auf `true` ändert gespeicherte Konten nicht. Deshalb liest REQ-030 §3.4 den Nachweis. Ein ohne Bestätigung registriertes Konto meldet sich weiter an (Anmelde-Gate bleibt `email_verified`), bekommt aber keine Benachrichtigungs-Mail, bis es einen Link bestätigt; `POST /auth/resend-verification` (§3.2b) stellt ihn mit `REQUIRE_EMAIL_VERIFICATION=true` auch solchen Konten aus. Migration v0080 stempelt bestehende verifizierte Konten (Grandfathering: Herkunft nicht unterscheidbar, sonst endete jede bestehende Mail beim ersten Deploy). Startwarnung `email_channel_without_verification`, wenn ein Versender (`EMAIL_ADAPTER` smtp/resend) mit `REQUIRE_EMAIL_VERIFICATION=false` zusammentrifft. Admin-gesetztes `email_verified` ist eine Zusicherung, kein Nachweis. |
| 1.37 | 2026-10-04 | **#2032 (§3.9):** Drei weitere Aktionen laufen durch den Step-up, jeweils an den Schlüssel der Mitgliedschaft gebunden (#1884): `admin_membership_role_change` (`PATCH /admin/platform/tenants/{tenant_key}/members/{membership_key}/role`, `PATCH /admin/platform/users/{user_key}/memberships/{membership_key}/role`), `tenant_member_role_change` (`PATCH /tenants/{slug}/members/{membership_key}/role`) und `tenant_member_removal` (`DELETE /tenants/{slug}/members/{membership_key}`) — das Konto, das den Step-up leistet, ist das **handelnde** (Plattform-Admin bzw. Mandanten-Verwalter mit `management`), nie das betroffene Mitglied. Die Tabelle und die Zielliste in §3.9 führen jetzt auch die Aktionen von #2009 (`admin_tenant_update`, `admin_membership_removal`). Die Routen: REQ-024 AK-56/AK-57. |
| 1.36 | 2026-10-04 | **#2010 (§3.5, AK-17):** Der Task `cleanup_unverified_accounts` erreichte bisher keine lokal registrierte, nie bestätigte Person: die Registrierung schreibt eine `LOCAL`-Anbieterzeile, und der Selektor behandelte jede Anbieterzeile als verknüpft (gemessen gegen eine echte ArangoDB). Betreiberentscheidung 2026-10-03: erst Trockenlauf. Der Task zählt diese Konten (`local_registrations_pending`) und löscht sie nur, wenn `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED` gesetzt ist; AK-17 gilt für Konten ohne Anbieterzeile uneingeschränkt, für lokale Registrierungen ab Freigabe. Einzelheiten: NFR-011 R-02, v1.28. |
| 1.35 | 2026-10-04 | **Nacharbeit zu #2043/#2045:** (1) **Ein Zähler je Route, nicht je Pfadwert (#2052):** der IP-Limiter nutzt `key_style="endpoint"`; vorher öffnete jeder vom Aufrufer gewählte Pfadwert (Glossar-Slug, Export-Schlüssel, Tenant-Slug) einen eigenen Zähler und einen eigenen Valkey-Schlüssel (gemessen: 31 Slugs → 31 × `200`). Details am Ende von §3.8. (2) **Limit-Prüfung nicht mehr auf der Ereignisschleife (#2048):** asynchrone begrenzte Routen prüfen über `run_in_threadpool`; `GET /api/health` zählt nur im Prozessspeicher. (3) **Rückfall-Stufe der anonymen Budgets verdrängt nicht (#2058):** eine volle Stufe wirft abgelaufene Einträge hinaus und behandelt sonst eine neue Adresse als über dem Budget; vorher verschaffte eine Flut von 4096 Adressen dem Opfer einen vierten Link. `maxmemory` des Chart-Valkey bleibt bewusst ungesetzt (§3.2c). (4) **Reset-Budget zweistufig (#2059):** 3 je Adresse und Client-IP, 10 Links je Adresse insgesamt (nur zugelassene Anfragen zählen); vorher hielt eine Quelle mit einer Anfrage je Stunde bis zu 1199 Adressen gesperrt (gemessen: 0 von 100 Inhaberinnen bekamen einen Link, danach 100 von 100). Log-Ereignis `password_reset_budget_exhausted` (nur Digest). Kein Admin-Weg — §3.2c sagt das jetzt ausdrücklich. (5) **Reset-Link an die gespeicherte Adresse (#2060):** `to_email=user.email` statt der eingegebenen Schreibweise; Python-`lower()` gegen AQL-`LOWER()` gemessen (13 abweichende BMP-Zeichen, nur in der sicheren Richtung). (6) **Restposten #2062:** Kontosuche des Resets nach der Antwort (gleiche Arbeit diesseits und jenseits des Budgets); `resolve_client_ip` akzeptiert nur IP-Adressen (kanonisch), Chart pinnt `TRUSTED_PROXY_HOPS` genau auf `1`; Ausfall-Signale `rate_limit_storage_never_reached` (Fehler-Level) und `rate_limit_storage_still_unavailable`; TC-023-015 auf die gelbe Warnung und den mitgeschickten Link aktualisiert; der Valkey-Client der Mail-Budgets hat jetzt den Prüfplan des Limiters (`LatchedRedis`) — gemessen 1,0 s je Reset-Anfrage während eines Hängers vorher, 0,0 s nach der ersten danach. |
| 1.34 | 2026-10-03 | **Bündel-Prüfung #2043/#2045/#2046:** (1) Die Mail-Budgets (§3.2b, §3.2c, Login-Ablehnung) und der Zähler für unbekannte Adressen bekamen ihren Valkey-Client mit den redis-py-Defaults (5 s je Socket-Operation): gemessen über die echten Routen 5,0 s für eine Reset-Anfrage, 5,3 s für eine Login-Ablehnung, 10,6 s für eine fehlgeschlagene Anmeldung mit unbekannter Adresse, auch je für acht gleichzeitige. Jetzt ein eigener, geteilter Client mit den Optionen des IP-Limiters (0,5 s je Verbindungsversuch und Adresse, keine Wiederholung): gemessen 0,51 s, 0,78 s und 1,3 s; ohne Prüfplan, Valkey wird bei jeder Anfrage gefragt. (2) Das Subject des anonymen Bestätigungslinks wird im Service getrimmt und kleingeschrieben wie das des Resets. (3) Korrigiert: Summe der drei Budgets je Postfach, Squatting-Fall und Admin-Ausweg, Neustart von Valkey, `@` im Passwort, Proxy-Benennung, Bedingung der unveränderten Header-Namen. |
| 1.33 | 2026-10-03 | **Neuer Bestätigungslink über die Login-Ablehnung (#2046):** Das Budget je Adresse von `POST /auth/resend-verification` (§3.2b) zählt jede eingegebene Adresse — wer eine fremde Adresse kennt, konnte es für den Inhaber aufbrauchen und ihm so jeden neuen Link vorenthalten (bisher als Restrisiko geführt). Neu: Die Ablehnung `403 EMAIL_NOT_VERIFIED` (nur nach korrektem Passwort erreichbar) verschickt den neuen Link selbst, nach der Antwort, an die gespeicherte Adresse des Kontos — auf einem eigenen Budget je Konto (Subject `verification-resend-proven:<user_key>`, 3 je Stunde, Valkey-geteilt mit In-Process-Rückfall, nie fail-open), das anonyme Anfragen nicht erreichen. Kein neuer Endpunkt, kein Passwort in einem weiteren Request-Body. Die Antwort bleibt unverändert (Status, Body, Header) — ob gesendet, Budget erschöpft oder Zustellung gescheitert; ein falsches Passwort antwortet wie bisher `401` ohne Mail. Die Login-Route gibt die Ablehnung zurück statt sie zu werfen, weil FastAPI Background-Tasks bei einer Exception verwirft (gemessen). Frontend: der Hinweis stellt den Link in Aussicht (nie „gesendet“), die anonyme Aktion bleibt Rückfall. Details in §3.2b. |
| 1.32 | 2026-10-03 | **Budget je Adresse beim Passwort-Reset (#2043):** `POST /auth/password-reset/request` war nur je Client-IP begrenzt (`RATE_LIMIT_AUTH`, `20/minute`); gemessen über die echte Route: 20 Reset-Mails an eine Adresse aus einer Quelle in einer Minute, jede mit neuem Link — rechnerisch 1200 je Stunde und Quelle, mit jeder weiteren Quelle mehr. Neu: ein Budget je Adresse wie beim Bestätigungslink (§3.2b) — 3 Anfragen, Auffüllung nach einer Stunde Ruhe, eigenes Budget (Subject `password-reset:<Adresse>`), reserviert vor der Kontosuche für jede eingegebene Adresse gleich, stumm (unverändert `200`, gleicher Body, gleiche Header). Groß-/Kleinschreibung und umgebende Leerzeichen teilen ein Budget. Bei Valkey-Ausfall Rückfall auf die In-Process-Stufe, nie fail-open. Details in §3.2c. |
| 1.31 | 2026-10-03 | **IP-Rate-Limits geteilt über Replikas (#2045):** Der slowapi-Limiter aller Auth-Routen zählte bisher im Prozessspeicher (`memory://`); N Prozesse vervielfachten jedes Limit um N. Der Zähler liegt jetzt im Speicher aus `RATE_LIMIT_STORAGE_URL` (leer = Valkey aus `REDIS_URL`); scheitert der Speicher mit einem Fehler des Redis-Clients, zählt jeder Prozess für sich weiter (kein Fail-open, kein 500, auch nicht für Anfragen, die beim Ausfall gerade warten; ein frisches Fenster je Prozess und Fenster, nicht je Ausfall); ein hängender Speicher kostet eine Anfrage des Limiters einen Socket-Timeout von 0,5 s je Verbindungsversuch und Adresse (die Mail-Budgets: 1.34) (DNS, mehrere Adressen, Verbindungsaufbau plus Handshake und `NOSCRIPT`-Nachladen nicht abgedeckt); jeder Prozess kehrt mit seiner eigenen nächsten Prüfanfrage zum geteilten Zähler zurück; `RATE_LIMIT_STORAGE_URL` (Schema `redis`, `rediss`, `redis+unix`, `memory` und Form) und `REDIS_URL` (Form) werden beim Laden geprüft, ohne den Wert zu nennen. Neues Log-Ereignis `forwarded_chain_deeper_than_trusted_proxy_hops` bei `TRUSTED_PROXY_HOPS=0` und mehrteiliger `X-Forwarded-For`-Kette (nicht gezählter Proxy oder vom Aufrufer selbst gesendeter Header). Details am Ende von §3.8 (Rate-Limit und Sperre bei Einlösung). |
| 1.30 | 2026-10-03 | **Neuer Bestätigungslink (#2037):** Neuer §3.2b — `POST /auth/resend-verification` stellt einem Konto, dessen erster Bestätigungslink verloren ging oder abgelaufen ist, einen neuen aus. Ohne ihn kam ein solches Konto mit `REQUIRE_EMAIL_VERIFICATION=true` nie mehr in die Anmeldung (`/auth/register` antwortet einer belegten Adresse nur mit der Info-Mail, ohne neuen Token). Enumerationssicher: immer `202` mit demselben Body für unbekannte, unbestätigte und bestätigte Adressen; vor der Antwort für jede Adresse dieselbe Arbeit (eine Budget-Reservierung), Kontosuche, Token-Schreiben und Versand danach (#1890). Jeder Versand schreibt einen neuen Einmal-Token (24 h) und macht damit alle früheren Links ungültig. Grenzen: je Client-IP `RATE_LIMIT_RESEND_VERIFICATION` (Default `10/hour`, `429`), je Adresse 3 Anfragen mit Auffüllung nach einer Stunde Ruhe (stumm, unveränderte `202`). Keine Mail ohne `REQUIRE_EMAIL_VERIFICATION`, an Service-Accounts, an Konten ohne lokales Passwort (nur föderiert) oder an deaktivierte Konten. Die Login-Ablehnung `EMAIL_NOT_VERIFIED` nennt den Weg; das Frontend bietet ihn auf der Login-Seite und auf der Fehlerseite eines ungültigen Links an (§4.1 `ResendVerificationPage`). |
| 1.29 | 2026-10-03 | **#1948 umgesetzt:** Der Default `true` ist ausgeliefert (Settings, Helm-Chart, Doku); E2E-Compose und Skaffold-Dev-Werte setzen `false` ausdrücklich. SEC-H-009 Bedingung 1 sagte noch „per Default `false`“ und begründete damit, dass eine echte Registrierung keine Mail verschickt — das stimmt nur noch mit `false`; mit `true` geht die Bestätigungsmail nach der Antwort raus (#1890). Die Bedingung bleibt unverändert gültig. |
| 1.28 | 2026-10-03 | **Betreiberentscheidungen #1948, #1906:** `REQUIRE_EMAIL_VERIFICATION` hat den Default `true`; OIDC-Provider werden über eine eigene Admin-Seite im Optionen-Bereich verwaltet (neuer Abschnitt vor „Benannte SSO-Provider“). |
| 1.27 | 2026-10-03 | **#2007, #2008 (Nacharbeit zu #1987):** (1) Der **Token-Endpunkt** (erhält Client-Secret und Autorisierungscode) und der **Userinfo-Endpunkt** (erhält das Access-Token) laufen vor dem Abruf durch `validate_oidc_fetch_url` (`app/common/url_safety.py`) — beim Login und beim Step-up (§3.9): Stammt der Endpunkt aus dem Discovery-Dokument, nie eine Metadaten-/Link-Local-Adresse, eine private nur auf dem Host des Ausstellers selbst oder mit `DEBUG`; vom Admin gesetzt (`token_url`, `userinfo_url`), nie eine Metadaten-/Link-Local-Adresse, eine private ist seine Wahl; die eingebauten Endpunkte von Google/GitHub bleiben ungeprüfte Konstanten. Ebenso wird `issuer_url` vor dem Abruf des Discovery-Dokuments geprüft (wie ein vom Admin gesetzter Endpunkt). Beide Antworten werden wie Discovery und JWKS gestreamt und auf 256 KiB (dekodiert, `Accept-Encoding: identity`) mit 10 s Gesamtfrist begrenzt gelesen; eine Antwort, die kein JSON-Objekt ist, verweigert. Ein verweigerter Endpunkt wird nie angesprochen; der Login endet mit `provider_error` (`oauth_endpoint_refused`, Grund nennt Endpunktart und Regel, nie Adresse), der Step-up mit `step_up_failed`. (2) **Step-up prüft `nbf` und `iat` bewusst nicht** (Entscheidung zu #2008, §3.9): ohne Signaturprüfung stammen die Claims nur vom Provider, und `nonce` (je Anfrage, State einmalig, 5 Minuten) sowie `auth_time` (≤ 300 s + 30 s) begrenzen enger, was eine `iat`-Untergrenze leisten würde. |
| 1.26 | 2026-10-03 | **#1992:** `PATCH /admin/platform/users/{key}` verlangt das Step-up des Administrators (§3.9; kein API-Schlüssel, 403) bei **jeder Änderung** von `email_verified` oder `is_active` — nicht mehr nur beim Anheben: Eine Änderung, die zur Löschung oder Sperrung eines fremden Kontos führen kann, ist eine Step-up-Handlung. Das erneute Senden unveränderter Werte und eine Namensänderung brauchen keines. Ein gesenktes `email_verified` wird als `email_verified_lowered_at` vermerkt; der Bereinigungstask `cleanup_unverified_accounts` (AK-17) wählt ein so vermerktes Konto nie aus. `DELETE /admin/platform/users/{key}` antwortet seit #1949 mit `202` (REQ-025 AK-IE-01). |
| 1.25 | 2026-10-03 | **OIDC-Härtung (#1987), Nacharbeit zu #1935/#1936/#1969:** (1) **https an der API-Grenze:** `issuer_url`, `authorization_url`, `token_url`, `userinfo_url` und das neue `jwks_url` lehnen `POST`/`PUT /admin/oidc-providers` mit `422` ab, wenn sie nicht `https` sind (kein Host, Zugangsdaten in der URL ebenfalls); `http` ist nur für Loopback (`localhost`, `127.0.0.1`, `::1`, nach geparstem Host, nie nach Präfix) und nur mit `DEBUG=true` erlaubt — dem bestehenden Entwicklungsschalter, kein neuer. Dieselbe Regel gilt beim Login für einen gespeicherten Endpunkt (`OAuthEngine._resolve_*_url`, `fetch_discovery_document`): eine vor diesem Stand gespeicherte `http`-Konfiguration wird nicht mehr angesprochen, der Login endet mit `provider_error`, und erst die nächste Bearbeitung, die das Feld mitsendet, scheitert mit 422. (2) **Verknüpfung an den unveränderlichen Schlüssel:** `AuthProvider.oidc_config_key` (neu, der `_key` der Konfiguration; der Slug bleibt Beschriftung und Abgleich für Alt-Zeilen). Der Callback prüft vor jedem Schreiben (Konto anlegen, Verknüpfung anlegen oder ändern), dass die geladene Konfiguration unter ihrem Slug noch dieselbe, aktivierte, beim selben Aussteller ist (`reason=configuration_changed`); eine Verknüpfung mit anderem Schlüssel gehört einer gelöschten Konfiguration, passt nie und wird beim nächsten Login des `sub` entfernt; die Wiederanmeldung (§3.9) übergeht sie ebenso. Alt-Verknüpfungen ohne Schlüssel gelten wie bisher über den Slug — keine Migration. `create_provider` legt die Konfiguration zuerst **deaktiviert** an (der eindeutige Slug-Index serialisiert zwei gleichzeitige Anlagen, der Verlierer löscht keine fremden Verknüpfungen), löscht dann die Waisen des Slugs und aktiviert sie erst danach; schlägt das Löschen fehl, verschwindet die neue Konfiguration wieder. (3) **JWKS:** Schlüsselmenge je Konfiguration (und je aufgelöster Quelle, also nie über eine Umstellung hinweg) für 10 Minuten im Prozessspeicher des Workers (`app/domain/engines/jwks_cache.py`; je Worker ein Cache, nichts geteilt); ein unbekanntes `kid` löst genau einen Neuabruf aus, höchstens einen je 10 s und Konfiguration; ein Fehler wird 30 s gemerkt, nie so lange wie ein Erfolg, und nach einem fehlgeschlagenen Neuabruf einer abgelaufenen Menge wird nichts Altes ausgeliefert. Antworten (JWKS und Discovery) sind auf 256 KiB gedeckelt; ein nicht importierbarer oder symmetrischer Schlüssel wird übersprungen, die Menge bleibt nutzbar. Ein vom Anbieter genanntes `jwks_uri` läuft durch `validate_oidc_fetch_url` (`app/common/url_safety.py`): `https`, nie eine Metadaten-/Link-Local-Adresse, eine private nur auf dem Host des Ausstellers selbst oder mit `DEBUG`; ein vom Admin gesetztes `jwks_url` darf privat sein. (4) **`nbf`** wird mit 30 s Toleranz geprüft (vorhanden und falsch, etwa nicht numerisch, verweigert), **`iat`** darf höchstens 10 Minuten (+ Toleranz) zurückliegen. (5) **`jwks_url`** ist in Anlage und Änderung setzbar; ein Umstellen des Ausstellers (nach `same_issuer`, ein Schrägstrich ist keine) löscht im selben Schreibvorgang die gespeicherten `authorization_url`/`token_url`/`userinfo_url`/`jwks_url`, die die Anfrage nicht neu nennt. (6) `POST /admin/oidc-providers/{key}/test` meldet zusätzlich `jwks_check` (Abruf wie im Login, Schlüsselzahl, übersprungene Einträge, `kid`s) und `issuer_check` (nimmt der Login den vom Anbieter angekündigten `iss`; bei Abweisung durch Discovery 4.3 mit dem angekündigten Wert), jeweils `applicable: false` ohne ID-Token (GitHub). |
| 1.24 | 2026-10-02 | **#1961:** `DELETE /admin/platform/users/{key}` bleibt eine Sofortlöschung ohne Karenzzeit (Betreiberentscheidung, REQ-025 v1.26): die anderen Mitglieder eines persönlichen Mandanten des Zielkontos erfahren in der E-Mail, dass die Löschung jetzt stattfindet. Vor der Bestätigung liest die Administrator-Oberfläche `GET /admin/platform/users/{key}/erasure-preview` (nur Plattform-Admin, Form wie `GET /privacy/erasure-preview`) und zeigt Mandantenname und Anzahl weiterer Mitglieder des **Zielkontos**; eine nicht ladbare Vorschau sagt das ausdrücklich. |
| 1.23 | 2026-10-02 | **OIDC-Login prüft das ID-Token; Löschen und Umstellen eines Providers hinterlässt nichts Fremdes (#1935, #1936, #1969):** (1) Der Login verifiziert ein ausgestelltes ID-Token (`OAuthEngine.authenticate_login`): **Signatur** gegen die JWKS des Anbieters (`jwks_url`, sonst `jwks_uri` des gültigen Discovery-Dokuments, sonst die dokumentierte URL von Google/Apple, sonst ein sofort abgerufenes und validiertes Discovery-Dokument; nur `https`, nur asymmetrische Algorithmen, kein `none`/`HS*`; jeder Abruffehler verweigert), `iss` (über `same_issuer`, also Googles beide Schreibweisen), `aud`/`azp`, `nonce` (gleich der im State gespeicherten), `exp` und `iat` (30 s Toleranz). Ein Provider mit `openid`-Scope (und Apple), dessen Antwort kein ID-Token enthält, wird verweigert. Das `sub` des ID-Tokens muss nicht leer sein; bei Identität aus dem Userinfo-Endpunkt muss dessen `sub` gleich dem des ID-Tokens sein (OIDC Core 5.3.2); ein leeres, fehlendes oder `null`-`sub` (bzw. GitHub-`id`) verweigert die Anmeldung, auch ohne ID-Token. Jede Verweigerung ist für den Browser dieselbe `?error=provider_error` (kein Orakel, keine Sitzung, kein Konto); geloggt wird nur `oauth_login_refused` mit `provider` und `reason` aus einem festen Vokabular, nie ein Wert. Der Step-up (§3.9) bleibt unverändert beim TLS-Ersatz für die Signaturprüfung. **Betreiberwirkung:** Ein Provider, dessen Token diese Prüfungen nicht besteht, meldet niemanden mehr an — Diagnose über `oauth_login_refused.reason` (siehe Admin-Handbuch). (2) `delete_provider` löscht die Konfiguration und danach **alle** Verknüpfungen mit ihrem `oidc_config_slug` samt verschlüsselten Provider-Token (`IAuthProviderRepository.delete_by_config_slug`; Log: nur die Anzahl `links_deleted`); `create_provider` löscht vor dem Anlegen Verknüpfungen, die ein früheres Löschen unter dem Slug hinterlassen hat (`orphan_links_deleted`). Entscheidung Löschen statt Entbinden: eine Verknüpfung ohne ihre Konfiguration meldet niemanden mehr an; ein „ungebundener“ Zustand wäre die mehrdeutige Alt-Verknüpfung (kollidiert am Unique-Index, wenn zwei gelöschte Konfigurationen dasselbe `sub` hielten) oder ein ungeprüftes Tombstone-Vokabular. Keine Migration nötig — vor diesem Stand hinterlassene Waisen werden beim nächsten Anlegen unter ihrem Slug entfernt. (3) Das Umstellen von `issuer_url` oder `provider_type` setzt `discovery_document` und `discovery_refreshed_at` im selben `update_fields`-Schreibvorgang auf `null`; bei geändertem `issuer_url` werden zudem die Verknüpfungen der Konfiguration **ohne** gespeicherten Aussteller gelöscht (sie passten sonst auf jeden Aussteller, der erste Login des neuen IdP würde sie übernehmen), solche mit Aussteller verweigern den neuen IdP selbst. Zusätzlich nutzt die Engine ein gespeichertes Discovery-Dokument nur, solange sein `issuer` der konfigurierte ist (`OAuthEngine.usable_discovery`; Endpunkte und erwarteter `iss` kommen nie aus dem Dokument eines anderen Ausstellers). `fetch_discovery_document` lehnt ein Dokument ab, das kein JSON-Objekt ist, dessen `issuer` nicht der abgerufene ist (OIDC Discovery 4.3) oder dem `authorization_endpoint`, `token_endpoint` oder `jwks_uri` fehlt, oder dessen Endpunkte (einschl. `userinfo_endpoint`) nicht `https` sind; Apple erwartet `iss` = `https://appleid.apple.com` unabhängig von `issuer_url` — Rotation zählt es als Fehler und schreibt nichts, der Admin-Test meldet den Abruffehler. |
| 1.22 | 2026-10-02 | **Ausfallender Mail-Versand als Enumerations-Orakel geschlossen (#1890); Discovery-Rotation ohne Voll-Snapshot (#1909):** (1) `POST /auth/password-reset/request` und `POST /auth/register` (bei `require_email_verification`) versenden die Mail jetzt **nach** dem Schreiben der Antwort (FastAPI-Background-Task) und fangen jeden Versandfehler ab; beim Reset wandert auch das Schreiben des Reset-Tokens in den Background-Task, damit der Request-Pfad für bekannte und unbekannte Adresse dieselbe Datenbankarbeit leistet (`AuthService._deliver_mail`). Vorher beantwortete ein bekannter Absender (Reset) bzw. eine freie Adresse (Registrierung) einen SMTP-Ausfall oder ein Resend-429 mit 500, die jeweils andere Seite mit 200/201 — ein Orakel, das SEC-H-009/010 schließen sollten, samt Laufzeitunterschied durch den synchronen Versand. Der Fehler wird als `auth_mail_send_failed` mit `kind` und Fehlertyp geloggt, nie mit Adresse oder Fehlertext; ein Wiederholungsversuch findet nicht statt (kein dauerhafter Ausgang, der Token oder Adresse in einen zweiten Speicher legen würde) — die Person fordert erneut an. Der Mailversand der Schrittbestätigung (`503 STEP_UP_CODE_UNDELIVERABLE`, v1.17) und der E-Mail-Änderung bleibt bewusst unverändert: beide laufen angemeldet bzw. antworten in beiden Zweigen gleich. (2) `rotate_oidc_discovery` schreibt per `IOidcConfigRepository.update_discovery` nur `discovery_document` und `discovery_refreshed_at` und nur, solange der Issuer noch der abgerufene ist; ein während des (bis zu 15 s langen, vom Issuer getakteten) Abrufs per Schrittbestätigung geänderter Provider (`enabled`, Secret, Issuer) wird nicht mehr zurückgesetzt. |
| 1.21 | 2026-09-30 | **OAuth/OIDC-Login: eine Rückruf-URL, Verknüpfung je Konfiguration (#1865, #1869):** (1) Der Login bildet die Rückruf-URL `{APP_BASE_URL}/api/v1/auth/oauth/{slug}/callback` aus der konfigurierten öffentlichen Basis-URL (nicht mehr aus `request.base_url`/Host-Header), legt sie im OAuth-State ab und tauscht den Code mit genau diesem Wert (RFC 6749 §4.1.3); bisher ging an den Token-Endpunkt `{FRONTEND_URL}/auth/callback`. Ein State ohne `redirect_uri` (vor dem Deployment ausgestellt) wird verweigert (`invalid_state`). Login und Step-up nutzen dieselbe Funktion. (2) Der Login ordnet eine Anbieter-Verknüpfung nur noch über (Konfiguration, `sub`) zu, nicht über (Typ, `sub`): `sub` ist nur je Aussteller eindeutig, und alle generischen OIDC-Konfigurationen speichern unter dem Typ `oidc` — eine Identität bei IdP A mit dem `sub` eines Opfers bei IdP B meldete sich bisher **als das Opfer** an. Wo die Verknüpfung einen Aussteller gespeichert hat, muss `iss` passen (ohne abschließenden `/`, ein fehlendes Schema gilt als `https://` — Google sendet beide Schreibweisen); passt er nicht, wird die Anmeldung mit `link_requires_password` verweigert, ohne ein Konto anzulegen. Eine Verknüpfung ohne gespeicherten Aussteller übernimmt ihn bei der ersten Anmeldung. Eine Verknüpfung ohne `oidc_config_slug` (vor #1815) passt zu keiner Anmeldung und ist auch für die erneute Anmeldung (§3.9) nicht mehr fähig: Migration v0064 bindet beim Deployment jede, deren Typ genau **eine** Konfiguration hat (aktiv oder nicht); eine danach noch ungebundene war mehrdeutig und wird nicht geraten — die Anmeldung läuft dann über den E-Mail-Auto-Link-Pfad, der Step-up über den E-Mail-Code. Der eindeutige Index auf `auth_providers` ist jetzt `[provider, oidc_config_slug, provider_user_id]`; Migration v0064 bindet eindeutige Alt-Verknüpfungen und entfernt den alten Index `[provider, provider_user_id]`. |
| 1.20 | 2026-09-26 | **Zielbindung und OIDC-Provider-Konfiguration (#1883, #1884):** Code und `step_up_token` einer Aktion auf etwas anderes als das eigene Konto (`admin_account_update`, `admin_account_erasure`, `tenant_deletion`, `provider_unlink`, neu `oidc_provider_change`) sind zusätzlich an das **Ziel** gebunden (Schlüssel des anderen Kontos, des Mandanten, der Provider-Verknüpfung bzw. der OIDC-Konfiguration, `new:<slug>` beim Anlegen). `POST /users/me/step-up-code` und `POST /users/me/step-up/oidc` verlangen dafür das Feld `target` (422 ohne; 422 auch, wenn eine Aktion auf das eigene Konto eines nennt) und stellen den Faktor nur für ein existierendes Ziel aus, auf das die anfragende Person handeln darf (403 vor 404, Betreiber-Entscheid D2). **Breaking** für API-Clients außerhalb des Frontends, die für diese Aktionen Codes oder Reauth-Token anfordern. `POST`/`PUT`/`DELETE /admin/oidc-providers` laufen durch den Step-up des Admins (`oidc_provider_change`); ohne Step-up bleiben nur `display_name` und `icon_url`; auch das Ein- und Abschalten eines Providers verlangt ihn (Betreiber-Entscheide D5/D6, D6 nach Security-Review SEC-001 korrigiert). |
| 1.19 | 2026-09-26 | **Step-up vor Anmeldemitteln und Vertrauensanhebung (#1847, #1857):** `POST /auth/api-keys`, `POST /auth/device-pairing` und `DELETE /users/me/providers/{provider_key}` laufen durch den Step-up aus §3.9 (Aktionen `api_key_creation`, `device_pairing`, `provider_unlink`; Body-Felder `current_password`/`step_up_token`/`step_up_code`). Damit kann auch ein API-Key keinen API-Key und keinen Kopplungscode mehr ausstellen (403). `PATCH /admin/platform/users/{key}` verlangt den Step-up des Admins (`admin_account_update`), sobald `email_verified` oder `is_active` von false auf true wechselt. Im Light-Modus entfällt der Step-up beim API-Key (einziges Systemkonto, kein Mensch zu bestätigen). Umgesetzter Standard, offene Betreiber-Entscheidung (Fragenliste #1650): Passwortänderung, Passwort-Reset und „überall abmelden" widerrufen API-Keys **nicht** (Begründung in §3.9). |
| 1.18 | 2026-09-26 | **Frische OIDC-Anmeldung als Regelfall des Step-up (#1815, Betreiber-Entscheid Variante 1):** Neuer Endpunkt `POST /users/me/step-up/oidc` (`{action, provider_key?}` → `{authorization_url}`, `prompt=login`+`max_age=0`) — für ein Konto ohne lokales Passwort mit mindestens einem OIDC-fähigen verknüpften Anbieter (Google, generisches OIDC mit `openid`-Scope) jetzt der Weg, unumkehrbare Aktionen und Zugangsdaten-Änderungen zu bestätigen, statt des E-Mail-Codes. Der bestehende OAuth-Callback meldet dabei niemanden an, sondern leitet auf `/auth/step-up/callback` weiter: Erfolg als `#step_up_token=…&action=…` im URL-Fragment, Fehler als `?error=step_up_failed\|step_up_stale\|step_up_cancelled`. Geprüft werden `iss`, `aud`/`azp`, `nonce`, `exp`, dass `sub` zu einer Verknüpfung dieses Kontos gehört, und dass `auth_time` höchstens fünf Minuten alt ist (30 s Uhrtoleranz) — keine JWKS-Signaturprüfung, weil das ID-Token direkt vom Token-Endpunkt über TLS in einem client-authentifizierten Austausch kommt (OIDC Core 3.1.3.7 Nr. 6). Der `step_up_token` ist fünf Minuten gültig, an Konto und Aktion gebunden, einmal verwendbar; neue Nachweis-Methode `oidc_reauth`. Neuer Fehlercode `STEP_UP_REAUTH_REQUIRED` (401, 422 beim Anfordern eines Codes) und `STEP_UP_REAUTH_FAILED` (401, nur als Redirect-Fehlercode). **Anbietergrenze:** GitHub ist reines OAuth2 ohne ID-Token, Apple liefert kein `auth_time` — ein Konto, dessen verknüpfte Anbieter ausschließlich aus diesen beiden bestehen, behält den E-Mail-Code als Ausweichweg (`EMAIL_CODE_FALLBACK = True`); jedem anderen Konto mit OIDC-fähigem Anbieter wird der Code verweigert. Begründung für den Ausweichweg statt einer Verweigerung ganz ohne Alternative (Variante 2): Sonst könnten GitHub/Apple-only-Konten ihr Art.-17-Löschrecht nicht mehr selbst ausüben. |
| 1.17 | 2026-09-25 | **Unzustellbarer Step-up-Code (/code-review of #1862):** Scheitert der Mailversand eines Bestätigungscodes (Konsolen-Adapter außerhalb `debug`, SMTP-Fehler), antwortet `POST /users/me/step-up-code` jetzt 503 `STEP_UP_CODE_UNDELIVERABLE` statt 202 zu melden und den Code stillschweigend zu verwerfen; der Code wird zurückgenommen und sein Platz im Stundenkontingent sowie die 60-Sekunden-Wartezeit werden freigegeben, sodass ein Versuch nach Behebung durch den Betreiber sofort möglich ist. Die Redis-Ausgabereservierung läuft als ein `SET NX`-Schritt gegen ein Race zweier gleichzeitiger Anfragen. Zusätzlich laufen bei der Passwortänderung die Passwort-Policy-Prüfung und bei der E-Mail-Änderung die zustandslosen Prüfungen (eigene Adresse, reservierte Domain) jetzt **vor** dem Step-up, damit ein Tippfehler keinen Code und keinen gedrosselten Versuch verbraucht — nur der Adress-Lookup (frei/vergeben) bleibt hinter dem Step-up. |
| 1.16 | 2026-09-25 | **Security-Review von #1815/#1841:** Der E-Mail-Code aus `POST /users/me/step-up-code` bindet jetzt die Aktion in den Digest (`HMAC(Schlüssel, "Konto:Aktion:Code")`) — Pflichtfeld `action` im Request-Body (`account_erasure`, `admin_account_erasure`, `tenant_deletion`, `password_change`, `email_change`; fehlend/unbekannt → 422); ein für eine Aktion angeforderter Code bestätigt keine andere, die Mail nennt die Aktion. Der Digest ist jetzt ein HMAC-SHA256 unter einem aus `JWT_SECRET_KEY` abgeleiteten Schlüssel, damit ein Valkey-Dump die 10⁸ möglichen Codes nicht offline umkehrbar macht. Neue Ausgabegrenzen: ein noch unverbrauchter Code jünger als 60 Sekunden wird nicht ersetzt, höchstens 5 Codes pro Konto und Stunde — beide Male 429 `STEP_UP_LOCKED` mit `retry_after_minutes`. `POST /users/me/step-up-code` und `POST /users/me/password` verweigern zusätzlich im Light-Modus (403, #1844): das einzige Konto der Instanz hat kein Passwort, ein dort gesetztes würde nach dem Wechsel in den Full-Modus zur gültigen Anmeldung. |
| 1.15 | 2026-09-25 | **E-Mail-Code-Step-up für Konten ohne lokales Passwort (#1815); Step-up jetzt auch auf der E-Mail-Änderung (#1841):** Ein Konto ohne lokales Passwort (ausschließlich föderiertes Sign-in) bestätigt eine unumkehrbare Aktion oder eine Zugangsdaten-Änderung nicht mehr mit dem bloßen zurückgetippten Ziel, sondern mit einem per E-Mail zugestellten Einmalcode. Neuer Endpunkt `POST /users/me/step-up-code` (202, `{expires_at, expires_in}`, nie der Code selbst): acht Ziffern, zehn Minuten gültig, einmal verwendbar, als `step_up_code` im Step-up-Body von Kontolöschung, Mandantenlöschung und der ersten Passwortvergabe. Verweigert 403 einer API-Key-Anfrage, einem Dienstkonto oder im Light-Modus, 422 einem Konto mit lokalem Passwort. Ein fehlender Code antwortet 401 `STEP_UP_CODE_REQUIRED`, ein falscher zählt in dasselbe Drossel-Budget wie ein falsches Passwort. Kein OIDC-Re-Login mit `max_age`/`auth_time`: GitHub ist reines OAuth2 ohne `auth_time`, das hätte eine Provider-Klasse auf dem alten Stand belassen. `POST /privacy/email-change` (REQ-025 Art. 16) läuft jetzt ebenfalls durch diesen Step-up. Betriebsvoraussetzung: Ein föderiertes Konto braucht dafür funktionierenden Mail-Versand (`EMAIL_ADAPTER=smtp`) — mit dem Konsolen-Adapter und `DEBUG=false` (die produktive Voreinstellung ohne SMTP-Konfiguration) wird der Code nie zugestellt, und ein solches Konto kann sich dann nicht löschen, kein erstes lokales Passwort setzen, keinen Mandanten löschen und die E-Mail-Adresse nicht ändern. |
| 1.14 | 2026-09-25 | **Step-up für unumkehrbare Kontoaktionen (#1813, #1814, #1816):** Neuer §3.9. Eine einzige Prüfung (`StepUpVerifier`) für Kontolöschung (`DELETE /users/me`, `POST /privacy/erasure`), Konto-Sofortlöschung durch Plattform-Admins (`DELETE /admin/platform/users/{key}`), Mandantenlöschung (REQ-024 AK-44d) und Passwortänderung: nur aus einer angemeldeten Sitzung eines Menschen (kein API-Key, kein Service Account — 403), Ziel wird zurückgetippt (E-Mail bzw. Slug — 422), das eigene aktuelle Passwort bei lokalem Konto (401). Fehlgeschlagene Passwort-Step-ups werden je Konto **und** Client-Adresse gezählt (Valkey, In-Process-Fallback) und über denselben `LoginThrottleEngine` gesperrt (429 `STEP_UP_LOCKED`), zusätzlich mit kontoweiter Obergrenze; die Login-Sperre bleibt bewusst unberührt. `DELETE /users/me` setzt nicht mehr nur einen Tombstone, sondern eröffnet den Art.-17-Löschauftrag (REQ-025). |
| 1.12 | 2026-08-12 | **QR-Gerätekopplung für native Clients (#1118):** Neuer §3.8 — eine per QR-Code gekoppelte App tauscht einen Einmalcode gegen das **bestehende** REQ-023-Token-Paar (keine neue Token-Klasse, kein neuer Claim). Der Code liegt ausschließlich in Redis (kein neuer ArangoDB-Node, keine neue Collection); die Prüfspur sind structlog-Events, kein persistiertes Protokoll (§9). Einlösung ist rate-limitiert (`rate_limit_device_pairing_redeem`, Default 10/min) und zusätzlich per Quell-IP über den `LoginThrottleEngine` gesperrt — dieselbe Engine wie `login_local` —, wobei die Sperre **vor** dem Code-Store greift. `POST /auth/refresh` erhält einen Body-Transport (`{"refresh_token": …}`) für Clients ohne Cookie-Jar: Body schlägt Cookie, CSRF entfällt auf dem Body-Pfad (die Double-Submit-Tabelle in §1 ist entsprechend präzisiert). Neuer Frontend-Dialog „Gerät verbinden" im Sessions-Tab (§4.6). TTL `device_pairing_ttl_seconds` (Default 90, validiert 60–120). |
| 1.11 | 2026-08-07 | **SEC-H-009 Info-Mail gebaut (#958):** Die in §3.2 seit v1.8 geforderte Info-Mail an die bereits registrierte Adresse ist implementiert — aber unter zwei Bedingungen, die §3.2 jetzt ausformuliert, weil die naive Variante genau das Enumeration-Orakel wieder öffnet, das #957 geschlossen hat: (1) **asynchrone Zustellung** über den Celery-Task `app.tasks.auth_tasks.send_duplicate_registration_notice`, eingereiht in einem FastAPI-Background-Task, also erst nachdem die Antwort geschrieben ist; (2) **Sperrfenster je Empfängeradresse** (24 h, `IRegistrationNoticeStore`) statt je Absender-IP. Zusätzlich: `POST /api/v1/privacy/email-change` erhält ein eigenes Rate-Limit (`rate_limit_email_change`, Default 5/hour). |
| 1.10 | 2026-04-27 | **W-015:** §3.7 M2M-Auth um Light-Modus-Hinweis ergänzt — Service Accounts und API-Keys sind im Light-Modus deaktiviert (REQ-027 §2.1). Bei Mode-Switch Light→Full müssen externe Integrationen neue Keys generieren. |
| 1.9 | 2026-04-27 | **W-004 Fix (Refresh-Token Family + Offline-Grace-Window):** RefreshToken-Modell um `family_key`, `device_id`, `rotated_at`, `successor_key` erweitert. Token-Rotation idempotent innerhalb 60s Grace-Window bei Device-Match (für PWA-Reconnect-Race UI-NFR-012 R-049). Echter Replay (außerhalb Grace-Window oder Device-Mismatch) sprengt die ganze Token-Family. **Hard Cutover bei Deployment** — alle bestehenden Refresh-Tokens werden invalidiert, alle User müssen neu einloggen. Telemetrie: structlog `auth.refresh_replay_detected` + Prometheus `kp_auth_refresh_replay_total`. |
| 1.8 | 2026-03-18 | **Security-Hardening (IT-Security-Review):** (1) SEC-M-001: PII-Minimierung im JWT-Payload — `email` und `display_name` entfernt, nur `sub`, `tenant_roles`, `is_platform_admin` im Access Token. (2) SEC-H-009: Account-Enumeration-Schutz bei Registrierung — generische Antwort bei existierender E-Mail. (3) SEC-M-002: RS256/ES256-Migrationsplan dokumentiert, JWT-Secret >= 256 Bit. |
| 1.7 | 2026-03-17 | **Service Accounts, RBAC-Erweiterung & Tenant-Notfallverwaltung:** (1) `account_type: Literal['human', 'service']` auf User-Modell. Service Accounts als eigenständige, nicht-interaktive Konten für Third-Party-Systeme (Home Assistant, Grafana, CI/CD). Keine Passwort/SSO-Fähigkeit, API-Key-only. Tenant-scoped oder Platform-scoped. ServiceAccountEngine, ServiceAccountService, 15 neue API-Endpoints. Rate-Limit und IP-Allowlist pro Service Account. (2) Tenant-Notfallverwaltung: Emergency-Admin-Ernennung bei verwaisten Tenants (`orphaned_since`), Tenant-Suspendierung/Reaktivierung, User-Suspendierung/Reaktivierung durch Platform-Admin. 7 neue Admin-API-Endpoints. Celery-Task für Verwaist-Erkennung. |
| 1.6 | 2026-03-16 | **Platform-Admin-Rolle:** Neues Konzept Platform-Tenant (`is_platform: true`) als Träger der KA-Admin-Berechtigung. Platform-Admins verwalten globale Stammdaten, `tenant_has_access`-Zuweisungen und Promotions. User kann gleichzeitig Platform-Admin und regulärer Tenant-Nutzer sein. Neue User Stories, JWT-Erweiterung (`is_platform_admin`), Dependency `is_platform_admin`. |
| 1.5 | 2026-02-28 | Home Assistant Integration: `ha_url` + `ha_token_encrypted` auf User-Modell, neuer Tab „Integrationen" in AccountSettingsPage, Verbindungstest-Endpoint. Temperatureinheit: Verweis auf `temperature_unit` in UserPreference (REQ-020 v1.2). |
| 1.4 | 2026-02-27 | M2M-Authentifizierung: API-Key-Modell (`kp_`-Prefix, SHA-256-Hash), `api_keys` Collection, `has_api_key` Edge, 3 Endpoints (erstellen/auflisten/revoken), Bearer-Erkennung neben JWT, Rate Limit 1000 req/min. |
| 1.3 | 2026-02-27 | „Angemeldet bleiben"-Option: Session-Cookie (Browser-Session) vs. persistentes Cookie (30 Tage) via `remember_me`-Flag. Neue User Story, Login-Checkbox, `is_persistent`-Feld auf RefreshToken, differenzierte Cookie-Strategie. |
| 1.2 | 2026-02-27 | SEC-K-002: IP-Anonymisierung nach 7 Tagen, `ip_anonymized_at` Feld. SEC-K-004: CSRF-Strategie — `SameSite=Lax` (statt Strict) + Double-Submit Cookie für zustandsändernde Cookie-Endpunkte. |
| 1.1 | 2026-02-25 | Tech-Stack-Review: Authlib statt python-jose, Token-TTL-Anpassungen |
| 1.0 | 2026-02-24 | Erstversion |

## 1. Business Case

**User Story (Lokale Registrierung):** "Als Einzelgärtner möchte ich mich mit E-Mail und Passwort registrieren können, ohne einen externen Anbieter wie Google nutzen zu müssen — weil ich meine Pflanzendaten privat halten möchte und keinen Social-Login verwenden will."

**User Story (SSO-Anmeldung):** "Als Hobby-Gärtner möchte ich mich mit meinem bestehenden Google-Konto anmelden können — damit ich kein weiteres Passwort verwalten muss und sofort loslegen kann."

**User Story (Account-Verknüpfung):** "Als Nutzer, der sich initial mit Google angemeldet hat, möchte ich nachträglich ein lokales Passwort setzen können — damit ich auch ohne Google-Verfügbarkeit auf meine Pflanzen zugreifen kann."

**User Story (Profilpflege):** "Als registrierter Nutzer möchte ich meinen Anzeigenamen, mein Profilbild und meine Sprach-/Zeitzoneneinstellungen verwalten können — damit andere Gartenmitglieder mich erkennen und das System in meiner Zeitzone arbeitet."

**User Story (Angemeldet bleiben):** "Als Gärtner möchte ich auf meinem privaten Gerät angemeldet bleiben können, damit ich nicht bei jedem Besuch erneut E-Mail und Passwort eingeben muss — auf öffentlichen Geräten möchte ich aber bewusst darauf verzichten können."

**User Story (Passwort-Reset):** "Als Nutzer, der sein Passwort vergessen hat, möchte ich über meine E-Mail-Adresse ein neues Passwort setzen können — ohne den Support kontaktieren zu müssen."

**User Story (OIDC-Anbindung):** "Als Systemadministrator möchte ich einen eigenen OpenID-Connect-Provider (z.B. Keycloak, Authentik) konfigurieren können — damit unser Gemeinschaftsgarten den zentralen Identity Provider der Organisation nutzen kann."

<!-- Quelle: Platform-Admin v1.6 -->
**User Story (Platform-Admin):** "Als Plattform-Betreiber möchte ich globale Stammdaten (Pflanzenarten, Sorten, Schädlinge) zentral pflegen und einzelnen Tenants zuweisen können — damit jeder Tenant nur die für ihn relevanten Daten sieht und die Datenqualität zentral sichergestellt wird."

**User Story (Doppelrolle):** "Als KA-Admin möchte ich gleichzeitig meinen eigenen privaten Garten als normaler Tenant-Nutzer verwalten können — ohne zwischen verschiedenen Accounts wechseln zu müssen."
<!-- /Quelle: Platform-Admin v1.6 -->

<!-- Quelle: Service Accounts v1.7 -->
**User Story (Home Assistant Integration):** "Als Hobby-Gärtner mit Home Assistant möchte ich einen Service Account für meine HA-Installation erstellen können — damit HA automatisch Sensordaten liefert und Aktoren steuert, ohne dass mein persönlicher Account dafür missbraucht wird."

**User Story (CI/CD Pipeline):** "Als Plattform-Betreiber möchte ich einen Service Account für meine CI/CD-Pipeline erstellen können — damit automatisierte Tests und Deployments API-Zugriff haben, ohne menschliche Credentials zu verwenden."

**User Story (Monitoring-System):** "Als Tenant-Admin möchte ich einen Service Account für Grafana/Prometheus erstellen können — damit das Monitoring-System Metriken abrufen kann, mit eigenen Rate-Limits und eingeschränktem Zugriff nur auf meinen Tenant."

**User Story (Service Account Verwaltung):** "Als Tenant-Admin möchte ich Service Accounts für meinen Garten erstellen, deren Berechtigungen steuern und sie bei Bedarf deaktivieren können — damit ich volle Kontrolle über maschinelle Zugriffe auf meine Daten habe."

**User Story (Platform Service Account):** "Als KA-Admin möchte ich Service Accounts auf Plattformebene erstellen können — damit zentrale Systeme (Backup, Monitoring, Enrichment-Pipelines) über einen dedizierten, auditierbaren Account auf globale Daten zugreifen."

**User Story (IP-Einschränkung):** "Als sicherheitsbewusster Admin möchte ich Service Accounts auf bestimmte IP-Bereiche einschränken können — damit ein kompromittierter API-Key nicht von beliebigen Netzwerken aus genutzt werden kann."
<!-- /Quelle: Service Accounts v1.7 -->

**Beschreibung:**
Kamerplanter ist aktuell ein Einbenutzer-System ohne Authentifizierung. Für Mehrbenutzerbetrieb (Gemeinschaftsgärten, Mikro-Farmen, Anbauvereinigungen) ist eine vollständige Benutzerverwaltung die **Grundvoraussetzung**. Diese REQ **ersetzt NFR-001 §6.1** (JWT-Skizze mit `python-jose`, 1h Access Token) durch eine vollständige Spezifikation und bildet die Basis für REQ-024 (Mandantenverwaltung).

**Technologie-Entscheidung (JWT/OAuth-Library):**
Diese Spezifikation verwendet **Authlib** (aktiv maintained) anstelle von `python-jose` (letztes Release 2022, in NFR-001 §6.1 referenziert). Authlib bietet:
- JWT-Signierung/-Validierung (ersetzt `python-jose`)
- OAuth2/OIDC Client mit PKCE-Support (ersetzt manuelle `httpx`-Implementierung)
- OIDC Discovery (`.well-known/openid-configuration`) built-in
- Flask/FastAPI-Integration

**Abweichungen von NFR-001 §6.1:**
| Aspekt | NFR-001 §6.1 (alt) | REQ-023 (neu) | Begründung |
|--------|--------------------|--------------|-----------|
| Library | `python-jose` + `passlib` | `authlib` + `passlib` | `python-jose` unmaintained seit 2022; Authlib bietet OIDC/PKCE built-in |
| Access Token TTL | 1 Stunde | **15 Minuten** | Kürzeres Fenster bei Token-Kompromittierung; Refresh-Token-Mechanismus kompensiert UX |
| Refresh Token | Nicht spezifiziert | 30 Tage (persistent) oder 24h (Session), HttpOnly Cookie, Rotation, steuerbar via „Angemeldet bleiben" | Erforderlich für 15-Min-Access-Tokens ohne ständige Neuanmeldung; Session-Cookie als sicherer Standard für geteilte Geräte |
| Token Payload | `sub`, `exp`, `type` | `sub`, `tenant_roles`, `is_platform_admin`, `exp`, `iat`, `type` (dazu `jti`, `gen`, `sid`, §3.2a) | PII-Minimierung (SEC-M-001): kein email/display_name. **`tenant_roles` und `is_platform_admin` sind informativ** (v1.46, #2121): `tenant_roles` wird heute leer ausgestellt, keine Autorisierung liest einen der beiden Claims — die Wächter lesen die Mitgliedschaften zur Laufzeit, sodass eine Rollenänderung sofort wirkt und kein Token eine entzogene Rolle weiterträgt |
| Refresh Grace Window <!-- W-004 --> | Nicht spezifiziert | **60 Sekunden** | Idempotenter Refresh innerhalb dieses Fensters (bei Device-Match) — toleriert paralleles `POST /auth/refresh` aus PWA-Reconnect (Service-Worker + UI-Thread). Nach 60s: strikte Replay-Detection mit Family-Sprengung. (UI-NFR-012 R-049) |
| Token Family <!-- W-004 --> | Nicht spezifiziert | **`family_key` pro Login**, geteilt durch alle aus Rotation entstandenen Nachfolger | Replay-Detection sprengt die ganze Family; jeder neue Login startet eine neue Family — Multi-Device-Nutzung bleibt unbeeinträchtigt |

**Kernkonzepte:**

**Dual-Authentifizierung — Lokal + Föderiert:**
Das System unterstützt zwei gleichberechtigte Authentifizierungspfade:
1. **Lokale Accounts** — E-Mail + Passwort (Bcrypt-gehasht), vollständig self-contained
2. **Föderierte Accounts** — OAuth2/OIDC mit benannten Providern (Google, GitHub, Apple) und beliebig vielen generischen OIDC-Providern

Ein User kann mehrere Auth-Methoden verknüpfen (z.B. Google + lokales Passwort). Die erste erfolgreiche Anmeldung erstellt den User-Account; weitere Provider werden verknüpft.

**Benannte SSO-Provider:**

| Provider | Protokoll | Scope | Besonderheit |
|----------|-----------|-------|-------------|
| Google | OAuth2 + OIDC | `openid email profile` | Größte Verbreitung, E-Mail immer verifiziert |
| GitHub | OAuth2 | `read:user user:email` | Technische Nutzer, E-Mail ggf. privat → separater API-Call |
| Apple | OAuth2 + OIDC | `name email` | Name nur beim ersten Login übermittelt, muss gespeichert werden |

**Generischer OIDC-Provider:**
Zusätzlich können beliebig viele OIDC-Provider über Konfiguration registriert werden (z.B. Keycloak, Authentik, Azure AD, Okta). Die Konfiguration erfolgt per Provider-Eintrag:

```yaml
# Konfigurationsbeispiel: Generischer OIDC-Provider
oidc_providers:
  - slug: "keycloak-gemeinschaftsgarten"
    display_name: "Gemeinschaftsgarten Berlin"
    issuer_url: "https://auth.garden-berlin.org/realms/garten"
    client_id: "kamerplanter"
    client_secret: "${KEYCLOAK_SECRET}"
    scopes: ["openid", "email", "profile"]
    icon_url: "https://auth.garden-berlin.org/logo.png"  # Optional
    auto_discover: true  # .well-known/openid-configuration
```

**JWT-Token-Lifecycle:**

| Token | Lebensdauer | Speicherort | Refresh-Mechanismus |
|-------|-------------|-------------|---------------------|
| Access Token | 15 Minuten | Memory (Frontend) | Automatisch via Refresh Token |
| Refresh Token (persistent) | 30 Tage | HttpOnly Secure Cookie (`Expires` gesetzt) | Rotation bei Nutzung (altes Token wird invalidiert) |
| Refresh Token (Session) | Browser-Session | HttpOnly Secure Session-Cookie (kein `Expires`/`Max-Age`) | Rotation bei Nutzung |

- **Access Token:** Enthält `sub` (user_key), `tenant_roles` (Mapping tenant_key → role; **informativ und heute leer** — Autorisierung liest die gespeicherte Mitgliedschaft, nie diesen Claim, v1.46), `exp`, `iat`, `type`. Kurzlebig, wird bei jedem API-Request als `Authorization: Bearer <token>` mitgesendet.
  - **PII-Minimierung (SEC-M-001):** `email` und `display_name` werden **nicht** im JWT-Payload übertragen, um die Exposition personenbezogener Daten bei Token-Leaks zu minimieren. Diese Daten werden bei Bedarf über `GET /api/v1/users/me` abgefragt (gecacht im Frontend-State).
- **Refresh Token:** Wird als HttpOnly/Secure/SameSite=Lax Cookie gespeichert. Bei Nutzung wird ein neues Refresh-Token-Paar ausgestellt und das alte invalidiert (Token-Rotation verhindert Token-Diebstahl).
- **Token-Revocation:** Logout invalidiert alle Refresh Tokens des Nutzers. Optional: "Von allen Geräten abmelden" invalidiert alle Sessions.

**„Angemeldet bleiben"-Strategie:**

Das Login-Formular bietet eine Checkbox „Angemeldet bleiben" (`remember_me`). Diese steuert die **Cookie-Persistenz** des Refresh Tokens:

| `remember_me` | Cookie-Typ | Verhalten | Serverseitige TTL |
|----------------|------------|-----------|-------------------|
| `true` (aktiviert) | **Persistentes Cookie** — `Max-Age: 30 Tage` | Cookie überlebt Browser-Neustart. Nutzer bleibt bis zu 30 Tage angemeldet (sliding window durch Token-Rotation). | 30 Tage |
| `false` (Standard) | **Session-Cookie** — kein `Expires`/`Max-Age` | Cookie wird gelöscht, wenn der Browser geschlossen wird. Nutzer muss sich nach Browser-Neustart erneut anmelden. | 24 Stunden |

- **Standard:** `remember_me = false` — sicherere Standardeinstellung, besonders relevant für öffentliche/geteilte Geräte
- **Session-TTL bei `remember_me=false`:** Das Refresh Token hat serverseitig eine verkürzte Lebensdauer von 24 Stunden (statt 30 Tage). Selbst wenn der Browser die Session wider Erwarten beibehält (z.B. Session-Restore-Feature), läuft das Token nach 24h ab.
- **SSO-Logins:** OAuth/OIDC-Logins setzen `remember_me` implizit auf `true`, da der Nutzer bereits einen bewussten Redirect-Flow durchlaufen hat. Der Nutzer kann dies über die Session-Verwaltung (`AccountSettingsPage → Sessions`) jederzeit widerrufen.
- **Token-Rotation:** Bei jedem Refresh wird der Cookie-Typ (persistent vs. Session) des ursprünglichen Tokens beibehalten. Ein Session-Token wird nicht durch Rotation zu einem persistenten Token.

**CSRF-Schutz-Strategie (SEC-K-004):**

Da Refresh Tokens als HttpOnly Cookie übertragen werden, sind zustandsändernde Endpunkte, die diesen Cookie verwenden, potenziell CSRF-anfällig. Die Strategie kombiniert zwei Maßnahmen:

1. **`SameSite=Lax`** (statt `Strict`): OAuth-Callbacks sind Top-Level-Navigationen (Redirect von Google/GitHub/Apple zurück zur App). `SameSite=Strict` würde den Refresh-Token-Cookie bei diesen Cross-Origin-Navigationen blockieren. `SameSite=Lax` erlaubt den Cookie bei Top-Level-Navigationen (GET), blockiert ihn aber bei Cross-Origin POST/PUT/DELETE (CSRF-Schutz für die meisten Szenarien).

2. **Double-Submit Cookie Pattern** für POST-Endpunkte, die den Refresh-Token-Cookie verwenden:
   - Bei Token-Refresh (`POST /auth/refresh`): Server setzt zusätzlich einen nicht-HttpOnly Cookie `csrf_token` mit einem zufälligen Wert. Client muss diesen Wert als `X-CSRF-Token`-Header mitsenden. Server vergleicht Cookie-Wert mit Header-Wert.
   - Betroffene Endpunkte: `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`
   - Der CSRF-Token wird bei jedem Token-Refresh erneuert (analog zur Refresh-Token-Rotation)
   - **Nicht** betroffen: `POST /auth/login`, `POST /auth/register` (verwenden keinen Cookie, sondern Request-Body-Credentials)
   - **Nur der Cookie-Pfad** von `POST /auth/refresh` ist Double-Submit-geschützt (#1118): Seit v1.12 akzeptiert dieser Endpunkt zusätzlich einen optionalen Refresh-Token im JSON-Body (§3.8). Ein Body-Token ist kein *ambient* übertragenes Credential — der Browser hängt ihn nicht selbsttätig an —, deshalb entfällt die Double-Submit-Prüfung auf dem Body-Pfad. Der Cookie-Pfad bleibt unverändert CSRF-pflichtig.

| Endpunkt | Cookie-basiert | CSRF-Schutz |
|----------|---------------|-------------|
| `POST /auth/login` | Nein (Body) | Nicht nötig |
| `POST /auth/register` | Nein (Body) | Nicht nötig |
| `POST /auth/refresh` (Cookie-Pfad) | Ja (Refresh Cookie) | Double-Submit Cookie |
| `POST /auth/refresh` (Body-Pfad, #1118) | Nein (Refresh-Token im Body) | Nicht nötig (kein ambient Credential) |
| `POST /auth/logout` | Ja (Refresh Cookie) | Double-Submit Cookie |
| `POST /auth/logout-all` | Ja (Refresh Cookie) | Double-Submit Cookie |
| `GET /auth/oauth/{slug}/callback` | Nein (OAuth State) | OAuth State-Parameter |
| Alle anderen Endpunkte | Nein (Bearer Token) | Nicht nötig (Token im Header) |

**Passwort-Policy:**
- Minimale Länge: 10 Zeichen
- Keine Komplexitätsregeln (NIST 800-63B Empfehlung: Länge > Komplexität)
- Bcrypt mit Cost Factor 12
- Breach-Check gegen HaveIBeenPwned API (SHA-1-Prefix, k-Anonymity, optional)
- Rate Limiting: Max. 5 fehlgeschlagene Login-Versuche pro 15 Minuten pro E-Mail

**E-Mail-Verifizierung:**
- Lokale Registrierung: Verifizierungs-Link per E-Mail (Token gültig 24h)
- SSO-Registrierung: E-Mail automatisch als verifiziert markiert (Provider garantiert Verifizierung)
- Unbestätigte Accounts können das System nutzen, aber keine Einladungen (REQ-024) versenden

**Account-Linking:**
Ein User kann mehrere Auth-Provider verknüpfen:
- Matching erfolgt über **verifizierte E-Mail-Adresse**: Login mit Google (`max@example.com`) wird automatisch mit dem lokalen Account (`max@example.com`) verknüpft
- Kein Auto-Link bei unverifizierter E-Mail (verhindert Account-Übernahme). Die Seite des bestehenden Kontos ist der Bestätigungsnachweis (`email_confirmed_at`, `User.address_proven`), nicht `email_verified` allein: bei `REQUIRE_EMAIL_VERIFICATION=false` setzt die Registrierung das Flag ohne Bestätigung. Ein Konto ohne Nachweis (auch die Seed-Konten) wird nicht verknüpft; der Inhaber bestätigt die Adresse über den Link (§3.2b) und meldet sich danach über den Anbieter an.
- User kann verknüpfte Provider jederzeit entfernen (mindestens eine Auth-Methode muss bestehen bleiben)
- **Kein manuelles Verknüpfen:** ein zusätzlicher Provider entsteht nur über den Auto-Link beim Login mit ihm. Der dafür gedachte Endpunkt `POST /users/me/providers/{provider_slug}/link` existierte, hatte aber nie einen Aufrufer im Frontend und wurde mit #1416 entfernt (Betreiberentscheidung 2026-09-17). Wer den Auto-Link nicht erhält — etwa weil der Anbieter keinen `email_verified`-Anspruch liefert — meldet sich mit E-Mail und Passwort an; die beiden Konten bleiben getrennt.

### 1.1 Szenarien

**Szenario 1: Lokale Registrierung — Einzelgärtner**
```
1. Nutzer öffnet /register
2. Gibt ein: E-Mail "max@example.com", Anzeigename "Max", Passwort "mein-sicheres-passwort-2024"
3. System erstellt User-Account (status: unverified)
4. Verifizierungs-E-Mail wird gesendet (Token: 24h gültig)
5. Nutzer klickt Verifizierungs-Link → status: active
6. Nutzer wird eingeloggt (Access Token + Refresh Token)
7. System erstellt automatisch einen persönlichen Tenant "Maxs Garten"
```

**Szenario 2: Google-SSO — Schnelleinstieg**
```
1. Nutzer klickt "Mit Google anmelden"
2. Redirect zu Google OAuth2 Consent Screen
3. Google gibt zurück: email="lisa@gmail.com", name="Lisa Müller", picture_url="..."
4. System prüft: Existiert User mit email="lisa@gmail.com"?
   → Nein: Neuer User wird erstellt (status: active, email_verified: true)
   → Ja: Bestehender User wird eingeloggt, Google-Provider wird verknüpft
5. JWT-Token-Paar wird ausgestellt
6. Redirect zu Dashboard
```

**Szenario 3: Generischer OIDC — Gemeinschaftsgarten mit Keycloak**
```
1. Admin hat OIDC-Provider "keycloak-gemeinschaftsgarten" konfiguriert
2. Nutzer öffnet /login → sieht Button "Gemeinschaftsgarten Berlin"
3. Redirect zu Keycloak-Login-Seite der Organisation
4. Nach Authentifizierung: OIDC-Token mit sub/email/name
5. System erstellt/verknüpft User-Account
6. Nutzer wird in den zugehörigen Tenant eingeladen (falls konfiguriert)
```

**Szenario 4: Account-Linking — Google-User setzt lokales Passwort**
```
1. Nutzer hat sich initial mit Google angemeldet
2. Navigiert zu /settings/account
3. Wählt "Lokales Passwort hinzufügen"
4. Setzt Passwort → system speichert Bcrypt-Hash
5. Nutzer kann sich jetzt wahlweise mit Google ODER E-Mail/Passwort anmelden
```

**Szenario 5: Angemeldet bleiben — Privates Gerät**
```
1. Nutzer öffnet /login
2. Gibt E-Mail und Passwort ein
3. Aktiviert Checkbox "Angemeldet bleiben"
4. POST /auth/login mit { email, password, remember_me: true }
5. Server erstellt RefreshToken (is_persistent: true, expires_at: +30 Tage)
6. Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000
7. Nutzer schließt Browser und öffnet die App am nächsten Tag
8. Browser sendet persistenten Cookie → automatischer Token-Refresh → Nutzer ist eingeloggt
```

**Szenario 6: Ohne "Angemeldet bleiben" — Öffentliches Gerät**
```
1. Nutzer öffnet /login auf einem geteilten Gerät
2. Gibt E-Mail und Passwort ein, lässt Checkbox "Angemeldet bleiben" deaktiviert
3. POST /auth/login mit { email, password, remember_me: false }
4. Server erstellt RefreshToken (is_persistent: false, expires_at: +24 Stunden)
5. Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax  (KEIN Max-Age/Expires)
6. Nutzer arbeitet normal — Token-Refresh funktioniert transparent
7. Nutzer schließt Browser → Session-Cookie wird gelöscht
8. Nutzer öffnet Browser erneut → kein Cookie → Redirect zu /login
```

**Szenario 7: Passwort-Reset**
```
1. Nutzer klickt "Passwort vergessen" auf /login
2. Gibt E-Mail ein → System sendet Reset-Link (Token: 1h gültig, einmalig verwendbar)
3. Nutzer klickt Link → Setzt neues Passwort
4. Alle bestehenden Refresh Tokens werden invalidiert (erzwingt Neuanmeldung auf allen Geräten)
```

## 2. ArangoDB-Modellierung

### Nodes:

- **`:User`** — Benutzerkonto (menschliche User und Service Accounts)
  - Collection: `users`
  - Properties:
    - `email: str` (UNIQUE, lowercase-normalisiert)
    - `display_name: str` (Anzeigename, z.B. "Max Mustermann")
    - `avatar_url: Optional[str]` (Profilbild-URL, von SSO übernommen oder manuell gesetzt)
    - `locale: str` (Default: `de`, Sprachpräferenz für i18n)
    - `timezone: str` (Default: `Europe/Berlin`, IANA-Zeitzone)
    <!-- Quelle: Service Accounts v1.7 -->
    - `account_type: Literal['human', 'service']` (Default: `human`) — Unterscheidet menschliche Nutzer von Service Accounts. Service Accounts können sich nicht interaktiv anmelden (kein Passwort, kein SSO), werden ausschließlich per API-Key authentifiziert.
    <!-- /Quelle: Service Accounts v1.7 -->
    - `status: Literal['unverified', 'active', 'suspended', 'deleted']`
    - `email_verified: bool` (Default: `false`)
    - `email_verification_token_hash: Optional[str]` (SHA-256-Hex des einmaligen Tokens; der Klartext steht nur in der Mail, #2158)
    - `email_verification_expires: Optional[datetime]`
    - `password_hash: Optional[str]` (Bcrypt, `null` bei reinen SSO-Accounts und Service Accounts)
    - `password_reset_token_hash: Optional[str]` (SHA-256-Hex des einmaligen Tokens; der Klartext steht nur in der Mail, #2158)
    - `password_reset_expires: Optional[datetime]`
    - `session_generation: int` (Default: 0) — steigt bei jedem Ereignis, das **alle** Sitzungen beendet; ein Refresh-Token einer älteren Generation wird abgelehnt (#2116)
    - `access_token_generation: int` (Default: 0) — steigt bei **jedem** Widerruf; ein Access Token mit anderem `gen` wird abgelehnt (#2116). Beide Zähler schreibt nur das Refresh-Token-Repository.
    - `failed_login_attempts: int` (Default: 0, Reset nach erfolgreichem Login)
    - `locked_until: Optional[datetime]` (Temporäre Sperrung nach zu vielen Fehlversuchen)
    - `last_login_at: Optional[datetime]`
    - `ha_url: Optional[str]` (Home Assistant URL, z.B. `"http://homeassistant.local:8123"`)
    - `ha_token_encrypted: Optional[str]` (Home Assistant Long-Lived Access Token, AES-256 verschlüsselt gespeichert. Wird vom `HomeAssistantConnector` (REQ-005) zur Kommunikation mit der HA REST API verwendet.)
    <!-- Quelle: Service Accounts v1.7 -->
    - `description: Optional[str]` (Nur für Service Accounts — Zweck/Beschreibung, z.B. "Home Assistant Zelt 1", "Grafana Monitoring")
    - `created_by: Optional[str]` (user_key des Erstellers, nur für Service Accounts)
    - `rate_limit_rpm: Optional[int]` (Rate Limit pro Minute, nur für Service Accounts. Default: `1000`. `null` = globaler Default.)
    - `allowed_ip_ranges: Optional[list[str]]` (CIDR-Notation, nur für Service Accounts. `null` = keine Einschränkung. z.B. `["192.168.1.0/24", "10.0.0.0/8"]`)
    - `last_active_at: Optional[datetime]` (Letzte API-Aktivität, nur für Service Accounts — wird bei jedem API-Key-Zugriff aktualisiert)
    <!-- /Quelle: Service Accounts v1.7 -->
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:AuthProvider`** — Verknüpfter Authentifizierungsprovider
  - Collection: `auth_providers`
  - Properties:
    - `provider: str` (z.B. `google`, `github`, `apple`, `keycloak-gemeinschaftsgarten`)
    - `provider_user_id: str` (ID beim Provider, z.B. `sub` — nur je Aussteller eindeutig)
    - `oidc_config_slug: Optional[str]` (Konfiguration, über die die Verknüpfung entstand; `null` nur bei mehrdeutigen Verknüpfungen von vor #1815, die zu keiner Anmeldung passen — siehe v1.21)
    - `issuer: Optional[str]` (`iss` des ID-Tokens; bei der Verknüpfung oder der ersten Anmeldung danach gesetzt; `null` ohne ID-Token, z.B. GitHub)
    - `provider_email: Optional[str]` (E-Mail beim Provider, kann von User.email abweichen)
    - `provider_name: Optional[str]` (Name beim Provider)
    - `provider_avatar_url: Optional[str]`
    - `access_token_encrypted: Optional[str]` (Verschlüsselt, für API-Zugriff beim Provider)
    - `refresh_token_encrypted: Optional[str]` (Verschlüsselt, für Token-Refresh beim Provider)
    - `token_expires_at: Optional[datetime]`
    - `linked_at: datetime`
    - `last_used_at: Optional[datetime]`

- **`:RefreshToken`** — Aktive Refresh-Token-Sessions
  - Collection: `refresh_tokens`
  - Properties:
    - `token_hash: str` (SHA-256 Hash des Tokens, UNIQUE)
    - `device_info: Optional[str]` (User-Agent, für "Aktive Sessions"-Übersicht)
    - `ip_address: Optional[str]` (Letzte bekannte IP; **Rechtsgrundlage:** Art. 6(1)(f) berechtigtes Interesse — Erkennung kompromittierter Sessions)
    - `ip_anonymized_at: Optional[datetime]` (Zeitpunkt der IP-Anonymisierung; `null` = noch nicht anonymisiert)
    - `issued_at: datetime`
    - `expires_at: datetime`
    - `is_persistent: bool` (Default: `false` — `true` wenn Login mit „Angemeldet bleiben", steuert Cookie-Typ bei Rotation)
    - `revoked: bool` (Default: `false`)
    - `replaced_by: Optional[str]` (Token-Hash des Nachfolgers bei Rotation)
    <!-- Quelle: Widerspruchsanalyse W-004 -->
    - `family_key: str` (UUID; alle aus Rotation desselben Logins entstehenden Tokens teilen die `family_key`. Bei nachgewiesenem Replay wird die ganze Family invalidiert. Jeder neue Login startet eine neue Family — Multi-Device-Nutzung bleibt unbeeinträchtigt.)
    - `device_id: Optional[str]` (Stable Device-Identifier vom Frontend, persistiert in IndexedDB als UUID — siehe UI-NFR-012 R-049b. Default `null` für migrierte Tokens und API-Clients ohne PWA-Setup. Bei `null` greift der Grace-Window-Schutz nicht.)
    - `rotated_at: Optional[datetime]` (Wann wurde dieses Token durch Rotation invalidiert; `null` = noch aktiv. Wird beim Refresh auf den Vorgänger gesetzt.)
    - `successor_key: Optional[str]` (Token-Hash des direkten Nachfolgers nach Rotation; nur für Grace-Window-Lookup. Identisch zu `replaced_by` für Tokens nach v1.9; bei Migration werden ältere Tokens mit eigenem Hash gefüllt.) **Umgesetzt (#2116):** Dokumentschlüssel des Nachfolgers, nicht dessen Hash; keine Migration — ein Token ohne `family_key` übernimmt bei seiner ersten Rotation den eigenen Schlüssel als Family.
    - `session_generation: int` (Default: 0, #2116) — `users.session_generation` beim Login, an Nachfolger vererbt
    <!-- /Quelle: Widerspruchsanalyse W-004 -->
  - **IP-Anonymisierung (SEC-K-002):** Nach 7 Tagen wird `ip_address` automatisch anonymisiert (Celery-Task, NFR-011 R-03):
    - IPv4: Letztes Oktett → `0` (z.B. `192.168.1.42` → `192.168.1.0`)
    - IPv6: Auf `/48`-Präfix gekürzt (z.B. `2001:db8:85a3::8a2e:370:7334` → `2001:db8:85a3::`)
    - `ip_anonymized_at` wird auf den Anonymisierungszeitpunkt gesetzt

- **`:OidcProviderConfig`** — Konfigurierte OIDC-Provider (System-Level)
  - Collection: `oidc_provider_configs`
  - Properties:
    - `slug: str` (URL-sicher, UNIQUE, z.B. `keycloak-gemeinschaftsgarten`)
    - `display_name: str` (Anzeigename auf Login-Seite)
    - `provider_type: Literal['google', 'github', 'apple', 'oidc']`
    - `issuer_url: Optional[str]` (OIDC Discovery URL, für generische Provider)
    - `authorization_url: str`
    - `token_url: str`
    - `userinfo_url: Optional[str]`
    - `jwks_url: Optional[str]` (JSON Web Key Set für Token-Validierung)
    - `client_id: str`
    - `client_secret_encrypted: str` (Verschlüsselt gespeichert)
    - `scopes: list[str]` (Default: `['openid', 'email', 'profile']`)
    - `icon_url: Optional[str]` (Für Login-Button)
    - `enabled: bool` (Default: `true`)
    - `auto_discover: bool` (Default: `true`, nutzt `.well-known/openid-configuration`)
    - `default_tenant_key: Optional[str]` (Forward-Referenz → REQ-024: Neuen Usern automatisch diesem Tenant zuweisen. Wird erst mit REQ-024 aktiv.)
    - `created_at: datetime`
    - `updated_at: datetime`

### Edges:

```
has_auth_provider:  users → auth_providers     (1:N, User hat Auth-Provider)
has_session:        users → refresh_tokens      (1:N, User hat aktive Sessions)
```

### Indizes:

```
users:
  - PERSISTENT INDEX on [email] UNIQUE
  - PERSISTENT INDEX on [status]

auth_providers:
  - PERSISTENT INDEX on [provider, oidc_config_slug, provider_user_id] UNIQUE  (eindeutig je Konfiguration — `sub` ist nur je Aussteller eindeutig, #1869)

refresh_tokens:
  - PERSISTENT INDEX on [token_hash] UNIQUE
  - PERSISTENT INDEX on [expires_at]  (für TTL-Cleanup)
  - TTL INDEX on [expires_at] expireAfter: 0  (automatische Bereinigung abgelaufener Tokens)

oidc_provider_configs:
  - PERSISTENT INDEX on [slug] UNIQUE
  - PERSISTENT INDEX on [provider_type]
```

### AQL-Beispiellogik:

**User mit allen Auth-Providern laden:**
```aql
LET user = DOCUMENT(users, @user_key)
LET providers = (
  FOR ap IN 1..1 OUTBOUND user GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_auth_provider'] }
    RETURN {
      provider: ap.provider,
      provider_email: ap.provider_email,
      linked_at: ap.linked_at,
      last_used_at: ap.last_used_at
    }
)
RETURN MERGE(user, { auth_providers: providers })
```

**User per Provider-ID finden (SSO-Login):** liefert die **Kandidaten** eines (Typ, `sub`)-Paars; der Login wählt daraus die Verknüpfung der Konfiguration, über die angemeldet wurde (v1.21, #1869) — nie die erste beliebige.
```aql
FOR ap IN auth_providers
  FILTER ap.provider == @provider AND ap.provider_user_id == @provider_user_id
  LET user = FIRST(
    FOR u IN 1..1 INBOUND ap GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['has_auth_provider'] }
      RETURN u
  )
  RETURN { auth_provider: ap, user: user }
```

**Aktive Sessions eines Users:**
```aql
FOR rt IN 1..1 OUTBOUND DOCUMENT(users, @user_key) GRAPH 'kamerplanter_graph'
  OPTIONS { edgeCollections: ['has_session'] }
  FILTER rt.revoked == false AND rt.expires_at > DATE_ISO8601(DATE_NOW())
  SORT rt.issued_at DESC
  RETURN {
    device_info: rt.device_info,
    ip_address: rt.ip_address,
    issued_at: rt.issued_at,
    expires_at: rt.expires_at
  }
```

**Abgelaufene/Revoked Tokens bereinigen (Celery-Task):**
```aql
FOR rt IN refresh_tokens
  FILTER rt.revoked == true OR rt.expires_at < DATE_ISO8601(DATE_NOW())
  REMOVE rt IN refresh_tokens
```

## 3. Backend-Architektur

### 3.1 Engine-Schicht

**`PasswordEngine`** — Passwort-Hashing und -Validierung (pure Logik, kein I/O):

```python
class PasswordEngine:
    BCRYPT_ROUNDS = 12
    MIN_LENGTH = 10

    def hash_password(self, password: str) -> str: ...
    def verify_password(self, password: str, password_hash: str) -> bool: ...
    def validate_password_policy(self, password: str) -> list[str]: ...
        # Gibt Liste von Fehlermeldungen zurück, leer = gültig
        # Prüft: Mindestlänge, nicht identisch mit E-Mail
```

**`TokenEngine`** — JWT-Erstellung und -Validierung (pure Logik, nutzt `authlib.jose`):

```python
# Implementierung nutzt authlib.jose.jwt (nicht python-jose)
# pip install authlib

class TokenEngine:
    def create_access_token(self, user: User, tenant_roles: dict[str, str]) -> str: ...
        # Payload: { sub: user_key, tenant_roles, is_platform_admin, exp, iat, type: "access" }
        # PII-Minimierung (SEC-M-001): KEIN email/display_name im Payload
        # Algorithmus: HS256 (via authlib.jose.jwt.encode), Lebensdauer: 15 Minuten
        # Migration zu RS256/ES256 (SEC-M-002): Langfristig geplant — ermöglicht Token-Validierung
        # ohne Shared Secret. Voraussetzung: JWK-Rotation-Infrastruktur. Kurzfristig:
        # JWT-Secret MUSS >= 256 Bit sein, Secret-Rotation über ENV-Variable mit Overlap-Periode.

    def create_refresh_token(self) -> tuple[str, str]: ...
        # Gibt (raw_token, token_hash) zurück
        # raw_token = secrets.token_urlsafe(32), token_hash = SHA-256(raw_token)
        # raw_token wird an Client gesendet, token_hash wird gespeichert

    def decode_access_token(self, token: str) -> TokenPayload: ...
        # Validiert Signatur, Ablaufdatum, Typ (via authlib.jose.jwt.decode)
        # Wirft InvalidTokenError bei Fehler

    def hash_token(self, raw_token: str) -> str: ...
        # SHA-256 Hash für DB-Speicherung (hashlib.sha256)
```

**`OAuthEngine`** — OAuth2/OIDC-Flow-Logik (nutzt `authlib.integrations.httpx_client`):

Authlib stellt `AsyncOAuth2Client` bereit, der PKCE, OIDC Discovery und Token-Exchange kapselt. Der `OAuthEngine` nutzt diesen Client intern und normalisiert die Provider-spezifischen Unterschiede:

```python
# Implementierung nutzt authlib.integrations.httpx_client.AsyncOAuth2Client
# PKCE (S256) wird automatisch von Authlib gehandhabt

class OAuthEngine:
    def create_oauth_client(self, provider_config: OidcProviderConfig) -> AsyncOAuth2Client: ...
        # Erstellt konfigurierten Authlib-Client mit PKCE-Support
        # Bei auto_discover=True: nutzt Authlib's OIDC Discovery automatisch

    def build_authorization_url(self, client: AsyncOAuth2Client, state: str, nonce: str) -> str: ...
        # Delegiert an client.create_authorization_url() (PKCE code_verifier wird automatisch generiert)

    def exchange_code_for_token(self, client: AsyncOAuth2Client, code: str, code_verifier: str) -> dict: ...
        # Delegiert an client.fetch_token() — gibt id_token + access_token zurück

    def validate_state(self, state: str, expected_state: str) -> bool: ...
        # CSRF-Schutz: Vergleicht state-Parameter

    def extract_user_info(self, provider_type: str, id_token: dict, userinfo: dict) -> OAuthUserInfo: ...
        # Normalisiert Provider-spezifische Claims zu einheitlichem Format
        # Google: sub, email, name, picture
        # GitHub: id, email (separater API-Call), login, avatar_url
        # Apple: sub, email, name (nur beim ersten Login — muss gespeichert werden!)
        # OIDC: sub, email, preferred_username, name, picture

    def should_auto_link(
        self, existing_email_verified: bool, oauth_email_verified: bool | None
    ) -> bool: ...
        # True nur wenn BEIDE Seiten bestätigt sind (#1403).
        #
        # Der zweite Parameter ist der `email_verified`-Anspruch des Anbieters und
        # hat DREI Zustände: True, False und None — None heißt, der Anbieter hat
        # nichts gesagt. Der Anspruch ist in OIDC optional, und viele Anbieter
        # lassen ihn weg; GitHub führt ihn gar nicht auf `/user`, sondern pro
        # Adresse auf `/user/emails` (dafür ist der Scope `user:email` nötig).
        #
        # **None lehnt ab.** Schweigen als Bestätigung zu werten reproduziert
        # genau die Lücke, gegen die der Anspruch existiert: ein falsch
        # konfigurierter oder kompromittierter Anbieter behauptet
        # `email = opfer@example.org` und übernimmt das Konto, sofern das lokale
        # Konto bestätigt ist — was jedes regulär registrierte ist. Der Aufrufer
        # landet stattdessen auf „mit Passwort anmelden". Ein anschließendes
        # manuelles Verknüpfen gibt es nicht (#1416); der Anbieter wird erst
        # verknüpft, wenn er den Anspruch liefert.
        #
        # Bis #1403 reichte der Aufrufort ein literales `True` für den zweiten
        # Parameter, der Anspruch wurde also nie gelesen. Dieselbe Annahme stand
        # im Neuanlage-Pfad: ein über OAuth erzeugtes Konto galt unbesehen als
        # bestätigt und erfüllte damit die erste Bedingung für jeden späteren
        # Anbieter.
```

**`LoginThrottleEngine`** — Brute-Force-Schutz (pure Logik):

```python
class LoginThrottleEngine:
    MAX_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    def check_allowed(self, failed_attempts: int, locked_until: Optional[datetime]) -> bool: ...
    def calculate_lockout(self, failed_attempts: int) -> Optional[datetime]: ...
        # Exponentielle Verzögerung: 15min, 30min, 1h, 2h, 4h
```

### 3.2 Service-Schicht

**`AuthService`** — Orchestriert Authentifizierungsflows:

```python
class AuthService:
    def __init__(self, user_repo, auth_provider_repo, refresh_token_repo,
                 oidc_config_repo, password_engine, token_engine,
                 oauth_engine, login_throttle_engine, email_service): ...

    # --- Lokale Authentifizierung ---
    async def register_local(self, email: str, password: str, display_name: str,
                             *, on_existing_address: Callable[[UserKey], None] | None = None) -> User: ...
        # 1. Validiert Passwort-Policy (PasswordEngine)
        # 2. Prüft E-Mail-Eindeutigkeit
        # 3. Erstellt User (status: unverified)
        # 4. Sendet Verifizierungs-E-Mail
        # 5. Erstellt persönlichen Default-Tenant (REQ-024)
        # SEC-H-009 (Account-Enumeration-Schutz): Bei bereits existierender E-Mail wird
        # die gleiche generische Antwort zurückgegeben ("Verifizierungs-E-Mail gesendet").
        # An die existierende Adresse wird stattdessen eine Info-Mail gesendet:
        # "Jemand hat versucht, ein Konto mit deiner E-Mail zu erstellen."
        # Der Service verschickt sie NICHT selbst — er reicht nur den Key des
        # existierenden Kontos an `on_existing_address` weiter (Details: §3.2a).

    async def login_local(self, email: str, password: str, remember_me: bool = False) -> TokenPair: ...
        # 1. Prüft Throttle (LoginThrottleEngine)
        # 2. Findet User per E-Mail
        # 3. Verifiziert Passwort (PasswordEngine)
        # 4. Erstellt Token-Paar (TokenEngine), TTL abhängig von remember_me:
        #    - remember_me=True:  Refresh Token 30 Tage, persistentes Cookie
        #    - remember_me=False: Refresh Token 24 Stunden, Session-Cookie
        # 5. Speichert RefreshToken mit is_persistent=remember_me
        # 6. Aktualisiert last_login_at

    async def verify_email(self, token: str) -> User: ...
    async def request_password_reset(self, email: str) -> None: ...
        # Sendet Reset-E-Mail, KEIN Fehler wenn E-Mail nicht existiert (Enumeration-Schutz)
        # Versand nach der Antwort; ein Versandfehler wird nur geloggt, nie beantwortet (#1890)
    async def reset_password(self, token: str, new_password: str) -> None: ...
        # Invalidiert alle Refresh Tokens nach Reset

    # --- Föderierte Authentifizierung ---
    async def initiate_oauth(self, provider_slug: str) -> OAuthRedirect: ...
        # 1. Lädt OidcProviderConfig
        # 2. Generiert state + nonce (CSRF-Schutz)
        # 3. Speichert state in Redis (5 Min TTL)
        # 4. Gibt Authorization URL zurück

    async def complete_oauth(self, provider_slug: str, code: str, state: str) -> TokenPair: ...
        # 1. Validiert state (OAuthEngine)
        # 2. Tauscht code gegen Token beim Provider
        # 3. Extrahiert User-Info (OAuthEngine)
        # 4. Findet/erstellt User + AuthProvider
        # 5. Auto-Link falls gleiche verifizierte E-Mail (OAuthEngine)
        # 6. Erstellt JWT-Token-Paar

    # --- Token-Management ---
    async def refresh_tokens(
        self,
        refresh_token: str,
        *,
        device_id: Optional[str] = None,                      # W-004
    ) -> TokenPair: ...
        # Token-Rotation mit Offline-Grace-Window (W-004, UI-NFR-012 R-049):
        #
        # Standard-Pfad (Token noch nicht rotiert):
        #   1. Token validieren (Signatur, Ablauf, revoked-Flag)
        #   2. Neues Token-Paar generieren, family_key vom Vorgänger erben
        #   3. Vorgänger markieren: rotated_at=now, successor_key=neues_hash
        #   4. Neues Token zurückgeben
        #
        # Grace-Window-Pfad (Token bereits rotiert, innerhalb 60s):
        #   - Wenn rotated_at != null UND
        #     (now - rotated_at) <= REFRESH_GRACE_WINDOW_SECONDS UND
        #     stored.device_id == request.device_id (beide nicht null):
        #     → Bereits ausgestellten Nachfolger zurückgeben (idempotent),
        #       KEIN neues Token erzeugen, KEINE Family-Sprengung.
        #
        # Replay-Pfad (Token rotiert, außerhalb Grace-Window oder Device-Mismatch):
        #   - Logge security_event: auth.refresh_replay_detected mit reason
        #     ('grace_expired' | 'device_mismatch' | 'no_device_id')
        #   - Inkrementiere kp_auth_refresh_replay_total{reason=...}
        #   - Invalidiere ALLE Tokens mit gleicher family_key (Family-Sprengung)
        #   - Werfe HTTPException 401 mit error_code='refresh_replay_detected'
        # is_persistent wird vom alten Token übernommen (Session bleibt Session, persistent bleibt persistent)

    async def logout(self, refresh_token: str) -> None: ...
        # Invalidiert das aktuelle Refresh Token

    async def logout_all_devices(self, user_key: str) -> int: ...
        # Invalidiert ALLE Refresh Tokens des Users, gibt Anzahl zurück

    # --- Account-Linking ---
    # Es gibt KEIN manuelles `link_provider`: verknüpft wird ausschließlich
    # automatisch beim OAuth-Login (`complete_oauth` -> `should_auto_link`).
    # Die frühere Methode und ihre Route hatten nie einen Aufrufer und wurden
    # mit #1416 entfernt (Betreiberentscheidung 2026-09-17).
    async def unlink_provider(self, user_key: str, provider_key: str) -> None: ...
        # Fehler wenn es die letzte Auth-Methode wäre

    async def add_local_password(self, user_key: str, password: str) -> None: ...
        # Für SSO-Only-User die ein lokales Passwort setzen wollen

    # --- M2M API-Key-Management ---
    async def create_api_key(self, user_key: str, label: str) -> ApiKeyCreated: ...
        # Generiert kryptografisch sicheren Key (kp_ + 48 Hex-Zeichen)
        # Speichert SHA-256-Hash in DB, gibt Klartext einmalig zurück
    async def list_api_keys(self, user_key: str) -> list[ApiKeySummary]: ...
        # Gibt alle aktiven Keys des Users zurück (ohne Hash, mit Prefix-Preview)
    async def revoke_api_key(self, user_key: str, key_id: str) -> None: ...
        # Setzt revoked_at, Key ist sofort ungültig
```

<!-- Quelle: Issue #942 / PR #957 / Issue #958 -->
#### SEC-H-009 — Info-Mail an die bereits registrierte Adresse

Die Info-Mail aus dem Kommentar oben ist **gebaut** (v1.11). Sie steht und fällt
mit zwei Bedingungen. Beide sind hier festgehalten, damit die nächste Person sie
nicht neu herleiten muss — und damit niemand die Mail „vereinfacht" und dabei
genau das Orakel wieder öffnet, das SEC-H-009 schließen soll.

**Bedingung 1 — asynchrone Zustellung, nach der Antwort.**
Eine *echte* Registrierung verschickt **innerhalb der Anfrage keine Mail**: mit
`require_email_verification=false` gar keine, mit `true` (Default seit #1948,
v1.28) geht die Bestätigungsmail erst nach der Antwort raus (#1890). Ein synchroner SMTP-Roundtrip nur im
Duplikat-Zweig macht diesen Zweig damit messbar **langsamer** als eine echte
Registrierung — dieselbe Auskunft, nur über die Uhr statt über den Body. Schlimmer
noch: `SmtpEmailAdapter._send` wirft weiter, ein Zustellfehler würde aus dem
Duplikat-Zweig eine **500** machen, während die echte Registrierung 201 antwortet.
Das wäre ein *stärkeres* Orakel als das ursprüngliche.

Deshalb:

* `AuthService.register_local` verschickt nichts. Es ruft nur den Callback
  `on_existing_address(user_key)` auf — vertraglich nicht-blockierend.
* Der Router (`POST /auth/register`) hängt daran einen **FastAPI-Background-Task**.
  Starlette sendet erst die Response und ruft danach `response.background` auf;
  weder der Import noch das Einreihen noch ein hängender Broker liegen im
  Zeitfenster, das ein Aufrufer mit Stoppuhr misst.
* Der Background-Task reiht den Celery-Task
  `app.tasks.auth_tasks.send_duplicate_registration_notice` ein und schluckt eine
  Broker-Störung (geloggt, nicht geworfen). Kein Retry, kein Outbox — die Mail ist
  rein informativ.
* Nutzlast ist der **Konto-Key**, nicht die Adresse: die Adresse gehört einem
  Dritten und läge sonst im Klartext in der Broker-Queue (NFR-011).

Gemessen (Median über 25 bzw. 15 Durchläufe je Zweig, gleiche Maschine, gleiche
Bedingungen wie in #957): Verhältnis echt/duplikat **1.000× vorher → 0.999×
nachher** auf Service-Ebene und **1.001× → 1.001× (Broker ok), 1.002× (Broker
tot), 0.999× (Broker hängt 5 s)** über HTTP. Der hängende Broker ist der
eigentliche Beweis: er kostet den Duplikat-Zweig nichts, weil er hinter der
Antwort liegt.

**Bedingung 2 — Sperrfenster je Empfängeradresse, nicht je Absender-IP.**
`/auth/register` ist anonym: der Angreifer wählt Empfänger *und* Auslöser. Ohne
Schranke pro Empfänger ist die Mail ein unauthentifiziertes Mail-Bombing-Primitiv
auf Kosten der Absender-Reputation dieser Installation. Eine Sperre gegen die
*Quelle* hilft nicht — sie legt Passwort-Reset und E-Mail-Verifikation für alle
mit lahm.

* `IRegistrationNoticeStore.claim(email)` gewährt pro Adresse **einen** Versand
  pro Fenster (24 h). Der Anspruch wird atomar erhoben (`SET … NX EX`), sonst
  senden zwei gleichzeitige Versuche beide.
* Zwei Stufen, analog `IUnknownAccountStore`: Valkey (geteilt über Worker) mit
  Rückfall auf eine beschränkte In-Process-Map. Bei Redis-Störung wird **nicht**
  fail-open entschieden — das wäre genau der unbeschränkte Versand.
* Schlüssel ist der SHA-256 der normalisierten Adresse; die Adresse selbst wird
  nirgends im Klartext abgelegt oder geloggt (NFR-011).
* Der Anspruch wird **vor** dem Versand erhoben. Ein Zustellfehler verbrennt damit
  das Fenster — bewusst: die Schranke existiert gegen den anonymen Auslöser, und
  ein SMTP-Ausfall darf sie nicht aufheben.

**Inhalt der Mail** (DE kanonisch, EN als Spiegel;
`RegistrationNoticeEngine`, Auswahl über `user.locale`, Fallback `de`):
Sie nennt genau den Vorgang, stellt fest, dass **nichts** passiert ist, und
verlinkt Anmeldung und Passwort-Reset (aus `frontend_url`, nie aus Request-Daten).
Sie enthält **nicht**: den vom Aufrufer gewählten Anzeigenamen (sonst wird die
Mail zum Nachrichtenkanal in fremde Postfächer), das eingegebene Passwort, die
IP, irgendein Feld des betroffenen Kontos und keinerlei Token oder Ein-Klick-Aktion.
Sie geht nicht an deaktivierte oder gelöschte Konten.

<!-- Quelle: Widerspruchsanalyse W-004 -->
### 3.2a Refresh-Token Family + Offline-Grace-Window (W-004)

Diese Sektion spezifiziert die in §3.2 angedeutete Grace-Window-Logik im Detail. Hintergrund: PWA-Reconnect-Race nach Offline-Phase (UI-NFR-012 R-049).

#### Konzept Token-Family

Jeder erfolgreiche Login (Local oder OAuth) erzeugt ein **frisches Refresh-Token mit neuer `family_key` (UUID4)**. Bei Token-Rotation wird die `family_key` an den Nachfolger weitergegeben — alle aus diesem Login entstehenden Tokens teilen die Family.

```
Login Tablet (12:00)        →  T1 (family=F1)
  Refresh Tablet (13:00)    →  T2 (family=F1, T1.successor_key=T2.hash)
    Refresh Tablet (14:00)  →  T3 (family=F1, T2.successor_key=T3.hash)

Login Desktop (12:30)       →  T4 (family=F2)              # andere Family!
  Refresh Desktop (13:30)   →  T5 (family=F2, T4.successor_key=T5.hash)
```

Replay-Detection auf F1 (z.B. T1 wird nach 14:00 nochmal eingereicht) sprengt nur F1 — Desktop (F2) bleibt unbetroffen.

#### Grace-Window-Algorithmus (Pseudocode)

```python
GRACE_WINDOW = timedelta(seconds=60)


async def refresh_tokens(
    raw_token: str,
    *,
    device_id: Optional[str],
) -> TokenPair:
    stored = await refresh_token_repo.get_by_hash(sha256(raw_token))
    if stored is None or stored.revoked or stored.expires_at < now():
        raise UnauthorizedError("invalid_token")

    # --- Grace-Window-Pfad ---
    if stored.rotated_at is not None:
        age = now() - stored.rotated_at
        device_match = (
            stored.device_id is not None
            and device_id is not None
            and stored.device_id == device_id
        )

        if age <= GRACE_WINDOW and device_match:
            # Idempotent: bereits ausgestellten Nachfolger zurückgeben
            successor = await refresh_token_repo.get_by_hash(stored.successor_key)
            return TokenPair(
                access_token=mint_access_token(successor.user_key),
                refresh_token_handle=successor.handle,
            )

        # Replay erkannt — Family sprengen
        reason = (
            "grace_expired" if age > GRACE_WINDOW
            else "device_mismatch" if (stored.device_id and device_id)
            else "no_device_id"
        )
        await _detect_and_handle_replay(stored, reason)
        raise UnauthorizedError(
            error_code="refresh_replay_detected",
            family_invalidated=stored.family_key,
        )

    # --- Standard-Pfad (Token noch nicht rotiert) ---
    new_token = await _create_refresh_token(
        user_key=stored.user_key,
        family_key=stored.family_key,           # Family weitergeben
        device_id=device_id or stored.device_id,
        is_persistent=stored.is_persistent,
    )
    await refresh_token_repo.mark_rotated(
        token_hash=stored.token_hash,
        successor_key=new_token.token_hash,
        rotated_at=now(),
    )
    return TokenPair(
        access_token=mint_access_token(stored.user_key),
        refresh_token_handle=new_token.handle,
    )


async def _detect_and_handle_replay(stored: RefreshToken, reason: str) -> None:
    """Telemetrie + Family-Sprengung bei nachgewiesenem Replay."""
    logger.warning(
        "auth.refresh_replay_detected",
        family_key=stored.family_key,
        user_key=stored.user_key,
        reason=reason,
        token_age_seconds=(now() - stored.rotated_at).total_seconds(),
    )
    metrics.kp_auth_refresh_replay_total.labels(reason=reason).inc()

    # Alle Tokens der Family invalidieren (hard)
    affected = await refresh_token_repo.revoke_family(stored.family_key)
    logger.info(
        "auth.token_family_invalidated",
        family_key=stored.family_key,
        revoked_count=affected,
    )
```

#### Umsetzungsstand (#2116, v1.44)

Umgesetzt in `AuthService.refresh_tokens` / `ArangoRefreshTokenRepository`, mit diesen Abweichungen vom Pseudocode oben (gemessen und entschieden; der Betreiber kann sie überstimmen):

- **Kein Hard Cutover** (v1.9 sah vor, alle Refresh-Tokens beim Deployment zu invalidieren): Tokens ohne `family_key` bleiben bis zum Ablauf gültig und bilden bei ihrer ersten Rotation eine Family mit dem eigenen Schlüssel. Kein erzwungenes Neuanmelden.
- **Client-Abgleich über `User-Agent` statt `device_id`:** Das Frontend führt keine `device_id` (UI-NFR-012 R-049b nicht umgesetzt). Das Gnadenfenster greift nur bei gleichem, nicht leerem `User-Agent`; fehlt er auf einer Seite, gibt es kein Gnadenfenster (wie `device_id = null`).
- **Gnadenpfad gibt nur ein Access Token aus**, keinen Nachfolger: Der Klartext des Nachfolgers ist nicht rekonstruierbar (Tokens liegen nur als Hash vor). Der Cookie-Weg braucht ihn nicht — der Gewinner des Wettlaufs hat den Nachfolger bereits in das gemeinsame Cookie-Glas des Browsers geschrieben; die Antwort des Verlierers setzt keinen Cookie.
- **Body-Transport (gekoppelte Geräte) ohne Gnadenfenster:** Ein Client mit einem einzigen Token darf nicht doppelt rotieren; ein erneut vorgelegtes rotiertes Token sprengt die Family (auch nach verlorener Antwort — der Client koppelt neu).
- **Antwort `401 INVALID_TOKEN`** wie bei einem unbekannten Token, kein eigener `error_code` (der Fehlervertrag bleibt unverändert); der Fall steht im Log als `auth.refresh_replay_detected` mit `reason` ∈ {`grace_expired`, `no_grace_transport`, `client_mismatch`, `family_ended`}, pseudonymem `subject` und `family_revoked` (ob Tokens widerrufen wurden).
- **Keine Prometheus-Zähler** `kp_auth_refresh_replay_total` / `kp_auth_token_family_invalidated_total`: Die Domänenschicht schreibt keine Metriken (NFR-001); Auswertung über das Log-Ereignis. **Kein Eintrag im `security_audit_log`** (MT-014): dessen Zeilenmodell ist auf Mitgliedschaftsänderungen mit Pflicht-`tenant_key` zugeschnitten.
- **Die Family-Sprengung beendet auch die Access Tokens des Kontos** (`access_token_generation` steigt), damit der Inhaber des gestohlenen Strangs nicht noch bis zu 15 Minuten weiterarbeitet.
- **Rotation atomar:** Das Beanspruchen eines Tokens ist eine AQL-Anweisung mit Bedingung `revoked == false AND rotated_at == null`; von zwei gleichzeitigen Anfragen gewinnt genau eine.

#### Verhaltenstabelle

| Situation | `rotated_at` | Alter | Device-Match | Verhalten |
|-----------|--------------|-------|--------------|-----------|
| Token aktiv | `null` | — | — | Standard-Rotation, neues Paar ausstellen |
| Bereits rotiert, Grace, Match | gesetzt | ≤ 60s | ja | **Idempotent:** vorhandenen Nachfolger zurückgeben |
| Bereits rotiert, Grace, Mismatch | gesetzt | ≤ 60s | nein | **Replay:** Family sprengen, 401 |
| Bereits rotiert, Grace, no `device_id` | gesetzt | ≤ 60s | n/a (eines `null`) | **Replay:** Family sprengen, 401 |
| Bereits rotiert, außerhalb Grace | gesetzt | > 60s | beliebig | **Replay:** Family sprengen, 401 |

`device_id=null` auf beiden Seiten → kein Match möglich → kein Grace-Window. Das schützt API-Clients ohne PWA-Setup vor einem versehentlichen Replay-Schutz, indem solche Clients schlicht nicht doppelt rotieren dürfen.

#### Telemetrie

**Structlog-Event** (`logger.warning`):

```python
event="auth.refresh_replay_detected"
fields=[family_key, user_key, reason, token_age_seconds]
```

`reason` ∈ `{"grace_expired", "device_mismatch", "no_device_id"}`.

**Prometheus-Counter:**

```
kp_auth_refresh_replay_total{reason="grace_expired|device_mismatch|no_device_id"}
kp_auth_token_family_invalidated_total
```

Alerts (NFR-012, optional):
- > 5 Replay-Events pro 5 min für denselben User → wahrscheinlich Bug oder Angriff
- > 50 Replay-Events pro 5 min systemweit → systematischer Angriff oder Deployment-Regression

#### Hard Cutover bei v1.9-Deployment

Bei Deployment dieser Version werden **alle bestehenden Refresh-Tokens invalidiert** — bestehende Tokens haben kein `family_key`, kein `device_id`, kein `successor_key` und können nicht zuverlässig im Grace-Window-Schema betrieben werden.

```python
# Migrations-Skript (einmalig zur Deployment-Zeit)
async def cutover_refresh_tokens_v19():
    """W-004: Hard Cutover beim Upgrade auf v1.9.

    Alle bestehenden Refresh-Tokens werden revoked. Alle User müssen
    sich neu anmelden. Begründung: Bestehende Tokens haben kein
    family_key/device_id — Grace-Window-Schutz wäre nicht zuverlässig.
    """
    affected = await refresh_token_repo.revoke_all_active()
    logger.warning(
        "auth.v19_cutover_completed",
        revoked_count=affected,
        note="All active refresh tokens invalidated; users must re-login",
    )
```

Operator-Kommunikation: Im Release-Notes-Hinweis vermerken, dass alle User nach dem Upgrade neu einloggen müssen — analog zu Hash-Algorithmus-Wechseln in der Vergangenheit.

#### Frontend-Verhalten (Cross-Reference)

Frontend-Anforderungen sind in **UI-NFR-012 §3.9** definiert:
- R-049: `X-Device-Id`-Header beim Refresh-Aufruf mitsenden
- R-049a: Bei `error_code='refresh_replay_detected'` lokale Tokens löschen, Re-Login auffordern, Offline-Daten erhalten
- R-049b: `device_id` als UUIDv4 in IndexedDB persistieren, beim ersten Login generiert

<!-- /Quelle: Widerspruchsanalyse W-004 -->

<!-- Quelle: Issue #2037 -->
### 3.2b Neuer Bestätigungslink (`POST /auth/resend-verification`, #2037)

Ein Konto, dessen erster Bestätigungslink verloren ging oder abgelaufen ist,
kommt mit `REQUIRE_EMAIL_VERIFICATION=true` sonst nie in die Anmeldung: der Login
antwortet `403 EMAIL_NOT_VERIFIED`, und eine erneute Registrierung derselben
Adresse nimmt den Duplikat-Zweig (§3.2, SEC-H-009 — Info-Mail, kein neuer Token).
Der Endpunkt ist **anonym** und unterliegt denselben Anti-Enumerations-Regeln wie
Registrierung und Passwort-Reset.

**Eine Antwort für jede Adresse.** Immer `202 Accepted` mit demselben Body
(`"If this address belongs to an account that still needs verification, a new
verification email is on its way."`) — für eine unbekannte, eine unbestätigte, eine
bestätigte Adresse, einen Service-Account, ein Konto ohne lokales Passwort, eine
Adresse über ihrem Budget und eine Installation ohne Verifikationspflicht.

**Dieselbe Arbeit vor der Antwort.** Im Request-Pfad passiert für jede Adresse
genau eine Reservierung im Budget je Adresse (unten) und — innerhalb des Budgets —
die Übergabe einer Aufgabe an die FastAPI-Background-Tasks. Kontosuche,
Token-Schreiben und Versand laufen erst, nachdem die Antwort geschrieben ist
(#1890-Muster; der Passwort-Reset macht es seit #2062 genauso, §3.2c). Ein Zustellfehler wird gefangen und nur mit Typ geloggt
(`auth_mail_send_failed`, `kind=verification_resend`), nie mit Adresse.

**Wer eine Mail bekommt.** Nur mit `REQUIRE_EMAIL_VERIFICATION=true` (sonst wird
nichts reserviert und nichts verschickt) und nur ein Konto, das aktiv, unbestätigt,
interaktiv (`account_type` nicht `service`, #1559) ist und ein lokales Passwort hat.
Ein nur föderiertes Konto meldet sich beim Anbieter an und braucht keinen Link.

**Frischer Einmal-Token.** Jeder Versand schreibt den SHA-256-Hash eines neuen
Tokens (32 Byte, `secrets.token_urlsafe`; Feld `email_verification_token_hash`, v1.44) mit 24 h Gültigkeit
über den gespeicherten — jeder früher verschickte Link ist ab da ungültig.
`POST /auth/verify-email` löscht den Token beim Einlösen (einmalig verwendbar).
**Reihenfolge (#2062):** Token-Schreiben und Versand eines Kontos laufen unter einem
Lock je Konto und Tokenart (`KeyedLocks`, Eintrag nur solange jemand hält oder wartet),
auch beim Reset (§3.2c). Ohne ihn konnten ein anonymer Resend und ein bewiesener Link
(oder zwei Reset-Anfragen) so verschränken: Schreiben A, Schreiben B, Mail B, Mail A —
die zuletzt eintreffende Mail trug dann das schon überschriebene Token (mit Ereignissen
deterministisch reproduziert). Der Lock gilt je Prozess: Zwei Replikas können weiter
verschränken; Folge ist eine tote Mail über der gültigen, der Weg zurück ist eine
weitere Anfrage. Er wird nicht über Valkey verteilt — das wäre ein verteilter Lock mit
Ausfallpfad für höchstens eine tote Mail. Die Haltezeit ist die Versandzeit (SMTP-Timeout
10 s) und blockiert nur Mails desselben Kontos.

**Grenzen.**

| Grenze | Wert | Antwort bei Überschreitung | Umsetzung |
|--------|------|----------------------------|-----------|
| Je Client-IP | `settings.rate_limit_resend_verification`, Env `RATE_LIMIT_RESEND_VERIFICATION`, Default `10/hour` | `429 Too Many Requests` | slowapi-Limiter des Auth-Routers, Schlüssel über `resolve_client_ip` (#1130) |
| Je Adresse | 3 Anfragen; Auffüllung, sobald eine Stunde lang keine Anfrage für die Adresse kam (Fenster wird je Anfrage erneuert) | Unverändert `202`, es wird nur nichts verschickt | Zähler-Mechanik des Step-up-Throttles (`reserve_attempt`, atomar per `MULTI/EXEC`), eigene Instanz mit 1-h-Fenster und eigenem In-Process-Rückfall; Subject `verification-resend:<Adresse>`, normalisiert und als SHA-256 abgelegt (NFR-011); bei Valkey-Ausfall Rückfall auf die In-Process-Stufe, nie fail-open |

Die Grenze je IP darf `429` antworten, weil sie eine Eigenschaft der Quelle ist,
nie der Adresse. Die Grenze je Adresse zählt **jede** eingegebene Adresse gleich,
bevor irgendetwas über sie bekannt ist — ein Budget nur für echte Konten wäre selbst
das Orakel —, und antwortet deshalb stumm. Beide Werte sind nach der legitimen
Nutzung bemessen (ein, höchstens zwei neue Links; mehrere Personen hinter einem
NAT). Die Grenze je Adresse ist bewusst nicht konfigurierbar: ein höherer Wert
macht den Endpunkt wieder zum Werkzeug, ein fremdes Postfach zu fluten.

**Restrisiko.** Wer eine fremde Adresse dauerhaft über ihrem Budget hält (eine
Anfrage pro Stunde reicht), verhindert neue Links **über diesen Endpunkt**. Das ist
der Preis der stummen Grenze je Adresse. Seit #2046 sperrt das den Inhaber nicht
mehr aus: die Login-Ablehnung mit korrektem Passwort verschickt den Link auf einem
eigenen Budget (unten). Ein Plattform-Admin kann zusätzlich `email_verified` über
`PATCH /admin/platform/users/{key}` setzen — aber erst, nachdem er geprüft hat, dass
die anfragende Person das Postfach besitzt: Hat jemand eine fremde Adresse
registriert (Squatting), bestätigt dieser Schritt das Konto des Squatters. Im
Zweifel löscht er das Konto, statt es zu bestätigen.

<!-- Quelle: Issue #2046 -->
**Neuer Link über die Login-Ablehnung (#2046).** Die Ablehnung
`403 EMAIL_NOT_VERIFIED` von `POST /auth/login` wird erst nach dem korrekten
Passwort erreicht (nach Sperr-, Passwort- und Aktiv-Prüfung). Sie verschickt den
neuen Link deshalb selbst, ohne neuen Endpunkt und ohne Passwort in einem
weiteren Request-Body:

- **Wann:** nur mit `REQUIRE_EMAIL_VERIFICATION=true` und nur für ein Konto, das
  einen Link braucht (aktiv, unbestätigt, interaktiv, lokales Passwort, keine
  Tombstone-Adresse — dieselbe Prüfung wie oben).
- **Budget je Konto:** vor dem Versand eine Reservierung auf einem eigenen Budget,
  Subject `verification-resend-proven:<user_key>` (Kontoschlüssel, nicht Adresse:
  keine Schreibweise der Adresse kauft ein zweites Budget, und das anonyme Subject
  `verification-resend:<Adresse>` kann es nie verbrauchen). 3 Links, Auffüllung
  nach einer Stunde ohne Anforderung, als SHA-256 abgelegt (NFR-011). Gleiche
  Mechanik wie oben, eigene Instanz: Valkey-geteilt, bei Ausfall Rückfall auf die
  eigene In-Process-Stufe, nie fail-open. Diese Stufe hat die Grenze der
  Rückfall-Stufe des Step-ups (feste Kapazität von 4096, LRU-Verdrängung eines
  verbrauchten Budgets) — hier zählen allerdings Konten, die nur mit ihrem
  Passwort erreichbar sind. Die beiden anonymen Budgets (oben und §3.2c)
  verdrängen nicht (#2058, §3.2c).
- **Nach der Antwort:** Token-Schreiben und Versand laufen als eine Einheit über
  die Background-Tasks (#1890-Muster), Zustellfehler werden gefangen und nur mit
  Typ geloggt (`auth_mail_send_failed`, `kind=verification_resend_proven`).
  Empfänger ist `user.email` (gespeicherte Schreibweise), nie die eingegebene.
  Weil FastAPI Background-Tasks verwirft, wenn der Handler eine Exception wirft,
  gibt die Login-Route die Ablehnung als Antwort zurück — gebaut von derselben
  Funktion wie der Exception-Handler (`app_error_response`).
- **Kein neues Orakel:** Die Ablehnung war schon vorher von der Antwort auf ein
  falsches Passwort unterscheidbar. Status, Body und Header-Namen bleiben
  unverändert — gleich, ob eine Mail ging, das Budget erschöpft war oder die
  Zustellung scheiterte. Die Header-Namen gelten nur, solange
  `RATELIMIT_HEADERS_ENABLED` nicht gesetzt ist: slowapi liest den Schalter aus
  der Umgebung, und mit `true` trägt die jetzt zurückgegebene `403`
  `X-RateLimit-*`-Header, eine geworfene Antwort wie die `401` nicht; ein falsches Passwort antwortet unverändert `401` und
  reserviert und verschickt nichts.

| Grenze | Wert | Antwort bei Überschreitung |
|--------|------|----------------------------|
| Je Client-IP | `settings.rate_limit_auth` (`RATE_LIMIT_AUTH`, gilt für den ganzen Login) | `429 Too Many Requests` |
| Je Konto | 3 Links; Auffüllung, sobald eine Stunde lang keine Anmeldung mit `EMAIL_NOT_VERIFIED` abgelehnt wurde — jede solche Ablehnung reserviert, auch über dem Budget, und erneuert damit das Fenster | Unverändert `403 EMAIL_NOT_VERIFIED`, es wird nur nichts verschickt |

Wer das Passwort kennt, kann über diesen Weg höchstens dreimal pro Stunde einen
Link an das Postfach schicken lassen. Das ist eines von drei unabhängigen Budgets
für dasselbe Postfach: Reset (§3.2c, 3), anonymer Bestätigungslink (oben, 3) und
dieser Weg (3) — zusammen bis zu 16 Mails pro Stunde an ein Postfach (gemessen über den
Service mit den Produktions-Stores, #2062: 3 + 3 + 10, bei vier oder mehr Quellen für den
Reset; keine Mail darüber hinaus innerhalb des Fensters), während eines Valkey-Ausfalls bis
zu 16·P + 16 bei P Backend-Prozessen (aus der früheren Rechnung abgeleitet, nicht gemessen). Ein gemeinsames Budget über die drei Wege gibt es
bewusst nicht: Wer eine fremde Adresse registriert, verbräuchte damit den Reset der
Inhaberin — dieselbe Aussperrung durch Dritte wie in §3.2c. Wer das Passwort hält, hält
nicht unbedingt das Postfach: Wer eine fremde Adresse registriert (Squatting), kennt
das Passwort seines Kontos, aber die Mails gehen an die echte Inhaberin der Adresse.

**Restrisiko beider Wege.** Wer Adresse **und** Passwort kennt, kann den Inhaber
aus beiden Wegen zugleich aussperren: Sind beide Budgets einmal verbraucht, hält
etwa eine anonyme Resend-Anfrage und eine Anmeldung pro Stunde (rund zwei Anfragen)
beide Fenster offen. Ausweg ist der Plattform-Admin, der `email_verified` über
`PATCH /admin/platform/users/{key}` setzt — nach Prüfung, dass die anfragende
Person das Postfach besitzt; im Squatting-Fall bestätigt er sonst das Konto des
Squatters und löscht es besser.

**Frontend.** Die Login-Seite zeigt bei `error_code=EMAIL_NOT_VERIFIED` statt des
englischen Backend-Texts einen lokalisierten Hinweis (`role="alert"`), der den
über die Ablehnung verschickten Link nur in Aussicht stellt — „falls ein neuer
Link fällig war, ist er unterwegs“, nie „gesendet“ (#2046) —, und darunter als
Rückfall die Aktion „Neue Bestätigungs-E-Mail senden" (für die Adresse des
abgelehnten Logins; Ergebnis in einer `role="status"`-Live-Region). Die Fehlerseite eines ungültigen Links
verweist auf `ResendVerificationPage` (`/resend-verification`, §4.1).

<!-- Quelle: Issue #2043 -->
### 3.2c Budget je Adresse beim Passwort-Reset (`POST /auth/password-reset/request`, #2043)

Der Reset-Endpunkt ist anonym, und der Aufrufer wählt den Empfänger. Bis #2043
begrenzte ihn nur das IP-Limit `RATE_LIMIT_AUTH` (`20/minute`): Eine Quelle konnte
einem Postfach zwanzig Reset-Links pro Minute schicken, jede weitere Quelle zwanzig
mehr — Last auf dem Postfach und auf der Absender-Reputation (ein Resend-`429`
blockiert dann auch legitime Mails).

| Grenze | Wert | Antwort bei Überschreitung | Umsetzung |
|--------|------|----------------------------|-----------|
| Je Client-IP | `settings.rate_limit_auth`, Env `RATE_LIMIT_AUTH`, Default `20/minute` | `429 Too Many Requests` | slowapi-Limiter des Auth-Routers, Schlüssel über `resolve_client_ip` (#1130) |
| Je Adresse und Client-IP (#2059) | 3 Anfragen; Auffüllung, sobald von dieser IP eine Stunde lang keine Anfrage für die Adresse kam (Fenster wird je Anfrage dieser Quelle erneuert, auch über dem Budget) | Unverändert `200` mit demselben Body und denselben Headern, es wird nur nichts verschickt | Wie das Budget in §3.2b, aber eigene Instanz: Zähler-Mechanik des Step-up-Throttles (`reserve_attempt`, atomar per `MULTI/EXEC`), 1-h-Fenster, eigener In-Process-Rückfall; Subject `password-reset-source:<Adresse>|<IP>`, IP aus `resolve_client_ip` (ohne auflösbare IP: eine gemeinsame Quelle `unknown`), die Adresse getrimmt und kleingeschrieben, als SHA-256 abgelegt (NFR-011); bei Valkey-Ausfall Rückfall auf die In-Process-Stufe, nie fail-open |
| Je Adresse insgesamt (#2059) | 10 Links über alle Quellen; gezählt und erneuert **nur** für Anfragen, die die erste Stufe zugelassen hat; Auffüllung, sobald eine Stunde lang keine solche Anfrage kam | wie oben | Dieselbe Instanz, Subject `password-reset:<Adresse>` (`MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW`) |

Beide Reservierungen laufen **vor** der Kontosuche, für jede eingegebene Adresse
gleich — unbekannt, Service-Account oder echtes Konto: zuerst je Adresse und Quelle,
dann (nur wenn die erste zulässt) je Adresse insgesamt. Über einem der Budgets folgt
weder Kontosuche noch Token noch Mail. Innerhalb der Budgets laufen Kontosuche,
Token-Schreiben und Versand seit #2062 erst nach der Antwort, wie beim
Bestätigungslink: Im Request-Pfad stehen nur die Reservierungen, diesseits wie
jenseits des Budgets (vorher machte die Kontosuche eine Antwort innerhalb des
Budgets messbar langsamer als eine darüber). Die Anfrage, die eine Stufe als erste
überschreitet, loggt `password_reset_budget_exhausted` mit `stage`
(`address_source` / `address`) und `email_digest` (HMAC mit `LOG_PSEUDONYM_SALT`) —
nie die Adresse, nie die IP; weitere Anfragen über dem Budget loggen nichts.

**Empfänger ist die gespeicherte Adresse (#2060).** Der Link geht an `user.email`,
nicht an die eingegebene Schreibweise — wie beim Bestätigungslink (§3.2b) und bei
der Login-Ablehnung. Die Kontosuche vergleicht ohne Groß-/Kleinschreibung, ein
Mailserver darf den lokalen Teil aber unterscheiden (RFC 5321): Ein Link für
`Owner@d` hätte sonst ein anderes Postfach `owner@d` erreichen können. Gemessen
(ArangoDB 3.12.8, Python 3.14): Python `str.lower()` und AQL `LOWER()` stimmen bei
allen 1152 BMP-Zeichen mit Kleinbuchstaben-Abbildung überein außer 13 neueren
Unicode-Großbuchstaben (u. a. U+1C89, U+2C2F, U+A7C0–U+A7DC, U+A7F5), die AQL
unverändert lässt. Das Budget (Python) ist dort gröber als die Kontosuche (AQL):
Zwei Konten, die sich nur in einem dieser Zeichen unterscheiden, teilen sich ein
Budget — die sichere Richtung; eine Schreibweise, die bei gleichem Konto ein zweites
Budget kauft, gibt es nicht. EmailStr kleinschreibt nur die Domain. Beide Budgets sind getrennt: Wer das Budget des
Bestätigungslinks einer Adresse ausschöpft, verbraucht nicht ihr Reset-Budget, und
umgekehrt. Wert und Fenster sind die des Bestätigungslinks und ebenso bewusst
nicht konfigurierbar.

**Aussperren durch Dritte (#2059).** Bis #2059 zählte das Budget nur je Adresse,
und jede Anfrage — auch über dem Budget — erneuerte das Fenster: Eine Anfrage pro
Stunde und Adresse hielt die Adresse dauerhaft über dem Budget, ohne jede Kenntnis
des Kontos. Gemessen über die echte Route mit gefälschter Uhr (IP-Limit 20/min als
3 s je Anfrage): eine Quelle hielt 1000 und 1199 Adressen; 100 von 1000 Inhaberinnen
fragten von ihrer eigenen IP an und bekamen **0** Links. (Bei genau 1200 Adressen
läuft das Fenster beim nächsten Durchgang gerade ab — die Grenze liegt bei 1199,
nicht bei den zuvor genannten „rund 1200“.) Seit #2059 verbraucht eine Quelle nur
ihr eigenes Budget je Adresse; dieselbe Messung ergibt 100 von 100 Links. Aussperren
geht nur noch über das Gesamtbudget: zehn **zugestellte** Links je Stunde, also
mindestens vier Quellen je Adresse, deren Links tatsächlich bei der Inhaberin
ankommen. Der Preis: Ein Postfach kann jetzt bis zu zehn statt drei Reset-Links je
Stunde bekommen (aus mindestens vier Quellen).

**Kein Admin-Weg.** Kein Endpunkt setzt ein Passwort, löst einen Reset-Link aus oder
leert das Budget — auch nicht für eine Plattform-Administratorin
(Betreiberentscheidung zu #2059). Wer ausgesperrt ist, wartet eine Stunde ohne
Anfrage oder meldet sich mit dem bisherigen Passwort an, wenn sie es noch kennt;
hat ein Squatter ihre Adresse registriert, gibt es kein „bisheriges Passwort“ von
ihr. Das Log-Ereignis `password_reset_budget_exhausted` macht gehäufte
Überschreitungen für Betreiber sichtbar, ohne die Adresse zu nennen.

**Valkey ohne AUTH — Entscheidung für den Betreiber (#2062, #2050).** Die `LIMITS:*`-
und Budget-Schlüssel liegen in einem Valkey ohne Passwort; ihre Integrität ruht auf der
NetworkPolicy des Charts (`networkpolicies.valkey`): Ingress nur von den Controllern
`backend`, `celery-worker` und `celery-beat` auf 6379. Gemessen am Chart: kein
`requirepass`, keine ACL, `REDIS_URL` ohne Zugangsdaten. Ein eigener DB-Index trennt
nichts (ein Server, keine ACL je Index); ein Passwort wäre ein Secret in allen drei
Controllern und in `REDIS_URL` und ist eine Chart-/Secret-Änderung. Wer einen dieser
drei Pods beherrscht, kann die Zähler ohnehin umgehen (das Backend signiert die Tokens
selbst); schützen muss die Richtung „fremder Pod im Namespace“, und die schließt nur
eine CNI, die NetworkPolicies durchsetzt — eine ohne diese Durchsetzung lässt die Regel
wirkungslos. **Vorschlag:** Annahme mit dieser Begründung und `requirepass` nur dort, wo die
CNI keine NetworkPolicies durchsetzt; nicht von dieser Änderung entschieden, Helm-Secrets
sind unverändert.

**Alle Valkey-Clients der Request-Pfade sind begrenzt (#2062).** `_get_redis_client()`
und der OAuth-State-Store nutzten die redis-py-Vorgabe von 5 s je Socket-Operation:
gemessen gegen einen Socket, der annimmt und nie antwortet, 5,01 s je Aufruf, die
anonyme Kopplungs-Einlösung (`POST /auth/device-pairing/redeem`, Throttle plus
Code-Store) 10,10 s. Beide benutzen jetzt `bounded_redis_client_options()` wie der
Limiter (0,5 s je Verbindung und Lesen, kein Retry): 0,50 s je Aufruf, die Einlösung
1,10 s. Jeder dieser Aufrufer behandelt einen Valkey-Fehler schon als Ausfall (lokale
Stufe oder fail-closed wie der API-Key-Limiter, SEC-004); verkürzt ist die Dauer eines
Ausfalls, nicht seine Bedeutung. Der Rückfall mit Probenplan (`LatchedRedis`) bleibt den
Budget-Stores vorbehalten.

**Bei Valkey-Ausfall** zählt jeder Prozess für sich: bis zu 3 Links je Adresse,
Stunde und Worker-Prozess über alle Replikas. **Die In-Process-Stufe verdrängt nie
(#2058)** — das gilt für dieses Budget und das von §3.2b, deren Subjects frei
gewählte Adressen sind: Bis dahin verdrängte die volle Stufe (4096 Einträge) den
ältesten Eintrag und mit ihm ein verbrauchtes Budget; gemessen über die echte
Route mit ausgefallenem Valkey: nach 4096 erfundenen Adressen bekam das Opfer einen
vierten Link. Jetzt wirft eine volle Stufe (`anonymous_budget_fallback`, 16 384
Einträge je Prozess und Budget) zuerst abgelaufene Einträge hinaus; ist sie dann
noch voll, gilt eine **neue** Adresse als über dem Budget — stumm, kein Link —, bis
Einträge ablaufen (einmal je Episode `anonymous_budget_fallback_full` im Log, ohne
Adresse). Seit #2059 belegt beim Reset eine neue Adresse aus einer neuen Quelle
zwei Einträge (je Quelle und insgesamt). Der Preis: Wer während eines Ausfalls
16 384 Einträge in einen Prozess
schickt, hält neue Reset-Links dieses Prozesses bis zu eine Stunde lang auf.
**`maxmemory` des Chart-Valkey** bleibt ungesetzt (Default `noeviction` ohne
Obergrenze), bewusst: Eine Verdrängungs-Policy (`allkeys-*`, `volatile-*`) würde
Budget- und Limiter-Schlüssel — alle mit TTL — verdrängen und so verbrauchte
Budgets zurückgeben; `noeviction` mit Obergrenze ließe bei vollem Speicher auch die
Celery-Queue scheitern. Das Wachstum ist begrenzt: Limiter-Schlüssel je Client-
Adresse und Route (§3.8, #2052), Budget-Schlüssel je Anfrage höchstens eine Stunde. Die Zähler der beiden Stufen sind
getrennt, ein flatternder Valkey kann deshalb bis zu 3 weitere Links freigeben —
solange Valkey seine Schlüssel behält. Ein Neustart, der sie verliert, gibt je
Budget weitere 3 frei.

### 3.2d Registrierungsmodus (`REGISTRATION_MODE`, #2132)

**Betreiberentscheidung 2026-10-04.** Wer ein Konto anlegen darf, entscheidet der Betreiber, nicht der Zufall der
Erreichbarkeit. Zwei Einstellungen:

| Einstellung | Werte | Default |
|---|---|---|
| `REGISTRATION_MODE` | `open` · `invite_only` · `closed` | `open` (unverändertes Verhalten) |
| `REGISTRATION_ALLOWED_DOMAINS` | kommagetrennte E-Mail-Domains, exakt, Groß-/Kleinschreibung egal, keine Subdomains | leer = jede Domain |

**Regel** (in dieser Reihenfolge entschieden, `RegistrationPolicy.admits`):

1. `closed` lässt **niemanden** zu — auch nicht mit Einladung. Begründung: Ließe die Einladung auch hier zu, wären `closed` und `invite_only` derselbe Modus. Neue Konten entstehen dann nur durch den Betreiber (Seeds, Plattform-Admin).
2. Eine **E-Mail-Einladung**, die die Adresse zulässt — Typ `email`, Status `pending`, nicht abgelaufen, ausgestellt für genau diese Adresse (Groß-/Kleinschreibung egal) —, ist die Ausnahme von `invite_only` **und** von der Allowlist. Bewiesen wird sie
   - bei der **lokalen Registrierung** durch ihr Token (`invitation_token` im Body von `POST /auth/register`) — die bloße Existenz einer Einladung für eine Adresse genügt nicht, sonst könnte jemand die eingeladene Adresse vor ihrem Inhaber belegen;
   - bei der **ersten OIDC-Anmeldung** ohne Token durch die vom Anbieter bestätigte Adresse (`email_verified: true`). Eine unbestätigte Adresse wird gar nicht erst nachgeschlagen.
3. `invite_only` lässt sonst niemanden zu.
4. `open` lässt jeden zu; mit Allowlist nur Adressen ihrer Domains. Bei der ersten OIDC-Anmeldung zählt die Allowlist nur für eine vom Anbieter bestätigte Adresse.

Eine **Link-Einladung** öffnet keine Registrierung: Sie ist zum Teilen gedacht, ein weitergegebener Link würde die Installation für jeden öffnen, der ihn hat. Die Annahme einer Einladung durch ein bestehendes Konto (REQ-024 §1a.2) bleibt von der Einstellung unberührt.

**Antwort.** Jede Ablehnung ist `403 REGISTRATION_NOT_ALLOWED` mit derselben Meldung — gleich, ob der Modus, das Token oder die Domain der Grund ist, und gleich, ob die Adresse bereits ein Konto hat: Die Entscheidung fällt vor jedem Lesen gespeicherter Konten und vor der bcrypt-Runde. Die erste OIDC-Anmeldung leitet mit `?error=registration_not_allowed` zurück; es wird nichts angelegt. Die Ablehnung wird nur mit dem gesalzenen Adress-Digest geloggt (`registration_refused`). Das IP-Rate-Limit von `/auth/register` gilt unverändert.

**Bestehende Konten** melden sich in jedem Modus an (lokal und über OIDC, inklusive Auto-Link nach §2); der Modus entscheidet nur über das **Anlegen**.

**Frontend.** `GET /mode` liefert `registration: {mode, domain_restricted}` (die Domains selbst werden nicht veröffentlicht). Die Anmeldeseite blendet den Registrieren-Link bei `closed` aus und beschriftet ihn bei `invite_only` als „Mit Einladung registrieren"; die Registrierungsseite zeigt bei `closed` nur einen Hinweis, bei `invite_only` ein Pflichtfeld „Einladungscode" (vorbelegt aus `/register?invitation=<token>`). Das Frontend ist nur Hinweis — durchgesetzt wird im Backend.

**Light-Modus** ist unberührt: Er bindet keine `/auth`-Routen ein; `/mode` meldet dort `closed`.

<!-- Quelle: Smart-Home-HA-Integration Review A-003 -->
### 3.7 M2M-Authentifizierung (API-Keys)

Neben der JWT-basierten Browser-Authentifizierung unterstützt Kamerplanter **langlebige API-Keys** für Machine-to-Machine-Zugriff. Hauptanwendungsfälle: Home Assistant Custom Integration, CI/CD-Pipelines, Monitoring-Systeme.

<!-- Quelle: Widerspruchsanalyse W-015 -->
**Light-Modus-Hinweis (W-015):** Service Accounts und API-Keys sind im Light-Modus (REQ-027) **deaktiviert** — die Light-Modus-Endpunkte sind ohne Auth erreichbar, externe Integrationen brauchen keinen Bearer-Token. Bei Upgrade Light→Full (REQ-027 §1.1 Szenario 5) müssen externe Integrationen auf Service-Account-API-Keys umgestellt werden; bestehende Konfigurationen erhalten 401 beim nächsten API-Aufruf nach Mode-Switch.
<!-- /Quelle: Widerspruchsanalyse W-015 -->

#### Datenmodell

**`ApiKey`** — ArangoDB Document Collection `api_keys`:

```python
class ApiKey(BaseModel):
    _key: str                          # Auto-generiert
    user_key: str                      # Besitzer (human User ODER Service Account)
    label: str                         # Vom User vergebener Name (z.B. "Home Assistant")
    key_prefix: str                    # Erste 8 Zeichen des Keys (für Anzeige: "kp_a3f8...")
    key_hash: str                      # SHA-256-Hash des vollständigen Keys
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    tenant_scope: str | None = None    # Optional: Key auf einen Tenant beschränken
```

**Edge:** `has_api_key` (User → ApiKey) — funktioniert für `account_type: 'human'` und `account_type: 'service'` gleichermaßen, da Service Accounts als User modelliert sind.

#### Key-Format

```
kp_<48 hex characters>
```

- Prefix `kp_` identifiziert Kamerplanter-Keys (unterscheidbar von JWTs)
- 48 Hex-Zeichen = 192 Bit Entropie (kryptografisch sicher via `secrets.token_hex(24)`)
- Speicherung in DB: **nur SHA-256-Hash** — Klartext wird bei Erstellung einmalig angezeigt

#### Middleware-Erkennung

```python
# Authorization-Header-Auswertung:
# Bearer kp_...  → API-Key-Lookup (SHA-256-Hash vergleichen)
# Bearer eyJ...  → JWT-Validierung (bestehender Flow)
```

Die Middleware erkennt anhand des `kp_`-Prefix automatisch, ob ein API-Key oder JWT vorliegt. API-Keys werden gegen den gespeicherten Hash validiert und `last_used_at` wird aktualisiert.

**`tenant_scope` gilt auf REST und MCP gleich, Abgleich auf den Tenant-Key (#1852):** Der Wert wird bereits beim Anlegen des Keys aufgelöst und geprüft — der Aufrufer muss im benannten Tenant (per Slug oder Key referenzierbar) *aktives* Mitglied sein, sonst weist `POST /auth/api-keys` mit `403 Forbidden` ab ("tenant_scope must name a tenant you are an active member of."), mit derselben Antwort für einen unbekannten wie für einen fremden Tenant. Gespeichert und zurückgegeben wird ausschließlich der **Key** des Tenants, nicht der eingegebene Slug — ein Abgleich auf den Slug findet zur Laufzeit nicht mehr statt. Dadurch bleibt der Scope über eine Umbenennung des Tenants hinweg stabil, und die Tenant-Löschung, die Keys mit passendem `tenant_scope` widerruft, trifft weiterhin genau die richtigen Keys. Bestandskeys wurden per Migration (v0063) auf den Tenant-Key umgeschrieben, sofern der Besitzer dort noch aktives Mitglied war, sonst widerrufen.

Auf REST geschieht die Bindung in der Tenant-Auflösung (`/t/{slug}/`-Pfad und `X-Active-Tenant`-Header) mit derselben 403-Antwort wie für einen fremden Tenant; der header-lose Fallback auf den persönlichen Tenant greift nur, wenn dieser der Scope ist, sonst gilt nur der globale Katalog.

**Routen ohne Tenant-Auflösung sind seit #1851 erfasst.** Ein Key mit `tenant_scope` handelt nur innerhalb des einen Tenants — die folgende Tabelle zeigt, wie jede Routenklasse mit einem begrenzten Key umgeht:

| Routenklasse | Beispiele | Verhalten mit `tenant_scope` |
|---|---|---|
| Konto-/Anmeldedaten-Routen | `PATCH`/`DELETE /users/me`, Passwort, Sitzungen, verknüpfte Provider | `403 Forbidden` über `require_account_principal` ("This API key is restricted to one tenant and cannot act on the account.") |
| Datenschutz-Routen | `/api/v1/privacy/*` | `403 Forbidden` über `require_account_principal` |
| Tenant-Lebenszyklus & API-Key-Verwaltung | `POST /tenants`, `POST /tenants/invitations/accept`, `POST`/`GET`/`DELETE /auth/api-keys`, `POST /auth/device-pairing`, `POST /auth/logout-all` | `403 Forbidden` über `require_account_principal` |
| Kontoweite Einstellungen unter `/t/{slug}/` | `PUT …/notifications/preferences`, `POST …/notifications/pwa/subscribe`/`unsubscribe`, `PATCH …/user-preferences`, `POST …/onboarding/skip`/`reset`, `PATCH …/onboarding/state`, `DELETE …/favorites/{key}` | `403 Forbidden` über `require_account_principal` — die Einstellungen gelten für alle Tenants des Kontos, nicht nur für den Scope-Tenant |
| Plattform-Admin-Routen | `/api/v1/admin/*` | Abgewiesen — ein begrenzter Key ist nie Plattform-Admin (unabhängig von `require_account_principal`) |
| Tenant-auflösende Routen | `/t/{slug}/...`, jede Route mit `X-Active-Tenant` | Scope bindet wie zuvor beschrieben |
| Identitätsabfrage | `GET /users/me` | Zugelassen — liefert `is_platform_admin: false` für einen begrenzten Key |
| Tenant-Liste | `GET /tenants` | Zugelassen, aber auf den Scope-Tenant eingeengt |
| Globale Stammdaten & Berechnungen | z. B. Arten-/Sorten-Katalog, IPM-Referenzdaten, zustandslose Rechner | Zugelassen — kein Tenant-Bezug |

Ein Key **ohne** `tenant_scope` ist von dieser Tabelle nicht betroffen.

**IP-Allowlist und Rate Limit gelten für REST und MCP durch dieselbe Implementierung (#1850):** `ip_allowlist` (CIDR-Liste) und `rate_limit_per_minute` auf `ApiKey` wurden bis dahin nur vom MCP-Authenticator gelesen; ein REST-Aufruf mit demselben Key war davon unberührt. Beide Kontrollen laufen jetzt über eine gemeinsame Funktion, die von beiden Oberflächen aufgerufen wird — eine Adresse außerhalb der Allowlist (oder eine nicht auflösbare) liefert auf beiden Wegen `401 Unauthorized` ("Client IP is not permitted for this API key."), ein überschrittenes Budget `429 Too Many Requests`. Das Budget ist eine Eigenschaft des Keys, nicht der Oberfläche: REST- und MCP-Aufrufe desselben Keys teilen sich einen Zähler pro Minute. Ist der Zähler-Speicher nicht erreichbar, wird `429` geantwortet (fail-closed) statt das Limit stillschweigend zu ignorieren.

<!-- Quelle: Service Accounts v1.7 -->
**Erweiterter Flow bei Service-Account-API-Keys:**

Bei API-Key-Authentifizierung wird zusätzlich geprüft:
1. **IP-Allowlist:** Wenn `allowed_ip_ranges` auf dem zugehörigen User (Service Account) gesetzt ist, wird die Client-IP gegen die CIDR-Bereiche geprüft. Mismatch → 403 Forbidden.
2. **Service-Account-Status:** `status` des Service Accounts muss `active` sein. Suspended/Deleted → 401 Unauthorized.
3. **Rate Limit:** `rate_limit_rpm` des Service Accounts wird als individuelle Obergrenze verwendet (statt des globalen 1000 req/min Defaults).
4. **`last_active_at`:** Wird bei jedem erfolgreichen API-Key-Zugriff auf dem Service Account aktualisiert.
<!-- /Quelle: Service Accounts v1.7 -->

#### Rate Limiting

| Auth-Methode | Rate Limit | Begründung |
|-------------|-----------|-----------|
| JWT (Browser) | 100 req/min | Interaktive Nutzung, geringere Last |
| API-Key (M2M) | 1000 req/min | Coordinator-Polling, Batch-Operationen |

#### API-Endpoints

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/api/v1/auth/api-keys` | Neuen API-Key erstellen — Step-up nach §3.9 (#1847), kein API-Key | JWT (nur authentifizierte User) |
| `GET` | `/api/v1/auth/api-keys` | Alle eigenen Keys auflisten | JWT |
| `DELETE` | `/api/v1/auth/api-keys/{key_id}` | Key revoken | JWT |

**POST /api/v1/auth/api-keys — Request:**
```json
{
  "label": "Home Assistant",
  "tenant_scope": "mein-garten",
  "current_password": "<aktuelles Passwort>"
}
```

**POST /api/v1/auth/api-keys — Response (einmalig mit Klartext):**
```json
{
  "_key": "ak_001",
  "label": "Home Assistant",
  "api_key": "kp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "key_prefix": "kp_a3f8...",
  "created_at": "2026-02-27T14:30:00Z",
  "tenant_scope": "t-a1b2c3d4"
}
```

Die Request nennt den Tenant per Slug (oder Key); gespeichert und in der Response zurückgegeben wird stets der Tenant-**Key** (#1852, siehe oben).

> **Hinweis:** Der vollständige Key wird nur bei der Erstellung angezeigt. Nach dem Schließen des Dialogs ist er nicht mehr abrufbar. Bei Verlust muss ein neuer Key erstellt werden.

**`UserService`** — Benutzerprofil-Verwaltung:

```python
class UserService:
    def __init__(self, user_repo, auth_provider_repo): ...

    async def get_profile(self, user_key: str) -> UserProfile: ...
    async def update_profile(self, user_key: str, updates: UserProfileUpdate) -> User: ...
        # Erlaubte Felder: display_name, avatar_url, locale, timezone
    async def list_auth_providers(self, user_key: str) -> list[AuthProviderInfo]: ...
    async def list_active_sessions(self, user_key: str) -> list[SessionInfo]: ...
    async def delete_account(self, user_key: str) -> None: ...
        # Soft-Delete: status → deleted, E-Mail anonymisiert
        # Alle Refresh Tokens invalidiert
        # Tenant-Mitgliedschaften entfernt (REQ-024)
```

### 3.3 API-Schicht

**Router: `/api/v1/auth`** — Authentifizierung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| POST | `/auth/register` | Lokale Registrierung; Body optional `invitation_token`. `403 REGISTRATION_NOT_ALLOWED`, wenn der Registrierungsmodus die Adresse nicht zulässt (§3.2d, #2132) | Nein |
| POST | `/auth/login` | Lokaler Login (Body: `email`, `password`, `remember_me: bool = false`); `403 EMAIL_NOT_VERIFIED` nach korrektem Passwort verschickt einen neuen Bestätigungslink, 3 je Konto und Stunde (§3.2b, #2046) | Nein |
| POST | `/auth/logout` | Logout (aktuelles Gerät) | Ja |
| POST | `/auth/logout-all` | Logout (alle Geräte) | Ja |
| POST | `/auth/refresh` | Token-Refresh (Cookie-Pfad **oder** optionaler Body-Token `{"refresh_token"}` für native Clients, #1118 — siehe §3.8) | Nein (Cookie oder Body) |
| POST | `/auth/device-pairing` | Einmaligen QR-Kopplungscode erzeugen (#1118, §3.8) — Step-up nach §3.9 (#1847) | Ja (Bearer) |
| POST | `/auth/device-pairing/redeem` | QR-Kopplungscode gegen Token-Paar einlösen (#1118, §3.8) | Nein (öffentlich) |
| POST | `/auth/verify-email` | E-Mail bestätigen | Nein |
| POST | `/auth/resend-verification` | Neuen Bestätigungslink anfordern — immer `202`, gleicher Body für jede Adresse; 10/h je IP, 3 je Adresse (§3.2b, #2037) | Nein |
| POST | `/auth/password-reset/request` | Passwort-Reset anfordern — immer `200`, gleicher Body für jede Adresse; 20/min je IP, 3 je Adresse und IP, 10 je Adresse insgesamt, je Stunde (§3.2c, #2043, #2059) | Nein |
| POST | `/auth/password-reset/confirm` | Passwort-Reset durchführen | Nein |
| GET | `/auth/oauth/providers` | Aktivierte Provider auflisten (für Login-Seite) | Nein |
| GET | `/auth/oauth/{provider_slug}` | OAuth-Redirect initiieren | Nein |
| GET | `/auth/oauth/{provider_slug}/callback` | OAuth-Callback verarbeiten | Nein |

<!-- #1461 -->
**Der Callback ist ein Schreibpfad mit GET-Verb.** Der Identity-Provider schickt den Nutzer
per Browser-Redirect zurück; ein Redirect kann nur ein `GET` sein, ein anderes Verb steht
protokollbedingt nicht zur Verfügung. Der Handler legt dabei den User an oder aktualisiert
ihn, verknüpft den `AuthProvider` und stellt das Refresh-Token aus — er **persistiert also
auf einem `GET`**, und das ist hier kein Defekt, sondern die Form, die OAuth2 vorgibt. Die
Ausnahme ist an die gemessenen Schreibsenken gebunden (`_INTENTIONAL_PERSISTING_READS` in
`tests/unit/api/test_write_route_gates.py`): erreicht der Handler eine Schreibstelle, die
dort nicht steht, wird der Wächter rot. Für jeden anderen `GET` der API gilt unverändert,
dass er nichts schreibt.

**Router: `/api/v1/users`** — Benutzerverwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/users/me` | Eigenes Profil abrufen | Ja |
| PATCH | `/users/me` | Eigenes Profil aktualisieren | Ja |
| GET | `/users/me/providers` | Verknüpfte Auth-Provider auflisten | Ja |
| DELETE | `/users/me/providers/{provider_key}` | Provider-Verknüpfung entfernen — Step-up nach §3.9 (#1847) | Ja |
| POST | `/users/me/password` | Lokales Passwort setzen/ändern; das aktuelle Passwort ist ein Step-up nach §3.9 (gedrosselt, kein API-Key) | Ja |
| POST | `/users/me/step-up/oidc` | Frische Anmeldung beim verknüpften OIDC-Provider zur Bestätigung starten — Regelfall für Konten ohne lokales Passwort (§3.9, #1815) | Ja |
| POST | `/users/me/step-up-code` | Einmaligen Bestätigungscode per E-Mail anfordern — Ausweichweg nur für Konten ohne lokales Passwort und ohne OIDC-fähigen Anbieter; Body `{action}` bindet den Code an die Aktion (§3.9, #1815) | Ja |
| GET | `/users/me/sessions` | Aktive Sessions auflisten | Ja |
| DELETE | `/users/me/sessions/{session_key}` | Einzelne Session beenden | Ja |
| DELETE | `/users/me` | Konto löschen — eröffnet den Art.-17-Löschauftrag wie `POST /privacy/erasure` (REQ-025); Body `{confirm_email, password?}`, Step-up nach §3.9 | Ja |

**Router: `/api/v1/admin/oidc-providers`** — OIDC-Provider-Verwaltung (nur System-Admin):

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/admin/oidc-providers` | Alle konfigurierten Provider auflisten | Plattform-Admin |
| POST | `/admin/oidc-providers` | Neuen OIDC-Provider registrieren — Step-up nach §3.9 (#1883) | Plattform-Admin |
| GET | `/admin/oidc-providers/{slug}` | Provider-Details abrufen | Plattform-Admin |
| PUT | `/admin/oidc-providers/{key}` | Provider aktualisieren — Step-up nach §3.9, außer für `display_name` und `icon_url` (#1883) | Plattform-Admin |
| DELETE | `/admin/oidc-providers/{key}` | Provider löschen — Step-up nach §3.9 (#1883) | Plattform-Admin |
| POST | `/admin/oidc-providers/{slug}/test` | OIDC-Discovery testen; meldet zusätzlich `scope_check`, `provider_type_check`, `jwks_check` und `issuer_check` (#1987) | Plattform-Admin |

**Endpunkte sind `https` (#1987).** `issuer_url`, `authorization_url`, `token_url`, `userinfo_url` und `jwks_url` (optional, pinnt den Schlüsselendpunkt) lehnen `POST`/`PUT` mit `422` ab, wenn sie nicht `https` sind; `http` nur zu Loopback und nur mit `DEBUG=true`. Der Login wendet dieselbe Regel auf bereits gespeicherte Konfigurationen an (siehe Changelog 1.25).

**Geschlossenes Vokabular für `provider_type` (#1497).** `provider_type` ist an der API-Grenze auf `google | github | apple | oidc` beschränkt (Enum `OidcProviderType`); jede andere Schreibweise — auch `GitHub`, `GITHUB` oder `local` — lehnen `POST` und `PUT` mit `422` ab. Der Grund ist die Auswertung: `OAuthEngine.extract_user_info` verzweigt auf die exakte Schreibweise und die Tabelle der Well-known-Endpunkte trägt dieselben Werte als Schlüssel; ein Provider vom Typ `GitHub` wurde also gespeichert und danach **stillschweigend vom generischen OIDC-Zweig bedient** — ohne Well-known-Endpunkte, ohne den GitHub-Adressabruf und ohne jede Meldung. Das Datenmodell oben schrieb dieses `Literal` bereits vor; die Implementierung hatte es zu `str` verbreitert.

Das Domänenmodell `OidcProviderConfig` behält bewusst `str`: das Repository baut dasselbe Modell beim **Lesen**, ein Enum dort machte eine vor dieser Prüfung gespeicherte Konfiguration unlesbar statt reparierbar. `POST /{key}/test` meldet den Befund für Bestandskonfigurationen im Antwortfeld `provider_type_check` (`ok`, `provider_type`, `known_provider_types`, `detail`). Es gibt keine Migration und keine Normalisierung beim Schreiben.

**Scope-Anforderung GitHub (#1477).** Ein Provider mit `provider_type == "github"`, dessen `scopes` weder `user:email` noch den übergeordneten Scope `user` enthalten, wird von `POST` und `PATCH` mit `422` abgelehnt. GitHub liefert das `verified`-Merkmal einer Adresse nur über `GET /user/emails`, das ohne diesen Scope `403` antwortet; ohne ihn ist `email_verified` bei jeder Anmeldung leer und die automatische Kontoverknüpfung (§ REQ-023 OAuth-Callback) bleibt dauerhaft aus. `POST /{slug}/test` meldet denselben Befund für Bestandskonfigurationen im Antwortfeld `scope_check` (`ok`, `provider_type`, `configured_scopes`, `missing_scopes`, `detail`) — unabhängig davon, ob ein Discovery-Dokument abrufbar ist, denn GitHub veröffentlicht keins.

**Gesamtanzahl API-Endpunkte:** ~27

### 3.4 Middleware

**`AuthMiddleware`** — FastAPI Dependency für geschützte Endpunkte:

```python
async def get_current_user(
    authorization: str = Header(None),
    token_engine: TokenEngine = Depends(get_token_engine),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Extrahiert und validiert den Access Token.
    Gibt den vollständigen User zurück.
    Wirft 401 bei fehlendem/ungültigem Token."""

async def get_current_user_optional(
    authorization: str = Header(None),
    token_engine: TokenEngine = Depends(get_token_engine),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Optional[User]:
    """Wie get_current_user, gibt aber None statt 401 bei fehlendem Token.
    Für Endpunkte die sowohl authentifiziert als auch anonym funktionieren."""

def require_role(role: str):
    """Factory für Dependency die eine bestimmte Tenant-Rolle erfordert.
    Wird in REQ-024 vollständig spezifiziert."""
```

### 3.5 Celery-Tasks

| Task | Schedule | Beschreibung |
|------|----------|-------------|
| `cleanup_expired_tokens` | Stündlich | Entfernt abgelaufene/revoked Refresh Tokens |
| `cleanup_unverified_accounts` | Täglich 03:10 | Löscht unbestätigte Accounts älter als 7 Tage; Konten mit `LOCAL`-Anbieterzeile (lokale Registrierung) erst nach Freigabe `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED`, bis dahin nur gezählt (#2010) |
| `rotate_oidc_discovery` | Alle 6 Stunden | Aktualisiert OIDC-Discovery-Dokumente (JWKS, Endpoints); schreibt nur `discovery_document` und `discovery_refreshed_at`, nur solange der Issuer unverändert ist (#1909) |

<!-- Quelle: Issue #1118 -->
### 3.8 Gerätekopplung per QR-Code (#1118)

Eine native App (aktuell nur der Kontrakt, die Flutter-App selbst ist ausgeklammert — siehe §9) meldet sich ohne Passwort-Eingabe an, indem sie einen im Browser erzeugten QR-Code scannt. Der Flow ist vollständig aus der bestehenden REQ-023-Maschinerie zusammengesetzt: er stellt **keine** neue Token-Klasse und **keinen** neuen Claim aus.

**Einmalcode nur in Redis — kein neuer Node, keine neue Collection.**
Der Kopplungscode wird ausschließlich in Redis abgelegt (Store `IDevicePairingCodeStore` / `RedisDevicePairingCodeStore`, TTL-`SET` + pipelined `GET`+`DEL` für atomaren Einmalgebrauch, analog zum OAuth-State-Store). Es gibt **bewusst** keinen ArangoDB-Node und keine neue Collection dafür — die Einlösung ist ein flüchtiger Vorgang, kein zu persistierender Datensatz. Der Rohcode ist nie Redis-Key oder -Value; gespeichert wird `sha256(code)`. Die **Prüfspur** sind strukturierte structlog-Events (`device_pairing_created`, `device_pairing_redeemed`, `device_pairing_redeem_failed`) — genau wie jedes andere Auth-Ereignis in diesem Code, **nicht** ein persistiertes Protokoll (siehe §9 und die Abgrenzung des allgemeinen Audit-Logs).

**TTL-Grenzen.**
Die Lebensdauer des Codes steuert `settings.device_pairing_ttl_seconds` (Default `90`, im Settings-Modell validiert `ge=60, le=120`). Ein Wert außerhalb 60–120 s verweigert den Start, statt still geklemmt zu werden. Unter 60 s läuft der Code ab, bevor der Nutzer scannen kann; über 120 s überlebt er den Moment, in dem der Nutzer auf den Bildschirm sah.

**Rate-Limit und Sperre bei Einlösung.**
Die Einlösung ist rate-limitiert (`settings.rate_limit_device_pairing_redeem`, Default `10/minute`, bewusst unter `rate_limit_auth`). Der slowapi-Limiter zählt dabei — wie an allen Auth-Routen — je aufgelöster Client-Adresse (`resolve_client_ip`), nicht je Proxy. Der eigentliche verhaltensbasierte Schutz ist eine **Sperre pro Quell-IP**: `AuthService.redeem_device_pairing` zählt Fehlversuche je Adresse (`resolve_client_ip`, proxy-bewusst) und entscheidet die Sperre über **denselben** `LoginThrottleEngine`, den auch `login_local` nutzt (kein zweiter Schwellwert). **Reihenfolge:** Die Sperre wird geprüft, **bevor** der Code-Store konsultiert wird — ein gesperrter Versuch verbraucht den Code also nicht. Ein erfolgreicher Versuch leert den Zähler der IP.

**Geltungsbereich der IP-Rate-Limits (#2045).** Alle `@limiter.limit`-Grenzen der Auth-Routen (Login, Registrierung, Passwort-Reset, Einlösung u. a.) zählen in einem **über alle Replikas und Worker-Prozesse geteilten Speicher**: `RATE_LIMIT_STORAGE_URL`, bei leerem Wert der Valkey aus `REDIS_URL`. Erlaubte Schemata sind `redis://`, `rediss://`, `redis+unix://` und `memory://` (gemessen gegen `limits` 5.8: `valkey://` ist dort registriert, braucht aber das nicht ausgelieferte Paket `valkey`; `async+…` liefert dem synchronen Limiter Koroutinen); ein anderer Wert verhindert den Start, ebenso eine URL in `RATE_LIMIT_STORAGE_URL` oder `REDIS_URL`, deren Authority nicht als `[user[:password]@]host[:port]` zerfällt (unkodiertes `/`, `#` oder `?` im Passwort — `urllib` läse das Passwort sonst als Port, und redis-py zitierte es beim Import — oder ein `@` in Pfad, Query oder Fragment; ein `@` im Passwort selbst ist zulässig, `redis://:p@ss@h:6379/0` lädt, weil `urllib` am letzten `@` trennt). Die Meldung nennt nur Variable und erlaubte Form, nie den Wert (Muster #1832); jeder Fehler beim Bau des Speichers wird ohne Wert und ohne `__context__` als `RateLimitStorageConfigError` gemeldet. `memory://` ohne `DEBUG` loggt beim Bau des Limiters einmal `rate_limit_storage_counts_per_process`. Ist der Speicher nicht erreichbar, **degradiert** der Limiter auf eine Zählung je Prozess (kein Fail-open; kein 500 bei Speicherfehlern, d. h. Fehlern aus der Fehlerfamilie des Speichers, bei Redis `RedisError`): Ein Wrapper um den Speicher (`FailoverStorage`, `app/common/rate_limit.py`) beantwortet **jeden** Speicheraufruf, der mit dieser Fehlerfamilie scheitert, aus dem Prozessspeicher — auch Anfragen, die beim Ausfall gerade warten. Ein anderer Fehler gilt als Defekt und wird nicht verschluckt; trifft er eine Prüfanfrage, rückt der Prüfplan trotzdem weiter. Der Fixed-Window-Zähler je Prozess beginnt bei null, wenn der Prozess im laufenden Fenster noch nicht selbst gezählt hat; die Zählungen je Prozess bleiben über die Rückkehr hinaus bis zum Ablauf ihres Fensters stehen, sodass ein flatternder Speicher kein frisches Fenster je Ausfall erzeugt (höchstens eines je Prozess und Fenster). Der Redis-Client hat Socket-Timeouts von 0,5 s und keine Wiederholung: Bei hängendem Speicher wartet die Anfrage, die den Ausfall bemerkt (und jede gleichzeitig wartende), einen Socket-Timeout je Verbindungsversuch und Adresse; Namensauflösung (DNS), mehrere Adressen eines Namens, Verbindungsaufbau plus Handshake und das Nachladen des Skripts nach `NOSCRIPT` sind darin nicht abgedeckt. Danach spricht der Prozess den Speicher nicht mehr je Anfrage an, sondern mit je einer Prüfanfrage in Abständen von 1, 2, 4, 8, 16 und 32 s und danach alle 32 s. Die Rückkehr gilt **je Prozess**: Antwortet der Speicher, zählt dieser Prozess ab seiner Prüfanfrage wieder im geteilten Speicher; jeder andere Prozess erst mit seiner eigenen nächsten Prüfanfrage — bis zu rund 32 s, nachdem der Speicher wieder da ist, und nur, wenn bei ihm Anfragen eintreffen (`rate_limit_storage_unavailable` / `rate_limit_storage_recovered` im Log). Das alles gilt für den Limiter. Die Mail-Budgets (§3.2b, §3.2c, Login-Ablehnung) und der Zähler für unbekannte Adressen nutzen einen eigenen geteilten Client mit denselben Optionen (`_get_throttle_redis_client`, `app/common/dependencies.py`) und seit #2062 mit demselben Prüfplan (`LatchedRedis`, `app/data_access/external/latched_redis.py`): Der erste Speicheraufruf, der einen Ausfall bemerkt, wartet höchstens einen Socket-Timeout (0,5 s) — mit denselben Ausnahmen (DNS, mehrere Adressen, Verbindungsaufbau plus Handshake) —, danach fällt jeder Aufruf des Prozesses sofort auf die In-Process-Stufe zurück, bis eine Prüfanfrage (1, 2, 4, 8, 16, 32 s, danach alle 32 s) wieder eine Antwort bekommt (`throttle_store_unavailable` / `throttle_store_recovered`). Gemessen über die echte Reset-Route gegen einen Socket, der nie antwortet: vorher 1,0 s je Anfrage (zwei Reservierungen seit #2059) für die ganze Dauer des Ausfalls, danach 0,58 s für die erste Anfrage und 0,0 s für die folgenden. Steht `TRUSTED_PROXY_HOPS` auf `0`, obwohl die `X-Forwarded-For`-Kette mehr als einen Eintrag hat, loggt das Backend einmal je Prozess `forwarded_chain_deeper_than_trusted_proxy_hops` (ohne Header-Wert und ohne IP). Zwei Ursachen sind möglich: ein Proxy, den die Einstellung nicht zählt, oder ein Aufrufer, der auf einer Installation ohne Ingress (für die `0` richtig ist) selbst `X-Forwarded-For` sendet. Der `hint` im Log nennt beide und rät, `TRUSTED_PROXY_HOPS` nur zu erhöhen, wenn wirklich mehr Proxys davor stehen — ein zu hoher Wert macht jede IP-basierte Kontrolle fälschbar. Das Helm-Chart setzt `TRUSTED_PROXY_HOPS=1`. **Ein Zähler je Route und Client-Adresse, nie je Pfadwert (#2052).** Der Limiter wird mit `key_style="endpoint"` gebaut (`LIMITER_KEY_STYLE`, `app/common/rate_limit.py`): Der Schlüssel nennt die Routenfunktion, nicht den Anfragepfad. Mit dem slowapi-Default (`"url"`) war auf einer Route mit Pfadparameter jeder vom Aufrufer gewählte Wert ein eigener Zähler — gemessen auf `GET /public/glossary/term/{slug}` (30/min): 31 verschiedene Slugs → 31 × `200` und 31 Speicherschlüssel, `vpd%20` statt `vpd` ebenso; dasselbe galt für `/privacy/export/{export_key}/download` und `/t/{tenant_slug}/notifications/test`. Seitdem teilen sich alle Werte einer Route einen Zähler je Adresse; auch das Budget für Testbenachrichtigungen gilt je Adresse über alle Tenants hinweg (es war schon immer als „je Client-Adresse“ beschrieben). Der Wächter `tests/unit/guards/test_limited_routes_count_per_endpoint.py` misst für jede begrenzte Route der App den Schlüssel zweier Anfragen, die sich nur im Pfad unterscheiden. **Die Prüfung läuft nie auf der Ereignisschleife (#2048).** slowapi prüft auch auf `async def`-Routen synchron im Wrapper; gegen den geteilten Speicher war das ein Netzwerk-Roundtrip auf der Ereignisschleife, hinter dem jede andere Anfrage des Prozesses wartete — gemessen über die echte App: eine unbeteiligte asynchrone Route 0,007 s allein, 0,935 s, während drei begrenzte `POST /public/ai/ask` auf einen Speicher mit 0,3 s Antwortzeit trafen. Der Limiter (`OffLoopLimiter`) führt die Prüfung asynchroner Routen über `run_in_threadpool` aus, wo die Prüfung jeder `def`-Route ohnehin läuft (betroffen: `public_ask`, `download_export`, `send_test_notification`; danach 0,02 s). Gewählt statt die drei Routen auf `def` umzustellen, weil ihre Rümpfe asynchrone Services awaiten und der Wrapper jede künftige asynchrone Route ohne Zutun erfasst. `GET /api/health` zählt in einem eigenen Limiter nur im Prozessspeicher (`process_memory_limiter`): Das Limit bindet dort Last auf interne Dienste (SEC-003), kein replikaübergreifendes Budget, und eine Health-Anfrage soll nie auf Valkey warten (vorher 0,34 s je Anfrage bei 0,3 s Speicher-Antwortzeit). Der Wächter `tests/unit/guards/test_async_limited_routes_check_off_the_loop.py` prüft jede begrenzte asynchrone Route der App, unter welchem Limiter auch immer. **Signale bei Ausfall (#2049, #2062).** Hat der Speicher seit dem Prozessstart nie geantwortet (falsches Passwort oder falscher Host in `REDIS_URL` sehen genau so aus), loggt der erste Fehlschlag `rate_limit_storage_never_reached` auf Fehler-Level statt der Warnung `rate_limit_storage_unavailable`; bleibt er weg, loggt jede zehnte fehlgeschlagene Prüfanfrage `rate_limit_storage_still_unavailable` (im Dauerzustand etwa alle fünf Minuten, mit `down_for_s` und `never_answered`). Die Readiness bleibt bewusst unberührt. **Client-Adresse ist eine IP (#2053, #2062).** `resolve_client_ip` gibt den gewählten `X-Forwarded-For`-Eintrag nur zurück, wenn er eine IP-Adresse ist, und dann in kanonischer Form; sonst `None` („nicht ermittelbar“: die Allowlist lehnt ab, das IP-Limit zählt unter dem Gegenüber, Kopplungssperre und Reset-Budget in einem gemeinsamen `unknown`-Topf) — nicht das Gegenüber selbst, das einer unserer Proxys sein kann und so in einer Allowlist mit Cluster-Bereichen landete (Bündel-Prüfung). Vorher wurde jeder Text zum Schlüssel aller IP-gebundenen Kontrollen (gemessen: `not-an-ip` und 200 × `x` je ein eigener Zähler, `2001:DB8::1` und `2001:db8:0:0::1` zwei). Der Chart-Wächter verlangt `TRUSTED_PROXY_HOPS` jetzt genau `1`, nicht nur ≥ 1: ein zu hoher Wert liest einen Eintrag, den der Aufrufer geschrieben hat. **Valkey ohne AUTH:** Die Integrität der `LIMITS:*`- und Budget-Schlüssel ruht auf der NetworkPolicy des Charts (Ingress auf 6379 nur von `backend`, `celery-worker`, `celery-beat`); bewusst so akzeptiert, kein eigenes Passwort und keine eigene DB in diesem Schritt.

**Einlösung liefert das bestehende Token-Paar.**
`redeem_device_pairing` ruft dieselbe Fabrik `_create_tokens` wie `login_local` und `complete_oauth` — dasselbe Access-/Refresh-Paar, dieselbe `RefreshToken`-Session (in der Sessions-Liste sichtbar und dort widerrufbar), keine neue Token-Art. Das Konto stammt aus dem gespeicherten Code-Record, nie aus einer vom Aufrufer gelieferten Identität. Unbekannter, benutzter, abgelaufener und unlesbarer Code liefern **eine** generische 401 (kein Orakel); ein deaktiviertes Konto 401; eine gesperrte IP 423 mit Restminuten.

**Autorisierung pro Request, nicht im Token eingefroren.**
Das Access Token trägt — wie bei jedem Login — nur die zum Ausstellungszeitpunkt aufgelösten Tenant-Rollen; die tatsächliche Zugriffsentscheidung fällt pro Request aus der Mitgliedschaft (`get_current_tenant`, REQ-024). Ein gekoppeltes Gerät verliert den Zugriff auf einen Tenant daher **sofort**, sobald die Mitgliedschaft entzogen wird — die Kopplung schafft keinen von der Mitgliedschaft entkoppelten Dauerzugriff.

**Body-getragener Refresh für native Clients.**
Ein per QR gekoppeltes Gerät hält den Rohwert des Refresh-Tokens im Plattform-Keystore und hat weder Cookie-Jar noch `csrf_token`-Cookie. Damit das ausgestellte Paar überhaupt rotierbar ist, akzeptiert `POST /auth/refresh` seit v1.12 einen **optionalen** JSON-Body `{"refresh_token": "…"}`:

- Ist ein Body-Token vorhanden, **schlägt der Body den Cookie** (kein „erst Body, dann Cookie"-Fallback — der wäre die eigentliche Lücke). Der Cookie wird vollständig ignoriert, es wird **kein** `kp_refresh`-Cookie gesetzt, und der rotierte Token kommt im Body zurück (`TokenPairResponse`).
- Auf dem Body-Pfad wird `verify_csrf` **nicht** aufgerufen: Ein Body-Token ist kein ambient übertragenes Credential, daher greift die Double-Submit-Abwehr nicht (siehe präzisierte CSRF-Tabelle in §1). Ein ungültiger Body-Token liefert 401, **ohne** den Cookie zu verbrauchen.
- Der **Cookie-Pfad bleibt byte-identisch**: fehlender Cookie → 401 vor jeder CSRF-Prüfung; vorhandener Cookie → `verify_csrf` wie bisher, Rotation als Cookie.

Die Ausgabe-Endpunkte:

- `POST /auth/device-pairing` — **Bearer-authentifiziert** (`get_current_user`, kein CSRF, wie `create_api_key`), liefert `{payload_version, server_url, code, expires_at, expires_in}`. `server_url` stammt aus `settings.app_base_url` (der QR-SSOT aus REQ-032), nie aus `request.base_url` (hinter Traefik cluster-intern und für das scannende Telefon unerreichbar). QR-Nutzlast: `{"v": payload_version, "url": server_url, "code": code}`.
- `POST /auth/device-pairing/redeem` — **öffentlich** (`security: []` in der generierten OpenAPI, damit der ZAP-Auth-Bypass-Check korrekt einordnet), liefert `{access_token, token_type, expires_in, refresh_token}` und setzt **keinen** Cookie.

Beide Endpunkte hängen am `auth_router` (nicht am `api_keys_router`) und sind daher im Light-Modus (REQ-027) nicht gemountet — eine Light-Instanz antwortet auf beide mit **404**.
<!-- /Quelle: Issue #1118 -->

### 3.9 Step-up-Re-Authentifizierung für unumkehrbare Kontoaktionen und Anmeldemittel (#1813, #1814, #1816, #1847, #1857, #1883, #1884)

Unumkehrbare Kontoaktionen verlangen eine erneute Bestätigung durch die handelnde Person. Alle laufen durch **eine** Prüfung (`StepUpVerifier`, `app/domain/services/step_up_service.py`), die im Service erzwungen wird — die Einstiegspunkte nehmen den Step-up als Keyword-Argumente ohne Default, sodass eine neue Route ihn nicht vergessen kann.

| Aktion | Route(n) | Zurückgetipptes Ziel | Passwort / Erneute Anmeldung / Code |
|---|---|---|---|
| Eigenes Konto löschen (Art. 17, Karenz) | `DELETE /users/me`, `POST /privacy/erasure` | eigene E-Mail (`confirm_email`) | eigenes Passwort; ohne lokales Passwort ein `step_up_token` aus `POST /users/me/step-up/oidc`, nur bei ausschließlich GitHub/Apple der per E-Mail zugeschickte Einmalcode |
| Anderes Konto sofort löschen (Plattform-Admin) | `DELETE /admin/platform/users/{key}` | E-Mail des Zielkontos | das des **Admins**; ohne dessen lokales Passwort dessen `step_up_token` bzw. Code |
| Mandant löschen (REQ-024 AK-44d) | `DELETE /tenants/{slug}`, `DELETE /admin/platform/tenants/{key}` | Slug (`confirm_slug`) | eigenes Passwort; sonst `step_up_token` bzw. Code |
| E-Mail-Adresse ändern (REQ-025 Art. 16, #1841) | `POST /privacy/email-change` | — (kein Ziel; nur die eigene Sitzung wird bestätigt) | eigenes Passwort; sonst `step_up_token` bzw. Code |
| Passwort ändern / erstmals setzen | `POST /users/me/password` | — | aktuelles Passwort; die **erste** Passwortvergabe eines Kontos ohne eines bestätigt stattdessen mit `step_up_token` bzw. Code |
| API-Key ausstellen (#1847) | `POST /auth/api-keys` | — | eigenes Passwort; sonst `step_up_token` bzw. Code. **Light-Modus:** kein Step-up (siehe unten) |
| Gerät per QR-Code koppeln (#1847) | `POST /auth/device-pairing` | — | eigenes Passwort; sonst `step_up_token` bzw. Code |
| Anmeldeweg (Provider-Verknüpfung) entfernen (#1847) | `DELETE /users/me/providers/{provider_key}` | — | eigenes Passwort; sonst `step_up_token` bzw. Code |
| Vertrauen eines anderen Kontos anheben (Plattform-Admin, #1857) | `PATCH /admin/platform/users/{key}`, nur wenn `email_verified` oder `is_active` von false auf true wechselt | — | das des **Admins**; sonst dessen `step_up_token` bzw. Code |
| OIDC-Provider-Konfiguration anlegen, ändern, löschen (Plattform-Admin, #1883) | `POST /admin/oidc-providers`, `PUT`/`DELETE /admin/oidc-providers/{key}`; beim `PUT` nicht, wenn nur `display_name` oder `icon_url` geändert werden | — | das des **Admins**; sonst dessen `step_up_token` bzw. Code |
| Mandanten deaktivieren oder reaktivieren (Plattform-Admin, #2009, REQ-024 AK-56) | `PATCH /admin/platform/tenants/{key}`, nur wenn `is_active` wechselt | — | das des **Admins**; sonst dessen `step_up_token` bzw. Code |
| Mitglied aus einem Mandanten entfernen (Plattform-Admin, #2009) | `DELETE /admin/platform/tenants/{tenant_key}/members/{membership_key}`, `DELETE /admin/platform/users/{user_key}/memberships/{membership_key}` | — | das des **Admins**; sonst dessen `step_up_token` bzw. Code |
| Rolle eines Mitglieds ändern (Plattform-Admin, #2032, REQ-024 AK-57) | `PATCH /admin/platform/tenants/{tenant_key}/members/{membership_key}/role`, `PATCH /admin/platform/users/{user_key}/memberships/{membership_key}/role`; nur bei tatsächlicher Änderung | — | das des **Admins**; sonst dessen `step_up_token` bzw. Code |
| Rolle eines Mitglieds ändern oder Mitglied entfernen (Mandanten-Verwalter, #2032) | `PATCH /tenants/{slug}/members/{membership_key}/role` (nur bei tatsächlicher Änderung), `DELETE /tenants/{slug}/members/{membership_key}` | — | das des **handelnden** Kontos (`management` im Mandanten); sonst dessen `step_up_token` bzw. Code |

**Anmeldemittel ausstellen und entfernen (#1847).** Ein API-Key überlebt Passwortänderung und „überall abmelden"; ein Kopplungscode wird zu einer vollen Sitzung; das Entfernen eines Anmeldewegs ändert, wie das Konto zurückgeholt werden kann. Bis #1847 genügte für alle drei die bloße Sitzung — auch eine, die mit einem `kp_`-Key authentifiziert war: Ein gestohlener Key konnte weitere Keys ausstellen, eine gestohlene Sitzung einen Key hinterlassen, der die Passwortänderung der Eigentümerin überdauert. Sie laufen deshalb durch denselben Step-up wie die Passwortänderung. Im **Light-Modus** (REQ-027) stellt `POST /auth/api-keys` den MCP-Key ohne Step-up aus: Jede Anfrage ist dort ohnehin das eine Systemkonto, es gibt keinen Menschen zu bestätigen und kein Postfach für einen Code, und der Key gewährt nichts, was eine Anfrage nicht schon hat (REQ-033 §4.3). Gerätekopplung und Provider-Trennung existieren im Light-Modus nicht.

**Keine automatische Widerrufung von API-Keys — umgesetzter Standard, offene Betreiber-Entscheidung (#1847, Fragenliste in #1650).** Passwortänderung, Passwort-Reset und „überall abmelden" widerrufen die Refresh-Token, **nicht** die API-Keys des Kontos. Der Betreiber hat noch nicht entschieden, ob das so bleibt; bis dahin gilt dieser Standard mit der folgenden Begründung. Ein Key steht für eine bewusst eingerichtete Maschinen-Integration (Home Assistant, MCP-Client); ihn bei jeder Passwortänderung stillschweigend zu entwerten, würde diese Integrationen ohne Hinweis brechen. Seit #1847 kann ein Key nur noch hinter dem Step-up entstehen, also nicht mehr aus einer bloß gestohlenen Sitzung oder aus einem anderen Key. Die Keys sind unter „API-Keys" mit Erstellungs- und letztem Nutzungszeitpunkt gelistet und einzeln widerrufbar. Restrisiko: Ein Key, den ein Angreifer mit Kenntnis des Passworts (oder vor #1847) ausgestellt hat, bleibt bis zum manuellen Widerruf gültig.

**Vertrauensanhebung durch Plattform-Admins (#1857).** `email_verified` ist der Vertrauensanker der OAuth-Auto-Verknüpfung (`OAuthEngine.should_auto_link`). Eine gekaperte Admin-Sitzung konnte ein vorab registriertes Angreiferkonto unter der Adresse eines Opfers als verifiziert markieren; die nächste föderierte Anmeldung des Opfers mit dieser Adresse landete dann im Angreiferkonto. Wechselt `email_verified` oder `is_active` von false auf true, verlangt `PATCH /admin/platform/users/{key}` deshalb den Step-up des **Admins**. Die Step-up-Felder werden nie in das Konto geschrieben. Namensänderung, Deaktivierung und das erneute Senden unveränderter Werte (das Bearbeitungsformular schickt alle Felder) bleiben ohne Step-up.

**Reihenfolge der Prüfung:**

1. **Wer:** nur die angemeldete Sitzung eines Menschen. Ein Service Account oder eine Anfrage mit `kp_`-API-Key — auch einem, den ein menschliches Konto ausgestellt hat — wird mit 403 abgewiesen, **bevor** etwas gezählt wird.
2. **Sperre:** ist der Step-up gesperrt, antwortet die Route 429 `STEP_UP_LOCKED` (`details[0].retry_after_minutes`), ohne das Geheimnis zu prüfen.
3. **Ziel:** wo eine Aktion eines zurücktippt, muss es passen (E-Mail ohne Groß-/Kleinschreibung, Slug exakt) — sonst 422. Ein falsches Echo wird **nicht** gezählt; es prüft kein Geheimnis. Passwortänderung und E-Mail-Änderung haben kein Ziel zum Zurücktippen.
4. **Geheimnis:** bei einem Konto mit lokalem Passwort das aktuelle — sonst 401. Ohne lokales Passwort prüft `verify()` zuerst, ob der Body ein `reauth_token` (`step_up_token`) trägt — dann zählt nur dieses, unabhängig davon, ob ein Code mitgeschickt wurde. Fehlt es: Hat das Konto einen OIDC-fähigen verknüpften Anbieter (§ unten), verweigert die Route mit 401 `STEP_UP_REAUTH_REQUIRED` — ein Code wird für ein solches Konto nicht mehr geprüft. Sonst (ausschließlich GitHub/Apple) prüft sie den Einmalcode aus `POST /users/me/step-up-code`; fehlt der, 401 `STEP_UP_CODE_REQUIRED`. Ein falsches Geheimnis jeder Art zählt in dasselbe Budget.

**Frische Anmeldung beim Provider statt Echo (#1815, Betreiber-Entscheid: Variante 1).** Bis dahin bestätigte ein ausschließlich föderiertes Konto jede der obigen Aktionen mit dem zurückgetippten Ziel allein — dem Echo —, und die erste Passwortvergabe eines solchen Kontos bestätigte gar nichts. Das Echo prüft kein Geheimnis: Wer die Sitzung hält, liest die eigene E-Mail-Adresse ohnehin vom Profil ab. Ein Konto ohne lokales Passwort, dessen verknüpfter Anbieter das kann, bestätigt seitdem mit einer **frischen** Anmeldung genau bei diesem Anbieter — dem stärksten verfügbaren Nachweis, stärker als ein Einmalcode, der nur die Mailbox belegt.

**Anbietergrenze.** Nur OpenID-Connect-Anbieter können belegen, *wann* sich die Person angemeldet hat: Google und ein generischer OIDC-Provider mit dem `openid`-Scope (`supports_fresh_reauth`, `app/domain/engines/oauth_engine.py`). **GitHub** ist reines OAuth2 und stellt kein ID-Token aus — also auch kein `auth_time`. **Apple** stellt ein ID-Token aus, aber ohne `auth_time`. Ein Konto, dessen verknüpfte Anmeldewege ausschließlich aus GitHub und/oder Apple bestehen, behält deshalb den per E-Mail zugeschickten Code als **Ausweichweg** (`EMAIL_CODE_FALLBACK = True`); ein Konto mit mindestens einem OIDC-fähigen Anbieter wird der Code verweigert (`STEP_UP_REAUTH_REQUIRED`) — der Code belegt nur die Mailbox, die frische Anmeldung mehr. Variante 2 (gar kein Code) hätte GitHub/Apple-only-Konten ihr Art.-17-Löschrecht in Selbstbedienung genommen; der Unterschied zu Variante 1 ist die eine Flagge `EMAIL_CODE_FALLBACK`.

**`POST /users/me/step-up/oidc` (#1815).** Startet die frische Anmeldung: Body `{"action": "...", "provider_key": "..."}` (`provider_key` optional — ohne ihn der erste verknüpfte Anbieter, der es kann), Antwort `{"authorization_url": "..."}`. Die Anfrage an den Provider ist dieselbe wie beim Login (PKCE, State, Nonce, dieselbe Rückruf-URL), zusätzlich `prompt=login` und `max_age=0`: Der Provider muss die Person erneut anmelden statt aus eigener Sitzung zu antworten, und den Anmeldezeitpunkt (`auth_time`) zurückmelden. Der bestehende Callback (`/api/v1/auth/oauth/{slug}/callback`) meldet dabei niemanden an, sondern leitet auf `{frontend}/auth/step-up/callback` weiter — bei Erfolg mit `#step_up_token=…&action=…` im URL-**Fragment** (nie in der Query: erreicht keinen Server, keinen Proxy, keinen `Referer`-Header), bei Fehler mit `?error=step_up_failed` (allgemein), `?error=step_up_stale` (Anmeldung älter als fünf Minuten) oder `?error=step_up_cancelled` (am Provider abgebrochen).

**Prüfung des ID-Tokens (`validate_fresh_reauth_claims`).** `iss` ist der erwartete Aussteller, `aud`/`azp` diese Instanz, `nonce` stimmt mit der Anfrage überein, `exp` ist nicht abgelaufen (`FRESH_REAUTH_CLOCK_SKEW_SECONDS` = 30 s Toleranz), `auth_time` ist vorhanden und höchstens `FRESH_REAUTH_MAX_AGE_SECONDS` = 300 s alt (dieselbe Toleranz) — älter ist `reason="stale"` (die Person kann es erneut versuchen). Zusätzlich prüft der Service, dass `sub` zu einer verknüpften Anmeldung **dieses** Kontos bei diesem Anbieter gehört (`complete_step_up_reauth`) und das Konto noch ein aktiver Mensch ist.

**Keine JWKS-Signaturprüfung.** Das ID-Token kommt direkt vom Token-Endpunkt des Providers über TLS, in einem Austausch, den dieser Server mit seinem eigenen Client-Secret und dem PKCE-Verifier authentifiziert hat — genau der Fall, für den OIDC Core 1.0 §3.1.3.7 Nr. 6 die TLS-Serverauthentifizierung als Ersatz für die Signaturprüfung vorsieht. Ein zusätzlicher JWKS-Abruf und -Cache je Provider würde gegen einen Angreifer, der nicht in dieser TLS-Sitzung sitzt, keinen Gewinn bringen. Deshalb gilt ein Provider nur mit einem `https`-Token-Endpunkt als re-authentifizierbar (`supports_fresh_reauth`, zusätzlich vor dem Tausch geprüft); `auth_time` und `exp` müssen endliche Zahlen sein (kein `NaN`/`Infinity`, kein Boolean).

**Kein `nbf`, keine `iat`-Grenze (Entscheidung zu #2008).** Anders als der Login (v1.25, #1987) liest der Step-up `nbf` und `iat` nicht. Gemessen: `validate_fresh_reauth_claims` prüft `iss`, `aud`/`azp`, `nonce`, `exp` und `auth_time`, keine Signatur. Eine `iat`-Untergrenze würde ein lange gehaltenes oder wiederverwendetes Token abweisen — das leistet hier schon die `nonce`: Sie wird je `POST /users/me/step-up/oidc` neu erzeugt, ihr State ist einmalig verwendbar und lebt fünf Minuten, ein früher ausgestelltes Token kann sie nicht tragen; und `auth_time` begrenzt die Anmeldung selbst auf 300 s (+ 30 s Toleranz). `nbf` gehört nicht zu den ID-Token-Prüfungen von OIDC Core 3.1.3.7; da die Claims ohne Signatur nur über die TLS-Sitzung zum Token-Endpunkt vertraut werden, kann ein `nbf` ohnehin nur vom Provider selbst stammen. Beide Prüfungen würden gegen keinen Angreifer etwas hinzufügen, der nicht in dieser TLS-Sitzung sitzt — gegen einen, der es tut, hilft keine Claim-Prüfung ohne Signatur. Der Token-Endpunkt selbst wird vor dem Austausch adressgeprüft (v1.27, #2007).

**Bindung an Konfiguration, Aussteller und Tab (Security-Review des Bundles).** `sub` ist nur je Aussteller eindeutig. Eine Anbieter-Verknüpfung speichert deshalb die Konfiguration (`oidc_config_slug`) und den Aussteller (`issuer`), über die sie entstand; die frische Anmeldung geht an genau diese Konfiguration, und `iss` muss zum gespeicherten Aussteller passen. Eine ältere Verknüpfung ohne diese Angaben ist seit v1.21 nicht re-authentifizierbar (Migration v0064 hat die eindeutigen gebunden) — ihr steht der E-Mail-Code offen, damit kein Konto ausgesperrt wird. Die Rückruf-URL wird — bei Login und erneuter Anmeldung — aus `APP_BASE_URL` gebildet, nie aus dem Host-Header. Der Client kann ein `client_nonce` (32 Hex-Zeichen) mitgeben, das unverändert neben Token bzw. Fehler zurückkommt; die Callback-Seite übernimmt nur ein Ergebnis mit dem eigenen Nonce. Ein Verifier ohne Re-Authentifizierungs-Richtlinie verweigert Code und Token (fail closed). Unterscheidbare 422-Codes: `STEP_UP_PASSWORD_REQUIRED` (Konto hat ein Passwort), `STEP_UP_REAUTH_UNAVAILABLE` (kein fähiger Anbieter → E-Mail-Code), `STEP_UP_REAUTH_REQUIRED` (beim Code-Abruf: Re-Authentifizierung nehmen). Der Login-Pfad ordnet Verknüpfungen seit v1.21 ebenfalls über (Konfiguration, `sub`) zu und tauscht den Code mit der `redirect_uri` des Autorisierungs-Requests (#1865, #1869). Anders als der Step-up verifiziert der Login das ID-Token vollständig, einschließlich der Signatur gegen die JWKS des Anbieters, und vergleicht `sub` aus Userinfo und ID-Token (v1.23, #1936).

Der zurückgegebene `step_up_token` (32 Zufallsbytes, nur als HMAC unter demselben `JWT_SECRET_KEY`-abgeleiteten, aber zweckgetrennten Schlüssel gespeichert — `kp-step-up-reauth` statt `kp-step-up-code`) ist `REAUTH_TOKEN_TTL_SECONDS` = 5 Minuten gültig, an Konto, Aktion **und** — bei den zielgebundenen Aktionen — Ziel gebunden, wird durch die erste Aktion verbraucht, die ihn vorlegt, und ersetzt einen noch gültigen Token bei erneuter Anfrage. Er geht als `step_up_token` in den Step-up-Body der Aktion (Tabelle oben) — Nachweis-Methode `oidc_reauth`.

Verweigert (Start): 403 einer API-Key-Anfrage, einem Dienstkonto oder im Light-Modus; 422 einem Konto mit lokalem Passwort, einem Konto ohne (bzw. ohne den über `provider_key` gewählten) OIDC-fähigen verknüpften Anbieter — es bestätigt dann mit dem Code —, oder bei fehlendem/unbekanntem `action`; 429 `STEP_UP_LOCKED` bei gesperrtem Step-up. Verweigert (Abschluss/Callback): kein JSON-Fehler, sondern einer der drei Redirect-Fehlercodes oben; die Prüfung selbst schreibt nichts.

**Betreiber-Voraussetzung.** Der verknüpfte Identity-Provider muss `prompt=login`/`max_age` und den Claim `auth_time` unterstützen. Die beim Provider hinterlegte Rückruf-URL ist dieselbe wie beim normalen Login, keine zusätzliche Konfiguration nötig.

**`POST /users/me/step-up-code` (#1815, Ausweichweg für GitHub/Apple, gehärtet im Security-Review des Bundles).** Verschickt einen achtstelligen Code an die eigene E-Mail-Adresse (202, Antwort `{expires_at, expires_in}` — nie der Code selbst). Der Body ist Pflicht: `{"action": "..."}` mit einem der Werte aus der Tabelle oben (`account_erasure`, `admin_account_erasure`, `tenant_deletion`, `email_change`, `password_change`, `api_key_creation`, `device_pairing`, `provider_unlink`, `admin_account_update`, `oidc_provider_change`, `admin_tenant_update`, `admin_membership_removal`, `admin_membership_role_change`, `tenant_member_removal`, `tenant_member_role_change`) — fehlt `action` oder ist er unbekannt, antwortet die Route 422. Für die zielgebundenen Aktionen (nächster Absatz) gehört `target` dazu. Die Mail nennt die Aktion in Klartext (`CODE_PURPOSES`, feste englische Texte, nie Nutzereingabe).

**Aktionsbindung (review SEC-003).** Der Digest bindet Kontoschlüssel **und** Aktion: `HMAC(Schlüssel, "Kontoschlüssel:Aktion:Ziel:Code")`. Ein für `password_change` angeforderter Code lehnt `verify()` für `account_erasure` ab, ohne ihn zu verbrauchen — er passt einfach auf nichts.

**Zielbindung (#1884).** Eine Aktion auf etwas anderes als das eigene Konto bindet Code und `step_up_token` zusätzlich an ihr Ziel — den Schlüssel, den die Aktion im Pfad nennt:

| Aktion | Ziel (`target`) |
|---|---|
| `admin_account_update`, `admin_account_erasure` | Schlüssel des anderen Kontos |
| `tenant_deletion` | Schlüssel des Mandanten |
| `provider_unlink` | Schlüssel der Provider-Verknüpfung (`GET /users/me/providers`) |
| `oidc_provider_change` | Schlüssel der OIDC-Konfiguration; beim Anlegen `new:<slug>` |
| `admin_tenant_update` | Schlüssel des Mandanten |
| `admin_membership_removal`, `admin_membership_role_change`, `tenant_member_removal`, `tenant_member_role_change` | Schlüssel der Mitgliedschaft |
| `admin_membership_add` | Mandant und Konto, getrennt durch `\|`: `<tenant_key>\|<user_key>` (#2106) |

Ein für Konto A angeforderter Code bestätigt die Aktion für Konto B nicht und wird durch den Fehlversuch nicht verbraucht. Das Ziel wird im Digest längenpräfixiert (`new:<slug>` enthält den Trenner). Die übrigen Aktionen wirken auf das eigene Konto, das der Digest schon bindet; sie nennen kein Ziel. `POST /users/me/step-up-code` und `POST /users/me/step-up/oidc` verlangen `target` für die zielgebundenen Aktionen (422 ohne; 422 auch für ein Ziel bei einer Aktion auf das eigene Konto) und prüfen es **bei der Ausgabe** (Betreiber-Entscheid D2): das Ziel muss existieren und die anfragende Person muss darauf handeln dürfen — Plattform-Admin (für beide Kontoaktionen und `oidc_provider_change`), `lead` + `management` im Mandanten oder Plattform-Admin (`tenant_deletion`; ein durch einen abgebrochenen Lauf bereits entfernter Mandant mit offenem Löschauftrag zählt), eigene Verknüpfung (`provider_unlink`), Plattform-Admin (`admin_tenant_update`, `admin_membership_removal`, `admin_membership_role_change`; für `admin_tenant_update` nicht auf den Plattform-Mandanten), `management` im Mandanten der Mitgliedschaft (`tenant_member_removal`, `tenant_member_role_change`, #2032 — eine unbekannte und eine fremde Mitgliedschaft sind dieselbe Antwort, 403). Die Berechtigung wird vor der Existenz geprüft (403 vor 404), damit die Ablehnung nichts über vorhandene Ziele verrät. Die Mail nennt das Ziel nicht (Betreiber-Entscheid D4). Die Aktion selbst prüft Berechtigung und Ziel beim Ausführen erneut; die Prüfung bei der Ausgabe ist das frühere von zwei Toren. Ein vor diesem Stand begonnener Reauth-Lauf ohne Ziel im State endet mit `step_up_failed`, statt einen ungebundenen Token auszustellen.

**OIDC-Provider-Konfiguration (#1883).** Eine Provider-Konfiguration entscheidet, wem eine föderierte Anmeldung zugeordnet wird: Ein Provider unter Kontrolle eines Angreifers kann `email=<Opfer>` mit `email_verified=true` behaupten, und der Auto-Link verknüpft die Anmeldung mit dem Konto des Opfers. Anlegen, Ändern und Löschen laufen deshalb durch denselben Step-up wie eine Anmeldemittel-Änderung (Betreiber-Entscheid D5), geprüft in `OidcProviderAdminService`, nicht im Router; ein API-Key eines Admins ist 403. Ohne Step-up bleiben nur Felder, die die Darstellung ändern — `display_name`, `icon_url` (Betreiber-Entscheid D6, Positivliste: ein neues Feld verlangt den Step-up, bis es bewusst freigegeben wird). Auch `enabled` verlangt ihn in **beide** Richtungen (Korrektur von D6 nach Security-Review SEC-001): `FederatedReauthPolicy` liest nur aktive Konfigurationen, ein Abschalten ohne Step-up würde daher jedes Konto, dessen einzige re-authentifizierbare Verknüpfung dieser Provider ist, von der frischen Anmeldung auf den E-Mail-Code herabstufen — erreichbar mit einer gekaperten Admin-Sitzung oder einem Admin-API-Key. Ein unverändert mitgesendeter Wert gilt nicht als Änderung. Bekannter Randfall: Ein Admin, dessen einzige Anmeldung eine Verknüpfung mit genau dem Provider ist, der gerade repariert werden soll, kann sich dort nicht frisch anmelden und bekommt keinen Code (ein Konto mit OIDC-fähiger Verknüpfung wird auf die erneute Anmeldung verwiesen); ein lokales Passwort oder der Betreiber helfen dann.

**Schlüsselwahl.** Der HMAC-Schlüssel ist von `JWT_SECRET_KEY` abgeleitet (`HMAC(JWT_SECRET_KEY, "kp-step-up-code")`), nicht `ERASURE_TOMBSTONE_SALT` (kann leer sein, zweckgebunden für Pseudonymisierung) und kein neues Pflicht-Secret. Ein bloßer `sha256(Konto:Code)` über nur 10⁸ mögliche Codes wäre aus einem Valkey-Dump offline in Sekunden umkehrbar, solange der Code lebt. Eine Rotation von `JWT_SECRET_KEY` entwertet ausstehende Codes und Reauth-Token gleichermaßen (höchstens zehn bzw. fünf Minuten Bestand).

**Ausgabegrenzen (review SEC-002).** Gültig `CODE_TTL_SECONDS` = 10 Minuten, verbraucht durch die erste Aktion, die ihn vorlegt. Ein neuer Aufruf ersetzt einen noch gültigen Code — außer: ein **noch nicht verbrauchter** Code jünger als `CODE_COOLDOWN_SECONDS` = 60 Sekunden wird nicht ersetzt (sonst würde eine parallele Anfrage den Code entwerten, den die Person gerade eintippt), und höchstens `CODE_ISSUES_PER_WINDOW` = 5 Codes pro Konto und `CODE_ISSUE_WINDOW_SECONDS` = 3600 Sekunden werden ausgegeben. Beide Grenzen antworten 429 `STEP_UP_LOCKED` mit `details[0].retry_after_minutes` — dieselbe Fehlerform wie eine Verify-Sperre, mit eigenem `message`-Text, damit ein Client nicht zwei Fälle unterscheiden muss.

Verweigert: 403 einer API-Key-Anfrage, einem Dienstkonto oder im Light-Modus (`refuse_in_light_mode`-Dependency, #1844: das einzige Konto der Instanz hat kein Passwort, ein dort gesetztes würde nach dem Wechsel in den Full-Modus zur gültigen Anmeldung); 422 einem Konto mit lokalem Passwort (es bestätigt damit, nicht mit einem Code), bei fehlendem/unbekanntem `action`, **oder wenn das Konto einen OIDC-fähigen verknüpften Anbieter hat** (`STEP_UP_REAUTH_REQUIRED`, siehe oben — es bestätigt dann mit der frischen Anmeldung); 429 `STEP_UP_LOCKED` bei gesperrtem Step-up oder ausgeschöpfter Ausgabegrenze. Zusätzlich rate-limitiert wie die übrigen Auth-Routen (`settings.rate_limit_auth`, ein zweiter, adressbezogener Zähler ohne `STEP_UP_LOCKED`-Hülle).

**Unzustellbarer Code (/code-review of #1862).** Scheitert der Versand — der Konsolen-Adapter außerhalb von `debug` liefert bewusst nicht aus, oder der SMTP-Versand meldet einen Fehler —, antwortet die Route 503 `STEP_UP_CODE_UNDELIVERABLE`, statt 202 zu melden und den Code verschwinden zu lassen. `StepUpVerifier.withdraw_code` nimmt den Code dabei zurück: Der Eintrag im Code-Store wird gelöscht, die 60-Sekunden-Sperre aufgehoben und der Platz im Stundenkontingent zurückgegeben — ein erneuter Versuch nach der Behebung durch den Betreiber wartet also nicht auf `CODE_COOLDOWN_SECONDS` oder das nächste Zeitfenster. Die Redis-Reservierung selbst läuft als ein einziger `SET NX`-Schritt, damit zwei gleichzeitige Anfragen nicht beide "kein Warten nötig" lesen und beide einen Code ausgeben.

**Betriebsvoraussetzung.** Ein Konto mit OIDC-fähigem Anbieter braucht dessen `prompt=login`/`max_age`/`auth_time`-Unterstützung (siehe oben), keinen Mail-Versand. Nur ein Konto, dessen verknüpfte Anbieter ausschließlich GitHub und/oder Apple sind, braucht für den Ausweichweg funktionierenden Mail-Versand (`EMAIL_ADAPTER=smtp`). Läuft die Instanz mit dem Konsolen-Adapter und `DEBUG=false` (die produktive Voreinstellung ohne SMTP-Konfiguration), meldet die Route das explizit (503 `STEP_UP_CODE_UNDELIVERABLE`, siehe oben) — ein solches Konto kann sich bis zur Behebung trotzdem nicht löschen, kein erstes lokales Passwort setzen, keinen Mandanten löschen und die E-Mail-Adresse nicht ändern.

**Drosselung.** Jeder Bestätigungsversuch (Passwort, Code oder eine vorgelegte, aber ungültige/abgelaufene Reauth-Token) wird **vor** seiner Prüfung atomar reserviert (Valkey `INCR`, In-Process-Fallback bei Ausfall — nie fail-open). Zwei Zähler, beide über denselben `LoginThrottleEngine` wie der Login (ab 5 Fehlversuchen 15 Minuten, verdoppelnd bis 4 Stunden):

- je **(Konto, Client-Adresse)** mit der Login-Schwelle 5;
- je **Konto** mit der Obergrenze 15 (drei Adress-Budgets) gegen Adress-Rotation.

Nach Ablauf einer Sperre wird genau ein weiterer Versuch geprüft; schlägt er fehl, sperrt er sofort wieder mit doppelter Dauer (wie beim Login). Anfragen, die gleichzeitig über das Budget hinaus reserviert haben, werden ohne Prüfung abgewiesen; Sperre, Zählung der Sperren und Rücksetzen des Zählers geschehen in einem Schritt (eine Valkey-Transaktion). Die Zähler gelten für alle Step-up-Aktionen eines Kontos gemeinsam (kein Budget je Route) — das Anfordern und das Vorlegen eines Codes oder einer erneuten Anmeldung eingeschlossen. Ein erfolgreicher Step-up leert beide. Im Light-Modus wird keine Kontolöschung per Anfrage angenommen (403) — dort ist jede Anfrage das eine Systemkonto.

**Warum nicht die Login-Sperre.** Einen Step-up-Fehlversuch für ein Konto kann nur erzeugen, wer eine Sitzung dieses Kontos hält — geprüft wird immer das Geheimnis der handelnden Person, API-Keys werden vor dem Zählen abgewiesen. Ein Außenstehender kann ein Opfer über diesen Weg also nicht sperren. Flössen die Fehlversuche in `failed_login_attempts`, könnte aber ein Sitzungsdieb die Eigentümerin von der **Anmeldung** aussperren — genau dem Schritt, mit dem sie die gestohlene Sitzung sieht und widerruft. Umgekehrt würde das Lesen der Login-Sperre einem nicht angemeldeten Angreifer (der jede bekannte Adresse am Login sperren kann) erlauben, auch die Step-ups der Eigentümerin zu blockieren. Die Step-up-Sperre hält deshalb nur Step-ups auf. Restrisiko: ein Sitzungsdieb kann den kontoweiten Zähler gesperrt halten; die Eigentümerin kann sich trotzdem anmelden, Sitzungen widerrufen und das Passwort per E-Mail zurücksetzen. Letzteres trägt nur, solange die E-Mail-Adresse selbst hinter einem Step-up liegt — seit #1841 gilt das auch für die E-Mail-Änderung selbst (`POST /privacy/email-change`): sie läuft durch denselben Step-up wie die Kontolöschung, siehe oben. Verbleibendes Restrisiko: Ein Sitzungsdieb, der zusätzlich das Postfach eines föderierten Kontos kontrolliert oder sich am OIDC-Provider erneut anmelden kann, besteht auch diesen Step-up — das ist die Mailbox bzw. der Provider-Zugang, nicht diese Prüfung.

**Nachweis.** Der Löschauftrag (`erasure_requests`) hält `step_up` (`password` / `oidc_reauth` / `email_code`; ältere, vor #1815 geschriebene Datensätze noch mit dem historischen Echo-Wert); bei einer Admin-Löschung zusätzlich `requested_by_subject` — die gesalzene Referenz des Admins, nie dessen Kontoschlüssel.

## 4. Frontend

### 4.1 Neue Seiten

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| `LoginPage` | `/login` | E-Mail/Passwort-Login + SSO-Buttons |
| `RegisterPage` | `/register` | Lokale Registrierung; folgt dem Registrierungsmodus aus `GET /mode` (§3.2d): `closed` nur Hinweis, `invite_only` mit Pflichtfeld „Einladungscode" (`?invitation=` belegt es vor) |
| `EmailVerificationPage` | `/verify-email/:token` | E-Mail-Bestätigung; im Fehlerfall Verweis auf `ResendVerificationPage` |
| `ResendVerificationPage` | `/resend-verification` | Neuen Bestätigungslink anfordern (§3.2b, #2037) |
| `PasswordResetRequestPage` | `/password-reset` | Passwort-Reset anfordern |
| `PasswordResetConfirmPage` | `/password-reset/:token` | Neues Passwort setzen |
| `AccountSettingsPage` | `/settings/account` | Profil, Auth-Provider, Sessions |
| `AdminOidcProvidersPage` | `/admin/oidc-providers` | OIDC-Provider-Konfigurationen der Installation: Liste, Anlegen, Bearbeiten, Löschen, Discovery-Test (nur Plattform-Admin, §3.9, #1906) |

### 4.2 Komponenten

**`LoginPage`:**
- E-Mail + Passwort-Formular
- **Checkbox „Angemeldet bleiben"** (`remember_me`) — unterhalb des Passwort-Felds, vor dem Login-Button. Standard: nicht aktiviert. Tooltip: „Aktiviere diese Option nur auf privaten Geräten. Deine Sitzung bleibt bis zu 30 Tage aktiv."
- Divider "oder"
- SSO-Buttons (dynamisch aus `/api/v1/auth/oauth/providers`):
  - Google: Offizielles Google-Sign-In-Branding
  - GitHub: GitHub-Logo + "Mit GitHub anmelden"
  - Apple: Offizielles Apple-Sign-In-Branding (Dark/Light Modus)
  - Generische OIDC: icon_url + display_name
- Link zu "Passwort vergessen"
- Link zu "Registrieren" — entfällt bei `REGISTRATION_MODE=closed`, lautet bei `invite_only` „Mit Einladung registrieren" (§3.2d)

**`AccountSettingsPage`:**
- **Tab "Profil":** Anzeigename, Avatar (URL-Eingabe), Sprache (DE/EN), Zeitzone
- **Tab "Sicherheit":** Passwort ändern/setzen, Verknüpfte Provider (Google ✓, GitHub ✓, etc.), Provider entfernen
- **Tab "Sessions":** Liste aktiver Sessions (Gerät, IP, Zeitpunkt, „Angemeldet bleiben" Ja/Nein), "Andere Sessions beenden"-Button
- **Tab "API-Keys":** Verwaltung von M2M-API-Keys (siehe §3.7)
- **Tab "Integrationen":** Home Assistant Verbindung konfigurieren (siehe Detailbeschreibung unten)
- **Tab "Account":** Account löschen (Bestätigungs-Dialog mit Passworteingabe)

**Tab "Integrationen" — Detailbeschreibung:**

Ermöglicht dem Nutzer, seine Home Assistant Instanz mit Kamerplanter zu verbinden. Der hier hinterlegte Long-Lived Access Token wird vom `HomeAssistantConnector` (REQ-005) verwendet, um Sensordaten automatisch von Home Assistant abzurufen.

**Sichtbarkeit:** Der Tab „Integrationen" ist immer sichtbar — er dient als zentrale Stelle, an der der Nutzer die HA-Integration aktivieren oder deaktivieren kann. Solange die HA-Integration nicht aktiviert ist (`ha_token_set == false`), werden in allen anderen Bereichen des Systems (Sensoren, Aktoren, Tanks, Dashboard) die HA-spezifischen Felder und Panels ausgeblendet (siehe REQ-005 §4a Optionalitätsprinzip).

**Felder:**

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| Home Assistant URL | Text | URL der HA-Instanz (z.B. `http://homeassistant.local:8123`). Validierung: gültige URL, erreichbar beim Verbindungstest. |
| Long-Lived Access Token | Passwort | HA-Token aus Profil → Sicherheit → Long-Lived Access Tokens. Wird AES-256-verschlüsselt gespeichert, in der UI nach dem Speichern nur als `••••••••` angezeigt. |
| Verbindungsstatus | Chip | Zeigt den aktuellen Status: ✅ Verbunden (HA-Version), ⚠️ Nicht erreichbar, ❌ Nicht konfiguriert |

**Aktionen:**

- **Verbindung testen** → `POST /api/v1/auth/ha-connection/test` — Ruft HA `/api/` auf, zeigt Erfolg/Fehler mit HA-Version
- **Speichern** → `PATCH /api/v1/users/me` mit `ha_url` und `ha_token` (Token wird serverseitig verschlüsselt)
- **Token entfernen** → Setzt `ha_url` und `ha_token_encrypted` auf `null`

**Sicherheitshinweis:** Der Token wird niemals im Klartext an das Frontend zurückgegeben. `GET /api/v1/users/me` liefert nur `ha_url` und `ha_token_set: bool` (ob ein Token hinterlegt ist).

<!-- Quelle: Smart-Home-HA-Integration Review A-003 -->
**Tab "API-Keys" — Detailbeschreibung:**

Ermöglicht dem Nutzer, beliebig viele personalisierte API-Keys zu erstellen und zu verwalten — für Home Assistant, Monitoring, CI/CD oder andere M2M-Consumer.

**Ansicht: Key-Liste (Tabelle)**

| Spalte | Beschreibung |
|--------|-------------|
| Label | Vom User vergebener Name (z.B. "Home Assistant Zelt 1") |
| Key-Prefix | Erste 8 Zeichen (`kp_a3f8...`) — zur Identifikation |
| Tenant-Scope | Eingeschränkter Tenant oder "Alle" |
| Erstellt | Erstelldatum (relativ, z.B. "vor 3 Tagen") |
| Letzter Zugriff | Zeitpunkt der letzten Nutzung oder "Nie verwendet" |
| Aktion | Revoke-Button (Mülleimer-Icon) |

**Aktion: Neuen Key erstellen (Dialog)**

- **Label** (Pflicht): Freitext-Eingabe, z.B. "Home Assistant", "Grafana", "CI/CD Pipeline"
- **Tenant-Scope** (Optional): Dropdown mit eigenen Tenants + Option "Alle Tenants"
- **Erstellen-Button** → `POST /api/v1/auth/api-keys`
- **Ergebnis-Dialog (einmalig):** Zeigt den vollständigen Key im Klartext in einem read-only Textfeld mit Copy-Button. **Warnhinweis:** "Dieser Key wird nur einmal angezeigt. Kopieren Sie ihn jetzt und speichern Sie ihn sicher. Nach dem Schließen dieses Dialogs ist der Klartext-Key nicht mehr abrufbar."

**Aktion: Key revoken (Bestätigung)**

- Klick auf Revoke-Button → Bestätigungs-Dialog: "API-Key '{label}' wirklich widerrufen? Alle Anwendungen die diesen Key verwenden verlieren sofort den Zugriff."
- Bestätigen → `DELETE /api/v1/auth/api-keys/{key_id}`
- Key verschwindet aus der Liste (oder wird als "Widerrufen" markiert)

**Leerzustand:** "Keine API-Keys vorhanden. Erstellen Sie einen Key für Home Assistant, Monitoring oder andere Anwendungen."

### 4.3 Auth-State-Management (Redux)

```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Thunks:
// loginLocal(email, password, rememberMe) → setzt user + accessToken
// loginOAuth(providerSlug) → Redirect zu OAuth-Provider
// oauthCallback(providerSlug, code, state) → setzt user + accessToken
// refreshToken() → nutzt Cookie, aktualisiert accessToken
// logout() → löscht State + Cookie
```

### 4.4 Axios-Interceptor

```typescript
// Request-Interceptor: Fügt Authorization-Header hinzu
// Response-Interceptor: Bei 401 → automatischer Token-Refresh → Retry
// Falls Refresh fehlschlägt → Logout + Redirect zu /login
```

### 4.5 Route-Guards

```typescript
// ProtectedRoute: Erfordert authentifizierten User, Redirect zu /login
// PublicOnlyRoute: Nur für nicht-authentifizierte User (Login/Register), Redirect zu /dashboard
```

<!-- Quelle: Issue #1118 -->
### 4.6 Gerät-verbinden-Dialog (Sessions-Tab, #1118)

Im Tab „Sessions" der `AccountSettingsPage` (der ohnehin nur im Full-Modus existiert, sodass der Light-Modus baulich ausgeschlossen ist) öffnet eine Aktion „Gerät verbinden" den Dialog `ConnectDeviceDialog`. Er fordert über `POST /auth/device-pairing` einen Einmalcode an und rendert die QR-Nutzlast `{"v":…,"url":…,"code":…}` als `<QRCodeSVG>`.

- Ein Countdown zeigt die Restsekunden (`expires_in`); bei Null wird der QR durch einen Ablauf-Zustand mit „Neu erzeugen"-Aktion ersetzt, die einen frischen Code holt.
- Der Code erscheint **nirgends** als sichtbarer Text im Dialog (Schutz gegen Shoulder-Surfing) — nur im `value`-Prop des QR-Codes.
- Der Code wird nicht in Redux oder `localStorage` gehalten; Schließen des Dialogs verwirft ihn aus dem Komponenten-State. Nach dem Schließen wird die Sessions-Liste neu geladen, sodass ein frisch gekoppeltes Gerät dort erscheint.
- Alle Nutzertexte liegen als i18n-Keys unter `pages.auth.*` in DE und EN vor.

Im **Light-Modus** (REQ-027) existiert weder der Sessions-Tab noch ein Konto, und die Kopplungs-Endpunkte antworten mit `404`. Damit ein anonymer Nutzer eine Mobil-App dennoch auf die Instanz ausrichten kann, ist `ConnectDeviceDialog` modus-abhängig: Über einen eigenen Tab „App verbinden" (`connect`) im Light-Modus-Tab-Set öffnet er dort eine **reine URL-Variante**. Diese rendert seit #1118 P13 einen **App-Link-URL-String** `https://<window.location.origin>/connect?v=1` (kein JSON, kein `code`) als QR — bewusst eine URL und kein JSON-Blob, damit die System-Kamera eines Smartphones ihn als Link erkennt. Sie führt **keinen** Backend-Aufruf durch und hat weder Countdown noch Ablauf/Neu-Erzeugen; sie dient ausschließlich der Instanz-Erkennung und meldet niemanden an. Der Full-Modus-Pfad (Sessions-Tab, opakes JSON `{"v","url","code"}`, ausschließlich in-App scanbar) bleibt **unverändert**: Der Einmalcode darf kein abfangbarer Deep Link werden.

Der Pfad `/connect` rendert im Browser eine schlanke, credential-freie Landing-Seite (`ConnectLandingPage`, außerhalb von Auth-Guard und Modus-Weiche, in Light- **und** Full-Modus), damit der Link nie in ein 404 läuft: Sie erklärt, den Link mit der Kamerplanter-App zu öffnen, und bietet „Im Browser fortfahren" an. Der **App-seitige** Kontrakt — den die künftige Android-App implementieren wird — ist ein `intent-filter` mit **Wildcard-Host** (`android:host="*"`) auf dem Pfad `/connect` (unverifizierter Deep Link → System-Auswahldialog). Automatisch **verifizierte** App Links sind hier bewusst **nicht** möglich, weil sie an feste, im Manifest deklarierte Domains binden, Kamerplanter aber selbst gehostet wird und jede Instanz eine im Voraus unbekannte Domain hat. Der `intent-filter` selbst ist **nicht** Teil dieses Umfangs (die App ist nicht implementiert); gebaut ist hier nur die vom Frontend emittierte URL und der Browser-Fallback.
<!-- /Quelle: Issue #1118 -->

## 5. Seed-Daten

### Betreiberentscheidungen vom 2026-10-03 (#1948, #1906)

- **E-Mail-Bestätigung (#1948):** Der Default von `REQUIRE_EMAIL_VERIFICATION` ist **`true`**. Eine Installation ohne ausgehenden Mailversand setzt die Variable ausdrücklich auf `false`; dann gilt die Adresse als nicht belegt (REQ-030); den Beleg trägt `email_confirmed_at` (v1.37).
- **OIDC-Provider-Verwaltung (#1906):** Plattform-Admins verwalten OIDC-Provider über eine **eigene Seite im Optionen-Bereich** (Anlegen, Ändern, Deaktivieren; jede Änderung läuft über den Step-up `oidc_provider_change`, §3.9). Die Aussage „nur über die API“ (#1980) entfällt, sobald die Seite ausgeliefert ist; die Nutzerdokumentation (DE/EN) wird dann nachgezogen.

### Benannte SSO-Provider (Vorkonfiguriert):

```json
[
  {
    "slug": "google",
    "display_name": "Google",
    "provider_type": "google",
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
    "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
    "scopes": ["openid", "email", "profile"],
    "enabled": false,
    "auto_discover": true
  },
  {
    "slug": "github",
    "display_name": "GitHub",
    "provider_type": "github",
    "authorization_url": "https://github.com/login/oauth/authorize",
    "token_url": "https://github.com/login/oauth/access_token",
    "userinfo_url": "https://api.github.com/user",
    "scopes": ["read:user", "user:email"],
    "enabled": false,
    "auto_discover": false
  },
  {
    "slug": "apple",
    "display_name": "Apple",
    "provider_type": "apple",
    "authorization_url": "https://appleid.apple.com/auth/authorize",
    "token_url": "https://appleid.apple.com/auth/token",
    "jwks_url": "https://appleid.apple.com/auth/keys",
    "scopes": ["name", "email"],
    "enabled": false,
    "auto_discover": false
  }
]
```

**Hinweis:** Benannte Provider werden mit `enabled: false` ausgeliefert. Aktivierung erfordert das Setzen von `client_id` und `client_secret` durch den System-Admin.

### Demo-User (Nur Entwicklungsumgebung):

```json
{
  "email": "demo@kamerplanter.local",
  "display_name": "Demo-Gärtner",
  "password": "demo-passwort-2024",
  "status": "active",
  "email_verified": true,
  "locale": "de",
  "timezone": "Europe/Berlin"
}
```

<!-- Quelle: Platform-Admin v1.6 -->
## 5a. Platform-Admin-Rolle

### 5a.1 Konzept

Der **Platform-Admin** (KA-Admin) ist ein Benutzer mit Membership im **Platform-Tenant** (REQ-024 v1.3). Die Platform-Admin-Berechtigung wird über das bestehende Tenant/Membership-Modell abgebildet — es gibt kein separates Rollen-System.

**Architektur-Entscheidung:** Die Platform-Admin-Rolle nutzt das bestehende Membership-Modell (Variante 1: Platform-Tenant) statt eines `is_platform_admin`-Flags auf User-Ebene. Begründung:
- Wiederverwendung der bestehenden Tenant/Membership-Mechanik
- Differenzierte Rollen im Platform-Tenant möglich: `lead` = Plattform-Admin (umgesetzt). Eine Lese-Variante `viewer` (Read-Only-Zugang zum Admin-Panel, REQ-024 §1a.4) ist vorgesehen, aber **nicht implementiert** (#2179) — eine `viewer`-Mitgliedschaft in `platform` gewährt heute keinerlei Admin-Zugriff
- Kein zweites Rollen-System neben dem Tenant-scoped-Modell

**Doppelrolle:**
Ein User kann gleichzeitig Memberships in beliebig vielen Tenants haben, inklusive dem Platform-Tenant:

```
User "anna"
  ├── Membership in tenant/platform (role: lead) → KA-Admin
  ├── Membership in tenant/annas-garten (role: lead, admin_scopes: [management, technical]) → Privater Garten
  └── Membership in tenant/gruene-oase (role: grower) → Gemeinschaftsgarten
```

### 5a.2 JWT-Erweiterung

Das JWT Access Token wird um ein `is_platform_admin`-Flag erweitert:

```python
# Token Payload (Erweiterung)
{
    "sub": "users/anna",
    "email": "anna@example.com",
    "display_name": "Anna",
    "tenant_roles": {
        "platform": "lead",         # Platform-Tenant Membership
        "annas-garten": "lead",
        "gruene-oase": "grower"
    },
    "is_platform_admin": true,       # NEU: Shortcut für Frontend/Backend
    "exp": 1711276800,
    "iat": 1711275900,
    "type": "access"
}
```

Das `is_platform_admin`-Flag wird beim Token-Erstellen aus der gespeicherten Mitgliedschaft abgeleitet (`AuthService._holds_platform_lead`, dieselbe Regel wie `app.common.auth.is_platform_admin`):

```python
is_platform_admin = membership("platform") is not None and membership.is_active and membership.role == "lead"
```

**Umsetzungsstand (v1.46, #2121):** Das Beispiel oben zeigt das Zielbild. Ausgestellt wird `tenant_roles` heute **leer** (`{}`); `is_platform_admin` steht im Token, wird aber von keiner Autorisierung gelesen. Backend-Wächter und MCP lesen die Mitgliedschaft zur Laufzeit, das Frontend liest `is_platform_admin` aus `GET /users/me`. Beide Claims sind damit **informativ**: Eine Rollenänderung wirkt mit der nächsten Anfrage, nicht erst mit dem nächsten Token.

### 5a.3 Backend-Dependency

Neue FastAPI-Dependency für Platform-Admin-geschützte Endpunkte:

```python
def get_platform_admin(
    current_user: User = Depends(get_current_user),
    membership_repo: IMembershipRepository = Depends(get_membership_repo),
) -> User:
    """Stellt sicher, dass der aktuelle User Platform-Admin ist.
    Wirft ForbiddenError wenn keine aktive lead-Membership im Platform-Tenant."""
    platform_membership = membership_repo.get_by_user_and_tenant(
        current_user.key, "platform"
    )
    if not platform_membership or not platform_membership.is_active or platform_membership.role != "lead":
        raise ForbiddenError("Platform admin access required.")
    return current_user
```

**Umgesetzt** als `require_platform_admin` über `get_is_platform_admin` in `app/common/auth.py` (Light-Modus: der System-User gilt als Plattform-Admin; ein auf einen Mandanten beschränkter API-Key ist nie Plattform-Admin, #1817).

Verwendung in Routern:

```python
@router.post("/species/{species_key}/assign-to-tenant/{tenant_key}")
def assign_species_to_tenant(
    species_key: str,
    tenant_key: str,
    admin: User = Depends(get_platform_admin),  # Platform-Admin-Guard
):
    ...
```

### 5a.4 Platform-Admin-Rechte

| Aktion | Berechtigung | Endpoint-Pattern |
|--------|-------------|------------------|
| Globale Species/Cultivars erstellen/bearbeiten/löschen | Plattform-Admin | `POST/PUT/DELETE /api/v1/species/*` |
| `tenant_has_access`-Kanten verwalten (zuweisen/entziehen) | Plattform-Admin | `POST/DELETE /api/v1/admin/species/{key}/tenants/{tenant_key}` |
| Tenant-Species zu global promoten | Plattform-Admin | `POST /api/v1/admin/species/{key}/promote` |
| Alle Tenants auflisten | Plattform-Admin | `GET /api/v1/admin/tenants` |
| Globale IPM-Daten verwalten | Plattform-Admin | `POST/PUT/DELETE /api/v1/pests/*`, `/diseases/*`, `/treatments/*` |
| OIDC-Provider konfigurieren | Plattform-Admin | `POST/PUT/DELETE /api/v1/admin/oidc-providers/*` (bereits vorhanden) |
<!-- Quelle: Tenant-Notfallverwaltung v1.7 -->
| Verwaisten Tenant einsehen (Mitglieder, Status) | Plattform-Admin | `GET /api/v1/admin/tenants/{tenant_key}/members` |
| Neuen Admin in Tenant ernennen (Notfall) | Plattform-Admin | `POST /api/v1/admin/tenants/{tenant_key}/emergency-admin` |
| Tenant suspendieren | Plattform-Admin | `POST /api/v1/admin/tenants/{tenant_key}/suspend` |
| Tenant reaktivieren | Plattform-Admin | `POST /api/v1/admin/tenants/{tenant_key}/reactivate` |
| User-Status ändern (suspend/reactivate) | Plattform-Admin | `POST /api/v1/admin/users/{user_key}/suspend`, `POST .../reactivate` |
<!-- /Quelle: Tenant-Notfallverwaltung v1.7 -->

**Umsetzungsstand (v1.46, #2121):** Die Plattform-Admin-Routen liegen unter `/api/v1/admin/platform/...` (Mandanten, Nutzer, Mitgliedschaften, Löschungen, Sicherheits-Audit), die Katalog- und Anmeldeanbieter-Routen unter ihren eigenen Pfaden. Abweichend von der Tabelle: **Notfall-Admin ernennen** ist gestrichen (v1.43, #2134); **Mandant sperren/reaktivieren** ist `PATCH /admin/platform/tenants/{key}` mit `is_active` (Zustand `suspended`/`active`, Step-up, REQ-024 AK-56/AK-65); **Nutzer sperren/reaktivieren** ist `PATCH /admin/platform/users/{key}` mit `is_active` (Step-up; das Sperren beendet alle Sitzungen, #2116, und API-Keys des Kontos werden abgewiesen, solange es gesperrt ist). Einen **Plattform-Viewer** gibt es nicht (REQ-024 §1a.4, #2179).

<!-- Quelle: Tenant-Notfallverwaltung v1.7 -->
### 5a.5 Tenant-Notfallverwaltung durch Platform-Admin

> **Gestrichen (v1.43, #2134):** §5a.5.1 (Verwaist-Erkennung per wöchentlichem Task,
> `orphaned_since`) und §5a.5.2 (Emergency-Admin-Ernennung) werden **nicht** umgesetzt. Eine
> Organisation verliert ihre letzte Verwaltung nur noch durch eine Kontolöschung; dort
> übernimmt die dienstälteste Leitung, sonst wird die Organisation `orphaned` und nach der
> Gnadenfrist gelöscht (REQ-025 §3.1.3 Regel 4, REQ-024 AK-65). Der Text unten bleibt als
> Entscheidungshistorie stehen. §5a.5.3 ist als Mandantenzustand `suspended` umgesetzt
> (#2105, #2123), mit `PATCH /admin/platform/tenants/{key}` statt der hier skizzierten Routen.
>
> **Umsetzungsstand §5a.5.3/§5a.5.4 (v1.46, #2121):** Ein gesperrter Mandant antwortet auf
> `/t/{slug}/…`, `X-Active-Tenant` und MCP wie ein unbekannter Kurzname (`403` ohne eigene
> Meldung — eine Meldung „suspendiert“ wäre ein Existenz-Orakel, REQ-024 AK-48) und erscheint
> **nicht** im Mandanten-Wechsler (statt ausgegraut). **Nicht implementiert:** das Pausieren der
> Celery-Tasks eines gesperrten Mandanten (Pflege-Erinnerungen, Gieß-Aufgaben laufen weiter) und
> ein Sperrgrund (`suspended_reason`) — beides gehört zur Suspendierungs-Semantik von #2143. Die
> Konto-Sperre (§5a.5.4) ist `PATCH /admin/platform/users/{key}` mit `is_active`; der Schutz
> gegen Selbstsperre bzw. das Sperren des letzten Plattform-Admins fehlt (#2144, MT-045).

**Problem:** Wenn alle Admins eines Organisations-Tenants ausfallen (Account gelöscht, suspended, alle verlassen den Tenant), ist der Tenant verwaist — kein Mitglied kann Verwaltungsaktionen durchführen. Ohne Eingriffsmöglichkeit ist der Tenant und alle seine Daten faktisch verloren.

**Lösung:** Platform-Admins erhalten die Fähigkeit, in verwaiste Tenants einzugreifen und einen neuen Admin zu ernennen. Dieser Eingriff ist an strenge Bedingungen geknüpft und wird vollständig protokolliert.

#### 5a.5.1 Verwaist-Erkennung

Ein Tenant gilt als **verwaist** wenn:
```python
def is_orphaned(tenant_key: str) -> bool:
    """Verwaist = kein aktives Mitglied mit der Zusatzberechtigung `management`.

    Der Anker ist Achse 2, NICHT der fachliche Rang (REQ-024 AK-10): Ein
    Mandant ohne Leitung ist bedienbar -- niemand darf loeschen, aber alles
    andere laeuft. Ein Mandant ohne `management` ist handlungsunfaehig, weil
    niemand mehr Mitglieder einladen, Rollen aendern oder Einstellungen
    pflegen kann. Nur der zweite Fall rechtfertigt die Notfallverwaltung.
    """
    active_managers = membership_repo.count_active_managers(tenant_key)
    return active_managers == 0
```

**Automatische Erkennung:** Ein Celery-Task prüft wöchentlich alle Organisations-Tenants auf Verwaist-Status und setzt ggf. ein Flag `orphaned_since: datetime` auf dem Tenant. Platform-Admins sehen verwaiste Tenants prominent im Admin-Panel.

#### 5a.5.2 Emergency-Admin-Ernennung

```python
@router.post("/admin/tenants/{tenant_key}/emergency-admin")
def appoint_emergency_admin(
    tenant_key: str,
    request: EmergencyAdminRequest,
    admin: User = Depends(get_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> EmergencyAdminResponse:
    """Ernennt einen neuen Admin in einem verwaisten Tenant.

    Bedingungen:
    1. Aufrufender muss Platform-Admin sein
    2. Tenant muss verwaist sein (keine aktiven Admins)
    3. Ziel-User muss existieren und status 'active' haben
    4. Ziel-User darf bereits Mitglied sein (erhält Rolle 'lead' und Zusatzberechtigung `management`)
       ODER wird als neues Mitglied mit Rolle 'lead' und `management` hinzugefügt
    5. Aktion wird im Audit-Log protokolliert
    """
```

**Request:**
```json
{
  "user_key": "users/max",
  "reason": "Bisherige Admins Lisa und Tom haben Verein verlassen. Max ist stellvertretender Vorsitzender."
}
```

**Response:**
```json
{
  "tenant_key": "gruene-oase",
  "user_key": "users/max",
  "previous_role": "grower",
  "new_role": "lead",
  "reason": "Bisherige Admins Lisa und Tom haben Verein verlassen. Max ist stellvertretender Vorsitzender.",
  "appointed_by": "users/anna",
  "appointed_at": "2026-03-17T14:30:00Z",
  "orphaned_since": "2026-03-10T00:00:00Z"
}
```

**Sicherheitsregeln:**
- **Nur bei verwaisten Tenants:** Wenn der Tenant noch aktive Admins hat → 409 Conflict ("Tenant hat aktive Admins — Notfall-Eingriff nicht erforderlich")
- **Reason ist Pflichtfeld:** Der Grund wird persistent gespeichert (Audit-Trail)
- **Benachrichtigung:** Alle aktiven Mitglieder des Tenants werden benachrichtigt (E-Mail/In-App), dass ein neuer Admin durch Platform-Admin ernannt wurde
- **Keine Selbst-Ernennung:** Platform-Admin darf sich selbst als Emergency-Admin einsetzen (sinnvoll für kleine Instanzen mit einem einzigen KA-Admin)

#### 5a.5.3 Tenant-Suspendierung

Platform-Admins können Tenants bei Bedarf suspendieren (z.B. bei Missbrauch, Rechtsstreitigkeiten, nicht-zahlenden Kunden im SaaS-Modell):

```python
@router.post("/admin/tenants/{tenant_key}/suspend")
def suspend_tenant(
    tenant_key: str,
    request: TenantSuspendRequest,  # { reason: str }
    admin: User = Depends(get_platform_admin),
) -> Tenant:
    """Setzt Tenant auf status='suspended'.
    Alle API-Zugriffe im Tenant-Scope geben 403 zurück.
    Memberships bleiben erhalten, aber Zugriff wird blockiert."""
```

```python
@router.post("/admin/tenants/{tenant_key}/reactivate")
def reactivate_tenant(
    tenant_key: str,
    admin: User = Depends(get_platform_admin),
) -> Tenant:
    """Setzt Tenant zurück auf status='active'."""
```

**Verhalten bei suspendiertem Tenant:**
- Alle tenant-scoped API-Requests (`/api/v1/t/{slug}/...`) geben 403 zurück mit Meldung "Tenant ist suspendiert. Kontaktieren Sie den Plattform-Administrator."
- Tenant erscheint im Tenant-Switcher ausgegraut mit Hinweis
- Memberships bleiben erhalten → bei Reaktivierung sofort wieder funktionsfähig
- Celery-Tasks für den Tenant werden pausiert (kein Care-Reminder, kein Watering-Task)
- Platform-Tenant kann NICHT suspendiert werden (Schutz)
- Persönliche Tenants können suspendiert werden (z.B. bei Account-Missbrauch)

#### 5a.5.4 User-Verwaltung durch Platform-Admin

Platform-Admins können User-Accounts verwalten (z.B. bei Missbrauch, kompromittierten Accounts):

```python
@router.post("/admin/users/{user_key}/suspend")
def suspend_user(
    user_key: str,
    request: UserSuspendRequest,  # { reason: str }
    admin: User = Depends(get_platform_admin),
) -> User:
    """Setzt User auf status='suspended'.
    Alle Refresh Tokens werden invalidiert.
    Alle API-Keys werden suspendiert.
    User kann sich nicht mehr anmelden."""

@router.post("/admin/users/{user_key}/reactivate")
def reactivate_user(
    user_key: str,
    admin: User = Depends(get_platform_admin),
) -> User:
    """Setzt User zurück auf status='active'.
    User muss sich erneut anmelden (keine automatische Session-Wiederherstellung)."""
```

**Schutzregeln:**
- Platform-Admin kann sich NICHT selbst suspendieren
- Wenn der suspendierte User der letzte Admin eines Tenants ist → Tenant wird als verwaist markiert (`orphaned_since` gesetzt)
- System-User (Light-Modus) kann nicht suspendiert werden

#### 5a.5.5 Szenarien

**Szenario 12: Verwaister Gemeinschaftsgarten — Notfall-Admin**
```
Voraussetzung: Tenant "Grüne Oase e.V." mit 12 Mitgliedern
  Lisa (Admin) hat Account gelöscht
  Tom (Admin, Stellvertreter) hat Verein verlassen

1. Celery-Task erkennt: "Grüne Oase e.V." hat 0 aktive Admins
   → orphaned_since: 2026-03-10
2. KA-Admin Anna sieht im Admin-Panel: "1 verwaister Tenant"
3. Anna öffnet Tenant-Details → sieht Mitgliederliste:
   - Lisa (deleted), Tom (left), Max (grower), ...
4. Anna wählt "Notfall-Admin ernennen" → Max (Grower)
5. Grund: "Bisherige Admins haben Verein verlassen. Max ist Kassenwart."
6. System:
   a) Max' Rolle: grower → lead, Zusatzberechtigung management
   b) orphaned_since: null (Tenant nicht mehr verwaist)
   c) E-Mail an alle 10 verbleibenden Mitglieder:
      "Max wurde von der Plattform-Administration als neuer Admin ernannt."
7. Max kann jetzt Mitglieder verwalten, Einladungen erstellen, etc.
```

**Szenario 13: Tenant-Suspendierung bei Missbrauch**
```
1. KA-Admin erhält Hinweis: Tenant "spam-garden" missbraucht Plattform
2. Anna navigiert zu Admin-Panel → Tenant-Liste
3. Klickt auf "spam-garden" → "Tenant suspendieren"
4. Gibt Grund ein: "Spam-Inhalte, Meldung von 3 Nutzern"
5. System setzt status='suspended'
6. Alle 5 Mitglieder von "spam-garden":
   - Sehen im Tenant-Switcher: "spam-garden (suspendiert)"
   - API-Zugriffe auf /t/spam-garden/* → 403
   - Andere Tenants der Mitglieder funktionieren normal
7. Nach Klärung: Anna reaktiviert → sofort wieder funktionsfähig
```

**Szenario 14: User-Suspendierung bei kompromittiertem Account**
```
1. KA-Admin bemerkt: User "hacker@example.com" zeigt verdächtige Aktivität
2. Anna suspendiert den User über Admin-Panel
3. System:
   a) status → suspended
   b) Alle Refresh Tokens invalidiert (sofortiger Logout auf allen Geräten)
   c) Alle API-Keys suspendiert
   d) Prüfung: War User letzter Admin in einem Tenant?
      → Ja in "kleiner-garten" → Tenant als verwaist markiert
4. Anna untersucht den Vorfall
5. Nach Klärung: Reaktivierung → User muss sich neu anmelden
```
<!-- /Quelle: Tenant-Notfallverwaltung v1.7 -->

### 5a.6 Szenario: Platform-Admin verwaltet Stammdaten

```
1. Anna ist Platform-Admin (Membership in tenant/platform, role: lead)
2. Anna navigiert zum Admin-Panel (/admin/stammdaten)
3. Anna sieht alle globalen Species mit Zuweisungsstatus pro Tenant
4. Anna wählt Species "Cannabis sativa" und weist sie Tenant "grow-op" zu:
   → tenant_has_access-Kante wird erstellt
5. Anna entzieht Species "Cannabis sativa" von Tenant "gemuese-garten":
   → tenant_has_access-Kante wird gelöscht
6. Tenant "grow-op" sieht Cannabis, Tenant "gemuese-garten" nicht
7. Anna wechselt zu ihrem privaten Garten (Tenant-Switcher → "Annas Garten")
   → Anna arbeitet als normaler Tenant-Admin, nicht als KA-Admin
```
<!-- /Quelle: Platform-Admin v1.6 -->

<!-- Quelle: Service Accounts v1.7 -->
## 5b. Service Accounts

### 5b.1 Konzept

**Service Accounts** sind nicht-interaktive Konten für maschinellen API-Zugriff. Sie werden als User mit `account_type: 'service'` modelliert und nutzen die bestehende Membership- und API-Key-Infrastruktur. Hauptanwendungsfälle:

| System | Typische Rolle | Zugriff |
|--------|---------------|---------|
| **Home Assistant** | `grower` im Tenant | Sensordaten schreiben, Aktoren steuern, Tasks lesen |
| **Grafana/Prometheus** | `viewer` im Tenant | Metriken/Sensordaten lesen, Dashboard-Daten abfragen |
| **CI/CD Pipeline** | `grower` im Tenant (mehr vergibt ein Mandant an ein Dienstkonto nicht, §5b.3) | Seed-Daten deployen, Konfiguration aktualisieren |
| **Enrichment-Pipeline** | Platform `viewer` (**nicht implementiert**, REQ-024 §1a.4, #2179) | Globale Stammdaten lesen, Enrichment-Ergebnisse schreiben |
| **Backup-System** | Platform `lead` (= Plattform-Admin; Platform Service Accounts: §5b.4) | Cross-Tenant Read-Access für Datensicherung |

**Architektur-Entscheidung:** Service Accounts als User-Subtyp (Variante B) statt separater Entity (Variante A). Begründung:
- Wiederverwendung der gesamten Membership/API-Key/RBAC-Infrastruktur ohne Code-Duplikation
- `get_current_user`-Dependency funktioniert unverändert — gibt User zurück, egal ob `human` oder `service`
- Permission-Prüfung (REQ-024 Permission Matrix) greift identisch für beide Account-Typen
- Audit-Trail mit `user_key` funktioniert transparent (Service Account Keys sind in Logs identifizierbar)

### 5b.2 Abgrenzung: Service Account vs. API-Key eines menschlichen Users

| Eigenschaft | API-Key (human User) | Service Account |
|-------------|---------------------|-----------------|
| **Besitzer** | Menschlicher User | Eigenständiges Konto (`account_type: 'service'`) |
| **Erstellung** | User erstellt selbst | Tenant-Admin oder Platform-Admin erstellt |
| **Interaktiver Login** | User kann sich per Passwort/SSO anmelden | Kein Login möglich (kein Passwort, kein SSO) |
| **JWT-Tokens** | Ja (interaktive Sessions) | Nein (nur API-Key-Authentifizierung) |
| **Refresh Tokens** | Ja | Nein |
| **Membership** | Eigene Memberships des Users | Eigene Memberships — vom Ersteller festgelegt |
| **IP-Einschränkung** | Nicht unterstützt | `allowed_ip_ranges` (CIDR-Notation) |
| **Individuelles Rate Limit** | Nein (globaler Default) | `rate_limit_rpm` pro Account konfigurierbar |
| **Sichtbarkeit** | Nur für den User selbst | Für Tenant-Admins und Platform-Admins sichtbar |
| **Verantwortung** | User selbst | `created_by` → Ersteller ist verantwortlich |

### 5b.3 Tenant-scoped Service Accounts

Tenant-Admins können Service Accounts für ihren Tenant erstellen. Der Service Account erhält eine Membership im Tenant mit einer vom Admin festgelegten Rolle.

**Regeln:**
- Service Accounts eines Mandanten erstellt nur, wem REQ-049 §2.4 diese Aufgabe zuweist (bis v1.45 stand hier der stillgelegte Wert `admin`; Umsetzung und endgültige Regel: #2137)
- Die zugewiesene Rolle darf maximal `grower` sein — ein Service Account kann nicht `lead` im Tenant werden (verhindert Privilege Escalation über maschinelle Konten)
- Ausnahme: Platform-Admins dürfen Service Accounts mit jeder Rolle erstellen (auch `lead`)
- Service Accounts werden dem Tenant via Membership zugeordnet (analog zu menschlichen Usern)
- Ein Service Account kann Memberships in mehreren Tenants haben (z.B. Home Assistant, das mehrere Growzelte überwacht)
- Die `email` des Service Accounts folgt dem Pattern `{slugified-name}@service.{tenant_slug}.local` (nicht routbar, nur für Eindeutigkeit)

### 5b.4 Platform-scoped Service Accounts

Platform-Admins können Service Accounts auf Plattformebene erstellen. Diese erhalten eine Membership im Platform-Tenant und können zusätzlich Memberships in beliebigen regulären Tenants erhalten.

**Regeln:**
- Nur Platform-Admins dürfen Platform Service Accounts erstellen
- Platform Service Accounts können Rollen im Platform-Tenant haben (`lead` oder `viewer`; `viewer` dort ist **nicht implementiert**, REQ-024 §1a.4, #2179)
- Platform Service Accounts mit `lead`-Rolle im Platform-Tenant haben KA-Admin-Rechte (globale Stammdaten, `tenant_has_access`-Verwaltung)
- Platform Service Accounts mit `viewer`-Rolle im Platform-Tenant haben Read-Only-Zugriff auf das Admin-Panel (z.B. für Monitoring/Dashboards)

### 5b.5 Service Account Lifecycle

```
Erstellt (active) → Suspendiert (suspended) → Reaktiviert (active) → Gelöscht (deleted)
                  ↘                                                  ↗
                    → Gelöscht (deleted) ─────────────────────────────
```

| Status | Verhalten |
|--------|----------|
| `active` | API-Keys funktionieren, normale Zugriffskontrolle |
| `suspended` | Alle API-Keys sofort ungültig (401), Daten bleiben erhalten. Reaktivierung möglich. |
| `deleted` | Soft-Delete — Alle API-Keys invalidiert, Memberships auf `status: 'left'` gesetzt. Nicht reaktivierbar. |

### 5b.6 Backend-Architektur

**`ServiceAccountEngine`** — Validierungslogik (pure Logik, kein I/O):

```python
class ServiceAccountEngine:
    MAX_SERVICE_ACCOUNTS_PER_TENANT = 20
    DEFAULT_RATE_LIMIT_RPM = 1000

    def validate_name(self, name: str) -> list[str]: ...
        # Min 2, Max 100 Zeichen
        # Nur alphanumerisch, Leerzeichen, Bindestriche

    def generate_email(self, name: str, tenant_slug: str) -> str: ...
        # "Home Assistant" + "mein-garten" → "home-assistant@service.mein-garten.local"

    def validate_ip_ranges(self, ip_ranges: list[str]) -> list[str]: ...
        # Prüft gültige CIDR-Notation (IPv4 und IPv6)
        # Maximale Range: /8 (IPv4), /32 (IPv6) — verhindert "0.0.0.0/0"

    def check_ip_allowed(self, client_ip: str, allowed_ranges: list[str]) -> bool: ...
        # Prüft ob Client-IP in einem der erlaubten CIDR-Bereiche liegt
        # None/leere Liste → alle IPs erlaubt

    def can_assign_role(self, creator_role: str, target_role: str,
                        is_platform_admin: bool) -> bool: ...
        # Tenant-Admin: max. grower
        # Platform-Admin: alle Rollen (inkl. admin)

    def validate_rate_limit(self, rpm: int) -> list[str]: ...
        # Min: 10, Max: 10000 req/min
```

**`ServiceAccountService`** — Orchestriert Service-Account-CRUD:

```python
class ServiceAccountService:
    def __init__(self, user_repo, membership_repo, api_key_repo,
                 service_account_engine, membership_engine, tenant_repo): ...

    async def create_service_account(
        self,
        creator: User,
        tenant_key: str,
        name: str,
        role: str,
        description: str | None = None,
        rate_limit_rpm: int | None = None,
        allowed_ip_ranges: list[str] | None = None,
    ) -> ServiceAccountCreated: ...
        # 1. Prüft: Creator ist Admin im Tenant (oder Platform-Admin)
        # 2. Prüft: Max. 20 Service Accounts pro Tenant
        # 3. Validiert Name, IP-Ranges, Rate Limit, Rollen-Zuweisung
        # 4. Erstellt User mit account_type='service', generierter E-Mail
        # 5. Erstellt Membership im Tenant mit gewählter Rolle
        # 6. Erstellt initialen API-Key (kp_...)
        # 7. Gibt ServiceAccountCreated zurück (inkl. einmaligem API-Key-Klartext)

    async def list_service_accounts(
        self, tenant_key: str, actor: User
    ) -> list[ServiceAccountInfo]: ...
        # Alle Service Accounts des Tenants (nur für Tenant-Admins)

    async def get_service_account(
        self, service_account_key: str, actor: User
    ) -> ServiceAccountDetail: ...
        # Inkl. Memberships, API-Key-Liste, letzte Aktivität

    async def update_service_account(
        self, service_account_key: str, actor: User,
        updates: ServiceAccountUpdate
    ) -> ServiceAccountDetail: ...
        # Aktualisiert: name, description, rate_limit_rpm, allowed_ip_ranges
        # Rollen-Änderung über separate Membership-Verwaltung

    async def suspend_service_account(
        self, service_account_key: str, actor: User
    ) -> None: ...
        # Setzt status='suspended', alle API-Keys sofort ungültig

    async def reactivate_service_account(
        self, service_account_key: str, actor: User
    ) -> None: ...
        # Setzt status='active', bestehende (nicht-revoked) API-Keys funktionieren wieder

    async def delete_service_account(
        self, service_account_key: str, actor: User
    ) -> None: ...
        # Soft-Delete: status='deleted', alle API-Keys revoked, Memberships 'left'

    async def rotate_api_key(
        self, service_account_key: str, actor: User
    ) -> ApiKeyCreated: ...
        # Revoked alten Key, erstellt neuen Key
        # Gibt einmalig den neuen Key-Klartext zurück

    async def add_tenant_membership(
        self, service_account_key: str, target_tenant_key: str,
        role: str, actor: User
    ) -> Membership: ...
        # Fügt Service Account als Mitglied in einem weiteren Tenant hinzu
        # Nur Platform-Admin für Cross-Tenant, Tenant-Admin für eigenen Tenant
```

### 5b.7 API-Endpoints

**Router: `/api/v1/t/{tenant_slug}/service-accounts`** — Tenant-scoped Service Account Verwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/t/{slug}/service-accounts` | Service Account erstellen (inkl. initialer API-Key) | Verwaltung |
| `GET` | `/t/{slug}/service-accounts` | Alle Service Accounts des Tenants auflisten | Verwaltung |
| `GET` | `/t/{slug}/service-accounts/{sa_key}` | Details eines Service Accounts | Verwaltung |
| `PATCH` | `/t/{slug}/service-accounts/{sa_key}` | Service Account aktualisieren (Name, Beschreibung, Rate Limit, IP-Ranges) | Verwaltung |
| `POST` | `/t/{slug}/service-accounts/{sa_key}/suspend` | Service Account suspendieren | Verwaltung |
| `POST` | `/t/{slug}/service-accounts/{sa_key}/reactivate` | Service Account reaktivieren | Verwaltung |
| `DELETE` | `/t/{slug}/service-accounts/{sa_key}` | Service Account löschen (Soft-Delete) | Verwaltung |
| `POST` | `/t/{slug}/service-accounts/{sa_key}/rotate-key` | API-Key rotieren (alter Key revoked, neuer Key erstellt) | Verwaltung |

**Router: `/api/v1/admin/platform/service-accounts`** — Platform-scoped Service Account Verwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/admin/platform/service-accounts` | Platform Service Account erstellen | Plattform-Admin |
| `GET` | `/admin/platform/service-accounts` | Alle Platform Service Accounts auflisten | Plattform-Admin |
| `GET` | `/admin/platform/service-accounts/{sa_key}` | Details eines Platform Service Accounts | Plattform-Admin |
| `PATCH` | `/admin/platform/service-accounts/{sa_key}` | Platform Service Account aktualisieren | Plattform-Admin |
| `POST` | `/admin/platform/service-accounts/{sa_key}/tenants/{tenant_key}` | Service Account Membership in weiterem Tenant hinzufügen | Plattform-Admin |
| `DELETE` | `/admin/platform/service-accounts/{sa_key}/tenants/{tenant_key}` | Service Account Membership aus Tenant entfernen | Plattform-Admin |
| `DELETE` | `/admin/platform/service-accounts/{sa_key}` | Platform Service Account löschen | Plattform-Admin |

**Gesamt:** 15 neue API-Endpoints

**POST /api/v1/t/{slug}/service-accounts — Request:**
```json
{
  "name": "Home Assistant Growzelt",
  "description": "Sensordaten und Aktorsteuerung für Zelt 1",
  "role": "grower",
  "rate_limit_rpm": 500,
  "allowed_ip_ranges": ["192.168.1.0/24"]
}
```

**POST /api/v1/t/{slug}/service-accounts — Response (einmalig mit API-Key-Klartext):**
```json
{
  "_key": "sa_homeassistant_001",
  "name": "Home Assistant Growzelt",
  "description": "Sensordaten und Aktorsteuerung für Zelt 1",
  "account_type": "service",
  "email": "home-assistant-growzelt@service.mein-garten.local",
  "role": "grower",
  "status": "active",
  "rate_limit_rpm": 500,
  "allowed_ip_ranges": ["192.168.1.0/24"],
  "api_key": {
    "_key": "ak_sa_001",
    "api_key": "kp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "key_prefix": "kp_b7e2...",
    "created_at": "2026-03-17T10:00:00Z"
  },
  "created_by": "users/anna",
  "created_at": "2026-03-17T10:00:00Z"
}
```

> **Hinweis:** Der vollständige API-Key wird nur bei der Erstellung und bei Key-Rotation angezeigt. Danach ist er nicht mehr abrufbar.

### 5b.8 JWT-Erweiterung

Das JWT Access Token (§5a.2) wird um `account_type` erweitert:

```python
{
    "sub": "users/sa_homeassistant_001",
    "email": "home-assistant-growzelt@service.mein-garten.local",
    "display_name": "Home Assistant Growzelt",
    "account_type": "service",          # NEU: Unterscheidung human/service
    "tenant_roles": {
        "mein-garten": "grower"
    },
    "is_platform_admin": false,
    "exp": 1711276800,
    "iat": 1711275900,
    "type": "access"
}
```

**Hinweis:** Service Accounts erhalten kein JWT-Token über Login — das Token wird nur intern für die API-Key→User-Auflösung im Middleware-Kontext verwendet. Der `account_type` im Token ermöglicht es Endpunkten, Service-Account-Zugriffe gesondert zu behandeln (z.B. keine interaktiven Operationen wie Passwort-Änderung).

### 5b.9 Szenarien

**Szenario 8: Home Assistant Service Account erstellen**
```
1. Anna (Tenant-Admin von "Annas Garten") navigiert zu /t/annas-garten/settings/service-accounts
2. Klickt "Service Account erstellen"
3. Dialog: Name "Home Assistant", Beschreibung "Sensor- und Aktor-Integration",
   Rolle: Gärtner (grower), IP-Bereich: 192.168.1.0/24
4. System erstellt Service Account + initialen API-Key
5. Dialog zeigt API-Key einmalig an: "kp_xxxxxxxx..."
6. Anna kopiert Key und hinterlegt ihn in der HA-Konfiguration
7. HA authentifiziert sich per API-Key → Middleware erkennt kp_-Prefix
   → löst Service Account auf → prüft IP (192.168.1.x ✓) → Zugriff OK
8. HA kann im Tenant "Annas Garten" Sensordaten schreiben und Tasks lesen
```

**Szenario 9: Monitoring Service Account mit Platform-Zugriff**
```
1. KA-Admin erstellt Platform Service Account "Grafana Monitoring"
   → POST /api/v1/admin/platform/service-accounts
   → Rolle im Platform-Tenant: viewer
2. KA-Admin fügt Service Account als viewer in 3 Tenants hinzu:
   → POST /api/v1/admin/platform/service-accounts/{key}/tenants/annas-garten
   → POST /api/v1/admin/platform/service-accounts/{key}/tenants/gruene-oase
   → POST /api/v1/admin/platform/service-accounts/{key}/tenants/cannabis-club
3. Grafana nutzt den API-Key um Metriken aus allen 3 Tenants abzurufen
4. Read-Only: Grafana kann keine Daten ändern (viewer-Rolle)
```

**Szenario 10: Service Account Key-Rotation**
```
1. Anna vermutet, dass der HA-API-Key kompromittiert wurde
2. Navigiert zu Service Account Details
3. Klickt "Key rotieren"
4. System: Alter Key wird sofort revoked, neuer Key wird erstellt
5. Dialog zeigt neuen Key einmalig an
6. Anna aktualisiert den Key in der HA-Konfiguration
7. HA nutzt ab sofort den neuen Key — alter Key ist ungültig
```

**Szenario 11: Service Account suspendieren**
```
1. Anna bemerkt verdächtige API-Zugriffe vom HA-Service-Account
2. Klickt "Suspendieren" → sofortige Wirkung
3. Alle API-Keys des Service Accounts geben 401 zurück
4. Anna untersucht das Problem
5. Problem gelöst → "Reaktivieren" → API-Keys funktionieren wieder
```

### 5b.10 Frontend

**Service Account Verwaltung im Tenant-Settings-Bereich:**

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| `ServiceAccountListPage` | `/t/{slug}/settings/service-accounts` | Liste aller Service Accounts des Tenants |
| `ServiceAccountDetailPage` | `/t/{slug}/settings/service-accounts/{sa_key}` | Details, API-Keys, Memberships, Aktivitätslog |

**ServiceAccountListPage (Tabelle):**

| Spalte | Beschreibung |
|--------|-------------|
| Name | Anzeigename (z.B. "Home Assistant Growzelt") |
| Rolle | Rolle im Tenant (Chip: grower, viewer) |
| Status | Status-Chip (active: grün, suspended: orange, deleted: grau) |
| Letzte Aktivität | Zeitpunkt des letzten API-Zugriffs oder "Nie aktiv" |
| IP-Bereich | Konfigurierte Allowlist oder "Alle" |
| Aktionen | Suspendieren/Reaktivieren, Löschen |

**ServiceAccountDetailPage (Tabs):**

- **Tab "Übersicht":** Name, Beschreibung, Status, Erstellt von, Rate Limit, IP-Bereiche — editierbar
- **Tab "API-Keys":** Aktive Keys (Label, Prefix, Erstellt, Letzter Zugriff). Button "Key rotieren" (revoked alten, erstellt neuen)
- **Tab "Tenants":** Alle Memberships des Service Accounts (Tenant-Name, Rolle). Nur bei Platform Service Accounts: Tenants hinzufügen/entfernen

**Erstell-Dialog:**

- **Name** (Pflicht): z.B. "Home Assistant", "Grafana"
- **Beschreibung** (Optional): Freitext
- **Rolle** (Pflicht): Dropdown (Gärtner, Beobachter — kein Admin für Tenant-scoped)
- **Rate Limit** (Optional): Zahleneingabe, Default 1000 req/min
- **IP-Bereiche** (Optional): Chip-Input für CIDR-Notation
- **Erstellen** → API-Key wird einmalig angezeigt (Copy-Button, Warnhinweis wie bei normalen API-Keys)

**Sichtbarkeit:**
- Service Account Menüpunkt nur für Tenant-Admins sichtbar
- Im Light-Modus (REQ-027): Sichtbar, da System-User Admin ist — nützlich für HA-Integration
- Expertise-Level (REQ-021): Nur ab `intermediate` sichtbar (beginners brauchen keine Service Accounts)

### 5b.11 Light-Modus-Integration (REQ-027)

Im Light-Modus funktionieren Service Accounts uneingeschränkt:
- System-User ist Admin im System-Tenant → kann Service Accounts erstellen
- Nützlichster Use-Case: Home Assistant Service Account für lokale HA-Integration
- Service Account API-Keys funktionieren auch ohne JWT (LightAuthProvider gibt System-User zurück, aber API-Keys werden direkt per Hash validiert — kein Bypass)

**Sicherheitsaspekt:** Im Light-Modus gibt es keine Authentifizierung — aber Service Accounts mit API-Keys bieten eine optionale Sicherheitsebene für automatisierte Zugriffe. Ein Admin kann Service Accounts mit IP-Allowlist konfigurieren, auch wenn der Browser-Zugang offen ist.

### 5b.12 Seed-Daten

**Demo Service Account (nur Entwicklungsumgebung):**

```json
{
  "email": "demo-ha@service.demo-garten.local",
  "display_name": "Demo Home Assistant",
  "account_type": "service",
  "description": "Demo Service Account für Home Assistant Integration",
  "status": "active",
  "rate_limit_rpm": 1000,
  "allowed_ip_ranges": null,
  "created_by": "users/demo-user"
}
```

Membership: `grower` im Demo-Tenant. API-Key: `kp_demo000000000000000000000000000000000000000000000000` (nur in Seed-Daten, nicht für Produktion).
<!-- /Quelle: Service Accounts v1.7 -->

## 6. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Lokale Registrierung erstellt User mit `status: unverified` und sendet Verifizierungs-E-Mail | Integration |
| AK-02 | Verifizierungs-Link setzt `status: active` und `email_verified: true` | Integration |
| AK-03 | Lokaler Login mit `remember_me=true` gibt Access Token (15 Min) + persistentes Refresh Token (30 Tage, HttpOnly Cookie mit `Max-Age`) zurück | Integration |
| AK-03a | Lokaler Login mit `remember_me=false` (Standard) gibt Access Token (15 Min) + Session-Refresh-Token (24h TTL, HttpOnly Session-Cookie ohne `Max-Age`/`Expires`) zurück | Integration |
| AK-03b | SSO-Login setzt `is_persistent=true` (persistentes Cookie, 30 Tage) | Integration |
| AK-04 | Token-Refresh erstellt neues Token-Paar und invalidiert altes Refresh Token (Rotation); `is_persistent` wird vom Vorgänger-Token übernommen | Integration |
| AK-05 | Nach 5 Fehlversuchen wird Account 15 Minuten gesperrt (`locked_until` gesetzt) | Unit + Integration |
| AK-06 | Passwort-Reset-Token ist 1 Stunde gültig und einmalig verwendbar | Integration |
| AK-07 | Nach Passwort-Reset sind alle bestehenden Refresh Tokens invalidiert | Integration |
| AK-08 | Google-OAuth2-Login erstellt User mit `email_verified: true` und verknüpftem AuthProvider | Integration |
| AK-09 | GitHub-OAuth2-Login holt E-Mail via separatem API-Call wenn privat | Integration |
| AK-10 | Apple-Sign-In speichert Name beim ersten Login (wird nur einmal übermittelt) | Integration |
| AK-11 | Generischer OIDC-Provider mit `auto_discover: true` nutzt `.well-known/openid-configuration` | Integration |
| AK-12 | Account-Linking: SSO-Login mit gleicher verifizierter E-Mail verknüpft automatisch mit bestehendem Account | Integration |
| AK-13 | Account-Linking: Entfernen des letzten Auth-Providers wird verhindert (mindestens eine Methode) | Unit |
| AK-14 | Logout invalidiert Refresh Token; Logout-All invalidiert alle Tokens des Users — **auch die Access Tokens** (ab der nächsten Anfrage `401`, #2116 v1.44) | Integration |
| AK-15 | Profil-Update (display_name, locale, timezone) persistiert korrekt | Integration |
| AK-16 | Account-Löschung setzt `status: deleted`, anonymisiert E-Mail, invalidiert alle Tokens | Integration |
| AK-17 | Celery-Task bereinigt abgelaufene Tokens stündlich und unbestätigte Accounts nach 7 Tagen; abgebrochene lokale Registrierungen werden gezählt (Trockenlauf) und erst nach Freigabe gelöscht (#2010) | Integration |
<!-- Quelle: Platform-Admin v1.6 -->
| AK-18 | Platform-Admin-Dependency (`require_platform_admin` / `get_is_platform_admin`, `app/common/auth.py`) prüft eine **aktive** Membership im Platform-Tenant mit `role: lead` (v1.46: vorher `admin`, seit `v0032` stillgelegt) | Unit + Integration |
| AK-19 | JWT Access Token enthält `is_platform_admin: true` wenn User Platform-Admin ist — **informativ**: keine Autorisierung liest den Claim (v1.46) | Unit |
| AK-20 | User kann gleichzeitig Platform-Admin und regulärer Tenant-Nutzer sein (Doppelrolle) | Integration |
| AK-21 | Nicht-Platform-Admins erhalten 403 bei Zugriff auf Platform-Admin-Endpunkte | Integration |
| AK-22 | Platform-Admin kann globale Species/Cultivars erstellen, bearbeiten, löschen | Integration |
| AK-23 | Platform-Admin kann `tenant_has_access`-Kanten erstellen und entfernen | Integration |
| AK-24 | Platform-Admin kann Tenant-eigene Species zu globalen promoten (origin: tenant → system, tenant_key → null) | Integration |
<!-- /Quelle: Platform-Admin v1.6 -->
<!-- Quelle: Service Accounts v1.7 -->
| AK-25 | Service Account Erstellung erzeugt User mit `account_type: 'service'`, generierter E-Mail und Membership im Tenant | Integration |
| AK-26 | Service Account bekommt bei Erstellung automatisch einen API-Key (Klartext einmalig in Response) | Integration |
| AK-27 | Service Account kann sich NICHT per Passwort oder SSO anmelden (kein `password_hash`, kein AuthProvider) | Unit + Integration |
| AK-28 | Auf Mandanten-Ebene werden Service Accounts nur mit Rolle `grower` oder `viewer` erstellt (kein `lead`; wer sie anlegen darf, regelt REQ-049 §2.4) | Unit |
| AK-29 | Platform-Admin kann Service Accounts mit jeder Rolle erstellen (inkl. `lead`) | Integration |
| AK-30 | Maximal 20 Service Accounts pro Tenant (429 bei Überschreitung) | Unit + Integration |
| AK-31 | `allowed_ip_ranges` wird bei API-Key-Authentifizierung geprüft — Zugriff von nicht-erlaubter IP gibt 403 | Integration |
| AK-32 | `rate_limit_rpm` wird als individuelles Rate Limit pro Service Account angewendet | Integration |
| AK-33 | Suspendierung eines Service Accounts macht alle seine API-Keys sofort ungültig (401) | Integration |
| AK-34 | Reaktivierung eines Service Accounts stellt API-Key-Funktionalität wieder her (nicht-revoked Keys funktionieren) | Integration |
| AK-35 | Löschung (Soft-Delete) revoked alle API-Keys und setzt Memberships auf `status: 'left'` | Integration |
| AK-36 | Key-Rotation revoked den alten Key und erstellt einen neuen (Klartext einmalig in Response) | Integration |
| AK-37 | Platform Service Account kann Memberships in mehreren Tenants erhalten | Integration |
| AK-38 | `last_active_at` wird bei jedem API-Key-Zugriff des Service Accounts aktualisiert | Integration |
| AK-39 | Service Account E-Mail folgt Pattern `{slug}@service.{tenant_slug}.local` und ist UNIQUE | Unit |
| AK-40 | Service Accounts sind in der User-Auflistung (`GET /users/me/providers` etc.) nicht sichtbar — eigene Verwaltung über `/service-accounts` | Integration |
| AK-41 | `account_type` ist im JWT-Token enthalten und korrekt gesetzt (`human` oder `service`) | Unit |
<!-- /Quelle: Service Accounts v1.7 -->
<!-- Quelle: Tenant-Notfallverwaltung v1.7 -->
| AK-42 | **Gestrichen (v1.43, #2134; Status v1.46):** Verwaist-Erkennung: Tenant ohne aktive Admins wird korrekt als verwaist erkannt (`is_orphaned() == True`) | Unit + Integration |
| AK-43 | **Gestrichen (v1.43, #2134; Status v1.46):** Emergency-Admin-Ernennung nur bei verwaisten Tenants möglich (409 wenn aktive Admins vorhanden) | Integration |
| AK-44 | **Gestrichen (v1.43, #2134; Status v1.46):** Emergency-Admin-Ernennung erfordert Platform-Admin-Berechtigung (403 für Nicht-Platform-Admins) | Integration |
| AK-45 | **Gestrichen (v1.43, #2134; Status v1.46):** Emergency-Admin-Ernennung: `reason` ist Pflichtfeld (422 bei fehlendem Grund) | Unit |
| AK-46 | **Gestrichen (v1.43, #2134; Status v1.46):** Emergency-Admin-Ernennung: Ziel-User wird korrekt zum Admin befördert (bestehende Membership) oder als Admin hinzugefügt (neue Membership) | Integration |
| AK-47 | **Gestrichen (v1.43, #2134; Status v1.46):** Emergency-Admin-Ernennung: `orphaned_since` wird auf `null` zurückgesetzt | Integration |
| AK-48 | **Gestrichen (v1.43, #2134; Status v1.46):** Emergency-Admin-Ernennung: Alle aktiven Mitglieder des Tenants werden benachrichtigt | Integration |
| AK-49 | **Umgesetzt (#2105, #2123):** Tenant-Suspendierung: Alle tenant-scoped API-Requests geben 403 zurück — dieselbe Antwort wie für einen unbekannten Kurznamen, nicht die eigene Meldung aus §5a.5.3 (REQ-024 AK-48/AK-65) | Integration |
| AK-50 | **Umgesetzt mit 403 statt 400 (#1021):** Tenant-Suspendierung: Platform-Tenant kann NICHT suspendiert werden | Unit |
| AK-51 | **Umgesetzt (#2105):** Tenant-Reaktivierung: Zugriff wird sofort wiederhergestellt | Integration |
| AK-52 | **Umgesetzt (#2116):** User-Suspendierung (`PATCH /admin/platform/users/{key}`, `is_active=false`): Alle Refresh Tokens invalidiert; API-Keys werden nicht widerrufen, aber abgewiesen, solange das Konto gesperrt ist | Integration |
| AK-53 | **Nicht implementiert (#2144, MT-045):** User-Suspendierung: Platform-Admin kann sich NICHT selbst suspendieren (400) | Unit |
| AK-54 | **Gestrichen (v1.43, #2134; Status v1.46):** User-Suspendierung: Wenn User letzter Admin eines Tenants → Tenant als verwaist markiert | Integration |
| AK-55 | **Gestrichen (v1.43, #2134; Status v1.46):** Celery-Task erkennt verwaiste Tenants wöchentlich und setzt `orphaned_since` | Integration |
| AK-56 | **Registrierungsmodus (#2132, umgesetzt; Betreiberentscheidung 2026-10-04, §3.2d):** `REGISTRATION_MODE=invite_only` + `POST /auth/register` ohne gültiges E-Mail-Einladungs-Token für die Adresse → `403 REGISTRATION_NOT_ALLOWED` (gleiche Antwort für vergebene und freie Adresse, nichts geschrieben); mit Token einer offenen, gültigen E-Mail-Einladung für genau diese Adresse → `201`. Erste OIDC-Anmeldung ohne Einladung für die vom Anbieter bestätigte Adresse → Weiterleitung `?error=registration_not_allowed`, kein Konto. `closed` lehnt auch mit Einladung ab; bestehende Konten melden sich an. `REGISTRATION_ALLOWED_DOMAINS` beschränkt `open` auf die gelisteten Domains (OIDC nur mit bestätigter Adresse). `GET /mode` meldet `registration.mode`. Default `open` ändert nichts. Tests: `test_registration_mode.py` (Unit), `test_registration_mode_api.py` (API), `RegisterPage.test.tsx`, `LoginPage.test.tsx` | Unit + API + Frontend |
<!-- /Quelle: Tenant-Notfallverwaltung v1.7 -->

### Sicherheitskriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| SK-01 | Passwörter sind ausschließlich als Bcrypt-Hash (Cost 12) gespeichert | Code Review |
| SK-02 | Refresh Tokens sind als SHA-256-Hash gespeichert (Klartext nie in DB) | Code Review |
| SK-03 | OAuth-state-Parameter verhindert CSRF (Redis, 5 Min TTL) | Integration |
| SK-04 | PKCE (Proof Key for Code Exchange) wird für alle OAuth-Flows verwendet | Integration |
| SK-05 | Passwort-Reset-Request gibt keinen Hinweis ob E-Mail existiert (Enumeration-Schutz) | Integration |
| SK-06 | Client Secrets und Provider-Tokens sind AES-256-verschlüsselt in der Datenbank | Code Review |
| SK-07 | Alle Auth-Endpunkte haben Rate Limiting (100/min pro IP) | Integration |
| SK-08 | Access Token enthält keine sensitiven Daten (kein Passwort-Hash, keine Provider-Tokens) | Unit |
<!-- Quelle: Widerspruchsanalyse W-004 -->
| SK-09 | **Token-Family bei Login:** Jeder erfolgreiche Login (Local oder OAuth) erzeugt ein Refresh-Token mit neuer `family_key` (UUID4). Bei Token-Rotation erbt der Nachfolger die `family_key` vom Vorgänger. | Unit |
| SK-10 | **Grace-Window-Idempotenz:** `POST /auth/refresh` mit einem bereits rotierten Refresh-Token ≤ 60s nach Rotation und passender `device_id` liefert den bereits ausgestellten Nachfolger zurück (KEIN neues Token-Paar, KEINE Family-Sprengung). | Integration |
| SK-11 | **Replay-Detection außerhalb Grace:** `POST /auth/refresh` mit einem Token, das vor mehr als 60s rotiert wurde, sprengt die ganze Family (alle Tokens mit gleicher `family_key` werden revoked) und liefert HTTP 401 mit `error_code='refresh_replay_detected'`. | Integration |
| SK-12 | **Replay-Detection bei Device-Mismatch:** Auch innerhalb 60s führt eine abweichende `device_id` zu Family-Sprengung und HTTP 401. | Integration |
| SK-13 | **Family-Isolation Multi-Device:** Family-Sprengung von F1 (Tablet-Login) hat keinen Einfluss auf F2 (Desktop-Login desselben Users) — Desktop-Session bleibt aktiv. | Integration |
| SK-14 | **Telemetrie:** Bei jedem Replay-Event wird structlog-Event `auth.refresh_replay_detected` mit `family_key`, `user_key`, `reason`, `token_age_seconds` geloggt; Counter `kp_auth_refresh_replay_total{reason=...}` wird inkrementiert. | Integration |
| SK-15 | **Hard Cutover v1.9:** Beim Deployment von v1.9 werden alle bestehenden Refresh-Tokens via `cutover_refresh_tokens_v19()` revoked. Nach Deployment werden alle Auth-Endpunkte mit altem Refresh-Token mit 401 abgelehnt. | Integration |
<!-- /Quelle: Widerspruchsanalyse W-004 -->

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | Login-Seite zeigt dynamisch alle aktivierten SSO-Provider als Buttons | E2E |
| FK-01a | Login-Seite zeigt Checkbox „Angemeldet bleiben" unterhalb des Passwort-Felds, Standard: nicht aktiviert | E2E |
| FK-02 | Nach erfolgreichem Login wird User zum Dashboard redirected | E2E |
| FK-03 | 401-Response löst automatischen Token-Refresh aus; bei Refresh-Fehler → Redirect zu /login | Integration |
| FK-04 | AccountSettingsPage zeigt verknüpfte Provider und aktive Sessions korrekt an | E2E |
| FK-05 | Account-Löschung erfordert Passwort-Bestätigung im Dialog | E2E |
| FK-06 | Tab "API-Keys" zeigt Liste aller eigenen Keys mit Label, Prefix, Tenant-Scope, Erstellt, Letzter Zugriff | E2E |
| FK-07 | Neuen API-Key erstellen zeigt Klartext-Key einmalig im Dialog mit Copy-Button und Warnhinweis | E2E |
| FK-08 | Key revoken erfordert Bestätigungs-Dialog und entfernt Key aus der Liste | E2E |
| FK-09 | OIDC-Provider-Seite (`/admin/oidc-providers`, nur Plattform-Admin): Anlegen, Löschen und jede Änderung außer Anzeigename und Icon verlangen den Step-up für `oidc_provider_change` (Ziel: Schlüssel bzw. `new:<slug>`); Anzeigename und Icon speichern ohne Dialog; das Client-Secret wird nie angezeigt | TC-023-077 bis 079 |

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| NFR-001 | Architektur-Layer (erweitert §6.1 JWT-Skizze zur vollständigen Spezifikation) |
| NFR-006 | API-Fehlerbehandlung (401 UNAUTHORIZED, 403 FORBIDDEN) |
| NFR-007 | Retry-Logik (Auth-Fehler sind nicht retryable) |

### Wird benötigt von:

| REQ | Bezug |
|-----|-------|
| REQ-024 | Mandantenverwaltung — baut auf User-Entität und JWT-Token auf |
| REQ-006 | Task-Zuweisung an User (zukünftige Erweiterung) |
| REQ-015 | Kalenderansicht — "vorbereitet für JWT-Auth" |

### Neue Infrastruktur-Abhängigkeiten:

| Komponente | Zweck |
|------------|-------|
| Redis | OAuth-State-Speicherung (5 Min TTL), Rate Limiting |
| Fernet/AES-256 | Verschlüsselung von Provider-Secrets und -Tokens |

### E-Mail-Service (Adapter-Pattern):

Der E-Mail-Versand wird über ein **abstraktes Interface** entkapselt (analog zum bestehenden Adapter-Pattern für GBIF/Perenual in REQ-011):

```python
# domain/interfaces/email_service.py
class IEmailService(ABC):
    @abstractmethod
    async def send_verification_email(self, to: str, token: str, display_name: str) -> None: ...
    @abstractmethod
    async def send_password_reset_email(self, to: str, token: str) -> None: ...
    @abstractmethod
    async def send_invitation_email(self, to: str, tenant_name: str, inviter_name: str, token: str, role: str) -> None: ...
```

Konkrete Implementierungen (austauschbar, nicht Teil dieser REQ):
- `SmtpEmailAdapter` — Direkter SMTP-Versand (`aiosmtplib`)
- `ResendEmailAdapter` — Transactional API (Resend)
- `ConsoleEmailAdapter` — Entwicklungsumgebung (loggt E-Mails auf stdout)

Die Wahl der konkreten Implementierung erfolgt per Konfiguration (`EMAIL_ADAPTER=smtp|resend|console`). Für die Entwicklungsumgebung genügt der `ConsoleEmailAdapter`.

## 8. Neue Python-Dependencies

| Paket | Version | Zweck | Status im Stack |
|-------|---------|-------|----------------|
| `authlib` | `>=1.3.0` | JWT (HS256), OAuth2 Client, OIDC Discovery, PKCE | **Neu** — ersetzt `python-jose` aus NFR-001 §6.1 |
| `passlib[bcrypt]` | `>=1.7.4` | Passwort-Hashing (Bcrypt, Cost 12) | **Neu** — in NFR-001 §6.1 referenziert, aber nicht installiert |
| `slowapi` | `>=0.1.9` | Rate Limiting (nutzt Redis als Backend) | **Neu** |
| `cryptography` | `>=42.0` | Fernet-Verschlüsselung für Provider-Secrets | **Neu** |
| `httpx` | `>=0.28.0` | HTTP-Client für GitHub-API, HIBP-Check | **Bereits vorhanden** |
| `redis` | `>=5.2.0` | OAuth-State, Rate Limiting, Token-Blocklist | **Bereits vorhanden** (Celery-Broker) |

## 9. Scope-Abgrenzung

**In Scope:**
- Lokale Benutzerkonten (E-Mail + Passwort)
- OAuth2/OIDC mit Google, GitHub, Apple (benannt) + generische OIDC-Provider
- JWT Access/Refresh Token Lifecycle mit Rotation
- Benutzerprofil-Verwaltung (Name, Avatar, Locale, Timezone)
- Passwort-Reset per E-Mail
- Account-Linking (mehrere Auth-Methoden pro User)
- Login-Throttling und Rate Limiting
- Session-Verwaltung (aktive Geräte, Logout-All)
- OIDC-Provider-Konfiguration durch System-Admin
<!-- Quelle: Service Accounts v1.7 -->
- Service Accounts (`account_type: 'service'`) als nicht-interaktive Konten für Third-Party-Systeme
- Tenant-scoped und Platform-scoped Service Accounts
- API-Key-only Authentifizierung für Service Accounts (kein Passwort, kein SSO)
- IP-Allowlist und individuelles Rate Limit pro Service Account
- Service Account Lifecycle (erstellen, suspendieren, reaktivieren, löschen, Key-Rotation)
- 15 neue API-Endpoints für Service Account Verwaltung
<!-- /Quelle: Service Accounts v1.7 -->
<!-- Quelle: Tenant-Notfallverwaltung v1.7 -->
- Tenant-Notfallverwaltung: Emergency-Admin-Ernennung bei verwaisten Tenants
- Tenant-Suspendierung/Reaktivierung durch Platform-Admin
- User-Suspendierung/Reaktivierung durch Platform-Admin
- Verwaist-Erkennung via Celery-Task (wöchentlich)
- 7 neue Admin-API-Endpoints (`/admin/tenants/{key}/emergency-admin`, `/suspend`, `/reactivate`, `/admin/users/{key}/suspend`, `/reactivate`, `/admin/tenants/{key}/members`)
<!-- /Quelle: Tenant-Notfallverwaltung v1.7 -->

**Nicht in Scope (bewusst ausgeklammert):**
- Mandanten/Tenants und Rollenkonzept → REQ-024
- 2-Faktor-Authentifizierung (TOTP, WebAuthn) → zukünftige Erweiterung
- Social-Login-Profilsynchronisation (regelmäßiger Name/Bild-Abgleich) → zukünftig
- SAML 2.0 → Enterprise-Segment, aktuell nicht priorisiert
- E-Mail-Template-Customization → Standard-Templates genügen initial
- User-Administration durch Nicht-Admins (Nutzer können nur ihr eigenes Profil verwalten)
<!-- Quelle: Service Accounts v1.7 -->
- OAuth2 Client Credentials Grant für Service Accounts → API-Keys sind einfacher und ausreichend
- Service Account Impersonation (ein SA agiert im Namen eines menschlichen Users) → Sicherheitsrisiko, nicht unterstützt
- Automatische Service Account Erstellung bei Third-Party-Integration → immer manuell durch Admin
- Service Account Audit-Log (detailliertes Zugriffsprotokoll) → zukünftig, nach allgemeinem Audit-Log
<!-- /Quelle: Service Accounts v1.7 -->
<!-- Quelle: Issue #1118 -->
- Persistiertes Audit-Log der QR-Gerätekopplung (§3.8) → **bewusst nicht** eingeführt: die Prüfspur sind structlog-Events (`device_pairing_created` / `device_pairing_redeemed` / `device_pairing_redeem_failed`), kein ArangoDB-Datensatz und keine neue Collection. Ein persistiertes Zugriffsprotokoll bleibt an das allgemeine Audit-Log gebunden (siehe Service-Account-Audit-Log oben), damit dessen Zurückstellung kohärent bleibt.
<!-- /Quelle: Issue #1118 -->
