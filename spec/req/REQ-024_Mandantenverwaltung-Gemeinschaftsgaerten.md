# Spezifikation: REQ-024 - Mandantenverwaltung & Gemeinschaftsgärten

```yaml
ID: REQ-024
Titel: Mandantenverwaltung & Gemeinschaftsgärten
Kategorie: Plattform & Kollaboration
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React, TypeScript, MUI
Status: Entwurf
Version: 1.2 (Gemeinschaftsgarten-Kollaboration)
Abhängigkeit: REQ-023 v1.1 (Benutzerverwaltung & Authentifizierung)
```

## 1. Business Case

**User Story (Gemeinschaftsgarten gründen):** "Als Initiator eines Gemeinschaftsgartens möchte ich eine Organisation in Kamerplanter anlegen und meine 12 Gartenmitglieder einladen können — damit wir gemeinsam unsere Beete planen, Aufgaben verteilen und Ernten dokumentieren."

**User Story (Parzelle zuweisen):** "Als Garten-Admin möchte ich einzelne Parzellen (Sites/Slots) bestimmten Mitgliedern zuweisen können — damit jedes Mitglied nur seine eigenen Beete sieht und bearbeitet, aber trotzdem die Gemeinschaftsflächen (Kompost, Gewächshaus) allen zugänglich bleiben."

**User Story (Mehrere Gärten):** "Als engagierter Gärtner bin ich sowohl in meinem privaten Balkongarten als auch im Gemeinschaftsgarten 'Grüne Oase e.V.' aktiv — ich möchte zwischen diesen Gärten wechseln können, ohne mich ab- und neu anzumelden."

**User Story (Mitglied einladen):** "Als Garten-Admin möchte ich Mitglieder per E-Mail-Einladung oder Einladungslink hinzufügen können — weil nicht alle Mitglieder technisch versiert sind und ein einfacher Link einfacher ist als eine Registrierungs-Anleitung."

**User Story (Aufgaben delegieren):** "Als Garten-Admin möchte ich Gieß-Aufgaben an bestimmte Mitglieder zuweisen können — damit klar ist, wer diese Woche die Tomaten gießt, und nicht dreimal gegossen oder gar nicht."

**User Story (Nur-Lese-Zugang):** "Als Garten-Admin möchte ich Besuchern oder Interessenten einen Nur-Lese-Zugang geben können — damit sie sich den Gartenplan ansehen können, ohne versehentlich Daten zu ändern."

**User Story (Privater Bereich):** "Als Mitglied eines Gemeinschaftsgartens möchte ich meine privaten Zimmerpflanzen in einem separaten, nur für mich sichtbaren Bereich verwalten — ohne dass die Gemeinschaft Zugriff auf meine Wohnungspflanzen hat."

**User Story (OIDC-Tenant-Zuweisung):** "Als Admin einer Anbauvereinigung möchte ich, dass sich Mitglieder über unseren zentralen Identity Provider (Keycloak) anmelden und automatisch unserem Tenant zugewiesen werden — ohne manuelle Einladung."

<!-- Quelle: Outdoor-Garden-Planner Review G-030 -->
**User Story (Gießdienst-Rotation):** "Als Gemeinschaftsgarten-Admin möchte ich einen rotierenden Gießdienst einrichten — jede Woche ist ein anderes Mitglied für die Gemeinschaftsbeete zuständig, und die App erinnert automatisch das diensthabende Mitglied."

**User Story (Dienst tauschen):** "Als Gartenmitglied möchte ich meinen Gießdienst mit einem anderen Mitglied tauschen können, wenn ich im Urlaub bin — ohne den Admin belästigen zu müssen."

<!-- Quelle: Outdoor-Garden-Planner Review G-031 -->
**User Story (Pinnwand):** "Als Gartenmitglied möchte ich Nachrichten und Hinweise an alle Mitglieder posten können — 'Schneckenalarm! Bitte Bierfallen aufstellen' oder 'Am Samstag 10 Uhr gemeinsames Kompost-Umsetzen'."

**User Story (Ernte teilen):** "Als Gartenmitglied möchte ich überschüssige Ernte den anderen anbieten können — 'Zu viele Zucchini — wer will?' — ohne eine WhatsApp-Gruppe dafür zu brauchen."

