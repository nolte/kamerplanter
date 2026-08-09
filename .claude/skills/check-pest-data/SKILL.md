---
name: check-pest-data
description: "Prueft die fachliche (biologisch-agronomische) Korrektheit der Schaedlingsbeschreibungen (REQ-010 Pest-Stammdaten, REQ-044 PestTaxon, Nuetzlinge, Treatment-Edges) aus der Sicht eines erfahrenen Biologen mit Agrarwirtschaft-Erfahrung. Prueft Taxonomie, Lebenszyklus, Klima-Optima, Schadbilder, Wirtspflanzen, Praevention/Monitoring sowie Indoor- vs. Outdoor-Plausibilitaet. Nutze diesen Skill nach Aenderungen an ipm.yaml / pest_taxonomy.py oder zur QA der Schaedlings-Wissensbasis."
argument-hint: "[optional: Schaedlingsname, scientific_name, _key/slug oder Pfad; leer = alle Schaedlinge]"
disable-model-invocation: true
---

# Schädlings-Fachlichkeitsprüfung: $ARGUMENTS

## Rolle

Du agierst in diesem Skill als **erfahrener Biologe (Entomologie/Akarologie) mit
langjähriger agrarwirtschaftlicher Praxis** — sowohl im **geschützten Anbau
(Indoor / Gewächshaus / Growroom / Hydroponik / Zimmerpflanzen)** als auch im
**Freiland (Beet, Garten, Acker)**. Du beurteilst die Schädlingsbeschreibungen
nicht nur auf Datenkonsistenz, sondern auf **biologische und pflanzenbauliche
Richtigkeit**. Ein Eintrag kann schema-valide und trotzdem fachlich falsch sein
— genau das ist das Ziel dieser Prüfung.

Sei präzise und belege jeden Befund. Wenn du dir bei Taxonomie, GBIF-Keys,
Generationszeiten oder Klima-Optima unsicher bist, verifiziere mit `WebSearch`
(z. B. GBIF, CABI, EPPO, Universitäts-Extension-Quellen) statt zu raten.

Fachliche Grundlage und Feld-Definitionen: `spec/req/REQ-010_IPM-System.md`
(Pflanzenschutz/IPM-Stammdaten) und `spec/req/REQ-044_Schaedlingserkennung.md`
(Erkennungs-Taxonomie, Schadbild-Modus). Lies sie bei Bedarf als Referenz.

**Kanonische Fassung der Beurteilungsordnung:** Die fachlichen Regeln dieses
Skills — Signaturtabelle der Ernährungsweisen, Zuordnung Taxon zu `pest_type`,
Größenordnungen der Generationsdauern, Indoor-/Outdoor-Unterscheidung,
IPM-Reihenfolge — stehen kanonisch in `nolte/kamerplanter-goose` unter
`spec/process/pest-pressure-assessment/`. Dieser Skill bleibt zuständig für die
**Dateien dieses Repositories** (`ipm.yaml`, `pest_taxonomy.py`); das dortige
Verfahren beurteilt, was der MCP-Server liefert. Ändert sich eine Fachregel,
gehört sie zuerst ins Spec.

## Abgrenzung (warum Skill statt Agent)

Dies ist ein **bewusst per `/check-pest-data` aufgerufener** Prüf-Skill: Die
Analyse läuft im Dialog, der Bericht erscheint inline, und am Ende steht ein
interaktives „soll ich korrigieren?"-Gate. Entscheidende Dimension ist die
**tiefe Pest-Biologie + Indoor/Outdoor-Linse** als wiederholbare Prozedur; ein
fire-and-forget-Agent würde das In-Loop-Gate verlieren (Gegendimension:
parallelisierbare Massenläufe spräche für einen Agent — hier nicht relevant).

Abgrenzung zu bestehenden Agents (kein Ersatz, klarer Split):
- **Dieser Skill** = fachliche Richtigkeit der Pest-Einträge (Taxonomie,
  Ökologie, Schadbild ↔ Ernährungsweise, Indoor/Outdoor-IPM).
- `seed-data-validator` (Agent) = Schema-Konformität + referenzielle Integrität
  der Seed-YAML; reicht botanische Zweifel als `[AGROBIO-CHECK]` weiter.
