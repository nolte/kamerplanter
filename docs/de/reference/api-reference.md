# API-Referenz

!!! note "Automatisch generiert"
    Diese Seite wird automatisch aus Google-Style Docstrings des Backend-Codes via `mkdocstrings` generiert. Aktuell ist `mkdocstrings` noch nicht vollständig konfiguriert.

Für interaktive API-Docs mit laufendem Backend:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Print & Export (REQ-032)

Alle Print-Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{slug}/print/` und erfordern ein gültiges JWT-Token. Die Zugriffsrechte entsprechen den Berechtigungen der zugrundeliegenden Daten (REQ-024 RBAC) — wer einen Nährstoffplan lesen darf, darf ihn auch drucken.

**Gemeinsame Query-Parameter (alle Endpunkte):**

| Parameter | Typ | Standard | Werte |
|-----------|-----|---------|-------|
| `locale` | string | `de` | `de`, `en` |
| `format` | string | `pdf` | `pdf`, `csv` (nur bei tabellarischen Templates) |

### Nährstoffplan-PDF

Exportiert einen vollständigen Nährstoffplan als PDF inklusive Phasen-Tabelle, Mischanleitungen, Wasser-Konfiguration und CalMag/Flushing-Hinweisen.

```
GET /api/v1/t/{slug}/print/nutrient-plan/{plan_key}
```

**Pfad-Parameter:**

| Parameter | Beschreibung |
|-----------|-------------|
| `slug` | Mandanten-Slug |
| `plan_key` | ArangoDB-Key des NutrientPlan-Dokuments |

**Response:** `application/pdf` mit `Content-Disposition: attachment; filename="naehrstoffplan-{plan_key}.pdf"`

**Beispiel:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/mein-garten/print/nutrient-plan/nutrient_plans/42?locale=de" \
  -H "Authorization: Bearer <token>" \
  --output naehrstoffplan.pdf
```

---

### Pflege-Checkliste-PDF

Exportiert alle fälligen Pflegeaufgaben für ein bestimmtes Datum als Checkliste mit Checkboxen, gruppiert nach Dringlichkeit (überfällig, heute fällig, demnächst).

```
GET /api/v1/t/{slug}/print/care-checklist
```

**Query-Parameter (zusätzlich zu `locale` und `format`):**

| Parameter | Typ | Standard | Beschreibung |
|-----------|-----|---------|-------------|
| `date` | string (ISO 8601) | Heutiges Datum | Stichtag für fällige Aufgaben, z.B. `2026-04-01` |

**Response:** `application/pdf` mit `Content-Disposition: attachment; filename="pflege-checkliste-{date}.pdf"`

**Beispiel:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/mein-garten/print/care-checklist?date=2026-04-15&locale=de" \
  -H "Authorization: Bearer <token>" \
  --output pflege-checkliste.pdf
```

---

### Pflanzen-Infokarten / Etiketten-PDF

Druckt kompakte Infokarten mit QR-Code für eine oder mehrere Pflanzinstanzen. Der QR-Code enthält die Deep-Link-URL zur jeweiligen Pflanze in der App.

```
GET /api/v1/t/{slug}/print/plant-labels
```

**Query-Parameter (zusätzlich zu `locale`):**

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|-----------|-----|---------|---------|-------------|
| `plant_keys` | string | Ja | — | Komma-separierte ArangoDB-Keys der Pflanzinstanzen (mind. 1) |
| `fields` | string | Nein | `name,scientific_name,planted_date` | Komma-separierte Felder auf der Karte |
| `layout` | string | Nein | `grid_2x4` | `single` (A6), `grid_2x4` (8×A4), `grid_3x3` (9×A4) |
| `qr_size_mm` | integer | Nein | `25` | QR-Code-Seitenlänge in mm (min: 20, max: 60) |

**Mögliche Werte für `fields`:**

`name`, `scientific_name`, `family`, `planted_date`, `current_phase`, `location`, `cultivar`, `note`

Der QR-Code ist immer enthalten und kann nicht über `fields` abgewählt werden.

**Response:** `application/pdf` mit `Content-Disposition: attachment; filename="pflanzen-etiketten.pdf"`

**Beispiel — 8 Karten pro A4-Seite mit Pflanzenname, wissenschaftlichem Namen und Pflanzdatum:**

```bash
curl -X GET \
  "https://api.example.com/api/v1/t/mein-garten/print/plant-labels\
?plant_keys=plant_instances/101,plant_instances/102,plant_instances/103\
&fields=name,scientific_name,planted_date,location\
&layout=grid_2x4\
&qr_size_mm=25\
&locale=de" \
  -H "Authorization: Bearer <token>" \
  --output etiketten.pdf