**User Story (Gemeinsame Bestellliste):** "Als Garten-Admin möchte ich eine gemeinsame Einkaufsliste für Saatgut, Erde und Werkzeuge pflegen können — damit wir Sammelbestellungen koordinieren und Kosten teilen können."

**Beschreibung:**
Kamerplanter wird vom Einbenutzer-System zur Multi-Tenant-Plattform erweitert. Der **Tenant** (Mandant) ist der zentrale Isolations-Container: Alle Ressourcen (Pflanzen, Standorte, Aufgaben, Ernten) gehören zu genau einem Tenant. Benutzer können Mitglied in mehreren Tenants sein — mit unterschiedlichen Rollen pro Tenant.

**Kernkonzepte:**

**Tenant — Organisatorischer Container:**
Ein Tenant repräsentiert eine logische Organisationseinheit: einen privaten Garten, einen Gemeinschaftsgarten, einen Verein oder einen Betrieb. Jeder Tenant hat einen eigenen, isolierten Datenraum.

- Bei Registrierung (REQ-023) wird automatisch ein **persönlicher Tenant** erstellt (`type: personal`)
- Gemeinschaftsgärten, Vereine und Betriebe werden als **organisatorische Tenants** erstellt (`type: organization`)
- Ein User kann Mitglied in beliebig vielen Tenants sein
- Ressourcen gehören immer zu genau einem Tenant (kein Cross-Tenant-Sharing)

**Mandantenspezifisches Rollenmodell:**
Ein User hat pro Tenant genau eine Rolle. Die Rolle bestimmt, was der User innerhalb dieses Tenants darf:

| Rolle | Schlüssel | Rechte |
|-------|-----------|--------|
| **Admin** | `admin` | Vollzugriff: Tenant-Einstellungen, Mitgliederverwaltung, alle Ressourcen, Rollenzuweisung. Duty-Rotations erstellen/bearbeiten, Pinnwand-Posts pinnen/löschen, Shopping-Lists verwalten |
| **Gärtner** | `grower` | Lese- und Schreibzugriff auf zugewiesene und gemeinschaftliche Ressourcen, Aufgaben erstellen/bearbeiten, Ernten dokumentieren. An Duty-Rotation teilnehmen, Tausch anfragen, Pinnwand-Posts erstellen/kommentieren, auf Shopping-Lists eintragen |
| **Beobachter** | `viewer` | Nur-Lese-Zugriff auf alle Ressourcen des Tenants, keine Änderungen möglich. Pinnwand lesen, Shopping-Lists lesen (kein Schreiben) |

**Zuweisungsbasierte Sichtbarkeit:**
Innerhalb eines organisatorischen Tenants können Standorte (Sites, Locations, Slots) einzelnen Mitgliedern zugewiesen werden:

- **Zugewiesene Ressourcen:** Nur der zugewiesene Gärtner (und Admins) darf diese bearbeiten
- **Gemeinschaftliche Ressourcen:** Ohne Zuweisung → für alle Gärtner des Tenants bearbeitbar
- **Viewer** sehen immer alles (read-only), unabhängig von Zuweisungen

**Einladungssystem:**

| Methode | Flow |
|---------|------|
| **E-Mail-Einladung** | Admin gibt E-Mail ein → System sendet Einladungs-E-Mail mit Link → Empfänger registriert sich oder meldet sich an → wird automatisch dem Tenant mit vorgewählter Rolle hinzugefügt |
| **Einladungslink** | Admin generiert Link (optional: max. Nutzungen, Ablaufdatum, vordefinierte Rolle) → Link kann geteilt werden (WhatsApp, Aushang) → Jeder mit Link kann beitreten |
| **OIDC-Auto-Join** | OIDC-Provider hat `default_tenant_key` konfiguriert (REQ-023) → Neue User über diesen Provider werden automatisch dem Tenant hinzugefügt |

### 1.1 Szenarien

