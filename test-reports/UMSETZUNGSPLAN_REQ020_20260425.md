# Umsetzungsplan — REQ-020 Onboarding E2E Failures

**Quelle:** `/home/nolte/repos/github/kamerplanter/test-reports/e2e/20260425_110010/`
**Run:** 2026-04-25 11:00 UTC, Chrome desktop, full mode
**Ergebnis:** 10 von 18+ REQ-020-Tests fehlgeschlagen (protokoll.md zählt nur 4 — Diskrepanz, siehe F6)
**Adressat:** Full-Stack-Entwickler (Backend Python/FastAPI + Frontend React/TS + E2E pytest/Selenium)
**Geschätzter Aufwand:** 1.0–1.5 PT bei sequentieller Bearbeitung

---

## 1. Executive Summary

Alle 10 Failures lassen sich auf **drei Root-Causes** zurückführen, mit klarer Priorisierung:

| # | Root-Cause | Geschätzte Fixe Failures | Priorität |
|---|---|---|---|
| **F1** | Frontend rendert die Completed-Card, weil Redux-State nach `/onboarding/reset` nicht neu geladen wird | 6 von 10 | **P0** |
| **F2** | `PlantSelectionStep` und `PlantInstanceTable` zeigen rohe `species_key`-Werte (`3106`) statt Speziesnamen | 1 direkt + Folge-Tests | **P0** |
| **F3** | E2E-Test-Datenbank wird zwischen Runs nicht aufgeräumt (4× duplizierte `E2E-Sonnengarten`-Standorte, persistente `onb-*-1`-Plant-Instanzen) | 2 von 10 | **P1** |
| F4 | Site-Step Auto-Population aus Kit funktioniert nicht (Site-Name leer) | 1 von 10 | P1 |
| F5 | Wasser-Sektion in Site-Step für `intermediate` nicht sichtbar | 1 von 10 | P2 |
| F6 | `protokoll.md` zählt nur 8/10 Tests; Browser-Console-Logs nicht erfasst | Diagnose-Qualität | P2 |

**Empfohlene Reihenfolge:** F1 → F3 → F2 → F4 → F5 → F6.
F1 und F3 zusammen reparieren ≥ 8 von 10 Failures, weil sie die Setup-Voraussetzung für nahezu alle anderen Tests sind.

---

## 2. Detaillierte Root-Cause-Analyse

### F1 — Wizard-Reset wirkt nicht im Frontend (P0)

**Symptom:** Bei 6 von 10 Failures landet der Browser auf `/onboarding` mit dem Titel "Du hast die Einrichtung bereits abgeschlossen" (Buttons "Erneut einrichten" / "Zum Dashboard"). Erwartet: Wizard Step 1.

**Analyse-Pfad:**
1. `tests/e2e/test_req020_onboarding_wizard.py:48-66` ruft per `autouse`-Fixture `_e2e_api_post(..., "onboarding/reset")` auf.
2. Backend-Endpoint `src/backend/app/api/v1/onboarding/tenant_router.py:74-80` setzt `OnboardingState.completed = false` und `wizard_step = 0`.
3. Page-Object `tests/e2e/pages/onboarding_wizard_page.py:88-106` navigiert per `driver.get(/onboarding)`.
4. **Problem:** Der Browser-Tab hat aus dem vorherigen Test einen Redux-Store mit `onboardingState.completed = true` im Memory. Beim Page-Load triggert React zwar `fetchOnboardingState()`, aber **vor** dem Refetch rendert es bereits aus dem alten State die Completed-Card (`OnboardingWizard.tsx:388`).
5. Der Refetch setzt den State zwar danach korrekt um, doch der Test-Setup `_ensure_step_one()` (Zeile 108–139) prüft nicht robust genug auf den **Übergang** von Completed-Card → Welcome-Step. In der Diagnostics-MD steht `Checkpoints before failure: <none>` — d.h. `_ensure_step_one()` schlägt schon im Setup fehl.

**Beweis:**
- `FAILURE_test_change_site_type_from_dropdown__call.png` ⇒ Completed-Card sichtbar, Diagnostics: `current_url=http://frontend/onboarding`, `title=Willkommen bei Kamerplanter`.
- `FAILURE_test_kit_list_displays_cards__call.png` ⇒ identisches Bild.
- 6 weitere identische Failure-Screenshots.

