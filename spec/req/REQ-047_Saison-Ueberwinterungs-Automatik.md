# Spezifikation: REQ-047 - Saison- & Überwinterungs-Automatik

```yaml
ID: REQ-047
Titel: Automatische Saison- & Überwinterungs-Steuerung — Winter-/Frühlings-Erkennung aus Live- und Klimadaten, ohne manuelle Profile
Kategorie: Pflege & Erinnerungen / Automatisierung
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, React 19, TypeScript 5.9, MUI 7, Redux Toolkit
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-022 (Pflegeerinnerungen/OverwinteringProfile/CareProfile — erweitert), REQ-039 (Winterhärte-Ampel + Frost-Defaults), REQ-005 (Wetter-/Frost-Livedaten), REQ-046 (Wetterquellen-Auflösung), REQ-041 (Klimanormale als Saison-Fallback), REQ-002 (Standort — Innen/Außen, GPS, Hemisphäre), REQ-001 (frost_sensitivity), REQ-003 (dormancy-Phase, Invariante D5), REQ-006 (Task-Erzeugung), REQ-013 (Run/Dual-Support), REQ-024 (Mandanten-Scoping)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-07-05 | Initialer Entwurf. Konzeptionelle Überarbeitung des Überwinterungs-Managements: Der Nutzer legt **keine** Überwinterungsprofile mehr an. Führt die **SeasonState-Engine** ein — eine pro Outdoor-Standort berechnete Saison-Zustandsmaschine, die den Übergang in die Winterruhe (Schutz/Einräumen) und die Rückholung (Ausräumen/Abhärten) automatisch triggert. Trigger-Kaskade: Live-Wetter/Sensorik (REQ-005/046) → Klimanormale (REQ-041) → Kalender/Hemisphäre-Fallback. Verlagert die in REQ-022 datumsbasierten Winter-/Frühlings-Erinnerungen auf zustandsbasierte Auslösung, materialisiert das `OverwinteringProfile` automatisch aus dem Species-Template (REQ-022) + Standort-Ampel (REQ-039) und schaltet einen **Dormancy-Care-Modus** (Winterruhe-Pflegeplan) im CareProfile ein. |

## 1. Business Case

### User Stories

- **Als Gartenbesitzerin ohne Fachwissen** möchte ich, dass die App mir von selbst sagt, wann meine Kübelpflanzen rein müssen und meine Beetpflanzen Schutz brauchen — **ohne** dass ich für jede Pflanze vorher ein Überwinterungsprofil ausfüllen muss.
- **Als Nutzer mit Wetteranbindung** (Home Assistant oder öffentlicher Wetterdienst) möchte ich, dass die Winter-Warnung auf die **tatsächlich vorhergesagte Kälte** an meinem Standort reagiert — wenn nächste Woche der erste Frost kommt, will ich **jetzt** die Erinnerung, nicht an einem starren Kalendertag.
- **Als Nutzer ohne jede Sensorik oder Wetterquelle** möchte ich trotzdem sinnvolle Winter-Hinweise bekommen — abgeleitet aus **meinem Standort und der Jahreszeit** (Klimanormale bzw. Hemisphäre), damit die Funktion auch offline/hardwarelos nützlich bleibt.
- **Als Gärtnerin** möchte ich im Spätwinter **aktiv zurückgeholt** werden: wann ich die Dahlienknollen vorziehe, die Rosen abhäufle und die Kübelpflanzen schrittweise wieder rausstelle — abgestimmt auf das Ende der Frostgefahr, nicht auf ein fixes Datum.
- **Als Halterin überwinternder Pflanzen** möchte ich, dass die App während der Winterruhe **anders pflegt** — deutlich weniger gießen, nicht düngen, dafür an die Fäulnis-/Feuchte-Kontrolle im Winterquartier erinnern — damit mir die Pflanzen nicht im Keller verfaulen oder vertrocknen.
- **Als erfahrene Nutzerin** möchte ich die automatische Einschätzung im Einzelfall **übersteuern** können (z. B. ein besonders geschützter Standort, frühere/spätere Einräumung), ohne dass die Automatik meine Entscheidung wieder überschreibt.

### Beschreibung

Das bisherige Überwinterungs-Management (REQ-022) hat zwei Schwächen, die dieses Requirement behebt:

1. **Manuelle Profil-Pflege.** REQ-022 modelliert das `OverwinteringProfile` als ein pro Pflanze anzulegendes/zu pflegendes Objekt. Für die Zielgruppe (Gelegenheits-Gärtner) ist das eine zu hohe Einstiegshürde. Die fachliche Grundlage — **art-spezifische Überwinterungs-Bedingungen** — liegt bereits vollständig in den Steckbriefen (§4.3 Überwinterung) und wird deterministisch in **species-weite Templates** extrahiert (`overwintering_profiles.yaml`, REQ-022 / Overwintering-Template-Seeds). Diese Datenbasis wird hier zur **Auto-Materialisierung** genutzt: Der Nutzer legt nichts an; ein instanzbezogenes Profil entsteht bei Bedarf automatisch aus Template + Standort-Ampel und ist nur **optional** übersteuerbar.

2. **Starre Datums-Trigger.** Die Winter-/Frühlings-Erinnerungen feuern heute an festen Monaten (`winter_action_month`, `spring_action_month`). Das ignoriert sowohl vorhandene Livedaten (eine konkrete Frostvorhersage) als auch die reale Klimalage des Standorts. REQ-047 ersetzt den Datums-Trigger durch eine **Saison-Zustandsmaschine** (`SeasonState`) pro Outdoor-Standort, die aus der **besten verfügbaren Datenquelle** speist.

**Kernidee — dreistufige Trigger-Kaskade (beste Quelle gewinnt):**

| Stufe | Datenquelle | Wann aktiv | Charakter |
|-------|-------------|-----------|-----------|
| 1 — Live | `:WeatherForecast` (Frost-/Min-Temp-Vorhersage, REQ-005/046) und/oder Außen-Sensorik (REQ-005) | Standort hat aufgelöste Wetterquelle oder Außentemperatur-Sensor | Reagiert tagesaktuell auf die reale Wetterlage |
| 2 — Klimatologisch | `:ClimateNormal` (`monthly_temp_min_c`, `coldest_month_min_c`, REQ-041) + `HardinessZone.typical_first/last_frost_md` (REQ-039) | Standort hat GPS, aber keine Livedaten | Standortgenaue, aber statische Saison-Schätzung |
| 3 — Kalender | `Site.hemisphere` + Preset-Monate (REQ-022) | weder Livedaten noch Klimanormale | Grober Hemisphären-Fallback (heutiges Verhalten) |

Die Engine ist ausdrücklich so gebaut, dass sie **auf jeder Stufe** einen brauchbaren Zustand liefert (Graceful Degradation) und sich automatisch hochstuft, sobald eine bessere Quelle verfügbar wird.

**Abgrenzung (was dieses Dokument NICHT ist):**

- **Keine** Neudefinition der Wetter-/Frost-Datenbeschaffung — Livedaten kommen unverändert aus REQ-005 (Modell, Frost-Warnschwelle) und REQ-046 (Quellen-Auflösung). REQ-047 ist reiner **Konsument** dieser Signale.
- **Keine** Neudefinition der art-spezifischen Überwinterungs-Bedingungen — diese bleiben in den Steckbriefen (§4.3) und den daraus generierten Templates (REQ-022). REQ-047 **liest** sie.
- **Keine** Änderung der Winterhärte-Ampel-Logik — `evaluate_winter_hardiness` bleibt in REQ-039; REQ-047 nutzt das Ergebnis zur Pfad-Zuordnung (Invariante D5).
- **Kein** Ersatz des `CareProfile`/`CareReminderEngine` — der Winterruhe-Pflegeplan ist ein **Modus** des bestehenden CareProfile (REQ-022), keine parallele Pflege-Engine.

**Geltungsbereich (nur Freiland/Gewächshaus):** Ein `SeasonState` wird **ausschließlich** für Sites mit `type ∈ {outdoor, greenhouse}` berechnet. Reine Indoor-Sites (`type='indoor'`) haben keine Saison — Zimmerpflanzen bleiben bei der bestehenden hemisphären-basierten Winter-Gießanpassung (REQ-022). Für eine Pflanze, die in ein Winterquartier verlagert wird (Pfad B), bleibt der **Herkunfts-Standort** (Outdoor-Site) maßgeblich für die Saison-Übergänge; das Winterquartier (Indoor-Location) stellt nur die Pflegebedingungen der geschützten Ruhe.

## 2. Datenmodell (ArangoDB)

### 2.1 Neue Collection `:SeasonState` (der Saison-Zustand pro Standort)

- **`:SeasonState`** — aktueller Saison-/Winter-Zustand eines Outdoor-Standorts
  - Collection: `season_states`
  - Properties:
    - `season_state_id: str`
    - `site_key: str` (Referenz auf Site, REQ-002; 1:1 pro Outdoor-/Greenhouse-Site)
    - `tenant_key: str` (Mandanten-Scoping, REQ-024 — erbt von der Site)
    - `phase: SeasonPhase` (aktueller Zustand, s. §2.2)
    - `trigger_tier: Literal['live', 'climatological', 'calendar']` (welche Kaskadenstufe den aktuellen Zustand bestimmt hat — für UI-Transparenz)
    - `trigger_reason_i18n_key: str` (natürlichsprachliche Begründung, z. B. `pages.season.trigger.frostForecast`)
    - `entered_phase_at: datetime` (Zeitpunkt des letzten Zustandsübergangs)
    - `season_year: int` (Bezugsjahr der laufenden Überwinterungssaison — der Winter 2026/27 wird als `2026` geführt; verhindert Rücksprünge innerhalb derselben Saison, s. Hysterese)
    - `last_min_temp_c: Optional[float]` (zuletzt bewertete Nacht-/Tagesminimumtemperatur — aus Forecast oder Sensor)
    - `consecutive_signal_days: int = 0` (Zähler für den Hysterese-Schwellwert, s. §3.3)
    - `forecast_first_frost_date: Optional[date]` (aus Live-Forecast abgeleitetes nächstes Frostdatum, wenn vorhanden)
    - `estimated_first_frost_md: Optional[str]` (`MM-DD`, aus Klimanormalen/Zone abgeleitet — Stufe 2/3)
    - `estimated_last_frost_md: Optional[str]` (`MM-DD`, Frühjahrs-Frostende — Stufe 2/3)
    - `updated_at: datetime`
    - `evaluated_at: datetime` (letzter Engine-Lauf, auch ohne Übergang)

### 2.2 Enum `SeasonPhase` — die Zustandsmaschine

```python
SeasonPhase = Literal[
    'growing',          # Vegetationsperiode — keine Winter-Aktivität
    'pre_winter',       # Winter kündigt sich an: Vorbereitungs-/Handlungsfenster
                        # (Schutz anbringen, Kübel einräumen, Knollen ausgraben)
    'winter_dormancy',  # Winterruhe aktiv: geschützte Ruhe / in-situ-Dormanz
                        # → Dormancy-Care-Modus im CareProfile
    'pre_spring',       # Spätwinter/Frühjahr: Rückhol-Fenster
                        # (abhäufeln, vorziehen, abhärten, schrittweise rausstellen)
]
```

**Zulässige Übergänge (gerichtet, ein Zyklus pro `season_year`):**

```
growing ──▶ pre_winter ──▶ winter_dormancy ──▶ pre_spring ──▶ growing
   ▲                                                              │
   └──────────────────────────────────────────────────────────────┘