**Szenario 1: Gemeinschaftsgarten gründen — "Grüne Oase e.V."**
```
1. Lisa (bereits registriert) navigiert zu /tenants/create
2. Erstellt Tenant:
   name: "Grüne Oase e.V."
   type: organization
   description: "Gemeinschaftsgarten in Berlin-Kreuzberg, 24 Parzellen"
3. Lisa wird automatisch Admin dieses Tenants
4. Lisa erstellt Einladungslink:
   role: grower
   max_uses: 20
   expires_in: 30 Tage
5. Lisa teilt den Link in der WhatsApp-Gruppe des Vereins
6. 11 Mitglieder klicken den Link → werden als "Gärtner" hinzugefügt
7. Lisa ändert 2 Mitglieder zu "Admin" (Stellvertretung)
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

Sichtbarkeit für Max (Rolle: grower):
  ✅ Lesen: Alle Locations des Tenants
  ✅ Schreiben: "Parzelle A1" (zugewiesen) + "Kompostplatz" + "Gewächshaus" (Gemeinschaft)
  ❌ Schreiben: "Parzelle A2" (Lisas) + "Parzelle A3" (Toms)
```

**Szenario 3: Zwischen Gärten wechseln**
```
Max ist Mitglied in:
  1. "Maxs Garten" (personal, Admin) — 8 Zimmerpflanzen
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
  - default_role: "grower"

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

1. Admin Lisa erstellt Task im Gemeinschaftsgarten:
   title: "Tomaten gießen — Parzelle A1-A6"
   assigned_to: Max (user_key)
   due_date: 2026-03-15
2. Max sieht den Task in seiner persönlichen Task-Queue
3. Max markiert Task als erledigt
4. Lisa sieht im Admin-Dashboard: Task erledigt von Max, 2026-03-15 14:30
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

1. Admin Lisa erstellt Duty-Rotation:
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
   System benachrichtigt beide + Admin

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

5. Admin Lisa pinnt einen Beitrag:
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
    - `description: Optional[str]` (Beschreibung, z.B. "Gemeinschaftsgarten in Berlin-Kreuzberg")
    - `avatar_url: Optional[str]` (Logo/Bild der Organisation)
    - `settings: dict` (Tenant-spezifische Einstellungen, z.B. Default-Sprache, Zeitzone)
    - `max_members: Optional[int]` (Mitgliederlimit, `null` = unbegrenzt)
    - `status: Literal['active', 'suspended', 'deleted']`
    - `created_at: datetime`
    - `updated_at: datetime`

- **`:Membership`** — Mitgliedschaft (User ↔ Tenant)
  - Collection: `memberships`
  - Properties:
    - `role: Literal['admin', 'grower', 'viewer']`
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
    - `role: Literal['admin', 'grower', 'viewer']` (Rolle bei Beitritt)
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
    - `pinned: bool` (Angepinnt = bleibt oben, nur Admin)
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

**Globale Collections (Tenant-unabhängig):**

| Collection | Begründung |
|-----------|-----------|
| `botanical_families` | Botanische Stammdaten sind global/wissenschaftlich |
| `species` | Arten sind global (GBIF/Perenual) |
| `cultivars` | Sorten sind global (können von mehreren Tenants genutzt werden) |
| `pests`, `diseases`, `treatments` | IPM-Stammdaten sind global |
| `users` | User-Accounts existieren unabhängig von Tenants |
| `oidc_provider_configs` | System-Level-Konfiguration |

**Hinweis zu Seed-Daten in Tenant-scoped Collections:**
Einige Tenant-scoped Collections enthalten vorinstallierte Seed-Daten (z.B. `workflow_templates` mit 3 Workflows/16 Task-Templates aus REQ-006, `fertilizers` mit Standard-Düngern). Bei Erstellung eines neuen Tenants werden die System-Seed-Daten **als Kopie** in den Tenant übernommen (`tenant_key` wird gesetzt). Der Tenant-Admin kann diese anschließend anpassen oder löschen. Globale Stammdaten (Species, Cultivars, IPM) werden hingegen **referenziert, nicht kopiert** — alle Tenants teilen sich dieselben botanischen Daten.

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

// Admin darf alles bearbeiten
LET is_admin = membership.role == 'admin'

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

      LET is_assigned_to_me = LENGTH(
        FOR a IN assignments FILTER a.user_key == user_key RETURN 1
      ) > 0

      LET is_community = LENGTH(assignments) == 0

      LET can_edit = is_admin OR is_assigned_to_me OR (is_community AND membership.role == 'grower')

      RETURN {
        location: loc,
        can_edit: can_edit,
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
    ROLE_HIERARCHY = {'admin': 3, 'grower': 2, 'viewer': 1}

    def can_manage_members(self, actor_role: str) -> bool: ...
        # Nur Admin

    def can_assign_role(self, actor_role: str, target_role: str) -> bool: ...
        # Admin kann alle Rollen zuweisen
        # Niemand kann sich selbst zum Admin machen

    def can_edit_resource(self, membership: Membership, resource_tenant_key: str,
                          resource_assignments: list[LocationAssignment],
                          user_key: str) -> bool: ...
        # Admin → immer True
        # Grower → True wenn zugewiesen ODER Gemeinschaftsressource
        # Viewer → immer False

    def can_view_resource(self, membership: Membership, resource_tenant_key: str) -> bool: ...
        # Alle Rollen → True wenn im gleichen Tenant

    def validate_not_last_admin(self, tenant_memberships: list[Membership],
                                 target_user_key: str) -> bool: ...
        # Verhindert das Entfernen/Degradieren des letzten Admins
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
        # User wird Admin

    async def create_organization(self, user: User, name: str, description: str = None) -> Tenant: ...
        # Prüft: Max 10 Orgs pro User
        # Generiert Slug (TenantEngine)
        # Erstellt Tenant + Admin-Membership

    async def get_tenant(self, tenant_key: str, user: User) -> Tenant: ...
        # Prüft: User ist Mitglied
    async def update_tenant(self, tenant_key: str, user: User, updates: TenantUpdate) -> Tenant: ...
        # Nur Admin
    async def delete_tenant(self, tenant_key: str, user: User) -> None: ...
        # Nur Admin, Soft-Delete, warnt bei aktiven Mitgliedern

    async def list_my_tenants(self, user: User) -> list[TenantWithRole]: ...
        # Alle Tenants des Users mit jeweiliger Rolle

    # --- Mitgliederverwaltung ---
    async def list_members(self, tenant_key: str, user: User) -> list[MemberInfo]: ...
        # Alle aktiven Mitglieder mit Rolle
    async def update_member_role(self, tenant_key: str, user: User,
                                  target_user_key: str, new_role: str) -> Membership: ...
        # Nur Admin, verhindert Degradierung des letzten Admins
    async def remove_member(self, tenant_key: str, user: User, target_user_key: str) -> None: ...
        # Admin entfernt Mitglied, oder Mitglied entfernt sich selbst (Leave)
        # Verhindert Entfernung des letzten Admins
    async def leave_tenant(self, tenant_key: str, user: User) -> None: ...
        # User verlässt Tenant freiwillig
        # Verhindert wenn letzter Admin

    # --- Einladungen ---
    async def create_email_invitation(self, tenant_key: str, user: User,
                                       email: str, role: str) -> Invitation: ...
        # Nur Admin, sendet Einladungs-E-Mail
    async def create_link_invitation(self, tenant_key: str, user: User,
                                      role: str, max_uses: int = None,
                                      expires_in_days: int = None) -> InvitationLink: ...
        # Nur Admin, gibt Link + Token zurück
    async def accept_invitation(self, token: str, user: User) -> Membership: ...
        # Validiert Token, erstellt Membership, erhöht use_count
    async def revoke_invitation(self, tenant_key: str, user: User,
                                 invitation_key: str) -> Invitation: ...
        # Nur Admin, setzt status → revoked
    async def list_invitations(self, tenant_key: str, user: User) -> list[Invitation]: ...
        # Nur Admin

    # --- Standort-Zuweisungen ---
    async def assign_location(self, tenant_key: str, user: User,
                               location_key: str, target_user_key: str,
                               role: str = 'responsible',
                               valid_from: date = None,
                               valid_until: date = None) -> LocationAssignment: ...
        # Nur Admin
    async def unassign_location(self, tenant_key: str, user: User,
                                 assignment_key: str) -> None: ...
        # Nur Admin
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

def require_tenant_role(min_role: str):
    """Factory-Dependency: Prüft ob User mindestens die angegebene Rolle im Tenant hat.
    require_tenant_role('admin') → nur Admins
    require_tenant_role('grower') → Admins und Gärtner
    require_tenant_role('viewer') → alle Mitglieder"""
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
| GET | `/tenants/{slug}` | Tenant-Details abrufen | Mitglied |
| PATCH | `/tenants/{slug}` | Tenant aktualisieren | Admin |
| DELETE | `/tenants/{slug}` | Tenant löschen (Soft-Delete) | Admin |

**Router: `/api/v1/tenants/{slug}/members`** — Mitgliederverwaltung:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/tenants/{slug}/members` | Mitglieder auflisten | Mitglied |
| PATCH | `/tenants/{slug}/members/{user_key}` | Rolle ändern | Admin |
| DELETE | `/tenants/{slug}/members/{user_key}` | Mitglied entfernen | Admin |
| POST | `/tenants/{slug}/leave` | Tenant verlassen | Mitglied |

