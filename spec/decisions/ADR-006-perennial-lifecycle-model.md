# ADR-006: Modell des mehrjährigen Outdoor-Lebenszyklus (E1–E7)

## Status

**Proposed** — *Erstellt: 2026-07-12*
*Entscheider: nolte (Team-Gate für Epic #565)*

Dieses ADR hält die sieben Team-Entscheidungen **E1–E7** fest, die das Epic
[#565 — Perennial outdoor lifecycle] **vor** der Implementierung verlangt. Es
entscheidet, es implementiert nicht. Der auslösende Befund ist [#541]
(„strawberry phase flow looks wrong"); die Faktengrundlage ist der bereits
gemergte Konzept-Report
`spec/analysis/perennial-outdoor-lifecycle-modelling.md`. Nach Annahme wird der
Status auf **Accepted** gesetzt (Datum + Entscheider), und die verlinkten Specs
(REQ-003, REQ-047) tragen einen Changelog-Verweis auf dieses ADR.

## Context

Der Konzept-Report kommt zu einem klaren Verdikt: Das von #541 beobachtete
Symptom („Erdbeer-Phasenablauf sieht falsch aus") ist **real**, aber die
vermutete Ursache („Erdbeer-Stammdaten sind falsch") ist es **nicht**. Die
Erdbeer-Stammdaten gehören zu den besten im Bestand. Der Ablauf läuft nicht
rund, weil die **zyklische Perennierung (Dormanz → Neustart) auf Engine-Ebene
nie verdrahtet ist** — und das ist systematisch, kein Einzelfall.

Die Faktenlage aus dem Report (Belegstellen dort im Anhang):

1. **Zwei parallele Phasen-Modellierungswege** (Report Teil 2.1). *Weg A*
   (Legacy, per-Art-linear, `plant_info.yaml` `growth_phases` +
   `lifecycle_configs`) hat meist **keine** Terminalphase und **fast nie** einen
   `cycle_restart_phase_order`-Anker. *Weg B* (modern, Template-zyklisch,
   `lifecycles_outdoor.yaml` + `phase_sequences.yaml`) ist korrekt zyklisch
   (Terminal + Restart-Anker + `is_recurring`). **Erdbeere steht in Weg A** und
   ist in beiden Weg-B-Dateien abwesend.

2. **Der Zyklus-Restart-Motor ist in der Produktion nicht verdrahtet**
   (Report Teil 2.2). `CyclicLifecycleEngine.should_restart_cycle(...)` wird
   **nur in Unit-Tests** aufgerufen; die einzige automatische Fortschaltung
   (`check_auto_transitions`) ist rein regelbasiert, und der Seeder erzeugt für
   Weg-A-Arten **keine** Transition-Rules. Für die Erdbeere existieren weder
   Terminal noch Restart-Anker noch Transition-Rules → ihr REQ-003-Zyklus ist
   praktisch **inert**.

3. **Der einzige real rotierende Jahres-Zyklus (REQ-047 Season-State) ist
   entkoppelt** (Report Teil 2.3). Er ist **standort-, nicht artgetrieben**,
   liest weder `cycle_type` noch `cultivation_cycle_type`, läuft auf einem
   eigenen Phasen-Vokabular (`SeasonPhase`) und schaltet nur den **Pflege-Modus**
   — **nicht** die Wachstumsphase und **nicht** den Zyklus-Neustart.

4. **Die Einjährig-/Mehrjährig-Entscheidung ist 100 % art-fixiert**
   (Report Teil 3). `PlantInstance` hat **kein** Feld für `cycle_type`,
   `cultivation_cycle_type` oder `flowering_strategy`. Die von #541 benannte
   Spannung — „einjährig vs. mehrjährig ist oft eine **Kulturentscheidung pro
   Instanz**" (überwinterte Tomate, einjährig gezogene Erdbeere) — ist im
   Datenmodell nicht abbildbar.

**Constraints:**

- **#297-Entscheidung** (REQ-003 v2.7/2.8, `schemas/species.schema.yaml`):
  `cycle_type`/`flowering_strategy` sind **botanisch, Art-Ebene**;
  `cultivation_cycle_type` ist die **Kultur-Praxis-Achse**. Keine der hier
  getroffenen Entscheidungen darf #297 brechen.
- **ArangoDB schemalos** (ADR-001): additive Felder brauchen keinen Backfill;
  Datentransformationen laufen als versionierte Migration (ADR-005/NFR-016).
- **Globale Migrations-Queue** steht auf **v0019** → nächste freie Version
  **v0020**, Claim-at-Merge.
- **Migrations-vs-Seed-Trennung** (ADR-005): einmalige Daten-Transformationen
  sind Migrationen, idempotente Referenzdaten-Ladungen sind Seeds.

---

## Decision

Wir übernehmen die im Report empfohlene Richtung: **erst verdrahten, dann
überschreibbar machen, parallel Stammdaten angleichen** (Report §4.1). Die sieben
Team-Entscheidungen werden wie folgt getroffen.

### E1 — Instanz-Override: **Option C** (Art-Default + Instanz-Override + eine Auflösungs-Kaskade)

**Entscheidung.** Wir führen **Option C** ein: Die Art liefert den Default
(`cultivation_cycle_type` bzw. botanisches `cycle_type`), die Instanz **kann**
ihn überschreiben. Neu:

```python
class PlantInstance(...):
    cultivation_cycle_type: CycleType | None = None   # None = „wie Art"
```

Eine **einzige** zentrale Funktion `resolve_effective_cycle(instance, species)`
ist die **alleinige Quelle der Wahrheit** für alle Konsumenten. Kaskade:

```
Instanz.cultivation_cycle_type
  → Art.cultivation_cycle_type (Kultur-Praxis, #297)
    → Art.cycle_type (Botanik, #297)
```

**Begründung.** Trifft #541 direkt (der Gärtner entscheidet pro Pflanze), ist
additiv/`None`-defaultbar (non-breaking wie #297 selbst), koppelt sauber an #539
(„Ist-Zustand bei Anlage erfassen") und nutzt exakt das Kaskaden-Muster, das die
Codebasis bei Phasen-Auflösung (`PhaseSequence` → `LifecycleConfig`) und
`resolve_kc` bereits kennt. Eine einzige Auflösungsstelle minimiert die
Drift-Gefahr (Nachteil von Option B ohne zentrale Kaskade). Option A (bei
Art-Ebene bleiben) wird verworfen, weil sie #541 **nicht** löst.

**Sequenzierung — verbindlich:** Option C wird **NACH** dem Wiring-Fix (E2/E3,
WP-1..4) umgesetzt (WP-5). Der breitenwirksame Fix ist die zyklische
Verdrahtung; der Instanz-Override baut darauf auf und wäre auf einem inerten
Zyklus wirkungslos.

**Konsequenzen.** Alle Konsumenten (Phasen-Restart, REQ-047-Season-State,
Care-Reminder, Ernteplanung, Dashboard) müssen die Kaskade lesen statt
`species.cycle_type` (WP-8). Risiko widersprüchlicher Zustände (Instanz „annual",
Art hat nur zyklischen Ablauf) wird über E3 (Konfliktauflösung) und E6
(Fakultativ-Signal) entschärft.

### E2 — Ort der Zyklus-Wahrheit: **Konsolidierung auf Weg B** (Template-basiert), Weg A migrieren

**Entscheidung.** Zielbild ist **ein** Phasen-Modellierungsweg: der
**Template-basierte Weg B** (`phase_sequences.yaml`-Templates, gebunden über
`lifecycles_outdoor.yaml`-analoge Einträge). Weg A wird **migriert**, nicht
dauerhaft geduldet.

**Pragmatische Brücke.** Für Arten, die nicht sofort auf ein Template abgebildet
werden können, wird als **Interim** der minimale Laufzeit-Fix gesetzt
(Terminalphase markieren + `cycle_restart_phase_order` ergänzen), damit der
Restart-Pfad greift. Das Interim ist **kein** zweiter Dauer-Weg, sondern eine
Zwischenstufe auf dem Weg zur Template-Bindung.

**Begründung.** Weg B ist bereits nachweislich korrekt zyklisch (Terminal +
Restart-Anker, Report Teil 2.1, Forsythia/Rheum als Beleg). Weg A dauerhaft zu
dulden würde die zwei divergenten Modelle und die daraus folgende Drift
zementieren — genau die Ursache, die #541 offenlegt. Ein einziger Weg macht die
Laufzeit-Auflösung (`PhaseTransitionEngine._is_perennial_cycle_restart`
bevorzugt ohnehin Weg B) eindeutig.

**Konsequenzen.** Erdbeere + die ~90 Weg-A-Stauden werden auf Weg B überführt
(WP-2, Migration v0020, siehe E7). Der Seeder muss für die migrierten Arten
Transition-Rules erzeugen (heute tut er das nicht, Report Teil 2.2).

### E3 — Kopplung REQ-047 ↔ REQ-003: **Ja — Season-State treibt die Wachstumsphase, Instanz-Kaskade löst Konflikte**

**Entscheidung.** Der (standortweite) **Season-State treibt die
Instanz-Wachstumsphasen**. Die entkoppelten Zyklen werden verbunden:

- `SeasonState.winter_dormancy` → Wachstumsphasen-Übergang der betroffenen
  Instanzen **nach `dormancy`**.
- `SeasonState.pre_spring` → **Zyklus-Neustart** (Restart-Anker aus E2/E4).

**Konfliktauflösung.** Der Season-State ist ein **Standort-Signal**; ob er eine
konkrete Instanz treibt, **gated die `resolve_effective_cycle`-Kaskade aus E1**:

- Effektiv **perennial/biennial** → Season-State treibt Dormanz + Neustart.
- Effektiv **annual** (Instanz-Override an mehrjährigem Standort) → die Instanz
  wird **nicht** in Dormanz/Neustart gezwungen; sie durchläuft ihren Zyklus bis
  zum Terminal (`completed`/`dead`) normal. Der einjährige Nutzer-Wille schlägt
  das Standort-Signal.

**Begründung.** Löst die im Report benannte Entkopplung (Teil 2.3): heute liest
REQ-047 keinen Art-/Instanz-Zyklus. Genau hier entsteht die fehlende Kopplung —
aber **instanz-gegatet**, damit „annual instance an perennial location"
deterministisch aufgelöst ist. Der Season-State bleibt der klima-/kalendergetriebene
Taktgeber; die Instanz-Kaskade bleibt die Wahrheit über die Zyklus-Natur.

**Konsequenzen.** Der Season-State-Übergang bindet an den
Wachstumsphasen-Übergang (WP-4). Das Season-Vokabular (`SeasonPhase`) und das
Wachstumsphasen-Vokabular (`PhaseType`) bleiben getrennt, werden aber über die
Kopplung synchronisiert. Der bestehende Pflege-Modus-Effekt
(`dormancy_care_activator`) bleibt und wird um den Phasen-Effekt ergänzt.

### E4 — `cycle_restart_phase_order`-Semantik für Erdbeere: **Restart auf `vegetative` (Skip `germination`); `germination` in `establishment` + `sprouting` splitten**

**Entscheidung.**

1. Der **Restart-Anker springt auf die vegetative Phase**, nicht auf
   `germination`. Für die Erdbeere ist der jährliche Wiedereinstieg
   `dormancy → sprouting → vegetative`, nicht „Keimung".
2. Die heutige `germination`-Phase wird konzeptionell **gesplittet**:
   - **`establishment`** — einmalige Etablierung, `is_recurring: false`, nur im
     ersten Zyklus durchlaufen (Keimung **oder** Ausläufer-Anwachsen).
   - **`sprouting`** — zyklischer Wiedereinstieg nach der Dormanz,
     `is_recurring: true`, Ziel des Restart-Ankers.

**Begründung.** Report Teil 1.3 Punkt 3: „Keimung" als **wiederkehrender**
Einstieg ist für eine praktisch ausschließlich vegetativ (über Ausläufer)
vermehrte Staude botanisch schief. Der Steckbrief kombiniert bereits sprachlich
„Keimung/**Etablierung**"; das Modell muss „einmalige Etablierung" und
„jährlicher Wiedereinstieg" trennen. Das ist zugleich das **generische Muster**
für vegetativ vermehrte Perennials, nicht nur für die Erdbeere.

**Konsequenzen.** Das Weg-B-Template `perennial_standard` (bzw. eine
runner-vermehrte Variante) bekommt die `establishment`/`sprouting`-Trennung; die
Migration (E7/WP-2) setzt den Restart-Anker auf `sprouting`/`vegetative`. Der
`PhaseType`-Enum ist bereits auf 53 Werte erweitert (REQ-003 v2.9) — zu prüfen,
ob `establishment`/`sprouting` schon enthalten sind, sonst additiv ergänzen (WP-3).

### E5 — `flowering_strategy`-Ablageort: **In `species.yaml` `lifecycle_overrides` belassen + Konsistenz-Check**

**Entscheidung.** `flowering_strategy` (und die orthogonalen Achsen
`growth_determinacy`, `cultivation_cycle_type`) bleiben in **`species.yaml`
`lifecycle_overrides`** — dem laut `schemas/species.schema.yaml` deklarierten
**„authoritative source, keyed by scientific_name"**. Sie werden **nicht** in
`lifecycle_configs` zusammengeführt. Ergänzt wird ein **Seed-Validierungs-Check**,
der für jede perennierende/monokarpe Art die Präsenz und Konsistenz von
`flowering_strategy` prüft.

**Begründung.** Das Zusammenführen in `lifecycle_configs` würde eine **zweite
Autorität** für dasselbe Feld schaffen und damit #297 und die Schema-Autorität
brechen — genau die Drift, die wir an anderer Stelle (E2) gerade beseitigen. Der
Report (Teil 1.3 Punkt 2) benennt korrekt, dass die Zwei-Datei-Verteilung
Konsistenzprüfungen erschwert; die richtige Antwort ist ein **Check**, nicht eine
Verlagerung, die die Schema-Autorität aufweicht.

**Konsequenzen.** Ein neuer Check in der Seed-Validierung
(`seed-data-validator`-nah), der Widersprüche (z. B. `cycle_type: perennial` ohne
`flowering_strategy`) als Fehler meldet (WP-6). Die Erdbeer-Nebennüsse aus dem
Report (`base_temp`-, `allelopathy_score`-Drift Steckbrief↔`species.yaml`) werden
im Stammdaten-Sweep (WP-7) angeglichen.

### E6 — Fakultative Klassifikation: **Zwei-Achsen-Modell für Werte + explizites `cultivation_flexible`-Flag für die Fähigkeit**

**Entscheidung.** Die beiden bestehenden Achsen bleiben die **Werte-Quelle**:
`cycle_type` (botanisch) liefert die Lebensdauer, `cultivation_cycle_type` (falls
gesetzt) den **sinnvollen Default** der Kulturpraxis. Zusätzlich wird ein
**explizites, additives Boolean-Flag** auf Art-Ebene eingeführt:

```yaml
cultivation_flexible: true    # Art kann fakultativ annual ODER perennial gezogen werden
```

Default `false`. Das Flag drückt die **Fähigkeit** „kann beides" aus (nicht den
Wert); der Default für die Instanz-Wahl (E1) bleibt `cultivation_cycle_type`
bzw. `cycle_type`.

**Begründung.** Die zwei Achsen genügen, um einen **sinnvollen Default**
auszudrücken — aber **nicht**, um „diese Art ist genuin fakultativ" von „Override
technisch für alle erlaubt" zu unterscheiden. Genau diese Unterscheidung braucht
die UI aus E1/#539: Bei einer fakultativen Art (Tomate, Erdbeere) soll die
Instanz-Wahl **prominent** angeboten werden, mit vorbelegtem Default; bei einer
eindeutig einjährigen Art nicht. Ein einzelnes Boolean ist minimal, additiv und
non-breaking — kein neues Enum, keine Werte-Duplikation.

**Konsequenzen.** `cultivation_flexible` wird im Seed-Schema ergänzt und für die
bekannten fakultativen Arten gepflegt (WP-6). Die FE-Anlage-Maske (E1/#539) liest
das Flag, um die Zyklus-Wahl zu gaten/prominent zu machen.

### E7 — Migrations-Scope: **Additives Instanz-Feld migrationsfrei; Weg-A-Backfill als eine getrackte Migration v0020**

**Entscheidung.** Zweigeteilt entlang der ADR-005-Trennung:

1. **Instanz-Override-Feld (E1) — keine Migration.** `cultivation_cycle_type:
   CycleType | None = None` ist additiv, `None`-defaultbar; ArangoDB ist
   schemalos → **kein Backfill nötig** (Präzedenz ADR-004 §5). Bestehende
   Instanzen erben `None` = „wie Art".
2. **Weg-A→Weg-B-Backfill (E2/E4) — eine getrackte Migration.** Das Setzen von
   Terminalphase, Restart-Anker und Template-Bindung für Erdbeere + die ~90
   Weg-A-Stauden ist eine **Daten-Transformation** → einmalige, versionierte
   Migration. Sie **claimt `v0020`** aus der globalen Queue (Claim-at-Merge;
   Queue steht auf v0019).

**Begründung.** Der Report (Teil 3.2 Option C) hält fest, dass das Instanz-Feld
keinen Backfill braucht, aber „eine Migrations-Version zum Dokumentieren"
nutzt. Der breitenwirksame Fix (Report Teil 2.4: „keine einzelne Datenkorrektur")
ist die ~90-Arten-Angleichung — und **die** ist eine echte Transformation, die
nach ADR-005/NFR-016 getrackt (genau einmal, geordnet) laufen muss. Beides in
**einer** Migration v0020 zu bündeln hält die Queue schlank und dokumentiert den
Stand.

**Konsequenzen.** `v0020` wird beim Merge geclaimt (nicht vorher, um
Queue-Konflikte zu vermeiden). Die 16 `dormancy_required`-ohne-Dormanzphase-Fälle
und die fehlenden Kräuter-/Spargel-Modelle (Report Teil 2.4) sind
**Stammdaten-Sweep** (Seed-Ebene, WP-7) — sie fließen über den idempotenten
Seed-Upsert, nicht zwingend über die Migration.

---

## Umsetzungssequenz (WP-1..8, abgeleitet aus Report §4.1)

Der Report §4.1 gibt die Richtung in drei Blöcken vor („erst verdrahten, dann
überschreibbar, parallel Sweep"). Für die Implementierung nach dem ADR-Gate
werden daraus acht Arbeitspakete abgeleitet:

| WP | Inhalt | Entscheidung |
|----|--------|--------------|
| **WP-1** | Restart-Motor verdrahten: `should_restart_cycle` / Restart-Pfad in `check_auto_transitions` aufrufen; Transition-Rules für Weg-A-Arten erzeugen | E2 |
| **WP-2** | Erdbeere + ~90 Weg-A-Stauden auf Weg B überführen (Terminal, Restart-Anker, Template-Bindung) — Migration **v0020** | E2, E4, E7 |
| **WP-3** | `establishment`/`sprouting`-Split; `PhaseType`-Enum ggf. additiv ergänzen; runner-Template | E4 |
| **WP-4** | REQ-047 ↔ REQ-003 koppeln: Season-State treibt Wachstumsphase (instanz-gegatet) | E3 |
| **WP-5** | Instanz-Override `PlantInstance.cultivation_cycle_type` + `resolve_effective_cycle`-Kaskade; an #539 ankoppeln | E1 |
| **WP-6** | `cultivation_flexible`-Flag + Konsistenz-Check für `flowering_strategy` | E5, E6 |
| **WP-7** | Stammdaten-Sweep: 16 Dormanz-Inkonsistenzen, Kräuter/Spargel-Phasenmodelle, Erdbeer-Nebennüsse (`base_temp`, `allelopathy_score`, Benennung) | E4, E5 |
| **WP-8** | Konsumenten-Umstellung: Phasen-Restart, Season-State, Care-Reminder, Ernte, Dashboard lesen die Kaskade statt `species.cycle_type` | E1, E3 |

**Reihenfolge-Invariante:** WP-1..4 (Verdrahtung) **vor** WP-5/WP-8
(Instanz-Override) — der Override baut auf einem lauffähigen Zyklus auf (E1
Sequenzierung). WP-6/WP-7 laufen parallel.

## Alternatives Considered

- **E1 Option A (nur Art-Ebene).** Verworfen: löst #541 nicht — der Gärtner, der
  *diese* Tomate überwintert oder *diese* Erdbeere einjährig zieht, kann es nicht
  abbilden (Report Teil 3.2).
- **E1 Option B (Instanz-Override ohne zentrale Kaskade).** Verworfen zugunsten C:
  ohne eine einzige `resolve_effective_cycle`-Stelle droht Konsumenten-Drift.
- **E2 Weg A dauerhaft dulden.** Verworfen: zementiert zwei divergente Modelle und
  die #541-Ursache; nur als Interim-Brücke (Terminal/Restart-Anker) bis zur
  Template-Bindung akzeptiert.
- **E5 `flowering_strategy` in `lifecycle_configs` mergen.** Verworfen: schafft
  eine zweite Autorität, bricht #297/Schema-Autorität.
- **E6 kein Flag, nur zwei Achsen.** Verworfen: die zwei Achsen liefern den Wert,
  aber nicht die für die UI nötige Fähigkeits-Aussage „genuin fakultativ".
- **E7 Weg-A-Backfill als reiner Seed (keine Migration).** Verworfen für den
  Transformationsteil: ADR-005/NFR-016 verlangt getrackte, einmalige Ausführung
  für Daten-Transformationen; der reine Stammdaten-Sweep (WP-7) bleibt Seed.

## Consequences

- **Positiv:** #541 ist an der Wurzel adressiert (Verdrahtung **und**
  Instanz-Entscheidung); es gibt einen einzigen Zyklus-Weg (Weg B) und eine
  einzige Zyklus-Wahrheit (`resolve_effective_cycle`); REQ-047 und REQ-003 sind
  gekoppelt statt entkoppelt; die #297-Schema-Autorität bleibt unangetastet.
- **Negativ / Kosten:** Breite Konsumenten-Umstellung (WP-8); eine
  Backfill-Migration über ~90 Arten (v0020); zwei neue Art-Felder-/Flags
  (`cultivation_flexible`) plus ein Instanz-Feld; zusätzlicher Seed-Konsistenz-Check.
- **Folgemaßnahmen:** REQ-003 und REQ-047 erhalten einen Changelog-Verweis auf
  dieses ADR (bereits in diesem PR additiv ergänzt). Die WP-1..8-Umsetzung folgt
  als separate Arbeit im Epic #565 (dieses ADR ist das vorgelagerte
  Entscheidungs-Gate, **keine** Implementierung).

## References

- `spec/analysis/perennial-outdoor-lifecycle-modelling.md` (Konzept-Report,
  Faktengrundlage; Teil 2.1–2.4, Teil 3, §4.1–4.3)
- Issue #565 (Epic: perennial outdoor lifecycle — dieses ADR ist das E1–E7-Gate)
- Issue #541 (auslösender Befund: „strawberry phase flow looks wrong")
- Issue #539 (Ist-Zustand bei Anlage erfassen — Ankopplung Instanz-Override, E1)
- REQ-003 Phänologische Phasensteuerung (Zyklus-Restart, PhaseType, #297-Achsen)
- REQ-047 Saison- & Überwinterungs-Automatik (Season-State, Kopplung E3)
- ADR-001 ArangoDB als Multi-Modell-Datenbank (schemalose Persistenz, E7)
- ADR-004 Vermehrung als strukturierte per-Methode-Objekte (additiv-schemalos-Präzedenz, E7)
- ADR-005 Versioniertes Datenbank-Migrations-Framework (Migration-vs-Seed-Trennung, v0020, E7)
- #297-Entscheidung (REQ-003 v2.7/2.8, `schemas/species.schema.yaml`: botanisch vs. Kultur)