```

Kein Übergang überspringt regulär eine Phase; die Engine darf jedoch beim ersten Lauf oder bei plötzlichem Kälteeinbruch `growing → pre_winter → winter_dormancy` innerhalb weniger Läufe durchlaufen. **Rückwärtsübergänge sind innerhalb desselben `season_year` verboten** (Hysterese, §3.3): ein warmer Tag im Dezember bringt eine Pflanze nicht von `winter_dormancy` zurück nach `pre_winter`.

### 2.3 Erweiterung von `:OverwinteringProfile` (REQ-022, additiv)

Das instanzbezogene Profil bleibt bestehen, wird aber **automatisch materialisiert** statt vom Nutzer angelegt. Additive Felder:

- `user_overridden: bool = False` — `True`, sobald der Nutzer einen Wert manuell gesetzt hat. Die Auto-Materialisierung überschreibt ein `user_overridden`-Profil **nie** (nur additiv fehlende Felder ergänzen).
- `derived_path: Optional[Literal['A', 'B']]` — aus der Ampel abgeleiteter Winter-Pfad (Invariante D5, REQ-022): `A` = in-situ (Dormanz mit Schutz), `B` = verlagert (Winterquartier/Knollenlager). `None` bis zur ersten Materialisierung.
- `dormancy_care_active: bool = False` — `True`, solange die Pflanze im Dormancy-Care-Modus ist (gesetzt beim SeasonState-Übergang nach `winter_dormancy`, zurückgesetzt bei `pre_spring`/`growing`).
- `materialized_at: Optional[datetime]` — Zeitpunkt der Auto-Materialisierung aus dem Template.
- `source_template_key: Optional[str]` — `_key` des verwendeten `overwintering_profiles`-Templates (Nachvollziehbarkeit).

> **Hinweis:** `auto_generated` (REQ-022, bestehend) bleibt und ist bei materialisierten Profilen `True`. Neu ist die Trennung von `auto_generated` (Herkunft) und `user_overridden` (nachträgliche Nutzeranpassung): ein Profil kann `auto_generated=True` **und** `user_overridden=True` sein (Auto-Basis + punktueller Override).

### 2.4 Erweiterung von `:CareProfile` (REQ-022, additiv) — Dormancy-Care-Modus

- `dormancy_care_mode: bool = False` — aktiver Winterruhe-Pflegeplan. Wird von der SeasonState-Engine gesetzt/gelöscht, nicht direkt vom Nutzer.
- `dormancy_watering: Optional[Literal['none', 'minimal', 'reduced', 'normal']] = None` — Gießvorgabe während der Ruhe, materialisiert aus `OverwinteringProfile.winter_watering`. `None` ⇒ Rückfall auf `winter_watering_multiplier`.
- `dormancy_check_interval_days: int = 30` — Intervall der Winterquartier-/Ruhe-Kontrolle (Fäulnis, Feuchte, Schädlinge), Default aus `OverwinteringProfile.storage_check_interval_days` sofern gesetzt.

### 2.5 Zwei neue Erinnerungstypen (REQ-022 `ReminderType`, additiv)

| Typ | Schlüssel | Auslöser | Priorität |
|-----|-----------|----------|-----------|
| Ruhe-/Winterquartier-Kontrolle | `dormancy_health_check` | Intervall (`dormancy_check_interval_days`) während `winter_dormancy` — prüft Fäulnis, Schimmel, Feuchte, Schädlinge | `medium` |
| Winterquartier-Klima-Warnung | `quarter_climate_check` | Nur bei Livedaten des Winterquartiers (Sensor/HA): Ist-Temperatur verletzt `winter_quarter_temp_min/max` | `high` (Pflanze erfriert/treibt vorzeitig) |

Die bestehenden Winter-Erinnerungstypen (`winter_protection`, `spring_uncover`, `tuber_dig`, `storage_check`, `location_check`) bleiben unverändert — geändert wird **nur ihr Auslöser** (SeasonState-Übergang statt fester Monat, §3.4).

### 2.6 Edges

```
Edge Collection        _from     _to                       Attribut
──────────────────────────────────────────────────────────────────────────
has_season_state       sites     season_states             // NEU — Standort ↔ Saison-Zustand (1:1)
```

Bestehende Edges bleiben genutzt: `uses_overwintering_template` (PlantInstance/Species → overwintering_profiles-Template, REQ-022), `has_overwintering_profile`, `overwinters_at` (→ Winterquartier-Location), `has_care_profile`, `has_forecast` (Site → weather_forecasts, REQ-005).

### 2.7 Beispiel-AQL

**Alle Outdoor-Sites mit ihrem aktuellen Saison-Zustand und der besten Frost-Datenquelle:**
```aql
FOR site IN sites
  FILTER site.type IN ['outdoor', 'greenhouse']
  FILTER site.tenant_key == @tenant_key
  LET state = FIRST(
    FOR s IN 1..1 OUTBOUND site has_season_state RETURN s
  )
  // Nächste Frost-Vorhersage (Live, Stufe 1) — wenn vorhanden
  LET next_frost = FIRST(
    FOR fc IN 1..1 OUTBOUND site has_forecast
      FILTER fc.forecast_date >= DATE_ISO8601(DATE_NOW())
      FILTER fc.temp_min_c != null AND fc.temp_min_c <= @frost_warning_c
      SORT fc.forecast_date ASC
      LIMIT 1
      RETURN fc.forecast_date
  )
  RETURN {
    site_key: site._key,
    phase: state.phase,
    trigger_tier: state.trigger_tier,
    forecast_first_frost: next_frost,
    estimated_first_frost_md: state.estimated_first_frost_md
  }
