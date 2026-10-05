# Spezifikation: REQ-024 - Mandantenverwaltung & Gemeinschaftsgärten

```yaml
ID: REQ-024
Titel: Mandantenverwaltung & Gemeinschaftsgärten
Kategorie: Plattform & Kollaboration
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React, TypeScript, MUI
Status: Entwurf
Version: 1.25 (Dienstkonten verwalten: Leitung und Technik, §1a; #2137); 1.24 (Mandanten-Lebenszyklus `status` statt `is_active`, Löschung mit 90 Tagen Gnadenfrist und Abbruch, AK-52 umgesetzt, AK-65; #2123); 1.23 (Mitgliederlimit durchgesetzt, Plattform-Obergrenze `TENANT_MAX_MEMBERS_CEILING`, AK-64; #2133); 1.22 (Deaktivierter Mandant sperrt alle Mitglieder aus, AK-48 umgesetzt; #2105); 1.21 (Mitgliedschafts-Audit, Step-up für das Hinzufügen, adressgebundene E-Mail-Einladung, Zuweisungen enden mit der Mitgliedschaft, atomare Mandantengründung, AK-59 bis AK-63; #2111, #2106, #2115, #2114, #2118); 1.20 (Rollen-Eskalation: keine Selbst-Beförderung, `lead` in `platform` nur durch eine Leitung, AK-58; #2078); 1.19 (Step-up für Rollenwechsel und Entfernen eines Mitglieds, AK-56 umgesetzt und AK-57; #2009, #2032); 1.18 (Mandantenlöschung entfernt auch `is_system`-Zeilen des Mandanten; `v0078`, #2027)
Abhängigkeit: REQ-049 v1.4 (Rollenmodell & verbindliches Vokabular — **Autorität bei Widerspruch**), REQ-023 v1.13 (Service Accounts, Plattform-Admin), NFR-016 (Migrations-Framework — `v0032`)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.25 | 2026-10-05 | **#2137 (MT-041):** Dienstkonten verwaltet nicht mehr die Zusatzberechtigung **Verwaltung**, sondern wer **Leitung** ist **und** **Technik** hält (REQ-049 v1.10 §2.4/§4.2, dort begründet; Entscheidung nach Messung, überstimmbar). Die Matrix-Zeile „Service Accounts verwalten“ und die Achse-2-Tabelle sind angeglichen. Ein Dienstkonto belegt einen Platz des Mitgliederlimits (AK-64) und zählt zusätzlich gegen `TENANT_MAX_SERVICE_ACCOUNTS` (Default 20). `POST /tenants` und die Einladungsannahme weisen ein Dienstkonto ab (403); die Mitgliederverwaltung hebt es nicht zu `lead`. Details REQ-023 §5b.0. |
| 1.24 | 2026-10-05 | **#2123 (MT-027, AK-52 entschieden und umgesetzt, Betreiberentscheidung 2026-10-04, brechend):** Bis v1.22 löschte `DELETE /tenants/{slug}` (und `DELETE /admin/platform/tenants/{key}`) **sofort**: Mitgliedschaften deaktiviert, Celery-Task ausgelöst, kein Rückweg — gemessen in `TenantService.delete_tenant` (Nachweis anlegen → `deactivate_all_for_tenant` → `_dispatch_tenant_erasure`). Neu: (1) **Zustandsmodell** `Tenant.status: active \| suspended \| pending_deletion \| orphaned \| deleted` ersetzt `is_active` (Migration `v0085`: `is_active=false` → `suspended`, offener Löschnachweis → `deleted`, sonst `active`; das Feld `is_active` wird entfernt). `is_active` bleibt in den API-Antworten als **abgeleiteter** Wert (`status == active`) erhalten; jeder Resolver aus #2105 liest ihn, deshalb wird **jeder** Zustand außer `active` für niemanden aufgelöst (dieselbe `403`). (2) **Gnadenfrist** `RETENTION_TENANT_ERASURE_GRACE_DAYS` (Standard **90 Tage** wie bei Konten, Untergrenze 0 für Self-Hosted, Obergrenze 90, NFR-011 R-01b): Die Anfrage plant die Löschung (`202`, `status: scheduled`, `scheduled_for`), setzt den Mandanten auf `pending_deletion` und **lässt die Mitgliedschaften unverändert** — das Einfrieren ist der Zustand, nicht die Mitgliedschaft. Der tägliche Lauf `resume_tenant_erasures` beansprucht den Nachweis erst nach Fristablauf, setzt `deleted`, deaktiviert die Mitgliedschaften und löscht wie bisher (AK-53). Mit Frist 0 bleibt der Sofort-Pfad. (3) **Abbruch** `POST /tenants/{slug}/erasure/cancel` (Leitung **und** Verwaltung aus der gespeicherten Mitgliedschaft, Step-up `tenant_erasure_cancel`, nie per API-Schlüssel) und `POST /admin/platform/tenants/{key}/erasure/cancel` (Plattform-Admin, Step-up): Nachweis wird nur entfernt, solange er `scheduled` ist (atomar gegen den Claim des Laufs), der Mandant ist danach wieder `active` mit allen Mitgliedschaften. (4) **Benachrichtigung** aller aktiven Mitglieder mit dem Datum und dem Hinweis auf den persönlichen Datenexport (Art.-20-Fenster). **Exportfenster (gemessen):** Der persönliche Export (`POST /privacy/export`) ist kontobezogen, nicht mandantenaufgelöst — er erreicht die eigenen Beiträge im Mandanten ohne den Slug-Resolver. Ein `pending_deletion`-Mandant bleibt deshalb für alle gesperrt (`403`-Vertrag von #2105 unverändert); nur die Abbruch-Route ist ausgenommen und begründet in den Guards registriert. (5) Der Admin-Schalter `is_active` bewegt nur zwischen `active` und `suspended`; ein Mandant in `pending_deletion`, `orphaned` oder `deleted` wird darüber nicht reaktiviert (`422`). AK-52 umgesetzt, AK-16/AK-53 nachgeführt, **AK-65** neu (bei der Zusammenführung mit #2133 umnummeriert; AK-64 ist dort das Mitgliederlimit). |
| 1.23 | 2026-10-05 | **#2133 (MT-037, AK-64, brechend):** `max_members` wurde gespeichert und angezeigt, aber von keiner Entscheidung gelesen. Gemessen über die echte Route `POST /tenants/invitations/accept` auf ArangoDB 3.12: ein persönlicher Mandant mit `max_members=1` nahm ein zweites und drittes Mitglied mit `200` auf. **Betreiberentscheidung 2026-10-04:** (1) Eine **Plattform-Obergrenze** `TENANT_MAX_MEMBERS_CEILING` (Setting, Default `50`, mindestens 1); das wirksame Limit eines Mandanten ist `min(max_members, Obergrenze)`. (2) `max_members` ist `int` (kein `null` = unbegrenzt mehr; §2 angeglichen), wird beim Anlegen und bei jeder Änderung höchstens auf die Obergrenze gesetzt (darüber `422`, Detail-Code `max_members_above_ceiling`) — vom Mitglied mit Verwaltung (`PATCH /tenants/{slug}`) wie vom Plattform-Admin (`PATCH /admin/platform/tenants/{key}`); eine Organisation ohne Angabe erhält die Obergrenze. (3) Ein **persönlicher Mandant** wird mit `max_members=1` gegründet; ein weiteres Mitglied nimmt er erst auf, nachdem jemand mit Verwaltung das Limit angehoben hat (REQ-049 AK-19 angepasst). (4) Jeder Weg, der ein Konto einem **bestehenden** Mandanten hinzufügt — Einladungsannahme und `admin_add_membership` —, läuft durch die eine Einfügestelle `_create_membership_unless_erasing`; sie zählt die aktiven Mitgliedschaften (`is_active != false`) vor dem Einfügen und noch einmal danach (zwei gleichzeitige Beitritte können beide den letzten Platz sehen; der überzählige nimmt sich zurück). Voll → `422 MEMBER_LIMIT_REACHED`, nichts geschrieben: die Einladung bleibt offen, der Plattform-Admin wird nicht erst nach dem Step-up gefragt. (5) Ein Mandant, der heute **mehr** Mitglieder hat als sein Limit (vor dieser Version beigetreten oder nach einer Absenkung), behält alle; nur der nächste Beitritt wird verweigert. Keine Migration: gemessen kann ein Mandanten-Dokument `max_members` nur im Light-Modus-Mandanten auslassen (liest als `1`, dort gibt es keine Beitritte), `null` schreibt kein Pfad (`exclude_none`), und Werte über der Obergrenze (Plattform-Mandant `999`) werden zur Laufzeit gekappt. Die Ableitung des Limits aus einem Tarif (MT-049, #2142) ist **nicht** Teil dieser Version. Guard: `test_membership_mutations_write_the_security_audit.py` (Abschnitt #2133) hält, dass eine Mitgliedschaft nur in der begrenzten Einfügestelle entsteht (Gründung klassifiziert: der Gründer nimmt den ersten Platz). |
| 1.22 | 2026-10-05 | **#2105 (MT-007, AK-48 umgesetzt):** `PATCH /admin/platform/tenants/{key}` mit `is_active=false` (Step-up, AK-56) entfernte den Mandanten nur aus `GET /tenants`; der Resolver `_membership_for_slug` las `membership.is_active`, nie `tenant.is_active`. Gemessen über die echten Routen auf ArangoDB 3.12: `GET /tenants/{slug}` und ein globaler Katalog mit `X-Active-Tenant` antworteten einem Mitglied des deaktivierten Mandanten mit `200`, der Fallback ohne Header las weiter den deaktivierten persönlichen Mandanten. Neu: (1) Pfad `/t/{slug}/` und Header `X-Active-Tenant` verweigern einen deaktivierten Mandanten mit **derselben** `403` wie einen unbekannten Slug (kein Existenz-Orakel, kein neuer Statuscode); (2) ohne Header fällt ein deaktivierter persönlicher Mandant auf den globalen Katalog zurück (`""`, niedrigste Rolle), nie auf einen Fehler; (3) MCP war bereits dicht (`list_my_tenants` filtert `tenant.is_active`; `list_tenants` ohne ihn, Werkzeugaufruf `not_found`) und ist jetzt durch einen Test gehalten. Mitgliedschaften bleiben unverändert gespeichert; Reaktivieren stellt den Zugriff mit derselben Rolle wieder her. **Plattform-Admins** verwalten einen deaktivierten Mandanten weiter über `/admin/platform/…` (Zugriff per Schlüssel hinter `require_platform_admin`, nicht über den Slug-Resolver); der Mandant `platform` kann nicht deaktiviert werden (#1021). Bewusst **nicht** Teil dieser Version (Betreiberentscheidung: minimale Prüfung): `409` für Einladungsannahme und Admin-Hinzufügen in einen deaktivierten Mandanten, `401` für einen API-Schlüssel, dessen `tenant_scope` einen deaktivierten Mandanten nennt (er erhält dort die `403` des Resolvers). Guard `test_tenant_lookups_read_is_active.py`: jede Mandanten-Abfrage liest `is_active` auf der geladenen Variablen oder ist begründet klassifiziert. |
| 1.21 | 2026-10-04 | **Mitgliedschafts-Bündel (#2111, #2106, #2115, #2114, #2118):** (1) **#2111, AK-60:** Jede Änderung einer Mitgliedschaft — Hinzufügen, Rollen- oder Scope-Änderung, Entfernen, Austritt, Annahme einer Einladung, Gründung eines Mandanten — schreibt eine Zeile in das persistente Sicherheits-Audit `security_audit_log` (wer, wessen Mitgliedschaft, Mandant, alte/neue Rolle und Scopes, Anfrage-ID, Zeit; nur Konto- und Mandantenschlüssel, kein Freitext), Aufbewahrung 730 Tage (NFR-011 R-38, Migration `v0082`), Lesezugriff `GET /admin/platform/security-audit`; Guard `test_membership_mutations_write_the_security_audit.py`. (2) **#2106, AK-59:** `POST /admin/platform/tenants/{key}/members` und `…/users/{key}/memberships` verlangen den Step-up des Administrators (Aktion `admin_membership_add`, Ziel `<tenant_key>|<user_key>`); ein Plattform-Admin fügt sich nicht selbst dem Mandanten `platform` hinzu. Gemessen auf ArangoDB 3.12: vorher `201` ohne jeden Nachweis, auch für `lead` in `platform`. (3) **#2115, AK-61 (brechend):** Eine E-Mail-Einladung nimmt nur das Konto an, das die eingeladene Adresse trägt **und** bestätigt hat (`address_proven`); sonst 403, nichts geschrieben. Gemessen: vorher `200` für jedes angemeldete Konto mit dem Token. (4) **#2114, AK-62:** Ein endendes Mitgliedsverhältnis nimmt dem Ex-Mitglied die Aufgabenzuweisungen des Mandanten (`tasks.assigned_to_user_key`), und die Pflege-Erinnerungen gehen nur an aktive Mitglieder; die Tageszusammenfassung gilt je (Nutzer, Mandant). Gemessen: vorher blieb der Zuständige und wurde weiter benachrichtigt. (5) **#2118, AK-63:** Mandant, Gründer-Mitgliedschaft, beide Kanten und Audit-Zeile entstehen in **einer** Transaktion; eine fehlgeschlagene Registrierung nimmt das Konto zurück. Gemessen: vorher blieben Mandant, Mitgliedschaft und eine Kante zurück. |
| 1.20 | 2026-10-04 | **#2078 (AK-58):** `PATCH /tenants/platform/members/{eigene membership_key}/role` mit dem eigenen Passwort als Step-up machte ein `management`-Mitglied ohne Leitung im Mandanten `platform` zur `lead` (gemessen über die echte Route auf ArangoDB 3.12: `200`; `is_platform_admin` gilt dann für das Konto) — der Step-up (#2032) beweist, wer fragt, nicht, dass die Rolle zusteht. Die Einladungsrouten (`POST /tenants/{slug}/invitations/email` und `/link`) mit `role: lead` waren dieselbe Lücke (gemessen: `201`). Neu, im Dienst (`TenantService._refuse_role_grant`, Regel in `MembershipEngine.role_grant_refusal`), `403` **vor** dem Step-up und ohne Schreibzugriff: (1) niemand **erhöht die Rolle der eigenen Mitgliedschaft** über die Mandanten-Routen (Herabstufen bleibt erlaubt); (2) **`lead` im Mandanten `platform`** (die Plattform-Rolle) vergibt — per Rollenwechsel wie per Einladung — nur, wer dort selbst aktiver `lead` ist. **Vorschlag, Betreiberprüfung offen:** In allen anderen Mandanten bleibt es bei REQ-049 §2.4 (keine Rangdecke: die Verwaltung darf eine Leitung ernennen, sonst bekäme ein Mandant ohne Leitung nie wieder eine); die Forderung „nie eine Rolle über der eigenen vergeben“ aus dem Issue würde die Schriftführerin (Beobachter + Verwaltung) daran hindern und ist deshalb nicht umgesetzt. Die Plattform-Admin-Routen sind davon nicht berührt (Plattform-Admin = Leitung in `platform`). |
| 1.19 | 2026-10-04 | **#2032 (Betreiberentscheidung, AK-56/AK-57):** Step-up auf **allen vier** weiteren Routen, die ein Mitglied aus einem Mandanten aussperren oder ihm die Rolle nehmen: `PATCH /admin/platform/tenants/{tenant_key}/members/{membership_key}/role`, `PATCH /admin/platform/users/{user_key}/memberships/{membership_key}/role`, `PATCH /tenants/{slug}/members/{membership_key}/role` und `DELETE /tenants/{slug}/members/{membership_key}`. `DELETE /tenants/{slug}/assignments/{key}` bekommt **keinen** Step-up: Eine Parzellen-Zuordnung sperrt kein Mitglied aus dem Mandanten aus. Gemessen über die echten Routen vor der Änderung: alle vier antworteten ohne Step-up mit `200` — die letzte Leitung wurde zu `viewer` herabgestuft bzw. entfernt. Der Step-up (`StepUpVerifier`, REQ-023 §3.9) ist an die Mitgliedschaft gebunden (#1884); ein unverändert erneut gesendeter Rollenwert braucht keinen und schreibt nichts. AK-56 ist seit #2009 umgesetzt. |
| 1.18 | 2026-10-03 | **#2027 Nachtrag:** Die Mandantenlöschung behielt in `activities` und `workflow_templates` jede Zeile des Mandanten mit `is_system: true` (`keep_when`), in der Annahme, es sei ein von `v0004` gestempelter Seed. Ein Seed ist global (`tenant_key == ""`) und wird von der Löschung nie ausgewählt; die Ausnahme traf deshalb nur Zeilen des Mandanten, etwa ein über `POST /t/{slug}/tasks/workflows` mit `is_system` angelegtes Template, und diese überlebten die Löschung (gemessen auf ArangoDB 3.12). Die Ausnahme ist entfernt: Jede Zeile mit dem Schlüssel des Mandanten wird gelöscht, `is_system` oder nicht. Migration `v0078` setzt `is_system` auf allen Zeilen mit nicht-leerem `tenant_key` in beiden Collections auf `false` (der `tenant_key` bleibt; idempotent). Kein Request-Body einer nicht Plattform-Admin-geschützten Schreibroute nimmt `is_system` an (Guard über alle Schreibrouten). |
| 1.17 | 2026-10-03 | **#2027 umgesetzt:** Ein Seed-Loader gleicht einen Seed nur gegen globale Zeilen ab (`tenant_key` leer oder fehlend; Abschnitt „Eindeutigkeit in mandantenbezogenen Collections“). Gemessen auf ArangoDB 3.12: Der Aktivitäten- und der Workflow-Seed fanden eine gleichnamige Zeile eines Mandanten und schrieben sie als globale System-Zeile um; der Workflow-Seed hängte zusätzlich seine Phasen an das Template des Mandanten. Ein Substrat eines Mandanten mit der Identität eines Seeds verhinderte die globale Seed-Zeile. `activities` und `workflow_templates` sind von `name` auf `(tenant_key, name)` umgestellt (Migrationen `v0076`, `v0077`; entfernen den Alt-Index auch als `hash` und als `hash` mit `persistent`-Zwilling; eine globale Zeile ohne `tenant_key` bekommt vorher `""`, weil `null` und `""` für den Index zwei Werte sind). Aus dem Review: Die Bereinigung doppelter Task-Templates beim Start erfasst nur noch globale Seed-Zeilen unter ihrem Seed-Workflow (gemessen: sie löschte das gleichnamige eigenständige Template eines zweiten Mandanten und ein zweites gleichnamiges Template im eigenen Workflow). `POST /t/{slug}/tasks/workflows` nimmt kein `is_system` mehr an. Ein Namenskonflikt innerhalb eines Mandanten (Anlegen, Umbenennen, Duplizieren, Copy-on-write-Fork) antwortet `409 DUPLICATE_ENTRY` statt `500`. |
| 1.16 | 2026-10-03 | **#2029 umgesetzt:** Ein Unique-Index auf einer mandantenbezogenen Collection gilt je Mandant (Abschnitt „Eindeutigkeit in mandantenbezogenen Collections“). `tanks` ist von `name` auf `(tenant_key, name)` umgestellt (Migration `v0075`, entfernt den Alt-Index auch als `hash`). Ein `409` nennt das kollidierende Feld, nicht `tenant_key` (außer bei einem Index nur auf `tenant_key`, den es nicht gibt). Klassifikation aller Unique-Indizes und Guard `test_tenant_unique_indexes_are_scoped.py`. |
| 1.15 | 2026-10-03 | **#2009 (Betreiberentscheidung):** Admin-Deaktivierung eines Mandanten und Admin-Entfernung eines Mitglieds verlangen Step-up (AK-56, Umsetzung offen). |
| 1.14 | 2026-10-03 | **#1949 umgesetzt (brechende API-Änderung):** `DELETE /admin/platform/users/{key}` antwortet `202 Accepted` (Körper `{erasure_key, status, requested_at, message}`) statt `204`. Die Anfrage prüft Step-up und Berechtigung, legt den Löschauftrag an, sperrt das Konto, widerruft Sitzungen und Einladungen und benachrichtigt die anderen Mitglieder der persönlichen Mandanten **jetzt** (Sofortlöschung ohne Karenzzeit bleibt); der Celery-Task `retention.run_account_erasure` beansprucht den Auftrag atomar und führt die Löschung aus — die persönlichen Mandanten über die begrenzten Stapel mit Heartbeat aus §1a.2 (AK-53), danach den ArangoDB-Plan des Kontos. Ein fehlgeschlagener oder unvollständiger Lauf ist kein HTTP-Status mehr, sondern der Auftragsstatus `partially_completed` (täglicher Lauf wiederholt ihn), lesbar über das neue `GET /admin/platform/erasures/{erasure_key}`. Vor dem Schließen des Kontos entschieden und weiter synchron: 401/403/404/422/429 (Step-up, Berechtigung), 409 (ein lebender Lauf hält den Auftrag), 503 (Deployment kann nicht löschen, nichts geändert). |
| 1.13 | 2026-10-02 | **Q-L3 / AK-55 umgesetzt (#1878):** Migration `v0067_clean_legacy_foreign_references` bereinigt die #1871-Altlasten und `SiteRepository.update_slot` verschiebt die `HAS_SLOT`-Kante mit dem Feld `location_key`. Konservativ: Zeilen, deren Mandant nicht zweifelsfrei feststeht, bleiben liegen und werden gezählt. Die Umhänge-Variante für fremde Kanten entfällt, weil jedes Quell-Dokument denselben fremden Schlüssel auch in einem eigenen Feld trägt — ein eindeutiges richtiges Ziel ist aus dem Bestand nicht ableitbar; die Kante wird gelöscht. Messwerte aus echten Installationen liegen nicht vor (Befund war „vermutet, nicht gemessen“). |
| 1.12 | 2026-10-02 | **AK-54 umgesetzt (#1805).** Migration `v0066` setzt die v0004-Altstempel auf Seed-Zeilen von `fertilizers`, `nutrient_plans` (samt `nutrient_plan_phase_entries`), `workflow_templates` und `task_templates` auf `tenant_key == ""` zurück. Die Messung auf einer echten ArangoDB (synthetisches Altvolumen, echtes `backfill_tenant_key`, danach die Seed-Loader) ergab: die vier Eltern-Collections heilen die Seed-Loader beim Start selbst (`tenant_key` wird aus dem Modell mit `""` neu geschrieben); **nicht** geheilt wurden die Kinder `nutrient_plan_phase_entries` (198 von 198 blieben gestempelt) — die Mandantenlöschung hätte jedem Seed-Plan seine Phaseneinträge genommen. Seed-Identität = Name laut Seed-YAML **und** ein bewiesener Stempel (Kind unter globalem Elternteil oder Schlüssel auf mehr als der Hälfte der erwarteten Seed-Düngemittel/-Workflows); nicht beweisbare Zeilen bleiben unberührt. |
| 1.11 | 2026-10-02 | **#1792 umgesetzt (AK-53, brechende API-Änderung):** `DELETE /tenants/{slug}` und `DELETE /admin/platform/tenants/{key}` antworten `202 Accepted` (Körper `{tenant_key, status, requested_at, message}`) statt `200`/`204`. Die Anfrage prüft Berechtigung und Step-up, legt den Löschnachweis an und friert den Mandanten ein; der Celery-Task `run_tenant_erasure` beansprucht den Nachweis atomar und löscht in Stapeln zu 1000 Zeilen (eine ArangoDB-Transaktion je Stapel statt einer Transaktion über alle ~95 Collections), schreibt zwischen den Stapeln einen Heartbeat (bedingt auf den eigenen Claim-Stempel; ein verlorener Claim beendet den Lauf ohne Fehlereintrag) und eskaliert ab dem dritten erfolglosen Versuch (Log-Ereignis `tenant_erasure.escalated`, `escalated_at` am Nachweis). **Engere Lesart (bewusst):** Die Gnadenfrist AK-52 ist **weiterhin nicht umgesetzt** — AK-53 gilt für den heutigen Sofort-Pfad; sobald AK-52 gebaut ist, löst deren Frist-Task denselben Task aus. Der Weg über `DELETE /admin/platform/users/{key}` bleibt synchron in der Anfrage (die Kontolöschung braucht das Ergebnis der Mandantenlöschung, bevor ihr eigener Plan läuft), nutzt aber dieselben begrenzten Stapel und den Heartbeat; die Umstellung dieses Wegs ist als Folge-Issue #1949 erfasst. |
| 1.10 | 2026-09-26 | **Datenschutzplan-Entscheidungen, Batch 4–6 (#1792, #1805, #1878):** Mandantenlöschung wird zusätzlich zur v1.9-Gnadenfrist (AK-52) **asynchron** (202 Accepted, Celery-Batches mit Heartbeat und Eskalation) — Betreiberentscheidung, **noch nicht umgesetzt**, Breaking-Change-Kennzeichnung (Q-O1, **AK-53**). §2 dokumentiert die Datenkorrektur für v0004-Altstempel auf globalen Seed-Zeilen von `fertilizers`/`nutrient_plans`/`task_templates` (Q-L1/Q-L2, **AK-54**) und für verwaiste globale Referenzen aus den #1871-Lücken (Q-L3, **AK-55**). |
| 1.9 | 2026-09-26 | **Datenschutzplan-Betreiberentscheidungen, Batch 1-3 (#1790, #1793; reine Spec-Änderung, Umsetzung folgt in eigenen PRs).** **#1790:** AK-16 und die API-Tabelle (§API) beschrieben die Mandantenlöschung noch als Soft-Delete (`status: deleted`) — seit #1769 löscht sie über das Mandanten-Löschinventar. Beide auf das tatsächliche/gewollte Verhalten nachgeführt (AK-44d beschrieb das bereits korrekt). **Q-O2 (#1790):** neue, noch nicht umgesetzte Anforderung **AK-52** — die Mandantenlöschung erhält eine Gnadenfrist analog zur 90-Tage-Frist der Kontolöschung (NFR-011 R-01), statt sofort zu löschen. **Q-R4 (#1793):** `tenant_erasure_records` bekommt eine Aufbewahrungsfrist, siehe NFR-011 R-06a. |
| 1.8 | 2026-09-25 | **Mandant löschen verlangt beide Achsen und einen Step-up (#1791).** Seit #1769 löscht die Mandantenlöschung jede mandantenbezogene Collection unwiderruflich. Bis v1.7 hing sie allein an **Verwaltung** — eine Schriftführerin mit der Rolle Beobachter konnte damit einen ganzen Gemeinschaftsgarten mit einer Anfrage löschen. Neu: **Verwaltung und Leitung** (Schnittmenge, keine Vermischung der Achsen — die Irreversibilitätsgrenze aus REQ-049 §2.3 gilt auch hier), dazu ein **Step-up** im Anfragekörper: der Kurzname des Mandanten wird zurückgetippt, und ein Konto mit lokalem Passwort gibt es erneut ein; ein nur föderiert angemeldetes Konto bestätigt über den Kurznamen (Muster der Kontolöschung, REQ-394). Eigentümerschaft (`owner_user_key`) ist kein Recht und spielt keine Rolle. Dienstkonten und API-Schlüssel (auch die eines menschlichen Kontos) löschen nie einen Mandanten. Der Plattform-Admin-Weg (`DELETE /admin/platform/tenants/{key}`) verlangt denselben Step-up. Geprüft wird im Dienst, nicht nur am Router, sodass beide Wege dieselbe Regel haben; der Löschnachweis hält `step_up` und den Anfragenden als salzgehashte Log-Referenz fest. §1a.2, Rollentabelle §1, API §5 und **AK-44d** nachgeführt. |
| 1.7 | 2026-08-16 | **Nachführung auf REQ-049 v1.4 — die zuweisungsbasierte Write-Kontrolle ist weg.** v1.6 hatte die *Spaltenüberschriften* der Matrix auf das Zwei-Achsen-Vokabular umgestellt, die *Zellinhalte* aber nicht: §1a.1 trug weiterhin `U own+community`, `U own` und `U assigned+own`, §1.1 Szenario 2 beschrieb Parzellen als Schreibgrenze, und §1a.5 stand als Historie im Dokument. Genau das hat REQ-049 §3.5 abgeschafft — die Standort-Zuweisung ist Koordination, kein Recht — und REQ-049 §3.2 führt „Zugewiesene" als Rechteangabe seither unter den **verbotenen Begriffen**. Ein Leser, der nur REQ-024 kannte, baute die falsche Regel; der Code (`MembershipEngine`) tat es nie. Nachgeführt: Rollentabelle §1 (Zwei-Achsen-Modell, `admin` → `lead` + Zusatzberechtigungen), Matrix §1a.1 (alle Zellen auf reine Rangprüfung, Löschen durchgängig 🔒 Leitung), §1a.5 auf einen Grabstein reduziert, §1a.6 auf die drei **tatsächlich gebauten** Dependencies (`require_permission(resource, action)`, `require_tenant_role`, `require_admin_scope`) statt des nie so gebauten `ROLE_PERMISSIONS`-Dicts, Szenarien §1.1, Datenmodell §2, AQL, Engine §3.1, Middleware §3.3, Frontend §4.4/§4.5, Seeds §5, Abnahmekriterien §6 und Scope §8. **Verhaltensänderung gegenüber v1.6:** Das Löschen von Pflanzenfotos war für Gärtner als `D own+community` ausgewiesen und ist jetzt Leitung — die Irreversibilitätsgrenze kennt keine Foto-Ausnahme. |
| 1.6 | 2026-07-29 | **Zwei-Achsen-Rollenmodell (REQ-049, Issue #780):** Die Permission-Matrix (§1a) folgt jetzt dem verbindlichen Vokabular aus REQ-049. Der Wert `admin` ist stillgelegt — er stand in dieser Matrix überwiegend für „darf löschen" (jetzt fachliche Rolle **Leitung**) und an den übrigen Stellen für „verwaltet den Mandanten" (jetzt Zusatzberechtigung **Verwaltung**). §1a.2 hängt vollständig an der Verwaltung statt an einem Rang; technische Konfiguration innerhalb des Mandanten hängt an der Zusatzberechtigung **Technik**. §1a.4 hält fest, dass die Plattform-Rolle über `lead` im Mandanten `platform` abgebildet wird. Die „letzter Admin"-Regel wird zu INV-1 („letzte Verwaltung") und greift auch beim Herabstufen, nicht nur beim Entfernen. Migration `v0032` bildet jeden Bestandswert verlustfrei ab. |
| 1.5 | 2026-06-19 | **Pflanzenfoto-Galerie (REQ-034 Security-Review SR-002):** Permission-Matrix (§1a.1) um die Ressourcen-Zeile **Plant Instance Photos** (`category=plant`) erweitert. Upload/Cover/Löschen laufen über die generischen `CREATE_/UPDATE_/DELETE_RESOURCE`-Permissions mit Zuweisungs-Write-Kontrolle (§1a.5); Viewer nur lesend; DINOv2-Referenz-Freigabe bleibt Platform-Admin (REQ-029-A §4.5). Klärt die in NFR-013 §5.1 abstrakt notierte `attachment:create`-Anforderung gegen den realen `Permission`-Enum-Vertrag. |
| 1.4 | 2026-03-17 | **RBAC Permission-Matrix, Platform-Rollen & Tenant-Notfallverwaltung:** (1) Granulare Permission-Matrix (§1a) mit ressourcentyp-spezifischen CRUD-Rechten pro Rolle (admin/grower/viewer). Spezialaktionen (Phasen-Transition, Task-Zuweisung, Pinnwand-Pinnen). Zuweisungsbasierte Write-Kontrolle formalisiert. (2) Platform-Rollen erweitert: `admin` (KA-Admin) + `viewer` (Read-Only Admin-Panel). (3) Tenant-Notfallverwaltung: `orphaned_since` + `suspended_reason` auf Tenant-Modell. Platform-Admin-Permissions für Emergency-Admin, Tenant-/User-Suspendierung. (4) `Permission` Enum + `require_permission()` Dependency. Service Account Integration (REQ-023 v1.7). |
| 1.3 | 2026-03-16 | **Platform-Tenant & Stammdaten-Scoping:** Neues `is_platform: bool`-Feld auf Tenant. Platform-Tenant als Träger der KA-Admin-Berechtigung. Edge Collection `tenant_has_access` (Species→Tenant) für Sichtbarkeitssteuerung globaler Stammdaten. Auto-Assign-Logik für Tier 1+2 (alle globalen Species automatisch zugewiesen). Kuratierte Zuweisung für Tier 3 (Enterprise). Seed-Daten für Platform-Tenant. Neue User Stories, AQL-Queries, Abnahmekriterien. |
| 1.2 | 2026-03 | Gemeinschaftsgarten-Kollaboration (DutyRotation, BulletinPost, SharedShoppingList) |

## 1. Business Case

**User Story (Gemeinschaftsgarten gründen):** "Als Initiator eines Gemeinschaftsgartens möchte ich eine Organisation in Kamerplanter anlegen und meine 12 Gartenmitglieder einladen können — damit wir gemeinsam unsere Beete planen, Aufgaben verteilen und Ernten dokumentieren."

**User Story (Parzelle zuweisen):** "Als Mitglied mit Verwaltung möchte ich einzelne Parzellen (Sites/Slots) bestimmten Mitgliedern zuweisen können — damit jedes Mitglied nur seine eigenen Beete sieht und bearbeitet, aber trotzdem die Gemeinschaftsflächen (Kompost, Gewächshaus) allen zugänglich bleiben."

**User Story (Mehrere Gärten):** "Als engagierter Gärtner bin ich sowohl in meinem privaten Balkongarten als auch im Gemeinschaftsgarten 'Grüne Oase e.V.' aktiv — ich möchte zwischen diesen Gärten wechseln können, ohne mich ab- und neu anzumelden."

**User Story (Mitglied einladen):** "Als Mitglied mit Verwaltung möchte ich Mitglieder per E-Mail-Einladung oder Einladungslink hinzufügen können — weil nicht alle Mitglieder technisch versiert sind und ein einfacher Link einfacher ist als eine Registrierungs-Anleitung."

**User Story (Aufgaben delegieren):** "Als Gartenleitung möchte ich Gieß-Aufgaben an bestimmte Mitglieder zuweisen können — damit klar ist, wer diese Woche die Tomaten gießt, und nicht dreimal gegossen oder gar nicht."

**User Story (Nur-Lese-Zugang):** "Als Mitglied mit Verwaltung möchte ich Besuchern oder Interessenten einen Nur-Lese-Zugang geben können — damit sie sich den Gartenplan ansehen können, ohne versehentlich Daten zu ändern."

**User Story (Privater Bereich):** "Als Mitglied eines Gemeinschaftsgartens möchte ich meine privaten Zimmerpflanzen in einem separaten, nur für mich sichtbaren Bereich verwalten — ohne dass die Gemeinschaft Zugriff auf meine Wohnungspflanzen hat."

**User Story (OIDC-Tenant-Zuweisung):** "Als Mitglied mit Verwaltung in einer Anbauvereinigung möchte ich, dass sich Mitglieder über unseren zentralen Identity Provider (Keycloak) anmelden und automatisch unserem Tenant zugewiesen werden — ohne manuelle Einladung."

<!-- Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->
**User Story (Platform-Tenant):** "Als Plattform-Betreiber möchte ich über einen speziellen Platform-Tenant die globalen Stammdaten (Pflanzenarten, Sorten, Schädlinge, Krankheiten, Behandlungen, Düngemittel, Nährstoffpläne) verwalten und einzelnen Tenants zuweisen können — damit jeder Tenant nur relevante Daten sieht."

**User Story (Stammdaten-Zuweisung):** "Als KA-Admin möchte ich einem Cannabis-Tenant nur Cannabis-bezogene Stammdaten (Species, Schädlinge, Düngemittel) zuweisen und einem Gemüse-Tenant nur Gemüse-bezogene — damit die Nutzer nicht mit irrelevanten Einträgen überflutet werden."

**User Story (Tenant-übergreifende Elemente):** "Als KA-Admin möchte ich globale Düngemittel, Nährstoffpläne, Schädlinge, Krankheiten und Behandlungen pflegen können, die von mehreren Tenants genutzt werden — während jeder Tenant zusätzlich eigene anlegen kann."
<!-- /Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->

<!-- Quelle: Outdoor-Garden-Planner Review G-030 -->
**User Story (Gießdienst-Rotation):** "Als Gartenleitung möchte ich einen rotierenden Gießdienst einrichten — jede Woche ist ein anderes Mitglied für die Gemeinschaftsbeete zuständig, und die App erinnert automatisch das diensthabende Mitglied."

**User Story (Dienst tauschen):** "Als Gartenmitglied möchte ich meinen Gießdienst mit einem anderen Mitglied tauschen können, wenn ich im Urlaub bin — ohne den Admin belästigen zu müssen."

<!-- Quelle: Outdoor-Garden-Planner Review G-031 -->
**User Story (Pinnwand):** "Als Gartenmitglied möchte ich Nachrichten und Hinweise an alle Mitglieder posten können — 'Schneckenalarm! Bitte Bierfallen aufstellen' oder 'Am Samstag 10 Uhr gemeinsames Kompost-Umsetzen'."

**User Story (Ernte teilen):** "Als Gartenmitglied möchte ich überschüssige Ernte den anderen anbieten können — 'Zu viele Zucchini — wer will?' — ohne eine WhatsApp-Gruppe dafür zu brauchen."

**User Story (Gemeinsame Bestellliste):** "Als Gartenleitung möchte ich eine gemeinsame Einkaufsliste für Saatgut, Erde und Werkzeuge pflegen können — damit wir Sammelbestellungen koordinieren und Kosten teilen können."

**Beschreibung:**
Kamerplanter wird vom Einbenutzer-System zur Multi-Tenant-Plattform erweitert. Der **Tenant** (Mandant) ist der zentrale Isolations-Container: Alle Ressourcen (Pflanzen, Standorte, Aufgaben, Ernten) gehören zu genau einem Tenant. Benutzer können Mitglied in mehreren Tenants sein — mit unterschiedlichen Rollen pro Tenant.

**Kernkonzepte:**

**Tenant — Organisatorischer Container:**
Ein Tenant repräsentiert eine logische Organisationseinheit: einen privaten Garten, einen Gemeinschaftsgarten, einen Verein oder einen Betrieb. Jeder Tenant hat einen eigenen, isolierten Datenraum.

- Bei Registrierung (REQ-023) wird automatisch ein **persönlicher Tenant** erstellt (`type: personal`)
- Gemeinschaftsgärten, Vereine und Betriebe werden als **organisatorische Tenants** erstellt (`type: organization`)
- Ein User kann Mitglied in beliebig vielen Tenants sein
- Ressourcen gehören immer zu genau einem Tenant (kein Cross-Tenant-Sharing)

**Mandantenspezifisches Rollenmodell — zwei Achsen:**

Ein User hat pro Tenant genau **eine fachliche Rolle** (Achse 1) und **keine, eine oder beide administrativen Zusatzberechtigungen** (Achse 2). Das Modell ist in [REQ-049](REQ-049_Rollenmodell-und-Vokabular.md) normativ definiert; die Tabelle hier ist die Kurzfassung, REQ-049 gewinnt bei Widerspruch.

**Achse 1 — fachliche Rolle** (`TenantRole`, geordnet: Leitung ⊇ Gärtner ⊇ Beobachter):

| Rolle | Schlüssel | Was sie im Garten darf |
|-------|-----------|------------------------|
| **Beobachter** | `viewer` | Alles im Mandanten lesen, nichts ändern. Pinnwand und Einkaufslisten lesen |
| **Gärtner** | `grower` | Alle Fachdaten des Mandanten anlegen und ändern, Aufgaben erledigen, Ernte und Behandlungen dokumentieren, Phasen weiterschalten. **Kein Löschen.** An Duty-Rotation teilnehmen, Tausch anfragen, Pinnwand-Posts erstellen und kommentieren, auf Einkaufslisten eintragen |
| **Leitung** | `lead` | Zusätzlich **löschen**, Aufgaben an andere zuweisen, Standortstruktur umbauen, Vorlagen pflegen, Duty-Rotationen erstellen, Posts pinnen und fremde löschen, Einkaufslisten verwalten |

**Achse 2 — administrative Zusatzberechtigung** (`AdminScope`, unabhängig vom Rang):

| Zusatzberechtigung | Schlüssel | Was sie am Mandanten erlaubt |
|--------------------|-----------|------------------------------|
| **Verwaltung** | `management` | Mitglieder einladen, Rollen ändern, entfernen; Einladungslinks; Mandanten-Einstellungen; Standort-Zuweisungen; Mandant löschen (nur zusammen mit **Leitung** und Step-up, §1a.2) |
| **Technik** | `technical` | Home-Assistant- und InvenTree-Anbindung, MQTT, Sensor- und Aktor-Einrichtung, Import, Anreicherungs- und Wetterquellen; Dienstkonten (nur zusammen mit **Leitung** und Step-up, #2137) |

Die beiden Achsen sind **unabhängig**: Ein Beobachter kann Verwaltung halten (Schriftführerin, die nicht gärtnert), eine Leitung kann ohne Technik auskommen. Der frühere Wert `admin` ist stillgelegt — er stand in dieser Matrix überwiegend für „darf löschen" (jetzt `lead`) und an den übrigen Stellen für „verwaltet den Mandanten" (jetzt `management`). Migration `v0032` bildet jeden Bestandswert verlustfrei auf `lead` plus **beide** Zusatzberechtigungen ab.

**Die Standort-Zuweisung ist Koordination, keine Schreibgrenze:**

Standorte (Sites, Locations, Slots) können einzelnen Mitgliedern zugewiesen werden. Die Zuweisung sagt, **wer sich kümmert** — sie schränkt **nicht** ein, wer bearbeiten darf:

- Jeder Gärtner darf jeden Standort und jede Pflanze des Mandanten bearbeiten, zugewiesen oder nicht
- Die Zuweisung steuert Sortierung, Filter und die persönliche Ansicht „meine Parzelle"
- `valid_from`/`valid_until` bleiben für die **saisonale Darstellung** erhalten und wirken nicht auf Berechtigungen
- Beobachter sehen alles lesend, unabhängig von Zuweisungen

**Warum keine Schreibgrenze:** Eine Trennung innerhalb eines Mandanten erzeugt Unvorhersehbarkeit — Mitglieder sehen Datensätze, die sie nicht bearbeiten dürfen, ohne dass die Oberfläche den Grund erklären kann. Wer echte Trennung braucht, bekommt einen eigenen Mandanten; das ist billig, sofort verfügbar und für den Nutzer verständlich (REQ-049 §2.1 P1/P2, §3.5). REQ-049 §3.2 führt „Zugewiesene" als Rechteangabe deshalb unter den **verbotenen Begriffen**.

**Einladungssystem:**

| Methode | Flow |
|---------|------|
| **E-Mail-Einladung** | Ein Mitglied mit **Verwaltung** gibt die E-Mail ein → System sendet Einladungs-E-Mail mit Link → Empfänger registriert sich oder meldet sich an → wird automatisch dem Tenant mit vorgewählter Rolle hinzugefügt. **Nur das Konto, das die eingeladene Adresse trägt und bestätigt hat, nimmt sie an** (andere Adresse oder unbestätigt: 403, die Einladung bleibt offen; #2115, AK-61) |
| **Einladungslink** | Ein Mitglied mit **Verwaltung** generiert einen Link (optional: max. Nutzungen, Ablaufdatum, vordefinierte Rolle) → Link kann geteilt werden (WhatsApp, Aushang) → Jeder mit Link kann beitreten |
| **OIDC-Auto-Join** | OIDC-Provider hat `default_tenant_key` konfiguriert (REQ-023) → Neue User über diesen Provider werden automatisch dem Tenant hinzugefügt |

<!-- Quelle: RBAC Permission-Matrix v1.4 -->
### 1a. RBAC Permission-Matrix

Die Permission-Matrix definiert granular, welche Aktionen jede Rolle pro Ressourcentyp ausführen darf. Sie gilt identisch für menschliche User (`account_type: 'human'`) und Service Accounts (`account_type: 'service'`, REQ-023 v1.7).

**Vokabular:** Die Spaltenüberschriften folgen dem Zwei-Achsen-Modell aus [REQ-049](REQ-049_Rollenmodell-und-Vokabular.md). Achse 1 sind die fachlichen Rollen `Beobachter` / `Gärtner` / `Leitung`, Achse 2 die administrativen Zusatzberechtigungen `Verwaltung` und `Technik`. Der frühere Wert `Admin` ist stillgelegt: Er stand in dieser Matrix überwiegend für „darf löschen" (jetzt `Leitung`) und an den übrigen Stellen für „verwaltet den Mandanten" (jetzt `Verwaltung`). Die Migration `v0032` bildet jeden Bestandswert verlustfrei auf `Leitung` plus beide Zusatzberechtigungen ab.

#### 1a.1 Tenant-scoped Rollen — Ressourcen-Permissions

**Legende:**
- **C** = Create, **R** = Read, **U** = Update, **D** = Delete
- **all** = alle Ressourcen des Mandanten. Es gibt **kein** `own` und **kein** `community` mehr: Die Standort-Zuweisung schränkt Schreibrechte nicht ein (REQ-049 §3.5), und „Zugewiesene" ist als Rechteangabe verboten (REQ-049 §3.2).
- ✅ = erlaubt, ❌ = verboten, 🔒 = nur Leitung

**Die Matrix entscheidet allein über den Rang der fachlichen Rolle.** Jede Zeile lässt sich auf drei Regeln zurückführen: Lesen darf jedes Mitglied, Anlegen und Ändern ab Gärtner, Löschen nur die Leitung. Die Ressourcenzeilen sind deshalb heute weitgehend gleichförmig — sie stehen einzeln, weil eine künftige Verschärfung je Ressourcentyp hier ansetzt und nicht in den Routern. Wo eine Zeile davon abweicht, steht der Grund in der Spalte **Spezialaktionen** — sofern er nicht schon aus der Ressource folgt: Ein reiner Lesekatalog (`Substrate Types`, `Workflow Templates`) trägt sein `❌CUD` ohne weitere Begründung, weil er im Mandanten gar nicht geschrieben wird. Die Spalte ist also der Ort für begründungsbedürftige Abweichungen, nicht eine Zusage, dass jede Zelle jenseits der drei Regeln dort erklärt wäre.

| Ressource (Collection) | Leitung | Gärtner | Beobachter | Spezialaktionen |
|------------------------|-------|--------|--------|-----------------|
| **Sites** | CRUD all | CRU all, ❌D | R all | Standortstruktur umbauen (Hierarchie ändern): 🔒 Leitung |
| **Locations** | CRUD all | CRU all, ❌D | R all | Location-Erstellung erbt die Tenant-Zugehörigkeit der Parent-Site. `Location` trägt **keinen** eigenen `tenant_key` — die Prüfung hängt am Parent |
| **Slots** | CRUD all | CRU all, ❌D | R all | Wie Location: kein eigener `tenant_key`, Prüfung über die Parent-Site |
| **Plant Instances** | CRUD all | CRU all, ❌D | R all | **Phasen-Transition:** ab Gärtner. Auf run-gebundenen Pflanzen gesperrt (REQ-003 §3, HTTP 409 `phase.run_owned`) — eine Sperre der Fachlogik, keine Rollenfrage |
| **Planting Runs** | CRUD all | CRU all, ❌D | R all | **State-Transition** und **Batch-Ops:** ab Gärtner |
| **Tasks** | CRUD all | CRU all, ❌D | R all | **Zuweisen (`assigned_to`):** 🔒 Leitung. **Status ändern:** ab Gärtner, **auch bei fremd zugewiesenen Aufgaben** — die Zuweisung ist Absprache, kein Ausschluss, und deckt genau den Fall ab, dass die zugewiesene Person ausfällt (REQ-049 §3.5) |
| **Harvest Batches** | CRUD all | CRU all, ❌D | R all | **Quality Assessment:** ab Gärtner |
| **Tanks** | CRUD all | CRU all, ❌D | R all | **Tank-State erstellen:** ab Gärtner |
| **Fertilizers** (tenant-eigen) | CRUD all | CRU all, ❌D | R all | Globale Fertilizers: nur lesen (alle Rollen). Mandanteneigene sind Fachdaten — anlegen und ändern ab Gärtner (AK-25, REQ-001 Schicht 3) |
| **Nutrient Plans** (tenant-eigen) | CRUD all | CRU all, ❌D | R all | Globale Pläne: nur lesen (alle Rollen) |
| **Feeding Events** | CRUD all | CRU all, ❌D | R all | — |
| **Watering Events** | CRUD all | CRU all, ❌D | R all | **Quick-Confirm:** ab Gärtner |
| **Watering Logs** | CRUD all | CRU all, ❌D | R all | — |
| **IPM Inspections** | CRUD all | CRU all, ❌D | R all | — |
| **Treatment Applications** | CRUD all | CRU all, ❌D | R all | **Karenz-Gate:** automatisch, **kein Rollen-Override** — auch die Leitung kann es nicht übergehen (422) |
| **Care Profiles** | CRUD all | R all, U all (confirm/snooze), ❌CD | R all | **Care Confirmation:** ab Gärtner. Anlegen bleibt der Leitung: ein Pflegeprofil ist eine Vorlage, keine Beobachtung |
| **Workflow Templates** | CRUD all | R all, ❌CUD | R all | Custom-Templates: nur Leitung |
| **Substrate Types** | CRUD all | R all, ❌CUD | R all | — |
| **Import Jobs** | — | — | — | **Vollständig auf Achse 2: `Technik`** (REQ-049 §2.4, REQ-012 §5 und CI-001). Ausführen, Dry-Run, Bestätigen **und Lesen** der Import-Historie hängen an der Zusatzberechtigung; der fachliche Rang entscheidet hier nichts, deshalb stehen alle drei Rangspalten auf `—`. Ein Import schreibt in den Stammdatenbestand — technische Konfiguration, keine Gartenarbeit. Die Zeile steht hier nur, damit die Ressource in der Matrix auffindbar bleibt |
| **Plant Instance Photos** (Attachment, `category=plant`, REQ-034) | CRUD all | CRU all (Cover setzen), ❌D | R all | **Upload/Cover:** ab Gärtner. **Löschen: 🔒 Leitung** — v1.6 wies hier `D own+community` aus; die Irreversibilitätsgrenze aus REQ-049 §2.3 kennt keine Foto-Ausnahme, und `require_attachment_permission` entscheidet über dieselbe Matrix. Ein Gärtner darf zudem nur Attachments **referenzieren**, die er selbst hochgeladen hat (SEC-003) — das ist eine Herkunftsprüfung am Anhang, keine Rollenregel. Beobachter: nur ansehen. **DINOv2-Referenz-Freigabe (`is_active=true`):** 🔒 Platform-Admin (REQ-029-A §4.5) |

#### 1a.2 Tenant-Verwaltungs-Permissions

Diese Aktionen hängen an der Zusatzberechtigung **Verwaltung** (REQ-049 §2.4) — die fachliche Rolle spielt keine Rolle. Eine Schriftführerin mit der Rolle Beobachter verwaltet die Mitgliederliste; eine Leitung ohne Verwaltung nicht.

**Eine Ausnahme: Mandant löschen (#1791).** Die Löschung vernichtet seit #1769 alle Daten des Mandanten unwiderruflich und liegt damit zugleich auf der Irreversibilitätsgrenze der fachlichen Achse (REQ-049 §2.3). Sie verlangt deshalb **Verwaltung und Leitung** — beide, nicht eine von beiden — und einen **Step-up** im Anfragekörper: `confirm_slug` (der Kurzname des Mandanten, zurückgetippt) und, bei einem Konto mit lokalem Passwort, `password` (das aktuelle Passwort). Ein nur föderiert angemeldetes Konto hat kein lokales Geheimnis und bestätigt über den Kurznamen (wie die Kontolöschung, REQ-394). Antworten: `403` ohne beide Achsen, als Dienstkonto oder mit einem API-Schlüssel (auch dem eines menschlichen Kontos — ein Schlüssel kann sich nicht erneut anmelden), `422` bei falschem Kurznamen, `401` bei fehlendem oder falschem Passwort — jeweils bevor sich etwas ändert. Eigentümerschaft (`owner_user_key`) ist Herkunft, kein Recht: Sie genügt nicht und wird nicht verlangt, sonst wäre ein Garten unlöschbar, sobald sein Gründer ihn verlässt. Der Plattform-Admin löscht über `DELETE /admin/platform/tenants/{key}` mit demselben Step-up.

**Gnadenfrist und Abbruch (AK-52, umgesetzt v1.23, #2123).** Die Löschung wird **geplant**, nicht sofort ausgeführt: Der Mandant geht in den Zustand `pending_deletion` und ist ab sofort für jedes Mitglied, jeden API-Schlüssel und jeden MCP-Client gesperrt wie ein gesperrter Mandant (AK-48); die Mitgliedschaften bleiben unverändert gespeichert. Alle Mitglieder erhalten eine E-Mail mit dem Löschdatum und dem Hinweis, ihre eigenen Daten über den persönlichen Datenexport zu sichern (Art. 20). Nach `RETENTION_TENANT_ERASURE_GRACE_DAYS` (Standard 90 Tage, NFR-011 R-01b) beansprucht der tägliche Lauf `resume_tenant_erasures` den Nachweis, setzt den Zustand `deleted` und führt das Inventar aus (unten). Bis dahin bricht ein Mitglied mit **Leitung und Verwaltung** die Löschung über `POST /tenants/{slug}/erasure/cancel` ab — die Route steht bewusst nicht hinter dem Slug-Resolver, weil der Mandant für niemanden auflöst; der Dienst prüft die gespeicherte Mitgliedschaft, verweigert jeden API-Schlüssel und verlangt den Step-up `tenant_erasure_cancel`. Der Plattform-Admin bricht über `POST /admin/platform/tenants/{key}/erasure/cancel` ab. Mit einer Frist von 0 Tagen (Self-Hosted) bleibt der Sofort-Pfad.

<!-- Quelle: Datenschutzplan Q-O1, #1792 -->
**Asynchrone Ausführung des Mandanten-Löschinventars (Betreiberentscheidung
2026-09-26, #1792) — umgesetzt am 2026-10-02 (v1.11), brechende API-Änderung.** Das gilt
zusätzlich zur AK-52-Gnadenfrist (Q-O2, #1790, **umgesetzt v1.23, #2123**) und betrifft den
Schritt **nach** deren Ablauf (mit Frist 0: unmittelbar nach der Annahme). Bis v1.10
lief die eigentliche Löschung synchron im HTTP-Handler — der externe Phase-0-Schritt, dann eine
einzelne ArangoDB-Stream-Transaktion über ~95 inventarisierte Collections (gemessen: bei
200 000 Zeilen und 100 000 Kanten über 198 s, die Gegenstelle brach bei 60 s ab und auch der
Abbruch der Transaktion schlug fehl). Bei einem
großen Mandanten kann diese Transaktion die Server-Limits
(`--transaction.streaming-max-transaction-size`, Idle-Timeout) überschreiten; der Fehler
ist deterministisch, jeder tägliche Retry scheitert gleich, der Mandant bleibt eingefroren
(`partially_completed`), der aufrufende Proxy antwortet zwischenzeitlich mit 504.
Umgesetzt:

- `DELETE /tenants/{slug}` und `DELETE /admin/platform/tenants/{key}` antworten **`202
  Accepted`** statt zuvor `200`/`204` — der Löschnachweis wird angelegt und der Mandant
  eingefroren (Memberships deaktiviert), aber die Löschung selbst läuft danach.
- Ein **Celery-Task** führt die Löschung in **begrenzten, idempotenten Batches** aus
  (Elternschlüssel sind bereits am Löschnachweis persistiert, #1769); kein einzelner
  Batch darf die Server-Transaktionslimits erreichen.
- Der Lauf schreibt einen **Heartbeat** zwischen den Batches fort, damit
  `TenantErasureEngine.STALE_AFTER_HOURS` ihn nicht während eines noch laufenden,
  nur langsamen Laufs erneut beansprucht.
- Ein deterministisch scheiternder Batch **eskaliert** nach N Versuchen (Alarmierung des
  Betreibers), statt täglich lautlos denselben Fehler zu wiederholen.
- Der Weg über `DELETE /admin/platform/users/{key}` (REQ-025 AK-PT-01..03, AK-IE-01..03)
  ist seit **#1949** ebenfalls asynchron (`202`): Die Anfrage erfasst die Kontolöschung und
  sperrt das Konto, der Celery-Task `retention.run_account_erasure` löscht danach die
  persönlichen Mandanten über dieselben begrenzten Stapel und denselben Heartbeat und
  führt anschließend den Plan des Kontos aus. Der Kontolöschauftrag (nicht der
  Mandantennachweis) trägt den Status; ein unvollständiger Lauf ist `partially_completed`
  und wird vom täglichen Lauf (`retention.execute_scheduled_erasures`) wiederholt.

Dies ist eine **brechende API-Änderung** (Antwortcode und -semantik ändern sich für jeden
bestehenden Aufrufer, der auf einen synchronen Abschluss wartet); sie ist im Changelog als
solche gekennzeichnet. Ein Lauf, der beim Deploy bereits läuft, wird vom täglichen
`resume_tenant_erasures`-Lauf nach `STALE_AFTER_HOURS` (6 h) ohne Heartbeat übernommen. Refs #1769, REQ-025.
<!-- /Quelle: Datenschutzplan Q-O1, #1792 -->

| Aktion | Verwaltung | ohne Verwaltung |
|--------|------------|-----------------|
| **Tenant-Einstellungen ändern** | ✅ | ❌ |
| **Mitglieder auflisten** | ✅ | ✅ (Name + Rolle sichtbar, alle Rollen) |
| **Mitglied einladen** | ✅ | ❌ |
| **Mitglied-Rolle ändern** | ✅ | ❌ |
| **Mitglied-Zusatzberechtigungen ändern** | ✅ (INV-1: nicht die letzte Verwaltung) | ❌ |
| **Mitglied entfernen** | ✅ (INV-1: nicht die letzte Verwaltung) | ❌ |
| **Einladungslinks erstellen** | ✅ | ❌ |
| **Einladungslinks revoken** | ✅ | ❌ |
| **LocationAssignment erstellen** | ✅ | ❌ |
| **LocationAssignment ändern** | ✅ | ❌ |
| **LocationAssignment entfernen** | ✅ | ❌ |
| **Service Accounts verwalten** | ❌ allein nicht — Leitung **und** Technik (#2137, REQ-049 v1.10) | ❌ (mit Leitung **und** Technik: ✅) |
| **Tenant löschen** | ✅ nur mit **Leitung** + Step-up (Kurzname, Passwort) — siehe oben; geplant mit Gnadenfrist (AK-52) | ❌ |
| **Geplante Löschung abbrechen** | ✅ nur mit **Leitung** + Step-up (Passwort) — innerhalb der Gnadenfrist | ❌ |
| **Eigene Membership verlassen** | ✅ (INV-1: nicht die letzte Verwaltung) | ✅ |

Technische Konfiguration innerhalb des Mandanten — Home-Assistant- und InvenTree-Anbindung, MQTT, Sensor- und Aktor-Einrichtung, Import, Anreicherungs- und Wetterquellen — hängt an der Zusatzberechtigung **Technik** und ist in REQ-049 §2.4 abschließend aufgeführt. Sie steht bewusst getrennt von der Verwaltung: Wer die Sensorik betreut, braucht deshalb keinen Zugriff auf die Mitgliederliste.

#### 1a.3 Kollaborations-Permissions (Gemeinschaftsgarten)

| Aktion | Leitung | Gärtner | Beobachter |
|--------|---------|---------|------------|
| **Duty-Rotation erstellen** | ✅ | ❌ | ❌ |
| **Duty-Rotation bearbeiten** | ✅ | ❌ | ❌ |
| **Duty-Rotation anzeigen** | ✅ | ✅ | ✅ |
| **Am Dienst teilnehmen** | ✅ | ✅ (wenn in `rotation_members`) | ❌ |
| **Dienst-Tausch anfragen** | ✅ | ✅ | ❌ |
| **Dienst-Tausch akzeptieren** | ✅ | ✅ | ❌ |
| **Pinnwand-Post erstellen** | ✅ | ✅ | ❌ |
| **Pinnwand-Post kommentieren** | ✅ | ✅ | ❌ |
| **Pinnwand-Post lesen** | ✅ | ✅ | ✅ |
| **Pinnwand-Post pinnen** | ✅ | ❌ | ❌ |
| **Pinnwand-Post löschen** | ✅ (alle) | ✅ (eigene) | ❌ |
| **Shopping-List erstellen** | ✅ | ❌ | ❌ |
| **Shopping-List Items hinzufügen** | ✅ | ✅ | ❌ |
| **Shopping-List anzeigen** | ✅ | ✅ | ✅ |
| **Shopping-List abschließen** | ✅ | ❌ | ❌ |

#### 1a.4 Platform-Rollen — Differenziertes Admin-Panel

Der Platform-Tenant (§2, `is_platform: true`) trägt zusätzlich die Rolle Beobachter. Die Plattform-Rolle wird über die höchste fachliche Rolle im technischen Mandanten `platform` abgebildet (REQ-049 §2.5); der frühere Schlüssel `admin` heißt dort seit `v0032` `lead`.

| Platform-Rolle | Schlüssel | Rechte |
|---------------|-----------|--------|
| **Platform-Admin** | `lead` im Platform-Tenant | Voller KA-Admin-Zugriff: Globale Stammdaten CRUD, `tenant_has_access`-Verwaltung, Tenant-Übersicht, OIDC-Provider-Konfiguration, Platform Service Accounts, Species-Promotion, User-Übersicht |
| **Platform-Viewer** | `viewer` im Platform-Tenant | Read-Only Admin-Panel: Globale Stammdaten lesen, Tenant-Übersicht (read-only), OIDC-Provider-Liste, User-Statistiken. Kein Schreibzugriff auf globale Daten. Typischer Use-Case: Monitoring-Dashboards, Audit. |

**Platform-Permission-Matrix:**

| Aktion | Platform-Admin | Platform-Viewer |
|--------|---------------|-----------------|
| **Globale Species/Cultivars CRUD** | ✅ | R only |
| **`tenant_has_access`-Kanten verwalten** | ✅ | ❌ |
| **Species promoten (tenant → global)** | ✅ | ❌ |
| **Cultivar promoten (tenant → global)** <!-- ADR-002 --> | ✅ | ❌ |
| **promotion_audit_log einsehen** <!-- ADR-002 --> | ✅ | ✅ (read-only) |
| **Alle Tenants auflisten** | ✅ | ✅ (read-only) |
| **Tenant-Details anzeigen** | ✅ | ✅ (read-only) |
| **OIDC-Provider konfigurieren** | ✅ | R only |
| **Platform Service Accounts verwalten** | ✅ | ❌ |
| **User-Übersicht** | ✅ | ✅ (read-only) |
| **Globale IPM-Daten (Pests, Diseases, Treatments) CRUD** | ✅ | R only |
| **Globale Fertilizers/NutrientPlans CRUD** | ✅ | R only |
<!-- Quelle: Tenant-Notfallverwaltung v1.7 -->
| **Verwaiste Tenants einsehen** | ✅ | ✅ (read-only) |
| **Notfall-Admin in verwaistem Tenant ernennen** | ✅ | ❌ |
| **Tenant suspendieren** | ✅ | ❌ |
| **Tenant reaktivieren** | ✅ | ❌ |
| **User suspendieren** | ✅ | ❌ |
| **User reaktivieren** | ✅ | ❌ |
| **Tenant-Mitgliederliste einsehen (Cross-Tenant)** | ✅ | ✅ (read-only) |
<!-- /Quelle: Tenant-Notfallverwaltung v1.7 -->

#### 1a.5 Zuweisungsbasierte Write-Kontrolle — **entfallen**

> **Ersatzlos gestrichen mit v1.7.** Dieser Abschnitt definierte eine Funktion
> `can_write(user, resource, tenant)`, die einem Gärtner das Schreiben nur an zugewiesenen und
> gemeinschaftlichen Ressourcen erlaubte. **REQ-049 §3.5** hat sie aufgehoben: Der Mandant ist die
> gemeinsame Arbeitsmenge, die Standort-Zuweisung ist Koordination und kein Recht.
> `can_write()` reduziert sich damit auf die Rangprüfung der fachlichen Rolle und ist als eigene
> Funktion überflüssig — sie heißt heute `MembershipEngine.can_edit_resource(role)` und nimmt
> weder Ressource noch Zuweisungen entgegen.

Was von der Zuweisung bleibt und was nicht:

| Konstrukt | Bleibt | Wirkt **nicht** auf |
|-----------|--------|---------------------|
| `LocationAssignment` | Anzeige „meine Parzelle", Sortierung, Filter, Zuständigkeits-Hinweis | Schreibrechte |
| `valid_from` / `valid_until` | saisonale Darstellung der Zuständigkeit | Schreibrechte |
| `Task.assigned_to` | Hervorhebung, Reihenfolge, Benachrichtigungsempfänger (REQ-049 §2.8) | Wer die Aufgabe erledigen darf |

**Warum der Abschnitt ganz verschwindet statt als Historie stehen zu bleiben:** v1.6 hatte ihn mit
einem Vermerk „nicht mehr umzusetzen" versehen und die formalen Regeln darunter belassen. Das ist
die schlechteste der drei Möglichkeiten — der Pseudocode blieb lesbar, vollständig und ohne
Kontext zitierfähig, und genau danach wurde weiterhin gebaut und geprüft. Eine gestrichene Regel
gehört nicht in halber Länge konserviert; wer den Vorzustand braucht, findet ihn in der
Versionsgeschichte.

#### 1a.6 Backend-Dependencies: drei Wächter, disjunkt

> **Neu geschrieben mit v1.7.** Bis v1.6 beschrieb dieser Abschnitt ein `Permission`-Enum mit einem
> `ROLE_PERMISSIONS`-Dict, aus dem eine einzige Dependency `require_permission(permission)` ihre
> Entscheidung zog. So ist es nie gebaut worden, und es passt auch nicht zum Zwei-Achsen-Modell:
> Ein Dict, das Rolle → Permissions abbildet, kann Achse 2 nicht ausdrücken, weil eine
> Zusatzberechtigung gerade **unabhängig** vom Rang ist. Der Abschnitt beschreibt jetzt, was in
> `app/common/auth.py` steht.

REQ-049 §2.7 fordert drei **disjunkte** Zweige — eine Aktion darf nie über zwei zugleich
erreichbar sein. Jeder Zweig hat genau eine Dependency:

| Zweig | Dependency | Entscheidet über |
|-------|-----------|------------------|
| fachlich, je Ressource | `require_permission(resource, action)` | Anlegen / Ändern / Löschen einer Fachressource |
| fachlich, je Rang | `require_tenant_role(min_role)` | Aktionen, die einen Mindestrang verlangen, ohne an einer Ressource zu hängen |
| administrativ | `require_admin_scope(scope)` | Mitgliederverwaltung, Einstellungen, Integrationen |

```python
def require_permission(resource: ResourceType | str, action: Action) -> Callable: ...
def require_tenant_role(min_role: TenantRole) -> Callable: ...
def require_admin_scope(scope: AdminScope) -> Callable: ...
```

**Alle drei setzen auf `get_current_tenant` auf**, das den Mandanten aus dem Pfad auflöst und einen
Nicht-Mitglied bereits mit `403` abweist, bevor irgendein Wächter läuft. Die Wächter machen
deshalb **keine** eigene Datenbankabfrage — sie entscheiden allein auf `ctx.role` bzw.
`ctx.admin_scopes` — und sie schlagen fehl-geschlossen: Eine Rolle, auf die keine Regel passt,
wird abgewiesen.

**Die Autorität ist die reine `MembershipEngine`, nicht die Dependency.** `require_permission`
delegiert an genau das Prädikat, das zur Aktion gehört:

| `action` | Prädikat | Wer besteht |
|----------|----------|-------------|
| `CREATE`, `UPDATE` | `MembershipEngine.can_edit_resource` | Leitung, Gärtner |
| `DELETE` | `MembershipEngine.can_delete_resource` | **nur Leitung** (REQ-049 §2.3) |
| `READ` | `MembershipEngine.can_view_resource` | jedes Mitglied |

Diese Umleitung ist der Grund, warum die Router-Oberfläche und die Engine nicht auseinanderlaufen
können: Es gibt eine Stelle, an der „Gärtner darf nicht löschen" steht, und beide Wege gehen durch
sie. Lesen bleibt offen — ein `GET` braucht den Wächter nur, wenn ein bestimmter Lesezugriff
privilegiert ist.

**`resource` entscheidet heute nichts** und wird trotzdem verlangt. Die Prädikate sind
rollengetrieben, noch nicht ressourcentyp-spezifisch; das Argument dokumentiert an der Aufrufstelle,
*was* dort bewacht wird, und erlaubt einer künftigen Matrix je Ressourcentyp, einzelne Einträge zu
verschärfen, ohne jeden Router anzufassen.

**Die beschreibende Matrix `app/core/permissions.py`** trägt die Ressource×Aktion-Zuordnung aus
§1a.1 als Daten. Sie ist **nicht** der Wächter der HTTP-Router, sondern die Autorität für zwei
andere Oberflächen: die Anhang-Wache (`require_attachment_permission`) und den MCP-Dispatcher
(`assert_mcp_permission`, REQ-033). Ihre Einträge müssen mit §1a.1 übereinstimmen — die
Löschrechte der Pflanzendomäne sind dort bereits auf Leitung korrigiert.

**Verwendung in Routern:**

```python
@router.post("/t/{slug}/plant-instances")
def create_plant(
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.CREATE)),
): ...