**Hypothese pro Race-Condition:**
Das `useEffect` in `OnboardingWizard.tsx` ruft `fetchOnboardingState()` async auf — beim Erst-Render ist `loading=true`, dann sobald die persistierte `onboardingState.completed=true`-Antwort vom Server zurückkommt (aus dem vorherigen Test), wird die Completed-Card gerendert, **bevor** der Reset-Effekt zum Tragen kommt. Da die Reset-API-Antwort dem Frontend nicht mitgeteilt wird (Reset wird nur via Backend gemacht), zeigt das Frontend was es vom Backend bekommt.

**Aber:** Backend-Reset sollte `completed=false` zurückgeben. Falls die Completed-Card trotzdem erscheint, liefert entweder
(a) der Backend-Reset nicht den vollständigen State zurück, oder
(b) der `OnboardingState`-Lookup hat einen Cache-Bug (z.B. ArangoDB-Repository cached den User-Eintrag), oder
(c) der `e2e_seed_data`-Fixture ruft einmalig `onboarding/skip` auf (`tests/e2e/conftest.py:382`) und der Reset überschreibt `wizard_step` aber nicht `completed`.

**Wahrscheinlichste Ursache (c):** In `OnboardingService.reset_wizard` werden `completed` und `skipped` möglicherweise nicht beide auf `false` gesetzt. Das muss gegen die Implementierung verifiziert werden (siehe Schritt-für-Schritt unten).

---

### F2 — Species-Namen werden als rohe Keys gerendert (P0)

**Symptom:** In Step 5 "Pflanzen konfigurieren" (TC-REQ-020-031) erscheinen Labels `3106`, `3865`, `6763` statt Klartext-Speziesnamen. In der Pflanzeninstanzen-Tabelle (TC-REQ-020-008 `after-skip.png`) ist die Spalte "Pflanzenname" leer (`—`), und die Instanz-IDs lauten `onb-3106-1`, `onb-3865-1`, `onb-6763-1`.

**Analyse-Pfad:**
1. `src/frontend/src/pages/onboarding/steps/PlantSelectionStep.tsx:47-50` definiert
   ```ts
   const getSpeciesName = (key: string): string => {
     const sp = speciesMap.get(key);
     if (!sp) return key;          // Fallback: Key wird angezeigt!
     return sp.common_names?.[0] ?? sp.scientific_name;
   };
   ```
2. Die `speciesMap` enthält aber offenbar nicht die Keys `3106`, `3865`, `6763`. Diese Keys kommen aus `favorite_species_keys` im OnboardingState.
3. Die numerischen Werte deuten auf **ArangoDB-`_key`-Werte** hin (interne Document-Keys), nicht auf semantische Slugs (wie `basilikum`, `petersilie`).
4. Die Pflanzeninstanz-Tabelle zeigt zusätzlich keinen `display_name` — vermutlich resolvet auch sie den Species-Lookup nicht.

**Konsequenz:** Selbst wenn F1 gefixt wird, sehen Endnutzer im Wizard kryptische Zahlen. Der Test `test_summary_step_displays_setup_info` schlägt fehl, weil er auf Klartext prüft.

**Mögliche Ursachen:**
- Backend-Endpoint `/api/v1/species/` liefert nur eine Subset-Liste (mit Pagination), das Frontend lädt aber nicht alle Spezies, die das Kit referenziert.
- Die `StarterKit`-Definition referenziert Spezies per ArangoDB-`_key`, das Frontend erwartet aber `slug`/`semantic_key`.

---

### F3 — Persistente Test-Daten zwischen Runs (P1)

**Symptom:**
- `FAILURE_test_site_step_auto_populated_from_kit__call.png` zeigt unter "Bestehende Standorte" **4× `E2E-Sonnengarten` / Innenbereich** + 1× `Meine Fensterbank`.
- `TC-REQ-020-008_after-skip.png` zeigt 3 Plant-Instanzen `onb-3106-1`, `onb-3865-1`, `onb-6763-1`, alle mit `Gepflanzt am: 25.4.2026` (heutiges Datum) — d.h. sie wurden in einem **früheren Run am gleichen Tag** angelegt und nicht aufgeräumt.

