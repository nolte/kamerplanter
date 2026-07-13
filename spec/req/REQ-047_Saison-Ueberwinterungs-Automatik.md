# Spezifikation: REQ-047 - Saison- & Überwinterungs-Automatik

```yaml
ID: REQ-047
Titel: Automatische Saison- & Überwinterungs-Steuerung — Winter-/Frühlings-Erkennung aus Live- und Klimadaten, ohne manuelle Profile
Kategorie: Pflege & Erinnerungen / Automatisierung
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, React 19, TypeScript 5.9, MUI 7, Redux Toolkit
Status: Umgesetzt (Kern PR #406/#410; Vertiefungen §§3.7–3.10 teils als Ausbaustufe „noch nicht implementiert" markiert)
Version: 1.4
Abhängigkeit: REQ-022 (Pflegeerinnerungen/OverwinteringProfile/CareProfile — erweitert), REQ-039 (Winterhärte-Ampel + Frost-Defaults), REQ-005 (Wetter-/Frost-Livedaten), REQ-046 (Wetterquellen-Auflösung), REQ-041 (Klimanormale als Saison-Fallback), REQ-002 (Standort — Innen/Außen, GPS, Hemisphäre), REQ-001 (frost_sensitivity), REQ-003 (dormancy-Phase, Invariante D5), REQ-006 (Task-Erzeugung), REQ-013 (Run/Dual-Support), REQ-024 (Mandanten-Scoping)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.4 | 2026-07-13 | **ADR-006 E1/E3 per-Instanz-Gating (Epic #565 Phase 2):** Das E3-Instanz-Gating des `SeasonPhaseCoupler` liest jetzt die zentrale `resolve_effective_cycle`-Kaskade (REQ-003 v2.13) statt die konservative Inline-Auflösung. Damit gilt der neue **per-Instanz-Override** `PlantInstance.cultivation_cycle_type` auch für die Saison-Kopplung: eine als `annual` geführte Instanz an einem mehrjährigen Standort wird **nicht** in `dormancy`/Neustart getrieben (der einjährige Nutzer-Wille schlägt das Standort-Signal), während eine als `perennial` geführte Instanz einer ansonsten einjährigen Art in Dormanz/Neustart läuft. Der Season-State bleibt der klima-/kalendergetriebene Taktgeber; die Instanz-Kaskade bleibt die Wahrheit über die Zyklus-Natur. |
| 1.3 | 2026-07-13 | **ADR-006 E3-Kopplung verdrahtet (Epic #565 Phase 1, WP-3):** Der Season-State treibt jetzt real die REQ-003-**Wachstumsphase**, nicht mehr nur den Pflege-Modus. Neuer `SeasonPhaseCoupler`: beim Übergang → `winter_dormancy` wird die Wachstumsphase effektiv mehrjähriger Pflanzen auf `dormancy` gesetzt, beim Übergang → `pre_spring` der Perennierungs-Zyklus am Restart-Anker neu gestartet (Zyklusnummer inkrementiert). Aufruf im `SeasonStateService`-Transition-Sideeffect (best-effort/`_safe`, bricht die Standort-Auswertung nie ab). **Instanz-Gating konservativ** (ADR-006 E3): getrieben wird nur, wenn der *praktizierte* Zyklus der Art perennierend ist (`LifecycleConfig.cultivation_cycle_type` → botanische `cycle_type`, sonst PhaseSequence-`cycle_type`) — eine effektiv einjährige Instanz an einem mehrjährigen Standort wird **nicht** in Dormanz/Neustart gezwungen. Die zentrale `resolve_effective_cycle`-Kaskade (E1/Phase 2) ist noch nicht da; das Gating nimmt sie nicht vorweg. |
| 1.2 | 2026-07-12 | **ADR-006 (Epic #565, E3-Kopplung):** Verweis auf `spec/decisions/ADR-006-perennial-lifecycle-model.md`. Das ADR entscheidet (E3), dass der standortweite Season-State künftig die **Wachstumsphasen** der Instanzen treibt (`winter_dormancy` → Phase `dormancy`, `pre_spring` → Zyklus-Neustart) — heute schaltet er nur den Pflege-Modus. Konfliktauflösung: die Anwendung auf eine Instanz ist über die `resolve_effective_cycle`-Kaskade (REQ-003) **instanz-gegatet** — eine effektiv einjährige Instanz an einem mehrjährigen Standort wird nicht in Dormanz/Neustart gezwungen. Reine Entscheidung, keine Code-Änderung in dieser Version. |
| 1.0 | 2026-07-05 | Initialer Entwurf. Konzeptionelle Überarbeitung des Überwinterungs-Managements: Der Nutzer legt **keine** Überwinterungsprofile mehr an. Führt die **SeasonState-Engine** ein — eine pro Outdoor-Standort berechnete Saison-Zustandsmaschine, die den Übergang in die Winterruhe (Schutz/Einräumen) und die Rückholung (Ausräumen/Abhärten) automatisch triggert. Trigger-Kaskade: Live-Wetter/Sensorik (REQ-005/046) → Klimanormale (REQ-041) → Kalender/Hemisphäre-Fallback. Verlagert die in REQ-022 datumsbasierten Winter-/Frühlings-Erinnerungen auf zustandsbasierte Auslösung, materialisiert das `OverwinteringProfile` automatisch aus dem Species-Template (REQ-022) + Standort-Ampel (REQ-039) und schaltet einen **Dormancy-Care-Modus** (Winterruhe-Pflegeplan) im CareProfile ein. |
| 1.1 | 2026-07-11 | **Angleichung an den implementierten Stand (PR #406/#410) + fachliche Vertiefung.** Status Entwurf→Umgesetzt. *Angeglichen:* `season_year: Optional[int]`; klimatologische Stufe 2 speist real aus den Standort-Durchschnittsfrostdaten (REQ-002/015-A), der kälteste Monat aus hemisphären-basierten Monatsmengen — REQ-041-Klimanormale als künftiger Ausbaupfad markiert; zusätzliche Saison-Fenster-Guards, Zusatz-Endpunkt `overwintering/status` (#410) und Config `SEASON_LIVE_FORECAST_WINDOW_DAYS` dokumentiert; synchrone Implementierung vermerkt; `quarter_climate_check` als periodische Kontrolle beschrieben (Ist/Soll-Temperaturvergleich als Ausbaustufe markiert). *Vertieft (neue §§3.7–3.10):* Winterquartier/Pfad B, Frühjahrs-Rückholung/Abhärtung, Arten-Sonderfälle, Automatik-Robustheit — je mit neuen Akzeptanzkriterien (AC-21 ff.). Fachliche Werte verweisen auf die Steckbriefe §4.3 (SSOT), statt sie zu duplizieren. |

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
| 2 — Klimatologisch | Standort-Durchschnittsfrostdaten (`first/last_frost_date_avg`, `eisheilige_date`, REQ-002/015-A) + `HardinessZone.typical_first/last_frost_md` (REQ-039). *Ausbaupfad (noch nicht implementiert):* `:ClimateNormal.monthly_temp_min_c` / `coldest_month_min_c` (REQ-041) — Modell vorhanden, von der Season-Engine noch nicht konsumiert. | Standort hat GPS bzw. Frost-Richtwerte, aber keine Livedaten | Standortgenaue, aber statische Saison-Schätzung |
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
    - `season_year: Optional[int]` (Bezugsjahr der laufenden Überwinterungssaison — der Winter 2026/27 wird als `2026` geführt; verhindert Rücksprünge innerhalb derselben Saison, s. Hysterese. `None` während `growing` außerhalb einer laufenden Saison; gesetzt beim Übergang `growing → pre_winter`, freigegeben bei `pre_spring → growing`)
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
| Winterquartier-Klima-Warnung | `quarter_climate_check` | Ist-Stand: periodisch, sobald das Winterquartier Livedaten (Sensor/HA) liefert. *Ausbaustufe (noch nicht implementiert, §3.7.3 / AC-22):* Auslösung erst bei Verletzung von `winter_quarter_temp_min/max` | `high` (Pflanze erfriert/treibt vorzeitig) |

Die bestehenden Winter-Erinnerungstypen (`winter_protection`, `spring_uncover`, `tuber_dig`, `storage_check`) bleiben unverändert — geändert wird **nur ihr Auslöser** (SeasonState-Übergang statt fester Monat, §3.4). (`location_check` ist ein generischer, saisonunabhängiger Erinnerungstyp aus REQ-022 und gehört **nicht** zu dieser Winter-Gruppe.)

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
      2. CLIMATOLOGICAL — Standort-Durchschnittsfrostdaten (first/last_frost_date_avg,
                 eisheilige_date, REQ-002/015-A) + HardinessZone.typical_first/last_frost_md
                 (REQ-039). Ausbaupfad (noch nicht implementiert): :ClimateNormal (REQ-041).
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
        """Ist-Stand: nutzt die Standort-Durchschnittsfrostdaten
        (first/last_frost_date_avg, eisheilige_date, REQ-002/015-A) +
        HardinessZone-Frosttermine (REQ-039). Gibt None zurück, wenn dem Standort
        diese Frost-Richtwerte fehlen.
        Ausbaupfad (noch nicht implementiert): Ableitung von min_temp_c aus
        :ClimateNormal.monthly_temp_min_c[on_date.month - 1] (REQ-041)."""
        ...

    def _calendar_fallback(self, site, on_date) -> SeasonSignal:
        """Hemisphären-basierte Preset-Monate (REQ-022): Winterfenster
        Nov–Feb (northern) / Mai–Aug (southern). min_temp_c bleibt None —
        die Übergänge laufen rein monatsbasiert."""
        ...
```