**Router: `/api/v1/tenants/{slug}/invitations`** — Einladungen:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/tenants/{slug}/invitations` | Einladungen auflisten | Admin |
| POST | `/tenants/{slug}/invitations/email` | E-Mail-Einladung senden | Admin |
| POST | `/tenants/{slug}/invitations/link` | Einladungslink generieren | Admin |
| DELETE | `/tenants/{slug}/invitations/{key}` | Einladung widerrufen | Admin |
| POST | `/invitations/accept` | Einladung annehmen (Token im Body) | Ja |

**Router: `/api/v1/t/{tenant_slug}/assignments`** — Standort-Zuweisungen:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| GET | `/t/{slug}/assignments` | Zuweisungen auflisten (Filter: location, user) | Mitglied |
| POST | `/t/{slug}/assignments` | Zuweisung erstellen | Admin |
| PATCH | `/t/{slug}/assignments/{key}` | Zuweisung aktualisieren | Admin |
| DELETE | `/t/{slug}/assignments/{key}` | Zuweisung entfernen | Admin |

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
- Zeigt aktuelle Rolle als Chip (Admin: rot, Gärtner: grün, Beobachter: grau)
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
  role: 'admin' | 'grower' | 'viewer';
  memberCount: number;
}

// Thunks:
// loadMyTenants() → setzt myTenants
// switchTenant(slug) → setzt activeTenant, aktualisiert URL
// createOrganization(name, description) → erstellt Tenant, fügt zu myTenants hinzu
```