```

## 3. Technische Umsetzung (Python)

Alle neuen Klassen folgen der 5-Layer-Architektur (NFR-001): API → Service → Engine → Repository → ArangoDB. Die Zustandslogik liegt in einer reinen Engine (deterministisch, testbar ohne I/O); die Datenbeschaffung kapselt der Service.

### 3.1 `SeasonSignalResolver` — die Trigger-Kaskade (beste Quelle gewinnt)

```python
# app/business_logic/services/season_signal_resolver.py  (NEU)
from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional


@dataclass(frozen=True)
class SeasonSignal:
    """Das aufbereitete Kälte-/Wärme-Signal eines Standorts für einen Stichtag."""
    tier: Literal['live', 'climatological', 'calendar']
    #: Bewertete Nacht-/Tagesminimumtemperatur (°C) — None auf Kalender-Stufe.
    min_temp_c: Optional[float]
    #: Nächstes vorhergesagtes Frostdatum (nur Live-Stufe).
    forecast_first_frost_date: Optional[date]
    #: Klimatologische Frosttermine (Stufe 2/3), Format 'MM-DD'.
    estimated_first_frost_md: Optional[str]
    estimated_last_frost_md: Optional[str]
    reason_i18n_key: str


class SeasonSignalResolver:
    """Liefert für einen Standort das bestmögliche Saison-Signal.

    Kaskade (erste liefernde Stufe gewinnt):
      1. LIVE  — :WeatherForecast (Frost-/Min-Temp-Vorhersage, REQ-005/046)
                 und/oder Außentemperatur-Sensor (REQ-005). Bevorzugt, weil
                 tagesaktuell und standortnah.
      2. CLIMATOLOGICAL — :ClimateNormal.monthly_temp_min_c / coldest_month_min_c
                 (REQ-041) + HardinessZone.typical_first/last_frost_md (REQ-039).
      3. CALENDAR — Site.hemisphere + Preset-Monate (REQ-022) als grober Fallback.
    """

    async def resolve(self, site, on_date: date) -> SeasonSignal:
        live = await self._try_live(site, on_date)
        if live is not None:
            return live
        clim = await self._try_climatological(site, on_date)
        if clim is not None:
            return clim
        return self._calendar_fallback(site, on_date)

    async def _try_live(self, site, on_date) -> Optional[SeasonSignal]:
        """Nutzt die 7-Tage-Frost-/Min-Temp-Vorhersage (REQ-005/046) bzw. den
        aktuellen Außentemperatur-Sensorwert. Gibt None zurück, wenn der Standort
        weder eine aufgelöste Wetterquelle noch einen Außentemp-Sensor hat oder
        keine frischen Daten vorliegen (data_freshness CRITICAL, REQ-005)."""
        ...

    async def _try_climatological(self, site, on_date) -> Optional[SeasonSignal]:
        """Nutzt :ClimateNormal (REQ-041) + HardinessZone-Frosttermine (REQ-039).
        Gibt None zurück, wenn kein ClimateNormal/keine Zone für die GPS-Position
        vorliegt. min_temp_c = monthly_temp_min_c[on_date.month - 1]."""
        ...

    def _calendar_fallback(self, site, on_date) -> SeasonSignal:
        """Hemisphären-basierte Preset-Monate (REQ-022): Winterfenster
        Nov–Feb (northern) / Mai–Aug (southern). min_temp_c bleibt None —
        die Übergänge laufen rein monatsbasiert."""
        ...