@router.delete("/t/{slug}/sites/{site_key}")
def delete_site(
    ctx: TenantContext = Depends(require_permission(ResourceType.SITE, Action.DELETE)),
): ...

@router.post("/t/{slug}/members")
def invite_member(
    ctx: TenantContext = Depends(require_admin_scope(AdminScope.MANAGEMENT)),
): ...
```

**Was ausdrücklich nicht passieren darf:** Eine administrative Aktion über `require_permission` zu
gaten oder eine fachliche über `require_admin_scope`. Beides führte die Vermischung wieder ein, zu
deren Beseitigung REQ-049 geschrieben wurde — und beides sieht an der Aufrufstelle unauffällig
aus, weil ein Mitglied mit `lead` + `management` durch beide Wächter kommt. Der Fehler fällt erst
bei der Schriftführerin auf, die Beobachter ist und die Mitgliederliste pflegen soll.

<!-- /Quelle: RBAC Permission-Matrix v1.4 -->

### 1.1 Szenarien

**Szenario 1: Gemeinschaftsgarten gründen — "Grüne Oase e.V."**
```
1. Lisa (bereits registriert) navigiert zu /tenants/create
2. Erstellt Tenant:
   name: "Grüne Oase e.V."
   type: organization
   description: "Gemeinschaftsgarten in Berlin-Kreuzberg, 24 Parzellen"
