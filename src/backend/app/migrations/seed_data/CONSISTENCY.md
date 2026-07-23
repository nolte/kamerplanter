# Steckbrief ↔ Seed: Source-of-Truth-Vertrag (Issue #680)

> **Regel:** Die **Seed-YAMLs in diesem Verzeichnis sind die Source of Truth**
> für die lebenszyklus-treibenden Attribute. Die **Steckbriefe unter
> `spec/knowledge/plants/*.md` sind Dokumentation, die dem Seed folgen muss** —
> nicht umgekehrt.

## Warum

Es gibt **keinen Generator**, der den Seed aus den Steckbriefen ableitet; beide
Seiten wurden bisher unabhängig gepflegt und sind still divergiert (das Audit
`spec/analysis/master-data-capture-audit-2026-07.md` §3.2, UR-2 fand u. a. 14
`growth_habit`-Mismatches). Die Seed-Werte steuern den Lifecycle-Resolver
(REQ-003 §D14) und die Migrations-Kohorten (v0027), sind also maßgeblich. Bei
einem Konflikt gewinnt der Seed; der Steckbrief wird angeglichen.

## Erzwungen durch

`app/migrations/seed_steckbrief_consistency.py` verdrahtet fünf Attribute zum
Abgleich zwischen den KA-Feld-verankerten Tabellen der Steckbriefe und den
Seed-YAMLs und **bricht bei Drift** (Exit-Code ≠ 0):

| Attribut | Seed-Quelle | Status |
|----------|-------------|--------|
| `growth_habit` | `species.yaml:species[]`, `plant_info*.yaml:new_species[]` | aktiv |
| `photosynthesis_type` | `species.yaml:species[]`, `plant_info*.yaml:new_species[]` | aktiv |
| `photoperiod_type` | `plant_info*.yaml:lifecycle_configs[<name>]` | aktiv |
| `flowering_strategy` | `species.yaml:lifecycle_overrides[<name>]`, `lifecycle_configs` | aktiv |
| `growth_determinacy` | `species.yaml:lifecycle_overrides[<name>]`, `lifecycle_configs` | latent¹ |

Ein Abgleich greift nur, wenn **beide** Seiten einen Wert führen.

> ¹ **`growth_determinacy` ist derzeit latent:** Kein Steckbrief führt bislang
> den Anker `` `lifecycle_configs.growth_determinacy` `` (0/210), daher wird die
> Seed-Seite dafür heute nie verglichen. Die Verdrahtung bleibt bestehen, damit
> die Prüfung **automatisch greift**, sobald ein Steckbrief das Feld führt —
> ohne dann eine Anpassung des Validators zu erfordern. Es wird also keine volle
> Abdeckung für dieses Attribut behauptet.

Ausführung:

```bash
python src/backend/app/migrations/seed_steckbrief_consistency.py --verbose
```

Gates:

- **Required `static`-Check** — pre-commit-Hook `steckbrief-seed-consistency`.
- **Backend CI** (`.github/workflows/backend.yml`) — expliziter Schritt +
  Unit-Test `tests/unit/migrations/test_steckbrief_seed_consistency.py`.

## Bei Drift

1. **Steckbrief nachziehen (Normalfall):** den Wert im Steckbrief an den Seed
   angleichen, mit knapper `<!-- KORREKTUR #680: ... -->`-Notiz.
2. **Bewusste, belegte Ausnahme:** einen kommentierten Eintrag in
   `ALLOWED_DISCREPANCIES` (im Validator-Modul) hinzufügen — mit
   `scientific_name`, `attribute`, beiden Werten, `reason` und `source`. Der
   Eintrag pinnt beide Werte exakt, kann also keinen anderen künftigen Drift
   still verschlucken. Erster Eintrag: *Stephanotis floribunda* / `photoperiod_type`
   (Seed `short_day` für die v0027-Kohorten-Bindung vs. belegt `day_neutral`).

Mehrere Steckbriefe dürfen auf **eine** geseedete Art abbilden (`spp.`-Aggregate,
Sorten — das intendierte 210→207-Delta, Audit §6); ein Steckbrief ohne
Seed-Gegenstück wird übersprungen, nie als Drift gewertet.
