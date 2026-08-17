# Spezifikation: REQ-024 - Mandantenverwaltung & Gemeinschaftsgärten

```yaml
ID: REQ-024
Titel: Mandantenverwaltung & Gemeinschaftsgärten
Kategorie: Plattform & Kollaboration
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React, TypeScript, MUI
Status: Entwurf
Version: 1.7 (Nachführung auf REQ-049 v1.4 — die Standort-Zuweisung ist keine Schreibgrenze)
Abhängigkeit: REQ-049 v1.4 (Rollenmodell & verbindliches Vokabular — **Autorität bei Widerspruch**), REQ-023 v1.13 (Service Accounts, Plattform-Admin), NFR-016 (Migrations-Framework — `v0032`)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
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
| **Verwaltung** | `management` | Mitglieder einladen, Rollen ändern, entfernen; Einladungslinks; Mandanten-Einstellungen; Standort-Zuweisungen; Dienstkonten; Mandant löschen |
| **Technik** | `technical` | Home-Assistant- und InvenTree-Anbindung, MQTT, Sensor- und Aktor-Einrichtung, Import, Anreicherungs- und Wetterquellen |

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
| **E-Mail-Einladung** | Ein Mitglied mit **Verwaltung** gibt die E-Mail ein → System sendet Einladungs-E-Mail mit Link → Empfänger registriert sich oder meldet sich an → wird automatisch dem Tenant mit vorgewählter Rolle hinzugefügt |
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

Diese Aktionen hängen ausschließlich an der Zusatzberechtigung **Verwaltung** (REQ-049 §2.4) — die fachliche Rolle spielt keine Rolle. Eine Schriftführerin mit der Rolle Beobachter verwaltet die Mitgliederliste; eine Leitung ohne Verwaltung nicht.

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
| **Service Accounts verwalten** | ✅ (REQ-023 v1.7) | ❌ |
| **Tenant löschen** | ✅ (Soft-Delete) | ❌ |
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
    - `max_members: Optional[int]` (Mitgliederlimit, `null` = unbegrenzt)
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
| DELETE | `/tenants/{slug}` | Tenant löschen (Soft-Delete) | Verwaltung |

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
    max_members=None,
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
| AK-16 | Tenant-Löschung (Soft-Delete) setzt `status: deleted` und deaktiviert alle Memberships | Integration |
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
<!-- /Quelle: RBAC Permission-Matrix v1.4 -->
<!-- Quelle: Tenant-Notfallverwaltung v1.4 -->
| AK-45 | Der Platform-Admin kann die Mitgliederliste eines fremden Mandanten einsehen — die einzige Cross-Tenant-Leseerlaubnis der Plattform-Ebene | Integration |
| AK-46 | Platform-Viewer kann Mitgliederliste eines fremden Tenants read-only einsehen | Integration |
| AK-47 | Suspendierter Tenant: TenantSwitcher zeigt Tenant ausgegraut mit Hinweis "Suspendiert" | E2E |
| AK-48 | Suspendierter Tenant: Kein Zugriff auf Ressourcen (403 mit klarer Fehlermeldung) | Integration |
| AK-49 | Notfall-Admin ernennen, Tenant und User suspendieren und reaktivieren gelingt ausschließlich dem Platform-Admin (`lead` im Platform-Tenant) | Unit |
| AK-50 | Der Platform-Viewer darf Mitgliederlisten fremder Mandanten **lesen** — das ist die einzige Cross-Tenant-Leseerlaubnis der Rolle | Unit |
| AK-51 | Der Platform-Viewer kann weder einen Notfall-Admin ernennen noch Mandanten oder Nutzer suspendieren | Unit |
<!-- /Quelle: Tenant-Notfallverwaltung v1.4 -->

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
