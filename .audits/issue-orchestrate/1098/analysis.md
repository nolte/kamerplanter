# #1098 — MCP-Substratschicht: Analyse

**Datum der Messung:** 2026-08-15
**Zustand des Codes:** `develop` @ `ea073a1f2`

## 0. Methode

Jede Behauptung des Issues wurde **gegen den Code gemessen**, nicht gelesen. Der
Grund steht im Sweep vom selben Tag: bei drei von vier untersuchten Issues war die
angegebene *Ursache* falsch, und der jeweils vorgeschlagene Fix hätte nichts
bewirkt (#1177, #1155, #1112). Für die zentrale Sicherheitsbehauptung dieses
Issues wurde ein ausführbarer Probelauf gegen die echte Route gebaut, statt sich
auf das Lesen der Handler zu verlassen.

Ergebnis vorweg: **Fünf von sieben Lücken bestätigt, eine korrigiert, und eine
blockierende Vorbedingung gefunden, die das Issue nicht kennt.**

---

## 1. Was bestätigt ist

| # | Behauptung | Status |
|---|---|---|
| 1 | Von 57 MCP-Werkzeugen ist `list_substrates` das **einzige** substratbezogene | **bestätigt** |
| 2 | `set_plant_location` existiert als Muster für `set_plant_substrate` | **bestätigt** (`plants.py:43`, `WriteToolBase`) |
| 3 | REST hat `POST /substrates/preview-mix` (nicht persistierend) und `POST /substrates/mix` | **bestätigt** |
| 4 | REST hat `GET /substrates/{key}`, MCP nicht | **bestätigt** |
| 5 | Die gesamte Batch-Schicht ist über MCP unerreichbar | **bestätigt** — REST hat `GET /{key}/batches`, `POST /batches`, `GET/PUT/DELETE /batches/{key}`, `POST /batches/{key}/check-reusability`, `POST /batches/{key}/prepare-reuse` |
| 6 | Es gibt **kein** `get_location`/`get_site`/`list_locations` als MCP-Werkzeug | **bestätigt** — nur `list_plants_at_location` |
| 7 | `calculate_mixing_protocol` nimmt `substrate_type: SubstrateType` (Enum), kein `substrate_key` | **bestätigt** (`nutrient_calc.py:100`) |

`PlantCreate` trägt tatsächlich 14 Felder, darunter `substrate_key` **und**
`substrate_batch_key` — das Datenmodell erwartet Batches also im Spiel, wie das
Issue sagt.

---

## 2. Was korrigiert werden muss

> **Die Kernbehauptung des Issues — „ein naiver `PUT` löscht die Phasen still" — trifft nicht zu.**

Das Issue schreibt:

> *Ein naiver `PUT {"substrate_key": "..."}` — der offensichtliche Aufruf — **löscht diese Phasen still**, dazu `location_key`, `planted_on`, `cultivation_cycle_type` und den Rest.*

Gemessen gegen `app/api/v1/plant_instances/tenant_router.py:124` mit einem
Probelauf über die echte Route:

```
A) der wörtlich naive Aufruf
   PUT {"substrate_key": "sub_new"}  ->  422
   fehlende Pflichtfelder: instance_id, species_key, planted_on

B) der plausible Aufruf: Pflichtfelder + das zu ändernde Feld
   PUT {"instance_id", "species_key", "planted_on", "substrate_key"}  ->  200
   ERHALTEN  current_phase_key:        'phase_vegetative' -> 'phase_vegetative'
   GELÖSCHT  location_key:             'loc_livingroom'   -> None
   GELÖSCHT  slot_key:                 'slot_3'           -> None
   GELÖSCHT  cultivar_key:             'cv_gardeners'     -> None
   GELÖSCHT  plant_name:               'Fensterbank-Tomate' -> None
   GELÖSCHT  container_volume_liters:  12.0               -> None
   GELÖSCHT  substrate_batch_key:      'batch_7'          -> None
```

Zwei Abweichungen, und beide ändern die Priorisierung:

1. **`current_phase_key` wird nicht gelöscht.** Der Handler weist 13 der 14
   Body-Felder auf die geladene Zeile zu und lässt `current_phase_key`
   ausdrücklich aus — sein eigener Kommentar sagt „keep server-managed fields
   from existing". Die drei im Issue namentlich genannten Pflanzen (`13949`,
   `18132826`, `18132838`) waren nie in Gefahr, ihre Phase zu verlieren.
