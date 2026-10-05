# Spezifikation: REQ-025 - Datenschutz & Betroffenenrechte (DSGVO)

```yaml
ID: REQ-025
Titel: Datenschutz & Betroffenenrechte (DSGVO)
Kategorie: Plattform & Datenschutz
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery, React, TypeScript, MUI
Status: Entwurf
Version: 1.34 (Feldnamen `*_token_hash`, Access Tokens enden mit dem Widerruf; #2158, #2116); 1.33 (#2135: Art.-15-Export enthält den eigenen persönlichen Mandanten, §3.1.2 Regel 1 und Regel 8, AK-DE-02) — v1.32 (#2134: Kontolöschung lässt keine Organisation ohne Verwaltung zurück — Übergabe an die dienstälteste Leitung oder `orphaned` mit Löschfrist, Vorschau nennt beides, AK-FK-08) — v1.31 (#2136: §3.6 nur gelesene Consent-Zwecke, `hibp_check`/`external_enrichment` entfernt, `error_tracking` steuert die Zuordnung des Fehlerberichts) — v1.30 (REQ-055 v1.4: Consent-Text `social_publishing` nennt auch Freigeben/Senden) — v1.29 (REQ-055: Consent-Zweck `social_publishing` für die Übermittlung an soziale Netzwerke) — v1.28 (#1924 Beitritt/Einladung während der Gnadenfrist: genau ein Ausgang, keine Einladung mehr — v1.27 (#1949 Admin-Kontolöschung asynchron, #1992 Bereinigung verschont herabgestufte Konten — v1.26 (#1960/#1961: Benachrichtigung dauerhaft, Admin-Vorschau — v1.25 (#1834: AK-OS-10 Objekt-Rekonziliation — v1.24 Erasure-together + Mandanten-Vorschau, #1824 — v1.23 Beat-Takt von R-02/R-03/R-11 nach der Uhr, #1946 — v1.22 AK-02a/AK-15a/AK-15b umgesetzt: #1806 GDPR-006/-007/-010 — v1.21 #1793: Art. 15 findet pseudonymisierte Aufbewahrungszeilen über den Tombstone-Hash — v1.20 #1825/#1843: Einladungen bei Löschantrag widerrufen, Mitgliederprüfung nach dem Einfrieren — v1.19 Datenschutzplan-Entscheidungen Batch 4-6: Q-T2/Q-T3/Q-T4/Q-T5/Q-E8/Q-R12, #1806/#1839/#1793 — v1.18 Batch 1-3 #1789/#1793/#1800/#1824/#1825 — v1.17 #1848/#1856: eigene Mail und Seite für die E-Mail-Änderung, Formular in den Kontoeinstellungen, Rückgängig-Link an die vorherige Adresse; keine vom Anfragenden gewählten Texte in Mails an unbestätigte Adressen — v1.16 Betreiber-Entscheid Variante 1 zu #1815: E-Mail-Änderung bestätigt sich ohne lokales Passwort primär über eine frische OIDC-Anmeldung, der E-Mail-Code ist nur noch Ausweichweg für ausschließlich GitHub/Apple — v1.15 /code-review of #1862: zustandslose Prüfungen der E-Mail-Änderung laufen jetzt vor dem Step-up, nur der Adress-Nachschlag bleibt dahinter — v1.14 #1841: Step-up auf der E-Mail-Änderung, AK-06 umgesetzt — v1.13 #1813/#1814: Step-up auf jeder Kontolöschung; `DELETE /users/me` eröffnet den Art.-17-Auftrag — v1.12 #1770: deduplizierte Anhänge und Referenz-Vektoren gehören jedem Beitragenden selbst — v1.11 #1768: Löschumfang aus #1761/#1766/#1776 als Abnahmekriterien — v1.10 #1719: Art. 15 legt offen, was Art. 17 löscht; Inventar-Kopie durch Regeln ersetzt))
Abhängigkeit: REQ-023 v1.18 (Benutzerverwaltung), REQ-024 v1.7 (Mandantenverwaltung), NFR-011 v1.4 (Retention Policy), NFR-013 v1.5 (Object Storage), REQ-029-A v1.2 (DINOv2-Referenz-Index), REQ-034 v1.1 (Pflanzenfoto-Galerie), REQ-050 v1.5 (KI-Analyse von Tagebuch-Einträgen), REQ-051 v1.0 (Pflanzen-Tagebuch — Analyse-Archiv)
Security-Review-Referenz: SEC-K-001, SEC-K-003
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.34 | 2026-10-05 | **#2158 / #2116 (Feldnamen und Wirkung nachgezogen):** Die Rücknahme eines E-Mail-Wechsels löscht `password_reset_token_hash`/`-expires` (das Reset-Token liegt nur noch als SHA-256-Hash vor, REQ-023 v1.44). Jede Stelle, die „alle Refresh Tokens invalidiert" (Rücknahme, Bestätigung des Wechsels, Art.-17-Antrag), beendet damit auch die laufenden Access Tokens des Kontos ab der nächsten Anfrage. |
| 1.33 | 2026-10-05 | **#2135 (MT-039, Betreiberentscheidung 2026-10-04):** Gemessen: `DataExportEngine.USER_DATA_MANIFEST` hatte keine Quelle für `sites`, `locations`, `slots`, `plant_instances` und `planting_runs`; `tasks`, `attachments` und `plant_diary_entries` nur über ein Kontofeld (zugewiesene Aufgaben, eigene Uploads, eigene Einträge). Der persönliche Mandant ist nach seinem Eigentümer benannt und `Site.gps_coordinates` dort meist die Wohnadresse — das Bundle sagte darüber nichts. Neu (§3.1.2 Regel 1, fünfte Form): Quellen mit `personal_tenant_scope` legen den **eigenen** persönlichen Mandanten offen — Standorte (mit `gps_coordinates`), Beete/Lagerorte, Stellplätze, Pflanzen, Pflanzdurchläufe, Aufgaben, Tagebuch, Anhang-Metadaten (noch nicht: Sensor-Messwerte, Tank-/Gieß-/Düngeprotokolle) —, begrenzt auf `TenantService.personal_tenant_keys_of(user)`; Organisationsmandanten bleiben ausgenommen (dort nur die Mitgliedschaft und die eigenen Beiträge). `locations`/`slots` werden wie im Mandanten-Löschinventar über ihre Site erreicht (ihr eigenes `tenant_key` füllt kein Schreibpfad, #1397). Neue **Regel 8** (Drittdaten, Art. 15(4)): keine fremden Kontoschlüssel in diesen Quellen; keine Maskierung von Freitext. **Gemessen:** Die vom System erzeugten Benachrichtigungstexte (`notification_service`, `notification_propagation_service`) enthalten keine Anzeigenamen anderer Mitglieder, nur Aufgaben-/Pflanzennamen und Termine. Der Prüfer `scripts/check_privacy_inventory.py` (R2) gleicht eine Garten-Quelle mit dem Mandanten-Löschinventar ab, nicht mit dem Kontoplan. **AK-DE-02**. |
| 1.32 | 2026-10-05 | **#2134 (MT-038, Betreiberentscheidung 2026-10-04):** Gemessen: Der ArangoDB-Plan der Kontolöschung entfernt alle Mitgliedschaften der Person (`ErasureStep memberships`, `executor="account_cascade"`, `erasure_engine.py`) **ohne** die INV-1-Prüfung, die `remove_member`, `leave_tenant` und `change_member_scopes` anwenden (`TenantService._guard_last_manager`). Eine Organisation, deren einzige Verwaltung oder einziges Mitglied die Person war, blieb ohne jemanden zurück, der einladen, verwalten oder löschen konnte — Standorte (GPS), Fotos und Sensordaten ohne Frist. Neu (§3.1.3 Regel 4): Vor dem Plan entscheidet die Kontolöschung je Organisation der Person (`TenantService.settle_organisations_of_erased_account`, Regel `MembershipEngine.departure_settlement`): (a) war sie die letzte Person mit `management`, erhält die **dienstälteste verbleibende Leitung** (frühestes `joined_at`) die Verwaltung — Sicherheits-Audit `via=account_erasure`, alle verbleibenden Mitglieder werden benachrichtigt; (b) bleibt keine Leitung oder gar kein anderes Mitglied, wird die Organisation **`orphaned`** und läuft in die Gnadenfrist der Mandantenlöschung (REQ-024 AK-52, `RETENTION_TENANT_ERASURE_GRACE_DAYS`, Nachweis `origin: orphaned_organisation`); verbleibende Mitglieder und die Plattform-Admins werden benachrichtigt, das Admin-Panel zeigt den Zustand. Eine verwaiste Organisation wird **nicht** zurückgegeben (kein Abbruch, 422): REQ-023 §5a.5 (Notfall-Verwaltung) ist gestrichen. (c) Die Vorschau (`GET /privacy/erasure-preview`, `GET /admin/platform/users/{key}/erasure-preview`) nennt vor der Bestätigung „letzte Verwaltung in Organisation X“ / „niemand mehr in Organisation Y“ (`organizations[]`, **AK-FK-08**). Ersetzt die Q-E5-Aussage „ein organisatorischer Mandant mit der Person als einzigem Mitglied bleibt mit anonymisiertem Eigentümer erhalten“. |
| 1.31 | 2026-10-05 | **#2136 (MT-040) Consent-Zwecke ehrlich gemacht — Orchestrator-Entscheidung im Auftrag des Betreibers, rechtlich zu bestätigen und umkehrbar:** (1) `hibp_check` und `external_enrichment` sind aus `PURPOSES` entfernt: Kein Code las sie. Eine HaveIBeenPwned-Prüfung existiert nicht (`HIBP_ENABLED` ohne Adapter); die GBIF/Perenual-Anreicherung ist ein vom Plattform-Admin bzw. Beat ausgelöster Katalog-Job, der Artnamen und keine personenbezogenen Daten sendet und keinen Nutzer hat, dessen Einwilligung er prüfen könnte. Ein Zweck kommt mit dem Feature zurück, das ihn liest. **Bestehende Einwilligungsdatensätze** zu den beiden Zwecken bleiben unverändert (keine Migration): Art.-15-Export, Kontolöschung und die R-04-Bereinigung behandeln `consent_records` unabhängig vom Zweck; sie erscheinen nicht mehr in der Einwilligungsliste und in der Datenschutzerklärung, Erteilen und Widerrufen antworten mit `422` — es gibt keine Verarbeitung, die eines von beiden schalten könnte. (2) `error_tracking` wird gelesen: Ein Fehlerbericht des Backends trägt die Pseudonyme von Konto und Mandant (`user.id = sub_…`, `user.tenant = ten_…`) **nur** mit erteilter Einwilligung der anfragenden Person; ohne Einwilligung (oder wenn sie nicht lesbar ist) geht der Bericht ohne `user`-Block. Text und Bezeichnung des Zwecks beschreiben das jetzt. Das Ereignis selbst (bereits ohne Bodies, Header-Werte, Rohpfade und Freitexte) hängt nicht an der Einwilligung — §9 nennt dafür das berechtigte Interesse, **rechtlich zu bestätigen**. (3) §3.6 beschreibt den tatsächlichen Mechanismus (`ConsentGuard` in der Fachlogik, nicht eine FastAPI-Dependency) und die Regel, dass nur ein Zweck angeboten wird, den Code liest (Guard `test_consent_purposes_are_read.py`). §2, §3.1, §5 und §9 angeglichen. |
| 1.30 | 2026-10-04 | **Consent-Text `social_publishing` korrigiert (Pre-Merge-Review PR #2096):** Der Zwecktext versprach, ohne Einwilligung sei „nur das Verknüpfen" gesperrt; REQ-055 PS-PRI-054 prüft den Consent aber auch bei Freigeben und sofortigem Senden durch die handelnde Person (z. B. die Leitung, die einen fremden Entwurf freigibt). Beide Texte (DE/EN) nennen jetzt Verknüpfen, Freigeben und Senden. |
| 1.29 | 2026-10-04 | **REQ-055 Plant Identity / Plant Social:** Neuer Consent-Zweck `social_publishing` (§5): Übermittlung von Pflanzen-Beiträgen (Text, Fotos als EXIF-freie Renditions) an einen vom Nutzer gewählten Mastodon-Server, der eigenständiger Verantwortlicher ist und außerhalb der EU stehen kann. Rechtsgrundlage: nutzerinitiierte Veröffentlichung Art. 6(1)(b), automatische Veröffentlichung Art. 6(1)(a); der Consent wird beim ersten Verknüpfen je Nutzer abgefragt und bei `auto`-Regeln für die Person geprüft, die die Regel gesetzt hat (REQ-055 PS-PRI-054). Widerruf: eigene Pflanzen-Verknüpfungen werden widerrufen, eine selbst angelegte Garten-Verknüpfung wird pausiert und die übrigen Leitungen benachrichtigt (PS-PRI-050). Art. 15/17: REQ-055 PS-PRI-051/052 ergänzen `USER_DATA_MANIFEST` (u. a. `plant_events` als Aktivität der Person) und den Erasure-Plan feldgenau; Aufbewahrung NFR-011 R-28…R-37. Light-Modus: Verknüpfungen sind dort verweigert, der Consent entfällt. |
| 1.28 | 2026-10-04 | **#1924 AK-IE-06/AK-IE-07 geschlossen:** (1) **Kein Restfenster mehr** — ein Beitritt, der mit der zweiten Mitgliederlesung der Kontolöschung zusammenfällt, endet in genau einem Ausgang: entweder bleibt die Mitgliedschaft bestehen und der Mandant wird erhalten (`retained_late_joiner`), oder die Mitgliedschaft wird abgelehnt und der Mandant gelöscht — nie „erhalten, aber ohne den Beitretenden“. Die Rücknahme des Beitritts (`delete_while_tenant_frozen`) ist ein einziges AQL-Statement, das den Löschauftrag liest, **schreibt** und die Mitgliedschaft entfernt; die Rücknahme des Eintrags durch die Kontolöschung (`delete_unclaimed`) schreibt dasselbe Dokument, sodass beide nicht nebeneinander gewinnen. `TenantService._decide_retention_under_freeze` nimmt den Eintrag **zuerst** zurück und liest die Mitglieder danach erneut; findet die erneute Lesung niemanden mehr, wurde der Beitretende zurückgenommen — der Mandant wird erneut eingefroren und die Entscheidung wiederholt (höchstens dreimal, danach `WriteConflictError` und Wiederholung durch den täglichen Lauf). (2) **Einladungen während der Gnadenfrist:** `create_email_invitation`, `create_link_invitation` und `accept_invitation` lehnen eine Einladung in einen persönlichen Mandanten ab (403), dessen Eigentümer einen offenen Löschauftrag hat (`find_active_for_user`); organisatorische Mandanten sind nicht betroffen. Das Prädikat steht einmal im Dienst (`_refuse_invitation_while_owner_erasing`), ein Guard (`test_joins_and_invitations_ask_the_erasure_freeze`) leitet jeden Mitgliedschafts- und Einladungs-Schreibaufruf aus dem Quelltext ab. |
| 1.27 | 2026-10-03 | **#1949 / #1992:** (1) `DELETE /admin/platform/users/{key}` antwortet `202 Accepted` (Körper `{erasure_key, status, requested_at, message}`; brechend, vorher `204`): Auftrag anlegen, Konto sperren, Mitglieder jetzt benachrichtigen und an den Celery-Task `retention.run_account_erasure` übergeben; das Ergebnis (`completed` bzw. `partially_completed`) steht am Auftrag, lesbar über `GET /admin/platform/erasures/{erasure_key}` (nur Plattform-Admin). Die früheren Antworten 500 `ERASURE_INCOMPLETE` und 502 gibt es für diesen Weg nicht mehr (**AK-IE-01**, **AK-IE-03**). (2) Die Bereinigung unverifizierter Konten löscht nur Konten, die **nie bestätigt** waren: Senkt ein Administrator `email_verified` eines bestätigten Kontos, wird das mit `email_verified_lowered_at` vermerkt und das Konto nie bereinigt; die Senkung von `email_verified` und `is_active` verlangt das Step-up des Administrators wie das Anheben (REQ-023 §3.9, **AK-IE-09**). (3) Die Bereinigung benachrichtigt die anderen Mitglieder eines persönlichen Mandanten wie die übrigen Sofortwege (**AK-IE-09**). |
| 1.26 | 2026-10-02 | **#1960 Benachrichtigung dauerhaft, #1961 Vorschau für die Administrator-Löschung:** (1) Die Benachrichtigung der anderen Mitglieder (§3.1.3) wird am Löschauftrag vermerkt (`members_notified_at`, `members_notified_count`, `members_notice_failures`, gesalzene Empfängerreferenzen; keine Adresse). Der tägliche Lauf stellt eine nicht versandte Benachrichtigung vor der endgültigen Löschung zu (**AK-IE-08**); ein Löschauftrag aus der Zeit vor #1824 trägt keinen Vermerk, wird beim ersten Sehen benachrichtigt und frühestens `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` (Standard 7) Tage danach gelöscht (NFR-011 R-01a). Zugesichert ist damit nur, was hält: kein Mitglied wird ohne Versuch gelöscht, bei später Zustellung bleibt ihm die Wartezeit, und eine die ganze Wartezeit unzustellbare Benachrichtigung (kein Mailversand eingerichtet) hält Art. 17 nicht auf. (2) **Betreiberentscheidung (#1961):** Die Löschung durch einen Plattform-Administrator (`DELETE /admin/platform/users/{key}`) bleibt eine **Sofortlöschung ohne Karenzzeit**; die anderen Mitglieder erfahren in der E-Mail, dass die Löschung jetzt stattfindet, und die Vorschau sagt es ebenso. Eine Wartezeit gilt für diesen Weg nie (`immediate_erasure`), auch nicht bei einem Wiederholungsversuch durch den täglichen Lauf. Neu: `GET /admin/platform/users/{key}/erasure-preview` (nur Plattform-Admin; Form wie `GET /privacy/erasure-preview`, **AK-FK-07**). |
| 1.25 | 2026-10-02 | **#1834 AK-OS-10 umgesetzt:** Ein täglicher Rekonziliationslauf (`reconcile_orphaned_storage_objects`, NFR-013 §6.6) findet Objekte unter `t/`, die kein `attachments`-Datensatz mehr hält — die Reste, die die vier Pfade der Issue (fehlgeschlagener Storage-Aufruf nach dem committeten Plan, Datensatz im Fenster zwischen Phase 0 und Plan, generisch hochgeladene Schädlingsreferenz in einem verlassenen Mandanten, Storage-Delete nach entferntem Datensatz) hinterlassen. Löschen ist per Default aus (`STORAGE_RECONCILE_DELETE_ENABLED`); der Lauf berichtet nur Zahlen. Die Reach-Proben `requirement-req025-art17-storage-*` verankern weiter §3.1.3; sie sind nicht neu abgeleitet. |
| 1.24 | 2026-10-02 | **Erasure-together umgesetzt (#1824, Q-E1/Q-E5/Q-T6):** Ein persönlicher Mandant (`tenant_type: personal`) wird bei jeder Kontolöschung mitgelöscht, auch mit weiteren aktiven Mitgliedern — `TenantService._personal_tenant_retention` entscheidet nicht mehr nach „anderes Mitglied vorhanden", sondern nach „Mitglied nach dem Einfrieren hinzugekommen" (AK-IE-07; ein Spätbeitritt erhält den Mandanten). Der Ergebniswert `personal_tenants[].outcome = retained_other_members` wird nicht mehr geschrieben; ein erhaltener Mandant meldet `retained_late_joiner`, der alte Wert bleibt für vor #1824 gespeicherte Löschaufträge lesbar. Die verbleibenden aktiven Mitglieder werden **beim Löschantrag** (`request_erasure`; bei `erase_account_now` unmittelbar vor dem Lauf, nicht bei der Bereinigung unverifizierter Konten) per E-Mail benachrichtigt — mit dem Datum der endgültigen Löschung, ohne Namen, Adresse oder Gartennamen der Person (ein persönlicher Mandant ist nach seinem Eigentümer benannt); ein Versandfehler bricht den Antrag nicht ab. **AK-FK-06 umgesetzt:** neuer Endpunkt `GET /privacy/erasure-preview` und Mandanten-Vorschau im Tab „Konto löschen" und im Löschdialog der Kontoeinstellungen. `retained_reason` der Bestätigung (AK-08a) beschreibt die neue Regel. |
| 1.23 | 2026-10-02 | **#1946 (Folgearbeit zu #1806):** Abschnitt „Inhalt der Übersicht" (`latest_deletion_point`) — die Aussage „Frist plus ein Takt" ist nur zugesichert, weil R-02, R-03, R-11 (und R-12) uhrzeitverankert laufen (`crontab`, NFR-011 §3.1, v1.18) und nicht als fester Abstand ab dem Start des Beat-Prozesses, der bei jedem Pod-Neustart neu begänne. Die Obergrenzen für R-04/R-04a/R-12 und der R-06-Default 3 stehen in NFR-011 v1.18. |
| 1.22 | 2026-10-02 | **AK-02a, AK-15a und AK-15b umgesetzt (#1806, GDPR-006/-007/-010):** Der Frontend-Text `pages.privacy.exportExpired` nennt keine feste Stundenzahl mehr (R-05 ist ein Setting; der Text sagte „72 Stunden“ auch bei einem anderen Wert); die in AK-02a genannten Schlüssel `availableForHours`/`delete.warning` existieren im Frontend nicht und bleiben Zielbild. `GET /privacy/policy` liefert je Zeile `rule_id`, `latest_deletion_point`, `enforcement_status` und `exception_note`; neue Zeilen für R-07, R-11 und R-18, R-04 trägt `enforced`, R-16..R-18 `partial` (gelöscht werden nur Zeilen eines gelöschten Mandanten, NFR-011 v1.15). **Abweichung vom Zielbild:** `retention_period` behält seinen Namen (statt `period_text`), weil es die bestehende Antwortform ist und kein Client die Umbenennung braucht. |
| 1.21 | 2026-09-30 | **#1793 Teil 1 umgesetzt:** §3.1.2 Regel 6 / **AK-DE-01** — der Art.-15-Export findet die von einer Mandantenlöschung pseudonymisierten R-16/R-17/R-18-Zeilen eines weiterhin aktiven Kontos über dessen Tombstone-Hash, bei mandantengebundenen Quellen nur in Zeilen gelöschter Mandanten. Ablauf dieser Zeilen und des Mandanten-Löschnachweises siehe NFR-011 v1.15 (#1789, R-06a). |
| 1.20 | 2026-09-30 | **AK-IE-06 und AK-IE-07 umgesetzt (#1825), Löschantrag gehärtet (#1843):** Einladungen in persönliche Mandanten werden bei Antragstellung widerrufen (beide Einstiege, plus Rückfalllösung beim Hard-Delete); die Mitgliederprüfung des persönlichen Mandanten läuft zweimal — vor und nach dem Freeze-Eintrag — und ein Beitritt, der zwischen Prüfung und Einfügen der Mitgliedschaft vom Freeze überholt wird, wird zurückgenommen. Die Erasure-together-Regel (#1824) bleibt offen; die Entscheidung ist an einer Stelle gekapselt. `request_erasure` legt den Antrag unter demselben deterministischen Schlüssel an wie die Sofortlöschung (höchstens ein offener Antrag je Konto, ein gleichzeitiger zweiter Aufruf erhält denselben Datensatz) und verweigert mit 503 `FEATURE_NOT_CONFIGURED`, **bevor** Step-up verbraucht, Konto geschlossen oder etwas geschrieben wird, wenn die Installation nicht löschen kann. |
| 1.19 | 2026-09-26 | **Datenschutzplan-Entscheidungen, Batch 4–6 (#1806, #1839, #1793):** §3.1.2 neue Regel 7 (nach der in v1.18/Batch-1-3 eingefügten Regel 6) präzisiert Regel 5 (`attribution_gap`) für die vor #1770 zusammengeführten Anhänge, deren zweiter Hochlader nicht rekonstruierbar ist (Q-T2, **AK-01b**). §3.1.3 neue Regel 6 (Batch-1-3 fügte dort nur einen unnummerierten Absatz ein, keine neue Regelnummer): Bleiben nach einer Löschung geteilte Bytes bei einem fremden Datensatz bestehen (AK-OS-08) und betrifft der Inhalt erkennbar die gelöschte Person, wird der verbleibende Halter benachrichtigt (Art. 19, Q-E8, **AK-OS-09**). `PrivacyPolicyResponse.retention_summary` (§3.4) präzisiert: nennt den spätesten konkreten Löschzeitpunkt statt nur die Frist, die R-02-Ausnahme für Konten mit verknüpftem Anmeldeweg, und listet R-04/R-07/R-11 mit ihrem tatsächlichen (unvollständigen) Durchsetzungsstand (Q-T3/Q-T4, **AK-15a/AK-15b**). Kein UI-Text codiert eine Aufbewahrungsfrist fest — §4.2/§4.3 verlangen die Interpolation des von der API gelieferten Werts (Q-T5, GDPR-006, **AK-02a**). R-06 (NFR-011, Löschaudit `erasure_requests`) ist jetzt 3 statt 1 Jahr (Q-R12) — eigenständiger Wert, nicht an die tenant-gebundene R-06a-Formel aus Batch 1-3 gekoppelt; §1.1 Szenario 3 und §3.1.3 nachgeführt. |
| 1.18 | 2026-09-26 | **Datenschutzplan-Betreiberentscheidungen, Batch 1-3 (#1789, #1793, #1800, #1824, #1825; reine Spec-Änderung, Umsetzung folgt in eigenen PRs).** **Q-E1/Q-E5 (#1824):** §3.1.3 Regel 2 gilt für den persönlichen Mandanten nicht mehr — er wird bei Kontolöschung immer mitgelöscht (auch mit weiteren aktiven Mitgliedern), nicht mehr mit anonymisiertem Eigentümer erhalten; die verbleibenden Mitglieder werden vorher benachrichtigt. Gilt nur für `tenant_type: personal` (organisatorische Mandanten unverändert). **Ersetzt** die in NFR-011 v1.8/AK-PT-03 dokumentierte Retained-Entscheidung. **Q-T6 (#1824):** §4.2 „Tab Account löschen" bekommt eine Mandanten-Vorschau vor der Bestätigung; neue **AK-FK-06**, noch nicht implementiert. **Q-E6/Q-E7 (#1825, SEC-001/SEC-003):** neue **AK-IE-06** (Einladungen in den persönlichen Mandanten werden beim Löschantrag sofort widerrufen) und **AK-IE-07** (erneute Mitgliederprüfung unmittelbar vor der Löschung; ein Spätbeitritt erhält den Mandanten und anonymisiert nur die Person), beide noch nicht implementiert. **Q-T1 (#1793-1):** §3.1.2 Punkt 6 neu — der Art.-15-Export muss für ein noch aktives Mitglied eines gelöschten Mandanten zusätzlich auf den Tombstone-Hash prüfen, nicht nur auf `*_by_key`; neue **AK-DE-01**, noch nicht implementiert. **Q-R5 (#1800/NFR-011 R-04):** §3.1.3 Punkt 3 (Pseudonymisierungsliste) um Consent Records ergänzt — sie werden bei Kontolöschung vor Fristablauf pseudonymisiert, nicht gelöscht (siehe NFR-011 §5, jetzt widerspruchsfrei). |
| 1.17 | 2026-09-26 | **E-Mail-Änderung vollständig (#1848) und Mail-Texte ohne fremdes Markup (#1856):** Die neue Adresse erhält eine eigene Mail mit dem Link `{frontend}/email-change/{token}`; die Seite ruft `POST /privacy/email-change/confirm` auf. Bis dahin öffnete der Link die Kontobestätigungsseite (`POST /auth/verify-email`), die den Token ablehnte. Die Kontoeinstellungen haben ein Formular für die E-Mail-Änderung mit Step-up (REQ-023 §3.9). Die Info-Mail an die vorherige Adresse enthält einen Rückgängig-Link (`{frontend}/email-change/revert/{token}` → `POST /privacy/email-change/revert`): einmalig, gültig `RETENTION_EMAIL_CHANGE_REVERT_DAYS` (7 Tage). Er stellt die vorherige Adresse als bestätigt wieder her, sofern sie noch frei ist, meldet alle Sitzungen ab, entwertet einen Passwort-Reset-Token, widerruft offene E-Mail-Änderungen, entfernt seit der Beantragung verknüpfte föderierte Anmeldewege, widerruft seit der Beantragung erstellte API-Keys und schließt die Rückgängig-Fenster später bestätigter Änderungen; die Adresse, die das Konto dabei wieder verlässt, wird benachrichtigt. Mails an eine noch nicht bestätigte Adresse (Registrierung, E-Mail-Änderung) enthalten keinen vom Anfragenden gewählten Text mehr (kein Anzeigename); jeder andere Platzhalter in HTML-Mails wird escaped. `EmailChangeRequest` erhält `previous_email`, `revert_token_hash`, `revert_expires_at`, `reverted_at` und den Status `reverted`. Aufbewahrung in NFR-011 R-07. Neue **AK-EC-03**, **AK-EC-04**. |
| 1.16 | 2026-09-26 | **Frische OIDC-Anmeldung als Regelfall der E-Mail-Änderung ohne lokales Passwort (#1815, Betreiber-Entscheid Variante 1, siehe REQ-023 §3.9):** `POST /privacy/email-change` nimmt zusätzlich `step_up_token` — den Regelfall für ein Konto mit mindestens einem OIDC-fähigen verknüpften Anbieter (Google, generisches OIDC); der per E-Mail zugeschickte Code (`step_up_code`) bleibt nur für ein Konto, dessen Anbieter ausschließlich GitHub und/oder Apple sind. §3.2-Pseudocode, der §3.3-Absatz zum Step-up, das Schema und **AK-EC-01** entsprechend präzisiert. |
| 1.15 | 2026-09-25 | **Prüfreihenfolge der E-Mail-Änderung präzisiert (/code-review of #1862):** Nur die zustandslosen Prüfungen der neuen Adresse (identisch mit der eigenen, reservierte Tombstone-Domain — beide 422) laufen vor dem Step-up nach REQ-023 §3.9; sie verbrauchen deshalb keinen per E-Mail zugeschickten Code und keinen gedrosselten Versuch. Der Nachschlag, ob die Adresse bereits vergeben ist, bleibt weiterhin hinter dem Step-up (kein Adress-Orakel ohne bestandene Bestätigung). §3.2-Pseudocode und **AK-EC-01** entsprechend präzisiert — keine Verhaltensänderung außer der Reihenfolge der beiden 422-Prüfungen. |
| 1.14 | 2026-09-25 | **#1841 Step-up auf der E-Mail-Änderung; AK-06 jetzt umgesetzt:** `POST /privacy/email-change` läuft durch denselben Step-up wie die Kontolöschung (REQ-023 §3.9) — das aktuelle Passwort bei lokalem Konto, sonst der per E-Mail zugeschickte Einmalcode (`step_up_code`, #1815); API-Key/Service Account 403, gedrosselt im selben Budget (429 `STEP_UP_LOCKED`), geprüft **bevor** die neue Adresse validiert oder nachgeschlagen wird, damit die Route ohne bestandenen Step-up nichts über belegte Adressen verrät. Die **aktuelle** Adresse wird jetzt bei jeder Beantragung benachrichtigt (neu, beide Zweige — freie und bereits vergebene Adresse), die **alte** weiterhin bei der Bestätigung (AK-06, jetzt umgesetzt). Ein Passwort-Reset, eine Passwortänderung (beide hinter dem Step-up) und "alle Sitzungen abmelden" widerrufen jetzt eine offene E-Mail-Änderung — sie kann danach nicht mehr bestätigt werden. Offen bleibt: keine eigene Oberfläche für die E-Mail-Änderung und kein Rückgängig-Link nach einer Bestätigung (#1848). Neue **AK-EC-01**, **AK-EC-02**. |
| 1.13 | 2026-09-25 | **#1813/#1814 Step-up auf jeder Kontolöschung:** `POST /privacy/erasure` und `DELETE /users/me` nehmen denselben Body `{confirm_email, password?}` — die eigene E-Mail wird zurückgetippt (422), das aktuelle Passwort bei lokalem Konto (401), API-Key/Service Account 403, gedrosselt nach REQ-023 §3.9 (429 `STEP_UP_LOCKED`). `DELETE /users/me` schrieb bis dahin nur einen Tombstone ohne Löschauftrag und ließ alle personenbezogenen Daten liegen; es eröffnet jetzt den Art.-17-Auftrag mit Karenz. `DELETE /admin/platform/users/{key}` verlangt die E-Mail des Zielkontos und das Passwort des Admins; der Auftrag hält `step_up` und `requested_by_subject`. Neue **AK-IE-04**, **AK-IE-05**. |
| 1.12 | 2026-09-25 | **#1770 Deduplizierte Inhalte haben keinen einzelnen Eigentümer mehr:** Bisher erhielt ein zweiter Upload identischer Bytes im Mandanten den Anhang-Datensatz des *ersten* Hochladers (`created_by` blieb dieser), und ein zweiter Beitrag desselben Fotos zum Referenz-Index fiel — mandantenübergreifend — auf die Zeile des ersten Beitragenden. Die Löschung des ersten traf damit Inhalte des zweiten, die des zweiten erreichte nichts. **AK-OS-08:** Jeder Hochlader hat einen eigenen Anhang-Datensatz; identische Bytes liegen einmal im Object Storage und werden erst mit dem letzten Datensatz gelöscht, der sie hält. Phase 0 zählt entfernte und wegen Teilung behaltene Objekte (`storage_objects_removed` / `storage_objects_retained_shared`). Keine mandantenübergreifende Teilung. **AK-OS-05b:** Die Datensatz-ID eines Referenz-Beitrags ist pro Mandant und Beitragendem eindeutig; identische Fotos zweier Beitragender sind zwei Zeilen. Migration **v0062** gibt bestehenden Schädlingsbild-Beiträgen einen eigenen Datensatz. |
| 1.11 | 2026-09-25 | **#1768 Gelandeter Löschumfang als Abnahmekriterien:** Die Spec nennt jetzt, was #1761, #1766 und #1776 im Code bereits umgesetzt haben. **AK-OS-05a** (#1761/#1753): Der Referenz-Index wird über eine echte Bindung gelöscht; die No-op-Bindung verweigert, sobald Beiträge existieren, statt `0` zu melden, und der Löschauftrag nennt Bindung und Anzahl. **AK-OS-06** (#1760): Ein hart gelöschtes Original nimmt seine WebP-Vorschaubilder mit. **AK-OS-07** (#1759): Beigesteuerte Schädlings-Prototypen im pgvector-Index `pest_embeddings` werden bei Kontolöschung (jeder Status) und Mandantenlöschung gelöscht, nicht nur deaktiviert. **AK-IE-01..03** (#1767): Die Kontolöschung durch Plattform-Admins und die Bereinigung unverifizierter Konten laufen über dieselbe Finalisierung wie Art. 17 — persistierter Löschauftrag mit `origin` als Nachweis, `completed` nur ohne unerreichten Schritt, Wiederholung, Konfigurationsprüfung vor jeder Änderung, ein Lauf pro Konto. Die REQ-025-Reach-Proben unter `project/reach-probes/` sind in derselben Änderung neu abgeleitet. |
| 1.10 | 2026-09-24 | **#1719 Offenlegung folgt der Löschung, Inventare nur im Code:** Guard-Regel R2 in `scripts/check_privacy_inventory.py` prüft jetzt beide Richtungen: Jede Collection, die die Löschung als Daten der Person entfernt oder anonymisiert, steht im Art.-15-Manifest oder mit Begründung in `DataExportEngine.EXCLUDED_FROM_DISCLOSURE`. Vorher gemessen: 20 Collections ohne Offenlegung. **Neu offengelegt:** `user_favorites` (die Kantenzeile selbst, gefiltert über `_from`), `api_keys` (ohne `key_hash`), `user_preferences`, `onboarding_states`, `pest_detections` (ohne `image_hash`); `plant_diagnosis_requests` zusätzlich mit `inspection_key`, `harvest_observation_key`, `phenotype`, `confirmed_labels`, `created_at`. **Begründet ausgeschlossen:** 15 Kanten, deren Endpunkte offengelegte Dokumente sind und deren Attribute (falls vorhanden) offengelegte Felder kopieren (`has_api_key`, `has_membership`, `membership_in`, drei Standort-Zuweisungs-Kanten, drei Schädlingserkennungs-Kanten, `notification_for_run`, vier `cv_*`-Kanten, `has_invitation`). §3.1 führt keine Abschrift der beiden Inventare mehr, sondern die Regeln (Offenlegung, Löschung/Anonymisierung/Pseudonymisierung mit Aufbewahrungsgründen, Ausschlussprinzip) und Verweise auf `data_export_engine.py` / `erasure_engine.py`. Neues Abnahmekriterium AK-01a. |
| 1.9 | 2026-09-24 | **#1716 Export-Quellen ohne Gegenstück im Code:** Die beiden `DataSourceDefinition`s für `tenant_species_config` und `tenant_cultivar_config` (v1.3, ADR-002) sind aus der Manifest-Kopie in §3.1 genommen und als **nicht implementiert** gekennzeichnet. Gemessen: Keine der beiden Collections hat eine Konstante in `collections.py`, ein Modell oder ein Repository; das Tenant-Overlay aus REQ-001 v4.0 existiert nicht. Was es gibt — mandanteneigene `species`/`cultivars` (`tenant_key`, #1090) und die Freigabekanten `tenant_has_access` (#1092) — trägt keinen Nutzerschlüssel und ist deshalb keine Art.-15-Quelle zur betroffenen Person. Ebenso als nicht implementiert gekennzeichnet: der `SpeciesReferenceResolver` (ADR-002). Die vier `cv_*`-Kanten im Löschinventar stehen jetzt als `ErasureStep`s da, wie in `erasure_engine.py`, statt als Kommentar. |
| 1.8 | 2026-09-24 | **#1700 Vollständigkeit des Löschinventars:** Guard-Regel R6 in `scripts/check_privacy_inventory.py` ankert außerhalb der beiden Listen, an den Modellfeldern (`user_key`, `*_user_key`, `*_by_key`, `*_account_key`, `*_by`): Jedes gespeicherte Feld dieser Form muss vom Löschinventar erreicht oder in `ErasureEngine.EXCLUDED_USER_REFERENCES` mit Begründung ausgeschlossen sein. Vorher gemessen: 23 Felder in keiner der beiden Listen. **Gelöscht:** `ai_conversations`, `ai_tip_cache` (`dismissed_by`, REQ-031 §7.5; nach Review anonymisiert statt gelöscht, weil der Tipp mandantenweit gilt), `notifications` (+ `notification_for_run`), `notification_preferences`, `calendar_feeds` (der Feed-Token liefert danach nichts mehr), `plant_diagnosis_requests` (+ vier `cv_*`-Kanten), angenommene `invitations` (`accepted_by_user_key`, + `has_invitation`), `attachments` der Kategorie `pest_reference` (Bytes bereits gelöscht), `mcp_idempotency_record`, `location_assignments` (über `memberships`, `via` jetzt auch für Dokumente; + drei Zuweisungs-Kanten). **Anonymisiert (`_anonymized`):** `task_comments.created_by`, `invitations.invited_by_user_key`, `pest_image_contributions.promoted_by`, `attachments.created_by` (Rest), `ai_audit_log.user_key` (REQ-031 §7.5), `import_jobs.uploaded_by`, `weather_source_configs.updated_by`, `manual_overrides.created_by`, `tenants.owner_user_key` — beim persönlichen Mandanten zusätzlich `name`/`slug` → `anonymized-<Hash>` (aus dem Tombstone, Präfix reserviert) (`rename_fields`/`rename_when`). **Pseudonymisiert:** `mcp_audit_log.service_account_key`. **Ausgeschlossen (Freitext bzw. kein Kontoschlüssel):** `performed_by` in vier Protokoll-Collections, `workflow_templates.created_by`, `task_audit_entries.changed_by`, `sync_runs.triggered_by`. Der Mitgliedschaftsblock ist jetzt `account_cascade` (Bereinigung unbestätigter Konten läuft über die volle Löschung `erase_account`). Alle neuen Kategorien stehen im Art.-15-Manifest; `location_assignments` mit `disclosure_gap`. Löschprotokolle tragen statt des Klartext-Schlüssels den Tombstone-Hash (`subject`). |
| 1.7 | 2026-09-23 | **#1663 Nutzerfeld im Löschinventar:** Jeder `edge`-/`document`-Schritt von `ErasureEngine.DELETE_STEPS` nennt das Feld, über das die Zeilen des Nutzers gefunden werden (`user_field`; bei Kanten der Endpunkt `_from`/`_to`, ggf. mit `via` auf die Eltern-Collection), durchgesetzt von Guard-Regel R5 in `scripts/check_privacy_inventory.py`. Gemessen und ergänzt: `has_api_key`, `has_membership` und `user_favorites` fehlten im Inventar; `membership_in` und die drei Schädlingserkennungs-Kanten berühren `users` nicht und werden über `memberships` bzw. `pest_detections` erreicht. `quality_assessments` erhält das serverseitige `assessed_by_key` (Migration v0057, kein Rückschluss aus Freitext) und eine `tombstone_hash`-Regel (NFR-011 R-16); `yield_metrics` trägt kein Nutzerfeld. Die Code-Kopie in §3 ist an den Code angeglichen (vorher Freitextfelder `harvester`/`applicator`/`inspector` und Marker `"[gelöscht]"`). AK-DA-04/05 als nicht implementiert gekennzeichnet — `plant_diary_analyses` existiert im Code nicht. |
| 1.6 | 2026-08-16 | **REQ-051 Analyse-Archiv:** REQ-051 §5 fuehrt die Collection `plant_diary_analyses`, in der jeder abgeschlossene Analyselauf eines Tagebuch-Eintrags aufbewahrt wird. Damit entstehen zwei personenbezogene Felder ausserhalb des Eintragsdokuments (`requested_by`, `claimed_by`), die die drei Regeln aus v1.5 nicht erfassten — ohne Ergaenzung waere ein geloeschter Nutzer im Archiv weiterhin namentlich zugeordnet, waehrend er am Eintrag selbst bereits anonymisiert ist. Zwei neue `AnonymizationRule`-Eintraege schliessen die Luecke; die Abwaegung ist dieselbe wie beim Eintragsdokument (Anonymisierung statt Hard-Delete, weil der Lauf zum Pflanzen-Datensatz eines womoeglich geteilten Mandanten gehoert). Neue Abnahmekriterien AK-DA-04 (Anonymisierung) und AK-DA-05 (Art.-15-Auskunft umfasst die archivierten Laeufe). |
| 1.5 | 2026-08-04 | **REQ-050 KI-Analyse von Tagebuch-Einträgen:** Neuer Consent-Purpose `diary_ai_analysis` (Art. 6(1)(a), opt-in **je Eintrag**, nie automatisch). Gleichzeitig **Widerspruch aufgelöst:** Der Zwecktext von `ai_tenant_data_access` sagte pauschal, Tagebuch-Freitexte würden „NIE" übertragen. Diese Zusage gilt für den **serverseitigen** Assistenten (REQ-031) und ist entsprechend präzisiert; sie darf nicht als Verbot der ausdrücklich vom Nutzer ausgelösten Freigabe nach REQ-050 gelesen werden. Beide Wege sind getrennt und einzeln einwilligungspflichtig. |
| 1.4 | 2026-06-19 | **REQ-034 Pflanzenfoto-Galerie (Security-Review SR-001/SR-003):** Neuer Consent-Purpose `reference_contribution` in `ConsentEngine.PURPOSES` (opt-in Foto-Beitrag zum DINOv2-Index, Art. 6(1)(a), global pro Nutzer). `user_diary_attachments`-Cleanup-Regel um `category 'plant'` erweitert. Neue Erasure-**Phase 0.5** `_reference_index_cleanup` (pgvector): entfernt vom Nutzer beigesteuerte `user_contributed`-Embeddings via Provenienz `contributed_by`/`tenant_key` VOR der ArangoDB-Löschung. Neues Abnahmekriterium AK-OS-05. |
| 1.3 | 2026-04-27 | **ADR-002 (W-006 Tenant-Species im Export):** `SpeciesReferenceResolver` + `species_ref`-Wrapper-Struktur ergänzt. Tenant-eigene Species werden inline als Snapshot exportiert (DSGVO Art. 20 Datenübertragbarkeit). Globale Species bleiben als Referenz mit `scope='global'`. Neue `DataSourceDefinition`s für `tenant_species_config` und `tenant_cultivar_config`. |
| 1.2 | 2026-04-27 | **W-007 Fix (Object-Storage-Cleanup Phase 0):** Erasure-Pipeline um Phase 0 erweitert, die VOR allen ArangoDB-Operationen den Object Storage bereinigt. Zwei Scopes: `user_personal` (Hard-Delete von Profilfoto/persönlichen Notiz-Fotos) und `user_diary_attachments` (Anonymisierung der `created_by`-Metadaten + EXIF-Strip-Pass für Tenant-Datensätze mit `STORAGE_KEEP_EXIF=true`). Erasure-Reihenfolge: Phase 0 → Phase 1 (Edges) → Phase 2 (Documents) → Phase 2.5 (Audit-Pseudonymisierung) → Phase 3 (User). Drei neue Abnahmekriterien (AK-OS-01 bis AK-OS-03). |
| 1.1 | 2026-04-27 | **W-002 Fix (Audit-Pseudonymisierung):** Phase 2.5 (Audit-Log-Pseudonymisierung) im `ErasureEngine` ergänzt. Generischer Mechanismus über `PSEUDONYMIZE_AUDIT_COLLECTIONS`-Liste — aktuell ein Eintrag (`erasure_requests.user_key`). Tombstone-Hash via SHA-256 + 64 Bit Truncation + Per-Instanz-Salt (`ERASURE_TOMBSTONE_SALT`, NFR-011 §4 Pflicht-Setting). Zwei neue Abnahmekriterien (AK-PD-01, AK-PD-02). |
| 1.0 | 2026-02-27 | Erstversion — DSGVO Art. 15–21 Betroffenenrechte, ErasureEngine, ConsentEngine, Celery-Tasks, Privacy-API. |

## 1. Business Case

**User Story (Auskunft — Art. 15):** "Als registrierter Nutzer möchte ich alle über mich gespeicherten personenbezogenen Daten in einem maschinenlesbaren Format herunterladen können — damit ich weiß, welche Informationen das System über mich hat, und mein Auskunftsrecht nach DSGVO Art. 15 wahrnehmen kann."

**User Story (Berichtigung — Art. 16):** "Als Nutzer möchte ich meine E-Mail-Adresse ändern können — damit meine Kontaktdaten aktuell sind und ich mein Recht auf Berichtigung nach DSGVO Art. 16 ausüben kann."

**User Story (Löschung — Art. 17):** "Als Nutzer, der das System nicht mehr nutzen möchte, möchte ich die Löschung meines Accounts und aller zugehörigen personenbezogenen Daten beantragen können — damit mein Recht auf Löschung nach DSGVO Art. 17 umgesetzt wird. Ich verstehe, dass gesetzlich geschützte Daten (Erntedokumentation, IPM-Behandlungsnachweise) anonymisiert statt gelöscht werden (Art. 17 Abs. 3 lit. b)."

**User Story (Einschränkung — Art. 18):** "Als Nutzer möchte ich die Verarbeitung meiner Daten für bestimmte Zwecke einschränken können — beispielsweise wenn ich die Richtigkeit meiner Daten bestreite oder die Verarbeitung für unrechtmäßig halte."

**User Story (Datenportabilität — Art. 20):** "Als Nutzer möchte ich meine Daten in einem strukturierten, maschinenlesbaren Format exportieren können — damit ich sie in ein anderes System übertragen kann."

**User Story (Widerspruch — Art. 21):** "Als Nutzer möchte ich der Verarbeitung meiner Daten zu bestimmten Zwecken widersprechen können — insbesondere wenn die Verarbeitung auf berechtigtem Interesse (Art. 6(1)(f)) basiert."

**User Story (Einwilligung):** "Als Nutzer möchte ich jederzeit nachvollziehen können, welche Einwilligungen ich erteilt habe, und diese einzeln widerrufen können — damit ich die Kontrolle über meine Daten behalte."

**Beschreibung:**
Kamerplanter verarbeitet personenbezogene Daten (E-Mail, Name, IP-Adressen, Nutzungsverhalten, indirekt Sensordaten). Die DSGVO verpflichtet den Verantwortlichen, Betroffenenrechte (Art. 15–21) technisch und organisatorisch umzusetzen. Diese REQ spezifiziert die vollständige technische Implementierung aller Betroffenenrechte als Self-Service-Funktionalität.

**Kernkonzepte:**

- **Datenexport (Art. 15/20):** Asynchrone Zusammenstellung aller User-Daten als JSON-Download
- **E-Mail-Änderung (Art. 16):** Zweistufig mit Token-Verifikation der neuen Adresse
- **Kontolöschung (Art. 17):** Soft-Delete → 90-Tage-Retention (NFR-011 R-01) → Hard-Delete. Gesetzlich geschützte Daten werden anonymisiert statt gelöscht (Art. 17 Abs. 3 lit. b)
- **Verarbeitungseinschränkung (Art. 18):** Zweckbezogene Sperren, die bei Datenverarbeitung geprüft werden
- **Widerspruch (Art. 21):** Zweckbezogener Opt-out, technisch identisch mit Einschränkung für Verarbeitungen auf Basis von Art. 6(1)(f)
- **Consent-Tracking:** Nachweisbare Einwilligungen pro Verarbeitungszweck mit Zeitstempel

### 1.1 Szenarien

**Szenario 1: Datenexport — Nutzer fordert Auskunft an**
```
1. Nutzer navigiert zu /settings/privacy
2. Klickt "Meine Daten exportieren"
3. System erstellt Export-Auftrag (status: pending)
4. Celery-Task sammelt alle Daten des Nutzers aus allen Collections
5. JSON-Datei wird erstellt und zum Download bereitgestellt
6. Nutzer erhält Benachrichtigung (E-Mail oder In-App)
7. Download-Link ist 72 Stunden gültig (NFR-011 R-05)
```

**Szenario 2: E-Mail-Änderung — Nutzer korrigiert Kontaktdaten**
```
1. Nutzer navigiert zu /settings/privacy
2. Gibt neue E-Mail-Adresse ein
3. System prüft: Adresse nicht bereits vergeben
4. Verifikations-E-Mail wird an die NEUE Adresse gesendet
5. Nutzer klickt Verifikations-Link
6. E-Mail wird aktualisiert, alte E-Mail erhält Info-Mail
7. Alle bestehenden Sessions werden invalidiert (Neuanmeldung erforderlich)
```

**Szenario 3: Account-Löschung — Nutzer verlässt das System**
```
1. Nutzer navigiert zu /settings/privacy → Tab "Account löschen"
2. Bestätigt mit Passwort (oder OAuth Re-Auth)
3. System erstellt Löschauftrag (status: scheduled)
4. Sofort: Soft-Delete (status: deleted), alle Sessions invalidiert,
   **Zugangsdaten entfernt** (siehe unten)
