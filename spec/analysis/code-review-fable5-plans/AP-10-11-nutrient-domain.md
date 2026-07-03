# AP-10 / AP-11 (P1): Nährstoff-Domäne — EC-Pipeline-Konsolidierung & flächenbasierte Dosierung

> Arbeitspakete aus dem Kamerplanter-Code-Review (Fable 5). Priorität **P1**.
> Befund-IDs: **DOM-5** (falsche EC-Formel am Live-Endpoint), **DOM-6** (namensbasierte
> CalMag-Erkennung), **DUP-B7** (EC-net doppelt & divergierend), **DUP-B8**
> (`mixing_priority`-Fallback dreifach), **DOM-4** (flächenbasierte Dosierung nirgends berechnet).
> Betroffene Domäne: Bewässerung & Düngung (REQ-004, REQ-004-A).

---

## 1. Ziel & betroffene Anforderungen

### Ziel

Im Backend existieren **zwei parallele EC-Dosier-Pipelines**, von denen nur eine den
REQ-004-A-Vertrag erfüllt. Die veraltete Pipeline (`NutrientSolutionCalculator`) ist über
den öffentlichen Endpoint `POST /api/v1/nutrient-calculations/mixing-protocol` live und
wird vom Frontend (`NutrientCalculationsPage`) benutzt. Sie ignoriert pH-Reserve,
CalMag-/Silikat-Vorabzug, Unsicherheits-Reserve und EC_max-Validierung — die berechneten
Dosierungen sind systematisch **zu hoch** (der Nutzer landet über dem Ziel-EC, sobald er
pH korrigiert).

Nach diesem Arbeitspaket gilt:

- Der Endpoint `/nutrient-calculations/mixing-protocol` rechnet über die **kanonische
  Pipeline** (`EcBudgetCalculator`); `NutrientSolutionCalculator` ist gelöscht.
- Die EC-net-Formel (`EC_net = EC_target − EC_mix`) und die pH-Reserve-Staffel existieren
  genau **einmal** im Code und werden von beiden verbleibenden Engines benutzt.
- Der `mixing_priority`-Fallback `50` ist eine benannte Konstante an **einer** Stelle.
- CalMag-Erkennung ist **strukturbasiert** (`FertilizerType.CALMAG`) mit normalisiertem
  Namens-Fallback — „Cal-Mag" und „CaliMagic" werden erkannt.
- Flächenbasierte Dosierung (g/m², L/m² — REQ-004 W-013) wird von einer neuen Engine
  tatsächlich **berechnet**; die bislang toten Felder `TopDressParams.grams_per_m2` /
  `grams_per_plant` werden in der Dosier-Pipeline ausgewertet.

### Betroffene Anforderungen

- **REQ-004 (Dünge-Logik)** — `spec/req/REQ-004_Duenge-Logik.md`
  - Z. 67 ff. (W-013, Quelle Outdoor-Garden-Planner Review G-007): „Im Gegensatz zur
    Hydroponik-Kalkulation (EC-Budget, ml/L) wird im Freiland nach **Ausbringungsmenge
    pro Flächeneinheit** (g/m² oder L/m²) dosiert."
  - Z. 79 ff.: Ausbringungs-Modell — `application_rate_g_per_m2`,
    `application_rate_l_per_m2`, `dilution_ratio`, `application_season`,
    `nutrient_release_speed`.
  - Z. 88 ff.: Empfehlungstabelle nach `nutrient_demand_level`
    (heavy/medium/light_feeder, nitrogen_fixer).
  - Z. 110 ff.: Abgrenzung Hydro/Freiland — EC-Budget für `hydro/coco/...`,
    flächenbasierte organische Düngung für `soil/living_soil/raised_bed_mix`.
- **REQ-004-A (EC-Budget-Kalkulation)** — `spec/req/REQ-004-A_EC-Budget-Kalkulation.md`
  - Z. 43 / 240: `EC_net = EC_target − EC_mix`.
  - Z. 245: EC_net muss Platz für **alle** geplanten Dünger **plus geschätzten
    pH-Korrektur-EC** lassen.
  - Z. 279–291: `EC_net_effective = EC_net − EC_ph_reserve`, Staffel
    weich < 50 ppm → 0.02 mS, mittel 50–150 ppm → 0.03 mS, hart > 150 ppm → 0.05 mS.
  - Z. 441–465: Abzugsreihenfolge Silikat → CalMag → Rezept-Skalierung → pH-Reserve.
  - Z. 457: Silikat-Warnung explizit strukturbasiert: „`type = 'silicate'` oder
    `mixing_priority > mixing_priority_calmag`" — d. h. die Spec verlangt bereits
    **Typ-basierte**, nicht namensbasierte Erkennung.
  - Z. 385 / 408: Rezept-Skalierung `k = EC_net / EC_rezept` bzw. Gleichverteilung.

---

## 2. Ist-Analyse: die zwei EC-Pfade

### 2.1 Aufruf-Topologie