> **Hinweis (Ist-Stand):** Die Implementierung ist **synchron** (python-arango, kein
> async-I/O); die `async`-Signaturen in dieser Skizze sind illustrativ. Der Resolver ist
> deterministisch bis auf die injizierten Repositories und ohne HTTP-Zugriff im Kernpfad
> testbar.

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
    - Zusätzliche Saison-Fenster-Guards (Ist-Stand): ein growing → pre_winter-Übergang
      wird nur innerhalb der Herbst-/Winter-Monatsmenge (_PRE_WINTER_SEASON_MONTHS)
      zugelassen; ein winter_dormancy → pre_spring-Übergang frühestens
      _SPRING_RELEASE_WINDOW_DAYS = 182 Tage nach Saisonbeginn. Beides verhindert
      Fehlübergänge bei sommerlichen Kälte- bzw. spätwinterlichen Wärme-Ausreißern.
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
| `winter_dormancy` | `pre_spring` | `min_temp_c` (7-Tage-Mittel) `> SEASON_SPRING_TEMP_C` an ≥ N Folgetagen **und** `on_date` liegt nach dem kältesten Monat (Ist-Stand: hemisphären-basierte Monatsmenge `_AFTER_COLDEST_MONTHS`; Ausbaupfad `ClimateNormal.coldest_month_min_c`, REQ-041) |
| `pre_spring` | `growing` | `on_date ≥ estimated_last_frost_md` **und** keine Frostvorhersage innerhalb 7 Tagen |