```

### 3.2 Konfigurierbare Schwellwerte

```python
# Schwellwerte (Env-überschreibbar, §5). Werte in °C.
SEASON_PRE_WINTER_TEMP_C = 5.0    # erste Nacht < 5 °C (vorhergesagt/gemessen) → pre_winter
SEASON_FROST_TEMP_C      = 2.0    # < 2 °C → Frostgefahr → winter_dormancy (deckt sich
                                  #          mit der REQ-005-Frostwarnschwelle < 2 °C)
SEASON_SPRING_TEMP_C     = 10.0   # 7-Tage-Mittel-Min stabil > 10 °C → pre_spring
# Hysterese: Anzahl aufeinanderfolgender Signal-Tage bis zum Übergang.
SEASON_SIGNAL_THRESHOLD_DAYS = 3
```

### 3.3 `SeasonStateEngine` — reine Zustandslogik (Hysterese, kein I/O)

```python
# app/business_logic/engines/season_state_engine.py  (NEU)
class SeasonStateEngine:
    """Berechnet den nächsten SeasonPhase-Zustand aus dem aktuellen Zustand und
    dem aufbereiteten SeasonSignal. Deterministisch, ohne Datenbank-/HTTP-Zugriff.

    Invarianten:
    - Gerichteter Zyklus growing → pre_winter → winter_dormancy → pre_spring → growing.
    - Kein Rückwärtsübergang innerhalb desselben season_year (Oszillationsschutz,
      analog Aktorik-Hysterese REQ-018).
    - Ein Übergang erfordert SEASON_SIGNAL_THRESHOLD_DAYS aufeinanderfolgende
      Signaltage in dieselbe Richtung (consecutive_signal_days), damit ein
      einzelner Ausreißer-Tag keinen Umschalt-Flip auslöst. Auf der Kalender-Stufe
      (min_temp_c is None) entscheidet stattdessen das Monatsfenster sofort.
    """

    def next_phase(self, state: 'SeasonState', signal: SeasonSignal,
                   on_date: date) -> 'SeasonStateTransition':
        ...