| Pipeline | Engine-Datei | Live über | Konsument |
|---|---|---|---|
| **A (veraltet)** `NutrientSolutionCalculator` | `src/backend/app/domain/engines/nutrient_engine.py:6–127` | `POST /nutrient-calculations/mixing-protocol` — `src/backend/app/api/v1/nutrient_calculations/router.py:39–59` | Frontend `src/frontend/src/pages/duengung/NutrientCalculationsPage.tsx` via `src/frontend/src/api/endpoints/nutrient-calculations.ts` |
| **B (korrekt, REQ-004-A)** `EcBudgetCalculator` | `src/backend/app/domain/engines/ec_budget_engine.py:132–456` | `POST /nutrient-calculations/ec-budget` — `router.py:168–248` | Frontend EC-Budget-Ansicht |
| **C (korrekt, REQ-004 §4b, planbasiert)** `DosageCalculationEngine` | `src/backend/app/domain/engines/dosage_calculation_engine.py:104–611` | `POST /t/{slug}/nutrient-plans/{key}/calculate-dosages` — `src/backend/app/api/v1/nutrient_plans/tenant_router.py:208–217` via `NutrientPlanService.calculate_dosages` (`src/backend/app/domain/services/nutrient_plan_service.py:33, 327 ff.`) | Frontend Nährstoffplan-Detail |

Weitere Klassen in `nutrient_engine.py` (`FlushingProtocol`, `RunoffAnalyzer`,
`MixingSafetyValidator`) sind fachlich eigenständig und **bleiben erhalten** — nur
`NutrientSolutionCalculator` ist redundant.

### 2.2 Feature-Vergleich der drei Rechner

| REQ-004-A-Vertragspunkt | A `NutrientSolutionCalculator` | B `EcBudgetCalculator` | C `DosageCalculationEngine` |
|---|---|---|---|
| EC_net = target − base | ✅ (`nutrient_engine.py:35`) | ✅ (`ec_budget_engine.py:193`) | ✅ implizit (`dosage_calculation_engine.py:248`) |
| pH-Reserve-Abzug (Alkalinität) | ❌ **fehlt** | ✅ (`:204–209, :298`) | ✅ (`:246, :560–567`) |
| CalMag-Vorabzug | ❌ **fehlt** | ✅ (`:254–295`) | ✅ (Stage 2, `:212–242`) |
| Silikat-Vorabzug | ❌ **fehlt** | ✅ (`:211–252`) | ❌ (nicht modelliert; Silikat läuft als normale Rezept-Position mit) |
| Unsicherheits-Reserve (0.15 mS) | ❌ **fehlt** | ✅ (`:304–314`) | ❌ **fehlt** |
| EC_max-Validierung (Substrat×Phase) | ❌ **fehlt** | ✅ (`:176–179, :424–429`) | ❌ **fehlt** |
| Max-Dose-Cap | ✅ (`:93–99`) | ✅ (`:330–335`, Fallback `SYSTEM_MAX_ML_PER_LITER=20`) | ❌ **fehlt** in `_build_scaled_dosages` (`:453–493`) |
| Rezept-Skalierung k = EC_net/EC_rezept | ✅ (`:55–67`) | ✅ (`:316–324`) | ✅ (scaling_factor, `:251–256`) |
| Living-Soil-Bypass | ❌ | ✅ (`:154–169`) | ❌ (nur Legacy-/Referenz-Fallbacks) |
| Substrat-EC-Konvertierung | ❌ | ❌ | ✅ (`SubstrateEcAdapter`, `:124–129`) |

**Referenz ist eindeutig `EcBudgetCalculator` (B):** einzige Engine, die alle
Budget-Vertragspunkte aus REQ-004-A §4/§5 abdeckt. `DosageCalculationEngine` (C) ist der
planbasierte Orchestrator (Wasser-Mix → CalMag → Skalierung) und bleibt bestehen, soll
aber die Budget-Grundbausteine aus B **importieren statt duplizieren**.

### 2.3 Die EC-net-/Reserve-Duplikate im Detail (DUP-B7)

Drei Implementierungen, zwei Semantiken:

1. `nutrient_engine.py:35` — `available_ec = max(0, target_ec_ms - base_water_ec)`
   (keine Abzüge danach → **falsch**).
2. `ec_budget_engine.py:193` — `ec_net = max(0, inp.target_ec - ec_mix)`, danach
   **schrittweise** `remaining -= ec_silicate/ec_calmag/ph_reserve/uncertain` mit Guard
   `if remaining > 0` (`:316`). `remaining` kann still negativ werden → Dosierung wird
   übersprungen, aber es fehlt eine explizite Warnung „Vorabzüge übersteigen Budget".
3. `dosage_calculation_engine.py:248` —
   `ec_available_for_ferts = max(0.0, target_ec - base_water_ec - ec_calmag - ph_reserve)`
   — **einschrittig** geklemmt: klemmt *nach* allen Abzügen auf 0, während B *vor* den
   Abzügen klemmt. Bei `base_water_ec > target_ec` liefert B eine Warnung (`:195–198`),
   C schweigt und skaliert still auf 0. Zusätzlich dupliziert
   `DosageCalculationEngine._get_ph_reserve` (`:560–567`) die Alkalinitäts-Staffel aus
   `ec_budget_engine.py:204–209` (beide auf Basis des importierten `PH_RESERVE`-Dicts,
   aber mit je eigener Schwellwert-Logik).