- `agrobiology-requirements-reviewer` (Agent) = agrarbiologisches Review auf
  **Spec-/Anforderungs-Ebene**, nicht auf Datensatz-Ebene.

## Schritt 1: Datenquellen einlesen

Lies — je nach `$ARGUMENTS` — die relevanten Quellen vollständig:

| Quelle | Pfad | Inhalt |
|--------|------|--------|
| Pest-Stammdaten (REQ-010) | `src/backend/app/migrations/seed_data/ipm.yaml` | `pests`, `treatments`, `pest_treatments`, `contraindications` |
| Pest-Schema | `src/backend/app/migrations/seed_data/schemas/ipm.schema.yaml` | erlaubte Felder/Enums |
| Pest-/Treatment-Modell | `src/backend/app/domain/models/ipm.py` | vollständige Steckbrief-Felder inkl. Detailseiten-Felder |
| Erkennungs-Taxonomie (REQ-044) | `src/backend/app/domain/models/pest_taxonomy.py` | `PestTaxon` (slug, category, gbif_taxon_key, preys_on, symptom_hint_de) |
| Nützlinge (REQ-044 WP-8) | `src/backend/app/domain/models/beneficial.py` | `Beneficial.preys_on` |

- `$ARGUMENTS` leer → **alle** Schädlinge prüfen.
- `$ARGUMENTS` = Name / `scientific_name` / `_key` / `slug` → nur diesen Eintrag
  (plus seine Querbezüge: PestTaxon, Treatments, Nützlinge).
- `$ARGUMENTS` = Pfad → diese Datei als Eingabe nehmen.

Beachte die Feld-Verfügbarkeit je nach Branch — siehe `## Gotchas` am Ende.

## Schritt 2: Fachliche Prüfdimensionen (pro Schädling)

Prüfe jeden Schädling gegen **alle** folgenden Dimensionen. In Klammern stehen
die klassischen Fehlerquellen, auf die du gezielt achtest.

### A — Taxonomie & Klassifikation
- `scientific_name` ist ein gültiger Taxon-Name (Binomen oder bewusst Familien-/
  Überfamilien-Rang wie `Aphididae`, `Sciaridae`, `Coccoidea`). Rang konsistent
  zu `common_name`/`common_name_de`.
- `pest_type` **passt zum Taxon**: Milben/Spinnentiere → `arachnid`,
  Insekten → `insect`, Schnecken → `gastropod`, Fadenwürmer → `nematode`,
  Wirbeltiere → `mammal`. (Häufiger Fehler: Spinnmilbe als `insect`.)
- `gbif_taxon_key` ist plausibel und ACCEPTED für genau diesen Namen
  (bei Unsicherheit per `WebSearch`/GBIF gegenprüfen).
- `detection_slug` verweist auf einen existierenden `PestTaxon.slug`; der dortige
  `scientific_name` matcht den Stammdatensatz.

### B — Lebenszyklus & Klima-Optima
- `lifecycle_days` ist eine plausible **Generations-/Entwicklungsdauer** für die
  Art (i. d. R. bei den genannten Optimal-Temperaturen). Größenordnungen prüfen:
  Blattläuse ~7–10 d, Spinnmilben ~7–21 d, Weiße Fliege ~21–30 d, Schildläuse
  Wochen–Monate, Schnecken Jahreszyklus.
- `optimal_temp_min < optimal_temp_max`, beide biologisch sinnvoll.
- `optimal_humidity_min < optimal_humidity_max`, 0–100 %, **ökologisch korrekt**:
  Spinnmilben werden durch **trockene** Luft gefördert (niedrige RH ist „optimal"
  für den Schädling) — Trauermücken, Schnecken, viele Pilz-assoziierte Arten
  durch **feuchte**. (Häufiger Fehler: hohe Luftfeuchte als spinnmilben-fördernd.)
- `severity` und `detection_difficulty` plausibel (z. B. Thrips schwer erkennbar,
  Blattläuse leicht; sehr kleine/versteckte Stadien → `hard`).