3. Lisa wird automatisch Leitung dieses Tenants, mit beiden Zusatzberechtigungen
   (role: lead, admin_scopes: [management, technical])
4. Lisa erstellt Einladungslink:
   role: grower
   admin_scopes: []
   max_uses: 20
   expires_in: 30 Tage
5. Lisa teilt den Link in der WhatsApp-Gruppe des Vereins
6. 11 Mitglieder klicken den Link → werden als "Gärtner" hinzugefügt
7. Lisa gibt 2 Mitgliedern die Zusatzberechtigung "Verwaltung" (Stellvertretung
   in der Mitgliederpflege) und einem davon zusätzlich die Rolle "Leitung",
   damit er auch löschen darf. Die beiden Achsen werden getrennt vergeben —
   wer die Mitgliederliste pflegt, muss nicht löschen dürfen
```

**Szenario 2: Parzellen zuweisen**
```
Voraussetzung: Tenant "Grüne Oase e.V." mit 12 Mitgliedern
Site-Struktur (REQ-002):
  Site: "Grüne Oase Kreuzberg"
    Location: "Parzelle A1" → zugewiesen an Max
    Location: "Parzelle A2" → zugewiesen an Lisa
    Location: "Parzelle A3" → zugewiesen an Tom
    ...
    Location: "Kompostplatz" → keine Zuweisung (Gemeinschaft)
    Location: "Gewächshaus" → keine Zuweisung (Gemeinschaft)

