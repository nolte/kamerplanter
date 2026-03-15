# Spezifikation: REQ-022 - Einfache Pflegeerinnerungen für Zimmerpflanzen & Überwinterungsmanagement

```yaml
ID: REQ-022
Titel: Einfache Pflegeerinnerungen für Zimmerpflanzen & Überwinterungsmanagement
Kategorie: Pflege & Erinnerungen
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery, React, TypeScript, MUI
Status: Entwurf
Version: 2.4 (Agrarbiologie-Review Korrekturen)
```

## 1. Business Case

**User Story (Gießerinnerung):** "Als Zimmerpflanzen-Besitzer mit 15 Pflanzen möchte ich eine einfache Erinnerung bekommen, welche Pflanze heute gegossen werden muss — ohne Workflow-Templates, Task-Dependencies oder Cron-Expressions verstehen zu müssen."

**User Story (Ein-Tap-Bestätigung):** "Als Einsteiger möchte ich eine Pflege-Aktion mit einem einzigen Fingertipp als erledigt markieren können — damit ich nicht durch Formulare navigieren muss, nur um zu sagen 'Ja, gegossen'."

**User Story (Adaptive Intervalle):** "Als erfahrener Pflanzenhalter möchte ich, dass das System mein tatsächliches Gießverhalten lernt — wenn ich meine Monstera konsequent alle 8 statt 7 Tage gieße, soll das Intervall automatisch angepasst werden."

**User Story (Saisonale Erinnerungen):** "Als Zimmerpflanzen-Besitzer möchte ich im Oktober daran erinnert werden, meine Pflanzen vom Balkon zu holen und im März daran, sie an hellere Standorte umzuziehen — ohne diese Termine selbst im Kalender pflegen zu müssen."

**User Story (Dünge-Saison):** "Als Pflanzenbesitzer möchte ich, dass Dünge-Erinnerungen nur während der Wachstumssaison (März–Oktober) erscheinen — weil Zimmerpflanzen im Winter nicht gedüngt werden sollen."

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
**User Story (Überwinterung):** "Als Gartenbesitzerin möchte ich im Oktober automatisch daran erinnert werden, welche meiner Pflanzen Winterschutz brauchen, welche ich ausgraben muss und welche ins Haus müssen — damit mir kein einziger Dahlienknolle erfriert."

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
**User Story (Winterhärte-Ampel):** "Als Gärtnerin möchte ich auf einen Blick sehen, welche meiner 120 Pflanzen den Winter draußen überstehen (grün), welche Schutz brauchen (gelb) und welche unbedingt frostfrei überwintert werden müssen (rot) — abgestimmt auf MEINE Klimazone."

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
**User Story (Frühlings-Erinnerung):** "Als Gartenbesitzerin möchte ich im März/April daran erinnert werden, dass ich die Dahlienknollen vorziehen, die Rosen abhäufeln und die Kübelpflanzen schrittweise wieder rausstellen muss."

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
**User Story (Knollen-Zyklus):** "Als Gärtnerin möchte ich den kompletten Jahreszyklus meiner Dahlien, Gladiolen und Canna dokumentieren: Auspflanzen → Blühen → Ausgraben → Trocknen → Einlagern → Kontrollieren → Vorziehen → wieder Auspflanzen."

**Beschreibung:**
Zimmerpflanzen-Enthusiasten (5–50 Pflanzen) brauchen ein einfaches, verlässliches Erinnerungssystem für wiederkehrende Pflegeaufgaben. Das professionelle Workflow-System (REQ-006) mit seinen Templates, Dependency-Chains, HST-Validierung und Workflow-Executions ist für diesen Anwendungsfall überdimensioniert und einschüchternd.

REQ-022 ist eine **spezialisierte Vereinfachungsschicht** auf dem bestehenden Task-System. Alle Erinnerungen werden als reguläre `Task`-Objekte (mit `skill_level=beginner`, `category='care_reminder'`) in der bestehenden `tasks`-Collection gespeichert — kein paralleler Reminder-Store, keine Datenbank-Duplizierung.

**Kernkonzepte:**

**CareProfile — Pflegekonfiguration pro Pflanze:**
Jede `PlantInstance` erhält ein `CareProfile`, das die Pflegeintervalle für diese spezifische Pflanze definiert. Das Profil wird beim ersten Zugriff automatisch aus den Species-Stammdaten generiert (via `RequirementProfile` und `care_style`-Preset) und kann vom Nutzer nachträglich angepasst werden.

**Care-Style-Presets:**
Vordefinierte Pflegeprofile für typische Zimmerpflanzen-Kategorien:

| care_style | Gießen (Sommer) | Winter-Multiplikator | Düngen | Umtopfen | Schädlingsk. | Typische Pflanzen |
|------------|----------------|---------------------|--------|----------|-------------|-------------------|
| `tropical` | 7 Tage | 1.5× (→ 10–11 Tage) | 14 Tage (Mär–Okt) | 18 Monate | 14 Tage | Monstera, Philodendron, Ficus |
| `succulent` | 14 Tage | 2.5× (→ 35 Tage) | 30 Tage (Apr–Sep) | 24 Monate | 21 Tage | Echeveria, Haworthia, Aloe |
| `orchid` | 7 Tage (Tauchbad) | 1.5× (→ 10–11 Tage) | 14 Tage (Mär–Okt) | 24 Monate | 14 Tage | Phalaenopsis, Dendrobium |
| `calathea` | 5 Tage | 1.3× (→ 6–7 Tage) | 14 Tage (Mär–Sep) | 18 Monate | 7 Tage | Calathea, Maranta, Ctenanthe |
| `herb_tropical` | 3 Tage | 1.5× (→ 4–5 Tage) | 21 Tage (Mär–Okt) | 12 Monate | 14 Tage | Basilikum, Minze, Koriander |
| `mediterranean` | 10 Tage | 2.0× (→ 20 Tage) | 30 Tage (Apr–Sep) | 24 Monate | 21 Tage | Rosmarin, Lavendel, Thymian, Salbei |
| `fern` | 4 Tage | 1.3× (→ 5–6 Tage) | 21 Tage (Mär–Okt) | 12 Monate | 14 Tage | Nephrolepis, Adiantum, Asplenium |
| `cactus` | 21 Tage | 3.0× (→ 63 Tage) | 30 Tage (Mai–Aug) | 36 Monate | 30 Tage | Kakteen (Cactaceae). **Nicht** für Lithops/Mesembs (Aizoaceae) — deren Gießrhythmus erfordert gattungsspezifische Logik (Schrumpfphase Feb–Mai = 0 Wasser) |
| `custom` | Frei konfigurierbar | Frei konfigurierbar | Frei konfigurierbar | Frei konfigurierbar | — | — |

**Gießmethode pro Preset (`watering_method`):**

Die Erinnerung sagt nicht nur *wann*, sondern auch *wie* gegossen werden soll. Die Gießmethode ist artspezifisch und für Einsteiger eine der häufigsten Fehlerquellen:

| care_style | `watering_method` | Anleitung (i18n) |
|------------|-------------------|------------------|
| `tropical` | `top_water` | "Von oben gießen, bis Wasser unten herausläuft. Überschuss nach 30 Min. wegkippen." |
| `succulent` | `drench_and_drain` | "Kräftig durchgießen, vollständig ablaufen lassen. Untersetzer nach 10 Min. leeren." |
| `orchid` | `soak` | "Tauchbad: Topf 10–15 Minuten in zimmerwarmes Wasser stellen, dann abtropfen lassen." |
| `calathea` | `top_water` | "Von oben mit kalkarmem Wasser gießen. Blätter nicht benetzen (Pilzgefahr)." |
| `herb_tropical` | `top_water` | "Von oben gießen, Substrat gleichmäßig feucht halten." |
| `mediterranean` | `drench_and_drain` | "Durchdringend gießen, dann vollständig abtrocknen lassen." |
| `fern` | `top_water` | "Von oben gießen + regelmäßig Blätter besprühen (Luftfeuchte)." |
| `cactus` | `drench_and_drain` | "Kräftig durchgießen, vollständig austrocknen lassen (Substrat muss trocken sein)." |
| `custom` | Frei wählbar | — |

**Wasserqualitäts-Hinweis pro Preset (`water_quality_hint`):**

Bestimmte Pflanzengruppen reagieren empfindlich auf Kalk im Leitungswasser. Der Hinweis wird als optionaler Tooltip in der ReminderCard angezeigt:

| care_style | `water_quality_hint` |
|------------|---------------------|
| `tropical` | `null` (Leitungswasser OK) |
| `succulent` | `null` |
| `orchid` | "Kalkarmes Wasser bevorzugt. Abgestandenes Leitungswasser oder Regenwasser." |
| `calathea` | "Kalkempfindlich! Regenwasser, gefiltertes oder abgestandenes Wasser verwenden." |
| `herb_tropical` | `null` |
| `mediterranean` | `null` |
| `fern` | "Weiches Wasser bevorzugt. Abgestandenes Leitungswasser oder Regenwasser." |
| `cactus` | `null` |

Biologische Begründung: Calatheen und Maranteen reagieren mit braunen Blattspitzen auf kalkhaltiges Wasser. Orchideen-Velamen-Wurzeln können durch Kalkablagerungen in der Wasseraufnahme blockiert werden. Farne (insbes. Adiantum) sind kalkempfindlich.

**Biologische Begründung der Preset-Werte:**
- **Tropische Grünpflanzen** stammen aus gleichmäßig feuchten Wäldern — konstante Wasserversorgung, aber keine Staunässe. Dünger nur in der lichtreichen Wachstumsphase (Mär–Okt auf der Nordhalbkugel), da bei geringer Lichtintensität im Winter die Photosynthese-Rate sinkt und Nährstoffe nicht verwertet werden können (Salzakkumulation im Substrat).
- **Sukkulenten/Kakteen** speichern Wasser in sukkulenten Geweben (CAM-Metabolismus) — längere Trockenperioden sind physiologisch nötig, da dauerfeuchtes Substrat zu Wurzelfäule führt (Phytophthora, Pythium). Düngung nur in der kurzen Aktivphase. Im Winter nahezu komplett trocken halten (3× Multiplikator).
- **Calatheen** sind Unterwuchs-Pflanzen tropischer Regenwälder — hoher Wasserbedarf, empfindlich gegen Austrocknung und Spinnmilbenbefall (trockene Heizungsluft im Winter ist Hauptrisiko). Kürzere Schädlingskontroll-Intervalle sind daher essenziell. Im Winter nur leicht reduziertes Gießen (1.3×), da Calatheen Trockenheit nicht tolerieren.
- **Orchideen** (epiphytisch) haben Velamen-Wurzeln, die zyklisches Durchnässen und Abtrocknen brauchen — Tauchbad-Methode ist Standard. Wurzelfäule bei Staunässe ist häufigste Todesursache.
- **Kräuter (tropisch)** (`herb_tropical`): Feuchtigkeitsliebende, schnellwachsende Kräuter (Basilikum, Minze, Koriander) — hoher Wasserverbrauch durch große Blattfläche und schnelle Transpiration. Im Winter bei reduziertem Licht weniger Wasserverbrauch (1.5×).
- **Mediterrane Pflanzen** (`mediterranean`): Rosmarin, Lavendel, Thymian und Salbei stammen aus der Macchie — angepasst an Trockenperioden mit geringem Nährstoffbedarf. Überwässerung und Überdüngung sind die häufigsten Pflegefehler. Im Winter bei kühler Überwinterung stark reduzieren (2×). **Dürfen NICHT mit `herb_tropical` zusammengefasst werden** — Rosmarin bei 3-Tage-Gießintervall entwickelt Wurzelfäule innerhalb weniger Wochen.
- **Farne** (`fern`): Pteridophyten mit hohem Feuchtigkeitsbedarf — sowohl Substrat- als auch Luftfeuchte. Empfindlicher gegen Austrocknung als die meisten Blütenpflanzen, da Farne keine Cuticula-Verdickung als Verdunstungsschutz entwickelt haben. Im Winter nur minimal reduzieren (1.3×), da Farne keinen echten Dormanz-Modus haben.

**Saisonale Gießintervall-Anpassung (`winter_watering_multiplier`):**
Der Wasserbedarf von Zimmerpflanzen schwankt zwischen Sommer und Winter um den Faktor 1,3 bis 3,0. Die Ursachen sind:
- Reduzierte Lichtintensität → geringere Photosynthese-Rate → weniger Transpiration
- Kürzere Tage → weniger Stomata-Öffnungszeit
- Niedrigere Temperaturen (Fensterbankeffekt) → reduzierte Evaporation
- Heizungsluft senkt zwar rH, aber die Kombination mit kaltem Substrat (Fensterbankeffekt) erhöht das Risiko für Wurzelfäule bei gleichbleibendem Gießvolumen

