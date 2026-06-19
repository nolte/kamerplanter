# Spezifikation: REQ-039 - Klimazonen- & Winterhärte-Geodaten

```yaml
ID: REQ-039
Titel: Klimazonen- & Winterhärte-Geodaten (Hardiness Zones)
Kategorie: Standorte & Pflege
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB (Geo-Index), Celery, React, TypeScript, MUI
Status: Entwurf
Version: 1.1
Abhängigkeit: REQ-001 (Stammdaten), REQ-002 (Standort), REQ-022 (Überwinterung/Winterhärte-Ampel), REQ-005 (Frostwarnung), REQ-015-A (Aussaatkalender)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-19 | Initialer Entwurf — Integration von frostline (awesome-agriculture) + DACH-Adaption |
| 1.1 | 2026-06-20 | Lizenz-Schärfung: USDA/PHZM-Daten proprietär/US-only (nicht eingecheckt), DWD (GeoNutzV) + Open-Meteo (CC-BY-4.0) als kanonische DACH-Datenbasis |

## 1. Business Case

### User Stories

**User Story (Automatische Zonen-Ableitung):** "Als Gartenbesitzerin in Köln möchte ich, dass das System aus meinen GPS-Koordinaten (oder meiner Postleitzahl) automatisch meine Winterhärtezone bestimmt — damit ich nicht selbst nachschlagen muss, ob ich in Zone 8a oder 8b liege."

**User Story (Standort-Pflanze-Abgleich):** "Als Hobbygärtner möchte ich beim Anlegen einer mehrjährigen Pflanze sofort gewarnt werden, wenn diese Art an meinem Standort nicht winterhart ist — z.B. 'Dieser Feigenbaum ist für Zone 8 angegeben, dein Standort ist Zone 7a → ohne Winterschutz erfriert er.'"

**User Story (Ampel-Automatisierung):** "Als Gärtnerin möchte ich, dass die Winterhärte-Ampel (REQ-022) nicht mehr von einem manuell gepflegten `climate_zone`-String abhängt, sondern aus meinem realen Standort abgeleitet wird — abgestimmt auf MEINE Klimazone, ohne Konfigurationsaufwand."

**User Story (Frost-Basisdaten):** "Als Nutzer ohne Wetter-API möchte ich trotzdem brauchbare Frosttermine (durchschnittlicher letzter/erster Frost) für meinen Aussaatkalender bekommen — abgeleitet aus den Klimanormalen meiner Zone, als Default-Befüllung der Frosttermin-Felder."

**User Story (KA-Admin — Zonen-Referenzdaten):** "Als Plattform-Administrator möchte ich das USDA-Zonenschema als kuratierte Referenz-Collection pflegen — Temperaturklassen, deutsche Beschreibungen und repräsentative Pflanzen pro Zone — damit alle Tenants eine konsistente Zonen-Grundlage teilen."

### Beschreibung

Winterhärtezonen (engl. *plant hardiness zones*) klassifizieren Standorte nach ihrem **mittleren jährlichen Tiefsttemperatur-Minimum** (gemittelt über ~30 Jahre). Das USDA-Schema teilt diesen Wertebereich in Zonen 1–13, jeweils nochmals in Halbzonen `a`/`b` (z.B. `7a`, `8b`) mit einer Spreizung von je ~2,8 °C (5 °F).

Kamerplanter referenziert dieses Schema bereits an mehreren Stellen, aber **bisher nur als manuell gepflegten String**:

- `Species.hardiness_zones: list[str]` und `Species.frost_sensitivity` (REQ-001)
- `Site.climate_zone: str` (REQ-002, Validierung `^\d{1,2}[a-b]$`) und `Site.gps_coordinates` (Geo-Index vorhanden)
- `OverwinteringProfile.hardiness_zone_min` + Winterhärte-Ampel (REQ-022 §"Winterhärte-Ampel")
- Frosttermin-Felder `last_frost_date_avg` / `first_frost_date_avg` / `eisheilige_date` (REQ-015-A §4)

REQ-039 schließt die Lücke zwischen rohem Standort (GPS/PLZ) und diesen bereits konsumierten Zonen-Werten: Es liefert eine **kanonische Zonen-Referenz** (`HardinessZone`), eine **Ableitungs-Engine** (`HardinessZoneResolver`) die `Site.climate_zone` aus Geodaten bestimmt, sowie den **Abgleich** zwischen Species-Winterhärte und Standort-Zone, der die Winterhärte-Ampel (REQ-022) automatisiert und Frost-Basisdaten (REQ-005, REQ-015-A) liefert.

Inspiration und Vorlage ist das Open-Source-Projekt **frostline** aus der awesome-agriculture-Liste.

### Projekt-Steckbrief: frostline

| Eigenschaft | Wert |
|-------------|------|
| **Name** | frostline |
| **Repo-URL** | https://github.com/waldoj/frostline |
| **Lizenz (Code)** | MIT (permissiv, kompatibel) — gilt **nur für den frostline-Code** (Parser-Skripte, Tooling) |
| **Lizenz (Daten)** | **Proprietär (PRISM/OSU-Terms), nicht frei nachnutzbar** — die ausgelieferten USDA/PHZM-Zonendaten stehen NICHT unter MIT (Details s. §"Kritischer Caveat" + §5 Lizenz-Compliance) |
| **Sprache** | Python (Parser); HTML/JS für Kartenvisualisierung |
| **Typ** | Dataset **+** Parser **+** statische API (`{ZIP}.json`, gehostet als phzmapi.org) |
| **Datenquelle** | PRISM Climate Group / Oregon State University (OSU), Bulk-PHZ-Daten + ZIP-Geo-Daten — **US-only**, proprietäre PRISM/OSU-Nutzungsbedingungen |
| **Eingabe** | US-ZIP-Code (5-stellig) |
| **Ausgabe** | JSON pro ZIP: USDA-Zone + repräsentative Temperatur |
| **Reifegrad** | Etabliert, aber **nicht mehr aktiv gepflegt** (~57 Commits, letzte Aktivität älter, 164 Stars). Stabile Datenstruktur, geringes Update-Risiko, aber kein Upstream-Support. |

### Kritischer Caveat: US-zentriert vs. DACH/EU

**frostline liefert ausschließlich US-Daten.** Die Zuordnung erfolgt über **US-ZIP-Codes** auf Basis von **PRISM**-Klimadaten, die nur die USA abdecken. Für den DACH-Zielmarkt von Kamerplanter ist der frostline-**Datensatz daher nicht direkt nutzbar.**

Zu trennen sind zwei Dinge:

1. **Das USDA-Zonen-*Schema*** (Zonen 1–13 nach mittlerem Jahresminimum, Halbzonen `a`/`b`) ist ein **rein temperaturbasiertes Klassifikationssystem** und global anwendbar. Es ist bereits das in Kamerplanter etablierte Schema (`^\d{1,2}[a-b]$`). Dieses Schema übernehmen wir als kanonisches Datenmodell.
2. **Die frostline-*Daten* und der *ZIP→Zone*-Lookup** sind US-spezifisch **und proprietär lizenziert**. Die zugrunde liegenden USDA/PHZM-Zonendaten stammen von der **PRISM Climate Group / Oregon State University** (ausgeliefert über phzmapi.org) und stehen **nicht** unter der MIT-Lizenz des frostline-Codes, sondern unter **proprietären PRISM/OSU-Terms**: Redistribution ist nur mit USDA-ARS- **und** OSU-Logo gestattet; bei Veränderung der Daten sind ein Disclaimer beizufügen und die Logos zu entfernen; das Eigentum an den Daten bleibt bei OSU. **→ Diese Daten werden NICHT in das (MIT-lizenzierte) Kamerplanter-Repo eingecheckt.** Nutzbar ist allein der **frostline-Code (MIT)** als Schema-/Parser-Vorlage für unseren eigenen Lookup-Mechanismus — die **Daten** sind nicht frei nachnutzbar.

**Europäische/DACH-Situation (recherchiert):** **Eine fertige, frei lizenzierte DACH-Winterhärtezonen-Karte mit klarer Lizenz existiert nicht.** Es gibt keine offizielle behördliche USDA-Äquivalent-Karte für die EU mit frei nachnutzbarem PLZ-Lookup-Datensatz auf dem Reifegrad von frostline. Verbreitete abgeleitete Karten (z.B. plantmaps.com, Gardenia.net) mappen Europa zwar auf das USDA-Schema, sind aber lizenzrechtlich nicht sauber nachnutzbar. Für Deutschland gilt grob: weite Teile in **Zone 7b–8b**, Polen-naher Osten und höhere Lagen Bayerns kühler (bis 6b/7a), milde Regionen (Niederrhein, Weinbauklima) bis 8b. Diese Streuung macht klar: Ein fester Landeswert genügt nicht — die Zone muss **standortgenau aus Klimanormalen** abgeleitet werden.

**DACH-Ableitungsweg (konkret, lizenzsauber):** Statt eines proprietären ZIP→Zone-Lookups leitet Kamerplanter die Zone **selbst** aus offenen, klar lizenzierten Klimadaten ab. Die `HardinessZoneResolver`-Engine berechnet die Zone aus dem **mittleren jährlichen Tiefstwert** am Standort. Kanonische, lizenzsaubere Datenbasis sind:

- **DWD Open Data** (Deutscher Wetterdienst) — offizielle DACH-Klimanormale 1991–2020, **kostenfrei auch zur kommerziellen Nutzung** unter der **GeoNutzV**. Pflicht-Quellenvermerk: „Datenbasis: Deutscher Wetterdienst".
- **Open-Meteo Historical Weather API** — historische Tagesreihen, kostenlos, kein API-Key, weltweit, bereits als Wetter-Adapter in REQ-005 vorgesehen. Daten unter **CC-BY-4.0**, Pflicht-Attribution: „Weather data by Open-Meteo.com".

Algorithmus: pro Jahr der Normalperiode das absolute Tagesminimum bestimmen, über die Jahre mitteln (`mean_annual_minimum_c`), und über die `HardinessZone`-Schwellen in eine Zone klassifizieren. Das in Kamerplanter eingecheckte Material beschränkt sich auf das (lizenzfreie) USDA-Zonen-*Schema* und selbst abgeleitete Werte — nicht auf fremde Zonendatensätze. Für US-Standorte kann optional weiterhin der frostline-/phzmapi-Lookup als reiner Laufzeit-Schnellpfad genutzt werden (gleiche Zielwerte, kein eigener Klimanormal-Lauf nötig; ohne Einchecken der proprietären Daten — s. §3 `FrostlineUsAdapter`).

## 2. Datenmodell-Erweiterung (ArangoDB)

### Neue Document Collection: `HardinessZone`

Kanonische, global gepflegte Referenz der USDA-Zonen 1–13 (inkl. Halbzonen). Nicht tenant-gescoped (rein taxonomische Referenzdaten, analog `BotanicalFamily` in REQ-001).

- **`:HardinessZone`** — USDA-Winterhärtezone (Referenz)
  - Collection: `hardiness_zones`
  - Properties:
    - `zone: str` (Primärschlüssel-Wert, z.B. `"7a"` — entspricht `Site.climate_zone`-Format `^\d{1,2}[a-b]$`)
    - `zone_number: int` (1–13, Hauptzone ohne Halbzone)
    - `subzone: Literal['a', 'b']`
    - `temp_min_c: float` (Untergrenze des mittleren Jahresminimums in °C, z.B. `-17.8` für 7a)
    - `temp_max_c: float` (Obergrenze, z.B. `-15.0` für 7a)
    - `temp_min_f: float`, `temp_max_f: float` (US-Referenzwerte, da Schema in °F definiert ist)
    - `description_de: str` (z.B. "Mittleres Jahresminimum −17,8 °C bis −15,0 °C")
    - `representative_regions_de: list[str]` (z.B. `["Bayerischer Wald", "Erzgebirge"]` — illustrativ, nicht autoritativ)
    - `typical_last_frost_md: Optional[str]` (Richtwert letzter Frost als `MM-DD`, z.B. `"05-15"` — speist REQ-015-A-Default)
    - `typical_first_frost_md: Optional[str]` (Richtwert erster Frost als `MM-DD`, z.B. `"10-05"`)
  - Indizes:
    - PERSISTENT INDEX on `[zone]` UNIQUE
    - PERSISTENT INDEX on `[zone_number, subzone]`
  - Composite Key: `zone` (deterministisch, z.B. `_key = "7a"`)

### Erweiterung: `Site` (REQ-002)

Additive, non-breaking Felder. Das bestehende `Site.climate_zone: str` bleibt als **abgeleiteter/überschreibbarer** Wert erhalten.

- `hardiness_zone: Optional[str]` — kanonischer Zonen-Wert, der `climate_zone` ablöst/spiegelt (Format `^\d{1,2}[a-b]$`). Referenziert `hardiness_zones._key`.
  > **Migration:** Bestehendes `Site.climate_zone` wird als Initialwert in `hardiness_zone` übernommen. `climate_zone` bleibt als Alias lesbar, neue Logik liest `hardiness_zone`. Ein Field-Validator hält beide synchron.
- `hardiness_zone_source: Literal['manual', 'derived_gps', 'derived_postal', 'frostline_us']` (Default: `'manual'`) — Provenienz der Zone (DSGVO-/Transparenz-Anforderung: nachvollziehbar, woher der Wert stammt).
- `hardiness_zone_resolved_at: Optional[datetime]` — Zeitpunkt der letzten automatischen Ableitung.
- `mean_annual_minimum_c: Optional[float]` — der berechnete Klimanormal-Wert, aus dem die Zone klassifiziert wurde (Audit/Erklärbarkeit; treibt die Ampel-Differenzberechnung präziser als nur die Zonen-Stufe).
- `postal_code: Optional[str]` — optionale PLZ als alternative Ableitungs-Eingabe, wenn keine GPS-Koordinaten vorliegen.

### Neue Edge Collection: `located_in_zone`

- **`located_in_zone`**: `Site → HardinessZone`
  - Richtung: `(Site)-[:located_in_zone]->(HardinessZone)`
  - Properties:
    - `resolved_at: datetime`
    - `source: Literal['manual', 'derived_gps', 'derived_postal', 'frostline_us']`
  - Indizes: PERSISTENT INDEX on `[_from]`
  - Zweck: schnelle Graph-Traversierung „alle Sites einer Zone" und „Zone einer Site" ohne String-Join.

### Mapping `Species` ↔ Zone

Es wird **kein** neues Species-Feld eingeführt — REQ-001 liefert bereits `Species.hardiness_zones: list[str]` und `Species.frost_sensitivity`. REQ-039 definiert die **Vergleichssemantik**:

- `species.hardiness_zones` enthält die Zonen, in denen die Art **ohne Schutz winterhart** ist. Die **niedrigste** dieser Zonen ist die maßgebliche Untergrenze (`species_min_zone`).
- Die Engine vergleicht `zone_number(species_min_zone)` gegen `zone_number(site.hardiness_zone)` (siehe §3).

## 3. Technische Umsetzung (Python)

5-Layer-Architektur (API → Service → Engine → Repository → ArangoDB).

### Engine: `HardinessZoneResolver`

Layer: Engine (`app/business_logic/engines/hardiness_zone_resolver.py`). Reine Berechnungslogik, kein DB-Zugriff (Repository wird injiziert).

```python
class ZoneResolution(BaseModel):
    zone: str                       # z.B. "7b"
    mean_annual_minimum_c: float
    source: Literal["derived_gps", "derived_postal", "frostline_us"]