2. **Der wörtlich naive Aufruf scheitert laut mit 422.** Er schreibt nichts.

**Die Gefahr ist trotzdem real — nur eine andere, und für dieses Issue eine
schlimmere.** Der *plausible* Aufruf löscht sechs Felder, darunter
`location_key` und — mit besonderer Ironie — **`substrate_batch_key`**: eine
Substratzuweisung über diesen Pfad zerstört die Rückverfolgbarkeit auf die
Charge, also genau das, was #1098 erreichbar machen will.

Der Mechanismus dahinter ist dokumentiert und gewollt:
`ArangoPlantInstanceRepository._update_is_full_replace = True`, damit ein `PUT`
ein nullbares Feld *leeren* kann. Das ist für ein Formular richtig und für einen
Agenten eine Falle.

**Konsequenz für die Umsetzung:** Das AK „entweder bekommt `PUT` ein
`PATCH`-Geschwister, oder die Full-Replace-Semantik wird am Endpunkt
dokumentiert" bleibt gültig, aber die Begründung im Issue muss beim Umsetzen
korrigiert werden — sonst schreibt jemand einen Test, der die Phasen-Erhaltung
als *Fix* feiert, obwohl sie nie kaputt war. Das ist die Vakuum-Falle in ihrer
teuersten Form: ein grüner Test über einer Eigenschaft, die schon galt.

---

## 3. Die blockierende Vorbedingung, die das Issue nicht kennt

> **Die gesamte Substratschicht hat keine Mandantentrennung — weder Katalog noch Chargen.**

Gemessen:

```
Substrate            → kein tenant_key   (app/domain/models/substrate.py:17)
SubstrateBatch       → kein tenant_key   (app/domain/models/substrate.py:68)
ArangoSubstrateRepository → kein is_tenant_scoped  (Default: False)
get_batches_by_substrate  → find_by_field("substrate_key", …), kein Mandantenfilter
Router /api/v1/substrates → global gemountet, dependencies=[Depends(get_current_user)]
Gate-Zählung über alle 15 Routen: get_current_user 1×, sonst nur Service/Pagination
```

Daraus folgt heute, über REST:

- `GET /substrates/{key}/batches` liefert **die Chargen jedes Mandanten**.
- `PUT` / `DELETE /substrates/batches/{key}` verändert und löscht **fremde**
  Chargen.
- `POST` / `PUT` / `DELETE /substrates` und `/{key}` erlauben **jedem
  authentifizierten Nutzer**, den geteilten Katalog zu ändern und zu löschen —
  ohne Plattform-Admin-Gate.