Ohne saisonale Anpassung ist **Überwässerung im Winter die häufigste Todesursache** bei Zimmerpflanzen (Wurzelfäule durch Phytophthora, Pythium).

Der `winter_watering_multiplier` wird auf das Gießintervall angewendet, wenn der aktuelle Monat in den Winter-Monaten liegt (November–Februar auf der Nordhalbkugel, Mai–August auf der Südhalbkugel). Die Hemisphäre wird aus `Site.hemisphere` abgeleitet (Default: `'northern'`). Das effektive Intervall berechnet sich als: `effective_interval = base_interval × multiplier`.

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
**Outdoor-/Freiland-Care-Style-Presets:**

Ergänzende Presets für Freilandpflanzen, die nicht unter die Zimmerpflanzen-Presets fallen:

| care_style | Gießen (Sommer) | Winter-Aktion | Schnitt | Typische Pflanzen |
|------------|----------------|---------------|---------|-------------------|
| `outdoor_perennial` | Witterungsabhängig | Winterschutz prüfen (Mulch, Vlies) | Rückschnitt Frühjahr | Stauden (Rittersporn, Phlox, Astilbe) |
| `outdoor_annual_veg` | 2-3 Tage (Hochbeet: täglich) | Abräumen, Gründüngung | Ausgeizen (Tomate) | Tomaten, Zucchini, Gurken, Paprika |
| `fruit_tree` | Bei Trockenheit (Jungbäume regelmäßig) | Kalkanstrich, Stammschutz | Winter-/Sommerschnitt | Apfel, Birne, Kirsche, Pflaume |
| `berry_shrub` | Regelmäßig bei Trockenheit | Mulchen | Sortenabhängig | Himbeere, Johannisbeere, Stachelbeere |
| `rose` | 1x pro Woche tief | Anhäufeln + Vlies | Frühjahrsschnitt (Forsythienblüte!) | Beet-, Strauch-, Kletterrosen |
| `frost_tender_tuber` | Normal | AUSGRABEN + frostfrei lagern | Laub nach Frost abschneiden | Dahlie, Gladiole, Canna, Knollenbegonie |
| `frost_tender_container` | Normal (wenig im Winter) | Ins Winterquartier (5-12°C, hell) | Vor Einräumen | Oleander, Zitrus, Olive, Schmucklilie |
| `winter_vegetable` | Reduziert | Vlies bei Kahlfrost, draußen lassen | — | Grünkohl, Feldsalat, Winterpostelein |
| `spring_bulb` | — (Ruhe im Sommer) | Winterhart (im Boden lassen) | Laub einziehen lassen! | Tulpe, Narzisse, Krokus, Hyazinthe |

**10 Erinnerungstypen:**

| Typ | Schlüssel | Auslöser | Priorität |
|-----|-----------|----------|-----------|
| Gießen | `watering` | Intervall seit letzter Bestätigung | `high` (Pflanze vertrocknet) |
| Düngen | `fertilizing` | Intervall + nur in Aktivmonaten UND Phase `active_growth` / `vegetative` | `medium` |
| Umtopfen | `repotting` | Monate seit letztem Umtopfen | `low` |
| Schädlingskontrolle | `pest_check` | Festes Intervall (Default 14 Tage) | `medium` |
| Standort-Check | `location_check` | Saisonal: konfigurierbar (Default: Oktober + März, hemisphärenabhängig) | `medium` |
| Luftfeuchte-Check | `humidity_check` | Saisonal: Heizperiode (Okt–Mär NH), nur für feuchtigkeitsempfindliche Presets | `medium` |
| Winterschutz | `winter_protection` | Saisonal: konfigurierbar (Default: Oktober NH / April SH) | `high` (Pflanze erfriert!) |
| Frühlings-Auspacken | `spring_uncover` | Saisonal: konfigurierbar (Default: März NH / September SH) | `high` |
| Knollen ausgraben | `tuber_dig` | Saisonal: Vor erstem Frost (Oktober NH) | `critical` (Knollen erfrieren!) |
| Knollen-Kontrolle | `storage_check` | Intervall während Lagerung (Default: 30 Tage, Nov–Mär) | `medium` |

**Dünge-Guard:**
Dünge-Erinnerungen werden nur generiert, wenn **beide** Bedingungen erfüllt sind:
1. Aktueller Monat liegt innerhalb der `fertilizing_active_months` des CareProfile
2. `PlantInstance.current_phase` ist NICHT in `DORMANCY_PHASES` (siehe unten)

**DORMANCY_PHASES** (Phasen ohne Dünge-Erinnerungen):
- `dormancy` — Winterruhe (REQ-003)
- `senescence` — Alterungsphase (REQ-003)
- `hardening_off` — Abhärtung (REQ-003 Stress-Phase)
- `maintenance` — Winter-Erhaltungspflege bei Zimmerpflanzen (REQ-020)
- `acclimatization` — Eingewöhnungsphase nach Kauf/Transport (REQ-020)
- `repotting_recovery` — Erholungsphase nach Umtopfen (REQ-020)

Biologische Begründung: Düngung während Dormanz kann Salzstress verursachen, da die Pflanze keine aktive Nährstoffaufnahme betreibt. Die Wurzelaktivität ist auf Erhaltungsniveau, überschüssige Ionen akkumulieren im Substrat und können osmotischen Stress auslösen. Bei `acclimatization` und `repotting_recovery` sind die Wurzeln noch nicht etabliert — Dünger würde osmotischen Stress auf geschädigtes Wurzelgewebe ausüben.

**Adaptive Learning (Intervallanpassung):**
Das System lernt aus dem tatsächlichen Bestätigungsmuster des Nutzers:
- Wenn 3 aufeinanderfolgende Bestätigungen konsistent ≥1 Tag über dem Intervall liegen → Intervall um 1 Tag erhöhen
- Wenn 3 aufeinanderfolgende Bestätigungen konsistent ≥1 Tag unter dem Intervall liegen → Intervall um 1 Tag verringern
- Maximale Abweichung vom Species-Default: ±30% (Sicherheitsgrenze — verhindert, dass ein vergesslicher Nutzer das Gießintervall versehentlich auf 30 Tage "trainiert")
- Adaptive Learning ist pro Erinnerungstyp und pro Pflanze individuell

**Integration mit REQ-006 Task-System:**
Alle Erinnerungen werden als reguläre `Task`-Objekte gespeichert:
- `category: 'care_reminder'` (neue Task-Kategorie, ergänzt die bestehende Liste in REQ-006)
- `skill_level: 'beginner'`
- `stress_level: 'none'`
- `requires_photo: false`
- `requires_confirmation: false` (Ein-Tap genügt)
- Edge `has_task` verbindet Task mit PlantInstance (bestehende Edge-Collection aus REQ-006)

**Abgrenzung zu TaskTemplate:**
Care-Reminder-Tasks werden **direkt** vom `CareReminderEngine` erstellt — sie durchlaufen NICHT das `TaskTemplate`/`WorkflowTemplate`-System. Die `category: 'care_reminder'` existiert nur auf `:Task`-Ebene (freier `str` in REQ-006), nicht im `TaskTemplate.category`-Literal. Dies ist bewusste Vereinfachung: Pflegeerinnerungen brauchen keine Dependency-Chains, HST-Validation oder Workflow-Executions.

## 2. ArangoDB-Modellierung

### Nodes:

- **`:CareProfile`** — Pflegekonfiguration pro PlantInstance
  - Collection: `care_profiles`
  - Properties:
    - `care_style: Literal['tropical', 'succulent', 'orchid', 'calathea', 'herb_tropical', 'mediterranean', 'fern', 'cactus', 'custom']`
    - `watering_interval_days: int` (Default aus care_style-Preset, Sommer-Basiswert)
    - `winter_watering_multiplier: float` (Default aus care_style-Preset, z.B. 1.5 für tropical)
    - `fertilizing_interval_days: int`
    - `fertilizing_active_months: list[int]` (z.B. `[3, 4, 5, 6, 7, 8, 9, 10]` für Mär–Okt)
    - `repotting_interval_months: Optional[int]` (None = kein Umtopfen, z.B. bei annuellen Zierpflanzen)
    - `pest_check_interval_days: int`
    - `watering_method: Literal['soak', 'drench_and_drain', 'top_water', 'bottom_water']` (Default aus care_style-Preset)
    - `water_quality_hint: Optional[str]` (Default aus care_style-Preset, z.B. "Kalkarmes Wasser bevorzugt" für Orchideen)
    - `location_check_enabled: bool` (Default: `true`)
    - `location_check_months: Optional[dict]` (Konfigurierbare Monate für Standort-Checks, z.B. `{"winter_warning": 10, "spring_reminder": 3}`. Default: `null` = Oktober/März für NH, April/September für SH)
    - `humidity_check_enabled: bool` (Default aus care_style-Preset — `true` für `calathea`, `fern`, `tropical`; `false` für Rest)
    - `humidity_check_interval_days: int` (Default: 14 — nur relevant wenn `humidity_check_enabled`)
    - `adaptive_learning_enabled: bool` (Default: `true`)
    - `watering_interval_learned: Optional[float]` (Gelerntes Intervall, `null` = noch nicht adaptiert)
    - `fertilizing_interval_learned: Optional[float]`
    - `notes: Optional[str]` (Freitext-Notiz des Nutzers, z.B. "Mag kein Leitungswasser")
    - `created_at: datetime`
    - `updated_at: datetime`
    - `auto_generated: bool` (True wenn automatisch aus Species-Defaults erstellt)

- **`:CareConfirmation`** — Immutables Event-Log für Bestätigungen und Snoozes
  - Collection: `care_confirmations`
  - Properties:
    - `reminder_type: Literal['watering', 'fertilizing', 'repotting', 'pest_check', 'location_check', 'humidity_check', 'deadheading']`
    - `action: Literal['confirmed', 'snoozed', 'skipped']`
    - `confirmed_at: datetime`
    - `snooze_days: Optional[int]` (Default: 2, nur bei `action='snoozed'`)
    - `task_key: Optional[str]` (Referenz auf den bestätigten Task, wenn vorhanden)
    - `notes: Optional[str]` (Optionale Notiz, z.B. "Blätter leicht welk")
    - `interval_at_time: int` (Gültiges Intervall zum Zeitpunkt der Bestätigung — für Adaptive Learning)

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
- **`:OverwinteringProfile`** — Überwinterungs-Konfiguration pro PlantInstance
  - Collection: `overwintering_profiles`
  - Properties:
    - `hardiness_zone_min: Optional[str]` (Mindest-Winterhärtezone der Pflanze, z.B. "7b")
    - `hardiness_rating: Literal['hardy', 'needs_protection', 'frost_free', 'dig_and_store']`
      (hardy = draußen ohne Schutz, needs_protection = Vlies/Mulch/Anhäufeln,
       frost_free = ins Winterquartier (5-12°C), dig_and_store = Knollen ausgraben + einlagern)
    - `winter_action: Literal['none', 'mulch', 'fleece', 'earth_up', 'move_indoors', 'dig_store', 'wrap']`
      (Konkrete Schutzmaßnahme)
    - `winter_action_month: int` (Monat der Winterschutz-Aktion, z.B. 10 für Oktober)
    - `spring_action: Optional[Literal['uncover', 'move_outdoors', 'replant', 'prune', 'harden_off']]`
      (Frühlings-Aktion: Abdeckung entfernen / rausstellen / neu pflanzen / schneiden / abhärten)
    - `spring_action_month: Optional[int]` (Monat der Frühlings-Aktion, z.B. 3 für März)
    - `winter_quarter_key: Optional[str]` (Referenz auf Location = Winterquartier)
    - `winter_quarter_temp_min: Optional[float]` (Mindesttemperatur Winterquartier in °C)
    - `winter_quarter_temp_max: Optional[float]` (Maximaltemperatur Winterquartier)
    - `winter_quarter_light: Optional[Literal['bright', 'semi_bright', 'dark']]`
    - `winter_watering: Optional[Literal['none', 'minimal', 'reduced', 'normal']]`
      (Gießverhalten im Winter: none = Knollen trocken lagern, minimal = alle 4-6 Wochen, etc.)
    - `storage_medium: Optional[str]` (Lagermedium für Knollen: "Sand", "Torf", "Zeitungspapier", "luftig aufgehängt")
    - `storage_check_interval_days: Optional[int]` (Kontrollintervall für eingelagerte Knollen, z.B. 30)
    - `tuber_status: Optional[Literal['planted', 'growing', 'dig_pending', 'drying', 'stored', 'pre_sprouting']]`
      (Aktueller Status im Knollen-/Zwiebel-Jahreszyklus — nur für `hardiness_rating == 'dig_and_store'`)
    - `notes: Optional[str]`
    - `auto_generated: bool` (True wenn automatisch aus Species-Defaults erstellt)
    - `created_at: datetime`
    - `updated_at: datetime`