```

**Übergangsregeln (Live-/Klimatologisch, temperaturbasiert):**

| Aus | Nach | Bedingung (nach Hysterese-Schwelle) |
|-----|------|--------------------------------------|
| `growing` | `pre_winter` | `min_temp_c ≤ SEASON_PRE_WINTER_TEMP_C` an ≥ N Folgetagen **oder** Live-Forecast enthält Frost innerhalb 7 Tagen |
| `pre_winter` | `winter_dormancy` | `min_temp_c ≤ SEASON_FROST_TEMP_C` (Frost eingetreten/unmittelbar vorhergesagt) |
| `winter_dormancy` | `pre_spring` | `min_temp_c` (7-Tage-Mittel) `> SEASON_SPRING_TEMP_C` an ≥ N Folgetagen **und** `on_date` liegt nach dem kältesten Monat (`coldest_month`, REQ-041) |
| `pre_spring` | `growing` | `on_date ≥ estimated_last_frost_md` **und** keine Frostvorhersage innerhalb 7 Tagen |

**Übergangsregeln (Kalender-Fallback, monatsbasiert — heutiges Verhalten):**

| Aus | Nach | Bedingung |
|-----|------|-----------|
| `growing` | `pre_winter` | Monat == `winter_action_month` (Template) bzw. Hemisphären-Default (Okt NH / Apr SH) |
| `pre_winter` | `winter_dormancy` | Erster Wintermonat (Nov NH / Mai SH) erreicht |
| `winter_dormancy` | `pre_spring` | Monat == `spring_action_month` bzw. Hemisphären-Default (Mär NH / Sep SH) |
| `pre_spring` | `growing` | Nach `estimated_last_frost_md` bzw. Ende des Frühlings-Fallback-Monats |

Der `season_year` wird beim Übergang `growing → pre_winter` gesetzt (bzw. beim ersten Winterlauf) und beim Übergang zurück nach `growing` freigegeben. Solange `season_year` gesetzt ist und `on_date` in dessen Winterhalbjahr liegt, blockiert die Engine Rückwärtsübergänge.

### 3.4 `OverwinteringMaterializer` — Auto-Ableitung des Instanz-Profils

```python
# app/business_logic/services/overwintering_materializer.py  (NEU)
class OverwinteringMaterializer:
    """Erzeugt/aktualisiert das instanzbezogene OverwinteringProfile aus dem
    Species-Template + Standort-Winterhärte-Ampel — ohne Nutzerinteraktion.

    Ausgelöst beim SeasonState-Übergang growing → pre_winter für jede Pflanze
    an einer Outdoor-/Greenhouse-Site (Dual-Support Run/standalone, REQ-013).
    """

    async def materialize(self, entity, site) -> Optional['OverwinteringProfile']:
        # 1. Winterhart? Ampel grün → keine Winterschutzmaßnahme nötig; kein
        #    Profil materialisieren (Winterschutz-Guard, REQ-022/039).
        rating = evaluate_winter_hardiness(          # REQ-039
            species_min_zone=species.hardiness_zones[0] if species.hardiness_zones else None,
            site_zone=site.hardiness_zone or site.climate_zone,
            frost_sensitivity=species.frost_sensitivity,
        )
        if rating == 'green':
            return None

        # 2. Template laden (Edge uses_overwintering_template / species_key-Match).
        template = await self._load_template(species)   # overwintering_profiles.yaml
        if template is None:
            # Kein §4.3-Template (echte Einjährige o. Datenlücke) → generischer
            # Default nach Ampel (yellow → mulch/fleece, red → move_indoors) + Log.
            template = self._fallback_from_rating(rating)

        # 3. Pfad-Zuordnung (Invariante D5): yellow → A, red → B. Validieren, dass
        #    template.winter_action zum Pfad passt (sonst korrigieren + Log).
        derived_path = 'A' if rating == 'yellow' else 'B'

        # 4. Profil upserten. Bestehendes user_overridden-Profil NICHT überschreiben,
        #    nur fehlende Felder additiv ergänzen.
        return await self._upsert(entity, template, derived_path, rating)
```

**Winterschutz-Guard (unverändert aus REQ-022):** Für Arten mit `frost_sensitivity`, die zur Ampel **grün** führt, wird **kein** Profil materialisiert und **keine** Winterschutz-Erinnerung erzeugt (verhindert irreführende Hinweise für z. B. Stiefmütterchen/Primeln).

### 3.5 `DormancyCareActivator` — Winterruhe-Pflegeplan schalten

```python
# app/business_logic/services/dormancy_care_activator.py  (NEU)
class DormancyCareActivator:
    """Schaltet den Dormancy-Care-Modus im CareProfile beim SeasonState-Übergang.

    Bei Eintritt in winter_dormancy (für eine Pflanze auf Pfad A ODER B):
      - CareProfile.dormancy_care_mode = True
      - CareProfile.dormancy_watering  = OverwinteringProfile.winter_watering
      - CareProfile.dormancy_check_interval_days aus storage_check_interval_days
      - Düngung ist bereits über DORMANCY_PHASES ausgesetzt (REQ-022); zusätzlich
        wird sichergestellt, dass die Pflanze eine Ruhe-Phase führt (Pfad A:
        dormancy-GrowthPhase REQ-003; Pfad B: geschützte Ruhe, Invariante D5).

    Bei Übergang nach pre_spring / growing:
      - dormancy_care_mode = False, Rückkehr zum saisonalen Normalbetrieb.
    """
    ...
