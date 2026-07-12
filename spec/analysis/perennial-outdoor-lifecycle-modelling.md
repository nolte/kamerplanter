# Analyse & Konzept: Mehrjährige Outdoor-Lebenszyklen (Erdbeere → systematisches Modell)

**Erstellt von:** Perennial-Outdoor-Lifecycle-Konzept (Claude Code, Opus 4.8)
**Datum:** 2026-07-12
**Issue:** #541 — „Perennial outdoor lifecycle: strawberry phase flow looks wrong; clarify species-vs-user annual/perennial modelling"
**Typ:** Untersuchung + Konzept (KEINE Code-Änderung). Der konkrete Umsetzungsplan (Stammdaten-Korrektur,
Modell-/Engine-Änderung, Migration, Tests) folgt als separater Schritt.
**Methode:** Quellcode-Audit der Lifecycle-/Phasen-Engines, Diff Steckbrief ↔ Seed-YAML für *Fragaria x ananassa*,
scriptbasierter Survey aller 113 mehrjährigen/zweijährigen `lifecycle_configs` über 10 Seed-Dateien, Trace der
Laufzeit-Konsumenten von `should_restart_cycle` / `cycle_restart_phase_order`, Abgleich mit REQ-047 (Season-State)
und der #297-Lifecycle-Override-Entscheidung.

---

## Kernaussage (Verdict)

Das von #541 beobachtete Symptom ist **real**, aber die vermutete Ursache („Erdbeer-Stammdaten sind falsch") ist es
**nicht**. Die Erdbeer-Stammdaten gehören zu den **besten** im Datenbestand: `cycle_type: perennial`,
`dormancy_required: true`, eine eigene `dormancy`-Phase im Phasenablauf und `flowering_strategy: polycarpic`. Der
Erdbeer-Ablauf „läuft nicht rund", weil die **zyklische Rückkehr (Dormanz → Neustart) auf Engine-Ebene für sie nie
verdrahtet ist** — und das ist **kein Erdbeer-Einzelfall, sondern systematisch**: Es existieren zwei parallele
Phasen-Modellierungswege (ein moderner, korrekt zyklischer und ein Legacy-linearer), Erdbeere steht im falschen,
und die eigentliche Zyklus-Restart-Logik (`CyclicLifecycleEngine.should_restart_cycle`) wird in der Produktion
**überhaupt nicht aufgerufen**. Zusätzlich ist der einzige *tatsächlich* jährlich rotierende Zyklus (REQ-047
Season-State) **standort-, nicht artgetrieben** und mit der REQ-003-Phasenmaschine **nicht gekoppelt**.

Die von #541 aufgeworfene tiefere Frage — „einjährig vs. mehrjährig ist oft eine **Kulturentscheidung pro
Pflanzeninstanz**" — trifft eine echte Architekturlücke: Das Datenmodell kennt für diese Entscheidung heute
ausschließlich die **Art-Ebene** (`cultivation_cycle_type` in `species.yaml`), es gibt **keinen Instanz-Override**.

---

## Teil 1 — Erdbeer-Stammdaten-Audit

### 1.1 Was korrekt ist (Steckbrief `spec/knowledge/plants/fragaria_x_ananassa.md`)

Der Steckbrief ist fachlich sauber und vollständig:

| Aspekt | Wert | Beleg |
|---|---|---|
| `cycle_type` | perennial | `fragaria_x_ananassa.md:22` |
| `flowering_strategy` | polycarpic (mehrjährig wiederholt blühend) | `:23` |
| Dormanz erforderlich | true (Winterruhe/Semi-Dormanz) | `:37` |
| Vernalisation | true, 8–45 d (200–1080 h < 7 °C) | `:38-39` |
| Phasen inkl. Winterruhe | 6 Phasen: germination → vegetative → flowering → ripening → recovery → **dormancy** | `:152-161` |
| Zyklus-Hinweis | „zyklischer Phasenverlauf … Nach der Winterruhe beginnt der Zyklus erneut bei der vegetativen Phase" | `:161` |
| Übergang Winterruhe→Vegetativ | conditional (Vernalisation abgeschlossen + T > 10 °C) | `:338` |