### Edges:

```
has_care_profile:  plant_instances → care_profiles       (1:1, PlantInstance hat CareProfile)
confirms_care:     care_confirmations → care_profiles    (N:1, Bestätigung gehört zu Profil)
care_event_for:    care_confirmations → plant_instances   (N:1, Bestätigung bezieht sich auf Pflanze)
```

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
```
has_overwintering_profile:  plant_instances → overwintering_profiles  (1:1)
overwinters_at:             overwintering_profiles → locations         (N:1, Winterquartier)
```

### Indizes:

```
care_profiles:
  - PERSISTENT INDEX on [auto_generated]

care_confirmations:
  - PERSISTENT INDEX on [reminder_type, confirmed_at]
  - PERSISTENT INDEX on [action]

has_care_profile:
  - PERSISTENT INDEX on [_from] UNIQUE  (jede PlantInstance maximal ein CareProfile)
```

### AQL-Beispiellogik:

**Fällige Erinnerungen für alle Pflanzen (Dashboard-Query):**
```aql
LET today = DATE_ISO8601(DATE_NOW())
LET current_month = DATE_MONTH(DATE_NOW())

FOR plant IN plant_instances
  // Hole CareProfile
  LET profile = FIRST(
    FOR cp IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['has_care_profile'] }
      RETURN cp
  )
  FILTER profile != null

  // Hole aktuelle Phase
  LET phase = FIRST(
    FOR p IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['current_phase'] }
      RETURN p
  )

  // Letzte Bestätigungen pro Typ
  LET last_watering = FIRST(
    FOR cc IN care_confirmations
      FILTER cc.reminder_type == 'watering'
      FOR edge IN care_event_for
        FILTER edge._from == cc._id AND edge._to == plant._id
        FILTER cc.action == 'confirmed'
        SORT cc.confirmed_at DESC
        LIMIT 1
        RETURN cc
  )
  LET last_fertilizing = FIRST(
    FOR cc IN care_confirmations
      FILTER cc.reminder_type == 'fertilizing'
      FOR edge IN care_event_for
        FILTER edge._from == cc._id AND edge._to == plant._id
        FILTER cc.action == 'confirmed'
        SORT cc.confirmed_at DESC
        LIMIT 1
        RETURN cc
  )

  // Berechne Fälligkeit (mit saisonaler Anpassung, hemisphärenabhängig)
  LET site_hemisphere = FIRST(
    FOR s IN sites
      FOR loc IN locations FILTER loc._key == plant.location_key
        FILTER s._key == loc.site_key
        RETURN s.hemisphere
  ) ?? 'northern'
  LET winter_months = site_hemisphere == 'southern' ? [5, 6, 7, 8] : [11, 12, 1, 2]
  LET is_winter = current_month IN winter_months
  LET watering_base = profile.watering_interval_learned != null
    ? profile.watering_interval_learned
    : profile.watering_interval_days
  LET watering_interval_seasonal = is_winter
    ? ROUND(watering_base * profile.winter_watering_multiplier)
    : watering_base
  // Acclimatization-Phase: Gießintervall × 1.3 (Wurzeln noch nicht etabliert)
  LET is_acclimatization = phase != null AND phase.name == 'acclimatization'
  LET watering_interval = is_acclimatization
    ? ROUND(watering_interval_seasonal * 1.3)
    : watering_interval_seasonal
  LET days_since_watering = last_watering != null
    ? DATE_DIFF(last_watering.confirmed_at, DATE_NOW(), 'day')
    : 999
  LET watering_due = days_since_watering >= watering_interval

  LET fertilizing_interval = profile.fertilizing_interval_learned != null
    ? profile.fertilizing_interval_learned
    : profile.fertilizing_interval_days
  LET days_since_fertilizing = last_fertilizing != null
    ? DATE_DIFF(last_fertilizing.confirmed_at, DATE_NOW(), 'day')
    : 999
  LET fertilizing_in_season = current_month IN profile.fertilizing_active_months
  LET dormancy_phases = ['dormancy', 'senescence', 'hardening_off', 'maintenance', 'acclimatization', 'repotting_recovery']
  LET phase_allows_fertilizing = phase == null OR phase.name NOT IN dormancy_phases
  LET fertilizing_due = days_since_fertilizing >= fertilizing_interval
    AND fertilizing_in_season
    AND phase_allows_fertilizing

  // Humidity Check: Nur in Heizperiode und nur für feuchtigkeitsempfindliche Presets
  LET humidity_due = profile.humidity_check_enabled
    AND is_winter
    AND (
      LET last_humidity = FIRST(
        FOR cc IN care_confirmations
          FILTER cc.reminder_type == 'humidity_check'
          FOR edge IN care_event_for
            FILTER edge._from == cc._id AND edge._to == plant._id
            FILTER cc.action == 'confirmed'
            SORT cc.confirmed_at DESC
            LIMIT 1
            RETURN cc
      )
      LET days_since_humidity = last_humidity != null
        ? DATE_DIFF(last_humidity.confirmed_at, DATE_NOW(), 'day')
        : 999
      RETURN days_since_humidity >= profile.humidity_check_interval_days
    )

  // Dringlichkeit: Tage überfällig
  LET watering_urgency = days_since_watering - watering_interval
  LET fertilizing_urgency = days_since_fertilizing - fertilizing_interval

  FILTER watering_due OR fertilizing_due OR humidity_due

  LET species = FIRST(
    FOR s IN 1..1 INBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['has_instance'] }
      RETURN s
  )

  SORT MAX(watering_urgency, fertilizing_urgency) DESC

  RETURN {
    plant_key: plant._key,
    plant_name: plant.display_name,
    species_name: species.common_names[0],
    location: plant.location_name,
    reminders: APPEND(
      watering_due ? [{ type: 'watering', days_overdue: watering_urgency, watering_method: profile.watering_method, water_quality_hint: profile.water_quality_hint }] : [],
      fertilizing_due ? [{ type: 'fertilizing', days_overdue: fertilizing_urgency }] : [],
      humidity_due ? [{ type: 'humidity_check', days_overdue: 0 }] : []
    )
  }
```

<!-- Quelle: Outdoor-Garden-Planner Review G-002 -->
### Winterhärte-Ampel (Hardiness Traffic Light)

Das System berechnet pro PlantInstance eine Winterhärte-Ampel basierend auf:
1. `Species.frost_sensitivity` (REQ-001)
2. `Site.climate_zone` (REQ-002)
3. `OverwinteringProfile.hardiness_zone_min`

**Ampel-Logik:**
- **Winterhart (grün):** `frost_sensitivity == 'hardy'` UND `species.hardiness_zone_min <= site.climate_zone` — Kein Handlungsbedarf. **Keine Winterschutz-Erinnerungen generieren.**
- **Schutz nötig (gelb):** `frost_sensitivity == 'half_hardy'` ODER Hardiness-Zone knapp (Differenz <= 1 Zone) — Mulch/Vlies/Anhäufeln empfohlen
- **Muss rein (rot):** `frost_sensitivity == 'tender'` ODER Hardiness-Zone deutlich zu niedrig (Differenz > 1) — Winterquartier oder Ausgraben

<!-- Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->
**Winterschutz-Guard für frostharte Pflanzen:**
Die `CareReminderEngine` MUSS vor der Generierung von Winterschutz-Erinnerungen (`winter_protection`, `spring_uncover`, `tuber_dig`, `storage_check`) prüfen, ob `Species.frost_sensitivity == 'hardy'`. Ist dies der Fall, werden **keine** Winterschutz-Erinnerungen generiert. Dies verhindert irreführende Erinnerungen für frostharte Pflanzen wie Stiefmütterchen (Viola), Hornveilchen, Primeln oder Schneeglöckchen.

**FAMILY_CARE_MAP-Erweiterung für Zierpflanzen:**
Die Backend-Implementation (`care_reminder_engine.py`) MUSS um folgende Einträge erweitert werden:

| Familie | Care-Style | Begründung |
|---------|-----------|-----------|
| `Violaceae` | `outdoor_annual_ornamental` | Stiefmütterchen — frosthart, annuelle Balkonkultur. **Ausnahme:** *Viola cornuta* (Hornveilchen) ist eine winterharte Staude — für überwinterte Exemplare `mediterranean`-Preset verwenden (Rückschnitt nach Hauptblüte, Umtopfen alle 2–3 Jahre). |
| `Primulaceae` | `outdoor_annual_ornamental` | Primeln — frosthart, Frühblüher |
| `Geraniaceae` | `outdoor_annual_ornamental` | Geranien — frostempfindlich, annuelle Balkonkultur. **Hinweis Überwinterung (AB-003):** Werden *Pelargonium zonale* überwintert statt entsorgt, benötigen sie ein OverwinteringProfile (5–10°C, hell, reduziertes Gießen Nov–Feb, Rückschnitt im Frühjahr). Das `outdoor_annual_ornamental`-Preset gilt nur für den jährlichen Neukauf-Use-Case. |
| `Campanulaceae` | `outdoor_annual_ornamental` | Lobelien — annuelle Balkonkultur |
| `Balsaminaceae` | `outdoor_annual_ornamental` | Fleißiges Lieschen — Schattenbalkon |

<!-- Quelle: Agrarbiologie-Review AB-004, AB-016, 2026-03 -->
Hinweis: Die `auto_generate_profile()`-Methode nutzt `FAMILY_CARE_MAP` als Fallback. Für Outdoor-Zierpflanzen mit `traits=['ornamental']` (lowercase, konsistent mit Cultivar-Validator) UND `is_indoor == false` am Standort SOLL der `outdoor_annual_ornamental`-Preset bevorzugt werden, auch wenn die Familie nicht in der Map ist.

**Deadheading-Guard für Self-Cleaning-Sorten (AB-016):**
Cultivare mit `traits: ['self_cleaning']` (z.B. Surfinia-Petunien, Calibrachoa 'Million Bells') sollen KEINE Deadheading-Erinnerungen erhalten, auch wenn der Preset `deadheading_enabled: True` setzt. Die `CareReminderEngine` prüft vor der Deadheading-Generierung: `if 'self_cleaning' in cultivar.traits: skip deadheading`.
<!-- /Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->

**Dashboard-Widget "Winterschutz-Übersicht":**
Ab September zeigt das Dashboard ein Widget mit:
- Anzahl Pflanzen pro Ampelfarbe (z.B. "42 grün / 18 gelb / 7 rot")
- Liste der rot-Pflanzen mit konkreter Handlungsanweisung
- Countdown "Tage bis erster Frost" (basierend auf historischem Durchschnitt der Klimazone oder Wetter-API wenn verfügbar, REQ-005)
- Checkliste der erledigten/offenen Winterschutz-Maßnahmen

**Knollen-/Zwiebel-Zyklus:**
Für `hardiness_rating == 'dig_and_store'` (Dahlien, Gladiolen, Canna) bildet das System den kompletten Jahreszyklus ab:

| Monat (NH) | Status | Aktion | Erinnerung |
|-----------|--------|--------|------------|
| Mai | `planted` | Auspflanzen nach Eisheiligen | "Dahlienknollen einpflanzen" |
| Jun–Sep | `growing` | Normale Pflege | Standard Care-Reminders |
| Okt | `dig_pending` | Vor erstem Frost ausgraben | "3 Dahlien ausgraben! Frost in 5 Tagen" |
| Okt | `drying` | 1-2 Wochen kopfüber trocknen | "Dahlien sind trocken — einlagern" |
| Nov | `stored` | Frostfrei einlagern (5-10°C, Sand/Torf) | — |
| Nov–Mär | `stored` | Regelmäßig kontrollieren | "Knollen kontrollieren (Fäulnis, Austrocknung)" |
| Apr | `pre_sprouting` | Optional: Vorziehen bei 15-18°C | "Dahlienknollen vorziehen" |
| Mai | `planted` (Zyklus wiederholt) | Zyklus wiederholt sich | — |

Status-Feld auf OverwinteringProfile:
- `tuber_status: Optional[Literal['planted', 'growing', 'dig_pending', 'drying', 'stored', 'pre_sprouting']]`

## 3. Technische Umsetzung (Python)

### Pydantic-Modelle:

```python
from datetime import datetime, date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

# --- Care Style Presets ---
# Alle Presets definieren Monate für die Nordhalbkugel.
# Bei Site.hemisphere == 'southern' verschiebt CareReminderEngine._adjust_months_for_hemisphere()
# alle fertilizing_active_months um +6 Monate (z.B. Mär(3)→Sep(9), Mai(5)→Nov(11)).

CARE_STYLE_PRESETS: dict[str, dict] = {
    'tropical': {
        'watering_interval_days': 7,
        'winter_watering_multiplier': 1.5,
        'watering_method': 'top_water',
        'water_quality_hint': None,
        'fertilizing_interval_days': 14,
        'fertilizing_active_months': [3, 4, 5, 6, 7, 8, 9, 10],
        'repotting_interval_months': 18,
        'pest_check_interval_days': 14,
        'humidity_check_enabled': True,
        'humidity_check_interval_days': 14,
    },
    'succulent': {
        'watering_interval_days': 14,
        'winter_watering_multiplier': 2.5,
        'watering_method': 'drench_and_drain',
        'water_quality_hint': None,
        'fertilizing_interval_days': 30,
        'fertilizing_active_months': [4, 5, 6, 7, 8, 9],
        'repotting_interval_months': 24,
        'pest_check_interval_days': 21,
        'humidity_check_enabled': False,
        'humidity_check_interval_days': 14,
    },
    'orchid': {
        'watering_interval_days': 7,
        'winter_watering_multiplier': 1.5,
        'watering_method': 'soak',
        'water_quality_hint': 'pages.care.waterQuality.orchid',  # i18n-Key
        'fertilizing_interval_days': 14,
        'fertilizing_active_months': [3, 4, 5, 6, 7, 8, 9, 10],
        'repotting_interval_months': 24,
        'pest_check_interval_days': 14,
        'humidity_check_enabled': True,
        'humidity_check_interval_days': 14,
    },
    'calathea': {
        'watering_interval_days': 5,
        'winter_watering_multiplier': 1.3,
        'watering_method': 'top_water',
        'water_quality_hint': 'pages.care.waterQuality.calathea',  # i18n-Key
        'fertilizing_interval_days': 14,
        'fertilizing_active_months': [3, 4, 5, 6, 7, 8, 9],
        'repotting_interval_months': 18,  # Calathea/Maranten sind langsam wachsend und wurzelstörungsempfindlich
        'pest_check_interval_days': 7,
        'humidity_check_enabled': True,
        'humidity_check_interval_days': 7,  # Calatheen: höchste Empfindlichkeit gegen trockene Luft
    },
    'herb_tropical': {
        'watering_interval_days': 3,
        'winter_watering_multiplier': 1.5,
        'watering_method': 'top_water',
        'water_quality_hint': None,
        'fertilizing_interval_days': 21,
        'fertilizing_active_months': [3, 4, 5, 6, 7, 8, 9, 10],
        'repotting_interval_months': 12,
        'pest_check_interval_days': 14,
        'humidity_check_enabled': False,
        'humidity_check_interval_days': 14,
    },
    'mediterranean': {
        'watering_interval_days': 10,
        'winter_watering_multiplier': 2.0,
        'watering_method': 'drench_and_drain',
        'water_quality_hint': None,
        'fertilizing_interval_days': 30,
        'fertilizing_active_months': [4, 5, 6, 7, 8, 9],
        'repotting_interval_months': 24,
        'pest_check_interval_days': 21,
        'humidity_check_enabled': False,
        'humidity_check_interval_days': 14,
    },
    'fern': {
        'watering_interval_days': 4,
        'winter_watering_multiplier': 1.3,
        'watering_method': 'top_water',
        'water_quality_hint': 'pages.care.waterQuality.fern',  # i18n-Key
        'fertilizing_interval_days': 21,
        'fertilizing_active_months': [3, 4, 5, 6, 7, 8, 9, 10],
        'repotting_interval_months': 12,
        'pest_check_interval_days': 14,
        'humidity_check_enabled': True,
        'humidity_check_interval_days': 7,  # Farne: hoher Luftfeuchtebedarf
    },
    'cactus': {
        'watering_interval_days': 21,
        'winter_watering_multiplier': 3.0,
        'watering_method': 'drench_and_drain',
        'water_quality_hint': None,
        'fertilizing_interval_days': 30,
        'fertilizing_active_months': [5, 6, 7, 8],
        'repotting_interval_months': 36,
        'pest_check_interval_days': 30,
        'humidity_check_enabled': False,
        'humidity_check_interval_days': 14,
    },
    # Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03
    # Quelle: Agrarbiologie-Review AB-005, AB-014, AB-017, 2026-03
    'outdoor_annual_ornamental': {
        'watering_interval_days': 2,       # Balkonkästen trocknen schnell aus (Sommer, Jun–Aug)
        'winter_watering_multiplier': 1.5,  # Frühjahr/Herbst: alle 3 Tage (niedrigere Temperaturen)
        'watering_method': 'top_water',
        'water_quality_hint': None,         # Leitungswasser OK für Stiefmütterchen, Petunien etc.
        'fertilizing_interval_days': 14,    # Alle 2 Wochen Flüssigdünger
        'fertilizing_active_months': [3, 4, 5, 6, 7, 8, 9],  # März–September (AB-017: inkl. März für Voranzucht-Sämlinge)
        'repotting_interval_months': None,  # Kein Umtopfen (annuelle Kultur) — AB-005: None statt 0
        'pest_check_interval_days': 14,     # Blattläuse, Weiße Fliege, Grauschimmel
        'humidity_check_enabled': False,    # Outdoor — Luftfeuchtigkeit irrelevant
        'humidity_check_interval_days': 14,
        'deadheading_enabled': True,        # Verblühtes entfernen verlängert Blütezeit
        'deadheading_interval_days': 5,     # Alle 5 Tage kontrollieren (AB-016: Cultivar.self_cleaning überschreibt)
        'deadheading_active_phases': ['flowering'],  # Nur während der Blüte
    },
}

CareStyleType = Literal['tropical', 'succulent', 'orchid', 'calathea', 'herb_tropical', 'mediterranean', 'fern', 'cactus', 'outdoor_annual_ornamental', 'custom']
ReminderType = Literal['watering', 'fertilizing', 'repotting', 'pest_check', 'location_check', 'humidity_check', 'deadheading']
ConfirmAction = Literal['confirmed', 'snoozed', 'skipped']

# --- Dormancy Phases (no fertilizing) ---

DORMANCY_PHASES = frozenset([
    'dormancy',             # Winterruhe (REQ-003)
    'senescence',           # Alterungsphase (REQ-003)
    'hardening_off',        # Abhärtung (REQ-003)
    'maintenance',          # Winter-Erhaltungspflege Zimmerpflanzen (REQ-020)
    'acclimatization',      # Eingewöhnung nach Kauf/Transport (REQ-020)
    'repotting_recovery',   # Erholung nach Umtopfen (REQ-020)
])


WateringMethod = Literal['soak', 'drench_and_drain', 'top_water', 'bottom_water']


class CareProfile(BaseModel):
    """Pflegekonfiguration für eine einzelne PlantInstance."""

    care_style: CareStyleType
    watering_interval_days: int = Field(ge=1, le=90)
    winter_watering_multiplier: float = Field(
        ge=1.0, le=5.0, default=1.5,
        description="Multiplikator für Gießintervall in Wintermonaten (Nov–Feb NH / Mai–Aug SH — wird aus Site.hemisphere abgeleitet)"
    )
    watering_method: WateringMethod = Field(
        default='top_water',
        description="Gießmethode (aus care_style-Preset). Wird in der ReminderCard als Anleitungstext angezeigt."
    )
    water_quality_hint: Optional[str] = Field(
        None,
        description="i18n-Key für Wasserqualitäts-Hinweis (z.B. kalkarm für Calathea). None = Leitungswasser OK."
    )
    fertilizing_interval_days: int = Field(ge=7, le=90)
    fertilizing_active_months: list[int] = Field(
        min_length=1, max_length=12,
        description="Monate (1–12) in denen gedüngt werden soll"
    )
    repotting_interval_months: Optional[int] = Field(None, ge=6, le=60)  # AB-005: None = kein Umtopfen (annuelle Kultur)
    pest_check_interval_days: int = Field(ge=3, le=90)
    location_check_enabled: bool = True
    location_check_months: Optional[dict] = Field(
        None,
        description="Konfigurierbare Monate für Standort-Checks. Format: {'winter_warning': 10, 'spring_reminder': 3}. "
                    "None = Default (Okt/Mär für NH, Apr/Sep für SH)."
    )
    humidity_check_enabled: bool = Field(
        default=False,
        description="Luftfeuchte-Erinnerungen (Default aus care_style-Preset — true für calathea, fern, tropical)"
    )
    humidity_check_interval_days: int = Field(
        default=14, ge=3, le=90,
        description="Intervall für Luftfeuchte-Checks (nur aktiv in Heizperiode Okt–Mär NH / Apr–Sep SH)"
    )
    # Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03
    deadheading_enabled: bool = Field(
        default=False,
        description="Verblühtes-Entfernen-Erinnerungen (Default aus care_style-Preset — true für outdoor_annual_ornamental). "
                    "Nur aktiv wenn Species.traits 'ornamental' enthält UND aktuelle Phase 'flowering' ist."
    )
    deadheading_interval_days: int = Field(
        default=5, ge=2, le=30,
        description="Intervall für Deadheading-Checks in Tagen. Standard 5 Tage für Stiefmütterchen/Petunien."
    )
    deadheading_active_phases: list[str] = Field(
        default=['flowering'],
        description="Phasen in denen Deadheading-Erinnerungen generiert werden."
    )
    # /Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03
    adaptive_learning_enabled: bool = True
    watering_interval_learned: Optional[float] = Field(
        None, ge=1.0, le=90.0,
        description="Adaptiv gelerntes Gießintervall (None = noch nicht adaptiert)"
    )
    fertilizing_interval_learned: Optional[float] = Field(
        None, ge=7.0, le=90.0,
    )
    notes: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    auto_generated: bool = False

    @field_validator('fertilizing_active_months')
    @classmethod
    def validate_months(cls, v: list[int]) -> list[int]:
        if not all(1 <= m <= 12 for m in v):
            raise ValueError("Alle Monate müssen zwischen 1 und 12 liegen")
        return sorted(set(v))

    @classmethod
    def from_care_style(cls, care_style: CareStyleType) -> 'CareProfile':
        """Erstellt CareProfile aus einem Preset."""
        if care_style == 'custom':
            # Custom startet mit tropical-Defaults
            preset = CARE_STYLE_PRESETS['tropical'].copy()
        else:
            preset = CARE_STYLE_PRESETS[care_style].copy()
        return cls(care_style=care_style, auto_generated=True, **preset)


class CareProfileUpdate(BaseModel):
    """Partielle Aktualisierung des CareProfile."""
    care_style: Optional[CareStyleType] = None
    watering_interval_days: Optional[int] = Field(None, ge=1, le=90)
    winter_watering_multiplier: Optional[float] = Field(None, ge=1.0, le=5.0)
    watering_method: Optional[WateringMethod] = None
    water_quality_hint: Optional[str] = None
    fertilizing_interval_days: Optional[int] = Field(None, ge=7, le=90)
    fertilizing_active_months: Optional[list[int]] = None
    repotting_interval_months: Optional[int] = Field(None, ge=6, le=60)
    pest_check_interval_days: Optional[int] = Field(None, ge=3, le=90)
    location_check_enabled: Optional[bool] = None
    location_check_months: Optional[dict] = None
    humidity_check_enabled: Optional[bool] = None
    humidity_check_interval_days: Optional[int] = Field(None, ge=3, le=90)
    adaptive_learning_enabled: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)


class CareConfirmation(BaseModel):
    """Immutables Event: Nutzer hat eine Pflegeaktion bestätigt/verschoben."""

    reminder_type: ReminderType
    action: ConfirmAction
    confirmed_at: datetime = Field(default_factory=datetime.utcnow)
    snooze_days: Optional[int] = Field(None, ge=1, le=7)
    task_key: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    interval_at_time: int = Field(
        ge=1,
        description="Gültiges Intervall zum Zeitpunkt der Bestätigung (für Adaptive Learning)"
    )

    @field_validator('snooze_days')
    @classmethod
    def validate_snooze(cls, v: Optional[int], info) -> Optional[int]:
        if info.data.get('action') == 'snoozed' and v is None:
            return 2  # Default Snooze: 2 Tage
        return v


class CareDashboardEntry(BaseModel):
    """Ein Eintrag im Pflege-Dashboard (fällige Erinnerung)."""

    plant_key: str
    plant_name: str
    species_name: Optional[str] = None
    location_name: Optional[str] = None
    care_style: CareStyleType
    reminder_type: ReminderType
    days_overdue: int = Field(
        description="Tage über dem Intervall. 0 = heute fällig, >0 = überfällig, <0 = noch nicht fällig"
    )
    urgency: Literal['overdue', 'due_today', 'upcoming']
    interval_days: int
    last_confirmed_at: Optional[datetime] = None
    instruction_i18n_key: str = Field(
        description="i18n-Schlüssel für die natürlichsprachliche Anweisung"
    )
    watering_method: Optional[WateringMethod] = Field(
        None,
        description="Gießmethode — nur bei reminder_type == 'watering' befüllt"
    )
    water_quality_hint: Optional[str] = Field(
        None,
        description="i18n-Key für Wasserqualitäts-Hinweis — nur bei 'watering' und wenn relevant"
    )
    repotting_hint_i18n_key: Optional[str] = Field(
        None,
        description="i18n-Key für Symptom-Check-Hinweis — nur bei 'repotting'"
    )


class CareConfirmRequest(BaseModel):
    """Request für Ein-Tap-Bestätigung."""
    reminder_type: ReminderType
    notes: Optional[str] = Field(None, max_length=500)


class CareSnoozeRequest(BaseModel):
    """Request für Snooze (Verschiebung)."""
    reminder_type: ReminderType
    snooze_days: int = Field(default=2, ge=1, le=7)
```