class HardinessZoneResolver:
    """Leitet die USDA-Winterhärtezone aus Standortdaten ab."""

    def classify_from_minimum(
        self, mean_annual_minimum_c: float, zones: list[HardinessZone]
    ) -> str:
        """Klassifiziert einen mittleren Jahres-Tiefstwert in eine Zone.

        Vergleicht gegen die [temp_min_c, temp_max_c]-Intervalle der
        Referenz-Collection. Werte unterhalb Zone 1 → "1a", oberhalb 13 → "13b".
        """
        for z in sorted(zones, key=lambda z: z.temp_min_c):
            if z.temp_min_c <= mean_annual_minimum_c < z.temp_max_c:
                return z.zone
        ...  # Rand-Clamping

    def derive_from_climate_normals(
        self, daily_minima_by_year: dict[int, float], zones: list[HardinessZone]
    ) -> ZoneResolution:
        """DACH-Pfad: mittelt die jährlichen Tagesminima zu einem
        Klimanormal und klassifiziert (Quelle: Open-Meteo Historical / DWD)."""
        mean_min = mean(daily_minima_by_year.values())
        return ZoneResolution(
            zone=self.classify_from_minimum(mean_min, zones),
            mean_annual_minimum_c=mean_min,
            source="derived_gps",
        )