5. Erntedaten/Behandlungen: User-Referenz anonymisiert, Daten bleiben (CanG/PflSchG)
6. Nach 90 Tagen (NFR-011 R-01): Hard-Delete aller verbleibenden Daten
7. Erasure-Audit-Log wird für 3 Jahre aufbewahrt (NFR-011 R-06, Q-R12)
```

**Was der Soft-Delete sofort entfernt (verbindlich).** Der Soft-Delete ist kein
reines Statusfeld: `password_hash` und `avatar_url` werden mit demselben Schreibvorgang
aus dem gespeicherten Dokument **entfernt**, nicht nur im Modell auf `None` gesetzt.

Begründung: Zwischen Soft-Delete und Hard-Delete liegen 90 Tage (NFR-011 R-01). Ein
bcrypt-Hash, der in dieser Zeit stehen bleibt, ist ein weiterhin gespeichertes
Authentifizierungsgeheimnis eines Kontos, dem die Löschung zugesagt wurde — und der
lokale Login prüft `is_active` heute nicht, der Hash war also nutzbar. Gemessen am
2026-09-18 (#1525): das Repository lief im Merge-Modus, jedes `None` fiel aus der
Payload, und beide Felder überlebten den Löschvorgang. `ArangoUserRepository` schreibt
seitdem im Full-Replace-Modus; der Nachweis gegen eine echte ArangoDB liegt in
`src/backend/tests/integration/test_merge_mode_null_clearing.py`.

Die Tombstone-Adresse lautet `deleted_<user_key>@deleted.example.com`
(RFC 2606). Registrierung und E-Mail-Wechsel **weisen diese Domain zurück**:
`users.email` ist eindeutig indiziert, ein fremd registriertes
`deleted_<key>@deleted.example.com` würde die spätere Löschung genau des Kontos
blockieren, dessen Schlüssel es nennt.

**Bestandsdaten.** Von den beiden Soft-Delete-Pfaden kann nur der Löschauftrag
(`request_erasure`) Altbestand hinterlassen haben — die Kontolöschung
(`delete_account`) schrieb wegen der abgelehnten Adresse überhaupt nichts, also
auch keine Zeile. Gemessen am 2026-09-18 auf der kind-Installation: 0 inaktive
Konten, 0 überlebende Hashes, 0 Löschaufträge. Für Installationen, auf denen
Art. 17 ausgeübt wurde, entfernt die Migration **v0054** `password_hash` und
`avatar_url` auf genau dieser Menge — inaktiv **und** durch einen Löschauftrag
oder eine Tombstone-Adresse nachweislich gelöscht. Eine rein
`is_active == false`-Auswahl wäre falsch: eine administrative Deaktivierung ist
umkehrbar und darf ihr Passwort nicht verlieren.

**Szenario 4: Einwilligungsverwaltung**
```
1. Nutzer navigiert zu /settings/privacy → Tab "Einwilligungen"
2. Sieht Liste aller Verarbeitungszwecke:
   - "Grundfunktionen" (erforderlich, nicht widerrufbar)
   - "Fehler-Tracking (Sentry)" (optional)
   - "HaveIBeenPwned Passwort-Check" (optional)
   - "Externe Stammdatenanreicherung" (optional)