### 2.4 `mixing_priority`-Fallback `50` (DUP-B8)

Der Default steckt bereits im Modell (`src/backend/app/domain/models/fertilizer.py:27`,
`Field(default=50)`), wird aber als magisches Literal dreifach wiederholt, jeweils für
den Fall „fertilizer_key nicht auflösbar":

- `src/backend/app/domain/services/nutrient_plan_service.py:301`
  (`priority = fert.mixing_priority if fert else 50`)
- `src/backend/app/domain/engines/dosage_calculation_engine.py:468`
  (`_build_scaled_dosages`)
- `src/backend/app/domain/engines/dosage_calculation_engine.py:513`
  (`_build_reference_result`)

### 2.5 Namensbasierte CalMag-Erkennung (DOM-6)

`MixingSafetyValidator.validate_combination` (`nutrient_engine.py:294, 305, 325`) erkennt
CalMag ausschließlich per Substring `"calcium" in name or "calmag" in name`:

- **„Cal-Mag"** (Botanicare Cal-Mag Plus, sehr verbreitet) → `"cal-mag"` enthält weder
  `calmag` noch `calcium` → **nicht erkannt**, die CalMag-vor-Sulfat-Regel
  (Gips-Ausfällung, CLAUDE.md Architekturentscheidung 5) greift nicht.
- **„CaliMagic"** (General Hydroponics) → **nicht erkannt**.
- Sulfat-Erkennung analog fragil (`"sulfat"/"sulfate"/"epsom"`, `:296–299`); „Bittersalz"
  (deutscher Handelsname für Epsom) → **nicht erkannt**.

Das `FertilizerType`-Enum (`src/backend/app/common/enums.py:436–443`) kennt
`SILICATE`, aber **kein `CALMAG`** — die Spec (REQ-004-A Z. 457) setzt für Silikat
bereits Typ-basierte Erkennung voraus; CalMag braucht dasselbe strukturelle Fundament.
Die Silikat-Prüfung im selben Validator (`:324`) nutzt korrekt
`f.fertilizer_type == FertilizerType.SILICATE` — das Muster existiert also schon.

### 2.6 Flächenbasierte Dosierung fehlt komplett (DOM-4, AP-11)

- `TopDressParams.grams_per_plant` / `grams_per_m2`
  (`src/backend/app/domain/models/nutrient_plan.py:38–39`) werden von **keiner** Engine
  gelesen (Grep über `src/backend/app` liefert außer Modell + API-Schema-Spiegel
  `api/v1/nutrient_plans/schemas.py:44` keine Nutzung).
- Die von W-013 geforderten Fertilizer-Felder (`application_rate_g_per_m2`,
  `application_rate_l_per_m2`, `dilution_ratio`, `nutrient_release_speed`) existieren im
  `Fertilizer`-Modell **nicht**.
- Die Standortfläche ist vorhanden: `Location.area_m2`
  (`src/backend/app/domain/models/site.py:66`, Pflichtfeld `ge=0`) und
  `Site.total_area_m2` (`site.py:99`); Zugriff über
  `SiteService.get_location` (`src/backend/app/domain/services/site_service.py:56`) →
  `SiteRepository.get_location_by_key`
  (`src/backend/app/data_access/arango/site_repository.py:50`).
- `EcBudgetCalculator` verweist im Living-Soil-Bypass (`ec_budget_engine.py:154–159`)
  textlich auf „g/m²" — der referenzierte Rechenpfad existiert nicht. Das ist die Lücke,
  die AP-11 schließt.

---

## 3. Entscheidung

### 3.1 `/mixing-protocol` auf `EcBudgetCalculator` umstellen — nicht patchen

**Entscheidung: Option „Umstellen".** `NutrientSolutionCalculator` wird gelöscht; der
Endpoint `/mixing-protocol` wird zu einem dünnen Adapter über `EcBudgetCalculator`.

Begründung:

- Patchen von A hieße, pH-Reserve, Vorabzüge, Unsicherheits-Reserve und EC_max-Prüfung
  ein zweites Mal zu implementieren — exakt die Duplikation, die DUP-B7 beanstandet.
- B ist getestet (`tests/unit/domain/engines/test_ec_budget_engine.py`, 21 Tests) und
  spec-verankert (REQ-004-A §4/§5).
- Der API-Vertrag von `/mixing-protocol` bleibt **abwärtskompatibel erhalten** (Response-
  Felder `dosages[]`, `calculated_ec`, `ph_adjustment`, `warnings`, `instructions`),
  damit `NutrientCalculationsPage.tsx` ohne Zwang weiterläuft. Neue Request-Felder sind
  **additiv-optional** (`alkalinity_ppm`, `phase`, `recipe_ml_per_liter`) mit Defaults,
  die dem bisherigen Verhalten am nächsten kommen (`alkalinity_ppm=0` → weiche
  pH-Reserve 0.02 mS, `phase="vegetative"`).