**Analyse-Pfad:**
1. `tests/e2e/conftest.py:278-391` `e2e_seed_data` ist `scope="session"`, wird also pro pytest-xdist-Worker einmal aufgerufen.
2. Bei jedem CI-Run werden über `_post(f"{api}/sites", ...)` neue Sites angelegt — die Idempotenz prüft nur auf `name == "E2E-Sonnengarten"` (Zeile 310), löscht aber Duplikate nicht und prüft nicht auf vorherige Locations.
3. Wizard-Tests lassen über das Onboarding-Complete/Skip-Verhalten **PlantInstance-Records mit Pattern `onb-{key}-{n}`** zurück (Zeile 122 ff. von `test_req020_onboarding_wizard.py`).
4. Es existiert kein Teardown.

**Konsequenz:**
- Site-Step zeigt mit jedem Run mehr `E2E-Sonnengarten`-Einträge → UI wird vollgemüllt.
- Auto-Populate-Test (TC-REQ-020-023) könnte den vorgeschlagenen vs. existierenden Site nicht eindeutig identifizieren (Findings widersprüchlich).

---

### F4 — Site-Step Auto-Population fehlerhaft

**Symptom:** `FAILURE_test_site_step_auto_populated_from_kit__call.png` zeigt:
- Vorgeschlagene Site `Meine Fensterbank / Fensterbrett` ✓ (korrekt)
- Aber: **kein** Site-Name im Eingabefeld (Test erwartet vermutlich, dass das Eingabefeld sichtbar ist mit dem Kit-Namen)
- Stattdessen wird die **bestehende** Site `Meine Fensterbank` als ausgewählt markiert (grüner Haken am unteren Eintrag).

Vermutung: Das Auto-Select-Verhalten (existierende Site bevorzugen, wenn Name übereinstimmt) ist eine **neue** Logik, die der Test noch nicht kennt. Test prüft auf das Eingabefeld; die UI zeigt die existierende Site-Auswahl.

---

### F5 — Wasser-Sektion fehlt in Site-Step (intermediate)

**Symptom:** `FAILURE_test_water_section_visible_for_intermediate__call.png` zeigt Site-Step mit nur Standort-Auswahl, **ohne** "Dein Wasser"-Sektion (RO-System, EC, pH).

**Spec-Bezug:** REQ-020 v1.1 §… (siehe MEMORY: "Optional 'Dein Wasser' section in wizard step 3 (intermediate+ only)").

**Mögliche Ursachen:**
- `experience_level` wurde nicht korrekt auf `intermediate` gesetzt (Step 1 wurde übersprungen oder Default-Wert beibehalten).
- Frontend-Bedingung im `SiteSetupStep.tsx` prüft falsche Variable.
- Test-Sequenz erreicht den Site-Step nie auf intermediate-Pfad.

---

### F6 — Reporting-Lücken (P2)

**Symptom A:** `protokoll.md` meldet `Gesamt: 8 / Bestanden: 4 / Fehlgeschlagen: 4`, doch in `diagnostics/` liegen 10 Failure-Diagnose-Dateien. → Tests, die in der `setup`-Phase (autouse-Fixture `reset_onboarding_state`) fehlschlagen, werden vom Protocol-Plugin nicht als `call`-Failure aggregiert. Der `pytest_runtest_makereport`-Hook in `conftest.py:698` registriert nur `report.when == "call"` (Zeile 718). Setup-Failures landen nicht in `_protocol_generator.add_result()`.

**Symptom B:** Diagnostics enthalten `<not available: AttributeError("'WebDriver' object has no attribute 'get_log'")>` — Selenium Chrome ohne `goog:loggingPrefs`-Capability liefert keine Browser-Konsolen-Logs. JS-Errors bleiben unsichtbar.

---

## 3. Dependency-Graph

