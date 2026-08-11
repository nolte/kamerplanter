# ADR-009: Aktiver Mandant über den `X-Active-Tenant`-Header auf globalen Routen

## Status

Accepted — 2026-08-11

Hergeleitet aus der Issue-Orchestrierung zu #1091
(`.audits/issue-orchestrate/1091/analysis.md`) und der vorgelagerten
Anforderungserhebung (`project/requirements/active-tenant-resolution.md`, R1–R7,
Teach-back 2026-08-10). Die Entscheidung ist auf dem zugehörigen PR-Branch bereits
umgesetzt (`src/backend/app/common/auth.py`); dieses ADR hält die Signal-Wahl und
ihre Begründung fest und schließt damit die offene Designfrage **A1** aus #808
(siehe REQ-049 §2.11).

## Context

Die **globalen** Katalog-Routen — Arten, Sorten, botanische Familien und die
Companion-/Fruchtfolge-Anker — sind *pfadlos, aber mandantenbewusst*: Sie liegen
nicht unter `/api/v1/t/{tenant_slug}/…`, liefern aber je Mandant eine andere
Sicht (globaler Seed-Katalog **plus** die mandanteneigenen Arten/Sorten, #324 in
beide Richtungen) und stempeln beim Anlegen einen Eigentümer-Mandanten auf den
neuen Datensatz.

Diesen Routen fehlte bislang die eine fehlende Angabe: **in welchem Mandanten der
Aufrufer gerade handelt.** Der Resolver in `src/backend/app/common/auth.py`
(`get_active_tenant_key`, sein Alias `get_creating_tenant_key`,
`get_active_tenant_context`) löste hart den **persönlichen** Mandanten auf. Für ein
Org-Mitglied eines Gemeinschaftsgartens (REQ-024, O-4) war die org-eigene Sicht
auf den globalen Katalog damit unerreichbar, und ein Create landete im falschen
Mandanten. Das ist keine kosmetische Lücke: Es ist eine **stille
Kontext-Verwechslung** — die Anfrage wird bedient, aber im falschen Mandanten,
ohne dass der Aufrufer es merkt.

Betroffene Specs und Constraints:

- **REQ-049** (Rollenmodell) — die fachliche Rolle des Aufrufers muss aus dem
  Membership im *aktiven* Mandanten stammen, nicht aus dem persönlichen (§2.7);
  A1 war dort als offene Designfrage aus #808 vermerkt.
- **REQ-024** (Mandantenverwaltung) — die URL-Konvention `/api/v1/t/{tenant_slug}/…`
  benutzt bereits den **Slug** als menschenlesbaren Mandantenschlüssel.
- **NFR-001** (Schichtenarchitektur) — die Auflösung ist eine reine
  API-Schicht-Abhängigkeit (`Depends`), kein Durchgriff in tiefere Schichten.
- **SEC-005/#1113** — dasselbe Org-Kontext-Landing legt ein latentes
  Viewer-Write-Loch offen (ein Viewer der Org könnte über den globalen Create
  schreiben), das im selben Strang durch ein Rollen-Gate geschlossen wird.

## Decision

**Ein nicht-safelisted Request-Header `X-Active-Tenant` trägt den Mandanten-Slug,
in dem der Aufrufer auf einer globalen, mandantenbewussten Route handelt. Genau
ein Resolver wertet ihn aus — für Lesesichtbarkeit, Write-Stamping und die
Rollen-/Admin-Scope-Ableitung identisch.**

Ausführlich, als verbindliche Regeln:

1. **Ein Header, ein Slug.** `X-Active-Tenant` trägt einen Mandanten-**Slug**
   (menschenlesbar, symmetrisch zur `/t/{slug}/`-Pfadkonvention). Der Resolver
   bildet Slug→Key zentral ab; kein Aufrufer sieht den internen `tenant_key`.
2. **Ein Resolver, drei Sichten, die nicht divergieren können.**
   `get_active_tenant_key` (Read-Scope), `get_creating_tenant_key`
   (Write-Stamping, dasselbe Funktionsobjekt) und `get_active_tenant_context`
   (Rolle + Admin-Scopes) lösen den aktiven Mandanten über **einen** gemeinsamen
   internen Helfer aus demselben Header auf. Read-Sichtbarkeit und
   Eigentümer-Stempel können deshalb nie auf verschiedene Mandanten zeigen.