**Übergangsregeln (Kalender-Fallback, monatsbasiert — heutiges Verhalten):**

| Aus | Nach | Bedingung |
|-----|------|-----------|
| `growing` | `pre_winter` | Monat == `winter_action_month` (Template) bzw. Hemisphären-Default (Okt NH / Apr SH) |
| `pre_winter` | `winter_dormancy` | Erster Wintermonat (Nov NH / Mai SH) erreicht |
| `winter_dormancy` | `pre_spring` | Monat == `spring_action_month` bzw. Hemisphären-Default (Mär NH / Sep SH) |
| `pre_spring` | `growing` | Nach `estimated_last_frost_md` bzw. Ende des Frühlings-Fallback-Monats |

Der `season_year` wird beim Übergang `growing → pre_winter` gesetzt (bzw. beim ersten Winterlauf) und beim Übergang zurück nach `growing` freigegeben. Solange `season_year` gesetzt ist und `on_date` in dessen Winterhalbjahr liegt, blockiert die Engine Rückwärtsübergänge.

**Saison-Fenster-Guards (Ist-Stand, Werte je Hemisphäre aus `Site.hemisphere`):**

| Guard | Nordhalbkugel | Südhalbkugel | Wirkung |
|-------|---------------|--------------|---------|
| `_PRE_WINTER_SEASON_MONTHS` | {8, 9, 10, 11, 12} | {2, 3, 4, 5, 6} | Ein temperaturgetriebener `growing → pre_winter`-Übergang feuert nur in diesen Monaten (bindet den Live-Einstieg an das Herbst-/Winterhalbjahr). |
| `_AFTER_COLDEST_MONTHS` | {2, 3, 4, 5, 6} | {8, 9, 10, 11, 12} | Der `winter_dormancy → pre_spring`-Übergang setzt voraus, dass `on_date` in einem der Monate nach dem kältesten Monat liegt. |
| `_SPRING_RELEASE_WINDOW_DAYS` | `182` | `182` | Zusätzliche Schranke für `winter_dormancy → pre_spring`: der Abstand zum durchschnittlichen letzten Frost muss ≤ 182 Tage (halbes Jahr) betragen. |

Für den Übergang `winter_dormancy → pre_spring` gelten die Temperaturbedingung (§3.3-Tabelle oben), der `_AFTER_COLDEST_MONTHS`-Guard **und** die `_SPRING_RELEASE_WINDOW_DAYS`-Schranke **kumulativ** — alle drei müssen erfüllt sein.

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

### 3.7 Vertiefung: Winterquartier & Pfad B (Verlagerung)

Pfad B (`derived_path='B'`, Ampel rot) verlagert die Pflanze aus dem Freiland in ein
**Winterquartier** (Indoor-Location) oder ein **Knollenlager**. Der Herkunfts-Standort
(Outdoor-Site) bleibt für die Saison-Übergänge maßgeblich (§1 Geltungsbereich); das
Quartier stellt nur die Pflegebedingungen der geschützten Ruhe dar. Diese Vertiefung
präzisiert die Quartier-Typen, den Ein-/Ausräum-Prozess und die Lager-Kontrolle. **Die
art-spezifischen Werte (Ziel-Temperatur, Licht, Gießregime, Lagermedium, Kontrollintervall)
sind Single Source of Truth (SSOT) in den Steckbriefen §4.3 Überwinterung** und werden in die
`overwintering_profiles`-Templates extrahiert (REQ-022); dieses Dokument definiert die
**Semantik**, nicht die Werte.

#### 3.7.1 Quartier-Typen (aus vorhandenen Feldern klassifiziert)