3. Kann optionale Einwilligungen einzeln widerrufen
4. System speichert Widerruf mit Zeitstempel
```

---

## 2. ArangoDB-Modellierung

### Nodes:

- **`:DataExportRequest`** — Export-Auftrag (Art. 15/20)
  - Collection: `data_export_requests`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `status: Literal['pending', 'processing', 'completed', 'expired', 'failed']`
    - `file_path: Optional[str]` (Pfad zur generierten JSON-Datei)
    - `file_size_bytes: Optional[int]`
    - `requested_at: datetime`
    - `processing_started_at: Optional[datetime]`
    - `completed_at: Optional[datetime]`
    - `expires_at: Optional[datetime]` (72h nach Fertigstellung, NFR-011 R-05)
    - `error_message: Optional[str]` (bei Status `failed`)
    - `download_count: int` (Default: 0)

- **`:ConsentRecord`** — Einwilligung pro Verarbeitungszweck
  - Collection: `consent_records`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `purpose: str` (Schlüssel aus `ConsentEngine.PURPOSES`, z.B. `error_tracking`, `plant_identification`; Datensätze zu seit #2136 entfernten Zwecken bleiben erhalten)
    - `granted: bool` (true = erteilt, false = widerrufen)
    - `granted_at: Optional[datetime]`
    - `revoked_at: Optional[datetime]`
    - `ip_address: Optional[str]` (IP bei Einwilligungserteilung, anonymisiert nach 7d)
    - `user_agent: Optional[str]` (Browser bei Einwilligung)
    - `consent_version: str` (Version der Datenschutzerklärung, z.B. "1.0")

- **`:ProcessingRestriction`** — Verarbeitungseinschränkung (Art. 18)
  - Collection: `processing_restrictions`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `scope: str` (z.B. `all`, `sensor_data`, `analytics`, `enrichment`)
    - `reason: Literal['accuracy_contested', 'unlawful_processing', 'purpose_expired', 'objection_pending']`
    - `created_at: datetime`
    - `lifted_at: Optional[datetime]`
    - `notes: Optional[str]`

- **`:ErasureRequest`** — Löschauftrag (Art. 17)
  - Collection: `erasure_requests`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `status: Literal['scheduled', 'in_progress', 'completed', 'partially_completed']`
    - `requested_at: datetime`
    - `soft_deleted_at: Optional[datetime]`
    - `hard_delete_scheduled_at: Optional[datetime]` (90 Tage nach Soft-Delete)
    - `completed_at: Optional[datetime]`
    - `anonymized_collections: list[str]` (Collections in denen User-Referenz anonymisiert wurde)
    - `deleted_collections: list[str]` (Collections die vollständig gelöscht wurden)
    - `retained_reason: Optional[str]` (z.B. "CanG §X: Erntedaten 5 Jahre")

- **`:EmailChangeRequest`** — E-Mail-Änderungsauftrag (Art. 16)
  - Collection: `email_change_requests`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `new_email: str` (gewünschte neue E-Mail)
    - `verification_token_hash: str` (SHA-256 Hash des Tokens)
    - `status: Literal['pending', 'confirmed', 'expired', 'cancelled', 'reverted']`
    - `requested_at: datetime`
    - `expires_at: datetime` (24h nach Erstellung)
    - `previous_email: Optional[str]` (die bei der Bestätigung verlassene Adresse; nur bis `revert_expires_at`, #1848)
    - `revert_token_hash: Optional[str]` (Hash des Rückgängig-Tokens; nur bis `revert_expires_at`, #1848)
    - `revert_expires_at: Optional[datetime]` (Bestätigung + `RETENTION_EMAIL_CHANGE_REVERT_DAYS`)
    - `reverted_at: Optional[datetime]`
    - `confirmed_at: Optional[datetime]`

### Edges:

```
requested_export:      users → data_export_requests    (1:N, User hat Export-Aufträge)
has_consent:           users → consent_records          (1:N, User hat Einwilligungen)
has_restriction:       users → processing_restrictions  (1:N, User hat Verarbeitungssperren)
requested_erasure:     users → erasure_requests         (1:N, User hat Löschaufträge)
requested_email_change: users → email_change_requests   (1:N, User hat E-Mail-Änderungen)
```

### Indizes:

```
data_export_requests:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [status]
  - PERSISTENT INDEX on [expires_at]

consent_records:
  - PERSISTENT INDEX on [user_key, purpose] UNIQUE  (eine Einwilligung pro Zweck)
  - PERSISTENT INDEX on [user_key]

processing_restrictions:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [user_key, scope] UNIQUE  (eine Sperre pro Scope)

erasure_requests:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [status]
  - PERSISTENT INDEX on [hard_delete_scheduled_at]

email_change_requests:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [verification_token_hash] UNIQUE
  - TTL INDEX on [expires_at] expireAfter: 0  (automatische Bereinigung)