```

**Fehlercodes:**

| HTTP-Status | Bedeutung |
|-------------|----------|
| `400` | Ungültige Parameter (z.B. `layout`-Wert unbekannt, `qr_size_mm` außerhalb des Bereichs) |
| `401` | Nicht authentifiziert |
| `403` | Keine Berechtigung für diesen Mandanten oder die Ressource |
| `404` | Plan-Key oder Pflanzinstanz-Key nicht gefunden |
| `422` | Pflichtparameter fehlt (z.B. `plant_keys` bei `/plant-labels`) |

---

### Verfügbare Templates auflisten

Gibt eine Liste aller registrierten Print-Templates zurück.

```
GET /api/v1/print/templates
```

Dieser Endpunkt ist nicht mandantenspezifisch und erfordert lediglich eine gültige Authentifizierung.

**Response-Beispiel:**

```json
[
  {
    "type": "nutrient_plan",
    "label_de": "Nährstoffplan",
    "label_en": "Nutrient Plan",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  },
  {
    "type": "care_checklist",
    "label_de": "Pflege-Checkliste",
    "label_en": "Care Checklist",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  },
  {
    "type": "plant_label",
    "label_de": "Pflanzen-Infokarte",
    "label_en": "Plant Info Card",
    "formats": ["pdf"],
    "locales": ["de", "en"]
  }
]
```

---

---

## Browser Push / PWA-Benachrichtigungen

Alle drei Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{tenant_slug}/notifications/pwa/` und erfordern ein gültiges JWT-Token.

### VAPID-Public-Key abrufen

Gibt den VAPID-Public-Key der Instanz zurück. Der Browser benötigt diesen Schlüssel, um eine Push-Subscription zu erstellen.

```
GET /api/v1/t/{tenant_slug}/notifications/pwa/vapid-public-key
```

**Response (200):**

```json
{
  "vapid_public_key": "BNm..."
}
```

Ist kein VAPID-Schlüsselpaar konfiguriert, antwortet der Endpunkt mit `503 Service Unavailable`.

---

### Push-Subscription registrieren

Registriert das aktuelle Gerät für Browser-Push-Benachrichtigungen. Die Subscription-Daten werden vom Browser nach dem Aufruf von `PushManager.subscribe()` bereitgestellt.

```
POST /api/v1/t/{tenant_slug}/notifications/pwa/subscribe
```

**Request-Body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

**Response:** `201 Created` bei Erfolg, `409 Conflict` wenn die Subscription für dieses Gerät bereits registriert ist.

---

### Push-Subscription deregistrieren

Entfernt die Subscription des aktuellen Geräts. Danach werden keine Browser-Push-Benachrichtigungen mehr an dieses Gerät gesendet.

```
POST /api/v1/t/{tenant_slug}/notifications/pwa/unsubscribe
```

**Request-Body:**

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/..."
}
```

**Response:** `204 No Content` bei Erfolg, `404 Not Found` wenn die Subscription nicht gefunden wurde.

---

### Siehe auch

- [Druckansichten & Export — Benutzerhandbuch](../user-guide/print-export.md)
- [Dünge-Logik](../user-guide/fertilization.md)
- [Pflegeerinnerungen](../user-guide/care-reminders.md)
- [Umgebungsvariablen — Browser Push (VAPID)](environment-variables.md#browser-push-pwa-vapid)

---

## Standort-Wettervorhersage & Frost-Frühwarnung <!-- REQ-046 / Issue #392 -->

Beide Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{tenant_slug}/` und erfordern ein gültiges JWT-Token. Es gibt keine gesonderte Rollen-Einschränkung — jedes aktive Mandanten-Mitglied (auch die Rolle **Beobachter**) darf lesen. Beide Endpunkte sind **graceful**: Fehlt eine Wetterquelle, fehlen GPS-Koordinaten am Standort, oder ist die Wettervorhersage-Funktion betreiberseitig deaktiviert (`WEATHER_ENABLED=false`), liefern sie leere/`null`-Vorhersagefelder statt eines Fehlers.

### Wetter-Tagesvorhersage eines Standorts abrufen

Liefert die im Vorhersage-Zeitraum liegenden Tagesvorhersagen eines Standorts (aus der [Wetterquellen-Infrastruktur](../user-guide/weather-sources.md)) plus die zusammengefasste proaktive Frost-Frühwarnung. Speist das Dashboard-Widget „Wettervorhersage".

```
GET /api/v1/t/{tenant_slug}/sites/{site_key}/weather-forecast
```

**Response (200):** `SiteWeatherForecastResponse`

```json
{
  "site_key": "sites/42",
  "forecasts": [
    {
      "forecast_date": "2026-07-07",
      "temp_min_c": -1.5,
      "temp_max_c": 6.0,
      "precipitation_mm": 0.0,
      "wind_speed_kmh": 10.0,
      "humidity_percent": 80.0,
      "weather_code": "clear",
      "source": "open-meteo",
      "data_kind": "forecast"
    }
  ],
  "forecast_frost_warning": true,
  "forecast_min_temperature": -1.5,
  "forecast_expected_date": "2026-07-07",
  "forecast_source": "open-meteo"
}
```

