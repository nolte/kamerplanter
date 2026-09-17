# Gruppe `2026-09-17-care-profile-bootstrap`

Status: Analyse abgeschlossen · Write-Gate offen (Operator-Freigabe ausstehend)

Gemessen gegen `origin/develop` @ `0b4ce20bf` (2026-09-17). Transientes Artefakt — wird vor dem Bündel-PR per `git rm` entfernt.

## Die Frage, auf die die Research-Phase gescoped war

Mit welchen Eingaben füttert der Care-Profile-Bootstrap die Engine tatsächlich, welche davon sind falsch oder leer, wie viele Bestandsprofile tragen die Folge, und welche Stelle kennt die richtige Auflösung bereits?

## Die eine logische Änderung

Der Care-Profile-Bootstrap übergibt der Engine den Familien**namen** statt des `_key` und den WateringGuide der Art — über einen Resolver, den Bootstrap, Router und Migration teilen — und eine Migration v0049 repariert die seit #1440 auf TROPICAL gefallenen, nicht von Hand geänderten Profile einmal.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1489** | `bug`, `backend` | Anker | `src/backend/app/common/dependencies.py:296-307` reicht `species.family_key` (numerischer `_key`) als `botanical_family`; `FAMILY_CARE_MAP` (`care_reminder_engine.py:317-333`) ist namensbasiert → Miss → `TROPICAL` |
| **#1481** | `bug`, `backend` | geteilte Berührungsfläche | identischer Aufruf `dependencies.py:303-307`; Engine-Signatur `care_reminder_engine.py:568-571` — beide Tiers werden von genau dieser Stelle falsch (Familie) bzw. gar nicht (Guide) befüllt |

## Was gemessen wurde, und wo der Issue-Text danebenliegt

- **v0048 löst die Familie bereits korrekt auf** (`v0048_backfill_missing_care_profiles.py:217-221, 310-317`: `family_key → botanical_families.name`), aber nur in der Migration; der Bootstrap ist von #1486/#1490 unberührt. Ein zweites Muster existiert im AI-Context-Builder: `dependencies.py:1688-1690` `_resolve_family`. **Drei Stellen kennen die Auflösung, eine nicht — die, die jede neue Pflanze durchläuft.**
- `grep -rn "watering_guide=" src/backend/app/` → nur die Engine-Signatur (`:571`) und der v0048-Docstring (`:59`). Kein Produktionsaufrufer. `Species.watering_guide` existiert (`watering_service.py:325`).
- **Nicht im Issue:** `care_reminders/router.py:61,76` (GET, `may_create=False`) und `:174,178` (`reset_profile`) reichen **client-gelieferte** Werte durch. Ob das Frontend sie sendet, ist zu messen (`grep -rn "botanical_family" src/frontend/src/api/`); wenn nicht, sind die Parameter tot und der Server leitet ab.
- Umfang der Reparatur ist zu messen: Anzahl `care_profiles` mit `source`/Herkunftsmarker „auto" **und** Familienfeld in `_key`-Form bzw. `TROPICAL` bei Art mit bekannter Familie. Was v0048 nicht markiert, ist von Hand geänderten Profilen nicht zu unterscheiden — dann gilt: nur Profile, deren Werte **exakt** dem TROPICAL-Preset entsprechen, werden neu berechnet; alle anderen werden gemeldet, nie überschrieben.

## Strukturbefund (§E)