### Logik-Anforderungen:

**1. CareReminderEngine — Generierungslogik + Adaptive Learning:**

```python
from datetime import datetime, date, timedelta
from typing import Optional

class CareReminderEngine:
    """
    Kernlogik für Pflegeerinnerungen:
    - Generiert fällige Erinnerungen basierend auf CareProfile-Intervallen
    - Berechnet Dringlichkeit (overdue / due_today / upcoming)
    - Adaptiert Intervalle basierend auf Bestätigungsmuster
    - Prüft Dünge-Saisonalität und Phasen-Guard
    """

    # Adaptive Learning: Anzahl konsistenter Signale für Anpassung
    ADAPTIVE_SIGNAL_THRESHOLD = 3
    # Maximale Abweichung vom Basis-Intervall (30%)
    ADAPTIVE_MAX_DEVIATION = 0.30
    # Tage Vorschau für "upcoming" Erinnerungen
    UPCOMING_WINDOW_DAYS = 2

    def is_reminder_due(
        self,
        reminder_type: ReminderType,
        profile: CareProfile,
        last_confirmed_at: Optional[datetime],
        current_phase: Optional[str] = None,
    ) -> tuple[bool, int]:
        """
        Prüft ob eine Erinnerung fällig ist.

        Args:
            reminder_type: Typ der Erinnerung
            profile: CareProfile der Pflanze
            last_confirmed_at: Zeitpunkt der letzten Bestätigung
            current_phase: Aktuelle Wachstumsphase der Pflanze

        Returns:
            (is_due, days_overdue) — days_overdue kann negativ sein (noch nicht fällig)
        """
        interval = self._get_effective_interval(
            reminder_type, profile, current_phase=current_phase,
        )
        if interval is None:
            return False, 0

        # Sonderfall: Saisonale Erinnerungen
        if reminder_type == 'location_check':
            return self._check_location_reminder(profile)

        # Dünge-Guard: Saison + Phase prüfen
        if reminder_type == 'fertilizing':
            if not self._is_fertilizing_allowed(profile, current_phase):
                return False, 0

        # Intervall-basierte Prüfung
        if last_confirmed_at is None:
            return True, 999  # Nie bestätigt → sofort fällig

        days_since = (datetime.utcnow() - last_confirmed_at).days
        days_overdue = days_since - interval
        is_due = days_overdue >= -self.UPCOMING_WINDOW_DAYS

        return is_due, days_overdue

    # Winter-Monate nach Hemisphäre (aus Site.hemisphere abgeleitet)
    WINTER_MONTHS_NORTHERN = frozenset([11, 12, 1, 2])
    WINTER_MONTHS_SOUTHERN = frozenset([5, 6, 7, 8])
    # Offset für fertilizing_active_months bei Südhalbkugel: +6 Monate (mod 12)
    HEMISPHERE_MONTH_OFFSET = 6

    @staticmethod
    def _get_winter_months(hemisphere: str = 'northern') -> frozenset[int]:
        """Gibt Winter-Monate basierend auf Hemisphäre zurück."""
        if hemisphere == 'southern':
            return CareReminderEngine.WINTER_MONTHS_SOUTHERN
        return CareReminderEngine.WINTER_MONTHS_NORTHERN

    @staticmethod
    def _adjust_months_for_hemisphere(months: list[int], hemisphere: str) -> list[int]:
        """Verschiebt Monatslisten um 6 Monate für Südhalbkugel.

        Presets werden für Nordhalbkugel definiert. Bei hemisphere='southern'
        werden alle Monate um +6 (mod 12) verschoben, z.B. März(3) → September(9).
        """
        if hemisphere == 'northern':
            return months
        return [((m + 5) % 12) + 1 for m in months]

    # Acclimatization-Faktor: Gießintervall × 1.3 während Eingewöhnung
    ACCLIMATIZATION_WATERING_FACTOR = 1.3

    def _get_effective_interval(
        self,
        reminder_type: ReminderType,
        profile: CareProfile,
        hemisphere: str = 'northern',
        current_phase: Optional[str] = None,
    ) -> Optional[int]:
        """Gibt das effektive Intervall zurück (gelernt > konfiguriert, saisonal angepasst).

        Sonderbehandlung acclimatization-Phase (U-005):
        Während der Eingewöhnung nach Kauf/Umtopfen wird das Gießintervall
        um Faktor 1.3 verlängert. Biologische Begründung: Wurzeln sind durch
        Transport/Umtopfen geschädigt, reduzierte Wasseraufnahmekapazität,
        Substrat beim Kauf oft bereits durchfeuchtet.
        """
        if reminder_type == 'watering':
            base = profile.watering_interval_learned or profile.watering_interval_days
            if date.today().month in self._get_winter_months(hemisphere):
                interval = round(base * profile.winter_watering_multiplier)
            else:
                interval = round(base)
            # Acclimatization: Gießintervall verlängern (Wurzeln noch nicht etabliert)
            if current_phase == 'acclimatization':
                interval = round(interval * self.ACCLIMATIZATION_WATERING_FACTOR)
            return interval
        elif reminder_type == 'fertilizing':
            if profile.fertilizing_interval_learned is not None:
                return round(profile.fertilizing_interval_learned)
            return profile.fertilizing_interval_days
        elif reminder_type == 'repotting':
            if profile.repotting_interval_months is None:
                return None  # AB-005: Kein Umtopfen (annuelle Kultur) — keine Erinnerung generieren
            return profile.repotting_interval_months * 30  # Approximation
        elif reminder_type == 'pest_check':
            return profile.pest_check_interval_days
        elif reminder_type == 'humidity_check':
            if not profile.humidity_check_enabled:
                return None
            # Nur in Heizperiode (= Winter-Monate) aktiv
            if date.today().month not in self._get_winter_months(hemisphere):
                return None
            return profile.humidity_check_interval_days
        elif reminder_type == 'location_check':
            return None  # Saisonal, kein Intervall
        return None

    def _is_fertilizing_allowed(
        self,
        profile: CareProfile,
        current_phase: Optional[str],
    ) -> bool:
        """Prüft ob Düngung erlaubt ist (Saison + Phase)."""
        current_month = date.today().month
        if current_month not in profile.fertilizing_active_months:
            return False
        if current_phase and current_phase in DORMANCY_PHASES:
            return False
        return True

    def _check_location_reminder(
        self,
        profile: CareProfile,
        hemisphere: str = 'northern',
    ) -> tuple[bool, int]:
        """
        Saisonale Standort-Checks (hemisphärenabhängig, konfigurierbar).

        Die Monate können pro CareProfile über `location_check_months` konfiguriert
        werden. Falls nicht gesetzt, gelten die Defaults:
        - Nordhalbkugel: Oktober → Winterquartier, März → Frühlings-Umstellung
        - Südhalbkugel: April → Winterquartier, September → Frühlings-Umstellung

        Hinweis (P-001): Feste Datumswerte sind eine Vereinfachung. In Zukunft
        könnte eine Integration mit Wetterdaten (Frost-Warnung < 3°C oder
        7-Tage-Durchschnitt < 10°C) eine präzisere Auslösung ermöglichen.
        Die konfigurierbaren Monate erlauben dem Nutzer, die Werte an seine
        Klimazone anzupassen (z.B. September in Südbayern, November in Köln).
        """
        if not profile.location_check_enabled:
            return False, 0
        today = date.today()

        # Konfigurierbare Monate oder Default
        if profile.location_check_months:
            winter_warning_month = profile.location_check_months.get(
                'winter_warning', 10 if hemisphere == 'northern' else 4
            )
            spring_reminder_month = profile.location_check_months.get(
                'spring_reminder', 3 if hemisphere == 'northern' else 9
            )
        else:
            winter_warning_month = 10 if hemisphere == 'northern' else 4
            spring_reminder_month = 3 if hemisphere == 'northern' else 9

        if today.month == winter_warning_month and today.day <= 15:
            return True, 0
        if today.month == spring_reminder_month and today.day <= 15:
            return True, 0
        return False, 0

    def calculate_urgency(self, days_overdue: int) -> str:
        """Bestimmt die Dringlichkeitsstufe."""
        if days_overdue > 0:
            return 'overdue'
        elif days_overdue >= -self.UPCOMING_WINDOW_DAYS:
            return 'due_today'
        else:
            return 'upcoming'

    def adapt_interval(
        self,
        reminder_type: ReminderType,
        profile: CareProfile,
        recent_confirmations: list[CareConfirmation],
    ) -> Optional[float]:
        """
        Adaptive Learning: Passt Intervall basierend auf Bestätigungsmuster an.

        Algorithmus:
        1. Berechne tatsächliche Intervalle aus den letzten N Bestätigungen
        2. Prüfe ob N konsistente Signale in eine Richtung vorliegen
        3. Passe um 1 Tag an, maximal ±30% vom Basis-Intervall

        Args:
            reminder_type: Typ der Erinnerung
            profile: Aktuelles CareProfile
            recent_confirmations: Letzte Bestätigungen (nur 'confirmed', sortiert nach Datum)

        Returns:
            Neues Intervall oder None wenn keine Anpassung nötig
        """
        if not profile.adaptive_learning_enabled:
            return None
        if len(recent_confirmations) < self.ADAPTIVE_SIGNAL_THRESHOLD + 1:
            return None

        # Berechne tatsächliche Intervalle zwischen aufeinanderfolgenden Bestätigungen
        actual_intervals = []
        for i in range(1, len(recent_confirmations)):
            delta = (
                recent_confirmations[i - 1].confirmed_at
                - recent_confirmations[i].confirmed_at
            ).days
            if delta > 0:
                actual_intervals.append(delta)

        if len(actual_intervals) < self.ADAPTIVE_SIGNAL_THRESHOLD:
            return None

        # Prüfe die letzten N Intervalle auf konsistente Abweichung
        base_interval = self._get_base_interval(reminder_type, profile)
        current_effective = self._get_effective_interval(reminder_type, profile)
        if base_interval is None or current_effective is None:
            return None

        recent_n = actual_intervals[:self.ADAPTIVE_SIGNAL_THRESHOLD]
        deviations = [interval - current_effective for interval in recent_n]

        # Alle Abweichungen in gleiche Richtung und mindestens 1 Tag?
        all_above = all(d >= 1 for d in deviations)
        all_below = all(d <= -1 for d in deviations)

        if not (all_above or all_below):
            return None

        # Anpassung um 1 Tag
        adjustment = 1 if all_above else -1
        new_interval = current_effective + adjustment

        # Sicherheitsgrenze: max ±30% vom Basis-Intervall
        min_allowed = base_interval * (1 - self.ADAPTIVE_MAX_DEVIATION)
        max_allowed = base_interval * (1 + self.ADAPTIVE_MAX_DEVIATION)
        new_interval = max(min_allowed, min(max_allowed, new_interval))

        # Mindestens 1 Tag
        new_interval = max(1.0, new_interval)

        return round(new_interval, 1)

    def _get_base_interval(
        self,
        reminder_type: ReminderType,
        profile: CareProfile,
    ) -> Optional[int]:
        """Gibt das konfigurierte Basis-Intervall zurück (vor Adaptive Learning)."""
        if reminder_type == 'watering':
            return profile.watering_interval_days
        elif reminder_type == 'fertilizing':
            return profile.fertilizing_interval_days
        return None
```