```
                          F6 (Reporting)
                              │
                              │ verbessert Diagnose
                              ▼
F1 (Reset) ──── löst ──→ TC-005, TC-018, TC-019, TC-021, TC-024, TC-completion-redirect
                                                              ──┐
                                                                ▼
F3 (DB-Cleanup) ──── löst ──→ TC-023 (Auto-Populate), TC-001 (Completed-Card-Test)
                                                              ──┐
                                                                ▼
                                            F4 (Auto-Populate Logik)
                                                              ──┐
                                                                ▼
F2 (Species-Names) ──── repariert ──→ TC-031 (Summary), Cosmetic in TC-008
                                                              ──┐
                                                                ▼
                                            F5 (Water-Section, intermediate-Pfad)
```

**Kritischer Pfad:** F1 → F3 → F2. Erst dann sind F4/F5 sinnvoll testbar.

---

## 4. Konkrete Umsetzung

### Schritt 1 — F6 zuerst: Diagnose verbessern (15 Min)

**Warum zuerst?** Ohne Browser-Console-Logs kann F1 nicht eindeutig diagnostiziert werden.

**Datei:** `tests/e2e/conftest.py`

**Änderung A:** Browser-Logging aktivieren. Zeile ~439 (Chrome-Optionen) und ~470 (lokale Chrome) erweitern:

```python
options.add_argument("--lang=de-DE")
options.set_capability("goog:loggingPrefs", {"browser": "ALL"})  # NEU
```

und identisch im `else`-Zweig für lokale Chrome bei Zeile ~478.

**Änderung B:** Setup-Failures in Protokoll aufnehmen. In `pytest_runtest_makereport` (Zeile ~718):

```python
if report.when in ("call", "setup") and not report.skipped:
    # alte Bedingung: report.when == "call"
    # NEU: setup-Failures als eigenständiges Test-Ergebnis registrieren,
    # damit sie in protokoll.md erscheinen.
    if report.when == "setup" and not report.failed:
        return  # erfolgreicher setup → kein Eintrag
    item._report = report
    if _protocol_generator is not None:
        ...
```

**Verifikation:** Run lokal mit `pytest tests/e2e/test_req020_onboarding_wizard.py::TestSiteTypeChange --generate-protocol`. Im neuen `protokoll.md` müssen alle 10 Failures gelistet sein, und in `diagnostics/*.md` muss `console_errors` JS-Logs enthalten (kein `<not available>` mehr).

---

### Schritt 2 — F1 Backend-Reset prüfen & härten (30 Min)

**Datei:** `src/backend/app/domain/services/onboarding_service.py`

**Aktion:** `reset_wizard()`-Methode öffnen und sicherstellen, dass alle relevanten Felder genullt werden:

```python
def reset_wizard(self, user_key: str) -> OnboardingState:
    state = self._repo.get_or_create_for_user(user_key)
    state.completed = False
    state.completed_at = None
    state.skipped = False
    state.skipped_at = None
    state.wizard_step = 0
    state.selected_kit_id = None
    state.selected_experience_level = None
    state.site_name = None
    state.site_type = None
    state.plant_count = None
    state.favorite_species_keys = []
    state.favorite_nutrient_plan_keys = []
    # plant_configs etc. ebenfalls zurücksetzen
    state.plant_configs = []
    self._repo.update(state)
    return state
```

**Test:** Backend-Unit-Test in `src/backend/tests/domain/services/test_onboarding_service.py`:

```python
def test_reset_wizard_clears_all_state(svc, repo):
    user_key = "user_123"
    svc.complete_wizard(user_key=user_key, tenant_key="t1", kit_id="kit-A", ...)
    state = svc.reset_wizard(user_key)
    assert state.completed is False
    assert state.skipped is False
    assert state.wizard_step == 0
    assert state.favorite_species_keys == []
    assert state.plant_configs == []
```

---

### Schritt 3 — F1 Frontend Refetch nach Navigate (45 Min)

**Datei:** `src/frontend/src/pages/onboarding/OnboardingWizard.tsx`

**Problem:** Beim Navigieren auf `/onboarding` wird die Completed-Card gerendert, bevor der Refetch durch ist.

**Fix-Option A (bevorzugt) — Render gating:**

```tsx
const [stateLoaded, setStateLoaded] = useState(false);

useEffect(() => {
  dispatch(fetchOnboardingState())
    .unwrap()
    .finally(() => setStateLoaded(true));
}, [dispatch]);

// Vor JSX-Return:
if (!stateLoaded) return <LoadingSkeleton variant="card" />;
```

