# Audit: Vollständigkeit der Lebenszyklus-Abläufe (REQ-003)

**Erstellt von:** Lifecycle-Vollständigkeits-Audit (Claude Code, Opus 4.8)
**Datum:** 2026-07-02
**Frage:** Bildet REQ-003 (Phasensteuerung) die unterschiedlichen Lebenszyklus-Abläufe **vollständig** ab?
**Methode:** Diff der kanonischen `PhaseType`-Liste (REQ-003) gegen den tatsächlich in den Seed-Daten
(210 Arten) verwendeten `phase_entry.name`-Enum.

---

## Ergebnis

Die **Kern-Archetypen** waren bereits vollständig und hochwertig modelliert (annuell, biennial, perennial
outdoor/indoor, Autoflower, Geophyt, Juvenil-Skip, Monokarp, Post-Harvest-Handoff — Stand D1–D7). **Nicht**
abgebildet waren spezialisierte Sukkulenten-/Zier-/Sonderkultur-Abläufe, obwohl sie real in den Seed-Daten
vorkommen. Zusätzlich bestand ein **bidirektionaler Vokabular-Drift** zwischen Spec und Schema.

Alle Befunde wurden in REQ-003 (Audit-Block **D8–D13**) + den Seed-Schemas aufgearbeitet.

---

## Befund 1 — Bidirektionaler Vokabular-Drift Spec ↔ Schema (behoben)

Die Spec deklarierte 17 Phasen als „EINZIGE maßgebliche Wertliste"; der Schema-Enum hatte 47.

- **36 Phasenwerte** in Schema/Daten fehlten in der kanonischen Spec-Liste (kein Template, kein Mapping).
- **6 kanonische Spec-Phasen** (`bolting`, `bud_break`, `fruit_development`, `acclimatization`,
  `maintenance`, `repotting_recovery`) fehlten im Schema-Enum → Daten, die den Spec-Templates folgen,
  waren **nicht persistierbar**.
- `harvest` war im Schema-Enum + in Daten, obwohl die Spec sagt: „`harvest` ist KEINE Phase".

**Auflösung (D8/D13):** `PhaseType` auf **53 Werte** erweitert (= Schema-Enum); Engine-Rollen-Mapping für
alle 36 erweiterten Phasen; die 6 Kern-Phasen in `_defs`/`plant_info`/`lifecycles`/`fertilizers` ergänzt
(nun ebenfalls 53); `harvest` als Legacy mit Migrations-Pfad (`→ ripening` + Ernte-Event) dokumentiert.

## Befund 2 — Nicht abgebildete Abläufe (behoben via Flow-Templates)

| Fehlender Ablauf | Beleg (Phasen) | Auflösung |
|---|---|---|
| CAM-/Sukkulenten-(Doppel-)Ruhe | `winter_rest` (42×), `summer_rest`, `cool_rest`, `winter_hull_change` | **D9-Template** |
| Kindel-Monokarpie (Agave/Bromelie) | `pup_establishment`, `establishment`, `mature` | **D10-Template** (klonale Fortführung via neue Instanzen) |
| Photoperiodische Zier-Induktion | `short_day_induction`, `bract_coloring` | **D11-Template** |
| Palme | `young_palm`, `shaft_growth` | **D12-Template** |
| Farn | `leaf_phase`, `rest_phase`, `rest` | **D12-Template** |
| Feingranulare Geophyten | `corm_ripening`, `tuber_formation`, `sprout_formation`, `bulbil_establishment`, `dry_storage` | **D12-Template** (+ D7-Anbindung) |
| Distinkte Doppel-Dormanz | `summer_dormancy`, `winter_dormancy` | D8-Mapping → `dormancy` |
| Saisonale Wachstums-/Blühphasen | `spring_growth`, `autumn_growth_bloom`, `autumn_ripening`, `growth_bloom`, `flowering_fruit`, `pre_bloom`, `bud_formation`, `budding`, `sprouting`, `fruiting` | D8-Mapping (Engine-Rolle) |

---

## Umsetzung (Teil von PR #304)

| Änderung | Datei |
|---|---|
| `PhaseType` 17 → 53, gruppiert (Engine-Kern + erweitert) | `spec/req/REQ-003_Phasensteuerung.md` |
| Audit-Block D8–D13 (Mapping-Tabelle + 5 Flow-Templates) | `spec/req/REQ-003_Phasensteuerung.md` |
| Business-Case-Archetyp-Liste um D9–D12 ergänzt; Changelog 2.9 | `spec/req/REQ-003_Phasensteuerung.md` |
| 6 Kern-Phasen in Schema-Enum ergänzt (53 Werte) | `schemas/{_defs,plant_info,lifecycles,fertilizers}.schema.yaml` |

## Offen (Folgearbeit)

- **`harvest`-Daten-Backfill** (`name: harvest` → `ripening`) + anschließende Enum-Entfernung — eigener,
  datenverändernder Change (Removal-Verbot in additiven PRs).
- **Engine-Implementierung** der D8-Mappings + D9–D12-Templates im Backend (`PhaseTransitionEngine`,
  Phase-Sequence-Seeds) — dieser Audit ist spec-/schema-seitig; die Code-Umsetzung ist ein separater Strang.
- **`$ref`-Konsolidierung** des dupliziert-inline geführten Phasen-Enums auf `_defs#/$defs/phase_name`
  (seed-data-validator Phase 0.5) — optional, reduziert die 4-fache Duplikation.