### 4.5 Berechtigungs-Hooks

```typescript
function useTenantPermissions(): TenantPermissions {
  // Gibt Objekt mit Berechtigungsprüfungen zurück:
  // canEdit(resourceTenantKey, assignments): boolean
  // canManageMembers: boolean
  // canInvite: boolean
  // canAssignLocations: boolean
  // isAdmin: boolean
  // isGrowerOrAbove: boolean
}

function useCanEditLocation(locationKey: string): boolean {
  // Kombiniert: Tenant-Rolle + LocationAssignment-Prüfung
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
      "role": "admin"
    },
    {
      "_user": "demo@kamerplanter.local",
      "_tenant": "gemeinschaftsgarten-sonnenschein",
      "role": "admin"
    }
  ]
}
```

## 6. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Bei Registrierung (REQ-023) wird automatisch ein persönlicher Tenant (`type: personal`) erstellt | Integration |
| AK-02 | User kann maximal 10 organisatorische Tenants erstellen | Unit + Integration |
| AK-03 | Tenant-Slug wird URL-sicher generiert (Umlaute, Sonderzeichen korrekt) | Unit |
| AK-04 | User kann zwischen Tenants wechseln ohne Neuanmeldung | E2E |
| AK-05 | Ein User kann in Tenant A "Admin" und in Tenant B "Viewer" sein | Integration |
| AK-06 | E-Mail-Einladung sendet E-Mail und erstellt bei Annahme korrekte Membership | Integration |
| AK-07 | Einladungslink mit `max_uses: 5` wird nach 5 Nutzungen ungültig | Integration |
| AK-08 | Einladungslink mit `expires_at` wird nach Ablauf ungültig | Integration |
| AK-09 | OIDC-Provider mit `default_tenant_key` weist neue User automatisch dem Tenant zu | Integration |
| AK-10 | Letzter Admin eines Tenants kann weder entfernt noch degradiert werden | Unit + Integration |
| AK-11 | Grower sieht alle Locations (read), kann aber nur zugewiesene + Gemeinschafts-Locations bearbeiten | Integration |
| AK-12 | Viewer kann keine Ressourcen im Tenant erstellen, ändern oder löschen | Integration |
| AK-13 | Admin sieht und bearbeitet alle Ressourcen im Tenant | Integration |
| AK-14 | Ressourcen eines Tenants sind für Nicht-Mitglieder unsichtbar (kein Cross-Tenant-Zugriff) | Integration |
| AK-15 | LocationAssignment mit `valid_from`/`valid_until` wird außerhalb des Zeitraums nicht berücksichtigt | Unit |
| AK-16 | Tenant-Löschung (Soft-Delete) setzt `status: deleted` und deaktiviert alle Memberships | Integration |
| AK-17 | Task-Zuweisung (`assigned_to`) im Tenant-Kontext: nur Mitglieder des Tenants wählbar | Integration |
| AK-18 | Persönlicher Tenant ist für andere User unsichtbar | Integration |

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | TenantSwitcher zeigt alle Tenants des Users mit korrekter Rolle | E2E |
| FK-02 | Tenant-Wechsel aktualisiert URL (`/t/{slug}/...`) und lädt tenant-spezifische Daten | E2E |
| FK-03 | MemberListPage zeigt korrekte Rollen-Chips und erlaubt Admins die Rollenzuweisung | E2E |
| FK-04 | InviteDialog generiert funktionierenden Einladungslink | E2E |
| FK-05 | AssignmentListPage zeigt Matrix Location × Mitglied mit korrekter Farbcodierung | E2E |
| FK-06 | Nicht-Admin-User sehen keine Admin-Funktionen (Mitglieder verwalten, Einstellungen) | E2E |
| FK-07 | Viewer sehen keine Bearbeiten-/Erstellen-Buttons | E2E |

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| **REQ-023** | Benutzerverwaltung — User-Entität, JWT-Token mit `tenant_roles` |
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
- Mandantenspezifisches 3-Rollen-Modell (Admin, Grower, Viewer)
- Einladungssystem (E-Mail + Link + OIDC-Auto-Join)
- Standort-Zuweisung an Mitglieder (mit saisonalen Zeiträumen)
- Tenant-Switcher im Frontend
- Tenant-scoped API-Routing
- Tenant-Key auf allen bestehenden Ressourcen
<!-- Quelle: Outdoor-Garden-Planner Review G-030, G-031 -->
- Duty-Rotation (rotierende Dienstpläne, z.B. Gießdienst) mit Tausch-Funktion
- Pinnwand / Bulletin-Board (Posts, Kommentare, Reaktionen, Pinned-Posts)
- Gemeinsame Einkaufslisten (Sammelbestellungen koordinieren)

**Nicht in Scope (bewusst ausgeklammert):**
- Fein-granulare Permissions (z.B. "darf nur Gießen-Tasks erstellen") → 3 Rollen genügen initial
- Audit-Log (wer hat was geändert) → zukünftige REQ
- Cross-Tenant-Ressourcen-Sharing (z.B. geteilte Düngerliste) → Resourcen sind immer tenant-scoped
- Tenant-Billing / Abrechnung → SaaS-Modell zukünftig
- Hierarchische Tenants (Tenant-in-Tenant) → flache Struktur genügt
- Automatische Parzellen-Rotation (saisonaler Wechsel der Zuweisungen) → manuell
- Echtzeit-Chat/Direct-Messaging zwischen einzelnen Mitgliedern → externe Tools (WhatsApp, Signal); Pinnwand deckt asynchrone Kommunikation ab
- DSGVO-Export pro Tenant → zukünftig, nach Audit-Log