```

---

## 3. Backend-Architektur

### 3.1 Engine-Schicht

Die beiden Inventare personenbezogener Daten — **was nach Art. 15/20 offengelegt** und
**was nach Art. 17 gelöscht, anonymisiert oder pseudonymisiert** wird — stehen **nur im
Code**. Dieser Abschnitt legt die Regeln fest, denen beide folgen müssen, und sagt, wo sie
stehen. Er führt bewusst **keine Abschrift** der Listen (#1719): Bis v1.8 stand hier eine
handgepflegte Kopie beider Inventare. Sie wich zuletzt in rund 30 Quellen und in
Feldnamen (`harvester`, `assigned_to`, …) vom Code ab und musste in #1663, #1700 und #1716
jeweils von Hand nachgezogen werden — dieselbe Form (zwei Listen, die übereinstimmen
müssen und nie verglichen werden), die vor #1622 die beiden Code-Inventare
auseinanderlaufen ließ.

#### 3.1.1 Wo die Inventare stehen

| Inventar | Ort (maßgeblich) |
|----------|------------------|
| Art.-15/20-Manifest | `DataExportEngine.USER_DATA_MANIFEST` in `src/backend/app/domain/engines/data_export_engine.py` |
| Löschziele, die bewusst nicht offengelegt werden | `DataExportEngine.EXCLUDED_FROM_DISCLOSURE` (dieselbe Datei) |
| Löschschritte in Ausführungsreihenfolge | `ErasureEngine.DELETE_STEPS` in `src/backend/app/domain/engines/erasure_engine.py` |
| Anonymisierungsregeln | `ErasureEngine.ANONYMIZE_COLLECTIONS` (dieselbe Datei) |
| Audit-Pseudonymisierung | `ErasureEngine.PSEUDONYMIZE_AUDIT_COLLECTIONS` (dieselbe Datei) |
| Object-Storage- und pgvector-Bereinigung | `ErasureEngine.STORAGE_CLEANUP_RULES`, `ErasureEngine.REFERENCE_INDEX_CLEANUP_RULES` (dieselbe Datei) |
| Kontofelder, die die Löschung bewusst nicht anfasst | `ErasureEngine.EXCLUDED_USER_REFERENCES` (dieselbe Datei) |
| Datenmodell der Einträge | `DataSourceDefinition`, `DisclosureExclusion`, `ErasureStep`, `AnonymizationRule`, `PseudonymizationRule`, `ErasureExclusion` in `src/backend/app/domain/models/privacy.py` |
| Durchsetzung der Regeln unten | `scripts/check_privacy_inventory.py` (R1–R6, pre-commit und CI) sowie `src/backend/tests/unit/domain/engines/test_privacy_engines.py` und `src/backend/tests/integration/test_privacy_export_walk.py` |

Die Engines sind reine Logik ohne I/O. Das Manifest liest
`PrivacyService.process_data_export` über `build_export_manifest`, das Löschinventar
`PrivacyService.erase_account` über `build_erasure_plan` (#1622, #1645, #1664).

#### 3.1.2 Regeln für die Offenlegung (Art. 15/20)

1. **Jede Kategorie, die das System einer Person über ein Kontofeld zurechnet, ist eine
   Manifest-Quelle** (`DataSourceDefinition`). Die Zuordnung hat eine von vier Formen:
   das Profil selbst (`filter_field="_key"`), ein Kontofeld am Dokument
   (`filter_field="<feld>"`), eine Kante von `users` zum Dokument (`edge_collection`),
   oder der Endpunkt `_from`/`_to` einer Kante, deren Zeile selbst die Daten ist
   (`user_favorites`, #1719). **Fünfte Form (#2135, Betreiberentscheidung 2026-10-04):**
   der **eigene persönliche Mandant** der Person (`tenant_type: personal`, Eigentümerin ist
   sie) wird offengelegt (`personal_tenant_scope`) — Standorte einschließlich
   `gps_coordinates` (für einen persönlichen Garten meist die Wohnadresse), Beete,
   Stellplätze, Pflanzen, Pflanzdurchläufe, Aufgaben, Tagebuch und Anhang-Metadaten. Die
   Quellen sind auf `personal_tenant_keys_of(user)` begrenzt, nie auf Mitgliedschaften:
   Aus einem Organisationsmandanten erscheinen nur die Mitgliedschaft und die über ein
   Kontofeld zugeordneten eigenen Beiträge, aus dem persönlichen Garten einer anderen
   Person nichts. Was die Auskunft so offenlegt, löscht die Kontolöschung über das
   Mandanten-Löschinventar (#1788); der Prüfer R2 gleicht genau das ab. **Noch nicht
   offengelegt** (bekannte Lücke, Folge-Issue): die Sensor-Messwerte des Gartens
   (TimescaleDB, außerhalb des Manifest-Walks) sowie Tank-, Gieß- und Düngeprotokolle.
2. **Nur Felder, die das Modell trägt.** Ein falscher Feldname liefert eine leere Spalte,
   die sich wie „keine Daten" liest.
3. **Keine Zugangsdaten, keine internen Prüfwerte.** Gespeicherte Geheimnisse und ihre
   Hashes (API-Schlüssel-Hash, Kalender-Feed-Token) sowie interne Dedup-Hashes von
   Bildern werden nicht exportiert.
4. **Mandantenbindung, wo Fremde das Kontofeld schreiben können.** Ein Kontofeld, das
   jeder Bearbeiter setzt, wird nur in den Mandanten der Person gelesen
   (`tenant_scoped`, #1662 SCR-001). Ein serverseitig aus dem Aufrufer gestempeltes Feld
   braucht das nicht, und Daten aus einem verlassenen Mandanten bleiben dann Teil der
   Auskunft.
5. **Ehrliche Lücken statt leerer Listen.** Eine Kategorie, die sich nicht pro Person
   zuordnen lässt, steht mit Begründung im Bundle (`disclosure_gap`); Altdatensätze ohne
   Kontoschlüssel werden neben den gelieferten Zeilen benannt (`attribution_gap`). Leere
   Sektionen bleiben im Bundle (`record_count`).
6. **Pseudonymisierte Aufbewahrungszeilen bleiben für ein noch aktives Mitglied
   auskunftspflichtig (Betreiberentscheidung Q-T1, #1793).** Nach einer Mandantenlöschung
   tragen R-16/R-17/R-18-Zeilen (NFR-011 §2.3) den Tombstone-Hash der Person statt ihres
   Kontoschlüssels. Ist die Person weiterhin ein aktives Konto, deckt Art. 15 diese Zeilen
   weiterhin ab: Das Manifest muss sie zusätzlich über den Tombstone-Hash finden, nicht nur
   über `*_by_key`, sonst verschwinden sie unbemerkt aus der Auskunft, sobald ihr Mandant
   gelöscht wird. **Umgesetzt** (#1793, v1.21): Für jedes Kontofeld, das die
   Mandantenlöschung pseudonymisiert (`TenantErasureEngine.pseudonymized_account_fields()`,
   abgeleitet aus dem Inventar, keine zweite Liste), sucht der Export zusätzlich nach dem
   Tombstone-Hash der Person — bei einer `tenant_scoped`-Quelle nur in Zeilen, deren
   Mandant nicht mehr existiert, unabhängig von den aktuellen Mitgliedschaften der Person
   (sie ist Mitglied keines gelöschten Mandanten). Ein Tombstone-Hash in einer Zeile eines
   bestehenden Mandanten wird nicht zugeordnet (Regel 4 gilt dort unverändert).
7. **Pseudonymisierte Duplikate ohne rekonstruierbaren zweiten Hochlader
   (Betreiberentscheidung Q-T2, #1806/#1839).** Der Anhänge-Abschnitt wendet Regel 5
   ausdrücklich auf die vor #1770 zusammengeführten Duplikate an: Zwei identische Uploads
   vor der Trennung nach Hochlader (#1770, AK-OS-08) hinterließen keine Spur des zweiten
   Hochladers — dessen Bytes sind nie hart löschbar zugeordnet. Der Anhänge-Abschnitt des
   Bundles nennt diese Zeilen deshalb mit `attribution_gap` statt sie stillschweigend so
   darzustellen, als gäbe es nur einen Beitragenden (#1839 GDPR-007).
8. **Daten Dritter (Art. 15(4), Betreiberentscheidung 2026-10-04, #2135).** Ein geteilter
   persönlicher Garten enthält Zeilen, die andere Mitglieder geschrieben haben; sie gehören
   zum Garten der Person und werden mit ihm offengelegt. **Kontoschlüssel anderer Personen
   werden nicht ausgeliefert** — die Garten-Quellen enthalten weder `created_by` noch
   `assigned_to_user_key` noch ein anderes Kontofeld. Freitext (Aufgabennamen, Notizen,
   Tagebuchtexte, Benachrichtigungen) wird **nicht maskiert**: Die vom System erzeugten
   Benachrichtigungstexte nennen keine Anzeigenamen anderer Mitglieder (gemessen in
   `notification_service` / `notification_propagation_service`: Aufgaben- und Pflanzennamen,
   Termine), und was Mitglieder selbst in den Garten der Person geschrieben haben, war ihr
   ohnehin sichtbar — eine erneute Herausgabe an sie beeinträchtigt die Rechte der
   Schreibenden nicht. Ein Bundle enthält deshalb keine Daten, die der Person nicht schon
   in der App angezeigt wurden.

#### 3.1.3 Regeln für Löschung, Anonymisierung und Pseudonymisierung (Art. 17)

1. **Löschen ist der Normalfall** für Daten der Person ohne Aufbewahrungsgrund. Jeder
   Schritt nennt, wer ihn ausführt (`executor`), und wie die Zeilen der Person gefunden
   werden (`user_field`, bei Kanten `_from`/`_to`, ggf. `via` auf das Elterndokument,
   ggf. `where`). Reihenfolge: Object Storage (Phase 0) → pgvector-Referenz-Index
   (Phase 0.5) → Kanten → Dokumente → Anonymisierung → Audit-Pseudonymisierung
   (Phase 2.5) → `users`.
2. **Anonymisieren statt löschen**, wenn das Dokument bleiben muss:
   - **gesetzliche Aufbewahrungspflicht** — Ernten und Qualitätsbewertungen (CanG,
     5 Jahre, NFR-011 R-16), Behandlungen und Inspektionen (PflSchG §11, 3 Jahre,
     NFR-011 R-17/R-18). Der Kontoschlüssel wird zum Tombstone-Hash, damit die
     aufbewahrten Datensätze desselben Kontos für eine Prüfung verknüpfbar bleiben;
     Freitextnamen werden geleert (Art. 17 Abs. 3). Diese Frist läuft unverändert bis zu
     ihrem ursprünglichen Ende weiter, auch wenn der Mandant oder das Konto in der
     Zwischenzeit gelöscht wird (NFR-011 §2.3, Q-R1/Q-R2, #1789).
   - **Datensatz eines möglicherweise geteilten (organisatorischen) Mandanten** — Aufgaben
     und Aufgabenkommentare, Tagebucheinträge (REQ-050 §7.4), Anhänge (AK-OS-02),
     Importaufträge, Wetterquellen-Einstellungen, manuelle Übersteuerungen, verworfene
     KI-Tipps, versandte Einladungen, freigegebene Referenzbilder und der Mandant selbst
     (Eigentümerverweis). Der Kontobezug wird durch den Marker `_anonymized` ersetzt.
     **Der persönliche Mandant der Person fällt seit #1824 nicht mehr unter diese Regel**
     (siehe der eigene Absatz unten) — er wird nie mit anonymisiertem Eigentümer erhalten,
     unabhängig davon, ob er weitere aktive Mitglieder hat.
3. **Pseudonymisieren** für Datensätze mit eigener, vom Konto unabhängiger Aufbewahrung:
   Löschaudit (NFR-011 R-06, 3 Jahre nach Abschluss — Betreiberentscheidung Q-R12, #1793/#1806;
   eigenständiger Wert, **nicht** an die tenant-gebundene R-06a-Formel gekoppelt),
   MCP-Aufrufprotokoll (REQ-033) und Consent Records
   (NFR-011 R-04, 3 Jahre nach Widerruf — Betreiberentscheidung Q-R5, #1800: ersetzt die
   bis v1.17 hier fehlende, in NFR-011 §5 widersprüchlich als „sofort löschbar"
   beschriebene Behandlung). Tombstone-Hash siehe unten.
4. **Keine Organisation bleibt ohne Verwaltung zurück (INV-1, Betreiberentscheidung
   2026-10-04, #2134).** Die Kontolöschung entfernt die Mitgliedschaften der Person ohne die
   INV-1-Prüfung — wer Art. 17 ausübt, muss nichts vorher übergeben. Deshalb entscheidet sie
   **vor** ihrem ArangoDB-Plan für jede Organisation (`tenant_type: organization`, nicht der
   Plattform-Mandant, nur Organisationen im Zustand `active`/`suspended`), in der die Person
   aktives Mitglied ist (`TenantService.settle_organisations_of_erased_account`): **(a)** Ist
   sie die letzte aktive Mitgliedschaft mit `management`, erhält die dienstälteste
   verbleibende **Leitung** (frühestes `joined_at`; ein fehlender Beginn zählt zuletzt) den
   Scope `management` — protokolliert im Sicherheits-Audit (`via: account_erasure`),
   alle verbleibenden Mitglieder werden per E-Mail benachrichtigt (ohne Namen der Person).
   **(b)** Bleibt keine Leitung oder überhaupt kein anderes aktives Mitglied (ein Konto,
   dessen eigene Löschung beantragt ist, zählt nicht), wird die Organisation **`orphaned`**
   (REQ-024 AK-65): Sie ist für alle gesperrt und wird nach der Gnadenfrist der
   Mandantenlöschung (REQ-024 AK-52, NFR-011 R-01b) über das Mandanten-Löschinventar
   gelöscht; die verbleibenden Mitglieder (Exportfenster, Art. 20) und die Plattform-Admins
   werden benachrichtigt. Eine verwaiste Organisation lässt sich nicht zurückholen — die
   Notfall-Verwaltung aus REQ-023 §5a.5 ist gestrichen. **(c)** Sonst ändert sich nichts.
   Die Vorschau vor der Bestätigung nennt (a) und (b) je Organisation (AK-FK-08). Die
   Entscheidung ist idempotent: Ein Wiederholungslauf findet die Verwaltung bereits
   übergeben bzw. die Organisation bereits `orphaned`.

> **Persönlicher Mandant: Erasure statt Retention, auch mit weiteren Mitgliedern
> (Betreiberentscheidung Q-E1/Q-E5, #1824).** Bis v1.17 blieb ein persönlicher Mandant mit
> mindestens einem weiteren aktiven Mitglied erhalten (nur Eigentümer, Name und Kurzname
> wurden anonymisiert, `personal_tenants[].outcome = retained_other_members`). Diese
> Entscheidung ist **ersetzt**: Ein persönlicher Mandant (`tenant_type: personal`) der
> löschenden Person wird jetzt in jedem Fall über das Mandanten-Löschinventar (#1769)
> vollständig gelöscht — auch mit weiteren aktiven Mitgliedern; deren Sites, Pflanzen,
> Tagebuch und Aufgaben gehen mit, sofern sie keinen eigenen Aufbewahrungsgrund haben. Die
> verbleibenden Mitglieder werden **vor** der Löschung benachrichtigt. Die Regel ist
> ausdrücklich an `tenant_type: personal` geknüpft, nicht an „ist zufällig das einzige
> verbleibende aktive Mitglied" (Q-E5). **Seit v1.32 (#2134) gilt für organisatorische
> Mandanten Regel 4 unten:** Eine Organisation, deren einziges Mitglied die Person war, bleibt
> **nicht** mehr mit anonymisiertem Eigentümerverweis erhalten, sondern wird `orphaned` und
> nach der Gnadenfrist gelöscht; war die Person die letzte Verwaltung, übernimmt die
> dienstälteste Leitung. Die in #1824 gestellten Fragen nach Nachfolge oder Übertragung
> (Q-E2/Q-E3/Q-E4) sind damit für organisatorische Mandanten entschieden; für den
> persönlichen Mandanten bleiben sie gegenstandslos. Siehe NFR-011 AK-PT-03 (Retention-seitig) und AK-IE-06/AK-IE-07 unten
> (Race-Window-Absicherung, #1825; seit v1.20 umgesetzt). **Nicht implementiert:** Der Code
> **Implementiert (v1.24, #1824):** Der Code setzt die neue Regel um. Die Entscheidung
> liegt an einer Stelle, `TenantService._personal_tenant_retention`: Sie erhält einen
> persönlichen Mandanten nur noch für ein Mitglied, das **nach dem Löschantrag oder nach
> dem Einfrieren** des Mandanten (AK-IE-07) beigetreten ist — also keine Benachrichtigung
> erhalten haben kann; wer zum Antrag schon Mitglied war, geht mit dem Mandanten. Die Benachrichtigung der verbleibenden Mitglieder läuft **beim
> Löschantrag** (`PrivacyService.request_erasure`, bei `erase_account_now` unmittelbar
> vor dem Lauf), nicht erst bei der endgültigen Löschung — so bleibt ihnen die ganze
> Karenzzeit, um ihre Daten zu sichern oder den Mandanten zu verlassen. Die E-Mail nennt
> das Datum der endgültigen Löschung — bei der Sofortlöschung durch einen Administrator
> stattdessen den Hinweis, dass es keine Karenzzeit gibt — und nichts über die löschende
> Person (kein Name, keine Adresse, kein Gartenname). Die E-Mail empfiehlt nicht den
> persönlichen Datenexport als Sicherung: Gartendaten sind nicht Teil davon. Die Bereinigung unverifizierter Konten benachrichtigt
> niemanden; zwei gleichzeitige Anträge benachrichtigen einmal (nur der Aufruf, der den
> Löschauftrag anlegt, versendet). Ein Versandfehler blockiert den Löschantrag nicht
> (Art. 17 geht vor), geht aber nicht verloren: **Dauerhaft (v1.26, #1960)** — der Versand wird
> am Löschauftrag vermerkt (`members_notified_at`, Empfängerzahl, Fehlerzähler
> `members_notice_failures`; ohne Adressen), der tägliche Lauf wiederholt eine nicht versandte
> Benachrichtigung **vor** der endgültigen Löschung und protokolliert den Fehler ohne Adresse.
> Ein Löschauftrag ohne Vermerk (aus der Zeit vor #1824) wird beim ersten Sehen benachrichtigt;
> die endgültige Löschung wartet dann `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` Tage (Standard 7)
> nach dieser Benachrichtigung. Ist sie die ganze Wartezeit nicht zustellbar (kein Mailversand
> eingerichtet), geht die Löschung weiter — zugesichert ist der Versuch und die Wartezeit nach
> einer gelungenen Zustellung, nicht die Zustellung selbst. Die Löschung durch einen
> Plattform-Administrator ist eine **Sofortlöschung** ohne Karenzzeit; die E-Mail sagt „findet jetzt
> statt", und die Administrator-Oberfläche zeigt vor der Bestätigung dieselbe Vorschau wie die
> Selbstbedienung (AK-FK-07). Der Ergebniswert im Löschauftrag ist `erased` oder — nur bei einem
> Spätbeitritt — `retained_late_joiner`; `retained_other_members` wird nicht mehr
> geschrieben (alte Löschaufträge behalten ihn).
4. **Nie auf Freitext schlüsseln.** Eine Regel trifft nur ein serverseitig gesetztes
   Kontofeld; ein eingetippter Name ist kein Schlüssel (#1662, #1663).
5. **Jedes gespeicherte Feld in Form eines Kontoschlüssels** (`user_key`, `*_user_key`,
   `*_by_key`, `*_account_key`, `*_by`) wird vom Löschinventar erreicht oder steht mit
   Begründung in `EXCLUDED_USER_REFERENCES` (Freitext, Enum-Wert, nur Default
   geschrieben; #1700).
6. **Geteilte Bytes bleiben — mit Mitteilungspflicht (Art. 19, Q-E8, Betreiberentscheidung
   2026-09-26, #1839 GDPR-006).** Hält nach einer Löschung noch ein fremder
   `attachments`-Datensatz dasselbe gespeicherte Objekt (AK-OS-08), werden die Bytes
   **nicht** zusätzlich hart gelöscht — sie gehören inzwischen (auch) dem verbleibenden
   Halter. Betrifft der Inhalt erkennbar die gelöschte Person (z. B. ein Foto, das sie
   zeigt oder das sie ursprünglich beigetragen hat), MUSS der verbleibende Halter über
   den Fortbestand der Bytes benachrichtigt werden — Art. 19 DSGVO verlangt die
   Mitteilung von Berichtigung/Löschung an jeden Empfänger, dem die Daten offengelegt
   wurden. Die Benachrichtigung nennt keinen Kontoschlüssel der gelöschten Person.

#### 3.1.4 Gegenseitigkeit und Ausschlussprinzip

- **Was offengelegt wird, muss löschbar sein** (Guard-Regel R2, vorwärts).
- **Was die Löschung als Daten der Person entfernt oder anonymisiert, wird offengelegt**
  — oder steht mit Begründung in `EXCLUDED_FROM_DISCLOSURE` (R2, rückwärts, #1719). Dass
  die Löschung eine Collection anfasst, belegt, dass sie Daten der Person hält.
- **Ausgeschlossen werden darf nur, was keine Information über die Person trägt, die
  nicht schon eine offengelegte Quelle liefert:** die Kante zwischen Konto und einem
  offengelegten Dokument, eine Kante, deren Attribute Kopien offengelegter Felder sind,
  oder reiner technischer Zustand ohne eigenen Inhalt. Eine Kante mit eigenem Inhalt ist
  eine Manifest-Quelle (Favoriten: welcher Katalogeintrag, wann, manuell oder per
  Kaskade). Jede ausgeschlossene Kante gehört zu einem offengelegten Dokument; das prüft
  `test_every_excluded_edge_belongs_to_a_disclosed_document`.
- Ein Ausschluss für eine Collection, die die Löschung nicht anfasst oder die zugleich
  offengelegt wird, ist veraltet und wird abgewiesen.

> **Nicht implementiert (Stand #1663):** Die Collection `plant_diary_analyses` aus
> REQ-051 §5 existiert im Code nicht. Sobald sie angelegt wird, braucht sie zwei
> Anonymisierungsregeln für `requested_by` und `claimed_by` (Marker `_anonymized`,
> AK-DA-04) und eine Manifest-Quelle (AK-DA-05). Der Code führt bewusst keine
> Platzhalterregel.

> **Tenant-Overlay-Quellen: nicht implementiert (Stand #1716).** Bis v1.8 nannte die
> frühere Manifest-Kopie dieser Spec zwei weitere Quellen, `tenant_species_config` und
> `tenant_cultivar_config` (ADR-002 / W-006, Schicht 2 aus REQ-001 v4.0). Keine der beiden
> Collections existiert im Code: keine Konstante in `collections.py`, kein Modell, kein
> Repository, kein Eintrag in `DataExportEngine.USER_DATA_MANIFEST`. Der Export kann sie
> also nicht offenlegen. Was es heute an mandantenbezogenen Stammdaten gibt, ist keine
> Art.-15-Quelle zur betroffenen Person: mandanteneigene `species`/`cultivars` tragen nur
> `tenant_key` (#1090), die Freigabekanten `tenant_has_access` verbinden `tenants` mit
> `species`/`cultivars` (#1092) — beide ohne Nutzerschlüssel. Sobald REQ-001 das Overlay
> anlegt und es einen Nutzer zurechnet, gehört es mit diesem Schlüsselfeld in beide
> Inventare (Guard-Regeln R2 und R6 in `scripts/check_privacy_inventory.py`).

> **Zurechnung der aufbewahrungspflichtigen Datensätze (#1669, seit Migration v0056).**
> Die Freitextfelder `harvest_batches.harvester`, `inspections.inspector` und
> `treatment_applications.applied_by` sind Anzeigenamen (`"Maren"`, `"mcp:<account>"`)
> und **keine** Benutzerschlüssel — ein Manifest oder eine Anonymisierungsregel, die
> darauf schlüsselt, trifft nie das betroffene Konto (gemessen in #1662, #1663).
> Deshalb tragen die drei Modelle zusätzlich ein serverseitig gesetztes Schlüsselfeld
> `harvested_by_key` / `inspected_by_key` / `applied_by_key` (`str | None`): jeder
> Schreibpfad (REST, MCP, die Inspektions-Brücken aus Schädlingserkennung und
> CV-Diagnose) füllt es aus dem aufgelösten Aufrufer; ein Request-Body kann es nicht
> setzen (Feld nicht im Schema, `extra="ignore"`). Art. 15 filtert und Art. 17
> pseudonymisiert auf diesem Feld und leert dabei den Freitext. Vor #1669 geschriebene
> Zeilen tragen `null` — ohne Rückschluss aus dem Freitext, weil ein Name kein Schlüssel
> ist — und werden im Export als nicht zuordenbar benannt, nicht verschwiegen.
> Seit #1663 (Migration v0057) gilt dasselbe für `quality_assessments.assessed_by_key`
> neben dem Freitext `assessed_by` — Qualitätsbewertungen gehören nach NFR-011 R-16 zur
> Erntedokumentation. `yield_metrics` (ebenfalls R-16) trägt kein Nutzerfeld und braucht
> deshalb keine Regel.


Die Mechanik der Einträge, die die Listen im Code verwenden, ist unten beschrieben
(Tombstone-Hash, `StorageCleanupRule`, `ReferenceIndexCleanupRule`).

```python
# <!-- Quelle: Widerspruchsanalyse W-007 -->
@dataclass
class StorageCleanupRule:
    """Regel für die Object-Storage-Bereinigung in Phase 0 des Erasure-Tasks."""
    scope: Literal["user_personal", "user_diary_attachments", "user_pest_reference_images"]
    description: str
    action: Literal["hard_delete", "anonymize_metadata_and_strip_exif"]
    ref: str  # Referenz auf NFR-013-Sektion
# <!-- /Quelle: Widerspruchsanalyse W-007 -->


# <!-- Quelle: REQ-034 Security-Review SR-003 -->
# Referenz-Index-Cleanup (Phase 0.5): Der DINOv2-Referenz-Index
# (REQ-029-A species_embeddings) liegt physisch in pgvector, NICHT in
# ArangoDB. Vom Nutzer beigesteuerte Embeddings (source='user_contributed')
# tragen die Provenienz-Felder contributed_by / tenant_key / contributed_at und
# werden über eine ReferenceIndexCleanupRule entfernt. Kuratiert übernommene
# Referenzen bleiben unberührt — sie sind nicht personenbezogen. Bei
# Tenant-Löschung (REQ-024) greift dieselbe Regel mit Filter
# `source == 'user_contributed' AND tenant_key == X`.
@dataclass
class ReferenceIndexCleanupRule:
    """Regel für die pgvector-Referenz-Index-Bereinigung (Phase 0.5)."""
    store: Literal["pgvector"]
    collection: str
    filter: str
    action: Literal["hard_delete"]
    ref: str
# <!-- /Quelle: REQ-034 Security-Review SR-003 -->
```

<!-- Quelle: Widerspruchsanalyse W-002 -->
**Audit-Log-Pseudonymisierung (W-002):**

Die `PSEUDONYMIZE_AUDIT_COLLECTIONS`-Liste ist bewusst generisch ausgelegt: jede Collection, die einen User-Verweis länger als den User selbst aufbewahren muss (Compliance-Ausnahme), wird hier eingetragen. Die Pseudonymisierung läuft als **Phase 2.5** zwischen den Document-Löschungen (Phase 2) und der User-Löschung (Phase 3) — siehe Celery-Task in §3.5.

```python
from dataclasses import dataclass
from typing import Literal
import hashlib

@dataclass
class PseudonymizationRule:
    """Regel zur Pseudonymisierung eines User-Verweises in einer Audit-Collection."""
    collection: str                                    # z.B. "erasure_requests"
    user_field: str                                    # z.B. "user_key"
    replacement_strategy: Literal["tombstone_hash"]    # erweiterbar für andere Strategien
    reason: str                                         # Compliance-Begründung


def compute_tombstone_hash(user_key: str, salt: str) -> str:
    """Erzeugt einen nicht umkehrbaren Tombstone-Hash für gelöschte User.

    Format:    'anon_' + hex(sha256(user_key + salt))[:16]
    Länge:     21 Zeichen (5 Präfix + 16 Hex = 64 Bit Identitätsraum)
    Properties:
      - Deterministisch: gleicher (user_key, salt) → gleicher Hash
      - Einweg: aus dem Hash ist user_key nicht rekonstruierbar (SHA-256)
      - Salt-isoliert: ohne Kenntnis des per-Instanz-Salts ist keine
        Brute-Force-Reidentifikation gegen den User-Key-Raum möglich

    64 Bit reichen für Kamerplanter-Skalen (max. ~100k User über 10 Jahre,
    Geburtstagsparadox-Kollision ~2^32 Tombstones nicht erreichbar). Salt
    MUSS pro Instanz einzigartig in einem Secret abgelegt sein
    (NFR-011 §4 ERASURE_TOMBSTONE_SALT, Pflicht-Setting).

    Raises:
        ValueError: Wenn salt leer ist oder kürzer als 32 Zeichen
            (Mindestentropie für sichere Pseudonymisierung).
    """
    if not salt or len(salt) < 32:
        raise ValueError(
            "ERASURE_TOMBSTONE_SALT muss mindestens 32 Zeichen lang sein "
            "(siehe NFR-011 §4)."
        )
    h = hashlib.sha256((user_key + salt).encode("utf-8")).hexdigest()
    return f"anon_{h[:16]}"
```
<!-- /Quelle: Widerspruchsanalyse W-002 -->

**`ConsentEngine`** — Einwilligungsmanagement (pure Logik):

```python
class ConsentEngine:
    """Verwaltet Einwilligungen pro Verarbeitungszweck."""

    # Definierte Verarbeitungszwecke
    PURPOSES: list[ConsentPurpose] = [
        ConsentPurpose(
            key="core_functionality",
            label_de="Grundfunktionen",
            label_en="Core Functionality",
            description_de="Verarbeitung für den Betrieb des Systems (Pflanzenverwaltung, Phasensteuerung, etc.)",
            legal_basis="Art. 6(1)(b) Vertragserfüllung",
            required=True,  # Nicht widerrufbar
        ),
        ConsentPurpose(
            key="error_tracking",  # #2136: gelesen von app/observability/event_user.py
            label_de="Fehlerberichte meinem Konto zuordnen (Sentry)",
            label_en="Attribute error reports to my account (Sentry)",
            description_de="Ein Fehlerbericht zu einer deiner Anfragen trägt ein Pseudonym deines Kontos und Gartens; ohne Einwilligung wird er ohne diese Zuordnung übermittelt",
            legal_basis="Art. 6(1)(a) Einwilligung",
            required=False,
        ),
        # #2136: `hibp_check` und `external_enrichment` entfernt — kein Code las sie (§3.6).
        # REQ-034 §4.4 — opt-in Foto-Beitrag zum DINOv2-Referenz-Index (REQ-029-A).
        # Granularität: global pro Nutzer (die UNIQUE(user_key, purpose)-Constraint
        # auf consent_records erlaubt genau einen Datensatz pro Zweck → O-04 in
        # REQ-034 ist damit auf "global pro Nutzer" entschieden).
        ConsentPurpose(
            key="reference_contribution",
            label_de="Beitrag eigener Fotos zur Pflanzenerkennung",
            label_en="Contribution of own photos to plant recognition",
            description_de=(
                "Aus deinen Galerie-Fotos einer korrekt bestimmten Pflanze wird "
                "ein Embedding-Vektor berechnet und — nach Admin-Prüfung — als "
                "zusätzliche Referenz für die self-hosted Bilderkennung genutzt. "
                "Es wird ausschließlich der Vektor gespeichert, das Originalbild "
                "verlässt die Instanz nicht und geht an keinen Dritten. Jederzeit "
                "widerrufbar; bei Widerruf/Kontolöschung werden beigesteuerte "
                "Vektoren entfernt."
            ),
            legal_basis="Art. 6(1)(a) Einwilligung",
            required=False,
        ),
    ]

    def get_all_purposes(self) -> list[ConsentPurpose]:
        """Gibt alle definierten Verarbeitungszwecke zurück."""
        return self.PURPOSES

    def is_processing_allowed(self, purpose_key: str, consent: Optional[ConsentRecord]) -> bool:
        """Prüft ob Verarbeitung für den gegebenen Zweck erlaubt ist."""
        purpose = self._find_purpose(purpose_key)
        if purpose.required:
            return True  # Erforderliche Zwecke immer erlaubt
        if consent is None:
            return False  # Kein Consent-Record → nicht erlaubt
        return consent.granted

    def validate_consent_change(self, purpose_key: str, grant: bool) -> list[str]:
        """Validiert ob Einwilligungsänderung zulässig ist."""
        errors = []
        purpose = self._find_purpose(purpose_key)
        if purpose.required and not grant:
            errors.append(f"Einwilligung für '{purpose.label_de}' ist erforderlich und kann nicht widerrufen werden.")
        return errors
```

<!-- Quelle: ADR-002 / W-006 -->
**`SpeciesReferenceResolver`** — Wandelt `species_key`-Referenzen in `species_ref`-Wrapper um (DSGVO Art. 20 Datenübertragbarkeit).

> **Nicht implementiert** (Stand #1716): Der Resolver existiert im Code nicht, und der
> Export enthält keine `species_ref`-/`cultivar_ref`-Wrapper. Der folgende Abschnitt
> beschreibt den Zielzustand aus ADR-002.

Hintergrund: Plant-Daten enthalten `species_key`-Referenzen. Bei `origin='system'`/`'enrichment'` ist das eine globale Referenz, beim Empfänger auflösbar. Bei `origin='tenant'` ist die Referenz nur im Quell-Tenant gültig. Damit der Export self-contained ist, wird tenant-eigene Species **inline als Snapshot** eingebettet.

```python
class SpeciesReferenceResolver:
    """ADR-002: Wandelt species_key in self-contained species_ref-Wrapper um."""

    async def resolve(self, species_key: str) -> dict:
        """Liefert ein species_ref-Objekt für DSGVO-Export.

        Returns:
          {
            "scope": "global" | "tenant",
            "key": "<species_key>",
            "snapshot": <embedded_data> | None  // nur bei scope='tenant'
          }
        """
        species = await self.species_repo.get(species_key)
        if species.origin != "tenant":
            # Globale Species: nur Referenz, Empfänger kann auflösen
            return {"scope": "global", "key": species_key, "snapshot": None}

        # Tenant-eigene Species: Inline-Snapshot
        snapshot = self._build_snapshot(species)
        return {"scope": "tenant", "key": species_key, "snapshot": snapshot}

    def _build_snapshot(self, species) -> dict:
        """Kompakter, self-contained Snapshot der tenant-eigenen Species."""
        return {
            "scientific_name": species.scientific_name,
            "common_names": species.common_names,
            "family": species.family,
            "genus": species.genus,
            "origin": species.origin,
            "parent_species_key": species.parent_species_key,  # KI-Kontext-Hint
            "growth_phases": species.growth_phases,
            "care_profile": species.care_profile,
            "created_at": species.created_at.isoformat(),
            "_export_note": (
                "Diese Spezies wurde im Quell-Tenant erstellt und ist nicht "
                "in der globalen Stammdaten-Datenbank verfügbar. Inline-Snapshot "
                "für Datenübertragbarkeit (DSGVO Art. 20)."
            ),
        }
