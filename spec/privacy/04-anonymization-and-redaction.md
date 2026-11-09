# SPEC-04 — Anonymisierung und Schwärzung

```
Paket: spec/privacy · Version 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Anforderungs-IDs: PRIV-200 … PRIV-249
Hängt ab von: 01 §2 (Vokabular), 02 (Feldinventar), 03 (wann welche Regel greift)
```

---

## 1. Die drei Ersetzungsformen und was sie belegen

| Form | Geschrieben wo [verifiziert] | Verknüpfbar? | Ist die Zeile danach anonym? |
|------|------------------------------|--------------|------------------------------|
| `null` / Zeile gelöscht | `DELETE_STEPS`; `_end_membership` leert `assigned_to_user_key` | nein | das Attribut ist weg; die Zeile kann über ihren Inhalt weiterhin identifizieren |
| Marker `_anonymized` (`ANONYMIZED_MARKER`) | `ANONYMIZE_COLLECTIONS`-Regeln mit `anonymized_value=ANONYMIZED_MARKER`; R-25-Aufbewahrungs-Patch; Attachment-Storage-Scope; Mandanten-Import für nicht zugeordnete Konten (`ANONYMIZED_ACCOUNT`) | nein — alle gelöschten Personen eines Mandanten teilen sich dasselbe Literal | **nicht von sich aus**: die Zeile ist nur anonym, wenn kein Freitext, kein Foto und kein gemeinsam auftretendes Attribut die Person identifiziert (Erwägungsgrund 26) |
| Tombstone `anon_<16hex>` (`compute_tombstone_hash`) | `tombstone_hash`-Regeln (gesetzliche Zeilen), `PSEUDONYMIZE_AUDIT_COLLECTIONS`, Pseudonymisierung bei der Mandantenlöschung | ja — deterministisch pro `(user_key, ERASURE_TOMBSTONE_SALT)`, instanzweit | **nein**: pseudonymisierte personenbezogene Daten (Art. 4 Nr. 5); das Salt ist die „zusätzliche Information“ |

**PRIV-200** Das Paket MUSS die Begriffe wie oben in Code-Kommentaren, API-Dokumentation
und nutzersichtbaren Texten verwenden: „anonymisiert“ nur dort, wo die gesamte Zeile geprüft wurde oder
keinen identifizierenden Inhalt enthält; andernfalls „Zurechnung entfernt“ (Marker) oder „pseudonymisiert“
(Tombstone). Der i18n-Schlüssel für die Personendarstellung ist `enums.personRef.erased`,
mit dem deutschen Anzeigetext „entferntes Mitglied“ statt „anonymisiert“ **[Vorschlag]** — das aktuelle
Wort verspricht mehr, als die Daten einlösen.

**PRIV-201** Der Marker und die Tombstone-Regex MÜSSEN jeweils genau eine Definition haben.
[verifiziert] `_anonymized` ist viermal definiert (`erasure_engine.py:ANONYMIZED_MARKER`,
`models/care_event.py:ANONYMIZED_MARKER`, `attachment_repository.py:ANONYMIZED_MARKER`,
`tenant_export_engine.py:ANONYMIZED_ACCOUNT`), die Regex `^anon_[0-9a-f]{16}$` dreimal
(`erasure_engine.TOMBSTONE_FULLMATCH_REGEX`, `tenant_erasure_executor._TOMBSTONE_REGEX`,
`tenant_export_engine._TOMBSTONE`). Beide nach `domain/models/privacy.py` verschieben (die Domänenschicht
darf es aus jeder anderen Schicht importieren); der bestehende Test
`test_garden_plan_retention.py`, der drei Kopien als gleich festschreibt, wird zu einem Guard, dass es
nur eine gibt. Abnahme: TA-200.

---

## 2. Tombstone-Regeln

### 2.1 Ableitung (beibehalten)

**PRIV-202** Die Ableitung `anon_ + sha256(user_key + salt)[:16]` DARF NICHT für bestehende Daten
geändert werden: über Jahre geschriebene gesetzliche und Audit-Zeilen müssen untereinander verknüpfbar bleiben,
und der Tombstone-Lookup nach Art. 15 (REQ-025 §3.1.2 Regel 6) hängt davon ab. [verifiziert] Es handelt sich um
reines SHA-256 mit angehängtem Salt, nicht um HMAC, gekürzt auf 64 Bit; die Schwester-Ableitungen
(`compute_request_key`, `log_subject`) verwenden HMAC mit einem Zweck-Label. Festgehalten als
DEC-04; eine künftige Schlüsselrotation braucht eine Re-Keying-Migration (`09` §7) und liegt außerhalb des Umfangs.

