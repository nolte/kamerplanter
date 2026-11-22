# SPEC-05 — Zugriffs- und Sichtbarkeitsmatrix

```
Paket: spec/privacy · Version 1.2 · 2026-11-22 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
Anforderungs-IDs: PRIV-300 … PRIV-339
Abhängig von: REQ-049 (Rollen), REQ-024 (Mandanten), 01 §4 (Zurechnungsrollen), 03 §3 (ehemalige Mitglieder),
06 §5 / 15 DA-04 (Personengruppen), 13 (L-09, L-10)
Änderung v1.1: Defaults der Sichtbarkeit je Mandantenklasse, Rollennamen vereinheitlicht (W-12), Legende PRIV-316.
Änderungen 1.2: gemessener Ist-Stand je Matrixzeile (§3.2: LEG-02, LEG-28, LEG-29, LEG-38, LEG-39, LEG-51, LEG-53);
Widerspruch PRIV-300 ↔ PRIV-301 aufgelöst; Klassifizierung inert (LEG-30, §4); neue Anforderungen PRIV-317…PRIV-324
(Betriebsmodus „Organisation mit Beschäftigten“, Aufgaben-Leistungsfelder, Aktorbefehle, Export per API-Key, eigene
Fotos, MCP-Freitext, Prompt-Injection, Plattform-Export = W-30); ehemalige Mitglieder Ist (LEG-06, §8); Beschäftigtenkontext
mit Überwachungsanalyse Ü1–Ü9 (§11); Abnahme-Verweise TA-310…TA-318 (Definition in `10`).
```