3. **Die Rolle stammt aus dem aktiven Mandanten.** Die fachliche Rolle des
   Aufrufers kommt aus seinem Membership im *aktiven* Mandanten. Ein Org-Beobachter
   erhält die `viewer`-Rolle der Organisation — **nie** die `lead`-Rolle seines
   persönlichen Mandanten. Das ist die Bedingung dafür, dass das Rollen-Gate aus
   REQ-049 §2.7 im Org-Kontext dasselbe misst wie auf den `/t/{slug}/`-Routen.
4. **Ungültiger Header → 403, orakelfrei.** Benennt der Header einen unbekannten
   Slug **oder** einen Mandanten, in dem der Aufrufer kein aktives Membership hat,
   antwortet das System mit `403` — mit **byte-identischer** Antwort für beide
   Fälle (abgesehen von `error_id`/Zeitstempel). Die Antwort ist damit **kein
   Slug-Existenz-Orakel**: Ein Angreifer kann aus ihr nicht ablesen, ob ein Slug
   existiert. Der gemeinsame Ablehnungspfad ist der Helfer `_membership_for_slug`
   mit der Konstante `_ACTIVE_TENANT_DENIED`.
5. **Niemals ein stiller Rückfall.** Ein ungültiger Header verengt oder
   verweigert, er erweitert nie. Das System fällt **nicht** still auf den
   persönlichen Mandanten oder auf globalen Scope zurück — denn genau diese stille
   Kontext-Verwechslung ist der Fehler, den dieses Feature behebt. Ein Rückfall
   würde ihn wieder öffnen.
6. **Kein Header → heutiges Verhalten.** Ohne Header gilt unverändert der
   persönliche Mandant; anonym/Light-Modus → globaler Scope `""`. Ein leerer oder
   nur aus Leerraum bestehender Header-Wert zählt bewusst als *abwesend*. Der Slug
   wird **nicht** case-gefoldet — jede Abweichung führt zur fail-safe-Ablehnung.
7. **CORS.** `X-Active-Tenant` ist nicht safelisted; die bestehende
   `allow_headers=["*"]`-Konfiguration lässt ihn im Preflight zu, ohne
   zusätzliche Änderung.

**Nicht Teil dieser Entscheidung:** Die `/t/{slug}/`-Routen binden den Mandanten
weiterhin über den Pfad (`get_current_tenant`). Favoriten bleiben
persönlich-über-Mandanten und werden vom Header **nicht** umgebunden. Die
MCP-Katalog-Tools bleiben global-only (ihr Umzug wäre eine öffentliche
Contract-Änderung — eigenes Folge-Issue).

## Alternatives Considered

**A — Aktiven Mandanten als JWT-Claim tragen.** Der aktive Mandant wäre ein
Anspruch im Access-Token. Verworfen aus zwei Gründen. Erstens: Ein Wechsel des
aktiven Mandanten würde einen Token-Refresh erzwingen — der Kontextwechsel ist
aber eine reine Anzeige-/Interaktionsentscheidung und darf nicht an den
Token-Lebenszyklus gekoppelt sein. Zweitens, und schwerer: Ein Claim **überlebt
eine mitten in der Sitzung entzogene Mitgliedschaft**. Das Token würde weiter
Zugriff behaupten, den die Datenbank nicht mehr gewährt. Der Header wird dagegen
**pro Request** gegen das *lebende* Membership ausgewertet — Entzug wirkt sofort.

**B — `/t/{slug}/`-Zwillinge der Katalog-Routen.** Jede globale Katalog-Route
zusätzlich unter einem Mandantenpfad anbieten. Verworfen (bereits im
Anforderungsartefakt `project/requirements/active-tenant-resolution.md`
zurückgewiesen): Das verdoppelt die Routen-Oberfläche **und** die Pflege der
Sichtbarkeits-Prädikate für jede Kategorie. Der Header trägt das eine fehlende Bit
ohne einen parallelen Routenbaum — die Sicht bleibt an einer Stelle definiert.

**C — Tenant-Key statt Slug im Header.** Den internen `tenant_key` direkt im
Header führen. Verworfen zugunsten des Slugs: Der Slug ist menschenlesbar,
symmetrisch zur `/t/{slug}/`-Pfadkonvention und damit im Frontend, in Logs und beim
Debuggen dieselbe Angabe. Die Abbildung Slug→Key erledigt der Resolver zentral —
der Aufrufer muss den internen Schlüssel nie kennen.

## Consequences

**Positiv**