```

**Winterhärte-Abgleich (treibt REQ-022-Ampel):**

```python
def evaluate_winter_hardiness(
    species_min_zone: str | None,
    site_zone: str,
    frost_sensitivity: Literal["hardy", "half_hardy", "tender"] | None,
) -> Literal["green", "yellow", "red"]:
    """Vereinheitlicht die Winterhärte-Ampel (REQ-022).

    Konsistent mit REQ-022 §"Winterhärte-Ampel":
    - green  (winterhart): hardy UND species_zone <= site_zone
    - yellow (Schutz nötig): half_hardy ODER Zonendifferenz <= 1
    - red    (muss rein): tender ODER Zonendifferenz > 1
    """
    delta = _zone_delta(species_min_zone, site_zone)  # site - species
    if frost_sensitivity == "tender" or (delta is not None and delta < -1):
        return "red"
    if frost_sensitivity == "half_hardy" or (delta is not None and delta <= 0):
        return "yellow"
    return "green"
```

> Diese Funktion ersetzt die in REQ-022 inline beschriebene String-Vergleichslogik durch einen Zonen-numerischen Vergleich. REQ-022 `CareReminderEngine` ruft sie auf; die `hardy`-Kurzschluss-Regel (keine Winterschutz-Erinnerungen) bleibt unverändert.

### Adapter: `FrostlineUsAdapter` (optional, US-Standorte)

Folgt dem etablierten External-Adapter-Pattern (ABC in `domain/interfaces/`, Implementierung in `data_access/external/`, Registrierung via `AdapterRegistry` — analog REQ-011).

- Interface `HardinessZoneSourceAdapter`: `async def resolve(self, *, postal_code: str | None, gps: tuple[float, float] | None) -> ZoneResolution | None`.
- `FrostlineUsAdapter` (**rein optionaler US-Pfad**): ruft zur Laufzeit `https://phzmapi.org/{zip}.json` (statische frostline-API). **Nur für US-ZIP-Codes sinnvoll**, gibt `None` für Nicht-US-Eingaben zurück (sauberer Fallback auf den Klimanormal-Pfad). Wichtig: Dieser Adapter ist ein optionaler Komfortpfad für US-Nutzer und **nicht** Teil des DACH-Default-Flows. Die zugrunde liegenden PRISM/OSU-Zonendaten sind proprietär (s. §"Kritischer Caveat" + §5) und werden **nicht eingecheckt/vendored**. Wird dieser Pfad für US-Nutzer aktiviert, müssen die PRISM/OSU-Auflagen erfüllt werden (USDA-ARS- + OSU-Logo bzw. bei Veränderung Disclaimer + Logo-Entfernung); andernfalls bleibt er deaktiviert.
- `OpenMeteoClimateNormalAdapter` (Default DACH/global): holt historische Tagesminima (z.B. Normalperiode 1991–2020) für die GPS-Koordinaten und übergibt sie an `derive_from_climate_normals`. Datenlizenz CC-BY-4.0 (Attribution „Weather data by Open-Meteo.com"); alternativ DWD Open Data unter GeoNutzV (Quellenvermerk „Datenbasis: Deutscher Wetterdienst").