**Symptom-Cluster.** Eine Ursache: der Bootstrap füttert die Engine mit ungemessenen Eingaben (#1440s „species is passed through" war inert — die Art *wurde* durchgereicht, nur das falsche Feld). Der Plan setzt an der Ursache an: **ein** Resolver `species → CareInputs(family_name, watering_guide)` im Service, den Bootstrap, Router-Reset **und** v0049 aufrufen, statt drei Aufrufer einzeln zu reparieren. Klasse (MEMORY.md): *Guard/Regel existiert, Geschwister nie bedient* — v0048 löst auf, der Bootstrap nicht.

## Stufe und Designentscheidungen

**Stufe 3** — die Reparaturmigration schreibt bestehende Profile um (irreversibel), und die Presets, die jede neue Pflanze bekommt, ändern sich sichtbar.

Entscheidungen (Operator, 2026-09-17): **#1481 = verdrahten.** Damit:

1. Resolver `resolve_care_inputs(species)` in `care_reminder_service.py` (Service-Schicht; Repository-Zugriff auf `botanical_families` über das vorhandene Repo). `family_name` = Name der Familie hinter `species.family_key`, `None` bei Miss (Engine fällt dann auf `TROPICAL` **mit Log** zurück — heute fällt sie stumm).
2. Bootstrap `dependencies.py:296-307` und `reset_profile` rufen den Resolver; Client-Parameter des Routers werden entfernt, wenn das Frontend sie nicht sendet (messen), sonst deprecated und ignoriert.
3. Engine: `family_key` als Eingabe ist ein **Typfehler** — `botanical_family: str` bekommt einen Guard (`isdigit()` → `ValueError`), damit die Klasse nicht zurückkommt; Unit-Test.
4. **Migration `v0049_repair_care_profiles_family_and_guide.py`** (Form von v0048: `dry_run`, Report je Position, `reversible = False` mit Grund): für jedes Profil mit numerischem Familienfeld **oder** TROPICAL-Preset bei bekannter Familie → Neuberechnung über Engine + Resolver; Profile mit Abweichung vom Preset (von Hand geändert) → `skipped_user_edited`, gemeldet. **Dry-Run gegen kind** vor dem PR, Report in den PR-Body.
5. v0049 beansprucht die Nummer **vor** #1348 (v0050) und #1468 (v0051). `test_discovery.py`: falls noch hartcodiert, "0049" eintragen (#1469 leitet die Liste gerade ab — Kollision beim Merge ist erwartet und trivial).

## Modus und Scheiben

**Modus B** — Sub-Branch je Mitglied auf `fix/2026-09-17-care-profile-bootstrap`. Herauslösbar ist #1481: verändert es die E2E-Presets so, dass `e2e-nightly` einen Preset-Wert prüft (messen: `grep -rn "watering_interval\|preset" tests/e2e/`), und der Review lehnt die neuen Werte ab, wird der Guide-Tier herausgelöst und v0049 repariert nur die Familie.

Reihenfolge: **#1489 (Resolver + Bootstrap + Engine-Guard) → #1481 (Guide-Verdrahtung) → v0049 (beide Felder).**

| Scheibe | Inhalt | Rot-zuerst |
|---|---|---|
| 1 | Resolver, Bootstrap, Router-Reset, Engine-Guard | Unit: Bootstrap mit Art aus Familie „Solanaceae" → alter Code TROPICAL-Preset, neu Solanaceae-Preset; Engine-Guard `"12345"` → `ValueError` |
| 2 | Guide-Verdrahtung | Unit: Art mit `watering_guide` → Profil trägt Guide-Werte; ohne Guide → Familien-Preset |
| 3 | v0049 + Test + kind-Dry-Run | Integration: Profil mit `family = "12345"`/TROPICAL → repariert; von Hand geändertes Profil → `skipped_user_edited`, unverändert |

## Vollständigkeitsmatrix

| Issue | AK | Scheibe | Nachweis |
|---|---|---|---|
| #1489 | Bootstrap übergibt Familiennamen | 1 | Unit rot-zuerst |
| #1489 | Bestandsprofile seit #1440 repariert | 3 | v0049-Report (kind: Zahlen) |
| #1489 | Klasse kann nicht zurückkommen | 1 | Engine-Guard + Detektor-Test für `family_key`-Durchreichung (AST: kein `family_key` als `botanical_family`-Argument) |
| #1481 | Guide erreicht die Engine in Produktion | 2 | Unit + Aufrufgraph |
| #1481 | Docstring-Tier stimmt mit dem Code überein | 2 | Docstring-Test |

## Verifikation

Rot-zuerst je Scheibe, `pytest tests/unit tests/api --max-skipped` je Tier, `tests/integration` gegen `arangodb:3.12`, v0049 Dry-Run gegen kind (Port-Forward, nur lesen). Review `python-code-reviewer` auf dem Tip. Danach: Release v0.4.1 (Operator-Entscheidung #1494) — der Merge dieser Gruppe ist die Vorbedingung.

Dispatch: `nolte-engineering:fullstack-developer`, sequenziell.