- Die **gewollte Verhaltensänderung** (Dosen sinken um pH-Reserve + ggf. Caps/EC_max-
  Warnungen kommen hinzu) ist der eigentliche Bugfix von DOM-5 — siehe Risiko §8.

### 3.2 Kanonischer Ort für EC-Mathematik

`ec_budget_engine.py` wird der kanonische Ort für die Budget-Grundbausteine. Zwei pure
Modul-Funktionen werden dort extrahiert und überall importiert:

```python
# src/backend/app/domain/engines/ec_budget_engine.py

def compute_ec_net(target_ec: float, base_water_ec: float) -> float:
    """EC_net = EC_target − EC_mix, geklemmt auf ≥ 0 (REQ-004-A §4.1)."""
    return max(0.0, target_ec - base_water_ec)

def ph_reserve_for_alkalinity(alkalinity_ppm: float) -> float:
    """pH-Reserve-Staffel nach Alkalinität (REQ-004-A §4.4)."""
    if alkalinity_ppm < 50:
        return PH_RESERVE["soft"]
    if alkalinity_ppm <= 150:
        return PH_RESERVE["medium"]
    return PH_RESERVE["hard"]
```

- `EcBudgetCalculator.calculate` nutzt beide (ersetzt `:193` und `:204–209`).
- `DosageCalculationEngine` löscht `_get_ph_reserve` (`:560–567`) und ersetzt `:248`
  durch `compute_ec_net(target_ec, base_water_ec) - ec_calmag - ph_reserve` mit
  anschließendem explizitem Negativ-Check + Warnung (angleichen an B-Semantik:
  Warnung, wenn Vorabzüge das Budget übersteigen — behebt die stille Divergenz aus §2.3).
- Ebenfalls angleichen: `_build_scaled_dosages` erhält den **Max-Dose-Cap**
  (`f.max_dose_ml_per_liter or SYSTEM_MAX_ML_PER_LITER`, Import aus
  `ec_budget_engine`) — heute kann der Skalierungsfaktor unbegrenzt hochskalieren.

### 3.3 `mixing_priority`-Fallback als Konstante

```python
# src/backend/app/domain/models/fertilizer.py
DEFAULT_MIXING_PRIORITY: Final[int] = 50

class Fertilizer(BaseModel):
    ...
    mixing_priority: int = Field(default=DEFAULT_MIXING_PRIORITY, ge=1, le=100)
```

Die drei Fallback-Stellen (§2.4) importieren `DEFAULT_MIXING_PRIORITY`.

### 3.4 Strukturbasierte CalMag-Erkennung

1. **Enum erweitern** — `src/backend/app/common/enums.py:436 ff.`:
   `FertilizerType.CALMAG = "calmag"`.
2. **Klassifikations-Helfer** — neues Modul
   `src/backend/app/domain/engines/fertilizer_classification.py`:

   ```python
   _CALMAG_NAME_PATTERNS = ("calmag", "calimagic", "calcium", "camg")
   _SULFATE_NAME_PATTERNS = ("sulfat", "sulfate", "epsom", "bittersalz")

   def _normalized(name: str) -> str:
       """lowercase + alle Nicht-Alphanumerik entfernen: 'Cal-Mag' → 'calmag'."""

   def is_calmag(fert: Fertilizer) -> bool:
       """Primär: fertilizer_type == CALMAG. Fallback: normalisierter Produktname."""

   def is_sulfate_bearing(fert: Fertilizer) -> bool: ...
   def is_silicate(fert: Fertilizer) -> bool:
       """fertilizer_type == SILICATE (bestehendes Muster, zentralisiert)."""
   ```

   Der Namens-Fallback bleibt bewusst erhalten (Bestandsdaten von Tenants sind nicht
   reklassifiziert), aber **normalisiert** — „Cal-Mag" → `calmag` ✅,
   „CaliMagic" → `calimagic` ✅.
3. **`MixingSafetyValidator`** (`nutrient_engine.py:289–336`) ersetzt alle vier
   Inline-Substring-Blöcke (`:294–299, :304–313, :325–327`) durch die Helfer.
4. **Seed-/Bestandsdaten:** Migration `migrate_fertilizer_calmag_type` (Muster wie
   bestehende Migrationen unter `src/backend/app/migrations/`): setzt
   `fertilizer_type = "calmag"` für Dokumente, deren normalisierter Name einem
   CalMag-Pattern entspricht. Seed-YAML der Produktdaten
   (`spec/knowledge/products/`, sofern EC-Produkte enthalten) mitziehen.
5. **Frontend:** `FertilizerType`-Union/Enum + i18n `enums.fertilizerType.calmag`
   (DE: „CalMag", EN: „CalMag") ergänzen; Formular-Dropdown erhält den neuen Wert.
6. `DosageCalculationEngine._calculate_calmag_dosage` kann `calmag_product` künftig via
   `is_calmag` plausibilisieren (Warnung, wenn ein Nicht-CalMag-Produkt übergeben wird)
   — optional, kein Blocker.

### 3.5 Neuer flächenbasierter Dosier-Service (AP-11)

**Modell-Erweiterung `Fertilizer`** (W-013-Kernfelder, additiv-optional):