Die bestehenden Felder `winter_quarter_temp_min/max` und `winter_quarter_light`
(OverwinteringProfile, REQ-022) spannen einen Quartier-Typ auf. Die Engine leitet daraus
den passenden Dormancy-Care-Modus (§3.5) und die Kontroll-Erinnerungen ab:

| Quartier-Typ | Klassifikations-Grenzen (grobe Orientierung; art-spezifische Werte bleiben SSOT in §4.3) | Typische Kandidaten | `winter_watering` |
|--------------|-----------------------------------|---------------------|-------------------|
| **Kalt-dunkel (Knollenlager)** | ~2–8 °C, `dark`, kein Licht nötig | Dahlien-, Gladiolen-, Canna-Knollen | `none` |
| **Kalt-hell (Frostschutzhaus)** | ~0–8 °C, `semi_bright`/`bright` | Kübel-Lavendel, Oleander, Feige, Olive | `minimal` |
| **Temperiert-hell (frostfrei)** | ~8–15 °C, `bright` (`frost_free`) | Zitrus, Pelargonien, Fuchsien, immergrüne Kübelpflanzen | `reduced` |
| **Warm-hell (Zimmer)** | > 15 °C, `bright` | tropische Kübelpflanzen ohne echte Ruhe | `normal` |

Der Quartier-Typ ist **abgeleitet, kein neues Feld** — er ergibt sich deterministisch aus
`winter_quarter_temp_min/max` + `winter_quarter_light`. Fehlen diese im Template, greift der
Ampel-Fallback (rot → `move_indoors`, generisches Temperiert-hell-Default) mit Log-Hinweis.

#### 3.7.2 Ein-/Ausräum-Prozess (zustandsgesteuert)

- **Einräumen (Übergang `pre_winter`):** Für Pfad-B-Pflanzen erzeugt der Task neben
  `winter_protection`/`tuber_dig` eine **`move_indoors`-Handlungsaufforderung** mit dem
  Ziel-Quartier (`winter_quarter_key`, falls gesetzt) und den Ziel-Bedingungen aus dem
  Template. Der physische Umzug ist eine vom Nutzer zu bestätigende Aufgabe (REQ-006),
  keine Automatik.
- **Verlagerung folgt der Ampel/Frostgefahr, nicht dem Kalender:** Bei Live-Daten (Stufe 1)
  wird der Einräum-Hinweis **vor** dem ersten vorhergesagten Frost (< `SEASON_FROST_TEMP_C`)
  fällig; ohne Live-Daten greift die klimatologische/Kalender-Stufe.
- **Ausräumen (Übergang `pre_spring`):** siehe §3.8 (abgestimmt auf das Ende der
  Frostgefahr, mit Abhärtung).

#### 3.7.3 Fäulnis-, Feuchte- & Schädlingskontrolle im Lager

`dormancy_health_check` (REQ-022/047) wird im Dormancy-Modus im Intervall
`dormancy_check_interval_days` erzeugt. Diese Vertiefung präzisiert **Zweck und Inhalt** der
Kontrolle je Quartier-Typ (Checklisten-Text i18n, SSOT-Details in §4.3):

- **Knollenlager (kalt-dunkel):** weiche/faulende Stellen herausschneiden, Austrocknung
  prüfen, Lagermedium (`storage_medium`, z. B. Vermiculit/Perlite/Sägemehl) auf Feuchte
  prüfen. Bezug: §4.3-Einlagerungs-Protokoll der Art (z. B. Dahlie).
- **Kalt-/temperiert-hell:** Grauschimmel (*Botrytis*) an abgestorbenem Laub entfernen,
  Staunässe vermeiden, auf Schild-/Woll-/Spinnmilben-Befall in der warmen Ruhe achten
  (IPM-Verweis REQ-010), Lüften an frostfreien Tagen.

**Ausbaustufe (noch nicht implementiert):** `quarter_climate_check` wertet heute periodisch die
Quartier-Livedaten aus (sobald welche vorliegen). Zielbild ist die **ereignisbasierte Auslösung
bei tatsächlicher Verletzung** von `winter_quarter_temp_min/max` (z. B. Heizungsausfall →
Quartier fällt unter Mindesttemperatur → sofortige `high`-Warnung; oder Quartier zu warm →
vorzeitiger Austrieb). Dies erfordert einen Ist/Soll-Vergleich der Quartier-Livedaten gegen
die Template-Grenzen und ist als Folge-Implementierung markiert (AC-13, AC-22).

### 3.8 Vertiefung: Frühjahrs-Rückholung & Abhärtung

Der Übergang `winter_dormancy → pre_spring` beendet den Dormancy-Modus (§3.5) und startet
den **Rückhol-Prozess**. Diese Vertiefung präzisiert die gestaffelte Abhärtung, das
Knollen-Vorziehen und den Spätfrost-Schutz. `spring_action` ∈ {`uncover`, `move_outdoors`,
`replant`, `prune`, `harden_off`} (REQ-022) bestimmt den Prozess je Pflanze.