### Service: `HardinessZoneService`

Layer: Service (`app/services/hardiness_zone_service.py`). Orchestriert Adapter-Auswahl, persistiert Ergebnis, hält `Site.climate_zone`/`hardiness_zone` synchron und pflegt die `located_in_zone`-Kante (idempotent via UPSERT).

```python
async def resolve_for_site(self, site_key: str, *, force: bool = False) -> ZoneResolution:
    site = await self.site_repo.get(site_key)
    # 1. US-Schnellpfad falls postal_code US-Format
    # 2. sonst Klimanormal-Pfad (Open-Meteo / DWD) aus gps_coordinates
    # 3. Zone klassifizieren gegen hardiness_zones-Collection
    # 4. Site updaten (hardiness_zone, source, resolved_at, mean_annual_minimum_c)
    #    + located_in_zone-Kante UPSERTen
    ...
```

### Celery-Tasks

- `refresh_site_hardiness_zones` (Beat: vierteljährlich): leitet Zonen für Sites mit GPS, aber ohne manuelle Override (`hardiness_zone_source != 'manual'`) neu ab. Klimanormale ändern sich langsam — hohe Frequenz unnötig.
- `seed_hardiness_zones` (einmalig/Migration): befüllt die `hardiness_zones`-Collection aus den Seed-Daten (siehe §5).