| Feld | Typ | Bedeutung |
|------|-----|----------|
| `forecasts` | Liste | Tagesvorhersagen innerhalb des konfigurierten Vorhersage-Zeitraums (Standard: heute + 1 Tag), je Tag mit Herkunfts-Kennzeichnung (`source`, `data_kind`) |
| `forecast_frost_warning` | boolean \| null | `true`, wenn mindestens ein Tag im Zeitraum eine Minimaltemperatur auf oder unter dem Frost-Vorhersage-Schwellwert erreicht; `null`, wenn keine verwertbare Vorhersage vorliegt |
| `forecast_min_temperature` | number \| null | Minimaltemperatur des frühesten erwarteten Frosttages |
| `forecast_expected_date` | string \| null | Datum des frühesten erwarteten Frosttages |
| `forecast_source` | string \| null | Wetterquelle, aus der dieser Frosttag stammt |

### Zusätzliche Felder in der Frost-Warnung eines Standorts (`Location`)

Die bestehende reaktive Frost-Warnung liefert seit dieser Erweiterung zusätzlich die proaktive Vorhersage für die Site, zu der dieser Standort gehört. Das reaktive Feld `frost_warning` bleibt unverändert, damit der Home-Assistant-Koordinator kompatibel bleibt.

```
GET /api/v1/t/{tenant_slug}/locations/{key}/frost-warning
```

**Response (200):** `FrostWarningResponse` — zusätzlich zu den bestehenden Feldern (`location_key`, `frost_warning`, `temperature_celsius`, `threshold_celsius`, `source`, `entity_id`):

| Feld | Typ | Bedeutung |
|------|-----|----------|
| `forecast_frost_warning` | boolean \| null | Proaktive Vorhersage für die zugehörige Site (additiv, siehe oben) |
| `forecast_min_temperature` | number \| null | Voraussichtliche Minimaltemperatur des frühesten Frosttages |
| `forecast_expected_date` | string \| null | Datum des frühesten erwarteten Frosttages |
| `forecast_source` | string \| null | Herkunft der zugrundeliegenden Vorhersage |

### Siehe auch