#### 3.8.1 Gestaffelte Abhärtung (`harden_off`)

Verlagerte oder im Warmquartier getriebene Pflanzen müssen **schrittweise** an Freiland-Licht,
-Wind und -Temperatur gewöhnt werden (Sonnenbrand-/Kälteschock-Schutz). Die Engine erzeugt
bei `spring_action='harden_off'` einen **mehrstufigen Abhärtungsplan** (Richtwerte, art-/
wetterabhängig verfeinert über §4.3 bzw. Live-Daten):

| Stufe | Fenster | Exposition |
|-------|---------|------------|
| 1 | Tag 1–3 | 2–3 h Halbschatten, windgeschützt, tagsüber |
| 2 | Tag 4–6 | halbtags Halbschatten, abends wieder rein |
| 3 | Tag 7–10 | ganztags draußen, nachts noch geschützt |
| 4 | ab Tag 10 | dauerhaft draußen, sofern keine Frostvorhersage |

Der Plan erscheint als Schritt-Checkliste im Rückhol-Assistenten (§4.2). **Live-Kopplung:**
Liegt in einer Stufe eine Frostvorhersage (< `SEASON_FROST_TEMP_C`) vor, pausiert der Plan
(„heute nicht rausstellen").

#### 3.8.2 Knollen-Vorziehen & Auspflanzen

Für `tuber_status`-geführte Arten (REQ-022) staffelt der Prozess: `pre_sprouting`
(Vorziehen im Warmen, z. B. ab März) → `growing` → `move_outdoors`/`replant` **erst nach**
`estimated_last_frost_md` (bzw. nach den Eisheiligen bei entsprechendem Richtwert). Die
konkreten Monate/Temperaturen sind SSOT in §4.3 (z. B. Dahlie: März vorziehen, Mai auspflanzen).

#### 3.8.3 Spätfrost-Schutz (Live)

Solange `on_date < estimated_last_frost_md` **oder** eine Frostvorhersage innerhalb 7 Tagen
vorliegt, unterbleibt der `pre_spring → growing`-Übergang (Übergangsregel §3.3) und der
Rückhol-Assistent zeigt eine Spätfrost-Warnung mit dem konkreten Frostdatum. Das schützt vor
verfrühtem endgültigem Ausräumen/Abhäufeln.

### 3.9 Vertiefung: Arten & Sonderfälle

Diese Vertiefung schließt Abdeckungslücken bei Arten-Klassen, die die bisherige gelb/rot-
Zweiteilung nicht sauber treffen. **Keine art-spezifischen Werte hier** — nur die
Klassifikations-Semantik; die Werte bleiben SSOT in §4.3.

- **Immergrüne / wintergrüne Arten (Pfad A mit Zusatz):** behalten Laub und verdunsten auch
  im Winter → zusätzlich **Frosttrocknis-Risiko**. Über den Winterschutz (`fleece`/schattieren
  an sonnigen Frosttagen) hinaus generiert die Engine an frostfreien Tagen einen
  Gieß-Kontrollhinweis (`winter_watering='minimal'` statt `none`), auch wenn die Pflanze
  in-situ (Pfad A) bleibt.
- **Grenzwertig-winterharte Arten (Ampel-Grenzfall gelb↔rot):** Bei Zonendifferenz genau an
  der Schwelle (REQ-039 `delta`) hängt der Pfad von der konkreten Standort-Ampel ab. Der
  materialisierte Pfad (A/B) wird mit `trigger_reason_i18n_key` begründet („Standort 7a, Art
  grenzwertig → Schutz empfohlen"); ein Nutzer-Override kann bewusst auf den milderen/strengeren
  Pfad wechseln (Invariante D5 bleibt gewahrt).
- **Kübel vs. Beet (gleiche Art, anderer Pfad):** Dieselbe Art ist im Beet oft Pfad A
  (in-situ, `dormancy`), im Kübel Pfad B (Wurzelballen friert im Topf schneller durch). Die
  Unterscheidung folgt der **Location/Substrat-Situation** der Pflanze (REQ-002/019), nicht
  nur der Art. §4.3-Steckbriefe führen dazu die „Beet"- und „Kübel"-Varianten (vgl. Lavendel:
  Beet `none` / Kübel Frostschutzhaus). *Ausbaustufe (noch nicht implementiert):* automatische
  Pfad-Verschärfung Kübel→B über eine `container`-Kennzeichnung der Pflanzung.
- **Beheiztes vs. kaltes Gewächshaus (`type='greenhouse'`):** Heute behandelt die Engine
  `greenhouse` wie `outdoor`. Ein **beheiztes** Gewächshaus verschiebt aber die effektiven
  Frost-/Winter-Schwellen (die Innentemperatur folgt nicht der Außenluft). *Ausbaustufe (noch
  nicht implementiert):* ein `greenhouse_heated`-Flag bzw. eine Quartier-Innensensorik (Stufe
  1 des Quartiers) als maßgebliche Signalquelle statt der Außenprognose. Bis dahin gilt der
  Außen-/Kalender-Fallback mit Hinweis-Text.
- **Zwei-/mehrjährige Sonderfälle:** Zweijährige (Blüte im 2. Jahr) und monokarpische Arten
  brauchen die Überwinterung genau **einmal** vor der Blühsaison; die Saison-Automatik bleibt
  jahresweise (`season_year`) korrekt, muss aber nach Blüte/Absterben kein neues Profil
  materialisieren (Konsistenz mit REQ-003 Lebenszyklus / klonaler Fortführung).

### 3.10 Vertiefung: Automatik-Robustheit & Edge Cases

Diese Vertiefung härtet die Zustandsmaschine an den Rändern. Jeder Punkt ist als prüfbares Kriterium in §7
(AC-25 ff.) gespiegelt.

- **Mehrjahres-Hysterese:** Über `season_year` hinaus muss ein Standort, der eine volle Saison
  durchlaufen hat, im Folgejahr sauber neu starten (`season_year` freigegeben bei
  `pre_spring → growing`; neuer Winter setzt neuen `season_year`). Kein „Hängenbleiben" in
  `pre_spring`, wenn der Frühling ausbleibt bzw. der nächste Herbst beginnt.
- **Mildwinter / Kahlfrost:** Bleibt echter Frost aus (Mildwinter), darf die Engine trotzdem
  aus `pre_winter` nicht endlos hin- und herschalten; die Saison-Fenster-Guards (§3.3) und die
  Hysterese-Tage decken das ab. **Kahlfrost** (Frost ohne Schnee) ist über die Live-Min-Temp
  bereits erfasst — die Schutz-Erinnerung hängt an der Temperatur, nicht an Schnee.
- **Quellen-Hochstufung mitten in der Saison:** Wird für einen kalender-/klimageführten
  Standort mitten im Winter eine Wetterquelle konfiguriert (Stufe 1 wird verfügbar), übernimmt
  der nächste Lauf die Live-Stufe **ohne** einen bereits erreichten Zustand rückwärts zu
  brechen (Rückwärts-Verbot innerhalb `season_year`). `trigger_tier` wechselt auf `live`.
- **Fehlende / veraltete Daten:** Fällt die Live-Quelle aus (`data_freshness` CRITICAL,
  REQ-005), degradiert der Resolver auf Stufe 2/3 (Graceful Degradation, AC-18) — der Zustand
  bleibt erhalten, `trigger_tier` spiegelt die real genutzte Stufe. Kein Zustandssprung allein
  durch Datenausfall.
- **Override-Konflikte:** Ein `user_overridden`-Profil bleibt von der Auto-Materialisierung
  unangetastet (AC-11); ein Override, der die Ampel/Invariante D5 verletzt, wird mit 422
  abgewiesen (AC-10). Setzt der Nutzer das Profil auf Automatik zurück (`reset`), wird beim
  nächsten `pre_winter`-Lauf neu materialisiert.
- **Idempotenz-Grenzfälle:** Mehrere Läufe am selben Tag, ein Nachhol-Lauf nach Ausfall oder
  ein Zeitzonen-/Datumsgrenzen-Fall erzeugen **weder** doppelte Übergänge **noch** doppelte
  Erinnerungen (AC-16, Duplikat-Prüfung pro `[entity, reminder_type]`, REQ-022).

## 4. Frontend-Integration

Kein Anlege-Formular mehr. Die Automatik ist standardmäßig sichtbar; der Nutzer bestätigt nur Maßnahmen bzw. übersteuert punktuell. Mobile-First (Feedback), mit beschreibenden Texten und Fachbegriff-Erläuterungen (Feedback).

### 4.1 Dashboard-Widget „Saison & Überwinterung"

Erweitert das bestehende Winterschutz-Übersicht-Widget (REQ-022) um den Saison-Zustand (Ist-Stand: realisiert als `SeasonOverviewPanel` **innerhalb** des Dashboard-Widgets `winter_protection`, kein eigener Widget-Registry-Eintrag):

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
| `GET /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/status` | Materialisierungs-Status ohne Profil-Zwang: `has_profile` / `hardiness_light` / `will_materialize` / `site_overwinterable` (4-State-Antwort, auch für Pflanzen ohne Profil; Folge-PR #410) |
| `PATCH /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering` | Einzelne Felder übersteuern (setzt `user_overridden=True`) |
| `POST /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/reset` | Auf Automatik zurücksetzen + re-materialisieren |

Fehlerbehandlung (NFR-006): `404` Site/Plant nicht gefunden; `409` kein SeasonState (reine Indoor-Site); `422` ungültiger Override-Wert bzw. Pfad-Widerspruch zur Ampel (Invariante D5).

### 4.5 i18n

Alle Strings DE (Default/Fallback) + EN. Namespaces: `pages.season.*` (Widget/Assistent), `enums.seasonPhase.*` (`growing`/`pre_winter`/`winter_dormancy`/`pre_spring`), `enums.seasonTriggerTier.*` (`live`/`climatological`/`calendar`), `pages.season.trigger.*` (Begründungstexte). Custom Hooks mit Objekt-/Array-Return via `useMemo` stabilisieren (Projektkonvention).

## 5. Konfiguration, Deployment & Lizenz

**Environment:**
- `SEASON_PRE_WINTER_TEMP_C` (Default `5.0`), `SEASON_FROST_TEMP_C` (Default `2.0`), `SEASON_SPRING_TEMP_C` (Default `10.0`) — Übergangs-Schwellwerte.
- `SEASON_SIGNAL_THRESHOLD_DAYS` (Default `3`) — Hysterese-Fenster.
- `SEASON_LIVE_FORECAST_WINDOW_DAYS` (Default `7`) — Vorschau-Fenster für die Live-Frost-/Min-Temp-Auswertung (Stufe 1).
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
- **REQ-041 (NASA POWER / Klimanormale):** *Ausbaupfad (noch nicht implementiert):* soll `:ClimateNormal.monthly_temp_min_c` / `coldest_month_min_c` als verfeinerten Stufe-2-Eingang liefern. **Ist-Stand:** die Stufe 2 speist aus den Standort-Durchschnittsfrostdaten (REQ-002/015-A) + Zonen-Frostterminen (REQ-039); der kälteste Monat wird über hemisphären-basierte Monatsmengen bestimmt. **Vorgesehene Abhängigkeit.**
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
- [ ] **AC-4 (Klima-Fallback):** Ohne Livedaten, aber mit Standort-Durchschnittsfrostdaten (`first/last_frost_date_avg`, `eisheilige_date`, REQ-002/015-A) + Zonen-Frostterminen (REQ-039), leitet die Engine die Winter-/Frühlings-Fenster daraus ab; `trigger_tier='climatological'`. *Ausbaustufe (noch nicht implementiert):* verfeinerte Ableitung aus `:ClimateNormal.monthly_temp_min_c` (REQ-041).
- [ ] **AC-5 (Kalender-Fallback):** Ohne Livedaten und ohne Klimanormale fällt die Engine auf hemisphären-basierte Preset-Monate zurück (heutiges Verhalten); `trigger_tier='calendar'`.
- [ ] **AC-6 (Hochstufung):** Wird für einen zuvor kalender-/klimageführten Standort eine Wetterquelle konfiguriert, nutzt der nächste Lauf automatisch die Live-Stufe.
- [ ] **AC-7 (Hysterese/Oszillationsschutz):** Ein einzelner warmer Tag bringt eine Pflanze nicht von `winter_dormancy` zurück; Rückwärtsübergänge innerhalb desselben `season_year` sind ausgeschlossen; ein Übergang erfordert `SEASON_SIGNAL_THRESHOLD_DAYS` konsistente Signaltage (Live/Klima-Stufe).
- [ ] **AC-8 (Auto-Materialisierung):** Beim Übergang `growing → pre_winter` wird für jede nicht-winterharte Pflanze (Ampel gelb/rot) ein `OverwinteringProfile` aus dem Species-Template + Ampel materialisiert (`auto_generated=True`, `derived_path` gesetzt, `source_template_key` referenziert).
- [ ] **AC-9 (Winterschutz-Guard):** Für winterharte Arten (Ampel grün) wird **kein** Profil materialisiert und **keine** Winterschutz-Erinnerung erzeugt.
- [ ] **AC-10 (Pfad-Konsistenz, Invariante D5):** `derived_path` und `winter_action` widersprechen der Ampel nie; ein Override, der die Invariante verletzt, wird mit 422 abgewiesen.
- [ ] **AC-11 (Override-Schutz):** Ein `user_overridden`-Profil wird von der Auto-Materialisierung **nie** überschrieben; nur fehlende Felder werden additiv ergänzt.
- [ ] **AC-12 (Dormancy-Care-Modus an):** Beim Eintritt in `winter_dormancy` wird `CareProfile.dormancy_care_mode=True` gesetzt; Gießen folgt `dormancy_watering` (none/minimal/reduced/normal), Düngen ist ausgesetzt.
- [ ] **AC-13 (Winter-Kontrolle):** Im Dormancy-Modus erscheint `dormancy_health_check` im konfigurierten Intervall; hat das Winterquartier Livedaten (Sensor/HA), erscheint zusätzlich periodisch `quarter_climate_check` (Priorität high). *Ausbaustufe (noch nicht implementiert, s. §3.7):* Auslösung erst bei tatsächlicher Verletzung von `winter_quarter_temp_min/max` statt periodisch.
- [ ] **AC-14 (Rückhol-Assistent):** Beim Übergang `winter_dormancy → pre_spring` wird der Dormancy-Modus beendet und es erscheinen `spring_uncover`/`harden_off`/`pre_sprouting`-Erinnerungen gemäß `spring_action`; bei Live-Spätfrost wird vor dem Rausstellen gewarnt.
- [ ] **AC-15 (Trigger-Transparenz):** Das Dashboard zeigt je Standort den Saison-Zustand **und** die Trigger-Quelle (Live-Wetter / Klima-Schätzung / Kalender) sichtbar an.
- [ ] **AC-16 (Idempotenz):** Ein zweiter `evaluate_season_states`-Lauf am selben Tag erzeugt weder doppelte Übergänge noch doppelte Erinnerungen.
- [ ] **AC-17 (Tenant-Isolation):** `:SeasonState` erbt `tenant_key` von der Site; fremde Sites/Cross-Tenant-Zugriffe werden abgewiesen (403/422); Routen tenant-scoped.
- [ ] **AC-18 (Graceful Degradation):** Fällt der Wetter-Fetch aus, degradiert der Resolver auf Stufe 2/3 und der Task bleibt lauffähig — keine Winterfunktion bricht.
- [ ] **AC-19 (Migration):** Bestehende OverwinteringProfiles werden verlustfrei migriert (`user_overridden`/`derived_path` gesetzt); manuell gepflegte Profile behalten Vorrang.
- [ ] **AC-20 (i18n):** Alle neuen UI-Strings liegen in DE und EN vor; DE ist Default/Fallback.

**Vertiefung Winterquartier & Pfad B (§3.7):**

- [ ] **AC-21 (Quartier-Typ):** Der Quartier-Typ (kalt-dunkel / kalt-hell / temperiert-hell / warm-hell) wird deterministisch aus `winter_quarter_temp_min/max` + `winter_quarter_light` abgeleitet (kein neues Feld); der Dormancy-Care-Gießmodus folgt dem Typ. Keine art-spezifischen Werte im REQ-Text — Quelle ist §4.3 (SSOT).
- [ ] **AC-22 (Quartier-Klima-Auslösung, Ausbaustufe — noch nicht implementiert):** `quarter_climate_check` löst bei tatsächlicher Verletzung von `winter_quarter_temp_min/max` durch Quartier-Livedaten aus (Heizungsausfall → zu kalt; Überhitzung → vorzeitiger Austrieb), statt periodisch. Bis zur Umsetzung gilt AC-13 (periodisch).
- [ ] **AC-23 (Einräumen):** Beim Übergang `pre_winter` erhält jede Pfad-B-Pflanze eine `move_indoors`-Aufgabe mit Ziel-Quartier (`winter_quarter_key`, falls gesetzt) und Ziel-Bedingungen aus dem Template; der physische Umzug ist eine nutzerbestätigte Aufgabe (REQ-006), keine Automatik.

**Vertiefung Frühjahr & Abhärtung (§3.8):**

- [ ] **AC-24 (Abhärtung):** Bei `spring_action='harden_off'` erscheint ein mehrstufiger Abhärtungsplan als Schritt-Checkliste (§4.2); eine Frostvorhersage (< `SEASON_FROST_TEMP_C`) pausiert die aktuelle Stufe.
- [ ] **AC-25 (Spätfrost-Schutz):** Der Übergang `pre_spring → growing` unterbleibt, solange `on_date < estimated_last_frost_md` **oder** eine Frostvorhersage innerhalb 7 Tagen vorliegt; der Rückhol-Assistent warnt mit konkretem Frostdatum vor dem endgültigen Ausräumen.

**Vertiefung Arten & Sonderfälle (§3.9):**

- [ ] **AC-26 (Sonderfälle):** Immergrüne Arten erhalten in-situ (Pfad A) einen `minimal`-Gieß-Kontrollhinweis (Frosttrocknis); bei grenzwertigen Arten wird der Pfad via `trigger_reason_i18n_key` begründet. Der Kübel-vs.-Beet-Pfadunterschied ist dokumentiert; die automatische Kübel→B-Verschärfung und das `greenhouse_heated`-Signal sind als **noch nicht implementiert** markiert.

**Vertiefung Automatik-Robustheit (§3.10):**

- [ ] **AC-27 (Hochstufung/Degradation):** Wird mitten in der Saison eine Wetterquelle verfügbar, übernimmt der nächste Lauf die Live-Stufe (`trigger_tier='live'`), **ohne** einen erreichten Zustand zurückzudrehen; ein Live-Datenausfall degradiert auf Stufe 2/3 ohne Zustandssprung.
- [ ] **AC-28 (Mehrjahres-Hysterese):** `season_year` wird beim Übergang `pre_spring → growing` freigegeben und für jede Folgesaison sauber neu vergeben; ein Standort bleibt über den Jahreswechsel nicht in `pre_spring` hängen, wenn der Frühling ausbleibt oder der nächste Herbst beginnt.
- [ ] **AC-29 (Monokarpisch / zweijährig):** Für eine Pflanze, deren Lebenszyklus die Blüh-/Seneszenzphase eines monokarpischen bzw. zweijährigen Zyklus bereits durchlaufen hat (REQ-003), materialisiert der nächste `pre_winter`-Übergang **kein** neues Überwinterungsprofil.