Der Steckbrief beschreibt also **explizit einen zyklischen Perennierungs-Ablauf mit Neustart bei der vegetativen
Phase** — genau das, was #541 als fehlend vermutet. Er benennt sogar korrekt, dass Samenvermehrung bei der
Hybridart untypisch ist und Ausläufer (Runner) der Standard sind (`:70, :79, §1.8 :139-144`).

### 1.2 Was in der generierten Seed-YAML korrekt ist

Die aus dem Steckbrief generierte Seed-Struktur ist überwiegend korrekt:

- `lifecycle_configs["Fragaria x ananassa"]`: `cycle_type: perennial`, `dormancy_required: true`,
  `vernalization_required: true`, `vernalization_min_days: 30`, `critical_day_length_hours: 12`
  (`src/backend/app/migrations/seed_data/plant_info.yaml:501-508`).
- `growth_phases["Fragaria x ananassa"]`: alle 6 Phasen inkl. `dormancy` (`sequence_order: 6`)
  (`plant_info.yaml:1044-1203`).
- `species.yaml` `lifecycle_overrides`: `Fragaria x ananassa: { flowering_strategy: polycarpic }`
  (`src/backend/app/migrations/seed_data/species.yaml:2677`).
- Überwinterungs-Profil vorhanden (`overwintering_profiles.yaml:716`), Care-Style `outdoor_perennial`
  (Steckbrief `:416`).

### 1.3 Was für die Erdbeere tatsächlich falsch/unvollständig ist

Es sind **wenige, gezielte** Defekte — keiner davon „falscher `cycle_type`":

1. **Kein terminaler Phasenabschluss + kein Restart-Anker.** Keine der 6 Erdbeer-Phasen ist `is_terminal: true`,
   und `lifecycle_configs` setzt **kein** `cycle_restart_phase_order` (`plant_info.yaml:501-508` enthält das Feld
   nicht). Die Phasenkette endet damit bei `dormancy` in einer Sackgasse: kein Vorwärtspfad, kein definierter
   Rücksprung. → Der im Steckbrief beschriebene Neustart „Winterruhe → Vegetativ" ist in den Daten **nicht
   ausdrückbar** (Details siehe Teil 2).