```

**Effekt auf die `CareReminderEngine` (REQ-022):** Ist `dormancy_care_mode` aktiv, ersetzt die Gießlogik das `winter_watering_multiplier`-Intervall durch die diskrete `dormancy_watering`-Vorgabe:

| `dormancy_watering` | Gießverhalten |
|---------------------|---------------|
| `none` | Keine Gieß-Erinnerung (z. B. trocken gelagerte Knollen) |
| `minimal` | Erinnerung alle ~35–42 Tage („nur vor dem Austrocknen bewahren") |
| `reduced` | Erinnerung mit `winter_watering_multiplier × 1.5` |
| `normal` | Normales saisonales Intervall |

Zusätzlich generiert die Engine im Dormancy-Modus die neuen Kontroll-Erinnerungen `dormancy_health_check` (immer) und `quarter_climate_check` (nur wenn das Winterquartier Livedaten liefert).

### 3.6 Celery-Task-Einreihung

```python
@shared_task(name='season.evaluate_states')
def evaluate_season_states():
    """Täglicher Celery-Beat-Task (nach fetch_weather_forecasts, ~06:30 UTC):

    Für jede Site mit type ∈ {outdoor, greenhouse}:
      1. SeasonSignalResolver.resolve(site, today)  → bestes Signal (Kaskade)
      2. SeasonStateEngine.next_phase(state, signal, today)  → Übergang?
      3. Bei Übergang:
         - growing → pre_winter:      OverwinteringMaterializer.materialize(...)
                                      für alle Pflanzen der Site; erzeuge
                                      winter_protection / tuber_dig-Erinnerungen
                                      (REQ-022) je Pfad.
         - pre_winter → winter_dormancy: DormancyCareActivator (an);
                                      storage_check-Erinnerungen starten.
         - winter_dormancy → pre_spring: DormancyCareActivator (aus);
                                      erzeuge spring_uncover / harden_off /
                                      pre_sprouting-Erinnerungen je spring_action.
         - pre_spring → growing:      Saison abschließen (season_year freigeben).
      4. SeasonState persistieren (auch ohne Übergang: evaluated_at, Zähler).

    Idempotenz: Erinnerungen werden über REQ-022 (Duplikat-Prüfung pro
    [entity, reminder_type]) erstellt; ein zweiter Lauf am selben Tag erzeugt
    keine Duplikate und keinen zweiten Übergang.
    """
    ...