Für Max (Rolle: grower) bedeutet das:
  ✅ Lesen:     Alle Locations des Tenants
  ✅ Schreiben: Alle Locations des Tenants — auch A2 und A3.
                Die Zuweisung ist KEINE Schreibgrenze (REQ-049 §3.5)
  ❌ Löschen:   Keine. Löschen ist Leitung (REQ-049 §2.3)
  👁 Anzeige:   "Parzelle A1" erscheint in seiner Ansicht "meine Parzelle",
                die Liste ist danach vorsortiert, und an A2 steht sichtbar,
                dass Lisa sich kümmert
```

**Szenario 3: Zwischen Gärten wechseln**
```
Max ist Mitglied in:
  1. "Maxs Garten" (personal, Leitung + beide Zusatzberechtigungen) — 8 Zimmerpflanzen
  2. "Grüne Oase e.V." (organization, Grower) — Parzelle A1

1. Max öffnet Dashboard → sieht seinen aktiven Tenant "Maxs Garten"
2. Klickt auf Tenant-Switcher in der App-Bar
3. Dropdown zeigt:
   - "Maxs Garten" (privat) ✓ aktiv
   - "Grüne Oase e.V." (12 Mitglieder)
4. Max wählt "Grüne Oase e.V." → Dashboard zeigt jetzt Parzelle A1 und Gemeinschaftsflächen
5. URL ändert sich zu /t/gruene-oase/dashboard (Tenant-Slug in URL)
```

**Szenario 4: OIDC-Auto-Join — Anbauvereinigung mit Keycloak**
```
Voraussetzung:
  - OIDC-Provider "keycloak-anbauverein" konfiguriert (REQ-023)
  - default_tenant_key zeigt auf Tenant "Cannabis Social Club Berlin"
  - default_role: "grower"   # admin_scopes bleibt leer

1. Neues Vereinsmitglied Anna öffnet Kamerplanter
2. Klickt "Cannabis Social Club Berlin" (OIDC-Button)
3. Wird zu Keycloak weitergeleitet → meldet sich an
4. Kamerplanter erstellt User-Account
5. Automatisch: Membership in "Cannabis Social Club Berlin" mit Rolle "grower"
6. Anna sieht sofort das Vereins-Dashboard
```

**Szenario 5: Aufgabe an Mitglied delegieren**
```
Voraussetzung: REQ-006 Task-System + Tenant "Grüne Oase e.V."

1. Lisa (Leitung) erstellt Task im Gemeinschaftsgarten:
   title: "Tomaten gießen — Parzelle A1-A6"
   assigned_to: Max (user_key)
   due_date: 2026-03-15
2. Max sieht den Task in seiner persönlichen Task-Queue
3. Max markiert Task als erledigt
4. Lisa sieht im Leitungs-Dashboard: Task erledigt von Max, 2026-03-15 14:30
```

**Szenario 6: Persönlicher Bereich bleibt privat**
```
Max hat:
  - Tenant "Maxs Garten": 3 Orchideen, 5 Sukkulenten (privat)
  - Tenant "Grüne Oase e.V.": Parzelle A1 mit 20 Tomaten

Sichtbarkeit für andere Mitglieder der "Grüne Oase":
  ✅ Max' Parzelle A1 (20 Tomaten) — innerhalb des Gemeinschafts-Tenants
  ❌ Max' Orchideen und Sukkulenten — im persönlichen Tenant, unsichtbar
```

<!-- Quelle: Outdoor-Garden-Planner Review G-030 -->
**Szenario 7: Gießdienst-Rotation — "Wer gießt diese Woche?"**
```
Voraussetzung: Tenant "Grüne Oase e.V." mit 12 aktiven Mitgliedern

1. Lisa (Leitung) erstellt Duty-Rotation:
   name: "Gießdienst Gemeinschaftsbeete"
   type: watering_duty
   rotation_members: [Max, Lisa, Tom, Anna, ...] (8 von 12 Mitgliedern nehmen teil)
   rotation_interval: weekly
   duty_starts: monday

2. System generiert automatisch Wochenplan:
   KW 10: Max → Erinnerung Montag 8:00 "Du bist diese Woche Gießdienst!"
   KW 11: Lisa → Erinnerung Montag 8:00
   KW 12: Tom → ...

3. Tom geht in Urlaub (KW 12):
   Tom öffnet Dienstplan → "Tausch anfragen"
   Anna akzeptiert → KW 12: Anna statt Tom
   System benachrichtigt beide + die Leitung (REQ-049 §2.8)

4. Max bestätigt Gießdienst:
   Öffnet App → "Gießdienst erledigt" + optionales Foto
   Alle Mitglieder sehen: "✅ Max hat die Gemeinschaftsbeete gegossen (Di, 14:30)"
```

<!-- Quelle: Outdoor-Garden-Planner Review G-031 -->
**Szenario 8: Pinnwand — "Schneckenalarm!"**
```
1. Tom postet auf der Garten-Pinnwand:
   "🐌 Schneckenalarm auf den Salatbeeten! Bitte heute Abend Bierfallen aufstellen."
   Kategorie: alert

2. Alle 12 Mitglieder bekommen Push-Notification
3. Lisa kommentiert: "Habe Schneckenkorn (Eisen-III-Phosphat) mitgebracht, liegt im Schuppen"
4. Anna reagiert: 👍

5. Lisa (Leitung) pinnt einen Beitrag:
   "📌 Nächster Arbeitseinsatz: Samstag 14.03., 10 Uhr. Kompost umsetzen + Beete vorbereiten."
   pinned: true → bleibt oben
```

## 2. ArangoDB-Modellierung

### Nodes:

- **`:Tenant`** — Mandant / Organisation
  - Collection: `tenants`
  - Properties:
    - `name: str` (Anzeigename, z.B. "Grüne Oase e.V.")
    - `slug: str` (URL-sicher, UNIQUE, z.B. `gruene-oase`)
    - `type: Literal['personal', 'organization']`
    <!-- Quelle: Platform-Tenant v1.3 -->
    - `is_platform: bool` (Default: `false`) — `true` nur für den einen Platform-Tenant. Platform-Tenant-Admins haben KA-Admin-Rechte (REQ-023 v1.6). Wird beim Seeding automatisch erstellt. Reguläre Tenants können `is_platform` nicht auf `true` setzen.
    <!-- /Quelle: Platform-Tenant v1.3 -->
    - `description: Optional[str]` (Beschreibung, z.B. "Gemeinschaftsgarten in Berlin-Kreuzberg")
    - `avatar_url: Optional[str]` (Logo/Bild der Organisation)
    - `settings: dict` (Tenant-spezifische Einstellungen, z.B. Default-Sprache, Zeitzone)
    - `max_members: int` (Mitgliederlimit, mindestens 1; wirksam ist `min(max_members, TENANT_MAX_MEMBERS_CEILING)`, Plattform-Obergrenze Default 50; persönlicher Mandant bei Gründung `1`, Organisation ohne Angabe die Obergrenze; darüber `422`. Ein voller Mandant verweigert jeden weiteren Beitritt mit `422 MEMBER_LIMIT_REACHED`, AK-64)
    - `status: Literal['active', 'suspended', 'deleted']`
    <!-- Quelle: Tenant-Notfallverwaltung v1.4 -->
    - `orphaned_since: Optional[datetime]` (Zeitpunkt seit dem der Tenant keine aktiven Admins hat. `null` = Tenant hat aktive Admins. Wird von Celery-Task wöchentlich geprüft und bei Emergency-Admin-Ernennung auf `null` zurückgesetzt.)
    - `suspended_reason: Optional[str]` (Grund der Suspendierung durch Platform-Admin. `null` = nicht suspendiert oder kein Grund angegeben.)
    <!-- /Quelle: Tenant-Notfallverwaltung v1.4 -->
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:Membership`** — Mitgliedschaft (User ↔ Tenant)
  - Collection: `memberships`
  - Properties:
    - `role: Literal['viewer', 'grower', 'lead']` (Achse 1, genau eine — REQ-049 §2.3)
    - `admin_scopes: list[Literal['management', 'technical']]` (Achse 2, keine bis beide — REQ-049 §2.4; unabhaengig vom Rang)
    - `display_name_override: Optional[str]` (Spitzname im Garten, z.B. "Max der Tomatenkönig")
    - `joined_at: datetime`
    - `invited_by: Optional[str]` (user_key des Einladenden)
    - `status: Literal['active', 'suspended', 'left']`

- **`:Invitation`** — Einladung (E-Mail oder Link)
  - Collection: `invitations`
  - Properties:
    - `type: Literal['email', 'link']`
    - `email: Optional[str]` (Nur bei `type: email`)
    - `token_hash: str` (SHA-256 Hash des Einladungstokens)
    - `role: Literal['viewer', 'grower', 'lead']` (fachliche Rolle bei Beitritt)
    - `admin_scopes: list[Literal['management', 'technical']]` (Zusatzberechtigungen bei Beitritt, Vorgabe `[]`)
    - `max_uses: Optional[int]` (Nur bei `type: link`, `null` = unbegrenzt)
    - `use_count: int` (Default: 0)
    - `expires_at: Optional[datetime]` (`null` = kein Ablauf)
    - `created_by: str` (user_key des Erstellers)
    - `status: Literal['pending', 'accepted', 'expired', 'revoked']`
    - `created_at: datetime`

- **`:LocationAssignment`** — Parzellen-Zuweisung (User ↔ Location)
  - Collection: `location_assignments`
  - Properties:
    - `role: Literal['responsible', 'helper']` (Verantwortlicher vs. Helfer)
    - `assigned_at: datetime`
    - `assigned_by: str` (user_key des Zuweisenden)
    - `valid_from: Optional[date]` (Saisonale Zuweisung, z.B. ab 01.04.)
    - `valid_until: Optional[date]` (Saisonale Zuweisung, z.B. bis 31.10.)
    - `notes: Optional[str]` (z.B. "Nur Kräuter, bitte kein Mais")

<!-- Quelle: Outdoor-Garden-Planner Review G-030 -->
- **`:DutyRotation`** — Rotierende Dienstplanung (z.B. Gießdienst)
  - Collection: `duty_rotations`
  - Properties:
    - `name: str` (z.B. "Gießdienst Gemeinschaftsbeete")
    - `duty_type: Literal['watering', 'composting', 'general_maintenance', 'custom']`
    - `rotation_interval: Literal['daily', 'weekly', 'biweekly', 'monthly']`
    - `rotation_members: list[str]` (user_keys in Rotations-Reihenfolge)
    - `current_index: int` (Index des aktuell Diensthabenden in rotation_members)
    - `duty_start_day: Optional[Literal['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']]`
    - `reminder_time: time` (Uhrzeit der Erinnerung, Default: 08:00)
    - `reminder_days_before: int` (Tage vor Dienstbeginn, Default: 0 = am selben Tag)
    - `active_months: Optional[list[int]]` (Aktive Monate, z.B. [4,5,6,7,8,9,10] — kein Gießdienst im Winter)
    - `status: Literal['active', 'paused', 'archived']`
    - `created_by: str` (user_key)
    - `created_at: datetime`

