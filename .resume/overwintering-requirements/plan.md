# Plan — docs/overwintering-requirements

**Worktree:** `/home/nolte/repos/.worktrees/kamerplanter/overwintering-requirements`
**Branch:** `docs/overwintering-requirements` (off `origin/develop`)
**Aufgabe:** Anforderungsdokument(e) für die Überwinterung **inhaltlich vertiefen
und erweitern** — über das **gesamte überwinterungs-berührende REQ-Set** hinweg
(operator-bestätigt, 2026-07-11).

---

## Goal

Die über mehrere REQ-Dokumente verstreute Überwinterungs-Fachlichkeit soll
**inhaltlich vertieft und erweitert** werden: mehr abgedeckte Fälle (Arten,
Winterquartier-Situationen, Abhärtung/Rückholung, Edge Cases), präzisere
Akzeptanzkriterien, geschlossene fachliche Lücken. Es ist **Spec-Arbeit**, keine
Code-Implementierung: Ziel sind bessere, tiefere Anforderungsdokumente unter
`spec/req/` (DE-kanonisch), nicht neuer Produktivcode.

**Kern-Dokument:** `REQ-047_Saison-Ueberwinterungs-Automatik.md` (SeasonState-
Engine, dreistufige Trigger-Kaskade Live→Klima→Kalender). **Cluster:** REQ-039
(Winterhärte-Ampel) + REQ-022 (Pflegeerinnerungen/OverwinteringProfile/
CareProfile). **Berührt:** REQ-001 (`frost_sensitivity`), REQ-002 (Standort:
indoor/outdoor/greenhouse, GPS, Hemisphäre), REQ-003 (dormancy-Phase, Invariante
D5), REQ-005 (Frost-/Wetter-Livedaten), REQ-006 (Task-Erzeugung), REQ-013
(Run/Dual-Support), REQ-041 (Klimanormale als Saison-Fallback), REQ-046
(Wetterquellen-Auflösung), REQ-024 (Mandanten-Scoping).

## Current state (recherchiert am 2026-07-11, im Worktree)

Fakten mit Fundstellen (relativ zu `spec/req/`):

- **`REQ-047_Saison-Ueberwinterungs-Automatik.md`** (492 Zeilen, `Status:
  Entwurf`, `Version: 1.0` vom 2026-07-05). Führt die **SeasonState-Engine** ein
  (pro Outdoor-/Greenhouse-Standort), dreistufige Kaskade *beste Quelle gewinnt*:
  1 Live (`:WeatherForecast`/Sensorik), 2 Klimatologisch (`:ClimateNormal` +
  `HardinessZone.typical_first/last_frost_md`), 3 Kalender (`Site.hemisphere` +
  Preset-Monate). Auto-Materialisierung des `OverwinteringProfile` aus Species-
  Template + Standort-Ampel; **Dormancy-Care-Modus** im CareProfile.
  Geltungsbereich explizit nur `type ∈ {outdoor, greenhouse}`.
  - **⚠ Implementiert (Memory):** REQ-047 wurde als **PR #406 gemergt**
    (`8f2b55eb5`), Folge-PR #410. Das Spec-Doc trägt aber noch `Status: Entwurf`
    → mögliche Drift Spec↔Code (nicht primäres Ziel, aber beim Vertiefen
    mitzunehmen: nicht am gebauten Stand vorbei erweitern).
- **`REQ-039_Klimazonen-Winterhaerte.md`** (337 Zeilen) — Winterhärte-Ampel
  (`evaluate_winter_hardiness`), Klimazonen, Frost-Defaults. REQ-047 ist reiner
  **Konsument** des Ampel-Ergebnisses (Pfad-Zuordnung, Invariante D5).
- **`REQ-022_Pflegeerinnerungen.md`** — Heimat des `OverwinteringProfile`
  (bislang manuell), `CareProfile`, `CareReminderEngine`, datumsbasierte Winter-/
  Frühlings-Erinnerungen (die REQ-047 auf zustandsbasiert verlagert). Overwintering-
  Template-Seeds (`overwintering_profiles.yaml`, 175 Templates aus §4.3).
- **Steckbriefe** `spec/knowledge/plants/*.md` §4.3 Überwinterung = fachliche SSOT
  der art-spezifischen Überwinterungs-Bedingungen; Templates werden daraus
  deterministisch generiert. Vertiefung von Inhalten muss hierhin verweisen, statt
  Werte im REQ-Text zu duplizieren.
