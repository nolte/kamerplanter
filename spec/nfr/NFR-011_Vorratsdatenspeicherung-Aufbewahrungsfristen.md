# NFR-011: Vorratsdatenspeicherung & Aufbewahrungsfristen

```yaml
ID: NFR-011
Titel: Vorratsdatenspeicherung & Aufbewahrungsfristen
Kategorie: Datenschutz & Compliance
Unterkategorie: Retention Policy, Datensparsamkeit, DSGVO
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python, Celery, ArangoDB, TimescaleDB, Valkey
Status: Genehmigt
Priorität: Kritisch
Version: 1.33 (R-27: Anbauplanung aus REQ-054); 1.32 (R-25/R-26: Pflegeprotokoll und Plan-Audit aus REQ-053); 1.31 (Altbestand der Home-Assistant-Messwerte unter leerem Mandantenschlüssel: Befehl, Trockenlauf, Bestätigung, #2077); 1.30 (Messungen nach Löschung: kein Wiederanlegen, #1944; Beitritt gegen Löschung: kein Restfenster, #1924); 1.29 (Durchsetzungsstand aller Fristen benannt, Task-Tabelle gegen den Beat geprüft, #1800); 1.28 (R-02: abgebrochene lokale Registrierungen — Trockenlauf, Freigabe durch den Betreiber, #2010); 1.27 (Statustabelle §2.1/§3.1 an den Code angeglichen, R-06-Zähler fail-safe, #1955/#1800); 1.26 (Protokoll-Bereinigung: eine Redaktion unabhängig von der Schreibweise, #2020 #2019 #1927 #2054 #1926)
Datum: 2026-04-27
Tags: [dsgvo, retention, datensparsamkeit, loeschfristen, compliance, cross-cutting]
Abhängigkeiten: [REQ-023, REQ-024, REQ-025 v1.1, NFR-001]
Betroffene Module: [ALL]
Security-Review-Referenz: SEC-K-001, SEC-K-002, SEC-K-005
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.33 | 2026-10-04 | **REQ-054 v1.1 O-08 (Betreiberentscheidung):** R-27 `planning_requests`/`planting_proposals` — mit dem Request, verworfene Vorschläge 1 Jahr, angenommene 5 Jahre; nicht implementiert. |
| 1.32 | 2026-10-04 | **REQ-053 v1.2 (Security-Review SR-005, Betreiberentscheidung):** Zwei neue Zeilen für die Collections der Garten-/Beetplanung — R-25 `care_events` (Pflegeprotokoll: Nutzer-Keys, Freitexte, Fotos; **5 Jahre** ab `performed_at`, danach Anonymisierung der Personenfelder und Löschung der Freitexte/Fotos, Fachdaten bleiben für die Fruchtfolge; PflSchG-Vorbehalt für Pflanzenschutz-Ereignisse wie R-23/`treatment_applications`) und R-26 `garden_plan_audit` (1 Jahr, Hard-Delete). Beide sind bis zur Umsetzung von REQ-053 Welle 4 **nicht implementiert**. |
| 1.31 | 2026-10-04 | **#2077 Altbestand:** Messwerte der Home-Assistant-Abfrage aus der Zeit vor #1944 stehen unter `tenant_key = ''`; `delete_by_tenant` / `delete_by_sensor` erreichen sie nicht (§2.2 Absatz „Altbestand unter leerem Mandantenschlüssel"). Betreiberentscheidung: nur Zeilen **gelöschter** Sensoren dürfen entfallen, nur nach ausdrücklicher Bestätigung der Zahl aus einem Trockenlauf; Zeilen bestehender Sensoren werden gezählt und nicht angefasst. Umgesetzt als Betreiberbefehl `python -m app.migrations.purge_orphan_ha_readings` (nichts läuft automatisch). Die Messung auf einer echten Installation steht aus. |
| 1.30 | 2026-10-04 | **#1944:** Nach einer Sensor- oder Mandantenlöschung entsteht keine Zeitreihe neu — eine Messung, die einen gelöschten Besitzer trifft, wird abgewiesen bzw. zurückgenommen (§2.2 Absatz „Kein Wiederanlegen", AK-16 erweitert); die Home-Assistant-Abfrage speichert unter dem Mandanten des Sensor-Elternteils statt unter `''`. **#1924:** AK-PT-05 — das „Restfenster" ist geschlossen: ein Beitritt, der mit der erneuten Mitgliederprüfung zusammenfällt, endet in genau einem Ausgang (Mitgliedschaft bleibt und der Mandant wird erhalten, oder sie wird abgelehnt und der Mandant gelöscht). Siehe REQ-025 v1.28 AK-IE-06/AK-IE-07. |
| 1.29 | 2026-10-04 | **#1800 Durchsetzungsstand (Betreiberentscheidung: genau vier Fristen, alle bereits seit #1912 durchgesetzt):** R-04 (Consent Records, 3 Jahre nach Widerruf), R-04a (Consent-IP, Anonymisierung inkl. Zurücksetzen von `ip_anonymized_at` bei erneuter Einwilligung), R-07 (E-Mail-Änderungsanfragen, Hard-Delete nach 24 h) und R-12 (Einladungen, Hard-Delete 30 Tage nach Ablauf) laufen über die Beat-Tasks aus §3.1 und lesen ihre `RETENTION_*`-Einstellungen; weitere Fristen kamen nicht hinzu. **Weiter nicht implementiert:** R-14 (Sensor-Stufen, `SENSOR_*` ohne Leser), R-15 (Aktor-Logs, kein Speicher) und die Prometheus-Metriken (§3.3, AK-06) — Roadmap-Ziel „Retention-Observability". Eine Frist, zu der diese NFR schweigt, gilt als **Vorschlag, DSB-Prüfung offen**, bis sie hier steht; der Code erfindet keine. Zwei Guards halten die Aussage fest: Jedes `retention_*`-Setting hat einen lesenden Code (ein Setting ohne Leser ist wirkungslos), und die Task-Tabelle in §3.1 nennt genau die `retention.*`-Beat-Tasks. |
| 1.28 | 2026-10-04 | **#2010 R-02 Trockenlauf (Betreiberentscheidung 2026-10-03: erst zählen, dann löschen):** Gemessen gegen eine echte ArangoDB: `AuthService.register` schreibt für **jede** lokal registrierte Person eine `LOCAL`-Zeile in `auth_providers`, und der R-02-Selektor zählte *jede* Anbieterzeile als „verknüpft" — er erreichte also nur Konten ohne Anbieterzeile (Seeds, Importe, Altbestand). Eine abgebrochene lokale Registrierung blieb unbegrenzt liegen, entgegen R-02 und REQ-023 AK-17. **Jetzt:** `cleanup_unverified_accounts` zählt bei jedem Lauf (`local_registrations_pending`, Warnzeile `unverified_local_registrations_pending`), wie viele abgebrochene lokale Registrierungen die freigegebene Bereinigung löschen würde, und löscht **keine**, solange `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED` nicht gesetzt ist (Default `false`). Die Freigabe ist die Entscheidung des Betreibers nach Kenntnis der Zahl. Freigegeben, verengt `get_unverified_before(..., include_local_registrations=True)` den Ausschluss auf föderierte Anbieter (`provider != 'local'`) und schließt Servicekonten aus; der `held_undated`-Zähler benutzt dasselbe Prädikat. Alle bisherigen Ausschlüsse bleiben (nie bestätigt, kein `email_verified_lowered_at`, kein `last_login_at`, Alter lesbar und über der Frist); `erase_account_now(origin="unverified_cleanup")` prüft `last_login_at` beim Löschen erneut. **Fail-safe:** schlägt der Zähler fehl, bleibt es beim engen Selektor — nie Ausweitung auf einem Fehlerpfad. Neue Einstellung in §4 (bool, ohne Obergrenze). R-02 in §2.1 nennt jetzt, was der Selektor tut; die öffentliche Aufbewahrungsübersicht (`retention_summary`) führt R-02 bis zur Freigabe als `partial` mit Hinweis, danach als `enforced`. |
| 1.27 | 2026-10-04 | **#1955/#1800 Statustabelle:** §2.1 und §3.1 nennen den tatsächlichen Stand. R-04, R-04a, R-07 (Hard-Delete der unbestätigten Anfrage), R-07b und R-12 (Hard-Delete 30 Tage nach Ablauf) sind seit #1912 durchgesetzt und stehen jetzt als **Umgesetzt**; §3.1 führt R-04 (`retention.purge_expired_consent_records`, 04:35) und R-04a (`retention.anonymize_consent_ips`, 04:40) und nennt R-07b beim stündlichen Lauf. Weiter **nicht implementiert** bleiben R-14, R-15 und die Prometheus-Metriken (§3.3), Roadmap-Ziel „Retention-Observability". **R-06-Held-Zähler (#1955):** `count_completed_without_tombstone_before` läuft wie die übrigen Held-Zähler über `held_undated_count`; ein fehlschlagender Zähler lässt den Task nicht scheitern, das Ergebnis meldet dann `held_without_tombstone: null` (unbekannt, nicht null). Ein Guard hält fest, dass jedes `retention_*`-Setting einen lesenden Code hat und kein Zähler der Retention-Pfade ungeschützt läuft. |
| 1.26 | 2026-10-04 | **Protokoll-Bereinigung unabhängig von der Schreibweise (#2020, #2019, #1927, #2054, #1926).** (1) **#2020** L-1: Der Kontoschlüssel-Guard behandelt Akteur-Schlüsselwörter und -Namen (`*ed_by`: `contributed_by`, `created_by`, `requested_by` …) wie `user_key`. L-3/L-8: Ein Mandantenschlüssel *im Text* — als Erasure-Record-Schlüssel `ter_<Mandant>` oder als Objektschlüssel/Präfix `t/<Mandant>/…` — wird in jeder Senke durch `ten_…` ersetzt; gemessen: Celerys Zeile `Task … succeeded in …` trug den Rückgabewert des Mandanten-Lösch-Tasks (`{'record_key': 'ter_<Mandant>', …}`) im Klartext (Zeile und `extra['data']['return_value']`); der Task gibt jetzt die Protokollform zurück. (2) **#2019** L-1: Die 67 Log-Aufrufe, die einen rohen `tenant_key=` ohne Subjekt trugen, schreiben `tenant=ten_…`; der Guard hat keine Subjekt-Bedingung mehr. Dashboards oder Alarme, die auf `tenant_key=` dieser Zeilen filtern, müssen auf `tenant=` umgestellt werden. (3) **#1927** L-6: Die Pfad-Bereinigung maskiert zusätzlich Apprise-native URLs (`slack://…`, `pover://…`, `tgram://…`: alles nach dem Schema; `gotify://`, `matrix://`, `ntfy://`: der Server bleibt, der Pfad entfällt — die Schemata sind die Positivliste der Apprise-Zielprüfung), eine Punkt-Kette (`<Body>.<Signatur>`, JWT) als Ganzes, sobald ihr erstes Segment ein Token ist, und weitere Token-Alphabete in Segmenten ab 32 Zeichen aus Buchstaben und Ziffern (base36, base32, gemischte Schreibung ohne Ziffer). Gemessen mit dem echten `apprise`-Paket (kein Bestandteil des Backend-Images): Apprise kürzt jede URL in seinen eigenen Zeilen selbst (`slack://T...h/B...h/a...x//`), keine Log-Zeile der Anwendung nennt eine Apprise-URL; auf `DEBUG` schreibt Apprise aber die Nutzlast (`{'token': …, 'user': …}`), deshalb steht der Logger `apprise` wie `httpx` auf `WARNING`. (4) **#2054** L-4: Die Kürzung gilt auch für Logger von Drittanbietern, die den Client nennen: `slowapi` schrieb bei jeder abgelehnten Anfrage (429) `ratelimit <Limit> (<Schlüssel>) exceeded at endpoint: <Route>` mit der **vollen Client-Adresse** als Schlüssel (gemessen: `ratelimit 1 per 1 minute (203.0.113.77) exceeded at endpoint: /probe`); ein Filter auf dem Logger `slowapi` kürzt jede Adresse in seinen Argumenten (R-03) und maskiert einen Schlüssel, der keine Adresse ist. (5) **#1926** L-8: Die Nebendienste inference-service und knowledge-service übergeben `init_error_tracking` nicht mehr `redact_text=None`, sondern die gemeinsame formbasierte Bereinigung aus `kp_errortracking` und installieren die drei Hooks für unbehandelte Ausnahmen; Schlüssel und Werte von `extra`/`tags`/`contexts` laufen durch die Text-Bereinigung. Gemessen mit dem echten SDK: Passwort, API-Schlüssel, Adresse und Bot-Token eines Fehlertexts erreichten das Ereignis und stderr unverändert. |
| 1.25 | 2026-10-03 | **#2010 (Betreiberentscheidung):** Die Bereinigung abgebrochener lokaler Registrierungen wird zuerst nur als **Trockenlauf** gebaut (zählt, löscht nichts); der echte Lauf braucht die ausdrückliche Freigabe des Betreibers nach Kenntnis der Zahl. R-02 bleibt bis dahin unverändert. |
| 1.24 | 2026-10-03 | **#1989 L-1 (Mandanten-Referenz, Rest von #1928):** Die elf im Guard eingetragenen Protokollzeilen (Benachrichtigung, Anhang-Upload, Fotoqualität, Schädlingsbilder, Tagebuch-Analyse, Referenzbild-Beitrag) tragen neben der Subjekt-Referenz `tenant=ten_…` statt des Mandantenschlüssels. Dazu kamen Schreibweisen, die der erste Guard nicht sah: die vier Zeilen von `NotificationEngine.notify`, die das Paar über einen gebundenen Logger (`logger.bind`) erben, und die No-op-Zeile des Referenzbild-Beitrags, die neben `tenant_key=` den **Kontoschlüssel im Klartext** (`contributed_by=`) trug — sie nennt jetzt keinen Beitragenden mehr. Die beiden Zusammenfassungszeilen der Speicher-Adapter auf dem Löschpfad einer Person (`storage_delete_for_user`, `storage_strip_exif_for_user`) nennen selbst kein Subjekt, stehen aber unmittelbar vor der `retention.erasure.storage_*`-Zeile mit gleichem Umfang, gleichen Zählern und `subject=`; sie tragen ebenfalls `tenant=ten_…`. Der Guard erkennt jetzt auch Positionsargumente, f-Strings, `extra={…}`/`**{…}`, Mandanten unter neutralen Schlüsselwörtern, Akteur-Schlüsselwörter (`*ed_by`), aus `log_subject` gebildete Lokale und gebundene Logger; seine Ausnahmeliste ist leer. Dashboards oder Alarme, die auf `tenant_key=` dieser Zeilen filtern, müssen auf `tenant=` umgestellt werden. |
| 1.23 | 2026-10-03 | **#1992 R-02:** Die Bereinigung unbestätigter Accounts trifft nur Konten, die **nie bestätigt** waren. Ein Administrator, der `email_verified` eines bestätigten Kontos senkt, stempelt `email_verified_lowered_at`; Selektor und Zähler `held_undated` schließen ein so vermerktes Konto aus — ebenso ein Konto mit `last_login_at` (es wurde benutzt; sichert Herabstufungen aus der Zeit vor dem Vermerk) — und `erase_account_now(origin="unverified_cleanup")` prüft es erneut. Ein Konto mit Stempel unterliegt R-02 nicht (es ist kein verlassener Registrierungsversuch). |
| 1.22 | 2026-10-02 | **#1960 R-01a:** Die Benachrichtigung der anderen Mitglieder eines persönlichen Mandanten (AK-PT-03) ist am Löschauftrag vermerkt (`members_notified_at`, `members_notified_count`, `members_notice_failures`). Der tägliche Lauf `retention.execute_scheduled_erasures` stellt eine nicht versandte Benachrichtigung zu, **bevor** er hart löscht; ein Löschauftrag aus der Zeit vor #1824 (ohne Vermerk) wird beim ersten Sehen benachrichtigt und frühestens `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` (Standard 7, Obergrenze 7) Tage danach gelöscht. Neues Setting in §4 (Tabelle der Obergrenzen). Eine Benachrichtigung, die die ganze Wartezeit lang nicht zustellbar ist, hält die Löschung nicht auf (Art. 17 geht vor). Die Sofortlöschung durch einen Administrator wartet nie (#1961). |
| 1.21 | 2026-10-02 | **#1925/#1928/#1966 (Protokoll- und Tracker-Reste):** (1) L-8: Das Fehler-Tracker-Ereignis trägt als Anfrage-URL und Transaktionsname nur das **Routenmuster** des Frameworks (`/api/v1/t/{tenant_slug}/attachments/{key}/…`), nie den Rohpfad — dieser enthält das Download-Token (das *ist* die Berechtigung) und den aus dem Anzeigenamen abgeleiteten Mandanten-Kurznamen. Ohne Muster (404, Fehler vor dem Routing) reduziert der Dienst den Pfad (`loggable_path`, L-7); Query-String und Fragment entfallen. Methode und Host bleiben. (2) L-1: Der Mandantenschlüssel steht in Protokollzeilen nicht im Klartext neben einer Subjekt-Referenz — er hängt an den pseudonymisierten Aufbewahrungszeilen und verbindet sonst Pseudonym und Mandant (bei einem persönlichen Mandanten: Eigentümer). An seiner Stelle steht `tenant=ten_…`, ein HMAC-SHA256 mit `LOG_PSEUDONYM_SALT` und eigenem Zweck-Label `log-tenant`; auch der Erasure-Record-Schlüssel `ter_<Mandant>` erscheint nur als `ter_ten_…`. Umgesetzt für die Einladungs- und Mandantenlösch-Zeilen des `TenantService` sowie die Speicherbereinigung der Kontolöschung; elf weitere Zeilen sind im neuen Guard als Rest eingetragen (#1989). (3) L-3: Objektschlüssel `t/<Mandant>/…` erscheinen in den Zeilen beider Speicher-Adapter (auch bei jedem Löschen) nur mit der Mandanten-Referenz; Kategorie, Datumsteil, ULID und Endung bleiben zur Fehlersuche. Dashboards oder Alarme, die auf den Rohpfad im Tracker-Ereignis oder auf `tenant_key=`/`key=t/<Mandant>/…` in diesen Zeilen filtern, müssen auf `tenant=` bzw. das Routenmuster umgestellt werden. |
| 1.20 | 2026-10-02 | **#1834 Objekt-Rekonziliation (Auffangnetz, keine neue Frist):** Bytes im Object Store, deren Datensatz ohne sie gelöscht wurde, erreichte bisher keine Aufbewahrungsregel — jede Löschung fragt den `attachments`-Katalog. `reconcile_orphaned_storage_objects` (NFR-013 §6.6, REQ-025 AK-OS-10) läuft täglich 04:10, im ersten Release nur berichtend (`STORAGE_RECONCILE_DELETE_ENABLED=false`); die Marge `STORAGE_RECONCILE_MIN_AGE_HOURS` (24, Untergrenze 1) ist ein Sicherheitsabstand zur Upload-Reihenfolge, keine Aufbewahrungsfrist. Bericht und Logs tragen nur Zahlen (R-06: ein Log hat keine eigene Frist). |
| 1.19 | 2026-10-02 | **Erasure-together umgesetzt (#1824):** AK-PT-03 — ein persönlicher Mandant wird bei Kontolöschung auch mit weiteren aktiven Mitgliedern gelöscht; die Mitglieder werden beim Löschantrag benachrichtigt (ohne Daten der löschenden Person). AK-PT-02: `retained_other_members` wird nicht mehr geschrieben, ein Spätbeitritt ergibt `retained_late_joiner`. AK-PT-04/05 tragen den Stand „implementiert" (#1825, schon seit REQ-025 v1.20) nach. Siehe REQ-025 v1.24. |
| 1.18 | 2026-10-02 | **Folgearbeiten zu #1806 (#1946):** (1) §4 / **AK-14** Die drei seit #1912 durchgesetzten, bisher unbegrenzten Fristen R-04 (`RETENTION_CONSENT_RETENTION_YEARS`), R-04a (`RETENTION_CONSENT_IP_ANONYMIZATION_DAYS`) und R-12 (`RETENTION_INVITATION_RETENTION_DAYS`) bekommen eine Obergrenze in Höhe ihres NFR-Default-Werts — **3 Jahre / 7 Tage / 30 Tage** (Betreiberentscheidung, vom orchestrierenden Lauf im Auftrag des Betreibers unter ausdrücklich genanntem Standardwert getroffen; ersetzt die in v1.17 genannte „engere Lesart ohne Obergrenze"). Dieselbe Start-Verweigerung und dieselbe wertfreie Meldung wie bei den anderen sieben; `RetentionService` prüft sie im Konstruktor erneut. Damit haben zehn Settings eine Obergrenze; R-16..R-18 bleiben ohne (die gesetzliche Frist ist ihre Untergrenze). (2) §4 Der Code-Default von `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` ist jetzt 3 (Q-R12) statt 1 — Code und Spec stimmen überein. Bestehende Installationen ohne ausdrückliche Einstellung bewahren Löschnachweise damit 2 Jahre länger auf (die sichere Richtung; die Obergrenze 3 bleibt). (3) §3.1 R-02, R-03, R-11 und R-12 laufen nach der Uhr (`crontab`: 03:10, 03:20, stündlich Minute 10, 02:00 UTC) statt als fester Abstand ab dem Start des Beat-Prozesses; der Beat führt keinen persistierten Zeitplan, ein Pod-Neustart startete den Abstand neu und machte „spätestens N+1 Tage" nur wahr, solange der Pod so lange lebt. Jetzt gilt die Frist-plus-ein-Takt-Aussage der Datenschutzübersicht auch über Neustarts hinweg. (4) **AK-14b** erweitert: R-04 (`purge_expired_consent_records`, Zähler der widerrufenen Datensätze ohne lesbares `revoked_at`), R-07b (`expire_email_change_requests`, bestätigte Änderungen ohne lesbares `confirmed_at` **und** `revert_expires_at`) und der Glossar-Cache (`glossary.cleanup_expired_cache`, kein lesbares `valid_until`) melden jetzt ebenfalls `held_undated`. |
| 1.17 | 2026-10-02 | **Obergrenzen umgesetzt, Alias-Warnung, Held-Zähler (#1806, GDPR-003/-004/-008):** §4 Die Obergrenzen der sieben Settings (AK-14) sind in `Settings` als `le=` je Feld umgesetzt (Tabelle `RETENTION_CEILINGS` in `app/config/settings.py`); `RetentionService` prüft sie im Konstruktor erneut. Ein Wert oberhalb bricht das Laden der Settings ab, also Start von API und Worker; die Meldung nennt Variable und Grenzwert, nie den gesetzten Wert. Wird ein alter `PRIVACY_*`-Name gesetzt, schreibt der Start eine Warnung; sind alter und neuer Name mit verschiedenen Werten gesetzt, eine Fehlermeldung, die den gewinnenden Namen nennt (AK-14a, GDPR-008; nur Namen, nie Werte). Die Selektoren für R-02, `ai_audit_log`, `mcp_audit_log` und verwaiste Aufgabenfotos überspringen weiter einen Datensatz ohne lesbares Zeitfeld, zählen ihn aber jetzt und melden `held_undated` (AK-14b, GDPR-003). **Offen, nicht Teil dieses Eintrags:** der Code-Default von `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` ist weiter 1 statt der in §4 genannten 3 (Q-R12); die Obergrenze 3 gilt davon unabhängig. |
| 1.16 | 2026-10-02 | **#1793 Teil 3 umgesetzt (Q-O7):** `TimescaleObservationRepository.delete_by_tenant` / `delete_by_sensor` löschen in derselben Transaktion wie die Rohdaten die Buckets des Mandanten bzw. Sensors direkt aus den Materialisierungstabellen von `sensor_hourly` und `sensor_daily` (`DELETE ... WHERE tenant_key = …` [`AND sensor_key = …`]). Die in v1.13 alternativ genannte Variante „Refresh über den vollen historischen Bereich" ist **verworfen**: Ein Refresh berechnet aus den Rohdaten neu, die älteren Buckets (> 90 Tage) haben keine Rohdaten mehr und würden dabei verloren gehen — auch die **anderer** Mandanten (gemessen auf TimescaleDB 2.30.2). Neue **AK-16**. |
| 1.15 | 2026-09-30 | **#1789/#1793 umgesetzt:** R-16/R-17/R-18 werden durchgesetzt — der tägliche Task `retention.purge_expired_legal_retention_rows` (04:45 UTC) löscht eine aufbewahrte Ernte-, Behandlungs- oder Inspektionszeile, deren Frist (ab `harvest_date`/`applied_at`/`inspected_at`, je Regel aus einer eigenen Einstellung mit der gesetzlichen Frist als Untergrenze) abgelaufen ist, mitsamt Kindzeilen (`quality_assessments`, `yield_metrics`) und jeder Kante, die sie berührt (ADR-001). **Engere Lesart (#1789):** Gelöscht werden nur Zeilen, deren Mandant nicht mehr existiert — die Zeilen eines bestehenden Mandanten sind dessen eigene Aufzeichnungen, für die §2.3 nur eine Mindest-, keine Höchstfrist nennt. R-06a wird durchgesetzt (`retention.purge_expired_tenant_erasure_records`, 04:50 UTC). **Engere Lesart (R-06a):** Ein Nachweis, dessen Löschung keine R-16..R-18-Zeile aufbewahrt hat, bleibt bis zur 5-Jahres-Deckelung erhalten, statt in der Nacht nach der Löschung zu verschwinden. §3.1, §4 und die Umsetzungsvermerke in §2.2/§2.3 nachgeführt. |
| 1.14 | 2026-09-30 | **#1879/#1880/#1891:** L-6 deckt Zugangsdaten im URL-*Pfad* ab (Telegram-Bot-Token, Discord-/Slack-Webhook-Token, Geräte-Token eines Push-Endpunkts), auch in urllib3s Retry-Warnung und in Ausnahmetexten; die Push-An- und -Abmeldung protokolliert nur den Host des Push-Dienstes. L-8 gilt auch für Ausnahmen ohne Protokoll-Record (`sys.excepthook`, `threading.excepthook`, `sys.unraisablehook`) und für das Fehler-Tracker-Ereignis (Ausnahmetexte, Log-Eintrag, Breadcrumbs; lokale Variablen werden nicht übertragen). |
| 1.13 | 2026-09-26 | **Datenschutzplan-Entscheidungen, Batch 4–6 (#1806, #1800, #1793):** §3.4 Die Log-Pipeline-Frist ist entschieden statt offen: 30 Tage für Anwendungs- und Zugriffsprotokolle, Rotation löscht ältere Zeilen (Q-R3 — bestätigt den bisherigen Vorschlag, der Text trug nur noch die Hedge-Formulierung). §4 Jede über Settings konfigurierbare Frist bekommt eine Obergrenze in Höhe ihres eigenen NFR-Default-Werts; ein höherer Wert lässt Backend und Worker nicht starten (Q-R9, GDPR-004, neue Spalte „Obergrenze", **AK-14**). R-01 (Betreiberentscheidung, GDPR-009): die 90-Tage-Gnadenfrist bis zum Hard-Delete ist gegen Art. 12(3)/17(1) begründet dokumentiert — die Löschzusage wirkt sofort durch den Soft-Delete, die Frist ist Aufbewahrung, keine Antwortverzögerung (Q-R11). R-06 (Auskunfts-/Betroffenenrechte-Löschaudit, `erasure_requests`) auf **3 Jahre** verlängert — §195 BGB, eigenständiger Wert, **nicht** an die tenant-gebundene R-06a-Formel (Batch 1-3, v1.12) gekoppelt (Q-R12, GDPR-010, #1793). §2.2 R-14/ADR-003 (differenzierte Sensor-Retention) und R-15/AK-06 (Aktor-Logs, Retention-Metriken) sind als benanntes Roadmap-Ziel **„Retention-Observability"** markiert — vollständige Umsetzung ist außerhalb des Umfangs eines einzelnen PRs (Q-O5, Q-O6, #1800). TimescaleDB Continuous Aggregates: Tenant- und Sensor-Löschung entfernen jetzt gezielt auch die aggregierten Buckets jeden Alters, nicht nur das Rohdaten-Fenster (Q-O7, #1793). |
| 1.12 | 2026-09-26 | **Datenschutzplan-Betreiberentscheidungen, Batch 1-3 (#1789, #1793, #1800, #1806, #1824, #1825; Umsetzung folgt in eigenen PRs, dieser Eintrag ist reine Spec-Änderung).** **Q-R1/Q-R2 (#1789):** R-16/R-17/R-18 laufen bis zu ihrem ursprünglichen Fristende weiter, auch wenn der Mandant oder das Konto vorher gelöscht wird — §2.3 neuer Absatz. **Q-R4 (#1793):** neue Regel **R-06a** — `tenant_erasure_records` wird bis zum längsten noch laufenden Fristende der unter Q-R1 zurückgehaltenen Zeilen desselben Mandanten aufbewahrt, gedeckelt auf 5 Jahre. **Q-R5 (#1800, echter Widerspruch R-04 vs. §5):** §5 nannte Consent Records fälschlich als „sofort löschbar"; R-04 verlangt seit v1.0 3 Jahre Aufbewahrung nach Widerruf. Klargestellt: Bei Kontolöschung vor Fristablauf wird der Consent Record pseudonymisiert (Tombstone-Hash, R-06-Analogie) statt gelöscht; §5 Punkt 1 und Punkt 3 angepasst, §3.1.3-Verweis in REQ-025 ergänzt. **Q-R6 (#1800):** neue Regel **R-04a** — IP-Adresse eines Consent Records wird 7 Tage nach Aufzeichnung anonymisiert (R-03-Analogie), zurückgesetzt bei erneuter Einwilligung. **Q-R7 (#1800):** R-07 (unbestätigte E-Mail-Änderungsanfrage, Hard-Delete nach 24h) bleibt wie spezifiziert (weiterhin nicht durchgesetzt, #1800); ergänzend neue Regel **R-07b** — eine bestätigte Anfrage wird nach Ablauf des R-07a-Rückgängig-Fensters vollständig hart gelöscht, nicht nur die Rückgängig-Felder. **Q-R8 (#1800):** R-12 (Einladungen, 30 Tage nach Ablauf, Hard-Delete) ist bereits korrekt spezifiziert — reine Betreiberbestätigung des Zielverhaltens, kein Textwechsel nötig; die Umsetzung bleibt offen. **Q-E1/Q-E5 (#1824):** AK-PT-02/AK-PT-03 ersetzt — ein persönlicher Mandant der Person wird jetzt **immer** zusammen mit dem Konto gelöscht, auch wenn er weitere aktive Mitglieder hat (nicht mehr `retained_other_members`); die Regel gilt nur für `tenant_type: personal` (Q-E5, Statusquo-Geltungsbereich jetzt als bewusstes Design bestätigt). Diese Entscheidung **ersetzt** die in v1.8 dokumentierte Retained-Entscheidung. **Q-E6/Q-E7 (#1825):** siehe REQ-025 AK-IE-06/AK-IE-07 — kein eigener Retention-Eintrag hier, da Verfahrensregeln, keine Frist. **Q-T6 (#1824):** siehe REQ-025 §4.2/AK-FK-06 (Vorschau-Anzeige vor Bestätigung der Kontolöschung). **Q-O2 (#1790):** neue, noch nicht umgesetzte Anforderung — Mandantenlöschung erhält eine Gnadenfrist analog zu R-01, siehe REQ-024 §1a.2/AK-52. |
| 1.11 | 2026-09-26 | **#1812:** Die Log-Pseudonyme (`subject=`, `email_sha256=`) sind mit einem eigenen, rotierbaren `LOG_PSEUDONYM_SALT` verschlüsselt statt mit `ERASURE_TOMBSTONE_SALT` (L-1, L-2); API und Worker starten in Produktion nicht ohne ihn (L-5); neuer Absatz zur Rotation. Betreiberentscheidung vom 2026-09-26. |
| 1.10 | 2026-09-26 | **#1828/#1830/#1831/#1832:** L-1 nennt zusammengesetzte Schlüssel (Benachrichtigungs-Dedup- und Gruppen-Schlüssel), die den Kontoschlüssel enthalten. L-6 schließt das Präfix eines neu erzeugten API-Schlüssels aus. L-8 gilt nun unabhängig davon, welche Handler es wann gibt (Redaktion beim Erzeugen jedes Records), auch für Celerys Retry-Zeile und die an Celery-Records angehängten Task-Daten; L-9 neu: Redaktion vor dem Lifespan, Konfigurationsfehler ohne Wert. |
| 1.9 | 2026-09-25 | **#1795/#1796:** §3.4 um L-6 bis L-8 erweitert: keine API-Schlüssel und Einmal-Tokens in einer Log-Senke (httpx/httpcore/urllib3 auf WARNING mit Query-Filter in API und Worker, Console-Mail-Adapter ohne Link außerhalb von `DEBUG`), redigierte Zugriffsprotokolle von uvicorn und nginx, redigierte Tracebacks in beiden Prozessen. L-3 nennt zusätzlich URL-Userinfo und Fragmente; der Offen-Hinweis in L-4 entfällt. Ein eigener, rotierbarer Log-Salt ist eine offene DSB-Entscheidung (#1812). |
| 1.8 | 2026-09-25 | **#1788 Persönlicher Mandant bei Kontolöschung:** Die Kontolöschung behielt den bei der Registrierung angelegten persönlichen Mandanten samt Standorten, Pflanzen, Tagebuch und Aufgaben; nur Eigentümer, Name und Kurzname wurden ersetzt. Jetzt läuft für jeden persönlichen Mandanten der Person, in dem sie das einzige aktive Mitglied (mit aktivem Konto) ist, vor dem ArangoDB-Plan das Mandanten-Löschinventar (#1769) mit `origin: account_erasure`; R-16 bis R-18 bleiben dort unter ihrem Tombstone-Hash. **Entscheidung für Mandanten mit weiteren aktiven Mitgliedern:** keine Spezifikation nennt einen Nachfolger (REQ-049 AK-19); der Mandant bleibt wie bisher erhalten, der Löschauftrag nennt den Grund (`personal_tenants[].outcome = retained_other_members`); offen in #1824. §2.3 Klarstellung, Abnahmekriterien AK-PT-01 bis AK-PT-03 in §6. REQ-025 §3.1.3 Regel 2 wird nachgezogen (#1826), gemeinsam mit den an REQ-025 verankerten Reach-Proben. |
| 1.7 | 2026-09-25 | **#1782/#1784:** §3.1 beschreibt die Einzel-Tasks, die es gibt, statt eines Master-Tasks `enforce_retention_policy` (Begründung in §3.1). §3.2: Fristvergleiche in AQL vergleichen Zeitpunkte (`DATE_TIMESTAMP`), nie ISO-Strings — ArangoDB ordnet Strings nach ICU-Kollation, gemessen `"…00.5Z" < "…00+00:00"` → `true`. §3.3: Prometheus-Metriken als nicht implementiert gekennzeichnet (#1800). §4: die tatsächlichen Settings mit Untergrenzen; R-04, R-12, R-14, R-15 und R-16..R-18 ohne lesenden Code als nicht implementiert gekennzeichnet (#1800). AK-04 bis AK-06, AK-10 und AK-11 angepasst. |
| 1.6 | 2026-09-25 | **#1781:** §3.4 Anwendungs- und Zugriffsprotokolle ergänzt (L-1 bis L-5): keine Kontoschlüssel, E-Mail-Adressen oder ungekürzten IP-Adressen an Log-Aufrufen der Anwendung (Zugriffsprotokolle und Tracebacks noch offen), gesalzener E-Mail-Digest, Salt-Pflicht auch für den Celery-Worker. Die Aufbewahrungsfrist der Log-Pipeline selbst ist als offene Betreiber-Frage markiert. |
| 1.5 | 2026-09-23 | **#1663:** Die ID R-19 war doppelt vergeben (Gießdienst-Rotation in §2.1, Promotion-Audit-Log in §2.3). Das Promotion-Audit-Log heißt jetzt **R-24** (R-23 ist im `spec/knowledge/COMPLIANCE-PLAN.md` bereits für RAG-Anfragen vorgesehen); R-19 bleibt die Gießdienst-Rotation, auf die sich `spec/e2e-testcases/TC-NFR-011.md` bezieht. Die Zeilen R-19, R-19a, R-20, R-21 und R-24 sind als nicht implementiert gekennzeichnet — ihre Collections existieren im Code nicht. `quality_assessments` (R-16) wird seit #1663 über das serverseitige `assessed_by_key` anonymisiert; `yield_metrics` (R-16) trägt kein Nutzerfeld. |
| 1.4 | 2026-04-27 | **ADR-003 (W-014 Sensor-Retention für Perennials):** R-14 differenziert nach `Location.data_classification` (REQ-002): `OUTDOOR_OPEN` Stufe 2 = 5y, Stufe 3 = 20y (Opt-in); `GREENHOUSE` Stufe 3 = 10y (Opt-in); `INDOOR_*` und `UNKNOWN` weiterhin 5y. Forward-only-Klassifizierungs-Wechsel. Vier neue Settings. R-19a für Saison-Aggregate-Anonymisierung bei User-Löschung. |
| 1.3 | 2026-04-27 | **ADR-002 (W-006 Promotion-Audit):** R-19 (seit v1.5: R-24) ergänzt — `promotion_audit_log`-Collection mit 5 Jahren Aufbewahrung. Begründung: Bei Sortenrechts-Streitigkeiten relevant; konsistent mit Erntedaten-Retention (R-16). |
| 1.2 | 2026-04-27 | **ADR-001 (W-009 Karenz-Detach):** R-17 präzisiert: Aufbewahrungsfrist umfasst auch geerbte `to_plant`-Edges (Karenz-Snapshot beim Detach). Fristberechnung anhand Original-`applied_at`, nicht anhand `inherited_at`. Hard-Delete nach 3 Jahren entfernt Original-Treatment + alle abhängigen Edges (direkt, run, geerbt) im selben Schritt. |
| 1.1 | 2026-04-27 | **W-002 Fix (Tombstone-Salt):** R-06 Maßnahme präzisiert (Pseudonymisierung sofort nach User-Hard-Delete + Hard-Delete des Audit-Eintrags nach 1 Jahr). Pflicht-Setting `ERASURE_TOMBSTONE_SALT` in §4 ergänzt — Backend startet ohne dieses Setting nicht (siehe REQ-025 §3.1). Compliance-Begründung: Art. 5(1)(e) Speicherbegrenzung. |
| 1.0 | 2026-02-27 | Erstversion — Retention-Matrix R-01 bis R-15, Celery-Master-Task, TimescaleDB-Downsampling, Konfigurations-Defaults. |

## 1. Business Case

### 1.1 User Story

**Als** Datenschutzbeauftragter
**möchte ich** dass personenbezogene Daten automatisch nach definierten Fristen gelöscht oder anonymisiert werden
**um** die DSGVO-Grundsätze der Speicherbegrenzung (Art. 5 Abs. 1 lit. e) und Datenminimierung (Art. 5 Abs. 1 lit. c) einzuhalten.

**Als** Systemadministrator
**möchte ich** dass Löschfristen automatisch durch das System durchgesetzt werden
**um** manuellen Aufwand zu vermeiden und menschliche Fehler bei der Datenbereinigung auszuschließen.

**Als** Betreiber einer Anbauanlage
**möchte ich** dass gesetzlich vorgeschriebene Aufbewahrungsfristen (CanG, PflSchG) eingehalten werden
**um** bei behördlichen Kontrollen alle erforderlichen Nachweise vorlegen zu können.

### 1.2 Geschäftliche Motivation

Diese NFR ist ein **Cross-Cutting Concern** (querschnittliche Anforderung), der alle 24 funktionalen Anforderungen (REQ-001 bis REQ-024) sowie das zukünftige REQ-025 (Datenschutz & Betroffenenrechte) betrifft. Sie adressiert:

1. **DSGVO Art. 5 Abs. 1 lit. e (Speicherbegrenzung):** Personenbezogene Daten dürfen nur so lange gespeichert werden, wie es für den Verarbeitungszweck erforderlich ist.
2. **DSGVO Art. 17 (Recht auf Löschung):** Betroffene können Löschung verlangen; das System muss diese technisch umsetzen können.
3. **Gesetzliche Aufbewahrungspflichten:** CanG (Cannabis-Gesetz) und PflSchG (Pflanzenschutzgesetz) schreiben Mindestaufbewahrungsfristen für bestimmte Datenkategorien vor.
4. **Datensparsamkeit:** Sensor- und Verhaltensdaten, die Rückschlüsse auf Personen erlauben (SEC-K-005), müssen nach definierter Frist aggregiert oder gelöscht werden.

### 1.3 Hintergrund: IT-Security-Review-Findings

Diese NFR adressiert direkt die folgenden kritischen Befunde aus dem IT-Security-Review:

| Finding | Schweregrad | Adressiert durch |
|---------|-------------|-----------------|
| SEC-K-001 | Kritisch | Retention-Matrix (§2), Celery-Enforcement (§3) |
| SEC-K-002 | Kritisch | IP-Anonymisierung (§2.1 Zeile "IP-Adressen") |
| SEC-K-005 | Kritisch | Sensordaten-Downsampling (§2.2) |

---

## 2. Retention-Matrix

### 2.1 Personenbezogene Daten

| # | Datenkategorie | Collection(s) | Frist | Aktion nach Frist | Rechtsgrundlage | Referenz |
|---|---------------|---------------|-------|-------------------|----------------|----------|
| R-01 | Soft-Deleted User-Accounts | `users` (status: `deleted`) | 90 Tage nach Soft-Delete | Hard-Delete: Account-Daten endgültig entfernen, E-Mail-Hash für Duplikatprüfung behalten. **Der Soft-Delete selbst entfernt bereits `password_hash` und `avatar_url`** — die Frist darf kein Authentifizierungsgeheimnis überdauern (REQ-025 Szenario 3, #1525) | Art. 17 DSGVO, Art. 5(1)(e) | REQ-023 §2, REQ-025 |
| R-02 | Unbestätigte Accounts | `users` (status: `unverified`) | 7 Tage nach Erstellung | Hard-Delete: Account und zugehörige Auth-Provider entfernen. **Selektor (#1992, #2010):** nie bestätigt (`email_verified == false`), nie von einem Administrator herabgestuft (`email_verified_lowered_at`), nie angemeldet (`last_login_at`), Alter lesbar und über der Frist, **keine Anbieterzeile** (jede Zeile zählt als verknüpft). Eine lokal registrierte Person hat eine `LOCAL`-Zeile und wird daher **noch nicht** erreicht: Der Task zählt sie (Trockenlauf, `local_registrations_pending`) und löscht sie erst, wenn der Betreiber `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED` setzt; freigegeben zählen nur föderierte Anbieterzeilen als verknüpft, Servicekonten bleiben ausgenommen | Art. 5(1)(e), Zweckentfall | REQ-023 §3.5, AK-17 **Teilweise umgesetzt** (#2010): Provider-lose Konten werden gelöscht; abgebrochene lokale Registrierungen erst nach Freigabe |
| R-03 | IP-Adressen in Sessions | `refresh_tokens` (Feld: `ip_address`) | 7 Tage nach Speicherung | Anonymisierung: IPv4 letztes Oktett → `0`, IPv6 → `/48`-Präfix behalten | Art. 6(1)(f) berechtigtes Interesse, Art. 5(1)(c) Datenminimierung | REQ-023 §2 |
| R-04 | Consent Records | `consent_records` | 3 Jahre nach Widerruf | Hard-Delete nach Fristablauf. **Bei Kontolöschung vor Fristablauf (Betreiberentscheidung Q-R5, #1800):** Pseudonymisierung (`user_key` → Tombstone-Hash, R-06-Analogie, Phase 2.5 der Kontolöschung, REQ-025 §3.1.3 Ziffer 3) statt sofortiger Löschung; die 3-Jahres-Frist ab Widerruf läuft für den pseudonymisierten Datensatz unverändert weiter, danach Hard-Delete. Ersetzt die frühere §5-Formulierung „sofort löschbar" (echter Widerspruch, jetzt aufgelöst) | Art. 7(1) Nachweispflicht | REQ-025 **Umgesetzt** (#1800, #1912): `retention.purge_expired_consent_records` (täglich) löscht einen widerrufenen Datensatz hart, sobald `revoked_at` älter als `RETENTION_CONSENT_RETENTION_YEARS` ist; ein Datensatz ohne lesbares `revoked_at` wird nie gewählt, sondern als `held_undated` gezählt (AK-14b). Die Pseudonymisierung bei Kontolöschung läuft in der Kontolöschung selbst (Phase 2.5). |
| R-04a <!-- Q-R6, #1800 --> | IP-Adresse in Consent Records | `consent_records` (Feld `ip_address`) | 7 Tage nach Aufzeichnung; setzt sich bei erneuter Einwilligung (neuer `ip_address`-Wert) zurück | Anonymisierung wie R-03 (IPv4 letztes Oktett → `0`, IPv6 `/48`-Präfix), `ip_anonymized_at` gesetzt | Art. 5(1)(c) Datenminimierung | REQ-025 **Umgesetzt** (#1800, #1912): `retention.anonymize_consent_ips` (täglich) anonymisiert `ip_address` ab `granted_at` + `RETENTION_CONSENT_IP_ANONYMIZATION_DAYS` und stempelt `ip_anonymized_at`; eine erneute Einwilligung setzt `ip_anonymized_at` zurück. `anonymize_old_ips` (R-03) deckt weiter nur `refresh_tokens` ab. |
| R-05 | Export-Dateien | Dateisystem (Export-Verzeichnis) | 72 Stunden nach Erstellung | Datei löschen, Status auf `expired` setzen | Art. 15/20 DSGVO, Zweckentfall | REQ-025 |
| R-06 | Erasure-Audit-Logs (Löschnachweis einer Betroffenenrechte-/Kontolöschung) | `erasure_requests` | 3 Jahre nach Abschluss <!-- Q-R12, #1793/#1806 --> | **Pseudonymisierung sofort nach User-Hard-Delete (`user_key` → Tombstone-Hash via REQ-025 §3.1 Phase 2.5), anschließend Hard-Delete des Audit-Eintrags nach 3 Jahren** <!-- W-002, verlängert Q-R12 --> | Art. 5(2) Rechenschaftspflicht + Art. 5(1)(e) Speicherbegrenzung | REQ-025 |
| R-06a <!-- Q-R4, #1793/#1790 --> | Tenant-Erasure-Records (Löschnachweis einer Mandantenlöschung — eigener Datensatztyp, eigene Formel, nicht an R-06 gekoppelt) | `tenant_erasure_records` | Bis zum längsten noch laufenden Fristende der unter R-16/R-17/R-18 desselben Mandanten zurückgehaltenen Zeilen (siehe §2.3, Q-R1), **gedeckelt auf 5 Jahre nach Abschluss der Mandantenlöschung** | Hard-Delete nach Ablauf | Art. 5(2) Rechenschaftspflicht (R-06-Analogie) | REQ-024/REQ-025 **Umgesetzt** (#1793, v1.15): `retention.purge_expired_tenant_erasure_records` (täglich 04:50 UTC, nach dem R-16..R-18-Lauf) löscht einen `completed`-Nachweis, sobald keine der von ihm aufbewahrten Zeilen mehr den Mandantenschlüssel trägt, spätestens 5 Jahre nach Abschluss. Die Deckelung ist fest und keine Einstellung: Sie ist gleich der längsten gesetzlichen Mindestfrist (R-16), ein kürzerer Wert würde den Nachweis vor den von ihm bewiesenen Zeilen löschen (Security-Review SEC-002). Hat die Löschung keine R-16..R-18-Zeile aufbewahrt, gibt es kein zugehöriges Fristende; der Nachweis bleibt dann bis zur Deckelung (engere Lesart). |
| R-07 | E-Mail-Änderungsanfragen | `email_change_requests` | 24 Stunden nach Erstellung | Hard-Delete (abgelaufene Tokens) | Zweckentfall | REQ-025 **Umgesetzt** (#1800, #1912): `retention.expire_email_change_requests` setzt eine unbestätigte Anfrage (`pending`, `expired`, `cancelled`) nach `expires_at` auf `expired` und löscht sie im selben Lauf hart. |
| R-07a | Rückgängig-Fenster einer bestätigten E-Mail-Änderung (#1848) | `email_change_requests` (Felder: `previous_email`, `revert_token_hash`, `revert_expires_at`) | 7 Tage nach der Bestätigung (`RETENTION_EMAIL_CHANGE_REVERT_DAYS`) | Felder nullen | Zweckentfall: der Link, mit dem die vorherige Adresse das Konto zurückholt (REQ-025 AK-EC-04), ist abgelaufen | REQ-025 **Implementiert** (#1848): `retention.expire_email_change_requests` nullt die Felder im selben stündlichen Lauf. |
| R-07b <!-- Q-R7, #1800 --> | Bestätigte E-Mail-Änderungsanfrage (Restdokument) | `email_change_requests` (Status `confirmed`/`reverted`/`superseded`) | Sobald das R-07a-Rückgängig-Fenster abgelaufen ist (`RETENTION_EMAIL_CHANGE_REVERT_DAYS` nach Bestätigung) | Hard-Delete des **gesamten** Dokuments — ergänzt R-07a, das nur die Rückgängig-Felder nullt, ersetzt es aber nicht | Zweckentfall | REQ-025 **Umgesetzt** (#1800, #1912): derselbe stündliche Lauf löscht das ganze Dokument, sobald das gespeicherte `revert_expires_at` abgelaufen ist (nie aus `confirmed_at` und der aktuellen Einstellung neu gerechnet); ohne lesbares `confirmed_at`/`revert_expires_at` wird es nicht gewählt, sondern als `held_undated` gezählt. |
| R-08 | Passwort-Reset-Tokens | `users` (Felder: `password_reset_token`, `password_reset_expires`) | 1 Stunde (besteht) | Token-Felder nullen | REQ-023 §1 | REQ-023 |
| R-09 | E-Mail-Verifikations-Tokens | `users` (Felder: `email_verification_token`, `email_verification_expires`) | 24 Stunden (besteht) | Token-Felder nullen | REQ-023 §1 | REQ-023 |
| R-10 | OAuth State | Redis | 5 Minuten (besteht, Redis TTL) | Automatische Bereinigung durch Redis | REQ-023 §3.2 | REQ-023 |
| R-11 | Abgelaufene Refresh Tokens | `refresh_tokens` | Sofort nach Ablauf | Hard-Delete (TTL-Index besteht) | Zweckentfall | REQ-023 §2 |
| R-12 | Einladungen (abgelaufen) | `invitations` | 30 Tage nach Ablauf | Hard-Delete | Zweckentfall | REQ-024 **Umgesetzt** (#1800, #1912): `cleanup_expired_invitations` setzt abgelaufene Einladungen auf `expired` und löscht sie `RETENTION_INVITATION_RETENTION_DAYS` nach `expires_at` hart. |
| R-13 | Processing Restrictions | `processing_restrictions` | Unbegrenzt (bis Aufhebung durch Betroffenen) | Nur auf expliziten Wunsch entfernen | Art. 18 DSGVO | REQ-025 |
| R-19 | Gießdienst-Rotation (DutyRotation) | `duty_rotations` | Unbegrenzt (bei User-Löschung: User-Referenz anonymisieren) | Anonymisierung: User-Referenz auf NULL, Dienst-Zeitraum bleibt | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 **Nicht implementiert** (Stand #1663): Die Collection `duty_rotations` existiert im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |
| R-20 | Pinnwand-Beiträge (BulletinPost/Comment) | `bulletin_posts`, `bulletin_comments` | Bei User-Löschung: User-Referenz anonymisieren, Inhalt bleibt | Anonymisierung | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 **Nicht implementiert** (Stand #1663): Die Collections `bulletin_posts`/`bulletin_comments` existieren im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |
| R-21 | Einkaufslisten (SharedShoppingList) | `shared_shopping_lists` | Bei User-Löschung: User-Referenz anonymisieren | Anonymisierung | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 **Nicht implementiert** (Stand #1663): Die Collection `shared_shopping_lists` existiert im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |
| R-22 | Aufgaben-Bewertungen (Task difficulty/quality ratings) | `tasks` (Felder: `difficulty_rating`, `quality_rating`, `assigned_to_user_key`) | Bei User-Löschung: `assigned_to_user_key` durch den Marker `_anonymized` ersetzen (`ErasureEngine.ANONYMIZE_COLLECTIONS`), Bewertungen bleiben (aggregiert nutzbar) | Anonymisierung | Art. 17 Abs. 3 (Lern-System benötigt Aggregatdaten) | REQ-006 |
| R-25 <!-- REQ-053 --> | Pflegeprotokoll (CareEvent) | `care_events` (Felder: `performed_by_user_key`, `performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`, `summary`, `reason`, `observed_outcome`, `product_label`, `performed_by_label`, `photo_refs`) | **5 Jahre** ab `performed_at` (Fruchtfolge-Rückblick REQ-053 GP-FR-103); bei User-Löschung sofort: alle `*_by`/`*_user_key` → `_anonymized` | Nach Frist: Personenfelder → `_anonymized`, Freitexte → `[redacted]`, Attachments löschen; `category`, `performed_at`, `quantity`, `location_key`, `plant_keys` bleiben (Fruchtfolge, Art. 17 Abs. 3). Für `category ∈ {pest_control, ipm}` gilt der PflSchG-Vorbehalt wie bei `treatment_applications`. | Art. 5(1)(e); Art. 17 Abs. 3 (berechtigtes Interesse: Anbauhistorie) | REQ-053 v1.2 §13, GP-NFR-055, GP-FR-109 **Nicht implementiert** (Stand 2026-10-04): Collection entsteht mit REQ-053 Welle 4. |
| R-26 <!-- REQ-053 --> | Gartenplan-Änderungsprotokoll | `garden_plan_audit` (Feld `user_key`) | 1 Jahr | Hard-Delete; bei User-Löschung sofort `user_key → _anonymized` | Art. 5(1)(e) | REQ-053 v1.2 §20.13 **Nicht implementiert** (Stand 2026-10-04). |
| R-27 <!-- REQ-054 --> | Anbauplanung (PlanningRequest, PlantingProposal) | `planning_requests`, `planting_proposals` (Felder `created_by`, `computed_by`, `accepted_by`) | Mit dem Request (Nutzer löscht); verworfene/unerfüllbare Vorschläge (`discarded`, `infeasible`) 1 Jahr nach `computed_at`; angenommene Vorschläge 5 Jahre nach `accepted_at` (Begründung der Runs, wie R-25) | Hard-Delete (verworfen); nach 5 Jahren: Nutzer-Keys → `_anonymized`, Dokument bleibt; bei User-Löschung sofort `*_by → _anonymized` | Art. 5(1)(e); Art. 17 Abs. 3 (Anbauhistorie) | REQ-054 v1.1 §13 **Nicht implementiert** (Stand 2026-10-04). |
| R-19a <!-- ADR-003 --> | Saison-Aggregate (`seasonal_cycles.sensor_aggregates`) | `seasonal_cycles` (Feld `aggregate_computed_by`) | Aggregate bleiben unbegrenzt (keine personenbezogenen Daten); bei User-Löschung `aggregate_computed_by → NULL` | Anonymisierung | Art. 17 Abs. 3 (fachliche Trendanalyse über Pflanzenleben) | REQ-003 v2.x, REQ-025 **Nicht implementiert** (Stand #1663): Die Collection `seasonal_cycles` existiert im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |

<!-- Quelle: Datenschutzplan Q-R11, #1806 GDPR-009 -->
**R-01a — Wartezeit nach der Mitglieder-Benachrichtigung (#1960).** Die Benachrichtigung der anderen Mitglieder eines persönlichen Mandanten wird am Löschauftrag vermerkt (`members_notified_at`, Anzahl der Empfänger, Fehlerzähler `members_notice_failures`; keine Adressen, nur gesalzene Referenzen). Wurden die Mitglieder beim Antrag benachrichtigt, wartet die endgültige Löschung auf nichts weiter (die 90 Tage liegen dann ohnehin hinter der Benachrichtigung). Wurden sie erst später benachrichtigt — Löschauftrag aus der Zeit vor #1824 ohne Vermerk, oder eine fehlgeschlagene erste Zustellung —, löscht der Lauf frühestens `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` Tage nach dieser Benachrichtigung. Ohne weitere erreichbare Mitglieder entfällt die Wartezeit. Lässt sich die Benachrichtigung die ganze Wartezeit lang nicht zustellen, geht die Löschung weiter und der Lauf protokolliert das ohne Adresse. Ein Löschen durch einen Administrator wartet nie.

**R-01 — Warum 90 Tage Art. 12(3)/17(1) nicht verletzen (Betreiberentscheidung 2026-09-26).**
Art. 12(3) setzt für die **Antwort** auf einen Betroffenenantrag eine Ein-Monats-Basisfrist;
Art. 17(1) verlangt Löschung „unverzüglich". Beide sind bereits im Moment des Soft-Delete
erfüllt: Der Antrag wird **synchron** umgesetzt — Status auf `deleted`, alle Sitzungen
invalidiert, `password_hash` und `avatar_url` sofort aus dem Dokument entfernt (§1
oben, REQ-025 §1.1 Szenario 3). Die betroffene Person kann sich ab diesem Zeitpunkt nicht
mehr anmelden und hat keine wiederherstellbaren Zugangsdaten mehr im System — die Löschung
im Sinne von Art. 17(1) ist wirksam. Die 90 Tage danach sind keine Bearbeitungsverzögerung,
sondern eine **Aufbewahrungsfrist für die verbleibenden Restdaten** (u. a. zur Betrugs- und
Missbrauchsprävention sowie zur Behandlung von Wiederherstellungsanfragen kurz nach einer
Fehlbedienung) — vergleichbar mit einer Löschsperre, wie sie Art. 17(3) für andere
Zwecke ausdrücklich zulässt. Diese Einordnung ist hiermit als Entscheidung dokumentiert
(#1806 GDPR-009) und nicht mehr offen; eine Änderung der Frist selbst bleibt eine
gesonderte Entscheidung.

### 2.2 Sensordaten (Indirekt personenbezogen — SEC-K-005)

Sensordaten können Rückschlüsse auf Anwesenheit und Verhalten von Personen erlauben (CO2-Kurven, Bewegungssensoren, manuelle Overrides). Sie unterliegen daher einer gestuften Retention-Policy mit zunehmender Aggregierung:

| # | Datenkategorie | Speichersystem | Stufe 1 (Rohdaten) | Stufe 2 (Stündlich) | Stufe 3 (Täglich) | Rechtsgrundlage |
|---|---------------|---------------|-------------------|--------------------|--------------------|----------------|
| R-14 | Sensordaten (Temperatur, RH, CO2, Licht, Bodenfeuchtigkeit) <!-- ADR-003 differenziert nach Location.data_classification (REQ-002), siehe Tabelle unten --> | TimescaleDB | 90 Tage volle Auflösung | 90d–2 Jahre (Default) bzw. 90d–5 Jahre (`OUTDOOR_OPEN`): Stundenmittelwerte | **Differenziert nach Klassifizierung (siehe Untertabelle)** | Art. 6(1)(b) Vertragserfüllung |
| R-15 | Aktor-Logs (manuelle Overrides) | TimescaleDB | 90 Tage | 90d–1 Jahr: aggregiert (Override-Anzahl/Tag) | Danach löschen | Art. 6(1)(f) berechtigtes Interesse |

**Durchsetzungsstand (v1.29, #1800): R-14 und R-15 sind nicht implementiert.** Die Sensor-Intervalle (90 Tage, 2 Jahre, 5 Jahre) stehen als Literale in `003_retention_policies.sql`, die Stufen je Klassifizierung sind nicht modelliert; für Aktor-Logs gibt es keinen Speicher. Die Zahlen dieser Tabelle sind Zielbild, kein Verhalten.

<!-- Quelle: Datenschutzplan Q-O5/Q-O6, #1800 -->
**Roadmap-Ziel „Retention-Observability" (Betreiberentscheidung 2026-09-26, #1800).**
Zwei Lücken dieser NFR werden hiermit ausdrücklich zu einem gemeinsamen, benannten
Roadmap-Ziel erklärt, statt weiter als isolierte offene Punkte mitgeführt zu werden:

- **R-14/ADR-003 vollständig umsetzen (Q-O5):** ADR-003 (Sensor-Retention-Differenzierung
  nach `Location.data_classification`, §2.2 Untertabelle) ist als Architektur-Entscheidung
  **Accepted**, aber seine Folgemaßnahmen sind nicht gebaut — `Location.data_classification`
  existiert nicht im Modell, die Stufen-3-Werte je Klassifizierung sind Literale in
  `003_retention_policies.sql`, kein `SENSOR_*`-Setting hat einen Leser (§4). Die
  Vollumsetzung berührt REQ-002 (Modellfeld + UI), REQ-003 (SeasonalCycle-Aggregate),
  REQ-005 (TimescaleDB-Policy-Auswahl) und diese NFR gleichzeitig — das ist **Roadmap-Umfang,
  nicht der Zuschnitt eines einzelnen PRs** (ADR-003 „Folgemaßnahmen"-Tabelle).
- **R-15 Aktor-Logs + AK-06 Retention-Metriken bauen (Q-O6):** R-15 hat heute keinen
  Speicher (kein Task, keine Collection); AK-06 (Prometheus-Metriken
  `retention_records_processed_total` u. a., §3.3) hat keine Metrik-Pipeline, an die sie
  andocken könnten. Beide werden hier als **ein** vorwärtsverweisendes Roadmap-Item
  geführt, nicht länger nur einzeln als "nicht implementiert" vermerkt und sonst
  stillschweigend fallengelassen.

Dieser Absatz erschöpft die Anforderung nicht — er benennt sie als offen und referenziert
sie zusammenhängend; ein späteres Vorhaben (Issue/Epic „Retention-Observability") bricht
sie in umsetzbare Pakete herunter.
<!-- /Quelle: Datenschutzplan Q-O5/Q-O6, #1800 -->

<!-- Quelle: ADR-003 / W-014 -->
**R-14 Differenzierung nach `Location.data_classification` (ADR-003):**

Sensor-Retention auf Stufe 2 + 3 wird nach DSGVO-Risikogruppe der Location (REQ-002) differenziert. Die Klassifizierung steuert, wie lange aggregierte Daten aufbewahrt werden dürfen, ohne gegen Art. 5(1)(e) Speicherbegrenzung zu verstoßen.

| `data_classification` | Stufe 1 (Roh) | Stufe 2 (Stunde) | Stufe 3 (Tag) | Saison-Aggregate (REQ-003) |
|----------------------|---------------|------------------|---------------|----------------------------|
| `INDOOR_PRIVATE` (Default für `UNKNOWN`) | 90d | 2y | 5y | ∞ (anonymisiert bei User-Löschung, R-19a) |
| `INDOOR_PUBLIC` | 90d | 2y | 5y | ∞ (anonymisiert bei User-Löschung, R-19a) |
| `GREENHOUSE` | 90d | 2y | **10y (opt-in)** | ∞ (anonymisiert bei User-Löschung, R-19a) |
| `OUTDOOR_OPEN` | 90d | **5y** | **20y (opt-in)** | ∞ |

**Verlängerte Retention bei `GREENHOUSE` und `OUTDOOR_OPEN`:** Tenant-Admin muss explizit zustimmen (Opt-in), damit die längeren Stufen aktiviert werden. Default für alle Klassifizierungen ist die DSGVO-konservative 5-Jahres-Grenze auf Stufe 3. Begründung der Werte: Bei `OUTDOOR_OPEN` (Garten, Hochbeet) besteht kein Personenbezug — Stundenmittelwerte enthalten keine Anwesenheits-Indikatoren. Eine längere Aufbewahrung ist daher DSGVO-rechtlich unkritisch und fachlich für mehrjährige Analysen wertvoll (Apfelbäume, Beerensträucher).

**Forward-only-Klassifizierungs-Wechsel (Workshop-Frage 5):** Bei Wechsel der `data_classification` einer Location (z.B. `INDOOR_PRIVATE` → `OUTDOOR_OPEN`) gelten die neuen Retention-Fristen NUR für Sensor-Werte, die NACH dem Wechsel erfasst wurden. Bestehende Daten behalten ihre ursprüngliche Schutzklasse — verhindert nachträgliche Schutz-Senkung durch Klassifizierungs-Manipulation.

**Klassifizierungs-Default `UNKNOWN` (Workshop-Frage 2):** Locations ohne explizite Klassifizierung werden wie `INDOOR_PRIVATE` behandelt — DSGVO-konservativ, Anwender muss bewusst auf `OUTDOOR_OPEN` wechseln (UI-Warnung).
<!-- /Quelle: ADR-003 / W-014 -->

<!-- Quelle: Widerspruchsanalyse W-009 — Klimatische Extremwerte dauerhaft archivieren -->
**Ausnahme: Klimatische Extremwert-Events:**

Sensordaten-Rohdaten werden nach 90 Tagen aggregiert (R-14). Für die Pflanzenpflege-Analyse bei mehrjährigen Pflanzen (Perennials, Obstbäume) archiviert das System jedoch **klimatische Extremereignisse** (Frost, Hitzewelle, Sturm) als eigenständige Event-Dokumente in ArangoDB dauerhaft. Diese Events enthalten keinen Personenbezug und unterliegen daher nicht der DSGVO-Löschpflicht:

- `ClimateEvent`-Dokument in ArangoDB (nicht TimescaleDB): `type` (frost/heat/storm), `location_key`, `start_at`, `end_at`, `min_temp`/`max_temp`, `severity`
- Automatische Erkennung durch Schwellwert-Prüfung im Sensor-Ingestion-Task
- Konfigurierbar: `SENSOR_RAW_RETENTION_DAYS` (Standard 90), erhöhbar für Perennial-Anlagen

**TimescaleDB Continuous Aggregates:**

```sql
-- Stundenmittel (Stufe 2): automatisch nach 90 Tagen
CREATE MATERIALIZED VIEW sensor_hourly
  WITH (timescaledb.continuous) AS
  SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    location_key,
    sensor_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS sample_count
  FROM sensor_readings
  GROUP BY bucket, location_key, sensor_type;

-- Tagesmittel (Stufe 3): automatisch nach 2 Jahren
CREATE MATERIALIZED VIEW sensor_daily
  WITH (timescaledb.continuous) AS
  SELECT
    time_bucket('1 day', bucket) AS bucket,
    location_key,
    sensor_type,
    AVG(avg_value) AS avg_value,
    MIN(min_value) AS min_value,
    MAX(max_value) AS max_value,
    SUM(sample_count) AS sample_count
  FROM sensor_hourly
  GROUP BY time_bucket('1 day', bucket), location_key, sensor_type;

-- Retention-Policies
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');
SELECT add_retention_policy('sensor_hourly', INTERVAL '2 years');
SELECT add_retention_policy('sensor_daily', INTERVAL '5 years');
```

<!-- Quelle: Datenschutzplan Q-O7, #1793 -->
**Aggregate folgen der Löschung von Tenant und Sensor (Betreiberentscheidung 2026-09-26, #1793).**
Die Retention-Policies oben laufen altersbasiert und decken deshalb nicht den Fall ab, dass
ein Tenant oder ein einzelner Sensor vor Ablauf seiner Frist gelöscht wird: `sensor_hourly`
und `sensor_daily` behalten die materialisierten Buckets des gelöschten Tenants/Sensors
so lange, bis eine reguläre Policy-Aktualisierung zufällig ihr Zeitfenster erreicht.

- **Tenant-Löschung:** Alle Buckets **jeden Alters** des gelöschten Tenants werden in
  `sensor_hourly` und `sensor_daily` gezielt gelöscht (`DELETE ... WHERE tenant_key = …`
  direkt aus der Materialisierungstabelle; ein Refresh über den historischen Bereich ist
  **keine** Option, er würde auch die Buckets anderer Mandanten verlieren, deren Rohdaten
  die 90-Tage-Retention schon entfernt hat) —
  nicht nur das Rohdaten-Fenster von 90 Tagen.
- **Sensor-Löschung:** Wird ein einzelner Sensor gelöscht, werden seine Buckets in
  `sensor_hourly`/`sensor_daily` mit ihm gelöscht, nicht als historischer Datenbestand
  aufbewahrt.

Beide Fälle laufen als Teil desselben Löschvorgangs wie die Rohdaten-Löschung
(`TimescaleObservationRepository.delete_by_tenant` / `delete_by_sensor`), nicht als
separater, später laufender Aggregat-Job.

**Kein Wiederanlegen nach der Löschung (#1944).** Eine Messung, die nach `delete_by_tenant` /
`delete_by_sensor` eintrifft — von einer Anfrage, die ihre Besitzprüfung schon bestanden hatte,
oder von der Home-Assistant-Abfrage, die die Sensorliste Minuten zuvor gelesen hat —, darf weder eine
Rohzeile noch (nach dem nächsten Refresh) Buckets für den gelöschten Besitzer erzeugen. Alle
Messungen laufen daher durch `ObservationService`: Der Sensor wird vor dem Einfügen und
**danach** erneut aufgelöst (Besitzer = Mandant des Eltern-Objekts); ist er inzwischen weg, wird
die eben geschriebene Reihe des Sensors mit gelöscht (`delete_by_sensor`) und die Anfrage wie eine
abgewiesene beantwortet (404). `SensorService.delete_sensor` markiert den Sensor vor dem Löschen der
Reihe als `deletion_pending`; eine Messung für einen so markierten Sensor wird abgewiesen, ein
fehlgeschlagenes Löschen bleibt wiederholbar. **Bucket-Refresh-Rennen (Randfall):** Eine
Policy-Aktualisierung, die vor der Löschung begann, kann einen Bucket des heißen Fensters nach der
Löschung neu materialisieren; die Rohzeilen-Löschung protokolliert eine Invalidierung, der nächste
Policy-Lauf (stündlich bzw. täglich) berechnet den Bucket aus nicht mehr vorhandenen Zeilen und
entfernt ihn. Das Fenster ist damit durch den Policy-Takt begrenzt und braucht keinen eigenen
Schutz; es bleibt dokumentiert.
<!-- /Quelle: Datenschutzplan Q-O7, #1793 -->

**Altbestand unter leerem Mandantenschlüssel (#2077).** Messwerte, die die Home-Assistant-Abfrage vor
#1944 gespeichert hat, tragen `tenant_key = ''` (ein Sensor-Dokument hat keinen eigenen); weder
`delete_by_tenant` noch `delete_by_sensor` trifft sie, in den Rohdaten wie in den Stunden- und
Tagesmitteln. #1944 verhindert neue Zeilen dieser Art und ändert den Bestand nicht. Entscheidung des
Betreibers (2026-10-04): Zeilen eines Sensors, dessen Dokument **nicht mehr existiert**, dürfen
gelöscht werden — aber nur nach ausdrücklicher Bestätigung durch einen Menschen, mit einem Trockenlauf
davor; Zeilen eines **bestehenden** Sensors werden nicht gelöscht (nur gezählt, einschließlich der Zahl
der Zeitreihen, deren Mandant sich aus dem Eltern-Objekt ableiten ließe). Nichts davon läuft
automatisch: kein Migrationsschritt, kein Beat-Task. Der Betreiberbefehl
`python -m app.migrations.purge_orphan_ha_readings` ordnet jede Zeitreihe mit leerem Schlüssel in
*verwaist*, *lebend* oder *nicht zuordenbar* ein, meldet Zeilen je Klasse und Tabelle (`raw`, `hourly`,
`daily`) und löscht die verwaiste Klasse nur mit `--confirm-delete-orphans <Zahl>`, wobei die Zahl der
im Trockenlauf gemessenen verwaisten Zeilen entsprechen muss (sonst Abbruch, nichts gelöscht). Er
löscht in Zeitfenstern mit je einem Commit, prüft vor jeder Zeitreihe erneut, dass der Sensor fehlt,
ist idempotent und protokolliert nur Zahlen. Ohne TimescaleDB meldet er „nicht anwendbar". Das
Bucket-Refresh-Rennen des vorigen Absatzes gilt auch hier; der Befehl misst nach dem Löschen erneut.
Die Zahl betroffener Zeilen auf einer echten Installation ist nicht Teil dieser Umsetzung.

### 2.3 Fachliche Aufbewahrungspflichten

Diese Daten unterliegen gesetzlichen Mindestaufbewahrungsfristen und dürfen **nicht** vor Ablauf gelöscht werden:

| # | Datenkategorie | Collection(s) | Mindestfrist | Rechtsgrundlage | Referenz |
|---|---------------|---------------|-------------|----------------|----------|
| R-16 | Erntedaten (HarvestBatch, QualityAssessment, YieldMetric) | `harvest_batches`, `quality_assessments`, `yield_metrics` | 5 Jahre | Art. 6(1)(c) gesetzl. Pflicht, CanG (Cannabis-Gesetz) | REQ-007 |
| R-17 | Behandlungsanwendungen (TreatmentApplication) | `treatment_applications` + `to_plant`/`to_run`-Edges (inkl. geerbter `inherited_from_run`-Edges, ADR-001) | 3 Jahre | Art. 6(1)(c) gesetzl. Pflicht, PflSchG §11 | REQ-010 |
| R-18 | Inspektionsprotokolle | `inspections` | 3 Jahre | PflSchG §11 | REQ-010 |
| R-24 <!-- ADR-002; bis v1.4 doppelt als R-19 vergeben --> | Promotion-Audit-Log (Species/Cultivar tenant→global) | `promotion_audit_log` | 5 Jahre | Sortenrechts-Streitigkeiten, Art. 5(2) Rechenschaftspflicht. **Nicht implementiert** (Stand #1663): Die Collection `promotion_audit_log` existiert im Code nicht. | REQ-001 v4.1 |

**Wichtig:** Bei einer Löschanfrage (Art. 17 DSGVO) durch einen Betroffenen werden diese Daten **anonymisiert** (User-Referenz entfernt), aber nicht gelöscht, solange die gesetzliche Aufbewahrungsfrist läuft (Art. 17 Abs. 3 lit. b).

**Der persönliche Mandant der Person (#1788, aktualisiert #1824):** Die Aufbewahrungspflicht hält die Datensätze fest, nicht den Mandanten, in dem sie liegen. Ein persönlicher Mandant der Person wird bei Kontolöschung immer über das Mandanten-Löschinventar gelöscht — unabhängig davon, ob er weitere aktive Mitglieder hat (Betreiberentscheidung Q-E1/Q-E5, #1824; **ersetzt** die frühere Entscheidung, einen geteilten persönlichen Mandanten mit anonymisiertem Eigentümer zu erhalten, siehe AK-PT-03 in §6). Die Datensätze dieser Tabelle bleiben dabei unter dem Tombstone-Hash der Person erhalten, alles andere im Mandanten (Standorte, Pflanzen, Tagebuch, Aufgaben …) hat keinen Aufbewahrungsgrund und geht. Die Regel gilt nur für Mandanten mit `tenant_type: personal` — ein organisatorischer Mandant, dessen Gründerin zufällig das einzige aktive Mitglied ist, bleibt wie bisher mit anonymisiertem Eigentümerverweis erhalten (Q-E5-Abgrenzung).

**Q-R1/Q-R2 — Aufbewahrungspflicht überlebt Mandanten- und Kontolöschung unverändert (#1789).** R-16, R-17 und R-18 laufen bis zu ihrem ursprünglichen Fristende (5 bzw. 3 Jahre ab `harvest_date`/`applied_at`/`inspected_at`) weiter, gleichgültig ob in der Zwischenzeit der Mandant gelöscht wird (Q-R1) oder das Konto der Person gelöscht wird (Q-R2, dieselbe Regel). Weder die Mandanten- noch die Kontolöschung verkürzt oder setzt diese Frist zurück; beide pseudonymisieren nur den Kontoschlüssel (Tombstone-Hash) und lassen die Frist unangetastet weiterlaufen. **Umgesetzt** (#1789, v1.15): `retention.purge_expired_legal_retention_rows` (täglich 04:45 UTC) löscht eine Zeile, deren Mandant nicht mehr existiert, sobald ihre Frist abgelaufen ist — gelesen aus `RETENTION_HARVEST_DATA_MIN_RETENTION_YEARS` / `RETENTION_TREATMENT_MIN_RETENTION_YEARS` / `RETENTION_INSPECTION_MIN_RETENTION_YEARS` (§4), verglichen als Zeitpunkt (§3.2; eine Zeile ohne lesbares Datum wird nie gelöscht; eine Ernte ohne `harvest_date` zählt ab `created_at`, weil der Anlegeweg bis #1789 für ein fehlendes Datum „jetzt" angenommen, aber nicht gespeichert hat — seitdem speichert er es) —, zusammen mit `quality_assessments`/`yield_metrics` der Ernte und jeder Kante, die Zeile oder Kind berührt (R-17-Klarstellung unten). **Engere Lesart:** Die Zeilen eines weiterhin bestehenden Mandanten löscht der Task nicht; dort sind sie die eigenen Aufzeichnungen des Mandanten, und diese Tabelle nennt nur eine Mindestfrist. Die Regeln stehen in `TenantErasureEngine.LEGAL_RETENTION_RULES`; `TenantErasureEngine.validate` verweigert eine Inventarzeile, die für R-16..R-18 aufbewahrt wird, ohne dass eine Regel sie löscht.

<!-- Quelle: ADR-001 / W-009 -->
**R-17 Klarstellung — geerbte Treatment-Edges (ADR-001):**

Beim Detach einer PlantInstance werden aktive Run-Level-Treatments als `to_plant`-Edges mit `inherited_from_run`-Property auf die Plant kopiert (Karenz-Snapshot). Diese geerbten Edges teilen die 3-Jahre-Aufbewahrungsfrist des Original-Treatments. Die Fristberechnung erfolgt anhand des Original-`applied_at`-Timestamps des `treatment_applications`-Dokuments — nicht anhand des `inherited_at`-Timestamps der Edge.

Konsequenz: Bei Hard-Delete des Original-Treatments nach 3 Jahren werden auch alle abhängigen Edges (`to_plant`, `to_run`, geerbte `to_plant`) im selben Schritt entfernt. Pflanzen, die historisch detached wurden, verlieren damit ihren Karenz-Snapshot — der ist nach 3 Jahren ohnehin nicht mehr karenzwirksam.
<!-- /Quelle: ADR-001 / W-009 -->

---

## 3. Technische Umsetzung: Celery-Enforcement

### 3.1 Einzel-Tasks je Regel

Jede Regel läuft als eigener Celery-Beat-Task mit einem Takt, der zu ihrer Frist passt. Einen Master-Task, der alle Regeln in einem Lauf orchestriert, gibt es nicht (Entscheidung #1782, v1.7):

| Regel | Celery-Task | Takt (UTC) | Frist aus |
|-------|-------------|------------|-----------|
| R-01 | `retention.execute_scheduled_erasures` | täglich 04:00 | `RETENTION_SOFT_DELETE_RETENTION_DAYS` (beim Antrag in `hard_delete_scheduled_at` festgeschrieben) |
| R-02 | `app.tasks.auth_tasks.cleanup_unverified_accounts` | täglich 03:10 | `RETENTION_UNVERIFIED_ACCOUNT_DAYS`; Ausweitung auf lokale Registrierungen: `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED` (#2010) |
| R-03 | `app.tasks.auth_tasks.anonymize_old_ips` | täglich 03:20 | `RETENTION_IP_ANONYMIZATION_DAYS` |
| R-05 | `retention.expire_data_exports` | stündlich, Minute 20 | `RETENTION_EXPORT_FILE_RETENTION_HOURS` (bei Fertigstellung in `expires_at` festgeschrieben) |
| R-04 | `retention.purge_expired_consent_records` | täglich 04:35 | `RETENTION_CONSENT_RETENTION_YEARS` (ab `revoked_at`) |
| R-04a | `retention.anonymize_consent_ips` | täglich 04:40 | `RETENTION_CONSENT_IP_ANONYMIZATION_DAYS` (ab `granted_at`) |
| R-06 | `retention.purge_expired_erasure_records` | täglich 04:30 | `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` |
| R-07, R-07a, R-07b | `retention.expire_email_change_requests` | stündlich, Minute 15 | `RETENTION_EMAIL_CHANGE_RETENTION_HOURS` (beim Antrag in `expires_at` festgeschrieben); `RETENTION_EMAIL_CHANGE_REVERT_DAYS` (bei der Bestätigung in `revert_expires_at` festgeschrieben) |
| R-11 | `app.tasks.auth_tasks.cleanup_expired_tokens` | stündlich, Minute 10 | Ablaufzeitpunkt des Tokens |
| R-12 | `app.tasks.tenant_tasks.cleanup_expired_invitations` | täglich 02:00 | Ablaufzeitpunkt der Einladung (Status `expired`), danach `RETENTION_INVITATION_RETENTION_DAYS` bis zum Hard-Delete (#1800) |
| R-16, R-17, R-18 | `retention.purge_expired_legal_retention_rows` | täglich 04:45 | `RETENTION_HARVEST_DATA_MIN_RETENTION_YEARS`, `RETENTION_TREATMENT_MIN_RETENTION_YEARS`, `RETENTION_INSPECTION_MIN_RETENTION_YEARS` (#1789) |
| R-06a | `retention.purge_expired_tenant_erasure_records` | täglich 04:50 | fest 5 Jahre ab Abschluss (Q-R4) bzw. Ende der aufbewahrten R-16..R-18-Zeilen des Mandanten (#1793) |

Jede Frist wird aus genau einem Setting über `RetentionService` gelesen (§4); kein Task trägt eine eigene Zahl.

**Alle Retention-Tasks sind uhrzeitverankert (`crontab`), keiner ein fester Abstand (#1946).** Ein Intervall-Eintrag (`"schedule": 86400`) rechnet ab dem Start des Beat-Prozesses; ohne persistierten Zeitplan startet jeder Pod-Neustart den Abstand neu. „Spätestens N+1 Tage" in der Datenschutzübersicht (REQ-025, „Inhalt der Übersicht") ist nur mit einem Uhrzeit-Takt zugesichert.

**Warum kein Master-Task:** Nichts in dieser NFR verlangt einen Orchestrator als solchen. Was er leisten sollte — jede Regel wird regelmäßig durchgesetzt (AK-04), jeder Lauf protokolliert seine Zahlen (AK-05), ein Fehler in einer Regel hält keine andere auf — leisten die Einzel-Tasks bereits. Ein einheitlicher Tagestakt wäre für die stundengenauen Fristen sogar falsch: Ein Lauf um 02:00 UTC würde R-07 (24 h) um bis zu 24 Stunden überziehen und R-05 (72 h) ebenso, also länger speichern als deklariert. Die Beschreibung folgt deshalb dem Code, nicht umgekehrt.

### 3.2 Sub-Tasks (Beispiele)

**Fristvergleiche vergleichen Zeitpunkte, nie Strings (#1784).** ArangoDB ordnet Strings mit `<`/`>` nach ICU-Kollation, und gespeicherte Zeitstempel haben je nach Schreibweg verschiedene Formen (`…00Z`, `…00.500000Z`, `…00+00:00`, `…00.000Z`). Gemessen auf ArangoDB 3.12.8: `"2025-09-25T04:30:00.5Z" < "2025-09-25T04:30:00+00:00"` → `true` — ein Datensatz eine halbe Sekunde *nach* dem Stichtag galt als älter. Jeder Fristvergleich in AQL MUSS deshalb beide Seiten mit `DATE_TIMESTAMP(...)` vergleichen; `null < Zahl` ist in AQL wahr, deshalb entscheidet jeder `<`/`<=`-Selektor ausdrücklich, was mit einem Datensatz ohne lesbaren Zeitstempel geschieht, und zwar nach der Richtung der Aktion: Eine **zerstörende** Aktion nach Alter (Löschen, Erasure) schließt ihn aus (`DATE_TIMESTAMP(x) != null`), denn sein Alter ist nicht belegt. Eine **minimierende** Aktion (IP-Anonymisierung R-03) schließt ihn ein, denn Anonymisieren schadet niemandem, das Behalten der vollen Adresse schon. Die Ablauf-Selektoren (`expires_at`) für Sessions, Einladungen, E-Mail-Änderungen, MCP-Idempotenz und Aktor-Overrides behandeln einen fehlenden Ablaufzeitpunkt als abgelaufen; Export und KI-Gespräch tun das noch nicht (#1806). Durchgesetzt von `src/backend/tests/unit/guards/test_aql_timestamp_comparisons_are_instants.py`. `DATE_TIMESTAMP` löst auf Millisekunden auf; bei einem strikten `<` gegen den Stichtag kann das einen Datensatz nur jünger, nie älter erscheinen lassen.

Die folgenden Beispiele zeigen die Form; die tatsächlichen Selektoren liegen in den Repositories unter `src/backend/app/data_access/arango/`.

**R-01: Hard-Delete Soft-Deleted Accounts (90 Tage):**

```python
async def hard_delete_soft_deleted_accounts():
    """Löscht Accounts die seit > 90 Tagen im Status 'deleted' sind."""
    cutoff = datetime.utcnow() - timedelta(days=90)

    # AQL: Finde alle soft-deleted Accounts älter als 90 Tage
    accounts = await aql("""
        FOR u IN users
          FILTER u.status == 'deleted'
          FILTER DATE_TIMESTAMP(u.updated_at) != null
          FILTER DATE_TIMESTAMP(u.updated_at) < DATE_TIMESTAMP(@cutoff)
          RETURN u._key
    """, cutoff=cutoff.isoformat())

    for user_key in accounts:
        # Löschreihenfolge: Edges vor Nodes
        await delete_edges_for_user(user_key)  # has_auth_provider, has_session, etc.
        await delete_collection_docs("auth_providers", user_key)
        await delete_collection_docs("refresh_tokens", user_key)
        await delete_collection_docs("consent_records", user_key)
        await delete_user(user_key)
        log.info("retention.hard_delete_account", subject=log_subject(user_key))  # §3.4 L-1

    return {"deleted_count": len(accounts)}
```

**R-03: IP-Anonymisierung (7 Tage):**

```python
async def anonymize_session_ips():
    """Anonymisiert IP-Adressen in Sessions älter als 7 Tage."""
    cutoff = datetime.utcnow() - timedelta(days=7)

    # AQL: Anonymisiere IPs in nicht-anonymisierten Sessions
    result = await aql("""
        FOR rt IN refresh_tokens
          FILTER rt.ip_address != null
          FILTER rt.ip_anonymized_at == null
          FILTER DATE_TIMESTAMP(rt.issued_at) != null
          FILTER DATE_TIMESTAMP(rt.issued_at) < DATE_TIMESTAMP(@cutoff)
          UPDATE rt WITH {
            ip_address: REGEX_REPLACE(rt.ip_address, '\\.[0-9]+$', '.0'),
            ip_anonymized_at: DATE_ISO8601(DATE_NOW())
          } IN refresh_tokens
          RETURN 1
    """, cutoff=cutoff.isoformat())

    return {"anonymized_count": len(result)}
```

**R-05: Export-Dateien bereinigen (72 Stunden):**

```python
async def cleanup_expired_exports():
    """Löscht Export-Dateien die älter als 72 Stunden sind."""
    cutoff = datetime.utcnow() - timedelta(hours=72)

    exports = await aql("""
        FOR e IN data_export_requests
          FILTER e.status == 'completed'
          FILTER DATE_TIMESTAMP(e.completed_at) != null
          FILTER DATE_TIMESTAMP(e.completed_at) < DATE_TIMESTAMP(@cutoff)
          RETURN { _key: e._key, file_path: e.file_path }
    """, cutoff=cutoff.isoformat())

    for export in exports:
        if export["file_path"]:
            await delete_file(export["file_path"])
        await update_export_status(export["_key"], "expired")

    return {"expired_count": len(exports)}
```

### 3.3 Logging & Monitoring

Jeder Retention-Lauf wird strukturiert geloggt:

```python
log.info(
    "retention.run_completed",
    task="enforce_retention_policy",
    results={
        "hard_delete_soft_deleted_accounts": {"deleted_count": 3},
        "anonymize_session_ips": {"anonymized_count": 47},
        "cleanup_expired_exports": {"expired_count": 1},
        # ...
    },
    duration_ms=1234,
)
```

Tatsächlich protokolliert jeder Einzel-Task (§3.1) seine eigene Ergebniszeile, z.B. `retention.execute_scheduled_erasures.completed`, `anonymize_old_ips`, `retention.purge_expired_erasure_records` mit Zählern; eine gemeinsame Zeile `retention.run_completed` gibt es nicht.

**Prometheus-Metriken:** **Nicht implementiert** (Stand #1782): Das Backend hat keine Metrik-Pipeline; die folgenden Metriken sind Zielbild (#1800).

```python
retention_records_processed = Counter(
    'retention_records_processed_total',
    'Records processed by retention policy',
    ['category', 'action']  # action: delete, anonymize, expire
)

retention_run_duration = Histogram(
    'retention_run_duration_seconds',
    'Duration of retention policy enforcement run'
)

retention_run_errors = Counter(
    'retention_run_errors_total',
    'Errors during retention policy enforcement',
    ['category']
)
```

### 3.4 Anwendungs- und Zugriffsprotokolle (Log-Pipeline) <!-- #1781 -->

Die Retention-Matrix (§2) regelt Datenbank-Collections und Dateien. Protokollzeilen
fallen nicht darunter: Was die Anwendung auf `stdout` schreibt, liegt so lange vor, wie
die Log-Pipeline des Betreibers es aufbewahrt (Container-Runtime, Node-Rotation, ein
Log-Aggregator wie Loki). Eine Kennung, die dort landet, überdauert deshalb das Konto,
seine Löschung und den Löschnachweis (R-06). Die Anwendung stellt darum sicher, dass
ihre Protokolle keine direkte Kennung einer betroffenen Person enthalten:

| ID | Anforderung | Durchsetzung |
|----|-------------|--------------|
| L-1 | Keine Protokollzeile nennt den Kontoschlüssel. An seiner Stelle steht `subject=` — ein HMAC-SHA256 über den Schlüssel mit `LOG_PSEUDONYM_SALT` und dem Zweck-Label `log-subject` (`sub_…`, zweckgetrennt vom Tombstone-Hash). Der **Mandantenschlüssel** steht in keiner Protokollzeile im Klartext (#1928 neben einer Subjekt-Referenz, seit #2019 überall — Entscheidung (a): eine Zeile ohne Subjekt, die einen Entitätsschlüssel wie `attachment_id` mit einer Subjekt-Zeile desselben Ablaufs teilt, verband Pseudonym und Mandant sonst über diesen Schlüssel): er hängt an den pseudonymisierten Aufbewahrungszeilen und würde das Pseudonym wieder mit dem Mandanten verbinden. Stattdessen steht `tenant=ten_…` (derselbe Salt, Zweck-Label `log-tenant`); der Erasure-Record-Schlüssel `ter_<Mandant>` erscheint als `ter_ten_…`. Das gilt auch für Werte, die den Schlüssel enthalten: der Redis-Dedup-Schlüssel der Benachrichtigungen und ihre Gruppen-Schlüssel (`care:<Schlüssel>:…`) erscheinen nicht, höchstens deren Art (`group_kind=`). | Guard `test_privacy_logs_carry_no_plaintext_subject.py`, Selektor: die gesamten Bäume `src/backend/app/` und `src/backend/scripts/`; er lehnt auch Akteur-Felder (`*ed_by`) ab, die keine Referenz sind (#2020), und verfolgt auch lokale Variablen, die aus dem Schlüssel gebaut sind, und lehnt `dedup_key=`/`group_key=` ab; Guard `test_logs_carry_no_raw_tenant_beside_a_subject.py` (Dateiname historisch) für jeden Mandantenschlüssel an einem Log-Aufruf — mit oder ohne Subjekt —, auch über gebundene Logger, Positionsargumente und f-Strings (keine Ausnahmen, #1989, #2019) |
| L-2 | Keine Protokollzeile nennt eine E-Mail-Adresse. An ihrer Stelle steht ein **gesalzener** Digest (`email_sha256=`, HMAC mit demselben Salt, Zweck-Label `log-email`) — ein ungesalzener SHA-256 wäre per Wörterbuch umkehrbar. | derselbe Guard |
| L-3 | Fehlertexte (`error=`) laufen durch eine Bereinigung: Kontoschlüssel → Referenz, Export-Bundle-Pfade maskiert, Objektschlüssel `t/<Mandant>/…` mit Mandanten-Referenz statt Mandantenschlüssel (#1966); ein Mandantenschlüssel *im Text* — `ter_<Mandant>` oder `t/<Mandant>/…` mit Anhangs-Form oder als Präfix am Ende eines Zitats — wird in jeder Senke durch seine Referenz ersetzt (#2020; ein Mandantenschlüssel in anderer Schreibweise bleibt stehen), E-Mail-Adressen → Digest, Query-Strings und Fragmente aus URLs entfernt, Userinfo (`scheme://user:pw@`) maskiert. Die Bereinigung läuft in linearer Zeit auf einem längenbegrenzten Text. | derselbe Guard (`str(exc)` und `<name>.message` am Log-Aufruf werden abgelehnt) |
| L-4 | IP-Adressen erscheinen in Anwendungsprotokollen höchstens in der R-03-Kürzung (IPv4 letztes Oktett `0`, IPv6 `/48`, Feld `ip_prefix=`). Eine Protokollzeile hält damit nie mehr, als die Datenbank nach sieben Tagen behält. Das gilt auch für Zeilen, die eine Bibliothek selbst schreibt und die den Client nennen (`slowapi`, #2054); der Senken-Filter maskiert IP-Adressen im Allgemeinen nicht, weil ein Infrastruktur-Host in einem Verbindungsfehler für den Betrieb nötig ist. Das gilt seit #1796 auch für die Zugriffsprotokolle (L-7). | Guard (IP-Schlüsselwörter an Log-Aufrufen); Laufzeit-Guard `test_logs_carry_no_client_ip_from_libraries.py` (echtes slowapi, echte Route, beide Prozesse) |
| L-5 | API **und** Celery-Worker starten in Produktion (`DEBUG=false`) nicht ohne gültigen `ERASURE_TOMBSTONE_SALT` und nicht ohne gültigen `LOG_PSEUDONYM_SALT` (je mindestens 32 Zeichen) — ohne den Log-Salt fiele jede Referenz und jeder E-Mail-Digest auf eine Konstante zurück. | `app/main.py::insecure_default_secrets`, `app/tasks/__init__.py` (`celeryd_init`) |
| L-6 | Keine Log-Senke erhält einen API-Schlüssel, ein Passwort oder ein Einmal-Token. Die Logger `httpx`, `httpcore` und `urllib3` stehen in API **und** Worker auf `WARNING`; ein Filter entfernt Query-String und Userinfo aus ihren Zeilen, auch wenn jemand die Stufe senkt. Zugangsdaten im URL-**Pfad** (#1879) maskiert dieselbe Bereinigung in jeder Senke — im Filter dieser Logger (urllib3 nennt das Anfrageziel in seiner Retry-Warnung auf `WARNING`), in Fehlertexten (L-3) und in Tracebacks (L-8): die benannten Formen `/bot<id>:<token>` (Telegram), `/webhooks/<id>/<token>` (Discord) und `/services/T…/B…/<token>` (Slack) sowie jedes andere Pfadsegment ab 32 Zeichen, das wie ein erzeugtes Geheimnis aussieht (Groß- und Kleinbuchstaben mit Ziffern, oder eine Hex-Folge) — etwa das Geräte-Token im Pfad eines Web-Push-Endpunkts. **Grenze:** ein Token unter 32 Zeichen oder ein reiner Kleinbuchstaben-Lauf in einem unbenannten Pfad bleibt stehen; eine Punkt-Kette wird nur maskiert, wenn ihr erstes Segment ein Token ist. An- und Abmeldung einer Web-Push-Subscription protokollieren nur den Host des Push-Dienstes (`endpoint_host=`, #1891). Der Console-Mail-Adapter schreibt den Bestätigungs- oder Passwort-Reset-Link nur mit `DEBUG=true` und nie den Anzeigenamen; ohne SMTP warnt die API beim Start. Beim Anlegen eines API-Schlüssels steht im Protokoll die Kennung des Datensatzes, nicht das Schlüssel-Präfix (`kp_` plus fünf Zeichen des Geheimnisses). | Laufzeit-Guard `test_logs_carry_no_secrets_runtime.py` (echtes httpx, beide Prozesse), statischer Guard `test_logs_carry_no_secrets.py` (Secret-Namen und von ihnen abgeleitete Werte an Log-Aufrufen, seit #1891 auch `endpoint`/`*_endpoint`), Laufzeit-Guard `test_logs_carry_no_url_path_credentials.py` (echtes `requests`/urllib3, beide Prozesse) |
| L-7 | Zugriffsprotokolle nennen weder volle Client-Adresse noch `X-Forwarded-For`, User-Agent, Referrer oder Query-String. uvicorn schreibt die Adresse in der R-03-Kürzung und vom Pfad nur die festen Segmente der Routen (`/api/v1/t/{}/plants/{}`), sodass Tenant-Slug, Kontoschlüssel und Download-Token nicht erscheinen — außer ein Wert gleicht zufällig einem festen Routen-Segment. Dasselbe gilt für das Zugriffsprotokoll des knowledge-service (Query-String maskiert). nginx schreibt ein eigenes Format (`kp_redacted`) mit gekürzter Adresse; SPA-Pfade wie `/password-reset/<token>` erscheinen als `/<spa-route>`. Das nginx-Fehlerprotokoll steht auf `crit`, weil sein Format nicht redigierbar ist; die wenigen Meldungen ab `crit` tragen weiterhin Client-Adresse und Anfragezeile. | Laufzeit-Guard (echte `uvicorn.access`-Records), `nginx -t` und Live-Probe |
| L-8 | Tracebacks laufen durch dieselbe Bereinigung wie L-3: Die Meldung einer Domänen-Ausnahme erscheint nur als Klasse und Fehlercode, jede andere nur bereinigt. Die Bereinigung geschieht beim Erzeugen jedes Protokoll-Records, nicht erst im Handler — ein Handler, den eine Bibliothek oder eine Betreiber-Konfiguration später hinzufügt, schreibt dieselbe bereinigte Zeile. Sie gilt auch für Zeilen ohne angehängte Ausnahme, die während der Behandlung einer Ausnahme geschrieben werden (Celerys Retry-Zeile `Task … retry: …`). Die Task-Daten, die Celery an seine Records hängt (`extra={'data': …}`), verlieren Argumente und Roh-Traceback; der Rückgabewert eines Tasks (Zeile `Task … succeeded in …`) durchläuft die Text-Bereinigung (L-3), und der Mandanten-Lösch-Task gibt seinen Record-Schlüssel nur in der Protokollform zurück (#2020). **Grenze:** Die Bereinigung kennt dort den Kontoschlüssel nicht — ein Schlüssel oder Name im Text einer Standard- oder Drittanbieter-Ausnahme (`KeyError('<key>')`, ArangoDB-Konfliktmeldungen) wird nicht maskiert, nur E-Mail-Adressen, URL-Bestandteile und Export-Bundle-Pfade. Andere `extra=`-Werte als die von Celery bereinigt nur der Handler-Filter. **Ohne Protokoll-Record (#1880):** Eine Ausnahme, die den Prozesseinstieg verlässt (`sys.excepthook`), in einem Thread unbehandelt bleibt (`threading.excepthook`) oder in einem Finalizer auftritt (`sys.unraisablehook`), schreibt der Interpreter selbst nach stderr. Sobald der Prozess sein Logging konfiguriert (`setup_logging`: API-Import, Worker, Migrations-CLIs), geben diese drei Hooks denselben bereinigten Traceback aus; ein zuvor installierter Hook eines Fehler-Trackers läuft weiter, seine Rohausgabe wird verworfen. **Fehler-Tracker (optional, `SENTRY_DSN`):** Das Ereignis von Backend und Worker trägt Ausnahmetexte, Log-Eintrag (Format, Argumente, formatierte Zeile), Nachricht, Kontextfelder und Breadcrumbs nur nach derselben Bereinigung; Query-Strings (Anfrage und `http.query`/`http.fragment` der Breadcrumbs ausgehender Anfragen) nur ohne Werte; lokale Variablen der Stack-Frames werden nicht übertragen (`include_local_variables=False`). **Anfragepfad (#1925):** Anfrage-URL und Transaktionsname des Ereignisses sind das Routenmuster des Frameworks, nie der Rohpfad (Download-Token, Mandanten-Kurzname); ohne Muster reduziert `loggable_path` den Pfad, Query-String und Fragment entfallen, Methode und Host bleiben. Die Nebendienste inference-service und knowledge-service haben keine schlüsselbasierte Bereinigung (kein Salt, keine Routentabelle), sondern seit #1926 die gemeinsame **formbasierte** aus `kp_errortracking` (`shape_text_redactor`: URL-Userinfo, Query und Fragment, Pfad-Zugangsdaten, Token-Segmente, E-Mail-Adressen als `<email>`) für Ausnahmetexte, Log-Eintrag, Nachricht, Breadcrumbs, Schlüssel und Werte von `extra`/`tags`/`contexts`, und dieselben drei Interpreter-Hooks für unbehandelte Tracebacks. **Grenze:** Freitext ohne Form — die Suchfrage einer Person im knowledge-service, ein Name — bleibt in einem Ausnahmetext stehen; die eigenen Protokollzeilen der Nebendienste (ausser dem Zugriffsprotokoll, L-7) tragen keine Text-Bereinigung. | Tests (Nebendienste: je Dienst `tests/test_error_tracking_redacts_texts.py`, echter Subprozess mit dem `app.main` des Dienstes) über den structlog-Renderer, die Record-Factory und den Handler-Filter in API und Worker (`test_tracebacks_carry_no_personal_data.py`, `test_log_redaction_has_no_residual_gaps.py`); echte Subprozesse für die Interpreter-Hooks (`test_uncaught_exceptions_are_redacted.py`) und für das Tracker-Ereignis über den `before_send`-Pfad des SDK (`test_error_tracking_redacts_texts.py`) und den echten ASGI-Pfad der Anfrage (`test_error_tracking_redacts_paths.py`) |
| L-9 | Die Bereinigung ist aktiv, bevor die Anwendung etwas protokolliert: Die API konfiguriert sie beim Import von `app.main` (im Lifespan erneut), der Worker in `after_setup_logger`. Eine ungültige Einstellung beendet den Start mit dem Namen der Variable und dem Grund, **ohne ihren Wert** — Pydantics `input_value=` erschien vorher unbereinigt auf `stderr`, noch vor jeder Log-Konfiguration. | `test_log_redaction_has_no_residual_gaps.py` (Start in einem eigenen Prozess) |

**Log-Salt und Rotation (#1812).** `LOG_PSEUDONYM_SALT` verschlüsselt ausschließlich die
Log-Pseudonyme (`log-subject`, `log-email`) — auch dort, wo eine solche Referenz in einem
Datensatz landet (`requested_by_subject` in Lösch- und Mandanten-Löschnachweisen, die
um die Kontokennung bereinigten `error_message`-Texte von Löschanträgen). Ohne gültigen
Log-Salt verweigert die Löschung deshalb auch mit `DEBUG=true` jeden Lauf, bevor sie etwas
ändert — der Nachweis trüge sonst die Konstante `anon_unavailable`. Der
Tombstone-Hash, der Anfrage-Schlüssel und der Slug-Digest bleiben bei
`ERASURE_TOMBSTONE_SALT`, der nie wechseln darf. Den Log-Salt darf der Betreiber
wechseln (neuer Wert in API **und** Worker, Neustart beider): Protokollzeilen und
`requested_by_subject`-Werte von vor dem Wechsel korrelieren danach nicht mehr mit
späteren, und wer nur den neuen Salt kennt, kann alte Referenzen nicht mehr einer
Kontokennung zuordnen — auch nicht, *welches* Admin-Konto eine gespeicherte Löschung
ausgelöst hat. Soll diese Zuordnung für die R-06-Aufbewahrung (ein Jahr) nachprüfbar
bleiben, bewahrt der Betreiber den ausgemusterten Salt so lange gesichert auf; sonst
erlischt sie mit der Rotation. Weiter bricht nichts — keine Abfrage hängt vom Log-Salt ab.
Referenzen, die vor #1812 geschrieben wurden, sind mit dem Tombstone-Salt gebildet und
bleiben mit ihm nachrechenbar. Der Wert sollte sich vom Tombstone-Salt unterscheiden; die
Anwendung prüft das nicht.

**Aufbewahrung der Log-Pipeline — Betreiberpflicht, entschieden (Q-R3, Betreiberentscheidung
2026-09-26, #1781/#1806).** Auch pseudonyme Referenzen sind personenbezogene Daten
(Erwägungsgrund 26 DSGVO), solange der Salt existiert. Die Aufbewahrungsdauer der
Log-Pipeline MUSS deshalb begrenzt und dokumentiert sein. Sie ist eine
Infrastruktur-Entscheidung des Betreibers (Kubernetes-Log-Rotation, Loki-Retention,
Docker-`json-file`-Rotation) und wird von der Anwendung weder gesetzt noch geprüft; das
Helm-Chart dieses Repositorys betreibt keinen Log-Aggregator.

**Höchstfrist: 30 Tage.** Anwendungs- und Zugriffsprotokolle werden höchstens 30 Tage
aufbewahrt (Fehleranalyse und Sicherheitsvorfälle), mit einer Rotation, die ältere Zeilen
löscht statt archiviert. Das war der ursprüngliche Vorschlag dieser NFR und ist hiermit
bestätigt — keine offene Frage mehr. Die Frist ist im Verzeichnis der
Verarbeitungstätigkeiten (Art. 30 DSGVO) nachzutragen und beim Einrichten oder Ändern des
Log-Aggregators (Loki-Retention, `json-file`-Rotation, Kubernetes-Node-Log-Rotation) auf
diesen Wert zu konfigurieren.

---

## 4. Konfigurierbarkeit

**Umsetzungsstand (#1782, v1.7).** Die Settings-Klasse `Settings` hat kein Präfix; die Umgebungsvariablen heißen trotzdem wie unten (`RETENTION_…`). Jede Frist wird über `RetentionService` gelesen, und der Konstruktor prüft dieselben Unter- und Obergrenzen noch einmal:

<!-- Quelle: Datenschutzplan Q-R9, #1806 GDPR-004 -->
**Obergrenzen (Betreiberentscheidung 2026-09-26, Q-R9, GDPR-004).** Bis hierher hatte jede
konfigurierbare Frist nur eine Untergrenze (`ge=1`) — ein Betreiber konnte
`RETENTION_SOFT_DELETE_RETENTION_DAYS=3650` setzen, und nichts widersprach der
Datenminimierung nach Art. 5(1)(c). Jede Frist dieser Tabelle bekommt deshalb zusätzlich
eine **Obergrenze in Höhe ihres eigenen NFR-Default-Werts** (Spalte „Obergrenze"): Der
Betreiber darf eine Frist zur zusätzlichen Datenminimierung weiter absenken, aber nicht
über den von dieser NFR vorgegebenen Wert hinaus verlängern. Ein Startversuch mit einem
Wert oberhalb der Obergrenze bricht den Start von API **und** Worker ab — Fehlermeldung
nennt Variable und Grenzwert, analog zu den Pflicht-Salt-Prüfungen in §3.4 L-5 (**AK-14**).

| Setting (Umgebungsvariable) | Regel | Default | Untergrenze | Obergrenze | Auch akzeptiert (alter Name) |
|-----------------------------|-------|---------|-------------|------------|------------------------------|
| `RETENTION_SOFT_DELETE_RETENTION_DAYS` | R-01 | 90 | 1 | 90 | `PRIVACY_HARD_DELETE_AFTER_DAYS` |
| `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` | R-01a (#1960) | 7 | 1 | 7 | — |
| `RETENTION_UNVERIFIED_ACCOUNT_DAYS` | R-02 | 7 | 1 | 7 | — |
| `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED` <!-- #2010 --> | R-02 | `false` (Schalter, keine Frist) | — | — | — |
| `RETENTION_IP_ANONYMIZATION_DAYS` | R-03 | 7 | 1 | 7 | — |
| `RETENTION_EXPORT_FILE_RETENTION_HOURS` | R-05 | 72 | 1 | 72 | `PRIVACY_EXPORT_RETENTION_HOURS` |
| `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` | R-06 | 3 <!-- Q-R12 --> | 1 | 3 | — |
| `RETENTION_EMAIL_CHANGE_RETENTION_HOURS` | R-07 | 24 | 1 | 24 | `PRIVACY_EMAIL_CHANGE_TTL_HOURS` |
| `RETENTION_EMAIL_CHANGE_REVERT_DAYS` | R-07a | 7 | 1 | 7 | — |
| `RETENTION_CONSENT_RETENTION_YEARS` <!-- #1946 --> | R-04 | 3 | 1 | 3 | — |
| `RETENTION_CONSENT_IP_ANONYMIZATION_DAYS` <!-- #1946 --> | R-04a | 7 | 1 | 7 | — |
| `RETENTION_INVITATION_RETENTION_DAYS` <!-- #1946 --> | R-12 | 30 | 1 | 30 | — |
| `RETENTION_HARVEST_DATA_MIN_RETENTION_YEARS` <!-- #1789 --> | R-16 | 5 | 5 (CanG) | — | — |
| `RETENTION_TREATMENT_MIN_RETENTION_YEARS` <!-- #1789 --> | R-17 | 3 | 3 (PflSchG §11) | — | — |
| `RETENTION_INSPECTION_MIN_RETENTION_YEARS` <!-- #1789 --> | R-18 | 3 | 3 (PflSchG §11) | — | — |

Sind beide Namen gesetzt, gilt der `RETENTION_…`-Name. **Nicht implementiert** (kein Code liest sie): `SENSOR_*` (R-14; die Intervalle stehen als Literale in `src/backend/app/data_access/timescale/migrations/003_retention_policies.sql`: 90 Tage, 2 Jahre, 5 Jahre; die ADR-003-Stufen je Klassifizierung sind nicht modelliert — siehe „Roadmap-Ziel Retention-Observability" oben), `ACTOR_LOG_*` (R-15, es gibt keinen Aktor-Log-Speicher — dasselbe Roadmap-Ziel). Die R-16..R-18-Einstellungen (#1789) haben die gesetzliche Frist als Untergrenze und keine Q-R9-Obergrenze: Q-R9 gilt für die sieben oben genannten Settings, und eine Obergrenze gleich der Untergrenze machte die Einstellung wirkungslos (engere Lesart; eine Obergrenze wäre eine eigene Betreiberentscheidung). `ERASURE_TOMBSTONE_SALT` heißt im Code `ERASURE_TOMBSTONE_SALT` (ohne Präfix). **Stand v1.18:** `CONSENT_RETENTION_YEARS` (R-04), `RETENTION_CONSENT_IP_ANONYMIZATION_DAYS` (R-04a) und `INVITATION_RETENTION_DAYS` (R-12) werden seit #1912 gelesen und durchgesetzt und haben seit v1.18 (#1946) ebenfalls eine Obergrenze (3 Jahre / 7 Tage / 30 Tage, Betreiberentscheidung); damit gilt die Obergrenze für zehn Settings. Für die als nicht implementiert gekennzeichneten Settings hat eine Obergrenze noch keinen Leser. **Umgesetzt seit v1.16 (#1806):** AK-14 ist in `Settings` (`le=`) und im Konstruktor von `RetentionService` durchgesetzt.

Zielbild (unverändert):

Alle Fristen sind als Konfigurationsparameter definiert und können über Umgebungsvariablen überschrieben werden:

```python
class RetentionSettings(BaseSettings):
    """Konfigurierbare Retention-Fristen."""

    # Personenbezogene Daten
    SOFT_DELETE_RETENTION_DAYS: int = 90          # R-01
    UNVERIFIED_ACCOUNT_DAYS: int = 7              # R-02
    IP_ANONYMIZATION_DAYS: int = 7                # R-03
    CONSENT_RETENTION_YEARS: int = 3              # R-04
    EXPORT_FILE_RETENTION_HOURS: int = 72         # R-05
    ERASURE_AUDIT_RETENTION_YEARS: int = 3        # R-06 (Q-R12)
    EMAIL_CHANGE_RETENTION_HOURS: int = 24        # R-07
    INVITATION_RETENTION_DAYS: int = 30           # R-12

    # Sensordaten (TimescaleDB)
    SENSOR_RAW_RETENTION_DAYS: int = 90           # R-14 Stufe 1 (alle Klassifizierungen)
    SENSOR_HOURLY_RETENTION_YEARS: int = 2        # R-14 Stufe 2 Default (INDOOR_*, GREENHOUSE)
    SENSOR_DAILY_RETENTION_YEARS: int = 5         # R-14 Stufe 3 Default (alle, ohne Opt-in)
    # <!-- Quelle: ADR-003 / W-014 -->
    SENSOR_HOURLY_RETENTION_OUTDOOR_YEARS: int = 5    # R-14 Stufe 2 für OUTDOOR_OPEN
    SENSOR_DAILY_RETENTION_GREENHOUSE_YEARS: int = 10 # R-14 Stufe 3 für GREENHOUSE (Opt-in)
    SENSOR_DAILY_RETENTION_OUTDOOR_YEARS: int = 20    # R-14 Stufe 3 für OUTDOOR_OPEN (Opt-in)
    SENSOR_EXTENDED_RETENTION_REQUIRES_OPTIN: bool = True  # Tenant-Admin muss aktiv zustimmen
    # <!-- /Quelle: ADR-003 / W-014 -->
    ACTOR_LOG_RAW_RETENTION_DAYS: int = 90        # R-15 Stufe 1
    ACTOR_LOG_AGGREGATED_RETENTION_YEARS: int = 1 # R-15 Stufe 2

    # Gesetzliche Mindestfristen (NICHT konfigurierbar unterschreitbar)
    HARVEST_DATA_MIN_RETENTION_YEARS: int = 5     # R-16, CanG
    TREATMENT_MIN_RETENTION_YEARS: int = 3        # R-17, PflSchG
    INSPECTION_MIN_RETENTION_YEARS: int = 3       # R-18, PflSchG

    # <!-- Quelle: Widerspruchsanalyse W-002 -->
    # Audit-Log-Pseudonymisierung (R-06): Pflicht-Setting ohne Default.
    # Backend startet nicht, wenn ERASURE_TOMBSTONE_SALT nicht aus dem Helm
    # Secret bereitgestellt wird — analog zur W-001-Hard-Crash-Strategie.
    # Mindestens 32 Zeichen (256 Bit Entropie). Wechsel des Salts macht
    # alle bestehenden Tombstones nicht mehr deterministisch zuordenbar
    # (was im Compliance-Sinne unkritisch ist — Pseudonymisierung soll
    # gerade nicht reversibel sein), neue Erasures nutzen den neuen Salt.
    # Wechsel daher nur bei Sicherheitsvorfall vornehmen.
    ERASURE_TOMBSTONE_SALT: str = Field(
        ...,                                       # Pflicht — kein Default
        min_length=32,
        description=(
            "Per-Instanz-Salt für SHA-256-Tombstone-Hashes in "
            "PSEUDONYMIZE_AUDIT_COLLECTIONS (REQ-025 §3.1). MUSS aus "
            "einem Secret-Store (Helm Sealed Secret) kommen. Mindestens "
            "32 Zeichen (256 Bit Entropie)."
        ),
    )
    # <!-- /Quelle: Widerspruchsanalyse W-002 -->

    model_config = SettingsConfigDict(env_prefix="RETENTION_")
```

**Wichtig:** Die gesetzlichen Mindestfristen (R-16 bis R-18) sind als untere Schranke implementiert. Die konfigurierbaren Fristen dürfen diese nicht unterschreiten; eine Validierung in der `RetentionSettings`-Klasse stellt dies sicher.

<!-- Quelle: Widerspruchsanalyse W-002 -->
**Pflicht-Setting `ERASURE_TOMBSTONE_SALT` (W-002):**

| Aspekt | Verhalten |
|--------|-----------|
| **Quelle** | Helm Sealed Secret (`RETENTION_ERASURE_TOMBSTONE_SALT`), per Pod als Env-Var |
| **Bereitstellung** | Während Initial-Deployment vom Operator generiert (z.B. `openssl rand -base64 48`) |
| **Pflicht** | `Field(...)` ohne Default — Backend startet ohne dieses Setting nicht (Hard-Crash, analog REQ-027 W-001-Strategie) |
| **Mindestlänge** | 32 Zeichen (Pydantic-Validation `min_length=32`) — sonst Startup-Crash |
| **Rotation** | Nur bei Sicherheitsvorfall. Salt-Wechsel = neue Tombstones sind nicht mehr deterministisch mit alten verknüpfbar (Pseudonymisierung bleibt gültig, lediglich nicht mehr identisch zu früheren Hashes desselben Users — das ist gewollt). |
| **Backup** | Salt MUSS in Disaster-Recovery-Backup enthalten sein, sonst sind bestehende Tombstones nach Restore nicht mehr deterministisch erzeugbar. |
| **Zugriff** | Nur Backend-Pods. Keine Frontend-Exposition, kein Logging. |
<!-- /Quelle: Widerspruchsanalyse W-002 -->

---

## 5. Interaktion mit DSGVO-Löschanfragen (REQ-025)

Wenn ein Betroffener eine Löschanfrage stellt (Art. 17 DSGVO, REQ-025), interagiert das System wie folgt mit den Retention-Fristen:

1. **Sofort löschbar:** Processing Restrictions, Export-Dateien
2. **Soft-Delete + Retention:** User-Account → `status: deleted`, Hard-Delete nach 90 Tagen (R-01)
3. **Anonymisierung/Pseudonymisierung statt Löschung:** Erntedaten (R-16), Behandlungsanwendungen (R-17) und Inspektionsprotokolle (R-18) werden **anonymisiert** (User-Referenz entfernt), aber beibehalten, wenn die gesetzliche Aufbewahrungsfrist noch läuft (Art. 17 Abs. 3 lit. b DSGVO). **Consent Records werden bei Kontolöschung vor Fristablauf pseudonymisiert** (User-Referenz → Tombstone-Hash), nicht sofort gelöscht, und bleiben bis zum Ablauf der 3-Jahres-Frist nach Widerruf aufbewahrt (R-04, Art. 7(1) Nachweispflicht) — **korrigiert per Q-R5 (#1800):** Diese Zeile widersprach bis v1.11 R-04 und stand fälschlich unter Punkt 1 „Sofort löschbar".
4. **Shared Data:** Daten, die mehrere Betroffene betreffen (z.B. Tenant-Ressourcen), werden nicht gelöscht, sondern der User-Bezug wird entfernt

---

## 6. Abnahmekriterien

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Soft-Deleted Accounts werden nach 90 Tagen endgültig gelöscht (inkl. Edges und verknüpfte Collections) | Integration |
| AK-02 | IP-Adressen in `refresh_tokens` werden nach 7 Tagen anonymisiert (IPv4: letztes Oktett → 0) | Integration |
| AK-03 | Export-Dateien werden nach 72 Stunden vom Dateisystem entfernt | Integration |
| AK-04 | Jede Regel aus §3.1 hat einen Celery-Beat-Eintrag mit dem dort genannten Takt (seit v1.7 statt eines Master-Tasks) | Unit |
| AK-05 | Jeder Retention-Task protokolliert seinen Lauf strukturiert (structlog) mit Ergebniszählen | Integration |
| AK-06 | Prometheus-Metriken (`retention_records_processed_total`) werden pro Kategorie inkrementiert — **nicht implementiert** (#1800) | Integration |
| AK-07 | TimescaleDB Continuous Aggregates erzeugen Stunden-/Tagesmittel für Sensordaten | Integration |
| AK-08 | TimescaleDB Retention Policies löschen Rohdaten nach 90 Tagen, Stundendaten nach 2 Jahren, Tagesdaten nach 5 Jahren | Integration |
| AK-09 | Erntedaten und Behandlungsanwendungen werden bei Löschanfrage anonymisiert (User-Referenz entfernt), aber nicht gelöscht | Integration |
| AK-10 | Konfigurierbare Fristen können per Umgebungsvariable überschrieben werden, unterschreiten aber nicht ihre Untergrenze (§4); jede Frist wird aus genau einem Setting gelesen | Unit |
| AK-11 | Unbestätigte Accounts werden nach `RETENTION_UNVERIFIED_ACCOUNT_DAYS` (Default 7) Tagen gelöscht | Integration |
<!-- Quelle: Widerspruchsanalyse W-002 -->
| AK-12 | **Pflicht-Setting `ERASURE_TOMBSTONE_SALT`:** Backend startet nicht, wenn die Umgebungsvariable `RETENTION_ERASURE_TOMBSTONE_SALT` nicht gesetzt oder kürzer als 32 Zeichen ist (Pydantic `Field(..., min_length=32)`). Fehlermeldung verweist auf NFR-011 §4. | Integration |
| AK-13 | **R-06 Phase-Reihenfolge:** Im Erasure-Lauf (REQ-025 §3.5) wird die Pseudonymisierung der `erasure_requests`-Collection AUSGEFÜHRT, bevor der User selbst hard-deleted wird. Der Hard-Delete des Audit-Eintrags selbst erfolgt erst nach Ablauf von `ERASURE_AUDIT_RETENTION_YEARS` (Default 3 Jahre, Q-R12). | Integration |
<!-- /Quelle: Widerspruchsanalyse W-002 -->
<!-- Quelle: Datenschutzplan Q-R9, #1806 GDPR-004 -->
| AK-14 | **Obergrenze je konfigurierbarer Frist:** Für jedes der zehn in §4 gelisteten `RETENTION_*`-Settings verweigert der Start von API und Worker, sobald der gesetzte Wert die in §4 genannte Obergrenze (= NFR-Default) überschreitet; die Fehlermeldung nennt Variable und Grenzwert, nie den gesetzten Wert. Ein Wert an oder unterhalb der Obergrenze startet unverändert. | Unit + Integration |
| AK-14a <!-- #1806 GDPR-008 --> | **Alias-Auflösung ist nicht still:** Ist ein veralteter `PRIVACY_*`-Name der Tabelle in §4 gesetzt, schreibt der Start eine Warnung (`retention_setting_deprecated_name`); sind alter und `RETENTION_*`-Name mit verschiedenen Werten gesetzt, eine Fehlermeldung (`retention_setting_conflict`), die den gewinnenden Namen nennt. Beide Meldungen enthalten Variablennamen, nie Werte. | Unit |
| AK-14b <!-- #1806 GDPR-003 --> | **Nicht beurteilbare Datensätze werden gezählt:** Der Lauf jedes Alters-Selektors, der einen Datensatz ohne lesbares Zeitfeld überspringt (R-02 `cleanup_unverified_accounts`, `ai.cleanup_expired_audit_log`, `mcp.cleanup_expired_audit_log`, `cleanup_orphaned_task_photos`, R-04 `purge_expired_consent_records`, R-07b `expire_email_change_requests`, `glossary.cleanup_expired_cache`), meldet deren Anzahl als `held_undated`. Der Zähler benutzt dasselbe Prädikat wie der Selektor mit umgekehrter Datumsbedingung. | Unit + Integration |
<!-- /Quelle: Datenschutzplan Q-R9, #1806 GDPR-004 -->
| AK-16 <!-- Q-O7, #1793 --> | **Aggregate folgen der Löschung:** Nach `delete_by_tenant` bzw. `delete_by_sensor` enthalten `sensor_hourly` und `sensor_daily` keinen Bucket des gelöschten Mandanten bzw. Sensors — auch nicht für Zeiträume, deren Rohdaten die 90-Tage-Retention schon entfernt hat; Buckets anderer Mandanten/Sensoren (auch mit gleichem `sensor_key`) bleiben erhalten; eine nach der Löschung (oder zwischen Besitzprüfung und Einfügen) eintreffende Messung — über die Route und über die Home-Assistant-Abfrage — hinterlässt weder Rohzeile noch Bucket (#1944, `test_sensor_ingest_after_erase.py`) | Integration (gegen echte TimescaleDB, `test_timescale_aggregate_erasure.py`) |
<!-- Quelle: #1788 -->
| AK-PT-01 | **Persönlicher Mandant geht mit dem Konto:** Nach Abschluss einer Kontolöschung (Selbstbedienung, Plattform-Admin, Bereinigung unverifizierter Konten) ist von jedem persönlichen Mandanten, dessen einziges aktives Mitglied die Person war, keine Zeile mehr übrig außer den Aufbewahrungsdaten nach NFR-011 R-16 bis R-18 (Kontoschlüssel = Tombstone-Hash, Freitextnamen leer); ein `tenant_erasure_records`-Eintrag mit `origin: account_erasure` steht auf `completed`. | Integration + Reach (T2) |
| AK-PT-02 | **Nachweis im Löschauftrag (aktualisiert #1824):** Der Löschauftrag nennt je persönlichem Mandanten das Ergebnis (`erased` mit Schlüssel des Mandanten-Löschnachweises, `absent`) und ist erst `completed`, wenn jeder dieser Mandanten gelöscht oder als `absent` erklärt ist. Der Ergebniswert `retained_other_members` entfällt (Q-E1, #1824; seit v1.19 schreibt ihn kein Lauf mehr, ältere Löschaufträge behalten ihn) — ein persönlicher Mandant wird nie mehr allein wegen weiterer aktiver Mitglieder erhalten; ein Spätbeitritt ergibt `retained_late_joiner` (REQ-025 AK-IE-07). Scheitert die Mandantenlöschung, bleibt der Auftrag offen und der ArangoDB-Plan läuft nicht; die Wiederholung erreicht den Mandanten über die im Auftrag gespeicherten Schlüssel, auch wenn er nicht mehr über den Eigentümer auffindbar ist. | Unit + Integration |
| AK-PT-03 | **Geteilter persönlicher Mandant wird mitgelöscht (ersetzt die bis v1.11 gültige Fassung, Betreiberentscheidung Q-E1/Q-E5, #1824):** Hat ein persönlicher Mandant der Person ein weiteres aktives Mitglied, wird er trotzdem vollständig über das Mandanten-Löschinventar gelöscht, nicht mehr mit anonymisiertem Eigentümer erhalten. Die verbleibenden Mitglieder werden **vor** der Löschung benachrichtigt. Die Regel greift nur bei `tenant_type: personal` — ein organisatorischer Mandant bleibt bei alleiniger verbliebener Mitgliedschaft weiterhin mit anonymisiertem Eigentümerverweis erhalten (Q-E5). Kann das Deployment keinen Mandanten löschen, verweigert die Kontolöschung vor jeder Änderung (REQ-025 AK-IE-02). **Implementiert (v1.19, #1824):** Die Entscheidung liegt in `TenantService._personal_tenant_retention` (nur ein Spätbeitritt erhält den Mandanten); die Benachrichtigung der verbleibenden Mitglieder erfolgt **beim Löschantrag** (REQ-025 §3.1.3), ohne Namen, Adresse oder Gartennamen der Person. **Dauerhaft (v1.21, #1960):** Der Versand wird am Löschauftrag vermerkt und vom täglichen Lauf vor der endgültigen Löschung nachgeholt; für Löschaufträge ohne Vermerk gilt R-01a (§4). Zugesichert ist: jedes erreichbare Mitglied bekommt die Benachrichtigung vor der Löschung, bei später Zustellung mindestens `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` Tage davor; eine die ganze Wartezeit über unzustellbare Benachrichtigung hält die Löschung nicht auf. Die Löschung durch einen Administrator geschieht sofort, die Mitglieder erfahren das in der E-Mail. | Unit + Integration |
| AK-PT-04 <!-- Q-E6, #1825 --> | **Einladungen in den persönlichen Mandanten werden beim Löschantrag widerrufen:** `request_erasure`/`erase_account_now` widerrufen jede offene Einladung (E-Mail- wie Link-Einladung) in jeden persönlichen Mandanten der Person, sofort bei Antragstellung — nicht erst beim Hard-Delete. Siehe REQ-025 AK-IE-06. **Implementiert** (#1825, REQ-025 v1.20). | Unit + Integration |
| AK-PT-05 <!-- Q-E7, #1825 SEC-003 --> | **Erneute Prüfung unmittelbar vor der Löschung:** Die Mitgliederzahl des persönlichen Mandanten wird unmittelbar nach dem atomaren Claim des Löschlaufs und unmittelbar vor der eigentlichen Löschung erneut geprüft. Ist zwischen Antragstellung und Löschung trotz AK-PT-04 ein neues aktives Mitglied beigetreten (SEC-003), wird die Erasure-together-Logik **nicht** angewendet: Der Mandant bleibt erhalten, nur die Person wird anonymisiert (Fallback auf das Verhalten vor #1824). Trifft ein Beitritt mit der erneuten Prüfung zusammen, entscheidet genau eine Seite; „erhalten, aber ohne den Beitretenden" ist kein Ausgang mehr (#1924). Siehe REQ-025 AK-IE-07. **Implementiert** (#1825, REQ-025 v1.20; Beitritt gegen Löschung #1924, REQ-025 v1.28). | Unit + Integration |
<!-- /Quelle: #1788, aktualisiert #1824/#1825 -->
<!-- Quelle: Q-R4/Q-R6/Q-R7, #1793/#1800 -->
| AK-R04a | Die IP-Adresse eines Consent Records wird 7 Tage nach Aufzeichnung anonymisiert (R-04a) und bei erneuter Einwilligung zurückgesetzt | Integration |
| AK-R06a | `tenant_erasure_records` wird spätestens 5 Jahre nach Abschluss der Mandantenlöschung oder — falls früher — nach Ablauf der längsten zugehörigen R-16/R-17/R-18-Frist hart gelöscht (R-06a) | Integration |
| AK-R07b | Eine bestätigte E-Mail-Änderungsanfrage wird nach Ablauf des R-07a-Rückgängig-Fensters vollständig hart gelöscht, nicht nur die Rückgängig-Felder (R-07b) | Integration |
<!-- /Quelle: Q-R4/Q-R6/Q-R7, #1793/#1800 -->

---

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| REQ-023 | User-Datenmodell, RefreshToken-Collection, Celery-Tasks |
| REQ-024 | Membership- und Invitation-Collections |
| NFR-001 | Architektur-Layer (Tasks in Business Logic Layer) |

### Wird benötigt von:

| REQ/NFR | Bezug |
|---------|-------|
| REQ-025 | Datenschutz & Betroffenenrechte — referenziert Löschfristen aus dieser NFR |
| REQ-005 | Sensordaten-Retention (TimescaleDB Downsampling) |
| REQ-018 | Aktor-Log-Retention |

### Neue Infrastruktur-Abhängigkeiten:

| Komponente | Zweck |
|------------|-------|
| Celery Beat | Scheduling der Retention-Einzel-Tasks (§3.1) |
| TimescaleDB Continuous Aggregates | Automatische Sensordaten-Aggregierung |
| Prometheus | Monitoring der Retention-Läufe |

---

## 8. Scope-Abgrenzung

**In Scope:**
- Automatische Durchsetzung aller Retention-Fristen via Celery
- IP-Anonymisierung nach 7 Tagen
- Sensordaten-Downsampling in TimescaleDB (3-stufig)
- Konfigurierbare Fristen mit gesetzlichen Mindestschranken
- Monitoring und strukturiertes Logging

**Nicht in Scope:**
- Manuelle Löschanfragen durch Betroffene → REQ-025
- Consent-Management → REQ-025
- Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) → separates Organisationsdokument
- Datenschutz-Folgenabschätzung (Art. 35 DSGVO) → separates Bewertungsdokument

---

**Dokumenten-Ende**

**Version**: 1.7
**Status**: Genehmigt
**Datum**: 2026-02-27
**Security-Review**: Adressiert SEC-K-001, SEC-K-002, SEC-K-005
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