- **`:DutySwapRequest`** — Tausch-Anfrage für Dienstplan
  - Collection: `duty_swap_requests`
  - Properties:
    - `requester_key: str` (user_key des Tauschenden)
    - `target_key: Optional[str]` (user_key des Tauschpartners, null = offene Anfrage an alle)
    - `swap_date: date` (Datum des zu tauschenden Dienstes)
    - `reason: Optional[str]` (z.B. "Urlaub")
    - `status: Literal['pending', 'accepted', 'declined', 'cancelled']`
    - `accepted_by: Optional[str]` (user_key)
    - `created_at: datetime`

<!-- Quelle: Outdoor-Garden-Planner Review G-031 -->
- **`:BulletinPost`** — Pinnwand-Beitrag im Tenant
  - Collection: `bulletin_posts`
  - Properties:
    - `title: Optional[str]`
    - `body: str` (Nachrichtentext, Markdown erlaubt)
    - `category: Literal['info', 'alert', 'event', 'offer', 'request', 'general']`
      (info = Hinweis, alert = Warnung/Dringend, event = Termin, offer = "Wer will Zucchini?", request = "Brauche Mulch")
    - `pinned: bool` (Angepinnt = bleibt oben, nur Leitung)
    - `author_key: str` (user_key)
    - `photo_refs: list[str]` (Fotos, z.B. Schneckenbefall)
    - `expires_at: Optional[datetime]` (Automatisches Ausblenden nach Datum)
    - `status: Literal['active', 'archived', 'deleted']`
    - `reaction_counts: dict` (z.B. {"👍": 3, "👎": 0, "😂": 1})
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:BulletinComment`** — Kommentar zu Pinnwand-Beitrag
  - Collection: `bulletin_comments`
  - Properties:
    - `body: str`
    - `author_key: str`
    - `created_at: datetime`

- **`:SharedShoppingList`** — Gemeinsame Einkaufsliste
  - Collection: `shared_shopping_lists`
  - Properties:
    - `name: str` (z.B. "Saatgut-Sammelbestellung Frühjahr 2026")
    - `status: Literal['open', 'ordered', 'delivered', 'closed']`
    - `items: list[dict]` (Einträge: {item: str, quantity: str, requested_by: str, price_estimate: Optional[float], checked: bool})
    - `total_estimate: Optional[float]`
    - `notes: Optional[str]`
    - `created_by: str`
    - `created_at: datetime`
    - `updated_at: datetime`

### Edges:

```
has_membership:         users → memberships              (1:N, User hat Mitgliedschaften)
membership_in:          memberships → tenants             (N:1, Mitgliedschaft gehört zu Tenant)
has_invitation:         tenants → invitations             (1:N, Tenant hat Einladungen)
belongs_to_tenant:      sites → tenants                   (N:1, Site gehört zu Tenant)
assigned_to_location:   users → location_assignments      (1:N, User hat Standort-Zuweisungen)
assignment_for:         location_assignments → locations   (N:1, Zuweisung für Location)
assignment_in_tenant:   location_assignments → tenants     (N:1, Zuweisung im Kontext eines Tenants)
```

<!-- Quelle: Outdoor-Garden-Planner Review G-030, G-031 -->
```
has_duty_rotation:      tenants → duty_rotations          (1:N)
has_swap_request:       duty_rotations → duty_swap_requests (1:N)
has_bulletin_post:      tenants → bulletin_posts            (1:N)
has_bulletin_comment:   bulletin_posts → bulletin_comments  (1:N)
has_shopping_list:      tenants → shared_shopping_lists     (1:N)
```

### Tenant-Zugehörigkeit bestehender Entitäten:

Alle bestehenden Ressourcen-Collections erhalten ein `tenant_key: str`-Feld:

| Collection | Typ | Tenant-Bezug |
|-----------|-----|-------------|
| `sites` | Node | `tenant_key` + Edge `belongs_to_tenant` |
| `locations` | Node | Transitiv über Site (Site → Location) |
| `slots` | Node | Transitiv über Location |
| `plant_instances` | Node | `tenant_key` (direkt, für Pflanzen ohne Standort) |
| `planting_runs` | Node | `tenant_key` |
| `tasks` | Node | `tenant_key` + `assigned_to: Optional[str]` (user_key) |
| `harvest_batches` | Node | `tenant_key` |
| `tanks` | Node | `tenant_key` |
| `fertilizers` | Node | `tenant_key` (pro Tenant eigene Düngerliste) |
| `nutrient_plans` | Node | `tenant_key` |
| `inspections` | Node | `tenant_key` |
| `treatment_applications` | Node | `tenant_key` |
| `care_profiles` | Node | `tenant_key` (transitiv über PlantInstance) |
| `workflow_templates` | Node | `tenant_key` (Custom-Templates pro Tenant) |

#### Eindeutigkeit in mandantenbezogenen Collections (#2029)

Ein Unique-Index auf einer Collection, deren Dokumente einem Mandanten gehören, gilt **je Mandant**: Er enthält `tenant_key` oder, bei transitiv zugeordneten Collections, den Elternschlüssel. Ein collection-weiter Unique-Index verweigert Mandant B einen Wert, den Mandant A belegt. Der `409` verrät B außerdem, dass ein anderer Mandant diesen Wert hält. Ein `409` nennt das kollidierende Feld (z. B. `name`), nicht `tenant_key`. Ausnahme: ein Unique-Index, der nur aus `tenant_key` besteht, nennt dieses Feld; einen solchen Index gibt es nicht.

| Klasse | Regel | Collections (Stand 2026-10-03) |
|---|---|---|
| Mandanteneigen | Unique nur mit `tenant_key` | `tanks` (`tenant_key, name`; bis v0075 `name`), `climate_normals`, `irrigation_demands`, `season_states`, `weather_source_configs`, `memberships`, `mcp_idempotency_record`, `ha_publish_settings` |
| Hybrid-Katalog | Unique mit `tenant_key`; global (`tenant_key == ""`) genau einmal | `fertilizers` (`tenant_key, product_name, brand`), `species` (`tenant_key, scientific_name_normalized`), `activities` (`tenant_key, name`; bis v0076 `name`), `workflow_templates` (`tenant_key, name`; bis v0077 `name`) |
| Bewusst mandantenübergreifend eindeutig | Begründung steht im Guard | `calendar_feeds.token`, `invitations.token_hash` (geheimes Token, ohne Mandant aufgelöst), `location_assignments` (`membership_key` gehört genau einem Mandanten), `tasks.care_dedup_key` (berechneter Schlüssel beginnt mit `tenant_key`) |
| Offen (Defekt dieser Klasse) | Index noch collection-weit | `species.scientific_name`, `plant_instances.instance_id`, `harvest_batches.batch_id`, `slots.slot_id` |
| Global / kontobezogen | Collection-weit eindeutig ist korrekt | `botanical_families`, `phase_definitions`, `treatments`, `pests`, `diseases`, `beneficials`, `fish_species`, `starter_kits`, `glossary_terms`, `hardiness_zones`, Konto- und Credential-Collections |

**Seed-Abgleich (#2027).** Ein Seed-Loader gleicht einen Seed nur gegen die **globalen** Zeilen eines Hybrid-Katalogs ab (`tenant_key` leer oder fehlend), über den ganzen Katalog und ohne festes Fenster. Eine Zeile eines Mandanten mit der Identität eines Seeds (Name, bei Substraten `(type, name_de oder brand)`) wird weder gefunden noch verändert, und sie ersetzt die globale Seed-Zeile nicht. Die globale Zeile und die des Mandanten bestehen nebeneinander; der Unique-Index je Mandant ist die Voraussetzung dafür. Das gilt für `fertilizers` und `nutrient_plans` (#2000, #1957) sowie für `activities`, `workflow_templates` und `substrates` (#2027).

`pests`, `diseases` und `treatments` tragen heute kein `tenant_key` (nur `origin`). Werden tenant-eigene Einträge nach dem Stammdaten-Scoping unten umgesetzt, fallen ihre Unique-Indizes in die erste oder zweite Klasse.

Der Guard `src/backend/tests/unit/guards/test_tenant_unique_indexes_are_scoped.py` leitet die Klasse ab. Er nimmt jeden Unique-Index, den `ensure_collections` anlegt, und die mandantenbezogenen Collections aus der Modellableitung. Ein neuer collection-weiter Unique-Index auf einer solchen Collection schlägt fehl, bis er mandantenbezogen ist oder mit Begründung deklariert wird. Die Liste der offenen Einträge darf nur schrumpfen.

<!-- Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->
**Globale Collections mit Stammdaten-Scoping (`tenant_has_access`):**

Die folgenden Collections enthalten globale Referenzdaten, die per `tenant_has_access`-Edge einzelnen Tenants zugewiesen werden. Zusätzlich können Tenants eigene Einträge anlegen (`origin: 'tenant'`, `tenant_key` gesetzt):

| Collection | Sichtbarkeit | Tenant-eigene Einträge | Overlay |
|-----------|-------------|----------------------|---------|
| `species` | Via `tenant_has_access` Edge | Ja (`origin: 'tenant'`) | `tenant_species_config` (REQ-001 v4.0) |
| `cultivars` | Transitiv über Species | Ja (`origin: 'tenant'`) | `tenant_cultivar_config` (REQ-001 v4.0) |
| `pests` | Via `tenant_has_access` Edge | Ja (`origin: 'tenant'`) | — (Phase 2) |
| `diseases` | Via `tenant_has_access` Edge | Ja (`origin: 'tenant'`) | — (Phase 2) |
| `treatments` | Via `tenant_has_access` Edge | Ja (`origin: 'tenant'`) | — (Phase 2) |
| `fertilizers` | Via `tenant_has_access` Edge | Ja (`origin: 'tenant'`) | — (Phase 2) |
| `nutrient_plans` | Via `tenant_has_access` Edge | Ja (`origin: 'tenant'`) | — (Phase 2) |

**Erweiterung bestehender Collections:**

Die Collections `pests`, `diseases`, `treatments`, `fertilizers` und `nutrient_plans` erhalten analog zu Species/Cultivar (REQ-001 v4.0) folgende neue Felder:

```python
# Neue Felder auf pests, diseases, treatments, fertilizers, nutrient_plans:
origin: Literal['system', 'enrichment', 'import', 'tenant']  # Default: 'system'
tenant_key: Optional[str]  # Default: null (global)
```

- **Global (`tenant_key: null`):** Von KA-Admin gepflegt, sichtbar für Tenants mit `tenant_has_access`-Kante
- **Tenant-eigen (`tenant_key` gesetzt):** Im Mandanten angelegt (ab Gärtner, §1a.1), nur im eigenen Mandanten sichtbar
- Promotion (tenant → global) über KA-Admin wie bei Species (in-place: `origin` → `'system'`, `tenant_key` → `null`)

**`tenant_has_access`-Edge unterstützt mehrere Collection-Typen:**

```
tenant_has_access Edge Collection:
  _from: species/{key}        → _to: tenants/{key}
  _from: pests/{key}          → _to: tenants/{key}
  _from: diseases/{key}       → _to: tenants/{key}
  _from: treatments/{key}     → _to: tenants/{key}
  _from: fertilizers/{key}    → _to: tenants/{key}
  _from: nutrient_plans/{key} → _to: tenants/{key}
```

**Hinweis:** Cultivars werden **nicht** direkt über `tenant_has_access` zugewiesen — sie sind transitiv über ihre Species sichtbar.

**Ungefilterte globale Collections (kein Scoping):**

| Collection | Begründung |
|-----------|-----------|
| `botanical_families` | Rein taxonomische Referenzdaten, kein operativer Nutzen zum Einschränken |
| `users` | User-Accounts existieren unabhängig von Tenants |
| `oidc_provider_configs` | System-Level-Konfiguration |

**Auto-Assign-Logik:**

| Tier | Verhalten |
|------|-----------|
| **Tier 1 (Light-Modus)** | Alle globalen Stammdaten werden automatisch dem System-Tenant zugewiesen (REQ-027 v1.1) |
| **Tier 2 (Multi-User, kleine Instanzen)** | Bei Tenant-Erstellung werden automatisch `tenant_has_access`-Kanten für **alle** globalen Stammdaten erstellt. Kein manuelles Kuratieren nötig. |
| **Tier 3 (Enterprise)** | KA-Admin kuratiert Zuweisungen aktiv über das Admin-Panel. Bei Tenant-Erstellung werden **keine** automatischen Kanten erstellt — KA-Admin weist gezielt zu. |

Die Entscheidung zwischen Tier 2 und Tier 3 wird über ein neues Tenant-Setting gesteuert:

```python
# Tenant.settings Erweiterung
{
    "auto_assign_master_data": true  # Default: true (Tier 1+2), false für Enterprise
}
```

Alternativ kann der KA-Admin dies global konfigurieren:

```python
# Settings (Environment Variable)
KAMERPLANTER_AUTO_ASSIGN_MASTER_DATA: bool = True  # Default: True
```
<!-- /Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->

**Hinweis zu Seed-Daten in Tenant-scoped Collections:**
Einige Tenant-scoped Collections enthalten vorinstallierte Seed-Daten (z.B. `workflow_templates` mit 3 Workflows/16 Task-Templates aus REQ-006). Bei Erstellung eines neuen Tenants werden die System-Seed-Daten **als Kopie** in den Tenant übernommen (`tenant_key` wird gesetzt). Der Tenant-Admin kann diese anschließend anpassen oder löschen. Globale Stammdaten (Species, Cultivars, IPM, Fertilizer, NutrientPlans) werden hingegen **referenziert via `tenant_has_access`-Kanten, nicht kopiert**.

<!-- Quelle: Datenschutzplan Q-L1/Q-L2, #1805 -->
**Datenkorrektur: v0004-Altstempel auf globalen Seed-Zeilen (Betreiberentscheidung
2026-09-26, #1805).** Migration `v0004` (`backfill_tenant_key.py`, `TOP_LEVEL_COLLECTIONS`)
hat historisch jede Zeile von `fertilizers`, `nutrient_plans`, `workflow_templates` und
`task_templates` ohne `tenant_key` auf einen „Default-Tenant" gestempelt — einschließlich
globaler Seed-Zeilen, die zu diesem Zeitpunkt existierten. Anders als bei `species`
(`v0036`) und `cultivars` (`v0038`) hat bisher keine Migration diese Stempel auf den
hybriden Katalogen zurückgesetzt; `fertilizers`, `nutrient_plans` und `task_templates`
tragen zudem keinen `is_system`-Marker. Da die Mandantenlöschung (#1769) die Zeilen ihres
Mandanten löscht, verliert eine Installation mit solchen Altstempeln beim Löschen des
Default-Tenants globale Seed-Zeilen.

Beschlossen:

- Eine Migration setzt betroffene Seed-Zeilen auf `tenant_key == ""` zurück (dieselbe Form
  wie `v0036`/`v0038`), analog zu Species/Cultivars; ein Task-Template eines dabei
  erhaltenen System-Workflows wird mit ihm zurückgesetzt.
- **Die Vorab-Prüfung (Zählung betroffener Zeilen) läuft ausschließlich gegen einen
  Dev-Cluster oder ein wiederhergestelltes Produktions-Backup — nie gegen die
  Produktionsdatenbank direkt.** Das gilt unabhängig davon, wie einfach ein Read-only-Zugriff
  auf Produktion wäre; die Messung selbst darf keine Produktionslast oder
  Produktionsverbindung erzeugen.
- Ist auf dem gemessenen Bestand keine betroffene Zeile vorhanden, dokumentiert die
  Migration diesen Befund und bleibt ein No-op (idempotent, wie bei `v0036`/`v0038`).

**Umsetzung (v1.11, `v0066_reset_legacy_seed_tenant_stamps`).** Die Migration läuft vor den
Seed-Loadern. Eine Zeile wird nur zurückgesetzt, wenn die Seed-YAML sie benennt (Schlüssel wie im
Loader: `(product_name, brand)`, Plan-/Workflow-Name, `(Workflow-Name, Task-Name)`) **und** ihr
`tenant_key` als v0004-Stempel bewiesen ist: ein Kind (Phaseneintrag, Task-Template) trägt ihn unter
einem globalen Elternteil, oder er steht auf mehr als der Hälfte der laut YAML erwarteten
Seed-Düngemittel und -Workflows (nur diese beiden Collections zählen, weil ihre Identität
unique-indiziert ist). Eine Zeile wird nur zurückgesetzt, wenn sie die einzige globale oder
gleich gestempelte Zeile ihrer Identität und kein Klon ist; Kinder folgen einem globalen oder im
selben Lauf zurückgesetzten Elternteil. Der Seed-Name eines fremden Mandanten reicht nicht. Eine Zeile, die die YAML nicht benennt (z. B. ein
später umbenannter oder entfernter Seed), bleibt unberührt — ein Stempel ist dort nicht beweisbar,
und ein Überreset würde fremde Daten global machen. Nicht gemessen: echte produktive Volumes.

<!-- Quelle: Datenschutzplan Q-L3, #1878 -->
**Datenkorrektur: verwaiste globale Referenzen aus den #1871-Lücken (Betreiberentscheidung
2026-09-26, #1878).** Vor den #1871-Fixes konnten drei Klassen mandantenübergreifender
Referenzen entstehen: (1) geteilte Workflow-Templates (`tenant_key == ""`), die den Namen
einer **privaten** Species eines anderen Mandanten tragen; (2) Slots, deren
`location_key`-Feld und `HAS_SLOT`-Kante auf unterschiedliche Standorte zeigen; (3) Kanten
(`EQUIPMENT_AT`, `ASSIGNED_TO_LOCATION`, `LOG_SLOT`, `FEEDS_FROM`, Entry-→-Species-Kanten
von Pflanzdurchläufen) zu einem Ziel in einem fremden Mandanten. Die #1871-Fixes verhindern
neue Fälle, bereinigen aber keinen Bestand.

Beschlossen:

- Ein geteiltes globales Template, das eine **private** Species-Bezeichnung trägt, wird
  **privat** — Eigentümer ist der aktuelle Eigentümer dieser Species, nicht der
  Default-/Platform-Tenant.
- Eine fremde Kante aus Klasse (3) wird, wo eindeutig bestimmbar, auf den korrekten
  Mandanten **umgehängt** (z. B. anhand des Quell-Dokuments); ist das Ziel nicht eindeutig
  bestimmbar, wird die Kante **gelöscht**.
- Slots aus Klasse (2) folgen dem Feld (`location_key`), nicht der Kante — `update_slot`
  bewegt seither ohnehin beide gemeinsam (#1871 B1).
- Die Migration ist eine Zähl-Migration mit anschließendem, idempotentem Korrekturlauf; sie
  protokolliert nur Anzahlen, nie Inhalte einer fremden Species.

**Umsetzung (v1.13, Migration `v0067`).** Die Zählabfragen sind dieselben Prädikate, nach
denen die Migration repariert (`app/migrations/support/legacy_foreign_references.py`); der
Dry-Run der Migration liefert die Zahlen vorab. Festgelegte Grenzen:

- Ein Slot folgt dem Feld **nur**, wenn Feld-Standort und aktueller Kanten-Standort demselben
  Mandanten gehören. Zeigt das Feld in einen fremden Mandanten, hat der Slot keine oder
  mehrere `HAS_SLOT`-Kanten, bleibt die Zeile unverändert und wird gezählt.
- Eine fremde Kante wird nur gelöscht, wenn beide Endpunkt-Mandanten bekannt (nicht leer)
  sind und sich unterscheiden. Ein globales Ziel (`tenant_key == ""`, z. B. eine globale
  Species), eine an den Mandanten **freigegebene** Species (`tenant_has_access`) und jede
  Kante mit nicht bestimmbarem Endpunkt bleiben erhalten (Zählung `left_unclassified`).
- Ein geteiltes Template wird **nicht** zugeordnet (und nur gezählt), wenn die Species an einen
  Mandanten freigegeben ist (der Empfänger würde seinen genutzten Plan verlieren) oder der
  Eigentümer bereits einen generierten Plan für die Species besitzt (ein Duplikat könnte dessen
  bearbeitete Kopie verdecken).
- `LOG_SLOT` wird nur beurteilt, wenn Feld und `HAS_SLOT`-Kante des Slots denselben Mandanten
  nennen — das Feld ist bei Altzeilen genau der durch die Lücke geschriebene Wert.
- `ENTRY_FOR_SPECIES` wird nur gelöscht, wenn die Kante **vor** dem Merge der #1871-Fixes
  (2026-09-26) entstand: Eine Freigabe ist widerrufbar, eine jüngere Kante ohne aktuelle
  Freigabe kann unter einer später entzogenen Freigabe legitim entstanden sein.
- `SiteRepository.update_slot` verschiebt die Kante nie über eine Mandantengrenze (interne
  Aufrufer reichen den gelesenen Slot zurück, dessen Feld bei Altzeilen fremd sein kann).
- Das Quell-Dokument behält sein Feld (`location_key`, `slot_keys`, `species_key`, …); nur die
  Kante wird entfernt. Das Aufräumen dieser Felder ist nicht Teil von #1878.

### Indizes:

```
tenants:
  - PERSISTENT INDEX on [slug] UNIQUE
  - PERSISTENT INDEX on [status]
  - PERSISTENT INDEX on [type]