- **Governing conventions:** Doku DE-kanonisch (`spec/style-guides/DOCS.md`);
  Source-Code Englisch (NFR-003) — hier aber Spec-Text, also DE. REQ-Dokumente
  folgen dem Aufbau der bestehenden REQ-Dateien (YAML-Kopf, Versionshistorie,
  Business Case/User Stories, Datenmodell, …).

> **Noch offen (Grounding vertagt an `requirements-elicit`):** genaue inhaltliche
> Vertiefungs-Themen (welche Arten/Fälle/Edge-Cases konkret fehlen) werden in der
> nächsten Session präzise erhoben, bevor Text geschrieben wird.

## Design decision (load-bearing)

**Spec-Vertiefung über das Cluster, mit REQ-047 als Anker — nicht Neuschrieb, nicht Code.**

1. **Requirements-elicit zuerst.** „Inhaltlich vertiefen/erweitern über alle
   berührenden Docs" ist bewusst breit. Die nächste Session startet mit
   `/nolte-shared:requirements-elicit`, um **präzise** zu erheben, *welche*
   fachlichen Lücken/Fälle vertieft werden sollen (Priorisierung, Abgrenzung,
   Akzeptanzkriterien) → Artefakt `project/requirements/overwintering-requirements.md`.
2. **REQ-047 ist der Anker**, das übrige Cluster (039/022) und die berührenden
   REQs werden nur dort angefasst, wo die Vertiefung sie zwingend berührt —
   Querverweise sauber ziehen statt Fachlichkeit duplizieren (SSOT-Regel:
   art-spezifische Werte bleiben in Steckbriefen/Templates).