```python
# src/backend/app/domain/models/fertilizer.py
application_rate_g_per_m2: float | None = Field(default=None, gt=0)
application_rate_l_per_m2: float | None = Field(default=None, gt=0)
dilution_ratio: str | None = Field(default=None, pattern=r"^\d+:\d+$")  # z. B. "1:10"
nutrient_release_speed: NutrientReleaseSpeed | None = None  # neues StrEnum:
# IMMEDIATE / WEEKS / MONTHS / SEASON_LONG (enums.py)
```

(`application_season` aus W-013 wird bewusst zurückgestellt — Saisonlogik gehört zu
REQ-006/REQ-022-Erinnerungen, nicht in den Dosier-Rechner.)

**Neue Engine** `src/backend/app/domain/engines/area_dosing_engine.py`:

```python
class AreaDosingItem(BaseModel):
    fertilizer_key: str | None
    product_name: str
    rate_g_per_m2: float | None
    rate_l_per_m2: float | None
    total_grams: float | None      # rate_g_per_m2 × area_m2
    total_liters: float | None     # rate_l_per_m2 × area_m2
    dilution_ratio: str | None
    nutrient_release_speed: str | None
    note: str | None               # z. B. "1:10 verdünnt ausbringen"

class AreaDosingResult(BaseModel):
    area_m2: float
    items: list[AreaDosingItem]
    warnings: list[str]            # z. B. "X hat keine Flächen-Ausbringungsrate"
    instructions: list[str]        # Schritt-für-Schritt wie bei den EC-Rechnern

class AreaDosingCalculator:
    def calculate(
        self,
        fertilizers: list[Fertilizer],
        area_m2: float,                      # > 0, sonst ValueError → 422
        demand_level: str | None = None,     # optional: heavy/medium/light_feeder,
    ) -> AreaDosingResult: ...               # nitrogen_fixer → Empfehlungs-Hinweise
```

Rechenkern pro Dünger: `total_grams = rate_g_per_m2 × area_m2` (Rundung 1 g),
`total_liters = rate_l_per_m2 × area_m2` (Rundung 0.1 L). `nitrogen_fixer` +
N-haltiger Dünger (npk_ratio[0] > 0) → Warnung „Kein N-Dünger für N-Fixierer!"
(W-013-Tabelle Z. 94).

**Woher kommt die Fläche?** Zwei Wege, ein Rechenkern:

1. **Stateless** (Stil der bestehenden `nutrient_calculations`-Rechner):
   `POST /api/v1/nutrient-calculations/area-dosing` mit explizitem `area_m2` im Body —
   Frontend hat `Location.area_m2` ohnehin geladen.
2. **Tenant-scoped mit Standort-Auflösung:** optionales Request-Feld `location_key`;
   `FertilizerService` (bzw. neuer schlanker Service-Wrapper) löst über
   `SiteService.get_location(location_key).area_m2`
   (`site_service.py:56` → `site_repository.py:50`) auf. Wenn beides gesetzt ist,
   gewinnt `area_m2` (Override); Location mit `area_m2 == 0` → 422 mit klarer Meldung
   „Standort hat keine Fläche hinterlegt".

**TopDress-Wiring in Pipeline C** (macht `nutrient_plan.py:38–39` lebendig):

- `DosageCalculationInput` erhält `area_m2: float | None = None` und
  `plant_count: int | None = None`.
- `NutrientPlanService.calculate_dosages` (`nutrient_plan_service.py:327 ff.`) bekommt
  einen optionalen Parameter `location_key: str | None`; der Tenant-Router
  (`nutrient_plans/tenant_router.py:208–217`) reicht ihn als Query-Parameter durch.
  Auflösung der Fläche im Service (nicht in der Engine — 5-Layer, NFR-001).
- In `DosageCalculationEngine.calculate`: wenn der aufgelöste Channel
  `application_method == top_dress` und `method_params.grams_per_m2` gesetzt ist →
  `DosageEntry` mit `total_grams = grams_per_m2 × area_m2` (neues optionales Feld
  `total_grams` auf `DosageEntry`; `ml_per_liter/total_ml = 0`, `ec_contribution = 0`,
  `source = "reference"`). Analog `grams_per_plant × plant_count`. Fehlt die Fläche →
  Warnung statt stiller 0.

---

## 4. Konkrete Änderungen pro Datei

### Backend — Domäne