Dadurch wird nichts gerendert bis das Backend den frischen State geliefert hat.

**Fix-Option B — Slice-Initialwert auf `null`:**
In `src/frontend/src/store/slices/onboardingSlice.ts` sicherstellen, dass `initialState.onboardingState = null` (nicht ein gecachetes Persisted-Objekt). Falls Redux-Persist aktiv ist, `onboardingState` aus der Whitelist nehmen.

**Test:** Frontend-Vitest in `src/frontend/src/pages/onboarding/__tests__/OnboardingWizard.test.tsx`:

```tsx
it('does not render completed-card before backend state is loaded', async () => {
  // mock fetchOnboardingState to delay
  const { queryByText } = render(<OnboardingWizard />);
  expect(queryByText('Du hast die Einrichtung bereits abgeschlossen.')).toBeNull();
  // resolve mock
  await waitForLoading();
  // assert wizard or completed-card based on mocked response
});
```

---

### Schritt 4 — F3 Test-Datenbank-Cleanup (30 Min)

**Datei:** `tests/e2e/conftest.py`

**Aktion:** `e2e_seed_data` um Cleanup-Block erweitern, **bevor** neue Daten geseedet werden:

```python
# Zwischen Zeile 306 (try:) und 307 (list_status, sites = ...):
# 1. Lösche alle Plant-Instanzen mit name-prefix "onb-"
inst_status, instances = _get(f"{api}/plant-instances")
if inst_status == 200 and isinstance(instances, list):
    for inst in instances:
        if inst.get("instance_id", "").startswith("onb-"):
            _delete = lambda url: urllib.request.urlopen(  # noqa: E731
                urllib.request.Request(url, method="DELETE", headers=_headers())
            )
            try:
                _delete(f"{api}/plant-instances/{inst['key']}")
            except Exception:
                pass

# 2. Lösche duplizierte E2E-Sonnengarten-Sites (alle bis auf die erste)
list_status, sites = _get(f"{api}/sites")
if list_status == 200 and isinstance(sites, list):
    e2e_sites = [s for s in sites if s.get("name") == SITE_NAME]
    for s in e2e_sites[1:]:
        try:
            _delete(f"{api}/sites/{s['key']}")
        except Exception:
            pass
```

**Hinweis:** `_delete` braucht eine eigene Helper-Funktion analog zu `_post`/`_get` in `_api_helpers`. Die ergänzen.

**Alternativ (sauberer):** Backend-Endpoint `POST /api/v1/admin/e2e-cleanup` einführen, der per Token-Schutz im Light-Mode die gesamten E2E-User-Daten zurücksetzt. Vermeidet HTTP-Iterations-Komplexität in pytest.

---

### Schritt 5 — F2 Species-Resolver fixen (60 Min)

**Datei:** `src/frontend/src/pages/onboarding/steps/PlantSelectionStep.tsx`

**Problem-Verifikation:** Logge `speciesMap.size` und `key` an Zeile 47–50:
```tsx
const getSpeciesName = (key: string): string => {
  const sp = speciesMap.get(key);
  if (!sp) {
    console.warn('[PlantSelectionStep] species not found:', { key, mapSize: speciesMap.size });
    return key;
  }
  return sp.common_names?.[0] ?? sp.scientific_name;
};
```

Run einmal lokal, dann Console-Output prüfen. Hypothesen:
1. `speciesMap` ist leer → `useGetSpeciesQuery()` liefert nicht (vergleiche mit `FavoriteSpeciesStep.tsx`).
2. `key`-Format weicht ab: Backend liefert `_key` (z.B. `"3106"`), Frontend lädt nur Spezies mit semantischem Slug.

**Fix-Option A (Frontend lädt alle Species):**
Im `OnboardingWizard.tsx` oder in einem Page-Level-Provider: `useGetAllSpeciesQuery()` aufrufen mit `pageSize=10000`, in den Redux-Store legen, beide Step-Komponenten lesen aus dem Store.

**Fix-Option B (Backend liefert resolvte Daten):**
`/api/v1/t/{slug}/onboarding/state` so erweitern, dass `favorite_species_keys` ergänzt wird um `favorite_species` (Liste mit `key`, `common_name`, `scientific_name`). Frontend nutzt dann diese reichere Datenstruktur.

