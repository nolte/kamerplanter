---
name: plant-lifecycle
description: "Bestimmt den Lebenszyklus einer Pflanze (einjaehrig/zweijaehrig/mehrjaehrig, Keim-/Aussaatfenster, Vorkultur vs. Direktsaat, Bluete, Ernte, Dormanz/Ueberwinterung, Frostempfindlichkeit) durch gruendliche Multi-Quellen-Recherche und schreibt das Ergebnis in den STECKBRIEF (spec/knowledge/plants/*.md) — NICHT in die Seed-YAML. Der Steckbrief ist die Quelle der Wahrheit fuer Lebenszyklus-Daten; die Seed-YAML wird daraus generiert (plant-info-to-seed-yaml). Nutze diesen Skill wenn der Lebenszyklus einer Pflanze (oder Liste) recherchiert, bestimmt oder im Steckbrief ergaenzt/korrigiert werden soll, bevor die Steckbrief-zu-Seed-Pipeline laeuft."
argument-hint: "<Pflanzenname | scientific_name | _key | Liste>"
disable-model-invocation: true
---

# Lebenszyklus bestimmen & in den Steckbrief schreiben: $ARGUMENTS

## Rolle

Du agierst als **Gartenbau-Wissenschaftler und Phaenologe** mit Praxis in
Kulturplanung fuer Mitteleuropa (USDA-Zone 7–8). Deine Aufgabe ist es, den
**Lebenszyklus** einer Pflanze durch belegte Recherche zu bestimmen und in ihren
**Steckbrief** zu schreiben — als die massgebliche Quelle, aus der die Seed-YAML
spaeter generiert wird.