```

Aufruf-Pattern im Export-Builder:

```python
# Export-Wrapper für plant_instances:
plant_data = {
    "_key": plant.key,
    "name": plant.name,
    "species_ref": await species_resolver.resolve(plant.species_key),  # statt species_key
    "cultivar_ref": await cultivar_resolver.resolve(plant.cultivar_key) if plant.cultivar_key else None,
    # ... weitere Felder
}
```

Dasselbe Pattern gilt für Cultivar-Referenzen. Der Resolver kann mehrere `species_key`/`cultivar_key`-Auflösungen batch-cachen, um N+1-Queries zu vermeiden.
<!-- /Quelle: ADR-002 / W-006 -->

### 3.2 Service-Schicht

**`PrivacyService`** — Orchestriert alle Datenschutz-Operationen:

```python
class PrivacyService:
    def __init__(
        self,
        export_repo, consent_repo, restriction_repo, erasure_repo,
        email_change_repo, user_repo,
        data_export_engine, erasure_engine, consent_engine,
        token_engine, email_service,
    ): ...

    # --- Art. 15/20: Datenexport ---
    async def request_data_export(self, user_key: str) -> DataExportRequest: ...
        # 1. Validiert: kein aktiver Export vorhanden (DataExportEngine)
        # 2. Erstellt DataExportRequest (status: pending)
        # 3. Dispatcht Celery-Task process_data_export
        # 4. Gibt Request-Objekt zurück

    async def get_export_status(self, user_key: str, export_key: str) -> DataExportRequest: ...
        # Prüft Eigentümerschaft (user_key muss übereinstimmen)

    async def download_export(self, user_key: str, export_key: str) -> ExportFileResponse: ...
        # 1. Prüft Eigentümerschaft und Status (completed)
        # 2. Prüft Ablaufdatum (72h, NFR-011 R-05)
        # 3. Inkrementiert download_count
        # 4. Gibt Dateipfad zurück

    # --- Art. 16: E-Mail-Änderung ---
    def request_email_change(self, user_key: str, new_email: str, *, password: str | None,
                              step_up_code: str | None, step_up_token: str | None,
                              authenticated_with_api_key: bool, client_ip: str | None) -> EmailChangeRequest: ...
        # 1. Zustandslos zuerst (/code-review of #1862): neue E-Mail != eigene (422),
        #    keine reservierte Tombstone-Domain (422) — verrät nichts, verbraucht
        #    keinen Code, keinen gedrosselten Versuch und keine frische Anmeldung
        # 2. Step-up nach REQ-023 §3.9 (StepUpVerifier), VOR dem Adress-Nachschlag:
        #    aktuelles Passwort bei lokalem Konto, sonst eine frische OIDC-Anmeldung
        #    (step_up_token) bzw., nur bei ausschließlich GitHub/Apple, der E-Mail-Code
        #    (#1815, #1841)
        # 3. Schlägt neue E-Mail nach: bereits vergeben? (bei belegter Adresse: Info-Mail
        #    an deren Inhaber statt Fehler, #957 — Route bleibt indistinguishable)
        # 4. Generiert Verifikations-Token (secrets.token_urlsafe(32))
        # 5. Speichert EmailChangeRequest mit Token-Hash
        # 6. Sendet die E-Mail-Änderungs-Mail an die NEUE Adresse: Link
        #    {frontend}/email-change/{token}, kein Anzeigename (#1848, #1856)
        # 7. Benachrichtigt die AKTUELLE Adresse über die Beantragung (#1841, AK-06)

    def confirm_email_change(self, token: str) -> User: ...
        # 1. Findet Request per Token-Hash (verworfen ⇒ derselbe Fehler wie abgelaufen, s. u.)
        # 2. Prüft Ablaufdatum (24h)
        # 3. Aktualisiert User.email
        # 4. Setzt email_verified: true (neue Adresse wurde ja verifiziert)
        # 5. Invalidiert alle Refresh Tokens (Neuanmeldung)
        # 6. Setzt Request status: confirmed, speichert previous_email, den Hash eines
        #    Rückgängig-Tokens und revert_expires_at (#1848)
        # 7. Sendet Info-E-Mail an ALTE Adresse mit dem Rückgängig-Link (AK-06, AK-EC-03)

    def revert_email_change(self, token: str) -> User: ...
        # Öffentlich, Token aus der Info-Mail an die vorherige Adresse (#1848):
        # 1. Findet den bestätigten Request per Rückgängig-Token-Hash; unbekannt,
        #    bereits verwendet oder abgelaufen ⇒ 401 (derselbe Fehler)
        # 2. Vorherige Adresse inzwischen von einem anderen Konto belegt ⇒ 422
        # 3. Setzt User.email zurück, email_verified: true, löscht
        #    password_reset_token_hash/-expires (der Reset-Link ging an die neue Adresse)
        # 4. Invalidiert alle Refresh Tokens, widerruft offene E-Mail-Änderungen
        # 5. Setzt Request status: reverted (einmalig)

    # Ein Passwort-Reset, eine Passwortänderung (beide hinter dem Step-up) und "alle
    # Sitzungen abmelden" setzen jede offene EmailChangeRequest des Kontos auf
    # status: cancelled (#1841) — die drei Vorgänge, die beweisen, dass die
    # Eigentümerin das Konto zurückgeholt hat. Die Bestätigung eines widerrufenen
    # Tokens antwortet danach wie bei einem abgelaufenen.

    # --- Art. 17: Kontolöschung ---
    def request_erasure(self, user_key: str, *, confirmation: StepUpConfirmation,
                        authenticated_with_api_key: bool, client_ip: str | None) -> ErasureRequest: ...
        # 1. Step-up nach REQ-023 §3.9 (StepUpVerifier): eigene E-Mail zurückgetippt,
        #    Passwort bei lokalem Konto, kein API-Key, gedrosselt
        # 2. Erstellt ErasurePlan (ErasureEngine)
        # 3. Sofort: Soft-Delete (User.status → deleted)
        # 4. Sofort: Alle Refresh Tokens invalidieren
        # 5. Sofort: Anonymisierung gesetzlich geschützter Daten
        # 6. Erstellt ErasureRequest (status: scheduled, hard_delete in 90 Tagen)
        # 7. Tenant-Mitgliedschaften entfernen (REQ-024)

    async def get_erasure_status(self, erasure_key: str) -> ErasureRequest: ...

    # --- Art. 18: Verarbeitungseinschränkung ---
    async def restrict_processing(self, user_key: str, scope: str, reason: str) -> ProcessingRestriction: ...
        # Erstellt ProcessingRestriction für den gegebenen Scope

    async def lift_restriction(self, user_key: str, restriction_key: str) -> None: ...
        # Setzt lifted_at, entfernt Sperre

    # --- Art. 21: Widerspruch ---
    async def object_to_processing(self, user_key: str, purpose: str, reason: str) -> ProcessingRestriction: ...
        # Erstellt Restriction mit reason: objection_pending
        # Für Verarbeitungen auf Basis Art. 6(1)(f) berechtigtes Interesse

    # --- Consent-Management ---
    async def get_consents(self, user_key: str) -> list[ConsentWithPurpose]: ...
        # Gibt alle Zwecke mit aktuellem Consent-Status zurück

    async def grant_consent(self, user_key: str, purpose: str) -> ConsentRecord: ...
        # Erteilt Einwilligung (upsert: granted=true, granted_at=now)

    async def revoke_consent(self, user_key: str, purpose: str) -> ConsentRecord: ...
        # 1. Validiert: nicht erforderlich (ConsentEngine)
        # 2. Setzt granted=false, revoked_at=now

    # --- Datenschutzrichtlinie ---
    async def get_privacy_policy(self) -> PrivacyPolicyInfo: ...
        # Gibt aktuelle Version der Datenschutzrichtlinie zurück
        # Öffentlich zugänglich (kein Auth erforderlich)