Eine Charge ist eine *physische Sache, die ein Mandant angemischt hat*. Dass sie
keinen Eigentümer trägt, ist dieselbe Fehlerklasse, die dieser Sweep für Sorten
(#1090), für Referenzen (#1112) und für den botanischen Familienkatalog (#1120)
geschlossen hat. Substrate wurden dabei übersehen.

**Warum das #1098 blockiert und nicht nur begleitet:**

1. Das Issue verlangt, die Batch-Schicht über MCP erreichbar zu machen. Auf einem
   Modell ohne `tenant_key` heißt das, ein bestehendes REST-Loch auf die
   Agentenoberfläche zu heben — mit einem LLM als Aufrufer, das Schlüssel
   systematisch durchprobieren kann.
2. Das Muster, dem `set_plant_substrate` folgen soll, **stützt sich genau auf die
   fehlende Eigenschaft**: `set_plant_location._verify_targets` ruft
   `ctx.site_service.get_site(key, tenant_key=ctx.tenant_key)`, damit eine
   Pflanze nie auf einen fremden Standort gesetzt wird. Für Substrate und Chargen
   gibt es diesen Aufruf nicht — es gibt nichts, wogegen man prüfen könnte. Ein
   `set_plant_substrate` nach Vorlage wäre also die Vorlage **ohne ihren Wächter**.
3. `PlantCreate.substrate_batch_key` ist eine Referenz von einer mandanten-
   gebundenen Zeile auf eine mandantenlose — dieselbe Konstellation, die #1112
   für `cultivar_key` gerade behandelt hat.

---

## 4. Vorgeschlagene Zerlegung

Reihenfolge ist bindend: **P1 vor allem anderen.**

### P1 — Mandantentrennung der Substratschicht *(Vorbedingung, eigener PR)*

- `SubstrateBatch.tenant_key`, gestempelt beim Anlegen, Backfill per Migration.
  Offene Frage an den Betreiber: **wohin mit bestehenden Chargen?** (Abschnitt 5)
- `Substrate` bleibt **global** wie der Artenkatalog — aber die Schreibrouten
  bekommen das Plattform-Admin-Gate, das der botanische Familienkatalog in #1120
  bekommen hat.
- Batch-Lesepfade filtern auf den Mandanten; Batch-Schreibpfade gehen durch
  `require_permission`.
- `plant_instance.substrate_batch_key` wird zur *owned reference*
  (`_owned_reference_fields`), analog zu #1112 — mit derselben Inertheitsprüfung.

Ohne P1 hat kein Werkzeug aus P3 etwas, wogegen es prüfen könnte.

### P2 — Full-Replace-Semantik am Plant-Endpunkt entschärfen

- Entweder ein `PATCH`-Geschwister, oder die Semantik am Endpunkt dokumentieren.
- **Korrigierte Begründung** (siehe §2): nicht „Phasen gehen verloren", sondern
  „sechs optionale Felder werden geleert, darunter `substrate_batch_key`".
- Ein Test, der die *tatsächliche* Löschmenge festnagelt — nicht die behauptete.

### P3 — Die Werkzeuge, in der Kostenreihenfolge des Issues

| Werkzeug | Klasse | Anmerkung |
|---|---|---|
| `set_plant_substrate` | WRITE | Kopie von `set_plant_location`, inkl. `_verify_targets` gegen P1 |
| `preview_substrate_mix` | READ | reine Rechnung, Präzedenzfall `calculate_mixing_protocol` |
| `get_substrate` | READ | trivial |
| `create_substrate_mix` | WRITE | schreibt in den **globalen** Katalog → Plattform-Admin oder eigene Regel (Abschnitt 5) |
| `list_substrate_batches`, `get_substrate_batch`, `check_batch_reusability` | READ | mandantengefiltert nach P1 |
| `get_location` | READ | auch von #949 gefordert; klein, hoher Hebel |

### P4 — `calculate_mixing_protocol` nimmt optional `substrate_key`

Fallback auf `substrate_type`, damit bestehende Aufrufe unverändert gültig
bleiben — dieselbe Rückwärtskompatibilitätsregel wie bei `CatalogueToolInput`
in #1121.

---

## 5. Was vor der Umsetzung entschieden werden muss

1. **Bestehende Chargen beim Backfill.** Sie tragen heute keinen Eigentümer. Drei
   Möglichkeiten, und keine ist offensichtlich: (a) über die Pflanzen zuordnen,
   die auf sie zeigen — mehrdeutig, wenn Pflanzen mehrerer Mandanten auf dieselbe
   Charge zeigen; (b) alle global lassen und nur neue stempeln — der Guard bliebe
   für Altbestand inert, genau die Falle aus #1112; (c) alle einem
   Plattform-Mandanten zuschlagen und sichtbar machen, dass sie zugeordnet werden
   müssen.
2. **Wer darf einen Mix anlegen?** `create_substrate_mix` schreibt in den
   *globalen* Katalog. Entweder Plattform-Admin (konsistent zu #1120), oder Mixe
   werden mandantengebunden — was `Substrate` teilweise mandantenfähig machen
   würde und damit zur Hybrid-Katalog-Frage aus #1090 führt.
3. **Ist P1 Teil von #1098 oder ein eigenes Issue?** Es ist ein
   Sicherheitsdefekt, der unabhängig von MCP besteht und über REST heute
   ausnutzbar ist. Argument für ein eigenes Issue: es sollte nicht auf ein
   Feature warten. Argument dagegen: #1098 kann ohne es nicht korrekt gebaut
   werden.

---

## 6. Aufwandsschätzung

| Paket | Umfang |
|---|---|
| P1 | Modellfeld + Migration + 4 Repository-/Service-Pfade + Router-Gates + Tests mit Rot-zuerst — vergleichbar mit #1090, dem größten Einzelpaket dieses Sweeps |
| P2 | klein, aber mit einer Entscheidung (PATCH vs. Doku) |
| P3 | 8 Werkzeuge, davon 2 schreibend mit Dry-Run/Idempotenz |
| P4 | klein |

**Gesamt: deutlich größer als jedes Einzelpaket dieses Sweeps.** Die Empfehlung
ist, P1 sofort als Sicherheitsissue zu ziehen und #1098 danach in einem eigenen
Lauf zu planen.