# Celery Beat (celery_config.py):
# 'evaluate-season-states-daily': {
#     'task': 'season.evaluate_states',
#     'schedule': crontab(hour=6, minute=30),   # nach dem Wetter-Fetch
# }
```

## 4. Frontend-Integration

Kein Anlege-Formular mehr. Die Automatik ist standardmäßig sichtbar; der Nutzer bestätigt nur Maßnahmen bzw. übersteuert punktuell. Mobile-First (Feedback), mit beschreibenden Texten und Fachbegriff-Erläuterungen (Feedback).

### 4.1 Dashboard-Widget „Saison & Überwinterung"

Erweitert das bestehende Winterschutz-Übersicht-Widget (REQ-022) um den Saison-Zustand:

- **Saison-Statuszeile** je Outdoor-Standort: aktueller `SeasonPhase` mit Icon (Blatt/fallendes Blatt/Schneeflocke/Knospe) und der Trigger-Quelle als dezentes Badge — `Live-Wetter` / `Klima-Schätzung` / `Kalender`. Das schafft Transparenz, ob die Warnung auf echten Daten oder einer Schätzung beruht.
- **Frost-Countdown:** bei Live-Daten „Erster Frost in X Tagen" (aus `forecast_first_frost_date`), sonst „Erster Frost typisch um {{datum}}" (aus `estimated_first_frost_md`).
- **Winterhärte-Ampel-Übersicht** (bestehend, REQ-022): „N grün / N gelb / N rot" mit Handlungsliste der rot/gelb-Pflanzen.
- **Winter-Checkliste:** offene vs. erledigte Winterschutz-/Einräum-Maßnahmen (aus den generierten Erinnerungen).

### 4.2 Rückhol-Assistent (Frühling)

Bei `pre_spring` erscheint auf dem Pflege-Dashboard (REQ-022) eine Frühlings-Sektion:
- Gestaffelte Abhärtungs-Anleitung (`harden_off`): „Tag 1–3: 2 h in den Halbschatten … Tag 7+: ganztags draußen" als Schritt-Checkliste.
- Knollen-Vorziehen (`pre_sprouting`), Abhäufeln (`uncover`), Rausstellen (`move_outdoors`) — je nach `spring_action` des Profils.
- Bei Live-Daten Warnhinweis, wenn trotz `pre_spring` noch Spätfrost vorhergesagt ist („Noch nicht rausstellen — Frost am {{datum}}").

### 4.3 Optionaler Override-Dialog (statt Pflicht-Formular)

Auf der Pflanzeninstanz-Detailseite ein Abschnitt **„Überwinterung"**, der das **auto-materialisierte** Profil anzeigt (read-only mit „automatisch aus Steckbrief"-Hinweis) und pro Feld einen „Anpassen"-Affordance bietet. Sobald der Nutzer etwas ändert, wird `user_overridden=True` gesetzt und die Automatik ergänzt künftig nur noch fehlende Felder. Ein „Auf Automatik zurücksetzen"-Button (`user_overridden=False`, re-materialisieren) ist vorhanden.

### 4.4 API-Endpunkte (tenant-scoped, REQ-024)

| Methode & Pfad | Zweck |
|----------------|-------|
| `GET /api/v1/t/{tenant_slug}/sites/{site_key}/season-state` | Aktuellen Saison-Zustand + Trigger-Quelle lesen |
| `GET /api/v1/t/{tenant_slug}/season/overview` | Aggregierte Saison-/Ampel-Übersicht über alle Outdoor-Sites (Dashboard-Widget) |
| `GET /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering` | Auto-materialisiertes OverwinteringProfile lesen (mit `auto_generated`/`user_overridden`/`derived_path`) |
| `PATCH /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering` | Einzelne Felder übersteuern (setzt `user_overridden=True`) |
| `POST /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/reset` | Auf Automatik zurücksetzen + re-materialisieren |

Fehlerbehandlung (NFR-006): `404` Site/Plant nicht gefunden; `409` kein SeasonState (reine Indoor-Site); `422` ungültiger Override-Wert bzw. Pfad-Widerspruch zur Ampel (Invariante D5).

### 4.5 i18n

Alle Strings DE (Default/Fallback) + EN. Namespaces: `pages.season.*` (Widget/Assistent), `enums.seasonPhase.*` (`growing`/`pre_winter`/`winter_dormancy`/`pre_spring`), `enums.seasonTriggerTier.*` (`live`/`climatological`/`calendar`), `pages.season.trigger.*` (Begründungstexte). Custom Hooks mit Objekt-/Array-Return via `useMemo` stabilisieren (Projektkonvention).

## 5. Konfiguration, Deployment & Lizenz

**Environment:**
- `SEASON_PRE_WINTER_TEMP_C` (Default `5.0`), `SEASON_FROST_TEMP_C` (Default `2.0`), `SEASON_SPRING_TEMP_C` (Default `10.0`) — Übergangs-Schwellwerte.
- `SEASON_SIGNAL_THRESHOLD_DAYS` (Default `3`) — Hysterese-Fenster.
- `SEASON_STATE_EVAL_ENABLED` (Default `true`) — Kill-Switch für den Celery-Task.

**Deployment:**
- Neue Collection `season_states` + Edge `has_season_state` im `kamerplanter_graph` (idempotente Migration, NFR-016). Additive Felder auf `overwintering_profiles`/`care_profiles` mit Defaults → kein Break auf Alt-Daten.
- **Migration bestehender OverwinteringProfiles:** Ein einmaliger, getrackter Migrationsschritt (NFR-016) setzt bei vorhandenen Profilen `user_overridden = auto_generated == false` (manuell gepflegte Profile behalten Vorrang) und leitet `derived_path` aus der Ampel ab. Datenverlust ausgeschlossen (rein additiv).
- Graceful Degradation: Fällt der Wetter-Fetch aus (REQ-005/046), degradiert der `SeasonSignalResolver` automatisch auf Stufe 2/3; der Task bleibt lauffähig. Kein Hard-Dependency auf externe Verfügbarkeit.

**Lizenz / DSGVO:** REQ-047 führt **keine** neuen externen Datenquellen ein — es konsumiert nur die bereits in REQ-005/041/046 beschafften und lizenzierten Daten (Attribution dort). Es verarbeitet keine zusätzlichen personenbezogenen Daten; der Saison-Zustand ist standort-, nicht personenbezogen.

## 6. Abhängigkeiten

- **REQ-022 (Pflegeerinnerungen):** Zentrale Erweiterung. REQ-047 materialisiert das dort definierte `OverwinteringProfile`, schaltet den Dormancy-Care-Modus im `CareProfile`, ergänzt zwei `ReminderType`-Werte und **verlagert den Auslöser** der Winter-/Frühlings-Erinnerungen von festen Monaten auf SeasonState-Übergänge (die Monatsfelder bleiben als Kalender-Fallback). **Harte Abhängigkeit; Rück-Querverweis in REQ-022 erforderlich.**
- **REQ-039 (Winterhärte):** Liefert `evaluate_winter_hardiness` (Ampel → Pfad-Zuordnung, Invariante D5) und die Zonen-Frosttermine (`typical_first/last_frost_md`) als Stufe-2-Eingang. **Harte Abhängigkeit; Rück-Querverweis erforderlich.**
- **REQ-005 (Hybrid-Sensorik/Wetter):** Liefert das Live-Frost-/Min-Temp-Signal (`:WeatherForecast.temp_min_c`, Frostwarnschwelle < 2 °C) und Außen-Sensorik als Stufe-1-Eingang. **Konsumierende Abhängigkeit; Rück-Querverweis erforderlich.**
- **REQ-046 (Wetterquellen):** Bestimmt via `WeatherSourceResolver`, ob ein Standort überhaupt Livedaten hat (Stufe-1-Verfügbarkeit). **Konsumierende Abhängigkeit.**
- **REQ-041 (NASA POWER / Klimanormale):** Liefert `:ClimateNormal.monthly_temp_min_c` / `coldest_month_min_c` als Stufe-2-Eingang (Saison-Fallback ohne Livedaten). **Konsumierende Abhängigkeit; Rück-Querverweis erforderlich.**
- **REQ-002 (Standort):** Liefert `Site.type` (Geltungsbereich Outdoor/Greenhouse), `hemisphere` (Stufe-3-Fallback), `gps_coordinates`, `hardiness_zone`/`climate_zone`, `tenant_key`. **Harte Abhängigkeit.**
- **REQ-001 (Stammdaten):** Liefert `Species.frost_sensitivity` und `hardiness_zones` für die Ampel/Materialisierung. **Lesende Abhängigkeit.**
- **REQ-003 (Phasensteuerung):** Die `dormancy`-GrowthPhase (Pfad A) und die Invariante D5 (Widerspruchsverbot Dormanz vs. Verlagerung) bleiben maßgeblich. **Konsistenz-Abhängigkeit.**
- **REQ-006 (Aufgabenplanung):** Alle Erinnerungen entstehen als `Task` (`category='care_reminder'`). **Nutzende Abhängigkeit.**
- **REQ-013 (Pflanzdurchlauf):** Dual-Support (Run/standalone) bei Materialisierung und Care-Modus. **Muster-Abhängigkeit.**
- **REQ-024 (Mandantenverwaltung):** `:SeasonState` tenant-scoped; Routen `/t/{tenant_slug}/`; Cross-Tenant-Edges verboten. **Harte Abhängigkeit.**
- **REQ-009 (Dashboard):** Beheimatet das Saison-/Überwinterungs-Widget. **UI-Abhängigkeit.**

## 7. Akzeptanzkriterien

- [ ] **AC-1 (Kein Pflicht-Profil):** Ein Nutzer erhält vollständige Winter-Hinweise und einen materialisierten Überwinterungs-Plan pro Pflanze, **ohne** je ein Überwinterungsprofil angelegt zu haben.
- [ ] **AC-2 (SeasonState je Outdoor-Site):** Für jede Site mit `type ∈ {outdoor, greenhouse}` existiert genau ein `:SeasonState`; reine Indoor-Sites erhalten keinen (Endpoint liefert 409).
- [ ] **AC-3 (Live-Trigger):** Hat der Standort eine aufgelöste Wetterquelle (REQ-046) mit Frostvorhersage < 2 °C, wechselt der Zustand innerhalb der Hysterese-Schwelle nach `pre_winter`/`winter_dormancy` — unabhängig vom Kalendermonat; `trigger_tier='live'`.
- [ ] **AC-4 (Klima-Fallback):** Ohne Livedaten, aber mit GPS/`:ClimateNormal`, leitet die Engine die Winter-/Frühlings-Fenster aus `monthly_temp_min_c` + Zonen-Frostterminen ab; `trigger_tier='climatological'`.
- [ ] **AC-5 (Kalender-Fallback):** Ohne Livedaten und ohne Klimanormale fällt die Engine auf hemisphären-basierte Preset-Monate zurück (heutiges Verhalten); `trigger_tier='calendar'`.
- [ ] **AC-6 (Hochstufung):** Wird für einen zuvor kalender-/klimageführten Standort eine Wetterquelle konfiguriert, nutzt der nächste Lauf automatisch die Live-Stufe.
- [ ] **AC-7 (Hysterese/Oszillationsschutz):** Ein einzelner warmer Tag bringt eine Pflanze nicht von `winter_dormancy` zurück; Rückwärtsübergänge innerhalb desselben `season_year` sind ausgeschlossen; ein Übergang erfordert `SEASON_SIGNAL_THRESHOLD_DAYS` konsistente Signaltage (Live/Klima-Stufe).
- [ ] **AC-8 (Auto-Materialisierung):** Beim Übergang `growing → pre_winter` wird für jede nicht-winterharte Pflanze (Ampel gelb/rot) ein `OverwinteringProfile` aus dem Species-Template + Ampel materialisiert (`auto_generated=True`, `derived_path` gesetzt, `source_template_key` referenziert).
- [ ] **AC-9 (Winterschutz-Guard):** Für winterharte Arten (Ampel grün) wird **kein** Profil materialisiert und **keine** Winterschutz-Erinnerung erzeugt.
- [ ] **AC-10 (Pfad-Konsistenz, Invariante D5):** `derived_path` und `winter_action` widersprechen der Ampel nie; ein Override, der die Invariante verletzt, wird mit 422 abgewiesen.
- [ ] **AC-11 (Override-Schutz):** Ein `user_overridden`-Profil wird von der Auto-Materialisierung **nie** überschrieben; nur fehlende Felder werden additiv ergänzt.
- [ ] **AC-12 (Dormancy-Care-Modus an):** Beim Eintritt in `winter_dormancy` wird `CareProfile.dormancy_care_mode=True` gesetzt; Gießen folgt `dormancy_watering` (none/minimal/reduced/normal), Düngen ist ausgesetzt.
- [ ] **AC-13 (Winter-Kontrolle):** Im Dormancy-Modus erscheint `dormancy_health_check` im konfigurierten Intervall; bei Winterquartier mit Livedaten löst eine Temperaturverletzung (`winter_quarter_temp_min/max`) `quarter_climate_check` (Priorität high) aus.
- [ ] **AC-14 (Rückhol-Assistent):** Beim Übergang `winter_dormancy → pre_spring` wird der Dormancy-Modus beendet und es erscheinen `spring_uncover`/`harden_off`/`pre_sprouting`-Erinnerungen gemäß `spring_action`; bei Live-Spätfrost wird vor dem Rausstellen gewarnt.
- [ ] **AC-15 (Trigger-Transparenz):** Das Dashboard zeigt je Standort den Saison-Zustand **und** die Trigger-Quelle (Live-Wetter / Klima-Schätzung / Kalender) sichtbar an.
- [ ] **AC-16 (Idempotenz):** Ein zweiter `evaluate_season_states`-Lauf am selben Tag erzeugt weder doppelte Übergänge noch doppelte Erinnerungen.
- [ ] **AC-17 (Tenant-Isolation):** `:SeasonState` erbt `tenant_key` von der Site; fremde Sites/Cross-Tenant-Zugriffe werden abgewiesen (403/422); Routen tenant-scoped.
- [ ] **AC-18 (Graceful Degradation):** Fällt der Wetter-Fetch aus, degradiert der Resolver auf Stufe 2/3 und der Task bleibt lauffähig — keine Winterfunktion bricht.
- [ ] **AC-19 (Migration):** Bestehende OverwinteringProfiles werden verlustfrei migriert (`user_overridden`/`derived_path` gesetzt); manuell gepflegte Profile behalten Vorrang.
- [ ] **AC-20 (i18n):** Alle neuen UI-Strings liegen in DE und EN vor; DE ist Default/Fallback.