**2. CareReminderService — Orchestrierung:**

```python
class CareReminderService:
    """
    Orchestriert Pflege-Erinnerungen:
    - get_or_create_profile: CareProfile laden/erstellen
    - confirm_reminder: Bestätigung verarbeiten + Adaptive Learning
    - snooze_reminder: Verschieben um N Tage
    - get_care_dashboard: Alle fälligen Erinnerungen abrufen
    - reset_profile: Auf Species-Defaults zurücksetzen
    """

    def __init__(
        self,
        care_repo: CareReminderRepository,
        task_service: TaskService,  # Aus REQ-006
        engine: CareReminderEngine,
    ):
        self.care_repo = care_repo
        self.task_service = task_service
        self.engine = engine

    async def get_or_create_profile(
        self,
        plant_key: str,
    ) -> CareProfile:
        """
        Lädt das CareProfile einer Pflanze. Falls keins existiert, wird
        automatisch eines aus den Species-Defaults generiert:

        1. Lade PlantInstance → Species → RequirementProfile
        2. Bestimme care_style aus Species-Daten (growth_habit, native_habitat)
        3. Erstelle CareProfile aus Preset
        4. Speichere + Edge has_care_profile

        Mapping-Logik (Priorität von oben nach unten):
        0. Species.care_style (wenn explizit gesetzt — bevorzugte Methode, siehe P-002)
        1. BotanicalFamily 'Cactaceae' → 'cactus'
        2. BotanicalFamily 'Orchidaceae' → 'orchid'
        3. BotanicalFamily 'Marantaceae' → 'calathea'
        4. BotanicalFamily 'Polypodiaceae'/'Pteridaceae'/'Aspleniaceae'/'Nephrolepidaceae' → 'fern'
        5. BotanicalFamily 'Crassulaceae'/'Asphodelaceae' (Aloe/Haworthia) → 'succulent'
        6. common_names containing 'Rosmarin/Rosemary/Lavendel/Lavender/Thymian/Thyme/Salbei/Sage' → 'mediterranean'
        7. growth_habit == 'herb' → 'herb_tropical'
        8. native_habitat containing 'tropical'/'rainforest' → 'tropical'
        9. Fallback → 'tropical'

        Empfehlung (P-002): Das Heuristik-basierte Mapping über native_habitat und
        common_names (Stufen 6–8) ist fehleranfällig (z.B. "subtropical" enthält
        "tropical", Sprachvarianten). Es wird empfohlen, ein optionales
        `care_style: Optional[CareStyleType]`-Feld auf der Species-Ebene in REQ-001
        einzuführen. Wenn dieses Feld gesetzt ist (Stufe 0), wird die Heuristik
        übersprungen. Für existierende Species ohne explizites care_style greift
        die Heuristik als Fallback.

        Hinweis: Da REQ-001 kein `growth_habit: 'succulent'` definiert, werden
        Sukkulenten über ihre BotanicalFamily erkannt (Crassulaceae, Asphodelaceae)
        statt über den growth_habit.
        """
        ...

    async def confirm_reminder(
        self,
        plant_key: str,
        request: CareConfirmRequest,
    ) -> CareConfirmation:
        """
        Verarbeitet eine Ein-Tap-Bestätigung:

        1. Erstelle CareConfirmation (action='confirmed')
        2. Markiere zugehörigen Task als 'completed' (via TaskService)
        3. Triggere Adaptive Learning (engine.adapt_interval)
        4. Aktualisiere CareProfile falls neues Intervall berechnet
        5. Generiere nächsten Task für den gleichen Erinnerungstyp
        """
        ...

    async def snooze_reminder(
        self,
        plant_key: str,
        request: CareSnoozeRequest,
    ) -> CareConfirmation:
        """
        Verschiebt eine Erinnerung um N Tage:

        1. Erstelle CareConfirmation (action='snoozed')
        2. Aktualisiere due_date des zugehörigen Tasks (+snooze_days)
        3. Kein Adaptive Learning bei Snooze (würde Ergebnis verfälschen)
        """
        ...

    async def get_care_dashboard(self) -> list[CareDashboardEntry]:
        """
        Lädt alle fälligen Erinnerungen über alle Pflanzen.

        1. Iteriere über alle PlantInstances mit CareProfile
        2. Prüfe pro Pflanze alle 6 Erinnerungstypen
        3. Sortiere nach Dringlichkeit (overdue first, dann due_today)
        4. Füge natürlichsprachliche Anweisungen hinzu (i18n-Keys)
        """
        ...

    async def reset_profile(self, plant_key: str) -> CareProfile:
        """
        Setzt CareProfile auf Species-Defaults zurück:

        1. Lösche gelerntes Intervall (watering_interval_learned = None)
        2. Lade Species-Defaults neu
        3. Setze care_style basierend auf Species
        4. Behalte notes und location_check_enabled
        """
        ...

    async def get_confirmation_history(
        self,
        plant_key: str,
        limit: int = 50,
    ) -> list[CareConfirmation]:
        """Lädt Bestätigungshistorie für eine Pflanze."""
        ...
```

**3. Celery-Beat Task:**

```python
from celery import shared_task
from celery.schedules import crontab

@shared_task(name='care_reminders.generate_due')
def generate_due_care_reminders():
    """
    Täglicher Celery-Beat Task (06:00 UTC):

    1. Iteriere über alle PlantInstances mit CareProfile
    2. **Gießplan-Guard (NEU):** Prüfe ob die Pflanze in einem aktiven
       PlantingRun mit NutrientPlan + WateringSchedule ist:
       - Wenn ja: Unterdrücke WATERING und FERTILIZING Erinnerungen
         (diese werden über den Gießplan-Workflow REQ-006/REQ-014 gesteuert)
       - Andere Erinnerungstypen (repotting, pest_check, location_check,
         humidity_check) bleiben AKTIV — der Gießplan ersetzt nur die
         Bewässerungs-/Düngungsplanung, nicht die allgemeine Pflanzenpflege
    3. Prüfe pro Pflanze alle (nicht-unterdrückten) Erinnerungstypen via CareReminderEngine
    4. Für fällige Erinnerungen: Erstelle Task (REQ-006) falls noch kein
       offener Task für diesen Typ + Pflanze existiert
    5. Task-Properties:
       - category: 'care_reminder'
       - skill_level: 'beginner'
       - priority: basierend auf Erinnerungstyp (watering→high, rest→medium/low)
       - due_date: heute
       - stress_level: 'none'

    Gießplan-Guard-Logik:
    ```python
    def has_active_watering_schedule(plant_key: str) -> bool:
        # 1. Prüfe ob Pflanze in aktivem PlantingRun ist (run_contains-Edge, detached_at=null)
        # 2. Prüfe ob Run einen NutrientPlan hat (run_follows_plan-Edge oder nutrient_plan_key)
        # 3. Prüfe ob NutrientPlan ein watering_schedule hat (nicht null)
        # → Alle 3 Bedingungen müssen erfüllt sein
        ...

    SUPPRESSED_TYPES_WITH_SCHEDULE = {'watering', 'fertilizing'}
    ```

    Idempotenz: Erstellt keine Duplikate — prüft ob bereits ein pending
    Task für [plant_key, reminder_type] existiert.
    """
    ...

# Celery Beat Schedule (in celery_config.py):
# beat_schedule = {
#     'generate-care-reminders-daily': {
#         'task': 'care_reminders.generate_due',
#         'schedule': crontab(hour=6, minute=0),
#     },
# }
```

**4. CareReminderRepository:**

```python
class CareReminderRepository:
    """
    ArangoDB-Zugriff für CareProfile und CareConfirmation.

    Collections: care_profiles, care_confirmations
    Edge-Collections: has_care_profile, confirms_care, care_event_for
    """

    async def get_profile_by_plant(self, plant_key: str) -> Optional[CareProfile]:
        """Lädt CareProfile über has_care_profile Edge."""
        ...

    async def create_profile(self, plant_key: str, profile: CareProfile) -> str:
        """Erstellt CareProfile + has_care_profile Edge."""
        ...

    async def update_profile(self, profile_key: str, update: dict) -> CareProfile:
        """Partielle Aktualisierung des CareProfile."""
        ...

    async def create_confirmation(
        self,
        plant_key: str,
        profile_key: str,
        confirmation: CareConfirmation,
    ) -> str:
        """Erstellt CareConfirmation + confirms_care + care_event_for Edges."""
        ...

    async def get_recent_confirmations(
        self,
        plant_key: str,
        reminder_type: ReminderType,
        limit: int = 10,
    ) -> list[CareConfirmation]:
        """Letzte N Bestätigungen für Adaptive Learning."""
        ...

    async def get_last_confirmation(
        self,
        plant_key: str,
        reminder_type: ReminderType,
    ) -> Optional[CareConfirmation]:
        """Letzte Bestätigung (für Fälligkeitsberechnung)."""
        ...

    async def get_all_plants_with_profiles(self) -> list[dict]:
        """Alle PlantInstances mit CareProfile (für Dashboard/Celery)."""
        ...

    async def has_active_watering_schedule(self, plant_key: str) -> bool:
        """
        Prüft ob eine Pflanze in einem aktiven PlantingRun mit NutrientPlan
        + WateringSchedule ist (Gießplan-Guard für Duplikat-Vermeidung).

        AQL: plant → run_contains (detached_at null) → planting_run (status active)
             → run_follows_plan → nutrient_plan (watering_schedule != null)
        """
        ...

    async def get_confirmation_history(
        self,
        plant_key: str,
        limit: int = 50,
    ) -> list[CareConfirmation]:
        """Vollständige Bestätigungshistorie einer Pflanze."""
        ...
```

**5. CareConfirmation-Interop mit Gießplan-Workflow (REQ-014):**

Wenn eine Gießplan-basierte Bewässerung über den Bestätigungsflow (`POST /watering-events/confirm` oder `POST /watering-events/quick-confirm`) bestätigt wird, muss **zusätzlich** eine `CareConfirmation` erzeugt werden — damit die Adaptive-Learning-Daten fließen und die Fälligkeitsberechnung korrekt bleibt.

```python
def create_watering_plan_confirmation(
    plant_key: str,
    profile_key: str,
    task_key: str,
) -> CareConfirmation:
    """
    Wird von WateringEventService (REQ-014) aufgerufen, wenn ein
    Gießplan-Task bestätigt wird.

    Erzeugt CareConfirmation mit:
    - reminder_type: 'watering'
    - action: 'confirmed'
    - task_key: Referenz auf den bestätigten Gießplan-Task
    - interval_at_time: aktuelles Gieß-Intervall aus CareProfile
      (für Adaptive Learning — auch wenn das Gieß-Intervall vom
      WateringSchedule gesteuert wird, fließen die Daten als
      Feedback für das CareProfile)

    Damit bleibt die CareConfirmation-Timeline lückenlos — auch für
    Pflanzen, die sowohl über den Gießplan als auch über Care-Reminders
    versorgt werden (z.B. bei temporärer Deaktivierung des Gießplans).
    """
    ...
```

**Wichtig:** Die CareConfirmation wird **nur für Pflanzen mit bestehendem CareProfile** erzeugt. Pflanzen ohne CareProfile (z.B. reine Nutzpflanzen ohne Zimmerpflanzen-Pflege) erhalten keine CareConfirmation.

## 4. API-Endpunkte

Router: `/api/v1/care-reminders`

| Methode | Pfad | Beschreibung | Request | Response | Auth |
|---------|------|-------------|---------|----------|------|
| `GET` | `/dashboard` | Alle fälligen Erinnerungen, sortiert nach Dringlichkeit | Query: `?include_upcoming=true` | `list[CareDashboardEntry]` | Ja |
| `GET` | `/plants/{plant_key}/profile` | CareProfile abrufen (auto-erstellt falls nicht vorhanden) | — | `CareProfile` | Mitglied |
| `PATCH` | `/plants/{plant_key}/profile` | Intervalle anpassen | `CareProfileUpdate` | `CareProfile` | Mitglied |
| `POST` | `/plants/{plant_key}/confirm` | Ein-Tap-Bestätigung einer Pflegeaktion | `CareConfirmRequest` | `CareConfirmation` | Mitglied |
| `POST` | `/plants/{plant_key}/snooze` | Erinnerung um N Tage verschieben | `CareSnoozeRequest` | `CareConfirmation` | Mitglied |
| `GET` | `/plants/{plant_key}/history` | Bestätigungshistorie | Query: `?limit=50&reminder_type=watering` | `list[CareConfirmation]` | Mitglied |
| `POST` | `/plants/{plant_key}/reset-profile` | CareProfile auf Species-Defaults zurücksetzen | — | `CareProfile` | Mitglied |