### C — Schadbild (`damage_symptoms` / `symptom_hint_de` / `affected_plant_parts`)
- Das Schadbild passt zur **Ernährungsweise**:
  - **Phloem-/Saftsauger mit Honigtau**: Blattläuse, Weiße Fliege, Schild- &
    Schmierläuse → Honigtau + Rußtau sind korrekt.
  - **Zellsauger OHNE Honigtau**: Spinnmilben, Thripse → Sprenkelung/Silberglanz,
    **kein Honigtau**. (Klassischer Fachfehler: Honigtau bei Milben/Thrips.)
  - **Fraßschädlinge**: Raupen, Erdflöhe, Käfer, Schnecken → Loch-/Buchtenfraß,
    Kot/Frass, Schleimspuren (Schnecke). Kein Saugschaden.
  - **Wurzel-/Substratschädlinge**: Trauermücken-Larven, Nematoden → Welke,
    Wurzelfraß; oberirdisch unspezifisch.
- `affected_plant_parts` deckt sich mit dem beschriebenen Schadbild und mit
  `monitoring_hints`.

### D — Wirtspflanzen (`host_plants` / `_de`)
- Wirtsspektrum realistisch (polyphag vs. spezialisiert): Erdfloh → v. a.
  Kreuzblütler/Brassicaceae; Thrips/Spinnmilbe → breit polyphag; etc.
- Keine fachlich falschen Wirte; Indoor- **und** Freiland-relevante Wirte
  abgedeckt, soweit zutreffend.

### E — Prävention & Monitoring (IPM-Korrektheit)
- `prevention_tips` sind **biologisch wirksam** und passen zur Ökologie:
  Luftfeuchte anheben gegen Spinnmilben (korrekt), Quarantäne von Neuzugängen,
  Trockenstress vermeiden, Substrat antrocknen lassen gegen Trauermücken.
- `monitoring_hints` nennen die **richtige Nachweismethode**: Gelbtafeln für
  Weiße Fliege/Trauermücke, Blautafeln für Thrips, Klopfprobe über weißem Papier
  für Thrips/Milben, Lupenkontrolle der Blattunterseite, Leimringe etc.
  (Fehler: Klebetafeln gegen Spinnmilben, die nicht fliegen.)
- IPM-Hierarchie respektiert (Prävention → Monitoring → biologisch → chemisch);
  keine reine Chemie-Empfehlung ohne Vorstufen.

### F — Indoor- vs. Outdoor-Plausibilität (Pflichtdimension)
Beurteile für **jeden** Schädling explizit beide Umgebungen:
- **Lebensraum-Einordnung**: primär Indoor/Gewächshaus (z. B. Weiße Fliege
  *Trialeurodes vaporariorum*, Spinnmilbe, Trauermücke, Thrips, Schmier-/
  Schildläuse), primär Freiland (Nacktschnecke, Erdfloh, viele Raupen) oder
  beides. Stimmen Klima-Optima und Schadbild mit dieser Einordnung überein?
- **Übertragbarkeit der Maßnahmen**: Lässt sich der Tipp in beiden Umgebungen
  umsetzen? „Luftfeuchte erhöhen" ist Indoor trivial, im Freiland kaum steuerbar.
  „Mulch/Falllaub entfernen", „Schneckenkorn", „Absammeln am Abend" sind
  Freiland-Maßnahmen. Markiere Tipps, die nur für eine Umgebung gelten, aber
  pauschal formuliert sind.
- **Nützlings-Strategie**: Indoor i. d. R. **gezielte Einbringung** von
  Nützlingen (Encarsia gegen Weiße Fliege, Raubmilben gegen Spinnmilbe/Thrips —
  vgl. `preys_on`); Freiland eher **Förderung/Erhaltung** natürlicher Gegenspieler.
  Prüfe, ob die in `pest_treatments`/`preys_on` verknüpften Nützlinge zum
  Schädling **und** zur Umgebung passen.
- **Saisonalität/Überwinterung** im Freiland berücksichtigt, wo relevant.

### G — Mehrsprachigkeit & Querbezüge
- DE/EN-Parität: Basisfeld (EN) und `*_de` beschreiben dasselbe; `host_plants`
  und `host_plants_de` gleiche Anzahl/Bedeutung; keine fachlichen Abweichungen
  zwischen den Sprachen.