| Datei | Änderung |
|---|---|
| `src/backend/app/domain/engines/ec_budget_engine.py` | Modul-Funktionen `compute_ec_net`, `ph_reserve_for_alkalinity` extrahieren; `EcBudgetCalculator.calculate` nutzt sie (`:193`, `:204–209`); explizite Warnung, wenn Vorabzüge (Silikat/CalMag/Reserven) `remaining` unter 0 drücken |
| `src/backend/app/domain/engines/dosage_calculation_engine.py` | `_get_ph_reserve` löschen → Import `ph_reserve_for_alkalinity`; `:248` auf `compute_ec_net(...) − ec_calmag − ph_reserve` + Negativ-Warnung umbauen; Max-Dose-Cap in `_build_scaled_dosages`; Fallback-Literale `:468`, `:513` → `DEFAULT_MIXING_PRIORITY`; `DosageCalculationInput` + `DosageEntry` um `area_m2`/`plant_count`/`total_grams` erweitern; TopDress-Zweig |
| `src/backend/app/domain/engines/nutrient_engine.py` | `NutrientSolutionCalculator` (Z. 6–127) und `_build_instructions` (Z. 405–423) **löschen**; `MixingSafetyValidator` auf `fertilizer_classification`-Helfer umstellen (Z. 294–336); `_ph_adjustment` bleibt (vom Adapter weiterverwendet) |
| `src/backend/app/domain/engines/fertilizer_classification.py` | **neu** — `is_calmag`, `is_sulfate_bearing`, `is_silicate`, `_normalized` |
| `src/backend/app/domain/engines/area_dosing_engine.py` | **neu** — `AreaDosingCalculator` + Modelle (§3.5) |
| `src/backend/app/domain/models/fertilizer.py` | `DEFAULT_MIXING_PRIORITY`; W-013-Felder `application_rate_g_per_m2`, `application_rate_l_per_m2`, `dilution_ratio`, `nutrient_release_speed` |
| `src/backend/app/domain/models/nutrient_plan.py` | unverändert (Felder existieren; werden jetzt genutzt) |
| `src/backend/app/domain/services/nutrient_plan_service.py` | `:301` → `DEFAULT_MIXING_PRIORITY`; `calculate_dosages` um `location_key`-Auflösung (Fläche via `SiteService`/`SiteRepository`) erweitern |
| `src/backend/app/domain/services/fertilizer_service.py` | Methode `calculate_area_dosage(fertilizer_keys, area_m2 \| location_key)` (dünner Orchestrator über `AreaDosingCalculator`) |
| `src/backend/app/common/enums.py` | `FertilizerType.CALMAG`; neues `NutrientReleaseSpeed`-StrEnum |

### Backend — API

| Datei | Änderung |
|---|---|
| `src/backend/app/api/v1/nutrient_calculations/router.py` | `mixing_protocol` (Z. 39–59) baut `EcBudgetInput` und mappt `EcBudgetResult` → Legacy-Shape (`dosages` aus `dosage_table`, `calculated_ec = ec_final`, `ph_adjustment` via `_ph_adjustment`, `instructions = dosage_instructions`, `warnings`); zusätzlich additive Felder `ec_net`, `ec_ph_reserve`, `valid` in der Response; neuer Endpoint `POST /area-dosing` |
| `src/backend/app/api/v1/nutrient_calculations/schemas.py` | `MixingProtocolRequest` (Z. 6–13): optionale Felder `alkalinity_ppm: float = 0`, `phase: str = "vegetative"`, `recipe_ml_per_liter: dict[str, float] \| None`; `base_water_ec`-Limit `le=1.5` prüfen (EC-Budget erlaubt mehr — auf `le=5` anheben, konsistent mit `EcBudgetRequest`); neue `AreaDosingRequest/Response`-Schemas |
| `src/backend/app/api/v1/nutrient_plans/tenant_router.py` | `calculate-dosages` (Z. 208 ff.): optionaler Query-Param `location_key` |
| `src/backend/app/api/v1/fertilizers/…` (Schemas/Router) | neue Fertilizer-Felder durchreichen |
| `src/backend/app/migrations/…` | Migration: `fertilizer_type = "calmag"` für Bestandsdokumente per normalisiertem Namens-Match |

### Frontend (Folgearbeit im selben PR, UI-Review-Kette beachten)