### API-Endpunkte

Global (Referenzdaten) und tenant-gescoped (Site-bezogen, gemäß REQ-024-Routing `/api/v1/t/{tenant_slug}/...`):

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/api/v1/hardiness-zones` | Liste aller USDA-Zonen (Referenz, global) |
| GET | `/api/v1/hardiness-zones/{zone}` | Einzelne Zone mit Temperaturklassen + Frost-Richtwerten |
| POST | `/api/v1/t/{tenant_slug}/sites/{site_key}/resolve-hardiness-zone` | Zone aus GPS/PLZ ableiten + persistieren |
| GET | `/api/v1/t/{tenant_slug}/sites/{site_key}/hardiness` | Aufgelöste Zone + Quelle + `mean_annual_minimum_c` |
| GET | `/api/v1/t/{tenant_slug}/plants/{plant_key}/hardiness-check` | Ampel-Status (green/yellow/red) für Pflanze am Standort |

## 4. Frontend-Integration

React 19 + TypeScript 5.9 + MUI 7, i18n DE/EN. Custom Hooks geben Objekte/Arrays `useMemo`-stabilisiert zurück (Projekt-Konvention).

- **Site-Formular (REQ-002):** Neben dem bestehenden `climate_zone`-Feld ein Button „Zone automatisch ermitteln" (aktiv, sobald GPS-Koordinaten oder PLZ gesetzt sind). Ergebnis zeigt Zone + abgeleiteten Tiefstwert + Quelle. Manueller Override bleibt jederzeit möglich (setzt `source='manual'`).
- **`HardinessZoneBadge`-Komponente:** Chip mit Zone + Tooltip (Temperaturklasse aus `description_de`). Wiederverwendbar in Site-Detail und Pflanzen-Karten.
- **Winterhärte-Ampel (REQ-022):** Die bestehende Ampel-Darstellung konsumiert nun den `hardiness-check`-Endpunkt statt lokaler String-Logik. Roter/gelber Status zeigt die konkrete Zonendifferenz als Begründung („Standort 7a, Art braucht mind. 8a → 1 Zone zu kalt").
- **Pflanzen-Anlage-Dialog:** Inline-Warnung beim Auswählen einer Art, deren `species_min_zone` über der Standort-Zone liegt — verlinkt auf das OverwinteringProfile (REQ-022).
- **i18n:** Page-Keys unter `pages.hardiness.*`, Enum-Werte (`hardiness_zone_source`, Ampel) unter `enums.hardinessZoneSource.*` bzw. `enums.hardinessTrafficLight.*`. Beide Sprachen DE (Default) + EN.

## 5. Konfiguration, Deployment & Lizenz

### Seed-Daten

`hardiness_zones`-Collection wird mit den USDA-Zonen **1a–13b** geseedet (26 Einträge). Temperaturschwellen folgen der offiziellen USDA-Definition (in °F definiert, °C abgeleitet). Auszug:

| zone | zone_number | subzone | temp_min_c | temp_max_c | temp_min_f | temp_max_f |
|------|-------------|---------|-----------|-----------|-----------|-----------|
| 6a | 6 | a | -23.3 | -20.6 | -10 | -5 |
| 6b | 6 | b | -20.6 | -17.8 | -5 | 0 |
| 7a | 7 | a | -17.8 | -15.0 | 0 | 5 |
| 7b | 7 | b | -15.0 | -12.2 | 5 | 10 |
| 8a | 8 | a | -12.2 | -9.4 | 10 | 15 |
| 8b | 8 | b | -9.4 | -6.7 | 15 | 20 |

DACH-relevante Zonen (6a–8b) erhalten gepflegte `representative_regions_de` und Frost-Richtwerte (`typical_last_frost_md` / `typical_first_frost_md`), die als Defaults in die REQ-015-A-Frosttermine fließen, solange der Nutzer keine eigenen Werte und keine Wetter-API hat.

### Konfiguration (Umgebungsvariablen)

| Variable | Default | Zweck |
|----------|---------|-------|
| `HARDINESS_NORMAL_PERIOD_START` | `1991` | Startjahr der Klimanormalperiode |
| `HARDINESS_NORMAL_PERIOD_END` | `2020` | Endjahr |
| `HARDINESS_SOURCE_PRIORITY` | `frostline_us,open_meteo` | Adapter-Reihenfolge (US-Schnellpfad zuerst, sonst Klimanormale) |
| `FROSTLINE_API_BASE_URL` | `https://phzmapi.org` | Override für gespiegelten frostline-Datensatz |