**Empfehlung:** Option B, da sie auch der Pflanzeninstanz-Tabelle (siehe nächster Punkt) hilft.

**Datei:** `src/frontend/src/pages/pflanzen/PlantInstanceListPage.tsx` (oder vergleichbar)

Die Spalte "Pflanzenname" zeigt `—`. Vermutlich rendert sie ein Feld wie `instance.species.common_name`, doch `species` wird vom Backend nicht expandiert. Lösung: Backend-Endpoint `GET /api/v1/t/{slug}/plant-instances` mit `?expand=species` ausstatten und Frontend-Zelle anpassen.

---

### Schritt 6 — F4 Auto-Population Verhalten klären (30 Min)

**Vorgehen:**
1. Spec-Anker prüfen: `spec/req/REQ-020_*.md` Abschnitt zu Site-Step-Auto-Populate. Soll das Eingabefeld leer sein, wenn eine bestehende Site mit gleichem Namen existiert?
2. Falls **Spec sagt: existierende Site bevorzugen** → Test anpassen, der Test in `test_req020_onboarding_wizard.py:test_site_step_auto_populated_from_kit` muss prüfen, dass entweder das Eingabefeld den Kit-Namen enthält **oder** eine bestehende Site mit dem Namen vorausgewählt ist.
3. Falls **Spec sagt: Eingabefeld immer Kit-Name** → Frontend-Bug in `SiteSetupStep.tsx` (Auto-Select-Logik überschreibt manuell gesetzten Namen).

**Test-Anpassung (falls Spec-Verhalten korrekt ist):**

```python
def test_site_step_auto_populated_from_kit(self, wizard, screenshot):
    wizard.advance_to_step_kit()
    wizard.select_kit("fensterbank-kraeuter")
    wizard.advance_to_step_favorites()
    wizard.advance_to_step_site()

    # Akzeptiere beide Varianten: Eingabefeld ODER vorausgewählte Site
    site_name_value = wizard.get_site_name_value()
    selected_existing = wizard.is_existing_site_selected("Meine Fensterbank")

    assert site_name_value == "Meine Fensterbank" or selected_existing, (
        "Expected Kit-Name in input OR existing site preselected"
    )
```

---

### Schritt 7 — F5 Water-Section Verhalten

**Datei:** `tests/e2e/pages/onboarding_wizard_page.py`

In `advance_to_step_kit(experience_level="intermediate")` wirklich verifizieren, dass der `intermediate`-Card geklickt wird, **bevor** `Weiter` gedrückt wird. Falls die Methode nur den Klick auf `Weiter` macht ohne den Level zu setzen, bleibt `beginner` aktiv und die Water-Section wird gar nicht angezeigt.

**Frontend-Datei:** `src/frontend/src/pages/onboarding/steps/SiteSetupStep.tsx`

Conditional-Render der Water-Section: `{(experienceLevel === 'intermediate' || experienceLevel === 'expert') && <WaterSection />}` muss aus dem Redux-State lesen, nicht aus lokalem React-State, der bei Step-Wechsel verloren gehen könnte.

---

## 5. Verifikations-Schritte (nach Implementierung)

```bash
# 1. Backend-Tests
cd src/backend && pytest tests/domain/services/test_onboarding_service.py -v

# 2. Frontend-Tests
cd src/frontend && npm run test -- onboarding

# 3. E2E-Subset (lokal, ohne Docker, schnell)
cd tests/e2e && pytest -v --base-url http://localhost:5173 \
    test_req020_onboarding_wizard.py \
    test_req020_onboarding_steps.py \
    --generate-protocol

# 4. Diagnose-Datei prüfen — keine "<not available: get_log>"-Einträge mehr
grep -L "not available: get_log" \
    test-reports/e2e/<TIMESTAMP>/diagnostics/*.md

# 5. Erfolgs-Quote: 18/18 Tests passieren
```