memberships:
  - PERSISTENT INDEX on [role]
  - PERSISTENT INDEX on [status]

invitations:
  - PERSISTENT INDEX on [token_hash] UNIQUE
  - PERSISTENT INDEX on [email, status]
  - PERSISTENT INDEX on [expires_at]
  - TTL INDEX on [expires_at] expireAfter: 0  (automatische Bereinigung)

location_assignments:
  - PERSISTENT INDEX on [role]
  - PERSISTENT INDEX on [valid_from, valid_until]
```

### AQL-Beispiellogik:

**Alle Tenants eines Users mit Rollen:**
```aql
FOR m IN 1..1 OUTBOUND DOCUMENT(users, @user_key) GRAPH 'kamerplanter_graph'
  OPTIONS { edgeCollections: ['has_membership'] }
  FILTER m.status == 'active'
  LET tenant = FIRST(
    FOR t IN 1..1 OUTBOUND m GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['membership_in'] }
      RETURN t
  )
  FILTER tenant.status == 'active'
  LET member_count = LENGTH(
    FOR m2 IN memberships
      FOR e IN membership_in
        FILTER e._from == m2._id AND e._to == tenant._id
        FILTER m2.status == 'active'
        RETURN 1
  )
  RETURN {
    tenant_key: tenant._key,
    tenant_name: tenant.name,
    tenant_slug: tenant.slug,
    tenant_type: tenant.type,
    role: m.role,
    member_count: member_count
  }
```

**Bearbeitbare Locations für einen Gärtner im Tenant:**
```aql
LET user_key = @user_key
LET tenant_key = @tenant_key

// Prüfe Rolle im Tenant
LET membership = FIRST(
  FOR m IN 1..1 OUTBOUND DOCUMENT(users, user_key) GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_membership'] }
    FILTER m.status == 'active'
    LET t = FIRST(
      FOR t IN 1..1 OUTBOUND m GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['membership_in'] }
        FILTER t._key == tenant_key
        RETURN t
    )
    FILTER t != null
    RETURN m
)

// Schreibrecht haengt allein am Rang der fachlichen Rolle (REQ-049 §2.3, §3.5).
// Die Zuweisung wird mitgeliefert, weil die Oberflaeche sie ANZEIGT --
// sie geht bewusst NICHT in `can_edit` ein.
LET can_edit = membership.role IN ['grower', 'lead']
LET can_delete = membership.role == 'lead'

FOR site IN sites
  FOR e IN belongs_to_tenant
    FILTER e._from == site._id AND e._to == CONCAT('tenants/', tenant_key)
    FOR loc IN 1..1 OUTBOUND site GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['has_location'] }

      // Prüfe ob Location zugewiesen ist
      LET assignments = (
        FOR la IN location_assignments
          FOR ae IN assignment_for
            FILTER ae._from == la._id AND ae._to == loc._id
            FOR ue IN assigned_to_location
              FILTER ue._to == la._id
              RETURN { user_key: PARSE_IDENTIFIER(ue._from).key, role: la.role }
      )

      // Rein darstellend: steuert Sortierung und die Ansicht "meine Parzelle"
      LET is_mine = LENGTH(
        FOR a IN assignments FILTER a.user_key == user_key RETURN 1
      ) > 0

      LET is_community = LENGTH(assignments) == 0

      RETURN {
        location: loc,
        can_edit: can_edit,        // gleich fuer JEDE Location des Mandanten
        can_delete: can_delete,
        is_mine: is_mine,          // Anzeige, kein Recht
        is_community: is_community,
        assigned_to: assignments
      }
```

**Einladung per Token einlösen:**
```aql
LET invitation = FIRST(
  FOR inv IN invitations
    FILTER inv.token_hash == @token_hash
    FILTER inv.status == 'pending'
    FILTER inv.expires_at == null OR inv.expires_at > DATE_ISO8601(DATE_NOW())
    FILTER inv.max_uses == null OR inv.use_count < inv.max_uses
    RETURN inv
)

// Tenant der Einladung finden
LET tenant = FIRST(
  FOR t IN 1..1 INBOUND invitation GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_invitation'] }
    RETURN t
)

RETURN { invitation: invitation, tenant: tenant }
```

## 3. Backend-Architektur

### 3.1 Engine-Schicht

**`TenantEngine`** — Tenant-Logik (pure Logik, kein I/O):

```python
class TenantEngine:
    def generate_slug(self, name: str) -> str: ...
        # URL-sicherer Slug: "Grüne Oase e.V." → "gruene-oase-ev"
        # Umlaute: ä→ae, ö→oe, ü→ue, ß→ss
        # Sonderzeichen entfernen, Leerzeichen → Bindestrich

    def validate_tenant_name(self, name: str) -> list[str]: ...
        # Min 2, Max 100 Zeichen
        # Kein reiner Whitespace

    def can_create_organization(self, user_memberships: list[Membership]) -> bool: ...
        # Max. 10 organisatorische Tenants pro User (Missbrauchsschutz)
```

**`MembershipEngine`** — Rollenlogik und Berechtigungsprüfung:

```python
class MembershipEngine:
    """Reine Praedikate. Kein Repository, kein Request, keine Zuweisungen."""

    # Werte wie im Code (membership_engine.py) -- Rangvergleich, keine Bedeutung
    # der Zahlen selbst; nur die Ordnung ist verbindlich.
    ROLE_HIERARCHY = {TenantRole.VIEWER: 0, TenantRole.GROWER: 1, TenantRole.LEAD: 2}

    # ── Achse 1: fachliche Rolle ─────────────────────────────────────────
    @staticmethod
    def can_edit_resource(role: TenantRole) -> bool: ...
        # Leitung und Gaertner. NIMMT KEINE Zuweisungen ENTGEGEN --
        # die Signatur ist der Ort, an dem REQ-049 §3.5 durchgesetzt wird:
        # was nicht hereinkommt, kann die Entscheidung nicht beeinflussen.

    @staticmethod
    def can_delete_resource(role: TenantRole) -> bool: ...
        # NUR Leitung -- die Irreversibilitaetsgrenze aus REQ-049 §2.3

    @staticmethod
    def can_view_resource(role: TenantRole) -> bool: ...
        # Jede fachliche Rolle. Die Mandantenzugehoerigkeit ist zu diesem
        # Zeitpunkt bereits geprueft (get_current_tenant), sonst gaebe es
        # keine Rolle.

    # ── Achse 2: administrative Zusatzberechtigung ───────────────────────
    # Zwei getrennte Praedikate statt eines generischen `has_scope`, damit die
    # Aufrufstelle die gemeinte Befugnis benennt statt einen Enum-Wert.
    @staticmethod
    def can_manage_members(admin_scopes: list[AdminScope]) -> bool: ...
        # `management`. Unabhaengig vom Rang: ein Beobachter mit `management`
        # besteht, eine Leitung ohne `management` nicht.

    @staticmethod
    def can_configure_integrations(admin_scopes: list[AdminScope]) -> bool: ...
        # `technical`. Home Assistant, MQTT, Sensorik, Import, KI-Provider.

    @staticmethod
    def validate_not_last_manager(manager_count: int,
                                  target_has_management: bool) -> bool: ...
        # INV-1: der letzte Traeger von `management` darf weder entfernt noch
        # dieser Berechtigung entzogen werden -- sonst ist der Mandant
        # verwaist (REQ-023 §5a.5). Nimmt die ZAHL entgegen, nicht die Liste:
        # das Praedikat bleibt damit frei von Repository-Kenntnis.
```

**`InvitationEngine`** — Einladungslogik:

```python
class InvitationEngine:
    def create_invitation_token(self) -> tuple[str, str]: ...
        # Gibt (raw_token, token_hash) zurück

    def validate_invitation(self, invitation: Invitation) -> list[str]: ...
        # Prüft: nicht abgelaufen, nicht revoked, max_uses nicht erreicht

    def can_accept(self, invitation: Invitation, user: User) -> bool: ...
        # Prüft: User ist nicht bereits Mitglied im Tenant
```

### 3.2 Service-Schicht

**`TenantService`** — Tenant-CRUD und Mitgliederverwaltung:

```python
class TenantService:
    def __init__(self, tenant_repo, membership_repo, invitation_repo,
                 location_assignment_repo, tenant_engine, membership_engine,
                 invitation_engine, email_service): ...

    # --- Tenant-CRUD ---
    async def create_personal_tenant(self, user: User) -> Tenant: ...
        # Automatisch bei Registrierung (REQ-023)
        # name: "{display_name}s Garten", type: personal
        # Ersteller wird role=lead mit beiden Zusatzberechtigungen

    async def create_organization(self, user: User, name: str, description: str = None) -> Tenant: ...
        # Prüft: Max 10 Orgs pro User
        # Generiert Slug (TenantEngine)
        # Erstellt Tenant + Membership (role=lead, admin_scopes=[management, technical])

    async def get_tenant(self, tenant_key: str, user: User) -> Tenant: ...
        # Prüft: User ist Mitglied
    async def update_tenant(self, tenant_key: str, user: User, updates: TenantUpdate) -> Tenant: ...
        # Nur mit Verwaltung
    async def delete_tenant(self, tenant_key: str, user: User) -> None: ...
        # Nur mit Verwaltung, Soft-Delete, warnt bei aktiven Mitgliedern

    async def list_my_tenants(self, user: User) -> list[TenantWithRole]: ...
        # Alle Tenants des Users mit fachlicher Rolle und Zusatzberechtigungen

    # --- Mitgliederverwaltung ---
    async def list_members(self, tenant_key: str, user: User) -> list[MemberInfo]: ...
        # Alle aktiven Mitglieder mit Rolle und Zusatzberechtigungen -- fuer JEDE Rolle
        # sichtbar (Name + Rolle), das Aendern haengt an der Verwaltung (§1a.2)
    async def update_member_role(self, tenant_key: str, user: User,
                                  target_user_key: str, new_role: str,
                                  new_scopes: list[AdminScope] | None = None) -> Membership: ...
        # Nur mit Verwaltung. Beide Achsen sind einzeln setzbar.
        # INV-1: verhindert das Entziehen der LETZTEN Verwaltung
    async def remove_member(self, tenant_key: str, user: User, target_user_key: str) -> None: ...
        # Mit Verwaltung, oder Mitglied entfernt sich selbst (Leave)
        # INV-1: verhindert die Entfernung der letzten Verwaltung
    async def leave_tenant(self, tenant_key: str, user: User) -> None: ...
        # User verlässt Tenant freiwillig
        # INV-1: verhindert, wenn er die letzte Verwaltung traegt

    # --- Einladungen ---
    async def create_email_invitation(self, tenant_key: str, user: User,
                                       email: str, role: str) -> Invitation: ...
        # Nur mit Verwaltung, sendet Einladungs-E-Mail
    async def create_link_invitation(self, tenant_key: str, user: User,
                                      role: str, max_uses: int = None,
                                      expires_in_days: int = None) -> InvitationLink: ...
        # Nur mit Verwaltung, gibt Link + Token zurück
    async def accept_invitation(self, token: str, user: User) -> Membership: ...
        # Validiert Token, erstellt Membership, erhöht use_count
    async def revoke_invitation(self, tenant_key: str, user: User,
                                 invitation_key: str) -> Invitation: ...
        # Nur mit Verwaltung, setzt status → revoked
    async def list_invitations(self, tenant_key: str, user: User) -> list[Invitation]: ...
        # Nur mit Verwaltung

    # --- Standort-Zuweisungen ---
    async def assign_location(self, tenant_key: str, user: User,
                               location_key: str, target_user_key: str,
                               role: str = 'responsible',
                               valid_from: date = None,
                               valid_until: date = None) -> LocationAssignment: ...
        # Nur mit Verwaltung. Setzt eine ZUSTAENDIGKEIT, kein Recht (§1a.5)
    async def unassign_location(self, tenant_key: str, user: User,
                                 assignment_key: str) -> None: ...
        # Nur mit Verwaltung
    async def list_assignments(self, tenant_key: str, user: User,
                                location_key: str = None,
                                user_key: str = None) -> list[LocationAssignment]: ...
        # Filter nach Location und/oder User