### Deployment

Kein neuer Service. Open-Meteo Historical ist API-Key-frei; DWD Open Data ebenfalls. Der frostline-**Datensatz** wird **nicht** ins MIT-Repo vendored — die ausgelieferten USDA/PHZM-Zonendaten sind proprietär (PRISM/OSU-Terms, s. §"Lizenz-Compliance"), nicht von der MIT-Lizenz des frostline-Codes gedeckt. Der optionale US-Schnellpfad (`FrostlineUsAdapter`) nutzt daher die phzmapi.org-API zur Laufzeit (ohne eingecheckte Daten); ein Mirror käme nur unter Erfüllung der PRISM/OSU-Auflagen und außerhalb des MIT-Repos in Frage.

### Lizenz-Compliance

Strikt zu trennen sind **frostline-Code** und **frostline-/PHZM-Daten**:

- **frostline-Code** steht unter **MIT** und darf als **Schema-/Parser-Vorlage** übernommen werden. Bei Übernahme von Parser-Code-Mustern ist der MIT-Copyright-Hinweis im `THIRD_PARTY_LICENSES`/NOTICE zu führen.
- **frostline-/PHZM-Zonendaten** (PRISM Climate Group / Oregon State University, ausgeliefert über phzmapi.org) sind **proprietär und US-only**. Sie stehen **nicht** unter MIT: Redistribution nur mit USDA-ARS- **und** OSU-Logo; bei Veränderung der Daten Disclaimer beifügen und Logos entfernen; Eigentum bleibt OSU. **→ Diese Daten werden NICHT in das MIT-lizenzierte Kamerplanter-Repo eingecheckt/vendored.** Sie sind nur über den optionalen, zur Laufzeit gegen phzmapi.org laufenden `FrostlineUsAdapter` für US-Nutzer relevant (s. §3) — und auch dann nur unter Erfüllung der PRISM/OSU-Auflagen. Für DACH spielen sie keine Rolle.