Eine Einschränkung des **Filterns** ist keine Einschränkung der **Sichtbarkeit** (#2517): heute sieht jedes
Mitglied jede ausführende Person in der ungefilterten Liste und in der CSV; nur die Abkürzung
(nach einer anderen Person filtern) ist rollenbeschränkt. Dieses Dokument legt fest, wer welche personenbezogene
Zurechnung zu welchem Zweck sehen darf, und trennt Berechtigungen auf Mandantenebene vom Zugriff auf Plattformebene.

---

## 1. Akteure

| Akteur | Definition [verifiziert] | Hinweise |
|--------|---------------------------|----------|
| **Anonym** | kein Token | erreicht `/api/v1/auth/*`, `/privacy/policy`, öffentlichen Katalog (Light-Modus: alles als Systemnutzer) |
| **Viewer** (`viewer`) | Mitglied, Rang 0 | liest, druckt, exportiert alle Mandantendaten (REQ-049 §2.3: „Buchhalter, Prüfer, Angehörige") |
| **Grower** (`grower`) | Rang 1 | erstellt und bearbeitet; kein Löschen; typische Inhaber sind u. a. „Mitarbeiter, Saisonkraft" |
| **Lead** (`lead`) | Rang 2 | löscht, weist anderen zu, ändert Struktur, annulliert/schwärzt Pflegeereignisse |
| **Management** (`admin_scopes ∋ management`) | Achse 2, rangunabhängig | Mitglieder, Rollen, Einladungen, Standortzuweisungen; Mandantenlöschung mit `lead` |
| **Technical** (`admin_scopes ∋ technical`) | Achse 2 | Integrationen, Service-Accounts (mit `lead`); liest die Mitgliederliste |
| **Mandantenadministrator** | keine Rolle im Code; dieses Paket verwendet den Begriff für `lead ∧ management` | das Zwei-Achsen-Modell kennt keinen einzelnen „Admin" |
| **Plattformbetreiber** | `lead` im Mandanten `platform` (Light-Modus: immer) | administrative Daten über Mandanten hinweg (Existenz, Name, Mitgliederliste, Security-Audit); **keine Domänendaten** (REQ-049 P4, AK-09) |
| **Plattform-Viewer** | spezifiziert (REQ-024 §1a.4), **nicht implementiert** (#2179) | heute kein Zugriff |
| **Service-Account** | `account_type: service`, maximale Rolle `grower`, mandantenbezogener API-Key | kein interaktiver Login |
| **API-Key eines Menschenkontos** | `kp_`-Key ohne `tenant_scope` (z. B. in einer HA-Integration) | erreicht konto­bezogene Routen wie `/privacy/export` ohne Step-up (LEG-38, PRIV-320) |
| **MCP-Agent** | Agent, der mit dem API-Key eines Mitglieds MCP-Werkzeuge aufruft (`mcp.read` ab `viewer`) | erbt die Rechte des Schlüssels; liest fremde Freitexte (LEG-51) und kann eingebettete Anweisungen ausführen (LEG-52) |
| **Betroffene Person (selbst)** | jedes Konto bezüglich seiner eigenen Daten | Art. 15–21 Selbstbedienung |

**[verifiziert]** `require_permission(resource, action)` ignoriert `resource` („does not change the
decision today"); die beschreibende Matrix `core/permissions.py:_RBAC` weicht stellenweise von den echten
Gates ab (Mandanten-`UPDATE` in der Tabelle dem Viewer gewährt, im Router aber `management` erforderlich;
Mitgliedschaftsschreibzugriffe in der Tabelle `lead` gewährt, im Code durch `management` abgesichert). Dieses Paket korrigiert die Tabelle nicht (Folgepunkt in `12` vermerkt), es ergänzt **Sichtbarkeits-
regeln**, die im Service neben dem Ownership-Prädikat ausgewertet werden.

---

## 2. Sichtbarkeitsdimensionen

| Dimension | Bedeutung |
|-----------|-----------|
| **P** Identität der ausführenden Person | `performed_by` / `performed_for` von Pflegeereignissen, Ernten, Behandlungen, Inspektionen, aus Bestätigungen abgeleiteten Ereignissen |
| **C** Identität des Erstellers/der Erstellerin | `created_by` von Tagebucheinträgen, Kommentaren, Objekten, Vorlagen, Anhängen, Pflegeereignissen |
| **K** Identität der Bestätigung | der Principal eines Aufgabenabschlusses / einer Pflegebestätigung (= P des abgeleiteten Ereignisses; kein eigenes Feld) |
| **M** Identität von Ändernden/Handelnden | `voided_by`, `redacted_by`, `plan_updated_by`, `garden_plan_audit.user_key` |
| **F** Freitextinhalt | Zusammenfassungen, Notizen, Namen, Kommentare, Bildunterschriften |
| **H** historische Datensätze | die Zeilen selbst (Pflegelog, Tagebuch, Audit) |
| **E** Mitgliederverzeichnis | `display_name`, `email`, Rolle, Scopes, `joined_at` der Mitglieder |
| **A** Datenschutzadministration | Prüfwarteschlange, Schwärzung, Löschzustand pro Mandant |
| **X** Exporte | CSV mit Namen, Plan-PDF/JSON, Art.-15-Bündel, Mandantenarchiv |
| **S** Statistiken pro Person | Zähler/Aggregationen der Aktivität nach Mitglied |

Darstellungszustände einer Identität (aus `01` §4.3): `member` (Name angezeigt), `former_member`
(kein Name nach N Tagen), `erased`, `third_party` (Label), `system`, `service_account`.

---

## 3. Die Matrix

Legende: **N** = Name angezeigt; **R** = nur Rolle/Beziehung („ein Mitglied", „ein Lead"), kein Name;
**–** = nichts / kein Zugriff; **eigene** = nur die eigenen Zeilen des Akteurs; **S** = Selbstbedienung;
**!** = auditierter Lesezugriff (Security-Audit-Zeile, PRIV-316); **(t)** = abhängig von der Mandanten-
einstellung `attribution_visibility` (§4; Default je Mandantenklasse, DA-04); **[v]** heute verifiziert
(VERIFIED_CODE); **[V]** Vorschlag (PROPOSED). Rollenbezeichner: `viewer`/`grower`/`lead` (Rang) und
`management`/`technical` (Scope) sind die einzigen Rollennamen des Codes (REQ-049); „Mandantenadministrator“
ist in diesem Paket nur die Kurzform für `lead ∧ management` und erscheint nicht in API oder Code (W-12).

| Dimension | Anonym | Viewer | Grower | Lead | Management | Lead ∧ Management | Plattformbetreiber | Service-Account |
|-----------|--------|--------|--------|------|------------|-------------------|--------------------|-----------------|
| **P** Ausführende/r, aktuelles Mitglied | – | N (t) [v: N] | N (t) [v: N] | N | N | N | – | R |
| **P** Ausführende/r, ehemaliges Mitglied (> N Tage) | – | R | R | R | R | R | – (nur Kontoseite) | R |
| **P** Ausführende/r, gelöscht | – | `erased` | `erased` | `erased` | `erased` | `erased` | – | `erased` |
| **P** Label Dritter | – | Label | Label | Label | Label | Label | – | Label |
| **P** Filtern / Suchen nach einer anderen Person | – | – [v] | – [v] | ja [v] | ja [v] | ja | – | – |
| **C** Ersteller/in von Tagebuch / Kommentar / Objekt | – | N (t) | N (t) | N | N | N | – | R |
| **C** Marker für eigene Zeile (`created_by_me`) | – | eigene | eigene | eigene | eigene | eigene | – | eigene |
| **K** wer eine Aufgabe bestätigt hat | – | N (t) | N (t) | N | N | N | – | R |
| **M** wer annulliert / geschwärzt hat | – | R [V; v: N nur über Performer-Join] | R | N | N | N | – | R |
| **M** Akteur im Plan-Audit (`changed_by`) | – | R [V; v: N] | R | N | N | N | – | – |
| **F** Freitext beliebiger Mitglieder | – | ja [v] | ja [v] | ja | ja | ja | – | ja (Lese-Tools) |
| **F** Freitext schwärzen | – | – | – | ja [v: nur Pflegeereignisse] | ja [V] | ja | – | – |
| **H** Pflegelog, Tagebuch, Historie (Zeilen) | – | ja [v] | ja [v] | ja | ja | ja | – | ja |
| **H** `garden_plan_audit`-Zeilen | – | ja [v] | ja | ja | ja | ja | – | – |
| **E** Anzeigenamen + Rollen der Mitglieder | – | ja [v] | ja | ja | ja | ja | ja (Admin-Liste) | ja |
| **E** E-Mail-Adressen der Mitglieder | – | ja [v] → **–** [V, LEG-14] | – [V] | – [V] | ja | ja | ja | – |
| **A** Prüfwarteschlange, Löschzustand des Mandanten | – | – | – | ja [V] | ja [V] | ja | nur Zähler [V] | – |
| **A** eigene Art.-15–21-Anfragen | – | S | S | S | S | S | S (Admin-Löschung, Vorschau) | – |
| **X** Pflegeereignis-CSV mit Namen anderer Mitglieder | – | – [V; v: ja] | – [V; v: ja] | ja ! | ja ! | ja ! | – | – |
| **X** Pflegeereignis-CSV, eigene Zeilen / Namen als R dargestellt | – | ja | ja | ja | ja | ja | – | – |
| **X** Beetlisten-CSV `include_assignment=true` | – | ja [v, §32.5 Pkt. 13] → (t) [V] | (t) | ja ! | ja ! | ja ! | – | – |
| **X** Plan-JSON / SVG / PDF (konstruktionsbedingt keine Namen) | – | ja [v] | ja | ja | ja | ja | – | ja |
| **X** Mandantenarchiv (REQ-056) | – | – | – | – | ja ! [v: management + Step-up] | ja ! | [v: jeder Zustand außer `deleted`, mit Fachdaten, Fotos, GPS, Mitgliedsnamen; Step-up + Audit + Hinweis] → nur Ausnahmeliste mit `reason` ! [V, PRIV-324; W-30] | – |
| **X** Art.-15-Bündel des eigenen Kontos | – | S | S | S | S | S | S | – |
| **X** Art.-15-Bündel per ungescoptem API-Key | – | [v: ja, ohne Step-up] → – [V, PRIV-320] | wie Viewer | wie Viewer | wie Viewer | wie Viewer | – | – |
| **P** Aufgaben: Zuständige/r (`assigned_to`) | – | [v: roher Kontoschlüssel] → N (t) als `PersonRef` [V, PRIV-318] | wie Viewer | N | N | N | – | R |
| **S** Aufgaben-Leistungsfelder (`started_at`, `actual_duration_minutes`, `difficulty_rating`, `quality_rating`) fremder Aufgaben | – | [v: ja] → – [V, PRIV-318] | [v: ja] → – (eigene: ja) | ja | – [V] | ja | – | – |
| **P** Auslöser eines Aktorbefehls (`control_events.triggered_by_user`) | – | [v: roher Kontoschlüssel] → R [V, PRIV-319] | wie Viewer | N | N | N | – | R |
| **F** eigene Fotos (Galerie, Anhänge) löschen | – | – | [v: nur Beetfotos] → eigene ja [V, PRIV-321] | ja [v] | ja (mit `lead`) | ja | – | – |
| **F** fremde unmarkierte Tagebucheinträge/Fotos/Notizen über MCP-Lesewerkzeuge | – | [v: ja, `mcp.read`] → nur Metadaten [V, PRIV-322, Option A] | wie Viewer | ja | ja | ja | – | – |
| **S** Aktivitätsstatistiken pro Person | – | – | – | – [V: existiert nicht; DARF NICHT ohne LEG-05 gebaut werden] | – | – | – | – |

### 3.1 Lesarten der Matrix

- **Mandantenebene**: alles oben außer der Spalte „Plattformbetreiber". Plattformzugriff
  erreicht nie die Dimensionen P/C/K/M/F/H eines Mandanten (REQ-049 P4); er sieht E (Admin-Mitglieder-
  listen mit E-Mail, nötig für Support und INV-1), A als Zähler und das Security-Audit.
- **Gesetzlich aufzubewahrende Zeilen** (`06` §3): die/der Anwendende bzw. Erntende einer `treatment_applications` /
  `harvest_batches`-Zeile folgt **P**, solange das Konto existiert; nach der Löschung wird das Pseudonym
  nie dargestellt (Zustand `erased`); der typisierte Anzeigename ist geleert [v].
- **Light-Modus**: ein einzelner Systemnutzer; die Matrix kollabiert für den
  einzigen Akteur auf „Lead ∧ Management"; es entstehen keine Zustände `former_member`/`erased` (keine Konten).

### 3.2 Gemessener Ist-Stand (Audit 2026-11-22, develop 007a4ea90)

[VERIFIED_CODE] Pfade unter `src/backend/app/`. Status-Token des Audits in Klammern.

**Pflegeprotokoll (LEG-02, `CONFIRMED`; Rechtsstatus `LEGAL_REVIEW_REQUIRED`, Q-DSB-01):** Ausführende und
Erstellende werden aus dem Token gestempelt (`domain/services/care_event_service.py:528`). Liste und CSV erhält jedes
Mitglied — die Routen prüfen nur `get_current_tenant`, keine Rolle (`api/v1/care_events/tenant_router.py:45–129`); die
CSV trägt `performed_by`, `performed_for` und `outcome_rating` (`domain/engines/care_event_csv_engine.py:22–40`) und
umfasst bis 50 000 Zeilen; ohne Bereich/Beet/Pflanze gilt ein 90-Tage-Fenster, mit `from`/`to` bis 5 Jahre
(`care_event_service.py:405–447`). Der Personenfilter ist auf Lead/`management` beschränkt
(`care_event_service.py:151–178`, `domain/engines/membership_engine.py:118–126`; Filter auf den Marker → 422 `:164–170`),
ebenso in der Beethistorie (`api/v1/locations/tenant_router.py:818–860`). R-25 = 5 J. (`config/settings.py:125`).
`attribution_visibility` hat 0 Treffer in `app/`; es gibt keine `ATTRIBUTION_*`-Audit-Aktion (`common/enums.py:1990–2025`).
**Folge:** Die Filtersperre ist eine Abkürzungssperre, keine Zugriffsbeschränkung — jedes Mitglied, auch `viewer`,
lädt per CSV bis 50 000 Zeilen mit Namen über bis zu 5 Jahre und filtert lokal je Person; ehemalige Mitglieder werden
nicht unterdrückt, nichts wird auditiert. Der Ist-Stand liegt außerhalb der eigenen LIA-1 (`06`). Priorität P1.
Einschränkende Sofortmaßnahmen ohne Rechtsgate: PRIV-307, PRIV-308, PRIV-112 (`03`); die Entkopplung der Zurechnungs-
von der Inhaltsfrist („R-25a“, Vorschlag ≤ 2 J., Setting mit Default = Bestand) gehört nach `06`. Maßnahme PRA-2.05.

**Mitgliederverzeichnis:** `MemberInfoResponse` enthält `email` für jedes Mitglied (`api/v1/tenants/schemas.py:219–223`;
PRIV-305 offen).

**Aufgaben (LEG-28, P1):** `GET /tasks`, `/tasks/queue`, `/tasks/overdue`, `/tasks/{key}` liefern jedem Mitglied
`assigned_to_user_key` als **rohen Kontoschlüssel** sowie `started_at`, `completed_at`, `actual_duration_minutes`,
`difficulty_rating`, `quality_rating`, `reopened_at` (`api/v1/tasks/schemas.py:304–357`, `:375–378`; Router
`api/v1/tasks/tenant_router.py:380–426, 529–613, 699, 739–788` nur `get_current_tenant`; UI zeigt den Schlüssel,
`TaskDetailPage.tsx:910–912`). Zusammen mit `care_events.performed_by_user_key` der Abschließenden ergibt das je Person
Zuständigkeit, Bearbeitungsbeginn, Ist-Dauer, Bewertung und Überfälligkeit. Widerspricht PRIV-407 (`06` §5) und dem
Grundsatz „nie Kontoschlüssel“ (GP-API-034, DEC-03/DEC-18). → PRIV-318, PRA-2.06.

**Aktorik (LEG-29, P1):** `control_events.triggered_by_user` geht als roher Kontoschlüssel an jedes Mitglied
(`api/v1/actuators/schemas.py:111–125`); Lebenszyklus `02` §3.9. → PRIV-319, PRA-2.07.

**Art.-15-Export (LEG-38, P2):** `POST /privacy/export`, `GET /privacy/export/{key}` und `/download` hängen nur an
`require_account_principal`, das nur mandanten-gescopte Keys abweist (`api/v1/privacy/router.py:124–181`,
`common/auth.py:62–79`); E-Mail-Änderung und Löschung verlangen dagegen Step-up und weisen API-Keys ab
(`router.py:184–221, 271–295`). → PRIV-320.

**Eigene Fotos (LEG-39, P2):** Das Löschen eines Galeriefotos (`DELETE …/plants/{key}/photos/{id}`,
`api/v1/plant_instances/photo_router.py:350–354`) und eines Anhangs (`DELETE /t/{slug}/attachments/{id}`,
`api/v1/attachments/tenant_router.py:320–323`) prüft `Action.DELETE` = nur `lead` (`common/auth.py:798–814`), ohne
Ausnahme für die hochladende Person; bei Beetfotos darf sie es (`domain/services/location_photo_service.py:128–135`,
`_may_remove`, #2643 Pkt. 7) — Drift zwischen Geschwistern. → PRIV-321.

**MCP (LEG-51, LEG-52, P2):** `list_diary_entries`, `get_diary_entry` (`text`, `title`, `created_by` roh) und
`get_diary_entry_photos` liefern jeden Eintrag des Mandanten an jedes Mitglied mit `mcp.read` (auch `viewer`), ohne
Prüfung von Markierung, Autorschaft oder Einwilligung des Verfassers (`mcp_server/tools/diary.py:451–525, 530–600,
1092–1100`); ebenso Freitext-`notes` in `get_plant_care_log`, `get_plant_inspections`, `get_plant_diagnostics` und den
Düngewerkzeugen (`plant_reads.py:303–307`, `ipm.py:318–331`, `diagnostics.py:336, 362, 400`). Der Dienst bindet nur an
den Mandanten (`plant_diary_service.py:347–384, 738–746`), und bei der Analyse zählt die Einwilligung der markierenden
Person, nicht die des Verfassers (`:761–767`). Das widerspricht REQ-050 §7.2/§7.6 und dem Einwilligungstext
`diary_ai_analysis` („nothing is ever analysed automatically …“). Derselbe Schlüssel hat 18 WRITE- und 3 SETUP-Werkzeuge,
`dry_run` ist per Default `false` (`mcp_server/base.py:265–279`); REQ-033/REQ-050 behandeln Prompt-Injection nicht (nur der
Knowledge-Service hat Schutzklauseln, `src/knowledge-service/app/prompt_engine.py:148–190`). → PRIV-322, PRIV-323,
PRA-2.10. PRIV-310 (rohe Schlüssel, `diary.py:507–510`; `inspector = "mcp:<key>"`, `ipm.py:463`) bleibt offen.

**Plattformebene (LEG-53 = W-30, P2):** siehe §7, PRIV-324.

**Leseaudit (PRIV-316):** Die Löschvorschau des Plattform-Admins schreibt keine Audit-Zeile
(`api/v1/admin/platform/router.py:544–560`; das Enum kennt keine Leseaktion) — offen.

---

## 4. Mandanteneinstellung `attribution_visibility` [Vorschlag, DEC-10]

**PRIV-300** Ein Mandant MUSS `settings.attribution_visibility ∈ {all_members,
leads_and_self}` führen, mit dem Standard **je Mandantenklasse nach PRIV-301** (für `personal`, Vereine und
Bestandsmandanten `all_members` = heutiges Verhalten, REQ-049 P2 „keine privaten Bereiche within a tenant"; Audit
2026-11-22: die v1.1-Fassung „Standard `all_members`“ widersprach den Klassen-Defaults in PRIV-301,
`DOCUMENTATION_GAP`). **Ist:** nicht gebaut (0 Treffer in `app/`). Bei `leads_and_self` werden die Dimensionen P/C/K/M für Viewer und
Grower als **R** dargestellt, außer die Zeile ist ihre eigene (`eigene` → N). Leads und `management` sehen für
aktuelle Mitglieder immer N.

**PRIV-301** Die Einstellung DARF NUR von `lead ∧ management` geändert werden können, mit dem in der UI angezeigten
Grund: „In Betrieben mit Beschäftigten kann das Gesetz verlangen, dass die Aktivität einzelner Beschäftigter nicht für
alle Kolleginnen und Kollegen sichtbar ist (Art. 88 DSGVO, § 26 BDSG, § 87 Abs. 1 Nr. 6 BetrVG); für Vereinsmitglieder
und Ehrenamtliche gilt § 26 BDSG nicht (§ 26 Abs. 8 BDSG)“ (L-09, L-10; PRIV-414). **Defaults nach Mandantenklasse
(DA-04, löst die v1.0-Formulierung ab):** `personal` → `all_members`; `organization_kind = commercial` →
`leads_and_self`; `association`/`community`/`other` → `all_members`; Bestandsmandanten (`unknown_legacy`) →
`all_members` (keine stille Änderung). **[LEGAL_REVIEW_REQUIRED LEG-05]** ob `leads_and_self` für gewerbliche
Mandanten verpflichtend sein muss (Q-LAW-03).

**Ist-Stand der Klassifizierung (Audit 2026-11-22, LEG-30, P1) [VERIFIED_CODE]:** `TenantSettings.record_keeping` und
`organization_kind` existieren (`domain/models/tenant.py:31–38`, Kommentar „In no request or response schema yet“;
Enums `common/enums.py:1200, 1222`), v0110 stempelt den Bestand (`unknown_legacy`), der Import setzt `undeclared`
(`domain/services/tenant_export_service.py:145`) — es gibt aber **keinen** API-/UI-Pfad zum Setzen und **keinen Leser**
(`grep RecordKeeping|OrganizationKind` außerhalb von Modell, Enum und Migration = 0). Folgen: (1) Die Klassen-Defaults
dieser Anforderung, alle Beschäftigtenschutzmaßnahmen, die an `commercial` hängen (PRIV-404, DA-04, PRIV-317), und die
feldgenaue Pflichtaufbewahrung (PRIV-400/410/411, `06`) sind technisch nicht umsetzbar; (2) neue Organisationsmandanten
bleiben `undeclared` ohne den PRIV-409-Leitungshinweis; (3) neue persönliche Mandanten erhalten nicht `none` — der
Docstring von v0110 behauptet einen Anlagepfad, den es nicht gibt (`DOCUMENTATION_GAP`); (4) das Gate DEC-32 („kein
SaaS mit gewerblichen Mandanten“) ist technisch nicht durchsetzbar; (5) Bestandsbetriebe `unknown_legacy` →
`all_members` ohne Weg zur Reklassifizierung. Soll (PRA-1.02): Klassifizierung bei der Anlage eines Organisationsmandanten
Pflicht (422 ohne Angabe), persönlich → `none` automatisch; Änderung nur `lead ∧ management`, auditiert
(`TENANT_RECORD_KEEPING_CHANGED`, neu `TENANT_ORGANIZATION_KIND_CHANGED`); Leitungshinweis bei `undeclared`/
`unknown_legacy`; Betreiberzähler (PRIV-110); mindestens ein Leser (Default von `attribution_visibility`). Abnahme TA-409, TA-034 (`10`).

**PRIV-302** Die Einstellung MUSS Teil des Mandantenexports (REQ-056) und des Abschnitts zum persönlichen Mandanten
im Art.-15-Bündel sein (dort ist sie die eigene Einstellung der Person).

**PRIV-303** Benachrichtigungen MÜSSEN der Einstellung folgen: ein Benachrichtigungstext an einen Viewer/Grower
DARF NICHT die ausführende Person der Aktion eines anderen Mitglieds nennen, wenn der Mandant `leads_and_self` ist
[heute verifiziert: Systembenachrichtigungstexte enthalten Aufgaben- und Pflanzennamen, keine Mitgliedsnamen —
REQ-025 §3.1.2 Regel 8 Messung; unabhängig von der Einstellung so beibehalten].

---

## 5. Zweckbezogene Berechtigungen

**PRIV-304** Drei Zweck-Berechtigungen MÜSSEN in `core/permissions.py` existieren und dort verdrahtet sein, wo
die Matrix es vorsieht, ausgewertet im Service (nicht allein im Router, gemäß #2107):

| Berechtigung | Gewährt an | Sichert ab |
|--------------|-----------|------------|
| `attribution.filter` | `lead`, `management` [v: `MembershipEngine.can_filter_care_log_by_member`] | `performed_by`-Filter für eine andere Person (Pflegelog, Beethistorie) |
| `attribution.export` | `lead`, `management` | CSV-/Export-Zeilen mit Namen anderer Mitglieder; `include_assignment=true` bei der Beetlisten-CSV, wenn `attribution_visibility = leads_and_self` |
| `privacy.review` | `lead`, `management` | Lesen der Prüfwarteschlange, Entscheidungen, generische Schwärzung (PRIV-228) |

**PRIV-305** `GET /tenants/{slug}/members` MUSS `email` nur an `management` zurückgeben (und die
Plattform-Admin-Routen); für jedes andere Mitglied wird das Feld weggelassen (nicht genullt, um die
Semantik des Schemas zu wahren) — **Spec-Änderungsvorschlag** zu REQ-024/REQ-049; **[rechtlich LEG-14]**
Notwendigkeit, jedem Mitglied die E-Mail jedes Mitglieds zu zeigen. [verifiziert] heute ist die Route
nur durch `get_current_tenant` abgesichert, und `MemberInfoResponse` enthält `email`.

**PRIV-306** Der Scope `technical` liest die Mitgliederliste wie heute (REQ-049 §2.4) — Namen und
Rollen, keine E-Mail (PRIV-305 gilt).

---

## 6. Exporte und Massenlesezugriffe

**PRIV-307** Ein CSV-Export, der Namen anderer Mitglieder enthalten würde, MUSS
`attribution.export` erfordern; für alle anderen MUSS derselbe Export gelingen, wobei die Spalten P/C/K
als **R** dargestellt werden (`"Mitglied"` / `"member"` über i18n des angeforderten `locale`, oder der eigene Name
bei eigenen Zeilen). Begründung: eine CSV mit 50 000 Zeilen und Namen ist ein Aktivitätsprofil; der operative
Bedarf eines Viewers („den Gießplan drucken") erfordert keine Namen. [heute verifiziert] jedes
Mitglied exportiert die CSV mit Anzeigenamen.

**PRIV-308** [Vorschlag] Exporte mit Namen MÜSSEN eine `security_audit_log`-Zeile schreiben
(`ATTRIBUTION_EXPORTED`, `tenant_key`, Akteur, Zeilenanzahl, kein Inhalt). Heute protokolliert das Mandanten-
archiv `tenant_export_requested` [verifiziert im NFR-011-R-38-Plan], die Pflegelog-CSV protokolliert
nichts.

**PRIV-309** Die Beetlisten-CSV mit `include_assignment=true` [verifiziert: keine Rollenprüfung, §32.5
Pkt. 13 argumentiert, dass ohnehin jedes Mitglied `/members` und `/assignments` liest] MUSS
`attribution_visibility` folgen: unter `leads_and_self` wird die Zuweisungsspalte für
Nicht-Leads als R dargestellt; das Lesen von `/assignments` folgt derselben Regel (Standortzuweisungen sind
Zuständigkeitshinweise, REQ-049 §3.5).

**PRIV-310** MCP-Lese-Tools MÜSSEN `PersonRef`-Darstellungen zurückgeben, niemals rohe Keys. [verifiziert]
`mcp_server/tools/diary.py` gibt `created_by` als nackten `users._key` zurück; `ipm.py` schreibt
`inspector = "mcp:<account_key>"` (ein Freitext-Pseudo-Key — umklassifizieren: es ist eine Konto-
Referenz in Verkleidung und MUSS zu `inspected_by_key` = Service-Account-Key werden, Label
`service_account`). Audit 2026-11-22: unverändert offen (`diary.py:507–510`, `ipm.py:463`).

### 6a. Neue Anforderungen aus dem Audit 2026-11-22

**PRIV-318** [PROPOSED, LEG-28] Aufgabenantworten MÜSSEN `assigned_to` als `PersonRef`/Anzeigename nach
`attribution_visibility` liefern, nie `assigned_to_user_key`. `actual_duration_minutes`, `difficulty_rating`,
`quality_rating` und `started_at` DÜRFEN nur an die zuständige bzw. abschließende Person und an Leads gehen; in
`organization_kind = commercial` werden sie standardmäßig nicht erhoben (Setting, Default aus; beim Abschließen verworfen,
dokumentiert). Ein Guard verbietet Antwortschemata, die ein Dauer-/Bewertungsfeld zusammen mit einem Personenbezug ohne
Rollenfilter ausliefern (Erweiterung TA-309). Die Frist R-47 (Leistungsfelder abgeschlossener Aufgaben nach 90 d leeren)
gehört nach `06`. PRIV-407 (`06` §5) gilt ausdrücklich auch für `tasks`. Fachlicher Zweck der Felder: Q-PO-13.
Maßnahme PRA-2.06. Abnahme TA-309 (präzisiert), TA-312, TA-313 (`10`).

**PRIV-319** [PROPOSED, LEG-29] Die API MUSS den Auslöser eines Aktorbefehls als `PersonRef` nach
`attribution_visibility` liefern, nie als rohen Kontoschlüssel; Lebenszyklus (Marker, Art.-15-Quelle, Frist) nach
`02` §3.9 und PRA-2.07; ob ein Personenbezug überhaupt nötig ist: Q-PO-15. Abnahme TA-314 (`10`).

**PRIV-320** [PROPOSED, LEG-38] Die Export-Routen `POST /privacy/export`, `GET /privacy/export/{key}` und
`/download` MÜSSEN Anfragen per API-Key (`via_api_key`) mit 403 abweisen wie die Löschung **oder** beim Anlegen einen
Step-up `data_export` verlangen; Anlage und Download lösen eine Benachrichtigung an die Kontoadresse aus. Begründung:
Ein langlebiger Maschinen-Credential ist kein angemessener Identitätsnachweis für eine Komplettkopie (Art. 12 Abs. 6,
ErwG 64, Art. 32 [INFERRED, Auslegung]; Q-LAW-13); ein kompromittierter Integrations-Key wird sonst zum
Exfiltrationswerkzeug für alle personenbezogenen Daten des Kontos über alle Mandanten. Maßnahme PRA-2.04. Abnahme TA-635 (`10`).

**PRIV-321** [PROPOSED, LEG-39] Eigene Uploads (Galeriefotos, Anhänge) MÜSSEN ab `grower` von der hochladenden
Person gelöscht werden können, fremde nur von `lead` — dieselbe `_may_remove`-Regel wie bei Beetfotos, ausgewertet im
Service (`PlantPhotoService.delete_photo`, `AttachmentService.delete`) mit `tenant_key` und `user_key` als
Pflichtargumenten (MT-010). Ein Guard prüft, dass alle Foto-Löschrouten dasselbe Prädikat nutzen. Begründung: Art. 17
Abs. 1, Art. 12 Abs. 2 („Erleichterung der Ausübung“), Art. 25 [INFERRED]; Q-PO-06. Maßnahme PRA-2.12. Abnahme TA-137 (`10`).

**PRIV-322** [OPEN_DECISION, LEG-51] MCP-Lesewerkzeuge DÜRFEN die Zusage aus REQ-050 §7.2/§7.6 und dem
Einwilligungstext `diary_ai_analysis` nicht umgehen. Option A (schutzverstärkend, empfohlen): `get_diary_entry` und
`get_diary_entry_photos` liefern Freitext und Fotos nur für eigene Einträge, für Einträge im Zustand
`requested`/`in_progress`/`completed` oder für die Leitung, sonst nur Metadaten (Fotos: `not_found` ohne
Existenzpreisgabe); Mandanten-Setting `mcp_member_free_text` (`own_only` Default in `commercial`, `all` in `personal`)
auch für `notes` der übrigen Lesewerkzeuge. Option B: Einwilligungstext und REQ-050 §7.6 an das Verhalten anpassen und
die Mitglieder informieren. Entscheidung Q-PO-17; Verantwortlichkeit bei agentischem Zugriff Q-LAW-10. Maßnahme PRA-2.10.
Abnahme TA-315 (`10`).

**PRIV-323** [PROPOSED, LEG-52] Gegen indirekte Prompt-Injection über Mandanteninhalte MÜSSEN die MCP-Werkzeuge
(1) Mandanten-Freitext in Antworten in einem eigenen Feld (`untrusted_content`, mit Herkunft `authored_by_self: bool`)
führen und in der Werkzeugbeschreibung als Daten kennzeichnen; (2) ein API-Key-Attribut `read_only` kennen, das WRITE und
SETUP sperrt (Default für neue persönliche Schlüssel, Q-PO-18); (3) zerstörende oder massenhafte Writes
(`archive_plant`, `generate_succession_runs`) zweistufig ausführen (`dry_run` → Bestätigungs-Token); (4) REQ-033 und
`docs/de/development/mcp-tools.md` erhalten einen Abschnitt „Agentensicherheit“. Rechtlich Art. 32 Abs. 1 lit. b,
Art. 25 Abs. 1 (empfohlene technische Schutzmaßnahme). Maßnahme PRA-2.10. Abnahme TA-316 (`10`).

---

## 7. Plattformebene

**PRIV-311** Der Plattformbetreiber DARF durch dieses Paket KEINEN Lesezugriff auf die Dimensionen P/C/K/M/F/H erhalten. Der Endpunkt für Datenschutzvorgänge
(`08` §5) liefert **Zähler** pro Mandant und **Zustände** der Vorgänge; die Löschvorschau und
`GET /admin/platform/erasures/{key}` bleiben wie heute [verifiziert].

**Widerspruch W-30 (Audit 2026-11-22, LEG-53, P2):** REQ-049 P4 sagt: „Ein Plattform-Admin erhält durch seine
Plattform-Rolle keinen Lesezugriff auf die Fachdaten eines fremden Mandanten“ (`spec/req/REQ-049_Rollenmodell-und-Vokabular.md:84–85`).
REQ-056 §8 (`:347–348`) und der Code erlauben ihm aber den vollständigen Mandantenexport in jedem Zustand außer `deleted`
— einschließlich Fachdaten, Fotos, GPS und Mitgliedsnamen — und den Download durch ihn selbst
(`domain/services/tenant_export_service.py:3–13, 282–283, 333–336`). Step-up, Audit und Hinweis an die Verwaltung sind
vorhanden; es fehlen Zweckbindung und eine dokumentierte Ausnahme von P4. Damit gilt PRIV-311 im Ist-Stand nicht
vollständig. Register: `14` W-30.

**PRIV-324** [PROPOSED, LEG-53] REQ-049 P4 MUSS eine abschließende Ausnahmeliste für Plattform-Exporte erhalten
(Rückgabe bei Vertragsende, verwaister Mandant, Weisung), und der Plattform-Export MUSS einen verpflichtenden
`reason` aus dieser Liste tragen (422 ohne `reason`); REQ-056 §8 verweist darauf; das AVV-Muster bildet die Ausnahme ab
(Art. 28 Abs. 3 lit. a/g [VERIFIED_LEGAL Normtext]; Weisungsgrundlage Q-LAW-08; Ausnahmeliste Q-PO-19; Zweckbindung
des Archivs LEG-13 → `06`). Maßnahme PRA-2.11. Abnahme TA-317 (`10`).

**PRIV-312** Ein künftiger **Plattform-Viewer** (#2179) MUSS die Spalte des Betreibers erben, wobei
jeder Schreibzugriff entfällt; er ist hier vermerkt, nicht spezifiziert.

**PRIV-313** Der Light-Modus (`kamerplanter_mode = light`) hat keine Konten; jede obige Regel, die
vom Zustand einer Person abhängt, ist dort inaktiv, und die Prüfwarteschlange wird nicht angelegt (es gibt
keine Löschung).

---

## 8. Historische Datensätze und die Grenze „ehemaliges Mitglied"

**PRIV-314** Historische Zeilen (H) bleiben für jedes Mitglied lesbar, unabhängig davon, wer sie
geschrieben hat — die Historie des Mandanten gehört dem Mandanten (REQ-049 P2). Was sich mit diesem Paket ändert, ist
nur die **Darstellung der Person** (P/C/K/M) und die **Prüfbarkeit des Textes** (F).

**PRIV-315** Der Zustand `former_member` MUSS für jede Mandantenrolle identisch dargestellt werden (keine
Lead-Ausnahme, `03` PRIV-113); der Plattformbetreiber sieht das Konto auf der Nutzerseite nur,
wenn es noch existiert.

**Ist-Stand ehemaliger Mitglieder (Audit 2026-11-22, LEG-06, `CONFIRMED`; Rechtsstatus `LEGAL_REVIEW_REQUIRED`,
Q-DSB-02) [VERIFIED_CODE]:** Die Anforderungen dazu stehen in `03` §3 (PRIV-111…118); hier der Sichtbarkeits-Ist-Stand.
(1) Das Mitgliedschaftsende löscht nur Mitgliedschaft, Kanten und `location_assignments`
(`data_access/arango/membership_repository.py:130–142`), schreibt `security_audit_log` (`domain/services/tenant_service.py:3762–3771`,
`:3786–3795`) und ruft `_end_membership` (`:3798–3806`): nur `tasks.assigned_to_user_key` wird geleert, die
Kalender-Feeds des Mandanten werden gelöscht. (2) Der Anzeigename wird live über `DOCUMENT(users/<key>).display_name`
aufgelöst, ohne Prüfung von Mitgliedschaft oder `is_active` (`data_access/arango/care_event_repository.py:657–662`,
analog `:791`); `display_performer` prüft nur den Marker (`domain/models/care_event.py:430–444`). (3)
`check_performed_by_filter` (`care_event_service.py:151–178`) erlaubt Lead/`management` den Filter auf jeden Schlüssel
außer dem Marker, also auch auf Ex-Mitglieder, unbefristet. (4) Die CSV enthält `performed_by`/`performed_for`
(`care_event_csv_engine.py:28–29`). (5) Der Art.-15-Export bindet mandantenbezogene Quellen an **aktuelle**
Mitgliedschaften (`privacy_service.py:2343`, `:3564–3573`; Filter `personal_data_repository.py:122–131`). (6)
`RETENTION_FORMER_MEMBER` / `former_member` = 0 Treffer in `src/`: PRIV-112, -114, -115, -116 sind nicht gebaut. Die
Matrixzeile „P Ausführende/r, ehemaliges Mitglied (> N Tage) → R“ ist damit **Soll**; Ist ist N für jede Rolle, unbefristet.
Priorität P2; Umsetzung schutzverstärkend ohne Rechtsgate mit Default 90 d (PRA-2.03); für den Art.-15-Teil
empfiehlt das Audit, in verlassenen Mandanten nur auf server-gestempelten Kontofeldern (`created_by`,
`performed_by_user_key` aus dem Token) zu suchen — das vermeidet das SCR-001-Risiko eingeschleuster Fremdschlüssel
(`03`, PRA-2.04).

---

## 9. Audit-Protokollierung datenschutzrelevanter Lesezugriffe

**PRIV-316** Die folgenden Lesezugriffe MÜSSEN eine `security_audit_log`-Zeile schreiben (Akteur, Mandant,
Aktion, Anzahl; kein Inhalt): Exporte mit Namen (PRIV-308), Mandantenarchiv, Löschvorschau des Plattform-Admins,
Entscheidungen in der Prüfwarteschlange. Gewöhnliche Listenzugriffe DÜRFEN NICHT auditiert werden (Volumen
und REQ-049 („keine Überwachung von Mitgliedern")). Ist (Audit 2026-11-22): keiner dieser Lesezugriffe wird auditiert
(§3.2); der Plattform-Export (Mutation) ist auditiert.

---

## 10. Abnahme (Zusammenfassung)

| ID | Kriterium |
|----|-----------|
| TA-300 | Mit `leads_and_self` stellt die Pflegelog-Liste eines Growers die ausführende Person anderer Mitglieder als `R` dar, eigene Zeilen als `N`; ein Lead sieht `N`. |
| TA-301 | Mit `all_members` entspricht das Verhalten dem heutigen (Regressions-Pin). |
| TA-302 | `GET /members` lässt `email` für Viewer/Grower/Lead ohne `management` weg; enthält sie für `management` und Plattform-Admin. |
| TA-303 | CSV-Export durch einen Viewer stellt andere Mitglieder als `R` dar; durch einen Lead mit Namen und schreibt `ATTRIBUTION_EXPORTED`. |
| TA-304 | MCP-Diary-/IPM-Tools geben keinen rohen `users._key` zurück. |
| TA-305 | Plattform-Admin kann keine Prüfeinträge lesen (403), nur Zähler. |
| TA-306 | `performed_by`-Filter für ein anderes Mitglied durch einen Grower → 403 (Regressions-Pin); für ein unterdrücktes ehemaliges Mitglied → 422. |
| TA-307 | Routen-Walk: jede neue `/t/{slug}/privacy/*`-Route steht in einer Matrix im Stil von `test_garden_plan_tenant_isolation` und weist einen fremden Mandanten mit 404 ab. |
| TA-310 | (PRIV-405, LEG-02) jede Abfrage mit `performed_by`-Filter schreibt genau eine `ATTRIBUTION_FILTER_USED`-Zeile (`10`). |
| TA-311 | (PRIV-317) `commercial` erzwingt `leads_and_self`; Umschalten ohne Flag abgewiesen (`10`). |
| TA-312 | (PRIV-318) als `viewer` enthält `GET /tasks/{key}` einer fremden Aufgabe weder Kontoschlüssel noch Dauer/Bewertungen; `assigned_to` als `PersonRef` (`10`); Guard TA-309 präzisiert. |
| TA-313 | (PRIV-317/318) `commercial` ohne Leistungsfelder; Werte beim Abschließen verworfen (`10`). |
| TA-314 | (PRIV-319, LEG-29) `control_events` im Lebenszyklus; API ohne Kontoschlüssel (`10`). |
| TA-315 | (PRIV-322, Option A) MCP-Freitextpolitik (`10`). |
| TA-316 | (PRIV-323) Agentensicherheit: `read_only`, `untrusted_content`, Bestätigungs-Token (`10`). |
| TA-317 | (PRIV-324) Plattform-Admin-Export ohne `reason` → 422 (`10`). |
| TA-318 | (PRIV-316) Leseaudit der Löschvorschau (`10`). |
| weitere | PRIV-320 → TA-635; PRIV-321 → TA-137; Klassifizierung (§4) → TA-409, TA-034 (alle `10`). |

---

## 11. Beschäftigtenkontext und Überwachungspotenzial (Audit 2026-11-22, LEG-05)

### 11.1 Revalidierung LEG-05

Verifikationsstatus: technisch `PARTIALLY_CONFIRMED` — die Durchführende-Regel und die Filtersperre sind bestätigt, das
Überwachungspotenzial ist in der Spec unvollständig erfasst; Rechtsstatus `LEGAL_REVIEW_REQUIRED` (Q-LAW-01 § 26 BDSG
nach C-34/21, V-08; Q-LAW-02 BAG-Linie zu § 87 Abs. 1 Nr. 6 BetrVG, V-05, nicht an der Quelle verifiziert;
Ehrenamtliche sind keine Beschäftigten, L-09). Priorität P1; P0, falls gewerbliche Mandanten mit Beschäftigten produktiv
sind (Prüfauftrag PRA-0.04, Q-OP-12).

**Bestätigt [VERIFIED_CODE]:** Die Zurechnungsregel „immer die aufrufende Person“ gilt auf allen vier
Bestätigungspfaden — REST `api/v1/care_reminders/router.py:159–170`, Benachrichtigungsaktion
`api/v1/notifications/tenant_router.py:215–220`, Aufgabenwarteschlange `domain/services/task_service.py:1840–1855` →
`care_reminder_service.py:1290–1368`, MCP `mcp_server/tools/care.py:77–86`; Mapper `care_reminder_service.py:951–964`;
Guard `tests/unit/guards/test_care_confirmation_names_its_performer.py`. Weitere Schreiber stempeln den Aufrufer
(`care_event_service.py:528`, `garden_resource_service.py:775`, `irrigation_zone_service.py:609, 732`); gesetzliche
Schlüssel kommen aus dem Token (`api/v1/harvest/tenant_router.py:160, 232`, `api/v1/ipm/tenant_router.py:175, 213`,
`mcp_server/tools/ipm.py:468`). Der Personenfilter ist auf `lead`/`management` beschränkt (§3.2).

**Unterschätzt:** (i) Aufgaben-Leistungsfelder für jedes Mitglied lesbar (LEG-28, PRIV-318); (ii)
`control_events.triggered_by_user` roh für alle Mitglieder (LEG-29, PRIV-319); (iii) Zurechnung durch Dritte über
Freitext (`performed_for_user_key`, `performed_by_label`, `applied_by`, `harvester`, `inspector` via MCP `ipm.py:463`)
unterliegt der Durchführende-Regel nicht; (iv) die Klassifizierung ist inert (LEG-30, §4); (v) kein Guard für
PRIV-403/407 (`06` §5). RISK-01 „kein Statistik-Endpunkt“ (`11`) ist nur `PARTIALLY_CONFIRMED`: Es gibt keine
Personen-`COLLECT` in `data_access/`, aber Einzeldaten mit Dauer und Bewertung je Aufgabe machen die Aggregation
clientseitig trivial.

**Bewertung:** Ein Koordinationsprotokoll („wer hat wann gegossen“) ist nicht per se unzulässig. Unverhältnismäßig wird
es durch Zeit-, Dauer- und Qualitätsdaten je Person, unbeschränkte Sichtbarkeit unter Kolleginnen und Kollegen, Exporte
ohne Audit und eine 5-jährige namentliche Historie [INFERRED]. Die Mitbestimmungspflicht nach § 87 Abs. 1 Nr. 6 BetrVG
trifft den Arbeitgeber-Mandanten; die objektive Eignung zur Leistungskontrolle liegt bei den Aufgabenfeldern nahe
[LEGAL_REVIEW_REQUIRED].

### 11.2 Überwachungspotenzial je Datenquelle

| # | Datenquelle | Was je Person ableitbar ist | Wer es heute sieht [v] | Legitime Nachvollziehbarkeit? | Unverhältnismäßig? | Gegenmaßnahme | Gate (einschränkend) |
|---|---|---|---|---|---|---|---|
| Ü1 | `care_events` + CSV | wann, wo, was je Person über 5 J. (Anwesenheitsmuster) | alle Mitglieder (CSV), Filter L/M | ja (Koordination, PflSchG) | ja — Export an alle und Namen über 5 J. | PRIV-307/308, `attribution_visibility`, Zurechnungsfrist ≤ 2 J. (`06`), PRIV-112 | ja |
| Ü2 | `tasks`-Leistungsfelder | Ist-Dauer, Beginn, Ende, Qualitäts-/Schwierigkeitsbewertung, Überfälligkeit je Zuständige/r | alle Mitglieder | Zuständigkeit ja; Dauer/Bewertung nein | **ja** | PRIV-318, R-47 (`06`), `PersonRef` | ja |
| Ü3 | `control_events.triggered_by_user`, `manual_overrides` | wer schaltet wann Aktoren (Anwesenheit im Raum, Arbeitszeit) | alle Mitglieder | Sicherheit/Fehleranalyse ja (kurzfristig) | ja ohne Frist | PRIV-319, Frist 90 d, Marker (`02` §3.9) | ja |
| Ü4 | Pflichtaufzeichnungen | Anwendungen/Ernten je Person | alle Mitglieder (Freitextname), Behörde | ja (Gesetz, beruflich) | nein, sofern nur Pflichtfelder und Pflichtfrist | Feldgenauigkeit PRIV-410/411, Fristbeginn PRIV-412 (`06`) | teils (LEG-03) |
| Ü5 | Kopie Pflichtzeile → Pflegeprotokoll | macht die Pflichtangabe filter- und exportierbar | wie Ü1 | Historie ja, Person nein | in `commercial` ja | Schalter; in `commercial` keine Kopie (LEG-07, PRA-2.08) | vorläufig |
| Ü6 | Plan-Audit, Aufgabenkommentare, Tagebuch | Arbeitsinhalte, Formulierungen | alle Mitglieder | ja | nein | Prüfwarteschlange (`04` §5, LEG-08) | — |
| Ü7 | Logs (stabiles `log_subject` + Route + Zeit) | vollständige pseudonyme Nutzungsspur | Betreiber | Sicherheit ja | ja ohne Frist | Log-Frist ≤ 30 d festschreiben (LEG-44, `06`), Rotation des Subjekt-Salts erwägen | Betrieb |
| Ü8 | Service-Accounts/MCP → Home Assistant/KI | Weitergabe in fremde Historien | Drittsysteme | Automatisierung ja | ja mit Personenbezug | Antworten für Service-Accounts ohne Personenfelder (PRIV-310), PRIV-322/323, Doku; Q-OP-13 | ja |
| Ü9 | `last_login_at` | Anmeldeverhalten | nur Plattform-Admin | Sicherheit ja | nein (nur Plattform) | keine | — |

### 11.3 Empfohlener Betriebsmodus „Organisation mit Beschäftigten“

**PRIV-317** [PROPOSED, LEG-05; Voraussetzung LEG-30] Das System MUSS einen technischen Betriebsmodus
„Organisation mit Beschäftigten“ führen, gekoppelt an `organization_kind = commercial` (setzbar nach §4, PRA-1.02). In
diesem Modus gelten:
1. `attribution_visibility = leads_and_self` **erzwungen**, bis LEG-05 anders entschieden ist (Q-LAW-03);
2. Aufgaben-Leistungsfelder aus (PRIV-318);
3. CSV mit Namen nur für `lead`/`management`, mit Audit (PRIV-307/308);
4. keine Backfill-/Konsistenzkopie der Person aus Pflichtzeilen ins Pflegeprotokoll (Ü5, LEG-07);
5. verkürzte Zurechnungsfrist (Wert in `06`);
6. Pflichthinweis „Betriebsrat/DSFA“ bei Aktivierung (PRIV-406, `06` §5; DSFA-Kopplung `11`, PRA-3.04).
Für Vereine und Gemeinschaftsgärten bleibt `all_members` mit PRIV-112 und Audit; für Haushalte gilt das heutige Verhalten.
Rechtlich ist die Mitbestimmung bzw. DSFA eine Pflicht des Arbeitgeber-Mandanten (§ 87 BetrVG, Art. 35); der Modus ist
eine empfohlene technische Schutzmaßnahme bzw. Produktempfehlung des Anbieters (Art. 25, Art. 28 Abs. 3 lit. f)
[INFERRED]. Produktvariante: Q-PO-14; Nutzung von Freitext für Beschäftigtenbewertungen: Q-CUS-02. Maßnahmen PRA-1.02,
PRA-2.05, PRA-2.06. Abnahme: TA-311, TA-313 (`10`), Klassifizierung TA-409.