- [Dashboard: Wettervorhersage und Frost-Frühwarnung — Benutzerhandbuch](../user-guide/dashboard.md#wettervorhersage-und-frost-fruehwarnung)
- [Benachrichtigungen: Frost-Frühwarnung — Benutzerhandbuch](../user-guide/notifications.md#frost-fruehwarnung)
- [Wetterquellen je Standort — Benutzerhandbuch](../user-guide/weather-sources.md)
- [Umgebungsvariablen — Wettervorhersage & Frost-Frühwarnung](environment-variables.md#wettervorhersage-frost-fruehwarnung)

---

## Pflanzinstanzen: Entfernen mit Abschlussart & Überlebens-Statistik

Alle Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{tenant_slug}/plant-instances/` und erfordern ein gültiges JWT-Token. <!-- REQ-003 E5/G1 -->

### Pflanze entfernen (mit optionaler Abschlussklassifizierung)

Entfernt eine Pflanzinstanz. Der Request-Body ist optional und abwärtskompatibel: ein leerer Body (bzw. gar kein Body) entspricht dem bisherigen einfachen Entfernen ohne Klassifizierung.

```
POST /api/v1/t/{tenant_slug}/plant-instances/{key}/remove
```

**Request-Body (optional):**

```json
{
  "termination_type": "died",
  "termination_cause": "pest"
}
```

| Feld | Typ | Pflicht | Werte |
|------|-----|---------|-------|
| `termination_type` | string \| null | Nein | `harvested`, `senesced`, `died`, `cancelled` |
| `termination_cause` | string \| null | Nein — nur zusammen mit `termination_type: "died"` gültig | `disease`, `pest`, `frost`, `heat`, `drought`, `waterlogging`, `neglect`, `mechanical`, `unknown` |

**Verhalten:**

- Ohne Body oder mit `termination_type: null`: reines Entfernen, wie vor der Einführung dieser Felder — `removed_on` wird gesetzt, keine weitere Klassifizierung.
- Mit `termination_type: "died"`: Die aktuelle Wachstumsphase wird über die Phasenübergangs-Engine **eingefroren** (der offene Phasenhistorie-Eintrag wird geschlossen, ohne eine Seneszenz-Transition auszulösen), und `termination_cause` wird für die Verlustursachen-Auswertung übernommen.
- Bei jedem Wert von `termination_type`: Offene Aufgaben und Pflegeerinnerungen der Pflanze werden aus der Warteschlange entfernt; abgeschlossene/übersprungene Aufgaben bleiben als Historie erhalten.

**Response (200):** `PlantResponse` — enthält jetzt zusätzlich die Felder `termination_type` und `termination_cause` (beide `null`, wenn nicht klassifiziert).

**Fehlercodes:**

| HTTP-Status | Bedeutung |
|-------------|----------|
| `404` | Pflanzinstanz nicht gefunden oder gehört nicht zum Mandanten |
| `422` | `termination_cause` gesetzt, aber `termination_type` ungleich `died` (`VALIDATION_ERROR`) |

**Beispiel — Verlust durch Schädlingsbefall:**

```bash
curl -X POST \
  "https://api.example.com/api/v1/t/mein-garten/plant-instances/plant_instances/101/remove" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"termination_type": "died", "termination_cause": "pest"}'
```

### Überlebens-Statistik abrufen

Liefert eine mandantenweite Auswertung aller Pflanzinstanzen: Überlebensrate, Aufschlüsselung nach Abschlussart, nach Wachstumsphase (nur ungeplante Verluste) und nach Verlustursache.

```
GET /api/v1/t/{tenant_slug}/plant-instances/survival-stats
```

**Response (200):**

```json
{
  "total": 42,
  "terminated": 18,
  "active": 24,
  "died": 3,
  "survived": 39,
  "survival_rate": 0.9286,
  "by_termination_type": [
    { "termination_type": "harvested", "count": 12 },
    { "termination_type": "died", "count": 3 },
    { "termination_type": "cancelled", "count": 2 },
    { "termination_type": "senesced", "count": 1 }
  ],
  "by_termination_cause": [
    { "termination_cause": "pest", "count": 2 },
    { "termination_cause": "frost", "count": 1 }
  ],
  "loss_by_phase": [
    { "phase_name": "seedling", "count": 2 },
    { "phase_name": "vegetative", "count": 1 }
  ]
}
```

`survived` zählt jede Pflanze, die **kein** ungeplanter Verlust war — geerntete, natürlich abgestorbene, abgebrochene und noch aktive Pflanzen zählen alle als überlebt; nur `termination_type: "died"` zählt als Verlust. `loss_by_phase` ist nach dem aufgelösten Phasen-**Namen** aggregiert (nicht nach Phasen-Key), damit dieselbe kanonische Phase über mehrere Arten hinweg zusammengefasst wird, und absteigend nach Anzahl sortiert.

!!! note "Reihenfolge der Routen"
    `/survival-stats` ist im Router **vor** `/{key}` deklariert, damit der literale Pfad nicht versehentlich als Pflanzen-Key interpretiert wird.

### Siehe auch

- [Wachstumsphasen — Benutzerhandbuch: Eine Pflanze entfernen](../user-guide/growth-phases.md#pflanze-entfernen)
- [Wachstumsphasen — Benutzerhandbuch: Überlebensrate und Verlustursachen auswerten](../user-guide/growth-phases.md#ueberlebensrate-verlustursachen)
- [Fehlerbehandlung](../api/error-handling.md)

---

## Pflanzinstanzen: Kindel-Abstammung (`mother_key`)

Wenn eine monokarpische Mutterpflanze automatisch in ihre letzte Blühphase wechselt, erzeugt Kamerplanter automatisch eine neue Pflanzinstanz (das Kindel) und verknüpft sie mit der Mutterpflanze. <!-- REQ-003 D10 / REQ-017 -->

### Zusätzliches Feld in der Pflanzinstanz-Antwort

```
GET /api/v1/t/{tenant_slug}/plant-instances/{key}
```

Die `PlantResponse` enthält seit dieser Erweiterung zusätzlich:

| Feld | Typ | Bedeutung |
|------|-----|----------|
| `mother_key` | string \| null | Schlüssel der Mutterpflanze, aus der diese Instanz als Kindel hervorgegangen ist. `null` für direkt angelegte Pflanzen. |

Die maßgebliche Abstammungsbeziehung ist zusätzlich als Graph-Kante `descended_from` (Kindel → Mutter) hinterlegt; `mother_key` spiegelt sie für einen günstigen Zugriff aus dem Frontend, ohne dass dafür eine Graph-Traversal-Abfrage nötig ist.

### Auslöser und Verhalten

- Der automatische Kindel-Spawn wird ausgelöst, sobald eine als monokarpisch konfigurierte Pflanzenart (`flowering_strategy: "monocarpic"`) automatisch in eine ihrer terminalen reproduktiven Phasen (Blüte, Fruchtentwicklung oder Reife) übergeht.
- Genau eine neue Pflanzinstanz wird angelegt; ein erneutes Auswerten desselben Übergangs erzeugt **kein** zweites Kindel (idempotent — geprüft über das Vorhandensein einer eingehenden `descended_from`-Kante der Mutter).
- Das Kindel übernimmt `tenant_key`, `species_key`, `cultivar_key` und den Standort der Mutter, **aber keinen Platz** (`slot_key: null`) — die Mutterpflanze behält ihren Platz, während sie seneszent auswelkt. Als `planted_on` wird das Datum des Übergangs übernommen.
- Zusätzlich zur Kante wird ein `PropagationEvent` mit `method: "clone"` persistiert (Mutter → Kindel).

!!! note "Kein eigener Endpunkt, kein manuelles Auslösen"
    Der Kindel-Spawn ist ein Seiteneffekt des automatischen Phasenübergangs (siehe [Wachstumsphasen — Automatische Phasenübergänge](../user-guide/growth-phases.md#automatische-phasenuebergaenge)) und besitzt **keinen** eigenen REST-Endpunkt zum manuellen Auslösen oder zum Abfragen der Vermehrungshistorie. Die volle Vermehrungs-API (Abstammungs-Traversal, Auflistung von Vermehrungsereignissen je Pflanze) bleibt REQ-017-Folgearbeit. <!-- REQ-017 -->

### Siehe auch

- [Wachstumsphasen — Benutzerhandbuch: Monokarpische Pflanzen](../user-guide/growth-phases.md#monokarpische-pflanzen)
- [Vermehrungsmanagement — Benutzerhandbuch](../user-guide/propagation.md#automatische-kindel-fortfuehrung)
- [Datenbankschema — Pflanzinstanz-Graph](database-schema.md#pflanzinstanz-graph)

---

## Saison- & Überwinterungs-Automatik

Diese Endpunkte lesen den automatisch berechneten Saison-Zustand eines Standorts und das automatisch materialisierte Überwinterungsprofil einer Pflanze. Beides entsteht ohne Nutzerinteraktion, sobald eine Pflanze einem Freiland-, Gewächshaus- oder Balkon-Standort (`OVERWINTERING_SITE_TYPES`) zugeordnet wird — beim Anlegen der Pflanze, bei einem Standortwechsel, sowie zusätzlich als Sicherheitsnetz aus der täglichen Saison-Auswertung — siehe [Saison-Automatik](../user-guide/season-automation.md) und [Überwinterung](../user-guide/overwintering.md) im Benutzerhandbuch. <!-- REQ-047 -->

Alle Endpunkte liegen unter dem mandantenspezifischen Pfad `/api/v1/t/{tenant_slug}/` und erfordern ein gültiges JWT-Token.

### Saison-Zustand eines Standorts lesen

```
GET /api/v1/t/{tenant_slug}/sites/{site_key}/season-state
```

**Response (200):**

```json
{
  "site_key": "sites/12",
  "season_state_id": "season-4f2a9c1b3d0e",
  "phase": "pre_winter",
  "trigger_tier": "live",
  "trigger_reason_i18n_key": "pages.season.trigger.frostForecast",
  "season_year": 2026,
  "entered_phase_at": "2026-10-18T06:30:00Z",
  "last_min_temp_c": 3.5,
  "forecast_first_frost_date": "2026-10-24",
  "estimated_first_frost_md": "10-20",
  "estimated_last_frost_md": "04-15",
  "evaluated_at": "2026-10-19T06:30:00Z"
}
```

`phase` ∈ `growing`, `pre_winter`, `winter_dormancy`, `pre_spring`. `trigger_tier` ∈ `live`, `climatological`, `calendar` — welche Kaskadenstufe (siehe [Saison-Automatik](../user-guide/season-automation.md#woher-die-einschatzung-kommt-die-drei-datenquellen)) den Zustand aktuell bestimmt.

Existiert für den Standort noch kein Saison-Zustand, wertet der Endpunkt ihn lazy aus und persistiert das Ergebnis, statt `404` zurückzugeben.

**Fehlercodes:**

| HTTP-Status | Bedeutung |
|-------------|----------|
| `404` | Standort nicht gefunden oder gehört nicht zum Mandanten |
| `409` | Standort ist nicht vom Typ `outdoor`, `greenhouse` oder `balcony` — nur diese frostexponierten Standort-Typen führen einen Saison-Zustand |

### Saison-Übersicht über alle Standorte

```
GET /api/v1/t/{tenant_slug}/season/overview
```

Liefert `{"states": [ ... ]}` mit einem `SeasonStateResponse`-Objekt (siehe oben) je Freiland-, Gewächshaus- oder Balkon-Standort des Mandanten. Speist das Dashboard-Widget „Winterschutz" (siehe [Dashboard personalisieren](../user-guide/dashboard-personalization.md)).

### Überwinterungsprofil einer Pflanze lesen

```
GET /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering
```

**Response (200):** das `OverwinteringProfile`-Objekt inklusive `auto_generated`, `user_overridden`, `derived_path` (`A` = in-situ, `B` = verlagert) und `materialized_at`.

**Fehlercodes:** `404` wenn die Pflanze kein (materialisiertes) Profil hat — z. B. weil sie winterhart ist, an keinem frostexponierten Standort steht, oder noch kein Übergang in „Winter kündigt sich an" stattgefunden hat.

### Überwinterungsstatus einer Pflanze lesen

```
GET /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/status
```

Additiver, rein lesender Begleit-Endpunkt zu `GET .../overwintering`: liefert **immer** `200`, auch ganz ohne Profil — praktisch für die Pflanzen-Detailseite, um zwischen „winterhart", „Schutz nötig, Plan folgt" und „Standort nicht frostexponiert" zu unterscheiden, ohne den 404-Fall des Profil-Endpunkts dafür zu missbrauchen.

**Response (200):** `PlantOverwinteringStatus`-Objekt:

```json
{
  "has_profile": false,
  "hardiness_light": "yellow",
  "will_materialize": true,
  "site_overwinterable": true
}
```

| Feld | Bedeutung |
|------|----------|
| `has_profile` | Ob bereits ein Überwinterungsprofil materialisiert ist. |
| `hardiness_light` | Winterhärte-Ampel (`green`, `yellow`, `red`) oder `null`, wenn sie sich nicht bestimmen lässt (z. B. fehlende Art- oder Standortzuordnung). |
| `will_materialize` | Ob (noch) automatisch ein Profil angelegt wird — `true` nur, wenn `site_overwinterable` und die Ampel nicht `green` ist. |
| `site_overwinterable` | Ob der Standort-Typ überhaupt frostexponiert ist (`outdoor`, `greenhouse`, `balcony`). `false` bei Innenbereich, Fensterbrett, Growzelt oder unauflösbarem Standort. |

**Fehlercodes:** keine — der Endpunkt antwortet immer mit `200`, auch für eine fremde oder unauflösbare Pflanze (Schutz vor einem Cross-Tenant-Existence-Oracle über den 404-Unterschied).

### Überwinterungsprofil übersteuern

```
PATCH /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering
```

Setzt einzelne Felder des Profils und markiert es als `user_overridden: true`. Danach ergänzt die Automatik nur noch fehlende Felder, überschreibt aber keine gesetzten Werte mehr.

**Fehlercodes:**

| HTTP-Status | Bedeutung |
|-------------|----------|
| `404` | Pflanze bzw. Profil nicht gefunden oder gehört nicht zum Mandanten |
| `422` | Ungültiger Wert, oder die gewählte Schutzmaßnahme widerspricht der Winterhärte-Ampel (Invariante D5 — z. B. „Ausgraben & lagern" bei winterharter Einstufung) |

### Überwinterungsprofil auf Automatik zurücksetzen

```
POST /api/v1/t/{tenant_slug}/plants/{plant_key}/overwintering/reset
```

Setzt `user_overridden` auf `false` zurück und materialisiert das Profil erneut vollständig aus dem Art-Steckbrief und der Winterhärte-Ampel des Standorts.

**Fehlercodes:** `404` wenn Pflanze oder Profil nicht gefunden werden bzw. nicht zum Mandanten gehören.

### Siehe auch

- [Saison-Automatik — Benutzerhandbuch](../user-guide/season-automation.md)
- [Überwinterung — Benutzerhandbuch](../user-guide/overwintering.md)
- [Umgebungsvariablen — Saison- & Überwinterungs-Automatik](environment-variables.md#saison-uberwinterungs-automatik)
- [Fehlerbehandlung](../api/error-handling.md)

---

## Pflanzenerkennung: Referenzbild-Beitrag (Self-Hosted-Erkennung)

Beim Anlegen einer Pflanze aus einer Foto-Identifikation heraus kann ein Nutzer das Identifikationsfoto optional als Trainingsreferenz für die selbst-gehostete DINOv2-Erkennung beitragen (siehe [Foto der neuen Pflanze zuordnen — Benutzerhandbuch](../user-guide/plant-identification.md#foto-der-neuen-pflanze-zuordnen)). <!-- Issue #447 -->

```
POST /api/v1/t/{tenant_slug}/identification/reference
```

Erfordert ein gültiges JWT-Token und mindestens die Mandanten-Rolle **grower**. Nur verfügbar, wenn die selbst-gehostete DINOv2-Erkennung aktiv ist (`INFERENCE_SERVICE_ENABLED=true`) — der externe Pl@ntNet-Pfad besitzt keinen lokalen Referenz-Index.

**Request-Body:** `multipart/form-data`

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `image` | file | Ja | JPEG- oder PNG-Bild, maximal `IDENTIFICATION_MAX_IMAGE_SIZE_MB` |
| `species_key` | string | Ja | Aufgelöster Art-Schlüssel, dem das Referenzbild zugeordnet wird |

!!! note "Kein `scientific_name`-Feld"
    Der Endpunkt erwartet **kein** Formularfeld `scientific_name`. Der wissenschaftliche Name wird serverseitig aus dem `species_key`-Datensatz abgeleitet; ein trotzdem mitgesendeter Wert wird ignoriert.

**Response (202 Accepted):** `ReferenceContributionResponse`

```json
{
  "accepted": true,
  "pending_review": true,
  "species_key": "species/123",
  "dim": 768
}
```

| Feld | Typ | Bedeutung |
|------|-----|----------|
| `accepted` | boolean | Ob der Beitrag angenommen und indexiert wurde |
| `pending_review` | boolean | `true`, solange der Beitrag **quarantiert** ist (`is_active=false`) und noch nicht in die aktive Erkennung anderer Nutzer einfließt. Wird erst nach Freigabe durch einen Platform-Admin `false`. |
| `species_key` | string | Der Art-Schlüssel, dem das Referenzbild zugeordnet wurde |
| `dim` | integer \| null | Dimensionalität des berechneten Embedding-Vektors |

**Fehlercodes:**

| HTTP-Status | Bedeutung |
|-------------|----------|
| `403` | Aktive Mandanten-Rolle unterhalb **grower** (z. B. **viewer**) |
| `404` | `species_key` verweist auf keine bekannte Art |
| `409` | Selbst-gehostete Erkennung ist nicht aktiviert (`INFERENCE_SERVICE_ENABLED=false`) |
| `413` | Bild überschreitet `IDENTIFICATION_MAX_IMAGE_SIZE_MB` |
| `415` | `Content-Type` ist weder `image/jpeg` noch `image/png` |
| `422` | Bild lässt sich nicht dekodieren (beschädigt oder kein gültiges Bildformat) |
| `429` | Tages-Kontingent für Beiträge (`REFERENCE_CONTRIBUTION_RATE_LIMIT_PER_USER_DAY`) ausgeschöpft |

!!! note "Sicherheitsmodell (Quarantäne, Provenienz, Dedup)"
    Jeder Beitrag wird mit `source="user_contributed"`, `is_active=false` sowie beitragendem Nutzer und Mandant als Provenienz gespeichert — er beeinflusst die Erkennung anderer Mandanten daher nicht, bevor ein Platform-Admin ihn geprüft hat. Ein erneuter Beitrag desselben Fotos (SHA-256-Hash des normalisierten Bilds) aktualisiert den bestehenden Eintrag statt einen weiteren anzulegen. Das Originalbild selbst wird nie persistiert — nur das Embedding.

### Siehe auch

- [Pflanze per Foto identifizieren — Benutzerhandbuch: Foto der neuen Pflanze zuordnen](../user-guide/plant-identification.md#foto-der-neuen-pflanze-zuordnen)
- [Referenzbilder kuratieren — Benutzerhandbuch](../user-guide/reference-image-curation.md)
- [Umgebungsvariablen — Foto-Identifikation](environment-variables.md#foto-identifikation-req-029)
- [Fehlerbehandlung](../api/error-handling.md)

---

## KI-Assistent <!-- REQ-031 --> {#ki-assistent}

!!! note "Teilweise verfügbar"
    Die hier dokumentierten Endpunkte sind implementiert und aktiv. Vom vollständigen Spezifikations-Umfang (u. a. Tipp-Karten-Erzeugung im Hintergrund, Tenant-Settings-Endpunkt, Provider-Verwaltung per API) sind bislang nur die unten aufgeführten Endpunkte umgesetzt — siehe die Hinweise je Abschnitt.

Alle Endpunkte antworten mit `404 Not Found`, wenn der Plattformbetreiber KI-Funktionen instanzweit deaktiviert hat (`AI_FEATURES_ENABLED=false`) — die KI-API existiert dann faktisch nicht. Details zur dreistufigen Freischaltung: [KI-Assistent — Benutzerhandbuch](../user-guide/ai-assistant.md#so-ist-der-ki-assistent-aufgebaut-drei-stufen-freischaltung).

### Öffentliche Wissensfrage (Light-Modus-fähig)

Kein Login nötig, IP-ratenbegrenzt (`AI_PUBLIC_RATE_LIMIT_PER_MIN`, Standard 10/Minute). Es wird **kein** Mandanten- oder Nutzerkontext an die Wissensbasis übergeben.

```
POST /api/v1/public/ai/ask
```

**Request-Body:**

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|-------------|
| `question` | string | Ja | 3–2000 Zeichen |
| `language` | `de` \| `en` | Nein | Standard: `de` |

**Response (200):** `AiResponseSchema`

```json
{
  "answer_text": "VPD (Dampfdruckdefizit) beschreibt den Unterschied ...",
  "sources": [
    { "source_key": "vpd-basics", "source_type": "guide", "title": "VPD-Grundlagen", "score": 0.87, "language": "de" }
  ],
  "language": "de",
  "language_mismatch_warning": false,
  "uses_tenant_data": false,
  "uses_cloud_provider": false,
  "confidence": "high",
  "fallback_species": null,
  "cultivar_hint": null,
  "model_name": "gemma3:12b",
  "provider_type": "ollama",
  "kb_version": "ks-1.4.2-idx-20260420",
  "generated_at": "2026-07-11T10:15:00Z"
}
```

`confidence` ist einer von `high` | `medium` | `low` | `none` (ADR-002 — sinkt, wenn die Frage auf eine mandanteneigene Art/Sorte referenziert, die nicht in der Wissensbasis vorhanden ist).

```
GET /api/v1/public/ai/health
```

**Response (200):** `{ "healthy": true }`

### Mandantenbezogene Endpunkte

Alle folgenden Endpunkte liegen unter `/api/v1/t/{tenant_slug}/ai/` und erfordern ein gültiges JWT-Token sowie eine aktive Mandanten-Mitgliedschaft. Eine rollenspezifische Einschränkung (Beobachter/Grower/Admin) ist in dieser Version noch **nicht** implementiert — jedes aktive Mitglied darf alle Endpunkte aufrufen.

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `GET` | `/ai/tips?context_type=&context_key=&language=` | Tipp-Karten für einen Kontext (cache-first) |
| `POST` | `/ai/tips/refresh?context_type=&context_key=&language=` | Tipp-Karten neu erzeugen (erzwingt Cache-Miss) |
| `POST` | `/ai/tips/{tip_key}/dismiss` | Tipp wegklicken |
| `POST` | `/ai/tips/{tip_key}/acted-on` | Tipp als umgesetzt markieren |
| `GET` | `/ai/daily-tip?language=` | Ein einzelner Tagestipp (kann `null` sein) |
| `POST` | `/ai/daily-tip/dismiss` | Heutigen Tagestipp wegklicken |
| `POST` | `/ai/explain` | „Warum?"-Erklärung für ein konkretes Element |
| `GET` | `/ai/conversations` | Konversationen auflisten |
| `POST` | `/ai/conversations` | Neue Konversation anlegen |
| `POST` | `/ai/conversations/{conversation_key}/messages` | Nachricht senden — Antwort als SSE-Stream |
| `DELETE` | `/ai/conversations/{conversation_key}` | Konversation sofort löschen (DSGVO Art. 17) |
| `GET` | `/ai/providers` | Verfügbare Provider auflisten (nur lesend) |

!!! info "Nur über API / Betreiber-Konfiguration: Tenant-Freischaltung"
    Jeder dieser Endpunkte erfordert zusätzlich `tenant.settings.ai_features_enabled=true` — dafür gibt es aktuell weder eine Oberfläche noch einen eigenen `GET`/`PUT`-Endpunkt; das Feld lässt sich nur direkt am Mandanten-Dokument setzen. Ohne diese Freischaltung antworten alle mandantenbezogenen Endpunkte mit `403` und `{ "detail": "ai.disabled_for_tenant" }` (Fehlercode `AI_DISABLED_FOR_TENANT`).

`POST /ai/explain` erwartet folgenden Request-Body:

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `subject_type` | `task` \| `reminder` \| `phase_transition` \| `feeding_event` | Art des zu erklärenden Elements |
| `subject_key` | string | Schlüssel des Elements |
| `question_template_id` | string | ID der kuratierten Frage-Vorlage |
| `language` | `de` \| `en` | Optional, Standard: `de` |

`POST /ai/conversations/{conversation_key}/messages` liefert die Antwort als `text/event-stream` (SSE) mit den Event-Typen `token` (einzelnes Antwort-Token), `done` (finale `AiResponseSchema` als JSON) und `error`.

**Fehlercodes (alle mandantenbezogenen Endpunkte):**

| HTTP-Status | Fehlercode | Bedeutung |
|-------------|-----------|----------|
| `404` | — | KI-Funktionen instanzweit deaktiviert (Stufe 1) |
| `403` | `AI_DISABLED_FOR_TENANT` | KI-Funktionen für diesen Mandanten deaktiviert (Stufe 2) |
| `403` | `CONSENT_REQUIRED` | Erforderliche Einwilligung fehlt (Stufe 3, `consent_purpose` im Body: `ai_tenant_data_access` oder `ai_cloud_processing`) |

### Globale Endpunkte (Platform-Admin)

```
GET /api/v1/ai/knowledge-service/health
```

Erfordert Platform-Admin-Rechte. Nur im Vollmodus gemountet (`KAMERPLANTER_MODE=full`). Liefert `{ "healthy": true|false }`.

### Siehe auch

- [KI-Assistent — Benutzerhandbuch](../user-guide/ai-assistant.md)
- [Datenschutz & DSGVO — Benutzerhandbuch](../user-guide/privacy.md)
- [Umgebungsvariablen — KI-Assistent](environment-variables.md#ki-assistent)
- [Fehlerbehandlung](../api/error-handling.md)