**PRIV-203** Neue, von diesem Paket eingeführte Ableitungen (keine ist zwingend erforderlich; z. B. ein
Schlüssel für Prüfeinträge) MÜSSEN HMAC mit einem Zweck-Label verwenden, nicht `sha256(x + salt)`. Die Wiederverwendung
von `erasure_tombstone_salt` als Digest-Schlüssel für Client-Events (REQ-053 §32.6 Pkt. 16, SEC-003) wird vermerkt, hier
aber nicht geändert.

### 2.2 Wo ein Tombstone existieren darf

**PRIV-204** Tombstones MÜSSEN ausschließlich in der **Tombstone-Allowlist** existieren, die aus dem
Inventar abgeleitet wird (keine zweite Liste): jede Collection/jedes Feld, das eine `tombstone_hash`-Regel in
`ANONYMIZE_COLLECTIONS` oder einen Eintrag in `PSEUDONYMIZE_AUDIT_COLLECTIONS` hat. [verifiziert heute]:
`harvest_batches.harvested_by_key`, `quality_assessments.assessed_by_key`,
`treatment_applications.applied_by_key`, `inspections.inspected_by_key`,
`garden_plan_audit.user_key` (→ Marker nach DEC-16), `erasure_requests.user_key`,
`mcp_audit_log.service_account_key`, `security_audit_log.actor_user_key/target_user_key`,
`consent_records.user_key`.