| Datei | Änderung |
|---|---|
| `src/frontend/src/api/endpoints/nutrient-calculations.ts` | Typen: optionale Request-Felder, additive Response-Felder; neue `area-dosing`-Funktion |
| `src/frontend/src/pages/duengung/NutrientCalculationsPage.tsx` | optionales Alkalinitäts-/Phasen-Feld im Mixing-Formular (mit erklärendem Hilfetext, Feedback „Beschreibende Texte"); Anzeige `ec_ph_reserve` |
| i18n (`de`/`en`) | `enums.fertilizerType.calmag`, `enums.nutrientReleaseSpeed.*`, `pages.nutrientCalc.areaDosing.*` |

---

## 5. Testplan

Bestehende Suiten: `tests/unit/domain/engines/test_nutrient_engine.py` (32 Tests — die
Klassen `TestNutrientSolutionCalculator`-Fälle Z. 38–180 entfallen bzw. wandern als
API-Tests auf den Adapter), `test_ec_budget_engine.py` (21), `test_dosage_calculation_engine.py` (22).

### AP-10 — Konsolidierung

1. **pH-Reserve-Abzug am Live-Pfad** (`tests/unit/api/…/test_nutrient_calculations_router.py`
   bzw. bestehender API-Testort): `POST /mixing-protocol` mit
   `target_ec_ms=1.8, base_water_ec=0.4, alkalinity_ppm=200` (hart) und einem Dünger
   (`ec_contribution_per_ml=0.1`, Rezept 10 ml/L) → Dünger-EC ≈ `1.8 − 0.4 − 0.05 = 1.35`,
   `ml_per_liter ≈ 13.5`, Response enthält `ec_ph_reserve == 0.05`. Alt-Verhalten
   (14.0 ml/L) darf nicht mehr auftreten.
2. **Staffel-Grenzen** (parametrisiert, direkt auf `ph_reserve_for_alkalinity`):
   `49 → 0.02`, `50 → 0.03`, `150 → 0.03`, `151 → 0.05`.
3. **Paritätstest der Engines:** gleiche Inputs (ohne CalMag/Silikat) → `EcBudgetCalculator`
   und `DosageCalculationEngine` liefern identisches `ec_net`/pH-Reserve-Ergebnis
   (verhindert erneutes Auseinanderlaufen).
4. **Negativ-Budget-Warnung:** `base_water_ec=1.9 > target=1.8` → beide Engines warnen,
   Dosages leer / 0 — kein stilles Nullen mehr in Pipeline C.
5. **Max-Dose-Cap in C:** Skalierungsfaktor 3× auf Referenzdosis 10 ml/L bei
   `max_dose_ml_per_liter=15` → gekappt auf 15 + Warnung.
6. **`DEFAULT_MIXING_PRIORITY`:** unbekannter `fertilizer_key` in
   `_build_scaled_dosages`, `_build_reference_result` und
   `NutrientPlanService._build_channels_data` → überall identisch 50 (ein gemeinsamer
   Assert gegen die Konstante, kein Literal).
7. **Abwärtskompatibilität Response-Shape:** Contract-Test — `/mixing-protocol`-Response
   enthält weiterhin `dosages[].{fertilizer_key,product_name,ml_per_liter,total_ml,ec_contribution}`,
   `calculated_ec`, `ph_adjustment.{needed,direction,delta}`, `warnings`, `instructions`;
   Frontend-Seite: `src/frontend/src/test/api/endpoints/nutrient-calculations.test.ts`
   aktualisieren (MSW-Fixture mit neuen additiven Feldern).

### AP-10 — CalMag-Erkennung

8. **„Cal-Mag":** `Fertilizer(product_name="Cal-Mag Plus", fertilizer_type=SUPPLEMENT,
   mixing_priority=20)` + Epsom (`mixing_priority=10`) → `MixingSafetyValidator` liefert
   die CRITICAL-Reihenfolge-Warnung (Namens-Fallback normalisiert).
9. **„CaliMagic":** `fertilizer_type=FertilizerType.CALMAG` → erkannt rein über Typ,
   Name irrelevant.
10. **Kein False Positive:** `product_name="Calgon"` (kein CalMag-Typ) → nicht als
    CalMag klassifiziert.
11. **„Bittersalz"** → als sulfathaltig erkannt.
12. **Regression:** bestehende Fälle `test_calmag_sulfate_wrong_order` /
    `test_calmag_sulfate_correct_order` / Silikat-vor-CalMag bleiben grün.
13. **Migration:** Dokument mit `product_name="CaliMagic", fertilizer_type="supplement"`
    → nach Migration `fertilizer_type == "calmag"`.

### AP-11 — Flächenbasierte Dosierung

14. **g/m² × Fläche:** Hornspäne `application_rate_g_per_m2=80`, `area_m2=2.5` →
    `total_grams == 200`.
15. **L/m² × Fläche:** Kompost `application_rate_l_per_m2=3`, `area_m2=4` →
    `total_liters == 12.0`.
16. **Verdünnung:** Brennnesseljauche `dilution_ratio="1:10"` → `note`/`instructions`
    enthalten den Verdünnungshinweis.
17. **Fehlende Rate:** Dünger ohne Flächenfelder → Item mit `total_grams is None` +
    Warnung, kein Crash.
18. **N-Fixierer-Guard:** `demand_level="nitrogen_fixer"` + Dünger mit `npk_ratio=(12,0,0)`
    → Warnung.
19. **Flächen-Auflösung:** Request mit `location_key` → Fläche aus `Location.area_m2`;
    `area_m2`-Override gewinnt; `area_m2 == 0` am Standort → 422.
20. **TopDress-Wiring:** Plan-Entry mit TopDress-Channel (`grams_per_m2=40`),
    `calculate_dosages(..., location_key=…)` mit Location `area_m2=1.5` →
    `DosageEntry.total_grams == 60`, `ec_contribution == 0`; ohne `location_key` →
    Warnung „Fläche unbekannt".

---

## 6. Akzeptanzkriterien

1. `NutrientSolutionCalculator` existiert nicht mehr; `grep -rn "NutrientSolutionCalculator" src/` ist leer.
2. `POST /nutrient-calculations/mixing-protocol` erfüllt REQ-004-A: pH-Reserve nach
   Alkalinitäts-Staffel abgezogen, Rezept-Skalierung `k = EC_net_effective / EC_rezept`,
   Max-Dose-Caps, EC_max-Warnungen — bei unverändertem Legacy-Response-Shape.
3. `EC_net`-Formel und pH-Reserve-Staffel existieren genau einmal
   (`compute_ec_net` / `ph_reserve_for_alkalinity` in `ec_budget_engine.py`); beide
   verbleibenden Engines importieren sie (Paritätstest grün).
4. Das Literal `50` als mixing-priority-Fallback kommt außerhalb von
   `DEFAULT_MIXING_PRIORITY` nicht mehr vor.
5. `MixingSafetyValidator` erkennt „Cal-Mag", „CaliMagic" (Typ) und „Bittersalz"
   (Fallback); `FertilizerType.CALMAG` existiert in Backend-Enum, Migration, Frontend-Typ
   und i18n.
6. `AreaDosingCalculator` berechnet g/m²- und L/m²-Totale aus `Location.area_m2` bzw.
   explizitem `area_m2`; `TopDressParams.grams_per_m2`/`grams_per_plant` werden in
   `calculate_dosages` ausgewertet — kein totes Feld mehr.
7. Alle bestehenden Tests grün (Backend pytest, Frontend vitest), `ruff`/`eslint`/`tsc`
   clean; neue Tests aus §5 vorhanden.
8. REQ-004/REQ-004-A benötigen keine Spec-Änderung (reine Implementierungslücke); falls
   Feldnamen abweichen (Modell `application_rate_g_per_m2` == Spec W-013), Drift-Marker
   prüfen.

---

## 7. Umsetzungsreihenfolge (empfohlene PR-Schnitte)

1. **PR 1 (AP-10a, risikoarm):** Konstanten/Funktionen extrahieren
   (`compute_ec_net`, `ph_reserve_for_alkalinity`, `DEFAULT_MIXING_PRIORITY`),
   `DosageCalculationEngine` angleichen (inkl. Max-Dose-Cap + Negativ-Warnung),
   `fertilizer_classification.py` + `FertilizerType.CALMAG` + Migration + Validator-Umbau.
   Kein API-Verhalten des `/mixing-protocol`-Endpoints betroffen.
2. **PR 2 (AP-10b, Verhaltensänderung):** `/mixing-protocol` auf `EcBudgetCalculator`
   umstellen, `NutrientSolutionCalculator` löschen, Frontend-Formular + Tests.
3. **PR 3 (AP-11):** Fertilizer-W-013-Felder, `AreaDosingCalculator`, `/area-dosing`-
   Endpoint, TopDress-Wiring, Frontend-Ansicht.

Nach jedem PR: 3-Agent-Kette (UI-Review → Tests → Doku) gemäß Projekt-Feedback.

---

## 8. Risiko & Rollout

| Risiko | Bewertung | Mitigation |
|---|---|---|
| **Verhaltensänderung am bestehenden API-Pfad** `/mixing-protocol`: ml/L-Dosen sinken (pH-Reserve, ggf. Caps), `calculated_ec` enthält künftig die Reserve; Nutzer mit gespeicherten Erwartungswerten sehen andere Zahlen | **Hoch, aber gewollt** — das Alt-Verhalten ist der Bug (DOM-5): reale Mischungen überschießen den Ziel-EC nach pH-Korrektur | Änderung ist ein dedizierter PR (PR 2) mit explizitem Release-Note-Eintrag; Response additiv um `ec_ph_reserve`/`ec_net`/`valid` erweitert, damit das Frontend die Differenz **erklärt** statt sie zu verstecken; Default `alkalinity_ppm=0` wählt die kleinste Reserve (0.02 mS) → minimale Abweichung für Bestandsnutzer |
| Request-Limit-Anhebung `base_water_ec le=1.5 → le=5` lockert Validierung | niedrig | bewusste Angleichung an `EcBudgetRequest`; Grenzwerte im Contract-Test fixiert |
| `FertilizerType.CALMAG`: Alt-Clients kennen den Enum-Wert nicht | niedrig | StrEnum-Werte sind additive Strings; Frontend-Typ im selben PR; HA-Integration prüfen (`ha-integration-sync`), falls sie Fertilizer-Typen spiegelt |
| Migration klassifiziert ein Nicht-CalMag-Produkt um (False Positive im Namens-Match) | niedrig | Migration loggt jede Änderung (structlog); Pattern-Liste bewusst eng (`calmag`, `calimagic`, `calcium` nur in Kombination mit `mag`-Prüfung — im Code-Review des PR verifizieren); Feld bleibt vom Nutzer editierbar |
| TopDress-Wiring ändert `calculate_dosages`-Ergebnisse für Pläne mit TopDress-Kanälen | niedrig | Nur additiv: neue `DosageEntry`-Zeilen mit `total_grams`, EC-Budget unberührt (`ec_contribution = 0`) |
| Rollback | — | PR-weise revertierbar; PR 1 ist reines Refactoring, PR 2/3 sind in sich geschlossen |

---

## 9. Aufwandsschätzung

| Paket | Aufwand |
|---|---|
| PR 1 — Konsolidierung + Klassifikation + Migration | ~1 Tag |
| PR 2 — Endpoint-Umstellung + Frontend + Contract-Tests | ~1 Tag |
| PR 3 — Area-Dosing (Modell, Engine, API, Frontend, Tests) | ~1.5 Tage |