```

### 3.3 API-Schicht

**Router: `/api/v1/privacy`** — Datenschutz & Betroffenenrechte:

| Methode | Pfad | Beschreibung | Auth | Art. |
|---------|------|-------------|------|------|
| POST | `/privacy/export` | Datenexport beantragen | Ja | 15/20 |
| GET | `/privacy/export/{key}` | Export-Status abfragen | Ja | 15/20 |
| GET | `/privacy/export/{key}/download` | Export-Datei herunterladen | Ja | 15/20 |

<!-- #1461 -->
**Der Download-Endpunkt persistiert bewusst auf einem `GET`.** Er erhöht `download_count`
am `DataExportRequest` (§4.2a) — der Art.-15-Nachweis *ist* die Abholung des Exports.
Würde die Schreibung in eine eigene Anfrage wandern, hielte der Nachweis ein anderes
Ereignis fest als das, das er belegen soll. Die Ausnahme ist an genau diese eine
Schreibsenke gebunden (`_INTENTIONAL_PERSISTING_READS` in
`tests/unit/api/test_write_route_gates.py`); jede weitere Schreibstelle auf demselben
Handler macht den Wächter rot.
| POST | `/privacy/email-change` | E-Mail-Änderung beantragen — Step-up nach REQ-023 §3.9 (`password` bzw. `step_up_code`) | Ja | 16 |<!-- rate-limited, s. u.; #1841 -->
| POST | `/privacy/email-change/confirm` | E-Mail-Änderung bestätigen | Nein (Token) | 16 |<!-- rate-limited, s. u. -->
| POST | `/privacy/erasure` | Kontolöschung beantragen | Ja | 17 |
| GET | `/privacy/erasure/{key}` | Löschstatus abfragen | Ja | 17 |
| GET | `/admin/platform/users/{key}/erasure-preview` | Vorschau für die Administrator-Löschung eines anderen Kontos: dieselbe Form wie `/privacy/erasure-preview`, nur Plattform-Admin, nur Daten des Zielkontos (AK-FK-07, #1961) | Plattform-Admin | 17 |
| GET | `/privacy/erasure-preview` | Vorschau, welche persönlichen Mandanten die Löschung mitnimmt (AK-FK-06, #1824) und welche Organisationen sie verändert — Übergabe der Verwaltung oder verwaist (AK-FK-08, #2134) | Ja | 17 |
| POST | `/privacy/restrict` | Verarbeitungseinschränkung setzen | Ja | 18 |
| DELETE | `/privacy/restrict/{key}` | Verarbeitungseinschränkung aufheben | Ja | 18 |
| POST | `/privacy/object` | Widerspruch einlegen | Ja | 21 |
| GET | `/privacy/consents` | Einwilligungen auflisten | Ja | 7 |
| POST | `/privacy/consents` | Einwilligung erteilen | Ja | 7 |
| DELETE | `/privacy/consents/{purpose}` | Einwilligung widerrufen | Ja | 7 |
| GET | `/privacy/policy` | Datenschutzrichtlinie abrufen | Nein | 13/14 |

**Gesamtanzahl API-Endpunkte:** 14

<!-- Quelle: Issue #1841 -->
**Step-up auf `POST /privacy/email-change` (#1841).** Läuft durch den in REQ-023 §3.9
beschriebenen `StepUpVerifier` — kein zurückgetipptes Ziel (es gibt keins zu bestätigen außer
der eigenen Sitzung), sondern das aktuelle Passwort bzw., bei einem Konto ohne lokales
Passwort, ein `step_up_token` aus einer frischen Anmeldung beim verknüpften OIDC-Provider
(`POST /users/me/step-up/oidc`) oder — nur wenn sämtliche verknüpften Anbieter GitHub und/oder
Apple sind — der Code aus `POST /users/me/step-up-code` (#1815). Nur die **zustandslosen**
Prüfungen der neuen Adresse — identisch mit der eigenen (422), reservierte Tombstone-Domain
(422) — laufen davor: Sie verraten nichts, was der Anfragende nicht schon weiß, und ein
Tippfehler dort verbraucht deshalb weder den mailversandten Code noch einen gedrosselten
Versuch (/code-review of #1862). Der **Nachschlag**, ob die Adresse bereits vergeben ist,
bleibt hinter dem Step-up — ohne bestandenen Step-up prüft die Route also nicht, ob eine
Adresse frei oder vergeben ist. Nach bestandenem Step-up wird die aktuelle Adresse in beiden
Zweigen (freie und bereits vergebene Adresse) benachrichtigt, damit sie für den Anfragenden
ununterscheidbar bleiben (#957).

<!-- Quelle: Issue #958 §2 -->
**Rate-Limit auf `POST /privacy/email-change`** (`settings.rate_limit_email_change`,
Default `5/hour` je Client-IP): Jeder Aufruf verschickt eine Mail an eine vom
Aufrufer **frei gewählte** Adresse — den Verifikations-Link, wenn die Adresse frei
ist, sonst die Info-Mail an deren Inhaber (SEC-H-009 / REQ-023 §3.2). Die
Authentifizierung regelt, *wer* das auslösen darf, aber bis dahin nichts, *wie
oft*; dieser Router trug als einziger schreibender Router überhaupt kein Limit.
Bewusst deutlich strenger als `rate_limit_auth` (20/minute = 1200/Stunde): die
`/auth/*`-Routen sind interaktive Wiederholungsflächen (Tippfehler beim Passwort),
eine Adressänderung ist ein seltener, bewusster Vorgang.

<!-- Quelle: Issue #990 -->
**Rate-Limit auf `POST /privacy/email-change/confirm`**
(`settings.rate_limit_email_change_confirm`, Default `10/minute` je Client-IP):
Der Endpunkt ist unauthentifiziert und verändert Zustand. Das Gegenargument — der
Token sind 32 Zufallsbytes, verglichen über den Hash, Raten ist also kein
realistischer Angriff — stimmt heute und ist eine Eigenschaft von *Code*, die sich
ändern kann, ohne dass jemand diese Entscheidung neu herleitet. Das Limit ist
billige Versicherung, die nicht davon abhängt, dass die Eigenschaft bestehen
bleibt.

Bewusst **nicht** `rate_limit_email_change`: Jenes Limit begrenzt ausgehende Mail
an eine frei gewählte Adresse, deshalb kumulativ und stundenweise. Das Bestätigen
verschickt keine Mail, es begrenzt Token-*Versuche* — und dort ist der Burst aus
einer Quelle die sinnvolle Einheit, nicht ein Stundenkontingent. Die Zahl ist von
der legitimen Seite hergeleitet, nicht von der Angreiferseite: kein Per-IP-Wert
macht einen 2^256-Token ratbar oder unratbar, ein legitimer Vorgang ist genau ein
Request, ein Reload oder ein Retry macht zwei bis drei, und zehn lässt Raum für
mehrere Personen hinter einer NAT in derselben Minute. Link-Prefetching (Outlook
Safe Links, Gmail-Proxy, URL-Detonation) greift hier nicht: das sind GETs, dies
ist ein POST mit JSON-Body.

Die beiden Limits müssen unterschiedlich bleiben, und die Richtung ist
festgeschrieben (`tests/api/test_privacy_email_change_confirm_rate_limit.py`):
Bestätigen muss **großzügiger** als Beantragen sein — sonst nimmt das System mehr
Änderungswünsche an, als es Bestätigungen zulässt — und **strenger** als
`rate_limit_auth`, weil ein Klick keine interaktive Wiederholungsfläche ist.

### 3.4 Request/Response-Schemas

```python
# --- Export (Art. 15/20) ---
class DataExportResponse(BaseModel):
    key: str
    status: Literal['pending', 'processing', 'completed', 'expired', 'failed']
    requested_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    file_size_bytes: Optional[int]
    download_count: int

# --- E-Mail-Änderung (Art. 16) ---
class EmailChangeCreateRequest(BaseModel):  # Step-up nach REQ-023 §3.9 (#1841)
    new_email: EmailStr
    password: Optional[str] = None      # aktuelles Passwort — Pflicht bei lokalem Konto
    step_up_token: Optional[str] = None # Token aus POST /users/me/step-up/oidc — Regelfall ohne lokales Passwort (#1815)
    step_up_code: Optional[str] = None  # Code aus POST /users/me/step-up-code — nur Ausweichweg (ausschließlich GitHub/Apple, #1815)

class EmailChangeConfirmRequest(BaseModel):
    token: str

class EmailChangeRevertRequest(BaseModel):  # POST /privacy/email-change/revert (#1848)
    token: str

# --- Löschung (Art. 17) ---
class ErasureCreateRequest(BaseModel):  # auch Body von DELETE /users/me und DELETE /admin/platform/users/{key}
    confirm_email: str                 # E-Mail des zu löschenden Kontos, zurückgetippt (Pflicht, jedes Konto)
    password: Optional[str] = None     # aktuelles Passwort der handelnden Person — Pflicht bei lokalem Passwort
    # Föderierte Konten bestätigen mit dem Echo allein; echte Re-Auth beim Provider: #1815

class ErasureResponse(BaseModel):
    key: str
    status: Literal['scheduled', 'in_progress', 'completed', 'partially_completed']
    requested_at: datetime
    soft_deleted_at: Optional[datetime]
    hard_delete_scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    anonymized_collections: list[str]
    retained_reason: Optional[str]

# --- Einschränkung (Art. 18) ---
class RestrictionCreateRequest(BaseModel):
    scope: str  # z.B. 'all', 'sensor_data', 'analytics'
    reason: Literal['accuracy_contested', 'unlawful_processing', 'purpose_expired', 'objection_pending']

class RestrictionResponse(BaseModel):
    key: str
    scope: str
    reason: str
    created_at: datetime
    lifted_at: Optional[datetime]

# --- Widerspruch (Art. 21) ---
class ObjectionRequest(BaseModel):
    purpose: str
    reason: str  # Freitext-Begründung

# --- Consent ---
class ConsentGrantRequest(BaseModel):
    purpose: str

class ConsentResponse(BaseModel):
    purpose: str
    label: str  # Lokalisiert (DE/EN)
    description: str  # Lokalisiert
    legal_basis: str
    required: bool
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]

# --- Policy ---
class PrivacyPolicyResponse(BaseModel):
    version: str
    effective_date: date
    purposes: list[ConsentPurposeInfo]
    retention_summary: list[RetentionCategoryInfo]
    data_controller: DataControllerInfo
    rights_summary: list[RightInfo]

# <!-- Quelle: Datenschutzplan Q-T3/Q-T4, #1806 GDPR-007/GDPR-010 -->
class RetentionCategoryInfo(BaseModel):
    """Eine Zeile der Art.-13-Übersicht (`GET /privacy/policy`).

    Werte kommen live aus RetentionService/NFR-011 §4 — nie als Text im
    Frontend fest codiert (Q-T5). Betreiberentscheidung 2026-09-26.
    """
    category: str            # z.B. "soft_deleted_accounts"
    rule_id: str              # NFR-011-Regel, z.B. "R-01"
    period_text: str          # menschlich lesbar, z.B. "90 Tage nach Soft-Delete"
    latest_deletion_point: str
    # Der SPÄTESTE konkrete Zeitpunkt, nicht nur die Frist (Q-T3): die Frist PLUS
    # den ungünstigsten Zeilenabstand des durchsetzenden Takts (§3.1), z.B.
    # "spätestens 91 Tage nach Soft-Delete, um 04:00 UTC" statt nur "nach 90 Tagen" —
    # der tägliche/stündliche Lauf kann den reinen Fristablauf um bis zu ein Intervall
    # überziehen (R-01/R-02/R-03/R-07/R-11 laufen nach der Uhr getaktet, `crontab`, nie
    # als fester Abstand ab dem Beat-Start — NFR-011 §3.1; R-05 wird bei Fertigstellung
    # exakt gestempelt, siehe `DataExportResponse.expires_at`).
    enforcement_status: Literal['enforced', 'partial', 'not_implemented']
    exception_note: Optional[str] = None
    # z.B. bei R-02: "Konten mit verknüpftem Anmeldeweg werden über diesen Pfad nie
    # entfernt" (Q-T3)
```

**Inhalt der Übersicht (Q-T3/Q-T4, Betreiberentscheidung 2026-09-26, #1806).** Zwei
Präzisierungen gegenüber einer reinen Fristangabe:

1. **Spätester konkreter Zeitpunkt statt Fristtext (Q-T3, GDPR-007).** "Nach 90 Tagen"
   verschweigt, dass R-01 täglich um 04:00 UTC läuft und ein Datensatz deshalb bis zu
   einen Tag über den reinen Fristablauf hinaus bestehen kann; `latest_deletion_point`
   MUSS diesen ungünstigsten Fall nennen, nicht nur die Frist selbst. R-02 (unbestätigte
   Accounts) bekommt zusätzlich die Ausnahme genannt: ein Konto mit verknüpftem
   föderiertem Anmeldeweg wird über diesen Pfad nie entfernt (`exception_note`).
2. **R-04/R-07/R-11 stehen jetzt in der Übersicht (Q-T4, GDPR-010) — mit ihrem
   tatsächlichen Stand, nicht erst wenn sie vollständig durchgesetzt sind.** `R-04`
   (Consent Records) und `R-07` (E-Mail-Änderungsanfragen, Hard-Delete-Teil) tragen
   `enforcement_status: 'not_implemented'` bzw. `'partial'` gemäß NFR-011 §2.1
   (Stand #1782/#1800); `R-11` (abgelaufene Refresh Tokens) trägt `'enforced'`. Die
   Übersicht wartet nicht darauf, dass eine Regel vollständig gebaut ist, um sie zu
   nennen — eine fehlende Zeile wäre selbst eine Falschangabe nach Art. 13.
   **Stand seit v1.22 (#1806):** Gemessen am Code tragen R-04 (`retention.purge_expired_consent_records`),
   R-07 (`retention.expire_email_change_requests`, inkl. R-07a/R-07b) und R-11
   (`cleanup_expired_tokens`) alle `enforced`; die Zeile nennt den tatsächlichen Stand,
   nicht den hier ursprünglich vorhergesagten. R-16..R-18 stehen auf `partial` (nur
   Zeilen eines gelöschten Mandanten werden gelöscht). Ein Test bindet jede
   `enforced`-Zeile an einen registrierten Beat-Task.

### 3.5 Celery-Tasks

| Task | Schedule | Beschreibung |
|------|----------|-------------|
| `process_data_export` | On-Demand (dispatcht bei Export-Request) | Sammelt alle User-Daten, erstellt JSON-Datei |
| `execute_scheduled_erasures` | Täglich 04:00 UTC | Führt Hard-Deletes für fällige Löschaufträge aus |

```python
async def process_data_export(export_key: str):
    """Celery-Task: Sammelt alle User-Daten und erstellt Export-Datei."""
    export = await get_export(export_key)
    await update_export_status(export_key, "processing")

    try:
        manifest = data_export_engine.build_export_manifest(export.user_key)
        export_data = {}

        for source in manifest:
            data = await fetch_user_data(source, export.user_key)
            export_data[source.label] = data

        # JSON-Datei schreiben
        file_path = f"/exports/{export_key}.json"
        await write_json(file_path, export_data)
        file_size = await get_file_size(file_path)

        await update_export(export_key, {
            "status": "completed",
            "file_path": file_path,
            "file_size_bytes": file_size,
            "completed_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=72),
        })
    except Exception as e:
        await update_export(export_key, {
            "status": "failed",
            "error_message": str(e),
        })
```

```python
async def execute_scheduled_erasures():
    """Celery-Task: Führt Hard-Deletes für fällige Löschaufträge aus."""
    now = datetime.utcnow()
    pending = await get_due_erasures(now)

    for erasure in pending:
        await update_erasure_status(erasure.key, "in_progress")
        try:
            plan = erasure_engine.build_erasure_plan(erasure.user_key, {})
            # <!-- Quelle: Widerspruchsanalyse W-007 -->
            # Phase 0: Object-Storage-Cleanup (W-007)
            # MUSS vor Phase 1 laufen — nutzt attachments-Metadaten in
            # ArangoDB als Lookup-Quelle (created_by == user_key).
            storage_adapter = get_storage_adapter()
            for rule in plan.storage_cleanup:
                if rule.action == "hard_delete":
                    deleted_count = await storage_adapter.delete_for_user(
                        tenant_key=erasure.tenant_key,
                        user_key=erasure.user_key,
                        scope=rule.scope,
                    )
                    logger.info(
                        "storage_cleanup_hard_delete",
                        scope=rule.scope,
                        user_key=erasure.user_key,
                        tenant_key=erasure.tenant_key,
                        deleted=deleted_count,
                    )
                elif rule.action == "anonymize_metadata_and_strip_exif":
                    # 1. ArangoDB-Metadaten anonymisieren (created_by → '_anonymized')
                    anon_count = await attachment_repo.anonymize_user_metadata(
                        tenant_key=erasure.tenant_key,
                        user_key=erasure.user_key,
                        scope=rule.scope,
                    )
                    # 2. EXIF-Strip-Pass für Tenant-Datensätze mit
                    #    STORAGE_KEEP_EXIF_<category>=true (NFR-013 §6.4).
                    #    Adapter überspringt Dateien ohne EXIF-Daten oder
                    #    Tenant-Settings ohne Keep-EXIF.
                    stripped = await storage_adapter.strip_exif_for_user(
                        tenant_key=erasure.tenant_key,
                        user_key=erasure.user_key,
                        scope=rule.scope,
                    )
                    logger.info(
                        "storage_cleanup_anonymize",
                        scope=rule.scope,
                        user_key=erasure.user_key,
                        tenant_key=erasure.tenant_key,
                        metadata_anonymized=anon_count,
                        exif_stripped=stripped,
                    )
            # <!-- /Quelle: Widerspruchsanalyse W-007 -->
            # <!-- Quelle: REQ-034 Security-Review SR-003 -->
            # Phase 0.5: Referenz-Index-Cleanup (pgvector, REQ-034 §5)
            # MUSS ebenfalls vor Phase 1 laufen. Der DINOv2-Referenz-Index
            # liegt außerhalb von ArangoDB; ohne diesen Pfad blieben vom
            # Nutzer beigesteuerte Embeddings (source='user_contributed')
            # nach der Löschung dauerhaft im Index (Verstoß gegen Art. 17).
            reference_index = get_reference_index_store()  # pgvector
            for rule in erasure_engine.REFERENCE_INDEX_CLEANUP_RULES:
                removed = await reference_index.delete_user_contributions(
                    tenant_key=erasure.tenant_key,
                    user_key=erasure.user_key,
                )
                logger.info(
                    "reference_index_cleanup",
                    store=rule.store,
                    collection=rule.collection,
                    user_key=erasure.user_key,
                    tenant_key=erasure.tenant_key,
                    removed=removed,
                )
            # <!-- /Quelle: REQ-034 Security-Review SR-003 -->
            # Phase 1: Edges löschen
            for edge_collection in plan.edge_deletions:
                await delete_user_edges(edge_collection, erasure.user_key)
            # Phase 2: Documents löschen
            for doc_collection in plan.doc_deletions:
                await delete_user_docs(doc_collection, erasure.user_key)
            # <!-- Quelle: Widerspruchsanalyse W-002 -->
            # Phase 2.5: Audit-Log-Pseudonymisierung (W-002)
            # user_key in Aufbewahrungspflichtigen Audit-Logs durch Tombstone
            # ersetzen, BEVOR Phase 3 den User selbst löscht.
            tombstone = compute_tombstone_hash(
                erasure.user_key, settings.erasure_tombstone_salt
            )
            for rule in plan.pseudonymize_audit:
                affected = await replace_user_field(
                    collection=rule.collection,
                    old_user_key=erasure.user_key,
                    new_value=tombstone,
                    field=rule.user_field,
                )
                logger.info(
                    "audit_log_pseudonymized",
                    collection=rule.collection,
                    field=rule.user_field,
                    affected_rows=affected,
                    tombstone=tombstone,  # Hash ist nicht personenbezogen
                )
            # <!-- /Quelle: Widerspruchsanalyse W-002 -->
            # Phase 3: User löschen
            await hard_delete_user(erasure.user_key)

            await update_erasure(erasure.key, {
                "status": "completed",
                "completed_at": now,
                "deleted_collections": plan.delete,
                "pseudonymized_collections": [r.collection for r in plan.pseudonymize_audit],  # W-002
                "storage_cleanup_scopes": [r.scope for r in plan.storage_cleanup],  # W-007
            })
        except Exception as e:
            await update_erasure(erasure.key, {
                "status": "partially_completed",
                "error_message": str(e),
            })
```

### 3.6 Consent-Prüfung

**Regel (#2136, MT-040): Ein optionaler Zweck steht nur dann in `ConsentEngine.PURPOSES`, wenn Code ihn liest.** Ein Zweck, der in der Einwilligungsliste und in der Datenschutzerklärung (Art. 13) erscheint, verspricht eine Verarbeitung, die die Einwilligung schaltet; liest ihn nichts, startet eine Erteilung nichts und ein Widerruf stoppt nichts (Art. 7 (3)). Der Guard `tests/unit/guards/test_consent_purposes_are_read.py` verlangt, dass jeder optionale Schlüssel außerhalb seiner Deklaration unter `app/` genannt wird (als Literal oder über die Konstante aus `consent_engine.py`). Ein Zweck kommt mit dem Feature, das ihn liest.

Geprüft wird in der Fachlogik, nicht in einer FastAPI-Dependency: `ConsentGuard.require_consent(user_key, purpose)` (`app/domain/guards/consent_guard.py`) wirft `ConsentRequiredError` (403), `has_consent` antwortet mit `bool`. Beide lesen den Datensatz und fragen `ConsentEngine.is_processing_allowed` — ein fehlender Datensatz heißt „nicht erteilt".

| Zweck | Wo gelesen | Wirkung ohne Einwilligung |
|---|---|---|
| `ai_tenant_data_access`, `ai_cloud_processing` | `ConsentGuard.require_consent` in KI-Assistent, Diagnose, Glossar (REQ-031/035/036) | 403 |
| `diary_ai_analysis` | Tagebuch-Freigabe (REQ-050) | 403 |
| `plant_identification`, `pest_detection_cloud`, `plant_diagnosis`, `reference_contribution` | jeweilige Fachservices (REQ-029/034/038/044) | 403 bzw. kein Beitrag |
| `error_tracking` | `app/observability/event_user.py` beim Erfassen eines Fehlerberichts, höchstens einmal je Anfrage | Bericht ohne `user`-Block (keine Konto-/Mandanten-Pseudonyme); nicht lesbare Einwilligung zählt als „nein" |

```python
# Fachlogik (Beispiel REQ-031):
self._consent.require_consent(ctx.user_key, AI_TENANT_DATA_ACCESS)

# Fehler-Tracking (#2136): der user-Block des Ereignisses nur mit Einwilligung
if not telemetry.consent(ERROR_TRACKING, has_consent):
    return None  # Ereignis ohne user
```

**Entfernte Zwecke (#2136):** `hibp_check` (keine HaveIBeenPwned-Prüfung vorhanden) und `external_enrichment` (Katalog-Job ohne Personenbezug und ohne Nutzer). Gespeicherte Datensätze bleiben, werden exportiert, gelöscht und nach R-04 bereinigt wie jeder andere; sie werden nicht mehr gelistet, Erteilen und Widerrufen antworten mit `422`.

### 3.7 Middleware: Restriction-Prüfung

```python
def check_processing_restriction(scope: str):
    """FastAPI Dependency: Prüft ob Verarbeitungseinschränkung für den Scope aktiv ist."""
    async def check(
        current_user: User = Depends(get_current_user),
        restriction_repo: RestrictionRepository = Depends(get_restriction_repo),
    ) -> None:
        restrictions = await restriction_repo.get_active_by_user(current_user.key)
        for r in restrictions:
            if r.scope in ("all", scope) and r.lifted_at is None:
                raise HTTPException(
                    status_code=423,  # Locked
                    detail=f"Verarbeitung eingeschränkt: {r.reason}"
                )
    return check
```

---

## 4. Frontend

### 4.1 Neue Seiten

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| `PrivacySettingsPage` | `/settings/privacy` | Datenschutz-Einstellungen mit 4 Tabs |

### 4.2 Komponenten

**`PrivacySettingsPage`** — 4 Tabs:

**Tab "Einwilligungen":**
- Liste aller Verarbeitungszwecke (aus `GET /privacy/consents`)
- Jeder Zweck zeigt: Label, Beschreibung, Rechtsgrundlage, Status (erteilt/widerrufen)
- Erforderliche Zwecke: Toggle deaktiviert, Hinweistext "Erforderlich für den Betrieb"
- Optionale Zwecke: Toggle zum Erteilen/Widerrufen
- Zeitstempel der letzten Änderung

**Tab "Datenexport":**
- Button "Meine Daten exportieren" (disabled wenn bereits ein Export läuft)
- Liste vergangener Exporte mit Status (pending/processing/completed/expired)
- Download-Link für abgeschlossene Exporte (mit Dateigröße)
- Info-Text zur Verfügbarkeitsdauer <!-- Q-T5, #1806 GDPR-006, Betreiberentscheidung 2026-09-26 -->
  **interpoliert die tatsächliche Stundenzahl aus der API-Antwort** (`DataExportResponse.expires_at`
  bzw. eine vom Backend gelieferte Stundenzahl aus `RETENTION_EXPORT_FILE_RETENTION_HOURS`),
  nie eine im Frontend fest codierte Zahl. Der Text "Download ist 72 Stunden verfügbar" ist
  nur der Default-Fall bei unverändertem Setting, keine feste Zeichenkette — ändert der
  Betreiber die Frist über §4, MUSS die UI ohne Code-Änderung die neue Zahl zeigen.

**Tab "Account löschen":**
- Warnhinweis zur Unwiderruflichkeitsfrist <!-- Q-T5, #1806 GDPR-006 -->, ebenfalls aus der
  API interpoliert (`RETENTION_SOFT_DELETE_RETENTION_DAYS`), nie fest codiert. Default-Fall:
  "Diese Aktion ist nach 90 Tagen unwiderruflich"
- **Transparente Aufschlüsselung:** Welche Daten vollständig gelöscht werden (Profil, Sessions, Einwilligungen, Aufgaben) und welche nur anonymisiert werden (Erntedokumentation, IPM-Behandlungsnachweise — gesetzliche Aufbewahrungspflicht nach CanG/PflSchG). <!-- Quelle: Widerspruchsanalyse W-001 -->
- **Mandanten-Vorschau (Betreiberentscheidung Q-T6, #1824):** Vor der Bestätigung zeigt der Dialog je persönlichem Mandanten der Person eine Zeile "Mandant „<Name>" wird gelöscht, N weitere Mitglieder betroffen" (bei `N = 0` ohne den Mitglieder-Zusatz), damit die Transparenzpflicht auch die neue Erasure-together-Regel (Q-E1) abdeckt, bevor die Person bestätigt.

    **Implementiert (v1.24, #1824).** Die Vorschau liest `GET /privacy/erasure-preview`
    (nur für das eigene Konto; Mandantenname der Person und eine Anzahl, nie Name, E-Mail
    oder Rolle der anderen Mitglieder). Sie erscheint schon im Tab und noch einmal im
    Bestätigungsdialog; im Dialog der Kontoeinstellungen („Konto" → „Konto löschen")
    ebenfalls. Lässt sich die Vorschau nicht laden, sagt der Dialog das ausdrücklich — er
    zeigt dann keine leere Liste, die wie „nichts betroffen" aussähe.
- Bestätigung: die eigene E-Mail-Adresse zurücktippen und — bei lokalem Konto — das aktuelle Passwort; ein Konto ohne eines meldet sich stattdessen frisch beim verknüpften OIDC-Provider erneut an, nur bei ausschließlich GitHub/Apple über den per E-Mail zugeschickten Einmalcode (REQ-023 §3.9, #1815); nach zu vielen Fehlversuchen zeigt der Dialog die Wartezeit (429 `STEP_UP_LOCKED`)
- Bestätigungs-Dialog mit Checkbox "Ich verstehe, dass mein Account gelöscht wird und gesetzlich geschützte Daten anonymisiert aufbewahrt bleiben"

**Tab "Verarbeitungseinschränkung":**
- Info-Text: Erklärung Art. 18 DSGVO
- Formular: Scope auswählen, Grund auswählen
- Liste aktiver Einschränkungen mit "Aufheben"-Button
- Widerspruchs-Formular (Art. 21): Zweck + Freitext-Begründung

### 4.3 i18n-Keys

```
pages.privacy.title: "Datenschutz-Einstellungen"
pages.privacy.tabs.consents: "Einwilligungen"
pages.privacy.tabs.export: "Datenexport"
pages.privacy.tabs.delete: "Account löschen"
pages.privacy.tabs.restrictions: "Verarbeitungseinschränkung"
pages.privacy.export.button: "Meine Daten exportieren"
pages.privacy.export.pending: "Export wird vorbereitet..."
pages.privacy.export.download: "Herunterladen"
pages.privacy.export.expires: "Verfügbar bis {{date}}"
pages.privacy.export.availableForHours: "Verfügbar für {{hours}} Stunden" <!-- Q-T5: {{hours}} aus der API, nie fest codiert -->
pages.privacy.delete.warning: "Diese Aktion ist nach {{days}} Tagen unwiderruflich." <!-- Q-T5: {{days}} aus der API, nie fest codiert -->
pages.privacy.delete.confirm: "Ich verstehe, dass mein Account gelöscht wird"
pages.privacy.delete.button: "Account endgültig löschen"
pages.privacy.delete.tenantPreview: "Mandant „{{name}}" wird gelöscht ({{memberCount}} weitere Mitglieder betroffen)"
pages.privacy.consent.required: "Erforderlich für den Betrieb"
pages.privacy.consent.granted: "Erteilt am {{date}}"
pages.privacy.consent.revoked: "Widerrufen am {{date}}"
pages.privacy.restriction.info: "Sie können die Verarbeitung Ihrer Daten für bestimmte Zwecke einschränken."
pages.privacy.objection.title: "Widerspruch"
```

---

## 5. Seed-Daten

### Standard-Consent-Purposes (Vorkonfiguriert):

```json
[
  {
    "key": "core_functionality",
    "label_de": "Grundfunktionen",
    "label_en": "Core Functionality",
    "required": true,
    "legal_basis": "Art. 6(1)(b)"
  },
  {
    "key": "error_tracking",
    "label_de": "Fehlerberichte meinem Konto zuordnen (Sentry)",
    "label_en": "Attribute error reports to my account (Sentry)",
    "required": false,
    "legal_basis": "Art. 6(1)(a)"
  },
  {
    "key": "ai_tenant_data_access",
    "label_de": "KI-Assistent darf meine Pflanzendaten als Kontext nutzen",
    "label_en": "AI assistant may use my plant data as context",
    "required": false,
    "legal_basis": "Art. 6(1)(a)",
    "description_de": "Erlaubt dem serverseitigen KI-Assistenten (REQ-031), bei Tipp-Karten, 'Warum?'-Erklärungen, Chat und Diagnose-Sessions auf Stammwerte deiner Pflanzen (Art, Phase, Substrat, EC, pH, VPD, IPM-Status) zuzugreifen, um personalisierte Empfehlungen zu generieren. Ohne diese Einwilligung sind nur allgemeine Wissensfragen (Glossar, REQ-035) verfügbar. Auf diesem Weg werden personenbezogene Daten (Name, E-Mail, Tagebuch-Freitexte) NIE übertragen. Wenn du einzelne Tagebuch-Einträge samt Fotos ausdrücklich zur Analyse freigeben möchtest, ist das ein getrennter Weg mit eigener Einwilligung (siehe 'diary_ai_analysis').",
    "description_en": "Allows the server-side AI assistant (REQ-031) to access stem values of your plants (species, phase, substrate, EC, pH, VPD, IPM status) when generating tip cards, 'Why?' explanations, chat answers and diagnosis sessions. Without this consent only general knowledge questions (Glossary, REQ-035) are available. On this path, personal data (name, email, diary free text) is NEVER transmitted. Releasing individual diary entries including photos for analysis is a separate path with its own consent (see 'diary_ai_analysis')."
  },
  {
    "key": "diary_ai_analysis",
    "label_de": "Einzelne Tagebuch-Einträge dürfen von meinem KI-Agenten analysiert werden",
    "label_en": "Individual diary entries may be analysed by my AI agent",
    "required": false,
    "legal_basis": "Art. 6(1)(a)",
    "description_de": "Erlaubt dir, einzelne Tagebuch-Einträge samt Freitext und Fotos zur Analyse freizugeben (REQ-050). Die Analyse führt ein KI-Agent aus, den DU betreibst und der die Daten über deinen eigenen API-Schlüssel abruft — Kamerplanter selbst ruft dabei kein Sprachmodell auf. Es wird nie automatisch etwas analysiert: Jeden einzelnen Eintrag musst du selbst markieren. Übertragen werden verkleinerte Bildfassungen ohne Aufnahmeort und Gerätekennung. Ein Widerruf verhindert neue Markierungen und lässt vorhandene Ergebnisse unberührt.",
    "description_en": "Allows you to release individual diary entries, including free text and photos, for analysis (REQ-050). The analysis is performed by an AI agent that YOU operate and that fetches the data via your own API key — Kamerplanter itself never calls a language model. Nothing is ever analysed automatically: you have to mark every single entry yourself. Only downscaled image renditions without capture location or device identifier are transmitted. Withdrawing consent prevents new markings and leaves existing results untouched."
  },
  {
    "key": "ai_cloud_processing",
    "label_de": "KI-Anfragen dürfen über Cloud-Provider verarbeitet werden",
    "label_en": "AI requests may be processed via cloud providers",
    "required": false,
    "legal_basis": "Art. 6(1)(a) + Art. 49 (Drittland)",
    "description_de": "Erlaubt die Verarbeitung deiner KI-Anfragen über Cloud-Provider (OpenAI, Anthropic, OpenAI-kompatible Anbieter). Dabei werden anonymisierte Pflanzdaten und deine Frage an den Cloud-Anbieter (typischerweise USA) übermittelt. Lokale Provider (Ollama im eigenen Cluster) erfordern diesen Consent NICHT.",
    "description_en": "Allows your AI requests to be processed via cloud providers (OpenAI, Anthropic, OpenAI-compatible). Anonymized plant data and your question are transmitted to the cloud provider (typically USA). Local providers (Ollama in own cluster) do NOT require this consent."
  },
  {
    "key": "social_publishing",
    "label_de": "Beiträge meiner Pflanzen dürfen an ein soziales Netzwerk (Mastodon) übertragen werden",
    "label_en": "Posts of my plants may be transmitted to a social network (Mastodon)",
    "required": false,
    "legal_basis": "Art. 6(1)(b) (nutzerinitiierte Veröffentlichung); Art. 6(1)(a) (automatische Veröffentlichung); Art. 49 (Drittland möglich)",
    "description_de": "Erlaubt Kamerplanter, Beiträge deiner Pflanzen (Text, Fotos als bereinigte Bildfassungen ohne Aufnahmeort) an den Mastodon-Server zu senden, den du für die Pflanze verknüpft hast. Der Mastodon-Server ist ein eigener Anbieter mit eigenen Datenschutzregeln und kann außerhalb der EU stehen. Dein Name, dein Wohnort, Sensorwerte, Düngung und Notizen werden nie übertragen. Löschen auf dem Mastodon-Server klappt nur, soweit der Server es zulässt. Ohne diese Einwilligung kannst du Profile und Verlauf deiner Pflanzen weiter nutzen und per Link teilen; nicht möglich sind das Verknüpfen eines Mastodon-Kontos sowie das Freigeben oder Senden von Beiträgen an Mastodon — auch für Beiträge, die andere Gärtner vorbereitet haben.",
    "description_en": "Allows Kamerplanter to send posts of your plants (text, photos as cleaned renditions without capture location) to the Mastodon server you linked for the plant. The Mastodon server is a separate provider with its own privacy rules and may be located outside the EU. Your name, your place of residence, sensor values, fertilisation and notes are never transmitted. Deletion on the Mastodon server only works as far as that server allows. Without this consent you can still use plant profiles and timelines and share them by link; linking a Mastodon account and approving or sending posts to Mastodon — including posts prepared by other gardeners — are unavailable."
  }
]
```

<!-- Quelle: REQ-031 v2.0; social_publishing: REQ-055 v1.3 §17.6 -->

**Hinweis zur Abgrenzung `ai_tenant_data_access` ↔ `diary_ai_analysis`:** Das sind zwei getrennte Wege mit gegenläufigen Eigenschaften, und sie dürfen nicht miteinander verrechnet werden. `ai_tenant_data_access` betrifft den **serverseitigen** Assistenten: Kamerplanter ruft das Modell, überträgt Stammwerte und niemals Freitext. `diary_ai_analysis` betrifft den **vom Nutzer betriebenen** Agenten (REQ-050): Kamerplanter ruft kein Modell, sondern gibt einen einzelnen, ausdrücklich markierten Eintrag samt Freitext und Bildfassungen über die MCP-Schnittstelle heraus. Keiner der beiden Consents impliziert den anderen. `ai_cloud_processing` gilt für `diary_ai_analysis` **nicht** — die Wahl des Modells und des Anbieters liegt dort vollständig beim Nutzer und außerhalb der Verantwortung der Instanz.

**Hinweis zur Verkettung:** `ai_cloud_processing` ist eine Zusatz-Einwilligung. Wenn ein Tenant-Admin einen Cloud-Provider als Default konfiguriert hat, brauchen Endpoints, die Tenant-Daten mit Cloud-Verarbeitung kombinieren, beide Einwilligungen (`ai_tenant_data_access` UND `ai_cloud_processing`). Light-Modus-Endpoints (`/api/v1/public/ai/*` aus REQ-031 v2.0 §5.3 und das Glossar aus REQ-035) brauchen weder den einen noch den anderen Consent, da sie keine personenbezogenen Daten verarbeiten.

---

## 6. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Art. | Prüfmethode |
|---|-----------|------|-------------|
| AK-01 | Datenexport enthält alle im Manifest definierten User-Daten als JSON | 15/20 | Integration |
| AK-01a | Jede Collection, die die Kontolöschung als Daten der Person löscht oder anonymisiert, ist im Datenexport enthalten oder mit Begründung in `DataExportEngine.EXCLUDED_FROM_DISCLOSURE` ausgeschlossen (§3.1.4, #1719) | 15/17 | Unit + Integration |
<!-- Quelle: Datenschutzplan Q-T2, #1839 GDPR-007 -->
| AK-01b | Der Anhänge-Abschnitt des Datenexports markiert eine vor #1770 zusammengeführte doppelte Datei, deren zweiter Hochlader nicht rekonstruierbar ist, mit `attribution_gap` statt sie so darzustellen, als hätte nur ein Konto sie hochgeladen (§3.1.2 Regel 5) | 15 | Integration |
<!-- /Quelle: Datenschutzplan Q-T2, #1839 GDPR-007 -->
| AK-02 | Export-Datei ist nach 72 Stunden nicht mehr downloadbar (Status: expired) | 15/20 | Integration |
<!-- Quelle: Datenschutzplan Q-T5, #1806 GDPR-006 -->
| AK-02a | Kein Frontend-Text codiert eine Aufbewahrungs- oder Verfügbarkeitsfrist fest; Export-Verfügbarkeit (`pages.privacy.export.availableForHours`) und Lösch-Unwiderruflichkeit (`pages.privacy.delete.warning`) interpolieren den von der API gelieferten Wert (`{{hours}}`/`{{days}}`). Ein Test, der die Frist ändert (Settings) und denselben Text unverändert erwartet, prüft die durch diese Entscheidung gestrichene Regel | Unit + Vitest |
<!-- /Quelle: Datenschutzplan Q-T5, #1806 GDPR-006 -->
| AK-03 | Max. 1 aktiver Export-Auftrag pro User | 15/20 | Unit |
| AK-04 | E-Mail-Änderung erfordert Verifikation der neuen Adresse (Token, 24h gültig) | 16 | Integration |
| AK-05 | Nach E-Mail-Änderung werden alle Sessions invalidiert | 16 | Integration |
| AK-06 | Info-E-Mail wird an die alte Adresse gesendet (bei Bestätigung) und an die aktuelle Adresse (bei Beantragung, #1841) | 16 | Integration |
| AK-07 | Kontolöschung setzt User sofort auf status: deleted (Soft-Delete) | 17 | Integration |
| AK-07a | Kontolöschung und Löschauftrag entfernen `password_hash` (und die Kontolöschung zusätzlich `avatar_url`) aus dem gespeicherten Dokument | 17 | Integration |
| AK-08 | Erntedaten und Behandlungsanwendungen werden anonymisiert, nicht gelöscht | 17 | Integration |
| AK-08a | Löschbestätigung unterscheidet zwischen `fully_deleted_categories` und `anonymized_categories` und zeigt beide Listen transparent an | 17 | E2E |
| AK-09 | Hard-Delete erfolgt 90 Tage nach Soft-Delete (NFR-011 R-01) | 17 | Integration |
| AK-10 | Erasure-Audit-Log wird für 3 Jahre aufbewahrt (Q-R12) | 17 | Integration |
| AK-11 | Verarbeitungseinschränkung blockiert betroffene Endpunkte (423 Locked) | 18 | Integration |
| AK-12 | Widerspruch erstellt Restriction mit reason: objection_pending | 21 | Integration |
| AK-13 | Erforderliche Einwilligungen können nicht widerrufen werden | 7 | Unit |
| AK-14 | Consent-Prüfung blockiert Feature-Endpunkte ohne Einwilligung (403) | 7 | Integration |
| AK-15 | Datenschutzrichtlinie ist ohne Authentifizierung abrufbar | 13/14 | Integration |
<!-- Quelle: Datenschutzplan Q-T3, #1806 GDPR-007 -->
| AK-15a | Jede Zeile in `retention_summary` nennt in `latest_deletion_point` den spätesten konkreten Zeitpunkt (Frist plus ungünstigster Takt-Abstand des durchsetzenden Celery-Tasks, §3.1), nicht nur die Frist; die R-02-Zeile trägt in `exception_note` die Ausnahme für Konten mit verknüpftem Anmeldeweg | 13 | Unit |
<!-- /Quelle: Datenschutzplan Q-T3, #1806 GDPR-007 -->
<!-- Quelle: Datenschutzplan Q-T4, #1806 GDPR-010 -->
| AK-15b | `retention_summary` enthält Zeilen für R-04, R-07 und R-11 mit ihrem tatsächlichen `enforcement_status` (`not_implemented`/`partial`/`enforced` gemäß NFR-011 §2.1); eine Regel fehlt nicht deshalb, weil sie noch nicht vollständig durchgesetzt ist | 13 | Unit |
<!-- /Quelle: Datenschutzplan Q-T4, #1806 GDPR-010 -->
| AK-16 | Celery-Task process_data_export erstellt korrekte JSON-Datei | 15/20 | Integration |
| AK-17 | Celery-Task execute_scheduled_erasures löscht fällige Accounts endgültig | 17 | Integration |
<!-- Quelle: Widerspruchsanalyse W-002 -->
| AK-PD-01 | **Audit-Pseudonymisierung:** Nach Abschluss eines Erasure-Requests MUSS in jeder Collection aus `PSEUDONYMIZE_AUDIT_COLLECTIONS` (aktuell: `erasure_requests`) der `user_key`-Wert durch einen Tombstone-Hash im Format `anon_<16hex>` ersetzt sein. Der Original-`user_key` darf nicht mehr in der Collection auffindbar sein. | 5(1)(e) | Integration |
| AK-PD-02 | **Tombstone-Determinismus & Salt-Schutz:** `compute_tombstone_hash(user_key, salt)` erzeugt für gleiche Eingaben denselben Hash; ohne Kenntnis von `ERASURE_TOMBSTONE_SALT` ist eine Reidentifikation aus dem Hash nicht möglich. Bei `salt=""` oder `len(salt) < 32` MUSS `ValueError` geworfen werden. | 5(1)(e) | Unit |
<!-- /Quelle: Widerspruchsanalyse W-002 -->
<!-- Quelle: Widerspruchsanalyse W-007 -->
| AK-OS-01 | **Storage-Cleanup `user_personal`:** Nach Abschluss eines Erasure-Requests sind alle Anhaenge mit `created_by == user_key` UND `category in {profile, user_notes}` aus dem Object Storage HART GELÖSCHT (`storage_adapter.delete_for_user(scope='user_personal')`). Anschließendes `head_object(key)` MUSS HTTP 404 liefern. | 17 | E2E |
| AK-OS-02 | **Storage-Anonymisierung `user_diary_attachments`:** Nach Abschluss eines Erasure-Requests haben alle Anhaenge mit `created_by == user_key` UND `category in {diary, inspection, treatment, harvest}` das ArangoDB-Metadatum `created_by = '_anonymized'`. Die S3-Datei selbst bleibt erhalten und behält ihren ursprünglichen Pfad (`t/{tenant}/{entity_type}/{entity_key}/{filename}`). | 17 | Integration |
| AK-OS-03 | **EXIF-Strip-Pass:** Wenn der Tenant für eine Kategorie `STORAGE_KEEP_EXIF_<category>=true` gesetzt hat, MUSS bei der Erasure ein `storage_adapter.strip_exif_for_user()`-Aufruf alle EXIF-Daten (GPS, Kamera-Seriennummer, Aufnahmezeit) aus den verbleibenden Diary-Fotos des Users entfernen. Bilder ohne EXIF und Tenants ohne Keep-EXIF werden nicht modifiziert. | 17, NFR-013 §6.4 | Integration |
| AK-OS-04 | **Phase-Reihenfolge:** Im Celery-Task `execute_scheduled_erasures` läuft Phase 0 (Storage-Cleanup) VOR Phase 1 (Edges). Wenn Phase 0 fehlschlägt, MUSS der Erasure-Status auf `partially_completed` gesetzt werden — kein Phase-1-Aufruf. | — | Unit |
<!-- /Quelle: Widerspruchsanalyse W-007 -->
<!-- Quelle: REQ-034 Security-Review SR-003 -->
| AK-OS-05 | **Referenz-Index-Cleanup (Phase 0.5):** Nach Abschluss eines Erasure-Requests sind alle DINOv2-Embeddings im pgvector-`species_embeddings`-Index mit `source == 'user_contributed'` UND `contributed_by == user_key` gelöscht. Bei Tenant-Löschung gilt derselbe Filter mit `tenant_key == X`. Phase 0.5 läuft VOR Phase 1; Fehlschlag ⇒ `partially_completed` (kein ArangoDB-Delete). Kuratiert übernommene Referenzen (`source != 'user_contributed'`) bleiben unberührt. | REQ-029-A §5.1, REQ-034 §5 | Integration |
| AK-OS-05a | **Referenz-Index-Bindung meldet ehrlich:** Die Löschung nach AK-OS-05 läuft über eine Bindung, die die Vektoren tatsächlich entfernt (`InferenceServiceReferenceIndexStore`, gebunden bei `INFERENCE_SERVICE_ENABLED`). Die No-op-Bindung meldet nur so lange `0`, wie nie ein Beitrag geschrieben wurde; ist `system_settings.reference_contributions_since` gesetzt, verweigert sie: fällige Löschaufträge bleiben als Konfigurationsfehler offen, die Mandantenlöschung antwortet 503. Der Löschauftrag hält `reference_index_binding` und `reference_index_removed` fest (#1761). | 17 | Unit + Integration |
<!-- /Quelle: REQ-034 Security-Review SR-003 -->
<!-- Quelle: #1766 (#1759, #1760) -->
| AK-OS-06 | **Vorschaubilder gehen mit dem Original:** Löscht Phase 0 ein gespeichertes Original hart (Scopes mit `action == 'hard_delete'`, heute `user_personal` und `user_pest_reference_images`), sind danach auch seine WebP-Renditionen (`<stem>_t128.webp`, `<stem>_t512.webp`, `<stem>_t1280.webp`, `rendition_keys()`) aus dem Object Storage entfernt; dasselbe gilt für das Löschen eines einzelnen Anhangs. Renditionen, die der Thumbnail-Task erst nach der Löschung fertigstellt, verwirft er. Dateien unter `anonymize_metadata_and_strip_exif` bleiben samt Renditionen erhalten (AK-OS-02). | 17 | Integration + Reach (T2) |
| AK-OS-07 | **Beigesteuerte Schädlings-Prototypen werden gelöscht:** Nach Abschluss eines Erasure-Requests ist zu jedem `pest_image_contributions`-Eintrag des Nutzers der Prototyp im pgvector-Index `pest_embeddings` gelöscht — unabhängig vom Status, also auch ein bereits deaktivierter (herabgestufter) — und zwar vor den Verknüpfungsdokumenten. Bei Mandantenlöschung gilt dasselbe für alle Beiträge des Mandanten, auch solche, deren Dokument schon fehlt, vor jeder ArangoDB-Löschung. Kuratierte Prototypen (`source != 'user_contributed'`) bleiben unberührt. Fehlschlag ⇒ `partially_completed` (kein ArangoDB-Delete) bzw. Mandantenlöschung 502; die No-op-Bindung verweigert, sobald `system_settings.pest_prototype_contributions_since` gesetzt ist. Der Löschauftrag hält `pest_prototype_binding` und `pest_prototypes_removed` fest. | 17 | Integration + Reach (T2) |
<!-- /Quelle: #1766 (#1759, #1760) -->
<!-- Quelle: #1770 (GDPR-006, SEC-007) -->
| AK-OS-08 | **Deduplizierte Anhänge gehören jedem Hochlader selbst:** Lädt ein zweites Mitglied (oder dasselbe Mitglied in einer anderen Kategorie) Bytes hoch, die im Mandanten schon gespeichert sind, erhält es einen eigenen `attachments`-Datensatz mit eigenem `created_by`, der auf dasselbe gespeicherte Objekt zeigt; ein erneuter Upload desselben Mitglieds in derselben Kategorie liefert dessen eigenen Datensatz zurück. Löscht Phase 0 die Datensätze eines Nutzers hart, bleibt ein Objekt (samt Renditionen), das ein Datensatz außerhalb dieser Löschung noch hält, erhalten; jedes andere wird gelöscht. Dasselbe gilt für das Löschen eines einzelnen Anhangs. Hält nach dem ArangoDB-Schritt kein Datensatz mehr ein Objekt, das Phase 0 für ein anderes Mitglied behalten hat (dessen Datensatz ging zwischenzeitlich), löscht der Lauf es danach. Der Löschauftrag hält `storage_objects_removed`, `storage_objects_retained_shared` und `storage_objects_released` fest. Jeder Schädlingsbild-Beitrag hat einen eigenen Datensatz, auch wenn dasselbe Mitglied dasselbe Foto mehrfach beiträgt. Die EXIF-Bereinigung nach AK-OS-03 schreibt ein geteiltes Objekt an Ort und Stelle um: Die Bytes sind identisch hochgeladen, die Metadaten also auch die der gelöschten Person. Identische Bytes verschiedener Mandanten werden nie geteilt. | 17 | Integration + Reach (T2) |
| AK-OS-05b | **Ein Referenz-Beitrag, eine Zeile, ein Beitragender:** Die `source_record_id` eines Beitrags zum Referenz-Index (`species_embeddings`) ist aus Bildhash, `tenant_key` und Beitragendem abgeleitet. Ein erneuter Beitrag desselben Fotos durch denselben Beitragenden bleibt eine Zeile; dasselbe Foto eines anderen Beitragenden — auch aus einem anderen Mandanten — ist eine eigene Zeile mit dessen Provenienz, die nur dessen Löschung (AK-OS-05) bzw. die Löschung seines Mandanten entfernt. | 17 | Unit |
<!-- /Quelle: #1770 (GDPR-006, SEC-007) -->
<!-- Quelle: Datenschutzplan Q-E8, #1839 GDPR-006 -->
| AK-OS-09 | **Nicht implementiert** (#1839, Betreiberentscheidung 2026-09-26): Bleibt nach einer Löschung ein von AK-OS-08 erfasstes Objekt bestehen, weil ein fremder Datensatz es noch hält, und betrifft der Inhalt erkennbar die gelöschte Person, wird der verbleibende Halter benachrichtigt (Art. 19 DSGVO). Die Benachrichtigung nennt keinen Kontoschlüssel der gelöschten Person. | 19 | Integration |
<!-- /Quelle: Datenschutzplan Q-E8, #1839 GDPR-006 -->
<!-- Quelle: Datenschutzplan Q-O3, #1834 -->
| AK-OS-10 | **Objekte ohne Datensatz werden gefunden:** Jeder Löschpfad entscheidet über ein Objekt aus dem `attachments`-Katalog; bleibt ein Objekt zurück, dessen letzter Datensatz verschwunden ist (Storage-Fehler nach dem committeten Plan, Datensatz im Fenster zwischen Phase 0 und Plan, generisch hochgeladene Schädlingsreferenz in einem Mandanten, den die Person verlassen hat, Storage-Delete nach entferntem Datensatz), erreicht es kein Art.-17-Verfahren und keine Quota mehr. Der tägliche Lauf `reconcile_orphaned_storage_objects` (NFR-013 §6.6) listet `t/` über beide Adapter, bildet Originale und Renditionen auf haltende Datensätze ab und meldet nur Zahlen (`found`, `young`, `eligible`, `would_delete`, `deleted`, `failed`). Er löscht erst mit `STORAGE_RECONCILE_DELETE_ENABLED=true` (Default aus), nur ältere als `STORAGE_RECONCILE_MIN_AGE_HOURS` (Default 24, Untergrenze 1) und nie ein gehaltenes Objekt. | Integration (ArangoDB + local-fs), Unit |
<!-- /Quelle: Datenschutzplan Q-O3, #1834 -->
<!-- Quelle: #1776 (#1767 GDPR-004, SEC-003) -->
| AK-IE-01 | **Sofortlöschung mit Nachweis:** `DELETE /admin/platform/users/{key}` (Plattform-Admin) und die Bereinigung unverifizierter Konten (`cleanup_unverified_accounts`) persistieren einen Löschauftrag in `erasure_requests` (`origin` `platform_admin` bzw. `unverified_cleanup`; ein offener Auftrag der Person wird weiterverwendet) und führen dieselbe Finalisierung aus wie der geplante Art.-17-Lauf. Der Auftrag wird nur `completed`, wenn jeder deklarierte Schritt erreicht wurde; sonst `partially_completed` mit Backoff, den der tägliche Lauf wiederholt, und der Zustand ist am Auftrag sichtbar. **Seit #1949 antwortet `DELETE /admin/platform/users/{key}` mit `202`**, sobald der Auftrag persistiert, das Konto gesperrt und die Mitglieder benachrichtigt sind; der Lauf selbst (auch der Löschlauf der persönlichen Mandanten in begrenzten Stapeln mit Heartbeat) läuft im Celery-Task `retention.run_account_erasure`, und ein Fehler (vorher 500 `ERASURE_INCOMPLETE` bzw. 502) ist der Auftragsstatus `partially_completed`, lesbar über `GET /admin/platform/erasures/{erasure_key}`. Nach Abschluss nennt kein Löschauftrag mehr den Kontoschlüssel im Klartext (AK-PD-01). | 17, 5(2) | Unit + Integration + Reach (T2) |
| AK-IE-02 | **Erst prüfen, dann schließen, dann löschen:** Kann das Deployment nicht löschen (Executor, Tombstone-Salt, abgeleiteter Index nach AK-OS-05a/AK-OS-07), verweigert die Sofortlöschung mit 503, bevor irgendetwas angelegt oder geändert ist. Andernfalls ist das Konto deaktiviert und alle Sitzungen widerrufen, bevor Phase 0 beginnt. Die Bereinigung unverifizierter Konten lässt ein inzwischen verifiziertes Konto unberührt. | 17, 32 | Unit + Integration |
| AK-IE-03 | **Ein Lauf pro Konto:** Von Admin-Löschung, Bereinigung und täglichem Lauf löscht höchstens einer dasselbe Konto (atomarer Claim; der Sofortauftrag trägt einen gesalzenen, deterministischen Schlüssel, der nicht mit dem Audit-Tombstone verknüpfbar ist). Ein zweiter Aufruf, während ein Lauf den Auftrag hält, wird mit 409 abgewiesen — bei der asynchronen Admin-Löschung (#1949) **bevor** das Konto angefasst wird; ein wiederholter Aufruf eines offenen Auftrags stößt ihn erneut an und antwortet wieder `202`, ein zweiter Auftrag entsteht nie. | 17, 32 | Unit + Integration |
| AK-IE-09 <!-- #1992 --> | **Die Bereinigung trifft nur nie bestätigte Konten und schweigt nicht:** `cleanup_unverified_accounts` wählt ein Konto nicht aus (und `erase_account_now(origin="unverified_cleanup")` löscht es nicht), dessen `email_verified` ein Administrator gesenkt hat (`email_verified_lowered_at`); die Senkung von `email_verified` und `is_active` durch `PATCH /admin/platform/users/{key}` verlangt das Step-up des Administrators (kein API-Schlüssel), weil sie zur Löschung bzw. Sperre eines fremden Kontos führen kann. Die Bereinigung benachrichtigt die anderen Mitglieder eines persönlichen Mandanten (Anzahl 0 und kein Versand ohne Mitglieder). | 17, 32 | Unit + Integration |
<!-- /Quelle: #1776 (#1767 GDPR-004, SEC-003) -->
<!-- Quelle: #1813, #1814 (REQ-023 §3.9) -->
| AK-IE-04 | **Keine Kontolöschung ohne Step-up:** `POST /privacy/erasure`, `DELETE /users/me` und `DELETE /admin/platform/users/{key}` löschen nichts und schreiben keinen Löschauftrag, solange der Body die E-Mail des Zielkontos nicht zurücktippt (422), das Passwort der handelnden Person bei lokalem Konto fehlt oder falsch ist (401), die Anfrage mit einem API-Key authentifiziert ist oder von einem Service Account kommt (403), die Installation im Light-Modus läuft (403 — jede Anfrage ist dort das eine Systemkonto) oder der Step-up gesperrt ist (429). `DELETE /users/me` eröffnet denselben Art.-17-Auftrag wie `POST /privacy/erasure`, nie nur einen Tombstone. | 17, 32 | Unit (Route) |
| AK-IE-05 | **Admin-Löschung mit Nachweis der Bestätigung:** Die Plattform-Admin-Löschung prüft die Admin-Mitgliedschaft im Service erneut, verweigert das eigene Konto (403) und verlangt das Passwort des **Admins**; der Löschauftrag hält `step_up` und `requested_by_subject` (gesalzene Referenz, nie der Kontoschlüssel). | 17, 5(2) | Unit (Route) |
<!-- /Quelle: #1813, #1814 (REQ-023 §3.9) -->
<!-- Quelle: #1825 (GDPR-04, SEC-001, SEC-003), Betreiberentscheidungen Q-E6/Q-E7 -->
| AK-IE-06 | **Einladungen werden beim Löschantrag sofort widerrufen (Q-E6, #1825):** `request_erasure` und `erase_account_now` widerrufen bei Antragstellung — nicht erst beim Hard-Delete — jede offene Einladung (E-Mail- und Link-Einladung) in jeden persönlichen Mandanten der Person. Ein Beitritt über eine solche Einladung ist danach nicht mehr möglich, auch während der 90-Tage-Gnadenfrist (R-01). **Implementiert (v1.20):** `TenantService.revoke_invitations_into_personal_tenants_of` setzt in einer Anweisung je persönlichem Mandanten (`revoke_pending_for_tenant`) jede `pending`-Einladung auf `revoked`; beide Einstiege rufen sie nach dem Schließen des Kontos auf, und `erase_personal_tenant_of` wiederholt sie als Rückfalllösung unmittelbar vor der Mitgliederprüfung (eine während der Gnadenfrist von einem anderen Verwaltungsmitglied erzeugte Einladung wird dort erfasst). `accept_invitation` lehnt eine widerrufene Einladung über den Token-Pfad ab („Invitation is no longer pending"); der Übergang `pending → accepted` ist ein bedingter Schreibvorgang, sodass ein Widerruf, der zwischen Statusprüfung und Mitgliedschaftsanlage eintrifft, gewinnt und die Mitgliedschaft zurückgenommen wird. Ein erneuter Löschantrag („bereits in Bearbeitung") widerruft erneut. Einladungen in organisatorische Mandanten der Person bleiben unberührt. **Seit v1.28 (#1924):** Auch eine Einladung, die erst **während** der Gnadenfrist entstünde (ein Mitglied mit dem Verwaltungs-Scope kann sie anlegen) oder deren Widerruf misslang, ist wirkungslos: `create_email_invitation`, `create_link_invitation` und `accept_invitation` verweigern sie mit 403, solange der Eigentümer des persönlichen Mandanten einen offenen Löschauftrag hat (`TenantService._refuse_invitation_while_owner_erasing`, ein Prädikat für beide Einladungsarten und beide Einstiege). | 17 | Unit + Integration |
| AK-IE-08 | **Benachrichtigung der Mitglieder ist dauerhaft (#1960):** `ErasureRequest` trägt `members_notified_at`, `members_notified_count`, `members_notice_failures` und `members_notice_first_attempt_at`. `retention.execute_scheduled_erasures` stellt vor der Auswahl der fälligen Aufträge jede nicht versandte Benachrichtigung eines offenen Selbstbedienungs-Auftrags (`scheduled`, `partially_completed`, `in_progress`) zu — fällig oder noch in der Karenz. Kann der Lauf die offenen Aufträge nicht listen, hält er einen nie benachrichtigten Auftrag eine Wartezeit lang zurück und protokolliert das, statt ihn unbemerkt zu löschen oder ewig zu halten. Ein Auftrag ohne Vermerk wird frühestens `RETENTION_ERASURE_MEMBER_NOTICE_DAYS` (Standard 7, Obergrenze 7) Tage nach der Benachrichtigung gelöscht; ein beim Antrag benachrichtigter Auftrag wird nicht verzögert. Eine ganze Wartezeit lang unzustellbare Benachrichtigung hält die Löschung nicht auf (`personal_tenant_erasure_notice_given_up`). Ein Versandfehler wird ohne Adresse protokolliert und am Auftrag gezählt. Die Sofortlöschung durch einen Administrator wartet nie. Test über den echten Lauf mit einem Auftrag ohne Vermerk: `test_erasure_notice_durability.py`. | 17, 32 | Unit |
| AK-IE-07 | **Erneute Mitgliederprüfung unmittelbar vor der Löschung (Q-E7, #1825 SEC-003):** Die Mitgliederzahl eines persönlichen Mandanten wird unmittelbar nach dem atomaren Claim des Löschlaufs (AK-IE-03) und unmittelbar vor der Ausführung der Mandantenlöschung erneut geprüft. Ist trotz AK-IE-06 zwischen Antragstellung und Löschung ein neues aktives Mitglied beigetreten (Restfenster), wird die Erasure-together-Regel (§3.1.3, Q-E1) **nicht** angewendet: Der Mandant bleibt erhalten, nur der Eigentümerverweis der Person wird anonymisiert (Fallback auf das Verhalten vor #1824). **Implementiert (v1.20, #1825; Erasure-together v1.24, #1824):** Die zweite Prüfung existiert — `erase_personal_tenant_of` liest die aktiven Mitglieder einmal vor dem Einfügen des `tenant_erasure_records`-Eintrags (der Freeze, auf den `_refuse_while_erasing` prüft) und ein zweites Mal unmittelbar danach, vor Claim und Mitgliederdeaktivierung; findet die zweite Lesung ein Mitglied, das die erste nicht kannte, wird der noch nie beanspruchte Eintrag bedingt entfernt (`delete_unclaimed`) und der Mandant erhalten. Ein Eintrag, den ein abgebrochener Lauf ungeclaimt hinterließ, wird beim nächsten Versuch ebenso erneut geprüft; der tägliche Mandanten-Lauf (`resume_tenant_erasures`) überspringt einen solchen Eintrag und überlässt ihn dem Wiederholungsversuch der Kontolöschung. `delete_unclaimed` entfernt nur Einträge mit `origin: account_erasure`. Gegenstück auf der Beitrittsseite: `accept_invitation` und `admin_add_membership` prüfen den Freeze nach dem Einfügen der Mitgliedschaft erneut und nehmen sie zurück, wenn inzwischen ein Eintrag existiert (403, die Einladung bleibt `pending`). **Seit v1.24 (#1824) ist die Erasure-together-Regel umgesetzt:** Die erste Lesung entscheidet nichts mehr, sie hält nur fest, wer schon Mitglied ist (`known_members`); die zweite Lesung erhält den Mandanten nur für ein Mitglied, das in der ersten noch nicht stand (`retained_late_joiner`). Zusätzlich gilt als spät, wessen Mitgliedschaft (`joined_at`) nach dem `requested_at` des **Löschauftrags** begann — ein während der Karenzzeit eingeladenes oder von einem Administrator hinzugefügtes Mitglied, an das die Benachrichtigung nie ging (Review #1824 SEC-001); ein nicht lesbares oder fehlendes `joined_at` macht auch dort nicht spät. Ein von einem früheren Lauf unbeanspruchter Eintrag hat keine erste Lesung zum Vergleich; dort gilt als spät, wessen Mitgliedschaft (`joined_at`, als Zeitpunkt verglichen) nicht vor dem `requested_at` des Eintrags begann ; ein nicht gespeicherter Beginn macht nicht spät (jeder Anlegeweg setzt `joined_at`, nur Seed-Mitgliedschaften haben keinen). **Kein Restfenster (v1.28, #1924):** Fällt die zweite Lesung mit einem Beitritt zusammen (Beitritt zwischen Einfügen des Eintrags und zweiter Lesung, dessen Nachprüfung den Eintrag noch sieht), entscheidet genau eine Seite. Die Rücknahme des Beitritts ist atomar gegen die Rücknahme des Eintrags (`IMembershipRepository.delete_while_tenant_frozen`: ein Statement liest und beschreibt den Löschauftrag und entfernt die Mitgliedschaft; ist der Eintrag zurückgenommen oder abgeschlossen, bleibt die Mitgliedschaft bestehen; gegen einen bereits beanspruchten Eintrag — die Löschung ist dann beschlossen — entfernt das Statement die Mitgliedschaft, ohne den Eintrag zu beschreiben, weil ein Schreibzugriff mit dem Heartbeat des laufenden Laufs kollidieren und als verlorener Claim gelten würde). `erase_personal_tenant_of` nimmt den Eintrag daher **vor** der Entscheidung zurück und liest die Mitglieder erneut: steht der Beitretende noch, bleibt der Mandant für ihn erhalten (`retained_late_joiner`); ist er zurückgenommen, wird der Mandant erneut eingefroren und gelöscht. Ein anhaltender Konflikt (dreimal) beendet den Lauf mit `WriteConflictError`; der offene Eintrag bleibt für die Wiederholung bestehen. Es gibt keinen Ausgang „Mandant erhalten, niemand aktiv“. | 17, 32 | Unit + Integration |
<!-- /Quelle: #1825 -->
<!-- Quelle: #1793-1 (GDPR-004), Betreiberentscheidung Q-T1 -->
| AK-DE-02 | **Auskunft enthält den eigenen persönlichen Mandanten (#2135, MT-039):** Das Bundle einer Person mit persönlichem Garten enthält dessen Standorte mit `gps_coordinates`, Beete, Stellplätze, Pflanzen, Pflanzdurchläufe, Aufgaben, Tagebuch und Anhang-Metadaten; ein Standort eines Organisationsmandanten, in dem sie Mitglied ist, und der persönliche Garten einer anderen Person erscheinen nicht; keine Garten-Quelle liefert einen fremden Kontoschlüssel. **Umgesetzt:** `tests/integration/test_privacy_export_personal_tenant.py` (echte ArangoDB, inklusive `locations`/`slots` ohne eigenes `tenant_key`), `tests/unit/domain/services/test_privacy_export_personal_tenant.py`, `tests/unit/domain/engines/test_export_personal_tenant_manifest.py`; Prüfer R2 (`scripts/check_privacy_inventory.py`) in beiden Richtungen grün. | 15 | Unit + Integration |
| AK-DE-01 | **Auskunft erreicht pseudonymisierte Aufbewahrungszeilen eines gelöschten Mandanten (Q-T1, #1793):** Ist eine Person weiterhin aktives Konto, umfasst ihr Datenexport auch R-16/R-17/R-18-Zeilen, deren Mandant zwischenzeitlich gelöscht wurde und die deshalb den Tombstone-Hash statt eines Kontoschlüssels tragen (§3.1.2 Punkt 6). **Umgesetzt** (#1793): `tests/integration/test_privacy_export_tombstone.py` erzeugt den Zustand über die echte Mandantenlöschung und liest das ausgelieferte Bundle zurück. | 15 | Unit + Integration |
<!-- /Quelle: #1793-1 -->
<!-- Quelle: #1841 (REQ-023 §3.9) -->
| AK-EC-01 | **Keine E-Mail-Änderung ohne Step-up:** `POST /privacy/email-change` prüft den Step-up nach REQ-023 §3.9, bevor die neue Adresse **nachgeschlagen** wird (ob sie bereits vergeben ist): das aktuelle Passwort bei lokalem Konto (401 sonst); ohne lokales Passwort ein `step_up_token` aus einer frischen Anmeldung beim verknüpften OIDC-Provider (401 `STEP_UP_REAUTH_REQUIRED` ohne, wenn ein solcher Anbieter verknüpft ist), sonst — nur bei ausschließlich GitHub/Apple — der per E-Mail zugeschickte Einmalcode (401 `STEP_UP_CODE_REQUIRED` ohne, #1815); 403 für eine API-Key-Anfrage oder ein Dienstkonto, 429 `STEP_UP_LOCKED` im selben Budget wie jeder andere Step-up des Kontos. Nur die zustandslosen Prüfungen (neue Adresse identisch mit der eigenen, reservierte Tombstone-Domain — beide 422) laufen davor und verbrauchen deshalb keinen Code, keine frische Anmeldung und keinen gedrosselten Versuch (/code-review of #1862). Die aktuelle Adresse wird in beiden Zweigen (freie und bereits vergebene Adresse) über die Beantragung benachrichtigt. | 16 | Unit (Route) |
| AK-EC-02 | **Ein Passwort-Reset, eine Passwortänderung und "alle Sitzungen abmelden" widerrufen eine offene E-Mail-Änderung:** Alle drei Vorgänge setzen jede `pending` `EmailChangeRequest` des Kontos auf `cancelled`; eine Bestätigung mit deren Token antwortet danach mit demselben Fehler wie ein abgelaufener Token. Ohne dies bliebe eine im Postfach der neuen Adresse gelesene Bestätigungs-Mail wirksam, selbst nachdem die Eigentümerin ihr Konto durch den Reset zurückgeholt hat. | 16 | Unit + Integration |
| AK-EC-03 | **Eigene Mail, eigene Seite, eigenes Formular (#1848):** Die Mail an die neue Adresse verlinkt `{frontend}/email-change/{token}`; die Seite bestätigt über `POST /privacy/email-change/confirm`. Die Kontoeinstellungen bieten die E-Mail-Änderung mit Step-up an (REQ-023 §3.9) und zeigen `STEP_UP_LOCKED` an. Die Mail an eine noch nicht bestätigte Adresse (Registrierung, E-Mail-Änderung) enthält keinen vom Anfragenden gewählten Text; jeder andere Platzhalter einer HTML-Mail wird escaped (#1856). | 16 | Unit + Vitest |
| AK-EC-04 | **Rückgängig durch die vorherige Adresse (#1848):** Die Info-Mail an die vorherige Adresse enthält einen einmaligen Link, gültig `RETENTION_EMAIL_CHANGE_REVERT_DAYS` (Standard 7 Tage). `POST /privacy/email-change/revert` stellt die vorherige Adresse als bestätigt wieder her, sofern sie noch frei ist (sonst 422), und nimmt zurück, was eine Übernahme über die Änderung hinterlassen haben kann: alle Sitzungen, einen offenen Passwort-Reset-Token, offene E-Mail-Änderungen, seit der Beantragung verknüpfte föderierte Anmeldewege (ein automatisch verknüpftes Google-/OIDC-Konto meldet sonst per `sub` weiter an) und seit der Beantragung erstellte API-Keys. Ältere Anmeldewege und Keys bleiben. Später bestätigte Änderungen desselben Kontos werden `superseded`: Ihr Rückgängig-Link kann die Rücknahme nicht wieder aufheben. Frühere Fenster bleiben offen. Die Bestätigung und die Rücknahme setzen den Status atomar (compare-and-set) und schreiben die Adresse nur, solange das Konto noch die gelesene Adresse trägt (compare-and-set auf `users.email`); wer ein solches Rennen verliert, gibt seinen Anspruch zurück — der Token bleibt gültig (409, erneut versuchen). Solange das Fenster offen ist, ist die vorherige Adresse **reserviert**: eine Registrierung (lokal oder per OIDC) und die E-Mail-Änderung eines anderen Kontos auf diese Adresse werden wie bei einer vergebenen Adresse behandelt. Die Adresse, die das Konto dabei verlässt, erhält eine Nachricht mit festem Text. Ein unbekannter, bereits verwendeter oder abgelaufener Token antwortet 401, ein zur Löschung geschlossenes Konto 409 `ACCOUNT_BEING_ERASED`; in beiden Fällen bleibt der Token unverbraucht. `previous_email` und der Token-Hash werden mit dem Ablauf des Fensters gelöscht (NFR-011 R-07a). **Restrisiko:** Wer die vorherige Adresse liest — etwa weil sie der Grund für den Wechsel war —, kann das Konto innerhalb des Fensters zurückholen; die neue Adresse wird darüber informiert. | 16 | Unit + Integration |
<!-- /Quelle: #1841 (REQ-023 §3.9) -->
**Bekannte Lücke (#1841, #1848).** Es gibt noch keine eigene Oberfläche für die E-Mail-Änderung — die Kontoeinstellungen zeigen die Adresse nur schreibgeschützt an, §4.2 sieht dafür keinen Tab vor — und keinen Rückgängig-Link nach einer Bestätigung.

<!-- Quelle: REQ-050 §7.4 -->
| AK-DA-01 | **Tagebuch-Anonymisierung:** Nach Abschluss eines Erasure-Requests sind in `plant_diary_entries` die Felder `created_by`, `analysis_requested_by` und `analysis_claimed_by` mit dem Wert `user_key` auf `_anonymized` gesetzt. Das Eintragsdokument selbst — Freitext, Tags, Messwerte, `photo_refs` und ein vorhandenes `analysis`-Ergebnis — bleibt vollstaendig erhalten. Dies schliesst die Luecke, dass bislang nur die **Anhaenge** (AK-OS-02), nicht aber das Eintragsdokument geregelt waren. | 17 | Integration |
| AK-DA-02 | **Auskunft umfasst Tagebuch:** Der Datenexport nach Art. 15/20 enthaelt die Tagebuch-Eintraege des Nutzers samt vorhandener KI-Analyse-Ergebnisse (REQ-050). | 15/20 | Integration |
| AK-DA-03 | **Einwilligung `diary_ai_analysis`:** Ohne erteilte Einwilligung lehnt das Markieren eines Tagebuch-Eintrags zur KI-Analyse ab; ein Widerruf verhindert neue Markierungen und laesst bestehende Ergebnisse unberuehrt. Im Light-Modus (REQ-027) entfaellt die Pruefung, weil dort kein Consent erteilt werden kann (REQ-050 §7.5). | 6(1)(a) | Integration |
| AK-DA-04 | **Nicht implementiert** (Stand #1663): Die Collection `plant_diary_analyses` existiert im Code noch nicht, es gibt also nichts zu anonymisieren und keine Regel dafür. Sobald REQ-051 §5 sie anlegt, gilt: **Archiv-Anonymisierung:** Nach Abschluss eines Erasure-Requests sind in `plant_diary_analyses` die Felder `requested_by` und `claimed_by` mit dem Wert `user_key` auf `_anonymized` gesetzt. Der Lauf selbst — Zusammenfassung, Befunde, Empfehlungen, Herkunftsangabe — bleibt vollstaendig erhalten (REQ-051 §5.4, §11). | 17 | Integration |
| AK-DA-05 | **Nicht implementiert** (Stand #1663, dieselbe Ursache wie AK-DA-04). Sobald REQ-051 §5 umgesetzt ist, gilt: **Auskunft umfasst das Analyse-Archiv:** Der Datenexport nach Art. 15/20 enthaelt die archivierten Analyselaeufe, nicht nur das juengste Ergebnis am Eintrag (REQ-051 §11). | 15/20 | Integration |
<!-- /Quelle: REQ-050 §7.4 -->

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | PrivacySettingsPage zeigt alle 4 Tabs korrekt an | E2E |
| FK-02 | Einwilligungs-Toggles für optionale Zwecke funktionieren | E2E |
| FK-03 | Erforderliche Einwilligungen sind als nicht-änderbar dargestellt | E2E |
| FK-04 | Export-Button ist deaktiviert während ein Export läuft | E2E |
| FK-05 | Lösch-Dialog erfordert Passwort-Bestätigung und Checkbox | E2E |
| FK-07 <!-- #1961 --> | Der Lösch-Dialog der Administrator-Seite (`AdminEditUserPage`) zeigt vor der Bestätigung dieselbe Vorschau für das **Zielkonto** (`GET /admin/platform/users/{key}/erasure-preview`, nur Plattform-Admin, nur Name des Mandanten und Anzahl) und nennt, dass die anderen Mitglieder keine Frist erhalten; eine nicht ladbare Vorschau sagt das ausdrücklich — Unit-/Komponententest `AdminEditUserErasurePreview.test.tsx`, Backend `test_admin_platform_user_erasure_preview.py` | Unit |
| FK-06 <!-- Q-T6, #1824 --> | Lösch-Dialog zeigt vor der Bestätigung je betroffenem persönlichen Mandanten eine Vorschau-Zeile mit Name und Anzahl weiterer Mitglieder — **implementiert (v1.24)**, Unit-/Komponententest `ErasurePreview.test.tsx`; E2E-Testfall noch offen | E2E |
| FK-08 <!-- #2134 --> | Lösch-Dialog (Selbstbedienung und Administrator-Seite) nennt vor der Bestätigung je Organisation, die die Löschung verändert, entweder „letzte Person mit Verwaltungsrecht — die dienstälteste Leitung übernimmt“ oder „niemand mehr, der verwalten kann — wird nach der Frist gelöscht“ (`organizations[]` der Vorschau); unberührte Organisationen erscheinen nicht — **implementiert (v1.32)** | Unit + Vitest |

---

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| REQ-023 v1.2 | User-Modell, AuthService, TokenEngine, E-Mail-Verifikation |
| REQ-024 v1.1 | Tenant-Mitgliedschaften (werden bei Löschung entfernt) |
| NFR-011 | Retention-Fristen (R-01, R-04, R-05, R-06, R-07, R-16, R-17, R-18) |
| NFR-006 | API-Fehlerbehandlung (403, 423, 422 Fehlercodes) |

### Wird benötigt von:

| REQ | Bezug |
|-----|-------|
| REQ-011 | Consent-Prüfung für externe Stammdatenanreicherung |
| REQ-007 | Anonymisierung von Harvester-Referenzen bei Löschung |
| REQ-010 | Anonymisierung von Inspector-Referenzen bei Löschung |
| REQ-006 | Anonymisierung von Task-assigned_to bei Löschung |

### Neue Collections im Named Graph `kamerplanter_graph`:

| Typ | Collection | Zweck |
|-----|-----------|-------|
| Document | `data_export_requests` | Art. 15/20 Export-Aufträge |
| Document | `consent_records` | Einwilligungen pro Zweck |
| Document | `processing_restrictions` | Art. 18 Verarbeitungssperren |
| Document | `erasure_requests` | Art. 17 Löschaufträge |
| Document | `email_change_requests` | Art. 16 E-Mail-Änderungen |
| Edge | `requested_export` | users → data_export_requests |
| Edge | `has_consent` | users → consent_records |
| Edge | `has_restriction` | users → processing_restrictions |
| Edge | `requested_erasure` | users → erasure_requests |
| Edge | `requested_email_change` | users → email_change_requests |

---

## 8. Scope-Abgrenzung

**In Scope:**
- Art. 15 Auskunftsrecht (Datenexport als JSON)
- Art. 16 Berichtigungsrecht (E-Mail-Änderung mit Re-Verifikation)
- Art. 17 Recht auf Löschung (Soft-Delete + Hard-Delete nach Retention-Frist)
- Art. 18 Recht auf Einschränkung (zweckbezogene Verarbeitungssperren)
- Art. 20 Datenportabilität (maschinenlesbarer JSON-Export)
- Art. 21 Widerspruchsrecht (zweckbezogener Opt-out)
- Consent-Tracking (nachweisbare Einwilligungen)
- Privacy-Settings-Seite (Frontend)

**Nicht in Scope (bewusst ausgeklammert):**
- Art. 13/14 Informationspflichten: Datenschutzerklärung als statisches Dokument, nicht als Feature
- Art. 30 Verzeichnis von Verarbeitungstätigkeiten: Organisationsdokument, nicht Software-Feature
- Art. 35 Datenschutz-Folgenabschätzung (DSFA): Separates Bewertungsdokument (siehe NFR-001 §6.7)
- Art. 28 Auftragsverarbeitungsverträge (AVV): Vertragliche, nicht technische Anforderung
- DSGVO-Export pro Tenant (REQ-024 Out-of-Scope, zukünftige Erweiterung)

---

## 9. Datenschutz-Bewertung externer Dienste

<!-- Quelle: IT-Security-Review SEC-H-008 -->

Kamerplanter kommuniziert mit mehreren externen Diensten. Für jeden Dienst MUSS eine Datenschutz-Bewertung dokumentiert werden, die die übertragenen Daten, Rechtsgrundlage und Schutzmaßnahmen beschreibt.

| Dienst | Übertragene Daten | Rechtsgrundlage | Schutzmaßnahmen | Consent-pflichtig |
|--------|-------------------|-----------------|-----------------|-------------------|
| **GBIF** (REQ-011) | Artname (Suchanfrage) | Kein Personenbezug (Katalog-Job, vom Plattform-Admin oder Beat ausgelöst) | Keine PII übertragen; Zweck `external_enrichment` entfernt (#2136) | Nein |
| **Perenual** (REQ-011) | Artname (Suchanfrage) | Kein Personenbezug (Katalog-Job, vom Plattform-Admin oder Beat ausgelöst) | Keine PII übertragen; Zweck `external_enrichment` entfernt (#2136) | Nein |
| **HaveIBeenPwned** (REQ-023) | — (nicht implementiert) | — | Zweck `hibp_check` bis zur Umsetzung entfernt (#2136); kommt mit dem Adapter zurück | — |
| **Sentry** (NFR-001 §8.3) | Backend: Stack-Traces, Routenmuster, User-Agent (keine Bodies, keine IP); mit Einwilligung zusätzlich Konto-/Mandanten-Pseudonym | Ereignis: berechtigtes Interesse Art. 6(1)(f) (Betriebsstabilität) — **#2136, rechtlich zu bestätigen**; Zuordnung (`user`-Block): Art. 6(1)(a) | PII-Scrubbing, EU-Hosting oder AVV; `error_tracking`-Consent für die Zuordnung | Nur die Zuordnung |
| **DWD / OpenWeatherMap / Open-Meteo** (REQ-005) | GPS-Koordinaten des Standorts (Site.latitude/longitude) | Art. 6(1)(b) Vertragserfüllung | Koordinaten auf 2 Dezimalstellen gerundet (~1 km Genauigkeit); kein Personenbezug | Nein |
| **InvenTree** (REQ-016) | Produktreferenzen, Bestandsänderungen | Art. 6(1)(b) Vertragserfüllung | Self-Hosted; kein externer Dienst im Regelfall | Nein |
| **OAuth-Provider** (REQ-023) | E-Mail, Name (vom Provider empfangen) | Art. 6(1)(b) Vertragserfüllung | Nur bei explizitem Nutzer-Login; Daten vom Provider kontrolliert | Nein (funktional) |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| DP-001 | Externe API-Aufrufe DÜRFEN NUR nach Prüfung der Consent-Pflicht erfolgen. Consent-pflichtige Dienste MÜSSEN `ConsentGuard.require_consent()` (bzw. `has_consent()`) in der Fachlogik verwenden (§3.6). | MUSS |
| DP-002 | GPS-Koordinaten MÜSSEN vor Übertragung an Wetter-APIs auf maximal 2 Dezimalstellen gerundet werden. | MUSS |
| DP-003 | Bei Nutzung von Sentry SaaS MUSS ein AVV nach Art. 28 DSGVO vorliegen (siehe NFR-001 §8.3 SE-004). | MUSS |

---

## 10. TTDSG-Konformität (Cookie-/Speicher-Einwilligung)

<!-- Quelle: IT-Security-Review SEC-M-007 -->

Das Telemediengesetz (TTDSG) §25 unterscheidet zwischen technisch notwendigen und nicht-notwendigen Zugriffen auf die Endeinrichtung des Nutzers (Cookies, localStorage, sessionStorage).

**Klassifikation der Speicherzugriffe in Kamerplanter:**

| Speicherzugriff | Zweck | TTDSG-Kategorie | Einwilligung nötig |
|----------------|-------|-----------------|-------------------|
| `refresh_token` (HttpOnly Cookie) | Authentifizierung | Technisch notwendig (§25 Abs. 2 Nr. 2) | Nein |
| `csrf_token` (Cookie) | CSRF-Schutz | Technisch notwendig | Nein |
| `i18next` (localStorage) | Spracheinstellung | Technisch notwendig | Nein |
| `theme` (localStorage) | Dark/Light-Mode | Technisch notwendig | Nein |
| `redux_state` (sessionStorage) | App-State | Technisch notwendig | Nein |
| Sentry SDK (localStorage, Cookies) | Fehler-Tracking | **Nicht notwendig** | **Ja** (`error_tracking`-Consent) |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| TT-001 | Technisch notwendige Cookies/Storage-Zugriffe DÜRFEN OHNE Einwilligung gesetzt werden. | Info |
| TT-002 | Sentry und alle zukünftigen Tracking-/Analyse-Dienste DÜRFEN Cookies/Storage ERST NACH expliziter Einwilligung nutzen (ConsentEngine `error_tracking`). | MUSS |
| TT-003 | Ein Cookie-/Einwilligungs-Banner ist NICHT erforderlich, solange ausschließlich technisch notwendige Speicherzugriffe erfolgen. Bei Aktivierung von Sentry oder Analytics MUSS ein Einwilligungs-Dialog implementiert werden (UI-NFR-013). | BEDINGT |

---

**Dokumenten-Ende**

**Version**: 1.5
**Status**: Entwurf
**Datum**: 2026-08-04
**Security-Review**: Adressiert SEC-K-001, SEC-K-003, SEC-H-008, SEC-M-005, SEC-M-007
