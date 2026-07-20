# Audit: Master-Data-Capture-Qualität (Cross-cutting)

**Erstellt von:** Master-Data-Capture-Audit (Claude Code, Opus 4.8) — Issue #611 Workstream 4
**Datum:** 2026-07-20
**Frage:** An welchen Stellen wird ein Master-Data-Attribut *upstream* erfasst (Steckbrief / Schema),
aber *downstream* verworfen, ignoriert oder hart defaultet (Seed-Loader / Resolver / API / Frontend / HA)?
**Methode:** End-to-End-Trace jedes lebenszyklus-relevanten Attributs entlang der Kette
Steckbrief → Seed-YAML → Seed-Loader → Domain-Model → API → Frontend → HA; statische Analyse, kein DB-Lauf.
**Bezug:** Baut auf `spec/analysis/seed-phase-sequence-audit.md` (#586) auf; der dort behobene
`indoor_default`-Blankett-Link (via #616) ist der **Archetyp** des gesuchten Musters.

> **Scope-Hinweis:** Reiner Analyse-/Findings-Report. Größere Findings sind als Folge-Issue-Vorschläge
> (Abschnitt 5) gelistet — dieser Report erzeugt **keine** GitHub-Issues und ändert **keinen** Produktivcode.
> Ausnahme: die im Zuge der Verifikation (WS2) korrigierten Steckbrief-`growth_habit`-Werte (Finding **NCT-3**)
> wurden direkt gefixt, weil es eine eindeutige biologische Korrektur ohne Verhaltensrisiko ist.

---

## 1. Kernbefund

Das in #586/#616 aufgedeckte und behobene `indoor_default`-Muster ist **kein Einzelfall**. Der End-to-End-Trace
der lebenszyklus-treibenden Attribute findet **8 weitere Instanzen** desselben „specified-but-not-carried-through"-
Musters plus **3 unterspezifizierte Anforderungen**. Der rote Faden: die **Steckbriefe (210) sind reicher als der
Seed**, der **Seed ist reicher als die API-getriebene Erfassung**, und die **Frontend-Erfassungsmasken exponieren
mehrere der Attribute nicht**, von denen der attributgetriebene Resolver (REQ-003 §D14) abhängt.

| Kennzahl | Wert |
|---|---|
| Getracete lebenszyklus-treibende Attribute | 7 (`flowering_strategy`, `photosynthesis_type`, `photoperiod_type`, `growth_habit`, `cycle_type`, `cultivation_cycle_type`, `growth_determinacy`) |
| Findings gesamt | **11** |
| davon `not-carried-through` (NCT) | **8** |
| davon `unclear-requirement` (UR) | **3** |
| In diesem PR bereits behoben | **2** (NCT-3 Steckbrief-`growth_habit`; NCT-8 REQ-001-`growth_determinacy`) |
| Vorgeschlagene Folge-Issues | **5** |

**Schärfste Einzelbefunde:**

1. **NCT-1 — Der Seed-Resolver kann die photoperiodische Kohorte nicht reproduzieren.** Die 11
   Kurztag-Zierpflanzen tragen `photoperiod_type: short_day` **im Steckbrief**, aber **nicht** im Seed
   (`plant_info_*.yaml` haben keinen `lifecycle_configs`-Block für sie). Der Seed-Resolver (`resolve_phase_sequence_name`)
   liest `photoperiod_type` aus der `LifecycleConfig` — die für diese Arten `None`/`day_neutral` ist. Folge: auf einer
   **Frischinstallation** kann der Resolver `photoperiodic_ornamental` **nicht** erzeugen; die Korrektheit hängt allein
   am hartkodierten Frozen-Dict der **Migration v0027**. Genau das Muster, das #616 eigentlich beheben sollte —
   für diese Kohorte ist der Resolver **inert**.

2. **NCT-5 — Die Erfassungs-UI kann die Resolver-Eingaben nicht setzen.** Der `SpeciesCreateDialog` bietet im
   `growth_habit`-Dropdown nur **5 von 12** Enum-Werten (`herb, shrub, tree, vine, groundcover`) — die
   resolver-kritischen `fern`, `bulb_geophyte`, `epiphyte`, `succulent` fehlen. Ein per-UI angelegter Farn/Geophyt/
   Aufsitzer bekommt `herb` und wird vom Resolver falsch getypt. `photosynthesis_type` (CAM) und `growth_determinacy`
   sind **gar nicht** im Frontend erfassbar. Ein Resolver, der auf `growth_habit`/`photosynthesis_type` schlüsselt, ist
   wertlos, wenn die Maske diese Achsen nicht anbietet (vgl. #610).

---

## 2. End-to-End-Trace der lebenszyklus-treibenden Attribute

Legende: ✓ = getragen/erfasst · ⚠ = teilweise/defekt · ✗ = verworfen/nicht erfasst · — = n/a.

| Attribut | Steckbrief | Seed-YAML | Seed-Loader | Domain-Model | API (`SpeciesResponse`) | Frontend-Erfassung | Resolver-Input | Finding |
|---|---|---|---|---|---|---|---|---|
| `cycle_type` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (`LifecycleConfigSection`) | ✓ | — |
| `cultivation_cycle_type` | ✓ | ✓ (`species.yaml/overrides`) | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `flowering_strategy` | ✓ | ✓ (`species.yaml/overrides`) | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `photoperiod_type` | ✓ (inkl. `short_day`) | ⚠ **nur wo `lifecycle_configs`-Block** | ⚠ | ✓ | ✓ | ✓ | ⚠ | **NCT-1** |
| `photosynthesis_type` (CAM) | ✓ | ✓ (`species`-Feld) | ✓ | ✓ | ✓ | ✗ **nicht erfassbar** | ✓ | **NCT-6** |
| `growth_habit` | ⚠ **war `herb` statt fern/epiphyte/bulb_geophyte** | ✓ | ✓ | ✓ | ✓ | ⚠ **Dropdown 5/12 Werte** | ✓ | **NCT-3, NCT-5** |
| `growth_determinacy` | ⚠ (nur wo gepflegt) | ✓ (`species.yaml/overrides`) | ✓ | ✓ | ✗ **nicht im API-Typ** | ✗ **nicht erfassbar** | (E4) | **NCT-4, NCT-8** |

**Kritischste Drop-Punkte:**

- **Seed-Loader (`_build_lifecycle_configs`, `seed_plant_info.py:282`):** eine `LifecycleConfig` mit
  `photoperiod_type` entsteht **nur**, wenn die YAML einen top-level `lifecycle_configs:`-Block mit dem
  Scientific-Name als Key hat. Für die 11 photoperiodischen Zierpflanzen fehlt dieser Block → keine
  `photoperiod_type`-Erfassung im Seed → Resolver-Regel 1 (`short_day AND perennial`) feuert nie (**NCT-1**).
- **Frozen Whitelist (`seed_adventskalender.py:95`, `optional_fields`):** nur die 27 gelisteten Felder werden
  aus der YAML in das `Species`-Objekt übernommen; jedes andere Attribut (u. a. `photosynthesis_type`,
  `growth_determinacy`, die Umgebungs-Physiologie-Felder aus REQ-001 v4.2) wird stumm verworfen (**NCT-7**,
  #453-Archetyp).
- **Frontend (`SpeciesCreateDialog.tsx:36`, `LifecycleConfigSection.tsx`):** `growth_habit` truncated auf 5 Werte
  (**NCT-5**); `photosynthesis_type` und `growth_determinacy` fehlen komplett (**NCT-4/NCT-6**).

---

## 3. Findings

### 3.1 `not-carried-through` (NCT)

#### NCT-1 — Photoperiodische Kohorte: `short_day` erfasst, aber nicht im Seed getragen · **hoch**
**Kette:** Steckbrief ✓ → Seed-YAML ✗ → Resolver ⚠ → Migration ✓ (hartkodiert).
Die 11 Arten (`Euphorbia pulcherrima`, `Kalanchoe blossfeldiana`/`daigremontiana`, `Schlumbergera truncata`,
`Rhododendron simsii`, `Gardenia jasminoides`, `Jasminum polyanthum`, `Stephanotis floribunda`, `Aphelandra
squarrosa`, `Dahlia pinnata`/`x cultorum`) tragen `photoperiod_type: short_day` im Steckbrief, aber keinen
`lifecycle_configs`-Block im Seed. `resolve_phase_sequence_name` liest `photoperiod_type` aus der `LifecycleConfig`
(die hier fehlt) → Regel 1 feuert nicht → Frischinstallation bindet nicht auf `photoperiodic_ornamental`.
Für die CAM-Kurztag-Arten (`Kalanchoe`) routet der Resolver stattdessen auf `cam_succulent_rest` (Regel 3, ein
**Nicht-Blankett**) → die v0027-Scope-Guard hängt sie nicht um → **residuale Seed↔Migration-Divergenz**.
**Remediation (Seed-Change):** je photoperiodischer Art einen `lifecycle_configs`-Block mit
`{cycle_type: perennial, photoperiod_type: short_day, critical_day_length_hours: 12}` in die `plant_info_*.yaml`
aufnehmen (aus dem Steckbrief materialisiert), damit der Resolver die Bindung **unabhängig** reproduziert. Danach
kann das Frozen-Dict in v0027 unverändert bleiben (Konvergenz). → **Folge-Issue FI-1**.

#### NCT-2 — Season→Wachstumsphasen-Kopplung erkennt die feingetypten Rest-Phasen nicht · **mittel**
`SeasonPhaseCoupler.enter_dormancy` (`season_phase_coupler.py:65`) sucht die Zielphase per **Literalnamen**
`find_phase_key_by_name(species_key, "dormancy")` und ignoriert die REQ-003 §D8 Rollen-Map. Die #616-Rest-Phasen
(`winter_rest`, `summer_rest`, `rest_phase`, `dry_storage`, `winter_hull_change`) sind zwar über
`phase_role_map.is_rest_phase` korrekt als `dormancy`-Rolle klassifiziert, werden vom Standort-Wintersignal aber
**nicht** angesteuert — eine `cam_succulent_rest`-Sukkulente wird nicht aktiv in ihre `winter_rest`-Ruhe getrieben.
Der Gegenweg `restart_cycle` funktioniert (über `cycle_restart_entry_order`, nicht Literalname). Die **Pflege**-Kopplung
(`DormancyCareActivator`) ist dagegen phasennamen-agnostisch und korrekt. Dokumentiert in REQ-047 §3.5.1 v1.5.
**Remediation (Resolver/Engine):** `enter_dormancy` gegen die Rollen-Map auflösen (erste gebundene Sequenz-Phase mit
`is_rest_phase == True`, Fallback Literal `dormancy`). → **Folge-Issue FI-2**.

#### NCT-3 — Steckbrief-`growth_habit` gröber als der Seed (BEHOBEN in diesem PR) · **mittel**
Die Steckbriefe der Farn-, Aufsitzer- und Geophyten-Kohorten führten `growth_habit: herb`, während der Seed
korrekt `fern`/`epiphyte`/`bulb_geophyte` trägt — die Steckbriefe (nominell Source of Truth) waren also **falscher**
als der Seed. Bei Regeneration des Seeds aus den Steckbriefen würde die resolver-kritische Präzision verloren gehen.
**Behoben:** 14 Steckbriefe auf den biologisch korrekten Wert korrigiert (Summary-Tabelle + eingebettete CSV):
4 Farne → `fern`, 4 Bromelien → `epiphyte`, 6 Geophyten → `bulb_geophyte`. **Restrisiko:** die Divergenz Steckbrief↔Seed
ist nicht durch einen Generator abgesichert (siehe UR-2).

#### NCT-4 — `growth_determinacy` im Frontend nicht erfasst/angezeigt · **niedrig**
Das Feld existiert in `_defs.schema.yaml`, `species.schema.yaml`, dem `LifecycleConfig`-Model, `species.yaml/overrides`
und (ab WS1) in REQ-001, ist aber **nirgends im Frontend** (`api/types.ts` kennt es nicht, keine Erfassung, keine
Anzeige). Damit ist die E4-Achse (indeterminate/gleichzeitige Phasen) master-data-seitig unpflegbar.
**Remediation (API+UI):** `growth_determinacy` in `SpeciesResponse`/`api/types.ts` und als Expert-Level-Select in
`LifecycleConfigSection` ergänzen. → gebündelt in **Folge-Issue FI-3**.

#### NCT-5 — `SpeciesCreateDialog`-`growth_habit`-Dropdown truncated (5/12) · **hoch**
`SpeciesCreateDialog.tsx:36` beschränkt `growth_habit` auf `['herb','shrub','tree','vine','groundcover']`. Die 2024
in REQ-001 v4.5 ergänzten Werte (`subshrub, grass, succulent, bulb_geophyte, fern, aquatic, epiphyte`) sind nicht
wählbar. Ein per-UI angelegter Farn/Geophyt/CAM-Sukkulent kann seinen korrekten Wuchstyp nicht bekommen → Resolver
mis-typt ihn auf `evergreen_foliage_perennial`/`indoor_default`. Direkter #610-Klassen-Defekt (Erfassungsfläche).
**Remediation (UI):** Dropdown auf die vollständige `GrowthHabit`-Enum (12 Werte) erweitern, i18n-Labels ergänzen.
→ **Folge-Issue FI-3**.

#### NCT-6 — `photosynthesis_type` (CAM) im Frontend nicht erfassbar · **mittel**
Die resolver-treibende CAM-Achse (`photosynthesis_type: cam` → `cam_succulent_rest`) ist im Backend voll vorhanden,
aber im Frontend weder erfassbar noch angezeigt. Ein neu angelegter Kaktus/Orchidee kann nicht als CAM markiert werden.
**Remediation (UI):** `photosynthesis_type`-Select (`c3`/`c4`/`cam`) in die Species-Overview-/Lifecycle-Maske.
→ **Folge-Issue FI-3**.

#### NCT-7 — `seed_adventskalender`-`optional_fields`-Whitelist verwirft Attribute · **mittel**
`seed_adventskalender.py:95` überträgt nur 27 gelistete Felder aus der YAML in `Species`. Jedes nicht gelistete
Attribut (`photosynthesis_type`, `growth_determinacy`, `light_compensation_point_*`, `salt_tolerance_*` u. a.) wird
stumm verworfen — der #453-Archetyp dieses Musters. Adventskalender-Arten können resolver-treibende Achsen strukturell
nicht tragen, selbst wenn die YAML sie enthielte.
**Remediation (Seed-Loader):** Whitelist durch eine Model-getriebene Feld-Übernahme ersetzen (alle bekannten
`Species`-Felder statt einer manuell gepflegten Liste), oder die resolver-treibenden Felder explizit ergänzen.
→ **Folge-Issue FI-4**.

#### NCT-8 — `growth_determinacy` in REQ-001 nicht geführt (BEHOBEN in diesem PR) · **niedrig**
Das Feld war in Schema/Model/Seed/REQ-003 präsent, fehlte aber in der REQ-001-Feldliste — ein Spec-Level-„not-carried-
through". **Behoben (WS1):** Feld + `GrowthDeterminacy`-Enum in REQ-001 v4.7 nachgezogen, plus die
„Lifecycle-Resolution-Pflichtfelder"-Klausel.

### 3.2 `unclear-requirement` (UR)

#### UR-1 — `Gardenia jasminoides`: `day_neutral` vs. `short_day` · **mittel**
Der Steckbrief führt `photoperiod_type: day_neutral`; Audit #586 §4 und das v0027-Frozen-Dict behandeln die Art als
`short_day` → `photoperiodic_ornamental`. Im Seed hat Gardenia **gar keinen** `photoperiod_type` (nur `growth_habit:
shrub`). Biologisch ist Gardenia jasminoides fakultativ kurztag-/temperatur-induziert — die Klassifikation ist echt
strittig. **Remediation (Spec-Entscheidung + Seed):** botanische Achse festlegen (Empfehlung: `short_day` mit
`critical_day_length_hours`), im Steckbrief **und** Seed konsistent setzen. Teil von **FI-1**.

#### UR-2 — Kein verbindlicher Steckbrief→Seed-Vertrag · **hoch**
CLAUDE.md deklariert den Steckbrief als „Source of Truth, Seed wird daraus generiert". Real existiert **kein Generator**;
Steckbrief und Seed-YAML werden unabhängig gepflegt und driften (NCT-1/NCT-3/UR-1 sind Symptome). Es ist unklar,
welche Ebene bei Konflikt gewinnt und wie Drift verhindert wird. **Remediation (Prozess/Tooling):** entweder einen
`seed-consistency`-Validator einführen, der die resolver-treibenden Achsen Steckbrief↔Seed abgleicht (CI-Gate), oder
den Steckbrief-Status als „Doku, nicht Quelle" klarstellen und den Seed als SSOT deklarieren. → **Folge-Issue FI-5**.

#### UR-3 — `indoor_default`-Grenze für genuin annuelle Indoor-Nutzpflanzen · **niedrig**
REQ-003 §D14 deklariert `indoor_default` als Last-Resort-Fallback (annuell/biennial/unbekannt). Für genuin annuelle
Indoor-Nutzpflanzen (Cannabis, Tomate, Basilikum) ist das die **korrekte** Bindung — aber die Spec grenzt „korrekter
Fallback" nicht scharf von „unaufgelöste Lücke" ab. Der Audit #586 §4 zählt 45 `default-fallback`-Arten, für die
`annual_harvest`/`annual_flower` sauberer wären. **Remediation (Spec):** in §D14 einen Sub-Fallback ergänzen
(`cycle_type=annual` → `annual_harvest`/`annual_flower` je `allows_harvest`), `indoor_default` nur für echt
unbestimmte Arten. Nicht-blockierend, Präzisierung. Teil von **FI-1** (optional).

---

## 4. Capture-UI-Prüfung (Resolver-Abhängigkeiten)

| Resolver-Eingabe (REQ-003 §D14) | In Erfassungsmaske? | Befund |
|---|---|---|
| `flowering_strategy` | ✓ `LifecycleConfigSection` (Expert) | ok |
| `cultivation_cycle_type` | ✓ `LifecycleConfigSection` (Intermediate) | ok |
| `photoperiod_type` | ✓ `LifecycleConfigSection` | ok (aber Seed-Lücke NCT-1) |
| `cycle_type` | ✓ `LifecycleConfigSection` | ok |
| `growth_habit` | ⚠ `SpeciesCreateDialog` (5/12 Werte) | **NCT-5** |
| `photosynthesis_type` | ✗ | **NCT-6** |
| `growth_determinacy` | ✗ | **NCT-4** |

**Fazit:** 4 von 7 Resolver-Eingaben sind sauber erfassbar; `growth_habit` truncated, `photosynthesis_type` und
`growth_determinacy` fehlen. Die Erfassungsfläche deckt die Resolver-Achsen also **nicht vollständig** ab — ein neu
angelegter Aufsitzer/CAM-Sukkulent/Geophyt kann nicht korrekt getypt werden.

---

## 5. Vorgeschlagene Folge-Issues

> Keine Issues erstellt — nur Vorschläge (englischer Titel + Scope), damit der Requester entscheidet.

- **FI-1 — `seed: carry photoperiod_type into the seed for the short-day ornamental cohort`**
  Scope: `lifecycle_configs`-Blöcke (`cycle_type: perennial`, `photoperiod_type: short_day`,
  `critical_day_length_hours: 12`) für die 11 photoperiodischen Zierpflanzen in `plant_info_*.yaml` materialisieren;
  Gardenia-Achse entscheiden (UR-1); Resolver-Regel-1-Konvergenz mit v0027 verifizieren (Unit-Test Fresh-Install ==
  Migration). Optional §D14-Annual-Sub-Fallback (UR-3). Behebt **NCT-1**, **UR-1**. Label: `backend`, `enhancement`.

- **FI-2 — `lifecycle: couple season winter signal to role-mapped rest phases`**
  Scope: `SeasonPhaseCoupler.enter_dormancy` über `phase_role_map.is_rest_phase`/`find_phase_key_by_role` auflösen
  statt Literal `dormancy`; Unit-Test mit einer `cam_succulent_rest`-Art. Behebt **NCT-2**. Label: `backend`.

- **FI-3 — `frontend: expose full growth-habit enum + photosynthesis_type + growth_determinacy in species capture`**
  Scope: `SpeciesCreateDialog`-`growth_habit`-Dropdown auf 12 Enum-Werte; `photosynthesis_type`- und
  `growth_determinacy`-Selects in `LifecycleConfigSection`/Overview; `api/types.ts` + i18n DE/EN. Behebt **NCT-4**,
  **NCT-5**, **NCT-6**. Label: `frontend`, `enhancement`.

- **FI-4 — `seed: replace adventskalender optional_fields whitelist with model-driven field carry`**
  Scope: die manuelle `optional_fields`-Liste in `seed_adventskalender.py` durch eine `Species`-Model-getriebene
  Übernahme ersetzen (oder resolver-treibende Felder ergänzen); Schema-Validierung. Behebt **NCT-7** (#453-Muster).
  Label: `backend`.

- **FI-5 — `tooling: enforce Steckbrief↔seed consistency for lifecycle-driving attributes`**
  Scope: CI-Validator, der `growth_habit`/`photoperiod_type`/`photosynthesis_type`/`flowering_strategy`/
  `growth_determinacy` zwischen `spec/knowledge/plants/*.md` und den Seed-YAMLs abgleicht und bei Drift bricht; oder
  Steckbrief-Status als „Doku" vs. Seed-SSOT dokumentieren. Behebt **UR-2** (Root Cause der ganzen Klasse).
  Label: `backend`, `spec`.

---

## 6. Bestätigungen (keine Findings)

- **3-Arten-Delta (210 Steckbriefe → 207 geseedet):** intendiert. Ursache sind `spp.`-Aggregate und Sorten-Steckbriefe,
  die auf **eine** geseedete Art abbilden (z. B. 5 Dahlien-Steckbriefe → 1 Seed-Art `Dahlia x cultorum`) sowie
  einzelne Steckbriefe ohne eigenen Seed-Eintrag — konsistent mit Audit #586 §2. Kein Datenverlust.
- **`indoor_default`-Blankett (Archetyp):** durch #616 behoben — der attributgetriebene Resolver (REQ-003 §D14) und
  die Migration v0027 ersetzen den Blankett-Link. **Als behoben markiert.** Restlücke ausschließlich NCT-1 (der Resolver
  kann eine Kohorte mangels Seed-Attribut noch nicht selbst reproduzieren).
- **CAM-/Farn-/Geophyten-Achsen:** `photosynthesis_type: cam` und `growth_habit: fern`/`bulb_geophyte`/`epiphyte` sind
  im Seed korrekt vorhanden (verifiziert) — für diese Kohorten reproduziert der Frischinstallations-Resolver die
  Bindung eigenständig; nur die photoperiodische Kohorte (NCT-1) hängt an der Migration.

---

## Quellen

- `spec/analysis/seed-phase-sequence-audit.md` (#586) — Vorgänger-Audit, `indoor_default`-Archetyp.
- `spec/req/REQ-003_Phasensteuerung.md` v2.17 §D14 (attributgetriebener Resolver), §D8 (Rollen-Map).
- `spec/req/REQ-001_Stammdatenverwaltung.md` v4.7 (Lifecycle-Resolution-Pflichtfelder, `growth_determinacy`).
- `spec/req/REQ-047_Saison-Ueberwinterungs-Automatik.md` v1.5 §3.5.1 (Rest-Phasen-Kopplung).
- Seed-Loader: `seed_data.py:link_indoor_species_to_phase_sequence`, `seed_plant_info.py:_build_lifecycle_configs`,
  `seed_adventskalender.py:95` (`optional_fields`).
- Resolver/Engine: `perennial_binding.py:resolve_phase_sequence_name`, `phase_role_map.py`,
  `season_phase_coupler.py`, Migration `versions/v0027_finetype_cam_monocarp_photoperiodic_sequences.py`.
- Frontend: `SpeciesCreateDialog.tsx`, `LifecycleConfigSection.tsx`, `api/types.ts`.
- Related: #610 (Fertilizer-Freitext statt Dropdowns), #453 (Adventskalender-Backfill/Whitelist-Drop), #565 (Epic).
</content>
</invoke>