Das **USDA-Zonenschema selbst** (Temperaturklassen, Halbzonen) ist ein öffentliches Klassifikationssystem ohne Lizenzbeschränkung und ist das einzige aus diesem Umfeld eingecheckte Material.

**Kanonische, lizenzsaubere DACH-Datenbasis** für die selbst abgeleiteten Zonen (`HardinessZoneResolver`):

- **DWD Open Data** — **GeoNutzV**, kostenfrei auch zur kommerziellen Nutzung; Pflicht-Quellenvermerk „Datenbasis: Deutscher Wetterdienst".
- **Open-Meteo** — Daten unter **CC-BY-4.0**; Pflicht-Attribution „Weather data by Open-Meteo.com".

Daraus leitet Kamerplanter die Zonen selbst ab; eine fertige freie DACH-Winterhärtezonen-Karte mit klarer Lizenz existiert nicht. Die zu führenden Attributionen/Quellenvermerke (DWD, Open-Meteo) gehören in `THIRD_PARTY_LICENSES`/NOTICE.

> Vollständige Bewertung der Lizenz- und Nutzungslage siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

## 6. Abhängigkeiten

| REQ/NFR | Beziehung |
|---------|-----------|
| **REQ-001** | Liefert `Species.hardiness_zones` + `frost_sensitivity` (Vergleichsbasis). Kein neues Feld nötig. |
| **REQ-002** | `Site` wird um `hardiness_zone`-Felder erweitert; nutzt vorhandene `gps_coordinates` + Geo-Index. `climate_zone` bleibt rückwärtskompatibel. |
| **REQ-022** | Winterhärte-Ampel + Überwinterungs-Erinnerungen konsumieren `evaluate_winter_hardiness` und die abgeleitete Zone. REQ-039 ersetzt die inline-String-Vergleichslogik. |
| **REQ-005** | Stellt die Wetter-/Klima-Adapter (DWD, Open-Meteo) bereit, deren Historie die Klimanormale liefert. Frost-Richtwerte ergänzen die Frostwarnung als Fallback ohne Live-Wetter. |
| **REQ-015-A** | `typical_last_frost_md` / `typical_first_frost_md` der Zone befüllen die Frosttermin-Defaults (`last_frost_date_avg` etc.), wenn nicht manuell gesetzt. |
| **REQ-011** | Adapter-/Registry-Pattern wird wiederverwendet. |
| **REQ-024** | Site-bezogene Endpunkte sind tenant-gescoped; `hardiness_zones` bleibt globale Referenz. |
| **REQ-025 / NFR-011** | `hardiness_zone_source` macht Geodaten-Verarbeitung transparent; GPS bleibt optional (PLZ-Fallback), keine zusätzliche personenbezogene Speicherung über REQ-002 hinaus. |