```

### 3.3 Tenant-Context-Middleware

Jeder API-Request im Tenant-Kontext enthält den Tenant im URL-Pfad:

```python
async def get_current_tenant(
    tenant_slug: str = Path(...),
    user: User = Depends(get_current_user),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> TenantContext:
    """Extrahiert Tenant aus URL, prüft Membership.
    Gibt TenantContext zurück mit: tenant, membership, role.
    Wirft 403 wenn User nicht Mitglied ist."""

def require_tenant_role(min_role: TenantRole):
    """Achse 1 — Mindestrang der fachlichen Rolle (REQ-049 §2.3).
    require_tenant_role(TenantRole.LEAD)   → nur Leitung
    require_tenant_role(TenantRole.GROWER) → Leitung und Gärtner
    require_tenant_role(TenantRole.VIEWER) → alle Rollen"""

def require_admin_scope(scope: AdminScope):
    """Achse 2 — administrative Zusatzberechtigung (REQ-049 §2.4).
    Unabhängig vom Rang: ein Beobachter mit `management` besteht,
    eine Leitung ohne `management` nicht. Disjunkt zu Achse 1 —
    eine Aktion darf nie über beide erreichbar sein (§1a.6)."""

def require_permission(resource: ResourceType | str, action: Action):
    """Achse 1 je Ressource — delegiert an die MembershipEngine (§1a.6)."""
```

### 3.4 Tenant-scoped API-Routing

Alle bestehenden Ressourcen-Endpunkte werden unter einen Tenant-Prefix verschoben:

```
/api/v1/t/{tenant_slug}/sites/...
/api/v1/t/{tenant_slug}/plant-instances/...
/api/v1/t/{tenant_slug}/planting-runs/...
/api/v1/t/{tenant_slug}/tasks/...
/api/v1/t/{tenant_slug}/harvest-batches/...
/api/v1/t/{tenant_slug}/tanks/...
/api/v1/t/{tenant_slug}/fertilizers/...
/api/v1/t/{tenant_slug}/nutrient-plans/...
/api/v1/t/{tenant_slug}/inspections/...
...
```

Globale Ressourcen bleiben unter dem bestehenden Pfad:
```
/api/v1/botanical-families/...     (global, read-only für alle authentifizierten User)
/api/v1/species/...                 (global)
/api/v1/cultivars/...               (global)
/api/v1/pests/...                   (global, IPM-Stammdaten)
/api/v1/diseases/...                (global)
/api/v1/treatments/...              (global)
```

**Router: `/api/v1/tenants`** — Tenant-Verwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/tenants` | Eigene Tenants auflisten | Ja |
| POST | `/tenants` | Neuen Org-Tenant erstellen | Ja |
| GET | `/tenants/{slug}` | Tenant-Details abrufen | Alle Rollen |
| PATCH | `/tenants/{slug}` | Tenant aktualisieren | Verwaltung |
| DELETE | `/tenants/{slug}` | Tenant löschen (Erasure über das Mandanten-Löschinventar, #1769 — **kein** Soft-Delete, Nachführung #1790); Körper `{confirm_slug, password?}`. Antwortet **`202 Accepted`** (Körper `{tenant_key, status, requested_at, message}`): die Löschung ist angenommen und der Mandant eingefroren, ausgeführt wird sie danach asynchron über Celery-Batches (Q-O1, #1792, Breaking Change gegenüber `200` — siehe §1a.2) | Verwaltung **und** Leitung + Step-up (§1a.2) |

**Router: `/api/v1/tenants/{slug}/members`** — Mitgliederverwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/tenants/{slug}/members` | Mitglieder auflisten | Alle Rollen |
| PATCH | `/tenants/{slug}/members/{user_key}` | Rolle ändern | Verwaltung |
| DELETE | `/tenants/{slug}/members/{user_key}` | Mitglied entfernen | Verwaltung |
| POST | `/tenants/{slug}/leave` | Tenant verlassen | Alle Rollen |

**Router: `/api/v1/tenants/{slug}/invitations`** — Einladungen:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/tenants/{slug}/invitations` | Einladungen auflisten | Verwaltung |
| POST | `/tenants/{slug}/invitations/email` | E-Mail-Einladung senden | Verwaltung |
| POST | `/tenants/{slug}/invitations/link` | Einladungslink generieren | Verwaltung |
| DELETE | `/tenants/{slug}/invitations/{key}` | Einladung widerrufen | Verwaltung |
| POST | `/invitations/accept` | Einladung annehmen (Token im Body) | Ja |

**Router: `/api/v1/t/{tenant_slug}/assignments`** — Standort-Zuweisungen:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/t/{slug}/assignments` | Zuweisungen auflisten (Filter: location, user) | Alle Rollen |
| POST | `/t/{slug}/assignments` | Zuweisung erstellen | Verwaltung |
| PATCH | `/t/{slug}/assignments/{key}` | Zuweisung aktualisieren | Verwaltung |
| DELETE | `/t/{slug}/assignments/{key}` | Zuweisung entfernen | Verwaltung |

**Gesamtanzahl neue API-Endpunkte:** ~18

### 3.5 Bestehende Repositories erweitern

Alle bestehenden Repositories erhalten eine Tenant-Filterung:

```python
class SiteRepository:
    async def list_by_tenant(self, tenant_key: str) -> list[Site]: ...
    async def create(self, site: Site, tenant_key: str) -> Site: ...
        # Setzt tenant_key, erstellt belongs_to_tenant-Edge

class PlantInstanceRepository:
    async def list_by_tenant(self, tenant_key: str) -> list[PlantInstance]: ...
    # ... analog für alle tenant-scoped Collections
```

### 3.6 Celery-Tasks

| Task | Schedule | Beschreibung |
|------|----------|-------------|
| `cleanup_expired_invitations` | Täglich 02:00 | Setzt abgelaufene Einladungen auf `status: expired` |
| `cleanup_inactive_memberships` | Wöchentlich | Warnung per E-Mail bei Memberships ohne Login > 90 Tage |
| `retention.run_account_erasure` (`app.tasks.retention_tasks`) <!-- #1949 --> | Bei `202`-Annahme einer Konto-Löschung durch einen Plattform-Admin (`apply_async`); Auffangnetz: der tägliche `retention.execute_scheduled_erasures` (der Auftrag ist sofort fällig) | Beansprucht den Löschauftrag atomar (`claim_for_run`), löscht Objektspeicher, die persönlichen Mandanten in begrenzten Stapeln mit Heartbeat (siehe `run_tenant_erasure`) und führt den ArangoDB-Plan des Kontos aus; Fehler werden am Auftrag als `partially_completed` vermerkt (Backoff), nie geworfen |
| `run_tenant_erasure` (`app.tasks.tenant_tasks`) <!-- Q-O1, #1792 --> | Bei `202`-Annahme einer Mandantenlöschung (`.delay`); Auffangnetz: der tägliche `resume_tenant_erasures` (04:30 UTC) beansprucht einen Nachweis ohne frischen Heartbeat | Beansprucht den Nachweis atomar (`claim_for_run`), löscht den eingefrorenen Mandanten in begrenzten, idempotenten Stapeln zu je 1000 Zeilen (eine Transaktion je Stapel), schreibt zwischen den Stapeln einen Heartbeat (`heartbeat`, bedingt auf den eigenen Claim-Stempel) und eskaliert ab dem 3. erfolglosen Versuch (`tenant_erasure.escalated`, `escalated_at`); Fehler werden am Nachweis vermerkt, nie geworfen (§1a.2) |

## 4. Frontend

### 4.1 Neue Seiten

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| `TenantCreatePage` | `/tenants/create` | Neuen Org-Tenant erstellen |
| `TenantSettingsPage` | `/t/{slug}/settings` | Tenant-Name, Beschreibung, Avatar |
| `MemberListPage` | `/t/{slug}/members` | Mitglieder auflisten, Rollen verwalten |
| `InvitationListPage` | `/t/{slug}/invitations` | Einladungen verwalten |
| `InvitationAcceptPage` | `/invitations/accept/:token` | Einladung annehmen |
| `AssignmentListPage` | `/t/{slug}/assignments` | Standort-Zuweisungen verwalten |

### 4.2 Komponenten

**`TenantSwitcher`** — Tenant-Wechsel in der App-Bar:
- Dropdown in der oberen Navigationsleiste
- Zeigt alle Tenants des Users mit Rolle und Typ-Icon
- Aktiver Tenant hervorgehoben
- "Neuen Garten erstellen"-Button am Ende der Liste
- Speichert zuletzt aktiven Tenant in `localStorage`

**`MemberListPage`:**
- DataTable mit Spalten: Avatar, Name, Rolle (Chip), Beigetreten-am
- Rollen-Änderung per Dropdown (nur für Admins sichtbar)
- "Mitglied entfernen"-Button mit Bestätigungs-Dialog
- "Einladen"-Button → öffnet `InviteDialog`

**`InviteDialog`:**
- **Tab "Per E-Mail":** E-Mail-Eingabe + Rollen-Auswahl → sendet Einladungs-E-Mail
- **Tab "Per Link":** Rollen-Auswahl + optionale Einschränkungen (max. Nutzungen, Ablaufdatum) → generiert kopierbaren Link

**`AssignmentListPage`:**
- Matrix-Darstellung: Locations als Zeilen, Mitglieder als Spalten
- Drag-and-Drop oder Click-to-Assign für Zuweisung
- Farbcodierung: Zugewiesen (grün), Gemeinschaft (blau), Nicht zugewiesen (grau)
- Saisonale Filter (Datum-Range)

**`TenantBadge`** — Kleine visuelle Indikatoren:
- Zeigt die fachliche Rolle als Chip (Leitung: rot, Gärtner: grün, Beobachter: grau) und die Zusatzberechtigungen als eigene, kleinere Chips — beide Achsen bleiben auch in der Anzeige getrennt
- Zeigt Tenant-Typ-Icon (Haus = persönlich, Gruppe = Organisation)

### 4.3 URL-Struktur

Alle tenant-scoped Seiten erhalten den Tenant-Slug als URL-Prefix:

```
/t/{slug}/dashboard              → Tenant-Dashboard
/t/{slug}/sites                   → Standorte dieses Tenants
/t/{slug}/plant-instances         → Pflanzen dieses Tenants
/t/{slug}/tasks                   → Aufgaben dieses Tenants
/t/{slug}/members                 → Mitglieder (nur für Admins vollständig)
/t/{slug}/settings                → Tenant-Einstellungen (nur Admins)
/t/{slug}/invitations             → Einladungen (nur Admins)
/t/{slug}/assignments             → Standort-Zuweisungen (nur Admins)
```

### 4.4 Tenant-Context in Redux

```typescript
interface TenantState {
  activeTenant: TenantWithRole | null;
  myTenants: TenantWithRole[];
  isLoading: boolean;
}

interface TenantWithRole {
  key: string;
  name: string;
  slug: string;
  type: 'personal' | 'organization';
  role: 'viewer' | 'grower' | 'lead';
  adminScopes: Array<'management' | 'technical'>;
  memberCount: number;
}

// Thunks:
// loadMyTenants() → setzt myTenants
// switchTenant(slug) → setzt activeTenant, aktualisiert URL
// createOrganization(name, description) → erstellt Tenant, fügt zu myTenants hinzu
```

### 4.5 Berechtigungs-Hooks

Die Hooks bilden die **zwei Achsen** ab und **kein** Ressourcenargument. Ein
`useCanEditLocation(locationKey)` gab es bis v1.6 und ist mit der zuweisungsbasierten
Write-Kontrolle entfallen (§1a.5): Es gibt keine Location im Mandanten, die ein Gärtner nicht
bearbeiten darf, also auch keine Frage, die der Hook beantworten könnte. Wer ihn behält, baut die
gestrichene Regel im Client nach — und der Server widerspricht ihm nicht, weil er sie gar nicht
mehr kennt.

Die Hooks sind **Anzeigehilfen, keine Autorisierung.** Sie entscheiden, ob ein Knopf erscheint;
abgewiesen wird serverseitig (§1a.6).

```typescript
function useTenantPermissions(): TenantPermissions {
  // Achse 1 — fachliche Rolle, KEIN Ressourcen- oder Zuweisungsargument:
  //   canEdit: boolean          // Leitung oder Gärtner
  //   canDelete: boolean        // nur Leitung
  //   isGrowerOrAbove: boolean
  //   isLead: boolean
  // Achse 2 — Zusatzberechtigungen, unabhängig vom Rang:
  //   hasManagement: boolean    // Mitglieder, Einladungen, Zuweisungen, Einstellungen
  //   hasTechnical: boolean     // HA/MQTT/Sensorik/Import/Wetterquellen
}
```

## 5. Seed-Daten

### Demo-Tenant (Nur Entwicklungsumgebung):

```json
{
  "tenants": [
    {
      "name": "Demo-Garten",
      "slug": "demo-garten",
      "type": "personal",
      "description": "Persönlicher Garten des Demo-Users",
      "status": "active"
    },
    {
      "name": "Gemeinschaftsgarten Sonnenschein",
      "slug": "gemeinschaftsgarten-sonnenschein",
      "type": "organization",
      "description": "Demo-Gemeinschaftsgarten mit 3 Parzellen und Gemeinschaftsfläche",
      "max_members": 20,
      "status": "active"
    }
  ],
  "memberships": [
    {
      "_user": "demo@kamerplanter.local",
      "_tenant": "demo-garten",
      "role": "lead",
      "admin_scopes": ["management", "technical"]
    },
    {
      "_user": "demo@kamerplanter.local",
      "_tenant": "gemeinschaftsgarten-sonnenschein",
      "role": "lead",
      "admin_scopes": ["management", "technical"]
    },
    {
      "_user": "demo@kamerplanter.local",
      "_tenant": "platform",
      "role": "lead",
      "admin_scopes": ["management", "technical"],
      "_comment": "Demo-User ist auch KA-Admin (Leitung im Platform-Tenant, REQ-049 §2.5)"
    }
  ]
}
```

<!-- Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->
### 5.2 Platform-Tenant Seed-Daten

Der Platform-Tenant wird beim ersten App-Start automatisch erstellt (idempotent):

```python
PLATFORM_TENANT = Tenant(
    key="platform",
    name="Kamerplanter Admin",
    slug="platform",
    type="organization",
    is_platform=True,
    description="Plattform-Administration: Globale Stammdaten, Tenant-Zuweisungen",
    status="active",
    max_members=999,  # gespeichert; wirksam gekappt auf TENANT_MAX_MEMBERS_CEILING (AK-64)
    settings={"auto_assign_master_data": True},
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
)
```

**Seed-Logik:**
- Wird in `seed_initial_data()` erstellt (beide Modi: light + full)
- Idempotent: Doppelter Aufruf erzeugt keine Duplikate
- Im Light-Modus: System-User erhält automatisch eine Membership mit `role: lead` und beiden Zusatzberechtigungen im Platform-Tenant
- Im Full-Modus: Der erste Betreiber sollte manuell als Platform-Admin (`role: lead` im Platform-Tenant) hinzugefügt werden (oder über Environment Variable `KAMERPLANTER_INITIAL_ADMIN_EMAIL` beim ersten Start)

### 5.3 Auto-Assign Seed-Logik

Bei `auto_assign_master_data=true` (Default) werden bei Tenant-Erstellung automatisch `tenant_has_access`-Kanten für alle globalen Stammdaten erstellt:

```python
def auto_assign_all_master_data(tenant_key: str, db: StandardDatabase) -> int:
    """Erstellt tenant_has_access-Kanten für alle globalen Stammdaten.
    Gibt die Anzahl erstellter Kanten zurück."""
    edge_col = db.collection("tenant_has_access")
    count = 0
    for collection_name in ["species", "pests", "diseases", "treatments", "fertilizers", "nutrient_plans"]:
        col = db.collection(collection_name)
        for doc in col.find({"tenant_key": None}):  # Nur globale Einträge
            edge_key = f"{doc['_key']}__{tenant_key}"
            if not edge_col.has(edge_key):
                edge_col.insert({
                    "_key": edge_key,
                    "_from": f"{collection_name}/{doc['_key']}",
                    "_to": f"tenants/{tenant_key}",
                    "assigned_at": datetime.now(UTC).isoformat(),
                    "assigned_by": None,
                })
                count += 1
    return count
```
<!-- /Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->

## 6. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Bei Registrierung (REQ-023) wird automatisch ein persönlicher Tenant (`type: personal`) erstellt | Integration |
| AK-02 | User kann maximal 10 organisatorische Tenants erstellen | Unit + Integration |
| AK-03 | Tenant-Slug wird URL-sicher generiert (Umlaute, Sonderzeichen korrekt) | Unit |
| AK-04 | User kann zwischen Tenants wechseln ohne Neuanmeldung | E2E |
| AK-05 | Ein User kann in Tenant A Leitung und in Tenant B Beobachter sein; die Zusatzberechtigungen werden je Mandant getrennt geführt | Integration |
| AK-06 | E-Mail-Einladung sendet E-Mail und erstellt bei Annahme korrekte Membership | Integration |
| AK-07 | Einladungslink mit `max_uses: 5` wird nach 5 Nutzungen ungültig | Integration |
| AK-08 | Einladungslink mit `expires_at` wird nach Ablauf ungültig | Integration |
| AK-09 | OIDC-Provider mit `default_tenant_key` weist neue User automatisch dem Tenant zu | Integration |
| AK-10 | Das letzte Mitglied mit der Zusatzberechtigung **Verwaltung** kann weder entfernt noch dieser Berechtigung entzogen werden (INV-1). Der Anker ist die Verwaltung, **nicht** die Rolle Leitung: Ein Mandant ohne Leitung ist bedienbar, ein Mandant ohne Verwaltung ist verwaist (REQ-023 §5a.5) | Unit + Integration |
| AK-11 | Ein Gärtner sieht **und bearbeitet** alle Locations des Mandanten — zugewiesene wie fremde. Löschen gelingt ihm bei keiner (REQ-049 §2.3, §3.5) | Integration |
| AK-12 | Ein Beobachter kann keine Ressource des Mandanten erstellen, ändern oder löschen | Integration |
| AK-13 | Die Leitung sieht, bearbeitet **und löscht** alle Ressourcen des Mandanten | Integration |
| AK-14 | Ressourcen eines Tenants sind für Nicht-Mitglieder unsichtbar (kein Cross-Tenant-Zugriff) | Integration |
| AK-15 | Eine `LocationAssignment` außerhalb von `valid_from`/`valid_until` verschwindet aus Anzeige und Vorsortierung und verändert **keine** Berechtigung (siehe AK-43) | Unit |
| AK-16 | **Tenant-Löschung läuft über das Mandanten-Löschinventar, kein Soft-Delete (nachgeführt #1790, war bis v1.8 als Soft-Delete beschrieben; v1.23 #2123):** Jede mandantenbezogene Collection wird über die deklarierte Inventarliste (#1769) gelöscht, aufbewahrungspflichtige Zeilen (R-16..R-18) bleiben bis zu ihrem ursprünglichen Fristende pseudonymisiert erhalten (NFR-011 §2.3, Q-R1), und ein `tenant_erasure_records`-Nachweis wird angelegt. Seit v1.23 geht der Löschung die Gnadenfrist AK-52 voraus: Der Zustand `pending_deletion` sperrt den Mandanten, die Memberships werden erst deaktiviert, wenn der Lauf den Nachweis nach Fristablauf beansprucht (`status: deleted` für die Dauer des Laufs — das Mandantendokument selbst entfernt das Inventar) | Integration |
| AK-17 | Task-Zuweisung (`assigned_to`) im Tenant-Kontext: nur Mitglieder des Tenants wählbar | Integration |
| AK-18 | Persönlicher Tenant ist für andere User unsichtbar | Integration |
<!-- Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->
| AK-19 | Platform-Tenant (`is_platform: true`) wird beim App-Start automatisch erstellt (idempotent) | Integration |
| AK-20 | `is_platform: true` kann nur auf dem Platform-Tenant gesetzt sein — reguläre Tenants lehnen `is_platform=true` ab | Unit |
| AK-21 | Bei Tenant-Erstellung mit `auto_assign_master_data=true` werden `tenant_has_access`-Kanten für alle globalen Stammdaten automatisch erstellt | Integration |
| AK-22 | `tenant_has_access`-Kanten werden für Species, Pests, Diseases, Treatments, Fertilizers, NutrientPlans erstellt | Integration |
| AK-23 | Cultivars sind transitiv sichtbar — keine eigenen `tenant_has_access`-Kanten | Unit |
| AK-24 | BotanicalFamilies bleiben ungefiltert (kein `tenant_has_access`) | Unit |
| AK-25 | Ab der Rolle Gärtner können mandanteneigene Pests, Diseases, Treatments, Fertilizers und NutrientPlans angelegt werden (`origin: 'tenant'`); löschen kann sie nur die Leitung | Integration |
| AK-26 | Tenant-eigene Stammdaten sind für andere Tenants unsichtbar | Integration |
| AK-27 | KA-Admin kann Tenant-eigene Stammdaten zu global promoten (in-place: `origin` → `'system'`, `tenant_key` → `null`) | Integration |
| AK-28 | Der Demo-User trägt im Platform-Tenant `role: lead` mit beiden Zusatzberechtigungen | Seed-Validation |
<!-- /Quelle: Platform-Tenant & Stammdaten-Scoping v1.3 -->
<!-- Quelle: RBAC Permission-Matrix v1.4 -->
| AK-29 | Rolle **Leitung** besteht `can_edit_resource` **und** `can_delete_resource`; die Zusatzberechtigungen bleiben davon unberührt (eine Leitung ohne `management` verwaltet keine Mitglieder) | Unit |
| AK-30 | Rolle **Gärtner** besteht `can_edit_resource`, aber **nicht** `can_delete_resource` — an **jeder** Fachressource des Mandanten, unabhängig von der Zuweisung. Die **Autorschaft** ist davon nicht berührt: Sie ist keine Rollenfrage und wird nicht von diesem Prädikat entschieden, sondern zusätzlich am Dienst geprüft, dort wo REQ-049 §3.1 sie zulässt — bei **verfassten Inhalten** (Pinnwand-Beiträge und Kommentare, AK-35; Tagebuch-Einträge, REQ-051 §3.2). Für Fachdaten gibt es keine Autorschafts-Schranke | Unit + Integration |
| AK-31 | Rolle **Beobachter** besteht ausschließlich `can_view_resource`; jeder Schreib- und Löschversuch endet in `403` | Unit |
| AK-32 | Ein Gärtner kann eine Aufgabe bearbeiten und ihren Status ändern, die **einem anderen Mitglied** zugewiesen ist. Ein Test, der das Gegenteil erwartet, prüft die mit REQ-049 §3.5 gestrichene Regel | Integration |
| AK-33 | Aufgaben **zuweisen** (`assigned_to` setzen) gelingt nur der Leitung | Integration |
| AK-34 | Pinnwand-Posts **pinnen** gelingt nur der Leitung | Integration |
| AK-35 | Ein Gärtner kann **eigene** Pinnwand-Posts löschen, die Leitung alle. Das ist die eine dokumentierte Ausnahme von der Irreversibilitätsgrenze: REQ-049 §3.1 lässt „Eigene" ausdrücklich für **verfasste Inhalte** (Pinnwand-Beiträge, Kommentare) zu und verbietet es nur für Fachdaten. Ein Beitrag ist die Äußerung seines Verfassers, kein Datensatz über die Pflanze | Integration |
| AK-36 | `require_permission(resource, action)` antwortet `403` mit klarer Meldung; eine Rolle, auf die keine Regel passt, wird abgewiesen (fehl-geschlossen), nicht durchgelassen | Unit + Integration |
| AK-37 | Alle drei Wächter verhalten sich identisch für `account_type: 'human'` und `'service'` | Integration |
| AK-38 | Platform-Viewer (`viewer` im Platform-Tenant) kann das Admin-Panel read-only sehen, aber keine Daten ändern | Integration |
| AK-39 | Platform-Viewer kann keine `tenant_has_access`-Kanten erstellen oder löschen | Integration |
| AK-40 | Platform-Viewer kann keine Species promoten oder globale Stammdaten ändern | Integration |
| AK-41 | **Die Standort-Zuweisung wirkt nicht auf Schreibrechte:** Ein Gärtner bearbeitet eine Location, die einem anderen Mitglied zugewiesen ist, erfolgreich. Ein `403` an dieser Stelle ist ein Fehlschlag des Kriteriums | Integration |
| AK-42 | **`can_edit_resource` nimmt keine Zuweisungen entgegen.** Ein Test weist die **Abwesenheit** eines solchen Parameters in der Signatur nach — wird er wieder eingeführt, ist die gestrichene Regel zurück, ohne dass ein Verhaltenstest anschlägt | Unit |
| AK-43 | Eine `LocationAssignment` mit abgelaufenem `valid_until` verändert **keine** Berechtigung; sie verschwindet lediglich aus der Ansicht „meine Parzelle" und aus der Vorsortierung | Unit + Integration |
| AK-44 | Ein Dienstkonto mit Rolle `grower` hat dieselben Zugriffsmuster wie ein menschlicher Gärtner — insbesondere Schreibzugriff auf **alle** Fachdaten des Mandanten und **kein** Löschrecht | Integration |
| AK-44a | Ein Mitglied mit `role: viewer` und `admin_scopes: ['management']` kann Mitglieder einladen und Rollen ändern, aber keine Pflanze anlegen. Ein Mitglied mit `role: lead` ohne `management` kann löschen, aber keine Mitglieder verwalten. Damit ist die Unabhängigkeit der beiden Achsen nachgewiesen | Integration |
| AK-44b | Kein Router gatet eine administrative Aktion über `require_permission`/`require_tenant_role` oder eine fachliche über `require_admin_scope`. Ein statischer Test über die Router-Signaturen weist das nach — ein Mitglied mit `lead` + beiden Zusatzberechtigungen käme sonst durch beide Wächter und der Fehler bliebe unsichtbar | Unit |
| AK-44c | Die beschreibende Matrix in `app/core/permissions.py` stimmt mit §1a.1 überein; insbesondere ist das Löschrecht der Pflanzendomäne dort auf Leitung beschränkt. Ein Test vergleicht beide Quellen, statt sie unabhängig zu pflegen | Unit |
| AK-44d | **Mandant löschen (#1791):** Über `DELETE /tenants/{slug}` löscht nur ein aktives Mitglied mit Rolle **Leitung und** Zusatzberechtigung **Verwaltung**; Beobachter oder Gärtner mit Verwaltung, eine Leitung ohne Verwaltung jedes Dienstkonto und jede per API-Schlüssel authentifizierte Anfrage erhalten `403`. Fehlt der Kurzname oder ist er falsch → `422`; fehlt bei einem Konto mit lokalem Passwort das Passwort oder ist es falsch → `401`; ein föderiertes Konto bestätigt über den Kurznamen allein. In keinem abgelehnten Fall wird ein Löschnachweis angelegt oder eine Zeile gelöscht. Der Plattform-Admin-Weg verlangt denselben Step-up. Der Löschnachweis nennt den Step-up und den Anfragenden nur als salzgehashte Referenz | Unit (Route) + Integration |
<!-- /Quelle: RBAC Permission-Matrix v1.4 -->
<!-- Quelle: Tenant-Notfallverwaltung v1.4 -->
| AK-45 | Der Platform-Admin kann die Mitgliederliste eines fremden Mandanten einsehen — die einzige Cross-Tenant-Leseerlaubnis der Plattform-Ebene | Integration |
| AK-46 | Platform-Viewer kann Mitgliederliste eines fremden Tenants read-only einsehen | Integration |
| AK-47 | Suspendierter Tenant: TenantSwitcher zeigt Tenant ausgegraut mit Hinweis "Suspendiert" | E2E |
| AK-48 | **Deaktivierter Tenant sperrt aus (#2105, umgesetzt v1.22):** Ein Mandant mit `is_active=false` wird für kein Mitglied aufgelöst: `/t/{slug}/…` und `X-Active-Tenant` antworten mit **derselben** `403` wie für einen unbekannten Slug (die frühere Forderung „klare Fehlermeldung“ ist damit bewusst ersetzt — eine eigene Meldung wäre ein Existenz-Orakel); ohne Header fällt ein deaktivierter persönlicher Mandant auf den globalen Katalog zurück; MCP führt den Mandanten nicht in `list_tenants`, ein Werkzeugaufruf mit seinem Slug antwortet `not_found`. Reaktivieren stellt den Zugriff mit unveränderter Rolle wieder her. Die Plattform-Administration (`/admin/platform/…`) erreicht den Mandanten weiterhin. Test: `tests/integration/test_inactive_tenant_resolution_reach.py`. | Integration |
| AK-49 | Notfall-Admin ernennen, Tenant und User suspendieren und reaktivieren gelingt ausschließlich dem Platform-Admin (`lead` im Platform-Tenant) | Unit |
| AK-50 | Der Platform-Viewer darf Mitgliederlisten fremder Mandanten **lesen** — das ist die einzige Cross-Tenant-Leseerlaubnis der Rolle | Unit |
| AK-51 | Der Platform-Viewer kann weder einen Notfall-Admin ernennen noch Mandanten oder Nutzer suspendieren | Unit |
<!-- /Quelle: Tenant-Notfallverwaltung v1.4 -->
<!-- Quelle: #1790, Betreiberentscheidung Q-O2 -->
| AK-52 | **Gnadenfrist für die Mandantenlöschung (Q-O2, #1790; entschieden und umgesetzt v1.23, #2123):** `DELETE /tenants/{slug}` markiert den Mandanten zur Löschung vor (`pending_deletion`, `deletion_scheduled_at`) und führt das Mandanten-Löschinventar erst nach der Gnadenfrist `RETENTION_TENANT_ERASURE_GRACE_DAYS` (NFR-011 R-01b; **Betreiberentscheidung 2026-10-04: 90 Tage** wie R-01, Untergrenze 0 für Self-Hosted, Obergrenze 90) tatsächlich aus; innerhalb der Frist kann ein Mitglied mit Verwaltung **und** Leitung (oder ein Plattform-Admin) die Löschung mit Step-up widerrufen (`POST /tenants/{slug}/erasure/cancel`). Alle Mitglieder werden mit dem Datum benachrichtigt (Art.-20-Exportfenster über den persönlichen Export). Tests: `tests/unit/domain/services/test_tenant_erasure_grace.py`, `tests/integration/test_v0085_tenant_status_model.py`. | Unit + Integration |

    !!! warning "Noch nicht implementiert"
        `TenantService.delete_tenant` löscht heute sofort, ohne Gnadenfrist und ohne
        Widerrufsmöglichkeit. Diese Anforderung ist eine bewusste Betreiberentscheidung
        (2026-09-26) für ein künftiges Implementierungs-Issue, keine Beschreibung des
        Ist-Zustands.
<!-- /Quelle: #1790 -->
<!-- Quelle: Datenschutzplan Q-O1, #1792 -->
| AK-53 | **Umgesetzt (v1.11, #1792; seit v1.23 hinter der Gnadenfrist AK-52, #2123):** Nach Ablauf der AK-52-Gnadenfrist (mit Frist 0: nach Annahme) antworten `DELETE /tenants/{slug}` und `DELETE /admin/platform/tenants/{key}` mit `202 Accepted`, der Mandant ist eingefroren (Memberships deaktiviert, Löschnachweis angelegt), und ein Celery-Task führt das Mandanten-Löschinventar in begrenzten, idempotenten Batches mit fortlaufendem Heartbeat aus. Ein deterministisch scheiternder Batch eskaliert nach N = 3 Versuchen (`TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS`), statt täglich lautlos zu wiederholen. Dies ist eine brechende API-Änderung gegenüber dem bis v1.10 synchronen `200`/`204`-Vertrag (§1a.2, §3.6). | Unit (`test_tenant_erasure_async.py`, `test_tenant_delete_authorization.py`) + Integration (`test_tenant_erasure_batches.py`, `test_tenant_erasure_reach.py`) |
<!-- /Quelle: Datenschutzplan Q-O1, #1792 -->
<!-- Quelle: Datenschutzplan Q-L1/Q-L2, #1805 -->
| AK-54 | Eine Migration setzt v0004-Altstempel auf globalen Seed-Zeilen von `fertilizers`, `nutrient_plans` und `task_templates` auf `tenant_key == ""` zurück (Form wie `v0036`/`v0038`); ihre Vorab-Prüfung läuft ausschließlich gegen einen Dev-Cluster oder ein wiederhergestelltes Backup, nie gegen die Produktionsdatenbank direkt; ein Task-Template eines erhaltenen System-Workflows wird mit ihm zurückgesetzt | Integration |
<!-- /Quelle: Datenschutzplan Q-L1/Q-L2, #1805 -->
<!-- Quelle: Datenschutzplan Q-L3, #1878 -->
| AK-55 | **Umgesetzt (v1.13, #1878; Migration `v0067`, Test `test_v0067_clean_legacy_foreign_references.py`):** Ein geteiltes globales Template mit dem Namen einer privaten Species wird der aktuellen Eigentümerin dieser Species als privates Template zugeordnet; eine fremde Kante aus den #1871-Lücken wird bei eindeutigem Ziel auf den korrekten Mandanten umgehängt, sonst gelöscht; die Korrektur-Migration ist idempotent und protokolliert nur Anzahlen | Integration |
| AK-65 | **Mandanten-Lebenszyklus (v1.24, #2123):** Ein Mandant hat genau einen Zustand `active`, `suspended` (Plattform-Admin-Schalter, AK-56), `pending_deletion` (Löschung geplant, AK-52), `orphaned` (nach einer Kontolöschung verwaltet ihn niemand mehr, REQ-025 §3.1.3, #2134 — läuft in dieselbe Gnadenfrist) oder `deleted` (Frist abgelaufen, Inventar läuft, nicht mehr abbrechbar). Nur `active` wird aufgelöst; alle anderen antworten wie AK-48. Der Admin-Schalter wechselt nur zwischen `active` und `suspended`; aus `pending_deletion`/`orphaned` führt nur der Abbruch (zurück zu `active`) oder der Fristablauf (`deleted`). Das Admin-Panel zeigt den Zustand und das Löschdatum. | Unit + Integration |
| AK-56 | **Step-up für Admin-Eingriffe in Mandanten (Betreiberentscheidung #2009, umgesetzt):** Das Deaktivieren eines Mandanten und das Entfernen eines Mitglieds durch einen Plattform-Admin verlangen wie die übrigen Admin-Löschpfade (#2011) einen Step-up des handelnden Admins (REQ-023 §3.9); ohne gültigen Step-up bleibt der Zustand unverändert (401). Die **Wirkung** der Deaktivierung hält AK-48 (#2105). | Integrationstest |
| AK-57 | **Step-up für Rollenwechsel und Entfernen eines Mitglieds (Betreiberentscheidung #2032, umgesetzt):** Eine tatsächliche Änderung der Rolle einer Mitgliedschaft (`PATCH /admin/platform/tenants/{tenant_key}/members/{membership_key}/role`, `PATCH /admin/platform/users/{user_key}/memberships/{membership_key}/role`, `PATCH /tenants/{slug}/members/{membership_key}/role`) und das Entfernen eines Mitglieds über `DELETE /tenants/{slug}/members/{membership_key}` verlangen den Step-up des **handelnden** Kontos (REQ-023 §3.9; Aktionen `admin_membership_role_change`, `tenant_member_role_change`, `tenant_member_removal`, gebunden an den Schlüssel der Mitgliedschaft, #1884); ohne gültigen Step-up bleibt der Zustand unverändert (401), ein API-Key-Aufruf ist 403, eine Sperre 429 `STEP_UP_LOCKED`. Die Prüfung läuft im Service (`TenantService`), beide Admin-Sichten und der Mandanten-Pfad teilen sie. Der Mandanten-Pfad prüft zuerst den Verwaltungsbereich (403), die Zugehörigkeit zum Mandanten (404) und INV-1 (422), dann den Step-up. Ein Faktor wird nur für eine Mitgliedschaft des eigenen Mandanten ausgestellt, in dem das Konto `management` hält (403 für eine unbekannte und eine fremde Mitgliedschaft gleichermaßen). `DELETE /tenants/{slug}/assignments/{key}` ist **kein** Step-up-Akt. | Integrationstest |
| AK-58 | **Rollen-Eskalation (#2078, umgesetzt):** Über `PATCH /tenants/{slug}/members/{membership_key}/role` erhöht niemand die Rolle der **eigenen** Mitgliedschaft (403, auch mit gültigem Step-up; Herabstufen und unveränderter Wert bleiben möglich). Im Mandanten `platform` vergibt `lead` — per Rollenwechsel und über `POST /tenants/platform/invitations/email|link` — nur ein dort aktives Mitglied mit der Rolle `lead` (403, kein Schreibzugriff, kein Einladungsdatensatz). Außerhalb von `platform` darf die Verwaltung weiterhin jede Rolle vergeben (REQ-049 §2.4; Vorschlag, Betreiberprüfung offen, s. v1.20). Jede Dienstfunktion, die eine Rolle an Mitgliedschaft oder Einladung schreibt, ruft `_refuse_role_grant` oder ist begründet klassifiziert (Guard `test_membership_role_grants_check_for_escalation.py`). | Integrationstest (`test_member_role_escalation_reach.py`) + Unit |
| AK-59 | **Step-up für das Hinzufügen eines Mitglieds (#2106, umgesetzt):** `POST /admin/platform/tenants/{tenant_key}/members` und `POST /admin/platform/users/{user_key}/memberships` verlangen den Step-up des Administrators (`current_password`, oder `step_up_token` / `step_up_code` für `admin_membership_add`, gebunden an `<tenant_key>|<user_key>`): 401 ohne, 403 aus einem API-Schlüssel, 429 `STEP_UP_LOCKED`; ohne gültigen Step-up bleibt der Bestand unverändert. Vor dem Passwort wird abgewiesen, was nicht gelingen kann (unbekannter Mandant 404, Mandant in Löschung 403, bereits Mitglied 409, `lead` in `platform` durch einen, der sie nicht hält 403, ein Plattform-Admin, der sich dem Mandanten `platform` hinzufügt, 422). Beide Admin-Seiten fragen den Step-up beim Hinzufügen ab. | Integrationstest (`test_admin_tenant_step_up_reach.py`) + Unit (`test_admin_membership_add_step_up.py`) + Frontend |
| AK-60 | **Persistentes Sicherheits-Audit (#2111, umgesetzt; Migration `v0082`):** Jede Dienstfunktion, die eine Mitgliedschaft anlegt, ändert oder löscht, schreibt eine Zeile in `security_audit_log` oder ist begründet klassifiziert (Guard `test_membership_mutations_write_the_security_audit.py`); eine fehlschlagende Audit-Zeile wird nicht verschluckt. Aufbewahrung 730 Tage (NFR-011 R-38, Task `security_audit.purge_expired`); bei Kontolöschung werden `actor_user_key` und `target_user_key` zu Tombstone-Hashes, bei Mandantenlöschung bleibt die Zeile. Lesezugriff nur für Plattform-Admins. **Nicht erfasst (Rest von #2111):** Admin-Änderungen an Nutzer (`is_active`, `email_verified`) und Mandant (`is_active`), das Löschen eines Mandanten. | Integrationstest (`test_security_audit_log_reach.py`) + Unit + Guard |
| AK-61 | **E-Mail-Einladung an die Adresse gebunden (#2115, umgesetzt, brechend):** `POST /tenants/invitations/accept` mit einer Einladung vom Typ `email` antwortet 403, wenn das Konto eine andere Adresse trägt, seine Adresse nicht belegt hat (`email_verified` **und** `email_confirmed_at`) oder die Einladung keine Adresse nennt; die Einladung bleibt `pending`, es entsteht keine Mitgliedschaft und keine Audit-Zeile, und die Antwort nennt die eingeladene Adresse nicht. Einladungslinks bleiben für jedes angemeldete Konto gültig. | Integrationstest (`test_email_invitation_address_binding_reach.py`) + Unit |
| AK-62 | **Aufgabenzuweisungen enden mit der Mitgliedschaft (#2114, umgesetzt):** `remove_member`, `admin_remove_membership` und `leave_tenant` löschen `tasks.assigned_to_user_key` des Ex-Mitglieds in diesem Mandanten und nur dort (`ITaskRepository.clear_assignee`); `notifications.dispatch_due_care` und `notifications.send_daily_summary` benachrichtigen nur aktive Mitglieder des Aufgaben-Mandanten, die Tageszusammenfassung wird je (Nutzer, Mandant) gebildet. Jede Dienstfunktion, die eine Mitgliedschaft löscht, ruft `_end_task_assignments` auf oder ist klassifiziert (Guard). | Integrationstest (`test_membership_end_task_assignments_reach.py`) + Unit + Guard |
| AK-63 | **Mandantengründung atomar (#2118, umgesetzt):** `create_personal_tenant` und `create_organization` schreiben Mandant, Gründer-Mitgliedschaft, `has_membership`, `membership_in` und Audit-Zeile in einer Stream-Transaktion (`ITenantRepository.create_with_lead_membership`); ein Fehler bei jedem der fünf Schreibvorgänge hinterlässt keinen Mandanten, kein Mitglied, keine Kante. Die Registrierung (`register_local`, OAuth-Registrierung) nimmt das Konto zurück, wenn Anbieter- oder Mandant-Schreibvorgang scheitert; die Wiederholung ist eine echte Registrierung. Ein Reparatur-Task für Konten ohne persönlichen Mandanten ist **nicht** gebaut (Restfenster: Prozessabbruch zwischen Konto- und Gründungs-Transaktion). | Integrationstest (`test_tenant_founding_atomicity_reach.py`) + Unit |
| AK-64 | **Mitgliederlimit (#2133, umgesetzt, brechend; Betreiberentscheidung 2026-10-04):** Das wirksame Limit eines Mandanten ist `min(max_members, TENANT_MAX_MEMBERS_CEILING)` (Setting, Default 50). Erreichen die aktiven Mitgliedschaften (`is_active != false`) das Limit, antworten Einladungsannahme (`POST /tenants/invitations/accept`) und Plattform-Admin-Hinzufügen (`POST /admin/platform/tenants/{key}/members`, `POST /admin/platform/users/{key}/memberships`) mit `422 MEMBER_LIMIT_REACHED`; nichts wird geschrieben, die Einladung bleibt offen, der Admin wird nicht nach dem Step-up gefragt. Gezählt wird vor und nach dem Einfügen (ein gleichzeitiger Überschuss nimmt sich zurück). `max_members` über der Obergrenze → `422` beim Anlegen und Ändern. Ein Mandant über seinem Limit behält alle Mitglieder. Tests: `test_member_limit_is_enforced.py` (Unit), `test_member_limit_reach.py` (Integration, ArangoDB) | Unit + Integration |
<!-- /Quelle: Datenschutzplan Q-L3, #1878 -->

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | TenantSwitcher zeigt alle Tenants des Users mit korrekter Rolle | E2E |
| FK-02 | Tenant-Wechsel aktualisiert URL (`/t/{slug}/...`) und lädt tenant-spezifische Daten | E2E |
| FK-03 | MemberListPage zeigt je Mitglied den Rollen-Chip **und** die Zusatzberechtigungen getrennt; beide sind für Mitglieder mit `management` einzeln änderbar | E2E |
| FK-04 | InviteDialog generiert funktionierenden Einladungslink | E2E |
| FK-05 | AssignmentListPage zeigt die Matrix Location × Mitglied als **Zuständigkeit**, nicht als Berechtigung; die Oberfläche behauptet an keiner Stelle, eine Zuweisung schränke das Bearbeiten ein | E2E |
| FK-06 | Ohne die Zusatzberechtigung `management` erscheinen Mitgliederverwaltung und Mandanten-Einstellungen nicht — auch nicht für die Rolle Leitung | E2E |
| FK-07 | Beobachter sehen keine Bearbeiten- und Erstellen-Schaltflächen; Gärtner sehen keine Löschen-Schaltflächen | E2E |

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| **REQ-023 v1.7** | Benutzerverwaltung — User-Entität, JWT-Token mit `tenant_roles`, `account_type`, Service Accounts |
| REQ-002 | Standortverwaltung — Site/Location/Slot-Hierarchie für Parzellen-Zuweisung |
| REQ-006 | Aufgabenplanung — Task.assigned_to für Aufgaben-Delegation |
| NFR-001 | Architektur-Layer |
| NFR-006 | API-Fehlerbehandlung (403 FORBIDDEN für fehlende Tenant-Berechtigung) |

### Wird benötigt von:

| REQ | Bezug |
|-----|-------|
| REQ-006 | Task-Zuweisung an Mitglieder (assigned_to als user_key) |
| REQ-015 | Kalenderansicht — Tenant-gefilterte Kalendereinträge |
| Zukünftig | Audit-Log (wer hat was wann in welchem Tenant geändert) |
| Zukünftig | Compliance-Modul (Cannabis-Anbauvereinigungen, CanG) |

### Auswirkung auf bestehende Implementierung:

| Bereich | Änderung |
|---------|---------|
| **Alle Repositories** | `tenant_key`-Filter bei allen Queries, `tenant_key` bei allen Create-Operationen |
| **Alle API-Router** | URL-Prefix `/api/v1/t/{tenant_slug}/...` für tenant-scoped Endpunkte |
| **Alle Frontend-Pages** | URL-Prefix `/t/{slug}/...`, TenantContext in allen Seiten |
| **Redux Store** | Neuer `tenant`-Slice, bestehende Slices um `tenant_key`-Filter erweitern |
| **Seed-Daten** | Bestehende Seed-Daten einem Default-Tenant zuweisen |

## 8. Scope-Abgrenzung

**In Scope:**
- Tenant als Isolations-Container (personal + organization)
- Mandantenspezifisches **Zwei-Achsen-Rollenmodell** nach REQ-049: fachliche Rolle (Beobachter / Gärtner / Leitung) plus administrative Zusatzberechtigungen (Verwaltung / Technik)
- Einladungssystem (E-Mail + Link + OIDC-Auto-Join)
- Standort-Zuweisung an Mitglieder (mit saisonalen Zeiträumen) — als **Zuständigkeitshinweis**, nicht als Schreibgrenze
- Tenant-Switcher im Frontend
- Tenant-scoped API-Routing
- Tenant-Key auf allen bestehenden Ressourcen
<!-- Quelle: Outdoor-Garden-Planner Review G-030, G-031 -->
- Duty-Rotation (rotierende Dienstpläne, z.B. Gießdienst) mit Tausch-Funktion
- Pinnwand / Bulletin-Board (Posts, Kommentare, Reaktionen, Pinned-Posts)
- Gemeinsame Einkaufslisten (Sammelbestellungen koordinieren)
<!-- Quelle: RBAC Permission-Matrix v1.4 -->
- Granulare RBAC Permission-Matrix (§1a) mit ressourcentyp-spezifischen CRUD-Rechten pro Rolle
- Platform-Rollen-Differenzierung: `lead` (KA-Admin) und `viewer` (Read-Only Admin-Panel) im Platform-Tenant
- Drei disjunkte FastAPI-Dependencies: `require_permission(resource, action)`, `require_tenant_role(min_role)`, `require_admin_scope(scope)` (§1a.6)
- Service Account Integration: Permission-Matrix gilt identisch für `account_type: 'human'` und `'service'`
- `orphaned_since` und `suspended_reason` auf Tenant-Modell
- Platform-Admin-Notfallrechte: Emergency-Admin, Tenant-/User-Suspendierung (REQ-023 §5a.5)
<!-- /Quelle: RBAC Permission-Matrix v1.4 -->

**Ausdrücklich gestrichen (war bis v1.6 in Scope):**
- **Zuweisungsbasierte Write-Kontrolle** (`can_write(user, resource, tenant)`, §1a.5) — von REQ-049 §3.5 ersatzlos aufgehoben. Schreibrechte hängen allein am Rang der fachlichen Rolle.
- **`useCanEditLocation(locationKey)`** und jeder andere Client-Hook, der eine Zuweisung in eine Berechtigung übersetzt (§4.5).
- **Der Rollenwert `admin`** — stillgelegt zugunsten von `lead` plus Zusatzberechtigungen; Migration `v0032` bildet ihn verlustfrei ab.

**Nicht in Scope (bewusst ausgeklammert):**
- **Attribut-basiertes Access Control (ABAC)** — z.B. "darf nur Gießen-Tasks erstellen" oder zeitlich beschränkte Permissions → 3 Rollen + Permission-Matrix genügen
- Audit-Log (wer hat was geändert) → zukünftige REQ
- Cross-Tenant-Ressourcen-Sharing (z.B. geteilte Düngerliste) → Resourcen sind immer tenant-scoped
- Tenant-Billing / Abrechnung → SaaS-Modell zukünftig
- Hierarchische Tenants (Tenant-in-Tenant) → flache Struktur genügt
- Automatische Parzellen-Rotation (saisonaler Wechsel der Zuweisungen) → manuell
- **Untergruppen innerhalb eines Mandanten** (Klassen, Semester-Gruppen) und **befristete Mitgliedschaft / Urlaubsvertretung** → eigene Vorhaben, ausdrücklich keine Rollenfragen (REQ-049 §9)
- Echtzeit-Chat/Direct-Messaging zwischen einzelnen Mitgliedern → externe Tools (WhatsApp, Signal); Pinnwand deckt asynchrone Kommunikation ab
- DSGVO-Export pro Tenant → zukünftig, nach Audit-Log
<!-- Quelle: RBAC Permission-Matrix v1.4 -->
- Custom Roles (nutzerdefinierte Rollen pro Tenant) → drei fachliche Rollen plus zwei Zusatzberechtigungen decken die erhobenen Zielgruppen ab (REQ-049 §2.7)
- Permission-Delegation (User gibt temporär eigene Rechte an ein anderes Mitglied weiter) → manuell über die Verwaltung
- Row-Level Security in ArangoDB → wird in der Service-Schicht gelöst, nicht auf DB-Ebene
<!-- /Quelle: RBAC Permission-Matrix v1.4 -->