**Akzeptanzkriterien:**
- [ ] `protokoll.md` zeigt mindestens 18 Tests (alle REQ-020-Tests inkl. Setup-Failures)
- [ ] 0 von 18 Failures
- [ ] In keinem Failure-Screenshot ist mehr die Completed-Card zu sehen wenn Wizard erwartet wird
- [ ] Step-5-Plant-Konfig-Labels enthalten Klartextnamen (z.B. "Basilikum"), keine Zahlen
- [ ] Pflanzeninstanz-Tabelle zeigt Klartext-Speziesnamen
- [ ] Im Site-Step erscheint maximal **eine** `E2E-Sonnengarten`-Site (nicht 4)
- [ ] Im `intermediate`-Pfad ist die Water-Section sichtbar
- [ ] `console_errors` in Diagnostics enthält valides JSON-Array (auch wenn leer)

---

## 6. Risiken & Edge Cases

| Risiko | Mitigation |
|---|---|
| Backend-Reset wird in OAuth-Setup nicht gesehen, weil User-Key wechselt | `_e2e_api_post` ruft mit aktuellem JWT, sollte konsistent sein. Verifizieren mit Login-Token-Decode. |
| Redux-Persist cached `onboardingState` über Browser-Reload | `redux-persist`-Konfig prüfen. Falls `onboardingState` persistiert wird, aus Whitelist entfernen oder beim Reset purge. |
| `_delete`-Helper fehlt in `_api_helpers` | Im Cleanup-Block direkt mit `urllib.request.Request(url, method="DELETE")` arbeiten. |
| Spec für Auto-Population ist nicht eindeutig | Vor Code-Änderung Spec lesen (`spec/req/REQ-020_Onboarding-Wizard.md`), bei Zweifel mit Product klären. |
| F2 Option B (Backend-Expansion) bricht andere Konsumenten | Neuer Endpoint-Parameter `?expand=species` ist additiv, keine Breaking Changes. |
| Setup-Failure-Aggregation in F6 verändert bestehende Reports | Nur additiv (Setup-Failures werden zusätzlich gezählt). Bestandstests bleiben unverändert. |

---

## 7. Spec-Referenzen

- **REQ-020 v1.1:** Onboarding-Wizard, optional "Dein Wasser"-Sektion (intermediate+)
- **REQ-021:** UI-Erfahrungsstufen (beginner/intermediate/expert)
- **NFR-001:** 5-Layer-Architektur (Frontend darf nicht direkt DB-State lesen)
- **NFR-008 §3.1, §3.4, §4.4:** E2E-Test-Konventionen, Screenshot-Checkpoints, Protokoll-Generierung
- **MEMORY:** REQ-020 implementiert (StarterKitService, OnboardingService, 9 Endpoints, 9 Seed-Kits)

---

## 8. Pull-Request-Strategie

**Empfehlung:** Aufteilen in 3 PRs für saubere Reviews:

1. **PR 1 — Diagnose & Test-Infrastruktur (F6 + F3):**
   `feat(e2e): browser console logging, setup-failure aggregation, test-data cleanup`
   - Pfade: `tests/e2e/conftest.py`
   - Risiko: niedrig, additiv
   - Reviewer: QA-Lead

2. **PR 2 — Backend Reset härten (F2 Option B + Backend-Teil von F1):**
   `fix(onboarding): full reset clears all state, expand species in onboarding-state response`
   - Pfade: `src/backend/app/domain/services/onboarding_service.py`, `src/backend/app/api/v1/onboarding/...`, Tests
   - Risiko: mittel (API-Schema-Erweiterung)
   - Reviewer: Backend-Lead

3. **PR 3 — Frontend Render-Gating + Species-Resolution (F1, F2, F4, F5):**
   `fix(frontend): gate onboarding render on backend state, resolve species names`
   - Pfade: `src/frontend/src/pages/onboarding/OnboardingWizard.tsx`, `PlantSelectionStep.tsx`, `SiteSetupStep.tsx`, `PlantInstanceListPage.tsx`, Slice
   - Risiko: mittel (UX-Änderung im First-Render-Verhalten)
   - Reviewer: Frontend-Lead + QA

**Reihenfolge:** PR 1 → PR 2 → PR 3 jeweils nach Merge des Vorgängers.

---

*Erstellt am 2026-04-25 aus Test-Run `20260425_110010` für `fix/e2e-onboarding`.*