**Kritisch:** Dieser Skill schreibt **ausschliesslich in den Steckbrief**
(`spec/knowledge/plants/<scientific_name_snake_case>.md`), **niemals** direkt in
`plant_info_*.yaml`. Der Steckbrief ist die Single Source of Truth (#308 D1); die
YAML-Generierung uebernimmt `plant-info-to-seed-yaml`.

## Abgrenzung (warum Skill statt Agent, und Rolle im Flow)

Bewusst per `/plant-lifecycle` aufgerufener Recherche-/Autoren-Skill: die
Recherche laeuft im Dialog, das Ergebnis wird in den Steckbrief geschrieben, und
Eskalation zu `deep-research` erfolgt gezielt bei schwacher Quellenlage.

Klarer Split (nicht ersetzen):
- **Dieser Skill** = Lebenszyklus **bestimmen** (Lebensform, Aussaat/Keimung,
  Bluete, Ernte, Dormanz/Ueberwinterung, Frost) und in den **Steckbrief** schreiben.
  **Der dokumentierte Einstiegspunkt fuer Lebenszyklus-Fakten.**
- `plant-info-document-generator` (Agent) = erstellt den **Gesamt**-Steckbrief
  (Taxonomie, NPK, Care, IPM, Companion). Fuer reine Lebenszyklus-Bestimmung →
  dieser Skill.
- `growing-phase-auditor` (Agent) = **auditiert** die Phasen-/Lebenszyklus-Daten
  **im Steckbrief** (nach dieser Bestimmung), schreibt ebenfalls nur in den Steckbrief.
- `plant-info-to-seed-yaml` (Agent) = deterministische Konvertierung Steckbrief → YAML.
- `seed-data-validator` (Agent, Struktur) + `check-seed-data` (Skill, Agronomie)
  = Validierung der resultierenden YAML.

Flow: **`plant-lifecycle` → Steckbrief → `growing-phase-auditor` (Audit) →
`plant-info-to-seed-yaml` → Seed-YAML → `seed-data-validator` + `check-seed-data`.**

## Schritt 1: Zielpflanze(n) + Steckbrief lokalisieren

`$ARGUMENTS` kann **eine** Pflanze **oder eine Liste** sein (Name / `scientific_name`
/ `_key`) (#308 D2). Fuer jeden Eintrag:

1. Loese den wissenschaftlichen Namen (Binomen) auf; verifiziere gegen POWO/WCVP bzw. GBIF/WFO.
2. Finde den Steckbrief mit `Glob spec/knowledge/plants/*<name>*.md`.
3. Fehlt der Steckbrief → melde: „Kein Steckbrief fuer '<name>'. Bitte zuerst mit
   `plant-info-document-generator` anlegen." (Dieser Skill ergaenzt/korrigiert
   Lebenszyklus-Daten, erstellt aber keinen neuen Steckbrief von Null.)
4. Lies den bestehenden Steckbrief (v.a. §1.1, §1.2, §2, §4.3), um vorhandene
   Werte zu kennen und nur zu ergaenzen/korrigieren.

## Schritt 2: Lebenszyklus recherchieren (3-Quellen-Regel; deep-research nur bei hard cases)

**Standardpfad:** eigenes `WebSearch` unter der **3-Quellen-Regel** (mind. 2–3
unabhaengige, zuverlaessige Quellen je Wert — RHS, University-Extension, ISTA,
Saatgut-Fachkataloge, POWO/WCVP fuer Taxonomie). Konsistent mit
`growing-phase-auditor` / `check-seed-data`.

**Eskalation (#308 D3):** Nutze den `deep-research`-Skill **nur bei hard cases** —
wenn Quellen duenn, widerspruechlich oder fehlend sind (z.B. selten kultivierte
Arten, uneinige Angaben zu Stratifikation/Dormanz). Nicht fuer Standardarten.

Recherchiere je Pflanze:
- **Lebensform**: `annual` / `biennial` / `perennial` (botanisch) — und ob sie in
  Kultur abweichend gefuehrt wird (z.B. Zwiebel botanisch biennial, als Gemuese einjaehrig).
- **Keimung & Aussaat**: Keimfenster; **Vorkultur** (Wochen vor letztem Frost) vs.
  **Direktsaat** (Tage nach letztem Frost / Monate); ggf. Stratifikation/Vernalisation.
- **Bluetefenster** (Monate, Mitteleuropa).
- **Erntefenster** (Monate).
- **Dormanz / Ueberwinterung**: Ruhephasen, Knollen-Einziehung, Ueberwinterungsmethode.
- **Frostempfindlichkeit**: `sensitive` / `moderate` / `hardy` / `very_hardy` (Eisheiligen-Bezug).

## Schritt 3: Ergebnis in den Steckbrief schreiben (NICHT Seed-YAML)

Trage die belegten Werte in die **bestehenden Steckbrief-Sektionen** ein (behalte
das `| Feld | Wert | KA-Feld |`-Format und die `KA-Feld`-Spalte bei, damit
`plant-info-to-seed-yaml` sie deterministisch uebertraegt):

| Steckbrief-Sektion | Felder (KA-Feld) |
|---|---|
| §1.1 Botanische Einordnung | Lebenszyklus (`lifecycle_configs.cycle_type`), Frostempfindlichkeit (`species.frost_sensitivity`), Dormanz/Vernalisation, `critical_day_length_hours` |
| §1.2 Aussaat- & Erntezeiten | `sowing_indoor_weeks_before_last_frost`, `sowing_outdoor_after_last_frost_days`, `direct_sow_months`, `harvest_months`, `bloom_months` |
| §2 Wachstumsphasen | `growth_phases` (Phasenfolge, Dauer, Terminal/Ernte) |
| §4.3 Ueberwinterung | Ueberwinterungs-/Dormanz-Profil (nur Outdoor/Mehrjaehrige) |

Regeln:
- **Nur belegte Werte** eintragen (≥2 Quellen). Nicht recherchierbare Werte mit
  `<!-- DATEN FEHLEN -->` markieren — **nicht raten**.
- Enum-Werte exakt in KA-Konvention (`sensitive`/`moderate`/`hardy`/`very_hardy`;
  `annual`/`biennial`/`perennial`; Monate als Zahlen 1–12).
- **Quellen zitieren** im Quellenverzeichnis des Steckbriefs (konsistent mit den
  bestehenden Konventionen).
- Vorhandene, bereits belegte Werte nur korrigieren, wenn die neue Quellenlage sie
  klar widerlegt (Konfidenz gesichert); sonst beibehalten und im Bericht vermerken.

## Schritt 4: Uebergabe

Gib eine kompakte Zusammenfassung: welche Steckbriefe aktualisiert wurden, welche
Lebenszyklus-Felder gesetzt/geaendert wurden, offene Luecken (`DATEN FEHLEN`), und
den naechsten Schritt:

> Naechster Schritt: `growing-phase-auditor` auf den Steckbrief zum Audit, dann
> `plant-info-to-seed-yaml` fuer die Seed-YAML, dann `seed-data-validator` +
> `check-seed-data` zur Validierung.

## Gotchas

- **`WebSearch` / `deep-research` sind deferred.** In diesem Repo erst per
  `ToolSearch` laden. `deep-research` nur bei echter hard case (D3).
- **Kultur- vs. botanischer Zyklus.** Viele Nutzpflanzen sind botanisch biennial/
  perennial, werden aber einjaehrig kultiviert — beide Angaben festhalten (z.B. Zwiebel).
- **`allium_cepa`** ist das End-to-End-Referenzbeispiel (#308): klarer biennial-als-
  Gemuese-einjaehrig-Zyklus mit definierten Aussaat-/Bluete-/Erntefenstern.

## Hard rules

- **NIEMALS** in `plant_info_*.yaml` schreiben — ausschliesslich in den Steckbrief.
- **NIEMALS** Lebenszyklus-Werte erfinden — recherchieren+zitieren oder als fehlend markieren.
- **Der Steckbrief ist die Quelle der Wahrheit** (#308 D1); die YAML wird daraus generiert.
- Frontmatter-Feldnamen/Identifier bleiben Englisch (Projekt-Konvention).