**Fehlerbehandlung (NFR-006):**

| HTTP-Status | Bedingung |
|-------------|-----------|
| `404` | PlantInstance nicht gefunden |
| `409` | Kein offener Task zum Bestätigen vorhanden (bereits bestätigt) |
| `422` | Ungültige Intervall-Werte (Validation Error) |

## 5. Frontend-Spezifikation

### 5.1 PflegeDashboardPage (`/pflege`)

Kartenbasierte Übersicht aller fälligen Erinnerungen. Primäre Seite für Einsteiger (Beginner-Navigation: Position 3 "Pflege").

**Layout:**
- Header: "Pflege-Erinnerungen" mit Datum
- Sortierung: Überfällig → Heute fällig → Demnächst (nächste 2 Tage)
- Leerer Zustand: Illustration + "Alle Pflanzen sind versorgt!" (Erfolgsmeldung)
- Pull-to-Refresh (mobile UX)

**ReminderCard — Einzelne Erinnerungskarte:**

| Element | Beschreibung |
|---------|-------------|
| Pflanzenname | Display-Name der PlantInstance |
| Species-Name | Umgangssprachlicher Artname |
| Erinnerungstyp-Icon | Wassertropfen (Gießen), Flasche (Düngen), Topf (Umtopfen), Lupe (Schädling), Sonne/Mond (Standort), Tropfen/Nebel (Luftfeuchte) |
| Dringlichkeits-Badge | Rot: "X Tage überfällig", Gelb: "Heute fällig", Grau: "In X Tagen" |
| Ein-Tap-Bestätigung | Prominenter Button: "Gegossen" / "Gedüngt" / "Kontrolliert" |
| Snooze-Link | Dezenter Link: "Später (+2 Tage)" |
| Letzte Aktion | "Zuletzt gegossen: vor 8 Tagen" |
| Gießmethode (nur bei `watering`) | Anleitungstext aus `watering_method` (i18n) — z.B. "Tauchbad: Topf 10–15 Min. in Wasser stellen" |
| Wasserqualität (wenn `water_quality_hint` gesetzt) | Tooltip/Hinweis: z.B. "Kalkempfindlich! Regenwasser oder gefiltertes Wasser verwenden." |
| Symptom-Check (nur bei `repotting`) | Hinweistext mit Prüfkriterien: Wurzeln aus Ablaufloch, schnelle Austrocknung, verlangsamtes Wachstum |

**Farbcodierung:**
- Überfällig (`days_overdue > 0`): Rot (`error.main`)
- Heute fällig (`days_overdue == 0`): Gelb/Orange (`warning.main`)
- Demnächst (`days_overdue < 0`): Grau (`text.secondary`)

### 5.2 CareProfileEditDialog

Vereinfachter Dialog zur Anpassung der Pflegeintervalle. Erreichbar über die ReminderCard oder die PlantInstance-Detailseite.

**Felder:**

| Feld | Eingabe | Beschreibung |
|------|---------|-------------|
| Care-Style | Dropdown | Wechselt Preset (setzt alle Intervalle zurück auf Preset-Werte) |
| Gießintervall (Sommer) | Slider (1–30 Tage) | Basisintervall mit Tagesanzeige |
| Winter-Multiplikator | Slider (1.0–3.0×) | "Im Winter X-mal seltener gießen" mit Ergebnis-Anzeige |
| Düngeintervall | Slider (7–60 Tage) | Mit Tagesanzeige |
| Aktive Düngemonate | Monats-Chips (Jan–Dez) | Multi-Select, visuell hervorgehoben |
| Umtopfintervall | Slider (6–36 Monate) | Mit Monatsanzeige |
| Schädlingskontrolle | Slider (3–30 Tage) | Mit Tagesanzeige |
| Gießmethode | Dropdown (soak/drench_and_drain/top_water/bottom_water) | Vorbelegt aus Preset, änderbar |
| Standort-Check | Toggle | An/Aus für saisonale Erinnerungen |
| Standort-Check Monate | 2× Monats-Dropdown (Winter-Warnung, Frühlings-Erinnerung) | Nur sichtbar wenn Standort-Check aktiv. Default aus Hemisphäre. |
| Luftfeuchte-Check | Toggle | An/Aus — Default aus Preset (aktiv für calathea, fern, tropical) |
| Luftfeuchte-Intervall | Slider (3–30 Tage) | Nur sichtbar wenn Luftfeuchte-Check aktiv |
| Adaptive Learning | Toggle | An/Aus |
| Notizen | Textfeld | Freitext, z.B. "Mag Regenwasser" |

**Verhalten bei Care-Style-Wechsel:**
Wenn der Nutzer den Care-Style ändert, werden alle Intervalle auf die Preset-Werte des neuen Styles gesetzt. Ein Bestätigungsdialog warnt: "Alle Intervalle werden auf die Standardwerte für [Style] zurückgesetzt. Fortfahren?"

### 5.3 Integration mit REQ-021 Einsteiger-Pflegekarte

Die Einsteiger-Pflegekarte (REQ-021, Sektion 3.5) zeigt eine "Nächste Aktion"-Zeile. REQ-022 liefert die Daten dafür:

| Information | Quelle (REQ-022) | Darstellung |
|-------------|------------------|-------------|
| Nächste Aktion | `CareDashboardEntry` mit höchster Dringlichkeit | "Morgen gießen", "Heute düngen", "Schädlingskontrolle in 3 Tagen" |
| Letzte Pflege | `CareConfirmation` (letzte Bestätigung) | "Zuletzt gegossen: vor 5 Tagen" |
| Pflegeprofil | `CareProfile.care_style` | "Tropische Grünpflanze" |

### 5.4 Redux Slice

```typescript
interface CareRemindersState {
  dashboard: {
    entries: CareDashboardEntry[];
    status: 'idle' | 'loading' | 'error';
    error: string | null;
    lastFetched: string | null;  // ISO timestamp
  };
  profiles: Record<string, CareProfile>;  // Keyed by plant_key
  history: Record<string, CareConfirmation[]>;  // Keyed by plant_key
}

interface CareDashboardEntry {
  plantKey: string;
  plantName: string;
  speciesName: string | null;
  locationName: string | null;
  careStyle: CareStyleType;
  reminderType: ReminderType;
  daysOverdue: number;
  urgency: 'overdue' | 'due_today' | 'upcoming';
  intervalDays: number;
  lastConfirmedAt: string | null;
  instructionI18nKey: string;
  /** Gießmethode — nur bei reminderType === 'watering' befüllt */
  wateringMethod: WateringMethod | null;
  /** Wasserqualitäts-Hinweis (i18n-Key) — nur bei reminderType === 'watering' und wenn relevant */
  waterQualityHint: string | null;
  /** Symptom-Check-Hinweis (i18n-Key) — nur bei reminderType === 'repotting' */
  repottingHintI18nKey: string | null;
}

type WateringMethod = 'soak' | 'drench_and_drain' | 'top_water' | 'bottom_water';
type ReminderType = 'watering' | 'fertilizing' | 'repotting' | 'pest_check' | 'location_check' | 'humidity_check';

interface CareProfile {
  careStyle: CareStyleType;
  wateringIntervalDays: number;
  winterWateringMultiplier: number;
  wateringMethod: WateringMethod;
  waterQualityHint: string | null;
  fertilizingIntervalDays: number;
  fertilizingActiveMonths: number[];
  repottingIntervalMonths: number;
  pestCheckIntervalDays: number;
  locationCheckEnabled: boolean;
  locationCheckMonths: { winterWarning: number; springReminder: number } | null;
  humidityCheckEnabled: boolean;
  humidityCheckIntervalDays: number;
  adaptiveLearningEnabled: boolean;
  wateringIntervalLearned: number | null;
  fertilizingIntervalLearned: number | null;
  notes: string | null;
  autoGenerated: boolean;
}

// Actions (mit Optimistic Updates für Confirm/Snooze):
// fetchDashboard() — GET /dashboard
// fetchProfile(plantKey) — GET /plants/{plantKey}/profile
// updateProfile(plantKey, update) — PATCH /plants/{plantKey}/profile
// confirmReminder(plantKey, request) — POST /plants/{plantKey}/confirm (optimistic: entfernt Eintrag aus Dashboard)
// snoozeReminder(plantKey, request) — POST /plants/{plantKey}/snooze (optimistic: verschiebt Eintrag auf "upcoming")
// fetchHistory(plantKey) — GET /plants/{plantKey}/history
// resetProfile(plantKey) — POST /plants/{plantKey}/reset-profile
```

**Optimistic Updates:**
- `confirmReminder`: Entfernt den Dashboard-Eintrag sofort aus der Liste (vor API-Response). Bei Fehler: Eintrag wird wieder eingefügt + Fehler-Snackbar.
- `snoozeReminder`: Verschiebt den Eintrag sofort auf "upcoming" (Grau) und passt `daysOverdue` an.

### 5.5 i18n-Schlüssel

```
pages.care.title                             = "Pflege-Erinnerungen" / "Care Reminders"
pages.care.allCaredFor                       = "Alle Pflanzen sind versorgt!" / "All plants are taken care of!"
pages.care.lastAction                        = "Zuletzt {{action}}: vor {{days}} Tagen" / "Last {{action}}: {{days}} days ago"

pages.care.types.watering                    = "Gießen" / "Watering"
pages.care.types.fertilizing                 = "Düngen" / "Fertilizing"
pages.care.types.repotting                   = "Umtopfen" / "Repotting"
pages.care.types.pest_check                  = "Schädlingskontrolle" / "Pest Check"
pages.care.types.location_check              = "Standort-Check" / "Location Check"
pages.care.types.humidity_check              = "Luftfeuchte-Check" / "Humidity Check"

pages.care.actions.watered                   = "Gegossen" / "Watered"
pages.care.actions.fertilized                = "Gedüngt" / "Fertilized"
pages.care.actions.repotted                  = "Umgetopft" / "Repotted"
pages.care.actions.checked                   = "Kontrolliert" / "Checked"
pages.care.actions.snooze                    = "Später (+{{days}} Tage)" / "Later (+{{days}} days)"

pages.care.urgency.overdue                   = "{{days}} Tage überfällig" / "{{days}} days overdue"
pages.care.urgency.dueToday                  = "Heute fällig" / "Due today"
pages.care.urgency.upcoming                  = "In {{days}} Tagen" / "In {{days}} days"

pages.care.instructions.watering             = "{{plantName}} braucht Wasser" / "{{plantName}} needs water"
pages.care.instructions.fertilizing          = "{{plantName}} braucht Dünger" / "{{plantName}} needs fertilizer"
pages.care.instructions.repotting            = "{{plantName}} sollte umgetopft werden" / "{{plantName}} should be repotted"
pages.care.instructions.repotting_hint       = "Prüfen: (1) Wachsen Wurzeln aus dem Ablaufloch? (2) Trocknet das Substrat ungewöhnlich schnell? (3) Wächst die Pflanze merklich langsamer?" / "Check: (1) Are roots growing out of the drain hole? (2) Does the soil dry out unusually fast? (3) Has growth noticeably slowed down?"
pages.care.instructions.pest_check           = "{{plantName}} auf Schädlinge kontrollieren" / "Check {{plantName}} for pests"
pages.care.instructions.location_check_oct   = "{{plantName}} ins Winterquartier holen" / "Move {{plantName}} to winter location"
pages.care.instructions.location_check_mar   = "{{plantName}} an helleren Standort stellen" / "Move {{plantName}} to brighter location"
pages.care.instructions.humidity_check       = "Luftfeuchtigkeit bei {{plantName}} prüfen — ggf. Luftbefeuchter oder Kieselschale verwenden" / "Check humidity for {{plantName}} — consider using a humidifier or pebble tray"

pages.care.wateringMethod.soak               = "Tauchbad: Topf 10–15 Min. in zimmerwarmes Wasser stellen, abtropfen lassen." / "Soak: Place pot in lukewarm water for 10-15 min, then drain."
pages.care.wateringMethod.drench_and_drain   = "Kräftig durchgießen, vollständig ablaufen lassen. Überschuss wegkippen." / "Drench thoroughly, let drain completely. Discard excess water."
pages.care.wateringMethod.top_water          = "Von oben gießen, bis Wasser unten herausläuft. Überschuss nach 30 Min. wegkippen." / "Water from top until water runs out the bottom. Discard excess after 30 min."
pages.care.wateringMethod.bottom_water       = "Untersetzer mit Wasser füllen, 20–30 Min. saugen lassen, Rest wegkippen." / "Fill saucer with water, let absorb for 20-30 min, discard remainder."

pages.care.waterQuality.orchid               = "Kalkarmes Wasser bevorzugt. Abgestandenes Leitungswasser oder Regenwasser." / "Prefers low-lime water. Use stale tap water or rainwater."
pages.care.waterQuality.calathea             = "Kalkempfindlich! Regenwasser, gefiltertes oder abgestandenes Wasser verwenden." / "Lime-sensitive! Use rainwater, filtered, or stale tap water."
pages.care.waterQuality.fern                 = "Weiches Wasser bevorzugt. Abgestandenes Leitungswasser oder Regenwasser." / "Prefers soft water. Use stale tap water or rainwater."

pages.care.profile.title                     = "Pflegeprofil bearbeiten" / "Edit Care Profile"
pages.care.profile.careStyle                 = "Pflegestil" / "Care Style"
pages.care.profile.wateringInterval          = "Gießintervall (Tage)" / "Watering Interval (days)"
pages.care.profile.fertilizingInterval       = "Düngeintervall (Tage)" / "Fertilizing Interval (days)"
pages.care.profile.activeMonths              = "Aktive Düngemonate" / "Active Fertilizing Months"
pages.care.profile.repottingInterval         = "Umtopfintervall (Monate)" / "Repotting Interval (months)"
pages.care.profile.pestCheckInterval         = "Schädlingskontrolle (Tage)" / "Pest Check Interval (days)"
pages.care.profile.locationCheck             = "Saisonale Standort-Erinnerungen" / "Seasonal Location Reminders"
pages.care.profile.humidityCheck             = "Luftfeuchte-Erinnerungen (Heizperiode)" / "Humidity Reminders (Heating Season)"
pages.care.profile.humidityCheckInterval     = "Luftfeuchte-Check (Tage)" / "Humidity Check (days)"
pages.care.profile.wateringMethod            = "Gießmethode" / "Watering Method"
pages.care.profile.waterQuality              = "Wasserqualität" / "Water Quality"
pages.care.profile.adaptiveLearning          = "Automatische Intervallanpassung" / "Automatic Interval Adjustment"
pages.care.profile.notes                     = "Notizen" / "Notes"
pages.care.profile.resetConfirm              = "Auf Standardwerte zurücksetzen?" / "Reset to defaults?"
pages.care.profile.styleChangeConfirm        = "Alle Intervalle werden auf {{style}}-Standardwerte zurückgesetzt." / "All intervals will be reset to {{style}} defaults."

enums.careStyle.tropical                     = "Tropische Grünpflanze" / "Tropical Foliage"
enums.careStyle.succulent                    = "Sukkulente" / "Succulent"
enums.careStyle.orchid                       = "Orchidee" / "Orchid"
enums.careStyle.calathea                     = "Calathea / Marante" / "Calathea / Prayer Plant"
enums.careStyle.herb_tropical                = "Kräuter (feuchtigkeitsliebend)" / "Herbs (moisture-loving)"
enums.careStyle.mediterranean                = "Mediterrane Pflanze" / "Mediterranean Plant"
enums.careStyle.fern                         = "Farn" / "Fern"
enums.careStyle.cactus                       = "Kaktus" / "Cactus"
enums.careStyle.custom                       = "Benutzerdefiniert" / "Custom"

enums.wateringMethod.soak                    = "Tauchbad" / "Soak"
enums.wateringMethod.drench_and_drain        = "Durchgießen & ablaufen lassen" / "Drench & Drain"
enums.wateringMethod.top_water               = "Von oben gießen" / "Top Watering"
enums.wateringMethod.bottom_water            = "Von unten gießen" / "Bottom Watering"
```

