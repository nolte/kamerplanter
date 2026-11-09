# SPEC-05 — Zugriffs- und Sichtbarkeitsmatrix

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Anforderungs-IDs: PRIV-300 … PRIV-339
Abhängig von: REQ-049 (Rollen), REQ-024 (Mandanten), 01 §4 (Zurechnungsrollen), 03 §3 (ehemalige Mitglieder),
06 §5 / 15 DA-04 (Personengruppen), 13 (L-09, L-10)
Änderung v1.1: Defaults der Sichtbarkeit je Mandantenklasse, Rollennamen vereinheitlicht (W-12), Legende PRIV-316.
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
| **X** Mandantenarchiv (REQ-056) | – | – | – | – | ja ! [v: management + Step-up] | ja ! | Export verwaister Mandant ! | – |
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

---

## 4. Mandanteneinstellung `attribution_visibility` [Vorschlag, DEC-10]

**PRIV-300** Ein Mandant MUSS `settings.attribution_visibility ∈ {all_members,
leads_and_self}` führen, mit Standard `all_members` (heutiges Verhalten, REQ-049 P2 „keine privaten Bereiche
within a tenant"). Bei `leads_and_self` werden die Dimensionen P/C/K/M für Viewer und
Grower als **R** dargestellt, außer die Zeile ist ihre eigene (`eigene` → N). Leads und `management` sehen für
aktuelle Mitglieder immer N.

**PRIV-301** Die Einstellung DARF NUR von `lead ∧ management` geändert werden können, mit dem in der UI angezeigten
Grund: „In Betrieben mit Beschäftigten kann das Gesetz verlangen, dass die Aktivität einzelner Beschäftigter nicht für
alle Kolleginnen und Kollegen sichtbar ist (Art. 88 DSGVO, § 26 BDSG, § 87 Abs. 1 Nr. 6 BetrVG); für Vereinsmitglieder
und Ehrenamtliche gilt § 26 BDSG nicht (§ 26 Abs. 8 BDSG)“ (L-09, L-10; PRIV-414). **Defaults nach Mandantenklasse
(DA-04, löst die v1.0-Formulierung ab):** `personal` → `all_members`; `organization_kind = commercial` →
`leads_and_self`; `association`/`community`/`other` → `all_members`; Bestandsmandanten (`unknown_legacy`) →
`all_members` (keine stille Änderung). **[LEGAL_REVIEW_REQUIRED LEG-05]** ob `leads_and_self` für gewerbliche
Mandanten verpflichtend sein muss.

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
`service_account`).

---

## 7. Plattformebene

**PRIV-311** Der Plattformbetreiber DARF durch dieses Paket KEINEN Lesezugriff auf die Dimensionen P/C/K/M/F/H erhalten. Der Endpunkt für Datenschutzvorgänge
(`08` §5) liefert **Zähler** pro Mandant und **Zustände** der Vorgänge; die Löschvorschau und
`GET /admin/platform/erasures/{key}` bleiben wie heute [verifiziert].

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

---

## 9. Audit-Protokollierung datenschutzrelevanter Lesezugriffe

**PRIV-316** Die folgenden Lesezugriffe MÜSSEN eine `security_audit_log`-Zeile schreiben (Akteur, Mandant,
Aktion, Anzahl; kein Inhalt): Exporte mit Namen (PRIV-308), Mandantenarchiv, Löschvorschau des Plattform-Admins,
Entscheidungen in der Prüfwarteschlange. Gewöhnliche Listenzugriffe DÜRFEN NICHT auditiert werden (Volumen
und REQ-049 („keine Überwachung von Mitgliedern")).

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