2. **`flowering_strategy` an zwei Orten / getrennt von `lifecycle_configs`.** Der Wert `polycarpic` steht nur im
   separaten `species.yaml`-Block `lifecycle_overrides` (`species.yaml:2677`), nicht bei den übrigen
   Lifecycle-Feldern in `plant_info.yaml`. Das ist bewusst so (Schema-Autorität: `schemas/species.schema.yaml`
   deklariert `lifecycle_overrides` als „authoritative source … keyed by scientific_name"), aber es verteilt den
   Lebenszyklus einer Art über zwei Dateien und erschwert Konsistenzprüfungen.

3. **`germination` als erste Phase einer runner-vermehrten Staude.** `sequence_order: 1` ist
   `germination`/„Keimung/Etablierung" (`plant_info.yaml:1045`). Für eine praktisch ausschließlich vegetativ
   (über Ausläufer) vermehrte Art ist „Keimung" als **wiederkehrender** Zyklus-Einstieg botanisch schief; korrekt
   ist eine einmalige Etablierung, und der **jährliche** Zyklus-Einstieg muss `dormancy`/`sprouting`/`vegetative`
   sein, nicht `germination`. Der Steckbrief kombiniert das bereits sprachlich zu „Keimung/**Etablierung**", das
   Modell trennt „einmalige Etablierung" und „jährlicher Wiedereinstieg" aber nicht.

4. **`base_temp`-Drift Steckbrief ↔ `species.yaml`.** Steckbrief nennt GDD-Basis 3 °C (Phänologie Blüte-Frucht)
   mit Blattproduktions-Näherung 7 °C (`:35`); `species.yaml:2089` führt `base_temp: 5.0`. Kein Fehler, aber eine
   dokumentierte Ungenauigkeit; die Übergangstabelle im Steckbrief rechnet ihrerseits mit „Basis 5 °C" (`:334`).

5. **`allelopathy_score`-Drift.** Steckbrief `-0.4` (`:29`), `species.yaml:2092` `0.1`. Nebenbefund, für #541 nicht
   relevant, aber ein Steckbrief↔Seed-Widerspruch.

**Fazit Teil 1:** Die Erdbeere ist kein Stammdaten-Fehler im engeren Sinn. Ihr Ablauf „sieht falsch aus", weil das
**Modell den zyklischen Wiedereinstieg für sie nicht verdrahtet** (Punkt 1) — plus zwei kleinere Datennüsse
(Punkt 2/3).

---

## Teil 2 — Systematische Gap-Analyse

### 2.1 Es gibt zwei parallele Phasen-Modellierungswege

| | Weg A — **Legacy, per-Art-linear** | Weg B — **Modern, Template-zyklisch** |
|---|---|---|
| Ablageort | `plant_info.yaml` `growth_phases` (+ `lifecycle_configs`) | `lifecycles_outdoor.yaml` (38 Arten) + `phase_sequences.yaml` (7 Templates) |
| Terminaler Abschluss | meist **fehlt** (`is_terminal: false`) | vorhanden (`senescence` = `is_terminal: true`) |
| Restart-Anker | `cycle_restart_phase_order` **fast nie gesetzt** | `cycle_restart_phase_order: 1` (30×) bzw. `cycle_restart_entry_order: 0` (7 Templates) |
| `is_recurring`-Flags | nicht genutzt | genutzt |
| Beispiel | **Fragaria x ananassa** | Forsythia, Rheum (Rhabarber), Rubus, Vaccinium, Vitis … |

Weg B ist **korrekt zyklisch**. Forsythia z. B.: `cycle_type: perennial`, `cycle_restart_phase_order: 1`,
`phase_sequence: "perennial_standard"`, Phasen `dormancy → sprouting → vegetative → flowering → senescence(terminal)`
(`lifecycles_outdoor.yaml:13-62`). Das Template `perennial_standard` schließt mit `senescence (is_terminal: true)`
und `cycle_restart_entry_order: 0` (`phase_sequences.yaml:129-167`). Erdbeere ist in **beiden** modernen Dateien
**abwesend** (Grep leer) und steckt in Weg A.

Die Laufzeit-Auflösung bevorzugt Weg B: `PhaseTransitionEngine._is_perennial_cycle_restart` versucht zuerst die
`PhaseSequence` (`cycle_restart_entry_order`), fällt sonst auf `LifecycleConfig.cycle_restart_phase_order` zurück
(`src/backend/app/domain/engines/phase_transition_engine.py:42-65`; `phase_service.py:112`). Für die Erdbeere sind
**beide Anker leer und keine Phase ist terminal**, also greift der Restart-Pfad nie (die Vorbedingung
`current_phase.is_terminal` in `phase_transition_engine.py:39` ist nie erfüllt).

### 2.2 Der Zyklus-Restart-Motor ist in der Produktion gar nicht verdrahtet

`CyclicLifecycleEngine.should_restart_cycle(...)` (`src/backend/app/domain/engines/cyclic_lifecycle_engine.py:88-106`)
entscheidet sauber, ob eine Staude nach der Terminalphase neu startet — **wird aber ausschließlich in Unit-Tests
aufgerufen**, nirgends in `src/backend/app/**` (Grep: nur `tests/unit/domain/engines/…`). Die einzige automatische
Phasen-Fortschaltung läuft in `tasks/phase_transitions.py::check_auto_transitions` und ist **rein regelbasiert**
(`get_transition_rules`) plus die E4-Unterdrückung `stays_in_productive_phase`
(`phase_transitions.py:104-157`). Der Seeder `seed_plant_info.py` erzeugt jedoch **keine `transition_rules`**
(nur species/lifecycle_configs/growth_phases/cultivars/companion/IPM). Für die Erdbeere existieren also weder
Transition-Rules noch ein Terminal noch ein Restart-Anker → ihr REQ-003-Lebenszyklus ist praktisch **inert**
(das bekannte „implementiert-aber-inert"-Muster aus der REQ-003-Historie).

### 2.3 Der einzige real rotierende Jahres-Zyklus (REQ-047) ist entkoppelt

REQ-047 besitzt eine **eigene**, funktionierende zyklische Zustandsmaschine:
`growing → pre_winter → winter_dormancy → pre_spring → growing` (`domain/engines/season_state_engine.py:44-51`),
klima-/kalendergetrieben mit Hysterese. Aber:

- Sie ist **standort-, nicht artgetrieben**: `season_state_service.py:80` gated auf `site.type`, nicht auf Art.
- Sie liest **weder** `cycle_type` **noch** `cultivation_cycle_type` **noch** `dormancy_required` (Grep in Engine,
  Resolver, Service, Materializer = leer).
- Sie läuft auf einem **anderen Phasen-Vokabular** (`SeasonPhase`) als die REQ-003-Wachstumsphasen.
- Ihr einziger Instanz-Effekt ist der **Pflege-Modus** (`dormancy_care_activator.py:33-70` schaltet `CareProfile`
  in Dormanz-Bewässerung) und die Überwinterungs-Materialisierung — sie schaltet die **Wachstumsphase nicht** auf
  `dormancy` und löst den Wachstumsphasen-**Neustart nicht** aus.

Der „mehrjährige Zyklus" existiert also — aber im **falschen Subsystem** (Pflege/Überwinterung), getrennt von der
biologischen Phasensteuerung, die #541 meint.

### 2.4 Betroffene Arten — Erdbeere ist die Spitze, nicht der Einzelfall

Survey über 113 mehrjährige/zweijährige `lifecycle_configs` (Script, 10 Seed-Dateien):

- **~90 polykarpe Stauden** in Weg A haben eine `dormancy`-Phase, aber **keine Terminalphase und keinen
  Restart-Anker** → derselbe inerte Zustand wie die Erdbeere (u. a. alle Zimmerpflanzen-Perennials in
  `plant_info_indoor_*`).
- **16 Arten deklarieren `dormancy_required: true`, haben aber keine literale `dormancy`-Phase.** Davon 11 Outdoor
  ganz ohne `growth_phases` (u. a. **Asparagus officinalis**, `plant_info_outdoor_1.yaml`); 5 Indoor nutzen
  abweichende Namen (`winter_rest`/`cool_rest`/`rest_phase`: Ardisia, Begonia, Clivia, Dendrobium, Hippeastrum).
- **Perennierende Kräuter** (Lavendel, Rosmarin, Salbei, Thymian, Minze) und **Spargel** haben **überhaupt kein**
  Phasen-/Dormanz-Modell — weder in `plant_info` noch in `lifecycles_outdoor` (nur `species`/`enrichment`-Einträge).
  `plant_info_outdoor_2.yaml` (die Obststrauch-/Kräuter-Datei) hat **weder `lifecycle_configs` noch `growth_phases`**.
- Fruchtsträucher/Obst (Rhabarber, Him-/Brombeere, Heidelbeere, Wein, Johannis-/Stachelbeere) sind dagegen in
  Weg B korrekt zyklisch modelliert (`lifecycles_outdoor.yaml`).

**Verdikt:** Systematisch. Der Fix ist **keine einzelne Datenkorrektur**, sondern (a) eine Modell-/Engine-Verdrahtung
des Perennierungs-Neustarts und (b) eine breite Stammdaten-Angleichung (Erdbeere + ~90 Weg-A-Stauden in den
zyklischen Pfad überführen, 16 Dormanz-Inkonsistenzen bereinigen, fehlende Kräuter/Spargel-Modelle ergänzen).

### 2.5 Warum das Vorgänger-Audit den Gap nicht sah

`spec/analysis/lifecycle-flow-completeness-audit.md` (2026-07-02) erklärte die Perennial-Archetypen für „vollständig
und hochwertig modelliert" (`:13-14`) — prüfte aber die **Phasen-Vokabular-Vollständigkeit** (welche Phasennamen
existieren, D8-Rollen-Mapping), **nicht die Ende-zu-Ende-Laufzeit-Verdrahtung** (Terminal + Restart + Trigger-Rules +
`should_restart_cycle`-Aufruf). Fragaria/Spargel/Kräuter kommen dort nicht vor (Grep leer). #541 legt genau die
Achse offen, die jenes Audit nicht adressierte.

---

## Teil 3 — Die Kern-Modellierungsspannung: Art-Merkmal vs. Instanz-Entscheidung

### 3.1 Ist-Zustand (nach #297)

Die #297-Entscheidung (dokumentiert nicht per Issue-Token, sondern in `spec/req/REQ-003_Phasensteuerung.md:19-20`
Changelog v2.7/2.8 sowie `schemas/species.schema.yaml`) trennt sauber:

- `cycle_type` = **botanische** Lebensdauer (Art-Ebene, `LifecycleConfig`, `domain/models/lifecycle.py:43`).
- `cultivation_cycle_type` = **praktizierte** Lebensdauer, wenn abweichend (Art-Ebene, optional, `lifecycle.py:47-51`).
- `flowering_strategy`, `growth_determinacy` = orthogonale Reproduktions-/Wuchsachsen (Art-Ebene, `lifecycle.py:53-63`).

Diese Overrides sind heute **ausschließlich Art-Ebene**, gepflegt in `species.yaml` `lifecycle_overrides`
(`species.yaml:2600-2739`): `cultivation_cycle_type` für 14 Arten (z. B. Tomate/Chili/Aubergine `annual`,
Sellerie/Karotte `biennial`), `flowering_strategy` für ~130 Arten, `growth_determinacy` für 3 (Tomate, Paprika,
Gurke = `indeterminate`). **`max_seasons` und `first_bearing_year` sind im Seed-Bestand gar nicht gepflegt.**

Entscheidend: `PlantInstance` (`domain/models/plant_instance.py`) hat **kein** Feld für `cycle_type`,
`cultivation_cycle_type` oder `flowering_strategy` — nur `current_phase_key`, `chill_days_accumulated`,
`termination_type`, `reversion_count` (`:35-58`). Die Einjährig-/Mehrjährig-Entscheidung ist damit **100 %
art-fixiert**. Genau das ist die von #541 benannte Spannung: Tomate/Chili (botanisch perennial, meist einjährig, aber
überwinterbar) und Erdbeere (perennial, oft nach 2–3 Jahren erneuert oder einjährig gezogen) sind **pro Instanz** eine
Kulturentscheidung des Gärtners.

### 3.2 Design-Optionen

**Option A — Bei Art-Ebene bleiben (`cultivation_cycle_type` als „sinnvoller Default").**
- *Pro:* keine Migration; #297 unangetastet; RAG-/Seed-Konsistenz bleibt; die 14 bereits gepflegten Overrides decken
  die häufigsten „einjährig kultivierten Perennials" ab.
- *Contra:* löst #541 **nicht** — der Gärtner, der *diese* Tomate überwintert oder *diese* Erdbeere einjährig zieht,
  kann es nicht abbilden; die App zeigt weiter den art-typischen Ablauf.
- *Migration:* keine. *REQ-047/003:* unverändert.

**Option B — Instanz-Override einführen (`PlantInstance.cultivation_cycle_type: CycleType | None`).**
- *Pro:* trifft #541 direkt; der Gärtner entscheidet pro Pflanze; koppelt sauber an #539 („Ist-Zustand bei Anlage
  erfassen") — die Wahl fällt bei der Anlage. Additiv/`None`-defaultbar (non-breaking wie #297 selbst).
- *Contra:* neue Auflösungs-Kaskade nötig (Instanz > Art-`cultivation_cycle_type` > botanisches `cycle_type`); alle
  Konsumenten (Phasen-Restart, REQ-047-Season-State, Care-Reminder, Ernteplanung) müssen die Kaskade lesen statt
  `species.cycle_type`; Test-/Doku-Aufwand; Risiko widersprüchlicher Zustände (Instanz „annual", aber Art hat nur
  einen zyklischen Phasenablauf).
- *Migration:* additives Instanz-Feld (Default `None` = „wie Art"); ArangoDB schemalos → kein Backfill zwingend;
  eine Migrations-Version zum Dokumentieren.
- *REQ-047/003:* Season-State und Zyklus-Restart müssten die **effektive** Kaskade abfragen (heute liest REQ-047 gar
  keinen Art-Zyklus, Teil 2.3 — hier entstünde die Kopplung, die heute fehlt).

**Option C — Hybrid: Art-Default + Instanz-Override (empfohlen, siehe Teil 4).**
- Kombination: Art liefert den Default (`cultivation_cycle_type` bzw. `cycle_type`), Instanz **kann** ihn
  überschreiben; eine zentrale `resolve_effective_cycle(instance, species)`-Funktion ist die *einzige* Quelle der
  Wahrheit für alle Konsumenten. Genau die vorhandene botanisch-vs.-Kultur-Doppelung (`lifecycle.py:44-51`) wird um
  eine dritte, feinste Ebene (Instanz) erweitert — dasselbe Kaskaden-Muster, das die Codebasis bei
  Phasen-Auflösung (`PhaseSequence` → `LifecycleConfig`) und `resolve_kc` (Phase → … ) bereits nutzt.
- *Pro/Contra/Migration:* wie B, aber mit expliziter Default-Semantik und einer einzigen Auflösungsstelle → geringste
  Drift-Gefahr.

### 3.3 Verhältnis zu #297

Keine der Optionen bricht #297. #297 sagt „`cycle_type`/`flowering_strategy` **botanisch**, Art-Ebene". Ein
Instanz-`cultivation_cycle_type` ist die **Kultur-Praxis-Achse**, die #297 bereits konzeptionell von der Botanik
getrennt hat — Option C zieht diese Trennung nur konsequent bis zur Instanz durch. `cycle_type` (botanisch) bleibt
art-fix; nur die **praktizierte** Achse wird instanz-fähig.

---

## Teil 4 — Empfehlung, Entscheidungsrahmen & offene Fragen

### 4.1 Empfohlene Richtung

1. **Erst verdrahten, dann überschreibbar machen.** Der dringlichere, breitenwirksame Fix ist der **zyklische
   Perennierungs-Ablauf** (Teil 2), unabhängig von der Instanz-Frage. Empfehlung:
   - Erdbeere (und die ~90 Weg-A-Stauden) in den **zyklischen Pfad** überführen: Terminalphase markieren,
     `cycle_restart_phase_order` setzen (Erdbeere: Rücksprung auf die **vegetative** Phase, nicht `germination`),
     bevorzugt via Bindung an ein `phase_sequences.yaml`-Template analog `lifecycles_outdoor.yaml`.
   - Den **Restart-Motor tatsächlich aufrufen**: `should_restart_cycle` / den Restart-Pfad in
     `check_auto_transitions` (oder einem dedizierten Task) verdrahten und Transition-Rules für die Weg-A-Arten
     erzeugen (heute erzeugt der Seeder keine).
   - **REQ-047 ↔ REQ-003 koppeln**: `winter_dormancy`/`pre_spring`-Übergänge des Season-State an den
     Wachstumsphasen-Übergang (`→ dormancy` bzw. Zyklus-Neustart) binden — statt zweier entkoppelter Zyklen.
2. **Danach die Instanz-Entscheidung (Option C).** `PlantInstance.cultivation_cycle_type: CycleType | None`
   einführen, zentrale `resolve_effective_cycle`-Kaskade (Instanz > Art-Kultur > Art-Botanik), an #539
   („Ist-Zustand bei Anlage") ankoppeln, alle Konsumenten auf die Kaskade umstellen.
3. **Stammdaten-Sweep** parallel: 16 `dormancy_required`-ohne-Dormanzphase-Fälle bereinigen; Lavendel/Rosmarin/
   Salbei/Thymian/Minze/Spargel ein Phasen-/Dormanz-Modell geben; Erdbeer-Nebennüsse (`base_temp`,
   `allelopathy_score`, `germination`-Benennung) angleichen.

### 4.2 Entscheidungen, die das Team treffen muss

- **E1 — Instanz-Override ja/nein?** Option A vs. B/C. (Empfehlung: C, aber Priorität *nach* der Verdrahtung.)
- **E2 — Ort der Zyklus-Wahrheit.** Konsolidieren auf **einen** Phasen-Modellierungsweg (Weg B, Template-basiert)
  und Weg A migrieren? Oder Weg A dauerhaft dulden und nur um Terminal/Restart ergänzen?
- **E3 — Kopplung REQ-047 ↔ REQ-003.** Soll der Season-State (standortweit) die Wachstumsphasen der Instanzen
  treiben — und wie werden Konflikte (einjährige Instanz an mehrjährigem Standort) aufgelöst?
- **E4 — Semantik `cycle_restart_phase_order` für Erdbeere.** Rücksprung auf `vegetative` (Skip `germination`) — und
  wird `germination` in `establishment` (einmalig) + zyklischen `sprouting`/`vegetative`-Einstieg getrennt?
- **E5 — `flowering_strategy`-Ablageort.** In `lifecycle_configs` zusammenführen oder in `species.yaml`
  `lifecycle_overrides` belassen (Schema-Autorität) und nur einen Konsistenz-Check ergänzen?
- **E6 — Fakultative Klassifikation.** Wie drückt Stammdatum aus, dass eine Art *beides* kann (fakultativ
  einjährig/mehrjährig) inkl. sinnvollem Default? (Heute implizit über `cycle_type` botanisch +
  `cultivation_cycle_type` praktisch; reicht das, oder braucht es ein explizites `facultative`-Flag/Enum?)
- **E7 — Migrationsumfang.** Nur additives Instanz-Feld, oder auch Backfill/One-off für die ~90 Weg-A-Stauden
  (globale Migrations-Queue beachten)?

### 4.3 Offene Fragen für die Voruntersuchung (vor dem Umsetzungsplan)

- Reiner Datenfehler oder Modell-Lücke? → **Beantwortet:** Modell-/Verdrahtungslücke (Teil 2), plus kleine Datennüsse.
- Wie viele reale Konsumenten müssten auf eine `resolve_effective_cycle`-Kaskade umgestellt werden (Phasen-Restart,
  Season-State, Care-Reminder, Ernte, Dashboard)? → im Umsetzungsplan pro Aufrufstelle auflisten.
- Verhält sich der Season-State-Zyklus (REQ-047) bereits „gut genug" als De-facto-Perennierung für Outdoor, sodass
  REQ-003-Restart nur für Indoor-Perennials/Container relevant ist? → Kopplungs-Design in E3 klären.
- Wie interagiert ein Instanz-Override mit `chill_days_accumulated`/Vernalisation (E2-Trigger) und der
  Rückwärts-Transitions-Sperre (`is_reversion`)? → Zustandsdiagramm im Plan.

---

## Anhang — zentrale Belegstellen

| Thema | Datei:Zeile |
|---|---|
| Erdbeer-Steckbrief (zyklischer Ablauf, Dormanz, Restart) | `spec/knowledge/plants/fragaria_x_ananassa.md:22-37, 152-161, 329-338` |
| Erdbeer-`lifecycle_configs` (kein Restart-Anker) | `src/backend/app/migrations/seed_data/plant_info.yaml:501-508` |
| Erdbeer-`growth_phases` (6 Phasen, keine terminal) | `plant_info.yaml:1044-1203` |
| Erdbeer-`flowering_strategy: polycarpic` (separat) | `species.yaml:2677` |
| `LifecycleConfig` (botanisch vs. Kultur vs. Restart-Anker) | `src/backend/app/domain/models/lifecycle.py:40-95` |
| `PlantInstance` (kein Instanz-Zyklus-Feld) | `src/backend/app/domain/models/plant_instance.py:8-86` |
| Restart-Gate (Terminal-Vorbedingung, Kaskade) | `src/backend/app/domain/engines/phase_transition_engine.py:25-65` |
| `should_restart_cycle` (nur in Tests aufgerufen) | `src/backend/app/domain/engines/cyclic_lifecycle_engine.py:88-106` |
| Auto-Transition rein regelbasiert | `src/backend/app/tasks/phase_transitions.py:104-157` |
| Korrekter zyklischer Outdoor-Weg (Forsythia/Rheum) | `src/backend/app/migrations/seed_data/lifecycles_outdoor.yaml:13-62`, Templates `phase_sequences.yaml:129-167` |
| REQ-047 Season-State (standortgetrieben, entkoppelt) | `src/backend/app/domain/engines/season_state_engine.py:44-51`; `season_state_service.py:80`; `dormancy_care_activator.py:33-70` |
| #297-Entscheidung (Art-Ebene, botanisch vs. Kultur) | `spec/req/REQ-003_Phasensteuerung.md:19-20`; `species.yaml:2600-2739`; `schemas/species.schema.yaml` |
| Vorgänger-Audit (Vokabular, nicht Verdrahtung) | `spec/analysis/lifecycle-flow-completeness-audit.md:13-17, 40-47` |