**PRIV-205** Jeder Prozess, der einen kontoförmigen Wert von einer Zeile in eine andere kopiert
(Backfill-Mapper, Konsistenz-Job, Mandanten-Import, Task-Completion-Engine, die
`harvested_by_key=event.performed_by_user_key` schreibt, Supersede, das die Ausführenden des Vorgängers behält)
MUSS den Wert durch eine Funktion `carry_account_reference(value) -> str | None` leiten:
ein aktuell geformter Schlüssel wird unverändert zurückgegeben; ein Tombstone oder der Marker wird zu `_anonymized`,
wenn das Ziel ein Marker-Feld ist, und zu `null`, wenn das Ziel ein Tombstone-Feld ist (ein
Pseudonym darf nie aus einer Kopie neu erzeugt werden). [verifizierter Defekt] `account_of` in
`care_event_backfill_mapper.py` akzeptiert jeden nicht leeren String (#2770 Punkt 1).

**PRIV-206** Eine Konsistenzprüfung (`privacy.consistency`, neuer Beat, `08` §6) MUSS jeden
tombstone-förmigen Wert außerhalb der Allowlist und jeden Marker in einem Tombstone-Feld melden, pro
Collection, als Anzahlen; der Befund ist ein Defekt und wird nie stillschweigend korrigiert, außer durch die
Einmal-Migration aus `09` §3.

**PRIV-207** Die `erased`-Darstellung MUSS einen tombstone-förmigen Wert wie den Marker behandeln
(`display_performer` prüft heute nur `ANONYMIZED_MARKER` [verifiziert]; ein Tombstone wird nur deshalb als
„anonymisiert“ dargestellt, weil das Nutzerdokument fehlt). Der `performed_by`-Filter MUSS einen tombstone-förmigen Wert
ebenso zurückweisen wie den Marker (422) [verifizierte Lücke: nur der exakte
Marker wird zurückgewiesen].

### 2.3 Verknüpfbarkeit als Rechtsfrage

**PRIV-208 [rechtlich LEG-15]** Ob ein deterministisches Pseudonym pro Person über alle gesetzlichen
Zeilen für bis zu fünf Jahre verhältnismäßig ist (gegenüber zufälligen Tokens pro Zeile, die den Inhalt des Eintrags
dennoch erfüllen), ist Sache der Rechtsberatung. Das aktuelle Design argumentiert: Das Pseudonym lässt
eine Prüfperson nachvollziehen, dass dieselbe (ungenannte) anwendende Person mehrere Parzellen behandelt hat — eine Eigenschaft, die der Eintrag
braucht; und es lässt den eigenen Art.-15-Export der Person die Zeilen finden. Das Paket behält
es für gesetzliche und Security-Audit-Zeilen bei und entfernt es aus `garden_plan_audit` (DEC-16),
wo keines der beiden Argumente greift.

---

## 3. Anonymisierungsregeln (Kontolöschung)

### 3.1 Regelsatz

**PRIV-209** Der Regelsatz MUSS das einzige `ErasureEngine`-Inventar bleiben; dieses Paket ergänzt
Attribute, keine zweite Engine. Erforderliche Ergänzungen (Dataclass-Änderungen siehe `08` §2):

| Regelattribut | Bedeutung |
|---------------|-----------|
| `attribution` | Rolle aus `01` §4.1 |
| `retention_class` | `ephemeral`, `shared_history`, `statutory`, `audit` |
| `review_fields` | Freitextfelder der Zeile, die in die Prüfwarteschlange gehen, wenn die Regel greift (z. B. `care_events: summary, reason, observed_outcome, product_label, material, performed_by_label`) |
| `clear_fields` (existiert) | Freitextfelder, die bei der Löschung **geleert** werden (eingetippte Anzeigenamen, `user_agent`) |

### 3.2 Was wird geleert, was geprüft, was behalten

**PRIV-210** Das Leeren (`clear_fields`) MUSS auf Felder beschränkt bleiben, deren *einziger* Zweck es ist,
die Kontoinhaberin bzw. den Kontoinhaber zu benennen: `harvester`, `assessed_by`, `inspector`, `applied_by`,
`consent_records.user_agent` [verifiziert]. Inhaltlicher Freitext wird nie automatisch geleert
(REQ-025 §3.1.3 Regel 4 „never key on free text“; REQ-053 E-16).

**PRIV-211** [Vorschlag] Zwei Felder MÜSSEN zu `clear_fields` hinzugefügt werden, weil sie
konstruktionsbedingt identitätstragend und kein Inhalt sind:
- `attachments.original_filename` → `""` (ein Kamera-/Telefon-Dateiname enthält häufig den Namen
  der Eigentümerin bzw. des Eigentümers; der gespeicherte Objektschlüssel nie);
- `care_events.performed_by_label` **nur wenn** `performed_by_user_key` die betroffene Person ist? —
  Nein: das Label benennt eine *dritte Person*, nicht die betroffene Person; es bleibt und geht in die Prüfung.

**PRIV-212** [Vorschlag] Inhaltlicher Freitext der Zeilen der betroffenen Person in einem geteilten Mandanten MUSS
**behalten und zugleich** zur Prüfung aufgelistet werden (§5). Die Liste der prüfbaren Felder ist das
`review_fields` der Registry; `02` §3 gibt das vollständige Inventar. Mindestmenge (verifizierte Felder):

| Collection | Prüfbare Felder |
|------------|-----------------|
| `care_events` | `summary`, `reason`, `observed_outcome`, `product_label`, `material`, `performed_by_label`, `void_reason`, `redaction_reason` |
| `plant_diary_entries` | `title`, `text`, `tags`, `analysis.summary` |
| `task_comments` | `comment_text` |
| `tasks` (der betroffenen Person zugewiesen oder von ihr erstellt — `tasks` hat kein `created_by` [verifiziert]; nur Zeilen mit Zuweisung) | `name`, `instruction`, `completion_notes` |
| `garden_objects` | `label`, `notes` |
| `bed_templates` | `name` |
| `locations`, die aus einer Vorlage der betroffenen Person erstellt wurden (`template_key`-Datenlinie) | `name` (kopiert), `description`, `notes` |
| `garden_plan_audit`-Zeilen mit der betroffenen Person als Akteurin | `summary`; `snapshot` (Import-Snapshot) |
| `attachments` | `caption` |
| `manual_overrides` | `reason` |
| `harvest_batches`, `quality_assessments`, `inspections`, `treatment_applications` (wenn `record_keeping = none`, sonst als gesetzlich behalten) | `notes` |

**PRIV-213** `care_events.material` MUSS in die Schwärzungs-Feldmenge `FREE_TEXT_FIELDS`
(Code `models/care_event.py`) und in die Spec-Listen (REQ-053 GP-FR-109, NFR-011 R-25) aufgenommen werden — ein
**Spec-Änderungsvorschlag**, keine stille Änderung: Das Feld ist Freitext (≤ 200), wird im
CSV exportiert und bleibt heute von Schwärzung und R-25 unberührt [verifiziert]. Ebenso
MÜSSEN `measurements[].source` und `measurements[].extraction_method` (freie Strings) mit der Menge
geschwärzt werden.

### 3.3 Backfill-Zeilen und abgeleitete Zeilen

**PRIV-214** Der Backfill-Mapper und der Konsistenz-Job MÜSSEN `created_by = null`
(Systemursprung) setzen und `performed_by_user_key` nur über `carry_account_reference` aus einem
Feld der **gleichen Zurechnungsrolle** (`applied_by_key`, `harvested_by_key` sind
`performed_by`; `watering_events.performed_by` ist Freitext → niemals). [verifiziert] Der Mapper
weist Labels bereits zurück und setzt `created_by = None`; Tombstones weist er nicht zurück.

**PRIV-215** Zeilen mit Systemursprung (`trigger ∈ {backfill}` und `created_by = null`) MÜSSEN
Korrekturrechte an die **Ausführenden** vergeben: `care_event_service` lässt `created_by == user`
oder eine Lead-Rolle korrigieren [verifiziert]; ergänze `or (created_by is None and performed_by_user_key == user)`.
Das ersetzt den Vorschlag in #2770 Punkt 3 für Backfill-Zeilen (bei denen es keine Autorin bzw. keinen Autor gibt);
Live-Erinnerungszeilen erhalten `created_by = principal` (`03` §4.2).

---

## 4. Verhalten des Audit-Trails

### 4.1 Garden-Plan-Audit

**PRIV-216** [DEC-16, Spec-Änderungsvorschlag] `garden_plan_audit.user_key` MUSS von
`PSEUDONYMIZE_AUDIT_COLLECTIONS` (Tombstone) nach `ANONYMIZE_COLLECTIONS` (Marker) wandern. NFR-011
R-26 nennt heute beides [verifizierter Widerspruch]; GP-NFR-055 argumentiert mit Verknüpfbarkeit „so that rows
stay linkable — WP 1.8“. Die Zeilen werden nach 365 Tagen (R-26) und mit dem Mandanten gelöscht; der
Art.-15-Export braucht keine Verknüpfbarkeit (die eigenen Zeilen der Person werden über den echten Schlüssel gefunden,
solange das Konto existiert). **[rechtlich LEG-15]**

**PRIV-217** `garden_plan_audit.summary` enthält eine Kopie von `Location.name` /
`GardenObject.label` / `Site.name` / Zonenname [verifiziert], und `snapshot` enthält den vollständigen Plan-Export
einschließlich `notes`/`description`. Beide sind Prüffelder (PRIV-212) und MÜSSEN
schwärzbar sein (`[redacted]` in `summary`; `snapshot` → die Felder `notes`/`description`/`label`
innerhalb des JSON über dieselbe Allowlist schwärzen). Das Audit einer Schwärzung selbst schreibt
nur die Kategorie (Kommentar in `care_event_repository.py`: „The category, never the text“)
[verifiziert] — dieses Muster MUSS für jeden Audit-Schreiber gelten.

**PRIV-218** [verifizierte Lücke] `garden_plan_audit`-Zeilen sind für jedes Mitglied mit einem
aktiven Anzeigenamen lesbar (`changed_by_name`), und die UI verwirft `null`-Akteure stillschweigend
(`SnapshotPanel.tsx`). Nach diesem Paket: `changed_by` wird zu einer `PersonRef` (`08` §3),
dargestellt über den einen Resolver, `former_member`/`erased` werden als solche angezeigt.

### 4.2 Security-Audit

**PRIV-219** [unverändert] `security_audit_log` behält den Tombstone für 730 Tage; er enthält keinen
Freitext [verifiziert]. Neue Aktionen für Datenschutzvorgänge (`08` §4): `ERASURE_REQUESTED`,
`ERASURE_COMPLETED`, `EXPORT_REQUESTED`, `CONSENT_CHANGED`, `REDACTION_APPLIED`,
`REVIEW_DECIDED`, `ATTRIBUTION_REMOVED` (PRIV-116). `target_user_key` einer Löschzeile wird
**von Anfang an als Tombstone** geschrieben (der Schlüssel verschwindet gleich; der Anfrage-Datensatz
macht das bereits so).

### 4.3 Schwärzungs-Audit

**PRIV-220** Jede Schwärzung und jede Prüfentscheidung MUSS erzeugen: eine Zeile in
`garden_plan_audit`, wenn das Ziel eine Garden-Plan-Collection ist (bestehendes Muster), **oder** sonst eine
`security_audit_log`-Zeile (`REDACTION_APPLIED`, mandantenbezogen); dazu die Felder `decision`, `decided_by`,
`decided_at`, `reason_code`, `reason_text` des `privacy_review_items`-Eintrags
(≤ 500, selbst Freitext — Mitgliedern nicht angezeigt, für Leads des Mandanten sichtbar
und mit dem Eintrag gelöscht). Der *vorherige Wert* DARF NICHT irgendwo gespeichert werden (kein „Undo“
einer Schwärzung — sie ist eine Löschung im Sinne von Art. 17).

---

## 5. Freitext-Prüfwarteschlange (Datenschutzverwaltung)

### 5.1 Warum eine Warteschlange und keine Regel

Automatisches Löschen anhand von Freitext ist verboten (REQ-025 Regel 4) und falsch (der Text ist
meist die agronomische Aufzeichnung des Mandanten: „gegossen 10 L“, „Blattläuse auf Beet 3“). Reaktives
manuelles Schwärzen ohne Liste genügt nicht (#2517). Der Mittelweg: Das System
**findet** Kandidaten, ein Mensch **entscheidet**, die Entscheidung wird **protokolliert**.

### 5.2 Anlage von Einträgen

**PRIV-221** Wenn eine Kontolöschung committet (und wenn die Zurechnungsentfernung nach PRIV-116 läuft),
MUSS die Engine einen `privacy_review_items`-Eintrag pro `(tenant_key, collection,
row_key)` anlegen für jede Zeile, die (a) den Schlüssel der betroffenen Person in irgendeiner Zurechnungsrolle trug und
mindestens ein nicht leeres Prüffeld hat, **oder** (b) — nur wenn die betroffene Person einen `display_name` von
≥ 3 Zeichen hatte — in einem Prüffeld einen **Namens-Token** der betroffenen Person enthält. Namens-Token:
der Anzeigename, an Leerraum getrennt, Tokens mit ≥ 3 Buchstaben, Substring-Vergleich ohne Beachtung der Groß-/Kleinschreibung,
berechnet **bevor** die Nutzerzeile gelöscht wird und danach verworfen; der lokale Teil der E-Mail-Adresse wird
**nicht** verwendet (zu viele Fehltreffer, und er ist selbst personenbezogen und entsprechend
zu behandeln). Der Eintrag speichert `match_kinds ∈ {authored, performed, name_token}` und die Feld­namen —
**niemals den Text, niemals den Token, niemals den Schlüssel der betroffenen Person** (der `erasure_key` des Eintrags verweist auf den Anfrage-Datensatz,
dessen `user_key` der Tombstone ist).

**PRIV-222** Einträge MÜSSEN auf **ausschließlich geteilte Mandanten** begrenzt sein: Ein persönlicher Mandant der betroffenen Person
wird gelöscht; ein persönlicher Mandant einer anderen Person, in dem die betroffene Person beigetragen hat, *gilt*
für diesen Zweck als geteilt. Gesetzliche Zeilen erzeugen nur für `notes` einen Eintrag und nur dort, wo der Mandant
`record_keeping = none` hat oder die Zeile ihre gesetzliche Frist überschritten hat.

**PRIV-223** Die Anlage von Einträgen MUSS begrenzt sein: höchstens `PRIVACY_REVIEW_ITEMS_MAX_PER_ERASURE`
(Standard 5 000) pro Löschung; darüber hinaus vermerkt die Engine `review_items_truncated = true`,
und die Leads des Mandanten sehen ein Banner „Es gibt mehr Zeilen als aufgeführt — Pflegeprotokoll-Suche
nach Datum nutzen“. Der Namens-Token-Scan MUSS mit derselben begrenzten, seitenweisen AQL wie der Export lesen
(`test_beat_task_reads_are_paged`).

### 5.3 Prüfung und Entscheidung

**PRIV-224** Leads und `management` des Mandanten MÜSSEN die Warteschlange sehen
(`GET /t/{slug}/privacy/review?status=open|decided`, `08` §5), wobei jeder Eintrag über den normalen
(rollengeprüften) Lesepfad auf die aktuelle Zeile aufgelöst wird, sodass sie den Live-Text in der eigenen
Detailansicht der App ansehen.

**PRIV-225** Entscheidungen: `redact` (im Eintrag aufgelistete Felder oder eine Teilmenge) → die generische
Schwärzung (`§6`); `keep` mit `reason_code ∈ {no_personal_reference, agronomic_record,
third_party_consent, statutory}` und optionalem `reason_text`; `defer` (bleibt offen). Ein entschiedener
Eintrag DARF NICHT durch eine spätere Löschung einer *anderen* betroffenen Person, die dieselbe Zeile trifft, wieder geöffnet werden
— stattdessen wird ein neuer Eintrag angelegt (der Schlüssel enthält `erasure_key`).

**PRIV-226** Offene Einträge, die älter als `PRIVACY_REVIEW_SLA_DAYS` (Standard 30) sind, MÜSSEN auf der
Datenschutzseite des Mandanten als überfällig erscheinen und in der Plattform-Metrik
`privacy_review_items_open{tenant_kind}`; die Plattformadministration sieht nur Zählwerte (REQ-049 P4).
**[rechtlich LEG-08]** ob die verantwortliche Stelle (LEG-01) die Entscheidung den Leads des Mandanten überlassen darf
und ob 30 Tage gegenüber dem „unverzüglich“ aus Art. 17 Abs. 1 vertretbar sind.

**PRIV-227** Einträge und ihre Entscheidungen werden mit dem Mandanten und nach
`PRIVACY_REVIEW_ITEM_RETENTION_DAYS` (Standard 3 Jahre, abgestimmt auf R-06 als Nachweis der
Nachverfolgung der Löschung) gelöscht — NFR-011 braucht eine Zeile `R-43` (Spec-Änderungsvorschlag, `06`).

---

## 6. Generische Schwärzung

**PRIV-228** Ein Schwärzungs-Endpunkt pro Mandant MUSS mit der Zeit die Route nur für Care-Events ersetzen:
`POST /t/{slug}/privacy/redactions` mit Body `{collection, key, fields[], reason_code,
reason_text?, review_item_key?}`; das bestehende `POST /care-events/{key}/redact` bleibt bestehen und
delegiert. Zulässige `(collection, field)`-Paare sind das `REDACTABLE_FIELDS` der Registry
(= die Vereinigung der `review_fields`); alles andere ist 422 `redaction.field_not_redactable`.

**PRIV-229** Schwärzungssemantik je Feldtyp: String → `[redacted]` (Code `REDACTED`);
Liste von Strings (`tags`) → `[]`; verschachteltes JSON (`snapshot`) → die per Allowlist freigegebenen Blattfelder schwärzen;
`photo_refs` → Attachments werden wie heute gelöscht (`care_event_repository.redact`, vorher die
anderen Halter fragen gemäß `test_stored_object_deletes_ask_for_other_holders`). `redacted_at`,
`redacted_by`, `redaction_reason` der Zeile werden gesetzt, wo das Modell sie hat
(`care_events`); andere Modelle erhalten eine Metadatenliste `redactions: list[{field, at}]`, **nur wenn**
die UI den Chip anzeigen muss; andernfalls genügt die Audit-Zeile (Entscheidung je Collection in
`08` §3).

**PRIV-230** Die Schwärzung MUSS der Datenlinie folgen (`02` §5, `DERIVED_FIELDS`): Das Schwärzen von
`bed_templates.name` bietet die daraus erstellten Locations (`template_key`) und deren
`garden_plan_audit.summary`-Kopien als **Stapelvorschlag** in der UI an; sie werden nicht
automatisch geschwärzt (ein inzwischen vom Mandanten überschriebener Beetname gehört ihm). Das Schwärzen einer
Care-Event-Kette schwärzt die gesamte Supersede-Kette [verifiziert, GP-FR-109].

**PRIV-231** Wer schwärzen darf: Rolle `lead` oder Scope `management` (ACV, `05` §3). Heute:
`require_permission(CARE_EVENT, DELETE)` = nur Lead [verifiziert]. Die Aufnahme von `management` folgt
REQ-049 §2.4 („members, roles …“) — **Spec-Änderungsvorschlag**, weil der Scope heute keine
Datenrechte hat.

**PRIV-232** Die Schwärzung DARF NICHTS in einem anderen Mandanten berühren und MUSS idempotent sein
(das Schwärzen eines bereits geschwärzten Felds ist ein No-op mit 200).

---

## 7. Migration von Alt-Tombstones und -Markern (Verfahren siehe `09` §3)

**PRIV-233** Zu korrigierende Altzeilen, alle **[verifiziert]**:

| Befund | Korrektur |
|--------|-----------|
| `care_events.performed_by_user_key =~ ^anon_[0-9a-f]{16}$` (von v0104 / Konsistenz-Job aus gelöschten gesetzlichen Zeilen kopiert) | → `_anonymized`; Anzahl pro Mandant |
| `garden_plan_audit.user_key`-Tombstones (nach DEC-16) | → `_anonymized` |
| vor #1669/#1663 geschriebene Zeilen mit `*_by_key = null` und eingetipptem Anzeigenamen (`harvester`, `applied_by`, `inspector`, `assessed_by`) | **nicht** automatisch korrigierbar (REQ-025: ein Name ist kein Schlüssel); den Leads des Mandanten **einmalig** als Prüfeinträge aufgelistet, mit `match_kind = legacy_unkeyed_name`, begrenzt durch PRIV-223 |
| `attachments.original_filename` von Zeilen mit `created_by = _anonymized` | → `""` |
| `tenant_export_engine.ANONYMIZED_ACCOUNT` / drei Regex-Kopien | Code-Konsolidierung, keine Datenänderung |

---

## 8. Verifikation erfolgreicher Anonymisierung

**PRIV-234** Nach jeder Löschung MUSS der Executor die **Restbestandsprüfung (Residue-Scan)** ausführen, die die Mandantenlöschung
bereits hat (die Residue-Prüfung in `tenant_erasure_executor` meldet `undeclared:<collection>`
[verifiziert]), nun auch für die Kontolöschung: für jede Collection mit einem kontoförmigen Feld Zeilen zählen,
bei denen das Feld dem echten Schlüssel **oder** dem Tombstone der betroffenen Person entspricht (außerhalb der
Allowlist). Ein Wert ungleich null markiert die Löschung als `partially_completed` mit
`residue = {collection: count}`.

**PRIV-235** Die Reach-Tests (`tests/integration/test_account_erasure_reach.py`) MÜSSEN die
Negativfälle aus `10` §4 erhalten: Tombstone in einer nicht auf der Allowlist stehenden Collection, Marker in einem Tombstone-
Feld, Namens-Token in der Prüfwarteschlange, Darstellung eines geschlossenen Kontos.

**PRIV-236** „Anonymisiert“ DARF in keinem Bericht und keinem UI-Text für eine Zeile allein aufgrund eines Markers behauptet werden;
Berichte sagen „Zurechnung entfernt; N Freitext-Zeilen in Prüfung / entschieden“.

---

## 9. Vorher-/Nachher-Beispiele

### 9.1 Care-Event eines gelöschten Mitglieds (geteilter Mandant)

Vorher (Mitglied „Maren K.“ am 2026-12-01 gelöscht; ihr Schlüssel `u_7f3a`):

```json
{"_key":"ce_1","tenant_key":"t_garden","category":"watering",
 "summary":"Maren hat Beet 3 gegossen, 10 L","material":null,
 "performed_by_user_key":"u_7f3a","created_by":"u_7f3a","performed_by_label":null}
```

Nach dem Löschungs-Commit (heutiges Verhalten, beibehalten):

```json
{"_key":"ce_1","summary":"Maren hat Beet 3 gegossen, 10 L",
 "performed_by_user_key":"_anonymized","created_by":"_anonymized"}
```

Neu: ein Prüfeintrag (kein Text, kein Name):

```json
{"_key":"rvw_9c…","tenant_key":"t_garden","erasure_key":"erq_…","collection":"care_events",
 "row_key":"ce_1","fields":["summary"],"match_kinds":["performed","name_token"],
 "status":"open","created_at":"2026-12-01T04:12:00Z"}
```

Der Lead entscheidet `redact` → Zeile: `"summary":"[redacted]"`, `redacted_at/by/reason` gesetzt,
`garden_plan_audit`-Zeile `{op:"redact", entity:"care_event", summary:"watering"}`; Eintrag
`status:"decided", decision:"redact", decided_by:"u_lead"`.

API-Darstellung der Zeile für eine Grower-Rolle, vorher und nachher: `performed_by: null`,
`performed_by_kind: "erased"` (heute: `performed_by: "anonymisiert"`).

### 9.2 Behandlungsmaßnahme (gesetzlicher Mandant)

Vorher: `{"applied_by":"Maren K.","applied_by_key":"u_7f3a","notes":"Neem auf Tomaten, Maren hat die Dosis halbiert"}`
Nachher (heute unverändert): `{"applied_by":"","applied_by_key":"anon_3b9f…","notes":"… Maren hat …"}`
Neu: Prüfeintrag für `notes` **nur wenn** `record_keeping = none` oder die Zeile R-17 überschritten hat;
andernfalls bleibt die Zeile, wie sie ist (gesetzlicher Inhalt) — LEG-04 kann das ändern.

### 9.3 Alt-Tombstone, kopiert

Vorher (von v0104 am 2026-11-07 geschrieben): `care_events.performed_by_user_key = "anon_3b9f…"`
Nach der Migration `09` §3: `"_anonymized"`; Bericht `{tenant: t_garden, corrected: 12}`.

### 9.4 Name einer Beetvorlage

Vorher: `bed_templates {name:"Omas Hochbeet", created_by:"u_7f3a"}`;
`locations {name:"Omas Hochbeet", template_key:"bt_1"}`;
`garden_plan_audit {op:"delete", summary:"Omas Hochbeet"}`.
Nach der Löschung: Vorlage `created_by:"_anonymized"`, Name bleibt; Prüfeinträge für die
Vorlage (`name`), die Location (`name`, Datenlinie `template_key`) und die Audit-Zeile
(`summary`). Der Lead schwärzt die Vorlage und übernimmt den Stapelvorschlag → alle drei
`[redacted]`; oder behält mit `reason_code: no_personal_reference` („Oma“ ist nicht das Mitglied).

---

## 10. Abnahme (Zusammenfassung)

| ID | Kriterium |
|----|-----------|
| TA-200 | Eine Definition des Markers und der Tombstone-Regex; eine eingeschleuste zweite Kopie lässt den Guard fehlschlagen. |
| TA-201 | `carry_account_reference` bildet Tombstone/Marker → Marker für Marker-Felder, → `null` für Tombstone-Felder, Label → `null` ab. |
| TA-202 | Der Konsistenz-Beat meldet einen eingeschleusten Tombstone in `care_events` und einen eingeschleusten Marker in `treatment_applications.applied_by_key`. |
| TA-203 | Filter mit einem tombstone-förmigen `performed_by` → 422. |
| TA-204 | `material` und Messwert-Strings werden mit der Menge geschwärzt, durch Schwärzung und durch R-25. |
| TA-205 | Prüfeinträge werden für selbst verfasste Zeilen und Namens-Token-Zeilen angelegt, speichern keinen Text/Token/Schlüssel, sind pro Löschung idempotent und begrenzt. |
| TA-206 | Die generische Schwärzung weist ein nicht auf der Allowlist stehendes Feld zurück, ist idempotent, schreibt die Audit-Zeile nur mit Kategorie und speichert nie den alten Wert. |
| TA-207 | `garden_plan_audit.user_key` erhält den Marker; ein eingeschleuster Tombstone dort wird gemeldet. |
| TA-208 | Der Residue-Scan markiert eine Löschung als `partially_completed`, wenn eine eingeschleuste Zeile den echten Schlüssel oder den Tombstone außerhalb der Allowlist behält. |
| TA-209 | `original_filename` wird bei der Löschung geleert. |