- **Eine Entscheidungsstelle.** Read-Scope, Write-Stamping und Rollenableitung
  hängen an einem Resolver mit einem gemeinsamen Helfer. Sie können bei künftigen
  Änderungen nicht auseinanderlaufen — die teuerste Fehlerklasse dieses Bereichs
  („zwei Kopien einer Regel driften") ist strukturell ausgeschlossen.
- **Kein Existenz-Orakel an beiden Mandantengrenzen.** Package A-11 hat im selben
  Strang die `/t/{slug}/`-**Pfad**-Route nachgezogen: `get_current_tenant`
  antwortete zuvor **404** für einen unbekannten Slug, aber **403** für einen
  Nicht-Member — das war ein Slug-Existenz-Orakel. Sie antwortet jetzt für **beide**
  Fälle mit einem byte-identischen, orakelfreien **403** und teilt sich die
  Ablehnungsform (`_membership_for_slug`, `_ACTIVE_TENANT_DENIED`) mit dem
  Header-Resolver. **Beide Oberflächen — Pfad und Header — sind damit orakelfrei.**
- **Diese Angleichung ist der Grund, warum REQ-049 AK-09 von `404` auf `403`
  wandert.** AK-09 verlangte bislang, dass ein Plattform-Admin ohne Mitgliedschaft
  auf Fachdaten eines fremden Mandanten `404` erhält. Nach A-11 verweigert
  `get_current_tenant` einem Nicht-Member (auch einem Plattform-Admin ohne
  Membership) mit **403 vor jedem Datenzugriff** — die orakelfreie Ablehnung an der
  Mandantengrenze. Der bisherige `404`-Wortlaut widerspräche dem ausgelieferten,
  spec-getragenen Verhalten; AK-09 wird deshalb auf `403` korrigiert.
- **Sofortige Wirkung von Entzug.** Weil der Header pro Request gegen das lebende
  Membership prüft, verliert ein entzogenes Mitglied den Org-Kontext ohne Wartezeit
  auf einen Token-Ablauf.

**Negativ / Risiken**

- **Der Header muss zuverlässig gesetzt werden.** Das Frontend muss ihn zentral im
  API-Client führen, sobald ein Org-Kontext gewählt ist. Ein vergessener Header
  fällt (korrekt) auf den persönlichen Mandanten zurück — im Org-Kontext wäre das
  eine überraschend leere Sicht, kein Fehler. Die UI-Seite ist ein eigener Strang.
- **Die Orakelfreiheit ist eine Verhaltenszusage, keine Typgrenze.** Sie hängt an
  der byte-identischen Ablehnung über den gemeinsamen Helfer. Ein späterer
  Fix, der einen der beiden Fälle „hilfreicher" macht (etwa „Slug unbekannt" statt
  „kein Zugriff"), öffnet das Orakel wieder. Der Test muss die Gleichheit beider
  Antworten prüfen, nicht nur ihren Status.

**Folgemaßnahmen an Specs**

- **REQ-049** erhält §2.11 (Aktiver Mandant auf globalen Routen), einen
  Versionshistorie-Eintrag 1.4 und die AK-09-Korrektur `404`→`403`. A1 aus #808
  wird dort als geschlossen vermerkt.
- **REQ-024** bleibt unverändert; die `/t/{slug}/`-Pfadkonvention und der Slug als
  Mandantenschlüssel werden hier nur referenziert.
- Nach `Accepted` wird dieses ADR als Doku-ADR auf der MkDocs-Site gespiegelt
  (`docs/{de,en}/adr/`), wie die vorangegangenen ADRs.

## References

- `.audits/issue-orchestrate/1091/analysis.md` — Issue-Orchestrierung zu #1091,
  Work-Package-Zerlegung (A-1 Spec, A-11 Pfad-Orakel)
- `project/requirements/active-tenant-resolution.md` — Anforderungen R1–R7
  (Teach-back 2026-08-10), Alternative B dort zurückgewiesen
- Issue #1091 (Org-Kontext-Auflösung auf globalen mandantenbewussten Routen),
  Issue #808 (offene Designfrage A1), Issue #1113/SEC-005 (Create-Rollen-Gate)
- `src/backend/app/common/auth.py` — `get_active_tenant_key`,
  `get_creating_tenant_key`, `get_active_tenant_context`, `_membership_for_slug`,
  `_ACTIVE_TENANT_DENIED`, `get_current_tenant` (A-11), `ACTIVE_TENANT_HEADER`
- REQ-049 §2.7 (Rolle aus dem aktiven Mandanten), §2.11 (Aktiver Mandant),
  AK-09 (Mandantengrenze); REQ-024 (`/t/{slug}/`-Konvention, Slug als Schlüssel)
- NFR-001 (Schichtenarchitektur) — Auflösung als reine API-Schicht-Abhängigkeit