## 7. Akzeptanzkriterien

- [ ] Collection `hardiness_zones` ist mit allen USDA-Zonen 1a–13b geseedet; DACH-Zonen (6a–8b) haben `description_de` und Frost-Richtwerte.
- [ ] `GET /api/v1/hardiness-zones` und `/{zone}` liefern die Referenzdaten.
- [ ] `HardinessZoneResolver.classify_from_minimum` ordnet einen mittleren Jahres-Tiefstwert korrekt einer Zone zu (inkl. Rand-Clamping <1a / >13b).
- [ ] `POST .../sites/{site_key}/resolve-hardiness-zone` leitet für einen DACH-Standort mit GPS die Zone aus Open-Meteo-Klimanormalen ab, persistiert `hardiness_zone`, `mean_annual_minimum_c`, `source='derived_gps'` und legt die `located_in_zone`-Kante an.
- [ ] Für einen US-ZIP-Standort wird (bei aktiviertem `FrostlineUsAdapter`) `source='frostline_us'` gesetzt; für Nicht-US-Eingaben fällt der Resolver sauber auf den Klimanormal-Pfad zurück.
- [ ] Ein manuell gesetztes `hardiness_zone` (`source='manual'`) wird vom periodischen `refresh_site_hardiness_zones`-Task **nicht** überschrieben.
- [ ] `evaluate_winter_hardiness` liefert für (Art mind. Zone 8a, Standort 7a, `tender`) `red`; für (`hardy`, Standort-Zone ≥ Art-Zone) `green`; für Differenz ≤ 1 Zone `yellow` — konsistent mit REQ-022.
- [ ] Die Winterhärte-Ampel in REQ-022 nutzt den `hardiness-check`-Endpunkt; für `hardy`-Arten werden weiterhin **keine** Winterschutz-Erinnerungen generiert.
- [ ] `GET .../plants/{plant_key}/hardiness-check` gibt Ampel-Status plus erklärende Zonendifferenz zurück.
- [ ] Die Frosttermin-Defaults (REQ-015-A) werden aus den Zonen-Richtwerten vorbefüllt, solange weder manuelle Werte noch Wetter-API-Daten vorliegen.
- [ ] `Site.climate_zone` (Alt) und `Site.hardiness_zone` (Neu) bleiben nach Migration synchron; bestehende Sites ohne GPS funktionieren unverändert (manuelle Zone).
- [ ] Frontend: „Zone automatisch ermitteln" im Site-Formular, `HardinessZoneBadge` mit Tooltip, Inline-Warnung bei nicht-winterharter Art; alle Texte DE + EN.
- [ ] MIT-Lizenzhinweis für frostline-**Code** ist in `THIRD_PARTY_LICENSES`/NOTICE geführt, falls Parser-Muster übernommen werden; die proprietären frostline-/PHZM-Zonendaten (PRISM/OSU, US-only) werden **nicht** ins Repo eingecheckt/vendored. DWD- (GeoNutzV) und Open-Meteo- (CC-BY-4.0) Attributionen sind geführt, wenn deren Daten zur Zonenableitung genutzt werden.
- [ ] Backend-Tests (pytest) für Resolver-Klassifikation, Ampel-Logik und Adapter-Fallback; Frontend-Tests (vitest) für Badge + Ampel-Status; ruff/ESLint/TypeScript clean.