3. **Drift-bewusst erweitern:** REQ-047 ist gebaut (#406/#410). Beim Vertiefen den
   real implementierten Stand berücksichtigen (Code im Worktree lesen), damit die
   Spec nicht am Produkt vorbei wächst; wo Spec-Text und Code auseinanderlaufen,
   im Elicit als Entscheidung markieren (angleichen vs. bewusst voraus-spezifizieren).
4. **Werkzeuge:** Autoren-/Review-Skills nutzen — `spec` (Schreiben/Index/
   Übersetzung), `spec-readiness-reviewer` + `requirements-contradiction-analyzer`
   (nach dem Vertiefen: Konsistenz gegen den Rest des Clusters absichern).

**Open questions — vor Arbeitsbeginn (in der nächsten Session via elicit) zu klären:**

- **Q1 — Vertiefungs-Fokus:** Welche konkreten Themen zuerst? (z. B. Winterquartier-
  Fälle/Pfad B, Abhärtungs-/Rückhol-Prozess im Frühjahr, mehr Arten-Klassen,
  Greenhouse-Sonderfälle, Fäulnis-/Feuchte-Kontrolle im Quartier, mehrjährige
  Kübelpflanzen vs. Beet.)
- **Q2 — Spec↔Code-Drift bei REQ-047:** Erweitern wir *auf* dem implementierten
  Stand (Spec dem Code angleichen + darüber hinaus vertiefen) oder rein
  fachlich-vorausschauend? Status/Version-Pflege von REQ-047 (Entwurf→?) dabei.
- **Q3 — Cluster-Reichweite:** Wie invasiv dürfen REQ-039/022 und die berührenden
  REQs geändert werden — nur Querverweise/Ergänzungen, oder eigene Vertiefungen dort?
- **Q4 — DoD:** Gilt die Doku-Lektorats-DoD (DOCS.md), und ist am Ende ein
  Konsistenz-Review über das Cluster verpflichtend (contradiction-analyzer)?
- **Q5 — Übersetzung/Index:** Bleibt DE-kanonisch ohne EN-Mirror-Pflicht für
  `spec/req/` (wie Bestand), oder ist Index/Mirror mitzuführen?

## Work steps

1. **`/nolte-shared:requirements-elicit`** → Vertiefungs-Umfang präzise erheben,
   Q1–Q5 beantworten; Artefakt `project/requirements/overwintering-requirements.md`
   ≥ Threshold.
2. **Grounding:** REQ-047/039/022 vollständig lesen + berührende REQs überfliegen +
   implementierten Stand (Backend/Frontend zu SeasonState/Overwintering) sichten,
   um Spec↔Code-Drift zu kennen.
3. **Vertiefen (REQ-047 zuerst):** priorisierte fachliche Lücken schließen —
   neue/erweiterte User Stories, Akzeptanzkriterien, Datenmodell-/Zustands-
   Ergänzungen, Edge Cases; SSOT-Regel wahren (Werte → Steckbriefe verweisen).
4. **Cluster nachziehen:** REQ-039/022 (und berührende REQs) nur an den durch die
   Vertiefung erzwungenen Stellen; Querverweise/Abhängigkeiten aktualisieren.
5. **Konsistenz-Review:** `spec-readiness-reviewer` + `requirements-contradiction-
   analyzer` über das Cluster; gefundene Widersprüche auflösen.
6. **Lektorat/DoD** (falls in Q4 bestätigt): `lektorat-apply` / DOCS.md-Konventionen;
   Versionshistorie + Status/Version je geändertem REQ pflegen.
7. **PR** nach `develop` via `pull-request-create` (Conventional Commits, EN;
   `docs`-Scope).

## Invariants & guardrails (aus CLAUDE.md + Specs)

- **Spec-Arbeit, kein Code:** Deliverable sind REQ-Dokumente unter `spec/req/`.
  Keine Produktivcode-Änderung im Rahmen dieser Aufgabe (falls die Vertiefung neue
  Impl. nahelegt → als Folge-REQ/Backlog markieren, nicht hier bauen).
- **Doku Deutsch, DE-kanonisch** (`spec/style-guides/DOCS.md`, NFR-003-Ausnahme:
  Doku DE); REQ-Dateien folgen dem Aufbau der Bestandsdokumente.
- **SSOT:** Art-spezifische Überwinterungs-Werte bleiben in Steckbriefen §4.3 /
  Templates (REQ-022); REQ-Text **verweist**, dupliziert nicht.
- **Abgrenzung wahren:** REQ-047 bleibt Konsument von REQ-005/046 (Wetter) und
  REQ-039 (Ampel); keine Neudefinition dieser Domänen in REQ-047.
- **Drift-Ehrlichkeit:** REQ-047 ist implementiert (#406/#410) — nicht am gebauten
  Stand vorbei spezifizieren; Divergenzen bewusst entscheiden (Q2).
- **GitHub-Texte Englisch** (PR-Titel/Beschreibung, Commits); Kommunikation mit dem
  Operator Deutsch.
- **Branch von `develop`;** Hauptcheckout bleibt auf `develop` — Arbeit nur im
  Worktree. `docs/`-Prefix (Spec-/Doku-Änderung).

## Status / resume-anchor checklist

Erste unerledigte Box = Wiedereinstiegspunkt der nächsten Session.

- [x] **`requirements-elicit`** ausgeführt, Q1–Q5 beantwortet, Artefakt
      `project/requirements/overwintering-requirements.md` ≥ Threshold.
      → 2026-07-11: 4 Frage-Turns, `U_gate=0.80` (Sättigung). Q1=alle 4 Themen;
      Q2=erst angleichen→vertiefen; Q3=additiv wo Thema wohnt; Q4=volle DoD;
      Q5=DE-only (spec/req/ per Faktencheck ohne EN-Mirror/Index). Reihenfolge
      per Teach-back: REQ-047 angleichen → Winterquartier → Frühjahr → Arten → Robustheit.
- [x] Grounding: Cluster-Docs + implementierter REQ-047-Stand gelesen, Drift notiert.
      → 2026-07-11: REQ-047/039 vollständig, REQ-022 überwinterungs-relevant, Template-SSOT-
        Schema + §4.3-Steckbriefe (dahlia/lavandula/hydrangea) gelesen. §4.3 = fachliche SSOT.
        Code-Kartierung (Agent ad2f0d8): REQ-047-Kern real+vollständig gebaut (#406/#410).
        **Drift für Angleichung (R2), echte Punkte:**
        (D1) AC-13 quarter_climate_check: Code = periodische 7-Tage-Kontrolle bei Livedaten;
             Spec = Temperaturverletzung winter_quarter_temp_min/max. Kein Ist/Soll-Vergleich real.
        (D2) SeasonSignal Stufe 2 speist aus Site-Ø-Frostdaten (REQ-002/015-A), NICHT REQ-041;
             coldest_month hartkodierte Hemisphären-Monate (_AFTER_COLDEST_MONTHS), nicht
             ClimateNormal.coldest_month_min_c.
        (D3) Zusatz-Engine-Guards _PRE_WINTER_SEASON_MONTHS + _SPRING_RELEASE_WINDOW_DAYS=182
             nicht in §3.3 dokumentiert.
        (D4) Zusatz-Endpunkt GET .../overwintering/status (#410) fehlt in §4.4-Tabelle.
        (D5) season_year: Spec int → Code int|None (None während growing).
        (D6) §3.1/§3.4-Skizzen async, Code synchron (python-arango).
        (D7) §4.1-Widget real als SeasonOverviewPanel INNERHALB Widget winter_protection.
        (D8) Config SEASON_LIVE_FORECAST_WINDOW_DAYS (Default 7) fehlt in §5-Env-Liste.
        **Agent-Fehlalarm gegengeprüft/verworfen:** materialized_at/source_template_key stehen
        schon in §2.3 (Z.112-113); SEASON_STATE_EVAL_ENABLED steht schon in §5 (Z.447).
        harden_off/pre_sprouting sind SpringAction/TuberStatus, KEINE ReminderType (Spec korrekt).
        Cluster-intern: REQ-039 Z.521 + REQ-022 Z.513-535 zeigen noch ALTE String-Ampel vs.
        neue zonen-numerische evaluate_winter_hardiness (REQ-039 §3) → beim Nachziehen angleichen.
- [x] REQ-047 inhaltlich vertieft (priorisierte Lücken geschlossen, AC ergänzt).
      → 2026-07-11: Block 0 Angleichung (Status→Umgesetzt v1.1, D1-D8 surgical). Block 1-4
        Vertiefung §§3.7-3.10 (Winterquartier/Quartier-Typen/Ein-Ausräumen/Fäulniskontrolle;
        Abhärtungs-Staging/Vorziehen/Spätfrost; Arten-Sonderfälle immergrün/grenzwertig/Kübel-Beet/
        GWH-heated/mehrjährig; Robustheit-Edge-Cases). AC-21..28 ergänzt, „noch nicht
        implementiert"-Markierungen gesetzt. SSOT-treu (Werte → §4.3).
- [x] Cluster (REQ-039/022 + berührende REQs) an erzwungenen Stellen nachgezogen,
      Querverweise aktualisiert.
      → 2026-07-11: REQ-022 additiv (v2.7→2.8): Alt-Ampel-Inkonsistenz aufgelöst (Verweis
        auf maßgebliche evaluate_winter_hardiness REQ-039 §3), Querverweis auf REQ-047
        §§3.7-3.10; keine Modell-Änderung (SSOT §4.3). REQ-039 unverändert (minimal per R3:
        listet REQ-047 bereits als Konsument, evaluate_winter_hardiness ist dort maßgeblich).
- [x] Konsistenz-Review (readiness + contradiction-analyzer) grün, Widersprüche gelöst.
      → 2026-07-11: 2 Agenten. contradiction: W-1 HOCH (AC-4/§6 REQ-041 nicht nachgezogen,
        selbst verursacht), W-2 MITTEL (REQ-041/005 cross-doc), W-3 MITTEL (Ampel-Grenzfall
        delta<=0), W-4/W-5 LOW. readiness: Crit-1=W-1, Crit-2 (veraltete reminder_type-Listen
        REQ-022:240/1601), High-3=W-5, High-4 (undef. Guards), Med-5 (fehl. AC monokarpisch),
        Med-6 (Status-Konvention), Low-7/8/9. ALLE gefixt: AC-4+§6+§2.5 (W-1/W-5), evaluate_
        winter_hardiness delta<=0 an Code angeglichen REQ-039 v1.3 + REQ-022 (W-3), reminder_type
        13-Werte-Sync REQ-022 (Crit-2), Guard-Werte-Tabelle §3.3 (High-4/Low-9), AC-29 monokarpisch
        (Med-5), Status qualifiziert (Med-6, OFFEN für User-Override), location_check/§3.7.1 (Low-7/8),
        REQ-041 v1.1 + REQ-005 v2.8 Cross-Doc (W-2). Verifikation folgt.
- [x] Lektorat/DoD + Versionshistorie/Status je geändertem REQ gepflegt.
      → 2026-07-11: lektorat-scanner auf REQ-047-Neuprosa (LIX=55, im Ziel). 3 crit (Grammatik:
        Kongruenz „treffen", fehl. Subjekt §3.10, „stellt…dar"), 8 warn, Präpositions-/Idiomatik-
        Fixes alle angewandt. Versionen/Historie: REQ-047 v1.1 (Status qualifiziert), REQ-022 v2.8,
        REQ-039 v1.3, REQ-041 v1.1, REQ-005 v2.8.
- [x] PR nach `develop` via `pull-request-create` (docs-Scope) erstellt.
      → 2026-07-11: Rebase auf origin/develop (2 Commits, konfliktfrei), Push, Draft-PR
        **#476** (https://github.com/nolte/kamerplanter/pull/476). Tracking-Issue **#477**
        (Verifikation Ist-Implementierung gegen vertiefte Anforderungen + not-yet-implemented
        Ausbaustufen AC-4/22/26/29) erstellt und am PR verlinkt. ABGESCHLOSSEN.