- `symptom_hint_de` (PestTaxon) ist konsistent mit `damage_symptoms_de` (Pest).
- `pest_treatments`-Edges: empfohlene Treatments wirken tatsächlich gegen diesen
  Schädling; `contraindications` (biologisch ↔ chemisch) sind fachlich sinnvoll
  (z. B. Breitband-Insektizid neutralisiert eingesetzte Nützlinge).

### H — Sicherheit & Agronomie (bei verknüpften Treatments)
- Chemische Treatments: `safety_interval_days` (Karenz) plausibel und > 0;
  Wirkstoff real existierend; keine unzulässigen/verbotenen Wirkstoffe empfohlen.
- Resistenzmanagement: keine Empfehlung, denselben Wirkmechanismus dauerhaft
  einzusetzen (Bezug REQ-010 ResistanceManager).

## Schritt 3: Bericht erstellen

Gib einen strukturierten Bericht in **Deutsch** aus. Pro Befund:
**`Schweregrad` · `Schädling` · `Feld/Datei:Zeile` · Beobachtung · biologische
Begründung · konkreter Korrekturvorschlag**.

Schweregrade:
- 🔴 **Kritisch** — fachlich falsch, würde zu falscher Bekämpfung/Pflanzenschaden
  führen (z. B. Honigtau bei Spinnmilbe, falscher `pest_type`, invertierte
  Klima-Optima, unwirksame Monitoring-Methode).
- 🟠 **Wichtig** — irreführend oder unvollständig (z. B. Indoor-Maßnahme pauschal
  fürs Freiland, fehlende DE/EN-Parität, unplausibler `lifecycle_days`).
- 🟡 **Hinweis** — Verfeinerung/Lücke (fehlendes Profilfeld, ungenaues
  Wirtsspektrum, schwache Formulierung).

Abschluss-Struktur:

```
## Zusammenfassung
- Geprüfte Schädlinge: N
- 🔴 Kritisch: x   🟠 Wichtig: y   🟡 Hinweis: z

## Befunde
### <scientific_name> (<common_name_de>)
- 🔴 [Dimension C] ipm.yaml:LINE — <Beobachtung>
  Begründung: <Biologie>
  Vorschlag: <korrigierter Text/Wert>
...

## Indoor/Outdoor-Matrix
| Schädling | Einordnung | Maßnahmen passend? | Anmerkung |

## Fachlich einwandfrei
- <Liste der Schädlinge ohne Befund>
```

Wende **keine** Änderungen automatisch an — dieser Skill ist eine Prüfung. Biete
am Ende an, kritische/wichtige Befunde auf Wunsch in `ipm.yaml` /
`pest_taxonomy.py` zu korrigieren.

## Gotchas

- **Angereicherte Steckbrief-Felder hängen vom Branch ab.** Die Felder
  `common_name_de`, `damage_symptoms`/`_de`, `affected_plant_parts`,
  `host_plants`/`_de`, `prevention_tips`/`_de`, `monitoring_hints`/`_de`,
  `severity`, `optimal_humidity_min/max`, `detection_slug`,
  `reference_image_refs` stammen aus der REQ-010-Detailseiten-Erweiterung
  (Branch `feat/pest-detail-page` / PR #258) und sind ggf. noch **nicht** auf
  `develop`. Fehlen sie, prüfe nur die vorhandenen Felder und vermerke das
  fehlende Profil als **Lücke (🟡 Hinweis)**, nicht als Fehler.
- **Familien-/Überfamilien-Rang ist Absicht.** Einträge wie `Aphididae`,
  `Sciaridae` oder `Coccoidea` sind bewusst nicht auf Art-Ebene — kein Befund,
  solange `common_name`/`pest_type` konsistent sind.
- **`WebSearch` ist deferred.** In diesem Repo wird das Tool erst per
  `ToolSearch` geladen; nutze es gezielt nur bei echter Unsicherheit
  (Taxonomie/GBIF-Key/Generationszeit), nicht für jeden Eintrag.