### 5.6 Navigations-Integration (REQ-021)

Die PflegeDashboardPage wird in die Navigations-Tiering-Konfiguration integriert:

| Modus | Navigation | Position |
|-------|-----------|----------|
| Einsteiger | "Pflege" (prominenter Menüpunkt) | Position 3 (nach Dashboard, Meine Pflanzen) |
| Fortgeschritten | "Pflege" | Position 3 |
| Experte | "Pflege & Erinnerungen" (zusätzlich zu "Aufgaben & Workflows") | Position 6 |

Im Experten-Modus ist die PflegeDashboardPage eine alternative Ansicht auf dieselben Tasks — Experten können zwischen der klassischen Task-Queue (REQ-006) und der vereinfachten Pflege-Ansicht wechseln.

## 6. Akzeptanzkriterien

### Funktional:

- [ ] CareProfile wird automatisch generiert beim ersten Zugriff auf `/plants/{key}/profile`
- [ ] Auto-generiertes Profil nutzt Species-Defaults (BotanicalFamily → care_style Mapping, Fallback über common_names/native_habitat)
- [ ] Alle 9 `care_style`-Presets liefern agrobiologisch sinnvolle Intervall-Werte
- [ ] Gieß-Erinnerungen erscheinen nach Ablauf des konfigurierten Intervalls (saisonal angepasst via `winter_watering_multiplier` in Nov–Feb)
- [ ] Winter-Multiplikator verhindert Überwässerung: Kaktus 3×, Sukkulente 2.5×, Mediterran 2×, Tropical 1.5×, Calathea/Farn 1.3×
- [ ] Dünge-Erinnerungen erscheinen NUR in den konfigurierten Aktivmonaten
- [ ] Dünge-Erinnerungen erscheinen NICHT wenn `current_phase` in DORMANCY_PHASES (inkl. `maintenance`, `acclimatization`, `repotting_recovery`)
- [ ] Umtopf-Erinnerungen erscheinen basierend auf dem Monatsintervall seit letztem Umtopfen
- [ ] Schädlingskontroll-Erinnerungen erscheinen im konfigurierten Intervall
- [ ] Standort-Check-Erinnerungen erscheinen in den konfigurierbaren Monaten (Default: Oktober/März NH, April/September SH, jeweils erste 15 Tage)
- [ ] Standort-Check-Monate sind pro CareProfile über `location_check_months` konfigurierbar (Anpassung an Klimazone)
- [ ] Ein-Tap-Bestätigung markiert den zugehörigen Task als completed
- [ ] Snooze verschiebt das Task-due_date um die gewählte Anzahl Tage
- [ ] Adaptive Learning passt Intervall nach 3 konsistenten Signalen um 1 Tag an
- [ ] Adaptive Learning-Grenze: maximal ±30% Abweichung vom Basis-Intervall
- [ ] Reset-Profile setzt alle Intervalle und gelernten Werte auf Species-Defaults zurück
- [ ] Dashboard zeigt alle fälligen Erinnerungen, sortiert nach Dringlichkeit
- [ ] Dashboard: Überfällige Erinnerungen haben rotes Badge, heutige gelb, kommende grau
- [ ] Care-Style-Wechsel setzt alle Intervalle auf Preset-Werte (mit Bestätigungsdialog)
- [ ] Gieß-Erinnerungen zeigen die artspezifische Gießmethode (`watering_method`) als Anleitungstext an
- [ ] Gieß-Erinnerungen zeigen ggf. einen Wasserqualitäts-Hinweis (`water_quality_hint`) als Tooltip an (Calathea, Orchidee, Farn)
- [ ] Umtopf-Erinnerungen zeigen zusätzlich einen Symptom-Check-Hinweis an (Wurzeln aus Ablaufloch, schnelle Austrocknung, verlangsamtes Wachstum)
- [ ] Luftfeuchte-Check-Erinnerungen erscheinen saisonal (Heizperiode Okt–Mär NH) für feuchtigkeitsempfindliche Presets (calathea, fern, tropical)
- [ ] Gießintervall wird in der `acclimatization`-Phase automatisch um Faktor 1.3 verlängert (Wurzeln nach Kauf/Umtopfen noch nicht etabliert)
- [ ] Alle Bestätigungen werden als immutable CareConfirmation-Events gespeichert
- [ ] Celery-Beat generiert täglich fehlende Tasks (idempotent, keine Duplikate)
- [ ] **Gießplan-Guard:** WATERING und FERTILIZING Erinnerungen werden unterdrückt für Pflanzen in aktivem Run mit NutrientPlan+WateringSchedule
- [ ] **Gießplan-Guard Granularität:** Nur WATERING und FERTILIZING werden unterdrückt — repotting, pest_check, location_check, humidity_check bleiben aktiv
- [ ] **CareConfirmation-Interop:** Gießplan-Bestätigung (REQ-014 confirm/quick-confirm) erzeugt CareConfirmation für adaptive Learning
- [ ] **CareConfirmation-Interop nur bei CareProfile:** CareConfirmation wird nur erzeugt wenn die Pflanze ein bestehendes CareProfile hat
- [ ] i18n: Alle Texte in DE und EN verfügbar

### Technisch:

- [ ] Erinnerungen werden als reguläre `Task`-Objekte gespeichert (`category='care_reminder'`)
- [ ] Keine Duplizierung des Task-Stores — vollständige Integration mit REQ-006
- [ ] CareProfile 1:1 Beziehung zu PlantInstance (UNIQUE Index auf `has_care_profile._from`)
- [ ] CareConfirmation ist immutable (Insert-only, kein Update/Delete)
- [ ] Dashboard-API < 200ms Antwortzeit für 50 Pflanzen (Index-basierte Abfragen)
- [ ] Optimistic Updates im Frontend für Confirm/Snooze
- [ ] Redux Slice mit camelCase-Konvention (Frontend) ↔ snake_case (API)
- [ ] Slider-Komponenten für Intervall-Anpassung (nicht Zahlenfelder)
- [ ] Celery-Beat Task ist idempotent (Duplikat-Prüfung vor Task-Erstellung)
- [ ] Alle neuen Collections/Edges sind im `kamerplanter_graph` registriert

## 7. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Pflege-Dashboard | Ja | — | — |
| Pflegepläne (pro Pflanze) | Mitglied | Mitglied | Mitglied |
| Erinnerungen (pro Pflanze) | Mitglied | Mitglied | Mitglied |

## 8. Abhängigkeiten

| REQ/NFR | Art | Beschreibung |
|---------|-----|-------------|
| REQ-006 | Nutzt | Task/TaskService/TaskRepository — alle Erinnerungen als Tasks gespeichert |
| REQ-001 | Liest | Species + BotanicalFamily für CareProfile-Auto-Generierung (care_style-Mapping) |
| REQ-003 | Liest | PlantInstance.current_phase für Dünge-Guard (Dormanz-Check) + RequirementProfile für Species-Defaults |
| REQ-020 | Liest | Zimmerpflanzen-Phasen (acclimatization, active_growth, maintenance, repotting_recovery) für DORMANCY_PHASES |
| REQ-021 | Erweitert | Einsteiger-Pflegekarte: "Nächste Aktion"-Zeile + Navigations-Tiering |
| REQ-004 | Liest | NutrientPlan.watering_schedule für Gießplan-Guard (Duplikat-Vermeidung: Pflanzen mit aktivem Schedule erhalten keine WATERING/FERTILIZING Reminders) |
| REQ-013 | Liest | PlantingRun + run_contains-Edge für Gießplan-Guard (Prüfung ob Pflanze in aktivem Run mit NutrientPlan ist) |
| REQ-014 | Muster + Aufrufer | Celery-Beat-Pattern (tägliche Task-Generierung analog `tank_maintenance_check`); **Aufrufer:** WateringEventService ruft `create_watering_plan_confirmation` auf bei Gießplan-Bestätigung |
| NFR-001 | Einhält | 5-Layer-Architektur (API → Service → Engine → Repository → ArangoDB) |
| NFR-003 | Einhält | Source Code in English, Dokumentation in German |
| NFR-006 | Einhält | Fehlerbehandlung mit strukturierten HTTP-Statuscodes |
| NFR-010 | Erweitert | CRUD-Masken für CareProfile mit Validierung (siehe CRUD-Ausnahmen unten) |

### NFR-010 CRUD-Ausnahmen

Die folgenden Entitäten weichen begründet von der NFR-010-Vorgabe "Jede Domänenentität MUSS Delete unterstützen" ab:

| Entität | Create | Read | Update | Delete | Begründung |
|---------|--------|------|--------|--------|------------|
| CareProfile | Auto (get_or_create) | GET `/plants/{key}/profile` | PATCH `/plants/{key}/profile` | Nein — `reset-profile` stattdessen | 1:1-Beziehung zu PlantInstance; Löschen würde sofort Neuanlage erzwingen. Reset auf Species-Defaults ist die fachlich korrekte Alternative. |
| CareConfirmation | POST `/plants/{key}/confirm` | GET (via Dashboard-Aggregation) | Nein | Nein | Immutables Event-Log (Audit-Trail). Nachträgliche Änderung würde Adaptive-Learning-Integrität gefährden. |
